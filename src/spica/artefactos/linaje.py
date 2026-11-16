"""Cotejo puro de inventarios explícitos, sin E/S ni ejecución de productores."""

from ..adquisicion.catalogo.modelos import EstadoVerificacion as V
from ..adquisicion.nucleo.modelos import EstadoIntegridad
from ..calidad.restricciones import TipoRestriccionQA
from ..contextos import EstadoOperacion as S, TipoOperacion, validar_relaciones
from ..coordinacion import RestriccionPropagada, inspeccionar_composicion
from ..interoperabilidad.adaptadores import DiagnosticoAdaptacion as D, NivelDiagnostico as N
from ..interoperabilidad.modelos import EstadoAptitud as E
from .modelos import (
    EstadoArtefacto as L, InformeArtefacto, InformeLinaje,
    InventarioArtefactos, TipoArtefacto as T, _unir_origenes,
)


def _diag(codigo, nivel=N.CONTRADICCION):
    # Códigos fijos: no interpolar rutas, parámetros, URLs o mensajes externos.
    return D(codigo, "linaje", nivel)


def _unicos(ds):
    return tuple(dict.fromkeys(ds))


def _politicas(rs, origen):
    return tuple(RestriccionPropagada(r, (origen,)) for r in rs)


def _clave_operacion(o):
    return o.proyecto.contexto_id, o.operacion_id


def inspeccionar_linaje(inventario: InventarioArtefactos) -> InformeLinaje:
    """Valida pertenencia, estados, contenido, procedencia y restricciones.

    Inspecciona RC3 mediante su API; no invoca lectores, motores, red o SQLite.
    Evidencia VERIFICADO es aportada, no autenticada. Ningún orden inicia tareas.
    """
    if type(inventario) is not InventarioArtefactos:
        raise TypeError("inventario_artefactos_requerido")
    globales, por_ref, locales, propios = [], {}, {}, {}
    proyectos, entradas, operaciones = {}, {}, {}

    def contexto(e):
        p = e.proyecto
        previo = proyectos.setdefault(p.contexto_id, p)
        if previo is not p:
            globales.append(_diag("contexto_proyecto_no_canonico"))
        clave = p.contexto_id, e.entrada_id
        previa = entradas.setdefault(clave, e)
        if previa is not e:
            globales.append(_diag("entrada_redefinida_o_revision_no_distinguida"))

    contenidos, hashes, perfiles, tipos_objeto = {}, {}, {}, {}
    for a in inventario.artefactos:
        ref, e, perfil = a.referencia, a.entrada_perfil.entrada, a.entrada_perfil.perfil
        if ref in por_ref:
            globales.append(_diag("identidad_revision_artefacto_duplicada"))
        por_ref[ref] = a
        anterior_tipo = tipos_objeto.setdefault(ref.object_id, a.tipo)
        if anterior_tipo is not a.tipo:
            globales.append(_diag("identidad_artefacto_con_tipo_distinto"))
        contexto(e)
        ds = list(a.diagnosticos + e.diagnosticos)
        if a.estado_logico is L.PARCIAL:
            ds.append(_diag("artefacto_parcial_no_es_final", N.FALTANTE))
        if a.contenido_id is None:
            ds.append(_diag("identidad_contenido_desconocida", N.FALTANTE))
        if a.integridad_aportada is not EstadoIntegridad.VERIFICADA:
            ds.append(_diag("sin_comprobacion_fisica_aportada", N.FALTANTE))
        if a.generacion_conservacion_ref is not None:
            ds.append(_diag("generacion_historica_no_comprobada", N.FALTANTE))
        if a.tipo is T.ORIGINAL and a.estado_logico is L.FINAL_DECLARADO and a.integridad_aportada is not EstadoIntegridad.VERIFICADA:
            ds.append(_diag("original_final_sin_evidencia_de_preservacion"))
        clave_perfil = perfil.identificador, perfil.version
        if clave_perfil in perfiles and perfiles[clave_perfil] != perfil:
            globales.append(_diag("perfil_version_con_definiciones_distintas"))
        perfiles[clave_perfil] = perfil
        # Ni el ID de contenido ni el hash fusionan proyectos/recursos.
        huella = e.sha256_declarado if e.sha256_declarado is not None else a.sha256_comprobado_aportado
        tamano = e.size_bytes_declarado if e.size_bytes_declarado is not None else a.size_bytes_comprobado_aportado
        if a.contenido_id is not None:
            previo_hash, previo_tamano = contenidos.get(a.contenido_id, (None, None))
            if (previo_hash is not None and huella is not None and previo_hash != huella
                    or previo_tamano is not None and tamano is not None and previo_tamano != tamano):
                globales.append(_diag("identidad_contenido_con_metadatos_contradictorios"))
            contenidos[a.contenido_id] = (previo_hash if previo_hash is not None else huella,
                                        previo_tamano if previo_tamano is not None else tamano)
        if huella is not None and tamano is not None:
            if huella in hashes and hashes[huella] != tamano:
                globales.append(_diag("hash_declarado_con_tamanos_contradictorios"))
            hashes[huella] = tamano
        locales[ref] = _politicas(a.restricciones, "descriptor:" + str(len(locales)))
        propios[ref] = ds

    informes_rc3 = tuple(inspeccionar_composicion(c) for c in inventario.composiciones)
    nodos = {}
    for numero, r in enumerate(informes_rc3):
        globales.extend(r.diagnosticos)
        for i in r.operaciones:
            o = i.nodo.contexto
            clave = _clave_operacion(o)
            if clave in nodos:
                globales.append(_diag("operacion_en_composiciones_duplicada"))
            nodos[clave] = r, i, numero
            operaciones[clave] = o
            for e in o.entradas:
                contexto(e)
        if r.estado_estructural is not E.APTO_ESTRUCTURALMENTE:
            globales.append(_diag("composicion_con_condiciones_no_satisfechas",
                N.CONTRADICCION if r.estado_estructural is E.INCOMPATIBLE else N.FALTANTE))

    productoras, por_operacion, ejecuciones = {}, {}, set()
    aristas = {ref: set() for ref in por_ref}
    aportes = {ref: () for ref in por_ref}
    for numero, p in enumerate(inventario.producciones):
        o, clave = p.operacion, _clave_operacion(p.operacion)
        if clave in por_operacion:
            globales.append(_diag("produccion_de_operacion_duplicada"))
        por_operacion[clave] = p
        anterior = operaciones.setdefault(clave, o)
        if anterior is not o:
            globales.append(_diag("productora_con_instantanea_operacion_distinta"))
        if p.ejecucion_id is not None:
            if p.ejecucion_id in ejecuciones:
                globales.append(_diag("ejecucion_atribuida_a_operaciones_distintas"))
            ejecuciones.add(p.ejecucion_id)
        for e in o.entradas:
            contexto(e)
        ds = list(p.diagnosticos + o.diagnosticos)
        if o.tipo is not TipoOperacion.DESCRIPCION_ESTRUCTURAL:
            ds.append(_diag("resultado_qa_no_es_dataset_derivado"))
        if len(set(p.entradas)) != len(p.entradas) or len(set(p.salidas)) != len(p.salidas):
            ds.append(_diag("referencia_produccion_repetida"))
        nativo = nodos.get(clave)
        politicas = _politicas(o.restricciones, "operacion:" + str(numero))
        politicas = _unir_origenes(politicas, _politicas(p.restricciones_adicionales, "relacion:" + str(numero)))
        if nativo is None:
            ds.append(_diag("productora_sin_referencia_rc3", N.FALTANTE if not inventario.composiciones else N.CONTRADICCION))
        else:
            r, i, _ = nativo
            if i.nodo.contexto is not o:
                ds.append(_diag("productora_no_es_instantanea_rc3"))
            ds.extend(i.diagnosticos)
            politicas = _unir_origenes(politicas, i.restricciones,
                _politicas(r.composicion.restricciones_adicionales, "composicion:" + str(nativo[2])))
        if p.respaldo.estado is not V.VERIFICADO or p.ejecucion_id is None:
            ds.append(_diag("relacion_sin_evidencia_ejecucion_suficiente", N.FALTANTE))
        else:
            ds.append(_diag("respaldo_aportado_no_autenticado", N.INFORMACION))
        if o.estado is not S.CONCLUIDA:
            ds.append(_diag("productora_sin_conclusion_declarada", N.FALTANTE))
        esperadas = {id(e) for e in o.entradas}
        encontradas = {id(por_ref[ref].entrada_perfil.entrada) for ref in p.entradas if ref in por_ref}
        if esperadas != encontradas:
            ds.append(_diag("entradas_linaje_no_corresponden_a_operacion"))
        for ref in p.entradas + p.salidas:
            a = por_ref.get(ref)
            if a is None:
                globales.append(_diag("referencia_artefacto_inexistente"))
            elif a.entrada_perfil.entrada.proyecto is not o.proyecto:
                ds.append(_diag("relacion_atribuida_a_otro_proyecto_o_contexto"))
        for destino in p.salidas:
            if destino in productoras:
                globales.append(_diag("artefacto_con_productoras_contradictorias"))
            productoras[destino] = p
            if destino not in por_ref:
                continue
            a = por_ref[destino]
            propios[destino].extend(ds)
            if a.tipo is T.ORIGINAL:
                propios[destino].append(_diag("original_no_puede_ser_salida_preparada"))
            if a.estado_logico is L.FINAL_DECLARADO and (o.estado is not S.CONCLUIDA
                    or p.respaldo.estado is not V.VERIFICADO or p.ejecucion_id is None):
                propios[destino].append(_diag("salida_final_sin_soporte_declarativo_suficiente"))
            if o.estado in (S.PARCIAL, S.FALLIDA, S.CANCELADA) and a.estado_logico is not L.PARCIAL:
                propios[destino].append(_diag("salida_de_operacion_no_completa_debe_ser_parcial"))
            if o.estado in (S.PARCIAL, S.CONCLUIDA, S.FALLIDA, S.CANCELADA, S.INICIADA):
                if a.entrada_perfil.entrada.entrada_id not in o.referencias_resultado:
                    propios[destino].append(_diag("salida_no_declarada_en_referencias_resultado"))
            aportes[destino] = _unir_origenes(aportes[destino], politicas)
            for origen in p.entradas:
                if origen == destino:
                    globales.append(_diag("autoarista_linaje"))
                if origen in aristas:
                    aristas[origen].add(destino)

        # Los errores sobreviven aunque ninguna salida exista en el inventario.
        globales.extend(d for d in ds if d.nivel is N.CONTRADICCION)

    if len(entradas) > 256 or len(operaciones) > 256:
        globales.append(_diag("inventario_supera_cota_relaciones_rc1"))
    else:
        globales.extend(validar_relaciones(tuple(proyectos.values()), tuple(entradas.values()), tuple(operaciones.values())))

    for ref, a in por_ref.items():
        if a.tipo is not T.ORIGINAL and ref not in productoras:
            propios[ref].append(_diag("artefacto_sin_operacion_productora"))
        productora = productoras.get(ref)
        if productora is not None:
            for origen in productora.entradas:
                previa = productoras.get(origen)
                if previa is None:
                    continue
                c1, c2 = nodos.get(_clave_operacion(previa.operacion)), nodos.get(_clave_operacion(productora.operacion))
                if c1 is None or c2 is None:
                    continue
                if c1[0] is not c2[0] or not any(d.predecesora == previa.operacion.operacion_id
                        and d.dependiente == productora.operacion.operacion_id for d in c2[0].composicion.dependencias):
                    propios[ref].append(_diag("linaje_sin_dependencia_rc3_explicita"))

    # DAG de artefactos, no DAG de operaciones: mismas entradas/salidas explícitas,
    # ninguna coincidencia de nombre, SHA o revisión crea una relación.
    grados = {ref: 0 for ref in por_ref}
    for destinos in aristas.values():
        for ref in destinos:
            if ref in grados:
                grados[ref] += 1
    orden, pendientes = [], set(grados)
    while pendientes:
        capa = sorted((r for r in pendientes if grados[r] == 0), key=lambda r: (r.object_id, r.revision))
        if not capa:
            globales.append(_diag("ciclo_linaje"))
            orden = []
            break
        orden.extend(capa)
        pendientes.difference_update(capa)
        for ref in capa:
            for destino in aristas[ref]:
                if destino in grados:
                    grados[destino] -= 1

    heredadas = dict(aportes)
    if orden:
        for ref in orden:
            for destino in sorted(aristas[ref], key=lambda r: (r.object_id, r.revision)):
                if destino in heredadas:
                    heredadas[destino] = _unir_origenes(heredadas[destino], locales[ref], heredadas[ref])
                    niveles = {d.nivel for d in propios[ref]}
                    if N.CONTRADICCION in niveles:
                        propios[destino].append(_diag("antecesor_con_coherencia_contradictoria"))
                    elif N.FALTANTE in niveles:
                        propios[destino].append(_diag("antecesor_pendiente_de_evidencia", N.FALTANTE))
    else:
        # Con ciclo no hay clausura válida. Conservar todas las políticas de forma
        # conservadora y diagnosticar; nunca elegir una interpretación permisiva.
        todas = _unir_origenes(*locales.values(), *aportes.values())
        heredadas = {ref: todas for ref in por_ref}

    resultados = []
    for ref, a in por_ref.items():
        ds = propios[ref]
        total = _unir_origenes(locales[ref], heredadas[ref])
        p = productoras.get(ref)
        nativo = None if p is None else nodos.get(_clave_operacion(p.operacion))
        usos = None if nativo is None else nativo[1].nodo.usos_declarados
        for rp in total:
            r = rp.restriccion
            if r.tipo is TipoRestriccionQA.BLOQUEO_USO_DEL_RESULTADO:
                if usos is None:
                    ds.append(_diag("aplicabilidad_restriccion_desconocida", N.FALTANTE))
                elif set(r.operaciones).intersection(usos):
                    ds.append(_diag("restriccion_heredada_impide_uso_declarado"))
        resultados.append(InformeArtefacto(a, _unicos(ds), locales[ref], heredadas[ref]))
    return InformeLinaje(inventario, tuple(resultados), informes_rc3, _unicos(globales), tuple(orden))
