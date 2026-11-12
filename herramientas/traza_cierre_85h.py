"""Proyección pura de informes 85-G. No abre rutas, ejecuta QA ni autoriza usos.

La referencia SHA y el informe cotejado deben proceder del ensayo confiable.
Ni un DTO congelado ni una huella aportada por el mismo emisor autentican hechos.
"""

from collections import Counter
from dataclasses import dataclass, fields, is_dataclass
from datetime import datetime
from enum import Enum
import hashlib
import json
import math
import re
from types import MappingProxyType

from spica.calidad import restricciones_resultado
from spica.calidad.consumo import EstadoConsumoQA, consumir_exportaciones, LimitesConsumoQA
from spica.calidad.conciliacion_lotes import LoteQA, conciliar_lotes

VERSION_TRAZA_85H = "0.1.0"
MAX_BYTES_TRAZA = 8_388_608
LIMITACIONES = (
    "solo_memoria_proceso_confiable", "sin_persistencia_duradera",
    "sin_recuperacion_tras_apagado", "sin_autenticidad_independiente",
    "hash_no_es_firma", "sin_revalidacion_fisica_tras_eliminar_temporales",
    "sin_autorizacion_cientifica_u_operativa", "sin_unicidad_global",
    "sin_resumen_equivalente_entre_activos_distintos",
)
NO_REALIZADAS = (
    "red_o_get_externo", "adquisicion_institucional", "validacion_cientifica",
    "conversion_hora_ubigeo_pp", "gis", "ia", "persistencia_de_traza",
    "migracion_de_almacenes_preexistentes", "lectura_operativa",
)
ETAPAS = ("validacion", "adquisicion_simulada", "catalogo", "recuperacion_A", "qa_A",
          "exportacion_A", "consumo_A", "recuperacion_B", "qa_B", "exportacion_B",
          "consumo_B", "conciliacion")


def _canonico(d):
    return json.dumps(d, ensure_ascii=False, sort_keys=True, allow_nan=False, separators=(",", ":"))


def _huella(texto):
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def _datos(v, *, omitir=()):
    """Solo valores de contratos conocidos. Nunca serializa rutas o __dict__."""
    if v is None or type(v) in (str, bool, int):
        return v
    if type(v) is float and math.isfinite(v):
        return v  # Presupuestos técnicos (p. ej. expansión ZIP), nunca observaciones.
    if isinstance(v, Enum) and type(v).__module__.startswith(("spica.", "herramientas.piloto_integracion_85g")):
        return v.value
    if type(v) is datetime:
        return v.isoformat()
    if type(v) in (tuple, list):
        return [_datos(x) for x in v]
    if type(v) in (dict, MappingProxyType):
        if not all(type(k) is str for k in v):
            raise TypeError("claves_de_traza_no_admitidas")
        return {k: _datos(x) for k, x in v.items()}
    if is_dataclass(v) and not isinstance(v, type) and type(v).__module__.startswith(
            ("spica.", "herramientas.piloto_integracion_85g")):
        return {f.name: _datos(getattr(v, f.name)) for f in fields(v) if f.name not in omitir}
    raise TypeError("tipo_de_traza_no_admitido")


def _informe(r):
    # Importación diferida: el auxiliar puede capturar durante su propio cierre.
    from herramientas.piloto_integracion_85g import InformeEjecucion85G, ContratoEjecucion85G
    if type(r) is not InformeEjecucion85G or type(r.contrato) is not ContratoEjecucion85G:
        raise TypeError("informe_85g_tipado_requerido")
    r.contrato.__post_init__()
    p = r.contrato.presupuesto
    for nombre in ("resultados", "informes_qa", "lecturas", "exportaciones", "consumos"):
        v = getattr(r, nombre)
        if type(v) is not tuple or len(v) > 2:
            raise ValueError("lotes_de_traza_no_admitidos")
    for lote in r.resultados:
        if type(lote) is not tuple or len(lote) > p.max_resultados:
            raise ValueError("resultados_de_traza_excesivos")
    for lote in r.exportaciones:
        if type(lote) is not tuple or len(lote) > p.max_resultados:
            raise ValueError("exportaciones_de_traza_excesivas")
        usados = 0
        for texto in lote:
            _limite(texto, min(p.max_bytes_json, 1_048_576))
            usados += len(texto.encode("utf-8"))
            if usados > p.max_bytes_json:
                raise ValueError("exportaciones_de_traza_excesivas")


def evidencia_85h(r):
    """Datos materiales conservados, sin rutas absolutas ni copias extras del CSV.

    El JSON oficial se conserva una vez por exportación, incluso si fue rechazado.
    Los nativos se referencian por contenido, regla, posición y restricciones.
    """
    _informe(r)
    a = r.adquisicion
    activo = None if a is None else _datos(a.activo, omitir=("ruta_interna",))
    http = None if a is None else _datos(a.informe_http, omitir=("ruta_local", "temporal_restante"))
    nativos = []
    for lote in r.resultados:
        nativos.append([dict(huella_contenido=_huella(_canonico(_datos(v))),
            regla=_datos(v.regla), numero_registro=v.registro.numero_registro,
            campos=[k for k, _ in v.valores_originales], estado=v.estado.value,
            diagnostico=v.diagnostico, procedencia=_datos(v.procedencia),
            restricciones=_datos(restricciones_resultado(v))) for v in lote])
    consumos = []
    for c in r.consumos:
        d = _datos(c, omitir=("documentos_aceptados",))
        d["huellas_documentos_aceptados"] = [_huella(t) for t in c.documentos_aceptados]
        consumos.append(d)
    conciliacion = None
    if r.conciliacion is not None:
        conciliacion = _datos(r.conciliacion, omitir=("lotes",))
        conciliacion["lotes"] = [_datos(lote, omitir=("documentos",)) for lote in r.conciliacion.lotes]
    return dict(contrato=_datos(r.contrato), activo_id_conocido=r.activo_id, activo=activo,
        http=http, fase_adaptador=None if a is None else a.fase.value,
        estructura=None if a is None else _datos(a.estructura),
        intentos=[] if a is None else _datos(a.intentos_http),
        catalogo=_datos(r.registro_catalogo), recuperaciones=list(r.recuperaciones),
        resultados=nativos, informes_qa=_datos(r.informes_qa), lecturas=_datos(r.lecturas),
        exportaciones=[list(lote) for lote in r.exportaciones], consumos=consumos,
        conciliacion=conciliacion, recursos_adquiridos=list(r.recursos_adquiridos),
        solicitudes_simuladas=r.solicitudes_simuladas)


def capturar_evidencia_85h(r):
    """Captura antes de cerrar; no vuelve a leer el archivo ni calcula su SHA."""
    texto = _canonico(evidencia_85h(r))
    _limite(texto, MAX_BYTES_TRAZA)
    return texto


def _limite(texto, max_bytes):
    if type(max_bytes) is not int or not 0 < max_bytes <= MAX_BYTES_TRAZA:
        raise ValueError("presupuesto_traza_no_admitido")
    if type(texto) is not str or len(texto) > max_bytes or len(texto.encode("utf-8")) > max_bytes:
        raise ValueError("presupuesto_traza_excedido")


def _auditar(r):
    """Cotejos puros contra objetos reales retenidos; no prueba su autenticidad."""
    from herramientas.piloto_integracion_85g import FUENTE_SINTETICA, URL_SIMULADA, ORIGEN_SIMULADO
    problemas, enlaces = [], []

    def enlace(nombre, condicion, disponible):
        estado = "coherente" if disponible and condicion else "discontinuidad"
        enlaces.append((nombre, estado))
        if disponible and not condicion:
            problemas.append(nombre + "_inconsistente")

    c, a, cat = r.contrato, r.adquisicion, r.registro_catalogo
    inicios = tuple(n for n, e in r.traza if e == "iniciada")
    if (inicios != ETAPAS[:len(inicios)] or len(inicios) > len(ETAPAS)
            or not r.traza or r.traza[0] != ("contrato", "planificada")
            or r.traza[-1] != (r.fase_final, r.estado.value)):
        problemas.append("transiciones_de_etapas_inconsistentes")
    if c.version != "0.1.0" or c.naturaleza != "simulacion_sintetica_offline":
        problemas.append("version_o_naturaleza_incompatible")
    requeridas = {"solo_sintetico_sin_red", "sin_autenticidad_institucional", "sin_validacion_cientifica",
                  "sin_autorizacion_operativa", "sin_normalizar_hora_ubigeo_pp",
                  "sin_derivados_persistentes", "contextos_declarados_sin_unicidad_global"}
    if set(r.restricciones) != requeridas or len(r.restricciones) != len(requeridas):
        problemas.append("restricciones_globales_incompatibles")
    if (len(r.resultados) > 2 or len(r.informes_qa) != len(r.resultados)
            or len(r.lecturas) != len(r.resultados) or len(r.consumos) > len(r.exportaciones)
            or len(r.exportaciones) > len(r.resultados)):
        problemas.append("cardinalidad_de_etapas_inconsistente")
        return tuple(problemas), ()
    if (len(set(r.recursos_adquiridos)) != len(r.recursos_adquiridos)
            or not set(r.recursos_adquiridos) <= {"raw_sqlite", "cliente_mock", "catalogo_cientifico_sqlite"}
            or not set(r.recursos_liberados) <= set(r.recursos_adquiridos)):
        problemas.append("recursos_inconsistentes")
    if r.autorizacion_operativa or r.ejecucion_cientifica:
        problemas.append("autorizacion_no_admitida")
    activo = None if a is None else a.activo
    enlace("entrada_activo", activo is not None and (
        r.activo_id == activo.asset_id and activo.size_bytes == c.tamano_esperado
        and activo.sha256 == c.sha256_esperado and activo.declaracion.proyecto_id == c.proyecto_id
        and activo.declaracion.objeto_id == c.objeto_id and activo.declaracion.fuente == FUENTE_SINTETICA
        and activo.declaracion.recurso_id == c.recurso_id), activo is not None)
    enlace("transferencia_activo", a is not None and (
        a.informe_http.sha256 == activo.sha256 and a.informe_http.bytes_almacenados == activo.size_bytes
        and a.informe_http.bytes_declarados == activo.size_bytes and a.informe_http.origen == ORIGEN_SIMULADO + "/"
        and a.informe_http.codigo_http == 200), a is not None)
    enlace("activo_catalogo", cat is not None and activo is not None and (
        cat.revision == 1 and cat.entidad.fuente == activo.declaracion.fuente
        and cat.entidad.producto_id == c.producto_id and cat.entidad.identificador == c.recurso_id
        and cat.entidad.localizador == URL_SIMULADA
        and cat.entidad.procedencia.evidencia == "asset_id=" + activo.asset_id), cat is not None)
    enlace("activo_recuperacion", bool(r.recuperaciones) and activo is not None,
           bool(r.recuperaciones))
    limites = LimitesConsumoQA(max_resultados=c.presupuesto.max_resultados,
                              max_bytes_lote=c.presupuesto.max_bytes_json)
    reconsumos = []
    for i, lote in enumerate(r.resultados):
        nombre = "AB"[i]
        qa = r.informes_qa[i] if i < len(r.informes_qa) else None
        procedencias = all(activo is not None and v.procedencia.asset_id == activo.asset_id
            and v.procedencia.sha256_referencia == activo.sha256
            and v.procedencia.fuente == FUENTE_SINTETICA and v.procedencia.recurso_id == c.recurso_id
            and v.procedencia.adquisicion_id is None and v.procedencia.documento is None for v in lote)
        enlace("recuperacion_qa_" + nombre, procedencias and "recuperacion_" + nombre in r.recuperaciones,
               True)
        if qa is None or qa.resultados_emitidos != len(lote):
            problemas.append("cardinalidad_qa_" + nombre)
        if qa is not None:
            conteos = Counter((v.regla.categoria, v.estado) for v in lote)
            if (qa.configuracion != c.configuracion
                    or len(qa.conteos) != len(conteos)
                    or len(qa.reglas_ejecutadas) != len(set(qa.reglas_ejecutadas))
                    or Counter({(cat, estado): cantidad for cat, estado, cantidad in qa.conteos}) != conteos
                    or set(qa.reglas_ejecutadas) != {v.regla for v in lote}
                    or any(v.procedencia != qa.procedencia for v in lote)):
                problemas.append("informe_qa_" + nombre + "_inconsistente")
        documentos = r.exportaciones[i] if i < len(r.exportaciones) else ()
        consumo = r.consumos[i] if i < len(r.consumos) else None
        valido = consumo is not None and consumo.estado is EstadoConsumoQA.CONTRATO_VALIDO_EN_ALCANCE
        enlace("qa_exportacion_" + nombre, valido and len(documentos) == len(lote), valido)
        if valido:
            nuevo = consumir_exportaciones(documentos, limites=limites)
            reconsumos.append(nuevo)
            if nuevo != consumo:
                problemas.append("consumo_" + nombre + "_inconsistente")
            if nuevo.estado is EstadoConsumoQA.CONTRATO_VALIDO_EN_ALCANCE:
                vistos = set()
                nativos_por_huella = {_huella(_canonico(_datos(v))): v for v in lote}
                for texto in nuevo.documentos_aceptados:
                    d = json.loads(texto)  # Solo salida validada por el consumidor acotado.
                    if d["resultado_id"] in vistos:
                        problemas.append("identidad_resultado_duplicada")
                    vistos.add(d["resultado_id"])
                    v = nativos_por_huella.get(d["huella_contenido"])
                    if (v is None
                            or d["contexto"]["evaluacion_id"] != c.evaluacion_id
                            or d["contexto"]["configuracion"] != _datos(c.configuracion)
                            or d["contexto"]["entrada_id"] != c.entrada_id + ":" + str(v.registro.numero_registro)):
                        problemas.append("resultado_json_" + nombre + "_inconsistente")
                if len(vistos) != len(lote) or nuevo.duplicados_exactos:
                    problemas.append("cardinalidad_exportacion_" + nombre)
                restricciones = tuple(x for v in lote for x in restricciones_resultado(v))
                conteo = Counter(x.tipo.value for x in restricciones)
                if (conteo["informativa"], conteo["bloqueo_uso_del_resultado"]) != (
                        nuevo.restricciones_informativas, nuevo.restricciones_bloqueantes):
                    problemas.append("restricciones_" + nombre + "_inconsistentes")
        enlace("exportacion_consumo_" + nombre, valido and reconsumos[-1] == consumo if valido else False,
               consumo is not None)
    if r.conciliacion is not None:
        if len(reconsumos) != 2:
            problemas.append("conciliacion_sin_consumos_validos")
        else:
            esperado = conciliar_lotes(tuple(LoteQA(n, v) for n, v in zip("AB", reconsumos, strict=True)),
                                       limites_consumo=limites)
            if esperado != r.conciliacion:
                problemas.append("conciliacion_inconsistente")
    enlace("consumos_conciliacion", r.conciliacion is not None and len(reconsumos) == 2
           and "conciliacion_inconsistente" not in problemas, r.conciliacion is not None)
    return tuple(dict.fromkeys(problemas)), tuple(enlaces)


def _etapas(r):
    salida = []
    for nombre in ETAPAS:
        eventos = [e for n, e in r.traza if n == nombre]
        if "iniciada" not in eventos:
            estado = "no_iniciada"
        elif any(e in eventos for e in ("completada", "bytes_incorporados_y_controlados",
                "recurso_consultado_sin_capacidad_institucional", "evaluacion_cerrada_y_original_recomprobado",
                "restricciones_nativas_y_consumidas_coinciden", "reproducciones_del_mismo_activo_coinciden")):
            estado = "concluida_en_alcance"
        elif nombre == r.fase_final:
            estado = r.estado.value
        else:
            estado = "sin_confirmacion_de_cierre"
        salida.append((nombre, estado))
    salida.append(("cierre", "liberado" if r.temporales_eliminados and
        sorted(r.recursos_adquiridos) == sorted(r.recursos_liberados) else "no_confirmado"))
    return tuple(salida)


@dataclass(frozen=True)
class TrazaCierre85H:
    canonico: str
    sha256: str

    def __bool__(self):
        raise TypeError("traza_no_es_permiso_ni_autenticacion")


@dataclass(frozen=True)
class VerificacionTraza85H:
    coherente_en_alcance: bool
    cadena_completa: bool
    diagnosticos: tuple[str, ...]
    comprobaciones: tuple[str, ...] = (
        "referencia_memoria", "representacion_canonica", "linaje_contractual",
        "restricciones", "consumo_y_conciliacion", "captura_previa_y_cierre")
    limitaciones: tuple[str, ...] = LIMITACIONES

    def __bool__(self):
        raise TypeError("verificacion_no_es_autorizacion")


def construir_traza_85h(r, *, max_bytes=MAX_BYTES_TRAZA):
    """No acepta JSON de terceros. El informe tipado tampoco es prueba de origen."""
    _informe(r)
    _limite("", max_bytes)
    evidencia = evidencia_85h(r)
    _limite(_canonico(evidencia), max_bytes)
    problemas, enlaces = _auditar(r)
    from herramientas.piloto_integracion_85g import EstadoEjecucion85G
    if r.estado not in (EstadoEjecucion85G.CONCLUIDA, EstadoEjecucion85G.INCOMPLETA,
                        EstadoEjecucion85G.FALLIDA, EstadoEjecucion85G.CANCELADA):
        raise ValueError("estado_no_final")
    previa = r.captura_antes_cierre
    if previa is not None and previa != _canonico(evidencia):
        raise ValueError("evidencia_cambio_tras_captura")
    if r.recursos_adquiridos and previa is None and "captura_previa_no_disponible" not in r.diagnosticos:
        raise ValueError("captura_previa_ausente")
    cerrados = sorted(r.recursos_adquiridos) == sorted(r.recursos_liberados)
    completa = r.estado is EstadoEjecucion85G.CONCLUIDA
    if completa and (problemas or any(s != "coherente" for _, s in enlaces)
                     or len(r.consumos) != 2 or len(r.resultados) != 2
                     or any(s != "concluida_en_alcance" for _, s in _etapas(r)[:-1])
                     or "pre_cierre" not in r.recuperaciones
                     or r.recuperaciones != ("recuperacion_A", "post_qa_A", "recuperacion_B", "post_qa_B", "pre_cierre")
                     or set(r.recursos_adquiridos) != {"raw_sqlite", "cliente_mock", "catalogo_cientifico_sqlite"}
                     or r.solicitudes_simuladas != 1 or r.error_http_raw is not None
                     or r.fase_final != "cierre"
                     or not r.temporales_eliminados or not cerrados or r.diagnosticos):
        raise ValueError("cierre_concluido_contradictorio")
    # El fallo de limpieza debe impedir un éxito incluso si el resto fue válido.
    if (not r.temporales_eliminados or not cerrados) and r.estado is not EstadoEjecucion85G.FALLIDA:
        raise ValueError("cierre_recursos_contradictorio")
    if r.estado is not EstadoEjecucion85G.CONCLUIDA and not r.diagnosticos:
        raise ValueError("estado_parcial_sin_causa")
    datos = dict(version_traza=VERSION_TRAZA_85H, evidencia=evidencia,
        estado_final=r.estado.value, fase_final=r.fase_final, diagnosticos=list(r.diagnosticos),
        error_http_raw=_datos(r.error_http_raw),
        etapas=_datos(_etapas(r)), eventos=_datos(r.traza), restricciones=list(r.restricciones),
        recursos_liberados=list(r.recursos_liberados), temporales_eliminados=r.temporales_eliminados,
        captura_previa_sha256=None if previa is None else _huella(previa),
        incidencias_linaje=list(problemas), enlaces=_datos(enlaces),
        cadena_completa=completa, limitaciones=list(LIMITACIONES), no_realizadas=list(NO_REALIZADAS),
        ejecucion_cientifica=False, autorizacion_operativa=False)
    texto = _canonico(datos)
    _limite(texto, max_bytes)
    return TrazaCierre85H(texto, _huella(texto))


def verificar_traza_85h(traza, informe, *, referencia_sha256):
    """Cotejo con referencia e informe conservados por separado en memoria.

    No importa ni autocertifica un expediente ajeno. No lee el activo eliminado.
    Un atacante que sustituya informe Y referencia queda fuera de este modelo.
    """
    if type(traza) is not TrazaCierre85H:
        raise TypeError("traza_tipificada_requerida")
    if type(referencia_sha256) is not str or not re.fullmatch(r"[0-9a-f]{64}", referencia_sha256):
        raise ValueError("referencia_sha256_requerida")
    try:
        _limite(traza.canonico, MAX_BYTES_TRAZA)
        if _huella(traza.canonico) != referencia_sha256 or traza.sha256 != referencia_sha256:
            return VerificacionTraza85H(False, False, ("huella_no_corresponde_a_referencia",))
        esperada = construir_traza_85h(informe)
        if traza != esperada:
            return VerificacionTraza85H(False, False, ("traza_no_corresponde_a_evidencia",))
    except (TypeError, ValueError, IndexError, KeyError):
        return VerificacionTraza85H(False, False, ("evidencia_incompatible_o_contradictoria",))
    from herramientas.piloto_integracion_85g import EstadoEjecucion85G
    return VerificacionTraza85H(True, informe.estado is EstadoEjecucion85G.CONCLUIDA, ())
