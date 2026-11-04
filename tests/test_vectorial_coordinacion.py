"""Coordinación sin red, persistencia ni fixtures institucionales."""

import ast
from dataclasses import replace
from datetime import timedelta
import gc
from pathlib import Path
import subprocess
import sys
from threading import Event
import tracemalloc
import unittest
from unittest.mock import patch
import weakref

from test_vectorial_featureset import FECHA, consulta, featureset, respuesta
from spica.adquisicion.vectorial import (
    EstadoCompletitud as EC, EstadoPagina as EP, EstrategiaPaginacion as ES,
    EvidenciaConjunto, LimitesVector, SolicitudPagina, TransporteSintetico, coordinar,
)


def evidencia(ids=(1, 2, 3), *, sellada=True, **kw):
    d = dict(huella_consulta=consulta().huella, obtenida_utc=FECHA, referencia="manifest-inventado",
             total=len(ids), object_ids=tuple(ids), ids_obtenidos_utc=FECHA,
             instantanea_id="instantanea-inventada", instantanea_consistente=sellada)
    d.update(kw)
    return EvidenciaConjunto(**d)


def pagina(ids=(1,), *, numero=1, exceso=False, **kw):
    kw.setdefault("instantanea_id", "instantanea-inventada")
    return respuesta(featureset(ids, exceso=exceso), numero=numero, **kw)


class CoordinacionVectorTests(unittest.TestCase):
    def ejecutar(self, paginas, **kw):
        self.transporte = TransporteSintetico(iter(paginas))
        return coordinar(consulta(), self.transporte, tamano_pagina=2, **kw)

    def test_offset_completo_con_ids_y_evidencia_explicita(self):
        r = self.ejecutar([pagina((1, 2), exceso=True), pagina((3,), numero=2)], evidencia=evidencia())
        self.assertEqual(r.completitud, EC.COMPLETA_COMPROBADA)
        self.assertEqual(r.entidades_recibidas, 3)
        self.assertEqual(len(r.recibos), 2)
        self.assertEqual(r.recibos[1].solicitud.parametros["resultOffset"], "2")
        self.assertEqual(r.recibos[1].solicitud.parametros["orderByFields"], "oid ASC")
        self.assertEqual(self.transporte.intentos, 2)

    def test_por_object_ids_conserva_orden_documentado(self):
        r = self.ejecutar([pagina((9, 1)), pagina((7,), numero=2)],
                          evidencia=evidencia((9, 1, 7)), estrategia=ES.OBJECT_IDS)
        self.assertEqual(r.completitud, EC.COMPLETA_COMPROBADA)
        self.assertEqual(r.recibos[0].solicitud.parametros["objectIds"], "9,1")
        self.assertEqual(r.recibos[1].solicitud.parametros["objectIds"], "7")
        self.assertNotIn("resultOffset", r.recibos[0].solicitud.parametros)

    def test_conteo_documentado_y_evidencia_ids(self):
        r = self.ejecutar([pagina((1, 2), exceso=True), pagina((3,), numero=2)],
                          evidencia=evidencia(), estrategia=ES.CONTEO_DOCUMENTADO)
        self.assertEqual(r.completitud, EC.COMPLETA_COMPROBADA)

    def test_conteo_coincidente_solo_no_demuestra_completitud(self):
        e = evidencia((1, 2), object_ids=None, ids_obtenidos_utc=None)
        r = self.ejecutar([pagina((8, 9), total_observado=2)], evidencia=e,
                          estrategia=ES.CONTEO_DOCUMENTADO)
        self.assertEqual(r.completitud, EC.DESCONOCIDA)
        self.assertNotEqual(r.completitud, EC.COMPLETA_COMPROBADA)

    def test_ids_coincidentes_sin_instantanea_no_completan(self):
        r = self.ejecutar([pagina((1, 2))], evidencia=evidencia((1, 2), sellada=False))
        self.assertEqual(r.completitud, EC.DESCONOCIDA)
        self.assertIn("sin_garantia_de_instantanea_consistente", r.limitaciones)

    def test_sin_evidencia_false_no_completa(self):
        r = self.ejecutar([pagina((1,))])
        self.assertEqual(r.completitud, EC.DESCONOCIDA)
        self.assertEqual(r.recibos[0].estado, EP.VALIDA)

    def test_pagina_corta_true_continua_sin_saltar_offset(self):
        r = self.ejecutar([pagina((1,), exceso=True), pagina((2,), numero=2)], evidencia=evidencia((1, 2)))
        self.assertEqual(r.completitud, EC.COMPLETA_COMPROBADA)
        self.assertEqual(r.recibos[1].solicitud.parametros["resultOffset"], "1")
        self.assertIn("pagina_corta_no_demuestra_fin", r.diagnosticos)

    def test_pagina_corta_sin_flag_no_completa(self):
        d = featureset((1,))
        del d["exceededTransferLimit"]
        r = self.ejecutar([respuesta(d)])
        self.assertEqual(r.completitud, EC.PARCIAL)
        self.assertIn("pagina_corta_no_demuestra_fin", r.diagnosticos)

    def test_ids_completos_sin_flag_fin_no_completa(self):
        d = featureset((1, 2))
        del d["exceededTransferLimit"]
        r = self.ejecutar([respuesta(d, instantanea_id="instantanea-inventada")], evidencia=evidencia((1, 2)))
        self.assertNotEqual(r.completitud, EC.COMPLETA_COMPROBADA)

    def test_pagina_completa_en_tamano_no_equivale_a_coleccion(self):
        r = self.ejecutar([pagina((1, 2), exceso=True)])
        self.assertEqual(r.completitud, EC.PARCIAL)

    def test_vacio_documentado_completo_con_pagina_explicita(self):
        r = self.ejecutar([pagina(())], evidencia=evidencia(()))
        self.assertEqual(r.completitud, EC.COMPLETA_COMPROBADA)
        self.assertEqual(r.entidades_recibidas, 0)

    def test_ids_vacios_no_genera_object_ids_ambiguo(self):
        r = self.ejecutar([], evidencia=evidencia(()), estrategia=ES.OBJECT_IDS)
        self.assertEqual(self.transporte.intentos, 0)
        self.assertEqual(r.completitud, EC.DESCONOCIDA)

    def test_pagina_vacia_con_continuacion(self):
        r = self.ejecutar([pagina((), exceso=True)])
        self.assertEqual(r.completitud, EC.INCONSISTENTE)
        self.assertIn("pagina_vacia_con_continuacion", r.diagnosticos)

    def test_pagina_vacia_sin_flag_no_concluye(self):
        d = featureset(())
        del d["exceededTransferLimit"]
        r = self.ejecutar([respuesta(d)])
        self.assertEqual(r.completitud, EC.DESCONOCIDA)

    def test_pagina_repetida_detectada_por_bytes_aun_con_otro_id(self):
        r = self.ejecutar([pagina((1, 2), exceso=True), pagina((1, 2), numero=2, exceso=True)])
        self.assertEqual(r.completitud, EC.INCONSISTENTE)
        self.assertIn("pagina_repetida", r.diagnosticos)

    def test_identidad_respuesta_repetida_con_cuerpo_distinto(self):
        r = self.ejecutar([pagina((1,), exceso=True), replace(pagina((2,), numero=2), respuesta_id="respuesta-1")])
        self.assertIn("pagina_repetida", r.diagnosticos)

    def test_oid_duplicado_entre_paginas(self):
        r = self.ejecutar([pagina((1, 2), exceso=True), pagina((2, 3), numero=2)])
        self.assertEqual(r.completitud, EC.INCONSISTENTE)
        self.assertIn("oid_duplicado_entre_paginas", r.diagnosticos)

    def test_orden_inestable_dentro_y_entre_paginas(self):
        for paginas in ([pagina((2, 1), exceso=True)],
                         [pagina((5, 7), exceso=True), pagina((2, 3), numero=2)]):
            r = self.ejecutar(paginas)
            self.assertIn("ordenacion_inestable", r.diagnosticos)

    def test_huecos_oid_son_legitimos_no_infiere_faltantes(self):
        r = self.ejecutar([pagina((1, 8), exceso=True), pagina((900,), numero=2)], evidencia=evidencia((1, 8, 900)))
        self.assertEqual(r.completitud, EC.COMPLETA_COMPROBADA)

    def test_cambio_remoto_de_instantanea(self):
        r = self.ejecutar([pagina((1, 2), exceso=True), pagina((3,), numero=2, instantanea_id="otra")],
                          evidencia=evidencia())
        self.assertIn("cambio_de_instantanea", r.diagnosticos)

    def test_falta_de_sello_en_pagina_no_se_inventa(self):
        r = self.ejecutar([pagina((1, 2), instantanea_id=None)], evidencia=evidencia((1, 2)))
        self.assertEqual(r.completitud, EC.INCONSISTENTE)
        self.assertIn("instantanea_no_acreditada_en_pagina", r.diagnosticos)

    def test_cambio_conteo_remoto_aun_sin_evidencia_previa(self):
        r = self.ejecutar([pagina((1, 2), exceso=True, total_observado=4),
                          pagina((3,), numero=2, total_observado=3)])
        self.assertIn("conteo_remoto_cambiante", r.diagnosticos)

    def test_mismo_conteo_ids_cambiados(self):
        r = self.ejecutar([pagina((1, 9))], evidencia=evidencia((1, 2)))
        self.assertEqual(r.completitud, EC.INCONSISTENTE)
        self.assertIn("identificadores_remotos_ajenos", r.diagnosticos)

    def test_conteo_e_ids_contradictorios_antes_de_pedir(self):
        r = self.ejecutar([pagina()], evidencia=evidencia(total=4))
        self.assertEqual(r.completitud, EC.INCONSISTENTE)
        self.assertEqual(self.transporte.intentos, 0)

    def test_conteo_en_pagina_contradice_ids_sin_conteo_previo(self):
        r = self.ejecutar([pagina((1, 2), total_observado=3)], evidencia=evidencia((1, 2), total=None))
        self.assertIn("conteo_e_identificadores_contradictorios", r.diagnosticos)
        self.assertEqual(r.completitud, EC.INCONSISTENTE)

    def test_lote_ids_incompleto_no_salta_al_siguiente(self):
        r = self.ejecutar([pagina((1,))], evidencia=evidencia(), estrategia=ES.OBJECT_IDS)
        self.assertIn("lote_object_ids_incompleto_o_ajeno", r.diagnosticos)
        self.assertEqual(self.transporte.intentos, 1)

    def test_lote_ids_con_limite_anunciado_detiene_operacion(self):
        r = self.ejecutar([pagina((1,), exceso=True), pagina((3,), numero=2)],
                          evidencia=evidencia(), estrategia=ES.OBJECT_IDS)
        self.assertEqual(r.completitud, EC.INCOMPLETA_POR_LIMITES)
        self.assertEqual(self.transporte.intentos, 1)

    def test_lote_ids_contradictorio_no_se_oculta_con_final_correcto(self):
        r = self.ejecutar([pagina((1, 2), exceso=True), pagina((3,), numero=2)],
                          evidencia=evidencia(), estrategia=ES.OBJECT_IDS)
        self.assertEqual(r.completitud, EC.INCONSISTENTE)
        self.assertIn("continuacion_con_lote_ids_agotado", r.diagnosticos)
        self.assertEqual(self.transporte.intentos, 1)

    def test_fin_declarado_con_ids_ausentes(self):
        r = self.ejecutar([pagina((1, 2))], evidencia=evidencia())
        self.assertIn("fin_con_entidades_documentadas_ausentes", r.diagnosticos)

    def test_continuacion_con_ids_agotados_es_contradiccion(self):
        r = self.ejecutar([pagina((1, 2), exceso=True)], evidencia=evidencia((1, 2)))
        self.assertIn("continuacion_con_identificadores_agotados", r.diagnosticos)

    def test_continuacion_con_conteo_agotado(self):
        e = evidencia((1, 2), object_ids=None, ids_obtenidos_utc=None)
        r = self.ejecutar([pagina((1, 2), exceso=True)], evidencia=e)
        self.assertIn("continuacion_con_conteo_agotado", r.diagnosticos)

    def test_mas_entidades_que_conteo(self):
        e = evidencia((1,), object_ids=None, ids_obtenidos_utc=None)
        r = self.ejecutar([pagina((1, 2))], evidencia=e)
        self.assertIn("entidades_superan_conteo", r.diagnosticos)

    def test_respuesta_excede_tamano_solicitado(self):
        r = self.ejecutar([pagina((1, 2, 3))])
        self.assertIn("pagina_supera_tamano_solicitado", r.diagnosticos)

    def test_interrupcion_conserva_recibos_y_no_reintenta(self):
        r = self.ejecutar([pagina((1, 2), exceso=True), pagina((3,), numero=2, interrumpida=True), pagina((4,), numero=3)])
        self.assertEqual(r.completitud, EC.PARCIAL)
        self.assertEqual(self.transporte.intentos, 2)
        self.assertEqual(r.entidades_recibidas, 2)
        self.assertEqual(r.recibos[-1].estado, EP.INTERRUMPIDA)

    def test_json_truncado_o_error_no_se_promueven_a_completos(self):
        for cuerpo in (b'{"features":[', b'{"error":{"code":500}}'):
            r = self.ejecutar([respuesta(cuerpo)])
            self.assertEqual(r.completitud, EC.INCONSISTENTE)
            self.assertEqual(r.entidades_recibidas, 0)

    def test_evidencia_de_otra_consulta(self):
        r = self.ejecutar([pagina()], evidencia=replace(evidencia(), huella_consulta="a" * 64))
        self.assertEqual(r.completitud, EC.INCONSISTENTE)
        self.assertEqual(self.transporte.intentos, 0)

    def test_fechas_de_evidencias_y_paginas_conservadas(self):
        e = evidencia((1, 2))
        r = self.ejecutar([pagina((1, 2))], evidencia=e)
        self.assertEqual(r.evidencia.ids_obtenidos_utc, FECHA)
        self.assertEqual(r.evidencia.obtenida_utc, FECHA)
        self.assertEqual(r.recibos[0].obtenida_utc, FECHA + timedelta(seconds=1))

    def test_cronologia_incoherente(self):
        for kw in ({"obtenida_utc": FECHA - timedelta(seconds=1)},
                   {"ids_obtenidos_utc": FECHA - timedelta(seconds=1)}):
            r = self.ejecutar([pagina()], evidencia=replace(evidencia(), **kw))
            self.assertEqual(r.completitud, EC.INCONSISTENTE)
        r = self.ejecutar([pagina((1, 2), numero=4, exceso=True), pagina((3,), numero=2)])
        self.assertIn("cronologia_de_evidencia_contradictoria", r.diagnosticos)

    def test_discontinuidad_de_parametros_no_aceptada(self):
        s = SolicitudPagina(consulta().adquisicion_id, consulta().huella, 9, {"resultOffset": "90"})
        r = self.ejecutar([pagina(solicitud=s)])
        self.assertIn("discontinuidad_de_solicitud", r.diagnosticos)
        self.assertEqual(r.recibos[0].solicitud_observada, s)
        self.assertEqual(r.recibos[0].estado, EP.NO_INSPECCIONADA)
        self.assertEqual(r.bytes_inspeccionados, 0)

    def test_limite_paginas_en_secuencia_infinita(self):
        def infinito():
            n = 1
            while True:
                yield pagina((n,), numero=n, exceso=True)
                n += 1
        r = self.ejecutar(infinito(), limites=replace(LimitesVector(), max_paginas=3))
        self.assertEqual(r.completitud, EC.INCOMPLETA_POR_LIMITES)
        self.assertEqual(self.transporte.intentos, 3)

    def test_limite_entidades_antes_de_exceder_agregado(self):
        r = self.ejecutar([pagina((1, 2), exceso=True), pagina((3, 4), numero=2)],
                          limites=replace(LimitesVector(), entidades_total=3))
        self.assertEqual(r.completitud, EC.INCOMPLETA_POR_LIMITES)
        self.assertEqual(r.entidades_recibidas, 2)

    def test_limite_bytes_acumulados(self):
        a, b = pagina((1, 2), exceso=True), pagina((3,), numero=2)
        r = self.ejecutar([a, b], limites=replace(LimitesVector(), bytes_total=len(a.contenido)))
        self.assertEqual(r.completitud, EC.INCOMPLETA_POR_LIMITES)
        self.assertEqual(r.bytes_recibidos, len(a.contenido) + len(b.contenido))
        self.assertEqual(r.bytes_inspeccionados, len(a.contenido))
        self.assertEqual(len(r.recibos), 2)
        self.assertEqual(r.recibos[-1].estado, EP.NO_INSPECCIONADA)
        self.assertIsNone(r.recibos[-1].sha256)

    def test_limite_respuesta_preserva_rechazo(self):
        r = self.ejecutar([pagina()], limites=replace(LimitesVector(), max_bytes_respuesta=10))
        self.assertEqual(r.completitud, EC.INCOMPLETA_POR_LIMITES)
        self.assertIsNone(r.recibos[0].sha256)

    def test_memoria_auxiliar_antes_de_obtener_pagina(self):
        r = self.ejecutar([pagina()], limites=replace(LimitesVector(), bytes_auxiliares=100))
        self.assertEqual(r.completitud, EC.INCOMPLETA_POR_LIMITES)
        self.assertEqual(self.transporte.intentos, 0)

    def test_memoria_evidencia_y_conteos_acotados(self):
        r = self.ejecutar([], evidencia=evidencia(), limites=replace(LimitesVector(), bytes_auxiliares=200))
        self.assertIn("limite_evidencia_ids", r.diagnosticos)
        r = self.ejecutar([], evidencia=evidencia(total=100, object_ids=None, ids_obtenidos_utc=None),
                          limites=replace(LimitesVector(), entidades_total=5))
        self.assertIn("limite_conteo_documentado", r.diagnosticos)

    def test_cancelacion_antes_sin_consumir_fixture(self):
        e = Event()
        e.set()
        r = self.ejecutar([pagina()], cancelacion=e)
        self.assertEqual(r.completitud, EC.PARCIAL)
        self.assertIn("operacion_cancelada", r.diagnosticos)
        self.assertEqual(self.transporte.intentos, 0)

    def test_cancelacion_entre_paginas(self):
        e = Event()
        def respuestas():
            yield pagina((1, 2), exceso=True)
            e.set()
            yield pagina((3,), numero=2)
        r = self.ejecutar(respuestas(), cancelacion=e)
        self.assertEqual(r.completitud, EC.PARCIAL)
        self.assertEqual(r.entidades_recibidas, 2)
        self.assertEqual(r.recibos[-1].estado, EP.CANCELADA)

    def test_configuracion_no_sustituye_transporte_por_cliente(self):
        class ClienteAjeno:
            def recibir(self, solicitud):
                raise AssertionError("No debe ejecutarse")
        with self.assertRaises(TypeError):
            coordinar(consulta(), ClienteAjeno())
        with self.assertRaises(TypeError):
            TransporteSintetico(url="https://ejemplo.invalid")

    def test_no_hay_red_ni_sqlite_ni_archivos_en_coordinacion(self):
        p = [pagina((1, 2))]
        e = evidencia((1, 2))
        for destino in ("socket.create_connection", "socket.getaddrinfo", "socket.socket.connect",
                        "sqlite3.connect", "builtins.open"):
            with patch(destino, side_effect=AssertionError("IO prohibida")):
                r = self.ejecutar(p, evidencia=e)
                self.assertEqual(r.completitud, EC.COMPLETA_COMPROBADA)

    def test_importacion_limpia_no_carga_cliente_http(self):
        # Inspección de importaciones propias, independiente del orden de tests.
        raiz = Path(__file__).resolve().parents[1] / "src/spica/adquisicion/vectorial"
        prohibidos = ("httpx", "transportes", "almacenamiento", "integracion", "ensayo", "socket")
        for f in raiz.glob("*.py"):
            arbol = ast.parse(f.read_text(encoding="utf-8"))
            for n in ast.walk(arbol):
                if isinstance(n, ast.ImportFrom):
                    self.assertFalse(any(x in (n.module or "") for x in prohibidos), f.name)
                elif isinstance(n, ast.Import):
                    self.assertFalse(any(x in a.name for a in n.names for x in prohibidos), f.name)

    def test_importacion_transitiva_no_carga_http_en_proceso_nuevo(self):
        codigo = ("import sys; import spica.adquisicion.vectorial; "
                  "assert 'httpx' not in sys.modules; "
                  "assert not any(m.startswith(('spica.adquisicion.transportes',"
                  "'spica.adquisicion.integracion','spica.adquisicion.inspeccion_arcgis')) for m in sys.modules)")
        r = subprocess.run([sys.executable, "-B", "-c", codigo], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_memoria_auxiliar_incluye_parametros_de_cada_recibo(self):
        c = replace(consulta(), parametros={"where": "x" * 8000})
        t = TransporteSintetico([pagina((1,))])
        r = coordinar(c, t, tamano_pagina=1, limites=replace(LimitesVector(), bytes_auxiliares=10_000))
        self.assertEqual(r.completitud, EC.INCOMPLETA_POR_LIMITES)
        self.assertEqual(t.intentos, 0)

    def test_parametros_ids_excesivos_se_detienen_con_diagnostico(self):
        ids = tuple(2**62 + i for i in range(1000))
        t = TransporteSintetico([])
        r = coordinar(consulta(), t, tamano_pagina=1000, estrategia=ES.OBJECT_IDS, evidencia=evidencia(ids))
        self.assertEqual(r.completitud, EC.INCOMPLETA_POR_LIMITES)
        self.assertIn("limite_parametros_pagina", r.diagnosticos)
        self.assertEqual(t.intentos, 0)

    def test_sin_instantanea_cambios_no_observables_permanecen_desconocidos(self):
        # Páginas sin duplicados y conteo estable no prueban que no cambiaron
        # atributos o entidades omitidas entre peticiones.
        r = self.ejecutar([pagina((1, 2), exceso=True, instantanea_id=None),
                          pagina((4,), numero=2, instantanea_id=None)])
        self.assertEqual(r.completitud, EC.DESCONOCIDA)
        self.assertIn("sin_garantia_de_instantanea_consistente", r.limitaciones)

    def test_geometrias_y_cuerpos_no_quedan_en_resultado(self):
        import spica.adquisicion.vectorial.coordinador as modulo
        referencias, entidades = [], []
        original = modulo.validar_featureset
        def observar(*a, **kw):
            p = original(*a, **kw)
            referencias.append(weakref.ref(p.respuesta))
            entidades.extend(weakref.ref(e) for e in p.entidades)
            return p
        def fixture():
            for n in range(1, 5):
                yield pagina((n,), numero=n, exceso=n < 4)
        # new=función, sin Mock que retenga los argumentos y sus cuerpos.
        with patch.object(modulo, "validar_featureset", new=observar):
            r = self.ejecutar(fixture())
        gc.collect()
        self.assertEqual(len(referencias), 4)
        self.assertTrue(all(ref() is None for ref in referencias))
        self.assertTrue(all(ref() is None for ref in entidades))
        self.assertFalse(hasattr(r, "entidades"))
        self.assertTrue(all(not hasattr(x, "contenido") for x in r.recibos))

    def test_memoria_medida_con_paginas_perezosas(self):
        def fixture(n):
            for i in range(n):
                d = featureset((i,), exceso=True)
                d["features"][0]["attributes"]["texto"] = "x" * 50_000
                yield respuesta(d, numero=i + 1)
        def pico(n):
            gc.collect()
            tracemalloc.start()
            try:
                r = self.ejecutar(fixture(n), limites=replace(LimitesVector(), max_paginas=n))
                return tracemalloc.get_traced_memory()[1], len(r.recibos)
            finally:
                tracemalloc.stop()
        pequeno, _ = pico(4)
        grande, paginas = pico(24)
        self.assertEqual(paginas, 24)
        self.assertLess(grande, pequeno + 512_000)

    def test_determinismo(self):
        p = [pagina((1, 2), exceso=True), pagina((3,), numero=2)]
        self.assertEqual(self.ejecutar(p, evidencia=evidencia()), self.ejecutar(p, evidencia=evidencia()))

    def test_resultado_no_admite_listas_mutables(self):
        r = self.ejecutar([pagina((1, 2))], evidencia=evidencia((1, 2)))
        for kw in ({"recibos": list(r.recibos)}, {"diagnosticos": []}, {"limitaciones": []}):
            with self.assertRaises(TypeError):
                replace(r, **kw)

    def test_estrategias_requieren_evidencia_pertinente(self):
        for estrategia in (ES.OBJECT_IDS, ES.CONTEO_DOCUMENTADO):
            with self.assertRaises(ValueError):
                self.ejecutar([], estrategia=estrategia)


if __name__ == "__main__":
    unittest.main()
