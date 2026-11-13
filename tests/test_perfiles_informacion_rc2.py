"""RC2: esquemas inventados en memoria. Sin archivos institucionales ni ciencia."""

from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from spica.adquisicion.almacenamiento.modelos import ProyectoCientifico, ObjetoCientifico
from spica.adquisicion.catalogo.modelos import VariableCatalogo, ProcedenciaCatalogo, EstadoVerificacion as V
from spica.adquisicion.nucleo import Fuente
from spica.adquisicion.readquisicion.modelos import EvidenciaLocal, EstadoLocal
from spica.calidad.restricciones import RestriccionQA, TipoRestriccionQA as T
from spica.contextos import (
    ConfiguracionContexto, ContextoProyecto, ContextoEntrada, ContextoOperacion,
    TipoOperacion, EstadoOperacion,
)
from spica.interoperabilidad import (
    IdentidadRecurso, RecursoInteroperable, Respaldo, MarcoTemporal,
    EstadoAptitud as E, DimensionEvaluacion as D, evaluar_aptitud,
)
from spica.interoperabilidad.adaptadores import NivelDiagnostico as N
from spica.interoperabilidad.perfiles import (
    VERSION_PERFILES, AspectoCampo as A, CampoInformacion, DeclaracionPerfil,
    EntradaPerfil, EstadoUnidad as U, FinalidadCompatibilidad,
    PerfilInformacion, UnidadPerfil, comparar_perfiles,
)
# Reutiliza marcos sintéticos existentes, no sus clases TestCase ni datos reales.
from test_interoperabilidad_modelos import espacial, temporal, periodo


FECHA = datetime(2026, 11, 13, tzinfo=timezone.utc)
PROC = ProcedenciaCatalogo("fixture:rc2", FECHA, "construccion_sintetica", "evidencia-inventada-rc2")
VER = Respaldo(V.VERIFICADO, PROC)
DEC = Respaldo(V.DECLARADO, PROC)
FUENTE = Fuente("SPICA-SINTETICA", "RC2")
SHA = "a" * 64  # Declaración sintética; no se afirma haber calculado un archivo.


def declarado(valor):
    return DeclaracionPerfil(valor, VER)


def variable(**kw):
    d = dict(id_interno="variable-ficticia", fuente=FUENTE, producto_id="producto-ficticio",
             procedencia=PROC, codigo_original=" código original ", unidad_declarada="u-ficticia",
             frecuencia_declarada="frecuencia-ficticia", tipo_medicion="medicion-ficticia")
    d.update(kw)
    return VariableCatalogo(**d)


def campo(**kw):
    d = dict(nombre=" magnitud original ", tipo=declarado("decimal-literal"),
             variable=variable(), respaldo_variable=VER, significado=declarado("significado ficticio"),
             unidad=UnidadPerfil(U.ACREDITADA, "u-ficticia", VER, declarado("dimension-ficticia")),
             valores_ausentes=("", "ausente-ficticio"), respaldo_ausentes=VER,
             agregacion=declarado("agregacion-ficticia"), calendario=declarado("calendario-ficticio"))
    d.update(kw)
    return CampoInformacion(**d)


def perfil(nombre="A", **kw):
    d = dict(identificador="perfil-" + nombre, version="1", tipo_recurso="tabla-sintetica",
             campos=(campo(),), ambito=declarado("solo escenario inventado RC2"))
    d.update(kw)
    return PerfilInformacion(**d)


def vinculo(nombre="A", *, p=None, proyecto=None, **kw):
    p = perfil(nombre) if p is None else p
    proyecto = (ContextoProyecto("contexto-A", ProyectoCientifico("proyecto-A"),
        ConfiguracionContexto("configuracion-sintetica", "1")) if proyecto is None else proyecto)
    d = dict(entrada_id="entrada-" + nombre, proyecto=proyecto,
             objeto=ObjetoCientifico("objeto-" + nombre, proyecto.project_id),
             recurso=RecursoInteroperable(IdentidadRecurso(FUENTE, "recurso-" + nombre, "producto-ficticio"),
                 "metadatos-1", procedencia=PROC), revision="descripcion-1", tipo_recurso=p.tipo_recurso,
             perfil_estructural=p.identificador, version_contenido="edicion-ficticia",
             sha256_declarado=SHA, size_bytes_declarado=7)
    d.update(kw)
    return EntradaPerfil(ContextoEntrada(**d), p)


def finalidad(**kw):
    d = dict(identificador="comparar-fixture", descripcion="Cotejar descriptores ficticios",
        campos=((" magnitud original ", " magnitud original "),),
        versiones_admitidas=(("perfil-A", "1"), ("perfil-B", "1")), aspectos=tuple(A))
    d.update(kw)
    return FinalidadCompatibilidad(**d)


def cambiar_campo(v, **kw):
    return EntradaPerfil(v.entrada, replace(v.perfil, campos=(replace(v.perfil.campos[0], **kw),)))


def marco(v, **kw):
    return EntradaPerfil(replace(v.entrada, recurso=replace(v.entrada.recurso, **kw)), v.perfil)


def codigos(r):
    return tuple(d.codigo for d in r.diagnosticos)


class ContratosPerfilesRC2Tests(unittest.TestCase):
    def test_versiones_distintas_de_contrato_perfil_contenido_e_institucion(self):
        v = vinculo()
        self.assertEqual(v.perfil.version_contrato, VERSION_PERFILES)
        self.assertEqual(v.perfil.version, "1")
        self.assertEqual(v.entrada.version_contenido, "edicion-ficticia")
        self.assertIsNone(v.entrada.recurso.version_institucional)

    def test_literales_y_variables_catalogo_se_conservan_sin_normalizar(self):
        c = campo()
        self.assertEqual(c.nombre, " magnitud original ")
        self.assertEqual(c.variable.codigo_original, " código original ")
        self.assertEqual(c.valores_ausentes, ("", "ausente-ficticio"))
        self.assertEqual(c.unidad.dimension_fisica.valor, "dimension-ficticia")

    def test_inmutabilidad_de_campos_colecciones_y_vinculo(self):
        v = vinculo()
        for objeto, atributo, valor in ((v, "perfil", perfil("B")), (v.perfil, "version", "2"),
                (v.perfil.campos[0], "nombre", "otro"), (v.perfil.campos[0].unidad, "literal", "otra")):
            with self.subTest(atributo=atributo), self.assertRaises(FrozenInstanceError):
                setattr(objeto, atributo, valor)
        self.assertIs(type(v.perfil.campos), tuple)

    def test_rechazo_de_listas_y_objetos_sin_tipo(self):
        for constructor in (lambda: perfil(campos=[campo()]), lambda: perfil(campos=(object(),)),
                lambda: campo(tipo="decimal"), lambda: campo(variable={}),
                lambda: campo(respaldo_variable="verificado"), lambda: EntradaPerfil({}, perfil()),
                lambda: DeclaracionPerfil("tipo", "verificado")):
            with self.subTest(constructor=constructor), self.assertRaises(TypeError):
                constructor()

    def test_campos_duplicados_se_rechazan(self):
        with self.assertRaises(ValueError):
            perfil(campos=(campo(), campo()))

    def test_version_de_contrato_desconocida_no_se_acepta(self):
        for constructor in (lambda: perfil(version_contrato="99"), lambda: finalidad(version_contrato="99")):
            with self.subTest(constructor=constructor), self.assertRaises(ValueError):
                constructor()

    def test_cotas_de_campos_y_literales(self):
        with self.assertRaises(ValueError):
            perfil(campos=tuple(campo(nombre=str(i)) for i in range(65)))
        with self.assertRaises(ValueError):
            DeclaracionPerfil("x" * 513)
        with self.assertRaises(ValueError):
            campo(valores_ausentes=tuple(str(i) for i in range(33)))
        self.assertEqual(len(perfil(campos=tuple(campo(nombre=str(i)) for i in range(64))).campos), 64)

    def test_vacios_y_caracteres_de_control_no_son_identificadores(self):
        for texto in ("", "  ", "a\nb"):
            with self.subTest(texto=texto), self.assertRaises(ValueError):
                perfil(identificador=texto)

    def test_ausencia_none_y_sin_marcadores_no_se_confunden(self):
        self.assertIsNone(campo(valores_ausentes=None, respaldo_ausentes=Respaldo()).valores_ausentes)
        self.assertEqual(campo(valores_ausentes=()).valores_ausentes, ())
        with self.assertRaises(ValueError):
            campo(valores_ausentes=None)

    def test_no_se_admite_respaldo_de_literal_o_variable_ausente(self):
        with self.assertRaises(ValueError):
            DeclaracionPerfil(None, VER)
        with self.assertRaises(ValueError):
            campo(variable=None)

    def test_unidad_conocida_necesita_literal_y_evidencia(self):
        for constructor in (lambda: UnidadPerfil(U.ACREDITADA, "m", DEC),
                lambda: UnidadPerfil(U.ACREDITADA, None, VER),
                lambda: UnidadPerfil(U.DECLARADA, "m", VER),
                lambda: UnidadPerfil(U.DESCONOCIDA, "m"),
                lambda: UnidadPerfil(U.NO_APLICABLE),
                lambda: UnidadPerfil(U.CONTRADICTORIA, respaldo=VER)):
            with self.subTest(constructor=constructor), self.assertRaises(ValueError):
                constructor()

    def test_dimension_fisica_no_se_infiere_sin_evidencia(self):
        with self.assertRaises(ValueError):
            UnidadPerfil(U.DECLARADA, "m", DEC, DeclaracionPerfil("longitud", DEC))
        self.assertIsNone(UnidadPerfil(U.DECLARADA, "m", DEC).dimension_fisica.valor)

    def test_dimension_documentada_se_conserva_aunque_unidad_desconocida(self):
        u = UnidadPerfil(dimension_fisica=declarado("dimension-documentada-ficticia"))
        self.assertIs(u.estado, U.DESCONOCIDA)
        self.assertIsNone(u.literal)
        self.assertEqual(u.dimension_fisica.valor, "dimension-documentada-ficticia")
        r = comparar_perfiles(cambiar_campo(vinculo(), unidad=u),
            cambiar_campo(vinculo("B"), unidad=u), finalidad())
        self.assertIs(r.estado, E.PENDIENTE_DE_EVIDENCIA)

    def test_unidad_no_aplicable_no_es_unidad_desconocida(self):
        u = UnidadPerfil(U.NO_APLICABLE, respaldo=VER)
        self.assertIsNot(u.estado, UnidadPerfil().estado)
        with self.assertRaises(ValueError):
            replace(u, literal="1")

    def test_desacuerdo_con_unidad_catalogo_exige_conflicto_explicito(self):
        with self.assertRaises(ValueError):
            campo(unidad=UnidadPerfil(U.ACREDITADA, "otra", VER))
        c = campo(unidad=UnidadPerfil(U.CONTRADICTORIA, "otra", VER,
                                     contradicciones=("dos referencias discrepan",)))
        self.assertEqual(c.variable.unidad_declarada, "u-ficticia")

    def test_finalidad_obligatoria_no_vacia_y_sin_mapeos_duplicados(self):
        for cambio in (dict(campos=()), dict(versiones_admitidas=()),
                dict(campos=(("a", "x"), ("a", "y"))), dict(campos=(("a", "x"), ("b", "x"))),
                dict(campos=(("a",),)), dict(aspectos=()), dict(aspectos=(A.TIPO, A.TIPO))):
            with self.subTest(cambio=cambio), self.assertRaises(ValueError):
                finalidad(**cambio)

    def test_semantica_y_dimension_tienen_dependencias_explicitas(self):
        for aspectos in ((A.TIPO, A.SIGNIFICADO), (A.TIPO, A.DIMENSION_FISICA)):
            with self.subTest(aspectos=aspectos), self.assertRaises(ValueError):
                finalidad(aspectos=aspectos)
        with self.assertRaises(ValueError):
            finalidad(requiere_mismo_sitio=True)
        with self.assertRaises(TypeError):
            finalidad(requiere_mismo_recurso=1)

    def test_valores_no_se_ejecutan_como_expresiones(self):
        texto = "__import__('os').system('NO_EJECUTAR')"
        a, b = vinculo(), vinculo("B")
        a, b = cambiar_campo(a, tipo=declarado(texto)), cambiar_campo(b, tipo=declarado(texto))
        with patch("os.system", side_effect=AssertionError("codigo_arbitrario")):
            self.assertIs(comparar_perfiles(a, b, finalidad(aspectos=(A.TIPO,))).estado, E.APTO_ESTRUCTURALMENTE)


class ComparacionPerfilesRC2Tests(unittest.TestCase):
    def setUp(self):
        self.a, self.b, self.f = vinculo(), vinculo("B"), finalidad()

    def comparar(self, **kw):
        return comparar_perfiles(kw.get("a", self.a), kw.get("b", self.b), kw.get("f", self.f))

    def test_estructuras_completas_equivalentes_para_finalidad(self):
        r = self.comparar()
        self.assertIs(r.estado, E.APTO_ESTRUCTURALMENTE)
        self.assertTrue(all(d.nivel is N.INFORMACION for d in r.diagnosticos))
        self.assertIs(r.primero, self.a)
        self.assertIs(r.finalidad, self.f)

    def test_finalidad_no_es_opcional_ni_objeto_sin_tipo(self):
        with self.assertRaises(TypeError):
            comparar_perfiles(self.a, self.b)
        with self.assertRaises(TypeError):
            comparar_perfiles(self.a, self.b, {})

    def test_campo_ausente_es_incompatible_con_proyeccion_requerida(self):
        b = EntradaPerfil(self.b.entrada, replace(self.b.perfil, campos=()))
        r = self.comparar(b=b)
        self.assertIs(r.estado, E.INCOMPATIBLE)
        self.assertIn("campo_requerido_ausente", codigos(r))

    def test_tipos_acreditados_diferentes_no_se_convierten(self):
        r = self.comparar(b=cambiar_campo(self.b, tipo=declarado("texto")))
        self.assertIs(r.estado, E.INCOMPATIBLE)
        self.assertIn("literales_distintos_sin_transformacion_admitida", codigos(r))

    def test_tipo_solo_declarado_no_es_compatible_por_coincidir(self):
        r = self.comparar(b=cambiar_campo(self.b, tipo=DeclaracionPerfil("decimal-literal", DEC)))
        self.assertIs(r.estado, E.PENDIENTE_DE_EVIDENCIA)

    def test_mapeo_explicito_admite_nombres_distintos_sin_renombrar(self):
        b = cambiar_campo(self.b, nombre="OTRA_COLUMNA")
        f = replace(self.f, campos=((" magnitud original ", "OTRA_COLUMNA"),))
        self.assertIs(self.comparar(b=b, f=f).estado, E.APTO_ESTRUCTURALMENTE)
        self.assertEqual(b.perfil.campos[0].nombre, "OTRA_COLUMNA")

    def test_nombres_iguales_no_suplantan_identidad_variable(self):
        b = cambiar_campo(self.b, variable=variable(id_interno="otra-variable", codigo_original="otro-codigo"))
        r = self.comparar(b=b)
        self.assertIs(r.estado, E.INCOMPATIBLE)
        self.assertIn("identidades_variable_distintas_sin_correspondencia", codigos(r))

    def test_variable_desconocida_permanece_indeterminada(self):
        b = cambiar_campo(self.b, variable=None, respaldo_variable=Respaldo())
        self.assertIs(self.comparar(b=b).estado, E.PENDIENTE_DE_EVIDENCIA)

    def test_mismo_nombre_variable_en_otro_producto_no_demuestra_identidad(self):
        recurso = replace(self.b.entrada.recurso, identidad=replace(self.b.entrada.recurso.identidad, producto_id="otro"))
        b = EntradaPerfil(replace(self.b.entrada, recurso=recurso),
            replace(self.b.perfil, campos=(campo(variable=variable(producto_id="otro")),)))
        self.assertIs(self.comparar(b=b).estado, E.INCOMPATIBLE)

    def test_significados_distintos_son_incompatibles(self):
        self.assertIs(self.comparar(b=cambiar_campo(self.b, significado=declarado("otra definicion"))).estado,
                      E.INCOMPATIBLE)

    def test_tipo_medicion_y_frecuencia_distintos_se_diagnostican(self):
        for cambio in (dict(tipo_medicion="otro-tipo"), dict(frecuencia_declarada="otra-frecuencia")):
            with self.subTest(cambio=cambio):
                r = self.comparar(b=cambiar_campo(self.b, variable=variable(**cambio)))
                self.assertIs(r.estado, E.INCOMPATIBLE)
                self.assertTrue(any(d.campo.endswith(tuple(cambio)) and d.nivel is N.CONTRADICCION for d in r.diagnosticos))

    def test_medicion_o_frecuencia_ausente_no_se_suple(self):
        for cambio in (dict(tipo_medicion=None), dict(frecuencia_declarada=None)):
            with self.subTest(cambio=cambio):
                self.assertIs(self.comparar(b=cambiar_campo(self.b, variable=variable(**cambio))).estado,
                              E.PENDIENTE_DE_EVIDENCIA)

    def test_unidades_distintas_no_se_convierten_ni_se_igualan_por_dimension(self):
        b = cambiar_campo(self.b, variable=variable(unidad_declarada="otra-u"),
            unidad=UnidadPerfil(U.ACREDITADA, "otra-u", VER, declarado("dimension-ficticia")))
        r = self.comparar(b=b)
        self.assertIs(r.estado, E.INCOMPATIBLE)
        self.assertIn("unidades_distintas_sin_conversion_admitida", codigos(r))

    def test_celsius_kelvin_no_tienen_equivalencia_implicita(self):
        def con_unidad(v, u):
            return cambiar_campo(v, variable=variable(unidad_declarada=u),
                unidad=UnidadPerfil(U.ACREDITADA, u, VER, declarado("temperatura-ficticia")))
        self.assertIs(self.comparar(a=con_unidad(self.a, "°C"), b=con_unidad(self.b, "K")).estado, E.INCOMPATIBLE)

    def test_unidad_desconocida_o_solo_declarada_no_se_acredita_por_catalogo(self):
        for u in (UnidadPerfil(), UnidadPerfil(U.DECLARADA, "u-ficticia", DEC)):
            with self.subTest(unidad=u):
                self.assertIs(self.comparar(b=cambiar_campo(self.b, unidad=u)).estado, E.PENDIENTE_DE_EVIDENCIA)

    def test_unidad_contradictoria_bloquea_aun_si_literal_coincide(self):
        u = UnidadPerfil(U.CONTRADICTORIA, "u-ficticia", VER, contradicciones=("conflicto-documental-ficticio",))
        r = self.comparar(b=cambiar_campo(self.b, unidad=u))
        self.assertIs(r.estado, E.INCOMPATIBLE)
        self.assertIn("unidad_con_evidencia_contradictoria_aportada", codigos(r))

    def test_no_aplicable_documentada_no_se_confunde_con_dimension_desconocida(self):
        def sin_unidad(v):
            return cambiar_campo(v, variable=variable(unidad_declarada=None),
                unidad=UnidadPerfil(U.NO_APLICABLE, respaldo=VER))
        self.assertIs(self.comparar(a=sin_unidad(self.a), b=sin_unidad(self.b)).estado, E.APTO_ESTRUCTURALMENTE)
        self.assertIs(self.comparar(b=sin_unidad(self.b)).estado, E.INCOMPATIBLE)

    def test_dimension_fisica_desconocida_no_se_infiere_de_unidad(self):
        b = cambiar_campo(self.b, unidad=UnidadPerfil(U.ACREDITADA, "u-ficticia", VER))
        self.assertIs(self.comparar(b=b).estado, E.PENDIENTE_DE_EVIDENCIA)

    def test_finalidad_estructural_no_exige_inventar_unidad_o_tiempo(self):
        b = cambiar_campo(self.b, unidad=UnidadPerfil(), variable=None, respaldo_variable=Respaldo())
        r = self.comparar(b=b, f=replace(self.f, aspectos=(A.TIPO,)))
        self.assertIs(r.estado, E.APTO_ESTRUCTURALMENTE)
        self.assertIsNone(r.aptitud_referencias)
        self.assertIsNone(r.segundo.entrada.recurso.temporal)

    def test_convenciones_ausentes_distintas_son_incompatibles_sin_reemplazo(self):
        r = self.comparar(b=cambiar_campo(self.b, valores_ausentes=("NA",)))
        self.assertIs(r.estado, E.INCOMPATIBLE)
        self.assertIn("convenciones_ausentes_distintas", codigos(r))

    def test_marcadores_en_orden_distinto_no_cambian_convencion(self):
        r = self.comparar(b=cambiar_campo(self.b, valores_ausentes=("ausente-ficticio", "")))
        self.assertIs(r.estado, E.APTO_ESTRUCTURALMENTE)

    def test_agregacion_y_calendario_no_se_inventan(self):
        for nombre in ("agregacion", "calendario"):
            with self.subTest(nombre=nombre):
                self.assertIs(self.comparar(b=cambiar_campo(self.b, **{nombre: DeclaracionPerfil()})).estado,
                              E.PENDIENTE_DE_EVIDENCIA)
                self.assertIs(self.comparar(b=cambiar_campo(self.b, **{nombre: declarado("otra")})).estado,
                              E.INCOMPATIBLE)

    def test_version_local_no_admitida_es_incompatible(self):
        b = EntradaPerfil(self.b.entrada, replace(self.b.perfil, version="2"))
        r = self.comparar(b=b)
        self.assertIs(r.estado, E.INCOMPATIBLE)
        self.assertIn("version_perfil_no_admitida", codigos(r))

    def test_versiones_locales_diferentes_admitidas_exigen_cotejo_real(self):
        b = EntradaPerfil(self.b.entrada, replace(self.b.perfil, version="2"))
        f = replace(self.f, versiones_admitidas=(("perfil-A", "1"), ("perfil-B", "2")))
        self.assertIs(self.comparar(b=b, f=f).estado, E.APTO_ESTRUCTURALMENTE)
        self.assertIs(self.comparar(b=cambiar_campo(b, tipo=declarado("otro")), f=f).estado, E.INCOMPATIBLE)

    def test_identidad_y_version_iguales_con_definiciones_distintas_se_rechazan(self):
        b = vinculo("B", p=replace(self.a.perfil, ambito=declarado("otro ambito")))
        r = self.comparar(b=b)
        self.assertIs(r.estado, E.INCOMPATIBLE)
        self.assertIn("misma_identidad_y_version_de_perfil_con_definiciones_distintas", codigos(r))

    def test_ambito_no_acreditado_es_indeterminado(self):
        b = EntradaPerfil(self.b.entrada, replace(self.b.perfil, ambito=DeclaracionPerfil("ficticio", DEC)))
        self.assertIs(self.comparar(b=b).estado, E.PENDIENTE_DE_EVIDENCIA)

    def test_restriccion_bloqueante_aplica_a_finalidad_exacta(self):
        bloqueo = RestriccionQA("bloqueo-rc2", T.BLOQUEO_USO_DEL_RESULTADO,
                               (self.f.identificador,), "Solo ensayo ficticio")
        b = EntradaPerfil(self.b.entrada, replace(self.b.perfil, restricciones=(bloqueo,)))
        r = self.comparar(b=b)
        self.assertIs(r.estado, E.INCOMPATIBLE)
        self.assertIn(bloqueo, r.restricciones)
        otra = self.comparar(b=b, f=replace(self.f, identificador="otra-finalidad"))
        self.assertIs(otra.estado, E.APTO_ESTRUCTURALMENTE)
        self.assertIn(bloqueo, otra.restricciones)
        self.assertFalse(otra.autoriza_operacion)

    def test_restricciones_conflictivas_no_se_resuelven_reduciendo_bloqueos(self):
        a = EntradaPerfil(self.a.entrada, replace(self.a.perfil, restricciones=(
            RestriccionQA("r", T.INFORMATIVA, (), "motivo-1"),)))
        b = EntradaPerfil(self.b.entrada, replace(self.b.perfil, restricciones=(
            RestriccionQA("r", T.BLOQUEO_USO_DEL_RESULTADO, (self.f.identificador,), "motivo-2"),)))
        with self.assertRaises(ValueError):
            self.comparar(a=a, b=b)

    def test_incertidumbres_se_preservan_sin_convertir_texto_en_reglas(self):
        b = EntradaPerfil(replace(self.b.entrada, incertidumbres=("incertidumbre-entrada",)),
            replace(self.b.perfil, incertidumbres=("incertidumbre-perfil",)))
        r = self.comparar(b=b)
        self.assertIs(r.segundo, b)
        self.assertEqual(r.segundo.entrada.incertidumbres, ("incertidumbre-entrada",))
        self.assertEqual(r.segundo.perfil.incertidumbres, ("incertidumbre-perfil",))

    def test_determinismo_sin_reordenar_descriptores(self):
        primero = self.comparar()
        for _ in range(3):
            self.assertEqual(self.comparar(), primero)
        self.assertEqual(len(primero.diagnosticos), len(set(primero.diagnosticos)))


class ReferenciasEIdentidadesRC2Tests(unittest.TestCase):
    def setUp(self):
        self.a, self.b = vinculo(), vinculo("B")

    def test_tiempo_conocido_reutiliza_realmente_evaluador_y_conserva_marco(self):
        a, b = marco(self.a, temporal=temporal()), marco(self.b, temporal=temporal())
        f = finalidad(referencias=D.TEMPORAL)
        nativo = evaluar_aptitud(a.entrada.recurso, b.entrada.recurso, D.TEMPORAL)
        with patch("spica.interoperabilidad.perfiles.comparador.evaluar_aptitud", wraps=evaluar_aptitud) as evaluar:
            r = comparar_perfiles(a, b, f)
        evaluar.assert_called_once_with(a.entrada.recurso, b.entrada.recurso, D.TEMPORAL)
        self.assertEqual(r.aptitud_referencias, nativo)
        self.assertIs(r.estado, E.APTO_ESTRUCTURALMENTE)
        self.assertIs(r.primero.entrada.recurso.temporal, a.entrada.recurso.temporal)

    def test_tiempo_declarado_sin_interpretacion_es_indeterminado(self):
        a = marco(self.a, temporal=MarcoTemporal(valores_originales=(("HORA", "10000"),)))
        r = comparar_perfiles(a, marco(self.b, temporal=temporal()), finalidad(referencias=D.TEMPORAL))
        self.assertIs(r.estado, E.PENDIENTE_DE_EVIDENCIA)
        self.assertEqual(r.primero.entrada.recurso.temporal.valores_originales, (("HORA", "10000"),))
        self.assertIsNone(r.primero.entrada.recurso.temporal.zona_horaria_declarada)

    def test_datetime_sin_zona_permanece_ambiguo(self):
        fecha = datetime(2026, 1, 1)
        t = temporal(fecha_observacion=fecha, observaciones=periodo(fecha, fecha), zona_horaria_declarada=None)
        r = comparar_perfiles(marco(self.a, temporal=t), marco(self.b, temporal=t), finalidad(referencias=D.TEMPORAL))
        self.assertIs(r.estado, E.PENDIENTE_DE_EVIDENCIA)
        self.assertIsNone(t.fecha_observacion.tzinfo)

    def test_resoluciones_horaria_diaria_no_son_equivalentes(self):
        a, b = marco(self.a, temporal=temporal(resolucion="horaria")), marco(self.b, temporal=temporal(resolucion="diaria"))
        r = comparar_perfiles(a, b, finalidad(referencias=D.TEMPORAL))
        self.assertIs(r.estado, E.INCOMPATIBLE)
        self.assertIn("resoluciones_temporales_distintas_sin_agregacion", codigos(r))
        self.assertIs(r.aptitud_referencias.estado, E.PENDIENTE_DE_EVIDENCIA)

    def test_espacio_conocido_no_significa_coincidencia_geometrica(self):
        a, b = marco(self.a, espacial=espacial()), marco(self.b, espacial=espacial(coordenadas=(9, 12)))
        r = comparar_perfiles(a, b, finalidad(referencias=D.ESPACIAL))
        self.assertIs(r.estado, E.APTO_ESTRUCTURALMENTE)
        self.assertIn("sin_reproyeccion_distancias_intersecciones_o_topologia", r.aptitud_referencias.restricciones)
        self.assertNotEqual(a.entrada.recurso.espacial.coordenadas, b.entrada.recurso.espacial.coordenadas)

    def test_espacio_desconocido_conserva_no_evaluable_nativo(self):
        r = comparar_perfiles(self.a, self.b, finalidad(referencias=D.ESPACIAL))
        self.assertIs(r.estado, E.PENDIENTE_DE_EVIDENCIA)
        self.assertIs(r.aptitud_referencias.estado, E.NO_EVALUABLE)

    def test_crs_distintos_no_se_transforman_para_producir_compatibilidad(self):
        from test_interoperabilidad_modelos import crs
        a, b = marco(self.a, espacial=espacial()), marco(self.b, espacial=espacial(crs=(crs(declaracion="OTRO-CRS"),)))
        self.assertIs(comparar_perfiles(a, b, finalidad(referencias=D.ESPACIAL)).estado, E.PENDIENTE_DE_EVIDENCIA)

    def test_sitios_distintos_no_se_unen_por_nombre_o_coordenadas(self):
        a = marco(self.a, espacial=espacial(identificador_ubicacion="sitio-A", respaldo_identidad=VER))
        b = marco(self.b, espacial=espacial(identificador_ubicacion="sitio-B", respaldo_identidad=VER))
        r = comparar_perfiles(a, b, finalidad(referencias=D.ESPACIAL, requiere_mismo_sitio=True))
        self.assertIs(r.estado, E.INCOMPATIBLE)
        self.assertIn("identidades_sitio_distintas_sin_correspondencia", codigos(r))

    def test_identidad_sitio_ambigua_no_se_suple_por_nombre(self):
        a = marco(self.a, espacial=espacial(identificador_ubicacion="sitio-A", respaldo_identidad=DEC, identidad_ambigua=True))
        b = marco(self.b, espacial=espacial(identificador_ubicacion="sitio-A", respaldo_identidad=VER))
        self.assertIs(comparar_perfiles(a, b, finalidad(referencias=D.ESPACIAL, requiere_mismo_sitio=True)).estado,
                      E.PENDIENTE_DE_EVIDENCIA)

    def test_mismo_codigo_sitio_en_otro_producto_no_se_asocia(self):
        a = marco(self.a, espacial=espacial(identificador_ubicacion="codigo-compartido", respaldo_identidad=VER))
        recurso = replace(self.b.entrada.recurso, identidad=replace(self.b.entrada.recurso.identidad, producto_id="otro"),
                          espacial=a.entrada.recurso.espacial)
        b = EntradaPerfil(replace(self.b.entrada, recurso=recurso),
            replace(self.b.perfil, campos=(campo(variable=variable(producto_id="otro")),)))
        f = finalidad(referencias=D.ESPACIAL, requiere_mismo_sitio=True, aspectos=(A.TIPO,))
        r = comparar_perfiles(a, b, f)
        self.assertIs(r.estado, E.INCOMPATIBLE)
        self.assertIn("identidades_sitio_distintas_sin_correspondencia", codigos(r))

    def test_mismo_sitio_documentado_no_ejecuta_asociacion(self):
        m = espacial(identificador_ubicacion="sitio-ficticio", respaldo_identidad=VER)
        r = comparar_perfiles(marco(self.a, espacial=m), marco(self.b, espacial=m),
            finalidad(referencias=D.ESPACIAL, requiere_mismo_sitio=True))
        self.assertIs(r.estado, E.APTO_ESTRUCTURALMENTE)
        self.assertIn("identidad_sitio_literal_con_respaldo", codigos(r))
        self.assertFalse(r.autoriza_operacion)

    def test_recursos_de_nombre_similar_no_se_declaran_identicos(self):
        r = comparar_perfiles(self.a, self.b, finalidad(requiere_mismo_recurso=True))
        self.assertIs(r.estado, E.INCOMPATIBLE)
        self.assertIn("identidades_recurso_distintas", codigos(r))
        self.assertNotEqual(r.primero.entrada.recurso.identidad, r.segundo.entrada.recurso.identidad)

    def test_mismo_contenido_en_dos_proyectos_no_fusiona_identidades(self):
        p = ContextoProyecto("contexto-B", ProyectoCientifico("proyecto-B"), ConfiguracionContexto("otra", "1"))
        b = vinculo("B", proyecto=p)
        r = comparar_perfiles(self.a, b, finalidad())
        self.assertIs(r.estado, E.APTO_ESTRUCTURALMENTE)
        self.assertIn("contextos_proyecto_distintos_no_fusionados", codigos(r))
        self.assertEqual(self.a.entrada.sha256_declarado, b.entrada.sha256_declarado)
        self.assertNotEqual(self.a.entrada.objeto, b.entrada.objeto)

    def test_hash_declarado_igual_sin_evidencia_no_acredita_identidad_contenido(self):
        r = comparar_perfiles(self.a, self.b, finalidad(requiere_mismo_contenido=True))
        self.assertIs(r.estado, E.PENDIENTE_DE_EVIDENCIA)
        self.assertIn("identidad_contenido_sin_evidencia_fisica_aportada", codigos(r))

    def test_contenido_distinto_incompatible_con_finalidad_de_identidad(self):
        b = EntradaPerfil(replace(self.b.entrada, sha256_declarado="b" * 64), self.b.perfil)
        self.assertIs(comparar_perfiles(self.a, b, finalidad(requiere_mismo_contenido=True)).estado, E.INCOMPATIBLE)

    def test_evidencia_fisica_aportada_se_conserva_sin_reverificar_archivos(self):
        def con_evidencia(v):
            e = EvidenciaLocal(EstadoLocal.INTEGRO, FECHA, PROC, SHA, 7, "asset-" + v.entrada.entrada_id)
            return EntradaPerfil(replace(v.entrada, evidencia_local=e, asset_id=e.activo_id), v.perfil)
        a, b = con_evidencia(self.a), con_evidencia(self.b)
        r = comparar_perfiles(a, b, finalidad(requiere_mismo_contenido=True))
        self.assertIs(r.estado, E.APTO_ESTRUCTURALMENTE)
        self.assertIn("sin_comprobacion_fisica_de_contenido", r.limitaciones)
        self.assertIs(r.primero.entrada.evidencia_local, a.entrada.evidencia_local)


class IntegracionContextosRC2Tests(unittest.TestCase):
    def test_vinculo_preserva_todas_las_identidades_y_procedencia_por_referencia(self):
        v = vinculo()
        self.assertIs(v.entrada.recurso.procedencia, PROC)
        self.assertEqual(v.entrada.entrada_id, "entrada-A")
        self.assertEqual(v.entrada.proyecto.project_id, "proyecto-A")
        self.assertEqual(v.entrada.objeto.object_id, "objeto-A")
        self.assertEqual(v.entrada.sha256_declarado, SHA)
        self.assertIsNone(v.entrada.asset_id)

    def test_perfil_incompatible_con_tipo_o_identificador_rc1_se_rechaza(self):
        v = vinculo()
        for p in (replace(v.perfil, identificador="otro"), replace(v.perfil, tipo_recurso="raster")):
            with self.subTest(p=p), self.assertRaises(ValueError):
                EntradaPerfil(v.entrada, p)

    def test_variable_fuera_de_fuente_o_producto_se_rechaza(self):
        v = vinculo()
        for var in (variable(producto_id="otro"), variable(fuente=Fuente("otra", "otra"))):
            with self.subTest(var=var), self.assertRaises(ValueError):
                EntradaPerfil(v.entrada, replace(v.perfil, campos=(campo(variable=var),)))

    def test_campos_fuera_de_atributos_explicitos_no_se_inventan(self):
        with self.assertRaises(ValueError):
            marco(vinculo(), atributos_declarados=("otro-campo",))
        a = marco(vinculo(), atributos_declarados=(" magnitud original ", "campo-extra"))
        self.assertEqual(len(a.perfil.campos), 1)

    def test_recurso_desconocido_no_se_completa_desde_variables(self):
        a = vinculo(recurso=None)
        r = comparar_perfiles(a, vinculo("B"), finalidad())
        self.assertIs(r.estado, E.PENDIENTE_DE_EVIDENCIA)
        self.assertIsNone(a.entrada.recurso)

    def test_producto_desconocido_no_se_infiere_del_catalogo_variable(self):
        a = vinculo()
        a = marco(a, identidad=replace(a.entrada.recurso.identidad, producto_id=None))
        r = comparar_perfiles(a, vinculo("B"), finalidad())
        self.assertIs(r.estado, E.PENDIENTE_DE_EVIDENCIA)
        self.assertIn("producto_no_documentado", codigos(r))
        self.assertIsNone(a.entrada.recurso.identidad.producto_id)
        self.assertEqual(a.perfil.campos[0].variable.producto_id, "producto-ficticio")

    def test_perfil_desconocido_en_rc1_se_conserva_y_diagnostica(self):
        a = vinculo(perfil_estructural=None)
        r = comparar_perfiles(a, vinculo("B"), finalidad())
        self.assertIs(r.estado, E.PENDIENTE_DE_EVIDENCIA)
        self.assertIsNone(a.entrada.perfil_estructural)

    def test_procedencia_sin_evidencia_impide_compatibilidad_positiva(self):
        a = marco(vinculo(), procedencia=replace(PROC, evidencia=None))
        self.assertIs(comparar_perfiles(a, vinculo("B"), finalidad()).estado, E.PENDIENTE_DE_EVIDENCIA)

    def test_contradiccion_del_recurso_no_desaparece_en_perfil(self):
        a = marco(vinculo(), contradicciones_declaradas=("contradiccion-ficticia",))
        self.assertIs(comparar_perfiles(a, vinculo("B"), finalidad()).estado, E.INCOMPATIBLE)

    def test_compatibilidad_no_autoriza_ni_marca_operacion_ejecutada(self):
        a, b, f = vinculo(), vinculo("B"), finalidad()
        o = ContextoOperacion("operacion-rc2", a.entrada.proyecto, (a.entrada, b.entrada),
            TipoOperacion.DESCRIPCION_ESTRUCTURAL, f.descripcion)
        r = comparar_perfiles(a, b, f, operacion=o)
        self.assertIs(r.estado, E.APTO_ESTRUCTURALMENTE)
        self.assertIs(r.operacion, o)
        self.assertIs(o.estado, EstadoOperacion.DECLARADA)
        self.assertFalse(r.autoriza_operacion)
        self.assertFalse(o.autoriza_operacion)
        with self.assertRaises(TypeError):
            bool(r)

    def test_operacion_con_otra_finalidad_o_entradas_no_se_vincula(self):
        a, b, f = vinculo(), vinculo("B"), finalidad()
        o = ContextoOperacion("operacion", a.entrada.proyecto, (a.entrada,),
            TipoOperacion.DESCRIPCION_ESTRUCTURAL, f.descripcion)
        with self.assertRaises(ValueError):
            comparar_perfiles(a, b, f, operacion=o)
        with self.assertRaises(ValueError):
            comparar_perfiles(a, a, f, operacion=replace(o, proposito="otra finalidad"))

    def test_bloqueo_de_operacion_se_conserva_en_resultado(self):
        a, b, f = vinculo(), vinculo("B"), finalidad()
        bloqueo = RestriccionQA("limite-operacion", T.BLOQUEO_USO_DEL_RESULTADO, (f.identificador,), "ensayo")
        o = ContextoOperacion("operacion", a.entrada.proyecto, (a.entrada, b.entrada),
            TipoOperacion.DESCRIPCION_ESTRUCTURAL, f.descripcion, restricciones_adicionales=(bloqueo,))
        r = comparar_perfiles(a, b, f, operacion=o)
        self.assertIs(r.estado, E.INCOMPATIBLE)
        self.assertIn(bloqueo, r.restricciones)
        self.assertIn(bloqueo, replace(r, restricciones=()).restricciones)

    def test_restricciones_de_proyecto_entrada_y_perfil_se_acumulan(self):
        a = vinculo()
        r1 = RestriccionQA("r-proyecto", T.INFORMATIVA, (), "límite de proyecto")
        r2 = RestriccionQA("r-entrada", T.INFORMATIVA, (), "límite de entrada")
        r3 = RestriccionQA("r-perfil", T.INFORMATIVA, (), "límite de perfil")
        a = EntradaPerfil(replace(a.entrada, proyecto=replace(a.entrada.proyecto, restricciones=(r1,)),
                                  restricciones_adicionales=(r2,)), replace(a.perfil, restricciones=(r3,)))
        r = comparar_perfiles(a, vinculo("B"), finalidad())
        self.assertEqual(r.restricciones, (r1, r2, r3))
        self.assertEqual(replace(r, restricciones=()).restricciones, (r1, r2, r3))

    def test_perfil_qa0_existente_no_se_universaliza_ni_inventa_tipos(self):
        from spica.adquisicion.consultas_locales import ENCABEZADO_SENAMHI
        from test_contextos_rc1 import entrada, resultado
        from spica.calidad.exportacion import ContextoExportacionQA, exportar_resultado_json
        e = entrada()
        p = PerfilInformacion(e.perfil_estructural, "fixture-rc2", e.tipo_recurso,
            tuple(CampoInformacion(n, DeclaracionPerfil()) for n in ENCABEZADO_SENAMHI),
            ambito=declarado("solo encabezado sintético; sin acreditación PNDA"))
        v = EntradaPerfil(e, p)
        f = FinalidadCompatibilidad("cotejar-estructura-qa0", "Describir un encabezado conocido",
            tuple((n, n) for n in ENCABEZADO_SENAMHI), ((p.identificador, p.version),), (A.TIPO,))
        nativo = resultado(e)
        contexto = ContextoExportacionQA("fixture-rc2", "sin-ejecucion-nueva", "fila-1")
        anterior = exportar_resultado_json(nativo, contexto)
        r = comparar_perfiles(v, v, f)
        self.assertIs(r.estado, E.PENDIENTE_DE_EVIDENCIA)
        self.assertEqual(exportar_resultado_json(nativo, contexto), anterior)
        self.assertEqual(dict(nativo.registro.campos_originales)["HORA"], "10000")
        self.assertEqual(dict(nativo.registro.campos_originales)["UBIGEO"], "01234.0")

    def test_importacion_comparacion_sin_red_sqlite_o_escrituras(self):
        codigo = r'''
import os, sys
def denegar(evento, args):
    if evento.startswith('socket.') or evento in ('sqlite3.connect', 'os.mkdir', 'os.remove', 'os.rename'):
        raise AssertionError('efecto_no_permitido_rc2')
    if evento == 'open':
        modo, flags = args[1:3]
        if (isinstance(modo, str) and any(c in modo for c in 'wax+')) or (
                isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC)):
            raise AssertionError('escritura_no_permitida_rc2')
        if 'spica_datos' in str(args[0]).lower():
            raise AssertionError('lectura_operativa_no_permitida_rc2')
sys.addaudithook(denegar)
sys.path[:0] = ['src', 'tests']
IMPORTACION_PREVIA
from test_perfiles_informacion_rc2 import vinculo, finalidad, comparar_perfiles
r = comparar_perfiles(vinculo(), vinculo('B'), finalidad())
assert r.estado.value == 'apto_estructuralmente'
assert not r.autoriza_operacion
print('RC2_sin_efectos')
'''
        for previa in ("import spica.contextos", "import spica.interoperabilidad.perfiles"):
            with self.subTest(orden=previa):
                r = subprocess.run([sys.executable, "-B", "-c", codigo.replace("IMPORTACION_PREVIA", previa)],
                    cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, timeout=30)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertEqual(r.stdout.strip(), "RC2_sin_efectos")


if __name__ == "__main__":
    unittest.main()
