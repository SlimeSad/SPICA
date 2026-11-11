"""Consumo de JSON no confiable: fixtures independientes y piloto 85-A/85-C."""

from collections import Counter
from dataclasses import asdict, replace
from datetime import datetime, timezone
import json
import unittest
from unittest.mock import patch

from spica.adquisicion.catalogo import EvidenciaDocumental
from spica.adquisicion.catalogo.modelos import EstadoVerificacion, ProcedenciaCatalogo
from spica.adquisicion.nucleo import Fuente
from spica.calidad import ConfiguracionQA, EstadoResultadoQA as E, ProcedenciaQA
from spica.calidad.consumo import EstadoConsumoQA as EC, LimitesConsumoQA, consumir_exportaciones
from spica.calidad.exportacion import ContextoExportacionQA, exportar_resultado_json
from test_exportacion_qaqc_85c import resultado, contexto
from test_piloto_qaqc_estructural_85a import casos_piloto, evaluar_caso


def texto(**opciones):
    return exportar_resultado_json(resultado(**opciones), contexto())


def datos(**opciones):
    return json.loads(texto(**opciones))


def json_de(d):
    return json.dumps(d, ensure_ascii=True, allow_nan=False)


class ConsumoQA85DTests(unittest.TestCase):
    def rechazada(self, entrada):
        r = consumir_exportaciones(entrada)
        self.assertIs(r.estado, EC.CONTRATO_RECHAZADO)
        self.assertEqual((r.diagnosticos_aceptados, r.documentos_aceptados,
                          r.restricciones_informativas, r.restricciones_bloqueantes), (0, (), 0, 0))
        self.assertTrue(r.problemas)
        return r

    def incompleta(self, entrada, limites):
        r = consumir_exportaciones(entrada, limites=limites)
        self.assertIs(r.estado, EC.VALIDACION_INCOMPLETA)
        self.assertEqual((r.diagnosticos_aceptados, r.documentos_aceptados), (0, ()))
        self.assertTrue(r.problemas)
        return r

    def test_json_valido_bytes_y_texto_conserva_resultado_y_limites_de_confianza(self):
        t = texto()
        a, b = consumir_exportaciones(t), consumir_exportaciones(t.encode('utf-8'))
        self.assertEqual(a, b)
        self.assertIs(a.estado, EC.CONTRATO_VALIDO_EN_ALCANCE)
        self.assertEqual((a.diagnosticos_recibidos, a.diagnosticos_aceptados), (1, 1))
        self.assertEqual(json.loads(a.documentos_aceptados[0]), json.loads(t))
        self.assertEqual((a.version_contrato, a.version_exportacion), ('0.1.0', '0.1.0'))
        self.assertIn('autenticidad_institucional', a.comprobaciones_no_realizadas)
        self.assertIn('validacion_cientifica', a.comprobaciones_no_realizadas)
        self.assertIn('autorizacion_ejecucion', a.comprobaciones_no_realizadas)

    def test_json_malformado_raiz_ajena_y_entrada_no_admitida(self):
        for entrada in ('', '{', '{} trailing', '[]', 'null', '{}', 123, True, [], (), (texto(), object())):
            with self.subTest(tipo=type(entrada), muestra=str(entrada)[:20]):
                self.rechazada(entrada)

    def test_claves_duplicadas_en_raiz_y_anidadas_se_rechazan(self):
        t = texto()
        for manipulado in (t[:-1] + ',"version_esquema":"0.1.0"}',
                            t.replace('"version":"1.0.0"', '"version":"1.0.0","version":"1.0.0"', 1)):
            self.assertNotEqual(manipulado, t)
            r = self.rechazada(manipulado)
            self.assertIn('json_claves_duplicadas', [p.codigo for p in r.problemas])

    def test_versiones_incompatibles_y_emisor_null_no_se_migran(self):
        ubicaciones = (('version_esquema',), ('versiones', 'contrato_qa'), ('versiones', 'evaluador'),
                       ('versiones', 'restricciones'), ('resultado', 'regla', 'version'),
                       ('resultado', 'version_contrato'))
        for ruta in ubicaciones:
            d = datos(); nodo = d
            for k in ruta[:-1]: nodo = nodo[k]
            nodo[ruta[-1]] = '9.0.0'
            with self.subTest(ruta=ruta): self.rechazada(json_de(d))
        r = replace(resultado(), parametros=())
        self.rechazada(exportar_resultado_json(r, contexto()))

    def test_campos_ausentes_y_adicionales_se_rechazan_en_todos_los_niveles(self):
        rutas = ((), ('resultado',), ('resultado', 'registro'), ('resultado', 'procedencia'),
                 ('resultado', 'regla'), ('contexto',), ('versiones',), ('restricciones',))
        for ruta in rutas:
            for extra in (False, True):
                d = datos(); nodo = d
                for k in ruta: nodo = nodo[k]
                if extra: nodo['__clase_ejecutable__'] = 'no ejecutar'
                else: del nodo[next(iter(nodo))]
                with self.subTest(ruta=ruta, extra=extra): self.rechazada(json_de(d))

    def test_booleanos_y_strings_no_sustituyen_enteros(self):
        for v in (True, False, '1', 1.25, 2**53):
            d = datos(); d['resultado']['registro']['numero_registro'] = v
            with self.subTest(v=v): self.rechazada(json_de(d))
        for v in (1, 'true', None):
            d = datos(); d['resultado']['registro']['estructura_correcta'] = v
            with self.subTest(v=v): self.rechazada(json_de(d))

    def test_nan_infinity_y_floats_se_rechazan_literales_textuales_se_conservan(self):
        for v in ('NaN', 'Infinity', '-Infinity', '1e999', '1.25'):
            t = texto().replace('"numero_registro":1', '"numero_registro":' + v, 1)
            self.assertNotEqual(t, texto())
            with self.subTest(v=v): self.rechazada(t)
        for literal in ('NaN', 'Infinity', '0007'):
            r = consumir_exportaciones(texto(literal=literal))
            self.assertIs(r.estado, EC.CONTRATO_VALIDO_EN_ALCANCE)
            self.assertEqual(json.loads(r.documentos_aceptados[0])['resultado']['valores_originales'][0][1], literal)

    def test_unicode_invalido_incluso_surrogate_escapado_y_bom(self):
        for entrada in (b'\xff', '\ud800', texto().replace('001.20', '\\ud800'),
                        b'\xef\xbb\xbf' + texto().encode('utf-8')):
            self.rechazada(entrada)

    def test_unicode_valido_y_controles_no_se_normalizan(self):
        for literal in ('Pe\u00f1a\U0001f30e', 'n\u0303', '\u00f1', '\x00\n', '[[{{"\\' * 20):
            t = texto(literal=literal)
            r = consumir_exportaciones(t)
            self.assertIs(r.estado, EC.CONTRATO_VALIDO_EN_ALCANCE)
            self.assertEqual(json.loads(r.documentos_aceptados[0])['resultado']['valores_originales'][0][1], literal)

    def test_tamano_se_controla_antes_de_json_loads(self):
        t = texto()
        with patch('spica.adquisicion._json_acotado.json.loads', side_effect=AssertionError('parser')):
            self.incompleta(t, LimitesConsumoQA(max_bytes_documento=10))
            self.incompleta((t, t), LimitesConsumoQA(max_bytes_lote=len(t.encode('utf-8'))))
            self.incompleta((t, t), LimitesConsumoQA(max_resultados=1))

    def test_anidamiento_y_nodos_se_controlan_antes_del_parser(self):
        with patch('spica.adquisicion._json_acotado.json.loads', side_effect=AssertionError('parser')):
            self.incompleta('[' * 50 + '0' + ']' * 50, LimitesConsumoQA())
            self.incompleta('[0,0,0,0,0]', LimitesConsumoQA(unidades_documento=3))

    def test_limites_cadenas_objetos_restricciones_y_lote(self):
        t = texto()
        for l in (LimitesConsumoQA(caracteres_cadena=2), LimitesConsumoQA(max_objetos_documento=2),
                  LimitesConsumoQA(max_restricciones_documento=2), LimitesConsumoQA(unidades_lote=2),
                  LimitesConsumoQA(elementos_lista=1), LimitesConsumoQA(propiedades_objeto=2)):
            with self.subTest(limites=l): self.incompleta(t, l)
        self.incompleta((t, t), LimitesConsumoQA(max_restricciones_lote=4))
        for parametros in (dict(max_resultados=True), dict(profundidad=25), dict(max_bytes_lote=0)):
            with self.subTest(parametros=parametros), self.assertRaises(ValueError):
                LimitesConsumoQA(**parametros)

    def test_limite_bytes_utf8_exacto(self):
        t = texto(literal='\u00f1\x00'); n = len(t.encode('utf-8'))
        r = consumir_exportaciones(t, limites=LimitesConsumoQA(max_bytes_documento=n))
        self.assertIs(r.estado, EC.CONTRATO_VALIDO_EN_ALCANCE)
        self.incompleta(t, LimitesConsumoQA(max_bytes_documento=n - 1))

    def test_fallos_controlados_de_memoria_y_recursion_son_incompletos(self):
        t = texto()
        for error in (MemoryError(), RecursionError()):
            with patch('spica.calidad.consumo.leer_json', side_effect=error):
                r = consumir_exportaciones(t)
            self.assertIs(r.estado, EC.VALIDACION_INCOMPLETA)
            self.assertEqual(r.diagnosticos_aceptados, 0)
            self.assertIn('recursos_de_validacion_agotados', [p.codigo for p in r.problemas])

    def test_error_critico_prevalece_sobre_presupuesto_agotado_sin_aceptacion_parcial(self):
        r = consumir_exportaciones(('{', texto()), limites=LimitesConsumoQA(unidades_documento=3))
        self.assertIs(r.estado, EC.CONTRATO_RECHAZADO)
        self.assertEqual((r.diagnosticos_aceptados, r.documentos_aceptados), (0, ()))
        self.assertEqual(len(r.problemas), 2)

    def test_identificadores_acotados_y_pares_no_pierden_tipos(self):
        r = resultado(regla_id='R' * 129)
        self.rechazada(exportar_resultado_json(r, contexto()))
        d = datos(); d['resultado']['parametros'][0] = ['evaluador_nivel0', True]
        self.rechazada(json_de(d))
        d = datos(); d['resultado']['registro']['campos_originales'][0].append('extra')
        self.rechazada(json_de(d))

    def test_identidad_y_huella_alteradas_se_rechazan(self):
        for k, v in (('resultado_id', 'qa0-' + '0' * 64), ('huella_contenido', '0' * 64)):
            d = datos(); d[k] = v
            self.rechazada(json_de(d))

    def test_identidad_reutilizada_para_otra_regla_o_campo_se_rechaza(self):
        for cambiar_regla in (True, False):
            d = datos()
            if cambiar_regla: d['resultado']['regla']['identificador'] = 'OTRA-001'
            else:
                d['resultado']['valores_originales'][0][0] = 'OTRO_CAMPO'
                d['campos_objetivo'] = ['OTRO_CAMPO']
            r = self.rechazada((texto(), json_de(d)))
            self.assertTrue(any(p.codigo == 'identidad_incoherente' for p in r.problemas))

    def test_duplicados_exactos_son_idempotentes_incluso_con_formato_json_distinto(self):
        t = texto(); formateado = json.dumps(json.loads(t), indent=2, ensure_ascii=True)
        r = consumir_exportaciones((t, formateado, t))
        self.assertIs(r.estado, EC.CONTRATO_VALIDO_EN_ALCANCE)
        self.assertEqual((r.diagnosticos_recibidos, r.diagnosticos_aceptados, r.duplicados_exactos), (3, 1, 2))
        self.assertEqual(r.documentos_aceptados, consumir_exportaciones(t).documentos_aceptados)
        self.assertEqual((r.restricciones_informativas, r.restricciones_bloqueantes), (1, 2))

    def test_duplicado_contradictorio_incluso_resellado_rechaza_todo_el_lote(self):
        a = resultado(); b = replace(a, diagnostico='otro_diagnostico_declarado')
        x, y = (exportar_resultado_json(r, contexto()) for r in (a, b))
        self.assertEqual(json.loads(x)['resultado_id'], json.loads(y)['resultado_id'])
        r = self.rechazada((x, y))
        self.assertIn('identidad_reutilizada_contradictoria', [p.codigo for p in r.problemas])

    def test_entrada_reutilizada_con_posiciones_distintas_es_contradiccion(self):
        a, b = resultado(numero=1), resultado(numero=2)
        t = tuple(exportar_resultado_json(r, contexto()) for r in (a, b))
        r = self.rechazada(t)
        self.assertIn('entrada_reutilizada_contradictoria', [p.codigo for p in r.problemas])

    def test_dos_filas_iguales_con_identidades_distintas_se_conservan(self):
        a, b = resultado(numero=1), resultado(numero=2)
        r = consumir_exportaciones((exportar_resultado_json(a, contexto(entrada_id='fila-001')),
                                    exportar_resultado_json(b, contexto(entrada_id='fila-002'))))
        self.assertIs(r.estado, EC.CONTRATO_VALIDO_EN_ALCANCE)
        self.assertEqual((r.diagnosticos_aceptados, r.duplicados_exactos), (2, 0))

    def test_contexto_incompleto_y_regla_fuera_configuracion_no_se_aceptan(self):
        d = datos(); del d['contexto']['evaluacion_id']
        self.rechazada(json_de(d))
        c = contexto(configuracion=ConfiguracionQA(reglas=('L0-EST-001',)))
        self.rechazada(exportar_resultado_json(resultado(), c))

    def test_restricciones_omitidas_y_paquetes_sin_restricciones_no_se_reparan(self):
        for eliminar_campo in (False, True):
            d = datos()
            if eliminar_campo: del d['restricciones']
            else: d['restricciones']['bloqueantes'].pop()
            r = self.rechazada(json_de(d))
            self.assertEqual(r.documentos_aceptados, ())

    def test_restricciones_adulteradas_desconocidas_duplicadas_y_mal_tipadas(self):
        for campo, valor in (('motivo', 'Sin restricciones'), ('operaciones', []),
                             ('codigo', 'autorizar_uso'), ('tipo', 'informativa')):
            d = datos(); d['restricciones']['bloqueantes'][0][campo] = valor
            with self.subTest(campo=campo): self.rechazada(json_de(d))
        d = datos(); d['restricciones']['bloqueantes'].append(d['restricciones']['bloqueantes'][0])
        self.assertIn('restriccion_duplicada', [p.codigo for p in self.rechazada(json_de(d)).problemas])
        d = datos(); d['restricciones']['informativas'] = {}
        self.rechazada(json_de(d))

    def test_satisfecha_mantiene_bloqueos_y_literales_hora_ubigeo_pp(self):
        for campo, literal in (('HORA', '12345'), ('UBIGEO', '007777.0'), ('PP', '1.50'),
                                ('TEMP', '-9999'), ('HR', '500')):
            t = texto(campo=campo, literal=literal)
            r = consumir_exportaciones(t)
            self.assertIs(r.estado, EC.CONTRATO_VALIDO_EN_ALCANCE)
            d = json.loads(r.documentos_aceptados[0])
            self.assertEqual(d['resultado']['estado'], 'comprobacion_satisfecha')
            self.assertEqual(d['resultado']['valores_originales'], [[campo, literal]])
            self.assertEqual(d['restricciones'], json.loads(t)['restricciones'])
            self.assertGreater(r.restricciones_bloqueantes, 2)

    def test_cinco_estados_diagnosticos_y_motivos_se_conservan(self):
        for e in E:
            t = texto(estado=e, diagnostico='motivo_ficticio')
            r = consumir_exportaciones(t)
            self.assertIs(r.estado, EC.CONTRATO_VALIDO_EN_ALCANCE)
            d = json.loads(r.documentos_aceptados[0])
            self.assertEqual(d['resultado']['estado'], e.value)
            self.assertEqual(d['resultado']['diagnostico'], 'motivo_ficticio')
            self.assertEqual(d['restricciones'], json.loads(t)['restricciones'])
        d = datos(estado=E.NO_EVALUADO); d['estado_evaluacion'] = 'completa'
        self.rechazada(json_de(d))

    def test_contradicciones_nativas_reselladas_se_detectan_sin_reevaluar_reglas(self):
        r = resultado()
        distintos = (replace(r, valores_originales=(('MAGNITUD', 'otro_literal'),)),
                     replace(r, registro=replace(r.registro, estructura_correcta=False)))
        for a in distintos:
            self.rechazada(exportar_resultado_json(a, contexto()))

    def test_procedencia_verificada_declarada_no_se_autentica_por_consumo(self):
        f = Fuente('EMISOR_FICTICIO', 'fuente-ficticia'); fecha = datetime(2000, 1, 1, tzinfo=timezone.utc)
        doc = EvidenciaDocumental(f, 'recurso-ficticio', descubierta_utc=fecha,
            estado=EstadoVerificacion.VERIFICADO,
            procedencia=ProcedenciaCatalogo('referencia-ficticia', fecha, 'fixture', 'declaracion no cotejada'))
        r = replace(resultado(), procedencia=ProcedenciaQA(f, 'recurso-ficticio', documento=doc))
        informe = consumir_exportaciones(exportar_resultado_json(r, contexto()))
        self.assertIs(informe.estado, EC.CONTRATO_VALIDO_EN_ALCANCE)
        d = json.loads(informe.documentos_aceptados[0])
        self.assertEqual(d['resultado']['procedencia']['documento']['estado'], 'verificado')
        self.assertIn('autenticidad_institucional', informe.comprobaciones_no_realizadas)
        self.assertIn('hashes_no_son_firmas_de_origen', informe.limitaciones_confianza)

    def test_determinismo_orden_y_objetos_originales_intactos(self):
        a, b = resultado(numero=1), resultado(numero=2)
        antes = asdict(a), asdict(b)
        x = exportar_resultado_json(a, contexto(entrada_id='fila-001'))
        y = exportar_resultado_json(b, contexto(entrada_id='fila-002'))
        r = consumir_exportaciones((x, y))
        self.assertEqual(r, consumir_exportaciones((y, x)))
        self.assertEqual(r, consumir_exportaciones((x, y)))
        self.assertEqual((asdict(a), asdict(b)), antes)
        self.assertEqual(x, exportar_resultado_json(a, contexto(entrada_id='fila-001')))

    def test_excepciones_y_problemas_no_publican_datos_sensibles(self):
        marca = 'SECRETO_FICTICIO_85D'
        d = datos(); d['resultado']['estado'] = marca
        r = self.rechazada(json_de(d))
        self.assertNotIn(marca, repr(r))

    def test_consumidor_sin_red_archivos_sqlite_procesos_eval_exec_ni_ciencia(self):
        t = exportar_resultado_json(resultado(literal="__import__('os').system('NO_EJECUTAR')"),
            contexto(incertidumbres=('https://no-conectar.invalid', 'C:\\NO_ABRIR\\ficticio.csv')))
        with patch('builtins.open', side_effect=AssertionError('archivo')), \
             patch('pathlib.Path.open', side_effect=AssertionError('archivo')), \
             patch('sqlite3.connect', side_effect=AssertionError('sqlite')), \
             patch('socket.socket.connect', side_effect=AssertionError('red')), \
             patch('socket.getaddrinfo', side_effect=AssertionError('dns')), \
             patch('subprocess.Popen', side_effect=AssertionError('proceso')), \
             patch('spica.calidad.experimental.limites.evaluar_limites_sinteticos', side_effect=AssertionError('ciencia')), \
             patch('spica.calidad.reglas.evaluar_registro', side_effect=AssertionError('motor')), \
             patch('builtins.eval', side_effect=AssertionError('eval')), \
             patch('builtins.exec', side_effect=AssertionError('exec')):
            r = consumir_exportaciones(t)
        self.assertIs(r.estado, EC.CONTRATO_VALIDO_EN_ALCANCE)
        self.assertIn('autorizacion_ejecucion', r.comprobaciones_no_realizadas)

    def test_piloto_ida_vuelta_169_y_alteraciones_controladas(self):
        lotes, antes = [], []
        for caso in casos_piloto():
            for r in evaluar_caso(caso):
                antes.append(asdict(r))
                c = ContextoExportacionQA('spica:piloto:85c', 'regresion-001',
                    f'entrada-{r.registro.numero_registro}', escenario_id=caso[0],
                    configuracion=caso[2], incertidumbres=caso[7])
                lotes.append(exportar_resultado_json(r, c))
        copia = tuple(lotes)
        informe = consumir_exportaciones(copia)
        self.assertIs(informe.estado, EC.CONTRATO_VALIDO_EN_ALCANCE)
        self.assertEqual((informe.diagnosticos_recibidos, informe.diagnosticos_aceptados,
                          informe.duplicados_exactos), (169, 169, 0))
        self.assertEqual(informe, consumir_exportaciones(tuple(reversed(copia))))
        d = [json.loads(t) for t in informe.documentos_aceptados]
        self.assertEqual(len({x['resultado_id'] for x in d}), 169)
        self.assertEqual(Counter(x['resultado']['estado'] for x in d), dict(comprobacion_satisfecha=119,
            alerta_documental=3, problema_tecnico=2, no_evaluado=29, evaluacion_incompleta=16))
        self.assertEqual((informe.restricciones_informativas, informe.restricciones_bloqueantes), (169, 566))
        por_id = {json.loads(t)['resultado_id']: json.loads(t) for t in copia}
        self.assertEqual(por_id, {x['resultado_id']: x for x in d})
        self.assertEqual(copia, tuple(lotes))
        despues = [asdict(r) for c in casos_piloto() for r in evaluar_caso(c)]
        self.assertEqual(antes, despues)
        alterado = json.loads(copia[0]); alterado['restricciones']['bloqueantes'] = []
        self.rechazada(copia[1:] + (json_de(alterado),))


if __name__ == '__main__':
    unittest.main()
