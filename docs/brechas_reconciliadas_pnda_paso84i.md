# PASO 84-I — Propuesta de reconciliación de las 29 brechas PNDA

Fecha: **2026-11-08**. Propuesta documental para auditoría; **sin integración
operativa ni aprobación científica**. Conserva exactamente los IDs y estados
previos de la [matriz histórica 84-E](brechas_diccionario_pnda_paso84e.md), que
no se modifica. Las condiciones de cierre del
[84-D](brechas_metadatos_pnda_paso84d.md) siguen delimitando cada objeto.

Las referencias X01–X12, D01–D16 y H01 se definen con documento, hash,
localización y límites en el
[catálogo de evidencias](evidencias_consultas_pnda_paso84i.md).
X/D se comprobaron en este paso; **H01 es antecedente CSV histórico**.
Las búsquedas negativas se limitan a X12/D16, no a toda la documentación SENAMHI.

«Parcial» registra evidencia pertinente todavía insuficiente. No equivale a
verdad científica ni a verificación de los controles declarados. «Resuelta» cierra
solo la condición específica de la fila: R01 conserva/localiza el XLSX y R02
acredita disponibilidad, integridad y lectura acotada del DOCX. Ninguna de esas
dos filas cierra identidad de estaciones, zona horaria o calidad meteorológica.

## Recursos, procedencia y derechos

| ID | Estado previo 84-E | Evidencia XLSX | Evidencia DOCX | Coincidencias | Diferencias | Contradicciones | Estado propuesto 84-I | Justificación | Evidencia adicional necesaria | Consecuencia para SPICA |
|---|---|---|---|---|---|---|---|---|---|---|
| R01 | RESUELTA_CON_EVIDENCIA | X identificado desde manifiesto y verificado; X01–X12 localizados | Copia D y contenido localizado D01–D16, sin reemplazar el alcance anterior | Se preservan originales y referencias | Dos copias/formatos y adquisiciones distintos | Ninguna sobre conservación comprobada | RESUELTA_CON_EVIDENCIA | Se mantiene el cierre técnico del XLSX; no se amplía a backup general o autenticidad | Ninguna para ese cierre puntual; conservación/backup futuros requieren procedimiento propio | Referencias documentales reproducibles; originales e historial intactos |
| R02 | NO_EVALUABLE | X01 sirve de contraste de título; no sustituye DOCX | D completo en el perfil 0.2.1, hash/tamaño físicos y referencias de 55 párrafos/tabla; fechas/versión D09 y omisiones explícitas | Mismo producto descrito nominalmente | Ahora existe copia autorizada e inspección admitida | Ninguna que impida el cierre de disponibilidad/lectura | RESUELTA_CON_EVIDENCIA | Se cumple la condición específica del 84-D: adquisición autorizada histórica, integridad, lectura, versión/fecha declaradas y alcance | Revisión humana de este expediente; ediciones, autenticidad y suficiencia temática se evalúan en otras filas | Puede citarse el contenido permitido; no habilita metadatos operativos ni ciencia |
| R03 | PARCIALMENTE_DOCUMENTADA | X01, X02, X05–X10 | D01, D02, D08, D09, D13, D14 | Producto nominal, institución y conceptos de variables/redes compatibles | D es ficha general; X tiene 16 definiciones; ID/FECHA_CORTE no se enumeran en D08 | No se demuestra conflicto de producto ni equivalencia de ediciones | PARCIALMENTE_DOCUMENTADA | Misma descripción de producto y complementariedad; falta vínculo editorial de cada original | Manifiesto institucional CSV–XLSX–DOCX por identidades, revisión y período | Mantener asociación al CSV operativo pendiente; no fusionar revisiones |
| R04 | PENDIENTE_DE_EVIDENCIA | X11: propiedades técnicas; sin fecha/versión editorial | D09: creación/actualización 2024-05-30 y versión 1.0; D15 técnico separado | Las propiedades internas no prueban vigencia | D sí declara fechas y versión visibles; X no | Fechas técnicas distintas no son contradicción editorial demostrada | PARCIALMENTE_DOCUMENTADA | Mejora documental explícita, sin demostrar vigencia ni historia aplicable | Significado/alcance de las fechas, edición de X y CSV, sustituciones y aplicabilidad temporal | Conservar declaraciones y desconocidos; no seleccionar definiciones por fecha automáticamente |
| R05 | PENDIENTE_DE_EVIDENCIA | X12 no aporta términos de licencia; enlace histórico no consultado | D12 nombra Open Data Commons Attribution License y acceso Público | Compatible nominalmente con la referencia histórica ODC-BY | Nombre localizado ahora; términos no inspeccionados | Ningún conflicto de licencias acreditado | PARCIALMENTE_DOCUMENTADA | Existe declaración localizada de licencia/acceso, sin condiciones verificadas | Texto/edición aplicables, atribución y cobertura de distribuciones/revisiones para el uso previsto | No autoriza redistribución, publicación de originales o dictamen jurídico |
| R06 | PARCIALMENTE_DOCUMENTADA | X01: atribución SENAMHI; procedencia técnica de copia | D01/D10: entidad y fuente organizativa declaradas | Atribución institucional coincidente | D identifica una unidad como fuente | Sin contradicción de atribución; autenticidad independiente no evaluada | PARCIALMENTE_DOCUMENTADA | Se precisa la procedencia declarada, no su autenticidad | Confirmación del emisor/custodio para esta edición y respaldo verificable | Registrar por ahora solo en el expediente; no promover confianza automáticamente |

## Estaciones, instrumentos y espacio

| ID | Estado previo 84-E | Evidencia XLSX | Evidencia DOCX | Coincidencias | Diferencias | Contradicciones | Estado propuesto 84-I | Justificación | Evidencia adicional necesaria | Consecuencia para SPICA |
|---|---|---|---|---|---|---|---|---|---|---|
| S01 | PARCIALMENTE_DOCUMENTADA | X02: ID de registro, ESTACION nombre | D06/D08: medición en estación y nombre como metadato | Registro y nombre no se confunden con instalación | D no aporta código de estación | Ninguna entre ambos; el código sigue sin acreditar | PARCIALMENTE_DOCUMENTADA | Definiciones compatibles, sin identificador físico estable | Códigos originales, espacio de nombres y correspondencias con ESTACION por época | No usar ID como código ni inventar estaciones |
| S02 | PENDIENTE_DE_EVIDENCIA | X02/X12: sin ficha física | D06/D16: referencia genérica a estación, sin catálogo físico | Ambas aluden a estaciones automáticas | No hay nueva ficha de instalación | No demostrada; ausencia en el corpus no es inexistencia institucional | PENDIENTE_DE_EVIDENCIA | El nombre y la clase no prueban identidad física | Fichas de instalación, homónimos, emplazamientos y traslados | No fusionar series por similitud de nombres |
| S03 | PARCIALMENTE_DOCUMENTADA | X05: desarrollo de siglas GBON/RBON | D02/D03: contexto de redes e intercambio | Redes global/regional y producto relacionado | D amplía narrativa, no miembros | Sin contradicción localizada | PARCIALMENTE_DOCUMENTADA | Complementariedad conceptual sin membresía individual vigente | Padrón por estación/red/período y correspondencias oficiales | Citar redes declaradas; no inferir identidad entre ellas |
| S04 | PARCIALMENTE_DOCUMENTADA | X03/X09: ejes, DMS y divisiones | D08/D16: lista coordenadas y divisiones, sin CRS/datum | Presencia conceptual de ubicación | D no añade referencia geodésica o serialización | DMS frente a decimales históricos sigue siendo cuestión de representación; no nueva incompatibilidad física demostrada | PARCIALMENTE_DOCUMENTADA | Ubicación declarada, sin marco geodésico aplicable | CRS/datum, ejes, unidades, serialización, precisión y vínculo a instalación/época | No asignar WGS84, convertir ni atribuir coordenadas por nombre |
| S05 | PARCIALMENTE_DOCUMENTADA | X04: msnm y nivel medio del mar | D08 menciona altitud; D16 sin realización vertical | Campo altitud presente | Solo X aporta unidad/referencia genérica | Ninguna contradicción vertical localizada | PARCIALMENTE_DOCUMENTADA | No se completa datum, método o incertidumbre | Referencia/realización vertical, medición, calidad y vigencia por estación | No comparar altitudes como equivalentes científicamente |
| S06 | PENDIENTE_DE_EVIDENCIA | X02/X12: sin operación ni vigencias | D14: Perú, 2015–2024, para el producto | Contexto de estaciones y cobertura general | D añade cobertura de producto, no historia de una estación | Sin contradicción de operación evaluable | PENDIENTE_DE_EVIDENCIA | Cobertura anual no demuestra vida operativa o continuidad física | Historial de operación, cambios y validez de códigos/instalaciones | No extender identidad o sensor a toda la serie |
| S07 | PENDIENTE_DE_EVIDENCIA | X02/X12: automática, sin sensor/calibración | D06/D16: misma clase general, sin ficha instrumental | Estaciones automáticas | Sin configuración instrumental nueva | No demostrada | PENDIENTE_DE_EVIDENCIA | No hay instrumento/exposición/metrología vinculados | Fichas de sensores, calibración e incertidumbre por instalación/época | Mantener aplicabilidad instrumental pendiente |
| S08 | CONTRADICCIÓN_DOCUMENTADA | X09: UBIGEO alfanumérico/6 y referencia INEI | D08 enumera ubigeo; D16 no explica serialización | Campo administrativo presente | X especifica formato; D solo lo enumera | Persiste X09 frente a H01: .0 y longitudes 7–8 históricas, sin causa acreditada | CONTRADICCIÓN_DOCUMENTADA | No se ha resuelto la discrepancia representacional histórica; no se releyó CSV | Edición/codificación INEI, representación oficial y correspondencia con ese original | Conservar literales; no recortar .0, rellenar ceros o geocodificar |

## Tiempo y continuidad

| ID | Estado previo 84-E | Evidencia XLSX | Evidencia DOCX | Coincidencias | Diferencias | Contradicciones | Estado propuesto 84-I | Justificación | Evidencia adicional necesaria | Consecuencia para SPICA |
|---|---|---|---|---|---|---|---|---|---|---|
| T01 | PARCIALMENTE_DOCUMENTADA | X06: FECHA de medición y aaaammdd | D08 enumera fecha/hora; D03 dice horarios | Concepto fecha de observación | D09 son fechas de ficha, no FECHA | Sin contradicción temporal localizada entre documentos | PARCIALMENTE_DOCUMENTADA | Formato básico, sin relación exacta fecha–ventana | Calendario, relación con HORA, etiquetado y ventana por revisión | Conservar fecha civil; no construir instante absoluto |
| T02 | CONTRADICCIÓN_DOCUMENTADA | X06: HORA alfanumérica/6 y hhmmss | D08/D16 sin interpretación de cinco posiciones | Existencia de campo hora | D no especifica formato ni reparación | Persiste X06 frente a H01: cinco/seis posiciones históricas | CONTRADICCIÓN_DOCUMENTADA | Documento nuevo no explica discrepancia; pérdida de ceros sigue siendo hipótesis | Especificación de representaciones, casos especiales y alcance por edición/período | No completar ceros ni transformar HORA automáticamente |
| T03 | PENDIENTE_DE_EVIDENCIA | X06/X12: zona no localizada | D03/D08/D16: sin referencia horaria aplicable | Horariedad no determina zona | Ninguna convención nueva | No hay dos zonas contradictorias acreditadas | PENDIENTE_DE_EVIDENCIA | Sigue faltando zona/offset y reglas históricas | Convención institucional del producto y cambios por época | No asignar UTC, UTC−5 o zona por geografía |
| T04 | PARCIALMENTE_DOCUMENTADA | X06–X08: medición y promedios/total horarios | D03: datos horarios; D04/D05 conceptos generales | Horariedad nominal compatible | D no define inicio/cierre, alineación ni inclusividad | No localizada; falta especificación de ventanas | PARCIALMENTE_DOCUMENTADA | Hora nominal sin ventana verificable | Duración, etiqueta, extremos y ejemplos por variable | No desplazar observaciones ni decidir inclusión de límites |
| T05 | PARCIALMENTE_DOCUMENTADA | X07/X08: agregados horarios | D03: datos horarios; D11: actualización Mensual | Horariedad concordante | Horaria describe datos; mensual describe actualización del producto | Ninguna: procesos distintos, no frecuencias excluyentes | PARCIALMENTE_DOCUMENTADA | Se conoce actualización declarada; no cadencia instrumental/efectiva | Muestreo, agregación, publicación efectiva, interrupciones y redondeo por etapa | Separar frecuencias; no generar grillas o continuidad supuestas |
| T06 | PARCIALMENTE_DOCUMENTADA | X10: FECHA_CORTE día de generación | D09: creación/actualización de ficha; D11 actualización mensual | Hay fechas documentales y metadato de generación | Conceptos distintos, sin vínculo explícito | No se acredita conflicto entre fecha de ficha y corte del CSV histórico | PARCIALMENTE_DOCUMENTADA | D no define FECHA_CORTE ni su relación con edición | Relación generación–publicación–revisión y alcance de cada fecha | No sustituir FECHA por FECHA_CORTE, adquisición o fecha D09 |
| T07 | PENDIENTE_DE_EVIDENCIA | X02: ID único de registro; X12 sin política | D06: medición por registro; D16 sin política | Concepto registro compatible | Sin reglas de duplicados/huecos/revisiones nuevas | No demostrada | PENDIENTE_DE_EVIDENCIA | No hay identidad temporal ni política de continuidad | Política de revisión, reloj, duplicados, incidencias y huecos | No deduplicar, rellenar o eliminar observaciones |

## Variables, procesamiento y calidad

| ID | Estado previo 84-E | Evidencia XLSX | Evidencia DOCX | Coincidencias | Diferencias | Contradicciones | Estado propuesto 84-I | Justificación | Evidencia adicional necesaria | Consecuencia para SPICA |
|---|---|---|---|---|---|---|---|---|---|---|
| V01 | PARCIALMENTE_DOCUMENTADA | X07: TEMP promedio horario, °C | D03/D04: temperatura horaria y definición general | Concepto y horariedad compatibles | D no especifica promedio/muestreo/instrumento | Ninguna definición excluyente demostrada | PARCIALMENTE_DOCUMENTADA | Complemento conceptual, sin método ni aplicabilidad de umbrales | Estadístico, muestreo, ventana, exposición y vigencia | Preservar TEMP/°C; no habilitar reglas científicas |
| V02 | PARCIALMENTE_DOCUMENTADA | X07: HR promedio horario, % | D03/D04: humedad relativa horaria y explicación general del vapor de agua | Concepto porcentual compatible | D no especifica el cálculo del promedio ni referencia instrumental | No localizada | PARCIALMENTE_DOCUMENTADA | No se demuestra método/condiciones del agregado | Promedio, referencia/saturación, exposición, instrumento y vigencia | Preservar HR/%; no inferir tolerancias o equivalencia instrumental |
| V03 | PARCIALMENTE_DOCUMENTADA | X08: total horario, unidad literal milimetros por hora | D05: precipitación general medida en milímetros como altura acumulada; D03 horariedad | Tema precipitación y referencia horaria general | Unidad por hora de campo frente a mm en explicación general; ámbitos no idénticos | Tensión semántica explícita, no contradicción física inequívoca ni equivalencia de magnitudes demostradas | PARCIALMENTE_DOCUMENTADA | Se conservan ambas afirmaciones; D no vincula explícitamente su explicación al código PP/ventana | Definición institucional aplicable de magnitud, unidad, integración, reinicios y ventanas parciales | No cambiar PP a mm, mm/h, intensidad o acumulado; no calcular conversiones |
| V04 | PENDIENTE_DE_EVIDENCIA | X12: sin política de faltantes; E/F12:14 vacías | D07: filtrar registros vacíos para analizar las tres variables | Las variables coinciden | D aporta una recomendación antes no localizada | No define ni contradice causas/centinelas de los vacíos | PARCIALMENTE_DOCUMENTADA | Existe instrucción pertinente, insuficiente para política completa o su ejecución | Semántica de vacíos/centinelas, alcance por variable/conjunto y agregados parciales | Documentar la instrucción; no filtrar ni imputar originales |
| V05 | PENDIENTE_DE_EVIDENCIA | X07/X08: tamaño 10; X12 sin metrología | D04/D05 conceptos generales; D16 sin fichas | No hay especificaciones instrumentales nuevas | Definición física no es resolución o exactitud | No demostrada | PENDIENTE_DE_EVIDENCIA | Tamaño de campo y concepto no fijan resolución/rango/incertidumbre | Sensor, calibración, rango, resolución, redondeo e incertidumbre aplicables | No establecer umbrales, precisión o resolución por decimales |
| V06 | PENDIENTE_DE_EVIDENCIA | X12: no declara nivel o etapas aplicadas | D03 dice validados; D16 no nombra nivel ni procedimiento | Ningún nivel institucional identificable común | Afirmación genérica de validación, sin trazabilidad de procesamiento | No hay niveles contradictorios acreditados | PENDIENTE_DE_EVIDENCIA | El adjetivo no identifica etapas/nivel aplicados al original | Procedimiento/edición, etapas y evidencia de ejecución para el recurso | No mapear niveles SENAMHI a QA/QC SPICA ni afirmar procesamiento comprobado |
| V07 | PENDIENTE_DE_EVIDENCIA | X12: sin controles/flags aplicados | D03 declara datos validados; D16 sin controles, flags o aplicación localizada | Producto meteorológico relacionado | Se localiza una afirmación de calidad, no evidencia independiente de ejecución | Ningún conflicto demostrado; no se prueba ausencia institucional de QC | PARCIALMENTE_DOCUMENTADA | Solo mejora el expediente de declaraciones; controles y vínculo al CSV siguen sin acreditar | Qué significa validado, procedimiento/versión, controles y flags vinculados a registros/edición | No declarar calidad científica, aprobar umbrales ni activar QA/QC superior |
| V08 | PENDIENTE_DE_EVIDENCIA | X11/X12: sin historia/vigencias de definiciones | D09/D14/D15: versión de ficha y cobertura general, sin historia de definiciones | Fechas técnicas separadas de aplicabilidad | D declara versión; no sus efectos retrospectivos sobre TEMP/HR/PP | No se acredita sustitución o contradicción entre ediciones | PENDIENTE_DE_EVIDENCIA | No hay vigencia variable–producto–período demostrada | Historia y correspondencias de definiciones por variable/revisión/período | No aplicar metadatos retroactivamente a toda la serie |

## Balance propuesto y cambios justificados

| Estado | Previo 84-E | Propuesto 84-I |
|---|---:|---:|
| RESUELTA_CON_EVIDENCIA | 1 | **2** |
| PARCIALMENTE_DOCUMENTADA | 13 | **17** |
| PENDIENTE_DE_EVIDENCIA | 12 | **8** |
| CONTRADICCIÓN_DOCUMENTADA | 2 | **2** |
| NO_EVALUABLE | 1 | **0** |
| Total | **29** | **29** |

**27 brechas permanecen sin resolver.** Las dos resueltas son técnicas/documentales,
no propiedades meteorológicas validadas. No se suman evidencias o párrafos como
nuevas brechas, ni se usa el número de documentos coincidentes como aprobación.

Cinco cambios propuestos, todos localizados:

- R02: NO_EVALUABLE → RESUELTA_CON_EVIDENCIA, por disponibilidad/lectura segura,
  integridad y campos declarados de fecha/versión, con omisiones conservadas.
- R04: PENDIENTE_DE_EVIDENCIA → PARCIALMENTE_DOCUMENTADA, por D09; vigencia y
  correspondencia por período siguen pendientes.
- R05: PENDIENTE_DE_EVIDENCIA → PARCIALMENTE_DOCUMENTADA, por D12; no equivale a
  verificar términos o autorizar redistribución.
- V04: PENDIENTE_DE_EVIDENCIA → PARCIALMENTE_DOCUMENTADA, por D07; no define
  todas las representaciones ni ejecuta el filtrado.
- V07: PENDIENTE_DE_EVIDENCIA → PARCIALMENTE_DOCUMENTADA, por la declaración D03;
  no verifica controles, ejecución, flags o validez científica. V06 conserva
  pendiente porque no se nombra un nivel/etapa de procesamiento aplicable.

Los otros 24 estados permanecen iguales. La semántica de PP no se fuerza a
contradicción ni a resolución: una explicación general y una definición de campo
con distinta unidad escrita requieren aclaración de magnitud, ventana y edición.
S08/T02 son discrepancias documentadas con el **CSV histórico**, no dos nuevos
conflictos independientes entre XLSX y DOCX. Se mantienen ambas evidencias.

La asociación al CSV operativo, interpretación horaria, identidad física,
CRS/datum, procesamiento y validación institucional siguen bloqueados según su
evidencia. Las [consultas Q1–Q7](evidencias_consultas_pnda_paso84i.md) continúan
sin envío ni respuestas; R02 ya no requiere obtener una primera copia.
La aceptación de esta propuesta requiere auditoría humana. No actualiza catálogo,
SQLite, adaptadores, resultados de interoperabilidad ni reglas científicas.
