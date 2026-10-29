"""Evaluación conservadora de intervalos y asociaciones explícitas."""

from ..catalogo import EstadoVerificacion
from ..nucleo.temporal import instante_utc, validar_intervalo
from .modelos import EvaluacionIntervalo, SituacionTemporal, TramoTemporal


def evaluar_intervalo(registro, consulta, variables):
    d = registro.entidad
    s = consulta.solicitud
    variable = variables.get(d.variable_id)
    codigo = variable.codigo_original if variable is not None else None
    exacto = (not s.estaciones or d.estacion_id is not None) and (not s.variables or codigo is not None)
    frecuencia = (None if d.frecuencia_declarada is None else d.frecuencia_declarada == consulta.frecuencia)
    if consulta.frecuencia is None:
        frecuencia = True
    inicio, fin = s.fecha_inicial, s.fecha_final
    # Una zona textual no autoriza localizar timestamps naive.
    conocido = d.estado is not EstadoVerificacion.DESCONOCIDO and all(
        f is not None and f.utcoffset() is not None for f in (d.inicio, d.fin))
    if not conocido:
        return EvaluacionIntervalo(registro, d.estado, SituacionTemporal.DESCONOCIDA,
                                   TramoTemporal(inicio, fin), exacto, frecuencia)
    di, df = instante_utc(d.inicio), instante_utc(d.fin)
    si, sf = instante_utc(inicio), instante_utc(fin)
    if df < si or di > sf:
        return EvaluacionIntervalo(registro, d.estado, SituacionTemporal.FUERA_COBERTURA_CONOCIDA,
                                   None, exacto, frecuencia)
    tramo = TramoTemporal(max(inicio, d.inicio, key=instante_utc),
                          min(fin, d.fin, key=instante_utc))
    parcial = d.cobertura_parcial is not False or di > si or df < sf
    return EvaluacionIntervalo(registro, d.estado,
        SituacionTemporal.PARCIAL if parcial else SituacionTemporal.CATALOGADA, tramo, exacto, frecuencia)


def vacios(inicio, fin, tramos):
    """Complemento dentro de [inicio, fin], sin inferir resolución ni frecuencia.

    Solo la unión auxiliar se fusiona. Las operaciones y su evidencia permanecen
    separadas. Los indicadores también permiten representar puntos sin cobertura.
    """
    validar_intervalo(inicio, fin)
    si, sf = instante_utc(inicio), instante_utc(fin)
    recortados = []
    for t in tramos:
        ti, tf = instante_utc(t.inicio), instante_utc(t.fin)
        if tf < si or ti > sf:
            continue
        a, ia = (inicio, True) if ti < si else (t.inicio, t.incluye_inicio)
        b, ib = (fin, True) if tf > sf else (t.fin, t.incluye_fin)
        ai, bi = instante_utc(a), instante_utc(b)
        if ai < bi or (ai == bi and ia and ib):
            recortados.append((ai, bi, TramoTemporal(a, b, ia, ib)))
    unidos = []
    for ai, bi, t in sorted(recortados, key=lambda r: (r[0], not r[2].incluye_inicio, r[1])):
        if unidos:
            anterior = unidos[-1]
            af = instante_utc(anterior.fin)
            if ai < af or (ai == af and (anterior.incluye_fin or t.incluye_inicio)):
                if bi >= af:
                    unidos[-1] = TramoTemporal(anterior.inicio, t.fin, anterior.incluye_inicio,
                        t.incluye_fin if bi > af else anterior.incluye_fin or t.incluye_fin)
                continue
        unidos.append(t)
    resultado = []
    cursor, incluido = inicio, True
    for t in unidos:
        ci, ti = instante_utc(cursor), instante_utc(t.inicio)
        if ci < ti or (ci == ti and incluido and not t.incluye_inicio):
            resultado.append(TramoTemporal(cursor, t.inicio, incluido, not t.incluye_inicio))
        cursor, incluido = t.fin, not t.incluye_fin
    ci = instante_utc(cursor)
    if ci < sf or (ci == sf and incluido):
        resultado.append(TramoTemporal(cursor, fin, incluido, True))
    return tuple(resultado)
