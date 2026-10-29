"""Descubrimiento sin red: metadatos sintéticos, SQLite y raíces efímeras."""

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
import shutil
import sqlite3
import sys
import unittest
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from spica.adquisicion.nucleo import Fuente
from spica.adquisicion.catalogo import (
    CapacidadCatalogo, CatalogoCientifico, CoincidenciaTemporal, DisponibilidadCatalogo,
    ErrorCatalogo, EstacionCatalogo, EstadoVerificacion, FiltroCatalogo, FuenteCatalogo,
    MecanismoAdquisicion, ProcedenciaCatalogo, ProductoCatalogo, VariableCatalogo,
)


class CatalogoCientificoTests(unittest.TestCase):
    def setUp(self):
        proyecto = Path(__file__).resolve().parents[1]
        self.base = proyecto / (".suadc-test-" + uuid4().hex)
        self.base.mkdir(mode=0o755)
        assert self.base.resolve().is_relative_to(proyecto)
        self.addCleanup(shutil.rmtree, self.base)
        self.ruta = self.base / "catalogo_descubrimiento.sqlite3"
        self.catalogo = CatalogoCientifico(self.ruta)
        self.addCleanup(self.catalogo.close)
        self.fecha = datetime(2020, 1, 1, tzinfo=timezone.utc)
        self.procedencia = ProcedenciaCatalogo("urn:prueba:documento:01", self.fecha,
                                              "registro_sintetico", "evidencia-sintetica")
        self.fuente = Fuente("institucion-sintetica", " Fuente/01 ")
        self.otra = Fuente("otra-institucion-sintetica", " Fuente/01 ")
        for fuente in (self.fuente, self.otra):
            self.catalogo.registrar(FuenteCatalogo(fuente, self.procedencia, nombre="Nombre declarado"))
            self.catalogo.registrar(ProductoCatalogo(fuente, " Producto/01 ", self.procedencia,
                familia="familia-declarada", formatos_declarados=("formato-propio",), utiliza_estaciones=True))

    def estacion(self, identificador=" E/01 ", fuente=None):
        entidad = EstacionCatalogo(fuente or self.fuente, " Producto/01 ", identificador, self.procedencia)
        self.catalogo.registrar(entidad)
        return entidad

    def variable(self, identificador="variable-interna-1", fuente=None, **opciones):
        entidad = VariableCatalogo(identificador, fuente or self.fuente, " Producto/01 ", self.procedencia, **opciones)
        self.catalogo.registrar(entidad)
        return entidad

    def disponibilidad(self, identificador="intervalo-1", **opciones):
        base = dict(estado=EstadoVerificacion.DECLARADO, inicio=self.fecha,
                    fin=self.fecha + timedelta(days=10))
        base.update(opciones)
        entidad = DisponibilidadCatalogo(identificador, self.fuente, " Producto/01 ", self.procedencia, **base)
        self.catalogo.registrar(entidad)
        return entidad

    def buscar(self, **opciones):
        filtro = FiltroCatalogo(fuentes=(self.fuente,), **opciones)
        return self.catalogo.buscar(filtro).productos[0]

    def test_registro_de_fuentes_y_productos(self):
        fuente = self.catalogo.consultar_fuente(self.fuente)
        self.assertEqual(fuente.entidad.fuente, self.fuente)
        self.assertEqual(fuente.revision, 1)
        producto = self.catalogo.consultar_producto(self.fuente, " Producto/01 ").entidad
        self.assertEqual(producto.formatos_declarados, ("formato-propio",))
        self.assertEqual(producto.familia, "familia-declarada")

    def test_estaciones_repetidas_en_fuentes_distintas(self):
        a = self.estacion()
        b = self.estacion(fuente=self.otra)
        self.assertNotEqual(a.fuente, b.fuente)
        self.assertEqual(a.identificador, b.identificador)
        self.assertEqual(self.catalogo.consultar_estacion(self.otra, b.producto_id, b.identificador).entidad, b)

    def test_variables_originales_repetidas_entre_fuentes(self):
        a = self.variable(codigo_original=" X/01 ")
        b = self.variable("variable-interna-2", self.otra, codigo_original=" X/01 ")
        self.assertEqual(a.codigo_original, b.codigo_original)
        self.assertNotEqual(a.id_interno, b.id_interno)

    def test_multiples_variables_por_estacion_sin_inferencias(self):
        estacion = self.estacion()
        uno = self.variable()
        dos = self.variable("variable-interna-2")
        self.disponibilidad(estacion_id=estacion.identificador, variable_id=uno.id_interno)
        self.disponibilidad("intervalo-2", estacion_id=estacion.identificador, variable_id=dos.id_interno)
        resultado = self.buscar(estaciones=(estacion.identificador,), variables=(uno.id_interno, dos.id_interno))
        self.assertEqual(len(resultado.disponibilidades), 2)
        self.assertFalse(resultado.sin_evidencia_del_alcance)

    def test_variable_solo_en_ciertas_estaciones_no_se_propaga(self):
        a, b = self.estacion(), self.estacion(" E/02 ")
        variable = self.variable()
        self.disponibilidad(estacion_id=a.identificador, variable_id=variable.id_interno)
        resultado = self.buscar(estaciones=(b.identificador,), variables=(variable.id_interno,))
        self.assertEqual(resultado.disponibilidades, ())
        self.assertTrue(resultado.sin_evidencia_del_alcance)

    def test_variable_unidad_y_frecuencia_desconocidas(self):
        variable = self.variable()
        self.assertIsNone(variable.codigo_original)
        self.assertIsNone(variable.nombre_original)
        self.assertIsNone(variable.unidad_declarada)
        self.assertIsNone(variable.frecuencia_declarada)
        self.assertEqual(self.catalogo.consultar_variable(variable.id_interno).entidad, variable)

    def test_coordenadas_y_crs_desconocidos_no_se_inventan(self):
        estacion = self.estacion()
        self.assertIsNone(estacion.coordenada_x)
        self.assertIsNone(estacion.altitud)
        self.assertIsNone(estacion.sistema_referencia)
        self.assertIsNone(estacion.estado_operativo)

    def test_cobertura_parcial_conserva_su_condicion(self):
        self.disponibilidad(inicio=self.fecha + timedelta(days=3), cobertura_parcial=True)
        resultado = self.buscar(inicio=self.fecha, fin=self.fecha + timedelta(days=5))
        self.assertEqual(resultado.disponibilidades[0].coincidencia_temporal, CoincidenciaTemporal.SOLAPAMIENTO_PARCIAL)
        self.assertTrue(resultado.disponibilidades[0].disponibilidad.cobertura_parcial)

    def test_intervalos_discontinuos_no_se_fusionan(self):
        self.disponibilidad(fin=self.fecha + timedelta(days=2))
        self.disponibilidad("segundo", inicio=self.fecha + timedelta(days=8))
        resultado = self.buscar(inicio=self.fecha, fin=self.fecha + timedelta(days=10))
        self.assertEqual(len(resultado.disponibilidades), 2)
        self.assertTrue(all(d.coincidencia_temporal is CoincidenciaTemporal.SOLAPAMIENTO_PARCIAL
                            for d in resultado.disponibilidades))

    def test_consulta_fuera_de_cobertura_no_declara_inexistencia(self):
        self.disponibilidad()
        resultado = self.buscar(inicio=self.fecha + timedelta(days=20), fin=self.fecha + timedelta(days=30))
        self.assertEqual(len(resultado.disponibilidades), 1)
        self.assertEqual(resultado.disponibilidades[0].coincidencia_temporal,
                         CoincidenciaTemporal.FUERA_COBERTURA_CONOCIDA)

    def test_disponibilidad_desconocida_y_periodo_desconocido(self):
        self.disponibilidad(inicio=None, fin=None, estado=EstadoVerificacion.DESCONOCIDO)
        resultado = self.buscar(inicio=self.fecha, fin=self.fecha + timedelta(days=1))
        self.assertTrue(resultado.sin_evidencia_del_alcance)
        self.assertEqual(resultado.disponibilidades[0].coincidencia_temporal, CoincidenciaTemporal.DESCONOCIDA)

    def test_periodo_abierto_y_zona_desconocida(self):
        self.disponibilidad(inicio=None)
        self.disponibilidad("sin-zona", inicio=datetime(2020, 1, 1), fin=datetime(2020, 1, 5))
        resultado = self.buscar(inicio=self.fecha, fin=self.fecha + timedelta(days=1))
        self.assertTrue(all(d.coincidencia_temporal is CoincidenciaTemporal.DESCONOCIDA for d in resultado.disponibilidades))

    def test_frecuencias_distintas(self):
        self.disponibilidad(frecuencia_declarada="horaria-original")
        self.disponibilidad("diaria", frecuencia_declarada="diaria-original")
        resultado = self.buscar(frecuencias=("diaria-original",))
        self.assertEqual(len(resultado.disponibilidades), 1)
        self.assertEqual(resultado.disponibilidades[0].disponibilidad.identificador, "diaria")

    def test_frecuencia_no_conocida_se_etiqueta_sin_evidencia(self):
        self.disponibilidad()
        resultado = self.buscar(frecuencias=("horaria",))
        self.assertTrue(resultado.sin_evidencia_del_alcance)
        self.assertFalse(resultado.disponibilidades[0].alcance_exacto)

    def test_producto_sin_estaciones(self):
        producto = ProductoCatalogo(self.fuente, "recurso-documental", self.procedencia, utiliza_estaciones=False)
        self.catalogo.registrar(producto)
        intervalo = DisponibilidadCatalogo("documento", self.fuente, producto.identificador,
                                           self.procedencia, estado=EstadoVerificacion.DECLARADO)
        self.catalogo.registrar(intervalo)
        resultado = self.buscar(productos=(producto.identificador,))
        self.assertIsNone(resultado.disponibilidades[0].disponibilidad.estacion_id)
        with self.assertRaises(ErrorCatalogo):
            self.catalogo.registrar(EstacionCatalogo(self.fuente, producto.identificador, "E", self.procedencia))

    def test_preserva_codigos_y_unidad_original_exacta(self):
        variable = self.variable(codigo_original=" CÓDIGO/Ab ", nombre_original=" Nombre Original ",
            unidad_declarada=" unidad-proveedor ", version_diccionario=" v/01 ",
            procedencia_diccionario="urn:prueba:diccionario:original")
        recuperada = self.catalogo.consultar_variable(variable.id_interno).entidad
        self.assertEqual(recuperada, variable)
        self.assertEqual(recuperada.unidad_declarada, " unidad-proveedor ")

    def test_fk_impide_producto_sin_fuente(self):
        with self.assertRaises(ErrorCatalogo):
            self.catalogo.registrar(ProductoCatalogo(Fuente("no", "identificada"), "producto", self.procedencia))

    def test_fk_impide_disponibilidad_con_estacion_ajena(self):
        self.estacion(fuente=self.otra)
        with self.assertRaises(ErrorCatalogo):
            self.disponibilidad(estacion_id=" E/01 ")

    def test_fk_impide_variable_de_otro_producto(self):
        variable = self.variable("variable-ajena", self.otra)
        with self.assertRaises(ErrorCatalogo):
            self.disponibilidad(variable_id=variable.id_interno)
        self.assertEqual(self.catalogo._conexion.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_restricciones_sqlite_no_solo_validacion_python(self):
        c = self.catalogo._conexion
        with self.assertRaises(sqlite3.IntegrityError), c:
            c.execute("INSERT INTO estaciones VALUES ('ajeno','fuente','producto','E','{}',1)")

    def test_registro_idempotente_y_contradiccion_rechazada(self):
        estacion = self.estacion()
        self.assertEqual(self.catalogo.registrar(estacion).revision, 1)
        with self.assertRaises(ErrorCatalogo):
            self.catalogo.registrar(replace(estacion, nombre="Nombre diferente"))
        self.assertEqual(len(self.catalogo.historial(estacion)), 1)

    def test_actualizacion_controlada_y_procedencia_persistente(self):
        estacion = self.estacion()
        nueva = replace(estacion, nombre="Nombre revisado", procedencia=replace(
            self.procedencia, revisada_utc=self.fecha + timedelta(days=1), referencia="urn:prueba:revision:02"))
        actualizado = self.catalogo.actualizar(nueva, revision_esperada=1, motivo="correccion documentada")
        self.assertEqual(actualizado.revision, 2)
        historial = self.catalogo.historial(estacion)
        self.assertEqual(tuple(r.entidad for r in historial), (estacion, nueva))
        self.assertEqual(historial[0].entidad.procedencia.referencia, "urn:prueba:documento:01")

    def test_revision_obsoleta_y_sin_procedencia_nueva_se_rechazan(self):
        estacion = self.estacion()
        with self.assertRaises(ErrorCatalogo):
            self.catalogo.actualizar(replace(estacion, nombre="nuevo"), revision_esperada=1, motivo="revision")
        with self.assertRaises(ErrorCatalogo):
            self.catalogo.actualizar(estacion, revision_esperada=9, motivo="revision")

    def test_variable_no_reasigna_su_identidad_a_otra_fuente(self):
        variable = self.variable(codigo_original="codigo")
        nueva = replace(variable, fuente=self.otra, procedencia=replace(self.procedencia,
                        revisada_utc=self.fecha + timedelta(days=1)))
        with self.assertRaises(ErrorCatalogo):
            self.catalogo.actualizar(nueva, revision_esperada=1, motivo="intento de reasignacion")

    def test_codigo_original_duplicado_no_se_fusiona_en_misma_fuente(self):
        self.variable(codigo_original="codigo")
        with self.assertRaises(ErrorCatalogo):
            self.variable("otro-interno", codigo_original="codigo")

    def test_mecanismos_extensibles_y_verificacion(self):
        capacidad = CapacidadCatalogo("manual", self.fuente, " Producto/01 ",
            MecanismoAdquisicion.MANUAL, self.procedencia, estado=EstadoVerificacion.DECLARADO)
        self.catalogo.registrar(capacidad)
        otro = replace(capacidad, identificador="otro", mecanismo=MecanismoAdquisicion.OTRO,
                       otro_mecanismo="mecanismo-futuro", estado=EstadoVerificacion.VERIFICADO, comprobada_utc=self.fecha)
        self.catalogo.registrar(otro)
        resultado = self.buscar(mecanismos=(MecanismoAdquisicion.OTRO,))
        self.assertEqual(resultado.capacidades, (otro,))
        self.assertFalse(resultado.mecanismo_desconocido)

    def test_metodo_no_identificado_no_implica_recurso_inexistente(self):
        self.catalogo.registrar(CapacidadCatalogo("http", self.fuente, " Producto/01 ",
            MecanismoAdquisicion.HTTP_DIRECTO, self.procedencia))
        resultado = self.buscar(mecanismos=(MecanismoAdquisicion.API_REST,))
        self.assertEqual(resultado.capacidades, ())
        self.assertTrue(resultado.mecanismo_desconocido)

    def test_no_verifica_sin_evidencia(self):
        sin_evidencia = replace(self.procedencia, evidencia=None)
        with self.assertRaises(ValueError):
            DisponibilidadCatalogo("id", self.fuente, " Producto/01 ", sin_evidencia,
                                   estado=EstadoVerificacion.VERIFICADO, comprobada_utc=self.fecha)
        with self.assertRaises(ValueError):
            FuenteCatalogo(self.fuente, self.procedencia, estado=EstadoVerificacion.VERIFICADO)

    def test_consulta_multifuente_y_multiproducto(self):
        resultado = self.catalogo.buscar(FiltroCatalogo(fuentes=(self.fuente, self.otra), productos=(" Producto/01 ",)))
        self.assertEqual(len(resultado.productos), 2)
        self.assertEqual({r.producto.fuente for r in resultado.productos}, {self.fuente, self.otra})

    def test_persistencia_al_reabrir(self):
        estacion = self.estacion()
        variable = self.variable()
        intervalo = self.disponibilidad(estacion_id=estacion.identificador, variable_id=variable.id_interno)
        self.catalogo.close()
        with CatalogoCientifico(self.ruta) as otro:
            self.assertEqual(otro.consultar_estacion(self.fuente, estacion.producto_id, estacion.identificador).entidad, estacion)
            self.assertEqual(otro.consultar_variable(variable.id_interno).entidad, variable)
            self.assertEqual(otro.consultar_disponibilidad(self.fuente, intervalo.producto_id, intervalo.identificador).entidad, intervalo)

    def test_base_ajena_o_raw_no_se_adopta(self):
        ajena = self.base / "raw-sintetico.sqlite3"
        c = sqlite3.connect(ajena)
        try:
            c.executescript("CREATE TABLE proyectos(id TEXT PRIMARY KEY); PRAGMA user_version=1;")
        finally:
            c.close()
        contenido = ajena.read_bytes()
        with self.assertRaises(ErrorCatalogo):
            CatalogoCientifico(ajena)
        self.assertEqual(ajena.read_bytes(), contenido)

    def test_secretos_no_persisten_en_catalogo_o_historial(self):
        fuente = Fuente("prueba", "otra-fuente")
        for referencia in ("https://usuario:CLAVE_SINTETICA@prueba.invalid/r", "//usuario:CLAVE_SINTETICA@prueba.invalid/r"):
            with self.assertRaises(ErrorCatalogo):
                self.catalogo.registrar(FuenteCatalogo(fuente, replace(self.procedencia, referencia=referencia)))
        with self.assertRaises(ErrorCatalogo):
            self.catalogo.registrar(ProductoCatalogo(self.fuente, "otro", self.procedencia,
                                                   descripcion_autenticacion="token=CLAVE_SINTETICA"))
        self.assertNotIn(b"CLAVE_SINTETICA", self.ruta.read_bytes())

    def test_validaciones_temporales_y_de_coordenadas(self):
        with self.assertRaises(ValueError):
            DisponibilidadCatalogo("id", self.fuente, " Producto/01 ", self.procedencia,
                                   inicio=self.fecha + timedelta(days=1), fin=self.fecha)
        with self.assertRaises(ValueError):
            FiltroCatalogo(inicio=self.fecha)
        with self.assertRaises(ValueError):
            EstacionCatalogo(self.fuente, " Producto/01 ", "id", self.procedencia, coordenada_x=1)
        with self.assertRaises(ValueError):
            EstacionCatalogo(self.fuente, " Producto/01 ", "id", self.procedencia, altitud=float("nan"))

    def test_no_catalogado_no_es_no_existente(self):
        with self.assertRaisesRegex(ErrorCatalogo, "metadato_no_identificado"):
            self.catalogo.consultar_producto(self.fuente, "aun-no-identificado")
        resultado = self.buscar()
        self.assertTrue(resultado.sin_evidencia_del_alcance)
        self.assertEqual(resultado.disponibilidades, ())

    def test_intervalo_que_contiene_periodo_no_afirma_completitud(self):
        self.disponibilidad(cobertura_parcial=True)
        resultado = self.buscar(inicio=self.fecha + timedelta(days=2), fin=self.fecha + timedelta(days=3))
        self.assertEqual(resultado.disponibilidades[0].coincidencia_temporal, CoincidenciaTemporal.CONTIENE_PERIODO)
        self.assertTrue(resultado.disponibilidades[0].disponibilidad.cobertura_parcial)
        self.assertEqual(resultado.disponibilidades[0].disponibilidad.estado, EstadoVerificacion.DECLARADO)

    def test_busqueda_por_codigo_original_y_listado_del_diccionario(self):
        uno = self.variable(codigo_original=" X/Original ")
        dos = self.variable("otra-variable", codigo_original="otro-codigo")
        self.disponibilidad(variable_id=uno.id_interno)
        self.disponibilidad("otra-disponibilidad", variable_id=dos.id_interno)
        resultado = self.buscar(codigos_variables=(" X/Original ",))
        self.assertEqual(len(resultado.disponibilidades), 1)
        self.assertEqual(resultado.disponibilidades[0].disponibilidad.variable_id, uno.id_interno)
        self.assertEqual(len(self.catalogo.listar(VariableCatalogo, fuente=self.fuente, producto_id=" Producto/01 ")), 2)

    def test_codigo_original_desconocido_no_se_mapea_automaticamente(self):
        variable = self.variable()
        self.disponibilidad(variable_id=variable.id_interno)
        resultado = self.buscar(codigos_variables=("codigo-solicitado",))
        self.assertFalse(resultado.disponibilidades[0].alcance_exacto)
        self.assertTrue(resultado.sin_evidencia_del_alcance)

    def test_cobertura_general_no_prueba_variables_en_todas_las_estaciones(self):
        estacion = self.estacion()
        variable = self.variable()
        self.disponibilidad()
        resultado = self.buscar(estaciones=(estacion.identificador,), variables=(variable.id_interno,))
        self.assertTrue(resultado.sin_evidencia_del_alcance)
        self.assertFalse(resultado.disponibilidades[0].alcance_exacto)

    def test_revision_optimista_rechaza_un_segundo_escritor_obsoleto(self):
        estacion = self.estacion()
        with CatalogoCientifico(self.ruta) as otro:
            version_leida = otro.consultar_estacion(self.fuente, estacion.producto_id, estacion.identificador).revision
            nueva = replace(estacion, nombre="Revisado", procedencia=replace(self.procedencia,
                revisada_utc=self.fecha + timedelta(days=1)))
            self.catalogo.actualizar(nueva, revision_esperada=1, motivo="primera revision")
            with self.assertRaises(ErrorCatalogo):
                otro.actualizar(nueva, revision_esperada=version_leida, motivo="revision obsoleta")

    def test_producto_con_estaciones_no_pasa_a_sin_estaciones_silenciosamente(self):
        self.estacion()
        producto = self.catalogo.consultar_producto(self.fuente, " Producto/01 ").entidad
        nueva = replace(producto, utiliza_estaciones=False, procedencia=replace(self.procedencia,
            revisada_utc=self.fecha + timedelta(days=1)))
        with self.assertRaises(ErrorCatalogo):
            self.catalogo.actualizar(nueva, revision_esperada=1, motivo="cambio contradictorio")
        self.assertEqual(self.catalogo.consultar_producto(self.fuente, producto.identificador).revision, 1)


if __name__ == "__main__":
    unittest.main()
