"""GET a staging efímero y continuidad física hasta RAW, sin transacción global."""

from dataclasses import dataclass, replace
from enum import Enum
import os
from pathlib import Path
import re
import shutil
from typing import Mapping, TYPE_CHECKING
from uuid import uuid4

from ..almacenamiento import ActivoRAW, AlmacenRAW, DeclaracionRAW, ErrorAlmacenamientoRAW
from ..almacenamiento.raw import _declaracion_publica, _segura
from ..nucleo import EstadoDescarga
from ..transportes import ClienteHTTP, ErrorTransporteHTTP, InformeDescarga, RegistroIntento

if TYPE_CHECKING:
    from ..catalogo import EvidenciaDocumental


class FaseHTTPRAW(Enum):
    VALIDACION = "validacion"
    DESCARGA = "descarga"
    INCORPORACION = "incorporacion"
    COMPROBACION = "comprobacion"
    COMPLETADA = "completada"


@dataclass(frozen=True)
class ResultadoHTTPRAW:
    informe_http: InformeDescarga
    activo: ActivoRAW
    ruta_verificada: Path
    intentos_http: tuple[RegistroIntento, ...]
    temporal_restante: Path | None = None
    fase: FaseHTTPRAW = FaseHTTPRAW.COMPLETADA


class ErrorIntegracionHTTPRAW(Exception):
    """Solo códigos públicos; nunca guarda la URL, consulta ni excepción de red."""

    def __init__(self, codigo: str, fase: FaseHTTPRAW, *, activo_id: str | None = None,
                 codigo_http: int | None = None, temporal_restante: Path | None = None,
                 intentos_http: tuple[RegistroIntento, ...] = ()):
        super().__init__(codigo)
        self.codigo = codigo
        self.fase = fase
        self.activo_id = activo_id
        self.codigo_http = codigo_http
        self.temporal_restante = temporal_restante
        self.intentos_http = intentos_http


class AdaptadorHTTPRAW:
    """Uso secuencial con clientes/almacén prestados y raíz de staging privada.

    No cierra los componentes recibidos ni ejecuta migraciones de catálogo.
    El operador debe configurar permisos privados sobre el directorio temporal.
    """

    def __init__(self, cliente: ClienteHTTP, almacen: AlmacenRAW, directorio_temporal: Path,
                 *, max_bytes: int, tamano_bloque: int = 65_536):
        if type(max_bytes) is not int or max_bytes <= 0:
            raise ValueError("max_bytes debe ser un entero positivo")
        if type(tamano_bloque) is not int or not 1 <= tamano_bloque <= 1_048_576:
            raise ValueError("tamano_bloque debe estar entre 1 byte y 1 MiB")
        if not cliente.configuracion.verificar_tls:
            raise ValueError("La integración exige verificación TLS activada")
        raiz = _segura(directorio_temporal).resolve(strict=True)
        if (not raiz.is_dir() or raiz.is_relative_to(almacen.raiz)
                or not any(raiz.is_relative_to(p) for p in almacen.entradas)):
            raise ValueError("El staging debe ser un directorio de entrada RAW autorizado")
        self.cliente = cliente
        self.almacen = almacen
        self.temporales = raiz
        self.max_bytes = max_bytes
        self.bloque = tamano_bloque

    def _limpiar(self, operacion: Path | None) -> Path | None:
        if operacion is None:
            return None
        try:
            # Solo el árbol propio, con nombre UUID, debajo de la raíz autorizada.
            # Revalidar antes del borrado recursivo; nunca seguir una raíz enlazada.
            _segura(operacion)
            resuelta = operacion.resolve(strict=True)
            if resuelta.parent != self.temporales or resuelta.name != operacion.name:
                return operacion
            shutil.rmtree(resuelta)
        except (OSError, ErrorAlmacenamientoRAW):
            return operacion
        return None

    def adquirir(self, url: str, declaracion: DeclaracionRAW, *,
                 parametros: Mapping[str, str] | None = None) -> ResultadoHTTPRAW:
        return self._adquirir(url, declaracion, parametros=parametros)

    def adquirir_documentado(self, url: str, declaracion: DeclaracionRAW, evidencia: "EvidenciaDocumental", *,
                            parametros: Mapping[str, str] | None = None) -> ResultadoHTTPRAW:
        """La misma operación HTTP→RAW, con una instantánea documental opcional."""
        if evidencia is None:
            raise ErrorIntegracionHTTPRAW("evidencia_documental_requerida", FaseHTTPRAW.VALIDACION)
        return self._adquirir(url, declaracion, parametros=parametros, evidencia=evidencia)

    def _adquirir(self, url, declaracion, *, parametros=None, evidencia=None):
        fase = FaseHTTPRAW.VALIDACION
        operacion = None
        informe = None
        activo = None
        try:
            if not isinstance(declaracion, DeclaracionRAW):
                raise ValueError("Se requiere DeclaracionRAW")
            if declaracion.procedencia not in (None, url):
                raise ErrorIntegracionHTTPRAW("procedencia_no_coincidente", fase)
            declaracion = replace(declaracion, procedencia=url)
            # Validar sin persistir antes de enviar una solicitud; incorporar vuelve
            # a aplicar el mismo filtro y registra sus advertencias, no secretos.
            _declaracion_publica(declaracion, self.almacen.claves)
            if evidencia is not None:
                from ..catalogo.evidencias import validar_documento
                validar_documento(evidencia, declaracion)
            _segura(self.temporales)
            candidata = self.temporales / ("suadc-http-" + uuid4().hex)
            # Windows hereda ACL del padre privado. POSIX restringe el nuevo directorio.
            candidata.mkdir(mode=0o755 if os.name == "nt" else 0o700)
            operacion = candidata  # Solo se limpia una carpeta creada por esta ejecución.
            fase = FaseHTTPRAW.DESCARGA
            informe = self.cliente.descargar(url, operacion, "descarga.bin",
                max_bytes=self.max_bytes, tamano_bloque=self.bloque, parametros=parametros)
            if (informe.estado is not EstadoDescarga.COMPLETA
                    or informe.ruta_local != operacion / "descarga.bin"
                    or type(informe.bytes_almacenados) is not int or informe.bytes_almacenados < 0
                    or informe.bytes_almacenados > self.max_bytes
                    or not isinstance(informe.sha256, str)
                    or not re.fullmatch(r"[0-9a-f]{64}", informe.sha256)):
                raise ErrorIntegracionHTTPRAW("informe_http_no_utilizable", fase)
            fase = FaseHTTPRAW.INCORPORACION
            if evidencia is None:
                activo = self.almacen.incorporar(informe.ruta_local, declaracion,
                    tamano_esperado=informe.bytes_almacenados, sha256_esperado=informe.sha256)
            else:
                activo = self.almacen.incorporar_documentado(informe.ruta_local, declaracion, evidencia,
                    url_solicitada=url, http_comprobada_utc=informe.fecha_utc,
                    tamano_esperado=informe.bytes_almacenados, sha256_esperado=informe.sha256,
                    consulta_omitida=bool(parametros))
            fase = FaseHTTPRAW.COMPROBACION
            if (activo.tamano, activo.sha256) != (informe.bytes_almacenados, informe.sha256):
                raise ErrorIntegracionHTTPRAW("continuidad_no_coincidente", fase, activo_id=activo.asset_id)
            # recuperar realiza otra lectura física del archivo publicado y comprueba
            # tamaño/hash contra el catálogo antes de entregar una referencia.
            ruta = self.almacen.recuperar(activo.asset_id)
        except BaseException as exc:
            restante = self._limpiar(operacion)
            if not isinstance(exc, Exception):
                if restante is not None:
                    exc.add_note("Quedó un directorio temporal de integración pendiente de limpieza")
                raise
            codigo = (exc.codigo if isinstance(exc, (ErrorAlmacenamientoRAW, ErrorIntegracionHTTPRAW))
                      else exc.tipo.value if isinstance(exc, ErrorTransporteHTTP)
                      else "configuracion_no_admitida" if isinstance(exc, (ValueError, TypeError))
                      else "error_local_integracion")
            raise ErrorIntegracionHTTPRAW(codigo, fase,
                activo_id=getattr(exc, "activo_id", None) or (activo.asset_id if activo else None),
                codigo_http=getattr(exc, "codigo_http", None), temporal_restante=restante,
                intentos_http=self.cliente.historial_intentos if fase is not FaseHTTPRAW.VALIDACION else ()) from None
        restante = self._limpiar(operacion)
        return ResultadoHTTPRAW(informe, activo, ruta, self.cliente.historial_intentos, restante)
