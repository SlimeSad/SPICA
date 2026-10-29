"""Resultados técnicos de formato; separados de integridad y calidad científica."""

from dataclasses import dataclass, fields
from datetime import datetime
from enum import Enum
import math


class EstadoEstructura(Enum):
    COMPATIBLE = "reconocida_compatible"
    INCOMPATIBLE = "reconocida_incompatible"
    SIN_DECLARACION = "reconocida_sin_declaracion"
    NO_RECONOCIDA = "no_reconocida"
    INCIERTA = "incierta"
    INCOMPLETA = "incompleta_por_limites"
    ILEGIBLE_O_CORRUPTA = "ilegible_o_corrupta"


@dataclass(frozen=True)
class PoliticaEstructura:
    max_entradas_zip: int = 512
    max_central_zip: int = 2_097_152
    max_bytes_descomprimidos: int = 67_108_864
    max_bytes_entrada: int = 16_777_216
    max_expansion: float = 100.0
    max_bytes_xml: int = 524_288
    max_xml_pendiente: int = 65_536
    max_nodos_xml: int = 20_000
    max_profundidad_xml: int = 64
    max_muestra_csv: int = 262_144
    max_registros_csv: int = 1000
    max_campos_csv: int = 1024
    max_campo_csv: int = 65_536
    tamano_bloque: int = 65_536

    def __post_init__(self):
        for campo in fields(self):
            valor = getattr(self, campo.name)
            if campo.name == "max_expansion":
                if type(valor) not in (int, float) or not math.isfinite(valor) or valor <= 0:
                    raise ValueError("max_expansion debe ser positivo y finito")
            elif type(valor) is not int or valor <= 0:
                raise ValueError("Los límites estructurales deben ser enteros positivos")
        if (self.max_central_zip > 16_777_216 or self.max_bytes_xml > 4_194_304
                or self.max_muestra_csv > 8_388_608 or self.tamano_bloque > 1_048_576
                or self.max_xml_pendiente > 1_048_576):
            raise ValueError("Política superior a los topes de memoria admitidos")


@dataclass(frozen=True)
class DetalleCSV:
    codificacion: str | None = None
    bom: str | None = None
    delimitador: str | None = None
    encabezado_declarado: bool | None = None
    campos_primera_fila: int | None = None
    registros_examinados: int | None = None


@dataclass(frozen=True)
class ResultadoEstructura:
    estado: EstadoEstructura
    formato_declarado: str | None
    sugerido_extension: str | None
    sugerido_http: str | None
    formato_identificado: str | None
    tipo_medio_identificado: str | None
    fecha_utc: datetime
    tamano_archivo: int | None
    bytes_leidos: int
    bytes_descomprimidos: int
    alcance_completo: bool
    comprobaciones: tuple[str, ...]
    diagnosticos: tuple[str, ...]
    politica: PoliticaEstructura
    csv: DetalleCSV | None = None

    @property
    def utilizable_documentalmente(self) -> bool:
        return (self.estado is EstadoEstructura.COMPATIBLE and self.alcance_completo
                and self.formato_identificado in ("xlsx", "csv"))


class _Hallazgo(Exception):
    def __init__(self, estado, codigo):
        super().__init__(codigo)
        self.estado, self.codigo = estado, codigo


def _limite(codigo):
    raise _Hallazgo(EstadoEstructura.INCOMPLETA, codigo)


def _corrupto(codigo):
    raise _Hallazgo(EstadoEstructura.ILEGIBLE_O_CORRUPTA, codigo)
