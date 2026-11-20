"""RC11: arista explícita, productores nativos y TEMP sintético exclusivamente."""

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
from spica.artefactos.cierre_exportacion import ejecutar_exportacion_tecnica, USO_EXPORTAR
from spica.artefactos.admision_exportacion import admitir_exportacion_tecnica, USO_CONSUMIR
from spica.artefactos.conservacion_evidencias import capturar_evidencias
from spica.artefactos.conservacion import entorno_conservacion
from spica.artefactos.coordinacion import SolicitudIntegracion, inspeccionar_integracion
from spica.artefactos.materializacion import entorno_materializacion
from spica.artefactos.dependencia_exportacion import (
    DecisionDependencia as DD, PoliticaDependenciaExportacion as Politica,
    SolicitudDependenciaExportacion as Solicitud, dictaminar_dependencia_exportacion as dictaminar,
)
from spica.calidad.consumo import consumir_exportaciones
from spica.calidad.exportacion import exportar_resultado_json
from spica.calidad.restricciones import RestriccionQA, TipoRestriccionQA as TR
from spica.contextos import EstadoOperacion as S
from spica.coordinacion import DependenciaOperacion, inspeccionar_composicion
from spica.interoperabilidad.modelos import EstadoAptitud as E
# Fabricantes, nunca TestCase importados que dupliquen el descubrimiento.
from test_cierre_exportacion_rc8 import solicitud as s8
from test_admision_exportacion_rc9 import solicitud as s9, materializar
from test_conservacion_evidencias_rc10 import guardar
from test_coordinacion_rc3 import qa_real


def solicitud_exportacion(**kw):
    s = s8(contexto_id="contexto-RC11", **kw)
    c = s.inventario.composiciones[0]
    productor, consumidor = c.operaciones
    # Identidad y finalidad declaradas ANTES de ejecutar. Esta declaración no
    # acredita un cierre de la operación RC3 ni registra el consumidor en RC3.
    consumidor = replace(consumidor, contexto=replace(consumidor.contexto,
        proposito="Consumir JSON QA nativo en el piloto RC11"), usos_declarados=(USO_CONSUMIR,))
    c = replace(c, operaciones=(productor, consumidor))
    return replace(s, inventario=replace(s.inventario, composiciones=(c,)))


def politica(e, **kw):
    s = e.solicitud
    salida = next(x for x in s.inventario.artefactos if x.referencia == s.salida)
    valores = dict(inventario=s.inventario, composicion_id=s.composicion_id,
        dependencia=s.inventario.composiciones[0].dependencias[0], artefacto=s.salida,
        entrada_resultado_id=s.entrada_qa.referencia_resultado, contenido_id=salida.contenido_id)
    valores.update(kw)
    return Politica(**valores)


def nativos(**kw):
    e = ejecutar_exportacion_tecnica(solicitud_exportacion(**kw))
    a = admitir_exportacion_tecnica(s9(e))
    return e, a


def codigos(r):
    return {d.codigo for d in r.diagnosticos}


def historico(c, e, a):
    ex = capturar_evidencias(e, a, evidencia_id="expediente-RC11", proyecto=e.solicitud.entrada_qa.operacion.proyecto)
    control = guardar(c, ex)
    return Solicitud(politica(e), raiz_historica=c.raiz, control_historico=control)


class DependenciaNoQARC11Tests(unittest.TestCase):
    def setUp(self):
        self.e, self.a = nativos()
        self.p = politica(self.e)

    def evaluar(self, **kw):
        valores = dict(politica=self.p, evidencia=self.e, admision=self.a)
        valores.update(kw)
        return dictaminar(Solicitud(**valores))

    def test_cierre_real_coherente_pero_no_admisible_por_rc3_rc7(self):
        r = self.evaluar()
        self.assertTrue(r.cierre.cierre_tecnico_comprobado)
        self.assertTrue(r.admision.admisible_para_consumo_tecnico)
        self.assertIs(r.estado_correspondencia, E.APTO_ESTRUCTURALMENTE, codigos(r))
        self.assertIs(r.decision, DD.NO_ADMISIBLE)
        self.assertFalse(r.satisfecha)

    def test_piloto_invoca_productor_y_consumidor_nativos(self):
        with patch("spica.artefactos.cierre_exportacion.exportar_resultado_json", wraps=exportar_resultado_json) as p:
            e = ejecutar_exportacion_tecnica(solicitud_exportacion())
        with patch("spica.artefactos.admision_exportacion.consumir_exportaciones", wraps=consumir_exportaciones) as c:
            a = admitir_exportacion_tecnica(s9(e))
        p.assert_called_once()
        c.assert_called_once()
        r = dictaminar(Solicitud(politica(e), e, a))
        self.assertIs(r.decision, DD.NO_ADMISIBLE)

    def test_inspeccion_no_despacha_productor_ni_nueva_admision(self):
        with patch("spica.artefactos.cierre_exportacion.exportar_resultado_json", side_effect=AssertionError("despacho")), \
                patch("spica.artefactos.admision_exportacion.admitir_exportacion_tecnica", side_effect=AssertionError("admision")):
            self.assertIs(self.evaluar().decision, DD.NO_ADMISIBLE)

    def test_sin_evidencias_pendiente_y_sin_lecturas_fisicas(self):
        with patch("spica.artefactos.dependencia_exportacion._fisica", side_effect=AssertionError("lectura")):
            r = self.evaluar(evidencia=None, admision=None)
        self.assertIs(r.decision, DD.PENDIENTE)
        self.assertIn("evidencia_rc8_no_disponible", codigos(r))

    def test_rc8_sin_rc9_no_satisface(self):
        self.assertIs(self.evaluar(admision=None).decision, DD.PENDIENTE)

    def test_rc9_sin_rc8_es_contradictorio(self):
        self.assertIs(self.evaluar(evidencia=None).decision, DD.NO_SATISFECHA)

    def test_copias_no_restauran_testigos(self):
        for valores in (dict(evidencia=replace(self.e), admision=None), dict(admision=replace(self.a))):
            with self.subTest(valores=tuple(valores)):
                self.assertIs(self.evaluar(**valores).decision, DD.PENDIENTE)

    def test_alteracion_bytes_tamano_hash_y_productor(self):
        for cambios in (dict(resultado_nativo=self.e.resultado_nativo+" "), dict(size_bytes=1),
                dict(sha256_bytes="0"*64), dict(productor_id="otro.productor"), dict(version_productor="9.0.0")):
            with self.subTest(campos=tuple(cambios)):
                e = replace(self.e, **cambios)
                self.assertIs(self.evaluar(evidencia=e, admision=None).decision, DD.NO_SATISFECHA)

    def test_proyectos_independientes_no_se_fusionan_por_bytes(self):
        e2, a2 = nativos(project_id="proyecto-RC11-B")
        self.assertEqual(self.e.resultado_nativo, e2.resultado_nativo)
        self.assertEqual(self.e.sha256_bytes, e2.sha256_bytes)
        r1, r2 = self.evaluar(), dictaminar(Solicitud(politica(e2), e2, a2))
        self.assertIs(r1.decision, DD.NO_ADMISIBLE)
        self.assertIs(r2.decision, DD.NO_ADMISIBLE)
        self.assertNotEqual(r1.solicitud.politica.artefacto, r2.solicitud.politica.artefacto)
        self.assertIs(self.evaluar(evidencia=e2, admision=a2).decision, DD.NO_SATISFECHA)

    def test_politica_identidades_operaciones_revisiones_y_resultados(self):
        for cambios in (dict(composicion_id="otra-composicion"),
                dict(dependencia=DependenciaOperacion("otro", "consumidor", ("salida-exportacion",))),
                dict(dependencia=DependenciaOperacion("exportar", "otro", ("salida-exportacion",))),
                dict(artefacto=ReferenciaArtefacto(self.p.artefacto.object_id, "r2")),
                dict(entrada_resultado_id="otro-resultado"), dict(contenido_id="otro-contenido")):
            with self.subTest(campos=tuple(cambios)):
                self.assertIs(self.evaluar(politica=replace(self.p, **cambios)).decision, DD.NO_SATISFECHA)

    def test_rc9_consumidor_version_proyecto_y_entrada_incorrectos(self):
        e2, _ = nativos(project_id="proyecto-RC11-B")
        for cambios in (dict(consumidor_id="otro.consumidor"), dict(version_consumidor="9.0.0"),
                dict(proyecto=e2.solicitud.entrada_qa.operacion.proyecto),
                dict(operacion_productora_id="otro"), dict(entrada_resultado_id="otra"),
                dict(contenido_id="otro"), dict(finalidad="otro_uso")):
            with self.subTest(campos=tuple(cambios)):
                a = admitir_exportacion_tecnica(replace(s9(self.e), **cambios))
                self.assertIs(self.evaluar(admision=a).decision, DD.NO_SATISFECHA)

    def test_politica_fuera_del_perfil_no_da_permiso(self):
        for cambios in (dict(productor_id="otro"), dict(version_productor="9.0.0")):
            r = self.evaluar(politica=replace(self.p, **cambios))
            self.assertFalse(r.solicitud.politica.perfil_admitido)
            self.assertIs(r.decision, DD.NO_ADMISIBLE)
            self.assertFalse(r.autoriza_operacion)

    def test_restriccion_nueva_bloquea_y_no_se_cuenta_como_otra_evidencia(self):
        b = RestriccionQA("bloqueo-rc11", TR.BLOQUEO_USO_DEL_RESULTADO, (USO_CONSUMIR,), "Fixture")
        with self.assertRaises(ValueError):
            replace(self.p, restricciones_adicionales=(b, b))
        r = self.evaluar(politica=replace(self.p, restricciones_adicionales=(b,)))
        self.assertIs(r.decision, DD.NO_SATISFECHA)
        self.assertEqual(len(r.restricciones_nuevas), 1)
        self.assertIn(b, tuple(x.restriccion for x in r.restricciones_bloqueantes))

    def test_restricciones_informativas_no_aplicables_y_heredadas_permanecen(self):
        extra = RestriccionQA("otra-finalidad", TR.BLOQUEO_USO_DEL_RESULTADO, ("otro_uso",), "Fixture")
        r = self.evaluar(politica=replace(self.p, restricciones_adicionales=(extra,)))
        self.assertIs(r.decision, DD.NO_ADMISIBLE)
        self.assertTrue(r.restricciones_heredadas)
        self.assertIn(extra, tuple(x.restriccion for x in r.restricciones))
        self.assertNotIn(extra, tuple(x.restriccion for x in r.restricciones_bloqueantes))
        self.assertEqual(set(self.a.restricciones), {x.restriccion for x in r.restricciones_heredadas})

    def test_restricciones_contradictorias_conservan_ambas_variantes(self):
        vieja = self.a.restricciones[0]
        nueva = replace(vieja, motivo="otra definicion")
        r = self.evaluar(politica=replace(self.p, restricciones_adicionales=(nueva,)))
        self.assertIs(r.decision, DD.NO_SATISFECHA)
        self.assertIn(vieja, tuple(x.restriccion for x in r.restricciones))
        self.assertIn(nueva, tuple(x.restriccion for x in r.restricciones))

    def test_uso_desconocido_permanece_pendiente(self):
        s = solicitud_exportacion()
        c = s.inventario.composiciones[0]
        c = replace(c, operaciones=(c.operaciones[0], replace(c.operaciones[1], usos_declarados=None)))
        s = replace(s, inventario=replace(s.inventario, composiciones=(c,)))
        e = ejecutar_exportacion_tecnica(s)
        a = admitir_exportacion_tecnica(s9(e))
        self.assertIs(dictaminar(Solicitud(politica(e), e, a)).decision, DD.PENDIENTE)

    def test_autenticidad_exigida_no_se_infiere_del_hash(self):
        r = self.evaluar(politica=replace(self.p, exigir_autenticidad_independiente=True))
        self.assertIs(r.decision, DD.PENDIENTE)
        self.assertIn("autenticidad_independiente_no_acreditada", codigos(r))

    def test_fisica_requerida_sin_referencia_pendiente(self):
        self.assertIs(self.evaluar(politica=replace(self.p, exigir_integridad_fisica=True)).decision, DD.PENDIENTE)

    def test_externos_locales_no_se_declaran_comprobados(self):
        r = self.evaluar(politica=replace(self.p, exigir_externos_disponibles=True))
        self.assertIs(r.decision, DD.PENDIENTE)
        self.assertIn("referencias_externas_sin_comprobacion_actual", codigos(r))

    def test_bloqueo_heredado_del_proyecto_impide_consumo(self):
        b = RestriccionQA("bloqueo-proyecto", TR.BLOQUEO_USO_DEL_RESULTADO, (USO_CONSUMIR,), "Fixture")
        e, a = nativos(bloqueo=b)
        r = dictaminar(Solicitud(politica(e), e, a))
        self.assertIs(r.decision, DD.NO_SATISFECHA)
        self.assertIn(b, tuple(x.restriccion for x in r.restricciones_heredadas))

    def test_fisica_actual_valida_no_abre_cierre_rc3(self):
        with entorno_materializacion() as m:
            mat = materializar(m, self.e)
            a = admitir_exportacion_tecnica(s9(self.e, materializacion=mat, exigir_integridad_fisica=True))
            r = self.evaluar(admision=a)
            self.assertIs(r.verificacion_actual.estado_local, EstadoLocal.INTEGRO)
            self.assertEqual(r.verificacion_actual.sha256_fisico, hashlib.sha256(self.e.resultado_nativo.encode()).hexdigest())
            self.assertIs(r.decision, DD.NO_ADMISIBLE)
            self.assertIsNot(r.verificacion_actual, a.verificacion_fisica)

    def test_archivo_alterado_despues_de_admision_se_relee(self):
        with entorno_materializacion() as m:
            mat = materializar(m, self.e)
            a = admitir_exportacion_tecnica(s9(self.e, materializacion=mat, exigir_integridad_fisica=True))
            ruta = m.raiz / mat.referencia.nombre
            b = ruta.read_bytes()
            ruta.write_bytes(b"!"+b[1:])
            r = self.evaluar(admision=a)
            self.assertIs(r.decision, DD.NO_SATISFECHA)
            self.assertIs(r.verificacion_actual.estado_local, EstadoLocal.INCONSISTENTE)

    def test_materializacion_ajena_no_se_abre(self):
        e2, _ = nativos(project_id="proyecto-RC11-B")
        with entorno_materializacion() as m:
            mat = materializar(m, e2)
            a = admitir_exportacion_tecnica(s9(self.e, materializacion=mat))
            with patch("spica.artefactos.admision_exportacion.verificar_fisicamente", side_effect=AssertionError("ajeno")):
                r = self.evaluar(admision=a, politica=replace(self.p, exigir_integridad_fisica=True))
            self.assertIs(r.decision, DD.NO_SATISFECHA)
            self.assertIsNone(r.verificacion_actual)

    def test_ausencia_fisica_comprobada_se_distingue_de_no_disponible(self):
        with entorno_materializacion() as m:
            mat = materializar(m, self.e)
            a = admitir_exportacion_tecnica(s9(self.e, materializacion=mat, exigir_integridad_fisica=True))
            m._archivos.quitar_propio(mat.referencia.nombre)
            r = self.evaluar(admision=a)
            self.assertIs(r.verificacion_actual.estado_local, EstadoLocal.AUSENTE)
            self.assertIs(r.decision, DD.NO_SATISFECHA)

    def test_historia_rc10_verificada_sigue_sin_admision_actual(self):
        with entorno_conservacion() as c:
            r = dictaminar(historico(c, self.e, self.a))
            self.assertTrue(r.recuperacion.recuperada_en_alcance)
            self.assertTrue(r.recuperacion.expediente.hechos.admision_rc9_comprobada)
            self.assertFalse(r.admision.comprobacion_local_coherente)
            self.assertFalse(r.cierre.evidencia.captura_local_coherente)
            self.assertIs(r.decision, DD.NO_ADMISIBLE)
            self.assertIsNone(r.verificacion_actual)

    def test_historia_insuficiente_no_se_promueve(self):
        with entorno_conservacion() as c:
            r = dictaminar(historico(c, self.e, None))
            self.assertIs(r.decision, DD.PENDIENTE)
            self.assertFalse(r.satisfecha)

    def test_historia_de_fallo_real_conserva_el_incumplimiento(self):
        with patch("spica.artefactos.cierre_exportacion.exportar_resultado_json", side_effect=ValueError("fixture")):
            e = ejecutar_exportacion_tecnica(solicitud_exportacion())
        a = admitir_exportacion_tecnica(s9(e))
        with entorno_conservacion() as c:
            r = dictaminar(historico(c, e, a))
            self.assertTrue(r.recuperacion.recuperada_en_alcance)
            self.assertIs(r.cierre.evidencia.operacion_observada.estado, S.FALLIDA)
            self.assertIs(r.decision, DD.NO_SATISFECHA)

    def test_dos_historiales_independientes_y_cruce_rechazado(self):
        e2, a2 = nativos(project_id="proyecto-RC11-B")
        with entorno_conservacion() as c1, entorno_conservacion() as c2:
            s1, s2 = historico(c1, self.e, self.a), historico(c2, e2, a2)
            r1, r2 = dictaminar(s1), dictaminar(s2)
            self.assertIs(r1.decision, DD.NO_ADMISIBLE)
            self.assertIs(r2.decision, DD.NO_ADMISIBLE)
            self.assertEqual(r1.cierre.evidencia.resultado_nativo, r2.cierre.evidencia.resultado_nativo)
            self.assertNotEqual(s1.control_historico.project_id, s2.control_historico.project_id)
            self.assertIs(dictaminar(replace(s2, politica=self.p)).decision, DD.NO_SATISFECHA)

    def test_contenedor_corrupto_y_control_hash_incorrecto(self):
        for caso in ("bytes", "control"):
            with self.subTest(caso=caso), entorno_conservacion() as c:
                s = historico(c, self.e, self.a)
                if caso == "bytes":
                    ruta = c.raiz / "datos-000.bin"
                    b = ruta.read_bytes()
                    ruta.write_bytes(b"!"+b[1:])
                else:
                    control = replace(s.control_historico, generacion=replace(
                        s.control_historico.generacion, manifiesto_sha256="0"*64))
                    s = replace(s, control_historico=control)
                r = dictaminar(s)
                self.assertIs(r.decision, DD.NO_SATISFECHA)
                self.assertIsNone(r.recuperacion.expediente)

    def test_historia_incompleta_no_se_repara(self):
        with entorno_conservacion() as c:
            s = historico(c, self.e, self.a)
            c._fs.quitar_propio("cierre.json")
            r = dictaminar(s)
            self.assertIs(r.decision, DD.PENDIENTE)
            self.assertFalse((c.raiz / "cierre.json").exists())

    def test_referencias_externas_no_disponibles_no_equivalen_a_ausencia(self):
        with entorno_conservacion() as c:
            s = historico(c, self.e, self.a)
            s = replace(s, politica=replace(self.p, exigir_externos_disponibles=True))
            r = dictaminar(s)
            self.assertIs(r.decision, DD.PENDIENTE)
            self.assertTrue(r.recuperacion.externos_actuales)
            self.assertTrue(all(v is EstadoLocal.NO_DISPONIBLE for _, v in r.recuperacion.externos_actuales))

    def test_fisica_historica_no_se_reutiliza_como_actual(self):
        with entorno_materializacion() as m:
            mat = materializar(m, self.e)
            a = admitir_exportacion_tecnica(s9(self.e, materializacion=mat, exigir_integridad_fisica=True))
            with entorno_conservacion() as c:
                s = historico(c, self.e, a)
                with patch("spica.artefactos.admision_exportacion.verificar_fisicamente", side_effect=AssertionError("historia")):
                    r = dictaminar(s)
                self.assertIs(r.decision, DD.PENDIENTE)
                self.assertIsNone(r.verificacion_actual)

    def test_errores_reales_y_cancelacion_no_son_cierre(self):
        for error in (ValueError("fallo-fixture"), KeyboardInterrupt()):
            with self.subTest(tipo=type(error).__name__), patch(
                    "spica.artefactos.cierre_exportacion.exportar_resultado_json", side_effect=error):
                e = ejecutar_exportacion_tecnica(solicitud_exportacion())
            a = admitir_exportacion_tecnica(s9(e))
            r = dictaminar(Solicitud(politica(e), e, a))
            self.assertIs(r.decision, DD.NO_SATISFECHA)
            self.assertIn(e.operacion_observada.estado, (S.FALLIDA, S.CANCELADA))

    def test_parcial_real_no_se_promueve(self):
        evento = Event()
        def exportar(*args, **kw):
            b = exportar_resultado_json(*args, **kw)
            evento.set()
            return b
        with patch("spica.artefactos.cierre_exportacion.exportar_resultado_json", side_effect=exportar):
            e = ejecutar_exportacion_tecnica(solicitud_exportacion(), cancelacion=evento)
        a = admitir_exportacion_tecnica(s9(e))
        r = dictaminar(Solicitud(politica(e), e, a))
        self.assertIs(e.operacion_observada.estado, S.PARCIAL)
        self.assertIs(r.decision, DD.NO_SATISFECHA)

    def test_concluida_solo_declarada_no_se_promueve(self):
        e, a = nativos(estado=S.CONCLUIDA)
        r = dictaminar(Solicitud(politica(e), e, a))
        self.assertFalse(e.productor_invocado)
        self.assertFalse(r.satisfecha)
        self.assertIn(r.decision, (DD.PENDIENTE, DD.NO_SATISFECHA))

    def test_linaje_contradictorio_no_se_omite(self):
        inv = self.p.inventario
        prod = replace(inv.producciones[0], entradas=(self.p.artefacto,))
        p = replace(self.p, inventario=replace(inv, producciones=(prod,)))
        r = self.evaluar(politica=p)
        self.assertIs(r.decision, DD.NO_SATISFECHA)
        self.assertIs(r.linaje.estado_estructural, E.INCOMPATIBLE)

    def test_cierre_qa_genuino_no_es_cierre_de_exportacion(self):
        qa = qa_real()
        c = self.p.inventario.composiciones[0]
        adulterado = replace(c, operaciones=(replace(c.operaciones[0], cierre_qa=qa.cierre_qa), c.operaciones[1]))
        p = replace(self.p, inventario=replace(self.p.inventario, composiciones=(adulterado,)))
        r = self.evaluar(politica=p)
        self.assertIs(r.decision, DD.NO_SATISFECHA)
        self.assertIsNotNone(qa.cierre_qa)

    def test_rc3_conserva_diagnosticos_e_inhabilitacion_originales(self):
        c = self.p.inventario.composiciones[0]
        antes = inspeccionar_composicion(c)
        r = self.evaluar()
        self.assertEqual(antes, r.linaje.composiciones[0])
        self.assertNotIn("consumidor", antes.habilitadas_declarativamente)
        self.assertIn("dependencia_sin_cierre_tecnico_compatible_aportado",
            {d.codigo for x in antes.operaciones for d in x.diagnosticos})
        self.assertEqual(inspeccionar_composicion(c), antes)

    def test_rc7_no_admite_portador_historico_como_inventario_original(self):
        with entorno_conservacion() as c:
            r = dictaminar(historico(c, self.e, self.a))
            s7 = SolicitudIntegracion(r.recuperacion.generacion,
                self.p.inventario.composiciones[0], (), USO_CONSUMIR)
            r7 = inspeccionar_integracion(s7)
            self.assertNotIn("consumidor", r7.habilitadas_declarativamente)
            self.assertIsNot(r7.estado_estructural, E.APTO_ESTRUCTURALMENTE)
            self.assertFalse(r7.autoriza_operacion)

    def test_estados_descriptores_y_resultados_nativos_no_se_reescriben(self):
        antes = self.e.solicitud.inventario
        original = exportar_resultado_json(self.e.solicitud.entrada_qa.resultado,
            self.e.solicitud.entrada_qa.contexto_exportacion)
        self.evaluar()
        self.assertIs(self.p.inventario, antes)
        self.assertIs(antes.producciones[0].operacion.estado, S.INICIADA)
        self.assertIs(antes.composiciones[0].operaciones[1].contexto.estado, S.DECLARADA)
        self.assertEqual(self.e.resultado_nativo, original)

    def test_determinismo_y_flags_inmutables_sin_satisfecha_fabricable(self):
        r = self.evaluar()
        self.assertEqual(r, self.evaluar())
        self.assertIs(replace(r, diagnosticos=()).decision, DD.NO_ADMISIBLE)
        for atributo in ("habilitacion_rc3_rc7", "autoriza_operacion", "ejecucion_automatica",
                "autenticidad_acreditada", "validacion_cientifica"):
            self.assertFalse(getattr(r, atributo))
            with self.assertRaises(FrozenInstanceError):
                setattr(r, atributo, True)
        with self.assertRaises(TypeError):
            bool(r)

    def test_contratos_y_fuentes_invalidas_se_rechazan(self):
        for cambios in (dict(version_contrato="9.0.0"), dict(exigir_integridad_fisica=1),
                dict(dependencia="exportar->consumidor")):
            with self.subTest(campos=tuple(cambios)), self.assertRaises((TypeError, ValueError)):
                replace(self.p, **cambios)
        with self.assertRaises(TypeError):
            dictaminar(self.p)
        with self.assertRaises(ValueError):
            Solicitud(self.p, raiz_historica=Path("no-se-abre"))
        with entorno_conservacion() as c:
            s = historico(c, self.e, self.a)
            with self.assertRaises(ValueError):
                replace(s, evidencia=self.e)

    def test_temporales_del_piloto_se_limpian_y_no_se_reinicializan(self):
        with entorno_conservacion() as c:
            raiz = c.raiz
            s = historico(c, self.e, self.a)
            antes = {p.name: p.read_bytes() for p in raiz.iterdir() if p.is_file()}
            r = dictaminar(s)
            self.assertIs(r.decision, DD.NO_ADMISIBLE)
            self.assertEqual(antes, {p.name: p.read_bytes() for p in raiz.iterdir() if p.is_file()})
        self.assertFalse(raiz.exists())

    def test_barrera_de_efectos_en_proceso_independiente(self):
        programa = r'''
import os, sys
def barrera(evento, args):
    if evento.startswith('socket.') or evento == 'sqlite3.connect':
        raise RuntimeError('efecto_prohibido_rc11')
    if evento == 'open':
        p, modo, flags = args
        if 'spica_datos' in str(p).casefold(): raise RuntimeError('operativo_prohibido')
        if (isinstance(modo,str) and any(c in modo for c in 'wax+')) or flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):
            raise RuntimeError('escritura_prohibida_rc11')
    if evento in ('os.mkdir','os.remove','os.rmdir','os.rename','os.link','os.symlink','os.chmod'):
        raise RuntimeError('mutacion_prohibida_rc11')
sys.addaudithook(barrera)
from test_dependencia_noqa_rc11 import nativos, politica, Solicitud, dictaminar, DD
e,a = nativos()
r = dictaminar(Solicitud(politica(e),e,a))
assert r.decision is DD.NO_ADMISIBLE and not r.autoriza_operacion
print('RC11_SIN_EFECTOS')
'''
        p = subprocess.run((sys.executable, "-B", "-c", programa), capture_output=True, text=True,
            env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"), timeout=45)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout.strip(), "RC11_SIN_EFECTOS")


if __name__ == "__main__":
    unittest.main()
