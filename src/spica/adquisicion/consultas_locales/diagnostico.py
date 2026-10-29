"""Diagnóstico léxico acotado. El índice SQLite es desechable, ajeno a RAW."""

from dataclasses import dataclass, field
import os
from pathlib import Path
import re
import shutil
import sqlite3
import tempfile
from threading import Event
from uuid import uuid4

from ..verificacion import InformeLecturaCSV, PoliticaLecturaCSV
from .consulta import _Filas, _fecha_civil
from .modelos import ProcedenciaLocal


@dataclass(frozen=True)
class LimitesDiagnostico:
    max_claves_temporales: int = 500_000
    max_bytes_indice: int = 64 * 1024**2
    max_horas: int = 256
    max_relaciones: int = 2048
    max_ejemplos: int = 20
    max_caracteres_literal: int = 512
    lectura: PoliticaLecturaCSV = field(default_factory=PoliticaLecturaCSV)

    def __post_init__(self):
        topes = dict(max_claves_temporales=2_000_000, max_bytes_indice=256 * 1024**2,
                     max_horas=4096, max_relaciones=4096, max_ejemplos=100,
                     max_caracteres_literal=512)
        for nombre, tope in topes.items():
            valor = getattr(self, nombre)
            if type(valor) is not int or not 0 < valor <= tope:
                raise ValueError("Presupuesto de diagnóstico no admitido")
        if self.max_bytes_indice < 8192 or not isinstance(self.lectura, PoliticaLecturaCSV):
            raise ValueError("Presupuesto SQLite o lectura no admitidos")


@dataclass(frozen=True)
class InformeDiagnostico:
    procedencia: ProcedenciaLocal
    completo: bool
    motivo_fin: str
    filas_procesadas: int
    fechas_invalidas: int
    fecha_minima: str | None  # ISO civil, sin zona.
    fecha_maxima: str | None
    horas_por_longitud: tuple[tuple[int, int], ...]
    horas_por_patron: tuple[tuple[str, int], ...]
    horas_literales: tuple[tuple[str, int], ...]
    ubigeos_por_patron: tuple[tuple[str, int], ...]
    # ESTACION, UBIGEO, LONGITUD, LATITUD, ALTITUD, DEPARTAMENTO, PROVINCIA, DISTRITO, RED, cuenta.
    relaciones_ubicacion: tuple[tuple[tuple[str, ...], int], ...]
    claves_distintas: int
    claves_repetidas: int
    repeticiones_adicionales: int
    ejemplos_duplicados: tuple[tuple[str, str, str], ...]
    # ESTACION, variable, FECHA, HORA, número de registro; ejemplos originales vacíos.
    ejemplos_vacios: tuple[tuple[str, str, str, str, int], ...]
    temporal_eliminado: bool
    lectura: InformeLecturaCSV


def _patron_hora(valor):
    if re.fullmatch(r"[0-9]{6}", valor):
        return ("hhmmss_lexicamente_valido" if valor[:2] <= "23" and
                valor[2:4] <= "59" and valor[4:] <= "59" else "seis_digitos_fuera_de_rango")
    if re.fullmatch(r"[0-9]{5}", valor):
        return "cinco_digitos_no_hhmmss"
    return "vacio" if valor == "" else "otro_literal"


def _patron_ubigeo(valor):
    if re.fullmatch(r"[0-9]{6}", valor):
        return "seis_digitos_sin_validacion_administrativa"
    if re.fullmatch(r"[0-9]+\.0", valor):
        return "digitos_con_sufijo_decimal_punto_cero"
    return "vacio" if valor == "" else "otro_literal"


class _Limite(Exception):
    pass


def diagnosticar_csv(ruta, procedencia: ProcedenciaLocal, *, limites=None,
                    cancelacion=None, codificacion=None, directorio_temporal=None):
    """Recorre con LectorCSV. Solo escribe un índice efímero de tres literales.

    Duplicado significa igualdad exacta (ESTACION, FECHA, HORA); no demuestra
    duplicación de instantes. El índice admite filas desordenadas. No persiste
    observaciones, informes ni eventos RAW. KeyboardInterrupt se propaga tras limpiar.
    """
    if not isinstance(procedencia, ProcedenciaLocal):
        raise TypeError("Se requiere ProcedenciaLocal")
    p = limites if limites is not None else LimitesDiagnostico()
    if not isinstance(p, LimitesDiagnostico):
        raise TypeError("Se requiere LimitesDiagnostico")
    evento = cancelacion if cancelacion is not None else Event()
    filas = _Filas(ruta, p.lectura, evento, codificacion)
    horas, longitudes, patrones, ubigeos, relaciones = {}, {}, {}, {}, {}
    ejemplos, vacios = [], []
    procesadas = invalidas = claves = repetidas = adicionales = 0
    minimo = maximo = None
    motivo = None
    carpeta = conexion = None
    creada = False
    eliminado = True
    try:
        padre = Path(directorio_temporal) if directorio_temporal is not None else Path(tempfile.gettempdir()).resolve()
        if (not padre.is_absolute() or ".." in padre.parts or not padre.is_dir()
                or any(q.is_symlink() or q.is_junction() for q in (padre, *padre.parents))
                or padre.resolve().is_relative_to(Path(ruta).absolute().parent)):
            raise _Limite("directorio_temporal_no_admitido")
        # Margen para metadatos; no constituye reserva ni cuota del SO.
        if shutil.disk_usage(padre).free < p.max_bytes_indice + 2 * 1024**2:
            raise _Limite("espacio_temporal_insuficiente")
        carpeta = padre / ("spica-diagnostico-" + uuid4().hex)
        carpeta.mkdir(mode=0o755 if os.name == "nt" else 0o700)
        creada = True
        eliminado = False
        conexion = sqlite3.connect(carpeta / "indice.sqlite3")
        conexion.execute("PRAGMA page_size=4096")
        conexion.execute(f"PRAGMA max_page_count={p.max_bytes_indice // 4096}")
        conexion.execute("PRAGMA cache_size=-1024")
        # Sin journal: índice desechable, jamás se recupera ni reutiliza tras error.
        # Evita duplicar en disco el presupuesto del índice con un rollback journal.
        conexion.execute("PRAGMA journal_mode=OFF")
        conexion.execute("PRAGMA synchronous=OFF")
        conexion.execute("PRAGMA temp_store=MEMORY")
        conexion.execute("PRAGMA trusted_schema=OFF")
        conexion.execute("CREATE TABLE claves (estacion TEXT, fecha TEXT, hora TEXT, n INTEGER NOT NULL, "
                         "PRIMARY KEY (estacion,fecha,hora)) WITHOUT ROWID")
        with filas:
            for r in filas:
                if evento.is_set():
                    raise _Limite("cancelado")
                v = r.valores
                relacion = tuple(v[i] for i in (1, 14, 4, 5, 6, 11, 12, 13, 10))
                if any(len(t) > p.max_caracteres_literal for t in (*relacion, v[2], v[3])):
                    raise _Limite("limite_longitud_agregados")
                if v[3] not in horas and len(horas) >= p.max_horas:
                    raise _Limite("limite_horas_distintas")
                if relacion not in relaciones and len(relaciones) >= p.max_relaciones:
                    raise _Limite("limite_relaciones_ubicacion")
                clave = v[1], v[2], v[3]
                anterior = conexion.execute("SELECT n FROM claves WHERE estacion=? AND fecha=? AND hora=?", clave).fetchone()
                if anterior is None:
                    if claves >= p.max_claves_temporales:
                        raise _Limite("limite_claves_temporales")
                    conexion.execute("INSERT INTO claves VALUES (?,?,?,1)", clave)
                    claves += 1
                else:
                    conexion.execute("UPDATE claves SET n=n+1 WHERE estacion=? AND fecha=? AND hora=?", clave)
                    adicionales += 1
                    if anterior[0] == 1:
                        repetidas += 1
                        if len(ejemplos) < p.max_ejemplos:
                            ejemplos.append(clave)
                # Solo contar la fila tras comprobar todos los presupuestos.
                procesadas += 1
                horas[v[3]] = horas.get(v[3], 0) + 1
                longitudes[len(v[3])] = longitudes.get(len(v[3]), 0) + 1
                patron = _patron_hora(v[3])
                patrones[patron] = patrones.get(patron, 0) + 1
                patron = _patron_ubigeo(v[14])
                ubigeos[patron] = ubigeos.get(patron, 0) + 1
                relaciones[relacion] = relaciones.get(relacion, 0) + 1
                fecha = _fecha_civil(v[2])
                if fecha is None:
                    invalidas += 1
                else:
                    minimo = min(minimo, fecha) if minimo is not None else fecha
                    maximo = max(maximo, fecha) if maximo is not None else fecha
                for variable, indice in (("TEMP", 7), ("HR", 8), ("PP", 9)):
                    if v[indice] == "" and len(vacios) < p.max_ejemplos:
                        vacios.append((v[1], variable, v[2], v[3], r.numero))
                if procesadas % 1000 == 0:
                    conexion.commit()
            conexion.commit()
    except _Limite as error:
        motivo = str(error)  # Solo códigos propios constantes, nunca backend/rutas.
    except sqlite3.Error:
        motivo = "indice_temporal_no_disponible_o_limite_bytes"
    except OSError:
        motivo = "entrada_salida_temporal_no_disponible"
    finally:
        # También se ejecuta ante KeyboardInterrupt/SystemExit. No borrar recursivamente.
        try:
            if conexion is not None:
                conexion.close()
        finally:
            if creada:
                try:
                    (carpeta / "indice.sqlite3").unlink(missing_ok=True)
                    carpeta.rmdir()
                    eliminado = True
                except OSError:
                    motivo = "limpieza_temporal_fallida"
    lectura = filas.lector.informe
    completo = filas.completa and motivo is None and invalidas == 0 and eliminado
    motivo = (motivo or filas.motivo or ("fechas_civiles_invalidas" if invalidas else None)
              or ("estructura_no_compatible" if lectura.recorrido_completo and not filas.completa else None)
              or lectura.motivo_fin)
    return InformeDiagnostico(procedencia, completo, motivo, procesadas, invalidas,
        minimo.isoformat() if minimo else None, maximo.isoformat() if maximo else None,
        tuple(sorted(longitudes.items())), tuple(sorted(patrones.items())), tuple(sorted(horas.items())),
        tuple(sorted(ubigeos.items())), tuple(sorted(relaciones.items())), claves, repetidas,
        adicionales, tuple(ejemplos), tuple(vacios), eliminado, lectura)
