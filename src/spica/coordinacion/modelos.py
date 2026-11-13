"""Composición RC3 de referencias existentes, sin ejecución o persistencia."""

from dataclasses import dataclass, field

from ..calidad.modelos import InformeQA
from ..calidad.restricciones import RestriccionQA
from ..contextos import ContextoProyecto, ContextoOperacion, VinculoResultadoQA, combinar_restricciones
from ..interoperabilidad.adaptadores import DiagnosticoAdaptacion, NivelDiagnostico as N
from ..interoperabilidad.modelos import EstadoAptitud as E
from ..interoperabilidad.perfiles import EntradaPerfil, FinalidadCompatibilidad, ResultadoCompatibilidad

VERSION_COORDINACION = "0.1.0"
MAX_OPERACIONES = 32
MAX_DEPENDENCIAS = 128


def _texto(v):
    if type(v) is not str or not v.strip() or len(v) > 512 or any(ord(c) < 32 for c in v):
        raise ValueError("literal_coordinacion_no_admitido")


def _tupla(v, tipo, maximo):
    if type(v) is not tuple or any(type(x) is not tipo for x in v):
        raise TypeError("tupla_coordinacion_tipificada_requerida")
    if len(v) > maximo:
        raise ValueError("cota_coordinacion_excedida")


def _textos(v, maximo=128):
    _tupla(v, str, maximo)
    for x in v:
        _texto(x)
    if len(v) != len(set(v)):
        raise ValueError("referencia_coordinacion_repetida")


@dataclass(frozen=True, slots=True)
class LimitesComposicion:
    max_operaciones: int = 16
    max_dependencias: int = 64
    max_profundidad: int = 16  # Nodos del camino más largo; raíz = 1.
    max_visitas_descriptores: int = 100_000
    max_bytes_texto: int = 4_194_304
    max_registros_qa_declarados: int = 100_000
    max_resultados_qa_declarados: int = 1_000_000

    def __post_init__(self):
        for nombre, tope in (("max_operaciones", MAX_OPERACIONES), ("max_dependencias", MAX_DEPENDENCIAS),
                ("max_profundidad", MAX_OPERACIONES), ("max_visitas_descriptores", 200_000),
                ("max_bytes_texto", 8_388_608), ("max_registros_qa_declarados", 64_000_000),
                ("max_resultados_qa_declarados", 160_000_000)):
            v = getattr(self, nombre)
            if type(v) is not int or not 0 < v <= tope:
                raise ValueError("limite_composicion_no_admitido")


@dataclass(frozen=True, slots=True)
class DependenciaOperacion:
    predecesora: str
    dependiente: str
    referencias_resultado: tuple[str, ...] = ()  # () exige el cierre técnico completo.

    def __post_init__(self):
        _texto(self.predecesora)
        _texto(self.dependiente)
        _textos(self.referencias_resultado)


@dataclass(frozen=True, slots=True)
class RequisitoCompatibilidad:
    primero: EntradaPerfil = field(repr=False)
    segundo: EntradaPerfil = field(repr=False)
    finalidad: FinalidadCompatibilidad

    def __post_init__(self):
        if (type(self.primero) is not EntradaPerfil or type(self.segundo) is not EntradaPerfil
                or type(self.finalidad) is not FinalidadCompatibilidad):
            raise TypeError("requisito_rc2_tipificado_requerido")


@dataclass(frozen=True, slots=True)
class CierreQA:
    """Evidencia previamente producida y aportada; su coherencia se coteja al inspeccionar."""

    informe: InformeQA = field(repr=False)
    vinculos: tuple[VinculoResultadoQA, ...] = field(repr=False)

    def __post_init__(self):
        if type(self.informe) is not InformeQA:
            raise TypeError("informe_qa_existente_requerido")
        _tupla(self.vinculos, VinculoResultadoQA, 128)


@dataclass(frozen=True, slots=True)
class NodoOperacion:
    contexto: ContextoOperacion = field(repr=False)
    usos_declarados: tuple[str, ...] | None  # Alcance de cotejo, nunca operaciones autorizadas.
    compatibilidades: tuple[RequisitoCompatibilidad, ...] = field(default=(), repr=False)
    cierre_qa: CierreQA | None = field(default=None, repr=False)

    def __post_init__(self):
        if type(self.contexto) is not ContextoOperacion or self.contexto.version_contrato != "0.1.0":
            raise TypeError("contexto_operacion_rc1_compatible_requerido")
        if self.usos_declarados is not None:
            _textos(self.usos_declarados, 16)
            if not self.usos_declarados:
                raise ValueError("alcance_vacio_no_equivale_a_desconocido")
        _tupla(self.compatibilidades, RequisitoCompatibilidad, 8)
        if len({r.finalidad.identificador for r in self.compatibilidades}) != len(self.compatibilidades):
            raise ValueError("requisito_compatibilidad_duplicado")
        if self.cierre_qa is not None and type(self.cierre_qa) is not CierreQA:
            raise TypeError("cierre_qa_tipificado_requerido")


def fuentes_restricciones(nodo):
    """Origen de referencias; varias copias no son evidencias independientes."""
    o = nodo.contexto
    yield o.restricciones, "contexto_operacion:" + o.operacion_id
    for requisito in nodo.compatibilidades:
        for ep in (requisito.primero, requisito.segundo):
            yield ep.restricciones, "entrada_perfil:" + ep.entrada.entrada_id + ":" + ep.perfil.identificador
    if nodo.cierre_qa is not None:
        for v in nodo.cierre_qa.vinculos:
            yield v.restricciones, "vinculo_qa:" + o.operacion_id + ":" + v.referencia_resultado


@dataclass(frozen=True, slots=True)
class ComposicionOperaciones:
    identificador: str
    proyecto: ContextoProyecto = field(repr=False)
    operaciones: tuple[NodoOperacion, ...] = field(repr=False)
    dependencias: tuple[DependenciaOperacion, ...]
    finalidad: str
    limites: LimitesComposicion = field(default_factory=LimitesComposicion)
    restricciones_adicionales: tuple[RestriccionQA, ...] = ()
    version_contrato: str = VERSION_COORDINACION

    def __post_init__(self):
        _texto(self.identificador)
        _texto(self.finalidad)
        if type(self.version_contrato) is not str or self.version_contrato != VERSION_COORDINACION:
            raise ValueError("version_coordinacion_no_soportada")
        if type(self.proyecto) is not ContextoProyecto or self.proyecto.version_contrato != "0.1.0":
            raise TypeError("proyecto_rc1_compatible_requerido")
        if type(self.limites) is not LimitesComposicion:
            raise TypeError("limites_composicion_requeridos")
        _tupla(self.operaciones, NodoOperacion, MAX_OPERACIONES)
        _tupla(self.dependencias, DependenciaOperacion, MAX_DEPENDENCIAS)
        combinar_restricciones(self.proyecto.restricciones, self.restricciones_adicionales,
            *(rs for n in self.operaciones for rs, _ in fuentes_restricciones(n)))

    @property
    def autoriza_operacion(self):
        return False

    def __bool__(self):
        raise TypeError("composicion_declarativa_no_es_permiso")


@dataclass(frozen=True, slots=True)
class RestriccionPropagada:
    restriccion: RestriccionQA
    origenes: tuple[str, ...]


def estado_diagnosticos(ds):
    niveles = {d.nivel for d in ds}
    return E.INCOMPATIBLE if N.CONTRADICCION in niveles else E.PENDIENTE_DE_EVIDENCIA if N.FALTANTE in niveles else E.APTO_ESTRUCTURALMENTE


@dataclass(frozen=True, slots=True)
class InspeccionOperacion:
    nodo: NodoOperacion = field(repr=False)
    diagnosticos: tuple[DiagnosticoAdaptacion, ...]
    restricciones: tuple[RestriccionPropagada, ...]
    compatibilidades: tuple[ResultadoCompatibilidad, ...] = field(repr=False)
    cierre_qa_coherente_completo: bool

    @property
    def estado_estructural(self):
        return estado_diagnosticos(self.diagnosticos)

    @property
    def habilitada_declarativamente(self):
        from ..contextos import EstadoOperacion
        return (self.estado_estructural is E.APTO_ESTRUCTURALMENTE
                and self.nodo.contexto.estado in (EstadoOperacion.DECLARADA, EstadoOperacion.PLANIFICADA))


@dataclass(frozen=True, slots=True)
class InformeComposicion:
    composicion: ComposicionOperaciones = field(repr=False)
    operaciones: tuple[InspeccionOperacion, ...]
    diagnosticos: tuple[DiagnosticoAdaptacion, ...]
    orden_precedencia: tuple[str, ...]
    restricciones: tuple[RestriccionPropagada, ...]
    cuotas_qa_declaradas: tuple[int, int]  # Suma de máximos de registros y resultados por operación QA.
    consumos_qa_aportados: tuple[tuple[str, int, int], ...]  # Solo cierres coherentes, no consumo global.
    visitas_descriptores: int
    bytes_texto_descriptores: int | None  # None si la medición acotada se interrumpió.
    cancelada: bool  # Cancelación de inspección, no de motores externos.
    version_inspector: str = field(default=VERSION_COORDINACION, init=False)
    ejecucion_realizada: bool = field(default=False, init=False)
    recursos_reservados: bool = field(default=False, init=False)

    @property
    def estado_estructural(self):
        return estado_diagnosticos(self.diagnosticos + tuple(d for n in self.operaciones for d in n.diagnosticos))

    @property
    def habilitadas_declarativamente(self):
        if self.cancelada:
            return ()
        return tuple(n.nodo.contexto.operacion_id for n in self.operaciones if n.habilitada_declarativamente)

    @property
    def autoriza_operacion(self):
        return False

    def __bool__(self):
        raise TypeError("habilitacion_estructural_no_es_permiso")
