"""Cotejo físico/documental sintético; nunca abre evidencias institucionales."""

from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timezone
import hashlib
import io
from pathlib import Path
import stat
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from herramientas import vinculacion_documental as v
from spica.adquisicion.catalogo.modelos import ProcedenciaCatalogo
from spica.calidad.modelos_cientificos import ReferenciaCientifica
from spica.calidad.aplicabilidad.modelos import NivelEvidencia
from spica.metadatos_documentales import (
    FuenteDocumental, ReferenciaCelda, TipoDocumento as T, FormaDeclaracion,
    PresenciaInformacion as P, RelacionAfirmaciones, TipoRelacion, RestriccionUso,
    localizar, evaluar_uso, OperacionUso,
)
from test_metadatos_documentales import afirmacion, expediente
from test_inspector_docx import partes, parrafo, zip_docx
from test_diagnostico_xlsx_84e import libro
from test_hipervinculos_docx import enlace, relacion

C = v.Comprobacion
E = v.EstadoCotejo


class VinculacionDocumentalTests(unittest.TestCase):
    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory(prefix='spica-vinculacion-')
        self.raiz = Path(self.temporal.name).resolve()
        self.addCleanup(self.limpiar)
        self.ruta = self.raiz/'documento.bin'  # La extensión no demuestra formato.
        self.procedencia = ProcedenciaCatalogo('control sintetico previo',
            datetime(2000, 1, 1, tzinfo=timezone.utc), 'fixture acotado', 'referencia independiente de la afirmacion')
        self.preparar(zip_docx(partes(parrafo(' literal 001 '))), T.DOCX, ' literal 001 ')

    def limpiar(self):
        assert self.raiz.parent == Path(tempfile.gettempdir()).resolve()
        assert self.raiz.name.startswith('spica-vinculacion-')
        self.temporal.cleanup()

    def preparar(self, datos, tipo=T.DOCX, texto=' literal 001 '):
        # El control del fixture se establece antes de recibir la afirmación.
        self.datos = datos
        ref = ReferenciaCientifica('doc-a', 'emisor ficticio', 'documento sintetico',
            'control local de pruebas', sha256_referencia=hashlib.sha256(datos).hexdigest())
        self.control = v.ControlArchivo('control-a', self.ruta, self.raiz, tipo,
            ref, len(datos), self.procedencia)
        self.ruta.write_bytes(datos)
        self.a = afirmacion(f=FuenteDocumental(ref, tipo), contenido=texto)
        if tipo is T.XLSX:
            self.a = self.con_referencia(ReferenciaCelda('doc-a', ref.sha256_referencia, 'Hoja sintetica', 'A1'))

    def con_referencia(self, ref):
        return replace(self.a, referencia=ref, evidencia=replace(self.a.evidencia, localizacion=localizar(ref)))

    def ejecutar(self, a=None, control=None, *, e=None, seleccion=None):
        a = a if a is not None else self.a
        return v.CotejadorDocumental((control or self.control,)).cotejar('control-a',
            e if e is not None else expediente(a), seleccion if seleccion is not None else (a.identificador,))

    def test_docx_fisico_referencia_literal_y_repeticion_determinista(self):
        r = self.ejecutar()
        self.assertEqual(r, self.ejecutar())
        self.assertEqual((r.tamano_observado, r.sha256_calculado),
            (len(self.datos), hashlib.sha256(self.datos).hexdigest()))
        self.assertIs(r.ruta, C.SATISFECHA)
        self.assertIs(r.comparacion_control, C.SATISFECHA)
        self.assertIs(r.estructura, C.SATISFECHA)
        self.assertIs(r.conservacion, C.SATISFECHA)
        self.assertEqual(r.firma_inicial, r.firma_final)
        self.assertIs(r.cotejos[0].contenido, E.COINCIDE)
        self.assertEqual(r.cotejos[0].observado, ' literal 001 ')
        self.assertEqual(self.ruta.read_bytes(), self.datos)

    def test_xlsx_celda_unicode_y_espacios_sin_conversion(self):
        self.preparar(libro('<c r="A1" t="inlineStr"><is><t> 000 °C </t></is></c>'), T.XLSX, ' 000 °C ')
        r = self.ejecutar()
        self.assertIs(r.cotejos[0].contenido, E.COINCIDE)
        self.assertEqual(r.cotejos[0].observado, ' 000 °C ')
        self.assertEqual((r.inspector, r.version_inspector), ('diagnostico_xlsx_84e', '0.1.0'))
        self.assertIs(r.conservacion, C.SATISFECHA)

    def test_controles_requieren_referencia_previa_no_hash_de_la_afirmacion(self):
        with self.assertRaises(ValueError):
            v.CotejadorDocumental(())
        with self.assertRaises(ValueError):
            replace(self.control, procedencia=replace(self.procedencia, evidencia=None))
        with self.assertRaises(ValueError):
            replace(self.control, referencia=replace(self.control.referencia, sha256_referencia=None))
        for kw in ({'sha256_esperado':self.a.fuente.sha256}, {'verificado':True}, {'ejecucion_autorizada':True}):
            with self.subTest(kw=tuple(kw)), self.assertRaises(TypeError):
                v.CotejadorDocumental((self.control,)).cotejar('control-a', expediente(self.a), ('a',), **kw)

    def test_politica_rechaza_controles_duplicados_y_selecciones_invalidas(self):
        for controles in ((self.control,self.control), (self.control,replace(self.control, identificador='otro'))):
            with self.subTest(controles=len(controles)), self.assertRaises(ValueError):
                v.CotejadorDocumental(controles)
        for sel in ((),('a','a'),('ajena',)):
            with self.subTest(sel=sel), self.assertRaises(ValueError):
                self.ejecutar(seleccion=sel)
        with self.assertRaises(ValueError):
            v.CotejadorDocumental((self.control,)).cotejar('no-registrado', expediente(self.a), ('a',))

    def test_tamano_o_hash_del_control_incorrectos_no_inspeccionan(self):
        ref = replace(self.control.referencia, sha256_referencia='2'*64)
        casos = ((replace(self.control,tamano_esperado=len(self.datos)+1),self.a),
            (replace(self.control,referencia=ref), afirmacion(f=FuenteDocumental(ref,T.DOCX))))
        for control,a in casos:
            with self.subTest(tamano=control.tamano_esperado), patch.object(v,'inspeccionar_docx_bytes') as inspector:
                r=self.ejecutar(a,control)
                inspector.assert_not_called()
                self.assertIs(r.comparacion_control,C.FALLIDA)
                self.assertIs(r.estructura,C.NO_REALIZADA)
                self.assertIs(r.conservacion,C.SATISFECHA)
                self.assertIs(r.cotejos[0].contenido,E.NO_COTEJABLE)

    def test_archivo_alterado_no_lo_autocertifica_su_nombre_o_hash_declarado(self):
        self.ruta.write_bytes(self.datos+b'alteracion sintetica')
        r=self.ejecutar()
        self.assertIs(r.comparacion_control,C.FALLIDA)
        self.assertNotEqual(r.sha256_calculado,self.a.fuente.sha256)
        self.assertIs(r.cotejos[0].contenido,E.NO_COTEJABLE)

    def test_archivo_inexistente_no_inventa_comprobaciones(self):
        r=self.ejecutar(control=replace(self.control,ruta=self.raiz/'ausente'))
        self.assertIs(r.ruta,C.FALLIDA)
        self.assertIsNone(r.sha256_calculado)
        self.assertIs(r.comparacion_control,C.NO_REALIZADA)
        self.assertIs(r.conservacion,C.NO_REALIZADA)

    def test_rutas_fuera_de_raiz_escapes_y_unc_rechazados_sin_abrir(self):
        for ruta in (self.raiz.parent/'fuera', self.raiz/'..'/'fuera', Path('relativa')):
            with self.subTest(ruta=ruta.name), self.assertRaises(ValueError):
                replace(self.control,ruta=ruta)
        if v.os.name=='nt':
            with self.assertRaises(ValueError):
                replace(self.control,raiz=Path(r'\\servidor\recurso'),ruta=Path(r'\\servidor\recurso\documento'))

    def test_enlace_o_reparse_simulado_rechazado_antes_de_lectura(self):
        real=Path.lstat
        def lstat(p,*args,**kw):
            if p==self.ruta:
                s=real(p,*args,**kw)
                return SimpleNamespace(st_mode=s.st_mode,st_file_attributes=stat.FILE_ATTRIBUTE_REPARSE_POINT)
            return real(p,*args,**kw)
        with patch.object(Path,'lstat',lstat), patch.object(v,'_leer') as lector:
            r=self.ejecutar()
            lector.assert_not_called()
        self.assertIs(r.ruta,C.FALLIDA)
        self.assertTrue(any('enlace_o_reparse' in c for c in r.diagnosticos))

    def test_sustitucion_entre_lstat_y_apertura_detectada_por_descriptor(self):
        sustituto=self.raiz/'sustituto'
        sustituto.write_bytes(self.datos)
        real=Path.open
        def abrir(p,*args,**kw):
            if p==self.ruta and sustituto.exists():
                sustituto.replace(self.ruta)
            return real(p,*args,**kw)
        with patch.object(Path,'open',abrir):
            r=self.ejecutar()
        self.assertIs(r.comparacion_control,C.INCOMPLETA)
        self.assertIsNone(r.sha256_calculado)
        self.assertTrue(any('archivo_sustituido' in c for c in r.diagnosticos))

    def test_cambio_despues_de_inspeccionar_descarta_coincidencia(self):
        real=v.inspeccionar_docx_bytes
        def cambiar(*args,**kw):
            inventario=real(*args,**kw)
            self.ruta.write_bytes(self.datos+b'cambio controlado')
            return inventario
        with patch.object(v,'inspeccionar_docx_bytes',cambiar):
            r=self.ejecutar()
        self.assertIs(r.conservacion,C.FALLIDA)
        self.assertIs(r.cotejos[0].contenido,E.NO_COTEJABLE)
        self.assertIsNone(r.cotejos[0].observado)
        self.assertIs(r.cotejos[0].referencia_encontrada,C.SATISFECHA)
        self.assertIn('cotejo_invalidado_por_conservacion_final',r.cotejos[0].diagnosticos)

    def test_referencia_docx_inexistente(self):
        ref=replace(self.a.referencia,ruta_xml=self.a.referencia.ruta_xml.replace('}p[1]','}p[99]'),parrafo=99)
        r=self.ejecutar(self.con_referencia(ref))
        self.assertIs(r.cotejos[0].referencia_encontrada,C.FALLIDA)
        self.assertIn('parrafo_ausente_o_ambiguo',r.cotejos[0].diagnosticos)

    def test_ordinal_global_docx_inconsistente_no_suplido_por_ruta(self):
        r=self.ejecutar(self.con_referencia(replace(self.a.referencia,parrafo=2)))
        self.assertIn('contexto_referencia_docx_inconsistente',r.cotejos[0].diagnosticos)
        self.assertIs(r.cotejos[0].contenido,E.NO_COTEJABLE)

    def test_afirmacion_de_otro_documento_no_abre_archivo(self):
        ref=replace(self.control.referencia,identificador='otro-documento')
        a=afirmacion(f=FuenteDocumental(ref,T.DOCX))
        with patch.object(v,'_leer',side_effect=AssertionError('no leer')) as leer:
            r=self.ejecutar(a)
            leer.assert_not_called()
        self.assertIs(r.ruta,C.NO_REALIZADA)
        self.assertIn('identidad_de_afirmacion_no_corresponde_al_control',r.diagnosticos)

    def test_texto_distinto_no_se_normaliza_para_coincidir(self):
        r=self.ejecutar(replace(self.a,contenido=self.a.contenido.strip()))
        self.assertIs(r.cotejos[0].referencia_encontrada,C.SATISFECHA)
        self.assertIs(r.cotejos[0].contenido,E.DIFIERE)
        self.assertEqual(r.cotejos[0].observado,' literal 001 ')

    def test_restricciones_se_preservan_y_no_se_promueven_respaldos(self):
        a=replace(self.a,restricciones=(RestriccionUso.DERECHO_NO_COMPROBADO,))
        r=self.ejecutar(a)
        self.assertIs(r.cotejos[0].afirmacion,a)
        self.assertEqual(r.cotejos[0].afirmacion.restricciones,a.restricciones)
        self.assertIsNone(a.fuente.integridad)
        self.assertIsNone(a.fuente.inspeccion)
        consulta=evaluar_uso(expediente(a),OperacionUso.CONSULTA_DOCUMENTAL,('a',))
        self.assertFalse(consulta.requisitos_documentales_satisfechos)
        self.assertIs(r.ejecucion_autorizada,False)
        self.assertIs(r.operacion_ejecutada,False)
        with self.assertRaises(TypeError): bool(r)
        with self.assertRaises(TypeError): replace(r,ejecucion_autorizada=True)
        with self.assertRaises(FrozenInstanceError): r.ejecucion_autorizada=True

    def test_parafrasis_no_se_certifica_automaticamente(self):
        r=self.ejecutar(replace(self.a,forma=FormaDeclaracion.PARAFRASIS_CONTROLADA))
        self.assertEqual(r.cotejos[0].observado,self.a.contenido)
        self.assertIs(r.cotejos[0].contenido,E.NO_COTEJABLE)

    def test_ausencia_o_nulo_no_se_infiere_de_lectura_literal(self):
        for presencia,contenido,nivel in ((P.AUSENTE,None,NivelEvidencia.DESCONOCIDA),
                (P.NULO_DECLARADO,' literal 001 ',NivelEvidencia.DECLARADA)):
            a=afirmacion(f=self.a.fuente,presencia=presencia,contenido=contenido,nivel=nivel)
            with self.subTest(presencia=presencia):
                self.assertIs(self.ejecutar(a).cotejos[0].contenido,E.NO_COTEJABLE)

    def test_inspeccion_docx_incompleta_no_coteja_cache(self):
        cuerpo='<w:p><w:fldSimple w:instr="CAMPO"><w:r><w:t>cache</w:t></w:r></w:fldSimple></w:p>'
        self.preparar(zip_docx(partes(cuerpo)))
        r=self.ejecutar()
        self.assertIs(r.comparacion_control,C.SATISFECHA)
        self.assertIs(r.estructura,C.INCOMPLETA)
        self.assertIs(r.cotejos[0].contenido,E.NO_COTEJABLE)
        self.assertTrue(r.limitaciones)

    def test_documento_rechazado_con_hash_correcto_no_es_documento_validado(self):
        self.preparar(b'no es un paquete OOXML')
        r=self.ejecutar()
        self.assertIs(r.comparacion_control,C.SATISFECHA)
        self.assertIs(r.estructura,C.FALLIDA)
        self.assertIs(r.conservacion,C.SATISFECHA)
        self.assertIs(r.cotejos[0].contenido,E.NO_COTEJABLE)

    def test_xlsx_referencia_ausente_formula_y_rango_sin_promocion(self):
        self.preparar(libro('<c r="A1" t="str"><f>1+1</f><v>cache</v></c>'),T.XLSX,'cache')
        self.assertIn('celda_sin_literal_cotejable',self.ejecutar().cotejos[0].diagnosticos)
        for ref,codigo in ((replace(self.a.referencia,rango='B9'),'celda_ausente_o_ambigua'),
                (replace(self.a.referencia,rango='A1:B2'),'rango_no_admitido_en_cotejo_literal'),
                (replace(self.a.referencia,hoja='otra'),'hoja_ausente_o_ambigua')):
            with self.subTest(codigo=codigo):
                r=self.ejecutar(self.con_referencia(ref))
                self.assertIn(codigo,r.cotejos[0].diagnosticos)
                self.assertIs(r.cotejos[0].contenido,E.NO_COTEJABLE)

    def test_rechazo_xlsx_conserva_fallo_sin_cotejo(self):
        self.preparar(libro('<c r="A1"/><c r="A1"/>'),T.XLSX)
        r=self.ejecutar()
        self.assertIs(r.estructura,C.INCOMPLETA)
        self.assertIs(r.cotejos[0].contenido,E.NO_COTEJABLE)
        self.assertIn('inspeccion_xlsx_no_satisfactoria_en_alcance',r.diagnosticos)

    def test_contradiccion_explicita_no_desaparece_por_coincidencia_literal(self):
        a=replace(self.a,evidencia=replace(self.a.evidencia,contradicciones=('conflicto sintetico pendiente de clasificar',)))
        b=replace(a,identificador='b',contenido='otro literal')
        rel=RelacionAfirmaciones('a','b',TipoRelacion.CONTRADICCION,'mismo ambito, declaraciones incompatibles')
        e=expediente(a,b,relaciones=(rel,))
        r=self.ejecutar(e=e,seleccion=('a',))
        self.assertIs(r.cotejos[0].contenido,E.COINCIDE)
        self.assertIn('contradiccion_explicita_conservada_no_resuelta_por_cotejo',r.cotejos[0].diagnosticos)
        uso=evaluar_uso(e,OperacionUso.CONSULTA_DOCUMENTAL,('a',))
        self.assertFalse(uso.requisitos_documentales_satisfechos)
        self.assertFalse(r.ejecucion_autorizada)

    def test_referencias_compartidas_no_se_deduplican_como_afirmaciones(self):
        b=replace(self.a,identificador='b')
        e=expediente(self.a,b)
        r=self.ejecutar(e=e,seleccion=('b','a'))
        self.assertEqual(r,self.ejecutar(e=e,seleccion=('a','b')))
        self.assertEqual(len(r.cotejos),2)
        self.assertTrue(all(c.contenido is E.COINCIDE for c in r.cotejos))
        self.assertIn('referencia_compartida_no_es_corroboracion_independiente',r.diagnosticos)

    def test_salida_del_inspector_con_referencia_duplicada_no_se_acepta(self):
        real=v.inspeccionar_docx_bytes
        def duplicar(*args,**kw):
            r=real(*args,**kw)
            return replace(r,parrafos=r.parrafos+r.parrafos)
        with patch.object(v,'inspeccionar_docx_bytes',duplicar): r=self.ejecutar()
        self.assertIs(r.cotejos[0].referencia_encontrada,C.FALLIDA)

    def test_identidad_devuelta_por_inspector_debe_corresponder_al_snapshot(self):
        real=v.inspeccionar_docx_bytes
        def cambiar_identidad(*args,**kw):
            r=real(*args,**kw)
            return replace(r,identidad=replace(r.identidad,identificador='ajeno'))
        with patch.object(v,'inspeccionar_docx_bytes',cambiar_identidad): r=self.ejecutar()
        self.assertIs(r.estructura,C.FALLIDA)
        self.assertIs(r.cotejos[0].contenido,E.NO_COTEJABLE)
        self.assertIn('identidad_del_snapshot_inspeccionado_inconsistente',r.diagnosticos)

    def test_lectura_final_imposible_no_conserva_coincidencias_provisionales(self):
        real=v._leer
        llamadas=0
        def leer(*args,**kw):
            nonlocal llamadas
            llamadas+=1
            if llamadas==2: raise PermissionError('fallo final sintetico')
            return real(*args,**kw)
        with patch.object(v,'_leer',leer): r=self.ejecutar()
        self.assertIs(r.comparacion_control,C.SATISFECHA)
        self.assertIs(r.conservacion,C.INCOMPLETA)
        self.assertIs(r.cotejos[0].contenido,E.NO_COTEJABLE)
        self.assertIsNone(r.cotejos[0].observado)
        self.assertIs(r.cotejos[0].referencia_encontrada,C.SATISFECHA)
        self.assertIn('cotejo_invalidado_por_conservacion_final',r.cotejos[0].diagnosticos)
        self.assertIn('conservacion_final_no_comprobada',r.diagnosticos)

    def test_errores_no_revelan_rutas_o_mensajes_sensibles(self):
        with patch.object(v,'_leer',side_effect=PermissionError('SECRETO_FICTICIO ruta o credencial')):
            r=self.ejecutar()
        self.assertNotIn('SECRETO_FICTICIO',repr(r))
        self.assertNotIn('SECRETO_FICTICIO',str(r.diagnostico_publico()))
        self.assertNotIn(str(self.raiz),str(r.diagnostico_publico()))
        self.assertIsNone(r.sha256_calculado)
        self.assertIs(r.comparacion_control,C.INCOMPLETA)

    def test_solo_lectura_sin_red_sqlite_o_procesos(self):
        real=io.open
        modos=[]
        def abrir(ruta,mode='r',*args,**kw):
            self.assertEqual(mode,'rb')
            modos.append(mode)
            return real(ruta,mode,*args,**kw)
        with patch('io.open',abrir), patch('socket.socket.connect',side_effect=AssertionError('red')), \
             patch('sqlite3.connect',side_effect=AssertionError('sqlite')), \
             patch('subprocess.Popen',side_effect=AssertionError('proceso')):
            r=self.ejecutar()
        self.assertEqual(modos,['rb','rb'])
        self.assertIs(r.cotejos[0].contenido,E.COINCIDE)
        self.assertEqual(self.ruta.read_bytes(),self.datos)
        self.assertEqual([p.name for p in self.raiz.iterdir()],['documento.bin'])

    def test_interrupcion_cierra_descriptores_y_no_modifica_original(self):
        real=io.open
        abiertos=[]
        def abrir(*args,**kw):
            f=real(*args,**kw); abiertos.append(f); return f
        with patch('io.open',abrir), patch.object(v,'inspeccionar_docx_bytes',side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt): self.ejecutar()
        self.assertEqual(len(abiertos),2)
        self.assertTrue(all(f.closed for f in abiertos))
        self.assertEqual(self.ruta.read_bytes(),self.datos)

    def test_limite_de_archivo_no_se_elude_con_tamano_declarado_pequeno(self):
        self.ruta.write_bytes(b'x'*(v.MAX_ARCHIVO+1))
        with patch.object(v,'inspeccionar_docx_bytes') as inspector:
            r=self.ejecutar()
            inspector.assert_not_called()
        self.assertIsNone(r.sha256_calculado)
        self.assertIs(r.comparacion_control,C.INCOMPLETA)
        self.assertIs(r.cotejos[0].contenido,E.NO_COTEJABLE)

    def test_omisiones_hipervinculos_pasivos_conservadas_sin_destinos(self):
        p=partes('<w:p>'+enlace(texto=' literal 001 ')+'</w:p>')
        relacion(p,destino='https://prohibido.invalid/?token=SECRETO_FICTICIO')
        self.preparar(zip_docx(p))
        r=self.ejecutar()
        self.assertIs(r.cotejos[0].contenido,E.COINCIDE)
        self.assertIn('destinos_externos_docx_omitidos_no_abiertos',r.limitaciones)
        self.assertNotIn('SECRETO_FICTICIO',str(r.diagnostico_publico()))


if __name__=='__main__':
    unittest.main()
