"""Un único intercambio de fixture. No importa ni recibe un cliente de red."""

from datetime import datetime, timezone
from enum import Enum
import hashlib
from threading import Event

from .._json_acotado import _Invalido, _Incompleto, _exigir, leer_json
from ..vectorial.modelos import (
    CampoVector, EntidadVector, EstadoGeometria, LimitesVector, TipoCampo, _congelar,
)
from ..vectorial.validador import _valor
from .modelos import (
    EscenarioSintetico, EstadoEnsayo as EE, EstadoRecepcion as ER,
    EstadoValidacion as EV, PreparacionEnsayo, ResultadoEnsayo, SERVICIO, SolicitudSimulada,
)


class _Lectura(Enum):
    PARCIAL = "parcial"
    COMPLETO = "completo"


_CLAVES = {
    "features", "fields", "objectIdFieldName", "objectIdField", "exceededTransferLimit",
    "layerId", "serviceName", "geometryType", "spatialReference", "hasZ", "hasM",
    "displayFieldName", "fieldAliases",
}
_OID = CampoVector("objectid", TipoCampo.OID)


def _validar_sobre(d):
    _exigir(type(d) is dict, "sobre_no_es_objeto")
    _exigir("error" not in d, "error_arcgis_en_http_200")
    _exigir(set(d) <= _CLAVES, "propiedad_del_sobre_inesperada")
    if "layerId" in d:
        _exigir(type(d["layerId"]) is int and d["layerId"] == 7, "identidad_capa_incompatible")
    if "serviceName" in d:
        _exigir(d["serviceName"] == SERVICIO, "identidad_servicio_incompatible")
    if "geometryType" in d:
        _exigir(d["geometryType"] == "esriGeometryPolygon", "tipo_de_capa_incompatible")
    for k in ("hasZ", "hasM"):
        if k in d:
            _exigir(type(d[k]) is bool, "declaracion_dimensional_invalida")
    for k in ("objectIdFieldName", "objectIdField"):
        if k in d:
            _exigir(d[k] == "objectid", "descriptor_oid_incompatible")
    if "fields" in d:
        fs = d["fields"]
        _exigir(type(fs) is list and len(fs) == 1 and type(fs[0]) is dict, "campos_inesperados")
        f = fs[0]
        _exigir(f.get("name") == "objectid" and f.get("type") == TipoCampo.OID.value, "descriptor_oid_incompatible")
        if "nullable" in f:
            _exigir(f["nullable"] is False, "nulabilidad_oid_incompatible")
    if "exceededTransferLimit" in d:
        _exigir(type(d["exceededTransferLimit"]) is bool, "transfer_limit_no_booleano")
    features = d.get("features")
    _exigir(type(features) is list, "features_ausente_o_invalido")
    _exigir(len(features) <= 1, "multiples_entidades_no_admitidas")
    if not features:
        return ()
    f = features[0]
    _exigir(type(f) is dict, "entidad_malformada")
    _exigir("geometry" not in f, "geometria_prohibida_incluso_nula")
    _exigir(set(f) == {"attributes"} and type(f.get("attributes")) is dict, "atributos_ausentes_o_invalidos")
    a = f["attributes"]
    _exigir("objectid" in a, "objectid_ausente")
    _exigir(set(a) == {"objectid"}, "atributos_inesperados")
    _exigir(_valor(a["objectid"], _OID), "objectid_invalido")
    return (EntidadVector(a["objectid"], _congelar(a), EstadoGeometria.AUSENTE, None),)


class SimuladorEnsayo:
    """Instancia de un solo uso, secuencial y sin URL ejecutable o backend inyectable."""

    def __init__(self, preparacion: PreparacionEnsayo):
        if type(preparacion) is not PreparacionEnsayo:
            raise TypeError("preparacion_tipificada_requerida")
        self._solicitud = SolicitudSimulada(preparacion)
        self._consumido = False

    def ejecutar(self, escenario: EscenarioSintetico, *, cancelacion: Event | None = None,
                 evaluado_utc: datetime | None = None) -> ResultadoEnsayo:
        if self._consumido:
            raise RuntimeError("ensayo_ya_consumido_sin_reintento")
        if type(escenario) is not EscenarioSintetico or cancelacion is not None and type(cancelacion) is not Event:
            raise TypeError("escenario_y_cancelacion_tipificados_requeridos")
        fecha = evaluado_utc if evaluado_utc is not None else datetime.now(timezone.utc)
        # Validar fecha antes de consumir; no se ha simulado una respuesta.
        from ..nucleo.temporal import instante_utc
        fecha = instante_utc(fecha)
        self._consumido = True
        r = escenario.respuesta
        estado, recepcion, validacion, operaciones = EE.REVISION, ER.SIN_RESPUESTA, EV.NO_REALIZADA, 0
        codigo, rid, tamano, longitud, sha, cuerpo = None, None, None, None, None, None
        entidades, capa, exceso, json_completo, diagnosticos = (), None, None, False, ()

        def resultado():
            return ResultadoEnsayo(self._solicitud, fecha, estado, recepcion, validacion, operaciones,
                codigo, rid, tamano, longitud, sha, cuerpo, entidades, capa, exceso, json_completo, diagnosticos)

        if cancelacion is not None and cancelacion.is_set():
            estado, diagnosticos = EE.CANCELADO, ("cancelacion_antes_del_intercambio",)
            return resultado()
        operaciones = 1
        if escenario.fallo is not None:
            estado, diagnosticos = EE.FALLIDO, (escenario.fallo.value,)
            return resultado()
        codigo, rid, tamano, longitud = r.codigo_http, r.respuesta_id, len(r.contenido), r.longitud_declarada
        if tamano > self._solicitud.preparacion.max_bytes:
            recepcion, validacion, diagnosticos = ER.EXCEDIDA, EV.LIMITADA, ("limite_bytes_excedido",)
            return resultado()  # Sin copia retenida ni hash del cuerpo excesivo.
        cuerpo = r.contenido
        sha = hashlib.sha256(cuerpo).hexdigest()
        if r.interrumpida or not r.transferencia_completa or codigo == 206:
            recepcion, diagnosticos = ER.INCOMPLETA, ("respuesta_sintetica_parcial",)
            return resultado()
        if longitud is not None and longitud != tamano:
            recepcion, diagnosticos = ER.INCOMPLETA, ("content_length_discrepante",)
            return resultado()
        recepcion = ER.COMPLETA
        if codigo != 200:
            diagnosticos = ("redireccion_no_admitida" if 300 <= codigo < 400 else "estado_http_no_200",)
            return resultado()
        if escenario.content_encoding.lower() != "identity":
            diagnosticos = ("compresion_no_admitida",)
            return resultado()
        if escenario.content_type.lower().replace(" ", "") not in (
                "application/json", "application/json;charset=utf-8", "application/json;charset=utf8"):
            diagnosticos = ("content_type_no_admitido",)
            return resultado()
        limites = LimitesVector(max_bytes_respuesta=self._solicitud.preparacion.max_bytes,
            profundidad=16, unidades_documento=10_000, elementos_lista=64,
            propiedades_objeto=64, caracteres_cadena=4096, entidades_pagina=1)
        progreso = dict(unidades_prelectura=0, nodos_documento=0, profundidad_maxima=0)
        try:
            d = leer_json(cuerpo, limites, cancelacion, progreso, max_bytes=limites.max_bytes_respuesta,
                estados=_Lectura, codigo_bytes="limite_bytes_excedido", decimales_exactos=True)
            json_completo = True
            if type(d) is dict and type(d.get("layerId")) is int:
                capa = d["layerId"]  # Observación, incluso si contradice al candidato.
            entidades = _validar_sobre(d)
            capa, exceso = d.get("layerId"), d.get("exceededTransferLimit")
            notas = []
            if capa is None:
                notas.append("identidad_capa_no_declarada_en_fixture")
            if "fields" not in d:
                notas.append("descriptores_no_declarados_validacion_contra_contrato")
            if exceso is True:
                notas.append("seleccion_parcial_sin_segunda_operacion")
            if not entidades and exceso is True:
                raise _Invalido("vacio_con_continuacion_contradictoria")
            if cancelacion is not None and cancelacion.is_set():
                raise _Incompleto("inspeccion_cancelada")
            estado, validacion = (EE.COHERENTE, EV.COHERENTE) if entidades else (EE.VACIO, EV.VACIA)
            diagnosticos = tuple(notas)
        except _Incompleto as exc:
            if str(exc) == "inspeccion_cancelada":
                estado, diagnosticos = EE.CANCELADO, ("cancelacion_durante_validacion",)
            else:
                validacion, diagnosticos = EV.LIMITADA, (str(exc),)
        except _Invalido as exc:
            validacion, diagnosticos = EV.RECHAZADA, (str(exc),)
        except (ValueError, UnicodeError, RecursionError, OverflowError):
            validacion, diagnosticos = EV.RECHAZADA, ("json_invalido_o_no_admitido",)
        if estado not in (EE.COHERENTE, EE.VACIO):
            entidades = ()
        return resultado()
