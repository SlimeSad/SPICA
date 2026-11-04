"""Ensayos inventados: no leen evidencia institucional ni tienen transporte HTTP."""

import ast
from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from threading import Event
import unittest
from unittest.mock import patch

from spica.adquisicion.piloto_arcgis import (
    AutorizacionEnsayo, EscenarioSintetico, EstadoEnsayo as EE,
    EstadoRecepcion as ER, EstadoValidacion as EV, FalloSintetico,
    PreparacionEnsayo, SimuladorEnsayo,
)
from spica.adquisicion.piloto_arcgis.modelos import PARAMETROS_CANDIDATOS, SERVICIO
from spica.adquisicion.vectorial import EstadoCompletitud, EstadoGeometria, RespuestaSintetica


FECHA = datetime(2026, 1, 1, tzinfo=timezone.utc)
OID_INVENTADO = 9_007_199_254_740_993


def sobre(ids=(OID_INVENTADO,)):
    return dict(layerId=7, serviceName=SERVICIO, objectIdFieldName="objectid",
                fields=[dict(name="objectid", type="esriFieldTypeOID", nullable=False)],
                features=[dict(attributes=dict(objectid=x)) for x in ids])


def escenario(documento=None, *, contenido=None, **kw):
    if contenido is None:
        contenido = json.dumps(sobre() if documento is None else documento).encode("utf-8")
    return EscenarioSintetico(RespuestaSintetica("respuesta-sintetica-prueba", FECHA, contenido, **kw))


def ejecutar(esc=None, **kw):
    return SimuladorEnsayo(PreparacionEnsayo(ensayo_id="ensayo-sintetico-prueba")).ejecutar(
        esc if esc is not None else escenario(), evaluado_utc=FECHA, **kw)


class PreparacionPilotoTests(unittest.TestCase):
    def test_candidato_inmutable_y_parametros_copiados(self):
        p = dict(PARAMETROS_CANDIDATOS)
        c = PreparacionEnsayo(parametros=p)
        p["where"] = "otro"
        self.assertEqual(c.parametros["where"], "1=1")
        self.assertFalse(c.autoriza_red)
        self.assertEqual(c.autorizacion, AutorizacionEnsayo.PENDIENTE)
        self.assertTrue(c.url_candidata.startswith("https://geocatminnube.ingemmet.gob.pe/"))
        with self.assertRaises(TypeError):
            c.parametros["f"] = "pjson"
        with self.assertRaises(FrozenInstanceError):
            c.max_bytes = 100_000

    def test_host_ruta_metodo_capa_e_identidades_cerrados(self):
        cambios = [dict(host_candidato="otro.invalid"), dict(host_candidato="usuario:clave@host"),
                   dict(ruta_candidata="/query"), dict(ruta_candidata=PreparacionEnsayo().ruta_candidata + "?x=1"),
                   dict(metodo_previsto="POST"), dict(capa_id=8), dict(capa_id=True),
                   dict(servicio="otro"), dict(ensayo_id="adquisicion-real"), dict(ensayo_id="ensayo-sintetico-../x")]
        for cambio in cambios:
            with self.subTest(cambio=cambio), self.assertRaises(ValueError):
                PreparacionEnsayo(**cambio)

    def test_parametros_adicionales_geometria_paginacion_y_where_rechazados(self):
        for cambio in ({"token": "secreto"}, {"otro": "x"}, {"returnGeometry": "true"},
                       {"where": "objectid > 0"}, {"objectIds": "123"},
                       {"resultOffset": "1"}, {"resultRecordCount": "2"}, {"f": "geojson"}):
            with self.subTest(cambio=cambio), self.assertRaises(ValueError):
                PreparacionEnsayo(parametros=dict(PARAMETROS_CANDIDATOS) | cambio)
        with self.assertRaises(ValueError):
            PreparacionEnsayo(parametros={"f": "json"})

    def test_presupuestos_y_autorizacion_no_ampliables(self):
        for cambio in (dict(max_bytes=65_537), dict(max_bytes=0), dict(max_bytes=True),
                       dict(max_entidades=2), dict(max_entidades=True), dict(permitir_geometrias=True),
                       dict(autorizacion="aprobada"), dict(autorizacion=True)):
            with self.subTest(cambio=cambio), self.assertRaises(ValueError):
                PreparacionEnsayo(**cambio)
        self.assertEqual(PreparacionEnsayo(max_bytes=1024).max_bytes, 1024)
        self.assertEqual(list(AutorizacionEnsayo), [AutorizacionEnsayo.PENDIENTE])

    def test_escenario_exclusivo_y_sin_identidad_de_adquisicion(self):
        with self.assertRaises(ValueError):
            EscenarioSintetico()
        with self.assertRaises(ValueError):
            EscenarioSintetico(escenario().respuesta, FalloSintetico.CONEXION)
        for cambio in (dict(respuesta_id="adquisicion-1"), dict(instantanea_id="real"), dict(total_observado=1)):
            with self.subTest(cambio=cambio), self.assertRaises(ValueError):
                EscenarioSintetico(replace(escenario().respuesta, **cambio))
        with self.assertRaises(TypeError):
            SimuladorEnsayo(PreparacionEnsayo(), cliente=object())


class SimulacionPilotoTests(unittest.TestCase):
    def test_200_entidad_sin_geometria_oid_exacto_y_determinismo(self):
        esc = escenario()
        r = ejecutar(esc)
        self.assertEqual(r, ejecutar(esc))
        self.assertEqual((r.estado, r.recepcion, r.validacion), (EE.COHERENTE, ER.COMPLETA, EV.COHERENTE))
        self.assertEqual(r.operaciones_simuladas, 1)
        self.assertEqual(r.entidades[0].object_id_observado, OID_INVENTADO)
        self.assertIs(type(r.entidades[0].atributos["objectid"]), int)
        self.assertIsNone(r.entidades[0].identidad_logica)
        self.assertEqual(r.entidades[0].estado_geometria, EstadoGeometria.AUSENTE)
        self.assertEqual(r.contenido, esc.respuesta.contenido)
        self.assertEqual(r.sha256, hashlib.sha256(r.contenido).hexdigest())
        self.assertEqual(r.completitud_institucional, EstadoCompletitud.DESCONOCIDA)
        self.assertEqual(r.solicitud.destino, "fixture://spica/piloto-arcgis/atributos")
        self.assertFalse(hasattr(r, "adquisicion_id"))
        self.assertFalse(hasattr(r, "asset_id"))

    def test_sobre_minimo_no_inventa_capa_campos_ni_crs(self):
        r = ejecutar(escenario(dict(features=[dict(attributes=dict(objectid=OID_INVENTADO))])))
        self.assertEqual(r.estado, EE.COHERENTE)
        self.assertIsNone(r.capa_observada)
        self.assertIn("identidad_capa_no_declarada_en_fixture", r.diagnosticos)
        self.assertIn("descriptores_no_declarados_validacion_contra_contrato", r.diagnosticos)
        self.assertIsNone(r.entidades[0].geometria)

    def test_vacio_no_es_error_ni_objetivo_demostrado(self):
        r = ejecutar(escenario(sobre(())))
        self.assertEqual((r.estado, r.validacion), (EE.VACIO, EV.VACIA))
        self.assertEqual(r.entidades, ())
        self.assertEqual(r.completitud_institucional, EstadoCompletitud.DESCONOCIDA)

    def test_error_arcgis_200_no_es_featureset(self):
        r = ejecutar(escenario(dict(error=dict(code=400, message="secreto no registrar"))))
        self.assertEqual(r.validacion, EV.RECHAZADA)
        self.assertEqual(r.diagnosticos, ("error_arcgis_en_http_200",))
        self.assertTrue(r.sintaxis_completa)
        self.assertNotIn("secreto", repr(r))

    def test_multiples_entidades_no_aceptadas(self):
        r = ejecutar(escenario(sobre((111, 222))))
        self.assertEqual(r.validacion, EV.RECHAZADA)
        self.assertIn("multiples_entidades_no_admitidas", r.diagnosticos)
        self.assertEqual(r.entidades, ())

    def test_geometria_incluso_nula_rechazada(self):
        for g in (None, {}, dict(rings=[[[1, 2], [2, 3], [1, 2]]])):
            d = sobre()
            d["features"][0]["geometry"] = g
            with self.subTest(g=g):
                r = ejecutar(escenario(d))
                self.assertEqual(r.validacion, EV.RECHAZADA)
                self.assertIn("geometria_prohibida_incluso_nula", r.diagnosticos)

    def test_atributo_extra_y_oid_ausente(self):
        for attrs, codigo in (({}, "objectid_ausente"),
                              ({"objectid": 123, "extra": "no aprobado"}, "atributos_inesperados")):
            d = sobre()
            d["features"][0]["attributes"] = attrs
            with self.subTest(attrs=attrs):
                r = ejecutar(escenario(d))
                self.assertEqual(r.validacion, EV.RECHAZADA)
                self.assertEqual(r.diagnosticos, (codigo,))

    def test_oid_no_se_redondea_ni_convierte(self):
        for oid in (True, None, "123", -1, 1.0, 2**63):
            with self.subTest(oid=oid):
                self.assertEqual(ejecutar(escenario(sobre((oid,)))).validacion, EV.RECHAZADA)
        self.assertEqual(ejecutar(escenario(sobre((2**63 - 1,)))).entidades[0].object_id_observado, 2**63 - 1)

    def test_identidad_capa_servicio_y_descriptores_incompatibles(self):
        for cambio, codigo in ((dict(layerId=8), "identidad_capa_incompatible"),
                               (dict(serviceName="otro"), "identidad_servicio_incompatible"),
                               (dict(objectIdFieldName="otro"), "descriptor_oid_incompatible"),
                               (dict(fields=[dict(name="objectid", type="esriFieldTypeDouble")]), "descriptor_oid_incompatible")):
            with self.subTest(cambio=cambio):
                r = ejecutar(escenario(sobre() | cambio))
                self.assertEqual(r.validacion, EV.RECHAZADA)
                self.assertEqual(r.diagnosticos, (codigo,))
                if "layerId" in cambio:
                    self.assertEqual(r.capa_observada, 8)

    def test_json_truncado_duplicados_no_finitos_y_presupuesto_estructural(self):
        for cuerpo in (b'{"features":', b'{"features":[],"features":[]}', b'{"features":NaN}',
                       b'[' * 18 + b'0' + b']' * 18, b'{"features":[' + b'{},' * 65 + b'{}]}',
                       b'{"features":[],"extra":1e4097}'):
            with self.subTest(cuerpo=cuerpo[:40]):
                r = ejecutar(escenario(contenido=cuerpo))
                self.assertNotEqual(r.estado, EE.COHERENTE)
                self.assertIn(r.validacion, (EV.RECHAZADA, EV.LIMITADA))
                self.assertEqual(r.entidades, ())

    def test_64k_exactos_y_exceso_sin_hash_ni_parseo(self):
        inicial = escenario().respuesta.contenido
        completo = inicial + b' ' * (65_536 - len(inicial))
        self.assertEqual(ejecutar(escenario(contenido=completo)).estado, EE.COHERENTE)
        with patch("spica.adquisicion.piloto_arcgis.simulador.hashlib.sha256") as h, \
                patch("spica.adquisicion.piloto_arcgis.simulador.leer_json") as lector:
            r = ejecutar(escenario(contenido=completo + b' '))
        self.assertEqual((r.recepcion, r.validacion), (ER.EXCEDIDA, EV.LIMITADA))
        self.assertEqual(r.bytes_observados, 65_537)
        self.assertIsNone(r.sha256)
        self.assertIsNone(r.contenido)
        h.assert_not_called()
        lector.assert_not_called()

    def test_limite_reducido_tambien_se_respeta(self):
        r = SimuladorEnsayo(PreparacionEnsayo(max_bytes=5)).ejecutar(escenario())
        self.assertEqual(r.recepcion, ER.EXCEDIDA)

    def test_parcial_interrumpida_y_content_length_no_se_promueven(self):
        for cambio in (dict(codigo_http=206), dict(transferencia_completa=False), dict(interrumpida=True),
                       dict(longitud_declarada=1), dict(longitud_declarada=9999)):
            with self.subTest(cambio=cambio):
                r = ejecutar(escenario(**cambio))
                self.assertEqual((r.estado, r.recepcion, r.validacion), (EE.REVISION, ER.INCOMPLETA, EV.NO_REALIZADA))
                self.assertFalse(r.sintaxis_completa)
                self.assertEqual(r.entidades, ())
        esc = escenario()
        r = ejecutar(EscenarioSintetico(replace(esc.respuesta, longitud_declarada=len(esc.respuesta.contenido))))
        self.assertEqual(r.estado, EE.COHERENTE)

    def test_contrato_resultado_rechaza_evidencia_contradictoria(self):
        r = ejecutar()
        for cambio in (dict(codigo_http=206), dict(longitud_declarada=1), dict(sha256="0" * 64),
                       dict(bytes_observados=True), dict(sintaxis_completa=False), dict(entidades=()),
                       dict(recepcion=ER.SIN_RESPUESTA), dict(operaciones_simuladas=0)):
            with self.subTest(cambio=cambio), self.assertRaises(ValueError):
                replace(r, **cambio)

    def test_redireccion_y_estados_http_sin_segunda_operacion(self):
        for codigo in (301, 302, 307, 401, 403, 404, 429, 500, 503):
            with self.subTest(codigo=codigo):
                r = ejecutar(escenario(codigo_http=codigo))
                self.assertEqual(r.operaciones_simuladas, 1)
                self.assertEqual(r.estado, EE.REVISION)
                self.assertEqual(r.validacion, EV.NO_REALIZADA)
                self.assertFalse(r.sintaxis_completa)

    def test_mime_y_compresion_incompatibles(self):
        for cambio in (dict(content_type="text/html"), dict(content_encoding="gzip")):
            with self.subTest(cambio=cambio):
                r = ejecutar(replace(escenario(), **cambio))
                self.assertEqual(r.estado, EE.REVISION)
                self.assertEqual(r.validacion, EV.NO_REALIZADA)

    def test_fallos_de_conexion_y_timeout_sin_respuesta_inventada(self):
        for fallo in FalloSintetico:
            with self.subTest(fallo=fallo):
                r = ejecutar(EscenarioSintetico(fallo=fallo))
                self.assertEqual((r.estado, r.recepcion), (EE.FALLIDO, ER.SIN_RESPUESTA))
                self.assertIsNone(r.codigo_http)
                self.assertIsNone(r.contenido)
                self.assertIsNone(r.sha256)
                self.assertIsNone(r.bytes_observados)

    def test_cancelacion_previa_consume_ensayo_sin_intercambio(self):
        evento = Event()
        evento.set()
        sim = SimuladorEnsayo(PreparacionEnsayo())
        r = sim.ejecutar(escenario(), cancelacion=evento)
        self.assertEqual((r.estado, r.operaciones_simuladas), (EE.CANCELADO, 0))
        self.assertIsNone(r.contenido)
        with self.assertRaises(RuntimeError):
            sim.ejecutar(escenario())

    def test_cancelacion_durante_lectura_no_entrega_entidades(self):
        evento = Event()
        original = json.loads
        def cargar(*a, **kw):
            valor = original(*a, **kw)
            evento.set()
            return valor
        with patch("spica.adquisicion._json_acotado.json.loads", side_effect=cargar):
            r = ejecutar(cancelacion=evento)
        self.assertEqual(r.estado, EE.CANCELADO)
        self.assertEqual(r.entidades, ())

    def test_instancia_consumida_no_reintenta_ni_pagina(self):
        for esc in (escenario(), escenario(codigo_http=503), EscenarioSintetico(fallo=FalloSintetico.CONEXION)):
            sim = SimuladorEnsayo(PreparacionEnsayo())
            sim.ejecutar(esc)
            with self.subTest(esc=esc), self.assertRaisesRegex(RuntimeError, "sin_reintento"):
                sim.ejecutar(escenario())

    def test_transfer_limit_no_prueba_completitud_ni_habilita_continuacion(self):
        for flag in (True, False, None):
            d = sobre()
            if flag is not None:
                d["exceededTransferLimit"] = flag
            r = ejecutar(escenario(d))
            self.assertEqual(r.estado, EE.COHERENTE)
            self.assertEqual(r.exceeded_transfer_limit, flag)
            self.assertEqual(r.completitud_institucional, EstadoCompletitud.DESCONOCIDA)
        r = ejecutar(escenario(sobre(()) | dict(exceededTransferLimit=True)))
        self.assertEqual(r.validacion, EV.RECHAZADA)

    def test_simulador_no_usa_red_archivos_sqlite_o_http(self):
        with patch("socket.socket", side_effect=AssertionError("red")), \
                patch("builtins.open", side_effect=AssertionError("archivo")), \
                patch("sqlite3.connect", side_effect=AssertionError("sqlite")):
            self.assertEqual(ejecutar().estado, EE.COHERENTE)

    def test_importacion_sin_http_y_sin_backend_operativo_en_fuente(self):
        codigo = ("import sys; import spica.adquisicion.piloto_arcgis; "
                  "assert not any(x == 'httpx' or x.startswith('spica.adquisicion.transportes') "
                  "or x.startswith('spica.adquisicion.integracion') for x in sys.modules)")
        p = subprocess.run([sys.executable, "-B", "-c", codigo], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        paquete = Path(__file__).resolve().parents[1] / "src/spica/adquisicion/piloto_arcgis"
        for archivo in paquete.glob("*.py"):
            arbol = ast.parse(archivo.read_text(encoding="utf-8"))
            for nodo in ast.walk(arbol):
                if isinstance(nodo, (ast.Import, ast.ImportFrom)):
                    nombres = [nodo.module or ""] if isinstance(nodo, ast.ImportFrom) else [a.name for a in nodo.names]
                    self.assertFalse(any(x in n for n in nombres for x in ("httpx", "socket", "transportes", "integracion", "almacenamiento")))


if __name__ == "__main__":
    unittest.main()
