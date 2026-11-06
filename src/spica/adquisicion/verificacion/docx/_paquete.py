"""Perfil DOCX cerrado sobre los controles ZIP/XML compartidos existentes."""

from contextlib import contextmanager
from copy import copy
import posixpath
import re
import struct
from urllib.parse import urlsplit
from zipfile import ZipFile, ZIP_DEFLATED

from .._xlsx import (
    CONTENIDOS, MIME_WORD, RELACIONES, _XML, _directorio_previo,
    _relaciones, _tipos, inspeccionar_zip,
)
from ._control import FuenteZIP, _Fallo, exigir
from ._extraccion import Extractor, Q, R, detectar
from ._hipervinculos import clasificar, finalizar, registrar_usos
from .modelos import ParteDOCX, RelacionDOCX

BASE = "application/vnd.openxmlformats-officedocument."
MIME_RELS = "application/vnd.openxmlformats-package.relationships+xml"
MIME_CORE = "application/vnd.openxmlformats-package.core-properties+xml"
FIJOS = {
    "word/document.xml": (MIME_WORD, Q + "document"),
    "word/styles.xml": (BASE + "wordprocessingml.styles+xml", Q + "styles"),
    "word/settings.xml": (BASE + "wordprocessingml.settings+xml", Q + "settings"),
    "word/fontTable.xml": (BASE + "wordprocessingml.fontTable+xml", Q + "fonts"),
    "word/webSettings.xml": (BASE + "wordprocessingml.webSettings+xml", Q + "webSettings"),
    "word/numbering.xml": (BASE + "wordprocessingml.numbering+xml", Q + "numbering"),
    "word/footnotes.xml": (BASE + "wordprocessingml.footnotes+xml", Q + "footnotes"),
    "word/endnotes.xml": (BASE + "wordprocessingml.endnotes+xml", Q + "endnotes"),
    "word/comments.xml": (BASE + "wordprocessingml.comments+xml", Q + "comments"),
    "docProps/core.xml": (MIME_CORE, "{http://schemas.openxmlformats.org/package/2006/metadata/core-properties}coreProperties"),
    "docProps/app.xml": (BASE + "extended-properties+xml", "{http://schemas.openxmlformats.org/officeDocument/2006/extended-properties}Properties"),
    "docProps/custom.xml": (BASE + "custom-properties+xml", "{http://schemas.openxmlformats.org/officeDocument/2006/custom-properties}Properties"),
}
DIRECTORIOS = {"_rels/", "docProps/", "word/", "word/_rels/", "word/media/", "word/theme/"}
REL_TIPOS = {R + "/" + k: v for k, v in {
    "officeDocument": (MIME_WORD,), "styles": (FIJOS["word/styles.xml"][0],),
    "settings": (FIJOS["word/settings.xml"][0],), "fontTable": (FIJOS["word/fontTable.xml"][0],),
    "webSettings": (FIJOS["word/webSettings.xml"][0],), "numbering": (FIJOS["word/numbering.xml"][0],),
    "footnotes": (FIJOS["word/footnotes.xml"][0],), "endnotes": (FIJOS["word/endnotes.xml"][0],),
    "comments": (FIJOS["word/comments.xml"][0],),
    "header": (BASE + "wordprocessingml.header+xml",), "footer": (BASE + "wordprocessingml.footer+xml",),
    "theme": (BASE + "theme+xml",), "image": ("image/png", "image/jpeg"),
    "extended-properties": (FIJOS["docProps/app.xml"][0],),
    "custom-properties": (FIJOS["docProps/custom.xml"][0],),
}.items()}
REL_TIPOS[RELACIONES + "/metadata/core-properties"] = (MIME_CORE,)


def perfil(nombre):
    if nombre == "[Content_Types].xml":
        return None, "{" + CONTENIDOS + "}Types"
    if nombre in FIJOS:
        return FIJOS[nombre]
    m = re.fullmatch(r"word/(header|footer)[1-9][0-9]{0,3}\.xml", nombre)
    if m:
        return BASE + "wordprocessingml." + m[1] + "+xml", Q + ("hdr" if m[1] == "header" else "ftr")
    if re.fullmatch(r"word/theme/theme[1-9][0-9]{0,3}\.xml", nombre):
        return BASE + "theme+xml", "{http://schemas.openxmlformats.org/drawingml/2006/main}theme"
    if re.fullmatch(r"word/media/image[1-9][0-9]{0,3}\.(png|jpg|jpeg)", nombre):
        return ("image/png" if nombre.endswith("png") else "image/jpeg"), None
    if nombre == "_rels/.rels":
        return MIME_RELS, "{" + RELACIONES + "}Relationships"
    m = re.fullmatch(r"(word|word/theme)/_rels/([A-Za-z0-9]+\.xml)\.rels", nombre)
    if m and posixpath.join(m[1], m[2]) in FIJOS:
        return MIME_RELS, "{" + RELACIONES + "}Relationships"
    if m and re.fullmatch(r"(header|footer)[1-9][0-9]{0,3}\.xml", m[2]):
        return MIME_RELS, "{" + RELACIONES + "}Relationships"
    exigir(False, "parte_fuera_del_perfil_docx")


def _extra_seguro(extra):
    cursor = 0
    while cursor < len(extra):
        exigir(len(extra) - cursor >= 4, "zip_extra_incoherente")
        clase, n = struct.unpack_from("<HH", extra, cursor)
        exigir(clase not in (1, 0x9901), "zip64_o_cifrado_no_admitido")
        cursor += 4 + n
        exigir(cursor <= len(extra), "zip_extra_incoherente")


def _metadatos_zip(datos, c):
    exigir(datos.startswith(b"PK\x03\x04"), "firma_zip_no_admitida")
    with FuenteZIP(datos, c) as f:
        _directorio_previo(f, len(datos), c.limites.zip)
        with ZipFile(f) as z:
            infos = z.infolist()
            nombres = {i.filename for i in infos if not i.is_dir()}
            exigir({"[Content_Types].xml", "_rels/.rels", "word/document.xml"} <= nombres,
                    "componentes_docx_ausentes")
            xml = sum(not i.is_dir() and i.filename.endswith((".xml", ".rels")) for i in infos)
            c.limite(xml <= c.limites.max_xml, "limite_cantidad_xml")
            for i in infos:
                c.paso()
                if i.is_dir():
                    exigir(i.filename in DIRECTORIOS and i.file_size == 0, "directorio_zip_fuera_del_perfil")
                    continue
                perfil(i.filename)
                exigir(not i.flag_bits & 1, "zip_cifrado_no_admitido")
                exigir(not i.flag_bits & ~0x80e, "zip_flags_no_admitidos")
                _extra_seguro(i.extra)
                f.seek(i.header_offset)
                b = f.read(30)
                exigir(len(b) == 30 and b[:4] == b"PK\x03\x04", "zip_cabecera_incoherente")
                flags, metodo = struct.unpack_from("<HH", b, 6)
                crc, comprimidos, reales, ln, le = struct.unpack_from("<IIIHH", b, 14)
                exigir(flags == i.flag_bits and metodo == i.compress_type, "zip_cabeceras_no_coinciden")
                exigir(f.read(ln) == i.filename.encode("ascii"), "zip_nombre_local_no_coincide")
                _extra_seguro(f.read(le))
                if not flags & 8:
                    exigir((crc, comprimidos, reales) == (i.CRC, i.compress_size, i.file_size), "zip_tamanos_locales_incoherentes")
            return infos


@contextmanager
def entrada_observable(z, info):
    # ZipExtFile recorta a file_size: un byte testigo evita aceptar un prefijo
    # cuyo tamaño y CRC falsificados oculten contenido descomprimido sobrante.
    observable = copy(info)
    observable.file_size = info.file_size + 1
    with z.open(observable) as f:
        yield f
        if info.compress_type == ZIP_DEFLATED:
            # ZipExtFile también puede aceptar un flujo sin marcador final.
            # Perfil probado en CPython 3.15: si cambia esta interfaz privada,
            # rechazar en vez de afirmar una comprobación que no se realizó.
            decodificador = getattr(f, "_decompressor", None)
            exigir(decodificador is not None and decodificador.eof
                    and not decodificador.unused_data and not decodificador.unconsumed_tail
                    and getattr(f, "_compress_left", None) == 0, "flujo_deflate_incoherente")


@contextmanager
def arbol(z, info, c, *, namespaces_raiz=None):
    c.xml += 1
    c.limite(c.xml <= c.limites.max_xml, "limite_cantidad_xml")
    c.limite(info.file_size <= c.limites.zip.max_bytes_xml, "limite_xml")
    c.reservar(info.file_size)
    coste_namespaces = 0
    try:
        xml = _XML(c.limites.zip, c.ctx, True)
        xml.parser.CharacterDataHandler = xml.arbol.data
        if namespaces_raiz is not None:
            exigir(not namespaces_raiz, "contexto_namespaces_no_vacio")
            def declarar(prefijo, uri):
                nonlocal coste_namespaces
                c.paso()
                if xml.profundidad != 0:
                    return  # mc:Ignorable solo se admite en la raíz; no hay herencia MC.
                c.limite(len(namespaces_raiz) < 64, "limite_namespaces_raiz")
                prefijo, uri = prefijo or "", uri or ""
                coste = len(prefijo.encode("utf-8")) + len(uri.encode("utf-8"))
                c.reservar(coste)
                coste_namespaces += coste
                namespaces_raiz[prefijo] = uri
            xml.parser.StartNamespaceDeclHandler = declarar
        def prohibir_instruccion(*args):
            raise _Fallo("instruccion_xml_no_admitida")
        xml.parser.ProcessingInstructionHandler = prohibir_instruccion
        reales = 0
        with entrada_observable(z, info) as f:
            while b := f.read(c.limites.zip.tamano_bloque):
                c.paso()
                reales += len(b)
                c.ctx["descomprimidos"] += len(b)
                c.limite(reales <= min(c.limites.zip.max_bytes_entrada, c.limites.zip.max_bytes_xml), "limite_xml_real")
                c.limite(c.ctx["descomprimidos"] <= c.limites.zip.max_bytes_descomprimidos, "limite_descompresion_real")
                xml.alimentar(b)
        exigir(reales == info.file_size, "tamano_descomprimido_no_coincide")
        yield xml.cerrar()
    finally:
        if namespaces_raiz is not None:
            namespaces_raiz.clear()
        c.liberar(info.file_size + coste_namespaces)


def _fuente_rel(nombre):
    return "" if nombre == "_rels/.rels" else posixpath.join(
        posixpath.dirname(posixpath.dirname(nombre)), posixpath.basename(nombre)[:-5])


def _control_plano(arbol, namespace, atributos, c):
    """Tipos/relaciones no admiten árboles, texto o atributos opacos."""
    exigir(not arbol.attrib and not (arbol.text or "").strip(), "control_ooxml_no_admitido")
    for e in arbol:
        c.paso()
        nombre = e.tag.removeprefix("{" + namespace + "}")
        exigir(e.tag == "{" + namespace + "}" + nombre and nombre in atributos
                and not len(e) and set(e.attrib) <= atributos[nombre]
                and not (e.text or "").strip() and not (e.tail or "").strip(),
                "control_ooxml_no_admitido")


def inspeccionar_paquete(datos, c):
    infos = _metadatos_zip(datos, c)
    # Primera pasada compartida: valida rangos/rutas/CRC/tamaños y todo XML.
    carga = max((i.file_size for i in infos), default=0) + sum(
        i.file_size for i in infos if i.filename in ("[Content_Types].xml", "_rels/.rels"))
    c.reservar(carga)
    try:
        ctx = dict(comprobaciones=[], descomprimidos=0)
        with FuenteZIP(datos, c, 1) as primera:
            try:
                formato, completa = inspeccionar_zip(primera, len(datos), c.limites.zip, ctx)
            finally:
                c.verificados = ctx["descomprimidos"]
        exigir(formato == "docx" and completa, "marcadores_docx_no_admitidos")
        c.verificados = ctx["descomprimidos"]
    finally:
        c.liberar(carga)
    archivos = {i.filename: i for i in infos if not i.is_dir()}
    nombres = set(archivos)
    relaciones, mapas, grafo, pendientes = c.relaciones, {}, {}, {}
    ext = Extractor(c)
    partes = c.partes
    with FuenteZIP(datos, c, 2) as segunda, ZipFile(segunda) as z:
        with arbol(z, archivos["[Content_Types].xml"], c) as a:
            _control_plano(a, CONTENIDOS, {
                "Default": {"Extension", "ContentType"}, "Override": {"PartName", "ContentType"}}, c)
            tipos = _tipos(a, nombres)
            admitidos = {"application/xml", MIME_RELS, MIME_CORE, MIME_WORD,
                *(perfil(n)[0] for n in nombres if n != "[Content_Types].xml")}
            for e in a:
                exigir(e.get("ContentType") in admitidos, "tipo_de_contenido_fuera_del_perfil")
        del a
        for n in sorted(nombres):
            c.paso()
            esperado, _ = perfil(n)
            exigir(n == "[Content_Types].xml" or tipos.get(n) == esperado, "tipo_de_parte_no_coincide")
            i = archivos[n]
            if not n.endswith(".rels"):
                continue
            with arbol(z, i, c) as a:
                _control_plano(a, RELACIONES, {
                    "Relationship": {"Id", "Type", "Target", "TargetMode"}}, c)
                for e in a:
                    if e.get("TargetMode") != "External":
                        exigir(not urlsplit(e.get("Target", "")).fragment, "fragmento_en_relacion_no_admitido")
                rs = _relaciones(a, n, nombres, {})
                fuente = _fuente_rel(n)
                mapas[fuente] = rs
                for rid, (tipo, destino) in rs.items():
                    c.limite(len(relaciones) + len(pendientes) < c.limites.max_referencias, "limite_relaciones")
                    exigir(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.-]{0,127}", rid), "identificador_relacion_no_admitido")
                    if destino is None:
                        elemento = next(e for e in a if e.get("Id") == rid)
                        exigir(elemento.get("TargetMode") == "External", "modo_hipervinculo_incoherente")
                        esquema = clasificar(tipo, elemento.get("Target"), fuente, c)
                        c.guardar_textos(n, rid, tipo, fuente, esquema)
                        pendientes[fuente, rid] = dict(parte=n, esquema=esquema, usos=[])
                        continue
                    exigir(tipo in REL_TIPOS and tipos.get(destino) in REL_TIPOS[tipo], "tipo_relacion_no_admitido")
                    exigir((fuente == "") == (tipo in (R + "/officeDocument", RELACIONES + "/metadata/core-properties",
                        R + "/extended-properties", R + "/custom-properties")), "origen_relacion_incoherente")
                    exigir(fuente == "" or not destino.startswith("docProps/"), "destino_relacion_incoherente")
                    c.guardar_textos(n, rid, tipo, destino)
                    relaciones.append(RelacionDOCX(n, rid, tipo, destino))
                    grafo.setdefault(fuente, set()).add(destino)
            del a
        alcanzadas, cola = set(), [""]
        while cola:
            c.paso()
            for destino in sorted(grafo.get(cola.pop(), ())):
                if destino not in alcanzadas:
                    alcanzadas.add(destino); cola.append(destino)
        exigir(all(n in alcanzadas for n in nombres if n != "[Content_Types].xml" and not n.endswith(".rels")),
                "parte_no_referenciada")
        # Estilos primero; las demás partes se recorren en orden estable.
        orden = sorted(nombres - {"[Content_Types].xml"}, key=lambda n: (n != "word/styles.xml", n))
        global_ambigua = False
        for n in orden:
            c.paso()
            if n.endswith(".rels"):
                continue
            i = archivos[n]
            _, raiz_esperada = perfil(n)
            if raiz_esperada is None:
                c.limite(i.file_size <= 1_048_576, "limite_imagen_pasiva")
                reales, prefijo = 0, b""
                with entrada_observable(z, i) as f:
                    while b := f.read(c.limites.zip.tamano_bloque):
                        c.paso()
                        reales += len(b)
                        c.ctx["descomprimidos"] += len(b)
                        c.limite(reales <= 1_048_576, "limite_imagen_pasiva")
                        c.limite(c.ctx["descomprimidos"] <= c.limites.zip.max_bytes_descomprimidos,
                                 "limite_descompresion_real")
                        if not prefijo: prefijo = b[:8]
                exigir(reales == i.file_size, "tamano_descomprimido_no_coincide")
                exigir(prefijo.startswith(b"\x89PNG\r\n\x1a\n") if n.endswith("png") else prefijo.startswith(b"\xff\xd8\xff"),
                        "firma_imagen_no_admitida")
                c.diagnostico("imagen_no_renderizada_ni_interpretada", n, omision=True)
                continue
            namespaces_raiz = {}
            with arbol(z, i, c, namespaces_raiz=namespaces_raiz) as a:
                exigir(a.tag == raiz_esperada, "raiz_ooxml_no_admitida")
                ambigua = detectar(a, n, c, mapas.get(n, {}), namespaces_raiz)
                registrar_usos(a, n, pendientes, c, ext.ref)
                if n in ("word/styles.xml", "word/settings.xml") and ambigua:
                    global_ambigua = True
                es_texto = n == "word/document.xml" or n.startswith(("word/header", "word/footer")) or n in (
                    "word/footnotes.xml", "word/endnotes.xml")
                if ambigua:
                    c.diagnostico("campos_revisiones_o_caracteristicas_no_interpretadas", n, omision=True, incompleta=True)
                if n == "word/styles.xml": ext.estilos_de(a)
                elif n.startswith("docProps/"): ext.metadatos(n, a)
                elif n == "word/comments.xml":
                    c.diagnostico("comentarios_no_extraidos", n, omision=True, incompleta=True)
                elif es_texto and not ambigua:
                    ext.contenido(n, a)
                elif not es_texto:
                    c.diagnostico("formato_auxiliar_no_renderizado", n, omision=True)
            del a
        if global_ambigua:
            ext.parrafos.clear(); ext.tablas.clear()
            c.diagnostico("formato_global_ambiguo_texto_omitido", omision=True, incompleta=True)
        exigir(ext.usos_notas <= ext.ids_notas, "nota_referenciada_ausente")
        finalizar(pendientes, c)
        # Solo promover tamaños/CRC tras las lecturas observables de cada parte.
        for n in sorted(nombres):
            c.paso()
            i = archivos[n]
            esperado, _ = perfil(n)
            c.guardar_textos(n, esperado, f"{i.CRC:08x}")
            partes.append(ParteDOCX(n, esperado, i.compress_size, i.file_size, i.file_size, f"{i.CRC:08x}"))
        c.lecturas2 = segunda.leidos
    if not ext.parrafos:
        c.diagnostico("sin_parrafos_extraidos_en_alcance")
    c.paso()
    return tuple(partes), tuple(relaciones), tuple(ext.parrafos), tuple(ext.tablas), tuple(ext.propiedades)
