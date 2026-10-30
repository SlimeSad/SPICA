"""Registro secuencial en memoria, sin persistencia ni ejecución de Nivel 1."""

from .modelos_cientificos import (
    AmbitoReglaCientifica as A, ContextoCientifico, DimensionAplicabilidad as D,
    EstadoReglaCientifica as E, HabilitacionCientifica, ReglaCientifica,
    RevisionCientifica, RevisionReglaCientifica,
)


def _problemas_documentales(regla):
    problemas = []
    if not regla.referencias:
        problemas.append("referencias_ausentes")
    if any(r.version_documento is None or r.fecha_documento is None for r in regla.referencias):
        problemas.append("version_o_fecha_documental_desconocida")
    vistas = {}
    for ref in regla.referencias:
        firma = (ref.procedencia, ref.version_documento, ref.fecha_documento, ref.sha256_referencia)
        if ref.localizador in vistas and vistas[ref.localizador] != firma:
            problemas.append("referencias_contradictorias")
        vistas[ref.localizador] = firma
    if regla.contradicciones_documentales:
        problemas.append("contradicciones_documentales_pendientes")
    return problemas


def _problemas_aprobacion(regla, decision):
    problemas = _problemas_documentales(regla)
    if any(r.fecha_documento is not None and r.fecha_documento > decision.fecha_utc.date()
           for r in regla.referencias):
        problemas.append("documentacion_posterior_a_revision")
    if regla.procedencia_normativa is None:
        problemas.append("procedencia_normativa_desconocida")
    if {c.dimension for c in regla.aplicabilidad} != set(D):
        problemas.append("dimensiones_de_aplicabilidad_incompletas")
    if any(not c.referencias for c in regla.aplicabilidad):
        problemas.append("aplicabilidad_sin_referencia")
    condiciones = {c.dimension: c for c in regla.aplicabilidad}
    # El ámbito universal no exime de justificar cada dimensión.
    obligatorias = {A.INSTITUCIONAL: (D.INSTITUCION,), A.PRODUCTO: (D.INSTITUCION, D.PRODUCTO),
                    A.INSTRUMENTO: (D.INSTRUMENTO,), A.UNIVERSAL: ()}[regla.ambito]
    if any(d not in condiciones or condiciones[d].sin_restriccion for d in obligatorias):
        problemas.append("ambito_sin_restriccion_especifica")
    if regla.metodo is None or not regla.metodo.referencias:
        problemas.append("metodo_no_documentado")
    if regla.incertidumbre is None or not regla.incertidumbre.referencias:
        problemas.append("incertidumbre_no_documentada")
    if any(not p.referencias for p in regla.parametros):
        problemas.append("parametro_sin_referencia")
    if set(decision.referencias_revisadas) != {r.identificador for r in regla.referencias}:
        problemas.append("referencias_no_revisadas_o_ajenas")
    if not decision.aplicabilidad_demostrada:
        problemas.append("aplicabilidad_no_demostrada")
    if decision.contradicciones:
        problemas.append("revision_con_contradicciones")
    return problemas


class CatalogoReglasCientificas:
    """Cada (ID, versión) conserva revisiones inmutables. Instancia inicialmente vacía.

    No hay catálogo institucional precargado, conversión de unidades, descubrimiento
    de métodos ni aprobación automática. El control de revisión no sustituye locks.
    """

    def __init__(self):
        self._historial = {}

    def registrar(self, regla: ReglaCientifica) -> RevisionReglaCientifica:
        if not isinstance(regla, ReglaCientifica):
            raise TypeError("Descriptor científico requerido")
        clave = (regla.identificador, regla.version)
        if clave in self._historial:
            raise ValueError("ID y versión ya registrados; no se sobrescriben")
        versiones = [r[0].regla for k, r in self._historial.items() if k[0] == regla.identificador]
        if versiones:
            anterior = max(versiones, key=lambda r: tuple(map(int, r.version.split('.'))))
            if tuple(map(int, regla.version.split('.'))) <= tuple(map(int, anterior.version.split('.'))):
                raise ValueError("La nueva versión debe ser mayor")
            if regla.nombre != anterior.nombre or regla.ambito != anterior.ambito:
                raise ValueError("La identidad/ámbito cambió; utilizar otro ID")
        entrada = RevisionReglaCientifica(regla, 1, E.PROPUESTA)
        self._historial[clave] = [entrada]
        return entrada

    def obtener(self, identificador: str, version: str) -> RevisionReglaCientifica:
        return self._historial[identificador, version][-1]

    def historial(self, identificador: str, version: str) -> tuple[RevisionReglaCientifica, ...]:
        return tuple(self._historial[identificador, version])

    def listar(self) -> tuple[RevisionReglaCientifica, ...]:
        claves = sorted(self._historial, key=lambda k: (k[0], tuple(map(int, k[1].split('.')))))
        return tuple(self._historial[k][-1] for k in claves)

    def cambiar_estado(self, identificador: str, version: str, estado: E, *,
                       revision_esperada: int, decision: RevisionCientifica) -> RevisionReglaCientifica:
        actual = self.obtener(identificador, version)
        if not isinstance(estado, E) or not isinstance(decision, RevisionCientifica):
            raise TypeError("Estado y revisión científicos requeridos")
        if type(revision_esperada) is not int or revision_esperada != actual.revision:
            raise ValueError("Revisión desactualizada")
        permitidas = {E.PROPUESTA: (E.DOCUMENTADA, E.OBSOLETA),
                      E.DOCUMENTADA: (E.APROBADA, E.OBSOLETA),
                      E.APROBADA: (E.SUSPENDIDA, E.OBSOLETA),
                      E.SUSPENDIDA: (E.DOCUMENTADA, E.OBSOLETA), E.OBSOLETA: ()}
        if estado not in permitidas[actual.estado]:
            raise ValueError("Transición no admitida")
        if actual.decision is not None and decision.fecha_utc < actual.decision.fecha_utc:
            raise ValueError("La revisión no puede retroceder temporalmente")
        problemas = []
        if estado is E.DOCUMENTADA:
            problemas = _problemas_documentales(actual.regla)
            if any(r.fecha_documento is not None and r.fecha_documento > decision.fecha_utc.date()
                   for r in actual.regla.referencias):
                problemas.append("documentacion_posterior_a_revision")
            if set(decision.referencias_revisadas) != {r.identificador for r in actual.regla.referencias}:
                problemas.append("referencias_no_revisadas_o_ajenas")
            if decision.contradicciones:
                problemas.append("revision_con_contradicciones")
        elif estado is E.APROBADA:
            problemas = _problemas_aprobacion(actual.regla, decision)
        if problemas:
            # Solo códigos fijos, sin interpolar documentos, responsables ni valores.
            raise ValueError(";".join(dict.fromkeys(problemas)))
        nueva = RevisionReglaCientifica(actual.regla, actual.revision + 1, estado, decision)
        self._historial[identificador, version].append(nueva)
        return nueva

    def comprobar_habilitacion(self, identificador: str, version: str,
                              contexto: ContextoCientifico) -> HabilitacionCientifica:
        if not isinstance(contexto, ContextoCientifico):
            raise TypeError("Contexto científico requerido")
        actual = self.obtener(identificador, version)
        motivos = []
        if actual.estado is not E.APROBADA:
            motivos.append("regla_no_aprobada")
        else:
            motivos.extend(_problemas_aprobacion(actual.regla, actual.decision))
        datos = {d.dimension: d for d in contexto.datos}
        for condicion in actual.regla.aplicabilidad:
            if condicion.sin_restriccion:
                continue  # Requiere evidencia de esta ausencia de restricción al aprobar.
            dato = datos.get(condicion.dimension)
            if dato is None or dato.evidencia.version_documento is None or dato.evidencia.fecha_documento is None:
                motivos.append("contexto_no_demostrado:" + condicion.dimension.value)
            elif dato.valor not in condicion.valores_permitidos:
                motivos.append("contexto_incompatible:" + condicion.dimension.value)
        elegible = not motivos
        motivos.append("ejecucion_nivel1_no_implementada")
        return HabilitacionCientifica(actual, elegible, tuple(dict.fromkeys(motivos)))
