"""Perfil cerrado RC6. Referencias compartidas, sin importación elegida por JSON."""

from dataclasses import fields, is_dataclass
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from enum import Enum
import json
import math
from functools import lru_cache
from types import UnionType
from typing import get_args, get_origin, get_type_hints

from ..adquisicion.almacenamiento import modelos as md
from ..adquisicion.catalogo import modelos as cat
from ..adquisicion.nucleo import modelos as nuc
from ..adquisicion.readquisicion import modelos as rea
from ..adquisicion.vectorial.modelos import ReferenciaEspacial
from ..calidad import modelos as qa
from ..calidad import restricciones as pol
from ..contextos import modelos as ctx
from ..coordinacion import modelos as coo
from ..interoperabilidad import modelos as inter
from ..interoperabilidad import adaptadores as ada
from ..interoperabilidad.perfiles import modelos as per
from . import modelos as art
from . import materializacion as mat

VERSION = "rc6.generacion.0.1.0"
MAX_METADATOS = 2_097_152
MAX_NODOS = 50_000
MAX_PROFUNDIDAD = 64

# Lista literal: añadir un tipo requiere revisar/versionar este perfil. No se
# importan módulos ni se evalúan expresiones suministradas por el documento.
_GRUPOS = (
    (md, "ProyectoCientifico ObjetoCientifico"),
    (cat, "ProcedenciaCatalogo EstadoVerificacion VariableCatalogo"),
    (nuc, "Fuente"), (rea, "EvidenciaLocal EstadoLocal"),
    (qa, "EstadoEvaluacionQA"), (pol, "RestriccionQA TipoRestriccionQA"),
    (ctx, "ConfiguracionContexto ContextoProyecto ContextoEntrada ContextoOperacion TipoOperacion EstadoOperacion"),
    (coo, "LimitesComposicion DependenciaOperacion RequisitoCompatibilidad NodoOperacion ComposicionOperaciones RestriccionPropagada"),
    (inter, "Respaldo IdentidadRecurso CRSDeclarado MarcoEspacial PeriodoTemporal MarcoTemporal RecursoInteroperable RepresentacionEspacial AmbitoCRS DimensionEvaluacion"),
    (ada, "DiagnosticoAdaptacion NivelDiagnostico"),
    (per, "DeclaracionPerfil UnidadPerfil EstadoUnidad CampoInformacion PerfilInformacion AspectoCampo FinalidadCompatibilidad EntradaPerfil"),
    (art, "ReferenciaArtefacto DescriptorArtefacto TipoArtefacto EstadoArtefacto ProduccionArtefactos InventarioArtefactos"),
    (mat, "LimitesMaterializacion SolicitudMaterializacion ReferenciaFisica InformeVerificacion InformeMaterializacion EstadoPublicacion"),
)
_CLASES = tuple(getattr(m, n) for m, ns in _GRUPOS for n in ns.split()) + (ReferenciaEspacial,)
_REGISTRO = {c.__module__ + ":" + c.__name__: c for c in _CLASES}
_NOMBRES = {c: n for n, c in _REGISTRO.items()}


def canonico(v):
    return json.dumps(v, ensure_ascii=False, sort_keys=True, allow_nan=False,
                      separators=(",", ":")).encode("utf-8")


def leer_json(datos):
    if type(datos) is not bytes or len(datos) > MAX_METADATOS:
        raise ValueError("limite_metadatos_rc6")
    texto = datos.decode("utf-8", errors="strict")
    nivel, cadena, escape = 0, False, False
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
            if nivel > MAX_PROFUNDIDAD:
                raise ValueError("profundidad_json_rc6")
        elif c in "]}":
            nivel -= 1

    def pares(xs):
        d = {}
        for k, v in xs:
            if k in d:
                raise ValueError("clave_json_duplicada")
            d[k] = v
        return d

    def constante(_):
        raise ValueError("numero_no_finito")

    v = json.loads(texto, object_pairs_hook=pares, parse_constant=constante)
    pila, usados = [v], 0
    while pila:
        x = pila.pop()
        usados += 1
        if usados > MAX_NODOS:
            raise ValueError("nodos_json_rc6")
        if type(x) is dict:
            pila.extend(x.values())
        elif type(x) is list:
            pila.extend(x)
        elif type(x) is float and not math.isfinite(x):
            raise ValueError("numero_no_finito")
    return v


def _campos(clase):
    # Solo este campo se recalcula por contrato RC5 al construir la solicitud.
    return tuple(f for f in fields(clase) if not (
        clase is mat.SolicitudMaterializacion and f.name == "linaje"))


@lru_cache(maxsize=128)
def _tipos(clase):
    # Solo anotaciones del código confiable registrado; nunca texto del archivo.
    return get_type_hints(clase)


def _tipificado(v, t):
    origen, args = get_origin(t), get_args(t)
    if origen is UnionType:
        return any(_tipificado(v, a) for a in args)
    if origen is tuple:
        if type(v) is not tuple:
            return False
        if len(args) == 2 and args[1] is Ellipsis:
            return all(_tipificado(x, args[0]) for x in v)
        return len(v) == len(args) and all(_tipificado(x, a) for x, a in zip(v, args))
    return type(v) is t


def codificar(valor):
    tabla, memoria, activos = [], {}, set()
    visitas, bytes_texto = 0, 0

    def dato(v, profundidad=0):
        nonlocal visitas, bytes_texto
        visitas += 1
        if visitas > MAX_NODOS or profundidad > MAX_PROFUNDIDAD:
            raise ValueError("presupuesto_codec_rc6")
        if type(v) is str:
            bytes_texto += len(v.encode("utf-8"))
            if bytes_texto > MAX_METADATOS:
                raise ValueError("limite_texto_rc6")
            return v
        if v is None or type(v) in (bool, int):
            return v
        if type(v) is float and math.isfinite(v):
            return v
        if type(v) is Decimal and v.is_finite():
            return {"decimal": str(v)}
        if type(v) is date:
            return {"date": v.isoformat()}
        if type(v) is datetime:
            if v.tzinfo is not None and type(v.tzinfo) is not timezone:
                raise ValueError("zona_no_admitida_por_perfil_rc6")
            return {"datetime": v.isoformat(), "fold": v.fold}
        if type(v) is tuple:
            return {"tuple": [dato(x, profundidad + 1) for x in v]}
        if type(v) not in _NOMBRES:
            raise ValueError("tipo_fuera_del_perfil_rc6")
        if isinstance(v, Enum):
            return {"enum": _NOMBRES[type(v)], "valor": v.value}
        if not is_dataclass(v):
            raise ValueError("tipo_codec_rc6")
        identidad = id(v)
        if identidad in activos:
            raise ValueError("ciclo_objetos_codec_rc6")
        if identidad not in memoria:
            indice = len(tabla)
            memoria[identidad] = indice
            tabla.append(None)
            activos.add(identidad)
            tabla[indice] = {"clase": _NOMBRES[type(v)], "campos": {
                f.name: dato(getattr(v, f.name), profundidad + 1) for f in _campos(type(v))}}
            activos.remove(identidad)
        return {"ref": memoria[identidad]}

    raiz = dato(valor)
    b = canonico({"version": VERSION, "raiz": raiz, "objetos": tabla})
    if len(b) > MAX_METADATOS:
        raise ValueError("limite_metadatos_rc6")
    return b


def decodificar(datos):
    s = leer_json(datos)
    if type(s) is not dict or set(s) != {"version", "raiz", "objetos"} or s["version"] != VERSION:
        raise ValueError("version_codec_rc6_incompatible")
    tabla = s["objetos"]
    if type(tabla) is not list or len(tabla) > MAX_NODOS:
        raise ValueError("tabla_codec_rc6")
    memoria, activos, visitas = {}, set(), 0

    def valor(v, profundidad=0):
        nonlocal visitas
        visitas += 1
        if visitas > MAX_NODOS or profundidad > MAX_PROFUNDIDAD:
            raise ValueError("presupuesto_codec_rc6")
        if v is None or type(v) in (str, bool, int, float):
            return v
        if type(v) is not dict:
            raise ValueError("nodo_codec_rc6")
        ks = set(v)
        if ks == {"tuple"} and type(v["tuple"]) is list:
            return tuple(valor(x, profundidad + 1) for x in v["tuple"])
        if ks == {"decimal"} and type(v["decimal"]) is str:
            try:
                d = Decimal(v["decimal"])
            except InvalidOperation:
                raise ValueError("decimal_codec_rc6") from None
            if not d.is_finite():
                raise ValueError("numero_no_finito")
            return d
        if ks == {"date"} and type(v["date"]) is str:
            return date.fromisoformat(v["date"])
        if ks == {"datetime", "fold"} and type(v["datetime"]) is str and type(v["fold"]) is int and v["fold"] in (0, 1):
            return datetime.fromisoformat(v["datetime"]).replace(fold=v["fold"])
        if ks == {"enum", "valor"} and type(v["enum"]) is str:
            c = _REGISTRO.get(v["enum"])
            if c is None or not issubclass(c, Enum):
                raise ValueError("enum_codec_rc6")
            return c(v["valor"])
        if ks != {"ref"} or type(v["ref"]) is not int or not 0 <= v["ref"] < len(tabla):
            raise ValueError("referencia_codec_rc6")
        i = v["ref"]
        if i in activos:
            raise ValueError("ciclo_objetos_codec_rc6")
        if i not in memoria:
            activos.add(i)
            r = tabla[i]
            if type(r) is not dict or set(r) != {"clase", "campos"} or type(r["clase"]) is not str:
                raise ValueError("registro_codec_rc6")
            c = _REGISTRO.get(r["clase"])
            if c is None or not is_dataclass(c) or type(r["campos"]) is not dict:
                raise ValueError("clase_codec_rc6")
            fs = _campos(c)
            if set(r["campos"]) != {f.name for f in fs}:
                raise ValueError("campos_codec_rc6")
            vs = {f.name: valor(r["campos"][f.name], profundidad + 1) for f in fs}
            ts = _tipos(c)
            if any(not _tipificado(vs[f.name], ts[f.name]) for f in fs):
                raise ValueError("tipo_campo_codec_rc6")
            objeto = c(**{f.name: vs[f.name] for f in fs if f.init})
            if any(type(getattr(objeto, f.name)) is not type(vs[f.name])
                    or getattr(objeto, f.name) != vs[f.name] for f in fs if not f.init):
                raise ValueError("constante_codec_rc6")
            memoria[i] = objeto
            activos.remove(i)
        return memoria[i]

    resultado = valor(s["raiz"])
    if len(memoria) != len(tabla) or codificar(resultado) != datos:
        raise ValueError("representacion_rc6_no_canonica")
    return resultado
