"""Perfil descriptivo local; ningún modelo certifica validez científica."""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from ..adquisicion.catalogo import EvidenciaDocumental
from ..adquisicion.consultas_locales import ProcedenciaLocal
from ..adquisicion.verificacion import InformeLecturaCSV, PoliticaLecturaCSV


@dataclass(frozen=True)
class LimitesPerfil:
    lectura: PoliticaLecturaCSV = field(default_factory=PoliticaLecturaCSV)
    max_estaciones: int = 64
    max_variantes_campo: int = 16
    max_relaciones_estacion: int = 32
    max_horas_estacion: int = 128
    max_claves_hora: int = 500_000
    max_dias: int = 20_000
    max_claves_periodo: int = 20_000
    max_valores_distintos: int = 50_000
    max_bytes_indice: int = 64 * 1024**2
    max_caracteres_literal: int = 512
    max_caracteres_numero: int = 128
    max_digitos_numero: int = 64
    max_exponente: int = 1000
    max_ejemplos: int = 20
    max_repetidos: int = 10
    marcadores: tuple[str, ...] = ("NA", "N/A", "NULL", "null", "NaN", "nan", "S/D", "s/d",
                                   "-999", "-999.0", "-9999", "-9999.0", "-99.9", "9999")

    def __post_init__(self):
        topes = dict(max_estaciones=128, max_variantes_campo=64, max_relaciones_estacion=128,
            max_horas_estacion=256, max_claves_hora=2_000_000, max_dias=100_000,
            max_claves_periodo=100_000, max_valores_distintos=100_000,
            max_bytes_indice=256 * 1024**2, max_caracteres_literal=512,
            max_caracteres_numero=256, max_digitos_numero=128, max_exponente=10_000,
            max_ejemplos=100, max_repetidos=32)
        for nombre, tope in topes.items():
            valor = getattr(self, nombre)
            if type(valor) is not int or not 0 < valor <= tope:
                raise ValueError("Presupuesto de perfilado no admitido")
        if self.max_bytes_indice < 16_384 or not isinstance(self.lectura, PoliticaLecturaCSV):
            raise ValueError("Lectura o presupuesto SQLite no admitidos")
        if not isinstance(self.marcadores, (tuple, list)) or len(self.marcadores) > 32:
            raise ValueError("Marcadores deben ser una selección acotada")
        if any(not isinstance(t, str) or not t or len(t) > 128 for t in self.marcadores):
            raise ValueError("Marcadores literales no vacíos y acotados")
        if len(set(self.marcadores)) != len(self.marcadores):
            raise ValueError("Marcadores repetidos")
        object.__setattr__(self, "marcadores", tuple(self.marcadores))


@dataclass(frozen=True)
class HuellaPerfil:
    size_bytes: int
    sha256: str


@dataclass(frozen=True)
class ExtremoObservado:
    decimal: Decimal
    texto_original: str
    registro: int
    fecha_literal: str
    hora_literal: str


@dataclass(frozen=True)
class PerfilVariable:
    variable: str
    total: int
    vacios: int
    no_vacios: int
    numericos_finitos: int
    no_interpretables: int
    no_finitos: int
    fuera_presupuesto_numerico: int
    con_signo: int
    con_punto_decimal: int
    notaciones: tuple[tuple[str, int], ...]
    marcadores: tuple[tuple[str, int], ...]
    minimo: ExtremoObservado | None
    maximo: ExtremoObservado | None
    extremos_comparables_completos: bool
    valores_distintos_no_vacios: int | None
    repetidos: tuple[tuple[str, int], ...]
    ejemplos_especiales: tuple[tuple[str, str, int], ...]


@dataclass(frozen=True)
class PerfilHora:
    longitudes: tuple[tuple[int, int], ...]
    patrones: tuple[tuple[str, int], ...]
    literales: tuple[tuple[str, int], ...]
    # Literal, FECHA civil mínima y máxima observadas. No representa instantes.
    cobertura_literales: tuple[tuple[str, date, date], ...]
    # Fragmentos de caracteres, sin construir horas normalizadas.
    fragmentos_seis: tuple[tuple[str, str, str, int], ...]
    fragmentos_cinco: tuple[tuple[str, str, str, int], ...]


@dataclass(frozen=True)
class PerfilEstacion:
    nombre_literal: str
    registros: int
    variables: tuple[PerfilVariable, ...]
    horas: PerfilHora
    campos_ubicacion: tuple[tuple[str, tuple[tuple[str, int], ...]], ...]
    # RED, LONGITUD, LATITUD, ALTITUD, DEPARTAMENTO, PROVINCIA, DISTRITO, UBIGEO.
    relaciones_ubicacion: tuple[tuple[tuple[str, ...], int], ...]
    cambios_ubicacion_en_orden_archivo: int
    ejemplos_cambios: tuple[tuple[int, str, tuple[str, ...], tuple[str, ...]], ...]
    fechas_invalidas: int
    retrocesos_fecha_en_orden_archivo: int


@dataclass(frozen=True)
class PerfilDia:
    estacion: str
    fecha_civil: date
    registros: int
    horas_literales_distintas: int
    repeticiones_hora_literal: int


@dataclass(frozen=True)
class PerfilPeriodo:
    estacion: str
    mes_civil: str
    horas_literales: tuple[tuple[str, int], ...]
    patrones_hora: tuple[tuple[str, int], ...]


@dataclass(frozen=True)
class PerfilTemporal:
    estacion: str
    fecha_minima: date | None
    fecha_maxima: date | None
    dias_observados: int
    distribucion_registros_por_dia: tuple[tuple[int, int], ...]
    dias_con_varias_horas_literales: int
    repeticiones_hora_literal: int
    intervalos_entre_fechas_no_consecutivas: int
    # Fechas observadas vecinas, cantidad de fechas civiles intermedias no observadas.
    ejemplos_saltos: tuple[tuple[date, date, int], ...]
    cobertura_interpretable: bool


@dataclass(frozen=True)
class HallazgoPerfil:
    tipo: str  # alerta_tecnica / incertidumbre; no son dictámenes científicos.
    codigo: str
    estacion: str | None = None
    variable: str | None = None
    cantidad: int | None = None


@dataclass(frozen=True)
class InformePerfil:
    procedencia: ProcedenciaLocal
    documento: EvidenciaDocumental | None
    completo: bool
    motivo_fin: str
    filas_procesadas: int
    huella_antes: HuellaPerfil | None
    huella_despues: HuellaPerfil | None
    huellas_coinciden: bool
    estaciones: tuple[PerfilEstacion, ...]
    dias: tuple[PerfilDia, ...]
    periodos: tuple[PerfilPeriodo, ...]
    temporal: tuple[PerfilTemporal, ...]
    agregados_indexados_disponibles: bool
    temporal_eliminado: bool
    hallazgos: tuple[HallazgoPerfil, ...]
    reglas_cientificas_aplicadas: tuple[str, ...]
    lectura: InformeLecturaCSV
    limites: LimitesPerfil
