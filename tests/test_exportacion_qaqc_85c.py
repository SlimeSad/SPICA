"""Contrato JSON con resultados ficticios independientes y regresión 85-A."""

from collections import Counter
from dataclasses import asdict, fields, replace
from datetime import datetime, timezone
from decimal import Decimal
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from spica.adquisicion.catalogo import EvidenciaDocumental
from spica.adquisicion.catalogo.modelos import EstadoVerificacion, ProcedenciaCatalogo
from spica.adquisicion.nucleo import Fuente
from spica.calidad import (
    CategoriaQA as C, ConfiguracionQA, EstadoResultadoQA as E,
    ProcedenciaQA, ReferenciaDocumentalQA, RegistroQA, ReglaQA, ResultadoQA,
    restricciones_resultado,
)
from spica.calidad.exportacion import (
    ContextoExportacionQA, LimitesExportacionQA, VERSION_EXPORTACION_QA,
    exportar_resultado_json,
)
from test_piloto_qaqc_estructural_85a import casos_piloto, evaluar_caso


def resultado(*, campo='MAGNITUD', literal='001.20', estado=E.COMPROBACION_SATISFECHA,
              diagnostico='condicion_ficticia', numero=1, regla_id='ENSAYO-001'):
    """No simula una medición institucional ni afirma ejecución científica."""
    entrada = RegistroQA(numero, '0007', 'PUNTO_FICTICIO', numero, numero,
                         ((campo, literal),), True)
    regla = ReglaQA(regla_id, '1.0.0', C.ESTRUCTURA, 'Condición de fixture no institucional')
    return ResultadoQA(regla, entrada, ProcedenciaQA(), ((campo, literal),), (),
                       (('evaluador_nivel0', '1.0.1'),), estado, diagnostico)


def contexto(**cambios):
    return replace(ContextoExportacionQA('spica:ensayo:85c', 'ejecucion-001', 'entrada-001'), **cambios)


def leer(texto):
    def constante_no_json(v):
        raise AssertionError('Constante no JSON')
    return json.loads(texto, parse_constant=constante_no_json)


class ExportacionQA85CTests(unittest.TestCase):
    def test_salida_incluye_restricciones_automaticas_omitidas_por_asdict(self):
        r = resultado()
        self.assertNotIn('restricciones', asdict(r))
        with patch('spica.calidad.exportacion.restricciones_resultado', wraps=restricciones_resultado) as f:
            d = leer(exportar_resultado_json(r, contexto()))
        f.assert_called_once_with(r)
        self.assertEqual(d['version_esquema'], '0.1.0')
        self.assertEqual(d['resultado']['diagnostico'], r.diagnostico)
        self.assertEqual(d['detalle_diagnostico'], r.regla.descripcion)
        self.assertEqual(d['restricciones']['informativas'][0]['codigo'], 'alcance_estructural')
        self.assertIn('sin_validacion_cientifica', [a['codigo'] for a in d['restricciones']['bloqueantes']])

    def test_cinco_estados_se_conservan_sin_convertirlos_en_aprobacion(self):
        for estado, evaluacion in ((E.COMPROBACION_SATISFECHA, 'completa'),
                (E.ALERTA_DOCUMENTAL, 'completa'), (E.PROBLEMA_TECNICO, 'completa'),
                (E.NO_EVALUADO, 'no_evaluada'), (E.EVALUACION_INCOMPLETA, 'incompleta')):
            with self.subTest(estado=estado):
                r = resultado(estado=estado, diagnostico='impedimento_ficticio')
                d = leer(exportar_resultado_json(r, contexto()))
                self.assertEqual(d['resultado']['estado'], estado.value)
                self.assertEqual(d['estado_evaluacion'], evaluacion)
                if estado in (E.NO_EVALUADO, E.EVALUACION_INCOMPLETA):
                    codigo = 'condicion_no_evaluada' if estado is E.NO_EVALUADO else 'condicion_incompleta'
                    a = next(a for a in d['restricciones']['bloqueantes'] if a['codigo'] == codigo)
                    self.assertEqual(a['motivo'], 'impedimento_ficticio')

    def test_satisfecha_conserva_bloqueo_pp_y_valor_literal(self):
        d = leer(exportar_resultado_json(resultado(campo='PP', literal='1.50'), contexto()))
        self.assertEqual(d['resultado']['estado'], 'comprobacion_satisfecha')
        self.assertEqual(d['resultado']['valores_originales'], [['PP', '1.50']])
        a = next(a for a in d['restricciones']['bloqueantes'] if a['codigo'] == 'pp_sin_conversion')
        self.assertEqual(a['operaciones'], ['convertir_mm_mm_h', 'inferir_acumulacion_o_intensidad'])

    def test_versiones_regla_contrato_evaluador_y_politica_independientes(self):
        d = leer(exportar_resultado_json(resultado(), contexto()))
        self.assertEqual(d['version_esquema'], VERSION_EXPORTACION_QA)
        self.assertEqual(d['versiones'], dict(contrato_qa='1.0.0', evaluador='1.0.1', restricciones='1.0.0'))
        self.assertEqual(d['resultado']['regla']['version'], '1.0.0')
        self.assertEqual(d['resultado']['version_contrato'], '1.0.0')

    def test_evaluador_historico_desconocido_no_se_inventa(self):
        r = replace(resultado(), parametros=())
        d = leer(exportar_resultado_json(r, contexto()))
        self.assertIsNone(d['versiones']['evaluador'])
        self.assertEqual(d['resultado']['parametros'], [])

    def test_version_evaluador_ambigua_y_version_incompatible_se_rechazan(self):
        r = resultado()
        for parametros in ((('evaluador_nivel0', '1.0.1'), ('evaluador_nivel0', '1.0.1')),
                           (('evaluador_nivel0', 'desconocida'),)):
            with self.subTest(parametros=parametros), self.assertRaises(ValueError):
                exportar_resultado_json(replace(r, parametros=parametros), contexto())
        alterado = resultado()
        object.__setattr__(alterado, 'version_contrato', '9.0.0')
        with self.assertRaises(ValueError):
            exportar_resultado_json(alterado, contexto())

    def test_temp_hr_pp_y_reglas_sobre_el_mismo_campo_tienen_ids_distintos(self):
        ids = {leer(exportar_resultado_json(resultado(campo=c, regla_id=rid), contexto()))['resultado_id']
               for c in ('TEMP', 'HR', 'PP') for rid in ('ENSAYO-001', 'ENSAYO-002')}
        self.assertEqual(len(ids), 6)

    def test_identidad_varia_por_ejecucion_espacio_escenario_y_entrada(self):
        r, c = resultado(), contexto()
        contextos = (c, replace(c, espacio_id='otro:espacio'), replace(c, evaluacion_id='ejecucion-002'),
                     replace(c, entrada_id='entrada-002'), replace(c, escenario_id='S01'))
        self.assertEqual(len({leer(exportar_resultado_json(r, x))['resultado_id'] for x in contextos}), 5)
        self.assertTrue(all(leer(exportar_resultado_json(r, x))['naturaleza_identidad'] ==
                            'contextual_declarada_no_verificada' for x in contextos))

    def test_dos_filas_iguales_con_posiciones_distintas_no_colisionan(self):
        a, b = resultado(numero=1), resultado(numero=2)
        self.assertEqual(a.registro.campos_originales, b.registro.campos_originales)
        x = leer(exportar_resultado_json(a, contexto(entrada_id='fila-001')))
        y = leer(exportar_resultado_json(b, contexto(entrada_id='fila-002')))
        self.assertNotEqual(x['resultado_id'], y['resultado_id'])
        self.assertEqual(x['resultado']['registro']['id_original'], '0007')

    def test_versiones_y_configuracion_participan_en_identidad(self):
        r, c = resultado(), contexto()
        casos = ((r, c), (replace(r, regla=replace(r.regla, version='1.0.1')), c),
                 (replace(r, parametros=(('evaluador_nivel0', '1.0.2'),)), c),
                 (r, replace(c, configuracion=ConfiguracionQA())))
        self.assertEqual(len({leer(exportar_resultado_json(a, b))['resultado_id'] for a, b in casos}), 4)

    def test_contenido_no_es_identidad_y_huella_detecta_reutilizacion_contradictoria(self):
        a, c = resultado(), contexto()
        b = replace(a, diagnostico='otra_condicion_declarada')
        x, y = (leer(exportar_resultado_json(r, c)) for r in (a, b))
        self.assertEqual(x['resultado_id'], y['resultado_id'])
        self.assertNotEqual(x['huella_contenido'], y['huella_contenido'])

    def test_metadatos_no_aportados_son_null_y_declaraciones_quedan_etiquetadas(self):
        d = leer(exportar_resultado_json(resultado(), contexto()))
        self.assertIsNone(d['contexto']['configuracion'])
        self.assertIsNone(d['contexto']['metadatos_requeridos'])
        self.assertIsNone(d['contexto']['metadatos_ausentes'])
        self.assertIsNone(d['resultado']['procedencia']['fuente'])
        self.assertIn('configuracion_no_aportada_reproduccion_limitada', d['limitaciones'])
        c = contexto(metadatos_requeridos=('unidad', 'ventana'), metadatos_ausentes=('unidad',),
                     incertidumbres=('Ventana declarada sin aplicación demostrada',))
        d = leer(exportar_resultado_json(resultado(), c))
        self.assertEqual(d['contexto']['metadatos_ausentes'], ['unidad'])
        self.assertIn('inventario_metadatos_declarado_no_exhaustivo', d['limitaciones'])
        with self.assertRaises(ValueError):
            contexto(metadatos_ausentes=('unidad',))
        with self.assertRaises(ValueError):
            contexto(metadatos_requeridos=('unidad',), metadatos_ausentes=('instrumento',))

    def test_campo_ausente_no_es_cadena_vacia_ni_valor_inventado(self):
        r = replace(resultado(campo='X'), valores_originales=(('X', None),),
                    estado=E.EVALUACION_INCOMPLETA, diagnostico='campo_no_disponible')
        d = leer(exportar_resultado_json(r, contexto()))
        self.assertEqual(d['campos_objetivo_no_aportados'], ['X'])
        self.assertIsNone(d['resultado']['valores_originales'][0][1])
        vacio = leer(exportar_resultado_json(resultado(campo='X', literal=''), contexto()))
        self.assertEqual(vacio['campos_objetivo_no_aportados'], [])
        self.assertEqual(vacio['resultado']['valores_originales'][0][1], '')

    def test_hora_ubigeo_y_numeros_permanecen_textuales_sin_inferencias(self):
        for campo, literal, codigo in (('HORA', '12345', 'hora_sin_transformacion'),
                ('UBIGEO', '007777.0', 'ubigeo_sin_interpretacion'),
                ('PP', '1.50', 'pp_sin_conversion'), ('TEMP', '-9999', 'numero_sin_metrologia'),
                ('HR', '500', 'numero_sin_metrologia')):
            with self.subTest(campo=campo):
                d = leer(exportar_resultado_json(resultado(campo=campo, literal=literal), contexto()))
                self.assertEqual(d['resultado']['valores_originales'], [[campo, literal]])
                self.assertIn(codigo, [a['codigo'] for a in d['restricciones']['bloqueantes']])

    def test_unicode_y_ceros_se_preservan_sin_normalizacion(self):
        for literal in ('000123', 'NaN', 'Infinity', 'Pe\u00f1a\U0001f30e', 'n\u0303', '\u00f1', '\x00\n'):
            with self.subTest(literal=literal):
                r = resultado(literal=literal)
                texto = exportar_resultado_json(r, contexto())
                self.assertEqual(leer(texto)['resultado']['valores_originales'][0][1], literal)
                self.assertEqual(texto.encode('utf-8').decode('utf-8'), texto)
        with self.assertRaises(ValueError):
            exportar_resultado_json(resultado(literal='\ud800'), contexto())

    def test_json_estricto_rechaza_no_finitos_decimal_bytes_y_objetos(self):
        for v in (float('nan'), float('inf'), -float('inf'), 1.25, Decimal('1.20'), b'1', Path('privado')):
            with self.subTest(tipo=type(v)), self.assertRaises(TypeError):
                exportar_resultado_json(replace(resultado(), valores_originales=(('X', v),)), contexto())
        # Campo opaco de RegistroQA no validado por el constructor anterior.
        for v in (float('nan'), object(), 123):
            r = resultado()
            entrada = replace(r.registro, valores_csv_originales=(v,))
            with self.subTest(valor=type(v)), self.assertRaises(TypeError):
                exportar_resultado_json(replace(r, registro=entrada), contexto())

    def test_estados_y_objetivos_invalidos_no_generan_json(self):
        for estado in ('comprobacion_satisfecha', 'aprobado', None, True):
            with self.subTest(estado=estado), self.assertRaises(TypeError):
                exportar_resultado_json(replace(resultado(), estado=estado), contexto())
        with self.assertRaises(ValueError):
            exportar_resultado_json(replace(resultado(), valores_originales=(('X', '1'), ('X', '2'))), contexto())
        with self.assertRaises(TypeError):
            exportar_resultado_json(resultado(), {})

    def test_contexto_diagnosticos_y_tipos_externos_no_se_coaccionan(self):
        for cambios in (dict(espacio_id=''), dict(evaluacion_id='ejecucion con espacios'),
                        dict(entrada_id='x' * 129), dict(escenario_id='https://usuario@servidor'),
                        dict(configuracion={}), dict(incertidumbres=['no tipada'])):
            with self.subTest(cambios=cambios), self.assertRaises((TypeError, ValueError)):
                contexto(**cambios)
        with self.assertRaises(ValueError):
            exportar_resultado_json(replace(resultado(), diagnostico='x' * 4097), contexto())
        class Externo:
            def __str__(self):
                raise AssertionError('No invocar conversiones de objetos externos')
        r = replace(resultado(), procedencia=ProcedenciaQA())
        object.__setattr__(r.procedencia, 'documento', Externo())
        with self.assertRaises(TypeError):
            exportar_resultado_json(r, contexto())

    def test_limite_bytes_es_utf8_exacto_e_incluye_escapes_json(self):
        r, c = resultado(literal='\u00f1\x00'), contexto()
        texto = exportar_resultado_json(r, c)
        n = len(texto.encode('utf-8'))
        self.assertEqual(exportar_resultado_json(r, c, limites=LimitesExportacionQA(max_bytes=n)), texto)
        with self.assertRaises(ValueError):
            exportar_resultado_json(r, c, limites=LimitesExportacionQA(max_bytes=n - 1))

    def test_limites_texto_nodos_profundidad_y_enteros_interoperables(self):
        for limites in (LimitesExportacionQA(max_caracteres_texto=2),
                        LimitesExportacionQA(max_nodos=10), LimitesExportacionQA(max_profundidad=2)):
            with self.subTest(limites=limites), self.assertRaises(ValueError):
                exportar_resultado_json(resultado(), contexto(), limites=limites)
        for opciones in (dict(max_bytes=True), dict(max_bytes=4_194_305), dict(max_nodos=0)):
            with self.subTest(opciones=opciones), self.assertRaises(ValueError):
                LimitesExportacionQA(**opciones)
        with self.assertRaises(ValueError):
            exportar_resultado_json(resultado(numero=2**53), contexto())

    def test_procedencia_y_fechas_documentales_son_declaraciones_no_verificacion(self):
        f = Fuente('ENTIDAD_FICTICIA', 'fuente-001')
        fecha = datetime(2000, 1, 1, tzinfo=timezone.utc)
        doc = EvidenciaDocumental(f, 'recurso-ficticio', estado=EstadoVerificacion.DECLARADO,
            procedencia=ProcedenciaCatalogo('documento-ficticio', fecha, 'Declaración de fixture'))
        r = replace(resultado(), procedencia=ProcedenciaQA(f, 'recurso-ficticio', documento=doc),
                    evidencia=(ReferenciaDocumentalQA('ref-ficticia', 'No autenticada', 'a' * 64),))
        d = leer(exportar_resultado_json(r, contexto()))
        self.assertEqual(d['resultado']['procedencia']['documento']['estado'], 'declarado')
        self.assertEqual(d['resultado']['procedencia']['documento']['procedencia']['revisada_utc'], fecha.isoformat())
        self.assertIsNone(d['resultado']['procedencia']['documento']['revision_documental'])
        self.assertIn('sin_verificacion_fisica_de_originales', d['limitaciones'])
        self.assertEqual(d['resultado']['evidencia'][0]['sha256_referencia'], 'a' * 64)

    def test_determinismo_roundtrip_y_ausencia_de_mutaciones(self):
        r, c = resultado(), contexto()
        antes = asdict(r), asdict(c)
        a, b = exportar_resultado_json(r, c), exportar_resultado_json(r, c)
        self.assertEqual(a, b)
        self.assertEqual(leer(a), leer(json.dumps(leer(a), ensure_ascii=False, allow_nan=False)))
        self.assertEqual((asdict(r), asdict(c)), antes)
        self.assertEqual(tuple(f.name for f in fields(ResultadoQA)),
            ('regla', 'registro', 'procedencia', 'valores_originales', 'evidencia',
             'parametros', 'estado', 'diagnostico', 'version_contrato'))
        self.assertNotIn('restricciones', asdict(r))  # Ruta anterior sigue intacta.

    def test_no_crea_campos_globales_de_validez_ni_permisos(self):
        d = leer(exportar_resultado_json(resultado(), contexto()))
        def comprobar(v):
            if isinstance(v, dict):
                self.assertFalse({'valido', 'confiable', 'autorizado', 'permiso_ejecucion'} & set(v))
                for x in v.values(): comprobar(x)
            elif isinstance(v, list):
                for x in v: comprobar(x)
        comprobar(d)
        self.assertIn('sin_autorizacion_operativa', d['limitaciones'])

    def test_exportador_sin_red_archivos_sqlite_procesos_ni_motor_cientifico(self):
        r, c = resultado(), contexto()
        with patch('builtins.open', side_effect=AssertionError('archivo')), \
             patch('pathlib.Path.open', side_effect=AssertionError('archivo')), \
             patch('sqlite3.connect', side_effect=AssertionError('sqlite')), \
             patch('socket.socket.connect', side_effect=AssertionError('red')), \
             patch('socket.getaddrinfo', side_effect=AssertionError('dns')), \
             patch('subprocess.Popen', side_effect=AssertionError('proceso')), \
             patch('spica.calidad.experimental.limites.evaluar_limites_sinteticos',
                   side_effect=AssertionError('nivel1')), \
             patch('spica.calidad.reglas.evaluar_registro', side_effect=AssertionError('reevaluacion')):
            self.assertTrue(exportar_resultado_json(r, c))

    def test_piloto_169_identidades_estados_diagnosticos_y_restricciones(self):
        casos = casos_piloto()
        originales = tuple(asdict(r) for caso in casos for r in caso[1])
        salidas, estados = {}, Counter()
        for caso in casos:
            for r in evaluar_caso(caso):
                c = ContextoExportacionQA('spica:piloto:85c', 'regresion-001',
                    f'entrada-{r.registro.numero_registro}', escenario_id=caso[0],
                    configuracion=caso[2], incertidumbres=caso[7])
                texto = exportar_resultado_json(r, c)
                d = leer(texto)
                self.assertNotIn(d['resultado_id'], salidas)
                salidas[d['resultado_id']] = texto
                estados[d['resultado']['estado']] += 1
                self.assertEqual(d['resultado']['diagnostico'], r.diagnostico)
                self.assertEqual(d['campos_objetivo'], [k for k, _ in r.valores_originales])
                self.assertEqual(d['resultado']['regla']['version'], '1.0.0')
                self.assertEqual(d['versiones']['evaluador'], '1.0.1')
                a = d['restricciones']['informativas'] + d['restricciones']['bloqueantes']
                self.assertEqual({x['codigo'] for x in a}, {x.codigo for x in restricciones_resultado(r)})
                # JSON conserva tipos, operaciones y motivos, no solo los códigos.
                self.assertEqual({x['codigo']: (x['tipo'], x['operaciones'], x['motivo']) for x in a},
                    {x.codigo: (x.tipo.value, list(x.operaciones), x.motivo) for x in restricciones_resultado(r)})
        repetidas = {}
        for caso in reversed(casos):
            for r in reversed(evaluar_caso(caso)):
                c = ContextoExportacionQA('spica:piloto:85c', 'regresion-001',
                    f'entrada-{r.registro.numero_registro}', escenario_id=caso[0],
                    configuracion=caso[2], incertidumbres=caso[7])
                texto = exportar_resultado_json(r, c)
                repetidas[leer(texto)['resultado_id']] = texto
        self.assertEqual(salidas, repetidas)
        self.assertEqual((len(casos), sum(len(c[1]) for c in casos), len(salidas)), (12, 13, 169))
        self.assertEqual(estados, dict(comprobacion_satisfecha=119, alerta_documental=3,
            problema_tecnico=2, no_evaluado=29, evaluacion_incompleta=16))
        self.assertEqual(originales, tuple(asdict(r) for caso in casos for r in caso[1]))


if __name__ == '__main__':
    unittest.main()
