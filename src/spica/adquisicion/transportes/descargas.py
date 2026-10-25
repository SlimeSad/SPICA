"""Staging de descargas; no implementa almacenamiento científico definitivo."""

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import re
import tempfile
from typing import Mapping, TYPE_CHECKING

from ..nucleo import Descarga, EstadoDescarga
from .http import ErrorTransporteHTTP, TipoErrorHTTP, _url_autorizable

if TYPE_CHECKING:
    from .http import ClienteHTTP


@dataclass(frozen=True)
class InformeDescarga:
    origen: str
    fecha_utc: datetime
    estado: EstadoDescarga
    bytes_almacenados: int
    sha256: str | None
    ruta_local: Path | None
    codigo_http: int | None
    error: TipoErrorHTTP | None = None
    temporal_restante: Path | None = None
    bytes_declarados: int | None = None

    def como_descarga(self) -> Descarga:
        """Solo un archivo publicado puede representarse como descarga completa."""
        if self.estado is not EstadoDescarga.COMPLETA or self.ruta_local is None:
            raise ValueError("El informe no contiene un archivo publicado")
        return Descarga(EstadoDescarga.COMPLETA, str(self.ruta_local), self.bytes_almacenados)


class ErrorDescargaArchivo(ErrorTransporteHTTP):
    def __init__(self, tipo: TipoErrorHTTP, informe: InformeDescarga):
        super().__init__(tipo, "La descarga a disco no se completó", informe.codigo_http)
        self.informe = informe


def _destino_seguro(directorio: Path, nombre: str) -> Path:
    # Subconjunto portable: evita separadores, ADS, dispositivos Windows y nombres
    # proporcionados por Content-Disposition. El directorio debe existir previamente.
    if (not isinstance(nombre, str)
            or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,99}", nombre)
            or nombre.endswith(".")
            or nombre.split(".")[0].upper() in {
                "CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$",
                *(f"COM{i}" for i in range(10)), *(f"LPT{i}" for i in range(10)),
            }):
        raise ValueError("El nombre debe ser un componente local seguro y portable")
    raiz = Path(directorio).absolute()
    for componente in (raiz, *raiz.parents):
        if componente.is_symlink() or componente.is_junction():
            raise ValueError("El directorio controlado no admite enlaces ni junctions")
    raiz = raiz.resolve(strict=True)
    if not raiz.is_dir():
        raise ValueError("Se requiere un directorio controlado existente")
    return raiz / nombre


def _limpiar(temporal: Path | None) -> Path | None:
    if temporal is not None:
        try:
            temporal.unlink(missing_ok=True)
        except OSError:
            return temporal
    return None


def descargar_archivo(
    cliente: "ClienteHTTP", url: str, directorio: Path, nombre: str, *,
    max_bytes: int, tamano_bloque: int, parametros: Mapping[str, str] | None,
) -> InformeDescarga:
    for valor, etiqueta in ((max_bytes, "max_bytes"), (tamano_bloque, "tamano_bloque")):
        if type(valor) is not int or valor <= 0:
            raise ValueError(f"{etiqueta} debe ser un entero positivo")
    if tamano_bloque > 1_048_576:
        raise ValueError("tamano_bloque no puede superar 1 MiB")
    if not cliente.configuracion.verificar_tls:
        raise ValueError("La descarga a disco exige verificación TLS activada")
    destino = _destino_seguro(directorio, nombre)
    direccion = _url_autorizable(url)
    # El origen no incluye usuario, ruta, consulta ni fragmento.
    origen = str(direccion.copy_with(path="/", query=None, fragment=None))
    temporal = None
    recibidos = 0
    codigo = None
    esperado = None
    try:
        if os.path.lexists(destino):
            raise ErrorTransporteHTTP(TipoErrorHTTP.DESTINO_EXISTENTE, "El destino ya existe")
        with cliente._abrir(url, parametros, max_bytes) as (respuesta, esperado):
            codigo = respuesta.status_code
            # NamedTemporaryFile crea de forma exclusiva, en el mismo sistema de archivos.
            with tempfile.NamedTemporaryFile(mode="w+b", prefix=".suadc-", suffix=".tmp",
                                              dir=destino.parent, delete=False) as archivo:
                temporal = Path(archivo.name)
                hash_recibido = hashlib.sha256()
                for bloque in cliente._bloques(respuesta, esperado, max_bytes,
                                               min(tamano_bloque, max_bytes + 1)):
                    escritos = archivo.write(bloque)
                    if escritos is not None:
                        recibidos += escritos
                    if escritos != len(bloque):
                        raise OSError("Escritura incompleta")
                    hash_recibido.update(bloque)
                archivo.flush()
                os.fsync(archivo.fileno())
                archivo.seek(0)
                hash_disco = hashlib.sha256()
                tamano_disco = 0
                while bloque := archivo.read(min(tamano_bloque, max_bytes + 1)):
                    tamano_disco += len(bloque)
                    if tamano_disco > max_bytes:
                        raise ErrorTransporteHTTP(TipoErrorHTTP.INTEGRIDAD_LOCAL,
                                                  "El archivo local excede el tamaño permitido")
                    hash_disco.update(bloque)
                if tamano_disco != recibidos or hash_disco.digest() != hash_recibido.digest():
                    raise ErrorTransporteHTTP(TipoErrorHTTP.INTEGRIDAD_LOCAL,
                                              "La relectura local no coincide con los bytes escritos")
        # El enlace es exclusivo: nunca se usa replace ni rename con sobrescritura.
        # Si otro proceso crea el destino, el sistema operativo rechaza la publicación.
        try:
            os.link(temporal, destino)
        except FileExistsError:
            raise ErrorTransporteHTTP(TipoErrorHTTP.DESTINO_EXISTENTE,
                                      "El destino ya existe") from None
    except BaseException as exc:
        restante = _limpiar(temporal)
        if isinstance(exc, (OSError, ErrorTransporteHTTP)):
            tipo = exc.tipo if isinstance(exc, ErrorTransporteHTTP) else TipoErrorHTTP.DISCO
            codigo = getattr(exc, "codigo_http", None) or codigo
            informe = InformeDescarga(origen, datetime.now(timezone.utc), EstadoDescarga.FALLIDA,
                                       recibidos, None, None, codigo, tipo, restante, esperado)
            raise ErrorDescargaArchivo(tipo, informe) from exc
        if restante is not None:
            exc.add_note("No se pudo eliminar un temporal de descarga del directorio controlado")
        raise
    restante = _limpiar(temporal)
    return InformeDescarga(origen, datetime.now(timezone.utc), EstadoDescarga.COMPLETA,
                           recibidos, hash_disco.hexdigest(), destino, codigo,
                           temporal_restante=restante, bytes_declarados=esperado)
