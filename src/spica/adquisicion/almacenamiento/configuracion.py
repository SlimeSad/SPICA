"""Configuración operativa explícita; no inicializa ni escribe al importar."""

from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import shutil
import sqlite3
import stat
from uuid import uuid4

from .modelos import ErrorAlmacenamientoRAW
from .raw import AlmacenRAW, _segura
from .inspeccion import PoliticaInspeccionRAW, inspeccionar_catalogo
from ._errores import con_limpieza, error_publico


_CODIGO = Path(__file__).resolve().parents[4]
_MARCADOR = "spica-raw.json"
_EN_CURSO = ".spica-raw.inicializando"


def _error(codigo):
    return ErrorAlmacenamientoRAW(codigo)


def _directorio(ruta):
    # Windows hereda la ACL del padre; no se declara privacidad comprobada.
    ruta.mkdir(mode=0o755 if os.name == "nt" else 0o700)


def _estado(ruta):
    try:
        return ruta.stat()
    except FileNotFoundError:
        return None


def _sincronizar_directorio(ruta):
    # No hay fsync portable de directorios Windows con esta API estándar.
    if os.name == "nt":
        return False
    descriptor = os.open(ruta, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return True


@dataclass(frozen=True)
class ValidacionUbicacionRAW:
    raiz: Path
    staging: Path
    inicializado: bool
    espacio_libre_bytes: int
    advertencias: tuple[str, ...]

    @property
    def estado(self) -> str:
        return "inicializado" if self.inicializado else "no_inicializado"


@dataclass(frozen=True)
class ConfiguracionRAW:
    raiz: Path = field(default_factory=lambda: Path.home() / "SPICA_DATOS" / "raw")
    max_bytes: int = 10 * 1024**3
    tamano_bloque: int = 65_536
    espacio_minimo_libre: int = 64 * 1024**2
    claves_parametros_publicos: tuple[str, ...] = ("producto_id",)
    inspeccion: PoliticaInspeccionRAW = field(default_factory=PoliticaInspeccionRAW)

    def __post_init__(self):
        object.__setattr__(self, "raiz", Path(self.raiz).expanduser())
        if not self.raiz.is_absolute():
            raise ValueError("Se requiere una raiz absoluta")
        if not self.raiz.name:
            raise ValueError("La raiz de un volumen no es un almacen")
        for nombre in ("max_bytes", "tamano_bloque", "espacio_minimo_libre"):
            valor = getattr(self, nombre)
            if type(valor) is not int or valor <= 0:
                raise ValueError("Los limites deben ser enteros positivos")
        if self.tamano_bloque > 1_048_576:
            raise ValueError("Bloques de hasta 1 MiB")
        claves = self.claves_parametros_publicos
        if isinstance(claves, str):
            raise TypeError("Se requiere una coleccion de claves publicas")
        claves = tuple(claves)
        if any(not isinstance(c, str) or not c.strip() for c in claves):
            raise ValueError("Claves publicas no vacias requeridas")
        object.__setattr__(self, "claves_parametros_publicos", claves)
        if not isinstance(self.inspeccion, PoliticaInspeccionRAW):
            raise TypeError("Se requiere una politica de inspeccion RAW")

    @property
    def staging(self) -> Path:
        return self.raiz.with_name(self.raiz.name + "-staging")

    def _rutas(self):
        rutas = (self.raiz, self.staging)
        if self.inspeccion.directorio_temporal is not None:
            rutas += (self.inspeccion.directorio_temporal,)
        for ruta in rutas:
            _segura(ruta)
            resuelta = ruta.resolve(strict=False)
            if (resuelta.is_relative_to(_CODIGO) or _CODIGO.is_relative_to(resuelta)
                    or any(p.casefold() in {".git", ".venv", ".codex", ".agents"} for p in ruta.parts)):
                raise _error("ubicacion_dentro_de_codigo_o_control_interno")
            # También protege otros checkouts y worktrees (.git puede ser archivo).
            if any((p / ".git").exists() for p in (resuelta, *resuelta.parents)):
                raise _error("ubicacion_dentro_de_repositorio_git")

    def _contenido_marcador(self):
        return {"tipo": "spica.raw.operativo", "version": 1, "staging_nombre": self.staging.name}

    def _reconocer(self):
        if not self.raiz.is_dir():
            raise _error("raiz_raw_no_es_directorio")
        if _estado(_segura(self.raiz / _EN_CURSO)) is not None:
            raise _error("inicializacion_raw_requiere_revision")
        marcador = _segura(self.raiz / _MARCADOR)
        if not marcador.is_file():
            raise _error("almacen_no_gestionado_o_inicializacion_incompleta")
        with marcador.open("rb") as archivo:
            contenido = archivo.read(4097)
        if len(contenido) > 4096:
            raise _error("marcador_raw_invalido")
        try:
            datos = json.loads(contenido)
            if (not isinstance(datos, dict) or type(datos.get("version")) is not int
                    or datos != self._contenido_marcador()):
                raise _error("marcador_raw_incompatible")
        except (ValueError, UnicodeError):
            raise _error("marcador_raw_invalido") from None
        for ruta in (self.staging, self.raiz / "temporales", self.raiz / "sha256"):
            if not _segura(ruta).is_dir():
                raise _error("estructura_raw_incompleta")
        catalogo = _segura(self.raiz / "catalogo.sqlite3")
        info = _estado(catalogo)
        if info is None or not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise _error("catalogo_raw_no_regular_o_compartido")
        if not os.access(catalogo, os.R_OK | os.W_OK):
            raise _error("catalogo_raw_sin_permisos_basicos")
        inspeccionar_catalogo(catalogo, politica=self.inspeccion)

    @error_publico("validar", "ubicacion_raw_no_accesible", "error_inspeccion_ubicacion_raw")
    def validar(self) -> ValidacionUbicacionRAW:
        """No crea el almacén; WAL puede necesitar una copia temporal privada."""
        try:
            self._rutas()
            existe = _estado(self.raiz) is not None
            if existe:
                self._reconocer()
            elif _estado(self.staging) is not None:
                raise _error("staging_existente_sin_almacen_gestionado")
            padre = self.raiz
            while _estado(padre) is None:
                padre = padre.parent
            if not padre.is_dir():
                raise _error("ancestro_raw_no_es_directorio")
            if not os.access(padre, os.R_OK | os.W_OK | os.X_OK):
                raise _error("ubicacion_raw_sin_permisos_basicos")
            libre = shutil.disk_usage(padre).free
            if libre < self.espacio_minimo_libre:
                raise _error("espacio_raw_insuficiente")
            return ValidacionUbicacionRAW(self.raiz, self.staging, existe, libre,
                ("permisos_y_espacio_no_son_reservas", "acl_windows_no_auditada" if os.name == "nt"
                 else "permisos_no_aislan_procesos_del_usuario", "enlaces_duros_se_comprueban_al_abrir"))
        except PermissionError as error:
            raise con_limpieza(_error("ubicacion_raw_no_accesible"), getattr(error, "fallos_limpieza", ())) from None
        except (OSError, sqlite3.Error) as error:
            raise con_limpieza(_error("error_inspeccion_ubicacion_raw"), getattr(error, "fallos_limpieza", ())) from None

    def _limpiar_propios(self, recursos):
        fallos = []
        permitidos = {self.raiz, self.staging, self.raiz / "temporales", self.raiz / "sha256"}
        for rol, ruta in recursos:
            try:
                if ruta.parent not in permitidos or not ruta.name.startswith((".sonda-", ".spica-marcador-")):
                    raise _error("limpieza_fuera_de_directorio_controlado")
                _segura(ruta).unlink(missing_ok=True)
            except (OSError, ErrorAlmacenamientoRAW):
                fallos.append((rol, "eliminacion_no_disponible"))
        return tuple(fallos)

    def _probar_publicacion(self):
        """Sonda pequeña y explícita entre los directorios reales de publicación."""
        identificador = ".sonda-" + uuid4().hex
        entrada = self.raiz / "temporales" / identificador
        destino = self.raiz / "sha256" / identificador
        sonda_staging = self.staging / identificador
        recursos = []
        principal = None
        try:
            if not os.access(self.staging, os.R_OK | os.W_OK | os.X_OK):
                raise _error("staging_sin_permisos_basicos")
            # Prueba real de escritura del staging, usando únicamente archivo propio.
            with sonda_staging.open("xb") as archivo:
                recursos.append(("sonda_staging", sonda_staging))
                if archivo.write(b"SPICA staging") != len(b"SPICA staging"):
                    raise _error("escritura_sonda_incompleta")
                archivo.flush()
                os.fsync(archivo.fileno())
            with entrada.open("xb") as archivo:
                recursos.append(("sonda_entrada", entrada))
                if archivo.write(b"SPICA publicacion exclusiva") != len(b"SPICA publicacion exclusiva"):
                    raise _error("escritura_sonda_incompleta")
                archivo.flush()
                os.fsync(archivo.fileno())
            os.link(entrada, destino)
            recursos.insert(1, ("sonda_publicada", destino))
            try:
                os.link(entrada, destino)
            except FileExistsError:
                pass
            else:
                raise _error("publicacion_no_exclusiva")
            if destino.read_bytes() != b"SPICA publicacion exclusiva":
                raise _error("sonda_publicacion_no_coincidente")
        except PermissionError:
            principal = _error("operacion_raw_sin_permisos")
        except OSError:
            principal = _error("publicacion_exclusiva_no_disponible")
        except BaseException as error:
            principal = error
        fallos = self._limpiar_propios(recursos)
        if principal is not None:
            raise con_limpieza(principal, fallos)
        if fallos:
            raise con_limpieza(_error("limpieza_sondas_incompleta"), fallos)

    def _abrir_motor(self, nuevo):
        self._probar_publicacion()
        almacen = AlmacenRAW(self.raiz, (self.staging,), max_bytes=self.max_bytes,
            tamano_bloque=self.tamano_bloque, claves_parametros_publicos=self.claves_parametros_publicos,
            politica_inspeccion=self.inspeccion)
        return AlmacenOperativoRAW(self, almacen, nuevo)

    @error_publico("abrir", "operacion_raw_sin_permisos", "error_apertura_raw_operativo")
    def abrir(self):
        """Abre solo un almacén reconocido; no inicializa ni migra uno existente."""
        try:
            if not self.validar().inicializado:
                raise _error("almacen_raw_no_inicializado")
            return self._abrir_motor(False)
        except PermissionError as error:
            raise con_limpieza(_error("operacion_raw_sin_permisos"), getattr(error, "fallos_limpieza", ())) from None
        except (OSError, sqlite3.Error) as error:
            raise con_limpieza(_error("error_apertura_raw_operativo"), getattr(error, "fallos_limpieza", ())) from None

    def _crear_intencion(self):
        # Una intención existente nunca se adopta ni elimina automáticamente.
        with _segura(self.raiz / _EN_CURSO).open("xb") as archivo:
            contenido = b"revision hasta completar publicacion\n"
            if archivo.write(contenido) != len(contenido):
                raise _error("escritura_intencion_incompleta")
            archivo.flush()
            os.fsync(archivo.fileno())
        return _sincronizar_directorio(self.raiz)

    def _publicar_marcador(self):
        temporal = self.raiz / (".spica-marcador-" + uuid4().hex + ".tmp")
        marcador = self.raiz / _MARCADOR
        recursos = []
        principal = None
        sincronizado = False
        try:
            with temporal.open("x", encoding="utf-8") as archivo:
                recursos.append(("marcador_temporal", temporal))
                json.dump(self._contenido_marcador(), archivo, ensure_ascii=False)
                archivo.flush()
                os.fsync(archivo.fileno())
            with temporal.open("rb") as archivo:
                almacenado = archivo.read(4097)
            esperado = json.dumps(self._contenido_marcador(), ensure_ascii=False).encode("utf-8")
            if len(almacenado) > 4096 or almacenado != esperado:
                raise _error("marcador_temporal_no_coincidente")
            os.link(temporal, marcador)  # Exclusivo; no reemplaza otro marcador.
            sincronizado = _sincronizar_directorio(self.raiz)
        except BaseException as error:
            principal = error
        fallos = self._limpiar_propios(recursos)
        if principal is not None:
            raise con_limpieza(principal, fallos)
        if fallos:
            raise con_limpieza(_error("limpieza_marcador_incompleta"), fallos)
        advertencias = () if sincronizado else ("sincronizacion_directorio_no_disponible",)
        try:
            # Última operación necesaria: el marcador ya fue fsync y publicado.
            # No se exige fsync tras retirar la intención: si reaparece después
            # de un apagado, se rechaza por revisión, sin falso estado operativo.
            (self.raiz / _EN_CURSO).unlink()
        except OSError:
            if _estado(self.raiz / _EN_CURSO) is not None:
                raise
            # El sistema retiró la intención, pero falló al comunicarlo. Solo
            # devolver éxito si una nueva inspección reconoce el estado final.
            self._reconocer()
            advertencias += ("retiro_intencion_confirmado_tras_error",)
        return advertencias

    @error_publico("inicializar", "inicializacion_raw_sin_permisos", "error_inicializacion_raw_operativo")
    def inicializar(self):
        """Acción explícita. Un fallo conserva residuos propios para revisión manual."""
        try:
            validacion = self.validar()
            if validacion.inicializado:
                return self.abrir()
            pendientes = []
            padre = self.raiz.parent
            while _estado(padre) is None:
                pendientes.append(padre)
                padre = padre.parent
            for ruta in reversed(pendientes):
                _segura(ruta)
                _directorio(ruta)
            _directorio(self.raiz)  # Exclusivo; nunca exist_ok=True.
            _directorio(self.staging)
            _directorio(self.raiz / "temporales")
            _directorio(self.raiz / "sha256")
            self._crear_intencion()
            # CatalogoRAW reserva exclusivamente el archivo inexistente. No
            # dejar una base vacía que pudiera confundirse con una preexistente.
            resultado = self._abrir_motor(True)
            try:
                resultado.advertencias = self._publicar_marcador()
            except BaseException as error:
                try:
                    resultado.close()
                except (OSError, sqlite3.Error):
                    con_limpieza(error, (("catalogo", "cierre_no_disponible"),))
                raise
            return resultado
        except PermissionError as error:
            raise con_limpieza(_error("inicializacion_raw_sin_permisos"), getattr(error, "fallos_limpieza", ())) from None
        except (OSError, sqlite3.Error) as error:
            raise con_limpieza(_error("error_inicializacion_raw_operativo"), getattr(error, "fallos_limpieza", ())) from None


@dataclass
class AlmacenOperativoRAW:
    configuracion: ConfiguracionRAW
    almacen: AlmacenRAW
    nuevo: bool
    advertencias: tuple[str, ...] = ()

    def close(self):
        self.almacen.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def adaptador_http(self, cliente, *, max_bytes: int, tamano_bloque: int = 65_536):
        from ..integracion import AdaptadorHTTPRAW
        if type(max_bytes) is not int or not 0 < max_bytes <= self.configuracion.max_bytes:
            raise ValueError("Limite de descarga debe respetar el limite RAW")
        return AdaptadorHTTPRAW(cliente, self.almacen, self.configuracion.staging,
                               max_bytes=max_bytes, tamano_bloque=tamano_bloque)
