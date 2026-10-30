"""PASO 80: evidencia inventada en memoria, sin abrir RAW ni SQLite."""

from contextlib import ExitStack
from dataclasses import FrozenInstanceError, replace
from datetime import date, datetime, timedelta, timezone
import hashlib
from itertools import permutations
from pathlib import Path
import socket
import sqlite3
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from spica.adquisicion.almacenamiento import ActivoRAW, AlmacenRAW, DeclaracionRAW, EstadoIncorporacion
from spica.adquisicion.catalogo import EvidenciaAdquisicion, EvidenciaDocumental, MecanismoAdquisicion, ProcedenciaCatalogo
from spica.adquisicion.integracion import AdaptadorHTTPRAW
from spica.adquisicion.manual import DocumentoManual, FundamentoUsoManual, ProcedenciaManual, ReciboIngestaManual
from spica.adquisicion.nucleo import EstadoDescarga, Fuente
from spica.adquisicion.readquisicion import (
    AntecedenteAdquisicion, Decision, EstadoActualizacion, EstadoLocal, EvidenciaActualizacion,
    EvidenciaLocal, IdentidadRecurso, IndiciosHTTP, ModoConsulta, PoliticaReadquisicion,
    RelacionActualizacion, RestriccionesAcceso, SolicitudDecision, UsoPrevisto,
    antecedente_desde_raw, decidir_readquisicion,
)
from spica.adquisicion.transportes import ClienteHTTP


class ReadquisicionTests(unittest.TestCase):
    def setUp(self):
        self.ahora = datetime(2026, 10, 30, 12, tzinfo=timezone.utc)
        self.procedencia = ProcedenciaCatalogo("urn:fixture:evidencia", self.ahora - timedelta(minutes=1),
                                              "fixture_sintetico", "declaracion exclusivamente sintetica")
        self.identidad = IdentidadRecurso(" Proyecto/01 ", "Objeto-01", " Recurso/01 ",
                                          Fuente("Proveedor-sintetico", " Fuente/01 "), " Producto/01 ")
        self.mecanismo = MecanismoAdquisicion.HTTP_DIRECTO
        self.restricciones = RestriccionesAcceso(self.identidad, self.mecanismo, self.procedencia,
                                                permite_adquirir=True, permite_reutilizar=True)
        self.sha = hashlib.sha256(b"fixture sin datos reales").hexdigest()
        self.local = EvidenciaLocal(EstadoLocal.INTEGRO, self.ahora - timedelta(minutes=1),
                                    self.procedencia, self.sha, 23, activo_id="b" * 32)
        self.anterior = AntecedenteAdquisicion(self.identidad, self.procedencia,
            adquisicion_id="a" * 32, activo_id="b" * 32, mecanismo=self.mecanismo,
            estado_raw=EstadoIncorporacion.INCORPORADA, estado_descarga=EstadoDescarga.COMPLETA,
            fecha_adquisicion=self.ahora - timedelta(days=1), sha256_catalogado=self.sha,
            size_bytes_catalogado=23, local=self.local, version_recurso="edicion-original")

    def solicitud(self, antecedentes=(), **kwargs):
        datos = dict(identidad=self.identidad, mecanismo=self.mecanismo, evaluada_utc=self.ahora,
                     antecedentes=antecedentes, historial_completo=True, restricciones=self.restricciones)
        datos.update(kwargs)
        return SolicitudDecision(**datos)

    def decidir(self, antecedentes=(), **kwargs):
        r = decidir_readquisicion(self.solicitud(antecedentes, **kwargs))
        self.assertFalse(r.autoriza_red)
        self.assertFalse(r.vigencia_remota_comprobada)
        if r.decision is not Decision.REUTILIZAR_LOCAL:
            self.assertEqual(r.activos_reutilizables, ())
        return r

    def actualizacion(self, **kwargs):
        datos = dict(identidad=self.identidad, mecanismo=self.mecanismo, procedencia=self.procedencia,
                     relacion=RelacionActualizacion.POSTERIOR_DOCUMENTADA,
                     adquisicion_base_id=self.anterior.adquisicion_id,
                     version_previa=self.anterior.version_recurso, version_nueva="edicion-posterior")
        datos.update(kwargs)
        return EvidenciaActualizacion(**datos)

    def test_recurso_nuevo_recomienda_inicial_con_controles_pendientes(self):
        r = self.decidir(restricciones=None)
        self.assertEqual(r.decision, Decision.ADQUISICION_INICIAL)
        self.assertIn("permiso_de_adquisicion_documentado_para_este_alcance", r.informacion_faltante)
        self.assertIn("comprobar_mecanismo_y_acceso_actuales", r.informacion_faltante)

    def test_historial_vacio_no_exhaustivo_no_demuestra_recurso_nuevo(self):
        r = self.decidir(historial_completo=False)
        self.assertEqual(r.decision, Decision.EVIDENCIA_INSUFICIENTE)
        self.assertIn("historial_exhaustivo_del_recurso", r.informacion_faltante)

    def test_copia_integra_reutilizable_sin_afirmar_vigencia_remota(self):
        r = self.decidir((self.anterior,))
        self.assertEqual(r.decision, Decision.REUTILIZAR_LOCAL)
        self.assertEqual(r.activos_reutilizables, (self.anterior.activo_id,))
        self.assertEqual(r.estado_actualizacion, EstadoActualizacion.DESCONOCIDO)
        self.assertEqual(r.solicitud.identidad.recurso_id, " Recurso/01 ")

    def test_version_posterior_documentada_recomienda_nueva_sin_autorizar(self):
        r = self.decidir((self.anterior,), actualizaciones=(self.actualizacion(),))
        self.assertEqual(r.decision, Decision.RECOMENDAR_NUEVA)
        self.assertEqual(r.estado_actualizacion, EstadoActualizacion.DOCUMENTADA)
        self.assertEqual(len(r.solicitud.antecedentes), 1)

    def test_documentacion_sin_version_no_inventa_orden(self):
        r = self.decidir((replace(self.anterior, version_recurso=None),),
                         actualizaciones=(self.actualizacion(version_nueva=None),),
                         politica=PoliticaReadquisicion(ModoConsulta.EXIGIR_VIGENCIA))
        self.assertEqual(r.decision, Decision.EVIDENCIA_INSUFICIENTE)
        self.assertIn("relacion_de_versiones_con_una_adquisicion_base", r.informacion_faltante)

    def test_versiones_opacas_no_se_ordenan_numericamente(self):
        anterior = replace(self.anterior, version_recurso="v10")
        e = self.actualizacion(version_previa="v10", version_nueva="v2")
        r = self.decidir((anterior,), actualizaciones=(e,))
        self.assertEqual(r.decision, Decision.RECOMENDAR_NUEVA)
        self.assertEqual(r.estado_actualizacion, EstadoActualizacion.DOCUMENTADA)

    def test_version_distinta_sin_relacion_documentada_no_basta(self):
        e = self.actualizacion(relacion=RelacionActualizacion.DESCONOCIDA)
        r = self.decidir((self.anterior,), actualizaciones=(e,))
        self.assertEqual(r.decision, Decision.REUTILIZAR_LOCAL)
        self.assertEqual(r.estado_actualizacion, EstadoActualizacion.DESCONOCIDO)

    def test_misma_version_declarada_no_prueba_igualdad_ni_vigencia(self):
        e = self.actualizacion(relacion=RelacionActualizacion.MISMA_VERSION_DECLARADA,
                               version_nueva=self.anterior.version_recurso)
        r = self.decidir((self.anterior,), actualizaciones=(e,),
                         politica=PoliticaReadquisicion(ModoConsulta.EXIGIR_VIGENCIA))
        self.assertEqual(r.decision, Decision.EVIDENCIA_INSUFICIENTE)
        self.assertIn("misma_version_declarada_no_prueba_igualdad_de_bytes", r.limitaciones)

    def test_actualizacion_sin_fundamento_no_se_aprueba(self):
        e = self.actualizacion(procedencia=replace(self.procedencia, evidencia=None))
        r = self.decidir((self.anterior,), actualizaciones=(e,))
        self.assertEqual(r.decision, Decision.REUTILIZAR_LOCAL)
        self.assertEqual(r.estado_actualizacion, EstadoActualizacion.DESCONOCIDO)
        self.assertIn("fundamento_de_relacion_documental", r.informacion_faltante)

    def test_actualizacion_sin_base_identificada_conserva_incertidumbre(self):
        r = self.decidir((self.anterior,), actualizaciones=(self.actualizacion(adquisicion_base_id=None),))
        self.assertEqual(r.estado_actualizacion, EstadoActualizacion.DESCONOCIDO)
        self.assertIn("relacion_de_versiones_con_una_adquisicion_base", r.informacion_faltante)

    def test_version_posterior_ya_adquirida_no_recomienda_descarga_redundante(self):
        nuevo = replace(self.anterior, adquisicion_id="c" * 32, activo_id="d" * 32,
                         version_recurso="edicion-posterior", local=replace(self.local, activo_id="d" * 32))
        r = self.decidir((self.anterior, nuevo), actualizaciones=(self.actualizacion(),))
        self.assertEqual(r.decision, Decision.REUTILIZAR_LOCAL)
        self.assertEqual(r.activos_reutilizables, (nuevo.activo_id,))

    def test_otra_version_local_no_se_supone_anterior_ni_se_degrada(self):
        otro = replace(self.anterior, adquisicion_id="c" * 32, activo_id="d" * 32, version_recurso="otra-edicion",
                        local=replace(self.local, activo_id="d" * 32))
        r = self.decidir((self.anterior, otro), actualizaciones=(self.actualizacion(),))
        self.assertEqual(r.decision, Decision.REVISION_MANUAL)
        self.assertIn("version_local_no_comparable_con_actualizacion", r.justificacion)

    def test_varias_versiones_posteriores_no_se_ordenan_por_etiqueta(self):
        r = self.decidir((self.anterior,), actualizaciones=(self.actualizacion(), self.actualizacion(version_nueva="tercera")))
        self.assertEqual(r.decision, Decision.REVISION_MANUAL)
        self.assertEqual(r.estado_actualizacion, EstadoActualizacion.DOCUMENTADA)
        self.assertIn("versiones_posteriores_sin_orden_documentado", r.justificacion)

    def test_sin_comprobacion_local_el_hash_catalogado_no_es_prueba_fisica(self):
        r = self.decidir((replace(self.anterior, local=EvidenciaLocal()),))
        self.assertEqual(r.decision, Decision.EVIDENCIA_INSUFICIENTE)
        self.assertIn("comprobacion_fisica_local_disponible", r.informacion_faltante)

    def test_hash_observado_contradictorio_impide_reutilizacion(self):
        a = replace(self.anterior, local=replace(self.local, sha256_observado="0" * 64))
        r = self.decidir((a,))
        self.assertEqual(r.decision, Decision.REVISION_MANUAL)
        self.assertIn("evidencia_local_contradice_catalogo", r.justificacion)

    def test_tamano_observado_contradictorio_impide_reutilizacion(self):
        r = self.decidir((replace(self.anterior, local=replace(self.local, size_bytes_observado=24)),))
        self.assertEqual(r.decision, Decision.REVISION_MANUAL)

    def test_comprobacion_de_otro_activo_no_demuestra_copia_local_aunque_comparta_hash(self):
        local = replace(self.local, activo_id="c" * 32)
        r = self.decidir((replace(self.anterior, local=local),))
        self.assertEqual(r.decision, Decision.REVISION_MANUAL)
        self.assertIn("comprobacion_local_de_otro_activo", r.justificacion)

    def test_metadatos_catalogados_incompletos_no_se_completan_con_supuestos(self):
        a = replace(self.anterior, sha256_catalogado=None, size_bytes_catalogado=None)
        r = self.decidir((a,))
        self.assertEqual(r.decision, Decision.EVIDENCIA_INSUFICIENTE)
        self.assertIn("tamano_y_sha256_catalogados", r.informacion_faltante)

    def test_fechas_con_desplazamientos_equivalentes_producen_la_misma_decision(self):
        evaluada = self.ahora.astimezone(timezone(timedelta(hours=-5)))
        self.assertEqual(self.decidir((self.anterior,)), self.decidir((self.anterior,), evaluada_utc=evaluada))

    def test_copia_local_inconsistente_no_se_repara(self):
        local = EvidenciaLocal(EstadoLocal.INCONSISTENTE, self.local.comprobada_utc, self.procedencia, activo_id="b" * 32)
        r = self.decidir((replace(self.anterior, local=local, estado_raw=EstadoIncorporacion.INCONSISTENTE),))
        self.assertEqual(r.decision, Decision.REVISION_MANUAL)

    def test_ausencia_comprobada_no_se_confunde_con_integridad_desconocida(self):
        local = EvidenciaLocal(EstadoLocal.AUSENTE, self.local.comprobada_utc, self.procedencia, activo_id="b" * 32)
        self.assertIs(local.existencia_comprobada, False)
        r = self.decidir((replace(self.anterior, local=local),))
        self.assertEqual(r.decision, Decision.REVISION_MANUAL)

    def test_error_de_comprobacion_no_es_corrupcion_demostrada(self):
        local = EvidenciaLocal(EstadoLocal.NO_DISPONIBLE, self.local.comprobada_utc, self.procedencia, activo_id="b" * 32)
        self.assertIsNone(local.existencia_comprobada)
        self.assertEqual(self.decidir((replace(self.anterior, local=local),)).decision, Decision.EVIDENCIA_INSUFICIENTE)

    def test_descarga_parcial_no_se_presenta_como_completa(self):
        a = replace(self.anterior, estado_descarga=EstadoDescarga.PARCIAL,
                    estado_raw=None, local=EvidenciaLocal())
        r = self.decidir((a,))
        self.assertEqual(r.decision, Decision.REVISION_MANUAL)
        self.assertIn("transferencia_parcial_no_completa", r.justificacion)

    def test_adquisicion_fallida_preserva_su_identidad(self):
        a = replace(self.anterior, estado_descarga=EstadoDescarga.FALLIDA,
                    estado_raw=EstadoIncorporacion.FALLIDA, local=EvidenciaLocal())
        r = self.decidir((a,))
        self.assertEqual(r.decision, Decision.REVISION_MANUAL)
        self.assertEqual(r.solicitud.antecedentes[0].adquisicion_id, a.adquisicion_id)
        self.assertIn("adquisicion_fallida_preservada", r.justificacion)

    def test_interrupcion_no_se_presenta_como_completa(self):
        a = replace(self.anterior, estado_descarga=EstadoDescarga.FALLIDA,
                    estado_raw=EstadoIncorporacion.FALLIDA, interrumpida=True, local=EvidenciaLocal())
        r = self.decidir((a,))
        self.assertEqual(r.decision, Decision.REVISION_MANUAL)
        self.assertIn("antecedente_interrumpido_preservado", r.justificacion)

    def test_raw_preparada_y_verificada_no_equivalen_a_incorporada(self):
        for estado in (EstadoIncorporacion.PREPARADA, EstadoIncorporacion.VERIFICADA):
            with self.subTest(estado=estado):
                r = self.decidir((replace(self.anterior, estado_raw=estado),))
                self.assertEqual(r.decision, Decision.REVISION_MANUAL)

    def test_estado_raw_completo_y_descarga_parcial_son_contradictorios(self):
        r = self.decidir((replace(self.anterior, estado_descarga=EstadoDescarga.PARCIAL),))
        self.assertEqual(r.decision, Decision.REVISION_MANUAL)
        self.assertIn("estados_de_adquisicion_contradictorios", r.justificacion)

    def test_historico_fallido_no_oculta_copia_posterior_integra(self):
        fallido = replace(self.anterior, adquisicion_id="c" * 32, activo_id="d" * 32,
                         estado_descarga=EstadoDescarga.FALLIDA, estado_raw=EstadoIncorporacion.FALLIDA,
                         local=EvidenciaLocal())
        r = self.decidir((fallido, self.anterior))
        self.assertEqual(r.decision, Decision.REUTILIZAR_LOCAL)
        self.assertEqual(r.activos_reutilizables, (self.anterior.activo_id,))
        self.assertEqual(len(r.solicitud.antecedentes), 2)

    def test_multiples_adquisiciones_con_contenido_compartido_no_se_deduplican(self):
        otra = replace(self.anterior, adquisicion_id="c" * 32, activo_id="d" * 32,
                       local=replace(self.local, activo_id="d" * 32))
        r = self.decidir((otra, self.anterior))
        self.assertEqual(len(r.solicitud.antecedentes), 2)
        self.assertEqual(r.activos_reutilizables, tuple(sorted((otra.activo_id, self.anterior.activo_id))))

    def test_ids_duplicados_no_inflan_el_historial_silenciosamente(self):
        r = self.decidir((self.anterior, self.anterior))
        self.assertEqual(r.decision, Decision.REVISION_MANUAL)
        self.assertEqual(len(r.solicitud.antecedentes), 2)

    def test_manual_no_hereda_url_o_actualizacion_http(self):
        manual = replace(self.anterior, mecanismo=MecanismoAdquisicion.MANUAL, estado_descarga=None)
        restricciones = replace(self.restricciones, mecanismo=MecanismoAdquisicion.MANUAL)
        r = self.decidir((manual,), mecanismo=MecanismoAdquisicion.MANUAL, restricciones=restricciones,
                         actualizaciones=(self.actualizacion(),))
        self.assertEqual(r.decision, Decision.REUTILIZAR_LOCAL)
        self.assertEqual(r.estado_actualizacion, EstadoActualizacion.DESCONOCIDO)
        self.assertIn("entrega_manual_sin_comprobacion_remota", r.limitaciones)
        self.assertIsNone(r.solicitud.antecedentes[0].indicios_http)

    def test_url_coincidente_no_identifica_otro_recurso(self):
        indicios = IndiciosHTTP(url_declarada="https://fixture.invalid/recurso")
        otro = replace(self.anterior, identidad=replace(self.identidad, recurso_id="otro"), indicios_http=indicios)
        r = self.decidir((otro,))
        self.assertEqual(r.decision, Decision.ADQUISICION_INICIAL)
        self.assertEqual(len(r.solicitud.antecedentes), 1)

    def test_nombre_coincidente_no_prueba_igualdad(self):
        a = replace(self.anterior, local=EvidenciaLocal(), indicios_http=IndiciosHTTP(nombre_declarado="datos.csv"))
        r = self.decidir((a,))
        self.assertEqual(r.decision, Decision.EVIDENCIA_INSUFICIENTE)

    def test_content_length_coincidente_no_reemplaza_hash_fisico(self):
        a = replace(self.anterior, local=EvidenciaLocal(), indicios_http=IndiciosHTTP(content_length=23))
        e = self.actualizacion(relacion=RelacionActualizacion.DESCONOCIDA, indicios_http=IndiciosHTTP(content_length=23))
        r = self.decidir((a,), actualizaciones=(e,))
        self.assertEqual(r.decision, Decision.EVIDENCIA_INSUFICIENTE)

    def test_etag_debil_no_prueba_igualdad_de_bytes(self):
        i = IndiciosHTTP(etag='W/"fixture"')
        self.assertTrue(i.etag_debil)
        a = replace(self.anterior, local=EvidenciaLocal(), indicios_http=i)
        r = self.decidir((a,), actualizaciones=(self.actualizacion(relacion=RelacionActualizacion.DESCONOCIDA,
                                                                 indicios_http=i),))
        self.assertEqual(r.decision, Decision.EVIDENCIA_INSUFICIENTE)

    def test_etag_fuerte_sin_contexto_de_representacion_no_prueba_vigencia(self):
        i = IndiciosHTTP(etag='"fixture"')
        self.assertFalse(i.etag_debil)
        a = replace(self.anterior, indicios_http=i)
        r = self.decidir((a,), politica=PoliticaReadquisicion(ModoConsulta.EXIGIR_VIGENCIA),
                         actualizaciones=(self.actualizacion(relacion=RelacionActualizacion.DESCONOCIDA, indicios_http=i),))
        self.assertEqual(r.decision, Decision.EVIDENCIA_INSUFICIENTE)

    def test_etag_cambiado_no_se_convierte_en_version_cientifica(self):
        a = replace(self.anterior, indicios_http=IndiciosHTTP(etag='"anterior"'))
        e = self.actualizacion(relacion=RelacionActualizacion.DESCONOCIDA, indicios_http=IndiciosHTTP(etag='"nuevo"'))
        r = self.decidir((a,), actualizaciones=(e,))
        self.assertEqual(r.estado_actualizacion, EstadoActualizacion.DESCONOCIDO)

    def test_last_modified_disponible_o_ausente_no_es_fecha_documental(self):
        for fecha in (None, self.ahora - timedelta(hours=1)):
            with self.subTest(fecha=fecha):
                i = IndiciosHTTP(last_modified=fecha)
                a = replace(self.anterior, indicios_http=i)
                r = self.decidir((a,), politica=PoliticaReadquisicion(ModoConsulta.EXIGIR_VIGENCIA))
                self.assertEqual(r.decision, Decision.EVIDENCIA_INSUFICIENTE)
                self.assertIsNone(r.solicitud.antecedentes[0].fecha_documental)

    def test_evidencia_contradictoria_exige_revision(self):
        r = self.decidir((self.anterior,), actualizaciones=(self.actualizacion(relacion=RelacionActualizacion.CONTRADICTORIA),))
        self.assertEqual(r.decision, Decision.REVISION_MANUAL)
        self.assertEqual(r.estado_actualizacion, EstadoActualizacion.CONTRADICTORIO)

    def test_posterior_con_misma_version_y_base_distinta_son_contradicciones(self):
        for e in (self.actualizacion(version_nueva=self.anterior.version_recurso),
                  self.actualizacion(version_previa="no_coincide"),
                  self.actualizacion(relacion=RelacionActualizacion.MISMA_VERSION_DECLARADA)):
            with self.subTest(e=e):
                r = self.decidir((self.anterior,), actualizaciones=(e,))
                self.assertEqual(r.decision, Decision.REVISION_MANUAL)
                self.assertEqual(r.estado_actualizacion, EstadoActualizacion.CONTRADICTORIO)

    def test_cambio_y_permanencia_incompatibles_para_misma_base_y_fecha(self):
        misma = self.actualizacion(relacion=RelacionActualizacion.MISMA_VERSION_DECLARADA,
                                   version_nueva=self.anterior.version_recurso)
        r = self.decidir((self.anterior,), actualizaciones=(self.actualizacion(), misma))
        self.assertEqual(r.decision, Decision.REVISION_MANUAL)
        self.assertEqual(r.estado_actualizacion, EstadoActualizacion.CONTRADICTORIO)

    def test_adquisicion_con_permiso_negativo_se_bloquea(self):
        r = self.decidir(restricciones=replace(self.restricciones, permite_adquirir=False))
        self.assertEqual(r.decision, Decision.BLOQUEADA)

    def test_reutilizacion_con_permiso_negativo_se_bloquea(self):
        r = self.decidir((self.anterior,), restricciones=replace(self.restricciones, permite_reutilizar=False))
        self.assertEqual(r.decision, Decision.BLOQUEADA)

    def test_reutilizacion_sin_permiso_no_lo_inventa_de_la_integridad(self):
        r = self.decidir((self.anterior,), restricciones=None)
        self.assertEqual(r.decision, Decision.REVISION_MANUAL)

    def test_permiso_positivo_sin_evidencia_no_es_autorizacion(self):
        restricciones = replace(self.restricciones, procedencia=replace(self.procedencia, evidencia=None))
        r = self.decidir((self.anterior,), restricciones=restricciones)
        self.assertEqual(r.decision, Decision.REVISION_MANUAL)

    def test_permiso_de_adquirir_negativo_no_prohibe_reutilizacion_local_autorizada(self):
        r = self.decidir((self.anterior,), restricciones=replace(self.restricciones, permite_adquirir=False))
        self.assertEqual(r.decision, Decision.REUTILIZAR_LOCAL)

    def test_redistribucion_prohibida_no_se_deduce_del_permiso_de_lectura(self):
        r = self.decidir((self.anterior,), uso=UsoPrevisto.REDISTRIBUCION,
                         restricciones=replace(self.restricciones, permite_redistribuir=False))
        self.assertEqual(r.decision, Decision.BLOQUEADA)

    def test_publicacion_desconocida_exige_revision(self):
        self.assertEqual(self.decidir((self.anterior,), uso=UsoPrevisto.PUBLICACION).decision, Decision.REVISION_MANUAL)

    def test_prohibicion_historica_de_redistribucion_no_se_sobrescribe(self):
        a = replace(self.anterior, permite_redistribuir_historico=False)
        r = self.decidir((a,), uso=UsoPrevisto.REDISTRIBUCION,
                         restricciones=replace(self.restricciones, permite_redistribuir=True))
        self.assertEqual(r.decision, Decision.BLOQUEADA)

    def test_condiciones_textuales_no_se_ejecutan_ni_se_suponen_cumplidas(self):
        r = self.decidir((self.anterior,), restricciones=replace(self.restricciones,
                         condiciones=("revisar condicion declarada",)))
        self.assertEqual(r.decision, Decision.REVISION_MANUAL)
        a = replace(self.anterior, restricciones_historicas=("solo uso autorizado declarado",))
        self.assertEqual(self.decidir((a,)).decision, Decision.REVISION_MANUAL)

    def test_actualizacion_explicita_conserva_antecedentes_y_controles(self):
        r = self.decidir((self.anterior,), politica=PoliticaReadquisicion(ModoConsulta.SOLICITAR_NUEVA))
        self.assertEqual(r.decision, Decision.RECOMENDAR_NUEVA)
        self.assertEqual(r.solicitud.antecedentes, (self.anterior,))
        self.assertIn("autorizacion_operativa_independiente", r.informacion_faltante)

    def test_actualizacion_explicita_sin_permiso_no_elude_bloqueo(self):
        r = self.decidir((self.anterior,), politica=PoliticaReadquisicion(ModoConsulta.SOLICITAR_NUEVA),
                         restricciones=replace(self.restricciones, permite_adquirir=False))
        self.assertEqual(r.decision, Decision.BLOQUEADA)

    def test_solicitar_nueva_con_historial_incompleto_no_afirma_primera_adquisicion(self):
        r = self.decidir(historial_completo=False, politica=PoliticaReadquisicion(ModoConsulta.SOLICITAR_NUEVA))
        self.assertEqual(r.decision, Decision.RECOMENDAR_NUEVA)

    def test_no_reutiliza_autorizacion_de_otro_proyecto_producto_o_institucion(self):
        for identidad in (replace(self.identidad, proyecto_id="otro"), replace(self.identidad, producto_id="otro"),
                          replace(self.identidad, fuente=Fuente("otra", "fuente"))):
            with self.subTest(identidad=identidad):
                r = self.decidir((self.anterior,), restricciones=replace(self.restricciones, identidad=identidad))
                self.assertEqual(r.decision, Decision.REVISION_MANUAL)

    def test_fuente_o_producto_desconocido_no_es_comodin(self):
        for identidad in (replace(self.identidad, fuente=None), replace(self.identidad, producto_id=None)):
            a = replace(self.anterior, identidad=identidad)
            r = self.decidir((a,))
            self.assertEqual(r.decision, Decision.ADQUISICION_INICIAL)
            self.assertIn("antecedentes_o_evidencias_fuera_de_alcance_no_aplicados", r.limitaciones)

    def test_actualizacion_de_otro_proyecto_no_es_evidencia_aplicable(self):
        e = self.actualizacion(identidad=replace(self.identidad, proyecto_id="otro"))
        r = self.decidir((self.anterior,), actualizaciones=(e,))
        self.assertEqual(r.estado_actualizacion, EstadoActualizacion.DESCONOCIDO)

    def test_comprobacion_antigua_respeta_politica_configurable(self):
        local = replace(self.local, comprobada_utc=self.ahora - timedelta(hours=25))
        a = replace(self.anterior, fecha_adquisicion=self.ahora - timedelta(days=2), local=local)
        self.assertEqual(self.decidir((a,)).decision, Decision.EVIDENCIA_INSUFICIENTE)
        self.assertEqual(self.decidir((a,), politica=PoliticaReadquisicion(antiguedad_maxima_local=None)).decision,
                         Decision.REUTILIZAR_LOCAL)

    def test_limite_exacto_de_antiguedad_y_archivo_vacio_son_admitidos(self):
        sha = hashlib.sha256(b"").hexdigest()
        local = replace(self.local, comprobada_utc=self.ahora - timedelta(hours=24),
                        sha256_observado=sha, size_bytes_observado=0)
        a = replace(self.anterior, sha256_catalogado=sha, size_bytes_catalogado=0, local=local)
        self.assertEqual(self.decidir((a,)).decision, Decision.REUTILIZAR_LOCAL)

    def test_evidencia_del_futuro_y_comprobacion_anterior_a_ingesta_no_se_aceptan(self):
        for a in (replace(self.anterior, local=replace(self.local, comprobada_utc=self.ahora + timedelta(seconds=1))),
                  replace(self.anterior, fecha_incorporacion_raw=self.ahora)):
            with self.subTest(a=a):
                self.assertEqual(self.decidir((a,)).decision, Decision.REVISION_MANUAL)

    def test_determinismo_independiente_del_orden_de_antecedentes(self):
        otros = (self.anterior, replace(self.anterior, adquisicion_id="c" * 32, activo_id="d" * 32,
                                       local=replace(self.local, activo_id="d" * 32)),
                 replace(self.anterior, adquisicion_id="e" * 32, activo_id="f" * 32,
                         local=replace(self.local, activo_id="f" * 32)))
        esperado = self.decidir(otros)
        for orden in permutations(otros):
            self.assertEqual(self.decidir(orden), esperado)

    def test_determinismo_orden_de_evidencias_y_evaluacion_repetida(self):
        evidencias = (self.actualizacion(), self.actualizacion(version_nueva="tercera"))
        a = self.decidir((self.anterior,), actualizaciones=evidencias)
        b = self.decidir((self.anterior,), actualizaciones=tuple(reversed(evidencias)))
        self.assertEqual(a, b)
        self.assertEqual(decidir_readquisicion(a.solicitud), a)

    def test_motor_y_proyeccion_no_realizan_io_red_ni_escrituras_sqlite(self):
        d = DeclaracionRAW(self.identidad.proyecto_id, self.identidad.objeto_id,
                           self.identidad.fuente, self.identidad.recurso_id)
        activo = ActivoRAW("b" * 32, d, self.anterior.fecha_adquisicion,
            EstadoIncorporacion.INCORPORADA, 23, self.sha, "sha256/fixture", None, (), self.local.comprobada_utc)
        objetivos = ("builtins.open", "os.open", "sqlite3.connect", "socket.getaddrinfo")
        with ExitStack() as stack:
            mocks = [stack.enter_context(patch(p, side_effect=AssertionError("I/O prohibida"))) for p in objetivos]
            for tipo, metodo in ((Path, "open"), (socket.socket, "connect"), (AlmacenRAW, "verificar"),
                                  (AlmacenRAW, "recuperar"), (AlmacenRAW, "metadatos"),
                                  (ClienteHTTP, "get"), (ClienteHTTP, "descargar"), (AdaptadorHTTPRAW, "adquirir")):
                mocks.append(stack.enter_context(patch.object(tipo, metodo, side_effect=AssertionError("operacion prohibida"))))
            self.decidir((self.anterior,))
            normalizado = antecedente_desde_raw(activo, self.procedencia)
            self.assertEqual(normalizado.local.estado, EstadoLocal.DESCONOCIDO)
            for m in mocks:
                m.assert_not_called()

    def test_salida_y_entrada_inmutables_versionadas_y_sin_orden_ejecutable(self):
        r = self.decidir((self.anterior,))
        self.assertEqual((r.version_contrato, r.solicitud.version_contrato, r.version_motor), ("1", "1", "1.0.0"))
        with self.assertRaises(FrozenInstanceError):
            r.decision = Decision.RECOMENDAR_NUEVA
        with self.assertRaises((TypeError, ValueError)):
            replace(r, autoriza_red=True)
        self.assertFalse(hasattr(r, "ejecutar"))

    def test_contratos_rechazan_metadatos_sensibles_y_rutas(self):
        for kwargs in ({"url_declarada": "https://usuario:CLAVE_SINTETICA@fixture.invalid/a"},
                       {"nombre_declarado": r"C:\privado\archivo.csv"}):
            with self.subTest(kwargs=kwargs), self.assertRaises(Exception) as c:
                IndiciosHTTP(**kwargs)
            self.assertNotIn("CLAVE_SINTETICA", str(c.exception))
        with self.assertRaises(Exception) as c:
            replace(self.identidad, recurso_id="token=SECRETO_SINTETICO")
        self.assertNotIn("SECRETO_SINTETICO", str(c.exception))

    def test_contratos_rechazan_configuracion_ambigua_o_mutable(self):
        for crear in (lambda: EvidenciaLocal(EstadoLocal.INTEGRO),
                      lambda: replace(self.local, size_bytes_observado=True),
                      lambda: IndiciosHTTP(content_length=-1), lambda: IndiciosHTTP(etag="sin-comillas"),
                      lambda: IndiciosHTTP(last_modified=datetime(2020, 1, 1)),
                      lambda: replace(self.anterior, mecanismo=MecanismoAdquisicion.MANUAL,
                                      estado_descarga=None, indicios_http=IndiciosHTTP()),
                      lambda: PoliticaReadquisicion(antiguedad_maxima_local=timedelta(seconds=-1)),
                      lambda: self.solicitud(antecedentes=[self.anterior]),
                      lambda: self.solicitud(evaluada_utc=datetime(2020, 1, 1)),
                      lambda: PoliticaReadquisicion(modo="__import__('os')")):
            with self.subTest(crear=crear), self.assertRaises((TypeError, ValueError)):
                crear()


class ProyeccionRAWTests(unittest.TestCase):
    def setUp(self):
        self.fecha = datetime(2026, 10, 29, 12, tzinfo=timezone.utc)
        self.procedencia = ProcedenciaCatalogo("urn:fixture:instantanea", self.fecha, "fixture", "solo datos inventados")
        self.fuente = Fuente("SPICA", "recepcion-manual-local")
        self.declaracion = DeclaracionRAW("p", "o", self.fuente, "r")
        self.sha = hashlib.sha256(b"inventado").hexdigest()
        self.activo = ActivoRAW("b" * 32, self.declaracion, self.fecha, EstadoIncorporacion.INCORPORADA,
                                9, self.sha, "sha256/inventado", None, (), self.fecha)
        self.manual = ReciboIngestaManual("a" * 32, self.activo, ProcedenciaManual(
            fundamento=FundamentoUsoManual(DocumentoManual("urn:fixture:permiso", "revision-permiso-1", date(2026, 1, 1)),
                                          True, False, False), fecha_recepcion=date(2026, 10, 28)))

    def test_recibo_manual_preserva_desconocidos_sin_inventar_http(self):
        a = antecedente_desde_raw(self.activo, self.procedencia, evidencia=self.manual)
        self.assertEqual(a.mecanismo, MecanismoAdquisicion.MANUAL)
        self.assertEqual(a.adquisicion_id, self.manual.adquisicion_id)
        self.assertIsNone(a.identidad.fuente)
        self.assertIsNone(a.indicios_http)
        self.assertIsNone(a.estado_descarga)
        self.assertEqual(a.fecha_recepcion_civil, date(2026, 10, 28))
        self.assertEqual(a.local.estado, EstadoLocal.DESCONOCIDO)

    def test_version_de_permiso_no_se_convierte_en_version_del_recurso(self):
        a = antecedente_desde_raw(self.activo, self.procedencia, evidencia=self.manual)
        self.assertEqual(a.version_documental, "revision-permiso-1")
        self.assertIsNone(a.version_recurso)
        self.assertEqual(a.fecha_documental, date(2026, 1, 1))
        self.assertIsNone(a.fecha_observacion)
        self.assertFalse(a.permite_redistribuir_historico)

    def test_sin_recibo_no_inventa_adquisicion_ni_mecanismo_de_una_url(self):
        activo = replace(self.activo, declaracion=replace(self.declaracion, procedencia="https://fixture.invalid/recurso"))
        a = antecedente_desde_raw(activo, self.procedencia)
        self.assertIsNone(a.adquisicion_id)
        self.assertIsNone(a.mecanismo)
        self.assertIsNone(a.indicios_http)
        self.assertIsNone(a.fecha_adquisicion)
        self.assertEqual(a.fecha_incorporacion_raw, self.fecha)

    def test_http_reutiliza_evidencia_v1_sin_inventar_etag_o_version(self):
        doc = EvidenciaDocumental(self.fuente, "r", revision_documental=17)
        evidencia = EvidenciaAdquisicion("a" * 32, self.activo.asset_id, doc, "https://fixture.invalid/recurso",
            False, self.fecha - timedelta(seconds=2), (MecanismoAdquisicion.HTTP_DIRECTO,),
            self.sha, 9, self.activo.estado.value)
        a = antecedente_desde_raw(self.activo, self.procedencia, evidencia=evidencia)
        self.assertEqual(a.mecanismo, MecanismoAdquisicion.HTTP_DIRECTO)
        self.assertEqual(a.fecha_adquisicion, evidencia.http_comprobada_utc)
        self.assertEqual(a.fecha_incorporacion_raw, self.fecha)
        self.assertIsNone(a.version_recurso)
        self.assertIsNone(a.version_documental)
        self.assertIsNone(a.indicios_http.etag)
        self.assertIsNone(a.fecha_documental)

    def test_evidencia_de_otro_activo_rechazada(self):
        recibo = replace(self.manual, activo=replace(self.activo, activo_id="c" * 32))
        with self.assertRaises(ValueError):
            antecedente_desde_raw(self.activo, self.procedencia, evidencia=recibo)

    def test_comprobacion_local_solo_se_incluye_cuando_se_aporta_explicitamente(self):
        local = EvidenciaLocal(EstadoLocal.INTEGRO, self.fecha, self.procedencia, self.sha, 9, activo_id=self.activo.asset_id)
        a = antecedente_desde_raw(self.activo, self.procedencia, evidencia=self.manual,
                                  local=local, version_recurso="edicion-declarada")
        self.assertIs(a.local, local)
        self.assertEqual(a.version_recurso, "edicion-declarada")

    def test_estado_fallido_e_interrupcion_se_preservan(self):
        activo = replace(self.activo, estado=EstadoIncorporacion.FALLIDA, error="interrumpida")
        a = antecedente_desde_raw(activo, self.procedencia)
        self.assertEqual(a.estado_raw, EstadoIncorporacion.FALLIDA)
        self.assertTrue(a.interrumpida)
        self.assertEqual(a.local.estado, EstadoLocal.DESCONOCIDO)


if __name__ == "__main__":
    unittest.main()
