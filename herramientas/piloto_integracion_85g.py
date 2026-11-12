"""Ensayo de checkout 85-G: bytes sintéticos, MockTransport y temporales propios.

No es un ejecutor institucional, un permiso ni un orquestador general. No acepta
rutas, clientes, callbacks o planes ejecutables. Reutiliza todos los motores.
"""

from contextlib import ExitStack, contextmanager
import csv
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import io
import os
from pathlib import Path
import re
import tempfile
from threading import Event

import httpx

from spica.adquisicion.almacenamiento import AlmacenRAW, DeclaracionRAW
from spica.adquisicion.almacenamiento.raw import _segura
from spica.adquisicion.catalogo import (
    CatalogoCientifico, FuenteCatalogo, ProductoCatalogo, RecursoCatalogo,
    ProcedenciaCatalogo, EstadoVerificacion, RegistroRecurso,
)
from spica.adquisicion.consultas_locales import ENCABEZADO_SENAMHI, ProcedenciaLocal
from spica.adquisicion.integracion import AdaptadorHTTPRAW, ResultadoHTTPRAW, ErrorIntegracionHTTPRAW
from spica.adquisicion.nucleo import Fuente
from spica.adquisicion.transportes import ClienteHTTP, ConfiguracionHTTP, PoliticaReintentos, RegistroIntento
from spica.adquisicion.verificacion import LectorCSV, PoliticaLecturaCSV, InformeLecturaCSV
from spica.calidad import (
    ConfiguracionQA, EstadoEvaluacionQA, EvaluadorNivel0, InformeQA, LimitesQA,
    ProcedenciaQA, ResultadoQA, restricciones_resultado, TipoRestriccionQA,
)
from spica.calidad.exportacion import ContextoExportacionQA, exportar_resultado_json
from spica.calidad.consumo import (
    EstadoConsumoQA, InformeConsumoQA, LimitesConsumoQA, consumir_exportaciones,
)
from spica.calidad.conciliacion_lotes import (
    EstadoConciliacionQA, InformeConciliacionQA, LoteQA, conciliar_lotes,
)
from herramientas.traza_cierre_85h import capturar_evidencia_85h

VERSION_EJECUCION_85G = "0.1.0"
FUENTE_SINTETICA = Fuente("SPICA-SINTETICA", "fixture-85g")
ORIGEN_SIMULADO = "https://spica-85g.invalid"
URL_SIMULADA = ORIGEN_SIMULADO + "/fixture.csv"


class EstadoEjecucion85G(Enum):
    PLANIFICADA = "planificada"
    INICIADA = "iniciada"
    CONCLUIDA = "concluida_estructuralmente"
    INCOMPLETA = "incompleta"
    FALLIDA = "fallida"
    CANCELADA = "cancelada"


@dataclass(frozen=True)
class Presupuesto85G:
    max_bytes: int = 65_536
    max_registros: int = 8
    max_resultados: int = 256  # Por reproducción; hay exactamente dos.
    max_bytes_json: int = 1_048_576  # Por lote, no cuota de RAM del proceso.

    def __post_init__(self):
        for nombre, tope in (("max_bytes", 1_048_576), ("max_registros", 32),
                             ("max_resultados", 256), ("max_bytes_json", 4_194_304)):
            v = getattr(self, nombre)
            if type(v) is not int or not 0 < v <= tope:
                raise ValueError("presupuesto_85g_no_admitido")


@dataclass(frozen=True)
class ContratoEjecucion85G:
    ejecucion_id: str
    proyecto_id: str
    entrada_id: str  # Archivo sintético; los IDs de fila se derivan por posición.
    evaluacion_id: str
    tarea_ref: str  # Referencia declarada, no un PlanConsulta ejecutado.
    tamano_esperado: int
    sha256_esperado: str
    objeto_id: str = "objeto-ficticio-85g"
    producto_id: str = "producto-ficticio-85g"
    recurso_id: str = "recurso-ficticio-85g"
    presupuesto: Presupuesto85G = field(default_factory=Presupuesto85G)
    configuracion: ConfiguracionQA = field(default_factory=ConfiguracionQA)
    estado: EstadoEjecucion85G = field(default=EstadoEjecucion85G.PLANIFICADA, init=False)
    version: str = field(default=VERSION_EJECUCION_85G, init=False)
    naturaleza: str = field(default="simulacion_sintetica_offline", init=False)
    dependencias: tuple[str, ...] = field(default=("M09", "M10", "M11", "M13", "M17",
        "M18", "M27", "M28", "M29"), init=False)

    def __post_init__(self):
        for nombre in ("ejecucion_id", "proyecto_id", "entrada_id", "evaluacion_id",
                       "tarea_ref", "objeto_id", "producto_id", "recurso_id"):
            v = getattr(self, nombre)
            if type(v) is not str or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,63}", v):
                raise ValueError("identidad_85g_no_admitida")
        if type(self.tamano_esperado) is not int or self.tamano_esperado < 0:
            raise ValueError("tamano_esperado_85g_no_admitido")
        if type(self.sha256_esperado) is not str or not re.fullmatch(r"[0-9a-f]{64}", self.sha256_esperado):
            raise ValueError("sha256_esperado_85g_no_admitido")
        if type(self.presupuesto) is not Presupuesto85G or type(self.configuracion) is not ConfiguracionQA:
            raise TypeError("contratos_85g_tipados_requeridos")
        self.presupuesto.__post_init__()

    def __bool__(self):
        raise TypeError("contrato_planificado_no_es_permiso")


@dataclass(frozen=True)
class InformeEjecucion85G:
    contrato: ContratoEjecucion85G
    estado: EstadoEjecucion85G
    fase_final: str
    diagnosticos: tuple[str, ...]
    traza: tuple[tuple[str, str], ...]
    activo_id: str | None  # También conserva el ID conocido en un error parcial.
    adquisicion: ResultadoHTTPRAW | None = field(repr=False)
    registro_catalogo: RegistroRecurso | None
    resultados: tuple[tuple[ResultadoQA, ...], ...] = field(repr=False)
    informes_qa: tuple[InformeQA, ...]
    lecturas: tuple[InformeLecturaCSV, ...]
    consumos: tuple[InformeConsumoQA, ...] = field(repr=False)
    conciliacion: InformeConciliacionQA | None = field(repr=False)
    solicitudes_simuladas: int
    temporal: Path | None = field(repr=False)  # Referencia histórica, normalmente eliminada.
    temporales_eliminados: bool
    restricciones: tuple[str, ...] = (
        "solo_sintetico_sin_red", "sin_autenticidad_institucional", "sin_validacion_cientifica",
        "sin_autorizacion_operativa", "sin_normalizar_hora_ubigeo_pp",
        "sin_derivados_persistentes", "contextos_declarados_sin_unicidad_global")
    ejecucion_cientifica: bool = field(default=False, init=False)
    autorizacion_operativa: bool = field(default=False, init=False)
    # Evidencia auxiliar 85-H; no cambia contratos de src/spica ni el JSON QA.
    exportaciones: tuple[tuple[str, ...], ...] = field(default=(), repr=False)
    recuperaciones: tuple[str, ...] = ()
    recursos_adquiridos: tuple[str, ...] = ()
    recursos_liberados: tuple[str, ...] = ()
    captura_antes_cierre: str | None = field(default=None, repr=False)
    error_http_raw: tuple[str, str, int | None, tuple[RegistroIntento, ...]] | None = None

    def __bool__(self):
        raise TypeError("informe_estructural_no_es_permiso")


class _Detener(Exception):
    def __init__(self, codigo, estado=EstadoEjecucion85G.FALLIDA):
        self.codigo, self.estado = codigo, estado


def fixture_csv_85g() -> bytes:
    """Dos filas inventadas; perfil de columnas existente, sin datos institucionales."""
    salida = io.StringIO(newline="")
    escritor = csv.writer(salida, lineterminator="\n")
    escritor.writerow(ENCABEZADO_SENAMHI)
    for i in (1, 2):
        d = {c: "literal-ficticio" for c in ENCABEZADO_SENAMHI}
        d.update(ID=f"fila-ficticia-{i}", ESTACION="ESTACION_FICTICIA", FECHA="20260101",
            HORA="hora-incierta", TEMP="+001.250", HR="56.75", PP="4.00", UBIGEO="UBIGEO-INCIERTO")
        escritor.writerow(tuple(d[c] for c in ENCABEZADO_SENAMHI))
    return salida.getvalue().encode("utf-8")


def _base_temporal():
    # No buscar/probar TEMP alternativos ni acceder a una ruta operativa para rechazarla.
    valor = os.environ.get("TEMP") or os.environ.get("TMP")
    if valor is None:
        raise _Detener("temporal_no_configurado")
    base = Path(valor)
    protegidas = (Path.home() / "SPICA_DATOS", Path(__file__).absolute().parents[1])
    if (not base.is_absolute() or base.drive.startswith("\\\\") or ".." in base.parts
            or any(p.casefold() in {".git", ".venv", ".codex", ".agents"} for p in base.parts)
            or any(base.is_relative_to(p) or p.is_relative_to(base) for p in protegidas)):
        raise _Detener("base_temporal_no_admitida")
    _segura(base)
    base = base.resolve(strict=True)
    # Las raíces prohibidas son referencias léxicas: no resolverlas ni sondearlas.
    if not base.is_dir() or any(base.is_relative_to(p) for p in protegidas):
        raise _Detener("base_temporal_no_admitida")
    return base


def ejecutar_piloto_85g(contrato: ContratoEjecucion85G, contenido: bytes, *,
                       cancelacion: Event | None = None) -> InformeEjecucion85G:
    """Una adquisición simulada y dos reproducciones QA del MISMO activo temporal.

    Ejecuta motores reales. Solo la frontera HTTP es MockTransport cerrado; no
    admite inyección de transportes de red. Errores devuelven un informe acotado;
    KeyboardInterrupt/SystemExit se propagan después del cierre por los contextos.
    El contrato y la etiqueta sintética requieren un proceso/llamador confiables.
    """
    if type(contrato) is not ContratoEjecucion85G or type(contenido) is not bytes:
        raise TypeError("contrato_y_bytes_sinteticos_requeridos")
    contrato.__post_init__()
    if cancelacion is not None and type(cancelacion) is not Event:
        raise TypeError("cancelacion_85g_no_admitida")
    evento = cancelacion if cancelacion is not None else Event()
    p = contrato.presupuesto
    traza = [("contrato", EstadoEjecucion85G.PLANIFICADA.value)]
    fase, estado, diagnosticos = "validacion", EstadoEjecucion85G.INICIADA, ()
    raiz = adquisicion = registro = conciliacion = activo_id = None
    resultados, informes, lecturas, consumos = [], [], [], []
    exportaciones, recuperaciones, abiertos, cerrados = [], [], [], []
    captura_previa, captura_fallida, control_final_fallido = None, False, False
    error_http_raw = None
    solicitudes = 0

    def informe_actual(eliminados=False):
        return InformeEjecucion85G(contrato, estado, fase, diagnosticos, tuple(traza), activo_id,
            adquisicion, registro, tuple(resultados), tuple(informes), tuple(lecturas), tuple(consumos),
            conciliacion, solicitudes, raiz, eliminados,
            exportaciones=tuple(tuple(lote) for lote in exportaciones), recuperaciones=tuple(recuperaciones),
            recursos_adquiridos=tuple(abiertos), recursos_liberados=tuple(cerrados),
            captura_antes_cierre=captura_previa, error_http_raw=error_http_raw)

    @contextmanager
    def capturar_antes_de_cerrar():
        nonlocal captura_previa, captura_fallida, control_final_fallido, activo_id
        try:
            yield
        except ErrorIntegracionHTTPRAW as error:
            # El adaptador puede informar un ID después de publicar y antes de
            # retornar ResultadoHTTPRAW. Debe estar en la captura PREVIA también.
            if type(error.activo_id) is str and re.fullmatch(r"[0-9a-f]{32}", error.activo_id):
                activo_id = error.activo_id
            raise
        finally:
            if adquisicion is not None:
                try:
                    almacen.recuperar(adquisicion.activo.asset_id)
                    recuperaciones.append("pre_cierre")
                except Exception:
                    control_final_fallido = True
            try:
                captura_previa = capturar_evidencia_85h(informe_actual())
            except Exception:
                # No sustituir el error original ni impedir cerrar los recursos.
                captura_fallida = True

    def observar_recurso(pila, gestor, nombre):
        valor = gestor.__enter__()
        abiertos.append(nombre)
        def salir(tipo, valor_error, tb):
            respuesta = gestor.__exit__(tipo, valor_error, tb)
            cerrados.append(nombre)  # Solo después de que __exit__ haya retornado.
            return respuesta
        pila.push(salir)
        return valor

    def paso(nombre):
        nonlocal fase
        fase = nombre
        if evento.is_set():
            raise _Detener("cancelacion_solicitada", EstadoEjecucion85G.CANCELADA)
        traza.append((nombre, EstadoEjecucion85G.INICIADA.value))

    class Flujo(httpx.SyncByteStream):
        def __iter__(self):
            for i in range(0, len(contenido), 65_536):
                yield contenido[i:i + 65_536]

    def responder(peticion):
        nonlocal solicitudes
        if peticion.method != "GET" or str(peticion.url) != URL_SIMULADA:
            raise _Detener("solicitud_simulada_fuera_de_alcance")
        solicitudes += 1
        return httpx.Response(200, headers={"Content-Length": str(len(contenido)),
            "Content-Type": "text/csv"}, stream=Flujo())

    try:
        paso("validacion")
        if len(contenido) > p.max_bytes:
            raise _Detener("limite_bytes_entrada", EstadoEjecucion85G.INCOMPLETA)
        traza.append((fase, "completada"))
        with tempfile.TemporaryDirectory(prefix="spica-85g-", dir=_base_temporal()) as temporal:
            raiz = Path(temporal)
            with ExitStack() as recursos, capturar_antes_de_cerrar():
                raw, staging = raiz / "raw", raiz / "staging"
                raw.mkdir()
                staging.mkdir()
                almacen = observar_recurso(recursos, AlmacenRAW(raw, (staging,), max_bytes=p.max_bytes,
                    claves_parametros_publicos=("producto_id",)), "raw_sqlite")
                cliente = observar_recurso(recursos, ClienteHTTP((ORIGEN_SIMULADO,),
                    ConfiguracionHTTP(verificar_tls=True), transporte=httpx.MockTransport(responder),
                    politica_reintentos=PoliticaReintentos(max_intentos=1), cancelacion=evento), "cliente_mock")
                # Perfil de ensayo explícito. MockTransport no demuestra negociación TLS.
                if not URL_SIMULADA.startswith("https://") or not cliente.configuracion.verificar_tls:
                    raise _Detener("perfil_https_tls_requerido")
                paso("adquisicion_simulada")
                adaptador = AdaptadorHTTPRAW(cliente, almacen, staging, max_bytes=p.max_bytes)
                declaracion = DeclaracionRAW(contrato.proyecto_id, contrato.objeto_id, FUENTE_SINTETICA,
                    contrato.recurso_id, parametros_publicos={"producto_id": contrato.producto_id},
                    formato_declarado="csv")
                # Sin evidencia HTTP_DIRECTO verificada ficticia ni ID de adquisición inventado.
                adquisicion = adaptador.adquirir(URL_SIMULADA, declaracion)
                activo = adquisicion.activo
                activo_id = activo.asset_id
                if (activo.declaracion.proyecto_id, activo.declaracion.objeto_id,
                    activo.declaracion.fuente, activo.declaracion.recurso_id) != (
                    contrato.proyecto_id, contrato.objeto_id, FUENTE_SINTETICA, contrato.recurso_id):
                    raise _Detener("identidad_raw_incompatible")
                if (activo.size_bytes, activo.sha256) != (contrato.tamano_esperado, contrato.sha256_esperado):
                    raise _Detener("control_fisico_de_fixture_discrepante")
                if adquisicion.temporal_restante is not None or tuple(staging.iterdir()):
                    raise _Detener("residuo_staging_no_admitido")
                traza.append((fase, "bytes_incorporados_y_controlados"))

                paso("catalogo")
                catalogo = observar_recurso(recursos, CatalogoCientifico(raiz / "catalogo-prueba.sqlite3"),
                    "catalogo_cientifico_sqlite")
                procedencia = ProcedenciaCatalogo("urn:spica:85g:simulacion",
                    datetime.now(timezone.utc), "MockTransport_sin_red", "asset_id=" + activo.asset_id)
                catalogo.registrar_documental(FuenteCatalogo(FUENTE_SINTETICA, procedencia,
                    estado=EstadoVerificacion.DECLARADO))
                catalogo.registrar_documental(ProductoCatalogo(FUENTE_SINTETICA, contrato.producto_id, procedencia))
                recurso = RecursoCatalogo(FUENTE_SINTETICA, contrato.producto_id,
                    contrato.recurso_id, URL_SIMULADA, procedencia, formato="csv")
                catalogo.registrar_documental(recurso)
                registro = catalogo.consultar_recurso(FUENTE_SINTETICA, contrato.producto_id, contrato.recurso_id)
                esperado = (activo.declaracion.fuente, activo.declaracion.recurso_id,
                            activo.declaracion.parametros_publicos.get("producto_id"))
                if (type(registro) is not RegistroRecurso or registro.entidad != recurso or registro.revision != 1
                        or (registro.entidad.fuente, registro.entidad.identificador, registro.entidad.producto_id)
                        != esperado or registro.entidad.localizador != URL_SIMULADA):
                    raise _Detener("identidad_catalogo_incompatible")
                traza.append((fase, "recurso_consultado_sin_capacidad_institucional"))

                local = ProcedenciaLocal(FUENTE_SINTETICA, contrato.recurso_id, activo.asset_id, activo.sha256)
                procedencia_qa = ProcedenciaQA.desde_local(local)  # documento/adquisicion_id siguen None.
                limites_consumo = LimitesConsumoQA(max_resultados=p.max_resultados, max_bytes_lote=p.max_bytes_json)
                for nombre in ("A", "B"):
                    paso("recuperacion_" + nombre)
                    ruta = almacen.recuperar(activo.asset_id)
                    recuperaciones.append(fase)
                    traza.append((fase, "completada"))
                    paso("qa_" + nombre)
                    lector = LectorCSV(ruta, codificacion="utf-8", delimitador=",", campos_esperados=16,
                        encabezado_declarado=True, cancelacion=evento,
                        politica=PoliticaLecturaCSV(max_bytes_archivo=p.max_bytes,
                            max_registros=p.max_registros + 2))
                    qa = EvaluadorNivel0(lector, procedencia_qa, configuracion=contrato.configuracion,
                        limites=LimitesQA(max_registros=p.max_registros, max_resultados=p.max_resultados),
                        cancelacion=evento)
                    emitidos = []
                    try:
                        with qa:
                            for resultado in qa:
                                emitidos.append(resultado)
                    finally:
                        # También conserva los emitidos antes de una excepción.
                        nativos = tuple(emitidos)
                        resultados.append(nativos)
                        informes.append(qa.informe)
                        lecturas.append(lector.informe)
                    if evento.is_set():
                        raise _Detener("cancelacion_solicitada", EstadoEjecucion85G.CANCELADA)
                    if informes[-1].estado is not EstadoEvaluacionQA.COMPLETA:
                        raise _Detener("evaluacion_estructural_incompleta", EstadoEjecucion85G.INCOMPLETA)
                    # Otra comprobación física, sin confiar solo en el DTO de procedencia.
                    almacen.recuperar(activo.asset_id)
                    recuperaciones.append("post_qa_" + nombre)
                    traza.append((fase, "evaluacion_cerrada_y_original_recomprobado"))
                    paso("exportacion_" + nombre)
                    documentos, bytes_json = [], 0
                    exportaciones.append(documentos)
                    for resultado in nativos:
                        if evento.is_set():
                            raise _Detener("cancelacion_solicitada", EstadoEjecucion85G.CANCELADA)
                        contexto = ContextoExportacionQA("spica:experimental:85g", contrato.evaluacion_id,
                            contrato.entrada_id + ":" + str(resultado.registro.numero_registro),
                            configuracion=contrato.configuracion,
                            metadatos_requeridos=("documentacion_institucional",),
                            metadatos_ausentes=("documentacion_institucional",),
                            incertidumbres=("simulacion_sin_red", "sin_autorizacion_cientifica"))
                        documento = exportar_resultado_json(resultado, contexto)
                        bytes_json += len(documento.encode("utf-8"))
                        if bytes_json > p.max_bytes_json:
                            raise _Detener("limite_bytes_json", EstadoEjecucion85G.INCOMPLETA)
                        documentos.append(documento)
                    traza.append((fase, "completada"))
                    paso("consumo_" + nombre)
                    consumo = consumir_exportaciones(tuple(documentos), limites=limites_consumo)
                    consumos.append(consumo)
                    if consumo.estado is EstadoConsumoQA.VALIDACION_INCOMPLETA:
                        raise _Detener("validacion_contractual_incompleta", EstadoEjecucion85G.INCOMPLETA)
                    if (consumo.estado is not EstadoConsumoQA.CONTRATO_VALIDO_EN_ALCANCE
                            or consumo.diagnosticos_aceptados != len(nativos)):
                        raise _Detener("consumo_no_satisfactorio")
                    restricciones = tuple(x for r in nativos for x in restricciones_resultado(r))
                    conteos = tuple(sum(x.tipo is tipo for x in restricciones) for tipo in (
                        TipoRestriccionQA.INFORMATIVA, TipoRestriccionQA.BLOQUEO_USO_DEL_RESULTADO))
                    if conteos != (consumo.restricciones_informativas, consumo.restricciones_bloqueantes):
                        raise _Detener("restricciones_no_conservadas")
                    traza.append((fase, "restricciones_nativas_y_consumidas_coinciden"))
                paso("conciliacion")
                conciliacion = conciliar_lotes(tuple(LoteQA(nombre, consumo)
                    for nombre, consumo in zip(("A", "B"), consumos, strict=True)), limites_consumo=limites_consumo)
                if conciliacion.estado is not EstadoConciliacionQA.COINCIDENCIA:
                    raise _Detener("reproducciones_no_coincidentes")
                if evento.is_set():
                    raise _Detener("cancelacion_solicitada", EstadoEjecucion85G.CANCELADA)
                traza.append((fase, "reproducciones_del_mismo_activo_coinciden"))
                fase = "cierre"
            fase = "cierre"
        estado = EstadoEjecucion85G.CONCLUIDA
    except _Detener as error:
        estado, diagnosticos = error.estado, (error.codigo,)
    except ErrorIntegracionHTTPRAW as error:
        error_http_raw = (error.codigo, error.fase.value, error.codigo_http, error.intentos_http)
        if type(error.activo_id) is str and re.fullmatch(r"[0-9a-f]{32}", error.activo_id):
            activo_id = error.activo_id
        estado = (EstadoEjecucion85G.CANCELADA if error.codigo == "cancelado"
                  else EstadoEjecucion85G.FALLIDA)
        diagnosticos = ("fallo_http_raw_" + error.fase.value,)
    except Exception:
        # Se conserva la fase y un código fijo, nunca ruta/cuerpo/mensaje arbitrario.
        estado, diagnosticos = EstadoEjecucion85G.FALLIDA, ("fallo_componente_" + fase,)
    try:
        eliminados = raiz is None or not raiz.exists()
    except OSError:
        eliminados = False
    if not eliminados:
        estado = EstadoEjecucion85G.FALLIDA
        diagnosticos += ("limpieza_temporal_no_confirmada",)
    if captura_fallida:
        estado = EstadoEjecucion85G.FALLIDA
        diagnosticos += ("captura_previa_no_disponible",)
    if control_final_fallido:
        estado = EstadoEjecucion85G.FALLIDA
        diagnosticos += ("control_fisico_pre_cierre_fallido",)
    if sorted(abiertos) != sorted(cerrados):
        estado = EstadoEjecucion85G.FALLIDA
        diagnosticos += ("cierre_recursos_no_confirmado",)
    traza.append(("cierre", "temporales_eliminados" if eliminados else "revision_necesaria"))
    traza.append((fase, estado.value))
    return informe_actual(eliminados)
