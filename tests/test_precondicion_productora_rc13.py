"""RC13: datos sintéticos, APIs nativas y TEMP propio; sin efectos operativos."""

from dataclasses import FrozenInstanceError, replace
import hashlib
import os
from pathlib import Path
import subprocess
import sys
from threading import Event
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from spica.adquisicion.readquisicion.modelos import EstadoLocal
from spica.artefactos import ReferenciaArtefacto
from spica.artefactos.admision_exportacion import admitir_exportacion_tecnica, USO_CONSUMIR
from spica.artefactos.cierre_exportacion import ejecutar_exportacion_tecnica, USO_EXPORTAR
from spica.artefactos.conservacion import (
    UnidadConservacion, entorno_conservacion, recuperar_generacion, EstadoRecuperacion,
)
from spica.artefactos.coordinacion import (
    SolicitudIntegracion, VinculoEntradaRecuperada, inspeccionar_integracion,
)
from spica.artefactos.dependencia_exportacion import (
    DecisionDependencia as DD, SolicitudDependenciaExportacion as Solicitud11,
)
from spica.artefactos.materializacion import entorno_materializacion
from spica.artefactos.precondicion_productora import (
    PoliticaPrecondicionProductora as Politica,
    SolicitudPrecondicionProductora as Solicitud,
    examinar_precondicion_productora as examinar,
)
from spica.calidad.consumo import consumir_exportaciones
from spica.calidad.exportacion import exportar_resultado_json
from spica.calidad.restricciones import RestriccionQA, TipoRestriccionQA as TR
from spica.contextos import EstadoOperacion as S
from spica.coordinacion import DependenciaOperacion, inspeccionar_composicion
from spica.interoperabilidad.modelos import EstadoAptitud as E
# Solo fabricantes de fixtures; importar TestCase duplicaría el descubrimiento.
from test_dependencia_noqa_rc11 import solicitud_exportacion, politica, nativos, historico
from test_admision_exportacion_rc9 import solicitud as s9, materializar
from test_coordinacion_rc3 import qa_real


def seleccion(p):
    return Politica(p, p.dependencia.referencias_resultado[0])


def codigos(r):
    return {d.codigo for d in r.diagnosticos}


class PrecondicionProductoraRC13Tests(unittest.TestCase):
    def setUp(self):
        self.e, self.a = nativos()
        self.p = politica(self.e)
        self.s11 = Solicitud11(self.p, self.e, self.a)

    def evaluar(self, *, dependencia=None, **kw):
        dep = self.s11 if dependencia is None else dependencia
        valores = dict(dependencia=dep, politica=seleccion(dep.politica))
        valores.update(kw)
        return examinar(Solicitud(**valores))

    def test_precondicion_local_satisfecha_sin_admision_nativa(self):
        r = self.evaluar()
        self.assertIs(r.decision, DD.SATISFECHA, r.diagnosticos)
        self.assertIs(r.dictamen_rc11.decision, DD.NO_ADMISIBLE)
        self.assertTrue(r.dictamen_rc11.cierre.cierre_tecnico_comprobado)
        self.assertTrue(r.dictamen_rc11.admision.admisible_para_consumo_tecnico)
        self.assertIs(self.e.operacion_observada.estado, S.CONCLUIDA)
        self.assertIs(self.e.solicitud.inventario.composiciones[0].operaciones[1].contexto.estado, S.DECLARADA)
        self.assertNotIn("consumidor", r.coordinacion_rc3.habilitadas_declarativamente)
        self.assertFalse(r.habilitacion_rc3_rc7)
        self.assertFalse(r.ejecucion_automatica)
        self.assertFalse(r.autoriza_operacion)
        self.assertFalse(r.autenticidad_acreditada)
        self.assertFalse(r.validacion_cientifica)
        with self.assertRaises(TypeError):
            bool(r)

    def test_productor_y_consumidor_realmente_invocados(self):
        with patch("spica.artefactos.cierre_exportacion.exportar_resultado_json", wraps=exportar_resultado_json) as p:
            e = ejecutar_exportacion_tecnica(solicitud_exportacion())
        with patch("spica.artefactos.admision_exportacion.consumir_exportaciones", wraps=consumir_exportaciones) as c:
            a = admitir_exportacion_tecnica(s9(e))
        p.assert_called_once()
        c.assert_called_once()
        r = self.evaluar(dependencia=Solicitud11(politica(e), e, a))
        self.assertIs(r.decision, DD.SATISFECHA)

    def test_dictamen_no_despacha_operaciones(self):
        with patch("spica.artefactos.cierre_exportacion.exportar_resultado_json", side_effect=AssertionError("despacho")), \
                patch("spica.artefactos.admision_exportacion.admitir_exportacion_tecnica", side_effect=AssertionError("despacho")), \
                patch("spica.calidad.motor.evaluar_registro", side_effect=AssertionError("QA nuevo")):
            self.assertIs(self.evaluar().decision, DD.SATISFECHA)

    def test_sin_politica_no_hay_admision(self):
        self.assertIs(self.evaluar(politica=None).decision, DD.NO_ADMISIBLE)

    def test_perfil_clase_confianza_y_version_desconocidos(self):
        for campo in ("perfil", "clase_cierre", "confianza", "version_contrato"):
            with self.subTest(campo=campo):
                p = replace(seleccion(self.p), **{campo: "desconocido"})
                r = self.evaluar(politica=p)
                self.assertIs(r.decision, DD.NO_ADMISIBLE)

    def test_politica_y_solicitud_no_intercambiables(self):
        mala = replace(self.p, contenido_id="otra-identidad")
        r = self.evaluar(politica=seleccion(mala))
        self.assertIs(r.decision, DD.NO_SATISFECHA)
        self.assertIn("politica_rc13_y_solicitud_rc11_discrepantes", codigos(r))

    def test_productor_incompatible_no_se_ejecuta(self):
        e = ejecutar_exportacion_tecnica(solicitud_exportacion(metodo="productor.ajeno"))
        a = admitir_exportacion_tecnica(s9(e))
        r = self.evaluar(dependencia=Solicitud11(politica(e), e, a))
        self.assertFalse(e.productor_invocado)
        self.assertIs(r.decision, DD.NO_SATISFECHA)

    def test_consumidor_incompatible_rechazado(self):
        a = admitir_exportacion_tecnica(s9(self.e, consumidor_id="consumidor.ajeno"))
        r = self.evaluar(dependencia=replace(self.s11, admision=a))
        self.assertIs(r.decision, DD.NO_SATISFECHA)

    def test_operaciones_productora_y_dependiente_inequivocas(self):
        for d in (replace(self.p.dependencia, predecesora="otra-productora"),
                  replace(self.p.dependencia, dependiente="otro-consumidor")):
            with self.subTest(d=d):
                p = replace(self.p, dependencia=d)
                self.assertIs(self.evaluar(dependencia=replace(self.s11, politica=p)).decision, DD.NO_SATISFECHA)

    def test_otra_operacion_consumidora_real_no_reutiliza_captura(self):
        inv = self.p.inventario
        comp = inv.composiciones[0]
        p, n = comp.operaciones
        otro = replace(n, contexto=replace(n.contexto, operacion_id="otro-consumidor"))
        d = replace(comp.dependencias[0], dependiente="otro-consumidor")
        comp = replace(comp, operaciones=(p, otro), dependencias=(d,))
        nuevo = replace(self.p, inventario=replace(inv, composiciones=(comp,)), dependencia=d)
        self.assertIs(self.evaluar(dependencia=replace(self.s11, politica=nuevo)).decision, DD.NO_SATISFECHA)

    def test_entrada_resultado_artefacto_revision_y_contenido(self):
        for kw in (dict(entrada_resultado_id="otro-resultado"), dict(contenido_id="otro-contenido"),
                   dict(artefacto=ReferenciaArtefacto(self.p.artefacto.object_id, "r2"))):
            with self.subTest(kw=kw):
                p = replace(self.p, **kw)
                self.assertIs(self.evaluar(dependencia=replace(self.s11, politica=p)).decision, DD.NO_SATISFECHA)
        self.assertIs(self.evaluar(politica=replace(seleccion(self.p), entrada_consumidora_id="ajena")).decision,
                      DD.NO_SATISFECHA)

    def test_versiones_nativas_incompatibles(self):
        for kw in (dict(version_productor="9.0.0"), dict(version_contrato="9.0.0")):
            with self.subTest(kw=kw):
                e = replace(self.e, **kw)
                self.assertIs(self.evaluar(dependencia=replace(self.s11, evidencia=e, admision=None)).decision,
                              DD.NO_SATISFECHA)
        a = admitir_exportacion_tecnica(s9(self.e, version_consumidor="9.0.0"))
        self.assertIs(self.evaluar(dependencia=replace(self.s11, admision=a)).decision, DD.NO_SATISFECHA)

    def test_resultado_tamano_y_hash_alterados(self):
        for kw in (dict(resultado_nativo=self.e.resultado_nativo+" "), dict(size_bytes=1),
                   dict(sha256_bytes="0"*64)):
            with self.subTest(kw=kw):
                e = replace(self.e, **kw)
                r = self.evaluar(dependencia=replace(self.s11, evidencia=e, admision=None))
                self.assertIs(r.decision, DD.NO_SATISFECHA)

    def test_sin_rc8_ni_rc9_pendiente(self):
        r = self.evaluar(dependencia=replace(self.s11, evidencia=None, admision=None))
        self.assertIs(r.decision, DD.PENDIENTE)

    def test_sin_rc9_pendiente(self):
        self.assertIs(self.evaluar(dependencia=replace(self.s11, admision=None)).decision, DD.PENDIENTE)

    def test_rc8_rc9_contradictorios(self):
        e2, a2 = nativos(project_id="proyecto-RC13-B")
        self.assertIs(self.evaluar(dependencia=replace(self.s11, admision=a2)).decision, DD.NO_SATISFECHA)
        self.assertNotEqual(e2.operacion_observada.proyecto, self.e.operacion_observada.proyecto)

    def test_testigos_ausentes_no_satisfacen(self):
        for dep in (replace(self.s11, evidencia=replace(self.e), admision=None),
                    replace(self.s11, admision=replace(self.a))):
            with self.subTest(admision=dep.admision is None):
                self.assertIs(self.evaluar(dependencia=dep).decision, DD.PENDIENTE)

    def test_dto_favorable_o_copia_no_es_contraste_actual(self):
        r = self.evaluar()
        copia = replace(r, diagnosticos=())
        self.assertFalse(copia.contraste_local_coherente)
        self.assertIs(copia.decision, DD.PENDIENTE)
        with self.assertRaises(FrozenInstanceError):
            r.diagnosticos = ()

    def test_bloqueo_aplicable_prevalece_sobre_faltantes(self):
        bloqueo = RestriccionQA("bloqueo-rc13", TR.BLOQUEO_USO_DEL_RESULTADO,
            (USO_CONSUMIR,), "Fixture: consumo bloqueado")
        p = replace(self.p, restricciones_adicionales=(bloqueo,))
        r = self.evaluar(dependencia=replace(self.s11, politica=p, admision=None))
        self.assertIs(r.decision, DD.NO_SATISFECHA)
        self.assertIn(bloqueo, tuple(x.restriccion for x in r.restricciones))

    def test_aplicabilidad_desconocida_no_autoriza(self):
        s = solicitud_exportacion()
        c = s.inventario.composiciones[0]
        prod, dep = c.operaciones
        c = replace(c, operaciones=(prod, replace(dep, usos_declarados=None)))
        s = replace(s, inventario=replace(s.inventario, composiciones=(c,)))
        e = ejecutar_exportacion_tecnica(s)
        a = admitir_exportacion_tecnica(s9(e))
        self.assertIs(self.evaluar(dependencia=Solicitud11(politica(e), e, a)).decision, DD.PENDIENTE)

    def test_restricciones_heredadas_con_origen_sin_duplicar_pruebas(self):
        r = self.evaluar()
        self.assertEqual(r.restricciones, r.dictamen_rc11.restricciones)
        self.assertTrue(r.restricciones)
        self.assertTrue(all(x.origenes for x in r.restricciones))
        self.assertEqual(len(r.restricciones), len(set(x.restriccion for x in r.restricciones)))

    def test_salida_parcial_observada_no_se_promueve(self):
        evento = Event()
        def parcial(*args, **kw):
            texto = exportar_resultado_json(*args, **kw)
            evento.set()
            return texto
        with patch("spica.artefactos.cierre_exportacion.exportar_resultado_json", side_effect=parcial):
            e = ejecutar_exportacion_tecnica(solicitud_exportacion(), cancelacion=evento)
        self.assertIs(e.operacion_observada.estado, S.PARCIAL)
        self.assertIs(self.evaluar(dependencia=Solicitud11(politica(e), e, None)).decision, DD.NO_SATISFECHA)

    def test_fallo_observado_no_se_promueve(self):
        with patch("spica.artefactos.cierre_exportacion.exportar_resultado_json", side_effect=ValueError("fixture")):
            e = ejecutar_exportacion_tecnica(solicitud_exportacion())
        self.assertIs(e.operacion_observada.estado, S.FALLIDA)
        self.assertIs(self.evaluar(dependencia=Solicitud11(politica(e), e, None)).decision, DD.NO_SATISFECHA)

    def test_cancelacion_observada_no_se_promueve(self):
        evento = Event()
        evento.set()
        e = ejecutar_exportacion_tecnica(solicitud_exportacion(), cancelacion=evento)
        self.assertIs(e.operacion_observada.estado, S.CANCELADA)
        self.assertIs(self.evaluar(dependencia=Solicitud11(politica(e), e, None)).decision, DD.NO_SATISFECHA)

    def test_conclusion_declarada_no_sustituye_captura(self):
        e = ejecutar_exportacion_tecnica(solicitud_exportacion(estado=S.CONCLUIDA))
        self.assertFalse(e.productor_invocado)
        self.assertIsNot(self.evaluar(dependencia=Solicitud11(politica(e), e, None)).decision, DD.SATISFECHA)

    def test_dos_proyectos_con_bytes_identicos_conservan_identidades(self):
        e2, a2 = nativos(project_id="proyecto-RC13-B")
        self.assertEqual(self.e.resultado_nativo, e2.resultado_nativo)
        self.assertEqual(self.e.sha256_bytes, e2.sha256_bytes)
        r1 = self.evaluar()
        r2 = self.evaluar(dependencia=Solicitud11(politica(e2), e2, a2))
        self.assertIs(r1.decision, DD.SATISFECHA)
        self.assertIs(r2.decision, DD.SATISFECHA)
        self.assertNotEqual(r1.solicitud.dependencia.politica.inventario,
                            r2.solicitud.dependencia.politica.inventario)
        self.assertIs(self.evaluar(dependencia=replace(self.s11, evidencia=e2, admision=a2)).decision,
                      DD.NO_SATISFECHA)

    def test_linaje_contradictorio_no_satisface(self):
        inv = self.p.inventario
        produccion = replace(inv.producciones[0], entradas=inv.producciones[0].salidas)
        p = replace(self.p, inventario=replace(inv, producciones=(produccion,)))
        self.assertIs(self.evaluar(dependencia=replace(self.s11, politica=p)).decision, DD.NO_SATISFECHA)

    def test_rc3_predeterminado_estados_diagnosticos_y_contadores_intactos(self):
        c = self.p.inventario.composiciones[0]
        antes = inspeccionar_composicion(c)
        r = self.evaluar()
        self.assertEqual(antes, r.coordinacion_rc3)
        self.assertEqual(antes, inspeccionar_composicion(c))
        self.assertEqual(antes.consumos_qa_aportados, ())
        self.assertTrue(all(not x.cierre_qa_coherente_completo for x in antes.operaciones))
        self.assertTrue(any(d.codigo == "dependencia_sin_cierre_tecnico_compatible_aportado"
            for x in antes.operaciones for d in x.diagnosticos))

    def test_cierre_qa_genuino_se_conserva_separado(self):
        qa = qa_real()
        c = self.p.inventario.composiciones[0]
        c = replace(c, proyecto=qa.contexto.proyecto, operaciones=(qa,), dependencias=())
        antes = inspeccionar_composicion(c)
        self.assertTrue(antes.operaciones[0].cierre_qa_coherente_completo)
        self.evaluar()
        self.assertEqual(antes, inspeccionar_composicion(c))

    def test_dictamen_determinista_en_memoria(self):
        primero, segundo = self.evaluar(), self.evaluar()
        self.assertEqual(primero, segundo)
        self.assertEqual(primero.decision, segundo.decision)
        self.assertEqual(primero.diagnosticos, segundo.diagnosticos)

    def test_autenticidad_y_externos_exigidos_permanecen_pendientes(self):
        for campo in ("exigir_autenticidad_independiente", "exigir_externos_disponibles", "exigir_integridad_fisica"):
            with self.subTest(campo=campo):
                p = replace(self.p, **{campo: True})
                self.assertIs(self.evaluar(dependencia=replace(self.s11, politica=p)).decision, DD.PENDIENTE)

    def test_fisica_opcional_no_abre_archivos(self):
        with patch("spica.artefactos.admision_exportacion.verificar_fisicamente", side_effect=AssertionError("fisica")):
            r = self.evaluar()
        self.assertIsNone(r.dictamen_rc11.verificacion_actual)
        self.assertIs(r.decision, DD.SATISFECHA)

    def test_fisica_exigida_relee_bytes_actuales_y_limpia_temp(self):
        with entorno_materializacion() as m:
            mat = materializar(m, self.e)
            a = admitir_exportacion_tecnica(s9(self.e, materializacion=mat, exigir_integridad_fisica=True))
            r = self.evaluar(dependencia=replace(self.s11, admision=a))
            self.assertIs(r.decision, DD.SATISFECHA, r.diagnosticos)
            v = r.dictamen_rc11.verificacion_actual
            self.assertIs(v.estado_local, EstadoLocal.INTEGRO)
            self.assertIsNot(v, a.verificacion_fisica)
            self.assertEqual(v.sha256_fisico, hashlib.sha256(self.e.resultado_nativo.encode()).hexdigest())
        self.assertFalse(m.raiz.exists())

    def test_archivo_alterado_despues_de_rc9_no_satisface(self):
        with entorno_materializacion() as m:
            mat = materializar(m, self.e)
            a = admitir_exportacion_tecnica(s9(self.e, materializacion=mat, exigir_integridad_fisica=True))
            ruta = m.raiz / mat.referencia.nombre
            b = ruta.read_bytes()
            ruta.write_bytes(b"!"+b[1:])
            r = self.evaluar(dependencia=replace(self.s11, admision=a))
            self.assertIs(r.decision, DD.NO_SATISFECHA)
            self.assertIs(r.dictamen_rc11.verificacion_actual.estado_local, EstadoLocal.INCONSISTENTE)
        self.assertFalse(m.raiz.exists())

    def test_archivo_ausente_despues_de_rc9_no_satisface(self):
        with entorno_materializacion() as m:
            mat = materializar(m, self.e)
            a = admitir_exportacion_tecnica(s9(self.e, materializacion=mat, exigir_integridad_fisica=True))
            m._archivos.quitar_propio(mat.referencia.nombre)
            r = self.evaluar(dependencia=replace(self.s11, admision=a))
            self.assertIs(r.decision, DD.NO_SATISFECHA)
        self.assertFalse(m.raiz.exists())

    def test_historia_rc10_integra_no_es_ejecucion_actual(self):
        with entorno_conservacion() as c:
            dep = historico(c, self.e, self.a)
            r = self.evaluar(dependencia=dep)
            self.assertTrue(r.dictamen_rc11.recuperacion.recuperada_en_alcance)
            self.assertIs(r.decision, DD.NO_ADMISIBLE)
            ex = r.dictamen_rc11.recuperacion.expediente
            self.assertTrue(ex.hechos.cierre_rc8_comprobado)
            self.assertTrue(ex.hechos.admision_rc9_comprobada)
            self.assertFalse(ex.cierre_rc8.evidencia.captura_local_coherente)
            self.assertFalse(ex.admision_rc9.comprobacion_local_coherente)
        self.assertFalse(c.raiz.exists())

    def test_historia_corrupta_no_se_promueve(self):
        with entorno_conservacion() as c:
            dep = historico(c, self.e, self.a)
            ruta = c.raiz / "datos-000.bin"
            b = ruta.read_bytes()
            ruta.write_bytes(b"!"+b[1:])
            self.assertIs(self.evaluar(dependencia=dep).decision, DD.NO_SATISFECHA)
        self.assertFalse(c.raiz.exists())

    def test_rc7_recupera_inventario_original_y_conserva_bloqueo(self):
        with entorno_materializacion() as m, entorno_conservacion() as c:
            mat = materializar(m, self.e)
            inv = self.e.solicitud.inventario
            guardado = c.conservar(UnidadConservacion(inv, (mat,), (inv.artefactos[0].referencia,)))
            rec = recuperar_generacion(c.raiz, guardado.control)
            self.assertIs(rec.estado, EstadoRecuperacion.VERIFICADA)
            comp = rec.unidad.inventario.composiciones[0]
            vinculo = VinculoEntradaRecuperada("consumidor", self.p.dependencia.referencias_resultado[0], self.p.artefacto)
            s7 = SolicitudIntegracion(rec, comp, (vinculo,), USO_CONSUMIR)
            antes = inspeccionar_integracion(s7)
            r = self.evaluar(integracion=s7)
            self.assertIs(r.decision, DD.SATISFECHA, r.diagnosticos)
            self.assertEqual(r.integracion_rc7, antes)
            self.assertEqual(antes, inspeccionar_integracion(s7))
            self.assertNotIn("consumidor", r.integracion_rc7.habilitadas_declarativamente)
            self.assertTrue(all(estado is E.PENDIENTE_DE_EVIDENCIA for _, estado in antes.dependencias))
            self.assertEqual(rec.unidad.inventario, inv)
            self.assertIs(comp.operaciones[0].contexto.estado, S.INICIADA)
            # La ausencia de política no modifica el inspector nativo tampoco.
            sin = self.evaluar(politica=None, integracion=s7)
            self.assertIs(sin.decision, DD.NO_ADMISIBLE)
            self.assertEqual(sin.integracion_rc7, antes)
        self.assertFalse(m.raiz.exists())
        self.assertFalse(c.raiz.exists())

    def test_portador_rc10_no_sustituye_inventario_original_rc7(self):
        with entorno_conservacion() as c:
            dep = historico(c, self.e, self.a)
            rec = recuperar_generacion(c.raiz, dep.control_historico.generacion)
            comp = self.p.inventario.composiciones[0]
            vinculo = VinculoEntradaRecuperada("consumidor", self.p.dependencia.referencias_resultado[0], self.p.artefacto)
            s7 = SolicitudIntegracion(rec, comp, (vinculo,), USO_CONSUMIR)
            self.assertIs(self.evaluar(integracion=s7).decision, DD.NO_SATISFECHA)
        self.assertFalse(c.raiz.exists())

    def test_sin_red_sqlite_ni_almacenamiento_operativo(self):
        with patch("socket.socket.connect", side_effect=AssertionError("red")), \
                patch("sqlite3.connect", side_effect=AssertionError("SQLite")), \
                patch("spica.adquisicion.almacenamiento.raw.AlmacenRAW.__init__", side_effect=AssertionError("RAW")), \
                patch("spica.adquisicion.almacenamiento.configuracion.ConfiguracionRAW.abrir", side_effect=AssertionError("operativo")):
            self.assertIs(self.evaluar().decision, DD.SATISFECHA)

    def test_importacion_aislada_sin_ciclos_de_inicializacion(self):
        src = str(Path(__file__).resolve().parents[1] / "src")
        for codigo in (
            "import spica.artefactos.precondicion_productora; import spica.coordinacion",
            "import spica.coordinacion; import spica.artefactos.coordinacion; import spica.artefactos.precondicion_productora",
        ):
            with self.subTest(orden=codigo):
                r = subprocess.run([sys.executable, "-B", "-c", codigo], capture_output=True, text=True,
                    env=dict(os.environ, PYTHONPATH=src, PYTHONDONTWRITEBYTECODE="1"), timeout=30)
                self.assertEqual(r.returncode, 0, r.stderr)

    def test_piloto_en_proceso_con_barreras_de_efectos(self):
        codigo = r'''
import os, sys
def barrera(evento, args):
    if evento.startswith('socket.') or evento == 'sqlite3.connect':
        raise RuntimeError('red_sqlite_prohibidos_rc13')
    if evento == 'open':
        p, modo, flags = args
        if 'spica_datos' in str(p).casefold():
            raise RuntimeError('operativo_prohibido_rc13')
        if ((isinstance(modo, str) and any(c in modo for c in 'wax+'))
                or flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)):
            raise RuntimeError('escritura_prohibida_rc13')
    if evento in ('os.mkdir', 'os.remove', 'os.rmdir', 'os.rename', 'os.link', 'os.symlink', 'os.chmod'):
        raise RuntimeError('mutacion_prohibida_rc13')
sys.addaudithook(barrera)
from test_dependencia_noqa_rc11 import nativos, politica, Solicitud, DD
from spica.artefactos.precondicion_productora import (
    PoliticaPrecondicionProductora as P, SolicitudPrecondicionProductora as S,
    examinar_precondicion_productora,
)
e, a = nativos()
p = politica(e)
r = examinar_precondicion_productora(S(Solicitud(p, e, a), P(p, p.dependencia.referencias_resultado[0])))
assert r.decision is DD.SATISFECHA and not r.habilitacion_rc3_rc7
print('RC13_SIN_EFECTOS')
'''
        raiz = Path(__file__).resolve().parents[1]
        ruta = str(raiz / "src") + os.pathsep + str(raiz / "tests")
        r = subprocess.run([sys.executable, "-B", "-c", codigo], capture_output=True, text=True,
            env=dict(os.environ, PYTHONPATH=ruta, PYTHONDONTWRITEBYTECODE="1"), timeout=45)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), "RC13_SIN_EFECTOS")

    def test_contratos_tipificados_y_sin_codigo_cargado(self):
        for crear in (lambda: Solicitud({}), lambda: Solicitud(self.s11, politica={}),
                      lambda: Solicitud(self.s11, integracion={}), lambda: Politica({}, "entrada")):
            with self.subTest(crear=crear), self.assertRaises(TypeError):
                crear()
        with self.assertRaises(TypeError):
            examinar({})


if __name__ == "__main__":
    unittest.main()
