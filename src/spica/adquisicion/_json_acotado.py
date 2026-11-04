"""Lector JSON interno compartido; sin transporte, archivos ni política institucional."""

import json
import math
from decimal import Decimal


class _Invalido(Exception):
    pass


class _Incompleto(_Invalido):
    pass


def _presupuesto(condicion, codigo):
    if not condicion:
        raise _Incompleto(codigo)


def _cancelar(evento):
    if evento is not None and evento.is_set():
        raise _Incompleto("inspeccion_cancelada")


def _exigir(condicion, codigo):
    if not condicion:
        raise _Invalido(codigo)


def _recorrer(d, limites, cancelacion):
    """DFS con iteradores: frontera O(profundidad), sin listas de todos los hijos."""
    pila = [iter((d,))]
    nodos = 0
    while pila:
        try:
            v = next(pila[-1])
        except StopIteration:
            pila.pop()
            continue
        nodos += 1
        if nodos % 256 == 1:
            _cancelar(cancelacion)
        if type(v) is dict:
            # Cada clave cuenta también como nodo; sin copiar claves o valores.
            pila.append((x for par in v.items() for x in par))
        elif type(v) is list:
            pila.append(iter(v))
        elif type(v) is str:
            _presupuesto(len(v) <= limites.caracteres_cadena, "json_texto_excesivo")
        yield nodos


def leer_json(cuerpo, limites, cancelacion, progreso, *, max_bytes, estados, codigo_bytes,
              decimales_exactos=False, compatibilidad_binaria=False):
    _presupuesto(len(cuerpo) <= max_bytes, codigo_bytes)
    _cancelar(cancelacion)
    progreso["estado_json"] = estados.PARCIAL
    texto = cuerpo.decode("utf-8-sig")
    # Presupuesto léxico, no parser: json.loads valida TODA la gramática.
    # Para JSON válido cada apertura de contenedor/cadena y cada inicio de
    # primitivo representa un nodo (incluidas claves). La puntuación no añade
    # nodos: evita contar otra vez valores ya reservados por ':' o por ','.
    pila, unidades, cadena, escape, primitivo = [], 0, False, False, False
    for i, c in enumerate(texto):
        if i % 4096 == 0:
            _cancelar(cancelacion)
        if cadena:
            if escape:
                escape = False
            elif c == "\\":
                escape = True
            elif c == '"':
                cadena = False
        elif c == '"':
            cadena = True
            primitivo = False
            unidades += 1
        elif c in "[{":
            pila.append([c, 1])
            unidades += 1
            primitivo = False
            progreso["profundidad_maxima"] = max(progreso["profundidad_maxima"], len(pila))
            _presupuesto(len(pila) <= limites.profundidad, "json_demasiado_profundo")
        elif c in "]}":
            _exigir(pila and pila[-1][0] == ("[" if c == "]" else "{"),
                     "json_malformado_o_no_admitido")
            pila.pop()
            primitivo = False
        elif c == ",":
            primitivo = False
            if pila:
                pila[-1][1] += 1
                tope = limites.elementos_lista if pila[-1][0] == "[" else limites.propiedades_objeto
                _presupuesto(pila[-1][1] <= tope, "json_demasiados_elementos")
        elif c == ":":
            primitivo = False
        elif c in " \t\r\n":
            primitivo = False
        elif not primitivo:
            unidades += 1
            primitivo = True
        progreso["unidades_prelectura"] = unidades
        _presupuesto(unidades <= limites.unidades_documento, "json_presupuesto_documento_agotado")
    def pares(items):
        _cancelar(cancelacion)
        d = {}
        for k, v in items:
            _exigir(k not in d, "json_claves_duplicadas")
            d[k] = v
        return d
    def constante(_):
        raise _Invalido("json_numero_no_finito")
    def entero(s):
        _exigir(len(s) <= 32, "json_entero_excesivo")
        return int(s)
    def decimal(s):
        if decimales_exactos:
            # Solo la inspección vectorial opta por este camino. El constructor
            # Decimal(texto) es exacto e independiente de getcontext().prec.
            _presupuesto(len(s) <= limites.caracteres_numero, "json_numero_excesivo")
            exponente = s.lower().partition("e")[2]
            _presupuesto(not exponente or abs(int(exponente)) <= limites.exponente_decimal,
                         "json_exponente_excesivo")
            valor = Decimal(s)
            _exigir(valor.is_finite(), "json_numero_no_finito")
            _presupuesto(abs(valor.as_tuple().exponent) <= limites.exponente_decimal,
                         "json_exponente_excesivo")
            if compatibilidad_binaria:
                convertido = float(valor)
                _exigir(math.isfinite(convertido), "json_numero_no_finito")
                _exigir(convertido != 0 or valor.is_zero(), "json_subdesbordamiento_binario")
            return valor
        valor = float(s)
        _exigir(math.isfinite(valor), "json_numero_no_finito")
        return valor
    d = json.loads(texto, object_pairs_hook=pares, parse_constant=constante, parse_int=entero, parse_float=decimal)
    del texto
    for nodos in _recorrer(d, limites, cancelacion):
        progreso["nodos_documento"] = nodos
        _presupuesto(nodos <= limites.unidades_documento, "json_presupuesto_documento_agotado")
    _cancelar(cancelacion)
    progreso["estado_json"] = estados.COMPLETO
    return d


