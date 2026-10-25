"""Descargas simuladas y verificación física en directorios temporales, sin red."""

import hashlib
import os
from pathlib import Path
import sys
import tempfile
import shutil
from uuid import uuid4
import unittest
from unittest.mock import patch

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from spica.adquisicion.nucleo import EstadoDescarga, EstadoIntegridad, EstadoRecurso, Fuente, RecursoDescubierto, ResultadoRecurso
from spica.adquisicion.transportes import ClienteHTTP, ConfiguracionHTTP, ErrorDescargaArchivo, ErrorTransporteHTTP, TipoErrorHTTP
from test_transporte_http import Flujo


class DescargasHTTPTests(unittest.TestCase):
    ORIGEN = "https://prueba.invalid"

    def setUp(self):
        proyecto = Path(__file__).resolve().parents[1]
        # mkdtemp usa 0o700, que en este sandbox Windows impide el acceso posterior.
        # Directorio efímero con permisos heredados, siempre dentro del proyecto.
        self.raiz = proyecto / (".suadc-test-" + uuid4().hex)
        self.raiz.mkdir(mode=0o755)
        assert self.raiz.resolve().is_relative_to(proyecto)
        self.addCleanup(shutil.rmtree, self.raiz)

    def cliente(self, partes=(b"abc",), cabeceras=None, codigo=200, error=None):
        self.flujo = Flujo(partes, error)
        self.peticiones = []
        def handler(request):
            self.peticiones.append(request)
            return httpx.Response(codigo, headers=cabeceras, stream=self.flujo)
        cliente = ClienteHTTP((self.ORIGEN,), transporte=httpx.MockTransport(handler))
        self.addCleanup(cliente.close)
        return cliente

    def descargar(self, cliente, **opciones):
        return cliente.descargar(self.ORIGEN + "/recurso?token=secreto", self.raiz, "archivo.bin",
                                  max_bytes=opciones.pop("max_bytes", 100),
                                  tamano_bloque=opciones.pop("tamano_bloque", 2), **opciones)

    def comprobar_fallo(self, cliente, tipo, **opciones):
        with self.assertRaises(ErrorDescargaArchivo) as contexto:
            self.descargar(cliente, **opciones)
        error = contexto.exception
        self.assertEqual(error.tipo, tipo)
        self.assertEqual(error.informe.estado, EstadoDescarga.FALLIDA)
        self.assertIsNone(error.informe.sha256)
        self.assertIsNone(error.informe.ruta_local)
        self.assertIsNone(error.informe.temporal_restante)
        self.assertNotIn("secreto", repr(error.informe))
        self.assertEqual(list(self.raiz.iterdir()), [])
        self.assertTrue(self.flujo.cerrado)
        with self.assertRaises(ValueError):
            error.informe.como_descarga()
        return error

    def test_descarga_correcta_sha256_fisico_y_contrato_no_confirmado(self):
        cliente = self.cliente((b"ab", b"c"), {"Content-Length": "3", "Content-Disposition": 'attachment; filename="../malicioso"'})
        informe = self.descargar(cliente, parametros={"variable": " A/B "})
        self.assertEqual(informe.ruta_local.read_bytes(), b"abc")
        with informe.ruta_local.open("rb") as archivo:
            self.assertEqual(informe.sha256, hashlib.file_digest(archivo, "sha256").hexdigest())
        self.assertEqual(informe.bytes_almacenados, 3)
        self.assertEqual(informe.bytes_declarados, 3)
        self.assertEqual(informe.codigo_http, 200)
        self.assertEqual(informe.origen, self.ORIGEN + "/")
        self.assertEqual(informe.fecha_utc.utcoffset().total_seconds(), 0)
        self.assertNotIn("secreto", repr(informe))
        self.assertIsNone(informe.temporal_restante)
        self.assertEqual([p.name for p in self.raiz.iterdir()], ["archivo.bin"])
        self.assertTrue(self.flujo.cerrado)
        self.assertEqual(self.peticiones[0].url.params["variable"], " A/B ")
        self.assertEqual(self.peticiones[0].headers["accept-encoding"], "identity")
        self.assertEqual(self.peticiones[0].extensions["timeout"]["read"], 30)
        recurso = RecursoDescubierto(Fuente("prueba", "fuente"), "id", "localizador")
        resultado = ResultadoRecurso(recurso, informe.como_descarga())
        self.assertEqual(resultado.estado, EstadoRecurso.DESCARGADO)
        self.assertEqual(resultado.integridad.estado, EstadoIntegridad.PENDIENTE)

    def test_archivo_legitimamente_vacio(self):
        informe = self.descargar(self.cliente((), {"Content-Length": "0"}))
        self.assertEqual(informe.bytes_almacenados, 0)
        self.assertEqual(informe.ruta_local.stat().st_size, 0)
        self.assertEqual(informe.sha256, hashlib.sha256(b"").hexdigest())
        self.assertEqual(informe.como_descarga().estado, EstadoDescarga.COMPLETA)

    def test_archivo_mayor_de_un_mib_y_get_conserva_limite(self):
        # Generador: la fixture tampoco construye el archivo entero en RAM.
        bloque = b"a" * 65_536
        cliente = self.cliente((bloque for _ in range(17)), {"Content-Length": str(17 * len(bloque))})
        informe = self.descargar(cliente, max_bytes=2 * 1_048_576, tamano_bloque=8192)
        self.assertEqual(informe.ruta_local.stat().st_size, 17 * len(bloque))
        self.assertEqual(cliente.configuracion.max_bytes_respuesta, 1_048_576)
        with informe.ruta_local.open("rb") as archivo:
            self.assertEqual(informe.sha256, hashlib.file_digest(archivo, "sha256").hexdigest())
        otro = self.cliente((bloque,), {"Content-Length": str(17 * len(bloque))})
        with self.assertRaises(ErrorTransporteHTTP) as contexto:
            otro.get(self.ORIGEN)
        self.assertEqual(contexto.exception.tipo, TipoErrorHTTP.TAMANO_EXCEDIDO)

    def test_limite_excedido_sin_content_length(self):
        self.comprobar_fallo(self.cliente((b"12", b"34", b"56")), TipoErrorHTTP.TAMANO_EXCEDIDO, max_bytes=3)

    def test_limite_por_cabecera_antes_de_crear_temporal(self):
        cliente = self.cliente(cabeceras={"Content-Length": "101"})
        self.comprobar_fallo(cliente, TipoErrorHTTP.TAMANO_EXCEDIDO)
        self.assertEqual(self.flujo.leidas, 0)

    def test_content_length_incorrecto(self):
        for longitud in ("2", "4", "invalido"):
            with self.subTest(longitud=longitud):
                self.comprobar_fallo(self.cliente(cabeceras={"Content-Length": longitud}),
                                     TipoErrorHTTP.RESPUESTA_INVALIDA)

    def test_interrupcion_de_red(self):
        error = self.comprobar_fallo(self.cliente((b"ab",), error=httpx.ReadError("interrumpido")),
                                     TipoErrorHTTP.TRANSPORTE)
        self.assertEqual(error.informe.bytes_almacenados, 2)

    def test_timeout_y_estados_http(self):
        for codigo, tipo in ((206, TipoErrorHTTP.RESPUESTA_PARCIAL), (401, TipoErrorHTTP.NO_AUTENTICADO),
                             (403, TipoErrorHTTP.PROHIBIDO), (404, TipoErrorHTTP.NO_ENCONTRADO),
                             (429, TipoErrorHTTP.LIMITE_SOLICITUDES), (503, TipoErrorHTTP.SERVIDOR),
                             (302, TipoErrorHTTP.REDIRECCION)):
            with self.subTest(codigo=codigo):
                error = self.comprobar_fallo(self.cliente(codigo=codigo), tipo)
                self.assertEqual(error.codigo_http, codigo)
                self.assertEqual(len(self.peticiones), 1)
        self.comprobar_fallo(self.cliente(error=httpx.ReadTimeout("timeout")), TipoErrorHTTP.TIMEOUT)

    def test_compresion_rechazada(self):
        self.comprobar_fallo(self.cliente(cabeceras={"Content-Encoding": "gzip"}),
                             TipoErrorHTTP.RESPUESTA_INVALIDA)
        self.assertEqual(self.flujo.leidas, 0)

    def test_error_de_escritura_y_escritura_corta(self):
        crear = tempfile.NamedTemporaryFile
        for corta in (False, True):
            def crear_fallido(**opciones):
                archivo = crear(**opciones)
                if corta:
                    archivo.write = lambda bloque: 0
                else:
                    def fallar(bloque):
                        raise OSError("disco lleno")
                    archivo.write = fallar
                return archivo
            with self.subTest(corta=corta), patch(
                "spica.adquisicion.transportes.descargas.tempfile.NamedTemporaryFile", side_effect=crear_fallido
            ):
                self.comprobar_fallo(self.cliente(), TipoErrorHTTP.DISCO)

    def test_error_fsync_no_publica(self):
        with patch("spica.adquisicion.transportes.descargas.os.fsync", side_effect=OSError("fallo")):
            self.comprobar_fallo(self.cliente(), TipoErrorHTTP.DISCO)

    def test_hash_releido_distinto_no_publica(self):
        crear = tempfile.NamedTemporaryFile
        def crear_corrupto(**opciones):
            archivo = crear(**opciones)
            lecturas = iter((b"xxx", b""))
            archivo.read = lambda cantidad: next(lecturas)
            return archivo
        with patch("spica.adquisicion.transportes.descargas.tempfile.NamedTemporaryFile", side_effect=crear_corrupto):
            self.comprobar_fallo(self.cliente(), TipoErrorHTTP.INTEGRIDAD_LOCAL)

    def test_destino_existente_conserva_original_sin_solicitud(self):
        destino = self.raiz / "archivo.bin"
        destino.write_bytes(b"original")
        cliente = self.cliente()
        with self.assertRaises(ErrorDescargaArchivo) as contexto:
            self.descargar(cliente)
        self.assertEqual(contexto.exception.tipo, TipoErrorHTTP.DESTINO_EXISTENTE)
        self.assertEqual(destino.read_bytes(), b"original")
        self.assertEqual(self.peticiones, [])
        self.assertEqual(len(list(self.raiz.iterdir())), 1)

    def test_bloque_demasiado_grande_rechazado(self):
        with self.assertRaises(ValueError):
            self.descargar(self.cliente(), tamano_bloque=1_048_577)

    def test_limite_exacto_y_sin_longitud_declarada(self):
        informe = self.descargar(self.cliente((b"abc",)), max_bytes=3, tamano_bloque=1)
        self.assertEqual(informe.bytes_almacenados, 3)
        self.assertIsNone(informe.bytes_declarados)
        self.assertEqual(informe.ruta_local.read_bytes(), b"abc")
        self.assertEqual(len(list(self.raiz.iterdir())), 1)

    def test_destino_creado_durante_publicacion_no_se_sobrescribe(self):
        enlace = os.link
        def carrera(origen, destino):
            Path(destino).write_bytes(b"original concurrente")
            enlace(origen, destino)
        with patch("spica.adquisicion.transportes.descargas.os.link", side_effect=carrera):
            with self.assertRaises(ErrorDescargaArchivo) as contexto:
                self.descargar(self.cliente())
        self.assertEqual(contexto.exception.tipo, TipoErrorHTTP.DESTINO_EXISTENTE)
        self.assertEqual((self.raiz / "archivo.bin").read_bytes(), b"original concurrente")
        self.assertEqual(len(list(self.raiz.iterdir())), 1)

    def test_sistema_sin_enlaces_duros_falla_sin_fallback(self):
        with patch("spica.adquisicion.transportes.descargas.os.link", side_effect=OSError("no soportado")):
            self.comprobar_fallo(self.cliente(), TipoErrorHTTP.DISCO)

    def test_nombres_inseguros_no_generan_peticion(self):
        cliente = self.cliente()
        for nombre in ("../fuera", "a/b", "a\\b", "C:\\fuera", "a:ads", "CON", "NUL.bin", "a.", "", ".oculto"):
            with self.subTest(nombre=nombre), self.assertRaises(ValueError):
                cliente.descargar(self.ORIGEN, self.raiz, nombre, max_bytes=100)
        self.assertEqual(self.peticiones, [])
        self.assertEqual(list(self.raiz.iterdir()), [])

    def test_directorio_enlazado_rechazado(self):
        # No requiere privilegios para crear symlinks en Windows.
        cliente = self.cliente()
        with patch.object(Path, "is_symlink", return_value=True):
            with self.assertRaises(ValueError):
                self.descargar(cliente)
        self.assertEqual(self.peticiones, [])

    def test_origen_no_autorizado_y_tls_desactivado(self):
        cliente = self.cliente()
        with self.assertRaises(ValueError):
            cliente.descargar("https://otro.invalid", self.raiz, "archivo.bin", max_bytes=100)
        inseguro = ClienteHTTP((self.ORIGEN,), ConfiguracionHTTP(verificar_tls=False),
                               transporte=httpx.MockTransport(lambda request: self.fail("No debe solicitar")))
        with inseguro, self.assertRaises(ValueError):
            self.descargar(inseguro)
        self.assertEqual(self.peticiones, [])
        self.assertEqual(list(self.raiz.iterdir()), [])

    def test_configuracion_de_descarga_invalida(self):
        cliente = self.cliente()
        for clave in ("max_bytes", "tamano_bloque"):
            for valor in (0, -1, True, 1.5):
                with self.subTest(clave=clave, valor=valor), self.assertRaises(ValueError):
                    self.descargar(cliente, **{clave: valor})
        self.assertEqual(self.peticiones, [])

    def test_keyboardinterrupt_limpia_y_se_propaga(self):
        cliente = self.cliente((b"ab",), error=KeyboardInterrupt())
        with self.assertRaises(KeyboardInterrupt):
            self.descargar(cliente)
        self.assertEqual(list(self.raiz.iterdir()), [])
        self.assertTrue(self.flujo.cerrado)

    def test_temporal_conservado_se_informa_si_limpieza_falla(self):
        with patch.object(Path, "unlink", side_effect=PermissionError("ocupado")):
            with self.assertRaises(ErrorDescargaArchivo) as contexto:
                self.descargar(self.cliente((b"ab",), error=httpx.ReadError("fallo")))
            informe = contexto.exception.informe
        self.assertTrue(informe.temporal_restante.is_file())
        self.assertIsNone(informe.ruta_local)
        self.assertEqual(informe.temporal_restante.read_bytes(), b"ab")

    def test_publicacion_completa_informa_temporal_residual(self):
        with patch.object(Path, "unlink", side_effect=PermissionError("ocupado")):
            informe = self.descargar(self.cliente())
        self.assertEqual(informe.estado, EstadoDescarga.COMPLETA)
        self.assertTrue(informe.temporal_restante.exists())
        self.assertEqual(informe.ruta_local.read_bytes(), b"abc")


if __name__ == "__main__":
    unittest.main()
