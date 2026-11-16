"""RC7: composición y QA nativos sobre copias inventadas, sin datos operativos."""

from contextlib import contextmanager
from dataclasses import FrozenInstanceError, replace
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
from threading import Event
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from spica.adquisicion.almacenamiento.modelos import ObjetoCientifico
from spica.adquisicion.consultas_locales import ENCABEZADO_SENAMHI
from spica.adquisicion.readquisicion.modelos import EstadoLocal as L
from spica.adquisicion.verificacion import LectorCSV
from spica.artefactos import DescriptorArtefacto, EstadoArtefacto as A, InventarioArtefactos, ReferenciaArtefacto, TipoArtefacto as T
from spica.artefactos.coordinacion import (
    VERSION_INTEGRACION, SolicitudIntegracion, VinculoEntradaRecuperada as V,
    inspeccionar_integracion,
)
from spica.artefactos.conservacion import (
    ControlGeneracion, EstadoRecuperacion as R, UnidadConservacion,
    entorno_conservacion, recuperar_generacion,
)
from spica.artefactos._generacion_rc6 import ArchivosGeneracion
from spica.artefactos.materializacion import SolicitudMaterializacion, entorno_materializacion
from spica.calidad import EvaluadorNivel0, ConfiguracionQA, LimitesQA, ProcedenciaQA
from spica.calidad.exportacion import exportar_resultado_json
from spica.calidad.modelos import EstadoEvaluacionQA
from spica.calidad.restricciones import RestriccionQA, TipoRestriccionQA as TR
from spica.contextos import ContextoOperacion, EstadoOperacion as S, TipoOperacion as TO, VinculoResultadoQA, cambiar_estado, PERFIL_QA0
from spica.coordinacion import CierreQA, ComposicionOperaciones, DependenciaOperacion as Dep, LimitesComposicion, NodoOperacion, RequisitoCompatibilidad
from spica.interoperabilidad.adaptadores import DiagnosticoAdaptacion as D, NivelDiagnostico as N
from spica.interoperabilidad.modelos import EstadoAptitud as E
from spica.interoperabilidad.perfiles import EntradaPerfil, CampoInformacion, DeclaracionPerfil, PerfilInformacion, AspectoCampo
# Solo fabricantes; nunca se importan TestCase ni se abren archivos institucionales.
from test_artefactos_rc4 import produccion, composicion as composicion_historica
from test_contextos_rc1 import entrada as entrada_base, proyecto
from test_perfiles_informacion_rc2 import declarado, finalidad as finalidad_perfiles

FILA = ("fila-inventada-rc7", "estacion-ficticia", "20260101", "10000", "", "", "",
    "1.00", "2.00", "0.0", "red-ficticia", "", "", "", "01234.0", "20260102")
_texto_csv = io.StringIO(newline="")
_escritor_csv = csv.writer(_texto_csv)
_escritor_csv.writerow(ENCABEZADO_SENAMHI)
_escritor_csv.writerow(FILA)
CUERPO = _texto_csv.getvalue().encode("utf-8")
SHA = hashlib.sha256(CUERPO).hexdigest()
BLOQUEO = RestriccionQA("bloqueo-descriptor-rc7", TR.BLOQUEO_USO_DEL_RESULTADO,
    ("acreditar_ciencia",), "Fixture: conserva la limitacion cientifica")


def inventario_piloto(*, estado=S.PARCIAL, variante=None, sin_sha=False):
    pa, pb = proyecto(), proyecto("proyecto-B", "contexto-B", restricciones=())
    def entrada(p, nombre, conocido=True):
        return entrada_base(p, entrada_id="entrada-" + nombre,
            objeto=ObjetoCientifico("objeto-" + nombre, p.project_id), revision="r1",
            version_contenido="fixture-rc7", sha256_declarado=SHA if conocido and not (sin_sha and nombre=="original-A") else None,
            size_bytes_declarado=len(CUERPO) if conocido else None)
    def perfil(version, tipo=None):
        return PerfilInformacion(PERFIL_QA0, version, "tabla-sintetica", (
            CampoInformacion("ID", DeclaracionPerfil() if tipo == "pendiente" else declarado(tipo or "texto-ficticio")),),
            ambito=declarado("solo fixture RC7"))
    e1, eb, ec, ep, ed = (entrada(pa, "original-A"), entrada(pb, "original-B"),
        entrada(pa, "copia-A"), entrada(pa, "preparado", False), entrada(pa, "derivado", False))
    p1, p2 = perfil("fixture-1"), perfil("fixture-2", variante)
    original = DescriptorArtefacto(EntradaPerfil(e1, p1), T.ORIGINAL, "contenido-compartido", restricciones_adicionales=(BLOQUEO,))
    otro = DescriptorArtefacto(EntradaPerfil(eb, p1), T.ORIGINAL, "contenido-compartido")
    copia = DescriptorArtefacto(EntradaPerfil(ec, p2), T.ORIGINAL, "contenido-compartido")
    preparado = DescriptorArtefacto(EntradaPerfil(ep, p1), T.PREPARADO, "contenido-preparado")
    derivado = DescriptorArtefacto(EntradaPerfil(ed, p1), T.DERIVADO, "contenido-derivado", estado_logico=A.PARCIAL)
    prep = produccion((original,), (preparado,), estado=S.CONCLUIDA)
    der = produccion((preparado,), (derivado,), "derivar", estado=estado)
    independiente = NodoOperacion(ContextoOperacion("independiente", pa, (ec,), TO.DESCRIPCION_ESTRUCTURAL,
        "Inspeccionar una copia sintetica"), ("describir-fixture",))
    hist = composicion_historica((prep, der), dependencias=(Dep("preparar", "derivar"),))
    hist = replace(hist, operaciones=hist.operaciones + (independiente,))
    return InventarioArtefactos((original, otro, copia, preparado, derivado), (prep, der), (hist,))


def conservar(m, c, *, externos=(), **kw):
    inv = inventario_piloto(**kw)
    informes = tuple(m.materializar_sintetico(SolicitudMaterializacion(inv, a.referencia, len(CUERPO)),
        (CUERPO,)) for i, a in enumerate(inv.artefactos) if i not in externos)
    u = UnidadConservacion(inv, informes, tuple(a.referencia for i, a in enumerate(inv.artefactos) if i in externos))
    return c.conservar(u)


@contextmanager
def escenario(**kw):
    with entorno_materializacion() as m, entorno_conservacion() as c:
        yield conservar(m, c, **kw), c, m


def qa_genuino(r, raiz, *, parcial=False):
    """El motor existente LEE la copia realmente conservada, no otra fixture."""
    a = r.unidad.inventario.artefactos[0]
    e = a.entrada_perfil.entrada
    v = next(v for v in r.contenidos if v.artefacto == a.referencia)
    cfg, limites = ConfiguracionQA(reglas=("L0-EST-001",)), LimitesQA(max_registros=4, max_resultados=1 if parcial else 8)
    o = ContextoOperacion("qa-previo", e.proyecto, (e,), TO.QA_NIVEL0, "Comprobar fixture RC7",
        limites_qa=limites, configuracion_qa=cfg)
    o = cambiar_estado(cambiar_estado(o, S.PLANIFICADA), S.INICIADA)
    proc = ProcedenciaQA(e.recurso.identidad.fuente, e.recurso.identidad.recurso_id,
        asset_id=e.asset_id, sha256_referencia=e.sha256_declarado)
    lector = LectorCSV(raiz / v.relativa, codificacion="utf-8", delimitador=",",
        encabezado_declarado=True, campos_esperados=16)
    with EvaluadorNivel0(lector, proc, configuracion=cfg, limites=limites) as ev:
        resultados = tuple(ev)
    refs = tuple("resultado-" + str(i) for i in range(len(resultados)))
    o = cambiar_estado(o, S.PARCIAL if parcial else S.CONCLUIDA,
        diagnosticos=(D("prefijo_qa", "fixture", N.FALTANTE),) if parcial else (), referencias_resultado=refs)
    vs = tuple(VinculoResultadoQA(o, e.entrada_id, ref, res) for ref, res in zip(refs, resultados))
    return NodoOperacion(o, ("evaluar_estructura_qa0",), cierre_qa=CierreQA(ev.informe, vs))


def candidata(r, qa=None):
    inv = r.unidad.inventario
    a, _, b = inv.artefactos[:3]
    e1, e2 = a.entrada_perfil.entrada, b.entrada_perfil.entrada
    if qa is None:
        o = ContextoOperacion("qa-previo", e1.proyecto, (e1,), TO.QA_NIVEL0, "Comprobar fixture RC7",
            limites_qa=LimitesQA(max_registros=4, max_resultados=8), configuracion_qa=ConfiguracionQA(reglas=("L0-EST-001",)))
        qa = NodoOperacion(o, ("evaluar_estructura_qa0",))
    f = finalidad_perfiles(campos=(("ID", "ID"),), versiones_admitidas=((PERFIL_QA0, "fixture-1"),
        (PERFIL_QA0, "fixture-2")), aspectos=(AspectoCampo.TIPO,))
    o = ContextoOperacion("comparar", e1.proyecto, (e1, e2), TO.DESCRIPCION_ESTRUCTURAL, f.descripcion)
    comparar = NodoOperacion(o, (f.identificador,), (RequisitoCompatibilidad(a.entrada_perfil, b.entrada_perfil, f),))
    hist = inv.composiciones[0]
    dep = Dep(qa.contexto.operacion_id, "comparar", qa.contexto.referencias_resultado[:1])
    return ComposicionOperaciones("composicion-rc7", e1.proyecto, hist.operaciones + (qa, comparar),
        hist.dependencias + (dep,), "Inspeccion de consumidores sinteticos RC7")


def vinculos(r, c):
    ars = {a.entrada_perfil.entrada.entrada_id: a.referencia for a in r.unidad.inventario.artefactos}
    return tuple(V(n.contexto.operacion_id, e.entrada_id, ars[e.entrada_id]) for n in c.operaciones for e in n.contexto.entradas)


def solicitud(r, c=None, **kw):
    c = candidata(r) if c is None else c
    d = dict(recuperacion=r, composicion=c, vinculos=vinculos(r, c), finalidad="Inspeccion sintetica RC7")
    d.update(kw)
    return SolicitudIntegracion(**d)


def codigos(r):
    return [d.codigo for d in r.diagnosticos] + [d.codigo for a in r.relaciones for d in a.diagnosticos] + ([] if r.coordinacion_integrada is None else [
        d.codigo for i in r.coordinacion_integrada.operaciones for d in i.diagnosticos])


def nodo(r, identidad):
    return next(i for i in r.coordinacion_integrada.operaciones if i.nodo.contexto.operacion_id == identidad)


LECTOR = r'''
import json, os, sys
def barrera(evento, args):
    if evento.startswith("socket.") or evento == "sqlite3.connect":
        raise RuntimeError("efecto_prohibido_rc7")
    if evento == "open":
        p, modo, banderas = args
        if "spica_datos" in str(p).casefold():
            raise RuntimeError("acceso_operativo_prohibido")
        if (isinstance(modo,str) and any(x in modo for x in "wax+")) or (banderas & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)):
            raise RuntimeError("escritura_prohibida_rc7")
    if evento in ("os.mkdir","os.remove","os.rmdir","os.rename","os.link","os.symlink","os.chmod"):
        raise RuntimeError("mutacion_prohibida_rc7")
sys.addaudithook(barrera)
from spica.artefactos.conservacion import ControlGeneracion, recuperar_generacion
from spica.artefactos.coordinacion import SolicitudIntegracion,VinculoEntradaRecuperada,inspeccionar_integracion
r=recuperar_generacion(sys.argv[1],ControlGeneracion(*json.loads(sys.argv[2])))
inv=r.unidad.inventario
c=inv.composiciones[0]
ars={a.entrada_perfil.entrada.entrada_id:a.referencia for a in inv.artefactos}
vs=tuple(VinculoEntradaRecuperada(n.contexto.operacion_id,e.entrada_id,ars[e.entrada_id]) for n in c.operaciones for e in n.contexto.entradas)
v=inspeccionar_integracion(SolicitudIntegracion(r,c,vs,"Inspeccion independiente RC7"))
print(json.dumps(dict(generacion=v.control.generacion_id,habilitadas=v.habilitadas_declarativamente,
    proyectos=[a.entrada_perfil.entrada.proyecto.project_id for a in inv.artefactos],
    artefactos=[[a.referencia.object_id,a.referencia.revision,a.estado_logico.value] for a in inv.artefactos],
    operaciones=[[i.nodo.contexto.operacion_id,i.nodo.contexto.estado.value,i.cierre_qa_coherente_completo] for i in v.coordinacion_integrada.operaciones],
    restricciones=[[p.restriccion.codigo for p in i.restricciones] for i in v.coordinacion_integrada.operaciones],
    hashes=[x.sha256_fisico for x in r.contenidos],ejecucion=v.ejecucion_realizada,
    cotejo_fisico=v.comprobacion_fisica_realizada,autoriza=v.autoriza_operacion)))
'''


def lector_independiente(raiz, control):
    p = subprocess.run([sys.executable, "-B", "-c", LECTOR, str(raiz),
        json.dumps([control.generacion_id, control.manifiesto_sha256])], check=True, capture_output=True, text=True, timeout=45)
    return json.loads(p.stdout)


class IntegracionArtefactosRC7Tests(unittest.TestCase):
    def test_piloto_qa_genuino_satisface_solo_dependencia_admisible(self):
        with escenario() as (r,c,m):
            qa = qa_genuino(r,c.raiz)
            v = inspeccionar_integracion(solicitud(r, candidata(r,qa)))
            self.assertEqual(set(v.habilitadas_declarativamente), {"independiente", "comparar"})
            self.assertTrue(nodo(v,"qa-previo").cierre_qa_coherente_completo)
            self.assertIs(v.inspeccion_rc3.operaciones[-1].nodo, v.coordinacion_integrada.operaciones[-1].nodo)
            self.assertEqual([(d.predecesora, e) for d,e in v.dependencias],
                [("preparar", E.PENDIENTE_DE_EVIDENCIA),("qa-previo", E.APTO_ESTRUCTURALMENTE)])
            self.assertEqual(qa.cierre_qa.informe.registros_finalizados,1)
            self.assertEqual(qa.cierre_qa.informe.motivo_fin,"eof")
            self.assertFalse(v.autoriza_operacion)
            self.assertFalse(v.ejecucion_realizada)
            self.assertFalse(v.comprobacion_fisica_realizada)
            with self.assertRaises(TypeError): bool(v)

    def test_descriptor_y_sha_correcto_no_fabrican_qa(self):
        with escenario() as (r,c,m):
            v = inspeccionar_integracion(solicitud(r))
            self.assertFalse(nodo(v,"qa-previo").cierre_qa_coherente_completo)
            self.assertNotIn("comparar",v.habilitadas_declarativamente)
            self.assertIn("rc6_no_aporta_cierre_qa_nativo",codigos(v))
            self.assertTrue(all(x.estado_actual is L.INTEGRO for x in r.contenidos))

    def test_conclusion_descriptiva_no_satisface_dependencia(self):
        with escenario() as (r,c,m):
            v = inspeccionar_integracion(solicitud(r))
            self.assertEqual(nodo(v,"preparar").nodo.contexto.estado,S.CONCLUIDA)
            self.assertFalse(nodo(v,"preparar").cierre_qa_coherente_completo)
            self.assertIn("conclusion_declarada_sin_cierre_tecnico_admitido",codigos(v))

    def test_parcial_fallida_y_cancelada_permanecen(self):
        for estado in (S.PARCIAL,S.FALLIDA,S.CANCELADA):
            with self.subTest(estado=estado), escenario(estado=estado) as (r,c,m):
                v = inspeccionar_integracion(solicitud(r))
                self.assertEqual(nodo(v,"derivar").nodo.contexto.estado,estado)
                self.assertNotIn("derivar",v.habilitadas_declarativamente)
                self.assertEqual(v.linaje.inventario.artefactos[-1].estado_logico,A.PARCIAL)

    def test_identidades_y_sha_compartido_no_fusionan_proyectos(self):
        with escenario() as (r,c,m):
            v = inspeccionar_integracion(solicitud(r))
            self.assertEqual(v.control,r.control)
            self.assertEqual(v.linaje.inventario,r.unidad.inventario)
            self.assertNotEqual(v.linaje.artefactos[0].descriptor.referencia,v.linaje.artefactos[1].descriptor.referencia)
            self.assertEqual(r.contenidos[0].sha256_fisico,r.contenidos[1].sha256_fisico)
            self.assertEqual(v.fecha_comprobacion_fisica_aportada,r.fecha_utc)

    def test_restriccion_del_descriptor_omitida_en_contexto_se_propaga(self):
        with escenario() as (r,c,m):
            qa = qa_genuino(r,c.raiz)
            comp = candidata(r,qa)
            ns = tuple(replace(n,usos_declarados=n.usos_declarados+("acreditar_ciencia",)) if n.contexto.operacion_id=="comparar" else n for n in comp.operaciones)
            comp = replace(comp,operaciones=ns)
            v = inspeccionar_integracion(solicitud(r,comp))
            self.assertIn("comparar",v.inspeccion_rc3.habilitadas_declarativamente)
            self.assertNotIn("comparar",v.habilitadas_declarativamente)
            self.assertIn("independiente",v.habilitadas_declarativamente)
            self.assertIn(BLOQUEO,tuple(p.restriccion for p in nodo(v,"comparar").restricciones))
            self.assertTrue(any("generacion:"+r.control.generacion_id in p.origenes for p in nodo(v,"comparar").restricciones if p.restriccion==BLOQUEO))

    def test_restriccion_con_usos_desconocidos_no_desaparece(self):
        with escenario() as (r,c,m):
            comp = candidata(r)
            comp = replace(comp,operaciones=tuple(replace(n,usos_declarados=None) if n.contexto.operacion_id=="qa-previo" else n for n in comp.operaciones))
            v = inspeccionar_integracion(solicitud(r,comp))
            self.assertIn("aplicabilidad_restriccion_recuperada_pendiente",codigos(v))
            self.assertNotIn("qa-previo",v.habilitadas_declarativamente)

    def test_conflicto_restricciones_no_se_rebaja(self):
        with escenario() as (r,c,m):
            comp = candidata(r)
            op = next(n.contexto for n in comp.operaciones if n.contexto.operacion_id=="qa-previo")
            op = replace(op,restricciones_adicionales=(replace(BLOQUEO,tipo=TR.INFORMATIVA),))
            comp = replace(comp,operaciones=tuple(replace(n,contexto=op) if n.contexto.operacion_id=="qa-previo" else n for n in comp.operaciones))
            v = inspeccionar_integracion(solicitud(r,comp))
            self.assertIn("restricciones_recuperadas_no_unificables",codigos(v))
            self.assertNotIn("qa-previo",v.habilitadas_declarativamente)
            self.assertIn(BLOQUEO,tuple(p.restriccion for p in nodo(v,"qa-previo").restricciones))

    def test_perfil_incompatible_y_pendiente_sin_ignorar_rc2(self):
        for variante, esperado in (("otro-tipo",E.INCOMPATIBLE),("pendiente",E.PENDIENTE_DE_EVIDENCIA)):
            with self.subTest(variante=variante), escenario(variante=variante) as (r,c,m):
                qa = qa_genuino(r,c.raiz)
                v = inspeccionar_integracion(solicitud(r,candidata(r,qa)))
                self.assertEqual(nodo(v,"comparar").compatibilidades[0].estado,esperado)
                self.assertNotIn("comparar",v.habilitadas_declarativamente)
                self.assertIn("independiente",v.habilitadas_declarativamente)

    def test_generacion_incompleta_no_habilita(self):
        with escenario() as (r,c,m):
            (c.raiz/"cierre.json").unlink()
            incompleta=recuperar_generacion(c.raiz,r.control)
            v=inspeccionar_integracion(solicitud(r,recuperacion=incompleta))
            self.assertEqual(v.habilitadas_declarativamente,())
            self.assertIn("generacion_no_verificada_en_alcance",codigos(v))
            self.assertEqual(v.estado_estructural,E.PENDIENTE_DE_EVIDENCIA)
            self.assertIn("inventario_recuperado_no_disponible_para_vincular",codigos(v))
            self.assertNotIn("artefacto_o_revision_vinculados_inexistentes",codigos(v))

    def test_archivo_corrupto_no_promueve_ningun_estado(self):
        with escenario() as (r,c,m):
            (c.raiz/"datos-000.bin").write_bytes(b"Z"*len(CUERPO))
            corrupta=recuperar_generacion(c.raiz,r.control)
            v=inspeccionar_integracion(solicitud(r,recuperacion=corrupta))
            self.assertEqual(v.habilitadas_declarativamente,())
            self.assertEqual(corrupta.estado,R.CORRUPTA)
            self.assertEqual(v.solicitud.recuperacion.contenidos[0].estado_actual,L.INCONSISTENTE)

    def test_archivo_incluido_ausente(self):
        with escenario() as (r,c,m):
            (c.raiz/"datos-000.bin").unlink()
            ausente=recuperar_generacion(c.raiz,r.control)
            v=inspeccionar_integracion(solicitud(r,recuperacion=ausente))
            self.assertEqual(v.habilitadas_declarativamente,())
            self.assertEqual(ausente.contenidos[0].estado_actual,L.AUSENTE)

    def test_externo_no_se_presenta_como_disponible(self):
        with escenario(externos=(0,)) as (r,c,m):
            v=inspeccionar_integracion(solicitud(r))
            self.assertIn("contenido_solo_referenciado_sin_comprobacion_actual",codigos(v))
            self.assertNotIn("qa-previo",v.habilitadas_declarativamente)
            self.assertIn("independiente",v.habilitadas_declarativamente)
            self.assertEqual(r.contenidos[-1].estado_actual,L.NO_DISPONIBLE)

    def test_operacion_inexistente_no_se_realinea(self):
        with escenario() as (r,c,m):
            s=solicitud(r)
            malo=replace(s.vinculos[0],operacion_id="operacion-ajena")
            v=inspeccionar_integracion(replace(s,vinculos=(malo,)+s.vinculos[1:]))
            self.assertIn("operacion_vinculada_inexistente_o_ambigua",codigos(v))
            self.assertEqual(v.habilitadas_declarativamente,())

    def test_artefacto_de_otro_proyecto_ni_sha_igual_lo_justifica(self):
        with escenario() as (r,c,m):
            s=solicitud(r)
            malo=replace(s.vinculos[0],artefacto=r.unidad.inventario.artefactos[1].referencia)
            v=inspeccionar_integracion(replace(s,vinculos=(malo,)+s.vinculos[1:]))
            self.assertIn("artefacto_recuperado_de_otro_proyecto",codigos(v))

    def test_revision_incompatible(self):
        with escenario() as (r,c,m):
            s=solicitud(r)
            malo=replace(s.vinculos[0],artefacto=replace(s.vinculos[0].artefacto,revision="r-no-conservada"))
            v=inspeccionar_integracion(replace(s,vinculos=(malo,)+s.vinculos[1:]))
            self.assertIn("artefacto_o_revision_vinculados_inexistentes",codigos(v))

    def test_operacion_productora_equivocada_rechazada(self):
        with escenario() as (r,c,m):
            comp=candidata(r)
            n=next(n for n in comp.operaciones if n.contexto.operacion_id=="preparar")
            nuevo=replace(n.contexto,proposito="otra definicion de productor")
            comp=replace(comp,operaciones=tuple(replace(x,contexto=nuevo) if x is n else x for x in comp.operaciones))
            v=inspeccionar_integracion(solicitud(r,comp))
            self.assertIn("operacion_recuperada_redefinida",codigos(v))

    def test_proyecto_incompatible(self):
        with escenario() as (r,c,m):
            comp=candidata(r)
            comp=replace(comp,proyecto=replace(comp.proyecto,contexto_id="contexto-no-conservado"))
            v=inspeccionar_integracion(solicitud(r,comp))
            self.assertIn("proyecto_de_composicion_no_corresponde_a_generacion",codigos(v))
            self.assertEqual(v.habilitadas_declarativamente,())

    def test_vinculo_duplicado_y_entrada_omitida(self):
        with escenario() as (r,c,m):
            s=solicitud(r)
            for vs,codigo in ((s.vinculos+(s.vinculos[0],),"vinculo_entrada_recuperada_duplicado"),
                    (s.vinculos[1:],"entrada_sin_vinculo_a_generacion")):
                with self.subTest(codigo=codigo):
                    v=inspeccionar_integracion(replace(s,vinculos=vs))
                    self.assertIn(codigo,codigos(v))

    def test_identidad_entrada_o_objeto_contradictoria(self):
        with escenario() as (r,c,m):
            s=solicitud(r)
            malo=replace(s.vinculos[0],entrada_id="entrada-ajena")
            v=inspeccionar_integracion(replace(s,vinculos=(malo,)+s.vinculos[1:]))
            self.assertIn("entrada_vinculada_no_pertenece_a_operacion",codigos(v))

    def test_qa_genuino_de_otra_identidad_no_se_adopta(self):
        with escenario() as (r,c,m):
            qa=qa_genuino(r,c.raiz)
            ajena=replace(qa.contexto,operacion_id="qa-ajena")
            comp=candidata(r,replace(qa,contexto=ajena))
            v=inspeccionar_integracion(solicitud(r,comp))
            self.assertIn("vinculo_qa_de_otra_operacion_o_instantanea",codigos(v))
            self.assertNotIn("comparar",v.habilitadas_declarativamente)

    def test_qa_con_conteos_o_eof_contradictorios(self):
        with escenario() as (r,c,m):
            qa=qa_genuino(r,c.raiz)
            for inf in (replace(qa.cierre_qa.informe,resultados_emitidos=2),replace(qa.cierre_qa.informe,motivo_fin="interrupcion")):
                q=replace(qa,cierre_qa=replace(qa.cierre_qa,informe=inf))
                v=inspeccionar_integracion(solicitud(r,candidata(r,q)))
                self.assertFalse(nodo(v,"qa-previo").cierre_qa_coherente_completo)
                self.assertNotIn("comparar",v.habilitadas_declarativamente)

    def test_qa_parcial_no_cierra_dependencia(self):
        with escenario() as (r,c,m):
            qa=qa_genuino(r,c.raiz,parcial=True)
            v=inspeccionar_integracion(solicitud(r,candidata(r,qa)))
            self.assertEqual(qa.cierre_qa.informe.estado,EstadoEvaluacionQA.INCOMPLETA)
            self.assertEqual(nodo(v,"qa-previo").nodo.contexto.estado,S.PARCIAL)
            self.assertNotIn("comparar",v.habilitadas_declarativamente)

    def test_concluida_sin_qa_nativo_no_satisface(self):
        with escenario() as (r,c,m):
            comp=candidata(r)
            q=next(n for n in comp.operaciones if n.contexto.operacion_id=="qa-previo")
            q=replace(q,contexto=replace(q.contexto,estado=S.CONCLUIDA,referencias_resultado=("declarado",)))
            comp=replace(comp,operaciones=tuple(q if n.contexto.operacion_id=="qa-previo" else n for n in comp.operaciones))
            v=inspeccionar_integracion(solicitud(r,comp))
            self.assertIn("conclusion_declarada_sin_cierre_tecnico_admitido",codigos(v))
            self.assertNotIn("comparar",v.habilitadas_declarativamente)

    def test_json_qa_y_valores_originales_intactos(self):
        with escenario() as (r,c,m):
            qa=qa_genuino(r,c.raiz)
            vi=qa.cierre_qa.vinculos[0]
            antes=exportar_resultado_json(vi.resultado,vi.contexto_exportacion)
            inspeccionar_integracion(solicitud(r,candidata(r,qa)))
            self.assertEqual(antes,exportar_resultado_json(vi.resultado,vi.contexto_exportacion))
            self.assertEqual(vi.resultado.registro.valores_csv_originales,FILA)

    def test_determinismo_sin_evento_y_sin_mutacion(self):
        with escenario() as (r,c,m):
            s=solicitud(r,candidata(r,qa_genuino(r,c.raiz)))
            a,b=inspeccionar_integracion(s),inspeccionar_integracion(s)
            self.assertEqual(a,b)
            self.assertIs(a.solicitud,s)
            self.assertIs(a.coordinacion_integrada.composicion,s.composicion)
            self.assertIs(a.coordinacion_integrada.operaciones[0].nodo,a.inspeccion_rc3.operaciones[0].nodo)
            self.assertTrue(set(a.habilitadas_declarativamente)<=set(a.inspeccion_rc3.habilitadas_declarativamente))

    def test_cancelacion_y_presupuestos_no_habilitan(self):
        with escenario() as (r,c,m):
            s=solicitud(r)
            e=Event();e.set()
            v=inspeccionar_integracion(s,cancelacion=e)
            self.assertTrue(v.cancelada)
            self.assertEqual(v.habilitadas_declarativamente,())
            for limites in (LimitesComposicion(max_visitas_descriptores=2),LimitesComposicion(max_bytes_texto=4),LimitesComposicion(max_operaciones=1)):
                v=inspeccionar_integracion(replace(s,limites=limites))
                self.assertEqual(v.habilitadas_declarativamente,())
                self.assertIsNone(v.inspeccion_rc3)
            for limites in (LimitesComposicion(max_profundidad=1),LimitesComposicion(max_registros_qa_declarados=1)):
                v=inspeccionar_integracion(replace(s,limites=limites))
                self.assertEqual(v.habilitadas_declarativamente,())
                self.assertIsNotNone(v.inspeccion_rc3)
            v=inspeccionar_integracion(replace(s,max_vinculos=1))
            self.assertIn("cota_vinculos_integracion_excedida",codigos(v))

    def test_version_desconocida_y_dto_inmutable(self):
        with escenario() as (r,c,m):
            s=solicitud(r)
            with self.assertRaises(ValueError): replace(s,version_contrato="futura")
            with self.assertRaises(FrozenInstanceError): s.finalidad="otra"
            object.__setattr__(r,"version_contrato","futura")  # Solo simulación del DTO adversarial.
            v=inspeccionar_integracion(s)
            self.assertIn("version_recuperacion_no_admitida",codigos(v))
            self.assertEqual(v.habilitadas_declarativamente,())

    def test_comprobacion_fisica_aportada_incoherente(self):
        with escenario() as (r,c,m):
            malo=replace(r,contenidos=(replace(r.contenidos[0],sha256_fisico="0"*64),)+r.contenidos[1:])
            v=inspeccionar_integracion(solicitud(malo))
            self.assertIn("comprobacion_rc6_incoherente",codigos(v))
            self.assertEqual(v.habilitadas_declarativamente,())

    def test_comprobaciones_duplicadas_no_se_deduplican_silenciosamente(self):
        with escenario() as (r,c,m):
            for comprobaciones in (r.contenidos+(r.contenidos[0],),()):
                malo=replace(r,contenidos=comprobaciones)
                v=inspeccionar_integracion(solicitud(malo))
                self.assertIn("inventario_comprobaciones_rc6_discrepante",codigos(v))
                self.assertEqual(v.habilitadas_declarativamente,())

    def test_linaje_cache_alterado_se_recalcula_sin_perder_restricciones(self):
        with escenario() as (r,c,m):
            original=r.unidad.linaje
            object.__setattr__(r.unidad,"_linaje",replace(original,diagnosticos=()))
            v=inspeccionar_integracion(solicitud(r))
            self.assertIn("linaje_recuperado_contradictorio",codigos(v))
            self.assertIn(BLOQUEO,tuple(p.restriccion for p in nodo(v,"qa-previo").restricciones))

    def test_perfil_del_consumidor_redefinido(self):
        with escenario() as (r,c,m):
            comp=candidata(r)
            n=next(n for n in comp.operaciones if n.contexto.operacion_id=="comparar")
            req=n.compatibilidades[0]
            ep=replace(req.primero,perfil=replace(req.primero.perfil,version="revision-no-conservada"))
            comp=replace(comp,operaciones=tuple(replace(x,compatibilidades=(replace(req,primero=ep),)) if x is n else x for x in comp.operaciones))
            v=inspeccionar_integracion(solicitud(r,comp))
            self.assertIn("perfil_recuperado_redefinido",codigos(v))

    def test_grafo_invalido_se_conserva_sin_segundo_orden(self):
        with escenario() as (r,c,m):
            comp=candidata(r)
            comp=replace(comp,dependencias=comp.dependencias+(Dep("derivar","preparar"),))
            v=inspeccionar_integracion(solicitud(r,comp))
            self.assertEqual(v.inspeccion_rc3.orden_precedencia,())
            self.assertEqual(v.coordinacion_integrada.orden_precedencia,())
            self.assertEqual(v.habilitadas_declarativamente,())
            self.assertIn("dependencia_circular",codigos(v))

    def test_dependencia_exige_referencia_real_del_cierre(self):
        with escenario() as (r,c,m):
            comp=candidata(r,qa_genuino(r,c.raiz))
            comp=replace(comp,dependencias=(comp.dependencias[0],Dep("qa-previo","comparar",("resultado-no-emitido",))))
            v=inspeccionar_integracion(solicitud(r,comp))
            self.assertEqual(v.dependencias[-1][1],E.INCOMPATIBLE)
            self.assertNotIn("comparar",v.habilitadas_declarativamente)

    def test_adaptador_no_invoca_hash_archivos_qa_transporte_o_sqlite(self):
        with escenario() as (r,c,m):
            s=solicitud(r)
            with patch("builtins.open",side_effect=AssertionError("E/S prohibida")),patch("sqlite3.connect",side_effect=AssertionError("SQLite")),patch("socket.socket",side_effect=AssertionError("red")),patch.object(EvaluadorNivel0,"__init__",side_effect=AssertionError("QA automatico")):
                v=inspeccionar_integracion(s)
            self.assertFalse(v.comprobacion_fisica_realizada)
            self.assertFalse(v.ejecucion_realizada)

    def test_hash_fisico_no_se_afirma_vigente_despues_de_retirar_raiz(self):
        with escenario() as (r,c,m):
            s=solicitud(r)
            fecha=r.fecha_utc
        # No vuelve a abrir ni recrea la raíz retirada; el informe es evidencia a fecha.
        v=inspeccionar_integracion(s)
        self.assertEqual(v.fecha_comprobacion_fisica_aportada,fecha)
        self.assertFalse(v.comprobacion_fisica_realizada)
        self.assertFalse(c.raiz.exists())

    def test_proceso_lector_con_barrera_y_otra_raiz_temp(self):
        codigo='''
import json
from test_integracion_artefactos_rc7 import conservar
from spica.artefactos.materializacion import entorno_materializacion
from spica.artefactos.conservacion import entorno_conservacion
with entorno_conservacion(disponer_al_salir=False) as c:
    with entorno_materializacion() as m:
        r=conservar(m,c)
    print(json.dumps(dict(raiz=str(c.raiz),control=[r.control.generacion_id,r.control.manifiesto_sha256],nombres=sorted(p.name for p in c.raiz.iterdir()))))
'''
        p=subprocess.run([sys.executable,"-B","-c",codigo],capture_output=True,text=True,check=True,timeout=60)
        d=json.loads(p.stdout);raiz=Path(d["raiz"]);control=ControlGeneracion(*d["control"])
        def disponer():
            fs=ArchivosGeneracion.abrir(raiz)
            self.assertEqual(list(fs.nombres()),d["nombres"])
            for n in d["nombres"]:
                fs.regular(n)[0].unlink()
            fs.validar();fs.raiz.rmdir()
        try:
            b=lector_independiente(raiz,control)
            self.assertEqual(b["generacion"],control.generacion_id)
            self.assertEqual(b["habilitadas"],["independiente"])
            self.assertEqual(b["hashes"],[SHA]*5)
            self.assertFalse(b["ejecucion"])
            self.assertFalse(b["autoriza"])
            self.assertIn("proyecto-B",b["proyectos"])
            with entorno_conservacion() as destino:
                destino.copiar_de(raiz,control)
                disponer();raiz=None
                self.assertEqual(lector_independiente(destino.raiz,control),b)
        finally:
            if raiz is not None: disponer()

    def test_dependencia_historica_omitida_no_reescribe_linaje(self):
        with escenario() as (r,c,m):
            comp=candidata(r)
            comp=replace(comp,dependencias=comp.dependencias[1:])
            v=inspeccionar_integracion(solicitud(r,comp))
            self.assertIn("dependencia_historica_omitida_o_redefinida",codigos(v))
            self.assertEqual(v.linaje.inventario.composiciones[0].dependencias,r.unidad.inventario.composiciones[0].dependencias)
            self.assertEqual(nodo(v,"derivar").estado_estructural,E.INCOMPATIBLE)

    def test_qa_coherente_sin_sha_no_prueba_lectura_de_esos_bytes(self):
        with escenario(sin_sha=True) as (r,c,m):
            qa=qa_genuino(r,c.raiz)
            v=inspeccionar_integracion(solicitud(r,candidata(r,qa)))
            self.assertTrue(nodo(v,"qa-previo").cierre_qa_coherente_completo)
            self.assertIn("qa_sin_vinculo_hash_contenido_recuperado",codigos(v))
            self.assertNotIn("comparar",v.habilitadas_declarativamente)
            self.assertIsNone(qa.cierre_qa.informe.procedencia.sha256_referencia)

    def test_bloqueo_en_qa_cerrada_bloquea_dependiente(self):
        with escenario() as (r,c,m):
            qa=qa_genuino(r,c.raiz)
            qa=replace(qa,usos_declarados=qa.usos_declarados+("acreditar_ciencia",))
            v=inspeccionar_integracion(solicitud(r,candidata(r,qa)))
            self.assertTrue(nodo(v,"qa-previo").cierre_qa_coherente_completo)
            self.assertEqual(nodo(v,"qa-previo").estado_estructural,E.INCOMPATIBLE)
            self.assertEqual(v.dependencias[-1][1],E.INCOMPATIBLE)
            self.assertNotIn("comparar",v.habilitadas_declarativamente)

    def test_cancelacion_despues_de_cotejo_rc3(self):
        with escenario() as (r,c,m):
            from spica.artefactos.coordinacion import _recuperacion
            e=Event()
            def cancelar(g):
                resultado=_recuperacion(g)
                e.set()
                return resultado
            with patch("spica.artefactos.coordinacion._recuperacion",side_effect=cancelar):
                v=inspeccionar_integracion(solicitud(r),cancelacion=e)
            self.assertTrue(v.cancelada)
            self.assertEqual(v.habilitadas_declarativamente,())
            self.assertFalse(v.inspeccion_rc3.cancelada)

    def test_version_de_composicion_y_control_invalidos(self):
        with escenario() as (r,c,m):
            s=solicitud(r)
            object.__setattr__(s.composicion,"version_contrato","futura")
            v=inspeccionar_integracion(s)
            self.assertIn("version_composicion_no_admitida",codigos(v))
            self.assertEqual(v.habilitadas_declarativamente,())
        with escenario() as (r,c,m):
            s=solicitud(r)
            object.__setattr__(r.control,"generacion_id","identidad-invalida")
            v=inspeccionar_integracion(s)
            self.assertIn("control_recuperacion_invalido",codigos(v))
            self.assertEqual(v.habilitadas_declarativamente,())

    def test_productoras_contradictorias_no_se_aceptan_por_bandera_verificada(self):
        with escenario() as (r,c,m):
            s=solicitud(r)
            inv=r.unidad.inventario
            p,q=inv.producciones
            malo=replace(inv,producciones=(replace(p,salidas=q.salidas),q))
            object.__setattr__(r.unidad,"inventario",malo)
            v=inspeccionar_integracion(s)
            self.assertIn("linaje_recuperado_contradictorio",codigos(v))
            self.assertEqual(v.habilitadas_declarativamente,())

    def test_composicion_historica_no_se_redefine_para_agregar_qa(self):
        with escenario() as (r,c,m):
            comp=replace(candidata(r),identificador=r.unidad.inventario.composiciones[0].identificador)
            v=inspeccionar_integracion(solicitud(r,comp))
            self.assertIn("composicion_recuperada_redefinida",codigos(v))
            self.assertEqual(v.habilitadas_declarativamente,())


if __name__=="__main__":
    unittest.main()
