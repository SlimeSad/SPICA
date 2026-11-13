"""Vínculo puro con QA0 y su identidad de exportación; no ejecuta evaluaciones."""

from dataclasses import dataclass, field

from ..calidad.exportacion import ContextoExportacionQA
from ..calidad.modelos import (
    ResultadoQA, VERSION_CONTRATO_QA, EstadoResultadoQA, RegistroQA, ProcedenciaQA,
)
from ..calidad.reglas import seleccionar_reglas
from ..calidad.restricciones import RestriccionQA, restricciones_resultado
from ..interoperabilidad.adaptadores import EstadoAdaptacion
from .modelos import (
    ContextoOperacion, EstadoOperacion, TipoOperacion, VERSION_CONTEXTO, PERFIL_QA0,
    combinar_restricciones, _texto, _tupla,
)


def _entrada_qa(operacion, entrada_id):
    if type(operacion) is not ContextoOperacion or operacion.tipo is not TipoOperacion.QA_NIVEL0:
        raise TypeError("operacion_qa_tipificada_requerida")
    _texto(entrada_id, maximo=128)
    entradas = [e for e in operacion.entradas if e.entrada_id == entrada_id]
    if len(entradas) != 1:
        raise ValueError("entrada_no_pertenece_a_operacion")
    entrada = entradas[0]
    if (operacion.proyecto.configuracion.perfil != PERFIL_QA0
            or operacion.proyecto.configuracion.revision != "1.0.0"
            or entrada.perfil_estructural != PERFIL_QA0):
        raise ValueError("perfil_o_revision_qa_incompatibles")
    if entrada.recurso is None or entrada.recurso.procedencia is None:
        raise ValueError("metadatos_insuficientes_para_vincular_qa")
    if entrada.estado is EstadoAdaptacion.CONTRADICTORIO:
        raise ValueError("entrada_contradictoria_no_vinculable")
    return entrada


def contexto_exportacion_qa(operacion: ContextoOperacion, entrada_id: str,
                            numero_registro: int) -> ContextoExportacionQA:
    """Mapea contexto→espacio y operación→evaluación; no alinea evaluaciones ajenas.

    entrada_id QA identifica la fila, como en 85-G: ID RC1 + ':' + posición
    original explícita, nunca ID de estación o una observación reconstruida.
    La revisión de contenido puede ser desconocida: el diagnóstico se conserva
    como incertidumbre, sin impedir una comprobación literal de Nivel 0.
    """
    entrada = _entrada_qa(operacion, entrada_id)
    if type(numero_registro) is not int or numero_registro <= 0:
        raise ValueError("posicion_original_qa_requerida")
    incertidumbres = tuple(dict.fromkeys((*entrada.incertidumbres,
        *(d.codigo for d in entrada.diagnosticos))))
    return ContextoExportacionQA(operacion.proyecto.contexto_id, operacion.operacion_id,
        entrada.entrada_id + ":" + str(numero_registro), configuracion=operacion.configuracion_qa,
        incertidumbres=incertidumbres)


@dataclass(frozen=True, slots=True)
class VinculoResultadoQA:
    """Conserva por referencia el resultado nativo y todas las restricciones RC1.

    No es un nuevo ResultadoQA ni un formato de exportación. Las restricciones
    adicionales RC1 permanecen en esta envolvente, fuera del JSON QA 0.1.0.
    """

    operacion: ContextoOperacion = field(repr=False)
    entrada_id: str
    referencia_resultado: str
    resultado: ResultadoQA = field(repr=False)
    contexto_exportacion: ContextoExportacionQA = field(init=False)
    restricciones: tuple[RestriccionQA, ...] = field(init=False)
    version_contrato: str = field(default=VERSION_CONTEXTO, init=False)

    def __post_init__(self):
        entrada = _entrada_qa(self.operacion, self.entrada_id)
        _texto(self.referencia_resultado)
        o, r = self.operacion, self.resultado
        if o.estado in (EstadoOperacion.DECLARADA, EstadoOperacion.PLANIFICADA):
            raise ValueError("resultado_antes_de_inicio_declarado")
        if o.estado is not EstadoOperacion.INICIADA and self.referencia_resultado not in o.referencias_resultado:
            raise ValueError("resultado_ajeno_al_cierre_declarado")
        if type(r) is not ResultadoQA or r.version_contrato != VERSION_CONTRATO_QA:
            raise TypeError("resultado_qa_compatible_requerido")
        if (type(r.registro) is not RegistroQA or type(r.procedencia) is not ProcedenciaQA
                or type(r.estado) is not EstadoResultadoQA):
            raise TypeError("componentes_resultado_qa_tipados_requeridos")
        if r.regla not in seleccionar_reglas(o.configuracion_qa):
            raise ValueError("regla_fuera_de_configuracion_declarada")
        if o.estado is EstadoOperacion.CONCLUIDA and r.estado is EstadoResultadoQA.EVALUACION_INCOMPLETA:
            raise ValueError("resultado_incompleto_en_operacion_concluida")
        identidad = entrada.recurso.identidad
        p = r.procedencia
        if (p.fuente != identidad.fuente or p.recurso_id != identidad.recurso_id
                or p.asset_id != entrada.asset_id or p.sha256_referencia != entrada.sha256_declarado):
            raise ValueError("procedencia_qa_no_corresponde_a_entrada")
        local = r.registro.procedencia_original
        if local is not None and (local.fuente != p.fuente or local.recurso_id != p.recurso_id
                or local.asset_id != p.asset_id or local.sha256_declarado != p.sha256_referencia):
            raise ValueError("procedencia_original_qa_contradictoria")
        object.__setattr__(self, "contexto_exportacion", contexto_exportacion_qa(
            o, self.entrada_id, r.registro.numero_registro))
        object.__setattr__(self, "restricciones", combinar_restricciones(
            o.restricciones, restricciones_resultado(r)))

    @property
    def autoriza_operacion(self) -> bool:
        return False

    def __bool__(self):
        raise TypeError("vinculo_estructural_no_es_permiso")


def validar_vinculos_qa(operacion: ContextoOperacion,
                        vinculos: tuple[VinculoResultadoQA, ...]) -> None:
    """Coteja un lote explícito: pertenencia, referencias, cuotas y duplicaciones.

    No comprueba EOF, ejecución real, autenticidad, cobertura de todas las reglas
    ni integridad física. CONCLUIDA sigue siendo un estado declarado del llamador.
    """
    if type(operacion) is not ContextoOperacion or operacion.tipo is not TipoOperacion.QA_NIVEL0:
        raise TypeError("operacion_qa_tipificada_requerida")
    _tupla(vinculos, VinculoResultadoQA, min(operacion.limites_qa.max_resultados,
        operacion.proyecto.configuracion.max_referencias_resultado))
    if any(v.operacion != operacion for v in vinculos):
        raise ValueError("resultado_de_otro_contexto_u_operacion")
    referencias = tuple(v.referencia_resultado for v in vinculos)
    if len(set(referencias)) != len(referencias):
        raise ValueError("referencia_resultado_duplicada")
    if operacion.estado is not EstadoOperacion.INICIADA and referencias != operacion.referencias_resultado:
        raise ValueError("referencias_no_corresponden_al_cierre")
    claves, registros = set(), {}
    for v in vinculos:
        r = v.resultado
        registro = (v.entrada_id, r.registro.numero_registro)
        if registro in registros and registros[registro] != r.registro:
            raise ValueError("registro_qa_con_descripciones_distintas")
        clave = (*registro, r.regla.identificador, r.regla.version,
                 tuple(sorted(k for k, _ in r.valores_originales)))
        if clave in claves:
            raise ValueError("diagnostico_qa_duplicado_en_operacion")
        claves.add(clave)
        registros[registro] = r.registro
    if len(registros) > operacion.limites_qa.max_registros:
        raise ValueError("registros_superan_presupuesto_qa")
