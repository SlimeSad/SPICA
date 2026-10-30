# PASO 77: matriz de evidencias faltantes y bloqueos científicos

Producto: **Variables meteorológicas de las estaciones automáticas de intercambio
internacional, SENAMHI–PNDA, identificado en los expedientes como GBON/RBON**.
Referencia pública registrada anteriormente:
<https://www.datosabiertos.gob.pe/dataset/variables-meteorologicas-de-las-estaciones-autom%C3%A1ticas-de-intercambio-internacional-servicio>.
No se reconfirmó su disponibilidad o contenido actual mediante red.

Esta matriz usa exclusivamente el [expediente 74](fundamentacion_qa_nivel1.md),
las [fichas 75](especificaciones_temp_hr_lim.md), la
[matriz 76](aplicabilidad_temp_hr_lim.md), el
[perfilado 71](perfilado_meteorologico.md) y los antecedentes del
[diccionario 69](csv_streaming.md). Las inspecciones y hallazgos citados son
anteriores, no nuevas lecturas del CSV/diccionario/RAW en este paso.

P1: resolver antes de afirmar aplicabilidad de TEMP-LIM/HR-LIM al producto.
P2: resolver antes de usar la dimensión o método dependiente de ella; no necesariamente
bloquea un rango estático por sí sola. P1/P2 son prioridades internas de SPICA, no
clasificaciones atribuidas a SENAMHI. Una respuesta inexistente no prueba que la
información o el procedimiento institucional no existan.

## Documentación y control de calidad

| Campo/variable | Información documentada | Incertidumbre | Pregunta técnica a SENAMHI | Evidencia necesaria | Regla/módulo afectado | Consecuencia sin respuesta | Prioridad |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Producto/recurso | Página PNDA y denominación GBON/RBON registradas | Correspondencia estable entre publicación, archivo y edición del diccionario | ¿Qué identificador y revisión del producto/recurso corresponden al diccionario y procedimientos entregados? | Identificación institucional y relación de recursos/versiones | Catálogo y procedencia documental | Mantener identidad documental parcial, sin generalizar versiones | P1 |
| Diccionario | Hoja DiccionarioDatos inspeccionada; versión/fecha desconocidas | Vigencia y trazabilidad de definiciones | ¿Pueden proporcionar el diccionario aplicable, versionado y fechado, con historial de cambios disponible? | Diccionario oficial con edición, fecha y campos afectados | Aplicabilidad y Nivel 0 documental | No suplir fecha/versión con la adquisición local | P1 |
| MT-DRD-002 | v02, aprobación visible 28-12-2022; apartados TEMP/HR identificados | Vigencia actual y alcance exacto para GBON/RBON | ¿Sigue vigente esa edición? ¿Qué cambios o documentos la sustituyen o complementan para este producto? | Confirmación institucional, edición aplicable y modificaciones | TEMP-LIM, HR-LIM y demás candidatos | No afirmar vigencia ni traslado automático | P1 |
| Límites TEMP/HR | Condiciones transcritas en fichas 75 | Aplicabilidad a promedios horarios no demostrada | ¿Las subreglas §6.3.1.1(a,b) se aplican expresamente a los promedios horarios publicados? ¿Con qué condiciones y excepciones? | Correspondencia explícita entre método, variable, modalidad, producto y alcance | TEMP-LIM, HR-LIM | Mantener reglas deshabilitadas e información insuficiente | P1 |
| QC del producto | Manual describe procedimientos y códigos; no se acredita su aplicación completa a este CSV | Etapas realmente aplicadas, revisiones y resultados disponibles | ¿Qué controles se aplican antes de publicar el producto y cómo se documentan sus versiones y revisiones? | Procedimiento aplicable y descripción de etapas/productos | QA/QC documental y futura revisión científica | No afirmar que el CSV superó controles por su publicación | P1 |
| Códigos de calidad | Manual menciona C/D/M/ND/SC en su contexto | Existencia, ubicación y significado en el producto concreto | Si existen banderines o códigos por observación, ¿cómo obtener su diccionario y vinculación a registros? | Diccionario versionado y vínculo de códigos/registros | Interpretación de resultados y procedencia | No trasladar códigos del manual ni convertir vacíos a ND | P1 |
| Condiciones territoriales/ambientales | Manual tiene alcance institucional nacional | Pertenencia concreta al alcance y excepciones | ¿Qué redes, estaciones, instrumentos y condiciones ambientales/geográficas cubren las subreglas para este producto? | Alcance explícito y excepciones; relación espacial documentada si corresponde | Aplicabilidad, límites locales | Una etiqueta territorial no demuestra cobertura ni contención | P1 |

## Variables y agregación

| Campo/variable | Información documentada | Incertidumbre | Pregunta técnica a SENAMHI | Evidencia necesaria | Regla/módulo afectado | Consecuencia sin respuesta | Prioridad |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TEMP | B12: promedio horario, unidad °C | Definición de promedio y correspondencia con T_h | ¿Cómo se define el promedio horario de TEMP: muestras, estadístico, intervalo e identificación como temperatura del aire? | Especificación de medición/agregación y correspondencia con T_h | TEMP-LIM y perfil de variable | No equiparar promedio e instantánea ni aplicar límites | P1 |
| HR | B13: promedio horario, unidad % | Promedio, referencia de HR y tratamiento de saturación | ¿Cómo se calcula el promedio de HR y cuál es su definición/referencia instrumental, especialmente cerca de saturación? | Especificación, integración y tratamiento pertinente | HR-LIM | No inferir definición ni tolerancias | P1 |
| PP | B14: total horario; unidad literal «milimetros por hora» | Total frente a intensidad, acumulación y unidad exacta | ¿Qué magnitud representa PP? ¿Cuál es su unidad oficial y cómo se relaciona con el total/intervalo horario? | Definición, unidad exacta y ejemplos documentados de interpretación | PP-LIM y semántica del producto | Conservar literal; no convertir a mm, mm/h o intensidad | P2 |
| PP: integración/reinicios | Declaración de total horario | Ventana, reinicio del acumulador y tratamiento de cambios | ¿Cómo se delimita la ventana de PP y cómo se gestionan reinicios, desbordes o acumulaciones incompletas, cuando existan? | Especificación de agregación y tratamiento de incidencias | PP-LIM, PP-24H y futuras ventanas | No sumar acumulados ni reconstruir totales por analogía | P2 |
| Ventanas TEMP/HR/PP | Descripciones horarias | Intervalo exacto e instante de referencia | ¿Cuál es la duración, alineación y convención de etiquetado de cada ventana? | Definición por variable y edición del producto | Aplicabilidad de modalidades y métodos temporales | No asociar automáticamente a una hora o ventana | P1 para TEMP/HR; P2 para métodos PP |
| Observaciones incompletas | No se documenta política aplicable en el expediente | Mínimo de muestras y publicación de agregados parciales | ¿Qué requisitos de muestras válidas permiten publicar cada agregado y cómo se indican los parciales? | Política de completitud y marcas asociadas | TEMP/HR y futura completitud científica | No declarar completos los agregados por tener valor | P1 |
| Faltantes/centinelas | Existen antecedentes de vacíos; marcadores del perfil son solo léxicos | Convención institucional por campo y versión | ¿Qué valores representan faltantes, no medidos, no disponibles, inválidos u otras condiciones, si existen? | Diccionario de convenciones y política de uso | Nivel 0 documental y futura QA/QC | No recodificar números, cadenas o vacíos automáticamente | P1 |
| Resolución/redondeo | El expediente no acredita especificación instrumental por serie | Relación entre precisión textual, resolución y cálculo | ¿Qué resolución y reglas de redondeo se aplican en medición, agregación y publicación? | Especificación metrológica y de publicación por variable | Incertidumbre, persistencia y fronteras de límites | No deducir resolución de los decimales del CSV | P1 para revisión metrológica |

## Identidad, instrumentos y ubicación

| Campo/variable | Información documentada | Incertidumbre | Pregunta técnica a SENAMHI | Evidencia necesaria | Regla/módulo afectado | Consecuencia sin respuesta | Prioridad |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ESTACION / ID | B6: nombre de estación automática; B5: identificador de registro | Código institucional estable de estación | ¿Cuál es el código estable de estación y cómo se vincula al nombre y a los registros del producto? | Catálogo oficial y tabla de correspondencia versionada | Identidad de estación, catálogo y series | No usar ID del registro o nombre como código físico acreditado | P1 para vínculo instrumental |
| Identidad física | El nombre no acredita una única instalación | Emplazamiento e identidad física por período | ¿Cómo se distingue una estación física de homónimos, renombramientos o distintas instalaciones? | Identidad institucional y períodos de correspondencia | Continuidad, controles por estación | No fusionar series solo por nombre | P1 cuando se vincule evidencia local |
| Reubicaciones/cambios | Perfilado describe variantes léxicas de ubicación, sin demostrar traslados | Historial físico y continuidad | ¿Existe historial de reubicaciones, cambios de nombre o sustitución de instrumentos y sus fechas de validez? | Historial disponible y correspondencia de series | Paso, persistencia, límites locales y continuidad | No interpretar variantes como traslado ni continuidad probada | P2 |
| Instrumentos TEMP/HR | Tipo/modelo por serie no acreditados | Tipo, configuración, exposición y vínculo con estación | ¿Qué características instrumentales son pertinentes para interpretar TEMP/HR y aplicar esas subreglas? | Metadatos técnicos y relación instrumento–estación–período | TEMP-LIM, HR-LIM | No inventar sensor, exposición, altura o exactitud | P1 |
| Calibración/incertidumbre | No documentadas para el producto en el expediente | Incertidumbre, tolerancias y decisión cerca de extremos | ¿Qué documentación metrológica y política de incertidumbre/tolerancias corresponde a las observaciones publicadas? | Especificaciones y política aplicable; historial pertinente cuando esté disponible | Revisión científica de TEMP/HR | No inventar bandas de guarda ni clasificar extremos como errores | P1 |
| LONGITUD/LATITUD/ALTITUD | Campos y variantes descritos en antecedentes | Datum, unidades, referencia vertical y validez temporal | ¿Cuál es el sistema de referencia/datum, unidad de altitud y referencia vertical? ¿Qué período representa cada ubicación? | Catálogo geográfico con referencias y vigencia | Aplicabilidad geográfica y vinculación de estaciones | No asignar WGS84, nivel del mar o conversiones por defecto | P2; P1 si determina alcance |
| UBIGEO | Diccionario: alfanumérico de seis caracteres; antecedentes de representación decimal | Formato oficial, codificación y alcance de la representación | ¿Cuál es el significado, catálogo y formato oficial de UBIGEO en este recurso, incluida la representación decimal registrada en nuestros antecedentes? | Especificación/catálogo aplicable y aclaración de formato | Nivel 0 documental y contexto territorial | No reconstruir ceros, eliminar decimales ni crear códigos | P2 |

## Tiempo y continuidad

| Campo/variable | Información documentada | Incertidumbre | Pregunta técnica a SENAMHI | Evidencia necesaria | Regla/módulo afectado | Consecuencia sin respuesta | Prioridad |
| --- | --- | --- | --- | --- | --- | --- | --- |
| FECHA | F7: aaaammdd | Relación con la ventana horaria y calendario aplicable | ¿A qué fecha de la observación/ventana corresponde FECHA y cómo se combina con HORA? | Especificación temporal del recurso | Consultas y QA/QC temporal | No deducir el instante de cierre/inicio | P2; relación de ventana P1 |
| HORA | F8: hhmmss; perfilado previo con literales de cinco/seis caracteres | Significado oficial de ambas longitudes | ¿Cómo deben interpretarse los valores de cinco y seis caracteres y qué formato oficial garantiza el recurso? | Especificación y ejemplos institucionales documentados | Nivel 0 y futuros métodos temporales | No rellenar ceros ni reconstruir HORA | P2 |
| Zona horaria | Desconocida en la documentación revisada | Tiempo civil/UTC y cambios aplicables | ¿Qué zona horaria o referencia temporal utiliza el producto y qué cambios históricos deben considerarse? | Especificación y períodos de vigencia | Ventanas, paso y continuidad temporal | No asignar zona ni convertir a UTC; no bloquear por ello un rango estático aislado | P2 |
| Etiqueta horaria | Se declara agregación horaria | Inicio, cierre u otra referencia de la ventana | ¿La etiqueta identifica inicio, cierre u otro punto del intervalo? | Convención de etiquetado por variable | Aplicabilidad y correspondencia de agregados | No desplazar observaciones para resolverla | P1 para semántica TEMP/HR |
| Horas repetidas/ausentes | Antecedentes descriptivos; no acreditan causa ni falta de medición | Revisión, duplicado, reloj o ausencia | ¿Cómo se representan y distinguen horas repetidas, ausentes y registros revisados? | Política de duplicados, interrupciones y revisiones | Métodos temporales y trazabilidad | No completar, eliminar o consolidar observaciones | P2 |
| Frecuencia real | Etiqueta horaria en el diccionario | Cadencia de medición, agregación y publicación; continuidad | ¿Cuál es la frecuencia de cada etapa y cómo se informa una interrupción? | Especificación de cadencia y continuidad por serie | Paso, persistencia, ventanas y cobertura | No inferir continuidad de filas contiguas ni de 24 registros | P2 |
| FECHA_CORTE | Campo identificado en el recurso por antecedentes | Semántica y formato oficial no acreditados aquí | ¿Qué significa FECHA_CORTE, cuál es su formato y cómo se relaciona con observación, actualización o revisión? | Definición versionada y ejemplos documentados | Procedencia y temporalidad del producto | No tratarla como fecha de observación o publicación por su nombre | P2 |

## Uso de las respuestas y bloqueos

Cada respuesta deberá identificarse por documento, institución/procedencia, versión,
fecha, apartado y producto/variable a que aplica. Una respuesta puede declarar una
condición sin demostrar su cumplimiento para todas las estaciones o períodos.
Conservar incertidumbres y contradicciones; no convertir una ausencia de respuesta
en una afirmación negativa sobre SENAMHI.

Las preguntas no afirman que existan códigos, historiales, certificados o banderines
no acreditados. Tampoco convierten la respuesta futura en aprobación de SPICA.
TEMP-LIM/HR-LIM permanecen bloqueadas; PP y reglas temporales/locales mantienen sus
bloqueos específicos. La interpretación/revisión humana y cualquier autorización
operativa posterior siguen siendo decisiones separadas.
