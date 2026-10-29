"""Selección progresiva sobre LectorCSV; sin HTTP, persistencia ni conversiones."""

from datetime import date
from functools import lru_cache
from threading import Event

from ..verificacion import EstadoEstructura, LectorCSV
from .modelos import (ConsultaLocal, ENCABEZADO_SENAMHI, InformeConsulta,
                      LimitesConsulta, ObservacionLocal, ProcedenciaLocal)


def _fecha_civil(texto):
    if len(texto) != 8 or not texto.isascii() or not texto.isdigit():
        return None
    return _fecha_aaaammdd(texto)


@lru_cache(maxsize=4096)
def _fecha_aaaammdd(texto):
    # Solo claves de ocho caracteres; no retener campos arbitrariamente largos.
    try:
        return date(int(texto[:4]), int(texto[4:6]), int(texto[6:]))
    except ValueError:
        return None


class _Filas:
    """Perfil explícito del CSV SENAMHI. No infiere encabezados ni otro esquema."""
    def __init__(self, ruta, politica, cancelacion, codificacion):
        self.lector = LectorCSV(ruta, politica=politica, cancelacion=cancelacion,
            codificacion=codificacion, delimitador=",", encabezado_declarado=True,
            campos_esperados=len(ENCABEZADO_SENAMHI))
        self.motivo = None
        self.encabezado_correcto = False

    def __enter__(self):
        self.lector.__enter__()
        return self

    def __iter__(self):
        for registro in self.lector:
            if registro.numero == 1:
                if registro.valores != ENCABEZADO_SENAMHI:
                    self.motivo = "encabezado_no_admitido"
                    return
                self.encabezado_correcto = True
            elif registro.estructura_correcta:
                yield registro

    def __exit__(self, *args):
        self.lector.__exit__(*args)

    @property
    def completa(self):
        r = self.lector.informe
        return self.encabezado_correcto and r.recorrido_completo and r.estado is EstadoEstructura.COMPATIBLE


class ConsultorLocalCSV:
    """Una operación por instancia, dentro de with. Consultar informe tras cerrar.

    Los resultados son provisionales hasta evaluar el informe final. El mismo
    archivo y filtros producen el mismo orden de filas y de variables.
    """
    def __init__(self, ruta, consulta: ConsultaLocal, procedencia: ProcedenciaLocal, *,
                 limites: LimitesConsulta | None = None, cancelacion=None, codificacion=None):
        if not isinstance(consulta, ConsultaLocal) or not isinstance(procedencia, ProcedenciaLocal):
            raise TypeError("Consulta y procedencia tipadas requeridas")
        self.limites = limites if limites is not None else LimitesConsulta()
        if not isinstance(self.limites, LimitesConsulta):
            raise TypeError("Se requiere LimitesConsulta")
        self.consulta, self.procedencia = consulta, procedencia
        self.cancelacion = cancelacion if cancelacion is not None else Event()
        self._filas = _Filas(ruta, self.limites.lectura, self.cancelacion, codificacion)
        self._usada = self._abierta = self._agotada = False
        self._resultados = self._coincidentes = self._invalidas = 0
        self._motivo = None
        self._iterador = None

    def __enter__(self):
        if self._usada:
            raise RuntimeError("Crear otra operación para repetir la consulta")
        self._usada = True
        self._filas.__enter__()
        self._abierta = True
        self._iterador = self._consultar()
        return self

    def _consultar(self):
        c = self.consulta
        estaciones = frozenset(c.estaciones)
        indices = tuple((v, ENCABEZADO_SENAMHI.index(v)) for v in c.variables)
        for registro in self._filas:
            valores = registro.valores
            fecha = _fecha_civil(valores[2])
            if fecha is None:
                self._invalidas += 1
                continue
            if valores[1] not in estaciones or not c.fecha_inicial <= fecha <= c.fecha_final:
                continue
            self._coincidentes += 1
            campos = tuple(zip(ENCABEZADO_SENAMHI, valores))
            for variable, indice in indices:
                if self.cancelacion.is_set():
                    self._motivo = "cancelado"
                    return
                if self._resultados >= self.limites.max_resultados:
                    self._motivo = "limite_resultados"
                    return
                self._resultados += 1
                yield ObservacionLocal(self.procedencia, registro.numero, registro.linea_inicial,
                    registro.linea_final, campos, variable, valores[indice], valores[indice] != "", fecha)
                # No se lee por adelantado para suponer que el límite coincide con EOF.
                if self._resultados >= self.limites.max_resultados:
                    self._motivo = "limite_resultados"
                    return
        self._agotada = True

    def __iter__(self):
        return self

    def __next__(self):
        if not self._abierta:
            raise RuntimeError("La consulta requiere un contexto abierto")
        return next(self._iterador)

    def cancelar(self):
        self.cancelacion.set()

    def __exit__(self, tipo, valor, traza):
        try:
            if tipo is not None:
                self._motivo = "consumidor_interrumpido"
            self._iterador.close()
        finally:
            self._filas.__exit__(tipo, valor, traza)
            self._abierta = False

    @property
    def informe(self):
        lectura = self._filas.lector.informe
        completa = (not self._abierta and self._agotada and self._filas.completa
                    and not self._invalidas and self._motivo is None)
        motivo = (self._motivo or self._filas.motivo or
                  ("fechas_civiles_invalidas" if self._invalidas else None) or
                  ("estructura_no_compatible" if lectura.recorrido_completo and not self._filas.completa else None)
                  or lectura.motivo_fin)
        if self.cancelacion.is_set() and not completa:
            motivo = "cancelado"
        return InformeConsulta(completa, motivo, self._resultados, self._coincidentes,
                               self._invalidas, lectura)
