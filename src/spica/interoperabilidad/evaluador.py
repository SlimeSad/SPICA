"""Preparación documental para una futura alineación, sin ejecutar asociaciones."""

from datetime import date, datetime, timedelta
from dataclasses import fields, is_dataclass

from ..adquisicion.catalogo.modelos import EstadoVerificacion as V
from ..adquisicion.nucleo.temporal import instante_utc
from .modelos import (
    AmbitoCRS as A, DimensionEvaluacion as D, EstadoAptitud as E,
    RepresentacionEspacial as R, RecursoInteroperable, ResultadoAptitud,
)


class _Revision:
    def __init__(self):
        self.evidencias, self.faltantes, self.contradicciones = [], [], []
        self.no_evaluables, self.incompatibles = [], []

    def evidencia(self, p):
        if p is not None and p not in self.evidencias:
            self.evidencias.append(p)

    def exigir(self, condicion, codigo):
        if not condicion and codigo not in self.faltantes:
            self.faltantes.append(codigo)
        return bool(condicion)

    def respaldo(self, r, codigo):
        self.evidencia(r.procedencia)
        return self.exigir(r.estado is V.VERIFICADO, codigo + ".verificacion")

    def crs(self, c, codigo):
        if not self.exigir(c is not None and c.declaracion is not None, codigo + ".declaracion"):
            return False
        controles = (self.respaldo(c.respaldo, codigo),
                     self.exigir(c.definicion is not None, codigo + ".definicion"),
                     self.exigir(len(c.unidades_ejes) == 2, codigo + ".unidades_ejes"))
        return all(controles)


def _espacial(recursos, revision):
    crs_listos = []
    for i, recurso in enumerate(recursos):
        m, etiqueta = recurso.espacial, f"r{i}.espacial"
        if m is None:
            revision.no_evaluables.append(etiqueta + ".marco_ausente")
            crs_listos.append(None)
            continue
        # Registrar referencias disponibles no equivale a aceptar su afirmación.
        for r in (m.respaldo_geometria, m.respaldo_coordenadas, m.respaldo_extension,
                  m.respaldo_cobertura, m.respaldo_calidad, m.respaldo_identidad):
            revision.evidencia(r.procedencia)
        for c in m.crs:
            revision.evidencia(c.respaldo.procedencia)
        if m.representacion is R.RASTER:
            revision.no_evaluables.append(etiqueta + ".raster_fuera_del_subconjunto")
        revision.exigir(m.representacion is not R.DESCONOCIDA, etiqueta + ".representacion")
        if m.coordenadas is not None:
            revision.respaldo(m.respaldo_coordenadas, etiqueta + ".coordenadas")
        if m.representacion is R.PUNTUAL:
            revision.exigir(m.coordenadas is not None, etiqueta + ".coordenadas")
        elif m.representacion is R.VECTORIAL:
            if revision.exigir(m.geometria_declarada is not None, etiqueta + ".geometria_declarada"):
                revision.respaldo(m.respaldo_geometria, etiqueta + ".geometria_declarada")
            revision.exigir(m.extension is not None, etiqueta + ".extension")
        crs = {c.ambito: c for c in m.crs}
        geometria = crs.get(A.GEOMETRIA)
        crs_listos.append(geometria if revision.crs(geometria, etiqueta + ".crs_geometria") else None)
        if m.extension is not None:
            revision.respaldo(m.respaldo_extension, etiqueta + ".extension")
            revision.crs(crs.get(A.EXTENSION), etiqueta + ".crs_extension")
        # Un CRS de extensión distinto del de geometría no es una contradicción.
        if m.identidad_ambigua:
            revision.exigir(False, etiqueta + ".identidad_ubicacion_ambigua")
            if m.respaldo_identidad.estado is V.VERIFICADO:
                revision.contradicciones.append(etiqueta + ".identidad_verificada_y_ambigua")
        if m.identificador_ubicacion is not None:
            revision.respaldo(m.respaldo_identidad, etiqueta + ".identidad_ubicacion")
        if revision.exigir(m.cobertura_observada is not None, etiqueta + ".cobertura_observada"):
            revision.respaldo(m.respaldo_cobertura, etiqueta + ".cobertura_observada")
        revision.exigir(m.precision_declarada is not None, etiqueta + ".precision_documentada")
        revision.exigir(m.incertidumbre is not None, etiqueta + ".incertidumbre_documentada")
        revision.respaldo(m.respaldo_calidad, etiqueta + ".calidad_posicional")
    a, b = crs_listos
    if a is not None and b is not None:
        if a.declaracion != b.declaracion:
            revision.exigir(False, "espacial.correspondencia_crs_no_documentada")
        elif a.unidades_ejes != b.unidades_ejes:
            revision.contradicciones.append("espacial.unidades_incompatibles_para_crs_identico")


def _clave(t):
    return instante_utc(t) if type(t) is datetime and t.utcoffset() is not None else t


def _instantanea(v):
    # La igualdad datetime de Python ignora fold con tzinfo compartido. No usarla
    # para declarar idénticas dos revisiones con horas originales diferentes.
    if type(v) is datetime:
        return (v.isoformat(), v.fold, getattr(v.tzinfo, "key", None))
    if is_dataclass(v):
        return (type(v), tuple(_instantanea(getattr(v, f.name)) for f in fields(v)))
    if type(v) is tuple:
        return tuple(_instantanea(x) for x in v)
    return v


def _clase(t):
    if type(t) is date:
        return "civil_date"
    return "instante" if t.utcoffset() is not None else "datetime_sin_zona"


def _temporal(recursos, revision):
    listos = []
    for i, recurso in enumerate(recursos):
        m, etiqueta = recurso.temporal, f"r{i}.temporal"
        if m is None:
            revision.no_evaluables.append(etiqueta + ".marco_ausente")
            listos.append(False)
            continue
        controles = [revision.respaldo(m.respaldo_interpretacion, etiqueta + ".interpretacion")]
        for p in (m.observaciones, m.publicacion, m.vigencia_metadatos):
            if p is not None:
                revision.evidencia(p.respaldo.procedencia)
        for nombre in ("resolucion", "zona_horaria_declarada", "convencion", "incertidumbre"):
            controles.append(revision.exigir(getattr(m, nombre) is not None, etiqueta + "." + nombre))
        p = m.observaciones  # Publicación/adquisición/vigencia jamás se usan como sustitutos.
        if not revision.exigir(p is not None, etiqueta + ".periodo_observaciones"):
            listos.append(False)
            continue
        controles.append(revision.respaldo(p.respaldo, etiqueta + ".periodo_observaciones"))
        controles.append(revision.exigir(p.limites_inclusivos is not None, etiqueta + ".limites_inclusivos"))
        clase = _clase(p.inicio)
        controles.append(revision.exigir(clase != "datetime_sin_zona", etiqueta + ".instantes_sin_zona_resuelta"))
        if clase == "instante" and m.zona_horaria_declarada is not None:
            for extremo in (p.inicio, p.fin):
                if m.zona_horaria_declarada == "UTC" and extremo.utcoffset() != timedelta(0):
                    revision.contradicciones.append(etiqueta + ".utc_contradice_desplazamiento")
                    controles.append(False)
                else:
                    nombres = (extremo.tzname(), getattr(extremo.tzinfo, "key", None))
                    controles.append(revision.exigir(m.zona_horaria_declarada in nombres,
                                                      etiqueta + ".zona_declarada_no_vinculada_al_datetime"))
        f = m.fecha_observacion
        if f is not None:
            if _clase(f) != clase:
                controles.append(revision.exigir(False, etiqueta + ".fecha_y_periodo_de_distinta_representacion"))
            else:
                t, inicio, fin = _clave(f), _clave(p.inicio), _clave(p.fin)
                fuera = t < inicio or t > fin
                if p.limites_inclusivos is not None:
                    fuera |= t == inicio and not p.limites_inclusivos[0] or t == fin and not p.limites_inclusivos[1]
                if fuera:
                    revision.contradicciones.append(etiqueta + ".fecha_fuera_del_periodo_declarado")
        listos.append(all(controles))
    if not all(listos):
        return
    a, b = (r.temporal for r in recursos)
    compatibles = True
    for nombre in ("convencion", "resolucion"):
        compatibles &= revision.exigir(getattr(a, nombre) == getattr(b, nombre), "temporal.correspondencia_" + nombre)
    pa, pb = a.observaciones, b.observaciones
    ca, cb = _clase(pa.inicio), _clase(pb.inicio)
    compatibles &= revision.exigir(ca == cb, "temporal.representaciones_no_alineadas")
    if ca == cb == "civil_date":
        compatibles &= revision.exigir(a.zona_horaria_declarada == b.zona_horaria_declarada,
                                       "temporal.correspondencia_zonas_civiles")
    if not compatibles:
        return
    if ca == "civil_date":
        # Fechas civiles discretas, sin convertirlas a horas o asumir una zona.
        ai = pa.inicio.toordinal() + (not pa.limites_inclusivos[0])
        af = pa.fin.toordinal() - (not pa.limites_inclusivos[1])
        bi = pb.inicio.toordinal() + (not pb.limites_inclusivos[0])
        bf = pb.fin.toordinal() - (not pb.limites_inclusivos[1])
        separados = af < bi or bf < ai
    else:
        ai, af, bi, bf = map(_clave, (pa.inicio, pa.fin, pb.inicio, pb.fin))
        separados = (af < bi or bf < ai
            or af == bi and not (pa.limites_inclusivos[1] and pb.limites_inclusivos[0])
            or bf == ai and not (pb.limites_inclusivos[1] and pa.limites_inclusivos[0]))
    if separados:
        revision.incompatibles.append("temporal.periodos_sin_soporte_comun_para_alineacion")


def evaluar_aptitud(primero: RecursoInteroperable, segundo: RecursoInteroperable,
                    dimension: D = D.AMBAS) -> ResultadoAptitud:
    """Función pura: no autoriza uso, no consulta fuentes y no evalúa coincidencia GIS."""
    if type(primero) is not RecursoInteroperable or type(segundo) is not RecursoInteroperable or type(dimension) is not D:
        raise TypeError("dos_recursos_y_dimension_tipificados_requeridos")
    recursos = (primero, segundo)
    revision = _Revision()
    for i, r in enumerate(recursos):
        revision.evidencia(r.procedencia)
        for p in r.correspondencias:
            revision.evidencia(p)
        revision.exigir(r.identidad.producto_id is not None, f"r{i}.producto_id")
        revision.exigir(r.procedencia is not None and r.procedencia.evidencia is not None, f"r{i}.procedencia_con_evidencia")
        for j, _ in enumerate(r.contradicciones_declaradas):
            revision.contradicciones.append(f"r{i}.contradiccion_declarada_{j}")
    if (primero.identidad == segundo.identidad and primero.revision_metadatos == segundo.revision_metadatos
            and _instantanea(primero) != _instantanea(segundo)):
        revision.contradicciones.append("misma_identidad_revision_con_instantaneas_distintas")
    if dimension in (D.ESPACIAL, D.AMBAS):
        _espacial(recursos, revision)
    if dimension in (D.TEMPORAL, D.AMBAS):
        _temporal(recursos, revision)
    if revision.contradicciones or revision.incompatibles:
        estado = E.INCOMPATIBLE
        motivos = revision.contradicciones + revision.incompatibles
    elif revision.no_evaluables:
        estado, motivos = E.NO_EVALUABLE, revision.no_evaluables
    elif revision.faltantes:
        estado, motivos = E.PENDIENTE_DE_EVIDENCIA, ["evidencia_insuficiente_para_preparacion"]
    else:
        estado, motivos = E.APTO_ESTRUCTURALMENTE, ["metadatos_compatibles_para_preparacion_sin_asociacion"]
    motivos = motivos + revision.no_evaluables + revision.incompatibles
    return ResultadoAptitud(recursos, dimension, estado, tuple(revision.evidencias),
        tuple(dict.fromkeys(motivos)), tuple(revision.faltantes), tuple(dict.fromkeys(revision.contradicciones)))
