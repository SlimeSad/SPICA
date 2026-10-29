"""CSV sintéticos en temporales. Nunca se utiliza el RAW operativo."""

import csv
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
from spica.adquisicion.verificacion import EstadoEstructura as E, LectorCSV, PoliticaLecturaCSV


class LecturaCSVTests(unittest.TestCase):
    def setUp(self):
        padre = Path(tempfile.gettempdir()).resolve()
        self.base = padre / ("spica-csv-stream-" + uuid4().hex)
        self.base.mkdir(mode=0o755)
        assert self.base.resolve().is_relative_to(padre)
        self.addCleanup(shutil.rmtree, self.base)
        self.ruta = self.base / "sintetico.csv"

    def leer(self, datos, **opciones):
        self.ruta.write_bytes(datos)
        with LectorCSV(self.ruta, **opciones) as lector:
            filas = tuple(lector)
        return filas, lector.informe

    def test_valido_pequeno_infiere_dialecto_sin_inventar_encabezado(self):
        filas, r = self.leer(b"columna,valor\nuno,1\ndos,2\n")
        self.assertEqual(r.estado, E.COMPATIBLE)
        self.assertTrue(r.recorrido_completo and r.eof_alcanzado)
        self.assertEqual((r.registros_completos, r.registros_correctos, r.registros_problematicos), (3, 3, 0))
        self.assertEqual(r.primera_fila, ("columna", "valor"))
        self.assertIsNone(r.encabezado_declarado)
        self.assertEqual((r.codificacion, r.delimitador), ("ascii", ","))
        self.assertEqual(filas[1].valores, ("uno", "1"))

    def test_miles_de_registros_con_conteos_reproducibles(self):
        with self.ruta.open("wb") as f:
            for _ in range(10000):
                f.write(b"uno,2\n")
        resultados = []
        for _ in range(2):
            with LectorCSV(self.ruta, delimitador=",") as lector:
                self.assertEqual(sum(1 for _ in lector), 10000)
            resultados.append(lector.informe)
        self.assertEqual(resultados[0].registros_correctos, resultados[1].registros_correctos)
        self.assertEqual(resultados[0].bytes_recorrido, self.ruta.stat().st_size)

    def test_comillas_delimitadores_escapados_y_valores_exactos(self):
        filas, r = self.leer(b'" a,b ","dijo ""hola"""\n"001","=1+1"\n', delimitador=",")
        self.assertEqual(filas[0].valores, (" a,b ", 'dijo "hola"'))
        self.assertEqual(filas[1].valores, ("001", "=1+1"))
        self.assertEqual(r.estado, E.COMPATIBLE)

    def test_saltos_internos_y_lineas_fisicas_distintas_de_registros(self):
        filas, r = self.leer(b'a,b\r\n"uno\r\ndos\ntres",2\r\nx,y', delimitador=",")
        self.assertEqual(filas[1].valores[0], "uno\r\ndos\ntres")
        self.assertEqual((filas[1].linea_inicial, filas[1].linea_final), (2, 4))
        self.assertEqual((r.registros_completos, r.lineas_fisicas), (3, 5))

    def test_delimitadores_admitidos(self):
        for d in (",", ";", "\t", "|"):
            with self.subTest(delimitador=d):
                filas, r = self.leer(("a"+d+"b\n1"+d+"2\n").encode())
                self.assertEqual(r.delimitador, d)
                self.assertEqual(filas[1].valores, ("1", "2"))

    def test_sin_encabezado_no_descarta_primera_fila(self):
        filas, r = self.leer(b"01,2\n03,4\n", encabezado_declarado=False)
        self.assertEqual(filas[0].valores, ("01", "2"))
        self.assertEqual(r.registros_completos, 2)
        self.assertFalse(r.encabezado_declarado)

    def test_bom_utf8_utf16_utf32(self):
        for codec in ("utf-8-sig", "utf-16", "utf-32"):
            with self.subTest(codec=codec):
                filas, r = self.leer("estación,valor\nprueba,1\n".encode(codec), delimitador=",")
                self.assertEqual(r.estado, E.COMPATIBLE)
                self.assertTrue(r.codificacion_confirmada)
                self.assertIsNotNone(r.bom)
                self.assertEqual(filas[0].valores[0], "estación")

    def test_utf8_sin_bom_permanece_incierto_aunque_llegue_a_eof(self):
        filas, r = self.leer("a,b\nestación,1\n".encode(), delimitador=",")
        self.assertEqual(r.estado, E.INCIERTA)
        self.assertTrue(r.recorrido_completo)
        self.assertFalse(r.codificacion_confirmada)
        self.assertEqual(filas[1].valores[0], "estación")

    def test_muestra_ascii_no_confirma_codificacion_del_resto(self):
        p = PoliticaLecturaCSV(max_bytes_muestra=4, tamano_bloque=4)
        _, r = self.leer("a,b\nestación,1\n".encode(), delimitador=",", politica=p)
        self.assertEqual(r.estado, E.INCIERTA)
        self.assertFalse(r.codificacion_confirmada)

    def test_cp1252_solo_si_es_explicito(self):
        datos = "a,b\nestación,1\n".encode("cp1252")
        _, r = self.leer(datos, delimitador=",")
        self.assertEqual(r.estado, E.INCIERTA)
        self.assertFalse(r.recorrido_completo)
        filas, r = self.leer(datos, delimitador=",", codificacion="cp1252")
        self.assertEqual(r.estado, E.COMPATIBLE)
        self.assertEqual(filas[1].valores[0], "estación")

    def test_codificacion_invalida_no_reemplaza_y_ubica_byte_y_linea(self):
        filas, r = self.leer(b"a,b\n1,2\nx,\xff\n", codificacion="utf-8", delimitador=",")
        self.assertEqual(len(filas), 2)
        self.assertEqual(r.estado, E.ILEGIBLE_O_CORRUPTA)
        self.assertEqual((r.diagnosticos[-1].linea_final, r.diagnosticos[-1].columna,
                          r.diagnosticos[-1].byte), (3, 3, 11))
        self.assertEqual(r.registro_interrumpido, 3)

    def test_utf8_truncado_en_eof(self):
        _, r = self.leer(b"a,b\nx,\xc3", codificacion="utf-8", delimitador=",")
        self.assertEqual(r.estado, E.ILEGIBLE_O_CORRUPTA)
        self.assertFalse(r.recorrido_completo)

    def test_bom_y_codificacion_contradictorios(self):
        _, r = self.leer("a,b\n1,2\n".encode("utf-16"), codificacion="cp1252", delimitador=",")
        self.assertEqual(r.estado, E.INCIERTA)
        self.assertEqual(r.registros_completos, 0)

    def test_campos_faltantes_y_adicionales_con_posiciones(self):
        filas, r = self.leer(b"a,b\n1\n2,3,4\n5,6\n", delimitador=",")
        self.assertEqual([f.estructura_correcta for f in filas], [True, False, False, True])
        self.assertEqual((r.registros_completos, r.registros_correctos, r.registros_problematicos), (4, 2, 2))
        self.assertTrue(r.recorrido_completo)
        self.assertEqual(r.estado, E.ILEGIBLE_O_CORRUPTA)
        self.assertEqual([d.registro for d in r.diagnosticos], [2, 3])

    def test_comilla_sin_cerrar_detiene_sin_resincronizar(self):
        filas, r = self.leer(b'a,b\n"sin cerrar,2\nx,y\n', delimitador=",")
        self.assertEqual(len(filas), 1)
        self.assertEqual(r.estado, E.ILEGIBLE_O_CORRUPTA)
        self.assertEqual(r.registros_problematicos, 1)
        self.assertFalse(r.recorrido_completo)
        self.assertEqual(r.registro_interrumpido, 2)

    def test_comillas_en_campo_no_entrecomillado_y_caracter_tras_cierre(self):
        for datos in (b'a,b\nmal"campo,2\n', b'a,b\n"campo"x,2\n'):
            with self.subTest(datos=datos):
                _, r = self.leer(datos, delimitador=",")
                self.assertEqual(r.estado, E.ILEGIBLE_O_CORRUPTA)
                self.assertEqual(r.diagnosticos[-1].linea_final, 2)

    def test_campo_largo_entrecomillado_y_no_entrecomillado(self):
        for datos in (b'a,b\n"12345",2\n', b"a,b\n12345,2\n"):
            with self.subTest(datos=datos):
                _, r = self.leer(datos, delimitador=",", politica=PoliticaLecturaCSV(max_caracteres_campo=4))
                self.assertEqual(r.estado, E.INCOMPLETA)
                self.assertEqual(r.registros_completos, 1)

    def test_campo_de_tamano_exacto_admitido(self):
        _, r = self.leer(b'a,b\n"12""3",2\n', delimitador=",",
                         politica=PoliticaLecturaCSV(max_caracteres_campo=4))
        self.assertEqual(r.estado, E.COMPATIBLE)

    def test_limite_linea_sin_readline_ilimitado(self):
        _, r = self.leer(b"a,b\n" + b"x"*100 + b",2\n", delimitador=",",
                         politica=PoliticaLecturaCSV(max_caracteres_linea=20))
        self.assertEqual(r.estado, E.INCOMPLETA)
        self.assertEqual(r.motivo_fin, "limite_linea_fisica")
        self.assertEqual(r.diagnosticos[-1].columna, 21)

    def test_limite_registro_multilinea(self):
        _, r = self.leer(b'a,b\n"a\nb\nc\nd",2\n', delimitador=",",
                         politica=PoliticaLecturaCSV(max_caracteres_registro=8))
        self.assertEqual(r.motivo_fin, "limite_registro")
        self.assertEqual(r.registros_completos, 1)

    def test_limite_campos_antes_de_asignar_lista_csv(self):
        _, r = self.leer(b"a,b\n1,2,3,4\n", delimitador=",", politica=PoliticaLecturaCSV(max_campos=3))
        self.assertEqual(r.estado, E.INCOMPLETA)
        self.assertEqual(r.registros_completos, 1)

    def test_limite_archivo_antes_del_muestreo(self):
        _, r = self.leer(b"a,b\n1,2\n", delimitador=",", politica=PoliticaLecturaCSV(max_bytes_archivo=4))
        self.assertEqual(r.bytes_muestra, 0)
        self.assertEqual(r.motivo_fin, "limite_bytes_archivo")

    def test_limite_registros_informa_alcance_sin_falso_eof(self):
        _, r = self.leer(b"a,b\n1,2\n3,4\n", delimitador=",", politica=PoliticaLecturaCSV(max_registros=2))
        self.assertEqual(r.registros_completos, 2)
        self.assertFalse(r.recorrido_completo)
        self.assertEqual(r.motivo_fin, "limite_registros")

    def test_diagnosticos_acotados_sin_truncar_silenciosamente(self):
        _, r = self.leer(b"a,b\n1\n2\n3\n", delimitador=",", politica=PoliticaLecturaCSV(max_diagnosticos=2))
        self.assertEqual(len(r.diagnosticos), 2)
        self.assertEqual(r.registros_problematicos, 2)
        self.assertEqual(r.motivo_fin, "limite_diagnosticos")

    def test_archivo_vacio_incierto(self):
        _, r = self.leer(b"", delimitador=",")
        self.assertEqual(r.estado, E.INCIERTA)
        self.assertTrue(r.recorrido_completo)
        self.assertEqual(r.registros_completos, 0)

    def test_cancelacion_controlada_sin_escritura(self):
        self.ruta.write_bytes(b"a,b\n1,2\n3,4\n")
        cancelacion = Event()
        with LectorCSV(self.ruta, delimitador=",", cancelacion=cancelacion) as lector:
            next(lector)
            lector.cancelar()
            self.assertEqual(tuple(lector), ())
        self.assertEqual(lector.informe.motivo_fin, "cancelado")
        self.assertEqual(lector.informe.registros_completos, 1)

    def test_consumidor_interrumpe_y_cierra_descriptor(self):
        self.ruta.write_bytes(b"a,b\n1,2\n")
        with LectorCSV(self.ruta, delimitador=",") as lector:
            next(lector)
        self.assertFalse(lector.informe.recorrido_completo)
        self.assertEqual(lector.informe.motivo_fin, "consumidor_detuvo_lectura")
        self.assertIsNone(lector._archivo)

    def test_reapertura_y_lectura_no_destructiva(self):
        self.ruta.write_bytes(b"a,b\n001,=1+1\n")
        antes = self.ruta.read_bytes(), self.ruta.stat().st_mtime_ns
        lector = LectorCSV(self.ruta, delimitador=",")
        for _ in range(2):
            with lector:
                self.assertEqual(sum(1 for _ in lector), 2)
            self.assertEqual(lector.informe.estado, E.COMPATIBLE)
        self.assertEqual((self.ruta.read_bytes(), self.ruta.stat().st_mtime_ns), antes)

    def test_bloques_de_un_byte_cr_lf_unicode_y_bom(self):
        datos = 'a,b\r\n"uno\r\ndos",é\r\nx,y'.encode("utf-8-sig")
        filas, r = self.leer(datos, delimitador=",", politica=PoliticaLecturaCSV(tamano_bloque=1))
        self.assertEqual(r.estado, E.COMPATIBLE)
        self.assertEqual(filas[1].valores, ("uno\r\ndos", "é"))
        self.assertEqual(r.lineas_fisicas, 4)

    def test_delimitador_ambiguo_no_se_adivina(self):
        _, r = self.leer(b"a,b;c\n1,2;3\n")
        self.assertEqual(r.estado, E.INCIERTA)
        self.assertEqual(r.motivo_fin, "delimitador_no_resuelto")

    def test_no_modifica_limite_global_csv(self):
        previo = csv.field_size_limit()
        self.leer(b"a,b\n1,2\n")
        self.assertEqual(csv.field_size_limit(), previo)

    def test_limite_global_externo_mas_bajo_se_informa(self):
        previo = csv.field_size_limit()
        try:
            csv.field_size_limit(3)
            _, r = self.leer(b"a,b\n1234,2\n", delimitador=",")
            self.assertEqual(r.estado, E.INCOMPLETA)
            self.assertEqual(r.motivo_fin, "limite_parser_csv_proceso")
        finally:
            csv.field_size_limit(previo)

    def test_controles_binarios_no_son_csv(self):
        _, r = self.leer(b"a,b\nx,\x00\n", delimitador=",")
        self.assertEqual(r.estado, E.ILEGIBLE_O_CORRUPTA)

    def test_html_y_json_no_se_aceptan_por_tener_comas(self):
        for datos in (b'<html>a,b\n1,2</html>', b'{"a":1,"b":2}'):
            with self.subTest(datos=datos):
                _, r = self.leer(datos, delimitador=",")
                self.assertEqual(r.estado, E.INCOMPATIBLE)

    def test_todas_las_lecturas_binarias_tienen_limite(self):
        self.ruta.write_bytes(b"a,b\n" + b"uno,2\n" * 1000)
        abrir_real = Path.open
        cantidades = []
        class Vigilado:
            def __init__(self, archivo): self.archivo = archivo
            def read(self, cantidad=-1):
                cantidades.append(cantidad)
                if not 0 <= cantidad <= 128:
                    raise AssertionError("Lectura no acotada")
                return self.archivo.read(cantidad)
            def __getattr__(self, nombre): return getattr(self.archivo, nombre)
        def abrir(ruta, *args, **kwargs):
            return Vigilado(abrir_real(ruta, *args, **kwargs))
        p = PoliticaLecturaCSV(max_bytes_muestra=128, tamano_bloque=32)
        with patch.object(Path, "open", abrir):
            with LectorCSV(self.ruta, delimitador=",", politica=p) as lector:
                self.assertEqual(sum(1 for _ in lector), 1001)
        self.assertTrue(cantidades)

    def test_error_io_no_declara_corrupcion(self):
        self.ruta.write_bytes(b"a,b\n1,2\n")
        with patch.object(Path, "open", side_effect=PermissionError):
            with LectorCSV(self.ruta, delimitador=",") as lector:
                self.assertEqual(tuple(lector), ())
        self.assertEqual(lector.informe.estado, E.INCOMPLETA)

    def test_interrupcion_al_entrar_cierra_archivo_sin_exit(self):
        self.ruta.write_bytes(b"a,b\n1,2\n")
        archivo = self.ruta.open("rb")
        with patch.object(Path, "open", return_value=archivo):
            with patch("spica.adquisicion.verificacion.csv_streaming._texto", side_effect=KeyboardInterrupt):
                with self.assertRaises(KeyboardInterrupt):
                    with LectorCSV(self.ruta):
                        self.fail("No debe entrar")
        self.assertTrue(archivo.closed)

    def test_error_io_durante_recorrido_conserva_alcance_y_no_declara_corrupcion(self):
        self.ruta.write_bytes(b"a,b\n1,2\n")
        abrir_real = Path.open
        class FalloLectura:
            def __init__(self, archivo):
                self.archivo, self.lecturas = archivo, 0
            def read(self, n):
                self.lecturas += 1
                if self.lecturas == 3:
                    raise OSError
                return self.archivo.read(n)
            def __getattr__(self, nombre): return getattr(self.archivo, nombre)
        with patch.object(Path, "open", lambda ruta,*a,**kw:FalloLectura(abrir_real(ruta,*a,**kw))):
            with LectorCSV(self.ruta, delimitador=",", politica=PoliticaLecturaCSV(tamano_bloque=4)) as lector:
                filas = tuple(lector)
        self.assertEqual(len(filas), 1)
        self.assertEqual(lector.informe.estado, E.INCOMPLETA)
        self.assertEqual(lector.informe.motivo_fin, "lectura_no_disponible")

    def test_rutas_enlazadas_se_rechazan(self):
        with patch.object(Path, "is_symlink", return_value=True):
            with LectorCSV(self.ruta) as lector:
                self.assertEqual(tuple(lector), ())
        self.assertEqual(lector.informe.motivo_fin, "ruta_no_admitida")

    def test_modificacion_durante_lectura_detectada_al_cerrar(self):
        self.ruta.write_bytes(b"a,b\n1,2\n")
        with LectorCSV(self.ruta, delimitador=",") as lector:
            tuple(lector)
            with self.ruta.open("ab") as f:
                f.write(b"3,4\n")
        self.assertEqual(lector.informe.motivo_fin, "archivo_modificado_durante_lectura")
        self.assertFalse(lector.informe.recorrido_completo)

    def test_memoria_no_crece_con_numero_de_filas(self):
        picos = []
        for cantidad in (1000, 50000):
            with self.ruta.open("wb") as f:
                for _ in range(cantidad):
                    f.write(b"uno,2\n")
            tracemalloc.start()
            try:
                with LectorCSV(self.ruta, delimitador=",") as lector:
                    self.assertEqual(sum(1 for _ in lector), cantidad)
                picos.append(tracemalloc.get_traced_memory()[1])
            finally:
                tracemalloc.stop()
        self.assertLess(max(picos), 4*1024**2)
        self.assertLess(picos[1] - picos[0], 1024**2)

    def test_politicas_y_parametros_invalidos(self):
        for kw in ({"max_campos":True}, {"max_caracteres_campo":65537}, {"tamano_bloque":0}):
            with self.subTest(kw=kw), self.assertRaises(ValueError):
                PoliticaLecturaCSV(**kw)
        with self.assertRaises(ValueError):
            LectorCSV(self.ruta, delimitador=":")
        with self.assertRaises(TypeError):
            LectorCSV(self.ruta, encabezado_declarado=1)


if __name__ == "__main__":
    unittest.main()
