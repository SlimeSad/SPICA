"""Evidencia y requisitos documentales inmutables; no son permisos de ejecución."""

from dataclasses import dataclass, field
from enum import Enum

from ...adquisicion.catalogo.modelos import ProductoCatalogo
from ..modelos_cientificos import (
    CondicionAplicabilidad, DimensionAplicabilidad, ReferenciaCientifica, ReglaCientifica,
)

VERSION_VERIFICADOR = "1.0.0"


def _texto(valor, maximo=4096):
    if type(valor) is not str or not valor.strip() or len(valor) > maximo:
        raise ValueError("Texto literal requerido y acotado")


def _tupla(valores, tipos, maximo=64):
    if type(valores) is not tuple or len(valores) > maximo or any(type(v) not in tipos for v in valores):
        raise TypeError("Tupla inmutable, tipada y acotada requerida")


def _textos(valores, maximo=64):
    _tupla(valores, (str,), maximo)
    for v in valores:
        _texto(v)
    if len(set(valores)) != len(valores):
        raise ValueError("Textos repetidos")


class NivelEvidencia(Enum):
    VERIFICADA = "verificada"
    DECLARADA = "declarada"
    INFERIDA = "inferida"
    DESCONOCIDA = "desconocida"
    CONTRADICTORIA = "contradictoria"


class NaturalezaEvidencia(Enum):
    DOCUMENTAL = "documental"
    SINTETICA = "sintetica"


class VigenciaDocumento(Enum):
    VIGENTE = "vigente_segun_evidencia_aportada"
    DESCONOCIDA = "desconocida"
    OBSOLETO = "obsoleto_segun_evidencia_aportada"


class AspectoAdicional(Enum):
    """Solo dimensiones que faltan en DimensionAplicabilidad del PASO 73."""
    AGREGACION_TEMPORAL = "agregacion_temporal"
    IDENTIDAD_ESTACION = "identidad_estacion"
    CONTINUIDAD_SERIE = "continuidad_serie"
    COBERTURA_APLICACION = "cobertura_aplicacion"
    VIGENCIA_APLICACION = "vigencia_aplicacion"
    RESTRICCION_INSTITUCIONAL = "restriccion_institucional"
    PARAMETROS_ESPECIFICOS = "parametros_especificos"
    INCERTIDUMBRE = "incertidumbre"
    ZONA_HORARIA = "zona_horaria"


DimensionDocumental = DimensionAplicabilidad | AspectoAdicional


def _dimension(valor):
    if type(valor) not in (DimensionAplicabilidad, AspectoAdicional):
        raise TypeError("Dimensión documental tipada requerida")


@dataclass(frozen=True)
class EvidenciaDocumental:
    referencia: ReferenciaCientifica
    localizacion: str
    naturaleza: NaturalezaEvidencia
    nivel: NivelEvidencia
    vigencia: VigenciaDocumento = VigenciaDocumento.DESCONOCIDA
    incertidumbres: tuple[str, ...] = ()
    contradicciones: tuple[str, ...] = ()
    pendientes: tuple[str, ...] = ()

    def __post_init__(self):
        if type(self.referencia) is not ReferenciaCientifica:
            raise TypeError("Referencia científica requerida; no se convierten fixtures experimentales")
        _texto(self.localizacion)
        for valor, tipo in ((self.naturaleza, NaturalezaEvidencia), (self.nivel, NivelEvidencia),
                            (self.vigencia, VigenciaDocumento)):
            if type(valor) is not tipo:
                raise TypeError("Clasificación de evidencia tipada requerida")
        for valores in (self.incertidumbres, self.contradicciones, self.pendientes):
            _textos(valores)
        if self.nivel is NivelEvidencia.CONTRADICTORIA and not self.contradicciones:
            raise ValueError("La evidencia contradictoria requiere explicación")


@dataclass(frozen=True)
class AfirmacionAplicabilidad:
    dimension: DimensionDocumental
    valor: str | None
    nivel: NivelEvidencia
    referencias: tuple[str, ...] = ()
    incertidumbres: tuple[str, ...] = ()
    contradicciones: tuple[str, ...] = ()
    pendientes: tuple[str, ...] = ()

    def __post_init__(self):
        _dimension(self.dimension)
        if type(self.nivel) is not NivelEvidencia:
            raise TypeError("Nivel de evidencia requerido")
        if self.valor is not None:
            _texto(self.valor, 512)
        if self.nivel is NivelEvidencia.DESCONOCIDA and self.valor is not None:
            raise ValueError("Lo desconocido conserva valor None")
        if self.nivel not in (NivelEvidencia.DESCONOCIDA, NivelEvidencia.CONTRADICTORIA) and self.valor is None:
            raise ValueError("Afirmación conocida requiere valor literal")
        for valores in (self.referencias, self.incertidumbres, self.contradicciones, self.pendientes):
            _textos(valores)
        if self.nivel is NivelEvidencia.VERIFICADA and not self.referencias:
            raise ValueError("Una afirmación verificada necesita referencias")
        if self.nivel is NivelEvidencia.CONTRADICTORIA and not self.contradicciones:
            raise ValueError("La contradicción requiere explicación")


@dataclass(frozen=True)
class CondicionAdicional:
    """Complemento de CondicionAplicabilidad; no reemplaza sus dimensiones."""
    dimension: AspectoAdicional
    valores_permitidos: tuple[str, ...]
    referencias: tuple[str, ...] = ()

    def __post_init__(self):
        if type(self.dimension) is not AspectoAdicional:
            raise TypeError("Solo aspectos adicionales")
        _textos(self.valores_permitidos)
        _textos(self.referencias)
        if not self.valores_permitidos:
            raise ValueError("Condición adicional con valores exactos requerida")
        for v in self.valores_permitidos:
            _texto(v, 512)


CondicionDocumental = CondicionAplicabilidad | CondicionAdicional


class TipoRequisito(Enum):
    OBLIGATORIO = "obligatorio"
    CONDICIONAL = "condicional"


@dataclass(frozen=True)
class RequisitoAplicabilidad:
    identificador: str
    condicion: CondicionDocumental
    tipo: TipoRequisito = TipoRequisito.OBLIGATORIO
    activar_si: CondicionDocumental | None = None

    def __post_init__(self):
        _texto(self.identificador, 128)
        if type(self.condicion) not in (CondicionAplicabilidad, CondicionAdicional):
            raise TypeError("Condición declarativa requerida; no expresiones ni callbacks")
        if type(self.tipo) is not TipoRequisito:
            raise TypeError("Tipo de requisito requerido")
        if self.tipo is TipoRequisito.OBLIGATORIO and self.activar_si is not None:
            raise ValueError("Un requisito obligatorio no se desactiva")
        if self.tipo is TipoRequisito.CONDICIONAL:
            if type(self.activar_si) not in (CondicionAplicabilidad, CondicionAdicional):
                raise TypeError("El requisito condicional necesita condición declarativa")
            if isinstance(self.activar_si, CondicionAplicabilidad) and self.activar_si.sin_restriccion:
                raise ValueError("La activación necesita valores exactos")


@dataclass(frozen=True)
class EspecificacionAplicabilidad:
    regla: ReglaCientifica
    requisitos: tuple[RequisitoAplicabilidad, ...]
    documentos: tuple[EvidenciaDocumental, ...]

    def __post_init__(self):
        if type(self.regla) is not ReglaCientifica:
            raise TypeError("Descriptor inmutable requerido; no catálogo ni habilitación")
        _tupla(self.requisitos, (RequisitoAplicabilidad,))
        _documentos(self.documentos)
        if len({r.identificador for r in self.requisitos}) != len(self.requisitos):
            raise ValueError("Requisito repetido")
        if len({r.condicion.dimension for r in self.requisitos}) != len(self.requisitos):
            raise ValueError("Solo un requisito por dimensión")
        referencias = {r.identificador: r for r in self.regla.referencias}
        if any(referencias.get(d.referencia.identificador) != d.referencia for d in self.documentos):
            raise ValueError("Documento ajeno a la referencia de la regla")
        for requisito in self.requisitos:
            for condicion in (requisito.condicion, requisito.activar_si):
                if condicion is not None and not set(condicion.referencias) <= referencias.keys():
                    raise ValueError("Requisito con referencia ajena")
        # Impide ocultar o debilitar las restricciones previas del catálogo.
        for condicion in self.regla.aplicabilidad:
            if not any(r.condicion == condicion and r.tipo is TipoRequisito.OBLIGATORIO for r in self.requisitos):
                raise ValueError("Las condiciones del catálogo deben conservarse obligatorias")
        if self.regla.parametros and not any(r.condicion.dimension is AspectoAdicional.PARAMETROS_ESPECIFICOS
                                           and r.tipo is TipoRequisito.OBLIGATORIO for r in self.requisitos):
            raise ValueError("Parámetros del catálogo requieren correspondencia documental explícita")


def _documentos(documentos):
    _tupla(documentos, (EvidenciaDocumental,))
    if len({d.referencia.identificador for d in documentos}) != len(documentos):
        raise ValueError("Identidad documental repetida")
    if len({d.naturaleza for d in documentos}) > 1:
        raise ValueError("No mezclar evidencia sintética y documental")


@dataclass(frozen=True)
class ExpedienteProducto:
    producto: ProductoCatalogo
    documentos: tuple[EvidenciaDocumental, ...]
    afirmaciones: tuple[AfirmacionAplicabilidad, ...]

    def __post_init__(self):
        if type(self.producto) is not ProductoCatalogo:
            raise TypeError("Instantánea ProductoCatalogo requerida; no lectores ni rutas")
        _documentos(self.documentos)
        _tupla(self.afirmaciones, (AfirmacionAplicabilidad,), 128)
        if len(set(self.afirmaciones)) != len(self.afirmaciones):
            raise ValueError("Afirmación repetida; agrupar referencias sin duplicar")
        ids = {d.referencia.identificador for d in self.documentos}
        if any(not set(a.referencias) <= ids for a in self.afirmaciones):
            raise ValueError("Afirmación sin documento registrado en el producto")


class EstadoAplicabilidad(Enum):
    COMPATIBILIDAD_DOCUMENTAL_DEMOSTRADA = "compatibilidad_documental_demostrada"
    COMPATIBILIDAD_CONDICIONADA = "compatibilidad_condicionada"
    INFORMACION_INSUFICIENTE = "informacion_insuficiente"
    INCOMPATIBILIDAD_DOCUMENTADA = "incompatibilidad_documentada"
    EVIDENCIA_CONTRADICTORIA = "evidencia_contradictoria"


class EstadoRequisito(Enum):
    DEMOSTRADO = "demostrado"
    CONDICIONADO = "condicionado"
    INSUFICIENTE = "insuficiente"
    INCOMPATIBLE = "incompatible"
    CONTRADICTORIO = "contradictorio"
    NO_APLICA = "no_aplica_segun_condicion_demostrada"


@dataclass(frozen=True)
class HallazgoAplicabilidad:
    requisito_id: str
    dimension: DimensionDocumental | None
    estado: EstadoRequisito
    motivos: tuple[str, ...]
    referencias: tuple[str, ...]

    def __post_init__(self):
        _texto(self.requisito_id)
        if self.dimension is not None:
            _dimension(self.dimension)
        if type(self.estado) is not EstadoRequisito:
            raise TypeError("Estado de requisito requerido")
        _textos(self.motivos)
        _textos(self.referencias, 128)
        if not self.motivos:
            raise ValueError("Todo hallazgo necesita motivos")


@dataclass(frozen=True)
class DiagnosticoAplicabilidad:
    especificacion: EspecificacionAplicabilidad
    expediente: ExpedienteProducto
    estado: EstadoAplicabilidad
    hallazgos: tuple[HallazgoAplicabilidad, ...]
    motivos: tuple[str, ...]
    restricciones: tuple[str, ...] = field(default=(
        "diagnostico_documental_no_es_aprobacion_cientifica",
        "sin_autorizacion_operativa_ni_ejecucion_nivel1",
        "sin_conversion_de_unidades_ni_equivalencias_inferidas",
        "clasificaciones_de_evidencia_aportadas_no_autenticadas_por_este_verificador",
    ), init=False)
    version_verificador: str = field(default=VERSION_VERIFICADOR, init=False)
    ejecucion_autorizada: bool = field(default=False, init=False)

    def __post_init__(self):
        if type(self.especificacion) is not EspecificacionAplicabilidad or type(self.expediente) is not ExpedienteProducto:
            raise TypeError("Traza documental inmutable requerida")
        if type(self.estado) is not EstadoAplicabilidad:
            raise TypeError("Estado diagnóstico requerido")
        _tupla(self.hallazgos, (HallazgoAplicabilidad,), 512)
        _textos(self.motivos)
        if not self.hallazgos or not self.motivos:
            raise ValueError("Diagnóstico con hallazgos y motivos requerido")
        if len({d.naturaleza for d in (*self.especificacion.documentos, *self.expediente.documentos)}) > 1:
            raise ValueError("No mezclar evidencia sintética y documental")

    @property
    def naturaleza_evidencia(self) -> NaturalezaEvidencia | None:
        documentos = (*self.especificacion.documentos, *self.expediente.documentos)
        return documentos[0].naturaleza if documentos else None

    def __bool__(self):
        raise TypeError("Un diagnóstico documental no es un permiso booleano")
