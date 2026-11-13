"""RC3: inspección offline de composiciones acotadas, sin ejecutor automático."""

from .modelos import (
    VERSION_COORDINACION, CierreQA, ComposicionOperaciones, DependenciaOperacion,
    InformeComposicion, InspeccionOperacion, LimitesComposicion, NodoOperacion,
    RequisitoCompatibilidad, RestriccionPropagada,
)
from .inspeccion import inspeccionar_composicion

__all__ = [
    "VERSION_COORDINACION", "CierreQA", "ComposicionOperaciones", "DependenciaOperacion",
    "InformeComposicion", "InspeccionOperacion", "LimitesComposicion", "NodoOperacion",
    "RequisitoCompatibilidad", "RestriccionPropagada", "inspeccionar_composicion",
]
