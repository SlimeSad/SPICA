"""Laboratorio de límites sobre fixtures; sin habilitación operativa de Nivel 1."""

from .limites import evaluar_limites_sinteticos
from .modelos import (
    EstadoLimiteExperimental, EvidenciaSintetica, ObservacionSintetica,
    ReglaLimitesSintetica, ResultadoLimiteSintetico, TipoEvidenciaExperimental,
    VERSION_EXPERIMENTAL,
)

__all__ = ["evaluar_limites_sinteticos", "EstadoLimiteExperimental", "EvidenciaSintetica",
    "ObservacionSintetica", "ReglaLimitesSintetica", "ResultadoLimiteSintetico",
    "TipoEvidenciaExperimental", "VERSION_EXPERIMENTAL"]
