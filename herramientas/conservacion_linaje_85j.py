"""Conservación experimental offline de informes 85-G/H en temporales propios.

No acepta almacenes operativos, no ejecuta tareas, no repara ni elimina huérfanos.
Las rutas históricas del informe son datos inertes, nunca localizadores de E/S.
"""

from contextlib import closing, contextmanager
from dataclasses import dataclass, fields, is_dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import os
from pathlib import Path
import re
import sqlite3
import stat
import tempfile
from threading import Event
import time
from types import MappingProxyType
from uuid import uuid4

from herramientas import piloto_integracion_85g as h
from herramientas import traza_cierre_85h as t
from herramientas import _catalogo_linaje_85j as indice
from herramientas import _codec_linaje_85j as codec
from spica.adquisicion.almacenamiento.raw import _segura

VERSION_CONSERVACION = "0.1.0"
_ROLES = ("informe", "traza", "referencia", "manifiesto")
_HASH = re.compile(r"[0-9a-f]{64}")
_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}")
_LIMITACIONES = ("experimental_sintetico", "un_escritor_cooperativo", "sin_atomicidad_global",
    "sin_garantia_ante_apagado", "sin_autenticidad_independiente", "sin_validacion_cientifica",
    "sin_autorizacion_operativa", "original_85g_eliminado_no_revalidable",
    "sin_reanudacion_de_tareas", "sin_respaldo_general")


class EstadoConservacion85J(Enum):
    PREPARADA = "preparada"
    ESCRIBIENDO = "escribiendo"
    PUBLICADA = "publicada"
    REFERENCIAS_CONFIRMADAS = "referencias_confirmadas"
    CONSERVADA = "conservada"
    INCOMPLETA = "incompleta"
    FALLIDA = "fallida"


class EstadoRecuperacion85J(Enum):
    VERIFICADA = "verificada_en_alcance"
    INCOMPLETA = "incompleta"
    AUSENTE = "artefacto_ausente"
    CORRUPTA = "artefacto_corrupto"
    CONFLICTO = "conflicto_de_identidad"
    VERSION_INCOMPATIBLE = "version_incompatible"
    REVISION_NECESARIA = "revision_necesaria"


class ErrorConservacion85J(Exception):
    def __init__(self, codigo):
        self.codigo = codigo
        super().__init__(codigo)


@dataclass(frozen=True)
class LimitesConservacion85J:
    max_artefactos: int = 4
    max_bytes_artefacto: int = 8_388_608
    max_bytes_total: int = 25_165_824
    max_profundidad: int = 48
    max_nodos: int = 250_000
    max_referencias: int = 128
    tamano_bloque: int = 65_536
    max_segundos: float = 120.0

    def __post_init__(self):
        for nombre, tope in (("max_artefactos", 4), ("max_bytes_artefacto", 8_388_608),
                ("max_bytes_total", 33_554_432), ("max_profundidad", 64),
                ("max_nodos", 500_000), ("max_referencias", 1024), ("tamano_bloque", 1_048_576)):
            v = getattr(self, nombre)
            if type(v) is not int or not 0 < v <= tope:
                raise ValueError("limites_conservacion_invalidos")
        if type(self.max_segundos) not in (int, float) or not 0 < self.max_segundos <= 300:
            raise ValueError("plazo_conservacion_invalido")


@dataclass(frozen=True)
class Artefacto85J:
    rol: str
    sha256: str
    tamano: int


@dataclass(frozen=True)
class Recuperacion85J:
    estado: EstadoRecuperacion85J
    ejecucion_id: str
    conservacion_id: str | None = None
    estado_historico: h.EstadoEjecucion85G | None = None
    estado_conservacion: EstadoConservacion85J | None = None
    diagnosticos: tuple[str, ...] = ()
    artefactos: tuple[Artefacto85J, ...] = ()
    huerfanos: tuple[str, ...] = ()
    temporales: tuple[str, ...] = ()
    informe: h.InformeEjecucion85G | None = None
    traza: t.TrazaCierre85H | None = None
    referencia_sha256: str | None = None
    cotejo: t.VerificacionTraza85H | None = None
    limitaciones: tuple[str, ...] = _LIMITACIONES

    def __bool__(self):
        raise TypeError("recuperacion_no_es_permiso")

    def resumen(self):
        r = self.informe
        return dict(version=VERSION_CONSERVACION, estado=self.estado.value,
            ejecucion_id=self.ejecucion_id, conservacion_id=self.conservacion_id,
            estado_historico=None if self.estado_historico is None else self.estado_historico.value,
            estado_conservacion=None if self.estado_conservacion is None else self.estado_conservacion.value,
            diagnosticos=list(self.diagnosticos), artefactos=[dict(rol=a.rol, sha256=a.sha256,
                tamano=a.tamano) for a in self.artefactos], huerfanos=list(self.huerfanos),
            temporales=list(self.temporales), referencia_sha256=self.referencia_sha256,
            cotejo_85h=None if self.cotejo is None else self.cotejo.coherente_en_alcance,
            resultados=[] if r is None else [len(xs) for xs in r.resultados],
            restricciones=[] if r is None else [[c.restricciones_informativas,
                c.restricciones_bloqueantes] for c in r.consumos],
            restricciones_globales=[] if r is None else list(r.restricciones),
            autorizacion_operativa=False, ejecucion_cientifica=False,
            autenticidad_independiente=False, limitaciones=list(self.limitaciones))


def _ahora():
    return datetime.now(timezone.utc).isoformat()


def _sha(datos):
    return hashlib.sha256(datos).hexdigest()


def _id(valor):
    if type(valor) is not str or not _ID.fullmatch(valor):
        raise ErrorConservacion85J("identidad_invalida")


def _raiz(raiz):
    p = Path(raiz).absolute()
    # Rechazo léxico antes de sondear/resolver ubicaciones del llamador.
    if (".." in p.parts or p.drive.startswith("\\\\")
            or any(x.casefold() in {"spica_datos", ".git", ".venv", ".codex", ".agents"} for x in p.parts)
            or p.name != "conservacion" or not p.parent.name.startswith("spica-85j-")):
        raise ErrorConservacion85J("raiz_temporal_no_autorizada")
    base = h._base_temporal()
    if p.parent.parent != base:
        raise ErrorConservacion85J("raiz_temporal_no_autorizada")
    _segura(p)
    return p


@contextmanager
def entorno_piloto_85j():
    """El padre del ensayo controla la vida del temporal entre subprocesos."""
    with tempfile.TemporaryDirectory(prefix="spica-85j-", dir=h._base_temporal()) as carpeta:
        yield Path(carpeta) / "conservacion"


class ConservadorLinaje85J:
    def __init__(self, raiz, *, limites=LimitesConservacion85J()):
        if type(limites) is not LimitesConservacion85J:
            raise TypeError("limites_tipados_requeridos")
        self.raiz = _raiz(raiz)
        self.limites = limites
        self._cerrado = False

    @classmethod
    def crear(cls, raiz, *, limites=LimitesConservacion85J()):
        self = cls(raiz, limites=limites)
        try:
            self.raiz.mkdir(mode=0o700)  # Exclusiva: nunca reinicializar una raíz existente.
            for nombre in ("contenido", "temporales"):
                (self.raiz / nombre).mkdir(mode=0o700)
            instancia = uuid4().hex
            indice.crear_nuevo(self.raiz / "catalogo.sqlite3", instancia)
            datos = codec.canonico(dict(tipo="spica.linaje85j.temporal", version=VERSION_CONSERVACION,
                                       instancia_id=instancia))
            with (self.raiz / "piloto.json").open("xb") as f:
                if f.write(datos) != len(datos):
                    raise ErrorConservacion85J("escritura_incompleta")
                f.flush()
                os.fsync(f.fileno())
            return self
        except (OSError, sqlite3.Error, ValueError):
            raise ErrorConservacion85J("creacion_temporal_no_completada") from None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        self._cerrado = True  # Cada operación ya cerró sus conexiones/descriptores.

    def _punto(self, nombre):
        """Frontera inyectable solo por tests confiables; nunca desde archivos."""

    def _control(self, evento, inicio):
        if evento.is_set():
            raise ErrorConservacion85J("conservacion_cancelada")
        if time.monotonic() - inicio > self.limites.max_segundos:
            raise ErrorConservacion85J("plazo_excedido")

    def _abrir(self, *, lectura=False):
        if self._cerrado:
            raise ErrorConservacion85J("instancia_cerrada")
        _raiz(self.raiz)
        for nombre in ("contenido", "temporales"):
            if not _segura(self.raiz / nombre).is_dir():
                raise ErrorConservacion85J("estructura_temporal_incompleta")
        ruta = _segura(self.raiz / "catalogo.sqlite3")
        if not stat.S_ISREG(ruta.stat().st_mode) or ruta.stat().st_nlink != 1:
            raise ErrorConservacion85J("catalogo_no_regular")
        marcador = self._leer(self.raiz / "piloto.json", 4096)
        d = codec.leer_json(marcador, profundidad=4, nodos=16)
        if (type(d) is not dict or set(d) != {"tipo", "version", "instancia_id"}
                or d["tipo"] != "spica.linaje85j.temporal" or d["version"] != VERSION_CONSERVACION
                or type(d["instancia_id"]) is not str or not re.fullmatch(r"[0-9a-f]{32}", d["instancia_id"])):
            raise ErrorConservacion85J("version_marcador_incompatible")
        c = indice.abrir(ruta, lectura=lectura)
        try:
            instancia = c.execute("SELECT instancia_id FROM linaje_instancia").fetchone()[0]
            if instancia != d["instancia_id"]:
                raise ErrorConservacion85J("instancia_contradictoria")
            return c, instancia
        except BaseException:
            c.close()
            raise

    def _leer(self, ruta, limite, *, evento=None, inicio=None):
        _segura(ruta)
        with ruta.open("rb") as f:
            s = os.fstat(f.fileno())
            if not stat.S_ISREG(s.st_mode):
                raise ErrorConservacion85J("archivo_no_regular")
            if s.st_size > limite:
                raise ErrorConservacion85J("archivo_tamano_excedido")
            bloques = bytearray()
            while datos := f.read(min(self.limites.tamano_bloque, limite + 1 - len(bloques))):
                if evento is not None:
                    self._control(evento, inicio)
                bloques.extend(datos)
                if len(bloques) > limite:
                    raise ErrorConservacion85J("presupuesto_excedido")
            firma = lambda x: (x.st_dev, x.st_ino, x.st_size, x.st_mtime_ns)
            if firma(s) != firma(os.fstat(f.fileno())) or firma(s) != firma(ruta.stat()) or len(bloques) != s.st_size:
                raise ErrorConservacion85J("archivo_sustituido")
            _segura(ruta)
            return bytes(bloques)

    @contextmanager
    def _escritor(self):
        p = _segura(self.raiz / "escritor.lock")
        nonce = uuid4().hex.encode("ascii")
        try:
            with p.open("xb") as f:
                if f.write(nonce) != len(nonce):
                    raise ErrorConservacion85J("escritura_incompleta")
                f.flush()
                os.fsync(f.fileno())
        except FileExistsError:
            raise ErrorConservacion85J("escritor_o_marcador_pendiente") from None
        try:
            yield
        finally:
            if self._leer(p, 64) != nonce:
                raise ErrorConservacion85J("marcador_escritor_sustituido")
            _segura(p).unlink()

    def _ruta_artefacto(self, sha):
        if type(sha) is not str or not _HASH.fullmatch(sha):
            raise ErrorConservacion85J("hash_de_referencia_invalido")
        return _segura(self.raiz / "contenido" / sha[:2] / sha)

    def _publicar(self, rol, datos, evento, inicio):
        self._control(evento, inicio)
        if not 0 < len(datos) <= self.limites.max_bytes_artefacto:
            raise ErrorConservacion85J("presupuesto_excedido")
        huella = _sha(datos)
        temporal = _segura(self.raiz / "temporales" / (uuid4().hex + ".tmp"))
        # Los temporales incompletos se conservan para diagnóstico, no se borran aquí.
        with temporal.open("xb") as f:
            paso = min(self.limites.tamano_bloque, max(1, len(datos) // 2))
            for pos in range(0, len(datos), paso):
                self._control(evento, inicio)
                bloque = datos[pos:pos + paso]
                if f.write(bloque) != len(bloque):
                    raise ErrorConservacion85J("escritura_incompleta")
                if pos == 0:
                    f.flush()
                    self._punto("parcial")
            f.flush()
            os.fsync(f.fileno())
        self._punto("temporal")
        leidos = self._leer(temporal, len(datos), evento=evento, inicio=inicio)
        if leidos != datos or _sha(leidos) != huella:
            raise ErrorConservacion85J("integridad_temporal_fallida")
        self._punto("verificado")
        destino = self._ruta_artefacto(huella)
        destino.parent.mkdir(exist_ok=True)
        _segura(destino)
        try:
            os.link(temporal, destino)
        except FileExistsError:
            if self._leer(destino, len(datos), evento=evento, inicio=inicio) != datos:
                raise ErrorConservacion85J("conflicto_de_publicacion") from None
        leidos = self._leer(destino, len(datos), evento=evento, inicio=inicio)
        if leidos != datos or _sha(leidos) != huella:
            raise ErrorConservacion85J("integridad_publicacion_fallida")
        _segura(temporal).unlink()
        self._punto("manifiesto" if rol == "manifiesto" else "artefacto")
        return Artefacto85J(rol, huella, len(datos))

    def _evento(self, c, identidad, estado, codigo):
        c.execute("INSERT INTO linaje_eventos(ejecucion_id,estado,codigo,fecha_utc) VALUES (?,?,?,?)",
                  (identidad, estado, codigo, _ahora()))

    def _estado(self, c, identidad, estado, codigo):
        c.execute("UPDATE linaje_ejecuciones SET estado=? WHERE ejecucion_id=?", (estado, identidad))
        self._evento(c, identidad, estado, codigo)

    def _validar_informe(self, r, traza, referencia):
        if type(r) is not h.InformeEjecucion85G or type(traza) is not t.TrazaCierre85H:
            raise ErrorConservacion85J("contratos_tipados_requeridos")
        _id(r.contrato.ejecucion_id)
        cotejo = t.verificar_traza_85h(traza, r, referencia_sha256=referencia)
        if not cotejo.coherente_en_alcance:
            raise ErrorConservacion85J("cotejo_85h_rechazado")
        base = r.temporal
        if base is not None and (not base.is_absolute() or base.parent != h._base_temporal()
                or not base.name.startswith("spica-85g-") or ".." in base.parts):
            raise ErrorConservacion85J("referencia_historica_invalida")
        def rutas(v):
            if isinstance(v, Path):
                if base is None or ".." in v.parts or not v.is_relative_to(base):
                    raise ErrorConservacion85J("referencia_historica_invalida")
            elif is_dataclass(v) and not isinstance(v, type):
                for f in fields(v):
                    rutas(getattr(v, f.name))
            elif isinstance(v, (tuple, list)):
                for x in v:
                    rutas(x)
            elif type(v) in (dict, MappingProxyType):
                for x in v.values():
                    rutas(x)
        rutas(r)
        return cotejo

    def conservar(self, informe, traza, *, referencia_sha256, cancelacion=None):
        evento = cancelacion if cancelacion is not None else Event()
        if type(evento) is not Event:
            raise TypeError("evento_cancelacion_requerido")
        inicio = time.monotonic()
        preparada = confirmada = False
        identidad = None
        try:
            self._control(evento, inicio)
            self._validar_informe(informe, traza, referencia_sha256)
            identidad = informe.contrato.ejecucion_id
            l = self.limites
            datos = dict(informe=codec.codificar(informe, profundidad=l.max_profundidad, nodos=l.max_nodos),
                traza=traza.canonico.encode("utf-8"), referencia=codec.canonico(dict(
                    version=VERSION_CONSERVACION, traza_sha256=referencia_sha256,
                    naturaleza="control_local_previo_del_ensayo", autenticidad_independiente=False)))
            if l.max_artefactos < 4 or any(len(x) > l.max_bytes_artefacto for x in datos.values()):
                raise ErrorConservacion85J("presupuesto_excedido")
            if sum(map(len, datos.values())) > l.max_bytes_total:
                raise ErrorConservacion85J("presupuesto_excedido")
            # Demostrar reversibilidad antes de escribir; no aceptar un codec con pérdida.
            copia = codec.decodificar(datos["informe"], profundidad=l.max_profundidad, nodos=l.max_nodos)
            if copia != informe:
                raise ErrorConservacion85J("codec_no_reversible")
            contexto = _sha(codec.canonico({k: _sha(v) for k, v in datos.items()}))
            previo, _ = self._abrir(lectura=True)
            previo.close()
            with self._escritor():
                c, instancia = self._abrir()
                with closing(c):
                    fila = c.execute("SELECT * FROM linaje_ejecuciones WHERE ejecucion_id=?", (identidad,)).fetchone()
                    if fila is not None:
                        if fila["contexto_sha256"] != contexto:
                            raise ErrorConservacion85J("conflicto_de_identidad")
                        if fila["estado"] != "conservada":
                            raise ErrorConservacion85J("conservacion_previa_requiere_revision")
                    else:
                        if c.execute("SELECT count(*) FROM linaje_artefactos").fetchone()[0] + 4 > l.max_referencias:
                            raise ErrorConservacion85J("inventario_excede_presupuesto")
                        conservacion_id = uuid4().hex
                        with c:
                            c.execute("BEGIN IMMEDIATE")
                            c.execute("INSERT INTO linaje_ejecuciones VALUES (?,?,?,?,?,?,?)", (
                                identidad, conservacion_id, informe.estado.value, "preparada", contexto,
                                None, _ahora()))
                            self._evento(c, identidad, "preparada", "intencion_confirmada")
                        preparada = True
                        self._punto("intencion")
                        with c:
                            self._estado(c, identidad, "escribiendo", "escritura_iniciada")
                        ars = [self._publicar(rol, cuerpo, evento, inicio) for rol, cuerpo in datos.items()]
                        m = dict(version=VERSION_CONSERVACION, version_sqlite=indice.VERSION_SQLITE,
                            instancia_id=instancia, ejecucion_id=identidad, conservacion_id=conservacion_id,
                            estado_historico=informe.estado.value,
                            estado_conservacion="publicada_pendiente_confirmacion_sqlite",
                            artefactos=[dict(rol=a.rol, sha256=a.sha256, tamano=a.tamano) for a in ars],
                            linaje=dict(informe_sha256=ars[0].sha256, traza_sha256=ars[1].sha256,
                                referencia_sha256=ars[2].sha256),
                            restricciones=list(informe.restricciones), limitaciones=list(_LIMITACIONES),
                            ejecucion_cientifica=False, autorizacion_operativa=False)
                        manifiesto = codec.canonico(m)
                        if sum(map(len, datos.values())) + len(manifiesto) > l.max_bytes_total:
                            raise ErrorConservacion85J("presupuesto_excedido")
                        ars.append(self._publicar("manifiesto", manifiesto, evento, inicio))
                        with c:
                            self._estado(c, identidad, "publicada", "artefactos_releidos")
                        self._control(evento, inicio)
                        with c:
                            c.execute("BEGIN IMMEDIATE")
                            for a in ars:
                                c.execute("INSERT INTO linaje_artefactos VALUES (?,?,?,?)",
                                          (identidad, a.rol, a.sha256, a.tamano))
                            self._estado(c, identidad, "referencias_confirmadas", "referencias_en_transaccion")
                            self._punto("referencias")
                            c.execute("UPDATE linaje_ejecuciones SET manifiesto_sha256=? WHERE ejecucion_id=?",
                                      (ars[-1].sha256, identidad))
                            self._estado(c, identidad, "conservada", "confirmacion_logica")
                        confirmada = True
                        self._punto("confirmacion")
            self._punto("cierre")
            resultado = self.recuperar(identidad)
            if resultado.estado is not EstadoRecuperacion85J.VERIFICADA:
                raise ErrorConservacion85J("conservacion_no_verificable")
            return resultado
        except Exception as error:
            codigo = (error.codigo if isinstance(error, ErrorConservacion85J) else
                      "error_sqlite" if isinstance(error, sqlite3.Error) else
                      "error_archivo" if isinstance(error, OSError) else "entrada_o_estado_incompatible")
            if preparada and not confirmada:
                try:
                    c, _ = self._abrir()
                    with closing(c), c:
                        self._estado(c, identidad, "incompleta" if codigo == "conservacion_cancelada" else "fallida", codigo)
                except Exception:
                    pass  # Intención/residuos permiten detectar incertidumbre; no fingir evento persistido.
            raise ErrorConservacion85J(codigo) from None

    def _inventario(self, c):
        refs = c.execute("SELECT sha256 FROM linaje_artefactos").fetchmany(self.limites.max_referencias + 1)
        if len(refs) > self.limites.max_referencias:
            raise ErrorConservacion85J("inventario_excede_presupuesto")
        conocidos = {r[0] for r in refs}
        huerfanos, temporales = [], []
        vistos = 0
        for prefijo in (self.raiz / "contenido").iterdir():
            vistos += 1
            _segura(prefijo)
            if not re.fullmatch(r"[0-9a-f]{2}", prefijo.name) or not prefijo.is_dir():
                raise ErrorConservacion85J("contenido_ajeno")
            for p in prefijo.iterdir():
                vistos += 1
                _segura(p)
                if not p.is_file() or not _HASH.fullmatch(p.name) or not p.name.startswith(prefijo.name):
                    raise ErrorConservacion85J("contenido_ajeno")
                if p.name not in conocidos:
                    huerfanos.append(p.relative_to(self.raiz).as_posix())
                if vistos > self.limites.max_referencias * 3:
                    raise ErrorConservacion85J("inventario_excede_presupuesto")
        for p in (self.raiz / "temporales").iterdir():
            _segura(p)
            temporales.append(p.name)
            if len(temporales) > self.limites.max_referencias:
                raise ErrorConservacion85J("inventario_excede_presupuesto")
        return tuple(sorted(huerfanos)), tuple(sorted(temporales))

    def recuperar(self, ejecucion_id, *, cancelacion=None):
        _id(ejecucion_id)
        evento = cancelacion if cancelacion is not None else Event()
        inicio = time.monotonic()
        contexto = {}
        try:
            c, instancia = self._abrir(lectura=True)
            with closing(c):
                fila = c.execute("SELECT * FROM linaje_ejecuciones WHERE ejecucion_id=?", (ejecucion_id,)).fetchone()
                if fila is None:
                    return Recuperacion85J(EstadoRecuperacion85J.INCOMPLETA, ejecucion_id,
                                           diagnosticos=("ejecucion_no_conservada",))
                if type(fila["conservacion_id"]) is not str or not re.fullmatch(r"[0-9a-f]{32}", fila["conservacion_id"]):
                    raise ErrorConservacion85J("conflicto_de_identidad")
                contexto.update(conservacion_id=fila["conservacion_id"],
                    estado_historico=h.EstadoEjecucion85G(fila["estado_historico"]),
                    estado_conservacion=EstadoConservacion85J(fila["estado"]))
                hs, ts = self._inventario(c)
                contexto.update(huerfanos=hs, temporales=ts)
                if fila["estado"] != "conservada":
                    return Recuperacion85J(EstadoRecuperacion85J.INCOMPLETA, ejecucion_id,
                        diagnosticos=("cierre_logico_no_confirmado",), **contexto)
                filas = c.execute("SELECT * FROM linaje_artefactos WHERE ejecucion_id=? ORDER BY rol",
                                  (ejecucion_id,)).fetchmany(self.limites.max_artefactos + 1)
                if len(filas) != 4 or {r["rol"] for r in filas} != set(_ROLES):
                    raise ErrorConservacion85J("inventario_obligatorio_incompleto")
                artefactos = tuple(Artefacto85J(r["rol"], r["sha256"], r["tamano"]) for r in filas)
                contexto["artefactos"] = artefactos
                if sum(a.tamano for a in artefactos) > self.limites.max_bytes_total:
                    raise ErrorConservacion85J("presupuesto_excedido")
                cuerpos = {}
                for a in artefactos:
                    self._control(evento, inicio)
                    if type(a.tamano) is not int or not 0 < a.tamano <= self.limites.max_bytes_artefacto:
                        raise ErrorConservacion85J("presupuesto_excedido")
                    b = self._leer(self._ruta_artefacto(a.sha256), a.tamano, evento=evento, inicio=inicio)
                    if len(b) != a.tamano or _sha(b) != a.sha256:
                        raise ErrorConservacion85J("integridad_artefacto_fallida")
                    cuerpos[a.rol] = b
                l = self.limites
                m = codec.leer_json(cuerpos["manifiesto"], profundidad=l.max_profundidad, nodos=l.max_nodos)
                if type(m) is not dict or m.get("version") != VERSION_CONSERVACION or m.get("version_sqlite") != indice.VERSION_SQLITE:
                    raise ErrorConservacion85J("version_manifiesto_incompatible")
                r = codec.decodificar(cuerpos["informe"], profundidad=l.max_profundidad, nodos=l.max_nodos)
                ref = codec.leer_json(cuerpos["referencia"], profundidad=4, nodos=16)
                if (type(ref) is not dict or set(ref) != {"version", "traza_sha256", "naturaleza", "autenticidad_independiente"}
                        or ref["version"] != VERSION_CONSERVACION
                        or ref["naturaleza"] != "control_local_previo_del_ensayo" or ref["autenticidad_independiente"] is not False):
                    raise ErrorConservacion85J("control_de_referencia_incompatible")
                tr = t.TrazaCierre85H(cuerpos["traza"].decode("utf-8"), ref["traza_sha256"])
                cotejo = self._validar_informe(r, tr, ref["traza_sha256"])
                esperados = [dict(rol=rol, sha256=_sha(cuerpos[rol]), tamano=len(cuerpos[rol])) for rol in _ROLES[:3]]
                esperado = dict(version=VERSION_CONSERVACION, version_sqlite=indice.VERSION_SQLITE,
                    instancia_id=instancia, ejecucion_id=ejecucion_id, conservacion_id=fila["conservacion_id"],
                    estado_historico=r.estado.value, estado_conservacion="publicada_pendiente_confirmacion_sqlite",
                    artefactos=esperados, linaje=dict(informe_sha256=_sha(cuerpos["informe"]),
                        traza_sha256=_sha(cuerpos["traza"]), referencia_sha256=_sha(cuerpos["referencia"])),
                    restricciones=list(r.restricciones), limitaciones=list(_LIMITACIONES),
                    ejecucion_cientifica=False, autorizacion_operativa=False)
                if (m != esperado or cuerpos["manifiesto"] != codec.canonico(esperado)
                        or fila["manifiesto_sha256"] != _sha(cuerpos["manifiesto"])
                        or fila["contexto_sha256"] != _sha(codec.canonico({k: _sha(cuerpos[k]) for k in _ROLES[:3]}))
                        or r.contrato.ejecucion_id != ejecucion_id or r.estado.value != fila["estado_historico"]):
                    raise ErrorConservacion85J("conflicto_de_identidad")
                revision = _segura(self.raiz / "escritor.lock").exists() or bool(hs) or bool(ts)
                return Recuperacion85J(EstadoRecuperacion85J.REVISION_NECESARIA if revision else EstadoRecuperacion85J.VERIFICADA,
                    ejecucion_id, informe=r, traza=tr, referencia_sha256=ref["traza_sha256"], cotejo=cotejo,
                    diagnosticos=("residuos_o_escritor_requieren_revision",) if revision else (), **contexto)
        except Exception as error:
            codigo = getattr(error, "codigo", str(error) if isinstance(error, indice.ErrorIndice85J) else
                             "error_sqlite" if isinstance(error, sqlite3.Error) else "lectura_o_formato_no_disponible")
            if isinstance(error, ValueError) and str(error) in {"version_codec_incompatible"}:
                codigo = str(error)
            estado = EstadoRecuperacion85J.REVISION_NECESARIA
            if isinstance(error, FileNotFoundError):
                estado, codigo = EstadoRecuperacion85J.AUSENTE, "archivo_requerido_ausente"
            elif "version" in codigo:
                estado = EstadoRecuperacion85J.VERSION_INCOMPATIBLE
            elif codigo in {"integridad_artefacto_fallida", "integridad_temporal_fallida", "archivo_sustituido", "archivo_tamano_excedido"}:
                estado = EstadoRecuperacion85J.CORRUPTA
            elif codigo == "conflicto_de_identidad":
                estado = EstadoRecuperacion85J.CONFLICTO
            return Recuperacion85J(estado, ejecucion_id, diagnosticos=(codigo,), **contexto)
