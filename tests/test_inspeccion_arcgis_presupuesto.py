"""PASO 82-D: conteo léxico contrastado con árboles inventados, sin primarios."""

from dataclasses import replace
import hashlib
import json
import random
from threading import Event
import tracemalloc
import unittest
from unittest.mock import patch

from test_inspeccion_arcgis import capa, codificar, objetivo
from test_inspeccion_arcgis_extensa import extensa
from spica.adquisicion.inspeccion_arcgis import (
    AlcanceMetadatos, EstadoJSON, EstadoMetadatos, LIMITE_METADATOS,
    LimitesInspeccion, TipoMetadatos, inspeccionar_metadatos,
)
from spica.adquisicion.transportes import RespuestaHTTP


def nodos(v):
    """Oráculo de árbol: una aparición por contenedor, clave y valor."""
    if type(v) is dict:
        return 1 + sum(1 + nodos(x) for x in v.values())
    if type(v) is list:
        return 1 + sum(nodos(x) for x in v)
    return 1


def unidades_82b(v):
    if type(v) is dict:
        return 1 + 2 * len(v) + max(0, len(v) - 1) + sum(unidades_82b(x) for x in v.values())
    if type(v) is list:
        return 2 + max(0, len(v) - 1) + sum(unidades_82b(x) for x in v)
    return int(type(v) is str)


def presupuesto_exacto():
    d = capa()
    d["opcional"] = [[0] * 20_000 for _ in range(6)] + [[]]
    d["opcional"][-1] = [0] * (131_072 - nodos(d))
    return d


class PresupuestoLexicoTests(unittest.TestCase):
    def validar(self, d, **kw):
        cuerpo = d if type(d) is bytes else codificar(d)
        return inspeccionar_metadatos(RespuestaHTTP(200, {"content-type": "application/json"}, cuerpo),
                                      TipoMetadatos.CAPA, objetivo(), **kw)

    def revision(self, d, codigo, **kw):
        r = self.validar(d, **kw)
        self.assertEqual(r.estado, EstadoMetadatos.REVISION)
        self.assertIn(codigo, r.diagnosticos)
        self.assertEqual(dict(r.datos), {})
        return r

    def test_presupuesto_numerico_y_otros_topes_no_se_amplian(self):
        self.assertEqual(LIMITE_METADATOS, 1_048_576)
        self.assertEqual(LimitesInspeccion(), LimitesInspeccion(131_072, 20_000, 32, 20_000, 4096, 65_536))

    def test_escalares_y_contenedores_vacios_cuentan_una_aparicion(self):
        for d in (None, True, False, 0, -3, 1.25, "texto", {}, []):
            with self.subTest(d=d):
                r = self.validar(d)
                self.assertEqual(r.estado_json, EstadoJSON.COMPLETO)
                self.assertEqual(r.estadisticas.unidades_prelectura, 1)
                self.assertEqual(r.estadisticas.nodos_documento, 1)

    def test_escapes_unicode_signos_y_exponentes_no_duplican_nodos(self):
        d = {"\\\"[,]{}:": ["á😀\\\"[,]{}:", -1.25e-3, True, False, None, {}, []]}
        for ascii_solo in (True, False):
            cuerpo = json.dumps(d, ensure_ascii=ascii_solo).encode('utf-8')
            r = self.validar(cuerpo)
            self.assertEqual(r.estado_json, EstadoJSON.COMPLETO)
            self.assertEqual(r.estadisticas.unidades_prelectura, nodos(d))
            self.assertEqual(r.estadisticas.nodos_documento, nodos(d))

    def test_bom_y_whitespace_conservan_hash_original_y_conteo(self):
        d = capa()
        cuerpo = b'\xef\xbb\xbf \r\n' + codificar(d) + b'\t\n '
        r = self.validar(cuerpo)
        self.assertEqual(r.estado, EstadoMetadatos.COHERENTE)
        self.assertEqual(r.estadisticas.unidades_prelectura, nodos(d))
        self.assertEqual(r.sha256, hashlib.sha256(cuerpo).hexdigest())

    def test_arboles_aleatorios_reproducibles_coinciden_con_oraculo(self):
        azar = random.Random(82)
        def generar(nivel):
            if nivel == 0 or azar.randrange(3) == 0:
                return azar.choice((None, True, False, -25, 1.25e-4, 'á[]{}:\\"'))
            if azar.randrange(2):
                return [generar(nivel - 1) for _ in range(azar.randrange(5))]
            return {str(i): generar(nivel - 1) for i in range(azar.randrange(5))}
        for _ in range(200):
            d = generar(4)
            r = self.validar(d)
            self.assertEqual(r.estado_json, EstadoJSON.COMPLETO)
            self.assertEqual(r.estadisticas.unidades_prelectura, nodos(d))
            self.assertEqual(r.estadisticas.nodos_documento, nodos(d))

    def test_secundarias_extensas_superan_heuristica_pero_no_nodos(self):
        d = extensa(6000, 1)
        self.assertGreater(unidades_82b(d), 131_072)
        self.assertLess(nodos(d), 131_072)
        self.assertLess(len(codificar(d)), LIMITE_METADATOS)
        r = self.validar(d)
        self.assertEqual(r.estado_json, EstadoJSON.COMPLETO)
        self.assertEqual(r.estado, EstadoMetadatos.COHERENTE)
        self.assertEqual(r.estadisticas.unidades_prelectura, r.estadisticas.nodos_documento)
        self.assertNotIn('drawingInfo', r.datos)
        self.assertIn('drawingInfo', r.secciones_omitidas)

    def test_dos_representaciones_secundarias_no_se_eliminan_del_conteo(self):
        d = extensa(3000, 1)
        d['drawingInfo']['renderer']['uniqueValueGroups'] = [{'classes': [
            {'label': 'clase sintetica', 'symbol': {'color': [1, 2, 3, 4]}, 'values': [[str(i)]]}
            for i in range(2500)]}]
        self.assertLess(nodos(d), 131_072)
        self.assertGreater(unidades_82b(d), 131_072)
        r = self.validar(d)
        self.assertEqual(r.estado, EstadoMetadatos.COHERENTE)
        self.assertEqual(r.estadisticas.nodos_documento, nodos(d))

    def test_131072_nodos_se_aceptan_con_puntuacion_no_contada(self):
        d = presupuesto_exacto()
        self.assertEqual(nodos(d), 131_072)
        r = self.validar(d)
        self.assertEqual(r.estado, EstadoMetadatos.COHERENTE)
        self.assertEqual(r.estadisticas.unidades_prelectura, 131_072)
        self.assertEqual(r.estadisticas.nodos_documento, 131_072)

    def test_siguiente_nodo_se_rechaza_antes_del_parser(self):
        d = presupuesto_exacto()
        d['opcional'][-1].append(0)
        with patch('spica.adquisicion.inspeccion_arcgis.inspector.json.loads', side_effect=AssertionError):
            r = self.revision(d, 'json_presupuesto_documento_agotado')
        self.assertEqual(r.estadisticas.unidades_prelectura, 131_073)
        self.assertEqual(r.estadisticas.nodos_documento, 0)
        self.assertEqual(r.estado_json, EstadoJSON.PARCIAL)

    def test_complejidad_esencial_sigue_teniendo_presupuesto_independiente(self):
        d = extensa(4000, 1)
        d['fields'][1]['domain'] = {'codedValues': [{'code': i, 'name': str(i)} for i in range(4500)]}
        self.assertLess(nodos(d), 131_072)
        r = self.revision(d, 'json_presupuesto_esenciales_agotado')
        self.assertEqual(r.estado_json, EstadoJSON.COMPLETO)
        self.assertEqual(r.alcance, AlcanceMetadatos.INCOMPLETO)

    def test_cardinalidades_y_profundidad_se_rechazan_antes_del_parser(self):
        casos = [({'opcional': [0] * 20_001}, 'json_demasiados_elementos'),
                 ({'opcional': {str(i): 0 for i in range(4097)}}, 'json_demasiados_elementos'),
                 (b'[' * 33 + b'0' + b']' * 33, 'json_demasiado_profundo')]
        for d, codigo in casos:
            with self.subTest(codigo=codigo):
                with patch('spica.adquisicion.inspeccion_arcgis.inspector.json.loads', side_effect=AssertionError):
                    self.revision(d, codigo)

    def test_cadenas_largas_siguen_limitadas_en_secciones_omitidas(self):
        d = capa()
        d['opcional'] = 'x' * 65_537
        r = self.revision(d, 'json_texto_excesivo')
        self.assertEqual(r.alcance, AlcanceMetadatos.INCOMPLETO)

    def test_duplicados_criticos_al_final_de_json_extenso(self):
        cuerpo = codificar(extensa(6000, 1))
        for extra in (b',"id":7}', b',"\\u0069d":7}', b',"opcional":{"a":1,"a":2}}'):
            self.revision(cuerpo[:-1] + extra, 'json_claves_duplicadas')

    def test_truncamiento_y_tokens_invalidos_no_se_declaran_completos(self):
        cuerpo = codificar(extensa(6000, 1))
        for b in (cuerpo[:-1], cuerpo + b'{}', b'{"x":truefalse}', b'{"x":1 2}', b'{"x": [1,,2]}'):
            r = self.revision(b, 'json_malformado_o_no_admitido')
            self.assertEqual(r.estado_json, EstadoJSON.INVALIDO)

    def test_codificacion_invalida_no_se_omite_por_extraer_esenciales(self):
        self.revision(codificar(capa())[:-1] + b',"opcional":"\xff"}', 'json_malformado_o_no_admitido')

    def test_no_finitos_tardios_en_documento_extenso(self):
        cuerpo = codificar(extensa(6000, 1))
        for n in (b'NaN', b'Infinity', b'-Infinity', b'1e999'):
            self.revision(cuerpo[:-1] + b',"opcional":' + n + b'}', 'json_numero_no_finito')

    def test_error_arcgis_tardio_con_sintaxis_completa_no_se_acepta(self):
        d = extensa(6000, 1)
        d['error'] = {'code': 499, 'message': 'token=SECRETO_SINTETICO'}
        r = self.revision(d, 'error_arcgis_en_respuesta')
        self.assertEqual(r.estado_json, EstadoJSON.COMPLETO)
        self.assertNotIn('SECRETO_SINTETICO', repr(r))

    def test_campos_ausentes_y_oid_incorrecto_se_detectan_tras_json_extenso(self):
        d = extensa(6000, 1)
        d['fields'] = d['fields'][:-1]
        self.revision(d, 'campo_obligatorio_ausente')
        d = extensa(6000, 1)
        d['objectIdField'] = 'codi'
        self.revision(d, 'campo_oid_contradictorio')

    def test_source_spatial_reference_se_conserva_y_verifica(self):
        d = capa()
        d['sourceSpatialReference'] = {'wkid': 4326, 'latestWkid': 4326}
        r = self.validar(d)
        self.assertEqual(r.estado, EstadoMetadatos.COHERENTE)
        self.assertEqual(dict(r.datos['sourceSpatialReference']), d['sourceSpatialReference'])
        self.assertEqual(r.datos['extent']['spatialReference']['wkid'], 102100)
        self.assertIn('crs_fuente_sin_comprobacion_de_definicion_autoritativa', r.advertencias)

    def test_crs_de_fuente_invalido_no_se_oculta_como_opcional(self):
        for fuente, codigo in ((None, 'referencia_fuente_invalida'),
                               ({'wkid': True}, 'wkid_fuente_ausente_o_invalido'),
                               ({'wkid': '4326'}, 'wkid_fuente_ausente_o_invalido'),
                               ({'wkid': 0}, 'wkid_fuente_ausente_o_invalido'),
                               ({'wkid': 4326, 'latestWkid': False}, 'latest_wkid_fuente_invalido')):
            d = capa()
            d['sourceSpatialReference'] = fuente
            self.revision(d, codigo)

    def test_crs_de_extension_contradictorio_se_rechaza_con_origen_valido(self):
        d = capa()
        d['sourceSpatialReference'] = {'wkid': 4326, 'latestWkid': 4326}
        d['spatialReference'] = {'wkid': 4326}
        self.revision(d, 'referencia_espacial_distinta')
        del d['spatialReference']
        d['extent']['spatialReference']['latestWkid'] = 4326
        self.revision(d, 'latest_wkid_contradictorio')

    def test_cancelacion_lexica_descarta_datos_y_conserva_bytes(self):
        evento = Event()
        cuerpo = codificar(extensa(6000, 1))
        huella = hashlib.sha256(cuerpo).hexdigest()
        with patch.object(evento, 'is_set', side_effect=[False, False, False, True]):
            r = self.revision(cuerpo, 'inspeccion_cancelada', cancelacion=evento)
        self.assertEqual(r.estado_json, EstadoJSON.PARCIAL)
        self.assertEqual(hashlib.sha256(cuerpo).hexdigest(), huella)

    def test_memoria_medida_con_casi_131072_nodos_no_es_cota_de_rss(self):
        d = capa()
        d['opcional'] = [dict(a=i, b=i + 1, c=i + 2, d=i + 3, e=i + 4) for i in range(11_900)]
        cuerpo = codificar(d)
        self.assertLess(len(cuerpo), LIMITE_METADATOS)
        self.assertGreater(nodos(d), 130_000)
        tracemalloc.start()
        try:
            r = self.validar(cuerpo)
            _, pico = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
        self.assertEqual(r.estado, EstadoMetadatos.COHERENTE)
        self.assertLess(pico, 32 * 1024 * 1024)

    def test_determinismo_e_inmutabilidad_de_entrada_y_salida(self):
        cuerpo = codificar(extensa(6000, 1))
        original = hashlib.sha256(cuerpo).digest()
        a, b = self.validar(cuerpo), self.validar(cuerpo)
        self.assertEqual(a, b)
        self.assertEqual(original, hashlib.sha256(cuerpo).digest())
        with self.assertRaises(TypeError):
            a.datos['fields'][0]['name'] = 'cambiado'

    def test_presupuesto_reducido_mantiene_rechazo_previo(self):
        with patch('spica.adquisicion.inspeccion_arcgis.inspector.json.loads', side_effect=AssertionError):
            self.revision(capa(), 'json_presupuesto_documento_agotado',
                          limites=replace(LimitesInspeccion(), unidades_documento=10))


if __name__ == '__main__':
    unittest.main()
