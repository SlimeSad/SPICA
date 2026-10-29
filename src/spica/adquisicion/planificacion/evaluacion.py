"""Evaluación conservadora de intervalos y asociaciones explícitas."""

from ..catalogo import EstadoVerificacion
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
    if d.fin < inicio or d.inicio > fin:
        return EvaluacionIntervalo(registro, d.estado, SituacionTemporal.FUERA_COBERTURA_CONOCIDA,
                                   None, exacto, frecuencia)
    tramo = TramoTemporal(max(inicio, d.inicio), min(fin, d.fin))
    parcial = d.cobertura_parcial is not False or d.inicio > inicio or d.fin < fin
    return EvaluacionIntervalo(registro, d.estado,
        SituacionTemporal.PARCIAL if parcial else SituacionTemporal.CATALOGADA, tramo, exacto, frecuencia)


def vacios(inicio, fin, tramos):
    """Complemento de intervalos cerrados; no inventa una resolución temporal."""
    resultado = []
    cursor, incluido = inicio, True
    for tramo in sorted(tramos, key=lambda t: (t.inicio, t.fin)):
        if tramo.inicio > cursor:
            resultado.append(TramoTemporal(cursor, tramo.inicio, incluido, False))
        if tramo.fin >= cursor:
            cursor, incluido = tramo.fin, False
    if cursor < fin or (cursor == fin and incluido):
        resultado.append(TramoTemporal(cursor, fin, incluido, True))
    return tuple(resultado)
