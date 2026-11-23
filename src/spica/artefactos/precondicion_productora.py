"""RC13: política externa de una precondición, sin admisión nativa RC3/RC7.

No despacha operaciones. RC11 prepara los cotejos usando los inspectores
predeterminados. No se modifica su decisión ni se vuelve a recorrer el grafo.
El testigo efímero solo protege el uso cooperativo, no un proceso hostil.
"""

from dataclasses import dataclass, field, fields

from ..contextos import EstadoOperacion as S
from ..contextos.modelos import _texto
from ..coordinacion.inspeccion import _unicos
from ..interoperabilidad.adaptadores import DiagnosticoAdaptacion as D, NivelDiagnostico as N
from ..interoperabilidad.modelos import EstadoAptitud as E
from .coordinacion import (
    SolicitudIntegracion, InformeIntegracion, VinculoEntradaRecuperada,
    inspeccionar_integracion,
)
from .dependencia_exportacion import (
    DecisionDependencia, PoliticaDependenciaExportacion,
    SolicitudDependenciaExportacion, DictamenDependenciaExportacion,
    dictaminar_dependencia_exportacion,
)

VERSION_PRECONDICION = "0.1.0"
PERFIL_PRECONDICION = "rc13.exportacion_json_qa0_a_consumo_local"
CLASE_CIERRE = "rc8.exportacion_json_qa0"
CONFIANZA_LOCAL = "proceso_cooperativo_captura_local"
_TESTIGO = object()


def _diag(codigo, nivel=N.CONTRADICCION):
    return D(codigo, "precondicion_productora_rc13", nivel)


@dataclass(frozen=True, slots=True)
class PoliticaPrecondicionProductora:
    """Selección explícita de una sola arista, entrada, perfil y confianza."""

    vinculo: PoliticaDependenciaExportacion = field(repr=False)
    entrada_consumidora_id: str
    perfil: str = PERFIL_PRECONDICION
    clase_cierre: str = CLASE_CIERRE
    confianza: str = CONFIANZA_LOCAL
    version_contrato: str = VERSION_PRECONDICION

    def __post_init__(self):
        if type(self.vinculo) is not PoliticaDependenciaExportacion:
            raise TypeError("politica_rc11_tipificada_requerida")
        self.vinculo.__post_init__()
        for v in (self.entrada_consumidora_id, self.perfil, self.clase_cierre,
                  self.confianza, self.version_contrato):
            _texto(v, maximo=512)

    @property
    def perfil_admitido(self):
        return ((self.perfil, self.clase_cierre, self.confianza, self.version_contrato)
                == (PERFIL_PRECONDICION, CLASE_CIERRE, CONFIANZA_LOCAL, VERSION_PRECONDICION)
                and self.vinculo.perfil_admitido)


@dataclass(frozen=True, slots=True)
class SolicitudPrecondicionProductora:
    dependencia: SolicitudDependenciaExportacion = field(repr=False)
    politica: PoliticaPrecondicionProductora | None = field(default=None, repr=False)
    integracion: SolicitudIntegracion | None = field(default=None, repr=False)

    def __post_init__(self):
        if type(self.dependencia) is not SolicitudDependenciaExportacion:
            raise TypeError("solicitud_rc11_tipificada_requerida")
        self.dependencia.__post_init__()
        if self.politica is not None:
            if type(self.politica) is not PoliticaPrecondicionProductora:
                raise TypeError("politica_rc13_tipificada_o_none_requerida")
            self.politica.__post_init__()
        if self.integracion is not None:
            if type(self.integracion) is not SolicitudIntegracion:
                raise TypeError("solicitud_rc7_tipificada_o_none_requerida")
            self.integracion.__post_init__()


@dataclass(frozen=True, slots=True)
class DictamenPrecondicionProductora:
    solicitud: SolicitudPrecondicionProductora = field(repr=False)
    dictamen_rc11: DictamenDependenciaExportacion = field(repr=False)
    integracion_rc7: InformeIntegracion | None = field(repr=False)
    diagnosticos: tuple[D, ...]
    version_inspector: str = field(default=VERSION_PRECONDICION, init=False)
    habilitacion_rc3_rc7: bool = field(default=False, init=False)
    ejecucion_automatica: bool = field(default=False, init=False)
    autenticidad_acreditada: bool = field(default=False, init=False)
    autoriza_operacion: bool = field(default=False, init=False)
    validacion_cientifica: bool = field(default=False, init=False)
    _contraste: tuple | None = field(default=None, init=False, repr=False, compare=False)

    @property
    def contraste_local_coherente(self):
        c = self._contraste
        return (type(c) is tuple and len(c) == 2 and c[0] is _TESTIGO
                and c[1] == _datos(self))

    @property
    def decision(self):
        ds, s = self.diagnosticos, self.solicitud
        if any(d.nivel is N.CONTRADICCION for d in ds):
            return DecisionDependencia.NO_SATISFECHA
        if (s.politica is None or not s.politica.perfil_admitido
                or s.dependencia.control_historico is not None):
            return DecisionDependencia.NO_ADMISIBLE
        if (not self.contraste_local_coherente
                or any(d.nivel is N.FALTANTE for d in ds)):
            return DecisionDependencia.PENDIENTE
        return DecisionDependencia.SATISFECHA

    @property
    def restricciones(self):
        # RC11 ya reúne orígenes y conflictos; no se duplican como otra prueba.
        return self.dictamen_rc11.restricciones

    @property
    def coordinacion_rc3(self):
        p = self.solicitud.dependencia.politica
        return next((c for c in self.dictamen_rc11.linaje.composiciones
                     if c.composicion.identificador == p.composicion_id), None)

    def __bool__(self):
        raise TypeError("precondicion_local_no_es_permiso_ni_admision_rc3_rc7")


def _datos(r):
    return tuple(getattr(r, f.name) for f in fields(r) if f.name != "_contraste")


def _vinculo_consumidor(s, i7, ds):
    p = s.dependencia.politica
    if s.politica.vinculo != p:
        ds.append(_diag("politica_rc13_y_solicitud_rc11_discrepantes"))
    c = next((c for c in p.inventario.composiciones if c.identificador == p.composicion_id), None)
    if c is None:
        return  # RC11 conserva la contradicción nativa.
    n = next((n for n in c.operaciones if n.contexto.operacion_id == p.dependencia.dependiente), None)
    a = next((a for a in p.inventario.artefactos if a.referencia == p.artefacto), None)
    if n is None or a is None:
        return
    entrada = a.entrada_perfil.entrada
    if (s.politica.entrada_consumidora_id != entrada.entrada_id
            or not any(e is entrada for e in n.contexto.entradas)):
        ds.append(_diag("entrada_consumidora_no_corresponde"))
    if n.contexto.estado not in (S.DECLARADA, S.PLANIFICADA):
        ds.append(_diag("dependiente_fuera_del_escenario_de_precondicion", N.FALTANTE))
    if s.integracion is not None:
        i = s.integracion
        esperado = VinculoEntradaRecuperada(n.contexto.operacion_id, entrada.entrada_id, p.artefacto)
        if (i.composicion != c or i.recuperacion.unidad is None
                or i.recuperacion.unidad.inventario != p.inventario
                or i.vinculos != (esperado,) or i.finalidad != p.finalidad):
            ds.append(_diag("integracion_rc7_ajena_a_precondicion"))
        if i7 is not None and i7.estado_estructural is E.INCOMPATIBLE:
            ds.append(_diag("integracion_rc7_contradictoria"))


def examinar_precondicion_productora(s: SolicitudPrecondicionProductora) -> DictamenPrecondicionProductora:
    """Cotejo externo explícito. Nunca ejecuta el productor o una operación RC3.

    RC11 puede releer RC5/RC10 si se solicitaron. RC7 se inspecciona con su API
    predeterminada y mantiene sus bloqueos; no constituye otra prueba de cierre.
    """
    if type(s) is not SolicitudPrecondicionProductora:
        raise TypeError("solicitud_precondicion_rc13_requerida")
    s.__post_init__()
    r11 = dictaminar_dependencia_exportacion(s.dependencia)
    i7 = None if s.integracion is None else inspeccionar_integracion(s.integracion)
    ds = list(r11.diagnosticos)
    if s.politica is None:
        ds.append(_diag("politica_rc13_no_seleccionada", N.INFORMACION))
    elif not s.politica.perfil_admitido:
        ds.append(_diag("perfil_cierre_o_confianza_no_admitidos", N.INFORMACION))
    else:
        # Todos los diagnósticos e informes nativos quedan intactos en r11/i7.
        _vinculo_consumidor(s, i7, ds)
        if s.dependencia.control_historico is not None:
            ds.append(_diag("historia_no_admitida_como_ejecucion_actual", N.INFORMACION))
        else:
            e, a = s.dependencia.evidencia, s.dependencia.admision
            if e is None or not e.captura_local_coherente:
                ds.append(_diag("captura_actual_rc8_requerida", N.FALTANTE))
            if r11.cierre is None or not r11.cierre.cierre_tecnico_comprobado:
                ds.append(_diag("cierre_local_rc8_insuficiente", N.FALTANTE))
            if a is None or not a.comprobacion_local_coherente or not a.admisible_para_consumo_tecnico:
                ds.append(_diag("admision_actual_rc9_requerida", N.FALTANTE))
    ds.append(_diag("dictamen_local_sin_habilitacion_rc3_rc7_ni_cierre_consumidor", N.INFORMACION))
    r = DictamenPrecondicionProductora(s, r11, i7, _unicos(ds))
    object.__setattr__(r, "_contraste", (_TESTIGO, _datos(r)))
    return r
