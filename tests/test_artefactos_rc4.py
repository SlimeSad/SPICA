"""Contratos RC4; fixtures explícitamente ficticias, sin almacenes operativos."""

from dataclasses import FrozenInstanceError, replace
import hashlib
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from spica.artefactos import (
    VERSION_ARTEFACTOS, DescriptorArtefacto, DisponibilidadArtefacto as F,
    EstadoArtefacto as L, InventarioArtefactos, ProduccionArtefactos,
    ReferenciaArtefacto as Ref, TipoArtefacto as T, inspeccionar_linaje,
)
from spica.contextos import ContextoOperacion, EstadoOperacion as S, TipoOperacion
from spica.coordinacion import ComposicionOperaciones, DependenciaOperacion, NodoOperacion, RequisitoCompatibilidad
from spica.calidad.modelos import EstadoEvaluacionQA
from spica.calidad.restricciones import RestriccionQA, TipoRestriccionQA as TR
from spica.adquisicion.nucleo.modelos import EstadoIntegridad as I
from spica.adquisicion.readquisicion.modelos import EvidenciaLocal, EstadoLocal
from spica.interoperabilidad.adaptadores import DiagnosticoAdaptacion as D, NivelDiagnostico as N
from spica.interoperabilidad.modelos import EstadoAptitud as E
from spica.interoperabilidad.perfiles import EntradaPerfil
# Fabricantes previos, nunca TestCase ni acceso a datos institucionales.
from test_perfiles_informacion_rc2 import vinculo, perfil, cambiar_campo, PROC, FECHA, VER


CUERPO = b"RC4: contenido completamente ficticio; sin observaciones.\n"
SHA = hashlib.sha256(CUERPO).hexdigest()
BLOQUEO = RestriccionQA("bloqueo-rc4", TR.BLOQUEO_USO_DEL_RESULTADO,
    ("acreditar_ciencia",), "Fixture: no permite acreditar ciencia")


def descriptor(nombre="original", *, tipo=T.ORIGINAL, proyecto=None, entrada_kw=None, **kw):
    p = perfil("RC4")
    datos = dict(revision="r1", sha256_declarado=SHA if tipo is T.ORIGINAL else None,
                 size_bytes_declarado=len(CUERPO) if tipo is T.ORIGINAL else None)
    datos.update(entrada_kw or {})
    ep = vinculo(nombre, p=p, proyecto=proyecto, **datos)
    campos = dict(entrada_perfil=ep, tipo=tipo, contenido_id="contenido-sintetico" if tipo is T.ORIGINAL else None,
                  formato="texto-ficticio")
    campos.update(kw)
    return DescriptorArtefacto(**campos)


def produccion(entradas, salidas, identidad="preparar", *, estado=S.DECLARADA, **kw):
    es = tuple(a.entrada_perfil.entrada for a in entradas)
    refs = tuple(a.entrada_perfil.entrada.entrada_id for a in salidas)
    ds = (D("interrupcion_ficticia", "fixture", N.FALTANTE),) if estado in (S.PARCIAL, S.FALLIDA, S.CANCELADA) else ()
    o = ContextoOperacion(identidad, es[0].proyecto, es, TipoOperacion.DESCRIPCION_ESTRUCTURAL,
        "Describir producción ficticia, sin ejecutar transformaciones", parametros=(("alcance", "solo-descriptor"),),
        estado=estado, diagnosticos=ds, referencias_resultado=() if estado in (S.DECLARADA, S.PLANIFICADA) else refs)
    campos = dict(operacion=o, metodo_id="descriptor-ficticio", metodo_version="fixture-1",
        entradas=tuple(a.referencia for a in entradas), salidas=tuple(a.referencia for a in salidas))
    campos.update(kw)
    return ProduccionArtefactos(**campos)


def composicion(ps, *, usos=("describir-fixture",), dependencias=(), **kw):
    campos = dict(identificador="composicion-rc4", proyecto=ps[0].operacion.proyecto,
        operaciones=tuple(NodoOperacion(p.operacion, usos) for p in ps), dependencias=dependencias,
        finalidad="Inspeccionar descriptores sintéticos RC4")
    campos.update(kw)
    return ComposicionOperaciones(**campos)


def escenario(*, estado=S.DECLARADA, estado_salida=L.DESCRITO, **kw):
    a = descriptor()
    b = descriptor("preparado", tipo=T.PREPARADO, proyecto=a.entrada_perfil.entrada.proyecto, estado_logico=estado_salida)
    p = produccion((a,), (b,), estado=estado, **kw)
    return InventarioArtefactos((a, b), (p,), (composicion((p,)),))


def codigos(r):
    return tuple(d.codigo for d in r.diagnosticos) + tuple(d.codigo for a in r.artefactos for d in a.diagnosticos)


def piloto():
    a = descriptor(restricciones_adicionales=(BLOQUEO,))
    p_a = a.entrada_perfil.entrada.proyecto
    p_b = replace(p_a, contexto_id="contexto-B", proyecto=replace(p_a.proyecto, project_id="proyecto-B"))
    otro = descriptor("original-B", proyecto=p_b)
    preparado = descriptor("preparado", tipo=T.PREPARADO, proyecto=p_a)
    derivado = descriptor("derivado", tipo=T.DERIVADO, proyecto=p_a, estado_logico=L.PARCIAL)
    p1 = produccion((a,), (preparado,))
    p2 = produccion((preparado,), (derivado,), "derivar", estado=S.PARCIAL)
    c = composicion((p1, p2), dependencias=(DependenciaOperacion("preparar", "derivar"),))
    return InventarioArtefactos((a, otro, preparado, derivado), (p1, p2), (c,))


class ContratoArtefactosRC4Tests(unittest.TestCase):
    def test_descriptor_valido_sin_efectos(self):
        a = descriptor()
        r = inspeccionar_linaje(InventarioArtefactos((a,)))
        self.assertEqual(a.version_contrato, VERSION_ARTEFACTOS)
        self.assertEqual(a.referencia.object_id, a.entrada_perfil.entrada.objeto.object_id)
        self.assertEqual(r.estado_estructural, E.PENDIENTE_DE_EVIDENCIA)
        self.assertFalse(a.autoriza_operacion)
        self.assertFalse(r.comprobacion_fisica_realizada)
        self.assertFalse(r.persistencia_realizada)
        self.assertFalse(r.ejecucion_realizada)
        for v in (a, r):
            with self.assertRaises(TypeError):
                bool(v)

    def test_identificadores_invalidos_no_se_normalizan(self):
        for valor in ("", " ", "x\n", 1, "x" * 513):
            with self.subTest(valor=valor), self.assertRaises(ValueError):
                Ref(valor, "r1")
        self.assertEqual(Ref(" código original ", " revisión ").object_id, " código original ")

    def test_tipo_y_colecciones_cerradas(self):
        for crear in (lambda: replace(descriptor(), tipo="original"),
                lambda: InventarioArtefactos([descriptor()]),
                lambda: replace(descriptor(), entrada_perfil={}),
                lambda: replace(descriptor(), incertidumbres=["x"])):
            with self.subTest(crear=crear), self.assertRaises(TypeError):
                crear()

    def test_versiones_incompatibles_no_se_migran(self):
        inv = escenario()
        for objeto in (inv, inv.artefactos[0], inv.producciones[0], inv.artefactos[0].referencia):
            with self.subTest(objeto=type(objeto).__name__), self.assertRaises(ValueError):
                replace(objeto, version_contrato="99")
        with self.assertRaises(ValueError):
            Ref("objeto", "")

    def test_identidad_revision_duplicada_no_sobrescribe_historia(self):
        a = descriptor()
        inv = InventarioArtefactos((a, a))
        self.assertIn("identidad_revision_artefacto_duplicada", codigos(inspeccionar_linaje(inv)))
        self.assertEqual(len(inv.artefactos), 2)

    def test_mismo_contenido_dos_proyectos_no_fusionados(self):
        r = inspeccionar_linaje(piloto())
        a, b = r.artefactos[:2]
        self.assertEqual(a.descriptor.contenido_id, b.descriptor.contenido_id)
        self.assertNotEqual(a.descriptor.referencia, b.descriptor.referencia)
        self.assertNotEqual(a.descriptor.entrada_perfil.entrada.proyecto.project_id,
                            b.descriptor.entrada_perfil.entrada.proyecto.project_id)
        self.assertNotIn("identidad_contenido_con_metadatos_contradictorios", codigos(r))

    def test_identidad_contenido_contradictoria(self):
        a = descriptor()
        b = descriptor("otro", proyecto=a.entrada_perfil.entrada.proyecto, entrada_kw={"sha256_declarado": "b" * 64})
        self.assertIn("identidad_contenido_con_metadatos_contradictorios",
            codigos(inspeccionar_linaje(InventarioArtefactos((a, b)))))

    def test_hash_compartido_no_admite_tamanos_distintos(self):
        a = descriptor()
        b = descriptor("otro", proyecto=a.entrada_perfil.entrada.proyecto,
                       contenido_id="otro-contenido", entrada_kw={"size_bytes_declarado": len(CUERPO) + 1})
        self.assertIn("hash_declarado_con_tamanos_contradictorios",
            codigos(inspeccionar_linaje(InventarioArtefactos((a, b)))))

    def test_hash_real_en_memoria_sigue_siendo_declarado(self):
        a = descriptor()
        self.assertEqual(a.entrada_perfil.entrada.sha256_declarado, hashlib.sha256(CUERPO).hexdigest())
        self.assertEqual(a.disponibilidad, F.DESCONOCIDA)
        self.assertIsNone(a.sha256_comprobado_aportado)
        self.assertEqual(a.integridad_aportada, I.PENDIENTE)

    def test_original_ausente_no_se_promueve_por_referencia_historica(self):
        ev = EvidenciaLocal(EstadoLocal.AUSENTE, FECHA, PROC, activo_id="asset-ficticio")
        a = descriptor(entrada_kw={"asset_id": "asset-ficticio", "evidencia_local": ev},
            generacion_conservacion_ref="generacion-historica", estado_logico=L.FINAL_DECLARADO)
        r = inspeccionar_linaje(InventarioArtefactos((a,)))
        self.assertEqual(a.disponibilidad, F.AUSENTE_SEGUN_EVIDENCIA)
        self.assertEqual(a.estado_conservacion.value, "declarado")
        self.assertIn("original_final_sin_evidencia_de_preservacion", codigos(r))

    def test_evidencia_integra_es_aportada_no_leida_por_rc4(self):
        ev = EvidenciaLocal(EstadoLocal.INTEGRO, FECHA, PROC, SHA, len(CUERPO), "asset-ficticio")
        a = descriptor(entrada_kw={"asset_id": "asset-ficticio", "evidencia_local": ev})
        r = inspeccionar_linaje(InventarioArtefactos((a,)))
        self.assertEqual(a.integridad_aportada, I.VERIFICADA)
        self.assertEqual(a.disponibilidad, F.PRESENTE_SEGUN_EVIDENCIA)
        self.assertEqual(a.sha256_comprobado_aportado, SHA)
        self.assertFalse(r.comprobacion_fisica_realizada)

    def test_inconsistencia_no_inventa_verificacion_hash_fallida(self):
        ev = EvidenciaLocal(EstadoLocal.INCONSISTENTE, FECHA, PROC, activo_id="asset-ficticio")
        a = descriptor(entrada_kw={"asset_id": "asset-ficticio", "evidencia_local": ev})
        self.assertEqual(a.integridad_aportada, I.PENDIENTE)
        self.assertEqual(inspeccionar_linaje(InventarioArtefactos((a,))).estado_estructural, E.INCOMPATIBLE)

    def test_preparado_no_se_disfraza_de_original_raw(self):
        with self.assertRaises(ValueError):
            descriptor(tipo=T.PREPARADO, entrada_kw={"asset_id": "raw-inventado"})

    def test_sin_productora_explicita(self):
        a = descriptor(tipo=T.DERIVADO)
        self.assertIn("artefacto_sin_operacion_productora", codigos(inspeccionar_linaje(InventarioArtefactos((a,)))))

    def test_concluida_sin_evidencia_no_materializa(self):
        r = inspeccionar_linaje(escenario(estado=S.CONCLUIDA))
        self.assertIn("relacion_sin_evidencia_ejecucion_suficiente", codigos(r))
        self.assertIn("conclusion_declarada_sin_cierre_tecnico_admitido", codigos(r))
        self.assertEqual(r.artefactos[1].descriptor.disponibilidad, F.DESCONOCIDA)

    def test_final_declarado_sin_soporte_rechazado(self):
        r = inspeccionar_linaje(escenario(estado=S.CONCLUIDA, estado_salida=L.FINAL_DECLARADO))
        self.assertIn("salida_final_sin_soporte_declarativo_suficiente", codigos(r))

    def test_final_aportado_no_es_verificacion_ni_ciencia(self):
        r = inspeccionar_linaje(escenario(estado=S.CONCLUIDA, estado_salida=L.FINAL_DECLARADO,
            respaldo=VER, ejecucion_id="ejecucion-ficticia"))
        self.assertNotIn("salida_final_sin_soporte_declarativo_suficiente", codigos(r))
        a = r.artefactos[1].descriptor
        self.assertEqual(a.integridad_aportada, I.PENDIENTE)
        self.assertEqual(a.revision_cientifica, EstadoEvaluacionQA.NO_EVALUADA)
        self.assertFalse(r.autoriza_operacion)

    def test_parcial_conservado_sin_promocion(self):
        r = inspeccionar_linaje(escenario(estado=S.PARCIAL, estado_salida=L.PARCIAL))
        self.assertIn("artefacto_parcial_no_es_final", codigos(r))
        self.assertEqual(r.artefactos[1].descriptor.estado_logico, L.PARCIAL)

    def test_cancelada_y_fallida_no_admiten_salida_final(self):
        for estado in (S.CANCELADA, S.FALLIDA, S.PARCIAL):
            with self.subTest(estado=estado):
                r = inspeccionar_linaje(escenario(estado=estado, estado_salida=L.FINAL_DECLARADO))
                self.assertIn("salida_de_operacion_no_completa_debe_ser_parcial", codigos(r))

    def test_restriccion_omitida_en_salida_se_hereda_transitivamente(self):
        inv = piloto()
        self.assertEqual(inv.artefactos[-1].restricciones_adicionales, ())
        r = inspeccionar_linaje(inv)
        ultima = r.artefactos[-1]
        self.assertIn(BLOQUEO, tuple(x.restriccion for x in ultima.restricciones_heredadas))
        self.assertEqual(sum(x.restriccion.codigo == BLOQUEO.codigo for x in ultima.restricciones), 1)
        self.assertIn("aplicabilidad_restriccion_desconocida", codigos(r))

    def test_bloqueo_del_antecesor_impide_uso_exacto(self):
        inv = piloto()
        c = replace(inv.composiciones[0], operaciones=tuple(replace(n, usos_declarados=("acreditar_ciencia",))
            for n in inv.composiciones[0].operaciones))
        r = inspeccionar_linaje(replace(inv, composiciones=(c,)))
        self.assertIn("restriccion_heredada_impide_uso_declarado", codigos(r))

    def test_conflicto_no_rebaja_restriccion_heredada(self):
        inv = piloto()
        nuevo = replace(BLOQUEO, tipo=TR.INFORMATIVA, operaciones=())
        b = replace(inv.artefactos[2], restricciones_adicionales=(nuevo,))
        with self.assertRaises(ValueError):
            inspeccionar_linaje(replace(inv, artefactos=(*inv.artefactos[:2], b, inv.artefactos[3])))

    def test_perfil_incompatible_con_entrada_rechazado(self):
        a = descriptor()
        with self.assertRaises(ValueError):
            EntradaPerfil(a.entrada_perfil.entrada, replace(a.entrada_perfil.perfil, tipo_recurso="otra-estructura"))

    def test_misma_version_perfil_no_redefine_campos(self):
        a = descriptor()
        b = descriptor("otro", proyecto=a.entrada_perfil.entrada.proyecto)
        b = replace(b, entrada_perfil=cambiar_campo(b.entrada_perfil, tipo=replace(b.entrada_perfil.perfil.campos[0].tipo,
                                                                                 valor="otro-tipo")))
        self.assertIn("perfil_version_con_definiciones_distintas", codigos(inspeccionar_linaje(InventarioArtefactos((a, b)))))

    def test_referencia_inexistente_no_se_infiere_por_sha(self):
        inv = escenario()
        p = replace(inv.producciones[0], entradas=(Ref("no-existe", "r1"),))
        self.assertIn("referencia_artefacto_inexistente", codigos(inspeccionar_linaje(replace(inv, producciones=(p,)))))

    def test_autoarista_detectada(self):
        inv = escenario()
        p = replace(inv.producciones[0], entradas=(inv.artefactos[1].referencia,))
        self.assertIn("autoarista_linaje", codigos(inspeccionar_linaje(replace(inv, producciones=(p,)))))

    def test_ciclo_no_pierde_bloqueos(self):
        inv = piloto()
        p = replace(inv.producciones[0], entradas=(inv.artefactos[-1].referencia,))
        r = inspeccionar_linaje(replace(inv, producciones=(p, inv.producciones[1])))
        self.assertIn("ciclo_linaje", codigos(r))
        self.assertEqual(r.orden_linaje, ())
        self.assertTrue(all(BLOQUEO in tuple(x.restriccion for x in a.restricciones) for a in r.artefactos))

    def test_multiples_entradas_y_salidas_explicitas(self):
        a = descriptor()
        p_a = a.entrada_perfil.entrada.proyecto
        b = descriptor("original2", proyecto=p_a)
        c = descriptor("preparado", proyecto=p_a, tipo=T.PREPARADO)
        d = descriptor("derivado", proyecto=p_a, tipo=T.DERIVADO)
        p = produccion((a, b), (c, d))
        r = inspeccionar_linaje(InventarioArtefactos((a, b, c, d), (p,), (composicion((p,)),)))
        self.assertEqual(len(r.orden_linaje), 4)
        self.assertNotIn("entradas_linaje_no_corresponden_a_operacion", codigos(r))

    def test_revisiones_distinguidas_sin_reabrir_historia(self):
        inv = escenario()
        a, b = inv.artefactos
        e = b.entrada_perfil.entrada
        c = replace(b, entrada_perfil=EntradaPerfil(replace(e, entrada_id="entrada-r2", revision="r2"), b.entrada_perfil.perfil))
        p2 = produccion((b,), (c,), "revisar-preparado")
        ps = (inv.producciones[0], p2)
        inv = InventarioArtefactos((a, b, c), ps, (composicion(ps,
            dependencias=(DependenciaOperacion("preparar", "revisar-preparado"),)),))
        r = inspeccionar_linaje(inv)
        self.assertEqual(tuple(x.revision for x in r.orden_linaje if x.object_id == b.referencia.object_id), ("r1", "r2"))
        self.assertEqual(b.entrada_perfil.entrada.revision, "r1")

    def test_preparado_no_reutiliza_identidad_logica_del_original(self):
        a = descriptor()
        e = a.entrada_perfil.entrada
        b = replace(a, tipo=T.PREPARADO, entrada_perfil=EntradaPerfil(replace(e, entrada_id="otra-entrada", revision="r2"), a.entrada_perfil.perfil))
        self.assertIn("identidad_artefacto_con_tipo_distinto", codigos(inspeccionar_linaje(InventarioArtefactos((a, b)))))

    def test_original_vacio_con_evidencia_aportada_coherente(self):
        huella = hashlib.sha256(b"").hexdigest()
        ev = EvidenciaLocal(EstadoLocal.INTEGRO, FECHA, PROC, huella, 0, "asset-vacio")
        a = descriptor(entrada_kw={"asset_id": "asset-vacio", "evidencia_local": ev,
            "sha256_declarado": huella, "size_bytes_declarado": 0})
        self.assertEqual(a.size_bytes_comprobado_aportado, 0)
        self.assertEqual(a.integridad_aportada, I.VERIFICADA)
        self.assertEqual(inspeccionar_linaje(InventarioArtefactos((a,))).estado_estructural, E.APTO_ESTRUCTURALMENTE)

    def test_original_parcial_no_se_presenta_como_final(self):
        a = descriptor(estado_logico=L.PARCIAL)
        self.assertIn("artefacto_parcial_no_es_final", codigos(inspeccionar_linaje(InventarioArtefactos((a,)))))

    def test_revision_de_referencia_ausente_no_se_sustituye(self):
        inv = escenario()
        p = replace(inv.producciones[0], entradas=(replace(inv.artefactos[0].referencia, revision="r99"),))
        self.assertIn("referencia_artefacto_inexistente", codigos(inspeccionar_linaje(replace(inv, producciones=(p,)))))

    def test_referencia_repetida_en_relacion_no_duplica_evidencia(self):
        inv = escenario()
        p = replace(inv.producciones[0], entradas=inv.producciones[0].entradas * 2)
        self.assertIn("referencia_produccion_repetida", codigos(inspeccionar_linaje(replace(inv, producciones=(p,)))))

    def test_instantanea_operacion_distinta_de_rc3_no_se_alinea(self):
        inv = escenario()
        p = replace(inv.producciones[0], operacion=replace(inv.producciones[0].operacion))
        self.assertIn("productora_no_es_instantanea_rc3", codigos(inspeccionar_linaje(replace(inv, producciones=(p,)))))

    def test_restricciones_composicion_y_relacion_se_conservan(self):
        inv = escenario()
        r_composicion = replace(BLOQUEO, codigo="bloqueo-composicion")
        r_relacion = replace(BLOQUEO, codigo="bloqueo-relacion")
        c = replace(inv.composiciones[0], restricciones_adicionales=(r_composicion,))
        p = replace(inv.producciones[0], restricciones_adicionales=(r_relacion,))
        r = inspeccionar_linaje(replace(inv, producciones=(p,), composiciones=(c,)))
        rs = tuple(x.restriccion for x in r.artefactos[-1].restricciones_heredadas)
        self.assertIn(r_composicion, rs)
        self.assertIn(r_relacion, rs)

    def test_identidad_md_no_puede_atribuirse_a_dos_proyectos(self):
        inv = piloto()
        a, b = inv.artefactos[:2]
        e = b.entrada_perfil.entrada
        b = replace(b, entrada_perfil=EntradaPerfil(replace(e, objeto=replace(e.objeto, object_id=a.referencia.object_id),
            revision="otra-revision"), b.entrada_perfil.perfil))
        self.assertIn("identidad_objeto_con_descripciones_distintas", codigos(inspeccionar_linaje(InventarioArtefactos((a, b)))))

    def test_salida_problematica_transmite_diagnostico_al_descendiente(self):
        inv = piloto()
        a = replace(inv.artefactos[0], diagnosticos=(D("contradiccion-fixture", "fixture", N.CONTRADICCION),))
        r = inspeccionar_linaje(replace(inv, artefactos=(a, *inv.artefactos[1:])))
        self.assertIn("antecesor_con_coherencia_contradictoria", tuple(d.codigo for d in r.artefactos[-1].diagnosticos))

    def test_rc2_real_conserva_comparacion_incompatible_y_finalidad(self):
        from test_coordinacion_rc3 import con_perfiles
        for tipo, esperado in ((None, E.APTO_ESTRUCTURALMENTE), ("tipo-incompatible", E.INCOMPATIBLE)):
            with self.subTest(tipo=tipo):
                n = con_perfiles(tipo=tipo)
                req = n.compatibilidades[0]
                a, b = (DescriptorArtefacto(ep, T.ORIGINAL, "contenido-ficticio") for ep in (req.primero, req.segundo))
                salida = descriptor("salida", tipo=T.PREPARADO, proyecto=n.contexto.proyecto)
                p = ProduccionArtefactos(n.contexto, "descriptor", "1", (a.referencia, b.referencia), (salida.referencia,))
                c = composicion((p,), operaciones=(n,))
                r = inspeccionar_linaje(InventarioArtefactos((a, b, salida), (p,), (c,)))
                comp = r.composiciones[0].operaciones[0].compatibilidades[0]
                self.assertEqual(comp.estado, esperado)
                self.assertIs(comp.finalidad, req.finalidad)
                self.assertIs(comp.primero, req.primero)
                self.assertIs(comp.segundo.perfil, req.segundo.perfil)

    def test_qa_previo_y_json_nativo_preservados_con_restricciones(self):
        from test_coordinacion_rc3 import qa_real, piloto as piloto_rc3
        from spica.calidad.exportacion import exportar_resultado_json
        qa = qa_real()
        v = qa.cierre_qa.vinculos[0]
        antes = exportar_resultado_json(v.resultado, v.contexto_exportacion)
        c = piloto_rc3(qa)
        n = c.operaciones[1]
        req = n.compatibilidades[0]
        a, b = (DescriptorArtefacto(ep, T.ORIGINAL, "contenido-ficticio") for ep in (req.primero, req.segundo))
        salida = descriptor("salida", tipo=T.PREPARADO, proyecto=n.contexto.proyecto)
        p = ProduccionArtefactos(n.contexto, "descriptor", "1", (a.referencia, b.referencia), (salida.referencia,))
        r = inspeccionar_linaje(InventarioArtefactos((a, b, salida), (p,), (c,)))
        politicas = tuple(x.restriccion for x in r.artefactos[-1].restricciones)
        self.assertTrue(all(x in politicas for x in v.restricciones))
        self.assertIs(r.composiciones[0].composicion.operaciones[0].cierre_qa.informe, qa.cierre_qa.informe)
        self.assertEqual(exportar_resultado_json(v.resultado, v.contexto_exportacion), antes)

    def test_cruce_de_proyectos_no_se_repara_con_hash(self):
        inv = piloto()
        p = replace(inv.producciones[0], entradas=(inv.artefactos[1].referencia,))
        self.assertIn("relacion_atribuida_a_otro_proyecto_o_contexto", codigos(inspeccionar_linaje(replace(inv,
            producciones=(p, inv.producciones[1])))))

    def test_inmutabilidad_defensiva(self):
        inv = escenario()
        for objeto, campo, valor in ((inv, "producciones", ()), (inv.artefactos[0], "contenido_id", "otro"),
                (inv.producciones[0], "entradas", ()), (inv.artefactos[0].referencia, "revision", "r99")):
            with self.subTest(objeto=type(objeto).__name__), self.assertRaises(FrozenInstanceError):
                setattr(objeto, campo, valor)

    def test_piloto_rc1_rc2_rc3_por_referencia_sin_ejecucion(self):
        inv = piloto()
        r = inspeccionar_linaje(inv)
        self.assertIs(r.inventario, inv)
        self.assertIs(r.composiciones[0].composicion, inv.composiciones[0])
        self.assertIs(r.artefactos[0].descriptor.entrada_perfil, inv.artefactos[0].entrada_perfil)
        self.assertEqual(inv.producciones[0].parametros, (("alcance", "solo-descriptor"),))
        self.assertIn("dependencia_sin_cierre_tecnico_compatible_aportado", codigos(r))
        self.assertEqual(len(r.artefactos), 4)

    def test_dependencia_rc3_omitida_detectada(self):
        inv = piloto()
        c = replace(inv.composiciones[0], dependencias=())
        self.assertIn("linaje_sin_dependencia_rc3_explicita", codigos(inspeccionar_linaje(replace(inv, composiciones=(c,)))))

    def test_productora_ausente_del_grafo_rc3(self):
        inv = piloto()
        c = replace(inv.composiciones[0], operaciones=(inv.composiciones[0].operaciones[1],), dependencias=())
        self.assertIn("productora_sin_referencia_rc3", codigos(inspeccionar_linaje(replace(inv, composiciones=(c,)))))

    def test_productoras_contradictorias_no_sobrescriben(self):
        inv = escenario()
        p = replace(inv.producciones[0], operacion=replace(inv.producciones[0].operacion, operacion_id="otra"))
        r = inspeccionar_linaje(replace(inv, producciones=(inv.producciones[0], p)))
        self.assertIn("artefacto_con_productoras_contradictorias", codigos(r))

    def test_ejecucion_no_es_identidad_de_operacion(self):
        inv = piloto()
        ps = tuple(replace(p, ejecucion_id="misma-ejecucion") for p in inv.producciones)
        self.assertIn("ejecucion_atribuida_a_operaciones_distintas", codigos(inspeccionar_linaje(replace(inv, producciones=ps))))

    def test_salida_debe_corresponder_a_referencia_resultado(self):
        inv = escenario(estado=S.CONCLUIDA)
        p = replace(inv.producciones[0], operacion=replace(inv.producciones[0].operacion, referencias_resultado=("otro-resultado",)))
        self.assertIn("salida_no_declarada_en_referencias_resultado", codigos(inspeccionar_linaje(replace(inv, producciones=(p,)))))

    def test_cotas_acotan_descriptores_y_relaciones(self):
        a = descriptor()
        with self.assertRaises(ValueError):
            InventarioArtefactos((a,) * 65)
        inv = escenario()
        p = inv.producciones[0]
        with self.assertRaises(ValueError):
            InventarioArtefactos((a,), (replace(p, entradas=p.entradas * 16, salidas=p.salidas * 16),) * 5)

    def test_determinismo_sin_mutar_entradas(self):
        inv = piloto()
        a = inspeccionar_linaje(inv)
        self.assertEqual(a, inspeccionar_linaje(inv))
        self.assertEqual(a.inventario, inv)

    def test_inspeccion_no_llama_a_transporte_almacen_o_qa(self):
        with patch("spica.adquisicion.transportes.http.ClienteHTTP.get", side_effect=AssertionError("red")), \
                patch("spica.adquisicion.almacenamiento.raw.AlmacenRAW.__init__", side_effect=AssertionError("raw")), \
                patch("spica.calidad.EvaluadorNivel0.__init__", side_effect=AssertionError("qa")):
            self.assertFalse(inspeccionar_linaje(piloto()).ejecucion_realizada)

    def test_importaciones_y_piloto_sin_red_sqlite_ni_escrituras(self):
        codigo = r'''
import sys
def barrera(evento, argumentos):
    if evento.startswith("socket.") or evento == "sqlite3.connect":
        raise AssertionError("efecto_externo_prohibido")
    if evento == "open":
        ruta, modo, flags = argumentos
        if (isinstance(modo, str) and any(c in modo for c in "wax+")) or flags & (1 | 2 | 64 | 512 | 1024):
            raise AssertionError("escritura_prohibida")
        if isinstance(ruta, str) and "spica_datos" in ruta.lower():
            raise AssertionError("lectura_operativa_prohibida")
sys.addaudithook(barrera)
import spica.artefactos
import spica.coordinacion
from test_artefactos_rc4 import piloto
r = spica.artefactos.inspeccionar_linaje(piloto())
assert len(r.artefactos) == 4 and not r.ejecucion_realizada
print("sin_efectos")
'''
        p = subprocess.run([sys.executable, "-B", "-c", codigo], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout.strip(), "sin_efectos")


if __name__ == "__main__":
    unittest.main()
