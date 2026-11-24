"""Recepción M26 con contratos nativos y DOCX inventados; cero datos operativos."""

from dataclasses import FrozenInstanceError, replace
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from herramientas import primer_uso_m26_rc16 as v
from herramientas import vinculo_documental_rc15 as r15
from herramientas.vinculacion_documental import CotejadorDocumental, Comprobacion
from spica.coordinacion import RestriccionPropagada
from spica.interoperabilidad.adaptadores import DiagnosticoAdaptacion as D, NivelDiagnostico as N
from spica.interoperabilidad.modelos import EstadoAptitud as E
from spica.calidad.aplicabilidad.modelos import NivelEvidencia
from spica.metadatos_documentales import RestriccionUso, evaluar_uso, OperacionUso
from test_vinculo_documental_rc15 import escenario, PROC, BLOQUEO
from test_metadatos_documentales import expediente


def con_entrada(s, e):
    a=replace(s.artefacto, entrada_perfil=replace(s.artefacto.entrada_perfil, entrada=e))
    return replace(s,artefacto=a,operacion=replace(s.operacion,proyecto=e.proyecto,entradas=(e,)))


def sin_edicion(s):
    e=s.artefacto.entrada_perfil.entrada
    e=replace(e,version_contenido=None,recurso=replace(e.recurso,version_institucional=None))
    a=s.expediente.afirmaciones[0]
    a=replace(a,fuente=replace(a.fuente,version_producto=None))
    return replace(con_entrada(s,e),producto=replace(s.producto,version=None),expediente=expediente(a))


def informe_nativo(s,c,revision='sintetica'):
    if revision=='sintetica':
        revision=r15.RevisionVinculoRC15(s,'urn:fixture:revision-no-autenticada-rc16',PROC)
    return r15.vincular_producto_rc15(s,revision=revision,cotejador=c)


class PrimerUsoM26RC16Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='spica-rc16-')
        self.raiz=Path(self.temp.name).resolve()
        self.addCleanup(self.limpiar)
        self.s,self.revision,self.c,self.bytes=escenario(self.raiz)
        self.i=informe_nativo(self.s,self.c)

    def limpiar(self):
        self.temp.cleanup()
        self.assertFalse(self.raiz.exists())

    def ejecutar(self,informe=None,s=None):
        return v.comprobar_primer_uso_m26(self.i if informe is None else informe,
            solicitud_esperada=self.s if s is None else s,cotejador=self.c)

    def test_coherencia_y_recepcion_conservan_ambos_informes_completos(self):
        with patch.object(r15,'vincular_producto_rc15',wraps=r15.vincular_producto_rc15) as llamada:
            r=self.ejecutar()
        llamada.assert_called_once()
        self.assertIs(r.aportado,self.i)
        self.assertIsNot(r.actual,self.i)
        self.assertEqual(r.actual,self.i)
        self.assertIs(r.estado_coherencia,E.APTO_ESTRUCTURALMENTE)
        self.assertIs(r.estado_uso,E.PENDIENTE_DE_EVIDENCIA)
        self.assertIs(r.actual.expediente_producto.afirmaciones[0].nivel,NivelEvidencia.DECLARADA)
        self.assertEqual(r.restricciones,self.i.restricciones+r.actual.restricciones)
        self.assertEqual(self.c.controles[0].ruta.read_bytes(),self.bytes)

    def test_none_es_legitimo_preserva_identidad_y_no_infiere_edicion(self):
        s=sin_edicion(self.s)
        i=informe_nativo(s,self.c)
        r=self.ejecutar(i,s)
        self.assertIs(r.estado_coherencia,E.PENDIENTE_DE_EVIDENCIA)
        self.assertIsNone(r.actual.solicitud.producto.version)
        self.assertEqual(r.actual.solicitud.producto.identificador,self.s.producto.identificador)
        self.assertIsNone(r.actual.expediente_producto)
        self.assertIsNone(r.actual.cotejo)
        # Consulta y física documental son dimensiones separadas: ninguna
        # acredita la relación de edición desconocida del producto.
        uso=evaluar_uso(s.expediente,OperacionUso.CONSULTA_DOCUMENTAL,(s.afirmacion_id,))
        self.assertTrue(uso.requisitos_documentales_satisfechos)
        fisica=self.c.cotejar(s.control_id,s.expediente,(s.afirmacion_id,))
        self.assertIs(fisica.comparacion_control,Comprobacion.SATISFECHA)
        self.assertIsNone(s.producto.version)
        self.assertFalse(r.uso_documental_acreditado)

    def test_revision_incompatible_o_ausente_conserva_causas(self):
        otra=r15.RevisionVinculoRC15(replace(self.s,control_id='otro-control'),'urn:fixture:otro',PROC)
        for revision in (None,otra):
            with self.subTest(revision=revision is None):
                i=informe_nativo(self.s,self.c,revision)
                r=self.ejecutar(i)
                self.assertIsNot(r.estado_coherencia,E.APTO_ESTRUCTURALMENTE)
                self.assertTrue(all(d in r.diagnosticos_completos for d in i.diagnosticos))

    def test_documento_alterado_no_borra_lectura_anterior_ni_acredita_uso(self):
        self.c.controles[0].ruta.write_bytes(self.bytes+b'cambio-fixture')
        r=self.ejecutar()
        self.assertIs(r.aportado.cotejo.comparacion_control,Comprobacion.SATISFECHA)
        self.assertIs(r.actual.cotejo.comparacion_control,Comprobacion.FALLIDA)
        self.assertIs(r.estado_coherencia,E.PENDIENTE_DE_EVIDENCIA)
        self.assertIsNone(r.actual.expediente_producto)
        self.assertFalse(r.uso_documental_acreditado)

    def test_finalidad_no_admitida_y_revision_distinta_no_se_reinterpretan(self):
        for s in (replace(self.s,finalidad='finalidad-ajena'),
                  con_entrada(self.s,replace(self.s.artefacto.entrada_perfil.entrada,revision='otra-revision'))):
            with self.subTest(finalidad=s.finalidad), patch.object(CotejadorDocumental,'cotejar',side_effect=AssertionError('no leer')):
                r=self.ejecutar(s=s)
            self.assertIs(r.estado_coherencia,E.INCOMPATIBLE)
            self.assertIsNone(r.actual)
            self.assertIs(r.aportado,self.i)
        s=replace(self.s,finalidad='finalidad-ajena')
        self.assertIs(self.ejecutar(informe_nativo(s,self.c),s).estado_coherencia,E.INCOMPATIBLE)

    def test_bloqueo_heredado_y_local_sigue_estructurado(self):
        e=self.s.artefacto.entrada_perfil.entrada
        for origen in ('proyecto','artefacto','operacion'):
            if origen=='proyecto':
                p=replace(e.proyecto,restricciones=e.proyecto.restricciones+(BLOQUEO,))
                s=con_entrada(self.s,replace(e,proyecto=p))
            elif origen=='artefacto':
                s=replace(self.s,artefacto=replace(self.s.artefacto,restricciones_adicionales=(BLOQUEO,)))
            else:
                s=replace(self.s,operacion=replace(self.s.operacion,restricciones_adicionales=(BLOQUEO,)))
            i=informe_nativo(s,self.c)
            r=self.ejecutar(i,s)
            self.assertIs(r.estado_coherencia,E.INCOMPATIBLE)
            bloqueos=[x for x in r.restricciones if x.restriccion==BLOQUEO]
            self.assertTrue(bloqueos)
            self.assertTrue(all(x.origenes and x.restriccion.tipo==BLOQUEO.tipo for x in bloqueos))

    def test_informe_ausente_expediente_aislado_y_dictamen_no_sustituyen_unidad(self):
        for valor in (None,self.i.expediente_producto,{},True,lambda:True):
            with self.subTest(tipo=type(valor).__name__), patch.object(CotejadorDocumental,'cotejar',side_effect=AssertionError('no leer')):
                with self.assertRaises(TypeError):
                    v.comprobar_primer_uso_m26(valor,solicitud_esperada=self.s,cotejador=self.c)

    def test_restricciones_omitidas_o_rebajadas_no_se_admiten(self):
        for rs in ((),(RestriccionPropagada(BLOQUEO,('aporte-ajeno',)),)):
            i=replace(self.i,restricciones=rs)
            r=self.ejecutar(i)
            self.assertIs(r.estado_coherencia,E.INCOMPATIBLE)
            self.assertEqual(r.aportado.restricciones,rs)
            self.assertEqual(r.actual.restricciones,self.i.restricciones)
            self.assertTrue(all(x in r.restricciones for x in self.i.restricciones))

    def test_campos_documentales_truncados_no_producen_coherencia(self):
        for campo in ('uso_documental','cotejo','expediente_producto'):
            r=self.ejecutar(replace(self.i,**{campo:None}))
            self.assertIsNot(r.estado_coherencia,E.APTO_ESTRUCTURALMENTE)
        r=self.ejecutar(replace(self.i,diagnosticos=()))
        self.assertIs(r.estado_coherencia,E.INCOMPATIBLE)

    def test_pendientes_originales_no_desaparecen_por_nueva_lectura_favorable(self):
        causa=D('pendiente_antecedente_fixture','revision',N.FALTANTE)
        i=replace(self.i,diagnosticos=self.i.diagnosticos+(causa,))
        r=self.ejecutar(i)
        self.assertIs(r.actual.estado,E.APTO_ESTRUCTURALMENTE)
        self.assertIn(causa,r.diagnosticos_completos)
        self.assertIs(r.estado_coherencia,E.PENDIENTE_DE_EVIDENCIA)

    def test_licencia_desconocida_y_restriccion_documental_se_conservan(self):
        a=self.s.expediente.afirmaciones[0]
        a=replace(a,restricciones=(RestriccionUso.DERECHO_NO_COMPROBADO,))
        s=replace(self.s,expediente=expediente(a))
        r=self.ejecutar(informe_nativo(s,self.c),s)
        self.assertIsNone(r.actual.expediente_producto.producto.restricciones_licencia)
        self.assertEqual(r.aportado.solicitud.expediente.afirmaciones[0].restricciones,a.restricciones)
        self.assertIn('restriccion.derecho_no_comprobado',tuple(d.codigo for d in r.actual.uso_documental.diagnosticos))
        self.assertFalse(r.ejecucion_autorizada)

    def test_humano_autenticidad_ciencia_y_permisos_siguen_no_acreditados(self):
        r=self.ejecutar()
        for campo in ('uso_documental_acreditado','revision_humana_acreditada','autenticidad_institucional',
                      'validacion_cientifica','ejecucion_autorizada'):
            self.assertIs(getattr(r,campo),False)
            with self.assertRaises(TypeError):replace(r,**{campo:True})
        with self.assertRaises(TypeError):bool(r)
        with self.assertRaises(FrozenInstanceError):r.version='otra'
        self.assertIs(r.estado_uso,E.PENDIENTE_DE_EVIDENCIA)

    def test_dos_proyectos_mismos_bytes_no_intercambian_informes(self):
        rb=self.raiz/'proyecto-B';rb.mkdir()
        s,rev,c,datos=escenario(rb,'proyecto-rc16-B')
        self.assertEqual(datos,self.bytes)
        i=informe_nativo(s,c)
        r=v.comprobar_primer_uso_m26(i,solicitud_esperada=self.s,cotejador=c)
        self.assertIs(r.estado_coherencia,E.INCOMPATIBLE)
        self.assertIsNone(r.actual)
        propio=v.comprobar_primer_uso_m26(i,solicitud_esperada=s,cotejador=c)
        self.assertIs(propio.estado_coherencia,E.APTO_ESTRUCTURALMENTE)
        self.assertFalse(propio.uso_documental_acreditado)

    def test_determinismo_diagnostico_publico_y_compatibilidad_rc15(self):
        r=self.ejecutar()
        self.assertEqual(r,self.ejecutar())
        self.assertEqual(self.i,informe_nativo(self.s,self.c))
        publico=repr(r.diagnostico_publico())
        for literal in (str(self.raiz),self.s.producto.identificador,self.i.revision.responsable_ref):
            self.assertNotIn(literal,publico)

    def test_tipos_anidados_incompletos_se_rechazan_sin_lectura(self):
        for kw in ({'restricciones':[]},{'diagnosticos':('texto',)},{'uso_documental':{}},{'solicitud':None}):
            with self.subTest(campos=tuple(kw)), patch.object(CotejadorDocumental,'cotejar',side_effect=AssertionError('no leer')):
                with self.assertRaises(TypeError):self.ejecutar(replace(self.i,**kw))

    def test_barrera_de_proceso_en_piloto_rc16(self):
        programa=r'''
import os,sys,tempfile
from pathlib import Path
sys.path[:0]=sys.argv[1:]
with tempfile.TemporaryDirectory(prefix='spica-rc16-barrera-') as n:
 raiz=Path(n).resolve()
 def guardia(e,a):
  if e.startswith(('socket.','sqlite3.')) or e in ('subprocess.Popen','os.system'):raise RuntimeError('efecto_prohibido')
  if e=='open' and not isinstance(a[0],int):
   p=Path(os.fsdecode(a[0])).resolve()
   if 'spica_datos' in str(p).lower():raise RuntimeError('lectura_operativa')
   if a[2] & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND) and not p.is_relative_to(raiz):raise RuntimeError('escritura_ajena')
 sys.addaudithook(guardia)
 if os.environ['RC16_ORDEN']=='inverso':import herramientas.primer_uso_m26_rc16
 from test_vinculo_documental_rc15 import escenario
 from test_primer_uso_m26_rc16 import informe_nativo
 from herramientas.primer_uso_m26_rc16 import comprobar_primer_uso_m26
 s,rev,c,b=escenario(raiz)
 i=informe_nativo(s,c)
 r=comprobar_primer_uso_m26(i,solicitud_esperada=s,cotejador=c)
 assert r.actual.expediente_producto is not None and not r.uso_documental_acreditado
 assert c.controles[0].ruta.read_bytes()==b
assert not raiz.exists()
print('RC16_INFORME_COMPLETO_SIN_EFECTOS_OPERATIVOS')
'''
        for orden in ('directo','inverso'):
            p=subprocess.run([sys.executable,'-B','-I','-c',programa,str(Path(__file__).resolve().parents[1]/'src'),
                str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parent)],
                env=dict(os.environ,RC16_ORDEN=orden,PYTHONDONTWRITEBYTECODE='1'),capture_output=True,text=True,timeout=30)
            self.assertEqual(p.returncode,0,p.stderr)
            self.assertEqual(p.stdout.strip(),'RC16_INFORME_COMPLETO_SIN_EFECTOS_OPERATIVOS')


if __name__=='__main__':unittest.main()
