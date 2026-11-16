"""RC5: solo bytes inventados y raíces TEMP exclusivas, nunca datos operativos."""

from dataclasses import FrozenInstanceError, replace
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
from threading import Event
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from spica.artefactos import InventarioArtefactos, ReferenciaArtefacto, TipoArtefacto
from spica.artefactos.materializacion import (
    VERSION_MATERIALIZACION, EstadoPublicacion as P, InformeMaterializacion,
    LimitesMaterializacion, ReferenciaFisica, SolicitudMaterializacion,
    USO_MATERIALIZAR, USO_VERIFICAR, entorno_materializacion, verificar_fisicamente,
)
from spica.artefactos._archivos_rc5 import ArchivosTEMP, ErrorArchivoExperimental, LectorControlado
from spica.adquisicion.nucleo.modelos import EstadoIntegridad as I
from spica.adquisicion.readquisicion.modelos import EstadoLocal
from spica.calidad.restricciones import RestriccionQA, TipoRestriccionQA as TR
from spica.contextos import EstadoOperacion as S
from spica.interoperabilidad.perfiles import EntradaPerfil
from test_artefactos_rc4 import piloto as piloto_rc4, CUERPO as ORIGINAL

PREPARADO = b"RC5: preparado sintetico, no transformado.\n"
DERIVADO = b"RC5: derivado sintetico parcial, no cientifico.\n"


def inventario():
    inv = piloto_rc4()
    a, otro, preparado, derivado = inv.artefactos
    return replace(inv, artefactos=(a, otro, replace(preparado, contenido_id="contenido-preparado"),
        replace(derivado, contenido_id="contenido-derivado")))


def solicitud(indice=2, datos=PREPARADO, *, inv=None, **kw):
    inv = inventario() if inv is None else inv
    d = dict(inventario=inv, artefacto=inv.artefactos[indice].referencia, tamano_esperado=len(datos))
    d.update(kw)
    return SolicitudMaterializacion(**d)


def codigos(r):
    return tuple(d.codigo for d in r.diagnosticos)


def publicar(m, s=None, datos=PREPARADO):
    return m.materializar_sintetico(solicitud(datos=datos) if s is None else s, (datos,) if datos else ())


class MaterializacionRC5Tests(unittest.TestCase):
    def test_publica_reabre_y_hash_fisico_coincide(self):
        with entorno_materializacion() as m:
            raiz = m.raiz
            r = publicar(m)
            self.assertEqual(r.estado_tecnico, S.CONCLUIDA)
            self.assertEqual(r.publicacion, P.VERIFICADA)
            self.assertEqual(r.sha256_recibido, hashlib.sha256(PREPARADO).hexdigest())
            self.assertEqual(r.sha256_temporal, r.sha256_recibido)
            self.assertEqual(r.verificacion.sha256_fisico, r.sha256_recibido)
            self.assertEqual(r.verificacion.bytes_leidos, len(PREPARADO))
            self.assertEqual((m.raiz / r.referencia.nombre).read_bytes(), PREPARADO)
            self.assertEqual(r.temporales, ())
            self.assertFalse(r.productor_ejecutado)
            self.assertFalse(r.persistencia_durable)
        self.assertFalse(raiz.exists())

    def test_verificacion_repetida_sin_cambios(self):
        with entorno_materializacion() as m:
            r = publicar(m)
            ruta = m.raiz / r.referencia.nombre
            antes = (ruta.stat(), ruta.read_bytes())
            v1 = verificar_fisicamente(r.solicitud, r.referencia)
            v2 = verificar_fisicamente(r.solicitud, r.referencia)
            self.assertEqual((v1.sha256_fisico, v1.size_bytes_observado), (v2.sha256_fisico, v2.size_bytes_observado))
            self.assertEqual(v1.integridad, I.VERIFICADA)
            self.assertEqual(ruta.read_bytes(), antes[1])
            self.assertEqual(ruta.stat().st_mtime_ns, antes[0].st_mtime_ns)

    def test_vacio_legitimo(self):
        with entorno_materializacion() as m:
            r = publicar(m, datos=b"")
            self.assertEqual(r.estado_tecnico, S.CONCLUIDA)
            self.assertEqual(r.verificacion.bytes_leidos, 0)
            self.assertEqual(r.verificacion.sha256_fisico, hashlib.sha256(b"").hexdigest())

    def test_archivo_ausente_no_es_integridad_fallida(self):
        with entorno_materializacion() as m:
            r = publicar(m)
            (m.raiz / r.referencia.nombre).unlink()  # Únicamente nuestra fixture.
            v = verificar_fisicamente(r.solicitud, r.referencia)
            self.assertEqual(v.estado_local, EstadoLocal.AUSENTE)
            self.assertEqual(v.integridad, I.PENDIENTE)
            self.assertIsNone(v.sha256_fisico)

    def test_corrupcion_de_igual_tamano_detectada(self):
        with entorno_materializacion() as m:
            r = publicar(m)
            (m.raiz / r.referencia.nombre).write_bytes(b"X" * len(PREPARADO))
            v = verificar_fisicamente(r.solicitud, r.referencia)
            self.assertEqual(v.integridad, I.FALLIDA)
            self.assertTrue(v.lectura_completa)
            self.assertIn("hash_fisico_incorrecto", codigos(v))

    def test_tamano_fisico_incorrecto_sin_inventar_hash(self):
        with entorno_materializacion() as m:
            r = publicar(m)
            (m.raiz / r.referencia.nombre).write_bytes(b"corto")
            v = verificar_fisicamente(r.solicitud, r.referencia)
            self.assertEqual(v.integridad, I.FALLIDA)
            self.assertIsNone(v.sha256_fisico)
            self.assertFalse(v.lectura_completa)
            self.assertEqual(v.bytes_leidos, 0)

    def test_tamano_recibido_incorrecto_no_publica(self):
        with entorno_materializacion() as m:
            r = publicar(m, solicitud(tamano_esperado=len(PREPARADO) + 1))
            self.assertIn("tamano_recibido_incorrecto", codigos(r))
            self.assertIsNone(r.referencia)
            self.assertEqual(r.publicacion, P.TEMPORAL)

    def test_hash_esperado_incorrecto_no_publica(self):
        with entorno_materializacion() as m:
            r = publicar(m, solicitud(sha256_esperado="0" * 64))
            self.assertIn("hash_recibido_incorrecto", codigos(r))
            self.assertIsNone(r.referencia)
            self.assertEqual(r.sha256_recibido, hashlib.sha256(PREPARADO).hexdigest())

    def test_referencia_de_hash_incorrecto_comprobada_por_lectura(self):
        with entorno_materializacion() as m:
            r = publicar(m)
            v = verificar_fisicamente(r.solicitud, replace(r.referencia, sha256_recibido="0" * 64))
            self.assertEqual(v.integridad, I.FALLIDA)
            self.assertEqual(v.sha256_fisico, r.sha256_recibido)

    def test_destino_ocupado_preserva_original_sin_reintentar(self):
        with entorno_materializacion() as m:
            primero = publicar(m)
            ruta = m.raiz / primero.referencia.nombre
            antes = (ruta.stat().st_ino, ruta.read_bytes())
            with patch("spica.artefactos.materializacion.os.link", side_effect=AssertionError("no debe publicar")):
                segundo = publicar(m)
            self.assertIn("destino_ocupado", codigos(segundo))
            self.assertEqual((ruta.stat().st_ino, ruta.read_bytes()), antes)

    def test_colision_entre_comprobacion_y_enlace_no_sobrescribe(self):
        with entorno_materializacion() as m:
            with patch("spica.artefactos.materializacion.os.link", side_effect=FileExistsError) as link:
                r = publicar(m)
            self.assertEqual(link.call_count, 1)
            self.assertIn("destino_ocupado", codigos(r))
            self.assertIsNone(r.referencia)

    def test_rutas_externas_y_traversal_rechazadas_antes_de_sondear(self):
        for identidad in ("..", "../escape", "C:\\fuera", "/tmp/externo", "\\\\servidor\\ruta"):
            with self.subTest(identidad=identidad), patch("spica.artefactos._archivos_rc5.base_temporal", side_effect=AssertionError("no sondear")):
                with self.assertRaises(ErrorArchivoExperimental):
                    ArchivosTEMP(identidad)
        with entorno_materializacion() as m:
            for nombre in ("../escape", "C:\\fuera", "CON", "a:ads", "/absoluta"):
                with self.subTest(nombre=nombre), self.assertRaises(ErrorArchivoExperimental):
                    m._archivos.ruta(nombre)

    def test_ids_literales_no_se_interpretan_como_rutas(self):
        inv = inventario()
        a = inv.artefactos[0]
        ep = a.entrada_perfil
        e = replace(ep.entrada, objeto=replace(ep.entrada.objeto, object_id="../../CON:original"))
        a = replace(a, entrada_perfil=EntradaPerfil(e, ep.perfil))
        inv = InventarioArtefactos((a,))
        s = solicitud(0, ORIGINAL, inv=inv)
        with entorno_materializacion() as m:
            r = publicar(m, s, ORIGINAL)
            self.assertEqual(r.estado_tecnico, S.CONCLUIDA)
            self.assertTrue((m.raiz / r.referencia.nombre).is_relative_to(m.raiz))
            self.assertRegex(r.referencia.nombre, r"^a-[0-9a-f]{64}\.bin$")
            self.assertEqual(a.referencia.object_id, "../../CON:original")

    def test_symlink_y_junction_simulados_no_se_siguen(self):
        with entorno_materializacion() as m:
            r = publicar(m)
            for atributo in ("is_symlink", "is_junction"):
                with self.subTest(atributo=atributo), patch.object(Path, atributo, return_value=True):
                    v = verificar_fisicamente(r.solicitud, r.referencia)
                self.assertEqual(v.estado_local, EstadoLocal.NO_DISPONIBLE)
                self.assertFalse(v.lectura_completa)

    def test_reparse_point_simulado_rechazado(self):
        with entorno_materializacion() as m:
            r = publicar(m)
            original = Path.lstat
            def lstat(p, *args, **kwargs):
                s = original(p, *args, **kwargs)
                if p.name != r.referencia.nombre:
                    return s
                valores = {k: getattr(s, k) for k in dir(s) if k.startswith("st_")}
                valores["st_file_attributes"] = getattr(s, "st_file_attributes", 0) | stat.FILE_ATTRIBUTE_REPARSE_POINT
                return SimpleNamespace(**valores)
            with patch.object(Path, "lstat", new=lstat):
                v = verificar_fisicamente(r.solicitud, r.referencia)
            self.assertEqual(v.estado_local, EstadoLocal.NO_DISPONIBLE)

    def test_enlace_duro_real_rechazado(self):
        with entorno_materializacion() as m:
            r = publicar(m)
            alias = m.raiz / "alias-creado-por-esta-prueba"
            os.link(m.raiz / r.referencia.nombre, alias)
            try:
                v = verificar_fisicamente(r.solicitud, r.referencia)
                self.assertEqual(v.estado_local, EstadoLocal.NO_DISPONIBLE)
                self.assertIn("archivo_no_regular_o_enlace_duro", codigos(v))
            finally:
                alias.unlink()  # Nuestro alias sintético, no el archivo publicado.

    def test_identidad_proyecto_incompatible_no_abre_archivos(self):
        inv = inventario()
        with entorno_materializacion() as m:
            r = publicar(m, solicitud(0, ORIGINAL, inv=inv), ORIGINAL)
            s = solicitud(1, ORIGINAL, inv=inv)
            with patch.object(ArchivosTEMP, "regular", side_effect=AssertionError("no debe leer")):
                v = verificar_fisicamente(s, r.referencia)
            self.assertIn("referencia_no_corresponde_a_descriptor", codigos(v))

    def test_operacion_productora_y_version_incompatibles(self):
        inv = inventario()
        with entorno_materializacion() as m:
            r = publicar(m, solicitud(inv=inv))
            p = replace(inv.producciones[0], metodo_version="otra-version")
            s = solicitud(inv=replace(inv, producciones=(p, inv.producciones[1])))
            v = verificar_fisicamente(s, r.referencia)
            self.assertIn("referencia_no_corresponde_a_descriptor", codigos(v))

    def test_revision_y_contenido_de_referencia_no_se_realinean(self):
        with entorno_materializacion() as m:
            r = publicar(m)
            for ref in (replace(r.referencia, artefacto=replace(r.referencia.artefacto, revision="otra")),
                        replace(r.referencia, contenido_id="otro-contenido")):
                with self.subTest(ref=ref):
                    self.assertIn("referencia_no_corresponde_a_descriptor", codigos(verificar_fisicamente(r.solicitud, ref)))

    def test_restriccion_heredada_bloquea_sin_escrituras(self):
        inv = inventario()
        a = inv.artefactos[0]
        bloqueo = RestriccionQA("bloqueo-fisico", TR.BLOQUEO_USO_DEL_RESULTADO, (USO_MATERIALIZAR,), "fixture")
        a = replace(a, restricciones_adicionales=a.restricciones_adicionales + (bloqueo,))
        inv = replace(inv, artefactos=(a, *inv.artefactos[1:]))
        with entorno_materializacion() as m:
            r = publicar(m, solicitud(inv=inv))
            self.assertIn("restriccion_impide_materializacion", codigos(r))
            self.assertIn(bloqueo, tuple(rp.restriccion for rp in r.restricciones))
            self.assertEqual(tuple(m.raiz.iterdir()), ())

    def test_bloqueo_de_relectura_impide_publicacion_inverificable(self):
        inv = inventario()
        a = replace(inv.artefactos[2], restricciones_adicionales=(RestriccionQA("no-leer", TR.BLOQUEO_USO_DEL_RESULTADO,
            (USO_VERIFICAR,), "fixture"),))
        inv = replace(inv, artefactos=(*inv.artefactos[:2], a, inv.artefactos[3]))
        with entorno_materializacion() as m:
            r = publicar(m, solicitud(inv=inv))
            self.assertIn("restriccion_impide_verificacion", codigos(r))
            self.assertEqual(tuple(m.raiz.iterdir()), ())

    def test_publicacion_tecnica_no_promueve_operacion_parcial(self):
        s = solicitud(3, DERIVADO)
        antes = s.inventario.producciones[1].operacion
        with entorno_materializacion() as m:
            r = publicar(m, s, DERIVADO)
            self.assertEqual(r.estado_tecnico, S.CONCLUIDA)
            self.assertEqual(r.solicitud.descriptor.estado_logico.value, "parcial")
            self.assertIs(r.solicitud.inventario.producciones[1].operacion, antes)
            self.assertEqual(antes.estado, S.PARCIAL)
            self.assertFalse(r.productor_ejecutado)

    def test_cancelacion_previa_y_durante_escritura(self):
        for durante in (False, True):
            evento = Event()
            if not durante:
                evento.set()
            with self.subTest(durante=durante), entorno_materializacion() as m:
                def punto(nombre):
                    if durante and nombre == "bloque_escrito":
                        evento.set()
                with patch.object(m, "_punto", side_effect=punto):
                    r = m.materializar_sintetico(solicitud(), (PREPARADO,), cancelacion=evento)
                self.assertEqual(r.estado_tecnico, S.CANCELADA)
                self.assertIsNone(r.referencia)

    def test_operacion_cancelada_se_conserva_como_cancelada(self):
        inv = inventario()
        p = inv.producciones[1]
        op = replace(p.operacion, estado=S.CANCELADA)
        p = replace(p, operacion=op)
        c = inv.composiciones[0]
        c = replace(c, operaciones=tuple(replace(n, contexto=op) if n.contexto.operacion_id == op.operacion_id else n for n in c.operaciones))
        inv = replace(inv, producciones=(inv.producciones[0], p), composiciones=(c,))
        with entorno_materializacion() as m:
            r = publicar(m, solicitud(3, DERIVADO, inv=inv), DERIVADO)
            self.assertEqual(r.estado_tecnico, S.CONCLUIDA)
            self.assertEqual(op.estado, S.CANCELADA)
            self.assertEqual(r.solicitud.descriptor.estado_logico.value, "parcial")

    def test_fuente_interrumpida_conserva_prefijo_sin_hash_final(self):
        def bloques():
            yield b"prefijo"
            raise RuntimeError("detalle sensible que no debe registrarse")
        with entorno_materializacion() as m:
            r = m.materializar_sintetico(solicitud(), bloques())
            self.assertEqual(r.estado_tecnico, S.PARCIAL)
            self.assertEqual(r.bytes_escritos, 7)
            self.assertIsNone(r.sha256_recibido)
            self.assertEqual((m.raiz / r.temporales[0]).read_bytes(), b"prefijo")
            self.assertNotIn("sensible", str(r.diagnosticos))

    def test_keyboardinterrupt_propaga_informe_y_cierra_recursos(self):
        def bloques():
            yield b"prefijo"
            raise KeyboardInterrupt()
        with entorno_materializacion() as m:
            raiz = m.raiz
            with self.assertRaises(KeyboardInterrupt) as exc:
                m.materializar_sintetico(solicitud(), bloques())
            self.assertEqual(exc.exception.informe_rc5.estado_tecnico, S.PARCIAL)
            self.assertFalse((raiz / "escritor.lock").exists())
        self.assertFalse(raiz.exists())

    def test_escritura_corta_detectada(self):
        with entorno_materializacion() as m:
            def escribir(f, b):
                return f.write(b[:2])
            with patch.object(m, "_escribir", side_effect=escribir):
                r = publicar(m)
            self.assertEqual(r.estado_tecnico, S.PARCIAL)
            self.assertEqual(r.bytes_escritos, 2)
            self.assertIn("escritura_incompleta", codigos(r))

    def test_error_disco_con_diagnostico_sin_detalle_sensible(self):
        with entorno_materializacion() as m:
            with patch.object(m, "_escribir", side_effect=OSError("secret=contenido-no-publicable")):
                r = publicar(m)
            self.assertEqual(r.estado_tecnico, S.FALLIDA)
            self.assertIn("error_escritura_o_publicacion", codigos(r))
            self.assertNotIn("secret", str(r.diagnosticos))

    def test_fallo_fsync_no_publica(self):
        with entorno_materializacion() as m:
            with patch("spica.artefactos.materializacion.os.fsync", side_effect=OSError):
                r = publicar(m)
            self.assertIsNone(r.referencia)
            self.assertEqual(r.publicacion, P.TEMPORAL)

    def test_interrupcion_tras_enlace_no_finge_verificacion(self):
        with entorno_materializacion() as m:
            def punto(nombre):
                if nombre == "enlace_publicado":
                    raise OSError("interrupcion-simulada")
            with patch.object(m, "_punto", side_effect=punto):
                r = publicar(m)
            self.assertEqual(r.publicacion, P.PUBLICADA)
            self.assertEqual(r.estado_tecnico, S.PARCIAL)
            self.assertIsNone(r.verificacion)
            self.assertEqual(len(r.temporales), 1)
            self.assertEqual(verificar_fisicamente(r.solicitud, r.referencia).estado_local, EstadoLocal.NO_DISPONIBLE)

    def test_corrupcion_entre_relecturas_no_repara_destino(self):
        with entorno_materializacion() as m:
            def punto(nombre):
                if nombre == "antes_relectura_final":
                    ruta = next(m.raiz.glob("a-*.bin"))
                    ruta.write_bytes(b"Z" * len(PREPARADO))
            with patch.object(m, "_punto", side_effect=punto):
                r = publicar(m)
            self.assertEqual(r.publicacion, P.PUBLICADA)
            self.assertEqual(r.verificacion.integridad, I.FALLIDA)
            self.assertEqual((m.raiz / r.referencia.nombre).read_bytes(), b"Z" * len(PREPARADO))

    def test_temporal_alterado_antes_de_publicar_rechazado(self):
        with entorno_materializacion() as m:
            def punto(nombre):
                if nombre == "antes_publicacion":
                    ruta = next(m.raiz.glob("t-*.tmp"))
                    st = ruta.stat()
                    ruta.write_bytes(b"Z" * len(PREPARADO))
                    os.utime(ruta, ns=(st.st_atime_ns, st.st_mtime_ns + 10_000_000))
            with patch.object(m, "_punto", side_effect=punto):
                r = publicar(m)
            self.assertIn("temporal_cambio_antes_de_publicacion", codigos(r))
            self.assertIsNone(r.referencia)

    def test_limite_real_no_depende_de_tamano_declarado(self):
        s = solicitud(datos=b"12345678", limites=LimitesMaterializacion(8, 4))
        with entorno_materializacion() as m:
            r = m.materializar_sintetico(s, (b"1234", b"5678", b"EXTR"))
            self.assertIn("limite_entrada_excedido", codigos(r))
            self.assertEqual(r.bytes_recibidos, 12)
            self.assertEqual(r.bytes_escritos, 8)
            self.assertIsNone(r.referencia)

    def test_bloques_invalidos_no_se_interpretan_o_truncan(self):
        for bloques in ((b"",), ("texto",), (b"x" * 5,)):
            with self.subTest(bloques=bloques), entorno_materializacion() as m:
                r = m.materializar_sintetico(solicitud(limites=LimitesMaterializacion(128, 4)), bloques)
                self.assertIn("bloque_sintetico_no_admitido", codigos(r))

    def test_contenido_grande_por_bloques_acotados(self):
        bloque, cantidad = b"X" * 65536, 33
        esperado = hashlib.sha256()
        for _ in range(cantidad):
            esperado.update(bloque)
        s = solicitud(tamano_esperado=len(bloque) * cantidad, sha256_esperado=esperado.hexdigest(),
            limites=LimitesMaterializacion(3 * 1048576, 65536))
        with entorno_materializacion() as m:
            r = m.materializar_sintetico(s, (bloque for _ in range(cantidad)))
            self.assertEqual(r.estado_tecnico, S.CONCLUIDA)
            self.assertEqual(r.verificacion.sha256_fisico, esperado.hexdigest())

    def test_contenido_identico_no_fusiona_proyectos_ni_archivos(self):
        inv = inventario()
        with entorno_materializacion() as m:
            a = publicar(m, solicitud(0, ORIGINAL, inv=inv), ORIGINAL)
            b = publicar(m, solicitud(1, ORIGINAL, inv=inv), ORIGINAL)
            self.assertEqual(a.sha256_recibido, b.sha256_recibido)
            self.assertNotEqual(a.referencia.nombre, b.referencia.nombre)
            self.assertNotEqual(a.referencia.project_id, b.referencia.project_id)
            self.assertEqual(len(tuple(m.raiz.glob("a-*.bin"))), 2)

    def test_identidad_contenido_ya_publicada_no_se_redefine(self):
        inv = inventario()
        derivado = replace(inv.artefactos[3], contenido_id="contenido-preparado")
        inv = replace(inv, artefactos=(*inv.artefactos[:3], derivado))
        with entorno_materializacion() as m:
            a = publicar(m, solicitud(inv=inv))
            b = publicar(m, solicitud(3, DERIVADO, inv=inv), DERIVADO)
            self.assertEqual(a.estado_tecnico, S.CONCLUIDA)
            self.assertIn("contenido_contradice_publicacion_anterior", codigos(b))
            self.assertIsNone(b.referencia)

    def test_limpieza_no_elimina_archivos_ajenos(self):
        with entorno_materializacion() as m:
            ajeno = m.raiz / "archivo-ajeno-de-fixture"
            ajeno.write_bytes(b"ajeno")
            try:
                with self.assertRaises(ErrorArchivoExperimental):
                    m._archivos.limpiar()
                self.assertEqual(ajeno.read_bytes(), b"ajeno")
            finally:
                ajeno.unlink()  # Creado explícitamente por este test, no por RC5.

    def test_escritor_existente_impide_publicacion(self):
        with entorno_materializacion() as m:
            lock = m.raiz / "escritor.lock"
            lock.write_bytes(b"fixture-interrumpida")
            try:
                r = publicar(m)
                self.assertIn("destino_ocupado", codigos(r))
                self.assertEqual(lock.read_bytes(), b"fixture-interrumpida")
            finally:
                lock.unlink()

    def test_raiz_incompatible_no_se_relocaliza(self):
        with entorno_materializacion() as m:
            r = publicar(m)
            v = verificar_fisicamente(r.solicitud, replace(r.referencia, inodo_raiz=r.referencia.inodo_raiz + 1))
            self.assertIn("raiz_temporal_sustituida_o_incompatible", codigos(v))

    def test_cambio_durante_lectura_detectado(self):
        s = solicitud(datos=b"A" * 24, limites=LimitesMaterializacion(128, 8))
        with entorno_materializacion() as m:
            r = m.materializar_sintetico(s, (b"A" * 8,) * 3)
            ruta = m.raiz / r.referencia.nombre
            original = LectorControlado.read
            modificado = False
            def leer(lector, n):
                nonlocal modificado
                b = original(lector, n)
                if not modificado:
                    modificado = True
                    st = ruta.stat()
                    with ruta.open("r+b") as f:
                        f.seek(16)
                        f.write(b"B" * 8)
                    os.utime(ruta, ns=(st.st_atime_ns, st.st_mtime_ns + 10_000_000))
                return b
            with patch.object(LectorControlado, "read", new=leer):
                v = verificar_fisicamente(s, r.referencia)
            self.assertIn("archivo_cambio_durante_lectura", codigos(v))
            self.assertEqual(v.bytes_leidos, 24)
            self.assertFalse(v.lectura_completa)

    def test_cancelacion_de_verificacion_no_declara_corrupcion(self):
        with entorno_materializacion() as m:
            r = publicar(m)
            evento = Event()
            evento.set()
            v = verificar_fisicamente(r.solicitud, r.referencia, cancelacion=evento)
            self.assertEqual(v.integridad, I.PENDIENTE)
            self.assertIn("cancelacion_observada", codigos(v))

    def test_contratos_versionados_congelados_y_sin_permiso(self):
        s = solicitud()
        with self.assertRaises(ValueError):
            replace(s, version_contrato="99")
        for crear in (lambda: LimitesMaterializacion(True), lambda: LimitesMaterializacion(0),
                lambda: solicitud(tamano_esperado=2**30), lambda: solicitud(sha256_esperado="invalido")):
            with self.subTest(crear=crear), self.assertRaises(ValueError):
                crear()
        with entorno_materializacion() as m:
            r = publicar(m, s)
            self.assertEqual(r.version_contrato, VERSION_MATERIALIZACION)
            self.assertFalse(r.autoriza_operacion)
            with self.assertRaises(FrozenInstanceError):
                r.publicacion = P.VERIFICADA
            with self.assertRaises(TypeError):
                bool(r)
            with self.assertRaises(TypeError):
                bool(r.verificacion)
            self.assertFalse(r.verificacion.autoriza_operacion)

    def test_descriptor_no_es_prueba_fisica_ni_autenticidad(self):
        s = solicitud()
        with entorno_materializacion() as m:
            r = publicar(m, s)
            self.assertIs(r.solicitud.linaje, s.linaje)
            self.assertEqual(s.descriptor.disponibilidad.value, "desconocida")
            self.assertEqual(s.descriptor.integridad_aportada, I.PENDIENTE)
            self.assertFalse(s.linaje.comprobacion_fisica_realizada)
            self.assertEqual(r.verificacion.integridad, I.VERIFICADA)
            self.assertFalse(r.verificacion.autenticidad_acreditada)
            self.assertFalse(r.verificacion.custodia_independiente)
            self.assertTrue(all(x in r.restricciones for x in s.restricciones))

    def test_no_ejecuta_productor_http_raw_o_motor_qa(self):
        s = solicitud()
        with patch("spica.adquisicion.transportes.http.ClienteHTTP.get", side_effect=AssertionError("HTTP")), \
                patch("spica.adquisicion.almacenamiento.raw.AlmacenRAW.__init__", side_effect=AssertionError("RAW")), \
                patch("spica.calidad.EvaluadorNivel0.__init__", side_effect=AssertionError("QA")), entorno_materializacion() as m:
            self.assertEqual(publicar(m, s).estado_tecnico, S.CONCLUIDA)

    def test_verifica_desde_otro_proceso_sin_red_sqlite_o_escrituras(self):
        with entorno_materializacion() as m:
            r = publicar(m)
            p = referencia_para_proceso(r.referencia)
            proceso = subprocess.run([sys.executable, "-B", "-c", CODIGO_VERIFICADOR, json.dumps(p)], capture_output=True, text=True)
            self.assertEqual(proceso.returncode, 0, proceso.stderr)
            dato = json.loads(proceso.stdout)
            self.assertEqual(dato["sha256"], r.sha256_recibido)
            self.assertEqual(dato["bytes"], len(PREPARADO))
            self.assertEqual(dato["estado"], "comprobado_localmente")
            self.assertFalse(dato["custodia"])

    def test_referencia_historica_tras_cierre_no_recrea_raiz(self):
        with entorno_materializacion() as m:
            r = publicar(m)
            raiz = m.raiz
        v = verificar_fisicamente(r.solicitud, r.referencia)
        self.assertEqual(v.estado_local, EstadoLocal.AUSENTE)
        self.assertFalse(raiz.exists())

    def test_evidencia_aportada_no_se_sustituye_con_otro_hash_o_tamano(self):
        from spica.adquisicion.readquisicion.modelos import EvidenciaLocal
        from test_perfiles_informacion_rc2 import PROC, FECHA
        inv = inventario()
        a = inv.artefactos[0]
        ep = a.entrada_perfil
        e = replace(ep.entrada, sha256_declarado=None, size_bytes_declarado=None, asset_id="asset-ficticio",
            evidencia_local=EvidenciaLocal(EstadoLocal.INTEGRO, FECHA, PROC, hashlib.sha256(ORIGINAL).hexdigest(), len(ORIGINAL), "asset-ficticio"))
        a = replace(a, entrada_perfil=EntradaPerfil(e, ep.perfil))
        inv = InventarioArtefactos((a,))
        for kw in ({"tamano_esperado": len(ORIGINAL) + 1}, {"sha256_esperado": "0" * 64}):
            with self.subTest(kw=kw), self.assertRaises(ValueError):
                solicitud(0, ORIGINAL, inv=inv, **kw)

    def test_verificador_respeta_bloqueo_antes_de_abrir(self):
        with entorno_materializacion() as m:
            r = publicar(m)
            inv = r.solicitud.inventario
            a = replace(inv.artefactos[2], restricciones_adicionales=(RestriccionQA("no-leer", TR.BLOQUEO_USO_DEL_RESULTADO,
                (USO_VERIFICAR,), "fixture"),))
            inv = replace(inv, artefactos=(*inv.artefactos[:2], a, inv.artefactos[3]))
            s = solicitud(inv=inv)
            ref = replace(r.referencia, huella_vinculo=s.huella_vinculo)  # Referencia aportada, sin firma/autenticidad.
            with patch.object(ArchivosTEMP, "regular", side_effect=AssertionError("no debe leer")):
                v = verificar_fisicamente(s, ref)
            self.assertIn("restriccion_impide_verificacion", codigos(v))
            self.assertEqual(v.integridad, I.PENDIENTE)

    def test_error_lectura_no_inventa_integridad_fallida(self):
        with entorno_materializacion() as m:
            r = publicar(m)
            with patch.object(ArchivosTEMP, "leer", side_effect=PermissionError("secret=fixture")):
                v = verificar_fisicamente(r.solicitud, r.referencia)
            self.assertEqual(v.estado_local, EstadoLocal.NO_DISPONIBLE)
            self.assertEqual(v.integridad, I.PENDIENTE)
            self.assertNotIn("secret", str(v.diagnosticos))

    def test_cancelacion_durante_relectura_conserva_conteo_del_prefijo(self):
        evento = Event()
        s = solicitud(datos=b"A" * 24, limites=LimitesMaterializacion(128, 8))
        with entorno_materializacion() as m:
            r = m.materializar_sintetico(s, (b"A" * 8,) * 3)
            original = LectorControlado.read
            def leer(lector, n):
                b = original(lector, n)
                evento.set()
                return b
            with patch.object(LectorControlado, "read", new=leer):
                v = verificar_fisicamente(s, r.referencia, cancelacion=evento)
            self.assertEqual(v.bytes_leidos, 8)
            self.assertEqual(v.integridad, I.PENDIENTE)
            self.assertFalse(v.lectura_completa)
            self.assertIsNone(v.sha256_fisico)

    def test_escritor_cooperativo_impide_lectura_paralela(self):
        with entorno_materializacion() as m:
            a = publicar(m)
            observados = []
            def punto(nombre):
                if nombre == "temporal_creado":
                    observados.append(verificar_fisicamente(a.solicitud, a.referencia))
            with patch.object(m, "_punto", side_effect=punto):
                b = publicar(m, solicitud(3, DERIVADO), DERIVADO)
            self.assertEqual(b.estado_tecnico, S.CONCLUIDA)
            self.assertIn("escritor_o_interrupcion_pendiente", codigos(observados[0]))

    def test_temporal_corrupto_detectado_por_primera_relectura(self):
        with entorno_materializacion() as m:
            def punto(nombre):
                if nombre == "temporal_cerrado":
                    next(m.raiz.glob("t-*.tmp")).write_bytes(b"Z" * len(PREPARADO))
            with patch.object(m, "_punto", side_effect=punto):
                r = publicar(m)
            self.assertIn("temporal_fisico_no_coincidente", codigos(r))
            self.assertNotEqual(r.sha256_recibido, r.sha256_temporal)
            self.assertIsNone(r.referencia)

    def test_linaje_contradictorio_se_detiene_sin_efectos(self):
        inv = inventario()
        inv = replace(inv, artefactos=inv.artefactos + (inv.artefactos[0],))
        with self.assertRaises(ValueError):
            solicitud(inv=inv)

    def test_cancelacion_tras_publicar_conserva_archivo_sin_promocion(self):
        evento = Event()
        with entorno_materializacion() as m:
            def punto(nombre):
                if nombre == "antes_relectura_final":
                    evento.set()
            with patch.object(m, "_punto", side_effect=punto):
                r = m.materializar_sintetico(solicitud(), (PREPARADO,), cancelacion=evento)
            self.assertEqual(r.estado_tecnico, S.CANCELADA)
            self.assertEqual(r.publicacion, P.PUBLICADA)
            self.assertIsNotNone(r.referencia)
            self.assertEqual(r.verificacion.integridad, I.PENDIENTE)
            self.assertEqual((m.raiz / r.referencia.nombre).read_bytes(), PREPARADO)

    def test_error_de_creacion_de_raiz_no_expone_ruta(self):
        with patch.object(Path, "mkdir", side_effect=PermissionError("secret=ruta-ficticia")):
            with self.assertRaises(ErrorArchivoExperimental) as exc:
                with entorno_materializacion():
                    self.fail("no debe crear entorno")
        self.assertEqual(str(exc.exception), "entorno_temporal_no_creado")


def referencia_para_proceso(r):
    # IPC explícito de esta prueba; no API/codec de persistencia RC5.
    return dict(instancia_id=r.instancia_id, dispositivo_raiz=r.dispositivo_raiz, inodo_raiz=r.inodo_raiz,
        project_id=r.project_id, artefacto=dict(object_id=r.artefacto.object_id, revision=r.artefacto.revision),
        contenido_id=r.contenido_id, huella_vinculo=r.huella_vinculo, size_bytes=r.size_bytes, sha256_recibido=r.sha256_recibido)


CODIGO_VERIFICADOR = r'''
import sys, os, json
def barrera(evento, argumentos):
    if evento.startswith("socket.") or evento == "sqlite3.connect":
        raise AssertionError("red_o_sqlite_prohibido")
    if evento == "open":
        p, modo, flags = argumentos
        if isinstance(modo, str) and any(c in modo for c in "wax+") or flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
            raise AssertionError("escritura_prohibida")
        if not isinstance(p, int) and "spica_datos" in os.fsdecode(p).lower():
            raise AssertionError("lectura_operativa_prohibida")
sys.addaudithook(barrera)
from spica.artefactos.materializacion import ReferenciaFisica, verificar_fisicamente
from spica.artefactos import ReferenciaArtefacto
from test_materializacion_rc5 import solicitud
d = json.loads(sys.argv[1])
d["artefacto"] = ReferenciaArtefacto(**d["artefacto"])
r = ReferenciaFisica(**d)
v = verificar_fisicamente(solicitud(), r)
print(json.dumps(dict(sha256=v.sha256_fisico, bytes=v.bytes_leidos, estado=v.estado_local.value, custodia=v.custodia_independiente)))
'''


if __name__ == "__main__":
    unittest.main()
