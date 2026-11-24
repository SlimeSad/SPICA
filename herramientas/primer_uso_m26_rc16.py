"""Recepción acotada del informe RC15 completo, sin acreditar un uso real.

Composición efímera de contratos existentes: no almacén, permisos, revisión
humana automática o segundo evaluador documental. Solo fixtures cooperativas.
"""

from dataclasses import dataclass, field

from herramientas import vinculo_documental_rc15 as rc15
from herramientas.vinculacion_documental import CotejadorDocumental, ResultadoVinculacion
from spica.calidad.aplicabilidad.modelos import ExpedienteProducto
from spica.coordinacion import RestriccionPropagada
from spica.interoperabilidad.adaptadores import DiagnosticoAdaptacion as D, NivelDiagnostico as N
from spica.interoperabilidad.modelos import EstadoAptitud as E
from spica.metadatos_documentales import ResultadoUso

VERSION_RC16 = "0.1.0"
_FLAGS = ("autenticidad_institucional", "validacion_cientifica", "ejecucion_autorizada",
          "producto_leido", "operacion_ejecutada")


def _informe(valor):
    if type(valor) is not rc15.InformeVinculoRC15:
        raise TypeError("informe_completo_rc15_requerido_no_expediente_aislado")
    for v, t in ((valor.solicitud, rc15.SolicitudVinculoRC15),
                 (valor.revision, rc15.RevisionVinculoRC15),
                 (valor.uso_documental, ResultadoUso), (valor.cotejo, ResultadoVinculacion),
                 (valor.expediente_producto, ExpedienteProducto)):
        if type(v) is not t and not (v is None and t is not rc15.SolicitudVinculoRC15):
            raise TypeError("contenido_nativo_del_informe_rc15_requerido")
    for grupo, tipo in ((valor.restricciones, RestriccionPropagada), (valor.diagnosticos, D)):
        if type(grupo) is not tuple or any(type(v) is not tipo for v in grupo):
            raise TypeError("traza_completa_tipificada_rc15_requerida")


@dataclass(frozen=True, slots=True)
class ComprobacionPrimerUsoM26:
    """Referencias completas al antecedente y al nuevo contraste, sin extraer DTO."""
    solicitud_esperada: rc15.SolicitudVinculoRC15 = field(repr=False)
    aportado: rc15.InformeVinculoRC15 = field(repr=False)
    actual: rc15.InformeVinculoRC15 | None = field(repr=False)
    diagnosticos: tuple[D, ...] = field(repr=False)
    version: str = field(default=VERSION_RC16, init=False)
    uso_documental_acreditado: bool = field(default=False, init=False)
    revision_humana_acreditada: bool = field(default=False, init=False)
    autenticidad_institucional: bool = field(default=False, init=False)
    validacion_cientifica: bool = field(default=False, init=False)
    ejecucion_autorizada: bool = field(default=False, init=False)

    def __post_init__(self):
        if type(self.solicitud_esperada) is not rc15.SolicitudVinculoRC15:
            raise TypeError("solicitud_esperada_rc15_requerida")
        _informe(self.aportado)
        if self.actual is not None:
            _informe(self.actual)
        if (type(self.diagnosticos) is not tuple or len(self.diagnosticos) > 64
                or any(type(d) is not D for d in self.diagnosticos)):
            raise TypeError("diagnosticos_rc16_tipificados_requeridos")

    @property
    def diagnosticos_completos(self):
        return (self.aportado.diagnosticos + self.diagnosticos
                + (() if self.actual is None else self.actual.diagnosticos))

    @property
    def restricciones(self):
        # Conserva ambos conjuntos y orígenes, incluso si difieren. Repetición
        # entre lecturas no es evidencia independiente; ningún bloqueo se rebaja.
        return self.aportado.restricciones + (() if self.actual is None else self.actual.restricciones)

    @property
    def estado_coherencia(self):
        niveles = {d.nivel for d in self.diagnosticos_completos}
        if N.CONTRADICCION in niveles:
            return E.INCOMPATIBLE
        if N.FALTANTE in niveles or self.actual is None:
            return E.PENDIENTE_DE_EVIDENCIA
        return E.APTO_ESTRUCTURALMENTE

    @property
    def estado_uso(self):
        # RC15 solo admite fixtures. Ninguna lectura legitima su revisión
        # humana ni demuestra un uso institucional real; no hay vía de permiso.
        return E.INCOMPATIBLE if self.estado_coherencia is E.INCOMPATIBLE else E.PENDIENTE_DE_EVIDENCIA

    def __bool__(self):
        raise TypeError("comprobacion_rc16_no_es_permiso_ni_acreditacion")

    def diagnostico_publico(self):
        return dict(version=self.version, coherencia=self.estado_coherencia.value,
                    uso=self.estado_uso.value, numero_diagnosticos=len(self.diagnosticos_completos),
                    uso_documental_acreditado=False, revision_humana_acreditada=False,
                    autenticidad_institucional=False, validacion_cientifica=False,
                    ejecucion_autorizada=False)


def comprobar_primer_uso_m26(informe: rc15.InformeVinculoRC15, *,
                            solicitud_esperada: rc15.SolicitudVinculoRC15,
                            cotejador: CotejadorDocumental) -> ComprobacionPrimerUsoM26:
    """Exige informe completo, preserva el antecedente y vuelve a llamar a RC15.

    No acepta un expediente aislado ni convierte un informe antiguo pendiente
    en favorable. El resultado completo, no una proyección, es la entrega.
    """
    _informe(informe)
    if type(solicitud_esperada) is not rc15.SolicitudVinculoRC15 or type(cotejador) is not CotejadorDocumental:
        raise TypeError("solicitud_y_cotejador_nativos_requeridos_rc16")
    ds, actual = [], None

    def agregar(codigo, nivel=N.CONTRADICCION):
        ds.append(D(codigo, "primer_uso_m26_rc16", nivel))

    if informe.solicitud != solicitud_esperada:
        agregar("informe_de_otro_snapshot_para_el_uso")
    if informe.version != rc15.VERSION_RC15:
        agregar("version_informe_rc15_no_admitida")
    if any(getattr(informe, nombre) is not False for nombre in _FLAGS):
        agregar("garantias_ajenas_al_contrato_rc15")
    if not ds:
        actual = rc15.vincular_producto_rc15(solicitud_esperada, revision=informe.revision,
                                          cotejador=cotejador)
        if informe.restricciones != actual.restricciones:
            agregar("restricciones_aportadas_no_corresponden_al_recalculo")
        if informe.uso_documental != actual.uso_documental:
            agregar("diagnostico_documental_aportado_no_corresponde")
        if informe.estado is E.APTO_ESTRUCTURALMENTE and actual.estado is E.APTO_ESTRUCTURALMENTE:
            if any(d not in informe.diagnosticos for d in actual.diagnosticos):
                agregar("diagnosticos_nativos_omitidos_del_informe_aportado")
            if informe.expediente_producto != actual.expediente_producto:
                agregar("expediente_aportado_no_corresponde_al_recalculo")
            if informe.cotejo is None or informe.cotejo != actual.cotejo:
                agregar("cotejo_aportado_no_reproducido_en_lectura_actual", N.FALTANTE)
    agregar("revision_legitima_y_uso_real_no_acreditados_por_fixtures", N.INFORMACION)
    return ComprobacionPrimerUsoM26(solicitud_esperada, informe, actual, tuple(ds))
