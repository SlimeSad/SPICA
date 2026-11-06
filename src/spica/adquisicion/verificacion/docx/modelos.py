"""Contratos del inspector DOCX offline; no acreditan autenticidad o ciencia."""

from dataclasses import dataclass, field, fields
from enum import Enum
import math

from ..modelos import PoliticaEstructura


VERSION_INSPECTOR = "0.2.0"


class EstadoInspeccionDOCX(Enum):
    DOCUMENTO_VALIDADO_EN_ALCANCE = "DOCUMENTO_VALIDADO_EN_ALCANCE"
    DOCUMENTO_RECHAZADO = "DOCUMENTO_RECHAZADO"
    INSPECCION_INCOMPLETA = "INSPECCION_INCOMPLETA"


def _zip_predeterminado():
    return PoliticaEstructura(max_entradas_zip=128, max_central_zip=131_072,
        max_bytes_descomprimidos=16_777_216, max_bytes_entrada=2_097_152,
        max_expansion=100, max_bytes_xml=2_097_152, max_nodos_xml=100_000,
        max_profundidad_xml=32, tamano_bloque=65_536)


@dataclass(frozen=True)
class LimitesDOCX:
    zip: PoliticaEstructura = field(default_factory=_zip_predeterminado)
    max_archivo: int = 4_194_304
    max_xml: int = 64
    max_lecturas_zip: int = 33_554_432
    max_bytes_auxiliares: int = 8_388_608
    max_parrafos: int = 10_000
    max_tablas: int = 100
    max_celdas: int = 10_000
    max_texto_fragmento: int = 8192
    max_texto_total: int = 524_288
    max_referencias: int = 2048
    max_estilos: int = 512
    max_propiedades: int = 128
    max_diagnosticos: int = 64
    max_segundos: float = 5.0

    def __post_init__(self):
        if type(self.zip) is not PoliticaEstructura:
            raise TypeError("politica_zip_requerida")
        for f in fields(self):
            v = getattr(self, f.name)
            if f.name == "zip":
                continue
            if f.name == "max_segundos":
                if type(v) not in (int, float) or not math.isfinite(v) or not 0 < v <= 60:
                    raise ValueError("plazo_no_admitido")
            elif type(v) is not int or not 0 < v <= 67_108_864:
                raise ValueError("limite_positivo_acotado_requerido")
        if (self.max_archivo > 16_777_216 or self.max_xml > 256
                or self.max_parrafos > 20_000 or self.max_celdas > 20_000
                or self.max_tablas > 1000 or self.max_referencias > 4096
                or self.max_estilos > 2048 or self.max_propiedades > 512
                or self.max_texto_fragmento > 65_536 or self.max_texto_total > 2_097_152
                or self.max_diagnosticos > 256 or self.zip.max_entradas_zip > 1024
                or self.zip.max_central_zip > 2_097_152
                or self.zip.max_bytes_entrada > 4_194_304
                or self.zip.max_bytes_xml > 4_194_304
                or self.zip.max_bytes_descomprimidos > 67_108_864
                or self.zip.max_nodos_xml > 200_000 or self.zip.max_profundidad_xml > 64):
            raise ValueError("politica_fuera_del_perfil_acotado")


@dataclass(frozen=True)
class IdentidadDOCX:
    identificador: str
    origen: str  # memoria o archivo; nunca se publica automáticamente la ruta.
    tamano: int
    sha256: str | None


@dataclass(frozen=True)
class ReferenciaDOCX:
    archivo_id: str
    sha256: str
    parte: str
    ruta_xml: str  # Clark: /{namespace}elemento[ordinal entre hermanos]/...
    parrafo: int | None = None
    tabla: int | None = None
    fila: int | None = None
    columna: int | None = None  # ordinal de w:tc, no columna de una grilla renderizada.


@dataclass(frozen=True)
class ParteDOCX:
    nombre: str
    tipo_medio: str | None
    bytes_comprimidos: int
    bytes_declarados: int
    bytes_observados: int
    crc32: str


@dataclass(frozen=True)
class RelacionDOCX:
    parte_relaciones: str
    identificador: str
    tipo: str
    destino: str


@dataclass(frozen=True)
class HipervinculoOmitidoDOCX:
    """Destino externo descartado; solo procedencia y usos del XML local."""
    parte_relaciones: str
    identificador: str
    tipo: str
    target_mode: str
    parte_origen: str
    tipo_destino: str  # http, https o mailto; nunca una URI o dirección.
    referencias: tuple[ReferenciaDOCX, ...]


@dataclass(frozen=True)
class ParrafoDOCX:
    referencia: ReferenciaDOCX
    texto: str = field(repr=False)
    origen: str = "cuerpo"
    estilo_id: str | None = None
    titulo_por_estilo: bool = False


@dataclass(frozen=True)
class CeldaDOCX:
    referencia: ReferenciaDOCX
    parrafos: tuple[ParrafoDOCX, ...]
    tablas_anidadas: tuple[str, ...] = ()
    grid_span: str | None = None
    vmerge: str | None = None

    @property
    def texto(self):
        """Representación con LF entre párrafos; el literal está en cada párrafo."""
        return "\n".join(p.texto for p in self.parrafos)


@dataclass(frozen=True)
class FilaDOCX:
    indice: int
    celdas: tuple[CeldaDOCX, ...]


@dataclass(frozen=True)
class TablaDOCX:
    referencia: ReferenciaDOCX
    filas: tuple[FilaDOCX, ...]


@dataclass(frozen=True)
class PropiedadDOCX:
    referencia: ReferenciaDOCX
    nombre: str
    valor: str = field(repr=False)
    naturaleza: str = "propiedad_tecnica_editable_no_vigencia_editorial"


@dataclass(frozen=True)
class DiagnosticoDOCX:
    codigo: str
    parte: str | None = None
    ruta_xml: str | None = None


@dataclass(frozen=True)
class ConsumoDOCX:
    bytes_zip_verificacion: int = 0
    bytes_zip_extraccion: int = 0
    bytes_descomprimidos_verificacion: int = 0
    bytes_descomprimidos_extraccion: int = 0
    xml_procesados: int = 0  # segunda pasada; la primera también está acotada.
    nodos_xml: int = 0
    bytes_auxiliares_pico: int = 0  # carga contable, no RSS del intérprete.
    bytes_zip_preflight: int = 0


@dataclass(frozen=True)
class ResultadoDOCX:
    estado: EstadoInspeccionDOCX
    identidad: IdentidadDOCX | None
    limites: LimitesDOCX
    partes: tuple[ParteDOCX, ...] = ()
    relaciones: tuple[RelacionDOCX, ...] = ()
    parrafos: tuple[ParrafoDOCX, ...] = ()
    tablas: tuple[TablaDOCX, ...] = ()
    propiedades: tuple[PropiedadDOCX, ...] = ()
    advertencias: tuple[DiagnosticoDOCX, ...] = ()
    causas_rechazo: tuple[DiagnosticoDOCX, ...] = ()
    operaciones_omitidas: tuple[DiagnosticoDOCX, ...] = ()
    conservacion_comprobada: bool | None = None
    consumo: ConsumoDOCX = field(default_factory=ConsumoDOCX)
    version_inspector: str = field(default=VERSION_INSPECTOR, init=False)
    hipervinculos_omitidos: tuple[HipervinculoOmitidoDOCX, ...] = ()

    def diagnostico_publico(self):
        """Sin texto, rutas locales, relaciones recibidas o metadatos personales."""
        return dict(estado=self.estado.value, version=self.version_inspector,
            tamano=self.identidad.tamano if self.identidad else None,
            sha256=self.identidad.sha256 if self.identidad else None,
            partes=len(self.partes), parrafos=len(self.parrafos), tablas=len(self.tablas),
            hipervinculos_omitidos=len(self.hipervinculos_omitidos),
            causas=tuple(d.codigo for d in self.causas_rechazo),
            omitidas=tuple(d.codigo for d in self.operaciones_omitidas))
