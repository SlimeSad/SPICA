"""Archivo local autorizado → staging propio → incorporación RAW existente."""

import hashlib
import os
from pathlib import Path
import shutil
import stat
from threading import Event
from uuid import uuid4

from ..almacenamiento import AlmacenRAW, DeclaracionRAW, ErrorAlmacenamientoRAW, EstadoIncorporacion
from ..almacenamiento.raw import _declaracion_publica, _segura
from ..almacenamiento._errores import _publicar
from .evidencias import empaquetar_manual
from .modelos import (
    ErrorIngestaManual, EstadoIngestaManual, FUENTE_RECEPCION_LOCAL, PoliticaIngestaManual,
    ReciboIngestaManual, ResultadoIngestaManual, SolicitudIngestaManual,
)


def _ruta(ruta):
    ruta = Path(ruta)
    if (not ruta.is_absolute() or ruta.drive.startswith("\\\\")
            or any(":" in p for p in ruta.parts[1:])):
        raise ErrorAlmacenamientoRAW("ruta_manual_no_local_o_ambigua")
    _segura(ruta)
    for componente in (ruta, *ruta.parents):
        s = componente.lstat()
        if getattr(s, "st_file_attributes", 0) & 0x400:
            raise ErrorAlmacenamientoRAW("reparse_point_no_admitido")
    return ruta


def _firma(s):
    return s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns


class IngestorManual:
    """Secuencial; raíces previamente preparadas y privadas, sin inicialización RAW."""

    def __init__(self, almacen: AlmacenRAW, raices_origen: tuple[Path, ...], staging: Path,
                 *, politica: PoliticaIngestaManual | None = None):
        if not isinstance(almacen, AlmacenRAW):
            raise TypeError("Almacén RAW abierto requerido")
        self.almacen = almacen
        self.politica = politica or PoliticaIngestaManual()
        if type(self.politica) is not PoliticaIngestaManual or self.politica.max_bytes > almacen.max_bytes:
            raise ValueError("Política manual incompatible con el límite RAW")
        if type(raices_origen) is not tuple or not raices_origen:
            raise TypeError("Raíces de origen explícitas requeridas")
        try:
            self.staging = _ruta(staging).resolve(strict=True)
            self.origenes = tuple(_ruta(p).resolve(strict=True) for p in raices_origen)
            if (not self.staging.is_dir() or self.staging.is_relative_to(almacen.raiz)
                    or not any(self.staging.is_relative_to(p) for p in almacen.entradas)):
                raise ErrorAlmacenamientoRAW("staging_manual_no_autorizado")
            if any(not p.is_dir() or p == Path(p.anchor)
                   or p.is_relative_to(almacen.raiz) or almacen.raiz.is_relative_to(p)
                   or any(p.is_relative_to(e) or e.is_relative_to(p) for e in almacen.entradas)
                   for p in self.origenes):
                raise ErrorAlmacenamientoRAW("raiz_origen_manual_no_admitida")
        except (OSError, ErrorAlmacenamientoRAW):
            publico = ValueError("directorios_manuales_no_admitidos")
        else:
            return
        _publicar(publico)

    def _origen(self, ruta):
        # No hacer resolve/stat sobre una ruta prohibida antes de esta comprobación.
        if (ruta.is_relative_to(self.almacen.raiz)
                or any(ruta.is_relative_to(p) for p in self.almacen.entradas)
                or not any(ruta.is_relative_to(p) for p in self.origenes)):
            raise ErrorAlmacenamientoRAW("origen_manual_no_autorizado")
        ruta = _ruta(ruta)
        s = ruta.lstat()
        if not stat.S_ISREG(s.st_mode) or s.st_nlink != 1:
            raise ErrorAlmacenamientoRAW("origen_no_regular_o_compartido")
        if s.st_size > self.politica.max_bytes:
            raise ErrorAlmacenamientoRAW("limite_manual_excedido")
        if not s.st_size and not self.politica.aceptar_vacios:
            raise ErrorAlmacenamientoRAW("archivo_vacio_no_admitido")
        return ruta, s

    @staticmethod
    def _cancelar(evento):
        if evento is not None and evento.is_set():
            raise ErrorAlmacenamientoRAW("ingesta_manual_cancelada")

    def _leer(self, origen, inicial, destino, evento):
        try:
            return self._copiar(origen, inicial, destino, evento)
        except OSError:
            raise ErrorAlmacenamientoRAW("lectura_manual_no_disponible") from None

    def _copiar(self, origen, inicial, destino, evento):
        tamano, huella = 0, hashlib.sha256()
        with origen.open("rb") as archivo:
            estado = os.fstat(archivo.fileno())
            if _firma(estado) != _firma(inicial) or not stat.S_ISREG(estado.st_mode) or estado.st_nlink != 1:
                raise ErrorAlmacenamientoRAW("origen_modificado")
            while True:
                self._cancelar(evento)
                bloque = archivo.read(min(self.politica.tamano_bloque, self.politica.max_bytes + 1))
                if not bloque:
                    break
                tamano += len(bloque)
                if tamano > self.politica.max_bytes:
                    raise ErrorAlmacenamientoRAW("limite_manual_excedido")
                if destino is not None:
                    try:
                        escritos = destino.write(bloque)
                    except OSError:
                        raise ErrorAlmacenamientoRAW("escritura_manual_no_disponible") from None
                    if escritos != len(bloque):
                        raise ErrorAlmacenamientoRAW("escritura_manual_incompleta")
                huella.update(bloque)
            final = origen.lstat()
            if (tamano != inicial.st_size or _firma(inicial) != _firma(os.fstat(archivo.fileno()))
                    or _firma(inicial) != _firma(final) or not stat.S_ISREG(final.st_mode) or final.st_nlink != 1):
                raise ErrorAlmacenamientoRAW("origen_modificado")
        self._cancelar(evento)
        digest = huella.hexdigest()
        return tamano, digest

    def _espacio(self, tamano):
        mismo_volumen = self.staging.stat().st_dev == self.almacen.raiz.stat().st_dev
        necesarios = tamano * (2 if mismo_volumen else 1) + self.politica.margen_libre
        if (shutil.disk_usage(self.staging).free < necesarios
                or shutil.disk_usage(self.almacen.raiz).free < necesarios):
            raise ErrorAlmacenamientoRAW("espacio_manual_insuficiente")

    def _limpiar(self, operacion):
        if operacion is None:
            return None
        try:
            _ruta(operacion)
            if operacion.parent != self.staging or not operacion.name.startswith("suadc-manual-"):
                return operacion
            archivo = operacion / "contenido.bin"
            if os.path.lexists(archivo):
                _ruta(archivo).unlink()
            operacion.rmdir()  # Solo el archivo propio y directorio vacío; sin borrado recursivo.
        except (OSError, ErrorAlmacenamientoRAW):
            return operacion
        return None

    def ingestar(self, solicitud: SolicitudIngestaManual, *, cancelacion: Event | None = None
                 ) -> ResultadoIngestaManual:
        if type(solicitud) is not SolicitudIngestaManual or (cancelacion is not None and type(cancelacion) is not Event):
            raise TypeError("Solicitud manual y cancelación tipadas requeridas")
        fase, operacion, activo_id = "validacion", None, None
        try:
            self._cancelar(cancelacion)
            doc = solicitud.procedencia
            declaracion = DeclaracionRAW(solicitud.proyecto_id, solicitud.objeto_id,
                doc.fuente_declarada or FUENTE_RECEPCION_LOCAL, solicitud.recurso_id,
                formato_declarado=doc.formato_declarado, tipo_medio_declarado=doc.tipo_medio_declarado)
            empaquetar_manual(doc, declaracion, solicitud.adquisicion_id)
            _declaracion_publica(declaracion, self.almacen.claves)
            fase = "origen"
            origen, inicial = self._origen(solicitud.archivo)
            anterior = self.almacen.consultar_adquisicion(solicitud.adquisicion_id, permitir_ausente=True)
            if anterior is not None:
                activo_id = getattr(anterior, "activo_id", None)
                if (type(anterior) is not ReciboIngestaManual or anterior.procedencia != doc
                        or anterior.activo.declaracion != declaracion):
                    raise ErrorAlmacenamientoRAW("conflicto_idempotencia_manual")
                if anterior.activo.estado is not EstadoIncorporacion.INCORPORADA:
                    raise ErrorAlmacenamientoRAW("adquisicion_manual_requiere_revision")
                fase = "idempotencia"
                tamano, huella = self._leer(origen, inicial, None, cancelacion)
                if (tamano, huella) != (anterior.activo.size_bytes, anterior.activo.sha256):
                    raise ErrorAlmacenamientoRAW("conflicto_contenido_manual")
                estado = EstadoIngestaManual.YA_REGISTRADA
            else:
                self._espacio(inicial.st_size)
                _ruta(self.staging)
                candidata = self.staging / ("suadc-manual-" + uuid4().hex)
                candidata.mkdir(mode=0o755 if os.name == "nt" else 0o700)
                operacion = candidata
                fase = "copia"
                with (operacion / "contenido.bin").open("xb") as archivo:
                    tamano, huella = self._leer(origen, inicial, archivo, cancelacion)
                    archivo.flush()
                    os.fsync(archivo.fileno())
                if doc.sha256_externo is not None and huella != doc.sha256_externo:
                    raise ErrorAlmacenamientoRAW("hash_externo_discrepante")
                self._cancelar(cancelacion)
                fase = "incorporacion"
                activo = self.almacen.incorporar_manual_documentado(operacion / "contenido.bin", declaracion, doc,
                    adquisicion_id=solicitud.adquisicion_id, tamano_esperado=tamano, sha256_esperado=huella)
                activo_id = activo.asset_id
                estado = EstadoIngestaManual.INCORPORADA
            fase = "comprobacion"
            self._cancelar(cancelacion)
            ruta = self.almacen.recuperar(activo_id)
            recibo = self.almacen.consultar_adquisicion(solicitud.adquisicion_id)
            if (type(recibo) is not ReciboIngestaManual or recibo.activo_id != activo_id
                    or recibo.procedencia != doc or recibo.activo.declaracion != declaracion
                    or recibo.activo.estado is not EstadoIncorporacion.INCORPORADA
                    or (recibo.activo.size_bytes, recibo.activo.sha256) != (tamano, huella)):
                raise ErrorAlmacenamientoRAW("recibo_manual_no_coincidente")
            self._cancelar(cancelacion)
        except BaseException as exc:
            restante = self._limpiar(operacion)
            if not isinstance(exc, Exception):
                if restante is not None:
                    exc.add_note("Temporal manual pendiente de revisión")
                raise
            codigo = (exc.codigo if isinstance(exc, ErrorAlmacenamientoRAW) else
                      "archivo_manual_ausente" if isinstance(exc, FileNotFoundError) else
                      "operacion_manual_sin_permisos" if isinstance(exc, PermissionError) else
                      "escritura_manual_no_disponible" if fase == "copia" else "ingesta_manual_no_disponible")
            publico = ErrorIngestaManual(codigo, fase, solicitud.adquisicion_id,
                activo_id=getattr(exc, "activo_id", None) or activo_id, temporal_restante=restante)
        else:
            restante = self._limpiar(operacion)
            if restante is None:
                return ResultadoIngestaManual(recibo, ruta, recibo.activo.comprobacion_utc, estado)
            publico = ErrorIngestaManual("limpieza_manual_requiere_revision", "limpieza", solicitud.adquisicion_id,
                                        activo_id=activo_id, temporal_restante=restante)
        _publicar(publico)
