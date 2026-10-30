"""Contratos Nivel 1 con documentación ficticia; ninguna regla científica real."""

from collections import Counter
import csv
from dataclasses import FrozenInstanceError, replace
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from spica.adquisicion.consultas_locales import ENCABEZADO_SENAMHI
from spica.adquisicion.verificacion import LectorCSV
from spica.calidad import EvaluadorNivel0, ProcedenciaQA, REGLAS_NIVEL0, EstadoEvaluacionQA
from spica.calidad.catalogo_cientifico import CatalogoReglasCientificas
from spica.calidad.modelos_cientificos import (
    AmbitoReglaCientifica as A, CondicionAplicabilidad, ContextoCientifico,
    DatoContextoCientifico, DimensionAplicabilidad as D, EstadoReglaCientifica as E,
    EstadoResultadoCientifico as R, EvidenciaEjecucionCientifica, IncertidumbreCientifica,
    MetodoCientifico, ParametroCientifico, ReferenciaCientifica, ReglaCientifica,
    ResultadoCientifico, RevisionCientifica,
    RevisionReglaCientifica,
)


class CatalogoCientificoTests(unittest.TestCase):
    def setUp(self):
        self.ref = ReferenciaCientifica("manual-prueba", "institucion-ficticia", "Manual sintético",
            "urn:spica:fixture:manual", "edicion-prueba", date(2020, 1, 1))
        self.decision = RevisionCientifica("rol-revisor-prueba", datetime(2021, 1, 1, tzinfo=timezone.utc),
            "urn:spica:fixture:revision", (self.ref.identificador,), True)
        self.catalogo = CatalogoReglasCientificas()

    def regla(self, **cambios):
        valores = dict(identificador="L1-PRUEBA", version="1.0.0", nombre="Regla ficticia sin algoritmo",
            ambito=A.INSTITUCIONAL, procedencia_normativa="institucion-ficticia", referencias=(self.ref,),
            aplicabilidad=tuple(CondicionAplicabilidad(d, ("dato-" + d.value,), (self.ref.identificador,)) for d in D),
            parametros=(ParametroCientifico("modalidad", "sin-algoritmo", referencias=(self.ref.identificador,)),),
            metodo=MetodoCientifico("metodo_ficticio", "1.0.0", "Descriptor no ejecutable", (self.ref.identificador,)),
            incertidumbre=IncertidumbreCientifica("Incertidumbre solo para fixture", (self.ref.identificador,)))
        valores.update(cambios)
        return ReglaCientifica(**valores)

    def contexto(self, **cambios):
        return ContextoCientifico(tuple(DatoContextoCientifico(d, cambios.get(d.value, "dato-" + d.value), self.ref) for d in D))

    def cambiar(self, estado, *, decision=None, identificador="L1-PRUEBA", version="1.0.0"):
        actual = self.catalogo.obtener(identificador, version)
        return self.catalogo.cambiar_estado(identificador, version, estado,
            revision_esperada=actual.revision, decision=decision or self.decision)

    def aprobar(self, regla=None):
        self.catalogo.registrar(regla or self.regla())
        self.cambiar(E.DOCUMENTADA)
        return self.cambiar(E.APROBADA)

    def test_catalogo_inicial_vacio_y_sin_carga_institucional(self):
        self.assertEqual(self.catalogo.listar(), ())

    def test_registro_siempre_propuesto_sin_ejecucion(self):
        r = self.catalogo.registrar(self.regla())
        h = self.catalogo.comprobar_habilitacion(r.regla.identificador, r.regla.version, self.contexto())
        self.assertEqual((r.estado, r.revision), (E.PROPUESTA, 1))
        self.assertFalse(h.elegible_documentalmente)
        self.assertFalse(h.ejecucion_autorizada)
        self.assertEqual(h.estado_evaluacion, EstadoEvaluacionQA.NO_EVALUADA)

    def test_id_y_version_no_se_sobrescriben(self):
        r = self.regla()
        self.catalogo.registrar(r)
        for otra in (r, replace(r, incertidumbre=None)):
            with self.subTest(otra=otra), self.assertRaises(ValueError): self.catalogo.registrar(otra)
        self.assertEqual(len(self.catalogo.historial(r.identificador, r.version)), 1)

    def test_espacio_de_ids_no_colisiona_con_nivel0(self):
        for identificador in ("L0-VAL-001", "", "L1-", "L1-../ruta"):
            with self.subTest(identificador=identificador), self.assertRaises(ValueError): self.regla(identificador=identificador)

    def test_versiones_explicitas_sin_normalizacion_ambigua(self):
        for version in ("1", "1.0", "01.0.0", "1.0.0-beta", "1.0.0 ", True):
            with self.subTest(version=version), self.assertRaises(ValueError): self.regla(version=version)

    def test_nueva_version_no_hereda_aprobacion(self):
        previa = self.aprobar()
        nueva = self.catalogo.registrar(replace(previa.regla, version="1.1.0", incertidumbre=None))
        self.assertEqual(nueva.estado, E.PROPUESTA)
        self.assertEqual(self.catalogo.obtener("L1-PRUEBA", "1.0.0"), previa)
        self.assertFalse(self.catalogo.comprobar_habilitacion("L1-PRUEBA", "1.1.0", self.contexto()).ejecucion_autorizada)

    def test_versiones_retroactivas_e_identidad_cambiada_rechazadas(self):
        self.catalogo.registrar(self.regla(version="2.0.0"))
        for r in (self.regla(version="1.9.9"), self.regla(version="3.0.0", nombre="Otra identidad"),
                  self.regla(version="3.0.0", ambito=A.UNIVERSAL)):
            with self.subTest(r=r), self.assertRaises(ValueError): self.catalogo.registrar(r)

    def test_listado_determinista_y_orden_numerico_versiones(self):
        for version in ("1.0.0", "2.0.0", "10.0.0"):
            self.catalogo.registrar(self.regla(version=version))
        self.assertEqual([r.regla.version for r in self.catalogo.listar()], ["1.0.0", "2.0.0", "10.0.0"])
        self.assertEqual(self.catalogo.listar(), self.catalogo.listar())

    def test_historial_inmutable_y_revision_incremental(self):
        inicial = self.catalogo.registrar(self.regla())
        foto = self.catalogo.historial("L1-PRUEBA", "1.0.0")
        self.cambiar(E.DOCUMENTADA); self.cambiar(E.APROBADA)
        self.assertEqual(foto, (inicial,))
        self.assertEqual([r.revision for r in self.catalogo.historial("L1-PRUEBA", "1.0.0")], [1, 2, 3])
        with self.assertRaises(FrozenInstanceError): inicial.regla.nombre = "Cambio"

    def test_revision_desactualizada_no_cambia_historial(self):
        self.catalogo.registrar(self.regla()); self.cambiar(E.DOCUMENTADA)
        for revision in (1, True):
            with self.subTest(revision=revision), self.assertRaises(ValueError):
                self.catalogo.cambiar_estado("L1-PRUEBA", "1.0.0", E.APROBADA,
                    revision_esperada=revision, decision=self.decision)
        self.assertEqual(self.catalogo.obtener("L1-PRUEBA", "1.0.0").revision, 2)

    def test_propuesta_no_puede_aprobarse_directamente(self):
        self.catalogo.registrar(self.regla())
        with self.assertRaises(ValueError): self.cambiar(E.APROBADA)

    def test_referencias_obligatorias_para_documentar(self):
        self.catalogo.registrar(self.regla(referencias=(), aplicabilidad=(), parametros=(), metodo=None, incertidumbre=None))
        with self.assertRaises(ValueError): self.cambiar(E.DOCUMENTADA)

    def test_version_y_fecha_documental_desconocidas_no_se_inventan(self):
        for campo in ("version_documento", "fecha_documento"):
            with self.subTest(campo=campo):
                self.catalogo = CatalogoReglasCientificas()
                ref = replace(self.ref, **{campo: None})
                self.catalogo.registrar(self.regla(referencias=(ref,)))
                with self.assertRaises(ValueError): self.cambiar(E.DOCUMENTADA)
                self.assertIsNone(getattr(self.catalogo.obtener("L1-PRUEBA", "1.0.0").regla.referencias[0], campo))

    def test_todas_las_referencias_deben_revisarse(self):
        self.catalogo.registrar(self.regla())
        for referencias in ((), ("manual-ajeno",)):
            with self.subTest(referencias=referencias), self.assertRaises(ValueError):
                self.cambiar(E.DOCUMENTADA, decision=replace(self.decision, referencias_revisadas=referencias))

    def test_aprobacion_sin_aplicabilidad_demostrada_rechazada(self):
        self.catalogo.registrar(self.regla()); self.cambiar(E.DOCUMENTADA)
        with self.assertRaisesRegex(ValueError, "aplicabilidad_no_demostrada"):
            self.cambiar(E.APROBADA, decision=replace(self.decision, aplicabilidad_demostrada=False))

    def test_aplicabilidad_incompleta_no_es_universal_por_defecto(self):
        self.catalogo.registrar(self.regla(ambito=A.UNIVERSAL, aplicabilidad=()))
        self.cambiar(E.DOCUMENTADA)
        with self.assertRaisesRegex(ValueError, "dimensiones"): self.cambiar(E.APROBADA)

    def test_aplicabilidad_sin_documentacion_no_se_aprueba(self):
        r = self.regla()
        self.catalogo.registrar(replace(r, aplicabilidad=(replace(r.aplicabilidad[0], referencias=()), *r.aplicabilidad[1:])))
        self.cambiar(E.DOCUMENTADA)
        with self.assertRaisesRegex(ValueError, "aplicabilidad_sin_referencia"): self.cambiar(E.APROBADA)

    def test_ambitos_institucional_producto_instrumento_exigen_restriccion(self):
        for ambito, dimension in ((A.INSTITUCIONAL, D.INSTITUCION), (A.PRODUCTO, D.PRODUCTO), (A.INSTRUMENTO, D.INSTRUMENTO)):
            with self.subTest(ambito=ambito):
                self.catalogo = CatalogoReglasCientificas()
                r = self.regla(ambito=ambito)
                condiciones = tuple(CondicionAplicabilidad(dimension, referencias=(self.ref.identificador,), sin_restriccion=True)
                                    if c.dimension is dimension else c for c in r.aplicabilidad)
                self.catalogo.registrar(replace(r, aplicabilidad=condiciones)); self.cambiar(E.DOCUMENTADA)
                with self.assertRaisesRegex(ValueError, "ambito_sin_restriccion"): self.cambiar(E.APROBADA)

    def test_sin_restriccion_requiere_declaracion_y_evidencia(self):
        r = self.regla()
        condiciones = tuple(replace(c, valores_permitidos=(), sin_restriccion=True)
                            if c.dimension is D.GEOGRAFIA else c for c in r.aplicabilidad)
        self.aprobar(replace(r, aplicabilidad=condiciones))
        contexto = replace(self.contexto(), datos=tuple(d for d in self.contexto().datos if d.dimension is not D.GEOGRAFIA))
        self.assertTrue(self.catalogo.comprobar_habilitacion("L1-PRUEBA", "1.0.0", contexto).elegible_documentalmente)

    def test_metodo_incertidumbre_parametros_y_procedencia_requeridos(self):
        for cambios in ({"metodo": None}, {"incertidumbre": None}, {"procedencia_normativa": None},
                        {"parametros": (ParametroCientifico("dato", "literal"),)}):
            with self.subTest(cambios=cambios):
                self.catalogo = CatalogoReglasCientificas()
                self.catalogo.registrar(self.regla(**cambios)); self.cambiar(E.DOCUMENTADA)
                with self.assertRaises(ValueError): self.cambiar(E.APROBADA)

    def test_contradicciones_declaradas_impiden_aprobacion(self):
        self.catalogo.registrar(self.regla()); self.cambiar(E.DOCUMENTADA)
        with self.assertRaisesRegex(ValueError, "contradicciones"):
            self.cambiar(E.APROBADA, decision=replace(self.decision, contradicciones=("manuales no conciliados",)))

    def test_contradicciones_en_descriptor_impiden_documentar(self):
        self.catalogo.registrar(self.regla(contradicciones_documentales=("aplicabilidad discrepante",)))
        with self.assertRaisesRegex(ValueError, "contradicciones"): self.cambiar(E.DOCUMENTADA)

    def test_versiones_documentales_contradictorias_en_mismo_localizador(self):
        otra = replace(self.ref, identificador="manual-otro", version_documento="otra-edicion")
        self.catalogo.registrar(self.regla(referencias=(self.ref, otra)))
        with self.assertRaisesRegex(ValueError, "contradictorias"):
            self.cambiar(E.DOCUMENTADA, decision=replace(self.decision, referencias_revisadas=(self.ref.identificador, otra.identificador)))

    def test_referencias_dimensiones_y_parametros_duplicados_rechazados(self):
        r = self.regla()
        for cambios in ({"referencias": (self.ref, self.ref)}, {"aplicabilidad": (r.aplicabilidad[0],)*2},
                        {"parametros": r.parametros*2}):
            with self.subTest(cambios=cambios), self.assertRaises(ValueError): self.regla(**cambios)

    def test_referencia_ajena_en_metodo_rechazada(self):
        with self.assertRaises(ValueError): self.regla(metodo=MetodoCientifico("metodo", "1.0.0", "Ficticio", ("no-registrada",)))

    def test_unidad_incompatible_no_se_convierte(self):
        self.aprobar()
        contexto = self.contexto(unidad="unidad-diferente")
        h = self.catalogo.comprobar_habilitacion("L1-PRUEBA", "1.0.0", contexto)
        self.assertIn("contexto_incompatible:unidad", h.motivos)
        self.assertFalse(h.elegible_documentalmente)
        self.assertEqual(next(d.valor for d in contexto.datos if d.dimension is D.UNIDAD), "unidad-diferente")

    def test_variable_frecuencia_instrumento_geografia_y_ambiente_incompatibles(self):
        self.aprobar()
        for dimension in D:
            with self.subTest(dimension=dimension):
                h = self.catalogo.comprobar_habilitacion("L1-PRUEBA", "1.0.0", self.contexto(**{dimension.value: "otro"}))
                self.assertIn("contexto_incompatible:"+dimension.value, h.motivos)

    def test_contexto_sin_evidencia_suficiente_no_es_aplicable(self):
        self.aprobar()
        self.assertFalse(self.catalogo.comprobar_habilitacion("L1-PRUEBA", "1.0.0", ContextoCientifico()).elegible_documentalmente)
        c = self.contexto()
        dato = replace(c.datos[0], evidencia=replace(self.ref,
            identificador="contexto-fecha-desconocida", fecha_documento=None))
        h = self.catalogo.comprobar_habilitacion("L1-PRUEBA", "1.0.0", ContextoCientifico((dato,*c.datos[1:])))
        self.assertIn("contexto_no_demostrado:disciplina", h.motivos)

    def test_aprobada_y_aplicable_aun_no_autoriza_ejecucion(self):
        self.aprobar()
        h = self.catalogo.comprobar_habilitacion("L1-PRUEBA", "1.0.0", self.contexto())
        self.assertTrue(h.elegible_documentalmente)
        self.assertFalse(h.ejecucion_autorizada)
        self.assertEqual(h.motivos, ("ejecucion_nivel1_no_implementada",))
        with self.assertRaises(FrozenInstanceError): h.ejecucion_autorizada = True

    def test_suspendida_y_obsoleta_no_son_elegibles(self):
        self.aprobar(); self.cambiar(E.SUSPENDIDA)
        self.assertFalse(self.catalogo.comprobar_habilitacion("L1-PRUEBA", "1.0.0", self.contexto()).elegible_documentalmente)
        self.cambiar(E.OBSOLETA)
        self.assertFalse(self.catalogo.comprobar_habilitacion("L1-PRUEBA", "1.0.0", self.contexto()).elegible_documentalmente)
        with self.assertRaises(ValueError): self.cambiar(E.DOCUMENTADA)

    def test_reactivar_suspendida_exige_nueva_revision_y_aprobacion(self):
        self.aprobar(); self.cambiar(E.SUSPENDIDA)
        with self.assertRaises(ValueError): self.cambiar(E.APROBADA)
        self.cambiar(E.DOCUMENTADA); self.cambiar(E.APROBADA)
        self.assertEqual(self.catalogo.obtener("L1-PRUEBA", "1.0.0").revision, 6)

    def test_no_retrocede_fecha_de_revision(self):
        self.catalogo.registrar(self.regla()); self.cambiar(E.DOCUMENTADA)
        with self.assertRaises(ValueError):
            self.cambiar(E.APROBADA, decision=replace(self.decision, fecha_utc=self.decision.fecha_utc-timedelta(days=1)))

    def test_determinismo_con_las_mismas_decisiones(self):
        self.aprobar()
        a = self.catalogo.listar(), self.catalogo.comprobar_habilitacion("L1-PRUEBA", "1.0.0", self.contexto())
        self.catalogo = CatalogoReglasCientificas(); self.aprobar()
        b = self.catalogo.listar(), self.catalogo.comprobar_habilitacion("L1-PRUEBA", "1.0.0", self.contexto())
        self.assertEqual(a, b)

    def test_disciplinas_y_variables_no_limitadas_a_meteorologia(self):
        for disciplina in ("meteorologia", "hidrologia", "hidrogeoquimica", "geologia", "suelos"):
            with self.subTest(disciplina=disciplina):
                self.catalogo = CatalogoReglasCientificas()
                r = self.regla(ambito=A.UNIVERSAL)
                condiciones = tuple(replace(c, valores_permitidos=(disciplina,)) if c.dimension is D.DISCIPLINA else c for c in r.aplicabilidad)
                self.aprobar(replace(r, aplicabilidad=condiciones))
                self.assertTrue(self.catalogo.comprobar_habilitacion("L1-PRUEBA", "1.0.0", self.contexto(disciplina=disciplina)).elegible_documentalmente)

    def test_sin_codigo_dinamico_en_metodo_o_parametro(self):
        for metodo in ("paquete.funcion", "__import__('os')", lambda: None):
            with self.subTest(metodo=metodo), self.assertRaises(ValueError): MetodoCientifico(metodo, "1.0.0", "No admitido")
        with self.assertRaises(TypeError): ParametroCientifico("callback", lambda: None)
        # Un literal opaco es dato, nunca se interpreta o ejecuta.
        literal = "__import__('os').system('no-ejecutar')"
        self.assertEqual(ParametroCientifico("texto", literal).valor, literal)

    def test_parametros_exactos_y_acotados(self):
        self.assertEqual(ParametroCientifico("numero", Decimal("01.20")).valor, Decimal("1.20"))
        for valor in (1.2, [], {}, Decimal("NaN"), Decimal("Infinity"), 2**300):
            with self.subTest(valor=valor), self.assertRaises((TypeError, ValueError)): ParametroCientifico("dato", valor)

    def test_fecha_utc_y_desconocidos_sin_reconstruccion(self):
        with self.assertRaises(ValueError): replace(self.decision, fecha_utc=datetime(2021,1,1))
        with self.assertRaises(TypeError): replace(self.ref, fecha_documento=datetime(2020,1,1))
        with self.assertRaises(ValueError): ContextoCientifico((self.contexto().datos[0],)*2)
        with self.assertRaises(ValueError): CondicionAplicabilidad(D.UNIDAD)

    def test_resultado_no_evaluado_conserva_registro_y_procedencia_nivel0(self):
        from spica.calidad import RegistroQA
        registro = RegistroQA(2, "0001", "IMATA", 2, 2, (("HORA", "00000"),("UBIGEO", "40514.0")), True)
        regla = self.catalogo.registrar(self.regla())
        r = ResultadoCientifico(regla, registro, ProcedenciaQA(), None, R.NO_EVALUADO, "Sin autorización de ejecución")
        self.assertIs(r.registro, registro)
        self.assertEqual(r.registro.campos_originales, (("HORA", "00000"),("UBIGEO", "40514.0")))
        self.assertEqual(r.estado_evaluacion, EstadoEvaluacionQA.NO_EVALUADA)
        for estado in (R.ALERTA, R.SOSPECHA, R.PROBLEMA_DEMOSTRADO):
            with self.subTest(estado=estado), self.assertRaises(ValueError): replace(r, estado=estado)

    def test_resultado_ejecutado_requiere_evidencia_del_metodo_exacto(self):
        from spica.calidad import RegistroQA
        regla = self.aprobar()
        registro = RegistroQA(2, "1", "nombre", 2, 2, (("variable-original", "-9999"),), True)
        r = ResultadoCientifico(regla, registro, ProcedenciaQA(), "unidad-original", R.NO_EVALUADO, "Sin ejecución")
        with self.assertRaises(ValueError): replace(r, estado=R.PROBLEMA_DEMOSTRADO)
        evidencia = EvidenciaEjecucionCientifica(replace(regla.regla.metodo, version="2.0.0"),
            self.decision.fecha_utc, "1.0.0", (self.ref,), "Ejecución externa ficticia")
        with self.assertRaises(ValueError): replace(r, evidencia=evidencia)

    def test_documentacion_futura_no_se_declara_revisada(self):
        self.catalogo.registrar(self.regla(referencias=(replace(self.ref, fecha_documento=date(2022, 1, 1)),)))
        with self.assertRaisesRegex(ValueError, "posterior_a_revision"): self.cambiar(E.DOCUMENTADA)

    def test_contexto_no_admite_referencias_contradictorias(self):
        c = self.contexto()
        dato = replace(c.datos[0], evidencia=replace(self.ref, version_documento="contradictoria"))
        with self.assertRaises(ValueError): ContextoCientifico((dato,*c.datos[1:]))

    def test_revision_requiere_estado_decision_y_secuencia_coherentes(self):
        r = self.regla()
        for revision, estado, decision in ((True, E.PROPUESTA, None), (2, E.PROPUESTA, None),
                (1, E.APROBADA, self.decision), (2, E.APROBADA, None)):
            with self.subTest(revision=revision, estado=estado), self.assertRaises(ValueError):
                RevisionReglaCientifica(r, revision, estado, decision)

    def test_contrato_distinge_hallazgos_solo_como_metadatos_sinteticos(self):
        from spica.calidad import RegistroQA
        regla = self.aprobar()
        registro = RegistroQA(2, "original", "nombre-literal", 2, 2, (("valor", "-9999"),), True)
        evidencia = EvidenciaEjecucionCientifica(regla.regla.metodo, self.decision.fecha_utc,
            "1.0.0", (self.ref,), "Evidencia completamente ficticia; no se ejecutó algoritmo", self.contexto())
        for estado in R:
            with self.subTest(estado=estado):
                resultado = ResultadoCientifico(regla, registro, ProcedenciaQA(), "unidad-original",
                    estado, "Solo se prueba representación, no calidad científica", evidencia)
                self.assertIs(resultado.estado, estado)
                self.assertIs(resultado.registro, registro)
        self.assertEqual(len({r.value for r in R}), 6)

    def test_no_admite_ejecucion_declarada_anterior_a_aprobacion(self):
        from spica.calidad import RegistroQA
        regla = self.aprobar()
        registro = RegistroQA(2, "id", "nombre", 2, 2, (), True)
        evidencia = EvidenciaEjecucionCientifica(regla.regla.metodo,
            self.decision.fecha_utc-timedelta(days=1), "1.0.0", (self.ref,), "Ficticia")
        with self.assertRaisesRegex(ValueError, "precede"):
            ResultadoCientifico(regla, registro, ProcedenciaQA(), None, R.SOSPECHA, "No admisible", evidencia)


class CardinalidadNivel0Tests(unittest.TestCase):
    def setUp(self):
        padre = Path(tempfile.gettempdir()).resolve()
        self.base = padre / ("spica-paso73-test-"+uuid4().hex)
        self.base.mkdir(mode=0o755)
        assert self.base.resolve().is_relative_to(padre)
        self.addCleanup(shutil.rmtree, self.base)
        self.ruta = self.base / "sintetico.csv"
        self.fila = ("0001", "IMATA", "20150101", "00000", "-71.0906", "-15.8427", "4475.0",
                     "-9999", "", "NaN", "RBON", "AREQUIPA", "CAYLLOMA", "DISTRITO", "40514.0", "20240630")

    def escribir(self, cantidad):
        with self.ruta.open("w", encoding="ascii", newline="") as f:
            w = csv.writer(f); w.writerow(ENCABEZADO_SENAMHI)
            for _ in range(cantidad): w.writerow(self.fila)

    def test_744_filas_22_reglas_22320_resultados_sin_claves_duplicadas(self):
        self.escribir(744)
        vistos = set(); reglas = Counter(); campos = Counter()
        with EvaluadorNivel0(LectorCSV(self.ruta, delimitador=","), ProcedenciaQA()) as motor:
            for r in motor:
                objetivos = tuple(c for c,_ in r.valores_originales)
                clave = (r.registro.numero_registro, r.regla.identificador, objetivos)
                self.assertNotIn(clave, vistos)
                vistos.add(clave); reglas[r.regla.identificador] += 1
                if r.regla.identificador.startswith("L0-VAL-"):
                    campos[r.regla.identificador, objetivos] += 1
        self.assertEqual((len(vistos), motor.informe.resultados_emitidos), (22320, 22320))
        self.assertEqual((motor.informe.registros_finalizados, motor.informe.estado), (744, EstadoEvaluacionQA.COMPLETA))
        for r in REGLAS_NIVEL0:
            self.assertEqual(reglas[r.identificador], 2232 if r.identificador.startswith("L0-VAL-") else 744)
        self.assertEqual(len(campos), 12)
        self.assertTrue(all(n == 744 for n in campos.values()))

    def test_catalogo_no_modifica_resultados_previos_ni_original(self):
        self.escribir(1)
        original = self.ruta.read_bytes(), self.ruta.stat().st_mtime_ns
        def evaluar():
            with EvaluadorNivel0(LectorCSV(self.ruta, delimitador=","), ProcedenciaQA()) as motor:
                resultados = tuple(motor)
            return resultados, motor.informe
        antes = evaluar()
        catalogo = CatalogoReglasCientificas()
        regla = catalogo.registrar(ReglaCientifica("L1-SINTETICA", "1.0.0", "Propuesta sin ejecutar", A.UNIVERSAL))
        self.assertFalse(catalogo.comprobar_habilitacion(regla.regla.identificador, regla.regla.version, ContextoCientifico()).ejecucion_autorizada)
        self.assertEqual(antes, evaluar())
        self.assertEqual(original, (self.ruta.read_bytes(), self.ruta.stat().st_mtime_ns))
        self.assertEqual(len(antes[0]), 30)


if __name__ == "__main__":
    unittest.main()
