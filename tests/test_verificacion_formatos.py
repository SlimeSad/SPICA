"""SUADC-05: formatos y ataques sintéticos, sin red ni almacenamiento operativo."""

from io import BytesIO
from pathlib import Path
import shutil
import struct
import sys
import tempfile
import tracemalloc
import unittest
from unittest.mock import patch
from uuid import uuid4
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile, ZipInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from spica.adquisicion.verificacion import EstadoEstructura, PoliticaEstructura, verificar_archivo

CT = "http://schemas.openxmlformats.org/package/2006/content-types"
REL = "http://schemas.openxmlformats.org/package/2006/relationships"
MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
OFFICE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def partes_xlsx():
    return {
        "[Content_Types].xml": (f'<Types xmlns="{CT}"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>').encode(),
        "_rels/.rels": f'<Relationships xmlns="{REL}"><Relationship Id="rId1" Type="{OFFICE}/officeDocument" Target="xl/workbook.xml"/></Relationships>'.encode(),
        "xl/workbook.xml": f'<workbook xmlns="{MAIN}" xmlns:r="{OFFICE}"><sheets><sheet name="Hoja sintetica" sheetId="1" r:id="rId1"/></sheets></workbook>'.encode(),
        "xl/_rels/workbook.xml.rels": f'<Relationships xmlns="{REL}"><Relationship Id="rId1" Type="{OFFICE}/worksheet" Target="worksheets/sheet1.xml"/></Relationships>'.encode(),
        "xl/worksheets/sheet1.xml": f'<worksheet xmlns="{MAIN}"><sheetData><row r="1"><c r="A1"><v>1</v></c></row></sheetData></worksheet>'.encode(),
    }


def empaquetar(partes, compresion=ZIP_DEFLATED):
    memoria = BytesIO()
    with ZipFile(memoria, "w", compression=compresion) as z:
        for nombre, datos in partes.items():
            z.writestr(nombre, datos)
    return memoria.getvalue()


def xlsx_sintetico():
    return empaquetar(partes_xlsx())


class FormatosTests(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.gettempdir()).resolve() / ("spica-formatos-" + uuid4().hex)
        self.base.mkdir(mode=0o755)
        self.addCleanup(self.limpiar)
        self.ruta = self.base / "archivo.bin"

    def limpiar(self):
        assert self.base.resolve().parent == Path(tempfile.gettempdir()).resolve()
        assert self.base.name.startswith("spica-formatos-")
        shutil.rmtree(self.base)

    def inspeccionar(self, datos, declarado="xlsx", **opciones):
        self.ruta.write_bytes(datos)
        antes = self.ruta.read_bytes()
        resultado = verificar_archivo(self.ruta, formato_declarado=declarado, **opciones)
        self.assertEqual(self.ruta.read_bytes(), antes)
        return resultado

    def test_xlsx_minimo_reconocido_con_alcance_explicito(self):
        r = self.inspeccionar(xlsx_sintetico())
        self.assertEqual(r.estado, EstadoEstructura.COMPATIBLE)
        self.assertEqual(r.formato_identificado, "xlsx")
        self.assertTrue(r.utilizable_documentalmente)
        self.assertIn("zip_lectura_completa_crc_y_tamanos", r.comprobaciones)
        self.assertIn("xlsx_content_types_libro_relaciones_y_hojas", r.comprobaciones)
        self.assertGreater(r.bytes_descomprimidos, 0)

    def test_zip_corrupto(self):
        r = self.inspeccionar(b"PK\x03\x04invalido")
        self.assertEqual(r.estado, EstadoEstructura.ILEGIBLE_O_CORRUPTA)
        self.assertFalse(r.utilizable_documentalmente)

    def test_zip_truncado(self):
        r = self.inspeccionar(xlsx_sintetico()[:-15])
        self.assertEqual(r.estado, EstadoEstructura.ILEGIBLE_O_CORRUPTA)

    def test_crc_zip_incorrecto(self):
        datos = bytearray(empaquetar({"contenido.bin": b"contenido sintetico"}, ZIP_STORED))
        nombre, extra = struct.unpack_from("<HH", datos, 26)
        datos[30 + nombre + extra] ^= 1
        r = self.inspeccionar(datos)
        self.assertEqual(r.estado, EstadoEstructura.ILEGIBLE_O_CORRUPTA)
        self.assertIn("zip_corrupto_o_crc_no_coincidente", r.diagnosticos)

    def test_html_como_xlsx(self):
        r = self.inspeccionar(b"<!DOCTYPE html><html><body>Error sintetico</body></html>")
        self.assertEqual((r.estado, r.formato_identificado), (EstadoEstructura.INCOMPATIBLE, "html"))

    def test_json_como_xlsx(self):
        r = self.inspeccionar(b'{"error":"sintetico"}')
        self.assertEqual((r.estado, r.formato_identificado), (EstadoEstructura.INCOMPATIBLE, "json"))

    def test_docx_como_xlsx(self):
        partes = {
            "[Content_Types].xml": f'<Types xmlns="{CT}"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>'.encode(),
            "_rels/.rels": f'<Relationships xmlns="{REL}"><Relationship Id="r" Type="{OFFICE}/officeDocument" Target="word/document.xml"/></Relationships>'.encode(),
            "word/document.xml": b'<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body/></w:document>',
        }
        r = self.inspeccionar(empaquetar(partes))
        self.assertEqual((r.estado, r.formato_identificado), (EstadoEstructura.INCOMPATIBLE, "docx"))

    def test_zip_generico_no_es_xlsx(self):
        r = self.inspeccionar(empaquetar({"nota.txt": b"contenido sintetico"}))
        self.assertEqual((r.estado, r.formato_identificado), (EstadoEstructura.INCOMPATIBLE, "zip"))

    def test_binario_arbitrario_no_reconocido(self):
        r = self.inspeccionar(b"\x00\x01\x02\x03\xff\xfe")
        self.assertNotEqual(r.estado, EstadoEstructura.COMPATIBLE)
        self.assertIsNone(r.formato_identificado)

    def test_limite_entradas_antes_del_constructor_zipfile(self):
        datos = empaquetar({str(n): b"a" for n in range(4)})
        with patch("spica.adquisicion.verificacion._xlsx.ZipFile") as abrir:
            r = self.inspeccionar(datos, politica=PoliticaEstructura(max_entradas_zip=3))
        abrir.assert_not_called()
        self.assertEqual(r.estado, EstadoEstructura.INCOMPLETA)

    def test_contador_falsificado_no_elude_limite_entradas(self):
        datos = bytearray(empaquetar({str(n): b"a" for n in range(4)}))
        fin = datos.rfind(b"PK\x05\x06")
        struct.pack_into("<HH", datos, fin + 8, 0, 0)
        with patch("spica.adquisicion.verificacion._xlsx.ZipFile") as abrir:
            r = self.inspeccionar(datos, politica=PoliticaEstructura(max_entradas_zip=3))
        abrir.assert_not_called()
        self.assertEqual(r.estado, EstadoEstructura.INCOMPLETA)
        self.assertIn("limite_entradas_reales_zip", r.diagnosticos)

    def test_limite_directorio_central(self):
        r = self.inspeccionar(xlsx_sintetico(), politica=PoliticaEstructura(max_central_zip=30))
        self.assertEqual(r.estado, EstadoEstructura.INCOMPLETA)

    def test_expansion_excesiva(self):
        r = self.inspeccionar(empaquetar({"carga.bin": b"0" * 65_536}), politica=PoliticaEstructura(max_expansion=5))
        self.assertEqual(r.estado, EstadoEstructura.INCOMPLETA)
        self.assertEqual(r.bytes_descomprimidos, 0)

    def test_limites_descomprimidos_por_entrada_y_total(self):
        datos = empaquetar({"uno.bin": b"x" * 100, "dos.bin": b"y" * 100}, ZIP_STORED)
        for p in (PoliticaEstructura(max_bytes_entrada=50), PoliticaEstructura(max_bytes_descomprimidos=150)):
            with self.subTest(politica=p):
                self.assertEqual(self.inspeccionar(datos, politica=p).estado, EstadoEstructura.INCOMPLETA)

    def test_rutas_zip_sospechosas_no_se_extraen(self):
        for nombre in ("../escape.txt", "/absoluta.txt", "C:/escape.txt", "xl\\escape.txt", "%2e%2e/escape.txt"):
            with self.subTest(nombre=nombre):
                nombre_zip = nombre.replace("\\", "/")
                datos = empaquetar({nombre_zip: b"contenido sintetico"})
                # ZipInfo normaliza separadores Windows al escribir. Alterar
                # ambos nombres serializados para probar bytes realmente hostiles.
                if nombre_zip != nombre:
                    datos = datos.replace(nombre_zip.encode(), nombre.encode())
                r = self.inspeccionar(datos)
                self.assertEqual(r.estado, EstadoEstructura.ILEGIBLE_O_CORRUPTA)
                self.assertEqual({p.name for p in self.base.iterdir()}, {"archivo.bin"})

    def test_entrada_symlink_rechazada(self):
        entrada = ZipInfo("enlace")
        entrada.create_system = 3
        entrada.external_attr = 0o120777 << 16
        r = self.inspeccionar(empaquetar({entrada: b"destino-sintetico"}))
        self.assertEqual(r.estado, EstadoEstructura.ILEGIBLE_O_CORRUPTA)

    def test_componentes_xlsx_ausentes(self):
        for nombre in ("[Content_Types].xml", "xl/workbook.xml", "xl/_rels/workbook.xml.rels", "xl/worksheets/sheet1.xml"):
            partes = partes_xlsx()
            partes.pop(nombre)
            with self.subTest(componente=nombre):
                self.assertFalse(self.inspeccionar(empaquetar(partes)).utilizable_documentalmente)

    def test_relacion_de_hoja_rota(self):
        partes = partes_xlsx()
        partes["xl/workbook.xml"] = partes["xl/workbook.xml"].replace(b'r:id="rId1"', b'r:id="ausente"')
        r = self.inspeccionar(empaquetar(partes))
        self.assertEqual(r.estado, EstadoEstructura.ILEGIBLE_O_CORRUPTA)

    def test_hoja_con_raiz_incorrecta(self):
        partes = partes_xlsx()
        partes["xl/worksheets/sheet1.xml"] = b"<html/>"
        self.assertFalse(self.inspeccionar(empaquetar(partes)).utilizable_documentalmente)

    def test_xml_truncado(self):
        partes = partes_xlsx()
        partes["xl/workbook.xml"] = partes["xl/workbook.xml"][:-10]
        self.assertEqual(self.inspeccionar(empaquetar(partes)).estado, EstadoEstructura.ILEGIBLE_O_CORRUPTA)

    def test_dtd_y_entidades_rechazados_tambien_en_utf16(self):
        for codec in ("utf-8", "utf-16"):
            partes = partes_xlsx()
            xml = '<!DOCTYPE workbook [<!ENTITY secreto SYSTEM "https://prohibido.invalid/SECRETO_66">]>'
            xml += f'<workbook xmlns="{MAIN}">&secreto;</workbook>'
            partes["xl/workbook.xml"] = xml.encode(codec)
            with self.subTest(codec=codec), patch("socket.socket.connect", side_effect=AssertionError("Red prohibida")):
                r = self.inspeccionar(empaquetar(partes))
            self.assertEqual(r.estado, EstadoEstructura.ILEGIBLE_O_CORRUPTA)
            self.assertIn("xml_dtd_o_entidades_no_admitidos", r.diagnosticos)
            self.assertNotIn("SECRETO_66", repr(r))

    def test_limites_xml(self):
        for p in (PoliticaEstructura(max_bytes_xml=30), PoliticaEstructura(max_nodos_xml=3),
                  PoliticaEstructura(max_profundidad_xml=2)):
            with self.subTest(politica=p):
                self.assertEqual(self.inspeccionar(xlsx_sintetico(), politica=p).estado, EstadoEstructura.INCOMPLETA)

    def test_relacion_interna_escapa_del_paquete(self):
        partes = partes_xlsx()
        partes["xl/_rels/workbook.xml.rels"] = partes["xl/_rels/workbook.xml.rels"].replace(b"worksheets/sheet1.xml", b"../../fuera.xml")
        self.assertEqual(self.inspeccionar(empaquetar(partes)).estado, EstadoEstructura.ILEGIBLE_O_CORRUPTA)

    def test_relacion_externa_no_se_abre(self):
        partes = partes_xlsx()
        partes["xl/_rels/workbook.xml.rels"] = partes["xl/_rels/workbook.xml.rels"].replace(b"</Relationships>",
            f'<Relationship Id="externa" Type="{OFFICE}/hyperlink" Target="https://prohibido.invalid/?token=SECRETO_66" TargetMode="External"/></Relationships>'.encode())
        with patch("socket.socket.connect", side_effect=AssertionError("Red prohibida")):
            r = self.inspeccionar(empaquetar(partes))
        self.assertTrue(r.utilizable_documentalmente)
        self.assertNotIn("SECRETO_66", repr(r))
        self.assertIn("relaciones_externas_no_abiertas", r.diagnosticos)

    def test_formulas_no_se_ejecutan(self):
        partes = partes_xlsx()
        partes["xl/worksheets/sheet1.xml"] = f'<worksheet xmlns="{MAIN}"><sheetData><row><c><f>HYPERLINK("https://prohibido.invalid")</f><v>0</v></c></row></sheetData></worksheet>'.encode()
        with patch("socket.socket.connect", side_effect=AssertionError("Red prohibida")):
            self.assertTrue(self.inspeccionar(empaquetar(partes)).utilizable_documentalmente)

    def test_csv_sencillo_con_encabezado_explicito(self):
        r = self.inspeccionar(b"nombre,valor\nuno,1\ndos,2\n", "csv", encabezado_declarado=True)
        self.assertEqual((r.estado, r.csv.delimitador, r.csv.codificacion), (EstadoEstructura.COMPATIBLE, ",", "ascii"))
        self.assertEqual((r.csv.encabezado_declarado, r.csv.campos_primera_fila, r.csv.registros_examinados), (True, 2, 3))

    def test_csv_delimitadores_sin_predeterminar_coma(self):
        for delimitador in (";", "\t", "|"):
            with self.subTest(delimitador=delimitador):
                r = self.inspeccionar(("a" + delimitador + "b\n1" + delimitador + "2\n").encode(), "csv")
                self.assertTrue(r.utilizable_documentalmente)
                self.assertEqual(r.csv.delimitador, delimitador)
                self.assertIsNone(r.csv.encabezado_declarado)

    def test_csv_bom_utf8_utf16_utf32(self):
        for codec in ("utf-8-sig", "utf-16", "utf-32"):
            with self.subTest(codec=codec):
                r = self.inspeccionar("estación;valor\nprueba;1\n".encode(codec), "csv")
                self.assertTrue(r.utilizable_documentalmente)
                self.assertIsNotNone(r.csv.bom)

    def test_csv_codificacion_desconocida(self):
        r = self.inspeccionar("estación;valor\nprueba;1\n".encode("cp1252"), "csv")
        self.assertEqual(r.estado, EstadoEstructura.INCIERTA)
        self.assertIsNone(r.formato_identificado)

    def test_csv_utf8_sin_bom_no_se_supone_confirmado(self):
        r = self.inspeccionar("estación;valor\nprueba;1\n".encode("utf-8"), "csv")
        self.assertEqual(r.estado, EstadoEstructura.INCIERTA)
        self.assertEqual(r.csv.codificacion, "utf-8")

    def test_csv_codificacion_explicita(self):
        r = self.inspeccionar("estación;valor\nprueba;1\n".encode("cp1252"), "csv", codificacion="cp1252")
        self.assertTrue(r.utilizable_documentalmente)

    def test_csv_comillas_escapes_y_saltos_dentro_de_campos(self):
        datos = b'nombre,nota\r\n"uno, dos","dijo ""hola"""\r\n"tres\ncuatro",fin\r\n'
        r = self.inspeccionar(datos, "csv")
        self.assertTrue(r.utilizable_documentalmente)
        self.assertEqual(r.csv.registros_examinados, 3)

    def test_csv_lf_crlf_y_sin_salto_final(self):
        for datos in (b"a,b\n1,2\n", b"a,b\r\n1,2\r\n", b"a,b\n1,2"):
            with self.subTest(datos=datos):
                self.assertTrue(self.inspeccionar(datos, "csv").utilizable_documentalmente)

    def test_csv_vacio_incierto(self):
        r = self.inspeccionar(b"", "csv")
        self.assertEqual(r.estado, EstadoEstructura.INCIERTA)
        self.assertFalse(r.utilizable_documentalmente)

    def test_csv_registros_malformados(self):
        for datos in (b'a,b\n"sin cierre,1', b"a,b\n1,2,3\n", b'a,b\n"valor"x,2\n', b'a,b\n1,comilla"literal\n'):
            with self.subTest(datos=datos):
                self.assertEqual(self.inspeccionar(datos, "csv").estado, EstadoEstructura.ILEGIBLE_O_CORRUPTA)

    def test_csv_bytes_nulos(self):
        r = self.inspeccionar(b"a,b\n1,\x002\n", "csv")
        self.assertEqual(r.estado, EstadoEstructura.NO_RECONOCIDA)

    def test_html_y_json_como_csv(self):
        for datos, formato in ((b"<html><body>Error</body></html>", "html"), (b'{"error":1}', "json")):
            with self.subTest(formato=formato):
                r = self.inspeccionar(datos, "csv")
                self.assertEqual((r.estado, r.formato_identificado), (EstadoEstructura.INCOMPATIBLE, formato))

    def test_csv_delimitador_ambiguo(self):
        r = self.inspeccionar(b"a,b;c\n1,2;3\n", "csv")
        self.assertEqual(r.estado, EstadoEstructura.INCIERTA)
        self.assertIsNone(r.csv.delimitador)
        self.assertTrue(self.inspeccionar(b"a,b;c\n1,2;3\n", "csv", delimitador=";").utilizable_documentalmente)

    def test_csv_un_registro_o_columna_unica_son_inciertos(self):
        for datos in (b"a,b\n", b"a\nb\nc\n"):
            with self.subTest(datos=datos):
                self.assertEqual(self.inspeccionar(datos, "csv").estado, EstadoEstructura.INCIERTA)

    def test_csv_muestra_cortada_en_comilla_no_se_declara_corrupta(self):
        r = self.inspeccionar(b'a,b\n"campo largo multilinea\ncontinua",2\n', "csv",
                              politica=PoliticaEstructura(max_muestra_csv=15))
        self.assertEqual(r.estado, EstadoEstructura.INCOMPLETA)
        self.assertFalse(r.alcance_completo)

    def test_csv_limites_registros_campos_y_longitud(self):
        casos = ((b"a,b\n1,2\n3,4\n", PoliticaEstructura(max_registros_csv=2)),
                 (b"a,b,c\n1,2,3\n", PoliticaEstructura(max_campos_csv=2)),
                 (b"abcd,efgh\nijkl,mnop\n", PoliticaEstructura(max_campo_csv=3)))
        for datos, p in casos:
            with self.subTest(politica=p):
                self.assertEqual(self.inspeccionar(datos, "csv", politica=p).estado, EstadoEstructura.INCOMPLETA)

    def test_separacion_de_declaracion_sugerencias_e_identificacion(self):
        r = self.inspeccionar(xlsx_sintetico(), "XLSX", nombre_sugerido="https://sintetico.invalid/archivo.csv?token=SECRETO_66",
                              tipo_medio_sugerido="application/json; token=SECRETO_66")
        self.assertEqual((r.formato_declarado, r.sugerido_extension, r.sugerido_http, r.formato_identificado), ("XLSX", "csv", "json", "xlsx"))
        self.assertNotIn("SECRETO_66", repr(r))
        self.assertTrue(r.utilizable_documentalmente)

    def test_archivo_sin_declaracion_no_inventa_compatibilidad(self):
        r = self.inspeccionar(xlsx_sintetico(), None)
        self.assertEqual(r.estado, EstadoEstructura.SIN_DECLARACION)
        self.assertEqual(r.formato_identificado, "xlsx")
        self.assertFalse(r.utilizable_documentalmente)

    def test_reconocer_otro_formato_no_amplia_la_usabilidad_del_piloto(self):
        r = self.inspeccionar(b'{"sintetico":1}', "json")
        self.assertEqual((r.estado, r.formato_identificado), (EstadoEstructura.COMPATIBLE, "json"))
        self.assertFalse(r.utilizable_documentalmente)

    def test_csv_bom_incompatible_con_codificacion_explicita(self):
        r = self.inspeccionar("a,b\n1,2\n".encode("utf-16"), "csv", codificacion="cp1252")
        self.assertEqual(r.estado, EstadoEstructura.INCIERTA)
        self.assertIn("bom_y_codificacion_declarada_incompatibles", r.diagnosticos)

    def test_archivo_ilegible_no_filtra_excepcion(self):
        self.ruta.write_bytes(b"a,b\n1,2\n")
        with patch.object(Path, "open", side_effect=PermissionError("token=SECRETO_66")):
            r = verificar_archivo(self.ruta, formato_declarado="csv")
        self.assertEqual(r.estado, EstadoEstructura.ILEGIBLE_O_CORRUPTA)
        self.assertNotIn("SECRETO_66", repr(r))

    def test_csv_grande_memoria_y_lectura_acotadas(self):
        with self.ruta.open("wb") as archivo:
            for _ in range(128):
                archivo.write(b"uno,dos\n" * 4096)
        tracemalloc.start()
        try:
            with patch.object(Path, "read_bytes", side_effect=AssertionError("Lectura completa prohibida")):
                r = verificar_archivo(self.ruta, formato_declarado="csv")
            _, pico = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
        self.assertEqual(r.estado, EstadoEstructura.INCOMPLETA)
        self.assertLessEqual(r.bytes_leidos, r.politica.max_muestra_csv + 5)
        self.assertLess(pico, 8 * 1024**2)

    def test_hoja_xml_grande_se_lee_por_bloques_sin_arbol_de_datos(self):
        partes = partes_xlsx()
        partes.pop("xl/worksheets/sheet1.xml")
        with ZipFile(self.ruta, "w", compression=ZIP_STORED) as z:
            for nombre, contenido in partes.items():
                z.writestr(nombre, contenido)
            with z.open("xl/worksheets/sheet1.xml", "w") as hoja:
                hoja.write(f'<worksheet xmlns="{MAIN}"><sheetData><row><c><is><t>'.encode())
                for _ in range(64):
                    hoja.write(b"texto sintetico " * 2048)
                hoja.write(b"</t></is></c></row></sheetData></worksheet>")
        tracemalloc.start()
        try:
            r = verificar_archivo(self.ruta, formato_declarado="xlsx")
            _, pico = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
        self.assertTrue(r.utilizable_documentalmente)
        self.assertGreater(r.bytes_descomprimidos, 2_000_000)
        self.assertLess(pico, 8 * 1024**2)

    def test_token_xml_gigante_se_detiene_sin_acumular_la_entrada(self):
        partes = partes_xlsx()
        partes["xl/worksheets/sheet1.xml"] = (f'<worksheet xmlns="{MAIN}" dato="'.encode()
            + b"x" * 300_000 + b'"/>')
        r = self.inspeccionar(empaquetar(partes, ZIP_STORED))
        self.assertEqual(r.estado, EstadoEstructura.INCOMPLETA)
        self.assertIn("limite_xml_pendiente_de_analisis", r.diagnosticos)
        self.assertLess(r.bytes_descomprimidos, 200_000)

    def test_alias_de_entradas_zip_no_se_aceptan(self):
        r = self.inspeccionar(empaquetar({"xl/uno.xml": b"<uno/>", "XL/UNO.XML": b"<dos/>"}))
        self.assertEqual(r.estado, EstadoEstructura.ILEGIBLE_O_CORRUPTA)

    def test_macros_no_se_admiten_como_xlsx(self):
        partes = partes_xlsx()
        partes["xl/vbaProject.bin"] = b"macro sintetica inerte"
        partes["[Content_Types].xml"] = partes["[Content_Types].xml"].replace(
            b"</Types>", b'<Default Extension="bin" ContentType="application/vnd.ms-office.vbaProject"/></Types>')
        r = self.inspeccionar(empaquetar(partes))
        self.assertEqual(r.estado, EstadoEstructura.NO_RECONOCIDA)
        self.assertFalse(r.utilizable_documentalmente)
