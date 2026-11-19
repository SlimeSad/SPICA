"""RC8: captura explícita del exportador técnico existente, sin despacho general.

La inspección es pura. La captura local es trazabilidad de un proceso cooperativo,
no autenticación, permiso ni un cierre que RC3/RC7 admitan como dependencia.
"""

from dataclasses import dataclass, field, fields, replace
import hashlib
import json
from threading import Event

from ..calidad.consumo import consumir_exportaciones, EstadoConsumoQA, InformeConsumoQA, LimitesConsumoQA
from ..calidad.exportacion import exportar_resultado_json, LimitesExportacionQA, VERSION_EXPORTACION_QA, _Conversion
from ..calidad.restricciones import RestriccionQA, TipoRestriccionQA
from ..contextos import ContextoOperacion, EstadoOperacion as S, TipoOperacion, VinculoResultadoQA, cambiar_estado
from ..contextos.modelos import _texto
from ..coordinacion import InformeComposicion, LimitesComposicion, RestriccionPropagada, inspeccionar_composicion
from ..coordinacion._presupuesto import medir_descriptores
from ..coordinacion.inspeccion import _unicos
from ..coordinacion.modelos import estado_diagnosticos
from ..interoperabilidad.adaptadores import DiagnosticoAdaptacion as D, NivelDiagnostico as N
from ..interoperabilidad.modelos import EstadoAptitud as E
from . import InventarioArtefactos, ReferenciaArtefacto, InformeLinaje, TipoArtefacto, EstadoArtefacto, inspeccionar_linaje
from .coordinacion import _unir

VERSION_CIERRE = "0.1.0"
PRODUCTOR = "spica.calidad.exportacion.exportar_resultado_json"
USO_EXPORTAR = "exportar_json_qa0_rc8"
_TESTIGO = object()


def _diag(codigo, nivel=N.CONTRADICCION):
    return D(codigo, "cierre_exportacion_rc8", nivel)


@dataclass(frozen=True, slots=True)
class SolicitudExportacionTecnica:
    inventario: InventarioArtefactos = field(repr=False)
    composicion_id: str
    operacion_id: str
    salida: ReferenciaArtefacto
    entrada_qa: VinculoResultadoQA = field(repr=False)
    limites: LimitesComposicion = field(default_factory=LimitesComposicion)
    limites_exportacion: LimitesExportacionQA = field(default_factory=LimitesExportacionQA)
    version_contrato: str = VERSION_CIERRE

    def __post_init__(self):
        if type(self.version_contrato) is not str or self.version_contrato != VERSION_CIERRE:
            raise ValueError("version_cierre_rc8_no_admitida")
        for v in (self.composicion_id, self.operacion_id):
            _texto(v, maximo=128)
        for v, tipo in ((self.inventario, InventarioArtefactos), (self.salida, ReferenciaArtefacto),
                (self.entrada_qa, VinculoResultadoQA), (self.limites, LimitesComposicion),
                (self.limites_exportacion, LimitesExportacionQA)):
            if type(v) is not tipo:
                raise TypeError("contratos_tipificados_rc8_requeridos")
        self.limites_exportacion.__post_init__()


@dataclass(frozen=True, slots=True)
class EvidenciaExportacion:
    solicitud: SolicitudExportacionTecnica = field(repr=False)
    operacion_observada: ContextoOperacion | None = field(repr=False)
    resultado_nativo: str | None = field(repr=False)
    productor_invocado: bool
    size_bytes: int | None = None
    sha256_bytes: str | None = None  # Bytes UTF-8 en memoria; no hash físico.
    diagnosticos: tuple[D, ...] = ()
    productor_id: str = PRODUCTOR
    version_productor: str = VERSION_EXPORTACION_QA
    version_contrato: str = VERSION_CIERRE
    _captura: tuple | None = field(default=None, init=False, repr=False, compare=False)

    @property
    def captura_local_coherente(self):
        c = self._captura
        return (type(c) is tuple and len(c) == 2 and c[0] is _TESTIGO
                and c[1] == _datos_captura(self))

    @property
    def autoriza_operacion(self):
        return False

    def __bool__(self):
        raise TypeError("captura_rc8_no_es_permiso_ni_autenticacion")


@dataclass(frozen=True, slots=True)
class InformeCierreExportacion:
    evidencia: EvidenciaExportacion = field(repr=False)
    linaje: InformeLinaje | None = field(repr=False)
    coordinacion_rc3: InformeComposicion | None = field(repr=False)
    consumo: InformeConsumoQA | None = field(repr=False)
    restricciones: tuple[RestriccionQA, ...]
    diagnosticos: tuple[D, ...]
    version_contrato: str = field(default=VERSION_CIERRE, init=False)
    comprobacion_fisica_realizada: bool = field(default=False, init=False)
    autorizacion_concedida: bool = field(default=False, init=False)
    validacion_cientifica_realizada: bool = field(default=False, init=False)

    @property
    def estado_estructural(self):
        return estado_diagnosticos(self.diagnosticos)

    @property
    def cierre_tecnico_comprobado(self):
        e = self.evidencia
        return (self.estado_estructural is E.APTO_ESTRUCTURALMENTE
                and e.captura_local_coherente and e.productor_invocado is True
                and e.operacion_observada is not None and e.operacion_observada.estado is S.CONCLUIDA
                and self.consumo is not None and self.consumo.estado is EstadoConsumoQA.CONTRATO_VALIDO_EN_ALCANCE)

    @property
    def autoriza_operacion(self):
        return False

    def __bool__(self):
        raise TypeError("cierre_tecnico_especifico_no_es_permiso")


def _datos_captura(e):
    return tuple(getattr(e, f.name) for f in fields(e) if f.name != "_captura")


def _preparar(s):
    """Reutiliza inspectores; no construye ni recorre otro grafo de operaciones."""
    ds, linaje, rc3, op, salida, politicas = [], None, None, None, None, ()
    try:
        s.__post_init__()
        s.inventario.__post_init__()
        cs = [c for c in s.inventario.composiciones if c.identificador == s.composicion_id]
        if len(cs) != 1:
            return None, None, None, None, (), (_diag("composicion_rc3_ausente_o_ambigua"),)
        c = cs[0]
        c.__post_init__()
        cotas = LimitesComposicion(**{f.name: min(getattr(s.limites, f.name), getattr(c.limites, f.name)) for f in fields(s.limites)})
        _, _, codigo = medir_descriptores(replace(s, limites=cotas), None)
        if codigo:
            return None, None, None, None, (), (_diag(codigo, N.FALTANTE),)
        linaje = inspeccionar_linaje(s.inventario)
        rc3 = next(r for r in linaje.composiciones if r.composicion is c)
        if c.limites != cotas:
            rc3 = inspeccionar_composicion(replace(c, limites=cotas))
        if linaje.estado_estructural is E.INCOMPATIBLE:
            ds.append(_diag("linaje_o_coordinacion_contradictorios"))
        ns = [i for i in rc3.operaciones if i.nodo.contexto.operacion_id == s.operacion_id]
        ps = [p for p in s.inventario.producciones if p.operacion.operacion_id == s.operacion_id
              and p.operacion.proyecto == c.proyecto]
        if len(ns) != 1 or len(ps) != 1:
            return linaje, rc3, None, None, (), tuple(ds) + (_diag("operacion_productora_inexistente_o_ambigua"),)
        n, p = ns[0], ps[0]
        op = n.nodo.contexto
        p.__post_init__()
        op.__post_init__()
        if p.operacion is not op or op.tipo is not TipoOperacion.DESCRIPCION_ESTRUCTURAL:
            ds.append(_diag("operacion_productora_o_tipo_incompatible"))
        if p.metodo_id != PRODUCTOR or p.metodo_version != VERSION_EXPORTACION_QA:
            ds.append(_diag("productor_o_version_no_admitidos"))
        if op.estado is not S.INICIADA:
            ds.append(_diag("operacion_sin_inicio_explicito", N.FALTANTE))
        if n.nodo.cierre_qa is not None:
            ds.append(_diag("cierre_qa_no_admitido_en_exportador"))
        ds.extend(d for d in n.diagnosticos if d.nivel is not N.INFORMACION
                  and d.codigo != "estado_declarado_no_es_cierre_completo")
        if n.nodo.usos_declarados is None or USO_EXPORTAR not in n.nodo.usos_declarados:
            ds.append(_diag("uso_tecnico_no_declarado", N.FALTANTE))
        ars = {a.descriptor.referencia: a for a in linaje.artefactos}
        if len(p.entradas) != 1 or p.salidas != (s.salida,) or s.salida not in ars:
            return linaje, rc3, op, None, (), tuple(ds) + (_diag("entradas_o_salida_fuera_del_perfil_rc8"),)
        entrada, salida = ars[p.entradas[0]], ars[s.salida]
        ei, eo = entrada.descriptor.entrada_perfil.entrada, salida.descriptor.entrada_perfil.entrada
        for a in (entrada, salida):
            a.descriptor.__post_init__()
            a.descriptor.entrada_perfil.entrada.__post_init__()
        v = s.entrada_qa
        v.operacion.__post_init__()
        nativo = VinculoResultadoQA(v.operacion, v.entrada_id, v.referencia_resultado, v.resultado)
        if v.version_contrato != "0.1.0" or nativo != v:
            ds.append(_diag("vinculo_qa_de_entrada_incoherente"))
        if (ei.proyecto != v.operacion.proyecto or op.proyecto != v.operacion.proyecto
                or ei.entrada_id != v.referencia_resultado
                or ei.tipo_recurso != "resultado_qa_nativo" or op.entradas != (ei,)):
            ds.append(_diag("resultado_qa_no_corresponde_a_entrada_exportadora"))
        if (salida.descriptor.tipo is not TipoArtefacto.PREPARADO
                or salida.descriptor.formato != "application/json"
                or eo.entrada_id not in op.referencias_resultado
                or eo.proyecto != op.proyecto or s.salida in p.entradas):
            ds.append(_diag("identidad_o_tipo_de_salida_incompatible"))
        if any(a.descriptor.estado_logico is EstadoArtefacto.PARCIAL for a in (entrada, salida)):
            ds.append(_diag("artefacto_parcial_no_es_cierre", N.FALTANTE))
        grupos = (op.restricciones, v.restricciones,
            *(tuple(r.restriccion for r in a.restricciones) for a in (entrada, salida)),
            tuple(r.restriccion for r in n.restricciones))
        unidas, conflictos = _unir(*(tuple(RestriccionPropagada(r, ("fuente-rc8:"+str(i),)) for r in g)
                                    for i, g in enumerate(grupos)))
        politicas = tuple(r.restriccion for r in unidas)
        ds.extend(conflictos)
        if any(r.tipo is TipoRestriccionQA.BLOQUEO_USO_DEL_RESULTADO and USO_EXPORTAR in r.operaciones for r in politicas):
            ds.append(_diag("restriccion_impide_exportacion"))
    except (TypeError, ValueError, AttributeError, KeyError, StopIteration):
        ds.append(_diag("contratos_de_entrada_rc8_incompatibles"))
    return linaje, rc3, op, salida, politicas, _unicos(ds)


def ejecutar_exportacion_tecnica(solicitud, *, cancelacion=None):
    """Una invocación explícita del productor fijo; sin persistencia o reintentos."""
    if type(solicitud) is not SolicitudExportacionTecnica:
        raise TypeError("solicitud_rc8_requerida")
    if cancelacion is not None and type(cancelacion) is not Event:
        raise TypeError("event_estandar_o_none_requerido")
    s = solicitud
    _, _, op, salida, _, ds = _preparar(s)
    texto, invocada = None, False
    if cancelacion is not None and cancelacion.is_set():
        ds += (_diag("cancelacion_antes_de_exportar", N.FALTANTE),)
        if op is not None and op.estado is S.INICIADA:
            op = cambiar_estado(op, S.CANCELADA, diagnosticos=ds)
    elif not any(d.nivel is not N.INFORMACION for d in ds):
        invocada = True
        try:
            texto = exportar_resultado_json(s.entrada_qa.resultado,
                s.entrada_qa.contexto_exportacion, limites=s.limites_exportacion)
            if type(texto) is not str or len(texto) > s.limites_exportacion.max_bytes:
                raise ValueError("salida_no_admitida")
            datos = texto.encode("utf-8", errors="strict")
            if len(datos) > s.limites_exportacion.max_bytes:
                raise ValueError("salida_excesiva")
            parcial = cancelacion is not None and cancelacion.is_set()
            causa = (_diag("salida_obtenida_cierre_interrumpido", N.FALTANTE),) if parcial else ()
            op = cambiar_estado(op, S.PARCIAL if parcial else S.CONCLUIDA,
                diagnosticos=causa, referencias_resultado=(salida.descriptor.entrada_perfil.entrada.entrada_id,))
            ds += causa
        except KeyboardInterrupt:
            texto = None
            ds += (_diag("exportacion_interrumpida", N.FALTANTE),)
            op = cambiar_estado(op, S.CANCELADA, diagnosticos=ds)
        except Exception:
            texto = None
            ds += (_diag("productor_sin_resultado_completo", N.FALTANTE),)
            op = cambiar_estado(op, S.FALLIDA, diagnosticos=ds)
    datos = None if texto is None else texto.encode("utf-8")
    e = EvidenciaExportacion(s, op, texto, invocada,
        None if datos is None else len(datos), None if datos is None else hashlib.sha256(datos).hexdigest(), ds)
    object.__setattr__(e, "_captura", (_TESTIGO, _datos_captura(e)))
    return e


def inspeccionar_cierre_exportacion(evidencia):
    """Cotejo de captura/JSON; sin despacho, E/S o evaluación QA.

    El consumidor nativo reutiliza su contraste de codificación en memoria.
    Esto no despacha una operación ni vuelve a evaluar reglas QA.
    """
    if type(evidencia) is not EvidenciaExportacion or type(evidencia.solicitud) is not SolicitudExportacionTecnica:
        raise TypeError("evidencia_rc8_tipificada_requerida")
    e, s = evidencia, evidencia.solicitud
    linaje, rc3, op, salida, politicas, ds = _preparar(s)
    ds, consumo = list(ds), None
    if (e.version_contrato != VERSION_CIERRE or e.productor_id != PRODUCTOR
            or e.version_productor != VERSION_EXPORTACION_QA):
        ds.append(_diag("version_o_productor_de_evidencia_incompatible"))
    if not e.captura_local_coherente:
        ds.append(_diag("captura_aportada_no_observada_o_alterada", N.FALTANTE))
    if type(e.productor_invocado) is not bool or e.productor_invocado is not True:
        ds.append(_diag("productor_no_invocado", N.FALTANTE))
    ds.extend(e.diagnosticos)
    observado = e.operacion_observada
    try:
        if type(observado) is not ContextoOperacion or op is None:
            raise ValueError
        ContextoOperacion(**{f.name: getattr(observado, f.name) for f in fields(observado) if f.init})
        if replace(observado, estado=op.estado, diagnosticos=op.diagnosticos,
                   referencias_resultado=op.referencias_resultado) != op:
            raise ValueError
        if observado.estado is not S.CONCLUIDA:
            ds.append(_diag("estado_observado_sin_cierre_completo", N.FALTANTE))
        elif salida is None or observado.referencias_resultado != (salida.descriptor.entrada_perfil.entrada.entrada_id,):
            raise ValueError
    except (TypeError, ValueError):
        ds.append(_diag("operacion_observada_incompatible"))
    if e.resultado_nativo is None:
        ds.append(_diag("resultado_nativo_no_disponible", N.FALTANTE))
        if e.size_bytes is not None or e.sha256_bytes is not None:
            ds.append(_diag("huella_o_tamano_sin_resultado"))
    elif type(e.resultado_nativo) is not str or len(e.resultado_nativo) > s.limites_exportacion.max_bytes:
        ds.append(_diag("salida_fuera_del_presupuesto"))
    else:
        try:
            b = e.resultado_nativo.encode("utf-8", errors="strict")
            if len(b) > s.limites_exportacion.max_bytes:
                raise ValueError
            if type(e.size_bytes) is not int or e.size_bytes != len(b) or e.sha256_bytes != hashlib.sha256(b).hexdigest():
                ds.append(_diag("huella_o_tamano_de_salida_contradictorios"))
            consumo = consumir_exportaciones(b, limites=LimitesConsumoQA(
                max_bytes_documento=s.limites_exportacion.max_bytes,
                max_bytes_lote=s.limites_exportacion.max_bytes, max_resultados=1,
                profundidad=24, unidades_documento=50_000, unidades_lote=50_000))
            if consumo.estado is not EstadoConsumoQA.CONTRATO_VALIDO_EN_ALCANCE:
                ds.append(_diag("salida_rechazada_o_incompleta_por_consumidor",
                    N.FALTANTE if consumo.estado is EstadoConsumoQA.VALIDACION_INCOMPLETA else N.CONTRADICCION))
            else:
                doc = json.loads(consumo.documentos_aceptados[0])
                conversion = _Conversion(s.limites_exportacion)
                if (doc["resultado"] != conversion.convertir(s.entrada_qa.resultado)
                        or doc["contexto"] != conversion.convertir(s.entrada_qa.contexto_exportacion)):
                    ds.append(_diag("salida_no_corresponde_a_entrada_nativa"))
                if salida is not None:
                    eo = salida.descriptor.entrada_perfil.entrada
                    if (eo.sha256_declarado is not None and eo.sha256_declarado != e.sha256_bytes
                            or eo.size_bytes_declarado is not None and eo.size_bytes_declarado != len(b)):
                        ds.append(_diag("salida_contradice_descriptor_rc4"))
        except (ValueError, TypeError, UnicodeError, KeyError):
            ds.append(_diag("contenido_de_salida_no_comprobable"))
    ds.append(_diag("cierre_noqa_no_admitido_por_rc3_rc7", N.INFORMACION))
    return InformeCierreExportacion(e, linaje, rc3, consumo, politicas, _unicos(ds))
