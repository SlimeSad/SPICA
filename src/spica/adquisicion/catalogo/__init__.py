"""Catálogo de descubrimiento, separado de los originales RAW."""

from .modelos import (
    CapacidadCatalogo, CoincidenciaTemporal, DisponibilidadCatalogo, EntidadCatalogo,
    ErrorCatalogo, EstacionCatalogo, EstadoVerificacion, EvaluacionDisponibilidad,
    FiltroCatalogo, FuenteCatalogo, MecanismoAdquisicion, ProcedenciaCatalogo,
    ProductoCatalogo, RegistroCatalogo, ResultadoCatalogo, ResultadoProducto, VariableCatalogo,
)
from .persistencia import CatalogoCientifico

__all__ = [
    "CapacidadCatalogo", "CatalogoCientifico", "CoincidenciaTemporal", "DisponibilidadCatalogo",
    "EntidadCatalogo", "ErrorCatalogo", "EstacionCatalogo", "EstadoVerificacion",
    "EvaluacionDisponibilidad", "FiltroCatalogo", "FuenteCatalogo", "MecanismoAdquisicion",
    "ProcedenciaCatalogo", "ProductoCatalogo", "RegistroCatalogo", "ResultadoCatalogo",
    "ResultadoProducto", "VariableCatalogo",
]
