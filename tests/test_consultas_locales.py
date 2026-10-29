"""Solo fixtures sintéticas, temporales aislados y ninguna conexión externa."""

import csv
from dataclasses import replace
from datetime import date, datetime, timezone
import hashlib
from pathlib import Path
import shutil
import sys
import tempfile
from threading import Event
import tracemalloc
import unittest
from unittest.mock import patch
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from spica.adquisicion.nucleo import Fuente
from spica.adquisicion.consultas_locales import (
    ConsultaLocal, ConsultorLocalCSV, ENCABEZADO_SENAMHI as CAB, LimitesConsulta,
    LimitesDiagnostico, ProcedenciaLocal, diagnosticar_csv,
)
from spica.adquisicion.verificacion import PoliticaLecturaCSV


class ConsultasLocalesTests(unittest.TestCase):
    def setUp(self):
        padre = Path(tempfile.gettempdir()).resolve()
        self.base = padre / ("spica-local-test-" + uuid4().hex)
        self.base.mkdir(mode=0o755)
        assert self.base.resolve().is_relative_to(padre)
        self.addCleanup(shutil.rmtree, self.base)
        datos = self.base / "datos"
        datos.mkdir()
        self.ruta = datos / "sintetico.csv"
        self.indices = self.base / "indices"
        self.indices.mkdir()
        self.procedencia = ProcedenciaLocal(Fuente("SENAMHI", "SENAMHI"), "recurso-sintetico", "activo-sintetico")
        self.consulta = ConsultaLocal(("IMATA",), ("TEMP",), date(2015, 1, 1), date(2015, 1, 3))
        self.escribir(self.fila())

    def fila(self, **cambios):
        valores = dict(zip(CAB, ("0001", "IMATA", "20150101", "00000", "-71.0906",
            "-15.8427", "4475.0", "01.20", "90.0", "", "RBON", "AREQUIPA", "CAYLLOMA",
            "SAN ANTONIO DE CHUCA", "40514.0", "20240630")))
        valores.update(cambios)
        return tuple(valores[c] for c in CAB)

    def escribir(self, *filas, cabecera=CAB):
        with self.ruta.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(cabecera)
            w.writerows(filas)

    def consultar(self, consulta=None, **opciones):
        with ConsultorLocalCSV(self.ruta, consulta or self.consulta, self.procedencia, **opciones) as c:
            resultados = tuple(c)
        return resultados, c.informe

    def diagnosticar(self, **opciones):
        r = diagnosticar_csv(self.ruta, self.procedencia, directorio_temporal=self.indices, **opciones)
        self.assertEqual(tuple(self.indices.iterdir()), ())
        return r

    def test_estacion_existente_procedencia_y_campos_originales(self):
        filas, r = self.consultar()
        self.assertTrue(r.completa)
        self.assertEqual((r.resultados, r.filas_coincidentes), (1, 1))
        self.assertEqual(filas[0].procedencia, self.procedencia)
        self.assertEqual(tuple(v for _, v in filas[0].campos_originales), self.fila())
        self.assertEqual((filas[0].numero_registro, filas[0].linea_inicial), (2, 2))

    def test_estacion_inexistente_solo_ausencia_local_tras_eof(self):
        filas, r = self.consultar(replace(self.consulta, estaciones=("NO_EXISTE",)))
        self.assertEqual(filas, ())
        self.assertTrue(r.ausencia_comprobada)

    def test_nombres_similares_no_equivalentes(self):
        self.escribir(*(self.fila(ESTACION=e) for e in ("imata", "IMATA ", "IMATA_2", "IMATA")))
        filas, r = self.consultar()
        self.assertEqual(len(filas), 1)
        self.assertEqual(filas[0].numero_registro, 5)
        self.assertTrue(r.completa)

    def test_multivariable_multiestacion_solo_asociaciones_reales(self):
        self.escribir(self.fila(), self.fila(ESTACION="OTRA", TEMP="", HR="77", PP="0"))
        c = replace(self.consulta, estaciones=("IMATA", "OTRA", "AUSENTE"), variables=("PP", "TEMP", "HR"))
        filas, r = self.consultar(c)
        self.assertEqual([x.variable for x in filas], ["PP", "TEMP", "HR"] * 2)
        self.assertEqual([x.valor for x in filas], ["", "01.20", "90.0", "0", "", "77"])
        self.assertEqual((r.resultados, r.filas_coincidentes), (6, 2))

    def test_variables_no_admitidas(self):
        for variable in ("temp", "O3", "ID", "UBIGEO", "TEMP "):
            with self.subTest(variable=variable), self.assertRaises(ValueError):
                replace(self.consulta, variables=(variable,))

    def test_selecciones_vacias_duplicadas_y_excesivas(self):
        for cambios in (dict(estaciones=()), dict(variables=()), dict(estaciones=("IMATA", "IMATA")),
                        dict(variables=("TEMP", "TEMP")), dict(estaciones=("X",) * 129),
                        dict(estaciones="IMATA"), dict(estaciones=(" ",)), dict(estaciones=("x" * 257,))):
            with self.subTest(cambios=cambios), self.assertRaises(ValueError):
                replace(self.consulta, **cambios)

    def test_fechas_inclusivas_y_fuera_intervalo(self):
        self.escribir(*(self.fila(FECHA=d) for d in ("20141231", "20150101", "20150103", "20150104")))
        filas, r = self.consultar()
        self.assertEqual([dict(f.campos_originales)["FECHA"] for f in filas], ["20150101", "20150103"])
        self.assertTrue(r.completa)

    def test_intervalo_invertido(self):
        with self.assertRaises(ValueError):
            replace(self.consulta, fecha_inicial=date(2015, 1, 4))

    def test_solicitud_rechaza_strings_datetime_y_fechas_invalidas(self):
        for valor in ("2015-01-01", None, datetime(2015, 1, 1), datetime(2015, 1, 1, tzinfo=timezone.utc)):
            with self.subTest(valor=valor), self.assertRaises(TypeError):
                replace(self.consulta, fecha_inicial=valor)
        with self.assertRaises(ValueError):
            date(2015, 2, 29)

    def test_fechas_invalidas_en_datos_impiden_ausencia(self):
        for texto in ("20150229", "20151301", "2015011", "２０１５０１０１", "2015-01-01", ""):
            with self.subTest(texto=texto):
                self.escribir(self.fila(FECHA=texto))
                filas, r = self.consultar(codificacion="utf-8")
                self.assertEqual(filas, ())
                self.assertEqual(r.fechas_invalidas, 1)
                self.assertFalse(r.completa or r.ausencia_comprobada)
                self.assertEqual(r.motivo_fin, "fechas_civiles_invalidas")

    def test_dia_bisiesto_civil_valido(self):
        self.escribir(self.fila(FECHA="20160229"))
        c = replace(self.consulta, fecha_inicial=date(2016, 2, 29), fecha_final=date(2016, 2, 29))
        filas, r = self.consultar(c)
        self.assertEqual(filas[0].fecha_civil, date(2016, 2, 29))
        self.assertTrue(r.completa)

    def test_vacios_y_espacios_no_son_equivalentes(self):
        self.escribir(self.fila(TEMP="", HR=" ", PP="0"))
        filas, _ = self.consultar(replace(self.consulta, variables=("TEMP", "HR", "PP")))
        self.assertEqual([(r.valor, r.presente) for r in filas], [("", False), (" ", True), ("0", True)])

    def test_ids_repetidos_no_deduplican_observaciones(self):
        self.escribir(self.fila(), self.fila())
        filas, _ = self.consultar()
        self.assertEqual([dict(f.campos_originales)["ID"] for f in filas], ["0001", "0001"])

    def test_horas_ubigeo_y_textos_se_conservan_sin_conversion(self):
        self.escribir(self.fila(HORA="00000", UBIGEO="40514.0", TEMP=" -999.0 "),
                      self.fila(HORA="000000", UBIGEO="040514", TEMP="NaN"))
        filas, _ = self.consultar()
        self.assertEqual([dict(f.campos_originales)["HORA"] for f in filas], ["00000", "000000"])
        self.assertEqual([dict(f.campos_originales)["UBIGEO"] for f in filas], ["40514.0", "040514"])
        self.assertEqual([f.valor for f in filas], [" -999.0 ", "NaN"])

    def test_limite_resultados_incluso_si_coincide_con_ultimo(self):
        filas, r = self.consultar(limites=LimitesConsulta(max_resultados=1))
        self.assertEqual(len(filas), 1)
        self.assertEqual(r.motivo_fin, "limite_resultados")
        self.assertFalse(r.completa or r.ausencia_comprobada)

    def test_limite_puede_cortar_variables_de_una_fila(self):
        filas, r = self.consultar(replace(self.consulta, variables=("HR", "PP", "TEMP")),
                                  limites=LimitesConsulta(max_resultados=2))
        self.assertEqual([f.variable for f in filas], ["HR", "PP"])
        self.assertFalse(r.completa)

    def test_cancelacion_antes_de_leer_no_declara_ausencia(self):
        evento = Event()
        evento.set()
        filas, r = self.consultar(cancelacion=evento)
        self.assertEqual(filas, ())
        self.assertEqual(r.motivo_fin, "cancelado")
        self.assertFalse(r.ausencia_comprobada)

    def test_cancelacion_entre_variables_pendientes(self):
        with ConsultorLocalCSV(self.ruta, replace(self.consulta, variables=("TEMP", "HR")), self.procedencia) as c:
            next(c)
            c.cancelar()
            self.assertEqual(tuple(c), ())
        self.assertEqual(c.informe.motivo_fin, "cancelado")
        self.assertFalse(c.informe.completa)

    def test_break_cierra_y_mantiene_incompleta(self):
        with ConsultorLocalCSV(self.ruta, self.consulta, self.procedencia) as c:
            for _ in c:
                break
        self.assertFalse(c.informe.completa)
        self.assertEqual(c.informe.motivo_fin, "consumidor_detuvo_lectura")
        self.assertIsNone(c._filas.lector._archivo)

    def test_interrupcion_del_consumidor_cierra(self):
        with self.assertRaises(KeyboardInterrupt):
            with ConsultorLocalCSV(self.ruta, self.consulta, self.procedencia) as c:
                next(c)
                raise KeyboardInterrupt()
        self.assertFalse(c.informe.completa)
        self.assertEqual(c.informe.motivo_fin, "consumidor_interrumpido")
        self.assertIsNone(c._filas.lector._archivo)

    def test_limite_registros_fuente_impide_ausencia(self):
        filas, r = self.consultar(replace(self.consulta, estaciones=("AUSENTE",)),
            limites=LimitesConsulta(lectura=PoliticaLecturaCSV(max_registros=1)))
        self.assertEqual(filas, ())
        self.assertEqual(r.motivo_fin, "limite_registros")
        self.assertFalse(r.ausencia_comprobada)

    def test_limite_bytes_fuente(self):
        _, r = self.consultar(limites=LimitesConsulta(lectura=PoliticaLecturaCSV(max_bytes_archivo=10)))
        self.assertEqual(r.motivo_fin, "limite_bytes_archivo")
        self.assertFalse(r.completa)

    def test_encabezado_ajeno_o_reordenado_no_se_interpreta(self):
        self.escribir(self.fila(), cabecera=tuple(reversed(CAB)))
        filas, r = self.consultar()
        self.assertEqual(filas, ())
        self.assertEqual(r.motivo_fin, "encabezado_no_admitido")
        self.assertFalse(r.ausencia_comprobada)

    def test_fila_corta_no_crea_asociaciones(self):
        self.escribir(self.fila()[:7])
        filas, r = self.consultar()
        self.assertEqual(filas, ())
        self.assertFalse(r.completa or r.ausencia_comprobada)
        self.assertEqual(r.motivo_fin, "estructura_no_compatible")

    def test_archivo_modificado_durante_consulta_invalida_informe(self):
        with ConsultorLocalCSV(self.ruta, self.consulta, self.procedencia) as c:
            next(c)
            with self.ruta.open("ab") as f:
                f.write(b"\n")
            tuple(c)
        self.assertFalse(c.informe.completa)
        self.assertEqual(c.informe.lectura.motivo_fin, "archivo_modificado_durante_lectura")

    def test_resultados_reproducibles_y_original_intacto(self):
        antes = hashlib.sha256(self.ruta.read_bytes()).digest(), self.ruta.stat().st_mtime_ns
        a, ra = self.consultar()
        b, rb = self.consultar()
        self.assertEqual(a, b)
        self.assertTrue(ra.completa and rb.completa)
        self.assertEqual(antes, (hashlib.sha256(self.ruta.read_bytes()).digest(), self.ruta.stat().st_mtime_ns))

    def test_uso_exige_contexto_y_no_reutiliza_operacion(self):
        c = ConsultorLocalCSV(self.ruta, self.consulta, self.procedencia)
        with self.assertRaises(RuntimeError):
            next(c)
        with c:
            tuple(c)
        with self.assertRaises(RuntimeError):
            c.__enter__()

    def test_validacion_presupuestos_y_procedencia(self):
        for valor in (0, -1, True, 2_000_001):
            with self.subTest(valor=valor), self.assertRaises(ValueError):
                LimitesConsulta(max_resultados=valor)
        with self.assertRaises(TypeError):
            LimitesConsulta(lectura=object())
        with self.assertRaises(ValueError):
            replace(self.procedencia, asset_id="")
        with self.assertRaises(ValueError):
            replace(self.procedencia, sha256_declarado="no-verificado")

    def test_lectura_grande_secuencial_y_memoria_acotada(self):
        picos = []
        for cantidad in (1000, 15000):
            with self.ruta.open("w", newline="", encoding="ascii") as f:
                w = csv.writer(f)
                w.writerow(CAB)
                for _ in range(cantidad):
                    w.writerow(self.fila())
            tracemalloc.start()
            try:
                with ConsultorLocalCSV(self.ruta, self.consulta, self.procedencia,
                        limites=LimitesConsulta(max_resultados=20000)) as c:
                    self.assertEqual(sum(1 for _ in c), cantidad)
                picos.append(tracemalloc.get_traced_memory()[1])
            finally:
                tracemalloc.stop()
            self.assertTrue(c.informe.completa)
        self.assertGreater(self.ruta.stat().st_size, 1_048_576)
        self.assertLess(max(picos), 4 * 1024**2)
        self.assertLess(picos[1], picos[0] + 1024**2)

    def test_diagnostico_patrones_y_relaciones_literales(self):
        self.escribir(self.fila(), self.fila(HORA="000000", UBIGEO="040514"),
                      self.fila(HORA="240000", UBIGEO="otro"), self.fila(HORA="x", UBIGEO=""))
        r = self.diagnosticar()
        self.assertTrue(r.completo and r.temporal_eliminado)
        self.assertEqual(dict(r.horas_por_longitud), {5: 1, 6: 2, 1: 1})
        self.assertEqual(dict(r.horas_por_patron), {"cinco_digitos_no_hhmmss": 1,
            "hhmmss_lexicamente_valido": 1, "seis_digitos_fuera_de_rango": 1, "otro_literal": 1})
        self.assertEqual(dict(r.ubigeos_por_patron)["digitos_con_sufijo_decimal_punto_cero"], 1)
        self.assertEqual({v[0][1] for v in r.relaciones_ubicacion}, {"40514.0", "040514", "otro", ""})

    def test_diagnostico_duplicados_exactos_desordenados(self):
        self.escribir(self.fila(), self.fila(FECHA="20150102"), self.fila(), self.fila(),
                      self.fila(HORA="000000"), self.fila(ESTACION="OTRA"))
        r = self.diagnosticar()
        self.assertEqual((r.claves_distintas, r.claves_repetidas, r.repeticiones_adicionales), (4, 1, 2))
        self.assertEqual(r.ejemplos_duplicados, (("IMATA", "20150101", "00000"),))
        self.assertEqual(r.filas_procesadas, 6)

    def test_diagnostico_horas_cinco_y_seis_no_se_fusionan(self):
        self.escribir(self.fila(), self.fila(HORA="000000"))
        r = self.diagnosticar()
        self.assertEqual(r.claves_repetidas, 0)
        self.assertEqual(dict(r.horas_literales), {"00000": 1, "000000": 1})

    def test_diagnostico_limite_horas_no_presenta_total(self):
        self.escribir(self.fila(), self.fila(HORA="010000"))
        r = self.diagnosticar(limites=LimitesDiagnostico(max_horas=1))
        self.assertFalse(r.completo)
        self.assertEqual((r.motivo_fin, r.filas_procesadas), ("limite_horas_distintas", 1))

    def test_diagnostico_limite_relaciones(self):
        self.escribir(self.fila(), self.fila(LONGITUD="-71.1"))
        r = self.diagnosticar(limites=LimitesDiagnostico(max_relaciones=1))
        self.assertEqual(r.motivo_fin, "limite_relaciones_ubicacion")
        self.assertFalse(r.completo)

    def test_diagnostico_limite_claves_y_repeticion_no_consume_clave(self):
        self.escribir(self.fila(), self.fila(), self.fila(HORA="010000"))
        r = self.diagnosticar(limites=LimitesDiagnostico(max_claves_temporales=1))
        self.assertEqual((r.motivo_fin, r.filas_procesadas, r.repeticiones_adicionales),
                         ("limite_claves_temporales", 2, 1))
        self.assertFalse(r.completo)

    def test_diagnostico_longitud_agregados(self):
        self.escribir(self.fila(ESTACION="x" * 30))
        r = self.diagnosticar(limites=LimitesDiagnostico(max_caracteres_literal=25))
        self.assertEqual(r.motivo_fin, "limite_longitud_agregados")
        self.assertFalse(r.completo)

    def test_diagnostico_ejemplos_acotados_sin_truncar_conteos(self):
        self.escribir(self.fila(), self.fila(), self.fila(HORA="010000"), self.fila(HORA="010000"))
        r = self.diagnosticar(limites=LimitesDiagnostico(max_ejemplos=1))
        self.assertEqual((len(r.ejemplos_duplicados), r.claves_repetidas), (1, 2))
        self.assertTrue(r.completo)
        self.assertEqual(len(r.ejemplos_vacios), 1)

    def test_diagnostico_fecha_invalida_no_implica_instante_duplicado(self):
        self.escribir(self.fila(FECHA="sin-fecha"), self.fila(FECHA="sin-fecha"))
        r = self.diagnosticar()
        self.assertFalse(r.completo)
        self.assertEqual((r.fechas_invalidas, r.claves_repetidas), (2, 1))
        self.assertIsNone(r.fecha_minima)

    def test_diagnostico_cancelado_limpia(self):
        evento = Event()
        evento.set()
        r = self.diagnosticar(cancelacion=evento)
        self.assertFalse(r.completo)
        self.assertEqual(r.motivo_fin, "cancelado")

    def test_diagnostico_interrumpido_limpia_y_propaga(self):
        with patch("spica.adquisicion.consultas_locales.diagnostico._patron_hora", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.diagnosticar()
        self.assertEqual(tuple(self.indices.iterdir()), ())

    def test_diagnostico_sin_espacio_no_crea_temporales(self):
        with patch("spica.adquisicion.consultas_locales.diagnostico.shutil.disk_usage") as uso:
            uso.return_value.free = 0
            r = self.diagnosticar()
        self.assertEqual(r.motivo_fin, "espacio_temporal_insuficiente")
        self.assertTrue(r.temporal_eliminado)

    def test_diagnostico_error_sqlite_no_filtra_rutas(self):
        import sqlite3
        with patch("spica.adquisicion.consultas_locales.diagnostico.sqlite3.connect",
                   side_effect=sqlite3.OperationalError("secreto/ruta")):
            r = self.diagnosticar()
        self.assertEqual(r.motivo_fin, "indice_temporal_no_disponible_o_limite_bytes")
        self.assertNotIn("secreto", repr(r))

    def test_diagnostico_limite_disco_real(self):
        self.escribir(*(self.fila(ESTACION="E" + str(i), HORA=str(i)) for i in range(300)))
        r = self.diagnosticar(limites=LimitesDiagnostico(max_bytes_indice=8192, max_horas=512))
        self.assertFalse(r.completo)
        self.assertEqual(r.motivo_fin, "indice_temporal_no_disponible_o_limite_bytes")
        self.assertTrue(r.temporal_eliminado)

    def test_diagnostico_presupuestos_invalidos(self):
        for cambios in (dict(max_horas=True), dict(max_bytes_indice=4096), dict(max_relaciones=4097),
                        dict(max_ejemplos=0), dict(max_caracteres_literal=513)):
            with self.subTest(cambios=cambios), self.assertRaises(ValueError):
                LimitesDiagnostico(**cambios)

    def test_fechas_invalidas_largas_no_ocupan_cache(self):
        from spica.adquisicion.consultas_locales.consulta import _fecha_civil, _fecha_aaaammdd
        _fecha_aaaammdd.cache_clear()
        for i in range(100):
            self.assertIsNone(_fecha_civil(str(i) + "x" * 10000))
        self.assertEqual(_fecha_aaaammdd.cache_info().currsize, 0)

    def test_diagnostico_y_consulta_preservan_fuente(self):
        antes = self.ruta.read_bytes(), self.ruta.stat().st_mtime_ns
        r = self.diagnosticar()
        self.consultar()
        self.assertTrue(r.completo)
        self.assertEqual(antes, (self.ruta.read_bytes(), self.ruta.stat().st_mtime_ns))

    def test_diagnostico_rechaza_temporales_junto_a_fuente(self):
        r = diagnosticar_csv(self.ruta, self.procedencia, directorio_temporal=self.ruta.parent)
        self.assertEqual(r.motivo_fin, "directorio_temporal_no_admitido")
        self.assertEqual(tuple(self.ruta.parent.iterdir()), (self.ruta,))

    def test_diagnostico_no_borra_directorio_que_no_creo(self):
        class UUIDFijo:
            hex = "colision-sintetica"
        carpeta = self.indices / "spica-diagnostico-colision-sintetica"
        carpeta.mkdir()
        protegido = carpeta / "indice.sqlite3"
        protegido.write_bytes(b"ajeno")
        with patch("spica.adquisicion.consultas_locales.diagnostico.uuid4", return_value=UUIDFijo()):
            r = diagnosticar_csv(self.ruta, self.procedencia, directorio_temporal=self.indices)
        self.assertFalse(r.completo)
        self.assertEqual(protegido.read_bytes(), b"ajeno")

    def test_diagnostico_encabezado_incompatible_no_produce_agregados(self):
        self.escribir(self.fila(), cabecera=tuple(reversed(CAB)))
        r = self.diagnosticar()
        self.assertFalse(r.completo)
        self.assertEqual((r.motivo_fin, r.filas_procesadas), ("encabezado_no_admitido", 0))

    def test_no_ascii_sin_evidencia_conserva_incertidumbre(self):
        self.escribir(self.fila(DISTRITO="ESTACIÓN"))
        filas, r = self.consultar()
        self.assertEqual(len(filas), 1)
        self.assertFalse(r.completa)
        self.assertFalse(r.lectura.codificacion_confirmada)
        _, confirmado = self.consultar(codificacion="utf-8")
        self.assertTrue(confirmado.completa)

    def test_diagnostico_error_limpieza_explicito(self):
        original = Path.rmdir
        def falla(ruta):
            if ruta.name.startswith("spica-diagnostico-"):
                raise PermissionError("no borrar")
            return original(ruta)
        with patch.object(Path, "rmdir", falla):
            r = diagnosticar_csv(self.ruta, self.procedencia, directorio_temporal=self.indices)
        self.assertFalse(r.completo or r.temporal_eliminado)
        self.assertEqual(r.motivo_fin, "limpieza_temporal_fallida")
        for carpeta in self.indices.iterdir():
            carpeta.rmdir()  # Solo el directorio vacío propio de esta fixture.


if __name__ == "__main__":
    unittest.main()
