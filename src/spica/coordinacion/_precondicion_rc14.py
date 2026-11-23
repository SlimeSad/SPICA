"""Aporte privado y efímero de una única arista RC14; sin importar artefactos.

Solo la interfaz RC14 lo prepara después del cotejo RC13. No es una API de
plugins, permiso o autenticación frente a un proceso Python malicioso.
"""

from dataclasses import dataclass, field, fields, replace

from ..contextos import EstadoOperacion as S
from ..interoperabilidad.adaptadores import NivelDiagnostico as N
from .modelos import ComposicionOperaciones, DependenciaOperacion, RestriccionPropagada

_TESTIGO = object()


@dataclass(frozen=True, slots=True)
class _AporteExportacion:
    composicion: ComposicionOperaciones = field(repr=False)
    dependencia: DependenciaOperacion
    entrada_id: str
    artefacto: tuple[str, str]
    restricciones: tuple[RestriccionPropagada, ...] = field(repr=False)
    _testigo: tuple | None = field(default=None, init=False, repr=False, compare=False)

    def corresponde(self, c):
        t = self._testigo
        if not (type(t) is tuple and len(t) == 2 and t[0] is _TESTIGO and t[1] == _datos(self)):
            return False
        # RC7 puede reducir cotas, nunca ampliar el alcance de la composición.
        return (replace(c, limites=self.composicion.limites) == self.composicion
                and all(getattr(c.limites, f.name) <= getattr(self.composicion.limites, f.name)
                        for f in fields(c.limites)))


def _datos(a):
    return tuple(getattr(a, f.name) for f in fields(a) if f.name != "_testigo")


def _crear_aporte(c, d, entrada_id, artefacto, restricciones):
    a = _AporteExportacion(c, d, entrada_id, artefacto, restricciones)
    object.__setattr__(a, "_testigo", (_TESTIGO, _datos(a)))
    return a


def _admite_exportacion(aporte, c, d, previa):
    """Mismo predicado para RC3 y RC7, solo tras cotejo externo RC13 actual."""
    if (aporte is None or d != aporte.dependencia or not aporte.corresponde(c)
            or previa is None or previa.nodo.contexto.operacion_id != d.predecesora
            or previa.nodo.contexto.estado is not S.INICIADA
            or any(x.nivel is not N.INFORMACION for x in previa.nodo.contexto.diagnosticos)
            or any(r not in previa.nodo.contexto.referencias_resultado for r in d.referencias_resultado)):
        return False
    # Único faltante compensado: estado declarado propio, con cierre observado
    # aportado por RC8. Cualquier otro impedimento conserva el bloqueo.
    return all(x.nivel is N.INFORMACION or (
        x.nivel is N.FALTANTE and x.codigo == "estado_declarado_no_es_cierre_completo"
        and x.campo == d.predecesora) for x in previa.diagnosticos)


def _admite_entrada(aporte, c, vinculo):
    return (aporte is not None and vinculo.operacion_id == aporte.dependencia.dependiente
            and vinculo.entrada_id == aporte.entrada_id
            and (vinculo.artefacto.object_id, vinculo.artefacto.revision) == aporte.artefacto
            and aporte.corresponde(c))
