"""Proyección pura de instantáneas existentes; no abre un almacén ni lo verifica."""

from ..almacenamiento.modelos import ActivoRAW
from ..catalogo.evidencias import EvidenciaAdquisicion
from ..catalogo.modelos import MecanismoAdquisicion, ProcedenciaCatalogo
from ..manual.modelos import ReciboIngestaManual
from .modelos import AntecedenteAdquisicion, EvidenciaLocal, IdentidadRecurso, IndiciosHTTP


def antecedente_desde_raw(activo: ActivoRAW, procedencia: ProcedenciaCatalogo, *,
                          evidencia: EvidenciaAdquisicion | ReciboIngestaManual | None = None,
                          local: EvidenciaLocal | None = None,
                          version_recurso: str | None = None) -> AntecedenteAdquisicion:
    """La versión del recurso y la comprobación local nunca se deducen del catálogo.

    `procedencia` documenta la obtención de la instantánea por el llamador.
    Una revisión documental HTTP no se convierte en versión del recurso.
    """
    if type(activo) is not ActivoRAW:
        raise TypeError("Instantánea RAW requerida")
    d = activo.declaracion
    fuente, producto, adquisicion, mecanismo, indicios = d.fuente, d.parametros_publicos.get("producto_id"), None, None, None
    version_doc, fecha_doc, recepcion, restricciones = None, None, None, ()
    publicar, redistribuir = None, None
    fecha_adquisicion = None
    if evidencia is not None:
        if type(evidencia) is EvidenciaAdquisicion:
            documento = evidencia.documento
            if (evidencia.activo_id != activo.asset_id or documento.fuente != d.fuente
                    or documento.recurso_id != d.recurso_id
                    or (producto is not None and producto != documento.producto_id)
                    or (evidencia.sha256, evidencia.size_bytes, evidencia.estado_raw)
                       != (activo.sha256, activo.size_bytes, activo.estado.value)
                    or evidencia.capacidades_http_verificadas != (MecanismoAdquisicion.HTTP_DIRECTO,)):
                raise ValueError("Evidencia HTTP no coincide con la instantánea RAW")
            producto, adquisicion, mecanismo = documento.producto_id, evidencia.adquisicion_id, MecanismoAdquisicion.HTTP_DIRECTO
            indicios = IndiciosHTTP(url_declarada=evidencia.url_solicitada)
            fecha_adquisicion = evidencia.http_comprobada_utc
        elif type(evidencia) is ReciboIngestaManual:
            from ..manual.evidencias import empaquetar_manual
            anterior = evidencia.activo
            if (anterior.asset_id != activo.asset_id or anterior.declaracion != d
                    or (anterior.sha256, anterior.size_bytes, anterior.estado)
                       != (activo.sha256, activo.size_bytes, activo.estado)):
                raise ValueError("Recibo manual no coincide con la instantánea RAW")
            doc = evidencia.procedencia
            empaquetar_manual(doc, d, evidencia.adquisicion_id)
            fuente, producto = doc.fuente_declarada, doc.producto_id
            adquisicion, mecanismo = evidencia.adquisicion_id, MecanismoAdquisicion.MANUAL
            fecha_adquisicion, recepcion = activo.fecha_utc, doc.fecha_recepcion
            fundamento = doc.fundamento.documento
            if fundamento:
                version_doc, fecha_doc = fundamento.version, fundamento.fecha
            restricciones = doc.fundamento.restricciones
            publicar, redistribuir = doc.fundamento.permite_publicacion, doc.fundamento.permite_redistribucion
        else:
            raise TypeError("Evidencia de adquisición no admitida")
    identidad = IdentidadRecurso(d.proyecto_id, d.objeto_id, d.recurso_id, fuente, producto)
    return AntecedenteAdquisicion(identidad, procedencia, adquisicion_id=adquisicion,
        activo_id=activo.asset_id, mecanismo=mecanismo, estado_raw=activo.estado,
        interrumpida=activo.error == "interrumpida", fecha_adquisicion=fecha_adquisicion,
        fecha_incorporacion_raw=activo.fecha_utc, fecha_recepcion_civil=recepcion,
        sha256_catalogado=activo.sha256, size_bytes_catalogado=activo.size_bytes,
        local=local if local is not None else EvidenciaLocal(), version_recurso=version_recurso,
        version_documental=version_doc, fecha_documental=fecha_doc, indicios_http=indicios,
        restricciones_historicas=restricciones, permite_publicar_historico=publicar,
        permite_redistribuir_historico=redistribuir)
