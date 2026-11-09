"""Cardinalidad y límites de uso de diagnósticos, solo con fixtures 85-A."""

from collections import Counter
from dataclasses import asdict, fields, replace
from unittest.mock import patch
import unittest

from spica.calidad import (
    ConfiguracionQA, EstadoEvaluacionQA as EE, EstadoResultadoQA as E,
    ProcedenciaQA, REGLAS_NIVEL0, ResultadoQA, TipoRestriccionQA as T,
    VERSION_CONTRATO_QA, VERSION_EVALUADOR_NIVEL0, VERSION_RESTRICCIONES_QA,
    evaluar_registro, restricciones_resultado,
)
from spica.perfilado.interpretacion import VERSION_INTERPRETACION
from test_piloto_qaqc_estructural_85a import (
    REGLAS_PILOTO, casos_piloto, configuracion, evaluar_caso, registro,
)


def clave_traza(contexto, resultado):
    """Identidad local del ensayo, no ID meteorológico ni hash del contenido."""
    r = resultado.registro
    return (contexto, r.numero_registro, r.linea_inicial, r.linea_final,
            resultado.regla.identificador, resultado.regla.version,
            tuple(sorted(k for k, _ in resultado.valores_originales)))


def anotaciones(resultado):
    return {r.codigo: r for r in restricciones_resultado(resultado)}


class ContratosQA85BTests(unittest.TestCase):
    def test_cardinalidad_por_regla_campo_y_cinco_estados(self):
        por_regla, por_objetivo, estados = Counter(), Counter(), Counter()
        esperado = (
            (11, 0, 0, 2, 0), (8, 0, 0, 2, 3), (8, 0, 1, 4, 0),
            (11, 0, 0, 2, 0), (9, 1, 1, 2, 0), (0, 0, 0, 0, 13),
            (11, 1, 0, 1, 0), (11, 0, 0, 2, 0), (10, 1, 0, 2, 0),
            (11, 0, 0, 2, 0), (7, 0, 0, 6, 0), (22, 0, 0, 4, 0),
        )
        orden = (E.COMPROBACION_SATISFECHA, E.ALERTA_DOCUMENTAL,
                 E.PROBLEMA_TECNICO, E.NO_EVALUADO, E.EVALUACION_INCOMPLETA)
        casos = casos_piloto()
        self.assertEqual((len(casos), sum(len(c[1]) for c in casos)), (12, 13))
        for caso, resumen in zip(casos, esperado, strict=True):
            resultados = evaluar_caso(caso)
            conteo = Counter(r.estado for r in resultados)
            self.assertEqual(tuple(conteo[e] for e in orden), resumen, caso[0])
            for r in resultados:
                por_regla[r.regla.identificador] += 1
                por_objetivo[(r.regla.identificador, tuple(k for k, _ in r.valores_originales))] += 1
                estados[r.estado] += 1
        self.assertEqual(por_regla, {i: 39 if i.startswith('L0-VAL-') else 13 for i in REGLAS_PILOTO})
        for rid in ('L0-VAL-001', 'L0-VAL-002', 'L0-VAL-004'):
            for campo in ('TEMP', 'HR', 'PP'):
                self.assertEqual(por_objetivo[rid, (campo,)], 13)
        self.assertEqual(tuple(estados[e] for e in orden), (119, 3, 2, 29, 16))
        self.assertEqual(sum(estados.values()), 169)

    def test_identidad_estable_no_depende_del_orden_de_ejecucion(self):
        casos = casos_piloto()
        def indexar(secuencia):
            pares = [(clave_traza(c[0], r), r) for c in secuencia for r in evaluar_caso(c)]
            self.assertEqual(len(pares), len(dict(pares)))
            return dict(pares)
        a = indexar(casos)
        reordenados = tuple((c[0], tuple(reversed(c[1])),
                            replace(c[2], reglas=tuple(reversed(c[2].reglas)),
                                    variables=tuple(reversed(c[2].variables))), *c[3:])
                           for c in reversed(casos))
        self.assertEqual(len(a), 169)
        self.assertEqual(a, indexar(reordenados))
        # Contenido igual no identifica la entrada, y cada escenario tiene contexto.
        s01, s12 = casos[0], casos[-1]
        x, y = evaluar_caso(s01)[0], evaluar_caso(s12)[0]
        self.assertEqual(x, y)
        self.assertNotEqual(clave_traza(s01[0], x), clave_traza(s12[0], y))
        u, v = s12[1]
        self.assertEqual(u.valores_csv_originales, v.valores_csv_originales)
        self.assertNotEqual(u.numero_registro, v.numero_registro)

    def test_regresion_traza_incompleta_de_las_cuatro_val(self):
        entrada = casos_piloto()[5][1][0]
        resultados = tuple(evaluar_registro(entrada, ProcedenciaQA()))
        self.assertEqual(len(resultados), 30)
        self.assertEqual(len({clave_traza('S06-todas', r) for r in resultados}), 30)
        for numero in range(1, 5):
            grupo = [r for r in resultados if r.regla.identificador == f'L0-VAL-{numero:03d}']
            self.assertEqual([r.valores_originales[0][0] for r in grupo], ['TEMP', 'HR', 'PP'])
            self.assertTrue(all(r.diagnostico == 'estructura_no_evaluable' for r in grupo))
            self.assertTrue(all(r.registro is entrada for r in grupo))

    def test_versiones_independientes_y_esquema_anterior_inalterado(self):
        self.assertEqual(len({r.identificador for r in REGLAS_NIVEL0}), 22)
        self.assertEqual({r.version for r in REGLAS_NIVEL0}, {'1.0.0'})
        self.assertEqual((VERSION_CONTRATO_QA, VERSION_INTERPRETACION,
                          VERSION_EVALUADOR_NIVEL0, VERSION_RESTRICCIONES_QA),
                         ('1.0.0', '1.0.0', '1.0.1', '1.0.0'))
        r = evaluar_caso(casos_piloto()[0])[0]
        nombres = ('regla', 'registro', 'procedencia', 'valores_originales', 'evidencia',
                   'parametros', 'estado', 'diagnostico', 'version_contrato')
        self.assertEqual(tuple(f.name for f in fields(ResultadoQA)), nombres)
        # Constructor previo de ocho argumentos, sin atributos obligatorios nuevos.
        previo = ResultadoQA(r.regla, r.registro, r.procedencia, r.valores_originales,
                             r.evidencia, (), r.estado, r.diagnostico)
        self.assertEqual(tuple(asdict(previo)), nombres)
        self.assertEqual(previo.parametros, ())
        self.assertEqual(previo.version_contrato, '1.0.0')
        self.assertNotIn('restricciones', asdict(previo))
        self.assertNotIn('evaluador_nivel0', dict(previo.parametros))  # Desconocido, no retroasignado.
        self.assertEqual(restricciones_resultado(previo), restricciones_resultado(r))
        for caso in casos_piloto():
            for x in evaluar_caso(caso):
                self.assertEqual(dict(x.parametros)['evaluador_nivel0'], '1.0.1')
                self.assertEqual(sum(k == 'evaluador_nivel0' for k, _ in x.parametros), 1)

    def test_satisfecha_coexiste_con_restricciones_sin_autorizar(self):
        r = next(r for r in evaluar_caso(casos_piloto()[9])
                 if r.regla.identificador == 'L0-VAL-002' and r.valores_originales[0][0] == 'PP')
        self.assertIs(r.estado, E.COMPROBACION_SATISFECHA)
        self.assertIs(r.estado_evaluacion, EE.COMPLETA)
        a = anotaciones(r)
        self.assertIs(a['alcance_estructural'].tipo, T.INFORMATIVA)
        self.assertEqual(a['alcance_estructural'].operaciones, ())
        self.assertIs(a['pp_sin_conversion'].tipo, T.BLOQUEO_USO_DEL_RESULTADO)
        self.assertEqual(a['pp_sin_conversion'].operaciones,
                         ('convertir_mm_mm_h', 'inferir_acumulacion_o_intensidad'))
        self.assertIn('sin_validacion_cientifica', a)
        self.assertFalse(hasattr(r, 'autorizado'))

    def test_incompleta_identifica_impedimento_sin_aprobar(self):
        for caso in (casos_piloto()[1], casos_piloto()[5]):
            for r in evaluar_caso(caso):
                if r.estado is E.EVALUACION_INCOMPLETA:
                    self.assertIs(r.estado_evaluacion, EE.INCOMPLETA)
                    a = anotaciones(r)['condicion_incompleta']
                    self.assertEqual(a.motivo, r.diagnostico)
                    self.assertIn(r.diagnostico, ('campo_no_disponible', 'estructura_no_evaluable'))
                    self.assertEqual(a.operaciones, ('dar_por_concluida_la_condicion',))

    def test_no_evaluado_conserva_motivo_y_metadatos_desconocidos(self):
        resultados = tuple(evaluar_registro(registro(), ProcedenciaQA()))
        for r in resultados:
            if r.estado is E.NO_EVALUADO:
                self.assertIs(r.estado_evaluacion, EE.NO_EVALUADA)
                self.assertEqual(anotaciones(r)['condicion_no_evaluada'].motivo, r.diagnostico)
        zona = next(r for r in resultados if r.regla.identificador == 'L0-TMP-003')
        self.assertEqual(zona.diagnostico, 'zona_horaria_desconocida')
        self.assertEqual(zona.evidencia, ())
        self.assertEqual(zona.procedencia, ProcedenciaQA())

    def test_hora_ambigua_y_ubigeo_no_se_transforman(self):
        for indice, campo, literal, codigo in (
                (7, 'HORA', '12345', 'hora_sin_transformacion'),
                (8, 'UBIGEO', '007777.0', 'ubigeo_sin_interpretacion')):
            caso = casos_piloto()[indice]
            for r in evaluar_caso(caso):
                if campo in dict(r.valores_originales):
                    self.assertIn(codigo, anotaciones(r))
                    self.assertEqual(dict(r.valores_originales)[campo], literal)
            self.assertEqual(dict(caso[1][0].campos_originales)[campo], literal)
            self.assertIsNone(caso[2].zona_documentada)

    def test_temp_hr_no_metrologia_aun_con_extremos_finitos(self):
        for r in evaluar_registro(registro(TEMP='-9999', HR='500'), ProcedenciaQA(),
                                 configuracion=ConfiguracionQA(reglas=('L0-VAL-002',))):
            if r.valores_originales[0][0] in ('TEMP', 'HR'):
                self.assertIs(r.estado, E.COMPROBACION_SATISFECHA)
                self.assertIn('numero_sin_metrologia', anotaciones(r))

    def test_procedencia_no_verifica_archivos_ni_equivalencia(self):
        p = ProcedenciaQA(recurso_id='recurso-ficticio', asset_id='activo-ficticio',
                         sha256_referencia='a' * 64)
        for r in evaluar_registro(registro(), p,
                                 configuracion=ConfiguracionQA(reglas=('L0-PROV-004', 'L0-PROV-005'))):
            self.assertIs(r.estado, E.COMPROBACION_SATISFECHA)
            self.assertIn('referencia_sin_verificacion', anotaciones(r))
            self.assertIn('sin_equivalencia_editorial', anotaciones(r))
            self.assertEqual(dict(r.parametros)['verificacion_fisica'], 'no_realizada_por_esta_regla')

    def test_restricciones_no_alteran_resultados_entradas_ni_su_cardinalidad(self):
        for caso in casos_piloto():
            anteriores = tuple(asdict(r) for r in caso[1])
            resultados = evaluar_caso(caso)
            antes = tuple(asdict(r) for r in resultados)
            for r in resultados:
                a = restricciones_resultado(r)
                self.assertEqual(a, restricciones_resultado(r))
                self.assertEqual(len(a), len({x.codigo for x in a}))
            self.assertEqual(antes, tuple(asdict(r) for r in resultados))
            self.assertEqual(anteriores, tuple(asdict(r) for r in caso[1]))
            self.assertEqual(len(resultados), 13 * len(caso[1]))

    def test_politica_no_evalua_codigo_red_sqlite_ciencia_ni_archivos(self):
        resultados = tuple(r for c in casos_piloto() for r in evaluar_caso(c))
        with patch('builtins.open', side_effect=AssertionError('archivo')), \
             patch('pathlib.Path.open', side_effect=AssertionError('archivo')), \
             patch('sqlite3.connect', side_effect=AssertionError('sqlite')), \
             patch('socket.socket.connect', side_effect=AssertionError('red')), \
             patch('subprocess.Popen', side_effect=AssertionError('proceso')), \
             patch('spica.calidad.experimental.limites.evaluar_limites_sinteticos',
                   side_effect=AssertionError('nivel1')), \
             patch('builtins.eval', side_effect=AssertionError('eval')), \
             patch('builtins.exec', side_effect=AssertionError('exec')):
            self.assertEqual(sum(bool(restricciones_resultado(r)) for r in resultados), 169)
            with self.assertRaises(TypeError):
                restricciones_resultado({'estado': 'aprobado'})


if __name__ == '__main__':
    unittest.main()
