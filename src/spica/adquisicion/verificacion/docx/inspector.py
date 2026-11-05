"""API de lectura DOCX offline. Nunca descarga, extrae a disco o escribe."""

from dataclasses import replace
import hashlib
import os
from pathlib import Path
import re
import stat
from threading import Event
import time

from ..modelos import EstadoEstructura, _Hallazgo
from ._control import Control, _Fallo, exigir
from ._paquete import inspeccionar_paquete
from .modelos import (
    ConsumoDOCX, DiagnosticoDOCX, EstadoInspeccionDOCX as E,
    IdentidadDOCX, LimitesDOCX, ResultadoDOCX,
)


def _control(limites, cancelacion, reloj, identificador):
    if not isinstance(identificador, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", identificador):
        raise ValueError("identificador_local_neutro_requerido")
    if limites is not None and type(limites) is not LimitesDOCX:
        raise TypeError("limites_docx_requeridos")
    if cancelacion is not None and not isinstance(cancelacion, Event):
        raise TypeError("evento_cancelacion_requerido")
    if not callable(reloj):
        raise TypeError("reloj_requerido")
    return Control(limites or LimitesDOCX(), cancelacion if cancelacion is not None else Event(), reloj)


def _esperados(tamano, sha256):
    if tamano is not None and (type(tamano) is not int or tamano < 0):
        raise ValueError("tamano_esperado_no_admitido")
    if sha256 is not None and (type(sha256) is not str or not re.fullmatch(r"[0-9a-f]{64}", sha256)):
        raise ValueError("sha256_esperado_no_admitido")


def _consumo(c):
    return ConsumoDOCX(c.lecturas1, c.lecturas2, c.verificados, c.ctx["descomprimidos"],
        c.xml, c.ctx["nodos_xml"], c.pico, c.lecturas0)


def _resultado(c, estado, codigo=None, componentes=None):
    partes, relaciones, parrafos, tablas, propiedades = (componentes if componentes is not None
        else (tuple(c.partes), tuple(c.relaciones), (), (), ()))
    return ResultadoDOCX(estado, c.identidad, c.limites, partes, relaciones,
        parrafos, tablas, propiedades, tuple(c.advertencias),
        (DiagnosticoDOCX(codigo),) if codigo and estado is E.DOCUMENTO_RECHAZADO else (),
        tuple(c.omitidas) + ((DiagnosticoDOCX(codigo),) if codigo and estado is E.INSPECCION_INCOMPLETA else ()),
        consumo=_consumo(c))


def _evaluar(datos, c):
    try:
        exigir(bool(datos), "archivo_vacio_no_es_docx")
        componentes = inspeccionar_paquete(datos, c)
        return _resultado(c, E.INSPECCION_INCOMPLETA if c.incompleta else E.DOCUMENTO_VALIDADO_EN_ALCANCE,
                          componentes=componentes)
    except _Fallo as error:
        return _resultado(c, error.estado, error.codigo)
    except _Hallazgo as error:
        return _resultado(c, E.INSPECCION_INCOMPLETA if error.estado is EstadoEstructura.INCOMPLETA else E.DOCUMENTO_RECHAZADO,
                          error.codigo)
    except Exception:
        # No reflejar rutas, XML, cabeceras, notas de excepción o contenido recibido.
        return _resultado(c, E.DOCUMENTO_RECHAZADO, "paquete_no_inspeccionable")


def inspeccionar_docx_bytes(datos: bytes, *, identificador="memoria", limites=None,
                           cancelacion=None, reloj=time.monotonic) -> ResultadoDOCX:
    """Snapshot bytes inmutable acotado; no realiza ninguna lectura de archivo."""
    if type(datos) is not bytes:
        raise TypeError("snapshot_bytes_requerido")
    c = _control(limites, cancelacion, reloj, identificador)
    try:
        c.paso()
        c.identidad = IdentidadDOCX(identificador, "memoria", len(datos), None)
        c.limite(len(datos) <= c.limites.max_archivo, "limite_archivo")
        digest = hashlib.sha256()
        for inicio in range(0, len(datos), c.limites.zip.tamano_bloque):
            c.paso()
            digest.update(datos[inicio:inicio + c.limites.zip.tamano_bloque])
        c.identidad = replace(c.identidad, sha256=digest.hexdigest())
    except _Fallo as error:
        return _resultado(c, error.estado, error.codigo)
    return _evaluar(datos, c)


def _firma(s):
    return s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns


def _ruta_autorizada(ruta, directorio):
    exigir(isinstance(ruta, Path) and isinstance(directorio, Path), "rutas_path_requeridas")
    exigir(ruta.is_absolute() and directorio.is_absolute() and ".." not in ruta.parts and ".." not in directorio.parts,
            "ruta_absoluta_sin_escapes_requerida")
    exigir(ruta != directorio and ruta.is_relative_to(directorio), "archivo_fuera_del_directorio_autorizado")
    prohibidos = {"CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$",
        *(f"COM{i}" for i in range(10)), *(f"LPT{i}" for i in range(10))}
    exigir(not any(":" in p or p.endswith((".", " ")) or p.split(".")[0].upper() in prohibidos
        or any(ord(x) < 32 for x in p) for p in ruta.parts[1:]), "componente_local_no_admitido")
    # No seguir un reparse point, incluso si su destino es aparentemente interno.
    for p in reversed((ruta, *ruta.parents)):
        s = p.lstat()
        exigir(not stat.S_ISLNK(s.st_mode) and not getattr(s, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0),
                "enlace_o_reparse_no_admitido")
    exigir(stat.S_ISDIR(directorio.stat().st_mode) and stat.S_ISREG(ruta.stat().st_mode), "archivo_regular_requerido")
    exigir(ruta.resolve(strict=True).is_relative_to(directorio.resolve(strict=True)), "escape_del_directorio_autorizado")
    return ruta


def _leer(ruta, c, *, conservar):
    c.paso()
    inicial = ruta.lstat()
    exigir(stat.S_ISREG(inicial.st_mode), "archivo_regular_requerido")
    c.limite(inicial.st_size <= c.limites.max_archivo, "limite_archivo")
    digest = hashlib.sha256()
    datos = bytearray() if conservar else None
    leidos = 0
    with ruta.open("rb") as f:
        exigir(_firma(inicial) == _firma(os.fstat(f.fileno())), "archivo_sustituido")
        while b := f.read(min(c.limites.zip.tamano_bloque, c.limites.max_archivo - leidos + 1)):
            c.paso()
            leidos += len(b)
            c.limite(leidos <= c.limites.max_archivo, "limite_archivo")
            digest.update(b)
            if conservar: datos.extend(b)
        exigir(_firma(inicial) == _firma(os.fstat(f.fileno())) == _firma(ruta.lstat()), "archivo_modificado_durante_lectura")
    return bytes(datos) if conservar else None, leidos, digest.hexdigest(), _firma(inicial)


def inspeccionar_docx_archivo(ruta: Path, *, directorio_autorizado: Path,
                             identificador="archivo_local", tamano_esperado=None,
                             sha256_esperado=None, limites=None, cancelacion=None,
                             reloj=time.monotonic) -> ResultadoDOCX:
    """Solo lectura del archivo exacto, dentro de una raíz explícita del llamador.

    Hash antes/después; si se cancela o agota el plazo, no se afirma conservación
    final no ejecutada. Los controles no sustituyen aislamiento frente a un
    propietario malicioso que cambie rutas concurrentemente.
    """
    _esperados(tamano_esperado, sha256_esperado)
    c = _control(limites, cancelacion, reloj, identificador)
    inicial = None
    try:
        c.paso()
        ruta = _ruta_autorizada(ruta, directorio_autorizado)
        c.identidad = IdentidadDOCX(identificador, "archivo", ruta.stat().st_size, None)
        datos, n, digest, firma = _leer(ruta, c, conservar=True)
        inicial = (n, digest, firma)
        c.identidad = IdentidadDOCX(identificador, "archivo", n, digest)
        exigir((tamano_esperado is None or tamano_esperado == n)
                and (sha256_esperado is None or sha256_esperado == digest), "identidad_esperada_no_coincide")
        resultado = _evaluar(datos, c)
    except _Fallo as error:
        resultado = _resultado(c, error.estado, error.codigo)
    except Exception:
        resultado = _resultado(c, E.DOCUMENTO_RECHAZADO, "archivo_no_disponible")
    if inicial is not None:
        try:
            c.paso()
            _ruta_autorizada(ruta, directorio_autorizado)
            _, n, digest, firma = _leer(ruta, c, conservar=False)
            exigir((n, digest, firma) == inicial, "integridad_final_no_coincide")
            resultado = replace(resultado, conservacion_comprobada=True)
        except _Fallo as error:
            if resultado.estado is E.DOCUMENTO_RECHAZADO and error.estado is E.INSPECCION_INCOMPLETA:
                resultado = replace(resultado, operaciones_omitidas=resultado.operaciones_omitidas + (DiagnosticoDOCX(error.codigo),))
            else:
                nuevo = _resultado(c, error.estado, error.codigo)
                resultado = replace(nuevo, causas_rechazo=resultado.causas_rechazo + nuevo.causas_rechazo,
                    conservacion_comprobada=False if error.estado is E.DOCUMENTO_RECHAZADO else None)
        except Exception:
            resultado = replace(_resultado(c, E.DOCUMENTO_RECHAZADO, "verificacion_final_no_disponible"), conservacion_comprobada=False)
    return replace(resultado, consumo=_consumo(c))
