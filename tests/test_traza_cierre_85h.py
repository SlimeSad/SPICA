"""Cierre sintético: evidencias históricas, coherencia en memoria y cero permisos."""

from collections import Counter
from dataclasses import FrozenInstanceError, replace
import hashlib
import json
from pathlib import Path
import sqlite3
from threading import Event
import unittest
from unittest.mock import patch

import httpx

from herramientas import piloto_integracion_85g as h
from herramientas import traza_cierre_85h as t
from spica.adquisicion.almacenamiento import EstadoIncorporacion
from spica.adquisicion.integracion import FaseHTTPRAW
from spica.adquisicion.nucleo import EstadoDescarga
from spica.adquisicion.verificacion import EstadoEstructura
from spica.calidad.consumo import consumir_exportaciones, _resultado, _contexto
from spica.calidad.conciliacion_lotes import LoteQA, conciliar_lotes, EstadoConciliacionQA


def contrato(**cambios):
    b = h.fixture_csv_85g()
    c = h.ContratoEjecucion85G('ejecucion-85h', 'proyecto-ficticio-85g', 'entrada-85h',
        'evaluacion-85h', 'tarea-85h', len(b), hashlib.sha256(b).hexdigest())
    return replace(c, **cambios)


class Cierre85HTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bytes = h.fixture_csv_85g()
        cls.informe = h.ejecutar_piloto_85g(contrato(), cls.bytes)
        cls.traza = t.construir_traza_85h(cls.informe)
        cls.referencia = cls.traza.sha256  # Control conservado por separado.

    def verificar(self, r):
        tr = t.construir_traza_85h(r)
        v = t.verificar_traza_85h(tr, r, referencia_sha256=tr.sha256)
        self.assertTrue(v.coherente_en_alcance, v.diagnosticos)
        self.assertTrue(r.temporales_eliminados)
        if r.temporal is not None:
            self.assertFalse(r.temporal.exists())
        return json.loads(tr.canonico)

    def recapturar(self, r):
        # Solo para atacar el cotejo interno; no acredita una captura física real.
        return replace(r, captura_antes_cierre=t.capturar_evidencia_85h(r))

    def test_traza_completa_y_cardinalidad_real(self):
        d = self.verificar(self.informe)
        self.assertTrue(d['cadena_completa'])
        self.assertEqual(d['version_traza'], '0.1.0')
        e = d['evidencia']
        self.assertEqual(e['contrato']['tamano_esperado'], 572)
        self.assertEqual(e['activo']['sha256'], hashlib.sha256(self.bytes).hexdigest())
        for n, qa, consumo in zip(e['resultados'], e['informes_qa'], e['consumos'], strict=True):
            self.assertEqual(len(n), 60)
            self.assertEqual(len(qa['reglas_ejecutadas']), 22)
            self.assertEqual(qa['registros_examinados'], 2)
            self.assertEqual(Counter(v['estado'] for v in n),
                {'comprobacion_satisfecha': 34, 'no_evaluado': 26})
            self.assertEqual((consumo['restricciones_informativas'], consumo['restricciones_bloqueantes']), (60, 206))

    def test_inmutabilidad_y_ausencia_de_permiso(self):
        with self.assertRaises(FrozenInstanceError):
            self.traza.sha256 = '0' * 64
        with self.assertRaises(TypeError):
            bool(self.traza)
        v = t.verificar_traza_85h(self.traza, self.informe, referencia_sha256=self.referencia)
        with self.assertRaises(TypeError):
            bool(v)
        d = json.loads(self.traza.canonico)
        self.assertFalse(d['ejecucion_cientifica'])
        self.assertFalse(d['autorizacion_operativa'])
        self.assertIn('sin_autenticidad_independiente', d['limitaciones'])

    def test_representacion_determinista_mismo_contexto_conservado(self):
        otra = t.construir_traza_85h(self.informe)
        self.assertEqual(otra, self.traza)
        d = json.loads(self.traza.canonico)
        self.assertEqual(self.traza.canonico, json.dumps(d, sort_keys=True,
            ensure_ascii=False, allow_nan=False, separators=(',', ':')))

    def test_huella_del_activo_distinta_de_huella_de_traza(self):
        self.assertNotEqual(self.traza.sha256, self.informe.adquisicion.activo.sha256)
        self.assertEqual(self.traza.sha256, hashlib.sha256(self.traza.canonico.encode()).hexdigest())

    def test_referencia_independiente_obligatoria(self):
        with self.assertRaises(TypeError):
            t.verificar_traza_85h(self.traza, self.informe)
        with self.assertRaises(ValueError):
            t.verificar_traza_85h(self.traza, self.informe, referencia_sha256='')
        v = t.verificar_traza_85h(self.traza, self.informe, referencia_sha256='0' * 64)
        self.assertFalse(v.coherente_en_alcance)

    def test_no_autocertifica_traza_alterada_y_recalculada_por_emisor(self):
        d = json.loads(self.traza.canonico)
        d['version_traza'] = '99.0.0'
        texto = t._canonico(d)
        falsa = t.TrazaCierre85H(texto, t._huella(texto))
        self.assertFalse(t.verificar_traza_85h(falsa, self.informe,
            referencia_sha256=falsa.sha256).coherente_en_alcance)

    def test_adulteraciones_de_identidad_restriccion_version_y_estado(self):
        for campo, valor in (('estado_final', 'concluida_cientificamente'),
                             ('restricciones', []), ('cadena_completa', False),
                             ('diagnosticos', ['falso']), ('version_traza', '0.2.0')):
            with self.subTest(campo=campo):
                d = json.loads(self.traza.canonico); d[campo] = valor
                texto = t._canonico(d); falsa = t.TrazaCierre85H(texto, t._huella(texto))
                self.assertFalse(t.verificar_traza_85h(falsa, self.informe,
                    referencia_sha256=falsa.sha256).coherente_en_alcance)

    def test_datos_no_tipados_y_presupuestos_no_admitidos(self):
        with self.assertRaises(TypeError):
            t.construir_traza_85h({'estado': 'concluida'})
        for maximo in (True, 0, -1, t.MAX_BYTES_TRAZA + 1, 128):
            with self.subTest(maximo=maximo), self.assertRaises(ValueError):
                t.construir_traza_85h(self.informe, max_bytes=maximo)

    def test_informe_con_activo_inconsistente_no_pasa_cotejo(self):
        r = self.recapturar(replace(self.informe, activo_id='0' * 32))
        with self.assertRaisesRegex(ValueError, 'contradictorio'):
            t.construir_traza_85h(r)

    def test_catalogo_de_otro_recurso_no_pasa_cotejo(self):
        reg = self.informe.registro_catalogo
        r = self.recapturar(replace(self.informe, registro_catalogo=replace(reg,
            entidad=replace(reg.entidad, identificador='otro-recurso'))))
        with self.assertRaises(ValueError):
            t.construir_traza_85h(r)

    def test_captura_previa_detecta_cambio_posterior(self):
        r = replace(self.informe, solicitudes_simuladas=2)
        with self.assertRaisesRegex(ValueError, 'cambio_tras_captura'):
            t.construir_traza_85h(r)

    def test_resumen_qa_y_configuracion_no_contradicen_resultados(self):
        qa = self.informe.informes_qa[0]
        distinta = replace(self.informe.contrato.configuracion, variables=('TEMP',))
        casos = (
            replace(self.informe, informes_qa=(replace(qa, conteos=()), self.informe.informes_qa[1])),
            replace(self.informe, informes_qa=(replace(qa, reglas_ejecutadas=()), self.informe.informes_qa[1])),
            replace(self.informe, contrato=replace(self.informe.contrato, configuracion=distinta)),
        )
        for r in casos:
            with self.subTest(), self.assertRaises(ValueError):
                t.construir_traza_85h(self.recapturar(r))

    def test_discontinuidad_de_linaje_no_se_repara_por_nombres(self):
        r = self.recapturar(replace(self.informe, recuperaciones=()))
        with self.assertRaises(ValueError):
            t.construir_traza_85h(r)

    def test_omision_de_restricciones_bloqueantes_en_json(self):
        docs = list(self.informe.exportaciones[0]); d = json.loads(docs[0])
        d['restricciones']['bloqueantes'] = []; docs[0] = json.dumps(d)
        r = self.recapturar(replace(self.informe, exportaciones=(tuple(docs), self.informe.exportaciones[1])))
        with self.assertRaises(ValueError):
            t.construir_traza_85h(r)

    def test_restriccion_adulterada_con_mismos_conteos(self):
        docs = list(self.informe.exportaciones[0]); d = json.loads(docs[0])
        d['restricciones']['informativas'][0]['codigo'] = 'codigo_falso'; docs[0] = json.dumps(d)
        r = self.recapturar(replace(self.informe, exportaciones=(tuple(docs), self.informe.exportaciones[1])))
        with self.assertRaises(ValueError):
            t.construir_traza_85h(r)

    def test_resultado_duplicado_no_pasa_como_60_independientes(self):
        docs = self.informe.exportaciones[0]
        r = self.recapturar(replace(self.informe, exportaciones=((docs[0],) + docs[:-1],
                                                              self.informe.exportaciones[1])))
        with self.assertRaises(ValueError):
            t.construir_traza_85h(r)

    def test_json_valido_ajeno_al_nativo_no_pasa_cotejo(self):
        docs = self.informe.exportaciones[0]; d = json.loads(docs[0])
        adulterado = h.exportar_resultado_json(replace(_resultado(d['resultado']),
            diagnostico='variante_no_emitida'), _contexto(d['contexto']))
        nuevos = (adulterado,) + docs[1:]
        consumo = consumir_exportaciones(nuevos)
        r = replace(self.informe, exportaciones=(nuevos, self.informe.exportaciones[1]),
                    consumos=(consumo, self.informe.consumos[1]))
        r = self.recapturar(r)
        with self.assertRaises(ValueError):
            t.construir_traza_85h(r)

    def test_transicion_de_etapa_omitida_es_inconsistencia(self):
        r = replace(self.informe, traza=tuple(x for x in self.informe.traza if x[0] != 'catalogo'))
        with self.assertRaises(ValueError):
            t.construir_traza_85h(r)

    def test_estado_planificado_o_iniciado_no_es_cierre_final(self):
        for estado in (h.EstadoEjecucion85G.PLANIFICADA, h.EstadoEjecucion85G.INICIADA):
            with self.subTest(estado=estado), self.assertRaises(ValueError):
                t.construir_traza_85h(replace(self.informe, estado=estado))

    def test_captura_antes_de_liberar_y_verificacion_despues_sin_es(self):
        real = h.capturar_evidencia_85h; observados = []
        def observar(r):
            observados.append((r.temporal.exists(), r.adquisicion.ruta_verificada.is_file(),
                               r.recursos_liberados))
            return real(r)
        with patch.object(h, 'capturar_evidencia_85h', observar):
            r = h.ejecutar_piloto_85g(contrato(), self.bytes)
        self.assertEqual(observados, [(True, True, ())])
        self.assertEqual(r.recursos_liberados, tuple(reversed(r.recursos_adquiridos)))
        tr = t.construir_traza_85h(r)
        with patch.object(Path, 'open', side_effect=AssertionError('sin_archivos')), \
             patch.object(Path, 'exists', side_effect=AssertionError('sin_sondeo')), \
             patch('sqlite3.connect', side_effect=AssertionError('sin_sqlite')):
            self.assertTrue(t.verificar_traza_85h(tr, r, referencia_sha256=tr.sha256).coherente_en_alcance)

    def test_hash_del_activo_eliminado_no_puede_recalcularse(self):
        ruta = self.informe.adquisicion.ruta_verificada
        self.assertFalse(ruta.exists())
        with self.assertRaises(FileNotFoundError):
            ruta.open('rb')
        self.assertIn('sin_revalidacion_fisica_tras_eliminar_temporales', json.loads(self.traza.canonico)['limitaciones'])

    def test_fallo_sha_esperado_conserva_hash_observado_y_causa(self):
        r = h.ejecutar_piloto_85g(contrato(sha256_esperado='0' * 64), self.bytes)
        d = self.verificar(r)
        self.assertFalse(d['cadena_completa'])
        self.assertIn('control_fisico_de_fixture_discrepante', d['diagnosticos'])
        self.assertNotEqual(d['evidencia']['activo']['sha256'], d['evidencia']['contrato']['sha256_esperado'])
        self.assertIsNone(d['evidencia']['catalogo'])

    def test_cancelacion_previa_sin_etapas_o_recursos_inventados(self):
        evento = Event(); evento.set()
        r = h.ejecutar_piloto_85g(contrato(), self.bytes, cancelacion=evento)
        d = self.verificar(r)
        self.assertEqual(d['estado_final'], 'cancelada')
        self.assertFalse(d['evidencia']['recursos_adquiridos'])
        self.assertTrue(all(e == 'no_iniciada' for _, e in d['etapas'][:-1]))

    def test_presupuesto_previo_excedido_sin_almacenamiento(self):
        r = h.ejecutar_piloto_85g(contrato(presupuesto=h.Presupuesto85G(max_bytes=100)), self.bytes)
        d = self.verificar(r)
        self.assertEqual(d['estado_final'], 'incompleta')
        self.assertIsNone(d['evidencia']['activo'])
        self.assertIn('limite_bytes_entrada', d['diagnosticos'])

    def test_fallo_en_staging_conserva_estado_sin_activo_inventado(self):
        with patch('tempfile.NamedTemporaryFile', side_effect=PermissionError('secreto_no_copiar')):
            r = h.ejecutar_piloto_85g(contrato(), self.bytes)
        d = self.verificar(r)
        self.assertEqual(d['estado_final'], 'fallida')
        self.assertIsNone(d['evidencia']['activo'])
        self.assertNotIn('secreto_no_copiar', json.dumps(d))

    def test_fallo_en_catalogo_preserva_raw_y_no_inventa_qa(self):
        with patch.object(h.CatalogoCientifico, 'registrar_documental', side_effect=sqlite3.OperationalError):
            r = h.ejecutar_piloto_85g(contrato(), self.bytes)
        d = self.verificar(r)
        self.assertIsNotNone(d['evidencia']['activo'])
        self.assertFalse(d['evidencia']['resultados'])
        self.assertIn(['activo_catalogo', 'discontinuidad'], d['enlaces'])

    def test_fallo_recuperacion_sin_qa_ficticia(self):
        real = h.AlmacenRAW.recuperar; contador = 0
        def fallar(almacen, activo_id):
            nonlocal contador
            contador += 1
            if contador == 2:
                raise OSError('no_copiar_ruta')
            return real(almacen, activo_id)
        with patch.object(h.AlmacenRAW, 'recuperar', fallar):
            r = h.ejecutar_piloto_85g(contrato(), self.bytes)
        d = self.verificar(r)
        self.assertEqual(d['fase_final'], 'recuperacion_A')
        self.assertFalse(d['evidencia']['resultados'])

    def test_excepcion_durante_qa_conserva_emitidos(self):
        real = h.EvaluadorNivel0.__next__; contador = 0
        def fallar(qa):
            nonlocal contador
            contador += 1
            if contador == 4:
                raise RuntimeError('no_publicar')
            return real(qa)
        with patch.object(h.EvaluadorNivel0, '__next__', fallar):
            r = h.ejecutar_piloto_85g(contrato(), self.bytes)
        d = self.verificar(r)
        self.assertEqual(len(d['evidencia']['resultados'][0]), 3)
        self.assertEqual(d['evidencia']['informes_qa'][0]['resultados_emitidos'], 3)
        self.assertFalse(d['evidencia']['exportaciones'])

    def test_excepcion_exportando_conserva_prefijo_json(self):
        real = h.exportar_resultado_json; contador = 0
        def fallar(*a, **kw):
            nonlocal contador
            contador += 1
            if contador == 3:
                raise ValueError('no_publicar')
            return real(*a, **kw)
        with patch.object(h, 'exportar_resultado_json', fallar):
            r = h.ejecutar_piloto_85g(contrato(), self.bytes)
        d = self.verificar(r)
        self.assertEqual(len(d['evidencia']['exportaciones'][0]), 2)
        self.assertFalse(d['evidencia']['consumos'])
        self.assertIn('fallo_componente_exportacion_A', d['diagnosticos'])

    def test_excepcion_consumo_preserva_json_sin_aceptacion_ficticia(self):
        with patch.object(h, 'consumir_exportaciones', side_effect=ValueError):
            r = h.ejecutar_piloto_85g(contrato(), self.bytes)
        d = self.verificar(r)
        self.assertEqual(len(d['evidencia']['exportaciones'][0]), 60)
        self.assertFalse(d['evidencia']['consumos'])

    def test_excepcion_conciliacion_conserva_ambos_consumos(self):
        with patch.object(h, 'conciliar_lotes', side_effect=ValueError):
            r = h.ejecutar_piloto_85g(contrato(), self.bytes)
        d = self.verificar(r)
        self.assertEqual(len(d['evidencia']['consumos']), 2)
        self.assertIsNone(d['evidencia']['conciliacion'])

    def test_cancelacion_tras_raw_conserva_evidencia(self):
        real = h.CatalogoCientifico.consultar_recurso; evento = Event()
        def cancelar(*a, **kw):
            r = real(*a, **kw); evento.set(); return r
        with patch.object(h.CatalogoCientifico, 'consultar_recurso', cancelar):
            r = h.ejecutar_piloto_85g(contrato(), self.bytes, cancelacion=evento)
        d = self.verificar(r)
        self.assertEqual(d['estado_final'], 'cancelada')
        self.assertIsNotNone(d['evidencia']['catalogo'])
        self.assertFalse(d['evidencia']['resultados'])

    def test_presupuesto_qa_conserva_diez_resultados_sin_exportar(self):
        r = h.ejecutar_piloto_85g(contrato(presupuesto=h.Presupuesto85G(max_resultados=10)), self.bytes)
        d = self.verificar(r)
        self.assertEqual(d['estado_final'], 'incompleta')
        self.assertEqual(len(d['evidencia']['resultados'][0]), 10)
        self.assertFalse(d['evidencia']['exportaciones'])

    def test_control_fisico_previo_al_cierre_no_se_omite(self):
        self.assertIn('pre_cierre', self.informe.recuperaciones)
        self.assertIn('post_qa_A', self.informe.recuperaciones)
        self.assertIn('post_qa_B', self.informe.recuperaciones)
        self.assertEqual(self.bytes, h.fixture_csv_85g())

    def test_fallo_control_fisico_final_conserva_error(self):
        real = h.AlmacenRAW.recuperar; contador = 0
        def fallar(almacen, activo_id):
            nonlocal contador
            contador += 1
            if contador >= 6:
                raise OSError('error_final')
            return real(almacen, activo_id)
        with patch.object(h.AlmacenRAW, 'recuperar', fallar):
            r = h.ejecutar_piloto_85g(contrato(), self.bytes)
        d = self.verificar(r)
        self.assertEqual(d['estado_final'], 'fallida')
        self.assertIn('control_fisico_pre_cierre_fallido', d['diagnosticos'])
        self.assertEqual(len(d['evidencia']['consumos']), 2)

    def test_conciliacion_post_cierre_y_conflicto_conservado(self):
        a = self.informe.consumos[0]
        indice = next(i for i, texto in enumerate(a.documentos_aceptados)
            if json.loads(texto)['resultado']['regla']['identificador'] == 'L0-EST-001')
        d = json.loads(a.documentos_aceptados[indice])
        variante = h.exportar_resultado_json(replace(_resultado(d['resultado']),
            diagnostico='conflicto_sintetico_85h'), _contexto(d['contexto']))
        documentos = list(a.documentos_aceptados); documentos[indice] = variante
        b = consumir_exportaciones(tuple(documentos))
        r = conciliar_lotes((LoteQA('A', a), LoteQA('D', b)))
        self.assertIs(r.estado, EstadoConciliacionQA.CONFLICTO)
        self.assertEqual(len(r.coincidencias), 59)
        self.assertEqual(len(r.conflictos), 1)
        self.assertEqual(t.construir_traza_85h(self.informe), self.traza)

    def test_mismo_contexto_declarado_nueva_adquisicion_no_es_misma_evidencia(self):
        otro = h.ejecutar_piloto_85g(contrato(), self.bytes)
        self.assertNotEqual(t.construir_traza_85h(otro), self.traza)
        self.assertEqual(otro.contrato, self.informe.contrato)
        self.assertNotEqual(otro.activo_id, self.informe.activo_id)
        r = conciliar_lotes((LoteQA('A', self.informe.consumos[0]), LoteQA('C', otro.consumos[0])))
        self.assertIs(r.estado, EstadoConciliacionQA.CONFLICTO)

    def test_error_al_cerrar_no_pierde_resultados_y_no_es_concluido(self):
        real = h.CatalogoCientifico.__exit__
        def cerrar(cat, *args):
            real(cat, *args)
            raise OSError('no_publicar_ruta')
        with patch.object(h.CatalogoCientifico, '__exit__', cerrar):
            r = h.ejecutar_piloto_85g(contrato(), self.bytes)
        d = self.verificar(r)
        self.assertEqual(d['estado_final'], 'fallida')
        self.assertIn('cierre_recursos_no_confirmado', d['diagnosticos'])
        self.assertEqual(len(d['evidencia']['consumos']), 2)
        self.assertNotIn('no_publicar_ruta', json.dumps(d))

    def test_error_transferencia_preserva_causa_fase_e_intentos(self):
        real = httpx.MockTransport.handle_request
        class Interrumpido(httpx.SyncByteStream):
            def __iter__(self):
                yield b'fragmento'
                raise httpx.ReadError('no_publicar_credencial')
        def responder(transporte, peticion):
            respuesta = real(transporte, peticion); respuesta.stream = Interrumpido(); return respuesta
        with patch.object(httpx.MockTransport, 'handle_request', responder):
            r = h.ejecutar_piloto_85g(contrato(), self.bytes)
        d = self.verificar(r)
        self.assertEqual(d['estado_final'], 'fallida')
        self.assertIsNotNone(d['error_http_raw'])
        self.assertEqual(d['error_http_raw'][1], 'descarga')
        self.assertEqual(len(d['error_http_raw'][3]), 1)
        self.assertNotIn('no_publicar_credencial', json.dumps(d))

    def test_error_tras_publicar_conserva_id_conocido_sin_inventar_hash_observado(self):
        real = h.AlmacenRAW.recuperar
        def corromper(almacen, activo_id):
            a = almacen.metadatos(activo_id)
            ruta = almacen.raiz / a.ruta_interna
            contenido = ruta.read_bytes(); ruta.write_bytes(b'X' + contenido[1:])
            return real(almacen, activo_id)
        with patch.object(h.AlmacenRAW, 'recuperar', corromper):
            r = h.ejecutar_piloto_85g(contrato(), self.bytes)
        d = self.verificar(r)
        self.assertEqual(d['estado_final'], 'fallida')
        self.assertRegex(d['evidencia']['activo_id_conocido'], r'^[0-9a-f]{32}$')
        self.assertIsNone(d['evidencia']['activo'])
        self.assertIsNone(d['evidencia']['http'])
        self.assertFalse(d['evidencia']['resultados'])

    def test_contexto_distinto_no_se_iguala_por_hash(self):
        otro = h.ejecutar_piloto_85g(contrato(ejecucion_id='otra-ejecucion-85h',
            evaluacion_id='otra-evaluacion-85h'), self.bytes)
        tr = t.construir_traza_85h(otro)
        self.assertNotEqual(tr, self.traza)
        self.assertEqual(otro.adquisicion.activo.sha256, self.informe.adquisicion.activo.sha256)
        self.assertNotEqual(otro.activo_id, self.informe.activo_id)
        r = conciliar_lotes((LoteQA('A', self.informe.consumos[0]), LoteQA('C', otro.consumos[0])))
        self.assertIs(r.estado, EstadoConciliacionQA.NO_COMPARABLE)

    def test_sin_red_backend_real_ciencia_ni_acceso_operativo(self):
        with patch('socket.socket.connect', side_effect=AssertionError('red')), \
             patch('socket.getaddrinfo', side_effect=AssertionError('dns')), \
             patch.object(httpx.HTTPTransport, 'handle_request', side_effect=AssertionError('http')), \
             patch('spica.calidad.experimental.limites.evaluar_limites_sinteticos', side_effect=AssertionError('ciencia')):
            r = h.ejecutar_piloto_85g(contrato(), self.bytes)
            self.verificar(r)
        # Las llamadas internas GET a MockTransport no son conexiones/GET externos.
        self.assertEqual(r.solicitudes_simuladas, 1)
        self.assertFalse(r.autorizacion_operativa)

    def test_concluida_rechaza_qa_incompleta_o_conteos_de_recorrido_contradictorios(self):
        qa = self.informe.informes_qa[0]
        variantes = (
            replace(qa, estado=h.EstadoEvaluacionQA.INCOMPLETA),
            replace(qa, recorrido_completo=False),
            replace(qa, motivo_fin='limite_resultados_qa'),
            replace(qa, registros_examinados=0),
            replace(qa, registros_finalizados=0),
            replace(qa, evaluaciones_incompletas=1),
            replace(qa, limites=replace(qa.limites, max_registros=1)),
        )
        for cambiado in variantes:
            r = self.recapturar(replace(self.informe, informes_qa=(cambiado, self.informe.informes_qa[1])))
            with self.subTest(cambiado=cambiado), self.assertRaises(ValueError):
                t.construir_traza_85h(r)

    def test_concluida_rechaza_lector_sin_eof_o_recorrido_inconsistente(self):
        lector = self.informe.lecturas[0]
        variantes = (
            replace(lector, eof_alcanzado=False),
            replace(lector, recorrido_completo=False),
            replace(lector, estado=EstadoEstructura.INCOMPLETA),
            replace(lector, motivo_fin='consumidor_detuvo_lectura'),
            replace(lector, registros_correctos=0),
            replace(lector, bytes_recorrido=0),
        )
        for cambiado in variantes:
            r = self.recapturar(replace(self.informe, lecturas=(cambiado, self.informe.lecturas[1])))
            with self.subTest(motivo=cambiado.motivo_fin), self.assertRaises(ValueError):
                t.construir_traza_85h(r)

    def test_concluida_rechaza_transferencia_adaptador_o_raw_no_finalizados(self):
        a = self.informe.adquisicion
        variantes = tuple(replace(a, informe_http=replace(a.informe_http, estado=estado))
            for estado in (EstadoDescarga.PENDIENTE, EstadoDescarga.PARCIAL, EstadoDescarga.FALLIDA)) + (
            replace(a, fase=FaseHTTPRAW.COMPROBACION),
            replace(a, activo=replace(a.activo, estado=EstadoIncorporacion.INCONSISTENTE)),
            replace(a, activo=replace(a.activo, error='evidencia_contradictoria_sintetica')),
        )
        for cambiado in variantes:
            r = self.recapturar(replace(self.informe, adquisicion=cambiado))
            with self.subTest(fase=cambiado.fase), self.assertRaises(ValueError):
                t.construir_traza_85h(r)

    def test_fallo_captura_conserva_informe_y_cierra_sin_conclusion_ficticia(self):
        with patch.object(h, 'capturar_evidencia_85h', side_effect=ValueError('no_publicar_secreto')):
            r = h.ejecutar_piloto_85g(contrato(), self.bytes)
        d = self.verificar(r)
        self.assertEqual(d['estado_final'], 'fallida')
        self.assertFalse(d['cadena_completa'])
        self.assertIsNone(d['captura_previa_sha256'])
        self.assertIn('captura_previa_no_disponible', d['diagnosticos'])
        self.assertEqual(len(d['evidencia']['consumos']), 2)
        self.assertEqual(r.recursos_liberados, tuple(reversed(r.recursos_adquiridos)))
        self.assertNotIn('no_publicar_secreto', json.dumps(d))


if __name__ == '__main__':
    unittest.main()
