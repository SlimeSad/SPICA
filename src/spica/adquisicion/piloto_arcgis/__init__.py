"""Preparación y ensayo exclusivamente sintéticos, sin ejecutor HTTP."""

from .modelos import (
    AutorizacionEnsayo, EscenarioSintetico, EstadoEnsayo, EstadoRecepcion,
    EstadoValidacion, FalloSintetico, PreparacionEnsayo, ResultadoEnsayo,
    SolicitudSimulada,
)
from .simulador import SimuladorEnsayo
from .evidencia import EvidenciaTemporal, ErrorEvidenciaEnsayo, conservar_evidencia

__all__ = [
    "AutorizacionEnsayo", "EscenarioSintetico", "EstadoEnsayo", "EstadoRecepcion",
    "EstadoValidacion", "FalloSintetico", "PreparacionEnsayo", "ResultadoEnsayo",
    "SolicitudSimulada", "SimuladorEnsayo", "EvidenciaTemporal", "ErrorEvidenciaEnsayo",
    "conservar_evidencia",
]
