"""Fachada pública de las interpretaciones ya utilizadas por el perfilador.

No recorre archivos, reconstruye textos ni aplica criterios científicos.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from .meteorologico import _dia, _interpretar, _patron_hora
from .modelos import LimitesPerfil

VERSION_INTERPRETACION = "1.0.0"


@dataclass(frozen=True)
class InterpretacionNumerica:
    clase: str
    numero: Decimal | None
    notaciones: tuple[str, ...]


def interpretar_numero(texto: str, *, limites: LimitesPerfil | None = None) -> InterpretacionNumerica:
    if not isinstance(texto, str):
        raise TypeError("Se requiere texto original")
    politica = limites if limites is not None else LimitesPerfil()
    if not isinstance(politica, LimitesPerfil):
        raise TypeError("Se requiere LimitesPerfil")
    return InterpretacionNumerica(*_interpretar(texto, politica))


def interpretar_fecha_civil(texto: str) -> date | None:
    if not isinstance(texto, str):
        raise TypeError("Se requiere texto original")
    return _dia(texto)


def clasificar_hora_literal(texto: str) -> str:
    if not isinstance(texto, str):
        raise TypeError("Se requiere texto original")
    return _patron_hora(texto)
