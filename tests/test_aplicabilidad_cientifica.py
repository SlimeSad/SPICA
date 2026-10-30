"""Fixtures documentales inventadas; sin observaciones, red, RAW o SQLite operativo."""

from dataclasses import FrozenInstanceError, replace
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from spica.adquisicion.catalogo import ProcedenciaCatalogo, ProductoCatalogo
from spica.adquisicion.nucleo import Fuente
from spica.adquisicion.verificacion import RegistroCSV
from spica.calidad import ProcedenciaQA, adaptar_registro, evaluar_registro
from spica.calidad.aplicabilidad import (
    AfirmacionAplicabilidad as Afirmacion, AspectoAdicional as A, CondicionAdicional,
    EspecificacionAplicabilidad, EstadoAplicabilidad as E, EstadoRequisito as R,
    EvidenciaDocumental, ExpedienteProducto, NaturalezaEvidencia as Origen,
    NivelEvidencia as N, RequisitoAplicabilidad as Requisito, TipoRequisito as T,
    VigenciaDocumento as V, verificar_aplicabilidad,
)
from spica.calidad.catalogo_cientifico import CatalogoReglasCientificas
from spica.calidad.experimental import (
    EvidenciaSintetica, ObservacionSintetica, ReglaLimitesSintetica, evaluar_limites_sinteticos,
)
from spica.calidad.modelos_cientificos import (
    AmbitoReglaCientifica, CondicionAplicabilidad, ContextoCientifico,
    DimensionAplicabilidad as D, EstadoReglaCientifica, HabilitacionCientifica,
    ParametroCientifico, ReferenciaCientifica, ReglaCientifica, RevisionReglaCientifica,
)


class AplicabilidadCientificaTests(unittest.TestCase):
    def setUp(self):
        # "Verificada" y "vigente" solo describen el mundo inventado de esta fixture.
        self.ref_regla = ReferenciaCientifica("doc-regla-fixture", "emisor-ficticio", "Manual inventado",
            "urn:fixture:manual", "edicion-ficticia", date(2000, 1, 1))
        self.ref_producto = replace(self.ref_regla, identificador="doc-producto-fixture",
            titulo="Ficha inventada", localizador="urn:fixture:producto")
        self.doc_regla = EvidenciaDocumental(self.ref_regla, "seccion-ficticia", Origen.SINTETICA,
                                             N.VERIFICADA, V.VIGENTE)
        self.doc_producto = replace(self.doc_regla, referencia=self.ref_producto, localizacion="tabla-ficticia")
        self.valores = {D.PRODUCTO: " producto-fixture ", D.INSTITUCION: "institucion-ficticia",
            D.VARIABLE: "variable-ficticia", D.UNIDAD: "unidad-ficticia",
            D.TIPO_MEDICION: "modalidad-ficticia", D.FRECUENCIA: "frecuencia-ficticia"}
        condiciones = tuple(CondicionAplicabilidad(d, (v,), (self.ref_regla.identificador,))
                            for d, v in self.valores.items())
        self.regla = ReglaCientifica("L1-FIXTURE-DOCUMENTAL", "1.0.0", "Descriptor inventado sin algoritmo",
            AmbitoReglaCientifica.PRODUCTO, "institucion-ficticia", (self.ref_regla,), condiciones)
        self.plan = EspecificacionAplicabilidad(self.regla,
            tuple(Requisito(c.dimension.value, c) for c in condiciones), (self.doc_regla,))
        procedencia = ProcedenciaCatalogo("urn:fixture:producto", datetime(2001, 1, 1, tzinfo=timezone.utc),
                                         "fixture_sintetica", "No es evidencia institucional")
        producto = ProductoCatalogo(Fuente("institucion-ficticia", "fuente-ficticia"),
            self.valores[D.PRODUCTO], procedencia, version="version-ficticia")
        self.expediente = ExpedienteProducto(producto, (self.doc_producto,),
            tuple(Afirmacion(d, v, N.VERIFICADA, (self.ref_producto.identificador,))
                  for d, v in self.valores.items()))

    def evaluar(self, *, plan=None, expediente=None):
        return verificar_aplicabilidad(plan or self.plan, expediente or self.expediente)

    def con_dato(self, dimension, **cambios):
        datos = list(self.expediente.afirmaciones)
        indice = next((i for i, a in enumerate(datos) if a.dimension is dimension), None)
        base = datos[indice] if indice is not None else Afirmacion(dimension, None, N.DESCONOCIDA)
        nuevo = replace(base, **cambios)
        if indice is None:
            datos.append(nuevo)
        else:
            datos[indice] = nuevo
        return replace(self.expediente, afirmaciones=tuple(datos))

    def exigir(self, dimension, valor="valor-ficticio", **opciones):
        tipo = CondicionAdicional if type(dimension) is A else CondicionAplicabilidad
        condicion = tipo(dimension, (valor,), (self.ref_regla.identificador,))
        req = Requisito(dimension.value, condicion, **opciones)
        return replace(self.plan, requisitos=(*self.plan.requisitos, req))

    def test_producto_y_regla_compatibles_sin_permiso(self):
        r = self.evaluar()
        self.assertEqual(r.estado, E.COMPATIBILIDAD_DOCUMENTAL_DEMOSTRADA)
        self.assertFalse(r.ejecucion_autorizada)
        self.assertTrue(r.restricciones)
        self.assertTrue(r.motivos)
        self.assertEqual(r.naturaleza_evidencia, Origen.SINTETICA)
        self.assertTrue(all(h.referencias for h in r.hallazgos))
        self.assertNotIsInstance(r, HabilitacionCientifica)

    def test_variable_incompatible(self):
        r = self.evaluar(expediente=self.con_dato(D.VARIABLE, valor="otra-variable"))
        self.assertEqual(r.estado, E.INCOMPATIBILIDAD_DOCUMENTADA)

    def test_unidad_incompatible_sin_conversion(self):
        for valor in ("otra-unidad", " UNIDAD-FICTICIA ", "unidad-ficticia "):
            with self.subTest(valor=valor):
                self.assertEqual(self.evaluar(expediente=self.con_dato(D.UNIDAD, valor=valor)).estado,
                                 E.INCOMPATIBILIDAD_DOCUMENTADA)

    def test_unidad_desconocida(self):
        self.assertEqual(self.evaluar(expediente=self.con_dato(D.UNIDAD, valor=None, nivel=N.DESCONOCIDA)).estado,
                         E.INFORMACION_INSUFICIENTE)

    def test_modalidad_distinta(self):
        self.assertEqual(self.evaluar(expediente=self.con_dato(D.TIPO_MEDICION, valor="otra-modalidad")).estado,
                         E.INCOMPATIBILIDAD_DOCUMENTADA)

    def test_promedio_no_equivale_a_instantanea(self):
        original = next(r for r in self.plan.requisitos if r.condicion.dimension is D.TIPO_MEDICION)
        condicion = replace(original.condicion, valores_permitidos=("instantanea-ficticia",))
        regla = replace(self.regla, aplicabilidad=tuple(condicion if c.dimension is D.TIPO_MEDICION else c
                                                      for c in self.regla.aplicabilidad))
        plan = replace(self.plan, regla=regla, requisitos=tuple(replace(r, condicion=condicion)
            if r is original else r for r in self.plan.requisitos))
        self.assertEqual(self.evaluar(plan=plan, expediente=self.con_dato(D.TIPO_MEDICION,
                         valor="promedio-ficticio")).estado, E.INCOMPATIBILIDAD_DOCUMENTADA)

    def test_agregacion_independiente_de_modalidad(self):
        plan = self.exigir(A.AGREGACION_TEMPORAL, "promedio-ficticio")
        expediente = self.con_dato(A.AGREGACION_TEMPORAL, valor="total-ficticio", nivel=N.VERIFICADA,
                                   referencias=(self.ref_producto.identificador,))
        self.assertEqual(self.evaluar(plan=plan, expediente=expediente).estado, E.INCOMPATIBILIDAD_DOCUMENTADA)

    def test_frecuencia_incompatible(self):
        self.assertEqual(self.evaluar(expediente=self.con_dato(D.FRECUENCIA, valor="otra-frecuencia")).estado,
                         E.INCOMPATIBILIDAD_DOCUMENTADA)

    def test_frecuencia_desconocida(self):
        self.assertEqual(self.evaluar(expediente=self.con_dato(D.FRECUENCIA, valor=None, nivel=N.DESCONOCIDA)).estado,
                         E.INFORMACION_INSUFICIENTE)

    def test_instrumento_desconocido(self):
        self.assertEqual(self.evaluar(plan=self.exigir(D.INSTRUMENTO)).estado, E.INFORMACION_INSUFICIENTE)

    def test_tipo_estacion_desconocido(self):
        self.assertEqual(self.evaluar(plan=self.exigir(D.TIPO_ESTACION)).estado, E.INFORMACION_INSUFICIENTE)

    def test_identidad_estacion_ambigua(self):
        plan = self.exigir(A.IDENTIDAD_ESTACION)
        expediente = self.con_dato(A.IDENTIDAD_ESTACION, nivel=N.CONTRADICTORIA,
                                   contradicciones=("Dos identidades posibles sin resolver",))
        self.assertEqual(self.evaluar(plan=plan, expediente=expediente).estado, E.EVIDENCIA_CONTRADICTORIA)

    def test_cobertura_geografica_insuficiente(self):
        self.assertEqual(self.evaluar(plan=self.exigir(D.GEOGRAFIA)).estado, E.INFORMACION_INSUFICIENTE)

    def test_cobertura_no_infiere_contencion(self):
        expediente = self.con_dato(D.GEOGRAFIA, valor="region-grande-ficticia", nivel=N.VERIFICADA,
                                   referencias=(self.ref_producto.identificador,))
        self.assertEqual(self.evaluar(plan=self.exigir(D.GEOGRAFIA, "subregion-ficticia"),
                                     expediente=expediente).estado, E.INCOMPATIBILIDAD_DOCUMENTADA)

    def test_continuidad_no_se_deduce_de_frecuencia(self):
        self.assertEqual(self.evaluar(plan=self.exigir(A.CONTINUIDAD_SERIE)).estado, E.INFORMACION_INSUFICIENTE)

    def test_cobertura_y_periodo_aplicacion_explicitos(self):
        for dimension in (A.COBERTURA_APLICACION, A.VIGENCIA_APLICACION, A.RESTRICCION_INSTITUCIONAL,
                          A.PARAMETROS_ESPECIFICOS, A.INCERTIDUMBRE, D.AMBIENTE):
            with self.subTest(dimension=dimension):
                self.assertEqual(self.evaluar(plan=self.exigir(dimension)).estado, E.INFORMACION_INSUFICIENTE)

    def test_documento_regla_sin_version(self):
        ref = replace(self.ref_regla, version_documento=None)
        plan = replace(self.plan, regla=replace(self.regla, referencias=(ref,)),
                       documentos=(replace(self.doc_regla, referencia=ref),))
        self.assertEqual(self.evaluar(plan=plan).estado, E.INFORMACION_INSUFICIENTE)

    def test_documento_producto_sin_version_o_fecha(self):
        for campo in ("version_documento", "fecha_documento"):
            ref = replace(self.ref_producto, **{campo: None})
            expediente = replace(self.expediente, documentos=(replace(self.doc_producto, referencia=ref),))
            with self.subTest(campo=campo):
                self.assertEqual(self.evaluar(expediente=expediente).estado, E.INFORMACION_INSUFICIENTE)

    def test_documento_obsoleto_verificado(self):
        expediente = replace(self.expediente, documentos=(replace(self.doc_producto, vigencia=V.OBSOLETO),))
        self.assertEqual(self.evaluar(expediente=expediente).estado, E.INCOMPATIBILIDAD_DOCUMENTADA)

    def test_obsolescencia_inferida_no_es_incompatibilidad_demostrada(self):
        expediente = replace(self.expediente, documentos=(replace(self.doc_producto,
            vigencia=V.OBSOLETO, nivel=N.INFERIDA),))
        self.assertEqual(self.evaluar(expediente=expediente).estado, E.COMPATIBILIDAD_CONDICIONADA)

    def test_vigencia_desconocida(self):
        plan = replace(self.plan, documentos=(replace(self.doc_regla, vigencia=V.DESCONOCIDA),))
        self.assertEqual(self.evaluar(plan=plan).estado, E.COMPATIBILIDAD_CONDICIONADA)

    def test_referencias_contradictorias(self):
        ref = replace(self.ref_regla, version_documento="otra-edicion")
        expediente = replace(self.expediente, documentos=(*self.expediente.documentos,
                              replace(self.doc_regla, referencia=ref)))
        self.assertEqual(self.evaluar(expediente=expediente).estado, E.EVIDENCIA_CONTRADICTORIA)

    def test_distintos_ids_mismo_localizador_y_version_conflictiva(self):
        ref = replace(self.ref_regla, identificador="otro-id", version_documento="otra-edicion")
        expediente = replace(self.expediente, documentos=(*self.expediente.documentos,
                              replace(self.doc_regla, referencia=ref)))
        self.assertEqual(self.evaluar(expediente=expediente).estado, E.EVIDENCIA_CONTRADICTORIA)

    def test_alias_de_misma_referencia_no_inventa_contradiccion(self):
        ref = replace(self.ref_regla, identificador="alias-fixture")
        expediente = replace(self.expediente, documentos=(*self.expediente.documentos,
                              replace(self.doc_regla, referencia=ref)))
        self.assertEqual(self.evaluar(expediente=expediente).estado, E.COMPATIBILIDAD_DOCUMENTAL_DEMOSTRADA)

    def test_distintas_secciones_de_mismo_documento_no_son_contradiccion(self):
        expediente = replace(self.expediente, documentos=(*self.expediente.documentos,
                              replace(self.doc_regla, localizacion="otra-seccion-ficticia")))
        self.assertEqual(self.evaluar(expediente=expediente).estado, E.COMPATIBILIDAD_DOCUMENTAL_DEMOSTRADA)

    def test_dos_afirmaciones_distintas_no_se_elige_la_favorable(self):
        otro = replace(self.expediente.afirmaciones[2], valor="otra-variable", nivel=N.DECLARADA)
        expediente = replace(self.expediente, afirmaciones=(*self.expediente.afirmaciones, otro))
        self.assertEqual(self.evaluar(expediente=expediente).estado, E.EVIDENCIA_CONTRADICTORIA)

    def test_dato_inferido_o_declarado_no_demuestra_compatibilidad(self):
        for nivel in (N.INFERIDA, N.DECLARADA):
            with self.subTest(nivel=nivel):
                self.assertEqual(self.evaluar(expediente=self.con_dato(D.UNIDAD, nivel=nivel)).estado,
                                 E.COMPATIBILIDAD_CONDICIONADA)

    def test_dato_no_verificado_distinto_no_afirma_incompatibilidad(self):
        expediente = self.con_dato(D.UNIDAD, valor="otra-unidad", nivel=N.DECLARADA)
        self.assertEqual(self.evaluar(expediente=expediente).estado, E.COMPATIBILIDAD_CONDICIONADA)

    def test_afirmacion_verificada_documento_declarado_no_basta(self):
        expediente = replace(self.expediente, documentos=(replace(self.doc_producto, nivel=N.DECLARADA),))
        self.assertEqual(self.evaluar(expediente=expediente).estado, E.COMPATIBILIDAD_CONDICIONADA)

    def test_integridad_hash_no_autentica_emisor_ni_verifica_documento(self):
        ref = replace(self.ref_producto, sha256_referencia="a" * 64)
        expediente = replace(self.expediente, documentos=(replace(self.doc_producto, referencia=ref,
                                                                 nivel=N.DECLARADA),))
        self.assertEqual(self.evaluar(expediente=expediente).estado, E.COMPATIBILIDAD_CONDICIONADA)

    def test_documento_desconocido(self):
        expediente = replace(self.expediente, documentos=(replace(self.doc_producto, nivel=N.DESCONOCIDA),))
        self.assertEqual(self.evaluar(expediente=expediente).estado, E.INFORMACION_INSUFICIENTE)

    def test_zona_desconocida_no_bloquea_limite_estatico(self):
        expediente = self.con_dato(A.ZONA_HORARIA)
        self.assertEqual(self.evaluar(expediente=expediente).estado, E.COMPATIBILIDAD_DOCUMENTAL_DEMOSTRADA)

    def test_zona_desconocida_bloquea_requisito_temporal(self):
        self.assertEqual(self.evaluar(plan=self.exigir(A.ZONA_HORARIA)).estado, E.INFORMACION_INSUFICIENTE)

    def test_requisito_condicional_inactivo_demostrado(self):
        guardia = CondicionAplicabilidad(D.TIPO_MEDICION, ("secuencia-ficticia",), (self.ref_regla.identificador,))
        plan = self.exigir(A.ZONA_HORARIA, tipo=T.CONDICIONAL, activar_si=guardia)
        r = self.evaluar(plan=plan)
        self.assertEqual(r.estado, E.COMPATIBILIDAD_DOCUMENTAL_DEMOSTRADA)
        self.assertEqual(r.hallazgos[-1].estado, R.NO_APLICA)

    def test_requisito_condicional_activo_necesita_evidencia(self):
        guardia = CondicionAplicabilidad(D.TIPO_MEDICION, (self.valores[D.TIPO_MEDICION],),
                                         (self.ref_regla.identificador,))
        plan = self.exigir(A.ZONA_HORARIA, tipo=T.CONDICIONAL, activar_si=guardia)
        self.assertEqual(self.evaluar(plan=plan).estado, E.INFORMACION_INSUFICIENTE)

    def test_condicion_desconocida_no_se_desactiva(self):
        guardia = CondicionAplicabilidad(D.INSTRUMENTO, ("instrumento-ficticio",), (self.ref_regla.identificador,))
        plan = self.exigir(A.ZONA_HORARIA, tipo=T.CONDICIONAL, activar_si=guardia)
        r = self.evaluar(plan=plan)
        self.assertEqual((r.estado, r.hallazgos[-1].estado), (E.COMPATIBILIDAD_CONDICIONADA, R.CONDICIONADO))

    def test_condicion_inferida_no_se_desactiva_por_diferencia(self):
        guardia = CondicionAplicabilidad(D.INSTRUMENTO, ("instrumento-ficticio",), (self.ref_regla.identificador,))
        expediente = self.con_dato(D.INSTRUMENTO, valor="otro-instrumento", nivel=N.INFERIDA,
                                   referencias=(self.ref_producto.identificador,))
        plan = self.exigir(A.ZONA_HORARIA, tipo=T.CONDICIONAL, activar_si=guardia)
        r = self.evaluar(plan=plan, expediente=expediente)
        self.assertEqual((r.estado, r.hallazgos[-1].estado), (E.COMPATIBILIDAD_CONDICIONADA, R.CONDICIONADO))

    def test_ausencia_explicita_de_restriccion_requiere_fuente(self):
        condicion = CondicionAplicabilidad(D.INSTRUMENTO, referencias=(self.ref_regla.identificador,), sin_restriccion=True)
        plan = replace(self.plan, requisitos=(*self.plan.requisitos, Requisito("instrumento", condicion)))
        self.assertEqual(self.evaluar(plan=plan).estado, E.COMPATIBILIDAD_DOCUMENTAL_DEMOSTRADA)
        plan = replace(plan, requisitos=(*self.plan.requisitos, Requisito("instrumento", replace(condicion, referencias=()))))
        self.assertEqual(self.evaluar(plan=plan).estado, E.INFORMACION_INSUFICIENTE)

    def test_incertidumbres_y_pendientes_no_se_ignoran(self):
        for campo in ("incertidumbres", "pendientes"):
            with self.subTest(campo=campo):
                expediente = self.con_dato(D.UNIDAD, **{campo: ("Aspecto sin resolver",)})
                self.assertEqual(self.evaluar(expediente=expediente).estado, E.COMPATIBILIDAD_CONDICIONADA)

    def test_contradiccion_regla_prioritaria_frente_a_faltantes(self):
        plan = replace(self.exigir(D.INSTRUMENTO), regla=replace(self.regla,
                       contradicciones_documentales=("Contradiccion-ficticia",)))
        self.assertEqual(self.evaluar(plan=plan).estado, E.EVIDENCIA_CONTRADICTORIA)

    def test_documento_con_contradiccion_explicita(self):
        doc = replace(self.doc_producto, nivel=N.CONTRADICTORIA, contradicciones=("Texto en conflicto",))
        expediente = replace(self.expediente, documentos=(doc,))
        self.assertEqual(self.evaluar(expediente=expediente).estado, E.EVIDENCIA_CONTRADICTORIA)

    def test_identidad_producto_no_puede_cambiarse_en_afirmacion(self):
        self.assertEqual(self.evaluar(expediente=self.con_dato(D.PRODUCTO, valor="otro-producto")).estado,
                         E.EVIDENCIA_CONTRADICTORIA)

    def test_regla_propuesta_permanece_sin_ejecucion_y_sin_mutacion(self):
        catalogo = CatalogoReglasCientificas()
        propuesta = catalogo.registrar(self.regla)
        antes = catalogo.historial(self.regla.identificador, self.regla.version)
        with patch.object(catalogo, "cambiar_estado", side_effect=AssertionError("No aprobar")):
            r = self.evaluar()
        despues = catalogo.historial(self.regla.identificador, self.regla.version)
        self.assertEqual(antes, despues)
        self.assertEqual(propuesta.estado, EstadoReglaCientifica.PROPUESTA)
        self.assertFalse(r.ejecucion_autorizada)
        self.assertFalse(catalogo.comprobar_habilitacion(self.regla.identificador, self.regla.version,
                                                       ContextoCientifico()).ejecucion_autorizada)

    def test_etiqueta_aprobada_no_habilita_ejecucion(self):
        # Doble: no se crea una aprobación humana ni se invoca una transición.
        revision = Mock(spec=RevisionReglaCientifica, estado=EstadoReglaCientifica.APROBADA, regla=self.regla)
        with self.assertRaises(TypeError): verificar_aplicabilidad(revision, self.expediente)
        r = self.evaluar(plan=replace(self.plan, regla=revision.regla))
        self.assertFalse(r.ejecucion_autorizada)
        h = HabilitacionCientifica(revision, True, ("Fixture de barrera",))
        self.assertFalse(h.ejecucion_autorizada)
        with self.assertRaises(TypeError): verificar_aplicabilidad(h, self.expediente)

    def test_no_admite_permisos_callbacks_o_configuracion_ejecutable(self):
        for objeto in ({"activar": True}, lambda: True, "__import__('os').getcwd()"):
            with self.subTest(tipo=type(objeto)), self.assertRaises(TypeError):
                verificar_aplicabilidad(objeto, self.expediente)
            with self.subTest(condicion=type(objeto)), self.assertRaises(TypeError):
                Requisito("req", objeto)
        with self.assertRaises(TypeError): replace(self.evaluar(), ejecucion_autorizada=True)

    def test_diagnostico_no_se_usa_como_booleano_o_permiso_del_catalogo(self):
        r = self.evaluar()
        with self.assertRaises(TypeError): bool(r)
        with self.assertRaises(TypeError): CatalogoReglasCientificas().registrar(r)
        self.assertFalse(callable(r))

    def test_texto_con_apariencia_de_codigo_permanece_inerte(self):
        expediente = self.con_dato(D.VARIABLE, valor="__import__('os').getcwd()")
        with patch("builtins.eval", side_effect=AssertionError("No evaluar código")), \
             patch("builtins.exec", side_effect=AssertionError("No ejecutar código")):
            r = self.evaluar(expediente=expediente)
        self.assertEqual(r.estado, E.INCOMPATIBILIDAD_DOCUMENTADA)
        with self.assertRaises(ValueError): self.con_dato(D.VARIABLE, valor=lambda: True)

    def test_fixture_experimental_no_es_referencia_institucional(self):
        evidencia = EvidenciaSintetica("FIXTURE-BARRERA", "v1", "Evidencia inventada")
        with self.assertRaises(TypeError): replace(self.doc_regla, referencia=evidencia)
        documental = replace(self.doc_producto, naturaleza=Origen.DOCUMENTAL)
        expediente = replace(self.expediente, documentos=(documental,))
        with self.assertRaises(ValueError): self.evaluar(expediente=expediente)
        with self.assertRaises(ValueError): replace(self.expediente, documentos=(self.doc_producto, documental))

    def test_rechaza_contexto_lectores_y_rutas_reales(self):
        for objeto in (ContextoCientifico(), Path("no-abrir.csv"), {"producto": "datos"}, RegistroCSV(2, 2, 2, (), True)):
            with self.subTest(tipo=type(objeto)), self.assertRaises(TypeError):
                verificar_aplicabilidad(self.plan, objeto)

    def test_paso75_rechaza_diagnostico_y_no_se_integra(self):
        r = self.evaluar()
        ev = EvidenciaSintetica("FIXTURE-BARRERA", "v1", "Prueba inventada")
        regla = ReglaLimitesSintetica("EXP-LIM-BARRERA", "v1", "X", "u", "m", "f",
                                    Decimal("-2.5"), Decimal("7.5"), True, True, ev)
        obs = ObservacionSintetica("OBS-FIXTURE", "X", "1", "u", "m", "f", ev)
        with self.assertRaises(TypeError): evaluar_limites_sinteticos(r, obs)
        with self.assertRaises(TypeError): evaluar_limites_sinteticos(regla, r)

    def test_no_omite_ni_debilita_condiciones_del_catalogo(self):
        with self.assertRaisesRegex(ValueError, "conservarse"):
            replace(self.plan, requisitos=self.plan.requisitos[1:])
        primero = self.plan.requisitos[0]
        with self.assertRaisesRegex(ValueError, "conservarse"):
            replace(self.plan, requisitos=(replace(primero, tipo=T.CONDICIONAL,
                activar_si=self.plan.requisitos[1].condicion), *self.plan.requisitos[1:]))

    def test_parametros_del_catalogo_necesitan_requisito_explicito(self):
        regla = replace(self.regla, parametros=(ParametroCientifico("modo", "ficticio",
                        referencias=(self.ref_regla.identificador,)),))
        with self.assertRaisesRegex(ValueError, "Parámetros"):
            replace(self.plan, regla=regla)
        plan = replace(self.exigir(A.PARAMETROS_ESPECIFICOS), regla=regla)
        self.assertEqual(self.evaluar(plan=plan).estado, E.INFORMACION_INSUFICIENTE)

    def test_no_hay_compatibilidad_vacia(self):
        regla = replace(self.regla, aplicabilidad=(), referencias=())
        plan = EspecificacionAplicabilidad(regla, (), ())
        self.assertEqual(self.evaluar(plan=plan).estado, E.INFORMACION_INSUFICIENTE)

    def test_referencia_de_regla_sin_evidencia(self):
        self.assertEqual(self.evaluar(plan=replace(self.plan, documentos=())).estado, E.INFORMACION_INSUFICIENTE)

    def test_identificadores_y_dimensiones_sin_duplicacion(self):
        with self.assertRaises(ValueError): replace(self.plan, requisitos=(*self.plan.requisitos, self.plan.requisitos[0]))
        with self.assertRaises(ValueError): replace(self.expediente, afirmaciones=(*self.expediente.afirmaciones,
                                                                                self.expediente.afirmaciones[0]))
        with self.assertRaises(ValueError): replace(self.plan, documentos=(self.doc_regla, self.doc_regla))

    def test_referencias_ajenas_no_se_aceptan(self):
        with self.assertRaises(ValueError): replace(self.expediente, documentos=())
        with self.assertRaises(ValueError): replace(self.plan, documentos=(self.doc_producto,))
        with self.assertRaises(ValueError): replace(self.plan, requisitos=(*self.plan.requisitos,
            Requisito("instrumento", CondicionAplicabilidad(D.INSTRUMENTO, ("x",), ("ajena",)))))

    def test_inmutabilidad_y_preservacion_literal(self):
        r = self.evaluar()
        self.assertEqual(r.expediente.producto.identificador, " producto-fixture ")
        with self.assertRaises(FrozenInstanceError): r.estado = E.INFORMACION_INSUFICIENTE
        with self.assertRaises(FrozenInstanceError): r.expediente.afirmaciones[0].valor = "otro"
        with self.assertRaises(FrozenInstanceError): r.especificacion.requisitos[0].tipo = T.CONDICIONAL
        with self.assertRaises(TypeError): replace(self.plan, requisitos=list(self.plan.requisitos))

    def test_determinismo_y_traza_completa(self):
        a, b = self.evaluar(), self.evaluar()
        self.assertEqual(a, b)
        self.assertIs(a.especificacion, self.plan)
        self.assertIs(a.expediente, self.expediente)
        self.assertEqual(a.version_verificador, "1.0.0")

    def test_traza_no_omite_referencias_dentro_del_presupuesto(self):
        docs = (self.doc_producto, *(replace(self.doc_producto, referencia=replace(self.ref_producto,
            identificador="doc-fixture-" + str(i), localizador="urn:fixture:extra:" + str(i))) for i in range(63)))
        referencias = tuple(d.referencia.identificador for d in docs)
        afirmaciones = tuple(replace(a, referencias=referencias) if a.dimension is D.VARIABLE else a
                             for a in self.expediente.afirmaciones)
        expediente = replace(self.expediente, documentos=docs, afirmaciones=afirmaciones)
        r = self.evaluar(expediente=expediente)
        self.assertEqual(r.estado, E.COMPATIBILIDAD_DOCUMENTAL_DEMOSTRADA)
        hallazgo = next(h for h in r.hallazgos if h.requisito_id == D.VARIABLE.value)
        self.assertEqual(len(hallazgo.referencias), 65)

    def test_resultados_no_admiten_colecciones_mutables(self):
        r = self.evaluar()
        with self.assertRaises(TypeError): replace(r, hallazgos=list(r.hallazgos))
        with self.assertRaises(TypeError): replace(r.hallazgos[0], motivos=["mutable"])

    def test_validaciones_de_nivel_evidencia_y_presupuestos(self):
        with self.assertRaises(ValueError): self.con_dato(D.UNIDAD, nivel=N.DESCONOCIDA)
        with self.assertRaises(ValueError): self.con_dato(D.UNIDAD, referencias=())
        with self.assertRaises(ValueError): replace(self.doc_producto, nivel=N.CONTRADICTORIA)
        with self.assertRaises(TypeError): replace(self.doc_producto, nivel="verificada")
        with self.assertRaises(ValueError): self.con_dato(D.UNIDAD, valor="x" * 513)
        with self.assertRaises(TypeError): replace(self.expediente, afirmaciones=self.expediente.afirmaciones * 22)

    def test_verificador_no_ejecuta_algoritmos_ni_realiza_io(self):
        with patch("builtins.open", side_effect=AssertionError("I/O")), \
             patch("io.open", side_effect=AssertionError("I/O")), \
             patch("os.stat", side_effect=AssertionError("I/O")), \
             patch("os.scandir", side_effect=AssertionError("I/O")), \
             patch("sqlite3.connect", side_effect=AssertionError("SQLite")), \
             patch("socket.socket.connect", side_effect=AssertionError("red")), \
             patch("spica.calidad.experimental.limites.evaluar_limites_sinteticos", side_effect=AssertionError("QA")):
            r = self.evaluar()
        self.assertEqual(r.estado, E.COMPATIBILIDAD_DOCUMENTAL_DEMOSTRADA)

    def test_nivel0_preserva_resultados(self):
        fila = ("ID-FIXTURE", "ESTACION-FIXTURE", "20000101", "00000", "1", "2", "3", "1.25", "2.5", "3.5",
                "RED-FIXTURE", "DEP", "PROV", "DIST", "12345.0", "20000101")
        registro = adaptar_registro(RegistroCSV(2, 2, 2, fila, True))
        antes = tuple(evaluar_registro(registro, ProcedenciaQA()))
        self.evaluar()
        self.assertEqual(antes, tuple(evaluar_registro(registro, ProcedenciaQA())))
        self.assertEqual(len(antes), 30)
        self.assertEqual(registro.valores_csv_originales, fila)


if __name__ == "__main__":
    unittest.main()
