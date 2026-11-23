"""Puente de checkout C20 -> C24: identidad PNDA para revisión documental.

No aprueba aplicabilidad científica. La revisión es un antecedente aportado por
un responsable cooperativo, no una firma. Solo el cotejador existente abre el
documento controlado; nunca se abre el producto descrito ni un almacén.
"""

from dataclasses import dataclass, field

from herramientas.vinculacion_documental import (
    CotejadorDocumental, Comprobacion as C, EstadoCotejo, ResultadoVinculacion,
)
from spica.adquisicion.catalogo.modelos import ProductoCatalogo, ProcedenciaCatalogo
from spica.adquisicion.conectores.senamhi.modelos import (
    FUENTE_SENAMHI, PRODUCTO_GBON_RBON_ID,
)
from spica.artefactos.modelos import DescriptorArtefacto, EstadoArtefacto
from spica.artefactos.modelos import _unir_origenes
from spica.calidad.aplicabilidad.modelos import (
    AfirmacionAplicabilidad, ExpedienteProducto, NaturalezaEvidencia,
    NivelEvidencia, VigenciaDocumento,
)
from spica.calidad.modelos_cientificos import DimensionAplicabilidad
from spica.calidad.restricciones import TipoRestriccionQA
from spica.contextos import ContextoOperacion, EstadoOperacion, TipoOperacion
from spica.coordinacion import RestriccionPropagada
from spica.interoperabilidad.adaptadores import DiagnosticoAdaptacion as D, NivelDiagnostico as N
from spica.interoperabilidad.modelos import EstadoAptitud as E
from spica.metadatos_documentales import (
    ExpedienteMetadatos, FormaDeclaracion, OperacionUso, PresenciaInformacion,
    ResultadoUso, TipoDocumento, evaluar_uso,
)

VERSION_RC15 = "0.1.0"
FINALIDAD_RC15 = "revision_documental_identidad_producto_pnda"


def _texto(valor):
    if (type(valor) is not str or not valor.strip() or len(valor) > 512
            or any(ord(c) < 32 for c in valor)):
        raise ValueError("literal_rc15_requerido_y_acotado")


@dataclass(frozen=True, slots=True)
class SolicitudVinculoRC15:
    producto: ProductoCatalogo = field(repr=False)
    artefacto: DescriptorArtefacto = field(repr=False)
    operacion: ContextoOperacion = field(repr=False)
    expediente: ExpedienteMetadatos | None = field(repr=False)
    afirmacion_id: str
    control_id: str
    finalidad: str = FINALIDAD_RC15
    version_contrato: str = VERSION_RC15

    def __post_init__(self):
        for valor, tipo in ((self.producto, ProductoCatalogo),
                            (self.artefacto, DescriptorArtefacto),
                            (self.operacion, ContextoOperacion)):
            if type(valor) is not tipo:
                raise TypeError("contratos_nativos_rc15_requeridos")
        if self.expediente is not None and type(self.expediente) is not ExpedienteMetadatos:
            raise TypeError("expediente_documental_rc15_requerido")
        for valor in (self.afirmacion_id, self.control_id, self.finalidad, self.version_contrato):
            _texto(valor)


@dataclass(frozen=True, slots=True)
class RevisionVinculoRC15:
    """Revisión explícita del snapshot completo, aportada; no aprobación científica."""
    solicitud: SolicitudVinculoRC15 = field(repr=False)
    responsable_ref: str = field(repr=False)
    procedencia: ProcedenciaCatalogo = field(repr=False)

    def __post_init__(self):
        if type(self.solicitud) is not SolicitudVinculoRC15 or type(self.procedencia) is not ProcedenciaCatalogo:
            raise TypeError("revision_y_procedencia_rc15_requeridas")
        _texto(self.responsable_ref)
        if self.procedencia.evidencia is None:
            raise ValueError("antecedente_revision_rc15_requerido")


@dataclass(frozen=True, slots=True)
class InformeVinculoRC15:
    solicitud: SolicitudVinculoRC15 = field(repr=False)
    revision: RevisionVinculoRC15 | None = field(repr=False)
    uso_documental: ResultadoUso | None = field(repr=False)
    cotejo: ResultadoVinculacion | None = field(repr=False)
    expediente_producto: ExpedienteProducto | None = field(repr=False)
    restricciones: tuple[RestriccionPropagada, ...] = field(repr=False)
    diagnosticos: tuple[D, ...] = field(repr=False)
    version: str = field(default=VERSION_RC15, init=False)
    autenticidad_institucional: bool = field(default=False, init=False)
    validacion_cientifica: bool = field(default=False, init=False)
    ejecucion_autorizada: bool = field(default=False, init=False)
    producto_leido: bool = field(default=False, init=False)
    operacion_ejecutada: bool = field(default=False, init=False)

    @property
    def estado(self):
        niveles = {d.nivel for d in self.diagnosticos}
        if N.CONTRADICCION in niveles:
            return E.INCOMPATIBLE
        if N.FALTANTE in niveles:
            return E.PENDIENTE_DE_EVIDENCIA
        return E.APTO_ESTRUCTURALMENTE

    def __bool__(self):
        raise TypeError("vinculo_documental_rc15_no_es_permiso")

    def diagnostico_publico(self):
        # Omite textos, identidades recibidas, responsables, referencias y rutas.
        return dict(estado=self.estado.value, version=self.version,
                    numero_diagnosticos=len(self.diagnosticos),
                    autenticidad_institucional=False, validacion_cientifica=False,
                    ejecucion_autorizada=False, producto_leido=False, operacion_ejecutada=False)


def vincular_producto_rc15(solicitud: SolicitudVinculoRC15, *,
                          revision: RevisionVinculoRC15 | None,
                          cotejador: CotejadorDocumental) -> InformeVinculoRC15:
    """Coteja de nuevo el documento y prepara solo PRODUCTO, nivel DECLARADA.

    Un dictamen previo/DTO de cotejo no sustituye al cotejador. La integridad
    comprobada pertenece al documento dentro de esa lectura, no al CSV PNDA.
    No autentica la revisión ni escribe el expediente en un catálogo.
    """
    if type(solicitud) is not SolicitudVinculoRC15 or type(cotejador) is not CotejadorDocumental:
        raise TypeError("solicitud_y_cotejador_nativos_rc15_requeridos")
    if revision is not None and type(revision) is not RevisionVinculoRC15:
        raise TypeError("revision_rc15_tipificada_requerida")
    s = solicitud
    e = s.artefacto.entrada_perfil.entrada
    ds, uso, cotejo, salida = [], None, None, None
    rs = _unir_origenes(
        tuple(RestriccionPropagada(r, ("artefacto_rc15",)) for r in s.artefacto.restricciones),
        tuple(RestriccionPropagada(r, ("operacion_rc15",)) for r in s.operacion.restricciones))

    def agregar(codigo, nivel=N.CONTRADICCION):
        ds.append(D(codigo, "vinculo_documental_rc15", nivel))

    if s.version_contrato != VERSION_RC15 or s.finalidad != FINALIDAD_RC15:
        agregar("perfil_o_finalidad_rc15_no_admitidos")
    if (s.producto.fuente, s.producto.identificador) != (FUENTE_SENAMHI, PRODUCTO_GBON_RBON_ID):
        agregar("producto_fuera_del_perfil_pnda_rc15")
    recurso = e.recurso
    if recurso is None:
        agregar("recurso_producto_ausente", N.FALTANTE)
    elif (recurso.identidad.fuente, recurso.identidad.producto_id) != (
            s.producto.fuente, s.producto.identificador):
        agregar("identidad_producto_destino_contradictoria")
    versiones = (s.producto.version, e.version_contenido,
                 recurso.version_institucional if recurso is not None else None)
    if any(v is None for v in versiones):
        agregar("version_producto_desconocida", N.FALTANTE)
    elif len(set(versiones)) != 1:
        agregar("version_producto_destino_contradictoria")
    if s.operacion.proyecto != e.proyecto or not any(x is e for x in s.operacion.entradas):
        agregar("proyecto_o_entrada_no_canonicos")
    if s.operacion.tipo is not TipoOperacion.DESCRIPCION_ESTRUCTURAL or s.operacion.proposito != FINALIDAD_RC15:
        agregar("operacion_fuera_del_uso_documental")
    if s.operacion.estado not in (EstadoOperacion.DECLARADA, EstadoOperacion.PLANIFICADA):
        agregar("estado_operacion_no_admisible")
    if s.artefacto.estado_logico is EstadoArtefacto.PARCIAL:
        agregar("artefacto_parcial_no_admisible")
    if s.artefacto.contenido_id is None:
        agregar("identidad_contenido_ausente", N.FALTANTE)
    ds.extend(s.artefacto.diagnosticos + e.diagnosticos + s.operacion.diagnosticos)
    if any(r.restriccion.tipo is TipoRestriccionQA.BLOQUEO_USO_DEL_RESULTADO
           and FINALIDAD_RC15 in r.restriccion.operaciones for r in rs):
        agregar("restriccion_bloquea_finalidad_rc15")
    if revision is None:
        agregar("revision_explicita_ausente", N.FALTANTE)
    elif revision.solicitud != s:
        agregar("revision_de_otro_snapshot")
    if s.expediente is None:
        agregar("expediente_documental_ausente", N.FALTANTE)
    else:
        a = next((a for a in s.expediente.afirmaciones if a.identificador == s.afirmacion_id), None)
        if a is None:
            agregar("afirmacion_documental_ausente", N.FALTANTE)
        else:
            uso = evaluar_uso(s.expediente, OperacionUso.CONSULTA_DOCUMENTAL, (a.identificador,))
            if not uso.requisitos_documentales_satisfechos:
                agregar("requisitos_documentales_no_satisfechos", N.FALTANTE)
            if a.fuente.producto is None or a.fuente.version_producto is None:
                agregar("producto_o_edicion_documental_no_acreditados", N.FALTANTE)
            elif (a.fuente.producto != (recurso.identidad if recurso is not None else None)
                    or s.producto.version is not None and a.fuente.version_producto != s.producto.version):
                agregar("documento_de_otro_producto_recurso_o_edicion")
            if (a.concepto, a.ambito, a.presencia, a.forma, a.contenido) != (
                    "identificador_producto", FINALIDAD_RC15, PresenciaInformacion.CON_VALOR,
                    FormaDeclaracion.LITERAL, s.producto.identificador):
                agregar("afirmacion_no_describe_identidad_para_esta_finalidad")
            if a.fuente.tipo is not TipoDocumento.DOCX:
                agregar("tipo_documental_fuera_del_perfil_rc15")
            if a.evidencia.nivel not in (NivelEvidencia.DECLARADA, NivelEvidencia.VERIFICADA):
                agregar("nivel_documental_insuficiente", N.FALTANTE)
            if a.evidencia.vigencia is not VigenciaDocumento.VIGENTE or a.evidencia.pendientes:
                agregar("vigencia_o_revision_documental_pendiente", N.FALTANTE)
            if a.fuente.referencia.version_documento is None or a.fuente.referencia.fecha_documento is None:
                agregar("edicion_o_fecha_documental_desconocida", N.FALTANTE)
            if a.evidencia.naturaleza is not NaturalezaEvidencia.SINTETICA:
                agregar("piloto_rc15_solo_admite_evidencia_sintetica")
            if any(r.tipo.value == "contradiccion_declarada" and a.identificador in (r.primera, r.segunda)
                   for r in s.expediente.relaciones) or a.evidencia.contradicciones:
                agregar("contradiccion_documental_no_resuelta")
            if any(b.identificador != a.identificador and b.referencia == a.referencia for b in s.expediente.afirmaciones):
                agregar("relacion_documental_duplicada")
            controles = [c for c in cotejador.controles if c.identificador == s.control_id]
            if len(controles) != 1:
                agregar("control_documental_ausente", N.FALTANTE)
            elif controles[0].referencia != a.fuente.referencia or controles[0].tipo is not a.fuente.tipo:
                agregar("referencia_documental_distinta_del_control")
            if not any(d.nivel is not N.INFORMACION for d in ds):
                cotejo = cotejador.cotejar(s.control_id, s.expediente, (a.identificador,))
                if (any(v is not C.SATISFECHA for v in (cotejo.ruta, cotejo.comparacion_control,
                        cotejo.estructura, cotejo.conservacion)) or cotejo.diagnosticos
                        or len(cotejo.cotejos) != 1 or cotejo.cotejos[0].contenido is not EstadoCotejo.COINCIDE):
                    agregar("cotejo_fisico_literal_no_satisfactorio", N.FALTANTE)
                else:
                    afirmacion = AfirmacionAplicabilidad(DimensionAplicabilidad.PRODUCTO,
                        a.contenido, NivelEvidencia.DECLARADA, (a.fuente.identificador,),
                        incertidumbres=a.evidencia.incertidumbres,
                        pendientes=("revision_aportada_no_autenticada_ni_aprobacion_cientifica",
                                    "revisar_aplicabilidad_y_restricciones_con_el_informe_rc15"))
                    salida = ExpedienteProducto(s.producto, (a.evidencia,), (afirmacion,))
                    agregar("vinculo_producto_declarado_preparado_para_revision", N.INFORMACION)
    agregar("sin_autenticidad_permiso_validacion_cientifica_ni_lectura_del_producto", N.INFORMACION)
    return InformeVinculoRC15(s, revision, uso, cotejo, salida, rs,
                             tuple(dict.fromkeys(ds)))
