# PASO 85-A — Inventario y auditoría QA/QC Nivel 0

Fecha: **2026-11-08**. Dictamen: **APTO CON RESTRICCIONES** para el
[piloto estructural sintético](piloto_qaqc_estructural_paso85a.md).
No habilita niveles superiores, procesamiento institucional ni una etapa nueva.

## Recuperación e inventario previo a cambios

Git inicial limpio, rama **feature/suadc-http**, HEAD **496976d**, «SUADC:
vinculacion verificable de evidencia documental». El PASO 84-L está registrado.
Historial comprobado:

```text
496976d SUADC: vinculacion verificable de evidencia documental
f6c2a36 SUADC: auditoria de procedencia y piloto documental PNDA
1c06125 SUADC: contratos experimentales de metadatos documentales
ef17ad4 SUADC: reconciliacion documental de metadatos PNDA
b3c2748 SUADC: compatibilidad OOXML y extraccion documental PNDA
```

Antes de editar se revisaron el [diseño Nivel 0 del PASO 72](calidad_nivel0.md),
la [auditoría de cardinalidad del PASO 73](catalogo_reglas_cientificas.md),
[modelos](../src/spica/calidad/modelos.py),
[reglas](../src/spica/calidad/reglas.py),
[motor](../src/spica/calidad/motor.py) y
[53 pruebas anteriores](../tests/test_calidad_nivel0.py), junto con
[interpretación compartida](../src/spica/perfilado/interpretacion.py), procedencia,
interoperabilidad, [84-C](integracion_local_pnda_paso84c.md) y
[84-L](vinculacion_evidencia_paso84l.md).

**Las 22 reglas sí existen en código**, en REGLAS_NIVEL0 y en las ramas de
evaluar_registro; no son únicamente títulos documentados. El registro cerrado
contiene 1 EST, 4 VAL, 4 TMP, 5 ID y 8 PROV. Todas conservan identificadores
originales y versión **1.0.0**, contrato QA **1.0.0**.

Clasificación del inventario:

- **A:** implementada y probada en su alcance limitado, no certificada científicamente.
- **B:** implementación parcial; **C:** diseño sin programa. No se identifican B/C
  entre estas 22 definiciones; no significa cobertura exhaustiva de todo dato posible.
- **D:** falta evidencia para una evaluación concreta; **E:** fuera del subconjunto
  del piloto. D/E describen aplicabilidad de una ejecución, no inexistencia del código.

Una regla A puede devolver NO_EVALUADO por diseño. En particular TMP-004 es
una barrera explícita: identifica que no se determinará un instante; no es un
conversor temporal implementado a medias. La detección semántica de duplicados,
esquemas ambientales generales y unidades científicas no son reglas de este registro.

## Las 22 reglas: entradas, metadatos y condiciones

Abreviaturas de resultados: **S** COMPROBACION_SATISFECHA, **A** ALERTA_DOCUMENTAL,
**P** PROBLEMA_TECNICO, **N** NO_EVALUADO, **I** EVALUACION_INCOMPLETA.
No son categorías de calidad meteorológica. Para toda regla, una fila con
estructura recibida incoherente produce I/estructura_no_evaluable, sin resultados
satisfechos; cada VAL conserva ahora su objetivo particular TEMP/HR/PP.

| ID original | Descripción y objetivo limitado | Entrada requerida | Metadatos requeridos | Condición de evaluación y diagnóstico esperado |
|---|---|---|---|---|
| L0-EST-001 | Coherencia del registro recibido; reconocer el estado estructural aportado por el adaptador | RegistroQA y estructura_correcta | Perfil tabular del adaptador/lector; no esquema inferido | True: S/estructura_recibida_coherente; False: I. No valida por sí sola un esquema arbitrario ni todos sus campos obligatorios |
| L0-VAL-001 | Presencia literal por variable; separar vacío de dato no aportado | Campo seleccionado TEMP/HR/PP como texto | Selección de variables del contrato | Ausente: I/campo_no_disponible; cadena vacía exacta: P/campo_vacio_sin_inferir_medicion; resto: S/valor_literal_presente |
| L0-VAL-002 | Representación numérica finita interpretable | Texto de cada variable | Politica numérica compartida, versión/límites | Finito: S/numero_finito_interpretable; no interpretable: P/numero_no_interpretable; vacío o no finito: N; presupuesto excedido: I |
| L0-VAL-003 | Detección explícita de NaN/Infinity y otros no finitos reconocidos | Texto de cada variable | Misma gramática/presupuesto | Finito: S/numero_finito; no finito: P/literal_nan_o_infinity; texto o vacío: N; límite: I |
| L0-VAL-004 | Comparación con formato numérico documental explícito | Texto de cada variable | FormatoDocumentadoQA NUMERO_ASCII y ReferenciaDocumentalQA | Sin formato: N; finito conforme: S; discrepancia: A; vacío: N; campo ausente o límite: I |
| L0-TMP-001 | Fecha civil documental, representación y calendario | FECHA textual | Formato AAAAMMDD con referencia explícita | Fecha civil válida: S; ocho dígitos con calendario imposible: P/fecha_civil_invalida; otro formato: A; sin documento/vacío: N; ausente: I |
| L0-TMP-002 | Formato HORA hhmmss y rangos léxicos | HORA textual | Formato HHMMSS explícito y referencia | Literal de seis dígitos en rango: S; diferente o fuera de rango: A; sin formato acreditado para la comparación: N; ausente: I |
| L0-TMP-003 | Disponibilidad de una referencia de zona | FECHA/HORA para traza; configuración de zona | DatoDocumentadoQA opcional | Si se aportó: S/zona_documentada_sin_asignarla; si no: N/zona_horaria_desconocida |
| L0-TMP-004 | Incertidumbre del instante absoluto; mantener barrera de alcance | FECHA/HORA y disponibilidad documental de zona | Zona puede ser desconocida | Siempre N: instante_no_determinable_sin_zona o conversion_de_instantes_fuera_alcance. No produce datetime |
| L0-ID-001 | Nombre literal de estación presente | ESTACION | Ningún catálogo inferido | Ausente: I; vacío/solo espacios: P; otro texto: S/nombre_literal_presente, sin modificarlo |
| L0-ID-002 | Correspondencia literal con identidades documentadas, o ambigüedad | ESTACION y mappings IdentidadEstacionQA | Nombre literal, identificador y referencia documental aportados | Sin correspondencia: N/identidad_fisica_no_acreditada; un ID: S/identidad_referenciada_sin_verificacion_fisica; varios: A/identidad_documental_ambigua |
| L0-ID-003 | Coordenadas declaradas disponibles | LONGITUD y LATITUD como textos | No requiere CRS para comprobar solo presencia | Falta campo: I; texto vacío/solo espacios: P; textos presentes: S/metadatos_declarados_presentes_sin_validacion_espacial |
| L0-ID-004 | Representación documental de UBIGEO, solo anchura | UBIGEO textual | Formato SEIS_CARACTERES y referencia | Longitud seis: S; discrepancia: A; sin formato/vacío: N; ausente: I. No exige dígitos ni valida un catálogo territorial |
| L0-ID-005 | Presencia de ocho campos de ubicación declarada | RED, LONGITUD, LATITUD, ALTITUD, DEPARTAMENTO, PROVINCIA, DISTRITO, UBIGEO | Perfil de campos del contrato | Falta campo: I; alguno vacío/solo espacios: P; todos presentes: S, sin validación espacial |
| L0-PROV-001 | Referencia a institución/fuente, no autenticación | ProcedenciaQA.fuente, proveedor e identificador | Fuente opcional del núcleo | Presente: S/referencia_declarada_presente_sin_verificacion_fisica; desconocida: N/referencia_desconocida |
| L0-PROV-002 | Identidad declarada del recurso | recurso_id | ProcedenciaQA | Presente: S con aviso sin verificación física; desconocida: N |
| L0-PROV-003 | Identificador de adquisición | adquisicion_id | ProcedenciaQA | Presente: S con el mismo alcance; desconocido: N |
| L0-PROV-004 | Referencia de activo RAW | asset_id | ProcedenciaQA | Presente: S solo por referencia; desconocido: N. No abre RAW |
| L0-PROV-005 | SHA-256 de referencia disponible | sha256_referencia | ProcedenciaQA valida la sintaxis del SHA | Presente: S solo por referencia; desconocido: N. No calcula hash del archivo |
| L0-PROV-006 | Documento asociado a fuente/recurso | documento de catálogo y contexto de procedencia | EvidenciaDocumental existente, no el tipo homónimo de aplicabilidad | Ausente: N; fuente/recurso coinciden: S/documento_asociado_sin_certificar_observaciones; otro recurso: P/documento_de_otro_recurso |
| L0-PROV-007 | Licencia declarada o referenciada disponible | documento aplicable, licencia_declarada/referencia_licencia | Asociación de fuente/recurso de PROV-006 | Mención o referencia: S/licencia_declarada_o_referenciada_sin_analisis; desconocida/no aplicable: N. No concede derechos |
| L0-PROV-008 | Coherencia con procedencia propia de la entrada | registro.procedencia_original y contexto QA | ProcedenciaLocal opcional con fuente/recurso/asset/SHA | Sin procedencia propia: N; referencias iguales: S/referencias_coinciden_sin_verificacion_fisica; diferentes: P/procedencias_contradictorias |

## Implementación, pruebas, dependencias y ejecución offline

Los tests citados pertenecen a CalidadNivel0Tests en
[test_calidad_nivel0.py](../tests/test_calidad_nivel0.py). Cada celda indica
el nombre después de `test_`. El ensayo de registro/versiones ejecuta las 22;
el test de cardinalidad de
[test_reglas_cientificas.py](../tests/test_reglas_cientificas.py) contrasta también
22.320 claves sintéticas de 744 filas. No es una nueva lectura del piloto histórico.

Dependencias: **Q** modelos/selección/emitir de calidad; **N** interpretar_numero
compartido del perfilador; **F** formato documental cerrado; **C** calendario civil;
**H** clasificar_hora_literal; **D** asociación de EvidenciaDocumental; **L**
ProcedenciaLocal para contraste. Todas se pueden evaluar offline. No se ejecuta
el perfilador agregado, un índice de observaciones o un módulo científico.

| ID | Código y pruebas | Test representativo existente | Dependencia adicional | Restricción científica | Disponibilidad en este piloto, siempre offline |
|---|---|---|---|---|---|
| L0-EST-001 | A | registro_cerrado_ids_versiones_y_contrato; estructura_incompleta_conserva_valores_y_no_aplica_reglas_como_satisfechas | Q; adaptar_registro/lector en flujo | Estructura recibida no es validez del fenómeno | Seleccionada; S06 I |
| L0-VAL-001 | A | vacio_y_presente_no_infiere_medicion_ausente; funcion_pura_y_campos_ausentes | Q | Un vacío no acredita medición ausente o su causa | Seleccionada; S02 I, S03 P |
| L0-VAL-002 | A | numeros_interpretables_y_texto_invalido; extremos_y_marcadores_numericos_se_conservan | Q/N | No verifica unidades, rangos normales o centinelas | Seleccionada; S04 S, S05 P, S10 S lexical |
| L0-VAL-003 | A | nan_e_infinity_son_regla_especifica | Q/N | No es control instrumental o plausibilidad | E: no seleccionada en los 12 escenarios; sí en regresiones |
| L0-VAL-004 | A | sin_formato_documental_no_se_infiere_regla; nan_e_infinity_son_regla_especifica | Q/N/F | Formato aportado no prueba autenticidad/aplicabilidad científica | Seleccionada con referencia ficticia; S11 D/N |
| L0-TMP-001 | A | fechas_calendario_validas_e_invalidas | Q/F/C | Fecha civil no es instante ni ventana | E; evidencia real aplicable no evaluada |
| L0-TMP-002 | A | hora_cinco_seis_y_rangos_sin_reconstruccion | Q/F/H | No corrige ceros, asigna zona o crea timestamp | Seleccionada; D/N sin formato HORA en fixtures |
| L0-TMP-003 | A | zona_desconocida_no_asigna_instante; zona_documentada_no_convierte_a_datetime | Q | Presencia documental no equivale a localización | E; no se aporta zona |
| L0-TMP-004 | A, barrera | zona_documentada_no_convierte_a_datetime | Q | Conversión de instantes no implementada/permitida aquí | E; se mantiene barrera anterior |
| L0-ID-001 | A | nombre_literal_presente_o_vacio_sin_normalizar | Q | Nombre no identifica estación física | E |
| L0-ID-002 | A | identidad_requiere_nombre_literal_y_evidencia; identidad_documental_contradictoria_no_se_resuelve | Q | Mapping es referencia suministrada, no verificación de instalación | Seleccionada; D/N por defecto y A en S07 |
| L0-ID-003 | A | coordenadas_presentes_no_se_validan_geodesicamente | Q | No interpreta coordenadas ni supone CRS | E; fixtures sin coordenadas aportadas |
| L0-ID-004 | A | ubigeo_decimal_no_se_reconstruye; ubigeo_seis_caracteres_no_impone_digitos_no_documentados | Q/F | Anchura no acredita catálogo, territorio o geocodificación | Seleccionada con contrato ficticio; A en S09 |
| L0-ID-005 | A | coordenadas_ausentes_y_metadatos_incompletos | Q | Presencia no acredita exactitud o referencia vertical | E |
| L0-PROV-001 | A | procedencia_incompleta_se_conserva_desconocida; registro_cerrado_ids_versiones_y_contrato | Q | No autentica institución | E; procedencia desconocida en el piloto puro |
| L0-PROV-002 | A | procedencia_incompleta_se_conserva_desconocida; registro_cerrado_ids_versiones_y_contrato | Q | Recurso declarado no verifica identidad física | E |
| L0-PROV-003 | A | procedencia_incompleta_se_conserva_desconocida; registro_cerrado_ids_versiones_y_contrato | Q | No confirma adquisición real | E |
| L0-PROV-004 | A | sha_y_asset_solo_referencias_no_confirmacion_raw | Q | No confirma RAW ni persistencia | E |
| L0-PROV-005 | A | sha_y_asset_solo_referencias_no_confirmacion_raw | Q | SHA declarado no es SHA físico comprobado | E |
| L0-PROV-006 | A | documento_disponible_y_licencia_desconocida; documento_ajeno_no_valida_licencia | Q/D | Asociación no verifica emisor, estado declarado o contenido | E en escenarios; contraste sintético adicional de tres estados |
| L0-PROV-007 | A | licencia_referenciada_sin_afirmar_permisos | Q/D | Mención no permite redistribución | E |
| L0-PROV-008 | A | consultas_locales_reutilizadas_y_procedencia_conservada; procedencia_contradictoria_no_se_oculta | Q/L | Coherencia de referencias no verifica originales | E; no ObservacionLocal real |

Se seleccionan **siete definiciones existentes** para el piloto, no siete reglas
nuevas. Las otras quince quedan fuera de ese subconjunto; sus regresiones sí se
ejecutan. Las 22 implementaciones conservan su alcance técnico/documental.
Las pruebas no equivalen a aprobación científica o cobertura de todas las ramas.

## Arquitectura y estados: alcance efectivo

evaluar_registro es un generador puro. EvaluadorNivel0 compone LectorCSV o
ConsultorLocalCSV, controla límites/cancelación y conserva el informe de cierre.
No se crea un segundo motor, validador de unidades o parser. El adaptador y
el encabezado están especializados en las 16 columnas del perfil SENAMHI;
ConfiguracionQA solo admite TEMP/HR/PP. No es todavía un motor genérico para
hidrología, suelos o datos GIS. Tampoco valida un diccionario de tipos de Python
arbitrario: RegistroQA exige valores textuales y los formatos permitidos son cerrados.

| Petición de nomenclatura | Contrato reutilizado y cautela |
|---|---|
| CUMPLE | COMPROBACION_SATISFECHA, solo la condición concreta |
| INCUMPLE | PROBLEMA_TECNICO para un problema técnico probado; ALERTA_DOCUMENTAL para discrepancia representacional o ambigüedad. No deben fusionarse como error científico |
| NO_EVALUABLE | NO_EVALUADO por falta de evidencia/alcance, o EVALUACION_INCOMPLETA si faltó entrada/presupuesto o hubo estructura incoherente; el código explica la causa |
| NO_APLICA | No hay un enum separado; los códigos de fuera de alcance usan NO_EVALUADO. No confundir información ausente con inaplicabilidad demostrada |

ResultadoQA identifica regla/versión, RegistroQA con posición/líneas y originales,
ProcedenciaQA, valores afectados, referencias, parámetros, estado y diagnóstico.
estado_evaluacion distingue completa/incompleta/no evaluada. Configuración y
límites completos se conservan en InformeQA o en el expediente del ensayo puro.

**Limitaciones de contrato auditadas:** ResultadoQA no tiene un campo general
de restricciones o de autorización científica. ReferenciaDocumentalQA no codifica
por sí sola autenticidad, nivel de confianza o aplicabilidad editorial. El estado
de EvidenciaDocumental, si existe, se conserva en procedencia; PROV-006 solo
contrasta asociación de fuente/recurso, independientemente de ese estado.
Las restricciones globales del piloto se documentan en el expediente/fixture;
no se inventa un atributo como si ya existiera en el modelo. No se construye un
puente automático desde el cotejador 84-L a estos formatos o estados.

En la función pura, estructura_correcta es información del adaptador/llamador,
no una prueba física. Un campo ausente en una entrada parcial se informa I,
sin afirmar que haya sido omitido en un original no inspeccionado. El motor de
archivo sí rechaza un encabezado diferente y conserva la tupla CSV bruta cuando
la cantidad de campos es incorrecta. Un motivo eof puede coexistir con informe
INCOMPLETA: alcanzar EOF no certifica estructura o evaluación completas.

## Hallazgo corregido: objetivos indistinguibles en filas incoherentes

**85A-01, gravedad media, corregido.** Antes del cambio, una fila sintética de
17 campos recibida por adaptar_registro quedaba marcada estructura_correcta=False.
Ejecutar solo L0-VAL-002 con TEMP/HR/PP producía **tres resultados exactamente
iguales**: misma regla, fila, lista de todos los campos y diagnóstico I. Había
tres emisiones pero una sola traza distinta; no se conservaba qué variable se
había intentado evaluar.

La corrección mínima en reglas.py mantiene `(campo,)` como objetivo de cada VAL
incompleta; las otras reglas conservan el contexto de fila. El RegistroQA y su
valores_csv_originales siguen conservando todo, incluido el campo adicional.
No cambia estados, diagnósticos, número de emisiones, condiciones científicas,
gramática o formatos, ni modifica valores originales. Solo corrige la atribución
del resultado que no se pudo evaluar.

Las versiones de regla/contrato siguen **1.0.0**, porque no se cambian condiciones
de evaluación; la corrección de traza queda identificada por el diff y la huella
de código registrada en el piloto. No se declara una nueva regla ni se reescribe
el informe histórico. Una política futura de versiones para correcciones de
trazabilidad debe acordarse antes de persistir resultados comparables por versión.

El test nuevo confirma 169 claves únicas del piloto e individualiza TEMP/HR/PP
también en S06. La corrección no permite llamar completa a una fila malformada.
No se identificó necesidad de modificar contratos públicos o implementar reglas
de Nivel 1. Los demás límites son explícitos, no funciones terminadas por este paso.

## Cardinalidad, duplicaciones y muestra PNDA

Con las 22 reglas y tres variables: **18 + 4×3 = 30 resultados por fila**.
El antecedente de 744 filas explica **22320 resultados**, no 22320 observaciones
independientes. Son cifras históricas, no un nuevo piloto institucional.
Con las siete seleccionadas aquí: **4 + 3×3 = 13 por entrada**; 13 entradas
en 12 escenarios producen **169**, incluso con resultados no evaluados o incompletos.

No hay una regla de duplicación de observaciones entre las 22. El motor exige
números de registro crecientes y conserva filas con ID o contenido repetidos;
el número lógico no es una clave de identidad meteorológica. Existe además
diagnosticar_csv en consultas_locales, fuera de QA, que cuenta claves literales
ESTACION/FECHA/HORA con índice SQLite temporal; no prueba instantes duplicados.
No se invoca ni se copia ese diagnóstico en este piloto puro. S12 compara solo
la igualdad exacta de la tupla de valores de una fixture y conserva ambas filas;
no inventa una clave de estación o ventana horaria científica.

El [84-C](integracion_local_pnda_paso84c.md) documenta dos filas originales y seis
descripciones TEMP/HR/PP en memoria. Sus artefactos temporales resultado_real.json
y auditoría se describen expresamente sin volcado de mediciones ni copia CSV.
El arnés ejecutar requiere abrir RAW/SQLite y leer el CSV autorizado de entonces;
**no se invocó ahora**. No se identifica una muestra independiente con valores
y ubicación autorizada para 85-A. Esto no afirma inexistencia en todo el equipo:
no se buscaron carpetas ajenas ni se abrieron sus temporales antiguos. Se usaron
solo fixtures nuevas, sin CANDARAVE ni mediciones institucionales como datos.

## Riesgos y recomendación para revisión

- El perfil de columnas y variables es específico; no declarar interoperabilidad
  multidisciplinaria universal ni soporte de reglas aún no diseñadas.
- Formatos/identidades/documentos son aportados, no autenticados por Nivel 0.
  La coexistencia de texto cotejado y restricciones no se reduce a un booleano.
- Las restricciones genéricas y procedencia por ejecución requieren un diseño
  futuro de vinculación explícita, sin ampliar ahora modelos estables.
- Espacios, no finitos, límites y representación discrepante tienen significados
  distintos. Una observación extrema no se rechaza por ser extrema.
- Los estados completos del recorrido no certifican ciencia ni ausencia de defectos;
  frozen no protege contra Python hostil y no hay aislamiento frente a escritores.

Para un eventual **85-B**, sujeto a auditoría: acordar el perfil de entrada y
metadatos aplicables, criterios de versionado de correcciones de traza, registro
de restricciones por ejecución y clave literal de duplicación si se requiere.
Mantener separadas la evidencia física, declaración, aplicabilidad y ejecución.
No activar umbrales, zonas, geocodificación, conversiones PP o QA/QC científico.

Las verificaciones y el estado final se detallan en el
[informe del piloto](piloto_qaqc_estructural_paso85a.md). Permanecen exactamente
**29 brechas: 2 resueltas documentalmente, 17 parciales, 8 pendientes,
2 contradicciones, 0 no evaluables; 27 abiertas**. No se modifica ninguna matriz.
