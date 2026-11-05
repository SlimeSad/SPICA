"""Extracción literal limitada de WordprocessingML ya comprobado; sin renderizar."""

import re

from ._control import exigir
from .modelos import CeldaDOCX, FilaDOCX, ParrafoDOCX, PropiedadDOCX, ReferenciaDOCX, TablaDOCX

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
Q = "{" + W + "}"

# Perfil cerrado de estructura y formato pasivo para partes con texto.
PASIVOS = set("""document body hdr ftr footnotes footnote endnotes endnote p pPr r rPr t
tbl tblPr tblGrid gridCol tr trPr tc tcPr tblStyle tblW tblInd tblBorders top left bottom
right insideH insideV start end tblLayout tblLook tblCellMar tcW gridSpan vMerge hMerge
vAlign cantSplit tblHeader trHeight gridBefore gridAfter wBefore wAfter
pStyle rStyle jc spacing ind tabs tab br cr noBreakHyphen softHyphen
b bCs i iCs u strike dstrike caps smallCaps color highlight sz szCs rFonts lang
rtl cs vertAlign shd border position kern w fitText textScale snapToGrid
keepNext keepLines pageBreakBefore widowControl contextualSpacing outlineLvl
numPr ilvl numId bidi textDirection suppressLineNumbers suppressAutoHyphens
sectPr headerReference footerReference pgSz pgMar cols col docGrid pgNumType
titlePg type footnotePr endnotePr numFmt numStart numRestart separator continuationSeparator
bookmarkStart bookmarkEnd hyperlink proofErr lastRenderedPageBreak footnoteReference
endnoteReference drawing""".split())

AMBIGUOS = set("""fldSimple fldChar instrText delInstrText ins del moveFrom moveTo
moveFromRangeStart moveFromRangeEnd moveToRangeStart moveToRangeEnd
commentRangeStart commentRangeEnd commentReference sdt sdtContent customXml
vanish webHidden specVanish sym ruby hMerge""".split())
ACTIVOS = set("""object control altChunk subDoc attachedTemplate saveThroughXslt
frameset oleObject OLEObject activeX vbaProject""".split())


def rutas(arbol):
    """Clark paths con ordinal entre hermanos del mismo QName; no páginas."""
    def visitar(e, ruta):
        yield e, ruta
        indices = {}
        for h in e:
            indices[h.tag] = indices.get(h.tag, 0) + 1
            yield from visitar(h, ruta + "/" + h.tag + f"[{indices[h.tag]}]")
    return visitar(arbol, "/" + arbol.tag + "[1]")


def detectar(arbol, parte, control, relaciones):
    """No interpreta campos. Desconocidos omiten toda la parte textual."""
    ambigua = False
    es_texto = parte == "word/document.xml" or parte.startswith(("word/header", "word/footer")) or parte in (
        "word/footnotes.xml", "word/endnotes.xml")
    for e in arbol.iter():
        control.paso()
        local = e.tag.rsplit("}", 1)[-1]
        exigir(local not in ACTIVOS, "contenido_activo_no_admitido")
        exigir(not e.tag.startswith("{http://www.w3.org/2001/XInclude}"), "xinclude_no_admitido")
        if e.tag.startswith(Q) and local in AMBIGUOS:
            ambigua = True
        if es_texto and (not e.tag.startswith(Q) or local not in PASIVOS):
            ambigua = True
        if e.tag == Q + "drawing":
            ambigua = True  # No se reconstruye colocación ni texto de gráficos.
        if e.tag in (Q + "headerReference", Q + "footerReference"):
            exigir(e.get("{" + R + "}id") is not None, "referencia_rid_ausente")
        for a, valor in e.attrib.items():
            if es_texto and not a.startswith((Q, "{" + R + "}", "{http://www.w3.org/XML/1998/namespace}")):
                ambigua = True
            if a.startswith("{" + R + "}"):
                exigir(valor in relaciones, "referencia_rid_ausente")
                clase = relaciones[valor][0].rsplit("/", 1)[-1]
                esperadas = {"headerReference": "header", "footerReference": "footer", "blip": "image"}
                exigir(local in esperadas and clase == esperadas[local], "uso_relacion_fuera_del_perfil")
    if es_texto and not ambigua:
        padres = {
            "body": {"document"}, "p": {"body", "hdr", "ftr", "tc", "footnote", "endnote"},
            "r": {"p", "hyperlink"}, "t": {"r"}, "tbl": {"body", "hdr", "ftr", "tc", "footnote", "endnote"},
            "tr": {"tbl"}, "tc": {"tr"}, "footnote": {"footnotes"}, "endnote": {"endnotes"},
            "pPr": {"p"}, "rPr": {"r", "pPr"}, "tblPr": {"tbl"}, "trPr": {"tr"}, "tcPr": {"tc"},
        }
        def estructura(e, padre=None):
            local = e.tag[len(Q):]
            if local in padres:
                exigir(padre in padres[local], "estructura_textual_incoherente")
            exigir(local != "t" or not len(e), "texto_con_elementos_no_admitido")
            exigir(local == "t" or not (e.text or "").strip(), "texto_fuera_de_contexto")
            for h in e:
                exigir(not (h.tail or "").strip(), "texto_fuera_de_contexto")
                estructura(h, local)
        estructura(arbol)
    return ambigua


class Extractor:
    def __init__(self, control):
        self.c = control
        self.parrafos, self.tablas, self.propiedades = [], [], []
        self.estilos = {}
        self.celdas = 0
        self.ids_notas, self.usos_notas = set(), set()

    def ref(self, parte, ruta, **indices):
        self.c.guardar_textos(parte, ruta)
        i = self.c.identidad
        return ReferenciaDOCX(i.identificador, i.sha256, parte, ruta, **indices)

    def estilos_de(self, raiz):
        for e in raiz.findall(Q + "style"):
            self.c.paso()
            self.c.limite(len(self.estilos) < self.c.limites.max_estilos, "limite_estilos")
            sid = e.get(Q + "styleId")
            exigir(sid and sid not in self.estilos and len(sid) <= 128, "estilo_ambiguo")
            nivel = e.find(Q + "pPr/" + Q + "outlineLvl")
            nombre = e.find(Q + "name")
            titulo = nivel is not None and nivel.get(Q + "val") in tuple(str(i) for i in range(9))
            titulo |= nombre is not None and nombre.get(Q + "val") in ("Title", "Subtitle")
            self.c.guardar_textos(sid)
            self.estilos[sid] = (e.get(Q + "type", "paragraph"), titulo)

    def metadatos(self, parte, arbol):
        permitidos = {"title", "subject", "description", "created", "modified", "revision", "version", "Application", "AppVersion"}
        for e, ruta in rutas(arbol):
            self.c.paso()
            if e is arbol:
                continue
            nombre = e.tag.rsplit("}", 1)[-1]
            if nombre in permitidos and e.text is not None and not len(e):
                self.c.limite(len(self.propiedades) < self.c.limites.max_propiedades, "limite_propiedades")
                valor = self.c.literal(e.text)
                self.propiedades.append(PropiedadDOCX(self.ref(parte, ruta), nombre, valor))
        self.c.diagnostico("otros_metadatos_no_publicados", parte, omision=True)

    def contenido(self, parte, arbol):
        origen = ("cuerpo" if parte == "word/document.xml" else
                  "encabezado" if parte.startswith("word/header") else
                  "pie" if parte.startswith("word/footer") else "nota")
        caminos, coste = {}, 0
        try:
            for e, r in rutas(arbol):
                self.c.paso()
                n = len(r.encode("utf-8"))
                self.c.reservar(n)
                coste += n
                caminos[id(e)] = r
            npar, ntabla = 0, 0
            def parrafo(e, tabla=None, fila=None, columna=None):
                nonlocal npar
                self.c.limite(len(self.parrafos) < self.c.limites.max_parrafos, "limite_parrafos")
                npar += 1
                pedazos, largo = [], 0
                estilo = None
                titulo = False
                for h in e.iter():
                    self.c.paso()
                    if h.tag == Q + "pStyle":
                        estilo = h.get(Q + "val")
                        exigir(estilo in self.estilos, "estilo_referenciado_ausente")
                        exigir(self.estilos[estilo][0] == "paragraph", "tipo_estilo_incoherente")
                        titulo = self.estilos[estilo][1]
                    elif h.tag == Q + "outlineLvl":
                        titulo |= h.get(Q + "val") in tuple(str(i) for i in range(9))
                    t = (h.text or "") if h.tag == Q + "t" else {
                        Q + "tab": "\t", Q + "br": "\n", Q + "cr": "\n",
                        Q + "noBreakHyphen": "\u2011", Q + "softHyphen": "\u00ad",
                    }.get(h.tag, "")
                    largo += len(t)
                    self.c.limite(largo <= self.c.limites.max_texto_fragmento, "limite_texto_fragmento")
                    pedazos.append(t)
                    if h.tag in (Q + "footnoteReference", Q + "endnoteReference"):
                        self.usos_notas.add(("footnotes" if h.tag == Q + "footnoteReference" else "endnotes", h.get(Q + "id")))
                p = ParrafoDOCX(self.ref(parte, caminos[id(e)], parrafo=npar,
                    tabla=tabla, fila=fila, columna=columna), self.c.literal("".join(pedazos)), origen, estilo, titulo)
                self.parrafos.append(p)
                return p

            def tabla(e):
                nonlocal ntabla
                self.c.limite(len(self.tablas) < self.c.limites.max_tablas, "limite_tablas")
                ntabla += 1
                indice = ntabla
                referencia = self.ref(parte, caminos[id(e)], tabla=indice)
                pos = len(self.tablas)
                self.tablas.append(None)  # Reserva el orden antes de tablas anidadas.
                filas = []
                for f, row in enumerate(e.findall(Q + "tr"), 1):
                    celdas = []
                    for col, cell in enumerate(row.findall(Q + "tc"), 1):
                        self.c.limite(self.celdas < self.c.limites.max_celdas, "limite_celdas")
                        self.celdas += 1
                        ps, anidadas = [], []
                        for h in cell:
                            if h.tag == Q + "p": ps.append(parrafo(h, indice, f, col))
                            elif h.tag == Q + "tbl": anidadas.append(tabla(h).referencia.ruta_xml)
                        span = cell.find(Q + "tcPr/" + Q + "gridSpan")
                        vm = cell.find(Q + "tcPr/" + Q + "vMerge")
                        exigir(span is None or re.fullmatch(r"[1-9][0-9]{0,3}", span.get(Q + "val", "")), "grid_span_fuera_del_perfil")
                        exigir(vm is None or vm.get(Q + "val") in (None, "restart", "continue"), "vmerge_fuera_del_perfil")
                        celdas.append(CeldaDOCX(self.ref(parte, caminos[id(cell)], tabla=indice, fila=f, columna=col),
                            tuple(ps), tuple(anidadas), span.get(Q + "val") if span is not None else None,
                            vm.get(Q + "val", "") if vm is not None else None))
                    filas.append(FilaDOCX(f, tuple(celdas)))
                t = TablaDOCX(referencia, tuple(filas))
                self.tablas[pos] = t
                return t

            def bloques(e):
                for h in e:
                    self.c.paso()
                    if h.tag == Q + "p": parrafo(h)
                    elif h.tag == Q + "tbl": tabla(h)
                    elif h.tag in (Q + "footnote", Q + "endnote"):
                        clave = ("footnotes" if h.tag == Q + "footnote" else "endnotes", h.get(Q + "id"))
                        exigir(clave[1] is not None and clave not in self.ids_notas, "identidad_nota_ambigua")
                        self.ids_notas.add(clave)
                        if h.get(Q + "type", "normal") == "normal": bloques(h)
                        else: self.c.diagnostico("separadores_notas_no_interpretados", parte, omision=True)
                    elif h.tag != Q + "sectPr":
                        exigir(False, "bloque_documental_no_admitido")
            if parte == "word/document.xml":
                cuerpos = arbol.findall(Q + "body")
                exigir(len(cuerpos) == 1, "cuerpo_docx_ausente_o_ambiguo")
                bloques(cuerpos[0])
            else:
                bloques(arbol)
        finally:
            self.c.liberar(coste)
