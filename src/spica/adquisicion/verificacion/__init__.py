"""Comprobaciones estructurales locales acotadas, sin validación científica."""

from .modelos import DetalleCSV, EstadoEstructura, PoliticaEstructura, ResultadoEstructura
from .inspector import verificar_archivo
from .csv_streaming import LectorCSV, PoliticaLecturaCSV, RegistroCSV, DiagnosticoCSV, InformeLecturaCSV

__all__ = ["DetalleCSV", "EstadoEstructura", "PoliticaEstructura", "ResultadoEstructura", "verificar_archivo"]
__all__ += ["LectorCSV", "PoliticaLecturaCSV", "RegistroCSV", "DiagnosticoCSV", "InformeLecturaCSV"]
