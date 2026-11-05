"""Inspección DOCX local, acotada y sin integración operativa HTTP/RAW."""

from .modelos import (
    CeldaDOCX, ConsumoDOCX, DiagnosticoDOCX, EstadoInspeccionDOCX, FilaDOCX,
    IdentidadDOCX, LimitesDOCX, ParrafoDOCX, ParteDOCX, PropiedadDOCX,
    ReferenciaDOCX, RelacionDOCX, ResultadoDOCX, TablaDOCX,
)
from .inspector import inspeccionar_docx_archivo, inspeccionar_docx_bytes

__all__ = [
    "CeldaDOCX", "ConsumoDOCX", "DiagnosticoDOCX", "EstadoInspeccionDOCX", "FilaDOCX",
    "IdentidadDOCX", "LimitesDOCX", "ParrafoDOCX", "ParteDOCX", "PropiedadDOCX",
    "ReferenciaDOCX", "RelacionDOCX", "ResultadoDOCX", "TablaDOCX",
    "inspeccionar_docx_archivo", "inspeccionar_docx_bytes",
]
