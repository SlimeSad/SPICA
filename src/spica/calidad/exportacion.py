"""Exportación experimental QA 0.1.0 en memoria; no autoriza usos ni lee archivos.

La identidad depende de un espacio y una ejecución coordinados por el llamador.
El JSON conserva declaraciones; no autentica contexto, referencias u originales.
"""

from dataclasses import dataclass, fields
from datetime import datetime
import hashlib
import json
import re

from ..adquisicion.catalogo import EvidenciaDocumental
from ..adquisicion.catalogo.modelos import (
    EstadoVerificacion, MecanismoAdquisicion, ProcedenciaCatalogo,
)
from ..adquisicion.consultas_locales import ProcedenciaLocal
from ..adquisicion.nucleo import Fuente
from ..adquisicion.verificacion import PoliticaLecturaCSV
from ..perfilado import LimitesPerfil
from .modelos import (
    CategoriaQA, ConfiguracionQA, DatoDocumentadoQA, EstadoResultadoQA,
    FormatoDocumentadoQA, FormatoQA, IdentidadEstacionQA, ProcedenciaQA,
    ReferenciaDocumentalQA, RegistroQA, ReglaQA, ResultadoQA, VERSION_CONTRATO_QA,
)
from .restricciones import (
    RestriccionQA, TipoRestriccionQA, VERSION_RESTRICCIONES_QA, restricciones_resultado,
)

VERSION_EXPORTACION_QA = "0.1.0"
_VERSION = re.compile(r"(0|[1-9][0-9]{0,3})(\.(0|[1-9][0-9]{0,3})){2}")
_IDENTIDAD = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}")


def _texto(valor, maximo=4096):
    if type(valor) is not str or not valor.strip() or len(valor) > maximo:
        raise ValueError("Texto de exportación requerido y acotado")


@dataclass(frozen=True)
class ContextoExportacionQA:
    """Identidades y metadatos DECLARADOS, no identidades institucionales verificadas.

    Una ejecución independiente necesita otro evaluacion_id dentro del espacio.
    entrada_id debe identificar la entrada dentro de esa ejecución/escenario.
    None en metadatos significa inventario desconocido; () inventario declarado vacío.
    """

    espacio_id: str
    evaluacion_id: str
    entrada_id: str
    escenario_id: str | None = None
    configuracion: ConfiguracionQA | None = None
    metadatos_requeridos: tuple[str, ...] | None = None
    metadatos_ausentes: tuple[str, ...] | None = None
    incertidumbres: tuple[str, ...] = ()

    def __post_init__(self):
        for v in (self.espacio_id, self.evaluacion_id, self.entrada_id):
            if type(v) is not str or not _IDENTIDAD.fullmatch(v):
                raise ValueError("Identidad contextual ASCII explícita y acotada requerida")
        if self.escenario_id is not None and (type(self.escenario_id) is not str
                or not _IDENTIDAD.fullmatch(self.escenario_id)):
            raise ValueError("Escenario no admitido")
        if self.configuracion is not None and type(self.configuracion) is not ConfiguracionQA:
            raise TypeError("Configuración QA tipada o desconocida requerida")
        for valores in (self.metadatos_requeridos, self.metadatos_ausentes, self.incertidumbres):
            if valores is not None:
                if type(valores) is not tuple or len(valores) > 32:
                    raise ValueError("Metadatos y motivos requieren tuplas acotadas")
                for v in valores:
                    _texto(v, 512)
                if len(set(valores)) != len(valores):
                    raise ValueError("Declaraciones repetidas")
        if self.incertidumbres is None:
            raise ValueError("Incertidumbres declaradas requieren una tupla")
        if self.metadatos_ausentes is not None and (self.metadatos_requeridos is None
                or not set(self.metadatos_ausentes).issubset(self.metadatos_requeridos)):
            raise ValueError("Ausencias declaradas requieren su inventario de requisitos")


@dataclass(frozen=True)
class LimitesExportacionQA:
    max_bytes: int = 1_048_576
    max_caracteres_texto: int = 65_536
    max_nodos: int = 20_000
    max_profundidad: int = 20

    def __post_init__(self):
        for nombre, tope in (("max_bytes", 4_194_304), ("max_caracteres_texto", 65_536),
                             ("max_nodos", 50_000), ("max_profundidad", 24)):
            v = getattr(self, nombre)
            if type(v) is not int or not 0 < v <= tope:
                raise ValueError("Límite de exportación no admitido")


_CLASES = frozenset((ContextoExportacionQA, ResultadoQA, ReglaQA, RegistroQA,
    ProcedenciaQA, ReferenciaDocumentalQA, ConfiguracionQA, FormatoDocumentadoQA,
    DatoDocumentadoQA, IdentidadEstacionQA, RestriccionQA, ProcedenciaLocal, Fuente,
    EvidenciaDocumental, ProcedenciaCatalogo, LimitesPerfil, PoliticaLecturaCSV))
_ENUMS = frozenset((CategoriaQA, EstadoResultadoQA, FormatoQA, TipoRestriccionQA,
                    EstadoVerificacion, MecanismoAdquisicion))


class _Conversion:
    """Recorrido acotado sin asdict/deepcopy ni serializadores de objetos externos."""

    def __init__(self, limites):
        self.limites, self.nodos, self.bytes_texto = limites, 0, 0

    def convertir(self, v, profundidad=0):
        self.nodos += 1
        if self.nodos > self.limites.max_nodos or profundidad > self.limites.max_profundidad:
            raise ValueError("Estructura de exportación superior al presupuesto")
        tipo = type(v)
        if v is None or tipo is bool:
            return v
        if tipo is int:
            if not -(2**53 - 1) <= v <= 2**53 - 1:
                raise ValueError("Entero fuera del intervalo JSON interoperable")
            return v
        if tipo is str:
            if len(v) > self.limites.max_caracteres_texto:
                raise ValueError("Texto de exportación superior al presupuesto")
            try:
                self.bytes_texto += len(v.encode("utf-8", errors="strict"))
            except UnicodeError:
                raise ValueError("Texto no representable como UTF-8 estricto") from None
            if self.bytes_texto > self.limites.max_bytes:
                raise ValueError("Contenido de exportación superior al presupuesto")
            return v
        if tipo in _ENUMS:
            return self.convertir(v.value, profundidad + 1)
        if tipo is datetime:
            if v.utcoffset() is None:
                raise ValueError("Fecha documental sin referencia temporal")
            return self.convertir(v.isoformat(), profundidad + 1)
        if tipo in _CLASES:
            datos = {f.name: self.convertir(getattr(v, f.name), profundidad + 1) for f in fields(v)}
            try:
                # Reutilizar validaciones nativas, sin modificar el objeto recibido.
                tipo(**{f.name: getattr(v, f.name) for f in fields(v) if f.init})
            except (TypeError, ValueError, AttributeError):
                raise ValueError("Contrato nativo incompatible con la exportación") from None
            return datos
        if tipo in (tuple, list):
            if len(v) > self.limites.max_nodos:
                raise ValueError("Colección superior al presupuesto")
            return [self.convertir(x, profundidad + 1) for x in v]
        if tipo is dict:
            if len(v) > self.limites.max_nodos or any(type(k) is not str for k in v):
                raise ValueError("Objeto JSON no admitido")
            return {self.convertir(k, profundidad + 1): self.convertir(x, profundidad + 1)
                    for k, x in v.items()}
        # Tampoco se convierten float/Decimal finitos: observaciones siguen textuales.
        raise TypeError("Tipo no admitido en la exportación QA")


def _json(datos, limites):
    encoder = json.JSONEncoder(ensure_ascii=False, allow_nan=False, sort_keys=True,
                               separators=(",", ":"))
    partes, usados = [], 0
    for parte in encoder.iterencode(datos):
        usados += len(parte.encode("utf-8", errors="strict"))
        if usados > limites.max_bytes:
            raise ValueError("JSON de exportación superior al presupuesto")
        partes.append(parte)
    return "".join(partes)


def _validar_resultado(r):
    if (type(r) is not ResultadoQA or type(r.regla) is not ReglaQA
            or type(r.registro) is not RegistroQA or type(r.procedencia) is not ProcedenciaQA
            or type(r.estado) is not EstadoResultadoQA or type(r.regla.categoria) is not CategoriaQA):
        raise TypeError("Resultado QA nativo y estado tipado requeridos")
    if r.version_contrato != VERSION_CONTRATO_QA:
        raise ValueError("Versión de contrato QA no admitida")
    entrada = r.registro
    if any(v is not None and type(v) is not str for v in (entrada.id_original, entrada.estacion_literal)):
        raise TypeError("Identificadores originales textuales o desconocidos requeridos")
    if entrada.procedencia_original is not None and type(entrada.procedencia_original) is not ProcedenciaLocal:
        raise TypeError("Procedencia original no admitida")
    if entrada.valores_csv_originales is not None and (type(entrada.valores_csv_originales) is not tuple
            or len(entrada.valores_csv_originales) > 4096
            or any(type(v) is not str for v in entrada.valores_csv_originales)):
        raise TypeError("Tupla original textual y acotada requerida")
    for texto in (r.regla.identificador, r.regla.descripcion, r.diagnostico):
        _texto(texto)
    if type(r.regla.version) is not str or not _VERSION.fullmatch(r.regla.version):
        raise ValueError("Versión de regla no admitida")
    for pares, opcional in ((r.valores_originales, True), (r.parametros, False)):
        if type(pares) is not tuple or len(pares) > 128:
            raise ValueError("Pares de resultado acotados requeridos")
        for par in pares:
            if type(par) is not tuple or len(par) != 2:
                raise ValueError("Par de resultado no admitido")
            _texto(par[0], 128)
            if type(par[1]) is not str and not (opcional and par[1] is None):
                raise TypeError("Valor textual original o ausencia explícita requeridos")
    if len({k for k, _ in r.valores_originales}) != len(r.valores_originales):
        raise ValueError("Objetivos repetidos en el resultado")
    if type(r.evidencia) is not tuple or len(r.evidencia) > 128 or any(
            type(e) is not ReferenciaDocumentalQA for e in r.evidencia):
        raise TypeError("Evidencia QA tipada y acotada requerida")
    versiones = [v for k, v in r.parametros if k == "evaluador_nivel0"]
    if len(versiones) > 1 or (versiones and not _VERSION.fullmatch(versiones[0])):
        raise ValueError("Versión del evaluador ambigua o no admitida")
    return versiones[0] if versiones else None


def exportar_resultado_json(resultado: ResultadoQA, contexto: ContextoExportacionQA,
                            *, limites: LimitesExportacionQA | None = None) -> str:
    """JSON estricto y determinista, sin E/S, reloj, IDs aleatorios o autorización.

    No se devuelve un modelo QA alternativo ni se reconstruyen objetos ejecutables
    desde JSON. Reutilizar identidades con otro contenido es responsabilidad del
    llamador; huella_contenido permite detectar esa contradicción al comparar.
    """
    if type(contexto) is not ContextoExportacionQA:
        raise TypeError("Contexto de exportación explícito requerido")
    contexto.__post_init__()
    limites = limites if limites is not None else LimitesExportacionQA()
    if type(limites) is not LimitesExportacionQA:
        raise TypeError("Límites de exportación tipados requeridos")
    limites.__post_init__()
    version_evaluador = _validar_resultado(resultado)
    conversion = _Conversion(limites)
    nativo = conversion.convertir(resultado)
    contexto_json = conversion.convertir(contexto)
    anotaciones = conversion.convertir(restricciones_resultado(resultado))
    entrada = resultado.registro
    identidad = dict(contexto=contexto_json, numero_registro=entrada.numero_registro,
        linea_inicial=entrada.linea_inicial, linea_final=entrada.linea_final,
        regla_id=resultado.regla.identificador, version_regla=resultado.regla.version,
        version_evaluador=version_evaluador, version_contrato_qa=resultado.version_contrato,
        version_restricciones=VERSION_RESTRICCIONES_QA,
        version_esquema=VERSION_EXPORTACION_QA,
        campos_objetivo=sorted(k for k, _ in resultado.valores_originales))
    resultado_id = "qa0-" + hashlib.sha256(_json(identidad, limites).encode("utf-8")).hexdigest()
    huella = hashlib.sha256(_json(nativo, limites).encode("utf-8")).hexdigest()
    paquete = dict(
        version_esquema=VERSION_EXPORTACION_QA,
        resultado_id=resultado_id,
        huella_contenido=huella,
        naturaleza_identidad="contextual_declarada_no_verificada",
        contexto=contexto_json,
        campos_objetivo=[k for k, _ in resultado.valores_originales],
        versiones=dict(contrato_qa=resultado.version_contrato, evaluador=version_evaluador,
                       restricciones=VERSION_RESTRICCIONES_QA),
        resultado=nativo,
        estado_evaluacion=resultado.estado_evaluacion.value,
        detalle_diagnostico=resultado.regla.descripcion,
        campos_objetivo_no_aportados=[k for k, v in resultado.valores_originales if v is None],
        restricciones=dict(
            informativas=[a for a in anotaciones if a["tipo"] == TipoRestriccionQA.INFORMATIVA.value],
            bloqueantes=[a for a in anotaciones if a["tipo"] == TipoRestriccionQA.BLOQUEO_USO_DEL_RESULTADO.value]),
        limitaciones=["contexto_y_procedencia_declarados_no_autenticados",
            "sin_verificacion_fisica_de_originales", "sin_equivalencia_editorial_acreditada",
            "sin_validacion_cientifica", "sin_autorizacion_operativa",
            "inventario_metadatos_declarado_no_exhaustivo"],
    )
    if contexto.configuracion is None:
        paquete["limitaciones"].append("configuracion_no_aportada_reproduccion_limitada")
    # Incluye claves añadidas y duplicaciones de contexto en el presupuesto total.
    return _json(_Conversion(limites).convertir(paquete), limites)
