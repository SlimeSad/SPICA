"""Ingesta local declarada; sin transporte de red ni interpretación científica."""

from .modelos import (
    AutenticidadManual, DocumentoManual, ErrorIngestaManual, EstadoIngestaManual,
    FundamentoUsoManual, IntegridadManual, PoliticaIngestaManual, ProcedenciaManual,
    ReciboIngestaManual, ResultadoIngestaManual, SolicitudIngestaManual,
)
from .ingesta import IngestorManual

__all__ = [
    "AutenticidadManual", "DocumentoManual", "ErrorIngestaManual", "EstadoIngestaManual",
    "FundamentoUsoManual", "IntegridadManual", "PoliticaIngestaManual", "ProcedenciaManual",
    "ReciboIngestaManual", "ResultadoIngestaManual", "SolicitudIngestaManual", "IngestorManual",
]
