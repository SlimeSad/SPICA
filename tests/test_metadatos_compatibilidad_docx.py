"""Metadatos XML pasivos exactos; no habilita revisiones, campos o extensiones."""

from dataclasses import asdict, replace
from html import escape
import hashlib
from io import BytesIO
from pathlib import Path
import shutil
import struct
import sys
import tempfile
from threading import Event
import unittest
from unittest.mock import patch
from uuid import uuid4
from zipfile import ZipFile, ZIP_DEFLATED

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from spica.adquisicion.verificacion.docx import (
    EstadoInspeccionDOCX as E, LimitesDOCX, inspeccionar_docx_bytes, inspeccionar_docx_archivo,
)
from spica.adquisicion.verificacion.docx import _paquete as paquete
from spica.adquisicion.verificacion.docx._extraccion import MC, W14, W, Q
from test_inspector_docx import partes, parrafo, zip_docx, agregar
from test_hipervinculos_docx import relacion, enlace


def documento(cuerpo=None, *, ignorable='w14', namespaces=None):
    p=partes(parrafo('Texto literal') if cuerpo is None else cuerpo)
    ns={'mc':MC,'w14':W14} if namespaces is None else namespaces
    atributos=''.join(f' xmlns:{prefijo}="{escape(uri,quote=True)}"' for prefijo,uri in ns.items())
    if ignorable is not None: atributos+=f' mc:Ignorable="{escape(ignorable,quote=True)}"'
    p['word/document.xml']=p['word/document.xml'].replace(b'<w:document ',('<w:document'+atributos+' ').encode())
    return p


class MetadatosCompatibilidadTests(unittest.TestCase):
    def inspeccionar(self,p=None,**kw):
        return inspeccionar_docx_bytes(zip_docx(documento() if p is None else p),**kw)

    def test_documento_sin_metadatos_es_compatible(self):
        r=self.inspeccionar(partes())
        self.assertIs(r.estado,E.DOCUMENTO_VALIDADO_EN_ALCANCE)
        self.assertEqual(r.parrafos[0].texto,'Texto sintetico')

    def test_ignorable_e_identificadores_no_cambian_texto_o_orden(self):
        cuerpo=parrafo(' 00123 ')+ '<w:tbl><w:tr><w:tc>'+parrafo('Texto de celda')+'</w:tc></w:tr></w:tbl>'
        sin=self.inspeccionar(partes(cuerpo))
        con=cuerpo.replace('<w:p>','<w:p w14:paraId="ABCDEF12" w14:textId="77777777">').replace(
            '<w:tr>','<w:tr w14:paraId="ABCDEF12" w14:textId="77777777">')
        r=self.inspeccionar(documento(con))
        self.assertIs(r.estado,E.DOCUMENTO_VALIDADO_EN_ALCANCE)
        self.assertEqual([p.texto for p in r.parrafos],[p.texto for p in sin.parrafos])
        self.assertEqual([p.referencia.ruta_xml for p in r.parrafos],[p.referencia.ruta_xml for p in sin.parrafos])
        self.assertIs(r.tablas[0].filas[0].celdas[0].parrafos[0],r.parrafos[1])
        self.assertNotEqual(r.identidad.sha256,sin.identidad.sha256)
        self.assertNotIn('ABCDEF12',str(asdict(r)))
        self.assertIn('declaracion_mc_ignorable_sin_procesamiento',[d.codigo for d in r.operaciones_omitidas])
        self.assertIn('identificadores_word2010_no_interpretados',[d.codigo for d in r.operaciones_omitidas])

    def test_id_opaco_repetido_no_deduplica_parrafos(self):
        cuerpo=''.join('<w:p w14:paraId="00000001" w14:textId="00000001"><w:r><w:t>'+t+'</w:t></w:r></w:p>'
                       for t in ('uno','dos','tres'))
        r=self.inspeccionar(documento(cuerpo,ignorable=None))
        self.assertIs(r.estado,E.DOCUMENTO_VALIDADO_EN_ALCANCE)
        self.assertEqual([p.texto for p in r.parrafos],['uno','dos','tres'])
        self.assertEqual([p.referencia.parrafo for p in r.parrafos],[1,2,3])

    def test_prefijo_es_alias_del_namespace_no_su_identidad(self):
        cuerpo='<w:p ed:paraId="1234ABCD"><w:r><w:t>literal</w:t></w:r></w:p>'
        r=self.inspeccionar(documento(cuerpo,ignorable='ed',namespaces={'mc':MC,'ed':W14}))
        self.assertIs(r.estado,E.DOCUMENTO_VALIDADO_EN_ALCANCE)
        self.assertEqual(r.parrafos[0].texto,'literal')

    def test_todos_los_namespaces_declarables_solo_son_declaraciones(self):
        from spica.adquisicion.verificacion.docx._extraccion import NAMESPACES_DECLARABLES
        namespaces={'mc':MC,**{'n'+str(i):u for i,u in enumerate(sorted(NAMESPACES_DECLARABLES))}}
        r=self.inspeccionar(documento(namespaces=namespaces,ignorable=' '.join(k for k in namespaces if k!='mc')))
        self.assertIs(r.estado,E.DOCUMENTO_VALIDADO_EN_ALCANCE)

    def test_id_en_contexto_invalido_o_formato_no_admitido_se_rechaza(self):
        for etiqueta in ('body','r','t','tbl'):
            p=documento()
            apertura=('<w:'+etiqueta+(' xml:space="preserve"' if etiqueta=='t' else '')+'>').encode()
            p['word/document.xml']=p['word/document.xml'].replace(
                apertura,apertura[:-1]+b' w14:paraId="1234ABCD">')
            if etiqueta=='tbl':p=documento('<w:tbl w14:paraId="1234ABCD"/>')
            with self.subTest(etiqueta=etiqueta):
                self.assertIn(b'w14:paraId="1234ABCD"',p['word/document.xml'])
                self.assertIs(self.inspeccionar(p).estado,E.DOCUMENTO_RECHAZADO)
        for valor in ('','1','1234567','123456789','GGGGGGGG',' 1234ABCD','<nodo/>'):
            with self.subTest(valor=valor):
                p=documento('<w:p w14:textId="'+escape(valor,quote=True)+'"><w:r><w:t>x</w:t></w:r></w:p>')
                self.assertIs(self.inspeccionar(p).estado,E.DOCUMENTO_RECHAZADO)

    def test_ignorable_fuera_de_raiz_y_prefijos_invalidos_se_rechazan(self):
        for cuerpo in ('<w:p mc:Ignorable="w14"><w:r><w:t>x</w:t></w:r></w:p>',
                       '<w:tbl mc:Ignorable="w14"/>'):
            self.assertIs(self.inspeccionar(documento(cuerpo)).estado,E.DOCUMENTO_RECHAZADO)
        for valor in ('','w14 w14','noDeclarado','w14:elemento'):
            with self.subTest(valor=valor):self.assertIs(self.inspeccionar(documento(ignorable=valor)).estado,E.DOCUMENTO_RECHAZADO)

    def test_prefijos_falsos_reasignados_o_de_otra_parte_no_habilitan_atributos(self):
        p=documento(namespaces={'mc':MC,'w14':'urn:fixture:no-admitido'})
        self.assertIs(self.inspeccionar(p).estado,E.DOCUMENTO_RECHAZADO)
        p=documento('<w:p xmlns:w14="urn:fixture:otra-cosa" w14:paraId="1234ABCD"><w:r><w:t>x</w:t></w:r></w:p>')
        self.assertIs(self.inspeccionar(p).estado,E.INSPECCION_INCOMPLETA)
        p=documento(ignorable='ed')
        agregar(p,'word/styles.xml',f'<w:styles xmlns:w="{W}" xmlns:ed="{W14}"/>',paquete.FIJOS['word/styles.xml'][0],'styles')
        self.assertIs(self.inspeccionar(p).estado,E.DOCUMENTO_RECHAZADO)

    def test_namespace_declarado_no_habilita_elementos_atributos_o_reglas_mc(self):
        cuerpos=('<w14:extension>'+parrafo('no promover')+'</w14:extension>',
                 '<w:p w14:otraCosa="1234ABCD"><w:r><w:t>no promover</w:t></w:r></w:p>',
                 '<w14:paraId>'+parrafo('no promover')+'</w14:paraId>')
        for cuerpo in cuerpos:
            with self.subTest(cuerpo=cuerpo):
                r=self.inspeccionar(documento(cuerpo));self.assertIs(r.estado,E.INSPECCION_INCOMPLETA);self.assertEqual(r.parrafos,())
        for nombre in ('ProcessContent','MustUnderstand','PreserveElements','PreserveAttributes'):
            p=documento();p['word/document.xml']=p['word/document.xml'].replace(b'<w:document ',('<w:document mc:'+nombre+'="w14" ').encode())
            self.assertIs(self.inspeccionar(p).estado,E.INSPECCION_INCOMPLETA)

    def test_campos_simples_y_complejos_nunca_promueven_cache(self):
        cuerpos=(
            '<w:p><w:fldSimple w:instr="DATE"><w:r><w:t>CACHE_FICTICIO</w:t></w:r></w:fldSimple></w:p>',
            '<w:p><w:fldSimple w:instr="INSTRUCCION_NO_RECONOCIDA"><w:r><w:t>CACHE_FICTICIO</w:t></w:r></w:fldSimple></w:p>',
            '<w:p><w:r><w:fldChar w:fldCharType="begin"/><w:instrText>DDE programa_ficticio</w:instrText>'
            '<w:fldChar w:fldCharType="separate"/><w:t>CACHE_FICTICIO</w:t><w:fldChar w:fldCharType="end"/></w:r></w:p>')
        for cuerpo in cuerpos:
            with self.subTest(cuerpo=cuerpo[:30]):
                r=self.inspeccionar(documento(cuerpo));self.assertIs(r.estado,E.INSPECCION_INCOMPLETA);self.assertEqual(r.parrafos,())

    def test_revisiones_y_cambios_de_formato_no_eligen_version(self):
        cuerpos=('<w:ins w:author="AUTOR_FICTICIO">'+parrafo('insertado')+'</w:ins>',
                 '<w:del><w:p><w:r><w:delText>eliminado</w:delText></w:r></w:p></w:del>',
                 '<w:ins w:id="1">'+parrafo('insertado')+'</w:ins><w:del w:id="1">'+parrafo('eliminado')+'</w:del>',
                 '<w:moveFrom>'+parrafo('origen')+'</w:moveFrom><w:moveTo>'+parrafo('destino')+'</w:moveTo>',
                 '<w:p><w:pPr><w:pPrChange><w:pPr/></w:pPrChange></w:pPr><w:r><w:t>x</w:t></w:r></w:p>',
                 '<w:p><w:r><w:rPr><w:rPrChange><w:rPr/></w:rPrChange></w:rPr><w:t>x</w:t></w:r></w:p>')
        for cuerpo in cuerpos:
            with self.subTest(cuerpo=cuerpo[:30]):
                r=self.inspeccionar(documento(cuerpo));self.assertIs(r.estado,E.INSPECCION_INCOMPLETA);self.assertEqual(r.parrafos,())
                self.assertNotIn('AUTOR_FICTICIO',repr(r))

    def test_sdt_alternativas_y_contenido_anidado_desconocido_no_se_aplanan(self):
        cuerpos=('<w:sdt><w:sdtContent>'+parrafo('contenedor')+'</w:sdtContent></w:sdt>',
                 '<mc:AlternateContent><mc:Choice Requires="w14">'+parrafo('opcion')+'</mc:Choice>'
                 '<mc:Fallback>'+parrafo('alternativa')+'</mc:Fallback></mc:AlternateContent>',
                 '<w:estructuraDesconocida>'+parrafo('no promover')+'</w:estructuraDesconocida>')
        for cuerpo in cuerpos:
            with self.subTest(cuerpo=cuerpo[:30]):
                r=self.inspeccionar(documento(cuerpo));self.assertIs(r.estado,E.INSPECCION_INCOMPLETA);self.assertEqual(r.parrafos,())

    def test_xml_malformado_dtd_y_limite_de_namespaces_siguen_bloqueados(self):
        p=documento();p['word/document.xml']=p['word/document.xml'][:-4]
        self.assertIs(self.inspeccionar(p).estado,E.DOCUMENTO_RECHAZADO)
        p=documento();p['word/document.xml']=b'<!DOCTYPE w:document [<!ENTITY x "no">]>'+p['word/document.xml']
        self.assertIs(self.inspeccionar(p).estado,E.DOCUMENTO_RECHAZADO)
        p=documento(namespaces={'mc':MC,'w14':W14,**{'n'+str(i):'urn:fixture:'+str(i) for i in range(65)}})
        r=self.inspeccionar(p)
        self.assertIs(r.estado,E.INSPECCION_INCOMPLETA)
        self.assertIn('limite_namespaces_raiz',[d.codigo for d in r.operaciones_omitidas])

    def test_hipervinculos_pasivos_y_externas_prohibidas_conservan_politica(self):
        p=documento('<w:p>'+enlace()+'</w:p>');relacion(p)
        r=self.inspeccionar(p)
        self.assertIs(r.estado,E.DOCUMENTO_VALIDADO_EN_ALCANCE)
        self.assertEqual(r.parrafos[0].texto,'Texto local');self.assertEqual(len(r.hipervinculos_omitidos),1)
        p=documento('<w:p>'+enlace()+'</w:p>');relacion(p,tipo=paquete.R+'/image')
        self.assertIs(self.inspeccionar(p).estado,E.DOCUMENTO_RECHAZADO)

    def test_crc_deflate_y_limites_no_se_relajan_por_metadatos(self):
        p=documento();b=bytearray(zip_docx(p));b[b.index(b'Texto literal')]^=1
        self.assertIs(inspeccionar_docx_bytes(bytes(b)).estado,E.DOCUMENTO_RECHAZADO)
        b=bytearray(zip_docx(p,compresion=ZIP_DEFLATED))
        with ZipFile(BytesIO(b)) as z:i=z.getinfo('word/document.xml')
        ln,le=struct.unpack_from('<HH',b,i.header_offset+26);inicio=i.header_offset+30+ln+le
        self.assertTrue(b[inicio]&1);b[inicio]&=0xfe
        self.assertIs(inspeccionar_docx_bytes(bytes(b)).estado,E.DOCUMENTO_RECHAZADO)
        base=LimitesDOCX()
        for limites in (replace(base,max_archivo=10),replace(base,zip=replace(base.zip,max_nodos_xml=2)),replace(base,max_bytes_auxiliares=32)):
            self.assertIs(self.inspeccionar(p,limites=limites).estado,E.INSPECCION_INCOMPLETA)

    def test_cancelacion_y_ausencia_de_acceso_externo(self):
        evento=Event();evento.set()
        self.assertIs(self.inspeccionar(cancelacion=evento).estado,E.INSPECCION_INCOMPLETA)
        evento.clear();original=paquete.detectar
        def cancelar(*args,**kw):evento.set();return original(*args,**kw)
        with patch.object(paquete,'detectar',side_effect=cancelar):self.assertIs(self.inspeccionar(cancelacion=evento).estado,E.INSPECCION_INCOMPLETA)
        datos=zip_docx(documento())
        with patch('builtins.open',side_effect=AssertionError('archivo')),patch('pathlib.Path.open',side_effect=AssertionError('archivo')), \
             patch('socket.socket.connect',side_effect=AssertionError('red')),patch('socket.getaddrinfo',side_effect=AssertionError('DNS')), \
             patch('subprocess.Popen',side_effect=AssertionError('proceso')),patch('sqlite3.connect',side_effect=AssertionError('sqlite')):
            self.assertIs(inspeccionar_docx_bytes(datos).estado,E.DOCUMENTO_VALIDADO_EN_ALCANCE)

    def test_original_sintetico_se_preserva_y_resultado_es_determinista(self):
        raiz=Path(tempfile.gettempdir()).resolve()/('spica-84hc-test-'+uuid4().hex);raiz.mkdir(mode=0o755)
        try:
            p=raiz/'sintetico.docx';datos=zip_docx(documento());p.write_bytes(datos);antes=p.stat()
            r=inspeccionar_docx_archivo(p,directorio_autorizado=raiz,sha256_esperado=hashlib.sha256(datos).hexdigest())
            self.assertIs(r.estado,E.DOCUMENTO_VALIDADO_EN_ALCANCE);self.assertTrue(r.conservacion_comprobada)
            self.assertEqual(p.read_bytes(),datos);despues=p.stat()
            self.assertEqual((antes.st_mode,antes.st_ino,antes.st_mtime_ns),(despues.st_mode,despues.st_ino,despues.st_mtime_ns))
            self.assertEqual({p.name for p in raiz.iterdir()},{'sintetico.docx'})
            self.assertEqual(inspeccionar_docx_bytes(datos),inspeccionar_docx_bytes(datos))
        finally:
            assert raiz.resolve().parent==Path(tempfile.gettempdir()).resolve() and raiz.name.startswith('spica-84hc-test-')
            shutil.rmtree(raiz)


if __name__=='__main__':unittest.main()
