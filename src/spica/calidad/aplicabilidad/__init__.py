"""Diagnóstico documental de aplicabilidad, independiente de toda ejecución QA/QC."""

from .modelos import (
    AfirmacionAplicabilidad, AspectoAdicional, CondicionAdicional, DiagnosticoAplicabilidad,
    EspecificacionAplicabilidad, EstadoAplicabilidad, EstadoRequisito, EvidenciaDocumental,
    ExpedienteProducto, HallazgoAplicabilidad, NaturalezaEvidencia, NivelEvidencia,
    RequisitoAplicabilidad, TipoRequisito, VERSION_VERIFICADOR, VigenciaDocumento,
)
from .verificador import verificar_aplicabilidad

__all__ = [
    "AfirmacionAplicabilidad", "AspectoAdicional", "CondicionAdicional", "DiagnosticoAplicabilidad",
    "EspecificacionAplicabilidad", "EstadoAplicabilidad", "EstadoRequisito", "EvidenciaDocumental",
    "ExpedienteProducto", "HallazgoAplicabilidad", "NaturalezaEvidencia", "NivelEvidencia",
    "RequisitoAplicabilidad", "TipoRequisito", "VERSION_VERIFICADOR", "VigenciaDocumento",
    "verificar_aplicabilidad",
]
