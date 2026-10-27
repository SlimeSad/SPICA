"""Identidades y metadatos del almacenamiento experimental; sin calidad científica."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from types import MappingProxyType
from typing import Mapping

from ..nucleo import Fuente


def _texto_opcional(valor: str | None, nombre: str):
    if valor is not None and (not isinstance(valor, str) or not valor.strip()):
        raise ValueError(f"{nombre} debe ser texto no vacío o None")


@dataclass(frozen=True)
class ProyectoCientifico:
    project_id: str
    schema_version: str | None = None
    nombre: str | None = None
    contexto: str | None = None
    estado: str | None = None

    def __post_init__(self):
        _texto_opcional(self.project_id, "project_id")
        if self.project_id is None:
            raise ValueError("project_id es obligatorio")
        for nombre in ("schema_version", "nombre", "contexto", "estado"):
            _texto_opcional(getattr(self, nombre), nombre)


@dataclass(frozen=True)
class ObjetoCientifico:
    object_id: str
    project_id: str
    family: str | None = None
    kind: str | None = None
    created_at: datetime | None = None
    state: str | None = None

    def __post_init__(self):
        for nombre in ("object_id", "project_id"):
            valor = getattr(self, nombre)
            _texto_opcional(valor, nombre)
            if valor is None:
                raise ValueError(f"{nombre} es obligatorio")
        for nombre in ("family", "kind", "state"):
            _texto_opcional(getattr(self, nombre), nombre)
        if self.created_at is not None:
            if not isinstance(self.created_at, datetime) or self.created_at.utcoffset() is None:
                raise ValueError("created_at debe ser datetime con zona horaria o None")


class EstadoIncorporacion(Enum):
    PREPARADA = "preparada"
    VERIFICADA = "verificada_localmente"
    INCORPORADA = "incorporada"
    FALLIDA = "fallida"
    INCONSISTENTE = "inconsistente"


@dataclass(frozen=True)
class DeclaracionRAW:
    proyecto_id: str
    objeto_id: str
    fuente: Fuente
    recurso_id: str
    procedencia: str | None = None
    parametros_publicos: Mapping[str, str] = field(default_factory=dict)
    formato_declarado: str | None = None
    tipo_medio_declarado: str | None = None

    def __post_init__(self):
        for nombre in ("proyecto_id", "objeto_id", "recurso_id"):
            valor = getattr(self, nombre)
            if not isinstance(valor, str) or not valor.strip():
                raise ValueError(f"{nombre} debe ser texto no vacío")
        if not isinstance(self.fuente, Fuente):
            raise TypeError("fuente debe ser Fuente")
        for nombre in ("procedencia", "formato_declarado", "tipo_medio_declarado"):
            valor = getattr(self, nombre)
            if valor is not None and (not isinstance(valor, str) or not valor.strip()):
                raise ValueError(f"{nombre} debe ser texto no vacío o None")
        parametros = dict(self.parametros_publicos)
        if any(not isinstance(k, str) or not k.strip() or not isinstance(v, str)
               for k, v in parametros.items()):
            raise ValueError("parametros_publicos debe contener claves y valores de texto")
        object.__setattr__(self, "parametros_publicos", MappingProxyType(parametros))


@dataclass(frozen=True)
class ActivoRAW:
    activo_id: str
    declaracion: DeclaracionRAW
    fecha_utc: datetime
    estado: EstadoIncorporacion
    tamano: int | None
    sha256: str | None
    ruta_interna: str | None
    error: str | None
    advertencias: tuple[str, ...]
    comprobacion_utc: datetime | None
    media_detected: str | None = None

    @property
    def asset_id(self) -> str:
        return self.activo_id

    @property
    def object_id(self) -> str:
        return self.declaracion.objeto_id

    @property
    def size_bytes(self) -> int | None:
        return self.tamano

    @property
    def storage_ref(self) -> str | None:
        return self.ruta_interna


@dataclass(frozen=True)
class ComprobacionRAW:
    activo_id: str
    coincide: bool
    fecha_utc: datetime
    error: str | None = None


@dataclass(frozen=True)
class DiagnosticoRAW:
    incompletas: tuple[str, ...]
    inconsistentes: tuple[str, ...]
    sin_referencia: tuple[str, ...]
    temporales: tuple[str, ...]


class ErrorAlmacenamientoRAW(Exception):
    """Códigos técnicos seguros; no registra mensajes originales ni rutas de entrada."""

    def __init__(self, codigo: str, activo_id: str | None = None):
        super().__init__(codigo)
        self.codigo = codigo
        self.activo_id = activo_id
