"""Criterio común para instantes absolutos; no localiza fechas civiles."""

from datetime import datetime, timezone


def instante_utc(fecha: datetime) -> datetime:
    """Clave cronológica validada, sin modificar el datetime original.

    La vuelta por UTC detecta horas locales inexistentes. No se usa igualdad
    aware para esa comprobación: Python ignora fold con tzinfo compartido.
    """
    if not isinstance(fecha, datetime) or fecha.utcoffset() is None:
        raise ValueError("Se requiere datetime con desplazamiento horario conocido")
    try:
        instante = fecha.astimezone(timezone.utc)
        vuelta = instante.astimezone(fecha.tzinfo)
        if (vuelta.replace(tzinfo=None) != fecha.replace(tzinfo=None)
                or vuelta.utcoffset() != fecha.utcoffset()):
            raise ValueError("Hora local inexistente o zona horaria incoherente")
    except OverflowError:
        raise ValueError("Instante fuera del rango temporal admitido") from None
    return instante


def validar_intervalo(inicio: datetime, fin: datetime, *, permitir_civil: bool = False) -> None:
    """Valida orden real o, solo para metadatos sin zona, orden civil."""
    if not isinstance(inicio, datetime) or not isinstance(fin, datetime):
        raise ValueError("Los extremos deben ser datetime")
    zonas = (inicio.utcoffset() is not None, fin.utcoffset() is not None)
    if zonas == (True, True):
        primero, ultimo = instante_utc(inicio), instante_utc(fin)
    elif zonas == (False, False) and permitir_civil:
        # No constituye disponibilidad absoluta ni autoriza asignar una zona.
        primero, ultimo = inicio.replace(tzinfo=None), fin.replace(tzinfo=None)
    else:
        raise ValueError("Los extremos requieren información de zona coherente y conocida")
    if primero > ultimo:
        raise ValueError("Intervalo temporal invertido")
