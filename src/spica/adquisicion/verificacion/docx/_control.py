"""Presupuestos y cancelación de una operación local; sin I/O externo."""

from io import BytesIO
import math

from .modelos import DiagnosticoDOCX, EstadoInspeccionDOCX as E


class _Fallo(Exception):
    def __init__(self, codigo, estado=E.DOCUMENTO_RECHAZADO):
        self.codigo, self.estado = codigo, estado


def exigir(condicion, codigo):
    if not condicion:
        raise _Fallo(codigo)


class Control:
    def __init__(self, limites, cancelacion, reloj):
        self.limites, self.cancelacion, self.reloj = limites, cancelacion, reloj
        inicio = reloj()
        if type(inicio) not in (int, float) or not math.isfinite(inicio):
            raise ValueError("reloj_monotonico_finito_requerido")
        self.fin = inicio + limites.max_segundos
        self.identidad = None
        self.actual = self.pico = self.texto = 0
        self.xml = 0
        self.ctx = {"nodos_xml": 0, "descomprimidos": 0}
        self.omitidas, self.advertencias = [], []
        self.partes, self.relaciones = [], []
        self.incompleta = False
        self.verificados = self.lecturas0 = self.lecturas1 = self.lecturas2 = 0

    def paso(self):
        if self.cancelacion.is_set():
            raise _Fallo("cancelado", E.INSPECCION_INCOMPLETA)
        ahora = self.reloj()
        if not math.isfinite(ahora) or ahora > self.fin:
            raise _Fallo("plazo_excedido", E.INSPECCION_INCOMPLETA)

    def limite(self, condicion, codigo):
        self.paso()
        if not condicion:
            raise _Fallo(codigo, E.INSPECCION_INCOMPLETA)

    def reservar(self, cantidad):
        self.limite(self.actual + cantidad <= self.limites.max_bytes_auxiliares,
                    "limite_memoria_auxiliar_contable")
        self.actual += cantidad
        self.pico = max(self.pico, self.actual)

    def liberar(self, cantidad):
        self.actual -= cantidad

    def guardar_textos(self, *valores):
        self.reservar(sum(len(v.encode("utf-8")) for v in valores if v is not None))

    def literal(self, valor):
        self.limite(len(valor) <= self.limites.max_texto_fragmento, "limite_texto_fragmento")
        self.limite(self.texto + len(valor) <= self.limites.max_texto_total, "limite_texto_total")
        self.texto += len(valor)
        self.guardar_textos(valor)
        return valor

    def diagnostico(self, codigo, parte=None, *, omision=False, incompleta=False):
        d = DiagnosticoDOCX(codigo, parte)
        lista = self.omitidas if omision else self.advertencias
        if d not in lista:
            self.limite(len(self.omitidas) + len(self.advertencias) < self.limites.max_diagnosticos,
                        "limite_diagnosticos")
            self.guardar_textos(codigo, parte)
            lista.append(d)
        self.incompleta |= incompleta


class FuenteZIP(BytesIO):
    """Acota las lecturas de zipfile, también durante su constructor."""
    def __init__(self, datos, control, fase=0):
        super().__init__(datos)
        self.control, self.leidos, self.fase = control, 0, fase

    def read(self, cantidad=-1):
        c = self.control
        c.paso()
        if cantidad < 0:
            cantidad = len(self.getbuffer()) - self.tell()
        c.limite(cantidad <= max(65_557, c.limites.zip.max_central_zip,
                                c.limites.zip.tamano_bloque), "limite_lectura_zip")
        restante = c.limites.max_lecturas_zip - self.leidos
        datos = super().read(min(cantidad, max(0, restante) + 1))
        self.leidos += len(datos)
        setattr(c, "lecturas" + str(self.fase), self.leidos)
        c.limite(self.leidos <= c.limites.max_lecturas_zip, "limite_lecturas_zip")
        return datos

    def seek(self, *args):
        self.control.paso()
        return super().seek(*args)
