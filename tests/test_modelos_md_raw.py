"""Compatibilidad MD y migraciones solo en SQLite y archivos sintéticos temporales."""

from contextlib import closing
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import sys
import unittest
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from spica.adquisicion.almacenamiento import (
    AlmacenRAW, DeclaracionRAW, ErrorAlmacenamientoRAW, EstadoIncorporacion,
    ObjetoCientifico, ProyectoCientifico, migrar_a_v2,
)
from spica.adquisicion.nucleo import Fuente


class ModelosMDRawTests(unittest.TestCase):
    def setUp(self):
        proyecto = Path(__file__).resolve().parents[1]
        self.base = proyecto / (".suadc-test-" + uuid4().hex)
        self.base.mkdir(mode=0o755)
        assert self.base.resolve().is_relative_to(proyecto)
        self.addCleanup(shutil.rmtree, self.base)
        self.entrada = self.base / "entrada"
        self.raw = self.base / "raw"
        self.entrada.mkdir()
        self.raw.mkdir()
        self.archivo = self.entrada / "datos.csv"
        self.archivo.write_bytes(b"contenido sintetico sin formato certificado")
        self.almacen = AlmacenRAW(self.raw, (self.entrada,), max_bytes=100)
        self.addCleanup(self.almacen.close)
        self.proyecto = ProyectoCientifico(" P/01 ", "md-proyecto-1.0", "Proyecto de prueba",
                                           "Contexto sintetico", "planificado")
        self.objeto = ObjetoCientifico(" O/01 ", self.proyecto.project_id, "familia-declarada",
            "tipo-declarado", datetime(2020, 1, 2, tzinfo=timezone.utc), "registrado")
        self.declaracion = DeclaracionRAW(self.proyecto.project_id, self.objeto.object_id,
                                         Fuente("prueba", "fuente-original"), "recurso-original")

    def registrar(self):
        self.almacen.registrar_proyecto(self.proyecto)
        self.almacen.registrar_objeto(self.objeto)

    def crear_v1(self) -> Path:
        """Fixture independiente que reproduce el esquema y un activo de la versión anterior."""
        raiz = self.base / "legado"
        raiz.mkdir()
        digest = hashlib.sha256(self.archivo.read_bytes()).hexdigest()
        destino = raiz / "sha256" / digest[:2] / digest
        destino.parent.mkdir(parents=True)
        destino.write_bytes(self.archivo.read_bytes())
        datos = dict(proyecto_id=" Proyecto-legado ", objeto_id="Objeto-legado",
            fuente=dict(proveedor="prueba", identificador=" ID-fuente "), recurso_id=" ID-recurso ",
            procedencia="urn:spica:prueba:legado", parametros_publicos={"variable": " V/01 "},
            formato_declarado=None, tipo_medio_declarado=None)
        with closing(sqlite3.connect(raiz / "catalogo.sqlite3")) as c:
            c.executescript("""
                PRAGMA foreign_keys=ON;
                CREATE TABLE proyectos (id TEXT PRIMARY KEY);
                CREATE TABLE objetos (id TEXT PRIMARY KEY, proyecto_id TEXT NOT NULL REFERENCES proyectos(id));
                CREATE TABLE activos (
                    id TEXT PRIMARY KEY, objeto_id TEXT NOT NULL REFERENCES objetos(id),
                    declaracion TEXT NOT NULL, fecha_utc TEXT NOT NULL,
                    estado TEXT NOT NULL CHECK(estado IN ('preparada','verificada_localmente',
                      'incorporada','fallida','inconsistente')),
                    tamano INTEGER CHECK(tamano >= 0), sha256 TEXT, ruta_interna TEXT,
                    error TEXT, advertencias TEXT NOT NULL, comprobacion_utc TEXT);
                CREATE TABLE eventos (
                    secuencia INTEGER PRIMARY KEY, activo_id TEXT NOT NULL REFERENCES activos(id),
                    fecha_utc TEXT NOT NULL, estado TEXT NOT NULL, codigo TEXT);
                PRAGMA user_version=1;
            """)
            with c:
                c.execute("INSERT INTO proyectos VALUES (?)", (datos["proyecto_id"],))
                c.execute("INSERT INTO objetos VALUES (?,?)", (datos["objeto_id"], datos["proyecto_id"]))
                c.execute("INSERT INTO activos VALUES (?,?,?,?,?,?,?,?,?,?,?)", (
                    "activo-legado", datos["objeto_id"], json.dumps(datos, ensure_ascii=False),
                    "2021-02-03T00:00:00+00:00", "incorporada", len(self.archivo.read_bytes()), digest,
                    destino.relative_to(raiz).as_posix(), None, '["aviso-legado"]', "2021-02-03T00:00:00+00:00"))
                c.execute("INSERT INTO eventos VALUES (1,?,?,?,?)",
                          ("activo-legado", "2021-02-03T00:00:00+00:00", "incorporada", None))
        return raiz

    def test_creacion_proyecto_con_metadatos(self):
        self.assertEqual(self.almacen.registrar_proyecto(self.proyecto), self.proyecto)
        self.assertEqual(self.almacen.consultar_proyecto(self.proyecto.project_id), self.proyecto)

    def test_creacion_objeto_con_metadatos_y_fecha_explicita(self):
        self.registrar()
        self.assertEqual(self.almacen.consultar_objeto(self.objeto.object_id), self.objeto)
        activo = self.almacen.incorporar(self.archivo, self.declaracion)
        self.assertNotEqual(self.objeto.created_at, activo.fecha_utc)

    def test_estados_proyecto_objeto_y_adquisicion_independientes(self):
        self.registrar()
        activo = self.almacen.incorporar(self.archivo, self.declaracion)
        self.assertEqual(self.almacen.consultar_proyecto(self.proyecto.project_id).estado, "planificado")
        self.assertEqual(self.almacen.consultar_objeto(self.objeto.object_id).state, "registrado")
        self.assertEqual(activo.estado, EstadoIncorporacion.INCORPORADA)

    def test_metadatos_desconocidos_no_se_inventan(self):
        self.almacen.incorporar(self.archivo, self.declaracion)
        self.assertEqual(self.almacen.consultar_proyecto(self.proyecto.project_id), ProyectoCientifico(self.proyecto.project_id))
        self.assertEqual(self.almacen.consultar_objeto(self.objeto.object_id), ObjetoCientifico(self.objeto.object_id, self.proyecto.project_id))

    def test_schema_version_proyecto_independiente_de_sqlite(self):
        self.almacen.registrar_proyecto(replace(self.proyecto, schema_version="modelo-2030.5"))
        self.assertEqual(self.almacen._catalogo.conexion.execute("PRAGMA user_version").fetchone()[0], 2)
        self.assertEqual(self.almacen.consultar_proyecto(self.proyecto.project_id).schema_version, "modelo-2030.5")

    def test_md03_aliases_sin_identidad_duplicada_y_sin_inferir_csv(self):
        activo = self.almacen.incorporar(self.archivo, self.declaracion)
        self.assertEqual(activo.asset_id, activo.activo_id)
        self.assertEqual(activo.object_id, self.objeto.object_id)
        self.assertEqual(activo.size_bytes, len(self.archivo.read_bytes()))
        self.assertEqual(activo.storage_ref, activo.ruta_interna)
        self.assertEqual(activo.sha256, hashlib.sha256(self.archivo.read_bytes()).hexdigest())
        self.assertIsNone(activo.media_detected)

    def test_objeto_independiente_de_nombre_y_contenido(self):
        self.registrar()
        primero = self.almacen.incorporar(self.archivo, self.declaracion)
        nueva = self.entrada / "otro.bin"
        nueva.write_bytes(b"contenido diferente")
        segundo = self.almacen.incorporar(nueva, self.declaracion)
        self.assertEqual(primero.object_id, segundo.object_id)
        self.assertNotEqual(primero.sha256, segundo.sha256)
        self.assertEqual(self.almacen.consultar_objeto(primero.object_id), self.objeto)

    def test_adquisiciones_identicas_no_se_fusionan(self):
        self.registrar()
        primero = self.almacen.incorporar(self.archivo, self.declaracion)
        segundo = self.almacen.incorporar(self.archivo, self.declaracion)
        self.assertNotEqual(primero.asset_id, segundo.asset_id)
        self.assertEqual(primero.storage_ref, segundo.storage_ref)
        self.assertEqual(primero.object_id, segundo.object_id)

    def test_registro_idempotente_y_completar_desconocidos(self):
        self.almacen.incorporar(self.archivo, self.declaracion)
        self.registrar()
        self.registrar()
        self.assertEqual(self.almacen.consultar_objeto(self.objeto.object_id), self.objeto)
        self.assertEqual(self.almacen._catalogo.conexion.execute("SELECT COUNT(*) FROM objetos").fetchone()[0], 1)

    def test_conflictos_no_sobrescriben_ni_reasignan_ids(self):
        self.registrar()
        with self.assertRaises(ErrorAlmacenamientoRAW):
            self.almacen.registrar_proyecto(replace(self.proyecto, nombre="Otro nombre"))
        with self.assertRaises(ErrorAlmacenamientoRAW):
            self.almacen.registrar_objeto(replace(self.objeto, kind="otro tipo"))
        otro = ProyectoCientifico("otro-proyecto")
        self.almacen.registrar_proyecto(otro)
        with self.assertRaises(ErrorAlmacenamientoRAW):
            self.almacen.registrar_objeto(replace(self.objeto, project_id=otro.project_id))
        self.assertEqual(self.almacen.consultar_proyecto(self.proyecto.project_id), self.proyecto)
        self.assertEqual(self.almacen.consultar_objeto(self.objeto.object_id), self.objeto)

    def test_claves_externas_y_padre_obligatorio(self):
        with self.assertRaises(ErrorAlmacenamientoRAW):
            self.almacen.registrar_objeto(self.objeto)
        c = self.almacen._catalogo.conexion
        with self.assertRaises(sqlite3.IntegrityError), c:
            c.execute("INSERT INTO objetos(id,proyecto_id) VALUES ('huerfano','inexistente')")
        self.assertEqual(c.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_modelos_rechazan_identidades_y_fechas_invalidas(self):
        for crear in (lambda: ProyectoCientifico(""), lambda: ProyectoCientifico(None),
                      lambda: ObjetoCientifico("o", " "),
                      lambda: replace(self.objeto, created_at=datetime(2020, 1, 1)),
                      lambda: replace(self.proyecto, estado=EstadoIncorporacion.INCORPORADA)):
            with self.assertRaises(ValueError):
                crear()

    def test_metadatos_nuevos_no_evaden_filtro_de_secretos(self):
        with self.assertRaises(ErrorAlmacenamientoRAW):
            self.almacen.registrar_proyecto(replace(self.proyecto, contexto="token=secreto-sintetico"))
        self.assertEqual(self.almacen._catalogo.conexion.execute("SELECT COUNT(*) FROM proyectos").fetchone()[0], 0)

    def test_reapertura_conserva_identificadores_y_metadatos(self):
        self.registrar()
        activo = self.almacen.incorporar(self.archivo, self.declaracion)
        with AlmacenRAW(self.raw, (self.entrada,)) as otro:
            self.assertEqual(otro.consultar_proyecto(self.proyecto.project_id), self.proyecto)
            self.assertEqual(otro.consultar_objeto(self.objeto.object_id), self.objeto)
            self.assertEqual(otro.metadatos(activo.asset_id), activo)

    def test_abrir_v1_no_migra_y_conserva_operaciones_anteriores(self):
        raiz = self.crear_v1()
        with AlmacenRAW(raiz, (self.entrada,)) as legado:
            self.assertEqual(legado._catalogo.conexion.execute("PRAGMA user_version").fetchone()[0], 1)
            activo = legado.metadatos("activo-legado")
            self.assertIsNone(activo.media_detected)
            self.assertIsNone(legado.consultar_objeto(activo.object_id).created_at)
            self.assertTrue(legado.verificar(activo.asset_id).coincide)
            legado.incorporar(self.archivo, activo.declaracion)
            with self.assertRaises(ErrorAlmacenamientoRAW) as contexto:
                legado.registrar_proyecto(ProyectoCientifico(activo.declaracion.proyecto_id, nombre="nuevo dato"))
            self.assertEqual(contexto.exception.codigo, "migracion_explicita_requerida")
            self.assertEqual(legado._catalogo.conexion.execute("PRAGMA user_version").fetchone()[0], 1)

    def test_migracion_conserva_todas_las_columnas_filas_y_relaciones_v1(self):
        raiz = self.crear_v1()
        with closing(sqlite3.connect(raiz / "catalogo.sqlite3")) as c:
            tablas = ("proyectos", "objetos", "activos", "eventos")
            columnas = {t: tuple(f[1] for f in c.execute(f"PRAGMA table_info({t})")) for t in tablas}
            anterior = {t: c.execute(f"SELECT {','.join(columnas[t])} FROM {t}").fetchall() for t in tablas}
            migrar_a_v2(c)
            self.assertEqual(c.execute("PRAGMA user_version").fetchone()[0], 2)
            for tabla in tablas:
                self.assertEqual(c.execute(f"SELECT {','.join(columnas[tabla])} FROM {tabla}").fetchall(), anterior[tabla])
            self.assertEqual(c.execute("PRAGMA foreign_key_check").fetchall(), [])
            self.assertEqual(c.execute("SELECT schema_version,nombre,contexto,estado FROM proyectos").fetchone(), (None,) * 4)
            self.assertEqual(c.execute("SELECT family,kind,created_at,state FROM objetos").fetchone(), (None,) * 4)
        with AlmacenRAW(raiz, (self.entrada,)) as legado:
            self.assertEqual(legado.recuperar("activo-legado").read_bytes(), self.archivo.read_bytes())
            self.assertEqual(legado.metadatos("activo-legado").declaracion.recurso_id, " ID-recurso ")
            legado.registrar_proyecto(ProyectoCientifico(" Proyecto-legado ", nombre="Dato explicito"))

    def test_migracion_idempotente_no_modifica_segunda_vez(self):
        raiz = self.crear_v1()
        with closing(sqlite3.connect(raiz / "catalogo.sqlite3")) as c:
            migrar_a_v2(c)
            antes = tuple(c.iterdump())
            version = c.execute("PRAGMA schema_version").fetchone()[0]
            migrar_a_v2(c)
            self.assertEqual(tuple(c.iterdump()), antes)
            self.assertEqual(c.execute("PRAGMA schema_version").fetchone()[0], version)

    def test_migracion_fallida_revierte_ddl_y_version(self):
        raiz = self.crear_v1()
        class ConexionFallida(sqlite3.Connection):
            def execute(self, sentencia, *args, **kwargs):
                if sentencia == "ALTER TABLE objetos ADD COLUMN kind TEXT":
                    raise sqlite3.OperationalError("fallo sintetico de DDL")
                return super().execute(sentencia, *args, **kwargs)
        with closing(sqlite3.connect(raiz / "catalogo.sqlite3", factory=ConexionFallida)) as c:
            antes = tuple(c.iterdump())
            with self.assertRaises(sqlite3.OperationalError):
                migrar_a_v2(c)
            self.assertEqual(c.execute("PRAGMA user_version").fetchone()[0], 1)
            self.assertEqual(tuple(c.iterdump()), antes)

    def test_migracion_no_confirma_transaccion_del_llamador(self):
        raiz = self.crear_v1()
        with closing(sqlite3.connect(raiz / "catalogo.sqlite3")) as c:
            c.execute("INSERT INTO proyectos VALUES ('pendiente')")
            with self.assertRaises(ErrorAlmacenamientoRAW):
                migrar_a_v2(c)
            self.assertTrue(c.in_transaction)
            c.rollback()
            self.assertEqual(c.execute("PRAGMA user_version").fetchone()[0], 1)

    def test_migracion_rechaza_version_desconocida_sin_alterarla(self):
        with closing(sqlite3.connect(":memory:")) as c:
            c.execute("PRAGMA user_version=99")
            with self.assertRaises(ErrorAlmacenamientoRAW):
                migrar_a_v2(c)
            self.assertEqual(c.execute("PRAGMA user_version").fetchone()[0], 99)

    def test_migracion_rechaza_relaciones_rotas_sin_cambiar_datos(self):
        raiz = self.crear_v1()
        with closing(sqlite3.connect(raiz / "catalogo.sqlite3")) as c:
            with c:
                c.execute("UPDATE objetos SET proyecto_id='inexistente'")
            antes = tuple(c.iterdump())
            with self.assertRaises(ErrorAlmacenamientoRAW) as contexto:
                migrar_a_v2(c)
            self.assertEqual(contexto.exception.codigo, "relaciones_catalogo_inconsistentes")
            self.assertEqual(tuple(c.iterdump()), antes)
            self.assertEqual(c.execute("PRAGMA user_version").fetchone()[0], 1)

    def test_identidad_se_conserva_al_cambiar_ubicacion_del_almacen(self):
        self.registrar()
        activo = self.almacen.incorporar(self.archivo, self.declaracion)
        self.almacen.close()
        nueva = self.base / "otra-instalacion"
        shutil.copytree(self.raw, nueva)
        with AlmacenRAW(nueva, (self.entrada,)) as otro:
            self.assertEqual(otro.consultar_proyecto(self.proyecto.project_id), self.proyecto)
            self.assertEqual(otro.consultar_objeto(self.objeto.object_id), self.objeto)
            self.assertEqual(otro.metadatos(activo.asset_id), activo)
            self.assertTrue(otro.recuperar(activo.asset_id).is_relative_to(nueva))


if __name__ == "__main__":
    unittest.main()
