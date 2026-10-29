"""Comprobaciones estructurales locales acotadas, sin validación científica."""

from .modelos import DetalleCSV, EstadoEstructura, PoliticaEstructura, ResultadoEstructura
from .inspector import verificar_archivo

__all__ = ["DetalleCSV", "EstadoEstructura", "PoliticaEstructura", "ResultadoEstructura", "verificar_archivo"]
