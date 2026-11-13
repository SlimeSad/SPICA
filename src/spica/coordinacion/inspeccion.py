"""Coordinación estructural acotada: inspecciona, no despacha ni ejecuta tareas."""

from dataclasses import replace
from threading import Event

from ..calidad.restricciones import TipoRestriccionQA
from ..contextos import EstadoOperacion as S, TipoOperacion, validar_relaciones
from ..calidad.reglas import seleccionar_reglas
from ..interoperabilidad.adaptadores import DiagnosticoAdaptacion as Diag, NivelDiagnostico as N
from ..interoperabilidad.modelos import EstadoAptitud as E
from ..interoperabilidad.perfiles import comparar_perfiles
from .modelos import (
    ComposicionOperaciones, InformeComposicion, InspeccionOperacion,
    RestriccionPropagada, fuentes_restricciones,
)
from ._presupuesto import medir_descriptores
from ._qa import revisar_cierre_qa, revisar_preparacion_qa


def _diag(codigo, campo="composicion", nivel=N.CONTRADICCION):
    return Diag(codigo, campo, nivel)


def _unicos(ds):
    return tuple(sorted(set(ds), key=lambda d: (d.campo, d.codigo, d.nivel.value)))


def _propagadas(fuentes):
    valores, origenes = {}, {}
    for rs, origen in fuentes:
        for r in rs:
            if r.codigo in valores and valores[r.codigo] != r:
                raise ValueError("restriccion_coordinacion_contradictoria")
            valores[r.codigo] = r
            origenes.setdefault(r.codigo, set()).add(origen)
    return tuple(RestriccionPropagada(valores[c], tuple(sorted(origenes[c]))) for c in sorted(valores))


def _grafo(c):
    ids = [n.contexto.operacion_id for n in c.operaciones]
    ds, anteriores = [], {i: set() for i in ids}
    if not ids:
        ds.append(_diag("composicion_sin_operaciones"))
    if len(ids) != len(set(ids)):
        ds.append(_diag("identidad_operacion_duplicada"))
    aristas = set()
    for d in c.dependencias:
        clave = d.predecesora, d.dependiente
        if clave in aristas:
            ds.append(_diag("dependencia_duplicada", d.dependiente))
        aristas.add(clave)
        if d.predecesora not in anteriores or d.dependiente not in anteriores:
            ds.append(_diag("dependencia_inexistente", d.dependiente))
        elif d.predecesora == d.dependiente:
            ds.append(_diag("dependencia_de_si_misma", d.dependiente))
        else:
            anteriores[d.dependiente].add(d.predecesora)
    if ds:
        return (), anteriores, 0, ds
    orden, profundidad = [], {}
    pendientes = set(ids)
    while pendientes:
        listos = sorted(i for i in pendientes if anteriores[i].issubset(profundidad))
        if not listos:
            return (), anteriores, 0, [_diag("dependencia_circular")]
        for i in listos:
            profundidad[i] = 1 + max((profundidad[p] for p in anteriores[i]), default=0)
            orden.append(i)
            pendientes.remove(i)
    return tuple(orden), anteriores, max(profundidad.values(), default=0), ds


def inspeccionar_composicion(composicion: ComposicionOperaciones, *,
                              cancelacion: Event | None = None) -> InformeComposicion:
    """Diagnóstico reproducible sin Event; con Event, cancelación cooperativa de este cotejo.

    Cierres QA son evidencia aportada coherente, no autenticación de ejecución.
    Ninguna etiqueta, orden o habilitación inicia operaciones o concede permiso.
    """
    if type(composicion) is not ComposicionOperaciones:
        raise TypeError("composicion_tipificada_requerida")
    if cancelacion is not None and type(cancelacion) is not Event:
        raise TypeError("event_estandar_o_none_requerido")
    c = composicion
    globales = []
    orden, anteriores, profundidad, ds = _grafo(c)
    globales.extend(ds)
    entradas = {}
    for n in c.operaciones:
        for e in n.contexto.entradas:
            clave = e.proyecto.contexto_id, e.entrada_id
            if clave in entradas and entradas[clave] is not e:
                globales.append(_diag("entrada_redefinida_o_instantanea_no_canonica", e.entrada_id))
            entradas[clave] = e
    if len(entradas) > 256:
        globales.append(_diag("cota_inventario_entradas_rc1_excedida"))
    else:
        globales.extend(validar_relaciones((c.proyecto,), tuple(entradas.values()), tuple(n.contexto for n in c.operaciones)))
    cuotas = tuple(sum(getattr(n.contexto.limites_qa, campo) for n in c.operaciones if n.contexto.limites_qa is not None)
                   for campo in ("max_registros", "max_resultados"))
    for excedida, codigo in (
            (len(c.operaciones) > c.limites.max_operaciones, "cuota_operaciones_excedida"),
            (len(c.dependencias) > c.limites.max_dependencias, "cuota_dependencias_excedida"),
            (profundidad > c.limites.max_profundidad, "profundidad_composicion_excedida"),
            (cuotas[0] > c.limites.max_registros_qa_declarados, "cuota_compuesta_registros_qa_excedida"),
            (cuotas[1] > c.limites.max_resultados_qa_declarados, "cuota_compuesta_resultados_qa_excedida")):
        if excedida:
            globales.append(_diag(codigo))
    visitas, texto, problema = medir_descriptores(c, cancelacion)
    cancelada = problema == "cancelacion_inspeccion_observada"
    if problema and not cancelada:
        globales.append(_diag(problema))
    comunes = ((c.proyecto.restricciones, "proyecto:" + c.proyecto.contexto_id),
               (c.restricciones_adicionales, "composicion:" + c.identificador))
    bases = {n.contexto.operacion_id: tuple(fuentes_restricciones(n)) for n in c.operaciones}
    todas = _propagadas((*comunes, *(f for n in c.operaciones for f in fuentes_restricciones(n))))
    ancestros = {}
    for identidad in orden:
        ancestros[identidad] = set(anteriores[identidad])
        for predecesora in anteriores[identidad]:
            ancestros[identidad].update(ancestros[predecesora])
    nodos = {n.contexto.operacion_id: n for n in c.operaciones}
    secuencia = [nodos[i] for i in orden] if orden else sorted(c.operaciones, key=lambda n: n.contexto.operacion_id)
    informes, por_id, consumos = [], {}, []
    for nodo in secuencia:
        o = nodo.contexto
        if cancelacion is not None and cancelacion.is_set():
            cancelada = True
        restricciones = (_propagadas((*comunes, *bases[o.operacion_id],
            *(f for p in sorted(ancestros[o.operacion_id]) for f in bases[p]))) if orden else todas)
        ds = list(globales)
        comparaciones, cierre_completo = [], False
        if cancelada:
            ds.append(_diag("cancelacion_inspeccion_observada", o.operacion_id, N.FALTANTE))
        elif not globales:
            ds.extend(o.diagnosticos)
            ds.extend(_diag(codigo, o.operacion_id, N.CONTRADICCION if contradiccion else N.FALTANTE)
                      for codigo, contradiccion in revisar_preparacion_qa(o))
            if o.tipo is TipoOperacion.QA_NIVEL0:
                try:
                    seleccionar_reglas(o.configuracion_qa)
                except (TypeError, ValueError):
                    ds.append(_diag("configuracion_qa_no_admitida", o.operacion_id))
            for e in o.entradas:
                ds.extend(d for d in e.diagnosticos if d.nivel is N.CONTRADICCION)
            for requisito in nodo.compatibilidades:
                if cancelacion is not None and cancelacion.is_set():
                    cancelada = True
                    break
                if (o.proposito != requisito.finalidad.descripcion
                        or any(not any(ep.entrada is e for e in o.entradas) for ep in (requisito.primero, requisito.segundo))):
                    ds.append(_diag("requisito_rc2_ajeno_a_operacion", o.operacion_id))
                    continue
                r = comparar_perfiles(requisito.primero, requisito.segundo, requisito.finalidad)
                comparaciones.append(r)
                ds.append(_diag("resultado_rc2_conservado_con_diagnosticos",
                    "rc2:" + o.operacion_id + ":" + requisito.finalidad.identificador,
                    N.INFORMACION if r.estado is E.APTO_ESTRUCTURALMENTE else
                    N.CONTRADICCION if r.estado is E.INCOMPATIBLE else N.FALTANTE))
                if nodo.usos_declarados is None or requisito.finalidad.identificador not in nodo.usos_declarados:
                    ds.append(_diag("finalidad_rc2_fuera_de_usos_declarados", o.operacion_id, N.FALTANTE))
            codigo, contradictorio, cierre_completo, contadores = revisar_cierre_qa(o, nodo.cierre_qa)
            if codigo:
                ds.append(_diag(codigo, o.operacion_id, N.CONTRADICCION if contradictorio else
                                N.INFORMACION if cierre_completo else N.FALTANTE))
            if contadores is not None:
                consumos.append((o.operacion_id, *contadores))
            if o.estado is S.CONCLUIDA and not cierre_completo:
                ds.append(_diag("conclusion_declarada_sin_cierre_tecnico_admitido", o.operacion_id, N.FALTANTE))
            elif o.estado in (S.PARCIAL, S.FALLIDA, S.CANCELADA, S.INICIADA):
                ds.append(_diag("estado_declarado_no_es_cierre_completo", o.operacion_id, N.FALTANTE))
            for rp in restricciones:
                r = rp.restriccion
                if r.tipo is TipoRestriccionQA.BLOQUEO_USO_DEL_RESULTADO:
                    if nodo.usos_declarados is None:
                        ds.append(_diag("aplicabilidad_restriccion_no_resuelta", r.codigo, N.FALTANTE))
                    elif set(r.operaciones).intersection(nodo.usos_declarados):
                        ds.append(_diag("restriccion_bloqueante_para_uso_declarado", r.codigo))
            for d in c.dependencias:
                if d.dependiente != o.operacion_id:
                    continue
                previa = por_id[d.predecesora]
                if any(ref not in previa.nodo.contexto.referencias_resultado for ref in d.referencias_resultado):
                    ds.append(_diag("referencia_requerida_no_declarada_por_predecesora", o.operacion_id))
                if previa.estado_estructural is not E.APTO_ESTRUCTURALMENTE or not previa.cierre_qa_coherente_completo:
                    ds.append(_diag("dependencia_sin_cierre_tecnico_compatible_aportado", d.predecesora, N.FALTANTE))
            ds.append(_diag("solo_inspeccion_declarativa_sin_ejecucion", o.operacion_id, N.INFORMACION))
        informe = InspeccionOperacion(nodo, _unicos(ds), restricciones, tuple(comparaciones), cierre_completo)
        informes.append(informe)
        por_id[o.operacion_id] = informe
    if cancelacion is not None and cancelacion.is_set():
        cancelada = True
    if cancelada:
        cancelado = _diag("cancelacion_inspeccion_observada", nivel=N.FALTANTE)
        globales.append(cancelado)
        informes = [replace(i, diagnosticos=_unicos((*i.diagnosticos, cancelado))) for i in informes]
    return InformeComposicion(c, tuple(informes), _unicos(globales), orden, todas,
        cuotas, tuple(consumos), visitas, texto, cancelada)
