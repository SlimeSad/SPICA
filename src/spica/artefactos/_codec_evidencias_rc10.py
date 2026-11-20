"""Proyección cerrada RC10 sobre las primitivas JSON acotadas RC6.

No modifica el registro RC6. Los testigos privados nunca se reconstruyen.
"""

from dataclasses import fields, is_dataclass
from enum import Enum

from ..adquisicion.verificacion.csv_streaming import PoliticaLecturaCSV
from ..calidad import modelos as qa
from ..calidad.consumo import EstadoConsumoQA, InformeConsumoQA, LimitesConsumoQA, ProblemaConsumoQA
from ..calidad.exportacion import ContextoExportacionQA, LimitesExportacionQA
from ..contextos.adaptadores_qa import VinculoResultadoQA
from ..coordinacion.modelos import InformeComposicion, InspeccionOperacion
from ..perfilado.modelos import LimitesPerfil
from ..interoperabilidad.modelos import EstadoAptitud
from . import _codec_rc6 as base
from .modelos import InformeArtefacto, InformeLinaje
from .cierre_exportacion import EvidenciaExportacion, InformeCierreExportacion, SolicitudExportacionTecnica
from .admision_exportacion import InformeAdmisionExportacion, SolicitudAdmisionExportacion

VERSION = "rc10.evidencias.0.1.0"
_EXTRA = (
    EstadoAptitud,
    PoliticaLecturaCSV, EstadoConsumoQA, InformeConsumoQA, LimitesConsumoQA, ProblemaConsumoQA,
    ContextoExportacionQA, LimitesExportacionQA, VinculoResultadoQA, InformeComposicion,
    InspeccionOperacion, LimitesPerfil, InformeArtefacto, InformeLinaje,
    EvidenciaExportacion, InformeCierreExportacion, SolicitudExportacionTecnica,
    InformeAdmisionExportacion, SolicitudAdmisionExportacion,
    qa.CategoriaQA, qa.ConfiguracionQA, qa.EstadoResultadoQA, qa.LimitesQA,
    qa.ProcedenciaQA, qa.RegistroQA, qa.ReglaQA, qa.ResultadoQA,
    qa.ReferenciaDocumentalQA, qa.FormatoDocumentadoQA, qa.DatoDocumentadoQA,
    qa.IdentidadEstacionQA, qa.FormatoQA,
)
_REGISTRO = {c.__module__ + ":" + c.__name__: c for c in (*base._CLASES, *_EXTRA)}
_NOMBRES = {c: n for n, c in _REGISTRO.items()}
_PRIVADOS = {EvidenciaExportacion: {"_captura"}, InformeAdmisionExportacion: {"_comprobacion"}}


def _campos(c):
    return tuple(f for f in fields(c) if f.name not in _PRIVADOS.get(c, ()))


def codificar(valor):
    objetos, textos, indices, cadenas, activos = [], [], {}, {}, set()
    visitas, bytes_texto = 0, 0

    def dato(v, nivel=0):
        nonlocal visitas, bytes_texto
        visitas += 1
        if visitas > base.MAX_NODOS or nivel > 48:
            raise ValueError("presupuesto_proyeccion_rc10")
        if type(v) in (str, bytes):
            if len(v) > base.MAX_METADATOS:
                raise ValueError("limite_texto_rc10")
            clave = v.encode("utf-8", errors="strict") if type(v) is str else v
            if clave not in cadenas:
                bytes_texto += len(clave)
                if bytes_texto > base.MAX_METADATOS:
                    raise ValueError("limite_texto_rc10")
                cadenas[clave] = len(textos)
                textos.append(clave.hex())
            return ("texto" if type(v) is str else "bytes", cadenas[clave])
        if type(v) is tuple:
            return ("tupla", tuple(dato(x, nivel + 1) for x in v))
        if type(v) in _NOMBRES:
            if isinstance(v, Enum):
                return ("enum", _NOMBRES[type(v)], v.value)
            if not is_dataclass(v):
                raise ValueError("tipo_no_admitido_rc10")
            identidad = id(v)
            if identidad in activos:
                raise ValueError("ciclo_rc10")
            if identidad not in indices:
                indices[identidad] = len(objetos)
                objetos.append(None)
                activos.add(identidad)
                objetos[indices[identidad]] = (_NOMBRES[type(v)], tuple(
                    (f.name, dato(getattr(v, f.name), nivel + 1)) for f in _campos(type(v))))
                activos.remove(identidad)
            return ("objeto", indices[identidad])
        # RC6 limita y valida escalares, fechas y Decimal. Ningún objeto ejecutable.
        base.codificar(v)
        return ("escalar", v)

    raiz = dato(valor)
    cuerpo = base.leer_json(base.codificar((raiz, tuple(objetos), tuple(textos))))
    b = base.canonico(dict(perfil=VERSION, cuerpo=cuerpo))
    if len(b) > base.MAX_METADATOS:
        raise ValueError("limite_expediente_rc10")
    return b


def decodificar(datos):
    sobre = base.leer_json(datos)
    if type(sobre) is not dict or set(sobre) != {"perfil", "cuerpo"} or sobre["perfil"] != VERSION:
        raise ValueError("perfil_rc10_incompatible")
    raiz, tabla, textos = base.decodificar(base.canonico(sobre["cuerpo"]))
    if type(tabla) is not tuple or type(textos) is not tuple:
        raise ValueError("tablas_rc10_invalidas")
    memoria, activos = {}, set()
    visitas = 0

    def valor(v, nivel=0):
        nonlocal visitas
        visitas += 1
        if visitas > base.MAX_NODOS or nivel > 48 or type(v) is not tuple:
            raise ValueError("presupuesto_o_nodo_rc10")
        match v:
            case ("escalar", x):
                if type(x) in (str, bytes, tuple) or type(x) in _NOMBRES:
                    raise ValueError("escalar_rc10_invalido")
                return x
            case ("tupla", xs) if type(xs) is tuple:
                return tuple(valor(x, nivel + 1) for x in xs)
            case (tipo, i) if tipo in ("texto", "bytes") and type(i) is int and 0 <= i < len(textos):
                texto = textos[i]
                if type(texto) is not str:
                    raise ValueError("texto_rc10_invalido")
                b = bytes.fromhex(texto)
                return b.decode("utf-8", errors="strict") if tipo == "texto" else b
            case ("enum", nombre, x) if type(nombre) is str:
                c = _REGISTRO.get(nombre)
                if c is None or not issubclass(c, Enum):
                    raise ValueError("enum_rc10_invalido")
                return c(x)
            case ("objeto", i) if type(i) is int and 0 <= i < len(tabla):
                if i in activos:
                    raise ValueError("ciclo_rc10")
                if i not in memoria:
                    activos.add(i)
                    nombre, pares = tabla[i]
                    c = _REGISTRO.get(nombre)
                    if c is None or not is_dataclass(c) or type(pares) is not tuple:
                        raise ValueError("clase_rc10_invalida")
                    fs = _campos(c)
                    if tuple(k for k, _ in pares) != tuple(f.name for f in fs):
                        raise ValueError("campos_rc10_invalidos")
                    vs = {k: valor(x, nivel + 1) for k, x in pares}
                    ts = base._tipos(c)
                    if any(not base._tipificado(vs[f.name], ts[f.name]) for f in fs):
                        raise ValueError("tipo_campo_rc10_invalido")
                    objeto = c(**{f.name: vs[f.name] for f in fs if f.init})
                    if any(getattr(objeto, f.name) != vs[f.name] for f in fs if not f.init):
                        raise ValueError("constante_rc10_contradictoria")
                    # Los derivados ya se recalcularon y cotejaron. Conservar sus
                    # referencias compartidas, nunca los testigos excluidos.
                    for f in fs:
                        if not f.init:
                            object.__setattr__(objeto, f.name, vs[f.name])
                    memoria[i] = objeto
                    activos.remove(i)
                return memoria[i]
        raise ValueError("nodo_rc10_invalido")

    resultado = valor(raiz)
    if len(memoria) != len(tabla) or codificar(resultado) != datos:
        raise ValueError("representacion_rc10_no_canonica")
    return resultado
