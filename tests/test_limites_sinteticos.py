"""Ensayos exclusivamente inventados. No abren RAW, staging o catálogos operativos."""

from dataclasses import FrozenInstanceError, replace
from decimal import Decimal, InvalidOperation, localcontext
import json
from pathlib import Path
import sys
from threading import Event
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from spica.calidad import EstadoEvaluacionQA, ProcedenciaQA, adaptar_registro, evaluar_registro
from spica.calidad.catalogo_cientifico import CatalogoReglasCientificas
from spica.calidad.experimental import (
    EstadoLimiteExperimental as E, EvidenciaSintetica, ObservacionSintetica,
    ReglaLimitesSintetica, TipoEvidenciaExperimental, evaluar_limites_sinteticos,
)
from spica.calidad.modelos_cientificos import (
    ContextoCientifico, EstadoReglaCientifica, HabilitacionCientifica, RevisionReglaCientifica,
)
from spica.adquisicion.consultas_locales import ObservacionLocal
from spica.adquisicion.verificacion import RegistroCSV
from spica.perfilado import LimitesPerfil
from spica.perfilado.interpretacion import interpretar_numero
from test_expediente_qa_nivel1 import FIXTURE, propuestas_aisladas


class LimitesSinteticosTests(unittest.TestCase):
    def setUp(self):
        self.evidencia = EvidenciaSintetica("FIXTURE-INTERVALOS", "fixture-v1", "Datos y parámetros inventados para ensayo")
        self.regla = ReglaLimitesSintetica("EXP-LIM-INTERVALO", "ensayo-v1", "VAR_SINTETICA", "u_sintetica",
            "modalidad_sintetica", "frecuencia_sintetica", Decimal("-2.5"), Decimal("7.5"), True, True, self.evidencia)
        self.observacion = ObservacionSintetica("OBS-SINT-0001", "VAR_SINTETICA", "1.25", "u_sintetica",
            "modalidad_sintetica", "frecuencia_sintetica", self.evidencia)

    def evaluar(self, valor=None, *, regla=None, **cambios):
        if valor is not None:
            cambios["valor_original"] = valor
        return evaluar_limites_sinteticos(regla or self.regla, replace(self.observacion, **cambios))

    def test_valor_dentro_intervalo(self):
        r = self.evaluar("1.25")
        self.assertEqual((r.estado, r.valor_numerico), (E.CONDICION_SATISFECHA, Decimal("1.25")))
        self.assertEqual(r.estado_evaluacion, EstadoEvaluacionQA.COMPLETA)

    def test_valor_debajo_no_implica_medicion_invalida(self):
        r = self.evaluar("-99.00")
        self.assertEqual((r.estado,r.motivo), (E.CONDICION_NO_SATISFECHA,"por_debajo_del_intervalo_sintetico"))
        self.assertEqual(r.observacion.valor_original, "-99.00")
        self.assertFalse(hasattr(r, "cientificamente_invalida"))

    def test_valor_encima_conservado(self):
        r = self.evaluar("9000.00")
        self.assertEqual((r.estado,r.motivo), (E.CONDICION_NO_SATISFECHA,"por_encima_del_intervalo_sintetico"))
        self.assertEqual(r.observacion.valor_original, "9000.00")

    def test_igualdad_en_ambos_extremos_inclusivos(self):
        for valor in ("-2.5", "7.5"):
            with self.subTest(valor=valor): self.assertEqual(self.evaluar(valor).estado, E.CONDICION_SATISFECHA)

    def test_extremo_inferior_exclusivo(self):
        r = self.evaluar("-2.5", regla=replace(self.regla, incluir_inferior=False))
        self.assertEqual((r.estado,r.motivo), (E.CONDICION_NO_SATISFECHA,"extremo_inferior_excluido"))

    def test_extremo_superior_exclusivo(self):
        r = self.evaluar("7.5", regla=replace(self.regla, incluir_superior=False))
        self.assertEqual((r.estado,r.motivo), (E.CONDICION_NO_SATISFECHA,"extremo_superior_excluido"))

    def test_combinaciones_de_inclusividad(self):
        for inferior in (False,True):
            for superior in (False,True):
                regla = replace(self.regla, incluir_inferior=inferior, incluir_superior=superior)
                with self.subTest(inferior=inferior,superior=superior):
                    self.assertEqual(self.evaluar("-2.5", regla=regla).estado is E.CONDICION_SATISFECHA, inferior)
                    self.assertEqual(self.evaluar("7.5", regla=regla).estado is E.CONDICION_SATISFECHA, superior)

    def test_limites_invertidos_no_son_configuracion_valida(self):
        with self.assertRaisesRegex(ValueError,"invertidos"):
            replace(self.regla, limite_inferior=Decimal("8"))

    def test_intervalo_puntual_y_intervalo_vacio(self):
        regla = replace(self.regla, limite_inferior=Decimal("1.25"), limite_superior=Decimal("1.25"))
        self.assertEqual(self.evaluar("1.25", regla=regla).estado, E.CONDICION_SATISFECHA)
        for campo in ("incluir_inferior","incluir_superior"):
            with self.subTest(campo=campo), self.assertRaisesRegex(ValueError,"vacío"): replace(regla, **{campo:False})

    def test_limites_requieren_decimal_finito_y_presupuesto(self):
        for valor in (0, 1.5, "-2.5", Decimal("NaN"), Decimal("Infinity"), Decimal("1e1001"), Decimal("1"*65)):
            with self.subTest(valor=valor), self.assertRaises(ValueError): replace(self.regla, limite_inferior=valor)
        with self.assertRaises(TypeError): replace(self.regla, incluir_inferior=1)

    def test_valor_vacio(self):
        r = self.evaluar("")
        self.assertEqual((r.estado,r.motivo), (E.ERROR_TECNICO,"valor_vacio"))
        self.assertEqual(r.observacion.valor_original, "")

    def test_valores_no_numericos_sin_correccion(self):
        for valor in ("texto", "1,25", " 1.25", "1_000", "１２"):
            with self.subTest(valor=valor):
                r = self.evaluar(valor)
                self.assertEqual((r.estado,r.motivo), (E.ERROR_TECNICO,"valor_no_numerico"))
                self.assertEqual(r.observacion.valor_original, valor)

    def test_nan_infinity_no_se_comparan(self):
        for valor in ("NaN", "sNaN", "Infinity", "-Infinity", "+Inf"):
            with self.subTest(valor=valor):
                r = self.evaluar(valor)
                self.assertEqual((r.estado,r.motivo), (E.ERROR_TECNICO,"literal_no_finito"))
                self.assertIsNone(r.valor_numerico)

    def test_negativos_y_decimales_exactos(self):
        for valor in ("-1.25", "-0.00", "+001.2500", ".125", "1.25e0"):
            with self.subTest(valor=valor):
                r = self.evaluar(valor)
                self.assertEqual(r.estado, E.CONDICION_SATISFECHA)
                self.assertEqual(r.valor_numerico, Decimal(valor))
                self.assertEqual(r.observacion.valor_original, valor)

    def test_precision_no_depende_de_float_ni_contexto_de_redondeo(self):
        regla = replace(self.regla, limite_inferior=Decimal("1.0000000000000001"), limite_superior=Decimal("1.0000000000000002"))
        with localcontext() as contexto:
            contexto.prec = 2
            self.assertEqual(self.evaluar("1.0000000000000001", regla=regla).estado, E.CONDICION_SATISFECHA)
            self.assertEqual(self.evaluar("1.0000000000000000", regla=regla).estado, E.CONDICION_NO_SATISFECHA)

    def test_parser_existente_se_utiliza_una_vez_por_valor(self):
        with patch("spica.calidad.experimental.limites.interpretar_numero", wraps=interpretar_numero) as parser:
            self.evaluar()
        parser.assert_called_once_with("1.25", limites=self.regla.politica_numerica)

    def test_unidad_desconocida_en_dato_o_regla(self):
        a = self.evaluar(unidad=None)
        b = self.evaluar(regla=replace(self.regla, unidad=None))
        for r in (a,b):
            self.assertEqual((r.estado,r.motivo), (E.NO_EVALUADO_UNIDAD,"unidad_desconocida"))
            self.assertEqual(r.estado_evaluacion, EstadoEvaluacionQA.NO_EVALUADA)

    def test_unidad_incompatible_no_se_convierte(self):
        for unidad in ("otra_unidad", "u_sintetica "):
            with self.subTest(unidad=unidad):
                r = self.evaluar(unidad=unidad)
                self.assertEqual((r.estado,r.motivo), (E.NO_EVALUADO_UNIDAD,"unidad_incompatible"))
                self.assertEqual(r.observacion.unidad, unidad)

    def test_frecuencia_desconocida_o_incompatible(self):
        for frecuencia in (None,"otra_frecuencia"):
            with self.subTest(frecuencia=frecuencia):
                r = self.evaluar(frecuencia=frecuencia)
                self.assertEqual(r.estado,E.NO_EVALUADO_FRECUENCIA)
                self.assertIsNone(r.valor_numerico)

    def test_modalidad_desconocida_o_incompatible(self):
        for modalidad in (None,"otra_modalidad"):
            with self.subTest(modalidad=modalidad):
                self.assertEqual(self.evaluar(modalidad=modalidad).estado,E.NO_EVALUADO_MODALIDAD)

    def test_modalidad_instantanea_no_equivale_a_promedio(self):
        regla = replace(self.regla, modalidad="promedio_sintetico")
        r = self.evaluar(modalidad="instantaneo_sintetico", regla=regla)
        self.assertEqual(r.estado,E.NO_EVALUADO_MODALIDAD)

    def test_variable_distinta_no_se_infiere(self):
        self.assertEqual(self.evaluar(variable="OTRA_VARIABLE").estado,E.NO_EVALUADO_VARIABLE)

    def test_evidencia_de_parametros_ausente_no_evalua(self):
        with patch("spica.calidad.experimental.limites.interpretar_numero") as parser:
            r = self.evaluar(regla=replace(self.regla,evidencia_parametros=None))
        self.assertEqual(r.estado,E.NO_EVALUADO_EVIDENCIA)
        parser.assert_not_called()

    def test_evidencia_de_otra_fixture_o_version_no_evalua(self):
        for evidencia in (replace(self.evidencia,fixture_id="FIXTURE-OTRA"),replace(self.evidencia,version="fixture-v2")):
            with self.subTest(evidencia=evidencia):
                r = self.evaluar(regla=replace(self.regla,evidencia_parametros=evidencia))
                self.assertEqual(r.estado,E.NO_EVALUADO_EVIDENCIA)

    def test_identificador_documental_no_habilita_un_ensayo(self):
        for id_regla in ("L1-CAND-TEMP-LIM", "L1-CAND-HR-LIM", "L0-VAL-001"):
            with self.subTest(id_regla=id_regla), self.assertRaises(ValueError): replace(self.regla,identificador=id_regla)
        with self.assertRaises(ValueError): EvidenciaSintetica("MT-DRD-002", "02", "Documento oficial no es fixture")
        with self.assertRaises(TypeError): replace(self.regla,evidencia_parametros="MT-DRD-002")

    def test_todas_las_propuestas_del_expediente_son_rechazadas(self):
        expediente = json.loads(FIXTURE.read_text(encoding="utf-8"))
        catalogo = CatalogoReglasCientificas()
        for c, regla in propuestas_aisladas(expediente):
            entrada = catalogo.registrar(regla)
            h = catalogo.comprobar_habilitacion(regla.identificador,regla.version,ContextoCientifico())
            for objeto in (regla,entrada,h):
                with self.subTest(regla=regla.identificador,tipo=type(objeto)), self.assertRaises(TypeError):
                    evaluar_limites_sinteticos(objeto,self.observacion)
            self.assertFalse(h.ejecucion_autorizada)
        self.assertTrue(all(r.estado is EstadoReglaCientifica.PROPUESTA for r in catalogo.listar()))

    def test_estados_del_catalogo_no_son_autorizaciones(self):
        # Dobles de contrato, no aprobaciones ni decisiones humanas ficticias.
        for estado in EstadoReglaCientifica:
            etiqueta = Mock(spec=RevisionReglaCientifica)
            etiqueta.estado = estado
            with self.subTest(estado=estado), patch("spica.calidad.experimental.limites.interpretar_numero") as parser:
                with self.assertRaises(TypeError): evaluar_limites_sinteticos(etiqueta,self.observacion)
                parser.assert_not_called()

    def test_aprobada_y_elegible_sin_autorizacion_sigue_bloqueada(self):
        etiqueta = Mock(spec=RevisionReglaCientifica)
        etiqueta.estado = EstadoReglaCientifica.APROBADA
        h = HabilitacionCientifica(etiqueta,True,("ejecucion_nivel1_no_implementada",))
        self.assertFalse(h.ejecucion_autorizada)
        with self.assertRaises(FrozenInstanceError): h.ejecucion_autorizada = True
        with self.assertRaises(TypeError): evaluar_limites_sinteticos(h,self.observacion)

    def test_trazabilidad_explicita_y_sin_certificado_cientifico(self):
        r = self.evaluar()
        self.assertIs(r.regla,self.regla)
        self.assertEqual(r.observacion.observacion_id,"OBS-SINT-0001")
        self.assertEqual(r.observacion.variable,"VAR_SINTETICA")
        self.assertEqual((r.regla.limite_inferior,r.regla.limite_superior),(Decimal("-2.5"),Decimal("7.5")))
        self.assertEqual(r.regla.evidencia_parametros.tipo,TipoEvidenciaExperimental.FIXTURE_SINTETICA)
        self.assertTrue(r.datos_sinteticos and r.observacion.datos_sinteticos)
        self.assertFalse(r.ejecucion_operativa_autorizada)
        self.assertEqual((r.version_evaluador,r.version_interpretacion),("1.0.0","1.0.0"))

    def test_versiones_de_regla_distintas_no_se_confunden(self):
        a = self.evaluar()
        b = self.evaluar(regla=replace(self.regla,version="ensayo-v2"))
        self.assertEqual(a.estado,b.estado)
        self.assertNotEqual(a.regla.version,b.regla.version)
        self.assertNotEqual(a,b)

    def test_cancelacion_previa_no_interpreta(self):
        evento = Event(); evento.set()
        with patch("spica.calidad.experimental.limites.interpretar_numero") as parser:
            r = evaluar_limites_sinteticos(self.regla,self.observacion,cancelacion=evento)
        self.assertEqual((r.estado,r.motivo),(E.EVALUACION_INCOMPLETA,"cancelado_antes_de_evaluar"))
        self.assertEqual(r.estado_evaluacion,EstadoEvaluacionQA.INCOMPLETA)
        parser.assert_not_called()

    def test_cancelacion_durante_interpretacion_no_compara(self):
        evento = Event()
        def interpretar(texto,**kw):
            r = interpretar_numero(texto,**kw); evento.set(); return r
        with patch("spica.calidad.experimental.limites.interpretar_numero",side_effect=interpretar):
            r = evaluar_limites_sinteticos(self.regla,self.observacion,cancelacion=evento)
        self.assertEqual((r.estado,r.motivo),(E.EVALUACION_INCOMPLETA,"cancelado_tras_interpretacion"))
        self.assertIsNone(r.valor_numerico)

    def test_presupuesto_agotado_no_es_dato_cientificamente_erroneo(self):
        for valor in ("1"*129,"1"*65,"1e1001"):
            with self.subTest(valor=valor):
                r = self.evaluar(valor)
                self.assertEqual((r.estado,r.motivo),(E.EVALUACION_INCOMPLETA,"presupuesto_numerico_excedido"))
                self.assertEqual(r.observacion.valor_original,valor)

    def test_presupuesto_numerico_compartido_configurable(self):
        regla = replace(self.regla,politica_numerica=LimitesPerfil(max_caracteres_numero=10))
        self.assertEqual(self.evaluar("1.2345678901",regla=regla).estado,E.EVALUACION_INCOMPLETA)
        self.assertEqual(self.evaluar("1.2",regla=regla).estado,E.CONDICION_SATISFECHA)

    def test_error_tecnico_decimal_sin_exponer_excepcion(self):
        with patch("spica.calidad.experimental.limites.interpretar_numero",side_effect=InvalidOperation("detalle-no-publicable")):
            r = self.evaluar()
        self.assertEqual((r.estado,r.motivo),(E.ERROR_TECNICO,"error_de_interpretacion_decimal"))
        self.assertNotIn("detalle-no-publicable",r.motivo)

    def test_interrupcion_se_propaga_sin_recursos_abiertos(self):
        with patch("spica.calidad.experimental.limites.interpretar_numero",side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt): self.evaluar()

    def test_original_y_configuracion_inmutables_y_deterministas(self):
        r1 = self.evaluar("+001.2500")
        r2 = self.evaluar("+001.2500")
        self.assertEqual(r1,r2)
        self.assertEqual(self.observacion.valor_original,"1.25")
        with self.assertRaises(FrozenInstanceError): r1.observacion.valor_original = "otro"
        with self.assertRaises(FrozenInstanceError): r1.regla.limite_inferior = Decimal("0")

    def test_rechaza_lectores_registros_reales_rutas_y_dicts(self):
        for objeto in (Mock(spec=ObservacionLocal),RegistroCSV(2,2,2,("1",),True),Path("fixture.csv"),
                       {"valor_original":"1.25"},"fixture.csv"):
            with self.subTest(tipo=type(objeto)), self.assertRaises(TypeError): evaluar_limites_sinteticos(self.regla,objeto)
        with self.assertRaises(TypeError): evaluar_limites_sinteticos(self.regla,self.observacion,cancelacion=lambda:True)
        with self.assertRaises(ValueError): replace(self.observacion,valor_original=1.25)

    def test_evaluador_no_usa_almacenamiento_ni_archivos(self):
        with patch("builtins.open",side_effect=AssertionError("I/O no autorizado")), \
             patch("io.open",side_effect=AssertionError("I/O no autorizado")), \
             patch("os.stat",side_effect=AssertionError("I/O no autorizado")), \
             patch("os.scandir",side_effect=AssertionError("I/O no autorizado")), \
             patch("sqlite3.connect",side_effect=AssertionError("SQLite no autorizado")):
            r = evaluar_limites_sinteticos(self.regla,self.observacion)
        self.assertEqual(r.estado,E.CONDICION_SATISFECHA)

    def test_nivel0_conserva_sus_resultados(self):
        fila = ("ID-SINTETICO","ESTACION-FIXTURE","20000101","00000","1","2","3","1.25","2.5","3.5",
                "RED-FIXTURE","DEP","PROV","DIST","12345.0","20000101")
        registro = adaptar_registro(RegistroCSV(2,2,2,fila,True))
        antes = tuple(evaluar_registro(registro,ProcedenciaQA()))
        self.evaluar()
        despues = tuple(evaluar_registro(registro,ProcedenciaQA()))
        self.assertEqual(antes,despues)
        self.assertEqual(len(despues),30)
        self.assertEqual(registro.valores_csv_originales,fila)


if __name__ == "__main__":
    unittest.main()
