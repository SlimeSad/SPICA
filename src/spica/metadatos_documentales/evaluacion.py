"""Requisitos documentales de operaciones propuestas; jamás las ejecuta."""

from dataclasses import dataclass, field
from enum import Enum

from .modelos import (
    AspectoUso as A, ExpedienteMetadatos, PresenciaInformacion as P,
    TipoRelacion as T, VERSION_CONTRATO, localizar, _tupla, _texto, _id, _verificado,
)


class OperacionUso(Enum):
    CONSULTA_DOCUMENTAL = "consulta_documental"
    CONVERSION_TEMPORAL = "conversion_temporal_propuesta"
    ASIGNACION_ESPACIAL = "asignacion_espacial_propuesta"
    INTERPRETACION_VARIABLE = "interpretacion_variable_propuesta"
    EQUIVALENCIA_EDITORIAL = "equivalencia_editorial_propuesta"
    ACREDITACION_CALIDAD = "acreditacion_calidad_propuesta"
    REDISTRIBUCION = "redistribucion_propuesta"


@dataclass(frozen=True)
class DiagnosticoUso:
    codigo: str
    afirmaciones: tuple[str, ...]
    referencias: tuple[str, ...]
    bloqueante: bool

    def __post_init__(self):
        _texto(self.codigo, 128)
        _tupla(self.afirmaciones, str, 256)
        _tupla(self.referencias, str, 256)
        if not self.afirmaciones or len(self.afirmaciones) != len(self.referencias) or type(self.bloqueante) is not bool:
            raise ValueError("diagnostico_sin_traza_o_bloqueo_tipificado")
        for i in self.afirmaciones:
            _id(i)
        for r in self.referencias:
            _texto(r, 8192)
        if len(set(self.afirmaciones)) != len(self.afirmaciones):
            raise ValueError("diagnostico_con_afirmaciones_repetidas")


@dataclass(frozen=True)
class ResultadoUso:
    expediente: ExpedienteMetadatos = field(repr=False)
    operacion: OperacionUso
    seleccion: tuple[str, ...]
    diagnosticos: tuple[DiagnosticoUso, ...]
    ejecucion_autorizada: bool = field(default=False, init=False)
    operacion_ejecutada: bool = field(default=False, init=False)
    version: str = field(default=VERSION_CONTRATO, init=False)

    def __post_init__(self):
        if type(self.expediente) is not ExpedienteMetadatos or type(self.operacion) is not OperacionUso:
            raise TypeError("resultado_documental_tipificado_requerido")
        _tupla(self.seleccion, str, 256)
        _tupla(self.diagnosticos, DiagnosticoUso, 8192)
        mapa = {a.identificador: a for a in self.expediente.afirmaciones}
        if not self.diagnosticos or not self.seleccion or len(set(self.seleccion)) != len(self.seleccion) or not set(self.seleccion) <= mapa.keys():
            raise ValueError("resultado_sin_diagnosticos_o_seleccion_valida")
        for d in self.diagnosticos:
            if not set(d.afirmaciones) <= mapa.keys():
                raise ValueError("diagnostico_ajeno_al_expediente")
            refs = tuple(mapa[i].fuente.identificador + "@" + mapa[i].fuente.sha256 + "#" + localizar(mapa[i].referencia) for i in d.afirmaciones)
            if d.referencias != refs:
                raise ValueError("traza_diagnostica_inconsistente")

    @property
    def requisitos_documentales_satisfechos(self) -> bool:
        return not any(d.bloqueante for d in self.diagnosticos)

    def __bool__(self):
        raise TypeError("diagnostico_documental_no_es_permiso_booleano")


_BASE = (A.APLICABILIDAD_PRODUCTO, A.CORROBORACION)
_REQUISITOS = {
    OperacionUso.CONVERSION_TEMPORAL: _BASE + (A.CONVENCION_TEMPORAL, A.VALIDACION_CIENTIFICA),
    OperacionUso.ASIGNACION_ESPACIAL: _BASE + (A.IDENTIDAD_ESPACIAL, A.REFERENCIA_ESPACIAL, A.VALIDACION_CIENTIFICA),
    OperacionUso.INTERPRETACION_VARIABLE: _BASE + (A.SIGNIFICADO_VARIABLE, A.UNIDAD, A.VALIDACION_CIENTIFICA),
    OperacionUso.EQUIVALENCIA_EDITORIAL: _BASE,
    OperacionUso.ACREDITACION_CALIDAD: _BASE + (A.VALIDACION_CIENTIFICA,),
    OperacionUso.REDISTRIBUCION: (A.APLICABILIDAD_PRODUCTO, A.DERECHOS),
}


def evaluar_uso(expediente: ExpedienteMetadatos, operacion: OperacionUso,
                seleccion: tuple[str, ...]) -> ResultadoUso:
    if type(expediente) is not ExpedienteMetadatos or type(operacion) is not OperacionUso:
        raise TypeError("expediente_y_operacion_tipificados_requeridos")
    _tupla(seleccion, str, 256)
    mapa = {a.identificador: a for a in expediente.afirmaciones}
    if not seleccion or len(set(seleccion)) != len(seleccion) or not set(seleccion) <= mapa.keys():
        raise ValueError("seleccion_documental_vacia_repetida_o_ajena")
    seleccion = tuple(sorted(seleccion))
    consulta = operacion is OperacionUso.CONSULTA_DOCUMENTAL
    hallazgos = set()

    def agregar(codigo, ids, bloqueante=True):
        ids = tuple(sorted(ids))
        # Traza incluye ID, hash y localizador; nunca el texto ni credenciales.
        refs = tuple(mapa[i].fuente.identificador + "@" + mapa[i].fuente.sha256 + "#" + localizar(mapa[i].referencia) for i in ids)
        hallazgos.add(DiagnosticoUso(codigo, ids, refs, bloqueante))

    for i in seleccion:
        a = mapa[i]
        for nombre in ("integridad", "inspeccion"):
            if not _verificado(getattr(a.fuente, nombre)):
                agregar(nombre + "_no_acreditada", (i,))
        if a.presencia is P.AUSENTE:
            agregar("informacion_ausente", (i,))
        if a.evidencia.nivel.value == "contradictoria":
            agregar("evidencia_contradictoria", (i,))
        if a.evidencia.nivel.value == "inferida":
            agregar("afirmacion_inferida", (i,), not consulta)
        if a.evidencia.vigencia.value != "vigente_segun_evidencia_aportada":
            agregar("vigencia_no_acreditada", (i,), not consulta)
        for r in a.restricciones:
            agregar("restriccion." + r.value, (i,), not consulta)
        if consulta:
            continue
        if a.presencia is P.NULO_DECLARADO:
            agregar("nulo_declarado_no_es_valor_cientifico", (i,))
        if not _verificado(a.fuente.autenticidad):
            agregar("identidad_institucional_no_acreditada", (i,))
        if (a.fuente.referencia.version_documento is None or a.fuente.version_producto is None
                or not _verificado(a.fuente.correspondencia_editorial)):
            agregar("edicion_o_correspondencia_no_acreditada", (i,))
        aspectos = {c.aspecto: c.respaldo for c in a.constataciones}
        for aspecto in _REQUISITOS[operacion]:
            respaldo = aspectos.get(aspecto)
            if not _verificado(respaldo):
                agregar("falta." + aspecto.value, (i,))
        if operacion is OperacionUso.INTERPRETACION_VARIABLE and a.unidad_declarada is None:
            agregar("unidad_declarada_ausente", (i,))

    for r in expediente.relaciones:
        if not set((r.primera, r.segunda)).intersection(seleccion):
            continue
        if r.tipo is T.CONTRADICCION:
            agregar("contradiccion_entre_afirmaciones", (r.primera, r.segunda))
        if not consulta and r.tipo is T.CORRESPONDENCIA_NO_DEMOSTRADA:
            agregar("relacion_sin_correspondencia_demostrada", (r.primera, r.segunda))

    if operacion is OperacionUso.EQUIVALENCIA_EDITORIAL:
        fuentes = [mapa[i].fuente for i in seleccion]
        if len({f.identificador for f in fuentes}) < 2:
            agregar("equivalencia_requiere_documentos_distintos", seleccion)
        if len({(f.producto, f.version_producto) for f in fuentes}) != 1 or fuentes[0].producto is None:
            agregar("productos_o_ediciones_no_correspondientes", seleccion)
        pares = {frozenset((r.primera, r.segunda)) for r in expediente.relaciones if r.tipo is T.COINCIDENCIA}
        if any(frozenset((a, b)) not in pares for j, a in enumerate(seleccion) for b in seleccion[j+1:]):
            agregar("equivalencia_sin_comparacion_explicita", seleccion)

    agregar("experimental_sin_autorizacion_operativa", seleccion, False)
    agregar("clasificaciones_aportadas_no_autenticadas_por_el_nucleo", seleccion, False)
    diagnosticos = tuple(sorted(hallazgos, key=lambda h: (h.codigo, h.afirmaciones, h.referencias, h.bloqueante)))
    return ResultadoUso(expediente, operacion, seleccion, diagnosticos)
