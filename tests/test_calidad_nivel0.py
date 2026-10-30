"""QA/QC técnico/documental con fixtures aisladas; nunca utiliza RAW operativo."""

import csv
from dataclasses import replace
from datetime import date
from decimal import Decimal
from pathlib import Path
import shutil
import sys
import tempfile
from threading import Event
import tracemalloc
import unittest
from unittest.mock import patch
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from spica.adquisicion.catalogo import EvidenciaDocumental
from spica.adquisicion.consultas_locales import (
    ConsultaLocal, ConsultorLocalCSV, ENCABEZADO_SENAMHI as CAB, LimitesConsulta, ProcedenciaLocal,
)
from spica.adquisicion.nucleo import Fuente
from spica.adquisicion.verificacion import LectorCSV, PoliticaLecturaCSV, RegistroCSV
from spica.calidad import (
    CategoriaQA as C, ConfiguracionQA, DatoDocumentadoQA, EstadoEvaluacionQA as EE,
    EstadoResultadoQA as E, EvaluadorNivel0, FormatoDocumentadoQA, FormatoQA as F,
    IdentidadEstacionQA, LimitesQA, ProcedenciaQA, ReferenciaDocumentalQA,
    REGLAS_NIVEL0, adaptar_registro, evaluar_registro,
)
from spica.perfilado import LimitesPerfil
from spica.perfilado.interpretacion import interpretar_numero, interpretar_fecha_civil, clasificar_hora_literal


class CalidadNivel0Tests(unittest.TestCase):
    def setUp(self):
        padre = Path(tempfile.gettempdir()).resolve()
        self.base = padre / ("spica-qa-test-" + uuid4().hex)
        self.base.mkdir(mode=0o755)
        assert self.base.resolve().is_relative_to(padre)
        self.addCleanup(shutil.rmtree, self.base)
        self.ruta = self.base / "sintetico.csv"
        self.local = ProcedenciaLocal(Fuente("SENAMHI", "SENAMHI"), "recurso-sintetico", "activo-sintetico", "1" * 64)
        self.procedencia = ProcedenciaQA.desde_local(self.local, adquisicion_id="adquisicion-sintetica")
        self.evidencia = ReferenciaDocumentalQA("documento-sintetico", "Formatos declarados para la fixture")
        self.configuracion = ConfiguracionQA(formatos=tuple(FormatoDocumentadoQA(c, f, self.evidencia)
            for c, f in (("FECHA", F.AAAAMMDD), ("HORA", F.HHMMSS), ("UBIGEO", F.SEIS_CARACTERES),
                         ("TEMP", F.NUMERO_ASCII), ("HR", F.NUMERO_ASCII), ("PP", F.NUMERO_ASCII))))
        self.escribir(self.fila())

    def fila(self, **cambios):
        valores = dict(zip(CAB, ("0001", "IMATA", "20150101", "00000", "-71.0906", "-15.8427",
            "4475.0", "01.20", "90.0", "0.0", "RBON", "AREQUIPA", "CAYLLOMA",
            "SAN_ANTONIO_DE_CHUCA", "40514.0", "20240630")))
        valores.update(cambios)
        return tuple(valores[c] for c in CAB)

    def escribir(self, *filas, cabecera=CAB):
        with self.ruta.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(cabecera)
            w.writerows(filas)

    def evaluar(self, *, lector=None, configuracion=None, procedencia=None, **opciones):
        entrada = lector if lector is not None else LectorCSV(self.ruta, delimitador=",", campos_esperados=16)
        with EvaluadorNivel0(entrada, procedencia or self.procedencia,
                configuracion=configuracion or self.configuracion, **opciones) as motor:
            resultados = tuple(motor)
        return resultados, motor.informe

    def resultado(self, resultados, regla, campo=None):
        return next(r for r in resultados if r.regla.identificador == regla
                    and (campo is None or any(c == campo for c, _ in r.valores_originales)))

    def test_registro_cerrado_ids_versiones_y_contrato(self):
        r, informe = self.evaluar()
        self.assertEqual(len(REGLAS_NIVEL0), 22)
        self.assertEqual(len({x.identificador for x in REGLAS_NIVEL0}), 22)
        self.assertTrue(all(x.version == "1.0.0" for x in REGLAS_NIVEL0))
        self.assertEqual((len(r), informe.registros_examinados, informe.registros_finalizados), (30, 1, 1))
        self.assertTrue(all(x.version_contrato == "1.0.0" for x in r))
        self.assertEqual(informe.estado, EE.COMPLETA)

    def test_vacio_y_presente_no_infiere_medicion_ausente(self):
        self.escribir(self.fila(TEMP="", HR=" ", PP="0"))
        r, _ = self.evaluar()
        self.assertEqual(self.resultado(r, "L0-VAL-001", "TEMP").estado, E.PROBLEMA_TECNICO)
        self.assertEqual(self.resultado(r, "L0-VAL-001", "HR").estado, E.COMPROBACION_SATISFECHA)
        self.assertEqual(self.resultado(r, "L0-VAL-002", "TEMP").estado, E.NO_EVALUADO)
        self.assertEqual(self.resultado(r, "L0-VAL-002", "HR").estado, E.PROBLEMA_TECNICO)

    def test_numeros_interpretables_y_texto_invalido(self):
        self.escribir(self.fila(TEMP="-1.25", HR="1,2", PP="1e2"))
        r, _ = self.evaluar()
        self.assertEqual([self.resultado(r, "L0-VAL-002", v).estado for v in ("TEMP", "HR", "PP")],
                         [E.COMPROBACION_SATISFECHA, E.PROBLEMA_TECNICO, E.COMPROBACION_SATISFECHA])

    def test_nan_e_infinity_son_regla_especifica(self):
        for texto in ("NaN", "Infinity", "-Infinity", "sNaN"):
            with self.subTest(texto=texto):
                self.escribir(self.fila(TEMP=texto))
                r, _ = self.evaluar()
                self.assertEqual(self.resultado(r, "L0-VAL-003", "TEMP").estado, E.PROBLEMA_TECNICO)
                self.assertEqual(self.resultado(r, "L0-VAL-002", "TEMP").estado, E.NO_EVALUADO)
                self.assertEqual(self.resultado(r, "L0-VAL-004", "TEMP").estado, E.ALERTA_DOCUMENTAL)

    def test_extremos_y_marcadores_numericos_se_conservan(self):
        self.escribir(self.fila(TEMP="-9999", HR="500", PP="9e999"))
        r, _ = self.evaluar()
        for campo, original in (("TEMP", "-9999"), ("HR", "500"), ("PP", "9e999")):
            x = self.resultado(r, "L0-VAL-002", campo)
            self.assertEqual(x.estado, E.COMPROBACION_SATISFECHA)
            self.assertEqual(dict(x.valores_originales)[campo], original)

    def test_presupuesto_numerico_es_incompleto_no_numero_invalido(self):
        self.escribir(self.fila(TEMP="1e1001"))
        r, informe = self.evaluar()
        self.assertEqual(self.resultado(r, "L0-VAL-002", "TEMP").estado, E.EVALUACION_INCOMPLETA)
        self.assertEqual(informe.estado, EE.INCOMPLETA)
        self.assertTrue(informe.recorrido_completo)
        self.assertEqual(informe.evaluaciones_incompletas, 3)

    def test_no_duplica_parser_interpreta_una_vez_por_celda(self):
        from spica.perfilado.meteorologico import _interpretar
        with patch("spica.perfilado.interpretacion._interpretar", wraps=_interpretar) as interpretar:
            self.evaluar()
        self.assertEqual(interpretar.call_count, 3)

    def test_fachada_publica_reutiliza_fecha_hora_y_decimal(self):
        self.assertEqual(interpretar_numero("01.20").numero, Decimal("1.20"))
        self.assertEqual(interpretar_fecha_civil("20160229"), date(2016, 2, 29))
        self.assertIsNone(interpretar_fecha_civil("20150229"))
        self.assertEqual(clasificar_hora_literal("00000"), "cinco_digitos_compatibles_cero_inicial")
        with self.assertRaises(TypeError): interpretar_numero(1.2)

    def test_fechas_calendario_validas_e_invalidas(self):
        for fecha, estado in (("20160229", E.COMPROBACION_SATISFECHA),
                              ("20150229", E.PROBLEMA_TECNICO), ("2015-01-01", E.ALERTA_DOCUMENTAL)):
            with self.subTest(fecha=fecha):
                self.escribir(self.fila(FECHA=fecha))
                r, _ = self.evaluar()
                self.assertEqual(self.resultado(r, "L0-TMP-001").estado, estado)

    def test_sin_formato_documental_no_se_infiere_regla(self):
        r, _ = self.evaluar(configuracion=ConfiguracionQA())
        for regla in ("L0-TMP-001", "L0-TMP-002", "L0-ID-004", "L0-VAL-004"):
            self.assertEqual(self.resultado(r, regla).estado, E.NO_EVALUADO)

    def test_hora_cinco_seis_y_rangos_sin_reconstruccion(self):
        for hora, estado in (("00000", E.ALERTA_DOCUMENTAL), ("000000", E.COMPROBACION_SATISFECHA),
                             ("236000", E.ALERTA_DOCUMENTAL), ("240000", E.ALERTA_DOCUMENTAL)):
            with self.subTest(hora=hora):
                self.escribir(self.fila(HORA=hora))
                r, _ = self.evaluar()
                x = self.resultado(r, "L0-TMP-002")
                self.assertEqual(x.estado, estado)
                self.assertEqual(x.valores_originales, (("HORA", hora),))
                self.assertEqual(x.evidencia, (self.evidencia,))

    def test_zona_desconocida_no_asigna_instante(self):
        r, _ = self.evaluar()
        self.assertEqual(self.resultado(r, "L0-TMP-003").diagnostico, "zona_horaria_desconocida")
        self.assertEqual(self.resultado(r, "L0-TMP-004").estado, E.NO_EVALUADO)

    def test_zona_documentada_no_convierte_a_datetime(self):
        c = replace(self.configuracion, zona_documentada=DatoDocumentadoQA("zona-de-la-fixture", self.evidencia))
        r, _ = self.evaluar(configuracion=c)
        self.assertEqual(self.resultado(r, "L0-TMP-003").estado, E.COMPROBACION_SATISFECHA)
        self.assertEqual(self.resultado(r, "L0-TMP-004").diagnostico, "conversion_de_instantes_fuera_alcance")

    def test_ubigeo_decimal_no_se_reconstruye(self):
        r, _ = self.evaluar()
        x = self.resultado(r, "L0-ID-004")
        self.assertEqual((x.estado, x.valores_originales), (E.ALERTA_DOCUMENTAL, (("UBIGEO", "40514.0"),)))

    def test_ubigeo_seis_digitos_no_certifica_codigo_administrativo(self):
        self.escribir(self.fila(UBIGEO="040514"))
        r, _ = self.evaluar()
        self.assertEqual(self.resultado(r, "L0-ID-004").estado, E.COMPROBACION_SATISFECHA)

    def test_ubigeo_seis_caracteres_no_impone_digitos_no_documentados(self):
        self.escribir(self.fila(UBIGEO="AB1234"))
        r, _ = self.evaluar()
        x = self.resultado(r, "L0-ID-004")
        self.assertEqual(x.estado, E.COMPROBACION_SATISFECHA)
        self.assertEqual(x.valores_originales, (("UBIGEO", "AB1234"),))

    def test_nombre_literal_presente_o_vacio_sin_normalizar(self):
        self.escribir(self.fila(ESTACION="IMATA "), self.fila(ESTACION=" "))
        r, _ = self.evaluar()
        nombres = [x for x in r if x.regla.identificador == "L0-ID-001"]
        self.assertEqual(nombres[0].registro.estacion_literal, "IMATA ")
        self.assertEqual(nombres[1].estado, E.PROBLEMA_TECNICO)

    def test_id_registro_y_ubigeo_no_acreditan_identidad_fisica(self):
        r, _ = self.evaluar()
        x = self.resultado(r, "L0-ID-002")
        self.assertEqual(x.estado, E.NO_EVALUADO)
        self.assertEqual(x.registro.id_original, "0001")

    def test_identidad_requiere_nombre_literal_y_evidencia(self):
        c = replace(self.configuracion, identidades=(IdentidadEstacionQA("IMATA", "codigo-original", self.evidencia),))
        r, _ = self.evaluar(configuracion=c)
        self.assertEqual(self.resultado(r, "L0-ID-002").estado, E.COMPROBACION_SATISFECHA)
        self.escribir(self.fila(ESTACION="IMATA "))
        r, _ = self.evaluar(configuracion=c)
        self.assertEqual(self.resultado(r, "L0-ID-002").estado, E.NO_EVALUADO)

    def test_identidad_documental_contradictoria_no_se_resuelve(self):
        c = replace(self.configuracion, identidades=tuple(IdentidadEstacionQA("IMATA", codigo, self.evidencia)
                    for codigo in ("A", "B")))
        r, _ = self.evaluar(configuracion=c)
        self.assertEqual(self.resultado(r, "L0-ID-002").estado, E.ALERTA_DOCUMENTAL)

    def test_coordenadas_ausentes_y_metadatos_incompletos(self):
        self.escribir(self.fila(LONGITUD="", DISTRITO=""))
        r, _ = self.evaluar()
        self.assertEqual(self.resultado(r, "L0-ID-003").estado, E.PROBLEMA_TECNICO)
        self.assertEqual(self.resultado(r, "L0-ID-005").estado, E.PROBLEMA_TECNICO)

    def test_coordenadas_presentes_no_se_validan_geodesicamente(self):
        self.escribir(self.fila(LONGITUD="-071.09060", LATITUD="no-comprobada"))
        r, _ = self.evaluar()
        x = self.resultado(r, "L0-ID-003")
        self.assertEqual(x.estado, E.COMPROBACION_SATISFECHA)
        self.assertEqual(dict(x.valores_originales)["LONGITUD"], "-071.09060")

    def test_procedencia_incompleta_se_conserva_desconocida(self):
        r, informe = self.evaluar(procedencia=ProcedenciaQA())
        for x in r:
            if x.regla.categoria is C.PROCEDENCIA:
                self.assertEqual(x.estado, E.NO_EVALUADO)
        self.assertIsNone(informe.procedencia.adquisicion_id)
        self.assertEqual(informe.estado, EE.COMPLETA)  # Se ejecutaron las reglas de incertidumbre.

    def test_sha_y_asset_solo_referencias_no_confirmacion_raw(self):
        r, _ = self.evaluar()
        for regla in ("L0-PROV-004", "L0-PROV-005"):
            x = self.resultado(r, regla)
            self.assertEqual(x.estado, E.COMPROBACION_SATISFECHA)
            self.assertEqual(dict(x.parametros)["verificacion_fisica"], "no_realizada_por_esta_regla")

    def test_documento_disponible_y_licencia_desconocida(self):
        doc = EvidenciaDocumental(self.local.fuente, self.local.recurso_id)
        r, _ = self.evaluar(procedencia=replace(self.procedencia, documento=doc))
        self.assertEqual(self.resultado(r, "L0-PROV-006").estado, E.COMPROBACION_SATISFECHA)
        self.assertEqual(self.resultado(r, "L0-PROV-007").estado, E.NO_EVALUADO)
        self.assertIsNone(self.resultado(r, "L0-PROV-006").procedencia.documento.revision_documental)

    def test_licencia_referenciada_sin_afirmar_permisos(self):
        doc = EvidenciaDocumental(self.local.fuente, self.local.recurso_id, referencia_licencia="referencia-sintetica")
        r, _ = self.evaluar(procedencia=replace(self.procedencia, documento=doc))
        x = self.resultado(r, "L0-PROV-007")
        self.assertEqual(x.estado, E.COMPROBACION_SATISFECHA)
        self.assertIsNone(dict(x.valores_originales)["LICENCIA"])

    def test_documento_ajeno_no_valida_licencia(self):
        doc = EvidenciaDocumental(self.local.fuente, "otro-recurso", licencia_declarada="licencia-sintetica")
        r, _ = self.evaluar(procedencia=replace(self.procedencia, documento=doc))
        self.assertEqual(self.resultado(r, "L0-PROV-006").estado, E.PROBLEMA_TECNICO)
        self.assertEqual(self.resultado(r, "L0-PROV-007").estado, E.NO_EVALUADO)

    def test_consultas_locales_reutilizadas_y_procedencia_conservada(self):
        consulta = ConsultaLocal(("IMATA",), ("TEMP",), date(2015, 1, 1), date(2015, 1, 1))
        r, informe = self.evaluar(lector=ConsultorLocalCSV(self.ruta, consulta, self.local))
        self.assertEqual(self.resultado(r, "L0-PROV-008").estado, E.COMPROBACION_SATISFECHA)
        self.assertTrue(informe.recorrido_completo)
        self.assertEqual(r[0].registro.procedencia_original, self.local)

    def test_procedencia_contradictoria_no_se_oculta(self):
        consulta = ConsultaLocal(("IMATA",), ("TEMP",), date(2015, 1, 1), date(2015, 1, 1))
        r, _ = self.evaluar(lector=ConsultorLocalCSV(self.ruta, consulta, self.local),
                           procedencia=replace(self.procedencia, asset_id="otro-activo"))
        x = self.resultado(r, "L0-PROV-008")
        self.assertEqual(x.estado, E.PROBLEMA_TECNICO)
        self.assertEqual(x.registro.procedencia_original.asset_id, self.local.asset_id)

    def test_varias_alertas_por_mismo_registro(self):
        self.escribir(self.fila(TEMP="NaN", LONGITUD=""))
        r, _ = self.evaluar()
        alertas = [x for x in r if x.estado in (E.ALERTA_DOCUMENTAL, E.PROBLEMA_TECNICO)]
        self.assertGreaterEqual(len(alertas), 5)
        self.assertEqual({x.registro.numero_registro for x in alertas}, {2})

    def test_seleccion_por_categoria_y_reglas_es_estatica(self):
        c = replace(self.configuracion, categorias=(C.TEMPORALES,), reglas=("L0-TMP-002", "L0-TMP-001"))
        r, informe = self.evaluar(configuracion=c)
        self.assertEqual([x.regla.identificador for x in r], ["L0-TMP-001", "L0-TMP-002"])
        self.assertEqual(informe.resultados_emitidos, 2)

    def test_no_ejecuta_codigo_o_regex_configurados(self):
        with self.assertRaises(ValueError):
            self.evaluar(configuracion=replace(self.configuracion, reglas=("__import__('os').system('x')",)))
        with self.assertRaises(TypeError):
            FormatoDocumentadoQA("TEMP", "expresion-arbitraria", self.evidencia)

    def test_resultados_reproducibles_y_original_intacto(self):
        antes = self.ruta.read_bytes(), self.ruta.stat().st_mtime_ns
        a, ia = self.evaluar()
        b, ib = self.evaluar()
        self.assertEqual((a, ia), (b, ib))
        self.assertEqual(antes, (self.ruta.read_bytes(), self.ruta.stat().st_mtime_ns))

    def test_identificadores_repetidos_no_deduplican_filas(self):
        self.escribir(self.fila(), self.fila())
        r, informe = self.evaluar()
        self.assertEqual(informe.registros_examinados, 2)
        self.assertEqual({x.registro.numero_registro for x in r}, {2, 3})
        self.assertEqual({x.registro.id_original for x in r}, {"0001"})

    def test_limite_resultados_corta_una_fila_e_informa_parcial(self):
        r, informe = self.evaluar(limites=LimitesQA(max_resultados=4))
        self.assertEqual(len(r), 4)
        self.assertEqual((informe.estado, informe.registros_finalizados), (EE.INCOMPLETA, 0))
        self.assertEqual(informe.motivo_fin, "limite_resultados_qa")

    def test_limite_resultados_exacto_no_presume_eof(self):
        r, informe = self.evaluar(limites=LimitesQA(max_resultados=30))
        self.assertEqual(len(r), 30)
        self.assertEqual(informe.estado, EE.INCOMPLETA)

    def test_limite_registros_fuente_o_motor(self):
        self.escribir(self.fila(), self.fila())
        _, informe = self.evaluar(limites=LimitesQA(max_registros=1))
        self.assertEqual((informe.estado, informe.registros_examinados), (EE.INCOMPLETA, 1))
        _, informe = self.evaluar(lector=LectorCSV(self.ruta, politica=PoliticaLecturaCSV(max_registros=1)))
        self.assertEqual(informe.estado, EE.INCOMPLETA)

    def test_limite_texto_registro(self):
        _, informe = self.evaluar(limites=LimitesQA(max_caracteres_celda=5))
        self.assertEqual((informe.motivo_fin, informe.registros_examinados), ("limite_texto_registro_qa", 0))

    def test_cancelacion_previa(self):
        evento = Event()
        evento.set()
        r, informe = self.evaluar(cancelacion=evento)
        self.assertEqual(r, ())
        self.assertEqual(informe.motivo_fin, "cancelado")

    def test_cancelacion_entre_resultados(self):
        entrada = LectorCSV(self.ruta, delimitador=",")
        with EvaluadorNivel0(entrada, self.procedencia, configuracion=self.configuracion) as motor:
            next(motor)
            motor.cancelar()
            self.assertEqual(tuple(motor), ())
        self.assertEqual(motor.informe.estado, EE.INCOMPLETA)
        self.assertIsNone(entrada._archivo)

    def test_evento_externo_cancelacion_entre_resultados(self):
        evento = Event()
        with EvaluadorNivel0(LectorCSV(self.ruta, delimitador=","), self.procedencia,
                             cancelacion=evento) as motor:
            next(motor)
            evento.set()
            self.assertEqual(tuple(motor), ())
        self.assertEqual(motor.informe.motivo_fin, "cancelado")

    def test_break_cierra_y_no_declara_completa(self):
        entrada = LectorCSV(self.ruta, delimitador=",")
        with EvaluadorNivel0(entrada, self.procedencia) as motor:
            for _ in motor: break
        self.assertEqual(motor.informe.estado, EE.INCOMPLETA)
        self.assertIsNone(entrada._archivo)

    def test_interrupcion_consumidor_cierra_incluso_tras_eof(self):
        with self.assertRaises(KeyboardInterrupt):
            with EvaluadorNivel0(LectorCSV(self.ruta, delimitador=","), self.procedencia) as motor:
                tuple(motor)
                raise KeyboardInterrupt()
        self.assertEqual(motor.informe.estado, EE.INCOMPLETA)
        self.assertEqual(motor.informe.motivo_fin, "consumidor_interrumpido")

    def test_archivo_modificado_durante_consumo_no_declara_completo(self):
        with EvaluadorNivel0(LectorCSV(self.ruta, delimitador=","), self.procedencia) as motor:
            next(motor)
            with self.ruta.open("ab") as f: f.write(b"\n")
            tuple(motor)
        self.assertEqual(motor.informe.estado, EE.INCOMPLETA)

    def test_estructura_incompleta_conserva_valores_y_no_aplica_reglas_como_satisfechas(self):
        self.escribir(self.fila()[:7])
        r, informe = self.evaluar()
        self.assertTrue(all(x.estado is E.EVALUACION_INCOMPLETA for x in r))
        self.assertEqual(r[0].registro.valores_csv_originales, self.fila()[:7])
        self.assertEqual(informe.estado, EE.INCOMPLETA)

    def test_encabezado_incompatible_se_detiene(self):
        self.escribir(self.fila(), cabecera=tuple(reversed(CAB)))
        r, informe = self.evaluar()
        self.assertEqual(r, ())
        self.assertEqual(informe.motivo_fin, "encabezado_no_admitido")

    def test_consulta_limitada_no_se_presenta_completa(self):
        c = ConsultaLocal(("IMATA",), ("TEMP",), date(2015, 1, 1), date(2015, 1, 1))
        _, informe = self.evaluar(lector=ConsultorLocalCSV(self.ruta, c, self.local,
                                  limites=LimitesConsulta(max_resultados=1)))
        self.assertEqual(informe.estado, EE.INCOMPLETA)

    def test_consulta_multivariable_rechazada_antes_de_duplicar_filas(self):
        c = ConsultaLocal(("IMATA",), ("TEMP", "HR"), date(2015, 1, 1), date(2015, 1, 1))
        with self.assertRaises(ValueError):
            EvaluadorNivel0(ConsultorLocalCSV(self.ruta, c, self.local), self.procedencia)

    def test_entrada_sin_coincidencias_no_inventa_evaluaciones(self):
        self.escribir(cabecera=CAB)
        r, informe = self.evaluar()
        self.assertEqual(r, ())
        self.assertEqual(informe.estado, EE.NO_EVALUADA)
        self.assertTrue(informe.recorrido_completo)

    def test_validacion_contratos_y_limites(self):
        for valor in (0, -1, True, 5_000_001):
            with self.subTest(valor=valor), self.assertRaises(ValueError): LimitesQA(max_resultados=valor)
        with self.assertRaises(ValueError): ProcedenciaQA(sha256_referencia="incorrecto")
        with self.assertRaises(ValueError): ReferenciaDocumentalQA("ref", "desc", revision=0)
        with self.assertRaises(ValueError): ConfiguracionQA(variables=("O3",))
        with self.assertRaises(ValueError): ConfiguracionQA(formatos=self.configuracion.formatos * 2)
        with self.assertRaises(TypeError): EvaluadorNivel0(iter(()), self.procedencia)

    def test_uso_de_contexto_y_reutilizacion(self):
        motor = EvaluadorNivel0(LectorCSV(self.ruta, delimitador=","), self.procedencia)
        with self.assertRaises(RuntimeError): next(motor)
        with motor: tuple(motor)
        with self.assertRaises(RuntimeError): motor.__enter__()

    def test_funcion_pura_y_campos_ausentes(self):
        r = adaptar_registro(RegistroCSV(2, 2, 2, self.fila(), True))
        r = replace(r, campos_originales=tuple((k,v) for k,v in r.campos_originales if k != "TEMP"))
        resultados = tuple(evaluar_registro(r, self.procedencia, configuracion=self.configuracion))
        self.assertEqual(self.resultado(resultados, "L0-VAL-001", "TEMP").estado, E.EVALUACION_INCOMPLETA)

    def test_memoria_acotada_consumiendo_resultados_sin_acumular(self):
        picos = []
        c = replace(self.configuracion, categorias=(C.VALORES,), reglas=("L0-VAL-002",))
        for cantidad in (300, 10000):
            with self.ruta.open("w", newline="", encoding="ascii") as f:
                w = csv.writer(f)
                w.writerow(CAB)
                for _ in range(cantidad): w.writerow(self.fila())
            tracemalloc.start()
            try:
                with EvaluadorNivel0(LectorCSV(self.ruta, delimitador=","), self.procedencia,
                                     configuracion=c, limites=LimitesQA(max_registros=15000)) as motor:
                    self.assertEqual(sum(1 for _ in motor), cantidad * 3)
                picos.append(tracemalloc.get_traced_memory()[1])
            finally:
                tracemalloc.stop()
            self.assertEqual(motor.informe.estado, EE.COMPLETA)
        self.assertLess(max(picos), 5 * 1024**2)
        self.assertLess(picos[1], picos[0] + 1024**2)


if __name__ == "__main__":
    unittest.main()
