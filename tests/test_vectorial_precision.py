"""PASO 83-B: regresiones numéricas y presupuestos; solo contenido inventado."""

from dataclasses import replace
from decimal import Decimal, localcontext
import hashlib
import json
from threading import Event
from types import MappingProxyType
import unittest
from unittest.mock import patch

from test_vectorial_featureset import contrato, consulta, featureset, respuesta
from test_vectorial_coordinacion import evidencia, pagina
from spica.adquisicion.vectorial import (
    EstadoCompletitud as EC, EstadoPagina as EP, LimitesVector,
    PrecisionNumerica as PN, SolicitudPagina, TransporteSintetico, coordinar, validar_featureset,
)


def con_numero(literal):
    """Introduce el token original, sin redondearlo previamente con Python float."""
    return respuesta(respuesta().contenido.replace(b"1.25", literal.encode("ascii")))


class PrecisionVectorTests(unittest.TestCase):
    def exacta(self, r=None, **kw):
        return validar_featureset(r if r is not None else respuesta(), contrato(),
                                  precision=PN.DECIMAL_EXACTA, **kw)

    def test_decimales_atributos_exactos_signos_ceros_y_exponentes(self):
        for token in ("0.123456789012345678901234567890123456789", "-123.00000000000000000000000001",
                      "0.0", "-0.0", "1.2300E+02", "-1.20e-40"):
            with self.subTest(token=token):
                p = self.exacta(con_numero(token))
                self.assertEqual(p.estado, EP.VALIDA)
                valor = p.entidades[0].atributos["valor"]
                self.assertIs(type(valor), Decimal)
                self.assertEqual(valor.as_tuple(), Decimal(token).as_tuple())
                self.assertEqual(p.precision, PN.DECIMAL_EXACTA)

    def test_modo_predeterminado_conserva_float_y_declara_precision(self):
        r = con_numero("0.123456789012345678901234567890123456789")
        p = validar_featureset(r, contrato())
        self.assertIs(type(p.entidades[0].atributos["valor"]), float)
        self.assertEqual(p.precision, PN.BINARIA_COMPATIBLE)
        self.assertNotEqual(Decimal.from_float(p.entidades[0].atributos["valor"]),
                            Decimal("0.123456789012345678901234567890123456789"))

    def test_contexto_decimal_no_redondea_la_lectura(self):
        token = "123456789.12345678901234567890123456789"
        with localcontext() as c:
            c.prec = 3
            p = self.exacta(con_numero(token))
        self.assertEqual(p.entidades[0].atributos["valor"], Decimal(token))

    def test_subdesbordamiento_no_se_convierte_silenciosamente_en_cero(self):
        r = con_numero("1e-999")
        p = self.exacta(r)
        self.assertEqual(p.estado, EP.VALIDA)
        self.assertEqual(p.entidades[0].atributos["valor"], Decimal("1e-999"))
        b = validar_featureset(r, contrato())
        self.assertEqual(b.estado, EP.INVALIDA)
        self.assertIn("json_subdesbordamiento_binario", b.diagnosticos)

    def test_cierre_de_anillo_no_se_deduce_por_redondeo(self):
        raw = respuesta().contenido
        # Los dos tokens son distintos de cero; el segundo colapsaba a cero.
        for token in ("0.000000000000000000000000000001", "1e-999"):
            cuerpo = raw.replace(b"[0,1],[0,0]", ("[0,1],[" + token + ",0]").encode())
            self.assertNotEqual(cuerpo, raw)
            for precision in PN:
                p = validar_featureset(respuesta(cuerpo), contrato(), precision=precision)
                self.assertEqual(p.estado, EP.INVALIDA)
                self.assertEqual(p.entidades, ())
        # Dos números cercanos que el float binario representa como 1.0.
        d = featureset()
        d["features"][0]["geometry"]["rings"] = [[[1, 0], [2, 0], [1, 1], [1, 0]]]
        cuerpo = respuesta(d).contenido.replace(b"[1,1],[1,0]", b"[1,1],[1.00000000000000000000001,0]")
        for precision in PN:
            p = validar_featureset(respuesta(cuerpo), contrato(), precision=precision)
            self.assertIn("anillo_no_cerrado", p.diagnosticos)

    def test_anillos_y_vertices_decimales_conservan_orden_y_crs(self):
        raw = respuesta().contenido
        anillos = (b'"rings":[[[0.123456789012345678901,0],[1,0],[0,1],[0.123456789012345678901,0]],'
                   b'[[-0.20,-0.30],[-0.21,-0.30],[-0.20,-0.31],[-0.20,-0.30]]]')
        cuerpo = raw.replace(b'"rings":[[[0,0],[1,0],[0,1],[0,0]]]', anillos)
        p = self.exacta(respuesta(cuerpo))
        self.assertEqual(p.estado, EP.VALIDA)
        rings = p.entidades[0].geometria["rings"]
        self.assertEqual(rings[0][0][0], Decimal("0.123456789012345678901"))
        self.assertEqual(rings[1][1], (Decimal("-0.21"), Decimal("-0.30")))
        self.assertEqual(dict(p.referencia_declarada), {"wkid": 4326})
        self.assertEqual(p.coordenadas, 8)

    def test_enteros_oid_grandes_son_int_no_float_ni_decimal(self):
        for oid in (2**53 + 1, 2**63 - 1):
            p = self.exacta(respuesta(featureset((oid,))))
            self.assertEqual(p.estado, EP.VALIDA)
            self.assertIs(type(p.entidades[0].object_id_observado), int)
            self.assertEqual(p.entidades[0].atributos["oid"], oid)
        self.assertEqual(self.exacta(respuesta(featureset((2**63,)))).estado, EP.INVALIDA)

    def test_oid_decimal_y_booleanos_no_se_aceptan_como_enteros(self):
        for oid in ("1.0", "true"):
            cuerpo = respuesta().contenido.replace(b'"oid":1,', b'"oid":' + oid.encode() + b',')
            self.assertIn("tipo_atributo_incorrecto", self.exacta(respuesta(cuerpo)).diagnosticos)
        d = featureset()
        d["features"][0]["attributes"]["texto"] = None
        self.assertIsNone(self.exacta(respuesta(d)).entidades[0].atributos["texto"])
        d["features"][0]["attributes"]["valor"] = True
        self.assertEqual(self.exacta(respuesta(d)).estado, EP.INVALIDA)

    def test_no_finitos_rechazados_tambien_en_modo_exacto(self):
        for token in ("NaN", "Infinity", "-Infinity"):
            self.assertIn("json_numero_no_finito", self.exacta(con_numero(token)).diagnosticos)
        # Finito en Decimal, no representable por float binario. No es un
        # permiso científico ni certificación de almacenamiento IEEE del campo.
        self.assertEqual(self.exacta(con_numero("1e999")).estado, EP.VALIDA)
        self.assertEqual(validar_featureset(con_numero("1e999"), contrato()).estado, EP.INVALIDA)

    def test_presupuestos_numericos_antes_de_construir_decimal(self):
        for token, codigo in (("0." + "1" * 255, "json_numero_excesivo"),
                               ("1e999999999999999999999999", "json_exponente_excesivo")):
            with patch("spica.adquisicion._json_acotado.Decimal", side_effect=AssertionError):
                p = self.exacta(con_numero(token))
            self.assertEqual(p.estado, EP.LIMITADA)
            self.assertIn(codigo, p.diagnosticos)
            self.assertEqual(p.entidades, ())

    def test_fronteras_de_coeficiente_y_exponente_y_limite_reducido(self):
        self.assertEqual(self.exacta(con_numero("0." + "1" * 254)).estado, EP.VALIDA)
        self.assertEqual(self.exacta(con_numero("1e4096")).estado, EP.VALIDA)
        self.assertEqual(self.exacta(con_numero("1e-4096")).estado, EP.VALIDA)
        self.assertEqual(self.exacta(con_numero("1e4097")).estado, EP.LIMITADA)
        self.assertEqual(self.exacta(con_numero("1.1e-4096")).estado, EP.LIMITADA)
        p = self.exacta(con_numero("0.12345"), limites=replace(LimitesVector(), caracteres_numero=4))
        self.assertEqual(p.estado, EP.LIMITADA)

    def test_representacion_textual_no_se_reconstruye_por_serializar(self):
        r = con_numero("1.2300E+02")
        p = self.exacta(r)
        v = p.entidades[0].atributos["valor"]
        self.assertEqual(v, Decimal("123"))
        self.assertNotEqual(str(v), "1.2300E+02")
        self.assertIs(p.respuesta.contenido, r.contenido)
        self.assertEqual(p.sha256, hashlib.sha256(r.contenido).hexdigest())
        with self.assertRaises(TypeError):
            json.dumps({"valor": v})  # No hay conversión implícita a float.
        reserializado = json.dumps(json.loads(r.contenido)).encode()
        self.assertNotEqual(reserializado, r.contenido)

    def test_geometria_ausente_y_nula_en_modo_exacto(self):
        d = featureset()
        d["features"][0]["geometry"] = None
        nula = self.exacta(respuesta(d)).entidades[0]
        del d["features"][0]["geometry"]
        ausente = self.exacta(respuesta(d)).entidades[0]
        self.assertNotEqual(nula.estado_geometria, ausente.estado_geometria)

    def test_determinismo_e_inmutabilidad_decimal(self):
        r = con_numero("0.12345678901234567890123456789")
        self.assertEqual(self.exacta(r), self.exacta(r))
        p = self.exacta(r)
        with self.assertRaises(TypeError):
            p.entidades[0].atributos["valor"] = Decimal(3)

    def test_perfil_tipos_y_limites_no_admite_configuracion_ambigua(self):
        with self.assertRaises(TypeError):
            validar_featureset(respuesta(), contrato(), precision="decimal_exacta")
        for kw in ({"caracteres_numero": 257}, {"exponente_decimal": 4097}):
            with self.assertRaises(ValueError):
                LimitesVector(**kw)


class RegresionesCoordinacion83BTests(unittest.TestCase):
    def test_perfil_exacto_consta_en_resultado_incluso_cancelado(self):
        t = TransporteSintetico([pagina((1, 2))])
        r = coordinar(consulta(), t, tamano_pagina=2, evidencia=evidencia((1, 2)), precision=PN.DECIMAL_EXACTA)
        self.assertEqual(r.completitud, EC.COMPLETA_COMPROBADA)
        self.assertEqual(r.precision, PN.DECIMAL_EXACTA)
        e = Event()
        e.set()
        r = coordinar(consulta(), TransporteSintetico([]), cancelacion=e, precision=PN.DECIMAL_EXACTA)
        self.assertEqual(r.completitud, EC.PARCIAL)
        self.assertEqual(r.precision, PN.DECIMAL_EXACTA)

    def test_modo_exacto_se_aplica_al_validador_de_paginas(self):
        vistos = []
        import spica.adquisicion.vectorial.coordinador as m
        original = m.validar_featureset
        def observar(*a, **kw):
            p = original(*a, **kw)
            vistos.append(type(p.entidades[0].atributos["valor"]))
            return p
        with patch.object(m, "validar_featureset", new=observar):
            r = coordinar(consulta(), TransporteSintetico([pagina()]), tamano_pagina=1, precision=PN.DECIMAL_EXACTA)
        self.assertEqual(vistos, [Decimal])
        self.assertNotEqual(r.completitud, EC.COMPLETA_COMPROBADA)

    def test_eco_inesperado_no_elude_presupuesto_auxiliar(self):
        s = SolicitudPagina("otro", consulta().huella, 1, {"where": "x" * 8000})
        r = coordinar(consulta(), TransporteSintetico([respuesta(solicitud=s)]), tamano_pagina=1,
                       limites=replace(LimitesVector(), bytes_auxiliares=10_000))
        self.assertEqual(r.completitud, EC.INCONSISTENTE)
        self.assertIn("discontinuidad_de_solicitud", r.diagnosticos)
        self.assertIn("eco_omitido_por_limite_auxiliar", r.diagnosticos)
        self.assertIsNone(r.recibos[0].solicitud_observada)
        self.assertIsNone(r.recibos[0].sha256)

    def test_eco_distinto_pero_igual_en_valor_tambien_se_presupuesta(self):
        c = consulta()
        parametros = dict(c.parametros, resultOffset="0", resultRecordCount="1", orderByFields="oid ASC")
        s = SolicitudPagina(c.adquisicion_id, c.huella, 1, parametros)
        r = coordinar(c, TransporteSintetico([respuesta(solicitud=s)]), tamano_pagina=1,
                       limites=replace(LimitesVector(), bytes_auxiliares=6000))
        self.assertEqual(r.completitud, EC.INCOMPLETA_POR_LIMITES)
        self.assertIn("eco_omitido_por_limite_auxiliar", r.diagnosticos)

    def test_reutilizar_transporte_no_reanuda_ni_completa_consulta(self):
        t = TransporteSintetico([pagina((1, 2), exceso=True),
                                pagina((3,), numero=2, interrumpida=True), pagina((3,), numero=3)])
        primero = coordinar(consulta(), t, tamano_pagina=2, evidencia=evidencia())
        segundo = coordinar(consulta(), t, tamano_pagina=2, evidencia=evidencia())
        self.assertEqual(primero.completitud, EC.PARCIAL)
        self.assertEqual(segundo.completitud, EC.INCONSISTENTE)
        self.assertEqual(segundo.entidades_recibidas, 1)
        self.assertEqual(segundo.recibos[0].solicitud.parametros["resultOffset"], "0")

    def test_completitud_sigue_exigiendo_instantanea_en_modo_exacto(self):
        r = coordinar(consulta(), TransporteSintetico([pagina((1, 2))]), tamano_pagina=2,
                       evidencia=evidencia((1, 2), sellada=False), precision=PN.DECIMAL_EXACTA)
        self.assertEqual(r.completitud, EC.DESCONOCIDA)
        self.assertIn("sin_garantia_de_instantanea_consistente", r.limitaciones)


if __name__ == "__main__":
    unittest.main()
