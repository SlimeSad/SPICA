"""RC5: publicación y relectura TEMP de bytes explícitamente sintéticos.

No ejecuta productores, transforma datos, confirma RAW ni conserva un catálogo.
"""

from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import hashlib
import os
import re
from threading import Event
from uuid import uuid4

from ..adquisicion.nucleo.modelos import EstadoIntegridad
from ..adquisicion.readquisicion.modelos import EstadoLocal
from ..calidad.restricciones import TipoRestriccionQA
from ..contextos import EstadoOperacion as S
from ..interoperabilidad.adaptadores import DiagnosticoAdaptacion as D, NivelDiagnostico as N
from ..interoperabilidad.modelos import EstadoAptitud as E
from . import DescriptorArtefacto, InformeLinaje, InventarioArtefactos, ReferenciaArtefacto, inspeccionar_linaje
from ._archivos_rc5 import ArchivosTEMP, ErrorArchivoExperimental, controlar, firma, huella

VERSION_MATERIALIZACION = "0.1.0"
USO_MATERIALIZAR = "materializar_sintetico_rc5"
USO_VERIFICAR = "verificar_fisicamente_rc5"


def _sha(v):
    if type(v) is not str or not re.fullmatch(r"[0-9a-f]{64}", v):
        raise ValueError("huella_rc5_no_admitida")


def _entero(v, maximo):
    if type(v) is not int or not 0 <= v <= maximo:
        raise ValueError("entero_rc5_no_admitido")


def _version(v):
    if type(v) is not str or v != VERSION_MATERIALIZACION:
        raise ValueError("version_rc5_no_admitida")


def _diagnostico(codigo, nivel=N.CONTRADICCION):
    return D(codigo, "materializacion_rc5", nivel)


def _evento(v):
    if v is not None and type(v) is not Event:
        raise TypeError("event_estandar_o_none_requerido")


def _digest(valores):
    """Huella técnica de una lista explícita; no codec de objetos o conservación."""
    h = hashlib.sha256()
    for v in valores:
        b = b"N" if v is None else b"S" + str(v).encode("utf-8")
        h.update(len(b).to_bytes(8, "big"))
        h.update(b)
    return h.hexdigest()


class EstadoPublicacion(Enum):
    NO_PUBLICADA = "no_publicada"
    TEMPORAL = "temporal_no_publicado"
    PUBLICADA = "publicada_sin_verificacion_final"
    VERIFICADA = "publicada_y_releida"


@dataclass(frozen=True, slots=True)
class LimitesMaterializacion:
    max_bytes: int = 1_048_576
    tamano_bloque: int = 65_536

    def __post_init__(self):
        _entero(self.max_bytes, 16_777_216)
        _entero(self.tamano_bloque, 1_048_576)
        if not self.max_bytes or not self.tamano_bloque:
            raise ValueError("limite_rc5_debe_ser_positivo")


@dataclass(frozen=True, slots=True)
class SolicitudMaterializacion:
    inventario: InventarioArtefactos = field(repr=False)
    artefacto: ReferenciaArtefacto
    tamano_esperado: int
    sha256_esperado: str | None = None
    limites: LimitesMaterializacion = field(default_factory=LimitesMaterializacion)
    version_contrato: str = VERSION_MATERIALIZACION
    linaje: InformeLinaje = field(init=False, repr=False)

    def __post_init__(self):
        _version(self.version_contrato)
        if type(self.inventario) is not InventarioArtefactos or type(self.artefacto) is not ReferenciaArtefacto or type(self.limites) is not LimitesMaterializacion:
            raise TypeError("contratos_rc4_y_limites_rc5_requeridos")
        _entero(self.tamano_esperado, self.limites.max_bytes)
        if self.sha256_esperado is not None:
            _sha(self.sha256_esperado)
        r = inspeccionar_linaje(self.inventario)
        if r.estado_estructural is E.INCOMPATIBLE:
            raise ValueError("linaje_rc4_contradictorio")
        seleccion = tuple(a for a in r.artefactos if a.descriptor.referencia == self.artefacto)
        if len(seleccion) != 1 or seleccion[0].descriptor.contenido_id is None:
            raise ValueError("artefacto_o_identidad_contenido_no_disponible")
        object.__setattr__(self, "linaje", r)
        e = self.descriptor.entrada_perfil.entrada
        if e.size_bytes_declarado is not None and e.size_bytes_declarado != self.tamano_esperado:
            raise ValueError("tamano_rc5_contradice_descriptor")
        if self.sha256_esperado is not None and e.sha256_declarado is not None and self.sha256_esperado != e.sha256_declarado:
            raise ValueError("hash_rc5_contradice_descriptor")
        comprobado = self.descriptor.size_bytes_comprobado_aportado
        if comprobado is not None and comprobado != self.tamano_esperado:
            raise ValueError("tamano_rc5_contradice_evidencia_aportada")
        comprobado_sha = self.descriptor.sha256_comprobado_aportado
        if self.sha256_esperado is not None and comprobado_sha is not None and self.sha256_esperado != comprobado_sha:
            raise ValueError("hash_rc5_contradice_evidencia_aportada")

    @property
    def resultado_artefacto(self):
        return next(a for a in self.linaje.artefactos if a.descriptor.referencia == self.artefacto)

    @property
    def descriptor(self) -> DescriptorArtefacto:
        return self.resultado_artefacto.descriptor

    @property
    def restricciones(self):
        return self.resultado_artefacto.restricciones

    @property
    def sha_esperado(self):
        e = self.descriptor.entrada_perfil.entrada
        return self.sha256_esperado or e.sha256_declarado or self.descriptor.sha256_comprobado_aportado

    @property
    def huella_vinculo(self):
        a, e = self.descriptor, self.descriptor.entrada_perfil.entrada
        perfil = a.entrada_perfil.perfil
        ps = tuple(p for p in self.inventario.producciones if a.referencia in p.salidas)
        p = ps[0] if ps else None
        valores = ["vinculo-rc5-0.1.0", e.proyecto.project_id, e.proyecto.contexto_id,
            e.entrada_id, e.objeto.object_id, e.revision, e.version_contenido, a.tipo.value,
            a.estado_logico.value, a.contenido_id, a.formato, perfil.identificador, perfil.version,
            e.sha256_declarado, e.size_bytes_declarado, e.asset_id]
        valores.append("sin_recurso" if e.recurso is None else "con_recurso")
        if e.recurso is not None:
            i = e.recurso.identidad
            valores.extend((i.fuente.proveedor, i.fuente.identificador, i.recurso_id, i.producto_id, e.recurso.revision_metadatos))
        valores.append("sin_productora" if p is None else "con_productora")
        if p is not None:
            valores.extend((p.operacion.operacion_id, p.operacion.estado.value, p.ejecucion_id, p.metodo_id, p.metodo_version))
            valores.extend((len(p.entradas), len(p.salidas), len(p.parametros)))
            for r in p.entradas + p.salidas:
                valores.extend((r.object_id, r.revision))
            for par in p.parametros:
                valores.extend(par)
        valores.append(len(self.restricciones))
        for rp in sorted(self.restricciones, key=lambda x: x.restriccion.codigo):
            r = rp.restriccion
            valores.extend((r.codigo, r.tipo.value, r.motivo, len(r.operaciones), *r.operaciones))
        return _digest(valores)


@dataclass(frozen=True, slots=True)
class ReferenciaFisica:
    instancia_id: str
    dispositivo_raiz: int
    inodo_raiz: int
    project_id: str
    artefacto: ReferenciaArtefacto
    contenido_id: str
    huella_vinculo: str
    size_bytes: int
    sha256_recibido: str
    version_contrato: str = VERSION_MATERIALIZACION

    def __post_init__(self):
        _version(self.version_contrato)
        if type(self.instancia_id) is not str or not re.fullmatch(r"[0-9a-f]{32}", self.instancia_id):
            raise ValueError("instancia_rc5_no_admitida")
        for v in (self.project_id, self.contenido_id):
            if type(v) is not str or not v.strip() or len(v) > 512 or any(ord(c) < 32 for c in v):
                raise ValueError("identidad_rc5_no_admitida")
        if type(self.artefacto) is not ReferenciaArtefacto:
            raise TypeError("referencia_rc4_requerida")
        for v in (self.dispositivo_raiz, self.inodo_raiz):
            _entero(v, 2**256)
        _entero(self.size_bytes, 16_777_216)
        _sha(self.huella_vinculo)
        _sha(self.sha256_recibido)

    @property
    def nombre(self):
        # No deduplicar por contenido ni incorporar literales como rutas.
        return "a-" + _digest(("destino-rc5", self.project_id, self.artefacto.object_id, self.artefacto.revision)) + ".bin"


@dataclass(frozen=True, slots=True)
class InformeVerificacion:
    solicitud: SolicitudMaterializacion = field(repr=False)
    referencia: ReferenciaFisica
    fecha_utc: datetime
    estado_local: EstadoLocal
    bytes_leidos: int
    size_bytes_observado: int | None
    sha256_fisico: str | None
    lectura_completa: bool
    diagnosticos: tuple[D, ...]
    version_contrato: str = field(default=VERSION_MATERIALIZACION, init=False)
    autenticidad_acreditada: bool = field(default=False, init=False)
    custodia_independiente: bool = field(default=False, init=False)

    @property
    def integridad(self):
        return {EstadoLocal.INTEGRO: EstadoIntegridad.VERIFICADA,
                EstadoLocal.INCONSISTENTE: EstadoIntegridad.FALLIDA}.get(self.estado_local, EstadoIntegridad.PENDIENTE)

    @property
    def restricciones(self):
        return self.solicitud.restricciones

    @property
    def autoriza_operacion(self):
        return False

    def __bool__(self):
        raise TypeError("integridad_fisica_no_es_permiso_o_validez_cientifica")


@dataclass(frozen=True, slots=True)
class InformeMaterializacion:
    solicitud: SolicitudMaterializacion = field(repr=False)
    fecha_utc: datetime
    estado_tecnico: S
    publicacion: EstadoPublicacion
    bytes_recibidos: int
    bytes_escritos: int
    sha256_recibido: str | None
    sha256_temporal: str | None
    referencia: ReferenciaFisica | None
    verificacion: InformeVerificacion | None
    temporales: tuple[str, ...]
    diagnosticos: tuple[D, ...]
    version_contrato: str = field(default=VERSION_MATERIALIZACION, init=False)
    productor_ejecutado: bool = field(default=False, init=False)
    persistencia_durable: bool = field(default=False, init=False)

    @property
    def restricciones(self):
        return self.solicitud.restricciones

    @property
    def autoriza_operacion(self):
        return False

    def __bool__(self):
        raise TypeError("publicacion_tecnica_no_es_permiso_o_validez_cientifica")


def _bloqueada(s, uso):
    return any(r.restriccion.tipo is TipoRestriccionQA.BLOQUEO_USO_DEL_RESULTADO
               and uso in r.restriccion.operaciones for r in s.restricciones)


def _referencia(s, fs, sha):
    return ReferenciaFisica(fs.instancia_id, *fs.identidad_raiz, s.descriptor.entrada_perfil.entrada.proyecto.project_id,
        s.artefacto, s.descriptor.contenido_id, s.huella_vinculo, s.tamano_esperado, sha)


def _verificar(s, r, evento, propietario=None):
    _evento(evento)
    if type(s) is not SolicitudMaterializacion or type(r) is not ReferenciaFisica:
        raise TypeError("solicitud_y_referencia_rc5_requeridas")
    estado, leidos, observado, sha, completa = EstadoLocal.NO_DISPONIBLE, 0, None, None, False
    try:
        if (r.artefacto != s.artefacto or r.project_id != s.descriptor.entrada_perfil.entrada.proyecto.project_id
                or r.contenido_id != s.descriptor.contenido_id or r.huella_vinculo != s.huella_vinculo
                or r.size_bytes != s.tamano_esperado or s.sha_esperado is not None and r.sha256_recibido != s.sha_esperado):
            raise ErrorArchivoExperimental("referencia_no_corresponde_a_descriptor")
        if _bloqueada(s, USO_VERIFICAR):
            raise ErrorArchivoExperimental("restriccion_impide_verificacion")
        controlar(evento)
        fs = ArchivosTEMP(r.instancia_id, (r.dispositivo_raiz, r.inodo_raiz))
        lock = fs.ruta("escritor.lock")
        if os.path.lexists(lock):
            if propietario is None or propietario.creados.get("escritor.lock") != (lock.stat().st_dev, lock.stat().st_ino):
                raise ErrorArchivoExperimental("escritor_o_interrupcion_pendiente")
        _, st = fs.regular(r.nombre)
        observado = st.st_size
        if observado != r.size_bytes:
            estado = EstadoLocal.INCONSISTENTE
            codigo = "tamano_fisico_incorrecto"
        else:
            leidos, sha = fs.leer(r.nombre, s.limites.max_bytes, s.limites.tamano_bloque, evento)
            completa = True
            estado = EstadoLocal.INTEGRO if sha == r.sha256_recibido else EstadoLocal.INCONSISTENTE
            codigo = "contenido_fisico_coincidente" if estado is EstadoLocal.INTEGRO else "hash_fisico_incorrecto"
    except FileNotFoundError:
        estado, codigo = EstadoLocal.AUSENTE, "archivo_o_raiz_ausente"
    except ErrorArchivoExperimental as e:
        codigo, leidos = e.codigo, getattr(e, "bytes_leidos", 0)
    except OSError as e:
        codigo, leidos = "lectura_fisica_no_disponible", getattr(e, "bytes_leidos", 0)
    return InformeVerificacion(s, r, datetime.now(timezone.utc), estado, leidos, observado, sha, completa,
        (_diagnostico(codigo, N.INFORMACION if estado is EstadoLocal.INTEGRO else N.CONTRADICCION if estado is EstadoLocal.INCONSISTENTE else N.FALTANTE),))


def verificar_fisicamente(solicitud, referencia, *, cancelacion=None):
    """Raíz derivada del ID TEMP; no acepta rutas históricas o destinos del llamador."""
    return _verificar(solicitud, referencia, cancelacion)


class _FuenteSintetica:
    def __init__(self, bloques, archivo, s, evento, escribir, punto):
        self.bloques = iter(bloques)
        self.archivo, self.s, self.evento, self.escribir, self.punto = archivo, s, evento, escribir, punto
        self.recibidos = self.escritos = 0
        self.fin = False

    def read(self, n):
        controlar(self.evento)
        try:
            b = next(self.bloques)
        except StopIteration:
            self.fin = True
            return b""
        except Exception:
            raise ErrorArchivoExperimental("fuente_sintetica_interrumpida") from None
        if type(b) is not bytes or not b or len(b) > n:
            raise ErrorArchivoExperimental("bloque_sintetico_no_admitido")
        self.recibidos += len(b)
        if self.recibidos > self.s.limites.max_bytes:
            raise ErrorArchivoExperimental("limite_entrada_excedido")
        escritos = self.escribir(self.archivo, b)
        if type(escritos) is int and 0 <= escritos <= len(b):
            self.escritos += escritos
        if escritos != len(b):
            raise ErrorArchivoExperimental("escritura_incompleta")
        self.punto("bloque_escrito")
        return b


class MaterializadorExperimental:
    """Usar mediante entorno_materializacion; un escritor cooperativo, sin reintentos."""

    def __init__(self, archivos):
        if type(archivos) is not ArchivosTEMP:
            raise TypeError("entorno_temp_rc5_requerido")
        self._archivos = archivos
        self._contenidos = {}

    @property
    def raiz(self):
        return self._archivos.raiz

    def _punto(self, nombre):
        """Frontera inerte de inyección de fallos; no configurable desde documentos."""

    def _escribir(self, archivo, bloque):
        return archivo.write(bloque)

    def materializar_sintetico(self, solicitud, bloques, *, cancelacion=None):
        if type(solicitud) is not SolicitudMaterializacion:
            raise TypeError("solicitud_rc5_requerida")
        _evento(cancelacion)
        s, fs = solicitud, self._archivos
        publicacion, estado = EstadoPublicacion.NO_PUBLICADA, S.FALLIDA
        fuente = temporal = referencia = verificacion = recibido = releido = None
        ds, lock = [], False
        interrupcion = None
        try:
            if _bloqueada(s, USO_MATERIALIZAR):
                raise ErrorArchivoExperimental("restriccion_impide_materializacion")
            if _bloqueada(s, USO_VERIFICAR):
                raise ErrorArchivoExperimental("restriccion_impide_verificacion")
            controlar(cancelacion)
            with fs.abrir_nuevo("escritor.lock") as f:
                lock = True
                if f.write(b"RC5\n") != 4:
                    raise ErrorArchivoExperimental("escritura_marcador_incompleta")
            prevista = _referencia(s, fs, s.sha_esperado or "0" * 64)
            destino = fs.ruta(prevista.nombre)
            if os.path.lexists(destino):
                raise ErrorArchivoExperimental("destino_ocupado")
            temporal = "t-" + uuid4().hex + ".tmp"
            with fs.abrir_nuevo(temporal) as f:
                publicacion = EstadoPublicacion.TEMPORAL
                self._punto("temporal_creado")
                fuente = _FuenteSintetica(bloques, f, s, cancelacion, self._escribir, self._punto)
                total, recibido = huella(fuente, s.limites.tamano_bloque, s.limites.max_bytes)
                f.flush()
                os.fsync(f.fileno())
            self._punto("temporal_cerrado")
            if total != s.tamano_esperado:
                raise ErrorArchivoExperimental("tamano_recibido_incorrecto")
            if s.sha_esperado is not None and recibido != s.sha_esperado:
                raise ErrorArchivoExperimental("hash_recibido_incorrecto")
            for a in s.inventario.artefactos:
                if a.contenido_id == s.descriptor.contenido_id:
                    e = a.entrada_perfil.entrada
                    if (any(v is not None and v != recibido for v in (e.sha256_declarado, a.sha256_comprobado_aportado))
                            or any(v is not None and v != total for v in (e.size_bytes_declarado, a.size_bytes_comprobado_aportado))):
                        raise ErrorArchivoExperimental("contenido_contradice_identidad_compartida")
            anterior = self._contenidos.get(s.descriptor.contenido_id)
            if anterior is not None and anterior != (total, recibido):
                raise ErrorArchivoExperimental("contenido_contradice_publicacion_anterior")
            tamano, releido = fs.leer(temporal, s.limites.max_bytes, s.limites.tamano_bloque, cancelacion)
            if (tamano, releido) != (total, recibido):
                raise ErrorArchivoExperimental("temporal_fisico_no_coincidente")
            _, verificado = fs.regular(temporal)
            self._punto("antes_publicacion")
            controlar(cancelacion)
            fs.validar()
            _, actual = fs.regular(temporal)
            if firma(actual) != firma(verificado) or fs.creados.get(temporal) != (actual.st_dev, actual.st_ino):
                raise ErrorArchivoExperimental("temporal_cambio_antes_de_publicacion")
            os.link(fs.ruta(temporal), fs.ruta(prevista.nombre))
            fs.registrar(prevista.nombre, fs.ruta(prevista.nombre).lstat())
            referencia = _referencia(s, fs, recibido)
            publicacion = EstadoPublicacion.PUBLICADA
            self._punto("enlace_publicado")
            fs.quitar_propio(temporal)
            temporal = None
            self._contenidos[s.descriptor.contenido_id] = (total, recibido)
            self._punto("antes_relectura_final")
            verificacion = _verificar(s, referencia, cancelacion, propietario=fs)
            if verificacion.estado_local is not EstadoLocal.INTEGRO:
                if any(d.codigo == "cancelacion_observada" for d in verificacion.diagnosticos):
                    raise ErrorArchivoExperimental("cancelacion_observada")
                raise ErrorArchivoExperimental("publicacion_sin_verificacion_final")
            publicacion, estado = EstadoPublicacion.VERIFICADA, S.CONCLUIDA
            ds.append(_diagnostico("bytes_sinteticos_publicados_y_releidos", N.INFORMACION))
        except BaseException as e:
            codigo = e.codigo if isinstance(e, ErrorArchivoExperimental) else "destino_ocupado" if isinstance(e, FileExistsError) else "error_escritura_o_publicacion" if isinstance(e, OSError) else "interrupcion_o_fuente_no_admitida"
            estado = S.CANCELADA if codigo == "cancelacion_observada" else S.PARCIAL if referencia is not None or fuente is not None and fuente.escritos > 0 and not fuente.fin else S.FALLIDA
            ds.append(_diagnostico(codigo, N.FALTANTE if estado is S.CANCELADA else N.CONTRADICCION))
            if not isinstance(e, Exception):
                interrupcion = e
        finally:
            if lock:
                try:
                    fs.quitar_propio("escritor.lock")
                except (OSError, ErrorArchivoExperimental):
                    ds.append(_diagnostico("marcador_escritor_requiere_revision"))
                    if estado is S.CONCLUIDA:
                        estado = S.PARCIAL
        informe = InformeMaterializacion(s, datetime.now(timezone.utc), estado, publicacion,
            0 if fuente is None else fuente.recibidos, 0 if fuente is None else fuente.escritos,
            recibido, releido, referencia, verificacion, () if temporal is None else (temporal,), tuple(ds))
        if interrupcion is not None:
            interrupcion.informe_rc5 = informe
            raise interrupcion
        return informe


@contextmanager
def entorno_materializacion():
    """Crea solo TEMP privado; al salir retira únicamente archivos propios, sin recursión."""
    try:
        fs = ArchivosTEMP.crear()
    except OSError:
        raise ErrorArchivoExperimental("entorno_temporal_no_creado") from None
    try:
        yield MaterializadorExperimental(fs)
    except BaseException as e:
        try:
            fs.limpiar()
        except (OSError, ErrorArchivoExperimental):
            e.add_note("limpieza_temporal_rc5_requiere_revision")
        raise
    else:
        try:
            fs.limpiar()
        except OSError:
            raise ErrorArchivoExperimental("limpieza_temporal_requiere_revision") from None


__all__ = ("VERSION_MATERIALIZACION", "USO_MATERIALIZAR", "USO_VERIFICAR", "EstadoPublicacion",
    "LimitesMaterializacion", "SolicitudMaterializacion", "ReferenciaFisica", "InformeVerificacion",
    "InformeMaterializacion", "MaterializadorExperimental", "entorno_materializacion", "verificar_fisicamente")
