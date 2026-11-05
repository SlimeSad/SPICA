"""Escenarios 84-B y auditoría temporal: entradas y evidencias inventadas."""

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import unittest

from spica.adquisicion.catalogo.modelos import ProcedenciaCatalogo
from spica.interoperabilidad import DimensionEvaluacion as D, EstadoAptitud as E, Respaldo
from spica.interoperabilidad.adaptadores import adaptar_meteorologia, adaptar_vectorial
from spica.interoperabilidad.operaciones import OperacionPropuesta, evaluar_operacion
from test_adaptadores_interoperabilidad import (
    catalogo, disponibilidad, estacion, meteorologia, observacion, variable, vector,
)
from test_interoperabilidad_modelos import FECHA, PROC, periodo, recurso, espacial, temporal


def propuesta(dimension=D.ESPACIAL, precision=False):
    return OperacionPropuesta("operacion-sintetica-no-ejecutada", dimension, precision)


class IntegracionInteroperabilidadTests(unittest.TestCase):
    def sin_operacion_cientifica(self, resultado):
        self.assertFalse(resultado.operacion_ejecutada)
        self.assertFalse(resultado.verificacion_espacial_efectiva)
        self.assertEqual(resultado.confiabilidad_cientifica, "no_evaluada")

    def test_A_estacion_sin_coordenadas_y_capa_con_crs(self):
        a = meteorologia(estacion=estacion(coordenada_x=None, coordenada_y=None))
        b = adaptar_vectorial(*vector(), revision_metadatos="revision-local-1")
        r = evaluar_operacion(a.recurso, b.recurso, propuesta())
        self.assertEqual(r.aptitud.estado, E.PENDIENTE_DE_EVIDENCIA)
        self.assertTrue(any("coordenadas" in f for f in r.aptitud.faltantes))
        self.assertFalse(r.condiciones_documentales_satisfechas)
        self.sin_operacion_cientifica(r)

    def test_B_fechas_aparentemente_compatibles_sin_zona(self):
        a, b = meteorologia(), meteorologia(revision_metadatos="revision-local-2")
        r = evaluar_operacion(a.recurso, b.recurso, propuesta(D.TEMPORAL))
        self.assertEqual(r.aptitud.estado, E.PENDIENTE_DE_EVIDENCIA)
        self.assertTrue(any("zona" in f for f in r.aptitud.faltantes))
        self.assertIsNone(a.recurso.temporal.observaciones.inicio.tzinfo)
        self.sin_operacion_cientifica(r)

    def test_C_declaraciones_espaciales_no_son_verificacion(self):
        a, b = meteorologia(), meteorologia(revision_metadatos="revision-local-2")
        r = evaluar_operacion(a.recurso, b.recurso, propuesta())
        self.assertEqual(r.aptitud.estado, E.PENDIENTE_DE_EVIDENCIA)
        self.assertTrue(any("coordenadas" in f for f in r.aptitud.faltantes))
        self.sin_operacion_cientifica(r)

    def test_D_crs_por_ambito_no_se_homogeneizan_al_evaluar(self):
        a = adaptar_vectorial(*vector(), revision_metadatos="revision-local-1")
        anterior = a.recurso.espacial.crs
        b = replace(a.recurso, revision_metadatos="revision-local-2")
        r = evaluar_operacion(a.recurso, b, propuesta())
        self.assertEqual(r.aptitud.estado, E.PENDIENTE_DE_EVIDENCIA)
        self.assertNotEqual(anterior[0].declaracion, anterior[2].declaracion)
        self.assertIs(r.aptitud.recursos[0].espacial.crs, anterior)
        self.sin_operacion_cientifica(r)

    def test_E_nueva_evidencia_contradictoria_conserva_revision_y_resultado(self):
        inicial = meteorologia()
        pareja = recurso("otra-identidad")
        previo = evaluar_operacion(inicial.recurso, pareja, propuesta())
        p2 = ProcedenciaCatalogo("fixture://respuesta-futura-inventada", FECHA + timedelta(days=1),
                                "revision_sintetica", "evidencia-nueva-inventada")
        nueva = adaptar_meteorologia(catalogo(procedencia=p2), revision_metadatos="revision-local-2",
                    estacion=estacion(), disponibilidad=disponibilidad(estacion_id="otro-codigo", procedencia=p2),
                    variable=variable(), observacion=observacion())
        nueva_descripcion = replace(nueva.recurso, sustituye_revision=inicial.recurso.revision_metadatos)
        actual = evaluar_operacion(nueva_descripcion, pareja, propuesta())
        self.assertEqual(actual.aptitud.estado, E.INCOMPATIBLE)
        self.assertTrue(actual.aptitud.contradicciones)
        self.assertEqual(previo.aptitud.estado, E.PENDIENTE_DE_EVIDENCIA)
        self.assertIs(previo.aptitud.recursos[0], inicial.recurso)
        self.assertIn(inicial.recurso.procedencia, previo.aptitud.evidencias)
        self.assertNotIn(p2, previo.aptitud.evidencias)
        self.assertEqual(inicial.originales["disponibilidad"]["estacion_id"], " codigo original ")
        self.assertEqual(nueva.originales["disponibilidad"]["estacion_id"], "otro-codigo")
        self.assertEqual(evaluar_operacion(nueva_descripcion, pareja, propuesta()), actual)
        self.assertEqual(actual.aptitud.version_evaluador, previo.aptitud.version_evaluador)
        self.sin_operacion_cientifica(actual)

    def test_F_aptitud_con_evidencia_sintetica_no_afirma_superposicion(self):
        a = meteorologia().recurso
        # Aporte explícito de una fixture documentada, nunca promoción del adaptador.
        a = replace(a, revision_metadatos="revision-con-evidencia-inventada",
                    sustituye_revision=a.revision_metadatos, espacial=espacial())
        b = recurso("otra-identidad", espacial=espacial(coordenadas=(9000, 9000)))
        r = evaluar_operacion(a, b, propuesta(precision=True))
        self.assertEqual(r.aptitud.estado, E.APTO_ESTRUCTURALMENTE)
        self.assertTrue(r.condiciones_documentales_satisfechas)
        self.assertEqual(r.faltantes_operacion, ())
        self.assertNotEqual(a.espacial.coordenadas, b.espacial.coordenadas)
        self.sin_operacion_cientifica(r)

    def test_G_procedencia_insuficiente_no_desaparece_en_adaptacion(self):
        p = replace(PROC, evidencia=None)
        a = adaptar_meteorologia(catalogo(procedencia=p), revision_metadatos="r1").recurso
        r = evaluar_operacion(a, recurso(), propuesta())
        self.assertEqual(r.aptitud.estado, E.PENDIENTE_DE_EVIDENCIA)
        self.assertIn("r0.procedencia_con_evidencia", r.aptitud.faltantes)
        self.sin_operacion_cientifica(r)

    def test_H_precision_exigida_ausente_y_politica_general_conservada(self):
        a = recurso(espacial=espacial(precision_declarada=None, incertidumbre=None, respaldo_calidad=Respaldo()))
        r = evaluar_operacion(a, recurso("dos"), propuesta(precision=True))
        self.assertEqual(r.aptitud.estado, E.PENDIENTE_DE_EVIDENCIA)
        self.assertEqual(len(r.faltantes_operacion), 3)
        self.assertFalse(r.condiciones_documentales_satisfechas)
        sin_requisito_extra = evaluar_operacion(a, recurso("dos"), propuesta(precision=False))
        self.assertEqual(sin_requisito_extra.faltantes_operacion, ())
        self.assertEqual(sin_requisito_extra.aptitud.estado, E.PENDIENTE_DE_EVIDENCIA)
        self.assertFalse(sin_requisito_extra.condiciones_documentales_satisfechas)
        temporal_solo = evaluar_operacion(a, recurso("dos"), propuesta(D.TEMPORAL))
        self.assertEqual(temporal_solo.aptitud.estado, E.APTO_ESTRUCTURALMENTE)
        self.sin_operacion_cientifica(temporal_solo)

    def test_politica_explicita_y_resultado_no_permiten_afirmaciones_contradictorias(self):
        with self.assertRaises(TypeError):
            OperacionPropuesta("sin-politica-explicita", D.ESPACIAL)
        with self.assertRaises(ValueError):
            propuesta(D.TEMPORAL, precision=True)
        pendiente = evaluar_operacion(meteorologia().recurso, recurso(), propuesta())
        with self.assertRaises(ValueError):
            replace(pendiente, condiciones_documentales_satisfechas=True)
        with self.assertRaises(TypeError):
            replace(pendiente, operacion_ejecutada=True)


class AuditoriaTemporalIntegradaTests(unittest.TestCase):
    def test_offsets_equivalentes_preservan_originales_y_no_localizan_datos(self):
        a = meteorologia().recurso
        b = replace(a, revision_metadatos="revision-local-2")
        for zona in (timezone.utc, timezone(timedelta(hours=-5)), timezone(timedelta(hours=3))):
            with self.subTest(zona=zona):
                inicio, fin = FECHA.astimezone(zona), (FECHA + timedelta(days=1)).astimezone(zona)
                t = temporal(valores_originales=(("INSTANTE", inicio.isoformat()),), fecha_observacion=inicio,
                             zona_horaria_declarada=inicio.tzname(), observaciones=periodo(inicio, fin))
                # Nuevas descripciones con evidencia explícita sintética y versión distinta.
                enriquecido = replace(b, temporal=t)
                primero = replace(a, temporal=temporal())
                r = evaluar_operacion(primero, enriquecido, propuesta(D.TEMPORAL))
                self.assertEqual(r.aptitud.estado, E.APTO_ESTRUCTURALMENTE)
                self.assertIs(enriquecido.temporal.observaciones.inicio, inicio)
                self.assertEqual(enriquecido.temporal.valores_originales[0][1], inicio.isoformat())
                self.assertIsNone(a.temporal.observaciones.inicio.tzinfo)
                self.assertEqual(dict(a.temporal.valores_originales)["HORA"], "10000")
                self.assertFalse(r.operacion_ejecutada)

    def test_intervalos_iguales_contacto_y_separacion_con_limites_explicitos(self):
        a = recurso(temporal=temporal(fecha_observacion=None))
        casos = ((FECHA, FECHA, (True, True), E.APTO_ESTRUCTURALMENTE),
                 (FECHA + timedelta(days=1), FECHA + timedelta(days=2), (True, False), E.APTO_ESTRUCTURALMENTE),
                 (FECHA + timedelta(days=1), FECHA + timedelta(days=2), (False, True), E.INCOMPATIBLE),
                 (FECHA + timedelta(days=2), FECHA + timedelta(days=3), (True, True), E.INCOMPATIBLE))
        for inicio, fin, limites, esperado in casos:
            with self.subTest(inicio=inicio, limites=limites):
                b = recurso("dos", temporal=temporal(fecha_observacion=None,
                            observaciones=periodo(inicio, fin, limites_inclusivos=limites)))
                r = evaluar_operacion(a, b, propuesta(D.TEMPORAL))
                self.assertEqual(r.aptitud.estado, esperado)
                self.assertFalse(r.operacion_ejecutada)

    def test_observacion_no_se_sustituye_por_adquisicion_o_publicacion(self):
        for cambio in (dict(observaciones=None, adquirido=FECHA, publicacion=periodo()),
                       dict(convencion=None), dict(zona_horaria_declarada=None),
                       dict(observaciones=periodo(datetime(2026, 1, 1), datetime(2026, 1, 2)),
                            fecha_observacion=datetime(2026, 1, 1))):
            with self.subTest(cambio=cambio):
                a = recurso(temporal=temporal(**cambio))
                r = evaluar_operacion(a, recurso("dos"), propuesta(D.TEMPORAL))
                self.assertEqual(r.aptitud.estado, E.PENDIENTE_DE_EVIDENCIA)
                self.assertFalse(r.condiciones_documentales_satisfechas)

    def test_contradicciones_temporales_no_se_ocultan_por_la_operacion(self):
        for cambio in (dict(fecha_observacion=FECHA + timedelta(days=2)),
                       dict(observaciones=periodo(FECHA.astimezone(timezone(timedelta(hours=-5))),
                                                  FECHA.astimezone(timezone(timedelta(hours=-5)))))):
            with self.subTest(cambio=cambio):
                r = evaluar_operacion(recurso(temporal=temporal(**cambio)), recurso("dos"), propuesta(D.TEMPORAL))
                self.assertEqual(r.aptitud.estado, E.INCOMPATIBLE)
                self.assertTrue(r.aptitud.contradicciones)
                self.assertFalse(r.operacion_ejecutada)


if __name__ == "__main__":
    unittest.main()
