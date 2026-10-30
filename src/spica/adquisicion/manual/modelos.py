"""Recepción manual declarada. Ninguna marca acredita permisos o autenticidad."""

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from pathlib import Path
import re
from uuid import uuid4

from ..almacenamiento.modelos import ActivoRAW
from ..catalogo.modelos import MecanismoAdquisicion
from ..nucleo import Fuente

# Identidad del procedimiento local, no de una institución desconocida.
FUENTE_RECEPCION_LOCAL = Fuente("SPICA", "recepcion-manual-local")


def texto(valor, *, opcional=False):
    if valor is None and opcional:
        return
    if type(valor) is not str or not valor.strip() or len(valor) > 4096:
        raise ValueError("Texto requerido y acotado")


def identificador(valor):
    if type(valor) is not str or not re.fullmatch(r"[0-9a-f]{32}", valor):
        raise ValueError("Identificador de adquisición hexadecimal requerido")


def hash_sha256(valor):
    if valor is not None and (type(valor) is not str or not re.fullmatch(r"[0-9a-f]{64}", valor)):
        raise ValueError("SHA-256 hexadecimal o desconocido requerido")


class AutenticidadManual(Enum):
    NO_ACREDITADA = "no_acreditada"


class IntegridadManual(Enum):
    NO_COMPROBADA = "no_comprobada"
    COMPROBADA_LOCALMENTE = "comprobada_localmente"
    HASH_EXTERNO_DISCREPANTE = "hash_externo_discrepante"


class EstadoIngestaManual(Enum):
    INCORPORADA = "incorporada"
    YA_REGISTRADA = "ya_registrada_y_recomprobada"


@dataclass(frozen=True)
class DocumentoManual:
    referencia: str
    version: str | None = None
    fecha: date | None = None
    descripcion: str | None = None

    def __post_init__(self):
        texto(self.referencia)
        texto(self.version, opcional=True)
        texto(self.descripcion, opcional=True)
        if self.fecha is not None and type(self.fecha) is not date:
            raise TypeError("Fecha documental civil o desconocida requerida")


@dataclass(frozen=True)
class FundamentoUsoManual:
    documento: DocumentoManual | None = None
    permite_incorporacion: bool | None = None
    permite_publicacion: bool | None = None
    permite_redistribucion: bool | None = None
    restricciones: tuple[str, ...] = ()

    def __post_init__(self):
        if self.documento is not None and type(self.documento) is not DocumentoManual:
            raise TypeError("Documento de fundamento requerido")
        for v in (self.permite_incorporacion, self.permite_publicacion, self.permite_redistribucion):
            if v is not None and type(v) is not bool:
                raise TypeError("Permiso declarado bool o desconocido requerido")
        textos(self.restricciones)


def textos(valores):
    if type(valores) is not tuple or len(valores) > 32:
        raise TypeError("Tupla acotada requerida")
    for valor in valores:
        texto(valor)
    if len(set(valores)) != len(valores):
        raise ValueError("Elementos repetidos")


@dataclass(frozen=True)
class ProcedenciaManual:
    fundamento: FundamentoUsoManual = field(default_factory=FundamentoUsoManual)
    fuente_declarada: Fuente | None = None
    producto_id: str | None = None
    entregado_por: str | None = None
    registro_entregante_permitido: bool = False
    fecha_recepcion: date | None = None
    fecha_recurso: date | None = None
    medio_entrega: str | None = None
    documentos: tuple[DocumentoManual, ...] = ()
    privado: bool = False
    formato_declarado: str | None = None
    tipo_medio_declarado: str | None = None
    sha256_externo: str | None = None

    def __post_init__(self):
        if type(self.fundamento) is not FundamentoUsoManual:
            raise TypeError("Fundamento tipado requerido")
        if self.fuente_declarada is not None and type(self.fuente_declarada) is not Fuente:
            raise TypeError("Fuente declarada o desconocida requerida")
        for v in (self.producto_id, self.entregado_por, self.medio_entrega,
                  self.formato_declarado, self.tipo_medio_declarado):
            texto(v, opcional=True)
        for v in (self.registro_entregante_permitido, self.privado):
            if type(v) is not bool:
                raise TypeError("Indicador explícito requerido")
        if self.entregado_por is not None and not self.registro_entregante_permitido:
            raise ValueError("No se permite registrar al entregante sin declaración explícita")
        for v in (self.fecha_recepcion, self.fecha_recurso):
            if v is not None and type(v) is not date:
                raise TypeError("Fecha civil conocida o None requerida")
        if type(self.documentos) is not tuple or len(self.documentos) > 32 or any(
                type(d) is not DocumentoManual for d in self.documentos):
            raise TypeError("Documentos inmutables y acotados requeridos")
        if len({d.referencia for d in self.documentos}) != len(self.documentos):
            raise ValueError("Referencia documental repetida")
        hash_sha256(self.sha256_externo)


@dataclass(frozen=True)
class SolicitudIngestaManual:
    proyecto_id: str
    objeto_id: str
    recurso_id: str
    archivo: Path = field(repr=False)
    procedencia: ProcedenciaManual
    adquisicion_id: str = field(default_factory=lambda: uuid4().hex)
    mecanismo: MecanismoAdquisicion = field(default=MecanismoAdquisicion.MANUAL, init=False)

    def __post_init__(self):
        for v in (self.proyecto_id, self.objeto_id, self.recurso_id):
            texto(v)
        if not isinstance(self.archivo, Path) or not self.archivo.is_absolute():
            raise ValueError("Ruta local absoluta requerida")
        if type(self.procedencia) is not ProcedenciaManual:
            raise TypeError("Procedencia manual requerida")
        identificador(self.adquisicion_id)


@dataclass(frozen=True)
class PoliticaIngestaManual:
    max_bytes: int = 128 * 1024**2
    tamano_bloque: int = 65_536
    margen_libre: int = 16 * 1024**2
    aceptar_vacios: bool = True

    def __post_init__(self):
        for v in (self.max_bytes, self.tamano_bloque, self.margen_libre):
            if type(v) is not int or v <= 0:
                raise ValueError("Presupuesto positivo requerido")
        if self.tamano_bloque > 1_048_576:
            raise ValueError("Bloques de hasta 1 MiB")
        if type(self.aceptar_vacios) is not bool:
            raise TypeError("Política de vacíos explícita requerida")


@dataclass(frozen=True)
class ReciboIngestaManual:
    """Instantánea persistida; no implica una comprobación física actual."""
    adquisicion_id: str
    activo: ActivoRAW
    procedencia: ProcedenciaManual
    mecanismo: MecanismoAdquisicion = field(default=MecanismoAdquisicion.MANUAL, init=False)
    autenticidad: AutenticidadManual = field(default=AutenticidadManual.NO_ACREDITADA, init=False)

    @property
    def activo_id(self):
        return self.activo.asset_id


@dataclass(frozen=True)
class ResultadoIngestaManual:
    recibo: ReciboIngestaManual
    ruta_verificada: Path
    comprobacion_utc: datetime
    estado: EstadoIngestaManual
    integridad: IntegridadManual = field(default=IntegridadManual.COMPROBADA_LOCALMENTE, init=False)

    @property
    def hash_externo_coincide(self) -> bool | None:
        externo = self.recibo.procedencia.sha256_externo
        return None if externo is None else externo == self.recibo.activo.sha256


class ErrorIngestaManual(Exception):
    def __init__(self, codigo, fase, adquisicion_id, *, activo_id=None, temporal_restante=None):
        super().__init__(codigo)
        self.codigo, self.fase, self.adquisicion_id = codigo, fase, adquisicion_id
        self.activo_id, self.temporal_restante = activo_id, temporal_restante
        self.integridad = (IntegridadManual.HASH_EXTERNO_DISCREPANTE if codigo == "hash_externo_discrepante"
                           else IntegridadManual.NO_COMPROBADA)

    def diagnostico_publico(self):
        return dict(codigo=self.codigo, fase=self.fase, adquisicion_id=self.adquisicion_id,
                    activo_id=self.activo_id, integridad=self.integridad.value,
                    temporal_pendiente=self.temporal_restante is not None)
