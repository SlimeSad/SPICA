"""Reintentos con MockTransport, relojes y esperas simulados; nunca usa la red."""

from dataclasses import replace
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import shutil
import ssl
import sys
from threading import Event
import unittest
from unittest.mock import patch
from uuid import uuid4

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from spica.adquisicion.transportes import (
    ClienteHTTP, ErrorDescargaArchivo, ErrorTransporteHTTP, PoliticaReintentos, TipoErrorHTTP,
)
from spica.adquisicion.transportes.reintentos import interpretar_retry_after
from test_transporte_http import Flujo


class ReintentosHTTPTests(unittest.TestCase):
    ORIGEN = "https://prueba.invalid"
    AHORA = datetime(2026, 1, 1, tzinfo=timezone.utc)

    def setUp(self):
        proyecto = Path(__file__).resolve().parents[1]
        self.raiz = proyecto / (".suadc-test-" + uuid4().hex)
        self.raiz.mkdir(mode=0o755)
        assert self.raiz.resolve().is_relative_to(proyecto)
        self.addCleanup(shutil.rmtree, self.raiz)
        self.llamadas = []
        self.esperas = []
        self.flujos = []

    def cliente(self, secuencia, politica=None, **opciones):
        pasos = iter(secuencia)
        def handler(request):
            self.llamadas.append(request)
            paso = next(pasos)
            if isinstance(paso, BaseException):
                raise paso
            if callable(paso):
                return paso(request)
            codigo, cabeceras, partes = paso
            flujo = Flujo(partes)
            self.flujos.append(flujo)
            return httpx.Response(codigo, headers=cabeceras, stream=flujo)
        opciones.setdefault("espera", self.esperas.append)
        opciones.setdefault("reloj", lambda: self.AHORA)
        cliente = ClienteHTTP((self.ORIGEN,), transporte=httpx.MockTransport(handler),
            politica_reintentos=politica or PoliticaReintentos(max_intentos=3, jitter=0), **opciones)
        self.addCleanup(cliente.close)
        return cliente

    def descargar(self, cliente):
        return cliente.descargar(self.ORIGEN + "/archivo?token=secreto", self.raiz, "archivo.bin",
                                  max_bytes=100, tamano_bloque=2)

    def test_exito_primer_intento(self):
        cliente = self.cliente([(200, {}, (b"abc",))])
        self.assertEqual(cliente.get(self.ORIGEN).contenido, b"abc")
        self.assertEqual(len(self.llamadas), 1)
        self.assertEqual(self.esperas, [])
        self.assertEqual(cliente.historial_intentos[0].resultado, "exito")
        self.assertEqual(cliente.historial_intentos[0].numero, 1)

    def test_todos_los_estados_transitorios_recuperan(self):
        for codigo in (408, 429, 500, 502, 503, 504):
            with self.subTest(codigo=codigo):
                self.llamadas.clear()
                self.esperas.clear()
                cliente = self.cliente([(codigo, {}, ()), (200, {}, (b"ok",))])
                self.assertEqual(cliente.get(self.ORIGEN).contenido, b"ok")
                self.assertEqual(len(self.llamadas), 2)
                self.assertEqual(self.esperas, [1])
                self.assertEqual(cliente.historial_intentos[0].codigo_http, codigo)
                self.assertEqual(cliente.historial_intentos[-1].resultado, "exito")
                self.assertTrue(all(f.cerrado for f in self.flujos))

    def test_429_retry_after_segundos(self):
        cliente = self.cliente([(429, {"Retry-After": "5"}, ()), (200, {}, ())])
        cliente.get(self.ORIGEN)
        self.assertEqual(self.esperas, [5])
        self.assertEqual(cliente.historial_intentos[0].espera, 5)

    def test_503_retry_after_fecha_http(self):
        cliente = self.cliente([(503, {"Retry-After": "Thu, 01 Jan 2026 00:00:07 GMT"}, ()), (200, {}, ())])
        cliente.get(self.ORIGEN)
        self.assertEqual(self.esperas, [7])

    def test_interpretacion_retry_after(self):
        casos = ((None, None), ("", None), ("-1", None), ("1.5", None), ("basura", None),
                 ("0003", 3), ("0", 0), ("Wed, 31 Dec 2025 23:00:00 GMT", 0),
                 ("Thursday, 01-Jan-26 00:00:07 GMT", 7), ("Thu Jan  1 00:00:07 2026", 7))
        for valor, esperado in casos:
            with self.subTest(valor=valor):
                self.assertEqual(interpretar_retry_after(valor, self.AHORA), esperado)

    def test_retry_after_invalido_y_pasado_usan_retroceso(self):
        for valor in ("invalido", "Wed, 31 Dec 2025 23:00:00 GMT", "-2"):
            self.esperas.clear()
            cliente = self.cliente([(429, {"Retry-After": valor}, ()), (200, {}, ())])
            cliente.get(self.ORIGEN)
            self.assertEqual(self.esperas, [1])

    def test_retry_after_excesivo_no_reintenta_antes_del_plazo(self):
        for valor in ("61", "9" * 5000, "Thu, 01 Jan 2026 00:02:00 GMT"):
            with self.subTest(valor=valor[:30]):
                self.llamadas.clear()
                cliente = self.cliente([(429, {"Retry-After": valor}, ())])
                with self.assertRaises(ErrorTransporteHTTP) as contexto:
                    cliente.get(self.ORIGEN)
                self.assertFalse(contexto.exception.agotados)
                self.assertEqual(cliente.historial_intentos[-1].resultado, "limite_espera")
                self.assertEqual(len(self.llamadas), 1)
                self.assertEqual(self.esperas, [])

    def test_agotamiento_explicito_sin_espera_final(self):
        cliente = self.cliente([(503, {}, ())] * 3)
        with self.assertRaises(ErrorTransporteHTTP) as contexto:
            cliente.get(self.ORIGEN)
        error = contexto.exception
        self.assertTrue(error.agotados)
        self.assertEqual(error.intentos, 3)
        self.assertEqual(error.codigo_http, 503)
        self.assertEqual(self.esperas, [1, 2])
        self.assertEqual(error.historial, cliente.historial_intentos)
        self.assertEqual(error.historial[-1].resultado, "agotado")

    def test_estados_definitivos_no_reintentan(self):
        for codigo in (401, 403, 404, 400, 501, 505, 206, 302):
            self.llamadas.clear()
            cliente = self.cliente([(codigo, {}, ())])
            with self.subTest(codigo=codigo), self.assertRaises(ErrorTransporteHTTP) as contexto:
                cliente.get(self.ORIGEN)
            self.assertFalse(contexto.exception.agotados)
            self.assertEqual(len(self.llamadas), 1)
            self.assertEqual(self.esperas, [])

    def test_conexion_timeout_y_lectura_recuperables(self):
        for clase in (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout,
                      httpx.WriteTimeout, httpx.PoolTimeout, httpx.ReadError,
                      httpx.WriteError, httpx.RemoteProtocolError):
            self.llamadas.clear()
            cliente = self.cliente([clase("transitorio"), (200, {}, (b"ok",))])
            with self.subTest(clase=clase):
                self.assertEqual(cliente.get(self.ORIGEN).contenido, b"ok")
                self.assertEqual(len(self.llamadas), 2)

    def test_tls_con_causa_estructurada_no_reintenta(self):
        tls = ssl.SSLCertVerificationError(1, "CERTIFICATE_VERIFY_FAILED")
        error = httpx.ConnectError("fallo conexion")
        error.__cause__ = tls
        cliente = self.cliente([error])
        with self.assertRaises(ErrorTransporteHTTP) as contexto:
            cliente.get(self.ORIGEN)
        self.assertEqual(contexto.exception.tipo, TipoErrorHTTP.TLS)
        self.assertEqual(len(self.llamadas), 1)
        self.assertEqual(self.esperas, [])

    def test_tls_con_diagnostico_textual_no_reintenta(self):
        cliente = self.cliente([httpx.ConnectError("certificate verify failed")])
        with self.assertRaises(ErrorTransporteHTTP) as contexto:
            cliente.get(self.ORIGEN)
        self.assertEqual(contexto.exception.tipo, TipoErrorHTTP.TLS)
        self.assertEqual(len(self.llamadas), 1)

    def test_error_de_protocolo_local_no_reintenta(self):
        cliente = self.cliente([httpx.LocalProtocolError("definitivo")])
        with self.assertRaises(ErrorTransporteHTTP):
            cliente.get(self.ORIGEN)
        self.assertEqual(len(self.llamadas), 1)

    def test_retroceso_exponencial_jitter_y_tope(self):
        politica = PoliticaReintentos(max_intentos=5, espera_inicial=2, espera_maxima=7, jitter=0.5)
        cliente = self.cliente([(503, {}, ())] * 4 + [(200, {}, ())], politica, aleatorio=lambda: 1)
        cliente.get(self.ORIGEN)
        self.assertEqual(self.esperas, [3, 6, 7, 7])

    def test_jitter_inferior_y_retry_after_como_minimo(self):
        politica = PoliticaReintentos(max_intentos=2, espera_inicial=2, espera_maxima=5, jitter=1)
        cliente = self.cliente([(429, {"Retry-After": "5"}, ()), (200, {}, ())], politica, aleatorio=lambda: 0)
        cliente.get(self.ORIGEN)
        self.assertEqual(self.esperas, [5])

    def test_politica_invalida(self):
        politica = PoliticaReintentos()
        for cambios in ({"max_intentos": 0}, {"max_intentos": True}, {"max_intentos": 101},
                        {"espera_inicial": -1}, {"espera_maxima": float("inf")},
                        {"espera_maxima": 3601},
                        {"jitter": float("nan")}, {"jitter": 1.1}, {"jitter": True},
                        {"espera_inicial": 2, "espera_maxima": 1}):
            with self.subTest(cambios=cambios), self.assertRaises(ValueError):
                replace(politica, **cambios)

    def test_cancelacion_previa_no_solicita(self):
        cliente = self.cliente([])
        cliente.cancelar()
        with self.assertRaises(ErrorTransporteHTTP) as contexto:
            cliente.get(self.ORIGEN)
        self.assertEqual(contexto.exception.tipo, TipoErrorHTTP.CANCELADO)
        self.assertEqual(contexto.exception.intentos, 0)
        self.assertEqual(self.llamadas, [])

    def test_cancelacion_durante_espera_no_hace_otro_intento(self):
        evento = Event()
        def esperar(segundos):
            self.esperas.append(segundos)
            evento.set()
        cliente = self.cliente([(503, {}, ())], espera=esperar, cancelacion=evento)
        with self.assertRaises(ErrorTransporteHTTP) as contexto:
            cliente.get(self.ORIGEN)
        self.assertEqual(contexto.exception.tipo, TipoErrorHTTP.CANCELADO)
        self.assertEqual(contexto.exception.intentos, 1)
        self.assertEqual(len(self.llamadas), 1)
        self.assertEqual(cliente.historial_intentos[-1].resultado, "cancelado")

    def test_espera_predeterminada_es_evento_interrumpible(self):
        cliente = self.cliente([(503, {}, ()), (200, {}, ())], espera=None)
        with patch.object(cliente._gestor.cancelacion, "wait") as esperar:
            # El método enlazado se captura al construir el gestor.
            cliente._gestor.espera = esperar
            cliente.get(self.ORIGEN)
            esperar.assert_called_once_with(1)

    def test_streaming_fallido_limpia_y_reinicia_sin_range(self):
        primero = Flujo((b"ab",), httpx.ReadError("corte"))
        def intento_uno(request):
            return httpx.Response(200, stream=primero)
        def intento_dos(request):
            self.assertEqual(list(self.raiz.iterdir()), [])
            self.assertTrue(primero.cerrado)
            return httpx.Response(200, headers={"Content-Length": "3"}, stream=Flujo((b"xyz",)))
        cliente = self.cliente([intento_uno, intento_dos])
        informe = self.descargar(cliente)
        self.assertEqual(informe.ruta_local.read_bytes(), b"xyz")
        self.assertEqual(informe.sha256, hashlib.sha256(b"xyz").hexdigest())
        self.assertEqual(informe.bytes_almacenados, 3)
        self.assertEqual(len(list(self.raiz.iterdir())), 1)
        self.assertTrue(all("range" not in r.headers and r.method == "GET" for r in self.llamadas))
        self.assertNotIn("secreto", repr(cliente.historial_intentos))

    def test_descarga_503_retry_after_y_recuperacion(self):
        cliente = self.cliente([(503, {"Retry-After": "4"}, ()), (200, {}, (b"abc",))])
        self.assertEqual(self.descargar(cliente).ruta_local.read_bytes(), b"abc")
        self.assertEqual(self.esperas, [4])

    def test_descarga_truncada_reinicia_desde_cero(self):
        cliente = self.cliente([(200, {"Content-Length": "3"}, (b"ab",)),
                                (200, {"Content-Length": "3"}, (b"xyz",))])
        self.assertEqual(self.descargar(cliente).ruta_local.read_bytes(), b"xyz")
        self.assertEqual(len(self.llamadas), 2)

    def test_descarga_agotada_no_deja_archivos(self):
        cliente = self.cliente([httpx.ReadTimeout("corte")] * 3)
        with self.assertRaises(ErrorDescargaArchivo) as contexto:
            self.descargar(cliente)
        self.assertTrue(contexto.exception.agotados)
        self.assertEqual(contexto.exception.intentos, 3)
        self.assertEqual(list(self.raiz.iterdir()), [])

    def test_temporal_no_eliminado_impide_reintento(self):
        cliente = self.cliente([(200, {}, (b"abc",))])
        with patch.object(Path, "unlink", side_effect=PermissionError("ocupado")):
            with patch("spica.adquisicion.transportes.descargas.os.fsync", side_effect=OSError("disco")):
                with self.assertRaises(ErrorDescargaArchivo) as contexto:
                    self.descargar(cliente)
        self.assertIsNotNone(contexto.exception.informe.temporal_restante)
        self.assertEqual(len(self.llamadas), 1)
        self.assertEqual(self.esperas, [])

    def test_fallo_transitorio_con_temporal_residual_no_reintenta(self):
        def interrumpido(request):
            return httpx.Response(200, stream=Flujo((b"ab",), httpx.ReadError("corte")))
        cliente = self.cliente([interrumpido])
        with patch.object(Path, "unlink", side_effect=PermissionError("ocupado")):
            with self.assertRaises(ErrorDescargaArchivo) as contexto:
                self.descargar(cliente)
        self.assertTrue(contexto.exception.informe.temporal_restante.exists())
        self.assertEqual(len(self.llamadas), 1)
        self.assertFalse(contexto.exception.recuperable)

    def test_cancelacion_durante_streaming_limpia_temporal(self):
        evento = Event()
        def partes():
            yield b"ab"
            evento.set()
            yield b"cd"
        cliente = self.cliente([(200, {}, partes())], cancelacion=evento)
        with self.assertRaises(ErrorDescargaArchivo) as contexto:
            self.descargar(cliente)
        self.assertEqual(contexto.exception.tipo, TipoErrorHTTP.CANCELADO)
        self.assertEqual(list(self.raiz.iterdir()), [])
        self.assertEqual(len(self.llamadas), 1)

    def test_original_existente_no_se_sobrescribe_ni_reintenta(self):
        destino = self.raiz / "archivo.bin"
        destino.write_bytes(b"original")
        cliente = self.cliente([])
        with self.assertRaises(ErrorDescargaArchivo) as contexto:
            self.descargar(cliente)
        self.assertEqual(contexto.exception.tipo, TipoErrorHTTP.DESTINO_EXISTENTE)
        self.assertEqual(destino.read_bytes(), b"original")
        self.assertEqual(self.llamadas, [])
        self.assertEqual(self.esperas, [])

    def test_original_creado_entre_intentos_se_conserva(self):
        def esperar(segundos):
            (self.raiz / "archivo.bin").write_bytes(b"original")
        cliente = self.cliente([(503, {}, ())], espera=esperar)
        with self.assertRaises(ErrorDescargaArchivo) as contexto:
            self.descargar(cliente)
        self.assertEqual(contexto.exception.tipo, TipoErrorHTTP.DESTINO_EXISTENTE)
        self.assertEqual((self.raiz / "archivo.bin").read_bytes(), b"original")
        self.assertEqual(len(self.llamadas), 1)

    def test_limite_compresion_y_longitud_excesiva_no_reintentan(self):
        for cabeceras, partes, tipo in (({"Content-Length": "101"}, (), TipoErrorHTTP.TAMANO_EXCEDIDO),
                                       ({"Content-Encoding": "gzip"}, (), TipoErrorHTTP.RESPUESTA_INVALIDA),
                                       ({"Content-Length": "1"}, (b"abc",), TipoErrorHTTP.RESPUESTA_INVALIDA)):
            self.llamadas.clear()
            cliente = self.cliente([(200, cabeceras, partes)])
            with self.subTest(cabeceras=cabeceras), self.assertRaises(ErrorDescargaArchivo) as contexto:
                self.descargar(cliente)
            self.assertEqual(contexto.exception.tipo, tipo)
            self.assertEqual(len(self.llamadas), 1)
            self.assertEqual(list(self.raiz.iterdir()), [])

    def test_origen_no_autorizado_no_solicita_ni_espera(self):
        cliente = self.cliente([])
        with self.assertRaises(ValueError):
            cliente.get("https://otro.invalid")
        self.assertEqual(self.llamadas, [])
        self.assertEqual(self.esperas, [])
        self.assertEqual(cliente.historial_intentos, ())

    def test_historial_se_reemplaza_entre_operaciones(self):
        cliente = self.cliente([(503, {}, ()), (200, {}, ()), (200, {}, ())])
        cliente.get(self.ORIGEN)
        self.assertEqual(len(cliente.historial_intentos), 2)
        cliente.get(self.ORIGEN)
        self.assertEqual(len(cliente.historial_intentos), 1)
        self.assertEqual(cliente.historial_intentos[0].numero, 1)

    def test_get_interrumpido_descarta_buffer_previo(self):
        def interrumpido(request):
            return httpx.Response(200, stream=Flujo((b"primero",), httpx.ReadError("corte")))
        cliente = self.cliente([interrumpido, (200, {}, (b"segundo",))])
        self.assertEqual(cliente.get(self.ORIGEN).contenido, b"segundo")
        self.assertEqual(len(self.llamadas), 2)

    def test_politica_predeterminada_no_reintenta(self):
        cliente = self.cliente([(503, {}, ())], PoliticaReintentos())
        with self.assertRaises(ErrorTransporteHTTP) as contexto:
            cliente.get(self.ORIGEN)
        self.assertTrue(contexto.exception.agotados)
        self.assertEqual(len(self.llamadas), 1)
        self.assertEqual(self.esperas, [])

    def test_error_disco_no_reintenta_con_politica_activa(self):
        cliente = self.cliente([(200, {}, (b"abc",))])
        with patch("spica.adquisicion.transportes.descargas.os.fsync", side_effect=OSError("fallo")):
            with self.assertRaises(ErrorDescargaArchivo) as contexto:
                self.descargar(cliente)
        self.assertEqual(contexto.exception.tipo, TipoErrorHTTP.DISCO)
        self.assertEqual(len(self.llamadas), 1)
        self.assertEqual(list(self.raiz.iterdir()), [])

    def test_tls_en_descarga_no_reintenta(self):
        cliente = self.cliente([httpx.ConnectError("CERTIFICATE_VERIFY_FAILED")])
        with self.assertRaises(ErrorDescargaArchivo) as contexto:
            self.descargar(cliente)
        self.assertEqual(contexto.exception.tipo, TipoErrorHTTP.TLS)
        self.assertEqual(len(self.llamadas), 1)
        self.assertEqual(list(self.raiz.iterdir()), [])

    def test_exito_con_temporal_residual_no_vuelve_a_descargar(self):
        cliente = self.cliente([(200, {}, (b"abc",))])
        with patch.object(Path, "unlink", side_effect=PermissionError("ocupado")):
            informe = self.descargar(cliente)
        self.assertTrue(informe.temporal_restante.exists())
        self.assertEqual(informe.ruta_local.read_bytes(), b"abc")
        self.assertEqual(len(self.llamadas), 1)
        self.assertEqual(cliente.historial_intentos[-1].resultado, "exito")

    def test_jitter_inyectado_fuera_de_rango_se_rechaza(self):
        cliente = self.cliente([(503, {}, ())], PoliticaReintentos(max_intentos=2), aleatorio=lambda: 2)
        with self.assertRaises(ValueError):
            cliente.get(self.ORIGEN)
        self.assertEqual(self.esperas, [])


if __name__ == "__main__":
    unittest.main()
