"""Descriptores RC2 en memoria; ningún literal se interpreta como código o dato."""

from dataclasses import dataclass, field
from enum import Enum

from ...adquisicion.catalogo.modelos import VariableCatalogo, EstadoVerificacion as V
from ...calidad.restricciones import RestriccionQA
from ...contextos import ContextoEntrada, ContextoOperacion, combinar_restricciones
from ..modelos import Respaldo, DimensionEvaluacion, EstadoAptitud, ResultadoAptitud
from ..adaptadores import DiagnosticoAdaptacion, NivelDiagnostico


VERSION_PERFILES = "0.1.0"
MAX_CAMPOS = 64


def _texto(v, *, opcional=False, vacio=False, maximo=512):
    if v is None and opcional:
        return
    if (type(v) is not str or len(v) > maximo or (not vacio and not v.strip())
            or any(ord(c) < 32 for c in v)):
        raise ValueError("literal_perfil_no_admitido")


def _tupla(v, tipo, maximo=MAX_CAMPOS):
    if type(v) is not tuple or any(type(x) is not tipo for x in v):
        raise TypeError("tupla_perfil_tipificada_requerida")
    if len(v) > maximo:
        raise ValueError("cota_perfil_excedida")


def _textos(v, *, maximo=32, vacio=False):
    _tupla(v, str, maximo)
    for x in v:
        _texto(x, vacio=vacio)
    if len(set(v)) != len(v):
        raise ValueError("literal_perfil_repetido")


def _version(v):
    if type(v) is not str or v != VERSION_PERFILES:
        raise ValueError("version_contrato_perfil_no_soportada")


@dataclass(frozen=True, slots=True)
class DeclaracionPerfil:
    """Literal y respaldo aportado. VERIFICADO no autentica la referencia."""

    valor: str | None = None
    respaldo: Respaldo = field(default_factory=Respaldo)

    def __post_init__(self):
        _texto(self.valor, opcional=True)
        if type(self.respaldo) is not Respaldo:
            raise TypeError("respaldo_existente_requerido")
        if self.valor is None and self.respaldo.estado is not V.DESCONOCIDO:
            raise ValueError("respaldo_sin_literal")


class EstadoUnidad(Enum):
    ACREDITADA = "acreditada_por_evidencia_aportada"
    DECLARADA = "solamente_declarada"
    DESCONOCIDA = "desconocida"
    CONTRADICTORIA = "contradictoria"
    NO_APLICABLE = "no_aplicable_documentada"


@dataclass(frozen=True, slots=True)
class UnidadPerfil:
    estado: EstadoUnidad = EstadoUnidad.DESCONOCIDA
    literal: str | None = None
    respaldo: Respaldo = field(default_factory=Respaldo)
    dimension_fisica: DeclaracionPerfil = field(default_factory=DeclaracionPerfil)
    contradicciones: tuple[str, ...] = ()

    def __post_init__(self):
        if (type(self.estado) is not EstadoUnidad or type(self.respaldo) is not Respaldo
                or type(self.dimension_fisica) is not DeclaracionPerfil):
            raise TypeError("unidad_y_evidencia_tipificadas_requeridas")
        _texto(self.literal, opcional=True)
        _textos(self.contradicciones)
        e, r = self.estado, self.respaldo.estado
        if e in (EstadoUnidad.ACREDITADA, EstadoUnidad.DECLARADA) and self.literal is None:
            raise ValueError("unidad_conocida_sin_literal")
        if e is EstadoUnidad.DECLARADA and r is not V.DECLARADO:
            raise ValueError("unidad_declarada_requiere_respaldo_declarado")
        if e in (EstadoUnidad.ACREDITADA, EstadoUnidad.NO_APLICABLE, EstadoUnidad.CONTRADICTORIA) and r is not V.VERIFICADO:
            raise ValueError("estado_unidad_requiere_evidencia_explicita")
        if e in (EstadoUnidad.DESCONOCIDA, EstadoUnidad.NO_APLICABLE) and self.literal is not None:
            raise ValueError("unidad_desconocida_o_no_aplicable_con_literal")
        if e is EstadoUnidad.DESCONOCIDA and r is not V.DESCONOCIDO:
            raise ValueError("unidad_desconocida_con_respaldo_concluyente")
        if bool(self.contradicciones) != (e is EstadoUnidad.CONTRADICTORIA):
            raise ValueError("contradicciones_y_estado_unidad_incoherentes")
        d = self.dimension_fisica
        if d.valor is not None and d.respaldo.estado is not V.VERIFICADO:
            raise ValueError("dimension_fisica_sin_evidencia")
        if e is EstadoUnidad.NO_APLICABLE and d.valor is not None:
            raise ValueError("dimension_fisica_con_unidad_no_aplicable")


@dataclass(frozen=True, slots=True)
class CampoInformacion:
    nombre: str
    tipo: DeclaracionPerfil
    variable: VariableCatalogo | None = None
    respaldo_variable: Respaldo = field(default_factory=Respaldo)
    significado: DeclaracionPerfil = field(default_factory=DeclaracionPerfil)
    unidad: UnidadPerfil = field(default_factory=UnidadPerfil)
    valores_ausentes: tuple[str, ...] | None = None  # () = ninguno; None = desconocidos.
    respaldo_ausentes: Respaldo = field(default_factory=Respaldo)
    agregacion: DeclaracionPerfil = field(default_factory=DeclaracionPerfil)
    calendario: DeclaracionPerfil = field(default_factory=DeclaracionPerfil)

    def __post_init__(self):
        _texto(self.nombre)
        for d in (self.tipo, self.significado, self.agregacion, self.calendario):
            if type(d) is not DeclaracionPerfil:
                raise TypeError("declaraciones_perfil_requeridas")
        if (type(self.unidad) is not UnidadPerfil or type(self.respaldo_variable) is not Respaldo
                or type(self.respaldo_ausentes) is not Respaldo):
            raise TypeError("unidad_y_respaldos_requeridos")
        if self.variable is not None:
            if type(self.variable) is not VariableCatalogo:
                raise TypeError("variable_catalogo_existente_requerida")
            for n in ("id_interno", "producto_id", "codigo_original", "nombre_original", "descripcion",
                      "unidad_declarada", "frecuencia_declarada", "tipo_medicion",
                      "version_diccionario", "procedencia_diccionario"):
                _texto(getattr(self.variable, n), opcional=True, maximo=4096)
            for n in ("unidad_declarada", "frecuencia_declarada", "tipo_medicion"):
                _texto(getattr(self.variable, n), opcional=True)
            if self.unidad.literal is not None and self.variable.unidad_declarada is not None:
                if self.unidad.literal != self.variable.unidad_declarada and self.unidad.estado is not EstadoUnidad.CONTRADICTORIA:
                    raise ValueError("unidad_contradice_catalogo_sin_estado_de_conflicto")
        elif self.respaldo_variable.estado is not V.DESCONOCIDO:
            raise ValueError("respaldo_de_variable_ausente")
        if self.valores_ausentes is not None:
            _textos(self.valores_ausentes, vacio=True)
        elif self.respaldo_ausentes.estado is not V.DESCONOCIDO:
            raise ValueError("convencion_ausentes_sin_declaracion")


@dataclass(frozen=True, slots=True)
class PerfilInformacion:
    identificador: str
    version: str  # Revisión local del perfil, distinta de versión institucional/contenido.
    tipo_recurso: str
    campos: tuple[CampoInformacion, ...]
    ambito: DeclaracionPerfil = field(default_factory=DeclaracionPerfil)
    restricciones: tuple[RestriccionQA, ...] = ()
    incertidumbres: tuple[str, ...] = ()
    version_contrato: str = VERSION_PERFILES

    def __post_init__(self):
        _version(self.version_contrato)
        for x in (self.identificador, self.version, self.tipo_recurso):
            _texto(x)
        _tupla(self.campos, CampoInformacion)
        if len({c.nombre for c in self.campos}) != len(self.campos):
            raise ValueError("nombre_campo_repetido")
        if type(self.ambito) is not DeclaracionPerfil:
            raise TypeError("ambito_declarado_requerido")
        combinar_restricciones(self.restricciones)
        _textos(self.incertidumbres)


class AspectoCampo(Enum):
    TIPO = "tipo"
    VARIABLE = "variable"
    SIGNIFICADO = "significado"
    UNIDAD = "unidad"
    DIMENSION_FISICA = "dimension_fisica"
    TIPO_MEDICION = "tipo_medicion"
    FRECUENCIA = "frecuencia_declarada"
    AUSENTES = "valores_ausentes"
    AGREGACION = "agregacion"
    CALENDARIO = "calendario"


@dataclass(frozen=True, slots=True)
class FinalidadCompatibilidad:
    identificador: str  # Clave exacta de operación afectada por RestriccionQA.
    descripcion: str
    campos: tuple[tuple[str, str], ...]  # Correspondencia explícita; no se deduce por nombre.
    versiones_admitidas: tuple[tuple[str, str], ...]  # (perfil_id, versión local).
    aspectos: tuple[AspectoCampo, ...]
    referencias: DimensionEvaluacion | None = None
    requiere_mismo_recurso: bool = False
    requiere_mismo_contenido: bool = False
    requiere_mismo_sitio: bool = False
    version_contrato: str = VERSION_PERFILES

    def __post_init__(self):
        _version(self.version_contrato)
        _texto(self.identificador)
        _texto(self.descripcion)
        for pares in (self.campos, self.versiones_admitidas):
            _tupla(pares, tuple)
            if not pares:
                raise ValueError("finalidad_sin_campos_o_versiones")
            for par in pares:
                if len(par) != 2:
                    raise ValueError("correspondencia_requiere_dos_literales")
                for x in par:
                    _texto(x)
            if len(set(pares)) != len(pares):
                raise ValueError("correspondencia_repetida")
        for lado in (0, 1):
            if len({p[lado] for p in self.campos}) != len(self.campos):
                raise ValueError("correspondencia_campos_no_biyectiva")
        _tupla(self.aspectos, AspectoCampo, len(AspectoCampo))
        if AspectoCampo.TIPO not in self.aspectos or len(set(self.aspectos)) != len(self.aspectos):
            raise ValueError("aspectos_repetidos_o_sin_tipo")
        if AspectoCampo.SIGNIFICADO in self.aspectos and AspectoCampo.VARIABLE not in self.aspectos:
            raise ValueError("significado_requiere_identidad_variable_explicita")
        if AspectoCampo.DIMENSION_FISICA in self.aspectos and AspectoCampo.UNIDAD not in self.aspectos:
            raise ValueError("dimension_requiere_evaluar_unidad")
        if self.referencias is not None and type(self.referencias) is not DimensionEvaluacion:
            raise TypeError("dimension_evaluacion_existente_requerida")
        for v in (self.requiere_mismo_recurso, self.requiere_mismo_contenido, self.requiere_mismo_sitio):
            if type(v) is not bool:
                raise TypeError("politica_identidad_requiere_bool")
        if self.requiere_mismo_sitio and self.referencias not in (DimensionEvaluacion.ESPACIAL, DimensionEvaluacion.AMBAS):
            raise ValueError("identidad_sitio_requiere_referencia_espacial")


@dataclass(frozen=True, slots=True)
class EntradaPerfil:
    """Vínculo con RC1, sin copiar identidades, contenido, evidencias o marcos."""

    entrada: ContextoEntrada = field(repr=False)
    perfil: PerfilInformacion = field(repr=False)

    def __post_init__(self):
        if type(self.entrada) is not ContextoEntrada or type(self.perfil) is not PerfilInformacion:
            raise TypeError("contexto_entrada_y_perfil_requeridos")
        e, p = self.entrada, self.perfil
        if e.tipo_recurso != p.tipo_recurso or e.perfil_estructural not in (None, p.identificador):
            raise ValueError("perfil_no_corresponde_a_entrada")
        if e.recurso is not None:
            atributos = e.recurso.atributos_declarados
            if atributos and any(c.nombre not in atributos for c in p.campos):
                raise ValueError("campos_fuera_del_recurso_declarado")
            for c in p.campos:
                if c.variable is not None and (c.variable.fuente != e.recurso.identidad.fuente
                        or e.recurso.identidad.producto_id is not None
                        and c.variable.producto_id != e.recurso.identidad.producto_id):
                    raise ValueError("variable_fuera_del_ambito_del_recurso")
        combinar_restricciones(e.restricciones, p.restricciones)

    @property
    def restricciones(self) -> tuple[RestriccionQA, ...]:
        return combinar_restricciones(self.entrada.restricciones, self.perfil.restricciones)


LIMITACIONES_RC2 = (
    "solo_descriptores_y_finalidad_declarada", "evidencia_aportada_no_autenticada",
    "sin_comprobacion_fisica_de_contenido", "sin_transformaciones",
    "sin_validacion_cientifica", "sin_autorizacion_ni_ejecucion",
)


@dataclass(frozen=True, slots=True)
class ResultadoCompatibilidad:
    primero: EntradaPerfil = field(repr=False)
    segundo: EntradaPerfil = field(repr=False)
    finalidad: FinalidadCompatibilidad
    diagnosticos: tuple[DiagnosticoAdaptacion, ...]
    restricciones: tuple[RestriccionQA, ...]
    aptitud_referencias: ResultadoAptitud | None = field(default=None, repr=False)
    operacion: ContextoOperacion | None = field(default=None, repr=False)
    limitaciones: tuple[str, ...] = field(default=LIMITACIONES_RC2, init=False)
    version_comparador: str = field(default=VERSION_PERFILES, init=False)

    def __post_init__(self):
        if (type(self.primero) is not EntradaPerfil or type(self.segundo) is not EntradaPerfil
                or type(self.finalidad) is not FinalidadCompatibilidad):
            raise TypeError("resultado_perfiles_tipificado_requerido")
        _tupla(self.diagnosticos, DiagnosticoAdaptacion, 4096)
        if not self.diagnosticos:
            raise ValueError("resultado_sin_diagnosticos")
        adicionales = ()
        if self.operacion is not None:
            if type(self.operacion) is not ContextoOperacion:
                raise TypeError("contexto_operacion_existente_requerido")
            adicionales = self.operacion.restricciones
        object.__setattr__(self, "restricciones", combinar_restricciones(
            self.primero.restricciones, self.segundo.restricciones, self.restricciones, adicionales))
        if self.aptitud_referencias is not None and type(self.aptitud_referencias) is not ResultadoAptitud:
            raise TypeError("aptitud_existente_requerida")

    @property
    def estado(self) -> EstadoAptitud:
        niveles = {d.nivel for d in self.diagnosticos}
        if NivelDiagnostico.CONTRADICCION in niveles:
            return EstadoAptitud.INCOMPATIBLE
        if NivelDiagnostico.FALTANTE in niveles:
            return EstadoAptitud.PENDIENTE_DE_EVIDENCIA
        return EstadoAptitud.APTO_ESTRUCTURALMENTE

    @property
    def autoriza_operacion(self) -> bool:
        return False

    def __bool__(self):
        raise TypeError("compatibilidad_estructural_no_es_permiso")
