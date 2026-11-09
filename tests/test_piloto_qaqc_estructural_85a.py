"""Piloto Nivel 0 exclusivamente ficticio; no toma muestras institucionales."""

from collections import Counter
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
import csv
import tempfile
import unittest
from unittest.mock import patch

from spica.adquisicion.catalogo import EvidenciaDocumental
from spica.adquisicion.catalogo.modelos import EstadoVerificacion, ProcedenciaCatalogo
from spica.adquisicion.consultas_locales import ENCABEZADO_SENAMHI as CAB
from spica.adquisicion.nucleo import Fuente
from spica.adquisicion.verificacion import RegistroCSV, LectorCSV, PoliticaLecturaCSV
from spica.calidad import (
    ConfiguracionQA, EstadoResultadoQA as E, EstadoEvaluacionQA as EE,
    EvaluadorNivel0, FormatoDocumentadoQA, FormatoQA as F, IdentidadEstacionQA,
    LimitesQA, ProcedenciaQA, ReferenciaDocumentalQA, RegistroQA,
    adaptar_registro, evaluar_registro,
)

REGLAS_PILOTO = ('L0-EST-001', 'L0-VAL-001', 'L0-VAL-002', 'L0-VAL-004',
                 'L0-TMP-002', 'L0-ID-002', 'L0-ID-004')
EVIDENCIA = ReferenciaDocumentalQA('especificacion-ficticia-85a',
    'Contrato de fixture: numero ASCII finito y anchura textual seis; no es evidencia institucional')


def configuracion():
    return ConfiguracionQA(reglas=REGLAS_PILOTO, formatos=tuple(
        FormatoDocumentadoQA(c, f, EVIDENCIA) for c, f in (
            ('TEMP', F.NUMERO_ASCII), ('HR', F.NUMERO_ASCII), ('PP', F.NUMERO_ASCII),
            ('UBIGEO', F.SEIS_CARACTERES))))


def registro(**cambios):
    campos = {c: '' for c in CAB}
    campos.update(ID='fila-ficticia-001', ESTACION='ESTACION_FICTICIA_A',
        TEMP='+001.250', HR='56.75', PP='4.00', HORA='reloj-no-acreditado', UBIGEO='ABC123')
    campos.update(cambios)
    return adaptar_registro(RegistroCSV(2, 2, 2, tuple(campos[c] for c in CAB), True))


def casos_piloto():
    """Fixture, restricciones del expediente y resultado focal esperado.

    No se agregan campos al contrato QA. Las restricciones de uso científico
    se documentan fuera de ResultadoQA, que no las representa de forma general.
    """
    base, c = registro(), configuracion()
    faltante = RegistroQA(2, base.id_original, base.estacion_literal, 2, 2,
        tuple((k, v) for k, v in base.campos_originales if k != 'TEMP'), True)
    extra = adaptar_registro(RegistroCSV(2, 2, 2, base.valores_csv_originales + ('extra-ficticio',), True))
    ambigua = replace(c, identidades=tuple(IdentidadEstacionQA(base.estacion_literal, i, EVIDENCIA)
        for i in ('identidad-ficticia-a', 'identidad-ficticia-b')))
    duplicada = replace(base, numero_registro=3, linea_inicial=3, linea_final=3)
    comunes = ('sin_aptitud_cientifica_acreditada', 'sin_zona_o_coordenadas_asignadas')
    # ID, entradas, configuración, regla/campo focales, estado, código, restricciones.
    return (
        ('S01', (base,), c, 'L0-EST-001', None, E.COMPROBACION_SATISFECHA, 'estructura_recibida_coherente', comunes),
        ('S02', (faltante,), c, 'L0-VAL-001', 'TEMP', E.EVALUACION_INCOMPLETA, 'campo_no_disponible', comunes),
        ('S03', (registro(TEMP=''),), c, 'L0-VAL-001', 'TEMP', E.PROBLEMA_TECNICO, 'campo_vacio_sin_inferir_medicion', comunes),
        ('S04', (registro(TEMP='-3.125e1'),), c, 'L0-VAL-002', 'TEMP', E.COMPROBACION_SATISFECHA, 'numero_finito_interpretable', comunes),
        ('S05', (registro(TEMP='1,25'),), c, 'L0-VAL-002', 'TEMP', E.PROBLEMA_TECNICO, 'numero_no_interpretable', comunes),
        ('S06', (extra,), c, 'L0-EST-001', None, E.EVALUACION_INCOMPLETA, 'estructura_no_evaluable', comunes),
        ('S07', (base,), ambigua, 'L0-ID-002', 'ESTACION', E.ALERTA_DOCUMENTAL, 'identidad_documental_ambigua', comunes),
        ('S08', (registro(HORA='12345'),), c, 'L0-TMP-002', 'HORA', E.NO_EVALUADO, 'formato_documental_no_disponible', comunes),
        ('S09', (registro(UBIGEO='007777.0'),), c, 'L0-ID-004', 'UBIGEO', E.ALERTA_DOCUMENTAL, 'representacion_documental_discrepante', comunes),
        ('S10', (registro(PP='1.50'),), c, 'L0-VAL-002', 'PP', E.COMPROBACION_SATISFECHA, 'numero_finito_interpretable', comunes + ('unidad_PP_ambigua_no_convertir',)),
        ('S11', (base,), replace(c, formatos=()), 'L0-VAL-004', 'TEMP', E.NO_EVALUADO, 'formato_documental_no_disponible', comunes),
        ('S12', (base, duplicada), c, 'L0-EST-001', None, E.COMPROBACION_SATISFECHA, 'estructura_recibida_coherente', comunes + ('igualdad_literal_no_es_mismo_evento_cientifico',)),
    )


def evaluar_caso(caso):
    return tuple(x for r in caso[1] for x in evaluar_registro(r, ProcedenciaQA(), configuracion=caso[2]))


class PilotoQAQC85ATests(unittest.TestCase):
    def test_doce_escenarios_focales_reproducibles_sin_alterar_originales(self):
        casos = casos_piloto()
        self.assertEqual(len(casos), 12)
        for caso in casos:
            cid, registros, c, regla, campo, estado, diagnostico, restricciones = caso
            originales = tuple((r.campos_originales, r.valores_csv_originales) for r in registros)
            with self.subTest(caso=cid):
                a, b = evaluar_caso(caso), evaluar_caso(caso)
                self.assertEqual(a, b)
                self.assertEqual(len(a), 13 * len(registros))
                focales = [x for x in a if x.regla.identificador == regla
                    and (campo is None or campo in dict(x.valores_originales))]
                self.assertEqual(len(focales), len(registros))
                self.assertTrue(all(x.estado is estado and x.diagnostico == diagnostico for x in focales))
                self.assertEqual(originales, tuple((r.campos_originales, r.valores_csv_originales) for r in registros))
                self.assertTrue(restricciones)

    def test_cardinalidad_y_trazas_incompletas_distinguen_variables(self):
        vistos, reglas, total = set(), Counter(), 0
        for caso in casos_piloto():
            for r in evaluar_caso(caso):
                clave = (caso[0], r.registro.numero_registro, r.regla.identificador,
                         tuple(k for k, _ in r.valores_originales))
                self.assertNotIn(clave, vistos)
                vistos.add(clave); reglas[r.regla.identificador] += 1; total += 1
                self.assertEqual((r.regla.version, r.version_contrato), ('1.0.0', '1.0.0'))
                self.assertIsInstance(r.procedencia, ProcedenciaQA)
        self.assertEqual(total, 169)  # 13 entradas × (4 reglas por fila + 3 por variable × 3).
        self.assertEqual(reglas, {i:39 if i.startswith('L0-VAL-') else 13 for i in REGLAS_PILOTO})
        fila_invalida = casos_piloto()[5]
        for rid in ('L0-VAL-001', 'L0-VAL-002', 'L0-VAL-004'):
            resultados = [r for r in evaluar_caso(fila_invalida) if r.regla.identificador == rid]
            self.assertEqual([tuple(k for k, _ in r.valores_originales) for r in resultados],
                             [('TEMP',), ('HR',), ('PP',)])
            self.assertTrue(all(r.registro.valores_csv_originales[-1] == 'extra-ficticio' for r in resultados))

    def test_admision_csv_rechaza_columna_inesperada_y_preserva_fila_extra(self):
        with tempfile.TemporaryDirectory(prefix='spica-85a-csv-') as d:
            raiz = Path(d).resolve()
            self.assertEqual(raiz.parent, Path(tempfile.gettempdir()).resolve())
            ruta = raiz/'fixture.csv'
            base = registro().valores_csv_originales
            for cabecera, fila, motivo in ((CAB + ('COLUMNA_FICTICIA',), base + ('extra',), 'encabezado_no_admitido'),
                    (CAB, base + ('extra',), 'eof')):
                with self.subTest(motivo=motivo):
                    with ruta.open('w', encoding='utf-8', newline='') as f:
                        w = csv.writer(f); w.writerow(cabecera); w.writerow(fila)
                    antes = ruta.read_bytes(), ruta.stat().st_mtime_ns
                    entrada = LectorCSV(ruta, codificacion='utf-8', delimitador=',', campos_esperados=16,
                        politica=PoliticaLecturaCSV(max_bytes_archivo=4096, max_registros=5))
                    with EvaluadorNivel0(entrada, ProcedenciaQA(), configuracion=configuracion(),
                            limites=LimitesQA(max_registros=3, max_resultados=100)) as motor:
                        resultados = tuple(motor)
                    self.assertEqual(motor.informe.motivo_fin, motivo)
                    self.assertIs(motor.informe.estado, EE.INCOMPLETA)
                    if motivo == 'encabezado_no_admitido': self.assertEqual(resultados, ())
                    else:
                        self.assertTrue(all(x.estado is E.EVALUACION_INCOMPLETA for x in resultados))
                        self.assertEqual(resultados[0].registro.valores_csv_originales, fila)
                    self.assertEqual(antes, (ruta.read_bytes(), ruta.stat().st_mtime_ns))

    def test_tipos_no_textuales_y_cabeceras_duplicadas_no_se_coaccionan(self):
        base = registro()
        for valores in ((('TEMP', 1.25),), (('TEMP', '1'), ('TEMP', '2'))):
            with self.subTest(valores=valores), self.assertRaises(ValueError):
                replace(base, campos_originales=valores)

    def test_sin_llamadas_documentales_cientificas_red_archivos_o_sqlite(self):
        with patch('builtins.open', side_effect=AssertionError('archivo')), \
             patch('pathlib.Path.open', side_effect=AssertionError('archivo')), \
             patch('sqlite3.connect', side_effect=AssertionError('sqlite')), \
             patch('socket.socket.connect', side_effect=AssertionError('red')), \
             patch('subprocess.Popen', side_effect=AssertionError('proceso')), \
             patch('herramientas.vinculacion_documental.CotejadorDocumental.cotejar', side_effect=AssertionError('84L')), \
             patch('spica.calidad.experimental.limites.evaluar_limites_sinteticos', side_effect=AssertionError('nivel1')):
            self.assertEqual(sum(len(evaluar_caso(c)) for c in casos_piloto()), 169)

    def test_estado_documental_declarado_no_se_promueve_por_qa(self):
        fuente = Fuente('emisor-ficticio', 'fuente-ficticia')
        fecha = datetime(2000, 1, 1, tzinfo=timezone.utc)
        proc = ProcedenciaCatalogo('referencia-ficticia', fecha, 'declaracion sintetica', 'no es una comprobacion fisica')
        estados = (EstadoVerificacion.DESCONOCIDO, EstadoVerificacion.DECLARADO, EstadoVerificacion.VERIFICADO)
        for estado in estados:
            doc = EvidenciaDocumental(fuente, 'recurso-ficticio', estado=estado,
                procedencia=proc if estado is not EstadoVerificacion.DESCONOCIDO else None,
                descubierta_utc=fecha if estado is EstadoVerificacion.VERIFICADO else None)
            p = ProcedenciaQA(fuente, 'recurso-ficticio', documento=doc)
            r, = tuple(evaluar_registro(registro(), p, configuracion=ConfiguracionQA(reglas=('L0-PROV-006',))))
            self.assertIs(r.procedencia.documento, doc)
            self.assertIs(doc.estado, estado)
            self.assertIs(r.estado, E.COMPROBACION_SATISFECHA)  # Solo asociación, nunca autenticación.
            self.assertIsNone(doc.revision_documental)

    def test_pp_unidad_desconocida_y_hora_ubigeo_no_se_reconstruyen(self):
        for i, campo, literal in ((7, 'HORA', '12345'), (8, 'UBIGEO', '007777.0'), (9, 'PP', '1.50')):
            caso = casos_piloto()[i]
            r = evaluar_caso(caso)
            self.assertEqual(dict(caso[1][0].campos_originales)[campo], literal)
            self.assertTrue(all(dict(x.valores_originales).get(campo, literal) == literal for x in r))
            self.assertIsNone(caso[2].zona_documentada)
            self.assertTrue(all(not x.parametros or not any(k in ('unidad', 'zona_asignada', 'CRS') for k, _ in x.parametros) for x in r))

    def test_filas_iguales_no_son_instantes_duplicados_ni_se_deduplican(self):
        caso = casos_piloto()[-1]
        a, b = caso[1]
        self.assertEqual(a.valores_csv_originales, b.valores_csv_originales)
        self.assertNotEqual(a.numero_registro, b.numero_registro)
        r = evaluar_caso(caso)
        self.assertEqual(len(r), 26)
        self.assertEqual({x.registro.numero_registro for x in r}, {2, 3})
        self.assertIsNone(caso[2].zona_documentada)
        self.assertIsNone(a.procedencia_original)


if __name__ == '__main__':
    unittest.main()
