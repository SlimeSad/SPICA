"""Perfil cerrado de hipervínculos omitidos; solo OOXML sintético, sin red."""

from dataclasses import asdict, replace
from html import escape
import hashlib
from pathlib import Path
import shutil
import struct
import sys
import tempfile
from threading import Event
import unittest
from unittest.mock import patch
from uuid import uuid4
from io import BytesIO
from xml.etree import ElementTree as ET
from zipfile import ZipFile, ZIP_DEFLATED

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from spica.adquisicion.verificacion.docx import (
    EstadoInspeccionDOCX as E, LimitesDOCX, inspeccionar_docx_bytes, inspeccionar_docx_archivo,
)
from spica.adquisicion.verificacion.docx import _paquete as paquete
from spica.adquisicion.verificacion.docx._extraccion import Q, R, W
from test_inspector_docx import partes, parrafo, zip_docx, agregar, REL


def enlace(rid='rEnlace', texto='Texto local'):
    return f'<w:hyperlink r:id="{rid}"><w:r><w:t>{escape(texto)}</w:t></w:r></w:hyperlink>'


def relacion(p, rid='rEnlace', *, destino='https://prueba.invalid/referencia',
             tipo=R+'/hyperlink', modo='External', nombre='word/_rels/document.xml.rels'):
    if nombre not in p:
        p[nombre] = f'<Relationships xmlns="{REL}"></Relationships>'.encode()
    modo_xml = '' if modo is None else f' TargetMode="{escape(modo,quote=True)}"'
    p[nombre] = p[nombre].replace(b'</Relationships>',
        (f'<Relationship Id="{rid}" Type="{escape(tipo,quote=True)}" '
         f'Target="{escape(destino,quote=True)}"{modo_xml}/></Relationships>').encode())


class HipervinculosDOCXTests(unittest.TestCase):
    def fixture(self, cuerpo=None, **kw):
        p=partes('<w:p>'+enlace()+'</w:p>' if cuerpo is None else cuerpo)
        relacion(p,**kw)
        return p

    def inspeccionar(self,p=None,**kw):
        return inspeccionar_docx_bytes(zip_docx(self.fixture() if p is None else p),**kw)

    def test_sin_externas_conserva_resultados_anteriores(self):
        r=self.inspeccionar(partes())
        self.assertIs(r.estado,E.DOCUMENTO_VALIDADO_EN_ALCANCE)
        self.assertEqual(r.parrafos[0].texto,'Texto sintetico')
        self.assertEqual(r.hipervinculos_omitidos,())
        self.assertEqual(r.version_inspector,'0.2.1')

    def test_http_https_mailto_son_omitidos_sin_destino_en_resultado(self):
        for destino,esquema in (('http://prueba.invalid/ruta','http'),('https://prueba.invalid/ruta','https'),
                                ('mailto:persona.ficticia@example.invalid','mailto')):
            with self.subTest(esquema=esquema):
                r=self.inspeccionar(self.fixture(destino=destino))
                self.assertIs(r.estado,E.DOCUMENTO_VALIDADO_EN_ALCANCE)
                self.assertEqual(r.parrafos[0].texto,'Texto local')
                h,=r.hipervinculos_omitidos
                self.assertEqual((h.identificador,h.tipo,h.target_mode,h.parte_origen,h.tipo_destino),
                                 ('rEnlace',R+'/hyperlink','External','word/document.xml',esquema))
                self.assertNotIn(destino,str(asdict(r)))
                self.assertFalse(hasattr(h,'destino'))
                self.assertIn('destino_hipervinculo_externo_no_consultado',[d.codigo for d in r.operaciones_omitidas])

    def test_tabla_preserva_texto_orden_y_referencia_sin_duplicados(self):
        p=self.fixture(parrafo('antes')+'<w:tbl><w:tr><w:tc><w:p>'+enlace()+
            '</w:p></w:tc></w:tr></w:tbl>'+parrafo('despues'))
        r=self.inspeccionar(p)
        self.assertIs(r.estado,E.DOCUMENTO_VALIDADO_EN_ALCANCE)
        self.assertEqual([x.texto for x in r.parrafos],['antes','Texto local','despues'])
        self.assertIs(r.tablas[0].filas[0].celdas[0].parrafos[0],r.parrafos[1])
        ref=r.hipervinculos_omitidos[0].referencias[0]
        self.assertIn(Q+'tbl[1]/'+Q+'tr[1]/'+Q+'tc[1]',ref.ruta_xml)
        self.assertEqual(ref.sha256,r.identidad.sha256)

    def test_multiples_enlaces_y_multiples_usos_del_mismo_id(self):
        p=self.fixture('<w:p>'+enlace()+enlace('segundo','otro')+enlace(texto='repetido')+'</w:p>')
        relacion(p,'segundo',destino='https://otro.invalid/')
        r=self.inspeccionar(p)
        self.assertIs(r.estado,E.DOCUMENTO_VALIDADO_EN_ALCANCE)
        self.assertEqual(r.parrafos[0].texto,'Texto localotrorepetido')
        self.assertEqual({h.identificador:len(h.referencias) for h in r.hipervinculos_omitidos}, {'rEnlace':2,'segundo':1})

    def test_relacion_sin_uso_no_se_admite_por_su_solo_tipo(self):
        for p in (self.fixture(parrafo('sin uso')),self.fixture()):
            relacion(p,'sinUso')
            r=self.inspeccionar(p)
            self.assertIs(r.estado,E.DOCUMENTO_RECHAZADO)
            self.assertEqual(r.causas_rechazo[0].codigo,'hipervinculo_externo_sin_uso')
            self.assertEqual((r.parrafos,r.hipervinculos_omitidos),((),()))

    def test_imagen_plantilla_ole_altchunk_y_desconocidas_siguen_bloqueadas(self):
        for clase in ('image','attachedTemplate','oleObject','aFChunk','package','tipoDesconocido'):
            with self.subTest(clase=clase):
                r=self.inspeccionar(self.fixture(tipo=R+'/'+clase))
                self.assertIs(r.estado,E.DOCUMENTO_RECHAZADO)
                self.assertEqual(r.causas_rechazo[0].codigo,'relacion_externa_no_admitida')
                self.assertEqual(r.parrafos,())

    def test_targetmode_invalido_y_id_duplicado(self):
        for modo in ('external','External ','Otra',None):
            with self.subTest(modo=modo):self.assertIs(self.inspeccionar(self.fixture(modo=modo)).estado,E.DOCUMENTO_RECHAZADO)
        p=self.fixture();relacion(p)
        self.assertIs(self.inspeccionar(p).estado,E.DOCUMENTO_RECHAZADO)

    def test_rid_ausente_y_uso_con_tipo_interno_contradictorio(self):
        p=self.fixture('<w:p>'+enlace('noExiste')+'</w:p>')
        self.assertIs(self.inspeccionar(p).estado,E.DOCUMENTO_RECHAZADO)
        p=self.fixture();p['word/document.xml']=p['word/document.xml'].replace(b'r:id=',b'r:embed=')
        self.assertIs(self.inspeccionar(p).estado,E.DOCUMENTO_RECHAZADO)
        p=self.fixture();p['word/_rels/document.xml.rels']=p['word/_rels/document.xml.rels'].replace(
            b'TargetMode="External"',b'TargetMode="Internal"')
        self.assertIs(self.inspeccionar(p).estado,E.DOCUMENTO_RECHAZADO)

    def test_origen_raiz_o_auxiliar_no_se_admite(self):
        p=partes();relacion(p,nombre='_rels/.rels')
        self.assertIs(self.inspeccionar(p).estado,E.DOCUMENTO_RECHAZADO)
        p=partes();agregar(p,'word/settings.xml',f'<w:settings xmlns:w="{W}"/>',paquete.FIJOS['word/settings.xml'][0],'settings')
        relacion(p,nombre='word/_rels/settings.xml.rels')
        self.assertIs(self.inspeccionar(p).estado,E.DOCUMENTO_RECHAZADO)

    def test_contexto_no_textual_o_ambiguo_no_se_autoriza(self):
        for cuerpo in ('<w:sectPr>'+enlace()+'</w:sectPr>',
            '<w:p><w:hyperlink r:id="rEnlace" w:anchor="contradictorio"><w:r><w:t>x</w:t></w:r></w:hyperlink></w:p>',
            '<w:p><w:drawing r:id="rEnlace"/></w:p>',
            '<w:p><w:hyperlink r:id="rEnlace"><w:hyperlink><w:r><w:t>x</w:t></w:r></w:hyperlink></w:hyperlink></w:p>'):
            with self.subTest(cuerpo=cuerpo):self.assertIs(self.inspeccionar(self.fixture(cuerpo)).estado,E.DOCUMENTO_RECHAZADO)

    def test_destinos_no_admitidos_no_abren_archivos_o_programas(self):
        destinos=('file:///C:/privado.docx','C:/privado.docx','\\\\servidor\\archivo','javascript:alert(1)',
                  'data:text/plain,contenido','ftp://prueba.invalid/','https:///sin-host','https://prueba.invalid:99999/',
                  'https://prueba.invalid/%25250a','https://prueba.invalid/%zz','mailto:persona@example.invalid?body=mensaje',
                  'https://user:CLAVE_FICTICIA@prueba.invalid/')
        for destino in destinos:
            with self.subTest(destino=destino):
                r=self.inspeccionar(self.fixture(destino=destino))
                self.assertIs(r.estado,E.DOCUMENTO_RECHAZADO)
                self.assertNotIn('CLAVE_FICTICIA',repr(r))

    def test_destino_con_token_se_omite_sin_filtrarlo(self):
        r=self.inspeccionar(self.fixture(destino='https://prueba.invalid/?token=SECRETO_FICTICIO#privado'))
        self.assertIs(r.estado,E.DOCUMENTO_VALIDADO_EN_ALCANCE)
        self.assertNotIn('SECRETO_FICTICIO',str(asdict(r)))
        self.assertNotIn('SECRETO_FICTICIO',str(r.diagnostico_publico()))
        self.assertEqual(r.diagnostico_publico()['hipervinculos_omitidos'],1)

    def test_enlace_pasivo_no_exime_macros_ni_xml_malformado_dtd(self):
        p=self.fixture();p['word/vbaProject.bin']=b'fixture'
        self.assertIs(self.inspeccionar(p).estado,E.DOCUMENTO_RECHAZADO)
        for mal in (b'<!DOCTYPE Relationships [<!ENTITY x "no">]>',b'<sin-cierre>'):
            p=self.fixture();p['word/_rels/document.xml.rels']=mal+p['word/_rels/document.xml.rels']
            self.assertIs(self.inspeccionar(p).estado,E.DOCUMENTO_RECHAZADO)

    def test_otra_caracteristica_no_admitida_conserva_inspeccion_incompleta(self):
        p=self.fixture('<w:p>'+enlace()+'</w:p><w:p><w:fldSimple w:instr="CAMPO"><w:r><w:t>cache</w:t></w:r></w:fldSimple></w:p>')
        r=self.inspeccionar(p)
        self.assertIs(r.estado,E.INSPECCION_INCOMPLETA)
        self.assertEqual(r.parrafos,())

    def test_crc_limites_zip_y_deflate_siguen_activos(self):
        p=self.fixture();b=bytearray(zip_docx(p));b[b.index(b'Texto local')]^=1
        self.assertIs(inspeccionar_docx_bytes(bytes(b)).estado,E.DOCUMENTO_RECHAZADO)
        b=bytearray(zip_docx(p,compresion=ZIP_DEFLATED))
        with ZipFile(BytesIO(b)) as z:i=z.getinfo('word/document.xml')
        ln,le=struct.unpack_from('<HH',b,i.header_offset+26);pos=i.header_offset+30+ln+le
        self.assertTrue(b[pos]&1);b[pos]&=0xfe
        self.assertIs(inspeccionar_docx_bytes(bytes(b)).estado,E.DOCUMENTO_RECHAZADO)
        base=LimitesDOCX()
        for limites in (replace(base,max_archivo=10),replace(base,zip=replace(base.zip,max_nodos_xml=2)),
                        replace(base,max_bytes_auxiliares=32),replace(base,max_referencias=1)):
            p=self.fixture();relacion(p,'otro',destino='https://otro.invalid/')
            self.assertIs(self.inspeccionar(p,limites=limites).estado,E.INSPECCION_INCOMPLETA)

    def test_limite_de_usos_y_cancelacion_durante_revision(self):
        p=self.fixture('<w:p>'+enlace()+enlace()+enlace()+'</w:p>')
        r=self.inspeccionar(p,limites=replace(LimitesDOCX(),max_referencias=2))
        self.assertIs(r.estado,E.INSPECCION_INCOMPLETA)
        evento=Event();original=paquete.registrar_usos
        def cancelar(*a,**kw):evento.set();return original(*a,**kw)
        with patch.object(paquete,'registrar_usos',side_effect=cancelar):r=self.inspeccionar(cancelacion=evento)
        self.assertIs(r.estado,E.INSPECCION_INCOMPLETA)
        self.assertEqual(r.parrafos,())

    def test_ausencia_de_red_archivos_sqlite_o_subprocesos(self):
        datos=zip_docx(self.fixture())
        with patch('builtins.open',side_effect=AssertionError('archivo')), \
             patch('socket.socket.connect',side_effect=AssertionError('red')), \
             patch('socket.getaddrinfo',side_effect=AssertionError('DNS')), \
             patch('subprocess.Popen',side_effect=AssertionError('proceso')), \
             patch('sqlite3.connect',side_effect=AssertionError('sqlite')):
            self.assertIs(inspeccionar_docx_bytes(datos).estado,E.DOCUMENTO_VALIDADO_EN_ALCANCE)

    def test_determinismo_y_localizadores_resolubles(self):
        p=self.fixture();datos=zip_docx(p);a=inspeccionar_docx_bytes(datos);b=inspeccionar_docx_bytes(datos)
        self.assertEqual(a,b)
        ref=a.hipervinculos_omitidos[0].referencias[0];raiz=ET.fromstring(p[ref.parte])
        encontrado=raiz.find(ref.ruta_xml.removeprefix('/'+raiz.tag+'[1]/'))
        self.assertEqual(encontrado.tag,Q+'hyperlink')
        self.assertEqual(''.join(encontrado.itertext()),a.parrafos[0].texto)

    def test_original_sintetico_con_enlace_se_conserva_intacto(self):
        raiz=Path(tempfile.gettempdir()).resolve()/('spica-84hb-test-'+uuid4().hex)
        raiz.mkdir(mode=0o755)
        try:
            p=raiz/'sintetico.docx';datos=zip_docx(self.fixture());p.write_bytes(datos);antes=p.stat()
            r=inspeccionar_docx_archivo(p,directorio_autorizado=raiz,sha256_esperado=hashlib.sha256(datos).hexdigest())
            self.assertIs(r.estado,E.DOCUMENTO_VALIDADO_EN_ALCANCE)
            self.assertTrue(r.conservacion_comprobada)
            self.assertEqual(p.read_bytes(),datos)
            despues=p.stat()
            self.assertEqual((antes.st_mode,antes.st_ino,antes.st_mtime_ns),(despues.st_mode,despues.st_ino,despues.st_mtime_ns))
            self.assertEqual({p.name for p in raiz.iterdir()},{'sintetico.docx'})
        finally:
            assert raiz.resolve().parent==Path(tempfile.gettempdir()).resolve() and raiz.name.startswith('spica-84hb-test-')
            shutil.rmtree(raiz)


if __name__=='__main__':unittest.main()
