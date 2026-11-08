"""Ensayo offline 84-L. Controles de confianza separados de las afirmaciones.

Usar desde un llamador confiable en el checkout; no es una API operativa.
No escribe, no autentica al emisor y no promueve respaldos del núcleo.
"""

from dataclasses import dataclass, field
from enum import Enum
import os
from pathlib import Path
import re
import time

from herramientas import inspeccionar_xlsx_84e as xlsx
from spica.adquisicion.verificacion.docx import (
    EstadoInspeccionDOCX, LimitesDOCX, inspeccionar_docx_bytes,
)
from spica.adquisicion.verificacion.docx.inspector import _control, _leer, _ruta_autorizada
from spica.adquisicion.verificacion.docx._control import _Fallo
from spica.adquisicion.catalogo.modelos import ProcedenciaCatalogo
from spica.calidad.modelos_cientificos import ReferenciaCientifica
from spica.metadatos_documentales import (
    AfirmacionDocumental, ExpedienteMetadatos, FormaDeclaracion, PresenciaInformacion,
    ReferenciaCelda, TipoDocumento, TipoRelacion, localizar,
)
from spica.metadatos_documentales.modelos import _id, _sha, _tupla

VERSION = "0.1.0"
MAX_ARCHIVO = 1_048_576


class Comprobacion(Enum):
    NO_REALIZADA = "no_realizada"
    SATISFECHA = "satisfecha"
    FALLIDA = "fallida"
    INCOMPLETA = "incompleta"


class EstadoCotejo(Enum):
    COINCIDE = "coincide_literalmente"
    DIFIERE = "difiere_literalmente"
    NO_COTEJABLE = "no_cotejable"


@dataclass(frozen=True)
class ControlArchivo:
    """Política aportada ANTES de recibir afirmaciones, no autoaprobada aquí.

    referencia y procedencia son los contratos existentes. La procedencia debe
    identificar el antecedente de aprobación; su legitimidad la establece el
    responsable del arnés, no una cadena o firma creada por esta herramienta.
    """
    identificador: str
    ruta: Path = field(repr=False)
    raiz: Path = field(repr=False)
    tipo: TipoDocumento
    referencia: ReferenciaCientifica = field(repr=False)
    tamano_esperado: int
    procedencia: ProcedenciaCatalogo = field(repr=False)

    def __post_init__(self):
        _id(self.identificador)
        if type(self.referencia) is not ReferenciaCientifica or type(self.procedencia) is not ProcedenciaCatalogo:
            raise TypeError("control_con_referencia_y_procedencia_existentes_requerido")
        _sha(self.referencia.sha256_referencia)
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", self.referencia.identificador):
            raise ValueError("id_documento_fuera_del_perfil_del_inspector")
        if self.procedencia.evidencia is None:
            raise ValueError("antecedente_de_control_previo_requerido")
        if self.tipo not in (TipoDocumento.XLSX, TipoDocumento.DOCX):
            raise ValueError("tipo_documental_no_admitido")
        if type(self.tamano_esperado) is not int or not 0 <= self.tamano_esperado <= MAX_ARCHIVO:
            raise ValueError("tamano_control_fuera_del_perfil")
        if not isinstance(self.ruta, Path) or not isinstance(self.raiz, Path):
            raise TypeError("rutas_path_requeridas")
        if (not self.ruta.is_absolute() or not self.raiz.is_absolute()
                or '..' in self.ruta.parts or '..' in self.raiz.parts
                or self.ruta == self.raiz or not self.ruta.is_relative_to(self.raiz)):
            raise ValueError("ruta_control_fuera_de_raiz")
        # No provocar accesos SMB/UNC o a dispositivos en una operación offline.
        if os.name == 'nt' and any(not re.fullmatch(r"[A-Za-z]:", p.drive) for p in (self.ruta, self.raiz)):
            raise ValueError("solo_volumen_local_admitido")


@dataclass(frozen=True)
class CotejoAfirmacion:
    afirmacion: AfirmacionDocumental = field(repr=False)
    referencia_encontrada: Comprobacion
    contenido: EstadoCotejo
    observado: str | None = field(default=None, repr=False)
    diagnosticos: tuple[str, ...] = ()
    ejecucion_autorizada: bool = field(default=False, init=False)


@dataclass(frozen=True)
class ResultadoVinculacion:
    control: ControlArchivo = field(repr=False)
    ruta: Comprobacion
    tamano_observado: int | None
    sha256_calculado: str | None
    comparacion_control: Comprobacion
    inspector: str | None
    version_inspector: str | None
    estructura: Comprobacion
    conservacion: Comprobacion
    firma_inicial: tuple[int, ...] | None = field(repr=False)
    firma_final: tuple[int, ...] | None = field(repr=False)
    cotejos: tuple[CotejoAfirmacion, ...] = field(repr=False)
    diagnosticos: tuple[str, ...]
    limitaciones: tuple[str, ...]
    ejecucion_autorizada: bool = field(default=False, init=False)
    operacion_ejecutada: bool = field(default=False, init=False)
    version: str = field(default=VERSION, init=False)

    def __bool__(self):
        raise TypeError("cotejo_documental_no_es_permiso")

    def diagnostico_publico(self):
        """No exporta literales, rutas locales ni textos de procedencia recibidos."""
        return dict(control=self.control.identificador,
            documento=self.control.referencia.identificador,
            tamano_esperado=self.control.tamano_esperado,
            sha256_esperado=self.control.referencia.sha256_referencia,
            tamano_observado=self.tamano_observado, sha256_calculado=self.sha256_calculado,
            ruta=self.ruta.value, comparacion_control=self.comparacion_control.value,
            inspector=self.inspector, version_inspector=self.version_inspector,
            estructura=self.estructura.value, conservacion=self.conservacion.value,
            cotejos=tuple(dict(afirmacion=c.afirmacion.identificador,
                referencia=localizar(c.afirmacion.referencia), encontrada=c.referencia_encontrada.value,
                contenido=c.contenido.value, diagnosticos=c.diagnosticos) for c in self.cotejos),
            diagnosticos=self.diagnosticos, limitaciones=self.limitaciones,
            ejecucion_autorizada=False, operacion_ejecutada=False, version=self.version)


class _Detener(Exception):
    pass


_LIMITACIONES = (
    'control_previo_aportado_por_responsable_confiable_no_autenticado_por_el_componente',
    'inspeccion_limitada_no_es_validacion_ooxml_completa',
    'autenticidad_institucional_no_comprobada',
    'equivalencia_editorial_y_aplicabilidad_no_comprobadas',
    'derechos_y_validacion_cientifica_no_comprobados',
    'dataclasses_no_aislan_codigo_hostil_y_toctou_residual',
    'sin_autorizacion_operativa',
)


def _fragmento(a, inventario):
    """Busca en la salida del inspector; no analiza XML ni resuelve archivos."""
    ref = a.referencia
    if type(ref) is ReferenciaCelda:
        if ':' in ref.rango:
            return Comprobacion.NO_REALIZADA, None, ('rango_no_admitido_en_cotejo_literal',)
        hojas = [h for h in inventario['hojas'] if h['nombre'] == ref.hoja]
        if len(hojas) != 1:
            return Comprobacion.FALLIDA, None, ('hoja_ausente_o_ambigua',)
        celdas = [c for c in hojas[0]['celdas'] if c['celda'] == ref.rango]
        if len(celdas) != 1:
            return Comprobacion.FALLIDA, None, ('celda_ausente_o_ambigua',)
        c = celdas[0]
        if c['formula_presente'] or c['literal'] is None:
            return Comprobacion.SATISFECHA, None, ('celda_sin_literal_cotejable',)
        return Comprobacion.SATISFECHA, c['literal'], ()
    parrafos = [p for p in inventario.parrafos if
        (p.referencia.parte, p.referencia.ruta_xml) == (ref.parte, ref.ruta_xml)]
    if len(parrafos) != 1:
        return Comprobacion.FALLIDA, None, ('parrafo_ausente_o_ambiguo',)
    if parrafos[0].referencia != ref:
        return Comprobacion.FALLIDA, None, ('contexto_referencia_docx_inconsistente',)
    return Comprobacion.SATISFECHA, parrafos[0].texto, ()


def _cotejar(a, inventario, expediente):
    encontrada, observado, codigos = _fragmento(a, inventario)
    estado = EstadoCotejo.NO_COTEJABLE
    if encontrada is Comprobacion.SATISFECHA and observado is not None:
        if a.presencia is not PresenciaInformacion.CON_VALOR or a.forma is not FormaDeclaracion.LITERAL:
            codigos += ('presencia_o_parafrasis_requiere_revision_humana',)
        else:
            estado = EstadoCotejo.COINCIDE if a.contenido == observado else EstadoCotejo.DIFIERE
            codigos += ('literal_coincidente' if estado is EstadoCotejo.COINCIDE else 'literal_diferente',)
    if (a.evidencia.nivel.value == 'contradictoria' or a.evidencia.contradicciones or any(
            r.tipo is TipoRelacion.CONTRADICCION and a.identificador in (r.primera, r.segunda)
            for r in expediente.relaciones)):
        codigos += ('contradiccion_explicita_conservada_no_resuelta_por_cotejo',)
    return CotejoAfirmacion(a, encontrada, estado, observado, tuple(sorted(codigos)))


@dataclass(frozen=True)
class CotejadorDocumental:
    """El responsable fija controles. cotejar no recibe hashes o permisos."""
    controles: tuple[ControlArchivo, ...] = field(repr=False)

    def __post_init__(self):
        _tupla(self.controles, ControlArchivo)
        if (not self.controles or len({c.identificador for c in self.controles}) != len(self.controles)
                or len({c.referencia.identificador for c in self.controles}) != len(self.controles)):
            raise ValueError("controles_previos_vacios_o_identidades_repetidas")

    def cotejar(self, control_id: str, expediente: ExpedienteMetadatos,
                seleccion: tuple[str, ...]) -> ResultadoVinculacion:
        if type(expediente) is not ExpedienteMetadatos:
            raise TypeError("expediente_documental_requerido")
        _id(control_id)
        _tupla(seleccion, str, 256)
        controles = {c.identificador: c for c in self.controles}
        if control_id not in controles:
            raise ValueError("control_previo_no_registrado")
        control = controles[control_id]
        mapa = {a.identificador: a for a in expediente.afirmaciones}
        if not seleccion or len(set(seleccion)) != len(seleccion) or not set(seleccion) <= mapa.keys():
            raise ValueError("seleccion_vacia_repetida_o_ajena")
        aa = tuple(mapa[i] for i in sorted(seleccion))
        d = dict(control=control, ruta=Comprobacion.NO_REALIZADA, tamano_observado=None,
            sha256_calculado=None, comparacion_control=Comprobacion.NO_REALIZADA,
            inspector=None, version_inspector=None, estructura=Comprobacion.NO_REALIZADA,
            conservacion=Comprobacion.NO_REALIZADA, firma_inicial=None, firma_final=None,
            cotejos=(), diagnosticos=(), limitaciones=_LIMITACIONES)
        errores = []
        inicial = None
        contexto = _control(LimitesDOCX(max_archivo=MAX_ARCHIVO), None, time.monotonic,
                            control.referencia.identificador)
        try:
            if any((a.fuente.identificador, a.fuente.sha256, a.fuente.tipo) != (
                    control.referencia.identificador, control.referencia.sha256_referencia, control.tipo) for a in aa):
                raise _Detener('identidad_de_afirmacion_no_corresponde_al_control')
            d['ruta'] = Comprobacion.INCOMPLETA
            _ruta_autorizada(control.ruta, control.raiz)
            d['ruta'] = Comprobacion.SATISFECHA
            d['comparacion_control'] = Comprobacion.INCOMPLETA
            datos, n, sha, firma = _leer(control.ruta, contexto, conservar=True)
            inicial = (n, sha, firma)
            d.update(tamano_observado=n, sha256_calculado=sha, firma_inicial=firma)
            if (n, sha) != (control.tamano_esperado, control.referencia.sha256_referencia):
                d['comparacion_control'] = Comprobacion.FALLIDA
                raise _Detener('tamano_o_sha256_no_coinciden_con_control_previo')
            d['comparacion_control'] = Comprobacion.SATISFECHA
            d['estructura'] = Comprobacion.INCOMPLETA
            if control.tipo is TipoDocumento.XLSX:
                d.update(inspector='diagnostico_xlsx_84e', version_inspector=xlsx.VERSION)
                inventario = xlsx.inspeccionar_bytes(datos)
                omisiones = ('formatos_xlsx_no_renderizados', 'formulas_y_nombres_definidos_no_ejecutados')
                if inventario['relaciones_externas_no_abiertas']:
                    omisiones += ('relaciones_externas_xlsx_no_abiertas',)
            else:
                d['inspector'] = 'inspector_docx'
                inventario = inspeccionar_docx_bytes(datos, identificador=control.referencia.identificador,
                                                     limites=LimitesDOCX(max_archivo=MAX_ARCHIVO))
                d['version_inspector'] = inventario.version_inspector
                omisiones = tuple(sorted({x.codigo for x in (
                    inventario.operaciones_omitidas + inventario.advertencias + inventario.causas_rechazo)}))
                d['limitaciones'] += omisiones
                if inventario.hipervinculos_omitidos:
                    d['limitaciones'] += ('destinos_externos_docx_omitidos_no_abiertos',)
                if inventario.estado is not EstadoInspeccionDOCX.DOCUMENTO_VALIDADO_EN_ALCANCE:
                    d['estructura'] = (Comprobacion.INCOMPLETA if inventario.estado is
                        EstadoInspeccionDOCX.INSPECCION_INCOMPLETA else Comprobacion.FALLIDA)
                    raise _Detener('inspeccion_docx_no_satisfactoria_en_alcance')
                if (inventario.identidad.identificador, inventario.identidad.tamano, inventario.identidad.sha256) != (
                        control.referencia.identificador, n, sha):
                    d['estructura'] = Comprobacion.FALLIDA
                    raise _Detener('identidad_del_snapshot_inspeccionado_inconsistente')
            d['limitaciones'] += omisiones
            d['estructura'] = Comprobacion.SATISFECHA
            d['cotejos'] = tuple(_cotejar(a, inventario, expediente) for a in aa)
            if len({localizar(a.referencia) for a in aa}) != len(aa):
                errores.append('referencia_compartida_no_es_corroboracion_independiente')
        except _Detener as error:
            errores.append(error.args[0])
        except _Fallo as error:
            if d['ruta'] is Comprobacion.INCOMPLETA:
                d['ruta'] = Comprobacion.FALLIDA
            errores.append('lectura_o_ruta_no_comprobada.' + error.codigo)
        except xlsx.ErrorDiagnostico:
            d['estructura'] = Comprobacion.INCOMPLETA
            errores.append('inspeccion_xlsx_no_satisfactoria_en_alcance')
        except OSError:
            if d['ruta'] is Comprobacion.INCOMPLETA:
                d['ruta'] = Comprobacion.FALLIDA
            errores.append('archivo_o_lectura_no_disponibles')
        except Exception:
            errores.append('comprobacion_no_completada')
        finally:
            if inicial is not None:
                try:
                    _ruta_autorizada(control.ruta, control.raiz)
                    _, n, sha, firma = _leer(control.ruta, contexto, conservar=False)
                    d['firma_final'] = firma
                    d['conservacion'] = (Comprobacion.SATISFECHA if (n, sha, firma) == inicial
                                         else Comprobacion.FALLIDA)
                except Exception:
                    d['conservacion'] = Comprobacion.INCOMPLETA
                if d['conservacion'] is not Comprobacion.SATISFECHA:
                    errores.append('conservacion_final_no_comprobada')
                    # No publicar una coincidencia como comprobación vigente
                    # del archivo cuando la conservación final no se acreditó.
                    d['cotejos'] = tuple(CotejoAfirmacion(c.afirmacion,
                        c.referencia_encontrada, EstadoCotejo.NO_COTEJABLE,
                        diagnosticos=tuple(sorted((set(c.diagnosticos) - {
                            'literal_coincidente', 'literal_diferente'}) | {
                            'cotejo_invalidado_por_conservacion_final'}))) for c in d['cotejos'])
        if not d['cotejos']:
            d['cotejos'] = tuple(CotejoAfirmacion(a, Comprobacion.NO_REALIZADA,
                EstadoCotejo.NO_COTEJABLE, diagnosticos=('cotejo_no_realizado',)) for a in aa)
        d['diagnosticos'] = tuple(sorted(set(errores)))
        d['limitaciones'] = tuple(sorted(set(d['limitaciones'])))
        return ResultadoVinculacion(**d)
