"""RC14: entradas explícitas de coordinación para la única precondición RC13.

Prepara evidencia fuera del recorrido, conserva informes predeterminados y
reutiliza los recorridos RC3/RC7. No ejecuta operaciones ni concede permisos.
"""

from dataclasses import dataclass, field, fields
from threading import Event

from ..contextos.modelos import _texto
from ..coordinacion import ComposicionOperaciones, DependenciaOperacion, InformeComposicion, RestriccionPropagada
from ..coordinacion.inspeccion import _inspeccionar_composicion, _unicos
from ..coordinacion.modelos import estado_diagnosticos
from ..coordinacion._precondicion_rc14 import _crear_aporte
from ..interoperabilidad.adaptadores import DiagnosticoAdaptacion as D, NivelDiagnostico as N
from ..interoperabilidad.modelos import EstadoAptitud as E
from .coordinacion import SolicitudIntegracion, InformeIntegracion, _inspeccionar_integracion, _unir
from .dependencia_exportacion import DecisionDependencia as DD
from .precondicion_productora import (
    SolicitudPrecondicionProductora, DictamenPrecondicionProductora,
    examinar_precondicion_productora,
)

VERSION_RC14 = "0.1.0"
PERFIL_RC14 = "rc14.precondicion_exportacion_json_qa0"
_TESTIGO = object()


def _diag(codigo, nivel=N.CONTRADICCION):
    return D(codigo, "coordinacion_precondicion_rc14", nivel)


@dataclass(frozen=True, slots=True)
class SeleccionPrecondicionRC14:
    precondicion: SolicitudPrecondicionProductora = field(repr=False)
    perfil: str = PERFIL_RC14
    version_contrato: str = VERSION_RC14

    def __post_init__(self):
        if type(self.precondicion) is not SolicitudPrecondicionProductora:
            raise TypeError("solicitud_rc13_requerida_no_dictamen_aportado")
        self.precondicion.__post_init__()
        _texto(self.perfil, maximo=128)
        _texto(self.version_contrato, maximo=128)

    @property
    def perfil_admitido(self):
        return (self.perfil, self.version_contrato) == (PERFIL_RC14, VERSION_RC14)


@dataclass(frozen=True, slots=True)
class InformeCoordinacionRC14:
    seleccion: SeleccionPrecondicionRC14 | None = field(repr=False)
    precondicion: DictamenPrecondicionProductora | None = field(repr=False)
    predeterminado: InformeComposicion | InformeIntegracion = field(repr=False)
    opcional: InformeComposicion | InformeIntegracion = field(repr=False)
    dependencias: tuple[tuple[DependenciaOperacion, E], ...]
    restricciones: tuple[RestriccionPropagada, ...]
    diagnosticos: tuple[D, ...]
    version_inspector: str = field(default=VERSION_RC14, init=False)
    ejecucion_realizada: bool = field(default=False, init=False)
    autoriza_operacion: bool = field(default=False, init=False)
    autenticidad_acreditada: bool = field(default=False, init=False)
    validacion_cientifica: bool = field(default=False, init=False)
    _contraste: tuple | None = field(default=None, init=False, repr=False, compare=False)

    @property
    def contraste_local_coherente(self):
        c = self._contraste
        return (type(c) is tuple and len(c) == 2 and c[0] is _TESTIGO and c[1] == _datos(self))

    @property
    def decision_precondicion(self):
        if not self.contraste_local_coherente:
            return DD.PENDIENTE
        if self.seleccion is None or not self.seleccion.perfil_admitido:
            return DD.NO_ADMISIBLE
        return DD.PENDIENTE if self.precondicion is None else self.precondicion.decision

    @property
    def arista_admitida_por_rc14(self):
        if (self.decision_precondicion is not DD.SATISFECHA
                or any(d.nivel is N.CONTRADICCION for d in self.diagnosticos)):
            return False
        elegida = self.seleccion.precondicion.dependencia.politica.dependencia
        return any(d == elegida and estado is E.APTO_ESTRUCTURALMENTE for d, estado in self.dependencias)

    @property
    def habilitadas_declarativamente(self):
        return self.opcional.habilitadas_declarativamente if self.contraste_local_coherente else ()

    @property
    def estado_estructural(self):
        if not self.contraste_local_coherente:
            return E.PENDIENTE_DE_EVIDENCIA
        nivel = (N.CONTRADICCION if self.opcional.estado_estructural is E.INCOMPATIBLE else
                 N.FALTANTE if self.opcional.estado_estructural is E.PENDIENTE_DE_EVIDENCIA else N.INFORMACION)
        return estado_diagnosticos((*self.diagnosticos, _diag("estado_del_recorrido_conservado", nivel)))

    def __bool__(self):
        raise TypeError("coordinacion_rc14_no_es_permiso_ni_ejecucion")


def _datos(r):
    return tuple(getattr(r, f.name) for f in fields(r) if f.name != "_contraste")


def _validar(seleccion, cancelacion):
    if seleccion is not None:
        if type(seleccion) is not SeleccionPrecondicionRC14:
            raise TypeError("seleccion_rc14_tipificada_o_none_requerida")
        seleccion.__post_init__()
    if cancelacion is not None and type(cancelacion) is not Event:
        raise TypeError("event_estandar_o_none_requerido")


def _preparar(c, seleccion, cancelacion, integracion=None):
    if seleccion is None:
        return None, None, (_diag("rc14_no_seleccionado", N.INFORMACION),)
    if not seleccion.perfil_admitido:
        return None, None, (_diag("perfil_rc14_no_admitido", N.FALTANTE),)
    if cancelacion is not None and cancelacion.is_set():
        return None, None, (_diag("cancelacion_antes_del_cotejo_rc13", N.FALTANTE),)
    s = seleccion.precondicion
    r = examinar_precondicion_productora(s)
    p, ds = s.dependencia.politica, []
    esperada = next((x for x in p.inventario.composiciones if x.identificador == p.composicion_id), None)
    if c != esperada:
        ds.append(_diag("composicion_o_proyecto_ajenos_a_precondicion"))
    if integracion is not None:
        u = integracion.recuperacion.unidad
        if u is None or u.inventario != p.inventario:
            ds.append(_diag("inventario_recuperado_ajeno_a_precondicion"))
        if s.integracion is not None and s.integracion != integracion:
            ds.append(_diag("solicitud_rc7_distinta_de_la_cotejada_por_rc13"))
    if not r.contraste_local_coherente:
        ds.append(_diag("dictamen_rc13_sin_cotejo_local", N.FALTANTE))
    nivel = (N.INFORMACION if r.decision is DD.SATISFECHA else
             N.CONTRADICCION if r.decision is DD.NO_SATISFECHA else N.FALTANTE)
    ds.append(_diag("decision_rc13_" + r.decision.name.lower(), nivel))
    aporte = None
    if r.decision is DD.SATISFECHA and r.contraste_local_coherente and estado_diagnosticos(ds) is E.APTO_ESTRUCTURALMENTE:
        aporte = _crear_aporte(c, p.dependencia, seleccion.precondicion.politica.entrada_consumidora_id,
            (p.artefacto.object_id, p.artefacto.revision), r.restricciones)
    return aporte, r, _unicos(ds)


def _restricciones(informe):
    if type(informe) is InformeComposicion:
        return informe.restricciones
    vista = informe.coordinacion_integrada
    return () if vista is None else vista.restricciones


def _informe(seleccion, r, base, opcional, deps, ds):
    grupos = (_restricciones(base), _restricciones(opcional), () if r is None else r.restricciones)
    restricciones, conflictos = _unir(*grupos)
    informe = InformeCoordinacionRC14(seleccion, r, base, opcional, deps,
        restricciones, _unicos((*ds, *conflictos)))
    object.__setattr__(informe, "_contraste", (_TESTIGO, _datos(informe)))
    return informe


def inspeccionar_composicion_rc14(composicion: ComposicionOperaciones, *,
        seleccion: SeleccionPrecondicionRC14 | None = None,
        cancelacion: Event | None = None) -> InformeCoordinacionRC14:
    """Mismo recorrido RC3; selección lateral, sin cambiar la API predeterminada."""
    if type(composicion) is not ComposicionOperaciones:
        raise TypeError("composicion_tipificada_requerida")
    _validar(seleccion, cancelacion)
    aporte, r, ds = _preparar(composicion, seleccion, cancelacion)
    base, deps = _inspeccionar_composicion(composicion, cancelacion=cancelacion)
    opcional = base
    if aporte is not None:
        opcional, deps = _inspeccionar_composicion(composicion, cancelacion=cancelacion, aporte=aporte)
    return _informe(seleccion, r, base, opcional, deps, ds)


def inspeccionar_integracion_rc14(solicitud: SolicitudIntegracion, *,
        seleccion: SeleccionPrecondicionRC14 | None = None,
        cancelacion: Event | None = None) -> InformeCoordinacionRC14:
    """Mismo recorrido RC7; la precondición no suple contenido físico ausente."""
    if type(solicitud) is not SolicitudIntegracion:
        raise TypeError("solicitud_integracion_rc7_requerida")
    solicitud.__post_init__()
    _validar(seleccion, cancelacion)
    aporte, r, ds = _preparar(solicitud.composicion, seleccion, cancelacion, solicitud)
    base = _inspeccionar_integracion(solicitud, cancelacion=cancelacion)
    opcional = base if aporte is None else _inspeccionar_integracion(solicitud, cancelacion=cancelacion, aporte=aporte)
    return _informe(seleccion, r, base, opcional, opcional.dependencias, ds)
