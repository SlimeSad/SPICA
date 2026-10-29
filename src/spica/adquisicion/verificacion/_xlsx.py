"""ZIP/OOXML acotado: directorio previo, CRC y XML sin DTD ni extracción."""

import posixpath
import stat
import struct
from urllib.parse import unquote, urlsplit
from xml.etree.ElementTree import TreeBuilder
from xml.parsers import expat
from zipfile import BadZipFile, ZipFile, ZIP_STORED, ZIP_DEFLATED

from .modelos import EstadoEstructura, _Hallazgo, _corrupto, _limite

CONTENIDOS = "http://schemas.openxmlformats.org/package/2006/content-types"
RELACIONES = "http://schemas.openxmlformats.org/package/2006/relationships"
HOJAS = ("http://schemas.openxmlformats.org/spreadsheetml/2006/main", "http://purl.oclc.org/ooxml/spreadsheetml/main")
OFICINA = ("http://schemas.openxmlformats.org/officeDocument/2006/relationships", "http://purl.oclc.org/ooxml/officeDocument/relationships")
MIME_LIBRO = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"
MIME_HOJA = "application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"
MIME_WORD = "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"


def _directorio_previo(lectura, tamano, politica):
    longitud = min(tamano, 65_557)
    lectura.seek(tamano - longitud)
    cola = lectura.read(longitud)
    posicion = cola.rfind(b"PK\x05\x06")
    if posicion < 0 or len(cola) - posicion < 22:
        _corrupto("zip_fin_ausente_o_truncado")
    _, disco, disco_cd, numero_disco, numero, bytes_cd, inicio, comentario = struct.unpack_from("<4s4H2LH", cola, posicion)
    fin = tamano - longitud + posicion
    if posicion + 22 + comentario != len(cola):
        _corrupto("zip_fin_incoherente")
    if disco or disco_cd or numero_disco != numero:
        _corrupto("zip_multivolumen_no_admitido")
    if numero == 0xffff or bytes_cd == 0xffffffff or inicio == 0xffffffff:
        _limite("zip64_fuera_del_alcance_admitido")
    if numero > politica.max_entradas_zip or bytes_cd > politica.max_central_zip:
        _limite("limite_directorio_o_entradas_zip")
    if inicio + bytes_cd != fin:
        _corrupto("zip_directorio_fuera_de_rango")
    # No confiar en el contador del EOCD: contar registros antes de ZipFile,
    # cuyo constructor cargaría todo el directorio y crearía sus objetos.
    cantidad, cursor = 0, inicio
    while cursor < fin:
        lectura.seek(cursor)
        cabecera = lectura.read(46)
        if len(cabecera) != 46 or cabecera[:4] != b"PK\x01\x02":
            _corrupto("zip_directorio_corrupto")
        nombre, extra, nota = struct.unpack_from("<HHH", cabecera, 28)
        cursor += 46 + nombre + extra + nota
        cantidad += 1
        if cantidad > politica.max_entradas_zip:
            _limite("limite_entradas_reales_zip")
    if cursor != fin or cantidad != numero:
        _corrupto("zip_numero_entradas_incoherente")
    lectura.seek(0)
    return inicio, numero


def _nombre_seguro(nombre):
    decodificado = nombre
    for _ in range(3):
        decodificado = unquote(decodificado)
    for valor in (nombre, decodificado):
        partes = valor.rstrip("/").split("/")
        if (not valor or valor.startswith("/") or "\\" in valor or ":" in valor
                or any(p in ("", ".", "..") for p in partes)
                or any(ord(c) < 32 or ord(c) == 127 for c in valor)):
            _corrupto("zip_nombre_o_ruta_no_admitida")


def _destino(nombre_relaciones, destino, nombres):
    fuente = ("" if nombre_relaciones == "_rels/.rels" else
              posixpath.join(posixpath.dirname(posixpath.dirname(nombre_relaciones)),
                             posixpath.basename(nombre_relaciones).removesuffix(".rels")))
    if fuente and fuente not in nombres:
        _corrupto("relaciones_sin_parte_origen")
    uri = urlsplit(destino)
    if (uri.scheme or uri.netloc or uri.query or "\\" in destino
            or any(ord(c) < 32 or ord(c) == 127 for c in destino)):
        _corrupto("relacion_interna_no_admitida")
    ruta = unquote(uri.path)
    if unquote(ruta) != ruta or "\\" in ruta or ":" in ruta:
        _corrupto("relacion_interna_ambigua")
    resultado = (fuente if not ruta else posixpath.normpath(
        ruta.lstrip("/") if ruta.startswith("/") else posixpath.join(posixpath.dirname(fuente), ruta)))
    if resultado.startswith("../") or resultado in (".", "..") or resultado not in nombres:
        _corrupto("relacion_interna_sin_destino")
    return resultado


class _XML:
    def __init__(self, politica, contexto, construir=False):
        self.politica, self.contexto = politica, contexto
        self.arbol = TreeBuilder() if construir else None
        self.profundidad, self.raiz = 0, None
        self.enviados = 0
        self.parser = expat.ParserCreate(namespace_separator="}")
        self.parser.StartElementHandler = self.inicio
        self.parser.EndElementHandler = self.fin
        self.parser.StartDoctypeDeclHandler = self.prohibido
        self.parser.EntityDeclHandler = self.prohibido
        self.parser.ExternalEntityRefHandler = self.prohibido

    def prohibido(self, *argumentos):
        _corrupto("xml_dtd_o_entidades_no_admitidos")

    def inicio(self, nombre, atributos):
        self.profundidad += 1
        self.contexto["nodos_xml"] = self.contexto.get("nodos_xml", 0) + 1
        if (self.profundidad > self.politica.max_profundidad_xml
                or self.contexto["nodos_xml"] > self.politica.max_nodos_xml):
            _limite("limite_profundidad_o_nodos_xml")
        etiqueta = "{" + nombre if "}" in nombre else nombre
        if self.raiz is None:
            self.raiz = etiqueta
        if self.arbol is not None:
            self.arbol.start(etiqueta, {("{" + k if "}" in k else k): v for k, v in atributos.items()})

    def fin(self, nombre):
        if self.arbol is not None:
            self.arbol.end("{" + nombre if "}" in nombre else nombre)
        self.profundidad -= 1

    def alimentar(self, datos, final=False):
        try:
            self.enviados += len(datos)
            self.parser.Parse(datos, final)
            if self.enviados - self.parser.CurrentByteIndex > self.politica.max_xml_pendiente:
                _limite("limite_xml_pendiente_de_analisis")
        except expat.ExpatError:
            _corrupto("xml_no_bien_formado")

    def cerrar(self):
        self.alimentar(b"", True)
        return self.arbol.close() if self.arbol is not None else None


def _relaciones(arbol, nombre, nombres, contexto):
    if arbol.tag != "{" + RELACIONES + "}Relationships":
        _corrupto("xml_relaciones_no_reconocido")
    resultado = {}
    for elemento in arbol:
        identificador, tipo, destino = (elemento.get(c) for c in ("Id", "Type", "Target"))
        if (elemento.tag != "{" + RELACIONES + "}Relationship" or not identificador or not tipo
                or not destino or identificador in resultado):
            _corrupto("relacion_duplicada_o_incompleta")
        modo = elemento.get("TargetMode")
        if modo == "External":
            contexto["externas"] = True
            resultado[identificador] = (tipo, None)
        elif modo in (None, "Internal"):
            resultado[identificador] = (tipo, _destino(nombre, destino, nombres))
        else:
            _corrupto("modo_de_relacion_no_admitido")
    return resultado


def _tipos(arbol, nombres):
    if arbol.tag != "{" + CONTENIDOS + "}Types":
        _corrupto("content_types_no_reconocido")
    extensiones, partes = {}, {}
    for elemento in arbol:
        tipo = elemento.get("ContentType")
        if not tipo:
            _corrupto("tipo_de_contenido_ausente")
        if elemento.tag == "{" + CONTENIDOS + "}Override":
            nombre = elemento.get("PartName", "")
            if not nombre.startswith("/"):
                _corrupto("parte_content_types_invalida")
            nombre = nombre[1:]
            _nombre_seguro(nombre)
            if nombre in partes or nombre not in nombres:
                _corrupto("parte_content_types_duplicada_o_ausente")
            partes[nombre] = tipo
        elif elemento.tag == "{" + CONTENIDOS + "}Default":
            extension = elemento.get("Extension", "")
            if not extension or extension in extensiones:
                _corrupto("extension_content_types_duplicada_o_ausente")
            extensiones[extension] = tipo
        else:
            _corrupto("elemento_content_types_no_admitido")
    return {n: partes.get(n, extensiones.get(n.rsplit(".", 1)[-1])) for n in nombres}


def inspeccionar_zip(lectura, tamano, politica, contexto):
    inicio_cd, cantidad = _directorio_previo(lectura, tamano, politica)
    contexto["comprobaciones"].append("zip_directorio_previo_acotado")
    try:
        with ZipFile(lectura, "r") as contenedor:
            entradas = contenedor.infolist()
            if len(entradas) != cantidad:
                _corrupto("zip_numero_entradas_incoherente")
            nombres, normalizados, rangos, total = set(), set(), [], 0
            for entrada in entradas:
                _nombre_seguro(entrada.filename)
                normalizado = unquote(unquote(unquote(entrada.filename))).casefold()
                if entrada.filename != entrada.orig_filename or normalizado in normalizados:
                    _corrupto("zip_entrada_duplicada_o_ambigua")
                nombres.add(entrada.filename)
                normalizados.add(normalizado)
                tipo = stat.S_IFMT(entrada.external_attr >> 16)
                if tipo not in (0, stat.S_IFREG, stat.S_IFDIR):
                    _corrupto("zip_entrada_no_regular")
                if entrada.flag_bits & 1 or entrada.compress_type not in (ZIP_STORED, ZIP_DEFLATED):
                    raise _Hallazgo(EstadoEstructura.NO_RECONOCIDA, "zip_cifrado_o_compresion_no_admitida")
                total += entrada.file_size
                if (entrada.file_size > politica.max_bytes_entrada or total > politica.max_bytes_descomprimidos
                        or entrada.file_size > max(1, entrada.compress_size) * politica.max_expansion):
                    _limite("limite_tamano_o_expansion_zip")
                lectura.seek(entrada.header_offset)
                cabecera = lectura.read(30)
                if len(cabecera) != 30 or cabecera[:4] != b"PK\x03\x04":
                    _corrupto("zip_cabecera_local_corrupta")
                largo_nombre, extra = struct.unpack_from("<HH", cabecera, 26)
                fin = entrada.header_offset + 30 + largo_nombre + extra + entrada.compress_size
                if entrada.header_offset < 0 or fin > inicio_cd:
                    _corrupto("zip_entrada_fuera_de_rango")
                rangos.append((entrada.header_offset, fin))
            rangos.sort()
            if any(a[1] > b[0] for a, b in zip(rangos, rangos[1:])):
                _corrupto("zip_entradas_solapadas")
            contexto["comprobaciones"].append("zip_rutas_metodos_y_expansion")
            nombres = {n for n in nombres if not n.endswith("/")}
            ooxml = bool({"[Content_Types].xml", "xl/workbook.xml", "word/document.xml"} & nombres)
            controles, relaciones, raices = {}, {}, {}
            for entrada in entradas:
                if entrada.is_dir():
                    continue
                nombre = entrada.filename
                construir = ooxml and (nombre in {"[Content_Types].xml", "xl/workbook.xml"} or nombre.endswith(".rels"))
                if construir and entrada.file_size > politica.max_bytes_xml:
                    _limite("limite_xml_de_control")
                xml = _XML(politica, contexto, construir) if ooxml and (nombre.endswith(".xml") or nombre.endswith(".rels")) else None
                recibidos = 0
                with contenedor.open(entrada, "r") as archivo:
                    while bloque := archivo.read(politica.tamano_bloque):
                        recibidos += len(bloque)
                        contexto["descomprimidos"] += len(bloque)
                        if (recibidos > politica.max_bytes_entrada
                                or contexto["descomprimidos"] > politica.max_bytes_descomprimidos
                                or (construir and recibidos > politica.max_bytes_xml)):
                            _limite("limite_lectura_descomprimida_o_xml")
                        if xml is not None:
                            xml.alimentar(bloque)
                if recibidos != entrada.file_size:
                    _corrupto("zip_tamano_real_no_coincidente")
                if xml is not None:
                    arbol = xml.cerrar()
                    raices[nombre] = xml.raiz
                    if nombre.endswith(".rels"):
                        referencias = _relaciones(arbol, nombre, nombres, contexto)
                        if nombre in ("_rels/.rels", "xl/_rels/workbook.xml.rels"):
                            relaciones[nombre] = referencias
                    elif construir:
                        controles[nombre] = arbol
            contexto["comprobaciones"].append("zip_lectura_completa_crc_y_tamanos")
            if not ooxml:
                return "zip", True
            contexto["comprobaciones"].append("xml_sin_dtd_entidades_ni_recursos_externos")
            if "[Content_Types].xml" not in controles or "_rels/.rels" not in relaciones:
                _corrupto("ooxml_componentes_esenciales_ausentes")
            tipos = _tipos(controles["[Content_Types].xml"], nombres)
            if any(tipos[n] is None for n in nombres if n != "[Content_Types].xml"):
                _corrupto("ooxml_tipo_de_parte_no_declarado")
            principales = [(t, d) for t, d in relaciones["_rels/.rels"].values()
                           if t in {ns + "/officeDocument" for ns in OFICINA}]
            if len(principales) != 1 or principales[0][1] is None:
                _corrupto("ooxml_relacion_principal_invalida")
            principal = principales[0][1]
            if principal == "word/document.xml" and tipos.get(principal) == MIME_WORD:
                if raices.get(principal) == "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}document":
                    contexto["comprobaciones"].append("marcadores_docx_basicos")
                    return "docx", True
            if principal != "xl/workbook.xml" or tipos.get(principal) != MIME_LIBRO:
                return "zip", True
            libro = controles.get(principal)
            if libro is None or libro.tag not in {"{" + ns + "}workbook" for ns in HOJAS}:
                _corrupto("xlsx_raiz_de_libro_invalida")
            namespace = libro.tag.split("}")[0] + "}"
            hojas = libro.find(namespace + "sheets")
            vinculos = relaciones.get("xl/_rels/workbook.xml.rels", {})
            if hojas is None or not len(hojas):
                _corrupto("xlsx_sin_hojas_referenciadas")
            vistos, ids = set(), set()
            for hoja in hojas:
                rid = next((hoja.get("{" + ns + "}id") for ns in OFICINA if hoja.get("{" + ns + "}id") is not None), None)
                identificador = hoja.get("sheetId")
                if (hoja.tag != namespace + "sheet" or not rid or rid in vistos or not identificador
                        or identificador in ids or not hoja.get("name")):
                    _corrupto("xlsx_identidad_de_hoja_incoherente")
                vistos.add(rid)
                ids.add(identificador)
                tipo, destino = vinculos.get(rid, (None, None))
                if tipo in {ns + "/" + clase for ns in OFICINA for clase in ("chartsheet", "dialogsheet", "macrosheet", "intlMacrosheet")}:
                    raise _Hallazgo(EstadoEstructura.NO_RECONOCIDA, "tipo_de_hoja_fuera_del_alcance_admitido")
                if (tipo not in {ns + "/worksheet" for ns in OFICINA} or destino is None
                        or tipos.get(destino) != MIME_HOJA
                        or raices.get(destino) not in {"{" + ns + "}worksheet" for ns in HOJAS}):
                    _corrupto("xlsx_hoja_o_relacion_incoherente")
            if any(n.lower().endswith("vbaproject.bin") or tipos[n] and "macroenabled" in tipos[n].lower() for n in nombres):
                raise _Hallazgo(EstadoEstructura.NO_RECONOCIDA, "xlsx_contenido_activo_no_admitido")
            contexto["comprobaciones"].append("xlsx_content_types_libro_relaciones_y_hojas")
            return "xlsx", True
    except BadZipFile:
        _corrupto("zip_corrupto_o_crc_no_coincidente")
