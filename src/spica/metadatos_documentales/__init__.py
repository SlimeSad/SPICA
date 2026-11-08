"""Metadatos documentales experimentales offline, sin integración operativa."""

from .modelos import (
    AfirmacionDocumental, AspectoUso, ConstatacionAspecto, ExpedienteMetadatos,
    FormaDeclaracion, FuenteDocumental, LocalizadorDocumental, PresenciaInformacion,
    ReferenciaCelda, ReferenciaSeccion, RelacionAfirmaciones, RestriccionUso,
    TipoDocumento, TipoRelacion, VERSION_CONTRATO, localizar,
)
from .evaluacion import DiagnosticoUso, OperacionUso, ResultadoUso, evaluar_uso

__all__ = [
    "AfirmacionDocumental", "AspectoUso", "ConstatacionAspecto", "ExpedienteMetadatos",
    "FormaDeclaracion", "FuenteDocumental", "LocalizadorDocumental", "PresenciaInformacion",
    "ReferenciaCelda", "ReferenciaSeccion", "RelacionAfirmaciones", "RestriccionUso",
    "TipoDocumento", "TipoRelacion", "VERSION_CONTRATO", "localizar",
    "DiagnosticoUso", "OperacionUso", "ResultadoUso", "evaluar_uso",
]
