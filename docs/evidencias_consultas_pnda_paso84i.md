# PASO 84-I — Evidencias y consultas PNDA/SENAMHI

Elaboración: **2026-11-08**, para revisión. Complementa la
[reconciliación](reconciliacion_xlsx_docx_pnda_paso84i.md) y la
[matriz nueva de brechas](brechas_reconciliadas_pnda_paso84i.md).
No es una respuesta institucional ni una autorización operativa.

## Identidad y alcance de las referencias

Cada ID de evidencia de las tablas hereda **documento, SHA-256 y ámbito** de su
clave X o D. La columna SHA usa esa clave para evitar repetir 64 caracteres;
no sustituye el hash por un identificador sin correspondencia.

| Clave documental/SHA | Archivo autorizado e identificado | SHA-256 comprobado físicamente |
|---|---|---|
| X | `C:\Users\Propietario\SPICA_EVIDENCIAS_PNDA_84E\diccionario-1851039a07682a3f202314f6f8811fc616cb4ca2a486c9e737fd8cea62a4b4dd.xlsx`, 10815 bytes; ruta tomada de `procedencia.json` | `1851039a07682a3f202314f6f8811fc616cb4ca2a486c9e737fd8cea62a4b4dd` |
| D | `C:\Users\Propietario\SPICA_EVIDENCIAS_PNDA_84F\metadatos-pnda.docx`, 20664 bytes | `7b9dcbd71c4d00798d1795edfd5ba0d15ad0aaab0297a7f0aba91532437a0d18` |

**Fecha/versión de las afirmaciones:** X no contiene edición/fecha editorial
acreditada: **desconocidas**. D tiene los campos visibles «Fecha de creación» y
«Última actualización», ambos `2024-05-30`, y «Versión» `1.0` (D09). Se conservan
como declaraciones de la ficha, sin demostrar vigencia o correspondencia de
ediciones. La fecha de lectura de estas evidencias es 2026-11-08, no 2024-05-30.
En las tablas, **ND-X** y **DECL-D** remiten exactamente a esos alcances.

Todas las referencias X son de la hoja **DiccionarioDatos**, parte
`xl/worksheets/sheet1.xml`. Los intervalos identifican celdas de la tabla, no
rangos meteorológicos ni una conversión de valores de Excel. Una celda vacía
solo acredita ausencia de valor documental en esa celda.

Las referencias D son de **word/document.xml**, namespace
`w = http://schemas.openxmlformats.org/wordprocessingml/2006/main`.
La notación `D:T1/F3/C2/p5/P13` significa tabla 1, fila 3, celda XML 2,
párrafo local 5, párrafo global 13. El local cuenta hermanos `w:p`, incluidos
los vacíos; P es el ordinal canónico del inspector, no página. Su ruta Clark es:

```text
/{http://schemas.openxmlformats.org/wordprocessingml/2006/main}document[1]/{http://schemas.openxmlformats.org/wordprocessingml/2006/main}body[1]/{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tbl[1]/{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tr[3]/{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tc[2]/{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p[5]
```

Las demás referencias cambian los ordinales explícitamente indicados. Archivo D,
SHA completo anterior e ID local `DOCX-PNDA-84I` acompañan cada referencia privada.
No se reconstruyen páginas ni se abren enlaces.

## Evidencias XLSX

Declaraciones leídas con el [diagnóstico seguro 84-E](../herramientas/inspeccionar_xlsx_84e.py)
0.1.0. Las descripciones de esta tabla son **paráfrasis**, salvo literales cortos
entre comillas o en código. No se reproduce el libro completo.

| ID | Doc/SHA | Localización real | Variable/concepto | Declaración o paráfrasis fiel | Fecha/versión | Ámbito | Brechas | Interpretación permitida | Limitación |
|---|---|---|---|---|---|---|---|---|---|
| X01 | X | `X:DiccionarioDatos!B2` | Producto e institución | Título del conjunto de variables meteorológicas de estaciones automáticas de intercambio internacional, con atribución SENAMHI | ND-X | Identificación declarada del dataset | R03, R06 | Correspondencia nominal con D01; B2 termina en espacio | No acredita edición común, autenticidad ni vigencia |
| X02 | X | `X:DiccionarioDatos!A5:D6` | ID / ESTACION | ID identifica un registro; ESTACION contiene el nombre de estación automática | ND-X | Definiciones de campos | S01, S02, S06, T07 | Distinguir registro, nombre e instalación | Sin códigos institucionales ni padrón físico |
| X03 | X | `X:DiccionarioDatos!A9:D10` | LONGITUD / LATITUD | Descripciones en grados, minutos y segundos, respecto de Greenwich y ecuador; ejes X/Y | ND-X | Definición geográfica genérica | S04 | Conservar declaración DMS y ejes | No especifica CRS/datum ni serialización efectiva del CSV |
| X04 | X | `X:DiccionarioDatos!A11:D11` | ALTITUD | Altura respecto al nivel medio del mar, unidad declarada msnm | ND-X | Definición del campo | S05 | Citar unidad y referencia genérica | Sin realización vertical, incertidumbre o época por estación |
| X05 | X | `X:DiccionarioDatos!A15:D15` | RED | Desarrolla GBON y RBON como redes global/regional de observación básica | ND-X | Nombres de redes | S03 | Comparar conceptos con D02 | No identifica miembros ni vigencias |
| X06 | X | `X:DiccionarioDatos!A7:F8` | FECHA / HORA | Fecha/hora de medición; FECHA numérica de tamaño 8 y HORA alfanumérica de tamaño 6; F7 `Formato: aaaammdd`, F8 `Formato: hhmmss` | ND-X | Formatos declarados | T01, T02, T03, T04 | Conservar formatos y límites declarados | No explica cinco posiciones, zona o extremos horarios |
| X07 | X | `X:DiccionarioDatos!A12:D13` | TEMP / HR | Promedios horarios; unidades `°C` y `%`; tipo numérico, tamaño 10 | ND-X | Campos específicos | V01, V02, T04, T05 | Citar promedio y unidades originales | Sin muestreo, ponderación, instrumento o ventana exacta |
| X08 | X | `X:DiccionarioDatos!A14:D14` | PP | «Precipitación total horaria» con unidad literal `milimetros por hora` | ND-X | Campo PP | V03, T04, T05 | Mantener ambas partes de la declaración | No equiparar automáticamente total, acumulación e intensidad |
| X09 | X | `X:DiccionarioDatos!A16:F19` | Divisiones administrativas / UBIGEO | Campos de ubicación; UBIGEO alfanumérico de tamaño 6; E16:E19 mencionan Catálogo del INEI | ND-X | Esquema declarado | S04, S08 | Identificar la especificación documental | Sin edición INEI, reconstrucción o geocodificación autorizada |
| X10 | X | `X:DiccionarioDatos!A20:F20` | FECHA_CORTE | Día de generación del dataset; numérico, tamaño 8, `Formato: aaaammdd` | ND-X | Metadato de generación | T06, R03, R04 | Separar generación de observación y adquisición | No enlaza con las fechas D09 ni con una revisión del CSV |
| X11 | X | `docProps/core.xml`: dcterms:created, dcterms:modified, cp:revision; `docProps/app.xml`: Application, AppVersion | Propiedades técnicas | created `2021-07-05T17:23:13Z`, modified `2024-05-31T20:33:08Z`, revision sin valor; software Excel Online, AppVersion `16.0300` | Técnica; no ND-X editorial | Contenedor OOXML | R04, V08 | Distinguir edición y propiedades editables | No fechan vigencia científica ni prueban sustitución |
| X12 | X | Hoja completa inspeccionada: dimensión declarada A2:F28; 115 celdas XML, 79 con literal, 16 definiciones A5:F20; 0 fórmulas | Alcance de búsqueda y ausencias | No se localizaron especificaciones suficientes de códigos físicos, CRS, zona, instrumentación, centinelas, procesamiento o controles aplicados | ND-X | Literal del libro y propiedades seleccionadas | S01, S02, S04, S06, S07, T03, T07, V04, V05, V06, V07, V08 | Documentar lo no hallado en este corpus acotado | No demuestra inexistencia de documentación institucional |

## Evidencias DOCX

Extraídas con el [inspector seguro](../src/spica/adquisicion/verificacion/docx/inspector.py)
**0.2.1**, `DOCUMENTO_VALIDADO_EN_ALCANCE`. Los resúmenes preservan la distinción
entre afirmación institucional declarada, cotejo local y prueba independiente.

| ID | Doc/SHA | Localización real | Variable/concepto | Declaración o paráfrasis fiel | Fecha/versión | Ámbito | Brechas | Interpretación permitida | Limitación |
|---|---|---|---|---|---|---|---|---|---|
| D01 | D | `D:T1/F1/C2/p1/P5`; campo URL en F2, no consultado | Producto | Mismo título sustantivo que X01; el párrafo directo P3 lo presenta como metadatos del dataset | DECL-D | Ficha del producto | R02, R03, R06 | Coincidencia nominal localizada | No prueba edición común ni identidad de bytes del CSV |
| D02 | D | `D:T1/F3/C2/p2/P10`, `D:T1/F3/C2/p3/P11` | GBON / RBON | Describe GBON como acuerdo de intercambio global y RBON con referencia a lineamientos GBON y asociación regional | DECL-D | Contexto de redes | S03, R03 | Complementa el desarrollo de siglas X05 | No se verificaron documentos OMM citados o membresías |
| D03 | D | `D:T1/F3/C2/p5/P13` | Horariedad y calidad | SENAMHI declara disponer, mediante GBON/RBON, de datos horarios «validados» de temperatura, humedad relativa y precipitación | DECL-D | Afirmación general del dataset | T04, T05, V01, V02, V03, V06, V07 | Registrar que existe esa declaración | No demuestra procedimiento, nivel, flags, ejecución ni calidad de cada registro |
| D04 | D | `D:T1/F3/C2/p7/P15`, `D:T1/F3/C2/p8/P16` | Temperatura / humedad | Definición general de temperatura y relación porcentual del vapor de agua respecto del máximo a temperatura y presión dadas | DECL-D | Conceptos generales | V01, V02 | Información conceptual complementaria a X07 | No define estadístico/instrumento del promedio ni sustituye HR por otra variable |
| D05 | D | `D:T1/F3/C2/p9/P17` | Precipitación | Declara medida en milímetros como altura de lluvia acumulada sobre una superficie | DECL-D | Concepto general de precipitación | V03 | Conservar declaración junto a X08 | No identifica explícitamente código PP, ventana ni equivalencia con unidad por hora |
| D06 | D | `D:T1/F3/C2/p11/P19` | Registro y estación | Cada registro es una medición en una estación meteorológica automática de intercambio internacional | DECL-D | Unidad documental de registro | S01, S02, T07 | Compatible con ID de registro X02 | No suministra código de estación, unicidad temporal o historial físico |
| D07 | D | `D:T1/F3/C2/p13/P21` | Registros vacíos | Indica filtrar registros vacíos para analizar temperatura, humedad relativa y precipitación | DECL-D | Recomendación documental de análisis | V04 | Se documenta una instrucción, sin ejecutarla | No define centinelas, causa ni criterio conjunto/por variable; no autoriza descartar originales |
| D08 | D | `D:T1/F3/C2/p16/P24`, `D:T1/F3/C2/p17/P25` | Estación y campos meteorológicos | Enumera nombre, ubicación, altitud, divisiones, ubigeo y red; fecha, hora y tres variables meteorológicas | DECL-D | Descripción de campos del dataset | S01, S03, S04, S05, S08, T01, T02, R03 | Coincidencia conceptual con parte de los 16 campos X | No es diccionario de 16 filas; no enumera ID ni FECHA_CORTE ni define sus formatos |
| D09 | D | `D:T1/F7/C2/p1/P34`, `D:T1/F9/C2/p1/P38`, `D:T1/F10/C2/p1/P40` | Fechas / versión | Fecha de creación y última actualización `2024-05-30`; versión literal `1.0` | DECL-D | Campos de la ficha de metadatos | R04, R03, T06, V08 | Evidencia visible, distinta de propiedades OOXML | Sin manifiesto de recursos, vigencia por período ni equivalencia con edición XLSX/CSV |
| D10 | D | `D:T1/F4/C2/p1/P28`, `D:T1/F5/C2/p1/P30` | Entidad / fuente | Entidad SENAMHI; fuente «Subdirección de Gestión de Datos - Dirección de Red de Observación y Datos» | DECL-D | Atribución institucional explícita | R06 | Conservar la denominación literal declarada | No autentica independientemente emisor/custodio ni vigencia organizativa |
| D11 | D | `D:T1/F8/C2/p1/P36` | Actualización | Frecuencia declarada `Mensual` | DECL-D | Actualización del dataset | T05, R04 | Distinguir publicación/actualización de observación horaria | No prueba cumplimiento mensual efectivo ni cadencia de sensor |
| D12 | D | `D:T1/F11/C2/p1/P42`, `D:T1/F13/C2/p1/P46` | Licencia / acceso | `Open Data Commons Attribution License`; acceso `Público` | DECL-D | Condiciones nombradas en la ficha | R05 | Licencia y acceso declarados localizados | Destino no abierto; texto, edición, atribución y alcance a recursos/revisiones no verificados; sin autorización jurídica de redistribución |
| D13 | D | `D:T1/F14/C2/p1/P48`, `D:T1/F15/C2/p1/P50` | Recurso / formato | `Dataset` / `CSV` | DECL-D | Recurso descrito por los metadatos | R03 | Describe el recurso meteorológico | No cambia el formato físico DOCX ni demuestra vínculo al CSV operativo |
| D14 | D | `D:T1/F16/C2/p1/P52` | Cobertura | `Perú, 2015 - 2024` | DECL-D | Cobertura declarada del producto | S06, R03, V08 | Cobertura anual general | Sin extremos diarios, lista de estaciones, operación o vigencia de definiciones |
| D15 | D | `docProps/core.xml`: dcterms:created, dcterms:modified, cp:revision; `docProps/app.xml`: Application, AppVersion | Propiedades técnicas | created `2021-10-20T17:24:00Z`, modified `2024-06-01T03:56:00Z`, revision `19`, AppVersion `16.0000` | Técnica; separada de DECL-D | Contenedor OOXML | R04, V08 | Distinguir propiedades editables y campos visibles D09 | No convertir 19 en edición institucional ni en vigencia |
| D16 | D | Bloques revisados: tabla 1, filas 1–16, más párrafos directos P1/P2/P3/P55 y cinco propiedades técnicas seleccionadas | Alcance y ausencias | Sin catálogo/códigos físicos, CRS/datum, zona/HORA detallada, historial instrumental, centinelas o procedimiento QC localizado en esos bloques | DECL-D | 53 párrafos incluidos vacíos; dos de contacto omitidos de la revisión pública | S01, S02, S04, S05, S06, S07, T02, T03, T04, T07, V04, V05, V06, V07, V08 | Ausencia localizada en el corpus revisado | No cubre destinos externos, contacto privado, formato no renderizado ni documentación institucional no inspeccionada |

## Antecedente CSV y naturaleza de las comparaciones

**H01** es evidencia histórica, **no una lectura del CSV en 84-I**. Remite al
[84-D](auditoria_metadatos_pnda_paso84d.md), al
[recorrido CSV](csv_streaming.md) y al [perfilado](perfilado_meteorologico.md).
El original histórico se identifica allí por SHA-256
`3d3e8a0a75e070d0b8111faf921be17140c3a0f9db2b4c25d72d99a15a950eab`.
Sus conteos previos: HORA de cinco/seis posiciones y UBIGEO con `.0`/longitudes
7–8, frente a X06/X09. Se conservan ambas evidencias para S08/T02; no se afirma
haber revalidado hoy filas o causas. La cobertura civil histórica 2015-01-01 a
2024-06-30 es compatible con el intervalo anual D14, sin demostrar misma edición.

Los dos auxiliares son documentos distintos atribuidos a la misma institución:
coincidir entre ellos no crea dos verificaciones científicas independientes.
Integridad local, contenido, atribución, autenticidad, vigencia, aplicabilidad y
aprobación permanecen dimensiones distintas.

## Consultas que siguen siendo necesarias

Se conservan el [borrador histórico](solicitud_tecnica_senamhi_borrador.md), las
[consultas agrupadas 84-D](reconciliacion_evidencias_pnda_paso84d.md) y la
[precisión 84-E](brechas_diccionario_pnda_paso84e.md).
No se envió comunicación ni se abrió ninguna referencia web.

| Consulta | Prioridad | Pregunta ajustada a la evidencia actual | Evidencia de partida / brechas | Respuesta o documento necesario |
|---|---|---|---|---|
| Q1. Ediciones y vigencia | P1 | ¿Qué originales CSV/XLSX corresponden a la ficha que declara 1.0 y 2024-05-30? ¿Qué significa cada fecha, qué cambios/sustituciones y cobertura por revisión existen? | X01, X10, X11, D01, D09, D13–D15; R03, R04, T06, V08 | Manifiesto o aclaración institucional con identidades de recursos/ediciones, alcance y desconocidos expresos |
| Q2. Estaciones y redes | P1 | ¿Qué códigos y espacios de nombres corresponden a ESTACION y a instalaciones físicas? ¿Cómo se documentan membresía GBON/RBON, homónimos, traslados y épocas? | X02, X05, D02, D06, D08, D14; S01–S03, S06 | Catálogo e historial aplicables, sin inferir códigos desde ID o nombres |
| Q3. Espacio y metrología | P1 | ¿Qué CRS/datum, ejes y serialización corresponden a coordenadas descritas en DMS? ¿Qué realización vertical y calidad tiene msnm? ¿Qué instrumentos/calibraciones y edición/serialización INEI aplican? | X03, X04, X09, D08, H01; S04–S08, V05 | Fichas por estación/instrumento/época y explicación de representaciones |
| Q4. Convención temporal | P1 | ¿Cómo se interpretan HORA de cinco/seis posiciones, zona y cambios de reloj? ¿Qué etiqueta/extremos/ventana y cadencias corresponden a cada etapa? ¿Cómo se relaciona generación FECHA_CORTE con actualización mensual, publicación y revisiones? | X06, X10, D03, D09, D11, H01; T01–T07 | Especificación y casos documentados por variable, edición y período |
| Q5. Variables y ausentes | P1 | ¿Cuál es el método de los promedios TEMP/HR? ¿Qué representa PP y cómo se relacionan la unidad por hora X08 y los milímetros D05? ¿Qué vacíos/centinelas, ventanas parciales y reinicios existen, y qué criterio significa filtrar registros vacíos? | X07, X08, D04, D05, D07; V01–V05, T04, T05 | Definiciones aplicables y política de agregación/ausentes, sin conversiones presumidas |
| Q6. Validación y procesamiento | P1 | ¿Qué significa «validados» en D03 para esta edición? ¿Qué etapas, procedimientos, controles y flags se ejecutaron, cómo se vinculan a registros y qué alcance del manual MT-DRD-002 corresponde? | D03, X12, D16; V06–V08, R04 | Procedimiento/versión y evidencia de aplicación; no basta repetir el adjetivo |
| Q7. Procedencia y derechos | P1 antes de redistribuir | ¿Se confirma la fuente/unidad indicada en D10 para esta edición? ¿Qué texto y edición de la licencia nombrada en D12 cubre CSV, XLSX y DOCX, con qué atribución y alcance de uso/redistribución? | X01, D10, D12; R05, R06 | Emisor/custodio verificable y condiciones aplicables para revisión, sin presuponer permiso |

Se retira como necesidad pendiente **obtener una primera copia local del DOCX**:
esa tarea está cumplida (R02). También están contestadas, a nivel de declaración,
las preguntas sobre nombre de licencia, fuente, actualización, versión y fechas
visibles. No se vuelve a pedir su mera existencia; se pide su alcance verificable.

## Seguimiento pendiente de revisión

Destinatario propuesto: **SENAMHI, unidad custodio del producto por confirmar**;
la unidad de D10 es declarada, no un destinatario autorizado por SPICA.
Fecha de elaboración: **2026-11-08**. Fecha de envío, canal, referencia de trámite,
solicitante autorizado y revisor: **pendientes**. Estado: **NO ENVIADA**.
Respuestas y evidencias institucionales recibidas en este paso: **ninguna**.

Una futura recepción deberá registrar: consulta Q, emisor y referencia original,
fecha de recepción, archivo/hash físico, apartado/celda, literal o paráfrasis,
edición/fecha y ámbito declarados, brechas afectadas, contradicciones conservadas
y decisión humana motivada. No se rellenan respuestas ficticias ni se autoriza
automáticamente descargar, persistir metadatos o activar QA/QC.
