"""El destino institucional es declarativo; la evidencia siempre es inventada."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import hashlib
from types import MappingProxyType
from typing import Mapping
from uuid import uuid4

from ..nucleo.temporal import instante_utc
from ..vectorial.modelos import (
    EntidadVector, EstadoCompletitud, PrecisionNumerica, RespuestaSintetica, _parametros,
)


HOST_CANDIDATO = "geocatminnube.ingemmet.gob.pe"
RUTA_CANDIDATA = "/arcgis/rest/services/SERV_GEOLOGIA_50K_INTEGRADA/MapServer/7/query"
SERVICIO = "SERV_GEOLOGIA_50K_INTEGRADA"
PRODUCTO = "Mapa Geológico Integrado del Perú a escala 1:50.000"
DESTINO_SIMULADO = "fixture://spica/piloto-arcgis/atributos"
PARAMETROS_CANDIDATOS = MappingProxyType({
    "f": "json", "where": "1=1", "outFields": "objectid", "returnGeometry": "false",
    "resultOffset": "0", "resultRecordCount": "1", "orderByFields": "objectid ASC",
})
REQUISITOS_EVIDENCIA = (
    "solicitud_simulada_exacta", "estado_y_bytes_observados", "sha256_observado",
    "evaluacion_utc", "validacion_y_oid", "fuente_sintetica", "restricciones_y_detencion",
)
RESTRICCIONES = (
    "sin_red_ni_capacidad_institucional_demostrada", "autorizacion_pendiente",
    "limite_remoto_de_una_entidad_no_acreditado", "sin_raw_staging_o_sqlite_operativos",
    "sin_validacion_cientifica", "sin_instantanea_o_completitud_institucional",
)
DETENCIONES = (
    "destino_o_parametros_incompatibles", "operacion_consumida", "limite_agotado",
    "recepcion_incompleta", "error_simulado", "estructura_incompatible", "cancelacion",
)


class AutorizacionEnsayo(Enum):
    PENDIENTE = "pendiente_sin_permiso_operativo"


class EstadoRecepcion(Enum):
    SIN_RESPUESTA = "sin_respuesta"
    COMPLETA = "recepcion_sintetica_completa"
    INCOMPLETA = "recepcion_sintetica_incompleta"
    EXCEDIDA = "presupuesto_excedido"


class EstadoValidacion(Enum):
    NO_REALIZADA = "no_realizada"
    COHERENTE = "coherente"
    VACIA = "vacia"
    RECHAZADA = "rechazada"
    LIMITADA = "limitada"


class EstadoEnsayo(Enum):
    COHERENTE = "simulacion_coherente"
    VACIO = "simulacion_vacia_sin_demostracion_del_objetivo"
    REVISION = "requiere_revision"
    FALLIDO = "fallo_sintetico"
    CANCELADO = "cancelado"


class FalloSintetico(Enum):
    CONEXION = "conexion_simulada"
    TIMEOUT = "timeout_simulado"


def _identidad(v, prefijo):
    if (type(v) is not str or not v.startswith(prefijo) or len(v) > 100 or len(v) == len(prefijo)
            or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-_" for c in v)):
        raise ValueError("identidad_sintetica_requerida")


@dataclass(frozen=True)
class PreparacionEnsayo:
    ensayo_id: str = field(default_factory=lambda: "ensayo-sintetico-" + uuid4().hex)
    institucion_objetivo: str = "INGEMMET"
    producto_objetivo: str = PRODUCTO
    servicio: str = SERVICIO
    capa_id: int = 7
    capa_nombre: str = "Litologia"
    objetivo: str = "simular_un_oid_sin_geometria"
    metodo_previsto: str = "GET"
    host_candidato: str = HOST_CANDIDATO
    ruta_candidata: str = RUTA_CANDIDATA
    parametros: Mapping[str, str] = field(default_factory=lambda: dict(PARAMETROS_CANDIDATOS), repr=False)
    max_bytes: int = 65_536
    max_entidades: int = 1
    permitir_geometrias: bool = False
    autorizacion: AutorizacionEnsayo = AutorizacionEnsayo.PENDIENTE
    evidencia_requerida: tuple[str, ...] = field(default=REQUISITOS_EVIDENCIA, init=False)
    diagnosticos: tuple[str, ...] = field(default=RESTRICCIONES, init=False)
    motivos_detencion: tuple[str, ...] = field(default=DETENCIONES, init=False)

    def __post_init__(self):
        _identidad(self.ensayo_id, "ensayo-sintetico-")
        for k, esperado in (("institucion_objetivo", "INGEMMET"), ("producto_objetivo", PRODUCTO),
                            ("servicio", SERVICIO), ("capa_nombre", "Litologia"),
                            ("objetivo", "simular_un_oid_sin_geometria"), ("metodo_previsto", "GET"),
                            ("host_candidato", HOST_CANDIDATO), ("ruta_candidata", RUTA_CANDIDATA)):
            if type(getattr(self, k)) is not str or getattr(self, k) != esperado:
                raise ValueError("candidato_fuera_del_alcance")
        if type(self.capa_id) is not int or self.capa_id != 7:
            raise ValueError("capa_no_admitida")
        if type(self.max_bytes) is not int or not 1 <= self.max_bytes <= 65_536:
            raise ValueError("presupuesto_no_admitido")
        if type(self.max_entidades) is not int or self.max_entidades != 1 or self.permitir_geometrias is not False:
            raise ValueError("alcance_de_entidades_no_admitido")
        if self.autorizacion is not AutorizacionEnsayo.PENDIENTE:
            raise ValueError("preparacion_no_otorga_autorizacion")
        p = _parametros(self.parametros)
        if p != PARAMETROS_CANDIDATOS:
            raise ValueError("parametros_no_admitidos")
        object.__setattr__(self, "parametros", p)

    @property
    def url_candidata(self):
        return "https://" + self.host_candidato + self.ruta_candidata

    @property
    def autoriza_red(self):
        return False


@dataclass(frozen=True)
class SolicitudSimulada:
    preparacion: PreparacionEnsayo
    destino: str = field(default=DESTINO_SIMULADO, init=False)

    def __post_init__(self):
        if type(self.preparacion) is not PreparacionEnsayo:
            raise TypeError("preparacion_tipificada_requerida")


@dataclass(frozen=True)
class EscenarioSintetico:
    respuesta: RespuestaSintetica | None = field(default=None, repr=False)
    fallo: FalloSintetico | None = None
    content_type: str = "application/json"
    content_encoding: str = "identity"

    def __post_init__(self):
        if (self.respuesta is None) == (self.fallo is None):
            raise ValueError("escenario_debe_contener_respuesta_o_fallo")
        if self.fallo is not None and type(self.fallo) is not FalloSintetico:
            raise TypeError("fallo_sintetico_tipado_requerido")
        if self.respuesta is not None:
            if type(self.respuesta) is not RespuestaSintetica:
                raise TypeError("respuesta_sintetica_tipificada_requerida")
            _identidad(self.respuesta.respuesta_id, "respuesta-sintetica-")
            if (self.respuesta.solicitud is not None or self.respuesta.instantanea_id is not None
                    or self.respuesta.total_observado is not None):
                raise ValueError("sin_reutilizacion_de_adquisiciones_o_instantaneas")
        if any(type(v) is not str or len(v) > 256 for v in (self.content_type, self.content_encoding)):
            raise ValueError("metadatos_sinteticos_no_admitidos")


@dataclass(frozen=True)
class ResultadoEnsayo:
    solicitud: SolicitudSimulada = field(repr=False)
    evaluado_utc: datetime
    estado: EstadoEnsayo
    recepcion: EstadoRecepcion
    validacion: EstadoValidacion
    operaciones_simuladas: int
    codigo_http: int | None
    respuesta_id: str | None
    bytes_observados: int | None
    longitud_declarada: int | None
    sha256: str | None
    contenido: bytes | None = field(repr=False)
    entidades: tuple[EntidadVector, ...] = field(default=(), repr=False)
    capa_observada: int | None = None
    exceeded_transfer_limit: bool | None = None
    sintaxis_completa: bool = False
    diagnosticos: tuple[str, ...] = ()
    restricciones: tuple[str, ...] = field(default=RESTRICCIONES, init=False)
    procedencia: str = field(default="fixture_sintetica", init=False)
    precision: PrecisionNumerica = field(default=PrecisionNumerica.DECIMAL_EXACTA, init=False)
    completitud_institucional: EstadoCompletitud = field(default=EstadoCompletitud.DESCONOCIDA, init=False)

    def __post_init__(self):
        if (type(self.solicitud) is not SolicitudSimulada or type(self.estado) is not EstadoEnsayo
                or type(self.recepcion) is not EstadoRecepcion or type(self.validacion) is not EstadoValidacion
                or type(self.operaciones_simuladas) is not int or self.operaciones_simuladas not in (0, 1)
                or type(self.entidades) is not tuple or len(self.entidades) > 1
                or any(type(e) is not EntidadVector for e in self.entidades)
                or type(self.diagnosticos) is not tuple or any(type(x) is not str for x in self.diagnosticos)):
            raise TypeError("resultado_inmutable_tipificado_requerido")
        if self.contenido is not None and (type(self.contenido) is not bytes
                or len(self.contenido) > self.solicitud.preparacion.max_bytes):
            raise ValueError("contenido_fuera_del_presupuesto")
        if (self.codigo_http is not None and (type(self.codigo_http) is not int or not 100 <= self.codigo_http <= 599)
                or self.bytes_observados is not None and (type(self.bytes_observados) is not int or self.bytes_observados < 0)
                or self.longitud_declarada is not None and (type(self.longitud_declarada) is not int or self.longitud_declarada < 0)
                or self.capa_observada is not None and type(self.capa_observada) is not int
                or self.exceeded_transfer_limit is not None and type(self.exceeded_transfer_limit) is not bool
                or type(self.sintaxis_completa) is not bool):
            raise ValueError("metadatos_de_resultado_incompatibles")
        if self.respuesta_id is not None:
            _identidad(self.respuesta_id, "respuesta-sintetica-")
        if self.contenido is not None:
            if (self.bytes_observados != len(self.contenido)
                    or self.sha256 != hashlib.sha256(self.contenido).hexdigest()):
                raise ValueError("hash_o_tamano_del_resultado_incoherente")
        elif self.sha256 is not None:
            raise ValueError("hash_sin_bytes_disponibles")
        if self.recepcion is EstadoRecepcion.SIN_RESPUESTA:
            if any(x is not None for x in (self.codigo_http, self.respuesta_id, self.bytes_observados,
                                           self.longitud_declarada, self.contenido)):
                raise ValueError("sin_respuesta_con_metadatos_de_respuesta")
        elif self.operaciones_simuladas != 1 or self.codigo_http is None or self.respuesta_id is None:
            raise ValueError("respuesta_sin_intercambio_sintetico")
        if self.recepcion is EstadoRecepcion.EXCEDIDA:
            if (self.contenido is not None or self.bytes_observados is None
                    or self.bytes_observados <= self.solicitud.preparacion.max_bytes):
                raise ValueError("exceso_de_bytes_incoherente")
        if self.recepcion in (EstadoRecepcion.COMPLETA, EstadoRecepcion.INCOMPLETA) and self.contenido is None:
            raise ValueError("recepcion_sin_bytes")
        if self.recepcion is EstadoRecepcion.COMPLETA and (self.codigo_http == 206
                or self.longitud_declarada is not None and self.longitud_declarada != self.bytes_observados):
            raise ValueError("recepcion_completa_con_evidencia_contradictoria")
        if self.sintaxis_completa and (self.recepcion is not EstadoRecepcion.COMPLETA or self.codigo_http != 200):
            raise ValueError("sintaxis_sin_recepcion_completa_200")
        if self.estado in (EstadoEnsayo.COHERENTE, EstadoEnsayo.VACIO):
            esperada = EstadoValidacion.COHERENTE if self.estado is EstadoEnsayo.COHERENTE else EstadoValidacion.VACIA
            if (not self.sintaxis_completa or self.validacion is not esperada
                    or len(self.entidades) != (1 if self.estado is EstadoEnsayo.COHERENTE else 0)):
                raise ValueError("resultado_coherente_sin_validacion")
        elif self.entidades:
            raise ValueError("entidades_sin_validacion_coherente")
        object.__setattr__(self, "evaluado_utc", instante_utc(self.evaluado_utc))
