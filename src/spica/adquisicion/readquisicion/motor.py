"""Decisión pura: no recibe clientes, almacenes, conexiones, rutas ni callbacks."""

from ..almacenamiento.modelos import EstadoIncorporacion
from ..catalogo.modelos import MecanismoAdquisicion
from ..nucleo import EstadoDescarga
from ..nucleo.temporal import instante_utc
from .modelos import (
    Decision, EstadoActualizacion, EstadoLocal, ModoConsulta, RelacionActualizacion,
    ResultadoDecision, SolicitudDecision, UsoPrevisto,
)


def decidir_readquisicion(solicitud: SolicitudDecision) -> ResultadoDecision:
    """Recomienda según evidencia aportada; nunca certifica actualidad ni permisos."""
    if type(solicitud) is not SolicitudDecision:
        raise TypeError("Solicitud de decisión tipada requerida")
    s = solicitud
    faltantes, notas = set(), set()
    limites = {"recomendacion_no_autoriza_operaciones", "motor_no_comprueba_archivos",
               "vigencia_remota_no_acreditada", "declaraciones_no_acreditan_autenticidad",
               "sin_bloqueo_ni_instantanea_concurrente"}
    estado = EstadoActualizacion.DESCONOCIDO
    historicos = tuple(a for a in s.antecedentes if a.identidad == s.identidad)
    remotas = tuple(e for e in s.actualizaciones if e.identidad == s.identidad and e.mecanismo is s.mecanismo)
    if len(historicos) != len(s.antecedentes) or len(remotas) != len(s.actualizaciones):
        limites.add("antecedentes_o_evidencias_fuera_de_alcance_no_aplicados")
    if not s.historial_completo:
        faltantes.add("historial_exhaustivo_del_recurso")
    if s.mecanismo is MecanismoAdquisicion.MANUAL:
        limites.add("entrega_manual_sin_comprobacion_remota")
    if any(a.indicios_http for a in historicos) or any(e.indicios_http for e in remotas):
        limites.add("url_nombre_y_longitud_no_prueban_igualdad")
        limites.add("etag_no_es_sha256_ni_prueba_de_vigencia")
        limites.add("last_modified_no_es_fecha_documental_ni_de_observacion")
    restricciones = s.restricciones

    def resultado(decision, causa, candidatos=()):
        return ResultadoDecision(s, decision, tuple(sorted(notas | {causa})), tuple(sorted(faltantes)),
            tuple(sorted(limites)), estado, tuple(sorted(a.activo_id for a in candidatos)))

    def permiso(campo):
        if restricciones is None:
            return None
        valor = getattr(restricciones, campo)
        # Un permiso positivo sin evidencia no se transforma en autorización.
        return None if valor is True and restricciones.procedencia.evidencia is None else valor

    def nueva(decision, causa):
        faltantes.update(("autorizacion_operativa_independiente", "comprobar_mecanismo_y_acceso_actuales"))
        if permiso("permite_adquirir") is False:
            return resultado(Decision.BLOQUEADA, "nueva_adquisicion_prohibida")
        if permiso("permite_adquirir") is None:
            faltantes.add("permiso_de_adquisicion_documentado_para_este_alcance")
        return resultado(decision, causa)

    if restricciones is not None and (restricciones.identidad != s.identidad
                                       or restricciones.mecanismo is not s.mecanismo):
        faltantes.add("restricciones_del_proyecto_recurso_y_mecanismo_solicitados")
        return resultado(Decision.REVISION_MANUAL, "restricciones_de_otro_alcance")

    fechas = [a.procedencia.revisada_utc for a in historicos]
    for a in historicos:
        fechas.extend(v for v in (a.fecha_adquisicion, a.fecha_incorporacion_raw, a.local.comprobada_utc) if v is not None)
        if a.local.procedencia:
            fechas.append(a.local.procedencia.revisada_utc)
        if a.local.comprobada_utc is not None and any(a.local.comprobada_utc < f
                for f in (a.fecha_adquisicion, a.fecha_incorporacion_raw) if f is not None):
            return resultado(Decision.REVISION_MANUAL, "comprobacion_anterior_a_adquisicion")
    fechas.extend(e.procedencia.revisada_utc for e in remotas)
    if restricciones:
        fechas.append(restricciones.procedencia.revisada_utc)
    if any(instante_utc(f) > s.evaluada_utc for f in fechas):
        return resultado(Decision.REVISION_MANUAL, "evidencia_posterior_a_evaluacion")

    campo_uso = {UsoPrevisto.PUBLICACION: "permite_publicar", UsoPrevisto.REDISTRIBUCION: "permite_redistribuir"}.get(s.uso)
    if campo_uso:
        if permiso(campo_uso) is False:
            return resultado(Decision.BLOQUEADA, "uso_solicitado_prohibido")
        if permiso(campo_uso) is None:
            faltantes.add("permiso_documentado_del_uso_solicitado")
            return resultado(Decision.REVISION_MANUAL, "permiso_de_uso_desconocido")
    if restricciones and restricciones.condiciones:
        return resultado(Decision.REVISION_MANUAL, "condiciones_de_acceso_requieren_revision")

    adquisiciones = [a.adquisicion_id for a in historicos if a.adquisicion_id is not None]
    activos = [a.activo_id for a in historicos if a.activo_id is not None]
    if len(adquisiciones) != len(set(adquisiciones)) or len(activos) != len(set(activos)):
        return resultado(Decision.REVISION_MANUAL, "identidades_historicas_duplicadas_o_ambiguas")

    candidatos = []
    incompletos = False
    for a in historicos:
        if a.local.estado is not EstadoLocal.DESCONOCIDO and a.local.activo_id != a.activo_id:
            return resultado(Decision.REVISION_MANUAL, "comprobacion_local_de_otro_activo")
        incompleto = (a.estado_descarga in (EstadoDescarga.PENDIENTE, EstadoDescarga.PARCIAL, EstadoDescarga.FALLIDA)
                      or a.estado_raw in (EstadoIncorporacion.PREPARADA, EstadoIncorporacion.VERIFICADA,
                                          EstadoIncorporacion.FALLIDA) or a.interrumpida)
        if a.interrumpida:
            notas.add("antecedente_interrumpido_preservado")
        if a.estado_descarga is EstadoDescarga.PARCIAL:
            notas.add("transferencia_parcial_no_completa")
        if a.estado_descarga is EstadoDescarga.FALLIDA or a.estado_raw is EstadoIncorporacion.FALLIDA:
            notas.add("adquisicion_fallida_preservada")
        if incompleto and a.estado_raw is EstadoIncorporacion.INCORPORADA:
            return resultado(Decision.REVISION_MANUAL, "estados_de_adquisicion_contradictorios")
        if a.estado_raw is EstadoIncorporacion.INCONSISTENTE or a.local.estado in (
                EstadoLocal.INCONSISTENTE, EstadoLocal.AUSENTE):
            return resultado(Decision.REVISION_MANUAL, "problema_local_documentado_sin_reparacion_automatica")
        incompletos |= incompleto
        if a.local.estado is not EstadoLocal.INTEGRO:
            faltantes.add("comprobacion_fisica_local_disponible")
            continue
        if a.sha256_catalogado is None or a.size_bytes_catalogado is None:
            faltantes.add("tamano_y_sha256_catalogados")
            continue
        if (a.local.sha256_observado, a.local.size_bytes_observado) != (a.sha256_catalogado, a.size_bytes_catalogado):
            return resultado(Decision.REVISION_MANUAL, "evidencia_local_contradice_catalogo")
        edad_maxima = s.politica.antiguedad_maxima_local
        if edad_maxima is not None and s.evaluada_utc - a.local.comprobada_utc > edad_maxima:
            faltantes.add("renovar_comprobacion_local_segun_politica")
            continue
        if not incompleto and a.estado_raw is EstadoIncorporacion.INCORPORADA and a.activo_id is not None:
            candidatos.append(a)
        else:
            faltantes.add("incorporacion_raw_completa")

    versiones_nuevas = set()
    versiones_base = set()
    relaciones_por_base_y_fecha = {}
    for e in remotas:
        if e.relacion is RelacionActualizacion.CONTRADICTORIA:
            estado = EstadoActualizacion.CONTRADICTORIO
            return resultado(Decision.REVISION_MANUAL, "evidencia_documental_contradictoria")
        if e.relacion is RelacionActualizacion.DESCONOCIDA:
            continue
        if e.procedencia.evidencia is None:
            faltantes.add("fundamento_de_relacion_documental")
            continue
        base = next((a for a in historicos if a.adquisicion_id is not None and a.adquisicion_id == e.adquisicion_base_id), None)
        if base is None or e.version_previa is None or e.version_nueva is None or base.version_recurso is None:
            faltantes.add("relacion_de_versiones_con_una_adquisicion_base")
            continue
        contradictoria = (base.version_recurso != e.version_previa
            or (e.relacion is RelacionActualizacion.POSTERIOR_DOCUMENTADA and e.version_previa == e.version_nueva)
            or (e.relacion is RelacionActualizacion.MISMA_VERSION_DECLARADA and e.version_previa != e.version_nueva))
        if contradictoria:
            estado = EstadoActualizacion.CONTRADICTORIO
            return resultado(Decision.REVISION_MANUAL, "relacion_documental_contradice_antecedente")
        clave = (e.adquisicion_base_id, e.procedencia.revisada_utc)
        relaciones = relaciones_por_base_y_fecha.setdefault(clave, set())
        relaciones.add(e.relacion)
        if len(relaciones) > 1:
            estado = EstadoActualizacion.CONTRADICTORIO
            return resultado(Decision.REVISION_MANUAL, "relaciones_documentales_incompatibles_para_misma_base_y_fecha")
        if e.relacion is RelacionActualizacion.POSTERIOR_DOCUMENTADA:
            versiones_nuevas.add(e.version_nueva)
            versiones_base.add(e.version_previa)
            estado = EstadoActualizacion.DOCUMENTADA
        else:
            limites.add("misma_version_declarada_no_prueba_igualdad_de_bytes")
    if len(versiones_nuevas) > 1:
        return resultado(Decision.REVISION_MANUAL, "versiones_posteriores_sin_orden_documentado")
    if versiones_nuevas:
        actualizados = [a for a in candidatos if a.version_recurso in versiones_nuevas]
        if actualizados:
            candidatos = actualizados
            notas.add("version_posterior_ya_disponible_localmente")
        elif candidatos and any(a.version_recurso not in versiones_base for a in candidatos):
            return resultado(Decision.REVISION_MANUAL, "version_local_no_comparable_con_actualizacion")
        else:
            return nueva(Decision.RECOMENDAR_NUEVA, "version_posterior_documentada")

    if s.politica.modo is ModoConsulta.SOLICITAR_NUEVA:
        return nueva(Decision.ADQUISICION_INICIAL if not historicos and s.historial_completo else Decision.RECOMENDAR_NUEVA,
                     "nueva_adquisicion_solicitada_explicitamente")
    if not historicos:
        if s.historial_completo:
            return nueva(Decision.ADQUISICION_INICIAL, "sin_antecedente_en_historial_declarado_completo")
        return resultado(Decision.EVIDENCIA_INSUFICIENTE, "ausencia_de_antecedentes_no_demostrada")
    if candidatos:
        if s.politica.modo is ModoConsulta.EXIGIR_VIGENCIA:
            faltantes.add("evidencia_suficiente_de_vigencia_del_recurso")
            return resultado(Decision.EVIDENCIA_INSUFICIENTE, "integridad_local_no_demuestra_vigencia")
        if permiso("permite_reutilizar") is False:
            return resultado(Decision.BLOQUEADA, "reutilizacion_local_prohibida")
        if permiso("permite_reutilizar") is None:
            faltantes.add("permiso_de_reutilizacion_documentado_para_este_alcance")
            return resultado(Decision.REVISION_MANUAL, "permiso_de_reutilizacion_desconocido")
        campo_historico = {UsoPrevisto.PUBLICACION: "permite_publicar_historico",
                          UsoPrevisto.REDISTRIBUCION: "permite_redistribuir_historico"}.get(s.uso)
        if campo_historico:
            permitidos = [a for a in candidatos if getattr(a, campo_historico) is not False]
            if not permitidos:
                return resultado(Decision.BLOQUEADA, "restriccion_historica_del_uso_no_resuelta")
            candidatos = permitidos
        if any(a.restricciones_historicas for a in candidatos):
            return resultado(Decision.REVISION_MANUAL, "restricciones_historicas_requieren_revision")
        return resultado(Decision.REUTILIZAR_LOCAL, "copia_local_coincidente_segun_evidencia_aportada", candidatos)
    if incompletos:
        return resultado(Decision.REVISION_MANUAL, "adquisiciones_incompletas_sin_copia_elegible")
    return resultado(Decision.EVIDENCIA_INSUFICIENTE, "ninguna_copia_local_comprobada_elegible")
