"""CSV secuencial de solo lectura. No conoce HTTP, RAW, SQLite ni variables científicas."""

import codecs
import csv
from dataclasses import dataclass, fields
from datetime import datetime, timezone
from io import BytesIO
import os
from pathlib import Path
import re
import stat
from threading import Event

from ._csv import CODIFICACIONES, DELIMITADORES, _avanzar_comillas, _texto, inspeccionar_texto
from .modelos import EstadoEstructura, PoliticaEstructura

_SALTO = re.compile(r"\r\n|\r|\n")


@dataclass(frozen=True)
class PoliticaLecturaCSV:
    max_bytes_archivo: int = 134_217_728
    tamano_bloque: int = 65_536
    max_bytes_muestra: int = 65_536
    max_caracteres_linea: int = 262_144
    max_caracteres_registro: int = 1_048_576
    max_caracteres_campo: int = 65_536
    max_campos: int = 1024
    max_registros: int = 2_000_000
    max_diagnosticos: int = 20

    def __post_init__(self):
        for f in fields(self):
            if type(getattr(self, f.name)) is not int or getattr(self, f.name) <= 0:
                raise ValueError("Los límites CSV deben ser enteros positivos")
        if (self.tamano_bloque > 1_048_576 or self.max_bytes_muestra > 262_144
                or self.max_caracteres_linea > 1_048_576
                or self.max_caracteres_registro > 8_388_608
                or self.max_caracteres_campo > 65_536 or self.max_campos > 4096
                or self.max_diagnosticos > 1000):
            raise ValueError("Política superior a los topes de memoria CSV")


@dataclass(frozen=True)
class RegistroCSV:
    numero: int
    linea_inicial: int
    linea_final: int
    valores: tuple[str, ...]
    estructura_correcta: bool


@dataclass(frozen=True)
class DiagnosticoCSV:
    codigo: str
    registro: int | None
    linea_inicial: int | None
    linea_final: int | None
    columna: int | None = None
    byte: int | None = None  # Posición de base 1, si el decoder la conoce.


@dataclass(frozen=True)
class InformeLecturaCSV:
    estado: EstadoEstructura
    fecha_utc: datetime
    recorrido_completo: bool
    eof_alcanzado: bool
    motivo_fin: str
    tamano_archivo: int | None
    bytes_muestra: int
    bytes_recorrido: int
    lineas_fisicas: int
    registros_completos: int
    registros_correctos: int
    registros_problematicos: int
    registro_interrumpido: int | None
    campos_esperados: int | None
    primera_fila: tuple[str, ...] | None
    encabezado_declarado: bool | None
    codificacion: str | None
    codificacion_confirmada: bool
    bom: str | None
    delimitador: str | None
    dialecto: tuple[tuple[str, str], ...]
    diagnosticos: tuple[DiagnosticoCSV, ...]
    politica: PoliticaLecturaCSV


class _FalloCSV(Exception):
    def __init__(self, codigo, estado, *, linea=None, columna=None, byte=None):
        self.codigo, self.estado = codigo, estado
        self.linea, self.columna, self.byte = linea, columna, byte


class _Lineas:
    """Decoder estricto por bloques y líneas físicas acotadas, conservando CR/LF."""
    def __init__(self, archivo, codec, confirmada, politica, cancelacion):
        self.archivo, self.codec, self.confirmada = archivo, codec, confirmada
        self.p, self.cancelacion = politica, cancelacion
        self.bytes = self.linea = 0
        self.eof = self.no_ascii = False
        self.estado = "inicio"
        self.longitud_registro = self.longitud_campo = 0
        self.campos = 1
        self.iterador = self._lineas()

    def _bloques(self):
        decoder = codecs.getincrementaldecoder(self.codec)(errors="strict")
        while True:
            if self.cancelacion.is_set():
                raise _FalloCSV("cancelado", EstadoEstructura.INCOMPLETA)
            previo = self.bytes
            datos = self.archivo.read(min(self.p.tamano_bloque, self.p.max_bytes_archivo - self.bytes + 1))
            self.bytes += len(datos)
            if self.bytes > self.p.max_bytes_archivo:
                raise _FalloCSV("limite_bytes_archivo", EstadoEstructura.INCOMPLETA)
            estado = decoder.getstate()
            try:
                texto = decoder.decode(datos, final=not datos)
            except UnicodeDecodeError as error:
                # Entregar primero el prefijo válido: no perder líneas anteriores
                # por el read-ahead del decoder. No reemplazar el byte inválido.
                decoder.setstate(estado)
                n = max(0, error.start - len(estado[0]))
                prefijo = decoder.decode(datos[:n], final=False)
                if prefijo:
                    self.no_ascii |= not prefijo.isascii()
                    yield prefijo
                raise _FalloCSV("codificacion_invalida" if self.confirmada else "codificacion_no_resuelta",
                    EstadoEstructura.ILEGIBLE_O_CORRUPTA if self.confirmada else EstadoEstructura.INCIERTA,
                    byte=previo - len(estado[0]) + error.start + 1) from None
            self.no_ascii |= not texto.isascii()
            if texto:
                yield texto
            if not datos:
                self.eof = True
                return

    def _lineas(self):
        pendiente = ""
        try:
            for texto in self._bloques():
                pendiente += texto
                inicio = 0
                while True:
                    fin = _SALTO.search(pendiente, inicio)
                    if fin is None or (fin.group() == "\r" and fin.end() == len(pendiente)):
                        break
                    linea = pendiente[inicio:fin.end()]
                    inicio = fin.end()
                    if len(linea) > self.p.max_caracteres_linea:
                        raise _FalloCSV("limite_linea_fisica", EstadoEstructura.INCOMPLETA,
                                        columna=self.p.max_caracteres_linea + 1)
                    self.linea += 1
                    yield linea
                pendiente = pendiente[inicio:]
                if len(pendiente) > self.p.max_caracteres_linea:
                    raise _FalloCSV("limite_linea_fisica", EstadoEstructura.INCOMPLETA,
                                    columna=self.p.max_caracteres_linea + 1)
        except _FalloCSV as error:
            if error.byte is not None and pendiente.endswith("\r"):
                self.linea += 1
                yield pendiente
                pendiente = ""
            error.linea = self.linea + 1
            error.columna = error.columna or len(pendiente) + 1
            raise
        if pendiente:
            self.linea += 1
            yield pendiente

    def __iter__(self):
        return self

    def __next__(self):
        if self.cancelacion.is_set():
            raise _FalloCSV("cancelado", EstadoEstructura.INCOMPLETA, linea=self.linea + 1)
        linea = next(self.iterador)
        for columna, c in enumerate(linea, 1):
            self.longitud_registro += 1
            if self.longitud_registro > self.p.max_caracteres_registro:
                raise _FalloCSV("limite_registro", EstadoEstructura.INCOMPLETA,
                                linea=self.linea, columna=columna)
            previo = self.estado
            nuevo = _avanzar_comillas(previo, c, self.delimitador)
            if nuevo is None or ((ord(c) < 32 and c not in "\t\r\n") or ord(c) == 127):
                raise _FalloCSV("sintaxis_o_control_csv_invalido", EstadoEstructura.ILEGIBLE_O_CORRUPTA,
                                linea=self.linea, columna=columna)
            self.estado = nuevo
            if (previo == "entrecomillado" and c != '"') or (previo == "cerrado" and c == '"'):
                self.longitud_campo += 1
            elif previo not in ("entrecomillado", "cerrado") and c not in (self.delimitador, '"', "\r", "\n"):
                self.longitud_campo += 1
            if previo != "entrecomillado" and c == self.delimitador:
                self.campos += 1
                self.longitud_campo = 0
            if self.longitud_campo > self.p.max_caracteres_campo or self.campos > self.p.max_campos:
                raise _FalloCSV("limite_campo_o_numero_campos", EstadoEstructura.INCOMPLETA,
                                linea=self.linea, columna=columna)
        if self.estado != "entrecomillado":
            self.estado = "inicio"
            self.longitud_registro = self.longitud_campo = 0
            self.campos = 1
        return linea


class LectorCSV:
    """Usar con ``with`` y consumir secuencialmente. Informe independiente de las filas.

    Conserva solo una fila, la primera fila y diagnósticos acotados. No modifica
    csv.field_size_limit (global al proceso). El consumidor debe acotar sus agregados.
    """
    def __init__(self, ruta: Path, *, politica=None, codificacion=None, delimitador=None,
                 encabezado_declarado=None, campos_esperados=None, cancelacion=None):
        self.ruta = Path(ruta).absolute()
        self.politica = politica if politica is not None else PoliticaLecturaCSV()
        if not isinstance(self.politica, PoliticaLecturaCSV):
            raise TypeError("Se requiere PoliticaLecturaCSV")
        if codificacion is not None:
            codificacion = codecs.lookup(codificacion).name
            if codificacion not in CODIFICACIONES:
                raise ValueError("Codificación no admitida")
        if delimitador is not None and delimitador not in DELIMITADORES:
            raise ValueError("Delimitador no admitido")
        if encabezado_declarado is not None and type(encabezado_declarado) is not bool:
            raise TypeError("Indicador de encabezado debe ser bool o None")
        if campos_esperados is not None and (type(campos_esperados) is not int or
                                            not 0 < campos_esperados <= self.politica.max_campos):
            raise ValueError("Número de campos no admitido")
        self.codificacion, self.delimitador = codificacion, delimitador
        self.encabezado = encabezado_declarado
        self.esperados = campos_esperados
        self.cancelacion = cancelacion if cancelacion is not None else Event()
        self._archivo = None
        self._reiniciar()

    def _reiniciar(self):
        self._fuente = None
        self._inicial = None
        self._lector = None
        self._tamano = None
        self._muestra = 0
        self._registros = self._correctos = self._problemas = 0
        self._primera = self._interrumpido = None
        self._campos = self.esperados
        self._diagnosticos = []
        self._codigo = "lectura_no_completada"
        self._estado = EstadoEstructura.INCOMPLETA
        self._completo = self._finalizado = self._confirmada = False
        self._codec = self._bom = self._separador = None

    def _finalizar(self, estado, codigo):
        self._estado, self._codigo, self._finalizado = estado, codigo, True

    def __enter__(self):
        if self._archivo is not None:
            raise RuntimeError("Lector ya abierto")
        self._reiniciar()
        try:
            if ".." in self.ruta.parts or any(p.is_symlink() or p.is_junction() for p in (self.ruta, *self.ruta.parents)):
                raise _FalloCSV("ruta_no_admitida", EstadoEstructura.INCOMPLETA)
            if not stat.S_ISREG(self.ruta.stat().st_mode):
                raise _FalloCSV("archivo_no_regular", EstadoEstructura.INCOMPLETA)
            self._archivo = self.ruta.open("rb")
            self._inicial = os.fstat(self._archivo.fileno())
            self._tamano = self._inicial.st_size
            if self._tamano > self.politica.max_bytes_archivo:
                raise _FalloCSV("limite_bytes_archivo", EstadoEstructura.INCOMPLETA)
            muestra = self._archivo.read(min(self._tamano, self.politica.max_bytes_muestra))
            self._muestra = len(muestra)
            texto, codec, bom, segura = _texto(muestra[:4], False, self.codificacion)
            self._bom = bom
            if texto is None and segura is None:
                raise _FalloCSV("codificacion_no_resuelta_o_incompatible", EstadoEstructura.INCIERTA)
            self._confirmada = self.codificacion is not None or bom is not None
            self._codec = (codec or self.codificacion) if self._confirmada else "utf-8"
            contexto = dict(comprobaciones=[])
            p = PoliticaEstructura(max_muestra_csv=self.politica.max_bytes_muestra)
            formato, _, codigo, _ = inspeccionar_texto(BytesIO(muestra), self._tamano, p, contexto,
                self.codificacion, self.delimitador, self.encabezado)
            if formato in ("html", "json"):
                raise _FalloCSV("contenido_" + formato + "_no_csv", EstadoEstructura.INCOMPATIBLE)
            if codigo == "posible_json_sin_csv_comprobado":
                raise _FalloCSV(codigo, EstadoEstructura.INCIERTA)
            self._separador = self.delimitador
            if self._separador is None:
                self._separador = contexto["csv"].delimitador
            if self._separador is None:
                raise _FalloCSV("delimitador_no_resuelto", EstadoEstructura.INCIERTA)
            self._archivo.seek(0)
            self._fuente = _Lineas(self._archivo, self._codec, self._confirmada, self.politica, self.cancelacion)
            self._fuente.delimitador = self._separador
            self._lector = csv.reader(self._fuente, delimiter=self._separador, quotechar='"',
                                      doublequote=True, escapechar=None, skipinitialspace=False, strict=True)
        except _FalloCSV as error:
            self._finalizar(error.estado, error.codigo)
        except OSError:
            self._finalizar(EstadoEstructura.INCOMPLETA, "lectura_no_disponible")
        except BaseException:
            # __exit__ no se ejecuta si __enter__ es interrumpido.
            self._finalizar(EstadoEstructura.INCOMPLETA, "apertura_interrumpida")
            self.close()
            raise
        return self

    def __iter__(self):
        return self

    def __next__(self):
        if self._finalizado:
            raise StopIteration
        if self._archivo is None:
            raise RuntimeError("El lector requiere un contexto abierto")
        inicio = self._fuente.linea + 1
        try:
            if self._registros >= self.politica.max_registros:
                raise _FalloCSV("limite_registros", EstadoEstructura.INCOMPLETA, linea=inicio)
            valores = next(self._lector)
        except StopIteration:
            self._completo = self._fuente.eof
            self._confirmada |= not self._fuente.no_ascii
            if not self._fuente.no_ascii and self.codificacion is None and self._bom is None:
                self._codec = "ascii"
            estado = (EstadoEstructura.ILEGIBLE_O_CORRUPTA if self._problemas else
                      EstadoEstructura.INCIERTA if not self._registros or not self._confirmada else
                      EstadoEstructura.COMPATIBLE)
            self._finalizar(estado, "archivo_sin_registros" if not self._registros else
                            "codificacion_no_confirmada" if not self._confirmada else "eof")
            raise
        except (_FalloCSV, csv.Error, OSError) as error:
            if isinstance(error, _FalloCSV):
                estado, codigo = error.estado, error.codigo
            elif isinstance(error, csv.Error):
                estado = EstadoEstructura.INCOMPLETA if "field larger" in str(error) else EstadoEstructura.ILEGIBLE_O_CORRUPTA
                codigo = "limite_parser_csv_proceso" if estado is EstadoEstructura.INCOMPLETA else "registro_csv_malformado"
            else:
                estado, codigo = EstadoEstructura.INCOMPLETA, "lectura_no_disponible"
            if estado is EstadoEstructura.ILEGIBLE_O_CORRUPTA:
                self._problemas += 1
            self._interrumpido = self._registros + 1
            self._diagnosticos.append(DiagnosticoCSV(codigo, self._interrumpido, inicio,
                getattr(error, "linea", None) or self._fuente.linea,
                getattr(error, "columna", None), getattr(error, "byte", None)))
            self._finalizar(estado, codigo)
            raise StopIteration from None
        self._registros += 1
        if self._primera is None:
            self._primera = tuple(valores)
            self._campos = self._campos if self._campos is not None else len(valores)
        correcto = bool(self._campos) and len(valores) == self._campos
        if correcto:
            self._correctos += 1
        else:
            self._problemas += 1
            self._diagnosticos.append(DiagnosticoCSV("numero_campos_inconsistente", self._registros,
                                                    inicio, self._fuente.linea))
            if len(self._diagnosticos) >= self.politica.max_diagnosticos:
                self._finalizar(EstadoEstructura.INCOMPLETA, "limite_diagnosticos")
        return RegistroCSV(self._registros, inicio, self._fuente.linea, tuple(valores), correcto)

    def cancelar(self):
        self.cancelacion.set()

    def close(self):
        if self._archivo is not None:
            try:
                def firma(s):
                    return s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns
                if self._inicial is not None and (firma(self._inicial) != firma(os.fstat(self._archivo.fileno()))
                        or firma(self._inicial) != firma(self.ruta.stat())):
                    self._completo = False
                    self._finalizar(EstadoEstructura.ILEGIBLE_O_CORRUPTA, "archivo_modificado_durante_lectura")
            except OSError:
                self._completo = False
                self._finalizar(EstadoEstructura.INCOMPLETA, "comprobacion_final_no_disponible")
            finally:
                self._archivo.close()
                self._archivo = None
        if not self._finalizado:
            self._finalizar(EstadoEstructura.INCOMPLETA, "consumidor_detuvo_lectura")

    def __exit__(self, *args):
        self.close()

    @property
    def informe(self):
        s = self._fuente
        return InformeLecturaCSV(self._estado, datetime.now(timezone.utc), self._completo,
            s.eof if s else False, self._codigo, self._tamano, self._muestra, s.bytes if s else 0,
            s.linea if s else 0, self._registros, self._correctos, self._problemas, self._interrumpido,
            self._campos, self._primera, self.encabezado, self._codec, self._confirmada, self._bom,
            self._separador, (("quotechar", '"'), ("doublequote", "True"), ("escapechar", "None"),
                              ("skipinitialspace", "False"), ("strict", "True"), ("newline", "CR/LF/CRLF")),
            tuple(self._diagnosticos), self.politica)
