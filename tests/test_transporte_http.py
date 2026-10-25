"""Pruebas sin red; todos los destinos .invalid son fixtures de MockTransport."""

from dataclasses import replace
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from spica.adquisicion.transportes import (
    ClienteHTTP, ConfiguracionHTTP, ErrorTransporteHTTP, TipoErrorHTTP,
)


class Flujo(httpx.SyncByteStream):
    def __init__(self, partes=(), error=None):
        self.partes = partes
        self.error = error
        self.leidas = 0
        self.cerrado = False

    def __iter__(self):
        for parte in self.partes:
            self.leidas += 1
            yield parte
        if self.error:
            raise self.error

    def close(self):
        self.cerrado = True


class TransporteHTTPTests(unittest.TestCase):
    ORIGEN = "https://prueba.invalid"

    def cliente(self, handler, **config):
        cliente = ClienteHTTP((self.ORIGEN,), ConfiguracionHTTP(**config),
                              transporte=httpx.MockTransport(handler))
        self.addCleanup(cliente.close)
        return cliente

    def respuesta(self, partes=(b"abc",), codigo=200, cabeceras=None):
        flujo = Flujo(partes)
        cliente = self.cliente(lambda request: httpx.Response(
            codigo, headers=cabeceras, stream=flujo))
        return cliente, flujo

    def test_get_parametros_cabeceras_y_timeouts(self):
        recibidas = []
        def handler(request):
            recibidas.append(request)
            return httpx.Response(200, headers={"Content-Type": "application/octet-stream"},
                                  stream=Flujo((b"ab", b"cd")))
        cliente = self.cliente(handler, timeout_conexion=1, timeout_lectura=2,
                               timeout_escritura=3, timeout_pool=4)
        respuesta = cliente.get(self.ORIGEN + "/recurso", parametros={"variable": " A/B ", "estacion": "001"})
        self.assertEqual(respuesta.contenido, b"abcd")
        self.assertEqual(respuesta.codigo_http, 200)
        self.assertEqual(respuesta.cabeceras["content-type"], "application/octet-stream")
        with self.assertRaises(TypeError):
            respuesta.cabeceras["x"] = "y"
        request = recibidas[0]
        self.assertEqual(request.method, "GET")
        self.assertEqual(dict(request.url.params), {"variable": " A/B ", "estacion": "001"})
        self.assertEqual(request.headers["accept-encoding"], "identity")
        self.assertEqual(request.extensions["timeout"], {"connect": 1, "read": 2, "write": 3, "pool": 4})

    def test_configuracion_explicita_tls_redirecciones_y_entorno(self):
        for tls in (True, False):
            with self.subTest(tls=tls), patch("spica.adquisicion.transportes.http.httpx.Client") as constructor:
                cliente = ClienteHTTP((self.ORIGEN,), ConfiguracionHTTP(verificar_tls=tls))
                opciones = constructor.call_args.kwargs
                self.assertIs(opciones["verify"], tls)
                self.assertIs(opciones["follow_redirects"], False)
                self.assertIs(opciones["trust_env"], False)
                cliente.close()

    def test_estados_http_sin_leer_cuerpos(self):
        casos = {401: TipoErrorHTTP.NO_AUTENTICADO, 403: TipoErrorHTTP.PROHIBIDO,
                 404: TipoErrorHTTP.NO_ENCONTRADO, 429: TipoErrorHTTP.LIMITE_SOLICITUDES,
                 500: TipoErrorHTTP.SERVIDOR, 503: TipoErrorHTTP.SERVIDOR,
                 400: TipoErrorHTTP.ESTADO_HTTP, 206: TipoErrorHTTP.RESPUESTA_PARCIAL}
        for codigo, tipo in casos.items():
            with self.subTest(codigo=codigo):
                cliente, flujo = self.respuesta(codigo=codigo)
                with self.assertRaises(ErrorTransporteHTTP) as contexto:
                    cliente.get(self.ORIGEN)
                self.assertEqual(contexto.exception.tipo, tipo)
                self.assertEqual(contexto.exception.codigo_http, codigo)
                self.assertEqual(flujo.leidas, 0)
                self.assertTrue(flujo.cerrado)

    def test_redirecciones_no_generan_segunda_peticion(self):
        for codigo in (301, 302, 307, 308):
            llamadas = []
            def handler(request):
                llamadas.append(request)
                return httpx.Response(codigo, headers={"Location": "https://otro.invalid/"}, stream=Flujo())
            with self.subTest(codigo=codigo):
                cliente = self.cliente(handler)
                with self.assertRaises(ErrorTransporteHTTP) as contexto:
                    cliente.get(self.ORIGEN)
                self.assertEqual(contexto.exception.tipo, TipoErrorHTTP.REDIRECCION)
                self.assertEqual(len(llamadas), 1)

    def test_destinos_no_autorizados_no_alcanzan_transporte(self):
        llamadas = []
        cliente = self.cliente(lambda request: llamadas.append(request))
        for url in ("https://otro.invalid", "http://prueba.invalid", "https://prueba.invalid:444",
                    "/relativa", "file:///archivo", "https://u:p@prueba.invalid", self.ORIGEN + "/#x"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                cliente.get(url)
        self.assertEqual(llamadas, [])

    def test_origenes_invalidos(self):
        for origenes in ((), self.ORIGEN, (self.ORIGEN + "/ruta",),
                         (self.ORIGEN + "/?x=1",), ("file:///archivo",)):
            with self.subTest(origenes=origenes), self.assertRaises(ValueError):
                ClienteHTTP(origenes)

    def test_configuracion_invalida(self):
        config = ConfiguracionHTTP()
        for campo in ("timeout_conexion", "timeout_lectura", "timeout_escritura", "timeout_pool"):
            for valor in (0, -1, True, float("inf"), float("nan"), "1"):
                with self.subTest(campo=campo, valor=valor), self.assertRaises(ValueError):
                    replace(config, **{campo: valor})
        for valor in (0, -1, True, 1.5):
            with self.subTest(limite=valor), self.assertRaises(ValueError):
                replace(config, max_bytes_respuesta=valor)
        with self.assertRaises(TypeError):
            replace(config, verificar_tls="si")

    def test_parametros_invalidos_no_alcanzan_transporte(self):
        llamadas = []
        cliente = self.cliente(lambda request: llamadas.append(request))
        for parametros in ({"x": 1}, {1: "x"}, "x=1"):
            with self.subTest(parametros=parametros), self.assertRaises(TypeError):
                cliente.get(self.ORIGEN, parametros=parametros)
        self.assertEqual(llamadas, [])

    def test_limite_por_cabecera_no_lee_cuerpo(self):
        for longitud in ("9", "9" * 5000):
            flujo = Flujo((b"grande",))
            cliente = self.cliente(lambda request: httpx.Response(
                200, headers={"Content-Length": longitud}, stream=flujo), max_bytes_respuesta=4)
            with self.subTest(longitud=longitud[:10]), self.assertRaises(ErrorTransporteHTTP) as contexto:
                cliente.get(self.ORIGEN)
            self.assertEqual(contexto.exception.tipo, TipoErrorHTTP.TAMANO_EXCEDIDO)
            self.assertEqual(flujo.leidas, 0)
            self.assertTrue(flujo.cerrado)

    def test_limite_incremental_interrumpe_flujo(self):
        for cabeceras in ({}, {"Content-Length": "1"}):
            flujo = Flujo((b"12345", b"no debe leerse"))
            cliente = self.cliente(lambda request: httpx.Response(
                200, headers=cabeceras, stream=flujo), max_bytes_respuesta=4)
            with self.subTest(cabeceras=cabeceras), self.assertRaises(ErrorTransporteHTTP) as contexto:
                cliente.get(self.ORIGEN)
            self.assertEqual(contexto.exception.tipo, TipoErrorHTTP.TAMANO_EXCEDIDO)
            self.assertEqual(flujo.leidas, 1)
            self.assertTrue(flujo.cerrado)

    def test_tamano_exacto_al_limite(self):
        cliente = self.cliente(lambda request: httpx.Response(
            200, headers={"Content-Length": "4"}, stream=Flujo((b"12", b"34"))), max_bytes_respuesta=4)
        self.assertEqual(cliente.get(self.ORIGEN).contenido, b"1234")

    def test_cuerpo_vacio(self):
        cliente, flujo = self.respuesta(partes=(), codigo=204)
        self.assertEqual(cliente.get(self.ORIGEN).contenido, b"")
        self.assertTrue(flujo.cerrado)

    def test_longitud_invalida_o_discrepante(self):
        for longitud in ("-1", "abc", "1, 1", "2", "4"):
            cliente, flujo = self.respuesta(cabeceras={"Content-Length": longitud})
            with self.subTest(longitud=longitud), self.assertRaises(ErrorTransporteHTTP) as contexto:
                cliente.get(self.ORIGEN)
            self.assertEqual(contexto.exception.tipo, TipoErrorHTTP.RESPUESTA_INVALIDA)
            self.assertTrue(flujo.cerrado)

    def test_compresion_rechazada_sin_descomprimir(self):
        cliente, flujo = self.respuesta(cabeceras={"Content-Encoding": "gzip"})
        with self.assertRaises(ErrorTransporteHTTP) as contexto:
            cliente.get(self.ORIGEN)
        self.assertEqual(contexto.exception.tipo, TipoErrorHTTP.RESPUESTA_INVALIDA)
        self.assertEqual(flujo.leidas, 0)
        self.assertTrue(flujo.cerrado)

    def test_errores_de_conexion_y_timeout_sin_reintentos(self):
        for clase, tipo in ((httpx.ConnectError, TipoErrorHTTP.CONEXION),
                            (httpx.ConnectTimeout, TipoErrorHTTP.TIMEOUT),
                            (httpx.ReadTimeout, TipoErrorHTTP.TIMEOUT),
                            (httpx.PoolTimeout, TipoErrorHTTP.TIMEOUT),
                            (httpx.WriteTimeout, TipoErrorHTTP.TIMEOUT),
                            (httpx.RemoteProtocolError, TipoErrorHTTP.TRANSPORTE)):
            llamadas = []
            def handler(request):
                llamadas.append(request)
                raise clase("detalle", request=request)
            cliente = self.cliente(handler)
            with self.subTest(clase=clase), self.assertRaises(ErrorTransporteHTTP) as contexto:
                cliente.get(self.ORIGEN)
            self.assertEqual(contexto.exception.tipo, tipo)
            self.assertEqual(len(llamadas), 1)

    def test_error_durante_lectura_cierra_flujo(self):
        for error, tipo in ((httpx.ReadTimeout("timeout"), TipoErrorHTTP.TIMEOUT),
                            (httpx.ReadError("fallo"), TipoErrorHTTP.TRANSPORTE)):
            flujo = Flujo((b"ab",), error)
            cliente = self.cliente(lambda request: httpx.Response(200, stream=flujo))
            with self.subTest(error=type(error)), self.assertRaises(ErrorTransporteHTTP) as contexto:
                cliente.get(self.ORIGEN)
            self.assertEqual(contexto.exception.tipo, tipo)
            self.assertTrue(flujo.cerrado)

    def test_contexto_cierra_cliente_y_no_permite_reutilizacion(self):
        cliente, _ = self.respuesta()
        with cliente:
            cliente.get(self.ORIGEN)
        with self.assertRaises(RuntimeError):
            cliente.get(self.ORIGEN)


if __name__ == "__main__":
    unittest.main()
