"""Fixtures sintéticas exclusivamente; nunca accede a RAW ni a SQLite operativo."""

from dataclasses import asdict, replace
import csv
from decimal import Decimal, localcontext
import hashlib
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
from threading import Event
import tracemalloc
import unittest
from unittest.mock import patch
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from spica.adquisicion.catalogo import EvidenciaDocumental
from spica.adquisicion.consultas_locales import ENCABEZADO_SENAMHI as CAB, ProcedenciaLocal
from spica.adquisicion.nucleo import Fuente
from spica.adquisicion.verificacion import PoliticaLecturaCSV
from spica.perfilado import LimitesPerfil, perfilar_csv


class PerfilMeteorologicoTests(unittest.TestCase):
    def setUp(self):
        padre = Path(tempfile.gettempdir()).resolve()
        self.base = padre / ("spica-perfil-test-" + uuid4().hex)
        self.base.mkdir(mode=0o755)
        assert self.base.resolve().is_relative_to(padre)
        self.addCleanup(shutil.rmtree, self.base)
        (self.base / "datos").mkdir()
        self.ruta = self.base / "datos" / "sintetico.csv"
        self.indices = self.base / "indices"
        self.indices.mkdir()
        self.procedencia = ProcedenciaLocal(Fuente("SENAMHI", "SENAMHI"), "recurso-sintetico", "activo-sintetico")
        self.escribir(self.fila())

    def fila(self, **cambios):
        valores = dict(zip(CAB, ("0001", "IMATA", "20150101", "00000", "-71.0906",
            "-15.8427", "4475.0", "01.20", "90.0", "", "RBON", "AREQUIPA", "CAYLLOMA",
            "SAN_ANTONIO_DE_CHUCA", "40514.0", "20240630")))
        valores.update(cambios)
        return tuple(valores[c] for c in CAB)

    def escribir(self, *filas, cabecera=CAB):
        with self.ruta.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(cabecera)
            w.writerows(filas)

    def perfilar(self, **opciones):
        r = perfilar_csv(self.ruta, self.procedencia, directorio_temporal=self.indices, **opciones)
        self.assertEqual(tuple(self.indices.iterdir()), ())
        return r

    def variable(self, r, variable="TEMP", estacion="IMATA"):
        e = next(e for e in r.estaciones if e.nombre_literal == estacion)
        return next(v for v in e.variables if v.variable == variable)

    def test_numericos_finitos_exactos_sin_float(self):
        self.escribir(*(self.fila(TEMP=t) for t in ("-2.50", "+1.20", "0", "123456789.123456789")))
        r = self.perfilar()
        v = self.variable(r)
        self.assertTrue(r.completo)
        self.assertEqual((v.total, v.numericos_finitos, v.con_signo, v.con_punto_decimal), (4, 4, 2, 3))
        self.assertEqual(v.minimo.texto_original, "-2.50")
        self.assertEqual(v.maximo.decimal, Decimal("123456789.123456789"))

    def test_contexto_decimal_global_no_redondea_extremos(self):
        self.escribir(self.fila(TEMP="1.234567890123456789"), self.fila(TEMP="1.234567890123456788"))
        with localcontext() as c:
            c.prec = 2
            r = self.perfilar()
        self.assertEqual(self.variable(r).minimo.texto_original, "1.234567890123456788")

    def test_vacios_y_espacios_se_distinguen(self):
        self.escribir(self.fila(TEMP="", HR=" ", PP="0"))
        r = self.perfilar()
        self.assertEqual((self.variable(r).vacios, self.variable(r).no_vacios), (1, 0))
        self.assertEqual(self.variable(r, "HR").no_interpretables, 1)
        self.assertEqual(self.variable(r, "PP").numericos_finitos, 1)

    def test_no_numericos_y_notaciones_no_admitidas(self):
        textos = ("abc", " 1 ", "1,2", "1_000", "１２", "=1+1")
        self.escribir(*(self.fila(TEMP=t) for t in textos))
        v = self.variable(self.perfilar(codificacion="utf-8"))
        self.assertEqual(v.no_interpretables, len(textos))
        self.assertIsNone(v.minimo)
        self.assertEqual([t for _, t, _ in v.ejemplos_especiales], list(textos))

    def test_nan_infinity_y_snan_no_se_comparan(self):
        self.escribir(*(self.fila(TEMP=t) for t in ("NaN", "nan", "sNaN", "Infinity", "-Infinity", "+inf")))
        v = self.variable(self.perfilar())
        self.assertEqual((v.no_finitos, v.numericos_finitos, v.no_interpretables), (6, 0, 0))
        self.assertIsNone(v.minimo)

    def test_notaciones_numericas_se_clasifican_sin_reemplazar_textos(self):
        self.escribir(*(self.fila(TEMP=t) for t in (".5", "1.", "1e2", "001.20", "+2")))
        v = self.variable(self.perfilar())
        self.assertEqual(v.numericos_finitos, 5)
        self.assertEqual(dict(v.notaciones), {"ceros_iniciales": 1, "exponencial": 1,
            "sin_parte_entera": 1, "sin_parte_fraccionaria": 1})
        self.assertEqual(v.maximo.texto_original, "1e2")

    def test_marcadores_numericos_no_se_excluyen(self):
        self.escribir(self.fila(TEMP="-999"), self.fila(TEMP="9999"), self.fila(TEMP="NA"))
        v = self.variable(self.perfilar())
        self.assertEqual(dict(v.marcadores), {"-999": 1, "9999": 1, "NA": 1})
        self.assertEqual((v.minimo.texto_original, v.maximo.texto_original), ("-999", "9999"))
        self.assertEqual(v.numericos_finitos, 2)

    def test_marcadores_configurables_exactos(self):
        self.escribir(self.fila(TEMP="S/D"), self.fila(TEMP="s/d"))
        v = self.variable(self.perfilar(limites=LimitesPerfil(marcadores=("S/D",))))
        self.assertEqual(v.marcadores, (("S/D", 1),))

    def test_extremos_grandes_no_se_clasifican_como_error(self):
        self.escribir(self.fila(TEMP="-1e1000"), self.fila(TEMP="9e999", HR="200", PP="-1"))
        r = self.perfilar()
        v = self.variable(r)
        self.assertEqual(v.minimo.decimal, Decimal("-1e1000"))
        self.assertEqual(v.maximo.decimal, Decimal("9e999"))
        self.assertEqual(r.reglas_cientificas_aplicadas, ())
        self.assertTrue(r.completo)

    def test_limites_conversion_no_fabrican_extremos_globales(self):
        self.escribir(*(self.fila(TEMP=t) for t in ("2", "1e1001", "1" * 65, "1" * 129)))
        r = self.perfilar()
        v = self.variable(r)
        self.assertEqual((v.numericos_finitos, v.fuera_presupuesto_numerico), (1, 3))
        self.assertFalse(v.extremos_comparables_completos)
        self.assertTrue(r.completo)  # Recorrido completo, interpretación numérica acotada explícita.

    def test_decimal_no_recibe_exponentes_fuera_presupuesto(self):
        self.escribir(self.fila(TEMP="1e999999999999999", HR="", PP=""))
        with patch("spica.perfilado.meteorologico.Decimal", side_effect=AssertionError("no convertir")):
            r = self.perfilar()
        self.assertEqual(self.variable(r).fuera_presupuesto_numerico, 1)

    def test_repetidos_por_literal_no_por_equivalencia_decimal(self):
        self.escribir(*(self.fila(TEMP=t) for t in ("1.0", "1.00", "1.0", "1.00", "1")))
        v = self.variable(self.perfilar())
        self.assertEqual(v.valores_distintos_no_vacios, 3)
        self.assertEqual(v.repetidos, (("1.0", 2), ("1.00", 2)))
        self.assertEqual(v.minimo.registro, 2)  # Empate numérico conserva primera aparición.

    def test_repetidos_y_ejemplos_tienen_limites_explicitos(self):
        self.escribir(*(self.fila(TEMP=t) for t in ("NA", "NA", "S/D", "S/D", "NULL", "NULL")))
        v = self.variable(self.perfilar(limites=LimitesPerfil(max_repetidos=1, max_ejemplos=1)))
        self.assertEqual(v.repetidos, (("NA", 2),))
        self.assertEqual(len(v.ejemplos_especiales), 1)
        self.assertEqual(v.no_interpretables, 6)

    def test_particion_de_categorias_cubre_todas_las_celdas(self):
        self.escribir(*(self.fila(TEMP=t) for t in ("", "1", "nan", "abc", "1e1001")))
        v = self.variable(self.perfilar())
        self.assertEqual(v.total, v.vacios + v.numericos_finitos + v.no_finitos +
                         v.no_interpretables + v.fuera_presupuesto_numerico)

    def test_coordenadas_distintas_mismo_nombre_y_cambios(self):
        self.escribir(self.fila(), self.fila(LONGITUD="-71.1"), self.fila())
        r = self.perfilar()
        e = r.estaciones[0]
        self.assertEqual(dict(e.campos_ubicacion)["LONGITUD"], (("-71.0906", 2), ("-71.1", 1)))
        self.assertEqual(e.cambios_ubicacion_en_orden_archivo, 2)
        self.assertEqual(len(e.relaciones_ubicacion), 2)
        self.assertIn("nombre_con_ubicaciones_distintas", [h.codigo for h in r.hallazgos])

    def test_nombre_literal_no_id_ni_ubigeo_agrupa(self):
        self.escribir(self.fila(ID="9"), self.fila(ID="9", ESTACION="IMATA "), self.fila(ID="9", ESTACION="OTRA"))
        r = self.perfilar()
        self.assertEqual([e.nombre_literal for e in r.estaciones], ["IMATA", "IMATA ", "OTRA"])
        self.assertEqual([e.registros for e in r.estaciones], [1, 1, 1])

    def test_ubigeo_y_coordenadas_no_se_normalizan(self):
        self.escribir(self.fila(UBIGEO="040514", LONGITUD="-071.09060"), self.fila())
        e = self.perfilar().estaciones[0]
        self.assertEqual(dict(e.campos_ubicacion)["UBIGEO"], (("040514", 1), ("40514.0", 1)))
        self.assertIn(("-071.09060", 1), dict(e.campos_ubicacion)["LONGITUD"])

    def test_fecha_repetida_con_horas_distintas_y_literal_duplicado(self):
        self.escribir(self.fila(), self.fila(HORA="010000"), self.fila())
        r = self.perfilar()
        d = r.dias[0]
        self.assertEqual((d.registros, d.horas_literales_distintas, d.repeticiones_hora_literal), (3, 2, 1))
        self.assertEqual(r.temporal[0].dias_con_varias_horas_literales, 1)

    def test_horas_cinco_y_seis_fragmentos_sin_fusion(self):
        self.escribir(self.fila(), self.fila(HORA="000000"), self.fila(HORA="10000"))
        r = self.perfilar()
        h = r.estaciones[0].horas
        self.assertEqual(dict(h.longitudes), {5: 2, 6: 1})
        self.assertEqual(h.fragmentos_cinco, (("0", "00", "00", 1), ("1", "00", "00", 1)))
        self.assertEqual(h.fragmentos_seis, (("00", "00", "00", 1),))
        self.assertEqual(r.dias[0].horas_literales_distintas, 3)

    def test_patrones_hora_incompatibles_con_cero_inicial(self):
        horas = ("00000", "15900", "16000", "99999", "246000", "120030", "", "abc")
        self.escribir(*(self.fila(HORA=t) for t in horas))
        patrones = dict(self.perfilar().estaciones[0].horas.patrones)
        self.assertEqual(patrones, {"cinco_digitos_compatibles_cero_inicial": 2,
            "cinco_digitos_incompatibles_cero_inicial": 2, "seis_digitos_fuera_rango": 1,
            "hhmmss_lexico": 1, "vacio": 1, "otro_literal": 1})

    def test_distribucion_por_estacion_y_mes_civil(self):
        self.escribir(self.fila(), self.fila(FECHA="20150201", HORA="000000"), self.fila(ESTACION="OTRA"))
        r = self.perfilar()
        self.assertEqual([(x.estacion, x.mes_civil, x.horas_literales) for x in r.periodos], [
            ("IMATA", "2015-01", (("00000", 1),)), ("IMATA", "2015-02", (("000000", 1),)),
            ("OTRA", "2015-01", (("00000", 1),))])

    def test_fechas_desordenadas_y_saltos_solo_descriptivos(self):
        self.escribir(self.fila(FECHA="20150103"), self.fila(), self.fila(FECHA="20150105"))
        r = self.perfilar()
        t = r.temporal[0]
        self.assertEqual(t.intervalos_entre_fechas_no_consecutivas, 2)
        self.assertEqual([d.fecha_civil.isoformat() for d in r.dias], ["2015-01-01", "2015-01-03", "2015-01-05"])
        self.assertEqual(r.estaciones[0].retrocesos_fecha_en_orden_archivo, 1)

    def test_veinticuatro_filas_no_acreditan_continuidad_horaria(self):
        self.escribir(*(self.fila() for _ in range(24)))
        r = self.perfilar()
        self.assertEqual(r.temporal[0].distribucion_registros_por_dia, ((24, 1),))
        self.assertEqual(r.dias[0].horas_literales_distintas, 1)
        self.assertEqual(r.reglas_cientificas_aplicadas, ())

    def test_fechas_invalidas_no_se_inventan_coberturas(self):
        self.escribir(self.fila(FECHA="20150229"), self.fila(FECHA="2015-01-01"))
        r = self.perfilar()
        self.assertTrue(r.completo)
        self.assertEqual(r.estaciones[0].fechas_invalidas, 2)
        self.assertIsNone(r.temporal[0].fecha_minima)
        self.assertFalse(r.temporal[0].cobertura_interpretable)

    def test_procedencia_documental_y_huellas_fisicas(self):
        sha = hashlib.sha256(self.ruta.read_bytes()).hexdigest()
        self.procedencia = replace(self.procedencia, sha256_declarado=sha)
        documento = EvidenciaDocumental(self.procedencia.fuente, self.procedencia.recurso_id)
        r = self.perfilar(documento=documento)
        self.assertTrue(r.huellas_coinciden)
        self.assertEqual(r.huella_antes.sha256, sha)
        self.assertEqual(r.procedencia, self.procedencia)
        self.assertEqual(r.documento, documento)
        self.assertIsNone(r.documento.revision_documental)

    def test_documento_de_otro_recurso_rechazado(self):
        with self.assertRaises(ValueError):
            self.perfilar(documento=EvidenciaDocumental(self.procedencia.fuente, "otro"))

    def test_hash_declarado_incorrecto_impide_perfilado(self):
        self.procedencia = replace(self.procedencia, sha256_declarado="0" * 64)
        r = self.perfilar()
        self.assertEqual((r.motivo_fin, r.filas_procesadas), ("sha256_declarado_no_coincide", 0))
        self.assertFalse(r.completo)

    def test_original_intacto_y_salida_reproducible(self):
        antes = self.ruta.read_bytes(), self.ruta.stat().st_mtime_ns
        a, b = asdict(self.perfilar()), asdict(self.perfilar())
        a["lectura"].pop("fecha_utc")
        b["lectura"].pop("fecha_utc")
        self.assertEqual(a, b)
        self.assertEqual(antes, (self.ruta.read_bytes(), self.ruta.stat().st_mtime_ns))

    def test_limites_de_grupos_no_truncan_silenciosamente(self):
        casos = (("max_estaciones", 1, self.fila(ESTACION="OTRA"), "limite_estaciones"),
            ("max_variantes_campo", 1, self.fila(LONGITUD="-71.1"), "limite_variantes_campo"),
            ("max_relaciones_estacion", 1, self.fila(LONGITUD="-71.1"), "limite_relaciones_estacion"),
            ("max_horas_estacion", 1, self.fila(HORA="010000"), "limite_horas_estacion"),
            ("max_claves_hora", 1, self.fila(HORA="010000"), "limite_claves_horas"),
            ("max_dias", 1, self.fila(FECHA="20150102"), "limite_claves_dias"),
            ("max_claves_periodo", 1, self.fila(FECHA="20150201"), "limite_claves_periodos"),
            ("max_valores_distintos", 2, self.fila(TEMP="5"), "limite_claves_valores"))
        for campo, valor, fila, motivo in casos:
            with self.subTest(campo=campo):
                self.escribir(self.fila(), fila)
                r = self.perfilar(limites=replace(LimitesPerfil(), **{campo: valor}))
                self.assertFalse(r.completo or r.agregados_indexados_disponibles)
                self.assertEqual(r.motivo_fin, motivo)
                self.assertEqual((r.dias, r.periodos, r.temporal), ((), (), ()))
                self.assertFalse(self.variable(r).extremos_comparables_completos)

    def test_longitud_de_agregados_acotada(self):
        self.escribir(self.fila(TEMP="x" * 513))
        r = self.perfilar()
        self.assertEqual((r.motivo_fin, r.filas_procesadas), ("limite_longitud_agregados", 0))

    def test_limite_de_registros_fuente_marca_parcial(self):
        r = self.perfilar(limites=LimitesPerfil(lectura=PoliticaLecturaCSV(max_registros=1)))
        self.assertFalse(r.completo)
        self.assertEqual(r.motivo_fin, "limite_registros")

    def test_limite_de_bytes_no_abre_indice(self):
        r = self.perfilar(limites=LimitesPerfil(lectura=PoliticaLecturaCSV(max_bytes_archivo=10)))
        self.assertEqual(r.motivo_fin, "limite_bytes_archivo")

    def test_cancelacion_previa_no_crea_indice(self):
        evento = Event()
        evento.set()
        r = self.perfilar(cancelacion=evento)
        self.assertEqual((r.motivo_fin, r.filas_procesadas), ("cancelado", 0))

    def test_cancelacion_durante_lectura_descarta_agregados_indexados(self):
        from spica.perfilado.meteorologico import _interpretar
        self.escribir(self.fila(), self.fila())
        evento = Event()
        def cancelar(texto, p):
            resultado = _interpretar(texto, p)
            evento.set()
            return resultado
        with patch("spica.perfilado.meteorologico._interpretar", cancelar):
            r = self.perfilar(cancelacion=evento)
        self.assertEqual((r.motivo_fin, r.filas_procesadas), ("cancelado", 1))
        self.assertFalse(r.agregados_indexados_disponibles)

    def test_interrupcion_limpia_y_propaga(self):
        with patch("spica.perfilado.meteorologico._interpretar", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.perfilar()
        self.assertEqual(tuple(self.indices.iterdir()), ())

    def test_fila_incompleta_no_se_perfila_como_completa(self):
        self.escribir(self.fila(), self.fila()[:7])
        r = self.perfilar()
        self.assertEqual((r.motivo_fin, r.filas_procesadas), ("anchura_inconsistente", 1))
        self.assertFalse(r.completo)

    def test_encabezado_ajeno_no_se_adivina(self):
        self.escribir(self.fila(), cabecera=tuple(reversed(CAB)))
        r = self.perfilar()
        self.assertEqual(r.motivo_fin, "encabezado_no_admitido")

    def test_codificacion_incierta_no_declara_perfil_completo(self):
        self.escribir(self.fila(ESTACION="ESTACIÓN"))
        r = self.perfilar()
        self.assertFalse(r.completo)
        self.assertTrue(self.perfilar(codificacion="utf-8").completo)

    def test_cambio_del_archivo_se_detecta(self):
        from spica.perfilado.meteorologico import _resumir_indice
        def cambiar(*args):
            resultado = _resumir_indice(*args)
            with self.ruta.open("ab") as f:
                f.write(b"\n")
            return resultado
        with patch("spica.perfilado.meteorologico._resumir_indice", cambiar):
            r = self.perfilar()
        self.assertEqual(r.motivo_fin, "huellas_antes_despues_distintas")
        self.assertFalse(r.completo or r.huellas_coinciden)

    def test_sin_espacio_temporal(self):
        with patch("spica.perfilado._indice.shutil.disk_usage") as uso:
            uso.return_value.free = 0
            r = self.perfilar()
        self.assertEqual(r.motivo_fin, "espacio_temporal_insuficiente")

    def test_error_sqlite_sin_exponer_backend_y_limpieza(self):
        with patch("spica.perfilado._indice.sqlite3.connect", side_effect=sqlite3.OperationalError("secreto/ruta")):
            r = self.perfilar()
        self.assertEqual(r.motivo_fin, "indice_temporal_no_disponible_o_limite_bytes")
        self.assertNotIn("secreto", repr(r))

    def test_limite_fisico_del_indice(self):
        self.escribir(*(self.fila(ESTACION="E" + str(i), TEMP="t" * 100 + str(i)) for i in range(50)))
        r = self.perfilar(limites=LimitesPerfil(max_bytes_indice=20_480))
        self.assertFalse(r.completo or r.agregados_indexados_disponibles)
        self.assertEqual(r.motivo_fin, "indice_temporal_no_disponible_o_limite_bytes")

    def test_temporal_junto_a_fuente_rechazado(self):
        r = perfilar_csv(self.ruta, self.procedencia, directorio_temporal=self.ruta.parent)
        self.assertEqual(r.motivo_fin, "directorio_temporal_no_admitido")
        self.assertEqual(tuple(self.ruta.parent.iterdir()), (self.ruta,))

    def test_no_borra_directorio_que_no_creo(self):
        class UUIDFijo:
            hex = "colision-sintetica"
        carpeta = self.indices / "spica-perfil-colision-sintetica"
        carpeta.mkdir()
        (carpeta / "indice.sqlite3").write_bytes(b"ajeno")
        with patch("spica.perfilado._indice.uuid4", return_value=UUIDFijo()):
            r = perfilar_csv(self.ruta, self.procedencia, directorio_temporal=self.indices)
        self.assertFalse(r.completo)
        self.assertEqual((carpeta / "indice.sqlite3").read_bytes(), b"ajeno")

    def test_error_limpieza_es_explicito(self):
        original = Path.rmdir
        def fallar(ruta):
            if ruta.name.startswith("spica-perfil-"):
                raise PermissionError("privado")
            return original(ruta)
        with patch.object(Path, "rmdir", fallar):
            r = perfilar_csv(self.ruta, self.procedencia, directorio_temporal=self.indices)
        self.assertEqual(r.motivo_fin, "limpieza_temporal_fallida")
        self.assertFalse(r.completo or r.temporal_eliminado)
        for carpeta in self.indices.iterdir():
            carpeta.rmdir()

    def test_validacion_limites_y_metadatos(self):
        for cambios in (dict(max_estaciones=True), dict(max_bytes_indice=1), dict(max_dias=0),
                dict(max_digitos_numero=129), dict(marcadores=("x", "x")), dict(marcadores="NA")):
            with self.subTest(cambios=cambios), self.assertRaises(ValueError):
                LimitesPerfil(**cambios)
        with self.assertRaises(TypeError):
            perfilar_csv(self.ruta, object())

    def test_lecturas_binarias_siempre_son_acotadas(self):
        abrir = Path.open
        class Archivo:
            def __init__(self, f): self.f = f
            def __getattr__(self, nombre): return getattr(self.f, nombre)
            def __enter__(self): return self
            def __exit__(self, *args): self.f.close()
            def read(self, n=-1):
                self_test.assertGreater(n, 0)
                self_test.assertLessEqual(n, 1_048_576)
                return self.f.read(n)
        self_test = self
        def vigilado(ruta, modo="r", *args, **kwargs):
            f = abrir(ruta, modo, *args, **kwargs)
            return Archivo(f) if ruta == self.ruta and modo == "rb" else f
        with patch.object(Path, "open", vigilado):
            self.assertTrue(self.perfilar().completo)

    def test_memoria_no_crece_con_observaciones_repetidas(self):
        picos = []
        for cantidad in (500, 15000):
            with self.ruta.open("w", newline="", encoding="ascii") as f:
                w = csv.writer(f)
                w.writerow(CAB)
                for _ in range(cantidad): w.writerow(self.fila())
            tracemalloc.start()
            try:
                r = self.perfilar()
                picos.append(tracemalloc.get_traced_memory()[1])
            finally:
                tracemalloc.stop()
            self.assertTrue(r.completo)
            self.assertEqual(r.filas_procesadas, cantidad)
        self.assertGreater(self.ruta.stat().st_size, 1_048_576)
        self.assertLess(max(picos), 8 * 1024**2)
        self.assertLess(picos[1], picos[0] + 1024**2)


if __name__ == "__main__":
    unittest.main()
