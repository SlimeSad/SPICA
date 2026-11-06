"""Excepción cerrada para omitir destinos, sin resolver URI o incorporar recursos."""

import re
from urllib.parse import unquote, urlsplit

from ._control import exigir
from ._extraccion import Q, R, rutas
from .modelos import HipervinculoOmitidoDOCX

TIPO_HIPERVINCULO = R + "/hyperlink"


def clasificar(tipo, destino, fuente, c):
    """Devuelve solo el esquema; la URI no se conserva ni se devuelve."""
    exigir(tipo == TIPO_HIPERVINCULO, "relacion_externa_no_admitida")
    exigir(fuente == "word/document.xml" or fuente in ("word/footnotes.xml", "word/endnotes.xml")
            or re.fullmatch(r"word/(header|footer)[1-9][0-9]{0,3}\.xml", fuente),
            "origen_hipervinculo_externo_incoherente")
    c.paso()
    exigir(isinstance(destino, str) and 0 < len(destino) <= 2048, "destino_hipervinculo_no_admitido")
    exigir(not re.search(r"%(?![0-9A-Fa-f]{2})", destino), "destino_hipervinculo_no_admitido")
    decodificado = destino
    for paso in range(4):
        exigir(not any(ord(x) <= 32 or ord(x) == 127 or x == "\\" for x in decodificado),
                "destino_hipervinculo_no_admitido")
        if paso < 3:
            decodificado = unquote(decodificado)
    exigir(unquote(decodificado) == decodificado, "destino_hipervinculo_no_admitido")
    try:
        uri = urlsplit(destino)
        if uri.scheme in ("http", "https"):
            valido = bool(uri.hostname) and uri.username is None and uri.password is None
            # Acceder al puerto también detecta sintaxis/valores inválidos, sin DNS.
            uri.port
        elif uri.scheme == "mailto":
            valido = (not uri.netloc and not uri.query and not uri.fragment
                      and re.fullmatch(r"[^@\s?,;:/\\]+@[^@\s?,;:/\\]+", unquote(uri.path)))
        else:
            valido = False
    except ValueError:
        valido = False
    exigir(valido, "destino_hipervinculo_no_admitido")
    return uri.scheme


def registrar_usos(arbol, parte, pendientes, c, referencia):
    """Prueba el uso local exacto incluso si otra característica vuelve la parte incompleta."""
    propios = {rid: dato for (fuente, rid), dato in pendientes.items() if fuente == parte}
    if not propios:
        return
    padres = {}
    try:
        for e in arbol.iter():
            c.paso()
            for h in e:
                if h.tag == Q + "hyperlink" and h.get("{" + R + "}id") in propios:
                    c.limite(len(padres) < c.limites.max_referencias, "limite_usos_hipervinculos")
                    c.reservar(16)  # Carga de índice; el overhead Python se acota por nodos/usos.
                    padres[id(h)] = e.tag
        for e, ruta in rutas(arbol):
            c.paso()
            rid = e.get("{" + R + "}id")
            if e.tag != Q + "hyperlink" or rid not in propios:
                continue
            exigir(padres.get(id(e)) == Q + "p" and len(e) > 0 and all(h.tag == Q + "r" for h in e),
                    "uso_hipervinculo_externo_incoherente")
            exigir(set(e.attrib) <= {"{" + R + "}id", Q + "history", Q + "tooltip", Q + "tgtFrame"},
                    "hipervinculo_externo_ambiguo")
            exigir(all(h.tag in {Q + k for k in ("rPr", "t", "tab", "br", "cr", "noBreakHyphen", "softHyphen")}
                        for run in e for h in run), "contenido_hipervinculo_fuera_del_perfil")
            cantidad = sum(len(d["usos"]) for d in pendientes.values())
            c.limite(cantidad < c.limites.max_referencias, "limite_usos_hipervinculos")
            propios[rid]["usos"].append(referencia(parte, ruta))
    finally:
        c.liberar(len(padres) * 16)


def finalizar(pendientes, c):
    for d in pendientes.values():
        c.paso()
        exigir(d["usos"], "hipervinculo_externo_sin_uso")
    for (fuente, rid), d in sorted(pendientes.items()):
        c.paso()
        c.hipervinculos.append(HipervinculoOmitidoDOCX(d["parte"], rid, TIPO_HIPERVINCULO,
            "External", fuente, d["esquema"], tuple(d["usos"])))
        c.diagnostico("destino_hipervinculo_externo_no_consultado", fuente, omision=True)
