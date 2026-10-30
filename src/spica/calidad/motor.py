"""Evaluación progresiva de entradas existentes, con cierre y alcance explícitos."""

from collections import Counter
from threading import Event

from ..adquisicion.consultas_locales import ConsultorLocalCSV, ENCABEZADO_SENAMHI, ObservacionLocal
from ..adquisicion.verificacion import EstadoEstructura, LectorCSV, RegistroCSV
from .modelos import (ConfiguracionQA, EstadoEvaluacionQA as EE, EstadoResultadoQA as ER,
                      InformeQA, LimitesQA, ProcedenciaQA, RegistroQA)
from .reglas import evaluar_registro, seleccionar_reglas


def adaptar_registro(entrada: RegistroCSV | ObservacionLocal) -> RegistroQA:
    """No interpreta números ni fechas. Conserva también filas CSV malformadas."""
    if isinstance(entrada, RegistroCSV):
        campos = tuple(zip(ENCABEZADO_SENAMHI, entrada.valores))
        valores = dict(campos)
        return RegistroQA(entrada.numero, valores.get("ID"), valores.get("ESTACION"),
            entrada.linea_inicial, entrada.linea_final, campos,
            entrada.estructura_correcta and len(entrada.valores) == len(ENCABEZADO_SENAMHI),
            valores_csv_originales=entrada.valores)
    if isinstance(entrada, ObservacionLocal):
        campos = entrada.campos_originales
        valores = dict(campos)
        return RegistroQA(entrada.numero_registro, valores.get("ID"), valores.get("ESTACION"),
            entrada.linea_inicial, entrada.linea_final, campos,
            tuple(k for k, _ in campos) == ENCABEZADO_SENAMHI, entrada.procedencia)
    raise TypeError("Entrada no admitida")


class EvaluadorNivel0:
    """Posee el contexto de lectura recibido. Una instancia, una ejecución con with.

    ConsultorLocalCSV debe seleccionar una sola variable: sus resultados ya
    conservan los 16 campos. No se deduplican ni evalúan dos veces filas repetidas.
    """
    def __init__(self, entrada: LectorCSV | ConsultorLocalCSV, procedencia: ProcedenciaQA, *,
                 configuracion=None, limites=None, cancelacion=None):
        if not isinstance(entrada, (LectorCSV, ConsultorLocalCSV)) or not isinstance(procedencia, ProcedenciaQA):
            raise TypeError("Entrada y procedencia tipadas requeridas")
        self.configuracion = configuracion if configuracion is not None else ConfiguracionQA()
        self.limites = limites if limites is not None else LimitesQA()
        if not isinstance(self.configuracion, ConfiguracionQA) or not isinstance(self.limites, LimitesQA):
            raise TypeError("Configuración y límites QA requeridos")
        if isinstance(entrada, ConsultorLocalCSV) and len(entrada.consulta.variables) != 1:
            raise ValueError("Seleccionar una variable para representar cada fila una sola vez")
        self.reglas = seleccionar_reglas(self.configuracion)
        self.entrada, self.procedencia = entrada, procedencia
        self.cancelacion = cancelacion if cancelacion is not None else Event()
        self._usada = self._abierta = self._agotada = self._fuente_completa = False
        self._motivo = None
        self._registros = self._finalizados = self._resultados = self._incompletos = 0
        self._conteos, self._ejecutadas = Counter(), set()
        self._iterador = None

    def __enter__(self):
        if self._usada:
            raise RuntimeError("Crear otra evaluación para repetir")
        self._usada = True
        if self.cancelacion.is_set():
            self.entrada.cancelar()
        self.entrada.__enter__()
        self._abierta = True
        self._iterador = self._evaluar()
        return self

    def _evaluar(self):
        anterior = 0
        for entrada in self.entrada:
            if isinstance(entrada, RegistroCSV) and entrada.numero == 1:
                if entrada.valores != ENCABEZADO_SENAMHI:
                    self._motivo = "encabezado_no_admitido"
                    return
                continue
            if self.cancelacion.is_set():
                self._motivo = "cancelado"
                return
            if self._registros >= self.limites.max_registros:
                self._motivo = "limite_registros_qa"
                return
            registro = adaptar_registro(entrada)
            if registro.numero_registro <= anterior:
                self._motivo = "registro_repetido_o_desordenado"
                return
            anterior = registro.numero_registro
            textos = (registro.valores_csv_originales if registro.valores_csv_originales is not None else
                      tuple(v for _, v in registro.campos_originales))
            if (any(len(v) > self.limites.max_caracteres_celda for v in textos)
                    or sum(len(v) for v in textos) > self.limites.max_caracteres_registro):
                self._motivo = "limite_texto_registro_qa"
                return
            self._registros += 1
            for resultado in evaluar_registro(registro, self.procedencia, configuracion=self.configuracion):
                if self.cancelacion.is_set():
                    self._motivo = "cancelado"
                    return
                if self._resultados >= self.limites.max_resultados:
                    self._motivo = "limite_resultados_qa"
                    return
                self._resultados += 1
                self._ejecutadas.add(resultado.regla.identificador)
                self._conteos[resultado.regla.categoria, resultado.estado] += 1
                self._incompletos += resultado.estado is ER.EVALUACION_INCOMPLETA
                yield resultado
                if self._resultados >= self.limites.max_resultados:
                    self._motivo = "limite_resultados_qa"
                    return  # No presumir EOF por coincidir con el límite.
            self._finalizados += 1
        self._agotada = True

    def __iter__(self):
        return self

    def __next__(self):
        if not self._abierta:
            raise RuntimeError("La evaluación requiere contexto abierto")
        return next(self._iterador)

    def cancelar(self):
        self.cancelacion.set()
        self.entrada.cancelar()

    def __exit__(self, tipo, valor, traza):
        try:
            if tipo is not None:
                self._motivo = "consumidor_interrumpido"
            self._iterador.close()
        finally:
            self.entrada.__exit__(tipo, valor, traza)
            self._abierta = False
            informe = self.entrada.informe
            self._fuente_completa = (informe.completa if isinstance(self.entrada, ConsultorLocalCSV) else
                informe.recorrido_completo and informe.estado is EstadoEstructura.COMPATIBLE)
            if self._motivo is None:
                self._motivo = informe.motivo_fin

    @property
    def informe(self):
        recorrido = self._agotada and self._fuente_completa and not self._abierta
        completa = (recorrido and not self._incompletos and self._finalizados == self._registros
                    and self._motivo == "eof")
        estado = EE.COMPLETA if completa and self._resultados else EE.NO_EVALUADA if completa else EE.INCOMPLETA
        motivo = self._motivo or "evaluacion_no_finalizada"
        if self._incompletos and recorrido:
            motivo = "reglas_con_evaluacion_incompleta"
        if self.cancelacion.is_set() and not completa:
            motivo = "cancelado"
        return InformeQA(estado, recorrido, motivo, self._registros, self._finalizados, self._resultados,
            self._incompletos,
            tuple((categoria, estado, n) for (categoria, estado), n in sorted(self._conteos.items(),
                  key=lambda item: (item[0][0].value, item[0][1].value))),
            tuple(r for r in self.reglas if r.identificador in self._ejecutadas),
            self.procedencia, self.configuracion, self.limites)
