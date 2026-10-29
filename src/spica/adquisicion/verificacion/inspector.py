"""Inspección local de solo lectura; sin HTTP, SQLite ni extracción de archivos."""

import codecs
from datetime import datetime, timezone
import os
from pathlib import Path, PurePosixPath
import re
import stat
from urllib.parse import urlsplit

from ._csv import CODIFICACIONES, DELIMITADORES, inspeccionar_texto
from .modelos import EstadoEstructura, PoliticaEstructura, ResultadoEstructura, _Hallazgo, _limite

TIPOS = {
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "csv": "text/csv", "html": "text/html", "json": "application/json",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "zip": "application/zip",
}


def _extension(nombre):
    if not isinstance(nombre, str):
        return None
    try:
        extension = PurePosixPath(urlsplit(nombre).path.replace("\\", "/")).suffix[1:].lower()
        return extension if extension in TIPOS else None
    except ValueError:
        return None


def _http(tipo):
    if not isinstance(tipo, str):
        return None
    base = tipo.split(";", 1)[0].strip().lower()
    return next((f for f, mime in TIPOS.items() if mime == base), "csv" if base == "application/csv" else None)


class _Lectura:
    def __init__(self, archivo, politica):
        self.archivo = archivo
        self.leidos = 0
        self.max_lectura = max(politica.max_central_zip, politica.tamano_bloque, 65_557)

    def read(self, cantidad=-1):
        if cantidad is None or cantidad < 0:
            cantidad = os.fstat(self.archivo.fileno()).st_size - self.tell()
        if cantidad > self.max_lectura:
            _limite("lectura_individual_superior_al_limite")
        datos = self.archivo.read(cantidad)
        self.leidos += len(datos)
        return datos

    def seek(self, *argumentos):
        return self.archivo.seek(*argumentos)

    def tell(self):
        return self.archivo.tell()

    def seekable(self):
        return True


def verificar_archivo(ruta: Path, *, formato_declarado: str | None = None,
                      tipo_medio_sugerido: str | None = None, nombre_sugerido: str | None = None,
                      codificacion: str | None = None, delimitador: str | None = None,
                      encabezado_declarado: bool | None = None,
                      politica: PoliticaEstructura | None = None) -> ResultadoEstructura:
    politica = politica if politica is not None else PoliticaEstructura()
    if not isinstance(politica, PoliticaEstructura):
        raise TypeError("Se requiere PoliticaEstructura")
    if codificacion is not None:
        try:
            codificacion = codecs.lookup(codificacion).name
        except (LookupError, TypeError):
            raise ValueError("Codificación explícita no admitida") from None
        if codificacion not in CODIFICACIONES:
            raise ValueError("Codificación explícita no admitida")
    if delimitador is not None and delimitador not in DELIMITADORES:
        raise ValueError("Delimitador explícito no admitido")
    if encabezado_declarado is not None and type(encabezado_declarado) is not bool:
        raise TypeError("Encabezado declarado debe ser bool o None")
    declaracion = (formato_declarado if isinstance(formato_declarado, str)
                   and re.fullmatch(r"[ A-Za-z0-9_.+-]{1,64}", formato_declarado) else None)
    esperado = declaracion.strip().lower() if declaracion else None
    contexto = dict(comprobaciones=[], descomprimidos=0, csv=None)
    lectura, tamano, formato, completa, estado = None, None, None, False, None
    diagnosticos = []
    try:
        ruta = Path(ruta).absolute()
        if any(p.is_symlink() or p.is_junction() for p in (ruta, *ruta.parents)):
            raise _Hallazgo(EstadoEstructura.ILEGIBLE_O_CORRUPTA, "enlace_de_archivo_no_admitido")
        if not stat.S_ISREG(ruta.stat().st_mode):
            raise _Hallazgo(EstadoEstructura.ILEGIBLE_O_CORRUPTA, "archivo_no_regular")
        with ruta.open("rb") as archivo:
            inicial = os.fstat(archivo.fileno())
            if not stat.S_ISREG(inicial.st_mode):
                raise _Hallazgo(EstadoEstructura.ILEGIBLE_O_CORRUPTA, "archivo_no_regular")
            tamano = inicial.st_size
            lectura = _Lectura(archivo, politica)
            prefijo = lectura.read(min(tamano, 4))
            lectura.seek(0)
            contexto["comprobaciones"].append("cabecera_y_archivo_regular")
            if prefijo.startswith(b"PK"):
                from ._xlsx import inspeccionar_zip
                formato, completa = inspeccionar_zip(lectura, tamano, politica, contexto)
            else:
                formato, estado, codigo, completa = inspeccionar_texto(
                    lectura, tamano, politica, contexto, codificacion, delimitador, encabezado_declarado)
                diagnosticos.append(codigo)
            def identidad(s):
                return s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns
            if identidad(inicial) != identidad(os.fstat(archivo.fileno())) or identidad(inicial) != identidad(ruta.stat()):
                raise _Hallazgo(EstadoEstructura.ILEGIBLE_O_CORRUPTA, "archivo_modificado_durante_inspeccion")
    except _Hallazgo as hallazgo:
        estado, completa, formato = hallazgo.estado, False, None
        diagnosticos.append(hallazgo.codigo)
    except Exception:
        estado, completa, formato = EstadoEstructura.ILEGIBLE_O_CORRUPTA, False, None
        diagnosticos.append("archivo_o_inspeccion_no_disponible")
    if estado is None:
        estado = (EstadoEstructura.NO_RECONOCIDA if formato is None else
                  EstadoEstructura.SIN_DECLARACION if esperado is None else
                  EstadoEstructura.COMPATIBLE if formato == esperado else EstadoEstructura.INCOMPATIBLE)
    if contexto.get("externas"):
        diagnosticos.append("relaciones_externas_no_abiertas")
    if formato and _http(tipo_medio_sugerido) not in (None, formato):
        diagnosticos.append("sugerencia_http_no_coincidente")
    if formato and _extension(nombre_sugerido) not in (None, formato):
        diagnosticos.append("sugerencia_extension_no_coincidente")
    return ResultadoEstructura(estado, declaracion, _extension(nombre_sugerido), _http(tipo_medio_sugerido),
        formato, TIPOS.get(formato), datetime.now(timezone.utc), tamano, lectura.leidos if lectura else 0,
        contexto["descomprimidos"], completa, tuple(contexto["comprobaciones"]), tuple(diagnosticos),
        politica, contexto["csv"])
