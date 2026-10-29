"""Regresiones SUADC-04: instantes y zonas sintéticas, sin red ni datos operativos."""

from datetime import datetime, timedelta, timezone
from io import BytesIO
from itertools import permutations
import json
from pathlib import Path
import shutil
import struct
import sys
import tempfile
import unittest
from uuid import uuid4
import zoneinfo
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from spica.adquisicion.nucleo import Fuente, SolicitudAdquisicion
from spica.adquisicion.nucleo.temporal import instante_utc
from spica.adquisicion.catalogo import (
    CatalogoCientifico, CoincidenciaTemporal as CT, DisponibilidadCatalogo,
    ErrorCatalogo, EstadoVerificacion as EV, FiltroCatalogo, FuenteCatalogo,
    ProcedenciaCatalogo, ProductoCatalogo, RegistroCatalogo,
)
from spica.adquisicion.catalogo.persistencia import _datos, _leer_json, _temporal
from spica.adquisicion.planificacion import (
    ConsultaProducto, Planificador, SituacionTemporal as ST, SolicitudCientifica, TramoTemporal,
)
from spica.adquisicion.planificacion.evaluacion import evaluar_intervalo, vacios

UTC = timezone.utc
ZONA = "Prueba/Sintetica"


def tzif_sintetico():
    # Fixture TZif v1: dos transiciones explícitas; no representa una fuente real.
    transiciones = [int(datetime(2020, 3, 29, 1, tzinfo=UTC).timestamp()),
                    int(datetime(2020, 10, 25, 1, tzinfo=UTC).timestamp())]
    return (b"TZif\0" + b"\0" * 15 + struct.pack(">6l", 0, 0, 0, 2, 2, 8)
            + struct.pack(">2l", *transiciones) + b"\1\0"
            + struct.pack(">lbb", 0, 0, 0) + struct.pack(">lbb", 3600, 1, 4)
            + b"STD\0DST\0")


class ComparacionesTemporalesTests(unittest.TestCase):
    def setUp(self):
        self.zona = ZoneInfo.from_file(BytesIO(tzif_sintetico()), key=ZONA)
        self.fuente = Fuente("institucion-sintetica", " Fuente/01 ")
        self.procedencia = ProcedenciaCatalogo("urn:prueba:temporal", datetime(2020, 1, 1, tzinfo=UTC),
                                             "sintetica", "evidencia-sintetica")

    def local(self, minuto=30, fold=0):
        return datetime(2020, 10, 25, 1, minuto, tzinfo=self.zona, fold=fold)

    def solicitud(self, inicio, fin):
        return SolicitudAdquisicion(self.fuente, inicio, fin,
                                    (" E/01 ", " E/02 "), (" X/01 ", " Y/02 "))

    def disponibilidad(self, inicio, fin):
        return DisponibilidadCatalogo("d", self.fuente, " P/01 ", self.procedencia,
                                     inicio=inicio, fin=fin, estado=EV.DECLARADO, cobertura_parcial=False)

    def test_python_comparte_tzinfo_pero_ignora_fold_al_comparar(self):
        a, b = self.local(), self.local(fold=1)
        self.assertIs(a.tzinfo, b.tzinfo)
        self.assertEqual(a, b)  # Comportamiento de Python que NO sirve como criterio SUADC.
        self.assertEqual(b - a, timedelta(0))
        self.assertEqual(b.astimezone(UTC) - a.astimezone(UTC), timedelta(hours=1))

    def test_solicitud_acepta_orden_real_con_horas_civiles_invertidas(self):
        inicio, fin = self.local(45), self.local(15, 1)
        solicitud = self.solicitud(inicio, fin)
        self.assertIs(solicitud.fecha_inicial, inicio)
        self.assertIs(solicitud.fecha_final, fin)
        self.assertEqual(solicitud.estaciones, (" E/01 ", " E/02 "))
        self.assertEqual(solicitud.variables, (" X/01 ", " Y/02 "))

    def test_solicitud_rechaza_orden_real_invertido_entre_folds(self):
        with self.assertRaises(ValueError):
            self.solicitud(self.local(15, 1), self.local(45))

    def test_disponibilidad_acepta_orden_real(self):
        self.disponibilidad(self.local(45), self.local(15, 1))

    def test_disponibilidad_rechaza_orden_real_invertido(self):
        with self.assertRaises(ValueError):
            self.disponibilidad(self.local(15, 1), self.local(45))

    def test_filtro_acepta_orden_real(self):
        FiltroCatalogo(inicio=self.local(45), fin=self.local(15, 1))

    def test_filtro_rechaza_orden_real_invertido(self):
        with self.assertRaises(ValueError):
            FiltroCatalogo(inicio=self.local(15, 1), fin=self.local(45))

    def test_hora_inexistente_se_rechaza_para_ambos_folds(self):
        for fold in (0, 1):
            with self.subTest(fold=fold):
                inexistente = datetime(2020, 3, 29, 1, 30, tzinfo=self.zona, fold=fold)
                with self.assertRaises(ValueError):
                    self.solicitud(inexistente, inexistente)

    def test_catalogo_no_confunde_apariciones_de_hora_repetida(self):
        d = self.disponibilidad(self.local(15), self.local(45))
        filtro = FiltroCatalogo(inicio=self.local(20, 1), fin=self.local(40, 1))
        self.assertEqual(_temporal(d, filtro), CT.FUERA_COBERTURA_CONOCIDA)

    def test_evaluacion_no_propone_interseccion_falsa_entre_folds(self):
        d = self.disponibilidad(self.local(15), self.local(45))
        consulta = ConsultaProducto(self.solicitud(self.local(20, 1), self.local(40, 1)))
        evaluacion = evaluar_intervalo(RegistroCatalogo(d, 1), consulta, {})
        self.assertEqual(evaluacion.situacion, ST.FUERA_COBERTURA_CONOCIDA)
        self.assertIsNone(evaluacion.intervalo_aplicable)

    def test_vacio_real_entre_puntos_con_igual_hora_local(self):
        a, b = self.local(), self.local(fold=1)
        huecos = vacios(a, b, (TramoTemporal(a, a), TramoTemporal(b, b)))
        self.assertEqual(len(huecos), 1)
        self.assertEqual(huecos[0].inicio.astimezone(UTC), a.astimezone(UTC))
        self.assertEqual(huecos[0].fin.astimezone(UTC), b.astimezone(UTC))
        self.assertFalse(huecos[0].incluye_inicio)
        self.assertFalse(huecos[0].incluye_fin)

    def test_claves_utc_distinguen_fold_y_conservan_original(self):
        a, b = self.local(), self.local(fold=1)
        self.assertLess(instante_utc(a), instante_utc(b))
        self.assertIs(a.tzinfo, self.zona)
        self.assertEqual((a.fold, b.fold), (0, 1))

    def test_instante_equivalente_en_otra_zona_durante_fold(self):
        for fold in (0, 1):
            with self.subTest(fold=fold):
                a = self.local(fold=fold)
                b = a.astimezone(timezone(timedelta(hours=-5)))
                solicitud = self.solicitud(a, b)
                self.assertEqual(instante_utc(solicitud.fecha_inicial), instante_utc(solicitud.fecha_final))
                evaluacion = evaluar_intervalo(RegistroCatalogo(self.disponibilidad(a, a), 1),
                                              ConsultaProducto(solicitud), {})
                self.assertEqual(evaluacion.situacion, ST.CATALOGADA)
                self.assertIs(evaluacion.intervalo_aplicable.inicio, a)
                self.assertIs(evaluacion.intervalo_aplicable.fin, b)

    def test_intervalo_normal_en_zonas_diferentes(self):
        a = datetime(2020, 1, 1, tzinfo=UTC)
        b = (a + timedelta(days=1)).astimezone(timezone(timedelta(hours=3)))
        self.assertEqual(instante_utc(self.solicitud(a, b).fecha_final) - a, timedelta(days=1))
        with self.assertRaises(ValueError):
            self.solicitud(b, a)

    def test_interseccion_cruza_fold_y_preserva_extremos_inclusivos(self):
        d = self.disponibilidad(self.local(20), self.local(40, 1))
        a, b = self.local(45), self.local(15, 1)
        ev = evaluar_intervalo(RegistroCatalogo(d, 1), ConsultaProducto(self.solicitud(a, b)), {})
        self.assertEqual(ev.situacion, ST.CATALOGADA)
        self.assertIs(ev.intervalo_aplicable.inicio, a)
        self.assertIs(ev.intervalo_aplicable.fin, b)
        self.assertTrue(ev.intervalo_aplicable.incluye_inicio)
        self.assertTrue(ev.intervalo_aplicable.incluye_fin)

    def test_interseccion_puntual_al_final_de_segunda_aparicion(self):
        d = self.disponibilidad(self.local(15), self.local(45, 1))
        a = self.local(45, 1)
        ev = evaluar_intervalo(RegistroCatalogo(d, 1), ConsultaProducto(self.solicitud(a, a)), {})
        self.assertEqual(ev.situacion, ST.CATALOGADA)
        self.assertEqual(instante_utc(ev.intervalo_aplicable.inicio), instante_utc(a))
        self.assertEqual(vacios(a, a, (ev.intervalo_aplicable,)), ())

    def test_tramo_rechaza_inversion_y_naive(self):
        for a, b in ((self.local(15, 1), self.local(45)),
                     (datetime(2020, 1, 1), datetime(2020, 1, 2))):
            with self.subTest(inicio=a, fin=b), self.assertRaises(ValueError):
                TramoTemporal(a, b)

    def test_tramo_acepta_orden_real_y_requiere_indicadores_booleanos(self):
        TramoTemporal(self.local(45), self.local(15, 1))
        with self.assertRaises(TypeError):
            TramoTemporal(self.local(), self.local(fold=1), incluye_inicio=1)

    def test_naive_civil_se_conserva_sin_suponer_zona(self):
        a = datetime(2020, 3, 29, 1, 30)
        d = self.disponibilidad(a, a)
        self.assertIs(d.inicio, a)
        consulta = ConsultaProducto(self.solicitud(self.local(), self.local(fold=1)))
        ev = evaluar_intervalo(RegistroCatalogo(d, 1), consulta, {})
        self.assertEqual(ev.situacion, ST.DESCONOCIDA)
        self.assertIsNone(d.inicio.tzinfo)

    def test_naive_y_aware_no_se_mezclan_en_contratos(self):
        a, b = self.local().replace(tzinfo=None), self.local(fold=1)
        for construir in (self.solicitud, self.disponibilidad,
                          lambda i, f: FiltroCatalogo(inicio=i, fin=f)):
            with self.subTest(construir=construir), self.assertRaises(ValueError):
                construir(a, b)

    def test_civil_invertido_se_rechaza_sin_localizarlo(self):
        with self.assertRaises(ValueError):
            self.disponibilidad(datetime(2020, 1, 2), datetime(2020, 1, 1))

    def test_disponibilidad_filtro_y_procedencia_rechazan_hora_inexistente(self):
        for fold in (0, 1):
            a = datetime(2020, 3, 29, 1, 30, tzinfo=self.zona, fold=fold)
            for construir in (lambda: self.disponibilidad(a, None),
                              lambda: FiltroCatalogo(inicio=a, fin=a),
                              lambda: ProcedenciaCatalogo("urn:prueba:gap", a, "sintetica")):
                with self.subTest(fold=fold, construir=construir), self.assertRaises(ValueError):
                    construir()

    def test_procedencia_utc_distingue_revisiones_en_hora_repetida(self):
        a = ProcedenciaCatalogo("urn:prueba:a", self.local(), "sintetica")
        b = ProcedenciaCatalogo("urn:prueba:b", self.local(fold=1), "sintetica")
        self.assertEqual(b.revisada_utc - a.revisada_utc, timedelta(hours=1))

    def test_vacios_ordenan_en_utc_y_conservan_discontinuidad(self):
        a, b, c, d = self.local(10), self.local(40), self.local(20, 1), self.local(50, 1)
        tramos = (TramoTemporal(a, b), TramoTemporal(c, d))
        for orden in permutations(tramos):
            huecos = vacios(a, d, orden)
            self.assertEqual(len(huecos), 1)
            self.assertEqual((instante_utc(huecos[0].inicio), instante_utc(huecos[0].fin)),
                             (instante_utc(b), instante_utc(c)))
            self.assertEqual((huecos[0].incluye_inicio, huecos[0].incluye_fin), (False, False))

    def test_union_auxiliar_solapada_o_adyacente_cubre_sin_huecos(self):
        a, b, c, d = self.local(10), self.local(40), self.local(20, 1), self.local(50, 1)
        for tramos in ((TramoTemporal(a, c), TramoTemporal(b, d)),
                       (TramoTemporal(a, c), TramoTemporal(c, d))):
            for orden in permutations(tramos):
                self.assertEqual(vacios(a, d, orden), ())

    def test_union_no_elimina_punto_excluido_por_ambos_intervalos(self):
        a, b, c = self.local(10), self.local(30, 1), self.local(50, 1)
        huecos = vacios(a, c, (TramoTemporal(a, b, True, False), TramoTemporal(b, c, False, True)))
        self.assertEqual(len(huecos), 1)
        self.assertEqual(instante_utc(huecos[0].inicio), instante_utc(b))
        self.assertEqual(instante_utc(huecos[0].fin), instante_utc(b))
        self.assertTrue(huecos[0].incluye_inicio and huecos[0].incluye_fin)

    def test_union_con_empates_no_genera_puntos_desconocidos_falsos(self):
        a, b = self.local(), self.local(fold=1)
        for orden in permutations((TramoTemporal(a, b, False, False), TramoTemporal(a, a), TramoTemporal(b, b))):
            self.assertEqual(vacios(a, b, orden), ())

    def test_complemento_recorta_intervalos_exteriores(self):
        a, b = self.local(), self.local(fold=1)
        inicio, fin = a.astimezone(UTC) - timedelta(hours=2), b.astimezone(UTC) + timedelta(hours=2)
        self.assertEqual(vacios(a, b, (TramoTemporal(inicio, fin),)), ())
        self.assertEqual(vacios(a, b, (TramoTemporal(inicio, inicio), TramoTemporal(fin, fin))),
                         (TramoTemporal(a, b),))

    def test_limite_datetime_no_representable_en_utc_se_rechaza(self):
        a = datetime.min.replace(tzinfo=timezone(timedelta(hours=1)))
        with self.assertRaises(ValueError):
            self.solicitud(a, a)


class PersistenciaTemporalTests(unittest.TestCase):
    def setUp(self):
        padre = Path(tempfile.gettempdir()).resolve()
        self.base = padre / ("spica-temporal-" + uuid4().hex)
        self.base.mkdir(mode=0o755)
        assert self.base.resolve().is_relative_to(padre)
        self.addCleanup(shutil.rmtree, self.base)
        # Base TZif privada para probar ZoneInfo real y reapertura sin tzdata.
        raiz_zonas = self.base / "zonas"
        archivo = raiz_zonas / ZONA
        archivo.parent.mkdir(parents=True)
        archivo.write_bytes(tzif_sintetico())
        ruta_anterior = zoneinfo.TZPATH
        self.addCleanup(zoneinfo.reset_tzpath, ruta_anterior)
        self.addCleanup(ZoneInfo.clear_cache, only_keys=[ZONA])
        zoneinfo.reset_tzpath((str(raiz_zonas),))
        ZoneInfo.clear_cache(only_keys=[ZONA])
        self.zona = ZoneInfo(ZONA)
        self.fuente = Fuente("institucion-sintetica", " Fuente/01 ")
        self.p = ProcedenciaCatalogo("urn:prueba:temporal", datetime(2020, 1, 1, tzinfo=UTC), "sintetica")
        self.ruta = self.base / "catalogo.sqlite3"
        self.catalogo = CatalogoCientifico(self.ruta)
        self.addCleanup(self.catalogo.close)
        self.catalogo.registrar(FuenteCatalogo(self.fuente, self.p))
        self.catalogo.registrar(ProductoCatalogo(self.fuente, " P/01 ", self.p,
                                              utiliza_estaciones=False, autenticacion_requerida=False))

    def local(self, minuto=30, fold=0):
        return datetime(2020, 10, 25, 1, minuto, tzinfo=self.zona, fold=fold)

    def registrar(self, inicio, fin, identificador="d", **opciones):
        d = DisponibilidadCatalogo(identificador, self.fuente, " P/01 ", self.p,
                                  inicio=inicio, fin=fin, estado=EV.DECLARADO, cobertura_parcial=False,
                                  **opciones)
        return self.catalogo.registrar(d)

    def plan(self, inicio, fin, frecuencia=None):
        c = ConsultaProducto(SolicitudAdquisicion(self.fuente, inicio, fin), " P/01 ", frecuencia)
        return Planificador(self.catalogo).planificar(SolicitudCientifica("sintetica", (c,)))

    def test_sqlite_reabre_con_zona_fold_desplazamiento_y_procedencia_originales(self):
        a, b = self.local(45), self.local(15, 1)
        self.registrar(a, b, zona_horaria="zona-sintetica-declarada", precision_temporal="hora")
        self.catalogo.close()
        ZoneInfo.clear_cache(only_keys=[ZONA])
        with CatalogoCientifico(self.ruta) as nuevo:
            d = nuevo.consultar_disponibilidad(self.fuente, " P/01 ", "d").entidad
            self.assertEqual((d.inicio.tzinfo.key, d.fin.tzinfo.key), (ZONA, ZONA))
            self.assertEqual((d.inicio.fold, d.fin.fold), (0, 1))
            self.assertEqual(d.inicio.utcoffset(), a.utcoffset())
            self.assertEqual(d.fin.utcoffset(), b.utcoffset())
            self.assertEqual(d.procedencia, self.p)
            self.assertEqual(d.zona_horaria, "zona-sintetica-declarada")
            self.assertEqual(d.precision_temporal, "hora")
            self.assertEqual(instante_utc(d.inicio), instante_utc(a))
            self.assertEqual(instante_utc(d.fin), instante_utc(b))

    def test_json_anterior_iso_sigue_legible_sin_inventar_zona_o_fold(self):
        d = _leer_json('{"__fecha__":"2020-10-25T01:15:00+00:00"}')
        self.assertEqual(d.fold, 0)
        self.assertIsNone(getattr(d.tzinfo, "key", None))
        self.assertEqual(instante_utc(d), datetime(2020, 10, 25, 1, 15, tzinfo=UTC))

    def test_desplazamiento_fijo_y_nombre_se_conservan_sin_base_iana(self):
        d = datetime(2020, 1, 1, tzinfo=timezone(timedelta(hours=-5), "etiqueta-sintetica"), fold=1)
        nuevo = _leer_json(json.dumps(_datos(d)))
        self.assertEqual(nuevo.isoformat(), d.isoformat())
        self.assertEqual(nuevo.tzname(), "etiqueta-sintetica")
        self.assertEqual(nuevo.fold, 1)

    def test_zona_no_disponible_se_rechaza_sin_exponer_metadatos(self):
        datos = _datos(self.local())
        datos["__zona__"] = "Prueba/NoDisponible-" + uuid4().hex
        with self.assertRaises(ErrorCatalogo) as error:
            _leer_json(json.dumps(datos))
        self.assertNotIn(datos["__zona__"], str(error.exception))

    def test_offset_o_fold_persistido_contradictorio_se_rechaza(self):
        for campo, valor in (("__fecha__", "2020-10-25T01:30:00+02:00"), ("__fold__", 1)):
            datos = _datos(self.local())
            datos[campo] = valor
            with self.subTest(campo=campo), self.assertRaises(ErrorCatalogo):
                _leer_json(json.dumps(datos))

    def test_zona_sin_clave_no_se_aplana_silenciosamente(self):
        d = self.local().replace(tzinfo=ZoneInfo.from_file(BytesIO(tzif_sintetico())))
        with self.assertRaises(ErrorCatalogo):
            self.registrar(d, d)
        self.assertEqual(self.catalogo.listar(DisponibilidadCatalogo), ())

    def test_zona_no_reconstruible_no_se_escribe_en_sqlite(self):
        zona = ZoneInfo.from_file(BytesIO(tzif_sintetico()), key="Prueba/NoInstalada-" + uuid4().hex)
        a = self.local().replace(tzinfo=zona)
        antes = self.ruta.read_bytes()
        with self.assertRaises(ErrorCatalogo):
            self.registrar(a, a)
        self.assertEqual(self.ruta.read_bytes(), antes)
        self.assertFalse(self.catalogo._conexion.in_transaction)

    def test_reglas_distintas_para_misma_clave_no_se_escriben_en_sqlite(self):
        otras_reglas = tzif_sintetico().replace(struct.pack(">lbb", 3600, 1, 4),
                                               struct.pack(">lbb", 7200, 1, 4))
        zona = ZoneInfo.from_file(BytesIO(otras_reglas), key=ZONA)
        a = self.local().replace(tzinfo=zona)
        self.assertEqual(a.utcoffset(), timedelta(hours=2))
        antes = self.ruta.read_bytes()
        with self.assertRaises(ErrorCatalogo):
            self.registrar(a, a)
        self.assertEqual(self.ruta.read_bytes(), antes)
        self.assertEqual(self.catalogo.listar(DisponibilidadCatalogo), ())

    def test_busqueda_sqlite_distingue_folds_y_filtro_equivalente_utc(self):
        self.registrar(self.local(15), self.local(45))
        for a, b, esperado in ((self.local(20, 1), self.local(40, 1), CT.FUERA_COBERTURA_CONOCIDA),
                               (self.local(20), self.local(40), CT.CONTIENE_PERIODO)):
            for i, f in ((a, b), (a.astimezone(UTC), b.astimezone(UTC))):
                with self.subTest(inicio=i.isoformat()):
                    resultado = self.catalogo.buscar(FiltroCatalogo(inicio=i, fin=f))
                    self.assertEqual(resultado.productos[0].disponibilidades[0].coincidencia_temporal, esperado)

    def test_planificador_no_propone_adquisicion_falsa_en_segunda_aparicion(self):
        self.registrar(self.local(15), self.local(45))
        plan = self.plan(self.local(20, 1), self.local(40, 1))
        ev = plan.evaluaciones[0]
        self.assertEqual(ev.intervalos[0].situacion, ST.FUERA_COBERTURA_CONOCIDA)
        self.assertTrue(ev.tramos_desconocidos)
        self.assertIn("resolver_disponibilidad_solicitada", plan.operaciones[0].pendientes)
        self.assertNotIn(ST.AUSENCIA_DOCUMENTADA, (e.situacion for e in ev.intervalos))

    def test_plan_discontinuo_determinista_con_vacio_real_entre_folds(self):
        a, b, c, d = self.local(10), self.local(40), self.local(20, 1), self.local(50, 1)
        self.registrar(a, b, "primero")
        self.registrar(c, d, "segundo")
        antes = self.ruta.read_bytes()
        p = self.plan(a, d)
        self.assertEqual(p, self.plan(a, d))
        self.assertEqual(self.ruta.read_bytes(), antes)
        self.assertEqual(len(p.operaciones), 2)
        huecos = p.evaluaciones[0].tramos_desconocidos
        self.assertEqual(len(huecos), 1)
        self.assertEqual(instante_utc(huecos[0][2].inicio), instante_utc(b))
        self.assertEqual(instante_utc(huecos[0][2].fin), instante_utc(c))
        self.assertEqual({o.evidencias[1].entidad.identificador for o in p.operaciones}, {"primero", "segundo"})

    def test_catalogo_desconocido_no_usa_zona_textual_ni_cambia_frecuencia(self):
        a, b = self.local().replace(tzinfo=None), self.local(fold=1).replace(tzinfo=None)
        self.registrar(a, b, zona_horaria="America/Lima", frecuencia_declarada="Diaria")
        p = self.plan(self.local(), self.local(fold=1), frecuencia="diaria")
        ev = p.evaluaciones[0].intervalos[0]
        self.assertEqual(ev.situacion, ST.DESCONOCIDA)
        self.assertFalse(ev.frecuencia_compatible)
        self.assertIsNone(ev.evidencia.entidad.inicio.tzinfo)
        self.assertEqual(ev.evidencia.entidad.zona_horaria, "America/Lima")
        self.assertIn("frecuencia_incompatible_sin_conversion", p.operaciones[0].pendientes)

    def test_horas_civiles_con_zona_desconocida_siguen_desconocidas(self):
        a, b = datetime(2020, 10, 25, 1, 10), datetime(2020, 10, 25, 1, 50)
        self.registrar(a, b)
        p = self.plan(self.local(), self.local(fold=1))
        self.assertEqual(p.evaluaciones[0].intervalos[0].situacion, ST.DESCONOCIDA)
        self.assertIn("comprobar_cobertura_temporal", p.operaciones[0].pendientes)
        self.assertFalse(p.ejecutable)


if __name__ == "__main__":
    unittest.main()
