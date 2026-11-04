"""Validación estructural de metadatos JSON acotados. Sin red, archivos o GIS."""

import hashlib
import json
import math
from threading import Event

from .._json_acotado import (
    _Invalido, _Incompleto, _presupuesto, _cancelar, _exigir, _recorrer, leer_json,
)
from ..transportes import RespuestaHTTP
from .modelos import (
    AlcanceMetadatos, EstadisticasJSON, EstadoJSON, EstadoMetadatos, LIMITE_METADATOS,
    LimitesInspeccion, ObjetivoArcGIS, TipoMetadatos, ValidacionMetadatos,
)


def _texto(valor):
    return type(valor) is str and bool(valor.strip()) and len(valor) <= 65_536


def _entero(valor, minimo=0):
    return type(valor) is int and valor >= minimo


def _numero(valor):
    return type(valor) in (int, float) and math.isfinite(valor)


def _json_acotado(cuerpo, limites, cancelacion, progreso):
    return leer_json(cuerpo, limites, cancelacion, progreso,
                     max_bytes=LIMITE_METADATOS, estados=EstadoJSON,
                     codigo_bytes="limite_metadatos_excedido")


_COMUNES = {"currentVersion", "maxRecordCount", "supportedQueryFormats", "capabilities", "advancedQueryCapabilities"}
_SERVICIO = _COMUNES | {"mapName", "serviceName", "layers", "spatialReference", "fullExtent", "units"}
_CAPA = _COMUNES | {"id", "name", "type", "geometryType", "extent", "spatialReference", "fields",
                   "sourceSpatialReference", "objectIdField", "objectIdFieldName"}


def _seleccionar(d, tipo, limites, cancelacion, progreso):
    _exigir(type(d) is dict, "json_no_es_objeto")
    _exigir("error" not in d, "error_arcgis_en_respuesta")
    _exigir("features" not in d and "featureSets" not in d, "respuesta_de_entidades_no_admitida")
    claves = _SERVICIO if tipo is TipoMetadatos.SERVICIO else _CAPA
    seleccion = {k: v for k, v in d.items() if k in claves}
    omitidas = tuple(k for k in d if k not in claves)
    for nodos in _recorrer(seleccion, limites, cancelacion):
        progreso["nodos_esenciales"] = nodos
        _presupuesto(nodos <= limites.nodos_esenciales, "json_presupuesto_esenciales_agotado")
    return seleccion, omitidas


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


def _referencia_fuente(d, advertencias):
    # El origen nativo y la representación de extent pueden usar CRS distintos.
    # Se comprueban identificadores declarados, sin certificar sus definiciones.
    _exigir(type(d) is dict, "referencia_fuente_invalida")
    _exigir(_entero(d.get("wkid"), 1), "wkid_fuente_ausente_o_invalido")
    if "latestWkid" in d:
        _exigir(_entero(d["latestWkid"], 1), "latest_wkid_fuente_invalido")
    advertencias.append("crs_fuente_sin_comprobacion_de_definicion_autoritativa")


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
    if "sourceSpatialReference" in d:
        _referencia_fuente(d["sourceSpatialReference"], advertencias)
    campos = d.get("fields")
    _exigir(type(campos) is list and 0 < len(campos) <= 2048, "campos_ausentes_o_excesivos")
    nombres, oids = set(), []
    for c in campos:
        _exigir(type(c) is dict and _texto(c.get("name")), "campo_invalido")
        _exigir(c["name"] not in nombres, "campos_duplicados")
        nombres.add(c["name"])
        _exigir(c.get("type") in ("esriFieldTypeSmallInteger", "esriFieldTypeInteger", "esriFieldTypeSingle",
            "esriFieldTypeDouble", "esriFieldTypeString", "esriFieldTypeDate", "esriFieldTypeOID",
            "esriFieldTypeGeometry", "esriFieldTypeBlob", "esriFieldTypeRaster", "esriFieldTypeGUID",
            "esriFieldTypeGlobalID", "esriFieldTypeXML", "esriFieldTypeBigInteger", "esriFieldTypeDateOnly",
            "esriFieldTypeTimeOnly", "esriFieldTypeTimestampOffset"), "tipo_de_campo_invalido")
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


def _contrastar_servicio(servicio, datos, objetivo, advertencias):
    _exigir(type(servicio) is ValidacionMetadatos and servicio.tipo is TipoMetadatos.SERVICIO
        and servicio.estado is EstadoMetadatos.COHERENTE and servicio.estado_json is EstadoJSON.COMPLETO
        and servicio.alcance is AlcanceMetadatos.ESENCIALES and servicio.objetivo == objetivo,
        "contexto_servicio_no_coherente")
    anunciada = next(c for c in servicio.datos["layers"] if c["id"] == datos["id"])
    _exigir(anunciada["name"] == datos["name"], "servicio_capa_nombre_contradictorio")
    for k in ("type", "geometryType"):
        if k in anunciada:
            _exigir(anunciada[k] == datos[k], "servicio_capa_tipo_contradictorio")
    # Ambos CRS se contrastaron contra el mismo par esperado. No exigir igualdad
    # de extensiones/límites/capacidades: pueden tener ámbitos distintos.
    if servicio.datos.get("currentVersion") != datos.get("currentVersion"):
        advertencias.append("version_software_diferente_o_no_comparable")


def inspeccionar_metadatos(respuesta: RespuestaHTTP, tipo: TipoMetadatos,
                           objetivo: ObjetivoArcGIS, *, limites: LimitesInspeccion | None = None,
                           cancelacion: Event | None = None,
                           servicio: ValidacionMetadatos | None = None) -> ValidacionMetadatos:
    """Sintaxis completa y esquema esencial; no valida toda la semántica ArcGIS.

    El cuerpo debe proceder de un GET completado; hash de esos bytes en memoria.
    Sin contexto de servicio no se afirma coherencia entre las dos respuestas.
    """
    if (type(respuesta) is not RespuestaHTTP or type(tipo) is not TipoMetadatos or type(objetivo) is not ObjetivoArcGIS
            or type(respuesta.contenido) is not bytes):
        raise TypeError("Respuesta, tipo y objetivo tipados requeridos")
    if (limites is not None and type(limites) is not LimitesInspeccion
            or cancelacion is not None and type(cancelacion) is not Event):
        raise TypeError("Límites y cancelación tipados requeridos")
    limites = limites if limites is not None else LimitesInspeccion()
    diagnosticos, advertencias, datos, oid, omitidas, coherencia = [], [], {}, None, (), None
    alcance = AlcanceMetadatos.INCOMPLETO
    progreso = dict(estado_json=EstadoJSON.NO_INICIADO, unidades_prelectura=0,
                    nodos_documento=0, profundidad_maxima=0, nodos_esenciales=0)
    try:
        _cancelar(cancelacion)
        _exigir(respuesta.codigo_http == 200, "http_no_200")
        mime = respuesta.cabeceras.get("content-type", "").split(";", 1)[0].strip().lower()
        _exigir(mime == "application/json", "tipo_mime_inesperado")
        for parametro in respuesta.cabeceras.get("content-type", "").split(";")[1:]:
            clave, _, valor = parametro.partition("=")
            if clave.strip().lower() == "charset":
                _exigir(valor.strip().strip('"').lower() in ("utf-8", "utf8"), "charset_no_admitido")
        documento = _json_acotado(respuesta.contenido, limites, cancelacion, progreso)
        datos, omitidas = _seleccionar(documento, tipo, limites, cancelacion, progreso)
        del documento  # No congelar ni duplicar simbología u otras secciones ajenas.
        oid = _esquema(datos, tipo, objetivo, advertencias)
        if tipo is TipoMetadatos.CAPA:
            if servicio is None:
                advertencias.append("coherencia_servicio_capa_no_comprobada")
            else:
                _contrastar_servicio(servicio, datos, objetivo, advertencias)
                coherencia = True
        advertencias.append("semantica_arcgis_limitada_a_propiedades_esenciales")
        if omitidas:
            advertencias.append("secciones_no_esenciales_no_evaluadas")
        _cancelar(cancelacion)
        alcance = AlcanceMetadatos.ESENCIALES
    except _Incompleto as exc:
        diagnosticos.append(str(exc))
    except _Invalido as exc:
        diagnosticos.append(str(exc))
        alcance = AlcanceMetadatos.INVALIDO
        if progreso["estado_json"] is EstadoJSON.PARCIAL:
            progreso["estado_json"] = EstadoJSON.INVALIDO
    except (ValueError, UnicodeError, RecursionError, OverflowError):
        diagnosticos.append("json_malformado_o_no_admitido")
        alcance = AlcanceMetadatos.INVALIDO
        progreso["estado_json"] = EstadoJSON.INVALIDO
    if diagnosticos:
        datos, oid, coherencia = {}, None, None  # Sin cuerpos/error/HTML ni evidencia contradictoria.
    estadisticas = EstadisticasJSON(*(progreso[k] for k in (
        "unidades_prelectura", "nodos_documento", "profundidad_maxima", "nodos_esenciales")))
    # Una llamada directa también está acotada: no recorrer para hash un cuerpo
    # que el transporte habría rechazado por tamaño. No inventar una huella.
    sha256 = (hashlib.sha256(respuesta.contenido).hexdigest()
              if len(respuesta.contenido) <= LIMITE_METADATOS else None)
    return ValidacionMetadatos(tipo, EstadoMetadatos.REVISION if diagnosticos else EstadoMetadatos.COHERENTE,
        tuple(diagnosticos), tuple(advertencias), sha256,
        len(respuesta.contenido), oid, datos, progreso["estado_json"], alcance, estadisticas,
        omitidas, coherencia, objetivo)
