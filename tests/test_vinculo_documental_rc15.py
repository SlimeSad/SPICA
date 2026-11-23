"""M26 acotada: documentos/contextos inventados, sin datos institucionales."""

from dataclasses import FrozenInstanceError, replace
from datetime import date, datetime, timezone
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from herramientas import vinculo_documental_rc15 as v
from herramientas.vinculacion_documental import CotejadorDocumental, ControlArchivo, Comprobacion
from spica.adquisicion.catalogo.modelos import ProductoCatalogo, ProcedenciaCatalogo
from spica.adquisicion.conectores.senamhi.modelos import FUENTE_SENAMHI, PRODUCTO_GBON_RBON_ID
from spica.artefactos.modelos import DescriptorArtefacto, TipoArtefacto, EstadoArtefacto
from spica.calidad.aplicabilidad.modelos import NaturalezaEvidencia, NivelEvidencia, VigenciaDocumento
from spica.calidad.modelos_cientificos import DimensionAplicabilidad, ReferenciaCientifica
from spica.calidad.restricciones import RestriccionQA, TipoRestriccionQA
from spica.contextos import ContextoOperacion, EstadoOperacion, TipoOperacion
from spica.interoperabilidad.modelos import RecursoInteroperable, IdentidadRecurso, EstadoAptitud as E
from spica.interoperabilidad.perfiles import EntradaPerfil, PerfilInformacion
from spica.metadatos_documentales import FuenteDocumental, TipoDocumento, RelacionAfirmaciones, TipoRelacion
from spica.interoperabilidad.adaptadores import DiagnosticoAdaptacion, NivelDiagnostico
from test_contextos_rc1 import proyecto, entrada
from test_inspector_docx import partes, parrafo, zip_docx
from test_metadatos_documentales import afirmacion, expediente, respaldo

FECHA = datetime(2026, 11, 23, tzinfo=timezone.utc)
PROC = ProcedenciaCatalogo('urn:fixture:rc15', FECHA, 'fixture_sintetica', 'antecedente inventado sin aprobacion institucional')
INFO = RestriccionQA('solo-fixture-rc15', TipoRestriccionQA.INFORMATIVA, (), 'Contenido inventado, sin uso cientifico.')
BLOQUEO = RestriccionQA('bloqueo-fixture-rc15', TipoRestriccionQA.BLOQUEO_USO_DEL_RESULTADO,
                       (v.FINALIDAD_RC15,), 'Bloqueo sintetico de esta finalidad.')


def escenario(raiz, project_id='proyecto-rc15-A'):
    # Únicamente la identidad nominal PNDA es real; edición/recurso/documento
    # y revisión son ficticios. No se leen el CSV ni las adquisiciones reales.
    p = proyecto(project_id, 'contexto-'+project_id, restricciones=(INFO,))
    producto = ProductoCatalogo(FUENTE_SENAMHI, PRODUCTO_GBON_RBON_ID, PROC,
                               version='edicion-ficticia-rc15')
    identidad = IdentidadRecurso(FUENTE_SENAMHI, 'urn:fixture:recurso-catalogado-rc15', PRODUCTO_GBON_RBON_ID)
    recurso = RecursoInteroperable(identidad, 'metadatos-fixture-r1', PROC,
                                  version_institucional=producto.version)
    e = entrada(p, recurso=recurso, tipo_recurso='producto_catalogado',
                perfil_estructural='perfil-producto-rc15', version_contenido=producto.version,
                sha256_declarado=None)
    perfil = PerfilInformacion('perfil-producto-rc15', 'r1', e.tipo_recurso, ())
    artefacto = DescriptorArtefacto(EntradaPerfil(e, perfil), TipoArtefacto.PREPARADO,
                                  contenido_id='descripcion-catalogo-fixture-rc15')
    operacion = ContextoOperacion('revision-documental-rc15', p, (e,),
        TipoOperacion.DESCRIPCION_ESTRUCTURAL, v.FINALIDAD_RC15)
    datos = zip_docx(partes(parrafo(PRODUCTO_GBON_RBON_ID)))
    ruta = raiz/'documento-sintetico.docx'
    ruta.write_bytes(datos)
    ref = ReferenciaCientifica('doc-sintetico-rc15', 'emisor-ficticio-no-SENAMHI',
        'Documento de fixture, no institucional', 'urn:fixture:documento-rc15',
        'doc-edicion-fixture', date(2000, 1, 1), hashlib.sha256(datos).hexdigest())
    fuente = FuenteDocumental(ref, TipoDocumento.DOCX, identidad, producto.version,
                              integridad=respaldo(), inspeccion=respaldo())
    a = afirmacion('identidad-producto', fuente, contenido=producto.identificador,
                  concepto='identificador_producto', ambito=v.FINALIDAD_RC15)
    a = replace(a, evidencia=replace(a.evidencia, vigencia=VigenciaDocumento.VIGENTE))
    s = v.SolicitudVinculoRC15(producto, artefacto, operacion, expediente(a), a.identificador, 'control-rc15')
    revision = v.RevisionVinculoRC15(s, 'urn:fixture:responsable-no-autenticado', PROC)
    control = ControlArchivo(s.control_id, ruta, raiz, TipoDocumento.DOCX, ref, len(datos), PROC)
    return s, revision, CotejadorDocumental((control,)), datos


class VinculoDocumentalRC15Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='spica-rc15-')
        self.raiz = Path(self.temp.name).resolve()
        self.addCleanup(self.limpiar)
        self.s, self.revision, self.cotejador, self.datos = escenario(self.raiz)

    def limpiar(self):
        self.temp.cleanup()
        self.assertFalse(self.raiz.exists())

    def ejecutar(self, s=None, revision='actual', cotejador=None):
        s = self.s if s is None else s
        revision = v.RevisionVinculoRC15(s, self.revision.responsable_ref, PROC) if revision == 'actual' else revision
        return v.vincular_producto_rc15(s, revision=revision,
                                       cotejador=self.cotejador if cotejador is None else cotejador)

    def exigir_bloqueado(self, s=None, **kw):
        r = self.ejecutar(s, **kw)
        self.assertIsNone(r.expediente_producto)
        self.assertIsNot(r.estado, E.APTO_ESTRUCTURALMENTE)
        return r

    def con_afirmacion(self, a):
        return replace(self.s, expediente=expediente(a))

    def test_producto_correcto_cotejo_real_y_salida_nativa_sin_promocion(self):
        with patch.object(CotejadorDocumental, 'cotejar', autospec=True,
                          side_effect=CotejadorDocumental.cotejar) as llamada:
            r = self.ejecutar()
        llamada.assert_called_once()
        self.assertIs(r.estado, E.APTO_ESTRUCTURALMENTE)
        self.assertEqual(r.expediente_producto.producto, self.s.producto)
        a = r.expediente_producto.afirmaciones[0]
        self.assertEqual((a.dimension, a.valor, a.nivel),
                         (DimensionAplicabilidad.PRODUCTO, PRODUCTO_GBON_RBON_ID, NivelEvidencia.DECLARADA))
        self.assertIs(r.cotejo.comparacion_control, Comprobacion.SATISFECHA)
        self.assertEqual(r.cotejo.sha256_calculado, hashlib.sha256(self.datos).hexdigest())
        self.assertEqual(self.cotejador.controles[0].ruta.read_bytes(), self.datos)
        self.assertIs(r.expediente_producto.documentos[0], self.s.expediente.afirmaciones[0].evidencia)
        self.assertTrue(r.restricciones)

    def test_producto_inexistente_y_recurso_ajeno_no_se_admiten(self):
        self.exigir_bloqueado(replace(self.s, producto=replace(self.s.producto, identificador='urn:fixture:inexistente')))
        e = self.s.artefacto.entrada_perfil.entrada
        nuevo = replace(e, recurso=replace(e.recurso, identidad=replace(e.recurso.identidad, producto_id='ajeno')))
        a = replace(self.s.artefacto, entrada_perfil=replace(self.s.artefacto.entrada_perfil, entrada=nuevo))
        self.exigir_bloqueado(replace(self.s, artefacto=a))

    def test_proyecto_ajeno_y_entrada_igual_no_canonica(self):
        e = self.s.artefacto.entrada_perfil.entrada
        for otro in (entrada(proyecto('otro', 'otro-contexto')), replace(e)):
            with self.subTest(project_id=otro.proyecto.project_id):
                o = replace(self.s.operacion, proyecto=otro.proyecto, entradas=(otro,))
                self.exigir_bloqueado(replace(self.s, operacion=o))

    def test_finalidad_operacion_y_perfil_desconocidos_sin_lectura(self):
        with patch.object(CotejadorDocumental, 'cotejar', side_effect=AssertionError('lectura indebida')):
            for kw in ({'finalidad':'uso-ajeno'}, {'version_contrato':'9.0.0'},
                       {'operacion':replace(self.s.operacion, proposito='otro-uso')}):
                self.exigir_bloqueado(replace(self.s, **kw))

    def test_revision_ausente_y_de_otro_snapshot(self):
        self.exigir_bloqueado(revision=None)
        self.exigir_bloqueado(replace(self.s, control_id='otro'), revision=self.revision)

    def test_documento_afirmacion_y_control_ausentes(self):
        for kw in ({'expediente':None}, {'afirmacion_id':'ausente'}, {'control_id':'ausente'}):
            with self.subTest(kw=kw):
                self.exigir_bloqueado(replace(self.s, **kw))

    def test_archivo_ausente_no_inventa_integridad(self):
        c = replace(self.cotejador.controles[0], ruta=self.raiz/'no-existe.docx')
        r = self.exigir_bloqueado(cotejador=CotejadorDocumental((c,)))
        self.assertIsNone(r.cotejo.sha256_calculado)

    def test_version_producto_desconocida_incompatible_y_edicion_ajena(self):
        for version in (None, 'otra-edicion'):
            self.exigir_bloqueado(replace(self.s, producto=replace(self.s.producto, version=version)))
        a = self.s.expediente.afirmaciones[0]
        self.exigir_bloqueado(self.con_afirmacion(replace(a, fuente=replace(a.fuente, version_producto='otra'))))

    def test_referencia_alterada_mismo_id_y_sha_no_basta(self):
        a = self.s.expediente.afirmaciones[0]
        for cambios in ({'titulo':'otro-titulo'}, {'version_documento':'otra'}, {'fecha_documento':None}):
            ref = replace(a.fuente.referencia, **cambios)
            b = replace(a, fuente=replace(a.fuente, referencia=ref), evidencia=replace(a.evidencia, referencia=ref))
            self.exigir_bloqueado(self.con_afirmacion(b))

    def test_contenido_fisico_corrupto_se_coteja_de_nuevo(self):
        self.assertIs(self.ejecutar().estado, E.APTO_ESTRUCTURALMENTE)
        self.cotejador.controles[0].ruta.write_bytes(self.datos+b'cambio')
        r = self.exigir_bloqueado()
        self.assertIs(r.cotejo.comparacion_control, Comprobacion.FALLIDA)

    def test_hash_correcto_no_sustituye_inspeccion_o_literal(self):
        a = self.s.expediente.afirmaciones[0]
        from spica.metadatos_documentales import localizar
        otro = replace(a, contenido='otro-identificador')
        self.exigir_bloqueado(self.con_afirmacion(otro))
        # Un DOCX íntegro puede omitir el párrafo referenciado.
        ref = replace(a.referencia, parrafo=2, ruta_xml=a.referencia.ruta_xml.replace('p[1]', 'p[2]'))
        otro = replace(a, referencia=ref, evidencia=replace(a.evidencia, localizacion=localizar(ref)))
        r = self.exigir_bloqueado(self.con_afirmacion(otro))
        self.assertIs(r.cotejo.comparacion_control, Comprobacion.SATISFECHA)

    def test_integridad_inspeccion_y_procedencia_insuficientes(self):
        a = self.s.expediente.afirmaciones[0]
        for campo in ('integridad', 'inspeccion'):
            self.exigir_bloqueado(self.con_afirmacion(replace(a, fuente=replace(a.fuente, **{campo:None}))))
        e = self.s.artefacto.entrada_perfil.entrada
        e = replace(e, recurso=replace(e.recurso, procedencia=None))
        art = replace(self.s.artefacto, entrada_perfil=replace(self.s.artefacto.entrada_perfil, entrada=e))
        self.exigir_bloqueado(replace(self.s, artefacto=art))

    def test_restriccion_bloqueante_heredada_y_local_preservadas(self):
        a = self.s.artefacto
        e = a.entrada_perfil.entrada
        for nivel in ('proyecto', 'artefacto', 'operacion'):
            if nivel=='proyecto':
                p = replace(e.proyecto, restricciones=(INFO,BLOQUEO))
                ee = replace(e, proyecto=p)
                art = replace(a, entrada_perfil=replace(a.entrada_perfil, entrada=ee))
                s = replace(self.s, artefacto=art, operacion=replace(self.s.operacion, proyecto=p, entradas=(ee,)))
            elif nivel=='artefacto':
                s = replace(self.s, artefacto=replace(a, restricciones_adicionales=(BLOQUEO,)))
            else:
                s = replace(self.s, operacion=replace(self.s.operacion, restricciones_adicionales=(BLOQUEO,)))
            r = self.exigir_bloqueado(s)
            self.assertIn(BLOQUEO, tuple(x.restriccion for x in r.restricciones))
            self.assertTrue(all(x.origenes for x in r.restricciones))

    def test_evidencia_declarada_no_asciende_y_verificada_tampoco(self):
        a = self.s.expediente.afirmaciones[0]
        for nivel in (NivelEvidencia.DECLARADA, NivelEvidencia.VERIFICADA):
            b = replace(a, evidencia=replace(a.evidencia, nivel=nivel))
            r = self.ejecutar(self.con_afirmacion(b))
            self.assertIs(r.expediente_producto.afirmaciones[0].nivel, NivelEvidencia.DECLARADA)

    def test_relacion_duplicada_y_contradiccion_no_se_ignoran(self):
        a = self.s.expediente.afirmaciones[0]
        b = replace(a, identificador='otra')
        self.exigir_bloqueado(replace(self.s, expediente=expediente(a,b)))
        # Otra sección puede aportar evidencia adversa aunque no se seleccione.
        ref = replace(b.referencia, parrafo=2, ruta_xml=b.referencia.ruta_xml.replace('p[1]', 'p[2]'))
        from spica.metadatos_documentales import localizar
        b = replace(b, referencia=ref, contenido='otra-identidad', evidencia=replace(b.evidencia, localizacion=localizar(ref)))
        ex = expediente(a,b,relaciones=(RelacionAfirmaciones(a.identificador,b.identificador,TipoRelacion.CONTRADICCION,'Conflicto sintetico'),))
        self.exigir_bloqueado(replace(self.s, expediente=ex))

    def test_artefacto_parcial_y_operacion_fallida_cancelada_no_se_promueven(self):
        self.exigir_bloqueado(replace(self.s, artefacto=replace(self.s.artefacto, estado_logico=EstadoArtefacto.PARCIAL)))
        causa = DiagnosticoAdaptacion('causa-fixture', 'operacion', NivelDiagnostico.FALTANTE)
        for estado in (EstadoOperacion.PARCIAL,EstadoOperacion.FALLIDA,EstadoOperacion.CANCELADA):
            op = replace(self.s.operacion, estado=estado, diagnosticos=(causa,),
                         referencias_resultado=('parcial',) if estado is EstadoOperacion.PARCIAL else ())
            self.exigir_bloqueado(replace(self.s, operacion=op))

    def test_referencia_institucional_aportada_no_autentica(self):
        r = self.ejecutar()
        self.assertIsNone(self.s.expediente.fuentes[0].autenticidad)
        self.assertFalse(r.autenticidad_institucional)
        self.assertIs(r.estado,E.APTO_ESTRUCTURALMENTE)

    def test_dos_proyectos_con_mismos_bytes_no_comparten_revision(self):
        s, revision, cotejador, datos = escenario(self.raiz, 'proyecto-rc15-B')
        self.assertEqual(datos,self.datos)
        self.exigir_bloqueado(s,revision=self.revision,cotejador=cotejador)
        self.assertIs(self.ejecutar(s,revision=revision,cotejador=cotejador).estado,E.APTO_ESTRUCTURALMENTE)

    def test_vigencia_desconocida_y_naturaleza_real_no_se_aprueban(self):
        a = self.s.expediente.afirmaciones[0]
        for cambios in ({'vigencia':VigenciaDocumento.DESCONOCIDA}, {'naturaleza':NaturalezaEvidencia.DOCUMENTAL},
                        {'pendientes':('revision-pendiente',)}, {'nivel':NivelEvidencia.INFERIDA}):
            self.exigir_bloqueado(self.con_afirmacion(replace(a,evidencia=replace(a.evidencia,**cambios))))

    def test_edicion_y_producto_desconocidos_son_pendientes_no_contradicciones(self):
        a=self.s.expediente.afirmaciones[0]
        self.assertIs(self.exigir_bloqueado(replace(self.s,producto=replace(self.s.producto,version=None))).estado,
                      E.PENDIENTE_DE_EVIDENCIA)
        b=replace(a,fuente=replace(a.fuente,producto=None,version_producto=None))
        self.assertIs(self.exigir_bloqueado(self.con_afirmacion(b)).estado,E.PENDIENTE_DE_EVIDENCIA)
        e=self.s.artefacto.entrada_perfil.entrada
        ee=replace(e,recurso=replace(e.recurso,version_institucional=None))
        art=replace(self.s.artefacto,entrada_perfil=replace(self.s.artefacto.entrada_perfil,entrada=ee))
        s=replace(self.s,artefacto=art,operacion=replace(self.s.operacion,entradas=(ee,)))
        self.assertIs(self.exigir_bloqueado(s).estado,E.PENDIENTE_DE_EVIDENCIA)

    def test_conservacion_final_incierta_no_produce_relacion(self):
        nativo = CotejadorDocumental.cotejar(self.cotejador,self.s.control_id,self.s.expediente,(self.s.afirmacion_id,))
        with patch.object(CotejadorDocumental,'cotejar',return_value=replace(nativo,conservacion=Comprobacion.INCOMPLETA)):
            self.exigir_bloqueado()

    def test_determinismo_sin_modificar_contextos_o_contratos(self):
        previo = repr(self.s)
        self.assertEqual(self.ejecutar(),self.ejecutar())
        self.assertEqual(repr(self.s),previo)
        self.assertIs(self.s.operacion.estado,EstadoOperacion.DECLARADA)

    def test_flags_bool_y_diagnostico_publico_sin_datos_recibidos(self):
        r = self.ejecutar()
        for campo in ('autenticidad_institucional','validacion_cientifica','ejecucion_autorizada','producto_leido','operacion_ejecutada'):
            self.assertIs(getattr(r,campo),False)
            with self.assertRaises(TypeError): replace(r,**{campo:True})
        with self.assertRaises(TypeError): bool(r)
        with self.assertRaises(FrozenInstanceError): r.version='otra'
        texto=repr(r.diagnostico_publico())
        for secreto in (str(self.raiz),self.revision.responsable_ref,self.s.producto.identificador):
            self.assertNotIn(secreto,texto)

    def test_no_admite_dictamen_dto_codigo_o_contratos_ajenos(self):
        for revision in (True,{},lambda:True,self.ejecutar()):
            with self.assertRaises(TypeError): self.ejecutar(revision=revision)
        with self.assertRaises(TypeError): self.ejecutar(cotejador=self.ejecutar().cotejo)
        with self.assertRaises(TypeError): replace(self.s,producto={})

    def test_sin_red_sqlite_ni_apertura_del_producto(self):
        # Los únicos archivos de datos accesibles por el puente son su DOCX TEMP.
        with patch('socket.socket.connect',side_effect=AssertionError('red')), \
             patch('socket.getaddrinfo',side_effect=AssertionError('DNS')), \
             patch('sqlite3.connect',side_effect=AssertionError('SQLite')):
            r=self.ejecutar()
            self.assertIs(r.estado,E.APTO_ESTRUCTURALMENTE)
            self.assertFalse(r.producto_leido)

    def test_traspaso_conserva_limites_restricciones_y_no_es_fundamento_aprobado(self):
        from spica.metadatos_documentales import RestriccionUso
        a = self.s.expediente.afirmaciones[0]
        incertidumbres = tuple('incertidumbre-fixture-'+str(i) for i in range(64))
        a = replace(a, restricciones=(RestriccionUso.DERECHO_NO_COMPROBADO,),
                    evidencia=replace(a.evidencia,incertidumbres=incertidumbres))
        r = self.ejecutar(self.con_afirmacion(a))
        self.assertIs(r.estado,E.APTO_ESTRUCTURALMENTE)
        self.assertEqual(r.expediente_producto.afirmaciones[0].incertidumbres,incertidumbres)
        self.assertTrue(r.expediente_producto.afirmaciones[0].pendientes)
        self.assertEqual(r.solicitud.expediente.afirmaciones[0].restricciones,a.restricciones)
        self.assertIsNone(r.expediente_producto.producto.restricciones_licencia)
        self.assertFalse(r.ejecucion_autorizada)

    def test_barrera_real_de_proceso_y_ordenes_importacion(self):
        # El hook impide E/S operativa incluso si una regresión omite los mocks.
        programa = r'''
import os,sys,tempfile
from pathlib import Path
sys.path[:0]=sys.argv[1:]
with tempfile.TemporaryDirectory(prefix='spica-rc15-barrera-') as carpeta:
 raiz=Path(carpeta).resolve()
 def guardia(evento,args):
  if evento.startswith(('socket.','sqlite3.')) or evento in ('os.system','subprocess.Popen'):
   raise RuntimeError('efecto_prohibido')
  if evento=='open':
   p=Path(os.fsdecode(args[0])).resolve() if not isinstance(args[0],int) else None
   if p is not None and 'spica_datos' in str(p).lower():raise RuntimeError('lectura_operativa')
   if args[2] & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):
    if p is None or not p.is_relative_to(raiz):raise RuntimeError('escritura_ajena')
 sys.addaudithook(guardia)
 if os.environ.get('RC15_ORDEN')=='inverso':
  import spica.artefactos.coordinacion_precondicion
 from test_vinculo_documental_rc15 import escenario
 from herramientas.vinculo_documental_rc15 import vincular_producto_rc15
 s,r,c,b=escenario(raiz)
 informe=vincular_producto_rc15(s,revision=r,cotejador=c)
 assert informe.expediente_producto is not None
 assert not informe.producto_leido and not informe.ejecucion_autorizada
 assert c.controles[0].ruta.read_bytes()==b
assert not raiz.exists()
print('RC15_TEMP_VERIFICADO_SIN_EFECTOS_OPERATIVOS')
'''
        import os
        for orden in ('directo','inverso'):
            env=dict(os.environ,RC15_ORDEN=orden,PYTHONDONTWRITEBYTECODE='1')
            r=subprocess.run([sys.executable,'-B','-I','-c',programa,
                              str(Path(__file__).resolve().parents[1]/'src'),
                              str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parent)],
                              capture_output=True,text=True,timeout=30,env=env)
            self.assertEqual(r.returncode,0,r.stderr)
            self.assertEqual(r.stdout.strip(),'RC15_TEMP_VERIFICADO_SIN_EFECTOS_OPERATIVOS')


if __name__=='__main__':
    unittest.main()
