"""Cota de trabajo sobre descriptores; no serialización, reserva o medición RSS."""

from dataclasses import fields, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum


def medir_descriptores(composicion, cancelacion):
    visitas = texto = 0
    activos = set()
    limites = composicion.limites

    def visitar(v, profundidad=0):
        nonlocal visitas, texto
        visitas += 1
        if cancelacion is not None and cancelacion.is_set():
            raise InterruptedError
        if visitas > limites.max_visitas_descriptores or profundidad > 64:
            raise ValueError("cota_visitas_descriptores_excedida")
        if type(v) is str:
            if len(v) > limites.max_bytes_texto - texto:
                raise ValueError("cota_texto_descriptores_excedida")
            for i in range(0, len(v), 4096):
                texto += len(v[i:i + 4096].encode("utf-8"))
                if texto > limites.max_bytes_texto:
                    raise ValueError("cota_texto_descriptores_excedida")
        elif v is None or type(v) in (bool, int, float, Decimal, date, datetime) or isinstance(v, Enum):
            pass
        elif type(v) is tuple or is_dataclass(v) and not isinstance(v, type) and type(v).__module__.startswith("spica."):
            if id(v) in activos:
                raise ValueError("ciclo_en_descriptores")
            activos.add(id(v))
            try:
                valores = v if type(v) is tuple else (getattr(v, f.name) for f in fields(v))
                for elemento in valores:
                    visitar(elemento, profundidad + 1)
            finally:
                activos.remove(id(v))
        else:
            raise ValueError("descriptor_no_admitido")
    try:
        visitar(composicion)
    except InterruptedError:
        return visitas, None, "cancelacion_inspeccion_observada"
    except (ValueError, UnicodeError) as error:
        # Solo códigos propios; nunca se copia texto de evidencia en diagnósticos.
        admitidos = ("cota_visitas_descriptores_excedida", "cota_texto_descriptores_excedida",
                     "ciclo_en_descriptores", "descriptor_no_admitido")
        codigo = (error.args[0] if type(error) is ValueError and error.args and error.args[0] in admitidos
                  else "texto_descriptor_no_codificable")
        return visitas, None, codigo
    return visitas, texto, None
