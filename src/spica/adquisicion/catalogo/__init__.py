"""Catálogo de descubrimiento, separado de los originales RAW."""

from .modelos import (
    CapacidadCatalogo, CoincidenciaTemporal, DisponibilidadCatalogo, EntidadCatalogo,
    ErrorCatalogo, EstacionCatalogo, EstadoVerificacion, EvaluacionDisponibilidad,
    FiltroCatalogo, FuenteCatalogo, MecanismoAdquisicion, ProcedenciaCatalogo,
    ProductoCatalogo, RegistroCatalogo, ResultadoCatalogo, ResultadoProducto, VariableCatalogo,
)
from .persistencia import CatalogoCientifico
from .documental import RecursoCatalogo, RegistroRecurso, EstadoRegistroDocumental, ResultadoRegistroDocumental
from .evidencias import EvidenciaDocumental, EvidenciaAdquisicion

__all__ = [
    "CapacidadCatalogo", "CatalogoCientifico", "CoincidenciaTemporal", "DisponibilidadCatalogo",
    "EntidadCatalogo", "ErrorCatalogo", "EstacionCatalogo", "EstadoVerificacion",
    "EvaluacionDisponibilidad", "FiltroCatalogo", "FuenteCatalogo", "MecanismoAdquisicion",
    "ProcedenciaCatalogo", "ProductoCatalogo", "RegistroCatalogo", "ResultadoCatalogo",
    "ResultadoProducto", "VariableCatalogo",
    "RecursoCatalogo", "RegistroRecurso", "EstadoRegistroDocumental", "ResultadoRegistroDocumental",
    "EvidenciaDocumental", "EvidenciaAdquisicion",
]
