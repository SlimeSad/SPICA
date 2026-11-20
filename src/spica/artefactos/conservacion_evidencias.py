"""RC10: expediente histórico como un artefacto RC4 conservado por RC6.

TEMP sintético exclusivamente. No restaura testigos, ejecuta productores ni
resuelve localizadores físicos históricos. No constituye admisión RC3/RC7.
"""

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
import hashlib

from ..calidad.consumo import consumir_exportaciones, InformeConsumoQA, EstadoConsumoQA
from ..adquisicion.readquisicion.modelos import EstadoLocal
from ..contextos import ContextoProyecto, EstadoOperacion as S
from ..contextos.modelos import _texto
from ..coordinacion.modelos import estado_diagnosticos
from ..interoperabilidad.modelos import EstadoAptitud as E
from . import ReferenciaArtefacto, InventarioArtefactos
from .cierre_exportacion import EvidenciaExportacion, InformeCierreExportacion, inspeccionar_cierre_exportacion
from .admision_exportacion import InformeAdmisionExportacion, admitir_exportacion_tecnica
from .materializacion import LimitesMaterializacion, SolicitudMaterializacion, entorno_materializacion
from .conservacion import (
    ConservadorExperimental, ControlGeneracion, UnidadConservacion,
    RecuperacionGeneracion, EstadoRecuperacion, recuperar_generacion,
)
from ._generacion_rc6 import ArchivosGeneracion, leer_metadatos
from ._archivos_rc5 import ErrorArchivoExperimental
from . import _codec_evidencias_rc10 as codec

VERSION_EVIDENCIAS = codec.VERSION
_CAPTURA = "captura_aportada_no_observada_o_alterada"
_CIERRE = "cierre_rc8_no_comprobado"
_FISICOS = frozenset(("relectura_no_realizada_por_precondiciones", "referencia_fisica_no_disponible",
    "contratos_fisicos_no_admitidos", "referencia_fisica_no_corresponde_a_salida",
    "materializacion_historica_sin_cierre", "integridad_fisica_contradictoria",
    "integridad_fisica_no_comprobada", "bytes_fisicos_no_corresponden_a_salida"))


def _exigir(v, codigo):
    if not v:
        raise ValueError(codigo)


@dataclass(frozen=True, slots=True)
class HechosHistoricos:
    captura_rc8_observada: bool
    estado_rc8: E | None
    cierre_rc8_comprobado: bool
    comprobacion_rc9_observada: bool
    estado_rc9: E | None
    admision_rc9_comprobada: bool


@dataclass(frozen=True, slots=True)
class ExpedienteEvidencias:
    evidencia_id: str
    proyecto: ContextoProyecto = field(repr=False)
    fecha_captura_utc: datetime
    cierre_rc8: InformeCierreExportacion | None = field(repr=False)
    admision_rc9: InformeAdmisionExportacion | None = field(repr=False)
    hechos: HechosHistoricos
    version_formato: str = VERSION_EVIDENCIAS

    @property
    def restricciones(self):
        return tuple(dict.fromkeys((*self.proyecto.restricciones,
            *(() if self.cierre_rc8 is None else self.cierre_rc8.restricciones),
            *(() if self.admision_rc9 is None else self.admision_rc9.restricciones))))

    @property
    def referencias_externas(self):
        # No se buscan archivos de entradas ni rutas RC5 históricas.
        c = self.cierre_rc8
        if c is None:
            return ()
        e = c.evidencia
        return tuple(a.referencia for a in e.solicitud.inventario.artefactos
            if a.referencia != e.solicitud.salida or e.resultado_nativo is None)

    @property
    def autoriza_operacion(self):
        return False

    def __bool__(self):
        raise TypeError("historia_rc10_no_es_admision_actual")


def capturar_evidencias(evidencia: EvidenciaExportacion | None,
        admision: InformeAdmisionExportacion | None, *, evidencia_id: str,
        proyecto: ContextoProyecto) -> ExpedienteEvidencias:
    """Captura prospectiva del expediente, no una fecha de ejecución RC8/RC9."""
    _exigir(evidencia is None or type(evidencia) is EvidenciaExportacion, "evidencia_rc8_tipificada")
    _exigir(admision is None or type(admision) is InformeAdmisionExportacion, "informe_rc9_tipificado")
    c = None if evidencia is None else inspeccionar_cierre_exportacion(evidencia)
    if admision is not None:
        _exigir(admision.solicitud.evidencia is evidencia, "capturas_rc8_rc9_distintas")
    h = HechosHistoricos(
        False if evidencia is None else evidencia.captura_local_coherente,
        None if c is None else c.estado_estructural,
        False if c is None else c.cierre_tecnico_comprobado,
        False if admision is None else admision.comprobacion_local_coherente,
        None if admision is None else admision.estado_estructural,
        False if admision is None else admision.admisible_para_consumo_tecnico)
    e = ExpedienteEvidencias(evidencia_id, proyecto, datetime.now(timezone.utc), c, admision, h)
    codificar_expediente(e)  # Tipos, presupuesto y coherencia antes de conservar.
    return e


def _diagnosticos(ds, omitir):
    return tuple(d for d in ds if d.codigo not in omitir)


def _revisar(e):
    _exigir(type(e) is ExpedienteEvidencias and e.version_formato == VERSION_EVIDENCIAS, "perfil_rc10_incompatible")
    _texto(e.evidencia_id, maximo=128)
    _exigir(type(e.proyecto) is ContextoProyecto and type(e.hechos) is HechosHistoricos, "contexto_rc10_tipificado")
    e.proyecto.__post_init__()
    _exigir(type(e.fecha_captura_utc) is datetime and e.fecha_captura_utc.utcoffset() is not None
        and e.fecha_captura_utc.utcoffset().total_seconds() == 0, "fecha_captura_rc10_invalida")
    h, c, a = e.hechos, e.cierre_rc8, e.admision_rc9
    _exigir(all(type(x) is bool for x in (h.captura_rc8_observada, h.cierre_rc8_comprobado,
        h.comprobacion_rc9_observada, h.admision_rc9_comprobada)), "hechos_rc10_tipificados")
    _exigir(c is None or type(c) is InformeCierreExportacion, "cierre_rc8_tipificado")
    _exigir(a is None or type(a) is InformeAdmisionExportacion, "admision_rc9_tipificada")
    if c is None:
        _exigir(not h.captura_rc8_observada and h.estado_rc8 is None and not h.cierre_rc8_comprobado,
            "hechos_rc8_sin_evidencia")
    else:
        s = c.evidencia.solicitud
        _exigir(e.proyecto == s.entrada_qa.operacion.proyecto, "proyecto_expediente_distinto")
        actual = inspeccionar_cierre_exportacion(c.evidencia)
        omitir = {_CAPTURA} if h.captura_rc8_observada else set()
        _exigir(_diagnosticos(c.diagnosticos, omitir) == _diagnosticos(actual.diagnosticos, omitir)
            and replace(actual, diagnosticos=c.diagnosticos) == c, "cierre_historico_rc8_discrepante")
        esperado = (h.captura_rc8_observada and c.estado_estructural is E.APTO_ESTRUCTURALMENTE
            and c.evidencia.productor_invocado is True and c.evidencia.operacion_observada is not None
            and c.evidencia.operacion_observada.estado is S.CONCLUIDA and c.consumo is not None
            and c.consumo.estado is EstadoConsumoQA.CONTRATO_VALIDO_EN_ALCANCE)
        _exigir(type(h.estado_rc8) is E and h.estado_rc8 is c.estado_estructural
            and h.cierre_rc8_comprobado is esperado, "estado_historico_rc8_discrepante")
    if a is None:
        _exigir(not h.comprobacion_rc9_observada and h.estado_rc9 is None and not h.admision_rc9_comprobada,
            "hechos_rc9_sin_evidencia")
        return
    _exigir(a.cierre == c and a.solicitud.evidencia is (None if c is None else c.evidencia),
        "vinculo_historico_rc8_rc9_discrepante")
    if c is None:
        _exigir(e.proyecto == a.solicitud.proyecto, "proyecto_expediente_distinto")
    # Reutiliza la política nativa como contraste de datos. Física histórica inerte:
    # jamás abrir la raíz RC5 conservada, ni recrear su testigo privado.
    contraste = admitir_exportacion_tecnica(replace(a.solicitud, exigir_integridad_fisica=False))
    omitir = set(_FISICOS) if a.solicitud.exigir_integridad_fisica else set()
    if h.captura_rc8_observada:
        omitir.add(_CAPTURA)
    if h.cierre_rc8_comprobado:
        omitir.add(_CIERRE)
    _exigir(a.consumo == contraste.consumo and a.restricciones == contraste.restricciones
        and _diagnosticos(a.diagnosticos, omitir) == _diagnosticos(contraste.diagnosticos, omitir),
        "admision_historica_rc9_discrepante")
    ds = a.diagnosticos
    estado = estado_diagnosticos(ds)
    if not h.comprobacion_rc9_observada and estado is E.APTO_ESTRUCTURALMENTE:
        estado = E.PENDIENTE_DE_EVIDENCIA
    fisica = a.verificacion_fisica
    if fisica is not None:
        m = a.solicitud.materializacion
        _exigir(m is not None and fisica.solicitud == m.solicitud and fisica.referencia == m.referencia,
            "verificacion_historica_de_otro_archivo")
    if a.solicitud.exigir_integridad_fisica:
        # Cotejo de las asociaciones/causas físicas conservadas. No es relectura.
        base_ds = _diagnosticos(contraste.diagnosticos, omitir)
        m = a.solicitud.materializacion
        if estado_diagnosticos(base_ds) is not E.APTO_ESTRUCTURALMENTE:
            causas = {"relectura_no_realizada_por_precondiciones"}
            _exigir(fisica is None, "lectura_historica_sin_precondiciones")
        elif m is None or m.referencia is None:
            causas = {"referencia_fisica_no_disponible"}
            _exigir(fisica is None, "lectura_historica_sin_referencia")
        elif (m.solicitud.inventario != c.evidencia.solicitud.inventario
                or m.solicitud.artefacto != a.solicitud.artefacto
                or m.referencia.artefacto != a.solicitud.artefacto
                or m.referencia.project_id != a.solicitud.proyecto.project_id
                or m.referencia.contenido_id != a.solicitud.contenido_id
                or m.referencia.size_bytes != c.evidencia.size_bytes
                or m.referencia.sha256_recibido != c.evidencia.sha256_bytes
                or m.solicitud.tamano_esperado != c.evidencia.size_bytes):
            causas = {"referencia_fisica_no_corresponde_a_salida"}
            _exigir(fisica is None, "lectura_historica_de_otro_recurso")
        elif m.estado_tecnico is not S.CONCLUIDA:
            causas = {"materializacion_historica_sin_cierre"}
            _exigir(fisica is None, "lectura_historica_sin_materializacion")
        else:
            _exigir(fisica is not None, "verificacion_historica_omitida")
            if fisica.estado_local is EstadoLocal.INCONSISTENTE:
                causas = {"integridad_fisica_contradictoria"}
            elif fisica.estado_local is not EstadoLocal.INTEGRO or not fisica.lectura_completa:
                causas = {"integridad_fisica_no_comprobada"}
            elif (fisica.sha256_fisico != c.evidencia.sha256_bytes
                    or fisica.size_bytes_observado != c.evidencia.size_bytes):
                causas = {"bytes_fisicos_no_corresponden_a_salida"}
            else:
                causas = set()
        _exigir({d.codigo for d in ds if d.codigo in _FISICOS} == causas,
            "causas_fisicas_historicas_discrepantes")
    if a.solicitud.exigir_integridad_fisica and h.admision_rc9_comprobada:
        m = a.solicitud.materializacion
        _exigir(m is not None, "materializacion_historica_ausente")
        UnidadConservacion._incluible(m)  # Coherencia de metadatos, sin lectura.
        _exigir(fisica is not None and fisica.estado_local is EstadoLocal.INTEGRO and fisica.lectura_completa
            and fisica.sha256_fisico == c.evidencia.sha256_bytes
            and fisica.size_bytes_observado == c.evidencia.size_bytes
            and m.solicitud.inventario == c.evidencia.solicitud.inventario
            and m.referencia.artefacto == a.solicitud.artefacto, "integridad_historica_rc9_discrepante")
    fisica_apta = (not a.solicitud.exigir_integridad_fisica or fisica is not None
        and fisica.estado_local is EstadoLocal.INTEGRO)
    esperado = (h.comprobacion_rc9_observada and estado is E.APTO_ESTRUCTURALMENTE
        and h.cierre_rc8_comprobado and a.consumo is not None
        and a.consumo.estado is EstadoConsumoQA.CONTRATO_VALIDO_EN_ALCANCE and fisica_apta)
    _exigir(type(h.estado_rc9) is E and h.estado_rc9 is estado
        and h.admision_rc9_comprobada is esperado, "estado_historico_rc9_discrepante")


def codificar_expediente(e):
    _revisar(e)
    h = e.hechos
    b = codec.codificar((e.version_formato, e.evidencia_id, e.proyecto, e.fecha_captura_utc,
        e.cierre_rc8, e.admision_rc9, (h.captura_rc8_observada, h.estado_rc8,
        h.cierre_rc8_comprobado, h.comprobacion_rc9_observada, h.estado_rc9, h.admision_rc9_comprobada)))
    codec.decodificar(b)  # Tipos exactos y constantes también antes de escribir.
    return b


def decodificar_expediente(b):
    v, identidad, proyecto, fecha, c, a, hs = codec.decodificar(b)
    _exigir(type(hs) is tuple and len(hs) == 6, "hechos_rc10_invalidos")
    e = ExpedienteEvidencias(identidad, proyecto, fecha, c, a, HechosHistoricos(*hs), v)
    _revisar(e)
    _exigir(codificar_expediente(e) == b, "expediente_rc10_no_canonico")
    return e


@dataclass(frozen=True, slots=True)
class ControlEvidencias:
    generacion: ControlGeneracion
    artefacto: ReferenciaArtefacto
    project_id: str
    evidencia_id: str
    version_formato: str = VERSION_EVIDENCIAS

    def __post_init__(self):
        _exigir(type(self.generacion) is ControlGeneracion and type(self.artefacto) is ReferenciaArtefacto,
            "control_evidencias_tipificado")
        self.generacion.__post_init__()
        self.artefacto.__post_init__()
        _texto(self.project_id)
        _texto(self.evidencia_id, maximo=128)
        _exigir(self.version_formato == VERSION_EVIDENCIAS, "perfil_rc10_incompatible")


def _vincular(e, inventario, ref):
    _exigir(type(inventario) is InventarioArtefactos and type(ref) is ReferenciaArtefacto,
        "inventario_y_referencia_rc4_requeridos")
    _exigir(len(inventario.artefactos) == 1 and inventario.producciones == ()
        and inventario.composiciones == (), "portador_rc10_no_acotado")
    d = inventario.artefactos[0]
    _exigir(d.referencia == ref and d.entrada_perfil.entrada.proyecto == e.proyecto
        and d.formato == VERSION_EVIDENCIAS and d.contenido_id == e.evidencia_id,
        "portador_rc10_de_otro_expediente")
    _exigir(set(e.restricciones) <= set(d.restricciones), "restricciones_omitidas_en_portador")


def conservar_evidencias(conservador, inventario, artefacto, expediente, *, cancelacion=None):
    """Delega íntegramente publicación, copias y cierre de generación en RC5/RC6."""
    _exigir(type(conservador) is ConservadorExperimental, "conservador_rc6_requerido")
    b = codificar_expediente(expediente)
    _vincular(expediente, inventario, artefacto)
    with entorno_materializacion() as m:
        s = SolicitudMaterializacion(inventario, artefacto, len(b), hashlib.sha256(b).hexdigest(),
            limites=LimitesMaterializacion(max_bytes=codec.base.MAX_METADATOS))
        bloque = s.limites.tamano_bloque
        r = m.materializar_sintetico(s, (b[i:i+bloque] for i in range(0, len(b), bloque)),
            cancelacion=cancelacion)
        guardado = conservador.conservar(UnidadConservacion(inventario, (r,)), cancelacion=cancelacion)
    return ControlEvidencias(guardado.control, artefacto, expediente.proyecto.project_id, expediente.evidencia_id)


@dataclass(frozen=True, slots=True)
class RecuperacionEvidencias:
    generacion: RecuperacionGeneracion
    expediente: ExpedienteEvidencias | None = field(default=None, repr=False)
    consumo_actual: InformeConsumoQA | None = field(default=None, repr=False)
    diagnosticos: tuple[str, ...] = ()
    comprobacion_actual_rc8: bool = field(default=False, init=False)
    admision_actual_rc9: bool = field(default=False, init=False)
    habilitacion_rc3_rc7: bool = field(default=False, init=False)
    autenticidad_acreditada: bool = field(default=False, init=False)
    validacion_cientifica: bool = field(default=False, init=False)

    @property
    def recuperada_en_alcance(self):
        return self.generacion.estado is EstadoRecuperacion.VERIFICADA and self.expediente is not None and not self.diagnosticos

    @property
    def externos_actuales(self):
        return () if self.expediente is None else tuple(
            (ref, EstadoLocal.NO_DISPONIBLE) for ref in self.expediente.referencias_externas)

    @property
    def autoriza_operacion(self):
        return False

    def __bool__(self):
        raise TypeError("recuperacion_rc10_no_es_permiso")


def recuperar_evidencias(raiz, control, *, cancelacion=None):
    _exigir(type(control) is ControlEvidencias, "control_evidencias_requerido")
    control.__post_init__()
    r = recuperar_generacion(raiz, control.generacion, cancelacion=cancelacion)
    if r.estado is not EstadoRecuperacion.VERIFICADA:
        return RecuperacionEvidencias(r, diagnosticos=("generacion_rc6_no_verificada",))
    try:
        _exigir(len(r.contenidos) == 1, "inventario_rc10_incompatible")
        c = r.contenidos[0]
        _exigir(c.artefacto == control.artefacto and c.relativa == "datos-000.bin", "artefacto_rc10_discrepante")
        b, n, sha = leer_metadatos(ArchivosGeneracion.abrir(raiz), c.relativa, codec.base.MAX_METADATOS)
        _exigir((n, sha) == (c.size_bytes, c.sha256_fisico), "contenido_rc10_cambio")
        e = decodificar_expediente(b)
        _exigir(e.proyecto.project_id == control.project_id and e.evidencia_id == control.evidencia_id,
            "control_rc10_de_otro_expediente")
        _vincular(e, r.unidad.inventario, control.artefacto)
        consumo = None
        if e.admision_rc9 is not None and e.admision_rc9.solicitud.contenido is not None:
            s = e.admision_rc9.solicitud
            consumo = consumir_exportaciones(s.contenido, limites=s.limites)
        final = recuperar_generacion(raiz, control.generacion, cancelacion=cancelacion)
        _exigir(final.estado is EstadoRecuperacion.VERIFICADA and final.unidad == r.unidad
            and final.contenidos == r.contenidos, "generacion_rc10_cambio")
        return RecuperacionEvidencias(final, e, consumo)
    except (ValueError, TypeError, KeyError, AttributeError, ArithmeticError, RecursionError,
            OSError, ErrorArchivoExperimental):
        # Mensajes externos, rutas históricas y contenido no se copian al informe.
        return RecuperacionEvidencias(r, diagnosticos=("expediente_rc10_incompatible_o_no_disponible",))
