"""Ensayo acotado de metadatos; no representa una adquisición vectorial."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from types import MappingProxyType
from typing import Mapping
from urllib.parse import urlsplit


LIMITE_METADATOS = 1_048_576


class TipoMetadatos(Enum):
    SERVICIO = "servicio"
    CAPA = "capa"


class EstadoMetadatos(Enum):
    COHERENTE = "metadatos_coherentes"
    REVISION = "revision_necesaria"


@dataclass(frozen=True)
class ObjetivoArcGIS:
    url_servicio: str
    url_capa: str
    servicio_id: str
    capa_id: int
    capa_nombre: str
    wkid_esperado: int
    latest_wkid_esperado: int
    campos_obligatorios: tuple[str, ...]

    def __post_init__(self):
        if type(self.capa_id) is not int or self.capa_id < 0:
            raise ValueError("ID de capa no admitido")
        for valor in (self.servicio_id, self.capa_nombre):
            if type(valor) is not str or not valor.strip() or len(valor) > 256:
                raise ValueError("Identificador esperado no admitido")
        for valor in (self.wkid_esperado, self.latest_wkid_esperado):
            if type(valor) is not int or valor <= 0:
                raise ValueError("Identificador espacial esperado no admitido")
        if (type(self.campos_obligatorios) is not tuple or len(self.campos_obligatorios) > 128
                or any(type(c) is not str or not c or len(c) > 256 for c in self.campos_obligatorios)
                or len(set(self.campos_obligatorios)) != len(self.campos_obligatorios)):
            raise ValueError("Campos esperados no admitidos")
        try:
            u = urlsplit(self.url_servicio)
            if (u.scheme != "https" or not u.hostname or u.username or u.password or u.query or u.fragment
                    or u.port not in (None, 443) or any(ord(c) <= 32 or ord(c) == 127 for c in self.url_servicio)
                    or any(c in self.url_servicio for c in ("%", "\\"))
                    or "/../" in u.path or "//" in u.path
                    or not u.path.startswith("/arcgis/rest/services/")
                    or not u.path.endswith("/" + self.servicio_id + "/MapServer")
                    or self.url_capa != self.url_servicio + "/" + str(self.capa_id)):
                raise ValueError
        except (TypeError, ValueError):
            raise ValueError("Rutas HTTPS de metadatos no admitidas") from None

    @property
    def origen(self) -> str:
        u = urlsplit(self.url_servicio)
        return "https://" + u.netloc


def congelar(valor):
    if isinstance(valor, dict):
        return MappingProxyType({k: congelar(v) for k, v in valor.items()})
    if isinstance(valor, list):
        return tuple(congelar(v) for v in valor)
    return valor


@dataclass(frozen=True)
class ValidacionMetadatos:
    tipo: TipoMetadatos
    estado: EstadoMetadatos
    diagnosticos: tuple[str, ...]
    advertencias: tuple[str, ...]
    sha256: str
    bytes_recibidos: int
    campo_oid: str | None = None
    datos: Mapping[str, object] = field(default_factory=dict, repr=False)

    def __post_init__(self):
        object.__setattr__(self, "datos", congelar(self.datos))


@dataclass(frozen=True)
class IntentoMetadatos:
    tipo: TipoMetadatos
    url: str
    inicio_utc: datetime
    fin_utc: datetime
    intentos_get: int
    codigo_http: int | None
    content_type: str | None
    longitud_declarada: int | None
    validacion: ValidacionMetadatos | None
    error: str | None
    cuerpo: bytes | None = field(default=None, repr=False)

    @property
    def permite_continuar(self):
        return self.error is None and self.validacion is not None and self.validacion.estado is EstadoMetadatos.COHERENTE
