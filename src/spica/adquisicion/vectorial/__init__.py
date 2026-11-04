"""Prototipo vectorial exclusivamente sintético: no es un conector HTTP."""

from .modelos import (
    CampoVector, ConsultaVector, ContratoFeatureSet, EntidadVector, EstadoCompletitud,
    EstadoGeometria, EstadoPagina, EstrategiaPaginacion, EvidenciaConjunto,
    LimitesVector, PaginaValidada, RecursoVector, ReferenciaEspacial,
    RespuestaSintetica, ResultadoVector, SolicitudPagina, TipoCampo,
)
from .validador import validar_featureset
from .coordinador import coordinar
from .simulado import TransporteSintetico

__all__ = [
    "CampoVector", "ConsultaVector", "ContratoFeatureSet", "EntidadVector",
    "EstadoCompletitud", "EstadoGeometria", "EstadoPagina", "EstrategiaPaginacion",
    "EvidenciaConjunto", "LimitesVector", "PaginaValidada", "RecursoVector",
    "ReferenciaEspacial", "RespuestaSintetica", "ResultadoVector", "SolicitudPagina",
    "TipoCampo", "TransporteSintetico", "validar_featureset", "coordinar",
]
