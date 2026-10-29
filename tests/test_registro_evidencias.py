"""SUADC-03/06: exclusivamente HTML, bytes y SQLite sintéticos efímeros."""

from dataclasses import replace
from contextlib import closing
from datetime import datetime, timedelta, timezone
import hashlib
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
from spica.adquisicion.almacenamiento import AlmacenRAW, DeclaracionRAW, ErrorAlmacenamientoRAW, EstadoIncorporacion
from spica.adquisicion.catalogo import (
    CatalogoCientifico, CapacidadCatalogo, ErrorCatalogo, EstadoRegistroDocumental,
    EstadoVerificacion, EvidenciaDocumental, FuenteCatalogo, MecanismoAdquisicion,
    ProcedenciaCatalogo, ProductoCatalogo, RecursoCatalogo,
)
from spica.adquisicion.conectores.senamhi import ConectorSENAMHIPNDA, ErrorConectorPNDA, ORIGEN_PNDA, FUENTE_SENAMHI
from spica.adquisicion.integracion import AdaptadorHTTPRAW, ErrorIntegracionHTTPRAW
from spica.adquisicion.nucleo import Fuente
from spica.adquisicion.transportes import ClienteHTTP
from test_conector_senamhi_pnda import distribucion
from test_transporte_http import Flujo


class RegistroEvidenciasTests(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.gettempdir()).resolve() / ("spica-evidencias-" + uuid4().hex)
        self.base.mkdir(mode=0o755)
        self.addCleanup(self.limpiar)
        self.raiz, self.staging = self.base / "raw", self.base / "staging"
        self.raiz.mkdir()
        self.staging.mkdir()
        self.almacen = AlmacenRAW(self.raiz, (self.staging,), max_bytes=1_048_576,
                                  claves_parametros_publicos=("producto_id",))
        self.addCleanup(lambda: self.almacen.close())
        self.ruta_catalogo = self.base / "descubrimiento.sqlite3"
        self.catalogo = CatalogoCientifico(self.ruta_catalogo)
        self.addCleanup(lambda: self.catalogo.close())
        self.url = ORIGEN_PNDA + "/sites/default/files/diccionario_sintetico.xlsx"
        self.licencia = "https://licencia.invalid/declaracion-v1"
        self.contenido = b"contenido sintetico; sin validacion estructural ni cientifica\n"
        self.peticiones = []
        self.recursos = [("Diccionario sintetico", self.url)]
        self.cliente = ClienteHTTP((ORIGEN_PNDA,), transporte=httpx.MockTransport(self.responder))
        self.addCleanup(self.cliente.close)
        self.adaptador = AdaptadorHTTPRAW(self.cliente, self.almacen, self.staging, max_bytes=1_048_576)

    def limpiar(self):
        assert self.base.resolve().parent == Path(tempfile.gettempdir()).resolve()
        assert self.base.name.startswith("spica-evidencias-")
        shutil.rmtree(self.base)

    def responder(self, peticion):
        self.peticiones.append(peticion)
        if peticion.url.path.startswith("/dataset/"):
            html = "".join(distribucion(titulo, url) for titulo, url in self.recursos)
            if self.licencia is not None:
                html += ('<div class="pane-dkan-sitewide-dkan-sitewide-license"><a href="'
                         + self.licencia + '">Licencia declarada</a></div>')
            return httpx.Response(200, headers={"Content-Type": "text/html"}, stream=Flujo((html.encode(),)))
        return httpx.Response(200, headers={"Content-Length": str(len(self.contenido))},
                              stream=Flujo((self.contenido,)))

    def conector(self, producto="producto-sintetico"):
        return ConectorSENAMHIPNDA(self.cliente, self.adaptador,
                                    pagina_producto=ORIGEN_PNDA + "/dataset/" + producto)

    def adquirir(self, conector):
        return conector.adquirir(self.url, proyecto_id="proyecto-sintetico", objeto_id="objeto-sintetico")

    def preparado(self):
        c = self.conector()
        c.descubrir()
        c.registrar_catalogo(self.catalogo)
        return c

    def manual(self, fuente=None):
        fuente = fuente or Fuente("institucion-sintetica", " Institucion/01 ")
        p = ProcedenciaCatalogo("urn:prueba:publicacion", datetime(2020, 1, 1, tzinfo=timezone.utc), "sintetico")
        self.catalogo.registrar_documental(FuenteCatalogo(fuente, p))
        producto = ProductoCatalogo(fuente, " Producto/01 ", p, utiliza_estaciones=True)
        self.catalogo.registrar_documental(producto)
        return producto

    def declaracion_documento(self):
        d = DeclaracionRAW("p", "o", Fuente("sintetica", "institucion"), " Recurso/01 ",
                           parametros_publicos={"producto_id": " Producto/01 "})
        return d, EvidenciaDocumental(d.fuente, d.recurso_id, producto_id=" Producto/01 ")

    def dump_raw(self):
        return "\n".join(self.almacen._catalogo.conexion.iterdump())

    def test_redescubrir_mismo_producto_no_conflicta(self):
        c = self.conector()
        c.descubrir()
        c.registrar_catalogo(self.catalogo)
        c.descubrir()
        c.registrar_catalogo(self.catalogo)
        self.assertEqual(self.catalogo.consultar_producto(FUENTE_SENAMHI, c.producto_id).revision, 1)

    def test_dos_productos_comparten_institucion(self):
        for producto in ("producto-uno", "producto-dos"):
            c = self.conector(producto)
            c.descubrir()
            c.registrar_catalogo(self.catalogo)
        from spica.adquisicion.catalogo import FuenteCatalogo, ProductoCatalogo
        self.assertEqual(len(self.catalogo.listar(FuenteCatalogo)), 1)
        self.assertEqual(len(self.catalogo.listar(ProductoCatalogo)), 2)

    def test_cambio_licencia_genera_revision_y_conserva_historia(self):
        c = self.conector()
        anterior = c.descubrir().producto
        c.registrar_catalogo(self.catalogo)
        self.licencia = "https://licencia.invalid/declaracion-v2"
        c.descubrir()
        c.registrar_catalogo(self.catalogo)
        historial = self.catalogo.historial(anterior)
        self.assertEqual(tuple(r.revision for r in historial), (1, 2))
        self.assertEqual(historial[0].entidad.restricciones_licencia, anterior.restricciones_licencia)
        self.assertEqual(historial[1].entidad.restricciones_licencia, self.licencia)

    def test_evidencia_adquisicion_sobrevive_cierre_sqlite(self):
        c = self.conector()
        c.descubrir()
        c.registrar_catalogo(self.catalogo)
        resultado = self.adquirir(c)
        activo_id = resultado.resultado_raw.activo.asset_id
        self.almacen.close()
        self.almacen = AlmacenRAW(self.raiz, (self.staging,), claves_parametros_publicos=("producto_id",))
        evidencia = self.almacen.consultar_evidencia(activo_id)
        self.assertEqual(evidencia.documento.referencia_licencia, self.licencia)
        self.assertEqual(evidencia.activo_id, activo_id)
        self.assertEqual(evidencia.sha256, hashlib.sha256(self.contenido).hexdigest())
        self.assertEqual(evidencia.size_bytes, len(self.contenido))

    def test_resultados_explicitos_nuevo_identico_revision_contradiccion(self):
        producto = self.manual()
        nueva = replace(producto, identificador="otro")
        r = self.catalogo.registrar_documental(nueva)
        self.assertEqual(r.estado, EstadoRegistroDocumental.NUEVO)
        self.assertEqual(self.catalogo.registrar_documental(nueva).estado, EstadoRegistroDocumental.IDENTICO)
        nueva = replace(nueva, descripcion="Correccion documental", procedencia=replace(
            nueva.procedencia, revisada_utc=nueva.procedencia.revisada_utc + timedelta(days=1)))
        r = self.catalogo.registrar_documental(nueva)
        self.assertEqual((r.estado, r.registro.revision), (EstadoRegistroDocumental.REVISION_DOCUMENTAL, 2))
        contradiccion = replace(nueva, utiliza_estaciones=False)
        r = self.catalogo.registrar_documental(contradiccion)
        self.assertEqual(r.estado, EstadoRegistroDocumental.CONTRADICCION)
        self.assertEqual(self.catalogo.consultar_producto(producto.fuente, "otro").entidad, nueva)

    def test_solo_fecha_de_reconsulta_es_idempotente(self):
        producto = self.manual()
        posterior = replace(producto, procedencia=replace(producto.procedencia,
            revisada_utc=producto.procedencia.revisada_utc + timedelta(days=1)))
        r = self.catalogo.registrar_documental(posterior)
        self.assertEqual(r.estado, EstadoRegistroDocumental.IDENTICO)
        self.assertEqual(r.registro.entidad, producto)
        self.assertEqual(len(self.catalogo.historial(producto)), 1)

    def test_dos_recursos_no_comparten_identidad_ni_evidencia(self):
        otra_url = ORIGEN_PNDA + "/sites/default/files/segundo_sintetico.xlsx"
        self.recursos.append(("Diccionario segundo sintetico", otra_url))
        c = self.preparado()
        self.assertEqual(len(self.catalogo.listar_recursos(FUENTE_SENAMHI, c.producto_id)), 2)
        a = self.adquirir(c).resultado_raw
        b = c.adquirir(otra_url, proyecto_id="proyecto-sintetico", objeto_id="objeto-sintetico").resultado_raw
        ea, eb = (self.almacen.consultar_evidencia(r.activo.asset_id) for r in (a, b))
        self.assertEqual((ea.documento.recurso_id, eb.documento.recurso_id), (self.url, otra_url))
        self.assertEqual((ea.url_solicitada, eb.url_solicitada), (self.url, otra_url))
        self.assertNotEqual(ea.adquisicion_id, eb.adquisicion_id)
        self.assertEqual(a.ruta_verificada, b.ruta_verificada)

    def test_identificadores_locales_iguales_en_instituciones_diferentes(self):
        registros = []
        for fuente in (Fuente("institucion-A", "misma"), Fuente("institucion-B", "misma")):
            p = self.manual(fuente)
            r = RecursoCatalogo(fuente, p.identificador, " Recurso/01 ", "https://recurso.invalid/archivo", p.procedencia)
            registros.append(self.catalogo.registrar_documental(r).registro)
        self.assertNotEqual(registros[0].entidad.fuente, registros[1].entidad.fuente)
        for r in registros:
            e = r.entidad
            self.assertEqual(self.catalogo.consultar_recurso(e.fuente, e.producto_id, e.identificador), r)
            self.assertEqual(e.identificador, " Recurso/01 ")

    def test_revision_historica_de_recurso_y_producto_tras_reabrir(self):
        c = self.preparado()
        recurso = self.catalogo.consultar_recurso(FUENTE_SENAMHI, c.producto_id, self.url).entidad
        producto = self.catalogo.consultar_producto(FUENTE_SENAMHI, c.producto_id).entidad
        self.licencia = "https://licencia.invalid/revision-2"
        c.descubrir()
        c.registrar_catalogo(self.catalogo)
        self.catalogo.close()
        self.catalogo = CatalogoCientifico(self.ruta_catalogo)
        self.assertEqual(self.catalogo.consultar_revision(recurso, 1).entidad, recurso)
        self.assertEqual(self.catalogo.consultar_revision(producto, 1).entidad, producto)
        self.assertEqual(self.catalogo.consultar_recurso(FUENTE_SENAMHI, c.producto_id, self.url).revision, 2)
        with self.assertRaises(ErrorCatalogo):
            self.catalogo.consultar_revision(recurso, 3)

    def test_nueva_revision_no_modifica_adquisicion_anterior(self):
        c = self.preparado()
        a = self.adquirir(c).resultado_raw.activo
        original = self.almacen.consultar_evidencia(a.asset_id)
        self.licencia = "https://licencia.invalid/revision-2"
        c.descubrir()
        c.registrar_catalogo(self.catalogo)
        b = self.adquirir(c).resultado_raw.activo
        posterior = self.almacen.consultar_evidencia(b.asset_id)
        self.assertEqual(self.almacen.consultar_evidencia(a.asset_id), original)
        self.assertEqual((original.documento.revision_documental, posterior.documento.revision_documental), (1, 2))
        self.assertNotEqual(original.documento.referencia_licencia, posterior.documento.referencia_licencia)
        self.assertEqual((original.sha256, original.size_bytes), (posterior.sha256, posterior.size_bytes))

    def test_adquisiciones_repetidas_ids_distintos_y_mismos_bytes(self):
        c = self.preparado()
        activos = [self.adquirir(c).resultado_raw.activo for _ in range(2)]
        evidencias = [self.almacen.consultar_evidencia(a.asset_id) for a in activos]
        self.assertNotEqual(evidencias[0].adquisicion_id, evidencias[1].adquisicion_id)
        self.assertNotEqual(activos[0].asset_id, activos[1].asset_id)
        self.assertEqual(activos[0].storage_ref, activos[1].storage_ref)
        for a, e in zip(activos, evidencias):
            self.assertEqual(self.almacen.consultar_adquisicion(e.adquisicion_id), e)
            self.assertNotEqual(e.adquisicion_id, a.asset_id)
            self.assertEqual((a.object_id, a.declaracion.proyecto_id), ("objeto-sintetico", "proyecto-sintetico"))
            self.assertEqual(self.almacen.recuperar(a.asset_id).read_bytes(), self.contenido)
        self.assertEqual(len(self.almacen._catalogo.listar()), 2)
        self.assertEqual(self.almacen._catalogo.conexion.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_adquisicion_por_id_persiste_tras_reabrir(self):
        c = self.preparado()
        a = self.adquirir(c).resultado_raw.activo
        e = self.almacen.consultar_evidencia(a.asset_id)
        self.almacen.close()
        self.almacen = AlmacenRAW(self.raiz, (self.staging,))
        self.assertEqual(self.almacen.consultar_adquisicion(e.adquisicion_id), e)
        self.assertEqual(self.almacen.recuperar(a.asset_id).read_bytes(), self.contenido)

    def test_evidencia_incompleta_permanece_desconocida(self):
        d, documento = self.declaracion_documento()
        a = self.adaptador.adquirir_documentado(self.url, d, documento).activo
        e = self.almacen.consultar_evidencia(a.asset_id)
        self.assertEqual(e.documento.estado, EstadoVerificacion.DESCONOCIDO)
        for valor in (e.documento.referencia_publicacion, e.documento.descubierta_utc,
                      e.documento.licencia_declarada, e.documento.referencia_licencia,
                      e.documento.revision_documental, e.documento.procedencia):
            self.assertIsNone(valor)
        self.assertEqual(e.documento.capacidades_documentadas, ())
        self.assertEqual(e.capacidades_http_verificadas, (MecanismoAdquisicion.HTTP_DIRECTO,))

    def test_licencia_no_documentada_no_se_inventa(self):
        self.licencia = None
        c = self.preparado()
        a = self.adquirir(c).resultado_raw.activo
        e = self.almacen.consultar_evidencia(a.asset_id)
        self.assertIsNone(e.documento.referencia_licencia)
        self.assertIsNone(e.documento.licencia_declarada)
        self.assertIsNone(self.catalogo.consultar_recurso(FUENTE_SENAMHI, c.producto_id, self.url).entidad.referencia_licencia)

    def test_url_solicitada_sin_consulta_ni_fragmento_en_persistencia(self):
        d, documento = self.declaracion_documento()
        url = self.url + "?token=SECRETO_SINTETICO_65"
        a = self.adaptador.adquirir_documentado(url, d, documento).activo
        e = self.almacen.consultar_evidencia(a.asset_id)
        self.assertEqual(e.url_solicitada, self.url)
        self.assertTrue(e.url_saneada)
        self.assertNotIn("SECRETO_SINTETICO_65", self.dump_raw())
        self.assertEqual(a.declaracion.recurso_id, " Recurso/01 ")

    def test_parametros_separados_tampoco_se_persisten(self):
        d, documento = self.declaracion_documento()
        a = self.adaptador.adquirir_documentado(self.url, d, documento,
            parametros={"token": "SECRETO_SINTETICO_65"}).activo
        self.assertTrue(self.almacen.consultar_evidencia(a.asset_id).url_saneada)
        self.assertNotIn("SECRETO_SINTETICO_65", self.dump_raw())

    def test_referencia_documental_sensible_rechazada_antes_del_http(self):
        d, documento = self.declaracion_documento()
        documento = replace(documento, referencia_publicacion="https://publicacion.invalid/?token=SECRETO_SINTETICO_65")
        with self.assertRaises(ErrorIntegracionHTTPRAW) as capturado:
            self.adaptador.adquirir_documentado(self.url, d, documento)
        self.assertNotIn("SECRETO_SINTETICO_65", str(capturado.exception))
        self.assertEqual(self.peticiones, [])
        self.assertEqual(self.almacen._catalogo.listar(), ())

    def test_evidencia_de_otro_recurso_o_producto_rechazada_antes_del_http(self):
        d, documento = self.declaracion_documento()
        for otro in (replace(documento, recurso_id="otro"), replace(documento, producto_id="otro"),
                     replace(documento, fuente=Fuente("otra", "institucion"))):
            with self.subTest(documento=otro), self.assertRaises(ErrorIntegracionHTTPRAW):
                self.adaptador.adquirir_documentado(self.url, d, otro)
        self.assertEqual(self.peticiones, [])
        self.assertEqual(self.almacen._catalogo.listar(), ())

    def test_documento_grande_rechazado_antes_del_http(self):
        d, documento = self.declaracion_documento()
        with self.assertRaises(ErrorIntegracionHTTPRAW):
            self.adaptador.adquirir_documentado(self.url, d, replace(documento, licencia_declarada="x" * 65_537))
        self.assertEqual(self.peticiones, [])

    def test_activo_antiguo_sin_evidencia_no_se_reconstruye(self):
        d, _ = self.declaracion_documento()
        a = self.adaptador.adquirir(self.url, d).activo
        self.assertIsNone(self.almacen.consultar_evidencia(a.asset_id))
        self.almacen.close()
        self.almacen = AlmacenRAW(self.raiz, (self.staging,))
        self.assertIsNone(self.almacen.consultar_evidencia(a.asset_id))

    def test_fallo_preparacion_no_deja_evidencia_huerfana(self):
        c = self.preparado()
        self.almacen._catalogo.conexion.execute("""CREATE TEMP TRIGGER fallo BEFORE INSERT ON activos
            BEGIN SELECT RAISE(ABORT,'token=SECRETO_SINTETICO_65'); END""")
        with self.assertRaises(ErrorIntegracionHTTPRAW) as capturado:
            self.adquirir(c)
        self.assertNotIn("SECRETO_SINTETICO_65", str(capturado.exception))
        self.assertEqual(self.almacen._catalogo.listar(), ())
        self.assertEqual(list(self.staging.iterdir()), [])
        self.assertNotIn("SECRETO_SINTETICO_65", self.dump_raw().split("CREATE TEMP")[0])

    def test_fallo_persistencia_final_no_confirma_y_conserva_original_previo(self):
        c = self.preparado()
        previo = self.adquirir(c).resultado_raw.activo
        real = self.almacen._catalogo.transicion
        def fallar(activo_id, estado, **datos):
            if estado is EstadoIncorporacion.INCORPORADA:
                raise sqlite3.OperationalError("token=SECRETO_SINTETICO_65")
            return real(activo_id, estado, **datos)
        with patch.object(self.almacen._catalogo, "transicion", fallar):
            with self.assertRaises(ErrorIntegracionHTTPRAW) as capturado:
                self.adquirir(c)
        fallido = capturado.exception.activo_id
        e = self.almacen.consultar_evidencia(fallido)
        self.assertEqual(e.estado_raw, EstadoIncorporacion.FALLIDA.value)
        self.assertNotIn("SECRETO_SINTETICO_65", self.dump_raw())
        self.assertIn(fallido, self.almacen.diagnosticar().incompletas)
        with self.assertRaises(ErrorAlmacenamientoRAW):
            self.almacen.recuperar(fallido)
        self.assertEqual(self.almacen.recuperar(previo.asset_id).read_bytes(), self.contenido)
        self.assertEqual(list(self.staging.iterdir()), [])

    def test_interrupcion_conserva_documento_sin_inventar_huella(self):
        c = self.preparado()
        with patch.object(self.almacen, "_copiar", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.adquirir(c)
        activo, = self.almacen._catalogo.listar()
        e = self.almacen.consultar_evidencia(activo.asset_id)
        self.assertEqual(e.estado_raw, EstadoIncorporacion.FALLIDA.value)
        self.assertIsNone(e.sha256)
        self.assertIsNone(e.size_bytes)
        self.assertEqual(list(self.staging.iterdir()), [])
        self.assertEqual(list(self.almacen.temporales.iterdir()), [])

    def test_fallo_registro_recurso_no_deja_revision_y_bloquea_adquisicion(self):
        c = self.conector()
        c.descubrir()
        self.catalogo._conexion.execute("""CREATE TEMP TRIGGER fallo BEFORE INSERT ON revisiones
            WHEN NEW.tabla='recursos' BEGIN SELECT RAISE(ABORT,'token=SECRETO_SINTETICO_65'); END""")
        with self.assertRaises(ErrorCatalogo) as capturado:
            c.registrar_catalogo(self.catalogo)
        self.assertNotIn("SECRETO_SINTETICO_65", str(capturado.exception))
        self.assertFalse(self.catalogo._conexion.in_transaction)
        self.assertEqual(self.catalogo.listar_recursos(FUENTE_SENAMHI, c.producto_id), ())
        with self.assertRaises(ErrorConectorPNDA):
            self.adquirir(c)
        self.catalogo._conexion.execute("DROP TRIGGER fallo")
        c.registrar_catalogo(self.catalogo)
        self.assertEqual(self.catalogo.consultar_producto(FUENTE_SENAMHI, c.producto_id).revision, 1)
        self.assertEqual(self.catalogo.consultar_recurso(FUENTE_SENAMHI, c.producto_id, self.url).revision, 1)

    def test_recurso_sin_producto_no_se_registra(self):
        p = self.manual()
        recurso = RecursoCatalogo(p.fuente, "producto-ausente", "recurso", self.url, p.procedencia)
        with self.assertRaises(ErrorCatalogo):
            self.catalogo.registrar_documental(recurso)
        self.assertEqual(self.catalogo._conexion.execute("SELECT count(*) FROM revisiones WHERE tabla='recursos'").fetchone()[0], 0)
        self.assertFalse(self.catalogo._conexion.in_transaction)

    def test_cambio_documental_sin_fecha_posterior_requiere_evaluacion(self):
        p = self.manual()
        r = self.catalogo.registrar_documental(replace(p, restricciones_licencia="licencia modificada"))
        self.assertEqual((r.estado, r.motivo), (EstadoRegistroDocumental.CONTRADICCION, "procedencia_no_posterior"))
        self.assertEqual(self.catalogo.historial(p)[0].entidad, p)
        self.assertEqual(len(self.catalogo.historial(p)), 1)

    def test_cambio_de_localizador_no_es_revision_documental_automatica(self):
        c = self.preparado()
        r = self.catalogo.consultar_recurso(FUENTE_SENAMHI, c.producto_id, self.url)
        nuevo = replace(r.entidad, localizador="https://recurso.invalid/otro",
            procedencia=replace(r.entidad.procedencia, revisada_utc=r.entidad.procedencia.revisada_utc + timedelta(days=1)))
        resultado = self.catalogo.registrar_documental(nuevo)
        self.assertEqual(resultado.estado, EstadoRegistroDocumental.CONTRADICCION)
        self.assertEqual(self.catalogo.consultar_recurso(FUENTE_SENAMHI, c.producto_id, self.url), r)

    def test_bases_cientificas_ajenas_o_incompletas_no_se_adoptan(self):
        for ajena in (False, True):
            ruta = self.base / ("ajena.sqlite3" if ajena else "incompleta.sqlite3")
            with closing(sqlite3.connect(ruta)) as db:
                db.execute("CREATE TABLE fuentes(incompleta TEXT)")
                db.execute("PRAGMA application_id=" + str(0 if ajena else 0x53554341))
                db.execute("PRAGMA user_version=1")
                db.commit()
            antes = ruta.read_bytes()
            with self.subTest(ajena=ajena), self.assertRaises(ErrorCatalogo):
                CatalogoCientifico(ruta)
            self.assertEqual(ruta.read_bytes(), antes)

    def test_no_cambia_ddl_ni_versiones_sqlite(self):
        conexiones = (self.catalogo._conexion, self.almacen._catalogo.conexion)
        def esquema(db):
            return (db.execute("PRAGMA user_version").fetchone()[0],
                    tuple(tuple(f) for f in db.execute("SELECT type,name,sql FROM sqlite_master ORDER BY name")))
        antes = [esquema(db) for db in conexiones]
        c = self.preparado()
        self.adquirir(c)
        self.assertEqual([esquema(db) for db in conexiones], antes)

    def test_evidencia_funciona_sobre_raw_v1_sin_migrar(self):
        from spica.adquisicion.almacenamiento.inspeccion import SQL_CREAR_V1
        raiz = self.base / "raw-v1"
        raiz.mkdir()
        ruta = raiz / "catalogo.sqlite3"
        with closing(sqlite3.connect(ruta)) as db:
            db.executescript(SQL_CREAR_V1)
            db.execute("PRAGMA user_version=1")
            db.commit()
        d, documento = self.declaracion_documento()
        with AlmacenRAW(raiz, (self.staging,), claves_parametros_publicos=("producto_id",)) as almacen:
            adaptador = AdaptadorHTTPRAW(self.cliente, almacen, self.staging, max_bytes=1_048_576)
            a = adaptador.adquirir_documentado(self.url, d, documento).activo
            self.assertEqual(almacen._catalogo.conexion.execute("PRAGMA user_version").fetchone()[0], 1)
        with AlmacenRAW(raiz, (self.staging,)) as almacen:
            e = almacen.consultar_evidencia(a.asset_id)
            self.assertEqual((e.sha256, e.size_bytes), (a.sha256, len(self.contenido)))
            self.assertEqual(almacen.recuperar(a.asset_id).read_bytes(), self.contenido)
            self.assertEqual(almacen._catalogo.conexion.execute("PRAGMA user_version").fetchone()[0], 1)

    def test_catalogo_legacy_institucional_conserva_revision_original(self):
        c = self.conector()
        c.descubrir()
        anterior = FuenteCatalogo(FUENTE_SENAMHI,
            ProcedenciaCatalogo(c.pagina, datetime(2020, 1, 1, tzinfo=timezone.utc), "GET_publico_HTML"),
            nombre="Servicio Nacional de Meteorología e Hidrología del Perú - SENAMHI",
            referencia_oficial=c.pagina, estado=EstadoVerificacion.DECLARADO)
        self.catalogo.registrar(anterior)
        c.registrar_catalogo(self.catalogo)
        self.assertEqual(self.catalogo.consultar_revision(anterior, 1).entidad, anterior)
        actual = self.catalogo.consultar_fuente(FUENTE_SENAMHI)
        self.assertEqual(actual.revision, 2)
        self.assertEqual(actual.entidad.procedencia.referencia, "urn:spica:fuente:SENAMHI")
        self.assertIsNone(actual.entidad.referencia_oficial)

    def test_planificador_no_infiere_cobertura_del_recurso_verificado(self):
        from spica.adquisicion.nucleo import SolicitudAdquisicion
        from spica.adquisicion.planificacion import ConsultaProducto, SolicitudCientifica, Planificador, EstadoPreparacion
        c = self.preparado()
        self.adquirir(c)
        fecha = datetime(2020, 1, 1, tzinfo=timezone.utc)
        consulta = ConsultaProducto(SolicitudAdquisicion(FUENTE_SENAMHI, fecha, fecha), c.producto_id)
        peticiones = len(self.peticiones)
        plan = Planificador(self.catalogo).planificar(SolicitudCientifica("prueba-65", (consulta,)))
        self.assertFalse(plan.ejecutable)
        self.assertEqual(plan.operaciones[0].estado, EstadoPreparacion.CONDICIONADA)
        self.assertEqual(len(self.peticiones), peticiones)
        self.assertTrue(all(r.entidad.estado is EstadoVerificacion.DECLARADO
                            for r in self.catalogo.listar(CapacidadCatalogo)))

    def test_evidencia_no_sustituye_verificacion_fisica_actual(self):
        c = self.preparado()
        resultado = self.adquirir(c).resultado_raw
        e = self.almacen.consultar_evidencia(resultado.activo.asset_id)
        resultado.ruta_verificada.write_bytes(b"corrupcion sintetica")
        self.assertEqual(self.almacen.consultar_evidencia(e.activo_id), e)
        with self.assertRaises(ErrorAlmacenamientoRAW):
            self.almacen.recuperar(e.activo_id)
        self.assertEqual(self.almacen.consultar_evidencia(e.activo_id).estado_raw, EstadoIncorporacion.INCONSISTENTE.value)

    def test_nueva_lectura_raw_no_reescribe_fecha_http(self):
        c = self.preparado()
        a = self.adquirir(c).resultado_raw.activo
        e = self.almacen.consultar_evidencia(a.asset_id)
        self.almacen.recuperar(a.asset_id)
        posterior = self.almacen.consultar_evidencia(a.asset_id)
        self.assertEqual(posterior.http_comprobada_utc, e.http_comprobada_utc)
        self.assertEqual(posterior.documento, e.documento)
        self.assertGreater(self.almacen.metadatos(a.asset_id).comprobacion_utc, e.http_comprobada_utc)

    def test_archivo_vacio_tiene_evidencia_fisica_legitima(self):
        self.contenido = b""
        c = self.preparado()
        a = self.adquirir(c).resultado_raw.activo
        e = self.almacen.consultar_evidencia(a.asset_id)
        self.assertEqual((e.sha256, e.size_bytes), (hashlib.sha256(b"").hexdigest(), 0))
        self.assertEqual(e.estado_raw, EstadoIncorporacion.INCORPORADA.value)

    def test_sin_registro_previo_revision_desconocida_y_documento_persistido(self):
        c = self.conector()
        c.descubrir()
        a = self.adquirir(c).resultado_raw.activo
        e = self.almacen.consultar_evidencia(a.asset_id)
        self.assertIsNone(e.documento.revision_documental)
        self.assertEqual(e.documento.referencia_publicacion, c.pagina)
        self.assertEqual(e.documento.referencia_licencia, self.licencia)

    def test_paquete_incompatible_no_se_presenta_como_evidencia_valida(self):
        import json
        c = self.preparado()
        a = self.adquirir(c).resultado_raw.activo
        db = self.almacen._catalogo.conexion
        datos = json.loads(db.execute("SELECT declaracion FROM activos WHERE id=?", (a.asset_id,)).fetchone()[0])
        datos["_evidencia_adquisicion"]["version"] = 99
        with db:
            db.execute("UPDATE activos SET declaracion=? WHERE id=?", (json.dumps(datos), a.asset_id))
        with self.assertRaises(ErrorAlmacenamientoRAW) as capturado:
            self.almacen.consultar_evidencia(a.asset_id)
        self.assertEqual(capturado.exception.codigo, "evidencia_persistida_invalida")

    def test_sha256_no_es_identidad_de_producto_recurso_o_adquisicion(self):
        c = self.preparado()
        a = self.adquirir(c).resultado_raw.activo
        self.contenido += b"version fisica sintetica distinta\n"
        b = self.adquirir(c).resultado_raw.activo
        ea, eb = (self.almacen.consultar_evidencia(r.asset_id) for r in (a, b))
        self.assertEqual((ea.documento.producto_id, ea.documento.recurso_id),
                         (eb.documento.producto_id, eb.documento.recurso_id))
        self.assertNotEqual(ea.sha256, eb.sha256)
        self.assertNotEqual(ea.adquisicion_id, eb.adquisicion_id)

    def test_fragmentos_y_credenciales_siguen_rechazados_sin_http(self):
        d, documento = self.declaracion_documento()
        for url in (self.url + "#SECRETO_SINTETICO_65",
                    self.url.replace("https://", "https://usuario:SECRETO_SINTETICO_65@")):
            with self.subTest(url=url), self.assertRaises(ErrorIntegracionHTTPRAW) as capturado:
                self.adaptador.adquirir_documentado(url, d, documento)
            self.assertNotIn("SECRETO_SINTETICO_65", str(capturado.exception))
        self.assertEqual(self.peticiones, [])
        self.assertEqual(self.almacen._catalogo.listar(), ())

    def test_encabezados_no_se_conservan_en_evidencia(self):
        original = self.responder
        def responder(peticion):
            respuesta = original(peticion)
            respuesta.headers["Set-Cookie"] = "token=SECRETO_SINTETICO_65"
            respuesta.headers["X-Diagnostico"] = "SECRETO_SINTETICO_65"
            return respuesta
        with ClienteHTTP((ORIGEN_PNDA,), transporte=httpx.MockTransport(responder)) as cliente:
            adaptador = AdaptadorHTTPRAW(cliente, self.almacen, self.staging, max_bytes=1_048_576)
            d, documento = self.declaracion_documento()
            a = adaptador.adquirir_documentado(self.url, d, documento).activo
        self.assertEqual(self.almacen.consultar_evidencia(a.asset_id).url_solicitada, self.url)
        self.assertNotIn("SECRETO_SINTETICO_65", self.dump_raw())

    def test_campos_documentales_y_http_recuperables_con_estados_separados(self):
        c = self.preparado()
        a = self.adquirir(c).resultado_raw.activo
        e = self.almacen.consultar_evidencia(a.asset_id)
        documento = e.documento
        self.assertEqual(documento.fuente, FUENTE_SENAMHI)
        self.assertEqual((documento.producto_id, documento.recurso_id), (c.producto_id, self.url))
        self.assertEqual(documento.referencia_publicacion, c.pagina)
        self.assertEqual(documento.procedencia.referencia, c.pagina)
        self.assertEqual(documento.descubierta_utc, c._descubierto.recursos[0].procedencia.revisada_utc)
        self.assertEqual((documento.revision_fuente, documento.revision_producto, documento.revision_documental), (1, 1, 1))
        self.assertEqual(documento.estado, EstadoVerificacion.DECLARADO)
        self.assertEqual(documento.capacidades_documentadas, (MecanismoAdquisicion.HTTP_DIRECTO,))
        self.assertEqual(e.capacidades_http_verificadas, (MecanismoAdquisicion.HTTP_DIRECTO,))
        self.assertGreaterEqual(e.http_comprobada_utc, documento.descubierta_utc)
        self.assertEqual(e.http_comprobada_utc.utcoffset(), timedelta(0))

    def test_adquirir_documentado_exige_documento(self):
        d, _ = self.declaracion_documento()
        with self.assertRaises(ErrorIntegracionHTTPRAW):
            self.adaptador.adquirir_documentado(self.url, d, None)
        self.assertEqual(self.peticiones, [])


if __name__ == "__main__":
    unittest.main()
