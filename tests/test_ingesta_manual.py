"""PASO 79: archivos inventados, directorios privados efímeros y SQLite aislado."""

from dataclasses import replace
from datetime import date, datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import sqlite3
import sys
import tempfile
from threading import Event
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from spica.adquisicion.almacenamiento import (
    AlmacenRAW, DeclaracionRAW, ErrorAlmacenamientoRAW, EstadoIncorporacion,
)
from spica.adquisicion.catalogo import MecanismoAdquisicion
from spica.adquisicion.catalogo.evidencias import desempaquetar
from spica.adquisicion.manual import (
    AutenticidadManual, DocumentoManual, ErrorIngestaManual, EstadoIngestaManual,
    FundamentoUsoManual, IngestorManual, IntegridadManual, PoliticaIngestaManual,
    ProcedenciaManual, ReciboIngestaManual, SolicitudIngestaManual,
)
from spica.adquisicion.nucleo import Fuente


class ArchivoInstrumentado:
    """Instrumenta una lectura/escritura sin reemplazar el descriptor físico."""

    def __init__(self, archivo, *, leer=None, escribir=None):
        self.archivo, self.leer, self.escribir = archivo, leer, escribir

    def __enter__(self):
        self.archivo.__enter__()
        return self

    def __exit__(self, *args):
        return self.archivo.__exit__(*args)

    def __getattr__(self, nombre):
        return getattr(self.archivo, nombre)

    def read(self, n):
        return self.leer(self.archivo, n) if self.leer else self.archivo.read(n)

    def write(self, bloque):
        return self.escribir(self.archivo, bloque) if self.escribir else self.archivo.write(bloque)


class IngestaManualTests(unittest.TestCase):
    def setUp(self):
        self.temporales = Path(tempfile.gettempdir()).resolve()
        self.base = self.temporales / ("spica-manual-prueba-" + uuid4().hex)
        # Sigue la política de fixtures Windows del repositorio; no modifica ACL operativas.
        self.base.mkdir(mode=0o755)
        self.addCleanup(self.limpiar)
        self.raw, self.staging, self.origen = (self.base / p for p in ("raw", "staging", "origen"))
        for p in (self.raw, self.staging, self.origen):
            p.mkdir()
        self.almacen = AlmacenRAW(self.raw, (self.staging,), max_bytes=2 * 1024**2)
        self.addCleanup(lambda: self.almacen.close())
        self.politica = PoliticaIngestaManual(max_bytes=2 * 1024**2, tamano_bloque=19, margen_libre=4096)
        self.ingestor = self.crear_ingestor()
        self.archivo = self.origen / "institucion_sintetica.csv"
        self.contenido = b"bytes inventados; no observaciones cientificas\n" * 5
        self.archivo.write_bytes(self.contenido)
        self.doc = ProcedenciaManual(fundamento=FundamentoUsoManual(
            DocumentoManual("urn:fixture:fundamento", version="sintetica-1"), True))
        self.solicitud = SolicitudIngestaManual(" Proyecto/01 ", " Objeto/01 ", " Recurso/01 ",
                                               self.archivo, self.doc)

    def limpiar(self):
        assert self.base.parent == self.temporales
        assert self.base.resolve().is_relative_to(self.temporales)
        assert self.base.name.startswith("spica-manual-prueba-")
        shutil.rmtree(self.base)

    def crear_ingestor(self, politica=None):
        return IngestorManual(self.almacen, (self.origen,), self.staging,
                              politica=politica or self.politica)

    def ingestar(self, **opciones):
        return self.ingestor.ingestar(replace(self.solicitud, **opciones))

    def error(self, codigo, solicitud=None, *, ingestor=None, cancelacion=None):
        with self.assertRaises(ErrorIngestaManual) as c:
            (ingestor or self.ingestor).ingestar(solicitud or self.solicitud, cancelacion=cancelacion)
        self.assertEqual(c.exception.codigo, codigo)
        return c.exception

    def sin_residuos(self):
        self.assertEqual(list(self.staging.iterdir()), [])
        self.assertEqual(list(self.almacen.temporales.iterdir()), [])

    def abrir_instrumentado(self, *, leer=None, escribir=None):
        abrir = Path.open
        def interceptar(ruta, modo="r", *args, **kwargs):
            archivo = abrir(ruta, modo, *args, **kwargs)
            if ruta == self.archivo and modo == "rb" and leer:
                return ArchivoInstrumentado(archivo, leer=leer)
            if ruta.name == "contenido.bin" and modo == "xb" and escribir:
                return ArchivoInstrumentado(archivo, escribir=escribir)
            return archivo
        return patch.object(Path, "open", new=interceptar)

    def test_correcta_sha256_fisico_bytes_e_identidades_independientes(self):
        r = self.ingestar()
        a = r.recibo.activo
        with r.ruta_verificada.open("rb") as f:
            fisico = hashlib.file_digest(f, "sha256").hexdigest()
        self.assertEqual(fisico, hashlib.sha256(self.contenido).hexdigest())
        self.assertEqual(a.sha256, fisico)
        self.assertEqual(r.ruta_verificada.read_bytes(), self.contenido)
        self.assertEqual(a.size_bytes, len(self.contenido))
        self.assertEqual(a.estado, EstadoIncorporacion.INCORPORADA)
        self.assertEqual(r.estado, EstadoIngestaManual.INCORPORADA)
        self.assertEqual(r.integridad, IntegridadManual.COMPROBADA_LOCALMENTE)
        self.assertEqual(r.recibo.autenticidad, AutenticidadManual.NO_ACREDITADA)
        self.assertEqual(a.declaracion.proyecto_id, " Proyecto/01 ")
        self.assertEqual(a.object_id, " Objeto/01 ")
        self.assertEqual(a.declaracion.recurso_id, " Recurso/01 ")
        self.assertEqual(len({a.asset_id, a.sha256, r.recibo.adquisicion_id}), 3)
        self.assertEqual(r.comprobacion_utc.utcoffset().total_seconds(), 0)
        self.assertIsNone(a.media_detected)
        self.assertIsNone(r.hash_externo_coincide)
        self.sin_residuos()

    def test_origen_se_conserva_y_lecturas_acotadas(self):
        inicial, lecturas = self.archivo.stat(), []
        def leer(f, n):
            self.assertGreater(n, 0)
            self.assertLessEqual(n, self.politica.tamano_bloque)
            lecturas.append(n)
            return f.read(n)
        with self.abrir_instrumentado(leer=leer):
            self.ingestar()
        final = self.archivo.stat()
        self.assertGreater(len(lecturas), 2)
        self.assertEqual(self.archivo.read_bytes(), self.contenido)
        self.assertEqual((inicial.st_ino, inicial.st_size, inicial.st_mtime_ns),
                         (final.st_ino, final.st_size, final.st_mtime_ns))

    def test_persistencia_manual_sin_metadatos_http_ni_ruta_privada(self):
        r = self.ingestar()
        paquete = self.almacen._catalogo.evidencia(r.recibo.activo_id)
        self.assertEqual(paquete["version"], 2)
        self.assertEqual(paquete["mecanismo"], MecanismoAdquisicion.MANUAL.value)
        self.assertEqual(r.recibo.mecanismo, MecanismoAdquisicion.MANUAL)
        self.assertEqual(set(paquete), {"version", "mecanismo", "adquisicion_id", "documento"})
        serializado = json.dumps(paquete)
        self.assertNotIn(str(self.archivo), serializado)
        for campo in ("url_solicitada", "http_comprobada_utc", "capacidades_http_verificadas", "headers", "status_code"):
            self.assertNotIn(campo, serializado)
        self.assertIsNone(r.recibo.activo.declaracion.procedencia)
        self.almacen.close()
        self.almacen = AlmacenRAW(self.raw, (self.staging,), max_bytes=self.politica.max_bytes)
        recuperado = self.almacen.consultar_adquisicion(self.solicitud.adquisicion_id)
        self.assertEqual(recuperado, r.recibo)
        self.assertEqual(self.almacen.recuperar(recuperado.activo_id).read_bytes(), self.contenido)
        self.assertEqual(self.almacen._catalogo.conexion.execute("PRAGMA user_version").fetchone()[0], 2)

    def test_institucion_fechas_y_metadatos_desconocidos_no_inventados(self):
        r = self.ingestar()
        doc = r.recibo.procedencia
        for campo in ("fuente_declarada", "producto_id", "fecha_recepcion", "fecha_recurso",
                      "medio_entrega", "entregado_por", "sha256_externo", "formato_declarado"):
            self.assertIsNone(getattr(doc, campo))
        self.assertEqual(r.recibo.activo.declaracion.fuente, Fuente("SPICA", "recepcion-manual-local"))
        self.assertIsNone(doc.fundamento.permite_publicacion)
        self.assertIsNone(doc.fundamento.permite_redistribucion)

    def test_entrega_privada_restricciones_y_version_documental_persisten(self):
        doc = replace(self.doc, privado=True, fuente_declarada=Fuente(" Laboratorio/01 ", "LAB-000"),
            producto_id=" Producto/000 ", fecha_recepcion=date(2026, 10, 1), fecha_recurso=date(2020, 3, 4),
            medio_entrega="entrega local declarada", entregado_por="organizacion sintetica",
            registro_entregante_permitido=True,
            documentos=(DocumentoManual("urn:fixture:acta", "v2", date(2026, 9, 30)),),
            fundamento=replace(self.doc.fundamento, permite_publicacion=False, permite_redistribucion=False,
                                restricciones=("uso interno de prueba", "no redistribuir")))
        r = self.ingestar(procedencia=doc)
        self.assertEqual(self.almacen.consultar_evidencia(r.recibo.activo_id).procedencia, doc)
        self.assertEqual(r.recibo.activo.declaracion.fuente, doc.fuente_declarada)
        self.assertEqual(r.recibo.autenticidad, AutenticidadManual.NO_ACREDITADA)

    def test_fundamento_insuficiente_se_rechaza_antes_de_leer_o_crear_activo(self):
        for fundamento in (FundamentoUsoManual(), replace(self.doc.fundamento, permite_incorporacion=False),
                           replace(self.doc.fundamento, documento=None)):
            with self.subTest(fundamento=fundamento), patch.object(self.ingestor, "_origen") as origen:
                self.error("fundamento_de_uso_insuficiente", replace(self.solicitud,
                           procedencia=replace(self.doc, fundamento=fundamento)))
                origen.assert_not_called()
        self.assertEqual(self.almacen._catalogo.listar(), ())
        self.sin_residuos()

    def test_metadatos_con_credenciales_rechazados_y_error_sin_secretos(self):
        doc = replace(self.doc, medio_entrega="https://usuario:CLAVE_SINTETICA@ejemplo.invalid/archivo")
        error = self.error("ingesta_manual_no_disponible", replace(self.solicitud, procedencia=doc))
        self.assertNotIn("CLAVE_SINTETICA", str(error))
        self.assertNotIn(str(self.base), json.dumps(error.diagnostico_publico()))
        self.assertIsNone(error.__context__)
        self.assertIsNone(error.__cause__)
        self.assertEqual(self.almacen._catalogo.listar(), ())

    def test_archivo_vacio_permitido_con_hash_externo_real(self):
        self.archivo.write_bytes(b"")
        r = self.ingestar(procedencia=replace(self.doc, sha256_externo=hashlib.sha256(b"").hexdigest()))
        self.assertEqual(r.recibo.activo.size_bytes, 0)
        self.assertTrue(r.hash_externo_coincide)
        self.assertEqual(r.ruta_verificada.read_bytes(), b"")
        self.sin_residuos()

    def test_politica_puede_rechazar_vacio(self):
        self.archivo.write_bytes(b"")
        self.error("archivo_vacio_no_admitido", ingestor=self.crear_ingestor(
            replace(self.politica, aceptar_vacios=False)))
        self.assertEqual(self.almacen._catalogo.listar(), ())

    def test_limite_exacto_admitido_y_limite_superado_rechazado(self):
        ingestor = self.crear_ingestor(replace(self.politica, max_bytes=len(self.contenido)))
        r = ingestor.ingestar(self.solicitud)
        self.archivo.write_bytes(self.contenido + b"x")
        self.error("limite_manual_excedido", replace(self.solicitud, adquisicion_id=uuid4().hex), ingestor=ingestor)
        self.assertEqual(len(self.almacen._catalogo.listar()), 1)
        self.assertEqual(r.ruta_verificada.read_bytes(), self.contenido)
        self.sin_residuos()

    def test_archivo_grande_por_bloques_sin_limite_de_get_http(self):
        contenido = b"inventado" * 150_000
        self.archivo.write_bytes(contenido)
        ingestor = self.crear_ingestor(replace(self.politica, tamano_bloque=65_536))
        r = ingestor.ingestar(self.solicitud)
        self.assertGreater(r.recibo.activo.size_bytes, 1_048_576)
        self.assertEqual(r.recibo.activo.sha256, hashlib.sha256(contenido).hexdigest())
        self.sin_residuos()

    def test_inexistente_y_directorio_no_se_presentan_como_archivos(self):
        self.error("archivo_manual_ausente", replace(self.solicitud, archivo=self.origen / "ausente.bin"))
        self.error("origen_no_regular_o_compartido", replace(self.solicitud, archivo=self.origen))
        self.assertEqual(self.almacen._catalogo.listar(), ())

    def test_raw_staging_y_origen_no_autorizado_rechazados_sin_inspeccion(self):
        for archivo in (self.raw / "catalogo.sqlite3", self.staging / "contenido.bin", self.base / "otro.bin"):
            with self.subTest(archivo=archivo.name), patch("spica.adquisicion.manual.ingesta._ruta") as ruta:
                self.error("origen_manual_no_autorizado", replace(self.solicitud, archivo=archivo))
                ruta.assert_not_called()
        self.assertEqual(self.almacen._catalogo.listar(), ())

    def test_ruta_con_padre_ambiguo_rechazada(self):
        self.error("ruta_insegura", replace(self.solicitud, archivo=self.origen / ".." / "origen" / self.archivo.name))

    def test_enlace_simbolico_detectado_sin_seguirlo(self):
        original = Path.is_symlink
        with patch.object(Path, "is_symlink", new=lambda p: p == self.archivo or original(p)):
            self.error("enlace_no_autorizado")
        self.assertEqual(self.almacen._catalogo.listar(), ())

    def test_junction_detectada_sin_seguirla(self):
        original = Path.is_junction
        with patch.object(Path, "is_junction", new=lambda p: p == self.origen or original(p)):
            self.error("enlace_no_autorizado")

    def test_otro_reparse_point_rechazado(self):
        lstat = Path.lstat
        def estado(p, *args, **kwargs):
            s = lstat(p, *args, **kwargs)
            return SimpleNamespace(st_file_attributes=0x400) if p == self.archivo else s
        with patch.object(Path, "lstat", new=estado):
            self.error("reparse_point_no_admitido")

    def test_enlace_duro_real_rechazado_sin_alterar_contenido(self):
        alias = self.origen / "alias.bin"
        os.link(self.archivo, alias)
        self.error("origen_no_regular_o_compartido")
        self.assertEqual(alias.read_bytes(), self.contenido)

    def test_ads_y_unc_no_son_origenes_locales_admitidos(self):
        self.error("ruta_manual_no_local_o_ambigua", replace(self.solicitud,
                   archivo=self.archivo.with_name(self.archivo.name + ":alternativo")))
        self.error("origen_manual_no_autorizado", replace(self.solicitud,
                   archivo=Path(r"\\servidor.invalid\recurso\archivo.bin")))

    def test_extension_no_valida_estructura_ni_ejecuta_codigo(self):
        self.archivo.write_bytes(b"raise RuntimeError('no ejecutar')\n")
        r = self.ingestar(procedencia=replace(self.doc, formato_declarado="XLSX"))
        self.assertIsNone(r.recibo.activo.media_detected)
        self.assertEqual(r.ruta_verificada.read_bytes(), self.archivo.read_bytes())
        self.assertEqual(r.recibo.autenticidad, AutenticidadManual.NO_ACREDITADA)

    def test_hash_externo_correcto_sin_certificar_autenticidad(self):
        r = self.ingestar(procedencia=replace(self.doc, sha256_externo=hashlib.sha256(self.contenido).hexdigest()))
        self.assertTrue(r.hash_externo_coincide)
        self.assertEqual(r.recibo.autenticidad, AutenticidadManual.NO_ACREDITADA)

    def test_hash_externo_discrepante_no_publica_y_limpia(self):
        e = self.error("hash_externo_discrepante", replace(self.solicitud,
                       procedencia=replace(self.doc, sha256_externo="0" * 64)))
        self.assertEqual(e.integridad, IntegridadManual.HASH_EXTERNO_DISCREPANTE)
        self.assertEqual(self.almacen._catalogo.listar(), ())
        self.sin_residuos()

    def test_error_lectura_no_se_confunde_con_integridad_negativa(self):
        def leer(f, n):
            raise OSError("ruta_privada/CLAVE_SINTETICA")
        with self.abrir_instrumentado(leer=leer):
            e = self.error("lectura_manual_no_disponible")
        self.assertEqual(e.integridad, IntegridadManual.NO_COMPROBADA)
        self.assertNotIn("CLAVE_SINTETICA", str(e))
        self.assertIsNone(e.__context__)
        self.sin_residuos()

    def test_error_escritura_y_escritura_corta_no_crean_activo(self):
        def escribir(f, bloque):
            raise OSError("disco no disponible; dato privado")
        with self.abrir_instrumentado(escribir=escribir):
            self.error("escritura_manual_no_disponible")
        with self.abrir_instrumentado(escribir=lambda f, b: f.write(b[:-1])):
            self.error("escritura_manual_incompleta")
        self.assertEqual(self.almacen._catalogo.listar(), ())
        self.sin_residuos()

    def test_error_fsync_no_presenta_copia_completa(self):
        with patch("spica.adquisicion.manual.ingesta.os.fsync", side_effect=OSError("fallo simulado")):
            self.error("escritura_manual_no_disponible")
        self.assertEqual(self.almacen._catalogo.listar(), ())
        self.sin_residuos()

    def test_espacio_insuficiente_detiene_antes_de_copiar(self):
        with patch("spica.adquisicion.manual.ingesta.shutil.disk_usage", return_value=SimpleNamespace(free=0)):
            self.error("espacio_manual_insuficiente")
        self.assertEqual(self.almacen._catalogo.listar(), ())
        self.sin_residuos()

    def test_cancelacion_antes_de_comenzar(self):
        evento = Event()
        evento.set()
        with patch.object(self.ingestor, "_origen") as origen:
            self.error("ingesta_manual_cancelada", cancelacion=evento)
            origen.assert_not_called()
        self.assertEqual(self.almacen._catalogo.listar(), ())

    def test_cancelacion_durante_copia_limpia_y_permite_reintento_explicito(self):
        evento = Event()
        def leer(f, n):
            evento.set()
            return f.read(n)
        with self.abrir_instrumentado(leer=leer):
            self.error("ingesta_manual_cancelada", cancelacion=evento)
        self.sin_residuos()
        self.assertEqual(self.almacen._catalogo.listar(), ())
        self.assertEqual(self.ingestar().estado, EstadoIngestaManual.INCORPORADA)

    def test_keyboard_interrupt_limpia_y_no_se_oculta(self):
        def leer(f, n):
            raise KeyboardInterrupt
        with self.abrir_instrumentado(leer=leer), self.assertRaises(KeyboardInterrupt):
            self.ingestar()
        self.sin_residuos()
        self.assertEqual(self.almacen._catalogo.listar(), ())

    def test_cambio_observable_de_origen_durante_lectura(self):
        cambiado = []
        def leer(f, n):
            bloque = f.read(n)
            if not cambiado:
                cambiado.append(True)
                with self.archivo.open("r+b") as otro:
                    otro.write(b"x" * len(self.contenido))
                s = self.archivo.stat()
                os.utime(self.archivo, ns=(s.st_atime_ns, s.st_mtime_ns + 100_000_000))
            return bloque
        with self.abrir_instrumentado(leer=leer):
            self.error("origen_modificado")
        self.assertEqual(self.almacen._catalogo.listar(), ())
        self.sin_residuos()

    def test_crecimiento_durante_lectura_no_burla_limite(self):
        ingestor = self.crear_ingestor(replace(self.politica, max_bytes=len(self.contenido)))
        cambiado = []
        def leer(f, n):
            if not cambiado:
                cambiado.append(True)
                with self.archivo.open("ab") as otro:
                    otro.write(b"x" * 50)
            return f.read(n)
        with self.abrir_instrumentado(leer=leer):
            self.error("limite_manual_excedido", ingestor=ingestor)
        self.sin_residuos()

    def test_modificacion_staging_entre_etapas_no_publica(self):
        incorporar = self.almacen.incorporar_manual_documentado
        def modificar(entrada, *args, **kwargs):
            entrada.write_bytes(b"x" * len(self.contenido))
            return incorporar(entrada, *args, **kwargs)
        with patch.object(self.almacen, "incorporar_manual_documentado", side_effect=modificar):
            e = self.error("evidencia_entrada_no_coincidente")
        self.assertEqual(self.almacen.metadatos(e.activo_id).estado, EstadoIncorporacion.FALLIDA)
        self.assertIsInstance(self.almacen.consultar_adquisicion(self.solicitud.adquisicion_id), ReciboIngestaManual)
        self.assertEqual(tuple((self.raw / "sha256").glob("*/*")), ())
        self.sin_residuos()

    def test_eventos_independientes_deduplican_sin_perder_antecedentes(self):
        primero = self.ingestar()
        otro_doc = replace(self.doc, medio_entrega="segunda entrega sintetica independiente")
        segundo = self.ingestar(adquisicion_id=uuid4().hex, procedencia=otro_doc)
        self.assertNotEqual(primero.recibo.adquisicion_id, segundo.recibo.adquisicion_id)
        self.assertNotEqual(primero.recibo.activo_id, segundo.recibo.activo_id)
        self.assertEqual(primero.ruta_verificada, segundo.ruta_verificada)
        self.assertEqual(len(self.almacen._catalogo.listar()), 2)
        self.assertEqual(len(tuple((self.raw / "sha256").glob("*/*"))), 1)
        for r in (primero, segundo):
            self.assertEqual(self.almacen.consultar_adquisicion(r.recibo.adquisicion_id).procedencia, r.recibo.procedencia)
        self.sin_residuos()

    def test_idempotencia_recomprueba_sin_copia_ni_nuevo_activo(self):
        primero = self.ingestar()
        with patch.object(self.almacen, "incorporar_manual_documentado") as incorporar:
            segundo = self.ingestar()
            incorporar.assert_not_called()
        self.assertEqual(segundo.estado, EstadoIngestaManual.YA_REGISTRADA)
        self.assertEqual(primero.recibo.activo_id, segundo.recibo.activo_id)
        self.assertEqual(len(self.almacen._catalogo.listar()), 1)
        self.sin_residuos()

    def test_idempotencia_rechaza_metadatos_y_bytes_contradictorios(self):
        r = self.ingestar()
        self.error("conflicto_idempotencia_manual", replace(self.solicitud,
                   procedencia=replace(self.doc, medio_entrega="otro fundamento de entrega")))
        self.archivo.write_bytes(b"x" * len(self.contenido))
        self.error("conflicto_contenido_manual")
        self.assertEqual(r.ruta_verificada.read_bytes(), self.contenido)
        self.assertEqual(len(self.almacen._catalogo.listar()), 1)

    def test_original_fisico_existente_corrupto_nunca_se_sobrescribe(self):
        r = self.ingestar()
        corrupto = b"x" * len(self.contenido)
        r.ruta_verificada.write_bytes(corrupto)  # Solo RAW sintético de esta prueba.
        self.error("contenido_no_coincidente", replace(self.solicitud, adquisicion_id=uuid4().hex))
        self.assertEqual(r.ruta_verificada.read_bytes(), corrupto)
        self.sin_residuos()

    def test_reintento_idempotente_detecta_original_ausente(self):
        r = self.ingestar()
        r.ruta_verificada.unlink()  # Solo fixture efímero.
        self.error("integridad_local_fallida")
        self.assertEqual(len(self.almacen._catalogo.listar()), 1)

    def test_fallo_al_registrar_no_es_exito_y_reintento_explicito_sin_evento_es_posible(self):
        with patch.object(self.almacen._catalogo, "preparar", side_effect=sqlite3.OperationalError("dato privado")):
            e = self.error("error_sqlite")
        self.assertIsNotNone(e.activo_id)
        self.assertIsNone(self.almacen.consultar_adquisicion(self.solicitud.adquisicion_id, permitir_ausente=True))
        self.sin_residuos()
        self.assertEqual(self.ingestar().estado, EstadoIngestaManual.INCORPORADA)

    def test_fallo_despues_de_publicacion_conserva_evidencia_y_exige_revision(self):
        transicion = self.almacen._catalogo.transicion
        def fallar(activo_id, estado, **datos):
            if estado is EstadoIncorporacion.INCORPORADA:
                raise sqlite3.OperationalError("fallo sintetico")
            return transicion(activo_id, estado, **datos)
        with patch.object(self.almacen._catalogo, "transicion", side_effect=fallar):
            e = self.error("error_sqlite")
        a = self.almacen.metadatos(e.activo_id)
        self.assertEqual(a.estado, EstadoIncorporacion.FALLIDA)
        ruta = self.raw / a.storage_ref
        self.assertEqual(ruta.read_bytes(), self.contenido)
        self.error("adquisicion_manual_requiere_revision")
        self.assertEqual(len(self.almacen._catalogo.listar()), 1)
        self.assertIn(a.asset_id, self.almacen.diagnosticar().incompletas)
        self.sin_residuos()

    def test_cancelacion_tras_publicar_preserva_evento_sin_repetirlo(self):
        evento, incorporar = Event(), self.almacen.incorporar_manual_documentado
        def cancelar(*args, **kwargs):
            activo = incorporar(*args, **kwargs)
            evento.set()
            return activo
        with patch.object(self.almacen, "incorporar_manual_documentado", side_effect=cancelar):
            e = self.error("ingesta_manual_cancelada", cancelacion=evento)
        self.assertEqual(self.almacen.metadatos(e.activo_id).estado, EstadoIncorporacion.INCORPORADA)
        self.assertEqual(self.ingestar().estado, EstadoIngestaManual.YA_REGISTRADA)
        self.assertEqual(len(self.almacen._catalogo.listar()), 1)
        self.sin_residuos()

    def test_limpieza_fallida_informa_residuo_sin_declarar_exito(self):
        unlink = Path.unlink
        def fallar(p, *args, **kwargs):
            if p.name == "contenido.bin":
                raise PermissionError("archivo en uso sintetico")
            return unlink(p, *args, **kwargs)
        with patch.object(Path, "unlink", new=fallar):
            e = self.error("limpieza_manual_requiere_revision")
        self.assertEqual(e.temporal_restante.parent, self.staging)
        self.assertEqual(self.almacen.metadatos(e.activo_id).estado, EstadoIncorporacion.INCORPORADA)
        self.assertTrue(e.diagnostico_publico()["temporal_pendiente"])
        self.assertNotIn(str(self.base), json.dumps(e.diagnostico_publico()))

    def test_limpieza_no_borra_archivo_ajeno_en_directorio_propio(self):
        incorporar = self.almacen.incorporar_manual_documentado
        def agregar(entrada, *args, **kwargs):
            (entrada.parent / "ajeno.txt").write_bytes(b"preservar fixture")
            return incorporar(entrada, *args, **kwargs)
        with patch.object(self.almacen, "incorporar_manual_documentado", side_effect=agregar):
            e = self.error("limpieza_manual_requiere_revision")
        self.assertEqual((e.temporal_restante / "ajeno.txt").read_bytes(), b"preservar fixture")
        self.assertFalse((e.temporal_restante / "contenido.bin").exists())

    def test_error_permiso_en_origen_no_expone_ruta(self):
        with patch.object(self.ingestor, "_origen", side_effect=PermissionError(str(self.archivo))):
            e = self.error("operacion_manual_sin_permisos")
        self.assertNotIn(str(self.archivo), repr(e))
        self.assertIsNone(e.__context__)
        self.sin_residuos()

    def test_metadatos_ambiguos_no_se_tratan_como_adquisicion_ausente(self):
        self.ingestar()
        conexion = self.almacen._catalogo.conexion
        with conexion:
            fila = conexion.execute("SELECT * FROM activos").fetchone()
            columnas = tuple(fila.keys())
            valores = tuple(uuid4().hex if c == "id" else fila[c] for c in columnas)
            conexion.execute("INSERT INTO activos(" + ",".join(columnas) + ") VALUES ("
                             + ",".join("?" for _ in columnas) + ")", valores)
        self.error("adquisicion_no_identificada_o_ambigua")
        self.assertEqual(len(self.almacen._catalogo.listar()), 2)
        self.sin_residuos()

    def test_decoder_rechaza_evidencia_contradictoria_o_campos_http_inyectados(self):
        r = self.ingestar()
        paquete = self.almacen._catalogo.evidencia(r.recibo.activo_id)
        for mutar in (lambda p: p.update(url_solicitada="https://ejemplo.invalid"),
                      lambda p: p["documento"].update(sha256_externo="0" * 64),
                      lambda p: p.update(version=True)):
            p = json.loads(json.dumps(paquete))
            mutar(p)
            with self.assertRaises(ErrorAlmacenamientoRAW) as e:
                desempaquetar(p, r.recibo.activo)
            self.assertEqual(e.exception.codigo, "evidencia_persistida_invalida")

    def test_puerta_raw_no_admite_hash_externo_discrepante_ni_evento_repetido(self):
        entrada = self.staging / "directa.bin"
        entrada.write_bytes(self.contenido)
        d = DeclaracionRAW(self.solicitud.proyecto_id, self.solicitud.objeto_id,
                           Fuente("SPICA", "recepcion-manual-local"), self.solicitud.recurso_id)
        with self.assertRaises(ErrorAlmacenamientoRAW) as e:
            self.almacen.incorporar_manual_documentado(entrada, d, replace(self.doc, sha256_externo="0" * 64),
                adquisicion_id=self.solicitud.adquisicion_id, tamano_esperado=len(self.contenido),
                sha256_esperado=hashlib.sha256(self.contenido).hexdigest())
        self.assertEqual(e.exception.codigo, "hash_externo_discrepante")
        self.assertEqual(self.almacen._catalogo.listar(), ())
        self.ingestar()
        with self.assertRaises(ErrorAlmacenamientoRAW) as e:
            self.almacen.incorporar_manual_documentado(entrada, d, self.doc,
                adquisicion_id=self.solicitud.adquisicion_id, tamano_esperado=len(self.contenido),
                sha256_esperado=hashlib.sha256(self.contenido).hexdigest())
        self.assertEqual(e.exception.codigo, "adquisicion_manual_ya_registrada")
        self.assertEqual(len(self.almacen._catalogo.listar()), 1)

    def test_configuracion_rechaza_raices_inseguras_sin_crearlas(self):
        for raices, staging in (((self.base,), self.staging), ((self.raw,), self.staging),
                                ((self.origen,), self.origen), ((self.origen,), self.base / "ausente")):
            with self.subTest(raices=raices, staging=staging), self.assertRaises(ValueError):
                IngestorManual(self.almacen, raices, staging, politica=self.politica)
        self.assertFalse((self.base / "ausente").exists())
        with self.assertRaises(ValueError):
            self.crear_ingestor(replace(self.politica, max_bytes=self.almacen.max_bytes + 1))

    def test_no_se_realiza_ninguna_conexion(self):
        with (patch.object(socket.socket, "connect", side_effect=AssertionError("red prohibida")) as conectar,
              patch.object(socket, "getaddrinfo", side_effect=AssertionError("DNS prohibido")) as dns):
            self.ingestar()
            conectar.assert_not_called()
            dns.assert_not_called()


class ContratosManualesTests(unittest.TestCase):
    def test_sin_consentimiento_no_se_registra_entregante(self):
        with self.assertRaises(ValueError):
            ProcedenciaManual(entregado_por="persona sintetica")

    def test_fechas_civiles_conservan_precision_y_no_inventan_zona(self):
        doc = DocumentoManual("urn:prueba:fecha", fecha=date(2020, 1, 2))
        self.assertEqual(doc.fecha, date(2020, 1, 2))
        with self.assertRaises(TypeError):
            DocumentoManual("urn:prueba:fecha", fecha=datetime.now(timezone.utc))
        with self.assertRaises(TypeError):
            ProcedenciaManual(fecha_recepcion="desconocida")

    def test_politicas_y_metadatos_tipados_no_admiten_valores_ambiguos(self):
        for kwargs in ({"max_bytes": True}, {"max_bytes": 0}, {"tamano_bloque": 1_048_577},
                       {"margen_libre": -1}, {"aceptar_vacios": 1}):
            with self.subTest(kwargs=kwargs), self.assertRaises((TypeError, ValueError)):
                PoliticaIngestaManual(**kwargs)
        with self.assertRaises(ValueError):
            ProcedenciaManual(sha256_externo="desconocido")
        with self.assertRaises(TypeError):
            FundamentoUsoManual(permite_incorporacion="si")
        with self.assertRaises(ValueError):
            ProcedenciaManual(documentos=(DocumentoManual("urn:prueba:uno"), DocumentoManual("urn:prueba:uno")))


if __name__ == "__main__":
    unittest.main()
