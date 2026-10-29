"""Piloto SENAMHI–PNDA de recursos publicados; sin autenticación institucional."""

from .modelos import (
    ORIGEN_PNDA, PAGINA_GBON_RBON, PRODUCTO_GBON_RBON_ID, FUENTE_SENAMHI, RolRecurso,
    RecursoPublicado, CatalogoRecursos, AdquisicionPNDA, ErrorConectorPNDA,
)
from .pnda import ConectorSENAMHIPNDA

__all__ = [
    "ORIGEN_PNDA", "PAGINA_GBON_RBON", "PRODUCTO_GBON_RBON_ID", "FUENTE_SENAMHI", "RolRecurso",
    "RecursoPublicado", "CatalogoRecursos", "AdquisicionPNDA", "ErrorConectorPNDA",
    "ConectorSENAMHIPNDA",
]
