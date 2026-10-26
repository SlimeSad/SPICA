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
from urllib.parse import urlsplit, urlunsplit
from uuid import uuid4

from .catalogo import CatalogoRAW, ahora
from .modelos import (ActivoRAW, ComprobacionRAW, DeclaracionRAW, DiagnosticoRAW,
                      ErrorAlmacenamientoRAW, EstadoIncorporacion)


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


def _declaracion_publica(declaracion: DeclaracionRAW, claves: frozenset[str]):
    advertencias = []
    parametros = {}
    sensibles = ("token", "password", "passwd", "secret", "credential", "authorization",
                 "apikey", "signature", "contraseña", "contrasena", "cookie", "clave", "firma")
    for clave, valor in declaracion.parametros_publicos.items():
        normalizada = re.sub(r"[^a-z0-9ñ]", "", clave.casefold())
        if (clave not in claves or any(s in normalizada for s in sensibles)
                or _privada(valor) or "://" in valor):
            advertencias.append("parametro_omitido")
        else:
            parametros[clave] = valor
    procedencia = declaracion.procedencia
    if procedencia is not None:
        if "://" in procedencia:
            url = urlsplit(procedencia)
            if url.scheme not in ("http", "https") or not url.hostname:
                raise ErrorAlmacenamientoRAW("procedencia_no_admitida")
            host = url.hostname
            if ":" in host:
                host = f"[{host}]"
            netloc = host + (f":{url.port}" if url.port is not None else "")
            limpia = urlunsplit((url.scheme, netloc, url.path, "", ""))
            if limpia != procedencia:
                advertencias.append("procedencia_sin_credenciales_consulta_fragmento")
            procedencia = limpia
        if _privada(procedencia) or "?" in procedencia or "#" in procedencia:
            raise ErrorAlmacenamientoRAW("procedencia_sensible")
    for valor in (declaracion.proyecto_id, declaracion.objeto_id, declaracion.recurso_id,
                  declaracion.fuente.proveedor, declaracion.fuente.identificador,
                  declaracion.formato_declarado or "", declaracion.tipo_medio_declarado or ""):
        sensible = _privada(valor)
        if "://" in valor:
            uri = urlsplit(valor)
            sensible = sensible or bool(uri.username or uri.password or uri.query or uri.fragment)
        if sensible:
            raise ErrorAlmacenamientoRAW("identificador_o_metadato_sensible")
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
            if (_huella(archivo, self.bloque, self.max_bytes) != (tamano, hash_local)
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
        except (OSError, ErrorAlmacenamientoRAW) as exc:
            error = exc.codigo if isinstance(exc, ErrorAlmacenamientoRAW) else "contenido_no_accesible"
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
