"""Fixtures sintéticas, persistencia temporal y reapertura en procesos independientes."""

from contextlib import closing, contextmanager
from dataclasses import replace
import errno
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
from threading import Event
import unittest
from unittest.mock import patch

from herramientas import conservacion_linaje_85j as p
from herramientas import piloto_integracion_85g as h
from herramientas import traza_cierre_85h as t
from spica.adquisicion.catalogo import CatalogoCientifico, ErrorCatalogo


def muestra(**cambios):
    b = h.fixture_csv_85g()
    c = h.ContratoEjecucion85G('ejecucion-85j', 'proyecto-ficticio-85g', 'entrada-85j',
        'evaluacion-85j', 'tarea-85j', len(b), hashlib.sha256(b).hexdigest())
    return h.ejecutar_piloto_85g(replace(c, **cambios), b)


class InterrupcionSimulada(BaseException):
    pass


class Conservacion85JTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = muestra()
        cls.tr = t.construir_traza_85h(cls.r)
        cls.ref = cls.tr.sha256
        cls.parcial = muestra(presupuesto=h.Presupuesto85G(max_resultados=10))
        evento = Event()
        evento.set()
        cls.cancelada = h.ejecutar_piloto_85g(cls.r.contrato, h.fixture_csv_85g(), cancelacion=evento)

    @contextmanager
    def almacen(self, persistir=False, **limites):
        with p.entorno_piloto_85j() as raiz:
            with p.ConservadorLinaje85J.crear(raiz, limites=p.LimitesConservacion85J(**limites)) as a:
                if persistir:
                    self.conservar(a)
                yield a

    def conservar(self, a, r=None):
        r = self.r if r is None else r
        tr = t.construir_traza_85h(r)
        return a.conservar(r, tr, referencia_sha256=tr.sha256)

    def filas(self, a, sql='SELECT * FROM linaje_ejecuciones'):
        with closing(sqlite3.connect(a.raiz / 'catalogo.sqlite3')) as c, c:
            return c.execute(sql).fetchall()

    def archivo(self, a, rol):
        with closing(sqlite3.connect(a.raiz / 'catalogo.sqlite3')) as c, c:
            sha = c.execute('SELECT sha256 FROM linaje_artefactos WHERE rol=?', (rol,)).fetchone()[0]
        return a._ruta_artefacto(sha)

    def test_concluida_recupera_informe_y_traza_exactos(self):
        with self.almacen() as a:
            v = self.conservar(a)
            self.assertIs(v.estado, p.EstadoRecuperacion85J.VERIFICADA)
            self.assertIs(v.estado_conservacion, p.EstadoConservacion85J.CONSERVADA)
            self.assertEqual(v.informe, self.r)
            self.assertEqual(v.traza, self.tr)
            self.assertEqual(v.referencia_sha256, self.ref)
            self.assertTrue(v.cotejo.coherente_en_alcance)
            self.assertFalse(v.huerfanos or v.temporales)

    def test_incompleta_preserva_nativos_sin_exportacion_inventada(self):
        with self.almacen() as a:
            v = self.conservar(a, self.parcial)
            self.assertIs(v.estado_historico, h.EstadoEjecucion85G.INCOMPLETA)
            self.assertEqual(v.informe, self.parcial)
            self.assertEqual(len(v.informe.resultados[0]), 10)
            self.assertEqual(v.informe.exportaciones, ())
            self.assertFalse(v.cotejo.cadena_completa)

    def test_cancelada_sin_activo_es_conservacion_completa(self):
        with self.almacen() as a:
            v = self.conservar(a, self.cancelada)
            self.assertIs(v.estado_historico, h.EstadoEjecucion85G.CANCELADA)
            self.assertIs(v.estado_conservacion, p.EstadoConservacion85J.CONSERVADA)
            self.assertIsNone(v.informe.activo_id)
            self.assertEqual(v.informe.resultados, ())

    def test_fallida_conserva_evidencia_real_sin_promocion(self):
        with patch.object(h.CatalogoCientifico, 'consultar_recurso', side_effect=sqlite3.OperationalError('secreto')):
            r = muestra()
        with self.almacen() as a:
            v = self.conservar(a, r)
            self.assertIs(v.estado_historico, h.EstadoEjecucion85G.FALLIDA)
            self.assertIs(v.estado, p.EstadoRecuperacion85J.VERIFICADA)
            self.assertEqual(v.informe, r)
            self.assertNotIn('secreto', json.dumps(v.resumen()))

    def test_integridad_fisica_de_los_cuatro_artefactos(self):
        with self.almacen(True) as a:
            for ar in a.recuperar(self.r.contrato.ejecucion_id).artefactos:
                with self.subTest(rol=ar.rol), a._ruta_artefacto(ar.sha256).open('rb') as f:
                    self.assertEqual(hashlib.file_digest(f, 'sha256').hexdigest(), ar.sha256)
                    self.assertEqual(os.fstat(f.fileno()).st_size, ar.tamano)

    def test_control_incorrecto_no_prepara(self):
        with self.almacen() as a:
            with self.assertRaises(p.ErrorConservacion85J):
                a.conservar(self.r, self.tr, referencia_sha256='0' * 64)
            self.assertEqual(self.filas(a), [])

    def test_control_previo_obligatorio(self):
        with self.almacen() as a:
            with self.assertRaises(TypeError):
                a.conservar(self.r, self.tr)
            with self.assertRaises(p.ErrorConservacion85J):
                a.conservar(self.r, self.tr, referencia_sha256=None)
            self.assertEqual(self.filas(a), [])

    def test_informe_tipado_obligatorio(self):
        with self.almacen() as a:
            with self.assertRaises(p.ErrorConservacion85J):
                a.conservar({}, self.tr, referencia_sha256=self.ref)

    def test_ausencia_de_informe_no_elimina_referencia_sqlite(self):
        with self.almacen(True) as a:
            self.archivo(a, 'informe').unlink()
            self.assertIs(a.recuperar(self.r.contrato.ejecucion_id).estado, p.EstadoRecuperacion85J.AUSENTE)
            self.assertEqual(len(self.filas(a, 'SELECT * FROM linaje_artefactos')), 4)

    def test_control_sha_ausente_impide_recuperar_cotejo(self):
        with self.almacen(True) as a:
            self.archivo(a, 'referencia').unlink()
            self.assertIs(a.recuperar(self.r.contrato.ejecucion_id).estado, p.EstadoRecuperacion85J.AUSENTE)

    def test_huerfano_no_se_adopta_ni_elimina(self):
        with self.almacen(True) as a:
            datos = b'huerfano sintetico'
            ruta = a._ruta_artefacto(hashlib.sha256(datos).hexdigest())
            ruta.parent.mkdir(exist_ok=True)
            ruta.write_bytes(datos)
            v = a.recuperar(self.r.contrato.ejecucion_id)
            self.assertIs(v.estado, p.EstadoRecuperacion85J.REVISION_NECESARIA)
            self.assertTrue(v.huerfanos)
            self.assertEqual(ruta.read_bytes(), datos)

    def test_archivo_alterado_detectado_y_preservado(self):
        with self.almacen(True) as a:
            ruta = self.archivo(a, 'traza')
            datos = ruta.read_bytes()
            ruta.write_bytes(b'!' + datos[1:])
            self.assertIs(a.recuperar(self.r.contrato.ejecucion_id).estado, p.EstadoRecuperacion85J.CORRUPTA)
            self.assertEqual(ruta.read_bytes(), b'!' + datos[1:])

    def test_tamano_truncado_o_ampliado_detectado(self):
        for ampliar in (False, True):
            with self.subTest(ampliar=ampliar), self.almacen(True) as a:
                ruta = self.archivo(a, 'referencia')
                datos = ruta.read_bytes()
                ruta.write_bytes(datos + b'!' if ampliar else datos[:-1])
                self.assertIs(a.recuperar(self.r.contrato.ejecucion_id).estado, p.EstadoRecuperacion85J.CORRUPTA)

    def test_version_sqlite_incompatible_no_se_migra(self):
        with self.almacen(True) as a:
            with closing(sqlite3.connect(a.raiz / 'catalogo.sqlite3')) as c, c:
                c.execute('PRAGMA user_version=99999')
            antes = (a.raiz / 'catalogo.sqlite3').read_bytes()
            self.assertIs(a.recuperar(self.r.contrato.ejecucion_id).estado, p.EstadoRecuperacion85J.VERSION_INCOMPATIBLE)
            self.assertEqual((a.raiz / 'catalogo.sqlite3').read_bytes(), antes)

    def test_estructura_sqlite_ajena_rechazada(self):
        with self.almacen(True) as a:
            with closing(sqlite3.connect(a.raiz / 'catalogo.sqlite3')) as c, c:
                c.execute('CREATE TABLE ajena (x TEXT)')
            self.assertIs(a.recuperar(self.r.contrato.ejecucion_id).estado, p.EstadoRecuperacion85J.REVISION_NECESARIA)

    def test_lector_estable_rechaza_extension_y_v1_sigue_intacto(self):
        with self.almacen() as a:
            with self.assertRaises(ErrorCatalogo):
                CatalogoCientifico(a.raiz / 'catalogo.sqlite3')
            otra = a.raiz.parent / 'catalogo-v1.sqlite3'
            with CatalogoCientifico(otra):
                pass
            with CatalogoCientifico(otra):
                pass
            with closing(sqlite3.connect(otra)) as c, c:
                self.assertEqual(c.execute('PRAGMA user_version').fetchone()[0], 1)
                self.assertEqual(c.execute("SELECT count(*) FROM sqlite_master WHERE name LIKE 'linaje_%'").fetchone()[0], 0)

    def test_no_reinicializa_raiz_existente(self):
        with self.almacen(True) as a:
            antes = (a.raiz / 'catalogo.sqlite3').read_bytes()
            with self.assertRaises(p.ErrorConservacion85J):
                p.ConservadorLinaje85J.crear(a.raiz)
            self.assertEqual((a.raiz / 'catalogo.sqlite3').read_bytes(), antes)

    def test_repeticion_idempotente_sin_duplicar_eventos(self):
        with self.almacen() as a:
            uno = self.conservar(a)
            antes = self.filas(a, 'SELECT * FROM linaje_eventos')
            dos = self.conservar(a)
            self.assertEqual(uno.conservacion_id, dos.conservacion_id)
            self.assertEqual(self.filas(a, 'SELECT * FROM linaje_eventos'), antes)
            self.assertEqual(len(self.filas(a)), 1)

    def test_identidad_contradictoria_preserva_anterior(self):
        with self.almacen(True) as a:
            r = replace(self.r, contrato=replace(self.r.contrato, tarea_ref='otra-tarea'))
            r = replace(r, captura_antes_cierre=t.capturar_evidencia_85h(r))
            antes = (a.raiz / 'catalogo.sqlite3').read_bytes()
            with self.assertRaises(p.ErrorConservacion85J) as cm:
                self.conservar(a, r)
            self.assertEqual(cm.exception.codigo, 'conflicto_de_identidad')
            self.assertEqual((a.raiz / 'catalogo.sqlite3').read_bytes(), antes)

    def test_ejecuciones_distintas_no_se_fusionan_por_sha(self):
        with self.almacen(True) as a:
            r = replace(self.r, contrato=replace(self.r.contrato, ejecucion_id='otra-ejecucion'))
            r = replace(r, captura_antes_cierre=t.capturar_evidencia_85h(r))
            v = self.conservar(a, r)  # Variante contractual, no nueva evaluación demostrada.
            self.assertEqual(len(self.filas(a)), 2)
            self.assertEqual(v.informe.adquisicion.activo.sha256, self.r.adquisicion.activo.sha256)

    def test_restricciones_omitidas_rechazadas(self):
        with self.almacen() as a:
            r = replace(self.r, restricciones=self.r.restricciones[:-1])
            with self.assertRaises(p.ErrorConservacion85J):
                a.conservar(r, self.tr, referencia_sha256=self.ref)
            self.assertFalse(self.filas(a))

    def test_restricciones_individuales_y_globales_preservadas(self):
        with self.almacen(True) as a:
            v = a.recuperar(self.r.contrato.ejecucion_id)
            self.assertEqual(v.informe.restricciones, self.r.restricciones)
            for antes, despues in zip(self.r.resultados, v.informe.resultados, strict=True):
                self.assertEqual([h.restricciones_resultado(x) for x in antes],
                                 [h.restricciones_resultado(x) for x in despues])

    def test_nueve_fronteras_de_interrupcion(self):
        fases = ('intencion', 'parcial', 'temporal', 'verificado', 'artefacto',
                 'manifiesto', 'referencias', 'confirmacion', 'cierre')
        for fase in fases:
            with self.subTest(fase=fase), self.almacen() as a:
                def cortar(nombre):
                    if nombre == fase:
                        raise InterrupcionSimulada()
                with patch.object(a, '_punto', side_effect=cortar), self.assertRaises(InterrupcionSimulada):
                    self.conservar(a, self.cancelada)
                v = a.recuperar(self.r.contrato.ejecucion_id)
                if fase in ('confirmacion', 'cierre'):
                    self.assertIs(v.estado, p.EstadoRecuperacion85J.VERIFICADA)
                    self.assertEqual(v.informe, self.cancelada)
                else:
                    self.assertIs(v.estado, p.EstadoRecuperacion85J.INCOMPLETA)
                    self.assertIsNone(v.informe)
                self.assertEqual(len(self.filas(a)), 1)

    def test_error_sqlite_entre_publicacion_y_commit(self):
        with self.almacen() as a:
            def fallar(fase):
                if fase == 'referencias':
                    raise sqlite3.OperationalError('token=no-exponer')
            with patch.object(a, '_punto', side_effect=fallar), self.assertRaises(p.ErrorConservacion85J) as cm:
                self.conservar(a)
            self.assertEqual(str(cm.exception), 'error_sqlite')
            v = a.recuperar(self.r.contrato.ejecucion_id)
            self.assertIs(v.estado, p.EstadoRecuperacion85J.INCOMPLETA)
            self.assertEqual(len(v.huerfanos), 4)
            self.assertEqual(self.filas(a, 'SELECT * FROM linaje_artefactos'), [])

    def test_disco_lleno_y_permiso_denegado(self):
        for error in (OSError(errno.ENOSPC, 'token=privado'), PermissionError('ruta=privada')):
            with self.subTest(error=type(error).__name__), self.almacen() as a:
                with patch.object(p.os, 'link', side_effect=error), self.assertRaises(p.ErrorConservacion85J) as cm:
                    self.conservar(a)
                self.assertEqual(str(cm.exception), 'error_archivo')
                v = a.recuperar(self.r.contrato.ejecucion_id)
                self.assertIs(v.estado, p.EstadoRecuperacion85J.INCOMPLETA)
                self.assertTrue(v.temporales)

    def test_escritura_corta_rechazada(self):
        with self.almacen() as a:
            real = Path.open
            class Corto:
                def __init__(self, f): self.f = f
                def __enter__(self): return self
                def __exit__(self, *args): return self.f.__exit__(*args)
                def write(self, datos): return 0
                def __getattr__(self, nombre): return getattr(self.f, nombre)
            def abrir(ruta, *args, **kwargs):
                f = real(ruta, *args, **kwargs)
                return Corto(f) if ruta.suffix == '.tmp' and args == ('xb',) else f
            with patch.object(Path, 'open', abrir), self.assertRaises(p.ErrorConservacion85J) as cm:
                self.conservar(a)
            self.assertEqual(cm.exception.codigo, 'escritura_incompleta')

    def test_conflicto_publicacion_preserva_destino(self):
        with self.almacen() as a:
            datos = p.codec.codificar(self.r)
            ruta = a._ruta_artefacto(hashlib.sha256(datos).hexdigest())
            ruta.parent.mkdir()
            ruta.write_bytes(b'original ajeno')
            with self.assertRaises(p.ErrorConservacion85J) as cm:
                self.conservar(a)
            self.assertEqual(cm.exception.codigo, 'conflicto_de_publicacion')
            self.assertEqual(ruta.read_bytes(), b'original ajeno')

    def test_cancelacion_antes_de_conservar(self):
        with self.almacen() as a:
            e = Event()
            e.set()
            with self.assertRaises(p.ErrorConservacion85J) as cm:
                a.conservar(self.r, self.tr, referencia_sha256=self.ref, cancelacion=e)
            self.assertEqual(cm.exception.codigo, 'conservacion_cancelada')
            self.assertFalse(self.filas(a))

    def test_cancelacion_durante_escritura_conserva_parcial(self):
        with self.almacen() as a:
            e = Event()
            with patch.object(a, '_punto', side_effect=lambda n: e.set() if n == 'parcial' else None), self.assertRaises(p.ErrorConservacion85J):
                a.conservar(self.r, self.tr, referencia_sha256=self.ref, cancelacion=e)
            v = a.recuperar(self.r.contrato.ejecucion_id)
            self.assertIs(v.estado_conservacion, p.EstadoConservacion85J.INCOMPLETA)
            self.assertTrue(v.temporales)

    def test_plazo_cooperativo_excedido(self):
        with self.almacen() as a:
            with patch.object(p.time, 'monotonic', side_effect=(0.0, 200.0)), self.assertRaises(p.ErrorConservacion85J) as cm:
                self.conservar(a)
            self.assertEqual(cm.exception.codigo, 'plazo_excedido')

    def test_presupuestos_rechazan_antes_de_publicar(self):
        for cambio in ({'max_artefactos': 3}, {'max_bytes_artefacto': 128},
                       {'max_bytes_total': 128}, {'max_profundidad': 2}, {'max_nodos': 8}):
            with self.subTest(cambio=cambio), self.almacen(**cambio) as a:
                with self.assertRaises(p.ErrorConservacion85J):
                    self.conservar(a)
                self.assertFalse(self.filas(a))

    def test_limites_rechazan_booleanos(self):
        for nombre in ('max_artefactos', 'max_bytes_artefacto', 'max_bytes_total', 'max_profundidad',
                       'max_nodos', 'max_referencias', 'tamano_bloque', 'max_segundos'):
            with self.subTest(nombre=nombre), self.assertRaises(ValueError):
                p.LimitesConservacion85J(**{nombre: True})

    def test_segundo_escritor_rechazado(self):
        with self.almacen() as a:
            with a._escritor(), self.assertRaises(p.ErrorConservacion85J) as cm:
                self.conservar(a)
            self.assertEqual(cm.exception.codigo, 'escritor_o_marcador_pendiente')
            self.assertFalse(self.filas(a))

    def test_raices_traversal_y_nombres_reservados(self):
        for ruta in (Path.cwd() / 'conservacion', Path.home() / 'SPICA_DATOS' / 'conservacion',
                     Path('..') / 'conservacion', Path('CON')):
            with self.subTest(ruta=ruta), self.assertRaises(p.ErrorConservacion85J):
                p.ConservadorLinaje85J(ruta)

    def test_ids_no_forman_nombres_fisicos(self):
        with self.almacen() as a:
            for identidad in ('../archivo', 'CON/archivo', '', 'x' * 65):
                with self.subTest(identidad=identidad), self.assertRaises(p.ErrorConservacion85J):
                    a.recuperar(identidad)
            self.conservar(a)
            self.assertTrue(all(p._HASH.fullmatch(x.name) for d in (a.raiz / 'contenido').iterdir() for x in d.iterdir()))

    def test_enlace_rechazado_sin_seguirlo(self):
        with self.almacen(True) as a:
            ruta = self.archivo(a, 'referencia')
            real = Path.is_symlink
            with patch.object(Path, 'is_symlink', lambda x: True if x == ruta else real(x)):
                self.assertIs(a.recuperar(self.r.contrato.ejecucion_id).estado, p.EstadoRecuperacion85J.REVISION_NECESARIA)
            self.assertTrue(ruta.exists())

    def test_codec_estricto_sin_imports_arbitrarios(self):
        d = json.loads(p.codec.codificar(self.cancelada))
        d['informe']['c'] = 'os:system'
        with self.assertRaises(ValueError):
            p.codec.decodificar(p.codec.canonico(d))
        for texto in (b'{"x":1,"x":2}', b'{"x":NaN}', b'[' * 50 + b']' * 50):
            with self.subTest(texto=texto[:20]), self.assertRaises(ValueError):
                p.codec.leer_json(texto)

    def test_version_codec_y_campos_fijos_rechazados(self):
        d = json.loads(p.codec.codificar(self.cancelada))
        d['version'] = '99.0.0'
        with self.assertRaises(ValueError):
            p.codec.decodificar(p.codec.canonico(d))
        d['version'] = p.codec.VERSION_CODEC
        d['informe']['v']['autorizacion_operativa'] = True
        with self.assertRaises(ValueError):
            p.codec.decodificar(p.codec.canonico(d))

    def test_recuperacion_no_ejecuta_tarea_qa_http_ni_abre_historico(self):
        with self.almacen(True) as a:
            real = Path.open
            def abrir(ruta, *args, **kwargs):
                if ruta.is_relative_to(self.r.temporal):
                    raise AssertionError('lectura_historica')
                return real(ruta, *args, **kwargs)
            with patch.object(h, 'ejecutar_piloto_85g', side_effect=AssertionError('tarea')), \
                 patch.object(h, 'EvaluadorNivel0', side_effect=AssertionError('qa')), \
                 patch('socket.getaddrinfo', side_effect=AssertionError('dns')), \
                 patch('socket.socket.connect', side_effect=AssertionError('red')), \
                 patch('httpx.HTTPTransport.handle_request', side_effect=AssertionError('http')), \
                 patch.object(Path, 'open', abrir):
                self.assertIs(a.recuperar(self.r.contrato.ejecucion_id).estado, p.EstadoRecuperacion85J.VERIFICADA)

    def test_lector_no_modifica_archivos_o_sqlite(self):
        with self.almacen(True) as a:
            def huellas():
                return {x.relative_to(a.raiz).as_posix(): hashlib.sha256(x.read_bytes()).hexdigest()
                        for x in a.raiz.rglob('*') if x.is_file()}
            antes = huellas()
            a.recuperar(self.r.contrato.ejecucion_id)
            self.assertEqual(huellas(), antes)

    def test_cierre_y_limpieza_del_temporal_propietario(self):
        with p.entorno_piloto_85j() as raiz:
            a = p.ConservadorLinaje85J.crear(raiz)
            self.conservar(a)
            a.close()
            with self.assertRaises(p.ErrorConservacion85J):
                self.conservar(a)
        self.assertFalse(raiz.exists())

    def test_resumen_no_expone_rutas_ni_autoriza(self):
        with self.almacen(True) as a:
            v = a.recuperar(self.r.contrato.ejecucion_id)
            d = v.resumen()
            self.assertFalse(d['autorizacion_operativa'] or d['ejecucion_cientifica'] or d['autenticidad_independiente'])
            self.assertNotIn(str(self.r.temporal), json.dumps(d))
            with self.assertRaises(TypeError):
                bool(v)

    def test_escritor_finaliza_y_otro_proceso_recupera(self):
        escritor = '''import sys,json
from test_conservacion_linaje_85j import muestra
from herramientas import conservacion_linaje_85j as p, traza_cierre_85h as t
r=muestra(); tr=t.construir_traza_85h(r)
with p.ConservadorLinaje85J.crear(sys.argv[1]) as a:
    v=a.conservar(r,tr,referencia_sha256=tr.sha256)
print(json.dumps(v.resumen()))
'''
        lector = '''import sys,json
from herramientas import conservacion_linaje_85j as p
with p.ConservadorLinaje85J(sys.argv[1]) as a:
    v=a.recuperar('ejecucion-85j')
print(json.dumps(v.resumen()))
'''
        def ejecutar(codigo, raiz):
            hijo = subprocess.run([sys.executable, '-B', '-c', codigo, str(raiz)],
                capture_output=True, text=True, encoding='utf-8', timeout=120, env=os.environ.copy())
            self.assertEqual(hijo.returncode, 0, hijo.stderr)
            return json.loads(hijo.stdout)
        with p.entorno_piloto_85j() as raiz:
            escrito = ejecutar(escritor, raiz)  # El proceso termina antes de arrancar lector.
            leido = ejecutar(lector, raiz)
            self.assertEqual(escrito, leido)
            self.assertEqual(leido['resultados'], [60, 60])
            self.assertEqual(leido['restricciones'], [[60, 206], [60, 206]])
            self.assertTrue(leido['cotejo_85h'])

    def test_terminacion_forzada_deja_intencion_y_marcador(self):
        codigo = '''import os,sys
from test_conservacion_linaje_85j import muestra
from herramientas import conservacion_linaje_85j as p, traza_cierre_85h as t
r=muestra(); tr=t.construir_traza_85h(r)
a=p.ConservadorLinaje85J.crear(sys.argv[1])
def cortar(fase):
    if fase=='artefacto': os._exit(37)
a._punto=cortar
a.conservar(r,tr,referencia_sha256=tr.sha256)
'''
        with p.entorno_piloto_85j() as raiz:
            hijo = subprocess.run([sys.executable, '-B', '-c', codigo, str(raiz)],
                capture_output=True, timeout=120, env=os.environ.copy())
            self.assertEqual(hijo.returncode, 37, hijo.stderr)
            with p.ConservadorLinaje85J(raiz) as a:
                v = a.recuperar(self.r.contrato.ejecucion_id)
                self.assertIs(v.estado, p.EstadoRecuperacion85J.INCOMPLETA)
                self.assertTrue(v.huerfanos)
                self.assertTrue((raiz / 'escritor.lock').exists())
                with self.assertRaises(p.ErrorConservacion85J) as cm:
                    self.conservar(a)
                self.assertEqual(cm.exception.codigo, 'escritor_o_marcador_pendiente')

    def test_inventario_incompleto_en_sqlite_no_es_conservacion_valida(self):
        with self.almacen(True) as a:
            with closing(sqlite3.connect(a.raiz / 'catalogo.sqlite3')) as c, c:
                c.execute("DELETE FROM linaje_artefactos WHERE rol='informe'")
            self.assertIs(a.recuperar(self.r.contrato.ejecucion_id).estado, p.EstadoRecuperacion85J.REVISION_NECESARIA)

    def test_no_adopta_wal_o_diario_ajeno(self):
        with self.almacen(True) as a:
            (a.raiz / 'catalogo.sqlite3-wal').write_bytes(b'no es un WAL valido')
            self.assertIs(a.recuperar(self.r.contrato.ejecucion_id).estado, p.EstadoRecuperacion85J.REVISION_NECESARIA)

    def test_prefijo_json_real_sobrevive_fallo_de_exportacion(self):
        real = h.exportar_resultado_json
        llamadas = 0
        def exportar(*args, **kwargs):
            nonlocal llamadas
            llamadas += 1
            if llamadas == 3:
                raise OSError('no-exponer')
            return real(*args, **kwargs)
        with patch.object(h, 'exportar_resultado_json', side_effect=exportar):
            r = muestra()
        self.assertIs(r.estado, h.EstadoEjecucion85G.FALLIDA)
        self.assertEqual(len(r.exportaciones[0]), 2)
        with self.almacen() as a:
            v = self.conservar(a, r)
            self.assertEqual(v.informe.resultados, r.resultados)
            self.assertEqual(v.informe.exportaciones, r.exportaciones)
            self.assertEqual(v.informe.consumos, ())

    def test_junction_simulada_no_se_sigue(self):
        with self.almacen(True) as a:
            ruta = a.raiz / 'contenido'
            real = Path.is_junction
            with patch.object(Path, 'is_junction', lambda x: True if x == ruta else real(x)):
                self.assertIs(a.recuperar(self.r.contrato.ejecucion_id).estado, p.EstadoRecuperacion85J.REVISION_NECESARIA)

    def test_con_y_mayusculas_en_ids_logicos_no_colisionan_en_disco(self):
        with self.almacen() as a:
            for identidad in ('CON', 'con'):
                r = replace(self.cancelada, contrato=replace(self.cancelada.contrato, ejecucion_id=identidad))
                self.assertIs(self.conservar(a, r).estado, p.EstadoRecuperacion85J.VERIFICADA)
            self.assertEqual(len(self.filas(a)), 2)
            self.assertFalse(any(x.name.casefold() == 'con' for x in a.raiz.rglob('*')))

    def test_descriptores_y_ruta_con_firma_distinta_se_rechazan(self):
        with self.almacen(True) as a:
            real = p.os.fstat
            def distinto(fd):
                valores = list(real(fd))
                valores[6] += 1
                return os.stat_result(valores)
            with patch.object(p.os, 'fstat', side_effect=distinto):
                self.assertIsNot(a.recuperar(self.r.contrato.ejecucion_id).estado, p.EstadoRecuperacion85J.VERIFICADA)


if __name__ == '__main__':
    unittest.main()
