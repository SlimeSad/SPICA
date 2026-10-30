"""Contratos declarativos Nivel 1. No contienen algoritmos ni autorizan ejecución."""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import Enum
import re

from .modelos import EstadoEvaluacionQA, ProcedenciaQA, RegistroQA

VERSION_CONTRATO_CIENTIFICO = "1.0.0"


def _texto(valor, *, opcional=False, maximo=4096):
    if valor is None and opcional:
        return
    if not isinstance(valor, str) or not valor.strip() or len(valor) > maximo:
        raise ValueError("Texto requerido y acotado")


def _version(valor):
    if not isinstance(valor, str) or not re.fullmatch(r"(0|[1-9][0-9]{0,3})(\.(0|[1-9][0-9]{0,3})){2}", valor):
        raise ValueError("Versión requerida: mayor.menor.parche, sin sufijos")


def _tupla(valores, tipo, *, maximo=32):
    if not isinstance(valores, tuple) or len(valores) > maximo or any(not isinstance(v, tipo) for v in valores):
        raise ValueError("Tupla tipada y acotada requerida")


def _ids(valores):
    _tupla(valores, str)
    for v in valores:
        _texto(v, maximo=128)
    if len(set(valores)) != len(valores):
        raise ValueError("Referencias repetidas")


def _utc(valor):
    if not isinstance(valor, datetime) or valor.tzinfo is None or valor.utcoffset() != timedelta(0):
        raise ValueError("Fecha de revisión UTC consciente requerida")


class EstadoReglaCientifica(Enum):
    PROPUESTA = "propuesta"
    DOCUMENTADA = "documentada"
    APROBADA = "aprobada"
    SUSPENDIDA = "suspendida"
    OBSOLETA = "obsoleta"


class AmbitoReglaCientifica(Enum):
    UNIVERSAL = "universal"
    INSTITUCIONAL = "institucional"
    PRODUCTO = "producto"
    INSTRUMENTO = "instrumento"


class DimensionAplicabilidad(Enum):
    DISCIPLINA = "disciplina"
    VARIABLE = "variable"
    UNIDAD = "unidad"
    TIPO_MEDICION = "tipo_medicion"
    FRECUENCIA = "frecuencia"
    INSTITUCION = "institucion"
    PRODUCTO = "producto"
    TIPO_ESTACION = "tipo_estacion"
    INSTRUMENTO = "instrumento"
    GEOGRAFIA = "geografia"
    AMBIENTE = "ambiente"


class EstadoResultadoCientifico(Enum):
    COMPROBACION_SATISFECHA = "comprobacion_satisfecha"
    ALERTA = "alerta"
    SOSPECHA = "sospecha"
    PROBLEMA_DEMOSTRADO = "problema_demostrado"
    NO_EVALUADO = "no_evaluado"
    EVALUACION_INCOMPLETA = "evaluacion_incompleta"


@dataclass(frozen=True)
class ReferenciaCientifica:
    identificador: str
    procedencia: str
    titulo: str
    localizador: str  # DOI, URL, sección o referencia local; nunca se abre aquí.
    version_documento: str | None = None
    fecha_documento: date | None = None
    sha256_referencia: str | None = None

    def __post_init__(self):
        _texto(self.identificador, maximo=128)
        for v in (self.procedencia, self.titulo, self.localizador):
            _texto(v)
        _texto(self.version_documento, opcional=True, maximo=256)
        if self.fecha_documento is not None and type(self.fecha_documento) is not date:
            raise TypeError("Fecha documental civil requerida")
        if self.sha256_referencia is not None and (not isinstance(self.sha256_referencia, str)
                or not re.fullmatch(r"[0-9a-f]{64}", self.sha256_referencia)):
            raise ValueError("SHA de referencia no admitido")


@dataclass(frozen=True)
class CondicionAplicabilidad:
    dimension: DimensionAplicabilidad
    valores_permitidos: tuple[str, ...] = ()
    referencias: tuple[str, ...] = ()
    sin_restriccion: bool = False

    def __post_init__(self):
        if not isinstance(self.dimension, DimensionAplicabilidad) or type(self.sin_restriccion) is not bool:
            raise TypeError("Dimensión y modalidad tipadas requeridas")
        _ids(self.referencias)
        _tupla(self.valores_permitidos, str)
        for v in self.valores_permitidos:
            _texto(v, maximo=512)
        if len(set(self.valores_permitidos)) != len(self.valores_permitidos):
            raise ValueError("Condición repetida")
        if self.sin_restriccion == bool(self.valores_permitidos):
            raise ValueError("Elegir valores exactos o ausencia explícita de restricción")


@dataclass(frozen=True)
class MetodoCientifico:
    identificador: str  # Símbolo, nunca módulo, expresión, import ni callback.
    version: str
    descripcion: str
    referencias: tuple[str, ...] = ()

    def __post_init__(self):
        if not isinstance(self.identificador, str) or not re.fullmatch(r"[a-z][a-z0-9_]{0,63}", self.identificador):
            raise ValueError("Símbolo de método no admitido")
        _version(self.version)
        _texto(self.descripcion)
        _ids(self.referencias)


@dataclass(frozen=True)
class ParametroCientifico:
    nombre: str
    valor: str | int | bool | Decimal
    unidad: str | None = None
    referencias: tuple[str, ...] = ()

    def __post_init__(self):
        _texto(self.nombre, maximo=128)
        if type(self.valor) not in (str, int, bool, Decimal):
            raise TypeError("Solo datos escalares; no objetos ejecutables ni floats")
        if isinstance(self.valor, str):
            _texto(self.valor, maximo=512)
        if isinstance(self.valor, int) and self.valor.bit_length() > 256:
            raise ValueError("Entero fuera de presupuesto")
        if isinstance(self.valor, Decimal) and (not self.valor.is_finite() or len(str(self.valor)) > 512):
            raise ValueError("Decimal finito y acotado requerido")
        _texto(self.unidad, opcional=True, maximo=128)
        _ids(self.referencias)


@dataclass(frozen=True)
class IncertidumbreCientifica:
    descripcion: str  # No se interpreta como fórmula ni como incertidumbre cuantificada.
    referencias: tuple[str, ...] = ()

    def __post_init__(self):
        _texto(self.descripcion)
        _ids(self.referencias)


@dataclass(frozen=True)
class ReglaCientifica:
    identificador: str
    version: str
    nombre: str
    ambito: AmbitoReglaCientifica
    procedencia_normativa: str | None = None
    referencias: tuple[ReferenciaCientifica, ...] = ()
    aplicabilidad: tuple[CondicionAplicabilidad, ...] = ()
    parametros: tuple[ParametroCientifico, ...] = ()
    metodo: MetodoCientifico | None = None
    incertidumbre: IncertidumbreCientifica | None = None
    contradicciones_documentales: tuple[str, ...] = ()
    version_contrato: str = field(default=VERSION_CONTRATO_CIENTIFICO, init=False)

    def __post_init__(self):
        if not isinstance(self.identificador, str) or not re.fullmatch(r"L1-[A-Z0-9][A-Z0-9._-]{0,95}", self.identificador):
            raise ValueError("Identificador estable Nivel 1 requerido")
        _version(self.version)
        _texto(self.nombre)
        if not isinstance(self.ambito, AmbitoReglaCientifica):
            raise TypeError("Ámbito tipado requerido")
        _texto(self.procedencia_normativa, opcional=True)
        for valores, tipo in ((self.referencias, ReferenciaCientifica), (self.aplicabilidad, CondicionAplicabilidad),
                              (self.parametros, ParametroCientifico)):
            _tupla(valores, tipo)
        for claves in (tuple(r.identificador for r in self.referencias),
                       tuple(c.dimension for c in self.aplicabilidad), tuple(p.nombre for p in self.parametros)):
            if len(set(claves)) != len(claves):
                raise ValueError("Referencias, dimensiones o parámetros duplicados/contradictorios")
        if self.metodo is not None and not isinstance(self.metodo, MetodoCientifico):
            raise TypeError("Descriptor de método requerido")
        if self.incertidumbre is not None and not isinstance(self.incertidumbre, IncertidumbreCientifica):
            raise TypeError("Incertidumbre tipada requerida")
        _tupla(self.contradicciones_documentales, str)
        for v in self.contradicciones_documentales:
            _texto(v)
        conocidas = {r.identificador for r in self.referencias}
        componentes = (*self.aplicabilidad, *self.parametros,
                       *((self.metodo,) if self.metodo else ()),
                       *((self.incertidumbre,) if self.incertidumbre else ()))
        if any(not set(c.referencias) <= conocidas for c in componentes):
            raise ValueError("Referencia científica no registrada en la regla")


@dataclass(frozen=True)
class RevisionCientifica:
    responsable: str  # Referencia de rol/revisor, sin requerir datos personales.
    fecha_utc: datetime
    informe_referencia: str
    referencias_revisadas: tuple[str, ...] = ()
    aplicabilidad_demostrada: bool = False
    contradicciones: tuple[str, ...] = ()

    def __post_init__(self):
        _texto(self.responsable, maximo=256)
        _utc(self.fecha_utc)
        _texto(self.informe_referencia)
        _ids(self.referencias_revisadas)
        if type(self.aplicabilidad_demostrada) is not bool:
            raise TypeError("Declaración de aplicabilidad requerida")
        _tupla(self.contradicciones, str)
        for v in self.contradicciones:
            _texto(v)


@dataclass(frozen=True)
class RevisionReglaCientifica:
    regla: ReglaCientifica
    revision: int
    estado: EstadoReglaCientifica
    decision: RevisionCientifica | None = None

    def __post_init__(self):
        if not isinstance(self.regla, ReglaCientifica) or not isinstance(self.estado, EstadoReglaCientifica):
            raise TypeError("Revisión de regla tipada requerida")
        if type(self.revision) is not int or self.revision <= 0:
            raise ValueError("Revisión positiva requerida")
        if self.estado is EstadoReglaCientifica.PROPUESTA:
            if self.revision != 1 or self.decision is not None:
                raise ValueError("La propuesta inicia sin aprobación en revisión 1")
        elif self.revision < 2 or not isinstance(self.decision, RevisionCientifica):
            raise ValueError("Cambio de estado requiere decisión y revisión posterior")


@dataclass(frozen=True)
class DatoContextoCientifico:
    dimension: DimensionAplicabilidad
    valor: str
    evidencia: ReferenciaCientifica

    def __post_init__(self):
        if not isinstance(self.dimension, DimensionAplicabilidad) or not isinstance(self.evidencia, ReferenciaCientifica):
            raise TypeError("Contexto y evidencia tipados requeridos")
        _texto(self.valor, maximo=512)


@dataclass(frozen=True)
class ContextoCientifico:
    datos: tuple[DatoContextoCientifico, ...] = ()

    def __post_init__(self):
        _tupla(self.datos, DatoContextoCientifico)
        if len({d.dimension for d in self.datos}) != len(self.datos):
            raise ValueError("Contexto contradictorio/repetido")
        referencias = {}
        for d in self.datos:
            anterior = referencias.get(d.evidencia.identificador)
            if anterior is not None and anterior != d.evidencia:
                raise ValueError("Referencia de contexto contradictoria")
            referencias[d.evidencia.identificador] = d.evidencia


@dataclass(frozen=True)
class HabilitacionCientifica:
    regla: RevisionReglaCientifica
    elegible_documentalmente: bool
    motivos: tuple[str, ...]
    ejecucion_autorizada: bool = field(default=False, init=False)
    estado_evaluacion: EstadoEvaluacionQA = field(default=EstadoEvaluacionQA.NO_EVALUADA, init=False)


@dataclass(frozen=True)
class EvidenciaEjecucionCientifica:
    """Descripción de una ejecución futura/externa; no prueba que SPICA la ejecutó."""
    metodo: MetodoCientifico
    fecha_utc: datetime
    ejecutor_version: str
    referencias: tuple[ReferenciaCientifica, ...]
    detalle: str
    contexto: ContextoCientifico = field(default_factory=ContextoCientifico)

    def __post_init__(self):
        if not isinstance(self.metodo, MetodoCientifico):
            raise TypeError("Método tipado requerido")
        _utc(self.fecha_utc)
        _version(self.ejecutor_version)
        _tupla(self.referencias, ReferenciaCientifica)
        if not self.referencias or len({r.identificador for r in self.referencias}) != len(self.referencias):
            raise ValueError("Evidencia de ejecución identificada y no repetida requerida")
        _texto(self.detalle)
        if not isinstance(self.contexto, ContextoCientifico):
            raise TypeError("Contexto de ejecución tipado requerido")


@dataclass(frozen=True)
class ResultadoCientifico:
    """Contrato de resultados; este paso no incorpora ningún productor Nivel 1."""
    regla: RevisionReglaCientifica
    registro: RegistroQA
    procedencia: ProcedenciaQA
    unidad_declarada: str | None
    estado: EstadoResultadoCientifico
    diagnostico: str
    evidencia: EvidenciaEjecucionCientifica | None = None
    version_contrato: str = field(default=VERSION_CONTRATO_CIENTIFICO, init=False)

    def __post_init__(self):
        if (not isinstance(self.regla, RevisionReglaCientifica) or not isinstance(self.registro, RegistroQA)
                or not isinstance(self.procedencia, ProcedenciaQA) or not isinstance(self.estado, EstadoResultadoCientifico)):
            raise TypeError("Resultado científico tipado requerido")
        _texto(self.unidad_declarada, opcional=True, maximo=128)
        _texto(self.diagnostico)
        if self.evidencia is not None and not isinstance(self.evidencia, EvidenciaEjecucionCientifica):
            raise TypeError("Evidencia de ejecución tipada requerida")
        if self.evidencia is not None and self.evidencia.metodo != self.regla.regla.metodo:
            raise ValueError("Evidencia de otro método/versión")
        if self.estado is not EstadoResultadoCientifico.NO_EVALUADO:
            if self.regla.estado is not EstadoReglaCientifica.APROBADA or self.evidencia is None:
                raise ValueError("Resultado ejecutado requiere aprobación y evidencia explícitas")
            if self.evidencia.fecha_utc < self.regla.decision.fecha_utc:
                raise ValueError("La ejecución declarada precede a la aprobación")

    @property
    def estado_evaluacion(self):
        if self.estado is EstadoResultadoCientifico.NO_EVALUADO:
            return EstadoEvaluacionQA.NO_EVALUADA
        if self.estado is EstadoResultadoCientifico.EVALUACION_INCOMPLETA:
            return EstadoEvaluacionQA.INCOMPLETA
        return EstadoEvaluacionQA.COMPLETA
