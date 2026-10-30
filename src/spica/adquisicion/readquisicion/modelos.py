"""Contratos declarativos v1. Ningún modelo consulta archivos, SQLite o servidores."""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
import re

from ..catalogo.modelos import MecanismoAdquisicion, ProcedenciaCatalogo
from ..catalogo.persistencia import _publico
from ..nucleo import EstadoDescarga, Fuente
from ..nucleo.temporal import instante_utc
from ..almacenamiento.modelos import EstadoIncorporacion


def _texto(valor, *, opcional=False):
    if valor is None and opcional:
        return
    if type(valor) is not str or not valor.strip() or len(valor) > 4096:
        raise ValueError("Texto no vacío y acotado requerido")
    _publico(valor)  # Rechaza secretos reconocibles; no cambia identificadores.


def _fecha(objeto, nombre):
    valor = getattr(objeto, nombre)
    if valor is not None:
        object.__setattr__(objeto, nombre, instante_utc(valor))


def _civil(valor):
    if valor is not None and type(valor) is not date:
        raise TypeError("Fecha civil o desconocida requerida")


def _tupla(valores, tipo, limite=1024):
    if type(valores) is not tuple or len(valores) > limite or any(type(v) is not tipo for v in valores):
        raise TypeError("Tupla acotada de contratos tipados requerida")


def _procedencia(valor):
    if type(valor) is not ProcedenciaCatalogo:
        raise TypeError("Procedencia explícita requerida")
    _publico(valor)


@dataclass(frozen=True)
class _Contrato:
    version_contrato: str = field(default="1", init=False)


@dataclass(frozen=True)
class IdentidadRecurso(_Contrato):
    proyecto_id: str
    objeto_id: str
    recurso_id: str
    fuente: Fuente | None = None
    producto_id: str | None = None

    def __post_init__(self):
        for valor in (self.proyecto_id, self.objeto_id, self.recurso_id):
            _texto(valor)
        _texto(self.producto_id, opcional=True)
        if self.fuente is not None:
            if type(self.fuente) is not Fuente:
                raise TypeError("Fuente declarada o desconocida requerida")
            _publico(self.fuente)


class EstadoLocal(Enum):
    DESCONOCIDO = "desconocido"
    INTEGRO = "comprobado_localmente"
    INCONSISTENTE = "inconsistente"
    AUSENTE = "ausencia_comprobada"
    NO_DISPONIBLE = "comprobacion_no_disponible"


@dataclass(frozen=True)
class EvidenciaLocal(_Contrato):
    estado: EstadoLocal = EstadoLocal.DESCONOCIDO
    comprobada_utc: datetime | None = None
    procedencia: ProcedenciaCatalogo | None = None
    sha256_observado: str | None = None
    size_bytes_observado: int | None = None
    activo_id: str | None = None

    def __post_init__(self):
        if type(self.estado) is not EstadoLocal:
            raise TypeError("Estado local explícito requerido")
        _fecha(self, "comprobada_utc")
        _texto(self.activo_id, opcional=True)
        if self.procedencia is not None:
            _procedencia(self.procedencia)
        if self.sha256_observado is not None and (type(self.sha256_observado) is not str
                or not re.fullmatch(r"[0-9a-f]{64}", self.sha256_observado)):
            raise ValueError("SHA-256 observado no admitido")
        if self.size_bytes_observado is not None and (type(self.size_bytes_observado) is not int
                                                     or self.size_bytes_observado < 0):
            raise ValueError("Tamaño observado no admitido")
        if self.estado is EstadoLocal.DESCONOCIDO:
            if any(v is not None for v in (self.comprobada_utc, self.procedencia,
                                           self.sha256_observado, self.size_bytes_observado, self.activo_id)):
                raise ValueError("Desconocido no contiene una comprobación")
        elif (self.comprobada_utc is None or self.procedencia is None
              or self.procedencia.evidencia is None or self.activo_id is None):
            raise ValueError("La comprobación declarada requiere activo, fecha y procedencia con evidencia")
        if self.estado is EstadoLocal.INTEGRO and (self.sha256_observado is None or self.size_bytes_observado is None):
            raise ValueError("Integridad declarada requiere tamaño y SHA-256 observados")
        if self.estado in (EstadoLocal.AUSENTE, EstadoLocal.NO_DISPONIBLE) and (
                self.sha256_observado is not None or self.size_bytes_observado is not None):
            raise ValueError("No atribuir bytes observados a una comprobación no disponible o ausencia")

    @property
    def existencia_comprobada(self) -> bool | None:
        if self.estado is EstadoLocal.INTEGRO:
            return True
        if self.estado is EstadoLocal.AUSENTE:
            return False
        return None


@dataclass(frozen=True)
class IndiciosHTTP(_Contrato):
    url_declarada: str | None = None
    nombre_declarado: str | None = None
    content_length: int | None = None
    etag: str | None = None
    last_modified: datetime | None = None

    def __post_init__(self):
        for valor in (self.url_declarada, self.nombre_declarado, self.etag):
            _texto(valor, opcional=True)
        if self.url_declarada is not None:
            from urllib.parse import urlsplit
            url = urlsplit(self.url_declarada)
            if url.scheme not in ("http", "https") or not url.hostname:
                raise ValueError("Referencia HTTP pública requerida")
        if self.nombre_declarado is not None and any(c in self.nombre_declarado for c in ("/", "\\", ":")):
            raise ValueError("Nombre declarado sin ruta requerida")
        if self.content_length is not None and (type(self.content_length) is not int or self.content_length < 0):
            raise ValueError("Content-Length no negativo o desconocido requerido")
        if self.etag is not None and not re.fullmatch(r'(?:W/)?"[\x21\x23-\x7e]*"', self.etag):
            raise ValueError("ETag opaco entre comillas requerido")
        _fecha(self, "last_modified")

    @property
    def etag_debil(self) -> bool | None:
        return None if self.etag is None else self.etag.startswith("W/")


@dataclass(frozen=True)
class AntecedenteAdquisicion(_Contrato):
    identidad: IdentidadRecurso
    procedencia: ProcedenciaCatalogo
    adquisicion_id: str | None = None
    activo_id: str | None = None
    mecanismo: MecanismoAdquisicion | None = None
    estado_raw: EstadoIncorporacion | None = None
    estado_descarga: EstadoDescarga | None = None
    interrumpida: bool = False
    fecha_adquisicion: datetime | None = None
    fecha_incorporacion_raw: datetime | None = None
    fecha_recepcion_civil: date | None = None
    sha256_catalogado: str | None = None
    size_bytes_catalogado: int | None = None
    local: EvidenciaLocal = field(default_factory=EvidenciaLocal)
    version_recurso: str | None = None
    version_documental: str | None = None
    fecha_documental: date | None = None
    fecha_observacion: date | None = None
    indicios_http: IndiciosHTTP | None = None
    restricciones_historicas: tuple[str, ...] = ()
    permite_publicar_historico: bool | None = None
    permite_redistribuir_historico: bool | None = None

    def __post_init__(self):
        if type(self.identidad) is not IdentidadRecurso or type(self.local) is not EvidenciaLocal:
            raise TypeError("Identidad y evidencia local tipadas requeridas")
        _procedencia(self.procedencia)
        for valor in (self.adquisicion_id, self.activo_id, self.version_recurso, self.version_documental):
            _texto(valor, opcional=True)
        for valor, tipo in ((self.mecanismo, MecanismoAdquisicion), (self.estado_raw, EstadoIncorporacion),
                            (self.estado_descarga, EstadoDescarga)):
            if valor is not None and type(valor) is not tipo:
                raise TypeError("Estado o mecanismo no admitido")
        if type(self.interrumpida) is not bool:
            raise TypeError("Interrupción explícita requerida")
        _fecha(self, "fecha_adquisicion")
        _fecha(self, "fecha_incorporacion_raw")
        for valor in (self.fecha_documental, self.fecha_observacion, self.fecha_recepcion_civil):
            _civil(valor)
        if self.sha256_catalogado is not None and (type(self.sha256_catalogado) is not str
                or not re.fullmatch(r"[0-9a-f]{64}", self.sha256_catalogado)):
            raise ValueError("SHA-256 catalogado no admitido")
        if self.size_bytes_catalogado is not None and (type(self.size_bytes_catalogado) is not int
                                                     or self.size_bytes_catalogado < 0):
            raise ValueError("Tamaño catalogado no admitido")
        if self.indicios_http is not None and (type(self.indicios_http) is not IndiciosHTTP or self.mecanismo
                not in (MecanismoAdquisicion.HTTP_DIRECTO, MecanismoAdquisicion.API_REST)):
            raise ValueError("No atribuir indicios HTTP a un mecanismo distinto")
        if self.mecanismo is MecanismoAdquisicion.MANUAL and self.estado_descarga is not None:
            raise ValueError("Una entrega manual no declara estado de descarga HTTP")
        _tupla(self.restricciones_historicas, str, 32)
        for r in self.restricciones_historicas:
            _texto(r)
        for valor in (self.permite_publicar_historico, self.permite_redistribuir_historico):
            if valor is not None and type(valor) is not bool:
                raise TypeError("Restricción histórica bool o desconocida requerida")


class RelacionActualizacion(Enum):
    DESCONOCIDA = "desconocida"
    POSTERIOR_DOCUMENTADA = "posterior_documentada"
    MISMA_VERSION_DECLARADA = "misma_version_declarada"
    CONTRADICTORIA = "contradictoria"


@dataclass(frozen=True)
class EvidenciaActualizacion(_Contrato):
    identidad: IdentidadRecurso
    mecanismo: MecanismoAdquisicion
    procedencia: ProcedenciaCatalogo
    relacion: RelacionActualizacion = RelacionActualizacion.DESCONOCIDA
    adquisicion_base_id: str | None = None
    version_previa: str | None = None
    version_nueva: str | None = None
    version_documental: str | None = None
    fecha_documental: date | None = None
    indicios_http: IndiciosHTTP | None = None

    def __post_init__(self):
        if (type(self.identidad) is not IdentidadRecurso or type(self.mecanismo) is not MecanismoAdquisicion
                or type(self.relacion) is not RelacionActualizacion):
            raise TypeError("Identidad, mecanismo y relación tipados requeridos")
        _procedencia(self.procedencia)
        for v in (self.adquisicion_base_id, self.version_previa, self.version_nueva, self.version_documental):
            _texto(v, opcional=True)
        _civil(self.fecha_documental)
        if self.indicios_http is not None and (type(self.indicios_http) is not IndiciosHTTP or self.mecanismo
                not in (MecanismoAdquisicion.HTTP_DIRECTO, MecanismoAdquisicion.API_REST)):
            raise ValueError("No atribuir HTTP a una entrega manual u otro mecanismo")


@dataclass(frozen=True)
class RestriccionesAcceso(_Contrato):
    identidad: IdentidadRecurso
    mecanismo: MecanismoAdquisicion
    procedencia: ProcedenciaCatalogo
    permite_adquirir: bool | None = None
    permite_reutilizar: bool | None = None
    permite_publicar: bool | None = None
    permite_redistribuir: bool | None = None
    condiciones: tuple[str, ...] = ()

    def __post_init__(self):
        if type(self.identidad) is not IdentidadRecurso or type(self.mecanismo) is not MecanismoAdquisicion:
            raise TypeError("Alcance explícito de restricciones requerido")
        _procedencia(self.procedencia)
        for v in (self.permite_adquirir, self.permite_reutilizar, self.permite_publicar, self.permite_redistribuir):
            if v is not None and type(v) is not bool:
                raise TypeError("Permisos declarados bool o desconocidos requeridos")
        _tupla(self.condiciones, str, 32)
        for c in self.condiciones:
            _texto(c)


class ModoConsulta(Enum):
    PREFERIR_LOCAL = "preferir_local"
    EXIGIR_VIGENCIA = "exigir_evidencia_de_vigencia"
    SOLICITAR_NUEVA = "solicitar_nueva_adquisicion"


class UsoPrevisto(Enum):
    INTERNO = "interno"
    PUBLICACION = "publicacion"
    REDISTRIBUCION = "redistribucion"


@dataclass(frozen=True)
class PoliticaReadquisicion(_Contrato):
    modo: ModoConsulta = ModoConsulta.PREFERIR_LOCAL
    antiguedad_maxima_local: timedelta | None = timedelta(hours=24)

    def __post_init__(self):
        if type(self.modo) is not ModoConsulta:
            raise TypeError("Modo de consulta no admitido")
        if self.antiguedad_maxima_local is not None and (type(self.antiguedad_maxima_local) is not timedelta
                                                        or self.antiguedad_maxima_local < timedelta(0)):
            raise ValueError("Antigüedad máxima no negativa o None requerida")


@dataclass(frozen=True)
class SolicitudDecision(_Contrato):
    identidad: IdentidadRecurso
    mecanismo: MecanismoAdquisicion
    evaluada_utc: datetime
    antecedentes: tuple[AntecedenteAdquisicion, ...] = ()
    historial_completo: bool = False
    actualizaciones: tuple[EvidenciaActualizacion, ...] = ()
    restricciones: RestriccionesAcceso | None = None
    politica: PoliticaReadquisicion = field(default_factory=PoliticaReadquisicion)
    uso: UsoPrevisto = UsoPrevisto.INTERNO

    def __post_init__(self):
        if (type(self.identidad) is not IdentidadRecurso or type(self.mecanismo) is not MecanismoAdquisicion
                or type(self.politica) is not PoliticaReadquisicion or type(self.uso) is not UsoPrevisto):
            raise TypeError("Solicitud de decisión tipada requerida")
        if self.evaluada_utc is None:
            raise ValueError("Fecha de evaluación explícita requerida")
        _fecha(self, "evaluada_utc")
        if type(self.historial_completo) is not bool:
            raise TypeError("Alcance del historial explícito requerido")
        _tupla(self.antecedentes, AntecedenteAdquisicion)
        _tupla(self.actualizaciones, EvidenciaActualizacion, 128)
        if self.restricciones is not None and type(self.restricciones) is not RestriccionesAcceso:
            raise TypeError("Restricciones tipadas o desconocidas requeridas")
        object.__setattr__(self, "antecedentes", tuple(sorted(self.antecedentes, key=repr)))
        object.__setattr__(self, "actualizaciones", tuple(sorted(self.actualizaciones, key=repr)))


class Decision(Enum):
    ADQUISICION_INICIAL = "recomendar_adquisicion_inicial"
    REUTILIZAR_LOCAL = "considerar_reutilizacion_local"
    RECOMENDAR_NUEVA = "recomendar_nueva_adquisicion"
    EVIDENCIA_INSUFICIENTE = "evidencia_insuficiente"
    REVISION_MANUAL = "revision_manual_requerida"
    BLOQUEADA = "operacion_bloqueada"


class EstadoActualizacion(Enum):
    DESCONOCIDO = "desconocido"
    DOCUMENTADA = "actualizacion_documentada"
    CONTRADICTORIO = "contradictorio"


@dataclass(frozen=True)
class ResultadoDecision(_Contrato):
    solicitud: SolicitudDecision
    decision: Decision
    justificacion: tuple[str, ...]
    informacion_faltante: tuple[str, ...]
    limitaciones: tuple[str, ...]
    estado_actualizacion: EstadoActualizacion
    activos_reutilizables: tuple[str, ...] = ()
    version_motor: str = field(default="1.0.0", init=False)
    autoriza_red: bool = field(default=False, init=False)
    vigencia_remota_comprobada: bool = field(default=False, init=False)

    def __post_init__(self):
        if (type(self.solicitud) is not SolicitudDecision or type(self.decision) is not Decision
                or type(self.estado_actualizacion) is not EstadoActualizacion):
            raise TypeError("Resultado de decisión tipado requerido")
        for valores in (self.justificacion, self.informacion_faltante, self.limitaciones, self.activos_reutilizables):
            _tupla(valores, str)
            for valor in valores:
                _texto(valor)
        if not self.justificacion or ((self.decision is Decision.REUTILIZAR_LOCAL) != bool(self.activos_reutilizables)):
            raise ValueError("Decisión y candidatos locales no coherentes")
