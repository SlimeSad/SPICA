"""Comparación literal conservadora y acotada. Sin lectura o transformación."""

from ...adquisicion.catalogo.modelos import EstadoVerificacion as V
from ...adquisicion.readquisicion.modelos import EstadoLocal
from ...calidad.restricciones import TipoRestriccionQA
from ...contextos import ContextoOperacion, TipoOperacion, combinar_restricciones
from ..adaptadores import DiagnosticoAdaptacion as Diag, NivelDiagnostico as N
from ..evaluador import evaluar_aptitud
from ..modelos import EstadoAptitud as E, Respaldo, DimensionEvaluacion as D
from .modelos import (
    AspectoCampo as A, DeclaracionPerfil, EntradaPerfil, EstadoUnidad as U,
    FinalidadCompatibilidad, ResultadoCompatibilidad,
)


def comparar_perfiles(primero: EntradaPerfil, segundo: EntradaPerfil,
                      finalidad: FinalidadCompatibilidad, *,
                      operacion: ContextoOperacion | None = None) -> ResultadoCompatibilidad:
    """La finalidad enumera únicamente requisitos de comparación, nunca permisos.

    REFERENCIAS delega en evaluar_aptitud. NO_EVALUABLE se conserva en el resultado
    nativo y se presenta como PENDIENTE_DE_EVIDENCIA en el resumen RC2.
    """
    if (type(primero) is not EntradaPerfil or type(segundo) is not EntradaPerfil
            or type(finalidad) is not FinalidadCompatibilidad):
        raise TypeError("dos_entradas_perfil_y_finalidad_requeridas")
    restricciones = combinar_restricciones(primero.restricciones, segundo.restricciones)
    if operacion is not None:
        if type(operacion) is not ContextoOperacion or operacion.tipo is not TipoOperacion.DESCRIPCION_ESTRUCTURAL:
            raise TypeError("operacion_descriptiva_rc1_requerida")
        if operacion.proposito != finalidad.descripcion:
            raise ValueError("finalidad_no_corresponde_a_operacion")
        if any(not any(e.entrada is original for original in operacion.entradas) for e in (primero, segundo)):
            raise ValueError("entrada_no_pertenece_a_operacion")
        restricciones = combinar_restricciones(restricciones, operacion.restricciones)
    ds = []

    def anotar(codigo, campo, nivel=N.FALTANTE):
        d = Diag(codigo, campo, nivel)
        if d not in ds:
            ds.append(d)

    def literal(a, b, campo):
        if (a.valor is None or b.valor is None or a.respaldo.estado is not V.VERIFICADO
                or b.respaldo.estado is not V.VERIFICADO):
            anotar("literal_o_respaldo_insuficiente", campo)
        elif a.valor != b.valor:
            anotar("literales_distintos_sin_transformacion_admitida", campo, N.CONTRADICCION)
        else:
            anotar("literal_coincidente_con_respaldo_aportado", campo, N.INFORMACION)

    entradas = (primero, segundo)
    recursos = tuple(e.entrada.recurso for e in entradas)
    for i, v in enumerate(entradas):
        p, e = v.perfil, v.entrada
        if (p.identificador, p.version) not in finalidad.versiones_admitidas:
            anotar("version_perfil_no_admitida", f"p{i}.version", N.CONTRADICCION)
        if p.ambito.valor is None or p.ambito.respaldo.estado is not V.VERIFICADO:
            anotar("ambito_del_perfil_sin_respaldo", f"p{i}.ambito")
        if e.perfil_estructural is None:
            anotar("vinculo_perfil_no_declarado_en_rc1", f"p{i}.entrada")
        r = e.recurso
        if r is None or r.procedencia is None or r.procedencia.evidencia is None:
            anotar("recurso_o_procedencia_insuficientes", f"p{i}.recurso")
        for d in e.diagnosticos:
            if d.nivel is N.CONTRADICCION:
                anotar(d.codigo, f"p{i}.{d.campo}", N.CONTRADICCION)
        if r is not None and r.identidad.producto_id is None:
            anotar("producto_no_documentado", f"p{i}.recurso")
        if p.incertidumbres or e.incertidumbres:
            anotar("incertidumbres_conservadas_en_entrada_y_perfil", f"p{i}", N.INFORMACION)

    pa, pb = (e.perfil for e in entradas)
    if (pa.identificador, pa.version) == (pb.identificador, pb.version) and pa != pb:
        anotar("misma_identidad_y_version_de_perfil_con_definiciones_distintas", "perfiles", N.CONTRADICCION)
    for r in restricciones:
        bloquea = (r.tipo is TipoRestriccionQA.BLOQUEO_USO_DEL_RESULTADO
                   and finalidad.identificador in r.operaciones)
        anotar("restriccion_bloqueante" if bloquea else "restriccion_conservada",
               r.codigo, N.CONTRADICCION if bloquea else N.INFORMACION)

    ra, rb = recursos
    if ra is not None and rb is not None:
        iguales = ra.identidad == rb.identidad
        anotar("identidad_recurso_coincidente" if iguales else "identidades_recurso_distintas",
               "identidad_recurso", N.CONTRADICCION if finalidad.requiere_mismo_recurso and not iguales else N.INFORMACION)
    elif finalidad.requiere_mismo_recurso:
        anotar("identidad_recurso_insuficiente", "identidad_recurso")
    if primero.entrada.proyecto != segundo.entrada.proyecto:
        anotar("contextos_proyecto_distintos_no_fusionados", "proyecto", N.INFORMACION)
    if finalidad.requiere_mismo_contenido:
        ea, eb = (e.entrada for e in entradas)
        if (ea.sha256_declarado is not None and eb.sha256_declarado is not None
                and ea.sha256_declarado != eb.sha256_declarado
                or ea.size_bytes_declarado is not None and eb.size_bytes_declarado is not None
                and ea.size_bytes_declarado != eb.size_bytes_declarado):
            anotar("contenido_declarado_distinto", "contenido", N.CONTRADICCION)
        elif any(e.sha256_declarado is None or e.size_bytes_declarado is None
                 or e.evidencia_local is None or e.evidencia_local.estado is not EstadoLocal.INTEGRO
                 for e in (ea, eb)):
            anotar("identidad_contenido_sin_evidencia_fisica_aportada", "contenido")
        else:
            anotar("contenido_coincidente_segun_evidencia_aportada_no_reverificada", "contenido", N.INFORMACION)

    campos = tuple({c.nombre: c for c in e.perfil.campos} for e in entradas)
    for na, nb in finalidad.campos:
        a, b = campos[0].get(na), campos[1].get(nb)
        etiqueta = f"campos.{na}:{nb}"
        if a is None or b is None:
            anotar("campo_requerido_ausente", etiqueta, N.CONTRADICCION)
            continue
        for aspecto in finalidad.aspectos:
            clave = etiqueta + "." + aspecto.value
            if aspecto in (A.TIPO, A.SIGNIFICADO, A.AGREGACION, A.CALENDARIO):
                literal(getattr(a, aspecto.value), getattr(b, aspecto.value), clave)
            elif aspecto in (A.VARIABLE, A.TIPO_MEDICION, A.FRECUENCIA):
                va, vb = a.variable, b.variable
                if (va is None or vb is None or a.respaldo_variable.estado is not V.VERIFICADO
                        or b.respaldo_variable.estado is not V.VERIFICADO):
                    anotar("variable_o_respaldo_insuficientes", clave)
                elif aspecto is A.VARIABLE:
                    def identidad(v):
                        return (v.fuente, v.producto_id, v.id_interno, v.codigo_original)
                    anotar("identidad_variable_coincidente" if identidad(va) == identidad(vb) else
                           "identidades_variable_distintas_sin_correspondencia",
                           clave, N.INFORMACION if identidad(va) == identidad(vb) else N.CONTRADICCION)
                else:
                    literal(DeclaracionPerfil(getattr(va, aspecto.value),
                                a.respaldo_variable if getattr(va, aspecto.value) is not None else Respaldo()),
                            DeclaracionPerfil(getattr(vb, aspecto.value),
                                b.respaldo_variable if getattr(vb, aspecto.value) is not None else Respaldo()), clave)
            elif aspecto is A.UNIDAD:
                ua, ub = a.unidad, b.unidad
                if U.CONTRADICTORIA in (ua.estado, ub.estado):
                    anotar("unidad_con_evidencia_contradictoria_aportada", clave, N.CONTRADICCION)
                elif any(u.estado in (U.DESCONOCIDA, U.DECLARADA) for u in (ua, ub)):
                    anotar("unidad_sin_acreditacion_aportada", clave)
                elif ua.estado != ub.estado or ua.literal != ub.literal:
                    anotar("unidades_distintas_sin_conversion_admitida", clave, N.CONTRADICCION)
                else:
                    anotar("unidad_literal_o_no_aplicabilidad_coincidente", clave, N.INFORMACION)
            elif aspecto is A.DIMENSION_FISICA:
                if a.unidad.estado is b.unidad.estado is U.NO_APLICABLE:
                    anotar("dimension_no_aplicable_documentada", clave, N.INFORMACION)
                else:
                    literal(a.unidad.dimension_fisica, b.unidad.dimension_fisica, clave)
            elif aspecto is A.AUSENTES:
                if (a.valores_ausentes is None or b.valores_ausentes is None
                        or a.respaldo_ausentes.estado is not V.VERIFICADO
                        or b.respaldo_ausentes.estado is not V.VERIFICADO):
                    anotar("convencion_ausentes_no_documentada", clave)
                elif frozenset(a.valores_ausentes) != frozenset(b.valores_ausentes):
                    anotar("convenciones_ausentes_distintas", clave, N.CONTRADICCION)
                else:
                    anotar("convenciones_ausentes_coincidentes_sin_reemplazo", clave, N.INFORMACION)

    aptitud = None
    if finalidad.referencias is not None:
        if ra is None or rb is None:
            anotar("referencias_sin_recurso", "referencias")
        else:
            aptitud = evaluar_aptitud(ra, rb, finalidad.referencias)
            nivel = (N.INFORMACION if aptitud.estado is E.APTO_ESTRUCTURALMENTE else
                     N.CONTRADICCION if aptitud.estado is E.INCOMPATIBLE else N.FALTANTE)
            for motivo in aptitud.motivos + aptitud.faltantes + aptitud.contradicciones:
                anotar(motivo, "referencias", nivel)
            # Para alineación literal RC2, resoluciones distintas acreditadas
            # son incompatibles; el evaluador previo conserva su diagnóstico nativo.
            if finalidad.referencias in (D.TEMPORAL, D.AMBAS) and ra.temporal and rb.temporal:
                ta, tb = ra.temporal, rb.temporal
                if (ta.respaldo_interpretacion.estado is tb.respaldo_interpretacion.estado is V.VERIFICADO
                        and ta.resolucion is not None and tb.resolucion is not None and ta.resolucion != tb.resolucion):
                    anotar("resoluciones_temporales_distintas_sin_agregacion", "referencias", N.CONTRADICCION)
    if finalidad.requiere_mismo_sitio:
        ma, mb = (r.espacial if r is not None else None for r in recursos)
        if any(m is None or m.identificador_ubicacion is None or m.identidad_ambigua
               or m.respaldo_identidad.estado is not V.VERIFICADO for m in (ma, mb)):
            anotar("identidad_sitio_sin_respaldo", "sitio")
        elif ((ra.identidad.fuente, ra.identidad.producto_id, ma.identificador_ubicacion)
              != (rb.identidad.fuente, rb.identidad.producto_id, mb.identificador_ubicacion)):
            anotar("identidades_sitio_distintas_sin_correspondencia", "sitio", N.CONTRADICCION)
        else:
            anotar("identidad_sitio_literal_con_respaldo", "sitio", N.INFORMACION)
    anotar("alcance_limitado_a_finalidad_y_aspectos_declarados", "finalidad", N.INFORMACION)
    return ResultadoCompatibilidad(primero, segundo, finalidad, tuple(ds), restricciones, aptitud, operacion)
