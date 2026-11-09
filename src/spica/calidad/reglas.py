"""Registro cerrado de reglas Nivel 0; ninguna configuración ejecuta código."""

from ..perfilado.interpretacion import (VERSION_INTERPRETACION, clasificar_hora_literal,
                                        interpretar_fecha_civil, interpretar_numero)
from .modelos import (CategoriaQA as C, ConfiguracionQA, EstadoResultadoQA as E, FormatoQA,
                      ProcedenciaQA, RegistroQA, ReglaQA, ResultadoQA)

REGLAS_NIVEL0 = tuple(ReglaQA(f"L0-{prefijo}-{numero:03d}", "1.0.0", categoria, texto)
    for prefijo, categoria, textos in (
        ("EST", C.ESTRUCTURA, ("Coherencia del registro tabular recibido",)),
        ("VAL", C.VALORES, ("Presencia literal", "Número interpretable finito", "Literal no finito",
                            "Conformidad con formato numérico documental explícito")),
        ("TMP", C.TEMPORALES, ("Fecha civil documental", "HORA documental", "Referencia de zona horaria",
                              "Posibilidad de determinar un instante absoluto")),
        ("ID", C.IDENTIDAD_UBICACION, ("Nombre de estación", "Identidad física documentada",
            "Coordenadas declaradas disponibles", "Representación documental UBIGEO", "Metadatos de ubicación presentes")),
        ("PROV", C.PROCEDENCIA, ("Referencia de institución", "Referencia de recurso", "Referencia de adquisición",
            "Referencia de activo RAW", "SHA-256 de referencia", "Documento asociado", "Licencia declarada",
            "Coherencia con procedencia de la observación")))
    for numero, texto in enumerate(textos, 1))


def seleccionar_reglas(configuracion: ConfiguracionQA):
    ids = {r.identificador for r in REGLAS_NIVEL0}
    if any(r not in ids for r in configuracion.reglas):
        raise ValueError("Regla no registrada")
    reglas = tuple(r for r in REGLAS_NIVEL0 if r.categoria in configuracion.categorias
                   and (not configuracion.reglas or r.identificador in configuracion.reglas))
    if not reglas:
        raise ValueError("Selección sin reglas aplicables")
    return reglas


def _documento_aplicable(p):
    return p.documento is not None and p.documento.fuente == p.fuente and p.documento.recurso_id == p.recurso_id


def evaluar_registro(registro: RegistroQA, procedencia: ProcedenciaQA, *, configuracion=None):
    """Generador puro de resultados. No afirma alcance ni integridad del archivo."""
    if not isinstance(registro, RegistroQA) or not isinstance(procedencia, ProcedenciaQA):
        raise TypeError("Registro y procedencia QA tipados requeridos")
    c = configuracion if configuracion is not None else ConfiguracionQA()
    if not isinstance(c, ConfiguracionQA):
        raise TypeError("Se requiere ConfiguracionQA")
    reglas = seleccionar_reglas(c)
    campos = dict(registro.campos_originales)
    formatos = {f.campo: f for f in c.formatos}
    numeros = {}  # Como máximo las tres variables; una interpretación por celda.

    def numero(campo):
        if campo not in numeros:
            numeros[campo] = interpretar_numero(campos[campo], limites=c.politica_numerica)
        return numeros[campo]

    def emitir(regla, nombres, estado, codigo, evidencia=(), parametros=(), valores=None):
        originales = tuple((n, campos.get(n)) for n in nombres) if valores is None else valores
        return ResultadoQA(regla, registro, procedencia, originales, tuple(evidencia), tuple(parametros), estado, codigo)

    def formato(regla, campo, esperado):
        texto = campos.get(campo)
        f = formatos.get(campo)
        if texto is None:
            return emitir(regla, (campo,), E.EVALUACION_INCOMPLETA, "campo_no_disponible")
        if f is None or f.formato is not esperado:
            return emitir(regla, (campo,), E.NO_EVALUADO, "formato_documental_no_disponible")
        if texto == "":
            return emitir(regla, (campo,), E.NO_EVALUADO, "vacio_sin_formato_comprobable", (f.evidencia,))
        parametros = (("formato", esperado.value), ("interpretacion", VERSION_INTERPRETACION))
        if esperado is FormatoQA.NUMERO_ASCII:
            n = numero(campo)
            if n.clase == "fuera_presupuesto_numerico":
                return emitir(regla, (campo,), E.EVALUACION_INCOMPLETA, "presupuesto_numerico_excedido",
                               (f.evidencia,), parametros)
            correcto = n.clase == "finito"
        elif esperado is FormatoQA.AAAAMMDD:
            correcto = interpretar_fecha_civil(texto) is not None
            if not correcto and len(texto) == 8 and texto.isascii() and texto.isdigit():
                return emitir(regla, (campo,), E.PROBLEMA_TECNICO, "fecha_civil_invalida",
                               (f.evidencia,), parametros)
        elif esperado is FormatoQA.HHMMSS:
            correcto = clasificar_hora_literal(texto) == "hhmmss_lexico"
        else:
            correcto = len(texto) == 6  # Solo anchura documentada, sin inventar un catálogo de códigos.
        return emitir(regla, (campo,), E.COMPROBACION_SATISFECHA if correcto else E.ALERTA_DOCUMENTAL,
                       "formato_documental_coincide" if correcto else "representacion_documental_discrepante",
                       (f.evidencia,), parametros)

    for regla in reglas:
        rid = regla.identificador
        objetivos = c.variables if regla.categoria is C.VALORES else (None,)
        for campo in objetivos:
            if not registro.estructura_correcta:
                # Conservar el objetivo por variable incluso si no se pudo
                # evaluarlo; la fila completa sigue en registro y su tupla bruta.
                nombres = (campo,) if campo is not None else tuple(campos)
                yield emitir(regla, nombres, E.EVALUACION_INCOMPLETA, "estructura_no_evaluable")
                continue
            if rid == "L0-EST-001":
                yield emitir(regla, (), E.COMPROBACION_SATISFECHA, "estructura_recibida_coherente")
            elif regla.categoria is C.VALORES:
                valor = campos.get(campo)
                parametros = (("interpretacion", VERSION_INTERPRETACION),
                    ("max_caracteres", str(c.politica_numerica.max_caracteres_numero)),
                    ("max_digitos", str(c.politica_numerica.max_digitos_numero)),
                    ("max_exponente", str(c.politica_numerica.max_exponente)))
                if valor is None:
                    yield emitir(regla, (campo,), E.EVALUACION_INCOMPLETA, "campo_no_disponible")
                elif rid == "L0-VAL-001":
                    yield emitir(regla, (campo,), E.PROBLEMA_TECNICO if valor == "" else E.COMPROBACION_SATISFECHA,
                        "campo_vacio_sin_inferir_medicion" if valor == "" else "valor_literal_presente")
                elif rid == "L0-VAL-004":
                    yield formato(regla, campo, FormatoQA.NUMERO_ASCII)
                elif valor == "":
                    yield emitir(regla, (campo,), E.NO_EVALUADO, "vacio_sin_numero")
                else:
                    n = numero(campo)
                    if n.clase == "fuera_presupuesto_numerico":
                        estado, codigo = E.EVALUACION_INCOMPLETA, "presupuesto_numerico_excedido"
                    elif rid == "L0-VAL-002":
                        estado, codigo = {
                            "finito": (E.COMPROBACION_SATISFECHA, "numero_finito_interpretable"),
                            "no_finito": (E.NO_EVALUADO, "no_finito_tratado_por_regla_especifica"),
                            "no_interpretable": (E.PROBLEMA_TECNICO, "numero_no_interpretable")}[n.clase]
                    else:
                        estado, codigo = {
                            "finito": (E.COMPROBACION_SATISFECHA, "numero_finito"),
                            "no_finito": (E.PROBLEMA_TECNICO, "literal_nan_o_infinity"),
                            "no_interpretable": (E.NO_EVALUADO, "sin_numero_para_comprobar_finitud")}[n.clase]
                    yield emitir(regla, (campo,), estado, codigo, parametros=parametros)
            elif rid in ("L0-TMP-001", "L0-TMP-002", "L0-ID-004"):
                campo, esperado = {"L0-TMP-001": ("FECHA", FormatoQA.AAAAMMDD),
                    "L0-TMP-002": ("HORA", FormatoQA.HHMMSS), "L0-ID-004": ("UBIGEO", FormatoQA.SEIS_CARACTERES)}[rid]
                yield formato(regla, campo, esperado)
            elif rid == "L0-TMP-003":
                z = c.zona_documentada
                yield emitir(regla, ("FECHA", "HORA"), E.COMPROBACION_SATISFECHA if z else E.NO_EVALUADO,
                    "zona_documentada_sin_asignarla" if z else "zona_horaria_desconocida",
                    (z.evidencia,) if z else (), (("zona_documentada", z.valor),) if z else ())
            elif rid == "L0-TMP-004":
                yield emitir(regla, ("FECHA", "HORA"), E.NO_EVALUADO,
                    "conversion_de_instantes_fuera_alcance" if c.zona_documentada else "instante_no_determinable_sin_zona")
            elif rid == "L0-ID-001":
                texto = campos.get("ESTACION")
                yield emitir(regla, ("ESTACION",), E.EVALUACION_INCOMPLETA if texto is None else
                    E.COMPROBACION_SATISFECHA if texto.strip() else E.PROBLEMA_TECNICO,
                    "nombre_literal_presente" if texto and texto.strip() else "nombre_estacion_no_disponible")
            elif rid == "L0-ID-002":
                identidades = tuple(i for i in c.identidades if i.nombre_literal == campos.get("ESTACION"))
                ids = {i.identificador_original for i in identidades}
                estado = E.NO_EVALUADO if not ids else E.COMPROBACION_SATISFECHA if len(ids) == 1 else E.ALERTA_DOCUMENTAL
                yield emitir(regla, ("ESTACION",), estado, "identidad_fisica_no_acreditada" if not ids else
                    "identidad_referenciada_sin_verificacion_fisica" if len(ids) == 1 else "identidad_documental_ambigua",
                    tuple(i.evidencia for i in identidades), tuple(("identificador_documentado", i) for i in sorted(ids)))
            elif rid in ("L0-ID-003", "L0-ID-005"):
                nombres = (("LONGITUD", "LATITUD") if rid == "L0-ID-003" else
                    ("RED", "LONGITUD", "LATITUD", "ALTITUD", "DEPARTAMENTO", "PROVINCIA", "DISTRITO", "UBIGEO"))
                valores = tuple(campos.get(n) for n in nombres)
                estado = E.EVALUACION_INCOMPLETA if None in valores else E.PROBLEMA_TECNICO if any(not t.strip() for t in valores) else E.COMPROBACION_SATISFECHA
                yield emitir(regla, nombres, estado, "metadatos_declarados_presentes_sin_validacion_espacial"
                    if estado is E.COMPROBACION_SATISFECHA else "metadatos_incompletos")
            elif rid.startswith("L0-PROV-"):
                p = procedencia
                if rid in ("L0-PROV-001", "L0-PROV-002", "L0-PROV-003", "L0-PROV-004", "L0-PROV-005"):
                    valores = {
                        "L0-PROV-001": (("FUENTE.PROVEEDOR", p.fuente.proveedor if p.fuente else None),
                                        ("FUENTE.ID", p.fuente.identificador if p.fuente else None)),
                        "L0-PROV-002": (("RECURSO_ID", p.recurso_id),),
                        "L0-PROV-003": (("ADQUISICION_ID", p.adquisicion_id),),
                        "L0-PROV-004": (("ASSET_ID", p.asset_id),),
                        "L0-PROV-005": (("SHA256_REFERENCIA", p.sha256_referencia),)}[rid]
                    presente = all(v is not None for _, v in valores)
                    yield emitir(regla, (), E.COMPROBACION_SATISFECHA if presente else E.NO_EVALUADO,
                        "referencia_declarada_presente_sin_verificacion_fisica" if presente else "referencia_desconocida",
                        parametros=(("verificacion_fisica", "no_realizada_por_esta_regla"),), valores=valores)
                elif rid == "L0-PROV-006":
                    estado = E.NO_EVALUADO if p.documento is None else E.COMPROBACION_SATISFECHA if _documento_aplicable(p) else E.PROBLEMA_TECNICO
                    yield emitir(regla, (), estado, "documento_no_disponible" if p.documento is None else
                        "documento_asociado_sin_certificar_observaciones" if _documento_aplicable(p) else "documento_de_otro_recurso")
                elif rid == "L0-PROV-007":
                    aplicable = _documento_aplicable(p)
                    d = p.documento if aplicable else None
                    conocida = d is not None and (d.licencia_declarada is not None or d.referencia_licencia is not None)
                    yield emitir(regla, (), E.COMPROBACION_SATISFECHA if conocida else E.NO_EVALUADO,
                        "licencia_declarada_o_referenciada_sin_analisis" if conocida else "licencia_desconocida_o_documento_no_aplicable",
                        valores=(("LICENCIA", d.licencia_declarada if d else None),
                                 ("REFERENCIA_LICENCIA", d.referencia_licencia if d else None)))
                else:
                    original = registro.procedencia_original
                    coincide = original is not None and (original.fuente, original.recurso_id, original.asset_id,
                        original.sha256_declarado) == (p.fuente, p.recurso_id, p.asset_id, p.sha256_referencia)
                    yield emitir(regla, (), E.NO_EVALUADO if original is None else E.COMPROBACION_SATISFECHA if coincide else E.PROBLEMA_TECNICO,
                        "entrada_sin_procedencia_propia_para_contrastar" if original is None else
                        "referencias_coinciden_sin_verificacion_fisica" if coincide else "procedencias_contradictorias")
