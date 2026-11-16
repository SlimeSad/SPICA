"""Generaciones RC6 autocontenidas y acotadas, exclusivamente sintéticas/TEMP.

No catálogo SQL, permisos, ejecución de productores ni restauración de RAW.
"""

from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import hashlib
import io
import os
import re
from threading import Event
from uuid import uuid4

from ..adquisicion.readquisicion.modelos import EstadoLocal
from ..calidad.restricciones import TipoRestriccionQA
from ..contextos import EstadoOperacion, TipoOperacion
from ..interoperabilidad.modelos import EstadoAptitud
from . import InformeLinaje, InventarioArtefactos, ReferenciaArtefacto, inspeccionar_linaje
from .materializacion import InformeMaterializacion, EstadoPublicacion, verificar_fisicamente
from ._archivos_rc5 import ArchivosTEMP, ErrorArchivoExperimental, controlar, firma
from ._generacion_rc6 import (
    ArchivosGeneracion, BLOQUE, MAX_ARCHIVO, MAX_TOTAL, leer_metadatos, publicar, transferir,
)
from . import _codec_rc6 as codec

VERSION_CONSERVACION = codec.VERSION
USO_CONSERVAR = "conservar_sintetico_rc6"
USO_RECUPERAR = "recuperar_sintetico_rc6"


class ErrorConservacion(ValueError):
    def __init__(self, codigo):
        self.codigo = codigo
        super().__init__(codigo)


def _exigir(condicion, codigo):
    if not condicion:
        raise ErrorConservacion(codigo)


def _sha(b):
    return hashlib.sha256(b).hexdigest()


def _resumen(linaje):
    return (linaje.diagnosticos, linaje.orden_linaje, tuple((a.descriptor.referencia,
        a.diagnosticos, a.restricciones_locales, a.restricciones_heredadas) for a in linaje.artefactos))


def _evento(e):
    _exigir(e is None or type(e) is Event, "evento_estandar_requerido")


def _fecha(f):
    return type(f) is datetime and f.utcoffset() is not None and f.utcoffset().total_seconds() == 0


def _bloqueo(linaje, uso):
    return any(r.restriccion.tipo is TipoRestriccionQA.BLOQUEO_USO_DEL_RESULTADO
        and uso in r.restriccion.operaciones for a in linaje.artefactos for r in a.restricciones)


@dataclass(frozen=True, slots=True)
class UnidadConservacion:
    inventario: InventarioArtefactos = field(repr=False)
    materializaciones: tuple[InformeMaterializacion, ...] = field(default=(), repr=False)
    externos: tuple[ReferenciaArtefacto, ...] = ()
    _linaje: InformeLinaje = field(init=False, repr=False)

    def __post_init__(self):
        _exigir(type(self.inventario) is InventarioArtefactos
            and 0 < len(self.inventario.artefactos) <= 16, "inventario_rc6_no_admitido")
        _exigir(type(self.materializaciones) is tuple and len(self.materializaciones) <= 16
            and all(type(r) is InformeMaterializacion for r in self.materializaciones), "informes_rc5_requeridos")
        _exigir(type(self.externos) is tuple and len(self.externos) <= 16
            and all(type(r) is ReferenciaArtefacto for r in self.externos), "referencias_externas_tipificadas")
        linaje = inspeccionar_linaje(self.inventario)
        object.__setattr__(self, "_linaje", linaje)
        _exigir(linaje.estado_estructural is not EstadoAptitud.INCOMPATIBLE, "linaje_rc6_contradictorio")
        # Perfil mínimo: descripciones RC1–RC3 completas; cierres QA y sus registros
        # quedan fuera del codec, sin fingir recuperación de lo que no se conserva.
        ops = [p.operacion for p in self.inventario.producciones]
        for c in self.inventario.composiciones:
            for n in c.operaciones:
                _exigir(n.cierre_qa is None, "cierre_qa_fuera_del_perfil_rc6")
                ops.append(n.contexto)
        _exigir(all(o.tipo is TipoOperacion.DESCRIPCION_ESTRUCTURAL for o in ops), "operacion_fuera_del_perfil_rc6")
        refs = {a.referencia for a in self.inventario.artefactos}
        externas = set(self.externos)
        _exigir(len(externas) == len(self.externos) and externas <= refs, "externos_duplicados_o_inexistentes")
        informes, contenidos = set(), {}
        for r in self.materializaciones:
            s = r.solicitud
            _exigir(s.inventario is self.inventario and s.artefacto in refs
                and s.artefacto not in informes, "informe_de_otro_inventario_o_duplicado")
            informes.add(s.artefacto)
            _exigir(_fecha(r.fecha_utc) and type(r.estado_tecnico) is EstadoOperacion
                and type(r.publicacion) is EstadoPublicacion, "estado_historico_rc5_invalido")
            _exigir(type(r.bytes_recibidos) is int and type(r.bytes_escritos) is int
                and 0 <= r.bytes_escritos <= s.limites.max_bytes
                and r.bytes_escritos <= r.bytes_recibidos <= s.limites.max_bytes + s.limites.tamano_bloque,
                "contadores_historicos_invalidos")
            _exigir(not r.productor_ejecutado and not r.persistencia_durable, "promocion_historica_invalida")
            _exigir(_resumen(s.linaje) == _resumen(linaje), "restricciones_o_linaje_historico_discrepantes")
            if r.referencia is not None:
                ref = r.referencia
                _exigir(ref.artefacto == s.artefacto and ref.contenido_id == s.descriptor.contenido_id
                    and ref.project_id == s.descriptor.entrada_perfil.entrada.proyecto.project_id
                    and ref.huella_vinculo == s.huella_vinculo and ref.size_bytes == s.tamano_esperado,
                    "referencia_historica_contradictoria")
            if r.verificacion is not None:
                _exigir(r.verificacion.solicitud is s and r.verificacion.referencia == r.referencia
                    and _fecha(r.verificacion.fecha_utc), "verificacion_historica_de_otro_recurso")
            if r.estado_tecnico is EstadoOperacion.CONCLUIDA or s.artefacto not in externas:
                self._incluible(r)
            if s.artefacto not in externas:
                clave = s.descriptor.contenido_id
                valores = r.bytes_escritos, r.sha256_recibido
                _exigir(clave not in contenidos or contenidos[clave] == valores,
                    "identidad_contenido_fisico_contradictoria")
                contenidos[clave] = valores
        _exigir(informes | externas == refs, "inventario_sin_cobertura_explicita")
        for a in self.inventario.artefactos:
            if a.contenido_id not in contenidos:
                continue
            n, sha = contenidos[a.contenido_id]
            e = a.entrada_perfil.entrada
            _exigir(all(x is None or x == n for x in (e.size_bytes_declarado, a.size_bytes_comprobado_aportado))
                and all(x is None or x == sha for x in (e.sha256_declarado, a.sha256_comprobado_aportado)),
                "contenido_fisico_contradice_descriptores")
        _exigir(sum(r.bytes_escritos for r in self.incluidos) <= MAX_TOTAL, "limite_total_rc6")

    @staticmethod
    def _incluible(r):
        s, ref, v = r.solicitud, r.referencia, r.verificacion
        _exigir(r.estado_tecnico is EstadoOperacion.CONCLUIDA
            and r.publicacion is EstadoPublicacion.VERIFICADA and ref is not None and v is not None
            and r.temporales == (), "materializacion_sin_cierre_acreditado")
        _exigir(v.solicitud is s and v.referencia == ref and _fecha(v.fecha_utc)
            and v.estado_local is EstadoLocal.INTEGRO and v.lectura_completa is True
            and not v.autenticidad_acreditada and not v.custodia_independiente,
            "evidencia_rc5_historica_incoherente")
        _exigir(ref.project_id == s.descriptor.entrada_perfil.entrada.proyecto.project_id
            and ref.artefacto == s.artefacto and ref.contenido_id == s.descriptor.contenido_id
            and ref.huella_vinculo == s.huella_vinculo, "referencia_rc5_incoherente")
        _exigir(ref.size_bytes == r.bytes_recibidos == r.bytes_escritos == s.tamano_esperado
            == v.bytes_leidos == v.size_bytes_observado
            and ref.sha256_recibido == r.sha256_recibido == r.sha256_temporal == v.sha256_fisico
            and (s.sha_esperado is None or s.sha_esperado == ref.sha256_recibido), "huellas_historicas_contradictorias")

    @property
    def incluidos(self):
        return tuple(r for r in self.materializaciones if r.solicitud.artefacto not in self.externos)

    @property
    def linaje(self):
        return self._linaje


@dataclass(frozen=True, slots=True)
class ControlGeneracion:
    generacion_id: str
    manifiesto_sha256: str

    def __post_init__(self):
        _exigir(type(self.generacion_id) is str and re.fullmatch(r"[0-9a-f]{32}", self.generacion_id), "identidad_generacion_invalida")
        _exigir(type(self.manifiesto_sha256) is str and re.fullmatch(r"[0-9a-f]{64}", self.manifiesto_sha256), "huella_control_invalida")


class EstadoRecuperacion(Enum):
    VERIFICADA = "cerrada_verificada_en_alcance"
    INCOMPLETA = "incompleta"
    CORRUPTA = "corrupcion_comprobada"
    INCOMPATIBLE = "contrato_o_relaciones_incompatibles"
    NO_DISPONIBLE = "revision_necesaria"


@dataclass(frozen=True, slots=True)
class ComprobacionContenido:
    artefacto: ReferenciaArtefacto
    contenido_id: str | None
    relativa: str | None
    estado_actual: EstadoLocal
    size_bytes: int | None
    sha256_fisico: str | None
    lectura_completa: bool


@dataclass(frozen=True, slots=True)
class RecuperacionGeneracion:
    estado: EstadoRecuperacion
    fecha_utc: datetime
    control: ControlGeneracion
    unidad: UnidadConservacion | None = field(default=None, repr=False)
    contenidos: tuple[ComprobacionContenido, ...] = ()
    diagnosticos: tuple[str, ...] = ()
    version_contrato: str = field(default=VERSION_CONSERVACION, init=False)
    autenticidad_acreditada: bool = field(default=False, init=False)
    custodia_independiente: bool = field(default=False, init=False)
    persistencia_durable: bool = field(default=False, init=False)

    @property
    def autoriza_operacion(self):
        return False

    def __bool__(self):
        raise TypeError("recuperacion_no_es_permiso_ni_revision_cientifica")


def _cuerpo(u):
    return codec.codificar((u.inventario, u.materializaciones, u.externos, _resumen(u.linaje)))


def _unidad(b):
    v = codec.decodificar(b)
    _exigir(type(v) is tuple and len(v) == 4, "envolvente_unidad_invalida")
    u = UnidadConservacion(*v[:3])
    _exigir(_resumen(u.linaje) == v[3], "clausura_linaje_o_restricciones_discrepante")
    return u


def _inventario_fisico(u):
    return [dict(artefacto=[r.solicitud.artefacto.object_id, r.solicitud.artefacto.revision],
        contenido_id=r.solicitud.descriptor.contenido_id, relativa=f"datos-{i:03}.bin",
        size_bytes=r.bytes_escritos, sha256=r.sha256_recibido) for i, r in enumerate(u.incluidos)]


def recuperar_generacion(raiz, control, *, cancelacion=None):
    """Lectura física desde raíz actual: jamás busca una ruta RC5 histórica."""
    _exigir(type(control) is ControlGeneracion, "control_tipificado_requerido")
    _evento(cancelacion)
    estado, ds, contenidos, u = EstadoRecuperacion.NO_DISPONIBLE, [], [], None
    try:
        controlar(cancelacion)
        fs = ArchivosGeneracion.abrir(raiz)
        nombres = fs.nombres()
        _exigir("escritor.lock" not in nombres and not any(n.endswith(".tmp") for n in nombres), "generacion_sin_cierre_o_con_temporales")
        for n in ("intencion.json", "manifiesto.json", "metadatos.json", "cierre.json"):
            if n not in nombres:
                raise FileNotFoundError
        mb, _, mh = leer_metadatos(fs, "manifiesto.json", codec.MAX_METADATOS)
        m = codec.leer_json(mb)
        _exigir(type(m) is dict and set(m) == {"version", "generacion_id", "fecha_utc", "estado", "metadatos", "archivos", "externos"}, "campos_manifiesto_incompatibles")
        _exigir(m["version"] == VERSION_CONSERVACION, "version_generacion_incompatible")
        _exigir(mb == codec.canonico(m) and mh == control.manifiesto_sha256
            and m["generacion_id"] == control.generacion_id, "control_generacion_discrepante")
        _exigir(m["estado"] == "cerrada_en_alcance" and _fecha(datetime.fromisoformat(m["fecha_utc"])), "estado_manifiesto_invalido")
        ib, _, _ = leer_metadatos(fs, "intencion.json", codec.MAX_METADATOS)
        cb, _, _ = leer_metadatos(fs, "cierre.json", codec.MAX_METADATOS)
        _exigir(ib == codec.canonico(dict(version=VERSION_CONSERVACION, generacion_id=control.generacion_id, fecha_utc=m["fecha_utc"], estado="preparada")), "intencion_incompatible")
        _exigir(cb == codec.canonico(dict(version=VERSION_CONSERVACION, generacion_id=control.generacion_id,
            manifiesto_sha256=mh, estado="cerrada_en_alcance")), "sello_cierre_incompatible")
        b, n, sha = leer_metadatos(fs, "metadatos.json", codec.MAX_METADATOS)
        _exigir(codec.canonico(m["metadatos"]) == codec.canonico(dict(size_bytes=n, sha256=sha)), "hash_metadatos_discrepante")
        u = _unidad(b)
        _exigir(not _bloqueo(u.linaje, USO_RECUPERAR), "restriccion_impide_recuperacion")
        esperado = _inventario_fisico(u)
        _exigir(codec.canonico(m["archivos"]) == codec.canonico(esperado) and m["externos"] == [
            [r.object_id, r.revision] for r in u.externos], "inventario_manifiesto_discrepante")
        requeridos = {"intencion.json", "manifiesto.json", "metadatos.json", "cierre.json"} | {a["relativa"] for a in esperado}
        _exigir(set(nombres) <= requeridos, "archivos_ajenos_a_generacion")
        firmas_contenidos = {}
        for a, r in zip(esperado, u.incluidos):
            nombre = a["relativa"]  # Generado localmente, nunca una ruta del JSON.
            try:
                _, st = fs.regular(nombre)
                if st.st_size != a["size_bytes"]:
                    contenidos.append(ComprobacionContenido(r.solicitud.artefacto,
                        a["contenido_id"], nombre, EstadoLocal.INCONSISTENTE, st.st_size, None, False))
                    ds.append("tamano_copia_incorrecto")
                    continue
                n, sha = fs.leer(nombre, MAX_ARCHIVO, BLOQUE, cancelacion)
                _, despues = fs.regular(nombre)
                _exigir(firma(st) == firma(despues), "contenido_cambio_durante_recuperacion")
                firmas_contenidos[nombre] = firma(despues)
                coincide = sha == a["sha256"]
                contenidos.append(ComprobacionContenido(r.solicitud.artefacto, a["contenido_id"],
                    nombre, EstadoLocal.INTEGRO if coincide else EstadoLocal.INCONSISTENTE, n, sha, True))
                if not coincide:
                    ds.append("hash_copia_incorrecto")
            except FileNotFoundError:
                contenidos.append(ComprobacionContenido(r.solicitud.artefacto,
                    a["contenido_id"], nombre, EstadoLocal.AUSENTE, None, None, False))
                ds.append("contenido_incluido_ausente")
        for ref in u.externos:
            d = next(a for a in u.inventario.artefactos if a.referencia == ref)
            contenidos.append(ComprobacionContenido(ref, d.contenido_id, None,
                EstadoLocal.NO_DISPONIBLE, None, None, False))
        controlar(cancelacion)
        _exigir(nombres == fs.nombres() and not os.path.lexists(fs.ruta("escritor.lock")), "generacion_cambio_durante_recuperacion")
        # Releer los metadatos/cierre detecta cambios observados en la ventana.
        for nombre, original in (("manifiesto.json", mb), ("metadatos.json", b), ("cierre.json", cb), ("intencion.json", ib)):
            _exigir(leer_metadatos(fs, nombre, codec.MAX_METADATOS)[0] == original, "metadatos_cambiaron_durante_recuperacion")
        for nombre, original in firmas_contenidos.items():
            _exigir(firma(fs.regular(nombre)[1]) == original, "contenido_cambio_antes_cierre_lectura")
        estado = (EstadoRecuperacion.CORRUPTA if any(c.estado_actual is EstadoLocal.INCONSISTENTE for c in contenidos)
            else EstadoRecuperacion.INCOMPLETA if ds else EstadoRecuperacion.VERIFICADA)
    except FileNotFoundError:
        estado, ds = EstadoRecuperacion.INCOMPLETA, ds + ["raiz_o_metadatos_ausentes"]
    except ErrorConservacion as e:
        estado = EstadoRecuperacion.INCOMPLETA if e.codigo == "generacion_sin_cierre_o_con_temporales" else EstadoRecuperacion.INCOMPATIBLE
        ds.append(e.codigo)
    except ErrorArchivoExperimental as e:
        ds.append(e.codigo)
    except OSError:
        ds.append("lectura_generacion_no_disponible")
    except (ValueError, TypeError, KeyError, AttributeError, ArithmeticError, RecursionError):
        estado, ds = EstadoRecuperacion.INCOMPATIBLE, ds + ["metadatos_fuera_del_contrato_rc6"]
    return RecuperacionGeneracion(estado, datetime.now(timezone.utc), control, u,
        tuple(contenidos), tuple(ds))


class ConservadorExperimental:
    def __init__(self, archivos):
        _exigir(type(archivos) is ArchivosGeneracion, "entorno_rc6_requerido")
        self._fs = archivos

    @property
    def raiz(self):
        return self._fs.raiz

    def _punto(self, nombre):
        """Punto inerte para inyección de fallos controlados en pruebas."""

    def _bytes(self, nombre, b, evento):
        def fuente(f):
            return transferir_memoria(b, f, evento)
        return publicar(self._fs, nombre, fuente, codec.MAX_METADATOS, evento, self._punto)

    def _iniciar(self):
        _exigir(self._fs.nombres() == (), "raiz_destino_ocupada")
        with self._fs.abrir_nuevo("escritor.lock") as f:
            _exigir(f.write(b"RC6\n") == 4, "escritura_marcador_incompleta")
            f.flush()
            os.fsync(f.fileno())

    def conservar(self, unidad, *, cancelacion=None):
        _exigir(type(unidad) is UnidadConservacion, "unidad_tipificada_requerida")
        _evento(cancelacion)
        try:
            controlar(cancelacion)
            _exigir(not _bloqueo(unidad.linaje, USO_CONSERVAR)
                and not _bloqueo(unidad.linaje, USO_RECUPERAR), "restriccion_impide_conservacion")
            b = _cuerpo(unidad)  # Perfil/tamaño se verifican antes de escribir.
            identidad, fecha = uuid4().hex, datetime.now(timezone.utc).isoformat()
            self._iniciar()
            self._bytes("intencion.json", codec.canonico(dict(version=VERSION_CONSERVACION,
                generacion_id=identidad, fecha_utc=fecha, estado="preparada")), cancelacion)
            self._punto("intencion")
            for i, r in enumerate(unidad.incluidos):
                v = verificar_fisicamente(r.solicitud, r.referencia, cancelacion=cancelacion)
                _exigir(v.estado_local is EstadoLocal.INTEGRO and v.lectura_completa, "origen_rc5_no_verificable")
                ref = r.referencia
                fs = ArchivosTEMP(ref.instancia_id, (ref.dispositivo_raiz, ref.inodo_raiz))
                def fuente(f, fs=fs, ref=ref):
                    _exigir(not os.path.lexists(fs.ruta("escritor.lock")), "escritor_rc5_pendiente")
                    n, sha = transferir(fs, ref.nombre, MAX_ARCHIVO, cancelacion, f)
                    _exigir((n, sha) == (ref.size_bytes, ref.sha256_recibido), "origen_cambio_durante_conservacion")
                    _exigir(not os.path.lexists(fs.ruta("escritor.lock")), "escritor_rc5_pendiente")
                    return n, sha
                publicar(self._fs, f"datos-{i:03}.bin", fuente, MAX_ARCHIVO, cancelacion, self._punto)
            self._bytes("metadatos.json", b, cancelacion)
            m = dict(version=VERSION_CONSERVACION, generacion_id=identidad, fecha_utc=fecha,
                estado="cerrada_en_alcance", metadatos=dict(size_bytes=len(b), sha256=_sha(b)),
                archivos=_inventario_fisico(unidad), externos=[[r.object_id, r.revision] for r in unidad.externos])
            mb = codec.canonico(m)
            control = ControlGeneracion(identidad, _sha(mb))
            self._bytes("manifiesto.json", mb, cancelacion)
            self._punto("antes_cierre")
            self._bytes("cierre.json", codec.canonico(dict(version=VERSION_CONSERVACION,
                generacion_id=identidad, manifiesto_sha256=control.manifiesto_sha256, estado="cerrada_en_alcance")), cancelacion)
            self._punto("cierre")
            self._fs.quitar_propio("escritor.lock")
            resultado = recuperar_generacion(self.raiz, control, cancelacion=cancelacion)
            _exigir(resultado.estado is EstadoRecuperacion.VERIFICADA, "generacion_final_no_verificable")
            return resultado
        except (ErrorConservacion, KeyboardInterrupt, SystemExit):
            raise
        except ErrorArchivoExperimental as e:
            raise ErrorConservacion(e.codigo) from None
        except OSError:
            raise ErrorConservacion("escritura_generacion_no_disponible") from None
        except (ValueError, TypeError, AttributeError, RecursionError):
            raise ErrorConservacion("perfil_conservacion_rc6_no_admitido") from None

    def copiar_de(self, origen, control, *, cancelacion=None):
        """Copia autocontenida a esta raíz nueva; no restaura ubicaciones históricas."""
        _evento(cancelacion)
        try:
            controlar(cancelacion)
            r = recuperar_generacion(origen, control, cancelacion=cancelacion)
            _exigir(r.estado is EstadoRecuperacion.VERIFICADA, "origen_generacion_no_verificable")
            fs = ArchivosGeneracion.abrir(origen)
            self._iniciar()
            nombres = fs.nombres()
            # Sello siempre último. Una interrupción conserva la copia sin cierre.
            for nombre in sorted(nombres, key=lambda n: (n == "cierre.json", n)):
                def fuente(f, nombre=nombre):
                    return transferir(fs, nombre, MAX_ARCHIVO if nombre.endswith(".bin") else codec.MAX_METADATOS, cancelacion, f)
                publicar(self._fs, nombre, fuente, MAX_ARCHIVO, cancelacion, self._punto)
            _exigir(nombres == fs.nombres() and recuperar_generacion(origen, control,
                cancelacion=cancelacion).estado is EstadoRecuperacion.VERIFICADA, "origen_cambio_durante_traslado")
            self._fs.quitar_propio("escritor.lock")
            final = recuperar_generacion(self.raiz, control, cancelacion=cancelacion)
            _exigir(final.estado is EstadoRecuperacion.VERIFICADA, "traslado_no_verificable")
            return final
        except (ErrorConservacion, KeyboardInterrupt, SystemExit):
            raise
        except ErrorArchivoExperimental as e:
            raise ErrorConservacion(e.codigo) from None
        except OSError:
            raise ErrorConservacion("copia_generacion_no_disponible") from None


def transferir_memoria(b, f, evento):
    # Solo metadatos acotados; los contenidos usan transferir() sobre disco.
    h = hashlib.sha256()
    with io.BytesIO(b) as fuente:
        while True:
            controlar(evento)
            bloque = fuente.read(BLOQUE)
            if not bloque:
                break
            _exigir(f.write(bloque) == len(bloque), "escritura_corta_metadatos")
            h.update(bloque)
    return len(b), h.hexdigest()


@contextmanager
def entorno_conservacion(*, disponer_al_salir=True):
    """Propiedad y disposición de fixtures; no es retención operativa permanente."""
    _exigir(type(disponer_al_salir) is bool, "politica_disposicion_invalida")
    try:
        fs = ArchivosGeneracion.crear()
    except (OSError, ErrorArchivoExperimental):
        raise ErrorConservacion("entorno_conservacion_no_creado") from None
    try:
        yield ConservadorExperimental(fs)
    except BaseException as e:
        if not disponer_al_salir:
            e.add_note("generacion_temporal_preservada_para_revision")
            raise
        try:
            fs.limpiar()
        except (OSError, ErrorArchivoExperimental):
            e.add_note("limpieza_generacion_requiere_revision")
        raise
    else:
        if not disponer_al_salir:
            return  # Retención TEMP explícita para lectura por un proceso posterior.
        try:
            fs.limpiar()
        except (OSError, ErrorArchivoExperimental):
            raise ErrorConservacion("limpieza_generacion_requiere_revision") from None


__all__ = (
    "VERSION_CONSERVACION", "USO_CONSERVAR", "USO_RECUPERAR", "ErrorConservacion",
    "UnidadConservacion", "ControlGeneracion", "EstadoRecuperacion",
    "ComprobacionContenido", "RecuperacionGeneracion", "ConservadorExperimental",
    "entorno_conservacion", "recuperar_generacion",
)
