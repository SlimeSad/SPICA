"""Descriptores RC4 en memoria. No almacenan bytes ni acreditan efectos."""

from dataclasses import dataclass, field
from enum import Enum

from ..adquisicion.catalogo.modelos import EstadoVerificacion as V
from ..adquisicion.nucleo.modelos import EstadoIntegridad
from ..adquisicion.readquisicion.modelos import EstadoLocal
from ..calidad.modelos import EstadoEvaluacionQA
from ..calidad.restricciones import RestriccionQA
from ..contextos import ContextoOperacion, combinar_restricciones
from ..coordinacion import ComposicionOperaciones, InformeComposicion, RestriccionPropagada
from ..interoperabilidad.adaptadores import DiagnosticoAdaptacion, NivelDiagnostico as N
from ..interoperabilidad.modelos import EstadoAptitud as E, Respaldo
from ..interoperabilidad.perfiles import EntradaPerfil


VERSION_ARTEFACTOS = "0.1.0"


def _texto(v, opcional=False):
    if v is None and opcional:
        return
    if type(v) is not str or not v.strip() or len(v) > 512 or any(ord(c) < 32 for c in v):
        raise ValueError("literal_artefacto_no_admitido")


def _tupla(v, tipo, maximo):
    if type(v) is not tuple or any(type(x) is not tipo for x in v):
        raise TypeError("tupla_artefactos_tipificada_requerida")
    if len(v) > maximo:
        raise ValueError("cota_artefactos_excedida")


def _version(v):
    if type(v) is not str or v != VERSION_ARTEFACTOS:
        raise ValueError("version_artefactos_no_soportada")


class TipoArtefacto(Enum):
    ORIGINAL = "original"
    PREPARADO = "preparado"
    DERIVADO = "derivado"


class EstadoArtefacto(Enum):
    DESCRITO = "descrito"
    PARCIAL = "parcial"
    FINAL_DECLARADO = "final_declarado"


class DisponibilidadArtefacto(Enum):
    DESCONOCIDA = "desconocida"
    PRESENTE_SEGUN_EVIDENCIA = "presente_segun_evidencia_aportada"
    AUSENTE_SEGUN_EVIDENCIA = "ausente_segun_evidencia_aportada"
    NO_COMPROBABLE = "comprobacion_no_disponible"


@dataclass(frozen=True, slots=True)
class ReferenciaArtefacto:
    object_id: str  # MD-02, no nombre de archivo, asset_id o SHA.
    revision: str  # Revisión literal local de ContextoEntrada.
    version_contrato: str = VERSION_ARTEFACTOS

    def __post_init__(self):
        _version(self.version_contrato)
        _texto(self.object_id)
        _texto(self.revision)


@dataclass(frozen=True, slots=True)
class DescriptorArtefacto:
    entrada_perfil: EntradaPerfil = field(repr=False)
    tipo: TipoArtefacto
    contenido_id: str | None = None
    estado_logico: EstadoArtefacto = EstadoArtefacto.DESCRITO
    formato: str | None = None
    generacion_conservacion_ref: str | None = None  # Histórica, no comprobación J/K.
    restricciones_adicionales: tuple[RestriccionQA, ...] = ()
    incertidumbres: tuple[str, ...] = ()
    diagnosticos: tuple[DiagnosticoAdaptacion, ...] = ()
    version_contrato: str = VERSION_ARTEFACTOS
    revision_cientifica: EstadoEvaluacionQA = field(default=EstadoEvaluacionQA.NO_EVALUADA, init=False)

    def __post_init__(self):
        _version(self.version_contrato)
        if type(self.entrada_perfil) is not EntradaPerfil:
            raise TypeError("entrada_perfil_rc2_requerida")
        if type(self.tipo) is not TipoArtefacto or type(self.estado_logico) is not EstadoArtefacto:
            raise TypeError("tipo_y_estado_artefacto_requeridos")
        for v in (self.contenido_id, self.formato, self.generacion_conservacion_ref):
            _texto(v, opcional=True)
        _tupla(self.incertidumbres, str, 32)
        for v in self.incertidumbres:
            _texto(v)
        _tupla(self.diagnosticos, DiagnosticoAdaptacion, 64)
        combinar_restricciones(self.entrada_perfil.restricciones, self.restricciones_adicionales)
        # MD-03 y EvidenciaLocal describen originales; no inventar un activo RAW
        # para acomodar un preparado/derivado sin adaptador físico aprobado.
        e = self.entrada_perfil.entrada
        ReferenciaArtefacto(e.objeto.object_id, e.revision)
        if self.tipo is not TipoArtefacto.ORIGINAL and (e.asset_id is not None
                or e.evidencia_local is not None and e.evidencia_local.estado is not EstadoLocal.DESCONOCIDO):
            raise ValueError("evidencia_raw_no_admitida_para_derivado")

    @property
    def referencia(self):
        e = self.entrada_perfil.entrada
        return ReferenciaArtefacto(e.objeto.object_id, e.revision)

    @property
    def restricciones(self):
        """Solo fuentes locales; la clausura de antecesores está en InformeArtefacto."""
        return combinar_restricciones(self.entrada_perfil.restricciones, self.restricciones_adicionales)

    @property
    def disponibilidad(self):
        e = self.entrada_perfil.entrada.evidencia_local
        if e is None:
            return DisponibilidadArtefacto.DESCONOCIDA
        return {EstadoLocal.INTEGRO: DisponibilidadArtefacto.PRESENTE_SEGUN_EVIDENCIA,
                EstadoLocal.AUSENTE: DisponibilidadArtefacto.AUSENTE_SEGUN_EVIDENCIA,
                EstadoLocal.NO_DISPONIBLE: DisponibilidadArtefacto.NO_COMPROBABLE}.get(
                    e.estado, DisponibilidadArtefacto.DESCONOCIDA)

    @property
    def integridad_aportada(self):
        e = self.entrada_perfil.entrada.evidencia_local
        # INCONSISTENTE no identifica por sí solo qué comprobación falló.
        return EstadoIntegridad.VERIFICADA if e is not None and e.estado is EstadoLocal.INTEGRO else EstadoIntegridad.PENDIENTE

    @property
    def sha256_comprobado_aportado(self):
        e = self.entrada_perfil.entrada.evidencia_local
        return e.sha256_observado if self.integridad_aportada is EstadoIntegridad.VERIFICADA else None

    @property
    def size_bytes_comprobado_aportado(self):
        e = self.entrada_perfil.entrada.evidencia_local
        return e.size_bytes_observado if self.integridad_aportada is EstadoIntegridad.VERIFICADA else None

    @property
    def estado_conservacion(self):
        return V.DESCONOCIDO if self.generacion_conservacion_ref is None else V.DECLARADO

    @property
    def autoriza_operacion(self):
        return False

    def __bool__(self):
        raise TypeError("descriptor_no_es_permiso_ni_validacion")


@dataclass(frozen=True, slots=True)
class ProduccionArtefactos:
    """Relación explícita N→M: todos los orígenes contribuyen a todas las salidas.

    Si las salidas tienen entradas diferentes, se requieren operaciones distintas.
    Es procedencia declarada, nunca orden de ejecución o ejecución certificada.
    """

    operacion: ContextoOperacion = field(repr=False)
    metodo_id: str
    metodo_version: str
    entradas: tuple[ReferenciaArtefacto, ...]
    salidas: tuple[ReferenciaArtefacto, ...]
    ejecucion_id: str | None = None
    respaldo: Respaldo = field(default_factory=Respaldo, repr=False)
    restricciones_adicionales: tuple[RestriccionQA, ...] = ()
    diagnosticos: tuple[DiagnosticoAdaptacion, ...] = ()
    version_contrato: str = VERSION_ARTEFACTOS

    def __post_init__(self):
        _version(self.version_contrato)
        if type(self.operacion) is not ContextoOperacion or type(self.respaldo) is not Respaldo:
            raise TypeError("operacion_rc1_y_respaldo_requeridos")
        for v in (self.metodo_id, self.metodo_version):
            _texto(v)
        _texto(self.ejecucion_id, opcional=True)
        for refs in (self.entradas, self.salidas):
            _tupla(refs, ReferenciaArtefacto, 16)
            if not refs:
                raise ValueError("produccion_requiere_entradas_y_salidas")
        _tupla(self.diagnosticos, DiagnosticoAdaptacion, 64)
        combinar_restricciones(self.operacion.restricciones, self.restricciones_adicionales)

    @property
    def tipo_vinculo(self):
        return "produccion_declarada"

    @property
    def parametros(self):
        return self.operacion.parametros


@dataclass(frozen=True, slots=True)
class InventarioArtefactos:
    artefactos: tuple[DescriptorArtefacto, ...] = field(repr=False)
    producciones: tuple[ProduccionArtefactos, ...] = field(default=(), repr=False)
    composiciones: tuple[ComposicionOperaciones, ...] = field(default=(), repr=False)
    version_contrato: str = VERSION_ARTEFACTOS

    def __post_init__(self):
        _version(self.version_contrato)
        _tupla(self.artefactos, DescriptorArtefacto, 64)
        _tupla(self.producciones, ProduccionArtefactos, 32)
        _tupla(self.composiciones, ComposicionOperaciones, 16)
        if sum(len(c.operaciones) for c in self.composiciones) > 64:
            raise ValueError("cota_operaciones_rc3_excedida")
        if sum(len(p.entradas) * len(p.salidas) for p in self.producciones) > 1024:
            raise ValueError("cota_relaciones_linaje_excedida")


def _estado(ds):
    niveles = {d.nivel for d in ds}
    return E.INCOMPATIBLE if N.CONTRADICCION in niveles else E.PENDIENTE_DE_EVIDENCIA if N.FALTANTE in niveles else E.APTO_ESTRUCTURALMENTE


@dataclass(frozen=True, slots=True)
class InformeArtefacto:
    descriptor: DescriptorArtefacto = field(repr=False)
    diagnosticos: tuple[DiagnosticoAdaptacion, ...]
    restricciones_locales: tuple[RestriccionPropagada, ...]
    restricciones_heredadas: tuple[RestriccionPropagada, ...]

    @property
    def estado_estructural(self):
        return _estado(self.diagnosticos)

    @property
    def restricciones(self):
        return _unir_origenes(self.restricciones_locales, self.restricciones_heredadas)


def _unir_origenes(*grupos):
    combinar_restricciones(*(tuple(r.restriccion for r in g) for g in grupos))
    resultado = {}
    for grupo in grupos:
        for r in grupo:
            anterior = resultado.get(r.restriccion.codigo)
            origenes = () if anterior is None else anterior.origenes
            resultado[r.restriccion.codigo] = RestriccionPropagada(r.restriccion,
                tuple(dict.fromkeys(origenes + r.origenes)))
    return tuple(resultado.values())


@dataclass(frozen=True, slots=True)
class InformeLinaje:
    inventario: InventarioArtefactos = field(repr=False)
    artefactos: tuple[InformeArtefacto, ...]
    composiciones: tuple[InformeComposicion, ...] = field(repr=False)
    diagnosticos: tuple[DiagnosticoAdaptacion, ...]
    orden_linaje: tuple[ReferenciaArtefacto, ...]  # Inspección, no programación de tareas.
    version_inspector: str = field(default=VERSION_ARTEFACTOS, init=False)
    ejecucion_realizada: bool = field(default=False, init=False)
    comprobacion_fisica_realizada: bool = field(default=False, init=False)
    persistencia_realizada: bool = field(default=False, init=False)

    @property
    def estado_estructural(self):
        return _estado(self.diagnosticos + tuple(d for a in self.artefactos for d in a.diagnosticos))

    @property
    def autoriza_operacion(self):
        return False

    def __bool__(self):
        raise TypeError("linaje_coherente_no_es_permiso_ni_validacion")
