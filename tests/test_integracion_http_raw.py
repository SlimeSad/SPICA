"""Integración física con MockTransport, SQLite y datos exclusivamente sintéticos."""

from dataclasses import replace
import hashlib
from pathlib import Path
import shutil
import sqlite3
import sys
import traceback
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from uuid import uuid4

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from spica.adquisicion.almacenamiento import AlmacenRAW, DeclaracionRAW, EstadoIncorporacion
from spica.adquisicion.integracion import AdaptadorHTTPRAW, ErrorIntegracionHTTPRAW, FaseHTTPRAW
from spica.adquisicion.nucleo import Fuente
from spica.adquisicion.transportes import ClienteHTTP, ConfiguracionHTTP, PoliticaReintentos
from test_transporte_http import Flujo
import test_modelos_md_raw as fixtures_md


class IntegracionHTTPRAWTests(unittest.TestCase):
    ORIGEN = "https://prueba.invalid"

    def setUp(self):
        proyecto = Path(__file__).resolve().parents[1]
        self.base = proyecto / (".suadc-test-" + uuid4().hex)
        self.base.mkdir(mode=0o755)
        assert self.base.resolve().is_relative_to(proyecto)
        self.addCleanup(shutil.rmtree, self.base)
        self.staging = self.base / "staging"
        self.raw = self.base / "raw"
        self.staging.mkdir()
        self.raw.mkdir()
        self.almacen = AlmacenRAW(self.raw, (self.staging,), max_bytes=2 * 1024**2,
                                  claves_parametros_publicos=("variable",))
        self.addCleanup(self.almacen.close)
        self.declaracion = DeclaracionRAW(" P-01 ", "objeto/01", Fuente("prueba", " Fuente "), " Recurso/01 ")
        self.peticiones = []
        self.flujos = []

    def adaptador(self, partes=(b"abc",), *, codigo=200, cabeceras=None, error=None,
                  max_bytes=2 * 1024**2, politica=None):
        def handler(request):
            self.peticiones.append(request)
            flujo = Flujo(partes, error)
            self.flujos.append(flujo)
            return httpx.Response(codigo, headers=cabeceras, stream=flujo)
        cliente = ClienteHTTP((self.ORIGEN,), transporte=httpx.MockTransport(handler),
            politica_reintentos=politica, espera=lambda segundos: None)
        self.addCleanup(cliente.close)
        return AdaptadorHTTPRAW(cliente, self.almacen, self.staging, max_bytes=max_bytes,
                                 tamano_bloque=65_536)

    def adquirir(self, adaptador, declaracion=None, url=None, **opciones):
        return adaptador.adquirir(url or self.ORIGEN + "/archivo?token=CLAVE_SINTETICA",
                                  declaracion or self.declaracion, **opciones)

    def test_descarga_incorporacion_y_recuperacion_fisica(self):
        resultado = self.adquirir(self.adaptador(cabeceras={"Content-Length": "3"}))
        self.assertEqual(resultado.fase, FaseHTTPRAW.COMPLETADA)
        self.assertEqual(resultado.ruta_verificada.read_bytes(), b"abc")
        with resultado.ruta_verificada.open("rb") as archivo:
            hash_real = hashlib.file_digest(archivo, "sha256").hexdigest()
        self.assertEqual(hash_real, resultado.informe_http.sha256)
        self.assertEqual(hash_real, resultado.activo.sha256)
        self.assertEqual(resultado.activo.size_bytes, resultado.informe_http.bytes_almacenados)
        self.assertEqual(resultado.activo.estado, EstadoIncorporacion.INCORPORADA)
        self.assertEqual(resultado.activo.declaracion.proyecto_id, " P-01 ")
        self.assertEqual(resultado.activo.object_id, "objeto/01")
        self.assertEqual(resultado.activo.declaracion.recurso_id, " Recurso/01 ")
        self.assertNotEqual(resultado.activo.asset_id, resultado.activo.sha256)
        self.assertEqual(resultado.intentos_http[-1].resultado, "exito")
        self.assertEqual(list(self.staging.iterdir()), [])
        self.assertTrue(all(f.cerrado for f in self.flujos))
        self.assertIsNone(resultado.temporal_restante)
        self.assertIsNone(resultado.activo.media_detected)

    def test_archivo_vacio(self):
        resultado = self.adquirir(self.adaptador((), cabeceras={"Content-Length": "0"}))
        self.assertEqual(resultado.activo.size_bytes, 0)
        self.assertEqual(resultado.activo.sha256, hashlib.sha256(b"").hexdigest())
        self.assertEqual(resultado.ruta_verificada.read_bytes(), b"")

    def test_mayor_de_un_mib_sin_acumular_cuerpo_completo(self):
        bloque = b"x" * 65_536
        resultado = self.adquirir(self.adaptador((bloque for _ in range(17)),
            cabeceras={"Content-Length": str(17 * len(bloque))}))
        self.assertEqual(resultado.ruta_verificada.stat().st_size, 17 * len(bloque))
        with resultado.ruta_verificada.open("rb") as archivo:
            self.assertEqual(hashlib.file_digest(archivo, "sha256").hexdigest(), resultado.informe_http.sha256)

    def test_modificacion_entre_etapas_rechazada_antes_de_publicar(self):
        adaptador = self.adaptador()
        incorporar = self.almacen.incorporar
        def modificado(entrada, declaracion, **evidencia):
            entrada.write_bytes(b"xyz")  # Igual tamaño, diferente SHA-256.
            return incorporar(entrada, declaracion, **evidencia)
        with patch.object(self.almacen, "incorporar", side_effect=modificado):
            with self.assertRaises(ErrorIntegracionHTTPRAW) as contexto:
                self.adquirir(adaptador)
        self.assertEqual(contexto.exception.codigo, "evidencia_entrada_no_coincidente")
        self.assertEqual(contexto.exception.fase, FaseHTTPRAW.INCORPORACION)
        activo = self.almacen.metadatos(contexto.exception.activo_id)
        self.assertEqual(activo.estado, EstadoIncorporacion.FALLIDA)
        self.assertEqual(tuple((self.raw / "sha256").glob("*/*")), ())
        self.assertEqual(list(self.staging.iterdir()), [])
        self.assertIn(activo.asset_id, self.almacen.diagnosticar().incompletas)

    def test_informe_con_tamano_falso_no_se_confirma(self):
        adaptador = self.adaptador()
        descargar = adaptador.cliente.descargar
        def informe_falso(*args, **opciones):
            return replace(descargar(*args, **opciones), bytes_almacenados=4)
        with patch.object(adaptador.cliente, "descargar", side_effect=informe_falso):
            with self.assertRaises(ErrorIntegracionHTTPRAW) as contexto:
                self.adquirir(adaptador)
        self.assertEqual(contexto.exception.codigo, "evidencia_entrada_no_coincidente")
        self.assertEqual(self.almacen.metadatos(contexto.exception.activo_id).estado, EstadoIncorporacion.FALLIDA)

    def test_fallos_http_timeout_y_descarga_incompleta_sin_activo(self):
        for opciones in (dict(codigo=404), dict(codigo=503), dict(error=httpx.ReadTimeout("timeout")),
                        dict(cabeceras={"Content-Length": "5"}), dict(codigo=206),
                        dict(cabeceras={"Content-Encoding": "gzip"}), dict(max_bytes=2)):
            with self.subTest(opciones=opciones), self.assertRaises(ErrorIntegracionHTTPRAW) as contexto:
                self.adquirir(self.adaptador(**opciones))
            self.assertEqual(contexto.exception.fase, FaseHTTPRAW.DESCARGA)
            self.assertIsNone(contexto.exception.activo_id)
            self.assertEqual(self.almacen._catalogo.listar(), ())
            self.assertEqual(list(self.staging.iterdir()), [])

    def test_error_sqlite_no_produce_resultado_satisfactorio(self):
        adaptador = self.adaptador()
        with patch.object(self.almacen._catalogo, "preparar", side_effect=sqlite3.OperationalError("error sqlite")):
            with self.assertRaises(ErrorIntegracionHTTPRAW) as contexto:
                self.adquirir(adaptador)
        self.assertEqual(contexto.exception.codigo, "error_sqlite")
        self.assertEqual(self.almacen._catalogo.listar(), ())
        self.assertEqual(list(self.staging.iterdir()), [])

    def test_error_escritura_http(self):
        adaptador = self.adaptador()
        with patch("spica.adquisicion.transportes.descargas.os.fsync", side_effect=OSError("disco lleno")):
            with self.assertRaises(ErrorIntegracionHTTPRAW):
                self.adquirir(adaptador)
        self.assertEqual(list(self.staging.iterdir()), [])
        self.assertEqual(self.almacen._catalogo.listar(), ())

    def test_error_de_escritura_raw_tras_descarga_completa(self):
        adaptador = self.adaptador()
        with patch.object(self.almacen, "_copiar", side_effect=OSError("disco lleno")):
            with self.assertRaises(ErrorIntegracionHTTPRAW) as contexto:
                self.adquirir(adaptador)
        self.assertEqual(contexto.exception.fase, FaseHTTPRAW.INCORPORACION)
        self.assertEqual(self.almacen.metadatos(contexto.exception.activo_id).estado, EstadoIncorporacion.FALLIDA)

    def test_destino_raw_existente_corrupto_no_se_sobrescribe(self):
        anterior = self.adquirir(self.adaptador())
        anterior.ruta_verificada.write_bytes(b"original alterado")
        with self.assertRaises(ErrorIntegracionHTTPRAW):
            self.adquirir(self.adaptador())
        self.assertEqual(anterior.ruta_verificada.read_bytes(), b"original alterado")

    def test_adquisiciones_duplicadas_comparten_bytes_no_identidad(self):
        primero = self.adquirir(self.adaptador(), url=self.ORIGEN + "/primero")
        segundo = self.adquirir(self.adaptador(), url=self.ORIGEN + "/segundo")
        self.assertNotEqual(primero.activo.asset_id, segundo.activo.asset_id)
        self.assertEqual(primero.ruta_verificada, segundo.ruta_verificada)
        self.assertNotEqual(primero.activo.declaracion.procedencia, segundo.activo.declaracion.procedencia)
        self.assertEqual(len(tuple((self.raw / "sha256").glob("*/*"))), 1)
        self.assertEqual(list(self.staging.iterdir()), [])

    def test_procedencia_publica_y_secretos_solo_sinteticos(self):
        declaracion = replace(self.declaracion, parametros_publicos={"variable": " V/01 ", "token": "CLAVE_SINTETICA"})
        resultado = self.adquirir(self.adaptador(), declaracion, parametros={"variable": " V/01 ", "token": "CLAVE_SINTETICA"})
        self.assertEqual(resultado.activo.declaracion.procedencia, self.ORIGEN + "/archivo")
        self.assertEqual(dict(resultado.activo.declaracion.parametros_publicos), {"variable": " V/01 "})
        self.assertNotIn("CLAVE_SINTETICA", repr(resultado))
        self.assertNotIn(b"CLAVE_SINTETICA", (self.raw / "catalogo.sqlite3").read_bytes())

    def test_error_publico_no_reproduce_consulta_secreta(self):
        with self.assertRaises(ErrorIntegracionHTTPRAW) as contexto:
            self.adquirir(self.adaptador(codigo=403))
        self.assertNotIn("CLAVE_SINTETICA", "".join(traceback.format_exception(contexto.exception)))
        self.assertNotIn("CLAVE_SINTETICA", repr(contexto.exception.__dict__))

    def test_publicacion_sin_registro_final_deja_incompleta_detectable(self):
        real = self.almacen._catalogo.transicion
        def fallar(activo_id, estado, **opciones):
            if estado in (EstadoIncorporacion.INCORPORADA, EstadoIncorporacion.FALLIDA):
                raise sqlite3.OperationalError("fallo persistencia")
            return real(activo_id, estado, **opciones)
        with patch.object(self.almacen._catalogo, "transicion", side_effect=fallar):
            with self.assertRaises(ErrorIntegracionHTTPRAW) as contexto:
                self.adquirir(self.adaptador())
        self.assertIn(contexto.exception.activo_id, self.almacen.diagnosticar().incompletas)
        self.assertEqual(len(self.almacen.diagnosticar().sin_referencia), 1)
        self.assertEqual(list(self.staging.iterdir()), [])

    def test_corrupcion_despues_de_publicar_impide_exito(self):
        real = self.almacen.recuperar
        def corromper(activo_id):
            activo = self.almacen.metadatos(activo_id)
            (self.raw / activo.storage_ref).write_bytes(b"corrupto")
            return real(activo_id)
        with patch.object(self.almacen, "recuperar", side_effect=corromper):
            with self.assertRaises(ErrorIntegracionHTTPRAW) as contexto:
                self.adquirir(self.adaptador())
        self.assertEqual(contexto.exception.fase, FaseHTTPRAW.COMPROBACION)
        self.assertEqual(self.almacen.metadatos(contexto.exception.activo_id).estado, EstadoIncorporacion.INCONSISTENTE)

    def test_interrupcion_limpia_y_se_propaga(self):
        with self.assertRaises(KeyboardInterrupt):
            self.adquirir(self.adaptador(error=KeyboardInterrupt()))
        self.assertEqual(list(self.staging.iterdir()), [])
        self.assertEqual(self.almacen._catalogo.listar(), ())

    def test_fallo_limpieza_se_informa_sin_borrar_raw(self):
        adaptador = self.adaptador()
        with patch("spica.adquisicion.integracion.http_raw.shutil.rmtree", side_effect=PermissionError("ocupado")):
            resultado = self.adquirir(adaptador)
        self.assertTrue(resultado.temporal_restante.exists())
        self.assertEqual(resultado.ruta_verificada.read_bytes(), b"abc")
        self.assertEqual(resultado.fase, FaseHTTPRAW.COMPLETADA)

    def test_staging_no_autorizado_y_tls_inseguro_rechazados(self):
        adaptador = self.adaptador()
        with self.assertRaises(ValueError):
            AdaptadorHTTPRAW(adaptador.cliente, self.almacen, self.raw, max_bytes=100)
        cliente = ClienteHTTP((self.ORIGEN,), ConfiguracionHTTP(verificar_tls=False),
                              transporte=httpx.MockTransport(lambda r: self.fail("No debe solicitar")))
        with cliente, self.assertRaises(ValueError):
            AdaptadorHTTPRAW(cliente, self.almacen, self.staging, max_bytes=100)

    def test_origen_no_autorizado_y_procedencia_conflictiva_sin_incorporar(self):
        adaptador = self.adaptador()
        for url, declaracion in (("https://otro.invalid/recurso", self.declaracion),
                                (self.ORIGEN, replace(self.declaracion, procedencia="urn:otra:procedencia"))):
            with self.subTest(url=url), self.assertRaises(ErrorIntegracionHTTPRAW):
                self.adquirir(adaptador, declaracion, url)
        self.assertEqual(self.peticiones, [])
        self.assertEqual(self.almacen._catalogo.listar(), ())

    def test_sqlite_v1_funciona_sin_migracion(self):
        self.archivo = self.staging / "fixture.bin"
        self.archivo.write_bytes(b"abc")
        raiz = fixtures_md.ModelosMDRawTests.crear_v1(self)
        with AlmacenRAW(raiz, (self.staging,)) as legado:
            adaptador = self.adaptador()
            adaptador.almacen = legado
            resultado = self.adquirir(adaptador)
            self.assertEqual(legado._catalogo.conexion.execute("PRAGMA user_version").fetchone()[0], 1)
            self.assertEqual(resultado.ruta_verificada.read_bytes(), b"abc")

    def test_evidencia_opcional_raw_requiere_par_valido(self):
        archivo = self.staging / "entrada.bin"
        archivo.write_bytes(b"abc")
        for opciones in ({"tamano_esperado": 3}, {"sha256_esperado": "a" * 64},
                         {"tamano_esperado": True, "sha256_esperado": "a" * 64},
                         {"tamano_esperado": 3, "sha256_esperado": "invalido"}):
            with self.subTest(opciones=opciones), self.assertRaises(ValueError):
                self.almacen.incorporar(archivo, self.declaracion, **opciones)
        self.assertEqual(archivo.read_bytes(), b"abc")

    def test_reintentos_se_reutilizan_sin_duplicar_activos(self):
        llamadas = []
        def handler(request):
            llamadas.append(request)
            return httpx.Response(503 if len(llamadas) == 1 else 200, stream=Flujo((b"abc",)))
        with ClienteHTTP((self.ORIGEN,), transporte=httpx.MockTransport(handler),
                         politica_reintentos=PoliticaReintentos(max_intentos=2, jitter=0),
                         espera=lambda segundos: None) as cliente:
            resultado = self.adquirir(AdaptadorHTTPRAW(cliente, self.almacen, self.staging, max_bytes=100))
        self.assertEqual(len(resultado.intentos_http), 2)
        self.assertEqual(resultado.ruta_verificada.read_bytes(), b"abc")
        self.assertEqual(len(self.almacen._catalogo.listar()), 1)

    def test_colision_del_directorio_temporal_conserva_lo_existente(self):
        previo = self.staging / "suadc-http-colision"
        previo.mkdir()
        original = previo / "original.bin"
        original.write_bytes(b"original intacto")
        adaptador = self.adaptador()
        with patch("spica.adquisicion.integracion.http_raw.uuid4", return_value=SimpleNamespace(hex="colision")):
            with self.assertRaises(ErrorIntegracionHTTPRAW):
                self.adquirir(adaptador)
        self.assertEqual(original.read_bytes(), b"original intacto")
        self.assertEqual(self.peticiones, [])

    def test_ruta_inesperada_del_informe_no_se_usa_ni_se_elimina(self):
        ajeno = self.base / "original.bin"
        ajeno.write_bytes(b"original intacto")
        adaptador = self.adaptador()
        real = adaptador.cliente.descargar
        def cambiar_ruta(*args, **opciones):
            return replace(real(*args, **opciones), ruta_local=ajeno)
        with patch.object(adaptador.cliente, "descargar", side_effect=cambiar_ruta):
            with self.assertRaises(ErrorIntegracionHTTPRAW) as contexto:
                self.adquirir(adaptador)
        self.assertEqual(contexto.exception.codigo, "informe_http_no_utilizable")
        self.assertEqual(ajeno.read_bytes(), b"original intacto")
        self.assertEqual(self.almacen._catalogo.listar(), ())
        self.assertEqual(list(self.staging.iterdir()), [])

    def test_cancelacion_http_no_incorpora(self):
        adaptador = self.adaptador()
        adaptador.cliente.cancelar()
        with self.assertRaises(ErrorIntegracionHTTPRAW) as contexto:
            self.adquirir(adaptador)
        self.assertEqual(contexto.exception.codigo, "cancelado")
        self.assertEqual(self.peticiones, [])
        self.assertEqual(self.almacen._catalogo.listar(), ())
        self.assertEqual(list(self.staging.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
