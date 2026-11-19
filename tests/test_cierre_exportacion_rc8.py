"""RC8: exportador real y evidencia específica, solo fixtures y TEMP propios."""

from dataclasses import FrozenInstanceError, replace
import hashlib
import json
from pathlib import Path
import sys
from threading import Event
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from spica.adquisicion.almacenamiento.modelos import ObjetoCientifico
from spica.adquisicion.readquisicion.modelos import EstadoLocal
from spica.artefactos import DescriptorArtefacto, EstadoArtefacto, InventarioArtefactos, ProduccionArtefactos, TipoArtefacto
from spica.artefactos.cierre_exportacion import (
    VERSION_CIERRE, PRODUCTOR, USO_EXPORTAR, SolicitudExportacionTecnica,
    EvidenciaExportacion, ejecutar_exportacion_tecnica, inspeccionar_cierre_exportacion,
)
from spica.artefactos.conservacion import UnidadConservacion, entorno_conservacion, recuperar_generacion, EstadoRecuperacion
from spica.artefactos.coordinacion import SolicitudIntegracion, VinculoEntradaRecuperada, inspeccionar_integracion
from spica.artefactos.materializacion import SolicitudMaterializacion, entorno_materializacion, verificar_fisicamente
from spica.calidad.exportacion import LimitesExportacionQA, exportar_resultado_json
from spica.calidad.consumo import EstadoConsumoQA
from spica.calidad.restricciones import RestriccionQA, TipoRestriccionQA as TR
from spica.contextos import ContextoOperacion, TipoOperacion, EstadoOperacion as S, VinculoResultadoQA
from spica.coordinacion import ComposicionOperaciones, NodoOperacion, DependenciaOperacion, LimitesComposicion
from spica.interoperabilidad.adaptadores import DiagnosticoAdaptacion as D, NivelDiagnostico as N
from spica.interoperabilidad.modelos import EstadoAptitud as E
from spica.interoperabilidad.perfiles import EntradaPerfil, PerfilInformacion, CampoInformacion
# Fabricantes únicamente; no importar TestCase para duplicar descubrimiento.
from test_contextos_rc1 import proyecto, entrada, operacion, iniciada, resultado
from test_perfiles_informacion_rc2 import declarado


def solicitud(*, estado=S.INICIADA, project_id="proyecto-RC8", contexto_id="contexto-RC8",
              metodo=PRODUCTOR, version="0.1.0", bloqueo=None, parcial=False):
    p = proyecto(project_id, contexto_id, restricciones=() if bloqueo is None else (bloqueo,))
    fuente = entrada(p)
    qa = iniciada(operacion(fuente, "qa-fuente"))
    # El evaluador existente genera este resultado; no se inventa InformeQA.
    v = VinculoResultadoQA(qa, fuente.entrada_id, "resultado-qa-fuente", resultado(fuente))
    def ep(nombre, tipo, version, campos):
        e = entrada(p, entrada_id=nombre, objeto=ObjetoCientifico("objeto-"+nombre+"-"+project_id,p.project_id),
            tipo_recurso=tipo, perfil_estructural=tipo, version_contenido=version,
            sha256_declarado=None, size_bytes_declarado=None, revision="r1")
        perfil = PerfilInformacion(tipo,version,tipo,tuple(CampoInformacion(c,declarado("estructura-ficticia")) for c in campos),
            ambito=declarado("fixture RC8 sin uso institucional"))
        return EntradaPerfil(e,perfil)
    a = DescriptorArtefacto(ep(v.referencia_resultado,"resultado_qa_nativo","1.0.0",("resultado",)),
        TipoArtefacto.ORIGINAL,"entrada-logica-qa-fixture")
    b = DescriptorArtefacto(ep("salida-exportacion","json_qa","0.1.0",("version_esquema","resultado_id","resultado","contexto")),
        TipoArtefacto.PREPARADO,"salida-json-fixture",formato="application/json",
        estado_logico=EstadoArtefacto.PARCIAL if parcial else EstadoArtefacto.DESCRITO)
    causas = (D("interrupcion_fixture","fixture",N.FALTANTE),) if estado in (S.PARCIAL,S.FALLIDA,S.CANCELADA) else ()
    op = ContextoOperacion("exportar",p,(a.entrada_perfil.entrada,),TipoOperacion.DESCRIPCION_ESTRUCTURAL,
        "Exportar un resultado QA aportado, sin evaluarlo",estado=estado,diagnosticos=causas,
        referencias_resultado=() if estado in (S.DECLARADA,S.PLANIFICADA) else (b.entrada_perfil.entrada.entrada_id,))
    prod = ProduccionArtefactos(op,metodo,version,(a.referencia,),(b.referencia,))
    consumidor = ContextoOperacion("consumidor",p,(b.entrada_perfil.entrada,),TipoOperacion.DESCRIPCION_ESTRUCTURAL,
        "Consumidor hipotetico; no se ejecuta")
    c = ComposicionOperaciones("composicion-RC8",p,(NodoOperacion(op,(USO_EXPORTAR,)),NodoOperacion(consumidor,("inspeccionar",))),
        (DependenciaOperacion("exportar","consumidor",(b.entrada_perfil.entrada.entrada_id,)),),"Cotejo RC8 sin despachar dependencias")
    inv = InventarioArtefactos((a,b),(prod,),(c,))
    return SolicitudExportacionTecnica(inv,c.identificador,op.operacion_id,b.referencia,v)


def codigos(informe):
    return {d.codigo for d in informe.diagnosticos}


class CierreExportacionRC8Tests(unittest.TestCase):
    def test_ejecucion_real_y_salida_nativa_sin_fabricar_qa(self):
        s=solicitud()
        with patch("spica.artefactos.cierre_exportacion.exportar_resultado_json",wraps=exportar_resultado_json) as productor:
            e=ejecutar_exportacion_tecnica(s)
            productor.assert_called_once_with(s.entrada_qa.resultado,s.entrada_qa.contexto_exportacion,limites=s.limites_exportacion)
        r=inspeccionar_cierre_exportacion(e)
        self.assertTrue(r.cierre_tecnico_comprobado,codigos(r))
        self.assertTrue(e.captura_local_coherente)
        self.assertEqual(e.operacion_observada.estado,S.CONCLUIDA)
        self.assertEqual(r.consumo.estado,EstadoConsumoQA.CONTRATO_VALIDO_EN_ALCANCE)
        self.assertEqual(e.resultado_nativo,exportar_resultado_json(s.entrada_qa.resultado,s.entrada_qa.contexto_exportacion))
        self.assertEqual(json.loads(e.resultado_nativo)["version_esquema"],"0.1.0")
        self.assertEqual(e.sha256_bytes,hashlib.sha256(e.resultado_nativo.encode()).hexdigest())
        self.assertEqual(e.size_bytes,len(e.resultado_nativo.encode()))

    def test_estados_historicos_y_valores_originales_no_se_modifican(self):
        s=solicitud()
        op=s.inventario.producciones[0].operacion
        antes=exportar_resultado_json(s.entrada_qa.resultado,s.entrada_qa.contexto_exportacion)
        e=ejecutar_exportacion_tecnica(s)
        self.assertIs(s.inventario.producciones[0].operacion,op)
        self.assertEqual(op.estado,S.INICIADA)
        self.assertEqual(s.entrada_qa.operacion.estado,S.INICIADA)
        self.assertEqual(e.resultado_nativo,antes)
        self.assertIn("10000",e.resultado_nativo)
        self.assertIn("01234.0",e.resultado_nativo)
        self.assertNotIn("rc8",json.loads(e.resultado_nativo))

    def test_estado_solo_declarado_y_terminales_no_se_promueven(self):
        for estado in (S.DECLARADA,S.PLANIFICADA,S.CONCLUIDA,S.PARCIAL,S.FALLIDA,S.CANCELADA):
            with self.subTest(estado=estado):
                s=solicitud(estado=estado,parcial=estado in (S.PARCIAL,S.FALLIDA,S.CANCELADA))
                with patch("spica.artefactos.cierre_exportacion.exportar_resultado_json") as p:
                    e=ejecutar_exportacion_tecnica(s)
                    p.assert_not_called()
                self.assertFalse(inspeccionar_cierre_exportacion(e).cierre_tecnico_comprobado)
                self.assertEqual(e.operacion_observada.estado,estado)

    def test_composicion_u_operacion_inexistentes(self):
        for kw in (dict(composicion_id="ausente"),dict(operacion_id="ausente")):
            with self.subTest(kw=kw):
                e=ejecutar_exportacion_tecnica(replace(solicitud(),**kw))
                self.assertFalse(e.productor_invocado)
                self.assertFalse(inspeccionar_cierre_exportacion(e).cierre_tecnico_comprobado)

    def test_productor_o_version_incorrectos(self):
        for kw in (dict(metodo="productor-inexistente"),dict(version="99.0.0")):
            with self.subTest(kw=kw):
                r=inspeccionar_cierre_exportacion(ejecutar_exportacion_tecnica(solicitud(**kw)))
                self.assertIn("productor_o_version_no_admitidos",codigos(r))
                self.assertFalse(r.evidencia.productor_invocado)

    def test_entrada_qa_de_otro_proyecto(self):
        a,b=solicitud(),solicitud(project_id="otro",contexto_id="otro-contexto")
        r=inspeccionar_cierre_exportacion(ejecutar_exportacion_tecnica(replace(a,entrada_qa=b.entrada_qa)))
        self.assertIn("resultado_qa_no_corresponde_a_entrada_exportadora",codigos(r))
        self.assertFalse(r.evidencia.productor_invocado)

    def test_identidad_de_entrada_exportadora_no_es_el_csv(self):
        s=solicitud()
        a,b=s.inventario.artefactos
        with self.assertRaisesRegex(ValueError,"perfil_no_corresponde_a_entrada"):
            replace(a.entrada_perfil,entrada=s.entrada_qa.operacion.entradas[0])
        v=s.entrada_qa
        ajeno=VinculoResultadoQA(v.operacion,v.entrada_id,"otra-referencia-de-resultado",v.resultado)
        e=ejecutar_exportacion_tecnica(replace(s,entrada_qa=ajeno))
        self.assertFalse(e.productor_invocado)
        self.assertIn("resultado_qa_no_corresponde_a_entrada_exportadora",codigos(inspeccionar_cierre_exportacion(e)))
        self.assertFalse(inspeccionar_cierre_exportacion(e).cierre_tecnico_comprobado)

    def test_captura_externa_coherente_no_demuestra_invocacion(self):
        e=ejecutar_exportacion_tecnica(solicitud())
        externa=replace(e)
        self.assertFalse(externa.captura_local_coherente)
        r=inspeccionar_cierre_exportacion(externa)
        self.assertEqual(r.consumo.estado,EstadoConsumoQA.CONTRATO_VALIDO_EN_ALCANCE)
        self.assertIn("captura_aportada_no_observada_o_alterada",codigos(r))
        self.assertFalse(r.cierre_tecnico_comprobado)

    def test_resultado_json_valido_de_otra_entrada_no_se_asocia(self):
        s=solicitud()
        otro=resultado(s.entrada_qa.operacion.entradas[0],numero=2)
        ajeno=exportar_resultado_json(otro,s.entrada_qa.contexto_exportacion)
        with patch("spica.artefactos.cierre_exportacion.exportar_resultado_json",return_value=ajeno):
            r=inspeccionar_cierre_exportacion(ejecutar_exportacion_tecnica(s))
        self.assertFalse(r.cierre_tecnico_comprobado)
        self.assertIn("salida_no_corresponde_a_entrada_nativa",codigos(r))

    def test_salida_incompatible_y_version_json_desconocida(self):
        s=solicitud()
        d=json.loads(exportar_resultado_json(s.entrada_qa.resultado,s.entrada_qa.contexto_exportacion))
        d["version_esquema"]="99.0.0"
        for texto in ("{truncado",json.dumps(d),"{}"):
            with self.subTest(texto=texto[:20]),patch("spica.artefactos.cierre_exportacion.exportar_resultado_json",return_value=texto):
                r=inspeccionar_cierre_exportacion(ejecutar_exportacion_tecnica(s))
                self.assertFalse(r.cierre_tecnico_comprobado)
                self.assertIn("salida_rechazada_o_incompleta_por_consumidor",codigos(r))

    def test_resultado_alterado_despues_de_capturarlo(self):
        e=ejecutar_exportacion_tecnica(solicitud())
        object.__setattr__(e,"resultado_nativo",e.resultado_nativo+" ")
        r=inspeccionar_cierre_exportacion(e)
        self.assertFalse(e.captura_local_coherente)
        self.assertIn("huella_o_tamano_de_salida_contradictorios",codigos(r))
        self.assertFalse(r.cierre_tecnico_comprobado)

    def test_hash_y_tamano_incorrectos_no_se_confunden_con_fisicos(self):
        for kw in (dict(sha256_bytes="0"*64),dict(size_bytes=True),dict(size_bytes=0)):
            with self.subTest(kw=kw):
                r=inspeccionar_cierre_exportacion(replace(ejecutar_exportacion_tecnica(solicitud()),**kw))
                self.assertIn("huella_o_tamano_de_salida_contradictorios",codigos(r))
                self.assertFalse(r.comprobacion_fisica_realizada)
                self.assertFalse(r.cierre_tecnico_comprobado)

    def test_identidad_de_operacion_observada_contradictoria(self):
        e=ejecutar_exportacion_tecnica(solicitud())
        r=inspeccionar_cierre_exportacion(replace(e,operacion_observada=replace(e.operacion_observada,operacion_id="otra")))
        self.assertIn("operacion_observada_incompatible",codigos(r))
        self.assertFalse(r.cierre_tecnico_comprobado)

    def test_versiones_del_contrato_y_evidencia(self):
        with self.assertRaises(ValueError):
            replace(solicitud(),version_contrato="futuro")
        for kw in (dict(version_contrato="futuro"),dict(productor_id="otro"),dict(version_productor="futuro")):
            with self.subTest(kw=kw):
                r=inspeccionar_cierre_exportacion(replace(ejecutar_exportacion_tecnica(solicitud()),**kw))
                self.assertIn("version_o_productor_de_evidencia_incompatible",codigos(r))
        s=solicitud()
        object.__setattr__(s.inventario,"version_contrato","futuro")
        self.assertFalse(ejecutar_exportacion_tecnica(s).productor_invocado)

    def test_resultado_parcial_no_es_cierre(self):
        e=ejecutar_exportacion_tecnica(solicitud(parcial=True))
        self.assertFalse(e.productor_invocado)
        self.assertIn("artefacto_parcial_no_es_cierre",codigos(inspeccionar_cierre_exportacion(e)))

    def test_fallo_del_productor_sin_texto_sensible(self):
        with patch("spica.artefactos.cierre_exportacion.exportar_resultado_json",side_effect=OSError("credencial=/ruta/privada token=secreto")):
            e=ejecutar_exportacion_tecnica(solicitud())
        r=inspeccionar_cierre_exportacion(e)
        self.assertTrue(e.productor_invocado)
        self.assertEqual(e.operacion_observada.estado,S.FALLIDA)
        self.assertIsNone(e.resultado_nativo)
        self.assertNotIn("secreto",repr(r.diagnosticos))
        self.assertFalse(r.cierre_tecnico_comprobado)

    def test_cancelacion_antes_de_invocar(self):
        event=Event();event.set()
        with patch("spica.artefactos.cierre_exportacion.exportar_resultado_json") as p:
            e=ejecutar_exportacion_tecnica(solicitud(),cancelacion=event)
            p.assert_not_called()
        self.assertEqual(e.operacion_observada.estado,S.CANCELADA)
        self.assertFalse(inspeccionar_cierre_exportacion(e).cierre_tecnico_comprobado)

    def test_cancelacion_despues_de_salida_conserva_resultado_sin_cierre(self):
        event=Event()
        def producir(*args,**kw):
            texto=exportar_resultado_json(*args,**kw);event.set();return texto
        with patch("spica.artefactos.cierre_exportacion.exportar_resultado_json",side_effect=producir):
            e=ejecutar_exportacion_tecnica(solicitud(),cancelacion=event)
        self.assertEqual(e.operacion_observada.estado,S.PARCIAL)
        self.assertIsNotNone(e.resultado_nativo)
        self.assertFalse(inspeccionar_cierre_exportacion(e).cierre_tecnico_comprobado)

    def test_interrupcion_durante_productor(self):
        with patch("spica.artefactos.cierre_exportacion.exportar_resultado_json",side_effect=KeyboardInterrupt):
            e=ejecutar_exportacion_tecnica(solicitud())
        self.assertTrue(e.productor_invocado)
        self.assertEqual(e.operacion_observada.estado,S.CANCELADA)
        self.assertIsNone(e.resultado_nativo)

    def test_restriccion_bloqueante_impide_invocar(self):
        bloqueo=RestriccionQA("bloqueo-rc8",TR.BLOQUEO_USO_DEL_RESULTADO,(USO_EXPORTAR,),"Fixture: exportacion bloqueada")
        e=ejecutar_exportacion_tecnica(solicitud(bloqueo=bloqueo))
        self.assertFalse(e.productor_invocado)
        self.assertIn(bloqueo,inspeccionar_cierre_exportacion(e).restricciones)

    def test_restriccion_heredada_no_desaparece_por_exportar(self):
        bloqueo=RestriccionQA("ciencia-rc8",TR.BLOQUEO_USO_DEL_RESULTADO,("acreditar_ciencia",),"Fixture: sin validez cientifica")
        r=inspeccionar_cierre_exportacion(ejecutar_exportacion_tecnica(solicitud(bloqueo=bloqueo)))
        self.assertTrue(r.cierre_tecnico_comprobado,codigos(r))
        self.assertIn(bloqueo,r.restricciones)
        self.assertFalse(r.validacion_cientifica_realizada)

    def test_evidencia_sin_resultado_o_sin_invocacion(self):
        e=ejecutar_exportacion_tecnica(solicitud())
        for kw in (dict(resultado_nativo=None),dict(productor_invocado=False),dict(operacion_observada=None)):
            with self.subTest(kw=kw):
                self.assertFalse(inspeccionar_cierre_exportacion(replace(e,**kw)).cierre_tecnico_comprobado)

    def test_cotas_de_exportacion_y_descriptores(self):
        s=solicitud()
        e=ejecutar_exportacion_tecnica(replace(s,limites_exportacion=LimitesExportacionQA(max_bytes=100)))
        self.assertEqual(e.operacion_observada.estado,S.FALLIDA)
        self.assertIsNone(e.resultado_nativo)
        for limites in (LimitesComposicion(max_visitas_descriptores=2),LimitesComposicion(max_bytes_texto=16),
                        LimitesComposicion(max_operaciones=1)):
            with self.subTest(limites=limites):
                e=ejecutar_exportacion_tecnica(replace(s,limites=limites))
                self.assertFalse(e.productor_invocado)

    def test_asociacion_rc3_y_linaje_contradictorios(self):
        s=solicitud();inv=s.inventario;p=inv.producciones[0]
        for malo in (replace(p,entradas=p.salidas),replace(p,salidas=p.entradas),
                     replace(p,operacion=replace(p.operacion,proposito="otra instantanea"))):
            with self.subTest(malo=malo):
                e=ejecutar_exportacion_tecnica(replace(s,inventario=replace(inv,producciones=(malo,))))
                self.assertFalse(e.productor_invocado)
                self.assertFalse(inspeccionar_cierre_exportacion(e).cierre_tecnico_comprobado)

    def test_dos_proyectos_pueden_tener_mismos_bytes_sin_fusionarse(self):
        # La identidad JSON es contextual declarada: no incluye el project_id MD.
        # Se fuerza colision de espacios nominales, dentro de inventarios separados.
        a=ejecutar_exportacion_tecnica(solicitud(project_id="A",contexto_id="espacio-ficticio"))
        b=ejecutar_exportacion_tecnica(solicitud(project_id="B",contexto_id="espacio-ficticio"))
        self.assertEqual(a.resultado_nativo,b.resultado_nativo)
        self.assertTrue(inspeccionar_cierre_exportacion(a).cierre_tecnico_comprobado)
        self.assertTrue(inspeccionar_cierre_exportacion(b).cierre_tecnico_comprobado)
        self.assertNotEqual(a.operacion_observada.proyecto.project_id,b.operacion_observada.proyecto.project_id)
        cruzada=replace(a,solicitud=b.solicitud)
        self.assertIn("operacion_observada_incompatible",codigos(inspeccionar_cierre_exportacion(cruzada)))

    def test_inspeccion_determinista_sin_despacho_qa_red_archivos_sql(self):
        s=solicitud();e=ejecutar_exportacion_tecnica(s)
        with patch("spica.artefactos.cierre_exportacion.exportar_resultado_json",side_effect=AssertionError("no invocar")), \
             patch("builtins.open",side_effect=AssertionError("no E/S")), \
             patch("socket.socket",side_effect=AssertionError("no red")), \
             patch("sqlite3.connect",side_effect=AssertionError("no SQL")), \
             patch("spica.calidad.evaluar_registro",side_effect=AssertionError("no QA")):
            a=inspeccionar_cierre_exportacion(e);b=inspeccionar_cierre_exportacion(e)
        self.assertEqual(a,b)
        self.assertTrue(a.cierre_tecnico_comprobado)

    def test_invocacion_explicita_en_memoria_sin_red_o_escrituras(self):
        s=solicitud()
        with patch("builtins.open",side_effect=AssertionError("no E/S")), \
             patch("socket.socket",side_effect=AssertionError("no red")), \
             patch("sqlite3.connect",side_effect=AssertionError("no SQL")):
            e=ejecutar_exportacion_tecnica(s)
        self.assertTrue(e.productor_invocado)
        self.assertEqual(e.operacion_observada.estado,S.CONCLUIDA)

    def test_no_concede_permisos_y_conserva_pendiente_nativo_rc3(self):
        r=inspeccionar_cierre_exportacion(ejecutar_exportacion_tecnica(solicitud()))
        self.assertTrue(r.cierre_tecnico_comprobado)
        self.assertNotIn("consumidor",r.coordinacion_rc3.habilitadas_declarativamente)
        self.assertTrue(all(n.nodo.cierre_qa is None for n in r.coordinacion_rc3.operaciones))
        self.assertFalse(r.autoriza_operacion)
        self.assertFalse(r.evidencia.autoriza_operacion)
        self.assertFalse(r.autorizacion_concedida)
        for valor in (r,r.evidencia):
            with self.assertRaises(TypeError): bool(valor)

    def test_materializacion_real_y_comprobacion_fisica_separadas(self):
        e=ejecutar_exportacion_tecnica(solicitud());b=e.resultado_nativo.encode()
        with entorno_materializacion() as m:
            s5=SolicitudMaterializacion(e.solicitud.inventario,e.solicitud.salida,len(b),e.sha256_bytes)
            r5=m.materializar_sintetico(s5,(b[:29],b[29:]))
            self.assertEqual((m.raiz/r5.referencia.nombre).read_bytes(),b)
            v=verificar_fisicamente(s5,r5.referencia)
            self.assertEqual(v.estado_local,EstadoLocal.INTEGRO)
            self.assertEqual(r5.sha256_recibido,e.sha256_bytes)
            self.assertFalse(r5.productor_ejecutado)
            self.assertFalse(inspeccionar_cierre_exportacion(e).comprobacion_fisica_realizada)
        self.assertFalse(m.raiz.exists())

    def test_archivo_ausente_o_corrupto_no_invalida_captura_historica(self):
        e=ejecutar_exportacion_tecnica(solicitud());b=e.resultado_nativo.encode()
        for modo in ("ausente","corrupto"):
            with self.subTest(modo=modo),entorno_materializacion() as m:
                s5=SolicitudMaterializacion(e.solicitud.inventario,e.solicitud.salida,len(b),e.sha256_bytes)
                r5=m.materializar_sintetico(s5,(b,));p=m.raiz/r5.referencia.nombre
                if modo=="ausente": p.unlink()
                else: p.write_bytes(b"X"*len(b))
                v=verificar_fisicamente(s5,r5.referencia)
                self.assertIsNot(v.estado_local,EstadoLocal.INTEGRO)
                self.assertTrue(inspeccionar_cierre_exportacion(e).cierre_tecnico_comprobado)

    def test_rc6_conserva_bytes_pero_no_el_cierre_ni_habilita_rc7(self):
        e=ejecutar_exportacion_tecnica(solicitud());s=e.solicitud;b=e.resultado_nativo.encode()
        with entorno_materializacion() as m,entorno_conservacion() as c:
            r5=m.materializar_sintetico(SolicitudMaterializacion(s.inventario,s.salida,len(b),e.sha256_bytes),(b,))
            externo=s.inventario.artefactos[0].referencia
            guardado=c.conservar(UnidadConservacion(s.inventario,(r5,),(externo,)))
            r=recuperar_generacion(c.raiz,guardado.control)
            self.assertEqual(r.estado,EstadoRecuperacion.VERIFICADA)
            v=next(v for v in r.contenidos if v.artefacto==s.salida)
            self.assertEqual((c.raiz/v.relativa).read_bytes(),b)
            comp=r.unidad.inventario.composiciones[0]
            refs={a.entrada_perfil.entrada.entrada_id:a.referencia for a in r.unidad.inventario.artefactos}
            vs=tuple(VinculoEntradaRecuperada(n.contexto.operacion_id,en.entrada_id,refs[en.entrada_id]) for n in comp.operaciones for en in n.contexto.entradas)
            integrado=inspeccionar_integracion(SolicitudIntegracion(r,comp,vs,"Cotejo RC8 sin incorporar cierres nuevos"))
            self.assertNotIn("consumidor",integrado.habilitadas_declarativamente)
            self.assertTrue(all(n.cierre_qa is None for n in comp.operaciones))
            self.assertEqual(comp.operaciones[0].contexto.estado,S.INICIADA)
            self.assertTrue(inspeccionar_cierre_exportacion(e).cierre_tecnico_comprobado)
        self.assertFalse(c.raiz.exists())

    def test_datos_y_eventos_tipificados_sin_callbacks(self):
        for crear in (lambda: replace(solicitud(),entrada_qa={}),lambda: replace(solicitud(),limites_exportacion={}),
                      lambda: ejecutar_exportacion_tecnica(solicitud(),cancelacion=lambda: True)):
            with self.subTest(crear=crear),self.assertRaises(TypeError): crear()
        e=ejecutar_exportacion_tecnica(solicitud())
        with self.assertRaises(FrozenInstanceError): e.productor_id="otro"

    def test_bloqueo_del_descriptor_omitido_del_contexto(self):
        s=solicitud();a,b=s.inventario.artefactos
        bloqueo=RestriccionQA("descriptor-bloquea",TR.BLOQUEO_USO_DEL_RESULTADO,(USO_EXPORTAR,),"Fixture: bloqueo local")
        a=replace(a,restricciones_adicionales=(bloqueo,))
        s=replace(s,inventario=replace(s.inventario,artefactos=(a,b)))
        e=ejecutar_exportacion_tecnica(s)
        r=inspeccionar_cierre_exportacion(e)
        self.assertFalse(e.productor_invocado)
        self.assertIn(bloqueo,r.restricciones)
        self.assertIn("restriccion_impide_exportacion",codigos(r))

    def test_uso_desconocido_no_se_considera_aprobado(self):
        s=solicitud();c=s.inventario.composiciones[0]
        c=replace(c,operaciones=(replace(c.operaciones[0],usos_declarados=None),c.operaciones[1]))
        e=ejecutar_exportacion_tecnica(replace(s,inventario=replace(s.inventario,composiciones=(c,))))
        self.assertFalse(e.productor_invocado)
        self.assertIn("uso_tecnico_no_declarado",codigos(inspeccionar_cierre_exportacion(e)))

    def test_hash_declarado_del_descriptor_no_prevalece_sobre_salida(self):
        s=solicitud();a,b=s.inventario.artefactos
        b=replace(b,entrada_perfil=replace(b.entrada_perfil,entrada=replace(b.entrada_perfil.entrada,sha256_declarado="0"*64)))
        c=s.inventario.composiciones[0]
        consumidor=replace(c.operaciones[1],contexto=replace(c.operaciones[1].contexto,entradas=(b.entrada_perfil.entrada,)))
        c=replace(c,operaciones=(c.operaciones[0],consumidor))
        s=replace(s,inventario=replace(s.inventario,artefactos=(a,b),composiciones=(c,)))
        r=inspeccionar_cierre_exportacion(ejecutar_exportacion_tecnica(s))
        self.assertTrue(r.evidencia.productor_invocado)
        self.assertFalse(r.cierre_tecnico_comprobado)
        self.assertIn("salida_contradice_descriptor_rc4",codigos(r))

    def test_salida_de_tipo_incorrecto_y_entrada_nativa_invalida(self):
        with patch("spica.artefactos.cierre_exportacion.exportar_resultado_json",return_value=b"no str"):
            e=ejecutar_exportacion_tecnica(solicitud())
        self.assertEqual(e.operacion_observada.estado,S.FALLIDA)
        s=solicitud()
        object.__setattr__(s.entrada_qa.resultado,"version_contrato","futuro")
        e=ejecutar_exportacion_tecnica(s)
        self.assertFalse(e.productor_invocado)

    def test_publicacion_repetida_conserva_archivo_anterior(self):
        e=ejecutar_exportacion_tecnica(solicitud());b=e.resultado_nativo.encode()
        with entorno_materializacion() as m:
            s5=SolicitudMaterializacion(e.solicitud.inventario,e.solicitud.salida,len(b),e.sha256_bytes)
            r5=m.materializar_sintetico(s5,(b,))
            p=m.raiz/r5.referencia.nombre
            antes=p.stat().st_ino,p.read_bytes()
            segundo=m.materializar_sintetico(s5,(b,))
            self.assertEqual((p.stat().st_ino,p.read_bytes()),antes)
            self.assertIsNot(segundo.estado_tecnico,S.CONCLUIDA)

    def test_restricciones_contradictorias_conservan_variantes_y_bloquean(self):
        s=solicitud();inv=s.inventario;c=inv.composiciones[0];p=inv.producciones[0]
        original=s.entrada_qa.restricciones[0]
        contradiccion=replace(original,tipo=TR.BLOQUEO_USO_DEL_RESULTADO,
            operaciones=(USO_EXPORTAR,),motivo="Fixture: variante contradictoria")
        op=replace(p.operacion,restricciones_adicionales=(contradiccion,))
        c=replace(c,operaciones=(replace(c.operaciones[0],contexto=op),c.operaciones[1]))
        s=replace(s,inventario=replace(inv,producciones=(replace(p,operacion=op),),composiciones=(c,)))
        e=ejecutar_exportacion_tecnica(s)
        r=inspeccionar_cierre_exportacion(e)
        self.assertFalse(e.productor_invocado)
        self.assertIn("restricciones_recuperadas_no_unificables",codigos(r))
        self.assertIn(original,r.restricciones)
        self.assertIn(contradiccion,r.restricciones)


if __name__=="__main__":
    unittest.main()
