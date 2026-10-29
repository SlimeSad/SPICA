"""Configuración operativa usando solo directorios efímeros fuera del checkout."""

import hashlib
from contextlib import closing
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch
from uuid import uuid4

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from spica.adquisicion.almacenamiento import ConfiguracionRAW, DeclaracionRAW, ErrorAlmacenamientoRAW
from spica.adquisicion.nucleo import Fuente
from spica.adquisicion.transportes import ClienteHTTP
from test_transporte_http import Flujo


class ConfiguracionRAWTests(unittest.TestCase):
    def setUp(self):
        self.codigo = Path(__file__).resolve().parents[1]
        self.base = Path(tempfile.gettempdir()).resolve() / ("spica-config-test-" + uuid4().hex)
        assert not self.base.is_relative_to(self.codigo)
        self.base.mkdir(mode=0o755)
        self.addCleanup(shutil.rmtree, self.base)
        self.config = ConfiguracionRAW(self.base / "datos" / "raw", espacio_minimo_libre=1)

    def abrir_nuevo(self):
        resultado = self.config.inicializar()
        self.addCleanup(resultado.close)
        return resultado

    def declaracion(self):
        return DeclaracionRAW("proyecto-sintetico", "objeto-sintetico", Fuente("sintetica", "fuente"), "recurso")

    def test_configuracion_predeterminada_sin_escribir(self):
        with patch("pathlib.Path.home", return_value=self.base / "usuario"):
            c = ConfiguracionRAW()
        self.assertEqual(c.raiz, self.base / "usuario" / "SPICA_DATOS" / "raw")
        self.assertFalse(c.raiz.exists())
        self.assertFalse(c.staging.exists())

    def test_configuracion_personalizada(self):
        self.assertEqual(self.config.staging, self.base / "datos" / "raw-staging")
        self.assertEqual(self.config.claves_parametros_publicos, ("producto_id",))

    def test_validacion_no_crea_directorios(self):
        self.assertFalse(self.config.validar().inicializado)
        self.assertEqual(list(self.base.iterdir()), [])

    def test_rechaza_ruta_relativa(self):
        with self.assertRaises(ValueError):
            ConfiguracionRAW(Path("relativa"))

    def test_rechaza_traversal(self):
        with self.assertRaises(ErrorAlmacenamientoRAW):
            ConfiguracionRAW(self.base / ".." / "otro").inicializar()
        self.assertEqual(list(self.base.iterdir()), [])

    def test_rechaza_codigo_incluso_gitignore(self):
        for ruta in (self.codigo / "datos" / "raw", self.codigo / "src" / "datos", self.codigo / ".git" / "raw"):
            with self.subTest(ruta=ruta), self.assertRaises(ErrorAlmacenamientoRAW):
                ConfiguracionRAW(ruta).validar()

    def test_rechaza_otro_checkout(self):
        repo = self.base / "codigo"
        repo.mkdir()
        (repo / ".git").write_text("gitdir: sintetico", encoding="utf-8")
        with self.assertRaises(ErrorAlmacenamientoRAW):
            ConfiguracionRAW(repo / "datos" / "raw").inicializar()
        self.assertFalse((repo / "datos").exists())

    def test_rechaza_control_interno(self):
        with self.assertRaises(ErrorAlmacenamientoRAW):
            ConfiguracionRAW(self.base / ".codex" / "raw").validar()

    def test_detecta_enlace_no_autorizado(self):
        with patch("pathlib.Path.is_symlink", return_value=True):
            with self.assertRaises(ErrorAlmacenamientoRAW):
                self.config.validar()

    def test_inicializacion_explicita(self):
        op = self.abrir_nuevo()
        self.assertTrue(op.nuevo)
        self.assertTrue(self.config.validar().inicializado)
        self.assertTrue((self.config.raiz / "catalogo.sqlite3").is_file())
        self.assertTrue((self.config.raiz / "spica-raw.json").is_file())

    def test_reconocimiento_no_sobrescribe(self):
        a = self.config.inicializar()
        a.close()
        catalogo = self.config.raiz / "catalogo.sqlite3"
        marcador = self.config.raiz / "spica-raw.json"
        antes = (catalogo.read_bytes(), marcador.read_bytes())
        with self.config.inicializar() as b:
            self.assertFalse(b.nuevo)
        self.assertEqual(antes, (catalogo.read_bytes(), marcador.read_bytes()))

    def test_directorio_existente_no_se_adopta(self):
        self.config.raiz.mkdir(parents=True)
        original = self.config.raiz / "original.bin"
        original.write_bytes(b"preservar")
        with self.assertRaises(ErrorAlmacenamientoRAW):
            self.config.inicializar()
        self.assertEqual(original.read_bytes(), b"preservar")
        self.assertEqual(tuple(self.config.raiz.iterdir()), (original,))

    def test_archivo_en_lugar_de_raiz(self):
        self.config.raiz.parent.mkdir()
        self.config.raiz.write_bytes(b"intocable")
        with self.assertRaises(ErrorAlmacenamientoRAW):
            self.config.inicializar()
        self.assertEqual(self.config.raiz.read_bytes(), b"intocable")

    def test_staging_ajeno_se_conserva(self):
        self.config.staging.mkdir(parents=True)
        (self.config.staging / "archivo").write_bytes(b"original")
        with self.assertRaises(ErrorAlmacenamientoRAW):
            self.config.inicializar()
        self.assertFalse(self.config.raiz.exists())
        self.assertEqual((self.config.staging / "archivo").read_bytes(), b"original")

    def test_abrir_no_inicializa(self):
        with self.assertRaises(ErrorAlmacenamientoRAW):
            self.config.abrir()
        self.assertFalse(self.config.raiz.exists())

    def test_persistencia_hash_y_recuperacion(self):
        with self.config.inicializar() as op:
            archivo = self.config.staging / "sintetico.bin"
            archivo.write_bytes(b"archivo sintetico persistente")
            a = op.almacen.incorporar(archivo, self.declaracion())
            self.assertEqual(a.sha256, hashlib.sha256(archivo.read_bytes()).hexdigest())
        with self.config.abrir() as op:
            ruta = op.almacen.recuperar(a.asset_id)
            self.assertEqual(ruta.read_bytes(), b"archivo sintetico persistente")
            self.assertEqual(op.almacen.metadatos(a.asset_id).sha256, a.sha256)

    def test_deduplicacion_sin_perder_adquisiciones(self):
        with self.config.inicializar() as op:
            archivo = self.config.staging / "entrada.bin"
            archivo.write_bytes(b"sintetico")
            a = op.almacen.incorporar(archivo, self.declaracion())
            b = op.almacen.incorporar(archivo, self.declaracion())
            self.assertNotEqual(a.asset_id, b.asset_id)
            self.assertEqual(a.storage_ref, b.storage_ref)

    def test_integridad_detecta_corrupcion(self):
        with self.config.inicializar() as op:
            archivo = self.config.staging / "entrada.bin"
            archivo.write_bytes(b"sintetico")
            a = op.almacen.incorporar(archivo, self.declaracion())
            ruta = op.almacen.recuperar(a.asset_id)
            ruta.write_bytes(b"corrupto-sintetico")
            self.assertFalse(op.almacen.verificar(a.asset_id).coincide)

    def test_permisos_basicos_insuficientes(self):
        with patch("spica.adquisicion.almacenamiento.configuracion.os.access", return_value=False):
            with self.assertRaises(ErrorAlmacenamientoRAW) as e:
                self.config.validar()
        self.assertEqual(e.exception.codigo, "ubicacion_raw_sin_permisos_basicos")

    def test_permiso_denegado_creacion(self):
        with patch("spica.adquisicion.almacenamiento.configuracion._directorio", side_effect=PermissionError):
            with self.assertRaises(ErrorAlmacenamientoRAW):
                self.config.inicializar()
        self.assertFalse(self.config.raiz.exists())

    def test_espacio_insuficiente_no_crea(self):
        with patch("spica.adquisicion.almacenamiento.configuracion.shutil.disk_usage",
                   return_value=shutil._ntuple_diskusage(10, 10, 0)):
            with self.assertRaises(ErrorAlmacenamientoRAW):
                self.config.inicializar()
        self.assertEqual(list(self.base.iterdir()), [])

    def test_sin_enlaces_duros_falla_sin_marcador(self):
        with patch("spica.adquisicion.almacenamiento.configuracion.os.link", side_effect=OSError):
            with self.assertRaises(ErrorAlmacenamientoRAW):
                self.config.inicializar()
        self.assertFalse((self.config.raiz / "spica-raw.json").exists())
        self.assertEqual(list((self.config.raiz / "temporales").iterdir()), [])
        with self.assertRaises(ErrorAlmacenamientoRAW):
            self.config.inicializar()

    def test_fallo_fsync_limpia_sonda_staging(self):
        with patch("spica.adquisicion.almacenamiento.configuracion.os.fsync", side_effect=OSError):
            with self.assertRaises(ErrorAlmacenamientoRAW):
                self.config.inicializar()
        self.assertEqual(list(self.config.staging.iterdir()), [])

    def test_no_deja_sondas_al_abrir(self):
        self.abrir_nuevo()
        self.assertEqual(list(self.config.staging.iterdir()), [])
        self.assertEqual(list((self.config.raiz / "sha256").iterdir()), [])
        self.assertEqual(list((self.config.raiz / "temporales").iterdir()), [])

    def test_no_migra_version_existente(self):
        self.config.inicializar().close()
        ruta = self.config.raiz / "catalogo.sqlite3"
        with closing(sqlite3.connect(ruta)) as c:
            c.execute("PRAGMA user_version=1")
        self.config.abrir().close()
        with closing(sqlite3.connect(ruta)) as c:
            self.assertEqual(c.execute("PRAGMA user_version").fetchone()[0], 1)

    def test_version_ajena_rechazada_sin_alterar(self):
        self.config.inicializar().close()
        ruta = self.config.raiz / "catalogo.sqlite3"
        with closing(sqlite3.connect(ruta)) as c:
            c.execute("PRAGMA user_version=99")
        antes = ruta.read_bytes()
        with self.assertRaises(ErrorAlmacenamientoRAW):
            self.config.abrir()
        self.assertEqual(ruta.read_bytes(), antes)

    def test_marcador_danado_rechazado(self):
        self.config.inicializar().close()
        marcador = self.config.raiz / "spica-raw.json"
        marcador.write_bytes(b"no es JSON")
        with self.assertRaises(ErrorAlmacenamientoRAW):
            self.config.abrir()
        self.assertEqual(marcador.read_bytes(), b"no es JSON")

    def test_http_raw_mock_usa_staging_configurado(self):
        with self.config.inicializar() as op, ClienteHTTP(("https://sintetico.invalid",),
            transporte=httpx.MockTransport(lambda r: httpx.Response(200,
                headers={"Content-Length": "3"}, stream=Flujo((b"abc",))))) as cliente:
            adaptador = op.adaptador_http(cliente, max_bytes=1024)
            r = adaptador.adquirir("https://sintetico.invalid/archivo", self.declaracion())
            self.assertEqual(r.ruta_verificada.read_bytes(), b"abc")
            self.assertEqual(adaptador.temporales, self.config.staging.resolve())

    def test_limite_adaptador_respeta_raw(self):
        with self.config.inicializar() as op:
            with self.assertRaises(ValueError):
                op.adaptador_http(None, max_bytes=self.config.max_bytes + 1)

    def test_validacion_limites(self):
        for opciones in (dict(max_bytes=True), dict(tamano_bloque=2**22), dict(espacio_minimo_libre=0)):
            with self.subTest(opciones=opciones), self.assertRaises(ValueError):
                ConfiguracionRAW(self.config.raiz, **opciones)


if __name__ == "__main__":
    unittest.main()
