"""Validación estructural de metadatos JSON acotados. Sin red, archivos o GIS."""

import hashlib
import json
import math

from ..transportes import RespuestaHTTP
from .modelos import (
    EstadoMetadatos, LIMITE_METADATOS, ObjetivoArcGIS, TipoMetadatos, ValidacionMetadatos,
)


class _Invalido(Exception):
    pass


def _exigir(condicion, codigo):
    if not condicion:
        raise _Invalido(codigo)


def _texto(valor):
    return type(valor) is str and bool(valor.strip()) and len(valor) <= 65_536


def _entero(valor, minimo=0):
    return type(valor) is int and valor >= minimo


def _numero(valor):
    return type(valor) in (int, float) and math.isfinite(valor)


def _json_acotado(cuerpo):
    _exigir(len(cuerpo) <= LIMITE_METADATOS, "limite_metadatos_excedido")
    texto = cuerpo.decode("utf-8-sig")
    profundidad, tokens, cadena, escape = 0, 0, False, False
    for c in texto:
        if cadena:
            if escape:
                escape = False
            elif c == "\\":
                escape = True
            elif c == '"':
                cadena = False
        elif c == '"':
            cadena = True
            tokens += 1
        elif c in "[{":
            profundidad += 1
            tokens += 1
            _exigir(profundidad <= 32, "json_demasiado_profundo")
        elif c in "]}":
            profundidad -= 1
        elif c == ",":
            tokens += 1
        _exigir(tokens <= 20_000, "json_demasiados_elementos")
    def pares(items):
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
        valor = float(s)
        _exigir(math.isfinite(valor), "json_numero_no_finito")
        return valor
    d = json.loads(texto, object_pairs_hook=pares, parse_constant=constante, parse_int=entero, parse_float=decimal)
    pila, nodos = [d], 0
    while pila:
        v = pila.pop()
        nodos += 1
        _exigir(nodos <= 20_000, "json_demasiados_elementos")
        if type(v) is dict:
            pila.extend(v.keys())
            pila.extend(v.values())
        elif type(v) is list:
            pila.extend(v)
        elif type(v) is str:
            _exigir(len(v) <= 65_536, "json_texto_excesivo")
    return d


def _referencia(d, objetivo):
    _exigir(type(d) is dict, "referencia_espacial_ausente")
    wkid, latest = d.get("wkid"), d.get("latestWkid")
    _exigir(type(wkid) is int, "wkid_ausente_o_invalido")
    _exigir(wkid in (objetivo.wkid_esperado, objetivo.latest_wkid_esperado), "referencia_espacial_distinta")
    _exigir(latest is None or (type(latest) is int and latest == objetivo.latest_wkid_esperado),
             "latest_wkid_contradictorio")


def _extension(e, objetivo):
    _exigir(type(e) is dict, "extension_ausente")
    _exigir(all(_numero(e.get(k)) for k in ("xmin", "ymin", "xmax", "ymax")), "extension_invalida")
    _exigir(e["xmin"] <= e["xmax"] and e["ymin"] <= e["ymax"], "extension_invertida")
    _referencia(e.get("spatialReference"), objetivo)


def _esquema(d, tipo, objetivo, advertencias):
    _exigir(type(d) is dict, "json_no_es_objeto")
    _exigir("error" not in d, "error_arcgis_en_respuesta")
    _exigir("features" not in d and "featureSets" not in d, "respuesta_de_entidades_no_admitida")
    _exigir(_entero(d.get("maxRecordCount"), 1), "max_record_count_invalido")
    _exigir(_texto(d.get("supportedQueryFormats")), "formatos_de_consulta_ausentes")
    if "capabilities" in d:
        _exigir(_texto(d["capabilities"]), "capacidades_invalidas")
    else:
        advertencias.append("capacidades_no_declaradas")
    if "advancedQueryCapabilities" in d:
        a = d["advancedQueryCapabilities"]
        _exigir(type(a) is dict, "capacidades_avanzadas_invalidas")
        if "supportsPagination" in a:
            _exigir(type(a["supportsPagination"]) is bool, "paginacion_de_tipo_invalido")
        else:
            advertencias.append("paginacion_no_anunciada")
    else:
        advertencias.append("paginacion_no_anunciada")
    if "currentVersion" in d:
        _exigir(_numero(d["currentVersion"]) and d["currentVersion"] > 0, "version_software_invalida")
    else:
        advertencias.append("version_software_no_declarada")
    advertencias.extend(("licencia_y_derechos_no_acreditados", "sin_comprobacion_de_entidades_o_completitud"))
    if tipo is TipoMetadatos.SERVICIO:
        _exigir(_texto(d.get("mapName")), "nombre_de_mapa_ausente")
        if "serviceName" in d:
            _exigir(d["serviceName"] == objetivo.servicio_id, "servicio_distinto")
        else:
            advertencias.append("identidad_servicio_ligada_a_ruta_y_capas_no_a_mapname")
        capas = d.get("layers")
        _exigir(type(capas) is list and 0 < len(capas) <= 1024, "lista_de_capas_ausente_o_excesiva")
        vistos = set()
        for c in capas:
            _exigir(type(c) is dict and _entero(c.get("id")) and _texto(c.get("name")), "capa_anunciada_invalida")
            _exigir(c["id"] not in vistos, "capas_duplicadas")
            vistos.add(c["id"])
        candidata = next((c for c in capas if c["id"] == objetivo.capa_id), None)
        _exigir(candidata is not None, "capa_prioritaria_ausente")
        _exigir(candidata["name"] == objetivo.capa_nombre, "nombre_de_capa_distinto")
        _referencia(d.get("spatialReference"), objetivo)
        _extension(d.get("fullExtent"), objetivo)
        _exigir(_texto(d.get("units")), "unidades_no_declaradas")
        return None
    _exigir(type(d.get("id")) is int and d["id"] == objetivo.capa_id, "id_de_capa_distinto")
    _exigir(d.get("name") == objetivo.capa_nombre, "nombre_de_capa_distinto")
    _exigir(d.get("type") == "Feature Layer", "tipo_de_capa_distinto")
    _exigir(d.get("geometryType") == "esriGeometryPolygon", "geometria_distinta")
    _extension(d.get("extent"), objetivo)
    if "spatialReference" in d:
        _referencia(d["spatialReference"], objetivo)
    campos = d.get("fields")
    _exigir(type(campos) is list and 0 < len(campos) <= 2048, "campos_ausentes_o_excesivos")
    nombres, oids = set(), []
    for c in campos:
        _exigir(type(c) is dict and _texto(c.get("name")), "campo_invalido")
        _exigir(c["name"] not in nombres, "campos_duplicados")
        nombres.add(c["name"])
        _exigir(_texto(c.get("type")) and c["type"].startswith("esriFieldType"), "tipo_de_campo_invalido")
        if c["type"] == "esriFieldTypeOID":
            oids.append(c["name"])
        if "length" in c:
            _exigir(_entero(c["length"]), "longitud_de_campo_invalida")
        if "nullable" in c:
            _exigir(type(c["nullable"]) is bool, "nulabilidad_invalida")
        if "domain" in c:
            _exigir(c["domain"] is None or type(c["domain"]) is dict, "dominio_invalido")
    _exigir(all(c in nombres for c in objetivo.campos_obligatorios), "campo_obligatorio_ausente")
    _exigir(len(oids) == 1, "campo_oid_ausente_o_ambiguo")
    for clave in ("objectIdField", "objectIdFieldName"):
        if clave in d:
            _exigir(d[clave] == oids[0], "campo_oid_contradictorio")
    return oids[0]


def inspeccionar_metadatos(respuesta: RespuestaHTTP, tipo: TipoMetadatos,
                           objetivo: ObjetivoArcGIS) -> ValidacionMetadatos:
    """El cuerpo debe proceder de un GET completado; hash sobre sus bytes exactos."""
    if (type(respuesta) is not RespuestaHTTP or type(tipo) is not TipoMetadatos or type(objetivo) is not ObjetivoArcGIS
            or type(respuesta.contenido) is not bytes):
        raise TypeError("Respuesta, tipo y objetivo tipados requeridos")
    diagnosticos, advertencias, datos, oid = [], [], {}, None
    try:
        _exigir(respuesta.codigo_http == 200, "http_no_200")
        mime = respuesta.cabeceras.get("content-type", "").split(";", 1)[0].strip().lower()
        _exigir(mime == "application/json", "tipo_mime_inesperado")
        for parametro in respuesta.cabeceras.get("content-type", "").split(";")[1:]:
            clave, _, valor = parametro.partition("=")
            if clave.strip().lower() == "charset":
                _exigir(valor.strip().strip('"').lower() in ("utf-8", "utf8"), "charset_no_admitido")
        datos = _json_acotado(respuesta.contenido)
        oid = _esquema(datos, tipo, objetivo, advertencias)
    except _Invalido as exc:
        diagnosticos.append(str(exc))
    except (ValueError, UnicodeError, RecursionError, OverflowError):
        diagnosticos.append("json_malformado_o_no_admitido")
    if diagnosticos:
        datos = {}  # No exponer cuerpos/error/HTML mediante un resultado público.
    return ValidacionMetadatos(tipo, EstadoMetadatos.REVISION if diagnosticos else EstadoMetadatos.COHERENTE,
        tuple(diagnosticos), tuple(advertencias), hashlib.sha256(respuesta.contenido).hexdigest(),
        len(respuesta.contenido), oid, datos)
