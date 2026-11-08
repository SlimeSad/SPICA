"""Instantáneas documentales experimentales. Validan metadatos, nunca archivos."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import re
import sys
from typing import TYPE_CHECKING, TypeAlias

if TYPE_CHECKING:
    from ..calidad.modelos_cientificos import ReferenciaCientifica
    from ..calidad.aplicabilidad.modelos import EvidenciaDocumental
    from ..interoperabilidad.modelos import IdentidadRecurso, PeriodoTemporal, Respaldo
    from ..adquisicion.verificacion.docx.modelos import ReferenciaDOCX

VERSION_CONTRATO = "0.1.0"


def _es_contrato(valor: object, modulo: str, nombre: str) -> bool:
    # Identidad nominal sin importar módulos: ciertos __init__ heredados cargan
    # persistencia. El llamador aporta instancias existentes; no se cargan plugins.
    cargado = sys.modules.get("spica." + modulo)
    return cargado is not None and type(valor) is vars(cargado).get(nombre)


def _respaldo(valor: Respaldo | None) -> None:
    if valor is not None and not _es_contrato(valor, "interoperabilidad.modelos", "Respaldo"):
        raise TypeError("respaldo_existente_requerido")


def _verificado(valor: Respaldo | None) -> bool:
    return valor is not None and valor.estado.value == "verificado"


def _texto(valor: str, maximo: int = 4096) -> None:
    if type(valor) is not str or not valor.strip() or len(valor) > maximo or "\x00" in valor:
        raise ValueError("texto_documental_requerido_y_acotado")


def _id(valor: str) -> None:
    _texto(valor, 128)
    if any(ord(c) < 32 for c in valor):
        raise ValueError("identificador_con_controles")


def _sha(valor: str) -> None:
    if type(valor) is not str or not re.fullmatch(r"[0-9a-f]{64}", valor):
        raise ValueError("sha256_documental_requerido")


def _tupla(valores: tuple, tipo: type, maximo: int = 64) -> None:
    if type(valores) is not tuple or len(valores) > maximo or any(type(v) is not tipo for v in valores):
        raise TypeError("tupla_documental_tipificada_y_acotada")


class TipoDocumento(Enum):
    XLSX = "xlsx"
    DOCX = "docx"
    OTRO = "otro_con_seccion_aportada"


class PresenciaInformacion(Enum):
    CON_VALOR = "con_valor"
    AUSENTE = "ausente_en_el_ambito_inspeccionado"
    NULO_DECLARADO = "nulo_expresamente_declarado"


class FormaDeclaracion(Enum):
    LITERAL = "literal"
    PARAFRASIS_CONTROLADA = "parafrasis_controlada"


class TipoRelacion(Enum):
    COINCIDENCIA = "coincidencia_declarada"
    COMPLEMENTARIEDAD = "complementariedad_declarada"
    CONTRADICCION = "contradiccion_declarada"
    DIFERENCIA_AMBITO = "diferencia_de_ambito"
    CORRESPONDENCIA_NO_DEMOSTRADA = "correspondencia_no_demostrada"


class RestriccionUso(Enum):
    IDENTIDAD_INSTITUCIONAL_NO_COMPROBADA = "identidad_institucional_no_comprobada"
    EDICION_NO_COMPROBADA = "edicion_no_comprobada"
    UNIDAD_AMBIGUA = "unidad_ambigua"
    CONVENCION_TEMPORAL_DESCONOCIDA = "convencion_temporal_desconocida"
    IDENTIDAD_ESPACIAL_DESCONOCIDA = "identidad_espacial_desconocida"
    DERECHO_NO_COMPROBADO = "derecho_no_comprobado"
    PROCESAMIENTO_NO_VALIDADO = "procesamiento_cientifico_no_validado"


class AspectoUso(Enum):
    APLICABILIDAD_PRODUCTO = "aplicabilidad_al_producto"
    CORROBORACION = "corroboracion_independiente"
    CONVENCION_TEMPORAL = "convencion_temporal"
    IDENTIDAD_ESPACIAL = "identidad_espacial"
    REFERENCIA_ESPACIAL = "referencia_espacial"
    SIGNIFICADO_VARIABLE = "significado_variable"
    UNIDAD = "unidad_aplicable"
    VALIDACION_CIENTIFICA = "validacion_cientifica"
    DERECHOS = "derechos_para_el_uso"


@dataclass(frozen=True)
class FuenteDocumental:
    referencia: ReferenciaCientifica
    tipo: TipoDocumento
    producto: IdentidadRecurso | None = None
    version_producto: str | None = None
    integridad: Respaldo | None = None
    inspeccion: Respaldo | None = None
    autenticidad: Respaldo | None = None
    correspondencia_editorial: Respaldo | None = None

    def __post_init__(self):
        if not _es_contrato(self.referencia, "calidad.modelos_cientificos", "ReferenciaCientifica") or type(self.tipo) is not TipoDocumento:
            raise TypeError("fuente_documental_tipificada_requerida")
        _id(self.referencia.identificador)
        _sha(self.referencia.sha256_referencia)
        if self.producto is not None and not _es_contrato(self.producto, "interoperabilidad.modelos", "IdentidadRecurso"):
            raise TypeError("identidad_recurso_existente_requerida")
        if self.version_producto is not None:
            _texto(self.version_producto, 256)
            if self.producto is None:
                raise ValueError("version_producto_sin_producto")
        for respaldo in (self.integridad, self.inspeccion, self.autenticidad, self.correspondencia_editorial):
            _respaldo(respaldo)
        if self.producto is None and self.correspondencia_editorial is not None and self.correspondencia_editorial.estado.value != "desconocido":
            raise ValueError("correspondencia_sin_producto")
        if _verificado(self.correspondencia_editorial) and (
                self.referencia.version_documento is None or self.version_producto is None):
            raise ValueError("correspondencia_verificada_con_ediciones_desconocidas")

    @property
    def identificador(self) -> str:
        return self.referencia.identificador

    @property
    def sha256(self) -> str:
        return self.referencia.sha256_referencia


@dataclass(frozen=True)
class ReferenciaCelda:
    archivo_id: str
    sha256: str
    hoja: str
    rango: str

    def __post_init__(self):
        _id(self.archivo_id)
        _sha(self.sha256)
        _texto(self.hoja, 128)
        _texto(self.rango, 32)
        extremos = self.rango.split(":")
        if len(extremos) not in (1, 2):
            raise ValueError("rango_celdas_no_admitido")
        indices = []
        for extremo in extremos:
            m = re.fullmatch(r"([A-Z]{1,3})([1-9][0-9]{0,6})", extremo)
            if m is None:
                raise ValueError("referencia_celda_incompleta")
            col = 0
            for c in m[1]:
                col = col * 26 + ord(c) - ord("A") + 1
            fila = int(m[2])
            if col > 16384 or fila > 1048576:
                raise ValueError("referencia_celda_fuera_del_perfil")
            indices.append((col, fila))
        if len(indices) == 2 and any(a > b for a, b in zip(*indices)):
            raise ValueError("rango_celdas_invertido")


@dataclass(frozen=True)
class ReferenciaSeccion:
    archivo_id: str
    sha256: str
    seccion: str

    def __post_init__(self):
        _id(self.archivo_id)
        _sha(self.sha256)
        _texto(self.seccion, 1024)


LocalizadorDocumental: TypeAlias = "ReferenciaCelda | ReferenciaDOCX | ReferenciaSeccion"
_Q = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
_BASE = "/" + _Q + "document[1]/" + _Q + "body[1]/"
_N = r"([1-9][0-9]{0,4})"


def _validar_docx(ref: ReferenciaDOCX) -> None:
    # Perfil mínimo: párrafos directos o en tablas no anidadas del cuerpo.
    _id(ref.archivo_id)
    _sha(ref.sha256)
    _texto(ref.ruta_xml)
    if ref.parte != "word/document.xml" or type(ref.parrafo) is not int or not 0 < ref.parrafo <= 20000:
        raise ValueError("referencia_docx_incompleta_o_fuera_del_perfil")
    prefijo = re.escape(_BASE)
    directo = re.fullmatch(prefijo + re.escape(_Q) + r"p\[" + _N + r"\]", ref.ruta_xml)
    if directo:
        if any(v is not None for v in (ref.tabla, ref.fila, ref.columna)):
            raise ValueError("referencia_docx_contexto_inconsistente")
        return
    patron = prefijo + "/".join(re.escape(_Q) + tag + r"\[" + _N + r"\]" for tag in ("tbl", "tr", "tc", "p"))
    m = re.fullmatch(patron, ref.ruta_xml)
    if m is None or any(type(v) is not int for v in (ref.tabla, ref.fila, ref.columna)) or (
            ref.tabla, ref.fila, ref.columna) != tuple(int(v) for v in m.groups()[:3]):
        raise ValueError("referencia_docx_contexto_inconsistente")


def localizar(ref: LocalizadorDocumental) -> str:
    """Representación determinista; no resuelve ni abre el localizador."""
    if type(ref) is ReferenciaCelda:
        return "xlsx:" + ref.hoja + "!" + ref.rango
    if _es_contrato(ref, "adquisicion.verificacion.docx.modelos", "ReferenciaDOCX"):
        _validar_docx(ref)
        return ref.parte + "#" + ref.ruta_xml
    if type(ref) is ReferenciaSeccion:
        return "seccion:" + ref.seccion
    raise TypeError("referencia_estructural_tipificada_requerida")


@dataclass(frozen=True)
class ConstatacionAspecto:
    aspecto: AspectoUso
    descripcion: str
    respaldo: Respaldo | None = None

    def __post_init__(self):
        if type(self.aspecto) is not AspectoUso:
            raise TypeError("aspecto_y_respaldo_tipificados_requeridos")
        _respaldo(self.respaldo)
        _texto(self.descripcion)


@dataclass(frozen=True)
class AfirmacionDocumental:
    identificador: str
    fuente: FuenteDocumental
    referencia: LocalizadorDocumental
    evidencia: EvidenciaDocumental
    concepto: str
    ambito: str
    presencia: PresenciaInformacion
    contenido: str | None = field(repr=False)
    forma: FormaDeclaracion = FormaDeclaracion.LITERAL
    unidad_declarada: str | None = None
    vigencia: PeriodoTemporal | None = None
    restricciones: tuple[RestriccionUso, ...] = ()
    constataciones: tuple[ConstatacionAspecto, ...] = ()

    def __post_init__(self):
        _id(self.identificador)
        if type(self.fuente) is not FuenteDocumental or not _es_contrato(self.evidencia, "calidad.aplicabilidad.modelos", "EvidenciaDocumental"):
            raise TypeError("fuente_y_evidencia_existente_requeridas")
        localizacion = localizar(self.referencia)
        compatible = (self.fuente.tipo is TipoDocumento.XLSX and type(self.referencia) is ReferenciaCelda
                      or self.fuente.tipo is TipoDocumento.OTRO and type(self.referencia) is ReferenciaSeccion
                      or self.fuente.tipo is TipoDocumento.DOCX and _es_contrato(
                          self.referencia, "adquisicion.verificacion.docx.modelos", "ReferenciaDOCX"))
        if not compatible:
            raise TypeError("tipo_documento_y_localizador_incompatibles")
        if (self.referencia.archivo_id, self.referencia.sha256) != (self.fuente.identificador, self.fuente.sha256):
            raise ValueError("referencia_de_otro_documento_o_hash")
        if self.evidencia.referencia != self.fuente.referencia or self.evidencia.localizacion != localizacion:
            raise ValueError("evidencia_y_referencia_estructural_inconsistentes")
        for t in (self.concepto, self.ambito):
            _texto(t)
        if type(self.presencia) is not PresenciaInformacion or type(self.forma) is not FormaDeclaracion:
            raise TypeError("presencia_y_forma_tipificadas_requeridas")
        if self.presencia is PresenciaInformacion.AUSENTE:
            if self.contenido is not None or self.evidencia.nivel.value != "desconocida" or not self.evidencia.pendientes:
                raise ValueError("ausencia_requiere_alcance_pendiente_y_estado_desconocido")
        else:
            _texto(self.contenido)
            if self.evidencia.nivel.value == "desconocida":
                raise ValueError("contenido_con_estado_desconocido")
            if self.presencia is PresenciaInformacion.NULO_DECLARADO and self.evidencia.nivel.value not in ("declarada", "verificada"):
                raise ValueError("nulo_institucional_no_puede_inferirse")
        if self.unidad_declarada is not None:
            _texto(self.unidad_declarada, 256)
        if self.vigencia is not None and not _es_contrato(self.vigencia, "interoperabilidad.modelos", "PeriodoTemporal"):
            raise TypeError("periodo_temporal_existente_requerido")
        _tupla(self.restricciones, RestriccionUso)
        _tupla(self.constataciones, ConstatacionAspecto, 16)
        if len(set(self.restricciones)) != len(self.restricciones) or len({c.aspecto for c in self.constataciones}) != len(self.constataciones):
            raise ValueError("restriccion_o_aspecto_repetido")
        for c in self.constataciones:
            if _verificado(c.respaldo):
                if c.aspecto is AspectoUso.UNIDAD and self.unidad_declarada is None:
                    raise ValueError("unidad_acreditada_sin_unidad")
                if c.aspecto is AspectoUso.APLICABILIDAD_PRODUCTO and self.fuente.producto is None:
                    raise ValueError("aplicabilidad_sin_producto")

    @property
    def valor(self) -> str | None:
        # El marcador de nulo se conserva en contenido, sin confundirlo con ausencia.
        return self.contenido if self.presencia is PresenciaInformacion.CON_VALOR else None


@dataclass(frozen=True)
class RelacionAfirmaciones:
    primera: str
    segunda: str
    tipo: TipoRelacion
    justificacion: str

    def __post_init__(self):
        _id(self.primera)
        _id(self.segunda)
        if self.primera == self.segunda or type(self.tipo) is not TipoRelacion:
            raise ValueError("relacion_documental_invalida")
        _texto(self.justificacion)


@dataclass(frozen=True)
class ExpedienteMetadatos:
    fuentes: tuple[FuenteDocumental, ...]
    afirmaciones: tuple[AfirmacionDocumental, ...]
    relaciones: tuple[RelacionAfirmaciones, ...] = ()

    def __post_init__(self):
        _tupla(self.fuentes, FuenteDocumental)
        _tupla(self.afirmaciones, AfirmacionDocumental, 256)
        _tupla(self.relaciones, RelacionAfirmaciones, 512)
        fs = {f.identificador: f for f in self.fuentes}
        aa = {a.identificador: a for a in self.afirmaciones}
        if not fs or len(fs) != len(self.fuentes) or len(aa) != len(self.afirmaciones):
            raise ValueError("identidades_documentales_vacias_o_repetidas")
        if any(fs.get(a.fuente.identificador) != a.fuente for a in self.afirmaciones):
            raise ValueError("afirmacion_con_fuente_ajena")
        if len({a.evidencia.naturaleza for a in self.afirmaciones}) > 1:
            raise ValueError("no_mezclar_fixture_y_evidencia_documental")
        pares = set()
        for r in self.relaciones:
            par = tuple(sorted((r.primera, r.segunda)))
            if par in pares or not set(par) <= aa.keys():
                raise ValueError("relacion_duplicada_o_con_afirmacion_ajena")
            pares.add(par)
            a, b = aa[r.primera], aa[r.segunda]
            iguales = (a.concepto, a.ambito, a.presencia, a.contenido, a.unidad_declarada) == (
                b.concepto, b.ambito, b.presencia, b.contenido, b.unidad_declarada)
            if r.tipo is TipoRelacion.COINCIDENCIA and (not iguales or a.presencia is PresenciaInformacion.AUSENTE):
                raise ValueError("coincidencia_literal_no_demostrada_en_los_metadatos")
            if r.tipo is TipoRelacion.CONTRADICCION and (
                    iguales or (a.concepto, a.ambito) != (b.concepto, b.ambito)
                    or PresenciaInformacion.AUSENTE in (a.presencia, b.presencia)
                    or a.presencia is b.presencia is PresenciaInformacion.NULO_DECLARADO):
                raise ValueError("contradiccion_sin_afirmaciones_distintas_en_el_mismo_ambito")
            if r.tipo is TipoRelacion.DIFERENCIA_AMBITO and a.ambito == b.ambito:
                raise ValueError("diferencia_de_ambito_sin_ambitos_distintos")
