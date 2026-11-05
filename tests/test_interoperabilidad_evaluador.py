"""Reglas documentales genéricas; ningún recurso institucional real."""

from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import ast
import subprocess
import sys
import unittest
from unittest.mock import patch

from test_interoperabilidad_modelos import FECHA, PROC, VER, DEC, crs, espacial, temporal, periodo, recurso
from spica.adquisicion.nucleo import Fuente
from spica.adquisicion.vectorial import ReferenciaEspacial
from spica.interoperabilidad import (
    AmbitoCRS as A, DimensionEvaluacion as D, EstadoAptitud as E, IdentidadRecurso,
    MarcoEspacial, MarcoTemporal, RepresentacionEspacial as R, Respaldo, evaluar_aptitud,
)


def evaluar(m=None, dimension=D.ESPACIAL, **kw):
    return evaluar_aptitud(recurso(espacial=espacial() if m is None else m, **kw), recurso("dos"), dimension)


class AptitudEspacialTests(unittest.TestCase):
    def test_coordenadas_verificadas_documentacion_suficiente(self):
        r = evaluar()
        self.assertEqual(r.estado, E.APTO_ESTRUCTURALMENTE)
        self.assertEqual(r.faltantes, ())
        self.assertEqual(r.contradicciones, ())
        self.assertIn(PROC, r.evidencias)
        self.assertIn("sin_validacion_cientifica", r.restricciones)

    def test_coordenadas_solo_declaradas(self):
        r = evaluar(espacial(respaldo_coordenadas=DEC))
        self.assertEqual(r.estado, E.PENDIENTE_DE_EVIDENCIA)
        self.assertIn("r0.espacial.coordenadas.verificacion", r.faltantes)

    def test_coordenadas_ausentes_no_se_inventan_por_distrito(self):
        m = espacial(coordenadas=None, respaldo_coordenadas=Respaldo(),
                     ubicacion_declarada=(("DISTRITO", "distrito-inventado"), ("ESTACION", "nombre")))
        r = evaluar(m)
        self.assertEqual(r.estado, E.PENDIENTE_DE_EVIDENCIA)
        self.assertIsNone(r.recursos[0].espacial.coordenadas)
        self.assertIn("r0.espacial.coordenadas", r.faltantes)

    def test_crs_ausente_o_solo_declarado_no_es_compatible_por_nombre(self):
        for c in ((), (crs(declaracion=None, definicion=None, respaldo=Respaldo()),),
                  (crs(respaldo=DEC),), (crs(definicion=None),), (crs(unidades_ejes=()),)):
            with self.subTest(c=c):
                self.assertEqual(evaluar(espacial(crs=c)).estado, E.PENDIENTE_DE_EVIDENCIA)

    def test_crs_geometria_y_extension_diferentes_no_son_contradiccion(self):
        m = espacial(extension=(0, 0, 3, 4), respaldo_extension=VER,
                     crs=(crs(), crs(A.EXTENSION, declaracion="CRS-SINTETICO-EXTENSION")))
        r = evaluar(m)
        self.assertEqual(r.estado, E.APTO_ESTRUCTURALMENTE)
        self.assertEqual(r.contradicciones, ())
        self.assertNotEqual(m.crs[0].declaracion, m.crs[1].declaracion)

    def test_crs_extension_no_sustituye_crs_geometria(self):
        r = evaluar(espacial(crs=(crs(A.EXTENSION),)))
        self.assertEqual(r.estado, E.PENDIENTE_DE_EVIDENCIA)
        self.assertIn("r0.espacial.crs_geometria.declaracion", r.faltantes)

    def test_alias_crs_y_diferencias_no_se_resuelven(self):
        a = recurso(espacial=espacial(crs=(crs(declaracion=ReferenciaEspacial(102100, 3857)),)))
        b = recurso("dos", espacial=espacial(crs=(crs(declaracion=ReferenciaEspacial(3857)),)))
        r = evaluar_aptitud(a, b, D.ESPACIAL)
        self.assertEqual(r.estado, E.PENDIENTE_DE_EVIDENCIA)
        self.assertIn("espacial.correspondencia_crs_no_documentada", r.faltantes)

    def test_unidades_contradictorias_con_crs_identico(self):
        r = evaluar(espacial(crs=(crs(unidades_ejes=("grado", "grado")),)))
        self.assertEqual(r.estado, E.INCOMPATIBLE)
        self.assertIn("espacial.unidades_incompatibles_para_crs_identico", r.contradicciones)

    def test_cobertura_anunciada_no_se_promueve_a_observada(self):
        m = espacial(cobertura_observada=None, cobertura_anunciada="todo-el-pais-inventado")
        r = evaluar(m)
        self.assertEqual(r.estado, E.PENDIENTE_DE_EVIDENCIA)
        self.assertIsNone(r.recursos[0].espacial.cobertura_observada)

    def test_precision_e_incertidumbre_no_se_deducen_de_escala(self):
        for cambio in (dict(precision_declarada=None), dict(incertidumbre=None), dict(respaldo_calidad=DEC)):
            with self.subTest(cambio=cambio):
                r = evaluar(espacial(**cambio), atributos_declarados=("escala-de-mapa-1:50000",))
                self.assertEqual(r.estado, E.PENDIENTE_DE_EVIDENCIA)

    def test_identidad_ambigua_y_no_verificada_bloquean(self):
        for m in (espacial(identidad_ambigua=True), espacial(identificador_ubicacion="nombre-no-es-codigo", respaldo_identidad=DEC)):
            with self.subTest(m=m):
                self.assertEqual(evaluar(m).estado, E.PENDIENTE_DE_EVIDENCIA)
        self.assertEqual(evaluar(espacial(identidad_ambigua=True, respaldo_identidad=VER)).estado, E.INCOMPATIBLE)

    def test_vector_solo_preparacion_de_metadatos_no_inspeccion_geometrica(self):
        m = espacial(representacion=R.VECTORIAL, coordenadas=None, respaldo_coordenadas=Respaldo(),
                     geometria_declarada="poligono-declarado-en-fixture", respaldo_geometria=VER,
                     extension=(0, 0, 2, 3), respaldo_extension=VER, crs=(crs(), crs(A.EXTENSION)))
        self.assertEqual(evaluar(m).estado, E.APTO_ESTRUCTURALMENTE)
        self.assertEqual(evaluar(replace(m, extension=None, respaldo_extension=Respaldo())).estado, E.PENDIENTE_DE_EVIDENCIA)

    def test_coordenadas_declaradas_en_vector_tambien_requieren_evidencia(self):
        m = espacial(representacion=R.VECTORIAL, respaldo_coordenadas=DEC,
                     geometria_declarada="poligono-declarado-en-fixture", respaldo_geometria=VER,
                     extension=(0, 0, 2, 3), respaldo_extension=VER, crs=(crs(), crs(A.EXTENSION)))
        r = evaluar(m)
        self.assertEqual(r.estado, E.PENDIENTE_DE_EVIDENCIA)
        self.assertIn("r0.espacial.coordenadas.verificacion", r.faltantes)

    def test_raster_no_evaluable_y_representacion_desconocida_pendiente(self):
        self.assertEqual(evaluar(espacial(representacion=R.RASTER)).estado, E.NO_EVALUABLE)
        self.assertEqual(evaluar(MarcoEspacial()).estado, E.PENDIENTE_DE_EVIDENCIA)


class AptitudTemporalTests(unittest.TestCase):
    def test_zona_conocida_y_convencion_documentada(self):
        r = evaluar(dimension=D.TEMPORAL)
        self.assertEqual(r.estado, E.APTO_ESTRUCTURALMENTE)

    def test_zona_desconocida_no_recibe_utc_o_utc_menos_cinco(self):
        m = temporal(zona_horaria_declarada=None)
        r = evaluar(dimension=D.TEMPORAL, temporal=m)
        self.assertEqual(r.estado, E.PENDIENTE_DE_EVIDENCIA)
        self.assertIsNone(r.recursos[0].temporal.zona_horaria_declarada)

    def test_hora_ambigua_se_preserva_sin_reconstruccion(self):
        m = MarcoTemporal(valores_originales=(("FECHA", "20260101"), ("HORA", "10000")))
        r = evaluar(dimension=D.TEMPORAL, temporal=m)
        self.assertEqual(r.estado, E.PENDIENTE_DE_EVIDENCIA)
        self.assertEqual(r.recursos[0].temporal.valores_originales[1], ("HORA", "10000"))
        self.assertIsNone(m.fecha_observacion)

    def test_fechas_aparentemente_iguales_convenciones_distintas(self):
        m = temporal(convencion="otra-convencion-documentada")
        r = evaluar(dimension=D.TEMPORAL, temporal=m)
        self.assertEqual(r.estado, E.PENDIENTE_DE_EVIDENCIA)
        self.assertIn("temporal.correspondencia_convencion", r.faltantes)

    def test_periodos_disjuntos_incompatibles_para_alineacion(self):
        m = temporal(fecha_observacion=None, observaciones=periodo(FECHA + timedelta(days=3), FECHA + timedelta(days=4)))
        r = evaluar(dimension=D.TEMPORAL, temporal=m)
        self.assertEqual(r.estado, E.INCOMPATIBLE)
        self.assertEqual(r.contradicciones, ())  # Son períodos distintos, no hechos falsos.

    def test_fecha_fuera_del_periodo_es_contradiccion_documental(self):
        m = temporal(fecha_observacion=FECHA - timedelta(days=1))
        r = evaluar(dimension=D.TEMPORAL, temporal=m)
        self.assertEqual(r.estado, E.INCOMPATIBLE)
        self.assertIn("r0.temporal.fecha_fuera_del_periodo_declarado", r.contradicciones)

    def test_adquisicion_y_publicacion_no_sustituyen_observaciones(self):
        m = temporal(observaciones=None, adquirido=FECHA, publicacion=periodo())
        r = evaluar(dimension=D.TEMPORAL, temporal=m)
        self.assertEqual(r.estado, E.PENDIENTE_DE_EVIDENCIA)
        self.assertIn("r0.temporal.periodo_observaciones", r.faltantes)

    def test_adquisiciones_diferentes_no_cambian_compatibilidad_observacional(self):
        m = temporal(adquirido=FECHA + timedelta(days=90), publicacion=periodo(), vigencia_metadatos=periodo())
        self.assertEqual(evaluar(dimension=D.TEMPORAL, temporal=m).estado, E.APTO_ESTRUCTURALMENTE)

    def test_naive_con_etiqueta_zona_no_se_localiza(self):
        p = periodo(FECHA.replace(tzinfo=None), (FECHA + timedelta(days=1)).replace(tzinfo=None))
        m = temporal(observaciones=p, fecha_observacion=None)
        r = evaluar(dimension=D.TEMPORAL, temporal=m)
        self.assertEqual(r.estado, E.PENDIENTE_DE_EVIDENCIA)
        self.assertIsNone(p.inicio.tzinfo)

    def test_utc_declarado_con_desplazamiento_distinto_es_contradictorio(self):
        zona = timezone(timedelta(hours=-5))
        p = periodo(FECHA.astimezone(zona), (FECHA + timedelta(days=1)).astimezone(zona))
        m = temporal(observaciones=p, fecha_observacion=None)
        r = evaluar(dimension=D.TEMPORAL, temporal=m)
        self.assertEqual(r.estado, E.INCOMPATIBLE)
        self.assertIn("r0.temporal.utc_contradice_desplazamiento", r.contradicciones)

    def test_instantes_con_zonas_explicitas_se_comparan_por_clave_absoluta(self):
        zona = timezone(timedelta(hours=-5))
        p = periodo(FECHA.astimezone(zona), (FECHA + timedelta(days=1)).astimezone(zona))
        m = temporal(observaciones=p, fecha_observacion=None, zona_horaria_declarada="UTC-05:00")
        r = evaluar(dimension=D.TEMPORAL, temporal=m)
        self.assertEqual(r.estado, E.APTO_ESTRUCTURALMENTE)
        self.assertIs(r.recursos[0].temporal.observaciones, p)

    def test_zona_textual_no_resuelta_no_se_asocia_a_offset(self):
        m = temporal(zona_horaria_declarada="Zona-Sintetica-No-Resuelta")
        r = evaluar(dimension=D.TEMPORAL, temporal=m)
        self.assertEqual(r.estado, E.PENDIENTE_DE_EVIDENCIA)

    def test_fechas_civiles_sin_convertir_a_datetime(self):
        p = periodo(date(2026, 1, 1), date(2026, 1, 2))
        m = temporal(observaciones=p, fecha_observacion=date(2026, 1, 1), resolucion="dia-civil-documentado")
        r = evaluar_aptitud(recurso(temporal=m), recurso("dos", temporal=m), D.TEMPORAL)
        self.assertEqual(r.estado, E.APTO_ESTRUCTURALMENTE)
        self.assertIs(type(r.recursos[0].temporal.observaciones.inicio), date)

    def test_inclusividad_y_limites_no_documentados(self):
        m = temporal(observaciones=periodo(limites_inclusivos=None))
        self.assertEqual(evaluar(dimension=D.TEMPORAL, temporal=m).estado, E.PENDIENTE_DE_EVIDENCIA)
        a = temporal(fecha_observacion=None, observaciones=periodo(FECHA, FECHA + timedelta(days=1), limites_inclusivos=(True, False)))
        b = temporal(fecha_observacion=None, observaciones=periodo(FECHA + timedelta(days=1), FECHA + timedelta(days=2)))
        self.assertEqual(evaluar_aptitud(recurso(temporal=a), recurso("dos", temporal=b), D.TEMPORAL).estado, E.INCOMPATIBLE)

    def test_fechas_civiles_con_limites_exclusivos_no_fingen_soporte_comun(self):
        a = temporal(fecha_observacion=None, observaciones=periodo(date(2026, 1, 1), date(2026, 1, 3), limites_inclusivos=(True, False)))
        b = temporal(fecha_observacion=None, observaciones=periodo(date(2026, 1, 2), date(2026, 1, 4), limites_inclusivos=(False, True)))
        r = evaluar_aptitud(recurso(temporal=a), recurso("dos", temporal=b), D.TEMPORAL)
        self.assertEqual(r.estado, E.INCOMPATIBLE)

    def test_incertidumbre_resolucion_e_interpretacion_insuficientes(self):
        for cambio in (dict(incertidumbre=None), dict(resolucion=None), dict(respaldo_interpretacion=DEC),
                       dict(observaciones=periodo(respaldo=DEC))):
            with self.subTest(cambio=cambio):
                self.assertEqual(evaluar(dimension=D.TEMPORAL, temporal=temporal(**cambio)).estado, E.PENDIENTE_DE_EVIDENCIA)

    def test_resoluciones_o_representaciones_no_se_agregan(self):
        self.assertEqual(evaluar(dimension=D.TEMPORAL, temporal=temporal(resolucion="otra")).estado, E.PENDIENTE_DE_EVIDENCIA)
        m = temporal(observaciones=periodo(date(2026, 1, 1), date(2026, 1, 2)), fecha_observacion=None)
        self.assertEqual(evaluar(dimension=D.TEMPORAL, temporal=m).estado, E.PENDIENTE_DE_EVIDENCIA)


class EvaluadorComunTests(unittest.TestCase):
    def test_ambas_dimensiones_y_determinismo(self):
        a, b = recurso(), recurso("dos")
        r = evaluar_aptitud(a, b)
        self.assertEqual(r.estado, E.APTO_ESTRUCTURALMENTE)
        self.assertEqual(r, evaluar_aptitud(a, b))
        self.assertEqual(r.dimension, D.AMBAS)
        self.assertEqual(r.version_evaluador, "0.1.0")

    def test_procedencia_incompleta_y_producto_desconocido(self):
        for cambio in (dict(procedencia=None), dict(procedencia=replace(PROC, evidencia=None)),
                       dict(identidad=IdentidadRecurso(Fuente("otra", "fuente"), "recurso"))):
            with self.subTest(cambio=cambio):
                self.assertEqual(evaluar(**cambio).estado, E.PENDIENTE_DE_EVIDENCIA)

    def test_instituciones_distintas_no_colisionan_ni_se_declaran_equivalentes(self):
        a = recurso()
        b = recurso(identidad=IdentidadRecurso(Fuente("otra-institucion", "misma-fuente-local"), "uno", "producto-inventado"))
        r = evaluar_aptitud(a, b)
        self.assertEqual(r.estado, E.APTO_ESTRUCTURALMENTE)
        self.assertNotEqual(r.recursos[0].identidad, r.recursos[1].identidad)
        self.assertIn("preparacion_documental_sin_asociacion_ejecutada", r.restricciones)

    def test_servidores_distintos_no_se_funden_por_ids_coincidentes(self):
        i = recurso().identidad
        a = recurso(identidad=replace(i, localizador="https://servidor-a.invalid/recurso"))
        b = recurso(identidad=replace(i, localizador="https://servidor-b.invalid/recurso"))
        r = evaluar_aptitud(a, b)
        self.assertNotEqual(a.identidad, b.identidad)
        self.assertEqual(r.estado, E.APTO_ESTRUCTURALMENTE)
        self.assertEqual(a.identidad.recurso_id, b.identidad.recurso_id)

    def test_ambas_pendiente_y_razones_no_evaluables_conservadas(self):
        a = recurso(espacial=espacial(respaldo_coordenadas=DEC))
        self.assertEqual(evaluar_aptitud(a, recurso("dos")).estado, E.PENDIENTE_DE_EVIDENCIA)
        a = recurso(espacial=None, contradicciones_declaradas=("conflicto-documental-inventado",))
        r = evaluar_aptitud(a, recurso("dos"))
        self.assertEqual(r.estado, E.INCOMPATIBLE)
        self.assertIn("r0.espacial.marco_ausente", r.motivos)

    def test_marcos_ausentes_no_evaluables_y_dimension_seleccionada(self):
        a = recurso(espacial=None)
        self.assertEqual(evaluar_aptitud(a, recurso("dos"), D.ESPACIAL).estado, E.NO_EVALUABLE)
        self.assertEqual(evaluar_aptitud(a, recurso("dos"), D.TEMPORAL).estado, E.APTO_ESTRUCTURALMENTE)
        self.assertEqual(evaluar_aptitud(a, recurso("dos")).estado, E.NO_EVALUABLE)

    def test_contradiccion_y_revision_identica_con_diferente_contenido(self):
        a = recurso()
        b = replace(a, version_institucional="otra-declaracion")
        self.assertEqual(evaluar_aptitud(a, b).estado, E.INCOMPATIBLE)
        r = evaluar(contradicciones_declaradas=("dos_documentos_de_fixture_contradictorios",))
        self.assertEqual(r.estado, E.INCOMPATIBLE)
        self.assertIn("r0.contradiccion_declarada_0", r.contradicciones)

    def test_revision_identica_no_oculta_diferencias_de_fold(self):
        from io import BytesIO
        from zoneinfo import ZoneInfo
        from test_temporal import tzif_sintetico, ZONA
        zona = ZoneInfo.from_file(BytesIO(tzif_sintetico()), key=ZONA)
        a = datetime(2020, 10, 25, 1, 30, tzinfo=zona, fold=0)
        b = datetime(2020, 10, 25, 1, 30, tzinfo=zona, fold=1)
        primero = recurso(temporal=temporal(fecha_observacion=None, observaciones=periodo(a, a), zona_horaria_declarada=ZONA))
        segundo = replace(primero, temporal=temporal(fecha_observacion=None, observaciones=periodo(b, b), zona_horaria_declarada=ZONA))
        r = evaluar_aptitud(primero, segundo, D.TEMPORAL)
        self.assertEqual(r.estado, E.INCOMPATIBLE)
        self.assertIn("misma_identidad_revision_con_instantaneas_distintas", r.contradicciones)

    def test_sin_red_sqlite_archivos_o_reloj_en_evaluacion(self):
        a, b = recurso(), recurso("dos")
        with patch("socket.socket", side_effect=AssertionError("red")), \
                patch("builtins.open", side_effect=AssertionError("archivo")), \
                patch("sqlite3.connect", side_effect=AssertionError("sqlite")), \
                patch("time.time", side_effect=AssertionError("reloj")):
            self.assertEqual(evaluar_aptitud(a, b).estado, E.APTO_ESTRUCTURALMENTE)

    def test_importacion_no_carga_cliente_y_fuente_sin_ejecucion_arbitraria(self):
        codigo = ("import sys; import spica.interoperabilidad; "
                  "assert not any(x == 'httpx' or x.startswith('spica.adquisicion.transportes') "
                  "or x.startswith('spica.adquisicion.integracion') for x in sys.modules)")
        r = subprocess.run([sys.executable, "-B", "-c", codigo], text=True, capture_output=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        raiz = Path(__file__).resolve().parents[1] / "src/spica/interoperabilidad"
        for p in raiz.glob("*.py"):
            for n in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
                    self.assertNotIn(n.func.id, ("eval", "exec", "open"))
                if isinstance(n, ast.ImportFrom):
                    self.assertFalse(any(x in (n.module or "") for x in ("transportes", "almacenamiento", "integracion", "conectores")))


if __name__ == "__main__":
    unittest.main()
