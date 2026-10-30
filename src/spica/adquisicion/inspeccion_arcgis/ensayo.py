"""Dos rutas de metadatos explícitas; único transporte: ClienteHTTP de SPICA."""

from datetime import datetime, timezone
from threading import Event
from typing import Callable

import httpx

from ..nucleo.temporal import instante_utc
from ..transportes import ClienteHTTP, ConfiguracionHTTP, ErrorTransporteHTTP, PoliticaReintentos
from .inspector import inspeccionar_metadatos
from .modelos import EstadoMetadatos, IntentoMetadatos, LIMITE_METADATOS, ObjetivoArcGIS, TipoMetadatos


class EnsayoMetadatosArcGIS:
    """Uso único y secuencial; no abre RAW/SQLite, no guarda archivos ni autentica.

    Cada GET usa una instancia nueva del cliente común. Una cookie recibida nunca
    se reutiliza en la siguiente petición. Un fallo consume la ruta, sin reintento.
    """

    def __init__(self, objetivo: ObjetivoArcGIS, *, transporte: httpx.BaseTransport | None = None,
                 cancelacion: Event | None = None, reloj: Callable[[], datetime] | None = None):
        if type(objetivo) is not ObjetivoArcGIS or (cancelacion is not None and type(cancelacion) is not Event):
            raise TypeError("Objetivo y cancelación tipados requeridos")
        self.objetivo, self.transporte = objetivo, transporte
        self.cancelacion = cancelacion if cancelacion is not None else Event()
        self.reloj = reloj or (lambda: datetime.now(timezone.utc))
        self._usadas = set()
        self._historial: tuple[IntentoMetadatos, ...] = ()

    @property
    def historial(self):
        return self._historial

    def consultar_servicio(self) -> IntentoMetadatos:
        return self._consultar(TipoMetadatos.SERVICIO, self.objetivo.url_servicio)

    def consultar_capa(self) -> IntentoMetadatos:
        if not self._historial or self._historial[0].tipo is not TipoMetadatos.SERVICIO or not self._historial[0].permite_continuar:
            raise RuntimeError("Servicio no validado; consulta de capa bloqueada")
        return self._consultar(TipoMetadatos.CAPA, self.objetivo.url_capa)

    def _consultar(self, tipo, url):
        if tipo in self._usadas:
            raise RuntimeError("Ruta consumida; no repetir este ensayo")
        self._usadas.add(tipo)
        inicio, respuesta, validacion, error, intentos = instante_utc(self.reloj()), None, None, None, 0
        codigo, content_type, longitud, cuerpo = None, None, None, None
        cliente = None
        try:
            if self.cancelacion.is_set():
                error = "cancelado_antes_del_get"
            else:
                config = ConfiguracionHTTP(timeout_conexion=10, timeout_lectura=30,
                    timeout_escritura=30, timeout_pool=10, verificar_tls=True,
                    max_bytes_respuesta=LIMITE_METADATOS)
                # Reutiliza controles de conexión, TLS, errores y lectura por bloques.
                with ClienteHTTP((self.objetivo.origen,), config, transporte=self.transporte,
                                 politica_reintentos=PoliticaReintentos(max_intentos=1),
                                 cancelacion=self.cancelacion) as cliente:
                    respuesta = cliente.get(url, parametros={"f": "json"})
                intentos = max((r.numero for r in cliente.historial_intentos), default=0)
                codigo = respuesta.codigo_http
                content_type = respuesta.cabeceras.get("content-type")
                if content_type is not None:
                    # Solo este encabezado técnico; no guardar cookies ni el mapa completo.
                    from ..catalogo.persistencia import _publico
                    try:
                        if len(content_type) > 256:
                            raise ValueError
                        _publico(content_type)
                    except Exception:
                        content_type = "omitido_por_seguridad"
                longitud = respuesta.cabeceras.get("content-length")
                longitud = int(longitud) if longitud is not None else None
                cuerpo = respuesta.contenido
                validacion = inspeccionar_metadatos(respuesta, tipo, self.objetivo)
                if validacion.estado is not EstadoMetadatos.COHERENTE:
                    error = "validacion_de_metadatos_no_superada"
        except ErrorTransporteHTTP as exc:
            error, codigo, intentos = exc.tipo.value, exc.codigo_http, exc.intentos
        except Exception:
            error = "ensayo_no_disponible"
            if cliente is not None:
                intentos = max((r.numero for r in cliente.historial_intentos), default=0)
        registro = IntentoMetadatos(tipo, url + "?f=json", inicio, instante_utc(self.reloj()), intentos,
            codigo, content_type, longitud, validacion, error, cuerpo)
        self._historial += (registro,)
        return registro
