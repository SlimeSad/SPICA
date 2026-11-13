"""Envolventes RC1 declarativas. No registran proyectos ni ejecutan operaciones."""

from dataclasses import dataclass, field
from enum import Enum
import re

from ..adquisicion.almacenamiento.modelos import ProyectoCientifico, ObjetoCientifico
from ..adquisicion.readquisicion.modelos import EvidenciaLocal, EstadoLocal
from ..interoperabilidad.modelos import RecursoInteroperable
from ..interoperabilidad.adaptadores import (
    DiagnosticoAdaptacion, EstadoAdaptacion, NivelDiagnostico,
)
from ..calidad.modelos import ConfiguracionQA, LimitesQA
from ..calidad.restricciones import RestriccionQA, TipoRestriccionQA


VERSION_CONTEXTO = "0.1.0"
PERFIL_QA0 = "qa0-senamhi-16"


def _texto(v, *, opcional=False, maximo=512):
    if v is None and opcional:
        return
    if (type(v) is not str or not v.strip() or len(v) > maximo
            or any(ord(c) < 32 for c in v)):
        raise ValueError("texto_contextual_no_admitido")


def _tupla(v, tipo, maximo=64):
    if type(v) is not tuple:
        raise TypeError("tupla_contextual_tipificada_y_acotada_requerida")
    if len(v) > maximo:
        raise ValueError("coleccion_contextual_supera_cota")
    if any(type(x) is not tipo for x in v):
        raise TypeError("tupla_contextual_tipificada_y_acotada_requerida")


def _textos(v, maximo=64):
    _tupla(v, str, maximo)
    for x in v:
        _texto(x)
    if len(set(v)) != len(v):
        raise ValueError("referencia_contextual_repetida")


def _parametros(v):
    _tupla(v, tuple, 32)
    for par in v:
        if len(par) != 2:
            raise ValueError("parametro_contextual_requiere_par")
        _texto(par[0], maximo=128)
        _texto(par[1])
    if len({k for k, _ in v}) != len(v):
        raise ValueError("parametro_contextual_repetido")


def _version(v):
    if v != VERSION_CONTEXTO or type(v) is not str:
        raise ValueError("version_contextual_no_soportada")


def _restricciones(v):
    _tupla(v, RestriccionQA, 128)
    for r in v:
        _texto(r.codigo)
        _texto(r.motivo, maximo=4096)
        _textos(r.operaciones)
        if type(r.tipo) is not TipoRestriccionQA:
            raise TypeError("tipo_restriccion_no_admitido")
        if r.tipo is TipoRestriccionQA.BLOQUEO_USO_DEL_RESULTADO and not r.operaciones:
            raise ValueError("bloqueo_requiere_operaciones_explicitas")
    if len({r.codigo for r in v}) != len(v):
        raise ValueError("codigo_restriccion_repetido")


def combinar_restricciones(*grupos: tuple[RestriccionQA, ...]) -> tuple[RestriccionQA, ...]:
    """Unión estable por código; un conflicto nunca reduce silenciosamente un bloqueo."""
    resultado = {}
    for grupo in grupos:
        _restricciones(grupo)
        for r in grupo:
            if r.codigo in resultado and resultado[r.codigo] != r:
                raise ValueError("restriccion_contextual_contradictoria")
            resultado[r.codigo] = r
    valores = tuple(resultado.values())
    _restricciones(valores)
    return valores


@dataclass(frozen=True, slots=True)
class ConfiguracionContexto:
    """Configuración estructural literal, sin rutas, callbacks o evaluador de código.

    Las cotas limitan referencias de esta envolvente, no memoria/CPU del proceso.
    Los presupuestos de evaluación se reutilizan separadamente como LimitesQA.
    """

    perfil: str
    revision: str
    parametros: tuple[tuple[str, str], ...] = ()
    max_entradas: int = 16
    max_referencias_resultado: int = 256
    version_contrato: str = VERSION_CONTEXTO

    def __post_init__(self):
        _version(self.version_contrato)
        _texto(self.perfil)
        _texto(self.revision)
        _parametros(self.parametros)
        for v, tope in ((self.max_entradas, 64), (self.max_referencias_resultado, 4096)):
            if type(v) is not int or not 0 < v <= tope:
                raise ValueError("cota_contextual_no_admitida")


@dataclass(frozen=True, slots=True)
class ContextoProyecto:
    contexto_id: str
    proyecto: ProyectoCientifico
    configuracion: ConfiguracionContexto
    restricciones: tuple[RestriccionQA, ...] = ()
    version_contrato: str = VERSION_CONTEXTO

    def __post_init__(self):
        _version(self.version_contrato)
        _texto(self.contexto_id, maximo=128)
        if type(self.proyecto) is not ProyectoCientifico or type(self.configuracion) is not ConfiguracionContexto:
            raise TypeError("proyecto_y_configuracion_existentes_requeridos")
        _texto(self.proyecto.project_id, maximo=128)
        _restricciones(self.restricciones)

    @property
    def project_id(self) -> str:
        return self.proyecto.project_id

    @property
    def autoriza_operacion(self) -> bool:
        return False

    def __bool__(self):
        raise TypeError("contexto_declarado_no_es_permiso")


@dataclass(frozen=True, slots=True)
class ContextoEntrada:
    entrada_id: str
    proyecto: ContextoProyecto = field(repr=False)
    objeto: ObjetoCientifico
    recurso: RecursoInteroperable | None
    revision: str  # Revisión de la descripción local; no versión institucional.
    tipo_recurso: str
    perfil_estructural: str | None = None
    version_contenido: str | None = None
    asset_id: str | None = None  # Referencia opcional a MD-03; no un ActivoRAW nuevo.
    sha256_declarado: str | None = None
    size_bytes_declarado: int | None = None
    evidencia_local: EvidenciaLocal | None = None
    restricciones_adicionales: tuple[RestriccionQA, ...] = ()
    incertidumbres: tuple[str, ...] = ()
    version_contrato: str = VERSION_CONTEXTO

    def __post_init__(self):
        _version(self.version_contrato)
        _texto(self.entrada_id, maximo=128)
        _texto(self.revision)
        _texto(self.tipo_recurso)
        for v in (self.perfil_estructural, self.version_contenido, self.asset_id):
            _texto(v, opcional=True)
        if type(self.proyecto) is not ContextoProyecto or type(self.objeto) is not ObjetoCientifico:
            raise TypeError("contexto_y_objeto_md_requeridos")
        if self.objeto.project_id != self.proyecto.project_id:
            raise ValueError("objeto_de_otro_proyecto")
        if self.recurso is not None and type(self.recurso) is not RecursoInteroperable:
            raise TypeError("instantanea_interoperable_o_desconocida_requerida")
        if self.sha256_declarado is not None and (type(self.sha256_declarado) is not str
                or not re.fullmatch(r"[0-9a-f]{64}", self.sha256_declarado)):
            raise ValueError("huella_declarada_no_admitida")
        if self.size_bytes_declarado is not None and (type(self.size_bytes_declarado) is not int
                or self.size_bytes_declarado < 0):
            raise ValueError("tamano_declarado_no_admitido")
        e = self.evidencia_local
        if e is not None:
            if type(e) is not EvidenciaLocal or e.version_contrato != "1":
                raise TypeError("evidencia_local_compatible_requerida")
            if e.activo_id is not None and self.asset_id != e.activo_id:
                raise ValueError("evidencia_de_otro_activo")
            # Contrasta declaraciones; no abre el activo ni vuelve a calcular hashes.
            if e.estado is EstadoLocal.INTEGRO and (
                    (self.sha256_declarado is not None and self.sha256_declarado != e.sha256_observado)
                    or (self.size_bytes_declarado is not None and self.size_bytes_declarado != e.size_bytes_observado)):
                raise ValueError("contenido_y_evidencia_contradictorios")
        _restricciones(self.restricciones_adicionales)
        combinar_restricciones(self.proyecto.restricciones, self.restricciones_adicionales)
        _textos(self.incertidumbres, 32)

    @property
    def restricciones(self) -> tuple[RestriccionQA, ...]:
        return combinar_restricciones(self.proyecto.restricciones, self.restricciones_adicionales)

    @property
    def diagnosticos(self) -> tuple[DiagnosticoAdaptacion, ...]:
        faltantes = []
        if self.recurso is None:
            faltantes.append("identidad_recurso_y_procedencia_desconocidas")
        elif self.recurso.procedencia is None:
            faltantes.append("procedencia_desconocida")
        if self.perfil_estructural is None:
            faltantes.append("perfil_estructural_desconocido")
        if self.version_contenido is None:
            faltantes.append("version_contenido_desconocida")
        d = [DiagnosticoAdaptacion(c, "entrada", NivelDiagnostico.FALTANTE) for c in faltantes]
        if self.recurso is not None:
            d.extend(DiagnosticoAdaptacion("contradiccion_documental_declarada", "recurso",
                NivelDiagnostico.CONTRADICCION) for _ in self.recurso.contradicciones_declaradas)
        if self.evidencia_local is not None and self.evidencia_local.estado is EstadoLocal.INCONSISTENTE:
            d.append(DiagnosticoAdaptacion("integridad_declarada_inconsistente", "entrada",
                                          NivelDiagnostico.CONTRADICCION))
        return tuple(d)

    @property
    def estado(self) -> EstadoAdaptacion:
        niveles = {d.nivel for d in self.diagnosticos}
        if NivelDiagnostico.CONTRADICCION in niveles:
            return EstadoAdaptacion.CONTRADICTORIO
        return EstadoAdaptacion.PARCIAL if niveles else EstadoAdaptacion.DESCRITO


class TipoOperacion(Enum):
    DESCRIPCION_ESTRUCTURAL = "descripcion_estructural"
    QA_NIVEL0 = "qa_estructural_nivel0"


class EstadoOperacion(Enum):
    # Los estados QA, RAW y Plan no describen el ciclo de esta declaración.
    DECLARADA = "declarada"
    PLANIFICADA = "planificada"
    INICIADA = "iniciada"
    CONCLUIDA = "concluida_estructuralmente"
    PARCIAL = "parcial"
    FALLIDA = "fallida"
    CANCELADA = "cancelada"


@dataclass(frozen=True, slots=True)
class ContextoOperacion:
    operacion_id: str
    proyecto: ContextoProyecto = field(repr=False)
    entradas: tuple[ContextoEntrada, ...] = field(repr=False)
    tipo: TipoOperacion
    proposito: str
    parametros: tuple[tuple[str, str], ...] = ()
    limites_qa: LimitesQA | None = None
    configuracion_qa: ConfiguracionQA | None = None
    restricciones_adicionales: tuple[RestriccionQA, ...] = ()
    estado: EstadoOperacion = EstadoOperacion.DECLARADA
    diagnosticos: tuple[DiagnosticoAdaptacion, ...] = ()
    referencias_resultado: tuple[str, ...] = ()  # Referencias declaradas, no archivos.
    version_contrato: str = VERSION_CONTEXTO

    def __post_init__(self):
        _version(self.version_contrato)
        _texto(self.operacion_id, maximo=128)
        _texto(self.proposito)
        if type(self.proyecto) is not ContextoProyecto:
            raise TypeError("contexto_proyecto_requerido")
        _tupla(self.entradas, ContextoEntrada, self.proyecto.configuracion.max_entradas)
        if not self.entradas or len({e.entrada_id for e in self.entradas}) != len(self.entradas):
            raise ValueError("entradas_vacias_o_duplicadas")
        if any(e.proyecto != self.proyecto for e in self.entradas):
            raise ValueError("entrada_de_otro_contexto")
        if type(self.tipo) is not TipoOperacion or type(self.estado) is not EstadoOperacion:
            raise TypeError("tipo_y_estado_operacion_requeridos")
        _parametros(self.parametros)
        if self.tipo is TipoOperacion.QA_NIVEL0:
            if type(self.limites_qa) is not LimitesQA or type(self.configuracion_qa) is not ConfiguracionQA:
                raise TypeError("presupuesto_y_configuracion_qa_requeridos")
            # Copia solo las cuatro cotas para validar; no cambia el presupuesto recibido.
            LimitesQA(**vars(self.limites_qa))
            if self.parametros or self.proyecto.configuracion.parametros:
                raise ValueError("parametros_qa_requieren_configuracion_qa_tipificada")
        elif self.limites_qa is not None or self.configuracion_qa is not None:
            raise ValueError("configuracion_qa_en_otro_tipo_operacion")
        _restricciones(self.restricciones_adicionales)
        combinar_restricciones(self.proyecto.restricciones,
            *(e.restricciones for e in self.entradas), self.restricciones_adicionales)
        _tupla(self.diagnosticos, DiagnosticoAdaptacion)
        _textos(self.referencias_resultado, self.proyecto.configuracion.max_referencias_resultado)
        if self.estado in (EstadoOperacion.DECLARADA, EstadoOperacion.PLANIFICADA) and self.referencias_resultado:
            raise ValueError("resultado_previo_al_inicio")
        if self.estado is EstadoOperacion.CONCLUIDA and (not self.referencias_resultado
                or any(d.nivel is not NivelDiagnostico.INFORMACION for d in self.diagnosticos)):
            raise ValueError("conclusion_sin_referencias_o_con_pendientes")
        if self.estado in (EstadoOperacion.PARCIAL, EstadoOperacion.FALLIDA, EstadoOperacion.CANCELADA):
            if not self.diagnosticos:
                raise ValueError("estado_no_concluido_requiere_causa")
        if self.estado is EstadoOperacion.PARCIAL and not self.referencias_resultado:
            raise ValueError("parcial_requiere_resultados_identificados")

    @property
    def restricciones(self) -> tuple[RestriccionQA, ...]:
        return combinar_restricciones(self.proyecto.restricciones,
            *(e.restricciones for e in self.entradas), self.restricciones_adicionales)

    @property
    def autoriza_operacion(self) -> bool:
        return False

    def __bool__(self):
        raise TypeError("operacion_declarada_no_es_permiso")
