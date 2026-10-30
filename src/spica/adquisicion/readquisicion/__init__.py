"""Recomendaciones declarativas previas a adquirir; sin ejecución automática."""

from .modelos import (
    AntecedenteAdquisicion, Decision, EstadoActualizacion, EstadoLocal,
    EvidenciaActualizacion, EvidenciaLocal, IdentidadRecurso, IndiciosHTTP,
    ModoConsulta, PoliticaReadquisicion, RelacionActualizacion, RestriccionesAcceso,
    ResultadoDecision, SolicitudDecision, UsoPrevisto,
)
from .antecedentes import antecedente_desde_raw
from .motor import decidir_readquisicion

__all__ = [
    "AntecedenteAdquisicion", "Decision", "EstadoActualizacion", "EstadoLocal",
    "EvidenciaActualizacion", "EvidenciaLocal", "IdentidadRecurso", "IndiciosHTTP",
    "ModoConsulta", "PoliticaReadquisicion", "RelacionActualizacion", "RestriccionesAcceso",
    "ResultadoDecision", "SolicitudDecision", "UsoPrevisto", "antecedente_desde_raw",
    "decidir_readquisicion",
]
