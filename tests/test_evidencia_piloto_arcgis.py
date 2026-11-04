"""Persistencia efímera y física exclusivamente de bytes inventados en la prueba."""

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_piloto_arcgis import ejecutar, escenario
from spica.adquisicion.piloto_arcgis import (
    conservar_evidencia, ErrorEvidenciaEnsayo, EscenarioSintetico, FalloSintetico,
    EstadoRecepcion,
)


class EvidenciaPilotoTests(unittest.TestCase):
    def test_bytes_y_registro_reabiertos_hash_exacto_y_limpieza(self):
        r = ejecutar()
        with conservar_evidencia(r) as evidencia:
            d = evidencia.directorio
            self.assertNotIn(Path.cwd(), d.parents)
            self.assertEqual(evidencia.cuerpo.read_bytes(), r.contenido)
            self.assertTrue(evidencia.cuerpo_verificado_fisicamente)
            datos = evidencia.registro.read_bytes()
            registro = json.loads(datos)
            self.assertEqual(evidencia.sha256_registro, hashlib.sha256(datos).hexdigest())
            self.assertEqual(registro["sha256_bytes_sinteticos"], hashlib.sha256(evidencia.cuerpo.read_bytes()).hexdigest())
            self.assertEqual(registro["oid_observados_en_fixture"], [9_007_199_254_740_993])
            self.assertEqual(registro["solicitud_exacta_simulada"]["parametros"], dict(r.solicitud.preparacion.parametros))
            self.assertEqual(registro["procedencia"], "fixture_sintetica")
            self.assertEqual(registro["ensayo_id"], "ensayo-sintetico-prueba")
            self.assertFalse(registro["capacidad_institucional_demostrada"])
            self.assertFalse(registro["tls_ejercido"])
            self.assertIn("pendiente", registro["candidato_solo_declarativo"]["autorizacion"])
            self.assertNotIn("asset_id", registro)
            self.assertNotIn("adquisicion_id", registro)
            self.assertLessEqual(len(datos), 32_768)
            self.assertEqual(sorted(x.name for x in d.iterdir()), ["registro.json", "respuesta.bin"])
        self.assertFalse(d.exists())

    def test_parcial_verificada_fisicamente_no_se_declara_recepcion_completa(self):
        r = ejecutar(escenario(transferencia_completa=False))
        with conservar_evidencia(r) as e:
            registro = json.loads(e.registro.read_bytes())
            self.assertTrue(e.cuerpo_verificado_fisicamente)
            self.assertEqual(registro["recepcion"], EstadoRecepcion.INCOMPLETA.value)
            self.assertFalse(registro["sintaxis_completa"])
            self.assertEqual(registro["oid_observados_en_fixture"], [])

    def test_sin_respuesta_o_exceso_no_inventa_hash_archivo_o_verificacion(self):
        for r in (ejecutar(EscenarioSintetico(fallo=FalloSintetico.CONEXION)),
                  ejecutar(escenario(contenido=b'x' * 65_537))):
            with self.subTest(recepcion=r.recepcion), conservar_evidencia(r) as e:
                registro = json.loads(e.registro.read_bytes())
                self.assertIsNone(e.cuerpo)
                self.assertFalse(e.cuerpo_verificado_fisicamente)
                self.assertIsNone(registro["sha256_bytes_sinteticos"])
                self.assertIsNone(registro["archivo_cuerpo"])
                self.assertEqual(registro["bytes_observados"], r.bytes_observados)
                self.assertEqual([x.name for x in e.directorio.iterdir()], ["registro.json"])

    def test_interrupcion_en_contexto_limpia_sin_borrar_evidencia_ajena(self):
        with tempfile.TemporaryDirectory(prefix="spica-test-83c-") as padre:
            ajeno = Path(padre) / "ajeno.txt"
            ajeno.write_bytes(b"ajeno inventado")
            with patch("spica.adquisicion.piloto_arcgis.evidencia.tempfile.gettempdir", return_value=padre):
                with self.assertRaises(KeyboardInterrupt):
                    with conservar_evidencia(ejecutar()) as e:
                        d = e.directorio
                        raise KeyboardInterrupt()
            self.assertFalse(d.exists())
            self.assertEqual(ajeno.read_bytes(), b"ajeno inventado")

    def test_error_de_escritura_es_sanitizado_y_limpia_temporal_propio(self):
        abrir = Path.open
        def falla(p, *a, **kw):
            if p.name == "respuesta.bin":
                raise OSError("ruta privada y token secreto no mostrar")
            return abrir(p, *a, **kw)
        with tempfile.TemporaryDirectory(prefix="spica-test-83c-") as padre:
            with patch("spica.adquisicion.piloto_arcgis.evidencia.tempfile.gettempdir", return_value=padre), \
                    patch.object(Path, "open", falla):
                with self.assertRaisesRegex(ErrorEvidenciaEnsayo, "^error_evidencia_temporal_sintetica$"):
                    with conservar_evidencia(ejecutar()):
                        self.fail("no debe entregar evidencia")
            self.assertEqual(list(Path(padre).iterdir()), [])

    def test_corrupcion_fisica_detectada_y_no_promovida(self):
        leer = Path.read_bytes
        def corrupcion(p):
            contenido = leer(p)
            return contenido + b'x' if p.name == "respuesta.bin" else contenido
        with patch.object(Path, "read_bytes", corrupcion):
            with self.assertRaisesRegex(ErrorEvidenciaEnsayo, "comprobacion_fisica_sintetica_fallida"):
                with conservar_evidencia(ejecutar()):
                    self.fail("no debe confirmar bytes distintos")

    def test_hash_o_tamano_falsos_se_rechazan_antes_de_escribir(self):
        r = ejecutar()
        for cambio in (dict(sha256="0" * 64), dict(bytes_observados=1), dict(contenido=None)):
            with self.subTest(cambio=cambio), \
                    patch("spica.adquisicion.piloto_arcgis.evidencia._base_temporal") as base:
                with self.assertRaises(ValueError):
                    with conservar_evidencia(replace(r, **cambio)):
                        self.fail("no debe conservar metadatos contradictorios")
                base.assert_not_called()

    def test_destino_no_configurable_y_prohibicion_lexica_previa_a_stat(self):
        r = ejecutar()
        with self.assertRaises(TypeError):
            conservar_evidencia(r, destino="otro")
        ubicaciones = (str(Path.home() / "SPICA_DATOS" / "raw"),
                       str(Path.cwd() / "temporales"), r"\\servidor.invalid\share\temp",
                       str(Path.cwd() / ".git" / "evidencia"),
                       str(Path.cwd() / ".venv" / "evidencia"), "relativo")
        for ubicacion in ubicaciones:
            with self.subTest(ubicacion=ubicacion), \
                    patch("spica.adquisicion.piloto_arcgis.evidencia.tempfile.gettempdir", return_value=ubicacion), \
                    patch.object(Path, "is_symlink", side_effect=AssertionError("no inspeccionar")):
                with self.assertRaisesRegex(ErrorEvidenciaEnsayo, "base_temporal_no_admitida"):
                    with conservar_evidencia(r):
                        self.fail("no debe inspeccionar ni crear un destino protegido")

    def test_junction_o_symlink_temporal_rechazado(self):
        for metodo in ("is_symlink", "is_junction"):
            with self.subTest(metodo=metodo), patch.object(Path, metodo, return_value=True):
                with self.assertRaisesRegex(ErrorEvidenciaEnsayo, "base_temporal_con_enlace"):
                    with conservar_evidencia(ejecutar()):
                        self.fail("no debe seguir enlaces")

    def test_temporales_exclusivos_incluso_mismo_ensayo(self):
        r = ejecutar()
        with conservar_evidencia(r) as primero:
            a = primero.directorio
            bytes_antes = primero.cuerpo.read_bytes()
            with conservar_evidencia(r) as segundo:
                b = segundo.directorio
                self.assertNotEqual(a, b)
                self.assertEqual(primero.cuerpo.read_bytes(), bytes_antes)
            self.assertTrue(a.exists())
            self.assertFalse(b.exists())
        self.assertFalse(a.exists())


if __name__ == "__main__":
    unittest.main()
