"""Paquete MANUAL v2 en el diario existente; sin campos ni pruebas HTTP."""

from dataclasses import asdict
from datetime import date
import json

from ..almacenamiento.modelos import DeclaracionRAW, ErrorAlmacenamientoRAW
from ..nucleo import Fuente
from .modelos import (
    DocumentoManual, FundamentoUsoManual, ProcedenciaManual, ReciboIngestaManual,
    FUENTE_RECEPCION_LOCAL, identificador,
)


def validar_procedencia(documento):
    from ..catalogo.persistencia import _publico
    if type(documento) is not ProcedenciaManual:
        raise TypeError("Procedencia manual tipada requerida")
    _publico(documento)
    if documento.fundamento.permite_incorporacion is not True or documento.fundamento.documento is None:
        raise ErrorAlmacenamientoRAW("fundamento_de_uso_insuficiente")


def datos_procedencia(documento):
    # Solo dataclasses conocidas; no lectores, rutas, callbacks ni serializadores externos.
    datos = asdict(documento)
    datos["documentos"] = list(datos["documentos"])
    datos["fundamento"]["restricciones"] = list(datos["fundamento"]["restricciones"])
    for campo in ("fecha_recepcion", "fecha_recurso"):
        datos[campo] = getattr(documento, campo).isoformat() if getattr(documento, campo) else None
    docs = [datos["fundamento"]["documento"], *datos["documentos"]]
    for doc in docs:
        if doc is not None and doc["fecha"] is not None:
            doc["fecha"] = doc["fecha"].isoformat()
    return datos


def empaquetar_manual(documento, declaracion, adquisicion_id):
    validar_procedencia(documento)
    identificador(adquisicion_id)
    if type(declaracion) is not DeclaracionRAW:
        raise TypeError("Declaración RAW requerida")
    if (declaracion.fuente != (documento.fuente_declarada or FUENTE_RECEPCION_LOCAL)
            or declaracion.procedencia is not None or dict(declaracion.parametros_publicos)
            or declaracion.formato_declarado != documento.formato_declarado
            or declaracion.tipo_medio_declarado != documento.tipo_medio_declarado):
        raise ErrorAlmacenamientoRAW("declaracion_manual_no_coincidente")
    paquete = dict(version=2, mecanismo="importacion_manual", adquisicion_id=adquisicion_id,
                   documento=datos_procedencia(documento))
    if len(json.dumps(paquete, ensure_ascii=False).encode("utf-8")) > 60_000:
        raise ValueError("Evidencia manual superior al presupuesto")
    return paquete


def desempaquetar_manual(datos, activo):
    if set(datos) != {"version", "mecanismo", "adquisicion_id", "documento"}:
        raise ValueError("Paquete manual no admitido")
    def leer_documento(d):
        if d is None:
            return None
        d = dict(d)
        if d["fecha"] is not None:
            d["fecha"] = date.fromisoformat(d["fecha"])
        return DocumentoManual(**d)
    d = dict(datos["documento"])
    if d["fuente_declarada"] is not None:
        d["fuente_declarada"] = Fuente(**d["fuente_declarada"])
    for campo in ("fecha_recepcion", "fecha_recurso"):
        if d[campo] is not None:
            d[campo] = date.fromisoformat(d[campo])
    fundamento = dict(d["fundamento"])
    fundamento["documento"] = leer_documento(fundamento["documento"])
    fundamento["restricciones"] = tuple(fundamento["restricciones"])
    d["fundamento"] = FundamentoUsoManual(**fundamento)
    d["documentos"] = tuple(leer_documento(doc) for doc in d["documentos"])
    documento = ProcedenciaManual(**d)
    if empaquetar_manual(documento, activo.declaracion, datos["adquisicion_id"]) != datos:
        raise ValueError("Evidencia manual contradictoria")
    if (documento.sha256_externo is not None and activo.sha256 is not None
            and documento.sha256_externo != activo.sha256):
        raise ValueError("Hash externo contradictorio con el activo")
    return ReciboIngestaManual(datos["adquisicion_id"], activo, documento)
