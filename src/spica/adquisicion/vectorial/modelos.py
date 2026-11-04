"""Contratos vectoriales 0.1, independientes de HTTP, RAW y QA/QC científico."""

from dataclasses import dataclass, field, fields
from datetime import datetime
from enum import Enum
import hashlib
import json
import math
from types import MappingProxyType
from typing import Mapping

from ..nucleo import Fuente
from ..nucleo.temporal import instante_utc
from ..catalogo.modelos import ProcedenciaCatalogo


VERSION_CONTRATO = "0.1"


class _LimiteSnapshot(ValueError):
    pass


def _texto(v, maximo=512):
    if type(v) is not str or not v.strip() or len(v) > maximo:
        raise ValueError("Texto contractual no admitido")


def _entero(v, minimo=0, maximo=2**63 - 1):
    if type(v) is not int or not minimo <= v <= maximo:
        raise ValueError("Entero contractual no admitido")


def _utc(v):
    return instante_utc(v)


def _parametros(v):
    if not isinstance(v, Mapping) or len(v) > 64:
        raise ValueError("Parámetros declarativos no admitidos")
    d = {}
    for k, x in v.items():
        _texto(k, 128)
        if type(x) is not str or len(x) > 8192:
            raise ValueError("Valor de parámetro no admitido")
        # No autenticación: no conservar accidentalmente estos campos.
        if any(p in k.lower() for p in ("token", "password", "secret", "authorization", "cookie", "api_key")):
            raise ValueError("Parámetro sensible no admitido")
        d[k] = x
    return MappingProxyType(d)


def _congelar(v, _cuenta=None, _nivel=0):
    """Snapshot JSON profundo; también acota constructores invocados directamente."""
    cuenta = [0] if _cuenta is None else _cuenta
    cuenta[0] += 1
    if cuenta[0] > 500_000 or _nivel > 64:
        raise _LimiteSnapshot("Snapshot JSON excesivo o cíclico")
    if type(v) in (dict, MappingProxyType):
        if any(type(k) is not str for k in v):
            raise ValueError("Clave JSON no textual")
        cuenta[0] += len(v)  # Las claves son nodos, como en el lector compartido.
        if cuenta[0] > 500_000:
            raise _LimiteSnapshot("Snapshot JSON excesivo")
        return MappingProxyType({k: _congelar(x, cuenta, _nivel + 1) for k, x in v.items()})
    if type(v) in (list, tuple):
        return tuple(_congelar(x, cuenta, _nivel + 1) for x in v)
    if (type(v) not in (str, int, float, bool, type(None))
            or type(v) is float and not math.isfinite(v)):
        raise ValueError("Valor JSON no admitido")
    return v


class EstadoCompletitud(Enum):
    COMPLETA_COMPROBADA = "completa_comprobada"
    PARCIAL = "parcial"
    INCOMPLETA_POR_LIMITES = "incompleta_por_limites"
    INCONSISTENTE = "inconsistente"
    DESCONOCIDA = "desconocida"


class EstadoPagina(Enum):
    NO_INSPECCIONADA = "no_inspeccionada"
    VALIDA = "estructura_valida"
    INVALIDA = "estructura_invalida"
    LIMITADA = "inspeccion_limitada"
    INTERRUMPIDA = "transferencia_interrumpida"
    CANCELADA = "cancelada"


class EstadoGeometria(Enum):
    AUSENTE = "ausente"
    NULA = "nula"
    PRESENTE = "presente"


class EstrategiaPaginacion(Enum):
    OFFSET = "offset"
    OBJECT_IDS = "object_ids"
    CONTEO_DOCUMENTADO = "conteo_documentado"


class TipoCampo(Enum):
    OID = "esriFieldTypeOID"
    ENTERO = "esriFieldTypeInteger"
    ENTERO_CORTO = "esriFieldTypeSmallInteger"
    ENTERO_LARGO = "esriFieldTypeBigInteger"
    REAL = "esriFieldTypeDouble"
    REAL_SIMPLE = "esriFieldTypeSingle"
    TEXTO = "esriFieldTypeString"
    FECHA = "esriFieldTypeDate"  # Número original; sin interpretación temporal.
    GUID = "esriFieldTypeGUID"
    GLOBAL_ID = "esriFieldTypeGlobalID"


@dataclass(frozen=True)
class LimitesVector:
    """Topes locales sintéticos, NO autorizaciones de transferencia operativa."""

    max_bytes_respuesta: int = 8 * 1024 * 1024
    profundidad: int = 32
    unidades_documento: int = 500_000
    elementos_lista: int = 100_000
    propiedades_objeto: int = 256
    caracteres_cadena: int = 65_536
    entidades_pagina: int = 2000
    atributos_entidad: int = 128
    anillos_entidad: int = 256
    coordenadas_entidad: int = 50_000  # Posiciones, no componentes escalares.
    coordenadas_pagina: int = 100_000
    max_paginas: int = 100
    entidades_total: int = 20_000
    bytes_total: int = 64 * 1024 * 1024
    bytes_auxiliares: int = 8 * 1024 * 1024

    def __post_init__(self):
        for f in fields(self):
            _entero(getattr(self, f.name), 1, 512 * 1024 * 1024)
        if self.profundidad > 64:
            raise ValueError("Profundidad vectorial excesiva")


@dataclass(frozen=True)
class ReferenciaEspacial:
    wkid: int
    latest_wkid: int | None = None

    def __post_init__(self):
        _entero(self.wkid, 1)
        if self.latest_wkid is not None:
            _entero(self.latest_wkid, 1)

    def declaracion(self):
        return {"wkid": self.wkid, **({"latestWkid": self.latest_wkid} if self.latest_wkid is not None else {})}


@dataclass(frozen=True)
class RecursoVector:
    fuente: Fuente
    producto_id: str
    recurso_id: str
    servicio_id: str
    capa_id: int
    procedencia: ProcedenciaCatalogo = field(repr=False)

    def __post_init__(self):
        if type(self.fuente) is not Fuente or type(self.procedencia) is not ProcedenciaCatalogo:
            raise TypeError("Fuente y procedencia tipadas requeridas")
        for v in (self.producto_id, self.recurso_id, self.servicio_id):
            _texto(v)
        _entero(self.capa_id)


@dataclass(frozen=True)
class CampoVector:
    nombre: str
    tipo: TipoCampo
    nullable: bool = False

    def __post_init__(self):
        _texto(self.nombre, 128)
        if type(self.tipo) is not TipoCampo or type(self.nullable) is not bool:
            raise TypeError("Tipo y nulabilidad explícitos requeridos")


@dataclass(frozen=True)
class ContratoFeatureSet:
    campos: tuple[CampoVector, ...]
    campo_oid: str
    referencia: ReferenciaEspacial
    geometria: str = "esriGeometryPolygon"
    dimensiones: int = 2

    def __post_init__(self):
        if (type(self.campos) is not tuple or not 1 <= len(self.campos) <= 128
                or any(type(c) is not CampoVector for c in self.campos)
                or type(self.referencia) is not ReferenciaEspacial):
            raise ValueError("Esquema vectorial no admitido")
        if len({c.nombre for c in self.campos}) != len(self.campos):
            raise ValueError("Campos duplicados")
        oids = [c for c in self.campos if c.tipo is TipoCampo.OID]
        if len(oids) != 1 or oids[0].nombre != self.campo_oid or oids[0].nullable:
            raise ValueError("Campo OID no coherente")
        if self.geometria != "esriGeometryPolygon" or type(self.dimensiones) is not int or self.dimensiones != 2:
            raise ValueError("Solo polígonos lineales XY en este prototipo")


@dataclass(frozen=True)
class ConsultaVector:
    adquisicion_id: str
    consulta_id: str
    recurso: RecursoVector
    contrato: ContratoFeatureSet
    parametros: Mapping[str, str] = field(repr=False)
    creada_utc: datetime
    version_contrato: str = VERSION_CONTRATO

    def __post_init__(self):
        _texto(self.adquisicion_id)
        _texto(self.consulta_id)
        if type(self.recurso) is not RecursoVector or type(self.contrato) is not ContratoFeatureSet:
            raise TypeError("Recurso y contrato tipados requeridos")
        if self.version_contrato != VERSION_CONTRATO:
            raise ValueError("Versión contractual no soportada")
        object.__setattr__(self, "creada_utc", _utc(self.creada_utc))
        object.__setattr__(self, "parametros", _parametros(self.parametros))
        reservados = {"resultOffset", "resultRecordCount", "objectIds", "orderByFields"}
        if reservados.intersection(self.parametros):
            raise ValueError("Paginación reservada al coordinador")

    @property
    def huella(self):
        # Identidad de consulta completa, no identidad física de una página.
        r, c = self.recurso, self.contrato
        d = [self.version_contrato, self.consulta_id, r.fuente.proveedor, r.fuente.identificador,
             r.producto_id, r.recurso_id, r.servicio_id, r.capa_id, dict(self.parametros),
             [(x.nombre, x.tipo.value, x.nullable) for x in c.campos], c.campo_oid,
             c.referencia.declaracion(), c.geometria, c.dimensiones]
        return hashlib.sha256(json.dumps(d, sort_keys=True, ensure_ascii=True).encode()).hexdigest()


@dataclass(frozen=True)
class EvidenciaConjunto:
    huella_consulta: str
    obtenida_utc: datetime
    referencia: str = field(repr=False)
    total: int | None = None
    object_ids: tuple[int, ...] | None = field(default=None, repr=False)
    ids_obtenidos_utc: datetime | None = None
    instantanea_id: str | None = field(default=None, repr=False)
    instantanea_consistente: bool = False

    def __post_init__(self):
        if (type(self.huella_consulta) is not str or len(self.huella_consulta) != 64
                or any(c not in "0123456789abcdef" for c in self.huella_consulta)):
            raise ValueError("Huella de consulta no admitida")
        _texto(self.referencia)
        object.__setattr__(self, "obtenida_utc", _utc(self.obtenida_utc))
        if self.total is not None:
            _entero(self.total)
        if self.object_ids is not None:
            if type(self.object_ids) is not tuple or len(self.object_ids) > 100_000:
                raise ValueError("Evidencia de identificadores excesiva")
            for v in self.object_ids:
                _entero(v)
            if len(set(self.object_ids)) != len(self.object_ids) or self.ids_obtenidos_utc is None:
                raise ValueError("Identificadores ambiguos o sin fecha")
            object.__setattr__(self, "ids_obtenidos_utc", _utc(self.ids_obtenidos_utc))
        elif self.ids_obtenidos_utc is not None:
            raise ValueError("Fecha de identificadores sin identificadores")
        if type(self.instantanea_consistente) is not bool:
            raise TypeError("Garantía de instantánea no admitida")
        if self.instantanea_id is not None:
            _texto(self.instantanea_id)
        if self.instantanea_consistente and self.instantanea_id is None:
            raise ValueError("Garantía sin identidad de instantánea")


@dataclass(frozen=True)
class SolicitudPagina:
    adquisicion_id: str
    huella_consulta: str
    numero: int
    parametros: Mapping[str, str] = field(repr=False)

    def __post_init__(self):
        _texto(self.adquisicion_id)
        _texto(self.huella_consulta)
        _entero(self.numero, 1)
        object.__setattr__(self, "parametros", _parametros(self.parametros))


@dataclass(frozen=True)
class RespuestaSintetica:
    respuesta_id: str
    obtenida_utc: datetime
    contenido: bytes = field(repr=False)
    solicitud: SolicitudPagina | None = field(default=None, repr=False)
    codigo_http: int = 200
    transferencia_completa: bool = True
    longitud_declarada: int | None = None
    instantanea_id: str | None = field(default=None, repr=False)
    total_observado: int | None = None
    interrumpida: bool = False

    def __post_init__(self):
        _texto(self.respuesta_id)
        object.__setattr__(self, "obtenida_utc", _utc(self.obtenida_utc))
        if type(self.contenido) is not bytes:
            raise TypeError("Cuerpo sintético en bytes requerido")
        if self.solicitud is not None and type(self.solicitud) is not SolicitudPagina:
            raise TypeError("Solicitud tipada requerida")
        _entero(self.codigo_http, 100, 599)
        for x in (self.transferencia_completa, self.interrumpida):
            if type(x) is not bool:
                raise TypeError("Estado de transferencia no admitido")
        for x in (self.longitud_declarada, self.total_observado):
            if x is not None:
                _entero(x)
        if self.instantanea_id is not None:
            _texto(self.instantanea_id)


@dataclass(frozen=True)
class EntidadVector:
    object_id_observado: int
    atributos: Mapping[str, object] = field(repr=False)
    estado_geometria: EstadoGeometria
    geometria: Mapping[str, object] | None = field(repr=False)
    identidad_logica: str | None = None  # Nunca se infiere del OID ni del hash.

    def __post_init__(self):
        _entero(self.object_id_observado)
        # Las salidas del validador ya son snapshots inmutables; impedir que un
        # constructor público retenga mapas/listas mutables suministrados fuera.
        if type(self.atributos) is not MappingProxyType or any(
                type(v) not in (str, int, float, bool, type(None)) for v in self.atributos.values()):
            raise ValueError("Atributos escalares inmutables requeridos")
        object.__setattr__(self, "atributos", _congelar(self.atributos))
        if type(self.estado_geometria) is not EstadoGeometria:
            raise TypeError("Estado geométrico requerido")
        if self.estado_geometria is EstadoGeometria.PRESENTE:
            if type(self.geometria) is not MappingProxyType:
                raise ValueError("Geometría validada inmutable requerida")
            object.__setattr__(self, "geometria", _congelar(self.geometria))
        elif self.geometria is not None:
            raise ValueError("Geometría contradictoria")
        if self.identidad_logica is not None:
            _texto(self.identidad_logica)


@dataclass(frozen=True)
class PaginaValidada:
    respuesta: RespuestaSintetica = field(repr=False)
    estado: EstadoPagina
    entidades: tuple[EntidadVector, ...] = field(default=(), repr=False)
    referencia_declarada: Mapping[str, object] | None = field(default=None, repr=False)
    exceeded_transfer_limit: bool | None = None
    sha256: str | None = None
    bytes_recibidos: int = 0
    coordenadas: int = 0
    diagnosticos: tuple[str, ...] = ()

    def __post_init__(self):
        if (type(self.respuesta) is not RespuestaSintetica or type(self.estado) is not EstadoPagina
                or type(self.entidades) is not tuple or any(type(e) is not EntidadVector for e in self.entidades)
                or type(self.diagnosticos) is not tuple or any(type(d) is not str for d in self.diagnosticos)):
            raise TypeError("Salida de página tipada e inmutable requerida")
        if self.referencia_declarada is not None:
            object.__setattr__(self, "referencia_declarada", _congelar(self.referencia_declarada))


@dataclass(frozen=True)
class ReciboPagina:
    solicitud: SolicitudPagina = field(repr=False)
    respuesta_id: str
    obtenida_utc: datetime
    sha256: str | None
    bytes_recibidos: int
    entidades: int
    estado: EstadoPagina
    exceeded_transfer_limit: bool | None
    solicitud_observada: SolicitudPagina | None = field(default=None, repr=False)

    def __post_init__(self):
        if (type(self.solicitud) is not SolicitudPagina or type(self.estado) is not EstadoPagina
                or self.solicitud_observada is not None and type(self.solicitud_observada) is not SolicitudPagina):
            raise TypeError("Recibo de página tipado requerido")
        _texto(self.respuesta_id)
        object.__setattr__(self, "obtenida_utc", _utc(self.obtenida_utc))


@dataclass(frozen=True)
class ResultadoVector:
    consulta: ConsultaVector = field(repr=False)
    evidencia: EvidenciaConjunto | None = field(repr=False)
    estrategia: EstrategiaPaginacion
    completitud: EstadoCompletitud
    recibos: tuple[ReciboPagina, ...]
    entidades_recibidas: int
    bytes_recibidos: int
    bytes_inspeccionados: int
    diagnosticos: tuple[str, ...]
    limitaciones: tuple[str, ...]
    limites: LimitesVector

    def __post_init__(self):
        if (type(self.consulta) is not ConsultaVector or type(self.estrategia) is not EstrategiaPaginacion
                or type(self.completitud) is not EstadoCompletitud or type(self.limites) is not LimitesVector
                or self.evidencia is not None and type(self.evidencia) is not EvidenciaConjunto
                or type(self.recibos) is not tuple or any(type(r) is not ReciboPagina for r in self.recibos)):
            raise TypeError("Resultado vectorial tipado e inmutable requerido")
        for valores in (self.diagnosticos, self.limitaciones):
            if type(valores) is not tuple or any(type(v) is not str for v in valores):
                raise TypeError("Diagnósticos inmutables requeridos")
