"""Piloto sin conexiones reales: HTML y XLSX exclusivamente sintéticos."""

import hashlib
from io import BytesIO
from pathlib import Path
import shutil
import sys
import unittest
from uuid import uuid4
from zipfile import ZipFile

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from spica.adquisicion.almacenamiento import AlmacenRAW, EstadoIncorporacion
from spica.adquisicion.catalogo import CatalogoCientifico, EstadoVerificacion, CapacidadCatalogo
from spica.adquisicion.integracion import AdaptadorHTTPRAW, ErrorIntegracionHTTPRAW
from spica.adquisicion.transportes import ClienteHTTP, ConfiguracionHTTP
from spica.adquisicion.conectores.senamhi import (
    ConectorSENAMHIPNDA, PAGINA_GBON_RBON, PRODUCTO_GBON_RBON_ID, ORIGEN_PNDA, FUENTE_SENAMHI,
    RolRecurso, ErrorConectorPNDA,
)
from test_transporte_http import Flujo


def distribucion(nombre, href):
    return ('<li><div property="dcat:Distribution"><a class="heading" title="' + nombre
            + '">Nombre sintetico</a><span><a class="btn data-link" href="' + href
            + '">Descargar</a></span></div></li>')


class ConectorSENAMHIPNDATests(unittest.TestCase):
    def setUp(self):
        proyecto = Path(__file__).resolve().parents[1]
        self.base = proyecto / (".suadc-test-" + uuid4().hex)
        self.base.mkdir(mode=0o755)
        assert self.base.resolve().is_relative_to(proyecto)
        self.addCleanup(shutil.rmtree, self.base)
        self.staging = self.base / "staging"
        self.staging.mkdir()
        self.raiz_raw = self.base / "raw"
        self.raiz_raw.mkdir()
        self.almacen = AlmacenRAW(self.raiz_raw, (self.staging,), max_bytes=1_048_576,
                                  claves_parametros_publicos=("producto_id",))
        self.addCleanup(self.almacen.close)
        self.catalogo = CatalogoCientifico(self.base / "descubrimiento.sqlite3")
        self.addCleanup(self.catalogo.close)
        self.url_xlsx = ORIGEN_PNDA + "/sites/default/files/Diccionario_sintetico.xlsx"
        self.html = ('<html><div class="pane-dkan-sitewide-dkan-sitewide-license">'
                     '<a href="https://opendatacommons.org/licenses/by/1-0/">Licencia declarada</a></div>'
                     + distribucion("Diccionario sintetico", self.url_xlsx)
                     + distribucion("Datos sinteticos", "/sites/default/files/datos.csv")
                     + distribucion("Metadatos sinteticos", "/sites/default/files/metadatos.docx")
                     + '<footer><a class="data-link" href="/sites/default/files/pie.pdf">Pie</a></footer></html>')
        archivo = BytesIO()
        with ZipFile(archivo, "w") as z:
            z.writestr("[Content_Types].xml", '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>')
            z.writestr("xl/workbook.xml", '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"/>')
        self.xlsx = archivo.getvalue()
        self.codigo = 200
        self.cabeceras = {}
        self.error = None
        self.codigo_pagina = 200
        self.tipo_pagina = "text/html; charset=utf-8"
        self.peticiones, self.flujos = [], []

    def conector(self, *, origenes=(ORIGEN_PNDA,), config=None, max_bytes=1_048_576, max_recursos=100):
        def handler(request):
            self.peticiones.append(request)
            if str(request.url) == PAGINA_GBON_RBON:
                return httpx.Response(self.codigo_pagina, headers={"Content-Type": self.tipo_pagina},
                                      stream=Flujo((self.html.encode(),)))
            flujo = Flujo((self.xlsx[:50], self.xlsx[50:]), self.error)
            self.flujos.append(flujo)
            return httpx.Response(self.codigo, headers=self.cabeceras, stream=flujo)
        cliente = ClienteHTTP(origenes, config, transporte=httpx.MockTransport(handler))
        self.addCleanup(cliente.close)
        adaptador = AdaptadorHTTPRAW(cliente, self.almacen, self.staging, max_bytes=max_bytes)
        return ConectorSENAMHIPNDA(cliente, adaptador, max_recursos=max_recursos)

    def adquirir(self, conector):
        conector.descubrir()
        return conector.adquirir(self.url_xlsx, proyecto_id="proyecto-sintetico", objeto_id="objeto-sintetico")

    def test_identificacion_fuente_producto_recurso(self):
        datos = self.conector().descubrir()
        self.assertEqual(datos.producto.fuente, FUENTE_SENAMHI)
        self.assertEqual(datos.producto.identificador, PRODUCTO_GBON_RBON_ID)
        self.assertNotEqual(datos.recursos[0].recurso.identificador, datos.producto.identificador)
        self.assertEqual(datos.recursos[0].rol, RolRecurso.DICCIONARIO)

    def test_recursos_y_formatos_sin_enlaces_de_pie(self):
        datos = self.conector().descubrir()
        self.assertEqual(tuple(r.recurso.formato for r in datos.recursos), ("xlsx", "csv", "docx"))
        self.assertEqual(len(datos.recursos), 3)

    def test_registro_catalogo_sin_inventar_observaciones(self):
        c = self.conector()
        datos = c.descubrir()
        registros = c.registrar_catalogo(self.catalogo)
        self.assertEqual(len(registros), 3)
        self.assertEqual(registros[-1].entidad.estado, EstadoVerificacion.DECLARADO)
        self.assertIsNone(datos.producto.autenticacion_requerida)
        self.assertIsNone(datos.producto.utiliza_estaciones)

    def test_adquisicion_xlsx_y_continuidad_fisica(self):
        self.cabeceras = {"Content-Length": str(len(self.xlsx))}
        resultado = self.adquirir(self.conector())
        raw = resultado.resultado_raw
        self.assertEqual(raw.ruta_verificada.read_bytes(), self.xlsx)
        with raw.ruta_verificada.open("rb") as f:
            hash_real = hashlib.file_digest(f, "sha256").hexdigest()
        self.assertEqual(raw.activo.sha256, hash_real)
        self.assertEqual(raw.informe_http.sha256, hash_real)
        self.assertEqual(raw.activo.size_bytes, len(self.xlsx))
        self.assertEqual(raw.activo.estado, EstadoIncorporacion.INCORPORADA)
        self.assertIsNone(resultado.validacion_cientifica)
        self.assertEqual(list(self.staging.iterdir()), [])
        self.assertTrue(all(f.cerrado for f in self.flujos))

    def test_capacidad_verificada_solo_del_recurso(self):
        c = self.conector()
        resultado = self.adquirir(c)
        c.registrar_catalogo(self.catalogo)
        self.assertEqual(resultado.capacidad_recurso.estado, EstadoVerificacion.VERIFICADO)
        self.assertEqual(resultado.capacidad_recurso.identificador, self.url_xlsx)
        capacidades = self.catalogo.listar(CapacidadCatalogo)
        self.assertEqual(capacidades[0].entidad.estado, EstadoVerificacion.DECLARADO)
        self.assertIsNotNone(resultado.capacidad_recurso.comprobada_utc)

    def test_duplicados_enlaces_se_registran_una_vez(self):
        self.html += distribucion("Diccionario repetido", self.url_xlsx)
        datos = self.conector().descubrir()
        self.assertEqual(len(datos.recursos), 3)
        self.assertIn("enlace_duplicado_en_publicacion", datos.advertencias)

    def test_duplicados_conservan_adquisiciones_y_original(self):
        c = self.conector()
        c.descubrir()
        a = c.adquirir(self.url_xlsx, proyecto_id="p", objeto_id="o")
        b = c.adquirir(self.url_xlsx, proyecto_id="p", objeto_id="o")
        self.assertNotEqual(a.resultado_raw.activo.asset_id, b.resultado_raw.activo.asset_id)
        self.assertEqual(a.resultado_raw.ruta_verificada, b.resultado_raw.ruta_verificada)
        self.assertEqual(a.resultado_raw.ruta_verificada.read_bytes(), self.xlsx)

    def test_origen_no_autorizado_no_envia_peticion(self):
        c = self.conector(origenes=("https://sintetico.invalid",))
        with self.assertRaises(ValueError):
            c.descubrir()
        self.assertEqual(self.peticiones, [])

    def test_enlace_externo_no_se_autoriza_por_aparecer_en_html(self):
        self.html += distribucion("Diccionario externo", "https://sintetico.invalid/archivo.xlsx")
        c = self.conector()
        datos = c.descubrir()
        self.assertEqual(len(datos.recursos), 3)
        with self.assertRaises(ErrorConectorPNDA):
            c.adquirir("https://sintetico.invalid/archivo.xlsx", proyecto_id="p", objeto_id="o")
        self.assertEqual(len(self.peticiones), 1)

    def test_redireccion_no_se_sigue(self):
        self.codigo = 302
        self.cabeceras = {"Location": "https://sintetico.invalid/archivo"}
        with self.assertRaises(ErrorIntegracionHTTPRAW):
            self.adquirir(self.conector())
        self.assertEqual(len(self.peticiones), 2)
        self.assertEqual(list(self.staging.iterdir()), [])

    def test_estados_http_incorrectos_sin_reintento(self):
        for codigo in (401, 403, 404, 429, 500, 503, 206):
            with self.subTest(codigo=codigo):
                self.codigo = codigo
                anteriores = len(self.peticiones)
                with self.assertRaises(ErrorIntegracionHTTPRAW):
                    self.adquirir(self.conector())
                self.assertEqual(len(self.peticiones) - anteriores, 2)
        self.assertEqual(self.almacen._catalogo.listar(), ())

    def test_interrupcion_descarta_temporal(self):
        self.error = httpx.ReadError("secreto-sintetico-no-publicable")
        with self.assertRaises(ErrorIntegracionHTTPRAW) as error:
            self.adquirir(self.conector())
        self.assertNotIn("secreto-sintetico", str(error.exception))
        self.assertEqual(list(self.staging.iterdir()), [])
        self.assertEqual(self.almacen._catalogo.listar(), ())

    def test_metadatos_incompletos_no_se_inventan(self):
        self.html = distribucion("", self.url_xlsx)
        c = self.conector()
        datos = c.descubrir()
        self.assertIsNone(datos.producto.restricciones_licencia)
        self.assertIsNone(datos.recursos[0].titulo)
        self.assertEqual(datos.recursos[0].rol, RolRecurso.PUBLICADO)
        with self.assertRaises(ErrorConectorPNDA):
            c.adquirir(self.url_xlsx, proyecto_id="p", objeto_id="o")

    def test_procedencia_identidades_y_licencia(self):
        r = self.adquirir(self.conector())
        d = r.resultado_raw.activo.declaracion
        self.assertEqual(d.procedencia, self.url_xlsx)
        self.assertEqual(d.parametros_publicos["producto_id"], PRODUCTO_GBON_RBON_ID)
        self.assertEqual(d.recurso_id, self.url_xlsx)
        self.assertEqual(r.recurso.referencia_publicacion, PAGINA_GBON_RBON)
        self.assertIsNotNone(r.recurso.procedencia.revisada_utc.utcoffset())

    def test_rechaza_credenciales_en_enlaces_sin_exponer(self):
        self.html += distribucion("Diccionario sensible", self.url_xlsx + "?token=secreto-sintetico")
        datos = self.conector().descubrir()
        self.assertEqual(len(datos.recursos), 3)
        self.assertNotIn("secreto-sintetico", repr(datos))

    def test_rechaza_titulo_sensible(self):
        self.html = distribucion("password=secreto-sintetico", self.url_xlsx)
        with self.assertRaises(ErrorConectorPNDA) as error:
            self.conector().descubrir()
        self.assertNotIn("secreto-sintetico", str(error.exception))

    def test_sin_filtros_remotos_y_sin_solicitudes_adicionales(self):
        c = self.conector()
        self.assertFalse(c.descubrir().filtros_remotos_verificados)
        with self.assertRaises(TypeError):
            c.adquirir(self.url_xlsx, proyecto_id="p", objeto_id="o", estaciones=("falsa",))
        self.assertEqual(len(self.peticiones), 1)

    def test_csv_y_docx_no_autorizados_para_este_piloto(self):
        c = self.conector()
        datos = c.descubrir()
        for recurso in datos.recursos[1:]:
            with self.assertRaises(ErrorConectorPNDA):
                c.adquirir(recurso.recurso.identificador, proyecto_id="p", objeto_id="o")
        self.assertEqual(len(self.peticiones), 1)

    def test_formato_adicional_se_descubre_sin_whitelist(self):
        self.html += distribucion("Recurso adicional sintetico", "/sites/default/files/recurso.nc")
        datos = self.conector().descubrir()
        self.assertEqual(datos.recursos[-1].recurso.formato, "nc")

    def test_limite_tamano_en_transferencia(self):
        with self.assertRaises(ErrorIntegracionHTTPRAW):
            self.adquirir(self.conector(max_bytes=10))
        self.assertEqual(list(self.staging.iterdir()), [])

    def test_content_length_incorrecto(self):
        self.cabeceras = {"Content-Length": str(len(self.xlsx) + 1)}
        with self.assertRaises(ErrorIntegracionHTTPRAW):
            self.adquirir(self.conector())
        self.assertEqual(self.almacen._catalogo.listar(), ())

    def test_compresion_http_rechazada(self):
        self.cabeceras = {"Content-Encoding": "gzip"}
        with self.assertRaises(ErrorIntegracionHTTPRAW):
            self.adquirir(self.conector())

    def test_timeout_sin_reintentos(self):
        self.error = httpx.ReadTimeout("timeout sintetico")
        with self.assertRaises(ErrorIntegracionHTTPRAW):
            self.adquirir(self.conector())
        self.assertEqual(len(self.peticiones), 2)

    def test_no_adquiere_antes_del_descubrimiento(self):
        with self.assertRaises(ErrorConectorPNDA):
            self.conector().adquirir(self.url_xlsx, proyecto_id="p", objeto_id="o")
        self.assertEqual(self.peticiones, [])

    def test_cambio_html_falla_cerrado_y_revoca_descubrimiento(self):
        c = self.conector()
        c.descubrir()
        self.html = "<html>Pagina sin distribuciones reconocibles</html>"
        with self.assertRaises(ErrorConectorPNDA):
            c.descubrir()
        with self.assertRaises(ErrorConectorPNDA):
            c.adquirir(self.url_xlsx, proyecto_id="p", objeto_id="o")

    def test_limite_distribuciones(self):
        with self.assertRaises(ErrorConectorPNDA):
            self.conector(max_recursos=1).descubrir()

    def test_registro_idempotente_misma_evidencia(self):
        c = self.conector()
        c.descubrir()
        a = c.registrar_catalogo(self.catalogo)
        b = c.registrar_catalogo(self.catalogo)
        self.assertEqual(a, b)

    def test_almacen_sin_clave_producto_rechazado(self):
        c = self.conector()
        self.almacen.claves = frozenset()
        with self.assertRaises(ErrorConectorPNDA):
            ConectorSENAMHIPNDA(c.cliente, c.adaptador)

    def test_limite_piloto_y_tls_obligatorios(self):
        cliente = ClienteHTTP((ORIGEN_PNDA,), ConfiguracionHTTP(verificar_tls=False),
                              transporte=httpx.MockTransport(lambda r: httpx.Response(200)))
        self.addCleanup(cliente.close)
        with self.assertRaises(ErrorConectorPNDA):
            ConectorSENAMHIPNDA(cliente)
        with self.assertRaises(ErrorConectorPNDA):
            self.conector(max_bytes=2 * 1_048_576)

    def test_referencia_producto_ajena_rechazada(self):
        c = self.conector()
        with self.assertRaises(ErrorConectorPNDA):
            ConectorSENAMHIPNDA(c.cliente, pagina_producto="https://sintetico.invalid/dataset/x")

    def test_respuesta_pagina_no_html_rechazada(self):
        self.tipo_pagina = "application/json"
        with self.assertRaises(ErrorConectorPNDA):
            self.conector().descubrir()

    def test_registro_previo_descubrimiento_requerido(self):
        with self.assertRaises(ErrorConectorPNDA):
            self.conector().registrar_catalogo(self.catalogo)

    def test_adaptador_de_otro_cliente_rechazado(self):
        a, b = self.conector(), self.conector()
        with self.assertRaises(ErrorConectorPNDA):
            ConectorSENAMHIPNDA(a.cliente, b.adaptador)

    def test_identidad_producto_original_sin_normalizar(self):
        c = self.conector()
        otro = ConectorSENAMHIPNDA(c.cliente, pagina_producto=ORIGEN_PNDA + "/dataset/Producto-%C3%81")
        self.assertEqual(otro.producto_id, "Producto-%C3%81")

    def test_registro_licencia_declarada_no_inferida(self):
        c = self.conector()
        datos = c.descubrir()
        self.assertEqual(datos.producto.restricciones_licencia, "https://opendatacommons.org/licenses/by/1-0/")
        c.registrar_catalogo(self.catalogo)
        self.assertEqual(self.catalogo.consultar_producto(FUENTE_SENAMHI, PRODUCTO_GBON_RBON_ID).entidad,
                         datos.producto)

    def test_no_ejecuta_planificador_ni_infiere_fechas(self):
        c = self.conector()
        c.descubrir()
        c.registrar_catalogo(self.catalogo)
        from spica.adquisicion.nucleo import SolicitudAdquisicion
        from spica.adquisicion.planificacion import ConsultaProducto, SolicitudCientifica, Planificador, EstadoPreparacion
        from datetime import datetime, timezone
        fecha = datetime(2020, 1, 1, tzinfo=timezone.utc)
        consulta = ConsultaProducto(SolicitudAdquisicion(FUENTE_SENAMHI, fecha, fecha), PRODUCTO_GBON_RBON_ID)
        plan = Planificador(self.catalogo).planificar(SolicitudCientifica("prueba-sintetica", (consulta,)))
        self.assertFalse(plan.ejecutable)
        self.assertEqual(plan.operaciones[0].estado, EstadoPreparacion.CONDICIONADA)
        self.assertEqual(len(self.peticiones), 1)


if __name__ == "__main__":
    unittest.main()
