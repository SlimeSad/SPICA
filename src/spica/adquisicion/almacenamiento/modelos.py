"""Identidades y metadatos del almacenamiento experimental; sin calidad científica."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from types import MappingProxyType
from typing import Mapping

from ..nucleo import Fuente


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
