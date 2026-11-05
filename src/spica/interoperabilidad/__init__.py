"""Preparación documental espacial/temporal, exclusivamente offline."""

from .modelos import (
    AmbitoCRS, CRSDeclarado, DimensionEvaluacion, EstadoAptitud, IdentidadRecurso,
    MarcoEspacial, MarcoTemporal, PeriodoTemporal, RecursoInteroperable,
    RepresentacionEspacial, Respaldo, ResultadoAptitud, VERSION_EVALUADOR,
)
from .evaluador import evaluar_aptitud

__all__ = [
    "AmbitoCRS", "CRSDeclarado", "DimensionEvaluacion", "EstadoAptitud", "IdentidadRecurso",
    "MarcoEspacial", "MarcoTemporal", "PeriodoTemporal", "RecursoInteroperable",
    "RepresentacionEspacial", "Respaldo", "ResultadoAptitud", "VERSION_EVALUADOR", "evaluar_aptitud",
]
