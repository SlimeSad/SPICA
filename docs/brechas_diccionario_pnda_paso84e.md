# PASO 84-E: actualización trazable de las 29 brechas PNDA/SENAMHI

Fecha: **2026-11-05**. Propuesta para revisión, basada en la lectura local del
diccionario. Acompaña al [informe e inventario](inspeccion_diccionario_pnda_paso84e.md).
No sobrescribe la [matriz del 84-D](brechas_metadatos_pnda_paso84d.md).

**X84E**: XLSX de **10815 bytes**, SHA-256
`1851039a07682a3f202314f6f8811fc616cb4ca2a486c9e737fd8cea62a4b4dd`.
Todas las celdas de esta matriz corresponden a la única hoja **DiccionarioDatos**,
salvo propiedades OOXML expresamente indicadas. Origen, copia independiente,
manifiesto, tiempos, controles y límites se documentan en el informe. La evidencia
nueva acredita lectura/integridad local, **no autenticidad, vigencia o aplicación
automática al CSV**. No se volvió a leer el CSV ni se examinó el DOCX.

La columna anterior reproduce literalmente el estado de verificación del 84-D.
Las cinco etiquetas nuevas describen exclusivamente este expediente:
`RESUELTA_CON_EVIDENCIA`, `PARCIALMENTE_DOCUMENTADA`, `PENDIENTE_DE_EVIDENCIA`,
`CONTRADICCIÓN_DOCUMENTADA`, `NO_EVALUABLE`. No son estados nuevos del catálogo,
del evaluador ni del motor QA/QC. Una lectura nueva puede precisar una declaración
sin satisfacer toda la condición objetiva de cierre del 84-D.
Las ausencias se refieren al documento completo inspeccionado, no a SENAMHI.

## 1. Recursos, procedencia y derechos

| ID | Estado anterior (84-D) | Evidencia nueva | Estado propuesto | Justificación | Limitaciones restantes | Impacto sobre interoperabilidad | Consulta institucional |
|---|---|---|---|---|---|---|---|
| R01 | Integridad local comprobada; contenido según E-69/E-74 | X84E conservado en carpeta privada persistente, con copia exclusiva, manifiesto y localizaciones A2:F20 comprobadas | RESUELTA_CON_EVIDENCIA | Cumple conservación de la copia de referencia y localización del contenido del XLSX | Cierre técnico circunscrito al diccionario; no incluye DOCX, backup general, autenticidad ni cotejo editorial | Permite referencias reproducibles al documento identificado; no cambia aptitud | No para conservar este XLSX; sí para su edición/aplicabilidad (R03/R04) |
| R02 | Contenido y disponibilidad local DESCONOCIDOS | Ninguna lectura del DOCX autorizada o realizada; sigue solo la referencia histórica | NO_EVALUABLE | Sin copia acreditada no se evalúa su contenido | No prueba ausencia institucional, inaccesibilidad remota o que contenga lo requerido | No aporta metadatos ausentes del XLSX | Sí: copia/edición aplicable o aclaración de disponibilidad |
| R03 | Relación documental DECLARADA; equivalencia de ediciones DESCONOCIDA | B2 identifica el dataset; A5:A20 documenta los 16 campos; sin manifiesto de ediciones/hashes | PARCIALMENTE_DOCUMENTADA | Se reafirma correspondencia nominal/esquemática, no equivalencia entre revisiones | DOCX no inspeccionado; compartir título/campos no vincula cada original | Definiciones citables con reserva de alcance; sin sustituciones retroactivas | Sí: correspondencia CSV–XLSX–DOCX por edición/período |
| R04 | Vigencia DESCONOCIDA | `docProps/core.xml`: created 2021-07-05, modified 2024-05-31; revision sin valor. AppVersion 16.0300 es software | PENDIENTE_DE_EVIDENCIA | Fechas internas editables no acreditan vigencia o edición científica | Sin fecha/versión editorial explícita e historial aplicable | No selecciona definición vigente automáticamente | Sí: edición, vigencia e historial; se aceptará desconocido explícito con alcance |
| R05 | Referencia DECLARADA; términos/alcance no verificados aquí | No se encuentra texto o versión de licencia en X84E; enlace histórico se conserva sin abrir | PENDIENTE_DE_EVIDENCIA | El diccionario no añade términos aplicables | No se auditó web ni licencia del producto; no es una conclusión jurídica | No autoriza redistribución ni cambia condiciones históricas | Sí: términos, edición, atribución y recursos cubiertos |
| R06 | Atribución documental DECLARADA; autenticidad independiente no acreditada | B2 atribuye el dataset a SENAMHI; copia/hash/inspección trazables | PARCIALMENTE_DOCUMENTADA | Se localiza atribución y procedencia técnica de esta copia | Título/propiedades/hash no autentican autor o emisor | Conserva procedencia declarada; no promoción a autenticidad verificada | Sí: custodio, emisor y referencias verificables |

## 2. Estaciones, instrumentos y espacio

| ID | Estado anterior (84-D) | Evidencia nueva | Estado propuesto | Justificación | Limitaciones restantes | Impacto sobre interoperabilidad | Consulta institucional |
|---|---|---|---|---|---|---|---|
| S01 | Nombre DECLARADO; código institucional DESCONOCIDO | B5: ID único de registro; B6: nombre de estación; C6 texto | PARCIALMENTE_DOCUMENTADA | Se distingue registro de nombre de estación | No hay códigos/padrón/espacio de nombres/correspondencias | No crear identidad física a partir de ID o ESTACION | Sí: códigos originales y relación con nombres/épocas |
| S02 | No acreditada | B6 solo define un campo de nombre; A5:F20 no contiene ficha de instalación | PENDIENTE_DE_EVIDENCIA | No identifica estaciones físicas | No hay emplazamientos, homónimos o traslados documentados | Impide fusiones de series/estaciones por texto | Sí: identidad física y tratamiento de cambios |
| S03 | Declaraciones conservadas | B15 desarrolla GBON/RBON como redes global/regional de observación básica; C15/D15 texto/4 | PARCIALMENTE_DOCUMENTADA | Nombres de redes ya localizados, además de la atribución de B2 | Sin lista de miembros, identificadores, vigencia o equivalencias entre redes | Puede citar definición de RED; no vincular estaciones de fuentes diferentes | Sí: membresía, códigos, producto y vigencia |
| S04 | Ubicación DECLARADA; verificación geográfica y CRS DESCONOCIDOS | B9/B10: grados/minutos/segundos, Greenwich/ecuador, X/Y; E16:E19: mención INEI | PARCIALMENTE_DOCUMENTADA | Hay definición geográfica genérica de campos | Sin CRS/datum/precisión/vigencia; aclarar serialización frente a decimales históricos, sin inferir incompatibilidad física | No asignar WGS84, convertir o unir espacialmente | Sí: CRS, ejes, unidades, serialización, calidad y vínculo a instalación |
| S05 | Valor DECLARADO; unidad/referencia vertical no acreditadas | B11: altura respecto al nivel medio del mar; “En metros sobre nivel del mar (msnm)” | PARCIALMENTE_DOCUMENTADA | Unidad literal y referencia genérica ahora localizadas | Sin datum/realización vertical, método, incertidumbre o vinculación por época | Se admite declaración documental msnm, no comparación vertical científicamente defendible | Sí: datum, método/calidad y validez por estación |
| S06 | Cobertura histórica comprobada entonces; operación/validez DESCONOCIDAS | No hay períodos de operación, vigencia de códigos o traslados en X84E | PENDIENTE_DE_EVIDENCIA | El diccionario no añade historial por estación | Cobertura CSV previa no es vida operativa | No extender identidad/instrumento a toda la serie | Sí: períodos y criterios de continuidad |
| S07 | DESCONOCIDO | B6 dice estación automática; no hay sensor/configuración/calibración en el documento | PENDIENTE_DE_EVIDENCIA | Clase general no identifica instrumentación ni calidad posicional | Sin fichas ligadas a estación/época | Aplicabilidad y metrología permanecen pendientes | Sí: sensores, exposición, calibración e incertidumbre |
| S08 | Discrepancia representacional histórica | C19/D19: Alfanumerico/6; E19: Catálogo del INEI; frente a sufijo .0 y longitud 7/8 documentados en E-71 | CONTRADICCIÓN_DOCUMENTADA | Se confirma la declaración frente a la representación histórica discrepante | No se releyó CSV; no demuestra causa, código falso ni reparación única; edición INEI ausente | No geocodificar, recortar .0, completar ceros o reconstruir | Sí: codificación, versión/vigencia y serialización |

## 3. Fechas, horas y continuidad

| ID | Estado anterior (84-D) | Evidencia nueva | Estado propuesto | Justificación | Limitaciones restantes | Impacto sobre interoperabilidad | Consulta institucional |
|---|---|---|---|---|---|---|---|
| T01 | Formato DECLARADO, validez civil históricamente comprobada | B7/C7/D7/F7: fecha de medición, Numérico/8, Formato: aaaammdd | PARCIALMENTE_DOCUMENTADA | Semántica básica y formato localizados | Sin relación exacta con HORA/ventana, zona o etiquetado | Conserva uso civil previo; no crea instante absoluto | Sí: relación fecha–hora–intervalo y convención aplicable |
| T02 | Discrepancia histórica comprobada; interpretación pendiente | B8/C8/D8/F8: hora de medición, Alfanumerico/6, Formato: hhmmss; E-69 documenta cinco/seis posiciones | CONTRADICCIÓN_DOCUMENTADA | La nueva lectura no explica las cinco posiciones históricas | Pérdida de ceros sigue siendo hipótesis; no se reevalúa CSV ni se conoce tolerancia del tamaño | No normalizar HORA ni construir timestamps inequívocos | Sí: ambas representaciones, casos especiales y alcance por revisión |
| T03 | DESCONOCIDO | B7/B8 y F7/F8 no declaran zona; no se localizó otra convención temporal en el documento | PENDIENTE_DE_EVIDENCIA | Formato de reloj no prueba zona horaria | Sin offsets, reglas o cambios históricos | No convertir a UTC/UTC−5 o inferir por geografía | Sí: referencia temporal aplicable y su historia |
| T04 | Parcialmente DECLARADO; extremos DESCONOCIDOS | B12:B14: promedios/total horarios; B7/B8: momento de medición | PARCIALMENTE_DOCUMENTADA | Se reafirma la declaración horaria | Sin duración/alineación/etiqueta e inclusividad explícitas por variable | No desplazar tiempos o decidir contacto/inclusión de ventanas | Sí: límites y ejemplos institucionales de ventanas |
| T05 | Cadencias instrumental/publicación DESCONOCIDAS | B12:B14 declaran horaria; C12:D14 numérico/tamaño10 | PARCIALMENTE_DOCUMENTADA | Frecuencia nominal disponible, sin nuevas cadencias acreditadas | Tamaño 10 no es resolución; no hay muestreo/publicación/redondeo | No generar grillas esperadas ni afirmar continuidad | Sí: cadencias de cada etapa y interrupciones |
| T06 | FECHA_CORTE semánticamente DESCONOCIDA | B20: Día en que se generó el dataset; C20/D20/F20 numérico/8/aaaammdd | PARCIALMENTE_DOCUMENTADA | Se obtiene definición explícita de generación del dataset | No vincula edición/publicación/revisión/registro institucional ni fija extremos de observación | Conservar como metadato de generación declarado; no sustituir FECHA o adquisición | Sí: relación entre generación, publicación, edición y revisiones |
| T07 | Evidencia léxica, continuidad física no acreditada | B5 declara identificador único de registro; no hay política de duplicados/huecos/revisiones | PENDIENTE_DE_EVIDENCIA | Afirmar unicidad del ID no define identidad temporal o continuidad | Sin política de reloj, huecos o sustituciones | No borrar, rellenar o deduplicar observaciones por inferencia | Sí: identidad/revisión de registros e incidencias |

## 4. Variables, procesamiento y calidad

| ID | Estado anterior (84-D) | Evidencia nueva | Estado propuesto | Justificación | Limitaciones restantes | Impacto sobre interoperabilidad | Consulta institucional |
|---|---|---|---|---|---|---|---|
| V01 | Definición parcial DECLARADA | B12: Temperatura promedio horaria (unidad: °C); C12/D12 numérico/10 | PARCIALMENTE_DOCUMENTADA | Descripción, unidad y frecuencia leídas directamente | Sin muestreo, estadístico completo, ventana, modalidad/instrumento o vigencia | Metadatos declarados citables; no habilita umbrales del manual | Sí: definición/método y alcance por serie/revisión |
| V02 | Definición parcial DECLARADA | B13: Humedad relativa promedio horaria (unidad: %); C13/D13 numérico/10 | PARCIALMENTE_DOCUMENTADA | Descripción, unidad y frecuencia leídas directamente | Sin ponderación, referencia/saturación, exposición, instrumento o vigencia | No inferir tolerancias o equivalencia instrumental | Sí: definición, método y condiciones |
| V03 | Descripción/unidad DECLARADAS | B14: Precipitación total horaria (unidad: milimetros por hora); C14/D14 numérico/10 | PARCIALMENTE_DOCUMENTADA | Se conserva la tensión semántica ya descrita, sin demostrar contradicción física | Magnitud, integración, reinicios, ventanas parciales y alcance pendientes | No sustituir unidad por mm/mm/h, convertir o acumular | Sí: significado exacto de total/unidad y método |
| V04 | Vacíos históricos comprobados; codificación DESCONOCIDA | No hay política de vacíos/centinelas por variable en X84E; E/F12:14 vacías | PENDIENTE_DE_EVIDENCIA | Celda documental vacía no define un faltante meteorológico | El vacío histórico no se reinterpreta ni atribuye a ND, error o no medido | No imputar, sustituir por cero o asignar calidad | Sí: representaciones, semántica y agregados incompletos por edición |
| V05 | DESCONOCIDO | C/D12:14 solo declaran Numérico/10; no se hallan fichas metrológicas | PENDIENTE_DE_EVIDENCIA | Tamaño textual no acredita resolución/rango/precisión | Sensores, calibración e incertidumbre no identificados | No establecer límites científicos o resolución desde decimales | Sí: especificaciones y redondeo aplicables por época |
| V06 | Nivel aplicado al CSV DESCONOCIDO | X84E no declara etapas o nivel de procesamiento aplicado | PENDIENTE_DE_EVIDENCIA | Promedio/total no certifica un nivel institucional | Manual o publicación no prueban el tratamiento de este original | No equiparar niveles SENAMHI con QA/QC SPICA | Sí: procesamiento/revisiones y trazabilidad de esta edición |
| V07 | Aplicación y vínculo al CSV DESCONOCIDOS | No se documentan controles/flags aplicados en las 16 definiciones | PENDIENTE_DE_EVIDENCIA | Ausencia de banderines en este diccionario no demuestra ausencia de QC institucional | C/D/M/ND/SC del manual no se trasladan al producto | QA/QC científico sigue deshabilitado; sin etiquetas nuevas | Sí: controles reales, flags y vínculo a registros/edición |
| V08 | DESCONOCIDO | B12:B14 sin vigencias; fechas de core.xml técnicas y revision sin valor | PENDIENTE_DE_EVIDENCIA | Hash y modificación técnica no fechan vigencia de definiciones | Sin historia de cambios o alcance retrospectivo | No aplicar definiciones a todas las épocas automáticamente | Sí: historia variable–producto–período y correspondencias |

## 5. Balance y dudas que permanecen para SENAMHI

**29 IDs únicos:** 1 `RESUELTA_CON_EVIDENCIA`, 13 `PARCIALMENTE_DOCUMENTADA`,
12 `PENDIENTE_DE_EVIDENCIA`, 2 `CONTRADICCIÓN_DOCUMENTADA`, 1 `NO_EVALUABLE`.
**28 brechas permanecen sin resolver.** R01 cierra solo conservación y localización
del diccionario bajo este procedimiento; ninguna propiedad científica queda
certificada. Los dos conflictos representacionales son antecedentes históricos
contrastados con celdas recién leídas, no un recorrido nuevo del CSV.
La ambigüedad de PP y la definición DMS de coordenadas no se convierten en
contradicciones físicas demostradas.

Se conserva el [borrador técnico anterior](solicitud_tecnica_senamhi_borrador.md)
y las [siete consultas agrupadas del 84-D](reconciliacion_evidencias_pnda_paso84d.md#4-consultas-técnicas-a-senamhi-para-revisión-futura).
No se envía comunicación. Destinatario/custodio concreto, canal, fecha de envío
y referencia de trámite: **pendientes**. No hay respuestas nuevas. Tras esta
inspección, las preguntas para futura revisión se precisan así:

| Grupo | Aclaración todavía necesaria | Evidencia que motivaría revisión | Brechas |
|---|---|---|---|
| Q1. Ediciones | ¿Qué diccionario y DOCX corresponden a cada original/edición del CSV y período? ¿Qué fecha/versión editorial y sustituciones rigen? | Manifiesto o declaración institucional que identifique recursos y alcance; no basta fecha interna OOXML | R02–R04, V08 |
| Q2. Estaciones y redes | ¿Cuáles son los códigos originales, espacios de nombres y relación con ESTACION/ID? ¿Qué instalación, membresía GBON/RBON, homónimos, cambios y vigencias corresponden? | Catálogo/historial institucional por estación, red y época | S01–S03, S06 |
| Q3. Espacio y metrología | ¿Qué CRS/datum y serialización tienen los ejes X/Y descritos en DMS? ¿Qué realización vertical corresponde a msnm y cómo se midió? ¿Qué sensores, calidad e incertidumbre aplican? ¿Qué edición INEI y serialización explican UBIGEO? | Fichas por instalación/época y aclaración de representaciones, conservando literales | S04–S08, V05 |
| Q4. Tiempo | ¿Cómo se interpretan cinco/seis posiciones de HORA, horas especiales/incompletas, zona y cambios históricos? ¿Cómo se fijan fecha, etiqueta, límites, duración y cadencias? ¿Cómo se relaciona el día de generación FECHA_CORTE con edición, publicación, revisiones y reloj? | Especificación temporal aplicable por variable/edición con casos explícitos | T01–T07 |
| Q5. Variables y faltantes | ¿Cómo se calculan los promedios TEMP/HR? ¿Qué representa exactamente PP total horario con unidad por hora? ¿Qué muestreo, ventanas parciales, reinicios, faltantes, errores y redondeo aplican? | Definiciones/métodos por variable, instrumento y período, política de vacíos y centinelas | V01–V05, T04–T05 |
| Q6. Procesamiento y QC | ¿Qué procesamiento, revisiones, controles y banderines se aplicaron realmente a este producto/edición? ¿Qué alcance del manual corresponde a estos agregados? | Procedimiento y evidencia de aplicación vinculados al original y registros | V06–V08, R04 |
| Q7. Procedencia y derechos | ¿Quién custodia/emite las definiciones y qué texto/edición de licencia cubre cada distribución/revisión, atribución y uso previsto? | Emisor verificable y condiciones aplicables, con revisión del alcance | R05–R06 |

La recepción futura de documentación no otorga permisos de descarga, persistencia,
identificación física o QA/QC. Puede aportar respuestas parciales o confirmar
limitaciones; no se presupone que existan todos los certificados solicitados.
Los estados propuestos quedan sometidos a revisión, sin actualización operativa.
