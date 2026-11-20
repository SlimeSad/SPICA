"""RC9: admisión específica del JSON QA nativo respaldado por captura RC8.

No despacha productores ni dependencias. Solo la comprobación RC5 opcional
relee archivos, en los entornos TEMP controlados que ya admite RC5.
"""

from dataclasses import dataclass, field, fields

from ..adquisicion.readquisicion.modelos import EstadoLocal
from ..calidad.consumo import (
    VERSION_CONSUMO_QA, EstadoConsumoQA, InformeConsumoQA, LimitesConsumoQA,
    consumir_exportaciones,
)
from ..calidad.restricciones import RestriccionQA, TipoRestriccionQA
from ..contextos import ContextoProyecto, EstadoOperacion
from ..contextos.modelos import _texto
from ..coordinacion import RestriccionPropagada
from ..coordinacion.inspeccion import _unicos
from ..coordinacion.modelos import estado_diagnosticos
from ..interoperabilidad.adaptadores import DiagnosticoAdaptacion as D, NivelDiagnostico as N
from ..interoperabilidad.modelos import EstadoAptitud as E
from . import ReferenciaArtefacto
from .coordinacion import _unir
from .cierre_exportacion import (
    EvidenciaExportacion, InformeCierreExportacion, SolicitudExportacionTecnica,
    inspeccionar_cierre_exportacion,
)
from .materializacion import (
    InformeMaterializacion, InformeVerificacion, ReferenciaFisica, SolicitudMaterializacion,
    verificar_fisicamente,
)

VERSION_ADMISION = "0.1.0"
CONSUMIDOR = "spica.calidad.consumo.consumir_exportaciones"
USO_CONSUMIR = "consumir_json_qa0_rc9"
_TESTIGO = object()


def _diag(codigo, nivel=N.CONTRADICCION):
    return D(codigo, "admision_exportacion_rc9", nivel)


@dataclass(frozen=True, slots=True)
class SolicitudAdmisionExportacion:
    contenido: bytes | str | None = field(repr=False)
    evidencia: EvidenciaExportacion | None = field(repr=False)
    proyecto: ContextoProyecto = field(repr=False)
    operacion_productora_id: str
    entrada_resultado_id: str
    artefacto: ReferenciaArtefacto
    contenido_id: str
    consumidor_id: str = CONSUMIDOR
    version_consumidor: str = VERSION_CONSUMO_QA
    finalidad: str = USO_CONSUMIR
    limites: LimitesConsumoQA = field(default_factory=LimitesConsumoQA)
    exigir_integridad_fisica: bool = False
    materializacion: InformeMaterializacion | None = field(default=None, repr=False)
    version_contrato: str = VERSION_ADMISION

    def __post_init__(self):
        if type(self.version_contrato) is not str or self.version_contrato != VERSION_ADMISION:
            raise ValueError("version_admision_rc9_no_admitida")
        if self.contenido is not None and type(self.contenido) not in (bytes, str):
            raise TypeError("documento_unico_bytes_texto_o_none_requerido")
        if self.evidencia is not None and type(self.evidencia) is not EvidenciaExportacion:
            raise TypeError("evidencia_rc8_o_none_requerida")
        if self.evidencia is not None and type(self.evidencia.solicitud) is not SolicitudExportacionTecnica:
            raise TypeError("solicitud_rc8_tipificada_requerida")
        if type(self.proyecto) is not ContextoProyecto or type(self.artefacto) is not ReferenciaArtefacto:
            raise TypeError("proyecto_rc1_y_referencia_rc4_requeridos")
        if type(self.limites) is not LimitesConsumoQA or type(self.exigir_integridad_fisica) is not bool:
            raise TypeError("limites_y_exigencia_fisica_tipificados_requeridos")
        if self.materializacion is not None and type(self.materializacion) is not InformeMaterializacion:
            raise TypeError("materializacion_rc5_o_none_requerida")
        self.proyecto.__post_init__()
        self.artefacto.__post_init__()
        self.limites.__post_init__()
        for v in (self.operacion_productora_id, self.entrada_resultado_id, self.artefacto.object_id,
                  self.contenido_id, self.consumidor_id, self.version_consumidor, self.finalidad):
            _texto(v, maximo=512)


@dataclass(frozen=True, slots=True)
class InformeAdmisionExportacion:
    solicitud: SolicitudAdmisionExportacion = field(repr=False)
    consumo: InformeConsumoQA | None = field(repr=False)
    cierre: InformeCierreExportacion | None = field(repr=False)
    verificacion_fisica: InformeVerificacion | None = field(repr=False)
    restricciones: tuple[RestriccionQA, ...]
    diagnosticos: tuple[D, ...]
    version_contrato: str = field(default=VERSION_ADMISION, init=False)
    autorizacion_concedida: bool = field(default=False, init=False)
    validacion_cientifica_realizada: bool = field(default=False, init=False)
    habilitacion_rc3_concedida: bool = field(default=False, init=False)
    _comprobacion: tuple | None = field(default=None, init=False, repr=False, compare=False)

    @property
    def comprobacion_local_coherente(self):
        c = self._comprobacion
        return (type(c) is tuple and len(c) == 2 and c[0] is _TESTIGO
                and c[1] == _datos_informe(self))

    @property
    def estado_estructural(self):
        ds = self.diagnosticos
        if not self.comprobacion_local_coherente:
            ds += (_diag("admision_aportada_no_observada_o_alterada", N.FALTANTE),)
        return estado_diagnosticos(ds)

    @property
    def admisible_para_consumo_tecnico(self):
        return (self.estado_estructural is E.APTO_ESTRUCTURALMENTE
                and self.cierre is not None and self.cierre.cierre_tecnico_comprobado
                and self.consumo is not None
                and self.consumo.estado is EstadoConsumoQA.CONTRATO_VALIDO_EN_ALCANCE
                and (not self.solicitud.exigir_integridad_fisica
                     or self.verificacion_fisica is not None
                     and self.verificacion_fisica.estado_local is EstadoLocal.INTEGRO))

    @property
    def autoriza_operacion(self):
        return False

    def __bool__(self):
        raise TypeError("admision_tecnica_especifica_no_es_permiso")


def _datos_informe(informe):
    return tuple(getattr(informe, f.name) for f in fields(informe) if f.name != "_comprobacion")


def _identidades(s, cierre):
    e = s.evidencia
    origen = e.solicitud
    ds = []
    if origen.entrada_qa.operacion.proyecto != s.proyecto:
        ds.append(_diag("proyecto_esperado_no_corresponde"))
    if origen.operacion_id != s.operacion_productora_id:
        ds.append(_diag("operacion_productora_no_corresponde"))
    if origen.entrada_qa.referencia_resultado != s.entrada_resultado_id:
        ds.append(_diag("entrada_resultado_no_corresponde"))
    if origen.salida != s.artefacto:
        ds.append(_diag("artefacto_o_revision_no_corresponde"))
    if cierre.linaje is None:
        ds.append(_diag("linaje_para_contraste_no_disponible", N.FALTANTE))
    else:
        salidas = [a for a in origen.inventario.artefactos if a.referencia == s.artefacto]
        if len(salidas) != 1 or salidas[0].contenido_id != s.contenido_id:
            ds.append(_diag("identidad_contenido_no_corresponde"))
    return ds


def _fisica(s, ds):
    """Nunca reutiliza el veredicto histórico como lectura actual."""
    m = s.materializacion
    if m is None or m.referencia is None:
        ds.append(_diag("referencia_fisica_no_disponible", N.FALTANTE))
        return None
    if type(m.solicitud) is not SolicitudMaterializacion or type(m.referencia) is not ReferenciaFisica:
        ds.append(_diag("contratos_fisicos_no_admitidos"))
        return None
    e = s.evidencia
    r = m.referencia
    if (m.solicitud.inventario != e.solicitud.inventario or m.solicitud.artefacto != s.artefacto
            or r.artefacto != s.artefacto or r.project_id != s.proyecto.project_id
            or r.contenido_id != s.contenido_id or r.size_bytes != e.size_bytes
            or r.sha256_recibido != e.sha256_bytes
            or m.solicitud.tamano_esperado != e.size_bytes):
        ds.append(_diag("referencia_fisica_no_corresponde_a_salida"))
        return None
    if m.estado_tecnico is not EstadoOperacion.CONCLUIDA:
        ds.append(_diag("materializacion_historica_sin_cierre", N.FALTANTE))
        return None
    v = verificar_fisicamente(m.solicitud, r)
    if v.estado_local is EstadoLocal.INCONSISTENTE:
        ds.append(_diag("integridad_fisica_contradictoria"))
    elif v.estado_local is not EstadoLocal.INTEGRO or not v.lectura_completa:
        ds.append(_diag("integridad_fisica_no_comprobada", N.FALTANTE))
    elif v.sha256_fisico != e.sha256_bytes or v.size_bytes_observado != e.size_bytes:
        ds.append(_diag("bytes_fisicos_no_corresponden_a_salida"))
    return v


def admitir_exportacion_tecnica(s: SolicitudAdmisionExportacion) -> InformeAdmisionExportacion:
    """Evalúa un documento; no ejecuta el productor ni modifica el grafo RC3/RC7."""
    if type(s) is not SolicitudAdmisionExportacion:
        raise TypeError("solicitud_admision_rc9_requerida")
    s.__post_init__()
    ds, consumo, cierre, fisica = [], None, None, None
    restricciones = s.proyecto.restricciones
    if s.consumidor_id != CONSUMIDOR or s.version_consumidor != VERSION_CONSUMO_QA:
        ds.append(_diag("consumidor_o_version_no_admitidos"))
    if s.finalidad != USO_CONSUMIR:
        ds.append(_diag("finalidad_fuera_de_politica_rc9"))
    if s.contenido is None:
        ds.append(_diag("contenido_no_aportado", N.FALTANTE))
    else:
        # Única validación del documento aportado: el consumidor real existente.
        consumo = consumir_exportaciones(s.contenido, limites=s.limites)
        if consumo.estado is EstadoConsumoQA.CONTRATO_RECHAZADO:
            ds.append(_diag("documento_rechazado_por_consumidor"))
        elif consumo.estado is EstadoConsumoQA.VALIDACION_INCOMPLETA:
            ds.append(_diag("consumo_no_completado", N.FALTANTE))
    if s.evidencia is None:
        ds.append(_diag("evidencia_rc8_no_aportada", N.FALTANTE))
    else:
        cierre = inspeccionar_cierre_exportacion(s.evidencia)
        ds.extend(cierre.diagnosticos)
        unidas, conflictos = _unir(
            tuple(RestriccionPropagada(r, ("proyecto_esperado_rc9",)) for r in restricciones),
            tuple(RestriccionPropagada(r, ("cierre_rc8",)) for r in cierre.restricciones),
        )
        restricciones = tuple(p.restriccion for p in unidas)
        ds.extend(conflictos)
        ds.extend(_identidades(s, cierre))
        if not cierre.cierre_tecnico_comprobado:
            ds.append(_diag("cierre_rc8_no_comprobado", N.FALTANTE))
        if consumo is not None and consumo.estado is EstadoConsumoQA.CONTRATO_VALIDO_EN_ALCANCE:
            # Comparación literal UTF-8, después de los presupuestos del consumidor.
            b = s.contenido.encode("utf-8") if type(s.contenido) is str else s.contenido
            texto = s.evidencia.resultado_nativo
            if cierre.consumo is not None and cierre.consumo.estado is EstadoConsumoQA.CONTRATO_VALIDO_EN_ALCANCE:
                if b != texto.encode("utf-8", errors="strict"):
                    ds.append(_diag("contenido_distinto_de_captura_rc8"))
    if any(r.tipo is TipoRestriccionQA.BLOQUEO_USO_DEL_RESULTADO and USO_CONSUMIR in r.operaciones
           for r in restricciones):
        ds.append(_diag("restriccion_impide_consumo_rc9"))
    if s.exigir_integridad_fisica:
        # No releer rutas ante identidades contradictorias o una captura insuficiente.
        if estado_diagnosticos(ds) is E.APTO_ESTRUCTURALMENTE:
            fisica = _fisica(s, ds)
        else:
            ds.append(_diag("relectura_no_realizada_por_precondiciones", N.FALTANTE))
    ds.append(_diag("admision_no_es_qa_permiso_ciencia_ni_habilitacion_rc3", N.INFORMACION))
    informe = InformeAdmisionExportacion(s, consumo, cierre, fisica, restricciones, _unicos(ds))
    object.__setattr__(informe, "_comprobacion", (_TESTIGO, _datos_informe(informe)))
    return informe
