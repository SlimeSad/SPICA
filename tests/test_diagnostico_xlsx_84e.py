"""Seguridad del diagnóstico aislado: solo libros ficticios y temporales."""

from io import BytesIO
import hashlib
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from uuid import uuid4
from zipfile import ZipFile, ZIP_STORED

from herramientas import inspeccionar_xlsx_84e as d
from test_verificacion_formatos import partes_xlsx, empaquetar, MAIN, OFFICE, REL


def libro(celdas, *, extras=None):
    p = partes_xlsx()
    p["xl/worksheets/sheet1.xml"] = (f'<worksheet xmlns="{MAIN}"><dimension ref="A1:F8"/>'
        '<sheetData><row r="1">' + celdas + '</row></sheetData></worksheet>').encode()
    p.update(extras or {})
    return empaquetar(p, ZIP_STORED)


class DiagnosticoXLSXTests(unittest.TestCase):
    def test_textos_compartidos_y_rich_text_conservan_ceros_y_espacios(self):
        ss = (f'<sst xmlns="{MAIN}"><si><t xml:space="preserve"> 00123 </t></si>'
              '<si><r><t>texto </t></r><r><t>literal</t></r><rPh><t>no-unir</t></rPh></si></sst>').encode()
        r = d.inspeccionar_bytes(libro('<c r="A1" t="s"><v>0</v></c><c r="B1" t="s"><v>1</v></c>',
                                     extras={"xl/sharedStrings.xml": ss}))
        cs = r["hojas"][0]["celdas"]
        self.assertEqual([c["literal"] for c in cs], [" 00123 ", "texto literal"])
        self.assertEqual(cs[0]["valor_almacenado"], "0")
        self.assertEqual(r["cadenas_compartidas"], 2)

    def test_numeros_codigos_estilos_y_fechas_no_se_convierten(self):
        styles = (f'<styleSheet xmlns="{MAIN}"><numFmts count="1"><numFmt numFmtId="164" formatCode="000000"/></numFmts>'
                  '<cellXfs count="1"><xf numFmtId="164"/></cellXfs></styleSheet>').encode()
        r = d.inspeccionar_bytes(libro('<c r="A1" s="0"><v>00123</v></c>'
            '<c r="B1" t="d"><v>2026-01-01</v></c><c r="C1" t="b"><v>0</v></c>',
            extras={"xl/styles.xml":styles}))
        cs = r["hojas"][0]["celdas"]
        self.assertEqual([c["literal"] for c in cs], ["00123","2026-01-01","0"])
        self.assertEqual(cs[0]["formato_personalizado"], "000000")
        self.assertEqual(cs[0]["numfmt_id"], "164")

    def test_formula_y_cache_no_se_promueven_a_definicion_oficial(self):
        r = d.inspeccionar_bytes(libro('<c r="A1" t="str"><f>1+1</f><v>resultado-en-cache</v></c>'
            '<c r="B1" t="inlineStr"><is><t>=texto literal</t></is></c><c r="C1" t="e"><v>#N/A</v></c>'))
        cs = r["hojas"][0]["celdas"]
        self.assertEqual(r["formulas"], 1)
        self.assertIsNone(cs[0]["literal"])
        self.assertEqual(cs[0]["valor_almacenado"], "resultado-en-cache")
        self.assertEqual(cs[0]["formula_texto"], "1+1")
        self.assertEqual(cs[1]["literal"], "=texto literal")
        self.assertEqual(cs[2]["literal"], "#N/A")

    def test_referencias_externas_no_se_abren_ni_publican_sus_destinos(self):
        rel = (f'<Relationships xmlns="{REL}"><Relationship Id="externa" Type="{OFFICE}/hyperlink" '
               'Target="https://prohibido.invalid/?token=SECRETO_FICTICIO" TargetMode="External"/></Relationships>').encode()
        with patch("socket.socket", side_effect=AssertionError("red")):
            r = d.inspeccionar_bytes(libro('<c r="A1"><v>0</v></c>',
                extras={"xl/worksheets/_rels/sheet1.xml.rels":rel}))
        self.assertEqual(len(r["relaciones_externas_no_abiertas"]), 1)
        self.assertNotIn("SECRETO_FICTICIO", str(r))

    def test_xml_dtd_entidades_y_profundidad_rechazados(self):
        base = partes_xlsx()
        for xml in (b'<!DOCTYPE worksheet [<!ENTITY dato "texto">]><worksheet/>',
                    b'<worksheet>' + b'<a>'*40 + b'</a>'*40 + b'</worksheet>', b'<worksheet>'):
            with self.subTest(xml=xml[:30]):
                p = dict(base); p["xl/worksheets/sheet1.xml"] = xml
                with self.assertRaises(d.ErrorDiagnostico):
                    d.inspeccionar_bytes(empaquetar(p,ZIP_STORED))

    def test_zip_rutas_cifrado_macros_y_crc_se_rechazan(self):
        variantes = []
        for nombre in ("../fuera.xml", "xl/vbaProject.bin"):
            p = partes_xlsx(); p[nombre] = b"contenido-ficticio"
            variantes.append(empaquetar(p,ZIP_STORED))
        raw = bytearray(empaquetar(partes_xlsx(),ZIP_STORED))
        pos = raw.index(b'<worksheet')
        raw[pos + 1] ^= 1
        variantes.append(bytes(raw))
        raw = bytearray(empaquetar(partes_xlsx(),ZIP_STORED))
        raw[6] |= 1  # Cifrado en cabecera local y directorio.
        central = raw.index(b'PK\x01\x02'); raw[central + 8] |= 1
        variantes.append(bytes(raw))
        for datos in variantes:
            with self.subTest(bytes=len(datos)), self.assertRaises(d.ErrorDiagnostico):
                d.inspeccionar_bytes(datos)

    def test_limites_de_directorio_expansion_y_tamano(self):
        p = partes_xlsx()
        p.update({f"extra{i}.xml":b"<a/>" for i in range(65)})
        expansion = partes_xlsx(); expansion["xl/worksheets/sheet1.xml"] = b" "*100_000
        for datos in (empaquetar(p,ZIP_STORED),empaquetar(expansion),b"x"*(d.MAX_ARCHIVO+1)):
            with self.subTest(bytes=len(datos)), self.assertRaises(d.ErrorDiagnostico):
                d.inspeccionar_bytes(datos)

    def test_indices_y_referencias_ambiguas_no_se_reparan(self):
        for cells in ('<c r="A1" t="s"><v>0</v></c>', '<c r="A1"/><c r="A1"/>',
                      '<c r="A1" s="99"/>','<c t="inlineStr"><is><t>texto</t></is></c>'):
            with self.subTest(cells=cells), self.assertRaises(d.ErrorDiagnostico):
                d.inspeccionar_bytes(libro(cells))

    def test_limites_del_inventario_y_deadline_son_efectivos(self):
        datos = libro('<c r="A1" t="inlineStr"><is><t>texto-largo</t></is></c><c r="B1"/>')
        for nombre, valor in (("MAX_CELDAS",1),("MAX_TEXTO",3),("MAX_TEXTO_TOTAL",3)):
            with self.subTest(nombre=nombre),patch.object(d,nombre,valor),self.assertRaises(d.ErrorDiagnostico):
                d.inspeccionar_bytes(datos)
        with patch.object(d.time,"monotonic",side_effect=[0,6]), self.assertRaisesRegex(d.ErrorDiagnostico,"plazo"):
            d.inspeccionar_bytes(datos)

    def test_metadatos_personales_no_se_publican(self):
        core = b'<coreProperties><creator>PERSONA_FICTICIA</creator><created>2020-01-01</created><revision>7</revision></coreProperties>'
        r = d.inspeccionar_bytes(libro('<c r="A1"/>', extras={"docProps/core.xml":core}))
        self.assertNotIn("PERSONA_FICTICIA", str(r))
        self.assertTrue(r["propiedades"]["docProps/core.xml"]["creator_presente_sin_publicar"])
        self.assertEqual(r["propiedades"]["docProps/core.xml"]["created"], "2020-01-01")

    def test_diagnostico_bytes_no_escribe_archivos_sqlite_o_red(self):
        datos = libro('<c r="A1" t="inlineStr"><is><t>literal</t></is></c>')
        with patch("builtins.open",side_effect=AssertionError("archivo")), \
             patch("sqlite3.connect",side_effect=AssertionError("sqlite")), \
             patch("socket.socket",side_effect=AssertionError("red")):
            self.assertEqual(d.inspeccionar_bytes(datos)["hojas"][0]["celdas"][0]["literal"],"literal")

    def test_archivo_identidad_incorrecta_y_conservacion_en_error(self):
        base = Path(tempfile.gettempdir()).resolve() / ("spica-84e-test-"+uuid4().hex)
        base.mkdir(mode=0o755)
        def limpiar():
            assert base.resolve().parent==Path(tempfile.gettempdir()).resolve()
            shutil.rmtree(base)
        self.addCleanup(limpiar)
        ruta = base / "ficticio.xlsx"
        datos = b"no-es-zip-ficticio"; ruta.write_bytes(datos)
        digest = hashlib.sha256(datos).hexdigest()
        with self.assertRaisesRegex(d.ErrorDiagnostico,"integridad_previa"):
            d.inspeccionar_archivo(ruta,tamano_esperado=len(datos),sha256_esperado="0"*64)
        with self.assertRaises(d.ErrorDiagnostico):
            d.inspeccionar_archivo(ruta,tamano_esperado=len(datos),sha256_esperado=digest)
        self.assertEqual(ruta.read_bytes(),datos)


if __name__ == "__main__":
    unittest.main()
