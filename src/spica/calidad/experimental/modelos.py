"""Contratos exclusivos de ensayos sintéticos, ajenos a aprobación científica."""

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
import re

from ..modelos import EstadoEvaluacionQA
from ...perfilado import LimitesPerfil
from ...perfilado.interpretacion import VERSION_INTERPRETACION, interpretar_numero

VERSION_EXPERIMENTAL = "1.0.0"


def _texto(valor, *, opcional=False, maximo=256):
    if valor is None and opcional:
        return
    if type(valor) is not str or not valor.strip() or len(valor) > maximo:
        raise ValueError("Texto literal requerido y acotado")


def _identificador(valor, prefijo):
    if type(valor) is not str or not re.fullmatch(prefijo + r"[A-Z0-9][A-Z0-9._-]{0,79}", valor):
        raise ValueError("Identificador del ámbito sintético requerido")


class TipoEvidenciaExperimental(Enum):
    FIXTURE_SINTETICA = "fixture_sintetica_sin_aprobacion_cientifica"


class EstadoLimiteExperimental(Enum):
    CONDICION_SATISFECHA = "condicion_experimental_satisfecha"
    CONDICION_NO_SATISFECHA = "condicion_experimental_no_satisfecha"
    NO_EVALUADO_EVIDENCIA = "no_evaluado_falta_evidencia"
    NO_EVALUADO_VARIABLE = "no_evaluado_variable_incompatible"
    NO_EVALUADO_UNIDAD = "no_evaluado_unidad_desconocida_o_incompatible"
    NO_EVALUADO_MODALIDAD = "no_evaluado_modalidad_desconocida_o_incompatible"
    NO_EVALUADO_FRECUENCIA = "no_evaluado_frecuencia_desconocida_o_incompatible"
    EVALUACION_INCOMPLETA = "evaluacion_incompleta"
    ERROR_TECNICO = "error_tecnico"


@dataclass(frozen=True)
class EvidenciaSintetica:
    fixture_id: str
    version: str
    descripcion: str
    tipo: TipoEvidenciaExperimental = field(default=TipoEvidenciaExperimental.FIXTURE_SINTETICA, init=False)

    def __post_init__(self):
        _identificador(self.fixture_id, "FIXTURE-")
        _texto(self.version, maximo=64)
        _texto(self.descripcion, maximo=4096)


@dataclass(frozen=True)
class ObservacionSintetica:
    observacion_id: str
    variable: str
    valor_original: str
    unidad: str | None
    modalidad: str | None
    frecuencia: str | None
    evidencia: EvidenciaSintetica
    datos_sinteticos: bool = field(default=True, init=False)

    def __post_init__(self):
        _texto(self.observacion_id)
        _texto(self.variable)
        if type(self.valor_original) is not str or len(self.valor_original) > 65_536:
            raise ValueError("Valor original textual y acotado requerido")
        for valor in (self.unidad, self.modalidad, self.frecuencia):
            _texto(valor, opcional=True)
        if type(self.evidencia) is not EvidenciaSintetica:
            raise TypeError("Declaración de fixture sintética requerida")


@dataclass(frozen=True)
class ReglaLimitesSintetica:
    identificador: str
    version: str
    variable: str
    unidad: str | None
    modalidad: str | None
    frecuencia: str | None
    limite_inferior: Decimal
    limite_superior: Decimal
    incluir_inferior: bool
    incluir_superior: bool
    evidencia_parametros: EvidenciaSintetica | None
    politica_numerica: LimitesPerfil = field(default_factory=LimitesPerfil)

    def __post_init__(self):
        _identificador(self.identificador, "EXP-LIM-")
        _texto(self.version, maximo=64)
        _texto(self.variable)
        for valor in (self.unidad, self.modalidad, self.frecuencia):
            _texto(valor, opcional=True)
        if type(self.incluir_inferior) is not bool or type(self.incluir_superior) is not bool:
            raise TypeError("Inclusividad explícita requerida")
        if self.evidencia_parametros is not None and type(self.evidencia_parametros) is not EvidenciaSintetica:
            raise TypeError("Los parámetros requieren evidencia sintética, no referencias científicas")
        if type(self.politica_numerica) is not LimitesPerfil:
            raise TypeError("Política numérica compartida requerida")
        for limite in (self.limite_inferior, self.limite_superior):
            if type(limite) is not Decimal or not limite.is_finite():
                raise ValueError("Límites Decimal finitos requeridos")
            # No construir una representación enorme antes de comprobar su presupuesto.
            _, digitos, exponente = limite.as_tuple()
            if len(digitos) > self.politica_numerica.max_digitos_numero or abs(exponente) > self.politica_numerica.max_exponente:
                raise ValueError("Límite fuera del presupuesto numérico")
            if interpretar_numero(str(limite), limites=self.politica_numerica).clase != "finito":
                raise ValueError("Representación del límite fuera del presupuesto numérico")
        if self.limite_inferior > self.limite_superior:
            raise ValueError("Límites invertidos")
        if self.limite_inferior == self.limite_superior and not (self.incluir_inferior and self.incluir_superior):
            raise ValueError("Intervalo vacío")


@dataclass(frozen=True)
class ResultadoLimiteSintetico:
    observacion: ObservacionSintetica
    regla: ReglaLimitesSintetica
    estado: EstadoLimiteExperimental
    motivo: str
    valor_numerico: Decimal | None = None
    datos_sinteticos: bool = field(default=True, init=False)
    ejecucion_operativa_autorizada: bool = field(default=False, init=False)
    version_evaluador: str = field(default=VERSION_EXPERIMENTAL, init=False)
    version_interpretacion: str = field(default=VERSION_INTERPRETACION, init=False)

    def __post_init__(self):
        if (type(self.observacion) is not ObservacionSintetica or type(self.regla) is not ReglaLimitesSintetica
                or type(self.estado) is not EstadoLimiteExperimental):
            raise TypeError("Resultado de ensayo tipado requerido")
        _texto(self.motivo)
        if self.valor_numerico is not None and (type(self.valor_numerico) is not Decimal or not self.valor_numerico.is_finite()):
            raise ValueError("Solo se conserva un Decimal finito interpretado")
        if self.estado in (EstadoLimiteExperimental.CONDICION_SATISFECHA,
                            EstadoLimiteExperimental.CONDICION_NO_SATISFECHA) and self.valor_numerico is None:
            raise ValueError("Una comparación requiere número interpretado")

    @property
    def estado_evaluacion(self):
        if self.estado in (EstadoLimiteExperimental.CONDICION_SATISFECHA,
                            EstadoLimiteExperimental.CONDICION_NO_SATISFECHA):
            return EstadoEvaluacionQA.COMPLETA
        if self.estado in (EstadoLimiteExperimental.EVALUACION_INCOMPLETA, EstadoLimiteExperimental.ERROR_TECNICO):
            return EstadoEvaluacionQA.INCOMPLETA
        return EstadoEvaluacionQA.NO_EVALUADA
