"""Registro aislado del expediente documental; sin observaciones ni acceso externo."""

from datetime import date, datetime, timezone
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from spica.calidad.catalogo_cientifico import CatalogoReglasCientificas
from spica.calidad.modelos_cientificos import (
    AmbitoReglaCientifica as A, CondicionAplicabilidad as C, ContextoCientifico,
    DatoContextoCientifico, DimensionAplicabilidad as D, EstadoReglaCientifica as E,
    IncertidumbreCientifica, ReferenciaCientifica, ReglaCientifica, RevisionCientifica,
)

FIXTURE = Path(__file__).resolve().parents[1] / "docs" / "fixtures" / "criterios_qa_nivel1.json"


def referencias(expediente, criterio):
    resultado = []
    for identificador in criterio["fuentes"]:
        f = expediente["fuentes"][identificador]
        resultado.append(ReferenciaCientifica(identificador, f["institucion"], f["titulo"], f["url"],
            f["version_documento"], date.fromisoformat(f["fecha_documento"]) if f["fecha_documento"] else None,
            f.get("sha256_referencia")))
    return tuple(resultado)


def propuestas_aisladas(expediente):
    """Traducción exclusiva de la prueba. No se publica un cargador operativo."""
    for c in expediente["criterios"]:
        if not c["registrar_como_propuesta"]:
            continue
        refs = referencias(expediente, c)
        ids = tuple(r.identificador for r in refs)
        omm = c["estado_verificacion"] == "NO_VERIFICADO_CONTENIDO_OMM"
        for variable in c["variables"]:
            # Se separan variables para no mezclar sus unidades en una sola condición.
            identificador = c["id_spica"] + ("-" + variable if len(c["variables"]) > 1 else "")
            condiciones = [C(D.VARIABLE, (variable,), ids), C(D.UNIDAD, (c["unidad_fuente"][variable],), ids)]
            if not omm:
                condiciones.append(C(D.INSTITUCION, ("SENAMHI",), ids))
            yield c, ReglaCientifica(identificador, c["version_propuesta"], c["nombre"] + " / " + variable,
                A.UNIVERSAL if omm else A.INSTITUCIONAL, None if omm else "SENAMHI", refs,
                tuple(condiciones), parametros=(), metodo=None,
                incertidumbre=IncertidumbreCientifica("; ".join(c["incertidumbres"]), ids),
                contradicciones_documentales=tuple(c["contradicciones_documentales"]))


class ExpedienteNivel1Tests(unittest.TestCase):
    def setUp(self):
        self.expediente = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_identidad_y_parametros_pendientes_con_referencias_resueltas(self):
        criterios = self.expediente["criterios"]
        self.assertEqual(len(criterios), len({c["id_spica"] for c in criterios}))
        for c in criterios:
            with self.subTest(criterio=c["id_spica"]):
                self.assertTrue(c["localizacion_verificada"])
                self.assertTrue(c["incertidumbres"])
                self.assertTrue(set(c["fuentes"]) <= self.expediente["fuentes"].keys())
                for parametro in c["parametros_requeridos"]:
                    self.assertIn(parametro["referencia"], c["fuentes"])
                    self.assertIsNone(parametro["valor"])  # No se cargan límites ejecutables.

    def test_registro_en_memoria_solo_propuestas_no_ejecutables(self):
        catalogo = CatalogoReglasCientificas()
        self.assertEqual(catalogo.listar(), ())
        for c, regla in propuestas_aisladas(self.expediente):
            entrada = catalogo.registrar(regla)
            h = catalogo.comprobar_habilitacion(regla.identificador, regla.version, ContextoCientifico())
            self.assertEqual(entrada.estado, E.PROPUESTA)
            self.assertFalse(h.elegible_documentalmente)
            self.assertFalse(h.ejecucion_autorizada)
            self.assertEqual(regla.parametros, ())
            self.assertIsNone(regla.metodo)
        self.assertTrue(catalogo.listar())
        self.assertTrue(all(r.estado is E.PROPUESTA for r in catalogo.listar()))
        self.assertEqual(CatalogoReglasCientificas().listar(), ())  # Sin persistencia/globales.

    def test_metadatos_desconocidos_impiden_documentar_y_aprobar(self):
        self.assertIsNone(self.expediente["diccionario"]["zona_horaria"])
        self.assertIsNone(self.expediente["diccionario"]["codigo_estacion_estable"])
        self.assertFalse(self.expediente["diccionario"]["continuidad_demostrada"])
        for c, regla in propuestas_aisladas(self.expediente):
            catalogo = CatalogoReglasCientificas(); catalogo.registrar(regla)
            decision = RevisionCientifica("rol-fixture-sin-aprobacion", datetime(2026, 10, 29, tzinfo=timezone.utc),
                "urn:spica:fixture:revision-no-autorizante", tuple(r.identificador for r in regla.referencias))
            with self.subTest(regla=regla.identificador):
                for estado in (E.DOCUMENTADA, E.APROBADA):
                    with self.assertRaises(ValueError):
                        catalogo.cambiar_estado(regla.identificador, regla.version, estado,
                            revision_esperada=1, decision=decision)
                self.assertEqual(catalogo.obtener(regla.identificador, regla.version).estado, E.PROPUESTA)

    def test_unidades_del_diccionario_no_se_normalizan_implicitamente(self):
        unidades = self.expediente["diccionario"]["campos"]
        self.assertEqual(unidades["TEMP"]["unidad_literal"], "°C")
        self.assertEqual(unidades["HR"]["unidad_literal"], "%")
        self.assertEqual(unidades["PP"]["unidad_literal"], "milimetros por hora")
        c, regla = next((c,r) for c,r in propuestas_aisladas(self.expediente) if r.identificador == "L1-CAND-PP-LIM")
        condicion = next(c for c in regla.aplicabilidad if c.dimension is D.UNIDAD)
        self.assertEqual(condicion.valores_permitidos, ("mm/h",))
        self.assertNotIn(unidades["PP"]["unidad_literal"], condicion.valores_permitidos)
        diccionario = next(r for r in regla.referencias if r.identificador == "diccionario_gbon")
        contexto = ContextoCientifico((DatoContextoCientifico(D.UNIDAD, unidades["PP"]["unidad_literal"], diccionario),))
        catalogo = CatalogoReglasCientificas(); catalogo.registrar(regla)
        h = catalogo.comprobar_habilitacion(regla.identificador, regla.version, contexto)
        self.assertIn("contexto_no_demostrado:unidad", h.motivos)
        self.assertFalse(h.ejecucion_autorizada)
        self.assertEqual(contexto.datos[0].valor, "milimetros por hora")

    def test_edicion_provisional_conserva_estado_y_fecha_desconocida(self):
        fuente = self.expediente["fuentes"]["omm_provisional"]
        self.assertEqual(fuente["estado_documental"], "PROVISIONAL_PAGINA_VERIFICADA_CAPITULOS_NO_VERIFICADOS")
        self.assertEqual(fuente["version_documento"], "2026 provisional")
        self.assertIsNone(fuente["fecha_documento"])
        for c, regla in propuestas_aisladas(self.expediente):
            if "omm_provisional" in c["fuentes"]:
                ref = next(r for r in regla.referencias if r.identificador == "omm_provisional")
                self.assertEqual(ref.version_documento, "2026 provisional")
                self.assertIsNone(ref.fecha_documento)
                self.assertIsNone(regla.procedencia_normativa)
                self.assertEqual(c["estado_verificacion"], "NO_VERIFICADO_CONTENIDO_OMM")

    def test_contradicciones_se_conservan_sin_resolucion_automatica(self):
        encontrados = set()
        for c, regla in propuestas_aisladas(self.expediente):
            if c["contradicciones_documentales"]:
                encontrados.add(c["id_spica"])
                self.assertEqual(regla.contradicciones_documentales, tuple(c["contradicciones_documentales"]))
                catalogo = CatalogoReglasCientificas()
                entrada = catalogo.registrar(regla)
                self.assertEqual(entrada.regla.contradicciones_documentales, regla.contradicciones_documentales)
        self.assertTrue({"L1-CAND-PERSISTENCIA", "L1-CAND-PP-24H", "L1-CAND-OMM-METROLOGIA"} <= encontrados)

    def test_criterios_no_aplicables_no_se_registran_por_analogia(self):
        registrados = {r.identificador for _,r in propuestas_aisladas(self.expediente)}
        for c in self.expediente["criterios"]:
            if c["recomendacion"] == "NO_APLICABLE":
                self.assertFalse(c["registrar_como_propuesta"])
                self.assertFalse(any(i.startswith(c["id_spica"]) for i in registrados))
        pp = next(c for c in self.expediente["criterios"] if c["id_spica"] == "L1-CAND-PP-TEMPORAL")
        self.assertEqual(pp["recomendacion"], "NO_APLICABLE")


if __name__ == "__main__":
    unittest.main()
