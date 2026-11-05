"""Regresiones del procedimiento 84-C; archivos y contenido exclusivamente ficticios."""

from contextlib import closing
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
from threading import Event
import unittest
from unittest.mock import patch

from herramientas import piloto_pnda_84c as piloto
from spica.adquisicion.catalogo import EstadoVerificacion as V, EvidenciaDocumental, ProcedenciaCatalogo
from spica.adquisicion.catalogo.evidencias import empaquetar
from spica.adquisicion.catalogo.persistencia import _datos
from spica.adquisicion.consultas_locales.modelos import ENCABEZADO_SENAMHI
from spica.adquisicion.almacenamiento.modelos import DeclaracionRAW
from spica.adquisicion.nucleo import Fuente
from spica.interoperabilidad import EstadoAptitud as E
from spica.interoperabilidad.operaciones import evaluar_operacion


class PilotoLocalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory(prefix="spica-84c-fixture-")
        self.addCleanup(self.tmp.cleanup)
        self.raiz = Path(self.tmp.name)
        self.fuente = Fuente("institucion-ficticia", "fuente-ficticia")
        self._crear()

    def _crear(self, filas=2):
        # Solo replica el esquema de selección necesario, no un almacén operativo.
        contenido = (",".join(ENCABEZADO_SENAMHI) + "\n" + "".join(
            f"{n},CANDARAVE,20150101,{n}0000,,, ,1.0,2.0,3.0,RED-FICTICIA,,,,12345.0,20150102\n"
            for n in range(filas))).encode()
        self.hash = hashlib.sha256(contenido).hexdigest()
        self.ruta = self.raiz / "sha256" / self.hash[:2] / self.hash
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        self.ruta.write_bytes(contenido)
        self.tamano = len(contenido)
        self.db = self.raiz / "catalogo.sqlite3"
        instante = datetime(2026, 1, 1, tzinfo=timezone.utc)
        proc = ProcedenciaCatalogo("https://pnda-ficticia.invalid/documento", instante, "revision_ficticia", "evidencia-ficticia")
        self.doc = EvidenciaDocumental(self.fuente, "https://pnda-ficticia.invalid/recurso.csv", "producto-ficticio",
            descubierta_utc=instante, estado=V.VERIFICADO, procedencia=proc)
        declaracion = DeclaracionRAW("proyecto-ficticio", "objeto-ficticio", self.fuente, self.doc.recurso_id,
            parametros_publicos={"producto_id": self.doc.producto_id}, formato_declarado="csv")
        datos = _datos(declaracion)
        datos["parametros_publicos"] = dict(declaracion.parametros_publicos)
        datos["_evidencia_adquisicion"] = empaquetar(self.doc, declaracion, self.doc.recurso_id, instante)
        with closing(sqlite3.connect(self.db)) as c, c:
            c.execute("CREATE TABLE activos (id TEXT PRIMARY KEY,objeto_id TEXT,declaracion TEXT,fecha_utc TEXT,"
                      "estado TEXT,tamano INTEGER,sha256 TEXT,ruta_interna TEXT,error TEXT,advertencias TEXT,"
                      "comprobacion_utc TEXT,media_detected TEXT)")
            c.execute("PRAGMA user_version=2")
            c.execute("INSERT INTO activos VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (
                "activo-ficticio", "objeto-ficticio", json.dumps(datos), instante.isoformat(), "incorporada",
                self.tamano, self.hash, f"sha256/{self.hash[:2]}/{self.hash}", None, "[]", instante.isoformat(), "text/csv"))
        self.kw = dict(asset_id="activo-ficticio", tamano_esperado=self.tamano,
                       sha256_esperado=self.hash, fuente_esperada=self.fuente)

    def ejecutar(self, **kw):
        return piloto.ejecutar(self.raiz, **(self.kw | kw))

    def test_integracion_incompleta_preserva_activo_procedencia_y_originales(self):
        antes = self.db.read_bytes(), self.ruta.read_bytes(), tuple(self.raiz.iterdir())
        r = self.ejecutar()
        self.assertEqual(r["activo"].asset_id, "activo-ficticio")
        self.assertEqual(r["evidencia"].documento, self.doc)
        self.assertEqual(r["antes_raw"], r["despues_raw"])
        self.assertEqual(r["antes_catalogo"], r["despues_catalogo"])
        self.assertEqual(antes, (self.db.read_bytes(), self.ruta.read_bytes(), tuple(self.raiz.iterdir())))
        self.assertEqual(len(r["adaptaciones"]), 6)
        a = r["adaptaciones"][0]
        self.assertEqual(a.originales["observacion"]["procedencia"]["asset_id"], "activo-ficticio")
        self.assertEqual(a.originales["observacion"]["procedencia"]["sha256_declarado"], self.hash)
        self.assertEqual(a.recurso.procedencia, self.doc.procedencia)
        self.assertEqual(dict(a.recurso.temporal.valores_originales)["HORA"], "00000")
        self.assertIsNone(a.recurso.temporal.zona_horaria_declarada)
        self.assertIsNone(a.recurso.temporal.observaciones)
        self.assertIsNone(a.recurso.espacial.coordenadas)
        self.assertEqual(a.recurso.espacial.crs, ())
        self.assertFalse(r["consulta"].completa)

    def test_fuente_senamhi_controlada_no_crea_evidencia_geografica(self):
        # Nombre institucional real, documento y observaciones enteramente ficticios.
        self.fuente = Fuente("SENAMHI", "SENAMHI")
        self.db.unlink()
        self._crear()
        r = self.ejecutar()
        self.assertEqual(r["activo"].declaracion.fuente, self.fuente)
        self.assertEqual(r["espacial"].aptitud.estado, E.PENDIENTE_DE_EVIDENCIA)
        self.assertFalse(r["espacial"].condiciones_documentales_satisfechas)
        self.assertFalse(r["espacial"].operacion_ejecutada)

    def test_temporal_no_depende_de_coordenadas_ni_autoriza_comparacion(self):
        r = self.ejecutar()
        a, b = (r["adaptaciones"][i].recurso for i in (0, 3))
        t = r["temporal"]
        self.assertEqual(t.aptitud.estado, E.PENDIENTE_DE_EVIDENCIA)
        self.assertFalse(t.condiciones_documentales_satisfechas)
        self.assertEqual(evaluar_operacion(replace(a, espacial=None), replace(b, espacial=None), t.operacion).aptitud.faltantes,
                         t.aptitud.faltantes)
        nueva = replace(a, revision_metadatos="revision-futura-ficticia", sustituye_revision=a.revision_metadatos,
                        contradicciones_declaradas=("evidencia_futura_contradictoria_ficticia",))
        self.assertEqual(evaluar_operacion(nueva, b, t.operacion).aptitud.estado, E.INCOMPATIBLE)
        self.assertIs(t.aptitud.recursos[0], a)
        self.assertEqual(evaluar_operacion(a, b, t.operacion), t)

    def test_auxiliares_o_inicializacion_impiden_abrir_sqlite(self):
        for nombre in ("catalogo.sqlite3-wal", "catalogo.sqlite3-shm", "catalogo.sqlite3-journal", ".spica-raw.inicializando"):
            with self.subTest(nombre=nombre):
                p = self.raiz / nombre
                p.write_bytes(b"auxiliar-ficticio")
                try:
                    with patch.object(piloto, "_consultar_activo", side_effect=AssertionError("no abrir")):
                        with self.assertRaisesRegex(piloto.ErrorPiloto, "auxiliar_o_inicializacion"):
                            self.ejecutar()
                finally:
                    p.unlink()

    def test_activo_o_fuente_distintos_se_rechazan_antes_de_csv(self):
        for cambio in (dict(asset_id="otro-activo"), dict(fuente_esperada=Fuente("otra", "otra")),
                       dict(sha256_esperado="0" * 64)):
            with self.subTest(cambio=cambio), patch.object(piloto, "ConsultorLocalCSV", side_effect=AssertionError("no CSV")):
                with self.assertRaises(piloto.ErrorPiloto):
                    self.ejecutar(**cambio)

    def test_contenido_corrupto_no_llega_al_adaptador(self):
        self.ruta.write_bytes(b"X" + self.ruta.read_bytes()[1:])
        with patch.object(piloto, "adaptar_meteorologia", side_effect=AssertionError("no adaptar")):
            with self.assertRaisesRegex(piloto.ErrorPiloto, "integridad_previa"):
                self.ejecutar()

    def test_error_de_acceso_redactado(self):
        with patch.object(Path, "open", side_effect=PermissionError("RUTA-PRIVADA-FICTICIA")):
            with self.assertRaisesRegex(piloto.ErrorPiloto, "^acceso_o_metadatos_requieren_revision$"):
                self.ejecutar()

    def test_cancelacion_antes_del_acceso_y_durante_adaptacion(self):
        evento = Event()
        evento.set()
        with patch.object(piloto, "_firma", side_effect=AssertionError("no acceso")):
            with self.assertRaisesRegex(piloto.ErrorPiloto, "cancelado"):
                self.ejecutar(cancelacion=evento)
        evento.clear()
        adaptar = piloto.adaptar_meteorologia
        def cancelar(*a, **kw):
            r = adaptar(*a, **kw)
            evento.set()
            return r
        antes = self.db.read_bytes(), self.ruta.read_bytes()
        with patch.object(piloto, "adaptar_meteorologia", side_effect=cancelar):
            with self.assertRaisesRegex(piloto.ErrorPiloto, "cancelado"):
                self.ejecutar(cancelacion=evento)
        self.assertEqual(antes, (self.db.read_bytes(), self.ruta.read_bytes()))

    def test_autorizador_sql_y_uri_inmutable_prohiben_escrituras(self):
        antes = self.db.read_bytes()
        with piloto._lectura_sqlite(self.db, False, piloto.PoliticaInspeccionRAW()) as c:
            c.execute("PRAGMA query_only=ON")
            c.execute("PRAGMA trusted_schema=OFF")
            c.set_authorizer(piloto._solo_select)
            for sql in ("DELETE FROM activos", "CREATE TABLE prohibida(x)", "PRAGMA journal_mode=WAL",
                        "ATTACH ':memory:' AS otro"):
                with self.subTest(sql=sql), self.assertRaises(sqlite3.DatabaseError):
                    c.execute(sql)
            self.assertEqual(c.execute("SELECT id FROM activos").fetchone(), ("activo-ficticio",))
        self.assertEqual(antes, self.db.read_bytes())
        self.assertFalse(any(Path(str(self.db) + s).exists() for s in ("-wal", "-shm", "-journal")))

    def test_modificacion_simulada_se_detecta_en_cierre(self):
        adaptar = piloto.adaptar_meteorologia
        cambiado = False
        def modificar(*a, **kw):
            nonlocal cambiado
            r = adaptar(*a, **kw)
            if not cambiado:
                self.ruta.write_bytes(b"X" + self.ruta.read_bytes()[1:])
                cambiado = True
            return r
        with patch.object(piloto, "adaptar_meteorologia", side_effect=modificar):
            with self.assertRaisesRegex(piloto.ErrorPiloto, "integridad_posterior"):
                self.ejecutar()

    def test_seleccion_sin_coincidencias_no_recorrera_todo_el_archivo(self):
        self.db.unlink()
        self._crear(filas=100)
        datos = self.ruta.read_bytes().replace(b"CANDARAVE", b"OTRA-NAME")
        # Reescribe la fixture catalogada como un recurso sintético diferente.
        self.ruta.write_bytes(datos)
        nueva_hash = hashlib.sha256(datos).hexdigest()
        nueva_ruta = self.raiz / "sha256" / nueva_hash[:2] / nueva_hash
        nueva_ruta.parent.mkdir(exist_ok=True)
        self.ruta.rename(nueva_ruta)
        with closing(sqlite3.connect(self.db)) as c, c:
            c.execute("UPDATE activos SET sha256=?,ruta_interna=?", (nueva_hash, f"sha256/{nueva_hash[:2]}/{nueva_hash}"))
        with patch.object(piloto, "adaptar_meteorologia", side_effect=AssertionError("no hubo muestra")):
            with self.assertRaisesRegex(piloto.ErrorPiloto, "muestra_acotada"):
                self.ejecutar(sha256_esperado=nueva_hash)


if __name__ == "__main__":
    unittest.main()
