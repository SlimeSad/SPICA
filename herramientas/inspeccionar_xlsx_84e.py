"""Diagnóstico OOXML aislado 84-E. No ejecuta celdas ni extrae archivos.

No es un importador de observaciones o una API científica. Devuelve inventario
literal en memoria; el llamador controla qué metadatos publica y su autorización.
"""

from io import BytesIO
import re
from threading import Event
import time
from zipfile import ZipFile

from spica.adquisicion.verificacion import PoliticaEstructura
from spica.adquisicion.verificacion._xlsx import _XML, _relaciones, inspeccionar_zip, HOJAS, OFICINA
from herramientas.piloto_pnda_84c import _huella

VERSION = "0.1.0"
MAX_ARCHIVO = 1_048_576
MAX_CELDAS = 2048
MAX_CADENAS = 4096
MAX_TEXTO = 8192
MAX_TEXTO_TOTAL = 131_072
POLITICA = PoliticaEstructura(max_entradas_zip=64, max_central_zip=65_536,
    max_bytes_descomprimidos=4_194_304, max_bytes_entrada=524_288,
    max_expansion=100, max_bytes_xml=524_288, max_nodos_xml=20_000,
    max_profundidad_xml=32, tamano_bloque=65_536)


class ErrorDiagnostico(Exception):
    """Código técnico; no reproduce cuerpos o rutas recibidos."""


def _exigir(condicion, codigo):
    if not condicion:
        raise ErrorDiagnostico(codigo)


def inspeccionar_bytes(datos, *, segundos=5.0):
    _exigir(type(datos) is bytes and len(datos) <= MAX_ARCHIVO, "limite_archivo")
    _exigir(type(segundos) in (int, float) and 0 < segundos <= 30, "plazo_no_admitido")
    fin = time.monotonic() + segundos
    def plazo():
        _exigir(time.monotonic() <= fin, "plazo_excedido")
    class Lectura(BytesIO):
        acumulados = 0
        def read(self, cantidad=-1):
            plazo()
            if cantidad < 0:
                cantidad = len(datos) - self.tell()
            _exigir(cantidad <= 65_557, "lectura_individual_excesiva")
            r = super().read(cantidad)
            self.acumulados += len(r)
            _exigir(self.acumulados <= 8_388_608, "limite_lecturas_zip")
            return r
    contexto = dict(comprobaciones=[], descomprimidos=0)
    try:
        formato, completo = inspeccionar_zip(Lectura(datos), len(datos), POLITICA, contexto)
        _exigir(formato == "xlsx" and completo, "estructura_xlsx_no_admitida")
        arboles, manifiesto = {}, []
        ctx = dict(descomprimidos=0)
        with ZipFile(Lectura(datos)) as z:
            nombres = {i.filename for i in z.infolist() if not i.is_dir()}
            for i in z.infolist():
                plazo()
                if i.is_dir():
                    continue
                xml = _XML(POLITICA, ctx, True) if i.filename.endswith((".xml", ".rels")) else None
                if xml is not None:
                    # Añadir texto a la construcción segura existente; jamás evaluar.
                    xml.parser.CharacterDataHandler = xml.arbol.data
                reales = 0
                with z.open(i) as f:
                    while b := f.read(POLITICA.tamano_bloque):
                        plazo()
                        reales += len(b)
                        ctx["descomprimidos"] += len(b)
                        _exigir(reales <= POLITICA.max_bytes_xml and
                                ctx["descomprimidos"] <= POLITICA.max_bytes_descomprimidos, "limite_xml_o_volumen")
                        if xml is not None:
                            xml.alimentar(b)
                _exigir(reales == i.file_size, "tamano_real_incoherente")
                manifiesto.append(dict(parte=i.filename,comprimidos=i.compress_size,
                    declarados=i.file_size,reales=reales,crc32=f"{i.CRC:08x}",metodo=i.compress_type))
                if xml is not None:
                    arboles[i.filename] = xml.cerrar()
        relaciones = {n: _relaciones(a, n, nombres, {}) for n,a in arboles.items() if n.endswith(".rels")}
        externas = [(n, rid, tipo.rsplit("/",1)[-1]) for n, rs in relaciones.items()
                    for rid, (tipo, destino) in rs.items() if destino is None]
        cadenas = []
        def texto_rico(e, ns):
            if e is None:
                return ""
            partes = []
            for h in e:
                if h.tag == ns + "t": partes.append(h.text or "")
                elif h.tag == ns + "r": partes.extend(x.text or "" for x in h.findall(ns + "t"))
            return "".join(partes)
        for n, a in arboles.items():
            if n == "xl/sharedStrings.xml":
                ns = a.tag.split("}")[0] + "}"
                _exigir(a.tag == ns + "sst", "cadenas_compartidas_no_reconocidas")
                for si in a.findall(ns + "si"):
                    t = texto_rico(si, ns)
                    _exigir(len(t) <= MAX_TEXTO and len(cadenas) < MAX_CADENAS, "limite_cadenas")
                    cadenas.append(t)
        estilos = []
        formatos = {}
        if "xl/styles.xml" in arboles:
            a = arboles["xl/styles.xml"]; ns = a.tag.split("}")[0] + "}"
            for x in a.findall(ns + "numFmts/" + ns + "numFmt"):
                formatos[x.get("numFmtId")] = x.get("formatCode")
            estilos = [x.get("numFmtId") for x in a.findall(ns + "cellXfs/" + ns + "xf")]
            _exigir(len(estilos) <= 512 and len(formatos) <= 512, "limite_estilos")
        libro = arboles["xl/workbook.xml"]
        ns = libro.tag.split("}")[0] + "}"
        hojas = []
        total_celdas = total_texto = 0
        for h in libro.find(ns + "sheets"):
            plazo()
            _exigir(len(hojas) < 8, "limite_hojas")
            rid = next(h.get("{" + x + "}id") for x in OFICINA if h.get("{" + x + "}id") is not None)
            parte = relaciones["xl/_rels/workbook.xml.rels"][rid][1]
            a = arboles[parte]; s = a.tag.split("}")[0] + "}"
            _exigir(a.tag in {"{"+x+"}worksheet" for x in HOJAS}, "hoja_no_reconocida")
            celdas, vistos = [], set()
            filas = a.findall(s + "sheetData/" + s + "row")
            for fila in filas:
                for c in fila.findall(s + "c"):
                    plazo()
                    ref, tipo = c.get("r"), c.get("t", "n")
                    _exigir(type(ref) is str and re.fullmatch(r"[A-Z]{1,3}[1-9][0-9]{0,6}",ref)
                            and ref not in vistos, "referencia_celda_ambigua")
                    vistos.add(ref)
                    _exigir(tipo in ("s","inlineStr","n","b","str","e","d"), "tipo_celda_no_admitido")
                    v, f = c.find(s + "v"), c.find(s + "f")
                    almacenado = v.text if v is not None else None
                    literal = almacenado
                    if tipo == "s":
                        _exigir(almacenado is not None and almacenado.isascii() and almacenado.isdigit()
                                and len(almacenado) <= 6, "indice_cadena_invalido")
                        indice = int(almacenado)  # Índice OOXML; nunca código institucional.
                        _exigir(indice < len(cadenas), "indice_cadena_fuera_de_rango")
                        literal = cadenas[indice]
                    elif tipo == "inlineStr":
                        literal = texto_rico(c.find(s + "is"),s)
                    if f is not None:
                        literal = None  # El caché no se promueve a texto oficial calculado.
                    _exigir(literal is None or len(literal) <= MAX_TEXTO, "limite_texto_celda")
                    total_texto += len(literal or "")
                    total_celdas += 1
                    _exigir(total_texto <= MAX_TEXTO_TOTAL and total_celdas <= MAX_CELDAS, "limite_celdas_o_texto")
                    estilo = c.get("s")
                    if estilo is not None:
                        _exigir(estilo.isascii() and estilo.isdigit() and len(estilo) <= 4
                                and int(estilo) < len(estilos), "indice_estilo_invalido")
                    numfmt = estilos[int(estilo)] if estilo is not None else None
                    celdas.append(dict(celda=ref,tipo_ooxml=tipo,literal=literal,valor_almacenado=almacenado,
                        formula_presente=f is not None,formula_texto=f.text if f is not None else None,
                        estilo=estilo,numfmt_id=numfmt,formato_personalizado=formatos.get(numfmt)))
            dimension = a.find(s + "dimension")
            hojas.append(dict(nombre=h.get("name"),sheet_id=h.get("sheetId"),estado=h.get("state","visible"),parte=parte,
                dimension_declarada=dimension.get("ref") if dimension is not None else None,
                filas_xml=len(filas),filas_con_valores=sorted({int(re.search(r"[0-9]+$",c["celda"])[0]) for c in celdas if c["literal"] is not None}),
                celdas=celdas,combinaciones=[x.get("ref") for x in a.findall(s+"mergeCells/"+s+"mergeCell")],
                tablas_referenciadas=len(a.findall(s+"tableParts/"+s+"tablePart"))))
        propiedades = {}
        for n in ("docProps/core.xml","docProps/app.xml","docProps/custom.xml"):
            if n not in arboles:
                continue
            valores = {}
            for e in arboles[n]:
                clave = e.tag.rsplit("}",1)[-1]
                if clave in ("created","modified","revision","title","subject","description","category","version","Application","AppVersion"):
                    valores[clave] = e.text
                else:
                    valores[clave + "_presente_sin_publicar"] = True
            propiedades[n] = valores
        plazo()
        return dict(version_diagnostico=VERSION,limites=dict(max_archivo=MAX_ARCHIVO,max_entradas=64,
            max_descomprimidos=POLITICA.max_bytes_descomprimidos,max_xml=POLITICA.max_bytes_xml,
            max_nodos=POLITICA.max_nodos_xml,max_profundidad=32,max_celdas=MAX_CELDAS,
            max_cadenas=MAX_CADENAS,max_texto_total=MAX_TEXTO_TOTAL,segundos=segundos),
            partes=manifiesto,bytes_descomprimidos=ctx["descomprimidos"],comprobaciones=contexto["comprobaciones"],
            partes_no_xml=[x["parte"] for x in manifiesto if x["parte"] not in arboles],
            relaciones_externas_no_abiertas=externas,cadenas_compartidas=len(cadenas),hojas=hojas,
            tablas=[dict(parte=n,nombre=a.get("name"),ref=a.get("ref"),columnas=[x.get("name") for x in a.iter() if x.tag.endswith("}tableColumn")])
                    for n,a in arboles.items() if n.startswith("xl/tables/")],
            nombres_definidos=[dict(nombre=x.get("name"),texto_no_evaluado=x.text) for x in libro.findall(ns+"definedNames/"+ns+"definedName")],
            propiedades=propiedades,formulas=sum(c["formula_presente"] for h in hojas for c in h["celdas"]))
    except ErrorDiagnostico:
        raise
    except Exception:
        raise ErrorDiagnostico("zip_xml_o_celdas_no_admitidos") from None


def inspeccionar_archivo(ruta, *, tamano_esperado, sha256_esperado):
    """Lectura del único archivo aportado; huella previa/posterior, sin escrituras."""
    antes = _huella(ruta, MAX_ARCHIVO, Event())
    _exigir(antes[:2] == (tamano_esperado,sha256_esperado), "integridad_previa_no_coincide")
    try:
        with ruta.open("rb") as f:
            datos = f.read(MAX_ARCHIVO + 1)
        import hashlib
        _exigir((len(datos),hashlib.sha256(datos).hexdigest()) == antes[:2], "snapshot_no_coincide")
        resultado = inspeccionar_bytes(datos)
    finally:
        despues = _huella(ruta, MAX_ARCHIVO, Event())
        _exigir(despues == antes, "integridad_posterior_no_coincide")
    resultado.update(tamano=antes[0],sha256=antes[1],integridad_antes_despues=True)
    return resultado
