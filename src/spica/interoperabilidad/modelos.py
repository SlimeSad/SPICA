"""Instantáneas documentales; no leen datos ni certifican evidencia externa."""

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
import math

from ..adquisicion.nucleo import Fuente
from ..adquisicion.nucleo.temporal import instante_utc, validar_intervalo
from ..adquisicion.catalogo.modelos import EstadoVerificacion, ProcedenciaCatalogo
from ..adquisicion.vectorial.modelos import ReferenciaEspacial


VERSION_EVALUADOR = "0.1.0"


def _texto(v, opcional=False):
    if v is None and opcional:
        return
    if type(v) is not str or not v.strip() or len(v) > 4096:
        raise ValueError("texto_literal_acotado_requerido")


def _tupla(v, tipo, maximo=64):
    if type(v) is not tuple or len(v) > maximo or any(type(x) is not tipo for x in v):
        raise TypeError("tupla_tipificada_inmutable_requerida")


def _originales(v):
    _tupla(v, tuple)
    for par in v:
        if len(par) != 2:
            raise ValueError("par_original_requerido")
        _texto(par[0])
        if type(par[1]) is not str or len(par[1]) > 4096:
            raise ValueError("valor_original_textual_requerido")
    if len({k for k, _ in v}) != len(v):
        raise ValueError("campo_original_repetido")


def _numeros(v, cantidad):
    if type(v) is not tuple or len(v) != cantidad:
        raise TypeError("coordenadas_inmutables_requeridas")
    for x in v:
        if type(x) not in (int, float, Decimal):
            raise TypeError("numero_sin_conversion_requerido")
        if type(x) is Decimal:
            finito = x.is_finite()
        else:
            finito = type(x) is int or math.isfinite(x)
        if not finito:
            raise ValueError("numero_no_finito")


class DimensionEvaluacion(Enum):
    ESPACIAL = "espacial"
    TEMPORAL = "temporal"
    AMBAS = "ambas"


class EstadoAptitud(Enum):
    APTO_ESTRUCTURALMENTE = "apto_estructuralmente"
    PENDIENTE_DE_EVIDENCIA = "pendiente_de_evidencia"
    INCOMPATIBLE = "incompatible"
    NO_EVALUABLE = "no_evaluable"


class RepresentacionEspacial(Enum):
    DESCONOCIDA = "desconocida"
    PUNTUAL = "puntual"
    VECTORIAL = "vectorial"
    RASTER = "raster"  # Se registra; su aptitud aún no se evalúa.


class AmbitoCRS(Enum):
    GEOMETRIA = "geometria"
    EXTENSION = "extension"
    ORIGEN = "origen"


@dataclass(frozen=True)
class Respaldo:
    estado: EstadoVerificacion = EstadoVerificacion.DESCONOCIDO
    procedencia: ProcedenciaCatalogo | None = None

    def __post_init__(self):
        if type(self.estado) is not EstadoVerificacion:
            raise TypeError("estado_de_verificacion_requerido")
        if self.procedencia is not None and type(self.procedencia) is not ProcedenciaCatalogo:
            raise TypeError("procedencia_tipificada_requerida")
        if self.estado is EstadoVerificacion.VERIFICADO and (
                self.procedencia is None or self.procedencia.evidencia is None):
            raise ValueError("verificado_requiere_referencia_de_evidencia")


@dataclass(frozen=True)
class IdentidadRecurso:
    fuente: Fuente
    recurso_id: str
    producto_id: str | None = None
    localizador: str | None = None  # Distingue publicaciones; no se abre ni normaliza.

    def __post_init__(self):
        if type(self.fuente) is not Fuente:
            raise TypeError("fuente_del_nucleo_requerida")
        _texto(self.recurso_id)
        _texto(self.producto_id, True)
        _texto(self.localizador, True)


@dataclass(frozen=True)
class CRSDeclarado:
    ambito: AmbitoCRS
    declaracion: ReferenciaEspacial | str | None = None
    definicion: str | None = None  # Referencia documental, no una resolución EPSG.
    unidades_ejes: tuple[str, ...] = ()
    respaldo: Respaldo = field(default_factory=Respaldo)

    def __post_init__(self):
        if type(self.ambito) is not AmbitoCRS or type(self.respaldo) is not Respaldo:
            raise TypeError("crs_y_respaldo_tipificados_requeridos")
        if self.declaracion is not None and type(self.declaracion) not in (str, ReferenciaEspacial):
            raise TypeError("declaracion_crs_no_admitida")
        if type(self.declaracion) is str:
            _texto(self.declaracion)
        if self.declaracion is None and self.respaldo.estado is not EstadoVerificacion.DESCONOCIDO:
            raise ValueError("crs_desconocido_sin_declaracion")
        _texto(self.definicion, True)
        _tupla(self.unidades_ejes, str, 2)
        if len(self.unidades_ejes) not in (0, 2):
            raise ValueError("unidades_xy_o_desconocidas_requeridas")
        for u in self.unidades_ejes:
            _texto(u)


@dataclass(frozen=True)
class MarcoEspacial:
    representacion: RepresentacionEspacial = RepresentacionEspacial.DESCONOCIDA
    geometria_declarada: str | None = None
    respaldo_geometria: Respaldo = field(default_factory=Respaldo)
    ubicacion_declarada: tuple[tuple[str, str], ...] = ()
    identificador_ubicacion: str | None = None
    identidad_ambigua: bool = False
    respaldo_identidad: Respaldo = field(default_factory=Respaldo)
    coordenadas: tuple[int | float | Decimal, ...] | None = None
    respaldo_coordenadas: Respaldo = field(default_factory=Respaldo)
    crs: tuple[CRSDeclarado, ...] = ()
    extension: tuple[int | float | Decimal, ...] | None = None  # xmin,ymin,xmax,ymax
    respaldo_extension: Respaldo = field(default_factory=Respaldo)
    cobertura_anunciada: str | None = None
    cobertura_observada: str | None = None
    respaldo_cobertura: Respaldo = field(default_factory=Respaldo)
    precision_declarada: str | None = None
    incertidumbre: str | None = None
    respaldo_calidad: Respaldo = field(default_factory=Respaldo)

    def __post_init__(self):
        if type(self.representacion) is not RepresentacionEspacial or type(self.identidad_ambigua) is not bool:
            raise TypeError("representacion_e_identidad_tipificadas_requeridas")
        for nombre in ("respaldo_geometria", "respaldo_identidad", "respaldo_coordenadas",
                       "respaldo_extension", "respaldo_cobertura", "respaldo_calidad"):
            if type(getattr(self, nombre)) is not Respaldo:
                raise TypeError("respaldo_tipificado_requerido")
        for nombre in ("geometria_declarada", "identificador_ubicacion", "cobertura_anunciada",
                       "cobertura_observada", "precision_declarada", "incertidumbre"):
            _texto(getattr(self, nombre), True)
        _originales(self.ubicacion_declarada)
        _tupla(self.crs, CRSDeclarado, 3)
        if len({c.ambito for c in self.crs}) != len(self.crs):
            raise ValueError("ambito_crs_repetido")
        if self.coordenadas is not None:
            _numeros(self.coordenadas, 2)
        elif self.respaldo_coordenadas.estado is not EstadoVerificacion.DESCONOCIDO:
            raise ValueError("coordenadas_ausentes_no_pueden_declararse_verificadas")
        if self.extension is not None:
            _numeros(self.extension, 4)
            if self.extension[0] > self.extension[2] or self.extension[1] > self.extension[3]:
                raise ValueError("extension_invertida")
        elif self.respaldo_extension.estado is not EstadoVerificacion.DESCONOCIDO:
            raise ValueError("extension_ausente_con_estado_conocido")


@dataclass(frozen=True)
class PeriodoTemporal:
    inicio: date | datetime
    fin: date | datetime
    respaldo: Respaldo = field(default_factory=Respaldo)
    limites_inclusivos: tuple[bool, bool] | None = None

    def __post_init__(self):
        if type(self.inicio) not in (date, datetime) or type(self.fin) is not type(self.inicio):
            raise TypeError("extremos_temporales_homogeneos_requeridos")
        if type(self.respaldo) is not Respaldo:
            raise TypeError("respaldo_tipificado_requerido")
        if type(self.inicio) is datetime:
            validar_intervalo(self.inicio, self.fin, permitir_civil=True)
        elif self.inicio > self.fin:
            raise ValueError("periodo_civil_invertido")
        if self.limites_inclusivos is not None:
            _tupla(self.limites_inclusivos, bool, 2)
            if len(self.limites_inclusivos) != 2:
                raise ValueError("dos_limites_requeridos")
            if type(self.inicio) is datetime and self.inicio.utcoffset() is not None:
                iguales = instante_utc(self.inicio) == instante_utc(self.fin)
            else:
                iguales = self.inicio == self.fin
            if iguales and self.limites_inclusivos != (True, True):
                raise ValueError("periodo_puntual_vacio")
            if type(self.inicio) is date:
                cantidad = (self.fin - self.inicio).days + 1 - sum(not x for x in self.limites_inclusivos)
                if cantidad <= 0:
                    raise ValueError("periodo_civil_sin_fechas")


@dataclass(frozen=True)
class MarcoTemporal:
    valores_originales: tuple[tuple[str, str], ...] = ()
    fecha_observacion: date | datetime | None = None
    resolucion: str | None = None
    zona_horaria_declarada: str | None = None
    convencion: str | None = None
    observaciones: PeriodoTemporal | None = None
    publicacion: PeriodoTemporal | None = None
    adquirido: datetime | None = None
    vigencia_metadatos: PeriodoTemporal | None = None
    incertidumbre: str | None = None
    respaldo_interpretacion: Respaldo = field(default_factory=Respaldo)

    def __post_init__(self):
        _originales(self.valores_originales)
        if self.fecha_observacion is not None and type(self.fecha_observacion) not in (date, datetime):
            raise TypeError("fecha_interpretada_tipificada_requerida")
        if type(self.fecha_observacion) is datetime and self.fecha_observacion.utcoffset() is not None:
            instante_utc(self.fecha_observacion)
        for nombre in ("resolucion", "zona_horaria_declarada", "convencion", "incertidumbre"):
            _texto(getattr(self, nombre), True)
        for p in (self.observaciones, self.publicacion, self.vigencia_metadatos):
            if p is not None and type(p) is not PeriodoTemporal:
                raise TypeError("periodo_tipificado_requerido")
        if self.adquirido is not None:
            instante_utc(self.adquirido)  # Solo valida; conserva el objeto original.
        if type(self.respaldo_interpretacion) is not Respaldo:
            raise TypeError("respaldo_tipificado_requerido")


@dataclass(frozen=True)
class RecursoInteroperable:
    identidad: IdentidadRecurso
    revision_metadatos: str
    procedencia: ProcedenciaCatalogo | None = None
    espacial: MarcoEspacial | None = None
    temporal: MarcoTemporal | None = None
    version_institucional: str | None = None
    atributos_declarados: tuple[str, ...] = ()
    condiciones_uso: str | None = None
    correspondencias: tuple[ProcedenciaCatalogo, ...] = ()
    sustituye_revision: str | None = None
    contradicciones_declaradas: tuple[str, ...] = ()

    def __post_init__(self):
        if type(self.identidad) is not IdentidadRecurso:
            raise TypeError("identidad_tipificada_requerida")
        _texto(self.revision_metadatos)
        for x in (self.version_institucional, self.condiciones_uso, self.sustituye_revision):
            _texto(x, True)
        for v, tipo in ((self.procedencia, ProcedenciaCatalogo), (self.espacial, MarcoEspacial),
                        (self.temporal, MarcoTemporal)):
            if v is not None and type(v) is not tipo:
                raise TypeError("metadatos_tipificados_requeridos")
        for textos in (self.atributos_declarados, self.contradicciones_declaradas):
            _tupla(textos, str)
            for x in textos:
                _texto(x)
            if len(set(textos)) != len(textos):
                raise ValueError("metadatos_repetidos")
        _tupla(self.correspondencias, ProcedenciaCatalogo, 16)
        if self.sustituye_revision == self.revision_metadatos:
            raise ValueError("revision_no_puede_sustituirse_a_si_misma")


RESTRICCIONES = (
    "preparacion_documental_sin_asociacion_ejecutada", "sin_validacion_cientifica",
    "sin_reproyeccion_distancias_intersecciones_o_topologia", "sin_autorizacion_de_red_o_uso",
    "evidencia_aportada_no_autenticada_por_el_evaluador", "vigencia_actual_no_comprobada",
)


@dataclass(frozen=True)
class ResultadoAptitud:
    recursos: tuple[RecursoInteroperable, RecursoInteroperable] = field(repr=False)
    dimension: DimensionEvaluacion
    estado: EstadoAptitud
    evidencias: tuple[ProcedenciaCatalogo, ...]
    motivos: tuple[str, ...]
    faltantes: tuple[str, ...]
    contradicciones: tuple[str, ...]
    restricciones: tuple[str, ...] = field(default=RESTRICCIONES, init=False)
    version_evaluador: str = field(default=VERSION_EVALUADOR, init=False)

    def __post_init__(self):
        _tupla(self.recursos, RecursoInteroperable, 2)
        if len(self.recursos) != 2 or type(self.dimension) is not DimensionEvaluacion or type(self.estado) is not EstadoAptitud:
            raise TypeError("resultado_de_dos_recursos_tipificado_requerido")
        _tupla(self.evidencias, ProcedenciaCatalogo, 64)
        for textos in (self.motivos, self.faltantes, self.contradicciones):
            _tupla(textos, str, 256)
            for x in textos:
                _texto(x)
        if not self.motivos:
            raise ValueError("resultado_sin_motivos")
        if self.estado is EstadoAptitud.APTO_ESTRUCTURALMENTE and (self.faltantes or self.contradicciones):
            raise ValueError("aptitud_con_evidencia_contradictoria_o_faltante")
        if self.estado is EstadoAptitud.APTO_ESTRUCTURALMENTE and not self.evidencias:
            raise ValueError("aptitud_sin_evidencia")
