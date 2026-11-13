"""Contextos RC1 con datos inventados en memoria; nunca abren almacenes operativos."""

from dataclasses import FrozenInstanceError, fields, replace
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from spica.adquisicion.almacenamiento.modelos import ProyectoCientifico, ObjetoCientifico
from spica.adquisicion.catalogo.modelos import ProcedenciaCatalogo
from spica.adquisicion.consultas_locales import ENCABEZADO_SENAMHI, ProcedenciaLocal
from spica.adquisicion.nucleo import Fuente
from spica.adquisicion.readquisicion.modelos import EvidenciaLocal, EstadoLocal
from spica.interoperabilidad import IdentidadRecurso, RecursoInteroperable
from spica.interoperabilidad.adaptadores import (
    DiagnosticoAdaptacion, EstadoAdaptacion, NivelDiagnostico,
)
from spica.calidad import (
    ConfiguracionQA, LimitesQA, ProcedenciaQA, RegistroQA, ResultadoQA,
    EstadoResultadoQA, evaluar_registro, restricciones_resultado,
    RestriccionQA, TipoRestriccionQA,
)
from spica.calidad.exportacion import ContextoExportacionQA, exportar_resultado_json
from spica.calidad.consumo import consumir_exportaciones, EstadoConsumoQA
from spica.calidad.conciliacion_lotes import conciliar_lotes, LoteQA, EstadoConciliacionQA
from spica.contextos import (
    ConfiguracionContexto, ContextoProyecto, ContextoEntrada, ContextoOperacion,
    TipoOperacion, EstadoOperacion as E, VERSION_CONTEXTO, PERFIL_QA0,
    combinar_restricciones, validar_relaciones, cambiar_estado,
    contexto_exportacion_qa, VinculoResultadoQA, validar_vinculos_qa,
)


FECHA = datetime(2026, 11, 13, tzinfo=timezone.utc)
FUENTE = Fuente("SPICA-SINTETICA", "fixture-rc1")
PROC = ProcedenciaCatalogo("fixture:rc1", FECHA, "construccion_en_memoria", "fixture-inventada")
SHA = hashlib.sha256(b"contenido sintetico compartido RC1\n").hexdigest()
BLOQUEO = RestriccionQA("bloqueo-fixture", TipoRestriccionQA.BLOQUEO_USO_DEL_RESULTADO,
    ("uso-ajeno-a-la-fixture",), "Restriccion inventada para el ensayo.")
CAUSA = DiagnosticoAdaptacion("interrupcion_declarada", "operacion", NivelDiagnostico.FALTANTE)


def proyecto(project_id="proyecto-A", contexto_id="contexto-A", **kw):
    d = dict(contexto_id=contexto_id, proyecto=ProyectoCientifico(project_id),
             configuracion=ConfiguracionContexto(PERFIL_QA0, "1.0.0"), restricciones=(BLOQUEO,))
    d.update(kw)
    return ContextoProyecto(**d)


def entrada(p=None, **kw):
    p = proyecto() if p is None else p
    d = dict(entrada_id="entrada-1", proyecto=p,
        objeto=ObjetoCientifico("objeto-" + p.project_id, p.project_id, family="fixture", kind="dataset"),
        recurso=RecursoInteroperable(IdentidadRecurso(FUENTE, " recurso literal ", "producto-ficticio"),
            "metadatos-1", procedencia=PROC), revision="descripcion-1", tipo_recurso="tabla-sintetica",
        perfil_estructural=PERFIL_QA0, sha256_declarado=SHA)
    d.update(kw)
    return ContextoEntrada(**d)


def operacion(e=None, operacion_id="operacion-1", **kw):
    e = entrada() if e is None else e
    d = dict(operacion_id=operacion_id, proyecto=e.proyecto, entradas=(e,),
        tipo=TipoOperacion.QA_NIVEL0, proposito="Comprobar una estructura inventada",
        limites_qa=LimitesQA(max_registros=4, max_resultados=8),
        configuracion_qa=ConfiguracionQA(reglas=("L0-EST-001",)))
    d.update(kw)
    return ContextoOperacion(**d)


def iniciada(o=None):
    o = operacion() if o is None else o
    return cambiar_estado(cambiar_estado(o, E.PLANIFICADA), E.INICIADA)


def resultado(e=None, *, numero=1, configuracion=None):
    e = entrada() if e is None else e
    valores = ("fila-inventada", "estacion-ficticia", "20260101", "10000", "", "", "",
               "1.00", "2.00", "0.0", "red-ficticia", "", "", "", "01234.0", "20260102")
    r = RegistroQA(numero, valores[0], valores[1], numero + 1, numero + 1,
                   tuple(zip(ENCABEZADO_SENAMHI, valores)), True,
                   valores_csv_originales=valores)
    p = ProcedenciaQA(e.recurso.identidad.fuente, e.recurso.identidad.recurso_id,
                     asset_id=e.asset_id, sha256_referencia=e.sha256_declarado)
    return tuple(evaluar_registro(r, p, configuracion=(configuracion if configuracion is not None
                 else ConfiguracionQA(reglas=("L0-EST-001",)))))[0]


class ModelosContextoRC1Tests(unittest.TestCase):
    def test_reutiliza_md_sin_copiar_o_asignar_version_desconocida(self):
        p = proyecto()
        e = entrada(p)
        o = operacion(e)
        self.assertIs(e.proyecto, p)
        self.assertIs(o.entradas[0], e)
        self.assertIsNone(p.proyecto.schema_version)
        self.assertEqual((p.project_id, e.objeto.project_id), ("proyecto-A", "proyecto-A"))
        self.assertEqual(e.objeto.kind, "dataset")

    def test_proyecto_invalido_y_contexto_sin_proyecto_rechazados(self):
        with self.assertRaises(ValueError):
            ProyectoCientifico(" ")
        with self.assertRaises(TypeError):
            proyecto(proyecto=None)
        for identificador in ("", " ", "ctx\nsecreto", "a" * 129):
            with self.subTest(identificador=repr(identificador)), self.assertRaises(ValueError):
                proyecto(contexto_id=identificador)

    def test_versiones_contextuales_incompatibles_rechazadas(self):
        for v in ("1.0.0", "0.2.0", None, 1):
            for dato in (proyecto().configuracion, proyecto(), entrada(), operacion()):
                with self.subTest(tipo=type(dato).__name__, version=v), self.assertRaises(ValueError):
                    replace(dato, version_contrato=v)

    def test_versiones_de_contenido_y_metadatos_no_se_confunden(self):
        e = entrada(version_contenido="edicion-declarada-8")
        self.assertEqual((e.revision, e.recurso.revision_metadatos, e.version_contenido,
                          e.version_contrato), ("descripcion-1", "metadatos-1", "edicion-declarada-8", VERSION_CONTEXTO))
        self.assertIsNone(e.recurso.version_institucional)

    def test_literales_de_recurso_preservados(self):
        e = entrada()
        self.assertEqual(e.recurso.identidad.recurso_id, " recurso literal ")
        self.assertIsNone(e.recurso.espacial)
        self.assertIsNone(e.recurso.temporal)

    def test_entrada_de_otro_proyecto_md_no_se_admite(self):
        with self.assertRaisesRegex(ValueError, "objeto_de_otro_proyecto"):
            entrada(objeto=ObjetoCientifico("objeto", "proyecto-ajeno"))

    def test_sha_y_tamano_declarados_no_son_comprobacion_fisica(self):
        e = entrada(size_bytes_declarado=0)
        self.assertIsNone(e.evidencia_local)
        self.assertEqual((e.sha256_declarado, e.size_bytes_declarado), (SHA, 0))
        for kw in ({"sha256_declarado": "x" * 64}, {"size_bytes_declarado": -1},
                   {"size_bytes_declarado": True}):
            with self.subTest(kw=kw), self.assertRaises(ValueError):
                entrada(**kw)

    def test_evidencia_local_reutilizada_y_contradictoria_rechazada(self):
        ev = EvidenciaLocal(EstadoLocal.INTEGRO, FECHA, PROC, SHA, 0, "activo-ficticio")
        e = entrada(asset_id="activo-ficticio", evidencia_local=ev, size_bytes_declarado=0)
        self.assertIs(e.evidencia_local, ev)
        for kw in ({"sha256_declarado": "0" * 64}, {"size_bytes_declarado": 1}, {"asset_id": "otro"}):
            with self.subTest(kw=kw), self.assertRaises(ValueError):
                replace(e, **kw)

    def test_integridad_inconsistente_no_se_oculta(self):
        ev = EvidenciaLocal(EstadoLocal.INCONSISTENTE, FECHA, PROC, SHA, 0, "activo-ficticio")
        e = entrada(asset_id="activo-ficticio", evidencia_local=ev)
        self.assertIs(e.estado, EstadoAdaptacion.CONTRADICTORIO)
        with self.assertRaisesRegex(ValueError, "contradictoria"):
            contexto_exportacion_qa(operacion(e), e.entrada_id, 1)

    def test_procedencia_desconocida_se_conserva_y_se_diagnostica(self):
        e = entrada(recurso=None)
        self.assertIsNone(e.recurso)
        self.assertIs(e.estado, EstadoAdaptacion.PARCIAL)
        self.assertIn("identidad_recurso_y_procedencia_desconocidas", [d.codigo for d in e.diagnosticos])
        with self.assertRaisesRegex(ValueError, "metadatos_insuficientes"):
            contexto_exportacion_qa(operacion(e), e.entrada_id, 1)

    def test_instantanea_sin_procedencia_no_gana_procedencia(self):
        r = replace(entrada().recurso, procedencia=None)
        e = entrada(recurso=r)
        self.assertIn("procedencia_desconocida", [d.codigo for d in e.diagnosticos])
        with self.assertRaises(ValueError):
            contexto_exportacion_qa(operacion(e), e.entrada_id, 1)

    def test_metadatos_insuficientes_de_perfil_no_se_inventan(self):
        e = entrada(perfil_estructural=None)
        self.assertIs(e.estado, EstadoAdaptacion.PARCIAL)
        with self.assertRaisesRegex(ValueError, "perfil_o_revision"):
            contexto_exportacion_qa(operacion(e), e.entrada_id, 1)

    def test_presupuesto_qa_reutilizado_y_cotas_invalidas_rechazadas(self):
        limites = LimitesQA(max_registros=2, max_resultados=4)
        self.assertIs(operacion(limites_qa=limites).limites_qa, limites)
        with self.assertRaises(ValueError):
            LimitesQA(max_resultados=0)
        with self.assertRaises(TypeError):
            operacion(limites_qa=None)
        for v in (0, -1, True, 65):
            with self.subTest(cota=v), self.assertRaises(ValueError):
                ConfiguracionContexto(PERFIL_QA0, "1.0.0", max_entradas=v)

    def test_parametros_opacos_no_ejecutables_y_qa_falla_cerrado(self):
        literal = "__import__('os').system('nunca ejecutar')"
        c = ConfiguracionContexto("perfil-declarativo", "r1", (("texto", literal),))
        self.assertEqual(c.parametros[0][1], literal)
        with self.assertRaisesRegex(ValueError, "parametros_qa"):
            operacion(parametros=(("umbral-no-aprobado", "4"),))
        with self.assertRaisesRegex(ValueError, "parametros_qa"):
            operacion(entrada(proyecto(configuracion=c)))
        with self.assertRaises(ValueError):
            replace(c, parametros=(("x", "a"), ("x", "b")))

    def test_operacion_declarativa_no_finge_presupuesto_qa(self):
        o = operacion(tipo=TipoOperacion.DESCRIPCION_ESTRUCTURAL, limites_qa=None, configuracion_qa=None)
        self.assertIs(o.estado, E.DECLARADA)
        with self.assertRaises(TypeError):
            contexto_exportacion_qa(o, "entrada-1", 1)
        with self.assertRaises(ValueError):
            operacion(tipo=TipoOperacion.DESCRIPCION_ESTRUCTURAL)

    def test_construccion_y_estados_no_otorgan_permiso(self):
        for dato in (proyecto(), operacion(), iniciada()):
            self.assertFalse(dato.autoriza_operacion)
            with self.assertRaises(TypeError):
                bool(dato)

    def test_inmutabilidad_de_envolventes_y_colecciones(self):
        for dato in (proyecto(), entrada(), operacion(), proyecto().configuracion):
            with self.subTest(tipo=type(dato).__name__), self.assertRaises(FrozenInstanceError):
                dato.version_contrato = "otra"
        with self.assertRaises(TypeError):
            operacion(entradas=[entrada()])
        with self.assertRaises(ValueError):
            ConfiguracionContexto("perfil", "r", parametros=(("x", ["mutable"]),))

    def test_restricciones_heredadas_no_se_omiten(self):
        e = entrada(restricciones_adicionales=())
        o = operacion(e, restricciones_adicionales=())
        self.assertIn(BLOQUEO, e.restricciones)
        self.assertIn(BLOQUEO, o.restricciones)
        with self.assertRaises(TypeError):
            replace(o, restricciones=())

    def test_restriccion_alterada_es_contradiccion_no_sustitucion(self):
        alterada = replace(BLOQUEO, tipo=TipoRestriccionQA.INFORMATIVA, operaciones=())
        with self.assertRaisesRegex(ValueError, "contradictoria"):
            entrada(restricciones_adicionales=(alterada,))
        with self.assertRaisesRegex(ValueError, "contradictoria"):
            combinar_restricciones((BLOQUEO,), (replace(BLOQUEO, motivo="otro"),))

    def test_union_de_restricciones_determinista_sin_duplicados(self):
        r = RestriccionQA("adicional", TipoRestriccionQA.INFORMATIVA, (), "declarada")
        self.assertEqual(combinar_restricciones((BLOQUEO,), (BLOQUEO, r)), (BLOQUEO, r))
        with self.assertRaises(ValueError):
            combinar_restricciones((replace(BLOQUEO, operaciones=()),))

    def test_errores_no_interpolan_entradas_del_llamador(self):
        secreto = "credencial-no-publica\nno-imprimir"
        with self.assertRaises(ValueError) as cm:
            proyecto(contexto_id=secreto)
        self.assertEqual(str(cm.exception), "texto_contextual_no_admitido")
        self.assertNotIn(secreto, str(cm.exception))


class RelacionesContextoRC1Tests(unittest.TestCase):
    def codigos(self, p=(), e=(), o=()):
        return tuple(d.codigo for d in validar_relaciones(p, e, o))

    def test_inventario_coherente_no_produce_errores(self):
        e = entrada()
        self.assertEqual(self.codigos((e.proyecto,), (e,), (operacion(e),)), ())

    def test_proyecto_no_inventariado_y_contexto_parcial(self):
        e = entrada()
        self.assertIn("contexto_proyecto_ausente_o_incompatible", self.codigos(e=(e,), o=(operacion(e),)))

    def test_colision_de_contexto_id_se_detecta(self):
        a, b = proyecto(), proyecto("proyecto-B", "contexto-A")
        self.assertIn("contexto_id_duplicado", self.codigos((a, b)))

    def test_proyecto_md_no_puede_cambiar_descripcion_silenciosamente(self):
        p = proyecto()
        otro = proyecto(contexto_id="contexto-B", proyecto=replace(p.proyecto, nombre="otra descripcion"))
        self.assertIn("identidad_proyecto_con_descripciones_distintas", self.codigos((p, otro)))

    def test_dos_contextos_del_mismo_proyecto_son_independientes(self):
        p = proyecto()
        otro = replace(p, contexto_id="otro-contexto")
        a, b = entrada(p), entrada(otro)
        self.assertEqual(self.codigos((p, otro), (a, b), (operacion(a), operacion(b))), ())
        with self.assertRaisesRegex(ValueError, "otro_contexto"):
            operacion(a, entradas=(b,))

    def test_entrada_duplicada_y_revision_discrepante(self):
        e = entrada()
        self.assertIn("entrada_id_duplicada", self.codigos((e.proyecto,), (e, e)))
        revision = replace(e, revision="descripcion-2")
        self.assertIn("entrada_ausente_o_revision_incompatible",
            self.codigos((e.proyecto,), (revision,), (operacion(e),)))

    def test_objeto_md_con_descripciones_contradictorias(self):
        e = entrada()
        otro = replace(e, entrada_id="otra", objeto=replace(e.objeto, family="otra-familia"))
        self.assertIn("identidad_objeto_con_descripciones_distintas", self.codigos((e.proyecto,), (e, otro)))

    def test_object_id_global_no_se_redefine_en_otro_proyecto(self):
        a = entrada()
        b = entrada(proyecto("proyecto-B", "contexto-B"))
        b = replace(b, objeto=replace(b.objeto, object_id=a.objeto.object_id))
        self.assertIn("identidad_objeto_con_descripciones_distintas", self.codigos((a.proyecto, b.proyecto), (a, b)))

    def test_un_activo_no_se_atribuye_a_objetos_distintos_por_compartir_sha(self):
        a = entrada(asset_id="activo-compartido")
        b = entrada(proyecto("proyecto-B", "contexto-B"), asset_id="activo-compartido")
        self.assertEqual(a.sha256_declarado, b.sha256_declarado)
        self.assertIn("activo_referenciado_desde_objetos_distintos", self.codigos((a.proyecto, b.proyecto), (a, b)))

    def test_dos_proyectos_comparten_sha_sin_fusionar_procedencia(self):
        a, b = entrada(), entrada(proyecto("proyecto-B", "contexto-B"))
        b = replace(b, recurso=replace(b.recurso, procedencia=replace(PROC, referencia="fixture:otra-adquisicion")))
        self.assertEqual(a.sha256_declarado, b.sha256_declarado)
        self.assertNotEqual(a.recurso.procedencia, b.recurso.procedencia)
        self.assertEqual(self.codigos((a.proyecto, b.proyecto), (a, b), (operacion(a), operacion(b))), ())

    def test_operacion_duplicada_no_es_idempotencia_demostrada(self):
        e = entrada()
        o = operacion(e)
        self.assertIn("operacion_id_duplicada", self.codigos((e.proyecto,), (e,), (o, o)))
        self.assertEqual(self.codigos((e.proyecto,), (e,), (o, replace(o, operacion_id="otra"))), ())

    def test_entradas_repetidas_o_ausentes_rechazadas(self):
        e = entrada()
        for v in ((), (e, e)):
            with self.subTest(cantidad=len(v)), self.assertRaises(ValueError):
                operacion(e, entradas=v)
        self.assertIn("entrada_ausente_o_revision_incompatible", self.codigos((e.proyecto,), o=(operacion(e),)))

    def test_orden_repetido_es_determinista_y_no_muta_inventario(self):
        e = entrada()
        inventario = ((e.proyecto,), (e,), (operacion(e),))
        self.assertEqual(validar_relaciones(*inventario), validar_relaciones(*inventario))
        self.assertIs(inventario[2][0].entradas[0], e)


class EstadosContextoRC1Tests(unittest.TestCase):
    def test_secuencia_y_cierre_con_referencias_sin_mutar_declaracion(self):
        o = operacion()
        i = iniciada(o)
        c = cambiar_estado(i, E.CONCLUIDA, referencias_resultado=("ref-1",))
        self.assertEqual((o.estado, i.estado, c.estado), (E.DECLARADA, E.INICIADA, E.CONCLUIDA))
        self.assertEqual(c.restricciones, o.restricciones)
        self.assertFalse(c.autoriza_operacion)

    def test_no_se_salta_planificacion_ni_se_reabre_un_terminal(self):
        with self.assertRaises(ValueError):
            cambiar_estado(operacion(), E.INICIADA)
        cancelada = cambiar_estado(operacion(), E.CANCELADA, diagnosticos=(CAUSA,))
        with self.assertRaises(ValueError):
            cambiar_estado(cancelada, E.PLANIFICADA)

    def test_conclusion_sin_referencia_o_con_faltantes_rechazada(self):
        with self.assertRaises(ValueError):
            cambiar_estado(iniciada(), E.CONCLUIDA)
        with self.assertRaises(ValueError):
            cambiar_estado(iniciada(), E.CONCLUIDA, diagnosticos=(CAUSA,), referencias_resultado=("r",))

    def test_parcial_fallida_cancelada_conservan_causa_y_referencias(self):
        for estado in (E.PARCIAL, E.FALLIDA, E.CANCELADA):
            with self.subTest(estado=estado):
                o = cambiar_estado(iniciada(), estado, diagnosticos=(CAUSA,), referencias_resultado=("prefijo-1",))
                self.assertEqual((o.diagnosticos, o.referencias_resultado), ((CAUSA,), ("prefijo-1",)))
                with self.assertRaises(ValueError):
                    replace(o, diagnosticos=())
        with self.assertRaises(ValueError):
            cambiar_estado(iniciada(), E.PARCIAL, diagnosticos=(CAUSA,))

    def test_resultado_previo_al_inicio_y_referencias_duplicadas(self):
        with self.assertRaises(ValueError):
            operacion(referencias_resultado=("r",))
        with self.assertRaises(ValueError):
            cambiar_estado(iniciada(), E.CONCLUIDA, referencias_resultado=("r", "r"))


class AdaptadorQAContextoRC1Tests(unittest.TestCase):
    def test_mapea_identidades_a_contrato_de_linaje_existente(self):
        o = operacion()
        c = contexto_exportacion_qa(o, "entrada-1", 1)
        self.assertIs(type(c), ContextoExportacionQA)
        self.assertEqual((c.espacio_id, c.evaluacion_id, c.entrada_id),
                         (o.proyecto.contexto_id, o.operacion_id, "entrada-1:1"))
        self.assertIs(c.configuracion, o.configuracion_qa)
        self.assertIn("version_contenido_desconocida", c.incertidumbres)
        self.assertIsNone(c.metadatos_requeridos)

    def test_perfil_o_revision_no_soportados_y_entrada_ajena(self):
        for kw in ({"perfil": "otro-perfil"}, {"revision": "2.0.0"}):
            c = replace(proyecto().configuracion, **kw)
            o = operacion(entrada(proyecto(configuracion=c)))
            with self.subTest(kw=kw), self.assertRaises(ValueError):
                contexto_exportacion_qa(o, "entrada-1", 1)
        with self.assertRaises(ValueError):
            contexto_exportacion_qa(operacion(), "entrada-ajena", 1)

    def test_contradiccion_documental_no_se_promueve_a_apta(self):
        e = entrada(recurso=replace(entrada().recurso, contradicciones_declaradas=("declaracion-fixture",)))
        self.assertIs(e.estado, EstadoAdaptacion.CONTRADICTORIO)
        with self.assertRaises(ValueError):
            contexto_exportacion_qa(operacion(e), e.entrada_id, 1)

    def test_resultado_real_nativo_se_conserva_por_referencia_y_restricciones(self):
        e = entrada()
        r = resultado(e)
        v = VinculoResultadoQA(iniciada(operacion(e)), e.entrada_id, "resultado-1", r)
        self.assertIs(v.resultado, r)
        self.assertTrue(set(restricciones_resultado(r)).issubset(v.restricciones))
        self.assertIn(BLOQUEO, v.restricciones)
        self.assertFalse(v.autoriza_operacion)
        with self.assertRaises(TypeError):
            bool(v)
        with self.assertRaises(FrozenInstanceError):
            v.resultado = resultado()

    def test_no_vincula_resultado_antes_de_inicio_declarado(self):
        with self.assertRaisesRegex(ValueError, "antes_de_inicio"):
            VinculoResultadoQA(operacion(), "entrada-1", "r", resultado())

    def test_procedencia_de_otro_recurso_hash_o_activo_rechazada(self):
        r = resultado()
        for kw in ({"recurso_id": "otro"}, {"fuente": Fuente("otra", "fuente")},
                   {"sha256_referencia": "0" * 64}, {"asset_id": "otro"}):
            with self.subTest(kw=kw), self.assertRaisesRegex(ValueError, "procedencia_qa"):
                VinculoResultadoQA(iniciada(), "entrada-1", "r", replace(r, procedencia=replace(r.procedencia, **kw)))

    def test_procedencia_original_del_registro_contradictoria(self):
        r = resultado()
        local = ProcedenciaLocal(FUENTE, "recurso-ajeno", "activo-inventado")
        r = replace(r, registro=replace(r.registro, procedencia_original=local))
        with self.assertRaisesRegex(ValueError, "procedencia_original"):
            VinculoResultadoQA(iniciada(), "entrada-1", "r", r)

    def test_resultado_regla_fuera_de_configuracion_rechazado(self):
        r = resultado(configuracion=ConfiguracionQA(reglas=("L0-VAL-001",)))
        with self.assertRaisesRegex(ValueError, "regla_fuera"):
            VinculoResultadoQA(iniciada(), "entrada-1", "r", r)

    def test_resultado_mal_tipado_no_se_acepta_por_ser_dataclass(self):
        for kw in ({"procedencia": None}, {"registro": None}, {"estado": "completa"}):
            with self.subTest(kw=kw), self.assertRaises(TypeError):
                VinculoResultadoQA(iniciada(), "entrada-1", "r", replace(resultado(), **kw))

    def test_resultado_incompleto_no_cierra_y_se_conserva_como_parcial(self):
        r = replace(resultado(), estado=EstadoResultadoQA.EVALUACION_INCOMPLETA)
        c = cambiar_estado(iniciada(), E.CONCLUIDA, referencias_resultado=("r",))
        with self.assertRaisesRegex(ValueError, "incompleto"):
            VinculoResultadoQA(c, "entrada-1", "r", r)
        p = cambiar_estado(iniciada(), E.PARCIAL, referencias_resultado=("r",), diagnosticos=(CAUSA,))
        v = VinculoResultadoQA(p, "entrada-1", "r", r)
        validar_vinculos_qa(p, (v,))
        self.assertIn("condicion_incompleta", [x.codigo for x in v.restricciones])

    def test_restriccion_qa_nativa_no_se_rebaja_desde_proyecto(self):
        nativa = restricciones_resultado(resultado())[1]
        alterada = replace(nativa, tipo=TipoRestriccionQA.INFORMATIVA, operaciones=())
        p = proyecto(restricciones=(alterada,))
        e = entrada(p)
        with self.assertRaisesRegex(ValueError, "restriccion_contextual_contradictoria"):
            VinculoResultadoQA(iniciada(operacion(e)), e.entrada_id, "r", resultado(e))

    def test_cierre_rechaza_referencia_ajena_o_omitida(self):
        c = cambiar_estado(iniciada(), E.CONCLUIDA, referencias_resultado=("r",))
        with self.assertRaisesRegex(ValueError, "ajeno_al_cierre"):
            VinculoResultadoQA(c, "entrada-1", "otro", resultado())
        with self.assertRaisesRegex(ValueError, "referencias_no_corresponden"):
            validar_vinculos_qa(c, ())

    def test_resultado_asociado_a_otro_proyecto_u_operacion(self):
        a, b = entrada(), entrada(proyecto("proyecto-B", "contexto-B"))
        oa, ob = iniciada(operacion(a)), iniciada(operacion(b))
        v = VinculoResultadoQA(ob, b.entrada_id, "r", resultado(b))
        with self.assertRaisesRegex(ValueError, "otro_contexto_u_operacion"):
            validar_vinculos_qa(oa, (v,))
        v = VinculoResultadoQA(iniciada(operacion(a, operacion_id="otra")), a.entrada_id, "r", resultado(a))
        with self.assertRaises(ValueError):
            validar_vinculos_qa(oa, (v,))

    def test_colision_de_referencias_y_diagnosticos_no_duplica_conteos(self):
        o = iniciada()
        a = VinculoResultadoQA(o, "entrada-1", "r", resultado())
        with self.assertRaisesRegex(ValueError, "referencia_resultado_duplicada"):
            validar_vinculos_qa(o, (a, a))
        b = VinculoResultadoQA(o, "entrada-1", "otro-id", a.resultado)
        with self.assertRaisesRegex(ValueError, "diagnostico_qa_duplicado"):
            validar_vinculos_qa(o, (a, b))

    def test_misma_posicion_con_contenido_o_lineas_distintos_es_conflicto(self):
        o = iniciada()
        r = resultado()
        a = VinculoResultadoQA(o, "entrada-1", "r", r)
        otros = (replace(r.registro, estacion_literal="otra-estacion-ficticia"),
                 replace(r.registro, linea_inicial=3, linea_final=3))
        for registro in otros:
            b = VinculoResultadoQA(o, "entrada-1", "r2", replace(r, registro=registro))
            with self.subTest(registro=registro.numero_registro), self.assertRaisesRegex(ValueError, "descripciones_distintas"):
                validar_vinculos_qa(o, (a, b))

    def test_posicion_original_debe_ser_explicita_y_valida(self):
        for n in (0, -1, True, "1"):
            with self.subTest(posicion=n), self.assertRaises(ValueError):
                contexto_exportacion_qa(operacion(), "entrada-1", n)

    def test_cotas_de_resultados_registros_y_referencias(self):
        o = iniciada(operacion(limites_qa=LimitesQA(max_registros=1, max_resultados=2)))
        a = VinculoResultadoQA(o, "entrada-1", "r1", resultado(numero=1))
        b = VinculoResultadoQA(o, "entrada-1", "r2", resultado(numero=2))
        with self.assertRaisesRegex(ValueError, "registros_superan_presupuesto"):
            validar_vinculos_qa(o, (a, b))
        o = iniciada(operacion(limites_qa=LimitesQA(max_resultados=1)))
        a = replace(a, operacion=o)
        b = replace(b, operacion=o)
        with self.assertRaises(ValueError):
            validar_vinculos_qa(o, (a, b))
        c = replace(proyecto().configuracion, max_referencias_resultado=1)
        o = iniciada(operacion(entrada(proyecto(configuracion=c))))
        with self.assertRaises(ValueError):
            cambiar_estado(o, E.CONCLUIDA, referencias_resultado=("a", "b"))


class IntegracionTransversalRC1Tests(unittest.TestCase):
    def test_dos_filas_se_exportan_y_consumen_con_identidades_distintas(self):
        o = iniciada()
        vs = tuple(VinculoResultadoQA(o, "entrada-1", "ref-" + str(n), resultado(numero=n))
                   for n in (1, 2))
        validar_vinculos_qa(o, vs)
        textos = tuple(exportar_resultado_json(v.resultado, v.contexto_exportacion) for v in vs)
        consumo = consumir_exportaciones(textos)
        self.assertIs(consumo.estado, EstadoConsumoQA.CONTRATO_VALIDO_EN_ALCANCE)
        self.assertEqual(consumo.diagnosticos_aceptados, 2)
        self.assertEqual(tuple(v.contexto_exportacion.entrada_id for v in vs), ("entrada-1:1", "entrada-1:2"))
        self.assertEqual(len({json.loads(t)["resultado_id"] for t in textos}), 2)

    def test_dos_proyectos_dos_operaciones_mismo_contenido_y_linaje_no_alineado(self):
        a, b = entrada(), entrada(proyecto("proyecto-B", "contexto-B"))
        oa1, oa2, ob = (iniciada(operacion(a, "operacion-1")), iniciada(operacion(a, "operacion-2")),
                       iniciada(operacion(b, "operacion-1")))
        self.assertEqual(validar_relaciones((a.proyecto, b.proyecto), (a, b), (oa1, oa2, ob)), ())
        documentos, nativos, vinculos, consumos = [], [], [], []
        for o in (oa1, oa2, ob):
            e = o.entradas[0]
            # Participa realmente el generador QA0; no se fabrica un ResultadoQA.
            r = resultado(e, configuracion=o.configuracion_qa)
            c = cambiar_estado(o, E.CONCLUIDA, referencias_resultado=("diagnostico-1",))
            v = VinculoResultadoQA(c, e.entrada_id, "diagnostico-1", r)
            validar_vinculos_qa(c, (v,))
            texto = exportar_resultado_json(v.resultado, v.contexto_exportacion)
            consumo = consumir_exportaciones((texto,))
            self.assertIs(consumo.estado, EstadoConsumoQA.CONTRATO_VALIDO_EN_ALCANCE)
            self.assertIn(BLOQUEO, v.restricciones)
            documentos.append(json.loads(texto))
            nativos.append(r)
            vinculos.append(v)
            consumos.append(consumo)
        self.assertEqual(nativos[0], nativos[1])
        self.assertEqual(nativos[0], nativos[2])
        self.assertEqual(len({d["resultado_id"] for d in documentos}), 3)
        for c in consumos[1:]:
            informe = conciliar_lotes((LoteQA("A", consumos[0]), LoteQA("B", c)))
            self.assertIs(informe.estado, EstadoConciliacionQA.NO_COMPARABLE)
            self.assertEqual(informe.coincidencias, ())
        self.assertEqual(a.sha256_declarado, b.sha256_declarado)
        self.assertIs(vinculos[0].resultado, nativos[0])
        # El JSON estable transporta las restricciones QA nativas, no las RC1 nuevas.
        self.assertNotIn("bloqueo-fixture", [r["codigo"] for r in documentos[0]["restricciones"]["bloqueantes"]])
        self.assertIn("sin_validacion_cientifica", [r["codigo"] for r in documentos[0]["restricciones"]["bloqueantes"]])

    def test_resultado_anterior_y_json_no_mutan_y_exportacion_es_determinista(self):
        r = resultado()
        c = ContextoExportacionQA("espacio-previo", "evaluacion-previa", "entrada-previa")
        previo = exportar_resultado_json(r, c)
        v = VinculoResultadoQA(iniciada(), "entrada-1", "r", r)
        self.assertIs(v.resultado, r)
        self.assertEqual(exportar_resultado_json(r, c), previo)
        self.assertEqual(exportar_resultado_json(r, v.contexto_exportacion),
                         exportar_resultado_json(r, v.contexto_exportacion))
        self.assertEqual(json.loads(previo)["version_esquema"], "0.1.0")
        self.assertEqual(tuple(f.name for f in fields(ResultadoQA)), (
            "regla", "registro", "procedencia", "valores_originales", "evidencia",
            "parametros", "estado", "diagnostico", "version_contrato"))
        self.assertEqual(dict(r.registro.campos_originales)["HORA"], "10000")
        self.assertEqual(dict(r.registro.campos_originales)["UBIGEO"], "01234.0")

    def test_importaciones_y_composicion_sin_red_escrituras_o_sqlite(self):
        # Auditoría del proceso hijo antes de importar SPICA; incluye red, SQLite y
        # cualquier apertura de escritura. No necesita abrir siquiera un TEMP.
        codigo = r'''
import os, sys
def denegar(evento, argumentos):
    if evento.startswith('socket.') or evento in ('sqlite3.connect', 'os.mkdir', 'os.remove', 'os.rename'):
        raise AssertionError('efecto_no_permitido_rc1')
    if evento == 'open':
        modo, flags = argumentos[1:3]
        if (isinstance(modo, str) and any(c in modo for c in 'wax+')) or (
            isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC)):
            raise AssertionError('escritura_no_permitida_rc1')
sys.addaudithook(denegar)
sys.path[:0] = ['src', 'tests']
IMPORTACION_PREVIA
from test_contextos_rc1 import entrada, iniciada, operacion, resultado
from spica.contextos import VinculoResultadoQA, validar_vinculos_qa
from spica.calidad.exportacion import exportar_resultado_json
o = iniciada(operacion(entrada()))
v = VinculoResultadoQA(o, 'entrada-1', 'r', resultado())
validar_vinculos_qa(o, (v,))
assert exportar_resultado_json(v.resultado, v.contexto_exportacion)
assert not v.autoriza_operacion
print('RC1_sin_efectos')
'''
        for previa in ("import spica.contextos", "import spica.calidad; import spica.interoperabilidad"):
            with self.subTest(orden=previa):
                r = subprocess.run([sys.executable, "-B", "-c", codigo.replace("IMPORTACION_PREVIA", previa)],
                    cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, timeout=30)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertEqual(r.stdout.strip(), "RC1_sin_efectos")


if __name__ == "__main__":
    unittest.main()
