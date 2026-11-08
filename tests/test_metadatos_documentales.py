"""Contratos documentales con fixtures ficticios, sin archivos institucionales."""

from dataclasses import FrozenInstanceError, asdict, replace
from datetime import date, datetime, timezone
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from spica.metadatos_documentales import (
    AfirmacionDocumental, AspectoUso as A, ConstatacionAspecto, ExpedienteMetadatos,
    FormaDeclaracion, FuenteDocumental, PresenciaInformacion as P, ReferenciaCelda,
    ReferenciaSeccion, RelacionAfirmaciones, RestriccionUso as R, TipoDocumento as T,
    TipoRelacion as L, DiagnosticoUso, OperacionUso as O, ResultadoUso, evaluar_uso, localizar,
)
from spica.calidad.modelos_cientificos import ReferenciaCientifica
from spica.calidad.aplicabilidad.modelos import EvidenciaDocumental, NivelEvidencia as N, NaturalezaEvidencia, VigenciaDocumento
from spica.interoperabilidad.modelos import Respaldo, IdentidadRecurso, PeriodoTemporal
from spica.adquisicion.catalogo.modelos import EstadoVerificacion as V, ProcedenciaCatalogo
from spica.adquisicion.nucleo import Fuente
from spica.adquisicion.verificacion.docx.modelos import ReferenciaDOCX


def respaldo():
    return Respaldo(V.VERIFICADO, ProcedenciaCatalogo('fixture de prueba',
        datetime(2000, 1, 1, tzinfo=timezone.utc), 'declaracion sintetica', 'sin comprobacion fisica real'))


def fuente(identificador='doc-a', tipo=T.OTRO, *, completa=False):
    ref = ReferenciaCientifica(identificador, 'emisor ficticio declarado', 'Documento sintetico',
        'referencia local ficticia', version_documento='ed-doc' if completa else None, sha256_referencia='1' * 64)
    producto = IdentidadRecurso(Fuente('Fuente ficticia', 'FUENTE_FICTICIA'), 'recurso', 'producto')
    return FuenteDocumental(ref, tipo, producto, 'ed-producto' if completa else None,
        integridad=respaldo(), inspeccion=respaldo(), autenticidad=respaldo() if completa else None,
        correspondencia_editorial=respaldo() if completa else None)


def afirmacion(identificador='a', f=None, *, contenido='valor literal', concepto='magnitud', ambito='ambito sintetico',
               presencia=P.CON_VALOR, nivel=N.DECLARADA, unidad=None, completa=False):
    f = f or fuente(completa=completa)
    if f.tipo is T.XLSX:
        ref = ReferenciaCelda(f.identificador, f.sha256, 'Campos', 'B2')
    elif f.tipo is T.DOCX:
        q = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
        ref = ReferenciaDOCX(f.identificador, f.sha256, 'word/document.xml',
            '/' + q + 'document[1]/' + q + 'body[1]/' + q + 'p[1]', parrafo=1)
    else:
        ref = ReferenciaSeccion(f.identificador, f.sha256, 'seccion 1')
    ev = EvidenciaDocumental(f.referencia, localizar(ref), NaturalezaEvidencia.SINTETICA, nivel,
        vigencia=VigenciaDocumento.VIGENTE if completa else VigenciaDocumento.DESCONOCIDA,
        pendientes=('no localizado en alcance sintetico',) if nivel is N.DESCONOCIDA else (),
        contradicciones=('conflicto sintetico',) if nivel is N.CONTRADICTORIA else ())
    constataciones = tuple(ConstatacionAspecto(a, 'respaldo sintetico de ' + a.value, respaldo()) for a in A) if completa else ()
    return AfirmacionDocumental(identificador, f, ref, ev, concepto, ambito, presencia, contenido,
        unidad_declarada=unidad, constataciones=constataciones)


def expediente(*afirmaciones, relaciones=()):
    fuentes = tuple({a.fuente.identificador: a.fuente for a in afirmaciones}.values())
    return ExpedienteMetadatos(fuentes, afirmaciones, relaciones)


def codigos(r):
    return {d.codigo for d in r.diagnosticos if d.bloqueante}


class MetadatosDocumentalesTests(unittest.TestCase):
    def test_fuente_conserva_referencia_y_no_inventa_ediciones(self):
        f = fuente()
        self.assertIs(type(f.referencia), ReferenciaCientifica)
        self.assertIsNone(f.referencia.version_documento)
        self.assertIsNone(f.version_producto)
        self.assertIsNone(f.autenticidad)
        self.assertEqual(f.sha256, '1' * 64)

    def test_sha_ausente_o_invalido_y_procedencia_vacia(self):
        ref = fuente().referencia
        for sha in (None, '', 'g' * 64, 'A' * 64, '1' * 63):
            with self.subTest(sha=sha), self.assertRaises(ValueError):
                FuenteDocumental(replace(ref, sha256_referencia=sha), T.OTRO)
        with self.assertRaises(ValueError):
            replace(ref, procedencia=' ')
        with self.assertRaises(TypeError):
            FuenteDocumental(None, T.OTRO)

    def test_correspondencia_no_puede_verificarse_sin_ediciones(self):
        f = fuente()
        with self.assertRaises(ValueError):
            replace(f, correspondencia_editorial=respaldo())
        with self.assertRaises(ValueError):
            replace(f, producto=None, version_producto='edicion')
        self.assertIs(fuente(completa=True).correspondencia_editorial.estado, V.VERIFICADO)

    def test_integridad_e_inspeccion_son_independientes_del_hash(self):
        f = replace(fuente(), integridad=None, inspeccion=None)
        a = afirmacion(f=f)
        r = evaluar_uso(expediente(a), O.CONSULTA_DOCUMENTAL, ('a',))
        self.assertEqual(codigos(r), {'integridad_no_acreditada', 'inspeccion_no_acreditada'})

    def test_referencia_xlsx_y_limites_de_rango(self):
        a = afirmacion(f=fuente(tipo=T.XLSX))
        self.assertEqual(localizar(a.referencia), 'xlsx:Campos!B2')
        self.assertEqual(ReferenciaCelda('x', '1' * 64, 'Hoja', 'A1:XFD1048576').rango, 'A1:XFD1048576')
        for rango in ('', 'A', '0', 'A0', 'a1', '$A$1', 'A1:B', 'B2:A1', 'XFE1', 'A1048577', 'A1:B2:C3'):
            with self.subTest(rango=rango), self.assertRaises(ValueError):
                ReferenciaCelda('x', '1' * 64, 'Hoja', rango)

    def test_referencia_docx_reutiliza_contrato_y_contexto(self):
        a = afirmacion(f=fuente(tipo=T.DOCX))
        ref = a.referencia
        self.assertIs(type(ref), ReferenciaDOCX)
        q = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
        ruta = '/' + q + 'document[1]/' + q + 'body[1]/'
        ref = replace(ref, ruta_xml=ruta+q+'tbl[2]/'+q+'tr[3]/'+q+'tc[1]/'+q+'p[4]', tabla=2, fila=3, columna=1, parrafo=20)
        ev = replace(a.evidencia, localizacion=localizar(ref))
        b = replace(a, referencia=ref, evidencia=ev)
        self.assertEqual((b.referencia.tabla, b.referencia.fila, b.referencia.columna), (2, 3, 1))
        for datos in (dict(fila=2), dict(columna=True), dict(parrafo=None), dict(parte='../otra.xml'), dict(tabla=None)):
            with self.subTest(datos=datos), self.assertRaises(ValueError):
                localizar(replace(ref, **datos))

    def test_referencia_ausente_o_de_otro_documento_no_se_acepta(self):
        a = afirmacion()
        with self.assertRaises(TypeError):
            replace(a, referencia=None)
        for ref in (replace(a.referencia, archivo_id='otro'), replace(a.referencia, sha256='2' * 64)):
            with self.subTest(ref=ref), self.assertRaises(ValueError):
                replace(a, referencia=ref)
        with self.assertRaises(TypeError):
            replace(a, referencia=ReferenciaCelda(a.fuente.identificador, a.fuente.sha256, 'Hoja', 'A1'))

    def test_afirmacion_sin_evidencia_o_localizacion_inconsistente(self):
        a = afirmacion()
        with self.assertRaises(TypeError):
            replace(a, evidencia=None)
        with self.assertRaises(ValueError):
            replace(a, evidencia=replace(a.evidencia, localizacion='otra seccion'))
        with self.assertRaises(ValueError):
            replace(a, evidencia=replace(a.evidencia, referencia=replace(a.fuente.referencia, identificador='otro')))

    def test_ausencia_no_equivale_a_nulo_ni_a_literal_null(self):
        ausencia = afirmacion(presencia=P.AUSENTE, contenido=None, nivel=N.DESCONOCIDA)
        nulo = afirmacion(presencia=P.NULO_DECLARADO, contenido='NULO expresamente declarado')
        literal = afirmacion(contenido='NULL')
        self.assertIsNone(ausencia.valor)
        self.assertIsNone(nulo.valor)
        self.assertEqual(nulo.contenido, 'NULO expresamente declarado')
        self.assertEqual(literal.valor, 'NULL')
        self.assertNotEqual(ausencia.presencia, nulo.presencia)
        self.assertTrue(evaluar_uso(expediente(nulo), O.CONSULTA_DOCUMENTAL, ('a',)).requisitos_documentales_satisfechos)
        self.assertIn('nulo_declarado_no_es_valor_cientifico', codigos(evaluar_uso(expediente(nulo), O.INTERPRETACION_VARIABLE, ('a',))))
        for otro in (replace(ausencia, identificador='b'), replace(nulo, identificador='b', contenido='otro marcador de nulo')):
            with self.subTest(presencia=otro.presencia), self.assertRaises(ValueError):
                expediente(nulo, otro, relaciones=(RelacionAfirmaciones('a', 'b', L.CONTRADICCION, 'clasificacion indebida'),))

    def test_nulo_no_se_infiere_y_ausencia_requiere_estado_y_alcance(self):
        with self.assertRaises(ValueError):
            afirmacion(presencia=P.NULO_DECLARADO, contenido='posible nulo', nivel=N.INFERIDA)
        with self.assertRaises(ValueError):
            afirmacion(presencia=P.AUSENTE, contenido=None)
        a = afirmacion(presencia=P.AUSENTE, contenido=None, nivel=N.DESCONOCIDA)
        with self.assertRaises(ValueError):
            replace(a, evidencia=replace(a.evidencia, pendientes=()))
        self.assertIn('informacion_ausente', codigos(evaluar_uso(expediente(a), O.CONSULTA_DOCUMENTAL, ('a',))))

    def test_literales_identificadores_y_vigencia_no_se_normalizan(self):
        a = afirmacion('id:original', contenido=' 0000.00 ', unidad=' unidad literal ')
        p = PeriodoTemporal(date(2001, 1, 1), date(2001, 2, 1))
        a = replace(a, vigencia=p, forma=FormaDeclaracion.PARAFRASIS_CONTROLADA)
        self.assertEqual((a.valor, a.unidad_declarada), (' 0000.00 ', ' unidad literal '))
        self.assertIs(a.vigencia, p)
        with self.assertRaises(TypeError):
            replace(a, vigencia='2001')

    def test_inmutabilidad_y_tuplas_estrictas(self):
        a = afirmacion()
        with self.assertRaises(FrozenInstanceError):
            a.contenido = 'alterado'
        for cambios in (dict(restricciones=[]), dict(constataciones=[])):
            with self.subTest(cambios=cambios), self.assertRaises(TypeError):
                replace(a, **cambios)
        with self.assertRaises(ValueError):
            replace(a, restricciones=(R.UNIDAD_AMBIGUA, R.UNIDAD_AMBIGUA))

    def test_registro_rechaza_identidades_repetidas_y_fuentes_ajenas(self):
        a = afirmacion()
        for fuentes, aa in (((a.fuente, a.fuente), (a,)), ((a.fuente,), (a, a)), ((fuente('otra'),), (a,))):
            with self.subTest(fuentes=fuentes), self.assertRaises(ValueError):
                ExpedienteMetadatos(fuentes, aa)
        with self.assertRaises(ValueError):
            ExpedienteMetadatos((), ())

    def test_no_se_mezclan_fixtures_con_evidencia_documental(self):
        a = afirmacion()
        b = replace(afirmacion('b'), evidencia=replace(a.evidencia, naturaleza=NaturalezaEvidencia.DOCUMENTAL))
        with self.assertRaises(ValueError):
            expediente(a, b)

    def test_complementariedad_no_promueve_corroboracion_o_edicion(self):
        a, b = afirmacion(), afirmacion('b', fuente('doc-b'), contenido='detalle complementario', concepto='metodo')
        e = expediente(a, b, relaciones=(RelacionAfirmaciones('a', 'b', L.COMPLEMENTARIEDAD, 'ambos describen aspectos distintos'),))
        consulta = evaluar_uso(e, O.CONSULTA_DOCUMENTAL, ('a', 'b'))
        self.assertTrue(consulta.requisitos_documentales_satisfechos)
        r = evaluar_uso(e, O.INTERPRETACION_VARIABLE, ('a', 'b'))
        self.assertIn('falta.corroboracion_independiente', codigos(r))
        self.assertIn('edicion_o_correspondencia_no_acreditada', codigos(r))

    def test_contradiccion_no_desaparece_al_seleccionar_un_solo_extremo(self):
        a, b = afirmacion(), afirmacion('b', contenido='otro valor')
        e = expediente(a, b, relaciones=(RelacionAfirmaciones('a', 'b', L.CONTRADICCION, 'valores excluyentes en el mismo ambito'),))
        r = evaluar_uso(e, O.CONSULTA_DOCUMENTAL, ('a',))
        d = next(d for d in r.diagnosticos if d.codigo == 'contradiccion_entre_afirmaciones')
        self.assertEqual(d.afirmaciones, ('a', 'b'))
        self.assertEqual(len(d.referencias), 2)
        self.assertFalse(r.requisitos_documentales_satisfechos)

    def test_relaciones_rechazan_extremos_ajenos_duplicados_y_clasificacion_incoherente(self):
        a, b = afirmacion(), afirmacion('b')
        for relaciones in ((RelacionAfirmaciones('a', 'x', L.COMPLEMENTARIEDAD, 'ficticia'),),
                (RelacionAfirmaciones('a', 'b', L.COINCIDENCIA, 'iguales'), RelacionAfirmaciones('b', 'a', L.COMPLEMENTARIEDAD, 'duplicada')),
                (RelacionAfirmaciones('a', 'b', L.CONTRADICCION, 'iguales no son contradiccion'),),
                (RelacionAfirmaciones('a', 'b', L.DIFERENCIA_AMBITO, 'mismo ambito'),)):
            with self.subTest(relaciones=relaciones), self.assertRaises(ValueError):
                expediente(a, b, relaciones=relaciones)

    def test_diferencia_de_ambito_no_es_contradiccion(self):
        a, b = afirmacion(), afirmacion('b', contenido='otro detalle', ambito='otro ambito')
        e = expediente(a, b, relaciones=(RelacionAfirmaciones('a', 'b', L.DIFERENCIA_AMBITO, 'procesos distintos'),))
        self.assertNotIn('contradiccion_entre_afirmaciones', codigos(evaluar_uso(e, O.CONSULTA_DOCUMENTAL, ('a', 'b'))))

    def test_coincidencia_literal_no_demuestra_equivalencia_editorial(self):
        a, b = afirmacion(), afirmacion('b', fuente('doc-b'))
        e = expediente(a, b, relaciones=(RelacionAfirmaciones('a', 'b', L.COINCIDENCIA, 'mismo literal'),))
        self.assertIn('edicion_o_correspondencia_no_acreditada', codigos(evaluar_uso(e, O.EQUIVALENCIA_EDITORIAL, ('a', 'b'))))
        with self.assertRaises(ValueError):
            expediente(a, replace(b, contenido='distinto'), relaciones=e.relaciones)
        a = afirmacion(completa=True, unidad='u')
        b = afirmacion('b', fuente('doc-b', completa=True), completa=True, unidad='u')
        e = expediente(a, b, relaciones=e.relaciones)
        r = evaluar_uso(e, O.EQUIVALENCIA_EDITORIAL, ('a', 'b'))
        self.assertTrue(r.requisitos_documentales_satisfechos)
        self.assertFalse(r.ejecucion_autorizada)
        sin_relaciones = expediente(a, b)
        self.assertIn('equivalencia_sin_comparacion_explicita', codigos(evaluar_uso(sin_relaciones, O.EQUIVALENCIA_EDITORIAL, ('a', 'b'))))
        f = replace(b.fuente, version_producto='otra-edicion')
        b = afirmacion('b', f, completa=True, unidad='u')
        self.assertIn('productos_o_ediciones_no_correspondientes', codigos(evaluar_uso(expediente(a, b, relaciones=e.relaciones), O.EQUIVALENCIA_EDITORIAL, ('a', 'b'))))

    def test_correspondencia_no_demostrada_se_conserva(self):
        a, b = afirmacion(), afirmacion('b', fuente('doc-b'))
        e = expediente(a, b, relaciones=(RelacionAfirmaciones('a', 'b', L.CORRESPONDENCIA_NO_DEMOSTRADA, 'ediciones desconocidas'),))
        self.assertIn('relacion_sin_correspondencia_demostrada', codigos(evaluar_uso(e, O.INTERPRETACION_VARIABLE, ('a',))))

    def test_unidad_sola_no_define_la_variable(self):
        a = afirmacion(unidad='u')
        r = evaluar_uso(expediente(a), O.INTERPRETACION_VARIABLE, ('a',))
        self.assertIn('falta.significado_variable', codigos(r))
        self.assertIn('falta.unidad_aplicable', codigos(r))

    def test_tiempo_sin_convencion_permanece_bloqueado(self):
        a = afirmacion(concepto='reloj literal', contenido='00000')
        r = evaluar_uso(expediente(a), O.CONVERSION_TEMPORAL, ('a',))
        self.assertIn('falta.convencion_temporal', codigos(r))
        self.assertEqual(a.contenido, '00000')

    def test_espacio_sin_identidad_y_referencia_no_se_asigna(self):
        a = afirmacion(concepto='ubicacion')
        r = evaluar_uso(expediente(a), O.ASIGNACION_ESPACIAL, ('a',))
        self.assertTrue({'falta.identidad_espacial', 'falta.referencia_espacial'} <= codigos(r))

    def test_mencion_de_licencia_no_acredita_derechos(self):
        a = afirmacion(concepto='licencia', contenido='licencia ficticia mencionada')
        self.assertTrue(evaluar_uso(expediente(a), O.CONSULTA_DOCUMENTAL, ('a',)).requisitos_documentales_satisfechos)
        self.assertIn('falta.derechos_para_el_uso', codigos(evaluar_uso(expediente(a), O.REDISTRIBUCION, ('a',))))

    def test_palabra_validado_y_nivel_documental_no_certifican_ciencia(self):
        a = afirmacion(contenido='validado', nivel=N.VERIFICADA)
        r = evaluar_uso(expediente(a), O.ACREDITACION_CALIDAD, ('a',))
        self.assertIn('falta.validacion_cientifica', codigos(r))
        self.assertFalse(r.ejecucion_autorizada)

    def test_respaldos_completos_son_diagnostico_no_permiso(self):
        a = afirmacion(completa=True, unidad='u')
        for op in (O.INTERPRETACION_VARIABLE, O.CONVERSION_TEMPORAL, O.ASIGNACION_ESPACIAL, O.ACREDITACION_CALIDAD, O.REDISTRIBUCION):
            with self.subTest(op=op):
                r = evaluar_uso(expediente(a), op, ('a',))
                self.assertTrue(r.requisitos_documentales_satisfechos)
                self.assertFalse(r.ejecucion_autorizada)
                self.assertFalse(r.operacion_ejecutada)
                with self.assertRaises(TypeError):
                    bool(r)
        with self.assertRaises(ValueError):
            replace(a, unidad_declarada=None)
        for vigencia in (VigenciaDocumento.DESCONOCIDA, VigenciaDocumento.OBSOLETO):
            b = replace(a, evidencia=replace(a.evidencia, vigencia=vigencia))
            self.assertIn('vigencia_no_acreditada', codigos(evaluar_uso(expediente(b), O.INTERPRETACION_VARIABLE, ('a',))))
            self.assertTrue(evaluar_uso(expediente(b), O.CONSULTA_DOCUMENTAL, ('a',)).requisitos_documentales_satisfechos)

    def test_restricciones_explicitas_no_se_borran_por_respaldos_positivos(self):
        a = replace(afirmacion(completa=True, unidad='u'), restricciones=(R.UNIDAD_AMBIGUA,))
        r = evaluar_uso(expediente(a), O.INTERPRETACION_VARIABLE, ('a',))
        self.assertIn('restriccion.unidad_ambigua', codigos(r))
        self.assertTrue(evaluar_uso(expediente(a), O.CONSULTA_DOCUMENTAL, ('a',)).requisitos_documentales_satisfechos)

    def test_seleccion_y_diagnostico_no_admiten_trazas_falsas(self):
        a = afirmacion()
        e = expediente(a)
        for seleccion in ((), ('a', 'a'), ('ajena',)):
            with self.subTest(seleccion=seleccion), self.assertRaises(ValueError):
                evaluar_uso(e, O.CONSULTA_DOCUMENTAL, seleccion)
        with self.assertRaises(ValueError):
            ResultadoUso(e, O.CONSULTA_DOCUMENTAL, ('a',), ())
        with self.assertRaises(ValueError):
            ResultadoUso(e, O.CONSULTA_DOCUMENTAL, ('a',), (DiagnosticoUso('falso', ('a',), ('otra traza',), False),))
        with self.assertRaises(TypeError):
            evaluar_uso(e, 'consulta', ('a',))

    def test_determinismo_con_orden_de_seleccion_y_relaciones(self):
        a, b = afirmacion(), afirmacion('b', contenido='detalle', concepto='metodo')
        e = expediente(a, b, relaciones=(RelacionAfirmaciones('a', 'b', L.COMPLEMENTARIEDAD, 'distintos aspectos'),))
        self.assertEqual(evaluar_uso(e, O.INTERPRETACION_VARIABLE, ('a', 'b')), evaluar_uso(e, O.INTERPRETACION_VARIABLE, ('b', 'a')))

    def test_conflicto_explicito_bloquea_aunque_el_nivel_no_se_haya_reclasificado(self):
        a = afirmacion(completa=True, unidad='u')
        for nivel in (N.DECLARADA, N.VERIFICADA, N.INFERIDA):
            b = replace(a, evidencia=replace(a.evidencia, nivel=nivel,
                contradicciones=('dos declaraciones incompatibles en el mismo ambito sintetico',)))
            for op in O:
                with self.subTest(nivel=nivel, op=op):
                    r = evaluar_uso(expediente(b), op, ('a',))
                    self.assertIn('evidencia_contradictoria', codigos(r))
                    self.assertFalse(r.requisitos_documentales_satisfechos)
                    self.assertFalse(r.ejecucion_autorizada)

    def test_banderas_no_configurables_por_constructor_ni_replace(self):
        a = afirmacion(completa=True, unidad='u')
        for op in O:
            r = evaluar_uso(expediente(a), op, ('a',))
            for campo in ('ejecucion_autorizada', 'operacion_ejecutada'):
                with self.subTest(op=op, campo=campo):
                    self.assertIs(getattr(r, campo), False)
                    with self.assertRaises(TypeError):
                        ResultadoUso(r.expediente, r.operacion, r.seleccion, r.diagnosticos, **{campo: True})
                    with self.assertRaises(TypeError):
                        replace(r, **{campo: True})
                    with self.assertRaises(FrozenInstanceError):
                        setattr(r, campo, True)

    def test_referencias_y_respaldos_anidados_conservan_inmutabilidad_cooperativa(self):
        a = afirmacion(completa=True, unidad='u')
        for objeto, campo, valor in (
                (a.fuente.referencia, 'titulo', 'otro'),
                (a.fuente.integridad, 'estado', V.DESCONOCIDO),
                (a.fuente.integridad.procedencia, 'evidencia', 'otra'),
                (a.referencia, 'seccion', 'otra'),
                (a.evidencia, 'contradicciones', ()),
                (a.constataciones[0], 'descripcion', 'otra')):
            with self.subTest(campo=campo), self.assertRaises(FrozenInstanceError):
                setattr(objeto, campo, valor)
        with self.assertRaises(TypeError):
            replace(a, evidencia=replace(a.evidencia, pendientes=['mutable']))

    def test_mismo_id_local_no_permite_sustituir_otro_documento(self):
        a = afirmacion()
        f = replace(a.fuente, referencia=replace(a.fuente.referencia, sha256_referencia='2' * 64))
        b = afirmacion('b', f)
        with self.assertRaises(ValueError):
            ExpedienteMetadatos((a.fuente, f), (a, b))
        with self.assertRaises(ValueError):
            ExpedienteMetadatos((a.fuente,), (b,))
        with self.assertRaises(ValueError):
            replace(a, fuente=f)
        xlsx = fuente(tipo=T.XLSX)
        docx = afirmacion(f=fuente(tipo=T.DOCX))
        with self.assertRaises(TypeError):
            replace(docx, fuente=xlsx, evidencia=replace(docx.evidencia, referencia=xlsx.referencia))

    def test_referencia_sintactica_no_acredita_existencia_o_hash_fisico(self):
        f = replace(fuente(tipo=T.XLSX), integridad=None, inspeccion=None)
        ref = ReferenciaCelda(f.identificador, f.sha256, 'Hoja no comprobada', 'XFD1048576')
        a = afirmacion(f=f)
        a = replace(a, referencia=ref, evidencia=replace(a.evidencia, localizacion=localizar(ref)))
        with patch('builtins.open', side_effect=AssertionError('no debe resolver archivos')):
            r = evaluar_uso(expediente(a), O.CONSULTA_DOCUMENTAL, ('a',))
        self.assertEqual(codigos(r), {'integridad_no_acreditada', 'inspeccion_no_acreditada'})
        self.assertFalse(r.ejecucion_autorizada)

    def test_asdict_no_es_deserializador_ni_permiso_sin_restricciones(self):
        a = replace(afirmacion(completa=True, unidad='u'), restricciones=(R.UNIDAD_AMBIGUA,))
        r = evaluar_uso(expediente(a), O.INTERPRETACION_VARIABLE, ('a',))
        datos = asdict(r)
        self.assertIs(datos['ejecucion_autorizada'], False)
        self.assertEqual(datos['expediente']['afirmaciones'][0]['restricciones'], (R.UNIDAD_AMBIGUA,))
        # Un volcado genérico no es una interfaz de carga admitida.
        with self.assertRaises(TypeError):
            ResultadoUso(**datos)
        for campo in ('ejecucion_autorizada', 'operacion_ejecutada', 'version'):
            datos.pop(campo)
        with self.assertRaises(TypeError):
            ResultadoUso(**datos)
        copia = replace(r)
        self.assertEqual(copia, r)
        self.assertIn('restriccion.unidad_ambigua', codigos(copia))
        self.assertFalse(copia.ejecucion_autorizada)

    def test_sin_red_archivos_sqlite_o_subprocesos_en_modelos_y_evaluacion(self):
        with patch('builtins.open', side_effect=AssertionError('archivo')), patch('pathlib.Path.open', side_effect=AssertionError('archivo')), \
             patch('socket.socket.connect', side_effect=AssertionError('red')), patch('socket.getaddrinfo', side_effect=AssertionError('DNS')), \
             patch('sqlite3.connect', side_effect=AssertionError('sqlite')), patch('subprocess.Popen', side_effect=AssertionError('proceso')):
            a = afirmacion(completa=True, unidad='u')
            self.assertTrue(evaluar_uso(expediente(a), O.INTERPRETACION_VARIABLE, ('a',)).requisitos_documentales_satisfechos)

    def test_importacion_fresca_no_carga_sqlite_http_o_catalogo(self):
        programa = '''import sys,os
sys.path.insert(0,sys.argv[1])
def guardia(e,a):
    if e.startswith(('socket.','sqlite3.')) or e in ('subprocess.Popen','os.system'):
        raise RuntimeError('I/O prohibido')
    if e=='open' and a[2] & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):
        raise RuntimeError('escritura prohibida')
sys.addaudithook(guardia)
class SinPersistencia:
    def find_spec(self,nombre,*args):
        if nombre.split('.')[0] in ('sqlite3','_sqlite3','httpx') or nombre.startswith(('spica.adquisicion','spica.calidad','spica.interoperabilidad')):
            raise RuntimeError('dependencia operativa cargada')
sys.meta_path.insert(0,SinPersistencia())
import spica.metadatos_documentales
assert 'sqlite3' not in sys.modules and 'httpx' not in sys.modules
print('importacion_pura')
'''
        r = subprocess.run([sys.executable, '-B', '-I', '-c', programa, str(Path(__file__).resolve().parents[1] / 'src')],
                           capture_output=True, text=True, timeout=15)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), 'importacion_pura')


if __name__ == '__main__':
    unittest.main()
