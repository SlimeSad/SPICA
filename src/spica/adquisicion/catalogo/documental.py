"""Registro documental explícito sobre el catálogo y su historial existentes.

Los recursos usan el diario ``revisiones`` (tabla lógica ``recursos``), sin DDL
ni migración. No son disponibilidades ni capacidades del producto completo.
"""

from dataclasses import dataclass
from enum import Enum
import json
import sqlite3

from ..nucleo import Fuente
from .modelos import (
    CapacidadCatalogo, ErrorCatalogo, FuenteCatalogo, ProductoCatalogo,
    ProcedenciaCatalogo, RegistroCatalogo, _Entidad,
)


class EstadoRegistroDocumental(Enum):
    NUEVO = "nuevo"
    IDENTICO = "identico"
    REVISION_DOCUMENTAL = "revision_documental"
    CONTRADICCION = "contradiccion_requiere_evaluacion"


@dataclass(frozen=True)
class RecursoCatalogo(_Entidad):
    fuente: Fuente
    producto_id: str
    identificador: str
    localizador: str
    procedencia: ProcedenciaCatalogo
    referencia_publicacion: str | None = None
    titulo: str | None = None
    formato: str | None = None
    tipo_medio: str | None = None
    licencia_declarada: str | None = None
    referencia_licencia: str | None = None

    def __post_init__(self):
        super().__post_init__()
        if not isinstance(self.localizador, str) or not self.localizador.strip():
            raise ValueError("Se requiere localizador público")


@dataclass(frozen=True)
class RegistroRecurso:
    entidad: RecursoCatalogo
    revision: int


@dataclass(frozen=True)
class ResultadoRegistroDocumental:
    estado: EstadoRegistroDocumental
    registro: RegistroCatalogo | RegistroRecurso
    motivo: str | None = None


def _clave_recurso(fuente, producto_id, recurso_id):
    return dict(proveedor=fuente.proveedor, fuente_id=fuente.identificador,
                producto_id=producto_id, identificador=recurso_id)


def _leer_recurso(contenido):
    from .persistencia import _leer_json
    datos = _leer_json(contenido)
    datos["fuente"] = Fuente(**datos["fuente"])
    datos["procedencia"] = ProcedenciaCatalogo(**datos["procedencia"])
    return RecursoCatalogo(**datos)


def consultar_recurso(catalogo, fuente, producto_id, recurso_id, revision=None):
    clave = _clave_recurso(fuente, producto_id, recurso_id)
    return consultar_revision(catalogo, "recursos", clave, revision)


def consultar_revision(catalogo, tabla, clave, revision):
    from .persistencia import _entidad
    if revision is not None and (type(revision) is not int or revision <= 0):
        raise ValueError("Se requiere revisión positiva")
    sql = "SELECT contenido,revision FROM revisiones WHERE tabla=? AND clave=?"
    valores = [tabla, json.dumps(clave, sort_keys=True)]
    if revision is not None:
        sql += " AND revision=?"
        valores.append(revision)
    fila = catalogo._conexion.execute(sql + " ORDER BY revision DESC LIMIT 1", valores).fetchone()
    if fila is None:
        raise ErrorCatalogo("revision_documental_no_identificada")
    entidad = _leer_recurso(fila[0]) if tabla == "recursos" else _entidad(tabla, fila[0])
    return (RegistroRecurso if tabla == "recursos" else RegistroCatalogo)(entidad, fila[1])


def _comparable(entidad):
    from .persistencia import _datos
    datos = _datos(entidad)
    # Otra fecha de consulta no constituye por sí sola un documento distinto.
    datos["procedencia"].pop("revisada_utc")
    if isinstance(entidad, FuenteCatalogo):
        datos.pop("revisada_utc")
    return datos


def _material(anterior, nueva):
    protegidos = {
        FuenteCatalogo: ("nombre", "tipo_organizacion", "estado"),
        ProductoCatalogo: ("familia", "modalidad_acceso", "autenticacion_requerida", "utiliza_estaciones"),
        RecursoCatalogo: ("localizador", "formato", "tipo_medio"),
        CapacidadCatalogo: ("mecanismo", "estado", "otro_mecanismo"),
    }
    return any(getattr(anterior, c) is not None and getattr(anterior, c) != getattr(nueva, c)
               for c in protegidos[type(nueva)])


def registrar_documental(catalogo, entidad):
    from .persistencia import _TABLAS, _clave, _datos, _publico
    if type(entidad) not in (FuenteCatalogo, ProductoCatalogo, RecursoCatalogo, CapacidadCatalogo):
        raise TypeError("Tipo no admitido por la política documental")
    _publico(entidad)
    recurso = isinstance(entidad, RecursoCatalogo)
    tabla = "recursos" if recurso else _TABLAS[type(entidad)]
    clave = (_clave_recurso(entidad.fuente, entidad.producto_id, entidad.identificador)
             if recurso else _clave(entidad))
    # Una sola transacción de catálogo para decisión, revisión y diario. El
    # transporte, el catálogo RAW y los archivos no participan en ella.
    if catalogo._conexion.in_transaction:
        raise ErrorCatalogo("registro_documental_requiere_conexion_sin_transaccion")
    catalogo._conexion.execute("BEGIN IMMEDIATE")
    try:
        if recurso:
            fila = catalogo._conexion.execute(
                "SELECT contenido,revision FROM revisiones WHERE tabla=? AND clave=? ORDER BY revision DESC LIMIT 1",
                (tabla, json.dumps(clave, sort_keys=True))).fetchone()
            anterior = RegistroRecurso(_leer_recurso(fila[0]), fila[1]) if fila else None
        else:
            fila = catalogo._fila(tabla, clave)
            anterior = catalogo._consultar(tabla, clave) if fila else None
        estado = EstadoRegistroDocumental.NUEVO
        if anterior is not None:
            if _comparable(anterior.entidad) == _comparable(entidad):
                catalogo._conexion.rollback()
                return ResultadoRegistroDocumental(EstadoRegistroDocumental.IDENTICO, anterior)
            motivo = ("cambio_material_requiere_evaluacion" if _material(anterior.entidad, entidad)
                      else "procedencia_no_posterior" if entidad.procedencia.revisada_utc <= anterior.entidad.procedencia.revisada_utc
                      else None)
            if motivo:
                catalogo._conexion.rollback()
                return ResultadoRegistroDocumental(EstadoRegistroDocumental.CONTRADICCION, anterior, motivo)
            estado = EstadoRegistroDocumental.REVISION_DOCUMENTAL
        revision = anterior.revision + 1 if anterior else 1
        if recurso:
            # El vínculo al producto se comprueba antes de insertar en el diario.
            catalogo.consultar_producto(entidad.fuente, entidad.producto_id)
            from datetime import datetime, timezone
            catalogo._conexion.execute(
                "INSERT INTO revisiones(tabla,clave,revision,contenido,registrada_utc,motivo) VALUES (?,?,?,?,?,?)",
                (tabla, json.dumps(clave, sort_keys=True), revision,
                 json.dumps(_datos(entidad), ensure_ascii=False, sort_keys=True),
                 datetime.now(timezone.utc).isoformat(), estado.value))
            registro = RegistroRecurso(entidad, revision)
        else:
            registro = catalogo._guardar(entidad, anterior.revision if anterior else None,
                                        estado.value, transaccion_externa=True)
        catalogo._conexion.commit()
        return ResultadoRegistroDocumental(estado, registro)
    except sqlite3.Error:
        catalogo._conexion.rollback()
        from ..almacenamiento._errores import _publicar
        _publicar(ErrorCatalogo("persistencia_documental_no_disponible"))
    except BaseException:
        catalogo._conexion.rollback()
        raise
