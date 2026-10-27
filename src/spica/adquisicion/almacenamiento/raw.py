"""Copia RAW direccionada por contenido, catálogo persistente y comprobación local."""

from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import re
import sqlite3
import stat
import tempfile
from urllib.parse import unquote, urlsplit, urlunsplit
from uuid import uuid4

from .catalogo import CatalogoRAW, ahora
from .modelos import (ActivoRAW, ComprobacionRAW, DeclaracionRAW, DiagnosticoRAW,
                      ErrorAlmacenamientoRAW, EstadoIncorporacion, ObjetoCientifico, ProyectoCientifico)


def _segura(ruta: Path) -> Path:
    ruta = Path(ruta).absolute()
    if ".." in ruta.parts:
        raise ErrorAlmacenamientoRAW("ruta_insegura")
    for parte in (ruta, *ruta.parents):
        if parte.is_symlink() or parte.is_junction():
            raise ErrorAlmacenamientoRAW("enlace_no_autorizado")
    return ruta


def _huella(archivo, bloque: int, limite: int) -> tuple[int, str]:
    hash_local = hashlib.sha256()
    tamano = 0
    while datos := archivo.read(bloque):
        tamano += len(datos)
        if tamano > limite:
            raise ErrorAlmacenamientoRAW("limite_excedido")
        hash_local.update(datos)
    return tamano, hash_local.hexdigest()


def _privada(texto: str) -> bool:
    texto = texto.casefold()
    return bool(re.search(r"bearer\s|(?:token|password|passwd|secret|credential|authorization|api[_-]?key|firma|contrase[nñ]a)\s*[:=]", texto))


def _referencia_publica(valor: str, *, sanear_url: bool) -> tuple[str, bool]:
    """Clasifica sin reescribir identificadores opacos; errores sin texto de entrada."""
    inspeccion = valor.strip()
    # Detecta formas ofuscadas; nunca las decodifica para persistirlas como identificador.
    decodificada = inspeccion
    for _ in range(3):
        decodificada = unquote(decodificada)
    if (any(ord(c) < 32 or ord(c) == 127 for c in valor + decodificada)
            or "\\" in decodificada or decodificada.startswith("//")):
        raise ErrorAlmacenamientoRAW("referencia_sensible_o_ambigua")
    try:
        uri = urlsplit(inspeccion)
        es_url = "://" in inspeccion or uri.scheme.lower() in ("http", "https") or bool(uri.netloc)
        if not es_url:
            if (_privada(decodificada) or "@" in decodificada
                    or (sanear_url and ("?" in valor or "#" in valor))):
                raise ErrorAlmacenamientoRAW("referencia_sensible_o_ambigua")
            # Una URL escondida en escapes no se acepta como referencia opaca.
            if "://" in decodificada:
                raise ErrorAlmacenamientoRAW("referencia_sensible_o_ambigua")
            return valor, False
        if (uri.scheme not in ("http", "https") or not uri.netloc or not uri.hostname
                or not inspeccion.lower().startswith(uri.scheme + "://")
                or any(c.isspace() for c in inspeccion)):
            raise ErrorAlmacenamientoRAW("referencia_url_no_admitida")
        puerto = uri.port  # Valida también puertos mal formados, sin propagar su texto.
        ruta_decodificada = uri.path
        for _ in range(3):
            ruta_decodificada = unquote(ruta_decodificada)
        if _privada(ruta_decodificada) or _privada(uri.hostname):
            raise ErrorAlmacenamientoRAW("referencia_sensible_o_ambigua")
        if not sanear_url:
            if uri.username is not None or uri.password is not None or uri.query or uri.fragment:
                raise ErrorAlmacenamientoRAW("identificador_o_metadato_sensible")
            return valor, False
        host = f"[{uri.hostname}]" if ":" in uri.hostname else uri.hostname
        limpia = urlunsplit((uri.scheme, host + (f":{puerto}" if puerto is not None else ""), uri.path, "", ""))
        return limpia, limpia != valor
    except ValueError:
        raise ErrorAlmacenamientoRAW("referencia_url_no_admitida") from None


def _declaracion_publica(declaracion: DeclaracionRAW, claves: frozenset[str]):
    advertencias = []
    parametros = {}
    sensibles = ("token", "password", "passwd", "secret", "credential", "authorization",
                 "apikey", "signature", "contraseña", "contrasena", "cookie", "clave", "firma")
    for clave, valor in declaracion.parametros_publicos.items():
        normalizada = re.sub(r"[^a-z0-9ñ]", "", clave.casefold())
        try:
            _referencia_publica(valor, sanear_url=False)
            valor_ambiguo = False
        except ErrorAlmacenamientoRAW:
            valor_ambiguo = True
        if (clave not in claves or any(s in normalizada for s in sensibles)
                or valor_ambiguo or "://" in valor):
            advertencias.append("parametro_omitido")
        else:
            parametros[clave] = valor
    procedencia = declaracion.procedencia
    if procedencia is not None:
        procedencia, modificada = _referencia_publica(procedencia, sanear_url=True)
        if modificada:
            advertencias.append("procedencia_sin_credenciales_consulta_fragmento")
    for valor in (declaracion.proyecto_id, declaracion.objeto_id, declaracion.recurso_id,
                  declaracion.fuente.proveedor, declaracion.fuente.identificador,
                  declaracion.formato_declarado or "", declaracion.tipo_medio_declarado or ""):
        _referencia_publica(valor, sanear_url=False)
    return replace(declaracion, procedencia=procedencia, parametros_publicos=parametros), tuple(dict.fromkeys(advertencias))


class AlmacenRAW:
    """Uso secuencial en directorios privados. No certifica autenticidad institucional."""

    def __init__(self, directorio: Path, raices_entrada: tuple[Path, ...], *,
                 max_bytes: int = 10 * 1024**3, tamano_bloque: int = 65_536,
                 claves_parametros_publicos: tuple[str, ...] = ()):
        for valor in (max_bytes, tamano_bloque):
            if type(valor) is not int or valor <= 0:
                raise ValueError("Los límites deben ser enteros positivos")
        if tamano_bloque > 1_048_576 or not raices_entrada:
            raise ValueError("Se requieren raíces de entrada y bloques de hasta 1 MiB")
        if any(not isinstance(c, str) or not c.strip() for c in claves_parametros_publicos):
            raise ValueError("Las claves públicas deben ser texto no vacío")
        self.raiz = _segura(directorio).resolve(strict=True)
        self.entradas = tuple(_segura(p).resolve(strict=True) for p in raices_entrada)
        if not self.raiz.is_dir() or any(not p.is_dir() for p in self.entradas):
            raise ValueError("Se requieren directorios existentes")
        self.max_bytes = max_bytes
        self.bloque = tamano_bloque
        self.claves = frozenset(claves_parametros_publicos)
        self.temporales = self.raiz / "temporales"
        self.contenidos = self.raiz / "sha256"
        for carpeta in (self.temporales, self.contenidos):
            _segura(carpeta).mkdir(exist_ok=True)
        catalogo = _segura(self.raiz / "catalogo.sqlite3")
        try:
            self._catalogo = CatalogoRAW(catalogo)
        except sqlite3.Error as exc:
            raise ErrorAlmacenamientoRAW("error_sqlite") from exc

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        self._catalogo.close()

    def registrar_proyecto(self, proyecto: ProyectoCientifico) -> ProyectoCientifico:
        if not isinstance(proyecto, ProyectoCientifico):
            raise TypeError("Se requiere ProyectoCientifico")
        for valor in (proyecto.project_id, proyecto.schema_version, proyecto.nombre,
                      proyecto.contexto, proyecto.estado):
            if valor is not None:
                _referencia_publica(valor, sanear_url=False)
        try:
            return self._catalogo.registrar_proyecto(proyecto)
        except sqlite3.Error as exc:
            raise ErrorAlmacenamientoRAW("error_sqlite") from exc

    def consultar_proyecto(self, project_id: str) -> ProyectoCientifico:
        try:
            return self._catalogo.consultar_proyecto(project_id)
        except sqlite3.Error as exc:
            raise ErrorAlmacenamientoRAW("error_sqlite") from exc

    def registrar_objeto(self, objeto: ObjetoCientifico) -> ObjetoCientifico:
        if not isinstance(objeto, ObjetoCientifico):
            raise TypeError("Se requiere ObjetoCientifico")
        for valor in (objeto.object_id, objeto.project_id, objeto.family, objeto.kind, objeto.state):
            if valor is not None:
                _referencia_publica(valor, sanear_url=False)
        try:
            return self._catalogo.registrar_objeto(objeto)
        except sqlite3.Error as exc:
            raise ErrorAlmacenamientoRAW("error_sqlite") from exc

    def consultar_objeto(self, object_id: str) -> ObjetoCientifico:
        try:
            return self._catalogo.consultar_objeto(object_id)
        except sqlite3.Error as exc:
            raise ErrorAlmacenamientoRAW("error_sqlite") from exc

    def _ruta_contenido(self, hash_local: str) -> Path:
        if not isinstance(hash_local, str) or not re.fullmatch(r"[0-9a-f]{64}", hash_local):
            raise ErrorAlmacenamientoRAW("hash_catalogo_invalido")
        return _segura(self.contenidos / hash_local[:2] / hash_local)

    def _entrada(self, ruta: Path) -> Path:
        ruta = _segura(ruta).resolve(strict=True)
        if ruta.is_relative_to(self.raiz) or not any(ruta.is_relative_to(p) for p in self.entradas):
            raise ErrorAlmacenamientoRAW("entrada_no_autorizada")
        if not stat.S_ISREG(ruta.stat().st_mode):
            raise ErrorAlmacenamientoRAW("entrada_no_regular")
        return ruta

    @staticmethod
    def _identidad(estado):
        # Windows puede presentar ctime distinto entre stat(path) y fstat(handle)
        # tras publicar un enlace. No usarlo como evidencia portable de modificación.
        return estado.st_dev, estado.st_ino, estado.st_size, estado.st_mtime_ns

    def _copiar(self, entrada: Path, archivo) -> tuple[int, str]:
        with entrada.open("rb") as original:
            inicial = os.fstat(original.fileno())
            if not stat.S_ISREG(inicial.st_mode):
                raise ErrorAlmacenamientoRAW("entrada_no_regular")
            if inicial.st_size > self.max_bytes:
                raise ErrorAlmacenamientoRAW("limite_excedido")
            tamano = 0
            hash_local = hashlib.sha256()
            while datos := original.read(self.bloque):
                tamano += len(datos)
                if tamano > self.max_bytes:
                    raise ErrorAlmacenamientoRAW("limite_excedido")
                if archivo.write(datos) != len(datos):
                    raise ErrorAlmacenamientoRAW("escritura_incompleta")
                hash_local.update(datos)
            if (self._identidad(inicial) != self._identidad(os.fstat(original.fileno()))
                    or self._identidad(inicial) != self._identidad(entrada.stat())
                    or tamano != inicial.st_size):
                raise ErrorAlmacenamientoRAW("entrada_modificada")
        archivo.flush()
        os.fsync(archivo.fileno())
        archivo.seek(0)
        esperado = tamano, hash_local.hexdigest()
        if _huella(archivo, self.bloque, self.max_bytes) != esperado:
            raise ErrorAlmacenamientoRAW("copia_no_coincidente")
        return esperado

    def _comprobar_archivo(self, ruta: Path, tamano: int, hash_local: str):
        _segura(ruta)
        if not stat.S_ISREG(ruta.stat().st_mode):
            raise ErrorAlmacenamientoRAW("contenido_no_regular")
        with ruta.open("rb") as archivo:
            inicial = os.fstat(archivo.fileno())
            if inicial.st_size != tamano:
                raise ErrorAlmacenamientoRAW("contenido_no_coincidente")
            try:
                # El tamaño del activo es evidencia persistida, no una política de entrada.
                huella = _huella(archivo, self.bloque, tamano)
            except ErrorAlmacenamientoRAW as exc:
                if exc.codigo == "limite_excedido":
                    raise ErrorAlmacenamientoRAW("contenido_no_coincidente") from None
                raise
            if (huella != (tamano, hash_local)
                    or self._identidad(inicial) != self._identidad(os.fstat(archivo.fileno()))
                    or self._identidad(inicial) != self._identidad(ruta.stat())):
                raise ErrorAlmacenamientoRAW("contenido_no_coincidente")

    def incorporar(self, entrada: Path, declaracion: DeclaracionRAW) -> ActivoRAW:
        if not isinstance(declaracion, DeclaracionRAW):
            raise TypeError("Se requiere DeclaracionRAW")
        declaracion, advertencias = _declaracion_publica(declaracion, self.claves)
        activo_id = uuid4().hex
        temporal = None
        preparada = False
        try:
            self._catalogo.preparar(activo_id, declaracion, advertencias)
            preparada = True
            entrada = self._entrada(entrada)
            _segura(self.temporales)
            with tempfile.NamedTemporaryFile(mode="w+b", prefix=activo_id + "-", suffix=".tmp",
                                              dir=self.temporales, delete=False) as archivo:
                temporal = Path(archivo.name)
                tamano, hash_local = self._copiar(entrada, archivo)
            destino = self._ruta_contenido(hash_local)
            destino.parent.mkdir(exist_ok=True)
            relativa = destino.relative_to(self.raiz).as_posix()
            self._catalogo.transicion(activo_id, EstadoIncorporacion.VERIFICADA,
                                      tamano=tamano, sha256=hash_local, ruta=relativa)
            try:
                os.link(temporal, destino)
            except FileExistsError:
                # Deduplícación solo si el contenido existente se comprueba realmente.
                self._comprobar_archivo(destino, tamano, hash_local)
            self._comprobar_archivo(destino, tamano, hash_local)
            temporal.unlink()
            temporal = None
            self._catalogo.transicion(activo_id, EstadoIncorporacion.INCORPORADA, comprobacion=ahora())
            return self.metadatos(activo_id)
        except BaseException as exc:
            codigo = (exc.codigo if isinstance(exc, ErrorAlmacenamientoRAW)
                      else "error_sqlite" if isinstance(exc, sqlite3.Error)
                      else "interrumpida" if not isinstance(exc, Exception)
                      else "error_archivo")
            if temporal is not None:
                try:
                    temporal.unlink(missing_ok=True)
                except OSError:
                    # Residuo con prefijo del activo: visible en diagnosticar(), nunca confirmado.
                    codigo = "temporal_no_eliminado"
            if preparada:
                try:
                    self._catalogo.transicion(activo_id, EstadoIncorporacion.FALLIDA, error=codigo)
                except sqlite3.Error:
                    # La preparación/verificación ya confirmada permite detectar la interrupción.
                    pass
            if not isinstance(exc, Exception):
                raise
            raise ErrorAlmacenamientoRAW(codigo, activo_id) from exc

    def metadatos(self, activo_id: str) -> ActivoRAW:
        """Instantánea del catálogo; no certifica el estado actual del archivo."""
        try:
            return self._catalogo.consultar(activo_id)
        except sqlite3.Error as exc:
            raise ErrorAlmacenamientoRAW("error_sqlite", activo_id) from exc

    def verificar(self, activo_id: str) -> ComprobacionRAW:
        activo = self.metadatos(activo_id)
        if activo.estado not in (EstadoIncorporacion.INCORPORADA, EstadoIncorporacion.INCONSISTENTE):
            raise ErrorAlmacenamientoRAW("activo_no_disponible", activo_id)
        momento = datetime.now(timezone.utc)
        error = None
        try:
            ruta = self._ruta_contenido(activo.sha256)
            if ruta.relative_to(self.raiz).as_posix() != activo.ruta_interna:
                raise ErrorAlmacenamientoRAW("ruta_catalogo_inconsistente")
            self._comprobar_archivo(ruta, activo.tamano, activo.sha256)
        except FileNotFoundError:
            error = "contenido_ausente"
        except (OSError, MemoryError):
            # Permisos, descriptores o fallos de lectura no demuestran corrupción.
            raise ErrorAlmacenamientoRAW("verificacion_no_disponible", activo_id) from None
        except ErrorAlmacenamientoRAW as exc:
            if exc.codigo not in {"contenido_no_coincidente", "contenido_no_regular",
                                   "ruta_catalogo_inconsistente", "hash_catalogo_invalido",
                                   "enlace_no_autorizado", "ruta_insegura"}:
                raise ErrorAlmacenamientoRAW("verificacion_no_disponible", activo_id) from None
            error = exc.codigo
        estado = EstadoIncorporacion.INCONSISTENTE if error else activo.estado
        try:
            self._catalogo.transicion(activo_id, estado, error=error or activo.error,
                                      comprobacion=momento.isoformat())
        except sqlite3.Error as exc:
            raise ErrorAlmacenamientoRAW("error_sqlite", activo_id) from exc
        return ComprobacionRAW(activo_id, error is None, momento, error)

    def recuperar(self, activo_id: str) -> Path:
        activo = self.metadatos(activo_id)
        if activo.estado is not EstadoIncorporacion.INCORPORADA:
            raise ErrorAlmacenamientoRAW("activo_no_disponible", activo_id)
        if not self.verificar(activo_id).coincide:
            raise ErrorAlmacenamientoRAW("integridad_local_fallida", activo_id)
        return self._ruta_contenido(activo.sha256)

    def diagnosticar(self) -> DiagnosticoRAW:
        """Detecta; no elimina, repara ni promueve operaciones incompletas."""
        try:
            activos = self._catalogo.listar()
            for activo in activos:
                if activo.estado is EstadoIncorporacion.INCORPORADA:
                    self.verificar(activo.activo_id)
            activos = self._catalogo.listar()
        except sqlite3.Error as exc:
            raise ErrorAlmacenamientoRAW("error_sqlite") from exc
        referencias = {a.ruta_interna for a in activos if a.estado is EstadoIncorporacion.INCORPORADA}
        _segura(self.contenidos)
        _segura(self.temporales)
        archivos = []
        for carpeta in self.contenidos.iterdir():
            _segura(carpeta)
            if carpeta.is_dir():
                archivos.extend(p.relative_to(self.raiz).as_posix() for p in carpeta.iterdir())
        return DiagnosticoRAW(
            tuple(a.activo_id for a in activos if a.estado in (EstadoIncorporacion.PREPARADA,
                  EstadoIncorporacion.VERIFICADA, EstadoIncorporacion.FALLIDA)),
            tuple(a.activo_id for a in activos if a.estado is EstadoIncorporacion.INCONSISTENTE),
            tuple(sorted(set(archivos) - referencias)),
            tuple(sorted(p.relative_to(self.raiz).as_posix() for p in self.temporales.iterdir())))
