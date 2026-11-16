"""RC7: cotejo puro de recuperación RC6 y composición RC3, sin ejecutar efectos."""

from dataclasses import dataclass, field, fields, replace
from datetime import datetime
from threading import Event

from ..adquisicion.readquisicion.modelos import EstadoLocal
from ..calidad.restricciones import TipoRestriccionQA
from ..contextos import TipoOperacion
from ..contextos.modelos import _texto
from ..coordinacion import ComposicionOperaciones, InformeComposicion, LimitesComposicion, RestriccionPropagada, inspeccionar_composicion
from ..coordinacion.modelos import DependenciaOperacion, estado_diagnosticos
from ..coordinacion.inspeccion import _unicos
from ..coordinacion._presupuesto import medir_descriptores
from ..interoperabilidad.adaptadores import DiagnosticoAdaptacion as D, NivelDiagnostico as N
from ..interoperabilidad.modelos import EstadoAptitud as E
from . import InformeArtefacto, InformeLinaje, ProduccionArtefactos, ReferenciaArtefacto, EstadoArtefacto, TipoArtefacto, inspeccionar_linaje
from .modelos import _unir_origenes
from .conservacion import (
    ComprobacionContenido, ControlGeneracion, RecuperacionGeneracion,
    UnidadConservacion, EstadoRecuperacion, VERSION_CONSERVACION,
)

VERSION_INTEGRACION = "0.1.0"


def _version(v):
    if type(v) is not str or v != VERSION_INTEGRACION:
        raise ValueError("version_integracion_rc7_no_admitida")


def _diag(codigo, campo="integracion_rc7", nivel=N.CONTRADICCION):
    return D(codigo, campo, nivel)


@dataclass(frozen=True, slots=True)
class VinculoEntradaRecuperada:
    operacion_id: str
    entrada_id: str
    artefacto: ReferenciaArtefacto
    version_contrato: str = VERSION_INTEGRACION

    def __post_init__(self):
        _version(self.version_contrato)
        _texto(self.operacion_id)
        _texto(self.entrada_id, maximo=128)
        if type(self.artefacto) is not ReferenciaArtefacto:
            raise TypeError("referencia_rc4_requerida")


@dataclass(frozen=True, slots=True)
class SolicitudIntegracion:
    recuperacion: RecuperacionGeneracion = field(repr=False)
    composicion: ComposicionOperaciones = field(repr=False)
    vinculos: tuple[VinculoEntradaRecuperada, ...]
    finalidad: str
    limites: LimitesComposicion = field(default_factory=LimitesComposicion)
    max_vinculos: int = 64
    version_contrato: str = VERSION_INTEGRACION

    def __post_init__(self):
        _version(self.version_contrato)
        _texto(self.finalidad)
        if (type(self.recuperacion) is not RecuperacionGeneracion
                or type(self.composicion) is not ComposicionOperaciones
                or type(self.limites) is not LimitesComposicion):
            raise TypeError("contratos_rc6_rc3_y_limites_requeridos")
        if type(self.max_vinculos) is not int or not 0 < self.max_vinculos <= 128:
            raise ValueError("cota_vinculos_rc7_invalida")
        if (type(self.vinculos) is not tuple or len(self.vinculos) > 128
                or any(type(v) is not VinculoEntradaRecuperada for v in self.vinculos)):
            raise TypeError("vinculos_rc7_tipificados_y_acotados")


@dataclass(frozen=True, slots=True)
class RelacionRecuperada:
    vinculo: VinculoEntradaRecuperada
    artefacto: InformeArtefacto | None = field(repr=False)
    comprobacion_en_recuperacion: ComprobacionContenido | None
    productora: ProduccionArtefactos | None = field(repr=False)
    diagnosticos: tuple[D, ...]

    @property
    def estado_estructural(self):
        return estado_diagnosticos(self.diagnosticos)


@dataclass(frozen=True, slots=True)
class InformeIntegracion:
    solicitud: SolicitudIntegracion = field(repr=False)
    linaje: InformeLinaje | None = field(repr=False)
    inspeccion_rc3: InformeComposicion | None = field(repr=False)
    coordinacion_integrada: InformeComposicion | None = field(repr=False)
    relaciones: tuple[RelacionRecuperada, ...]
    dependencias: tuple[tuple[DependenciaOperacion, E], ...]
    diagnosticos: tuple[D, ...]
    visitas_descriptores: int
    bytes_texto_descriptores: int | None
    cancelada: bool
    version_inspector: str = field(default=VERSION_INTEGRACION, init=False)
    ejecucion_realizada: bool = field(default=False, init=False)
    comprobacion_fisica_realizada: bool = field(default=False, init=False)

    @property
    def control(self):
        return self.solicitud.recuperacion.control

    @property
    def fecha_comprobacion_fisica_aportada(self):
        return self.solicitud.recuperacion.fecha_utc

    @property
    def estado_estructural(self):
        ds = self.diagnosticos
        if self.coordinacion_integrada is not None:
            ds += self.coordinacion_integrada.diagnosticos + tuple(
                d for i in self.coordinacion_integrada.operaciones for d in i.diagnosticos)
        return estado_diagnosticos(ds)

    @property
    def habilitadas_declarativamente(self):
        return () if self.cancelada or self.coordinacion_integrada is None else self.coordinacion_integrada.habilitadas_declarativamente

    @property
    def autoriza_operacion(self):
        return False

    def __bool__(self):
        raise TypeError("integracion_rc7_no_es_permiso_ni_certificacion")


def _unir(*grupos):
    """Unión RC4; ante conflicto conservar las variantes y bloquear su uso."""
    try:
        return _unir_origenes(*grupos), ()
    except ValueError:
        return tuple(dict.fromkeys(r for g in grupos for r in g)), (
            _diag("restricciones_recuperadas_no_unificables"),)


def _recuperacion(r):
    ds, linaje, por_ref = [], None, {}
    if r.version_contrato != VERSION_CONSERVACION:
        ds.append(_diag("version_recuperacion_no_admitida"))
    if (type(r.control) is not ControlGeneracion or type(r.fecha_utc) is not datetime
            or r.fecha_utc.utcoffset() is None or r.fecha_utc.utcoffset().total_seconds() != 0):
        ds.append(_diag("identidad_o_fecha_recuperacion_invalida"))
    elif type(r.estado) is not EstadoRecuperacion:
        ds.append(_diag("estado_recuperacion_no_admitido"))
    else:
        try:
            ControlGeneracion(r.control.generacion_id, r.control.manifiesto_sha256)
        except ValueError:
            ds.append(_diag("control_recuperacion_invalido"))
    if ds:
        return _unicos(ds), None, por_ref
    if r.estado is not EstadoRecuperacion.VERIFICADA:
        ds.append(_diag("generacion_no_verificada_en_alcance", nivel=N.CONTRADICCION
            if r.estado in (EstadoRecuperacion.CORRUPTA, EstadoRecuperacion.INCOMPATIBLE) else N.FALTANTE))
    elif r.diagnosticos:
        ds.append(_diag("recuperacion_verificada_con_diagnosticos_incoherentes"))
    if r.unidad is None:
        return tuple(ds) + (_diag("unidad_recuperada_no_disponible", nivel=N.FALTANTE),), None, por_ref
    u = r.unidad
    if type(u) is not UnidadConservacion or u.inventario.version_contrato != "0.1.0":
        return tuple(ds) + (_diag("unidad_recuperada_incompatible"),), None, por_ref
    linaje = inspeccionar_linaje(u.inventario)
    if linaje.estado_estructural is E.INCOMPATIBLE or linaje != u.linaje:
        ds.append(_diag("linaje_recuperado_contradictorio"))
    refs = {a.descriptor.referencia for a in linaje.artefactos}
    if (type(r.contenidos) is not tuple or any(type(x) is not ComprobacionContenido for x in r.contenidos)):
        return tuple(ds) + (_diag("comprobaciones_rc6_no_tipificadas"),), linaje, por_ref
    por_ref = {x.artefacto: x for x in r.contenidos}
    if len(por_ref) != len(r.contenidos) or set(por_ref) != refs:
        ds.append(_diag("inventario_comprobaciones_rc6_discrepante"))
    incluidos = {r5.solicitud.artefacto: (i, r5) for i, r5 in enumerate(u.incluidos)}
    for a in linaje.artefactos:
        ref = a.descriptor.referencia
        v = por_ref.get(ref)
        if v is None:
            continue
        incoherente = v.contenido_id != a.descriptor.contenido_id
        if ref in incluidos:
            i, r5 = incluidos[ref]
            incoherente |= v.relativa != f"datos-{i:03}.bin"
            if v.estado_actual is EstadoLocal.INTEGRO:
                incoherente |= (v.lectura_completa is not True or type(v.size_bytes) is not int
                    or v.size_bytes != r5.bytes_escritos or v.sha256_fisico != r5.sha256_recibido)
            elif r.estado is EstadoRecuperacion.VERIFICADA:
                incoherente = True
        else:
            incoherente |= (v.relativa is not None or v.size_bytes is not None
                or v.sha256_fisico is not None or v.lectura_completa is not False
                or v.estado_actual is not EstadoLocal.NO_DISPONIBLE)
        if incoherente:
            ds.append(_diag("comprobacion_rc6_incoherente", ref.object_id))
    return _unicos(ds), linaje, por_ref


def _relacion(v, s, linaje, comprobaciones):
    c = s.composicion
    ns = tuple(n for n in c.operaciones if n.contexto.operacion_id == v.operacion_id)
    ars = () if linaje is None else tuple(a for a in linaje.artefactos if a.descriptor.referencia == v.artefacto)
    a = ars[0] if len(ars) == 1 else None
    comp = comprobaciones.get(v.artefacto)
    ds, productora = [], None
    if len(ns) != 1:
        ds.append(_diag("operacion_vinculada_inexistente_o_ambigua", v.operacion_id))
    if a is None:
        ds.append(_diag("inventario_recuperado_no_disponible_para_vincular", v.entrada_id, N.FALTANTE)
            if linaje is None else _diag("artefacto_o_revision_vinculados_inexistentes", v.entrada_id))
    if a is not None:
        d = a.descriptor
        e = d.entrada_perfil.entrada
        productoras = tuple(p for p in linaje.inventario.producciones if d.referencia in p.salidas)
        productora = productoras[0] if len(productoras) == 1 else None
        if len(productoras) > 1:
            ds.append(_diag("productora_recuperada_ambigua", v.entrada_id))
        if e.proyecto != c.proyecto:
            ds.append(_diag("artefacto_recuperado_de_otro_proyecto", v.entrada_id))
        if len(ns) == 1:
            es = tuple(x for x in ns[0].contexto.entradas if x.entrada_id == v.entrada_id)
            if len(es) != 1:
                ds.append(_diag("entrada_vinculada_no_pertenece_a_operacion", v.entrada_id))
            elif es[0] != e:
                ds.append(_diag("snapshot_entrada_recuperada_discrepante", v.entrada_id))
            for req in ns[0].compatibilidades:
                for ep in (req.primero, req.segundo):
                    if ep.entrada.entrada_id == v.entrada_id and ep.perfil != d.entrada_perfil.perfil:
                        ds.append(_diag("perfil_recuperado_redefinido", v.entrada_id))
        if d.estado_logico is EstadoArtefacto.PARCIAL:
            ds.append(_diag("artefacto_recuperado_logicamente_parcial", v.entrada_id, N.FALTANTE))
        if d.tipo is not TipoArtefacto.ORIGINAL:
            ds.append(_diag("productor_no_qa_sin_cierre_ejecucion_admitido", v.entrada_id, N.FALTANTE))
    if comp is None or comp.relativa is None:
        ds.append(_diag("contenido_solo_referenciado_sin_comprobacion_actual", v.entrada_id, N.FALTANTE))
    elif comp.estado_actual is not EstadoLocal.INTEGRO or not comp.lectura_completa:
        ds.append(_diag("contenido_recuperado_no_integro", v.entrada_id,
            N.CONTRADICCION if comp.estado_actual is EstadoLocal.INCONSISTENTE else N.FALTANTE))
    else:
        ds.append(_diag("integridad_aportada_por_lectura_rc6_fechada", v.entrada_id, N.INFORMACION))
    return RelacionRecuperada(v, a, comp, productora, _unicos(ds))


def _dependencia(d, previa):
    if previa is None or any(x not in previa.nodo.contexto.referencias_resultado for x in d.referencias_resultado):
        return E.INCOMPATIBLE
    if previa.estado_estructural is E.INCOMPATIBLE:
        return E.INCOMPATIBLE
    return E.APTO_ESTRUCTURALMENTE if (previa.estado_estructural is E.APTO_ESTRUCTURALMENTE
        and previa.cierre_qa_coherente_completo) else E.PENDIENTE_DE_EVIDENCIA


def inspeccionar_integracion(solicitud, *, cancelacion=None):
    """Sin E/S. Reutiliza una comprobación RC6 a su fecha; no afirma vigencia nueva.

    No certifica que DTO coherentes provengan de un proceso confiable. Tampoco
    interpreta métodos, parámetros, finalidades o nombres de archivo como código.
    """
    if type(solicitud) is not SolicitudIntegracion:
        raise TypeError("solicitud_integracion_rc7_requerida")
    if cancelacion is not None and type(cancelacion) is not Event:
        raise TypeError("event_estandar_o_none_requerido")
    s, c = solicitud, solicitud.composicion
    _version(s.version_contrato)
    efectivos = LimitesComposicion(**{f.name: min(getattr(c.limites, f.name), getattr(s.limites, f.name))
        for f in fields(LimitesComposicion)})
    acotada = s if efectivos == s.limites else replace(s, limites=efectivos)
    visitas, texto, problema = medir_descriptores(acotada, cancelacion)
    ds = [] if problema is None else [_diag(problema, nivel=N.FALTANTE
        if problema == "cancelacion_inspeccion_observada" else N.CONTRADICCION)]
    if c.version_contrato != "0.1.0":
        ds.append(_diag("version_composicion_no_admitida"))
    for excedida, codigo in ((len(s.vinculos) > s.max_vinculos, "cota_vinculos_integracion_excedida"),
            (len(c.operaciones) > efectivos.max_operaciones, "cota_operaciones_integracion_excedida"),
            (len(c.dependencias) > efectivos.max_dependencias, "cota_dependencias_integracion_excedida")):
        if excedida:
            ds.append(_diag(codigo))
    if ds:
        return InformeIntegracion(s, None, None, None, (), (), _unicos(ds), visitas, texto,
            cancelacion is not None and cancelacion.is_set())
    base = inspeccionar_composicion(c if efectivos == c.limites else replace(c, limites=efectivos),
        cancelacion=cancelacion)
    adicionales, linaje, comprobaciones = _recuperacion(s.recuperacion)
    ds.extend(adicionales)
    if linaje is not None:
        proyectos = tuple(a.descriptor.entrada_perfil.entrada.proyecto for a in linaje.artefactos)
        if c.proyecto not in proyectos:
            ds.append(_diag("proyecto_de_composicion_no_corresponde_a_generacion"))
        for antigua in linaje.inventario.composiciones:
            if antigua.proyecto == c.proyecto and antigua.identificador == c.identificador and antigua != c:
                ds.append(_diag("composicion_recuperada_redefinida"))
    relaciones = tuple(_relacion(v, s, linaje, comprobaciones) for v in sorted(s.vinculos,
        key=lambda v: (v.operacion_id, v.entrada_id, v.artefacto.object_id, v.artefacto.revision)))
    ids = {n.contexto.operacion_id for n in c.operaciones}
    if any(r.vinculo.operacion_id not in ids for r in relaciones):
        ds.append(_diag("vinculo_fuera_de_composicion"))
    locales, politicas = {}, {}
    for i in base.operaciones:
        o = i.nodo.contexto
        rs = tuple(r for r in relaciones if r.vinculo.operacion_id == o.operacion_id)
        d = [x for r in rs for x in r.diagnosticos]
        claves = [r.vinculo.entrada_id for r in rs]
        if len(claves) != len(set(claves)):
            d.append(_diag("vinculo_entrada_recuperada_duplicado", o.operacion_id))
        if any(e.entrada_id not in claves for e in o.entradas):
            d.append(_diag("entrada_sin_vinculo_a_generacion", o.operacion_id, N.FALTANTE))
        if linaje is not None:
            historicas = tuple(n.contexto for co in linaje.inventario.composiciones
                if co.proyecto == c.proyecto for n in co.operaciones if n.contexto.operacion_id == o.operacion_id)
            historicas += tuple(p.operacion for p in linaje.inventario.producciones
                if p.operacion.proyecto == c.proyecto and p.operacion.operacion_id == o.operacion_id)
            if any(anterior != o for anterior in historicas):
                d.append(_diag("operacion_recuperada_redefinida", o.operacion_id))
            for antigua in linaje.inventario.composiciones:
                if antigua.proyecto != c.proyecto:
                    continue
                if any(dep.dependiente == o.operacion_id and dep.predecesora in ids
                        and dep not in c.dependencias for dep in antigua.dependencias):
                    d.append(_diag("dependencia_historica_omitida_o_redefinida", o.operacion_id))
        grupos = [i.restricciones]
        for r in rs:
            if r.artefacto is not None:
                grupos.append(tuple(RestriccionPropagada(p.restriccion,
                    tuple(dict.fromkeys(p.origenes + ("generacion:" + s.recuperacion.control.generacion_id,))))
                    for p in r.artefacto.restricciones))
        politicas[o.operacion_id], conflictos = _unir(*grupos)
        d.extend(conflictos)
        if o.tipo is TipoOperacion.QA_NIVEL0:
            if i.nodo.cierre_qa is None:
                d.append(_diag("rc6_no_aporta_cierre_qa_nativo", o.operacion_id, N.INFORMACION))
            else:
                proc = i.nodo.cierre_qa.informe.procedencia
                if any(r.comprobacion_en_recuperacion is not None
                        and (proc.sha256_referencia is None or proc.sha256_referencia != r.comprobacion_en_recuperacion.sha256_fisico)
                        for r in rs):
                    d.append(_diag("qa_sin_vinculo_hash_contenido_recuperado", o.operacion_id, N.FALTANTE))
                d.append(_diag("cierre_qa_adicional_no_conservado_por_rc6", o.operacion_id, N.INFORMACION))
        locales[o.operacion_id] = d
    # Único orden: el ya calculado por RC3. Se recorren sus aristas originales;
    # no se construye otro grafo ni se cambia el algoritmo de cierre nativo.
    vistas, por_id, deps = [], {}, []
    for i in base.operaciones:
        o = i.nodo.contexto
        d = list(i.diagnosticos) + ds + locales[o.operacion_id]
        grupos = [politicas[o.operacion_id]]
        if base.orden_precedencia:
            for dep in c.dependencias:
                if dep.dependiente != o.operacion_id:
                    continue
                previa = por_id.get(dep.predecesora)
                estado = _dependencia(dep, previa)
                deps.append((dep, estado))
                if previa is not None:
                    grupos.append(previa.restricciones)
                if estado is not E.APTO_ESTRUCTURALMENTE:
                    d.append(_diag("dependencia_sin_cotejo_recuperado_suficiente", dep.predecesora,
                        N.CONTRADICCION if estado is E.INCOMPATIBLE else N.FALTANTE))
        else:
            grupos.extend(politicas.values())
        restricciones, conflictos = _unir(*grupos)
        d.extend(conflictos)
        for rp in restricciones:
            p = rp.restriccion
            if p.tipo is TipoRestriccionQA.BLOQUEO_USO_DEL_RESULTADO:
                if i.nodo.usos_declarados is None:
                    d.append(_diag("aplicabilidad_restriccion_recuperada_pendiente", p.codigo, N.FALTANTE))
                elif set(p.operaciones).intersection(i.nodo.usos_declarados):
                    d.append(_diag("restriccion_recuperada_bloquea_uso", p.codigo))
        actual = replace(i, diagnosticos=_unicos(d), restricciones=restricciones)
        vistas.append(actual)
        por_id[o.operacion_id] = actual
    if not base.orden_precedencia:
        deps = [(d, E.INCOMPATIBLE) for d in c.dependencias]
    cancelada = base.cancelada or cancelacion is not None and cancelacion.is_set()
    if cancelada:
        cancelado = _diag("cancelacion_inspeccion_observada", nivel=N.FALTANTE)
        ds.append(cancelado)
        vistas = [replace(i, diagnosticos=_unicos(i.diagnosticos + (cancelado,))) for i in vistas]
    restricciones, conflictos = _unir(base.restricciones, *(i.restricciones for i in vistas))
    vista = replace(base, operaciones=tuple(vistas), diagnosticos=_unicos(base.diagnosticos + tuple(ds) + conflictos),
        restricciones=restricciones, cancelada=cancelada)
    # Un conflicto global de políticas tampoco permite habilitación local aparente.
    if conflictos:
        vista = replace(vista, operaciones=tuple(replace(i,
            diagnosticos=_unicos(i.diagnosticos + conflictos)) for i in vista.operaciones))
    if base.orden_precedencia:
        finales = {i.nodo.contexto.operacion_id: i for i in vista.operaciones}
        deps = [(d, _dependencia(d, finales.get(d.predecesora))) for d in c.dependencias]
    return InformeIntegracion(s, linaje, base, vista, relaciones, tuple(deps),
        _unicos(ds + list(conflictos)), visitas, texto, cancelada)


__all__ = ("VERSION_INTEGRACION", "VinculoEntradaRecuperada", "SolicitudIntegracion",
    "RelacionRecuperada", "InformeIntegracion", "inspeccionar_integracion")
