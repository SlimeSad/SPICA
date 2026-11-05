# PASO 84-D: matriz de brechas documentales PNDA/SENAMHI

Fecha: **2026-11-05**. Alcance, inventario y fuentes E-* en la
[auditoría principal](auditoria_metadatos_pnda_paso84d.md).
Esta matriz complementa la [matriz científica del 77](matriz_evidencias_senamhi.md),
sin sustituirla o declarar cerradas sus condiciones de aplicabilidad.

`DECLARADO`, `DESCONOCIDO` y las referencias a comprobaciones describen el alcance
de evidencia aportada; no autentican documentos. Una discrepancia de formato
históricamente comprobada se distingue de una hipótesis causal o un desconocido.
No se cambian estados del catálogo, del motor o de las reglas.

**P1:** resolver antes de habilitar la asociación/interpretación dependiente de la
propiedad. **P2:** completar para trazabilidad o para la operación específica que
la requiera; puede convertirse en bloqueante para esa operación. Son prioridades
internas, no clasificaciones de SENAMHI ni permisos de ejecución.
**S:** SENAMHI, mediante el custodio competente del producto PNDA, por identificar;
no se inventan destinatarios, contactos o respuestas. Cada cierre exige documento
identificado, localización concreta, fecha/versión o desconocido explícito, alcance
producto/estación/período y revisión humana de suficiencia. Recibir un archivo o
comprobar su hash no cierra automáticamente ninguna brecha científica.

## 1. Recursos, procedencia y derechos

| Propiedad requerida | Fuente disponible | Evidencia identificada | Estado de verificación | Contradicciones | Impacto sobre interoperabilidad | Requisito documental pendiente | Institución | Prioridad | Condición objetiva de cierre |
|---|---|---|---|---|---|---|---|---|---|
| R01. Acceso local a auxiliares | E-60/E-84D | Informe de 2744 bytes y XLSX de 10815 bytes con hashes comprobados hoy | Integridad local comprobada; contenido según E-69/E-74 | Ninguna nueva en esos bytes | Permite citar una copia identificada; no autoriza ciencia | Conservación estable y cotejo editorial si se requiere ampliar contenido | S para edición; operador SPICA para conservación | P2 | Copia de referencia conservada bajo procedimiento aprobado, manifiesto y localizaciones de contenido verificadas |
| R02. Documento DOCX | E-60/E-84D | URL y rol `metadatos` en informe histórico | Contenido y disponibilidad local DESCONOCIDOS | Ausencia de copia conocida no es contradicción | No puede aportar zona, códigos o procesamiento no leídos | Copia oficial identificada o aclaración documentada de disponibilidad | S | P1 para cualquier afirmación dependiente del DOCX | Entrega/adquisición autorizada, integridad y lectura acotada con versión/fecha y alcance; o constancia institucional de lo no disponible |
| R03. Correspondencia CSV–XLSX–DOCX | E-60/E-69/E-74/E-84C | Misma publicación y campos coincidentes; adquisiciones distintas | Relación documental DECLARADA; equivalencia de ediciones DESCONOCIDA | No se prueba conflicto; faltan ediciones | No trasladar una definición a todas las revisiones del producto | Manifiesto de recursos y edición aplicable | S | P1 | Vínculo institucional explícito entre recurso/revisión del CSV y ediciones de ambos auxiliares, con alcance temporal |
| R04. Vigencia y fechas documentales | E-74/E-84C/E-84D | Versiones del diccionario desconocidas; fechas de adquisición/revisión conocidas | Vigencia DESCONOCIDA | Distintos horarios técnicos no son versiones incompatibles | Bloquea selección automática de definición aplicable por época | Fecha/versión editorial e historial de sustituciones | S | P1 | Documento aplicable fechado/versionado o aclaración formal de versión desconocida y alcance; selección revisada para el período concreto |
| R05. Licencia y redistribución | E-60/E-84C | Mismo enlace `/licenses/odc-by/` en campos históricos distintos | Referencia DECLARADA; términos/alcance no verificados aquí | No hay dos licencias contradictorias demostradas | No autoriza distribución o cambio retroactivo de condiciones | Texto/edición, recursos cubiertos, atribución y condiciones pertinentes | S/custodio de publicación PNDA | P1 antes de redistribuir | Identificación de términos aplicables a las copias/revisiones y revisión del uso previsto; conservar la evidencia anterior |
| R06. Autoría y procedencia | E-60/E-74/E-84C | URLs, atribución SENAMHI, IDs, referencias, métodos y hashes | Atribución documental DECLARADA; autenticidad independiente no acreditada | Ningún conflicto nuevo observado | Referencia e integridad no autentican emisor o aprobación científica | Identificación de emisor y procedencia de nuevas respuestas | S | P1 cuando se requiera autenticidad | Evidencia institucional verificable y revisión de identidad/alcance; no basta una etiqueta VERIFICADO aportada por el llamador |

## 2. Estaciones, instrumentos y espacio

| Propiedad requerida | Fuente disponible | Evidencia identificada | Estado de verificación | Contradicciones | Impacto sobre interoperabilidad | Requisito documental pendiente | Institución | Prioridad | Condición objetiva de cierre |
|---|---|---|---|---|---|---|---|---|---|
| S01. Código de estación | E-74/E-71 | B5: ID de registro; B6: nombre de estación | Nombre DECLARADO; código institucional DESCONOCIDO | No convertir ID del registro en código físico | Identidad de ubicación pendiente | Catálogo y correspondencia con ESTACION del recurso | S | P1 | Código original con espacio de nombres, producto, nombre literal y períodos explícitos de correspondencia |
| S02. Identidad física | E-71/E-84C | Agrupaciones por cinco nombres; dos filas de CANDARAVE en el piloto | No acreditada | Igualdad textual no prueba identidad | No unir series o estaciones de distintas redes/fuentes | Instalación, emplazamiento y tratamiento de homónimos | S | P1 | Relación institucional del código con instalación y época, distinguiendo homónimos/cambios sin fusiones inferidas |
| S03. Institución y red | E-71/E-84C | Fuente SENAMHI; RED GBON/RBON por nombre | Declaraciones conservadas | No hay equivalencia acreditada entre redes/productos | No reutilizar códigos ajenos como identidad universal | Catálogo de redes y relación con el producto | S | P1 al vincular fuentes | Fuente/red/código/producto vinculados con vigencia explícita y procedencia |
| S04. Coordenadas y CRS | E-71 | LONGITUD/LATITUD textuales por nombre | Ubicación DECLARADA; verificación geográfica y CRS DESCONOCIDOS | Ausencia de CRS, no contradicción espacial demostrada | Bloquea alineación espacial defendible | CRS/datum, ejes, unidades, precisión, fecha y vínculo a instalación | S | P1 | Metadatos geográficos institucionales aplicables y revisión técnica pertinente; ninguna asignación automática WGS84 |
| S05. Altitud | E-71 | ALTITUD textual, p.ej. CANDARAVE `3410.0` | Valor DECLARADO; unidad/referencia vertical no acreditadas | Ninguna demostrada | No convertir o comparar altitudes científicamente | Unidad, referencia vertical y método/incertidumbre | S | P1 para operación vertical | Valor vinculado a instalación/fecha con unidad, datum vertical y calidad documentados |
| S06. Operación y vigencia del identificador | E-69/E-71 | Cobertura observada 2015-01-01–2024-06-30 | Cobertura histórica comprobada entonces; operación/validez DESCONOCIDAS | Cobertura del CSV no equivale a operación de estación | No extender identidad o instrumento a toda la historia | Períodos, renombramientos, traslados y criterio de continuidad | S | P1 para series históricas | Historial institucional con extremos/convención de vigencia y correspondencias revisadas por época |
| S07. Instrumentación y calidad posicional | E-74/E-77 | Sin ficha instrumento–estación–período suficiente | DESCONOCIDO | No se presume falla instrumental | Precisión/incertidumbre y aplicabilidad científica pendientes | Sensor/configuración/exposición, calibración y vínculo temporal | S | P1 | Evidencias aplicables al instrumento y ubicación, con períodos y limitaciones; verificación separada del nombre |
| S08. UBIGEO | E-74/E-71 | C19/D19: seis caracteres; datos históricos con `.0` y longitud 7/8 | Discrepancia representacional histórica | Sí, formato declarado frente a representación observada; causa desconocida | No geocodificar, completar ceros o asignar territorios | Codificación, catálogo/versión y aclaración de serialización | S; referencia INEI solo cuando se identifique aplicabilidad | P1 para asociación territorial | Correspondencia institucional explícita con codificación y vigencia; conservar literal original y revisión previa |

## 3. Fechas, horas y continuidad

| Propiedad requerida | Fuente disponible | Evidencia identificada | Estado de verificación | Contradicciones | Impacto sobre interoperabilidad | Requisito documental pendiente | Institución | Prioridad | Condición objetiva de cierre |
|---|---|---|---|---|---|---|---|---|---|
| T01. FECHA | E-74/E-69/E-70 | F7 `aaaammdd`, fechas civiles interpretadas | Formato DECLARADO, validez civil históricamente comprobada | Ninguna nueva | Permite filtro civil; no instante absoluto | Significado en la ventana y calendario/etiquetado aplicables | S | P1 para alineación temporal | Definición de fecha de observación/intervalo y relación explícita con HORA |
| T02. HORA de cinco/seis posiciones | E-74/E-69/E-84C | F8 `hhmmss`; conteos históricos y dos ejemplos `00000`/`10000` | Discrepancia histórica comprobada; interpretación pendiente | Sí, anchura; pérdida de ceros es hipótesis | Bloquea localización/conversión inequívoca | Especificación de ambas representaciones y política de correcciones | S | P1 | Regla institucional versionada, casos válidos y alcance por revisión/período, sin alterar originales |
| T03. Zona horaria | E-74/E-84C | No documentada en las evidencias examinadas | DESCONOCIDO | No es prueba de zona incorrecta | Bloquea comparación absoluta | Referencia temporal, offsets/reglas y cambios históricos | S | P1 para comparación absoluta | Zona/convención institucional aplicable al período, con evidencia de sus reglas; no inferida de la ubicación |
| T04. Ventana y límites | E-74/E-77 | Agregados horarios; etiqueta e inclusividad sin definición suficiente | Parcialmente DECLARADO; extremos DESCONOCIDOS | Ninguna demostrada | No decidir inicio/cierre, contactos o ventanas equivalentes | Duración, alineación, etiqueta y extremos por variable | S | P1 | Definición versionada de ventana e inclusividad, con ejemplos institucionales y alcance |
| T05. Resolución y cadencias | E-74/E-71 | Frecuencia horaria declarada; filas históricas | Cadencias instrumental/publicación DESCONOCIDAS | Número de filas no demuestra periodicidad | No crear grillas esperadas ni afirmar continuidad | Muestreo, agregación, publicación, interrupciones y redondeo | S | P1 para operación dependiente | Especificación por etapa/variable/serie; no deducida de precisión textual o conteos |
| T06. Registro, observación y FECHA_CORTE | E-69/E-84C | FECHA de observación interpretada, FECHA_CORTE literal y fechas técnicas separadas | FECHA_CORTE semánticamente DESCONOCIDA | Fechas técnicas posteriores no son error de observación | No usar adquisición/corte como sustituto del período | Significado de corte, publicación, revisión y fecha de registro institucional | S | P2; P1 si se usa como filtro | Definiciones y relaciones explícitas, distinguiendo registro RAW de registro institucional |
| T07. Duplicados, huecos y revisiones | E-70/E-71 | Unicidad de claves textuales en el perfil histórico | Evidencia léxica, continuidad física no acreditada | Ninguna causa de duplicación/hueco demostrada | No borrar, completar, deduplicar o consolidar por inferencia | Política de revisiones, reloj, interrupciones y ausencia | S | P1 para continuidad | Criterios documentados de identidad/revisión temporal y representación de incidencias |

## 4. Variables, procesamiento y calidad

| Propiedad requerida | Fuente disponible | Evidencia identificada | Estado de verificación | Contradicciones | Impacto sobre interoperabilidad | Requisito documental pendiente | Institución | Prioridad | Condición objetiva de cierre |
|---|---|---|---|---|---|---|---|---|---|
| V01. TEMP | E-74/E-71 | B12, promedio horario, `°C` | Definición parcial DECLARADA | Equivalencia con variable/modalidad del manual no acreditada | No aplicar reglas a promedios por similitud de nombre/unidad | Nombre/definición completos, muestreo, ventana y alcance | S | P1 | Definición aplicable a esta revisión/serie y correspondencia explícita con el método propuesto |
| V02. HR | E-74/E-71 | B13, promedio horario, `%` | Definición parcial DECLARADA | Ninguna física demostrada | Referencia/estadístico/saturación pendientes | Definición instrumental y de promedio, exposición y condiciones | S | P1 | Definición versionada y vínculo instrumento–serie; sin tolerancias inventadas |
| V03. PP | E-74/E-71 | B14, total horario; `milimetros por hora` | Descripción/unidad DECLARADAS | Tensión semántica, no incompatibilidad física probada | No convertir total a intensidad, sumar o normalizar unidades | Magnitud, unidad exacta, integración, reinicios y ventanas parciales | S | P1 antes de interpretar PP | Especificación que resuelva magnitud/unidad y alcance temporal, preservando las declaraciones previas |
| V04. Faltantes por variable | E-71/E-74 | Vacíos observados; sin política de significado suficiente | Vacíos históricos comprobados; codificación DESCONOCIDA | Ninguna semántica de faltante demostrada | No sustituir por cero, ND o dato inválido | Catálogo de vacíos/centinelas y agregados parciales por campo/edición | S | P1 | Política institucional que vincule cada representación a su significado y vigencia |
| V05. Resolución y rangos instrumentales | E-74/E-77 | No hay especificación suficiente de los sensores | DESCONOCIDO | Un límite de aceptación no es rango de sensor | No inferir resolución, exactitud o plausibilidad desde decimales | Ficha técnica aplicable, redondeo/calibración e incertidumbre | S | P1 para uso metrológico | Instrumento identificado por época y especificaciones aplicables, separadas de reglas de calidad |
| V06. Procesamiento institucional | E-74/E-84C | Producto publicado y manual identificado | Nivel aplicado al CSV DESCONOCIDO | Nivel I/II de SENAMHI no equivale a Nivel 0/1 SPICA | No elevar calidad por publicación o clasificación nominal | Etapas de procesamiento, revisiones y trazabilidad del recurso | S | P1 para afirmar calidad | Declaración institucional aplicable a esta edición, con procedimiento y alcance comprobados |
| V07. QC y banderines | E-74/E-77 | C/D/M/ND/SC descritos en ámbito del manual | Aplicación y vínculo al CSV DESCONOCIDOS | No se acredita conflicto ni ausencia de QC por faltar columnas | QA/QC científico permanece deshabilitado | Controles realmente aplicados, flags y relación con registros | S | P1 | Procedimiento/edición y evidencia de aplicación al producto; revisión científica y permiso operativo independientes |
| V08. Vigencia de definiciones | E-74/E-84D | Diccionario identificado por hash, sin versión/fecha | DESCONOCIDO | Fecha de descarga no resuelve vigencia | No aplicar una definición retrospectivamente por defecto | Historia de cambios y relación variable–producto–período | S | P1 | Definiciones y cambios con alcance explícito; revisión anterior y resultado siguen recuperables |

## Uso de la matriz

Ninguna fila se cierra en esta auditoría como identidad física, convención temporal
o validación científica demostradas. R01 aporta una comprobación técnica actual
con límites; no cierra R03/R04 ni cambia aptitudes históricas. El DOCX podría aportar
algunas respuestas, pero no se presume que las contenga.

Las consultas concretas y el procedimiento para incorporar una respuesta sin
sobrescribir historia se describen en la
[propuesta de reconciliación](reconciliacion_evidencias_pnda_paso84d.md).
No se enviaron solicitudes ni se programaron consultas externas.
