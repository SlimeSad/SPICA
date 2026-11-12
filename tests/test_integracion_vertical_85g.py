"""Integración vertical real con bytes ficticios y única frontera HTTP simulada."""

from collections import Counter
from dataclasses import FrozenInstanceError, replace
import hashlib
import io
import csv
import json
from pathlib import Path
import sqlite3
import tempfile
from threading import Event
import unittest
from unittest.mock import patch

import httpx

from herramientas import piloto_integracion_85g as h
from spica.adquisicion.almacenamiento import AlmacenRAW
from spica.adquisicion.catalogo import CatalogoCientifico
from spica.adquisicion.verificacion import LectorCSV
from spica.calidad import EstadoEvaluacionQA, EstadoResultadoQA, TipoRestriccionQA, restricciones_resultado
from spica.calidad.consumo import EstadoConsumoQA, consumir_exportaciones
from spica.calidad.conciliacion_lotes import EstadoConciliacionQA, LoteQA, conciliar_lotes


def contrato(contenido=None, **cambios):
    b = h.fixture_csv_85g() if contenido is None else contenido
    return h.ContratoEjecucion85G('ejecucion-85g', 'proyecto-ficticio-85g', 'entrada-85g',
        'evaluacion-85g', 'tarea-sintetica-85g', len(b), hashlib.sha256(b).hexdigest(), **cambios)


class IntegracionVertical85GTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bytes = h.fixture_csv_85g()
        cls.contrato = contrato()
        cls.informe = h.ejecutar_piloto_85g(cls.contrato, cls.bytes)

    def comprobar_cierre(self, r):
        self.assertTrue(r.temporales_eliminados)
        if r.temporal is not None:
            self.assertFalse(r.temporal.exists())
        self.assertIn(('cierre', 'temporales_eliminados'), r.traza)

    def test_contrato_planificado_no_es_permiso_ni_ejecucion(self):
        self.assertIs(self.contrato.estado, h.EstadoEjecucion85G.PLANIFICADA)
        self.assertEqual(self.contrato.naturaleza, 'simulacion_sintetica_offline')
        self.assertEqual(self.contrato.version, '0.1.0')
        self.assertIn('M18', self.contrato.dependencias)
        self.assertFalse(self.informe.autorizacion_operativa)
        self.assertFalse(self.informe.ejecucion_cientifica)
        with self.assertRaises(TypeError):
            bool(self.contrato)
        with self.assertRaises(TypeError):
            bool(self.informe)
        with self.assertRaises(FrozenInstanceError):
            self.contrato.ejecucion_id = 'otro'
        with self.assertRaises(TypeError):
            replace(self.contrato, estado=h.EstadoEjecucion85G.CONCLUIDA)

    def test_validacion_de_identidades_hash_tamano_y_presupuesto(self):
        for cambios in ({'entrada_id':'../ruta'}, {'evaluacion_id':''}, {'sha256_esperado':'Z'*64},
                        {'tamano_esperado':True}, {'tamano_esperado':-1}, {'presupuesto':True}):
            with self.subTest(cambios=tuple(cambios)):
                with self.assertRaises((ValueError,TypeError)):
                    replace(self.contrato, **cambios)
        for cambios in ({'max_bytes':True}, {'max_registros':33}, {'max_resultados':257},
                        {'max_bytes_json':0}):
            with self.subTest(cambios=cambios), self.assertRaises(ValueError):
                h.Presupuesto85G(**cambios)

    def test_no_admite_rutas_transportes_callbacks_o_cancelacion_booleana(self):
        with self.assertRaises(TypeError):
            h.ejecutar_piloto_85g(self.contrato, Path('fixture.csv'))
        with self.assertRaises(TypeError):
            h.ejecutar_piloto_85g(self.contrato, self.bytes, cancelacion=True)
        with self.assertRaises(TypeError):
            h.ejecutar_piloto_85g(self.contrato, self.bytes, transporte=object())

    def test_fixture_pequena_identificada_y_reproducible(self):
        self.assertEqual(h.fixture_csv_85g(), self.bytes)
        self.assertEqual(len(self.bytes), 572)
        self.assertEqual(hashlib.sha256(self.bytes).hexdigest(),
            '6894bcce331d4af7db8e4a2f6008a8617604d01e8dbf4cc9805dc8cf37e8ee1b')

    def test_cadena_real_concluye_y_concuerda_con_catalogo(self):
        r = self.informe
        self.assertIs(r.estado, h.EstadoEjecucion85G.CONCLUIDA, r.diagnosticos)
        self.assertEqual(r.fase_final, 'cierre')
        self.assertEqual(r.solicitudes_simuladas, 1)
        a, entidad = r.adquisicion.activo, r.registro_catalogo.entidad
        self.assertEqual(r.activo_id,a.asset_id)
        self.assertEqual((a.declaracion.proyecto_id,a.declaracion.objeto_id),
                         (self.contrato.proyecto_id,self.contrato.objeto_id))
        self.assertEqual((entidad.fuente,entidad.producto_id,entidad.identificador),
                         (h.FUENTE_SINTETICA,self.contrato.producto_id,self.contrato.recurso_id))
        self.assertIn(a.asset_id, entidad.procedencia.evidencia)
        self.assertEqual(r.registro_catalogo.revision,1)
        self.comprobar_cierre(r)

    def test_hash_fisico_y_bytes_se_releen_en_raw_real(self):
        real, observados = AlmacenRAW.recuperar, []
        def observar(almacen, activo_id):
            ruta = real(almacen, activo_id)
            with ruta.open('rb') as archivo:
                sha = hashlib.file_digest(archivo,'sha256').hexdigest()
            observados.append((ruta.read_bytes(),sha))
            return ruta
        with patch.object(AlmacenRAW,'recuperar',observar):
            r = h.ejecutar_piloto_85g(self.contrato,self.bytes)
        self.assertIs(r.estado,h.EstadoEjecucion85G.CONCLUIDA,r.diagnosticos)
        self.assertGreaterEqual(len(observados),5)
        self.assertTrue(all(b==self.bytes and sha==self.contrato.sha256_esperado for b,sha in observados))
        self.assertEqual(r.adquisicion.informe_http.sha256,r.adquisicion.activo.sha256)
        self.comprobar_cierre(r)

    def test_identidad_qa_no_inventa_adquisicion_ni_documento(self):
        r = self.informe
        a = r.adquisicion.activo
        for resultados in r.resultados:
            for v in resultados:
                self.assertEqual(v.procedencia.asset_id,a.asset_id)
                self.assertEqual(v.procedencia.sha256_referencia,a.sha256)
                self.assertEqual(v.procedencia.fuente,h.FUENTE_SINTETICA)
                self.assertEqual(v.procedencia.recurso_id,self.contrato.recurso_id)
                self.assertIsNone(v.procedencia.adquisicion_id)
                self.assertIsNone(v.procedencia.documento)

    def test_22_reglas_y_60_resultados_sin_conteo_enganoso(self):
        for resultados,informe in zip(self.informe.resultados,self.informe.informes_qa,strict=True):
            self.assertEqual(len(resultados),60)  # Dos filas, treinta comprobaciones por fila.
            self.assertEqual(len(informe.reglas_ejecutadas),22)
            self.assertEqual(informe.registros_examinados,2)
            self.assertEqual(informe.registros_finalizados,2)
            self.assertIs(informe.estado,EstadoEvaluacionQA.COMPLETA)
            self.assertEqual(Counter(v.estado for v in resultados),
                {EstadoResultadoQA.COMPROBACION_SATISFECHA:34,EstadoResultadoQA.NO_EVALUADO:26})

    def test_cierre_lector_real_y_eof_se_conservan(self):
        self.assertEqual(len(self.informe.lecturas),2)
        for lectura in self.informe.lecturas:
            self.assertTrue(lectura.recorrido_completo)
            self.assertTrue(lectura.eof_alcanzado)
            self.assertEqual(lectura.motivo_fin,'eof')
            self.assertEqual(lectura.registros_correctos,3)  # Encabezado y dos filas.

    def test_restricciones_nativas_exportadas_consumidas_conservadas(self):
        for nativos,consumo in zip(self.informe.resultados,self.informe.consumos,strict=True):
            esperadas={}
            for v in nativos:
                key=(v.registro.numero_registro,v.regla.identificador,tuple(k for k,_ in v.valores_originales))
                esperadas[key]=restricciones_resultado(v)
            for t in consumo.documentos_aceptados:
                d=json.loads(t);v=d['resultado']
                key=(v['registro']['numero_registro'],v['regla']['identificador'],tuple(k for k,_ in v['valores_originales']))
                for grupo,tipo in (('informativas',TipoRestriccionQA.INFORMATIVA),
                                   ('bloqueantes',TipoRestriccionQA.BLOQUEO_USO_DEL_RESULTADO)):
                    self.assertEqual(tuple(x['codigo'] for x in d['restricciones'][grupo]),
                                     tuple(x.codigo for x in esperadas[key] if x.tipo is tipo))
            self.assertEqual((consumo.restricciones_informativas,consumo.restricciones_bloqueantes),(60,206))

    def test_documentacion_ausente_no_habilita_ciencia(self):
        for t in self.informe.consumos[0].documentos_aceptados:
            d=json.loads(t)
            self.assertEqual(d['contexto']['metadatos_ausentes'],['documentacion_institucional'])
            self.assertIn('sin_validacion_cientifica',d['limitaciones'])
            self.assertIn('sin_autorizacion_operativa',d['limitaciones'])
        no_evaluados=[v for v in self.informe.resultados[0]
                      if v.regla.identificador=='L0-PROV-006']
        self.assertTrue(all(v.estado is EstadoResultadoQA.NO_EVALUADO for v in no_evaluados))
        self.assertIn('sin_autorizacion_operativa',self.informe.restricciones)

    def test_literales_hora_ubigeo_pp_y_ceros_no_se_transforman(self):
        for v in self.informe.resultados[0]:
            campos=dict(v.registro.campos_originales)
            self.assertEqual((campos['HORA'],campos['UBIGEO'],campos['PP'],campos['TEMP']),
                             ('hora-incierta','UBIGEO-INCIERTO','4.00','+001.250'))
        self.assertEqual(self.bytes,h.fixture_csv_85g())

    def test_exportacion_consumo_y_reproducciones_identicas_del_mismo_activo(self):
        a,b=self.informe.consumos
        self.assertEqual(a,b)
        self.assertIs(a.estado,EstadoConsumoQA.CONTRATO_VALIDO_EN_ALCANCE)
        c=self.informe.conciliacion
        self.assertIs(c.estado,EstadoConciliacionQA.COINCIDENCIA)
        self.assertEqual((c.resultados_examinados,len(c.coincidencias)),(120,60))
        self.assertFalse(c.conflictos)
        self.assertEqual(c.lotes[0].documentos,c.lotes[1].documentos)

    def test_control_sha_inconsistente_detiene_antes_de_catalogo_qa(self):
        r=h.ejecutar_piloto_85g(replace(self.contrato,sha256_esperado='0'*64),self.bytes)
        self.assertIs(r.estado,h.EstadoEjecucion85G.FALLIDA)
        self.assertEqual(r.diagnosticos,('control_fisico_de_fixture_discrepante',))
        self.assertIsNotNone(r.adquisicion)
        self.assertIsNone(r.registro_catalogo)
        self.assertFalse(r.resultados)
        self.comprobar_cierre(r)

    def test_control_tamano_inconsistente_no_se_autocorrige(self):
        r=h.ejecutar_piloto_85g(replace(self.contrato,tamano_esperado=571),self.bytes)
        self.assertIs(r.estado,h.EstadoEjecucion85G.FALLIDA)
        self.assertFalse(r.consumos)
        self.comprobar_cierre(r)

    def test_contenido_corrupto_no_llega_a_qa(self):
        real=AlmacenRAW.recuperar
        def alterar(almacen,activo_id):
            a=almacen.metadatos(activo_id)
            ruta=almacen.raiz/a.ruta_interna
            b=ruta.read_bytes();ruta.write_bytes(b'X'+b[1:])
            return real(almacen,activo_id)
        with patch.object(AlmacenRAW,'recuperar',alterar):
            r=h.ejecutar_piloto_85g(self.contrato,self.bytes)
        self.assertIs(r.estado,h.EstadoEjecucion85G.FALLIDA)
        self.assertEqual(r.diagnosticos,('fallo_http_raw_comprobacion',))
        self.assertRegex(r.activo_id,r'^[0-9a-f]{32}$')
        self.assertFalse(r.resultados)
        self.comprobar_cierre(r)

    def test_transferencia_interrumpida_sin_reintentos(self):
        real=httpx.MockTransport.handle_request
        class Interrumpido(httpx.SyncByteStream):
            def __iter__(self):
                yield b'fragmento'
                raise httpx.ReadError('secreto_sintetico_no_publicar')
        def fallar(transporte,peticion):
            r=real(transporte,peticion);r.stream=Interrumpido();return r
        with patch.object(httpx.MockTransport,'handle_request',fallar):
            r=h.ejecutar_piloto_85g(self.contrato,self.bytes)
        self.assertIs(r.estado,h.EstadoEjecucion85G.FALLIDA)
        self.assertEqual(r.solicitudes_simuladas,1)
        self.assertIsNone(r.adquisicion)
        self.assertFalse(r.consumos)
        self.assertNotIn('secreto_sintetico_no_publicar',repr(r))
        self.comprobar_cierre(r)

    def test_fallo_escritura_staging_cierra_y_propaga_fase(self):
        with patch('tempfile.NamedTemporaryFile',side_effect=PermissionError('ruta_sensible_ficticia')):
            r=h.ejecutar_piloto_85g(self.contrato,self.bytes)
        self.assertIs(r.estado,h.EstadoEjecucion85G.FALLIDA)
        self.assertEqual(r.diagnosticos,('fallo_http_raw_descarga',))
        self.assertFalse(r.resultados)
        self.assertNotIn('ruta_sensible_ficticia',repr(r))
        self.comprobar_cierre(r)

    def test_fallo_sqlite_de_catalogo_no_presenta_exito_global(self):
        with patch.object(CatalogoCientifico,'registrar_documental',side_effect=sqlite3.OperationalError('no_publicar')):
            r=h.ejecutar_piloto_85g(self.contrato,self.bytes)
        self.assertIs(r.estado,h.EstadoEjecucion85G.FALLIDA)
        self.assertEqual(r.fase_final,'catalogo')
        self.assertFalse(r.resultados)
        self.assertNotIn('no_publicar',repr(r))
        self.comprobar_cierre(r)

    def test_identidad_catalogo_incompatible_detectada_tras_consulta_real(self):
        real=CatalogoCientifico.consultar_recurso
        def distinto(cat,*args,**kw):
            r=real(cat,*args,**kw)
            return replace(r,entidad=replace(r.entidad,producto_id='otro-producto-ficticio'))
        with patch.object(CatalogoCientifico,'consultar_recurso',distinto):
            r=h.ejecutar_piloto_85g(self.contrato,self.bytes)
        self.assertIs(r.estado,h.EstadoEjecucion85G.FALLIDA)
        self.assertEqual(r.diagnosticos,('identidad_catalogo_incompatible',))
        self.assertFalse(r.resultados)
        self.comprobar_cierre(r)

    def test_campo_estructural_ausente_conserva_incompletitud(self):
        filas=list(csv.reader(io.StringIO(self.bytes.decode('utf-8'))))
        filas[1]=filas[1][:-1]
        s=io.StringIO(newline='');csv.writer(s,lineterminator='\n').writerows(filas)
        b=s.getvalue().encode('utf-8')
        r=h.ejecutar_piloto_85g(contrato(b),b)
        self.assertIs(r.estado,h.EstadoEjecucion85G.INCOMPLETA)
        self.assertIs(r.informes_qa[0].estado,EstadoEvaluacionQA.INCOMPLETA)
        self.assertTrue(any(v.estado is EstadoResultadoQA.EVALUACION_INCOMPLETA for v in r.resultados[0]))
        self.assertFalse(r.consumos)
        self.comprobar_cierre(r)

    def test_lectura_incompleta_no_exporta_parcial_como_completo(self):
        real=LectorCSV.__next__
        def detener(lector):
            if lector._registros>=2:raise StopIteration
            return real(lector)
        with patch.object(LectorCSV,'__next__',detener):
            r=h.ejecutar_piloto_85g(self.contrato,self.bytes)
        self.assertIs(r.estado,h.EstadoEjecucion85G.INCOMPLETA)
        self.assertFalse(r.lecturas[0].recorrido_completo)
        self.assertFalse(r.consumos)
        self.comprobar_cierre(r)

    def test_exportacion_sin_restricciones_rechazada_por_consumidor_real(self):
        real=h.exportar_resultado_json
        def adulterar(*args,**kw):
            d=json.loads(real(*args,**kw));del d['restricciones'];return json.dumps(d)
        with patch.object(h,'exportar_resultado_json',adulterar):
            r=h.ejecutar_piloto_85g(self.contrato,self.bytes)
        self.assertIs(r.estado,h.EstadoEjecucion85G.FALLIDA)
        self.assertEqual(r.fase_final,'consumo_A')
        self.assertIs(r.consumos[0].estado,EstadoConsumoQA.CONTRATO_RECHAZADO)
        self.assertEqual(r.consumos[0].diagnosticos_aceptados,0)
        self.assertIsNone(r.conciliacion)
        self.comprobar_cierre(r)

    def test_perdida_de_restricciones_en_enlace_es_fallo_de_integracion(self):
        real=h.consumir_exportaciones
        def perder(*args,**kw):
            return replace(real(*args,**kw),restricciones_bloqueantes=0)
        with patch.object(h,'consumir_exportaciones',perder):
            r=h.ejecutar_piloto_85g(self.contrato,self.bytes)
        self.assertIs(r.estado,h.EstadoEjecucion85G.FALLIDA)
        self.assertEqual(r.diagnosticos,('restricciones_no_conservadas',))
        self.assertIsNone(r.conciliacion)
        self.comprobar_cierre(r)

    def test_presupuesto_del_consumidor_conserva_validacion_incompleta(self):
        real=h.consumir_exportaciones
        def limitado(contenido,*,limites):
            return real(contenido,limites=replace(limites,max_resultados=1))
        with patch.object(h,'consumir_exportaciones',limitado):
            r=h.ejecutar_piloto_85g(self.contrato,self.bytes)
        self.assertIs(r.estado,h.EstadoEjecucion85G.INCOMPLETA)
        self.assertIs(r.consumos[0].estado,EstadoConsumoQA.VALIDACION_INCOMPLETA)
        self.assertEqual(r.consumos[0].diagnosticos_aceptados,0)
        self.assertEqual(r.diagnosticos,('validacion_contractual_incompleta',))
        self.assertIsNone(r.conciliacion)
        self.comprobar_cierre(r)

    def test_otro_contexto_de_evaluacion_no_se_alinea_por_mismos_valores(self):
        otro=h.ejecutar_piloto_85g(replace(self.contrato,ejecucion_id='otra-ejecucion',
                                       evaluacion_id='otra-evaluacion'),self.bytes)
        self.assertIs(otro.estado,h.EstadoEjecucion85G.CONCLUIDA,otro.diagnosticos)
        r=conciliar_lotes((LoteQA('A',self.informe.consumos[0]),LoteQA('C',otro.consumos[0])))
        self.assertIs(r.estado,EstadoConciliacionQA.NO_COMPARABLE)
        self.assertNotEqual(otro.adquisicion.activo.asset_id,self.informe.adquisicion.activo.asset_id)
        self.assertEqual(otro.adquisicion.activo.sha256,self.informe.adquisicion.activo.sha256)
        self.comprobar_cierre(otro)

    def test_conflicto_deliberado_individualmente_valido_no_se_deduplica(self):
        a=self.informe.consumos[0]
        # Reexportar un diagnóstico modificado, conservando el contexto original.
        from spica.calidad.consumo import _contexto,_resultado
        d=json.loads(a.documentos_aceptados[0])
        distinto=h.exportar_resultado_json(replace(_resultado(d['resultado']),diagnostico='conflicto_sintetico_85g'),
                                          _contexto(d['contexto']))
        textos=(distinto,)+a.documentos_aceptados[1:]
        b=consumir_exportaciones(textos)
        self.assertIs(b.estado,EstadoConsumoQA.CONTRATO_VALIDO_EN_ALCANCE)
        r=conciliar_lotes((LoteQA('A',a),LoteQA('D',b)))
        self.assertIs(r.estado,EstadoConciliacionQA.CONFLICTO)
        self.assertEqual((len(r.coincidencias),len(r.lotes)),(59,2))
        self.assertTrue(r.conflictos)
        self.assertEqual(r.lotes[0].restricciones_bloqueantes,r.lotes[1].restricciones_bloqueantes)

    def test_cancelacion_antes_de_empezar_no_crea_temporal(self):
        e=Event();e.set()
        with patch.object(h,'_base_temporal',side_effect=AssertionError('no_crear')):
            r=h.ejecutar_piloto_85g(self.contrato,self.bytes,cancelacion=e)
        self.assertIs(r.estado,h.EstadoEjecucion85G.CANCELADA)
        self.assertIsNone(r.temporal)
        self.assertEqual(r.solicitudes_simuladas,0)

    def test_cancelacion_entre_componentes_no_inicia_qa(self):
        real=CatalogoCientifico.consultar_recurso;e=Event()
        def cancelar(cat,*args,**kw):
            r=real(cat,*args,**kw);e.set();return r
        with patch.object(CatalogoCientifico,'consultar_recurso',cancelar):
            r=h.ejecutar_piloto_85g(self.contrato,self.bytes,cancelacion=e)
        self.assertIs(r.estado,h.EstadoEjecucion85G.CANCELADA)
        self.assertFalse(r.resultados)
        self.comprobar_cierre(r)

    def test_cancelacion_durante_transferencia_no_se_confunde_con_fallo(self):
        real=httpx.MockTransport.handle_request;e=Event()
        def cancelar(transporte,peticion):
            r=real(transporte,peticion);e.set();return r
        with patch.object(httpx.MockTransport,'handle_request',cancelar):
            r=h.ejecutar_piloto_85g(self.contrato,self.bytes,cancelacion=e)
        self.assertIs(r.estado,h.EstadoEjecucion85G.CANCELADA)
        self.assertEqual(r.solicitudes_simuladas,1)
        self.assertFalse(r.consumos)
        self.comprobar_cierre(r)

    def test_limite_de_bytes_antes_de_efectos(self):
        c=replace(self.contrato,presupuesto=h.Presupuesto85G(max_bytes=100))
        r=h.ejecutar_piloto_85g(c,self.bytes)
        self.assertIs(r.estado,h.EstadoEjecucion85G.INCOMPLETA)
        self.assertEqual(r.diagnosticos,('limite_bytes_entrada',))
        self.assertEqual(r.solicitudes_simuladas,0)
        self.assertIsNone(r.temporal)
        self.assertIsNone(r.activo_id)

    def test_limites_de_qa_y_json_no_producen_exito_parcial(self):
        for p,codigo in ((h.Presupuesto85G(max_resultados=10),'evaluacion_estructural_incompleta'),
                         (h.Presupuesto85G(max_bytes_json=100),'limite_bytes_json')):
            with self.subTest(codigo=codigo):
                r=h.ejecutar_piloto_85g(replace(self.contrato,presupuesto=p),self.bytes)
                self.assertIs(r.estado,h.EstadoEjecucion85G.INCOMPLETA)
                self.assertEqual(r.diagnosticos,(codigo,))
                self.assertFalse(r.consumos)
                self.comprobar_cierre(r)

    def test_sin_sockets_backend_http_real_procesos_ni_ciencia(self):
        with patch('socket.socket.connect',side_effect=AssertionError('red')), \
             patch('socket.getaddrinfo',side_effect=AssertionError('dns')), \
             patch.object(httpx.HTTPTransport,'handle_request',side_effect=AssertionError('http_real')), \
             patch('subprocess.Popen',side_effect=AssertionError('proceso')), \
             patch('spica.calidad.experimental.limites.evaluar_limites_sinteticos',side_effect=AssertionError('ciencia')):
            r=h.ejecutar_piloto_85g(self.contrato,self.bytes)
        self.assertIs(r.estado,h.EstadoEjecucion85G.CONCLUIDA,r.diagnosticos)
        self.comprobar_cierre(r)

    def test_temporal_operativo_rechazado_antes_de_inspeccionar_ruta(self):
        operativa=str(Path.home()/'SPICA_DATOS'/'raw')
        with patch.dict('os.environ',{'TEMP':operativa}), \
             patch.object(h,'_segura',side_effect=AssertionError('no_inspeccionar')):
            r=h.ejecutar_piloto_85g(self.contrato,self.bytes)
        self.assertIs(r.estado,h.EstadoEjecucion85G.FALLIDA)
        self.assertEqual(r.diagnosticos,('base_temporal_no_admitida',))
        self.assertIsNone(r.temporal)
        self.assertEqual(r.solicitudes_simuladas,0)

    def test_no_resuelve_raices_operativas_al_validar_temporal(self):
        real=Path.resolve
        protegida=Path.home()/'SPICA_DATOS'
        def resolver(ruta,*args,**kw):
            if ruta==protegida:raise AssertionError('no_resolver_operativa')
            return real(ruta,*args,**kw)
        with patch.object(Path,'resolve',resolver):
            r=h.ejecutar_piloto_85g(self.contrato,self.bytes)
        self.assertIs(r.estado,h.EstadoEjecucion85G.CONCLUIDA,r.diagnosticos)
        self.comprobar_cierre(r)

    def test_interrupcion_propaga_y_elimina_temporal_propio(self):
        real=tempfile.TemporaryDirectory;creados=[]
        def crear(*args,**kw):
            t=real(*args,**kw);creados.append(Path(t.name));return t
        with patch.object(h.tempfile,'TemporaryDirectory',crear), \
             patch.object(CatalogoCientifico,'consultar_recurso',side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                h.ejecutar_piloto_85g(self.contrato,self.bytes)
        self.assertTrue(creados)
        self.assertTrue(all(not p.exists() for p in creados))


if __name__=='__main__':
    unittest.main()
