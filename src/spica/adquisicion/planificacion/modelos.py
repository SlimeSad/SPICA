"""Solicitudes y planes declarativos: ninguna estructura ejecuta adquisiciones."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from ..nucleo import SolicitudAdquisicion
from ..catalogo import EstadoVerificacion, RegistroCatalogo, CapacidadCatalogo, ProductoCatalogo


class EstadoPreparacion(Enum):
    PREPARADA = "preparada_segun_catalogo"
    CONDICIONADA = "condicionada"


class SituacionTemporal(Enum):
    CATALOGADA = "catalogada"
    PARCIAL = "cobertura_parcial"
    DESCONOCIDA = "desconocida"
    FUERA_COBERTURA_CONOCIDA = "fuera_cobertura_conocida"
    AUSENCIA_DOCUMENTADA = "ausencia_documentada"  # Reservado: catálogo sin evidencia negativa.


@dataclass(frozen=True)
class ConsultaProducto:
    solicitud: SolicitudAdquisicion
    producto_id: str | None = None  # None explora los productos de esta fuente.
    frecuencia: str | None = None

    def __post_init__(self):
        if not isinstance(self.solicitud, SolicitudAdquisicion):
            raise TypeError("Se requiere SolicitudAdquisicion")
        for valor in (self.producto_id, self.frecuencia):
            if valor is not None and (not isinstance(valor, str) or not valor.strip()):
                raise ValueError("Producto/frecuencia deben ser textos no vacios")


@dataclass(frozen=True)
class SolicitudCientifica:
    identificador: str
    consultas: tuple[ConsultaProducto, ...]

    def __post_init__(self):
        if not isinstance(self.identificador, str) or not self.identificador.strip():
            raise ValueError("Identificador requerido")
        if isinstance(self.consultas, str):
            raise TypeError("Se requiere una coleccion de consultas")
        object.__setattr__(self, "consultas", tuple(self.consultas))
        if not self.consultas or any(not isinstance(c, ConsultaProducto) for c in self.consultas):
            raise ValueError("Se requieren consultas tipadas")


@dataclass(frozen=True)
class LimitesPlanificacion:
    max_operaciones: int = 1000
    max_registros_catalogo: int = 10000
    max_bytes_catalogo: int = 8 * 1024 * 1024
    max_consultas: int = 128
    max_elementos_solicitud: int = 10000
    max_bytes_solicitud: int = 2 * 1024 * 1024

    def __post_init__(self):
        for valor in vars(self).values():
            if type(valor) is not int or valor <= 0:
                raise ValueError("Los limites deben ser enteros positivos")


@dataclass(frozen=True)
class TramoTemporal:
    inicio: datetime
    fin: datetime
    incluye_inicio: bool = True
    incluye_fin: bool = True


@dataclass(frozen=True)
class EvaluacionIntervalo:
    evidencia: RegistroCatalogo
    estado_evidencia: EstadoVerificacion
    situacion: SituacionTemporal
    intervalo_aplicable: TramoTemporal | None
    alcance_exacto: bool
    frecuencia_compatible: bool | None


@dataclass(frozen=True)
class EvaluacionProducto:
    consulta_indice: int
    consulta: ConsultaProducto
    producto: RegistroCatalogo
    intervalos: tuple[EvaluacionIntervalo, ...]
    # Vacíos por asociación registrada, nunca uniones entre estaciones/variables.
    tramos_desconocidos: tuple[tuple[str | None, str | None, TramoTemporal], ...]
    capacidades: tuple[RegistroCatalogo, ...]
    advertencias: tuple[str, ...]
    estaciones_sin_evidencia_aplicable: tuple[str, ...]
    variables_sin_evidencia_aplicable: tuple[str, ...]


@dataclass(frozen=True)
class OperacionPlanificada:
    identificador: str
    consulta_indice: int
    consulta: ConsultaProducto
    producto: ProductoCatalogo
    estaciones: tuple[str, ...]
    variables: tuple[str, ...]  # Códigos originales, no IDs internos del catálogo.
    intervalo: TramoTemporal
    capacidad: CapacidadCatalogo | None
    estado: EstadoPreparacion
    pendientes: tuple[str, ...]
    evidencias: tuple[RegistroCatalogo, ...]


@dataclass(frozen=True)
class PlanConsulta:
    solicitud: SolicitudCientifica
    evaluaciones: tuple[EvaluacionProducto, ...]
    operaciones: tuple[OperacionPlanificada, ...]
    advertencias: tuple[str, ...]

    @property
    def operaciones_propuestas(self):
        return len(self.operaciones)

    @property
    def estimacion_operaciones_ejecucion(self) -> int | None:
        # Sin conectores no conocemos fragmentación, paginación ni lotes reales.
        return None

    @property
    def ejecutable(self):
        return False  # Preparación catalogada no equivale a un ejecutor disponible.


class ErrorPlanificacion(Exception):
    pass


class LimitePlanificacion(ErrorPlanificacion):
    pass
