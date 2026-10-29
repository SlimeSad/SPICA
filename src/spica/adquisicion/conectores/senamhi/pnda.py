"""Descubrimiento HTML público y piloto XLSX; sin motor HTTP propio."""

from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import PurePosixPath
from urllib.parse import urljoin, urlsplit

from ...almacenamiento import DeclaracionRAW, ErrorAlmacenamientoRAW
from ...almacenamiento.raw import _referencia_publica
from ...catalogo import (
    CapacidadCatalogo, CatalogoCientifico, EstadoVerificacion, FuenteCatalogo,
    MecanismoAdquisicion, ProcedenciaCatalogo, ProductoCatalogo, RecursoCatalogo,
    EstadoRegistroDocumental, EvidenciaDocumental,
)
from ...integracion import AdaptadorHTTPRAW
from ...nucleo import RecursoDescubierto
from ...transportes import ClienteHTTP
from .modelos import (
    ORIGEN_PNDA, PAGINA_GBON_RBON, FUENTE_SENAMHI, RolRecurso,
    RecursoPublicado, CatalogoRecursos, AdquisicionPNDA, ErrorConectorPNDA,
)


def _publica(texto):
    if not isinstance(texto, str) or not texto.strip():
        raise ErrorConectorPNDA("referencia_publica_requerida")
    try:
        _referencia_publica(texto, sanear_url=False)
    except (ErrorAlmacenamientoRAW, TypeError, ValueError):
        raise ErrorConectorPNDA("referencia_no_publica_o_ambigua") from None


def _url_producto(url):
    if not isinstance(url, str):
        raise ErrorConectorPNDA("referencia_producto_invalida")
    _publica(url)
    partes = urlsplit(url)
    identificador = partes.path.removeprefix("/dataset/")
    if (partes.scheme + "://" + partes.netloc != ORIGEN_PNDA
            or not partes.path.startswith("/dataset/") or partes.query or partes.fragment
            or not identificador or "/" in identificador):
        raise ErrorConectorPNDA("producto_fuera_del_ambito_pnda")


class _Publicacion(HTMLParser):
    """Solo enlaces de descarga de distribuciones, nunca scripts ni formularios."""
    def __init__(self, max_recursos):
        super().__init__(convert_charrefs=True)
        self.pila = []
        self.distribuciones = []
        self.licencia = None
        self.max_recursos = max_recursos

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        distribucion = {"titulo": None, "enlaces": []} if a.get("property") == "dcat:Distribution" else None
        if distribucion is not None:
            if len(self.distribuciones) >= self.max_recursos:
                raise ErrorConectorPNDA("limite_distribuciones_excedido")
            self.distribuciones.append(distribucion)
        licencia = "pane-dkan-sitewide-dkan-sitewide-license" in a.get("class", "").split()
        if tag not in {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}:
            self.pila.append((tag, distribucion, licencia))
            if len(self.pila) > 256:
                raise ErrorConectorPNDA("html_excesivamente_anidado")
        activa = next((d for _, d, _ in reversed(self.pila) if d is not None), None)
        if tag == "a":
            href = a.get("href")
            if href and any(l for _, _, l in self.pila) and self.licencia is None:
                self.licencia = href
            if activa is not None:
                if "heading" in a.get("class", "").split():
                    activa["titulo"] = a.get("title") or None
                if href and "data-link" in a.get("class", "").split():
                    if len(activa["enlaces"]) >= 8:
                        raise ErrorConectorPNDA("limite_enlaces_distribucion_excedido")
                    activa["enlaces"].append(href)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for i in range(len(self.pila) - 1, -1, -1):
            if self.pila[i][0] == tag:
                del self.pila[i:]
                break


class ConectorSENAMHIPNDA:
    """Recibe componentes prestados: el llamador conserva su ciclo de vida.

    El piloto solo adquiere diccionarios XLSX. Descubrir otros formatos no los
    autoriza para descarga ni comprueba su contenido. No recibe filtros remotos.
    """
    def __init__(self, cliente: ClienteHTTP, adaptador: AdaptadorHTTPRAW | None = None,
                 *, pagina_producto: str = PAGINA_GBON_RBON, max_recursos: int = 100):
        if not isinstance(cliente, ClienteHTTP):
            raise TypeError("Se requiere ClienteHTTP")
        _url_producto(pagina_producto)
        if not cliente.configuracion.verificar_tls:
            raise ErrorConectorPNDA("tls_verificado_requerido")
        if cliente.configuracion.max_bytes_respuesta > 1_048_576:
            raise ErrorConectorPNDA("limite_descubrimiento_superior_a_un_mib")
        if type(max_recursos) is not int or not 1 <= max_recursos <= 1000:
            raise ValueError("max_recursos debe estar entre 1 y 1000")
        if adaptador is not None:
            if not isinstance(adaptador, AdaptadorHTTPRAW) or adaptador.cliente is not cliente:
                raise ErrorConectorPNDA("adaptador_no_comparte_cliente")
            if adaptador.max_bytes > 1_048_576:
                raise ErrorConectorPNDA("limite_piloto_superior_a_un_mib")
            if "producto_id" not in adaptador.almacen.claves:
                raise ErrorConectorPNDA("almacen_requiere_parametro_publico_producto_id")
        self.cliente, self.adaptador = cliente, adaptador
        self.pagina, self.max_recursos = pagina_producto, max_recursos
        self.producto_id = urlsplit(pagina_producto).path.removeprefix("/dataset/")
        self._descubierto = None
        self.registros_documentales = ()
        self._revisiones = {}
        self._conflicto_catalogo = False

    def descubrir(self) -> CatalogoRecursos:
        self._descubierto = None  # Un fallo nunca deja una autorización anterior vigente.
        self.registros_documentales = ()
        self._revisiones = {}
        respuesta = self.cliente.get(self.pagina)
        if respuesta.codigo_http != 200 or "text/html" not in respuesta.cabeceras.get("content-type", "").lower():
            raise ErrorConectorPNDA("pagina_producto_no_es_html_publico")
        try:
            html = respuesta.contenido.decode("utf-8-sig")
        except UnicodeDecodeError:
            raise ErrorConectorPNDA("codificacion_pagina_no_admitida") from None
        parser = _Publicacion(self.max_recursos)
        parser.feed(html)
        parser.close()
        fecha = datetime.now(timezone.utc)
        procedencia = ProcedenciaCatalogo(self.pagina, fecha, "GET_publico_HTML",
            "HTTP_200_pagina;enlaces_declarados_dcat:Distribution;sin_comprobar_archivos")
        licencia = urljoin(self.pagina, parser.licencia) if parser.licencia else None
        if licencia:
            _publica(licencia)
        recursos, avisos, vistos = [], [], set()
        for distribucion in parser.distribuciones:
            titulo = distribucion["titulo"]
            if titulo:
                _publica(titulo)
            for href in distribucion["enlaces"]:
                try:
                    url = urljoin(self.pagina, href)
                    _publica(href)
                    _publica(url)
                    partes = urlsplit(url)
                    if (partes.scheme + "://" + partes.netloc != ORIGEN_PNDA
                            or not partes.path.startswith("/sites/default/files/")
                            or partes.query or partes.fragment):
                        raise ErrorConectorPNDA("recurso_fuera_del_ambito")
                except (ErrorConectorPNDA, ValueError):
                    avisos.append("enlace_no_publico_o_fuera_del_ambito_omitido")
                    continue
                if url in vistos:
                    avisos.append("enlace_duplicado_en_publicacion")
                    continue
                vistos.add(url)
                if len(recursos) >= self.max_recursos:
                    raise ErrorConectorPNDA("limite_recursos_excedido")
                sufijo = PurePosixPath(partes.path).suffix
                formato = sufijo[1:].lower() if sufijo else None
                nombre = (titulo or "").casefold()
                rol = (RolRecurso.DICCIONARIO if nombre.startswith("diccionario")
                       else RolRecurso.METADATOS if nombre.startswith("metadatos") else RolRecurso.PUBLICADO)
                recursos.append(RecursoPublicado(self.producto_id,
                    RecursoDescubierto(FUENTE_SENAMHI, url, url, formato=formato),
                    self.pagina, href, titulo, rol, procedencia))
        if not recursos:
            raise ErrorConectorPNDA("sin_recursos_publicados_reconocibles")
        formatos = tuple(dict.fromkeys(r.recurso.formato for r in recursos if r.recurso.formato is not None))
        producto = ProductoCatalogo(FUENTE_SENAMHI, self.producto_id, procedencia,
            formatos_declarados=formatos, modalidad_acceso="archivos_publicados_HTTP",
            restricciones_licencia=licencia)
        # Sin asumir autenticación/cobertura del CSV por haber leído su página.
        resultado = CatalogoRecursos(producto, tuple(recursos),
            tuple(dict.fromkeys(avisos + ["sin_filtros_remotos_verificados", "formatos_declarados_no_detectados"])))
        self._descubierto = resultado
        return resultado

    def registrar_catalogo(self, catalogo: CatalogoCientifico):
        """Política documental explícita; conserva los tres registros de retorno.

        Los resultados detallados, incluidos los recursos, quedan disponibles en
        registros_documentales. Cada registro es transaccional; el lote no es una
        transacción global. Una repetición segura permite completar un lote fallido.
        """
        if self._descubierto is None:
            raise ErrorConectorPNDA("descubrimiento_previo_requerido")
        if not isinstance(catalogo, CatalogoCientifico):
            raise TypeError("Se requiere CatalogoCientifico")
        producto = self._descubierto.producto
        institucional = ProcedenciaCatalogo("urn:spica:fuente:SENAMHI", producto.procedencia.revisada_utc,
            "identidad_institucional_declarada_por_conector")
        fuente = FuenteCatalogo(FUENTE_SENAMHI, institucional,
            nombre="Servicio Nacional de Meteorología e Hidrología del Perú - SENAMHI",
            estado=EstadoVerificacion.DECLARADO)
        capacidad = CapacidadCatalogo(self.pagina, FUENTE_SENAMHI, self.producto_id,
            MecanismoAdquisicion.HTTP_DIRECTO, producto.procedencia, estado=EstadoVerificacion.DECLARADO)
        recursos = tuple(RecursoCatalogo(r.recurso.fuente, r.producto_id, r.recurso.identificador,
            r.recurso.localizador, r.procedencia, referencia_publicacion=r.referencia_publicacion,
            titulo=r.titulo, formato=r.recurso.formato, tipo_medio=r.recurso.tipo_medio,
            referencia_licencia=producto.restricciones_licencia) for r in self._descubierto.recursos)
        self.registros_documentales, self._revisiones = (), {}
        self._conflicto_catalogo = True  # También bloquea adquisiciones si el lote se interrumpe.
        for entidad in (fuente, producto, capacidad, *recursos):
            resultado = catalogo.registrar_documental(entidad)
            self.registros_documentales += (resultado,)
            if resultado.estado is EstadoRegistroDocumental.CONTRADICCION:
                self._conflicto_catalogo = True
                raise ErrorConectorPNDA("contradiccion_documental_requiere_evaluacion")
        self._conflicto_catalogo = False
        self._revisiones = {r.registro.entidad.identificador: r.registro.revision
                            for r in self.registros_documentales if isinstance(r.registro.entidad, RecursoCatalogo)}
        return tuple(r.registro for r in self.registros_documentales[:3])

    def adquirir(self, recurso_id: str, *, proyecto_id: str, objeto_id: str) -> AdquisicionPNDA:
        if self._descubierto is None:
            raise ErrorConectorPNDA("descubrimiento_previo_requerido")
        if self._conflicto_catalogo:
            raise ErrorConectorPNDA("contradiccion_documental_no_resuelta")
        publicado = next((r for r in self._descubierto.recursos if r.recurso.identificador == recurso_id), None)
        if publicado is None:
            raise ErrorConectorPNDA("recurso_no_publicado_en_descubrimiento_actual")
        if publicado.rol is not RolRecurso.DICCIONARIO or publicado.recurso.formato != "xlsx":
            raise ErrorConectorPNDA("piloto_solo_autoriza_diccionario_xlsx")
        if self.adaptador is None:
            raise ErrorConectorPNDA("adaptador_raw_requerido")
        for texto in (proyecto_id, objeto_id):
            _publica(texto)
        declaracion = DeclaracionRAW(proyecto_id, objeto_id, FUENTE_SENAMHI, recurso_id,
            procedencia=publicado.recurso.localizador,
            parametros_publicos={"producto_id": publicado.producto_id}, formato_declarado=publicado.recurso.formato)
        documento = EvidenciaDocumental(FUENTE_SENAMHI, recurso_id, producto_id=publicado.producto_id,
            referencia_publicacion=publicado.referencia_publicacion,
            descubierta_utc=publicado.procedencia.revisada_utc,
            referencia_licencia=self._descubierto.producto.restricciones_licencia,
            revision_documental=self._revisiones.get(recurso_id),
            revision_producto=self.registros_documentales[1].registro.revision if self._revisiones else None,
            revision_fuente=self.registros_documentales[0].registro.revision if self._revisiones else None,
            estado=EstadoVerificacion.DECLARADO, capacidades_documentadas=(MecanismoAdquisicion.HTTP_DIRECTO,),
            procedencia=publicado.procedencia)
        resultado = self.adaptador.adquirir_documentado(publicado.recurso.localizador, declaracion, documento)
        fecha = resultado.activo.comprobacion_utc
        evidencia = ProcedenciaCatalogo(publicado.recurso.localizador, fecha, "GET_stream_HTTP_RAW",
            "tamano_y_SHA256_releidos_fisicamente;asset_id=" + resultado.activo.asset_id)
        capacidad = CapacidadCatalogo(recurso_id, FUENTE_SENAMHI, publicado.producto_id,
            MecanismoAdquisicion.HTTP_DIRECTO, evidencia, estado=EstadoVerificacion.VERIFICADO,
            comprobada_utc=fecha)
        # Esta capacidad se devuelve por recurso: no se publica como garantía de
        # todos los recursos del producto en el catálogo usado por el planificador.
        return AdquisicionPNDA(publicado, resultado, capacidad)
