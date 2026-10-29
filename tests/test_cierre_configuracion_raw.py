"""Regresiones del cierre RAW: datos sintéticos y directorios efímeros."""

from contextlib import contextmanager
from io import StringIO
import json
import logging
import os
from pathlib import Path
import shutil
import sys
import tempfile
import traceback
import unittest
from unittest.mock import patch
from uuid import uuid4

sys.path[:0] = [str(Path(__file__).resolve().parents[1] / "src")]
from spica.adquisicion.almacenamiento import ConfiguracionRAW, ErrorAlmacenamientoRAW
from spica.adquisicion.almacenamiento.inspeccion import PoliticaInspeccionRAW, inspeccionar_catalogo
import test_regresiones_altas as fixtures_sqlite


class CierreConfiguracionTests(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.gettempdir()).resolve() / ("spica-cierre-" + uuid4().hex)
        assert not self.base.is_relative_to(Path(__file__).resolve().parents[1])
        self.base.mkdir(mode=0o755)
        self.addCleanup(self.limpiar_base)
        self.cfg = ConfiguracionRAW(self.base / "raw", espacio_minimo_libre=1)

    def limpiar_base(self):
        assert self.base.resolve().parent == Path(tempfile.gettempdir()).resolve()
        shutil.rmtree(self.base)

    def comprobar_no_operativo(self):
        try:
            validacion = self.cfg.validar()
        except ErrorAlmacenamientoRAW:
            return
        self.assertFalse(validacion.inicializado)

    @contextmanager
    def fallar_archivo_marcador(self, fase):
        real = Path.open
        fds = set()
        class Archivo:
            def __init__(self, archivo):
                self.archivo = archivo
                fds.add(archivo.fileno())
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return self.archivo.__exit__(*args)
            def write(self, contenido):
                if fase == "write":
                    raise OSError("CREDENCIAL_SINTETICA_62D")
                if fase == "corta":
                    return self.archivo.write(contenido[:-1])
                return self.archivo.write(contenido)
            def flush(self):
                if fase == "flush":
                    raise OSError("CREDENCIAL_SINTETICA_62D")
                return self.archivo.flush()
            def fileno(self):
                return self.archivo.fileno()
        def abrir(ruta, mode="r", *args, **kwargs):
            if ruta.name.startswith(".spica-marcador-") and mode == "x":
                if fase == "crear":
                    raise OSError("CREDENCIAL_SINTETICA_62D")
                return Archivo(real(ruta, mode, *args, **kwargs))
            return real(ruta, mode, *args, **kwargs)
        fsync_real = os.fsync
        def sincronizar(fd):
            if fase == "fsync" and fd in fds:
                raise OSError("CREDENCIAL_SINTETICA_62D")
            return fsync_real(fd)
        with patch.object(Path, "open", abrir), patch(
                "spica.adquisicion.almacenamiento.configuracion.os.fsync", side_effect=sincronizar):
            yield

    def fallo_marcador(self, fase):
        with self.fallar_archivo_marcador(fase):
            error = self.comprobar_privacidad(self.cfg.inicializar)
        self.assertEqual(error.estado, "revision_necesaria")
        self.assertFalse((self.cfg.raiz / "spica-raw.json").exists())
        self.assertTrue((self.cfg.raiz / "catalogo.sqlite3").exists())
        self.assertEqual(list(self.cfg.raiz.glob(".spica-marcador-*")), [])
        self.comprobar_no_operativo()

    def test_fallo_crear_marcador(self):
        self.fallo_marcador("crear")

    def test_fallo_escribir_marcador(self):
        self.fallo_marcador("write")

    def test_fallo_flush_marcador(self):
        self.fallo_marcador("flush")

    def test_fallo_fsync_del_archivo_marcador(self):
        self.fallo_marcador("fsync")

    def test_escritura_corta_marcador_no_se_publica(self):
        self.fallo_marcador("corta")

    def test_fallo_limpieza_marcador_publicado_bloquea_apertura(self):
        real = Path.unlink
        def eliminar(ruta, *args, **kwargs):
            if ruta.name.startswith(".spica-marcador-"):
                raise PermissionError("CREDENCIAL_SINTETICA_62D")
            return real(ruta, *args, **kwargs)
        with patch.object(Path, "unlink", eliminar):
            error = self.comprobar_privacidad(self.cfg.inicializar)
        self.assertEqual(error.codigo, "limpieza_marcador_incompleta")
        self.assertEqual(error.fallos_limpieza, (("marcador_temporal", "eliminacion_no_disponible"),))
        self.assertTrue((self.cfg.raiz / "spica-raw.json").is_file())
        self.comprobar_no_operativo()

    def test_fallo_publicar_marcador_deja_revision(self):
        real = os.link
        def enlazar(entrada, destino):
            if destino.name == "spica-raw.json":
                raise OSError("CREDENCIAL_SINTETICA_62D")
            return real(entrada, destino)
        with patch("spica.adquisicion.almacenamiento.configuracion.os.link", side_effect=enlazar):
            self.comprobar_privacidad(self.cfg.inicializar)
        self.assertFalse((self.cfg.raiz / "spica-raw.json").exists())
        self.comprobar_no_operativo()

    def test_marcador_aparecido_durante_publicacion_no_se_sobrescribe(self):
        real = os.link
        ajeno = b"marcador sintetico preexistente"
        def enlazar(entrada, destino):
            if destino.name == "spica-raw.json":
                destino.write_bytes(ajeno)
            return real(entrada, destino)
        with patch("spica.adquisicion.almacenamiento.configuracion.os.link", side_effect=enlazar):
            with self.assertRaises(ErrorAlmacenamientoRAW):
                self.cfg.inicializar()
        self.assertEqual((self.cfg.raiz / "spica-raw.json").read_bytes(), ajeno)
        self.comprobar_no_operativo()

    def test_fallo_sincronizar_directorio_antes_de_publicacion(self):
        with patch("spica.adquisicion.almacenamiento.configuracion._sincronizar_directorio",
                   side_effect=OSError("sincronizacion sintetica")):
            with self.assertRaises(ErrorAlmacenamientoRAW):
                self.cfg.inicializar()
        self.assertFalse((self.cfg.raiz / "spica-raw.json").exists())
        self.comprobar_no_operativo()

    def test_fallo_sincronizar_directorio_tras_publicacion(self):
        with patch("spica.adquisicion.almacenamiento.configuracion._sincronizar_directorio",
                   side_effect=[True, OSError("sincronizacion sintetica")]):
            with self.assertRaises(ErrorAlmacenamientoRAW):
                self.cfg.inicializar()
        self.assertTrue((self.cfg.raiz / "spica-raw.json").is_file())
        with self.assertRaises(ErrorAlmacenamientoRAW) as error:
            self.cfg.validar()
        self.assertEqual(error.exception.codigo, "inicializacion_raw_requiere_revision")

    def test_fallo_retirar_intencion_no_declara_operativo(self):
        real = Path.unlink
        def eliminar(ruta, *args, **kwargs):
            if ruta.name == ".spica-raw.inicializando":
                raise PermissionError("ocupado sintetico")
            return real(ruta, *args, **kwargs)
        with patch.object(Path, "unlink", eliminar), self.assertRaises(ErrorAlmacenamientoRAW):
            self.cfg.inicializar()
        self.comprobar_no_operativo()

    def test_retiro_efectivo_con_error_se_reconoce_y_comunica(self):
        real = Path.unlink
        def eliminar(ruta, *args, **kwargs):
            resultado = real(ruta, *args, **kwargs)
            if ruta.name == ".spica-raw.inicializando":
                raise OSError("respuesta sintetica tras retirar intencion")
            return resultado
        with patch.object(Path, "unlink", eliminar):
            with self.cfg.inicializar() as op:
                self.assertIn("retiro_intencion_confirmado_tras_error", op.advertencias)
        self.assertTrue(self.cfg.validar().inicializado)

    def test_interrupcion_marcador_cierra_motor_y_bloquea_apertura(self):
        with patch("spica.adquisicion.almacenamiento.configuracion.json.dump", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.cfg.inicializar()
        self.assertTrue((self.cfg.raiz / "catalogo.sqlite3").is_file())
        self.assertEqual(list(self.cfg.raiz.glob(".spica-marcador-*")), [])
        self.comprobar_no_operativo()

    def test_inicializacion_repetida_conserva_contenido(self):
        from spica.adquisicion.almacenamiento import DeclaracionRAW
        from spica.adquisicion.nucleo import Fuente
        with self.cfg.inicializar() as op:
            entrada = self.cfg.staging / "sintetico.bin"
            entrada.write_bytes(b"original sintetico")
            activo = op.almacen.incorporar(entrada,
                DeclaracionRAW("p", "o", Fuente("sintetica", "f"), "r"))
        antes = {p.relative_to(self.base): p.read_bytes() for p in self.base.rglob("*") if p.is_file()}
        with self.cfg.inicializar() as op:
            self.assertFalse(op.nuevo)
            self.assertEqual(op.almacen.recuperar(activo.asset_id).read_bytes(), b"original sintetico")
        # Recuperar actualiza la fecha de verificación; los originales y el marcador se conservan.
        for ruta, contenido in antes.items():
            if ruta.name != "catalogo.sqlite3":
                self.assertEqual((self.base / ruta).read_bytes(), contenido)

    def test_estado_no_inicializado_e_inicializado(self):
        self.assertEqual(self.cfg.validar().estado, "no_inicializado")
        self.cfg.inicializar().close()
        self.assertEqual(self.cfg.validar().estado, "inicializado")

    def test_fsync_marcador_fallido_no_reconoce_inicializacion(self):
        real = os.fsync
        llamadas = 0
        def fallar(fd):
            nonlocal llamadas
            llamadas += 1
            if llamadas == 3:
                raise OSError("fsync sintetico")
            return real(fd)
        with patch("spica.adquisicion.almacenamiento.configuracion.os.fsync", side_effect=fallar):
            with self.assertRaises(ErrorAlmacenamientoRAW):
                self.cfg.inicializar()
        self.comprobar_no_operativo()

    def test_limpieza_destino_fallida_intenta_limpiar_entrada(self):
        self.cfg.inicializar().close()
        real = Path.unlink
        def fallar(ruta, *args, **kwargs):
            if ruta.parent == self.cfg.raiz / "sha256" and ruta.name.startswith(".sonda-"):
                raise PermissionError("ocupado sintetico")
            return real(ruta, *args, **kwargs)
        with patch.object(Path, "unlink", fallar), self.assertRaises(ErrorAlmacenamientoRAW):
            self.cfg.abrir()
        self.assertEqual(list((self.cfg.raiz / "temporales").iterdir()), [])

    def test_fallo_limpieza_no_oculta_error_principal(self):
        self.cfg.inicializar().close()
        unlink_real, read_real = Path.unlink, Path.read_bytes
        def fallar(ruta, *args, **kwargs):
            if ruta.parent == self.cfg.raiz / "sha256" and ruta.name.startswith(".sonda-"):
                raise PermissionError("ocupado sintetico")
            return unlink_real(ruta, *args, **kwargs)
        def leer(ruta):
            return b"discrepancia sintetica" if ruta.name.startswith(".sonda-") else read_real(ruta)
        with patch.object(Path, "unlink", fallar), patch.object(Path, "read_bytes", leer):
            with self.assertRaises(ErrorAlmacenamientoRAW) as capturado:
                self.cfg.abrir()
        self.assertEqual(capturado.exception.codigo, "sonda_publicacion_no_coincidente")
        self.assertTrue(capturado.exception.fallos_limpieza)

    def comprobar_limpiezas(self, fallar_roles):
        self.cfg.inicializar().close()
        real = Path.unlink
        intentados = []
        def eliminar(ruta, *args, **kwargs):
            if ruta.name.startswith(".sonda-"):
                rol = ("sonda_staging" if ruta.parent == self.cfg.staging else
                       "sonda_publicada" if ruta.parent == self.cfg.raiz / "sha256" else "sonda_entrada")
                intentados.append(rol)
                if rol in fallar_roles:
                    error = PermissionError(13, "CREDENCIAL_SINTETICA_62D", "CREDENCIAL_SINTETICA_62D")
                    error.add_note("CREDENCIAL_SINTETICA_62D")
                    raise error
            return real(ruta, *args, **kwargs)
        with patch.object(Path, "unlink", eliminar):
            error = self.comprobar_privacidad(self.cfg.abrir)
        self.assertEqual(intentados, ["sonda_staging", "sonda_publicada", "sonda_entrada"])
        self.assertEqual(error.codigo, "limpieza_sondas_incompleta")
        self.assertEqual({r for r, c in error.fallos_limpieza}, set(fallar_roles))
        self.assertEqual({c for r, c in error.fallos_limpieza}, {"eliminacion_no_disponible"})
        self.assertNotIn("CREDENCIAL_SINTETICA_62D", repr(error.diagnostico_publico()))

    def test_fallo_primera_limpieza_intenta_todas(self):
        self.comprobar_limpiezas({"sonda_staging"})

    def test_fallo_segunda_limpieza_intenta_todas(self):
        self.comprobar_limpiezas({"sonda_publicada"})

    def test_fallo_varias_limpiezas_informa_todos(self):
        self.comprobar_limpiezas({"sonda_staging", "sonda_publicada", "sonda_entrada"})

    def comprobar_privacidad(self, operacion):
        try:
            operacion()
        except ErrorAlmacenamientoRAW as error:
            salida = StringIO()
            logger = logging.Logger("cierre_raw_aislado")
            logger.addHandler(logging.StreamHandler(salida))
            logger.error("fallo tecnico", exc_info=True)
            self.assertIsNone(error.__cause__)
            self.assertIsNone(error.__context__)
            self.assertFalse(getattr(error, "__notes__", ()))
            for texto in (str(error), repr(error.args), repr(vars(error)),
                          "".join(traceback.format_exception(error)), salida.getvalue()):
                self.assertNotIn("CREDENCIAL_SINTETICA_62D", texto)
            return error
        self.fail("Se esperaba un error publico")

    def test_json_invalido_no_conserva_documento_en_contexto(self):
        self.cfg.inicializar().close()
        (self.cfg.raiz / "spica-raw.json").write_text(
            '{"token":"CREDENCIAL_SINTETICA_62D",', encoding="utf-8")
        error = self.comprobar_privacidad(self.cfg.validar)
        self.assertEqual(error.codigo, "marcador_raw_invalido")

    def test_permiso_no_conserva_ruta_en_contexto(self):
        error = PermissionError(13, "CREDENCIAL_SINTETICA_62D", "CREDENCIAL_SINTETICA_62D")
        with patch("spica.adquisicion.almacenamiento.configuracion._directorio", side_effect=error):
            publico = self.comprobar_privacidad(self.cfg.inicializar)
        self.assertEqual(publico.codigo, "inicializacion_raw_sin_permisos")

    def test_contexto_sensible_del_llamador_no_se_adjunta(self):
        try:
            raise RuntimeError("CREDENCIAL_SINTETICA_62D")
        except RuntimeError:
            error = self.comprobar_privacidad(self.cfg.abrir)
        self.assertEqual(error.codigo, "almacen_raw_no_inicializado")

    def test_temporal_configurado_dentro_del_codigo_rechazado(self):
        codigo = Path(__file__).resolve().parents[1]
        cfg = ConfiguracionRAW(self.cfg.raiz, inspeccion=PoliticaInspeccionRAW(directorio_temporal=codigo))
        with self.assertRaises(ErrorAlmacenamientoRAW):
            cfg.validar()
        self.assertFalse(self.cfg.raiz.exists())


class PresupuestoInspeccionTests(unittest.TestCase):
    def setUp(self):
        self.fixtures = fixtures_sqlite.InspeccionSQLiteTests(methodName="test_v2_valida")
        self.fixtures.setUp()
        self.addCleanup(self.fixtures.doCleanups)

    def test_wal_sin_espacio_rechazado_antes_de_copiar(self):
        ruta, _ = self.fixtures.crear(version=2, wal=True)
        antes = self.fixtures.instantanea(ruta)
        with patch("shutil.disk_usage", return_value=shutil._ntuple_diskusage(1, 1, 0)):
            with self.assertRaises(ErrorAlmacenamientoRAW):
                inspeccionar_catalogo(ruta)
        self.assertEqual(antes, self.fixtures.instantanea(ruta))

    def test_presupuesto_insuficiente_no_crea_snapshot(self):
        ruta, _ = self.fixtures.crear(version=2, wal=True)
        politica = PoliticaInspeccionRAW(max_bytes_temporales=1, margen_bytes=65_536)
        with patch("spica.adquisicion.almacenamiento.inspeccion.tempfile.TemporaryDirectory") as crear:
            with self.assertRaises(ErrorAlmacenamientoRAW) as error:
                inspeccionar_catalogo(ruta, politica=politica)
        self.assertEqual(error.exception.codigo, "presupuesto_inspeccion_excedido")
        crear.assert_not_called()

    def test_suma_sqlite_y_wal_excede_presupuesto(self):
        ruta, _ = self.fixtures.crear(version=2, wal=True)
        db, wal = ruta.stat().st_size, Path(str(ruta) + "-wal").stat().st_size
        # Un presupuesto que admite por separado cada archivo pero no la suma con margen.
        limite = db + wal + 65_536 - 1
        self.assertLess(db + 65_536, limite)
        self.assertLess(wal + 65_536, limite)
        antes = self.fixtures.instantanea(ruta)
        with self.assertRaises(ErrorAlmacenamientoRAW) as error:
            inspeccionar_catalogo(ruta, politica=PoliticaInspeccionRAW(
                max_bytes_temporales=limite, margen_bytes=65_536))
        self.assertEqual(error.exception.codigo, "presupuesto_inspeccion_excedido")
        self.assertEqual(antes, self.fixtures.instantanea(ruta))

    def test_aceptada_con_presupuesto_y_limpieza(self):
        ruta, _ = self.fixtures.crear(version=2, wal=True)
        antes = self.fixtures.instantanea(ruta)
        self.assertEqual(inspeccionar_catalogo(ruta, politica=PoliticaInspeccionRAW(
            max_bytes_temporales=4 * 1024**2, margen_bytes=65_536, tamano_bloque=1024)), 2)
        self.assertEqual(antes, self.fixtures.instantanea(ruta))
        self.assertEqual(list(self.fixtures.base.glob("snapshot-*")), [])

    def test_sin_wal_no_necesita_copia_ni_espacio_temporal(self):
        ruta, _ = self.fixtures.crear(version=2)
        with patch("shutil.disk_usage", side_effect=AssertionError("No hay copia")), patch(
                "spica.adquisicion.almacenamiento.inspeccion.tempfile.TemporaryDirectory",
                side_effect=AssertionError("No hay copia")):
            self.assertEqual(inspeccionar_catalogo(ruta), 2)

    def test_error_copia_limpia_snapshot_y_conserva_originales(self):
        ruta, _ = self.fixtures.crear(version=2, wal=True)
        antes = self.fixtures.instantanea(ruta)
        real = Path.open
        def abrir(archivo, mode="r", *args, **kwargs):
            if archivo == Path(str(ruta) + "-wal") and mode == "rb":
                raise OSError("CREDENCIAL_SINTETICA_62D")
            return real(archivo, mode, *args, **kwargs)
        with patch.object(Path, "open", abrir):
            with self.assertRaises(ErrorAlmacenamientoRAW) as error:
                inspeccionar_catalogo(ruta)
        self.assertIsNone(error.exception.__context__)
        self.assertEqual(list(self.fixtures.base.glob("snapshot-*")), [])
        self.assertEqual(antes, self.fixtures.instantanea(ruta))

    def test_escritura_corta_snapshot_rechazada_y_limpiada(self):
        ruta, _ = self.fixtures.crear(version=2, wal=True)
        antes = self.fixtures.instantanea(ruta)
        real = Path.open
        class Archivo:
            def __init__(self, archivo):
                self.archivo = archivo
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return self.archivo.__exit__(*args)
            def write(self, bloque):
                return self.archivo.write(bloque[:-1])
        def abrir(archivo, mode="r", *args, **kwargs):
            resultado = real(archivo, mode, *args, **kwargs)
            return Archivo(resultado) if mode == "xb" else resultado
        with patch.object(Path, "open", abrir):
            with self.assertRaises(ErrorAlmacenamientoRAW) as error:
                inspeccionar_catalogo(ruta)
        self.assertEqual(error.exception.codigo, "copia_inspeccion_incompleta")
        self.assertEqual(list(self.fixtures.base.glob("snapshot-*")), [])
        self.assertEqual(antes, self.fixtures.instantanea(ruta))

    def test_lecturas_de_copia_respetan_bloques_configurados(self):
        ruta, _ = self.fixtures.crear(version=2, wal=True)
        real = Path.open
        lecturas = []
        class Archivo:
            def __init__(self, archivo):
                self.archivo = archivo
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return self.archivo.__exit__(*args)
            def read(self, cantidad):
                lecturas.append(cantidad)
                return self.archivo.read(cantidad)
        def abrir(archivo, mode="r", *args, **kwargs):
            resultado = real(archivo, mode, *args, **kwargs)
            return Archivo(resultado) if mode == "rb" else resultado
        with patch.object(Path, "open", abrir):
            self.assertEqual(inspeccionar_catalogo(ruta, politica=PoliticaInspeccionRAW(tamano_bloque=512)), 2)
        self.assertTrue(lecturas)
        self.assertTrue(all(0 < cantidad <= 512 for cantidad in lecturas))

    def test_configuracion_propaga_politica_hasta_motor(self):
        from spica.adquisicion.almacenamiento import configuracion, catalogo
        politica = PoliticaInspeccionRAW(max_bytes_temporales=2 * 1024**2, margen_bytes=65_536)
        cfg = ConfiguracionRAW(self.fixtures.base / "gestionado", espacio_minimo_libre=1, inspeccion=politica)
        cfg.inicializar().close()
        with patch.object(configuracion, "inspeccionar_catalogo", wraps=inspeccionar_catalogo) as reconocimiento, patch.object(
                catalogo, "inspeccionar_catalogo", wraps=inspeccionar_catalogo) as motor:
            cfg.abrir().close()
        self.assertEqual(reconocimiento.call_args.kwargs["politica"], politica)
        self.assertEqual(motor.call_args.kwargs["politica"], politica)

    def test_consulta_espacio_en_padre_configurado_y_temporal_real(self):
        ruta, _ = self.fixtures.crear(version=2, wal=True)
        padre = self.fixtures.base / "volumen-temporal"
        padre.mkdir()
        llamadas = []
        @contextmanager
        def temporal(**kwargs):
            self.assertEqual(kwargs["dir"], padre)
            destino = padre / ("snapshot-" + uuid4().hex)
            destino.mkdir(mode=0o755)
            try:
                yield str(destino)
            finally:
                assert destino.resolve().parent == padre.resolve()
                shutil.rmtree(destino)
        def espacio(destino):
            llamadas.append(Path(destino))
            return shutil._ntuple_diskusage(10**9, 0, 10**9)
        with patch("spica.adquisicion.almacenamiento.inspeccion.tempfile.TemporaryDirectory", temporal), patch(
                "shutil.disk_usage", side_effect=espacio):
            self.assertEqual(inspeccionar_catalogo(ruta, politica=PoliticaInspeccionRAW(directorio_temporal=padre)), 2)
        self.assertEqual(llamadas[0], padre)
        self.assertEqual(llamadas[1].parent, padre)
        self.assertEqual(list(padre.iterdir()), [])

    def test_limpieza_fallida_conserva_error_principal(self):
        ruta, _ = self.fixtures.crear(version=1, wal=True, sql="CREATE TABLE ajena (id TEXT)")
        @contextmanager
        def temporal(**kwargs):
            destino = self.fixtures.base / ("snapshot-" + uuid4().hex)
            destino.mkdir(mode=0o755)
            try:
                yield str(destino)
            finally:
                raise PermissionError("CREDENCIAL_SINTETICA_62D")
        with patch("spica.adquisicion.almacenamiento.inspeccion.tempfile.TemporaryDirectory", temporal):
            with self.assertRaises(ErrorAlmacenamientoRAW) as error:
                inspeccionar_catalogo(ruta)
        self.assertEqual(error.exception.codigo, "catalogo_ajeno")
        self.assertEqual(error.exception.fallos_limpieza, (("snapshot_sqlite", "eliminacion_no_disponible"),))
        self.assertIsNone(error.exception.__context__)

    def test_validacion_politica(self):
        for opciones in (dict(max_bytes_temporales=True), dict(margen_bytes=1),
                         dict(tamano_bloque=2**21), dict(directorio_temporal=Path("relativa"))):
            with self.subTest(opciones=opciones), self.assertRaises(ValueError):
                PoliticaInspeccionRAW(**opciones)


if __name__ == "__main__":
    unittest.main()
