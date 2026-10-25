"""Transportes comunes, independientes de los conectores y modelos científicos."""

from .http import (
    ClienteHTTP, ConfiguracionHTTP, ErrorTransporteHTTP, RespuestaHTTP, TipoErrorHTTP,
)

__all__ = [
    "ClienteHTTP", "ConfiguracionHTTP", "ErrorTransporteHTTP", "RespuestaHTTP", "TipoErrorHTTP",
]
