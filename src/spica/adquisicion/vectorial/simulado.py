"""Única fuente ejecutable del prototipo: secuencia perezosa de bytes inventados."""

from dataclasses import replace
from typing import Iterable, final

from .modelos import RespuestaSintetica, SolicitudPagina


@final
class TransporteSintetico:
    """Sin URL, cliente, backend, callback de conexión ni acceso a disco.

    Consume una fixture por petición. Usar un generador para no retener páginas;
    si el llamador entrega una lista, esa memoria pertenece al llamador.
    No garantiza seguridad frente a Python malicioso ejecutado por el llamador.
    """

    def __init__(self, respuestas: Iterable[RespuestaSintetica]):
        self._respuestas = iter(respuestas)
        self.intentos = 0

    def recibir(self, solicitud: SolicitudPagina) -> RespuestaSintetica | None:
        if type(solicitud) is not SolicitudPagina:
            raise TypeError("Solicitud de página requerida")
        try:
            r = next(self._respuestas)
        except StopIteration:
            return None
        self.intentos += 1
        if type(r) is not RespuestaSintetica:
            raise TypeError("La fixture debe producir respuestas sintéticas")
        return replace(r, solicitud=solicitud) if r.solicitud is None else r
