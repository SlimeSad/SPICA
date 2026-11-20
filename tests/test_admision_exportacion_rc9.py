"""RC9: productor y consumidor nativos, adversarios y TEMP sintético propio."""

from dataclasses import FrozenInstanceError, replace
import hashlib
import json
from pathlib import Path
import sys
from threading import Event
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from spica.adquisicion.readquisicion.modelos import EstadoLocal
from spica.artefactos.admision_exportacion import (
    CONSUMIDOR, USO_CONSUMIR, SolicitudAdmisionExportacion,
    admitir_exportacion_tecnica,
)
from spica.artefactos.cierre_exportacion import ejecutar_exportacion_tecnica
from spica.artefactos.conservacion import (
    UnidadConservacion, entorno_conservacion, recuperar_generacion, EstadoRecuperacion,
)
from spica.artefactos.coordinacion import SolicitudIntegracion, VinculoEntradaRecuperada, inspeccionar_integracion
from spica.artefactos.materializacion import (
    SolicitudMaterializacion, entorno_materializacion, verificar_fisicamente,
)
from spica.calidad.consumo import consumir_exportaciones, EstadoConsumoQA, LimitesConsumoQA
from spica.calidad.exportacion import exportar_resultado_json
from spica.calidad.restricciones import RestriccionQA, TipoRestriccionQA as TR
from spica.contextos import EstadoOperacion as S
from spica.interoperabilidad.modelos import EstadoAptitud as E
# Solo fabricantes; no importar clases TestCase para duplicar descubrimiento.
from test_cierre_exportacion_rc8 import solicitud as solicitud_rc8
from test_contextos_rc1 import proyecto, resultado


def solicitud(e, **kw):
    s = e.solicitud
    salida = next(a for a in s.inventario.artefactos if a.referencia == s.salida)
    d = dict(contenido=e.resultado_nativo, evidencia=e, proyecto=s.entrada_qa.operacion.proyecto,
        operacion_productora_id=s.operacion_id, entrada_resultado_id=s.entrada_qa.referencia_resultado,
        artefacto=s.salida, contenido_id=salida.contenido_id)
    d.update(kw)
    return SolicitudAdmisionExportacion(**d)


def codigos(r):
    return {d.codigo for d in r.diagnosticos}


def materializar(m, e):
    b = e.resultado_nativo.encode("utf-8")
    return m.materializar_sintetico(
        SolicitudMaterializacion(e.solicitud.inventario, e.solicitud.salida, len(b), e.sha256_bytes),
        (b[:29], b[29:]),
    )


class AdmisionExportacionRC9Tests(unittest.TestCase):
    def setUp(self):
        self.e = ejecutar_exportacion_tecnica(solicitud_rc8())

    def test_productor_y_consumidor_reales_en_piloto(self):
        with patch("spica.artefactos.cierre_exportacion.exportar_resultado_json", wraps=exportar_resultado_json) as p:
            e = ejecutar_exportacion_tecnica(solicitud_rc8())
        p.assert_called_once()
        with patch("spica.artefactos.admision_exportacion.consumir_exportaciones", wraps=consumir_exportaciones) as c:
            r = admitir_exportacion_tecnica(solicitud(e))
        c.assert_called_once_with(e.resultado_nativo, limites=r.solicitud.limites)
        self.assertTrue(r.admisible_para_consumo_tecnico, codigos(r))
        self.assertIs(r.estado_estructural, E.APTO_ESTRUCTURALMENTE)
        self.assertTrue(r.comprobacion_local_coherente)
        self.assertTrue(r.cierre.cierre_tecnico_comprobado)
        self.assertEqual(r.consumo.estado, EstadoConsumoQA.CONTRATO_VALIDO_EN_ALCANCE)
        self.assertEqual((e.size_bytes, e.sha256_bytes), (3852,
            "8a9ed4f6977f1c25c2d230589666947fcca6bf50d7c3b2fff4ecc9a4c606eb07"))

    def test_bytes_utf8_coincidentes_son_admitidos(self):
        r = admitir_exportacion_tecnica(solicitud(self.e, contenido=self.e.resultado_nativo.encode()))
        self.assertTrue(r.admisible_para_consumo_tecnico)
        self.assertIsNone(r.verificacion_fisica)

    def test_json_invalido_y_raices_no_soportadas(self):
        for v in ("{incompleto", "[]", "null", b"\xff", "{}"):
            with self.subTest(v=v):
                r = admitir_exportacion_tecnica(solicitud(self.e, contenido=v))
                self.assertIs(r.estado_estructural, E.INCOMPATIBLE)
                self.assertIn("documento_rechazado_por_consumidor", codigos(r))

    def test_version_desconocida_del_json(self):
        d = json.loads(self.e.resultado_nativo)
        d["version_esquema"] = "99.0.0"
        r = admitir_exportacion_tecnica(solicitud(self.e, contenido=json.dumps(d)))
        self.assertIs(r.estado_estructural, E.INCOMPATIBLE)

    def test_version_consumidor_y_su_identidad(self):
        for kw in (dict(consumidor_id="otro.consumidor"), dict(version_consumidor="99.0.0")):
            with self.subTest(kw=kw):
                r = admitir_exportacion_tecnica(solicitud(self.e, **kw))
                self.assertIn("consumidor_o_version_no_admitidos", codigos(r))
                self.assertIs(r.estado_estructural, E.INCOMPATIBLE)

    def test_version_productor_y_contrato_rc8(self):
        for kw in (dict(productor_id="otro.productor"), dict(version_productor="99.0.0"),
                   dict(version_contrato="99.0.0")):
            with self.subTest(kw=kw):
                r = admitir_exportacion_tecnica(solicitud(self.e, evidencia=replace(self.e, **kw)))
                self.assertIs(r.estado_estructural, E.INCOMPATIBLE)
                self.assertIn("version_o_productor_de_evidencia_incompatible", codigos(r))

    def test_proyecto_y_contexto_esperados(self):
        p = self.e.operacion_observada.proyecto
        for otro in (proyecto("otro", p.contexto_id), replace(p, contexto_id="otro-contexto")):
            with self.subTest(otro=otro.project_id):
                r = admitir_exportacion_tecnica(solicitud(self.e, proyecto=otro))
                self.assertIs(r.estado_estructural, E.INCOMPATIBLE)
                self.assertIn("proyecto_esperado_no_corresponde", codigos(r))

    def test_operacion_entrada_y_contenido_esperados(self):
        for kw, codigo in ((dict(operacion_productora_id="otra"), "operacion_productora_no_corresponde"),
            (dict(entrada_resultado_id="otra"), "entrada_resultado_no_corresponde"),
            (dict(contenido_id="otro"), "identidad_contenido_no_corresponde")):
            with self.subTest(kw=kw):
                r = admitir_exportacion_tecnica(solicitud(self.e, **kw))
                self.assertIs(r.estado_estructural, E.INCOMPATIBLE)
                self.assertIn(codigo, codigos(r))

    def test_artefacto_y_revision_esperados(self):
        for kw in (dict(object_id="otro-objeto"), dict(revision="r2")):
            with self.subTest(kw=kw):
                r = admitir_exportacion_tecnica(solicitud(self.e, artefacto=replace(self.e.solicitud.salida, **kw)))
                self.assertIn("artefacto_o_revision_no_corresponde", codigos(r))
                self.assertIs(r.estado_estructural, E.INCOMPATIBLE)

    def test_resultado_nativo_de_otra_fila_no_se_asocia(self):
        s = self.e.solicitud
        otro = resultado(s.entrada_qa.operacion.entradas[0], numero=2)
        texto = exportar_resultado_json(otro, s.entrada_qa.contexto_exportacion)
        r = admitir_exportacion_tecnica(solicitud(self.e, contenido=texto))
        self.assertEqual(r.consumo.estado, EstadoConsumoQA.CONTRATO_VALIDO_EN_ALCANCE)
        self.assertIs(r.estado_estructural, E.INCOMPATIBLE)
        self.assertIn("contenido_distinto_de_captura_rc8", codigos(r))

    def test_sin_cierre_rc8_no_basta_json_valido(self):
        r = admitir_exportacion_tecnica(solicitud(self.e, evidencia=None))
        self.assertIs(r.estado_estructural, E.PENDIENTE_DE_EVIDENCIA)
        self.assertEqual(r.consumo.estado, EstadoConsumoQA.CONTRATO_VALIDO_EN_ALCANCE)
        self.assertFalse(r.admisible_para_consumo_tecnico)
        self.assertTrue(r.consumo.documentos_aceptados)  # Conservan restricciones nativas.

    def test_captura_externa_coherente_no_es_ejecucion_independiente(self):
        r = admitir_exportacion_tecnica(solicitud(self.e, evidencia=replace(self.e)))
        self.assertIs(r.estado_estructural, E.PENDIENTE_DE_EVIDENCIA)
        self.assertIn("captura_aportada_no_observada_o_alterada", codigos(r))

    def test_sin_invocacion_declarada_queda_pendiente(self):
        r = admitir_exportacion_tecnica(solicitud(self.e, evidencia=replace(self.e, productor_invocado=False)))
        self.assertIs(r.estado_estructural, E.PENDIENTE_DE_EVIDENCIA)

    def test_contenido_ausente_no_equivale_a_json_erroneo(self):
        r = admitir_exportacion_tecnica(solicitud(self.e, contenido=None))
        self.assertIsNone(r.consumo)
        self.assertIs(r.estado_estructural, E.PENDIENTE_DE_EVIDENCIA)
        self.assertIn("contenido_no_aportado", codigos(r))

    def test_bytes_con_espacios_distintos_no_son_salida_capturada(self):
        r = admitir_exportacion_tecnica(solicitud(self.e, contenido=self.e.resultado_nativo + " "))
        self.assertEqual(r.consumo.estado, EstadoConsumoQA.CONTRATO_VALIDO_EN_ALCANCE)
        self.assertIs(r.estado_estructural, E.INCOMPATIBLE)

    def test_hash_y_tamano_contradictorios_en_captura(self):
        for kw in (dict(sha256_bytes="0" * 64), dict(size_bytes=1)):
            with self.subTest(kw=kw):
                r = admitir_exportacion_tecnica(solicitud(self.e, evidencia=replace(self.e, **kw)))
                self.assertIs(r.estado_estructural, E.INCOMPATIBLE)
                self.assertIn("huella_o_tamano_de_salida_contradictorios", codigos(r))

    def test_unicode_invalido_de_captura_se_diagnostica(self):
        e = replace(self.e, resultado_nativo="\ud800")
        r = admitir_exportacion_tecnica(solicitud(self.e, evidencia=e))
        self.assertIs(r.estado_estructural, E.INCOMPATIBLE)

    def test_presupuesto_insuficiente_no_es_rechazo_de_formato(self):
        r = admitir_exportacion_tecnica(solicitud(self.e, limites=LimitesConsumoQA(max_bytes_documento=100)))
        self.assertIs(r.estado_estructural, E.PENDIENTE_DE_EVIDENCIA)
        self.assertIn("consumo_no_completado", codigos(r))

    def test_restriccion_para_consumir_no_impide_exportar_pero_rechaza_admision(self):
        b = RestriccionQA("bloqueo-consumo", TR.BLOQUEO_USO_DEL_RESULTADO, (USO_CONSUMIR,), "Fixture RC9")
        e = ejecutar_exportacion_tecnica(solicitud_rc8(bloqueo=b))
        self.assertTrue(e.productor_invocado)
        r = admitir_exportacion_tecnica(solicitud(e))
        self.assertTrue(r.cierre.cierre_tecnico_comprobado)
        self.assertIn(b, r.restricciones)
        self.assertIn("restriccion_impide_consumo_rc9", codigos(r))
        self.assertIs(r.estado_estructural, E.INCOMPATIBLE)

    def test_restricciones_cientificas_heredadas_se_conservan(self):
        b = RestriccionQA("heredada-rc9", TR.BLOQUEO_USO_DEL_RESULTADO, ("acreditar_ciencia",), "Fixture RC9")
        e = ejecutar_exportacion_tecnica(solicitud_rc8(bloqueo=b))
        r = admitir_exportacion_tecnica(solicitud(e))
        self.assertTrue(r.admisible_para_consumo_tecnico)
        self.assertIn(b, r.restricciones)
        self.assertTrue(set(e.solicitud.entrada_qa.restricciones) <= set(r.restricciones))

    def test_restriccion_conocida_se_conserva_sin_captura(self):
        b = RestriccionQA("bloqueo-sin-captura", TR.BLOQUEO_USO_DEL_RESULTADO, (USO_CONSUMIR,), "Fixture RC9")
        e = ejecutar_exportacion_tecnica(solicitud_rc8(bloqueo=b))
        r = admitir_exportacion_tecnica(solicitud(e, evidencia=None))
        self.assertIs(r.estado_estructural, E.INCOMPATIBLE)
        self.assertIn(b, r.restricciones)
        self.assertIn("restriccion_impide_consumo_rc9", codigos(r))

    def test_finalidad_distinta_no_amplia_la_politica(self):
        r = admitir_exportacion_tecnica(solicitud(self.e, finalidad="acreditar_aptitud_cientifica"))
        self.assertIs(r.estado_estructural, E.INCOMPATIBLE)
        self.assertIn("finalidad_fuera_de_politica_rc9", codigos(r))

    def test_resultado_parcial_no_se_promueve(self):
        evento = Event()
        def producir(*a, **kw):
            t = exportar_resultado_json(*a, **kw)
            evento.set()
            return t
        with patch("spica.artefactos.cierre_exportacion.exportar_resultado_json", side_effect=producir):
            e = ejecutar_exportacion_tecnica(solicitud_rc8(), cancelacion=evento)
        r = admitir_exportacion_tecnica(solicitud(e))
        self.assertEqual(e.operacion_observada.estado, S.PARCIAL)
        self.assertIs(r.estado_estructural, E.PENDIENTE_DE_EVIDENCIA)
        self.assertFalse(r.admisible_para_consumo_tecnico)
        self.assertEqual(r.consumo.estado, EstadoConsumoQA.CONTRATO_VALIDO_EN_ALCANCE)

    def test_productor_fallido_sin_resultado(self):
        with patch("spica.artefactos.cierre_exportacion.exportar_resultado_json", side_effect=OSError("secreto")):
            e = ejecutar_exportacion_tecnica(solicitud_rc8())
        r = admitir_exportacion_tecnica(solicitud(e))
        self.assertEqual(e.operacion_observada.estado, S.FALLIDA)
        self.assertFalse(r.admisible_para_consumo_tecnico)
        self.assertNotIn("secreto", repr(r.diagnosticos))

    def test_operacion_cancelada_sin_exportar(self):
        evento = Event()
        evento.set()
        e = ejecutar_exportacion_tecnica(solicitud_rc8(), cancelacion=evento)
        r = admitir_exportacion_tecnica(solicitud(e))
        self.assertEqual(e.operacion_observada.estado, S.CANCELADA)
        self.assertIs(r.estado_estructural, E.PENDIENTE_DE_EVIDENCIA)

    def test_dos_proyectos_con_mismos_bytes_no_comparten_identidad(self):
        a = ejecutar_exportacion_tecnica(solicitud_rc8(project_id="RC9-A", contexto_id="colision-fixture"))
        b = ejecutar_exportacion_tecnica(solicitud_rc8(project_id="RC9-B", contexto_id="colision-fixture"))
        self.assertEqual(a.resultado_nativo, b.resultado_nativo)
        ra = admitir_exportacion_tecnica(solicitud(a))
        rb = admitir_exportacion_tecnica(solicitud(b))
        self.assertTrue(ra.admisible_para_consumo_tecnico)
        self.assertTrue(rb.admisible_para_consumo_tecnico)
        self.assertNotEqual(ra.solicitud.proyecto.project_id, rb.solicitud.proyecto.project_id)
        r = admitir_exportacion_tecnica(replace(solicitud(a), evidencia=b))
        self.assertIs(r.estado_estructural, E.INCOMPATIBLE)

    def test_integridad_fisica_actual_y_bytes_coincidentes_sin_cierre_qa(self):
        e = self.e
        with entorno_materializacion() as m:
            r5 = materializar(m, e)
            with patch("spica.artefactos.admision_exportacion.verificar_fisicamente", wraps=verificar_fisicamente) as leer:
                r = admitir_exportacion_tecnica(solicitud(e, exigir_integridad_fisica=True, materializacion=r5))
            leer.assert_called_once_with(r5.solicitud, r5.referencia)
            self.assertTrue(r.admisible_para_consumo_tecnico, codigos(r))
            self.assertEqual(r.verificacion_fisica.estado_local, EstadoLocal.INTEGRO)
            self.assertEqual(r.verificacion_fisica.sha256_fisico, hashlib.sha256(e.resultado_nativo.encode()).hexdigest())
            self.assertIsNot(r.verificacion_fisica, r5.verificacion)
            self.assertEqual((m.raiz / r5.referencia.nombre).read_bytes(), e.resultado_nativo.encode())
            self.assertTrue(all(n.nodo.cierre_qa is None for n in r.cierre.coordinacion_rc3.operaciones))
            self.assertFalse(r.validacion_cientifica_realizada)
        self.assertFalse(m.raiz.exists())

    def test_exigencia_fisica_sin_referencia_pendiente(self):
        r = admitir_exportacion_tecnica(solicitud(self.e, exigir_integridad_fisica=True))
        self.assertIs(r.estado_estructural, E.PENDIENTE_DE_EVIDENCIA)
        self.assertIn("referencia_fisica_no_disponible", codigos(r))

    def test_archivo_ausente_no_reutiliza_integridad_historica(self):
        with entorno_materializacion() as m:
            r5 = materializar(m, self.e)
            self.assertEqual(r5.verificacion.estado_local, EstadoLocal.INTEGRO)
            (m.raiz / r5.referencia.nombre).unlink()
            r = admitir_exportacion_tecnica(solicitud(self.e, exigir_integridad_fisica=True, materializacion=r5))
            self.assertEqual(r.verificacion_fisica.estado_local, EstadoLocal.AUSENTE)
            self.assertIs(r.estado_estructural, E.PENDIENTE_DE_EVIDENCIA)

    def test_corrupcion_fisica_es_contradiccion(self):
        with entorno_materializacion() as m:
            r5 = materializar(m, self.e)
            (m.raiz / r5.referencia.nombre).write_bytes(b"X" * self.e.size_bytes)
            r = admitir_exportacion_tecnica(solicitud(self.e, exigir_integridad_fisica=True, materializacion=r5))
            self.assertEqual(r.verificacion_fisica.estado_local, EstadoLocal.INCONSISTENTE)
            self.assertIs(r.estado_estructural, E.INCOMPATIBLE)

    def test_materializacion_historica_parcial_no_es_cierre(self):
        with entorno_materializacion() as m:
            r5 = replace(materializar(m, self.e), estado_tecnico=S.PARCIAL)
            with patch("spica.artefactos.admision_exportacion.verificar_fisicamente") as p:
                r = admitir_exportacion_tecnica(solicitud(self.e, exigir_integridad_fisica=True, materializacion=r5))
            p.assert_not_called()
            self.assertIs(r.estado_estructural, E.PENDIENTE_DE_EVIDENCIA)

    def test_referencia_fisica_de_otro_proyecto_no_se_lee(self):
        otro = ejecutar_exportacion_tecnica(solicitud_rc8(project_id="RC9-otro"))
        with entorno_materializacion() as m:
            r5 = materializar(m, otro)
            with patch("spica.artefactos.admision_exportacion.verificar_fisicamente") as p:
                r = admitir_exportacion_tecnica(solicitud(self.e, exigir_integridad_fisica=True, materializacion=r5))
            p.assert_not_called()
            self.assertIs(r.estado_estructural, E.INCOMPATIBLE)

    def test_no_hay_relectura_implicita_sin_exigencia_fisica(self):
        with entorno_materializacion() as m:
            r5 = materializar(m, self.e)
            with patch("spica.artefactos.admision_exportacion.verificar_fisicamente", side_effect=AssertionError("no leer")):
                r = admitir_exportacion_tecnica(solicitud(self.e, materializacion=r5))
            self.assertTrue(r.admisible_para_consumo_tecnico)
            self.assertIsNone(r.verificacion_fisica)

    def test_rc6_recupera_bytes_no_cierre_rc8_ni_dependencia_rc7(self):
        e = self.e
        s = e.solicitud
        with entorno_materializacion() as m, entorno_conservacion() as c:
            r5 = materializar(m, e)
            externo = s.inventario.artefactos[0].referencia
            guardado = c.conservar(UnidadConservacion(s.inventario, (r5,), (externo,)))
            r6 = recuperar_generacion(c.raiz, guardado.control)
            self.assertEqual(r6.estado, EstadoRecuperacion.VERIFICADA)
            externo6 = next(a for a in r6.contenidos if a.artefacto == externo)
            self.assertIs(externo6.estado_actual, EstadoLocal.NO_DISPONIBLE)
            copia = next(a for a in r6.contenidos if a.artefacto == s.salida)
            b = (c.raiz / copia.relativa).read_bytes()
            pendiente = admitir_exportacion_tecnica(solicitud(e, contenido=b, evidencia=None))
            self.assertIs(pendiente.estado_estructural, E.PENDIENTE_DE_EVIDENCIA)
            self.assertTrue(admitir_exportacion_tecnica(solicitud(e, contenido=b)).admisible_para_consumo_tecnico)
            comp = r6.unidad.inventario.composiciones[0]
            refs = {a.entrada_perfil.entrada.entrada_id: a.referencia for a in r6.unidad.inventario.artefactos}
            vs = tuple(VinculoEntradaRecuperada(n.contexto.operacion_id, en.entrada_id, refs[en.entrada_id])
                for n in comp.operaciones for en in n.contexto.entradas)
            rc7 = inspeccionar_integracion(SolicitudIntegracion(r6, comp, vs, USO_CONSUMIR))
            self.assertNotIn("consumidor", rc7.habilitadas_declarativamente)
            self.assertTrue(all(n.cierre_qa is None for n in comp.operaciones))
        self.assertFalse(m.raiz.exists())
        self.assertFalse(c.raiz.exists())

    def test_dependencia_rc3_no_habilitada_y_estado_historico_intacto(self):
        e = self.e
        op = e.solicitud.inventario.producciones[0].operacion
        r = admitir_exportacion_tecnica(solicitud(e))
        self.assertTrue(r.admisible_para_consumo_tecnico)
        self.assertNotIn("consumidor", r.cierre.coordinacion_rc3.habilitadas_declarativamente)
        self.assertEqual(op.estado, S.INICIADA)
        self.assertEqual(e.operacion_observada.estado, S.CONCLUIDA)
        self.assertFalse(r.habilitacion_rc3_concedida)

    def test_cierre_qa_genuino_sigue_separado_de_la_exportacion(self):
        from test_coordinacion_rc3 import qa_real, composicion
        from spica.coordinacion import inspeccionar_composicion
        # Evaluador nativo sobre CSV sintético TEMP; InformeQA no construido a mano.
        qa = qa_real(self.e.solicitud.entrada_qa.operacion.entradas[0])
        previo = inspeccionar_composicion(composicion((qa,)))
        self.assertTrue(previo.operaciones[0].cierre_qa_coherente_completo)
        s = self.e.solicitud
        inv = s.inventario
        a, b = inv.artefactos
        v = qa.cierre_qa.vinculos[0]
        en = replace(a.entrada_perfil.entrada, entrada_id=v.referencia_resultado)
        a = replace(a, entrada_perfil=replace(a.entrada_perfil, entrada=en))
        prod = inv.producciones[0]
        op = replace(prod.operacion, entradas=(en,))
        comp = inv.composiciones[0]
        comp = replace(comp, operaciones=(replace(comp.operaciones[0], contexto=op), comp.operaciones[1]))
        inv = replace(inv, artefactos=(a, b), producciones=(replace(prod, operacion=op),), composiciones=(comp,))
        e = ejecutar_exportacion_tecnica(replace(s, inventario=inv, entrada_qa=v))
        r = admitir_exportacion_tecnica(solicitud(e))
        self.assertTrue(r.admisible_para_consumo_tecnico, codigos(r))
        self.assertEqual(qa.cierre_qa, previo.operaciones[0].nodo.cierre_qa)
        self.assertTrue(all(n.nodo.cierre_qa is None for n in r.cierre.coordinacion_rc3.operaciones))
        self.assertFalse(r.habilitacion_rc3_concedida)

    def test_conflictos_de_restricciones_conservan_ambas_variantes(self):
        s = self.e.solicitud
        inv = s.inventario
        original = s.entrada_qa.restricciones[0]
        contradictoria = replace(original, tipo=TR.BLOQUEO_USO_DEL_RESULTADO,
            operaciones=(USO_CONSUMIR,), motivo="Fixture: variante contradictoria")
        prod = inv.producciones[0]
        op = replace(prod.operacion, restricciones_adicionales=(contradictoria,))
        comp = inv.composiciones[0]
        comp = replace(comp, operaciones=(replace(comp.operaciones[0], contexto=op), comp.operaciones[1]))
        inv = replace(inv, producciones=(replace(prod, operacion=op),), composiciones=(comp,))
        e = ejecutar_exportacion_tecnica(replace(s, inventario=inv))
        r = admitir_exportacion_tecnica(solicitud(e))
        self.assertFalse(e.productor_invocado)
        self.assertIs(r.estado_estructural, E.INCOMPATIBLE)
        self.assertIn(original, r.restricciones)
        self.assertIn(contradictoria, r.restricciones)
        self.assertIn("restricciones_recuperadas_no_unificables", codigos(r))

    def test_informe_aportado_o_copiado_no_es_comprobacion_local(self):
        real = admitir_exportacion_tecnica(solicitud(self.e))
        ajeno = replace(real)
        self.assertFalse(ajeno.comprobacion_local_coherente)
        self.assertFalse(ajeno.admisible_para_consumo_tecnico)
        self.assertIs(ajeno.estado_estructural, E.PENDIENTE_DE_EVIDENCIA)

    def test_determinismo_sin_despacho_red_sql_escritura_o_qa(self):
        s = solicitud(self.e)
        with patch("spica.artefactos.cierre_exportacion.exportar_resultado_json", side_effect=AssertionError("no productor")), \
             patch("spica.calidad.evaluar_registro", side_effect=AssertionError("no QA")), \
             patch("builtins.open", side_effect=AssertionError("no archivos")), \
             patch("socket.socket", side_effect=AssertionError("no red")), \
             patch("sqlite3.connect", side_effect=AssertionError("no SQL")):
            a = admitir_exportacion_tecnica(s)
            b = admitir_exportacion_tecnica(s)
        self.assertEqual(a, b)
        self.assertTrue(a.admisible_para_consumo_tecnico)
        self.assertIs(a.cierre.evidencia, self.e)

    def test_no_es_autorizacion_ciencia_ni_bool_generico(self):
        r = admitir_exportacion_tecnica(solicitud(self.e))
        self.assertFalse(r.autoriza_operacion)
        self.assertFalse(r.autorizacion_concedida)
        self.assertFalse(r.validacion_cientifica_realizada)
        self.assertFalse(r.habilitacion_rc3_concedida)
        with self.assertRaises(TypeError):
            bool(r)
        with self.assertRaises(FrozenInstanceError):
            r.restricciones = ()

    def test_tipos_limites_y_version_de_solicitud(self):
        s = solicitud(self.e)
        for kw in (dict(contenido={}), dict(evidencia={}), dict(proyecto={}), dict(limites={}),
                   dict(materializacion={}), dict(exigir_integridad_fisica=1)):
            with self.subTest(kw=kw), self.assertRaises(TypeError):
                replace(s, **kw)
        with self.assertRaises(ValueError):
            replace(s, version_contrato="99.0.0")
        with self.assertRaises(TypeError):
            admitir_exportacion_tecnica({})


if __name__ == "__main__":
    unittest.main()
