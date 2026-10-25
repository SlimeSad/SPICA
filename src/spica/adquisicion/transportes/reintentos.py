"""Política y ejecución común de reintentos; no abre conexiones HTTP."""

from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import math
import random
from threading import Event
from typing import Callable, TypeVar

from .http import ErrorTransporteHTTP, TipoErrorHTTP

T = TypeVar("T")


@dataclass(frozen=True)
class PoliticaReintentos:
    # Incluye la primera ejecución; optativo para conservar compatibilidad.
    max_intentos: int = 1
    espera_inicial: float = 1.0
    espera_maxima: float = 60.0
    jitter: float = 0.2

    def __post_init__(self) -> None:
        if type(self.max_intentos) is not int or not 1 <= self.max_intentos <= 100:
            raise ValueError("max_intentos debe ser un entero entre 1 y 100")
        for nombre in ("espera_inicial", "espera_maxima", "jitter"):
            valor = getattr(self, nombre)
            if type(valor) not in (int, float) or not math.isfinite(valor) or valor < 0:
                raise ValueError(f"{nombre} debe ser finito y no negativo")
        if self.espera_inicial > self.espera_maxima or self.espera_maxima > 3600 or self.jitter > 1:
            raise ValueError("Se requiere espera_inicial <= espera_maxima <= 3600 y jitter <= 1")


@dataclass(frozen=True)
class RegistroIntento:
    numero: int
    resultado: str
    causa: str | None = None
    codigo_http: int | None = None
    espera: float = 0.0


def interpretar_retry_after(valor: str | None, ahora: datetime) -> float | None:
    """Segundos o fecha HTTP; None significa inválido. No conserva el texto."""
    if valor is None:
        return None
    valor = valor.strip()
    if valor.isascii() and valor.isdecimal():
        # Evita convertir enteros arbitrariamente grandes: siempre excederán el límite.
        digitos = valor.lstrip("0") or "0"
        return float(digitos) if len(digitos) <= 15 else math.inf
    try:
        fecha = parsedate_to_datetime(valor)
        if fecha.utcoffset() is None:
            # El formato HTTP obsoleto asctime no escribe GMT, pero representa UTC.
            fecha = fecha.replace(tzinfo=timezone.utc)
        return max(0.0, (fecha - ahora).total_seconds())
    except (ValueError, TypeError, OverflowError):
        return None


class GestorReintentos:
    """Una ejecución GET completa por intento; historial solo de la última operación."""

    def __init__(
        self, politica: PoliticaReintentos, *, espera: Callable[[float], object] | None = None,
        aleatorio: Callable[[], float] = random.random,
        reloj: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
        cancelacion: Event | None = None,
    ) -> None:
        self.politica = politica
        self.cancelacion = cancelacion if cancelacion is not None else Event()
        self.espera = espera if espera is not None else self.cancelacion.wait
        self.aleatorio = aleatorio
        self.reloj = reloj
        self.historial: tuple[RegistroIntento, ...] = ()

    def comprobar_cancelacion(self) -> None:
        if self.cancelacion.is_set():
            raise ErrorTransporteHTTP(TipoErrorHTTP.CANCELADO, "Operación HTTP cancelada")

    def _demora(self, numero: int, servidor: float | None) -> float | None:
        if servidor is not None and servidor > self.politica.espera_maxima:
            return None
        base = min(self.politica.espera_maxima,
                   self.politica.espera_inicial * (2 ** (numero - 1)))
        muestra = self.aleatorio() if self.politica.jitter else 0.0
        if type(muestra) not in (int, float) or not math.isfinite(muestra) or not 0 <= muestra <= 1:
            raise ValueError("La fuente de jitter debe devolver un número entre 0 y 1")
        retroceso = min(self.politica.espera_maxima, base * (1 + self.politica.jitter * muestra))
        return max(retroceso, servidor or 0.0)

    def ejecutar_get(self, operacion: Callable[[], T]) -> T:
        registros: list[RegistroIntento] = []
        try:
            for numero in range(1, self.politica.max_intentos + 1):
                if self.cancelacion.is_set():
                    registros.append(RegistroIntento(numero - 1, "cancelado", "cancelado"))
                    self.comprobar_cancelacion()
                try:
                    resultado = operacion()
                except ErrorTransporteHTTP as error:
                    recuperable = error.recuperable and not self.cancelacion.is_set()
                    agotado = recuperable and numero == self.politica.max_intentos
                    demora = self._demora(numero, error.espera_servidor) if recuperable and not agotado else None
                    if self.cancelacion.is_set() or error.tipo is TipoErrorHTTP.CANCELADO:
                        final = "cancelado"
                    elif agotado:
                        final = "agotado"
                    elif recuperable:
                        final = "limite_espera" if demora is None else "reintento"
                    else:
                        final = "definitivo"
                    registros.append(RegistroIntento(numero, final, error.tipo.value, error.codigo_http,
                                                      demora if final == "reintento" else 0.0))
                    error.intentos = numero
                    error.agotados = agotado
                    error.historial = tuple(registros)
                    if final != "reintento":
                        raise
                    self.espera(demora)
                else:
                    registros.append(RegistroIntento(numero, "exito", codigo_http=getattr(resultado, "codigo_http", None)))
                    return resultado
        except ErrorTransporteHTTP as error:
            error.intentos = max((r.numero for r in registros), default=0)
            error.historial = tuple(registros)
            raise
        finally:
            self.historial = tuple(registros)
