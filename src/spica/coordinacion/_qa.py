"""Cotejo de cierres QA aportados; nunca llama al motor ni prueba autenticidad."""

from collections import Counter

from ..calidad.modelos import EstadoEvaluacionQA, EstadoResultadoQA, VERSION_CONTRATO_QA
from ..calidad.reglas import seleccionar_reglas
from ..contextos import EstadoOperacion, TipoOperacion, PERFIL_QA0, validar_vinculos_qa


def revisar_preparacion_qa(operacion):
    """Precondiciones declaradas del adaptador RC1, sin fabricar fila o resultado."""
    if operacion.tipo is not TipoOperacion.QA_NIVEL0:
        return ()
    problemas = []
    cfg = operacion.proyecto.configuracion
    if cfg.perfil != PERFIL_QA0 or cfg.revision != "1.0.0":
        problemas.append(("perfil_o_revision_qa_no_admitidos", True))
    for e in operacion.entradas:
        if e.perfil_estructural is None:
            problemas.append(("perfil_entrada_qa_desconocido", False))
        elif e.perfil_estructural != PERFIL_QA0:
            problemas.append(("perfil_entrada_qa_no_admitido", True))
        if e.recurso is None or e.recurso.procedencia is None:
            problemas.append(("metadatos_qa_insuficientes", False))
    return tuple(dict.fromkeys(problemas))


def revisar_cierre_qa(operacion, cierre):
    """Devuelve código, contradicción, cierre completo y contadores aportados."""
    if cierre is None:
        return None, False, False, None
    if operacion.tipo is not TipoOperacion.QA_NIVEL0:
        return "cierre_qa_en_operacion_de_otro_tipo", True, False, None
    informe, vs = cierre.informe, cierre.vinculos
    if any(v.operacion is not operacion for v in vs):
        return "vinculo_qa_de_otra_operacion_o_instantanea", True, False, None
    try:
        validar_vinculos_qa(operacion, vs)
        seleccionadas = seleccionar_reglas(operacion.configuracion_qa)
    except (TypeError, ValueError):
        return "lote_qa_no_corresponde_a_contexto", True, False, None
    cantidades = (informe.registros_examinados, informe.registros_finalizados,
                  informe.resultados_emitidos, informe.evaluaciones_incompletas)
    if (informe.version_contrato != VERSION_CONTRATO_QA or type(informe.estado) is not EstadoEvaluacionQA
            or type(informe.recorrido_completo) is not bool
            or any(type(n) is not int or n < 0 for n in cantidades)):
        return "informe_qa_invalido", True, False, None
    registros = {(v.entrada_id, v.resultado.registro.numero_registro) for v in vs}
    conteos = Counter((v.resultado.regla.categoria, v.resultado.estado) for v in vs)
    reglas = tuple(r for r in seleccionadas
                   if any(v.resultado.regla == r for v in vs))
    esperados = tuple((c, e, n) for (c, e), n in sorted(conteos.items(), key=lambda x: (x[0][0].value, x[0][1].value)))
    if (informe.configuracion != operacion.configuracion_qa or informe.limites != operacion.limites_qa
            or any(v.resultado.procedencia != informe.procedencia for v in vs)
            or informe.resultados_emitidos != len(vs) or informe.registros_examinados != len(registros)
            or informe.registros_finalizados > informe.registros_examinados
            or informe.conteos != esperados or informe.reglas_ejecutadas != reglas
            or informe.evaluaciones_incompletas != sum(v.resultado.estado is EstadoResultadoQA.EVALUACION_INCOMPLETA for v in vs)):
        return "informe_y_resultados_qa_contradictorios", True, False, None
    completa = (bool(vs) and informe.estado is EstadoEvaluacionQA.COMPLETA and informe.recorrido_completo
                and informe.motivo_fin == "eof" and informe.registros_finalizados == informe.registros_examinados
                and not informe.evaluaciones_incompletas)
    if informe.estado is EstadoEvaluacionQA.COMPLETA and not completa:
        return "informe_qa_completo_con_condiciones_contradictorias", True, False, None
    if operacion.estado is EstadoOperacion.CONCLUIDA and not completa:
        return "operacion_concluida_con_qa_incompleta", True, False, None
    observados = informe.registros_examinados, informe.resultados_emitidos
    if completa and operacion.estado is EstadoOperacion.CONCLUIDA:
        return "cierre_qa_aportado_coherente_completo_no_autenticado", False, True, observados
    return "cierre_qa_parcial_o_sin_conclusion_contextual", False, False, observados
