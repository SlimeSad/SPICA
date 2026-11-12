"""Respaldo/restauración TEMP del perfil 85-J; no es un servicio operativo.

Un escritor cooperativo, una ejecución conservada y SQLite DELETE sin auxiliares.
El control se entrega al llamador: no se obtiene del propio respaldo al restaurar.
"""

from contextlib import closing, contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import io
import os
from pathlib import Path
import re
import shutil
import sqlite3
import stat
from tempfile import TemporaryDirectory
from threading import Event
import time
from uuid import uuid4

from herramientas import conservacion_linaje_85j as p
from herramientas import _catalogo_linaje_85j as indice
from herramientas import _codec_linaje_85j as codec

VERSION_RESPALDO = "0.1.0"
_HASH = re.compile(r"[0-9a-f]{64}\Z")
_UUID = re.compile(r"[0-9a-f]{32}\Z")
_BASE = ("fuentes", "productos", "estaciones", "variables", "disponibilidades", "capacidades", "revisiones")
_TABLAS = ("linaje_instancia", "linaje_ejecuciones", "linaje_artefactos", "linaje_eventos")
_ROLES = ("intencion", "catalogo", "piloto", "informe", "traza", "referencia", "manifiesto")
_CONDICIONES = ("una_ejecucion_conservada", "sqlite_delete_sin_auxiliares", "raiz_temporal_nueva",
                "un_escritor_cooperativo", "control_explicito")
_LIMITACIONES = ("sin_atomicidad_global", "sin_garantia_ante_apagado", "sin_autenticidad_independiente",
                 "sin_validacion_cientifica", "sin_autorizacion_operativa", "sin_respaldo_raw",
                 "sin_proteccion_ante_escritor_hostil", "sin_respaldo_general")


class ErrorRespaldo85K(ValueError):
    def __init__(self, codigo):
        self.codigo = codigo
        super().__init__(codigo)


def _exigir(condicion, codigo):
    if not condicion:
        raise ErrorRespaldo85K(codigo)


def _sha(b):
    return hashlib.sha256(b).hexdigest()


@dataclass(frozen=True)
class LimitesRespaldo85K:
    max_bytes_archivo: int = 8 * 1024**2
    max_bytes_sqlite: int = 16 * 1024**2
    max_bytes_total: int = 48 * 1024**2
    max_bytes_manifiesto: int = 65536
    max_eventos: int = 128
    bloque: int = 65536
    margen_libre: int = 1024**2
    segundos: int = 180

    def __post_init__(self):
        for nombre, tope in (("max_bytes_archivo", 8 * 1024**2), ("max_bytes_sqlite", 16 * 1024**2),
                ("max_bytes_total", 64 * 1024**2), ("max_bytes_manifiesto", 65536),
                ("max_eventos", 1024), ("bloque", 1024**2), ("margen_libre", 64 * 1024**2), ("segundos", 300)):
            v = getattr(self, nombre)
            _exigir(type(v) is int and 0 < v <= tope, "limite_invalido")


@dataclass(frozen=True)
class ControlRespaldo85K:
    respaldo_id: str
    generacion_sha256: str
    manifiesto_sha256: str

    def __post_init__(self):
        _exigir(type(self.respaldo_id) is str and bool(_UUID.fullmatch(self.respaldo_id)), "control_invalido")
        for valor in (self.generacion_sha256, self.manifiesto_sha256):
            _exigir(type(valor) is str and bool(_HASH.fullmatch(valor)), "control_invalido")

    def __bool__(self):
        raise TypeError("control_no_es_autorizacion")


@dataclass(frozen=True)
class Restauracion85K:
    restauracion_id: str
    control: ControlRespaldo85K
    recuperacion: p.Recuperacion85J

    def resumen(self):
        return dict(restauracion_id=self.restauracion_id, respaldo_id=self.control.respaldo_id,
                    recuperacion=self.recuperacion.resumen(), ejecucion_cientifica=False,
                    autorizacion_operativa=False, autenticidad_independiente=False)

    def __bool__(self):
        raise TypeError("restauracion_no_es_autorizacion")


@contextmanager
def entorno_respaldo_85k():
    with TemporaryDirectory(prefix="spica-85k-", dir=p.h._base_temporal()) as padre:
        yield Path(padre) / "respaldo"


def _raiz_respaldo(ruta):
    r = Path(ruta).absolute()
    _exigir(".." not in r.parts and not r.drive.startswith("\\\\")
        and not any(x.casefold() in {"spica_datos", ".git", ".venv", ".codex", ".agents"} for x in r.parts)
        and r.name == "respaldo" and r.parent.name.startswith("spica-85k-")
        and r.parent.parent == p.h._base_temporal(), "raiz_temporal_invalida")
    p._segura(r)
    return r


@contextmanager
def _errores():
    try:
        yield
    except ErrorRespaldo85K:
        raise
    except Exception as e:
        codigo = ("destino_existente" if isinstance(e, FileExistsError) else
                  "archivo_ausente" if isinstance(e, FileNotFoundError) else
                  "error_sqlite" if isinstance(e, sqlite3.Error) else
                  "error_archivo" if isinstance(e, OSError) else "estado_o_formato_incompatible")
        raise ErrorRespaldo85K(codigo) from None


class GestorRespaldo85K:
    def __init__(self, *, limites=None, cancelacion=None):
        self.limites = limites if limites is not None else LimitesRespaldo85K()
        self.cancelacion = cancelacion if cancelacion is not None else Event()
        _exigir(type(self.limites) is LimitesRespaldo85K and type(self.cancelacion) is Event,
                "configuracion_invalida")
        self._inicio = 0.0

    def _punto(self, nombre):
        """Frontera inerte para inyectar fallos en pruebas; no se carga desde archivos."""

    def _control(self):
        _exigir(not self.cancelacion.is_set(), "operacion_cancelada")
        _exigir(time.monotonic() - self._inicio <= self.limites.segundos, "plazo_excedido")

    def _iniciar(self):
        self._inicio = time.monotonic()
        self._control()

    def _archivo(self, ruta, limite, *, salida=None):
        """Hash físico por bloques; revalida descriptor, nombre, enlaces y tamaño."""
        self._control()
        p._segura(ruta)
        con_nombre = ruta.stat()
        _exigir(stat.S_ISREG(con_nombre.st_mode) and con_nombre.st_nlink == 1
                and con_nombre.st_size <= limite, "archivo_inseguro_o_excesivo")
        huella, total = hashlib.sha256(), 0
        with ruta.open("rb") as f:
            antes = os.fstat(f.fileno())
            while True:
                self._control()
                b = f.read(self.limites.bloque)
                if not b:
                    break
                total += len(b)
                _exigir(total <= limite, "presupuesto_excedido")
                huella.update(b)
                if salida is not None:
                    _exigir(salida.write(b) == len(b), "escritura_incompleta")
            despues = os.fstat(f.fileno())
        p._segura(ruta)
        final = ruta.stat()
        clave = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_nlink)
        _exigir(clave(con_nombre) == clave(antes) == clave(despues) == clave(final)
                and total == antes.st_size, "archivo_cambio_durante_lectura")
        return total, huella.hexdigest()

    def _bytes(self, ruta, limite):
        # Solo metadatos y artefactos 85-J acotados; nunca CSV/RAW científicos.
        b = io.BytesIO()
        self._archivo(ruta, limite, salida=b)
        return b.getvalue()

    def _libre(self, raiz, necesario):
        self._control()
        _exigir(shutil.disk_usage(raiz).free >= necesario + self.limites.margen_libre,
                "espacio_insuficiente")

    def _publicar_temporal(self, tmp, destino, esperado):
        _exigir(self._archivo(tmp, esperado[0]) == esperado, "hash_copia_incorrecto")
        p._segura(destino.parent)
        destino.parent.mkdir(exist_ok=True)
        p._segura(destino)
        # Enlace solo de la COPIA recién escrita, jamás de los bytes del origen.
        os.link(tmp, destino)
        self._punto("enlace_publicado")
        # Ya hay dos nombres de nuestro inode; liberar solo nuestro temporal.
        p._segura(tmp).unlink()
        _exigir(self._archivo(destino, esperado[0]) == esperado, "hash_publicacion_incorrecto")

    def _copiar(self, origen, destino, trabajo, esperado):
        self._libre(trabajo, esperado[0])
        tmp = trabajo / (uuid4().hex + ".tmp")
        with p._segura(tmp).open("xb") as f:
            recibido = self._archivo(origen, esperado[0], salida=f)
            _exigir(recibido == esperado, "hash_origen_incorrecto")
            f.flush()
            os.fsync(f.fileno())
        self._publicar_temporal(tmp, destino, esperado)
        self._punto("archivo_copiado")

    def _escribir(self, datos, destino, trabajo):
        self._libre(trabajo, len(datos))
        tmp = trabajo / (uuid4().hex + ".tmp")
        with p._segura(tmp).open("xb") as f:
            _exigir(f.write(datos) == len(datos), "escritura_incompleta")
            f.flush()
            os.fsync(f.fileno())
        self._publicar_temporal(tmp, destino, (len(datos), _sha(datos)))

    def _sql(self, ruta, ejecucion_id):
        self._archivo(ruta, self.limites.max_bytes_sqlite)
        with closing(indice.abrir(ruta, lectura=True)) as c:
            _exigir(c.execute("PRAGMA journal_mode").fetchone()[0] == "delete", "perfil_sqlite_no_admitido")
            for tabla in _BASE:
                _exigir(c.execute(f"SELECT 1 FROM {tabla} LIMIT 1").fetchone() is None,
                        "catalogo_fuera_del_perfil")
            filas = {}
            for tabla in _TABLAS:
                self._control()
                maximo = self.limites.max_eventos if tabla == "linaje_eventos" else 4
                rs = c.execute(f"SELECT * FROM {tabla} ORDER BY 1,2").fetchmany(maximo + 1)
                _exigir(len(rs) <= maximo, "inventario_sql_excesivo")
                filas[tabla] = [dict(r) for r in rs]
                if tabla == "linaje_ejecuciones":
                    _exigir(len(rs) == 1, "generacion_ambigua")
            _exigir(len(filas["linaje_instancia"]) == len(filas["linaje_ejecuciones"]) == 1,
                    "generacion_ambigua")
            e = filas["linaje_ejecuciones"][0]
            ars = filas["linaje_artefactos"]
            _exigir(e["ejecucion_id"] == ejecucion_id and e["estado"] == "conservada"
                and len(ars) == 4 and {a["rol"] for a in ars} == set(p._ROLES), "generacion_no_conservada")
            for fila in sum(filas.values(), []):
                _exigir(all(v is None or type(v) is int or type(v) is str and len(v) <= 256
                             for v in fila.values()), "fila_sql_excesiva")
            _exigir(all(0 < a["tamano"] <= self.limites.max_bytes_archivo for a in ars),
                    "presupuesto_excedido")
            generacion = _sha(codec.canonico(dict(version=VERSION_RESPALDO, sqlite=indice.VERSION_SQLITE, filas=filas)))
            return generacion, filas

    def _snapshot(self, origen, destino, trabajo):
        self._libre(trabajo, self.limites.max_bytes_sqlite)
        tmp = trabajo / (uuid4().hex + ".tmp")
        with p._segura(tmp).open("xb"):
            pass
        with closing(indice.abrir(origen, lectura=True)) as src, closing(sqlite3.connect(tmp)) as dst:
            def avance(estado, restantes, paginas):
                self._control()
                _exigir(paginas * src.execute("PRAGMA page_size").fetchone()[0]
                        <= self.limites.max_bytes_sqlite, "presupuesto_sqlite_excedido")
            src.backup(dst, pages=16, progress=avance, sleep=0.01)
        with tmp.open("r+b") as f:
            f.flush()
            os.fsync(f.fileno())
        self._publicar_temporal(tmp, destino, self._archivo(tmp, self.limites.max_bytes_sqlite))
        self._punto("snapshot_sqlite")

    def _relativa(self, rol, sha):
        if rol in {"intencion", "catalogo", "piloto"}:
            return {"intencion": "intencion.json", "catalogo": "catalogo.sqlite3", "piloto": "piloto.json"}[rol]
        _exigir(rol in p._ROLES and type(sha) is str and bool(_HASH.fullmatch(sha)), "inventario_invalido")
        return f"contenido/{sha[:2]}/{sha}"

    def _arbol(self, raiz, esperados, *, respaldo, temporales=()):
        """Recorrido cerrado, no recursivo arbitrario; rechaza extras y enlaces."""
        archivos, dirs, pendientes = set(), set(), [raiz]
        while pendientes:
            d = pendientes.pop()
            p._segura(d)
            for entrada in d.iterdir():
                self._control()
                p._segura(entrada)
                rel = entrada.relative_to(raiz).as_posix()
                _exigir(len(archivos) + len(dirs) < 32, "arbol_excesivo")
                if entrada.is_dir():
                    _exigir(rel in {"contenido", "trabajo" if respaldo else "temporales"}
                            or bool(re.fullmatch(r"contenido/[0-9a-f]{2}", rel)), "directorio_ajeno")
                    dirs.add(rel)
                    pendientes.append(entrada)
                else:
                    archivos.add(rel)
        _exigir(archivos == set(esperados) | set(temporales), "archivos_ajenos_o_ausentes")
        requeridos = {"contenido", "trabajo" if respaldo else "temporales"}
        requeridos |= {str(Path(x).parent).replace("\\", "/") for x in esperados if x.startswith("contenido/")}
        _exigir(dirs == requeridos, "directorios_ajenos_o_ausentes")

    def _metadatos(self, raiz, filas):
        """Coteja cuerpos y contrato 85-H; nunca resuelve rutas históricas."""
        e = filas["linaje_ejecuciones"][0]
        ars = {a["rol"]: a for a in filas["linaje_artefactos"]}
        cuerpos = {}
        for rol, a in ars.items():
            ruta = raiz / self._relativa(rol, a["sha256"])
            b = self._bytes(ruta, a["tamano"])
            _exigir((len(b), _sha(b)) == (a["tamano"], a["sha256"]), "hash_artefacto_incorrecto")
            cuerpos[rol] = b
        r = codec.decodificar(cuerpos["informe"])
        ref = codec.leer_json(cuerpos["referencia"], profundidad=4, nodos=16)
        _exigir(ref == dict(version=p.VERSION_CONSERVACION, traza_sha256=_sha(cuerpos["traza"]),
            naturaleza="control_local_previo_del_ensayo", autenticidad_independiente=False), "referencia_incompatible")
        tr = p.t.TrazaCierre85H(cuerpos["traza"].decode("utf-8"), ref["traza_sha256"])
        cotejo = p.t.verificar_traza_85h(tr, r, referencia_sha256=ref["traza_sha256"])
        _exigir(cotejo.coherente_en_alcance and r.contrato.ejecucion_id == e["ejecucion_id"]
                and r.estado.value == e["estado_historico"], "linaje_contradictorio")
        # Reconstrucción cerrada del manifiesto 85-J: no reinterpreta sus campos.
        otros = [dict(rol=rol, sha256=_sha(cuerpos[rol]), tamano=len(cuerpos[rol])) for rol in p._ROLES[:3]]
        m = dict(version=p.VERSION_CONSERVACION, version_sqlite=indice.VERSION_SQLITE,
            instancia_id=filas["linaje_instancia"][0]["instancia_id"], ejecucion_id=e["ejecucion_id"],
            conservacion_id=e["conservacion_id"], estado_historico=r.estado.value,
            estado_conservacion="publicada_pendiente_confirmacion_sqlite", artefactos=otros,
            linaje=dict(informe_sha256=_sha(cuerpos["informe"]), traza_sha256=_sha(cuerpos["traza"]),
                        referencia_sha256=_sha(cuerpos["referencia"])), restricciones=list(r.restricciones),
            limitaciones=list(p._LIMITACIONES), ejecucion_cientifica=False, autorizacion_operativa=False)
        _exigir(cuerpos["manifiesto"] == codec.canonico(m)
                and e["manifiesto_sha256"] == _sha(cuerpos["manifiesto"])
                and e["contexto_sha256"] == _sha(codec.canonico({k: _sha(cuerpos[k]) for k in p._ROLES[:3]})),
                "manifiesto_85j_contradictorio")
        marcador = codec.leer_json(self._bytes(raiz / "piloto.json", 4096), profundidad=4, nodos=16)
        _exigir(marcador == dict(tipo="spica.linaje85j.temporal", version=p.VERSION_CONSERVACION,
            instancia_id=m["instancia_id"]), "instancia_contradictoria")
        return dict(instancia_id=m["instancia_id"], ejecucion_id=e["ejecucion_id"], conservacion_id=e["conservacion_id"],
            estado_historico=r.estado.value, estado_conservacion=e["estado"], restricciones=list(r.restricciones),
            diagnosticos=list(r.diagnosticos))

    def _lector(self, almacen, identidad, *, propio=False, temporales=()):
        self._control()
        r = almacen.recuperar(identidad, cancelacion=self.cancelacion)
        _exigir(r.informe is not None and r.cotejo is not None and r.cotejo.coherente_en_alcance
            and not r.huerfanos and r.temporales == tuple(temporales)
            and r.estado is (p.EstadoRecuperacion85J.REVISION_NECESARIA if propio else p.EstadoRecuperacion85J.VERIFICADA)
            and r.diagnosticos == (("residuos_o_escritor_requieren_revision",) if propio else ()),
            "lector_85j_requiere_revision")
        self._control()
        return r

    def respaldar(self, origen, destino, ejecucion_id):
        with _errores():
            self._iniciar()
            src = p.ConservadorLinaje85J(origen)
            dst = _raiz_respaldo(destino)
            p._id(ejecucion_id)
            _exigir(not dst.exists(), "destino_existente")
            self._lector(src, ejecucion_id)
            with src._escritor():
                self._lector(src, ejecucion_id, propio=True)
                gen, filas = self._sql(src.raiz / "catalogo.sqlite3", ejecucion_id)
                rutas = ["catalogo.sqlite3", "piloto.json", "escritor.lock"] + [
                    self._relativa(a["rol"], a["sha256"]) for a in filas["linaje_artefactos"]]
                self._arbol(src.raiz, rutas, respaldo=False)
                total = sum(a["tamano"] for a in filas["linaje_artefactos"]) + self.limites.max_bytes_sqlite + 8192
                _exigir(total + self.limites.max_bytes_manifiesto <= self.limites.max_bytes_total, "presupuesto_excedido")
                self._libre(dst.parent, total)
                dst.mkdir()
                (dst / "contenido").mkdir()
                trabajo = dst / "trabajo"
                trabajo.mkdir()
                identidad = uuid4().hex
                intencion = dict(version=VERSION_RESPALDO, respaldo_id=identidad, estado="preparada",
                                  creada_utc=datetime.now(timezone.utc).isoformat())
                self._escribir(codec.canonico(intencion), dst / "intencion.json", trabajo)
                self._punto("intencion_respaldo")
                self._snapshot(src.raiz / "catalogo.sqlite3", dst / "catalogo.sqlite3", trabajo)
                for rol in ("piloto", *p._ROLES):
                    a = next((a for a in filas["linaje_artefactos"] if a["rol"] == rol), None)
                    rel = self._relativa(rol, a["sha256"] if a else None)
                    esperado = (a["tamano"], a["sha256"]) if a else self._archivo(src.raiz / rel, 4096)
                    self._copiar(src.raiz / rel, dst / rel, trabajo, esperado)
                _exigir(self._sql(dst / "catalogo.sqlite3", ejecucion_id)[0] == gen
                    == self._sql(src.raiz / "catalogo.sqlite3", ejecucion_id)[0], "generacion_cambio")
                self._lector(src, ejecucion_id, propio=True)
                metadatos = self._metadatos(dst, filas)
                inventario = []
                for rol in _ROLES:
                    a = next((a for a in filas["linaje_artefactos"] if a["rol"] == rol), None)
                    rel = self._relativa(rol, a["sha256"] if a else None)
                    tam, sha = self._archivo(dst / rel, self.limites.max_bytes_sqlite if rol == "catalogo" else self.limites.max_bytes_archivo)
                    inventario.append(dict(rol=rol, ruta=rel, tamano=tam, sha256=sha))
                manifiesto = dict(version=VERSION_RESPALDO, sqlite=indice.VERSION_SQLITE,
                    conservacion=p.VERSION_CONSERVACION, codec=codec.VERSION_CODEC,
                    respaldo_id=identidad, generacion_sha256=gen, estado="publicada",
                    intencion=intencion, inventario=inventario, metadatos=metadatos,
                    condiciones=list(_CONDICIONES), limitaciones=list(_LIMITACIONES),
                    ejecucion_cientifica=False, autorizacion_operativa=False, autenticidad_independiente=False)
                datos = codec.canonico(manifiesto)
                _exigir(len(datos) <= self.limites.max_bytes_manifiesto, "manifiesto_excesivo")
                self._punto("antes_publicacion_respaldo")
                self._control()
                self._escribir(datos, dst / "respaldo.json", trabajo)
                self._punto("respaldo_publicado")
            control = ControlRespaldo85K(identidad, gen, _sha(datos))
            self.verificar_respaldo(dst, control)
            return control

    def verificar_respaldo(self, raiz, control):
        with _errores():
            self._iniciar()
            _exigir(type(control) is ControlRespaldo85K, "control_explicito_requerido")
            raiz = _raiz_respaldo(raiz)
            datos = self._bytes(raiz / "respaldo.json", self.limites.max_bytes_manifiesto)
            _exigir(_sha(datos) == control.manifiesto_sha256, "hash_manifiesto_incorrecto")
            m = codec.leer_json(datos, profundidad=12, nodos=4096)
            _exigir(type(m) is dict and set(m) == {"version", "sqlite", "conservacion", "codec", "respaldo_id",
                "generacion_sha256", "estado", "intencion", "inventario", "metadatos", "ejecucion_cientifica",
                "autorizacion_operativa", "autenticidad_independiente", "condiciones", "limitaciones"}, "manifiesto_incompatible")
            _exigir(m["version"] == VERSION_RESPALDO and m["sqlite"] == indice.VERSION_SQLITE
                and m["conservacion"] == p.VERSION_CONSERVACION and m["codec"] == codec.VERSION_CODEC,
                "version_incompatible")
            _exigir(m["respaldo_id"] == control.respaldo_id and m["generacion_sha256"] == control.generacion_sha256
                and m["condiciones"] == list(_CONDICIONES) and m["limitaciones"] == list(_LIMITACIONES)
                and m["estado"] == "publicada" and all(m[x] is False for x in
                    ("ejecucion_cientifica", "autorizacion_operativa", "autenticidad_independiente")), "control_contradictorio")
            inv = m["inventario"]
            _exigir(type(inv) is list and len(inv) == 7, "inventario_invalido")
            vistos, total = set(), 0
            for a in inv:
                _exigir(type(a) is dict and set(a) == {"rol", "ruta", "tamano", "sha256"}
                    and type(a["rol"]) is str and a["rol"] in _ROLES and a["rol"] not in vistos
                    and type(a["sha256"]) is str and bool(_HASH.fullmatch(a["sha256"]))
                    and type(a["tamano"]) is int and 0 < a["tamano"] <= (self.limites.max_bytes_sqlite
                        if a["rol"] == "catalogo" else self.limites.max_bytes_archivo), "inventario_invalido")
                _exigir(a["ruta"] == self._relativa(a["rol"], a["sha256"]), "ruta_inventario_insegura")
                vistos.add(a["rol"])
                total += a["tamano"]
                _exigir(total + len(datos) <= self.limites.max_bytes_total, "presupuesto_excedido")
                _exigir(self._archivo(raiz / a["ruta"], a["tamano"]) == (a["tamano"], a["sha256"]), "hash_copia_incorrecto")
            self._arbol(raiz, [a["ruta"] for a in inv] + ["respaldo.json"], respaldo=True)
            intencion = codec.leer_json(self._bytes(raiz / "intencion.json", 4096), profundidad=4, nodos=16)
            _exigir(type(intencion) is dict and set(intencion) == {"version", "respaldo_id", "estado", "creada_utc"}
                and intencion == m["intencion"] and intencion["version"] == VERSION_RESPALDO
                and intencion["respaldo_id"] == control.respaldo_id and intencion["estado"] == "preparada",
                "intencion_contradictoria")
            fecha = datetime.fromisoformat(intencion["creada_utc"])
            _exigir(fecha.tzinfo is not None and fecha.utcoffset().total_seconds() == 0, "fecha_invalida")
            gen, filas = self._sql(raiz / "catalogo.sqlite3", m["metadatos"]["ejecucion_id"])
            _exigir(gen == control.generacion_sha256, "generacion_contradictoria")
            _exigir(self._metadatos(raiz, filas) == m["metadatos"], "metadatos_contradictorios")
            esperados = {a["rol"]: a for a in filas["linaje_artefactos"]}
            _exigir(all(a["sha256"] == esperados[a["rol"]]["sha256"] and a["tamano"] == esperados[a["rol"]]["tamano"]
                         for a in inv if a["rol"] in p._ROLES), "inventario_sql_contradictorio")
            return m

    def restaurar(self, respaldo, destino, control):
        with _errores():
            m = self.verificar_respaldo(respaldo, control)
            self._control()
            src, dst = _raiz_respaldo(respaldo), p._raiz(destino)
            _exigir(not dst.exists() and dst != src, "destino_existente")
            self._libre(dst.parent, sum(a["tamano"] for a in m["inventario"]))
            dst.mkdir()
            (dst / "contenido").mkdir()
            trabajo = dst / "temporales"
            trabajo.mkdir()
            restauracion_id = uuid4().hex
            intencion = trabajo / (restauracion_id + ".intencion")
            marca = codec.canonico(dict(restauracion_id=restauracion_id, respaldo_id=control.respaldo_id,
                                        estado="restauracion_preparada"))
            with intencion.open("xb") as f:
                _exigir(f.write(marca) == len(marca), "escritura_incompleta")
                f.flush()
                os.fsync(f.fileno())
            almacen = p.ConservadorLinaje85J(dst)
            with almacen._escritor():
                self._punto("intencion_restauracion")
                for a in m["inventario"]:
                    if a["rol"] != "intencion":
                        self._copiar(src / a["ruta"], dst / a["ruta"], trabajo, (a["tamano"], a["sha256"]))
                _exigir(self._sql(dst / "catalogo.sqlite3", m["metadatos"]["ejecucion_id"])[0]
                        == control.generacion_sha256, "generacion_contradictoria")
                _exigir(self._metadatos(dst, self._sql(dst / "catalogo.sqlite3", m["metadatos"]["ejecucion_id"])[1])
                        == m["metadatos"], "metadatos_contradictorios")
                self._lector(almacen, m["metadatos"]["ejecucion_id"], propio=True, temporales=(intencion.name,))
                self._arbol(dst, [a["ruta"] for a in m["inventario"] if a["rol"] != "intencion"] + ["escritor.lock"],
                            respaldo=False, temporales=("temporales/" + intencion.name,))
                self._punto("antes_publicacion_restauracion")
                self._control()
                _exigir(self._bytes(intencion, 1024) == marca, "intencion_contradictoria")
                p._segura(intencion).unlink()
            # La ausencia de nuestro lock/temporal habilita al lector existente.
            self._punto("restauracion_publicada")
            r = self._lector(almacen, m["metadatos"]["ejecucion_id"])
            return Restauracion85K(restauracion_id, control, r)
