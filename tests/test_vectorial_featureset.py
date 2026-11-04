"""PASO 83-A: todos los identificadores, polígonos y metadatos son inventados."""

from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import sys
from threading import Event
from types import MappingProxyType
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from spica.adquisicion.nucleo import Fuente
from spica.adquisicion.catalogo import ProcedenciaCatalogo
from spica.adquisicion.vectorial import (
    CampoVector, ConsultaVector, ContratoFeatureSet, EstadoGeometria, EstadoPagina,
    EvidenciaConjunto, LimitesVector, RecursoVector, ReferenciaEspacial,
    RespuestaSintetica, TipoCampo, validar_featureset,
)


FECHA = datetime(2026, 11, 4, tzinfo=timezone.utc)


def contrato():
    return ContratoFeatureSet((CampoVector("oid", TipoCampo.OID),
                              CampoVector("texto", TipoCampo.TEXTO, nullable=True),
                              CampoVector("valor", TipoCampo.REAL)), "oid", ReferenciaEspacial(4326))


def consulta(**kw):
    r = RecursoVector(Fuente("INSTITUCION_SINTETICA", "fuente-inventada"), "producto-inventado",
                       "recurso-inventado", "servicio-inventado", 3,
                       ProcedenciaCatalogo("fixture-sintetica", FECHA, "invencion_controlada"))
    return ConsultaVector("adquisicion-sintetica", "consulta-sintetica", r, contrato(),
                          {"f": "json", "where": "1=1", "outFields": "*"}, FECHA, **kw)


def featureset(ids=(1,), *, exceso=False):
    return {"geometryType": "esriGeometryPolygon", "objectIdFieldName": "oid",
            "spatialReference": {"wkid": 4326},
            "fields": [{"name": c.nombre, "type": c.tipo.value, "nullable": c.nullable} for c in contrato().campos],
            "features": [{"attributes": {"oid": i, "texto": " A Ω ", "valor": 1.25},
                          "geometry": {"rings": [[[0, 0], [1, 0], [0, 1], [0, 0]]]}} for i in ids],
            "exceededTransferLimit": exceso}


def respuesta(d=None, *, numero=1, **kw):
    if d is None:
        d = featureset()
    cuerpo = d if type(d) is bytes else json.dumps(d, ensure_ascii=False, separators=(",", ":")).encode()
    return RespuestaSintetica("respuesta-" + str(numero), FECHA + timedelta(seconds=numero), cuerpo, **kw)


class FeatureSetTests(unittest.TestCase):
    def validar(self, d=None, **kw):
        return validar_featureset(respuesta(d), contrato(), **kw)

    def rechazar(self, d, codigo, **kw):
        r = self.validar(d, **kw)
        self.assertNotEqual(r.estado, EstadoPagina.VALIDA)
        self.assertIn(codigo, r.diagnosticos)
        self.assertEqual(r.entidades, ())
        self.assertIsNone(r.referencia_declarada)
        return r

    def test_featureset_poligono_simple_valido(self):
        r = self.validar()
        self.assertEqual(r.estado, EstadoPagina.VALIDA)
        self.assertEqual(r.coordenadas, 4)
        self.assertEqual(r.entidades[0].object_id_observado, 1)
        self.assertIsNone(r.entidades[0].identidad_logica)

    def test_conserva_orden_atributos_y_tipos(self):
        d = featureset()
        d["features"][0]["attributes"]["valor"] = 2
        r = self.validar(d)
        e = r.entidades[0]
        self.assertEqual(tuple(e.atributos), ("oid", "texto", "valor"))
        self.assertEqual(e.atributos["texto"], " A Ω ")
        self.assertIs(type(e.atributos["valor"]), int)
        self.assertEqual(e.geometria["rings"][0], ((0, 0), (1, 0), (0, 1), (0, 0)))

    def test_multiples_anillos_no_se_reordenan(self):
        d = featureset()
        ring = [[.1, .1], [.1, .2], [.2, .1], [.1, .1]]
        d["features"][0]["geometry"]["rings"].append(ring)
        r = self.validar(d)
        self.assertEqual(r.estado, EstadoPagina.VALIDA)
        self.assertEqual(r.coordenadas, 8)
        self.assertEqual(r.entidades[0].geometria["rings"][1], tuple(map(tuple, ring)))

    def test_geometria_nula(self):
        d = featureset()
        d["features"][0]["geometry"] = None
        r = self.validar(d)
        self.assertEqual(r.estado, EstadoPagina.VALIDA)
        self.assertEqual(r.entidades[0].estado_geometria, EstadoGeometria.NULA)
        self.assertIsNone(r.entidades[0].geometria)

    def test_geometria_ausente_difiere_de_nula(self):
        d = featureset()
        del d["features"][0]["geometry"]
        self.assertEqual(self.validar(d).entidades[0].estado_geometria, EstadoGeometria.AUSENTE)

    def test_geometria_con_crs_exacto_conservado(self):
        d = featureset()
        d["features"][0]["geometry"]["spatialReference"] = {"wkid": 4326}
        r = self.validar(d)
        self.assertEqual(dict(r.referencia_declarada), {"wkid": 4326})
        self.assertEqual(dict(r.entidades[0].geometria["spatialReference"]), {"wkid": 4326})

    def test_crs_latest_conservado_sin_inferir_equivalencias(self):
        c = replace(contrato(), referencia=ReferenciaEspacial(102100, 3857))
        d = featureset()
        d["spatialReference"] = {"wkid": 102100, "latestWkid": 3857}
        r = validar_featureset(respuesta(d), c)
        self.assertEqual(dict(r.referencia_declarada), d["spatialReference"])
        d["spatialReference"] = {"wkid": 3857}
        self.assertIn("crs_no_coincide_con_contrato", validar_featureset(respuesta(d), c).diagnosticos)

    def test_crs_ausente_distinto_o_booleano_rechazado(self):
        for crs in (None, {"wkid": 3857}, {"wkid": True}, {"wkid": 4326.0}):
            with self.subTest(crs=crs):
                d = featureset()
                d["spatialReference"] = crs
                self.assertNotEqual(self.validar(d).estado, EstadoPagina.VALIDA)

    def test_crs_geometria_contradictorio(self):
        d = featureset()
        d["features"][0]["geometry"]["spatialReference"] = {"wkid": 3857}
        self.rechazar(d, "crs_no_coincide_con_contrato")

    def test_coordenadas_invalidas(self):
        for p in ([True, 1], ["0", 1], [0], [0, 1, 2], None, {}):
            with self.subTest(p=p):
                d = featureset()
                d["features"][0]["geometry"]["rings"][0][1] = p
                self.assertNotEqual(self.validar(d).estado, EstadoPagina.VALIDA)

    def test_no_finitos_y_desborde(self):
        cuerpo = respuesta().contenido
        for token in (b"NaN", b"Infinity", b"-Infinity", b"1e999"):
            self.rechazar(cuerpo.replace(b"1.25", token), "json_numero_no_finito")

    def test_anillo_abierto_no_se_repara(self):
        d = featureset()
        d["features"][0]["geometry"]["rings"][0][-1] = [2, 2]
        self.rechazar(d, "anillo_no_cerrado")
        self.assertEqual(d["features"][0]["geometry"]["rings"][0][-1], [2, 2])

    def test_anillos_vacios_cortos_o_forma_invalida(self):
        for rings in ([], {}, None, [[[0, 0]] * 3]):
            d = featureset()
            d["features"][0]["geometry"]["rings"] = rings
            self.assertNotEqual(self.validar(d).estado, EstadoPagina.VALIDA)

    def test_estructura_no_certifica_topologia(self):
        d = featureset()
        # Cruce deliberado, sin validez topológica: solo estructura XY cerrada.
        d["features"][0]["geometry"]["rings"] = [[[0, 0], [1, 1], [1, 0], [0, 1], [0, 0]]]
        self.assertEqual(self.validar(d).estado, EstadoPagina.VALIDA)

    def test_curvas_z_y_m_no_admitidos(self):
        d = featureset()
        d["features"][0]["geometry"] = {"curveRings": []}
        self.rechazar(d, "geometria_no_admitida")
        for k in ("hasZ", "hasM"):
            d = featureset()
            d[k] = True
            self.rechazar(d, "dimensiones_no_admitidas")

    def test_tipo_geometria_incorrecto(self):
        d = featureset()
        d["geometryType"] = "esriGeometryPoint"
        self.rechazar(d, "tipo_geometria_contradictorio")

    def test_no_interpreta_coordenadas_cuantizadas(self):
        d = featureset()
        d["transform"] = {"scale": [1, 1], "translate": [0, 0]}
        self.rechazar(d, "cuantizacion_no_admitida")

    def test_fields_distintos_y_duplicados(self):
        for cambio in ("tipo", "duplicado", "ausente", "nullable"):
            d = featureset()
            if cambio == "tipo":
                d["fields"][0]["type"] = "esriFieldTypeString"
            elif cambio == "duplicado":
                d["fields"][1] = d["fields"][0]
            elif cambio == "ausente":
                del d["fields"]
            else:
                d["fields"][0]["nullable"] = True
            self.assertNotEqual(self.validar(d).estado, EstadoPagina.VALIDA)

    def test_atributos_ausentes_nulos_extra_o_tipo_invalido(self):
        for a in (None, [], {"oid": 1}, {"oid": 1, "texto": "x", "valor": True},
                  {"oid": 1, "texto": "x", "valor": {}}, {"oid": 1, "texto": 4, "valor": 1},
                  {"oid": 1, "texto": "x", "valor": 1, "extra": 2}):
            d = featureset()
            d["features"][0]["attributes"] = a
            self.assertNotEqual(self.validar(d).estado, EstadoPagina.VALIDA)

    def test_nullable_conserva_null_sin_rellenar_ausencias(self):
        d = featureset()
        d["features"][0]["attributes"]["texto"] = None
        self.assertIsNone(self.validar(d).entidades[0].atributos["texto"])
        del d["features"][0]["attributes"]["texto"]
        self.rechazar(d, "atributos_distintos_del_contrato")

    def test_oid_ausente_nulo_duplicado_y_booleano(self):
        d = featureset((1, 1))
        self.rechazar(d, "oid_duplicado_en_pagina")
        for v in (None, True, "1", -1, 1.0):
            d = featureset()
            d["features"][0]["attributes"]["oid"] = v
            self.assertNotEqual(self.validar(d).estado, EstadoPagina.VALIDA)
        d = featureset()
        del d["features"][0]["attributes"]["oid"]
        self.rechazar(d, "oid_ausente")

    def test_oid_cero_y_huecos_numericos_no_se_inventan(self):
        self.assertEqual(self.validar(featureset((0, 7, 123))).estado, EstadoPagina.VALIDA)

    def test_error_arcgis_http_200_diagnostico_seguro(self):
        r = self.rechazar({"error": {"code": 500, "message": "token=secreto"}}, "error_arcgis_en_http_200")
        self.assertNotIn("secreto", repr(r))

    def test_features_forma_invalida(self):
        for features in (None, {}, [None], [{"geometry": None}], [5]):
            d = featureset()
            d["features"] = features
            self.assertNotEqual(self.validar(d).estado, EstadoPagina.VALIDA)

    def test_json_truncado_malformado_y_sufijo(self):
        for cuerpo in (respuesta().contenido[:-1], b'{"features":]', b'{} basura', b'{}{}', b'\xff', b''):
            self.assertNotEqual(self.validar(cuerpo).estado, EstadoPagina.VALIDA)

    def test_claves_duplicadas_criticas_escapadas_y_anidadas(self):
        cuerpo = respuesta().contenido
        for extra in (b',"features":[]}', b',"\\u0066eatures":[]}', b',"otro":{"x":1,"x":2}}'):
            self.rechazar(cuerpo[:-1] + extra, "json_claves_duplicadas")

    def test_bytes_exactos_sha256_y_sin_verificacion_fisica(self):
        r = self.validar()
        self.assertEqual(r.sha256, hashlib.sha256(r.respuesta.contenido).hexdigest())
        self.assertEqual(r.bytes_recibidos, len(r.respuesta.contenido))
        self.assertFalse(hasattr(r, "asset_id"))

    def test_transferencia_incompleta_no_es_pagina_valida(self):
        for kw in ({"transferencia_completa": False}, {"interrumpida": True}):
            r = validar_featureset(respuesta(**kw), contrato())
            self.assertEqual(r.estado, EstadoPagina.INTERRUMPIDA)
            self.assertEqual(r.entidades, ())

    def test_longitud_contradictoria_y_http_206(self):
        for r in (respuesta(longitud_declarada=0), respuesta(codigo_http=206), respuesta(codigo_http=503)):
            self.assertEqual(validar_featureset(r, contrato()).estado, EstadoPagina.INVALIDA)

    def test_exceeded_transfer_limit_triestado(self):
        for valor in (True, False, None):
            d = featureset(exceso=valor)
            if valor is None:
                del d["exceededTransferLimit"]
            r = self.validar(d)
            self.assertEqual(r.estado, EstadoPagina.VALIDA)
            self.assertIs(r.exceeded_transfer_limit, valor)
        d["exceededTransferLimit"] = 0
        self.rechazar(d, "transfer_limit_no_booleano")

    def test_vacio_estructural_valido_no_declara_coleccion_completa(self):
        r = self.validar(featureset(()))
        self.assertEqual(r.estado, EstadoPagina.VALIDA)
        self.assertEqual(r.entidades, ())
        self.assertFalse(hasattr(r, "completitud"))

    def test_limite_bytes_previo_a_parser_y_hash(self):
        with patch("spica.adquisicion._json_acotado.json.loads", side_effect=AssertionError):
            r = self.rechazar(respuesta().contenido, "limite_bytes_respuesta",
                               limites=replace(LimitesVector(), max_bytes_respuesta=10))
        self.assertEqual(r.estado, EstadoPagina.LIMITADA)
        self.assertIsNone(r.sha256)

    def test_featureset_mayor_un_mib_con_politica_independiente(self):
        d = featureset(range(40))
        for f in d["features"]:
            f["attributes"]["texto"] = "x" * 30_000
        r = self.validar(d)
        self.assertGreater(r.bytes_recibidos, 1_048_576)
        self.assertEqual(r.estado, EstadoPagina.VALIDA)
        from spica.adquisicion.inspeccion_arcgis import LIMITE_METADATOS, LimitesInspeccion
        self.assertEqual(LIMITE_METADATOS, 1_048_576)
        self.assertEqual(LimitesInspeccion().unidades_documento, 131_072)

    def test_limite_nodos_previo_a_materializar(self):
        with patch("spica.adquisicion._json_acotado.json.loads", side_effect=AssertionError):
            self.rechazar(featureset(), "json_presupuesto_documento_agotado",
                          limites=replace(LimitesVector(), unidades_documento=5))

    def test_limites_profundidad_cadena_lista_y_objeto(self):
        for limites, codigo in ((replace(LimitesVector(), profundidad=2), "json_demasiado_profundo"),
                                (replace(LimitesVector(), caracteres_cadena=5), "json_texto_excesivo"),
                                (replace(LimitesVector(), elementos_lista=2), "json_demasiados_elementos"),
                                (replace(LimitesVector(), propiedades_objeto=2), "json_demasiados_elementos")):
            self.rechazar(featureset(), codigo, limites=limites)

    def test_limites_entidades_atributos_anillos_y_coordenadas(self):
        for limites, codigo, d in (
            (replace(LimitesVector(), entidades_pagina=1), "limite_entidades_pagina", featureset((1, 2))),
            (replace(LimitesVector(), atributos_entidad=2), "limite_atributos", featureset()),
            (replace(LimitesVector(), coordenadas_entidad=3), "limite_coordenadas_entidad", featureset()),
            (replace(LimitesVector(), coordenadas_pagina=7), "limite_coordenadas_pagina", featureset((1, 2))),
        ):
            self.rechazar(d, codigo, limites=limites)
        d = featureset()
        d["features"][0]["geometry"]["rings"] *= 2
        self.rechazar(d, "limite_anillos", limites=replace(LimitesVector(), anillos_entidad=1))

    def test_snapshot_excesivo_no_se_etiqueta_como_json_malformado(self):
        d = featureset()
        d["features"][0]["geometry"]["rings"] = [[[0, 0]] * 170_000]
        limites = replace(LimitesVector(), unidades_documento=600_000, elementos_lista=200_000,
                           coordenadas_entidad=200_000, coordenadas_pagina=200_000)
        r = self.rechazar(d, "limite_snapshot_inmutable", limites=limites)
        self.assertEqual(r.estado, EstadoPagina.LIMITADA)

    def test_cancelacion_antes_y_durante_lectura(self):
        e = Event()
        e.set()
        self.assertEqual(self.validar(cancelacion=e).estado, EstadoPagina.CANCELADA)
        e.clear()
        original = json.loads
        def cancelar(*a, **kw):
            e.set()
            return original(*a, **kw)
        with patch("spica.adquisicion._json_acotado.json.loads", side_effect=cancelar):
            self.assertEqual(self.validar(cancelacion=e).estado, EstadoPagina.CANCELADA)

    def test_snapshot_inmutable_y_sin_aliases(self):
        r = self.validar()
        e = r.entidades[0]
        with self.assertRaises(TypeError):
            e.atributos["texto"] = "cambio"
        with self.assertRaises(TypeError):
            e.geometria["rings"][0][0][0] = 9
        with self.assertRaises(FrozenInstanceError):
            e.identidad_logica = "inventado"
        origen = {"oid": 1, "texto": "anterior", "valor": 2}
        copia = replace(e, atributos=MappingProxyType(origen))
        origen["texto"] = "cambio"
        self.assertEqual(copia.atributos["texto"], "anterior")

    def test_salida_crs_copiada_y_colecciones_mutables_rechazadas(self):
        p = self.validar()
        crs = {"wkid": 4326}
        copia = replace(p, referencia_declarada=crs)
        crs["wkid"] = 3857
        self.assertEqual(copia.referencia_declarada["wkid"], 4326)
        for kw in ({"entidades": list(p.entidades)}, {"diagnosticos": []}):
            with self.assertRaises(TypeError):
                replace(p, **kw)

    def test_determinismo(self):
        self.assertEqual(self.validar(), self.validar())


class ContratosVectorTests(unittest.TestCase):
    def test_identidades_y_version_diferenciadas(self):
        c = consulta()
        self.assertNotEqual(c.adquisicion_id, c.consulta_id)
        self.assertEqual(c.version_contrato, "0.1")
        self.assertEqual(replace(c, adquisicion_id="otra-adquisicion").huella, c.huella)
        self.assertNotEqual(replace(c, parametros={"where": "oid=7"}).huella, c.huella)
        self.assertNotEqual(replace(c, recurso=replace(c.recurso, capa_id=4)).huella, c.huella)

    def test_parametros_copiados_privados_y_declarativos(self):
        p = {"where": "__import__('os').remove('no-ejecutar')"}
        c = replace(consulta(), parametros=p)
        p["where"] = "otro"
        self.assertIn("__import__", c.parametros["where"])
        self.assertNotIn("__import__", repr(c))
        self.assertNotIn("where", repr(c))

    def test_rechaza_secretos_y_paginacion_ajena(self):
        for p in ({"token": "x"}, {"Authorization": "x"}, {"resultOffset": "4"}, {"objectIds": "1,2"}):
            with self.assertRaises(ValueError):
                replace(consulta(), parametros=p)

    def test_contratos_invalidos_rechazados(self):
        for kw in ({"campo_oid": "otro"}, {"campos": contrato().campos * 2},
                   {"dimensiones": 3}, {"geometria": "esriGeometryPoint"}):
            with self.assertRaises(ValueError):
                replace(contrato(), **kw)
        with self.assertRaises(ValueError):
            replace(consulta(), creada_utc=FECHA.replace(tzinfo=None))
        with self.assertRaises(ValueError):
            replace(consulta(), version_contrato="999")

    def test_evidencia_ids_sin_fecha_o_duplicados_rechazada(self):
        for kw in ({"object_ids": (1,)}, {"object_ids": (1, 1), "ids_obtenidos_utc": FECHA},
                   {"instantanea_consistente": True}):
            with self.assertRaises(ValueError):
                EvidenciaConjunto(consulta().huella, FECHA, "fixture", **kw)

    def test_limites_invalidos_rechazados(self):
        for kw in ({"max_paginas": 0}, {"bytes_auxiliares": True}, {"profundidad": 65}):
            with self.assertRaises(ValueError):
                LimitesVector(**kw)

    def test_tipos_enteros_conforme_contrato_sin_conversion(self):
        for tipo, valido, invalido in ((TipoCampo.ENTERO_CORTO, -32768, 32768),
                                       (TipoCampo.ENTERO, 2**31-1, 2**31),
                                       (TipoCampo.ENTERO_LARGO, 2**63-1, 2**63)):
            c = replace(contrato(), campos=contrato().campos[:2] + (CampoVector("valor", tipo),))
            d = featureset()
            d["fields"][2]["type"] = tipo.value
            d["features"][0]["attributes"]["valor"] = valido
            self.assertEqual(validar_featureset(respuesta(d), c).estado, EstadoPagina.VALIDA)
            d["features"][0]["attributes"]["valor"] = invalido
            self.assertEqual(validar_featureset(respuesta(d), c).estado, EstadoPagina.INVALIDA)

    def test_fecha_numerica_original_no_adquiere_zona(self):
        c = replace(contrato(), campos=contrato().campos[:2] + (CampoVector("valor", TipoCampo.FECHA),))
        d = featureset()
        d["fields"][2]["type"] = TipoCampo.FECHA.value
        d["features"][0]["attributes"]["valor"] = 0
        r = validar_featureset(respuesta(d), c)
        self.assertEqual(r.entidades[0].atributos["valor"], 0)
        self.assertIs(type(r.entidades[0].atributos["valor"]), int)


if __name__ == "__main__":
    unittest.main()
