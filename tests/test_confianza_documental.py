"""Auditoría adversarial adicional. Solo metadatos inventados, sin I/O operativo."""

from dataclasses import replace
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
# Reutilizar la fixture sin importar su TestCase al namespace de descubrimiento:
# de ese modo las 63 pruebas anteriores no se ejecutan duplicadas por este módulo.
import test_aplicabilidad_cientifica as fixtures
from spica.calidad.aplicabilidad import (
    AspectoAdicional as A, EstadoAplicabilidad as E, NaturalezaEvidencia as Origen,
    NivelEvidencia as N,
)
from spica.calidad.modelos_cientificos import DimensionAplicabilidad as D, ParametroCientifico


class ConfianzaDocumentalTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.AplicabilidadCientificaTests()
        self.fixture.setUp()

    def test_parametros_sin_procedencia_no_se_suplen_con_afirmacion_generica(self):
        f = self.fixture
        expediente = f.con_dato(A.PARAMETROS_ESPECIFICOS, valor="valor-ficticio", nivel=N.VERIFICADA,
                                referencias=(f.ref_producto.identificador,))
        casos = (((), E.INFORMACION_INSUFICIENTE),
                 ((f.ref_regla.identificador,), E.COMPATIBILIDAD_DOCUMENTAL_DEMOSTRADA))
        for referencias, esperado in casos:
            with self.subTest(referencias=referencias):
                # Un parámetro documentado no debe ocultar a otro sin procedencia.
                parametros = (ParametroCientifico("modo-uno", "ficticio", referencias=(f.ref_regla.identificador,)),
                              ParametroCientifico("modo-dos", "ficticio", referencias=referencias))
                regla = replace(f.regla, parametros=parametros)
                plan = replace(f.exigir(A.PARAMETROS_ESPECIFICOS), regla=regla)
                r = f.evaluar(plan=plan, expediente=expediente)
                self.assertEqual(r.estado, esperado)
                self.assertFalse(r.ejecucion_autorizada)
                self.assertEqual("parametros_sin_procedencia_documental" in r.motivos, not bool(referencias))

    def test_reclasificacion_total_de_fixture_no_acredita_origen_ni_autoriza(self):
        f = self.fixture
        # La API no autentica la verdad de las etiquetas aportadas por Python.
        # Esta reclasificación deliberada sigue siendo inventada, no institucional.
        plan = replace(f.plan, documentos=(replace(f.doc_regla, naturaleza=Origen.DOCUMENTAL),))
        expediente = replace(f.expediente, documentos=(replace(f.doc_producto, naturaleza=Origen.DOCUMENTAL),))
        r = f.evaluar(plan=plan, expediente=expediente)
        self.assertEqual(r.estado, E.COMPATIBILIDAD_DOCUMENTAL_DEMOSTRADA)
        self.assertEqual(r.naturaleza_evidencia, Origen.DOCUMENTAL)
        self.assertIn("clasificaciones_de_evidencia_aportadas_no_autenticadas_por_este_verificador", r.restricciones)
        self.assertFalse(r.ejecucion_autorizada)
        with self.assertRaises(TypeError): bool(r)

    def test_etiqueta_territorial_igual_no_certifica_relacion_espacial(self):
        f = self.fixture
        etiqueta = "territorio-ficticio-sin-geometria"
        plan = f.exigir(D.GEOGRAFIA, etiqueta)
        expediente = f.con_dato(D.GEOGRAFIA, valor=etiqueta, nivel=N.VERIFICADA,
                                referencias=(f.ref_producto.identificador,))
        r = f.evaluar(plan=plan, expediente=expediente)
        self.assertEqual(r.estado, E.COMPATIBILIDAD_DOCUMENTAL_DEMOSTRADA)
        hallazgo = next(h for h in r.hallazgos if h.requisito_id == D.GEOGRAFIA.value)
        self.assertEqual(hallazgo.motivos, ("coincidencia_literal_documentada",))
        self.assertEqual(r.expediente.afirmaciones[-1].valor, etiqueta)
        self.assertFalse(r.ejecucion_autorizada)


if __name__ == "__main__":
    unittest.main()
