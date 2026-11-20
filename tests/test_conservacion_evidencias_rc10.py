"""RC10: contratos reales, datos sintéticos, TEMP exclusivo y lectores aislados."""

from dataclasses import replace
import hashlib
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
from spica.adquisicion.readquisicion.modelos import EstadoLocal
from spica.artefactos import DescriptorArtefacto, InventarioArtefactos, TipoArtefacto, ReferenciaArtefacto
from spica.artefactos.conservacion import entorno_conservacion, ControlGeneracion, EstadoRecuperacion
from spica.artefactos.materializacion import entorno_materializacion
from spica.artefactos._generacion_rc6 import ArchivosGeneracion
from spica.artefactos.cierre_exportacion import ejecutar_exportacion_tecnica, USO_EXPORTAR
from spica.artefactos.admision_exportacion import admitir_exportacion_tecnica, USO_CONSUMIR
from spica.artefactos.conservacion_evidencias import (
    VERSION_EVIDENCIAS, capturar_evidencias, codificar_expediente, decodificar_expediente,
    conservar_evidencias, recuperar_evidencias, ControlEvidencias,
)
from spica.artefactos import _codec_evidencias_rc10 as codec
from spica.calidad.restricciones import RestriccionQA, TipoRestriccionQA
from spica.contextos import ContextoEntrada, EstadoOperacion as S
from spica.interoperabilidad.modelos import EstadoAptitud as E
from spica.interoperabilidad.perfiles import EntradaPerfil, PerfilInformacion, CampoInformacion
# Solo fabricantes; no importar TestCase ajenos para duplicar descubrimiento.
from test_cierre_exportacion_rc8 import solicitud as s8
from test_admision_exportacion_rc9 import solicitud as s9, materializar
from test_perfiles_informacion_rc2 import declarado


def expediente(*, project_id="proyecto-RC10-A", evidencia_id="evidencia-RC10", **kw):
    e = ejecutar_exportacion_tecnica(s8(project_id=project_id, contexto_id="contexto-RC10", **kw))
    a = admitir_exportacion_tecnica(s9(e))
    return capturar_evidencias(e, a, evidencia_id=evidencia_id, proyecto=a.solicitud.proyecto)


def portador(e):
    p = e.proyecto
    ce = ContextoEntrada("expediente-rc10", p, ObjetoCientifico("objeto-expediente-"+p.project_id,
        p.project_id), None, "r1", "expediente_tecnico_rc10", "expediente_tecnico_rc10", "0.1.0")
    perfil = PerfilInformacion("expediente_tecnico_rc10", "0.1.0", "expediente_tecnico_rc10",
        (CampoInformacion("expediente", declarado("estructura-ficticia")),))
    d = DescriptorArtefacto(EntradaPerfil(ce, perfil), TipoArtefacto.ORIGINAL, e.evidencia_id,
        formato=VERSION_EVIDENCIAS, restricciones_adicionales=e.restricciones)
    return InventarioArtefactos((d,), (), ()), d.referencia


def guardar(c, e):
    inv, ref = portador(e)
    return conservar_evidencias(c, inv, ref, e)


LECTOR = r'''
import os, sys, json
def barrera(evento,args):
    if evento.startswith('socket.') or evento=='sqlite3.connect':
        raise RuntimeError('efecto_prohibido_rc10')
    if evento=='open':
        p,modo,flags=args
        if 'spica_datos' in str(p).casefold(): raise RuntimeError('almacen_operativo_prohibido')
        if (isinstance(modo,str) and any(c in modo for c in 'wax+')) or flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):
            raise RuntimeError('escritura_prohibida_rc10')
    if evento in ('os.mkdir','os.remove','os.rmdir','os.rename','os.link','os.symlink','os.chmod'):
        raise RuntimeError('mutacion_prohibida_rc10')
sys.addaudithook(barrera)
from unittest.mock import patch
from spica.artefactos.conservacion_evidencias import ControlEvidencias,recuperar_evidencias
from spica.artefactos.conservacion import ControlGeneracion
from spica.artefactos import ReferenciaArtefacto
d=json.loads(sys.argv[2])
control=ControlEvidencias(ControlGeneracion(*d['generacion']),ReferenciaArtefacto(*d['artefacto']),d['proyecto'],d['evidencia'])
with patch('spica.artefactos.cierre_exportacion.exportar_resultado_json',side_effect=AssertionError('productor_no_admitido')), patch('spica.artefactos.admision_exportacion.verificar_fisicamente',side_effect=AssertionError('ruta_historica_no_admitida')):
    r=recuperar_evidencias(sys.argv[1],control)
e=r.expediente
print(json.dumps(dict(recuperada=r.recuperada_en_alcance,proyecto=e.proyecto.project_id,
    evidencia=e.evidencia_id,estado_rc8=e.hechos.estado_rc8.value,estado_rc9=e.hechos.estado_rc9.value,
    cierre_historico=e.hechos.cierre_rc8_comprobado,admision_historica=e.hechos.admision_rc9_comprobada,
    testigos=[e.cierre_rc8.evidencia.captura_local_coherente,e.admision_rc9.comprobacion_local_coherente],
    estado_operacion=e.cierre_rc8.evidencia.operacion_observada.estado.value,
    restricciones=[x.codigo for x in e.restricciones],externos=[x.object_id for x in e.referencias_externas],
    consumo=r.consumo_actual.estado.value,sha=e.cierre_rc8.evidencia.sha256_bytes,
    nuevas_garantias=[r.comprobacion_actual_rc8,r.admision_actual_rc9,r.habilitacion_rc3_rc7,r.autenticidad_acreditada,r.autoriza_operacion])))
'''


class ConservacionEvidenciasRC10Tests(unittest.TestCase):
    def setUp(self):
        self.e = expediente()

    def ida_vuelta(self, e):
        b = codificar_expediente(e)
        r = decodificar_expediente(b)
        self.assertEqual(e, r)
        self.assertEqual(codificar_expediente(r), b)
        return r

    def test_contratos_completos_y_referencias_compartidas(self):
        r = self.ida_vuelta(self.e)
        self.assertIs(r.admision_rc9.solicitud.evidencia, r.cierre_rc8.evidencia)
        self.assertIs(r.cierre_rc8.linaje.inventario, r.cierre_rc8.evidencia.solicitud.inventario)
        self.assertEqual(r.cierre_rc8.diagnosticos, self.e.cierre_rc8.diagnosticos)

    def test_historia_no_restaura_testigos_ni_admision_actual(self):
        r = self.ida_vuelta(self.e)
        self.assertTrue(r.hechos.cierre_rc8_comprobado)
        self.assertTrue(r.hechos.admision_rc9_comprobada)
        self.assertFalse(r.cierre_rc8.evidencia.captura_local_coherente)
        self.assertFalse(r.cierre_rc8.cierre_tecnico_comprobado)
        self.assertFalse(r.admision_rc9.comprobacion_local_coherente)
        self.assertFalse(r.admision_rc9.admisible_para_consumo_tecnico)

    def test_conservacion_real_hash_fisico_y_consumo_actual_separado(self):
        with entorno_conservacion() as c:
            control = guardar(c, self.e)
            r = recuperar_evidencias(c.raiz, control)
            self.assertTrue(r.recuperada_en_alcance, r.diagnosticos)
            b = (c.raiz / "datos-000.bin").read_bytes()
            self.assertEqual(hashlib.sha256(b).hexdigest(), r.generacion.contenidos[0].sha256_fisico)
            self.assertEqual(r.expediente, self.e)
            self.assertEqual(r.consumo_actual, self.e.admision_rc9.consumo)
            self.assertFalse(r.admision_actual_rc9)
            self.assertFalse(r.habilitacion_rc3_rc7)
            self.assertTrue(r.externos_actuales)
            self.assertTrue(all(estado is EstadoLocal.NO_DISPONIBLE for _, estado in r.externos_actuales))
            with self.assertRaises(TypeError): bool(r)

    def test_version_desconocida_y_formato_anterior_no_reinterpretado(self):
        b = codificar_expediente(self.e)
        with self.assertRaises(ValueError): decodificar_expediente(b.replace(b"rc10.evidencias.0.1.0", b"rc10.evidencias.9.9.9"))
        with self.assertRaises(ValueError): codec.base.decodificar(b)
        with self.assertRaises(ValueError): decodificar_expediente(codec.base.codificar((1,)))

    def test_json_duplicados_no_finitos_profundidad_y_limite(self):
        for b in (b'{"perfil":1,"perfil":2}', b'{"x":NaN}', b'{"x":1e999}',
                  b'['*66+b'0'+b']'*66, b' '* (codec.base.MAX_METADATOS+1)):
            with self.subTest(caso=len(b)), self.assertRaises(ValueError): codec.decodificar(b)

    def test_no_codigo_ejecutable_clases_o_campos_desconocidos(self):
        b = codificar_expediente(self.e)
        for antes, despues in ((b"spica.artefactos.cierre_exportacion:EvidenciaExportacion", b"os:system"),
                (b'"productor_id"', b'"codigo_ejecutable"')):
            with self.subTest(antes=antes), self.assertRaises(ValueError):
                decodificar_expediente(b.replace(antes, despues))

    def test_bytes_y_texto_comparten_contenido_sin_perder_tipo(self):
        e = self.e.cierre_rc8.evidencia
        a = admitir_exportacion_tecnica(s9(e, contenido=e.resultado_nativo.encode()))
        x = capturar_evidencias(e, a, evidencia_id="bytes", proyecto=self.e.proyecto)
        r = self.ida_vuelta(x)
        self.assertIs(type(r.admision_rc9.solicitud.contenido), bytes)
        sobre = codec.base.leer_json(codificar_expediente(x))
        _, _, textos = codec.base.decodificar(codec.base.canonico(sobre["cuerpo"]))
        self.assertEqual(textos.count(e.resultado_nativo.encode().hex()), 1)

    def test_rc8_ausente_y_rc9_ausente_no_se_completan(self):
        e = self.e.cierre_rc8.evidencia
        a = admitir_exportacion_tecnica(s9(e, evidencia=None))
        x = capturar_evidencias(None, a, evidencia_id="sin-rc8", proyecto=self.e.proyecto)
        self.assertFalse(self.ida_vuelta(x).hechos.admision_rc9_comprobada)
        x = capturar_evidencias(e, None, evidencia_id="sin-rc9", proyecto=self.e.proyecto)
        self.assertIsNone(self.ida_vuelta(x).admision_rc9)

    def test_captura_aportada_insuficiente_permanece_pendiente(self):
        e = replace(self.e.cierre_rc8.evidencia)
        a = admitir_exportacion_tecnica(s9(e))
        x = capturar_evidencias(e, a, evidencia_id="sin-testigo", proyecto=self.e.proyecto)
        r = self.ida_vuelta(x)
        self.assertFalse(r.hechos.captura_rc8_observada)
        self.assertIs(r.hechos.estado_rc9, E.PENDIENTE_DE_EVIDENCIA)

    def test_rc9_rechazado_y_resultado_sustituido_se_conservan_como_rechazo(self):
        e = self.e.cierre_rc8.evidencia
        for contenido in ("{}", e.resultado_nativo+" "):
            with self.subTest(contenido=contenido[:5]):
                a = admitir_exportacion_tecnica(s9(e, contenido=contenido))
                x = capturar_evidencias(e, a, evidencia_id="rechazado", proyecto=self.e.proyecto)
                self.assertIs(self.ida_vuelta(x).hechos.estado_rc9, E.INCOMPATIBLE)

    def test_proyecto_operacion_productor_consumidor_revision_contradictorios(self):
        e = self.e.cierre_rc8.evidencia
        for kw in (dict(operacion_productora_id="otra"), dict(consumidor_id="otro"),
                dict(artefacto=replace(e.solicitud.salida, revision="r2")),
                dict(contenido_id="otro"), dict(entrada_resultado_id="otro"),
                dict(proyecto=expediente(project_id="proyecto-RC10-B").proyecto)):
            with self.subTest(kw=list(kw)):
                a = admitir_exportacion_tecnica(s9(e, **kw))
                x = capturar_evidencias(e, a, evidencia_id="contradictorio", proyecto=self.e.proyecto)
                self.assertIs(self.ida_vuelta(x).hechos.estado_rc9, E.INCOMPATIBLE)
        e = replace(e, productor_id="otro")
        a = admitir_exportacion_tecnica(s9(e))
        x = capturar_evidencias(e, a, evidencia_id="otro-productor", proyecto=self.e.proyecto)
        self.assertIs(self.ida_vuelta(x).hechos.estado_rc8, E.INCOMPATIBLE)

    def test_adulterar_diagnosticos_restricciones_o_estado_no_pasa(self):
        a = self.e.admision_rc9
        for x in (replace(self.e, admision_rc9=replace(a, diagnosticos=())),
                replace(self.e, admision_rc9=replace(a, restricciones=())),
                replace(self.e, hechos=replace(self.e.hechos, estado_rc9=E.INCOMPATIBLE)),
                replace(self.e, hechos=replace(self.e.hechos, cierre_rc8_comprobado=False))):
            with self.subTest(x=x.hechos), self.assertRaises(ValueError): codificar_expediente(x)

    def test_adulterar_identidades_de_solicitud_sin_cambiar_informe_es_rechazado(self):
        a = self.e.admision_rc9
        for kw in (dict(operacion_productora_id="otra"), dict(consumidor_id="otro"),
                dict(contenido="{}"), dict(artefacto=replace(a.solicitud.artefacto, revision="otra"))):
            with self.subTest(kw=list(kw)), self.assertRaises(ValueError):
                codificar_expediente(replace(self.e, admision_rc9=replace(a, solicitud=replace(a.solicitud, **kw))))

    def test_bloqueos_exportacion_y_consumo_se_conservan(self):
        for uso in (USO_EXPORTAR, USO_CONSUMIR):
            bloqueo = RestriccionQA("bloqueo-fixture", TipoRestriccionQA.BLOQUEO_USO_DEL_RESULTADO,
                (uso,), "Solo fixture")
            x = expediente(bloqueo=bloqueo)
            r = self.ida_vuelta(x)
            self.assertIn(bloqueo, r.restricciones)
            self.assertFalse(r.hechos.admision_rc9_comprobada)

    def test_parcial_fallida_cancelada_y_no_invocadas_no_se_promueven(self):
        for estado in (S.PARCIAL, S.FALLIDA, S.CANCELADA, S.DECLARADA, S.PLANIFICADA):
            with self.subTest(estado=estado):
                r = self.ida_vuelta(expediente(estado=estado))
                self.assertIs(r.cierre_rc8.evidencia.operacion_observada.estado, estado)
                self.assertFalse(r.hechos.cierre_rc8_comprobado)
                self.assertFalse(r.hechos.admision_rc9_comprobada)

    def test_fallo_y_cancelacion_real_del_productor(self):
        for fallo, estado in ((ValueError("secreto"), S.FALLIDA), (KeyboardInterrupt(), S.CANCELADA)):
            with patch("spica.artefactos.cierre_exportacion.exportar_resultado_json", side_effect=fallo):
                e = ejecutar_exportacion_tecnica(s8())
            a = admitir_exportacion_tecnica(s9(e))
            x = capturar_evidencias(e, a, evidencia_id="fallo-real", proyecto=a.solicitud.proyecto)
            self.assertIs(self.ida_vuelta(x).cierre_rc8.evidencia.operacion_observada.estado, estado)

    def test_parcial_real_tras_retorno_conserva_bytes_sin_cierre(self):
        from spica.calidad.exportacion import exportar_resultado_json
        evento = Event()
        def producir(*args, **kw):
            texto = exportar_resultado_json(*args, **kw)
            evento.set()
            return texto
        with patch("spica.artefactos.cierre_exportacion.exportar_resultado_json", side_effect=producir):
            e = ejecutar_exportacion_tecnica(s8(), cancelacion=evento)
        a = admitir_exportacion_tecnica(s9(e))
        x = capturar_evidencias(e, a, evidencia_id="parcial-real", proyecto=a.solicitud.proyecto)
        r = self.ida_vuelta(x)
        self.assertIs(r.cierre_rc8.evidencia.operacion_observada.estado, S.PARCIAL)
        self.assertIsNotNone(r.cierre_rc8.evidencia.resultado_nativo)
        self.assertFalse(r.hechos.cierre_rc8_comprobado)

    def test_tipos_incorrectos_y_constantes_no_se_reconstruyen(self):
        from spica.calidad.consumo import LimitesConsumoQA
        limite = replace(LimitesConsumoQA(), max_resultados=1)
        object.__setattr__(limite, "max_resultados", True)
        b = codec.codificar(limite)
        with self.assertRaises(ValueError): codec.decodificar(b)
        with self.assertRaises(ValueError): codec.codificar("a"*(codec.base.MAX_METADATOS+1))

    def test_descriptores_no_contienen_el_documento_y_originales_se_preservan(self):
        b = codificar_expediente(self.e)
        inv, _ = portador(self.e)
        self.assertNotIn(self.e.cierre_rc8.evidencia.resultado_nativo, repr(inv))
        self.assertEqual(inv.artefactos[0].restricciones, self.e.restricciones)
        self.assertEqual(self.ida_vuelta(self.e).cierre_rc8.evidencia.resultado_nativo,
            self.e.cierre_rc8.evidencia.resultado_nativo)
        self.assertEqual(codificar_expediente(self.e), b)

    def test_integridad_rc5_historica_no_vuelve_a_abrirse(self):
        e = self.e.cierre_rc8.evidencia
        with entorno_materializacion() as m:
            mat = materializar(m, e)
            a = admitir_exportacion_tecnica(s9(e, exigir_integridad_fisica=True, materializacion=mat))
            x = capturar_evidencias(e, a, evidencia_id="fisica", proyecto=self.e.proyecto)
        with patch("spica.artefactos.admision_exportacion.verificar_fisicamente", side_effect=AssertionError("historia")):
            r = self.ida_vuelta(x)
        self.assertTrue(r.hechos.admision_rc9_comprobada)
        self.assertEqual(r.admision_rc9.verificacion_fisica, a.verificacion_fisica)

    def test_fisica_no_disponible_se_conserva_pendiente(self):
        e = self.e.cierre_rc8.evidencia
        a = admitir_exportacion_tecnica(s9(e, exigir_integridad_fisica=True))
        x = capturar_evidencias(e, a, evidencia_id="sin-fisica", proyecto=self.e.proyecto)
        self.assertIs(self.ida_vuelta(x).hechos.estado_rc9, E.PENDIENTE_DE_EVIDENCIA)

    def test_historia_conservada_no_habilita_dependencia_rc3(self):
        r = self.ida_vuelta(self.e)
        rc3 = r.cierre_rc8.coordinacion_rc3
        self.assertNotIn("consumidor", rc3.habilitadas_declarativamente)
        self.assertFalse(rc3.ejecucion_realizada)
        self.assertTrue(r.referencias_externas)

    def test_incompleta_ausente_corrupta_y_hash_control_incorrecto(self):
        for caso in ("cierre", "ausente", "corrupta", "control"):
            with self.subTest(caso=caso), entorno_conservacion() as c:
                control = guardar(c, self.e)
                if caso == "cierre": c._fs.quitar_propio("cierre.json")
                if caso == "ausente": c._fs.quitar_propio("datos-000.bin")
                if caso == "corrupta":
                    p = c.raiz / "datos-000.bin"
                    b = p.read_bytes(); p.write_bytes(b"!"+b[1:])
                if caso == "control":
                    control = replace(control, generacion=replace(control.generacion, manifiesto_sha256="0"*64))
                r = recuperar_evidencias(c.raiz, control)
                self.assertFalse(r.recuperada_en_alcance)
                self.assertIsNone(r.expediente)

    def test_control_otro_proyecto_evidencia_o_revision(self):
        with entorno_conservacion() as c:
            control = guardar(c, self.e)
            for kw in (dict(project_id="otro"), dict(evidencia_id="otra"),
                    dict(artefacto=replace(control.artefacto, revision="r2"))):
                with self.subTest(kw=list(kw)):
                    self.assertFalse(recuperar_evidencias(c.raiz, replace(control, **kw)).recuperada_en_alcance)

    def test_rutas_inseguras_rechazadas_antes_de_leer(self):
        with entorno_conservacion() as c:
            control = guardar(c, self.e)
            for ruta in ("../fuera", str(c.raiz / ".." / c.raiz.name), "C:/SPICA_DATOS/raw"):
                with self.subTest(ruta=ruta):
                    self.assertFalse(recuperar_evidencias(ruta, control).recuperada_en_alcance)

    def test_no_sobrescritura_y_cancelacion_conservacion(self):
        with entorno_conservacion() as c:
            control = guardar(c, self.e)
            original = (c.raiz / "datos-000.bin").read_bytes()
            with self.assertRaises(ValueError): guardar(c, self.e)
            self.assertEqual((c.raiz / "datos-000.bin").read_bytes(), original)
            self.assertTrue(recuperar_evidencias(c.raiz, control).recuperada_en_alcance)
        with entorno_conservacion() as c:
            inv, ref = portador(self.e); evento = Event(); evento.set()
            with self.assertRaises(ValueError): conservar_evidencias(c, inv, ref, self.e, cancelacion=evento)
            self.assertEqual(c._fs.nombres(), ())

    def test_portador_omite_restricciones_o_confunde_proyecto(self):
        inv, ref = portador(self.e)
        with entorno_conservacion() as c, self.assertRaises(ValueError):
            conservar_evidencias(c, replace(inv, artefactos=(replace(inv.artefactos[0], restricciones_adicionales=()),)), ref, self.e)

    def test_recuperacion_sin_red_sqlite_productor_o_qa_nuevo(self):
        with entorno_conservacion() as c:
            control = guardar(c, self.e)
            with patch("socket.socket", side_effect=AssertionError("red")), patch("sqlite3.connect", side_effect=AssertionError("sql")), patch("spica.artefactos.cierre_exportacion.exportar_resultado_json", side_effect=AssertionError("productor")), patch("spica.calidad.motor.EvaluadorNivel0.__init__", side_effect=AssertionError("QA")):
                self.assertTrue(recuperar_evidencias(c.raiz, control).recuperada_en_alcance)

    def test_productor_terminado_lector_independiente_dos_proyectos_y_otra_raiz(self):
        codigo = r'''
import json
from test_conservacion_evidencias_rc10 import expediente,guardar
from spica.artefactos.conservacion import entorno_conservacion
salidas=[];propios=[]
try:
    for proyecto in ('proyecto-RC10-A','proyecto-RC10-B'):
        e=expediente(project_id=proyecto)
        with entorno_conservacion(disponer_al_salir=False) as c:
            propios.append(c._fs)
            control=guardar(c,e)
            salidas.append(dict(raiz=str(c.raiz),generacion=[control.generacion.generacion_id,control.generacion.manifiesto_sha256],
                artefacto=[control.artefacto.object_id,control.artefacto.revision],proyecto=control.project_id,evidencia=control.evidencia_id,
                propios={n:list(v) for n,v in c._fs.creados.items()}))
    print(json.dumps(salidas))
except BaseException:
    for fs in propios: fs.limpiar()
    raise
'''
        p = subprocess.run([sys.executable, "-B", "-c", codigo], capture_output=True, text=True, timeout=60, check=True)
        ds = json.loads(p.stdout)
        pendientes = list(ds)
        def limpiar(d):
            fs = ArchivosGeneracion.abrir(d["raiz"])
            fs.creados = {n: tuple(v) for n,v in d["propios"].items()}
            fs.limpiar()  # Solo nombres/inodos comprobados del proceso hijo propio.
            pendientes.remove(d)
        def leer(raiz, d):
            p = subprocess.run([sys.executable, "-B", "-c", LECTOR, str(raiz), json.dumps(d)],
                capture_output=True, text=True, timeout=60, check=True)
            return json.loads(p.stdout)
        try:
            for d in ds:
                b = leer(d["raiz"], d)
                self.assertTrue(b["recuperada"])
                self.assertEqual(b["proyecto"], d["proyecto"])
                self.assertTrue(b["cierre_historico"] and b["admision_historica"])
                self.assertEqual(b["testigos"], [False, False])
                self.assertFalse(any(b["nuevas_garantias"]))
                control = ControlGeneracion(*d["generacion"])
                with entorno_conservacion() as destino:
                    destino.copiar_de(d["raiz"], control)
                    limpiar(d)
                    self.assertEqual(leer(destino.raiz, d), b)
        finally:
            for d in pendientes[:]: limpiar(d)


if __name__ == "__main__":
    unittest.main()
