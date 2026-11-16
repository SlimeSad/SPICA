"""Adaptador físico TEMP. Reutiliza primitivas RAW sin instanciar su almacén."""

from collections import Counter
from pathlib import Path
import os
import re
import stat
from uuid import uuid4

from ..adquisicion.almacenamiento.raw import _segura, _huella, AlmacenRAW
from ..adquisicion.almacenamiento.modelos import ErrorAlmacenamientoRAW


class ErrorArchivoExperimental(Exception):
    def __init__(self, codigo):
        super().__init__(codigo)
        self.codigo = codigo


def controlar(evento):
    if evento is not None and evento.is_set():
        raise ErrorArchivoExperimental("cancelacion_observada")


def base_temporal():
    # gettempdir() puede escribir una sonda en su primera llamada. El lector
    # independiente usa la ubicación ambiental explícita, sin sondas de escritura.
    valor = (os.environ.get("TEMP") or os.environ.get("TMP")) if os.name == "nt" else (os.environ.get("TMPDIR") or "/tmp")
    if valor is None:
        raise ErrorArchivoExperimental("base_temporal_no_configurada")
    p = Path(valor)
    if (not p.is_absolute() or ".." in p.parts or p.drive.startswith("\\\\")
            or p.is_relative_to(Path(__file__).resolve().parents[3])
            or any(c.casefold() in {"spica_datos", ".git", ".venv", ".codex", ".agents"} for c in p.parts)):
        raise ErrorArchivoExperimental("base_temporal_no_admitida")
    segura(p)
    return p


def segura(p):
    try:
        _segura(p)
        for a in (p, *p.parents):
            try:
                s = a.lstat()
            except FileNotFoundError:
                continue
            if getattr(s, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                raise ErrorArchivoExperimental("reparse_point_no_admitido")
    except ErrorAlmacenamientoRAW:
        raise ErrorArchivoExperimental("ruta_o_enlace_no_admitido") from None


def firma(s):
    return AlmacenRAW._identidad(s) + (s.st_nlink,)


def huella(archivo, bloque, limite):
    try:
        return _huella(archivo, bloque, limite)
    except ErrorAlmacenamientoRAW:
        raise ErrorArchivoExperimental("limite_fisico_excedido") from None


class LectorControlado:
    def __init__(self, archivo, evento):
        self.archivo, self.evento, self.leidos = archivo, evento, 0

    def read(self, n):
        controlar(self.evento)
        b = self.archivo.read(n)
        self.leidos += len(b)
        return b


class ArchivosTEMP:
    """Raíz plana con identidad comprobada. No inventario persistente ni recuperación."""

    def __init__(self, instancia_id, identidad_raiz=None):
        if type(instancia_id) is not str or not re.fullmatch(r"[0-9a-f]{32}", instancia_id):
            raise ErrorArchivoExperimental("instancia_temporal_no_admitida")
        self.instancia_id = instancia_id
        self.raiz = base_temporal() / ("spica-rc5-" + instancia_id)
        self.identidad_raiz = identidad_raiz
        self.creados = {}  # Solo nombres/inodos creados por esta instancia en el proceso.

    @classmethod
    def crear(cls):
        a = cls(uuid4().hex)
        a.raiz.mkdir(mode=0o700)  # Exclusivo; no reinicializar un directorio existente.
        s = a.raiz.lstat()
        a.identidad_raiz = (s.st_dev, s.st_ino)
        a.validar()
        return a

    def validar(self):
        segura(self.raiz)
        s = self.raiz.lstat()
        if not stat.S_ISDIR(s.st_mode) or (s.st_dev, s.st_ino) != self.identidad_raiz:
            raise ErrorArchivoExperimental("raiz_temporal_sustituida_o_incompatible")

    def ruta(self, nombre):
        if type(nombre) is not str or not re.fullmatch(r"(?:a-[0-9a-f]{64}\.bin|t-[0-9a-f]{32}\.tmp|escritor\.lock)", nombre):
            raise ErrorArchivoExperimental("referencia_fisica_insegura")
        self.validar()
        p = self.raiz / nombre
        segura(p)
        return p

    def registrar(self, nombre, s):
        self.creados[nombre] = (s.st_dev, s.st_ino)

    def abrir_nuevo(self, nombre):
        if len(self.creados) >= 128:
            raise ErrorArchivoExperimental("cota_archivos_temporales_excedida")
        f = self.ruta(nombre).open("xb")
        self.registrar(nombre, os.fstat(f.fileno()))
        return f

    def quitar_propio(self, nombre):
        p = self.ruta(nombre)
        s = p.lstat()
        if not stat.S_ISREG(s.st_mode) or self.creados.get(nombre) != (s.st_dev, s.st_ino):
            raise ErrorArchivoExperimental("archivo_propio_sustituido")
        p.unlink()
        del self.creados[nombre]

    def regular(self, nombre):
        p = self.ruta(nombre)
        s = p.lstat()
        if not stat.S_ISREG(s.st_mode) or s.st_nlink != 1:
            raise ErrorArchivoExperimental("archivo_no_regular_o_enlace_duro")
        return p, s

    def leer(self, nombre, limite, bloque, evento):
        lector = None
        try:
            p, inicial = self.regular(nombre)
            if inicial.st_size > limite:
                raise ErrorArchivoExperimental("limite_fisico_excedido")
            with p.open("rb") as f:
                antes = os.fstat(f.fileno())
                if firma(inicial) != firma(antes):
                    raise ErrorArchivoExperimental("archivo_cambio_antes_de_lectura")
                lector = LectorControlado(f, evento)
                total, sha = huella(lector, bloque, limite)
                despues = os.fstat(f.fileno())
            _, final = self.regular(nombre)
            controlar(evento)
            if firma(inicial) != firma(despues) or firma(inicial) != firma(final) or total != inicial.st_size:
                raise ErrorArchivoExperimental("archivo_cambio_durante_lectura")
            return total, sha
        except BaseException as e:
            e.bytes_leidos = 0 if lector is None else lector.leidos
            raise

    def limpiar(self):
        """Sin recursión. Ante archivos ajenos/sustitución se conserva la raíz."""
        self.validar()
        existentes = tuple(self.raiz.iterdir())
        firmas = {}
        for p in existentes:
            segura(p)
            s = p.lstat()
            if not stat.S_ISREG(s.st_mode) or self.creados.get(p.name) != (s.st_dev, s.st_ino):
                raise ErrorArchivoExperimental("limpieza_requiere_revision")
            firmas[p.name] = s
        enlaces = Counter((s.st_dev, s.st_ino) for s in firmas.values())
        if any(enlaces[(s.st_dev, s.st_ino)] != s.st_nlink for s in firmas.values()):
            raise ErrorArchivoExperimental("limpieza_con_enlaces_ajenos")
        for nombre in firmas:
            self.quitar_propio(nombre)
        self.validar()
        self.raiz.rmdir()
