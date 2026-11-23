"""RC14: recorridos compartidos, evidencia nativa y TEMP sintético propio."""

from contextlib import contextmanager
from dataclasses import FrozenInstanceError, replace
import hashlib
import inspect
import os
from pathlib import Path
import subprocess
import sys
from threading import Event
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from spica.adquisicion.readquisicion.modelos import EstadoLocal
from spica.artefactos.admision_exportacion import admitir_exportacion_tecnica, USO_CONSUMIR
from spica.artefactos.cierre_exportacion import ejecutar_exportacion_tecnica
from spica.artefactos.conservacion import UnidadConservacion, entorno_conservacion, recuperar_generacion
from spica.artefactos.coordinacion import SolicitudIntegracion, VinculoEntradaRecuperada, inspeccionar_integracion
from spica.artefactos.coordinacion_precondicion import (
    SeleccionPrecondicionRC14 as Seleccion, inspeccionar_composicion_rc14 as coordinar,
    inspeccionar_integracion_rc14 as integrar,
)
from spica.artefactos.dependencia_exportacion import DecisionDependencia as DD, SolicitudDependenciaExportacion as S11
from spica.artefactos.materializacion import SolicitudMaterializacion, entorno_materializacion
from spica.artefactos.precondicion_productora import (
    PoliticaPrecondicionProductora as P13, SolicitudPrecondicionProductora as S13,
    examinar_precondicion_productora,
)
from spica.calidad.exportacion import exportar_resultado_json
from spica.calidad.consumo import consumir_exportaciones
from spica.calidad.restricciones import RestriccionQA, TipoRestriccionQA as TR
from spica.contextos import ContextoOperacion, TipoOperacion as TO, EstadoOperacion as S
from spica.coordinacion import NodoOperacion, DependenciaOperacion as Dep, inspeccionar_composicion, LimitesComposicion
from spica.interoperabilidad.adaptadores import DiagnosticoAdaptacion as D, NivelDiagnostico as N
from spica.interoperabilidad.modelos import EstadoAptitud as E
from spica.interoperabilidad.perfiles import FinalidadCompatibilidad, AspectoCampo
from spica.coordinacion import RequisitoCompatibilidad
# Solo fabricantes: nunca TestCase importados que dupliquen descubrimiento.
from test_dependencia_noqa_rc11 import solicitud_exportacion, politica, historico
from test_admision_exportacion_rc9 import solicitud as s9, materializar
from test_coordinacion_rc3 import qa_real, con_perfiles, composicion as comp_qa
from test_perfiles_informacion_rc2 import declarado


def solicitud_piloto(*, segunda=None, **kw):
    s = solicitud_exportacion(**kw)
    inv = s.inventario
    a, b = inv.artefactos
    # La representación física fuente será JSON QA nativo del ResultadoQA previo.
    # Es una raíz lógica sintética, nunca un activo RAW institucional.
    a = replace(a, formato="application/json")
    c = inv.composiciones[0]
    op = ContextoOperacion("independiente", c.proyecto, (a.entrada_perfil.entrada,),
        TO.DESCRIPCION_ESTRUCTURAL, "Inspeccionar fixture independiente sin ejecutarla")
    if segunda == "fallida":
        op = replace(op, estado=S.FALLIDA, diagnosticos=(D("fallo_independiente_fixture", "fixture", N.FALTANTE),))
    independiente = NodoOperacion(op, ("inspeccionar_fixture_rc14",))
    ds = c.dependencias + (() if segunda is None else (Dep("independiente", "consumidor"),))
    c = replace(c, operaciones=(*c.operaciones, independiente), dependencias=ds)
    return replace(s, inventario=replace(inv, artefactos=(a, b), composiciones=(c,)))


def nativos14(**kw):
    e = ejecutar_exportacion_tecnica(solicitud_piloto(**kw))
    a = admitir_exportacion_tecnica(s9(e))
    return e, a


def seleccion(e, a, **kw):
    p = politica(e, **kw)
    return Seleccion(S13(S11(p, e, a), P13(p, p.dependencia.referencias_resultado[0])))


@contextmanager
def recuperacion(e, *, externo_qa=False, externo_json=False):
    inv = e.solicitud.inventario
    # Representación fuente real mediante el codificador nativo del QA previo;
    # no se afirma que RC8 haya leído este archivo durante su ejecución.
    v = e.solicitud.entrada_qa
    fuente = exportar_resultado_json(v.resultado, v.contexto_exportacion).encode("utf-8")
    salida = e.resultado_nativo.encode("utf-8")
    with entorno_materializacion() as m, entorno_conservacion() as c:
        mats, externos = [], []
        for descriptor, cuerpo, externo in zip(inv.artefactos, (fuente, salida), (externo_qa, externo_json)):
            if externo:
                externos.append(descriptor.referencia)
            else:
                mats.append(m.materializar_sintetico(SolicitudMaterializacion(inv, descriptor.referencia,
                    len(cuerpo), hashlib.sha256(cuerpo).hexdigest()), (cuerpo[:37], cuerpo[37:])))
        guardado = c.conservar(UnidadConservacion(inv, tuple(mats), tuple(externos)))
        r = recuperar_generacion(c.raiz, guardado.control)
        comp = r.unidad.inventario.composiciones[0]
        refs = {a.entrada_perfil.entrada.entrada_id: a.referencia for a in inv.artefactos}
        vs = tuple(VinculoEntradaRecuperada(n.contexto.operacion_id, en.entrada_id, refs[en.entrada_id])
            for n in comp.operaciones for en in n.contexto.entradas)
        yield SolicitudIntegracion(r, comp, vs, USO_CONSUMIR), m, c


def codigos(r):
    return {d.codigo for d in r.diagnosticos}


class CoordinacionPrecondicionRC14Tests(unittest.TestCase):
    def setUp(self):
        self.e, self.a = nativos14()
        self.sel = seleccion(self.e, self.a)
        self.c = self.e.solicitud.inventario.composiciones[0]

    def examinar(self, **kw):
        valores = dict(seleccion=self.sel)
        valores.update(kw)
        return coordinar(self.c, **valores)

    def test_rc3_sin_seleccion_es_identico_al_predeterminado(self):
        base = inspeccionar_composicion(self.c)
        r = self.examinar(seleccion=None)
        self.assertEqual(r.predeterminado, base)
        self.assertIs(r.opcional, r.predeterminado)
        self.assertEqual(r.habilitadas_declarativamente, base.habilitadas_declarativamente)
        self.assertFalse(r.arista_admitida_por_rc14)
        self.assertNotIn("consumidor", r.habilitadas_declarativamente)
        self.assertIn("independiente", r.habilitadas_declarativamente)

    def test_rc3_seleccion_expresa_resuelve_solo_arista_prevista(self):
        r = self.examinar()
        self.assertIs(r.decision_precondicion, DD.SATISFECHA)
        self.assertTrue(r.arista_admitida_por_rc14)
        self.assertEqual(set(r.habilitadas_declarativamente), {"consumidor", "independiente"})
        self.assertEqual(r.predeterminado, inspeccionar_composicion(self.c))
        self.assertIs(r.precondicion.dictamen_rc11.decision, DD.NO_ADMISIBLE)
        self.assertEqual(r.dependencias, ((self.c.dependencias[0], E.APTO_ESTRUCTURALMENTE),))
        self.assertIs(r.opcional.estado_estructural, E.PENDIENTE_DE_EVIDENCIA)
        for i in r.opcional.operaciones:
            self.assertFalse(i.cierre_qa_coherente_completo)
        self.assertEqual(r.opcional.consumos_qa_aportados, ())
        self.assertIs(self.c.operaciones[0].contexto.estado, S.INICIADA)
        self.assertIs(self.c.operaciones[1].contexto.estado, S.DECLARADA)

    def test_rc7_sin_seleccion_conserva_informe_y_limpieza(self):
        with recuperacion(self.e) as (s, m, c):
            r = integrar(s)
            self.assertEqual(r.predeterminado, inspeccionar_integracion(s))
            self.assertIs(r.opcional, r.predeterminado)
            self.assertNotIn("consumidor", r.habilitadas_declarativamente)
            self.assertIn("independiente", r.habilitadas_declarativamente)
        self.assertFalse(m.raiz.exists())
        self.assertFalse(c.raiz.exists())

    def test_rc7_seleccion_y_todos_los_bytes_incluidos_habilitan_consumidor(self):
        with recuperacion(self.e) as (s, m, c):
            r = integrar(s, seleccion=self.sel)
            self.assertIs(r.decision_precondicion, DD.SATISFECHA, r.diagnosticos)
            self.assertTrue(r.arista_admitida_por_rc14)
            self.assertEqual(set(r.habilitadas_declarativamente), {"consumidor", "independiente"})
            self.assertEqual(r.predeterminado, inspeccionar_integracion(s))
            self.assertEqual(r.opcional.dependencias, ((self.c.dependencias[0], E.APTO_ESTRUCTURALMENTE),))
            self.assertTrue(all(x.estado_actual is EstadoLocal.INTEGRO for x in s.recuperacion.contenidos))
            self.assertIs(s.recuperacion.unidad.inventario.composiciones[0].operaciones[0].contexto.estado, S.INICIADA)
            self.assertTrue(all(not x.cierre_qa_coherente_completo for x in r.opcional.coordinacion_integrada.operaciones))
        self.assertFalse(m.raiz.exists())
        self.assertFalse(c.raiz.exists())

    def test_segunda_dependencia_pendiente_bloquea_consumidor_en_rc3_y_rc7(self):
        e, a = nativos14(segunda="pendiente")
        sel = seleccion(e, a)
        c3 = e.solicitud.inventario.composiciones[0]
        r3 = coordinar(c3, seleccion=sel)
        self.assertTrue(r3.arista_admitida_por_rc14)
        self.assertNotIn("consumidor", r3.habilitadas_declarativamente)
        self.assertEqual(dict(r3.dependencias)[c3.dependencias[1]], E.PENDIENTE_DE_EVIDENCIA)
        with recuperacion(e) as (s7, m, c):
            r7 = integrar(s7, seleccion=sel)
            self.assertTrue(r7.arista_admitida_por_rc14)
            self.assertNotIn("consumidor", r7.habilitadas_declarativamente)
            self.assertEqual(dict(r7.dependencias)[c3.dependencias[1]], E.PENDIENTE_DE_EVIDENCIA)
        self.assertFalse(m.raiz.exists())
        self.assertFalse(c.raiz.exists())

    def test_segunda_dependencia_fallida_no_se_promueve(self):
        e, a = nativos14(segunda="fallida")
        c = e.solicitud.inventario.composiciones[0]
        r = coordinar(c, seleccion=seleccion(e, a))
        self.assertNotIn("consumidor", r.habilitadas_declarativamente)
        self.assertIsNot(r.decision_precondicion, DD.SATISFECHA)
        self.assertIs(c.operaciones[2].contexto.estado, S.FALLIDA)

    def test_cierre_qa_genuino_no_cambia(self):
        qa = qa_real()
        c = comp_qa((qa,))
        r = coordinar(c)
        self.assertEqual(r.opcional, inspeccionar_composicion(c))
        self.assertTrue(r.opcional.operaciones[0].cierre_qa_coherente_completo)

    def test_firmas_publicas_anteriores_conservadas(self):
        self.assertEqual(tuple(inspect.signature(inspeccionar_composicion).parameters), ("composicion", "cancelacion"))
        self.assertEqual(tuple(inspect.signature(inspeccionar_integracion).parameters), ("solicitud", "cancelacion"))
        self.assertEqual(inspect.signature(inspeccionar_integracion).parameters["cancelacion"].default, None)
        self.assertEqual(inspect.signature(inspeccionar_composicion).parameters["cancelacion"].kind, inspect.Parameter.KEYWORD_ONLY)

    def test_politica_rc14_desconocida_o_version_incompatible_no_admite(self):
        for kw in (dict(perfil="desconocida"), dict(version_contrato="9.0.0")):
            with self.subTest(kw=kw):
                r = self.examinar(seleccion=replace(self.sel, **kw))
                self.assertIs(r.decision_precondicion, DD.NO_ADMISIBLE)
                self.assertFalse(r.arista_admitida_por_rc14)
                self.assertNotIn("consumidor", r.habilitadas_declarativamente)

    def test_copiar_informe_no_recrea_contraste(self):
        r = self.examinar()
        copia = replace(r, diagnosticos=())
        self.assertIs(copia.decision_precondicion, DD.PENDIENTE)
        self.assertEqual(copia.habilitadas_declarativamente, ())
        self.assertFalse(copia.arista_admitida_por_rc14)
        with self.assertRaises(FrozenInstanceError):
            r.diagnosticos = ()

    def test_productor_y_consumidor_nativos_realmente_invocados(self):
        with patch("spica.artefactos.cierre_exportacion.exportar_resultado_json", wraps=exportar_resultado_json) as p:
            e = ejecutar_exportacion_tecnica(solicitud_piloto())
        with patch("spica.artefactos.admision_exportacion.consumir_exportaciones", wraps=consumir_exportaciones) as c:
            a = admitir_exportacion_tecnica(s9(e))
        p.assert_called_once()
        c.assert_called_once()
        r = coordinar(e.solicitud.inventario.composiciones[0], seleccion=seleccion(e, a))
        self.assertTrue(r.arista_admitida_por_rc14)

    def test_productor_incompatible_no_admitido(self):
        e, a = nativos14(metodo="otro.productor")
        r = coordinar(e.solicitud.inventario.composiciones[0], seleccion=seleccion(e, a))
        self.assertFalse(e.productor_invocado)
        self.assertFalse(r.arista_admitida_por_rc14)
        self.assertNotIn("consumidor", r.habilitadas_declarativamente)

    def test_consumidor_incompatible_no_admitido(self):
        a = admitir_exportacion_tecnica(s9(self.e, consumidor_id="otro.consumidor"))
        r = self.examinar(seleccion=seleccion(self.e, a))
        self.assertIs(r.decision_precondicion, DD.NO_SATISFECHA)
        self.assertNotIn("consumidor", r.habilitadas_declarativamente)

    def test_proyectos_con_bytes_identicos_no_comparten_habilitaciones(self):
        e, a = nativos14(project_id="proyecto-RC14-B")
        self.assertEqual(e.resultado_nativo, self.e.resultado_nativo)
        sel = seleccion(e, a)
        propia = coordinar(e.solicitud.inventario.composiciones[0], seleccion=sel)
        self.assertTrue(propia.arista_admitida_por_rc14)
        ajena = self.examinar(seleccion=sel)
        self.assertFalse(ajena.arista_admitida_por_rc14)
        self.assertNotIn("consumidor", ajena.habilitadas_declarativamente)
        self.assertIn("composicion_o_proyecto_ajenos_a_precondicion", codigos(ajena))
        self.assertIs(ajena.estado_estructural, E.INCOMPATIBLE)

    def test_otra_composicion_no_reutiliza_evidencia(self):
        c = replace(self.c, identificador="otra-composicion")
        r = coordinar(c, seleccion=self.sel)
        self.assertFalse(r.arista_admitida_por_rc14)
        self.assertIn("composicion_o_proyecto_ajenos_a_precondicion", codigos(r))

    def test_operacion_o_arista_incorrectas_no_admitidas(self):
        s = self.sel.precondicion
        for d in (Dep("otra-productora", "consumidor", ("salida-exportacion",)),
                  Dep("exportar", "otra-dependiente", ("salida-exportacion",))):
            with self.subTest(d=d):
                p = replace(s.dependencia.politica, dependencia=d)
                sel = Seleccion(S13(replace(s.dependencia, politica=p), P13(p, "salida-exportacion")))
                r = self.examinar(seleccion=sel)
                self.assertFalse(r.arista_admitida_por_rc14)
                self.assertNotIn("consumidor", r.habilitadas_declarativamente)

    def test_otra_arista_de_la_misma_productora_no_se_admite(self):
        s = solicitud_piloto()
        c = s.inventario.composiciones[0]
        c = replace(c, dependencias=(*c.dependencias, Dep("exportar", "independiente", ("salida-exportacion",))))
        s = replace(s, inventario=replace(s.inventario, composiciones=(c,)))
        e = ejecutar_exportacion_tecnica(s)
        a = admitir_exportacion_tecnica(s9(e))
        r = coordinar(c, seleccion=seleccion(e, a))
        self.assertTrue(r.arista_admitida_por_rc14)
        self.assertIn("consumidor", r.habilitadas_declarativamente)
        self.assertNotIn("independiente", r.habilitadas_declarativamente)
        self.assertEqual(dict(r.dependencias)[c.dependencias[1]], E.PENDIENTE_DE_EVIDENCIA)

    def test_version_nativa_incompatible_no_admitida(self):
        s = self.sel.precondicion
        e = replace(self.e, version_productor="9.0.0")
        sel = replace(self.sel, precondicion=replace(s, dependencia=replace(s.dependencia, evidencia=e, admision=None)))
        r = self.examinar(seleccion=sel)
        self.assertIs(r.decision_precondicion, DD.NO_SATISFECHA)
        self.assertFalse(r.arista_admitida_por_rc14)

    def test_entrada_resultado_revision_y_contenido_incompatibles(self):
        s = self.sel.precondicion
        for kw in (dict(entrada_resultado_id="otro-resultado"), dict(contenido_id="otro-contenido"),
                dict(artefacto=replace(s.dependencia.politica.artefacto, revision="r2"))):
            with self.subTest(kw=kw):
                p = replace(s.dependencia.politica, **kw)
                sel = Seleccion(S13(replace(s.dependencia, politica=p), P13(p, "salida-exportacion")))
                r = self.examinar(seleccion=sel)
                self.assertFalse(r.arista_admitida_por_rc14)
                self.assertNotIn("consumidor", r.habilitadas_declarativamente)

    def test_diagnostico_propio_no_se_oculta_como_limite_del_inspector(self):
        s = solicitud_piloto()
        inv = s.inventario
        c = inv.composiciones[0]
        p, n, i = c.operaciones
        causa = D("estado_declarado_no_es_cierre_completo", "exportar", N.FALTANTE)
        op = replace(p.contexto, diagnosticos=(causa,))
        c = replace(c, operaciones=(replace(p, contexto=op), n, i))
        inv = replace(inv, composiciones=(c,), producciones=(replace(inv.producciones[0], operacion=op),))
        e = ejecutar_exportacion_tecnica(replace(s, inventario=inv))
        a = admitir_exportacion_tecnica(s9(e))
        r = coordinar(c, seleccion=seleccion(e, a))
        self.assertIs(r.decision_precondicion, DD.SATISFECHA)
        self.assertFalse(r.arista_admitida_por_rc14)
        self.assertNotIn("consumidor", r.habilitadas_declarativamente)
        self.assertIn(causa, r.opcional.operaciones[0].nodo.contexto.diagnosticos)

    def test_consumidor_terminal_no_recibe_habilitacion(self):
        for estado in (S.INICIADA, S.PARCIAL, S.FALLIDA, S.CANCELADA, S.CONCLUIDA):
            with self.subTest(estado=estado):
                s = solicitud_piloto()
                c = s.inventario.composiciones[0]
                p, n, i = c.operaciones
                ds = (D("estado_consumidor_fixture", "fixture", N.FALTANTE),) if estado in (S.PARCIAL, S.FALLIDA, S.CANCELADA) else ()
                refs = ("resultado_declarado_no_comprobado",) if estado in (S.PARCIAL, S.CONCLUIDA) else ()
                n = replace(n, contexto=replace(n.contexto, estado=estado, diagnosticos=ds, referencias_resultado=refs))
                c = replace(c, operaciones=(p, n, i))
                e = ejecutar_exportacion_tecnica(replace(s, inventario=replace(s.inventario, composiciones=(c,))))
                r = coordinar(c, seleccion=seleccion(e, admitir_exportacion_tecnica(s9(e))))
                self.assertNotIn("consumidor", r.habilitadas_declarativamente)
                self.assertIs(n.contexto.estado, estado)

    def test_rc8_o_rc9_ausentes_no_se_compensan(self):
        s = self.sel.precondicion
        for kw in (dict(evidencia=None, admision=None), dict(admision=None)):
            with self.subTest(kw=kw):
                sel = replace(self.sel, precondicion=replace(s, dependencia=replace(s.dependencia, **kw)))
                r = self.examinar(seleccion=sel)
                self.assertIs(r.decision_precondicion, DD.PENDIENTE)
                self.assertFalse(r.arista_admitida_por_rc14)
                self.assertNotIn("consumidor", r.habilitadas_declarativamente)

    def test_testigos_locales_ausentes_no_se_compensan(self):
        s = self.sel.precondicion
        for kw in (dict(evidencia=replace(self.e), admision=None), dict(admision=replace(self.a))):
            with self.subTest(kw=kw):
                sel = replace(self.sel, precondicion=replace(s, dependencia=replace(s.dependencia, **kw)))
                self.assertIs(self.examinar(seleccion=sel).decision_precondicion, DD.PENDIENTE)

    def test_dictamen_favorable_aportado_no_es_entrada_admisible(self):
        previo = examinar_precondicion_productora(self.sel.precondicion)
        self.assertIs(previo.decision, DD.SATISFECHA)
        with self.assertRaises(TypeError):
            Seleccion(previo)
        with self.assertRaises(TypeError):
            self.examinar(seleccion=previo)
        copia = replace(previo, diagnosticos=())
        with patch("spica.artefactos.coordinacion_precondicion.examinar_precondicion_productora", return_value=copia):
            r = self.examinar()
        self.assertFalse(r.arista_admitida_por_rc14)
        self.assertIn("dictamen_rc13_sin_cotejo_local", codigos(r))

    def test_politica_rc13_desconocida_no_es_habilitada_por_rc14(self):
        s = self.sel.precondicion
        sel = replace(self.sel, precondicion=replace(s, politica=replace(s.politica, perfil="desconocida")))
        r = self.examinar(seleccion=sel)
        self.assertIs(r.decision_precondicion, DD.NO_ADMISIBLE)
        self.assertNotIn("consumidor", r.habilitadas_declarativamente)

    def test_restriccion_bloqueante_se_conserva_y_no_habilita(self):
        bloqueo = RestriccionQA("bloqueo-rc14", TR.BLOQUEO_USO_DEL_RESULTADO,
            (USO_CONSUMIR,), "Fixture: consumo bloqueado")
        sel = seleccion(self.e, self.a, restricciones_adicionales=(bloqueo,))
        r = self.examinar(seleccion=sel)
        self.assertIs(r.decision_precondicion, DD.NO_SATISFECHA)
        self.assertFalse(r.arista_admitida_por_rc14)
        self.assertNotIn("consumidor", r.habilitadas_declarativamente)
        self.assertTrue(any(x.restriccion == bloqueo and x.origenes for x in r.restricciones))

    def test_restricciones_admitidas_se_propagan_a_descendientes(self):
        s = solicitud_piloto()
        inv = s.inventario
        c = inv.composiciones[0]
        entrada = inv.artefactos[1].entrada_perfil.entrada
        d = NodoOperacion(ContextoOperacion("descendiente", c.proyecto, (entrada,), TO.DESCRIPCION_ESTRUCTURAL,
            "Describir fixture sin ejecutarla"), ("uso_bloqueado_fixture",))
        c = replace(c, operaciones=(*c.operaciones, d), dependencias=(*c.dependencias, Dep("consumidor", "descendiente")))
        s = replace(s, inventario=replace(inv, composiciones=(c,)))
        e = ejecutar_exportacion_tecnica(s)
        a = admitir_exportacion_tecnica(s9(e))
        bloqueo = RestriccionQA("conservada-rc14", TR.BLOQUEO_USO_DEL_RESULTADO,
            ("uso_bloqueado_fixture",), "Fixture: no eliminar restriccion")
        r = coordinar(c, seleccion=seleccion(e, a, restricciones_adicionales=(bloqueo,)))
        self.assertTrue(r.arista_admitida_por_rc14)
        consumidor = next(x for x in r.opcional.operaciones if x.nodo.contexto.operacion_id == "consumidor")
        descendiente = next(x for x in r.opcional.operaciones if x.nodo.contexto.operacion_id == "descendiente")
        for informe in (consumidor, descendiente):
            self.assertTrue(any(x.restriccion == bloqueo and x.origenes for x in informe.restricciones))
        self.assertNotIn("descendiente", r.habilitadas_declarativamente)
        self.assertTrue(any(x.codigo == "restriccion_bloqueante_para_uso_declarado" for x in descendiente.diagnosticos))

    def test_rc2_incompatible_no_se_omite(self):
        s = solicitud_piloto()
        inv = s.inventario
        a, b = inv.artefactos
        ep1, ep2 = a.entrada_perfil, b.entrada_perfil
        campos = ep2.perfil.campos
        ep2 = replace(ep2, perfil=replace(ep2.perfil, campos=(replace(campos[0], tipo=declarado("numero-incompatible")), *campos[1:])))
        b = replace(b, entrada_perfil=ep2)
        f = FinalidadCompatibilidad("comparar_fixture_rc14", "Cotejar tipos ficticios incompatibles",
            ((ep1.perfil.campos[0].nombre, ep2.perfil.campos[0].nombre),),
            ((ep1.perfil.identificador, ep1.perfil.version), (ep2.perfil.identificador, ep2.perfil.version)),
            (AspectoCampo.TIPO,))
        c = inv.composiciones[0]
        p, n, i = c.operaciones
        n = replace(n, contexto=replace(n.contexto, entradas=(ep1.entrada, ep2.entrada), proposito=f.descripcion),
            usos_declarados=(USO_CONSUMIR, f.identificador), compatibilidades=(RequisitoCompatibilidad(ep1, ep2, f),))
        c = replace(c, operaciones=(p, n, i))
        s = replace(s, inventario=replace(inv, artefactos=(a, b), composiciones=(c,)))
        e = ejecutar_exportacion_tecnica(s)
        r = coordinar(c, seleccion=seleccion(e, admitir_exportacion_tecnica(s9(e))))
        self.assertFalse(r.arista_admitida_por_rc14)
        self.assertNotIn("consumidor", r.habilitadas_declarativamente)
        consumidor = next(x for x in r.opcional.operaciones if x.nodo.contexto.operacion_id == "consumidor")
        self.assertIs(consumidor.compatibilidades[0].estado, E.INCOMPATIBLE)

    def test_parcial_fallida_y_cancelada_observadas_no_se_promueven(self):
        for caso in ("parcial", "fallida", "cancelada"):
            with self.subTest(caso=caso):
                evento = Event()
                if caso == "parcial":
                    def parcial(*args, **kw):
                        texto = exportar_resultado_json(*args, **kw)
                        evento.set()
                        return texto
                    with patch("spica.artefactos.cierre_exportacion.exportar_resultado_json", side_effect=parcial):
                        e = ejecutar_exportacion_tecnica(solicitud_piloto(), cancelacion=evento)
                    self.assertIs(e.operacion_observada.estado, S.PARCIAL)
                elif caso == "fallida":
                    with patch("spica.artefactos.cierre_exportacion.exportar_resultado_json", side_effect=ValueError("fixture")):
                        e = ejecutar_exportacion_tecnica(solicitud_piloto())
                    self.assertIs(e.operacion_observada.estado, S.FALLIDA)
                else:
                    evento.set()
                    e = ejecutar_exportacion_tecnica(solicitud_piloto(), cancelacion=evento)
                    self.assertIs(e.operacion_observada.estado, S.CANCELADA)
                r = coordinar(e.solicitud.inventario.composiciones[0], seleccion=seleccion(e, None))
                self.assertFalse(r.arista_admitida_por_rc14)
                self.assertNotIn("consumidor", r.habilitadas_declarativamente)

    def test_concluida_declarada_sin_captura_no_habilita(self):
        e, a = nativos14(estado=S.CONCLUIDA)
        r = coordinar(e.solicitud.inventario.composiciones[0], seleccion=seleccion(e, a))
        self.assertFalse(e.productor_invocado)
        self.assertFalse(r.arista_admitida_por_rc14)
        self.assertNotIn("consumidor", r.habilitadas_declarativamente)

    def test_historia_rc10_no_recupera_admision_actual(self):
        with entorno_conservacion() as c:
            dep = historico(c, self.e, self.a)
            sel = Seleccion(S13(dep, P13(dep.politica, "salida-exportacion")))
            r = self.examinar(seleccion=sel)
            self.assertIs(r.decision_precondicion, DD.NO_ADMISIBLE)
            self.assertTrue(r.precondicion.dictamen_rc11.recuperacion.recuperada_en_alcance)
            self.assertFalse(r.arista_admitida_por_rc14)
            self.assertNotIn("consumidor", r.habilitadas_declarativamente)
        self.assertFalse(c.raiz.exists())

    def test_portador_rc10_no_es_inventario_de_coordinacion_rc7(self):
        with entorno_conservacion() as c:
            dep = historico(c, self.e, self.a)
            rec = recuperar_generacion(c.raiz, dep.control_historico.generacion)
            vinculo = VinculoEntradaRecuperada("consumidor", "salida-exportacion", self.e.solicitud.salida)
            s7 = SolicitudIntegracion(rec, self.c, (vinculo,), USO_CONSUMIR)
            r = integrar(s7, seleccion=self.sel)
            self.assertFalse(r.arista_admitida_por_rc14)
            self.assertNotIn("consumidor", r.habilitadas_declarativamente)
            self.assertIn("inventario_recuperado_ajeno_a_precondicion", codigos(r))
        self.assertFalse(c.raiz.exists())

    def test_fisica_contradictoria_actual_impide_admision(self):
        with entorno_materializacion() as m:
            mat = materializar(m, self.e)
            a = admitir_exportacion_tecnica(s9(self.e, materializacion=mat, exigir_integridad_fisica=True))
            ruta = m.raiz / mat.referencia.nombre
            b = ruta.read_bytes()
            ruta.write_bytes(b"!"+b[1:])
            r = self.examinar(seleccion=seleccion(self.e, a))
            self.assertIs(r.decision_precondicion, DD.NO_SATISFECHA)
            self.assertFalse(r.arista_admitida_por_rc14)
            self.assertNotIn("consumidor", r.habilitadas_declarativamente)
        self.assertFalse(m.raiz.exists())

    def test_fuente_fisica_externa_pendiente_no_se_compensa_en_rc7(self):
        with recuperacion(self.e, externo_qa=True) as (s7, m, c):
            r = integrar(s7, seleccion=self.sel)
            self.assertIs(r.decision_precondicion, DD.SATISFECHA)
            self.assertFalse(r.arista_admitida_por_rc14)
            self.assertNotIn("consumidor", r.habilitadas_declarativamente)
            self.assertEqual(r.opcional.dependencias[0][1], E.PENDIENTE_DE_EVIDENCIA)
        self.assertFalse(m.raiz.exists())
        self.assertFalse(c.raiz.exists())

    def test_entrada_consumidora_externa_no_se_habilita_en_rc7(self):
        with recuperacion(self.e, externo_json=True) as (s7, m, c):
            r = integrar(s7, seleccion=self.sel)
            self.assertIs(r.decision_precondicion, DD.SATISFECHA)
            self.assertNotIn("consumidor", r.habilitadas_declarativamente)
            consumidor = next(x for x in r.opcional.coordinacion_integrada.operaciones if x.nodo.contexto.operacion_id == "consumidor")
            self.assertTrue(any(x.codigo == "contenido_solo_referenciado_sin_comprobacion_actual" for x in consumidor.diagnosticos))
        self.assertFalse(m.raiz.exists())
        self.assertFalse(c.raiz.exists())

    def test_recuperacion_corrupta_no_es_compensada_por_rc13(self):
        with recuperacion(self.e) as (s7, m, c):
            ruta = c.raiz / "datos-000.bin"
            b = ruta.read_bytes()
            ruta.write_bytes(b"!"+b[1:])
            rec = recuperar_generacion(c.raiz, s7.recuperacion.control)
            r = integrar(replace(s7, recuperacion=rec), seleccion=self.sel)
            self.assertFalse(r.arista_admitida_por_rc14)
            self.assertNotIn("consumidor", r.habilitadas_declarativamente)
        self.assertFalse(m.raiz.exists())
        self.assertFalse(c.raiz.exists())

    def test_cotas_rc3_y_rc7_no_se_relajan(self):
        c3 = replace(self.c, limites=LimitesComposicion(max_operaciones=1))
        r3 = coordinar(c3, seleccion=self.sel)
        self.assertEqual(r3.habilitadas_declarativamente, ())
        self.assertFalse(r3.arista_admitida_por_rc14)
        with recuperacion(self.e) as (s7, m, c):
            r7 = integrar(replace(s7, limites=LimitesComposicion(max_operaciones=1)), seleccion=self.sel)
            self.assertEqual(r7.habilitadas_declarativamente, ())
            self.assertFalse(r7.arista_admitida_por_rc14)
        self.assertFalse(m.raiz.exists())
        self.assertFalse(c.raiz.exists())

    def test_cancelacion_no_despacha_cotejo_ni_habilita(self):
        evento = Event()
        evento.set()
        with patch("spica.artefactos.coordinacion_precondicion.examinar_precondicion_productora") as p:
            r = self.examinar(cancelacion=evento)
        p.assert_not_called()
        self.assertIs(r.decision_precondicion, DD.PENDIENTE)
        self.assertEqual(r.habilitadas_declarativamente, ())
        self.assertFalse(r.arista_admitida_por_rc14)

    def test_orden_predeterminado_y_determinismo_conservados(self):
        a, b = self.examinar(), self.examinar()
        self.assertEqual(a, b)
        self.assertEqual(a.opcional.orden_precedencia, a.predeterminado.orden_precedencia)
        self.assertEqual(a.dependencias, b.dependencias)
        self.assertEqual(a.restricciones, b.restricciones)

    def test_sin_despacho_automatico_permiso_o_validacion_cientifica(self):
        with patch("spica.artefactos.cierre_exportacion.exportar_resultado_json", side_effect=AssertionError("despacho")), \
                patch("spica.artefactos.admision_exportacion.admitir_exportacion_tecnica", side_effect=AssertionError("despacho")), \
                patch("spica.calidad.motor.evaluar_registro", side_effect=AssertionError("QA nuevo")):
            r = self.examinar()
        self.assertTrue(r.arista_admitida_por_rc14)
        for campo in ("autoriza_operacion", "ejecucion_realizada", "autenticidad_acreditada", "validacion_cientifica"):
            self.assertFalse(getattr(r, campo))
        with self.assertRaises(TypeError):
            bool(r)

    def test_no_hay_cotejo_fisico_implicito_en_modo_memoria(self):
        with patch("spica.artefactos.admision_exportacion.verificar_fisicamente", side_effect=AssertionError("fisica")):
            self.assertTrue(self.examinar().arista_admitida_por_rc14)

    def test_proceso_aislado_prohibe_red_sqlite_y_escrituras(self):
        codigo = r'''
import os,sys
def barrera(evento,args):
    if evento.startswith('socket.') or evento=='sqlite3.connect':
        raise RuntimeError('efecto_prohibido_rc14')
    if evento=='open':
        p,modo,flags=args
        if 'spica_datos' in str(p).casefold(): raise RuntimeError('operativo_prohibido')
        if (isinstance(modo,str) and any(c in modo for c in 'wax+')) or flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):
            raise RuntimeError('escritura_prohibida')
    if evento in ('os.mkdir','os.remove','os.rmdir','os.rename','os.link','os.symlink','os.chmod'):
        raise RuntimeError('mutacion_prohibida')
sys.addaudithook(barrera)
from test_coordinacion_precondicion_rc14 import nativos14,seleccion,coordinar
e,a=nativos14()
r=coordinar(e.solicitud.inventario.composiciones[0],seleccion=seleccion(e,a))
assert r.arista_admitida_por_rc14 and not r.autoriza_operacion
print('RC14_SIN_EFECTOS')
'''
        raiz = Path(__file__).resolve().parents[1]
        rutas = str(raiz / "src") + os.pathsep + str(raiz / "tests")
        r = subprocess.run([sys.executable, "-B", "-c", codigo], capture_output=True, text=True,
            env=dict(os.environ, PYTHONPATH=rutas, PYTHONDONTWRITEBYTECODE="1"), timeout=45)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), "RC14_SIN_EFECTOS")

    def test_importaciones_en_dos_ordenes_sin_reentrada(self):
        ruta = str(Path(__file__).resolve().parents[1] / "src")
        for codigo in ("import spica.artefactos.coordinacion_precondicion; import spica.coordinacion",
                "import spica.coordinacion; import spica.artefactos.coordinacion_precondicion"):
            with self.subTest(codigo=codigo):
                r = subprocess.run([sys.executable, "-B", "-c", codigo], capture_output=True, text=True,
                    env=dict(os.environ, PYTHONPATH=ruta, PYTHONDONTWRITEBYTECODE="1"), timeout=30)
                self.assertEqual(r.returncode, 0, r.stderr)

    def test_tipado_estricto_sin_politicas_ejecutables(self):
        for crear in (lambda: Seleccion({}), lambda: self.examinar(seleccion=True),
                lambda: coordinar({}, seleccion=self.sel), lambda: integrar({}, seleccion=self.sel),
                lambda: self.examinar(cancelacion=lambda: False)):
            with self.subTest(crear=crear), self.assertRaises(TypeError):
                crear()


if __name__ == "__main__":
    unittest.main()
