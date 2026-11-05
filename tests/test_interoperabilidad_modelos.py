"""Contratos de preparación con evidencia exclusivamente inventada."""

from dataclasses import FrozenInstanceError, replace
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import unittest

from spica.adquisicion.catalogo.modelos import EstadoVerificacion as V, ProcedenciaCatalogo
from spica.adquisicion.nucleo import Fuente
from spica.adquisicion.vectorial import ReferenciaEspacial
from spica.interoperabilidad import (
    AmbitoCRS as A, CRSDeclarado, DimensionEvaluacion as D, EstadoAptitud as E,
    IdentidadRecurso, MarcoEspacial, MarcoTemporal, PeriodoTemporal,
    RecursoInteroperable, RepresentacionEspacial as R, Respaldo, evaluar_aptitud,
)


FECHA = datetime(2026, 1, 1, tzinfo=timezone.utc)
PROC = ProcedenciaCatalogo("fixture://documento-inventado", FECHA, "revision_sintetica", "evidencia-inventada")
VER = Respaldo(V.VERIFICADO, PROC)
DEC = Respaldo(V.DECLARADO, PROC)


def crs(ambito=A.GEOMETRIA, **kw):
    d = dict(ambito=ambito, declaracion="CRS-SINTETICO-XY", definicion="fixture://definicion-inventada",
             unidades_ejes=("m", "m"), respaldo=VER)
    d.update(kw)
    return CRSDeclarado(**d)


def espacial(**kw):
    d = dict(representacion=R.PUNTUAL, coordenadas=(Decimal("1.00000000000000000001"), Decimal("2")),
             respaldo_coordenadas=VER, crs=(crs(),), cobertura_observada="cobertura-inventada",
             respaldo_cobertura=VER, precision_declarada="precision-documentada-en-fixture",
             incertidumbre="incertidumbre-documentada-en-fixture", respaldo_calidad=VER)
    d.update(kw)
    return MarcoEspacial(**d)


def periodo(inicio=FECHA, fin=FECHA + timedelta(days=1), **kw):
    d = dict(inicio=inicio, fin=fin, respaldo=VER, limites_inclusivos=(True, True))
    d.update(kw)
    return PeriodoTemporal(**d)


def temporal(**kw):
    d = dict(valores_originales=(("FECHA", "20260101"), ("HORA", "000000")),
             fecha_observacion=FECHA, resolucion="instante-documentado-en-fixture",
             zona_horaria_declarada="UTC", convencion="convencion-sintetica-1",
             observaciones=periodo(), incertidumbre="incertidumbre-temporal-en-fixture",
             respaldo_interpretacion=VER)
    d.update(kw)
    return MarcoTemporal(**d)


def recurso(nombre="uno", **kw):
    d = dict(identidad=IdentidadRecurso(Fuente("institucion-sintetica", "fuente-inventada"), nombre, "producto-inventado"),
             revision_metadatos="revision-local-1", procedencia=PROC, espacial=espacial(), temporal=temporal())
    d.update(kw)
    return RecursoInteroperable(**d)


class ModelosInteroperabilidadTests(unittest.TestCase):
    def test_identificadores_y_originales_no_se_normalizan(self):
        i = IdentidadRecurso(Fuente(" fuente ", "ID-original"), " recurso ", " Producto ")
        m = MarcoEspacial(ubicacion_declarada=(("ESTACION", " Estación "), ("UBIGEO", "12345.0")))
        t = MarcoTemporal(valores_originales=(("FECHA", "20260101"), ("HORA", "10000")))
        self.assertEqual(i.recurso_id, " recurso ")
        self.assertEqual(i.producto_id, " Producto ")
        self.assertEqual(m.ubicacion_declarada[1][1], "12345.0")
        self.assertEqual(t.valores_originales[1][1], "10000")
        self.assertIsNone(m.coordenadas)
        self.assertIsNone(t.fecha_observacion)
        self.assertIsNone(t.zona_horaria_declarada)

    def test_verificado_necesita_procedencia_y_evidencia(self):
        sin_evidencia = replace(PROC, evidencia=None)
        for p in (None, sin_evidencia):
            with self.subTest(p=p), self.assertRaises(ValueError):
                Respaldo(V.VERIFICADO, p)
        self.assertEqual(Respaldo(V.DECLARADO, sin_evidencia).estado, V.DECLARADO)

    def test_inmutabilidad_profunda_sin_listas_o_mapas_mutables(self):
        r = recurso()
        with self.assertRaises(FrozenInstanceError):
            r.espacial.coordenadas = (3, 4)
        with self.assertRaises(TypeError):
            MarcoTemporal(valores_originales=[("HORA", "10000")])
        with self.assertRaises(TypeError):
            espacial(coordenadas=[1, 2])
        with self.assertRaises(TypeError):
            espacial(crs=[crs()])
        with self.assertRaises(ValueError):
            MarcoTemporal(valores_originales=(("HORA", "1"), ("HORA", "2")))

    def test_coordenadas_finitas_sin_conversion_ni_redondeo(self):
        m = espacial()
        self.assertIs(type(m.coordenadas[0]), Decimal)
        self.assertEqual(str(m.coordenadas[0]), "1.00000000000000000001")
        for x in (True, "1", float("nan"), float("inf"), Decimal("NaN")):
            with self.subTest(x=x), self.assertRaises((TypeError, ValueError)):
                espacial(coordenadas=(x, 2))

    def test_coordenadas_y_extension_ausentes_no_verificadas(self):
        with self.assertRaises(ValueError):
            espacial(coordenadas=None)
        with self.assertRaises(ValueError):
            MarcoEspacial(respaldo_extension=VER)
        m = MarcoEspacial()
        self.assertEqual(m.respaldo_coordenadas.estado, V.DESCONOCIDO)
        self.assertIsNone(m.coordenadas)

    def test_crs_ambitos_originales_y_unidades(self):
        ref = ReferenciaEspacial(102100, 3857)
        c = crs(declaracion=ref)
        self.assertIs(c.declaracion, ref)
        self.assertEqual(c.declaracion.declaracion(), {"wkid": 102100, "latestWkid": 3857})
        with self.assertRaises(ValueError):
            espacial(crs=(crs(), crs()))
        with self.assertRaises(ValueError):
            CRSDeclarado(A.GEOMETRIA, respaldo=VER)
        with self.assertRaises(ValueError):
            crs(unidades_ejes=("m",))

    def test_extension_ordenada_no_calcula_area_o_interseccion(self):
        self.assertEqual(espacial(extension=(0, 0, 2, 3), respaldo_extension=VER).extension, (0, 0, 2, 3))
        with self.assertRaises(ValueError):
            espacial(extension=(2, 0, 1, 3))

    def test_periodos_civiles_y_absolutos_se_conservan(self):
        civil = periodo(date(2026, 1, 1), date(2026, 1, 2))
        self.assertIs(type(civil.inicio), date)
        zona = timezone(timedelta(hours=-5))
        inicio = datetime(2026, 1, 1, 9, tzinfo=zona)
        p = periodo(inicio, inicio + timedelta(hours=1))
        self.assertIs(p.inicio, inicio)
        self.assertEqual(p.inicio.utcoffset(), timedelta(hours=-5))

    def test_extremos_invertidos_mixtos_y_vacios_rechazados(self):
        for inicio, fin in ((FECHA + timedelta(days=1), FECHA),
                            (FECHA, FECHA.replace(tzinfo=None)), (date(2026, 1, 1), FECHA)):
            with self.subTest(inicio=inicio, fin=fin), self.assertRaises((ValueError, TypeError)):
                periodo(inicio, fin)
        with self.assertRaises(ValueError):
            periodo(FECHA, FECHA, limites_inclusivos=(True, False))

    def test_folds_distintos_no_son_periodo_puntual_vacio(self):
        from io import BytesIO
        from zoneinfo import ZoneInfo
        from test_temporal import tzif_sintetico, ZONA
        zona = ZoneInfo.from_file(BytesIO(tzif_sintetico()), key=ZONA)
        a = datetime(2020, 10, 25, 1, 30, tzinfo=zona, fold=0)
        b = datetime(2020, 10, 25, 1, 30, tzinfo=zona, fold=1)
        self.assertEqual(a, b)  # Limitación conocida de Python, no criterio SUADC.
        p = periodo(a, b, limites_inclusivos=(True, False))
        self.assertEqual(p.inicio.fold, 0)
        self.assertEqual(p.fin.fold, 1)

    def test_periodo_civil_abierto_sin_fechas_rechazado(self):
        with self.assertRaisesRegex(ValueError, "sin_fechas"):
            periodo(date(2026, 1, 1), date(2026, 1, 2), limites_inclusivos=(False, False))

    def test_limites_de_evidencia_con_correspondencias_acotadas(self):
        correspondencias = tuple(replace(PROC, referencia=f"fixture://correspondencia-{i}") for i in range(16))
        r = evaluar_aptitud(recurso(correspondencias=correspondencias), recurso("dos", correspondencias=correspondencias))
        self.assertEqual(r.estado, E.APTO_ESTRUCTURALMENTE)
        with self.assertRaises(TypeError):
            recurso(correspondencias=correspondencias + (PROC,))

    def test_fecha_naive_no_recibe_zona_y_adquisicion_necesita_instante(self):
        naive = datetime(2026, 1, 1, 9)
        m = MarcoTemporal(fecha_observacion=naive)
        self.assertIsNone(m.fecha_observacion.tzinfo)
        self.assertIsNone(m.zona_horaria_declarada)
        with self.assertRaises(ValueError):
            MarcoTemporal(adquirido=naive)

    def test_ambitos_temporales_independientes(self):
        obs = periodo()
        pub = periodo(FECHA + timedelta(days=30), FECHA + timedelta(days=31))
        adquirido = FECHA + timedelta(days=60)
        vigencia = periodo(FECHA + timedelta(days=90), FECHA + timedelta(days=91))
        m = temporal(observaciones=obs, publicacion=pub, adquirido=adquirido, vigencia_metadatos=vigencia)
        self.assertIs(m.observaciones, obs)
        self.assertIs(m.publicacion, pub)
        self.assertIs(m.adquirido, adquirido)
        self.assertIs(m.vigencia_metadatos, vigencia)

    def test_actualizar_instantanea_preserva_resultado_y_revision_anteriores(self):
        original = recurso(espacial=espacial(respaldo_coordenadas=DEC))
        anterior = evaluar_aptitud(original, recurso("dos"), D.ESPACIAL)
        nueva = replace(original, revision_metadatos="revision-local-2", sustituye_revision="revision-local-1",
                        espacial=espacial(), procedencia=replace(PROC, revisada_utc=FECHA + timedelta(days=1)))
        actual = evaluar_aptitud(nueva, recurso("dos"), D.ESPACIAL)
        self.assertEqual(anterior.estado, E.PENDIENTE_DE_EVIDENCIA)
        self.assertEqual(actual.estado, E.APTO_ESTRUCTURALMENTE)
        self.assertIs(anterior.recursos[0], original)
        self.assertEqual(original.revision_metadatos, "revision-local-1")
        self.assertEqual(nueva.sustituye_revision, "revision-local-1")
        with self.assertRaises(ValueError):
            replace(nueva, sustituye_revision="revision-local-2")

    def test_modelos_anteriores_siguen_sin_exigir_nuevos_metadatos(self):
        from spica.adquisicion.catalogo.modelos import EstacionCatalogo
        estacion = EstacionCatalogo(Fuente("institucion-inventada", "fuente"), "producto", "codigo original ", PROC,
                                   coordenada_x=1, coordenada_y=2)
        self.assertIsNone(estacion.sistema_referencia)
        self.assertEqual(estacion.identificador, "codigo original ")
        self.assertEqual(ReferenciaEspacial(4326).declaracion(), {"wkid": 4326})


if __name__ == "__main__":
    unittest.main()
