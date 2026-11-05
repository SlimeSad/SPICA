"""Arnés manual 84-C. Requiere autorización del llamador para el activo exacto.

No es una API RAW ni un lector CSV nuevo. Solo lee y devuelve objetos en memoria;
no escribe informes. No ejecutar contra una base con escritores concurrentes.
"""

from datetime import date, datetime
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import stat
from threading import Event

from spica.adquisicion.almacenamiento.inspeccion import _lectura_sqlite, PoliticaInspeccionRAW
from spica.adquisicion.almacenamiento.modelos import (
    ActivoRAW, DeclaracionRAW, ErrorAlmacenamientoRAW, EstadoIncorporacion,
)
from spica.adquisicion.almacenamiento.raw import _segura
from spica.adquisicion.catalogo import RecursoCatalogo
from spica.adquisicion.catalogo.evidencias import desempaquetar
from spica.adquisicion.consultas_locales import (
    ConsultaLocal, ConsultorLocalCSV, LimitesConsulta, ProcedenciaLocal,
)
from spica.adquisicion.nucleo import Fuente
from spica.adquisicion.verificacion import PoliticaLecturaCSV
from spica.interoperabilidad import DimensionEvaluacion as D
from spica.interoperabilidad.adaptadores import adaptar_catalogo, adaptar_meteorologia
from spica.interoperabilidad.operaciones import OperacionPropuesta, evaluar_operacion


class ErrorPiloto(Exception):
    """Código fijo sin propagar contenido, rutas o mensajes de SQLite."""


def _cancelado(evento):
    if evento.is_set():
        raise ErrorPiloto("cancelado")


def _firma(ruta):
    ruta = _segura(Path(ruta))
    s = ruta.stat()
    if not stat.S_ISREG(s.st_mode):
        raise ErrorPiloto("archivo_no_regular")
    return s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns


def _huella(ruta, limite, evento):
    _cancelado(evento)
    inicial = _firma(ruta)
    if inicial[2] > limite:
        raise ErrorPiloto("limite_archivo")
    digest, recibidos = hashlib.sha256(), 0
    with ruta.open("rb") as f:
        def firma_descriptor():
            s = os.fstat(f.fileno())
            return s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns
        if inicial != firma_descriptor():
            raise ErrorPiloto("archivo_cambio")
        while True:
            _cancelado(evento)
            bloque = f.read(min(65_536, limite - recibidos + 1))
            if not bloque:
                break
            recibidos += len(bloque)
            if recibidos > limite:
                raise ErrorPiloto("limite_archivo")
            digest.update(bloque)
        if inicial != firma_descriptor() or inicial != _firma(ruta):
            raise ErrorPiloto("archivo_cambio")
    return recibidos, digest.hexdigest(), inicial


def _sin_auxiliares(raiz, catalogo):
    for p in (raiz / ".spica-raw.inicializando", *(
            Path(str(catalogo) + s) for s in ("-wal", "-shm", "-journal"))):
        # lexists también detecta enlaces colgantes; no se abren ni eliminan.
        if os.path.lexists(p):
            raise ErrorPiloto("auxiliar_o_inicializacion_requiere_revision")


def _solo_select(accion, primero, segundo, base, origen):
    if accion in (sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ):
        return sqlite3.SQLITE_OK
    if accion == sqlite3.SQLITE_PRAGMA and primero == "user_version" and segundo is None:
        return sqlite3.SQLITE_OK
    return sqlite3.SQLITE_DENY


def _consultar_activo(ruta, asset_id):
    # Se reutiliza únicamente la rama inmutable sin WAL. No inspecciona esquemas
    # de referencia, migra, abre CatalogoRAW ni registra eventos de comprobación.
    with _lectura_sqlite(ruta, False, PoliticaInspeccionRAW()) as c:
        c.execute("PRAGMA query_only=ON")
        c.execute("PRAGMA trusted_schema=OFF")
        c.set_authorizer(_solo_select)
        if c.execute("PRAGMA user_version").fetchone() != (2,):
            raise ErrorPiloto("version_catalogo_no_admitida")
        if c.execute("SELECT type FROM sqlite_master WHERE name='activos'").fetchone() != ("table",):
            raise ErrorPiloto("tabla_activos_no_reconocida")
        c.row_factory = sqlite3.Row
        filas = c.execute("SELECT id,objeto_id,declaracion,fecha_utc,estado,tamano,sha256,"
            "ruta_interna,error,advertencias,comprobacion_utc,media_detected FROM activos WHERE id=?",
            (asset_id,)).fetchmany(2)
        if len(filas) != 1:
            raise ErrorPiloto("activo_no_identificado")
        f = filas[0]
    if len(f["declaracion"].encode("utf-8")) > 65_536:
        raise ErrorPiloto("declaracion_excede_limite")
    datos = json.loads(f["declaracion"])
    paquete = datos.pop("_evidencia_adquisicion", None)
    datos["fuente"] = Fuente(**datos["fuente"])
    activo = ActivoRAW(f["id"], DeclaracionRAW(**datos), datetime.fromisoformat(f["fecha_utc"]),
        EstadoIncorporacion(f["estado"]), f["tamano"], f["sha256"], f["ruta_interna"], f["error"],
        tuple(json.loads(f["advertencias"])),
        datetime.fromisoformat(f["comprobacion_utc"]) if f["comprobacion_utc"] else None,
        f["media_detected"])
    if paquete is None:
        raise ErrorPiloto("evidencia_adquisicion_ausente")
    return activo, desempaquetar(paquete, activo)


def ejecutar(raiz, *, asset_id, tamano_esperado, sha256_esperado, fuente_esperada, cancelacion=None):
    """Ensayo secuencial acotado del recurso autorizado; sin autorización implícita.

    Los valores esperados deben proceder del expediente aprobado. Los parámetros
    permiten probar el mismo procedimiento con fixtures sin acceder al almacén real.
    La raíz debe estar controlada y sin escritores. Ante error no hay reintentos.
    """
    try:
        return _ejecutar(raiz, asset_id=asset_id, tamano_esperado=tamano_esperado,
                         sha256_esperado=sha256_esperado, fuente_esperada=fuente_esperada,
                         cancelacion=cancelacion)
    except (OSError, sqlite3.Error, ValueError, TypeError, KeyError, ErrorAlmacenamientoRAW):
        raise ErrorPiloto("acceso_o_metadatos_requieren_revision") from None


def _ejecutar(raiz, *, asset_id, tamano_esperado, sha256_esperado, fuente_esperada, cancelacion):
    evento = cancelacion if cancelacion is not None else Event()
    _cancelado(evento)
    if not Path(raiz).is_absolute():
        raise ErrorPiloto("raiz_no_admitida")
    raiz = _segura(Path(raiz))
    if not raiz.is_absolute() or not raiz.is_dir():
        raise ErrorPiloto("raiz_no_admitida")
    if (type(tamano_esperado) is not int or not 0 < tamano_esperado <= 134_217_728
            or type(sha256_esperado) is not str or len(sha256_esperado) != 64
            or any(c not in "0123456789abcdef" for c in sha256_esperado)
            or not isinstance(fuente_esperada, Fuente)):
        raise ErrorPiloto("identidad_esperada_no_admitida")
    db = raiz / "catalogo.sqlite3"
    _sin_auxiliares(raiz, db)
    antes_db = _huella(db, 1_048_576, evento)
    antes_raw = None
    ruta = None
    resultado = None
    try:
        activo, evidencia = _consultar_activo(db, asset_id)
        if (activo.asset_id != asset_id or activo.estado is not EstadoIncorporacion.INCORPORADA
                or activo.error is not None or activo.declaracion.fuente != fuente_esperada
                or activo.declaracion.formato_declarado != "csv"
                or activo.tamano != tamano_esperado or activo.sha256 != sha256_esperado
                or activo.ruta_interna != f"sha256/{sha256_esperado[:2]}/{sha256_esperado}"):
            raise ErrorPiloto("identidad_catalogada_no_corresponde")
        _cancelado(evento)
        ruta = raiz / "sha256" / sha256_esperado[:2] / sha256_esperado
        antes_raw = _huella(ruta, tamano_esperado, evento)
        if antes_raw[:2] != (tamano_esperado, sha256_esperado):
            raise ErrorPiloto("integridad_previa_no_coincide")
        doc = evidencia.documento
        if doc.producto_id is None or doc.procedencia is None:
            raise ErrorPiloto("procedencia_documental_insuficiente")
        c = RecursoCatalogo(doc.fuente, doc.producto_id, doc.recurso_id,
            evidencia.url_solicitada, doc.procedencia, doc.referencia_publicacion,
            formato=activo.declaracion.formato_declarado,
            tipo_medio=activo.declaracion.tipo_medio_declarado,
            licencia_declarada=doc.licencia_declarada, referencia_licencia=doc.referencia_licencia)
        base = f"paso84c-local:{asset_id}"
        descripcion_catalogo = adaptar_catalogo(c, revision_metadatos=base + ":catalogo", documento=doc)
        consulta = ConsultaLocal(("CANDARAVE",), ("TEMP", "HR", "PP"), date(2015, 1, 1), date(2015, 1, 1))
        limites = LimitesConsulta(max_resultados=6, lectura=PoliticaLecturaCSV(
            max_bytes_archivo=tamano_esperado, tamano_bloque=65_536, max_bytes_muestra=65_536,
            max_registros=33))  # Encabezado + hasta 32 filas; no búsqueda integral.
        proc = ProcedenciaLocal(c.fuente, c.identificador, activo.asset_id, activo.sha256)
        adaptaciones = []
        with ConsultorLocalCSV(ruta, consulta, proc, limites=limites, cancelacion=evento) as operacion:
            for o in operacion:
                _cancelado(evento)
                a = adaptar_meteorologia(c, revision_metadatos=base + f":registro-{o.numero_registro}:{o.variable}",
                                        observacion=o)
                if a.recurso is None or a.recurso.contradicciones_declaradas:
                    raise ErrorPiloto("adaptacion_requiere_revision")
                adaptaciones.append(a)
        _cancelado(evento)
        lectura = operacion.informe
        if (len(adaptaciones) != 6 or lectura.fechas_invalidas or lectura.lectura.registros_problematicos
                or lectura.motivo_fin != "limite_resultados"):
            raise ErrorPiloto("muestra_acotada_no_disponible")
        a, b = adaptaciones[0].recurso, adaptaciones[3].recurso
        espacial = evaluar_operacion(a, b, OperacionPropuesta("preparacion_espacial_con_precision", D.ESPACIAL, True))
        temporal = evaluar_operacion(a, b, OperacionPropuesta("comparacion_temporal_propuesta", D.TEMPORAL, False))
        if evaluar_operacion(a, b, temporal.operacion) != temporal:
            raise ErrorPiloto("evaluacion_no_reproducible")
        resultado = dict(activo=activo, evidencia=evidencia, catalogo=descripcion_catalogo,
                         adaptaciones=tuple(adaptaciones), espacial=espacial, temporal=temporal,
                         consulta=lectura, antes_raw=antes_raw, antes_catalogo=antes_db)
    except (OSError, sqlite3.Error, ValueError, TypeError, KeyError):
        raise ErrorPiloto("acceso_o_metadatos_requieren_revision") from None
    finally:
        # Se ejecuta también tras cancelación, error del consumidor o KeyboardInterrupt.
        # La comprobación de cierre no se cancela: puede requerir otra lectura binaria.
        try:
            final = Event()
            despues_raw = _huella(ruta, tamano_esperado, final) if antes_raw is not None else None
            despues_db = _huella(db, 1_048_576, final)
            _sin_auxiliares(raiz, db)
            if despues_db != antes_db or antes_raw is not None and despues_raw != antes_raw:
                raise ErrorPiloto("integridad_posterior_no_coincide")
            if resultado is not None:
                resultado.update(despues_raw=despues_raw, despues_catalogo=despues_db)
        except (OSError, sqlite3.Error, ValueError, TypeError):
            raise ErrorPiloto("integridad_posterior_no_disponible") from None
    return resultado
