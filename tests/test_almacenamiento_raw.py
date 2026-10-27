"""RAW con datos sintéticos, SQLite real y directorios efímeros; sin red."""

from dataclasses import replace
from contextlib import closing, contextmanager
import hashlib
import os
from pathlib import Path
import shutil
import sqlite3
import sys
import subprocess
import tempfile
import traceback
import unittest
from unittest.mock import patch
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from spica.adquisicion.almacenamiento import (
    AlmacenRAW, DeclaracionRAW, ErrorAlmacenamientoRAW, EstadoIncorporacion,
)
from spica.adquisicion.nucleo import Fuente, ResultadoRecurso, RecursoDescubierto


class AlmacenRAWTests(unittest.TestCase):
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
        self.archivo = self.entrada / "datos.bin"
        self.archivo.write_bytes(b"datos sinteticos\x00\xff")
        self.declaracion = DeclaracionRAW(" Proyecto-01 ", "objeto/01", Fuente("Prueba", " Fuente-01 "),
            " Recurso-001 ", "https://prueba.invalid/recurso", {"variable": " V/01 ", "estaciones": "001,002"})
        self.almacen = AlmacenRAW(self.raw, (self.entrada,), max_bytes=100,
            tamano_bloque=3, claves_parametros_publicos=("variable", "estaciones"))
        self.addCleanup(self.almacen.close)

    def incorporar(self):
        return self.almacen.incorporar(self.archivo, self.declaracion)

    def contenido(self):
        return tuple(p for p in (self.raw / "sha256").glob("*/*") if p.is_file())

    def test_incorporacion_hash_real_contenido_y_original_intacto(self):
        original = self.archivo.read_bytes()
        activo = self.incorporar()
        self.assertEqual(activo.estado, EstadoIncorporacion.INCORPORADA)
        self.assertEqual(activo.sha256, hashlib.sha256(original).hexdigest())
        ruta = self.almacen.recuperar(activo.activo_id)
        self.assertEqual(ruta.read_bytes(), original)
        self.assertEqual(self.archivo.read_bytes(), original)
        self.assertEqual(activo.tamano, len(original))
        self.assertEqual(activo.ruta_interna, f"sha256/{activo.sha256[:2]}/{activo.sha256}")
        self.assertEqual(activo.fecha_utc.utcoffset().total_seconds(), 0)
        self.assertIsNotNone(activo.comprobacion_utc)
        self.assertEqual(list((self.raw / "temporales").iterdir()), [])

    def test_archivo_vacio_legitimo(self):
        self.archivo.write_bytes(b"")
        activo = self.incorporar()
        self.assertEqual(activo.sha256, hashlib.sha256(b"").hexdigest())
        self.assertEqual(activo.tamano, 0)
        self.assertTrue(self.almacen.verificar(activo.activo_id).coincide)

    def test_dos_adquisiciones_duplicadas_conservan_identidad(self):
        primero = self.incorporar()
        segundo = self.incorporar()
        self.assertNotEqual(primero.activo_id, segundo.activo_id)
        self.assertEqual(primero.sha256, segundo.sha256)
        self.assertEqual(len(self.contenido()), 1)
        self.assertEqual(len(self.almacen._catalogo.listar()), 2)

    def test_objetos_y_proyectos_independientes_de_huella(self):
        primero = self.incorporar()
        segundo = self.almacen.incorporar(self.archivo, replace(self.declaracion,
            proyecto_id="otro-proyecto", objeto_id="otro-objeto"))
        self.assertEqual(primero.sha256, segundo.sha256)
        self.assertNotEqual(primero.declaracion.objeto_id, segundo.declaracion.objeto_id)
        self.assertEqual(len(self.contenido()), 1)

    def test_objeto_no_puede_cambiar_de_proyecto(self):
        self.incorporar()
        with self.assertRaises(ErrorAlmacenamientoRAW) as contexto:
            self.almacen.incorporar(self.archivo, replace(self.declaracion, proyecto_id="otro"))
        self.assertEqual(contexto.exception.codigo, "objeto_de_otro_proyecto")
        self.assertEqual(len(self.almacen._catalogo.listar()), 1)

    def test_identificadores_y_procedencia_publica_sin_normalizar(self):
        activo = self.incorporar()
        self.assertEqual(activo.declaracion, self.declaracion)
        self.assertEqual(activo.declaracion.parametros_publicos["variable"], " V/01 ")
        self.assertIsNone(activo.declaracion.formato_declarado)
        self.assertIsNone(activo.declaracion.tipo_medio_declarado)

    def test_procedencia_y_parametros_sensibles_no_entran_en_sqlite(self):
        declaracion = replace(self.declaracion,
            procedencia="https://usuario:secreto@prueba.invalid/recurso?token=secreto#clave",
            parametros_publicos={"token": "secreto", "password": "secreto", "variable": " V/01 ",
                                 "estaciones": "token=secreto", "desconocido": "secreto"})
        activo = self.almacen.incorporar(self.archivo, declaracion)
        self.assertEqual(activo.declaracion.procedencia, "https://prueba.invalid/recurso")
        self.assertEqual(dict(activo.declaracion.parametros_publicos), {"variable": " V/01 "})
        self.assertIn("parametro_omitido", activo.advertencias)
        self.assertNotIn(b"secreto", (self.raw / "catalogo.sqlite3").read_bytes())

    def test_parametros_no_se_guardan_sin_lista_publica_explicita(self):
        self.almacen.claves = frozenset()
        activo = self.incorporar()
        self.assertEqual(dict(activo.declaracion.parametros_publicos), {})

    def test_datos_declarados_no_se_promueven_a_comprobados(self):
        activo = self.almacen.incorporar(self.archivo, replace(self.declaracion,
            formato_declarado="formato-ficticio", tipo_medio_declarado="application/x-prueba"))
        self.assertEqual(activo.declaracion.formato_declarado, "formato-ficticio")
        self.assertEqual(activo.estado, EstadoIncorporacion.INCORPORADA)
        recurso = RecursoDescubierto(self.declaracion.fuente, self.declaracion.recurso_id,
                                     self.declaracion.procedencia)
        self.assertEqual(ResultadoRecurso(recurso).estado.value, "descubierto")

    def test_cambio_posterior_en_copia_raw_detectado(self):
        activo = self.incorporar()
        ruta = self.almacen.recuperar(activo.activo_id)
        datos = ruta.read_bytes()
        ruta.write_bytes(b"X" + datos[1:])  # Igual longitud, distinto SHA-256.
        self.assertFalse(self.almacen.verificar(activo.activo_id).coincide)
        self.assertEqual(self.almacen.metadatos(activo.activo_id).estado, EstadoIncorporacion.INCONSISTENTE)
        with self.assertRaises(ErrorAlmacenamientoRAW):
            self.almacen.recuperar(activo.activo_id)

    def test_cambio_del_original_no_modifica_la_copia_raw(self):
        activo = self.incorporar()
        self.archivo.write_bytes(b"otro contenido")
        self.assertTrue(self.almacen.verificar(activo.activo_id).coincide)
        self.assertNotEqual(self.almacen.recuperar(activo.activo_id).read_bytes(), self.archivo.read_bytes())

    def test_archivo_raw_faltante_no_se_considera_disponible(self):
        activo = self.incorporar()
        self.almacen.recuperar(activo.activo_id).unlink()
        with self.assertRaises(ErrorAlmacenamientoRAW):
            self.almacen.recuperar(activo.activo_id)
        self.assertIn(activo.activo_id, self.almacen.diagnosticar().inconsistentes)

    def test_duplicado_corrupto_no_se_sobrescribe(self):
        activo = self.incorporar()
        ruta = self.almacen.recuperar(activo.activo_id)
        ruta.write_bytes(b"alterado")
        with self.assertRaises(ErrorAlmacenamientoRAW):
            self.incorporar()
        self.assertEqual(ruta.read_bytes(), b"alterado")

    def test_ruta_inexistente_registra_fallo(self):
        with self.assertRaises(ErrorAlmacenamientoRAW) as contexto:
            self.almacen.incorporar(self.entrada / "inexistente", self.declaracion)
        activo = self.almacen.metadatos(contexto.exception.activo_id)
        self.assertEqual(activo.estado, EstadoIncorporacion.FALLIDA)
        self.assertEqual(self.contenido(), ())

    def test_ruta_fuera_de_raiz_y_traversal(self):
        fuera = self.base / "fuera.bin"
        fuera.write_bytes(b"fuera")
        for ruta in (fuera, self.entrada / ".." / "fuera.bin", self.entrada):
            with self.subTest(ruta=ruta), self.assertRaises(ErrorAlmacenamientoRAW):
                self.almacen.incorporar(ruta, self.declaracion)
        self.assertEqual(fuera.read_bytes(), b"fuera")

    def test_enlace_simbolico_de_entrada_rechazado(self):
        # Simula el resultado del sistema de archivos sin exigir privilegios Windows.
        real = Path.is_symlink
        def enlace(ruta):
            return ruta == self.archivo or real(ruta)
        with patch.object(Path, "is_symlink", enlace):
            with self.assertRaises(ErrorAlmacenamientoRAW) as contexto:
                self.incorporar()
        self.assertEqual(contexto.exception.codigo, "enlace_no_autorizado")

    def test_junction_rechazada(self):
        with patch.object(Path, "is_junction", return_value=True):
            with self.assertRaises(ErrorAlmacenamientoRAW):
                self.incorporar()

    def test_error_de_lectura_limpia_temporal(self):
        real = Path.open
        def abrir(ruta, *args, **kwargs):
            if ruta == self.archivo:
                raise PermissionError("lectura")
            return real(ruta, *args, **kwargs)
        with patch.object(Path, "open", abrir):
            with self.assertRaises(ErrorAlmacenamientoRAW) as contexto:
                self.incorporar()
        self.assertEqual(self.almacen.metadatos(contexto.exception.activo_id).estado, EstadoIncorporacion.FALLIDA)
        self.assertEqual(list((self.raw / "temporales").iterdir()), [])

    def test_error_de_escritura_limpia_temporal(self):
        with patch("spica.adquisicion.almacenamiento.raw.os.fsync", side_effect=OSError("disco")):
            with self.assertRaises(ErrorAlmacenamientoRAW):
                self.incorporar()
        self.assertEqual(list((self.raw / "temporales").iterdir()), [])
        self.assertEqual(self.contenido(), ())

    def test_escritura_corta_rechazada(self):
        crear = tempfile.NamedTemporaryFile
        def corto(**opciones):
            archivo = crear(**opciones)
            archivo.write = lambda datos: 0
            return archivo
        with patch("spica.adquisicion.almacenamiento.raw.tempfile.NamedTemporaryFile", side_effect=corto):
            with self.assertRaises(ErrorAlmacenamientoRAW) as contexto:
                self.incorporar()
        self.assertEqual(contexto.exception.codigo, "escritura_incompleta")

    def test_error_sqlite_en_preparacion_no_publica(self):
        with patch.object(self.almacen._catalogo, "preparar", side_effect=sqlite3.OperationalError("fallo")):
            with self.assertRaises(ErrorAlmacenamientoRAW) as contexto:
                self.incorporar()
        self.assertEqual(contexto.exception.codigo, "error_sqlite")
        self.assertEqual(self.contenido(), ())
        self.assertEqual(self.almacen._catalogo.listar(), ())

    def test_error_sqlite_despues_de_publicar_detecta_operacion_incompleta(self):
        real = self.almacen._catalogo.transicion
        def fallar(activo_id, estado, **opciones):
            if estado in (EstadoIncorporacion.INCORPORADA, EstadoIncorporacion.FALLIDA):
                raise sqlite3.OperationalError("fallo sqlite")
            return real(activo_id, estado, **opciones)
        with patch.object(self.almacen._catalogo, "transicion", side_effect=fallar):
            with self.assertRaises(ErrorAlmacenamientoRAW) as contexto:
                self.incorporar()
        activo = self.almacen.metadatos(contexto.exception.activo_id)
        self.assertEqual(activo.estado, EstadoIncorporacion.VERIFICADA)
        diagnostico = self.almacen.diagnosticar()
        self.assertIn(activo.activo_id, diagnostico.incompletas)
        self.assertEqual(len(diagnostico.sin_referencia), 1)
        with self.assertRaises(ErrorAlmacenamientoRAW):
            self.almacen.recuperar(activo.activo_id)

    def test_interrupcion_no_confirma_y_limpia(self):
        with patch.object(self.almacen, "_copiar", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.incorporar()
        self.assertEqual(list((self.raw / "temporales").iterdir()), [])
        self.assertEqual(self.almacen._catalogo.listar()[0].estado, EstadoIncorporacion.FALLIDA)

    def test_publicacion_no_soportada_no_tiene_fallback(self):
        with patch("spica.adquisicion.almacenamiento.raw.os.link", side_effect=OSError("no soportado")):
            with self.assertRaises(ErrorAlmacenamientoRAW):
                self.incorporar()
        self.assertEqual(self.contenido(), ())

    def test_catalogo_persistente_se_reabre(self):
        activo = self.incorporar()
        with AlmacenRAW(self.raw, (self.entrada,), max_bytes=100) as otro:
            self.assertEqual(otro.metadatos(activo.activo_id), activo)
            self.assertEqual(otro.recuperar(activo.activo_id).read_bytes(), self.archivo.read_bytes())

    def test_eventos_persistentes_de_cada_fase(self):
        activo = self.incorporar()
        estados = tuple(f[0] for f in self.almacen._catalogo.conexion.execute(
            "SELECT estado FROM eventos WHERE activo_id=? ORDER BY secuencia", (activo.activo_id,)))
        self.assertEqual(estados, ("preparada", "verificada_localmente", "incorporada"))

    def test_ruta_catalogo_manipulada_no_escapa(self):
        activo = self.incorporar()
        with self.almacen._catalogo.conexion:
            self.almacen._catalogo.conexion.execute("UPDATE activos SET ruta_interna='../fuera' WHERE id=?", (activo.activo_id,))
        resultado = self.almacen.verificar(activo.activo_id)
        self.assertFalse(resultado.coincide)
        self.assertEqual(resultado.error, "ruta_catalogo_inconsistente")

    def test_residuos_y_archivos_sin_referencia_se_detectan_sin_eliminar(self):
        temporal = self.raw / "temporales" / "interrumpida.tmp"
        temporal.write_bytes(b"fragmento")
        carpeta = self.raw / "sha256" / "aa"
        carpeta.mkdir()
        huerfano = carpeta / ("a" * 64)
        huerfano.write_bytes(b"sin catalogo")
        diagnostico = self.almacen.diagnosticar()
        self.assertIn("temporales/interrumpida.tmp", diagnostico.temporales)
        self.assertEqual(len(diagnostico.sin_referencia), 1)
        self.assertTrue(temporal.exists())
        self.assertTrue(huerfano.exists())

    def test_limite_de_tamano(self):
        self.archivo.write_bytes(b"x" * 101)
        with self.assertRaises(ErrorAlmacenamientoRAW) as contexto:
            self.incorporar()
        self.assertEqual(contexto.exception.codigo, "limite_excedido")
        self.assertEqual(self.contenido(), ())

    def test_modificacion_durante_lectura_detectada(self):
        real = os.fstat
        llamadas = 0
        def cambiar(fd):
            nonlocal llamadas
            llamadas += 1
            if llamadas == 2:
                self.archivo.write_bytes(b"archivo cambiado")
            return real(fd)
        with patch("spica.adquisicion.almacenamiento.raw.os.fstat", side_effect=cambiar):
            with self.assertRaises(ErrorAlmacenamientoRAW) as contexto:
                self.incorporar()
        self.assertEqual(contexto.exception.codigo, "entrada_modificada")

    def test_activo_inexistente(self):
        with self.assertRaises(ErrorAlmacenamientoRAW) as contexto:
            self.almacen.recuperar("desconocido")
        self.assertEqual(contexto.exception.codigo, "activo_no_encontrado")

    def test_identificador_original_url_publica_se_conserva(self):
        declaracion = replace(self.declaracion, recurso_id="https://prueba.invalid/ID-Original")
        activo = self.almacen.incorporar(self.archivo, declaracion)
        self.assertEqual(activo.declaracion.recurso_id, declaracion.recurso_id)

    def test_identificador_con_secretos_se_rechaza_sin_persistir(self):
        for identificador in ("token=secreto", "https://u:secreto@prueba.invalid/r", "https://prueba.invalid/r?key=secreto"):
            with self.subTest(identificador=identificador), self.assertRaises(ErrorAlmacenamientoRAW):
                self.almacen.incorporar(self.archivo, replace(self.declaracion, recurso_id=identificador))
        self.assertEqual(self.almacen._catalogo.listar(), ())
        self.assertNotIn(b"secreto", (self.raw / "catalogo.sqlite3").read_bytes())

    def test_no_se_repara_automaticamente_un_activo_inconsistente(self):
        activo = self.incorporar()
        ruta = self.almacen.recuperar(activo.activo_id)
        datos = ruta.read_bytes()
        ruta.write_bytes(b"alterado")
        self.almacen.verificar(activo.activo_id)
        ruta.write_bytes(datos)
        self.assertTrue(self.almacen.verificar(activo.activo_id).coincide)
        self.assertEqual(self.almacen.metadatos(activo.activo_id).estado, EstadoIncorporacion.INCONSISTENTE)
        with self.assertRaises(ErrorAlmacenamientoRAW):
            self.almacen.recuperar(activo.activo_id)

    def test_sqlite_revierte_transicion_y_evento_juntos(self):
        real = self.almacen._catalogo._evento
        def fallar(activo_id, estado, codigo):
            if estado is EstadoIncorporacion.INCORPORADA:
                raise sqlite3.OperationalError("evento no persistido")
            return real(activo_id, estado, codigo)
        with patch.object(self.almacen._catalogo, "_evento", side_effect=fallar):
            with self.assertRaises(ErrorAlmacenamientoRAW) as contexto:
                self.incorporar()
        activo = self.almacen.metadatos(contexto.exception.activo_id)
        self.assertEqual(activo.estado, EstadoIncorporacion.FALLIDA)
        eventos = tuple(f[0] for f in self.almacen._catalogo.conexion.execute(
            "SELECT estado FROM eventos WHERE activo_id=?", (activo.activo_id,)))
        self.assertNotIn("incorporada", eventos)

    def test_diagnostico_tras_reapertura_detecta_fallo_incompleto(self):
        real = self.almacen._catalogo.transicion
        def fallar(activo_id, estado, **opciones):
            if estado is EstadoIncorporacion.VERIFICADA:
                raise KeyboardInterrupt()
            return real(activo_id, estado, **opciones)
        with patch.object(self.almacen._catalogo, "transicion", side_effect=fallar):
            with self.assertRaises(KeyboardInterrupt):
                self.incorporar()
        with AlmacenRAW(self.raw, (self.entrada,), max_bytes=100) as otro:
            self.assertEqual(len(otro.diagnosticar().incompletas), 1)
            self.assertEqual(otro.diagnosticar().temporales, ())

    def test_fallo_de_limpieza_deja_residuo_diagnosticable(self):
        with patch.object(Path, "unlink", side_effect=PermissionError("ocupado")):
            with patch.object(self.almacen, "_copiar", side_effect=OSError("error lectura")):
                with self.assertRaises(ErrorAlmacenamientoRAW) as contexto:
                    self.incorporar()
        self.assertEqual(contexto.exception.codigo, "temporal_no_eliminado")
        diagnostico = self.almacen.diagnosticar()
        self.assertEqual(len(diagnostico.temporales), 1)
        self.assertIn(contexto.exception.activo_id, diagnostico.incompletas)

    def test_configuracion_invalida_y_catalogo_ajeno(self):
        for opciones in ({"max_bytes": 0}, {"max_bytes": True}, {"tamano_bloque": 1_048_577}):
            with self.subTest(opciones=opciones), self.assertRaises(ValueError):
                AlmacenRAW(self.raw, (self.entrada,), **opciones)
        ajeno = self.base / "ajeno"
        ajeno.mkdir()
        with closing(sqlite3.connect(ajeno / "catalogo.sqlite3")) as conexion:
            conexion.execute("CREATE TABLE ajena (id TEXT)")
        with self.assertRaises(ErrorAlmacenamientoRAW) as contexto:
            AlmacenRAW(ajeno, (self.entrada,))
        self.assertEqual(contexto.exception.codigo, "catalogo_ajeno")

    def test_error_en_write_real_se_traduce_sin_exponer_mensaje(self):
        crear = tempfile.NamedTemporaryFile
        def fallido(**opciones):
            archivo = crear(**opciones)
            def escribir(datos):
                raise OSError("token=secreto")
            archivo.write = escribir
            return archivo
        with patch("spica.adquisicion.almacenamiento.raw.tempfile.NamedTemporaryFile", side_effect=fallido):
            with self.assertRaises(ErrorAlmacenamientoRAW) as contexto:
                self.incorporar()
        self.assertEqual(str(contexto.exception), "error_archivo")
        self.assertNotIn(b"secreto", (self.raw / "catalogo.sqlite3").read_bytes())
        self.assertEqual(list((self.raw / "temporales").iterdir()), [])

    def test_referencias_de_red_ambiguas_no_persisten_secretos(self):
        secreto = "CLAVE_SINTETICA_AUDITORIA"
        referencias = (f"//usuario:{secreto}@prueba.invalid/recurso",
                       f"  //usuario:{secreto}@prueba.invalid/recurso",
                       f"\\\\usuario:{secreto}@prueba.invalid\\recurso",
                       f"https:usuario:{secreto}@prueba.invalid/recurso",
                       f"usuario:{secreto}@prueba.invalid/recurso",
                       f"%2F%2Fusuario:{secreto}@prueba.invalid/recurso",
                       f"https://prueba.invalid:{secreto}/recurso",
                       f"https://[invalido-{secreto}/recurso",
                       f"https://prueba.invalid/\n{secreto}")
        for referencia in referencias:
            with self.subTest(referencia=referencia), self.assertNoLogs():
                with self.assertRaises(ErrorAlmacenamientoRAW) as contexto:
                    self.almacen.incorporar(self.archivo, replace(self.declaracion, procedencia=referencia))
                texto_error = "".join(traceback.format_exception(contexto.exception))
                self.assertNotIn(secreto, texto_error)
        self.assertEqual(self.almacen._catalogo.listar(), ())
        self.assertEqual(self.almacen._catalogo.conexion.execute("SELECT COUNT(*) FROM eventos").fetchone()[0], 0)
        self.assertNotIn(secreto.encode(), (self.raw / "catalogo.sqlite3").read_bytes())

    def test_identificadores_con_autoridad_sin_esquema_se_rechazan(self):
        for campo in ("recurso_id", "proyecto_id", "objeto_id"):
            with self.subTest(campo=campo), self.assertRaises(ErrorAlmacenamientoRAW):
                self.almacen.incorporar(self.archivo, replace(self.declaracion,
                    **{campo: "//usuario:CLAVE_SINTETICA@prueba.invalid/r"}))
        self.assertEqual(self.almacen._catalogo.listar(), ())

    def test_http_https_publicos_se_sanean_sin_secretos_en_eventos(self):
        secreto = "CLAVE_SINTETICA_AUDITORIA"
        for esquema in ("http", "https"):
            with self.subTest(esquema=esquema), self.assertNoLogs():
                referencia = f"{esquema}://usuario:{secreto}@prueba.invalid/r?token={secreto}#password={secreto}"
                activo = self.almacen.incorporar(self.archivo, replace(self.declaracion, procedencia=referencia))
                self.assertEqual(activo.declaracion.procedencia, f"{esquema}://prueba.invalid/r")
                self.assertTrue(activo.advertencias)
                self.assertNotIn(secreto, repr(activo))
        eventos = self.almacen._catalogo.conexion.execute("SELECT * FROM eventos").fetchall()
        self.assertNotIn(secreto, repr([tuple(e) for e in eventos]))
        self.assertNotIn(secreto.encode(), (self.raw / "catalogo.sqlite3").read_bytes())

    def test_identificadores_cientificos_opacos_se_conservan_exactamente(self):
        for identificador in (" ESTACION/001 ", "doi:10.0000/Serie-A", "urn:spica:recurso:ABC", "Variable#01"):
            with self.subTest(identificador=identificador):
                activo = self.almacen.incorporar(self.archivo, replace(self.declaracion, recurso_id=identificador))
                self.assertEqual(activo.declaracion.recurso_id, identificador)
        for referencia in (" DOI:10.0000/Serie-A ", "urn:spica:recurso:ABC"):
            activo = self.almacen.incorporar(self.archivo, replace(self.declaracion, procedencia=referencia))
            self.assertEqual(activo.declaracion.procedencia, referencia)

    def test_parametro_publico_no_permite_credenciales_disfrazadas(self):
        for valor in ("//usuario:CLAVE_SINTETICA@prueba.invalid/r", "https:usuario:CLAVE_SINTETICA@prueba.invalid",
                      "%252F%252Fusuario:CLAVE_SINTETICA@prueba.invalid/r", "token%3DCLAVE_SINTETICA"):
            activo = self.almacen.incorporar(self.archivo, replace(self.declaracion,
                parametros_publicos={"variable": valor}))
            self.assertEqual(dict(activo.declaracion.parametros_publicos), {})
        self.assertNotIn(b"CLAVE_SINTETICA", (self.raw / "catalogo.sqlite3").read_bytes())

    def test_reapertura_con_limite_menor_verifica_y_recupera_sin_corrupcion(self):
        activo = self.incorporar()
        self.almacen.close()
        with AlmacenRAW(self.raw, (self.entrada,), max_bytes=1, tamano_bloque=2) as otro:
            self.assertTrue(otro.verificar(activo.activo_id).coincide)
            self.assertEqual(otro.recuperar(activo.activo_id).read_bytes(), self.archivo.read_bytes())
            self.assertEqual(otro.metadatos(activo.activo_id).estado, EstadoIncorporacion.INCORPORADA)
            self.assertEqual(otro.diagnosticar().inconsistentes, ())
            with self.assertRaises(ErrorAlmacenamientoRAW) as contexto:
                otro.incorporar(self.archivo, self.declaracion)
            self.assertEqual(contexto.exception.codigo, "limite_excedido")
            self.assertEqual(otro.metadatos(activo.activo_id).estado, EstadoIncorporacion.INCORPORADA)

    def test_corrupcion_real_detectada_con_limite_menor(self):
        activo = self.incorporar()
        ruta = self.almacen.recuperar(activo.activo_id)
        datos = ruta.read_bytes()
        ruta.write_bytes(b"X" + datos[1:])
        self.almacen.close()
        with AlmacenRAW(self.raw, (self.entrada,), max_bytes=1) as otro:
            self.assertFalse(otro.verificar(activo.activo_id).coincide)
            self.assertEqual(otro.metadatos(activo.activo_id).estado, EstadoIncorporacion.INCONSISTENTE)

    def test_fallo_de_acceso_o_recursos_no_declara_corrupcion(self):
        activo = self.incorporar()
        previo = self.almacen.metadatos(activo.activo_id)
        for error in (PermissionError("denegado"), OSError("fallo temporal"), MemoryError("sin memoria")):
            with self.subTest(error=type(error)), patch.object(self.almacen, "_comprobar_archivo", side_effect=error):
                with self.assertRaises(ErrorAlmacenamientoRAW) as contexto:
                    self.almacen.verificar(activo.activo_id)
                self.assertEqual(contexto.exception.codigo, "verificacion_no_disponible")
                self.assertEqual(self.almacen.metadatos(activo.activo_id), previo)
                with self.assertRaises(ErrorAlmacenamientoRAW):
                    self.almacen.recuperar(activo.activo_id)

    def test_error_de_politica_no_declara_corrupcion(self):
        activo = self.incorporar()
        with patch.object(self.almacen, "_comprobar_archivo", side_effect=ErrorAlmacenamientoRAW("limite_excedido")):
            with self.assertRaises(ErrorAlmacenamientoRAW) as contexto:
                self.almacen.verificar(activo.activo_id)
        self.assertEqual(contexto.exception.codigo, "verificacion_no_disponible")
        self.assertEqual(self.almacen.metadatos(activo.activo_id).estado, EstadoIncorporacion.INCORPORADA)

    def test_verificacion_lee_por_bloques_no_por_tamano_total(self):
        activo = self.incorporar()
        abrir_real = Path.open
        lecturas = []
        class LecturaAcotada:
            def __init__(self, archivo):
                self.archivo = archivo
            def fileno(self):
                return self.archivo.fileno()
            def read(self, cantidad):
                lecturas.append(cantidad)
                return self.archivo.read(cantidad)
        @contextmanager
        def abrir(ruta, *args, **opciones):
            with abrir_real(ruta, *args, **opciones) as archivo:
                yield LecturaAcotada(archivo)
        with patch.object(Path, "open", abrir):
            self.almacen.max_bytes = 1
            self.assertTrue(self.almacen.verificar(activo.activo_id).coincide)
        self.assertGreater(len(lecturas), 1)
        self.assertTrue(all(0 < n <= self.almacen.bloque for n in lecturas))

    def test_git_excluye_solo_raw_operativo_convencional(self):
        proyecto = Path(__file__).resolve().parents[1]
        rutas = ("datos/raw/catalogo.sqlite3", "datos/raw/sha256/aa/archivo",
                 "datos/raw/temporales/operacion.tmp", "datos/raw/catalogo.sqlite3-journal")
        resultado = subprocess.run(["git", "check-ignore", "--no-index", "--", *rutas],
                                   cwd=proyecto, capture_output=True, text=True, check=False)
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        self.assertEqual(set(resultado.stdout.splitlines()), set(rutas))
        control = subprocess.run(["git", "check-ignore", "--no-index", "--",
            "src/spica/adquisicion/almacenamiento/raw.py", "tests/test_almacenamiento_raw.py",
            "docs/almacenamiento_raw.md", "datos/documentacion.txt"],
            cwd=proyecto, capture_output=True, text=True, check=False)
        self.assertEqual(control.returncode, 1, control.stderr)
        self.assertEqual(control.stdout, "")


if __name__ == "__main__":
    unittest.main()
