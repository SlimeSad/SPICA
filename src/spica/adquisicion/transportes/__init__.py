"""Transportes comunes, independientes de los conectores y modelos científicos."""

from .http import (
    ClienteHTTP, ConfiguracionHTTP, ErrorTransporteHTTP, RespuestaHTTP, TipoErrorHTTP,
)
from .descargas import ErrorDescargaArchivo, InformeDescarga

__all__ = [
    "ClienteHTTP", "ConfiguracionHTTP", "ErrorTransporteHTTP", "RespuestaHTTP", "TipoErrorHTTP",
    "ErrorDescargaArchivo", "InformeDescarga",
]
