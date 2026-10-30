"""Contratos QA/QC Nivel 0. Los estados no certifican validez científica."""

from dataclasses import dataclass, field
from enum import Enum
import re

from ..adquisicion.catalogo import EvidenciaDocumental
from ..adquisicion.consultas_locales import ProcedenciaLocal, VARIABLES_SENAMHI
from ..adquisicion.nucleo import Fuente
from ..perfilado import LimitesPerfil

VERSION_CONTRATO_QA = "1.0.0"


class CategoriaQA(Enum):
    ESTRUCTURA = "estructura"
    VALORES = "valores"
    TEMPORALES = "temporales"
    IDENTIDAD_UBICACION = "identidad_ubicacion"
    PROCEDENCIA = "procedencia"


class EstadoResultadoQA(Enum):
    COMPROBACION_SATISFECHA = "comprobacion_satisfecha"
    ALERTA_DOCUMENTAL = "alerta_documental"
    PROBLEMA_TECNICO = "problema_tecnico"
    NO_EVALUADO = "no_evaluado"
    EVALUACION_INCOMPLETA = "evaluacion_incompleta"


class EstadoEvaluacionQA(Enum):
    COMPLETA = "completa"
    INCOMPLETA = "incompleta"
    NO_EVALUADA = "no_evaluada"


class FormatoQA(Enum):
    NUMERO_ASCII = "numero_ascii_finito"
    AAAAMMDD = "aaaammdd"
    HHMMSS = "hhmmss"
    SEIS_CARACTERES = "texto_seis_caracteres"


def _texto(valor, *, opcional=False, maximo=4096):
    if valor is None and opcional:
        return
    if not isinstance(valor, str) or not valor.strip() or len(valor) > maximo:
        raise ValueError("Texto requerido y acotado")


@dataclass(frozen=True)
class ReferenciaDocumentalQA:
    referencia: str
    descripcion: str
    sha256_referencia: str | None = None
    revision: int | None = None

    def __post_init__(self):
        _texto(self.referencia)
        _texto(self.descripcion)
        if self.sha256_referencia is not None and not re.fullmatch(r"[0-9a-f]{64}", self.sha256_referencia):
            raise ValueError("SHA documental no admitido")
        if self.revision is not None and (type(self.revision) is not int or self.revision <= 0):
            raise ValueError("Revisión positiva o desconocida")


@dataclass(frozen=True)
class FormatoDocumentadoQA:
    campo: str
    formato: FormatoQA
    evidencia: ReferenciaDocumentalQA

    def __post_init__(self):
        _texto(self.campo, maximo=128)
        if not isinstance(self.formato, FormatoQA) or not isinstance(self.evidencia, ReferenciaDocumentalQA):
            raise TypeError("Formato y evidencia tipados requeridos")


@dataclass(frozen=True)
class DatoDocumentadoQA:
    valor: str
    evidencia: ReferenciaDocumentalQA

    def __post_init__(self):
        _texto(self.valor, maximo=256)
        if not isinstance(self.evidencia, ReferenciaDocumentalQA):
            raise TypeError("Evidencia requerida")


@dataclass(frozen=True)
class IdentidadEstacionQA:
    nombre_literal: str
    identificador_original: str
    evidencia: ReferenciaDocumentalQA

    def __post_init__(self):
        _texto(self.nombre_literal, maximo=256)
        _texto(self.identificador_original, maximo=256)
        if not isinstance(self.evidencia, ReferenciaDocumentalQA):
            raise TypeError("Evidencia requerida")


@dataclass(frozen=True)
class ProcedenciaQA:
    fuente: Fuente | None = None
    recurso_id: str | None = None
    adquisicion_id: str | None = None
    asset_id: str | None = None
    sha256_referencia: str | None = None
    documento: EvidenciaDocumental | None = None

    def __post_init__(self):
        if self.fuente is not None and not isinstance(self.fuente, Fuente):
            raise TypeError("Fuente no admitida")
        for texto in (self.recurso_id, self.adquisicion_id, self.asset_id):
            _texto(texto, opcional=True)
        if self.sha256_referencia is not None and not re.fullmatch(r"[0-9a-f]{64}", self.sha256_referencia):
            raise ValueError("SHA de referencia no admitido")
        if self.documento is not None and not isinstance(self.documento, EvidenciaDocumental):
            raise TypeError("Documento no admitido")

    @classmethod
    def desde_local(cls, procedencia: ProcedenciaLocal, *, adquisicion_id=None, documento=None):
        if not isinstance(procedencia, ProcedenciaLocal):
            raise TypeError("Se requiere ProcedenciaLocal")
        return cls(procedencia.fuente, procedencia.recurso_id, adquisicion_id, procedencia.asset_id,
                   procedencia.sha256_declarado, documento)


@dataclass(frozen=True)
class ConfiguracionQA:
    categorias: tuple[CategoriaQA, ...] = tuple(CategoriaQA)
    reglas: tuple[str, ...] = ()  # Vacío selecciona todas las de las categorías indicadas.
    variables: tuple[str, ...] = VARIABLES_SENAMHI
    formatos: tuple[FormatoDocumentadoQA, ...] = ()
    zona_documentada: DatoDocumentadoQA | None = None
    identidades: tuple[IdentidadEstacionQA, ...] = ()
    politica_numerica: LimitesPerfil = field(default_factory=LimitesPerfil)

    def __post_init__(self):
        for nombre, tipo, maximo in (("categorias", CategoriaQA, 5), ("reglas", str, 32),
                ("variables", str, 3), ("formatos", FormatoDocumentadoQA, 32),
                ("identidades", IdentidadEstacionQA, 128)):
            valores = getattr(self, nombre)
            if not isinstance(valores, (tuple, list)) or len(valores) > maximo or any(not isinstance(v, tipo) for v in valores):
                raise ValueError("Configuración tipada y acotada requerida")
            object.__setattr__(self, nombre, tuple(valores))
        if not self.categorias or not self.variables or any(v not in VARIABLES_SENAMHI for v in self.variables):
            raise ValueError("Selección de categorías/variables no admitida")
        for valores in (self.categorias, self.variables, self.reglas):
            if len(set(valores)) != len(valores):
                raise ValueError("Selección repetida")
        if len({f.campo for f in self.formatos}) != len(self.formatos):
            raise ValueError("Formatos contradictorios para un campo")
        if self.zona_documentada is not None and not isinstance(self.zona_documentada, DatoDocumentadoQA):
            raise TypeError("Zona requiere evidencia documental")
        if not isinstance(self.politica_numerica, LimitesPerfil):
            raise TypeError("Se requiere política numérica existente")


@dataclass(frozen=True)
class LimitesQA:
    max_registros: int = 10_000
    max_resultados: int = 100_000
    max_caracteres_celda: int = 65_536
    max_caracteres_registro: int = 1_048_576

    def __post_init__(self):
        for nombre, tope in (("max_registros", 2_000_000), ("max_resultados", 5_000_000),
                            ("max_caracteres_celda", 65_536), ("max_caracteres_registro", 1_048_576)):
            valor = getattr(self, nombre)
            if type(valor) is not int or not 0 < valor <= tope:
                raise ValueError("Límite QA no admitido")


@dataclass(frozen=True)
class ReglaQA:
    identificador: str
    version: str
    categoria: CategoriaQA
    descripcion: str


@dataclass(frozen=True)
class RegistroQA:
    numero_registro: int
    id_original: str | None
    estacion_literal: str | None
    linea_inicial: int
    linea_final: int
    campos_originales: tuple[tuple[str, str], ...]
    estructura_correcta: bool
    procedencia_original: ProcedenciaLocal | None = None
    valores_csv_originales: tuple[str, ...] | None = None

    def __post_init__(self):
        for valor in (self.numero_registro, self.linea_inicial, self.linea_final):
            if type(valor) is not int or valor <= 0:
                raise ValueError("Posiciones originales positivas requeridas")
        if self.linea_final < self.linea_inicial or type(self.estructura_correcta) is not bool:
            raise ValueError("Registro incoherente")
        if not isinstance(self.campos_originales, tuple) or len(self.campos_originales) > 32:
            raise ValueError("Campos originales acotados requeridos")
        for par in self.campos_originales:
            if (not isinstance(par, tuple) or len(par) != 2 or not isinstance(par[0], str)
                    or not 0 < len(par[0]) <= 128 or not isinstance(par[1], str)):
                raise ValueError("Pares de campo y texto original requeridos")
        if len({k for k, _ in self.campos_originales}) != len(self.campos_originales):
            raise ValueError("Campos duplicados no admitidos")


@dataclass(frozen=True)
class ResultadoQA:
    regla: ReglaQA
    registro: RegistroQA
    procedencia: ProcedenciaQA
    valores_originales: tuple[tuple[str, str | None], ...]
    evidencia: tuple[ReferenciaDocumentalQA, ...]
    parametros: tuple[tuple[str, str], ...]
    estado: EstadoResultadoQA
    diagnostico: str
    version_contrato: str = field(default=VERSION_CONTRATO_QA, init=False)

    @property
    def estado_evaluacion(self):
        if self.estado is EstadoResultadoQA.NO_EVALUADO:
            return EstadoEvaluacionQA.NO_EVALUADA
        if self.estado is EstadoResultadoQA.EVALUACION_INCOMPLETA:
            return EstadoEvaluacionQA.INCOMPLETA
        return EstadoEvaluacionQA.COMPLETA


@dataclass(frozen=True)
class InformeQA:
    estado: EstadoEvaluacionQA
    recorrido_completo: bool
    motivo_fin: str
    registros_examinados: int
    registros_finalizados: int
    resultados_emitidos: int
    evaluaciones_incompletas: int
    conteos: tuple[tuple[CategoriaQA, EstadoResultadoQA, int], ...]
    reglas_ejecutadas: tuple[ReglaQA, ...]
    procedencia: ProcedenciaQA
    configuracion: ConfiguracionQA
    limites: LimitesQA
    version_contrato: str = field(default=VERSION_CONTRATO_QA, init=False)
