"""Planificación sin red con entidades exclusivamente sintéticas."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
import shutil
import sys
import unittest
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from spica.adquisicion.nucleo import Fuente, SolicitudAdquisicion
from spica.adquisicion.catalogo import (
    CatalogoCientifico, FuenteCatalogo, ProductoCatalogo, EstacionCatalogo,
    VariableCatalogo, DisponibilidadCatalogo, CapacidadCatalogo, ProcedenciaCatalogo,
    EstadoVerificacion as EV, MecanismoAdquisicion as MA, FiltroCatalogo, ErrorCatalogo,
)
from spica.adquisicion.planificacion import (
    ConsultaProducto, SolicitudCientifica, Planificador, LimitesPlanificacion,
    LimitePlanificacion, ErrorPlanificacion, EstadoPreparacion as EP, SituacionTemporal as ST,
)


class PlanificacionTests(unittest.TestCase):
    def setUp(self):
        raiz = Path(__file__).resolve().parents[1]
        self.base = raiz / (".suadc-test-" + uuid4().hex)
        self.base.mkdir(mode=0o755)
        assert self.base.resolve().is_relative_to(raiz)
        self.addCleanup(shutil.rmtree, self.base)
        self.catalogo = CatalogoCientifico(self.base / "descubrimiento.sqlite3")
        self.addCleanup(self.catalogo.close)
        self.t = datetime(2020, 1, 1, tzinfo=timezone.utc)
        self.p = ProcedenciaCatalogo("urn:sintetico:prueba", self.t, "prueba_local", "evidencia_sintetica")
        self.f = Fuente("institucion-sintetica-A", " Fuente/01 ")
        self.producto(self.f)
        for estacion in (" E/01 ", " E/02 "):
            self.catalogo.registrar(EstacionCatalogo(self.f, " P/01 ", estacion, self.p))
        for interno, codigo in (("id-X", " X/01 "), ("id-Y", " Y/02 ")):
            self.catalogo.registrar(VariableCatalogo(interno, self.f, " P/01 ", self.p, codigo_original=codigo))

    def producto(self, fuente, nombre=" P/01 ", **opciones):
        self.catalogo.registrar(FuenteCatalogo(fuente, self.p))
        base = dict(utiliza_estaciones=True, autenticacion_requerida=False)
        base.update(opciones)
        self.catalogo.registrar(ProductoCatalogo(fuente, nombre, self.p, **base))

    def disponibilidad(self, nombre="d1", **opciones):
        base = dict(estacion_id=" E/01 ", variable_id="id-X", inicio=self.t,
                    fin=self.t + timedelta(days=10), frecuencia_declarada="diaria",
                    cobertura_parcial=False, estado=EV.VERIFICADO, comprobada_utc=self.t)
        base.update(opciones)
        entidad = DisponibilidadCatalogo(nombre, self.f, " P/01 ", self.p, **base)
        self.catalogo.registrar(entidad)
        return entidad

    def capacidad(self, **opciones):
        base = dict(estado=EV.VERIFICADO, comprobada_utc=self.t)
        base.update(opciones)
        self.catalogo.registrar(CapacidadCatalogo("cap", self.f, " P/01 ", MA.HTTP_DIRECTO, self.p, **base))

    def consulta(self, **opciones):
        frecuencia = opciones.pop("frecuencia", "diaria")
        producto = opciones.pop("producto_id", " P/01 ")
        base = dict(fuente=self.f, fecha_inicial=self.t, fecha_final=self.t + timedelta(days=10),
                    estaciones=(" E/01 ",), variables=(" X/01 ",))
        base.update(opciones)
        return ConsultaProducto(SolicitudAdquisicion(**base), producto, frecuencia)

    def plan(self, consulta=None, limites=None):
        return Planificador(self.catalogo, limites or LimitesPlanificacion()).planificar(
            SolicitudCientifica("solicitud-sintetica", (consulta or self.consulta(),)))

    def test_una_estacion_variable_preparada(self):
        self.disponibilidad()
        self.capacidad()
        p = self.plan()
        self.assertEqual(p.operaciones[0].estado, EP.PREPARADA)
        self.assertFalse(p.ejecutable)
        self.assertEqual(p.operaciones_propuestas, 1)
        self.assertIsNone(p.estimacion_operaciones_ejecucion)

    def test_multivariable_multiestacion_sin_cartesiano(self):
        self.disponibilidad()
        self.disponibilidad("d2", estacion_id=" E/02 ", variable_id="id-Y")
        p = self.plan(self.consulta(estaciones=(" E/01 ", " E/02 "), variables=(" X/01 ", " Y/02 ")))
        pares = [(o.estaciones, o.variables) for o in p.operaciones]
        self.assertEqual(set(pares), {((" E/01 ",), (" X/01 ",)), ((" E/02 ",), (" Y/02 ",))})
        self.assertEqual(len(p.operaciones), 2)
        self.assertIn("cobertura_total_de_la_solicitud_no_garantizada", p.evaluaciones[0].advertencias)

    def test_variable_no_propagada_a_otra_estacion(self):
        self.disponibilidad()
        p = self.plan(self.consulta(estaciones=(" E/02 ",)))
        self.assertEqual(p.evaluaciones[0].intervalos, ())
        self.assertEqual(p.operaciones[0].estado, EP.CONDICIONADA)

    def test_identificadores_repetidos_otra_institucion(self):
        otra = Fuente("institucion-sintetica-B", self.f.identificador)
        self.producto(otra)
        self.disponibilidad()
        a, b = self.consulta(), self.consulta(fuente=otra)
        p = Planificador(self.catalogo).planificar(SolicitudCientifica("multi", (a, b)))
        self.assertEqual(len(p.evaluaciones), 2)
        self.assertEqual(p.evaluaciones[1].intervalos, ())
        self.assertNotEqual(p.operaciones[0].producto.fuente, p.operaciones[1].producto.fuente)

    def test_discontinuos_no_fusiona_operaciones(self):
        self.disponibilidad(fin=self.t + timedelta(days=2))
        self.disponibilidad("d2", inicio=self.t + timedelta(days=5))
        p = self.plan()
        self.assertEqual(len(p.operaciones), 2)
        hueco = p.evaluaciones[0].tramos_desconocidos[0][2]
        self.assertEqual((hueco.inicio, hueco.fin), (self.t + timedelta(days=2), self.t + timedelta(days=5)))
        self.assertFalse(hueco.incluye_inicio)
        self.assertFalse(hueco.incluye_fin)

    def test_cobertura_parcial_condiciona(self):
        self.disponibilidad(cobertura_parcial=True)
        self.capacidad()
        p = self.plan()
        self.assertEqual(p.evaluaciones[0].intervalos[0].situacion, ST.PARCIAL)
        self.assertEqual(p.operaciones[0].estado, EP.CONDICIONADA)

    def test_cobertura_parcial_desconocida_no_completa(self):
        self.disponibilidad(cobertura_parcial=None)
        self.assertEqual(self.plan().evaluaciones[0].intervalos[0].situacion, ST.PARCIAL)

    def test_sin_registros_es_desconocido(self):
        p = self.plan()
        self.assertEqual(len(p.evaluaciones[0].tramos_desconocidos), 1)
        self.assertIn("resolver_disponibilidad_solicitada", p.operaciones[0].pendientes)

    def test_estado_desconocido_no_es_evidencia_positiva(self):
        self.disponibilidad(estado=EV.DESCONOCIDO)
        p = self.plan()
        self.assertEqual(p.evaluaciones[0].intervalos[0].situacion, ST.DESCONOCIDA)
        self.assertTrue(p.evaluaciones[0].tramos_desconocidos)

    def test_declarada_no_es_verificada(self):
        self.disponibilidad(estado=EV.DECLARADO)
        self.capacidad()
        p = self.plan()
        self.assertEqual(p.evaluaciones[0].intervalos[0].estado_evidencia, EV.DECLARADO)
        self.assertIn("verificar_disponibilidad", p.operaciones[0].pendientes)

    def test_referencias_evidencia_y_revision(self):
        d = self.disponibilidad()
        self.capacidad()
        evidencia = self.plan().operaciones[0].evidencias[1]
        self.assertEqual(evidencia.entidad, d)
        self.assertEqual(evidencia.revision, 1)

    def test_fuera_cobertura_no_es_ausencia_documentada(self):
        self.disponibilidad(fin=self.t + timedelta(days=1))
        p = self.plan(self.consulta(fecha_inicial=self.t + timedelta(days=5)))
        self.assertEqual(p.evaluaciones[0].intervalos[0].situacion, ST.FUERA_COBERTURA_CONOCIDA)
        self.assertEqual(p.operaciones[0].estado, EP.CONDICIONADA)
        self.assertTrue(p.evaluaciones[0].tramos_desconocidos)

    def test_zonas_equivalentes_sin_modificar_originales(self):
        self.disponibilidad()
        fecha = self.t.astimezone(timezone(timedelta(hours=-5)))
        p = self.plan(self.consulta(fecha_inicial=fecha))
        self.assertEqual(p.solicitud.consultas[0].solicitud.fecha_inicial.utcoffset(), timedelta(hours=-5))
        self.assertEqual(p.evaluaciones[0].intervalos[0].situacion, ST.CATALOGADA)

    def test_naive_catalogado_no_se_localiza(self):
        self.disponibilidad(inicio=self.t.replace(tzinfo=None), fin=(self.t + timedelta(days=10)).replace(tzinfo=None),
                            zona_horaria="UTC", precision_temporal="dia")
        ev = self.plan().evaluaciones[0].intervalos[0]
        self.assertEqual(ev.situacion, ST.DESCONOCIDA)
        self.assertEqual(ev.evidencia.entidad.precision_temporal, "dia")

    def test_extremo_unico_inclusivo(self):
        self.disponibilidad()
        extremo = self.t + timedelta(days=10)
        p = self.plan(self.consulta(fecha_inicial=extremo, fecha_final=extremo))
        self.assertEqual(p.operaciones[0].intervalo.inicio, extremo)
        self.assertEqual(p.evaluaciones[0].tramos_desconocidos, ())

    def test_frecuencia_incompatible_no_convierte(self):
        self.disponibilidad(frecuencia_declarada="mensual")
        p = self.plan()
        self.assertFalse(p.evaluaciones[0].intervalos[0].frecuencia_compatible)
        self.assertIn("frecuencia_incompatible_sin_conversion", p.operaciones[0].pendientes)

    def test_frecuencia_desconocida_condiciona(self):
        self.disponibilidad(frecuencia_declarada=None)
        self.assertIn("identificar_frecuencia", self.plan().operaciones[0].pendientes)

    def test_sin_frecuencia_no_la_inventa(self):
        self.disponibilidad(frecuencia_declarada=None)
        p = self.plan(self.consulta(frecuencia=None))
        self.assertIsNone(p.operaciones[0].consulta.frecuencia)

    def test_producto_sin_estaciones_ni_variables(self):
        self.producto(self.f, "recurso-documental", utiliza_estaciones=False)
        p = self.plan(self.consulta(producto_id="recurso-documental", estaciones=(), variables=()))
        self.assertEqual(p.operaciones[0].estaciones, ())
        self.assertEqual(p.operaciones[0].variables, ())

    def test_estaciones_incompatibles_con_producto(self):
        self.producto(self.f, "documento", utiliza_estaciones=False)
        p = self.plan(self.consulta(producto_id="documento"))
        self.assertIn("estaciones_incompatibles_con_producto", p.operaciones[0].pendientes)

    def test_metodo_declarado_condiciona(self):
        self.disponibilidad()
        self.capacidad(estado=EV.DECLARADO)
        self.assertIn("verificar_mecanismo_adquisicion", self.plan().operaciones[0].pendientes)

    def test_metodo_ausente_no_ejecutable(self):
        self.disponibilidad()
        p = self.plan()
        self.assertIn("identificar_mecanismo_adquisicion", p.operaciones[0].pendientes)
        self.assertFalse(p.ejecutable)

    def test_parametros_preservados_sin_inventar_api(self):
        parametros = {"producto_version": " V/01 "}
        self.disponibilidad()
        p = self.plan(self.consulta(parametros_proveedor=parametros))
        self.assertEqual(dict(p.operaciones[0].consulta.solicitud.parametros_proveedor), parametros)
        self.assertIn("validar_parametros_con_conector", p.operaciones[0].pendientes)

    def test_ids_preservados_exactamente(self):
        self.disponibilidad()
        o = self.plan().operaciones[0]
        self.assertEqual(o.producto.identificador, " P/01 ")
        self.assertEqual(o.estaciones, (" E/01 ",))
        self.assertEqual(o.variables, (" X/01 ",))

    def test_limite_operaciones_atomico(self):
        self.disponibilidad()
        self.disponibilidad("d2")
        with self.assertRaises(LimitePlanificacion):
            self.plan(limites=LimitesPlanificacion(max_operaciones=1))

    def test_limite_catalogo_registros(self):
        with self.assertRaises(LimitePlanificacion):
            self.plan(limites=LimitesPlanificacion(max_registros_catalogo=1))

    def test_limite_catalogo_bytes(self):
        with self.assertRaises(LimitePlanificacion):
            self.plan(limites=LimitesPlanificacion(max_bytes_catalogo=10))

    def test_determinismo(self):
        self.disponibilidad()
        self.capacidad()
        self.assertEqual(self.plan(), self.plan())

    def test_consulta_por_institucion_explora_productos(self):
        self.producto(self.f, "segundo")
        self.assertEqual(len(self.plan(self.consulta(producto_id=None)).evaluaciones), 2)

    def test_producto_no_identificado_no_declara_ausencia(self):
        p = self.plan(self.consulta(producto_id="sin-metadatos"))
        self.assertEqual(p.operaciones, ())
        self.assertIn("consulta_0:producto_no_identificado_disponibilidad_desconocida", p.advertencias)

    def test_registro_general_no_confirma_asociacion(self):
        self.disponibilidad(estacion_id=None, variable_id=None)
        self.capacidad()
        o = self.plan().operaciones[0]
        self.assertIn("resolver_asociacion_solicitada", o.pendientes)
        self.assertEqual(o.estaciones, ())

    def test_rechaza_secretos_sin_reproducirlos(self):
        with self.assertRaises(ErrorPlanificacion) as error:
            self.plan(self.consulta(parametros_proveedor={"api_key": "secreto-sintetico"}))
        self.assertNotIn("secreto-sintetico", str(error.exception))

    def test_solicitud_limite_bytes(self):
        with self.assertRaises(LimitePlanificacion):
            self.plan(limites=LimitesPlanificacion(max_bytes_solicitud=5))

    def test_solicitud_limite_selectores(self):
        with self.assertRaises(LimitePlanificacion):
            self.plan(limites=LimitesPlanificacion(max_elementos_solicitud=1))

    def test_solicitud_limite_consultas(self):
        with self.assertRaises(LimitePlanificacion):
            Planificador(self.catalogo, LimitesPlanificacion(max_consultas=1)).planificar(
                SolicitudCientifica("sol", (self.consulta(), self.consulta())))

    def test_no_modifica_catalogo(self):
        ruta = self.base / "descubrimiento.sqlite3"
        antes = ruta.read_bytes()
        self.plan()
        self.assertEqual(antes, ruta.read_bytes())

    def test_lectura_acotada_filtra_y_libera_transaccion(self):
        otra = Fuente("sintetica-B", "otro")
        self.producto(otra)
        filtro = FiltroCatalogo(fuentes=(otra,))
        with self.assertRaises(ErrorCatalogo):
            self.catalogo.leer_acotado(filtro, max_registros=1, max_bytes=1)
        filas = self.catalogo.leer_acotado(filtro, max_registros=1, max_bytes=10000)
        self.assertEqual(len(filas), 1)
        self.assertEqual(filas[0].entidad.fuente, otra)

    def test_validacion_solicitud_y_limites(self):
        with self.assertRaises(ValueError):
            SolicitudCientifica("sol", ())
        with self.assertRaises(ValueError):
            LimitesPlanificacion(max_operaciones=True)
        with self.assertRaises(ValueError):
            self.consulta(producto_id=" ")

    def test_selectores_sin_evidencia_no_se_pierden(self):
        self.disponibilidad()
        p = self.plan(self.consulta(estaciones=(" E/01 ", " E/02 "), variables=(" X/01 ", " Y/02 ")))
        e = p.evaluaciones[0]
        self.assertEqual(e.estaciones_sin_evidencia_aplicable, (" E/02 ",))
        self.assertEqual(e.variables_sin_evidencia_aplicable, (" Y/02 ",))

    def test_solapamientos_no_crean_vacios_internos(self):
        self.disponibilidad(fin=self.t + timedelta(days=6))
        self.disponibilidad("d2", inicio=self.t + timedelta(days=4))
        self.assertEqual(self.plan().evaluaciones[0].tramos_desconocidos, ())

    def test_intervalos_adyacentes_inclusivos(self):
        medio = self.t + timedelta(days=5)
        self.disponibilidad(fin=medio)
        self.disponibilidad("d2", inicio=medio)
        self.assertEqual(self.plan().evaluaciones[0].tramos_desconocidos, ())

    def test_vacios_exteriores_extremos_abiertos_correctos(self):
        self.disponibilidad(inicio=self.t + timedelta(days=2), fin=self.t + timedelta(days=8))
        huecos = self.plan().evaluaciones[0].tramos_desconocidos
        self.assertEqual(len(huecos), 2)
        self.assertEqual((huecos[0][2].incluye_inicio, huecos[0][2].incluye_fin), (True, False))
        self.assertEqual((huecos[1][2].incluye_inicio, huecos[1][2].incluye_fin), (False, True))

    def test_limites_temporales_desconocidos_no_inventa(self):
        self.disponibilidad(inicio=None, fin=None)
        self.assertEqual(self.plan().evaluaciones[0].intervalos[0].situacion, ST.DESCONOCIDA)

    def test_producto_no_observacional_con_evidencia(self):
        self.producto(self.f, "documental", utiliza_estaciones=False)
        self.catalogo.registrar(DisponibilidadCatalogo("doc", self.f, "documental", self.p,
            inicio=self.t, fin=self.t + timedelta(days=10), estado=EV.VERIFICADO,
            comprobada_utc=self.t, cobertura_parcial=False))
        self.catalogo.registrar(CapacidadCatalogo("cap-doc", self.f, "documental", MA.MANUAL, self.p,
            estado=EV.VERIFICADO, comprobada_utc=self.t))
        p = self.plan(self.consulta(producto_id="documental", estaciones=(), variables=(), frecuencia=None))
        self.assertEqual(p.operaciones[0].estado, EP.PREPARADA)
        self.assertFalse(p.ejecutable)

    def test_variable_codigo_desconocido_no_preparada(self):
        self.catalogo.registrar(VariableCatalogo("id-sin-codigo", self.f, " P/01 ", self.p))
        self.disponibilidad(variable_id="id-sin-codigo")
        self.capacidad()
        p = self.plan(self.consulta(variables=()))
        self.assertIn("identificar_codigo_original_variable", p.operaciones[0].pendientes)

    def test_acceso_desconocido_condiciona(self):
        self.producto(self.f, "acceso-desconocido", autenticacion_requerida=None)
        p = self.plan(self.consulta(producto_id="acceso-desconocido"))
        self.assertIn("resolver_requisitos_acceso", p.operaciones[0].pendientes)

    def test_lectura_limite_exactamente_aceptado(self):
        filas = self.catalogo.leer_acotado(FiltroCatalogo(fuentes=(self.f,)), max_registros=5, max_bytes=100000)
        self.assertEqual(len(filas), 5)

    def test_limites_evaluaciones_repetidas(self):
        self.disponibilidad()
        consultas = (self.consulta(),) * 7
        with self.assertRaises(LimitePlanificacion):
            Planificador(self.catalogo, LimitesPlanificacion(max_registros_catalogo=6)).planificar(
                SolicitudCientifica("repetida", consultas))

    def test_frecuencias_distintas_no_se_homologan_por_nombre(self):
        self.disponibilidad(frecuencia_declarada="Diaria")
        self.assertFalse(self.plan().evaluaciones[0].intervalos[0].frecuencia_compatible)

    def test_plan_no_genera_localizadores(self):
        self.disponibilidad()
        self.assertFalse(hasattr(self.plan().operaciones[0], "url"))
        self.assertFalse(hasattr(self.plan().operaciones[0], "endpoint"))


if __name__ == "__main__":
    unittest.main()
