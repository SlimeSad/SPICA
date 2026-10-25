"""Pruebas del contrato; todos los identificadores y hashes son fixtures ficticios."""

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import unittest

# Permite probar el layout src sin instalar el proyecto ni modificar el entorno.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from spica.adquisicion.nucleo import (
    Descarga, EstadoDescarga, EstadoIntegridad, EstadoRecurso, Fuente, Integridad,
    RecursoDescubierto, ResultadoAdquisicion, ResultadoRecurso, SolicitudAdquisicion,
)


class ContratoAdquisicionTests(unittest.TestCase):
    def setUp(self):
        self.fuente = Fuente("proveedor-prueba", " Fuente-001 ")
        self.inicio = datetime(2026, 1, 1, tzinfo=timezone.utc)
        self.fin = self.inicio + timedelta(days=1)
        self.solicitud = SolicitudAdquisicion(self.fuente, self.inicio, self.fin)
        self.recurso = RecursoDescubierto(self.fuente, "Recurso-001", "localizador-prueba")
        self.descarga = Descarga(EstadoDescarga.COMPLETA, "archivo-prueba.bin", 3)
        self.integridad = Integridad(
            EstadoIntegridad.VERIFICADA, 3, "algoritmo-prueba",
            "hash-prueba", "hash-prueba", "manifiesto-prueba",
        )

    def test_solicitud_sin_estaciones_ni_variables(self):
        self.assertEqual(self.solicitud.estaciones, ())
        self.assertEqual(self.solicitud.variables, ())

    def test_multiples_identificadores_se_preservan_exactamente(self):
        solicitud = replace(self.solicitud, estaciones=(" E-01 ", "e-02"),
                            variables=("V/original", "variable-02"))
        self.assertEqual(solicitud.estaciones, (" E-01 ", "e-02"))
        self.assertEqual(solicitud.variables, ("V/original", "variable-02"))
        self.assertEqual(solicitud.fuente.identificador, " Fuente-001 ")

    def test_parametros_se_copian_y_no_se_pueden_mutar(self):
        parametros = {"clave-original": "valor-original"}
        solicitud = replace(self.solicitud, parametros_proveedor=parametros)
        parametros["clave-original"] = "cambiado"
        self.assertEqual(solicitud.parametros_proveedor["clave-original"], "valor-original")
        with self.assertRaises(TypeError):
            solicitud.parametros_proveedor["nuevo"] = "valor"

    def test_fechas_invalidas(self):
        for inicio, fin in ((self.fin, self.inicio),
                            (datetime(2026, 1, 1), self.fin),
                            (self.inicio, "2026-01-02")):
            with self.subTest(inicio=inicio, fin=fin), self.assertRaises(ValueError):
                SolicitudAdquisicion(self.fuente, inicio, fin)

    def test_instantes_iguales_y_zonas_distintas(self):
        fin = self.inicio.astimezone(timezone(timedelta(hours=-5)))
        self.assertEqual(replace(self.solicitud, fecha_final=fin).fecha_final, self.inicio)

    def test_identificadores_vacios_y_colecciones_incorrectas(self):
        for cambios in ({"estaciones": ("",)}, {"variables": (" ",)},
                        {"estaciones": "E-01"}, {"parametros_proveedor": {"x": 2}}):
            with self.subTest(cambios=cambios), self.assertRaises((ValueError, TypeError)):
                replace(self.solicitud, **cambios)
        with self.assertRaises(ValueError):
            Fuente("", "identificador")

    def test_recursos_de_formatos_abiertos_y_desconocidos(self):
        for formato in (None, "NetCDF", "GeoTIFF", "PDF", "ZIP", "formato-propio"):
            with self.subTest(formato=formato):
                recurso = replace(self.recurso, formato=formato)
                self.assertEqual(recurso.formato, formato)
                self.assertIsNone(recurso.tipo_medio)

    def test_descubrimiento_no_implica_descarga(self):
        resultado = ResultadoRecurso(self.recurso)
        self.assertEqual(resultado.estado, EstadoRecurso.DESCUBIERTO)
        self.assertIsNone(resultado.descarga.ruta_local)

    def test_descarga_sin_evidencia_no_se_confirma(self):
        resultado = ResultadoRecurso(self.recurso, self.descarga)
        self.assertEqual(resultado.estado, EstadoRecurso.DESCARGADO)
        self.assertEqual(resultado.integridad.estado, EstadoIntegridad.PENDIENTE)

    def test_confirmacion_con_evidencia_completa(self):
        resultado = ResultadoRecurso(self.recurso, self.descarga, self.integridad)
        self.assertEqual(resultado.estado, EstadoRecurso.CONFIRMADO)

    def test_rechaza_cada_evidencia_faltante(self):
        for campo in ("bytes_esperados", "algoritmo", "hash_esperado", "hash_observado",
                      "origen_evidencia"):
            with self.subTest(campo=campo), self.assertRaises(ValueError):
                replace(self.integridad, **{campo: None})

    def test_rechaza_hash_distinto_y_tamano_distinto(self):
        with self.assertRaises(ValueError):
            replace(self.integridad, hash_observado="otro-hash")
        with self.assertRaises(ValueError):
            ResultadoRecurso(self.recurso, self.descarga,
                             replace(self.integridad, bytes_esperados=4))

    def test_integridad_verificada_requiere_descarga_completa(self):
        with self.assertRaises(ValueError):
            ResultadoRecurso(self.recurso, integridad=self.integridad)

    def test_descarga_completa_requiere_ruta_y_tamano(self):
        for cambios in ({"ruta_local": None}, {"bytes_recibidos": None},
                        {"bytes_recibidos": -1}, {"bytes_recibidos": True},
                        {"error": "error-prueba"}):
            with self.subTest(cambios=cambios), self.assertRaises(ValueError):
                replace(self.descarga, **cambios)

    def test_archivo_vacio_puede_confirmarse_con_evidencia(self):
        resultado = ResultadoRecurso(self.recurso, replace(self.descarga, bytes_recibidos=0),
                                     replace(self.integridad, bytes_esperados=0))
        self.assertEqual(resultado.estado, EstadoRecurso.CONFIRMADO)

    def test_fallos_explicitos(self):
        descarga = Descarga(EstadoDescarga.FALLIDA, error="transferencia interrumpida")
        self.assertEqual(ResultadoRecurso(self.recurso, descarga).estado, EstadoRecurso.FALLIDO)
        integridad = replace(self.integridad, estado=EstadoIntegridad.FALLIDA,
                             hash_observado="otro-hash", error="hash diferente")
        self.assertEqual(ResultadoRecurso(self.recurso, self.descarga, integridad).estado,
                         EstadoRecurso.FALLIDO)
        for constructor, estado in ((Descarga, EstadoDescarga.FALLIDA),
                                    (Integridad, EstadoIntegridad.FALLIDA)):
            with self.assertRaises(ValueError):
                constructor(estado)

    def test_estados_son_enums_y_modelos_tipados(self):
        for constructor in (Descarga, Integridad):
            with self.assertRaises(TypeError):
                constructor("completa")
        with self.assertRaises(TypeError):
            ResultadoRecurso("recurso")

    def test_resultado_admite_estados_mixtos_y_errores(self):
        resultados = (ResultadoRecurso(self.recurso),
                      ResultadoRecurso(replace(self.recurso, identificador="Recurso-002"),
                                       self.descarga, self.integridad))
        resultado = ResultadoAdquisicion(self.solicitud, resultados, ("error de descubrimiento",))
        self.assertEqual([r.estado for r in resultado.recursos],
                         [EstadoRecurso.DESCUBIERTO, EstadoRecurso.CONFIRMADO])
        self.assertEqual(len(resultado.errores), 1)

    def test_resultado_vacio_no_declara_confirmacion(self):
        resultado = ResultadoAdquisicion(self.solicitud)
        self.assertEqual(resultado.recursos, ())
        self.assertEqual(resultado.errores, ())

    def test_resultado_rechaza_otra_fuente(self):
        recurso = replace(self.recurso, fuente=Fuente("otro-proveedor", "otra-fuente"))
        with self.assertRaises(ValueError):
            ResultadoAdquisicion(self.solicitud, (ResultadoRecurso(recurso),))

    def test_pendiente_solo_admite_cero_o_bytes_desconocidos_sin_ruta(self):
        for cantidad in (None, 0):
            resultado = ResultadoRecurso(self.recurso, Descarga(bytes_recibidos=cantidad))
            self.assertEqual(resultado.estado, EstadoRecurso.DESCUBIERTO)
        for cambios in ({"bytes_recibidos": 1}, {"ruta_local": "archivo"}, {"error": "fallo"}):
            with self.subTest(cambios=cambios), self.assertRaises(ValueError):
                Descarga(**cambios)

    def test_parcial_con_y_sin_tamano_esperado(self):
        descarga = Descarga(EstadoDescarga.PARCIAL, "archivo", 2)
        for esperado in (None, 2, 3):
            with self.subTest(esperado=esperado):
                resultado = ResultadoRecurso(self.recurso, descarga,
                                             Integridad(bytes_esperados=esperado))
                self.assertEqual(resultado.estado, EstadoRecurso.PARCIAL)

    def test_parcial_requiere_bytes_positivos_ruta_y_ausencia_de_error(self):
        parcial = Descarga(EstadoDescarga.PARCIAL, "archivo", 1)
        for cambios in ({"bytes_recibidos": None}, {"bytes_recibidos": 0},
                        {"ruta_local": None}, {"error": "fallo"}):
            with self.subTest(cambios=cambios), self.assertRaises(ValueError):
                replace(parcial, **cambios)

    def test_parcial_no_puede_exceder_tamano_esperado(self):
        with self.assertRaises(ValueError):
            ResultadoRecurso(self.recurso, Descarga(EstadoDescarga.PARCIAL, "archivo", 4),
                             Integridad(bytes_esperados=3))

    def test_completa_rechaza_tamano_distinto_incluso_con_integridad_pendiente(self):
        for esperado in (0, 2, 4):
            with self.subTest(esperado=esperado), self.assertRaises(ValueError):
                ResultadoRecurso(self.recurso, self.descarga, Integridad(bytes_esperados=esperado))

    def test_tamano_igual_sin_hash_no_confirma(self):
        for cantidad in (0, 3):
            resultado = ResultadoRecurso(self.recurso,
                replace(self.descarga, bytes_recibidos=cantidad), Integridad(bytes_esperados=cantidad))
            self.assertEqual(resultado.estado, EstadoRecurso.DESCARGADO)

    def test_fallo_transferencia_conserva_bytes_y_no_imputa_integridad(self):
        for cantidad in (0, 2, 3, 4):
            resultado = ResultadoRecurso(self.recurso,
                Descarga(EstadoDescarga.FALLIDA, "archivo", cantidad, "fallo transferencia"),
                Integridad(bytes_esperados=3))
            self.assertEqual(resultado.estado, EstadoRecurso.FALLIDO)
            self.assertEqual(resultado.integridad.estado, EstadoIntegridad.PENDIENTE)
        with self.assertRaises(ValueError):
            Descarga(EstadoDescarga.FALLIDA, bytes_recibidos=1, error="fallo")

    def test_integridad_fallida_exige_comparacion_contradictoria(self):
        for cambios in ({"hash_observado": None}, {"hash_observado": "hash-prueba"},
                        {"algoritmo": None}, {"hash_esperado": None},
                        {"origen_evidencia": None}, {"error": None}):
            datos = dict(estado=EstadoIntegridad.FALLIDA, bytes_esperados=3,
                         algoritmo="algoritmo-prueba", hash_esperado="hash-prueba",
                         hash_observado="otro-hash", origen_evidencia="manifiesto", error="discrepancia")
            datos.update(cambios)
            with self.subTest(cambios=cambios), self.assertRaises(ValueError):
                Integridad(**datos)

    def test_hashes_distintos_no_pueden_quedar_pendientes(self):
        with self.assertRaises(ValueError):
            replace(self.integridad, estado=EstadoIntegridad.PENDIENTE, hash_observado="otro")

    def test_verificacion_no_es_pertinente_sin_descarga_completa(self):
        descargas = (Descarga(), Descarga(EstadoDescarga.PARCIAL, "archivo", 1),
                     Descarga(EstadoDescarga.FALLIDA, error="fallo"))
        evidencias = (self.integridad,
                     replace(self.integridad, estado=EstadoIntegridad.PENDIENTE),
                     replace(self.integridad, estado=EstadoIntegridad.FALLIDA,
                             hash_observado="otro", error="discrepancia"))
        for descarga in descargas:
            for evidencia in evidencias:
                with self.subTest(descarga=descarga.estado, integridad=evidencia.estado), self.assertRaises(ValueError):
                    ResultadoRecurso(self.recurso, descarga, evidencia)

    def test_hashes_coincidentes_pendientes_no_confirman(self):
        resultado = ResultadoRecurso(self.recurso, self.descarga,
                                    replace(self.integridad, estado=EstadoIntegridad.PENDIENTE))
        self.assertEqual(resultado.estado, EstadoRecurso.DESCARGADO)

    def test_bytes_invalidos_en_descarga_e_integridad(self):
        for cantidad in (-1, True, 1.5, "3"):
            for constructor, campo in ((Descarga, "bytes_recibidos"),
                                       (Integridad, "bytes_esperados")):
                with self.subTest(cantidad=cantidad, campo=campo), self.assertRaises(ValueError):
                    constructor(**{campo: cantidad})


if __name__ == "__main__":
    unittest.main()
