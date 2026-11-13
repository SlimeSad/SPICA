"""Perfiles RC2 y comparación documental sin efectos ni autorización."""

from .modelos import (
    VERSION_PERFILES, AspectoCampo, CampoInformacion, DeclaracionPerfil,
    EntradaPerfil, EstadoUnidad, FinalidadCompatibilidad, PerfilInformacion,
    ResultadoCompatibilidad, UnidadPerfil,
)
from .comparador import comparar_perfiles

__all__ = [
    "VERSION_PERFILES", "AspectoCampo", "CampoInformacion", "DeclaracionPerfil",
    "EntradaPerfil", "EstadoUnidad", "FinalidadCompatibilidad", "PerfilInformacion",
    "ResultadoCompatibilidad", "UnidadPerfil", "comparar_perfiles",
]
