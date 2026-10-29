"""Transporte GET síncrono compartido por respuestas pequeñas y descargas a disco."""

from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
import math
import ssl
from datetime import datetime
from threading import Event
from types import MappingProxyType
from typing import Callable, Iterator, Mapping, TYPE_CHECKING
from pathlib import Path

import httpx

if TYPE_CHECKING:
    from .descargas import InformeDescarga
    from .reintentos import PoliticaReintentos, RegistroIntento


class TipoErrorHTTP(Enum):
    TIMEOUT = "timeout"
    CONEXION = "conexion"
    TRANSPORTE = "transporte"
    NO_AUTENTICADO = "no_autenticado"
    PROHIBIDO = "prohibido"
    NO_ENCONTRADO = "no_encontrado"
    LIMITE_SOLICITUDES = "limite_solicitudes"
    SERVIDOR = "servidor"
    ESTADO_HTTP = "estado_http"
    REDIRECCION = "redireccion"
    RESPUESTA_PARCIAL = "respuesta_parcial"
    TAMANO_EXCEDIDO = "tamano_excedido"
    RESPUESTA_INVALIDA = "respuesta_invalida"
    DISCO = "disco"
    DESTINO_EXISTENTE = "destino_existente"
    INTEGRIDAD_LOCAL = "integridad_local"
    TLS = "tls"
    CANCELADO = "cancelado"


class ErrorTransporteHTTP(Exception):
    """Error técnico sin cuerpo, URL ni parámetros potencialmente sensibles."""

    def __init__(self, tipo: TipoErrorHTTP, mensaje: str, codigo_http: int | None = None,
                 *, recuperable: bool = False, espera_servidor: float | None = None):
        super().__init__(mensaje)
        self.tipo = tipo
        self.codigo_http = codigo_http
        self.recuperable = recuperable
        self.espera_servidor = espera_servidor
        self.intentos = 0
        self.agotados = False
        self.historial = ()
        self.fase: str | None = None

    def diagnostico_publico(self) -> dict:
        """Campos técnicos permitidos; no serializa requests, frames ni cabeceras."""
        return {"tipo": self.tipo.value, "codigo_http": self.codigo_http,
                "fase": self.fase, "intentos": self.intentos, "agotados": self.agotados,
                "recuperable": self.recuperable}


def _error_publico(interno: ErrorTransporteHTTP, fase: str) -> ErrorTransporteHTTP:
    # No propagar el objeto original: puede conservar causas, notas y traceback
    # de HTTPX, del sistema operativo o del backend TLS.
    from .descargas import ErrorDescargaArchivo
    if isinstance(interno, ErrorDescargaArchivo):
        publico = ErrorDescargaArchivo(interno.tipo, interno.informe)
    else:
        publico = ErrorTransporteHTTP(interno.tipo, "Fallo HTTP: " + interno.tipo.value,
                                     interno.codigo_http)
    for atributo in ("recuperable", "espera_servidor", "intentos", "agotados", "historial"):
        setattr(publico, atributo, getattr(interno, atributo))
    publico.fase = fase
    return publico


def _publicar_error(error: Exception):
    # Python adjunta automáticamente el contexto activo incluso con `from None`.
    # Capturamos nuestro error nuevo y retiramos esa referencia antes del bare raise.
    try:
        raise error from None
    except Exception:
        error.__cause__ = None
        error.__context__ = None
        raise


@dataclass(frozen=True)
class ConfiguracionHTTP:
    timeout_conexion: float = 10.0
    timeout_lectura: float = 30.0
    timeout_escritura: float = 30.0
    timeout_pool: float = 10.0
    verificar_tls: bool = True
    max_bytes_respuesta: int = 1_048_576

    def __post_init__(self) -> None:
        for nombre in ("timeout_conexion", "timeout_lectura", "timeout_escritura", "timeout_pool"):
            valor = getattr(self, nombre)
            if type(valor) not in (int, float) or not math.isfinite(valor) or valor <= 0:
                raise ValueError(f"{nombre} debe ser finito y positivo")
        if type(self.verificar_tls) is not bool:
            raise TypeError("verificar_tls debe ser bool")
        if type(self.max_bytes_respuesta) is not int or self.max_bytes_respuesta <= 0:
            raise ValueError("max_bytes_respuesta debe ser un entero positivo")


@dataclass(frozen=True)
class RespuestaHTTP:
    codigo_http: int
    cabeceras: Mapping[str, str]
    contenido: bytes


def _url_autorizable(valor: str) -> httpx.URL:
    try:
        url = httpx.URL(valor)
    except (httpx.InvalidURL, TypeError):
        publico = ValueError("URL inválida")
    else:
        publico = None
    if publico is not None:
        _publicar_error(publico)
    if (url.scheme not in ("http", "https") or not url.host
            or url.userinfo or url.fragment):
        raise ValueError("Se requiere URL HTTP(S) absoluta, sin credenciales ni fragmento")
    return url


def _origen(url: httpx.URL) -> tuple[str, str, int]:
    return (url.scheme, url.host, url.port or (443 if url.scheme == "https" else 80))


def _error_tls(error: BaseException) -> bool:
    pendientes = [error]
    vistos = set()
    while pendientes:
        actual = pendientes.pop()
        if id(actual) in vistos:
            continue
        vistos.add(id(actual))
        if isinstance(actual, ssl.SSLError):
            return True
        # Algunos backends solo conservan el diagnóstico textual del certificado.
        texto = str(actual).lower()
        if any(marca in texto for marca in ("certificate", "certificado", "ssl", "tls")):
            return True
        pendientes.extend(e for e in (actual.__cause__, actual.__context__) if e is not None)
    return False


class ClienteHTTP:
    """El llamador autoriza el recurso; la lista de orígenes limita sus destinos.

    El cliente es dueño de su transporte y debe cerrarse o usarse con ``with``.
    Las redirecciones y los proxies del entorno están desactivados explícitamente.
    """

    def __init__(
        self,
        origenes_permitidos: tuple[str, ...],
        configuracion: ConfiguracionHTTP | None = None,
        *,
        transporte: httpx.BaseTransport | None = None,
        politica_reintentos: "PoliticaReintentos | None" = None,
        espera: Callable[[float], object] | None = None,
        aleatorio: Callable[[], float] | None = None,
        reloj: Callable[[], datetime] | None = None,
        cancelacion: Event | None = None,
    ) -> None:
        if isinstance(origenes_permitidos, str) or not origenes_permitidos:
            raise ValueError("Se requiere una colección no vacía de orígenes autorizados")
        origenes = set()
        for valor in origenes_permitidos:
            url = _url_autorizable(valor)
            if url.path != "/" or url.query:
                raise ValueError("Los orígenes no deben contener rutas ni consultas")
            origenes.add(_origen(url))
        self._origenes = frozenset(origenes)
        from .reintentos import GestorReintentos, PoliticaReintentos
        opciones = {}
        if aleatorio is not None:
            opciones["aleatorio"] = aleatorio
        if reloj is not None:
            opciones["reloj"] = reloj
        self._gestor = GestorReintentos(politica_reintentos or PoliticaReintentos(),
                                        espera=espera, cancelacion=cancelacion, **opciones)
        self.configuracion = configuracion or ConfiguracionHTTP()
        config = self.configuracion
        self._cliente = httpx.Client(
            timeout=httpx.Timeout(connect=config.timeout_conexion, read=config.timeout_lectura,
                                  write=config.timeout_escritura, pool=config.timeout_pool),
            verify=config.verificar_tls,
            follow_redirects=False,
            trust_env=False,
            headers={"Accept-Encoding": "identity"},
            transport=transporte,
        )

    def __enter__(self) -> "ClienteHTTP":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def close(self) -> None:
        self._cliente.close()

    @property
    def historial_intentos(self) -> "tuple[RegistroIntento, ...]":
        return self._gestor.historial

    def cancelar(self) -> None:
        """Cancelación cooperativa persistente para las operaciones de este cliente."""
        self._gestor.cancelacion.set()

    def get(self, url: str, *, parametros: Mapping[str, str] | None = None) -> RespuestaHTTP:
        try:
            return self._gestor.ejecutar_get(lambda: self._get_una_vez(url, parametros=parametros))
        except ErrorTransporteHTTP as interno:
            publico = _error_publico(interno, "get")
        _publicar_error(publico)

    def _get_una_vez(self, url: str, *, parametros: Mapping[str, str] | None) -> RespuestaHTTP:
        with self._abrir(url, parametros, self.configuracion.max_bytes_respuesta) as (respuesta, esperado):
            contenido = bytearray()
            bloque = min(65_536, self.configuracion.max_bytes_respuesta + 1)
            for parte in self._bloques(respuesta, esperado, self.configuracion.max_bytes_respuesta, bloque):
                contenido.extend(parte)
            return RespuestaHTTP(respuesta.status_code,
                                 MappingProxyType(dict(respuesta.headers)), bytes(contenido))

    def descargar(
        self, url: str, directorio: Path, nombre: str, *, max_bytes: int,
        tamano_bloque: int = 65_536, parametros: Mapping[str, str] | None = None,
    ) -> "InformeDescarga":
        """Descarga a staging controlado; no confirma ni almacena un original RAW."""
        from .descargas import descargar_archivo
        try:
            return self._gestor.ejecutar_get(lambda: descargar_archivo(
                self, url, directorio, nombre, max_bytes=max_bytes,
                tamano_bloque=tamano_bloque, parametros=parametros))
        except ErrorTransporteHTTP as interno:
            publico = _error_publico(interno, "descargar")
        _publicar_error(publico)

    @contextmanager
    def _abrir(
        self, url: str, parametros: Mapping[str, str] | None, limite: int,
    ) -> Iterator[tuple[httpx.Response, int | None]]:
        """Única política de autorización, HTTP, compresión y errores de red."""
        destino = _url_autorizable(url)
        if _origen(destino) not in self._origenes:
            raise ValueError("El origen del recurso no está autorizado")
        if parametros is not None:
            if not isinstance(parametros, Mapping) or any(
                not isinstance(k, str) or not isinstance(v, str) for k, v in parametros.items()
            ):
                raise TypeError("Los parámetros de consulta deben ser texto/texto")
        try:
            self._gestor.comprobar_cancelacion()
            with self._cliente.stream("GET", destino, params=parametros) as respuesta:
                try:
                    self._validar_estado(respuesta.status_code)
                except ErrorTransporteHTTP as error:
                    if error.recuperable:
                        from .reintentos import interpretar_retry_after
                        error.espera_servidor = interpretar_retry_after(
                            respuesta.headers.get("retry-after"), self._gestor.reloj())
                    raise
                # No se descomprime: evita expandir un cuerpo comprimido antes de limitarlo.
                if respuesta.headers.get("content-encoding", "identity").lower() != "identity":
                    raise ErrorTransporteHTTP(TipoErrorHTTP.RESPUESTA_INVALIDA,
                                              "La respuesta comprimida no está admitida")
                longitud = respuesta.headers.get("content-length")
                esperado = None
                if longitud is not None:
                    if not longitud.isascii() or not longitud.isdecimal():
                        raise ErrorTransporteHTTP(TipoErrorHTTP.RESPUESTA_INVALIDA,
                                                  "Content-Length inválido")
                    longitud = longitud.lstrip("0") or "0"
                    if len(longitud) > len(str(limite)):
                        raise ErrorTransporteHTTP(TipoErrorHTTP.TAMANO_EXCEDIDO,
                                                  "La respuesta excede el límite configurado")
                    esperado = int(longitud)
                    if esperado > limite:
                        raise ErrorTransporteHTTP(TipoErrorHTTP.TAMANO_EXCEDIDO,
                                                  "La respuesta excede el límite configurado")
                yield respuesta, esperado
        except httpx.TimeoutException as exc:
            if _error_tls(exc):
                raise ErrorTransporteHTTP(TipoErrorHTTP.TLS, "Fallo TLS") from exc
            raise ErrorTransporteHTTP(TipoErrorHTTP.TIMEOUT, "Tiempo de espera HTTP agotado",
                                      recuperable=True) from exc
        except httpx.ConnectError as exc:
            if _error_tls(exc):
                raise ErrorTransporteHTTP(TipoErrorHTTP.TLS, "Fallo TLS") from exc
            raise ErrorTransporteHTTP(TipoErrorHTTP.CONEXION, "No se pudo conectar",
                                      recuperable=True) from exc
        except httpx.RequestError as exc:
            if _error_tls(exc):
                raise ErrorTransporteHTTP(TipoErrorHTTP.TLS, "Fallo TLS") from exc
            raise ErrorTransporteHTTP(TipoErrorHTTP.TRANSPORTE, "Fallo del transporte HTTP",
                                      recuperable=isinstance(exc, (httpx.ReadError, httpx.WriteError,
                                                                   httpx.RemoteProtocolError))) from exc

    def _bloques(
        self, respuesta: httpx.Response, esperado: int | None, limite: int, bloque: int,
    ) -> Iterator[bytes]:
        recibido = 0
        for parte in respuesta.iter_raw(chunk_size=bloque):
            self._gestor.comprobar_cancelacion()
            recibido += len(parte)
            if recibido > limite:
                raise ErrorTransporteHTTP(TipoErrorHTTP.TAMANO_EXCEDIDO,
                                          "La respuesta excede el límite configurado")
            if esperado is not None and recibido > esperado:
                raise ErrorTransporteHTTP(TipoErrorHTTP.RESPUESTA_INVALIDA,
                                          "El tamaño recibido difiere de Content-Length")
            yield parte
        if esperado is not None and recibido != esperado:
            raise ErrorTransporteHTTP(TipoErrorHTTP.RESPUESTA_INVALIDA,
                                      "El tamaño recibido difiere de Content-Length", recuperable=True)
        self._gestor.comprobar_cancelacion()

    @staticmethod
    def _validar_estado(codigo: int) -> None:
        if 300 <= codigo < 400:
            tipo = TipoErrorHTTP.REDIRECCION
        elif codigo == 206:
            tipo = TipoErrorHTTP.RESPUESTA_PARCIAL
        elif 200 <= codigo < 300:
            return
        else:
            tipo = {
                401: TipoErrorHTTP.NO_AUTENTICADO,
                403: TipoErrorHTTP.PROHIBIDO,
                404: TipoErrorHTTP.NO_ENCONTRADO,
                429: TipoErrorHTTP.LIMITE_SOLICITUDES,
            }.get(codigo, TipoErrorHTTP.SERVIDOR if 500 <= codigo < 600
                  else TipoErrorHTTP.ESTADO_HTTP)
        raise ErrorTransporteHTTP(tipo, f"Respuesta HTTP no aceptada: {codigo}", codigo,
                                  recuperable=codigo in (408, 429, 500, 502, 503, 504))
