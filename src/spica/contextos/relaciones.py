"""Cotejos de un inventario explícito en memoria, sin registro global o ejecución."""

from dataclasses import replace

from ..interoperabilidad.adaptadores import DiagnosticoAdaptacion, NivelDiagnostico
from .modelos import (
    ContextoProyecto, ContextoEntrada, ContextoOperacion, EstadoOperacion, _tupla,
)


def validar_relaciones(proyectos: tuple[ContextoProyecto, ...],
                       entradas: tuple[ContextoEntrada, ...],
                       operaciones: tuple[ContextoOperacion, ...]) -> tuple[DiagnosticoAdaptacion, ...]:
    """Detecta ausencias, IDs repetidos y snapshots incompatibles; no autentica.

    Los IDs de entrada/operación se circunscriben a contexto_id. Un mismo proyecto
    MD puede tener varios contextos; la descripción MD debe coincidir. No fusiona
    contenido ni asigna autoridad por coincidencia de SHA, ruta o identidad.
    """
    _tupla(proyectos, ContextoProyecto, 128)
    _tupla(entradas, ContextoEntrada, 256)
    _tupla(operaciones, ContextoOperacion, 256)
    problemas = []

    def problema(codigo, campo):
        d = DiagnosticoAdaptacion(codigo, campo, NivelDiagnostico.CONTRADICCION)
        if d not in problemas:
            problemas.append(d)

    ps, md, es, os = {}, {}, {}, {}
    for p in proyectos:
        if p.contexto_id in ps:
            problema("contexto_id_duplicado", "proyecto")
        ps[p.contexto_id] = p
        if p.project_id in md and md[p.project_id] != p.proyecto:
            problema("identidad_proyecto_con_descripciones_distintas", "proyecto")
        md[p.project_id] = p.proyecto
    objetos, activos = {}, {}
    for e in entradas:
        clave = e.proyecto.contexto_id, e.entrada_id
        if clave in es:
            problema("entrada_id_duplicada", "entrada")
        es[clave] = e
        if ps.get(e.proyecto.contexto_id) != e.proyecto:
            problema("contexto_proyecto_ausente_o_incompatible", "entrada")
        # MD-02: object_id es único en el catálogo RAW, no por proyecto.
        objeto = e.objeto.object_id
        if objeto in objetos and objetos[objeto] != e.objeto:
            problema("identidad_objeto_con_descripciones_distintas", "entrada")
        objetos[objeto] = e.objeto
        if e.asset_id is not None:
            propietario = e.proyecto.project_id, objeto
            if e.asset_id in activos and activos[e.asset_id] != propietario:
                problema("activo_referenciado_desde_objetos_distintos", "entrada")
            activos[e.asset_id] = propietario
    for o in operaciones:
        clave = o.proyecto.contexto_id, o.operacion_id
        if clave in os:
            problema("operacion_id_duplicada", "operacion")
        os[clave] = o
        if ps.get(o.proyecto.contexto_id) != o.proyecto:
            problema("contexto_proyecto_ausente_o_incompatible", "operacion")
        for e in o.entradas:
            if es.get((o.proyecto.contexto_id, e.entrada_id)) != e:
                problema("entrada_ausente_o_revision_incompatible", "operacion")
    return tuple(problemas)


def cambiar_estado(operacion: ContextoOperacion, estado: EstadoOperacion, *,
                    diagnosticos: tuple[DiagnosticoAdaptacion, ...] = (),
                    referencias_resultado: tuple[str, ...] = ()) -> ContextoOperacion:
    """Nueva declaración inmutable. No inicia/termina un motor ni acredita ejecución.

    Los estados terminales no reabren; una repetición requiere otra operacion_id.
    El llamador es responsable de aportar evidencia y conservar su historial.
    """
    if type(operacion) is not ContextoOperacion or type(estado) is not EstadoOperacion:
        raise TypeError("operacion_y_estado_tipados_requeridos")
    e = EstadoOperacion
    permitidos = {
        e.DECLARADA: (e.PLANIFICADA, e.CANCELADA),
        e.PLANIFICADA: (e.INICIADA, e.CANCELADA),
        e.INICIADA: (e.CONCLUIDA, e.PARCIAL, e.FALLIDA, e.CANCELADA),
    }
    if estado not in permitidos.get(operacion.estado, ()):
        raise ValueError("transicion_contextual_no_admitida")
    return replace(operacion, estado=estado, diagnosticos=diagnosticos,
                   referencias_resultado=referencias_resultado)
