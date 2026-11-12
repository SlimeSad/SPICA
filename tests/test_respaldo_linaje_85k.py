"""Custodia experimental, exclusivamente fixtures y raíces TEMP propiedad del ensayo."""

from contextlib import closing
from dataclasses import asdict, replace
import errno
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
from threading import Event
import unittest
from unittest.mock import patch

from herramientas import respaldo_linaje_85k as k
from herramientas import conservacion_linaje_85j as p


def muestra(*, cancelada=False, parcial=False, identidad="ejecucion-85k"):
    b = p.h.fixture_csv_85g()
    c = p.h.ContratoEjecucion85G(identidad, "proyecto-ficticio-85g", "entrada-85k",
        "evaluacion-85k", "tarea-85k", len(b), hashlib.sha256(b).hexdigest())
    if parcial:
        c = replace(c, presupuesto=p.h.Presupuesto85G(max_resultados=10))
    evento = Event()
    if cancelada:
        evento.set()
    return p.h.ejecutar_piloto_85g(c, b, cancelacion=evento)


class CorteSimulado(BaseException):
    pass


class Respaldo85KTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cancelada = muestra(cancelada=True)
        cls.completa = muestra()
        cls.parcial = muestra(parcial=True)
        with patch.object(p.h.CatalogoCientifico, "consultar_recurso", side_effect=sqlite3.OperationalError("secreto")):
            cls.fallida = muestra()

    def setUp(self):
        self.g = k.GestorRespaldo85K()

    def almacen(self, informe=None):
        raiz = self.enterContext(p.entorno_piloto_85j())
        a = self.enterContext(p.ConservadorLinaje85J.crear(raiz))
        r = self.cancelada if informe is None else informe
        tr = p.t.construir_traza_85h(r)
        a.conservar(r, tr, referencia_sha256=tr.sha256)
        return a

    def backup(self, a=None):
        a = self.almacen() if a is None else a
        raiz = self.enterContext(k.entorno_respaldo_85k())
        control = self.g.respaldar(a.raiz, raiz, "ejecucion-85k")
        return a, raiz, control

    def destino(self):
        return self.enterContext(p.entorno_piloto_85j())

    def sql(self, ruta, orden):
        with closing(sqlite3.connect(ruta)) as c, c:
            return c.execute(orden).fetchall()

    def manifiesto(self, raiz):
        return json.loads((raiz / "respaldo.json").read_bytes())

    def resellar(self, raiz, control, m):
        b = k.codec.canonico(m)
        (raiz / "respaldo.json").write_bytes(b)
        return replace(control, manifiesto_sha256=k._sha(b))

    def fichero(self, raiz, rol):
        a = next(a for a in self.manifiesto(raiz)["inventario"] if a["rol"] == rol)
        return raiz / a["ruta"]

    def assertRechazo(self, funcion, codigo=None):
        with self.assertRaises(k.ErrorRespaldo85K) as e:
            funcion()
        if codigo is not None:
            self.assertEqual(e.exception.codigo, codigo)
        self.assertNotIn("secreto", str(e.exception))

    def test_copia_y_restauracion_exactas_con_lector_85j_y_cotejo_85h(self):
        a, raiz, ctrl = self.backup(self.almacen(self.completa))
        antes = a.recuperar("ejecucion-85k")
        nuevo = self.destino()
        r = self.g.restaurar(raiz, nuevo, ctrl)
        self.assertIs(r.recuperacion.estado, p.EstadoRecuperacion85J.VERIFICADA)
        self.assertEqual(r.recuperacion.informe, self.completa)
        self.assertEqual(r.recuperacion.traza, antes.traza)
        self.assertEqual(r.recuperacion.referencia_sha256, antes.referencia_sha256)
        self.assertEqual(r.recuperacion.conservacion_id, antes.conservacion_id)
        self.assertEqual(r.recuperacion.informe.activo_id, antes.informe.activo_id)
        self.assertEqual(r.recuperacion.informe.restricciones, antes.informe.restricciones)
        self.assertEqual(self.sql(nuevo / "catalogo.sqlite3", "PRAGMA user_version"), [(85001,)])
        self.assertFalse(r.resumen()["ejecucion_cientifica"])
        self.assertFalse(r.resumen()["autorizacion_operativa"])
        self.assertTrue(r.recuperacion.cotejo.coherente_en_alcance)
        self.assertEqual([len(x) for x in r.recuperacion.informe.resultados], [60, 60])

    def test_historias_cancelada_parcial_y_fallida_no_se_promueven(self):
        for informe in (self.cancelada, self.parcial, self.fallida):
            with self.subTest(estado=informe.estado.value):
                _, raiz, ctrl = self.backup(self.almacen(informe))
                r = self.g.restaurar(raiz, self.destino(), ctrl).recuperacion
                self.assertEqual(r.informe, informe)
                self.assertEqual(r.estado_historico, informe.estado)
                self.assertEqual(r.informe.diagnosticos, informe.diagnosticos)
                self.assertIs(r.estado_conservacion, p.EstadoConservacion85J.CONSERVADA)
                if informe is self.parcial:
                    self.assertEqual(len(r.informe.resultados[0]), 10)
                    self.assertEqual(r.informe.exportaciones, ())

    def test_copias_independientes_del_origen_y_del_respaldo(self):
        a, raiz, ctrl = self.backup()
        artefacto = self.fichero(raiz, "informe")
        original = a._ruta_artefacto(artefacto.name)
        self.assertFalse(os.path.samefile(original, artefacto))
        original.write_bytes(b"corrupcion sintetica posterior")
        nuevo = self.destino()
        self.g.restaurar(raiz, nuevo, ctrl)
        restaurado = nuevo / artefacto.relative_to(raiz)
        self.assertFalse(os.path.samefile(artefacto, restaurado))
        artefacto.write_bytes(b"alteracion posterior del respaldo")
        self.assertEqual(p.ConservadorLinaje85J(nuevo).recuperar("ejecucion-85k").informe, self.cancelada)

    def test_origen_y_respaldo_no_cambian_por_captura_y_restauracion(self):
        a = self.almacen()
        digest = lambda r: {x.relative_to(r).as_posix(): k._sha(x.read_bytes()) for x in r.rglob("*") if x.is_file()}
        previos = digest(a.raiz)
        _, raiz, ctrl = self.backup(a)
        self.assertEqual(digest(a.raiz), previos)
        capturados = digest(raiz)
        self.g.restaurar(raiz, self.destino(), ctrl)
        self.assertEqual(digest(raiz), capturados)
        self.assertFalse((a.raiz / "escritor.lock").exists())

    def test_control_explicito_y_hash_del_manifiesto(self):
        _, raiz, ctrl = self.backup()
        self.assertRechazo(lambda: self.g.verificar_respaldo(raiz, None), "control_explicito_requerido")
        self.assertRechazo(lambda: self.g.verificar_respaldo(raiz, replace(ctrl, manifiesto_sha256="0" * 64)),
                           "hash_manifiesto_incorrecto")
        with self.assertRaises(TypeError):
            bool(ctrl)
        m = self.manifiesto(raiz)
        m["condiciones"] = []
        ctrl = self.resellar(raiz, ctrl, m)
        self.assertRechazo(lambda: self.g.verificar_respaldo(raiz, ctrl), "control_contradictorio")

    def test_nuevos_respaldos_identidad_distinta_misma_generacion(self):
        a, _, c1 = self.backup()
        _, _, c2 = self.backup(a)
        self.assertNotEqual(c1.respaldo_id, c2.respaldo_id)
        self.assertEqual(c1.generacion_sha256, c2.generacion_sha256)
        self.assertNotEqual(c1.manifiesto_sha256, c2.manifiesto_sha256)

    def test_no_reutiliza_destinos_existentes_ni_reinicia_parciales(self):
        a, raiz, ctrl = self.backup()
        self.assertRechazo(lambda: self.g.respaldar(a.raiz, raiz, "ejecucion-85k"), "destino_existente")
        nuevo = self.destino()
        nuevo.mkdir()
        (nuevo / "ajeno").write_bytes(b"preservar")
        self.assertRechazo(lambda: self.g.restaurar(raiz, nuevo, ctrl), "destino_existente")
        self.assertEqual((nuevo / "ajeno").read_bytes(), b"preservar")

    def test_origen_no_conservado_antes_de_commit(self):
        raiz = self.enterContext(p.entorno_piloto_85j())
        a = self.enterContext(p.ConservadorLinaje85J.crear(raiz))
        tr = p.t.construir_traza_85h(self.cancelada)
        def cortar(nombre):
            if nombre == "referencias":
                raise CorteSimulado()
        with patch.object(a, "_punto", side_effect=cortar), self.assertRaises(CorteSimulado):
            a.conservar(self.cancelada, tr, referencia_sha256=tr.sha256)
        dst = self.enterContext(k.entorno_respaldo_85k())
        self.assertRechazo(lambda: self.g.respaldar(raiz, dst, "ejecucion-85k"))
        self.assertFalse(dst.exists())

    def test_marcador_de_escritor_y_residuos_rechazados_sin_borrarlos(self):
        for nombre in ("escritor.lock", "temporales/ajeno.tmp", "ajeno.txt"):
            with self.subTest(nombre=nombre):
                a = self.almacen()
                ruta = a.raiz / nombre
                ruta.write_bytes(b"incierto")
                dst = self.enterContext(k.entorno_respaldo_85k())
                self.assertRechazo(lambda: self.g.respaldar(a.raiz, dst, "ejecucion-85k"))
                self.assertEqual(ruta.read_bytes(), b"incierto")
                self.assertFalse(dst.exists())

    def test_archivo_huerfano_en_origen_no_adoptado(self):
        a = self.almacen()
        ruta = a.raiz / "contenido" / "ff" / ("f" * 64)
        ruta.parent.mkdir(exist_ok=True)
        ruta.write_bytes(b"huerfano")
        dst = self.enterContext(k.entorno_respaldo_85k())
        self.assertRechazo(lambda: self.g.respaldar(a.raiz, dst, "ejecucion-85k"))
        self.assertFalse(dst.exists())

    def test_varias_ejecuciones_fuera_del_perfil(self):
        a = self.almacen()
        r = muestra(cancelada=True, identidad="otra-ejecucion")
        tr = p.t.construir_traza_85h(r)
        a.conservar(r, tr, referencia_sha256=tr.sha256)
        dst = self.enterContext(k.entorno_respaldo_85k())
        self.assertRechazo(lambda: self.g.respaldar(a.raiz, dst, "ejecucion-85k"), "generacion_ambigua")
        self.assertFalse(dst.exists())

    def test_origen_inexistente_no_se_crea(self):
        src = self.destino()
        dst = self.enterContext(k.entorno_respaldo_85k())
        self.assertRechazo(lambda: self.g.respaldar(src, dst, "ejecucion-85k"))
        self.assertFalse(src.exists() or dst.exists())

    def test_archivo_fuente_ausente_o_corrupto(self):
        for ausente in (True, False):
            with self.subTest(ausente=ausente):
                a = self.almacen()
                sha = self.sql(a.raiz / "catalogo.sqlite3", "SELECT sha256 FROM linaje_artefactos WHERE rol='informe'")[0][0]
                f = a._ruta_artefacto(sha)
                f.unlink() if ausente else f.write_bytes(b"corrupto")
                dst = self.enterContext(k.entorno_respaldo_85k())
                self.assertRechazo(lambda: self.g.respaldar(a.raiz, dst, "ejecucion-85k"))
                self.assertFalse(dst.exists())

    def test_sqlite_invalido_version_ajena_y_auxiliares(self):
        for caso in ("corrupto", "version", "-wal", "-shm", "-journal"):
            with self.subTest(caso=caso):
                a = self.almacen()
                db = a.raiz / "catalogo.sqlite3"
                if caso == "corrupto":
                    db.write_bytes(b"no es SQLite")
                elif caso == "version":
                    self.sql(db, "PRAGMA user_version=999")
                else:
                    db.with_name(db.name + caso).write_bytes(b"")
                dst = self.enterContext(k.entorno_respaldo_85k())
                self.assertRechazo(lambda: self.g.respaldar(a.raiz, dst, "ejecucion-85k"))
                self.assertFalse(dst.exists())

    def test_archivos_respaldo_ausentes_alterados_y_hash_incorrecto(self):
        for rol, eliminar in (("informe", True), ("traza", False), ("catalogo", False)):
            with self.subTest(rol=rol):
                _, raiz, ctrl = self.backup()
                f = self.fichero(raiz, rol)
                f.unlink() if eliminar else f.write_bytes(b"alterado")
                self.assertRechazo(lambda: self.g.restaurar(raiz, self.destino(), ctrl))

    def test_version_respaldo_incompatible_aun_resellada(self):
        _, raiz, ctrl = self.backup()
        m = self.manifiesto(raiz)
        m["version"] = "9.0.0"
        ctrl = self.resellar(raiz, ctrl, m)
        self.assertRechazo(lambda: self.g.verificar_respaldo(raiz, ctrl), "version_incompatible")

    def test_generacion_sql_alterada_no_se_oculta_actualizando_hash_fisico(self):
        _, raiz, ctrl = self.backup()
        db = raiz / "catalogo.sqlite3"
        self.sql(db, "UPDATE linaje_eventos SET codigo='otro_codigo' WHERE secuencia=1")
        m = self.manifiesto(raiz)
        for a in m["inventario"]:
            if a["rol"] == "catalogo":
                a["sha256"] = k._sha(db.read_bytes())
        ctrl = self.resellar(raiz, ctrl, m)
        self.assertRechazo(lambda: self.g.verificar_respaldo(raiz, ctrl), "generacion_contradictoria")

    def test_identidad_restricciones_y_errores_contradictorios(self):
        for campo in ("conservacion_id", "restricciones", "diagnosticos"):
            with self.subTest(campo=campo):
                _, raiz, ctrl = self.backup()
                m = self.manifiesto(raiz)
                m["metadatos"][campo] = "0" * 32 if campo == "conservacion_id" else ["falso"]
                ctrl = self.resellar(raiz, ctrl, m)
                self.assertRechazo(lambda: self.g.verificar_respaldo(raiz, ctrl), "metadatos_contradictorios")

    def test_rutas_del_inventario_y_roles_duplicados(self):
        for ruta in ("../escape", "C:/fuera", "piloto.json:ads", "contenido/FF/" + "f" * 64):
            with self.subTest(ruta=ruta):
                _, raiz, ctrl = self.backup()
                m = self.manifiesto(raiz)
                m["inventario"][0]["ruta"] = ruta
                ctrl = self.resellar(raiz, ctrl, m)
                self.assertRechazo(lambda: self.g.verificar_respaldo(raiz, ctrl), "ruta_inventario_insegura")
        _, raiz, ctrl = self.backup()
        m = self.manifiesto(raiz)
        m["inventario"][1] = m["inventario"][0]
        ctrl = self.resellar(raiz, ctrl, m)
        self.assertRechazo(lambda: self.g.verificar_respaldo(raiz, ctrl), "inventario_invalido")

    def test_raices_fuera_de_temp_y_enlaces_rechazados(self):
        a = self.almacen()
        for ruta in (Path.cwd() / "respaldo", a.raiz / ".." / "respaldo", Path("C:/SPICA_DATOS/respaldo")):
            self.assertRechazo(lambda: self.g.respaldar(a.raiz, ruta, "ejecucion-85k"))
        dst = self.enterContext(k.entorno_respaldo_85k())
        for metodo in ("is_symlink", "is_junction"):
            with self.subTest(metodo=metodo), patch.object(Path, metodo, return_value=True):
                self.assertRechazo(lambda: self.g.respaldar(a.raiz, dst, "ejecucion-85k"))
        self.assertFalse(dst.exists())

    def test_enlace_fisico_ajeno_rechazado(self):
        a, raiz, ctrl = self.backup()
        f = self.fichero(raiz, "informe")
        enlace = raiz.parent / "ajeno"
        os.link(f, enlace)
        self.assertRechazo(lambda: self.g.verificar_respaldo(raiz, ctrl), "archivo_inseguro_o_excesivo")

    def test_extras_y_temporales_en_respaldo_bloquean_restauracion(self):
        for nombre in ("trabajo/residuo.tmp", "catalogo.sqlite3-wal", "ajeno", "contenido/ff/" + "f" * 64):
            with self.subTest(nombre=nombre):
                _, raiz, ctrl = self.backup()
                f = raiz / nombre
                f.parent.mkdir(exist_ok=True)
                f.write_bytes(b"incierto")
                dst = self.destino()
                self.assertRechazo(lambda: self.g.restaurar(raiz, dst, ctrl))
                self.assertFalse(dst.exists())
                self.assertEqual(f.read_bytes(), b"incierto")

    def test_los_limites_tipos_y_presupuestos_se_cumplen(self):
        for limite in (dict(bloque=True), dict(segundos=301), dict(max_bytes_archivo=0), dict(max_eventos=1025)):
            self.assertRechazo(lambda: k.LimitesRespaldo85K(**limite), "limite_invalido")
        a = self.almacen()
        for limite in (dict(max_bytes_total=1024), dict(max_bytes_archivo=8), dict(max_eventos=1), dict(max_bytes_sqlite=512)):
            with self.subTest(limite=limite):
                dst = self.enterContext(k.entorno_respaldo_85k())
                g = k.GestorRespaldo85K(limites=k.LimitesRespaldo85K(**limite))
                self.assertRechazo(lambda: g.respaldar(a.raiz, dst, "ejecucion-85k"))
                self.assertFalse(dst.exists())

    def test_espacio_insuficiente_antes_de_reservar_destino(self):
        a = self.almacen()
        dst = self.enterContext(k.entorno_respaldo_85k())
        with patch.object(k.shutil, "disk_usage", return_value=type("Uso", (), {"free": 0})()):
            self.assertRechazo(lambda: self.g.respaldar(a.raiz, dst, "ejecucion-85k"), "espacio_insuficiente")
        self.assertFalse(dst.exists())

    def test_cancelacion_y_plazo_sin_esperas(self):
        a = self.almacen()
        dst = self.enterContext(k.entorno_respaldo_85k())
        self.g.cancelacion.set()
        self.assertRechazo(lambda: self.g.respaldar(a.raiz, dst, "ejecucion-85k"), "operacion_cancelada")
        self.g.cancelacion.clear()
        with patch.object(k.time, "monotonic", side_effect=[0, 301]):
            self.assertRechazo(lambda: self.g.respaldar(a.raiz, dst, "ejecucion-85k"), "plazo_excedido")
        self.assertFalse(dst.exists())

    def test_error_copia_disco_y_permisos_conserva_parcial_y_libera_marcador(self):
        for error in (OSError(errno.ENOSPC, "secreto"), PermissionError("secreto")):
            with self.subTest(tipo=type(error).__name__):
                a = self.almacen()
                dst = self.enterContext(k.entorno_respaldo_85k())
                with patch.object(self.g, "_copiar", side_effect=error):
                    self.assertRechazo(lambda: self.g.respaldar(a.raiz, dst, "ejecucion-85k"), "error_archivo")
                self.assertTrue((dst / "intencion.json").exists())
                self.assertFalse((dst / "respaldo.json").exists())
                self.assertFalse((a.raiz / "escritor.lock").exists())
                self.assertIs(a.recuperar("ejecucion-85k").estado, p.EstadoRecuperacion85J.VERIFICADA)

    def test_escritura_corta_detectada_por_conteo(self):
        a = self.almacen()
        self.g._iniciar()
        f = a.raiz / "piloto.json"
        class Corta:
            def write(self, b):
                return len(b) - 1
        self.assertRechazo(lambda: self.g._archivo(f, 4096, salida=Corta()), "escritura_incompleta")

    def test_interrupciones_antes_de_publicar_respaldo_retienen_evidencia(self):
        for punto in ("intencion_respaldo", "snapshot_sqlite", "archivo_copiado", "antes_publicacion_respaldo"):
            with self.subTest(punto=punto):
                a = self.almacen()
                dst = self.enterContext(k.entorno_respaldo_85k())
                def corte(nombre):
                    if nombre == punto:
                        raise CorteSimulado()
                with patch.object(self.g, "_punto", side_effect=corte), self.assertRaises(CorteSimulado):
                    self.g.respaldar(a.raiz, dst, "ejecucion-85k")
                self.assertTrue((dst / "intencion.json").exists())
                self.assertFalse((dst / "respaldo.json").exists())
                self.assertFalse((a.raiz / "escritor.lock").exists())
                self.assertRechazo(lambda: self.g.respaldar(a.raiz, dst, "ejecucion-85k"), "destino_existente")

    def test_restauracion_interrumpida_no_da_cierre_y_conserva_intencion(self):
        _, raiz, ctrl = self.backup()
        for punto in ("intencion_restauracion", "archivo_copiado", "antes_publicacion_restauracion"):
            with self.subTest(punto=punto):
                dst = self.destino()
                def corte(nombre):
                    if nombre == punto:
                        raise CorteSimulado()
                with patch.object(self.g, "_punto", side_effect=corte), self.assertRaises(CorteSimulado):
                    self.g.restaurar(raiz, dst, ctrl)
                self.assertTrue(list((dst / "temporales").glob("*.intencion")))
                self.assertIsNot(p.ConservadorLinaje85J(dst).recuperar("ejecucion-85k").estado,
                                 p.EstadoRecuperacion85J.VERIFICADA)
                self.assertRechazo(lambda: self.g.restaurar(raiz, dst, ctrl), "destino_existente")

    def test_fallo_tras_enlace_conserva_ambos_nombres_y_no_publica_cierre(self):
        a = self.almacen()
        dst = self.enterContext(k.entorno_respaldo_85k())
        def cortar(nombre):
            if nombre == "enlace_publicado":
                raise CorteSimulado()
        with patch.object(self.g, "_punto", side_effect=cortar), self.assertRaises(CorteSimulado):
            self.g.respaldar(a.raiz, dst, "ejecucion-85k")
        self.assertTrue(list((dst / "trabajo").glob("*.tmp")))
        self.assertEqual((dst / "intencion.json").stat().st_nlink, 2)
        self.assertFalse((dst / "respaldo.json").exists())

    def test_cambio_logico_durante_captura_es_detectado(self):
        a = self.almacen()
        dst = self.enterContext(k.entorno_respaldo_85k())
        def cambiar(nombre):
            if nombre == "snapshot_sqlite":
                self.sql(a.raiz / "catalogo.sqlite3", "UPDATE linaje_eventos SET codigo='cambio' WHERE secuencia=1")
        with patch.object(self.g, "_punto", side_effect=cambiar):
            self.assertRechazo(lambda: self.g.respaldar(a.raiz, dst, "ejecucion-85k"), "generacion_cambio")
        self.assertFalse((dst / "respaldo.json").exists())

    def test_escritor_cooperativo_no_entra_durante_captura(self):
        a = self.almacen()
        dst = self.enterContext(k.entorno_respaldo_85k())
        visitas = []
        def verificar(nombre):
            if nombre == "snapshot_sqlite":
                with self.assertRaises(p.ErrorConservacion85J):
                    with a._escritor():
                        self.fail("dos escritores")
                visitas.append(nombre)
        with patch.object(self.g, "_punto", side_effect=verificar):
            self.g.respaldar(a.raiz, dst, "ejecucion-85k")
        self.assertEqual(visitas, ["snapshot_sqlite"])

    def test_respaldo_por_api_sqlite_no_copia_directa_del_indice(self):
        a = self.almacen()
        dst = self.enterContext(k.entorno_respaldo_85k())
        original = self.g._copiar
        roles = []
        def observar(origen, destino, trabajo, esperado):
            self.assertNotEqual(origen.name, "catalogo.sqlite3")
            roles.append(origen.name)
            return original(origen, destino, trabajo, esperado)
        with patch.object(self.g, "_snapshot", wraps=self.g._snapshot) as snap, patch.object(self.g, "_copiar", side_effect=observar):
            self.g.respaldar(a.raiz, dst, "ejecucion-85k")
        self.assertEqual(snap.call_count, 1)
        self.assertEqual(len(roles), 5)

    def test_cancelacion_durante_copia_deja_parcial_sin_cierre(self):
        a = self.almacen()
        dst = self.enterContext(k.entorno_respaldo_85k())
        def cancelar(nombre):
            if nombre == "snapshot_sqlite":
                self.g.cancelacion.set()
        with patch.object(self.g, "_punto", side_effect=cancelar):
            self.assertRechazo(lambda: self.g.respaldar(a.raiz, dst, "ejecucion-85k"), "operacion_cancelada")
        self.assertFalse((dst / "respaldo.json").exists())
        self.assertFalse((a.raiz / "escritor.lock").exists())

    def test_json_duplicado_y_profundidad_excesiva(self):
        _, raiz, ctrl = self.backup()
        for b in (b'{"version":"0.1.0","version":"0.1.0"}', b"[" * 40 + b"0" + b"]" * 40):
            (raiz / "respaldo.json").write_bytes(b)
            c = replace(ctrl, manifiesto_sha256=k._sha(b))
            self.assertRechazo(lambda: self.g.verificar_respaldo(raiz, c))

    def test_referencia_sql_ausente_impide_capturar(self):
        a = self.almacen()
        self.sql(a.raiz / "catalogo.sqlite3", "DELETE FROM linaje_artefactos WHERE rol='informe'")
        dst = self.enterContext(k.entorno_respaldo_85k())
        self.assertRechazo(lambda: self.g.respaldar(a.raiz, dst, "ejecucion-85k"))
        self.assertFalse(dst.exists())

    def test_catalogo_base_con_datos_ajenos_queda_fuera_del_perfil(self):
        a = self.almacen()
        self.sql(a.raiz / "catalogo.sqlite3", "INSERT INTO fuentes VALUES ('ficticia','ajena','{}',1)")
        dst = self.enterContext(k.entorno_respaldo_85k())
        self.assertRechazo(lambda: self.g.respaldar(a.raiz, dst, "ejecucion-85k"), "catalogo_fuera_del_perfil")
        self.assertFalse(dst.exists())

    def test_fallo_sqlite_backup_deja_intencion_sin_cierre(self):
        a = self.almacen()
        dst = self.enterContext(k.entorno_respaldo_85k())
        with patch.object(self.g, "_snapshot", side_effect=sqlite3.OperationalError("secreto")):
            self.assertRechazo(lambda: self.g.respaldar(a.raiz, dst, "ejecucion-85k"), "error_sqlite")
        self.assertTrue((dst / "intencion.json").exists())
        self.assertFalse((dst / "respaldo.json").exists())
        self.assertFalse((a.raiz / "escritor.lock").exists())

    def test_error_de_escritura_restaurando_preserva_intencion_y_respaldo(self):
        _, raiz, ctrl = self.backup()
        dst = self.destino()
        with patch.object(self.g, "_copiar", side_effect=OSError(errno.ENOSPC, "secreto")):
            self.assertRechazo(lambda: self.g.restaurar(raiz, dst, ctrl), "error_archivo")
        self.assertTrue(list((dst / "temporales").glob("*.intencion")))
        self.assertFalse((dst / "escritor.lock").exists())
        self.assertIsNot(p.ConservadorLinaje85J(dst).recuperar("ejecucion-85k").estado,
                         p.EstadoRecuperacion85J.VERIFICADA)
        self.g.verificar_respaldo(raiz, ctrl)

    def test_fallo_despues_de_publicar_no_reintenta_ni_elimina(self):
        a = self.almacen()
        dst = self.enterContext(k.entorno_respaldo_85k())
        def cortar(nombre):
            if nombre == "respaldo_publicado":
                raise CorteSimulado()
        with patch.object(self.g, "_punto", side_effect=cortar), self.assertRaises(CorteSimulado):
            self.g.respaldar(a.raiz, dst, "ejecucion-85k")
        self.assertTrue((dst / "respaldo.json").exists())
        self.assertFalse((a.raiz / "escritor.lock").exists())
        self.assertRechazo(lambda: self.g.respaldar(a.raiz, dst, "ejecucion-85k"), "destino_existente")

    def test_manifiesto_y_total_excesivos_rechazados_antes_de_restaurar(self):
        _, raiz, ctrl = self.backup()
        for limites in (dict(max_bytes_manifiesto=32), dict(max_bytes_total=1024), dict(max_eventos=1)):
            with self.subTest(limites=limites):
                dst = self.destino()
                g = k.GestorRespaldo85K(limites=k.LimitesRespaldo85K(**limites))
                self.assertRechazo(lambda: g.restaurar(raiz, dst, ctrl))
                self.assertFalse(dst.exists())

    def test_copia_detecta_sustitucion_de_descriptor(self):
        a = self.almacen()
        self.g._iniciar()
        f = a.raiz / "piloto.json"
        real = k.os.fstat
        llamadas = []
        def cambiado(fd):
            s = real(fd)
            llamadas.append(fd)
            if len(llamadas) == 2:
                return type("Stat", (), dict(st_dev=s.st_dev, st_ino=s.st_ino + 1,
                    st_size=s.st_size, st_mtime_ns=s.st_mtime_ns, st_nlink=s.st_nlink))()
            return s
        with patch.object(k.os, "fstat", side_effect=cambiado):
            self.assertRechazo(lambda: self.g._archivo(f, 4096), "archivo_cambio_durante_lectura")

    def test_procesos_independientes_restauran_tras_cerrar_productor(self):
        origen, destino = self.destino(), self.destino()
        respaldo = self.enterContext(k.entorno_respaldo_85k())
        escritor = '''
import json,sys,hashlib,os
from dataclasses import asdict
from herramientas import respaldo_linaje_85k as k
from herramientas import conservacion_linaje_85j as p
b=p.h.fixture_csv_85g()
c=p.h.ContratoEjecucion85G("ejecucion-85k","proyecto-ficticio-85g","entrada-85k","evaluacion-85k","tarea-85k",len(b),hashlib.sha256(b).hexdigest())
r=p.h.ejecutar_piloto_85g(c,b)
tr=p.t.construir_traza_85h(r)
with p.ConservadorLinaje85J.crear(sys.argv[1]) as a:
    v=a.conservar(r,tr,referencia_sha256=tr.sha256)
control=k.GestorRespaldo85K().respaldar(sys.argv[1],sys.argv[2],"ejecucion-85k")
ids=dict(instancia_id=json.loads((a.raiz/"piloto.json").read_bytes())["instancia_id"],activo_id=r.activo_id,
    proyecto_id=r.contrato.proyecto_id,entrada_id=r.contrato.entrada_id,evaluacion_id=r.contrato.evaluacion_id)
print(json.dumps(dict(pid=os.getpid(),control=asdict(control),identidades=ids,recuperacion=v.resumen()),sort_keys=True))
'''
        lector = '''
import json,sys,os
from herramientas import respaldo_linaje_85k as k
from herramientas import conservacion_linaje_85j as p
from unittest.mock import patch
ctrl=k.ControlRespaldo85K(**json.loads(sys.argv[3]))
with patch.object(p.h,"ejecutar_piloto_85g",side_effect=AssertionError("no repetir ejecucion")):
    r=k.GestorRespaldo85K().restaurar(sys.argv[1],sys.argv[2],ctrl)
from pathlib import Path
v=r.recuperacion.informe
ids=dict(instancia_id=json.loads((Path(sys.argv[2])/"piloto.json").read_bytes())["instancia_id"],activo_id=v.activo_id,
    proyecto_id=v.contrato.proyecto_id,entrada_id=v.contrato.entrada_id,evaluacion_id=v.contrato.evaluacion_id)
print(json.dumps(dict(pid=os.getpid(),identidades=ids,**r.resumen()),sort_keys=True))
'''
        def proceso(codigo, *args):
            r = subprocess.run([sys.executable, "-B", "-c", codigo, *map(str, args)], capture_output=True,
                text=True, timeout=180, check=False)
            self.assertEqual(r.returncode, 0, r.stderr)
            return json.loads(r.stdout)
        a = proceso(escritor, origen, respaldo)
        # El padre conserva solo los TEMP; el productor ya terminó.
        b = proceso(lector, respaldo, destino, json.dumps(a["control"]))
        self.assertNotEqual(a["pid"], b["pid"])
        self.assertEqual(a["recuperacion"], b["recuperacion"])
        self.assertEqual(a["identidades"], b["identidades"])
        self.assertEqual(b["recuperacion"]["estado"], "verificada_en_alcance")
        if os.environ.get("SPICA_85K_AUDIT"):
            (Path(os.environ["SPICA_85K_AUDIT"]) / "procesos-85k.json").write_text(
                json.dumps(dict(productor=a, restaurador=b), ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
