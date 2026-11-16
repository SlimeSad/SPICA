"""Ensayos RC6 exclusivamente con bytes ficticios y raíces TEMP propias."""

from dataclasses import FrozenInstanceError, replace
from datetime import date, datetime, timezone
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
from threading import Event
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from spica.artefactos import InventarioArtefactos, ReferenciaArtefacto, EstadoArtefacto, inspeccionar_linaje
from spica.artefactos.conservacion import (
    ControlGeneracion, ErrorConservacion, EstadoRecuperacion as R, UnidadConservacion,
    USO_CONSERVAR, USO_RECUPERAR, VERSION_CONSERVACION, entorno_conservacion,
    recuperar_generacion,
)
from spica.artefactos import _codec_rc6 as codec
from spica.artefactos._generacion_rc6 import ArchivosGeneracion
from spica.artefactos._archivos_rc5 import ErrorArchivoExperimental, base_temporal
from spica.artefactos.materializacion import entorno_materializacion
from spica.adquisicion.readquisicion.modelos import EstadoLocal as L
from spica.calidad.restricciones import RestriccionQA, TipoRestriccionQA as T
from spica.contextos import EstadoOperacion as S
from test_materializacion_rc5 import inventario, solicitud, publicar, ORIGINAL, PREPARADO, DERIVADO

DATOS = (ORIGINAL, ORIGINAL, PREPARADO, DERIVADO)


def unidad(m=None, *, inv=None, indices=(0, 1, 2, 3)):
    inv = inventario() if inv is None else inv
    informes = () if m is None else tuple(publicar(m, solicitud(i, DATOS[i], inv=inv), DATOS[i]) for i in indices)
    refs = {r.solicitud.artefacto for r in informes}
    return UnidadConservacion(inv, informes, tuple(a.referencia for a in inv.artefactos if a.referencia not in refs))


def resumen(r):
    return dict(estado=r.estado.value, diagnosticos=r.diagnosticos,
        artefactos=[] if r.unidad is None else [[a.referencia.object_id, a.referencia.revision,
            a.contenido_id, a.estado_logico.value, a.revision_cientifica.value] for a in r.unidad.inventario.artefactos],
        operaciones=[] if r.unidad is None else [[p.operacion.operacion_id,
            p.operacion.estado.value, p.metodo_id, p.metodo_version, p.ejecucion_id] for p in r.unidad.inventario.producciones],
        restricciones=[] if r.unidad is None else [[a.descriptor.referencia.object_id,
            [v.restriccion.codigo for v in a.restricciones]] for a in r.unidad.linaje.artefactos],
        contenidos=[[v.artefacto.object_id, v.estado_actual.value, v.size_bytes, v.sha256_fisico] for v in r.contenidos],
        autenticidad=r.autenticidad_acreditada, custodia=r.custodia_independiente)


LECTOR = r'''
import json, os, sys
def barrera(evento, args):
    if evento.startswith("socket.") or evento == "sqlite3.connect":
        raise RuntimeError("efecto_prohibido_rc6")
    if evento == "open":
        p, modo, banderas = args
        if "spica_datos" in str(p).casefold():
            raise RuntimeError("lectura_operativa_prohibida_rc6")
        if (isinstance(modo,str) and any(x in modo for x in "wax+")) or (banderas & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)):
            raise RuntimeError("escritura_prohibida_rc6")
    if evento in ("os.mkdir", "os.remove", "os.rmdir", "os.rename", "os.link", "os.symlink", "os.chmod"):
        raise RuntimeError("mutacion_prohibida_rc6")
sys.addaudithook(barrera)
from spica.artefactos.conservacion import ControlGeneracion, recuperar_generacion
r = recuperar_generacion(sys.argv[1], ControlGeneracion(*json.loads(sys.argv[2])))
# La reconstrucción se obtiene únicamente del lector real, sin factories de tests.
print(json.dumps(dict(estado=r.estado.value, diagnosticos=r.diagnosticos,
    ids=[] if r.unidad is None else [a.referencia.object_id for a in r.unidad.inventario.artefactos],
    estados=[] if r.unidad is None else [p.operacion.estado.value for p in r.unidad.inventario.producciones],
    restricciones=[] if r.unidad is None else [[x.restriccion.codigo for x in a.restricciones] for a in r.unidad.linaje.artefactos],
    hashes=[v.sha256_fisico for v in r.contenidos], custodia=r.custodia_independiente)))
'''


def otro_proceso(raiz, control):
    r = subprocess.run([sys.executable, "-B", "-c", LECTOR, str(raiz),
        json.dumps([control.generacion_id, control.manifiesto_sha256])], capture_output=True,
        text=True, timeout=45, check=True)
    return json.loads(r.stdout)


def resellar(c, control, *, metadatos=None, manifiesto=None):
    """Solo mutación adversarial explícita de nuestra fixture; nunca producción."""
    p = c.raiz
    m = codec.leer_json((p / "manifiesto.json").read_bytes())
    if metadatos is not None:
        (p / "metadatos.json").write_bytes(metadatos)
        m["metadatos"] = dict(size_bytes=len(metadatos), sha256=hashlib.sha256(metadatos).hexdigest())
    if manifiesto is not None:
        manifiesto(m)
    b = codec.canonico(m)
    (p / "manifiesto.json").write_bytes(b)
    nuevo = ControlGeneracion(control.generacion_id, hashlib.sha256(b).hexdigest())
    (p / "cierre.json").write_bytes(codec.canonico(dict(version=VERSION_CONSERVACION,
        generacion_id=nuevo.generacion_id, manifiesto_sha256=nuevo.manifiesto_sha256, estado="cerrada_en_alcance")))
    return nuevo


class ConservacionRC6Tests(unittest.TestCase):
    def test_conserva_inventario_lineaje_y_hashes_fisicos(self):
        with entorno_materializacion() as m, entorno_conservacion() as c:
            u = unidad(m)
            r = c.conservar(u)
            self.assertEqual(r.estado, R.VERIFICADA)
            self.assertEqual(r.unidad.inventario, u.inventario)
            self.assertEqual(r.unidad.materializaciones, u.materializaciones)
            self.assertEqual(r.unidad.linaje, u.linaje)
            for v, b in zip(r.contenidos, DATOS):
                self.assertEqual(v.sha256_fisico, hashlib.sha256(b).hexdigest())
                self.assertEqual((c.raiz / v.relativa).read_bytes(), b)
            self.assertFalse(r.autoriza_operacion)
            self.assertFalse(r.autenticidad_acreditada)
            self.assertFalse(r.custodia_independiente)
            self.assertFalse(r.persistencia_durable)
            with self.assertRaises(TypeError):
                bool(r)

    def test_relectura_no_promueve_parcial_ni_ciencia(self):
        with entorno_materializacion() as m, entorno_conservacion() as c:
            r = c.conservar(unidad(m))
            u = r.unidad
            self.assertEqual(u.inventario.artefactos[3].estado_logico, EstadoArtefacto.PARCIAL)
            self.assertEqual(u.inventario.producciones[1].operacion.estado, S.PARCIAL)
            self.assertTrue(all(a.revision_cientifica.value == "no_evaluada" for a in u.inventario.artefactos))
            self.assertTrue(all(x.estado_tecnico is S.CONCLUIDA for x in u.materializaciones))

    def test_igual_sha_no_fusiona_objetos_o_proyectos(self):
        with entorno_materializacion() as m, entorno_conservacion() as c:
            r = c.conservar(unidad(m))
            a, b = r.contenidos[:2]
            self.assertEqual(a.sha256_fisico, b.sha256_fisico)
            self.assertNotEqual(a.artefacto, b.artefacto)
            self.assertNotEqual((c.raiz / a.relativa).stat().st_ino, (c.raiz / b.relativa).stat().st_ino)

    def test_copia_sin_depender_de_raiz_rc5_historica(self):
        with entorno_conservacion() as c:
            with entorno_materializacion() as m:
                origen = m.raiz
                r = c.conservar(unidad(m))
            self.assertFalse(origen.exists())
            nuevo = recuperar_generacion(c.raiz, r.control)
            self.assertEqual(nuevo.estado, R.VERIFICADA)
            self.assertEqual(nuevo.unidad.materializaciones, r.unidad.materializaciones)

    def test_generacion_solo_referencias_externas(self):
        with entorno_conservacion() as c:
            r = c.conservar(unidad())
            self.assertEqual(r.estado, R.VERIFICADA)
            self.assertEqual(len(r.contenidos), 4)
            self.assertTrue(all(x.relativa is None and x.sha256_fisico is None
                and x.estado_actual is L.NO_DISPONIBLE for x in r.contenidos))
            self.assertFalse(any(p.suffix == ".bin" for p in c.raiz.iterdir()))

    def test_referencia_externa_con_evidencia_antigua_no_se_abre(self):
        with entorno_conservacion() as c:
            with entorno_materializacion() as m:
                u = unidad(m)
                u = replace(u, externos=tuple(a.referencia for a in u.inventario.artefactos))
            with patch("spica.artefactos.conservacion.verificar_fisicamente", side_effect=AssertionError("no abrir")):
                r = c.conservar(u)
            self.assertEqual(r.estado, R.VERIFICADA)
            self.assertTrue(all(x.estado_actual is L.NO_DISPONIBLE for x in r.contenidos))

    def test_archivo_vacio_legitimo(self):
        inv = inventario()
        with entorno_materializacion() as m, entorno_conservacion() as c:
            r = publicar(m, solicitud(2, b"", inv=inv), b"")
            u = UnidadConservacion(inv, (r,), tuple(a.referencia for i,a in enumerate(inv.artefactos) if i != 2))
            r = c.conservar(u)
            self.assertEqual(r.contenidos[0].size_bytes, 0)
            self.assertEqual(r.contenidos[0].sha256_fisico, hashlib.sha256(b"").hexdigest())

    def test_archivo_ausente_no_se_confunde_con_hash_fallido(self):
        with entorno_materializacion() as m, entorno_conservacion() as c:
            r = c.conservar(unidad(m))
            (c.raiz / "datos-002.bin").unlink()
            v = recuperar_generacion(c.raiz, r.control)
            self.assertEqual(v.estado, R.INCOMPLETA)
            self.assertEqual(v.contenidos[2].estado_actual, L.AUSENTE)
            self.assertIsNone(v.contenidos[2].sha256_fisico)

    def test_corrupcion_misma_longitud_se_lee_y_detecta(self):
        with entorno_materializacion() as m, entorno_conservacion() as c:
            u = unidad(m)
            r = c.conservar(u)
            malo = b"Z" * len(PREPARADO)
            (c.raiz / "datos-002.bin").write_bytes(malo)
            v = recuperar_generacion(c.raiz, r.control)
            self.assertEqual(v.estado, R.CORRUPTA)
            self.assertEqual(v.contenidos[2].sha256_fisico, hashlib.sha256(malo).hexdigest())
            self.assertEqual(v.contenidos[2].estado_actual, L.INCONSISTENTE)
            self.assertEqual((c.raiz / "datos-000.bin").read_bytes(), ORIGINAL)
            for r5, b in zip(u.materializaciones, DATOS):
                self.assertEqual((m.raiz / r5.referencia.nombre).read_bytes(), b)

    def test_tamano_incorrecto_sin_hash_inventado(self):
        with entorno_materializacion() as m, entorno_conservacion() as c:
            r = c.conservar(unidad(m))
            (c.raiz / "datos-000.bin").write_bytes(b"x")
            v = recuperar_generacion(c.raiz, r.control)
            self.assertEqual(v.estado, R.CORRUPTA)
            self.assertIsNone(v.contenidos[0].sha256_fisico)
            self.assertFalse(v.contenidos[0].lectura_completa)

    def test_manifiesto_ausente_y_no_reparado(self):
        with entorno_conservacion() as c:
            r = c.conservar(unidad())
            (c.raiz / "manifiesto.json").unlink()
            self.assertEqual(recuperar_generacion(c.raiz, r.control).estado, R.INCOMPLETA)
            self.assertFalse((c.raiz / "manifiesto.json").exists())

    def test_sello_ausente(self):
        with entorno_conservacion() as c:
            r = c.conservar(unidad())
            (c.raiz / "cierre.json").unlink()
            self.assertEqual(recuperar_generacion(c.raiz, r.control).estado, R.INCOMPLETA)

    def test_version_desconocida(self):
        with entorno_conservacion() as c:
            r = c.conservar(unidad())
            control = resellar(c, r.control, manifiesto=lambda m: m.update(version="futura"))
            v = recuperar_generacion(c.raiz, control)
            self.assertEqual(v.estado, R.INCOMPATIBLE)
            self.assertIn("version_generacion_incompatible", v.diagnosticos)

    def test_control_de_otra_generacion(self):
        with entorno_conservacion() as c:
            r = c.conservar(unidad())
            v = recuperar_generacion(c.raiz, ControlGeneracion("a" * 32, r.control.manifiesto_sha256))
            self.assertEqual(v.estado, R.INCOMPATIBLE)

    def test_sha_manifiesto_incorrecto(self):
        with entorno_conservacion() as c:
            r = c.conservar(unidad())
            v = recuperar_generacion(c.raiz, replace(r.control, manifiesto_sha256="0" * 64))
            self.assertIn("control_generacion_discrepante", v.diagnosticos)

    def test_hash_metadatos_incorrecto(self):
        with entorno_conservacion() as c:
            r = c.conservar(unidad())
            control = resellar(c, r.control, manifiesto=lambda m: m["metadatos"].update(sha256="0" * 64))
            self.assertEqual(recuperar_generacion(c.raiz, control).estado, R.INCOMPATIBLE)

    def test_ruta_inyectada_en_inventario_no_se_abre(self):
        with entorno_materializacion() as m, entorno_conservacion() as c:
            r = c.conservar(unidad(m))
            for ruta in ("../externo", "C:/SPICA_DATOS/raw/ajeno", "datos-000.bin:ads"):
                with self.subTest(ruta=ruta):
                    control = resellar(c, r.control, manifiesto=lambda m: m["archivos"][0].update(relativa=ruta))
                    v = recuperar_generacion(c.raiz, control)
                    self.assertEqual(v.estado, R.INCOMPATIBLE)
                    self.assertIn("inventario_manifiesto_discrepante", v.diagnosticos)

    def test_raiz_inyectada_rechazada_antes_de_sondearla(self):
        control = ControlGeneracion("a" * 32, "b" * 64)
        for ruta in ("../externo", "C:/SPICA_DATOS/raw", str(base_temporal() / "ajeno")):
            with self.subTest(ruta=ruta):
                v = recuperar_generacion(ruta, control)
                self.assertIn("raiz_generacion_no_admitida", v.diagnosticos)

    def test_archivo_ajeno_no_se_adopta_ni_elimina(self):
        with entorno_conservacion() as c:
            r = c.conservar(unidad())
            p = c.raiz / "ajeno.txt"
            p.write_bytes(b"propio de prueba adversarial")
            try:
                v = recuperar_generacion(c.raiz, r.control)
                self.assertEqual(v.estado, R.INCOMPATIBLE)
                self.assertTrue(p.exists())
            finally:
                p.unlink()  # Solo nuestra fixture, sin reparación de la generación.

    def test_enlace_duro_adicional_rechazado(self):
        with entorno_materializacion() as m, entorno_conservacion() as c, entorno_conservacion() as otro:
            r = c.conservar(unidad(m))
            alias = otro.raiz / "datos-000.bin"
            os.link(c.raiz / "datos-000.bin", alias)
            try:
                v = recuperar_generacion(c.raiz, r.control)
                self.assertEqual(v.estado, R.NO_DISPONIBLE)
                self.assertIn("archivo_no_regular_o_enlace_duro", v.diagnosticos)
            finally:
                alias.unlink()

    def test_interrupcion_antes_de_cierre_conserva_intencion(self):
        with entorno_conservacion() as c:
            def fallo(n):
                if n == "antes_cierre":
                    raise KeyboardInterrupt
            with patch.object(c, "_punto", side_effect=fallo), self.assertRaises(KeyboardInterrupt):
                c.conservar(unidad())
            self.assertTrue((c.raiz / "intencion.json").exists())
            self.assertTrue((c.raiz / "escritor.lock").exists())
            self.assertFalse((c.raiz / "cierre.json").exists())
            v = recuperar_generacion(c.raiz, ControlGeneracion("a" * 32, "b" * 64))
            self.assertEqual(v.estado, R.INCOMPLETA)

    def test_interrupcion_tras_enlace_no_se_repara(self):
        with entorno_conservacion() as c:
            def fallo(n):
                if n == "enlace_publicado:intencion.json":
                    raise OSError("ruta sensible")
            with patch.object(c, "_punto", side_effect=fallo), self.assertRaisesRegex(ErrorConservacion, "^escritura_generacion_no_disponible$"):
                c.conservar(unidad())
            self.assertEqual((c.raiz / "intencion.json").stat().st_nlink, 2)
            nombres = tuple(c.raiz.iterdir())
            v = recuperar_generacion(c.raiz, ControlGeneracion("a" * 32, "b" * 64))
            self.assertEqual(v.estado, R.INCOMPLETA)
            self.assertEqual(nombres, tuple(c.raiz.iterdir()))

    def test_raiz_ocupada_sin_sobrescritura(self):
        with entorno_conservacion() as c:
            r = c.conservar(unidad())
            antes = {p.name: p.read_bytes() for p in c.raiz.iterdir()}
            with self.assertRaisesRegex(ErrorConservacion, "raiz_destino_ocupada"):
                c.conservar(unidad())
            self.assertEqual(antes, {p.name: p.read_bytes() for p in c.raiz.iterdir()})
            self.assertEqual(recuperar_generacion(c.raiz, r.control).estado, R.VERIFICADA)

    def test_traslado_ocupado_preserva_destino(self):
        with entorno_conservacion() as a, entorno_conservacion() as b:
            r = a.conservar(unidad())
            b.conservar(unidad())
            antes = (b.raiz / "manifiesto.json").read_bytes()
            with self.assertRaisesRegex(ErrorConservacion, "raiz_destino_ocupada"):
                b.copiar_de(a.raiz, r.control)
            self.assertEqual((b.raiz / "manifiesto.json").read_bytes(), antes)

    def test_origen_fisico_corrupto_no_se_conserva(self):
        with entorno_materializacion() as m, entorno_conservacion() as c:
            u = unidad(m)
            (m.raiz / u.materializaciones[0].referencia.nombre).write_bytes(b"Z" * len(ORIGINAL))
            with self.assertRaisesRegex(ErrorConservacion, "origen_rc5_no_verificable"):
                c.conservar(u)
            self.assertFalse((c.raiz / "cierre.json").exists())

    def test_cancelacion_antes_de_escribir(self):
        with entorno_conservacion() as c:
            e = Event()
            e.set()
            with self.assertRaisesRegex(ErrorConservacion, "cancelacion_observada"):
                c.conservar(unidad(), cancelacion=e)
            self.assertEqual(tuple(c.raiz.iterdir()), ())

    def test_cancelacion_durante_publicacion(self):
        with entorno_conservacion() as c:
            e = Event()
            def parar(n):
                if n == "archivo_publicado:intencion.json":
                    e.set()
            with patch.object(c, "_punto", side_effect=parar), self.assertRaisesRegex(ErrorConservacion, "cancelacion_observada"):
                c.conservar(unidad(), cancelacion=e)
            self.assertFalse((c.raiz / "cierre.json").exists())

    def test_cancelacion_de_lector_no_inventa_corrupcion(self):
        with entorno_conservacion() as c:
            r = c.conservar(unidad())
            e = Event()
            e.set()
            v = recuperar_generacion(c.raiz, r.control, cancelacion=e)
            self.assertEqual(v.estado, R.NO_DISPONIBLE)
            self.assertIn("cancelacion_observada", v.diagnosticos)

    def test_restricciones_tecnicas_se_respetan(self):
        for uso in (USO_CONSERVAR, USO_RECUPERAR):
            with self.subTest(uso=uso), entorno_conservacion() as c:
                inv = inventario()
                primero = replace(inv.artefactos[0], restricciones_adicionales=(RestriccionQA("limite-rc6", T.BLOQUEO_USO_DEL_RESULTADO, (uso,), "fixture"),))
                u = unidad(inv=replace(inv, artefactos=(primero,) + inv.artefactos[1:]))
                with self.assertRaisesRegex(ErrorConservacion, "restriccion_impide_conservacion"):
                    c.conservar(u)
                self.assertEqual(tuple(c.raiz.iterdir()), ())

    def test_omision_de_restriccion_heredada_se_detecta(self):
        with entorno_conservacion() as c:
            r = c.conservar(unidad())
            v = codec.decodificar((c.raiz / "metadatos.json").read_bytes())
            ds, orden, ars = v[3]
            ars = tuple((ref, d, locales, ()) for ref, d, locales, heredadas in ars)
            b = codec.codificar(v[:3] + ((ds, orden, ars),))
            control = resellar(c, r.control, metadatos=b)
            q = recuperar_generacion(c.raiz, control)
            self.assertEqual(q.estado, R.INCOMPATIBLE)
            self.assertIn("clausura_linaje_o_restricciones_discrepante", q.diagnosticos)

    def test_registro_duplicado_y_enlace_faltante(self):
        inv = inventario()
        variantes = [replace(inv, artefactos=inv.artefactos + (inv.artefactos[0],)),
            replace(inv, producciones=(replace(inv.producciones[0], salidas=(ReferenciaArtefacto("ausente", "r1"),)),) + inv.producciones[1:])]
        for v in variantes:
            with self.subTest(v=len(v.artefactos)), self.assertRaisesRegex(ErrorConservacion, "linaje_rc6_contradictorio"):
                unidad(inv=v)

    def test_proyecto_incompatible_y_productora_duplicada(self):
        inv = inventario()
        p = inv.producciones[0]
        for v in (replace(inv, producciones=inv.producciones + (p,)),
                replace(inv, producciones=(replace(p, salidas=(inv.artefactos[1].referencia,)),) + inv.producciones[1:])):
            with self.assertRaisesRegex(ErrorConservacion, "linaje_rc6_contradictorio"):
                unidad(inv=v)

    def test_inventario_sin_cobertura_y_externo_inexistente(self):
        inv = inventario()
        with self.assertRaisesRegex(ErrorConservacion, "inventario_sin_cobertura"):
            UnidadConservacion(inv)
        with self.assertRaisesRegex(ErrorConservacion, "externos_duplicados_o_inexistentes"):
            UnidadConservacion(inv, externos=(ReferenciaArtefacto("ajeno", "r1"),))

    def test_evidencia_fisica_falsamente_confirmada_se_rechaza(self):
        with entorno_materializacion() as m:
            u = unidad(m)
            r = replace(u.materializaciones[0], sha256_temporal="0" * 64)
            with self.assertRaisesRegex(ErrorConservacion, "huellas_historicas_contradictorias"):
                replace(u, materializaciones=(r,) + u.materializaciones[1:])

    def test_materializacion_interrumpida_se_conserva_solo_como_externa(self):
        inv = inventario()
        with entorno_materializacion() as m, entorno_conservacion() as c:
            def fuente():
                yield b"prefijo"
                raise RuntimeError("interrupcion inventada")
            r5 = m.materializar_sintetico(solicitud(inv=inv), fuente())
            self.assertEqual(r5.estado_tecnico, S.PARCIAL)
            externos = tuple(a.referencia for a in inv.artefactos)
            u = UnidadConservacion(inv, (r5,), externos)
            r = c.conservar(u)
            self.assertEqual(r.estado, R.VERIFICADA)
            self.assertEqual(r.unidad.materializaciones[0].estado_tecnico, S.PARCIAL)
            self.assertTrue(all(x.relativa is None for x in r.contenidos))
            with self.assertRaisesRegex(ErrorConservacion, "materializacion_sin_cierre_acreditado"):
                replace(u, externos=tuple(a for a in externos if a != r5.solicitud.artefacto))

    def test_operacion_cancelada_no_se_promueve(self):
        inv = inventario()
        p = inv.producciones[1]
        op = replace(p.operacion, estado=S.CANCELADA)
        comp = inv.composiciones[0]
        comp = replace(comp, operaciones=tuple(replace(n, contexto=op) if n.contexto is p.operacion else n for n in comp.operaciones))
        inv = replace(inv, producciones=(inv.producciones[0], replace(p, operacion=op)), composiciones=(comp,))
        with entorno_conservacion() as c:
            r = c.conservar(unidad(inv=inv))
            self.assertEqual(r.unidad.inventario.producciones[1].operacion.estado, S.CANCELADA)

    def test_codec_determinista_y_referencias_canonicas(self):
        u = unidad()
        b = codec.codificar((u.inventario, u.externos))
        inv, refs = codec.decodificar(b)
        self.assertEqual(b, codec.codificar((inv, refs)))
        self.assertIs(inv.producciones[0].operacion, inv.composiciones[0].operaciones[0].contexto)
        self.assertEqual(inv, u.inventario)

    def test_codec_rechaza_claves_duplicadas_no_finitos_y_profundidad(self):
        for b in (b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":Infinity}', b'{"x":1e999}', b"[" * 70 + b"0" + b"]" * 70):
            with self.subTest(b=b[:20]), self.assertRaises(ValueError):
                codec.leer_json(b)

    def test_codec_rechaza_campo_tipo_y_version_inesperados(self):
        base = codec.codificar((unidad().inventario,))
        for modo in ("campo", "tipo", "version", "clase", "constante"):
            v = codec.leer_json(base)
            fila = next(x for x in v["objetos"] if x["clase"].endswith(":DescriptorArtefacto"))
            if modo == "campo":
                fila["campos"]["inesperado"] = "x"
            elif modo == "tipo":
                fila["campos"]["contenido_id"] = 5
            elif modo == "version":
                fila["campos"]["version_contrato"] = "futura"
            elif modo == "constante":
                fila["campos"]["revision_cientifica"]["valor"] = "evaluada"
            else:
                fila["clase"] = "os:system"
            with self.subTest(modo=modo), self.assertRaises((ValueError, TypeError)):
                codec.decodificar(codec.canonico(v))

    def test_codec_rechaza_ciclos_de_objetos_y_registros_ocultos(self):
        base = codec.codificar((unidad().inventario,))
        v = codec.leer_json(base)
        v["objetos"].append(v["objetos"][0])
        with self.assertRaises(ValueError):
            codec.decodificar(codec.canonico(v))
        v = codec.leer_json(base)
        v["objetos"][0]["campos"]["artefactos"] = {"tuple": [{"ref": 0}]}
        with self.assertRaisesRegex(ValueError, "ciclo_objetos"):
            codec.decodificar(codec.canonico(v))

    def test_codec_sin_pickle_evaluacion_o_rutas_ejecutables(self):
        with self.assertRaises(ValueError):
            codec.codificar(Path("C:/SPICA_DATOS/raw/ajeno"))
        with self.assertRaises(ValueError):
            codec.codificar(lambda: None)
        b = codec.codificar(("__import__('os').remove('x')",))
        self.assertEqual(codec.decodificar(b), ("__import__('os').remove('x')",))
        for d in ("no es decimal", "NaN", "Infinity"):
            b = codec.canonico(dict(version=codec.VERSION, objetos=[], raiz={"decimal": d}))
            with self.subTest(decimal=d), self.assertRaises(ValueError):
                codec.decodificar(b)

    def test_limites_metadatos_e_inventario(self):
        with self.assertRaises(ValueError):
            codec.leer_json(b" " * (codec.MAX_METADATOS + 1))
        with self.assertRaises(ValueError):
            codec.codificar("x" * (codec.MAX_METADATOS + 1))
        with self.assertRaises(ErrorConservacion):
            UnidadConservacion(InventarioArtefactos(()))

    def test_recuperacion_desde_otro_proceso_sin_escrituras_o_red(self):
        with entorno_materializacion() as m, entorno_conservacion() as c:
            r = c.conservar(unidad(m))
            v = otro_proceso(c.raiz, r.control)
            self.assertEqual(v["estado"], R.VERIFICADA.value)
            self.assertEqual(v["hashes"], [hashlib.sha256(x).hexdigest() for x in DATOS])
            self.assertEqual(v["estados"][-1], S.PARCIAL.value)
            self.assertIn("bloqueo-rc4", v["restricciones"][-1])
            self.assertFalse(v["custodia"])

    def test_productor_terminado_traslado_y_lector_independiente(self):
        codigo = '''
import json
from spica.artefactos.conservacion import entorno_conservacion
from spica.artefactos.materializacion import entorno_materializacion
from test_conservacion_rc6 import unidad
with entorno_conservacion(disponer_al_salir=False) as c:
    with entorno_materializacion() as m:
        r = c.conservar(unidad(m))
    print(json.dumps(dict(raiz=str(c.raiz), control=[r.control.generacion_id,r.control.manifiesto_sha256], nombres=sorted(p.name for p in c.raiz.iterdir()))))
'''
        a = subprocess.run([sys.executable, "-B", "-c", codigo], capture_output=True, text=True, timeout=60, check=True)
        d = json.loads(a.stdout)
        raiz = Path(d["raiz"])
        control = ControlGeneracion(*d["control"])
        # Única raíz creada por nuestro hijo. Limpieza explícita sin recursión ni
        # adopción de otros nombres. Ante una diferencia, preservar y fallar.
        def disponer():
            fs = ArchivosGeneracion.abrir(raiz)
            self.assertEqual(list(fs.nombres()), d["nombres"])
            for n in d["nombres"]:
                p, s = fs.regular(n)
                self.assertTrue(stat.S_ISREG(s.st_mode))
                p.unlink()
            fs.validar()
            fs.raiz.rmdir()
        try:
            b = otro_proceso(raiz, control)
            self.assertEqual(b["estado"], R.VERIFICADA.value)
            with entorno_conservacion() as destino:
                r = destino.copiar_de(raiz, control)
                self.assertEqual(r.estado, R.VERIFICADA)
                self.assertNotEqual(raiz, destino.raiz)
                disponer()
                raiz = None
                v = otro_proceso(destino.raiz, control)
                self.assertEqual(v, b)
        finally:
            if raiz is not None:
                disponer()

    def test_generacion_retirada_no_se_recrea(self):
        with entorno_conservacion() as c:
            raiz = c.raiz
            r = c.conservar(unidad())
        v = recuperar_generacion(raiz, r.control)
        self.assertEqual(v.estado, R.INCOMPLETA)
        self.assertFalse(raiz.exists())

    def test_reader_no_inicia_catalogo_ni_transporte(self):
        with entorno_conservacion() as c:
            r = c.conservar(unidad())
            with patch("sqlite3.connect", side_effect=AssertionError("SQLite prohibido")), patch("socket.socket", side_effect=AssertionError("red prohibida")):
                self.assertEqual(recuperar_generacion(c.raiz, r.control).estado, R.VERIFICADA)

    def test_fallo_escritura_y_privacidad_sin_cierre_ficticio(self):
        with entorno_conservacion() as c:
            with patch("spica.artefactos._generacion_rc6.os.fsync", side_effect=OSError("credencial y ruta sensible")), self.assertRaisesRegex(ErrorConservacion, "^escritura_generacion_no_disponible$"):
                c.conservar(unidad())
            self.assertFalse((c.raiz / "cierre.json").exists())

    def test_fallo_lectura_no_declara_corrupcion(self):
        with entorno_conservacion() as c:
            r = c.conservar(unidad())
            with patch("spica.artefactos.conservacion.leer_metadatos", side_effect=PermissionError("ruta sensible")):
                v = recuperar_generacion(c.raiz, r.control)
            self.assertEqual(v.estado, R.NO_DISPONIBLE)
            self.assertEqual(v.diagnosticos, ("lectura_generacion_no_disponible",))

    def test_contratos_inmutables_y_control_explicito(self):
        u = unidad()
        with self.assertRaises(FrozenInstanceError):
            u.externos = ()
        with self.assertRaises(ErrorConservacion):
            ControlGeneracion("ruta/inesperada", "a" * 64)
        with self.assertRaises(ErrorConservacion):
            recuperar_generacion("x", None)

    def test_ciclo_linaje_rechazado_por_inspector_rc4(self):
        inv = inventario()
        p, q = inv.producciones
        inv = replace(inv, producciones=(replace(p, entradas=q.salidas), q))
        self.assertIn("ciclo_linaje", [d.codigo for d in inspeccionar_linaje(inv).diagnosticos])
        with self.assertRaisesRegex(ErrorConservacion, "linaje_rc6_contradictorio"):
            unidad(inv=inv)

    def test_resultado_de_operacion_inexistente_se_rechaza(self):
        inv = inventario()
        p = inv.producciones[1]
        op = replace(p.operacion, referencias_resultado=("resultado-inexistente",))
        comp = inv.composiciones[0]
        comp = replace(comp, operaciones=tuple(replace(n, contexto=op) if n.contexto is p.operacion else n for n in comp.operaciones))
        inv = replace(inv, producciones=(inv.producciones[0], replace(p, operacion=op)), composiciones=(comp,))
        with self.assertRaisesRegex(ErrorConservacion, "linaje_rc6_contradictorio"):
            unidad(inv=inv)

    def test_revision_duplicada_conflictiva_no_desaparece(self):
        inv = inventario()
        otro = replace(inv.artefactos[0], incertidumbres=("diferencia conocida",))
        inv = replace(inv, artefactos=inv.artefactos + (otro,))
        with self.assertRaisesRegex(ErrorConservacion, "linaje_rc6_contradictorio"):
            unidad(inv=inv)

    def test_metadatos_alterados_en_lector_se_detectan(self):
        with entorno_conservacion() as c:
            r = c.conservar(unidad())
            from spica.artefactos.conservacion import leer_metadatos as original
            contador = 0
            def mutar(fs, nombre, limite):
                nonlocal contador
                if nombre == "metadatos.json":
                    contador += 1
                    if contador == 2:
                        return b"alterado", 8, "0" * 64
                return original(fs, nombre, limite)
            with patch("spica.artefactos.conservacion.leer_metadatos", side_effect=mutar):
                v = recuperar_generacion(c.raiz, r.control)
            self.assertNotEqual(v.estado, R.VERIFICADA)
            self.assertIn("metadatos_cambiaron_durante_recuperacion", v.diagnosticos)

    def test_enlace_publicacion_ocupado_no_sobrescribe(self):
        with entorno_conservacion() as c:
            from spica.artefactos._generacion_rc6 import os as sistema
            original = sistema.link
            def ocupar(a, b):
                if Path(b).name == "manifiesto.json":
                    # Registro de propiedad solo para disposición de esta fixture.
                    with c._fs.abrir_nuevo("manifiesto.json") as f:
                        f.write(b"ocupado por prueba")
                return original(a, b)
            with patch("spica.artefactos._generacion_rc6.os.link", side_effect=ocupar), self.assertRaises(ErrorConservacion):
                c.conservar(unidad())
            self.assertEqual((c.raiz / "manifiesto.json").read_bytes(), b"ocupado por prueba")
            self.assertFalse((c.raiz / "cierre.json").exists())

    def test_reparse_o_junction_rechazado_por_adaptador(self):
        with entorno_conservacion() as c:
            r = c.conservar(unidad())
            with patch("spica.artefactos._generacion_rc6.segura", side_effect=ErrorArchivoExperimental("reparse_point_no_admitido")):
                v = recuperar_generacion(c.raiz, r.control)
            self.assertEqual(v.estado, R.NO_DISPONIBLE)
            self.assertIn("reparse_point_no_admitido", v.diagnosticos)

    def test_evidencia_incoherente_tampoco_se_acepta_como_externa(self):
        with entorno_materializacion() as m:
            u = unidad(m)
            malo = replace(u.materializaciones[0], bytes_escritos=0)
            with self.assertRaisesRegex(ErrorConservacion, "huellas_historicas_contradictorias"):
                UnidadConservacion(u.inventario, (malo,), tuple(a.referencia for a in u.inventario.artefactos))

    def test_generacion_con_tamano_booleano_fuera_de_contrato(self):
        inv = inventario()
        with entorno_materializacion() as m, entorno_conservacion() as c:
            r5 = publicar(m, solicitud(2, b"", inv=inv), b"")
            u = UnidadConservacion(inv, (r5,), tuple(a.referencia for i,a in enumerate(inv.artefactos) if i != 2))
            r = c.conservar(u)
            control = resellar(c, r.control, manifiesto=lambda m: m["archivos"][0].update(size_bytes=False))
            self.assertEqual(recuperar_generacion(c.raiz, control).estado, R.INCOMPATIBLE)

    def test_evidencia_raw_externa_es_historica_sin_comprobacion_actual(self):
        from spica.adquisicion.readquisicion.modelos import EvidenciaLocal
        from spica.adquisicion.catalogo.modelos import ProcedenciaCatalogo
        from spica.interoperabilidad.perfiles import EntradaPerfil
        a = inventario().artefactos[0]
        e = a.entrada_perfil.entrada
        proc = ProcedenciaCatalogo("fixture:rc6", datetime(2026, 11, 16, tzinfo=timezone.utc), "cotejo ficticio", "fixture:sin-RAW-real")
        ev = EvidenciaLocal(L.INTEGRO, datetime(2026, 11, 16, tzinfo=timezone.utc), proc,
            e.sha256_declarado, e.size_bytes_declarado, "activo-ficticio-no-existe")
        e = replace(e, asset_id=ev.activo_id, evidencia_local=ev)
        a = replace(a, entrada_perfil=EntradaPerfil(e, a.entrada_perfil.perfil))
        inv = InventarioArtefactos((a,))
        with entorno_conservacion() as c:
            r = c.conservar(UnidadConservacion(inv, externos=(a.referencia,)))
            self.assertEqual(r.estado, R.VERIFICADA)
            self.assertEqual(r.contenidos[0].estado_actual, L.NO_DISPONIBLE)
            self.assertIsNone(r.contenidos[0].sha256_fisico)
            self.assertEqual(r.unidad.inventario.artefactos[0].entrada_perfil.entrada.evidencia_local, ev)

    def test_creacion_falla_sin_revelar_ruta(self):
        with patch.object(ArchivosGeneracion, "crear", side_effect=PermissionError("ruta y token sensibles")):
            with self.assertRaisesRegex(ErrorConservacion, "^entorno_conservacion_no_creado$"):
                with entorno_conservacion():
                    self.fail("no debe crearse")

    def test_preserva_numeros_y_tiempos_civiles_sin_convertir(self):
        valores = (Decimal("-3.1400"), date(2026, 11, 16), datetime(2026, 11, 16, 2, 3),
            datetime(2026, 11, 16, tzinfo=timezone.utc), -0.0, "zona desconocida")
        b = codec.codificar(valores)
        restaurados = codec.decodificar(b)
        self.assertEqual(restaurados, valores)
        self.assertEqual(str(restaurados[0]), "-3.1400")
        self.assertIsNone(restaurados[2].tzinfo)
        self.assertIs(restaurados[3].tzinfo, timezone.utc)


if __name__ == "__main__":
    unittest.main()
