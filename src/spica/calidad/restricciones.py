"""Límites de interpretación de un ResultadoQA, sin autorización operacional.

Política cerrada en código: no lee configuración, documentos ni observaciones
adicionales. No evalúa de nuevo la condición ni modifica el resultado recibido.
Los bloqueos impiden usar ESTE diagnóstico como evidencia de otra operación;
no deciden si dicha operación puede autorizarse por un mecanismo independiente.
"""

from dataclasses import dataclass
from enum import Enum

from .modelos import EstadoResultadoQA as E, ResultadoQA

VERSION_RESTRICCIONES_QA = "1.0.0"


class TipoRestriccionQA(Enum):
    INFORMATIVA = "informativa"
    BLOQUEO_USO_DEL_RESULTADO = "bloqueo_uso_del_resultado"


@dataclass(frozen=True)
class RestriccionQA:
    codigo: str
    tipo: TipoRestriccionQA
    operaciones: tuple[str, ...]
    motivo: str


def _bloqueo(codigo, operaciones, motivo):
    return RestriccionQA(codigo, TipoRestriccionQA.BLOQUEO_USO_DEL_RESULTADO,
                         operaciones, motivo)


_COMUNES = (
    RestriccionQA("alcance_estructural", TipoRestriccionQA.INFORMATIVA, (),
                  "El estado solo describe la condición técnica o documental indicada."),
    _bloqueo("sin_validacion_cientifica", ("acreditar_aptitud_cientifica",),
             "Nivel 0 no demuestra plausibilidad, condiciones de medición ni calidad instrumental."),
    _bloqueo("sin_equivalencia_editorial", ("afirmar_equivalencia_editorial",),
             "Una comprobación estructural no demuestra correspondencia editorial entre archivos."),
)

_HORA = _bloqueo("hora_sin_transformacion",
    ("construir_instantes", "asignar_zona_horaria", "completar_hora_por_inferencia"),
    "Nivel 0 no acredita una conversión temporal, incluso si se aportó un formato o zona.")
_UBIGEO = _bloqueo("ubigeo_sin_interpretacion",
    ("normalizar_sufijo_ubigeo", "asignar_coordenadas", "inferir_identidad_territorial"),
    "Anchura y presencia literal no verifican códigos territoriales ni geocodificación.")
_PP = _bloqueo("pp_sin_conversion",
    ("convertir_mm_mm_h", "inferir_acumulacion_o_intensidad"),
    "Una representación numérica no acredita unidad, tipo de medición o ventana de precipitación.")
_NUMEROS = _bloqueo("numero_sin_metrologia",
    ("afirmar_plausibilidad_meteorologica", "acreditar_calidad_instrumental", "suponer_condiciones_medicion"),
    "La gramática numérica no proporciona evidencia meteorológica o metrológica.")
_PROCEDENCIA = _bloqueo("referencia_sin_verificacion",
    ("afirmar_verificacion_fisica", "afirmar_autenticidad_documental", "autorizar_redistribucion"),
    "Presencia o coincidencia de referencias no comprueba originales, autenticidad ni permisos.")
_ESPACIO = _bloqueo("identidad_ubicacion_no_verificadas",
    ("acreditar_estacion_fisica", "validar_ubicacion_espacial"),
    "Nombre, mapping o metadatos declarados no verifican instalación, CRS ni ubicación física.")


def restricciones_resultado(resultado: ResultadoQA) -> tuple[RestriccionQA, ...]:
    """Anotaciones conservadoras, deterministas y separadas del esquema QA 1.0.0.

    Deben acompañarse de VERSION_RESTRICCIONES_QA al exportarse. No son campos
    de ResultadoQA y asdict(resultado) no las incluye. No autentica objetos
    construidos por el llamador ni sustituye una barrera de seguridad.
    """
    if not isinstance(resultado, ResultadoQA):
        raise TypeError("Se requiere ResultadoQA")
    restricciones = list(_COMUNES)
    campos = {k for k, _ in resultado.valores_originales}
    rid = resultado.regla.identificador
    if "HORA" in campos:
        restricciones.append(_HORA)
    if "UBIGEO" in campos:
        restricciones.append(_UBIGEO)
    if "PP" in campos:
        restricciones.append(_PP)
    if campos.intersection(("TEMP", "HR")):
        restricciones.append(_NUMEROS)
    if rid.startswith("L0-PROV-"):
        restricciones.append(_PROCEDENCIA)
    if rid.startswith("L0-ID-"):
        restricciones.append(_ESPACIO)
    if resultado.estado is E.NO_EVALUADO:
        restricciones.append(_bloqueo("condicion_no_evaluada", ("dar_por_evaluada_la_condicion",),
                                     resultado.diagnostico))
    elif resultado.estado is E.EVALUACION_INCOMPLETA:
        restricciones.append(_bloqueo("condicion_incompleta", ("dar_por_concluida_la_condicion",),
                                     resultado.diagnostico))
    return tuple(restricciones)
