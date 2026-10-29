"""Construye propuestas acotadas sin ejecutar mecanismos de adquisición."""

from ..catalogo import (
    CatalogoCientifico, FiltroCatalogo, ProductoCatalogo, VariableCatalogo,
    DisponibilidadCatalogo, CapacidadCatalogo, EstadoVerificacion, ErrorCatalogo,
)
from ..catalogo.persistencia import _publico
from .evaluacion import evaluar_intervalo, vacios
from .modelos import (
    SolicitudCientifica, LimitesPlanificacion, LimitePlanificacion,
    EstadoPreparacion, SituacionTemporal, TramoTemporal, EvaluacionProducto,
    OperacionPlanificada, PlanConsulta, ErrorPlanificacion,
)


class Planificador:
    def __init__(self, catalogo: CatalogoCientifico, limites: LimitesPlanificacion = LimitesPlanificacion()):
        if not isinstance(catalogo, CatalogoCientifico) or not isinstance(limites, LimitesPlanificacion):
            raise TypeError("Catalogo y limites tipados requeridos")
        self.catalogo, self.limites = catalogo, limites

    def _validar(self, solicitud):
        if not isinstance(solicitud, SolicitudCientifica):
            raise TypeError("Se requiere SolicitudCientifica")
        l = self.limites
        if len(solicitud.consultas) > l.max_consultas:
            raise LimitePlanificacion("limite_consultas_excedido")
        elementos, volumen = 0, 0
        textos = [solicitud.identificador]
        for c in solicitud.consultas:
            s = c.solicitud
            elementos += len(s.estaciones) + len(s.variables) + len(s.parametros_proveedor)
            if elementos > l.max_elementos_solicitud:
                raise LimitePlanificacion("limite_selectores_excedido")
            textos.extend((s.fuente.proveedor, s.fuente.identificador, c.producto_id, c.frecuencia))
            textos.extend(s.estaciones)
            textos.extend(s.variables)
            for clave, valor in s.parametros_proveedor.items():
                textos.extend((clave, valor))
                if len(clave) + len(valor) > l.max_bytes_solicitud:
                    raise LimitePlanificacion("limite_bytes_solicitud_excedido")
                # La clave aislada "api_key" no contiene el separador que
                # necesita el detector común de credenciales.
                textos.append(clave + "=" + valor)
        for texto in textos:
            if texto is not None:
                # len antes de encode impide una asignación adicional desproporcionada.
                if len(texto) > l.max_bytes_solicitud:
                    raise LimitePlanificacion("limite_bytes_solicitud_excedido")
                volumen += len(texto.encode("utf-8"))
                if volumen > l.max_bytes_solicitud:
                    raise LimitePlanificacion("limite_bytes_solicitud_excedido")
                try:
                    _publico(texto)
                except ErrorCatalogo:
                    raise ErrorPlanificacion("solicitud_no_publica_o_ambigua") from None

    def planificar(self, solicitud: SolicitudCientifica) -> PlanConsulta:
        self._validar(solicitud)
        fuentes = tuple(dict.fromkeys(c.solicitud.fuente for c in solicitud.consultas))
        productos = (() if any(c.producto_id is None for c in solicitud.consultas)
                     else tuple(dict.fromkeys(c.producto_id for c in solicitud.consultas)))
        try:
            registros = self.catalogo.leer_acotado(FiltroCatalogo(fuentes=fuentes, productos=productos),
                max_registros=self.limites.max_registros_catalogo, max_bytes=self.limites.max_bytes_catalogo)
        except ErrorCatalogo as error:
            if str(error) == "limite_lectura_catalogo_excedido":
                raise LimitePlanificacion("limite_catalogo_excedido") from None
            raise
        variables = {r.entidad.id_interno: r.entidad for r in registros if isinstance(r.entidad, VariableCatalogo)}
        por_producto = {}
        for registro in registros:
            e = registro.entidad
            producto = e.identificador if isinstance(e, ProductoCatalogo) else e.producto_id
            por_producto.setdefault((e.fuente, producto), []).append(registro)
        evaluaciones, operaciones, advertencias = [], [], ["sin_ejecutor_institucional", "no_confirma_disponibilidad_ni_completitud"]
        total_intervalos = 0

        def agregar(indice, consulta, producto, estaciones, codigos, tramo, capacidad, pendientes, evidencia):
            if len(operaciones) >= self.limites.max_operaciones:
                raise LimitePlanificacion("limite_operaciones_excedido")
            operaciones.append(OperacionPlanificada(
                f"op-{len(operaciones) + 1:06d}", indice, consulta, producto, estaciones, codigos, tramo,
                capacidad.entidad if capacidad else None,
                EstadoPreparacion.CONDICIONADA if pendientes else EstadoPreparacion.PREPARADA,
                tuple(dict.fromkeys(pendientes)), tuple(evidencia)))

        for indice, consulta in enumerate(solicitud.consultas):
            s = consulta.solicitud
            encontrados = 0
            for (fuente, producto_id), grupo in por_producto.items():
                if fuente != s.fuente or (consulta.producto_id is not None and consulta.producto_id != producto_id):
                    continue
                producto_reg = next((r for r in grupo if isinstance(r.entidad, ProductoCatalogo)), None)
                if producto_reg is None:
                    continue
                encontrados += 1
                producto = producto_reg.entidad
                capacidades = tuple(r for r in grupo if isinstance(r.entidad, CapacidadCatalogo))
                capacidad = next((r for r in capacidades if r.entidad.estado is EstadoVerificacion.VERIFICADO),
                                 capacidades[0] if capacidades else None)
                pendientes_base = []
                avisos = ["cobertura_total_de_la_solicitud_no_garantizada"]
                if capacidad is None:
                    pendientes_base.append("identificar_mecanismo_adquisicion")
                elif capacidad.entidad.estado is not EstadoVerificacion.VERIFICADO:
                    pendientes_base.append("verificar_mecanismo_adquisicion")
                if s.parametros_proveedor:
                    pendientes_base.append("validar_parametros_con_conector")
                if producto.autenticacion_requerida is not False:
                    pendientes_base.append("resolver_requisitos_acceso")
                incompatible = producto.utiliza_estaciones is False and bool(s.estaciones)
                if incompatible:
                    pendientes_base.append("estaciones_incompatibles_con_producto")
                intervalos, asociaciones = [], {}
                antes = len(operaciones)
                for registro in grupo:
                    d = registro.entidad
                    if not isinstance(d, DisponibilidadCatalogo):
                        continue
                    v = variables.get(d.variable_id)
                    codigo = v.codigo_original if v else None
                    if s.estaciones and d.estacion_id is not None and d.estacion_id not in s.estaciones:
                        continue
                    if s.variables and codigo is not None and codigo not in s.variables:
                        continue
                    total_intervalos += 1
                    if total_intervalos > self.limites.max_registros_catalogo:
                        raise LimitePlanificacion("limite_evaluaciones_excedido")
                    ev = evaluar_intervalo(registro, consulta, variables)
                    intervalos.append(ev)
                    if ev.frecuencia_compatible is False:
                        avisos.append("frecuencia_incompatible_sin_conversion")
                    clave = (d.estacion_id, d.variable_id)
                    conocidos = asociaciones.setdefault(clave, [])
                    if (ev.intervalo_aplicable is not None and ev.frecuencia_compatible is True
                            and ev.situacion in (SituacionTemporal.CATALOGADA, SituacionTemporal.PARCIAL)):
                        conocidos.append(ev.intervalo_aplicable)
                    if ev.intervalo_aplicable is None or ev.frecuencia_compatible is False or incompatible:
                        continue
                    pendientes = list(pendientes_base)
                    if d.estado is not EstadoVerificacion.VERIFICADO:
                        pendientes.append("verificar_disponibilidad")
                    if ev.situacion is not SituacionTemporal.CATALOGADA:
                        pendientes.append("comprobar_cobertura_temporal")
                    if not ev.alcance_exacto:
                        pendientes.append("resolver_asociacion_solicitada")
                    if d.variable_id is not None and codigo is None:
                        pendientes.append("identificar_codigo_original_variable")
                    if ev.frecuencia_compatible is None:
                        pendientes.append("identificar_frecuencia")
                    agregar(indice, consulta, producto,
                        (d.estacion_id,) if d.estacion_id else (), (codigo,) if codigo is not None else (),
                        ev.intervalo_aplicable, capacidad, pendientes,
                        (producto_reg, registro) + ((capacidad,) if capacidad else ()))
                desconocidos = []
                for (estacion, variable), conocidos in asociaciones.items():
                    desconocidos.extend((estacion, variable, t) for t in vacios(s.fecha_inicial, s.fecha_final, conocidos))
                if not asociaciones:
                    desconocidos.append((None, None, TramoTemporal(s.fecha_inicial, s.fecha_final)))
                if desconocidos:
                    avisos.append("tramos_desconocidos_no_son_ausencia_documentada")
                if len(operaciones) == antes:
                    # Una propuesta de descubrimiento por producto, sin producto cartesiano.
                    razones = pendientes_base + ["resolver_disponibilidad_solicitada"]
                    if any(ev.frecuencia_compatible is False for ev in intervalos):
                        razones.append("frecuencia_incompatible_sin_conversion")
                    agregar(indice, consulta, producto, s.estaciones, s.variables,
                        TramoTemporal(s.fecha_inicial, s.fecha_final), capacidad, razones,
                        (producto_reg,) + tuple(ev.evidencia for ev in intervalos) + ((capacidad,) if capacidad else ()))
                evaluaciones.append(EvaluacionProducto(indice, consulta, producto_reg, tuple(intervalos),
                    tuple(desconocidos), capacidades, tuple(dict.fromkeys(avisos)),
                    tuple(e for e in s.estaciones if not any(
                        ev.evidencia.entidad.estacion_id == e and ev.alcance_exacto
                        and ev.intervalo_aplicable is not None and ev.estado_evidencia is not EstadoVerificacion.DESCONOCIDO
                        and ev.frecuencia_compatible is True for ev in intervalos)),
                    tuple(c for c in s.variables if not any(
                        variables.get(ev.evidencia.entidad.variable_id) is not None
                        and variables[ev.evidencia.entidad.variable_id].codigo_original == c
                        and ev.alcance_exacto and ev.intervalo_aplicable is not None
                        and ev.estado_evidencia is not EstadoVerificacion.DESCONOCIDO
                        and ev.frecuencia_compatible is True for ev in intervalos))))
                if len(evaluaciones) > self.limites.max_registros_catalogo:
                    raise LimitePlanificacion("limite_productos_evaluados_excedido")
            if not encontrados:
                advertencias.append(f"consulta_{indice}:producto_no_identificado_disponibilidad_desconocida")
        return PlanConsulta(solicitud, tuple(evaluaciones), tuple(operaciones), tuple(advertencias))
