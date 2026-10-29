"""Regresiones SUADC-01/02: mocks y SQLite sintético, sin servicios externos."""

from contextlib import closing, contextmanager
from io import StringIO
import logging
from pathlib import Path
import shutil
import sqlite3
import ssl
import sys
import tempfile
import traceback
import unittest
from unittest.mock import patch
from uuid import uuid4

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from spica.adquisicion.almacenamiento import AlmacenRAW, ConfiguracionRAW, ErrorAlmacenamientoRAW
from spica.adquisicion.almacenamiento.catalogo import CatalogoRAW
from spica.adquisicion.transportes import (
    ClienteHTTP, ErrorDescargaArchivo, ErrorTransporteHTTP, PoliticaReintentos, TipoErrorHTTP,
)
from test_transporte_http import Flujo


class _Temporal(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.gettempdir()).resolve() / ("spica-regresion-" + uuid4().hex)
        assert not self.base.is_relative_to(Path(__file__).resolve().parents[1])
        self.base.mkdir(mode=0o755)
        self.addCleanup(shutil.rmtree, self.base)


class ExcepcionesPublicasTests(_Temporal):
    MARCA = "MARCADOR_SINTETICO_SUADC01"
    ORIGEN = "https://sintetico.invalid"

    def cliente(self, clase=httpx.ReadError, *, tls=False, intentos=1, parcial=False):
        self.llamadas = []
        def handler(request):
            self.llamadas.append(request)
            error = clase("token=" + self.MARCA, request=request)
            error.add_note("Authorization: Bearer " + self.MARCA)
            if tls:
                error.__cause__ = ssl.SSLError("certificate " + self.MARCA)
            if parcial:
                return httpx.Response(200, stream=Flujo((b"fragmento",), error))
            raise error
        cliente = ClienteHTTP((self.ORIGEN,), transporte=httpx.MockTransport(handler),
            politica_reintentos=PoliticaReintentos(max_intentos=intentos, jitter=0), espera=lambda s: None)
        self.addCleanup(cliente.close)
        return cliente

    def capturar(self, operacion):
        try:
            operacion()
        except ErrorTransporteHTTP as error:
            salida = StringIO()
            logger = logging.Logger("regresion_aislada")
            logger.addHandler(logging.StreamHandler(salida))
            logger.error("fallo tecnico", exc_info=True)
            return error, salida.getvalue()
        self.fail("Se esperaba un error tecnico")

    def comprobar_publico(self, error, registro):
        self.assertFalse(self.MARCA in str(error))
        self.assertFalse(self.MARCA in repr(error.__dict__))
        self.assertFalse(self.MARCA in "".join(traceback.format_exception(error)))
        self.assertFalse(self.MARCA in registro)
        self.assertIsNone(error.__cause__)
        self.assertIsNone(error.__context__)
        self.assertFalse(getattr(error, "__notes__", ()))
        self.assertFalse(self.MARCA in repr(error.diagnostico_publico()))

    def test_get_no_expone_httpx_causas_contextos_notas(self):
        c = self.cliente()
        e, registro = self.capturar(lambda: c.get(self.ORIGEN + "/archivo?token=" + self.MARCA))
        self.comprobar_publico(e, registro)
        self.assertEqual(e.tipo, TipoErrorHTTP.TRANSPORTE)
        self.assertEqual(e.fase, "get")

    def test_timeout_publico(self):
        c = self.cliente(httpx.ReadTimeout)
        e, registro = self.capturar(lambda: c.get(self.ORIGEN))
        self.comprobar_publico(e, registro)
        self.assertEqual(e.tipo, TipoErrorHTTP.TIMEOUT)

    def test_tls_publico_no_reintenta(self):
        c = self.cliente(httpx.ConnectError, tls=True, intentos=3)
        e, registro = self.capturar(lambda: c.get(self.ORIGEN))
        self.comprobar_publico(e, registro)
        self.assertEqual(e.tipo, TipoErrorHTTP.TLS)
        self.assertEqual(len(self.llamadas), 1)

    def test_conexion_publica(self):
        c = self.cliente(httpx.ConnectError)
        e, registro = self.capturar(lambda: c.get(self.ORIGEN))
        self.comprobar_publico(e, registro)
        self.assertEqual(e.tipo, TipoErrorHTTP.CONEXION)

    def test_agotamiento_conserva_diagnostico_seguro(self):
        c = self.cliente(intentos=3)
        e, registro = self.capturar(lambda: c.get(self.ORIGEN))
        self.comprobar_publico(e, registro)
        self.assertEqual(e.intentos, 3)
        self.assertTrue(e.agotados)
        self.assertEqual(len(e.historial), 3)

    def test_descarga_parcial_limpia_y_publica_error_seguro(self):
        c = self.cliente(parcial=True, intentos=2)
        e, registro = self.capturar(lambda: c.descargar(self.ORIGEN + "/archivo?token=" + self.MARCA,
            self.base, "archivo.bin", max_bytes=100, tamano_bloque=2))
        self.comprobar_publico(e, registro)
        self.assertIsInstance(e, ErrorDescargaArchivo)
        self.assertEqual(e.fase, "descargar")
        self.assertEqual(e.intentos, 2)
        self.assertEqual(list(self.base.iterdir()), [])

    def test_contexto_del_llamador_no_se_adjunta_al_error_publico(self):
        c = self.cliente()
        try:
            raise RuntimeError("password=" + self.MARCA)
        except RuntimeError:
            e, registro = self.capturar(lambda: c.get(self.ORIGEN))
        self.comprobar_publico(e, registro)

    def test_codigo_http_sigue_disponible(self):
        with ClienteHTTP((self.ORIGEN,), transporte=httpx.MockTransport(
            lambda r: httpx.Response(403, stream=Flujo()))) as c:
            e, registro = self.capturar(lambda: c.get(self.ORIGEN))
        self.comprobar_publico(e, registro)
        self.assertEqual(e.codigo_http, 403)

    def test_url_invalida_no_expone_causa_de_httpx(self):
        # HTTPX incluye el puerto inválido en InvalidURL; no debe encadenarse.
        with ClienteHTTP((self.ORIGEN,), transporte=httpx.MockTransport(lambda r: None)) as c:
            try:
                c.get(self.ORIGEN + ":token=" + self.MARCA)
            except ValueError as error:
                self.assertFalse(self.MARCA in "".join(traceback.format_exception(error)))
                self.assertIsNone(error.__cause__)
                self.assertIsNone(error.__context__)
            else:
                self.fail("URL invalida aceptada")


# Fixture independiente del esquema de producción, incluido el legado real v1.
_V1 = """
CREATE TABLE proyectos (id TEXT PRIMARY KEY);
CREATE TABLE objetos (id TEXT PRIMARY KEY, proyecto_id TEXT NOT NULL REFERENCES proyectos(id));
CREATE TABLE activos (
 id TEXT PRIMARY KEY, objeto_id TEXT NOT NULL REFERENCES objetos(id),
 declaracion TEXT NOT NULL, fecha_utc TEXT NOT NULL, estado TEXT NOT NULL
 CHECK(estado IN ('preparada','verificada_localmente','incorporada','fallida','inconsistente')),
 tamano INTEGER CHECK(tamano >= 0), sha256 TEXT, ruta_interna TEXT, error TEXT,
 advertencias TEXT NOT NULL, comprobacion_utc TEXT);
CREATE TABLE eventos (secuencia INTEGER PRIMARY KEY, activo_id TEXT NOT NULL REFERENCES activos(id),
 fecha_utc TEXT NOT NULL, estado TEXT NOT NULL, codigo TEXT);
"""
_V2 = (
    ("proyectos", "schema_version"), ("proyectos", "nombre"), ("proyectos", "contexto"), ("proyectos", "estado"),
    ("objetos", "family"), ("objetos", "kind"), ("objetos", "created_at"), ("objetos", "state"),
    ("activos", "media_detected"),
)


class InspeccionSQLiteTests(_Temporal):
    def setUp(self):
        super().setUp()
        # El aislamiento de Codex no puede reabrir directorios con la ACL privada
        # de mkdtemp en Windows. Solo para fixtures sintéticos, inyectar un
        # contenedor heredado del directorio de prueba. SQLite/DB/WAL son reales.
        @contextmanager
        def temporal_sintetico(**opciones):
            ruta = self.base / ("snapshot-" + uuid4().hex)
            ruta.mkdir(mode=0o755)
            try:
                yield str(ruta)
            finally:
                assert ruta.resolve().parent == self.base.resolve()
                shutil.rmtree(ruta)
        parche = patch("spica.adquisicion.almacenamiento.inspeccion.tempfile.TemporaryDirectory",
                       temporal_sintetico)
        parche.start()
        self.addCleanup(parche.stop)

    def crear(self, *, version=1, sql=_V1, wal=False):
        ruta = self.base / (uuid4().hex + ".sqlite3")
        c = sqlite3.connect(ruta)
        self.addCleanup(c.close)
        if wal:
            c.execute("PRAGMA journal_mode=WAL")
            c.execute("PRAGMA wal_autocheckpoint=0")
        c.executescript(sql)
        if version == 2 and sql == _V1:
            for tabla, columna in _V2:
                c.execute(f"ALTER TABLE {tabla} ADD COLUMN {columna} TEXT")
        c.execute(f"PRAGMA user_version={version}")
        c.commit()
        return ruta, c

    def instantanea(self, ruta):
        return {p.name: p.read_bytes() for p in ruta.parent.iterdir()
                if p.is_file() and p.name.startswith(ruta.name)}

    def rechazar_sin_cambios(self, ruta):
        antes = self.instantanea(ruta)
        with self.assertRaises(ErrorAlmacenamientoRAW):
            c = CatalogoRAW(ruta)
            self.addCleanup(c.close)
        self.assertEqual(antes, self.instantanea(ruta))

    def test_base_ajena_wal_v0_no_cambia_ni_auxiliares(self):
        ruta, c = self.crear(version=0, sql="CREATE TABLE ajena (valor TEXT);", wal=True)
        self.rechazar_sin_cambios(ruta)
        self.assertEqual(c.execute("PRAGMA journal_mode").fetchone()[0], "wal")

    def test_base_ajena_version_uno_rechazada(self):
        ruta, _ = self.crear(sql="CREATE TABLE ajena (valor TEXT);")
        self.rechazar_sin_cambios(ruta)

    def test_base_ajena_version_dos_rechazada(self):
        ruta, _ = self.crear(version=2, sql="CREATE TABLE ajena (valor TEXT);")
        self.rechazar_sin_cambios(ruta)

    def test_base_vacia_existente_no_se_adopta(self):
        ruta = self.base / "vacia.sqlite3"
        ruta.touch()
        self.rechazar_sin_cambios(ruta)

    def test_version_sin_esquema_no_se_adopta(self):
        ruta, _ = self.crear(sql="")
        self.rechazar_sin_cambios(ruta)

    def test_v1_real_valida_sin_migracion(self):
        ruta, c = self.crear()
        antes = self.instantanea(ruta)
        raw = CatalogoRAW(ruta)
        raw.close()
        self.assertEqual(c.execute("PRAGMA user_version").fetchone()[0], 1)
        self.assertEqual(antes, self.instantanea(ruta))

    def test_v2_valida(self):
        ruta, _ = self.crear(version=2)
        raw = CatalogoRAW(ruta)
        self.assertEqual(raw.listar(), ())
        raw.close()

    def test_v2_sin_columna_obligatoria(self):
        ruta, c = self.crear(version=2)
        c.execute("ALTER TABLE proyectos DROP COLUMN nombre")
        c.commit()
        self.rechazar_sin_cambios(ruta)

    def test_sin_relacion_obligatoria(self):
        ruta, _ = self.crear(sql=_V1.replace(" REFERENCES proyectos(id)", ""))
        self.rechazar_sin_cambios(ruta)

    def test_sin_restriccion_de_estado(self):
        sql = _V1.replace("CHECK(estado IN ('preparada','verificada_localmente','incorporada','fallida','inconsistente'))", "")
        ruta, _ = self.crear(sql=sql)
        self.rechazar_sin_cambios(ruta)

    def test_filas_con_relaciones_rotas_rechazadas(self):
        ruta, c = self.crear()
        c.execute("INSERT INTO objetos VALUES ('objeto', 'proyecto_ausente')")
        c.commit()
        self.rechazar_sin_cambios(ruta)

    def test_wal_valido_con_esquema_y_datos_sin_checkpoint(self):
        ruta, c = self.crear(version=2, wal=True)
        c.execute("INSERT INTO proyectos(id,nombre) VALUES ('p','sintetico')")
        c.commit()
        raw = CatalogoRAW(ruta)
        try:
            self.assertEqual(raw.consultar_proyecto('p').nombre, 'sintetico')
            self.assertEqual(raw.conexion.execute("PRAGMA journal_mode").fetchone()[0], "wal")
        finally:
            raw.close()

    def test_inspeccion_ruta_inexistente_no_crea_archivo(self):
        from spica.adquisicion.almacenamiento.inspeccion import inspeccionar_catalogo
        ruta = self.base / "no_existe.sqlite3"
        with self.assertRaises(ErrorAlmacenamientoRAW):
            inspeccionar_catalogo(ruta)
        self.assertFalse(ruta.exists())

    def test_configuracion_rechaza_v2_incompleto(self):
        cfg = ConfiguracionRAW(self.base / "raw", espacio_minimo_libre=1)
        cfg.inicializar().close()
        ruta = cfg.raiz / "catalogo.sqlite3"
        with closing(sqlite3.connect(ruta)) as c:
            c.execute("ALTER TABLE objetos DROP COLUMN kind")
            c.commit()
        antes = self.instantanea(ruta)
        with self.assertRaises(ErrorAlmacenamientoRAW):
            cfg.validar()
        self.assertEqual(antes, self.instantanea(ruta))

    def test_base_ajena_wal_v1_no_toca_auxiliares(self):
        ruta, _ = self.crear(version=1, sql="CREATE TABLE ajena (valor TEXT);", wal=True)
        self.rechazar_sin_cambios(ruta)

    def test_base_ajena_wal_cerrada_no_cambia_diario(self):
        ruta, c = self.crear(version=0, sql="CREATE TABLE ajena (valor TEXT);", wal=True)
        c.close()
        self.rechazar_sin_cambios(ruta)

    def test_inspeccion_wal_valido_no_toca_original_ni_auxiliares(self):
        from spica.adquisicion.almacenamiento.inspeccion import inspeccionar_catalogo
        ruta, _ = self.crear(version=2, wal=True)
        antes = self.instantanea(ruta)
        self.assertEqual(inspeccionar_catalogo(ruta), 2)
        self.assertEqual(antes, self.instantanea(ruta))

    def test_auxiliar_huerfano_no_provoca_creacion_de_base(self):
        ruta = self.base / "ausente.sqlite3"
        Path(str(ruta) + "-wal").write_bytes(b"auxiliar_sintetico")
        self.rechazar_sin_cambios(ruta)
        self.assertFalse(ruta.exists())

    def test_rechazo_raw_no_crea_directorios_del_motor(self):
        raiz = self.base / "raw_ajeno"
        raiz.mkdir()
        ruta = raiz / "catalogo.sqlite3"
        with closing(sqlite3.connect(ruta)) as c:
            c.execute("CREATE TABLE ajena (valor TEXT)")
        antes = set(raiz.iterdir())
        with self.assertRaises(ErrorAlmacenamientoRAW):
            AlmacenRAW(raiz, (self.base,))
        self.assertEqual(antes, set(raiz.iterdir()))

    def test_sin_restriccion_tamano_rechazado(self):
        ruta, _ = self.crear(sql=_V1.replace("CHECK(tamano >= 0)", ""))
        self.rechazar_sin_cambios(ruta)

    def test_sin_clave_primaria_rechazado(self):
        ruta, _ = self.crear(sql=_V1.replace("id TEXT PRIMARY KEY, objeto_id", "id TEXT, objeto_id"))
        self.rechazar_sin_cambios(ruta)

    def test_literales_check_no_se_normalizan(self):
        ruta, _ = self.crear(sql=_V1.replace("'incorporada'", "'in corporada'"))
        self.rechazar_sin_cambios(ruta)

    def test_columna_tipo_incompatible(self):
        ruta, _ = self.crear(sql=_V1.replace("tamano INTEGER", "tamano TEXT"))
        self.rechazar_sin_cambios(ruta)

    def test_application_id_ajeno_rechazado(self):
        ruta, c = self.crear(version=2)
        c.execute("PRAGMA application_id=42")
        self.rechazar_sin_cambios(ruta)

    def test_archivo_no_sqlite_rechazado(self):
        ruta = self.base / "falso.sqlite3"
        ruta.write_bytes(b"archivo sintetico que no es SQLite")
        self.rechazar_sin_cambios(ruta)

    def test_esquema_con_version_cero_no_se_adopta(self):
        ruta, _ = self.crear(version=0)
        self.rechazar_sin_cambios(ruta)

    def test_indice_no_unico_adicional_admitido(self):
        ruta, c = self.crear(version=2)
        c.execute("CREATE INDEX indice_nombre ON proyectos(nombre)")
        raw = CatalogoRAW(ruta)
        raw.close()

    def test_trigger_desconocido_rechazado_sin_ejecutar(self):
        ruta, c = self.crear()
        c.execute("CREATE TRIGGER desconocido AFTER INSERT ON proyectos BEGIN DELETE FROM objetos; END")
        self.rechazar_sin_cambios(ruta)

    def test_prefijo_parecido_a_sqlite_no_oculta_objetos_ajenos(self):
        # En LIKE, '_' consume cualquier carácter: solo 'sqlite_' es reservado.
        sentencias = (
            "CREATE TABLE sqliteXajena (valor TEXT)",
            "CREATE TRIGGER sqliteXajeno AFTER INSERT ON proyectos BEGIN DELETE FROM objetos; END",
        )
        for sql in sentencias:
            with self.subTest(sql=sql):
                ruta, c = self.crear()
                c.execute(sql)
                self.rechazar_sin_cambios(ruta)

    def test_diario_rollback_requiere_revision(self):
        ruta, _ = self.crear()
        Path(str(ruta) + "-journal").write_bytes(b"diario sintetico incompleto")
        self.rechazar_sin_cambios(ruta)


if __name__ == "__main__":
    unittest.main()
