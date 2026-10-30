"""Instantáneas documentales inmutables; no certifican los datos científicos."""

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import re
from uuid import uuid4

from ..nucleo import Fuente
from .modelos import EstadoVerificacion, MecanismoAdquisicion, ProcedenciaCatalogo, _fecha, _texto


@dataclass(frozen=True)
class EvidenciaDocumental:
    fuente: Fuente
    recurso_id: str
    producto_id: str | None = None
    referencia_publicacion: str | None = None
    descubierta_utc: datetime | None = None
    licencia_declarada: str | None = None
    referencia_licencia: str | None = None
    revision_documental: int | None = None
    revision_producto: int | None = None
    revision_fuente: int | None = None
    estado: EstadoVerificacion = EstadoVerificacion.DESCONOCIDO
    capacidades_documentadas: tuple[MecanismoAdquisicion, ...] = ()
    procedencia: ProcedenciaCatalogo | None = None

    def __post_init__(self):
        if not isinstance(self.fuente, Fuente) or not isinstance(self.estado, EstadoVerificacion):
            raise TypeError("Se requiere fuente y estado explícitos")
        _texto(self.recurso_id, "recurso_id", True)
        for campo in ("producto_id", "referencia_publicacion", "licencia_declarada", "referencia_licencia"):
            _texto(getattr(self, campo), campo)
        _fecha(self.descubierta_utc, "descubierta_utc")
        if self.descubierta_utc is not None:
            object.__setattr__(self, "descubierta_utc", self.descubierta_utc.astimezone(timezone.utc))
        for revision in (self.revision_documental, self.revision_producto, self.revision_fuente):
            if revision is not None and (type(revision) is not int or revision <= 0):
                raise ValueError("Revisión documental positiva o desconocida")
        if self.procedencia is not None and not isinstance(self.procedencia, ProcedenciaCatalogo):
            raise TypeError("Procedencia documental no admitida")
        if self.estado is not EstadoVerificacion.DESCONOCIDO and self.procedencia is None:
            raise ValueError("La evidencia declarada requiere procedencia")
        if self.estado is EstadoVerificacion.VERIFICADO:
            if self.descubierta_utc is None or self.procedencia.evidencia is None:
                raise ValueError("Evidencia verificada requiere fecha y comprobación explícitas")
        capacidades = tuple(self.capacidades_documentadas)
        if any(not isinstance(c, MecanismoAdquisicion) for c in capacidades):
            raise TypeError("Capacidades documentadas no admitidas")
        object.__setattr__(self, "capacidades_documentadas", capacidades)


@dataclass(frozen=True)
class EvidenciaAdquisicion:
    adquisicion_id: str
    activo_id: str
    documento: EvidenciaDocumental
    url_solicitada: str
    url_saneada: bool
    http_comprobada_utc: datetime
    capacidades_http_verificadas: tuple[MecanismoAdquisicion, ...]
    sha256: str | None
    size_bytes: int | None
    estado_raw: str


def validar_documento(documento, declaracion):
    from ..almacenamiento import ErrorAlmacenamientoRAW
    from .persistencia import _publico, _datos
    if not isinstance(documento, EvidenciaDocumental):
        raise TypeError("Se requiere EvidenciaDocumental")
    _publico(documento)
    if len(json.dumps(_datos(documento), ensure_ascii=False).encode("utf-8")) > 60_000:
        raise ValueError("Documento superior al límite de evidencia")
    producto = declaracion.parametros_publicos.get("producto_id")
    if (documento.fuente != declaracion.fuente or documento.recurso_id != declaracion.recurso_id
            or (producto is not None and documento.producto_id != producto)):
        raise ErrorAlmacenamientoRAW("evidencia_de_otro_recurso_o_producto")


def empaquetar(documento, declaracion, url_solicitada, http_comprobada_utc, consulta_omitida=False):
    from ..almacenamiento.raw import _referencia_publica
    from .persistencia import _datos
    validar_documento(documento, declaracion)
    if type(consulta_omitida) is not bool:
        raise TypeError("consulta_omitida debe ser bool")
    _fecha(http_comprobada_utc, "http_comprobada_utc", True)
    url, saneada = _referencia_publica(url_solicitada, sanear_url=True)
    # No se almacenan encabezados, consultas ni diagnósticos recibidos.
    datos = dict(version=1, adquisicion_id=uuid4().hex, documento=_datos(documento),
                 url_solicitada=url, url_saneada=saneada or consulta_omitida,
                 http_comprobada_utc=http_comprobada_utc.astimezone(timezone.utc).isoformat(),
                 capacidades_http_verificadas=[MecanismoAdquisicion.HTTP_DIRECTO.value])
    if len(json.dumps(datos, ensure_ascii=False).encode("utf-8")) > 65_536:
        raise ValueError("Evidencia documental superior a 64 KiB")
    return datos


def desempaquetar(datos, activo):
    from ..almacenamiento import ErrorAlmacenamientoRAW
    try:
        if type(datos.get("version")) is int and datos["version"] == 2 and datos.get("mecanismo") == "importacion_manual":
            from ..manual.evidencias import desempaquetar_manual
            return desempaquetar_manual(datos, activo)
        if type(datos["version"]) is not int or datos["version"] != 1 or not re.fullmatch(r"[0-9a-f]{32}", datos["adquisicion_id"]):
            raise ValueError
        from .persistencia import _leer_json
        documento = _leer_json(json.dumps(datos["documento"]))
        documento["fuente"] = Fuente(**documento["fuente"])
        documento["estado"] = EstadoVerificacion(documento["estado"])
        documento["capacidades_documentadas"] = tuple(MecanismoAdquisicion(c) for c in documento["capacidades_documentadas"])
        if documento["procedencia"] is not None:
            documento["procedencia"] = ProcedenciaCatalogo(**documento["procedencia"])
        documento = EvidenciaDocumental(**documento)
        validar_documento(documento, activo.declaracion)
        fecha = datetime.fromisoformat(datos["http_comprobada_utc"])
        _fecha(fecha, "http_comprobada_utc", True)
        from ..almacenamiento.raw import _referencia_publica
        _referencia_publica(datos["url_solicitada"], sanear_url=False)
        if type(datos["url_saneada"]) is not bool:
            raise ValueError
        capacidades = tuple(MecanismoAdquisicion(c) for c in datos["capacidades_http_verificadas"])
        if capacidades != (MecanismoAdquisicion.HTTP_DIRECTO,):
            raise ValueError
        return EvidenciaAdquisicion(datos["adquisicion_id"], activo.asset_id, documento,
            datos["url_solicitada"], datos["url_saneada"], fecha, capacidades,
            activo.sha256, activo.size_bytes, activo.estado.value)
    except Exception:
        raise ErrorAlmacenamientoRAW("evidencia_persistida_invalida", activo.asset_id) from None
