"""Contratos de selección local. Las fechas son civiles, nunca instantes UTC."""

from dataclasses import dataclass, field
from datetime import date
import re

from ..nucleo import Fuente
from ..verificacion import InformeLecturaCSV, PoliticaLecturaCSV


ENCABEZADO_SENAMHI = (
    "ID", "ESTACION", "FECHA", "HORA", "LONGITUD", "LATITUD", "ALTITUD",
    "TEMP", "HR", "PP", "RED", "DEPARTAMENTO", "PROVINCIA", "DISTRITO",
    "UBIGEO", "FECHA_CORTE",
)
VARIABLES_SENAMHI = ("TEMP", "HR", "PP")


@dataclass(frozen=True)
class ProcedenciaLocal:
    fuente: Fuente
    recurso_id: str
    asset_id: str
    sha256_declarado: str | None = None  # No implica comprobación física.

    def __post_init__(self):
        if not isinstance(self.fuente, Fuente):
            raise TypeError("Se requiere Fuente")
        for texto in (self.recurso_id, self.asset_id):
            if not isinstance(texto, str) or not texto.strip() or len(texto) > 4096:
                raise ValueError("Procedencia requerida y acotada")
        if self.sha256_declarado is not None and not re.fullmatch(r"[0-9a-f]{64}", self.sha256_declarado):
            raise ValueError("SHA-256 declarado no admitido")


@dataclass(frozen=True)
class ConsultaLocal:
    estaciones: tuple[str, ...]
    variables: tuple[str, ...]
    fecha_inicial: date
    fecha_final: date

    def __post_init__(self):
        # datetime es subclase de date, pero aquí no se admite una hora o zona.
        if type(self.fecha_inicial) is not date or type(self.fecha_final) is not date:
            raise TypeError("Se requieren fechas civiles date, sin hora ni zona")
        if self.fecha_inicial > self.fecha_final:
            raise ValueError("Intervalo civil invertido")
        for nombre, maximo in (("estaciones", 128), ("variables", 3)):
            valores = getattr(self, nombre)
            if not isinstance(valores, (tuple, list)) or not 0 < len(valores) <= maximo:
                raise ValueError("Selección vacía o superior al límite")
            if any(not isinstance(v, str) or not v.strip() or len(v) > 256 for v in valores):
                raise ValueError("Nombres literales requeridos y acotados")
            if len(set(valores)) != len(valores):
                raise ValueError("Filtros repetidos")
            object.__setattr__(self, nombre, tuple(valores))
        if any(v not in VARIABLES_SENAMHI for v in self.variables):
            raise ValueError("Variable no admitida por este perfil documental")


@dataclass(frozen=True)
class LimitesConsulta:
    max_resultados: int = 10_000  # Una fila × una variable = un resultado.
    lectura: PoliticaLecturaCSV = field(default_factory=PoliticaLecturaCSV)

    def __post_init__(self):
        if type(self.max_resultados) is not int or not 0 < self.max_resultados <= 2_000_000:
            raise ValueError("Límite de resultados no admitido")
        if not isinstance(self.lectura, PoliticaLecturaCSV):
            raise TypeError("Se requiere PoliticaLecturaCSV")


@dataclass(frozen=True)
class ObservacionLocal:
    procedencia: ProcedenciaLocal
    numero_registro: int
    linea_inicial: int
    linea_final: int
    campos_originales: tuple[tuple[str, str], ...]
    variable: str
    valor: str
    presente: bool  # Solamente valor != ""; no implica validez científica.
    fecha_civil: date


@dataclass(frozen=True)
class InformeConsulta:
    completa: bool
    motivo_fin: str
    resultados: int
    filas_coincidentes: int
    fechas_invalidas: int
    lectura: InformeLecturaCSV

    @property
    def ausencia_comprobada(self) -> bool:
        """Ausencia de coincidencias locales, no de observaciones en la institución."""
        return self.completa and self.resultados == 0
