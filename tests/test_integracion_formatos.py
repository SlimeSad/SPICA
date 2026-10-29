"""Formato, procedencia e integridad independientes con MockTransport."""

import hashlib
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from spica.adquisicion.almacenamiento import AlmacenRAW, DeclaracionRAW, EstadoIncorporacion
from spica.adquisicion.catalogo import EstadoVerificacion, EvidenciaDocumental
from spica.adquisicion.integracion import AdaptadorHTTPRAW
from spica.adquisicion.nucleo import Fuente
from spica.adquisicion.verificacion import EstadoEstructura, PoliticaEstructura, verificar_archivo
import test_registro_evidencias as fixtures
from test_verificacion_formatos import xlsx_sintetico


class IntegracionFormatosTests(unittest.TestCase):
    # Reutiliza solo la preparación/limpieza sintética; no hereda sus tests.
    setUp = fixtures.RegistroEvidenciasTests.setUp
    limpiar = fixtures.RegistroEvidenciasTests.limpiar
    conector = fixtures.RegistroEvidenciasTests.conector
    preparado = fixtures.RegistroEvidenciasTests.preparado
    adquirir = fixtures.RegistroEvidenciasTests.adquirir
    dump_raw = fixtures.RegistroEvidenciasTests.dump_raw

    def responder(self, peticion):
        respuesta = fixtures.RegistroEvidenciasTests.responder(self, peticion)
        if not peticion.url.path.startswith("/dataset/") and getattr(self, "tipo_http", None):
            respuesta.headers["Content-Type"] = self.tipo_http
        return respuesta

    def test_pnda_xlsx_utilizable_con_integridad_y_evidencia(self):
        self.contenido = xlsx_sintetico()
        c = self.preparado()
        r = self.adquirir(c)
        self.assertEqual(r.estructura.estado, EstadoEstructura.COMPATIBLE)
        self.assertTrue(r.utilizable_documentalmente)
        self.assertIsNone(r.validacion_cientifica)
        raw = r.resultado_raw
        e = self.almacen.consultar_evidencia(raw.activo.asset_id)
        self.assertEqual((e.sha256, e.size_bytes), (hashlib.sha256(self.contenido).hexdigest(), len(self.contenido)))
        self.assertEqual((e.documento.recurso_id, e.documento.producto_id), (self.url, c.producto_id))
        self.assertEqual(e.documento.referencia_licencia, self.licencia)
        self.assertEqual(raw.ruta_verificada.read_bytes(), self.contenido)

    def test_pnda_html_conservado_sin_confirmar_xlsx(self):
        self.contenido = b"<html><body>Error sintetico</body></html>"
        self.tipo_http = "text/html; token=SECRETO_66"
        r = self.adquirir(self.preparado())
        self.assertEqual((r.estructura.estado, r.estructura.formato_identificado), (EstadoEstructura.INCOMPATIBLE, "html"))
        self.assertEqual((r.estructura.sugerido_extension, r.estructura.sugerido_http), ("xlsx", "html"))
        self.assertFalse(r.utilizable_documentalmente)
        self.assertEqual(r.resultado_raw.activo.estado, EstadoIncorporacion.INCORPORADA)
        self.assertIsNone(r.resultado_raw.activo.media_detected)
        self.assertEqual(r.resultado_raw.ruta_verificada.read_bytes(), self.contenido)
        self.assertNotIn("SECRETO_66", repr(r))
        self.assertNotIn("SECRETO_66", self.dump_raw())
        self.assertEqual(r.capacidad_recurso.estado, EstadoVerificacion.VERIFICADO)  # Solo HTTP.
        self.assertIn("estructura=reconocida_incompatible", r.capacidad_recurso.procedencia.evidencia)
        self.assertIsNone(r.validacion_cientifica)

    def test_pnda_json_conservado_con_procedencia(self):
        self.contenido = b'{"error":"respuesta sintetica"}'
        self.tipo_http = "application/json"
        r = self.adquirir(self.preparado())
        self.assertFalse(r.utilizable_documentalmente)
        self.assertEqual(r.estructura.formato_identificado, "json")
        e = self.almacen.consultar_evidencia(r.resultado_raw.activo.asset_id)
        self.assertEqual(e.documento.referencia_publicacion, r.recurso.referencia_publicacion)
        self.assertEqual(e.url_solicitada, self.url)
        self.assertEqual(list(self.staging.iterdir()), [])

    def test_zip_truncado_conserva_evidencia_fisica_sin_usabilidad(self):
        self.contenido = xlsx_sintetico()[:-20]
        r = self.adquirir(self.preparado())
        self.assertEqual(r.estructura.estado, EstadoEstructura.ILEGIBLE_O_CORRUPTA)
        self.assertFalse(r.utilizable_documentalmente)
        self.assertEqual(self.almacen.recuperar(r.resultado_raw.activo.asset_id).read_bytes(), self.contenido)

    def test_limites_estructura_independientes_del_limite_http(self):
        self.contenido = xlsx_sintetico()
        self.adaptador = AdaptadorHTTPRAW(self.cliente, self.almacen, self.staging, max_bytes=1_048_576,
            politica_estructura=PoliticaEstructura(max_entradas_zip=1))
        r = self.adquirir(self.preparado())
        self.assertEqual(r.estructura.estado, EstadoEstructura.INCOMPLETA)
        self.assertFalse(r.utilizable_documentalmente)
        self.assertEqual(r.resultado_raw.activo.size_bytes, len(self.contenido))

    def test_csv_sintetico_mediante_adaptador_comun(self):
        self.contenido = b"columna_1;columna_2\nprueba;1\n"
        self.tipo_http = "text/csv"
        d = DeclaracionRAW("p", "o", Fuente("sintetica", "fuente"), "recurso-csv", formato_declarado="csv")
        documento = EvidenciaDocumental(d.fuente, d.recurso_id)
        r = self.adaptador.adquirir_documentado(self.url, d, documento)
        self.assertTrue(r.utilizable_documentalmente)
        self.assertEqual(r.estructura.csv.delimitador, ";")
        self.assertEqual(r.estructura.sugerido_http, "csv")
        self.assertEqual(r.activo.declaracion.recurso_id, d.recurso_id)

    def test_csv_vacio_integridad_correcta_estructura_incierta(self):
        self.contenido = b""
        d = DeclaracionRAW("p", "o", Fuente("sintetica", "fuente"), "recurso", formato_declarado="csv")
        r = self.adaptador.adquirir(self.url, d)
        self.assertEqual(r.activo.sha256, hashlib.sha256(b"").hexdigest())
        self.assertEqual(r.estructura.estado, EstadoEstructura.INCIERTA)
        self.assertFalse(r.utilizable_documentalmente)

    def test_originales_duplicados_no_se_modifican_por_inspeccion(self):
        self.contenido = xlsx_sintetico()
        c = self.preparado()
        a, b = (self.adquirir(c) for _ in range(2))
        self.assertNotEqual(a.resultado_raw.activo.asset_id, b.resultado_raw.activo.asset_id)
        self.assertEqual(a.resultado_raw.ruta_verificada, b.resultado_raw.ruta_verificada)
        self.assertTrue(a.utilizable_documentalmente and b.utilizable_documentalmente)
        self.assertEqual(a.resultado_raw.ruta_verificada.read_bytes(), self.contenido)

    def test_reapertura_conserva_documento_y_permite_reinspeccion(self):
        self.contenido = xlsx_sintetico()
        r = self.adquirir(self.preparado())
        activo_id = r.resultado_raw.activo.asset_id
        e = self.almacen.consultar_evidencia(activo_id)
        self.almacen.close()
        self.almacen = AlmacenRAW(self.raiz, (self.staging,))
        self.assertEqual(self.almacen.consultar_evidencia(activo_id), e)
        self.assertIsNone(self.almacen.metadatos(activo_id).media_detected)
        resultado = verificar_archivo(self.almacen.recuperar(activo_id), formato_declarado="xlsx")
        self.assertTrue(resultado.utilizable_documentalmente)

    def test_mime_erroneo_no_sustituye_comprobacion_fisica(self):
        self.contenido = xlsx_sintetico()
        self.tipo_http = "application/json"
        r = self.adquirir(self.preparado())
        self.assertEqual((r.estructura.sugerido_http, r.estructura.formato_identificado), ("json", "xlsx"))
        self.assertTrue(r.utilizable_documentalmente)
        self.assertIn("sugerencia_http_no_coincidente", r.estructura.diagnosticos)

    def test_encabezado_arbitrario_se_descarta(self):
        self.contenido = xlsx_sintetico()
        self.tipo_http = "application/token-SECRETO_66"
        r = self.adquirir(self.preparado())
        self.assertIsNone(r.resultado_raw.informe_http.tipo_medio_sugerido)
        self.assertNotIn("SECRETO_66", repr(r))
