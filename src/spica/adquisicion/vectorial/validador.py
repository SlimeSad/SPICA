"""FeatureSet JSON acotado, conservador y sin interpretación científica."""

from enum import Enum
from decimal import Decimal
import hashlib
import math
from threading import Event

from .._json_acotado import _Invalido, _Incompleto, _exigir, _presupuesto, leer_json
from .modelos import (
    ContratoFeatureSet, EntidadVector, EstadoGeometria, EstadoPagina, LimitesVector,
    PaginaValidada, RespuestaSintetica, TipoCampo, _congelar, _LimiteSnapshot, PrecisionNumerica,
)


class _Lectura(Enum):
    PARCIAL = "parcial"
    COMPLETO = "completo"


def _cancelar(evento):
    if evento is not None and evento.is_set():
        raise _Incompleto("operacion_cancelada")


def _crs(d, contrato):
    _exigir(type(d) is dict, "crs_ausente_o_invalido")
    _exigir(d == contrato.referencia.declaracion()
            and all(type(x) is int for x in d.values()), "crs_no_coincide_con_contrato")


def _campos(d, contrato, limites):
    esperados = {c.nombre: c for c in contrato.campos}
    _presupuesto(len(esperados) <= limites.atributos_entidad, "limite_atributos")
    _exigir(d.get("objectIdFieldName") == contrato.campo_oid, "descriptor_oid_contradictorio")
    campos = d.get("fields")
    _exigir(type(campos) is list and len(campos) == len(esperados), "esquema_campos_incorrecto")
    vistos = set()
    for c in campos:
        _exigir(type(c) is dict and type(c.get("name")) is str, "descriptor_campo_invalido")
        nombre = c["name"]
        _exigir(nombre not in vistos and nombre in esperados, "descriptor_campo_inesperado_o_duplicado")
        vistos.add(nombre)
        _exigir(c.get("type") == esperados[nombre].tipo.value, "tipo_campo_contradictorio")
        if "nullable" in c:
            _exigir(type(c["nullable"]) is bool and c["nullable"] == esperados[nombre].nullable,
                     "nulabilidad_contradictoria")


def _valor(v, campo):
    if v is None:
        return campo.nullable
    if campo.tipo in (TipoCampo.OID, TipoCampo.ENTERO, TipoCampo.ENTERO_CORTO, TipoCampo.ENTERO_LARGO):
        if type(v) is not int:
            return False
        if campo.tipo is TipoCampo.OID:
            return 0 <= v <= 2**63 - 1
        bits = {TipoCampo.ENTERO_CORTO: 16, TipoCampo.ENTERO: 32, TipoCampo.ENTERO_LARGO: 64}[campo.tipo]
        return -(2**(bits - 1)) <= v < 2**(bits - 1)
    if campo.tipo in (TipoCampo.REAL, TipoCampo.REAL_SIMPLE, TipoCampo.FECHA):
        return _numero(v)
    return type(v) is str  # GUID/GlobalID: solo tipo textual, sin afirmar unicidad.


def _numero(v):
    # Decimal.is_finite no convierte a float ni depende del contexto decimal.
    return (type(v) is int or type(v) is Decimal and v.is_finite()
            or type(v) is float and math.isfinite(v))


def _poligono(g, contrato, limites, cancelacion):
    _exigir(type(g) is dict and set(g) <= {"rings", "spatialReference"}, "geometria_no_admitida")
    if "spatialReference" in g:
        _crs(g["spatialReference"], contrato)
    rings = g.get("rings")
    _exigir(type(rings) is list and bool(rings), "anillos_ausentes_o_vacios")
    _presupuesto(len(rings) <= limites.anillos_entidad, "limite_anillos")
    posiciones = 0
    for ring in rings:
        _cancelar(cancelacion)
        _exigir(type(ring) is list and len(ring) >= 4, "anillo_malformado")
        posiciones += len(ring)
        _presupuesto(posiciones <= limites.coordenadas_entidad, "limite_coordenadas_entidad")
        for i, p in enumerate(ring):
            if i % 512 == 0:
                _cancelar(cancelacion)
            _exigir(type(p) is list and len(p) == contrato.dimensiones, "dimension_coordenada_invalida")
            _exigir(all(_numero(x) for x in p), "coordenada_no_numerica_o_finita")
        _exigir(ring[0] == ring[-1], "anillo_no_cerrado")
    return posiciones


def validar_featureset(respuesta: RespuestaSintetica, contrato: ContratoFeatureSet, *,
                      limites: LimitesVector | None = None,
                      cancelacion: Event | None = None,
                      precision: PrecisionNumerica = PrecisionNumerica.BINARIA_COMPATIBLE) -> PaginaValidada:
    """Valida una página entera en memoria acotada; nunca agrega otras páginas.

    Hash de bytes recibidos en memoria, NO verificación de un archivo físico ni
    autenticación de origen. El estado VALIDA no afirma completitud remota.
    """
    if type(respuesta) is not RespuestaSintetica or type(contrato) is not ContratoFeatureSet:
        raise TypeError("Respuesta sintética y contrato requeridos")
    if limites is not None and type(limites) is not LimitesVector:
        raise TypeError("Límites vectoriales requeridos")
    if cancelacion is not None and type(cancelacion) is not Event:
        raise TypeError("Cancelación tipada requerida")
    if type(precision) is not PrecisionNumerica:
        raise TypeError("Política numérica tipada requerida")
    binaria = precision is PrecisionNumerica.BINARIA_COMPATIBLE
    limites = limites if limites is not None else LimitesVector()
    cuerpo = respuesta.contenido
    estado, diagnosticos, entidades, crs, exceso, posiciones = EstadoPagina.INVALIDA, (), (), None, None, 0
    sha256 = None
    try:
        _cancelar(cancelacion)
        _presupuesto(len(cuerpo) <= limites.max_bytes_respuesta, "limite_bytes_respuesta")
        sha256 = hashlib.sha256(cuerpo).hexdigest()
        if respuesta.interrumpida or not respuesta.transferencia_completa:
            return PaginaValidada(respuesta, EstadoPagina.INTERRUMPIDA, sha256=sha256,
                                  bytes_recibidos=len(cuerpo), diagnosticos=("transferencia_interrumpida",),
                                  precision=precision)
        _exigir(respuesta.codigo_http == 200, "http_no_200")
        _exigir(respuesta.longitud_declarada is None or respuesta.longitud_declarada == len(cuerpo),
                 "longitud_declarada_contradictoria")
        progreso = dict(unidades_prelectura=0, nodos_documento=0, profundidad_maxima=0)
        d = leer_json(cuerpo, limites, cancelacion, progreso,
                      max_bytes=limites.max_bytes_respuesta, estados=_Lectura, codigo_bytes="limite_bytes_respuesta",
                      decimales_exactos=True, compatibilidad_binaria=binaria)
        _exigir(type(d) is dict, "featureset_no_es_objeto")
        _exigir("error" not in d, "error_arcgis_en_http_200")
        _exigir("transform" not in d, "cuantizacion_no_admitida")
        _exigir(d.get("geometryType") == contrato.geometria, "tipo_geometria_contradictorio")
        for k in ("hasZ", "hasM"):
            if k in d:
                _exigir(type(d[k]) is bool and d[k] is False, "dimensiones_no_admitidas")
        _crs(d.get("spatialReference"), contrato)
        _campos(d, contrato, limites)
        if "exceededTransferLimit" in d:
            _exigir(type(d["exceededTransferLimit"]) is bool, "transfer_limit_no_booleano")
            exceso = d["exceededTransferLimit"]
        features = d.get("features")
        _exigir(type(features) is list, "features_ausente_o_invalido")
        _presupuesto(len(features) <= limites.entidades_pagina, "limite_entidades_pagina")
        salida, vistos = [], set()
        campos = {c.nombre: c for c in contrato.campos}
        for f in features:
            _cancelar(cancelacion)
            _exigir(type(f) is dict and set(f) <= {"attributes", "geometry"}, "entidad_malformada")
            a = f.get("attributes")
            _exigir(type(a) is dict, "atributos_ausentes_o_invalidos")
            _presupuesto(len(a) <= limites.atributos_entidad, "limite_atributos")
            _exigir(contrato.campo_oid in a and a[contrato.campo_oid] is not None, "oid_ausente")
            _exigir(set(a) == set(campos), "atributos_distintos_del_contrato")
            _exigir(all(_valor(v, campos[k]) for k, v in a.items()), "tipo_atributo_incorrecto")
            oid = a[contrato.campo_oid]
            _exigir(oid not in vistos, "oid_duplicado_en_pagina")
            vistos.add(oid)
            if "geometry" not in f:
                eg, g = EstadoGeometria.AUSENTE, None
            elif f["geometry"] is None:
                eg, g = EstadoGeometria.NULA, None
            else:
                eg, g = EstadoGeometria.PRESENTE, f["geometry"]
                posiciones += _poligono(g, contrato, limites, cancelacion)
                _presupuesto(posiciones <= limites.coordenadas_pagina, "limite_coordenadas_pagina")
            # Comparar anillos con valores exactos ANTES de la representación
            # binaria opcional: el redondeo no debe cerrar un anillo abierto.
            salida.append(EntidadVector(oid, _congelar(a, binaria=binaria), eg, _congelar(g, binaria=binaria)))
        crs, entidades = _congelar(d["spatialReference"]), tuple(salida)
        _cancelar(cancelacion)
        estado = EstadoPagina.VALIDA
    except _Incompleto as exc:
        codigo = str(exc)
        estado = EstadoPagina.CANCELADA if codigo in ("operacion_cancelada", "inspeccion_cancelada") else EstadoPagina.LIMITADA
        diagnosticos = ("operacion_cancelada" if estado is EstadoPagina.CANCELADA else codigo,)
    except _Invalido as exc:
        diagnosticos = (str(exc),)
    except _LimiteSnapshot:
        estado, diagnosticos = EstadoPagina.LIMITADA, ("limite_snapshot_inmutable",)
    except (ValueError, UnicodeError, RecursionError, OverflowError):
        diagnosticos = ("json_malformado_o_no_admitido",)
    if estado is not EstadoPagina.VALIDA:
        entidades, crs, exceso, posiciones = (), None, None, 0
    return PaginaValidada(respuesta, estado, entidades, crs, exceso, sha256,
                          len(cuerpo), posiciones, diagnosticos, precision)
