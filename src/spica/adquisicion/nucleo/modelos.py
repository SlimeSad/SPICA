"""Contrato de adquisición sin conectores ni operaciones de entrada/salida."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from types import MappingProxyType
from typing import Mapping


def _texto(valor: str, nombre: str) -> None:
    if not isinstance(valor, str) or not valor.strip():
        raise ValueError(f"{nombre} debe ser texto no vacío")


class EstadoDescarga(Enum):
    PENDIENTE = "pendiente"
    PARCIAL = "parcial"
    COMPLETA = "completa"
    FALLIDA = "fallida"


class EstadoIntegridad(Enum):
    PENDIENTE = "pendiente"
    VERIFICADA = "verificada"
    FALLIDA = "fallida"


class EstadoRecurso(Enum):
    DESCUBIERTO = "descubierto"
    PARCIAL = "parcial"
    DESCARGADO = "descargado"
    CONFIRMADO = "confirmado"
    FALLIDO = "fallido"


@dataclass(frozen=True)
class Fuente:
    """Identificador original dentro del espacio de nombres del proveedor."""

    proveedor: str
    identificador: str

    def __post_init__(self) -> None:
        _texto(self.proveedor, "proveedor")
        _texto(self.identificador, "identificador")


@dataclass(frozen=True)
class SolicitudAdquisicion:
    fuente: Fuente
    fecha_inicial: datetime
    fecha_final: datetime
    estaciones: tuple[str, ...] = ()
    variables: tuple[str, ...] = ()
    parametros_proveedor: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.fuente, Fuente):
            raise TypeError("fuente debe ser Fuente")
        for fecha in (self.fecha_inicial, self.fecha_final):
            if not isinstance(fecha, datetime) or fecha.utcoffset() is None:
                raise ValueError("Las fechas deben ser datetime con zona horaria")
        if self.fecha_inicial > self.fecha_final:
            raise ValueError("fecha_inicial debe ser anterior o igual a fecha_final")
        for nombre in ("estaciones", "variables"):
            valores = getattr(self, nombre)
            if isinstance(valores, str):
                raise TypeError(f"{nombre} debe ser una colección de identificadores")
            valores = tuple(valores)
            for valor in valores:
                _texto(valor, nombre)
            object.__setattr__(self, nombre, valores)
        parametros = dict(self.parametros_proveedor)
        for clave, valor in parametros.items():
            _texto(clave, "clave de parámetro")
            if not isinstance(valor, str):
                raise TypeError("Los parámetros del proveedor deben ser texto")
        object.__setattr__(self, "parametros_proveedor", MappingProxyType(parametros))


@dataclass(frozen=True)
class RecursoDescubierto:
    fuente: Fuente
    identificador: str
    localizador: str
    tipo_medio: str | None = None
    formato: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.fuente, Fuente):
            raise TypeError("fuente debe ser Fuente")
        _texto(self.identificador, "identificador")
        _texto(self.localizador, "localizador")
        for nombre in ("tipo_medio", "formato"):
            valor = getattr(self, nombre)
            if valor is not None:
                _texto(valor, nombre)


@dataclass(frozen=True)
class Descarga:
    estado: EstadoDescarga = EstadoDescarga.PENDIENTE
    ruta_local: str | None = None
    bytes_recibidos: int | None = None
    error: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.estado, EstadoDescarga):
            raise TypeError("estado debe ser EstadoDescarga")
        if self.bytes_recibidos is not None:
            if type(self.bytes_recibidos) is not int or self.bytes_recibidos < 0:
                raise ValueError("bytes_recibidos debe ser un entero no negativo")
        if self.ruta_local is not None:
            _texto(self.ruta_local, "ruta_local")
        if self.error is not None:
            _texto(self.error, "error")
        if self.estado is EstadoDescarga.PENDIENTE:
            if self.ruta_local is not None or self.bytes_recibidos not in (None, 0):
                raise ValueError("Una descarga pendiente no puede contener ruta ni bytes positivos")
        if self.estado is EstadoDescarga.PARCIAL:
            if self.ruta_local is None or not self.bytes_recibidos or self.error is not None:
                raise ValueError("Una descarga parcial requiere ruta y bytes positivos, sin error")
        if self.bytes_recibidos and self.ruta_local is None:
            raise ValueError("Los bytes recibidos requieren una ruta local")
        if self.estado is EstadoDescarga.COMPLETA:
            if self.ruta_local is None or self.bytes_recibidos is None or self.error:
                raise ValueError("Una descarga completa requiere ruta y tamaño, sin error")
        if self.estado is EstadoDescarga.FALLIDA and self.error is None:
            raise ValueError("Una descarga fallida requiere un error")
        if self.estado is EstadoDescarga.PENDIENTE and self.error is not None:
            raise ValueError("Una descarga pendiente no puede contener un error")


@dataclass(frozen=True)
class Integridad:
    """Evidencia declarada por el ejecutor; este modelo no lee archivos."""

    estado: EstadoIntegridad = EstadoIntegridad.PENDIENTE
    bytes_esperados: int | None = None
    algoritmo: str | None = None
    hash_esperado: str | None = None
    hash_observado: str | None = None
    origen_evidencia: str | None = None
    error: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.estado, EstadoIntegridad):
            raise TypeError("estado debe ser EstadoIntegridad")
        if self.bytes_esperados is not None:
            if type(self.bytes_esperados) is not int or self.bytes_esperados < 0:
                raise ValueError("bytes_esperados debe ser un entero no negativo")
        for nombre in ("algoritmo", "hash_esperado", "hash_observado", "origen_evidencia", "error"):
            valor = getattr(self, nombre)
            if valor is not None:
                _texto(valor, nombre)
        if self.hash_observado is not None and not all((
            self.algoritmo, self.hash_esperado, self.origen_evidencia
        )):
            raise ValueError("Un hash observado requiere algoritmo, hash esperado y origen")
        hashes_distintos = (self.hash_observado is not None
                            and self.hash_observado != self.hash_esperado)
        if hashes_distintos and self.estado is not EstadoIntegridad.FALLIDA:
            raise ValueError("Los hashes contradictorios requieren integridad fallida")
        if self.estado is EstadoIntegridad.VERIFICADA:
            if self.bytes_esperados is None or not all((
                self.algoritmo, self.hash_esperado, self.hash_observado, self.origen_evidencia
            )):
                raise ValueError("Falta evidencia de integridad: tamaño, hashes, algoritmo y origen")
            if self.hash_esperado != self.hash_observado or self.error is not None:
                raise ValueError("La integridad verificada requiere hashes iguales y ningún error")
        if self.estado is EstadoIntegridad.FALLIDA and self.error is None:
            raise ValueError("La integridad fallida requiere un error")
        if self.estado is EstadoIntegridad.FALLIDA and not hashes_distintos:
            raise ValueError("La integridad fallida requiere evidencia de hashes distintos")
        if self.estado is EstadoIntegridad.PENDIENTE and self.error is not None:
            raise ValueError("La integridad pendiente no puede contener un error")


@dataclass(frozen=True)
class ResultadoRecurso:
    recurso: RecursoDescubierto
    descarga: Descarga = field(default_factory=Descarga)
    integridad: Integridad = field(default_factory=Integridad)

    def __post_init__(self) -> None:
        if not isinstance(self.recurso, RecursoDescubierto):
            raise TypeError("recurso debe ser RecursoDescubierto")
        if not isinstance(self.descarga, Descarga) or not isinstance(self.integridad, Integridad):
            raise TypeError("Se requieren modelos Descarga e Integridad")
        if self.descarga.estado is not EstadoDescarga.COMPLETA:
            if (self.integridad.estado is not EstadoIntegridad.PENDIENTE
                    or self.integridad.hash_observado is not None):
                raise ValueError("La verificación de integridad requiere una descarga completa")
        esperado = self.integridad.bytes_esperados
        recibido = self.descarga.bytes_recibidos
        if esperado is not None:
            if self.descarga.estado is EstadoDescarga.COMPLETA and recibido != esperado:
                raise ValueError("Una descarga completa debe coincidir con el tamaño esperado")
            if self.descarga.estado is EstadoDescarga.PARCIAL and recibido > esperado:
                raise ValueError("Los bytes parciales no pueden exceder el tamaño esperado")
        if self.integridad.estado is EstadoIntegridad.VERIFICADA:
            if self.descarga.estado is not EstadoDescarga.COMPLETA:
                raise ValueError("Verificar integridad requiere una descarga completa")
            if self.descarga.bytes_recibidos != self.integridad.bytes_esperados:
                raise ValueError("El tamaño recibido no coincide con el esperado")

    @property
    def estado(self) -> EstadoRecurso:
        if (self.descarga.estado is EstadoDescarga.FALLIDA
                or self.integridad.estado is EstadoIntegridad.FALLIDA):
            return EstadoRecurso.FALLIDO
        if self.integridad.estado is EstadoIntegridad.VERIFICADA:
            return EstadoRecurso.CONFIRMADO
        if self.descarga.estado is EstadoDescarga.COMPLETA:
            return EstadoRecurso.DESCARGADO
        if self.descarga.estado is EstadoDescarga.PARCIAL:
            return EstadoRecurso.PARCIAL
        return EstadoRecurso.DESCUBIERTO


@dataclass(frozen=True)
class ResultadoAdquisicion:
    """Colección de estados por recurso y errores de descubrimiento/ejecución."""

    solicitud: SolicitudAdquisicion
    recursos: tuple[ResultadoRecurso, ...] = ()
    errores: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.solicitud, SolicitudAdquisicion):
            raise TypeError("solicitud debe ser SolicitudAdquisicion")
        object.__setattr__(self, "recursos", tuple(self.recursos))
        if isinstance(self.errores, str):
            raise TypeError("errores debe ser una colección de textos")
        object.__setattr__(self, "errores", tuple(self.errores))
        for resultado in self.recursos:
            if not isinstance(resultado, ResultadoRecurso):
                raise TypeError("recursos debe contener ResultadoRecurso")
            if resultado.recurso.fuente != self.solicitud.fuente:
                raise ValueError("El recurso debe pertenecer a la fuente solicitada")
        for error in self.errores:
            _texto(error, "error")
