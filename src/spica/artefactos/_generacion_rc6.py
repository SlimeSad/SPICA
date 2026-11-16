"""Adaptador plano RC6 de las primitivas TEMP RC5; ninguna ruta operativa."""

import io
import os
from pathlib import Path
import re
from uuid import uuid4

from ._archivos_rc5 import (
    ArchivosTEMP, ErrorArchivoExperimental, LectorControlado, base_temporal,
    controlar, firma, huella, segura,
)

BLOQUE = 65_536
MAX_ARCHIVO = 16_777_216
MAX_TOTAL = 67_108_864
_NOMBRE = re.compile(r"(?:datos-[0-9]{3}\.bin|metadatos\.json|manifiesto\.json|cierre\.json|intencion\.json|escritor\.lock|t-[0-9a-f]{32}\.tmp)")


class ArchivosGeneracion(ArchivosTEMP):
    def __init__(self, instancia_id, identidad_raiz=None):
        super().__init__(instancia_id, identidad_raiz)
        self.raiz = base_temporal() / ("spica-rc6-" + instancia_id)

    @classmethod
    def abrir(cls, raiz):
        p = Path(raiz)
        # Comprobar léxicamente antes de consultar la ubicación solicitada.
        if (not p.is_absolute() or ".." in p.parts or p.parent != base_temporal()
                or not re.fullmatch(r"spica-rc6-[0-9a-f]{32}", p.name)):
            raise ErrorArchivoExperimental("raiz_generacion_no_admitida")
        a = cls(p.name.removeprefix("spica-rc6-"))
        segura(p)
        s = p.lstat()
        a.identidad_raiz = s.st_dev, s.st_ino
        a.validar()
        return a

    def ruta(self, nombre):
        if type(nombre) is not str or not _NOMBRE.fullmatch(nombre):
            raise ErrorArchivoExperimental("referencia_generacion_insegura")
        self.validar()
        p = self.raiz / nombre
        segura(p)
        return p

    def nombres(self):
        self.validar()
        nombres = []
        with os.scandir(self.raiz) as entradas:
            for e in entradas:
                if len(nombres) >= 80:
                    raise ErrorArchivoExperimental("inventario_fisico_excesivo")
                nombres.append(e.name)
        return tuple(sorted(nombres))


class _Copia(LectorControlado):
    def __init__(self, archivo, evento, salida, limite):
        super().__init__(archivo, evento)
        self.salida, self.limite = salida, limite

    def read(self, n):
        b = super().read(n)
        if self.leidos > self.limite:
            raise ErrorArchivoExperimental("limite_copia_rc6")
        if self.salida is not None and self.salida.write(b) != len(b):
            raise ErrorArchivoExperimental("escritura_corta_rc6")
        return b


def transferir(fs, nombre, limite, evento=None, salida=None):
    """Adaptación de la copia K: delega SHA en huella RC5, coteja firmas."""
    controlar(evento)
    p, inicial = fs.regular(nombre)
    if inicial.st_size > limite:
        raise ErrorArchivoExperimental("limite_archivo_rc6")
    with p.open("rb") as f:
        if firma(os.fstat(f.fileno())) != firma(inicial):
            raise ErrorArchivoExperimental("archivo_cambio_antes_copia")
        resultado = huella(_Copia(f, evento, salida, limite), BLOQUE, limite)
        despues = os.fstat(f.fileno())
    _, final = fs.regular(nombre)
    controlar(evento)
    if firma(inicial) != firma(despues) or firma(inicial) != firma(final) or resultado[0] != inicial.st_size:
        raise ErrorArchivoExperimental("archivo_cambio_durante_copia")
    return resultado


def leer_metadatos(fs, nombre, limite):
    b = io.BytesIO()
    n, sha = transferir(fs, nombre, limite, salida=b)
    return b.getvalue(), n, sha


def publicar(fs, nombre, fuente, limite, evento=None, punto=lambda _: None):
    """Solo archivos propios. Un fallo conserva nombres y no hace fallback."""
    controlar(evento)
    if os.path.lexists(fs.ruta(nombre)):
        raise ErrorArchivoExperimental("destino_generacion_ocupado")
    temporal = "t-" + uuid4().hex + ".tmp"
    with fs.abrir_nuevo(temporal) as f:
        esperado = fuente(f)
        f.flush()
        os.fsync(f.fileno())
    if fs.leer(temporal, limite, BLOQUE, evento) != esperado:
        raise ErrorArchivoExperimental("copia_temporal_incorrecta")
    _, antes = fs.regular(temporal)
    punto("antes_enlace:" + nombre)
    controlar(evento)
    _, ahora = fs.regular(temporal)
    if firma(antes) != firma(ahora):
        raise ErrorArchivoExperimental("temporal_cambio_antes_publicacion")
    os.link(fs.ruta(temporal), fs.ruta(nombre))
    fs.registrar(nombre, fs.ruta(nombre).lstat())
    punto("enlace_publicado:" + nombre)
    fs.quitar_propio(temporal)
    if fs.leer(nombre, limite, BLOQUE, evento) != esperado:
        raise ErrorArchivoExperimental("publicacion_rc6_incorrecta")
    punto("archivo_publicado:" + nombre)
    return esperado
