"""Referencias públicas de productos y recursos PNDA; sin modelos de observaciones."""

from dataclasses import dataclass
from enum import Enum

from ...catalogo import ProductoCatalogo, ProcedenciaCatalogo, CapacidadCatalogo
from ...nucleo import Fuente, RecursoDescubierto
from ...integracion import ResultadoHTTPRAW


ORIGEN_PNDA = "https://www.datosabiertos.gob.pe"
PAGINA_GBON_RBON = (
    ORIGEN_PNDA + "/dataset/variables-meteorologicas-de-las-estaciones-autom%C3%A1ticas-"
    "de-intercambio-internacional-servicio"
)
PRODUCTO_GBON_RBON_ID = PAGINA_GBON_RBON.rsplit("/", 1)[1]
FUENTE_SENAMHI = Fuente("SENAMHI", "SENAMHI")


class RolRecurso(Enum):
    DICCIONARIO = "diccionario"
    METADATOS = "metadatos"
    PUBLICADO = "publicado_sin_clasificar"


@dataclass(frozen=True)
class RecursoPublicado:
    producto_id: str
    recurso: RecursoDescubierto
    referencia_publicacion: str
    href_original: str
    titulo: str | None
    rol: RolRecurso
    procedencia: ProcedenciaCatalogo


@dataclass(frozen=True)
class CatalogoRecursos:
    producto: ProductoCatalogo
    recursos: tuple[RecursoPublicado, ...]
    advertencias: tuple[str, ...]

    @property
    def filtros_remotos_verificados(self) -> bool:
        return False


@dataclass(frozen=True)
class AdquisicionPNDA:
    recurso: RecursoPublicado
    resultado_raw: ResultadoHTTPRAW
    capacidad_recurso: CapacidadCatalogo

    @property
    def estructura(self):
        return self.resultado_raw.estructura

    @property
    def utilizable_documentalmente(self) -> bool:
        return self.resultado_raw.utilizable_documentalmente

    @property
    def validacion_cientifica(self):
        return None


class ErrorConectorPNDA(Exception):
    """Códigos públicos sin HTML, URL rechazada ni valores sensibles."""
