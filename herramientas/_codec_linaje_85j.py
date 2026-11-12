"""Codec cerrado del piloto 85-G/H; no importa clases elegidas por el documento."""

from dataclasses import fields, is_dataclass
from datetime import datetime, timezone
from enum import Enum
import json
import math
from pathlib import Path
from types import MappingProxyType

from herramientas import piloto_integracion_85g as h
from spica.adquisicion.almacenamiento.modelos import ActivoRAW, DeclaracionRAW, EstadoIncorporacion
from spica.adquisicion.catalogo.documental import RecursoCatalogo, RegistroRecurso
from spica.adquisicion.catalogo.modelos import ProcedenciaCatalogo
from spica.adquisicion.integracion.http_raw import FaseHTTPRAW, ResultadoHTTPRAW
from spica.adquisicion.nucleo.modelos import EstadoDescarga, Fuente
from spica.adquisicion.transportes.descargas import InformeDescarga
from spica.adquisicion.transportes.reintentos import RegistroIntento
from spica.adquisicion.verificacion.csv_streaming import InformeLecturaCSV, PoliticaLecturaCSV
from spica.adquisicion.verificacion.modelos import (
    DetalleCSV, EstadoEstructura, PoliticaEstructura, ResultadoEstructura,
)
from spica.calidad.conciliacion_lotes import (
    EstadoConciliacionQA, HallazgoLotesQA, InformeConciliacionQA, ResumenLoteQA,
)
from spica.calidad.consumo import EstadoConsumoQA, InformeConsumoQA
from spica.calidad.modelos import (
    CategoriaQA, ConfiguracionQA, EstadoEvaluacionQA, EstadoResultadoQA, InformeQA,
    LimitesQA, ProcedenciaQA, RegistroQA, ReglaQA, ResultadoQA,
)
from spica.perfilado.modelos import LimitesPerfil

VERSION_CODEC = "0.1.0"
_CLASES = (
    h.ContratoEjecucion85G, h.EstadoEjecucion85G, h.InformeEjecucion85G, h.Presupuesto85G,
    ActivoRAW, DeclaracionRAW, EstadoIncorporacion, RecursoCatalogo, RegistroRecurso,
    ProcedenciaCatalogo, FaseHTTPRAW, ResultadoHTTPRAW, EstadoDescarga, Fuente,
    InformeDescarga, RegistroIntento, InformeLecturaCSV, PoliticaLecturaCSV, DetalleCSV,
    EstadoEstructura, PoliticaEstructura, ResultadoEstructura, EstadoConciliacionQA,
    HallazgoLotesQA, InformeConciliacionQA, ResumenLoteQA, EstadoConsumoQA, InformeConsumoQA,
    CategoriaQA, ConfiguracionQA, EstadoEvaluacionQA, EstadoResultadoQA, InformeQA,
    LimitesQA, ProcedenciaQA, RegistroQA, ReglaQA, ResultadoQA, LimitesPerfil,
)
_REGISTRO = {c.__module__ + ":" + c.__name__: c for c in _CLASES}
_NOMBRES = {c: n for n, c in _REGISTRO.items()}


def canonico(dato):
    return json.dumps(dato, ensure_ascii=False, sort_keys=True, allow_nan=False,
                      separators=(",", ":")).encode("utf-8")


def leer_json(datos, *, profundidad=48, nodos=250_000):
    """Cotas antes de parsear, también para una entrada de JSON profundamente anidada."""
    texto = datos.decode("utf-8", errors="strict")
    nivel = 0
    cadena = escape = False
    for c in texto:
        if cadena:
            if escape:
                escape = False
            elif c == "\\":
                escape = True
            elif c == '"':
                cadena = False
        elif c == '"':
            cadena = True
        elif c in "[{":
            nivel += 1
            if nivel > profundidad:
                raise ValueError("profundidad_excedida")
        elif c in "]}":
            nivel -= 1
    def pares(valores):
        d = {}
        for k, v in valores:
            if k in d:
                raise ValueError("clave_duplicada")
            d[k] = v
        return d
    def constante(_):
        raise ValueError("numero_no_finito")
    d = json.loads(texto, object_pairs_hook=pares, parse_constant=constante)
    pendientes = [d]
    usados = 0
    while pendientes:
        v = pendientes.pop()
        usados += 1
        if usados > nodos:
            raise ValueError("nodos_excedidos")
        if type(v) is dict:
            pendientes.extend(v.values())
        elif type(v) is list:
            pendientes.extend(v)
        elif type(v) is float and not math.isfinite(v):
            raise ValueError("numero_no_finito")
    return d


def codificar(informe, *, profundidad=48, nodos=250_000):
    usados = 0
    def dato(v, nivel=0):
        nonlocal usados
        usados += 1
        if nivel > profundidad or usados > nodos:
            raise ValueError("presupuesto_codec_excedido")
        if v is None or type(v) in (str, int, bool):
            return v
        if type(v) is float and math.isfinite(v):
            return v
        if type(v) is datetime:
            if v.utcoffset() is None or v.utcoffset().total_seconds() != 0 or v.fold:
                raise ValueError("solo_fecha_utc_sintetica_admitida")
            return {"t": "utc", "v": v.isoformat()}
        if isinstance(v, Path):
            # Metadato histórico inerte. El lector no usa esta ruta para E/S.
            return {"t": "ruta_historica", "v": str(v)}
        if type(v) in _NOMBRES:
            nombre = _NOMBRES[type(v)]
            if isinstance(v, Enum):
                return {"t": "enum", "c": nombre, "v": v.value}
            if is_dataclass(v):
                return {"t": "dc", "c": nombre,
                        "v": {f.name: dato(getattr(v, f.name), nivel + 1) for f in fields(v)}}
        if type(v) in (tuple, list):
            return {"t": "tuple" if type(v) is tuple else "list",
                    "v": [dato(x, nivel + 1) for x in v]}
        if type(v) in (dict, MappingProxyType) and all(type(k) is str for k in v):
            return {"t": "dict" if type(v) is dict else "mapping",
                    "v": {k: dato(x, nivel + 1) for k, x in v.items()}}
        raise ValueError("tipo_codec_no_admitido")
    return canonico({"version": VERSION_CODEC, "informe": dato(informe)})


def decodificar(datos, *, profundidad=48, nodos=250_000):
    sobre = leer_json(datos, profundidad=profundidad, nodos=nodos)
    if type(sobre) is not dict or set(sobre) != {"version", "informe"} or sobre["version"] != VERSION_CODEC:
        raise ValueError("version_codec_incompatible")
    def valor(v):
        if v is None or type(v) in (str, int, bool, float):
            return v
        if type(v) is not dict or "t" not in v or "v" not in v:
            raise ValueError("nodo_codec_invalido")
        t, cuerpo = v["t"], v["v"]
        if t in ("dc", "enum"):
            if set(v) != {"t", "c", "v"} or type(v["c"]) is not str or v["c"] not in _REGISTRO:
                raise ValueError("clase_no_admitida")
            clase = _REGISTRO[v["c"]]
            if t == "enum" and issubclass(clase, Enum):
                return clase(cuerpo)
            if t != "dc" or not is_dataclass(clase) or type(cuerpo) is not dict:
                raise ValueError("tipo_codec_incoherente")
            fs = fields(clase)
            if set(cuerpo) != {f.name for f in fs}:
                raise ValueError("campos_codec_incompatibles")
            valores = {k: valor(x) for k, x in cuerpo.items()}
            objeto = clase(**{f.name: valores[f.name] for f in fs if f.init})
            if any(getattr(objeto, f.name) != valores[f.name] for f in fs if not f.init):
                raise ValueError("campo_fijo_contradictorio")
            return objeto
        if set(v) != {"t", "v"}:
            raise ValueError("campos_codec_incompatibles")
        if t in ("tuple", "list") and type(cuerpo) is list:
            xs = [valor(x) for x in cuerpo]
            return tuple(xs) if t == "tuple" else xs
        if t in ("dict", "mapping") and type(cuerpo) is dict:
            d = {k: valor(x) for k, x in cuerpo.items()}
            return MappingProxyType(d) if t == "mapping" else d
        if t == "utc" and type(cuerpo) is str:
            fecha = datetime.fromisoformat(cuerpo)
            if fecha.tzinfo != timezone.utc or fecha.fold:
                raise ValueError("fecha_no_admitida")
            return fecha
        if t == "ruta_historica" and type(cuerpo) is str:
            return Path(cuerpo)
        raise ValueError("nodo_codec_invalido")
    informe = valor(sobre["informe"])
    if type(informe) is not h.InformeEjecucion85G:
        raise ValueError("informe_tipado_requerido")
    return informe
