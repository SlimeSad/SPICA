"""Comparación documental pura. No importa ejecutores, catálogos mutables ni I/O."""

from dataclasses import replace

from ..modelos_cientificos import CondicionAplicabilidad, DimensionAplicabilidad
from .modelos import (
    AspectoAdicional, DiagnosticoAplicabilidad, EspecificacionAplicabilidad, EstadoAplicabilidad as E,
    EstadoRequisito as R, ExpedienteProducto, HallazgoAplicabilidad,
    NivelEvidencia as N, TipoRequisito, VigenciaDocumento as V,
)


def _documento(documento):
    motivos = []
    if documento.contradicciones or documento.nivel is N.CONTRADICTORIA:
        return R.CONTRADICTORIO, ("documento_contradictorio",)
    if documento.vigencia is V.OBSOLETO and documento.nivel is N.VERIFICADA:
        return R.INCOMPATIBLE, ("documento_obsoleto",)
    if documento.nivel is N.DESCONOCIDA:
        return R.INSUFICIENTE, ("documento_no_verificado",)
    ref = documento.referencia
    if ref.version_documento is None or ref.fecha_documento is None:
        return R.INSUFICIENTE, ("version_o_fecha_documental_desconocida",)
    if documento.nivel is not N.VERIFICADA:
        motivos.append("documento_declarado_o_inferido")
    if documento.vigencia is V.OBSOLETO:
        motivos.append("obsolescencia_no_verificada")
    if documento.vigencia is V.DESCONOCIDA:
        motivos.append("vigencia_documental_desconocida")
    if documento.incertidumbres or documento.pendientes:
        motivos.append("documento_con_incertidumbres_o_pendientes")
    return (R.CONDICIONADO, tuple(motivos)) if motivos else (R.DEMOSTRADO, ("documento_aportado_verificado",))


def _combinar(estados):
    for estado in (R.CONTRADICTORIO, R.INCOMPATIBLE, R.INSUFICIENTE, R.CONDICIONADO):
        if estado in estados:
            return estado
    return R.DEMOSTRADO


def _firma_referencia(ref):
    return (ref.procedencia, ref.titulo, ref.version_documento, ref.fecha_documento, ref.sha256_referencia)


def verificar_aplicabilidad(especificacion: EspecificacionAplicabilidad,
                            expediente: ExpedienteProducto) -> DiagnosticoAplicabilidad:
    """Sin ejecución, aprobaciones, lectura de documentos o normalización implícita.

    Las evidencias son instantáneas aportadas por el llamador. VERIFICADA no prueba
    autenticidad institucional ni la corrección de esa clasificación. Las coberturas
    se cotejan por etiquetas exactas documentadas, sin inferir contención espacial
    o temporal. La salida no es HabilitacionCientifica ni evidencia de ejecución.
    """
    if type(especificacion) is not EspecificacionAplicabilidad or type(expediente) is not ExpedienteProducto:
        raise TypeError("Solo especificación y expediente documentales inmutables")
    todos = (*especificacion.documentos, *expediente.documentos)
    if len({d.naturaleza for d in todos}) > 1:
        raise ValueError("La evidencia sintética no se utiliza como institucional")
    hallazgos = []

    def agregar(identificador, dimension, estado, motivos, referencias=()):
        hallazgos.append(HallazgoAplicabilidad(identificador, dimension, estado,
                                             tuple(dict.fromkeys(motivos)), tuple(dict.fromkeys(referencias))))

    documentos = {}
    localizadores = {}
    for doc in todos:
        ref = doc.referencia
        previo = documentos.get(ref.identificador)
        if previo is not None and replace(previo, localizacion=doc.localizacion) != doc:
            agregar("documentos", None, R.CONTRADICTORIO, ("misma_identidad_documental_con_distinta_evidencia",),
                    (ref.identificador,))
        anterior = localizadores.get(ref.localizador)
        # Distintos alias de una misma referencia no son una contradicción.
        if anterior is not None and _firma_referencia(anterior) != _firma_referencia(ref):
            agregar("documentos", None, R.CONTRADICTORIO, ("localizador_con_referencias_distintas",),
                    (ref.identificador, localizadores[ref.localizador].identificador))
        documentos[ref.identificador] = doc
        localizadores[ref.localizador] = ref

    # Audita todo el expediente aportado, incluso evidencia adversa no utilizada.
    for doc in dict.fromkeys(todos):
        estado, motivos = _documento(doc)
        agregar("documento:" + doc.referencia.identificador, None, estado, motivos, (doc.referencia.identificador,))
    for ref in especificacion.regla.referencias:
        if ref.identificador not in {d.referencia.identificador for d in especificacion.documentos}:
            agregar("documento:" + ref.identificador, None, R.INSUFICIENTE, ("evidencia_de_referencia_ausente",),
                    (ref.identificador,))
    if especificacion.regla.contradicciones_documentales:
        agregar("regla", None, R.CONTRADICTORIO, ("contradicciones_documentales_de_la_regla",))
    if any(not p.referencias for p in especificacion.regla.parametros):
        agregar("parametros", AspectoAdicional.PARAMETROS_ESPECIFICOS, R.INSUFICIENTE,
                ("parametros_sin_procedencia_documental",))
    if not especificacion.requisitos or not especificacion.regla.referencias:
        agregar("regla", None, R.INSUFICIENTE, ("requisitos_o_referencias_ausentes",))

    por_dimension = {}
    for afirmacion in expediente.afirmaciones:
        por_dimension.setdefault(afirmacion.dimension, []).append(afirmacion)
    for dimension, afirmaciones in por_dimension.items():
        if (any(a.contradicciones or a.nivel is N.CONTRADICTORIA for a in afirmaciones)
                or len({a.valor for a in afirmaciones if a.valor is not None}) > 1):
            agregar("producto", dimension, R.CONTRADICTORIO, ("afirmaciones_contradictorias",),
                    tuple(r for a in afirmaciones for r in a.referencias))
    if any(a.valor is not None and a.valor != expediente.producto.identificador
           for a in por_dimension.get(DimensionAplicabilidad.PRODUCTO, ())):
        agregar("producto", DimensionAplicabilidad.PRODUCTO, R.CONTRADICTORIO,
                ("afirmacion_no_corresponde_a_identidad_del_producto",))

    def comprobar(condicion):
        refs = condicion.referencias
        if not refs or any(ref not in documentos for ref in refs):
            return R.INSUFICIENTE, ("fundamento_del_requisito_ausente",), refs
        estados = [_documento(documentos[ref])[0] for ref in refs]
        if type(condicion) is CondicionAplicabilidad and condicion.sin_restriccion:
            return _combinar(estados), ("ausencia_de_restriccion_segun_referencia",), refs
        afirmaciones = por_dimension.get(condicion.dimension, ())
        if not afirmaciones:
            return R.INSUFICIENTE, ("dato_de_producto_ausente",), refs
        referencias = (*refs, *(r for a in afirmaciones for r in a.referencias))
        if (any(a.contradicciones or a.nivel is N.CONTRADICTORIA for a in afirmaciones)
                or len({a.valor for a in afirmaciones if a.valor is not None}) > 1):
            return R.CONTRADICTORIO, ("afirmaciones_contradictorias",), referencias
        if any(a.nivel is N.DESCONOCIDA for a in afirmaciones):
            return R.INSUFICIENTE, ("dato_de_producto_desconocido",), referencias
        for a in afirmaciones:
            if not a.referencias:
                estados.append(R.INSUFICIENTE)
            estados.extend(_documento(documentos[r])[0] for r in a.referencias)
            if a.nivel is not N.VERIFICADA or a.incertidumbres or a.pendientes:
                estados.append(R.CONDICIONADO)
        base = _combinar(estados)
        if base is not R.DEMOSTRADO:
            return base, ("evidencia_no_suficiente_para_cotejo_demostrado",), referencias
        if afirmaciones[0].valor not in condicion.valores_permitidos:
            return R.INCOMPATIBLE, ("valor_literal_incompatible",), referencias
        return R.DEMOSTRADO, ("coincidencia_literal_documentada",), referencias

    for requisito in especificacion.requisitos:
        dimension = requisito.condicion.dimension
        referencias_activacion = ()
        if requisito.tipo is TipoRequisito.CONDICIONAL:
            estado, motivos, refs = comprobar(requisito.activar_si)
            # Solo un valor incompatible verificado desactiva la condición.
            if estado is R.INCOMPATIBLE and motivos == ("valor_literal_incompatible",):
                agregar(requisito.identificador, dimension, R.NO_APLICA, ("condicion_no_activada_demostrada",), refs)
                continue
            if estado is not R.DEMOSTRADO:
                salida = R.CONTRADICTORIO if estado is R.CONTRADICTORIO else R.CONDICIONADO
                agregar(requisito.identificador, dimension, salida, ("activacion_condicional_no_resuelta", *motivos), refs)
                continue
            referencias_activacion = refs
        estado, motivos, refs = comprobar(requisito.condicion)
        if requisito.tipo is TipoRequisito.CONDICIONAL:
            motivos = ("condicion_activada_demostrada", *motivos)
            refs = (*referencias_activacion, *refs)
        agregar(requisito.identificador, dimension, estado, motivos, refs)

    global_ = _combinar([h.estado for h in hallazgos])
    estado = {R.CONTRADICTORIO: E.EVIDENCIA_CONTRADICTORIA,
              R.INCOMPATIBLE: E.INCOMPATIBILIDAD_DOCUMENTADA,
              R.INSUFICIENTE: E.INFORMACION_INSUFICIENTE,
              R.CONDICIONADO: E.COMPATIBILIDAD_CONDICIONADA,
              R.DEMOSTRADO: E.COMPATIBILIDAD_DOCUMENTAL_DEMOSTRADA}[global_]
    motivos = tuple(dict.fromkeys(m for h in hallazgos for m in h.motivos))
    return DiagnosticoAplicabilidad(especificacion, expediente, estado, tuple(hallazgos), motivos)
