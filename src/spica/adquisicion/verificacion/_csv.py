"""Muestra de texto acotada, sin inferir columnas científicas ni codificaciones."""

import codecs
import csv
from io import StringIO
import json
import re

from .modelos import DetalleCSV, EstadoEstructura

DELIMITADORES = (",", ";", "\t", "|")
CODIFICACIONES = {"ascii", "utf-8", "utf-8-sig", "utf-16", "utf-16-le", "utf-16-be",
                 "utf-32", "utf-32-le", "utf-32-be", "cp1252", "iso8859-1"}


def _texto(datos, completa, codificacion):
    bom, codec_bom = None, None
    for marca, codec, etiqueta in (
            (codecs.BOM_UTF32_LE, "utf-32", "utf-32-le"), (codecs.BOM_UTF32_BE, "utf-32", "utf-32-be"),
            (codecs.BOM_UTF8, "utf-8-sig", "utf-8-sig"), (codecs.BOM_UTF16_LE, "utf-16", "utf-16-le"),
            (codecs.BOM_UTF16_BE, "utf-16", "utf-16-be")):
        if datos.startswith(marca):
            bom, codec_bom = etiqueta, codec
            break
    compatibles = {bom, codec_bom} | ({"utf-8"} if bom == "utf-8-sig" else set())
    if codificacion and bom and codificacion not in compatibles:
        return None, codificacion, bom, None
    segura = bool(codificacion or bom or datos.isascii())
    codec = codificacion or codec_bom or ("ascii" if datos.isascii() else "utf-8")
    try:
        texto = codecs.getincrementaldecoder(codec)(errors="strict").decode(datos, final=completa)
    except UnicodeError:
        return None, codec if codificacion or bom else None, bom, segura
    return texto.removeprefix("\ufeff"), codec, bom, segura


def _avanzar_comillas(estado, caracter, delimitador):
    """Transición compartida por muestreo y streaming; None indica sintaxis inválida."""
    if estado == "entrecomillado":
        return "cerrado" if caracter == '"' else estado
    if estado == "cerrado":
        if caracter == '"':
            return "entrecomillado"
        return "inicio" if caracter == delimitador or caracter in "\r\n" else None
    if caracter == '"':
        return "entrecomillado" if estado == "inicio" else None
    return "inicio" if caracter == delimitador or caracter in "\r\n" else "campo"


def _comillas_coherentes(texto, delimitador):
    # csv.reader(strict=True) admite comillas literales en campos sin entrecomillar.
    estado = "inicio"
    for caracter in texto:
        estado = _avanzar_comillas(estado, caracter, delimitador)
        if estado is None:
            return False
    return estado != "entrecomillado"


def inspeccionar_texto(lectura, tamano, politica, contexto, codificacion, delimitador, encabezado):
    limite = politica.max_muestra_csv
    partes, restante = [], min(tamano, limite + 1)
    while restante:
        bloque = lectura.read(min(restante, politica.tamano_bloque))
        if not bloque:
            break
        partes.append(bloque)
        restante -= len(bloque)
    datos = b"".join(partes)
    completa = tamano <= limite and len(datos) == tamano
    datos = datos[:limite]
    texto, codec, bom, segura = _texto(datos, completa, codificacion)
    detalle = DetalleCSV(codec, bom, encabezado_declarado=encabezado)
    contexto["csv"] = detalle
    contexto["comprobaciones"].append("muestra_texto_codificacion_bom")
    if texto is None:
        if segura is None:
            return None, EstadoEstructura.INCIERTA, "bom_y_codificacion_declarada_incompatibles", completa
        estado = EstadoEstructura.ILEGIBLE_O_CORRUPTA if segura else EstadoEstructura.INCIERTA
        return None, estado, "texto_no_decodificable_con_evidencia_disponible", completa
    if not texto:
        return None, EstadoEstructura.INCIERTA, "archivo_sin_registros_csv", completa
    if any((ord(c) < 32 and c not in "\t\r\n") or ord(c) == 127 for c in texto):
        return None, EstadoEstructura.NO_RECONOCIDA, "texto_con_bytes_nulos_o_controles_binarios", completa
    inicio = texto.lstrip()
    if re.match(r"(?is)^(?:<!doctype\s+html\b|<(?:html|head|body|title|script|div|table|p)\b)", inicio):
        contexto["comprobaciones"].append("firma_textual_html")
        return "html", None, "contenido_html_identificado", False
    if inicio.startswith(("{", "[")):
        if completa:
            try:
                json.loads(texto)
            except (ValueError, RecursionError):
                pass
            else:
                contexto["comprobaciones"].append("sintaxis_json_completa")
                return "json", None, "contenido_json_identificado", True
        return None, EstadoEstructura.INCIERTA, "posible_json_sin_csv_comprobado", completa
    candidatos, malformada, limitada, lector_ejecutado = [], False, False, False
    for separador in ((delimitador,) if delimitador else DELIMITADORES):
        columnas, registros, consistente = None, 0, True
        if not _comillas_coherentes(texto, separador):
            malformada = True
            continue
        try:
            lector = csv.reader(StringIO(texto, newline=""), delimiter=separador, strict=True)
            lector_ejecutado = True
            for fila in lector:
                if registros == politica.max_registros_csv:
                    limitada = True
                    break
                registros += 1
                if (len(fila) > politica.max_campos_csv
                        or any(len(c) > politica.max_campo_csv for c in fila)):
                    limitada = True
                    consistente = False
                    break
                if columnas is None:
                    columnas = len(fila)
                if len(fila) != columnas:
                    consistente = False
            if consistente and columnas and columnas >= 2 and registros >= 2:
                candidatos.append((separador, columnas, registros))
            elif columnas and columnas >= 2:
                malformada |= not consistente
        except csv.Error as error:
            if "field larger than field limit" in str(error):
                limitada = True
            else:
                malformada = True
    contexto["comprobaciones"].append("comillas_csv_estrictas")
    if lector_ejecutado:
        contexto["comprobaciones"].append("registros_csv_reader_estricto")
    if len(candidatos) == 1:
        separador, columnas, registros = candidatos[0]
        contexto["csv"] = DetalleCSV(codec, bom, separador, encabezado, columnas, registros)
    if not completa or limitada:
        return None, EstadoEstructura.INCOMPLETA, "limite_muestra_registros_o_campos_csv", False
    if len(candidatos) > 1:
        return None, EstadoEstructura.INCIERTA, "delimitador_csv_ambiguo", True
    if len(candidatos) == 1:
        if not segura:
            return None, EstadoEstructura.INCIERTA, "utf8_compatible_sin_codificacion_confirmada", True
        return "csv", None, "estructura_csv_regular_en_archivo_completo", True
    if malformada:
        return None, EstadoEstructura.ILEGIBLE_O_CORRUPTA, "registros_csv_malformados", True
    return None, EstadoEstructura.INCIERTA, "sin_evidencia_suficiente_de_csv", True
