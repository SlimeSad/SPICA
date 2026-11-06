"""DOCX sintéticos adversariales; sin documentos reales, Word o conexiones."""

from dataclasses import FrozenInstanceError, replace
from io import BytesIO
import binascii
import hashlib
from pathlib import Path
import shutil
import stat
import struct
import sys
import tempfile
from threading import Event
import tracemalloc
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from uuid import uuid4
from xml.etree import ElementTree as ET
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED, ZIP_STORED

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from spica.adquisicion.verificacion.docx import (
    EstadoInspeccionDOCX as E, LimitesDOCX, inspeccionar_docx_archivo, inspeccionar_docx_bytes,
)
from spica.adquisicion.verificacion.docx import inspector as api
from spica.adquisicion.verificacion.docx import _paquete as paquete
from spica.adquisicion.verificacion.docx._extraccion import Q, W, R
from test_verificacion_formatos import CT, REL, OFFICE


def parrafo(texto="Texto sintetico"):
    return f'<w:p><w:r><w:t xml:space="preserve">{texto}</w:t></w:r></w:p>'


def partes(cuerpo=None):
    return {
        "[Content_Types].xml": (f'<Types xmlns="{CT}"><Default Extension="rels" '
            'ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/word/document.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>').encode(),
        "_rels/.rels": (f'<Relationships xmlns="{REL}"><Relationship Id="rPrincipal" '
            f'Type="{OFFICE}/officeDocument" Target="word/document.xml"/></Relationships>').encode(),
        "word/document.xml": (f'<w:document xmlns:w="{W}" xmlns:r="{R}"><w:body>'
            + (parrafo() if cuerpo is None else cuerpo) + '</w:body></w:document>').encode(),
    }


def agregar(p, nombre, datos, mime, clase, *, raiz=False):
    p[nombre] = datos.encode() if isinstance(datos, str) else datos
    p["[Content_Types].xml"] = p["[Content_Types].xml"].replace(b'</Types>',
        f'<Override PartName="/{nombre}" ContentType="{mime}"/></Types>'.encode())
    rel = "_rels/.rels" if raiz else "word/_rels/document.xml.rels"
    if rel not in p: p[rel] = f'<Relationships xmlns="{REL}"></Relationships>'.encode()
    rid = "rExtra" + str(len(p))
    destino = nombre if raiz else nombre.removeprefix("word/")
    tipo = clase if "://" in clase else OFFICE + "/" + clase
    p[rel] = p[rel].replace(b'</Relationships>',
        f'<Relationship Id="{rid}" Type="{tipo}" Target="{destino}"/></Relationships>'.encode())
    return rid


def zip_docx(p=None, *, compresion=ZIP_STORED, enlace=None):
    salida = BytesIO()
    with ZipFile(salida, "w") as z:
        for nombre, contenido in (partes() if p is None else p).items():
            i = ZipInfo(nombre, date_time=(2020, 1, 1, 0, 0, 0))
            i.compress_type = compresion
            i.create_system = 3
            i.external_attr = ((stat.S_IFLNK if nombre == enlace else stat.S_IFREG) | 0o600) << 16
            z.writestr(i, contenido)
    return salida.getvalue()


class InspectorDOCXTests(unittest.TestCase):
    def inspeccionar(self, p=None, **kw):
        return inspeccionar_docx_bytes(zip_docx(p), **kw)

    def test_docx_valido_identidad_partes_y_texto(self):
        datos = zip_docx()
        r = inspeccionar_docx_bytes(datos, identificador="sintetico-1")
        self.assertIs(r.estado, E.DOCUMENTO_VALIDADO_EN_ALCANCE)
        self.assertEqual((r.identidad.tamano, r.identidad.sha256), (len(datos), hashlib.sha256(datos).hexdigest()))
        self.assertEqual([p.texto for p in r.parrafos], ["Texto sintetico"])
        self.assertEqual(len(r.partes), 3)
        self.assertTrue(all(p.bytes_observados == p.bytes_declarados for p in r.partes))
        self.assertIsNone(r.conservacion_comprobada)  # No se abrió ningún archivo físico.

    def test_sin_tablas_y_body_vacio_son_alcances_distintos(self):
        self.assertEqual(self.inspeccionar().tablas, ())
        r = self.inspeccionar(partes(""))
        self.assertIs(r.estado, E.DOCUMENTO_VALIDADO_EN_ALCANCE)
        self.assertEqual(r.parrafos, ())
        self.assertIn("sin_parrafos_extraidos_en_alcance", [d.codigo for d in r.advertencias])

    def test_archivo_y_paquete_vacios_no_son_docx(self):
        for datos in (b"", zip_docx({})):
            with self.subTest(datos=len(datos)):
                self.assertIs(inspeccionar_docx_bytes(datos).estado, E.DOCUMENTO_RECHAZADO)

    def test_runs_espacios_ceros_y_saltos_se_conservan(self):
        p = partes('<w:p><w:r><w:t xml:space="preserve"> 00123 </w:t><w:tab/></w:r>'
            '<w:r><w:t>texto</w:t><w:br/><w:t>final</w:t><w:cr/></w:r></w:p>')
        self.assertEqual(self.inspeccionar(p).parrafos[0].texto, " 00123 \ttexto\nfinal\n")

    def test_tabuladores_de_formato_no_inventan_texto(self):
        formato = '<w:pPr><w:tabs><w:tab w:val="left" w:pos="720"/></w:tabs></w:pPr>'
        p = partes('<w:p>' + formato + '<w:hyperlink w:anchor="destino">'
            '<w:r><w:t>literal</w:t><w:tab/><w:t>final</w:t></w:r></w:hyperlink></w:p>')
        r = self.inspeccionar(p)
        self.assertIs(r.estado, E.DOCUMENTO_VALIDADO_EN_ALCANCE)
        self.assertEqual([x.texto for x in r.parrafos], ['literal\tfinal'])
        self.assertEqual(self.inspeccionar(partes('<w:p>' + formato + '</w:p>')).parrafos[0].texto, '')

    def test_contextos_inline_invalidos_no_se_omiten_como_validos(self):
        for cuerpo in (
            '<w:sectPr><w:hyperlink><w:r><w:t>omitido</w:t></w:r></w:hyperlink></w:sectPr>',
            '<w:p><w:pPr><w:br/></w:pPr><w:r><w:t>literal</w:t></w:r></w:p>',
            '<w:p><w:r><w:pStyle w:val="fuera"/><w:t>literal</w:t></w:r></w:p>',
            '<w:p><w:hyperlink><w:hyperlink><w:r><w:t>anidado</w:t></w:r></w:hyperlink></w:hyperlink></w:p>',
        ):
            with self.subTest(cuerpo=cuerpo):
                r = self.inspeccionar(partes(cuerpo))
                self.assertIs(r.estado, E.DOCUMENTO_RECHAZADO)
                self.assertEqual(r.parrafos, ())
                self.assertEqual(r.causas_rechazo[0].codigo, 'estructura_textual_incoherente')

    def test_titulo_por_estilo_documental_sin_inferir_oficialidad(self):
        p = partes('<w:p><w:pPr><w:pStyle w:val="TituloSintetico"/></w:pPr><w:r><w:t>Titulo</w:t></w:r></w:p>')
        agregar(p, "word/styles.xml", f'<w:styles xmlns:w="{W}"><w:style w:styleId="TituloSintetico">'
            '<w:pPr><w:outlineLvl w:val="0"/></w:pPr></w:style></w:styles>',
            paquete.FIJOS["word/styles.xml"][0], "styles")
        r = self.inspeccionar(p)
        self.assertIs(r.estado, E.DOCUMENTO_VALIDADO_EN_ALCANCE)
        self.assertEqual((r.parrafos[0].estilo_id, r.parrafos[0].titulo_por_estilo), ("TituloSintetico", True))

    def test_tablas_filas_celdas_y_parrafos_sin_doble_conteo(self):
        tabla = '<w:tbl>' + ''.join('<w:tr>' + ''.join('<w:tc>' + parrafo(str(i*2+j)) + '</w:tc>'
            for j in range(2)) + '</w:tr>' for i in range(2)) + '</w:tbl>'
        r = self.inspeccionar(partes(parrafo("fuera") + tabla + tabla))
        self.assertIs(r.estado, E.DOCUMENTO_VALIDADO_EN_ALCANCE)
        self.assertEqual((len(r.parrafos), len(r.tablas)), (9, 2))
        self.assertEqual([c.texto for c in r.tablas[0].filas[1].celdas], ["2", "3"])
        p = r.tablas[0].filas[1].celdas[0].parrafos[0]
        self.assertIs(p, r.parrafos[3])
        self.assertEqual((p.referencia.tabla, p.referencia.fila, p.referencia.columna), (1, 2, 1))

    def test_tablas_anidadas_y_combinaciones_sin_replicar_texto(self):
        interior = '<w:tbl><w:tr><w:tc>' + parrafo("interior") + '</w:tc></w:tr></w:tbl>'
        cuerpo = '<w:tbl><w:tr><w:tc><w:tcPr><w:gridSpan w:val="2"/><w:vMerge w:val="restart"/></w:tcPr>'
        r = self.inspeccionar(partes(cuerpo + parrafo("exterior") + interior + '</w:tc></w:tr></w:tbl>'))
        self.assertIs(r.estado, E.DOCUMENTO_VALIDADO_EN_ALCANCE)
        self.assertEqual([p.texto for p in r.parrafos], ["exterior", "interior"])
        celda = r.tablas[0].filas[0].celdas[0]
        self.assertEqual((celda.grid_span, celda.vmerge, celda.texto), ("2", "restart", "exterior"))
        self.assertEqual(celda.tablas_anidadas, (r.tablas[1].referencia.ruta_xml,))

    def test_encabezado_y_pie_referenciados_una_vez(self):
        p = partes()
        header = agregar(p, "word/header1.xml", f'<w:hdr xmlns:w="{W}">{parrafo("cabecera")}</w:hdr>',
            paquete.BASE + "wordprocessingml.header+xml", "header")
        footer = agregar(p, "word/footer1.xml", f'<w:ftr xmlns:w="{W}">{parrafo("pie")}</w:ftr>',
            paquete.BASE + "wordprocessingml.footer+xml", "footer")
        p["word/document.xml"] = p["word/document.xml"].replace(b'</w:body>',
            (f'<w:sectPr><w:headerReference r:id="{header}"/><w:footerReference r:id="{footer}"/></w:sectPr></w:body>').encode())
        r = self.inspeccionar(p)
        self.assertIs(r.estado, E.DOCUMENTO_VALIDADO_EN_ALCANCE)
        self.assertEqual({x.origen for x in r.parrafos}, {"cuerpo", "encabezado", "pie"})
        self.assertEqual(sum(x.texto == "cabecera" for x in r.parrafos), 1)
        self.assertEqual(len(r.relaciones), 3)

    def test_propiedades_tecnicas_no_son_version_editorial_y_no_publican_autor(self):
        p = partes()
        core = ('<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
            'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:d="http://purl.org/dc/terms/">'
            '<dc:title>Titulo declarado</dc:title><dc:creator>PERSONA_FICTICIA</dc:creator>'
            '<d:modified>2020-01-01T00:00:00Z</d:modified><cp:revision>7</cp:revision></cp:coreProperties>')
        agregar(p, "docProps/core.xml", core, paquete.MIME_CORE, REL + "/metadata/core-properties", raiz=True)
        r = self.inspeccionar(p)
        self.assertIs(r.estado, E.DOCUMENTO_VALIDADO_EN_ALCANCE)
        self.assertEqual([x.valor for x in r.propiedades], ["Titulo declarado", "2020-01-01T00:00:00Z", "7"])
        self.assertTrue(all("no_vigencia_editorial" in x.naturaleza for x in r.propiedades))
        self.assertNotIn("PERSONA_FICTICIA", repr(r))

    def test_referencias_clark_reproducibles_y_resolubles(self):
        datos = zip_docx(partes(parrafo("uno") + parrafo("dos")))
        a, b = inspeccionar_docx_bytes(datos), inspeccionar_docx_bytes(datos)
        self.assertEqual(a, b)
        with ZipFile(BytesIO(datos)) as z:
            for p in a.parrafos:
                raiz = ET.fromstring(z.read(p.referencia.parte))  # Solo este fixture confiable.
                ruta = p.referencia.ruta_xml.removeprefix('/' + raiz.tag + '[1]/')
                e = raiz.find(ruta)
                self.assertIsNotNone(e)
                self.assertEqual(''.join(e.itertext()), p.texto)
                self.assertEqual(p.referencia.sha256, a.identidad.sha256)

    def test_zip_invalido_y_truncado(self):
        for datos in (b"no-es-zip", zip_docx()[:-10]):
            with self.subTest(bytes=len(datos)):
                self.assertIs(inspeccionar_docx_bytes(datos).estado, E.DOCUMENTO_RECHAZADO)

    def test_crc_alterado_no_devuelve_texto(self):
        datos = bytearray(zip_docx())
        datos[datos.index(b'Texto sintetico')] ^= 1
        r = inspeccionar_docx_bytes(bytes(datos))
        self.assertIs(r.estado, E.DOCUMENTO_RECHAZADO)
        self.assertEqual(r.parrafos, ())

    def test_duplicados_explicitos_y_casefold(self):
        p = partes(); p["WORD/document.xml"] = p["word/document.xml"]
        datos = BytesIO(zip_docx())
        with self.assertWarns(UserWarning), ZipFile(datos, "a") as z:
            z.writestr("word/document.xml", b"duplicado")
        for b in (datos.getvalue(), zip_docx(p)):
            with self.subTest(bytes=len(b)):
                self.assertIs(inspeccionar_docx_bytes(b).estado, E.DOCUMENTO_RECHAZADO)

    def test_rutas_zip_inseguras_y_nombres_no_se_reflejan(self):
        for nombre in ("../SECRETO.xml", "/abs.xml", "C:/foo.xml", "word\\foo.xml", "%2e%2e/foo.xml", "word/NUL.xml"):
            p = partes(); p[nombre] = b"<a/>"
            with self.subTest(nombre=nombre):
                r = self.inspeccionar(p)
                self.assertIs(r.estado, E.DOCUMENTO_RECHAZADO)
                self.assertNotIn("SECRETO", str(r.diagnostico_publico()))

    def test_enlace_zip_no_admitido(self):
        self.assertIs(inspeccionar_docx_bytes(zip_docx(enlace="word/document.xml")).estado, E.DOCUMENTO_RECHAZADO)

    def test_cifrado_y_metodo_compresion_no_admitidos(self):
        for campo, valor in ((6, 1), (8, 99)):
            b = bytearray(zip_docx()); cd = b.index(b'PK\x01\x02')
            struct.pack_into('<H', b, campo, valor)
            struct.pack_into('<H', b, cd + (8 if campo == 6 else 10), valor)
            with self.subTest(campo=campo):
                self.assertIs(inspeccionar_docx_bytes(bytes(b)).estado, E.DOCUMENTO_RECHAZADO)

    def test_tamanos_locales_inconsistentes(self):
        b = bytearray(zip_docx()); struct.pack_into('<I', b, 22, 1)
        r = inspeccionar_docx_bytes(bytes(b))
        self.assertIs(r.estado, E.DOCUMENTO_RECHAZADO)
        self.assertEqual(r.causas_rechazo[0].codigo, "zip_tamanos_locales_incoherentes")

    def test_tamano_y_crc_de_prefijo_no_ocultan_bytes_sobrantes(self):
        for metodo in (ZIP_STORED, ZIP_DEFLATED):
            for nombre in ('word/document.xml', 'word/media/image1.png'):
                with self.subTest(metodo=metodo, nombre=nombre):
                    p = partes()
                    if nombre.endswith('.png'):
                        agregar(p, nombre, b'\x89PNG\r\n\x1a\nfixture', 'image/png', 'image')
                    original = p[nombre]
                    p[nombre] += b'EXCESO_SINTETICO'
                    b = bytearray(zip_docx(p, compresion=metodo))
                    with ZipFile(BytesIO(b)) as z:
                        info = z.getinfo(nombre)
                    # Ambas cabeceras concuerdan entre sí y con el CRC del prefijo.
                    struct.pack_into('<I', b, info.header_offset + 14, binascii.crc32(original))
                    struct.pack_into('<I', b, info.header_offset + 22, len(original))
                    cursor = b.index(b'PK\x01\x02')
                    while b[cursor:cursor+4] == b'PK\x01\x02':
                        ln, le, lc = struct.unpack_from('<HHH', b, cursor+28)
                        if b[cursor+46:cursor+46+ln] == nombre.encode():
                            struct.pack_into('<I', b, cursor+16, binascii.crc32(original))
                            struct.pack_into('<I', b, cursor+24, len(original))
                            break
                        cursor += 46 + ln + le + lc
                    else:
                        self.fail('El fixture no localizó su entrada central')
                    r = inspeccionar_docx_bytes(bytes(b))
                    self.assertIs(r.estado, E.DOCUMENTO_RECHAZADO)
                    self.assertEqual(r.parrafos, ())
                    self.assertEqual(r.partes, ())

    def test_deflate_sin_marcador_final_no_basta_con_tamano_y_crc(self):
        b = bytearray(zip_docx(compresion=ZIP_DEFLATED))
        with ZipFile(BytesIO(b)) as z:
            info = z.getinfo('word/document.xml')
        ln, le = struct.unpack_from('<HH', b, info.header_offset + 26)
        inicio = info.header_offset + 30 + ln + le
        self.assertTrue(b[inicio] & 1)  # BFINAL del único bloque sintético.
        b[inicio] &= 0xfe  # El contenido y CRC no cambian; falta el bloque final.
        r = inspeccionar_docx_bytes(bytes(b))
        self.assertIs(r.estado, E.DOCUMENTO_RECHAZADO)
        self.assertEqual(r.causas_rechazo[0].codigo, 'flujo_deflate_incoherente')
        self.assertEqual((r.parrafos, r.partes), ((), ()))
        # Si CPython deja de ofrecer el estado, no se declara validación completa.
        class SinEstado:
            def __init__(self, archivo): self.archivo = archivo
            def __getattr__(self, nombre):
                if nombre == '_decompressor': raise AttributeError(nombre)
                return getattr(self.archivo, nombre)
            def __enter__(self): return self
            def __exit__(self, *args): self.archivo.close()
        abrir = ZipFile.open
        def sin_estado(z, *args, **kw): return SinEstado(abrir(z, *args, **kw))
        with patch.object(ZipFile, 'open', sin_estado):
            self.assertIs(inspeccionar_docx_bytes(zip_docx(compresion=ZIP_DEFLATED)).estado, E.DOCUMENTO_RECHAZADO)

    def test_expansion_excesiva(self):
        b = zip_docx(partes(parrafo("A" * 80_000)), compresion=ZIP_DEFLATED)
        self.assertIs(inspeccionar_docx_bytes(b).estado, E.INSPECCION_INCOMPLETA)

    def test_limites_entrada_total_entradas_central_y_archivo(self):
        base = LimitesDOCX(); datos = zip_docx()
        opciones = (replace(base,max_archivo=10), replace(base,zip=replace(base.zip,max_bytes_entrada=10)),
            replace(base,zip=replace(base.zip,max_bytes_descomprimidos=10)),
            replace(base,zip=replace(base.zip,max_entradas_zip=2)), replace(base,zip=replace(base.zip,max_central_zip=30)))
        for lim in opciones:
            with self.subTest(lim=lim):
                self.assertIs(inspeccionar_docx_bytes(datos,limites=lim).estado,E.INSPECCION_INCOMPLETA)

    def test_limites_xml_numero_bytes_nodos_profundidad(self):
        base = LimitesDOCX()
        for lim in (replace(base,max_xml=1),replace(base,zip=replace(base.zip,max_bytes_xml=16)),
                    replace(base,zip=replace(base.zip,max_nodos_xml=2)),replace(base,zip=replace(base.zip,max_profundidad_xml=2))):
            with self.subTest(lim=lim):
                self.assertIs(self.inspeccionar(limites=lim).estado,E.INSPECCION_INCOMPLETA)

    def test_content_types_invalidos_y_mime_no_docx(self):
        for contenido in (b'<Types/>',partes()["[Content_Types].xml"].replace(b'wordprocessingml.document.main+xml',b'wordprocessingml.template.main+xml')):
            p=partes();p["[Content_Types].xml"]=contenido
            with self.subTest(contenido=contenido[:20]):self.assertIs(self.inspeccionar(p).estado,E.DOCUMENTO_RECHAZADO)

    def test_relaciones_internas_ausentes_rotas_o_duplicadas(self):
        original=partes()["_rels/.rels"]
        for contenido in (original.replace(b'word/document.xml',b'word/ausente.xml'),
            original.replace(b'</Relationships>',original[original.index(b'<Relationship Id='):original.index(b'</Relationships>')]+b'</Relationships>')):
            p=partes();p["_rels/.rels"]=contenido
            with self.subTest(contenido=contenido[:20]):self.assertIs(self.inspeccionar(p).estado,E.DOCUMENTO_RECHAZADO)

    def test_relacion_externa_bloqueada_sin_filtrar_destino(self):
        p=partes();p["_rels/.rels"]=p["_rels/.rels"].replace(b'</Relationships>',
            f'<Relationship Id="externa" Type="{R}/hyperlink" Target="https://prohibido.invalid/?token=SECRETO_FICTICIO" TargetMode="External"/></Relationships>'.encode())
        r=self.inspeccionar(p)
        self.assertIs(r.estado,E.DOCUMENTO_RECHAZADO)
        self.assertNotIn("SECRETO_FICTICIO",repr(r))
        self.assertEqual(r.parrafos,())

    def test_controles_ooxml_no_ignoran_contenido_anidado_o_desconocido(self):
        for nombre, antes, despues in (
            ('_rels/.rels', b'/></Relationships>', b'><Relationship Id="anidada" Type="fuera" '
                b'Target="https://prohibido.invalid/?token=SECRETO_FICTICIO" TargetMode="External"/></Relationship></Relationships>'),
            ('[Content_Types].xml', b'/></Types>', b'><objeto-no-admitido/></Override></Types>'),
            ('_rels/.rels', b'Id="rPrincipal"', b'Id="rPrincipal" Extra="opaco"'),
            ('[Content_Types].xml', b'</Types>', b'TEXTO_NO_ADMITIDO</Types>'),
        ):
            with self.subTest(nombre=nombre, despues=despues[:25]):
                p = partes(); p[nombre] = p[nombre].replace(antes, despues)
                r = self.inspeccionar(p)
                self.assertIs(r.estado, E.DOCUMENTO_RECHAZADO)
                self.assertEqual(r.causas_rechazo[0].codigo, 'control_ooxml_no_admitido')
                self.assertEqual(r.parrafos, ())
                self.assertNotIn('SECRETO_FICTICIO', repr(r))

    def test_macros_y_objetos_en_docx_con_marcadores_basicos_validos(self):
        for nombre,mime,clase in (("word/vbaProject.bin","application/vnd.ms-office.vbaProject","vbaProject"),
            ("word/embeddings/oleObject1.bin","application/vnd.openxmlformats-officedocument.oleObject","oleObject"),
            ("word/activeX/activeX1.xml","application/xml","control")):
            p=partes();agregar(p,nombre,b'contenido-ficticio',mime,clase)
            with self.subTest(nombre=nombre):self.assertIs(self.inspeccionar(p).estado,E.DOCUMENTO_RECHAZADO)

    def test_zip_anidado_no_autorizado(self):
        p=partes();agregar(p,"word/embeddings/adjunto.zip",zip_docx(),"application/zip","package")
        self.assertIs(self.inspeccionar(p).estado,E.DOCUMENTO_RECHAZADO)

    def test_xml_malformado_dtd_y_entidades(self):
        for xml in (b'<w:document',f'<!DOCTYPE w:document [<!ENTITY x SYSTEM "https://prohibido.invalid/">]><w:document xmlns:w="{W}"><w:body/></w:document>'.encode(),
            f'<!DOCTYPE w:document [<!ENTITY x "texto">]><w:document xmlns:w="{W}"><w:body/></w:document>'.encode()):
            p=partes();p["word/document.xml"]=xml
            with self.subTest(xml=xml[:25]):self.assertIs(self.inspeccionar(p).estado,E.DOCUMENTO_RECHAZADO)

    def test_instrucciones_xml_xinclude_y_atributos_no_contemplados(self):
        p=partes();p['word/document.xml']=b'<?xml-stylesheet href="https://prohibido.invalid/"?>'+p['word/document.xml']
        self.assertIs(self.inspeccionar(p).estado,E.DOCUMENTO_RECHAZADO)
        p=partes('<w:p xmlns:xi="http://www.w3.org/2001/XInclude"><xi:include href="https://prohibido.invalid/"/></w:p>')
        self.assertIs(self.inspeccionar(p).estado,E.DOCUMENTO_RECHAZADO)
        p=partes('<w:p extensionNoContemplada="si"><w:r><w:t>no promover</w:t></w:r></w:p>')
        r=self.inspeccionar(p)
        self.assertIs(r.estado,E.INSPECCION_INCOMPLETA);self.assertEqual(r.parrafos,())

    def test_parte_principal_ausente_y_strict_fuera_de_alcance(self):
        p=partes();del p["word/document.xml"]
        self.assertIs(self.inspeccionar(p).estado,E.DOCUMENTO_RECHAZADO)
        p=partes();p["word/document.xml"]=p["word/document.xml"].replace(W.encode(),b'http://purl.oclc.org/ooxml/wordprocessingml/main')
        self.assertIs(self.inspeccionar(p).estado,E.DOCUMENTO_RECHAZADO)

    def test_campos_y_cache_omiten_parte_completa_sin_ejecutar(self):
        for contenido in ('<w:p><w:fldSimple w:instr="DDE un-programa"><w:r><w:t>CACHE_NO_OFICIAL</w:t></w:r></w:fldSimple></w:p>',
            '<w:p><w:r><w:fldChar w:fldCharType="begin"/></w:r></w:p>'+parrafo("CACHE_NO_OFICIAL")):
            r=self.inspeccionar(partes(contenido))
            with self.subTest(contenido=contenido[:20]):
                self.assertIs(r.estado,E.INSPECCION_INCOMPLETA)
                self.assertEqual(r.parrafos,())
                self.assertNotIn("CACHE_NO_OFICIAL",repr(r))

    def test_revisiones_texto_oculto_y_caracteristicas_desconocidas_no_se_promueven(self):
        for contenido in ('<w:ins>'+parrafo("revision")+'</w:ins>',
            '<w:p><w:r><w:rPr><w:vanish/></w:rPr><w:t>oculto</w:t></w:r></w:p>',
            '<w:caracteristicaNueva>'+parrafo("no-conocido")+'</w:caracteristicaNueva>'):
            with self.subTest(contenido=contenido[:20]):
                r=self.inspeccionar(partes(contenido));self.assertIs(r.estado,E.INSPECCION_INCOMPLETA);self.assertEqual(r.parrafos,())

    def test_estructura_textual_invalida_no_se_aplana(self):
        for cuerpo in ('<w:p>'+parrafo("anidado-invalido")+'</w:p>',
            '<w:p><w:pPr><w:t>no-visible-como-run</w:t></w:pPr></w:p>', '<w:p>texto-sin-run</w:p>'):
            with self.subTest(cuerpo=cuerpo):self.assertIs(self.inspeccionar(partes(cuerpo)).estado,E.DOCUMENTO_RECHAZADO)

    def test_limites_texto_fragmento_y_total(self):
        for limite in (replace(LimitesDOCX(),max_texto_fragmento=3),replace(LimitesDOCX(),max_texto_total=3)):
            r=self.inspeccionar(limites=limite)
            self.assertIs(r.estado,E.INSPECCION_INCOMPLETA)
            self.assertEqual(r.parrafos,())

    def test_limites_tablas_celdas_parrafos_y_relaciones(self):
        tabla='<w:tbl><w:tr><w:tc>'+parrafo()+ '</w:tc><w:tc>'+parrafo()+'</w:tc></w:tr></w:tbl>'
        for cuerpo,lim in ((parrafo()+parrafo(),replace(LimitesDOCX(),max_parrafos=1)),
            (tabla+tabla,replace(LimitesDOCX(),max_tablas=1)),(tabla,replace(LimitesDOCX(),max_celdas=1))):
            with self.subTest(lim=lim):self.assertIs(self.inspeccionar(partes(cuerpo),limites=lim).estado,E.INSPECCION_INCOMPLETA)
        p=partes()
        agregar(p,"word/header1.xml",f'<w:hdr xmlns:w="{W}"/>',paquete.BASE+'wordprocessingml.header+xml','header')
        self.assertIs(self.inspeccionar(p,limites=replace(LimitesDOCX(),max_referencias=1)).estado,E.INSPECCION_INCOMPLETA)

    def test_metadatos_y_estilos_tienen_cupos_independientes(self):
        p=partes()
        agregar(p,"word/styles.xml",f'<w:styles xmlns:w="{W}"><w:style w:styleId="a"/><w:style w:styleId="b"/></w:styles>',
            paquete.FIJOS['word/styles.xml'][0],'styles')
        self.assertIs(self.inspeccionar(p,limites=replace(LimitesDOCX(),max_estilos=1)).estado,E.INSPECCION_INCOMPLETA)
        p=partes()
        agregar(p,'docProps/core.xml','<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
            'xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>a</dc:title><dc:subject>b</dc:subject></cp:coreProperties>',
            paquete.MIME_CORE,REL+'/metadata/core-properties',raiz=True)
        self.assertIs(self.inspeccionar(p,limites=replace(LimitesDOCX(),max_propiedades=1)).estado,E.INSPECCION_INCOMPLETA)

    def test_formato_global_oculto_no_deja_cache_ni_texto_promovido(self):
        p=partes(parrafo('TEXTO_NO_PROMOVIBLE'))
        agregar(p,'word/styles.xml',f'<w:styles xmlns:w="{W}"><w:style w:styleId="oculto"><w:rPr><w:vanish/></w:rPr></w:style></w:styles>',
            paquete.FIJOS['word/styles.xml'][0],'styles')
        r=self.inspeccionar(p)
        self.assertIs(r.estado,E.INSPECCION_INCOMPLETA);self.assertEqual(r.parrafos,())

    def test_notas_referenciadas_y_referencias_rotas(self):
        p=partes('<w:p><w:r><w:t>cuerpo</w:t><w:footnoteReference w:id="7"/></w:r></w:p>')
        agregar(p,'word/footnotes.xml',f'<w:footnotes xmlns:w="{W}"><w:footnote w:id="7">{parrafo("nota")}</w:footnote></w:footnotes>',
            paquete.FIJOS['word/footnotes.xml'][0],'footnotes')
        r=self.inspeccionar(p)
        self.assertIs(r.estado,E.DOCUMENTO_VALIDADO_EN_ALCANCE)
        self.assertEqual([x.texto for x in r.parrafos],['cuerpo','nota'])
        p['word/document.xml']=p['word/document.xml'].replace(b'w:id="7"',b'w:id="8"')
        self.assertIs(self.inspeccionar(p).estado,E.DOCUMENTO_RECHAZADO)

    def test_imagen_pasiva_no_se_decodifica_y_zip_renombrado_no_se_admite(self):
        p=partes()
        agregar(p,'word/media/image1.png',b'\x89PNG\r\n\x1a\nsolo-fixture-no-renderizado','image/png','image')
        r=self.inspeccionar(p)
        self.assertIs(r.estado,E.DOCUMENTO_VALIDADO_EN_ALCANCE)
        self.assertIn('imagen_no_renderizada_ni_interpretada',[d.codigo for d in r.operaciones_omitidas])
        p['word/media/image1.png']=zip_docx()
        self.assertIs(self.inspeccionar(p).estado,E.DOCUMENTO_RECHAZADO)

    def test_coherencia_de_tipo_rid_orfandad_y_fragmentos(self):
        p=partes();p['word/styles.xml']=f'<w:styles xmlns:w="{W}"/>'.encode()
        p['[Content_Types].xml']=p['[Content_Types].xml'].replace(b'</Types>',
            f'<Override PartName="/word/styles.xml" ContentType="{paquete.FIJOS["word/styles.xml"][0]}"/></Types>'.encode())
        self.assertIs(self.inspeccionar(p).estado,E.DOCUMENTO_RECHAZADO)
        p=partes('<w:sectPr><w:headerReference r:id="rNoExiste"/></w:sectPr>')
        self.assertIs(self.inspeccionar(p).estado,E.DOCUMENTO_RECHAZADO)
        p=partes();p['_rels/.rels']=p['_rels/.rels'].replace(b'word/document.xml',b'word/document.xml#fragmento')
        self.assertIs(self.inspeccionar(p).estado,E.DOCUMENTO_RECHAZADO)
        p=partes();p['word/document.xml']=p['word/document.xml'].replace(b'<w:body>',b'<w:body><w:sectPr><w:headerReference/></w:sectPr>')
        self.assertIs(self.inspeccionar(p).estado,E.DOCUMENTO_RECHAZADO)

    def test_actividad_en_elementos_y_mime_de_macro_no_se_acepta(self):
        for cuerpo in ('<w:altChunk/>','<w:p><w:r><w:object/></w:r></w:p>'):
            self.assertIs(self.inspeccionar(partes(cuerpo)).estado,E.DOCUMENTO_RECHAZADO)
        p=partes();p['[Content_Types].xml']=p['[Content_Types].xml'].replace(b'wordprocessingml.document.main+xml',b'vnd.ms-word.document.macroEnabled.main+xml')
        self.assertIs(self.inspeccionar(p).estado,E.DOCUMENTO_RECHAZADO)

    def test_zip64_falso_y_cabeceras_incoherentes_no_aceptadas(self):
        for cambiar in ('eocd','flags'):
            b=bytearray(zip_docx())
            if cambiar=='eocd':struct.pack_into('<I',b,b.rfind(b'PK\x05\x06')+12,0xffffffff)
            else:struct.pack_into('<H',b,6,0x800)
            with self.subTest(cambiar=cambiar):
                self.assertIsNot(inspeccionar_docx_bytes(bytes(b)).estado,E.DOCUMENTO_VALIDADO_EN_ALCANCE)

    def test_limite_lecturas_y_consumos_explicitos(self):
        r=self.inspeccionar(limites=replace(LimitesDOCX(),max_lecturas_zip=10))
        self.assertIs(r.estado,E.INSPECCION_INCOMPLETA)
        self.assertGreater(r.consumo.bytes_zip_preflight,0)
        r=self.inspeccionar()
        self.assertGreater(r.consumo.bytes_zip_verificacion,0)
        self.assertGreater(r.consumo.bytes_descomprimidos_extraccion,0)
        self.assertEqual(r.consumo.xml_procesados,3)

    def test_presupuesto_memoria_auxiliar_y_pico_acotado(self):
        r=self.inspeccionar(limites=replace(LimitesDOCX(),max_bytes_auxiliares=32))
        self.assertIs(r.estado,E.INSPECCION_INCOMPLETA)
        datos=zip_docx(partes(''.join(parrafo('x'*2000) for _ in range(100))))
        tracemalloc.start()
        try:
            r=inspeccionar_docx_bytes(datos)
            pico=tracemalloc.get_traced_memory()[1]
        finally:tracemalloc.stop()
        self.assertIs(r.estado,E.DOCUMENTO_VALIDADO_EN_ALCANCE)
        self.assertLessEqual(r.consumo.bytes_auxiliares_pico,r.limites.max_bytes_auxiliares)
        self.assertLess(pico,32*1024*1024)  # Ensayo concreto; no es cuota RSS del SO.

    def test_cancelacion_previa_y_durante_recorrido(self):
        evento=Event();evento.set()
        r=self.inspeccionar(cancelacion=evento)
        self.assertIs(r.estado,E.INSPECCION_INCOMPLETA);self.assertIsNone(r.identidad)
        evento.clear(); llamadas=0
        def reloj():
            nonlocal llamadas
            llamadas+=1
            if llamadas==40:evento.set()
            return 0
        r=self.inspeccionar(cancelacion=evento,reloj=reloj)
        self.assertIs(r.estado,E.INSPECCION_INCOMPLETA);self.assertEqual(r.parrafos,())

    def test_plazo_y_argumentos_de_politica(self):
        with patch.object(api.time,"monotonic",side_effect=[0,6]):
            r=self.inspeccionar(reloj=api.time.monotonic)
        self.assertIs(r.estado,E.INSPECCION_INCOMPLETA)
        for kw in ({"max_archivo":0},{"max_xml":True},{"max_segundos":float('nan')},{"max_bytes_auxiliares":100_000_000}):
            with self.subTest(kw=kw),self.assertRaises(ValueError):LimitesDOCX(**kw)
        with self.assertRaises(TypeError):inspeccionar_docx_bytes(bytearray(zip_docx()))
        with self.assertRaises(FrozenInstanceError):LimitesDOCX().max_archivo=1

    def test_bytes_sin_archivos_conexiones_sqlite_o_subprocesos(self):
        datos=zip_docx()
        with patch("builtins.open",side_effect=AssertionError("archivo")),patch("socket.socket.connect",side_effect=AssertionError("red")), \
             patch("socket.getaddrinfo",side_effect=AssertionError("DNS")),patch("sqlite3.connect",side_effect=AssertionError("SQLite")), \
             patch("subprocess.Popen",side_effect=AssertionError("proceso")),patch("zipfile.ZipFile.extractall",side_effect=AssertionError("extraer")):
            self.assertIs(inspeccionar_docx_bytes(datos).estado,E.DOCUMENTO_VALIDADO_EN_ALCANCE)

    def test_reutiliza_verificador_zip_existente(self):
        with patch.object(paquete,"inspeccionar_zip",wraps=paquete.inspeccionar_zip) as reutilizado:
            self.assertIs(self.inspeccionar().estado,E.DOCUMENTO_VALIDADO_EN_ALCANCE)
        reutilizado.assert_called_once()


class ArchivoDOCXTests(unittest.TestCase):
    def setUp(self):
        self.base=Path(tempfile.gettempdir()).resolve()/('spica-docx-84g-'+uuid4().hex)
        self.base.mkdir(mode=0o755)
        self.addCleanup(self.limpiar)
        self.ruta=self.base/'ficticio.docx';self.datos=zip_docx();self.ruta.write_bytes(self.datos)

    def limpiar(self):
        assert self.base.resolve().parent==Path(tempfile.gettempdir()).resolve()
        assert self.base.name.startswith('spica-docx-84g-')
        shutil.rmtree(self.base)

    def test_preservacion_fisica_hash_y_permisos_antes_despues(self):
        antes=self.ruta.stat()
        r=inspeccionar_docx_archivo(self.ruta,directorio_autorizado=self.base,
            tamano_esperado=len(self.datos),sha256_esperado=hashlib.sha256(self.datos).hexdigest())
        despues=self.ruta.stat()
        self.assertIs(r.estado,E.DOCUMENTO_VALIDADO_EN_ALCANCE)
        self.assertTrue(r.conservacion_comprobada)
        self.assertEqual(self.ruta.read_bytes(),self.datos)
        self.assertEqual((antes.st_mode,antes.st_mtime_ns,antes.st_ino),(despues.st_mode,despues.st_mtime_ns,despues.st_ino))
        self.assertEqual({p.name for p in self.base.iterdir()},{'ficticio.docx'})

    def test_identidad_esperada_incorrecta_y_preservacion_en_rechazo(self):
        r=inspeccionar_docx_archivo(self.ruta,directorio_autorizado=self.base,sha256_esperado='0'*64)
        self.assertIs(r.estado,E.DOCUMENTO_RECHAZADO);self.assertTrue(r.conservacion_comprobada)
        self.assertEqual(r.parrafos,());self.assertEqual(self.ruta.read_bytes(),self.datos)

    def test_escapes_rutas_inexistentes_directorio_y_reparse_sin_abrir(self):
        casos=((self.ruta,self.base/'otro'),(self.base/'..'/'archivo.docx',self.base),
            (self.base/'ausente.docx',self.base),(self.base,self.base))
        with patch.object(Path,"open",side_effect=AssertionError('no abrir')):
            for ruta,raiz in casos:
                with self.subTest(ruta=ruta):self.assertIs(inspeccionar_docx_archivo(ruta,directorio_autorizado=raiz).estado,E.DOCUMENTO_RECHAZADO)
        original=Path.lstat
        def enlace(p,*a,**k):
            if p==self.ruta:return SimpleNamespace(st_mode=stat.S_IFLNK,st_file_attributes=0x400)
            return original(p,*a,**k)
        with patch.object(Path,'lstat',enlace),patch.object(Path,'open',side_effect=AssertionError('no abrir')):
            self.assertIs(inspeccionar_docx_archivo(self.ruta,directorio_autorizado=self.base).estado,E.DOCUMENTO_RECHAZADO)

    def test_modificacion_durante_inspeccion_descarta_resultados(self):
        evaluar=api._evaluar
        def cambiar(datos,c):
            r=evaluar(datos,c)
            self.ruta.write_bytes(self.datos+b'alterado-por-fixture')
            return r
        with patch.object(api,'_evaluar',side_effect=cambiar):
            r=inspeccionar_docx_archivo(self.ruta,directorio_autorizado=self.base)
        self.assertIs(r.estado,E.DOCUMENTO_RECHAZADO);self.assertFalse(r.conservacion_comprobada);self.assertEqual(r.parrafos,())

    def test_cancelacion_no_inventa_comprobacion_final(self):
        evento=Event();evaluar=api._evaluar
        def cancelar(datos,c):
            r=evaluar(datos,c);evento.set();return r
        with patch.object(api,'_evaluar',side_effect=cancelar):
            r=inspeccionar_docx_archivo(self.ruta,directorio_autorizado=self.base,cancelacion=evento)
        self.assertIs(r.estado,E.INSPECCION_INCOMPLETA);self.assertIsNone(r.conservacion_comprobada)
        self.assertEqual(self.ruta.read_bytes(),self.datos)

    def test_cancelacion_final_conserva_rechazo_ya_demostrado(self):
        self.ruta.write_bytes(b'no-es-docx')
        evento=Event();evaluar=api._evaluar
        def cancelar(datos,c):
            r=evaluar(datos,c);evento.set();return r
        with patch.object(api,'_evaluar',side_effect=cancelar):
            r=inspeccionar_docx_archivo(self.ruta,directorio_autorizado=self.base,cancelacion=evento)
        self.assertIs(r.estado,E.DOCUMENTO_RECHAZADO)
        self.assertTrue(r.causas_rechazo);self.assertIsNone(r.conservacion_comprobada)
        self.assertIn('cancelado',[d.codigo for d in r.operaciones_omitidas])

    def test_archivo_excesivo_no_se_abre_ni_inventa_sha(self):
        with patch.object(Path,'open',side_effect=AssertionError('no leer')):
            r=inspeccionar_docx_archivo(self.ruta,directorio_autorizado=self.base,limites=replace(LimitesDOCX(),max_archivo=10))
        self.assertIs(r.estado,E.INSPECCION_INCOMPLETA)
        self.assertEqual(r.identidad.tamano,len(self.datos));self.assertIsNone(r.identidad.sha256)


if __name__ == '__main__':
    unittest.main()
