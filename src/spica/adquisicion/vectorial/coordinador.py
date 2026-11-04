"""Coordinación secuencial offline: conserva recibos acotados, no geometrías."""

from threading import Event

from .modelos import (
    ConsultaVector, EstadoCompletitud as EC, EstadoPagina as EP, EstrategiaPaginacion as ES,
    EvidenciaConjunto, LimitesVector, ReciboPagina, ResultadoVector, SolicitudPagina,
)
from .simulado import TransporteSintetico
from .validador import validar_featureset


def coordinar(consulta: ConsultaVector, transporte: TransporteSintetico, *,
              estrategia: ES = ES.OFFSET, tamano_pagina: int = 100,
              evidencia: EvidenciaConjunto | None = None,
              limites: LimitesVector | None = None,
              cancelacion: Event | None = None) -> ResultadoVector:
    """Las peticiones son declaraciones; el único transporte admitido es sintético.

    COMPLETA_COMPROBADA solo se refiere a la instantánea inventada y a la consulta
    exacta. Nunca acredita una instantánea institucional ni validez científica.
    """
    if type(consulta) is not ConsultaVector or type(transporte) is not TransporteSintetico:
        raise TypeError("Consulta y transporte exclusivamente sintético requeridos")
    if type(estrategia) is not ES or (limites is not None and type(limites) is not LimitesVector):
        raise TypeError("Estrategia y límites tipados requeridos")
    if evidencia is not None and type(evidencia) is not EvidenciaConjunto:
        raise TypeError("Evidencia tipada requerida")
    if cancelacion is not None and type(cancelacion) is not Event:
        raise TypeError("Cancelación tipada requerida")
    limites = limites if limites is not None else LimitesVector()
    if type(tamano_pagina) is not int or not 1 <= tamano_pagina <= limites.entidades_pagina:
        raise ValueError("Tamaño de página fuera de límites")
    if estrategia is ES.OBJECT_IDS and (evidencia is None or evidencia.object_ids is None):
        raise ValueError("Estrategia por IDs requiere identificadores documentados")
    if estrategia is ES.CONTEO_DOCUMENTADO and (evidencia is None or evidencia.total is None):
        raise ValueError("Estrategia por conteo requiere conteo documentado")
    recibos, vistos, hashes, respuestas = [], set(), set(), set()
    total_bytes, total_entidades, offset, indice_ids, ultimo_oid = 0, 0, 0, 0, None
    bytes_observados = 0
    auxiliares_recibos, diagnosticos = 0, []
    limitaciones = ["sin_validacion_topologica_o_cientifica", "solo_fuentes_sinteticas_sin_persistencia"]
    if evidencia is None or not evidencia.instantanea_consistente:
        limitaciones.append("sin_garantia_de_instantanea_consistente")
    ids = evidencia.object_ids if evidencia is not None else None
    # Cuotas de memoria lógicas conservadoras, verificadas ANTES de crear sets.
    # No equivalen a un límite de RSS del intérprete.
    base_aux = len(ids) * 128 if ids is not None else 0

    def terminar(e, *codigos):
        return ResultadoVector(consulta, evidencia, estrategia, e, tuple(recibos), total_entidades,
                               bytes_observados, total_bytes, tuple(diagnosticos) + codigos, tuple(limitaciones), limites)

    if cancelacion is not None and cancelacion.is_set():
        return terminar(EC.PARCIAL, "operacion_cancelada")
    if base_aux > limites.bytes_auxiliares or (ids is not None and len(ids) > limites.entidades_total):
        return terminar(EC.INCOMPLETA_POR_LIMITES, "limite_evidencia_ids")
    if evidencia is not None:
        if evidencia.huella_consulta != consulta.huella or evidencia.obtenida_utc < consulta.creada_utc:
            return terminar(EC.INCONSISTENTE, "evidencia_de_otra_consulta_o_anterior")
        if evidencia.ids_obtenidos_utc is not None and evidencia.ids_obtenidos_utc < consulta.creada_utc:
            return terminar(EC.INCONSISTENTE, "identificadores_anteriores_a_consulta")
        if ids is not None and evidencia.total is not None and len(ids) != evidencia.total:
            return terminar(EC.INCONSISTENTE, "conteo_e_identificadores_contradictorios")
        if evidencia.total is not None and evidencia.total > limites.entidades_total:
            return terminar(EC.INCOMPLETA_POR_LIMITES, "limite_conteo_documentado")
    esperados = frozenset(ids) if ids is not None else None
    total_remoto = evidencia.total if evidencia is not None else None
    instantanea = evidencia.instantanea_id if evidencia is not None else None
    if estrategia is ES.OBJECT_IDS and not ids:
        return terminar(EC.DESCONOCIDA, "ids_vacios_sin_peticion_ambigua")
    for numero in range(1, limites.max_paginas + 1):
        if cancelacion is not None and cancelacion.is_set():
            return terminar(EC.PARCIAL, "operacion_cancelada")
        parametros = dict(consulta.parametros)
        lote = ()
        if estrategia is ES.OBJECT_IDS:
            lote = ids[indice_ids:indice_ids + tamano_pagina]
            parametros["objectIds"] = ",".join(str(x) for x in lote)
        else:
            parametros.update(resultOffset=str(offset), resultRecordCount=str(tamano_pagina),
                              orderByFields=consulta.contrato.campo_oid + " ASC")
        if any(len(v) > 8192 for v in parametros.values()):
            return terminar(EC.INCOMPLETA_POR_LIMITES, "limite_parametros_pagina")
        coste_recibo = 4096 + 8 * sum(len(k) + len(v) for k, v in parametros.items())
        cuota = base_aux + (len(vistos) + tamano_pagina) * 128 + auxiliares_recibos + coste_recibo
        if cuota > limites.bytes_auxiliares:
            return terminar(EC.INCOMPLETA_POR_LIMITES, "limite_memoria_auxiliar")
        solicitud = SolicitudPagina(consulta.adquisicion_id, consulta.huella, numero, parametros)
        respuesta = transporte.recibir(solicitud)
        if respuesta is None:
            return terminar(EC.PARCIAL if total_entidades else EC.DESCONOCIDA, "fixture_agotada_sin_prueba_de_completitud")
        bytes_observados += len(respuesta.contenido)

        def sin_inspeccion():
            recibos.append(ReciboPagina(solicitud, respuesta.respuesta_id, respuesta.obtenida_utc,
                                        None, len(respuesta.contenido), 0, EP.NO_INSPECCIONADA,
                                        None, respuesta.solicitud))

        if respuesta.solicitud != solicitud:
            sin_inspeccion()
            return terminar(EC.INCONSISTENTE, "discontinuidad_de_solicitud")
        if (respuesta.obtenida_utc < consulta.creada_utc
                or recibos and respuesta.obtenida_utc < recibos[-1].obtenida_utc
                or evidencia is not None and respuesta.obtenida_utc < evidencia.obtenida_utc
                or evidencia is not None and evidencia.ids_obtenidos_utc is not None
                   and respuesta.obtenida_utc < evidencia.ids_obtenidos_utc):
            sin_inspeccion()
            return terminar(EC.INCONSISTENTE, "cronologia_de_evidencia_contradictoria")
        if total_bytes + len(respuesta.contenido) > limites.bytes_total:
            sin_inspeccion()
            return terminar(EC.INCOMPLETA_POR_LIMITES, "limite_bytes_total")
        pagina = validar_featureset(respuesta, consulta.contrato, limites=limites, cancelacion=cancelacion)
        total_bytes += pagina.bytes_recibidos
        recibos.append(ReciboPagina(solicitud, respuesta.respuesta_id, respuesta.obtenida_utc,
                                    pagina.sha256, pagina.bytes_recibidos, len(pagina.entidades),
                                    pagina.estado, pagina.exceeded_transfer_limit, respuesta.solicitud))
        auxiliares_recibos += coste_recibo
        if pagina.estado is not EP.VALIDA:
            ec = {EP.LIMITADA: EC.INCOMPLETA_POR_LIMITES, EP.CANCELADA: EC.PARCIAL,
                  EP.INTERRUMPIDA: EC.PARCIAL}.get(pagina.estado, EC.INCONSISTENTE)
            return terminar(ec, *pagina.diagnosticos)
        if respuesta.respuesta_id in respuestas or pagina.sha256 in hashes:
            return terminar(EC.INCONSISTENTE, "pagina_repetida")
        respuestas.add(respuesta.respuesta_id)
        hashes.add(pagina.sha256)
        if respuesta.instantanea_id is not None:
            if instantanea is not None and respuesta.instantanea_id != instantanea:
                return terminar(EC.INCONSISTENTE, "cambio_de_instantanea")
            instantanea = respuesta.instantanea_id
        if evidencia is not None and evidencia.instantanea_consistente and respuesta.instantanea_id != evidencia.instantanea_id:
            return terminar(EC.INCONSISTENTE, "instantanea_no_acreditada_en_pagina")
        if respuesta.total_observado is not None:
            if total_remoto is not None and total_remoto != respuesta.total_observado:
                return terminar(EC.INCONSISTENTE, "conteo_remoto_cambiante")
            total_remoto = respuesta.total_observado
        if esperados is not None and total_remoto is not None and len(esperados) != total_remoto:
            return terminar(EC.INCONSISTENTE, "conteo_e_identificadores_contradictorios")
        oids = tuple(e.object_id_observado for e in pagina.entidades)
        if any(x in vistos for x in oids):
            return terminar(EC.INCONSISTENTE, "oid_duplicado_entre_paginas")
        if estrategia is not ES.OBJECT_IDS:
            if tuple(sorted(oids)) != oids or oids and ultimo_oid is not None and oids[0] <= ultimo_oid:
                return terminar(EC.INCONSISTENTE, "ordenacion_inestable")
        elif set(oids) != set(lote):
            if set(oids) < set(lote) and pagina.exceeded_transfer_limit is True:
                return terminar(EC.INCOMPLETA_POR_LIMITES, "lote_object_ids_limitado_por_servidor_simulado")
            return terminar(EC.INCONSISTENTE, "lote_object_ids_incompleto_o_ajeno")
        elif pagina.exceeded_transfer_limit is True:
            return terminar(EC.INCONSISTENTE, "continuacion_con_lote_ids_agotado")
        if esperados is not None and any(x not in esperados for x in oids):
            return terminar(EC.INCONSISTENTE, "identificadores_remotos_ajenos")
        if estrategia is not ES.OBJECT_IDS and len(oids) > tamano_pagina:
            return terminar(EC.INCONSISTENTE, "pagina_supera_tamano_solicitado")
        if total_entidades + len(oids) > limites.entidades_total:
            return terminar(EC.INCOMPLETA_POR_LIMITES, "limite_entidades_total")
        vistos.update(oids)
        total_entidades += len(oids)
        ultimo_oid = oids[-1] if oids else ultimo_oid
        if total_remoto is not None and total_entidades > total_remoto:
            return terminar(EC.INCONSISTENTE, "entidades_superan_conteo")
        coinciden = esperados is not None and vistos == esperados
        exceso = pagina.exceeded_transfer_limit
        if not oids and exceso is True:
            return terminar(EC.INCONSISTENTE, "pagina_vacia_con_continuacion")
        if coinciden and exceso is True:
            return terminar(EC.INCONSISTENTE, "continuacion_con_identificadores_agotados")
        if coinciden and evidencia.instantanea_consistente and exceso is False:
            return terminar(EC.COMPLETA_COMPROBADA, "ids_exactos_y_evidencia_sintetica_coherentes")
        if estrategia is ES.OBJECT_IDS:
            indice_ids += len(lote)
            if indice_ids >= len(ids):
                return terminar(EC.DESCONOCIDA, "ids_recibidos_sin_prueba_suficiente_de_instantanea_o_fin")
        elif exceso is False:
            if esperados is not None and not coinciden or total_remoto is not None and total_entidades < total_remoto:
                return terminar(EC.INCONSISTENTE, "fin_con_entidades_documentadas_ausentes")
            return terminar(EC.DESCONOCIDA, "fin_de_pagina_no_demuestra_conjunto_remoto")
        elif not oids:
            return terminar(EC.PARCIAL if total_entidades else EC.DESCONOCIDA, "pagina_vacia_sin_prueba_de_fin")
        elif total_remoto is not None and total_entidades == total_remoto:
            if exceso is True:
                return terminar(EC.INCONSISTENTE, "continuacion_con_conteo_agotado")
            return terminar(EC.DESCONOCIDA, "conteo_coincidente_no_demuestra_identificadores")
        else:
            if len(oids) < tamano_pagina:
                diagnosticos.append("pagina_corta_no_demuestra_fin")
            # Avanzar por entidades observadas evita saltos tras página corta.
            offset += len(oids)
        # Liberar geometrías y cuerpo antes de solicitar otra página.
        del pagina, respuesta, sin_inspeccion
    return terminar(EC.INCOMPLETA_POR_LIMITES, "limite_paginas")
