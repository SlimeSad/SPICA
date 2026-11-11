"""Conciliación experimental 0.1.0, acotada y sin persistencia o autenticación.

Revalida documentos de informes de consumo; el estado del informe no es prueba
de origen. Conserva lotes y conflictos, sin construir un lote fusionado.
"""

from dataclasses import dataclass, field, fields
from enum import Enum
import hashlib
from itertools import combinations
import json
import re

from .consumo import (EstadoConsumoQA, InformeConsumoQA, LimitesConsumoQA,
                      consumir_exportaciones)

VERSION_CONCILIACION_QA = "0.1.0"


class EstadoConciliacionQA(Enum):
    COINCIDENCIA = "coincidencia_de_representacion"
    COMPATIBLES = "compatibles_en_alcance_sin_equivalencia"
    CONFLICTO = "conflicto"
    NO_COMPARABLE = "comparacion_no_disponible"


@dataclass(frozen=True)
class LoteQA:
    lote_id: str  # Etiqueta declarada, ajena al identificador de evaluación.
    consumo: InformeConsumoQA


@dataclass(frozen=True)
class ResumenLoteQA:
    lote_id: str
    huella_representacion: str
    recibidos_declarados: int
    duplicados_declarados: int
    documentos: tuple[str, ...]
    restricciones_informativas: int
    restricciones_bloqueantes: int


@dataclass(frozen=True)
class HallazgoLotesQA:
    codigo: str
    lote_ids: tuple[str, ...]
    resultado_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class InformeConciliacionQA:
    estado: EstadoConciliacionQA
    lotes: tuple[ResumenLoteQA, ...]
    resultados_examinados: int  # Suma por lote; no son observaciones independientes.
    coincidencias: tuple[HallazgoLotesQA, ...]
    conflictos: tuple[HallazgoLotesQA, ...]
    no_comparables: tuple[HallazgoLotesQA, ...]
    limitaciones: tuple[str, ...] = (
        "comparacion_de_declaraciones_sin_autenticacion", "sin_unicidad_global_acreditada",
        "sin_verificacion_fisica_independiente", "sin_prueba_de_ejecucion_real_de_reglas",
        "sin_validacion_cientifica", "sin_autorizacion_operativa",
        "sin_correspondencias_inferidas_entre_evaluaciones", "sin_fusion_o_persistencia_de_lotes")
    version_contrato: str = field(default=VERSION_CONCILIACION_QA, init=False)


class _NoComparable(Exception):
    pass


def _exigir(condicion, codigo):
    if not condicion:
        raise _NoComparable(codigo)


def _canonico(v):
    return json.dumps(v, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":"))


def _auditar(lote, limites):
    r = lote.consumo
    _exigir(type(r) is InformeConsumoQA, "informe_de_consumo_requerido")
    _exigir(r.estado is EstadoConsumoQA.CONTRATO_VALIDO_EN_ALCANCE, "lote_no_validado")
    for nombre in ("diagnosticos_recibidos", "diagnosticos_aceptados", "duplicados_exactos",
                   "restricciones_informativas", "restricciones_bloqueantes"):
        v = getattr(r, nombre)
        _exigir(type(v) is int and v >= 0, "conteos_de_informe_no_admitidos")
    _exigir(0 < r.diagnosticos_recibidos <= 1024 and
             r.diagnosticos_recibidos == r.diagnosticos_aceptados + r.duplicados_exactos,
             "conteos_de_informe_incoherentes")
    _exigir(type(r.documentos_aceptados) is tuple and
             0 < len(r.documentos_aceptados) <= limites.max_resultados and
             all(type(t) is str for t in r.documentos_aceptados), "documentos_de_informe_no_admitidos")
    for nombre in ("comprobaciones_realizadas", "comprobaciones_no_realizadas", "limitaciones_confianza"):
        v = getattr(r, nombre)
        _exigir(type(v) is tuple and len(v) <= 32 and all(type(x) is str for x in v),
                 "metadatos_de_informe_no_admitidos")
    _exigir(type(r.problemas) is tuple and not r.problemas and
             type(r.version_contrato) is str and type(r.version_exportacion) is str,
             "informe_incompatible")
    nuevo = consumir_exportaciones(r.documentos_aceptados, limites=limites)
    _exigir(nuevo.estado is EstadoConsumoQA.CONTRATO_VALIDO_EN_ALCANCE, "revalidacion_no_disponible")
    # Las repeticiones del transporte original ya no están en los documentos únicos.
    # Solo su consistencia aritmética puede contrastarse; no se autentica su historia.
    for f in fields(InformeConsumoQA):
        if f.name not in ("diagnosticos_recibidos", "duplicados_exactos"):
            _exigir(getattr(r, f.name) == getattr(nuevo, f.name), "informe_no_corresponde_a_documentos")
    h = hashlib.sha256()
    for i, t in enumerate(nuevo.documentos_aceptados):
        if i:
            h.update(b"\n")
        h.update(t.encode("utf-8"))
    return ResumenLoteQA(lote.lote_id, h.hexdigest(), r.diagnosticos_recibidos,
        r.duplicados_exactos, nuevo.documentos_aceptados,
        nuevo.restricciones_informativas, nuevo.restricciones_bloqueantes)


def _indices(lote):
    documentos, entradas, comprobaciones, ambitos = {}, {}, {}, set()
    # Solo se leen representaciones propias que acaban de superar el consumidor.
    for t in lote.documentos:
        d = json.loads(t)
        rid, c, r = d["resultado_id"], d["contexto"], d["resultado"]
        ambito = c["espacio_id"], c["evaluacion_id"]
        ambitos.add(ambito)
        entrada = ambito + (c["escenario_id"], c["entrada_id"])
        entradas.setdefault(entrada, (_canonico(r["registro"]), []))[1].append(rid)
        clave = entrada + (r["regla"]["identificador"], r["regla"]["version"],
            d["versiones"]["evaluador"], tuple(sorted(d["campos_objetivo"])))
        contextos, ids = comprobaciones.setdefault(clave, (set(), []))
        contextos.add(_canonico(c))
        ids.append(rid)
        documentos[rid] = (t, d["restricciones"])
    return documentos, entradas, comprobaciones, ambitos


def conciliar_lotes(lotes: tuple[LoteQA, ...], *,
                    limites_consumo: LimitesConsumoQA | None = None) -> InformeConciliacionQA:
    """Entre dos y ocho lotes declarados, revalidados en memoria y sin fusionar.

    Iguales IDs solo coinciden si todo el JSON canónico coincide. Otros contextos
    no se alinean automáticamente. Un conflicto observado prevalece sobre falta
    de comparabilidad; esta prevalece sobre coincidencias parciales.
    """
    limites = limites_consumo if limites_consumo is not None else LimitesConsumoQA()
    if type(limites) is not LimitesConsumoQA:
        raise TypeError("Límites de consumo tipados requeridos")
    limites.__post_init__()
    resumenes, coincidencias, conflictos, no_comparables = [], [], [], []
    if type(lotes) is not tuple or not 2 <= len(lotes) <= 8:
        no_comparables.append(HallazgoLotesQA("se_requieren_entre_dos_y_ocho_lotes", ()))
    else:
        for lote in lotes:
            nombre = ()
            try:
                _exigir(type(lote) is LoteQA, "lote_tipado_requerido")
                _exigir(type(lote.lote_id) is str and
                         re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", lote.lote_id),
                         "etiqueta_lote_no_admitida")
                nombre = (lote.lote_id,)
                resumenes.append(_auditar(lote, limites))
            except _NoComparable as e:
                no_comparables.append(HallazgoLotesQA(str(e), nombre))
            except (MemoryError, RecursionError):
                no_comparables.append(HallazgoLotesQA("recursos_de_comparacion_agotados", nombre))
                break
    resumenes.sort(key=lambda l: (l.lote_id, l.huella_representacion, l.documentos,
                                  l.recibidos_declarados, l.duplicados_declarados))
    try:
        indexados = [(l, _indices(l)) for l in resumenes]
        for (a, (ad, ae, ac, aa)), (b, (bd, be, bc, ba)) in combinations(indexados, 2):
            nombres = (a.lote_id, b.lote_id)
            if a.lote_id == b.lote_id and a.documentos != b.documentos:
                conflictos.append(HallazgoLotesQA("identidad_lote_reutilizada", nombres))
            if aa != ba:
                no_comparables.append(HallazgoLotesQA("ambitos_de_evaluacion_sin_correspondencia", nombres))
            for rid in sorted(ad.keys() & bd.keys()):
                at, ar = ad[rid]
                bt, br = bd[rid]
                if at == bt:
                    coincidencias.append(HallazgoLotesQA("resultado_identico", nombres, (rid,)))
                else:
                    conflictos.append(HallazgoLotesQA("identidad_resultado_reutilizada", nombres, (rid,)))
                    if ar != br:
                        conflictos.append(HallazgoLotesQA("restricciones_discrepantes", nombres, (rid,)))
            for clave in sorted(ae.keys() & be.keys(), key=_canonico):
                if ae[clave][0] != be[clave][0]:
                    ids = tuple(sorted(ae[clave][1] + be[clave][1]))
                    conflictos.append(HallazgoLotesQA("identidad_entrada_reutilizada", nombres, ids))
            for clave in sorted(ac.keys() & bc.keys(), key=_canonico):
                if ac[clave][0] != bc[clave][0]:
                    ids = tuple(sorted(ac[clave][1] + bc[clave][1]))
                    no_comparables.append(HallazgoLotesQA("contextos_de_comprobacion_distintos", nombres, ids))
    except (MemoryError, RecursionError):
        no_comparables.append(HallazgoLotesQA("recursos_de_comparacion_agotados", ()))
    mismos = len(resumenes) >= 2 and all(l.documentos == resumenes[0].documentos for l in resumenes)
    estado = (EstadoConciliacionQA.CONFLICTO if conflictos else
        EstadoConciliacionQA.NO_COMPARABLE if no_comparables else
        EstadoConciliacionQA.COINCIDENCIA if mismos else EstadoConciliacionQA.COMPATIBLES)
    ordenar = lambda h: (h.codigo, h.lote_ids, h.resultado_ids)
    return InformeConciliacionQA(estado, tuple(resumenes), sum(len(l.documentos) for l in resumenes),
        tuple(sorted(coincidencias, key=ordenar)), tuple(sorted(conflictos, key=ordenar)),
        tuple(sorted(no_comparables, key=ordenar)))
