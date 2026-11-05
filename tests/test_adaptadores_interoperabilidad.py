"""Integración de contratos construidos en memoria; ningún dato institucional."""

from dataclasses import FrozenInstanceError, replace
from datetime import date, datetime, timezone
import json
from types import MappingProxyType
import unittest
from unittest.mock import patch

from spica.adquisicion.nucleo import Fuente
from spica.adquisicion.catalogo import (
    DisponibilidadCatalogo, EstacionCatalogo, EstadoVerificacion as V,
    EvidenciaDocumental, ProductoCatalogo, ProcedenciaCatalogo, RecursoCatalogo, VariableCatalogo,
)
from spica.adquisicion.consultas_locales.modelos import ObservacionLocal, ProcedenciaLocal
from spica.adquisicion.inspeccion_arcgis import (
    EstadoJSON, ObjetivoArcGIS, TipoMetadatos, inspeccionar_metadatos,
)
from spica.adquisicion.transportes import RespuestaHTTP
from spica.adquisicion.vectorial import RecursoVector
from spica.interoperabilidad import AmbitoCRS as A, DimensionEvaluacion as D, EstadoAptitud as E, evaluar_aptitud
from spica.interoperabilidad.adaptadores import (
    EstadoAdaptacion as EA, adaptar_catalogo, adaptar_meteorologia, adaptar_vectorial,
)


FECHA = datetime(2026, 1, 1, tzinfo=timezone.utc)
FUENTE = Fuente("institucion-sintetica", "fuente-inventada")
PROC = ProcedenciaCatalogo("fixture://referencia-inventada", FECHA, "fixture_sintetica", "evidencia-inventada")


def catalogo(**kw):
    d = dict(fuente=FUENTE, producto_id="producto-original", identificador="recurso-original",
             localizador="fixture://recurso-original", procedencia=PROC)
    d.update(kw)
    return RecursoCatalogo(**d)


def estacion(**kw):
    d = dict(fuente=FUENTE, producto_id="producto-original", identificador=" codigo original ",
             procedencia=PROC, nombre=" nombre literal ", coordenada_x=1.0, coordenada_y=2.0,
             sistema_referencia="CRS-SINTETICO")
    d.update(kw)
    return EstacionCatalogo(**d)


def disponibilidad(**kw):
    d = dict(identificador="id-disponibilidad-no-serie", fuente=FUENTE, producto_id="producto-original",
             procedencia=PROC, estacion_id=" codigo original ", variable_id="variable-interna",
             inicio=datetime(2026, 1, 1), fin=datetime(2026, 1, 2), precision_temporal="dia-civil-documentado",
             frecuencia_declarada="frecuencia-textual", estado=V.DECLARADO)
    d.update(kw)
    return DisponibilidadCatalogo(**d)


def variable(**kw):
    d = dict(id_interno="variable-interna", fuente=FUENTE, producto_id="producto-original",
             procedencia=PROC, codigo_original="VARIABLE_ORIGINAL")
    d.update(kw)
    return VariableCatalogo(**d)


def observacion(**kw):
    d = dict(procedencia=ProcedenciaLocal(FUENTE, "recurso-original", "activo-sintetico"),
             numero_registro=2, linea_inicial=2, linea_final=2,
             campos_originales=(("ESTACION", " nombre literal "), ("FECHA", "20260101"), ("HORA", "10000"),
                                ("LONGITUD", "01.000"), ("LATITUD", "02.000"), ("UBIGEO", "12345.0")),
             variable="VARIABLE_ORIGINAL", valor="1.00", presente=True, fecha_civil=date(2026, 1, 1))
    d.update(kw)
    return ObservacionLocal(**d)


def meteorologia(**kw):
    d = dict(revision_metadatos="revision-local-1", estacion=estacion(), disponibilidad=disponibilidad(),
             variable=variable(), observacion=observacion())
    d.update(kw)
    return adaptar_meteorologia(catalogo(), **d)


def vector():
    url = "https://vector-sintetico.invalid/arcgis/rest/services/SERVICIO_SINTETICO/MapServer"
    obj = ObjetivoArcGIS(url, url + "/17", "SERVICIO_SINTETICO", 17, "Capa sintetica",
                       123456789, 123456790, ("oid_sintetico",))
    d = dict(id=17, name="Capa sintetica", type="Feature Layer", geometryType="esriGeometryPolygon",
             spatialReference=dict(wkid=123456790, latestWkid=123456790),
             sourceSpatialReference=dict(wkid=123456791),
             extent=dict(xmin=0, ymin=0, xmax=10, ymax=20,
                         spatialReference=dict(wkid=123456789, latestWkid=123456790)),
             fields=[dict(name="oid_sintetico", type="esriFieldTypeOID")],
             currentVersion=10.9, maxRecordCount=2, supportedQueryFormats="JSON", capabilities="Query")
    respuesta = RespuestaHTTP(200, {"content-type": "application/json"}, json.dumps(d).encode())
    meta = inspeccionar_metadatos(respuesta, TipoMetadatos.CAPA, obj)
    rec = RecursoVector(Fuente("institucion-vectorial-sintetica", "fuente-vectorial"),
                        "producto-vectorial", "recurso-vectorial", "SERVICIO_SINTETICO", 17, PROC)
    return rec, meta


class AdaptadorCatalogoTests(unittest.TestCase):
    def test_identidad_producto_procedencia_y_revision_exactos(self):
        c = catalogo(identificador=" recurso original ", producto_id=" Producto ")
        p = ProductoCatalogo(FUENTE, " Producto ", PROC, version="edicion-de-fixture", restricciones_licencia="terminos-fixture")
        r = adaptar_catalogo(c, revision_metadatos=" revision local ", producto=p)
        self.assertEqual(r.estado, EA.PARCIAL)
        self.assertEqual(r.recurso.identidad.recurso_id, " recurso original ")
        self.assertEqual(r.recurso.identidad.producto_id, " Producto ")
        self.assertEqual(r.recurso.version_institucional, "edicion-de-fixture")
        self.assertEqual(r.recurso.revision_metadatos, " revision local ")
        self.assertIs(r.recurso.procedencia, PROC)
        self.assertIsNone(r.recurso.temporal)
        self.assertIsNone(r.recurso.espacial)

    def test_estado_verificado_documental_no_verifica_coordenadas(self):
        doc = EvidenciaDocumental(FUENTE, "recurso-original", "producto-original", descubierta_utc=FECHA,
                                 estado=V.VERIFICADO, procedencia=PROC)
        r = adaptar_catalogo(catalogo(), revision_metadatos="r1", documento=doc)
        self.assertEqual(r.originales["documento"]["estado"], V.VERIFICADO.value)
        self.assertIsNone(r.recurso.espacial)
        self.assertIsNone(r.recurso.temporal)

    def test_producto_y_documento_de_otro_ambito_no_se_mezclan(self):
        p = ProductoCatalogo(Fuente("otra", "fuente"), "producto-original", PROC)
        r = adaptar_catalogo(catalogo(), revision_metadatos="r1", producto=p)
        self.assertEqual(r.estado, EA.CONTRADICTORIO)
        self.assertEqual(r.recurso.identidad.fuente, FUENTE)
        self.assertTrue(r.recurso.contradicciones_declaradas)
        doc = EvidenciaDocumental(FUENTE, "otro-recurso", "producto-original", procedencia=PROC)
        self.assertEqual(adaptar_catalogo(catalogo(), revision_metadatos="r1", documento=doc).estado, EA.CONTRADICTORIO)

    def test_terminos_distintos_sin_inventar_equivalencia_o_prohibicion(self):
        c = catalogo(licencia_declarada="termino-A")
        doc = EvidenciaDocumental(FUENTE, c.identificador, c.producto_id, licencia_declarada="termino-B", procedencia=PROC)
        r = adaptar_catalogo(c, revision_metadatos="r1", documento=doc)
        self.assertEqual(r.recurso.condiciones_uso, "termino-A")
        self.assertIn("terminos_distintos_requieren_aclaracion_de_alcance", [d.codigo for d in r.diagnosticos])
        self.assertEqual(r.originales["documento"]["licencia_declarada"], "termino-B")


class AdaptadorMeteorologicoTests(unittest.TestCase):
    def test_estacion_variable_originales_y_desconocidos_preservados(self):
        r = meteorologia()
        self.assertEqual(r.estado, EA.PARCIAL)
        self.assertEqual(r.recurso.espacial.identificador_ubicacion, " codigo original ")
        self.assertEqual(r.recurso.atributos_declarados, ("VARIABLE_ORIGINAL",))
        self.assertEqual(r.recurso.espacial.coordenadas, (1.0, 2.0))
        self.assertEqual(r.recurso.espacial.respaldo_coordenadas.estado, V.DECLARADO)
        t = r.recurso.temporal
        self.assertEqual(dict(t.valores_originales)["HORA"], "10000")
        self.assertEqual(dict(t.valores_originales)["UBIGEO"], "12345.0")
        self.assertIsNone(t.zona_horaria_declarada)
        self.assertIsNone(t.convencion)
        self.assertIsNone(t.observaciones.inicio.tzinfo)
        self.assertIsNone(t.observaciones.limites_inclusivos)
        self.assertIsNone(t.publicacion)
        self.assertIsNone(t.adquirido)
        self.assertEqual(r.originales["disponibilidad"]["identificador"], "id-disponibilidad-no-serie")

    def test_coordenadas_ausentes_no_se_geocodifican_por_nombre(self):
        r = meteorologia(estacion=estacion(coordenada_x=None, coordenada_y=None))
        self.assertIsNone(r.recurso.espacial.coordenadas)
        self.assertIn("coordenadas_ausentes", [d.codigo for d in r.diagnosticos])
        self.assertEqual(r.recurso.espacial.ubicacion_declarada[0][1], " nombre literal ")

    def test_sin_estacion_sin_periodo_no_se_inventan(self):
        r = meteorologia(estacion=None, disponibilidad=None)
        self.assertIsNone(r.recurso.espacial.identificador_ubicacion)
        self.assertIsNone(r.recurso.espacial.coordenadas)
        self.assertIsNone(r.recurso.temporal.observaciones)
        self.assertTrue(r.recurso.espacial.identidad_ambigua)
        self.assertIsNone(r.recurso.temporal.zona_horaria_declarada)

    def test_no_se_equiparan_fuentes_o_estaciones_distintas(self):
        for cambios in (dict(estacion=estacion(fuente=Fuente("otra-institucion", "fuente-inventada"))),
                        dict(disponibilidad=disponibilidad(estacion_id="otro-codigo")),
                        dict(disponibilidad=disponibilidad(variable_id="otra-variable")),
                        dict(observacion=observacion(procedencia=ProcedenciaLocal(FUENTE, "otro-recurso", "activo")))):
            with self.subTest(cambios=cambios):
                r = meteorologia(**cambios)
                self.assertEqual(r.estado, EA.CONTRADICTORIO)
                self.assertIsNone(r.recurso.espacial)

    def test_codigo_variable_no_coincidente_es_contradiccion(self):
        r = meteorologia(variable=variable(codigo_original="OTRA_VARIABLE"))
        self.assertEqual(r.estado, EA.CONTRADICTORIO)
        self.assertIn("codigo_variable_contradictorio", [d.codigo for d in r.diagnosticos])

    def test_periodo_verificado_no_promueve_interpretacion_o_zona(self):
        dis = disponibilidad(estado=V.VERIFICADO, comprobada_utc=FECHA,
                             inicio=FECHA, fin=FECHA, zona_horaria=None)
        r = meteorologia(disponibilidad=dis)
        self.assertEqual(r.recurso.temporal.observaciones.respaldo.estado, V.VERIFICADO)
        self.assertEqual(r.recurso.temporal.respaldo_interpretacion.estado, V.DECLARADO)
        self.assertIsNone(r.recurso.temporal.zona_horaria_declarada)
        self.assertEqual(r.recurso.temporal.resolucion, dis.precision_temporal)

    def test_fecha_imposible_en_objeto_debil_no_se_interpreta(self):
        o = observacion(fecha_civil="20260230", campos_originales=(("FECHA", "20260230"), ("HORA", "10000")))
        r = meteorologia(observacion=o)
        self.assertEqual(r.estado, EA.NO_REPRESENTABLE)
        self.assertIsNone(r.recurso)
        self.assertEqual(r.originales["observacion"]["fecha_civil"], "20260230")


class AdaptadorVectorialTests(unittest.TestCase):
    def test_ambitos_crs_atributos_y_version_tecnica_no_promovidos(self):
        rec, meta = vector()
        r = adaptar_vectorial(rec, meta, revision_metadatos="revision-local-1")
        self.assertEqual(r.estado, EA.PARCIAL)
        self.assertEqual(r.recurso.identidad.localizador, meta.objetivo.url_capa)
        self.assertEqual(r.recurso.atributos_declarados, ("oid_sintetico",))
        crs = {c.ambito: c for c in r.recurso.espacial.crs}
        self.assertNotEqual(crs[A.GEOMETRIA].declaracion, crs[A.EXTENSION].declaracion)
        self.assertEqual(crs[A.ORIGEN].declaracion.wkid, 123456791)
        self.assertEqual(r.recurso.espacial.extension, (0, 0, 10, 20))
        self.assertIsNone(r.recurso.espacial.cobertura_observada)
        self.assertIsNone(r.recurso.espacial.precision_declarada)
        self.assertIsNone(r.recurso.version_institucional)
        self.assertEqual(r.originales["metadatos"]["datos"]["currentVersion"], 10.9)
        self.assertEqual(crs[A.GEOMETRIA].respaldo.estado, V.DECLARADO)
        self.assertEqual(crs[A.GEOMETRIA].unidades_ejes, ())

    def test_crs_extension_o_fuente_no_se_usan_como_geometria_ausente(self):
        rec, meta = vector()
        d = dict(meta.datos); del d["spatialReference"]
        r = adaptar_vectorial(rec, replace(meta, datos=d), revision_metadatos="r1")
        self.assertNotIn(A.GEOMETRIA, {c.ambito for c in r.recurso.espacial.crs})
        self.assertIn(A.EXTENSION, {c.ambito for c in r.recurso.espacial.crs})

    def test_capa_servicio_y_host_contradictorios_bloquean(self):
        rec, meta = vector()
        cambios = (dict(id=18), dict(name="Otra capa"))
        for cambio in cambios:
            with self.subTest(cambio=cambio):
                r = adaptar_vectorial(rec, replace(meta, datos=dict(meta.datos) | cambio), revision_metadatos="r1")
                self.assertEqual(r.estado, EA.CONTRADICTORIO)
        c = RecursoCatalogo(rec.fuente, rec.producto_id, rec.recurso_id, "https://otro-host.invalid/capa", PROC)
        self.assertEqual(adaptar_vectorial(rec, meta, revision_metadatos="r1", catalogo=c).estado, EA.CONTRADICTORIO)
        self.assertEqual(adaptar_vectorial(replace(rec, servicio_id="OTRO"), meta, revision_metadatos="r1").estado, EA.CONTRADICTORIO)

    def test_inspeccion_parcial_y_extension_invalida_no_representables(self):
        rec, meta = vector()
        self.assertEqual(adaptar_vectorial(rec, replace(meta, estado_json=EstadoJSON.PARCIAL), revision_metadatos="r1").estado, EA.NO_REPRESENTABLE)
        d = dict(meta.datos); d["extent"] = dict(xmin=5, ymin=0, xmax=1, ymax=2)
        self.assertEqual(adaptar_vectorial(rec, replace(meta, datos=d), revision_metadatos="r1").estado, EA.NO_REPRESENTABLE)

    def test_coherencia_negativa_no_se_rebaja_a_dato_desconocido(self):
        rec, meta = vector()
        r = adaptar_vectorial(rec, replace(meta, coherencia_servicio_capa=False), revision_metadatos="r1")
        self.assertEqual(r.estado, EA.CONTRADICTORIO)
        self.assertTrue(r.recurso.contradicciones_declaradas)
        self.assertIs(r.originales["metadatos"]["coherencia_servicio_capa"], False)
        self.assertEqual(evaluar_aptitud(r.recurso, r.recurso, D.ESPACIAL).estado, E.INCOMPATIBLE)

    def test_snapshot_profundo_no_depende_de_mutaciones_del_origen(self):
        rec, meta = vector()
        datos = dict(meta.datos)
        datos["fields"] = [dict(name="oid_sintetico", type="esriFieldTypeOID")]
        debil = replace(meta, datos=MappingProxyType(datos))
        r = adaptar_vectorial(rec, debil, revision_metadatos="r1")
        datos["fields"][0]["name"] = "cambiado-despues"
        self.assertEqual(r.originales["metadatos"]["datos"]["fields"][0]["name"], "oid_sintetico")
        self.assertEqual(r.recurso.atributos_declarados, ("oid_sintetico",))
        with self.assertRaises(TypeError):
            r.originales["metadatos"]["datos"]["fields"][0]["name"] = "otro"
        with self.assertRaises(FrozenInstanceError):
            r.estado = EA.DESCRITO

    def test_snapshot_fuera_de_limite_no_trunca_silenciosamente(self):
        rec, meta = vector()
        r = adaptar_vectorial(rec, replace(meta, datos={"texto": "x" * 65_537}), revision_metadatos="r1")
        self.assertEqual(r.estado, EA.NO_REPRESENTABLE)
        self.assertEqual(dict(r.originales), {})


class SeguridadAdaptadoresTests(unittest.TestCase):
    def test_adaptacion_no_usa_red_sqlite_o_archivos(self):
        rec, meta = vector()
        c, e, dis, v, o = catalogo(), estacion(), disponibilidad(), variable(), observacion()
        with patch("socket.socket", side_effect=AssertionError("red")), \
                patch("sqlite3.connect", side_effect=AssertionError("sqlite")), \
                patch("builtins.open", side_effect=AssertionError("archivo")):
            self.assertEqual(adaptar_catalogo(c, revision_metadatos="r1").estado, EA.PARCIAL)
            self.assertEqual(adaptar_meteorologia(c, revision_metadatos="r1", estacion=e,
                             disponibilidad=dis, variable=v, observacion=o).estado, EA.PARCIAL)
            self.assertEqual(adaptar_vectorial(rec, meta, revision_metadatos="r1").estado, EA.PARCIAL)


if __name__ == "__main__":
    unittest.main()
