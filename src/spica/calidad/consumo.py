"""Consumidor experimental offline de JSON QA 0.1.0; confianza contractual limitada.

Solo construye contratos de datos conocidos, nunca clases elegidas por el JSON.
No evalúa reglas ni autoriza usos. Un lote se acepta atómicamente en memoria.
"""

from dataclasses import dataclass, field, fields
from datetime import datetime
from enum import Enum
import json
import re

from ..adquisicion._json_acotado import _Incompleto, _Invalido, leer_json
from ..adquisicion.catalogo import EvidenciaDocumental
from ..adquisicion.catalogo.modelos import EstadoVerificacion, MecanismoAdquisicion, ProcedenciaCatalogo
from ..adquisicion.consultas_locales import ProcedenciaLocal
from ..adquisicion.nucleo import Fuente
from ..adquisicion.verificacion import PoliticaLecturaCSV
from ..perfilado import LimitesPerfil
from .modelos import (CategoriaQA, ConfiguracionQA, DatoDocumentadoQA, EstadoResultadoQA,
    FormatoDocumentadoQA, FormatoQA, IdentidadEstacionQA, ProcedenciaQA,
    ReferenciaDocumentalQA, RegistroQA, ReglaQA, ResultadoQA)
from .exportacion import ContextoExportacionQA, LimitesExportacionQA, exportar_resultado_json

VERSION_CONSUMO_QA = "0.1.0"
# El contraste de una representación propia tiene un presupuesto distinto del
# recorrido léxico de entrada: ambas profundidades cuentan unidades diferentes.
_LIMITES_CONTRASTE = LimitesExportacionQA(max_bytes=4_194_304, max_nodos=50_000,
                                         max_profundidad=24)


class EstadoConsumoQA(Enum):
    CONTRATO_VALIDO_EN_ALCANCE = "contrato_valido_en_alcance"
    CONTRATO_RECHAZADO = "contrato_rechazado"
    VALIDACION_INCOMPLETA = "validacion_incompleta"


@dataclass(frozen=True)
class LimitesConsumoQA:
    max_bytes_documento: int = 1_048_576
    max_bytes_lote: int = 4_194_304
    max_resultados: int = 256
    profundidad: int = 20
    unidades_documento: int = 20_000
    unidades_lote: int = 200_000
    caracteres_cadena: int = 65_536
    elementos_lista: int = 4096
    propiedades_objeto: int = 64
    max_objetos_documento: int = 2048
    max_restricciones_documento: int = 32
    max_restricciones_lote: int = 4096

    def __post_init__(self):
        topes = (4_194_304, 16_777_216, 1024, 24, 50_000, 1_000_000,
                 65_536, 4096, 128, 8192, 128, 16_384)
        for f, tope in zip(fields(self), topes, strict=True):
            v = getattr(self, f.name)
            if type(v) is not int or not 0 < v <= tope:
                raise ValueError("Límite de consumo no admitido")


@dataclass(frozen=True)
class ProblemaConsumoQA:
    codigo: str
    indice_documento: int | None = None  # Base uno; no contiene valores recibidos.


_NO_REALIZADAS = ("autenticidad_institucional", "verificacion_fisica_originales",
    "reevaluacion_reglas_qa", "validacion_cientifica", "autorizacion_ejecucion",
    "unicidad_global", "exhaustividad_metadatos")
_CONFIANZA = ("procedencia_y_contexto_declarados", "hashes_no_son_firmas_de_origen",
    "coherencia_no_demuestra_ejecucion_real", "sin_permiso_cientifico_u_operativo",
    "identidad_global_depende_de_coordinacion_externa")
_ETAPAS = frozenset(("limites_entrada", "json_estricto", "esquema_tipos_y_versiones",
    "coherencia_interna", "restricciones_politica_1.0.0", "identidad_y_huella",
    "campos_derivados", "identidades_en_lote"))


@dataclass(frozen=True)
class InformeConsumoQA:
    estado: EstadoConsumoQA
    diagnosticos_recibidos: int
    diagnosticos_aceptados: int
    duplicados_exactos: int
    comprobaciones_realizadas: tuple[str, ...]
    comprobaciones_no_realizadas: tuple[str, ...]
    problemas: tuple[ProblemaConsumoQA, ...]
    documentos_aceptados: tuple[str, ...]  # JSON recibido, canonizado sin perder restricciones.
    restricciones_informativas: int
    restricciones_bloqueantes: int
    limitaciones_confianza: tuple[str, ...] = _CONFIANZA
    version_contrato: str = field(default=VERSION_CONSUMO_QA, init=False)
    version_exportacion: str = field(default="0.1.0", init=False)


class _Rechazo(Exception):
    pass


class _EstadoJSON(Enum):
    PARCIAL = "parcial"
    COMPLETO = "completo"


def _exigir(condicion, codigo):
    if not condicion:
        raise _Rechazo(codigo)


def _claves(d, nombres):
    _exigir(type(d) is dict, "objeto_requerido")
    _exigir(set(d) == set(nombres), "campos_ausentes_o_no_permitidos")


def _cadena(v):
    _exigir(type(v) is str, "tipo_textual_requerido")
    return v


def _entero(v):
    _exigir(type(v) is int and -(2**53 - 1) <= v <= 2**53 - 1, "entero_no_admitido")
    return v


def _booleano(v):
    _exigir(type(v) is bool, "booleano_requerido")
    return v


def _opcional(decodificar):
    return lambda v: None if v is None else decodificar(v)


def _lista(decodificar):
    def leer(v):
        _exigir(type(v) is list, "lista_requerida")
        return tuple(decodificar(x) for x in v)
    return leer


def _pares(decodificar):
    def leer(par):
        _exigir(type(par) is list and len(par) == 2, "par_no_admitido")
        return _cadena(par[0]), decodificar(par[1])
    return _lista(leer)


def _enum(clase):
    return lambda v: clase(_cadena(v))


def _fecha(v):
    fecha = datetime.fromisoformat(_cadena(v))
    _exigir(fecha.utcoffset() is not None, "fecha_documental_sin_zona")
    return fecha


def _modelo(clase, esquema):
    """Tabla cerrada por el programa, sin nombres de clases ni hooks del remitente."""
    def leer(d):
        _claves(d, esquema)
        return clase(**{k: decodificar(d[k]) for k, decodificar in esquema.items()})
    return leer


_fuente = _modelo(Fuente, dict(proveedor=_cadena, identificador=_cadena))
_local = _modelo(ProcedenciaLocal, dict(fuente=_fuente, recurso_id=_cadena,
    asset_id=_cadena, sha256_declarado=_opcional(_cadena)))
_referencia = _modelo(ReferenciaDocumentalQA, dict(referencia=_cadena, descripcion=_cadena,
    sha256_referencia=_opcional(_cadena), revision=_opcional(_entero)))
_procedencia_catalogo = _modelo(ProcedenciaCatalogo, dict(referencia=_cadena,
    revisada_utc=_fecha, metodo=_cadena, evidencia=_opcional(_cadena)))
_documento = _modelo(EvidenciaDocumental, dict(fuente=_fuente, recurso_id=_cadena,
    producto_id=_opcional(_cadena), referencia_publicacion=_opcional(_cadena),
    descubierta_utc=_opcional(_fecha), licencia_declarada=_opcional(_cadena),
    referencia_licencia=_opcional(_cadena), revision_documental=_opcional(_entero),
    revision_producto=_opcional(_entero), revision_fuente=_opcional(_entero),
    estado=_enum(EstadoVerificacion), capacidades_documentadas=_lista(_enum(MecanismoAdquisicion)),
    procedencia=_opcional(_procedencia_catalogo)))
_procedencia = _modelo(ProcedenciaQA, dict(fuente=_opcional(_fuente), recurso_id=_opcional(_cadena),
    adquisicion_id=_opcional(_cadena), asset_id=_opcional(_cadena),
    sha256_referencia=_opcional(_cadena), documento=_opcional(_documento)))
_registro = _modelo(RegistroQA, dict(numero_registro=_entero, id_original=_opcional(_cadena),
    estacion_literal=_opcional(_cadena), linea_inicial=_entero, linea_final=_entero,
    campos_originales=_pares(_cadena), estructura_correcta=_booleano,
    procedencia_original=_opcional(_local), valores_csv_originales=_opcional(_lista(_cadena))))
_regla = _modelo(ReglaQA, dict(identificador=_cadena, version=_cadena,
    categoria=_enum(CategoriaQA), descripcion=_cadena))
_formato = _modelo(FormatoDocumentadoQA, dict(campo=_cadena, formato=_enum(FormatoQA), evidencia=_referencia))
_dato = _modelo(DatoDocumentadoQA, dict(valor=_cadena, evidencia=_referencia))
_identidad = _modelo(IdentidadEstacionQA, dict(nombre_literal=_cadena,
    identificador_original=_cadena, evidencia=_referencia))
_lectura = _modelo(PoliticaLecturaCSV, {f.name: _entero for f in fields(PoliticaLecturaCSV)})
_perfil = _modelo(LimitesPerfil, {f.name: _lectura if f.name == "lectura" else
    _lista(_cadena) if f.name == "marcadores" else _entero for f in fields(LimitesPerfil)})
_configuracion = _modelo(ConfiguracionQA, dict(categorias=_lista(_enum(CategoriaQA)),
    reglas=_lista(_cadena), variables=_lista(_cadena), formatos=_lista(_formato),
    zona_documentada=_opcional(_dato), identidades=_lista(_identidad), politica_numerica=_perfil))
_contexto = _modelo(ContextoExportacionQA, dict(espacio_id=_cadena, evaluacion_id=_cadena,
    entrada_id=_cadena, escenario_id=_opcional(_cadena), configuracion=_opcional(_configuracion),
    metadatos_requeridos=_opcional(_lista(_cadena)), metadatos_ausentes=_opcional(_lista(_cadena)),
    incertidumbres=_lista(_cadena)))


def _resultado(d):
    esquema = dict(regla=_regla, registro=_registro, procedencia=_procedencia,
        valores_originales=_pares(_opcional(_cadena)), evidencia=_lista(_referencia),
        parametros=_pares(_cadena), estado=_enum(EstadoResultadoQA), diagnostico=_cadena,
        version_contrato=_cadena)
    _claves(d, esquema)
    _exigir(d["version_contrato"] == "1.0.0", "version_no_admitida")
    valores = {k: f(d[k]) for k, f in esquema.items() if k != "version_contrato"}
    return ResultadoQA(**valores)


_CAMPOS = ("version_esquema", "resultado_id", "huella_contenido", "naturaleza_identidad",
    "contexto", "campos_objetivo", "versiones", "resultado", "estado_evaluacion",
    "detalle_diagnostico", "campos_objetivo_no_aportados", "restricciones", "limitaciones")


def _canonico(d):
    return json.dumps(d, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":"))


def _comprobar_arbol(d, limites):
    pila, objetos = [d], 0
    while pila:
        v = pila.pop()
        if type(v) is dict:
            objetos += 1
            if objetos > limites.max_objetos_documento:
                raise _Incompleto("objetos_documento_excesivos")
            pila.extend(v.keys())
            pila.extend(v.values())
        elif type(v) is list:
            pila.extend(v)
        elif type(v) is str:
            v.encode("utf-8", errors="strict")  # También detecta surrogates escapados en JSON.
        elif type(v) is int:
            _entero(v)
        else:
            _exigir(v is None or type(v) is bool, "tipo_json_no_admitido")


def _coherencia(r, c):
    campos = dict(r.registro.campos_originales)
    for k, v in r.valores_originales:
        _exigir(k not in campos or campos[k] == v, "valor_objetivo_contradictorio")
    for nombre, valor in (("ID", r.registro.id_original), ("ESTACION", r.registro.estacion_literal)):
        _exigir(nombre not in campos or campos[nombre] == valor, "identidad_literal_contradictoria")
    _exigir(r.registro.estructura_correcta or r.estado is EstadoResultadoQA.EVALUACION_INCOMPLETA,
             "estado_incompatible_con_estructura")
    cfg = c.configuracion
    if cfg is not None:
        _exigir(r.regla.categoria in cfg.categorias and
                 (not cfg.reglas or r.regla.identificador in cfg.reglas), "regla_fuera_configuracion")
        if r.regla.categoria is CategoriaQA.VALORES:
            _exigir(len(r.valores_originales) == 1 and r.valores_originales[0][0] in cfg.variables,
                     "campo_fuera_configuracion")


def _restricciones(d, esperadas, limites):
    _claves(d, ("informativas", "bloqueantes"))
    vistos, cantidad = set(), 0
    for grupo in ("informativas", "bloqueantes"):
        _exigir(type(d[grupo]) is list, "lista_restricciones_requerida")
        cantidad += len(d[grupo])
    if cantidad > limites.max_restricciones_documento:
        raise _Incompleto("restricciones_documento_excesivas")
    conocidas = {a["codigo"] for grupo in esperadas.values() for a in grupo}
    for grupo in ("informativas", "bloqueantes"):
        for a in d[grupo]:
            _claves(a, ("codigo", "tipo", "operaciones", "motivo"))
            codigo = _cadena(a["codigo"])
            _cadena(a["tipo"])
            _lista(_cadena)(a["operaciones"])
            _cadena(a["motivo"])
            _exigir(codigo not in vistos, "restriccion_duplicada")
            vistos.add(codigo)
            _exigir(codigo in conocidas, "restriccion_no_comprobable")
    _exigir(d == esperadas, "restricciones_omitidas_o_adulteradas")
    return cantidad


def _validar_paquete(d, limites, etapas):
    _claves(d, _CAMPOS)
    _exigir(d["version_esquema"] == "0.1.0", "version_no_admitida")
    _claves(d["versiones"], ("contrato_qa", "evaluador", "restricciones"))
    _exigir(d["versiones"] == dict(contrato_qa="1.0.0", evaluador="1.0.1", restricciones="1.0.0"),
             "version_no_admitida")
    _exigir(type(d["resultado_id"]) is str and re.fullmatch(r"qa0-[0-9a-f]{64}", d["resultado_id"]),
             "identificador_no_admitido")
    _exigir(type(d["huella_contenido"]) is str and re.fullmatch(r"[0-9a-f]{64}", d["huella_contenido"]),
             "huella_no_admitida")
    for k in ("naturaleza_identidad", "estado_evaluacion", "detalle_diagnostico"):
        _cadena(d[k])
    for k in ("campos_objetivo", "campos_objetivo_no_aportados", "limitaciones"):
        _lista(_cadena)(d[k])
    r, c = _resultado(d["resultado"]), _contexto(d["contexto"])
    _exigir(0 < len(r.regla.identificador) <= 128, "identificador_no_admitido")
    _exigir(r.regla.version == "1.0.0", "version_no_admitida")
    _exigir([v for k, v in r.parametros if k == "evaluador_nivel0"] == ["1.0.1"], "version_no_admitida")
    etapas.add("esquema_tipos_y_versiones")
    _coherencia(r, c)
    etapas.add("coherencia_interna")
    salida = exportar_resultado_json(r, c, limites=_LIMITES_CONTRASTE)
    # Salida propia acotada, no entrada ajena; nunca se utiliza para reparar d.
    esperado = json.loads(salida)
    n = _restricciones(d["restricciones"], esperado["restricciones"], limites)
    etapas.add("restricciones_politica_1.0.0")
    _exigir(d["resultado_id"] == esperado["resultado_id"], "identidad_incoherente")
    _exigir(d["huella_contenido"] == esperado["huella_contenido"], "huella_incoherente")
    etapas.add("identidad_y_huella")
    _exigir(d == esperado, "campos_derivados_contradictorios")
    etapas.add("campos_derivados")
    clave_entrada = (c.espacio_id, c.evaluacion_id, c.escenario_id, c.entrada_id)
    return clave_entrada, _canonico(d["resultado"]["registro"]), n


def consumir_exportaciones(contenido: bytes | str | tuple[bytes | str, ...], *,
                           limites: LimitesConsumoQA | None = None) -> InformeConsumoQA:
    """Un documento o tupla explícita de documentos JSON 0.1.0, solo en memoria.

    Duplicados canónicos idénticos son idempotentes; cualquier contradicción
    rechaza el lote. Ante límites se devuelve INCOMPLETA sin resultados aceptados.
    No hay parser de clases, instrucciones, rutas o URLs recibidas.
    """
    limites = limites if limites is not None else LimitesConsumoQA()
    if type(limites) is not LimitesConsumoQA:
        raise TypeError("Límites de consumo tipados requeridos")
    limites.__post_init__()
    entradas = (contenido,) if type(contenido) in (bytes, str) else contenido
    recibidos = len(entradas) if type(entradas) is tuple else 0
    problemas, documentos, entradas_vistas = [], {}, {}
    comunes, duplicados, incompleta, critica = set(), 0, False, False
    informativas = bloqueantes = 0
    try:
        _exigir(type(entradas) is tuple and recibidos > 0, "entrada_o_lote_no_admitido")
        if recibidos > limites.max_resultados:
            raise _Incompleto("resultados_excesivos")
        cuerpos, bytes_lote = [], 0
        for entrada in entradas:
            _exigir(type(entrada) in (bytes, str), "entrada_o_lote_no_admitido")
            if len(entrada) > limites.max_bytes_documento:
                raise _Incompleto("bytes_documento_excesivos")
            cuerpo = entrada.encode("utf-8", errors="strict") if type(entrada) is str else entrada
            if len(cuerpo) > limites.max_bytes_documento:
                raise _Incompleto("bytes_documento_excesivos")
            bytes_lote += len(cuerpo)
            if bytes_lote > limites.max_bytes_lote:
                raise _Incompleto("bytes_lote_excesivos")
            _exigir(not cuerpo.startswith(b"\xef\xbb\xbf"), "bom_no_admitido")
            cuerpos.append(cuerpo)
        comunes.add("limites_entrada")
        nodos_lote = restricciones_lote = 0
        for indice, cuerpo in enumerate(cuerpos, 1):
            etapas = set()
            try:
                progreso = dict(profundidad_maxima=0)
                d = leer_json(cuerpo, limites, None, progreso, max_bytes=limites.max_bytes_documento,
                    estados=_EstadoJSON, codigo_bytes="bytes_documento_excesivos")
                _comprobar_arbol(d, limites)
                nodos_lote += progreso["nodos_documento"]
                if nodos_lote > limites.unidades_lote:
                    raise _Incompleto("nodos_lote_excesivos")
                etapas.add("json_estricto")
                clave, registro, cantidad = _validar_paquete(d, limites, etapas)
                restricciones_lote += cantidad  # Incluye repeticiones recibidas para acotar trabajo.
                if restricciones_lote > limites.max_restricciones_lote:
                    raise _Incompleto("restricciones_lote_excesivas")
                texto, rid = _canonico(d), d["resultado_id"]
                if rid in documentos:
                    _exigir(documentos[rid] == texto, "identidad_reutilizada_contradictoria")
                    duplicados += 1
                else:
                    _exigir(clave not in entradas_vistas or entradas_vistas[clave] == registro,
                             "entrada_reutilizada_contradictoria")
                    entradas_vistas[clave] = registro
                    documentos[rid] = texto
                    informativas += len(d["restricciones"]["informativas"])
                    bloqueantes += len(d["restricciones"]["bloqueantes"])
            except _Incompleto as e:
                incompleta = True
                problemas.append(ProblemaConsumoQA(str(e), indice))
                break  # No continuar trabajo después de agotar un presupuesto.
            except (_Rechazo, _Invalido) as e:
                critica = True
                problemas.append(ProblemaConsumoQA(str(e), indice))
            except (json.JSONDecodeError, UnicodeError, ValueError, TypeError, OverflowError):
                critica = True
                problemas.append(ProblemaConsumoQA("json_o_contrato_no_admitido", indice))
            finally:
                comunes = comunes | etapas if indice == 1 else comunes & (etapas | {"limites_entrada"})
        if not critica and not incompleta:
            comunes.add("identidades_en_lote")
    except _Incompleto as e:
        incompleta = True
        problemas.append(ProblemaConsumoQA(str(e)))
    except _Rechazo as e:
        critica = True
        problemas.append(ProblemaConsumoQA(str(e)))
    except UnicodeError:
        critica = True
        problemas.append(ProblemaConsumoQA("unicode_no_admitido"))
    except (RecursionError, MemoryError):
        incompleta = True
        problemas.append(ProblemaConsumoQA("recursos_de_validacion_agotados"))
    estado = (EstadoConsumoQA.CONTRATO_RECHAZADO if critica else
        EstadoConsumoQA.VALIDACION_INCOMPLETA if incompleta else EstadoConsumoQA.CONTRATO_VALIDO_EN_ALCANCE)
    valido = estado is EstadoConsumoQA.CONTRATO_VALIDO_EN_ALCANCE
    if incompleta:
        comunes.intersection_update(("limites_entrada",))
    return InformeConsumoQA(estado, recibidos, len(documentos) if valido else 0, duplicados,
        tuple(sorted(comunes)), tuple(sorted(_ETAPAS - comunes)) + _NO_REALIZADAS, tuple(problemas),
        tuple(documentos[k] for k in sorted(documentos)) if valido else (),
        informativas if valido else 0, bloqueantes if valido else 0)
