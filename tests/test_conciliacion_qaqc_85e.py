"""Auditoría de perfil y comparación de lotes sintéticos, sin evidencia operativa."""

from collections import Counter
from dataclasses import asdict, replace
import json
import unittest
from unittest.mock import patch

from spica.calidad import ConfiguracionQA, EstadoResultadoQA as E
from spica.calidad.consumo import EstadoConsumoQA as EC, LimitesConsumoQA, consumir_exportaciones
from spica.calidad.exportacion import ContextoExportacionQA, exportar_resultado_json
from spica.calidad.conciliacion_lotes import (
    EstadoConciliacionQA as ES, LoteQA, conciliar_lotes,
)
from test_exportacion_qaqc_85c import resultado, contexto
from test_piloto_qaqc_estructural_85a import casos_piloto, evaluar_caso


def lote(nombre, *, r=None, c=None):
    t = exportar_resultado_json(r if r is not None else resultado(), c if c is not None else contexto())
    return LoteQA(nombre, consumir_exportaciones(t))


def piloto(nombre, evaluacion='regresion-001'):
    documentos = []
    for caso in casos_piloto():
        for r in evaluar_caso(caso):
            c = ContextoExportacionQA('spica:piloto:85c', evaluacion,
                f'entrada-{r.registro.numero_registro}', escenario_id=caso[0],
                configuracion=caso[2], incertidumbres=caso[7])
            documentos.append(exportar_resultado_json(r, c))
    return LoteQA(nombre, consumir_exportaciones(tuple(documentos)))


class ConciliacionQA85ETests(unittest.TestCase):
    def test_perfil_aceptado_no_amplia_la_estructura_generada_por_exportador(self):
        r, c = resultado(literal='Pe\u00f1a 0007'), contexto()
        t = exportar_resultado_json(r, c)
        alternativo = json.dumps(json.loads(t), indent=2, ensure_ascii=True)
        a, b = consumir_exportaciones(t), consumir_exportaciones(alternativo)
        self.assertEqual(a, b)
        self.assertEqual(a.documentos_aceptados, (t,))
        self.assertEqual(json.loads(t), json.loads(exportar_resultado_json(r, c)))

    def test_perfil_es_mas_estrecho_en_versiones_ids_y_coherencia(self):
        r, c = resultado(), contexto()
        casos = (replace(r, parametros=()), replace(r, regla=replace(r.regla, version='1.0.1')),
                 replace(r, regla=replace(r.regla, identificador='R' * 129)),
                 replace(r, valores_originales=(('MAGNITUD', 'otro'),)))
        for nativo in casos:
            with self.subTest(regla=nativo.regla.identificador[:10], parametros=nativo.parametros):
                t = exportar_resultado_json(nativo, c)  # El exportador sí puede representarlo.
                self.assertIs(consumir_exportaciones(t).estado, EC.CONTRATO_RECHAZADO)
        c = replace(c, configuracion=ConfiguracionQA(reglas=('L0-EST-001',)))
        self.assertIs(consumir_exportaciones(exportar_resultado_json(r, c)).estado, EC.CONTRATO_RECHAZADO)

    def test_perfil_cerrado_rechaza_campos_superiores_ausentes_y_adicionales(self):
        d = json.loads(lote('A').consumo.documentos_aceptados[0])
        for nombre in d:
            cambiado = dict(d); del cambiado[nombre]
            with self.subTest(nombre=nombre):
                self.assertIs(consumir_exportaciones(json.dumps(cambiado)).estado, EC.CONTRATO_RECHAZADO)
        d['autorizado'] = True
        self.assertIs(consumir_exportaciones(json.dumps(d)).estado, EC.CONTRATO_RECHAZADO)

    def test_dos_lotes_identicos_coinciden_y_se_conservan_ambos(self):
        a, b = lote('A'), lote('B')
        r = conciliar_lotes((a, b))
        self.assertIs(r.estado, ES.COINCIDENCIA)
        self.assertEqual((len(r.lotes), r.resultados_examinados, len(r.coincidencias)), (2, 2, 1))
        self.assertEqual(r.lotes[0].documentos, r.lotes[1].documentos)
        self.assertEqual(r.lotes[0].huella_representacion, r.lotes[1].huella_representacion)
        self.assertFalse(r.conflictos)

    def test_etiqueta_lote_repetida_no_se_deduplica_si_el_contenido_coincide(self):
        a = lote('A'); r = conciliar_lotes((a, a))
        self.assertIs(r.estado, ES.COINCIDENCIA)
        self.assertEqual(len(r.lotes), 2)
        self.assertEqual(r.coincidencias[0].lote_ids, ('A', 'A'))

    def test_identidad_lote_reutilizada_con_otros_miembros_es_conflicto(self):
        a, b = lote('A'), lote('A', r=resultado(regla_id='OTRA-001'))
        r = conciliar_lotes((a, b))
        self.assertIs(r.estado, ES.CONFLICTO)
        self.assertIn('identidad_lote_reutilizada', [p.codigo for p in r.conflictos])

    def test_duplicado_exacto_en_lotes_con_solapamiento_parcial_es_compatible(self):
        a = lote('A')
        t = exportar_resultado_json(resultado(regla_id='OTRA-001'), contexto())
        b = LoteQA('B', consumir_exportaciones(a.consumo.documentos_aceptados + (t,)))
        r = conciliar_lotes((a, b))
        self.assertIs(r.estado, ES.COMPATIBLES)
        self.assertEqual((r.resultados_examinados, len(r.coincidencias)), (3, 1))
        self.assertEqual(len(r.lotes[1].documentos), 2)

    def test_repeticiones_originales_de_transporte_no_cambian_equivalencia(self):
        a = lote('A'); t = a.consumo.documentos_aceptados[0]
        b = LoteQA('B', consumir_exportaciones((t, t)))
        r = conciliar_lotes((a, b))
        self.assertIs(r.estado, ES.COINCIDENCIA)
        self.assertEqual((r.lotes[1].recibidos_declarados, r.lotes[1].duplicados_declarados), (2, 1))

    def test_duplicado_contradictorio_valido_por_separado_se_conserva_como_conflicto(self):
        a, b = lote('A'), lote('B', r=resultado(diagnostico='otro_diagnostico'))
        self.assertIs(a.consumo.estado, EC.CONTRATO_VALIDO_EN_ALCANCE)
        self.assertIs(b.consumo.estado, EC.CONTRATO_VALIDO_EN_ALCANCE)
        r = conciliar_lotes((a, b))
        self.assertIs(r.estado, ES.CONFLICTO)
        self.assertIn('identidad_resultado_reutilizada', [h.codigo for h in r.conflictos])
        self.assertNotEqual(r.lotes[0].documentos, r.lotes[1].documentos)

    def test_restricciones_distintas_bajo_misma_identidad_producen_conflicto(self):
        a = lote('A'); b = lote('B', r=resultado(estado=E.NO_EVALUADO))
        r = conciliar_lotes((a, b))
        self.assertIs(r.estado, ES.CONFLICTO)
        self.assertIn('restricciones_discrepantes', [h.codigo for h in r.conflictos])
        self.assertEqual([x.restricciones_bloqueantes for x in r.lotes], [2, 3])
        self.assertEqual(len(r.lotes), 2)  # No se descarta la evidencia contradictoria.

    def test_misma_entrada_con_reglas_diferentes_es_compatible_sin_equivalencia(self):
        r = conciliar_lotes((lote('A'), lote('B', r=resultado(regla_id='OTRA-001'))))
        self.assertIs(r.estado, ES.COMPATIBLES)
        self.assertEqual(r.coincidencias, ())

    def test_misma_regla_con_campos_distintos_es_compatible_sin_equivalencia(self):
        r = resultado()
        entrada = replace(r.registro, campos_originales=(('X', '1'), ('Y', '1')))
        a = lote('A', r=replace(r, registro=entrada, valores_originales=(('X', '1'),)))
        b = lote('B', r=replace(r, registro=entrada, valores_originales=(('Y', '1'),)))
        informe = conciliar_lotes((a, b))
        self.assertIs(informe.estado, ES.COMPATIBLES)
        self.assertEqual(informe.coincidencias, ())

    def test_misma_entrada_con_evaluaciones_independientes_no_se_alinea(self):
        a = lote('A', c=contexto(evaluacion_id='ejecucion-A'))
        b = lote('B', c=contexto(evaluacion_id='ejecucion-B'))
        r = conciliar_lotes((a, b))
        self.assertIs(r.estado, ES.NO_COMPARABLE)
        self.assertEqual(r.coincidencias, ())
        self.assertIn('ambitos_de_evaluacion_sin_correspondencia', [h.codigo for h in r.no_comparables])

    def test_espacios_y_escenarios_no_se_confunden_con_id_original(self):
        a = lote('A', c=contexto(espacio_id='espacio-A'))
        b = lote('B', c=contexto(espacio_id='espacio-B'))
        self.assertIs(conciliar_lotes((a, b)).estado, ES.NO_COMPARABLE)
        a, b = lote('A', c=contexto(escenario_id='S01')), lote('B', c=contexto(escenario_id='S02'))
        r = conciliar_lotes((a, b))
        self.assertIs(r.estado, ES.COMPATIBLES)
        self.assertFalse(r.coincidencias)

    def test_entradas_distintas_con_igual_contenido_permanecen_distintas(self):
        a = lote('A', c=contexto(entrada_id='entrada-A'))
        b = lote('B', c=contexto(entrada_id='entrada-B'))
        r = conciliar_lotes((a, b))
        self.assertIs(r.estado, ES.COMPATIBLES)
        self.assertEqual(r.coincidencias, ())
        ds = [json.loads(l.documentos[0]) for l in r.lotes]
        self.assertEqual(ds[0]['resultado'], ds[1]['resultado'])
        self.assertNotEqual(ds[0]['resultado_id'], ds[1]['resultado_id'])

    def test_identidad_entrada_reutilizada_con_otro_registro_es_conflicto(self):
        a, b = lote('A'), lote('B', r=resultado(numero=2, regla_id='OTRA-001'))
        r = conciliar_lotes((a, b))
        self.assertIs(r.estado, ES.CONFLICTO)
        self.assertIn('identidad_entrada_reutilizada', [h.codigo for h in r.conflictos])

    def test_contexto_insuficiente_o_declaraciones_distintas_no_se_igualan(self):
        a = lote('A')  # Inventario y configuración desconocidos.
        b = lote('B', c=contexto(metadatos_requeridos=(), metadatos_ausentes=()))
        r = conciliar_lotes((a, b))
        self.assertIs(r.estado, ES.NO_COMPARABLE)
        self.assertEqual(r.coincidencias, ())
        self.assertIn('contextos_de_comprobacion_distintos', [h.codigo for h in r.no_comparables])

    def test_lotes_rechazados_o_incompletos_no_son_utilizables(self):
        a = lote('A')
        b = LoteQA('B', consumir_exportaciones('{'))
        c = LoteQA('C', consumir_exportaciones(a.consumo.documentos_aceptados,
            limites=LimitesConsumoQA(max_bytes_documento=10)))
        for otro in (b, c):
            r = conciliar_lotes((a, otro))
            self.assertIs(r.estado, ES.NO_COMPARABLE)
            self.assertEqual(len(r.lotes), 1)

    def test_estado_booleano_y_conteos_falsos_no_prueban_validacion(self):
        a = lote('A')
        for cambios in (dict(estado=True), dict(diagnosticos_aceptados=True),
                        dict(restricciones_bloqueantes=0), dict(comprobaciones_realizadas=()),
                        dict(version_exportacion='9.0.0')):
            falso = replace(a.consumo)
            for nombre, valor in cambios.items():
                object.__setattr__(falso, nombre, valor)  # Simular manipulación, incluso init=False.
            b = LoteQA('B', falso)
            with self.subTest(cambios=cambios):
                self.assertIs(conciliar_lotes((a, b)).estado, ES.NO_COMPARABLE)

    def test_informe_marcado_valido_con_documentos_adulterados_se_revalida(self):
        a = lote('A')
        for cambio in ('restricciones_faltantes', 'restricciones_alteradas', 'version_diferente'):
            d = json.loads(a.consumo.documentos_aceptados[0])
            if cambio == 'restricciones_faltantes': del d['restricciones']
            elif cambio == 'restricciones_alteradas': d['restricciones']['bloqueantes'][0]['motivo'] = 'alterado'
            else: d['resultado']['regla']['version'] = '1.0.1'
            b = LoteQA('B', replace(a.consumo, documentos_aceptados=(json.dumps(d),)))
            with self.subTest(cambio=cambio):
                r = conciliar_lotes((a, b))
                self.assertIs(r.estado, ES.NO_COMPARABLE)
                self.assertIn('revalidacion_no_disponible', [h.codigo for h in r.no_comparables])

    def test_limites_de_lotes_etiquetas_y_revalidacion(self):
        a = lote('A')
        for lotes in ((), (a,), (a,) * 9, [a, a], (a, True), (a, LoteQA('../ruta', a.consumo))):
            self.assertIs(conciliar_lotes(lotes).estado, ES.NO_COMPARABLE)
        with patch('spica.calidad.conciliacion_lotes.consumir_exportaciones', side_effect=AssertionError('limite')):
            self.assertIs(conciliar_lotes((a,) * 9).estado, ES.NO_COMPARABLE)
        r = conciliar_lotes((a, a), limites_consumo=LimitesConsumoQA(max_bytes_documento=10))
        self.assertIs(r.estado, ES.NO_COMPARABLE)

    def test_conflicto_observado_prevalece_y_no_se_elimina_por_un_lote_invalido(self):
        a, b = lote('A'), lote('B', r=resultado(diagnostico='otro'))
        c = LoteQA('C', consumir_exportaciones('{'))
        r = conciliar_lotes((a, b, c))
        self.assertIs(r.estado, ES.CONFLICTO)
        self.assertTrue(r.conflictos)
        self.assertTrue(r.no_comparables)

    def test_determinismo_multilote_y_ausencia_de_mutaciones(self):
        lotes = (lote('C'), lote('A'), lote('B', r=resultado(diagnostico='otro')))
        antes = tuple(asdict(l) for l in lotes)
        a, b = conciliar_lotes(lotes), conciliar_lotes(tuple(reversed(lotes)))
        self.assertEqual(a, b)
        self.assertEqual(a, conciliar_lotes(lotes))
        self.assertEqual(tuple(asdict(l) for l in lotes), antes)
        self.assertEqual(len(a.lotes), 3)

    def test_sin_red_archivos_sqlite_procesos_exec_eval_ni_ciencia(self):
        a, b = lote('A'), lote('B')
        with patch('builtins.open', side_effect=AssertionError('archivo')), \
             patch('pathlib.Path.open', side_effect=AssertionError('archivo')), \
             patch('socket.socket.connect', side_effect=AssertionError('red')), \
             patch('socket.getaddrinfo', side_effect=AssertionError('dns')), \
             patch('sqlite3.connect', side_effect=AssertionError('sqlite')), \
             patch('subprocess.Popen', side_effect=AssertionError('proceso')), \
             patch('spica.calidad.experimental.limites.evaluar_limites_sinteticos', side_effect=AssertionError('ciencia')), \
             patch('spica.calidad.reglas.evaluar_registro', side_effect=AssertionError('motor')), \
             patch('builtins.eval', side_effect=AssertionError('eval')), \
             patch('builtins.exec', side_effect=AssertionError('exec')):
            r = conciliar_lotes((a, b))
        self.assertIs(r.estado, ES.COINCIDENCIA)
        self.assertIn('sin_autorizacion_operativa', r.limitaciones)
        self.assertIn('sin_validacion_cientifica', r.limitaciones)

    def test_piloto_dos_reproducciones_y_dos_ejecuciones_independientes(self):
        a, b = piloto('A'), piloto('B')  # Dos ciclos completos, mismo contexto de reproducibilidad.
        for l in (a, b):
            self.assertEqual(l.consumo.diagnosticos_aceptados, 169)
            self.assertEqual((l.consumo.restricciones_informativas, l.consumo.restricciones_bloqueantes), (169, 566))
            estados = Counter(json.loads(t)['resultado']['estado'] for t in l.consumo.documentos_aceptados)
            self.assertEqual(estados, dict(comprobacion_satisfecha=119, alerta_documental=3,
                problema_tecnico=2, no_evaluado=29, evaluacion_incompleta=16))
        r = conciliar_lotes((a, b))
        self.assertIs(r.estado, ES.COINCIDENCIA)
        self.assertEqual(len(r.coincidencias), 169)
        self.assertEqual(r.resultados_examinados, 338)
        c = piloto('C', evaluacion='ejecucion-independiente-C')
        self.assertIs(conciliar_lotes((a, c)).estado, ES.NO_COMPARABLE)
        self.assertEqual(c.consumo.diagnosticos_aceptados, 169)
        # Conflicto deliberado válido en cada lote, sin cambiar las fixtures previas.
        d = json.loads(a.consumo.documentos_aceptados[0])
        from spica.calidad.consumo import _resultado, _contexto
        alterado = exportar_resultado_json(replace(_resultado(d['resultado']), diagnostico='conflicto_ficticio'),
                                          _contexto(d['contexto']))
        documentos = tuple(alterado if json.loads(t)['resultado_id'] == d['resultado_id'] else t
                           for t in a.consumo.documentos_aceptados)
        otro = LoteQA('D', consumir_exportaciones(documentos))
        self.assertIs(otro.consumo.estado, EC.CONTRATO_VALIDO_EN_ALCANCE)
        r = conciliar_lotes((a, otro))
        self.assertIs(r.estado, ES.CONFLICTO)
        self.assertEqual((len(r.coincidencias), len(r.lotes)), (168, 2))


if __name__ == '__main__':
    unittest.main()
