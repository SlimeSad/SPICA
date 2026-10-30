"""PASO 82-B: documentos inventados; ninguna fixture reproduce la capa real."""

from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
from threading import Event
import tracemalloc
import unittest
from unittest.mock import patch

import httpx

from test_inspeccion_arcgis import capa, codificar, objetivo, servicio
from test_transporte_http import Flujo
from spica.adquisicion.inspeccion_arcgis import (
    AlcanceMetadatos, EnsayoMetadatosArcGIS, EstadoJSON, EstadoMetadatos,
    IntentoMetadatos, LIMITE_METADATOS, LimitesInspeccion, TipoMetadatos, inspeccionar_metadatos,
)
from spica.adquisicion.transportes import RespuestaHTTP


def extensa(cantidad=2600, longitud_etiqueta=200):
    d = capa()
    d["drawingInfo"] = {"renderer": {"type": "uniqueValue", "uniqueValueInfos": [
        {"value": str(i), "label": "x" * longitud_etiqueta + str(i),
         "symbol": {"type": "esriSFS", "color": [1, 2, 3, 255]}}
        for i in range(cantidad)]}}
    return d


def contar_anterior(cuerpo):
    """Reproduce solo los dos conteos del WIP; no se usa en producción."""
    unidades, cadena, escape = 0, False, False
    for c in cuerpo.decode("utf-8-sig"):
        if cadena:
            if escape:
                escape = False
            elif c == "\\":
                escape = True
            elif c == '"':
                cadena = False
        elif c == '"':
            cadena, unidades = True, unidades + 1
        elif c in "[{,":
            unidades += 1
    def nodos(v):
        if type(v) is dict:
            return 1 + sum(1 + nodos(x) for x in v.values())
        if type(v) is list:
            return 1 + sum(nodos(x) for x in v)
        return 1
    return unidades, nodos(json.loads(cuerpo))


class InspectorExtensoTests(unittest.TestCase):
    def validar(self, d, **kw):
        cuerpo = d if type(d) is bytes else codificar(d)
        return inspeccionar_metadatos(RespuestaHTTP(200, {"content-type": "application/json"}, cuerpo),
                                      TipoMetadatos.CAPA, objetivo(), **kw)

    def revision(self, d, codigo, **kw):
        r = self.validar(d, **kw)
        self.assertEqual(r.estado, EstadoMetadatos.REVISION)
        self.assertIn(codigo, r.diagnosticos)
        self.assertEqual(dict(r.datos), {})
        self.assertIsNone(r.campo_oid)
        self.assertIsNone(r.coherencia_servicio_capa)
        return r

    def test_pequeno_sintaxis_completa_esquema_esencial(self):
        r = self.validar(capa())
        self.assertEqual(r.estado_json, EstadoJSON.COMPLETO)
        self.assertEqual(r.alcance, AlcanceMetadatos.ESENCIALES)
        self.assertEqual(r.secciones_omitidas, ())
        self.assertIn("semantica_arcgis_limitada_a_propiedades_esenciales", r.advertencias)
        self.assertIsNone(r.coherencia_servicio_capa)

    def test_resultado_parcial_no_habilita_continuar_por_etiqueta_antigua(self):
        v = self.validar(capa())
        fecha = datetime(2026, 10, 30, tzinfo=timezone.utc)
        intento = IntentoMetadatos(TipoMetadatos.CAPA, objetivo().url_capa, fecha, fecha,
                                  1, 200, "application/json", None, v, None)
        self.assertTrue(intento.permite_continuar)
        for estado in (EstadoJSON.NO_INICIADO, EstadoJSON.PARCIAL, EstadoJSON.INVALIDO):
            with self.subTest(estado=estado):
                self.assertFalse(replace(intento, validacion=replace(v, estado_json=estado)).permite_continuar)
        for alcance in (AlcanceMetadatos.INCOMPLETO, AlcanceMetadatos.INVALIDO):
            with self.subTest(alcance=alcance):
                self.assertFalse(replace(intento, validacion=replace(v, alcance=alcance)).permite_continuar)

    def test_dos_conteos_anteriores_no_son_equivalentes(self):
        self.assertNotEqual(*contar_anterior(b'{"a":0}'))
        self.assertNotEqual(*contar_anterior(b'["a","b"]'))

    def test_simbologia_sintetica_demuestra_bloqueo_anterior_y_solucion(self):
        cuerpo = codificar(extensa())
        self.assertLess(len(cuerpo), LIMITE_METADATOS)
        unidades, nodos = contar_anterior(cuerpo)
        self.assertGreater(unidades, 20_000)
        self.assertGreater(nodos, 20_000)
        r = self.validar(cuerpo)
        self.assertEqual(r.estado, EstadoMetadatos.COHERENTE)
        self.assertEqual(r.estado_json, EstadoJSON.COMPLETO)
        self.assertEqual(r.secciones_omitidas, ("drawingInfo",))
        self.assertNotIn("drawingInfo", r.datos)
        self.assertEqual(r.campo_oid, "objectid")
        self.assertEqual(r.estadisticas.nodos_documento, nodos)
        self.assertGreaterEqual(r.estadisticas.unidades_prelectura, nodos)
        self.assertLess(r.estadisticas.nodos_esenciales, 20_000)
        self.assertEqual(r.sha256, hashlib.sha256(cuerpo).hexdigest())

    def test_extenso_exacto_un_mib_no_omite_final_del_documento(self):
        cuerpo = codificar(extensa(longitud_etiqueta=320))
        self.assertGreater(len(cuerpo), LIMITE_METADATOS * 0.99)
        self.assertLess(len(cuerpo), LIMITE_METADATOS)
        cuerpo += b" " * (LIMITE_METADATOS - len(cuerpo))
        r = self.validar(cuerpo)
        self.assertEqual(r.estado_json, EstadoJSON.COMPLETO)
        self.assertEqual(r.bytes_recibidos, LIMITE_METADATOS)
        self.assertEqual(r.sha256, hashlib.sha256(cuerpo).hexdigest())
        self.revision(cuerpo[:-1] + b"!", "json_malformado_o_no_admitido")

    def test_maximo_de_lista_y_rechazo_del_siguiente(self):
        d = capa()
        d["opcional"] = [0] * 20_000
        self.assertEqual(self.validar(d).estado, EstadoMetadatos.COHERENTE)
        d["opcional"].append(0)
        r = self.revision(d, "json_demasiados_elementos")
        self.assertEqual(r.alcance, AlcanceMetadatos.INCOMPLETO)
        self.assertEqual(r.estado_json, EstadoJSON.PARCIAL)

    def test_maximo_de_propiedades_por_objeto(self):
        d = capa()
        d["opcional"] = {str(i): i for i in range(4096)}
        self.assertEqual(self.validar(d).estado, EstadoMetadatos.COHERENTE)
        d["opcional"]["otra"] = 0
        self.revision(d, "json_demasiados_elementos")

    def test_agotamiento_global_antes_de_materializar_json(self):
        d = capa()
        # 132.141 nodos: excede el presupuesto también con el conteo exacto.
        d["opcional"] = [{"a": 0, "b": 0, "c": 0, "d": 0, "e": 0}] * 12_000
        cuerpo = codificar(d)
        self.assertLess(len(cuerpo), LIMITE_METADATOS)
        with patch("spica.adquisicion.inspeccion_arcgis.inspector.json.loads", side_effect=AssertionError):
            r = self.revision(cuerpo, "json_presupuesto_documento_agotado")
        self.assertEqual(r.estado_json, EstadoJSON.PARCIAL)
        self.assertEqual(r.estadisticas.nodos_documento, 0)

    def test_presupuesto_exactamente_suficiente_y_una_unidad_menos(self):
        cuerpo = codificar(capa())
        unidades = self.validar(cuerpo).estadisticas.unidades_prelectura
        self.assertEqual(self.validar(cuerpo, limites=LimitesInspeccion(unidades_documento=unidades)).estado,
                         EstadoMetadatos.COHERENTE)
        self.revision(cuerpo, "json_presupuesto_documento_agotado",
                      limites=LimitesInspeccion(unidades_documento=unidades - 1))

    def test_presupuesto_critico_independiente_del_documento(self):
        d = capa()
        d["fields"][1]["domain"] = {"codedValues": [{"code": i, "name": str(i)} for i in range(4500)]}
        r = self.revision(d, "json_presupuesto_esenciales_agotado")
        self.assertEqual(r.estado_json, EstadoJSON.COMPLETO)
        self.assertEqual(r.alcance, AlcanceMetadatos.INCOMPLETO)

    def test_profundidad_maxima_y_siguiente_incluso_en_seccion_omitida(self):
        d = capa()
        v = 0
        for _ in range(31):
            v = [v]
        d["opcional"] = v
        self.assertEqual(self.validar(d).estado, EstadoMetadatos.COHERENTE)
        d["opcional"] = [v]
        self.revision(d, "json_demasiado_profundo")

    def test_duplicados_criticos_y_escapados(self):
        cuerpo = codificar(capa())
        for extra in (b',"id":7}', b',"\\u0069d":7}', b',"fields":[]}'):
            r = self.revision(cuerpo[:-1] + extra, "json_claves_duplicadas")
            self.assertEqual(r.estado_json, EstadoJSON.INVALIDO)

    def test_duplicados_en_seccion_omitida_tambien_se_rechazan(self):
        self.revision(codificar(capa())[:-1] + b',"drawingInfo":{"a":1,"a":2}}', "json_claves_duplicadas")

    def test_esenciales_ausentes_no_se_ocultan_por_simbologia(self):
        for clave in ("id", "name", "geometryType", "extent", "fields", "maxRecordCount", "supportedQueryFormats"):
            with self.subTest(clave=clave):
                d = extensa(100)
                del d[clave]
                r = self.validar(d)
                self.assertEqual(r.estado, EstadoMetadatos.REVISION)
                self.assertEqual(r.estado_json, EstadoJSON.COMPLETO)
                self.assertEqual(r.alcance, AlcanceMetadatos.INVALIDO)

    def test_geometria_crs_y_oid_contradictorios_en_capa_extensa(self):
        for clave, valor, codigo in (("geometryType", "esriGeometryPoint", "geometria_distinta"),
                                    ("spatialReference", {"wkid": 4326}, "referencia_espacial_distinta"),
                                    ("objectIdFieldName", "codi", "campo_oid_contradictorio")):
            with self.subTest(clave=clave):
                d = extensa(100)
                d[clave] = valor
                self.revision(d, codigo)

    def test_no_se_acepta_un_tipo_esri_inventado(self):
        d = capa()
        d["fields"][1]["type"] = "esriFieldTypeInventado"
        self.revision(d, "tipo_de_campo_invalido")

    def test_oid_ausente_ambiguo_o_doble_declaracion_contradictoria(self):
        sin_oid = capa()
        sin_oid["fields"][0]["type"] = "esriFieldTypeInteger"
        ambiguo = capa()
        ambiguo["fields"][1]["type"] = "esriFieldTypeOID"
        for d in (sin_oid, ambiguo):
            self.revision(d, "campo_oid_ausente_o_ambiguo")
        d = capa()
        d.update(objectIdField="objectid", objectIdFieldName="codi")
        self.revision(d, "campo_oid_contradictorio")

    def test_truncamiento_malformacion_y_documentos_concatenados(self):
        cuerpo = codificar(extensa(100))
        for b in (cuerpo[:-1], cuerpo[:200], cuerpo + b"{}", b'{"x": [1,]}', b'{"x": "sin cierre}'):
            with self.subTest(longitud=len(b)):
                r = self.revision(b, "json_malformado_o_no_admitido")
                self.assertEqual(r.estado_json, EstadoJSON.INVALIDO)

    def test_codificacion_invalida_y_escape_unicode_completo(self):
        self.revision(codificar(capa())[:-1] + b',"opcional":"\xff"}', "json_malformado_o_no_admitido")
        d = capa()
        d["opcional"] = "á😀\\\"[]{}:,"
        self.assertEqual(self.validar(json.dumps(d, ensure_ascii=True).encode()).estado, EstadoMetadatos.COHERENTE)

    def test_nan_infinity_y_desborde_en_secciones_omitidas(self):
        for numero in (b"NaN", b"Infinity", b"-Infinity", b"1e999"):
            with self.subTest(numero=numero):
                self.revision(codificar(capa())[:-1] + b',"opcional":' + numero + b"}", "json_numero_no_finito")

    def test_limite_de_cadena_en_seccion_omitida(self):
        d = capa()
        d["opcional"] = "x" * 65_536
        self.assertEqual(self.validar(d).estado, EstadoMetadatos.COHERENTE)
        d["opcional"] += "x"
        r = self.revision(d, "json_texto_excesivo")
        self.assertEqual(r.alcance, AlcanceMetadatos.INCOMPLETO)

    def test_http_200_error_arcgis_y_entidades_nunca_son_coherentes(self):
        for clave, valor, codigo in (("error", {"message": "token=SECRETO"}, "error_arcgis_en_respuesta"),
                                    ("features", [], "respuesta_de_entidades_no_admitida")):
            d = capa()
            d[clave] = valor
            r = self.revision(d, codigo)
            self.assertNotIn("SECRETO", repr(r))

    def test_bytes_excesivos_no_inician_parser(self):
        with (patch("spica.adquisicion.inspeccion_arcgis.inspector.json.loads", side_effect=AssertionError),
              patch("spica.adquisicion.inspeccion_arcgis.inspector.hashlib.sha256", side_effect=AssertionError)):
            r = self.revision(b" " * (LIMITE_METADATOS + 1), "limite_metadatos_excedido")
        self.assertEqual(r.estado_json, EstadoJSON.NO_INICIADO)
        self.assertIsNone(r.sha256)

    def test_cancelacion_previa_no_inicia_parser(self):
        evento = Event()
        evento.set()
        r = self.revision(capa(), "inspeccion_cancelada", cancelacion=evento)
        self.assertEqual(r.estado_json, EstadoJSON.NO_INICIADO)

    def test_cancelacion_durante_prelectura(self):
        evento = Event()
        with patch.object(evento, "is_set", side_effect=[False, False, False, True]):
            r = self.revision(codificar(extensa()), "inspeccion_cancelada", cancelacion=evento)
        self.assertEqual(r.estado_json, EstadoJSON.PARCIAL)
        self.assertLess(r.estadisticas.unidades_prelectura, 1000)

    def test_cancelacion_despues_del_parser_no_publica_datos(self):
        evento = Event()
        original = json.loads
        def cancelar(*a, **kw):
            d = original(*a, **kw)
            evento.set()
            return d
        with patch("spica.adquisicion.inspeccion_arcgis.inspector.json.loads", side_effect=cancelar):
            self.revision(capa(), "inspeccion_cancelada", cancelacion=evento)

    def test_topes_solo_se_pueden_reducir(self):
        limites = LimitesInspeccion()
        for nombre in limites.__dataclass_fields__:
            for valor in (0, True, getattr(limites, nombre) + 1):
                with self.subTest(nombre=nombre, valor=valor), self.assertRaises(ValueError):
                    replace(limites, **{nombre: valor})
        self.revision(capa(), "json_presupuesto_documento_agotado", limites=replace(limites, unidades_documento=10))

    def test_determinismo_y_secciones_omitidas_sin_duplicar_arbol(self):
        cuerpo = codificar(extensa())
        a, b = self.validar(cuerpo), self.validar(cuerpo)
        self.assertEqual(a, b)
        self.assertEqual(a.datos["id"], 7)
        with self.assertRaises(TypeError):
            a.datos["fields"][0]["type"] = "alterado"
        self.assertNotIn("uniqueValueInfos", repr(a))

    def test_memoria_medida_acotada_en_fixtures_adversas(self):
        # No es prueba de una cota universal de RSS; controla regresiones de pico
        # Python para texto extenso y para muchos objetos/valores pequeños.
        denso = capa()
        denso["opcional"] = [{"a": i, "b": [1, 2, 3]} for i in range(5000)]
        for d in (extensa(), denso):
            cuerpo = codificar(d)
            cuerpo += b" " * (LIMITE_METADATOS - len(cuerpo))
            tracemalloc.start()
            try:
                r = self.validar(cuerpo)
                _, pico = tracemalloc.get_traced_memory()
            finally:
                tracemalloc.stop()
            self.assertEqual(r.estado, EstadoMetadatos.COHERENTE)
            self.assertLess(pico, 32 * 1024 * 1024)


class CoherenciaServicioCapaTests(unittest.TestCase):
    def validar_servicio(self, d=None, o=None):
        return inspeccionar_metadatos(RespuestaHTTP(200, {"content-type": "application/json"}, codificar(d or servicio())),
                                      TipoMetadatos.SERVICIO, o or objetivo())

    def validar_capa(self, contexto, d=None):
        return inspeccionar_metadatos(RespuestaHTTP(200, {"content-type": "application/json"}, codificar(d or capa())),
                                      TipoMetadatos.CAPA, objetivo(), servicio=contexto)

    def test_coherencia_explicita_no_inventa_simultaneidad_ni_oid_estable(self):
        r = self.validar_capa(self.validar_servicio())
        self.assertTrue(r.coherencia_servicio_capa)
        self.assertEqual(r.campo_oid, "objectid")
        self.assertNotIn("oid_estable", r.datos)

    def test_contexto_de_otro_objetivo_o_invalido_no_se_acepta(self):
        o = objetivo()
        distinto = replace(o, campos_obligatorios=o.campos_obligatorios[:-1])
        for contexto in (self.validar_servicio(o=distinto), self.validar_servicio({"error": {"code": 500}})):
            r = self.validar_capa(contexto)
            self.assertIn("contexto_servicio_no_coherente", r.diagnosticos)
            self.assertIsNone(r.coherencia_servicio_capa)

    def test_geometria_anunciada_contradictoria_entre_servicio_y_capa(self):
        d = servicio()
        d["layers"][0]["geometryType"] = "esriGeometryPoint"
        r = self.validar_capa(self.validar_servicio(d))
        self.assertIn("servicio_capa_tipo_contradictorio", r.diagnosticos)

    def test_ambitos_distintos_no_obligan_igualdad_de_limites_o_extension(self):
        d = capa()
        d["maxRecordCount"] = 1000
        d["extent"]["xmax"] = 5
        d["capabilities"] = "Query"
        d["extent"]["spatialReference"] = {"wkid": 3857}
        r = self.validar_capa(self.validar_servicio(), d)
        self.assertEqual(r.estado, EstadoMetadatos.COHERENTE)
        self.assertTrue(r.coherencia_servicio_capa)

    def test_ensayo_mock_compara_ambas_respuestas_sin_red(self):
        def handler(request):
            d = capa() if request.url.path.endswith("/7") else servicio()
            return httpx.Response(200, headers={"Content-Type": "application/json"}, stream=Flujo((codificar(d),)))
        ensayo = EnsayoMetadatosArcGIS(objetivo(), transporte=httpx.MockTransport(handler))
        self.assertTrue(ensayo.consultar_servicio().permite_continuar)
        r = ensayo.consultar_capa()
        self.assertTrue(r.permite_continuar)
        self.assertTrue(r.validacion.coherencia_servicio_capa)
        self.assertEqual(sum(i.intentos_get for i in ensayo.historial), 2)


if __name__ == "__main__":
    unittest.main()
