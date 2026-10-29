"""Perfil descriptivo del CSV SENAMHI. Sin QA/QC, normalización ni persistencia RAW."""

from collections import Counter
from datetime import date
from decimal import Decimal, InvalidOperation
from functools import lru_cache
import hashlib
import os
from pathlib import Path
import re
import sqlite3
import stat
from threading import Event

from ..adquisicion.catalogo import EvidenciaDocumental
from ..adquisicion.consultas_locales import ENCABEZADO_SENAMHI, ProcedenciaLocal, VARIABLES_SENAMHI
from ..adquisicion.verificacion import EstadoEstructura, LectorCSV
from ._indice import IndicePerfil, LimitePerfil
from .modelos import (ExtremoObservado, HallazgoPerfil, HuellaPerfil, InformePerfil,
    LimitesPerfil, PerfilDia, PerfilEstacion, PerfilHora, PerfilPeriodo, PerfilTemporal, PerfilVariable)

_NUMERO = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?\Z")
_NO_FINITO = re.compile(r"[+-]?(?:s?nan[0-9]*|inf(?:inity)?)\Z", re.IGNORECASE | re.ASCII)
_CAMPOS_UBICACION = ("RED", "LONGITUD", "LATITUD", "ALTITUD", "DEPARTAMENTO", "PROVINCIA", "DISTRITO", "UBIGEO")
_POS_UBICACION = tuple(ENCABEZADO_SENAMHI.index(c) for c in _CAMPOS_UBICACION)


@lru_cache(maxsize=4096)
def _dia_ocho(texto):
    try:
        return date(int(texto[:4]), int(texto[4:6]), int(texto[6:]))
    except ValueError:
        return None


def _dia(texto):
    # Solo ocho caracteres entran a la caché; no retener celdas largas.
    return _dia_ocho(texto) if len(texto) == 8 and texto.isascii() and texto.isdigit() else None


def _patron_hora(texto):
    if re.fullmatch(r"[0-9]{6}", texto):
        return ("hhmmss_lexico" if texto[:2] <= "23" and texto[2:4] <= "59" and texto[4:] <= "59"
                else "seis_digitos_fuera_rango")
    if re.fullmatch(r"[0-9]{5}", texto):
        # Comparación de caracteres, sin fabricar un literal reconstruido.
        return ("cinco_digitos_compatibles_cero_inicial" if texto[1:3] <= "59" and texto[3:] <= "59"
                else "cinco_digitos_incompatibles_cero_inicial")
    return "vacio" if texto == "" else "otro_literal"


def _interpretar(texto, p):
    """Clasificación controlada; Decimal solo con longitud, dígitos y exponente acotados."""
    notaciones = []
    if texto == "":
        return "vacio", None, ()
    if len(texto) > p.max_caracteres_numero:
        return "fuera_presupuesto_numerico", None, ("longitud_numerica_excedida",)
    if _NO_FINITO.fullmatch(texto):
        return "no_finito", None, ("no_finito_literal",)
    if not _NUMERO.fullmatch(texto):
        if texto != texto.strip():
            notaciones.append("espacios_externos")
        if "," in texto:
            notaciones.append("coma_no_admitida")
        if "_" in texto:
            notaciones.append("guion_bajo_no_admitido")
        if not texto.isascii():
            notaciones.append("caracteres_no_ascii")
        return "no_interpretable", None, tuple(notaciones or ["otro_no_numerico"])
    partes = re.split("[eE]", texto)
    mantisa = partes[0].lstrip("+-")
    if sum(c.isdigit() for c in mantisa) > p.max_digitos_numero:
        return "fuera_presupuesto_numerico", None, ("digitos_excedidos",)
    if len(partes) == 2:
        notaciones.append("exponencial")
        if abs(int(partes[1])) > p.max_exponente:
            return "fuera_presupuesto_numerico", None, ("exponente_excedido",)
    if mantisa.startswith("."):
        notaciones.append("sin_parte_entera")
    if mantisa.endswith("."):
        notaciones.append("sin_parte_fraccionaria")
    entero = mantisa.split(".")[0]
    if len(entero) > 1 and entero.startswith("0"):
        notaciones.append("ceros_iniciales")
    try:
        numero = Decimal(texto)  # Construcción exacta; no usa float ni redondea por contexto.
    except InvalidOperation:
        return "no_interpretable", None, ("decimal_no_interpretable",)
    return "finito", numero, tuple(notaciones)


def _huella(ruta, p, cancelacion):
    if (".." in ruta.parts or any(q.is_symlink() or q.is_junction() for q in (ruta, *ruta.parents))
            or not stat.S_ISREG(ruta.stat().st_mode)):
        raise LimitePerfil("ruta_fuente_no_admitida")
    def firma(s):
        return s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns
    inicial = ruta.stat()
    if inicial.st_size > p.lectura.max_bytes_archivo:
        raise LimitePerfil("limite_bytes_archivo")
    h, recibidos = hashlib.sha256(), 0
    with ruta.open("rb") as f:
        if firma(os.fstat(f.fileno())) != firma(inicial):
            raise LimitePerfil("fuente_cambio_durante_huella")
        while True:
            if cancelacion.is_set():
                raise LimitePerfil("cancelado")
            bloque = f.read(p.lectura.tamano_bloque)
            if not bloque:
                break
            recibidos += len(bloque)
            if recibidos > p.lectura.max_bytes_archivo:
                raise LimitePerfil("limite_bytes_archivo")
            h.update(bloque)
        if firma(os.fstat(f.fileno())) != firma(inicial) or firma(ruta.stat()) != firma(inicial):
            raise LimitePerfil("fuente_cambio_durante_huella")
    return HuellaPerfil(recibidos, h.hexdigest())


class _Variable:
    def __init__(self, nombre):
        self.nombre = nombre
        self.n = Counter()
        self.notaciones = Counter()
        self.marcadores = Counter()
        self.minimo = self.maximo = None
        self.ejemplos = []

    def agregar(self, texto, registro, p):
        self.n["total"] += 1
        clase, numero, notaciones = _interpretar(texto, p)
        self.n[clase] += 1
        self.notaciones.update(notaciones)
        if texto in p.marcadores:
            self.marcadores[texto] += 1
        if ((clase not in ("vacio", "finito") or notaciones or texto in p.marcadores)
                and len(self.ejemplos) < p.max_ejemplos):
            self.ejemplos.append((clase, texto, registro.numero))
        if clase == "finito":
            self.n["signo"] += texto.startswith(("+", "-"))
            self.n["punto"] += "." in re.split("[eE]", texto)[0]
            extremo = ExtremoObservado(numero, texto, registro.numero, registro.valores[2], registro.valores[3])
            if self.minimo is None or numero < self.minimo.decimal:
                self.minimo = extremo
            if self.maximo is None or numero > self.maximo.decimal:
                self.maximo = extremo

    def informe(self, indexado, distintos, repetidos):
        n = self.n
        return PerfilVariable(self.nombre, n["total"], n["vacio"], n["total"] - n["vacio"],
            n["finito"], n["no_interpretable"], n["no_finito"], n["fuera_presupuesto_numerico"],
            n["signo"], n["punto"], tuple(sorted(self.notaciones.items())), tuple(sorted(self.marcadores.items())),
            self.minimo, self.maximo, indexado and not n["fuera_presupuesto_numerico"],
            distintos if indexado else None, repetidos if indexado else (), tuple(self.ejemplos))


class _Estacion:
    def __init__(self, nombre):
        self.nombre, self.total = nombre, 0
        self.variables = {v: _Variable(v) for v in VARIABLES_SENAMHI}
        self.campos = {c: Counter() for c in _CAMPOS_UBICACION}
        self.relaciones, self.horas, self.patrones, self.longitudes = Counter(), Counter(), Counter(), Counter()
        self.cobertura = {}
        self.anterior = self.fecha_anterior = None
        self.cambios = self.invalidas = self.retrocesos = 0
        self.ejemplos = []

    def comprobar(self, v, relacion, p):
        if v[3] not in self.horas and len(self.horas) >= p.max_horas_estacion:
            raise LimitePerfil("limite_horas_estacion")
        if relacion not in self.relaciones and len(self.relaciones) >= p.max_relaciones_estacion:
            raise LimitePerfil("limite_relaciones_estacion")
        for campo, texto in zip(_CAMPOS_UBICACION, relacion):
            if texto not in self.campos[campo] and len(self.campos[campo]) >= p.max_variantes_campo:
                raise LimitePerfil("limite_variantes_campo")

    def agregar(self, registro, relacion, dia, p):
        v = registro.valores
        self.total += 1
        for variable, i in zip(VARIABLES_SENAMHI, (7, 8, 9)):
            self.variables[variable].agregar(v[i], registro, p)
        for campo, texto in zip(_CAMPOS_UBICACION, relacion):
            self.campos[campo][texto] += 1
        self.relaciones[relacion] += 1
        if self.anterior is not None and self.anterior != relacion:
            self.cambios += 1
            if len(self.ejemplos) < p.max_ejemplos:
                self.ejemplos.append((registro.numero, v[2], self.anterior, relacion))
        self.anterior = relacion
        self.horas[v[3]] += 1
        self.longitudes[len(v[3])] += 1
        self.patrones[_patron_hora(v[3])] += 1
        if dia is None:
            self.invalidas += 1
        else:
            minimo, maximo = self.cobertura.get(v[3], (dia, dia))
            self.cobertura[v[3]] = min(minimo, dia), max(maximo, dia)
            if self.fecha_anterior is not None and dia < self.fecha_anterior:
                self.retrocesos += 1
            self.fecha_anterior = dia

    def informe(self, indexado, repeticiones):
        return PerfilEstacion(self.nombre, self.total,
            tuple(v.informe(indexado, *repeticiones.get((self.nombre, k), (0, ()))) for k, v in self.variables.items()),
            PerfilHora(tuple(sorted(self.longitudes.items())), tuple(sorted(self.patrones.items())),
                tuple(sorted(self.horas.items())), tuple((h, *fechas) for h, fechas in sorted(self.cobertura.items())),
                tuple((h[:2], h[2:4], h[4:], n) for h, n in sorted(self.horas.items())
                      if re.fullmatch(r"[0-9]{6}", h)),
                tuple((h[:1], h[1:3], h[3:], n) for h, n in sorted(self.horas.items())
                      if re.fullmatch(r"[0-9]{5}", h))),
            tuple((c, tuple(sorted(v.items()))) for c, v in self.campos.items()),
            tuple(sorted(self.relaciones.items())), self.cambios, tuple(self.ejemplos), self.invalidas, self.retrocesos)


def _resumir_indice(indice, estaciones, p, evento):
    """Recorridos en orden de PK; sin GROUP BY/ORDER BY que generen sorts ilimitados."""
    dias, periodos, temporal, repeticiones = [], [], [], {}
    for nombre, grupo in sorted(estaciones.items()):
        if evento.is_set():
            raise LimitePerfil("cancelado")
        for variable in VARIABLES_SENAMHI:
            mejores, distintos = [], 0
            for literal, cuenta in indice.conexion.execute(
                    "SELECT literal,n FROM valores WHERE estacion=? AND variable=? ORDER BY literal", (nombre, variable)):
                if evento.is_set():
                    raise LimitePerfil("cancelado")
                distintos += 1
                if cuenta > 1:
                    # Más frecuentes; empates por literal, deterministas.
                    mejores.append((literal, cuenta))
                    mejores.sort(key=lambda x: (-x[1], x[0]))
                    if len(mejores) > p.max_repetidos:
                        mejores.pop()
            repeticiones[nombre, variable] = distintos, tuple(mejores)
        hist = Counter()
        primero = ultimo = None
        saltos, ejemplos, dias_multihora, repetidas, cantidad = 0, [], 0, 0, 0
        for fecha, n, horas in indice.conexion.execute(
                "SELECT fecha,n,horas FROM dias WHERE estacion=? ORDER BY fecha", (nombre,)):
            if evento.is_set():
                raise LimitePerfil("cancelado")
            dia = date.fromisoformat(fecha)
            dias.append(PerfilDia(nombre, dia, n, horas, n - horas))
            cantidad += 1
            hist[n] += 1
            dias_multihora += horas > 1
            repetidas += n - horas
            if ultimo is not None and (dia - ultimo).days > 1:
                saltos += 1
                if len(ejemplos) < p.max_ejemplos:
                    ejemplos.append((ultimo, dia, (dia - ultimo).days - 1))
            primero = primero or dia
            ultimo = dia
        temporal.append(PerfilTemporal(nombre, primero, ultimo, cantidad, tuple(sorted(hist.items())),
            dias_multihora, repetidas, saltos, tuple(ejemplos), grupo.invalidas == 0))
        mes_actual, horas_mes = None, []
        def guardar_mes():
            if mes_actual is not None:
                patrones = Counter()
                for hora, n in horas_mes:
                    patrones[_patron_hora(hora)] += n
                periodos.append(PerfilPeriodo(nombre, mes_actual, tuple(horas_mes), tuple(sorted(patrones.items()))))
        for mes, hora, n in indice.conexion.execute(
                "SELECT mes,hora,n FROM periodos WHERE estacion=? ORDER BY mes,hora", (nombre,)):
            if evento.is_set():
                raise LimitePerfil("cancelado")
            if mes != mes_actual:
                guardar_mes()
                mes_actual, horas_mes = mes, []
            horas_mes.append((hora, n))
        guardar_mes()
    return tuple(dias), tuple(periodos), tuple(temporal), repeticiones


def _hallazgos(estaciones):
    salida = [HallazgoPerfil("incertidumbre", codigo) for codigo in
              ("zona_horaria_no_asignada", "identidad_fisica_no_acreditada", "semantica_marcadores_no_inferida")]
    for e in estaciones:
        for v in e.variables:
            for codigo, cantidad in (("no_interpretables", v.no_interpretables), ("no_finitos", v.no_finitos),
                                      ("presupuesto_numerico_excedido", v.fuera_presupuesto_numerico)):
                if cantidad:
                    salida.append(HallazgoPerfil("alerta_tecnica", codigo, e.nombre_literal, v.variable, cantidad))
        for patron, cantidad in e.horas.patrones:
            if patron != "hhmmss_lexico":
                salida.append(HallazgoPerfil("alerta_tecnica", patron, e.nombre_literal, cantidad=cantidad))
        if len(e.relaciones_ubicacion) > 1:
            salida.append(HallazgoPerfil("incertidumbre", "nombre_con_ubicaciones_distintas", e.nombre_literal,
                                        cantidad=len(e.relaciones_ubicacion)))
        ubigeos = dict(e.campos_ubicacion)["UBIGEO"]
        no_seis = sum(n for texto, n in ubigeos if not re.fullmatch(r"[0-9]{6}", texto))
        if no_seis:
            salida.append(HallazgoPerfil("alerta_tecnica", "ubigeo_no_seis_digitos", e.nombre_literal, cantidad=no_seis))
        if e.fechas_invalidas:
            salida.append(HallazgoPerfil("alerta_tecnica", "fecha_civil_no_interpretable", e.nombre_literal,
                                        cantidad=e.fechas_invalidas))
    return tuple(salida)


def perfilar_csv(ruta, procedencia: ProcedenciaLocal, *, limites=None, documento=None,
                 cancelacion=None, codificacion=None, directorio_temporal=None):
    """Una lectura secuencial y hashes físicos antes/después, sin alterar el original.

    Al interrumpirse se conservan contadores en RAM de filas procesadas; se omiten
    TODOS los agregados del índice, que podría haber quedado parcialmente actualizado.
    Anomalías de contenido no significan recorrido incompleto ni validación científica.
    """
    if not isinstance(procedencia, ProcedenciaLocal):
        raise TypeError("Se requiere ProcedenciaLocal")
    p = limites if limites is not None else LimitesPerfil()
    if not isinstance(p, LimitesPerfil):
        raise TypeError("Se requiere LimitesPerfil")
    if documento is not None and (not isinstance(documento, EvidenciaDocumental)
            or documento.fuente != procedencia.fuente or documento.recurso_id != procedencia.recurso_id):
        raise ValueError("Documento incompatible con el recurso")
    ruta = Path(ruta).absolute()
    evento = cancelacion if cancelacion is not None else Event()
    lector = LectorCSV(ruta, politica=p.lectura, cancelacion=evento, codificacion=codificacion,
                       delimitador=",", encabezado_declarado=True, campos_esperados=len(ENCABEZADO_SENAMHI))
    indice = IndicePerfil(ruta, p, directorio_temporal)
    grupos, procesadas, motivo = {}, 0, None
    antes = despues = None
    dias = periodos = temporal = ()
    repeticiones = {}
    indexado = encabezado = False
    try:
        antes = _huella(ruta, p, evento)
        if procedencia.sha256_declarado is not None and antes.sha256 != procedencia.sha256_declarado:
            raise LimitePerfil("sha256_declarado_no_coincide")
        indice.abrir()
        with lector:
            for r in lector:
                if r.numero == 1:
                    if r.valores != ENCABEZADO_SENAMHI:
                        raise LimitePerfil("encabezado_no_admitido")
                    encabezado = True
                    continue
                if not r.estructura_correcta:
                    raise LimitePerfil("anchura_inconsistente")
                if evento.is_set():
                    raise LimitePerfil("cancelado")
                v = r.valores
                if any(len(v[i]) > p.max_caracteres_literal for i in range(1, 16)):
                    raise LimitePerfil("limite_longitud_agregados")
                if v[1] not in grupos:
                    if len(grupos) >= p.max_estaciones:
                        raise LimitePerfil("limite_estaciones")
                    grupo = _Estacion(v[1])
                else:
                    grupo = grupos[v[1]]
                relacion = tuple(v[i] for i in _POS_UBICACION)
                grupo.comprobar(v, relacion, p)
                dia = _dia(v[2])
                indice.registrar(v[1], v[2], v[3], dia, tuple(zip(VARIABLES_SENAMHI, v[7:10])))
                grupo.agregar(r, relacion, dia, p)
                grupos[v[1]] = grupo
                procesadas += 1
                if procesadas % 1000 == 0:
                    indice.conexion.commit()
        lectura = lector.informe
        if not encabezado or not lectura.recorrido_completo or lectura.estado is not EstadoEstructura.COMPATIBLE:
            raise LimitePerfil(lectura.motivo_fin if not lectura.recorrido_completo else "estructura_no_compatible")
        indice.conexion.commit()
        dias, periodos, temporal, repeticiones = _resumir_indice(indice, grupos, p, evento)
        despues = _huella(ruta, p, evento)
        if antes != despues:
            raise LimitePerfil("huellas_antes_despues_distintas")
        indexado = True
    except LimitePerfil as error:
        motivo = str(error)
    except sqlite3.Error:
        motivo = "indice_temporal_no_disponible_o_limite_bytes"
    except OSError:
        motivo = "entrada_salida_no_disponible"
    finally:
        try:
            indice.cerrar()
        except (OSError, sqlite3.Error):
            motivo = "limpieza_temporal_fallida"
    if motivo is not None:
        indexado = False
        dias = periodos = temporal = ()
        repeticiones = {}
    estaciones = tuple(g.informe(indexado, repeticiones) for _, g in sorted(grupos.items()))
    return InformePerfil(procedencia, documento, indexado and indice.eliminado, motivo or "eof", procesadas,
        antes, despues, antes is not None and antes == despues, estaciones, dias, periodos, temporal,
        indexado, indice.eliminado, _hallazgos(estaciones), (), lector.informe, p)
