"""Condiciones de una operación propuesta, adicionales al evaluador conservador."""

from dataclasses import dataclass, field

from ..adquisicion.catalogo.modelos import EstadoVerificacion as V
from .evaluador import evaluar_aptitud
from .modelos import DimensionEvaluacion as D, EstadoAptitud as E, RecursoInteroperable, ResultadoAptitud, _texto


@dataclass(frozen=True)
class OperacionPropuesta:
    identificador: str
    dimension: D
    requiere_precision_posicional: bool  # Sin valor por defecto: decisión explícita.

    def __post_init__(self):
        _texto(self.identificador)
        if type(self.dimension) is not D or type(self.requiere_precision_posicional) is not bool:
            raise TypeError("operacion_declarativa_tipificada_requerida")
        if self.dimension is D.TEMPORAL and self.requiere_precision_posicional:
            raise ValueError("precision_espacial_requiere_dimension_espacial")


@dataclass(frozen=True)
class ResultadoOperacion:
    operacion: OperacionPropuesta
    aptitud: ResultadoAptitud
    faltantes_operacion: tuple[str, ...]
    condiciones_documentales_satisfechas: bool
    operacion_ejecutada: bool = field(default=False, init=False)
    verificacion_espacial_efectiva: bool = field(default=False, init=False)
    confiabilidad_cientifica: str = field(default="no_evaluada", init=False)
    version: str = field(default="0.1.0", init=False)

    def __post_init__(self):
        if type(self.operacion) is not OperacionPropuesta or type(self.aptitud) is not ResultadoAptitud:
            raise TypeError("operacion_y_resultado_tipificados_requeridos")
        if self.operacion.dimension is not self.aptitud.dimension or type(self.faltantes_operacion) is not tuple:
            raise ValueError("dimension_o_faltantes_incoherentes")
        for texto in self.faltantes_operacion:
            _texto(texto)
        esperado = self.aptitud.estado is E.APTO_ESTRUCTURALMENTE and not self.faltantes_operacion
        if type(self.condiciones_documentales_satisfechas) is not bool or self.condiciones_documentales_satisfechas != esperado:
            raise ValueError("condiciones_contradictorias")


def evaluar_operacion(primero: RecursoInteroperable, segundo: RecursoInteroperable,
                      operacion: OperacionPropuesta) -> ResultadoOperacion:
    if type(operacion) is not OperacionPropuesta:
        raise TypeError("operacion_tipificada_requerida")
    resultado = evaluar_aptitud(primero, segundo, operacion.dimension)
    faltantes = []
    if operacion.requiere_precision_posicional:
        for i, r in enumerate(resultado.recursos):
            m = r.espacial
            if m is None or m.precision_declarada is None:
                faltantes.append(f"r{i}.operacion.precision_documentada")
            if m is None or m.incertidumbre is None:
                faltantes.append(f"r{i}.operacion.incertidumbre_documentada")
            if m is None or m.respaldo_calidad.estado is not V.VERIFICADO:
                faltantes.append(f"r{i}.operacion.respaldo_calidad")
    # No suprimir faltantes del núcleo cuando la operación no exige precisión.
    satisfechas = resultado.estado is E.APTO_ESTRUCTURALMENTE and not faltantes
    return ResultadoOperacion(operacion, resultado, tuple(faltantes), satisfechas)
