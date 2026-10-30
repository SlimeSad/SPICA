"""PASO 82: metadatos inventados y MockTransport; sin servidores institucionales."""

from contextlib import ExitStack
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import socket
import sys
from threading import Event
import unittest
from unittest.mock import patch

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from spica.adquisicion.almacenamiento import AlmacenRAW
from spica.adquisicion.inspeccion_arcgis import (
    EnsayoMetadatosArcGIS, EstadoMetadatos, LIMITE_METADATOS, ObjetivoArcGIS,
    TipoMetadatos, inspeccionar_metadatos,
)
from spica.adquisicion.transportes import RespuestaHTTP
from test_transporte_http import Flujo


CAMPOS = ("objectid", "codi", "codiunihoja", "etiqueta", "unidad", "tipo_unidad", "litologia", "descrip")


def objetivo():
    url = "https://fixture.invalid/arcgis/rest/services/SERV_SINTETICO/MapServer"
    return ObjetivoArcGIS(url, url + "/7", "SERV_SINTETICO", 7, "Litologia", 102100, 3857, CAMPOS)


def extension():
    return dict(xmin=0, ymin=0, xmax=10, ymax=10, spatialReference=dict(wkid=102100, latestWkid=3857))


def servicio():
    return dict(mapName="Mapa sintetico", serviceName="SERV_SINTETICO", currentVersion=10.9,
        layers=[dict(id=7, name="Litologia")], spatialReference=dict(wkid=102100, latestWkid=3857),
        fullExtent=extension(), units="esriMeters", maxRecordCount=2000,
        supportedQueryFormats="JSON, geoJSON, PBF", capabilities="Map,Query,Data")


def capa():
    return dict(id=7, name="Litologia", type="Feature Layer", geometryType="esriGeometryPolygon",
        extent=extension(), maxRecordCount=2000, supportedQueryFormats="JSON, geoJSON, PBF",
        capabilities="Map,Query,Data", advancedQueryCapabilities=dict(supportsPagination=True),
        fields=[dict(name=n, type="esriFieldTypeOID" if n == "objectid" else "esriFieldTypeString",
                     alias=n, nullable=True, domain=None, **({} if n == "objectid" else {"length": 250})) for n in CAMPOS])


def codificar(d):
    return json.dumps(d, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


class InspectorArcGISTests(unittest.TestCase):
    def validar(self, d, tipo=TipoMetadatos.SERVICIO, *, mime="application/json", codigo=200):
        cuerpo = d if type(d) is bytes else codificar(d)
        return inspeccionar_metadatos(RespuestaHTTP(codigo, {"content-type": mime}, cuerpo), tipo, objetivo())

    def invalido(self, d, esperado, tipo=TipoMetadatos.SERVICIO, **kwargs):
        r = self.validar(d, tipo, **kwargs)
        self.assertEqual(r.estado, EstadoMetadatos.REVISION)
        self.assertIn(esperado, r.diagnosticos)
        self.assertEqual(dict(r.datos), {})
        return r

    def test_servicio_valido_hash_y_datos_exactos(self):
        cuerpo = codificar(servicio())
        r = self.validar(cuerpo)
        self.assertEqual(r.estado, EstadoMetadatos.COHERENTE)
        self.assertEqual(r.sha256, hashlib.sha256(cuerpo).hexdigest())
        self.assertEqual(r.bytes_recibidos, len(cuerpo))
        self.assertEqual(r.datos["maxRecordCount"], 2000)

    def test_capa_valida_campos_tipos_oid_y_paginacion(self):
        r = self.validar(capa(), TipoMetadatos.CAPA)
        self.assertEqual(r.estado, EstadoMetadatos.COHERENTE)
        self.assertEqual(r.campo_oid, "objectid")
        self.assertEqual(tuple(c["name"] for c in r.datos["fields"]), CAMPOS)
        self.assertEqual(r.datos["fields"][0]["type"], "esriFieldTypeOID")
        self.assertTrue(r.datos["advancedQueryCapabilities"]["supportsPagination"])

    def test_http_200_con_error_arcgis_no_revela_mensaje(self):
        r = self.invalido({"error": {"code": 499, "message": "token=SECRETO_SINTETICO"}}, "error_arcgis_en_respuesta")
        self.assertNotIn("SECRETO_SINTETICO", repr(r))

    def test_json_malformado_y_html(self):
        for cuerpo in (b'{"layers":', b"<html>login sintetico</html>", b"\xff\xfe"):
            with self.subTest(cuerpo=cuerpo):
                self.invalido(cuerpo, "json_malformado_o_no_admitido")

    def test_tipo_mime_inesperado(self):
        for mime in ("text/html", "text/plain", "application/octet-stream", ""):
            with self.subTest(mime=mime):
                self.invalido(servicio(), "tipo_mime_inesperado", mime=mime)

    def test_content_type_con_charset_sin_normalizar_cuerpo(self):
        self.assertEqual(self.validar(servicio(), mime="application/json; charset=UTF-8").estado, EstadoMetadatos.COHERENTE)
        self.invalido(servicio(), "charset_no_admitido", mime="application/json;charset=latin1")

    def test_servicio_distinto(self):
        d = servicio()
        d["serviceName"] = "OTRO_SERVICIO"
        self.invalido(d, "servicio_distinto")

    def test_mapname_descriptivo_no_se_confunde_con_identidad_del_servicio(self):
        d = servicio()
        del d["serviceName"]
        r = self.validar(d)
        self.assertEqual(r.estado, EstadoMetadatos.COHERENTE)
        self.assertIn("identidad_servicio_ligada_a_ruta_y_capas_no_a_mapname", r.advertencias)

    def test_capa_anunciada_ausente_y_nombre_distinto(self):
        for capas, codigo in (([dict(id=8, name="Litologia")], "capa_prioritaria_ausente"),
                              ([dict(id=7, name="Otra")], "nombre_de_capa_distinto")):
            d = servicio()
            d["layers"] = capas
            self.invalido(d, codigo)

    def test_capa_id_nombre_tipo_y_geometria_distintos(self):
        for k, valor, codigo in (("id", 8, "id_de_capa_distinto"), ("id", True, "id_de_capa_distinto"),
                                 ("name", "Otra", "nombre_de_capa_distinto"),
                                 ("type", "Group Layer", "tipo_de_capa_distinto"),
                                 ("geometryType", "esriGeometryPoint", "geometria_distinta")):
            d = capa()
            d[k] = valor
            self.invalido(d, codigo, TipoMetadatos.CAPA)

    def test_referencia_espacial_ausente(self):
        d = servicio()
        del d["spatialReference"]
        self.invalido(d, "referencia_espacial_ausente")
        d = capa()
        del d["extent"]["spatialReference"]
        self.invalido(d, "referencia_espacial_ausente", TipoMetadatos.CAPA)

    def test_referencias_contradictorias_de_raiz_y_extension(self):
        d = servicio()
        d["spatialReference"]["latestWkid"] = 4326
        self.invalido(d, "latest_wkid_contradictorio")
        d = capa()
        d["extent"]["spatialReference"]["wkid"] = 4326
        self.invalido(d, "referencia_espacial_distinta", TipoMetadatos.CAPA)

    def test_wkid_sin_latest_no_inventa_el_valor_ausente(self):
        d = servicio()
        del d["spatialReference"]["latestWkid"]
        r = self.validar(d)
        self.assertEqual(r.estado, EstadoMetadatos.COHERENTE)
        self.assertNotIn("latestWkid", r.datos["spatialReference"])

    def test_extension_ausente_invertida_o_no_numerica(self):
        for valor, codigo in ((None, "extension_ausente"), (dict(extension(), xmin=20), "extension_invertida"),
                              (dict(extension(), ymax="10"), "extension_invalida")):
            d = servicio()
            d["fullExtent"] = valor
            self.invalido(d, codigo)

    def test_campos_obligatorios_ausentes_no_se_reconstruyen(self):
        for nombre in CAMPOS:
            d = capa()
            d["fields"] = [c for c in d["fields"] if c["name"] != nombre]
            self.invalido(d, "campo_obligatorio_ausente", TipoMetadatos.CAPA)

    def test_tipos_de_campos_longitudes_y_dominios_invalidos(self):
        for k, valor, codigo in (("type", 42, "tipo_de_campo_invalido"), ("length", True, "longitud_de_campo_invalida"),
                                 ("nullable", "si", "nulabilidad_invalida"), ("domain", [], "dominio_invalido")):
            d = capa()
            d["fields"][1][k] = valor
            self.invalido(d, codigo, TipoMetadatos.CAPA)

    def test_objectid_declarado_contradice_tipo_oid(self):
        d = capa()
        d["objectIdField"] = "codi"
        self.invalido(d, "campo_oid_contradictorio", TipoMetadatos.CAPA)

    def test_campos_y_capas_duplicados(self):
        d = capa()
        d["fields"].append(d["fields"][0])
        self.invalido(d, "campos_duplicados", TipoMetadatos.CAPA)
        d = servicio()
        d["layers"].append(d["layers"][0])
        self.invalido(d, "capas_duplicadas")

    def test_max_record_count_invalido_y_no_es_conteo_total(self):
        for valor in (None, 0, -1, True, "2000", 2.5):
            d = servicio()
            d["maxRecordCount"] = valor
            self.invalido(d, "max_record_count_invalido")
        r = self.validar(servicio())
        self.assertIn("sin_comprobacion_de_entidades_o_completitud", r.advertencias)

    def test_paginacion_anunciada_falsa_ausente_o_tipo_incorrecto(self):
        for valor in (True, False):
            d = capa()
            d["advancedQueryCapabilities"]["supportsPagination"] = valor
            r = self.validar(d, TipoMetadatos.CAPA)
            self.assertIs(r.datos["advancedQueryCapabilities"]["supportsPagination"], valor)
        d = capa()
        del d["advancedQueryCapabilities"]
        self.assertIn("paginacion_no_anunciada", self.validar(d, TipoMetadatos.CAPA).advertencias)
        d["advancedQueryCapabilities"] = {"supportsPagination": 1}
        self.invalido(d, "paginacion_de_tipo_invalido", TipoMetadatos.CAPA)

    def test_esquema_obligatorio_del_servicio(self):
        for campo, codigo in (("layers", "lista_de_capas_ausente_o_excesiva"), ("mapName", "nombre_de_mapa_ausente"),
                               ("units", "unidades_no_declaradas"), ("supportedQueryFormats", "formatos_de_consulta_ausentes")):
            d = servicio()
            del d[campo]
            self.invalido(d, codigo)

    def test_entidades_no_se_aceptan_como_metadatos(self):
        d = servicio()
        d["features"] = []
        self.invalido(d, "respuesta_de_entidades_no_admitida")

    def test_json_no_es_objeto(self):
        for d in ([], None, 1, "texto"):
            self.invalido(d, "json_no_es_objeto")

    def test_json_duplicado_no_finito_y_numero_excesivo(self):
        for cuerpo, codigo in ((b'{"a":1,"a":2}', "json_claves_duplicadas"),
                               (b'{"a":NaN}', "json_numero_no_finito"), (b'{"a":1e999}', "json_numero_no_finito"),
                               (b'{"a":' + b"9" * 40 + b"}", "json_entero_excesivo")):
            self.invalido(cuerpo, codigo)

    def test_json_profundo_excesivo_y_texto_excesivo(self):
        self.invalido(b"[" * 33 + b"0" + b"]" * 33, "json_demasiado_profundo")
        self.invalido(codificar({"a": "x" * 65_537}), "json_texto_excesivo")
        self.invalido(b"[" + b"0," * 20_001 + b"0]", "json_demasiados_elementos")

    def test_determinismo_inmutabilidad_y_ninguna_io_en_inspector(self):
        respuesta = RespuestaHTTP(200, {"content-type": "application/json"}, codificar(servicio()))
        with patch("builtins.open", side_effect=AssertionError("I/O prohibida")), patch("sqlite3.connect", side_effect=AssertionError("SQLite prohibido")):
            a = inspeccionar_metadatos(respuesta, TipoMetadatos.SERVICIO, objetivo())
            b = inspeccionar_metadatos(respuesta, TipoMetadatos.SERVICIO, objetivo())
        self.assertEqual(a, b)
        with self.assertRaises(TypeError):
            a.datos["maxRecordCount"] = 1


class EnsayoArcGISTests(unittest.TestCase):
    def setUp(self):
        self.peticiones, self.flujos = [], []
        self.instante = datetime(2026, 10, 30, 12, tzinfo=timezone.utc)

    def ensayo(self, *, servicio_datos=None, capa_datos=None, codigo=200, cabeceras=None, error=None,
               cuerpo=None, cancelacion=None):
        def handler(r):
            self.peticiones.append(r)
            if error:
                raise error
            d = (capa_datos or capa()) if r.url.path.endswith("/7") else (servicio_datos or servicio())
            datos = cuerpo if cuerpo is not None else codificar(d)
            flujo = Flujo((datos[i:i+8192] for i in range(0, len(datos), 8192)))
            self.flujos.append(flujo)
            return httpx.Response(codigo, headers=cabeceras if cabeceras is not None else
                                  {"Content-Type": "application/json", "Content-Length": str(len(datos))}, stream=flujo)
        return EnsayoMetadatosArcGIS(objetivo(), transporte=httpx.MockTransport(handler),
                                     cancelacion=cancelacion, reloj=lambda: self.instante)

    def test_dos_get_exclusivos_sin_query_de_entidades_ni_credenciales(self):
        e = self.ensayo()
        primero, segundo = e.consultar_servicio(), e.consultar_capa()
        self.assertTrue(primero.permite_continuar)
        self.assertTrue(segundo.permite_continuar)
        self.assertEqual((primero.intentos_get, segundo.intentos_get), (1, 1))
        self.assertEqual(len(e.historial), 2)
        for r, ruta in zip(self.peticiones, (objetivo().url_servicio, objetivo().url_capa)):
            self.assertEqual(r.method, "GET")
            self.assertEqual(str(r.url).split("?", 1)[0], ruta)
            self.assertEqual(dict(r.url.params), {"f": "json"})
            for h in ("cookie", "authorization", "proxy-authorization"):
                self.assertNotIn(h, r.headers)
            self.assertEqual(r.headers["accept-encoding"], "identity")
            self.assertEqual(r.extensions["timeout"], dict(connect=10, read=30, write=30, pool=10))
        self.assertTrue(all(f.cerrado for f in self.flujos))

    def test_cookie_recibida_no_se_envia_a_la_segunda_peticion(self):
        e = self.ensayo(cabeceras={"Content-Type": "application/json", "Set-Cookie": "sesion=SECRETO_SINTETICO; Path=/"})
        e.consultar_servicio()
        e.consultar_capa()
        self.assertEqual(len(self.peticiones), 2)
        self.assertTrue(all("cookie" not in r.headers for r in self.peticiones))
        self.assertNotIn("SECRETO_SINTETICO", repr(e.historial))

    def test_servicio_invalido_impide_segundo_get_y_no_permite_repetir(self):
        d = servicio()
        d["serviceName"] = "OTRO"
        e = self.ensayo(servicio_datos=d)
        r = e.consultar_servicio()
        self.assertFalse(r.permite_continuar)
        with self.assertRaises(RuntimeError):
            e.consultar_capa()
        with self.assertRaises(RuntimeError):
            e.consultar_servicio()
        self.assertEqual(len(self.peticiones), 1)

    def test_no_consulta_capa_antes_del_servicio_ni_repite_capa(self):
        e = self.ensayo()
        with self.assertRaises(RuntimeError):
            e.consultar_capa()
        self.assertEqual(self.peticiones, [])
        e.consultar_servicio()
        e.consultar_capa()
        with self.assertRaises(RuntimeError):
            e.consultar_capa()
        self.assertEqual(len(self.peticiones), 2)

    def test_respuesta_mayor_de_un_mib_sin_hash_de_respuesta_completa(self):
        e = self.ensayo(cuerpo=b" " * (LIMITE_METADATOS + 1), cabeceras={"Content-Type": "application/json"})
        r = e.consultar_servicio()
        self.assertEqual(r.error, "tamano_excedido")
        self.assertIsNone(r.cuerpo)
        self.assertIsNone(r.validacion)
        self.assertTrue(self.flujos[0].cerrado)
        self.assertEqual(len(self.peticiones), 1)

    def test_tamano_exacto_de_un_mib_admitido(self):
        d = codificar(servicio())
        cuerpo = d + b" " * (LIMITE_METADATOS - len(d))
        r = self.ensayo(cuerpo=cuerpo).consultar_servicio()
        self.assertTrue(r.permite_continuar)
        self.assertEqual(r.validacion.bytes_recibidos, LIMITE_METADATOS)

    def test_content_length_incorrecto_no_se_reintenta(self):
        e = self.ensayo(cabeceras={"Content-Type": "application/json", "Content-Length": "9999"})
        r = e.consultar_servicio()
        self.assertEqual(r.error, "respuesta_invalida")
        self.assertIsNone(r.validacion)
        self.assertEqual(r.intentos_get, 1)
        with self.assertRaises(RuntimeError):
            e.consultar_capa()

    def test_redireccion_y_respuesta_parcial_no_generan_otra_peticion(self):
        for codigo, error in ((302, "redireccion"), (206, "respuesta_parcial")):
            with self.subTest(codigo=codigo):
                e = self.ensayo(codigo=codigo, cabeceras={"Location": "https://otro.invalid"})
                r = e.consultar_servicio()
                self.assertEqual(r.error, error)
                self.assertEqual(r.codigo_http, codigo)
                self.assertEqual(r.intentos_get, 1)
        self.assertEqual(len(self.peticiones), 2)

    def test_http_401_403_404_429_y_5xx_un_intento(self):
        for codigo in (401, 403, 404, 429, 500, 503):
            with self.subTest(codigo=codigo):
                r = self.ensayo(codigo=codigo).consultar_servicio()
                self.assertIsNotNone(r.error)
                self.assertEqual(r.codigo_http, codigo)
                self.assertEqual(r.intentos_get, 1)
        self.assertEqual(len(self.peticiones), 6)

    def test_error_tls_conexion_y_timeout_sin_reintentos(self):
        for exc, codigo in ((httpx.ConnectError("certificate verify failed; token=SECRETO"), "tls"),
                            (httpx.ConnectError("fallo sintetico"), "conexion"),
                            (httpx.ReadTimeout("fallo sintetico"), "timeout")):
            with self.subTest(codigo=codigo):
                r = self.ensayo(error=exc).consultar_servicio()
                self.assertEqual(r.error, codigo)
                self.assertEqual(r.intentos_get, 1)
                self.assertNotIn("SECRETO", repr(r))
                self.assertIsNone(r.validacion)

    def test_compresion_se_rechaza(self):
        r = self.ensayo(cabeceras={"Content-Encoding": "gzip"}).consultar_servicio()
        self.assertEqual(r.error, "respuesta_invalida")
        self.assertIsNone(r.validacion)

    def test_cancelacion_antes_de_get_no_alcanza_transporte(self):
        evento = Event()
        evento.set()
        r = self.ensayo(cancelacion=evento).consultar_servicio()
        self.assertEqual(r.error, "cancelado_antes_del_get")
        self.assertEqual(r.intentos_get, 0)
        self.assertEqual(self.peticiones, [])

    def test_cancelacion_entre_servicio_y_capa_no_envia_segundo_get(self):
        evento = Event()
        e = self.ensayo(cancelacion=evento)
        e.consultar_servicio()
        evento.set()
        r = e.consultar_capa()
        self.assertEqual(r.intentos_get, 0)
        self.assertEqual(len(self.peticiones), 1)

    def test_interrupcion_durante_lectura_no_tiene_hash_completo(self):
        flujo = Flujo((b'{"mapName":',), httpx.ReadError("fallo sintetico"))
        llamadas = []
        def handler(r):
            llamadas.append(r)
            return httpx.Response(200, headers={"Content-Type": "application/json"}, stream=flujo)
        e = EnsayoMetadatosArcGIS(objetivo(), transporte=httpx.MockTransport(handler))
        r = e.consultar_servicio()
        self.assertEqual(r.error, "transporte")
        self.assertIsNone(r.validacion)
        self.assertIsNone(r.cuerpo)
        self.assertTrue(flujo.cerrado)
        self.assertEqual(len(llamadas), 1)

    def test_cancelacion_durante_lectura_cierra_sin_reintentar(self):
        evento = Event()
        def partes():
            yield b" " * 65_536
            evento.set()
            yield b" " * 65_536
        flujo = Flujo(partes())
        llamadas = []
        def handler(r):
            llamadas.append(r)
            return httpx.Response(200, headers={"Content-Type": "application/json"}, stream=flujo)
        e = EnsayoMetadatosArcGIS(objetivo(), transporte=httpx.MockTransport(handler), cancelacion=evento)
        r = e.consultar_servicio()
        self.assertEqual(r.error, "cancelado")
        self.assertIsNone(r.validacion)
        self.assertTrue(flujo.cerrado)
        self.assertEqual(len(llamadas), 1)

    def test_respuesta_completa_pero_invalida_tiene_hash_solo_de_esos_bytes(self):
        cuerpo = b'{"error":{"message":"no autorizado"}}'
        r = self.ensayo(cuerpo=cuerpo).consultar_servicio()
        self.assertFalse(r.permite_continuar)
        self.assertEqual(r.validacion.sha256, hashlib.sha256(cuerpo).hexdigest())
        self.assertEqual(r.validacion.bytes_recibidos, len(cuerpo))

    def test_no_raw_sqlite_archivos_operativos_ni_red_real(self):
        e = self.ensayo()
        with ExitStack() as stack:
            mocks = [stack.enter_context(patch("sqlite3.connect", side_effect=AssertionError("SQLite prohibido"))),
                     stack.enter_context(patch.object(socket.socket, "connect", side_effect=AssertionError("red prohibida")))]
            for metodo in ("incorporar", "verificar", "recuperar", "metadatos"):
                mocks.append(stack.enter_context(patch.object(AlmacenRAW, metodo, side_effect=AssertionError("RAW prohibido"))))
            self.assertTrue(e.consultar_servicio().permite_continuar)
            self.assertTrue(e.consultar_capa().permite_continuar)
            for m in mocks:
                m.assert_not_called()

    def test_objetivos_inseguros_se_rechazan_antes_de_crear_cliente(self):
        o = objetivo()
        for kwargs in ({"url_servicio": o.url_servicio.replace("https:", "http:")},
                       {"url_capa": o.url_capa + "/query"}, {"url_capa": o.url_capa.replace("fixture.invalid", "otro.invalid")},
                       {"url_servicio": o.url_servicio + "?token=SECRETO_SINTETICO"}, {"capa_id": True}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError) as c:
                replace(o, **kwargs)
            self.assertNotIn("SECRETO_SINTETICO", str(c.exception))


if __name__ == "__main__":
    unittest.main()
