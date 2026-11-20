"""RC11: dictamen externo de una arista de exportación, sin habilitar RC3/RC7.

No constituye otro coordinador. Inspecciona una arista RC3 ya declarada y
reutiliza RC4/RC8/RC9/RC10. Solo las API físicas nativas pueden releer TEMP.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from ..adquisicion.readquisicion.modelos import EstadoLocal
from ..calidad.restricciones import RestriccionQA, TipoRestriccionQA as TR
from ..contextos import EstadoOperacion as S, TipoOperacion, combinar_restricciones
from ..contextos.modelos import _texto
from ..coordinacion import DependenciaOperacion, RestriccionPropagada
from ..coordinacion.inspeccion import _unicos
from ..coordinacion.modelos import estado_diagnosticos
from ..interoperabilidad.adaptadores import DiagnosticoAdaptacion as D, NivelDiagnostico as N
from ..interoperabilidad.modelos import EstadoAptitud as E
from . import InventarioArtefactos, ReferenciaArtefacto, InformeLinaje, inspeccionar_linaje
from .coordinacion import _unir
from .cierre_exportacion import (
    PRODUCTOR, VERSION_CIERRE, USO_EXPORTAR, EvidenciaExportacion,
    InformeCierreExportacion, inspeccionar_cierre_exportacion,
)
from .admision_exportacion import CONSUMIDOR, VERSION_ADMISION, USO_CONSUMIR, InformeAdmisionExportacion, _fisica
from .conservacion import EstadoRecuperacion
from .conservacion_evidencias import ControlEvidencias, RecuperacionEvidencias, recuperar_evidencias
from .materializacion import InformeVerificacion

VERSION_DEPENDENCIA = "0.1.0"
# Se conservan íntegros en InformeLinaje. Son límites explícitos del contrato,
# no pruebas de contradicción de las correspondencias técnicas RC11.
_LIMITES_NATIVOS = frozenset((
    "estado_declarado_no_es_cierre_completo",
    "conclusion_declarada_sin_cierre_tecnico_admitido",
    "dependencia_sin_cierre_tecnico_compatible_aportado",
    "composicion_con_condiciones_no_satisfechas",
    "sin_comprobacion_fisica_aportada",
    "relacion_sin_evidencia_ejecucion_suficiente",
    "productora_sin_conclusion_declarada",
    "antecesor_pendiente_de_evidencia",
))


class DecisionDependencia(Enum):
    """Decisión de admisión; distinta de la aptitud estructural reutilizada."""

    SATISFECHA = "satisfecha_dentro_del_alcance_tecnico"
    NO_SATISFECHA = "no_satisfecha"
    PENDIENTE = "pendiente_de_evidencia"
    NO_ADMISIBLE = "no_admisible_por_politica"


def _diag(codigo, nivel=N.CONTRADICCION):
    return D(codigo, "dependencia_exportacion_rc11", nivel)


@dataclass(frozen=True, slots=True)
class PoliticaDependenciaExportacion:
    inventario: InventarioArtefactos = field(repr=False)
    composicion_id: str
    dependencia: DependenciaOperacion
    artefacto: ReferenciaArtefacto
    entrada_resultado_id: str
    contenido_id: str
    productor_id: str = PRODUCTOR
    version_productor: str = VERSION_CIERRE
    consumidor_id: str = CONSUMIDOR
    version_consumidor: str = VERSION_ADMISION
    finalidad: str = USO_CONSUMIR
    exigir_integridad_fisica: bool = False
    exigir_autenticidad_independiente: bool = False
    exigir_externos_disponibles: bool = False
    restricciones_adicionales: tuple[RestriccionQA, ...] = ()
    version_contrato: str = VERSION_DEPENDENCIA

    def __post_init__(self):
        if self.version_contrato != VERSION_DEPENDENCIA:
            raise ValueError("version_dependencia_rc11_no_admitida")
        for valor, tipo in ((self.inventario, InventarioArtefactos),
                (self.dependencia, DependenciaOperacion), (self.artefacto, ReferenciaArtefacto)):
            if type(valor) is not tipo:
                raise TypeError("contratos_rc3_rc4_tipificados_requeridos")
            valor.__post_init__()
        for valor in (self.composicion_id, self.entrada_resultado_id, self.contenido_id,
                self.productor_id, self.version_productor, self.consumidor_id,
                self.version_consumidor, self.finalidad):
            _texto(valor, maximo=512)
        for valor in (self.exigir_integridad_fisica, self.exigir_autenticidad_independiente,
                self.exigir_externos_disponibles):
            if type(valor) is not bool:
                raise TypeError("exigencia_booleana_requerida")
        combinar_restricciones(self.restricciones_adicionales)

    @property
    def perfil_admitido(self):
        return (self.productor_id, self.version_productor, self.consumidor_id,
            self.version_consumidor, self.finalidad) == (
                PRODUCTOR, VERSION_CIERRE, CONSUMIDOR, VERSION_ADMISION, USO_CONSUMIR)


@dataclass(frozen=True, slots=True)
class SolicitudDependenciaExportacion:
    politica: PoliticaDependenciaExportacion = field(repr=False)
    evidencia: EvidenciaExportacion | None = field(default=None, repr=False)
    admision: InformeAdmisionExportacion | None = field(default=None, repr=False)
    raiz_historica: Path | None = field(default=None, repr=False)
    control_historico: ControlEvidencias | None = None

    def __post_init__(self):
        if type(self.politica) is not PoliticaDependenciaExportacion:
            raise TypeError("politica_dependencia_tipificada_requerida")
        self.politica.__post_init__()
        for valor, tipo in ((self.evidencia, EvidenciaExportacion), (self.admision, InformeAdmisionExportacion),
                (self.control_historico, ControlEvidencias)):
            if valor is not None and type(valor) is not tipo:
                raise TypeError("evidencia_dependencia_tipificada_requerida")
        if (self.raiz_historica is None) != (self.control_historico is None):
            raise ValueError("raiz_y_control_historicos_inseparables")
        if self.raiz_historica is not None:
            if not isinstance(self.raiz_historica, Path):
                raise TypeError("raiz_path_requerida")
            if self.evidencia is not None or self.admision is not None:
                raise ValueError("fuentes_local_e_historica_no_combinables")


@dataclass(frozen=True, slots=True)
class DictamenDependenciaExportacion:
    solicitud: SolicitudDependenciaExportacion = field(repr=False)
    linaje: InformeLinaje = field(repr=False)
    cierre: InformeCierreExportacion | None = field(repr=False)
    admision: InformeAdmisionExportacion | None = field(repr=False)
    recuperacion: RecuperacionEvidencias | None = field(repr=False)
    verificacion_actual: InformeVerificacion | None = field(repr=False)
    restricciones: tuple[RestriccionPropagada, ...]
    diagnosticos: tuple[D, ...]
    version_inspector: str = field(default=VERSION_DEPENDENCIA, init=False)
    habilitacion_rc3_rc7: bool = field(default=False, init=False)
    autoriza_operacion: bool = field(default=False, init=False)
    ejecucion_automatica: bool = field(default=False, init=False)
    autenticidad_acreditada: bool = field(default=False, init=False)
    validacion_cientifica: bool = field(default=False, init=False)

    @property
    def estado_correspondencia(self):
        return estado_diagnosticos(self.diagnosticos)

    @property
    def decision(self):
        if self.estado_correspondencia is E.INCOMPATIBLE:
            return DecisionDependencia.NO_SATISFECHA
        if self.estado_correspondencia is E.PENDIENTE_DE_EVIDENCIA:
            return DecisionDependencia.PENDIENTE
        # No existe una clase de cierre no QA admitida por RC3/RC7 actuales.
        # Ningún DTO positivo, parámetro o hecho histórico abre esa barrera.
        return DecisionDependencia.NO_ADMISIBLE

    @property
    def satisfecha(self):
        return self.decision is DecisionDependencia.SATISFECHA

    @property
    def restricciones_nuevas(self):
        return tuple(r for r in self.restricciones if "politica_rc11" in r.origenes)

    @property
    def restricciones_heredadas(self):
        return tuple(r for r in self.restricciones if any(o != "politica_rc11" for o in r.origenes))

    @property
    def restricciones_bloqueantes(self):
        return tuple(r for r in self.restricciones if r.restriccion.tipo is TR.BLOQUEO_USO_DEL_RESULTADO
            and set(r.restriccion.operaciones).intersection((USO_EXPORTAR, self.solicitud.politica.finalidad)))

    def __bool__(self):
        raise TypeError("dictamen_rc11_no_es_permiso_ni_cierre_rc3")


def _correspondencias(p, linaje, e, a, ds):
    """Vínculos explícitos; las comprobaciones internas siguen en RC8/RC9."""
    comps = [c for c in p.inventario.composiciones if c.identificador == p.composicion_id]
    salidas = [d for d in p.inventario.artefactos if d.referencia == p.artefacto]
    if len(comps) != 1 or len(salidas) != 1:
        ds.append(_diag("composicion_o_artefacto_no_univoco"))
        return
    comp, salida = comps[0], salidas[0]
    nodos = {n.contexto.operacion_id: n for n in comp.operaciones}
    prod, dep = nodos.get(p.dependencia.predecesora), nodos.get(p.dependencia.dependiente)
    if (comp.dependencias.count(p.dependencia) != 1 or prod is None or dep is None):
        ds.append(_diag("arista_no_corresponde_a_composicion"))
        return
    entrada = salida.entrada_perfil.entrada
    if (entrada.proyecto is not comp.proyecto or salida.contenido_id != p.contenido_id
            or p.dependencia.referencias_resultado != (entrada.entrada_id,)
            or not any(x is entrada for x in dep.contexto.entradas)
            or prod.contexto.tipo is not TipoOperacion.DESCRIPCION_ESTRUCTURAL
            or dep.contexto.tipo is not TipoOperacion.DESCRIPCION_ESTRUCTURAL):
        ds.append(_diag("vinculo_operacion_entrada_salida_incompatible"))
    for n, uso in ((prod, USO_EXPORTAR), (dep, p.finalidad)):
        if n.usos_declarados is None:
            ds.append(_diag("aplicabilidad_de_uso_no_declarada", N.FALTANTE))
        elif uso not in n.usos_declarados:
            ds.append(_diag("finalidad_fuera_de_operacion_declarada"))
    if e is not None:
        s = e.solicitud
        if (s.inventario != p.inventario or s.composicion_id != p.composicion_id
                or s.operacion_id != prod.contexto.operacion_id or s.salida != p.artefacto
                or s.entrada_qa.referencia_resultado != p.entrada_resultado_id
                or s.entrada_qa.operacion.proyecto != comp.proyecto):
            ds.append(_diag("evidencia_rc8_ajena_a_arista"))
    if a is not None:
        s = a.solicitud
        if (s.evidencia is not e or s.proyecto != comp.proyecto
                or s.operacion_productora_id != prod.contexto.operacion_id
                or s.entrada_resultado_id != p.entrada_resultado_id
                or s.artefacto != p.artefacto or s.contenido_id != p.contenido_id
                or (s.consumidor_id, s.version_consumidor, s.finalidad) != (
                    p.consumidor_id, p.version_consumidor, p.finalidad)):
            ds.append(_diag("admision_rc9_ajena_a_arista"))
    # Conserva los informes completos; solo separa límites nativos conocidos.
    nativos = (*linaje.diagnosticos, *(d for x in linaje.artefactos for d in x.diagnosticos),
        *(d for c in linaje.composiciones for x in c.operaciones for d in x.diagnosticos))
    ds.extend(d for d in nativos if d.nivel is not N.INFORMACION and d.codigo not in _LIMITES_NATIVOS)


def dictaminar_dependencia_exportacion(s: SolicitudDependenciaExportacion) -> DictamenDependenciaExportacion:
    """Sin despacho de operaciones, escritura, red ni promoción de historia.

    RC10 relee solo su generación TEMP mediante su API. RC5, si se exige,
    verifica de nuevo la salida local y no acepta rutas libres del llamador.
    """
    if type(s) is not SolicitudDependenciaExportacion:
        raise TypeError("solicitud_dependencia_rc11_requerida")
    s.__post_init__()
    p = s.politica
    linaje = inspeccionar_linaje(p.inventario)
    ds, grupos = [], []
    historica, actual = None, None
    e, a, cierre = s.evidencia, s.admision, None
    if not p.perfil_admitido:
        ds.append(_diag("perfil_de_politica_no_admitido", N.INFORMACION))
    elif s.control_historico is not None:
        historica = recuperar_evidencias(s.raiz_historica, s.control_historico)
        if not historica.recuperada_en_alcance:
            nivel = N.CONTRADICCION if historica.generacion.estado in (
                EstadoRecuperacion.CORRUPTA, EstadoRecuperacion.INCOMPATIBLE) else N.FALTANTE
            ds.append(_diag("expediente_historico_no_recuperable", nivel))
        else:
            ex = historica.expediente
            cierre, a = ex.cierre_rc8, ex.admision_rc9
            e = None if cierre is None else cierre.evidencia
            ds.append(_diag("historia_rc10_no_es_captura_actual", N.INFORMACION))
            if not (ex.hechos.cierre_rc8_comprobado and ex.hechos.admision_rc9_comprobada):
                nivel = N.CONTRADICCION if E.INCOMPATIBLE in (
                    ex.hechos.estado_rc8, ex.hechos.estado_rc9) else N.FALTANTE
                ds.append(_diag("historia_sin_cierre_y_admision_comprobados", nivel))
            if p.exigir_externos_disponibles and historica.externos_actuales:
                ds.append(_diag("referencias_externas_sin_comprobacion_actual", N.FALTANTE))
            grupos.append(tuple(RestriccionPropagada(r, ("expediente_rc10",)) for r in ex.restricciones))
    if s.control_historico is None:
        if e is not None:
            cierre = inspeccionar_cierre_exportacion(e)
            ds.extend(cierre.diagnosticos)
        if a is not None:
            ds.extend(a.diagnosticos)
            if not a.comprobacion_local_coherente:
                ds.append(_diag("admision_rc9_sin_comprobacion_local", N.FALTANTE))
    _correspondencias(p, linaje, e, a, ds)
    if e is not None and e.operacion_observada is not None and e.operacion_observada.estado in (
            S.PARCIAL, S.FALLIDA, S.CANCELADA):
        ds.append(_diag("ejecucion_observada_no_completada"))
    if p.exigir_externos_disponibles and s.control_historico is None:
        # Ni RC8 ni RC9 comprueban físicamente las entradas externas del grafo.
        ds.append(_diag("referencias_externas_sin_comprobacion_actual", N.FALTANTE))
    if e is None or cierre is None:
        ds.append(_diag("evidencia_rc8_no_disponible", N.FALTANTE))
    if a is None:
        ds.append(_diag("admision_rc9_no_disponible", N.FALTANTE))
    if cierre is not None:
        grupos.append(tuple(RestriccionPropagada(r, ("cierre_rc8",)) for r in cierre.restricciones))
    if a is not None:
        grupos.append(tuple(RestriccionPropagada(r, ("admision_rc9",)) for r in a.restricciones))
    grupos.extend(x.restricciones for c in linaje.composiciones for x in c.operaciones)
    grupos.extend(x.restricciones for x in linaje.artefactos)
    grupos.append(tuple(RestriccionPropagada(r, ("politica_rc11",)) for r in p.restricciones_adicionales))
    restricciones, conflictos = _unir(*grupos)
    ds.extend(conflictos)
    for rp in restricciones:
        r = rp.restriccion
        if r.tipo is TR.BLOQUEO_USO_DEL_RESULTADO and set(r.operaciones).intersection((USO_EXPORTAR, p.finalidad)):
            ds.append(_diag("restriccion_bloqueante_para_dependencia"))
    exigir_fisica = p.exigir_integridad_fisica or (a is not None and a.solicitud.exigir_integridad_fisica)
    if exigir_fisica:
        if historica is not None or a is None or a.solicitud.materializacion is None:
            ds.append(_diag("integridad_actual_de_salida_no_disponible", N.FALTANTE))
        elif p.perfil_admitido and estado_diagnosticos(ds) is E.APTO_ESTRUCTURALMENTE:
            # Misma política física RC9; no duplicar asociación ni lectura RC5.
            actual = _fisica(a.solicitud, ds)
            if actual is not None:
                ds.extend(actual.diagnosticos)
                if actual.estado_local in (EstadoLocal.INCONSISTENTE, EstadoLocal.AUSENTE):
                    ds.append(_diag("integridad_actual_contradictoria"))
    if p.exigir_autenticidad_independiente:
        ds.append(_diag("autenticidad_independiente_no_acreditada", N.FALTANTE))
    ds.append(_diag("cierre_noqa_no_admitido_por_rc3_rc7", N.INFORMACION))
    return DictamenDependenciaExportacion(s, linaje, cierre, a, historica, actual,
        restricciones, _unicos(ds))
