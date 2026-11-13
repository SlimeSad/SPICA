"""Contextos RC1 en memoria; configuración, identidad y evidencia no son permisos."""

from .modelos import (
    ConfiguracionContexto, ContextoProyecto, ContextoEntrada, ContextoOperacion,
    EstadoOperacion, TipoOperacion, VERSION_CONTEXTO, PERFIL_QA0,
    combinar_restricciones,
)
from .relaciones import validar_relaciones, cambiar_estado
from .adaptadores_qa import contexto_exportacion_qa, VinculoResultadoQA, validar_vinculos_qa

__all__ = [
    "ConfiguracionContexto", "ContextoProyecto", "ContextoEntrada", "ContextoOperacion",
    "EstadoOperacion", "TipoOperacion", "VERSION_CONTEXTO", "PERFIL_QA0",
    "combinar_restricciones", "validar_relaciones", "cambiar_estado",
    "contexto_exportacion_qa", "VinculoResultadoQA", "validar_vinculos_qa",
]
