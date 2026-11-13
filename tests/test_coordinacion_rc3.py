"""Coordinación de DTO y un componente QA real, exclusivamente con fixtures."""

from dataclasses import FrozenInstanceError, replace
import csv
from pathlib import Path
import subprocess
import sys
import tempfile
from threading import Event
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from spica.contextos import (
    ContextoOperacion, EstadoOperacion as S, TipoOperacion as T, VinculoResultadoQA,
    cambiar_estado,
)
from spica.calidad import EvaluadorNivel0, ConfiguracionQA, LimitesQA, ProcedenciaQA
from spica.calidad.modelos import EstadoEvaluacionQA, EstadoResultadoQA
from spica.calidad.restricciones import RestriccionQA, TipoRestriccionQA as TR
from spica.adquisicion.consultas_locales import ENCABEZADO_SENAMHI
from spica.adquisicion.verificacion import LectorCSV
from spica.interoperabilidad.adaptadores import DiagnosticoAdaptacion as Diag, NivelDiagnostico as N
from spica.interoperabilidad.modelos import EstadoAptitud as E
from spica.interoperabilidad.perfiles import EntradaPerfil, PerfilInformacion, CampoInformacion, DeclaracionPerfil, AspectoCampo as A
from spica.coordinacion import (
    CierreQA, ComposicionOperaciones, DependenciaOperacion as Dep, LimitesComposicion,
    NodoOperacion, RequisitoCompatibilidad, VERSION_COORDINACION, inspeccionar_composicion,
)
# Solo fabricantes de datos existentes; no se importan TestCase ni se abren datos.
from test_perfiles_informacion_rc2 import vinculo, finalidad, cambiar_campo, declarado
from test_contextos_rc1 import entrada as entrada_qa, proyecto as proyecto_qa, resultado as resultado_fixture


def nodo(identidad="A", *, entrada=None, **kw):
    e = vinculo().entrada if entrada is None else entrada
    o = ContextoOperacion(identidad, e.proyecto, (e,), T.DESCRIPCION_ESTRUCTURAL, "Describir fixture RC3")
    d = dict(contexto=o, usos_declarados=("describir",))
    d.update(kw)
    return NodoOperacion(**d)


def composicion(operaciones=None, **kw):
    if operaciones is None:
        operaciones = (nodo(),)
    proyecto = operaciones[0].contexto.proyecto if operaciones else vinculo().entrada.proyecto
    d = dict(identificador="composicion-sintetica", proyecto=proyecto,
             operaciones=operaciones, dependencias=(), finalidad="Cotejo sintético offline RC3")
    d.update(kw)
    return ComposicionOperaciones(**d)


def con_perfiles(*, tipo=None, desconocido=False):
    a, b = vinculo(), vinculo("B")
    if tipo is not None or desconocido:
        b = cambiar_campo(b, tipo=DeclaracionPerfil() if desconocido else declarado(tipo))
    f = finalidad(aspectos=(A.TIPO,))
    o = ContextoOperacion("comparar", a.entrada.proyecto, (a.entrada, b.entrada), T.DESCRIPCION_ESTRUCTURAL, f.descripcion)
    return NodoOperacion(o, (f.identificador,), (RequisitoCompatibilidad(a, b, f),))


def codigos(informe):
    return tuple(d.codigo for d in informe.diagnosticos) + tuple(d.codigo for n in informe.operaciones for d in n.diagnosticos)


def por_id(informe, identidad):
    return next(i for i in informe.operaciones if i.nodo.contexto.operacion_id == identidad)


def qa_real(e=None, *, parcial=False):
    """Única rama que escribe: CSV inventado en TEMP propio y retirado al salir."""
    e = entrada_qa() if e is None else e
    cfg = ConfiguracionQA(reglas=("L0-EST-001",))
    limites = LimitesQA(max_registros=4, max_resultados=1 if parcial else 8)
    o = ContextoOperacion("qa-previo", e.proyecto, (e,), T.QA_NIVEL0,
        "Comprobar una fila ficticia", limites_qa=limites, configuracion_qa=cfg)
    o = cambiar_estado(cambiar_estado(o, S.PLANIFICADA), S.INICIADA)
    r = resultado_fixture(e)
    with tempfile.TemporaryDirectory(prefix="spica-rc3-qa-") as temporal:
        ruta = Path(temporal) / "fixture.csv"
        with ruta.open("w", encoding="utf-8", newline="") as archivo:
            escritor = csv.writer(archivo)
            escritor.writerow(ENCABEZADO_SENAMHI)
            escritor.writerow(r.registro.valores_csv_originales)
        proc = ProcedenciaQA(e.recurso.identidad.fuente, e.recurso.identidad.recurso_id,
                            asset_id=e.asset_id, sha256_referencia=e.sha256_declarado)
        lector = LectorCSV(ruta, codificacion="utf-8", delimitador=",", encabezado_declarado=True,
                          campos_esperados=len(ENCABEZADO_SENAMHI))
        with EvaluadorNivel0(lector, proc, configuracion=cfg, limites=limites) as evaluador:
            resultados = tuple(evaluador)
        informe = evaluador.informe
    assert not Path(temporal).exists()
    referencias = tuple("resultado-" + str(i) for i in range(len(resultados)))
    estado = S.PARCIAL if parcial else S.CONCLUIDA
    ds = (Diag("prefijo_qa_por_limite", "qa", N.FALTANTE),) if parcial else ()
    o = cambiar_estado(o, estado, diagnosticos=ds, referencias_resultado=referencias)
    vs = tuple(VinculoResultadoQA(o, e.entrada_id, ref, r) for ref, r in zip(referencias, resultados))
    return NodoOperacion(o, ("evaluar_estructura_qa0",), cierre_qa=CierreQA(informe, vs))


def piloto(qa, *, incompatible=False, pendiente=False):
    e1 = qa.contexto.entradas[0]
    e2 = replace(e1, entrada_id="entrada-2", objeto=replace(e1.objeto, object_id="otro-objeto-ficticio"))
    p1 = PerfilInformacion(e1.perfil_estructural, "fixture-1", e1.tipo_recurso,
        (CampoInformacion("ID", declarado("texto-sintetico")),), ambito=declarado("solo fixture RC3"))
    p2 = replace(p1, version="fixture-2", campos=(CampoInformacion("ID", DeclaracionPerfil() if pendiente else
        declarado("otro-tipo" if incompatible else "texto-sintetico")),))
    f = finalidad(campos=(("ID", "ID"),), versiones_admitidas=((p1.identificador, p1.version),
        (p2.identificador, p2.version)), aspectos=(A.TIPO,))
    o = ContextoOperacion("comparar", e1.proyecto, (e1, e2), T.DESCRIPCION_ESTRUCTURAL, f.descripcion)
    b = NodoOperacion(o, (f.identificador,), (RequisitoCompatibilidad(EntradaPerfil(e1, p1), EntradaPerfil(e2, p2), f),))
    independiente = nodo("independiente", entrada=e2)
    return composicion((qa, b, independiente), dependencias=(Dep(qa.contexto.operacion_id, o.operacion_id,
        (qa.contexto.referencias_resultado[0],)),))


class ContratosCoordinacionRC3Tests(unittest.TestCase):
    def test_contrato_versionado_e_inmutable_sin_ejecucion(self):
        c = composicion()
        self.assertEqual(c.version_contrato, VERSION_COORDINACION)
        self.assertFalse(c.autoriza_operacion)
        with self.assertRaises(FrozenInstanceError):
            c.finalidad = "otra"
        with self.assertRaises(TypeError):
            bool(c)

    def test_tipos_listas_y_campos_invalidos_rechazados(self):
        for crear in (lambda: composicion(operaciones=[]), lambda: replace(composicion(), operaciones=(object(),)),
                lambda: NodoOperacion({}, ("x",)), lambda: Dep("", "B"),
                lambda: CierreQA({}, ()), lambda: RequisitoCompatibilidad({}, {}, finalidad()),
                lambda: composicion(limites={})):
            with self.subTest(crear=crear), self.assertRaises((TypeError, ValueError)):
                crear()

    def test_version_incompatible_no_se_negocia(self):
        with self.assertRaises(ValueError):
            composicion(version_contrato="99")
        with self.assertRaises(ValueError):
            replace(nodo().contexto, version_contrato="99")

    def test_presupuestos_invalidos_y_booleanos(self):
        for cambio in (dict(max_operaciones=0), dict(max_dependencias=True), dict(max_profundidad=33),
                dict(max_bytes_texto=-1), dict(max_visitas_descriptores=200_001)):
            with self.subTest(cambio=cambio), self.assertRaises(ValueError):
                LimitesComposicion(**cambio)

    def test_cota_dura_de_nodos_y_aristas(self):
        e = vinculo().entrada
        with self.assertRaises(ValueError):
            composicion(tuple(nodo(str(i), entrada=e) for i in range(33)))
        with self.assertRaises(ValueError):
            composicion(dependencias=tuple(Dep("A", "B") for _ in range(129)))

    def test_inventario_de_entradas_superior_a_rc1_se_diagnostica_sin_desbordarlo(self):
        e = vinculo().entrada
        entradas = tuple(replace(e, entrada_id="e" + str(i), objeto=replace(e.objeto, object_id="o" + str(i))) for i in range(257))
        ns = tuple(NodoOperacion(ContextoOperacion("n" + str(i), e.proyecto, entradas[i:i + 16],
            T.DESCRIPCION_ESTRUCTURAL, "fixture"), ("describir",)) for i in range(0, len(entradas), 16))
        r = inspeccionar_composicion(composicion(ns, limites=LimitesComposicion(max_operaciones=32)))
        self.assertIn("cota_inventario_entradas_rc1_excedida", codigos(r))
        self.assertEqual(r.habilitadas_declarativamente, ())

    def test_usos_y_referencias_repetidas_rechazados(self):
        with self.assertRaises(ValueError):
            nodo(usos_declarados=())
        with self.assertRaises(ValueError):
            Dep("A", "B", ("r", "r"))
        with self.assertRaises(ValueError):
            nodo(usos_declarados=("x", "x"))

    def test_restriccion_alterada_falla_cerrada(self):
        r = RestriccionQA("r", TR.BLOQUEO_USO_DEL_RESULTADO, ("describir",), "original")
        a = nodo()
        a = replace(a, contexto=replace(a.contexto, restricciones_adicionales=(r,)))
        with self.assertRaises(ValueError):
            composicion((a,), restricciones_adicionales=(replace(r, tipo=TR.INFORMATIVA),))


class GrafosCoordinacionRC3Tests(unittest.TestCase):
    def setUp(self):
        self.e = vinculo().entrada
        self.a, self.b, self.c = tuple(nodo(i, entrada=self.e) for i in ("A", "B", "C"))

    def test_composicion_valida_sin_operaciones_ejecutadas(self):
        r = inspeccionar_composicion(composicion((self.a,)))
        self.assertIs(r.estado_estructural, E.APTO_ESTRUCTURALMENTE)
        self.assertEqual(r.habilitadas_declarativamente, ("A",))
        self.assertFalse(r.ejecucion_realizada)
        self.assertFalse(r.recursos_reservados)
        self.assertFalse(r.autoriza_operacion)
        self.assertIs(r.operaciones[0].nodo.contexto, self.a.contexto)
        with self.assertRaises(TypeError):
            bool(r)

    def test_composicion_vacia_no_es_exito_vacio(self):
        r = inspeccionar_composicion(composicion(()))
        self.assertIn("composicion_sin_operaciones", codigos(r))
        self.assertIs(r.estado_estructural, E.INCOMPATIBLE)
        self.assertEqual(r.habilitadas_declarativamente, ())

    def test_operaciones_duplicadas_se_diagnostican(self):
        r = inspeccionar_composicion(composicion((self.a, self.a)))
        self.assertIn("identidad_operacion_duplicada", codigos(r))
        self.assertEqual(r.habilitadas_declarativamente, ())

    def test_dependencia_inexistente(self):
        r = inspeccionar_composicion(composicion((self.a,), dependencias=(Dep("ausente", "A"),)))
        self.assertIn("dependencia_inexistente", codigos(r))
        self.assertEqual(r.orden_precedencia, ())

    def test_autodependencia(self):
        r = inspeccionar_composicion(composicion((self.a,), dependencias=(Dep("A", "A"),)))
        self.assertIn("dependencia_de_si_misma", codigos(r))

    def test_ciclo_y_prefijo_aciclico_no_producen_habilitacion(self):
        c = composicion((self.a, self.b, self.c), dependencias=(Dep("A", "B"), Dep("B", "A")))
        r = inspeccionar_composicion(c)
        self.assertIn("dependencia_circular", codigos(r))
        self.assertEqual(r.orden_precedencia, ())
        self.assertEqual(r.habilitadas_declarativamente, ())

    def test_arista_duplicada_no_equivale_a_dos_evidencias(self):
        r = inspeccionar_composicion(composicion((self.a, self.b), dependencias=(Dep("A", "B"), Dep("A", "B"))))
        self.assertIn("dependencia_duplicada", codigos(r))

    def test_orden_determinista_independiente_del_orden_de_nodos_y_aristas(self):
        ds = (Dep("A", "C"), Dep("B", "C"))
        r = inspeccionar_composicion(composicion((self.c, self.b, self.a), dependencias=ds))
        s = inspeccionar_composicion(composicion((self.a, self.c, self.b), dependencias=tuple(reversed(ds))))
        self.assertEqual(r.orden_precedencia, ("A", "B", "C"))
        self.assertEqual(r.orden_precedencia, s.orden_precedencia)
        self.assertEqual(r.habilitadas_declarativamente, ("A", "B"))

    def test_dependencia_no_se_satisface_por_estar_lista_la_predecesora(self):
        r = inspeccionar_composicion(composicion((self.a, self.b), dependencias=(Dep("A", "B"),)))
        self.assertIs(por_id(r, "A").estado_estructural, E.APTO_ESTRUCTURALMENTE)
        self.assertIs(por_id(r, "B").estado_estructural, E.PENDIENTE_DE_EVIDENCIA)
        self.assertIn("dependencia_sin_cierre_tecnico_compatible_aportado", codigos(r))

    def test_conclusion_declarada_y_referencia_inventada_no_satisfacen_dependencia(self):
        a = replace(self.a, contexto=replace(self.a.contexto, estado=S.CONCLUIDA, referencias_resultado=("inventada",)))
        r = inspeccionar_composicion(composicion((a, self.b), dependencias=(Dep("A", "B", ("inventada",)),)))
        self.assertIn("conclusion_declarada_sin_cierre_tecnico_admitido", codigos(r))
        self.assertEqual(r.habilitadas_declarativamente, ())

    def test_referencia_requerida_ausente_se_diagnostica(self):
        r = inspeccionar_composicion(composicion((self.a, self.b), dependencias=(Dep("A", "B", ("ausente",)),)))
        self.assertIn("referencia_requerida_no_declarada_por_predecesora", codigos(r))

    def test_dos_operaciones_sobre_misma_entrada_permanecen_independientes(self):
        r = inspeccionar_composicion(composicion((self.a, self.b)))
        self.assertEqual(r.habilitadas_declarativamente, ("A", "B"))
        self.assertIs(r.operaciones[0].nodo.contexto.entradas[0], r.operaciones[1].nodo.contexto.entradas[0])

    def test_entrada_recreada_no_sustituye_instantanea_canonica(self):
        b = replace(self.b, contexto=replace(self.b.contexto, entradas=(replace(self.e),)))
        r = inspeccionar_composicion(composicion((self.a, b)))
        self.assertIn("entrada_redefinida_o_instantanea_no_canonica", codigos(r))

    def test_profundo_excede_limite_declarado(self):
        r = inspeccionar_composicion(composicion((self.a, self.b, self.c),
            dependencias=(Dep("A", "B"), Dep("B", "C")), limites=LimitesComposicion(max_profundidad=2)))
        self.assertIn("profundidad_composicion_excedida", codigos(r))
        self.assertEqual(r.habilitadas_declarativamente, ())

    def test_cuota_de_operaciones_y_dependencias(self):
        for limites, ds, codigo in ((LimitesComposicion(max_operaciones=1), (), "cuota_operaciones_excedida"),
                (LimitesComposicion(max_dependencias=1), (Dep("A", "C"), Dep("B", "C")), "cuota_dependencias_excedida")):
            with self.subTest(codigo=codigo):
                r = inspeccionar_composicion(composicion((self.a, self.b, self.c), dependencias=ds, limites=limites))
                self.assertIn(codigo, codigos(r))

    def test_cotas_textuales_y_de_visitas_no_generan_medicion_completa(self):
        for limites in (LimitesComposicion(max_bytes_texto=8), LimitesComposicion(max_visitas_descriptores=8)):
            with self.subTest(limites=limites):
                r = inspeccionar_composicion(composicion((self.a,), limites=limites))
                self.assertIs(r.estado_estructural, E.INCOMPATIBLE)
                self.assertIsNone(r.bytes_texto_descriptores)
                self.assertEqual(r.habilitadas_declarativamente, ())

    def test_medicion_textual_utf8_por_ocurrencia_no_es_rss(self):
        c = composicion((self.a,), finalidad="a" * 512)
        a = inspeccionar_composicion(c)
        b = inspeccionar_composicion(replace(c, finalidad="é" * 512))
        self.assertEqual(b.bytes_texto_descriptores - a.bytes_texto_descriptores, 512)
        self.assertEqual(b.visitas_descriptores, a.visitas_descriptores)
        self.assertFalse(b.recursos_reservados)

    def test_configuracion_qa_con_regla_inexistente_no_habilita_operacion(self):
        qa = ContextoOperacion("qa", self.e.proyecto, (self.e,), T.QA_NIVEL0, "fixture",
            limites_qa=LimitesQA(), configuracion_qa=ConfiguracionQA(reglas=("INEXISTENTE",)))
        r = inspeccionar_composicion(composicion((NodoOperacion(qa, ("evaluar_estructura_qa0",)),)))
        self.assertIn("configuracion_qa_no_admitida", codigos(r))
        self.assertEqual(r.habilitadas_declarativamente, ())

    def test_perfil_qa_no_admitido_no_se_promueve_por_configuracion_valida(self):
        qa = ContextoOperacion("qa", self.e.proyecto, (self.e,), T.QA_NIVEL0, "fixture",
            limites_qa=LimitesQA(), configuracion_qa=ConfiguracionQA(reglas=("L0-EST-001",)))
        r = inspeccionar_composicion(composicion((NodoOperacion(qa, ("evaluar_estructura_qa0",)),)))
        self.assertIn("perfil_o_revision_qa_no_admitidos", codigos(r))
        self.assertEqual(r.habilitadas_declarativamente, ())

    def test_estado_cancelado_fallido_parcial_o_iniciado_no_se_rehabilita(self):
        for estado in (S.CANCELADA, S.FALLIDA, S.PARCIAL, S.INICIADA):
            ds = () if estado is S.INICIADA else (Diag("causa-aportada", "operacion", N.FALTANTE),)
            refs = ("resultado-parcial",) if estado is S.PARCIAL else ()
            o = replace(self.a.contexto, estado=estado, diagnosticos=ds, referencias_resultado=refs)
            r = inspeccionar_composicion(composicion((replace(self.a, contexto=o),)))
            self.assertEqual(r.habilitadas_declarativamente, ())
            self.assertIs(r.operaciones[0].nodo.contexto, o)
            self.assertEqual(o.referencias_resultado, refs)


class PerfilesYRestriccionesRC3Tests(unittest.TestCase):
    def test_rc2_realmente_recalculado_y_resultado_conservado(self):
        n = con_perfiles()
        from spica.interoperabilidad.perfiles import comparar_perfiles
        with patch('spica.coordinacion.inspeccion.comparar_perfiles', wraps=comparar_perfiles) as comparar:
            r = inspeccionar_composicion(composicion((n,)))
        comparar.assert_called_once()
        self.assertIs(r.operaciones[0].compatibilidades[0].estado, E.APTO_ESTRUCTURALMENTE)
        self.assertEqual(r.habilitadas_declarativamente, ("comparar",))

    def test_incompatibilidad_no_se_ignora(self):
        r = inspeccionar_composicion(composicion((con_perfiles(tipo="otro"),)))
        self.assertIs(r.estado_estructural, E.INCOMPATIBLE)
        self.assertEqual(r.habilitadas_declarativamente, ())

    def test_pendiente_de_evidencia_no_se_promueve(self):
        r = inspeccionar_composicion(composicion((con_perfiles(desconocido=True),)))
        self.assertIs(r.estado_estructural, E.PENDIENTE_DE_EVIDENCIA)
        self.assertIs(r.operaciones[0].compatibilidades[0].estado, E.PENDIENTE_DE_EVIDENCIA)

    def test_finalidad_o_entradas_ajenas_no_se_evalua(self):
        n = con_perfiles()
        for o in (replace(n.contexto, proposito="otro"), replace(n.contexto, entradas=(n.contexto.entradas[0],))):
            with self.subTest(o=o), patch('spica.coordinacion.inspeccion.comparar_perfiles', side_effect=AssertionError('no_comparar')):
                r = inspeccionar_composicion(composicion((replace(n, contexto=o),)))
                self.assertIn("requisito_rc2_ajeno_a_operacion", codigos(r))

    def test_alcance_no_incluye_finalidad_y_se_conserva_incertidumbre(self):
        n = replace(con_perfiles(), usos_declarados=("otra-finalidad",))
        r = inspeccionar_composicion(composicion((n,)))
        self.assertIn("finalidad_rc2_fuera_de_usos_declarados", codigos(r))
        self.assertEqual(r.habilitadas_declarativamente, ())

    def test_restriccion_bloqueante_no_desaparece(self):
        bloqueo = RestriccionQA("bloqueo", TR.BLOQUEO_USO_DEL_RESULTADO, ("describir",), "motivo-original")
        r = inspeccionar_composicion(composicion(restricciones_adicionales=(bloqueo,)))
        self.assertIn("restriccion_bloqueante_para_uso_declarado", codigos(r))
        self.assertIs(r.restricciones[0].restriccion, bloqueo)

    def test_aplicabilidad_desconocida_de_bloqueo_es_pendiente(self):
        bloqueo = RestriccionQA("bloqueo", TR.BLOQUEO_USO_DEL_RESULTADO, ("otro-uso",), "motivo")
        r = inspeccionar_composicion(composicion((nodo(usos_declarados=None),), restricciones_adicionales=(bloqueo,)))
        self.assertIs(r.estado_estructural, E.PENDIENTE_DE_EVIDENCIA)
        self.assertIn("aplicabilidad_restriccion_no_resuelta", codigos(r))

    def test_propagacion_transitiva_sin_duplicar_como_evidencia_independiente(self):
        e = vinculo().entrada
        bloqueo = RestriccionQA("r", TR.BLOQUEO_USO_DEL_RESULTADO, ("describir",), "conservar")
        a = nodo("A", entrada=e)
        a = replace(a, contexto=replace(a.contexto, restricciones_adicionales=(bloqueo,)))
        b, c = nodo("B", entrada=e), nodo("C", entrada=e)
        r = inspeccionar_composicion(composicion((a, b, c), dependencias=(Dep("A", "B"), Dep("B", "C"))))
        for i in r.operaciones:
            self.assertEqual(len([p for p in i.restricciones if p.restriccion.codigo == "r"]), 1)
            self.assertIn("contexto_operacion:A", i.restricciones[0].origenes)
        self.assertIs(por_id(r, "C").estado_estructural, E.INCOMPATIBLE)

    def test_diagnostico_de_entrada_contradictoria_se_conserva(self):
        n = nodo()
        e = n.contexto.entradas[0]
        e = replace(e, recurso=replace(e.recurso, contradicciones_declaradas=("conflicto-ficticio",)))
        n = replace(n, contexto=replace(n.contexto, entradas=(e,)))
        self.assertIs(inspeccionar_composicion(composicion((n,))).estado_estructural, E.INCOMPATIBLE)


class IntegracionQARC3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qa = qa_real()

    def test_cierre_qa_real_satisface_dependencia_tecnica_en_piloto(self):
        c = piloto(self.qa)
        r = inspeccionar_composicion(c)
        self.assertIs(r.estado_estructural, E.APTO_ESTRUCTURALMENTE)
        self.assertTrue(por_id(r, "qa-previo").cierre_qa_coherente_completo)
        self.assertEqual(r.habilitadas_declarativamente, ("independiente", "comparar"))
        self.assertIn(("qa-previo", 1, 1), r.consumos_qa_aportados)
        self.assertEqual(r.cuotas_qa_declaradas, (4, 8))
        self.assertFalse(r.ejecucion_realizada)
        self.assertIs(self.qa.cierre_qa.informe.estado, EstadoEvaluacionQA.COMPLETA)

    def test_qa_planificada_admitida_no_se_ejecuta_ni_se_confunde_con_cierre(self):
        o = replace(self.qa.contexto, estado=S.PLANIFICADA, referencias_resultado=())
        n = replace(self.qa, contexto=o, cierre_qa=None)
        r = inspeccionar_composicion(composicion((n,)))
        self.assertEqual(r.habilitadas_declarativamente, ("qa-previo",))
        self.assertFalse(r.operaciones[0].cierre_qa_coherente_completo)
        self.assertFalse(r.ejecucion_realizada)

    def test_perfil_entrada_qa_desconocido_queda_pendiente(self):
        e = replace(self.qa.contexto.entradas[0], perfil_estructural=None)
        o = replace(self.qa.contexto, entradas=(e,), estado=S.PLANIFICADA, referencias_resultado=())
        r = inspeccionar_composicion(composicion((replace(self.qa, contexto=o, cierre_qa=None),)))
        self.assertIs(r.estado_estructural, E.PENDIENTE_DE_EVIDENCIA)
        self.assertIn("perfil_entrada_qa_desconocido", codigos(r))

    def test_restricciones_qa_llegan_a_operacion_dependiente(self):
        r = inspeccionar_composicion(piloto(self.qa))
        rp = por_id(r, "comparar").restricciones
        self.assertIn("sin_validacion_cientifica", [p.restriccion.codigo for p in rp])
        p = next(p for p in rp if p.restriccion.codigo == "sin_validacion_cientifica")
        self.assertTrue(any(x.startswith("vinculo_qa:qa-previo:") for x in p.origenes))
        self.assertFalse(r.autoriza_operacion)

    def test_uso_cientifico_bloqueado_por_restriccion_qa_heredada(self):
        c = piloto(self.qa)
        ns = tuple(replace(n, usos_declarados=(*n.usos_declarados, "acreditar_aptitud_cientifica"))
                   if n.contexto.operacion_id == "comparar" else n for n in c.operaciones)
        r = inspeccionar_composicion(replace(c, operaciones=ns))
        self.assertIs(por_id(r, "comparar").estado_estructural, E.INCOMPATIBLE)

    def test_piloto_incompatible_y_pendiente_preserva_independiente(self):
        for kwargs, esperado in ((dict(incompatible=True), E.INCOMPATIBLE), (dict(pendiente=True), E.PENDIENTE_DE_EVIDENCIA)):
            with self.subTest(kwargs=kwargs):
                r = inspeccionar_composicion(piloto(self.qa, **kwargs))
                self.assertIs(por_id(r, "comparar").estado_estructural, esperado)
                self.assertEqual(r.habilitadas_declarativamente, ("independiente",))

    def test_conteos_informe_y_resultados_contradictorios_no_satisfacen_cierre(self):
        cierre = replace(self.qa.cierre_qa, informe=replace(self.qa.cierre_qa.informe, resultados_emitidos=2))
        r = inspeccionar_composicion(piloto(replace(self.qa, cierre_qa=cierre)))
        self.assertIn("informe_y_resultados_qa_contradictorios", codigos(r))
        self.assertFalse(por_id(r, "qa-previo").cierre_qa_coherente_completo)
        self.assertNotIn("comparar", r.habilitadas_declarativamente)

    def test_estado_completo_con_eof_o_recorrido_inconsistente_rechazado(self):
        for cambio in (dict(recorrido_completo=False), dict(motivo_fin="interrumpido")):
            with self.subTest(cambio=cambio):
                cierre = replace(self.qa.cierre_qa, informe=replace(self.qa.cierre_qa.informe, **cambio))
                r = inspeccionar_composicion(composicion((replace(self.qa, cierre_qa=cierre),)))
                self.assertIn("informe_qa_completo_con_condiciones_contradictorias", codigos(r))

    def test_vinculo_de_otra_operacion_no_se_reutiliza_como_exito(self):
        otro = replace(self.qa.contexto, operacion_id="otra-qa")
        r = inspeccionar_composicion(composicion((replace(self.qa, contexto=otro),)))
        self.assertIn("vinculo_qa_de_otra_operacion_o_instantanea", codigos(r))

    def test_presupuesto_compuesto_suma_cuotas_comparables_por_operacion(self):
        otra = replace(self.qa.contexto, operacion_id="otra-qa", estado=S.PLANIFICADA, referencias_resultado=())
        n = NodoOperacion(otra, ("evaluar_estructura_qa0",))
        for limites, codigo in ((LimitesComposicion(max_registros_qa_declarados=7), "cuota_compuesta_registros_qa_excedida"),
                (LimitesComposicion(max_resultados_qa_declarados=15), "cuota_compuesta_resultados_qa_excedida")):
            with self.subTest(codigo=codigo):
                r = inspeccionar_composicion(composicion((self.qa, n), limites=limites))
                self.assertEqual(r.cuotas_qa_declaradas, (8, 16))
                self.assertIn(codigo, codigos(r))
                self.assertFalse(r.recursos_reservados)

    def test_cierre_parcial_real_conserva_referencias_y_no_habilita_dependiente(self):
        qa = qa_real(parcial=True)
        r = inspeccionar_composicion(piloto(qa))
        self.assertIs(qa.contexto.estado, S.PARCIAL)
        self.assertFalse(por_id(r, "qa-previo").cierre_qa_coherente_completo)
        self.assertNotIn("comparar", r.habilitadas_declarativamente)
        self.assertTrue(qa.contexto.referencias_resultado)
        self.assertEqual(r.consumos_qa_aportados, (("qa-previo", 1, 1),))

    def test_conclusion_contextual_no_encubre_informe_qa_incompleto(self):
        qa = qa_real(parcial=True)
        o = replace(qa.contexto, estado=S.CONCLUIDA, diagnosticos=())
        vs = tuple(VinculoResultadoQA(o, v.entrada_id, v.referencia_resultado, v.resultado) for v in qa.cierre_qa.vinculos)
        qa = replace(qa, contexto=o, cierre_qa=replace(qa.cierre_qa, vinculos=vs))
        r = inspeccionar_composicion(piloto(qa))
        self.assertIn("operacion_concluida_con_qa_incompleta", codigos(r))
        self.assertNotIn("comparar", r.habilitadas_declarativamente)

    def test_cancelacion_inspeccion_conserva_cierre_y_resultados_previos(self):
        evento = Event(); evento.set()
        r = inspeccionar_composicion(piloto(self.qa), cancelacion=evento)
        self.assertTrue(r.cancelada)
        self.assertIs(por_id(r, "qa-previo").nodo.cierre_qa, self.qa.cierre_qa)
        self.assertEqual(por_id(r, "qa-previo").nodo.contexto.referencias_resultado,
                         self.qa.contexto.referencias_resultado)

    def test_dos_proyectos_con_mismo_contenido_se_mantienen_aislados(self):
        a = self.qa.contexto.entradas[0]
        p = proyecto_qa("proyecto-B", "contexto-B")
        e = entrada_qa(p, sha256_declarado=a.sha256_declarado)
        b = nodo("independiente-B", entrada=e)
        ca, cb = piloto(self.qa), composicion((b,))
        ra, rb = inspeccionar_composicion(ca), inspeccionar_composicion(cb)
        self.assertNotEqual(ra.composicion.proyecto.project_id, rb.composicion.proyecto.project_id)
        self.assertEqual(a.sha256_declarado, e.sha256_declarado)
        mezclada = inspeccionar_composicion(replace(ca, operaciones=(*ca.operaciones, b)))
        self.assertIn("contexto_proyecto_ausente_o_incompatible", codigos(mezclada))
        self.assertEqual(mezclada.habilitadas_declarativamente, ())

    def test_cierre_de_otro_proyecto_no_se_acepta(self):
        e = entrada_qa(proyecto_qa("proyecto-B", "contexto-B"))
        o = replace(self.qa.contexto, proyecto=e.proyecto, entradas=(e,))
        r = inspeccionar_composicion(composicion((replace(self.qa, contexto=o),)))
        self.assertIn("vinculo_qa_de_otra_operacion_o_instantanea", codigos(r))

    def test_resultados_y_json_qa_nativos_no_se_modifican(self):
        from spica.calidad.exportacion import exportar_resultado_json
        v = self.qa.cierre_qa.vinculos[0]
        antes = exportar_resultado_json(v.resultado, v.contexto_exportacion)
        inspeccionar_composicion(piloto(self.qa))
        self.assertEqual(exportar_resultado_json(v.resultado, v.contexto_exportacion), antes)
        self.assertEqual(dict(v.resultado.registro.campos_originales)["HORA"], "10000")
        self.assertEqual(dict(v.resultado.registro.campos_originales)["UBIGEO"], "01234.0")


class SeguridadYCancelacionRC3Tests(unittest.TestCase):
    def test_determinismo_y_objetos_originales_sin_mutacion(self):
        c = composicion((con_perfiles(),))
        r = inspeccionar_composicion(c)
        self.assertEqual(r, inspeccionar_composicion(c))
        self.assertIs(c.operaciones[0].contexto.estado, S.DECLARADA)
        with self.assertRaises(FrozenInstanceError):
            r.cancelada = True

    def test_cancelacion_previa_no_ejecuta_comprobacion_rc2(self):
        evento = Event(); evento.set()
        with patch('spica.coordinacion.inspeccion.comparar_perfiles', side_effect=AssertionError('no_comparar')):
            r = inspeccionar_composicion(composicion((con_perfiles(),)), cancelacion=evento)
        self.assertTrue(r.cancelada)
        self.assertEqual(r.habilitadas_declarativamente, ())
        self.assertIs(r.estado_estructural, E.PENDIENTE_DE_EVIDENCIA)

    def test_cancelacion_durante_cotejo_conserva_resultado_rc2_ya_obtenido(self):
        evento = Event()
        from spica.interoperabilidad.perfiles import comparar_perfiles
        def comparar(*args, **kwargs):
            r = comparar_perfiles(*args, **kwargs)
            evento.set()
            return r
        with patch('spica.coordinacion.inspeccion.comparar_perfiles', side_effect=comparar):
            r = inspeccionar_composicion(composicion((con_perfiles(),)), cancelacion=evento)
        self.assertTrue(r.cancelada)
        self.assertEqual(len(r.operaciones[0].compatibilidades), 1)
        self.assertEqual(r.habilitadas_declarativamente, ())
        self.assertIs(r.operaciones[0].nodo.contexto.estado, S.DECLARADA)

    def test_cancelacion_no_admite_callbacks_o_booleanos(self):
        for cancelacion in (True, lambda: True):
            with self.subTest(cancelacion=cancelacion), self.assertRaises(TypeError):
                inspeccionar_composicion(composicion(), cancelacion=cancelacion)

    def test_inspeccion_no_llama_motor_qa_planificador_o_transporte(self):
        c = composicion((con_perfiles(),))
        with patch('spica.calidad.motor.EvaluadorNivel0.__enter__', side_effect=AssertionError('qa_automatico')), \
             patch('spica.adquisicion.planificacion.planificador.Planificador.planificar', side_effect=AssertionError('planificador_automatico')), \
             patch('spica.adquisicion.transportes.http.ClienteHTTP.get', side_effect=AssertionError('red')):
            self.assertIs(inspeccionar_composicion(c).estado_estructural, E.APTO_ESTRUCTURALMENTE)

    def test_importacion_e_inspeccion_sin_red_sqlite_o_escrituras(self):
        codigo = r'''
import os, sys
def denegar(evento, args):
    if evento.startswith('socket.') or evento in ('sqlite3.connect', 'os.mkdir', 'os.remove', 'os.rename'):
        raise AssertionError('efecto_no_permitido_rc3')
    if evento == 'open':
        modo, flags = args[1:3]
        if (isinstance(modo, str) and any(c in modo for c in 'wax+')) or (
                isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC)):
            raise AssertionError('escritura_no_permitida_rc3')
        if 'spica_datos' in str(args[0]).lower():
            raise AssertionError('lectura_operativa_no_permitida_rc3')
sys.addaudithook(denegar)
sys.path[:0] = ['src', 'tests']
IMPORTACION
from test_coordinacion_rc3 import con_perfiles, composicion, inspeccionar_composicion
r = inspeccionar_composicion(composicion((con_perfiles(),)))
assert r.habilitadas_declarativamente == ('comparar',)
assert not r.autoriza_operacion and not r.ejecucion_realizada
print('RC3_sin_efectos')
'''
        for previa in ("import spica.coordinacion", "import spica.contextos; import spica.interoperabilidad.perfiles"):
            with self.subTest(orden=previa):
                r = subprocess.run([sys.executable, "-B", "-c", codigo.replace("IMPORTACION", previa)],
                    cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, timeout=30)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertEqual(r.stdout.strip(), "RC3_sin_efectos")


if __name__ == "__main__":
    unittest.main()
