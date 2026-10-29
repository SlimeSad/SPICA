"""Metadatos declarados y evidencia de catálogo; no representan datos adquiridos."""

from dataclasses import dataclass, fields
from datetime import datetime, timezone
from enum import Enum
import math

from ..nucleo import Fuente
from ..nucleo.temporal import instante_utc, validar_intervalo


class EstadoVerificacion(Enum):
    DESCONOCIDO = "desconocido"
    DECLARADO = "declarado"
    VERIFICADO = "verificado"


class MecanismoAdquisicion(Enum):
    API_REST = "api_rest"
    HTTP_DIRECTO = "http_directo"
    PORTAL_ASISTIDO = "portal_asistido"
    GEOESPACIAL = "servicio_geoespacial"
    MANUAL = "importacion_manual"
    INSTITUCIONAL = "importacion_institucional"
    OTRO = "otro"


class CoincidenciaTemporal(Enum):
    SIN_FILTRO = "sin_filtro_temporal"
    DESCONOCIDA = "desconocida"
    CONTIENE_PERIODO = "intervalo_contiene_periodo"
    SOLAPAMIENTO_PARCIAL = "solapamiento_parcial"
    FUERA_COBERTURA_CONOCIDA = "fuera_cobertura_conocida"


def _texto(valor, nombre, obligatorio=False):
    if valor is None and not obligatorio:
        return
    if not isinstance(valor, str) or not valor.strip():
        raise ValueError(f"{nombre} debe ser texto no vacío")


def _fecha(valor, nombre, obligatoria=False, zona=True):
    if valor is None and not obligatoria:
        return
    if not isinstance(valor, datetime) or (zona and valor.utcoffset() is None):
        raise ValueError(f"{nombre} debe ser datetime con zona conocida")
    if valor.utcoffset() is not None:
        instante_utc(valor)


@dataclass(frozen=True)
class ProcedenciaCatalogo:
    referencia: str
    revisada_utc: datetime
    metodo: str
    evidencia: str | None = None

    def __post_init__(self):
        _texto(self.referencia, "referencia", True)
        _texto(self.metodo, "metodo", True)
        _texto(self.evidencia, "evidencia")
        _fecha(self.revisada_utc, "revisada_utc", True)
        object.__setattr__(self, "revisada_utc", self.revisada_utc.astimezone(timezone.utc))


class _Entidad:
    def __post_init__(self):
        if not isinstance(self.fuente, Fuente):
            raise TypeError("Se requiere Fuente del núcleo")
        if not isinstance(self.procedencia, ProcedenciaCatalogo):
            raise TypeError("Se requiere procedencia explícita")
        for campo in fields(self):
            valor = getattr(self, campo.name)
            if campo.type in (str, str | None):
                _texto(valor, campo.name)
        for nombre in ("identificador", "producto_id", "id_interno"):
            if hasattr(self, nombre):
                _texto(getattr(self, nombre), nombre, True)


@dataclass(frozen=True)
class FuenteCatalogo(_Entidad):
    fuente: Fuente
    procedencia: ProcedenciaCatalogo
    nombre: str | None = None
    tipo_organizacion: str | None = None
    referencia_oficial: str | None = None
    revisada_utc: datetime | None = None
    estado: EstadoVerificacion = EstadoVerificacion.DESCONOCIDO

    def __post_init__(self):
        super().__post_init__()
        _fecha(self.revisada_utc, "revisada_utc")
        if self.revisada_utc is not None:
            object.__setattr__(self, "revisada_utc", self.revisada_utc.astimezone(timezone.utc))
        _verificacion(self.estado, self.revisada_utc, self.procedencia)


@dataclass(frozen=True)
class ProductoCatalogo(_Entidad):
    fuente: Fuente
    identificador: str
    procedencia: ProcedenciaCatalogo
    nombre: str | None = None
    descripcion: str | None = None
    familia: str | None = None
    formatos_declarados: tuple[str, ...] = ()
    version: str | None = None
    modalidad_acceso: str | None = None
    restricciones_licencia: str | None = None
    autenticacion_requerida: bool | None = None
    descripcion_autenticacion: str | None = None
    utiliza_estaciones: bool | None = None

    def __post_init__(self):
        super().__post_init__()
        if isinstance(self.formatos_declarados, str):
            raise TypeError("formatos_declarados debe ser una colección")
        object.__setattr__(self, "formatos_declarados", tuple(self.formatos_declarados))
        for formato in self.formatos_declarados:
            _texto(formato, "formato", True)
        for valor in (self.autenticacion_requerida, self.utiliza_estaciones):
            if valor is not None and type(valor) is not bool:
                raise TypeError("Los indicadores opcionales deben ser bool o None")


@dataclass(frozen=True)
class EstacionCatalogo(_Entidad):
    fuente: Fuente
    producto_id: str
    identificador: str
    procedencia: ProcedenciaCatalogo
    red_id: str | None = None
    nombre: str | None = None
    tipo_estacion: str | None = None
    coordenada_x: float | None = None
    coordenada_y: float | None = None
    altitud: float | None = None
    sistema_referencia: str | None = None
    estado_operativo: str | None = None

    def __post_init__(self):
        super().__post_init__()
        if (self.coordenada_x is None) != (self.coordenada_y is None):
            raise ValueError("Las coordenadas deben declararse juntas")
        for valor in (self.coordenada_x, self.coordenada_y, self.altitud):
            if valor is not None and (type(valor) not in (int, float) or not math.isfinite(valor)):
                raise ValueError("Las coordenadas/altitud deben ser números finitos o None")


@dataclass(frozen=True)
class VariableCatalogo(_Entidad):
    id_interno: str
    fuente: Fuente
    producto_id: str
    procedencia: ProcedenciaCatalogo
    codigo_original: str | None = None
    nombre_original: str | None = None
    descripcion: str | None = None
    unidad_declarada: str | None = None
    frecuencia_declarada: str | None = None
    tipo_medicion: str | None = None
    version_diccionario: str | None = None
    procedencia_diccionario: str | None = None


def _verificacion(estado, comprobada, procedencia):
    if not isinstance(estado, EstadoVerificacion):
        raise TypeError("Se requiere EstadoVerificacion")
    if estado is EstadoVerificacion.VERIFICADO:
        if comprobada is None or procedencia.evidencia is None:
            raise ValueError("Verificado exige fecha de comprobación y evidencia explícita")


@dataclass(frozen=True)
class DisponibilidadCatalogo(_Entidad):
    identificador: str
    fuente: Fuente
    producto_id: str
    procedencia: ProcedenciaCatalogo
    estacion_id: str | None = None
    variable_id: str | None = None
    inicio: datetime | None = None
    fin: datetime | None = None
    precision_temporal: str | None = None
    zona_horaria: str | None = None
    frecuencia_declarada: str | None = None
    cobertura_parcial: bool | None = None
    estado: EstadoVerificacion = EstadoVerificacion.DESCONOCIDO
    comprobada_utc: datetime | None = None

    def __post_init__(self):
        super().__post_init__()
        for valor in (self.inicio, self.fin):
            _fecha(valor, "extremo temporal", zona=False)
        if self.inicio is not None and self.fin is not None:
            validar_intervalo(self.inicio, self.fin, permitir_civil=True)
        if self.cobertura_parcial is not None and type(self.cobertura_parcial) is not bool:
            raise TypeError("cobertura_parcial debe ser bool o None")
        _fecha(self.comprobada_utc, "comprobada_utc")
        if self.comprobada_utc is not None:
            object.__setattr__(self, "comprobada_utc", self.comprobada_utc.astimezone(timezone.utc))
        _verificacion(self.estado, self.comprobada_utc, self.procedencia)


@dataclass(frozen=True)
class CapacidadCatalogo(_Entidad):
    identificador: str
    fuente: Fuente
    producto_id: str
    mecanismo: MecanismoAdquisicion
    procedencia: ProcedenciaCatalogo
    estado: EstadoVerificacion = EstadoVerificacion.DESCONOCIDO
    comprobada_utc: datetime | None = None
    otro_mecanismo: str | None = None

    def __post_init__(self):
        super().__post_init__()
        if not isinstance(self.mecanismo, MecanismoAdquisicion):
            raise TypeError("Se requiere MecanismoAdquisicion")
        if self.mecanismo is MecanismoAdquisicion.OTRO:
            _texto(self.otro_mecanismo, "otro_mecanismo", True)
        _fecha(self.comprobada_utc, "comprobada_utc")
        if self.comprobada_utc is not None:
            object.__setattr__(self, "comprobada_utc", self.comprobada_utc.astimezone(timezone.utc))
        _verificacion(self.estado, self.comprobada_utc, self.procedencia)


EntidadCatalogo = FuenteCatalogo | ProductoCatalogo | EstacionCatalogo | VariableCatalogo | DisponibilidadCatalogo | CapacidadCatalogo


@dataclass(frozen=True)
class FiltroCatalogo:
    fuentes: tuple[Fuente, ...] = ()
    productos: tuple[str, ...] = ()
    estaciones: tuple[str, ...] = ()
    variables: tuple[str, ...] = ()  # IDs internos, nunca conversiones de nombre.
    codigos_variables: tuple[str, ...] = ()  # Códigos originales exactos del proveedor.
    frecuencias: tuple[str, ...] = ()
    mecanismos: tuple[MecanismoAdquisicion, ...] = ()
    inicio: datetime | None = None
    fin: datetime | None = None

    def __post_init__(self):
        for nombre in ("fuentes", "productos", "estaciones", "variables", "codigos_variables", "frecuencias", "mecanismos"):
            valores = getattr(self, nombre)
            if isinstance(valores, str):
                raise TypeError("Los filtros deben ser colecciones")
            valores = tuple(valores)
            object.__setattr__(self, nombre, valores)
            for valor in valores:
                if nombre == "fuentes" and not isinstance(valor, Fuente):
                    raise TypeError("Se requiere Fuente")
                elif nombre == "mecanismos" and not isinstance(valor, MecanismoAdquisicion):
                    raise TypeError("Se requiere MecanismoAdquisicion")
                elif nombre not in ("fuentes", "mecanismos"):
                    _texto(valor, nombre, True)
        _fecha(self.inicio, "inicio solicitado")
        _fecha(self.fin, "fin solicitado")
        if (self.inicio is None) != (self.fin is None):
            raise ValueError("La consulta temporal requiere ambos extremos")
        if self.inicio is not None:
            validar_intervalo(self.inicio, self.fin)


@dataclass(frozen=True)
class RegistroCatalogo:
    entidad: EntidadCatalogo
    revision: int


@dataclass(frozen=True)
class EvaluacionDisponibilidad:
    disponibilidad: DisponibilidadCatalogo
    coincidencia_temporal: CoincidenciaTemporal
    alcance_exacto: bool


@dataclass(frozen=True)
class ResultadoProducto:
    producto: ProductoCatalogo
    disponibilidades: tuple[EvaluacionDisponibilidad, ...]
    capacidades: tuple[CapacidadCatalogo, ...]
    sin_evidencia_del_alcance: bool
    mecanismo_desconocido: bool


@dataclass(frozen=True)
class ResultadoCatalogo:
    filtro: FiltroCatalogo
    productos: tuple[ResultadoProducto, ...]


class ErrorCatalogo(Exception):
    pass
