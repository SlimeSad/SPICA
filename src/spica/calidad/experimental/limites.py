"""Comparación puntual de fixtures. No integra ni autoriza el catálogo científico."""

from decimal import DecimalException
from threading import Event

from ...perfilado.interpretacion import interpretar_numero
from .modelos import (
    EstadoLimiteExperimental as E, ObservacionSintetica, ReglaLimitesSintetica,
    ResultadoLimiteSintetico,
)


def evaluar_limites_sinteticos(regla: ReglaLimitesSintetica, observacion: ObservacionSintetica, *,
                              cancelacion: Event | None = None) -> ResultadoLimiteSintetico:
    """Una observación explícitamente sintética; sin I/O, loaders o lotes implícitos.

    No admite ReglaCientifica, revisiones/habilitaciones del catálogo, RegistroQA,
    ObservacionLocal, rutas o diccionarios. Ningún estado documental activa esta API.
    La procedencia sintética es declaración del llamador, no prueba criptográfica.
    """
    if type(regla) is not ReglaLimitesSintetica or type(observacion) is not ObservacionSintetica:
        raise TypeError("Solo se admiten contratos exclusivos de fixtures sintéticas")
    if cancelacion is not None and type(cancelacion) is not Event:
        raise TypeError("Cancelación mediante threading.Event requerida")

    def resultado(estado, motivo, numero=None):
        return ResultadoLimiteSintetico(observacion, regla, estado, motivo, numero)

    def cancelado():
        return cancelacion is not None and cancelacion.is_set()

    if cancelado():
        return resultado(E.EVALUACION_INCOMPLETA, "cancelado_antes_de_evaluar")
    evidencia = regla.evidencia_parametros
    if evidencia is None:
        return resultado(E.NO_EVALUADO_EVIDENCIA, "evidencia_de_parametros_ausente")
    if (evidencia.fixture_id, evidencia.version) != (observacion.evidencia.fixture_id, observacion.evidencia.version):
        return resultado(E.NO_EVALUADO_EVIDENCIA, "parametros_y_datos_de_distinta_fixture_o_version")
    if regla.variable != observacion.variable:
        return resultado(E.NO_EVALUADO_VARIABLE, "variable_incompatible")
    for nombre, estado in (("unidad", E.NO_EVALUADO_UNIDAD), ("modalidad", E.NO_EVALUADO_MODALIDAD),
                           ("frecuencia", E.NO_EVALUADO_FRECUENCIA)):
        esperado, recibido = getattr(regla, nombre), getattr(observacion, nombre)
        if esperado is None or recibido is None:
            return resultado(estado, nombre + "_desconocida")
        if esperado != recibido:
            return resultado(estado, nombre + "_incompatible")
    try:
        n = interpretar_numero(observacion.valor_original, limites=regla.politica_numerica)
    except DecimalException:
        return resultado(E.ERROR_TECNICO, "error_de_interpretacion_decimal")
    if cancelado():
        return resultado(E.EVALUACION_INCOMPLETA, "cancelado_tras_interpretacion")
    if n.clase == "fuera_presupuesto_numerico":
        return resultado(E.EVALUACION_INCOMPLETA, "presupuesto_numerico_excedido")
    if n.clase != "finito":
        motivos = {"vacio": "valor_vacio", "no_finito": "literal_no_finito", "no_interpretable": "valor_no_numerico"}
        return resultado(E.ERROR_TECNICO, motivos.get(n.clase, "clasificacion_numerica_no_admitida"))
    valor = n.numero
    try:
        inferior = valor >= regla.limite_inferior if regla.incluir_inferior else valor > regla.limite_inferior
        superior = valor <= regla.limite_superior if regla.incluir_superior else valor < regla.limite_superior
    except DecimalException:
        return resultado(E.ERROR_TECNICO, "error_de_comparacion_decimal")
    if cancelado():
        return resultado(E.EVALUACION_INCOMPLETA, "cancelado_tras_comparacion", valor)
    satisfecha = inferior and superior
    if satisfecha:
        motivo = "dentro_del_intervalo_sintetico"
    elif valor == regla.limite_inferior:
        motivo = "extremo_inferior_excluido"
    elif valor == regla.limite_superior:
        motivo = "extremo_superior_excluido"
    else:
        motivo = "por_debajo_del_intervalo_sintetico" if not inferior else "por_encima_del_intervalo_sintetico"
    return resultado(E.CONDICION_SATISFECHA if satisfecha else E.CONDICION_NO_SATISFECHA, motivo, valor)
