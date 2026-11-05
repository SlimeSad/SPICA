"""Adaptación documental de objetos ya construidos. Sin lectura ni adquisición."""

from collections.abc import Mapping
from dataclasses import dataclass, field, fields, is_dataclass, replace
from datetime import date, datetime
from enum import Enum

from ..adquisicion.catalogo.documental import RecursoCatalogo
from ..adquisicion.catalogo.evidencias import EvidenciaDocumental
from ..adquisicion.catalogo.modelos import (
    DisponibilidadCatalogo, EstacionCatalogo, EstadoVerificacion as V,
    ProductoCatalogo, VariableCatalogo,
)
from ..adquisicion.consultas_locales.modelos import ObservacionLocal
from ..adquisicion.inspeccion_arcgis.modelos import (
    AlcanceMetadatos, EstadoJSON, EstadoMetadatos, TipoMetadatos, ValidacionMetadatos,
)
from ..adquisicion.vectorial.modelos import RecursoVector, ReferenciaEspacial, _congelar
from .modelos import (
    AmbitoCRS as A, CRSDeclarado, IdentidadRecurso, MarcoEspacial, MarcoTemporal,
    PeriodoTemporal, RecursoInteroperable, RepresentacionEspacial as R, Respaldo, _texto,
)


VERSION_ADAPTADORES = "0.1.0"


class NivelDiagnostico(Enum):
    INFORMACION = "informacion"
    FALTANTE = "faltante"
    CONTRADICCION = "contradiccion"


class EstadoAdaptacion(Enum):
    DESCRITO = "descripcion_construida_sin_afirmar_aptitud"
    PARCIAL = "descripcion_parcial"
    CONTRADICTORIO = "entradas_contradictorias"
    NO_REPRESENTABLE = "entrada_no_representable"


@dataclass(frozen=True)
class DiagnosticoAdaptacion:
    codigo: str
    campo: str
    nivel: NivelDiagnostico

    def __post_init__(self):
        _texto(self.codigo)
        _texto(self.campo)
        if type(self.nivel) is not NivelDiagnostico:
            raise TypeError("nivel_diagnostico_requerido")


def _capturar(entradas):
    """Snapshot de auditoría, no formato de persistencia o modelo científico nuevo."""
    nodos = 0
    def visitar(v, profundidad=0):
        nonlocal nodos
        nodos += 1
        if nodos > 100_000 or profundidad > 32:
            raise ValueError("presupuesto_snapshot_excedido")
        if type(v) is datetime:
            return {"tipo": "datetime", "original_iso": v.isoformat(), "fold": v.fold,
                    "zona_key": getattr(v.tzinfo, "key", None)}
        if type(v) is date:
            return {"tipo": "date", "original_iso": v.isoformat()}
        if isinstance(v, Enum):
            return v.value
        if is_dataclass(v) and not isinstance(v, type):
            return {f.name: visitar(getattr(v, f.name), profundidad + 1) for f in fields(v)}
        if isinstance(v, Mapping):
            nodos += len(v)
            if nodos > 100_000:
                raise ValueError("presupuesto_snapshot_excedido")
            if any(type(k) is not str for k in v):
                raise ValueError("clave_snapshot_no_textual")
            if any(len(k) > 65_536 for k in v):
                raise ValueError("clave_snapshot_excesiva")
            return {k: visitar(x, profundidad + 1) for k, x in v.items()}
        if type(v) in (tuple, list):
            return tuple(visitar(x, profundidad + 1) for x in v)
        if type(v) is str and len(v) > 65_536:
            raise ValueError("texto_snapshot_excesivo")
        return v  # _congelar valida los escalares y números finitos.
    return _congelar(visitar(entradas))


@dataclass(frozen=True)
class ResultadoAdaptacion:
    estado: EstadoAdaptacion
    recurso: RecursoInteroperable | None = field(repr=False)
    diagnosticos: tuple[DiagnosticoAdaptacion, ...]
    originales: Mapping[str, object] = field(repr=False)
    version_adaptador: str = field(default=VERSION_ADAPTADORES, init=False)

    def __post_init__(self):
        if type(self.estado) is not EstadoAdaptacion or type(self.diagnosticos) is not tuple:
            raise TypeError("resultado_adaptacion_tipificado_requerido")
        if len(self.diagnosticos) > 128 or any(type(x) is not DiagnosticoAdaptacion for x in self.diagnosticos):
            raise ValueError("diagnosticos_no_admitidos")
        if self.recurso is not None and type(self.recurso) is not RecursoInteroperable:
            raise TypeError("recurso_interoperable_requerido")
        if (self.estado is EstadoAdaptacion.NO_REPRESENTABLE) != (self.recurso is None):
            raise ValueError("estado_y_recurso_incoherentes")
        object.__setattr__(self, "originales", _congelar(self.originales))


def _diag(lista, codigo, campo, nivel=NivelDiagnostico.FALTANTE):
    lista.append(DiagnosticoAdaptacion(codigo, campo, nivel))


def _resultado(recurso, diagnosticos, originales):
    contradicciones = tuple(d.codigo + ":" + d.campo for d in diagnosticos if d.nivel is NivelDiagnostico.CONTRADICCION)
    if recurso is None:
        estado = EstadoAdaptacion.NO_REPRESENTABLE
    elif contradicciones:
        estado = EstadoAdaptacion.CONTRADICTORIO
        recurso = replace(recurso, contradicciones_declaradas=contradicciones)
    elif any(d.nivel is NivelDiagnostico.FALTANTE for d in diagnosticos):
        estado = EstadoAdaptacion.PARCIAL
    else:
        estado = EstadoAdaptacion.DESCRITO
    return ResultadoAdaptacion(estado, recurso, tuple(diagnosticos), originales)


def _tipo(v, tipo, opcional=False):
    if v is None and opcional:
        return
    if type(v) is not tipo:
        raise TypeError("objeto_de_contrato_existente_requerido")


def _entradas(**entradas):
    try:
        return _capturar(entradas)
    except (TypeError, ValueError, OverflowError, RecursionError):
        return None


def _sin_snapshot():
    ds = [DiagnosticoAdaptacion("entrada_excede_snapshot_o_no_es_representable", "entrada", NivelDiagnostico.FALTANTE)]
    return _resultado(None, ds, {})


def _base(catalogo, revision, producto, documento, diagnosticos):
    identidad = IdentidadRecurso(catalogo.fuente, catalogo.identificador, catalogo.producto_id, catalogo.localizador)
    if producto is not None and (producto.fuente != catalogo.fuente or producto.identificador != catalogo.producto_id):
        _diag(diagnosticos, "producto_fuera_del_recurso", "producto", NivelDiagnostico.CONTRADICCION)
    if documento is not None and (documento.fuente != catalogo.fuente or documento.recurso_id != catalogo.identificador
                                 or documento.producto_id != catalogo.producto_id):
        _diag(diagnosticos, "documento_fuera_del_recurso", "documento", NivelDiagnostico.CONTRADICCION)
    if documento is not None and documento.licencia_declarada is not None and catalogo.licencia_declarada is not None and documento.licencia_declarada != catalogo.licencia_declarada:
        _diag(diagnosticos, "terminos_distintos_requieren_aclaracion_de_alcance", "documento.licencia_declarada")
    licencia = catalogo.licencia_declarada
    if licencia is None and producto is not None and producto.fuente == catalogo.fuente and producto.identificador == catalogo.producto_id:
        licencia = producto.restricciones_licencia
    if licencia is None:
        _diag(diagnosticos, "condiciones_uso_desconocidas", "condiciones_uso")
    version = producto.version if producto is not None and producto.fuente == catalogo.fuente and producto.identificador == catalogo.producto_id else None
    return RecursoInteroperable(identidad, revision, catalogo.procedencia,
                               version_institucional=version, condiciones_uso=licencia)


def adaptar_catalogo(catalogo: RecursoCatalogo, *, revision_metadatos: str,
                     producto: ProductoCatalogo | None = None,
                     documento: EvidenciaDocumental | None = None) -> ResultadoAdaptacion:
    _tipo(catalogo, RecursoCatalogo)
    _tipo(producto, ProductoCatalogo, True)
    _tipo(documento, EvidenciaDocumental, True)
    originales = _entradas(catalogo=catalogo, producto=producto, documento=documento)
    if originales is None:
        return _sin_snapshot()
    diagnosticos = []
    base = _base(catalogo, revision_metadatos, producto, documento, diagnosticos)
    _diag(diagnosticos, "catalogo_no_aporta_marcos_espaciotemporales", "recurso")
    _diag(diagnosticos, "revision_descubrimiento_no_es_observacion", "procedencia.revisada_utc", NivelDiagnostico.INFORMACION)
    return _resultado(base, diagnosticos, originales)


def adaptar_meteorologia(catalogo: RecursoCatalogo, *, revision_metadatos: str,
                         estacion: EstacionCatalogo | None = None,
                         disponibilidad: DisponibilidadCatalogo | None = None,
                         variable: VariableCatalogo | None = None,
                         observacion: ObservacionLocal | None = None) -> ResultadoAdaptacion:
    _tipo(catalogo, RecursoCatalogo)
    for v, tipo in ((estacion, EstacionCatalogo), (disponibilidad, DisponibilidadCatalogo),
                    (variable, VariableCatalogo), (observacion, ObservacionLocal)):
        _tipo(v, tipo, True)
    originales = _entradas(catalogo=catalogo, estacion=estacion, disponibilidad=disponibilidad,
                           variable=variable, observacion=observacion)
    if originales is None:
        return _sin_snapshot()
    ds = []
    base = _base(catalogo, revision_metadatos, None, None, ds)
    for nombre, v in (("estacion", estacion), ("disponibilidad", disponibilidad), ("variable", variable)):
        if v is not None and (v.fuente != catalogo.fuente or v.producto_id != catalogo.producto_id):
            _diag(ds, "fuente_o_producto_contradictorios", nombre, NivelDiagnostico.CONTRADICCION)
    if observacion is not None and (observacion.procedencia.fuente != catalogo.fuente
                                  or observacion.procedencia.recurso_id != catalogo.identificador):
        _diag(ds, "observacion_de_otro_recurso", "observacion", NivelDiagnostico.CONTRADICCION)
    if disponibilidad is not None:
        if estacion is not None and disponibilidad.estacion_id is not None and disponibilidad.estacion_id != estacion.identificador:
            _diag(ds, "estacion_no_corresponde_a_disponibilidad", "disponibilidad.estacion_id", NivelDiagnostico.CONTRADICCION)
        if variable is not None and disponibilidad.variable_id is not None and disponibilidad.variable_id != variable.id_interno:
            _diag(ds, "variable_no_corresponde_a_disponibilidad", "disponibilidad.variable_id", NivelDiagnostico.CONTRADICCION)
    if any(d.nivel is NivelDiagnostico.CONTRADICCION for d in ds):
        return _resultado(base, ds, originales)
    try:
        campos = observacion.campos_originales if observacion is not None else ()
        if observacion is not None:
            _tipo(observacion.fecha_civil, date)
            if type(campos) is not tuple or any(type(p) is not tuple or len(p) != 2 for p in campos):
                raise ValueError("originales_no_representables")
        crs = ()
        coordenadas, respaldo = None, Respaldo()
        if estacion is not None:
            declarado = Respaldo(V.DECLARADO, estacion.procedencia)
            if estacion.coordenada_x is not None:
                coordenadas, respaldo = (estacion.coordenada_x, estacion.coordenada_y), declarado
            else:
                _diag(ds, "coordenadas_ausentes", "estacion.coordenadas")
            if estacion.sistema_referencia is not None:
                crs = (CRSDeclarado(A.GEOMETRIA, estacion.sistema_referencia, respaldo=declarado),)
            else:
                _diag(ds, "crs_desconocido", "estacion.sistema_referencia")
        else:
            _diag(ds, "estacion_catalogada_no_aportada", "estacion")
        ubicacion = tuple((k, v) for k, v in campos if k in (
            "ESTACION", "RED", "LONGITUD", "LATITUD", "ALTITUD", "DEPARTAMENTO", "PROVINCIA", "DISTRITO", "UBIGEO"))
        nombre = next((v for k, v in campos if k == "ESTACION"), None)
        ambigua = nombre is not None and (estacion is None or estacion.nombre is None or nombre != estacion.nombre)
        if nombre is not None:
            _diag(ds, "nombre_literal_no_acredita_identidad_fisica", "observacion.ESTACION")
        m = MarcoEspacial(R.PUNTUAL, ubicacion_declarada=ubicacion,
            identificador_ubicacion=estacion.identificador if estacion is not None else None,
            identidad_ambigua=ambigua, respaldo_identidad=Respaldo(V.DECLARADO, estacion.procedencia) if estacion else Respaldo(),
            coordenadas=coordenadas, respaldo_coordenadas=respaldo, crs=crs)
        p = None
        if disponibilidad is not None and disponibilidad.inicio is not None and disponibilidad.fin is not None:
            p = PeriodoTemporal(disponibilidad.inicio, disponibilidad.fin,
                                Respaldo(disponibilidad.estado, disponibilidad.procedencia))
        else:
            _diag(ds, "periodo_documentado_incompleto", "disponibilidad")
        _diag(ds, "identificador_disponibilidad_no_es_identificador_serie", "disponibilidad.identificador")
        _diag(ds, "convencion_limites_e_incertidumbre_no_documentados", "temporal")
        zona = disponibilidad.zona_horaria if disponibilidad else None
        if zona is None:
            _diag(ds, "zona_horaria_no_documentada", "temporal.zona_horaria_declarada")
        if any(k == "HORA" for k, _ in campos):
            _diag(ds, "hora_original_no_localizada_ni_reconstruida", "observacion.HORA", NivelDiagnostico.INFORMACION)
        t = MarcoTemporal(valores_originales=campos,
            fecha_observacion=observacion.fecha_civil if observacion else None,
            resolucion=disponibilidad.precision_temporal if disponibilidad else None,
            zona_horaria_declarada=zona, observaciones=p,
            respaldo_interpretacion=Respaldo(V.DECLARADO, disponibilidad.procedencia) if disponibilidad else Respaldo())
        codigo = variable.codigo_original if variable else None
        if observacion is not None:
            if codigo is not None and codigo != observacion.variable:
                _diag(ds, "codigo_variable_contradictorio", "observacion.variable", NivelDiagnostico.CONTRADICCION)
            codigo = observacion.variable
        atributos = (codigo,) if codigo is not None else ()
        _diag(ds, "precision_incertidumbre_y_cobertura_no_inferidas", "espacial")
        return _resultado(replace(base, espacial=m, temporal=t, atributos_declarados=atributos), ds, originales)
    except (ValueError, TypeError, OverflowError):
        _diag(ds, "metadatos_no_representables_sin_conversion", "meteorologia")
        return _resultado(None, ds, originales)


def adaptar_vectorial(recurso: RecursoVector, metadatos: ValidacionMetadatos, *,
                      revision_metadatos: str, catalogo: RecursoCatalogo | None = None) -> ResultadoAdaptacion:
    _tipo(recurso, RecursoVector)
    _tipo(metadatos, ValidacionMetadatos)
    _tipo(catalogo, RecursoCatalogo, True)
    originales = _entradas(recurso_vector=recurso, metadatos=metadatos, catalogo=catalogo)
    if originales is None:
        return _sin_snapshot()
    ds = []
    if (metadatos.tipo is not TipoMetadatos.CAPA or metadatos.estado is not EstadoMetadatos.COHERENTE
            or metadatos.estado_json is not EstadoJSON.COMPLETO or metadatos.alcance is not AlcanceMetadatos.ESENCIALES
            or metadatos.diagnosticos):
        _diag(ds, "inspeccion_de_capa_incompleta_o_invalida", "metadatos")
        return _resultado(None, ds, originales)
    objetivo = metadatos.objetivo
    if objetivo is not None and (objetivo.servicio_id != recurso.servicio_id or objetivo.capa_id != recurso.capa_id):
        _diag(ds, "servicio_o_capa_contradictorios", "metadatos.objetivo", NivelDiagnostico.CONTRADICCION)
    if catalogo is not None and (catalogo.fuente != recurso.fuente or catalogo.producto_id != recurso.producto_id
                                 or catalogo.identificador != recurso.recurso_id):
        _diag(ds, "catalogo_de_otro_recurso", "catalogo", NivelDiagnostico.CONTRADICCION)
    if catalogo is not None and objetivo is not None and catalogo.localizador != objetivo.url_capa:
        _diag(ds, "localizadores_distintos_no_se_unifican", "catalogo.localizador", NivelDiagnostico.CONTRADICCION)
    localizador = catalogo.localizador if catalogo else objetivo.url_capa if objetivo else None
    identidad = IdentidadRecurso(recurso.fuente, recurso.recurso_id, recurso.producto_id, localizador)
    base = RecursoInteroperable(identidad, revision_metadatos, recurso.procedencia,
                               condiciones_uso=catalogo.licencia_declarada if catalogo else None)
    d = metadatos.datos
    if not isinstance(d, Mapping):
        _diag(ds, "datos_de_capa_no_representables", "metadatos.datos")
        return _resultado(None, ds, originales)
    if type(d.get("id")) is not int or d["id"] != recurso.capa_id:
        _diag(ds, "id_capa_contradictorio_o_ausente", "metadatos.datos.id", NivelDiagnostico.CONTRADICCION)
    if objetivo is not None and d.get("name") != objetivo.capa_nombre:
        _diag(ds, "nombre_capa_contradictorio", "metadatos.datos.name", NivelDiagnostico.CONTRADICCION)
    if any(x.nivel is NivelDiagnostico.CONTRADICCION for x in ds):
        return _resultado(base, ds, originales)
    if objetivo is None:
        _diag(ds, "vinculo_servicio_capa_no_acreditado", "metadatos.objetivo")
    if metadatos.coherencia_servicio_capa is False:
        _diag(ds, "servicio_capa_con_contradiccion_declarada", "metadatos.coherencia_servicio_capa",
              NivelDiagnostico.CONTRADICCION)
    elif metadatos.coherencia_servicio_capa is not True:
        _diag(ds, "coherencia_servicio_capa_no_comprobada", "metadatos.coherencia_servicio_capa")
    declarado = Respaldo(V.DECLARADO, recurso.procedencia)
    referencias = []
    def agregar_crs(ambito, valor, campo):
        if valor is None:
            _diag(ds, "crs_no_aportado_en_su_ambito", campo)
            return
        if not isinstance(valor, Mapping) or "wkid" not in valor:
            _diag(ds, "definicion_crs_no_interpretada", campo)
            referencias.append(CRSDeclarado(ambito))
            return
        referencias.append(CRSDeclarado(ambito,
            ReferenciaEspacial(valor["wkid"], valor.get("latestWkid")), respaldo=declarado))
    try:
        agregar_crs(A.GEOMETRIA, d.get("spatialReference"), "metadatos.spatialReference")
        agregar_crs(A.ORIGEN, d.get("sourceSpatialReference"), "metadatos.sourceSpatialReference")
        e = d.get("extent")
        limites = None
        if e is not None:
            if not isinstance(e, Mapping):
                raise ValueError("extension_no_representable")
            limites = tuple(e[k] for k in ("xmin", "ymin", "xmax", "ymax"))
            agregar_crs(A.EXTENSION, e.get("spatialReference"), "metadatos.extent.spatialReference")
        else:
            _diag(ds, "extension_no_aportada", "metadatos.extent")
        geometria = d.get("geometryType")
        if geometria is None:
            _diag(ds, "geometria_no_declarada", "metadatos.geometryType")
        atributos = tuple(c["name"] for c in d.get("fields", ()))
        m = MarcoEspacial(R.VECTORIAL, geometria, declarado if geometria else Respaldo(),
            crs=tuple(referencias), extension=limites,
            respaldo_extension=declarado if limites is not None else Respaldo())
        _diag(ds, "extension_anunciada_no_acredita_cobertura_observada", "espacial.cobertura_observada")
        _diag(ds, "sin_precision_incertidumbre_o_unidades_por_eje", "espacial")
        _diag(ds, "version_software_no_es_edicion_de_producto", "metadatos.currentVersion", NivelDiagnostico.INFORMACION)
        _diag(ds, "metadatos_no_son_geometria_geograficamente_verificada", "metadatos", NivelDiagnostico.INFORMACION)
        if base.condiciones_uso is None:
            _diag(ds, "condiciones_uso_desconocidas", "condiciones_uso")
        return _resultado(replace(base, espacial=m, atributos_declarados=atributos), ds, originales)
    except (KeyError, TypeError, ValueError, OverflowError):
        _diag(ds, "metadatos_vectoriales_no_representables_sin_conversion", "metadatos.datos")
        return _resultado(None, ds, originales)
