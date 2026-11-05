# PASO 84-F: mapa potencial de evidencia para las 29 brechas

Fecha: **2026-11-05**. Preparación offline; **ningún DOCX adquirido o inspeccionado**.
Se mantiene íntegra la [matriz del 84-E](brechas_diccionario_pnda_paso84e.md).
Este mapa no actualiza estados, cierra brechas o afirma que el DOCX contenga
respuestas. Se relaciona con el [plan de adquisición](preparacion_docx_pnda_paso84f.md)
y el [protocolo de lectura futura](protocolo_docx_pnda_paso84f.md).

## Categorías de evidencia potencial

- **A:** diccionario XLSX identificado e inspeccionado en 84-E.
- **B:** documento DOCX todavía desconocido; podría aportar definiciones o referencias.
- **C:** catálogo/fichas/historial **oficiales** de estaciones e instrumentos.
- **D:** documentación temporal institucional de SENAMHI aplicable al producto.
- **E:** condiciones institucionales de uso, procedencia/emisor acreditados.
- **F:** correspondencia oficial entre ediciones/recursos/períodos.

Las letras son clases de evidencia, no documentos existentes demostrados ni
capacidades implementadas. La mención **B posible** es una pregunta de inspección,
no una predicción. Una referencia dentro del DOCX a C/D/E/F solo localizaría otra
fuente pendiente; no la autenticaría o comprobaría. Muestreo, metrología y QC
podrían necesitar documentación técnica adicional que no encaja exclusivamente
en una de estas seis categorías; se explicita en cada caso.

## Cobertura completa, sin cambios de estado

| ID | Estado conservado del 84-E | Evidencia potencial | Qué buscar si se autorizase el DOCX | Evidencia/alcance que seguiría siendo necesario |
|---|---|---|---|---|
| R01 | RESUELTA_CON_EVIDENCIA | A; B solo conservación futura | Identificar su propia copia/hash y localizadores, sin atribuirle el cierre previo | R01 resuelta solo para XLSX; la preservación DOCX sería otra evidencia y no reabre/reescribe el antecedente |
| R02 | NO_EVALUABLE | B | Formato real, contenido localizado, título, edición o desconocido expreso | Adquisición autorizada, lectura segura e integridad; recibir bytes no acredita suficiencia científica |
| R03 | PARCIALMENTE_DOCUMENTADA | A, B posible, F | Manifiesto o referencias explícitas a revisiones del CSV/diccionario | F aplicable a los originales/hashes/períodos; compartir página no basta |
| R04 | PENDIENTE_DE_EVIDENCIA | B posible, F | Versión/fecha editorial, vigencia y sustituciones declaradas | Vinculación de esa edición a producto/período y procedencia; propiedades técnicas no son edición |
| R05 | PENDIENTE_DE_EVIDENCIA | B posible, E, F | Texto o referencia de condiciones, edición y recursos cubiertos | Términos aplicables y revisión del uso/redistribución previsto; no extrapolar de un enlace |
| R06 | PARCIALMENTE_DOCUMENTADA | A, B posible, E | Emisor/custodio y referencia institucional verificable | Autenticidad/procedencia y alcance acreditados, separados de integridad local |
| S01 | PARCIALMENTE_DOCUMENTADA | A, B posible, C, F | Distinción nombre/código/ID de registro y espacio de nombres | Códigos originales y correspondencia oficial con ESTACION por época; sin códigos inventados |
| S02 | PENDIENTE_DE_EVIDENCIA | B posible, C, F | Relación de códigos con instalación, homónimos y emplazamientos | Historial físico aplicable; no equivalencia por texto |
| S03 | PARCIALMENTE_DOCUMENTADA | A, B posible, C, F | Definición y membresía de redes, códigos/producto | Pertenencia vigente por estación/período; B15 XLSX solo desarrolla siglas |
| S04 | PARCIALMENTE_DOCUMENTADA | A, B posible, C, F | CRS/datum, ejes, serialización/unidades y calidad posicional | Ficha geográfica aplicable y verificación técnica pertinente; sin WGS84 por inferencia |
| S05 | PARCIALMENTE_DOCUMENTADA | A, B posible, C, F | Datum/realización vertical, método/calidad y vigencia | A ya declara msnm genérico; falta vínculo a instalación/época e incertidumbre |
| S06 | PENDIENTE_DE_EVIDENCIA | B posible, C, D, F | Vida operativa, renombramientos/traslados, vigencias de identificadores | Historial institucional y convenciones de extremos; cobertura del archivo no es operación |
| S07 | PENDIENTE_DE_EVIDENCIA | B posible, C, F | Instrumentación, exposición, calibración y calidad posicional | Fichas/certificados metrológicos ligados a estación/instrumento/época, si están disponibles |
| S08 | CONTRADICCIÓN_DOCUMENTADA | A, B posible, C, F | Codificación/edición INEI y explicación de serialización UBIGEO | Correspondencia oficial y alcance que expliquen seis caracteres frente a literales .0/7–8 históricos; conservar ambos |
| T01 | PARCIALMENTE_DOCUMENTADA | A, B posible, D, F | Relación FECHA–HORA–ventana, calendario/etiqueta | Definición temporal aplicable al producto/revisión; formato aaaammdd no localiza un instante |
| T02 | CONTRADICCIÓN_DOCUMENTADA | A, B posible, D, F | Especificación de cinco/seis posiciones, casos especiales y correcciones | Evidencia que explique ambos formatos por edición/período; no completar ceros |
| T03 | PENDIENTE_DE_EVIDENCIA | B posible, D, F | Zona, offsets y cambios históricos declarados | Convención institucional aplicable, no deducida por localización nacional |
| T04 | PARCIALMENTE_DOCUMENTADA | A, B posible, D, F | Duración/alineación, etiqueta, extremos/inclusividad por variable | Ejemplos y especificación de ventanas aplicables; no desplazar registros |
| T05 | PARCIALMENTE_DOCUMENTADA | A, B posible, C, D, F | Muestreo, agregación, publicación, redondeo e interrupciones | Cadencias por etapa/instrumento/variable/época; horaria no prueba continuidad |
| T06 | PARCIALMENTE_DOCUMENTADA | A, B posible, D, F | Generación FECHA_CORTE frente a publicación, registro y revisión | A define día de generación; faltan relaciones con ediciones/observaciones y fechas institucionales |
| T07 | PENDIENTE_DE_EVIDENCIA | B posible, C, D, F | Política de duplicados, reloj, huecos y revisiones | Identidad/revisión de registros e incidencias documentadas; no deduplicar por inferencia |
| V01 | PARCIALMENTE_DOCUMENTADA | A, B posible, C, D, F | Método/estadístico/muestreo de TEMP promedio horario y alcance | Definición/instrumento/ventana aplicables; no habilita límites por unidad °C |
| V02 | PARCIALMENTE_DOCUMENTADA | A, B posible, C, D, F | Método/referencia de HR promedio horario, exposición/condiciones | Definición instrumental, promedio, vigencia e incertidumbre; % no prueba equivalencia |
| V03 | PARCIALMENTE_DOCUMENTADA | A, B posible, C, D, F | Magnitud exacta de PP total horario con unidad por hora, integración/reinicios | Aclaración institucional aplicable que preserve el literal previo; sin conversión o corrección personal |
| V04 | PENDIENTE_DE_EVIDENCIA | B posible, D, F | Vacíos, centinelas, errores y ventanas parciales por variable | Política de significado y vigencia por campo/edición; vacío no equivale a cero/ND |
| V05 | PENDIENTE_DE_EVIDENCIA | B posible, C, F | Resolución/rango, calibración, redondeo e incertidumbre | Especificaciones técnicas de instrumento/época; tamaño/decimales no son resolución |
| V06 | PENDIENTE_DE_EVIDENCIA | B posible, F | Etapas de procesamiento/revisión efectivamente aplicadas | Procedimiento y evidencia de ejecución vinculados al original; niveles institucionales no equivalen a SPICA |
| V07 | PENDIENTE_DE_EVIDENCIA | B posible, F | Controles reales, banderines y relación con registros | Procedimiento QC y evidencia de aplicación por edición; citar manual no prueba su ejecución |
| V08 | PENDIENTE_DE_EVIDENCIA | A, B posible, F | Vigencia y cambios de definiciones, producto/variable/período | Historia aplicable y selección revisada; no asumir retroactividad desde un hash o fecha técnica |

## Condiciones de revisión futura

El balance se conserva: **1 resuelta, 13 parciales, 12 pendientes, 2 contradicciones,
1 no evaluable; 28 sin resolver**. En particular, R02 sigue NO_EVALUABLE; el
diseño de una inspección o el enlace recuperado no constituye lectura documental.

Un eventual cierre requerirá documento identificado, hash comprobado, ubicación
concreta, literal/contexto, versión/fecha conocida o desconocida explícita,
alcance producto/estación/variable/período y revisión humana de suficiencia.
Se distinguirán declaración, interpretación, integridad, autenticidad, vigencia,
aplicabilidad y permiso operativo. Una respuesta nueva se registra en otra
revisión documental, sin sobrescribir la matriz histórica, los originales,
catálogo operativo o resultados del piloto de interoperabilidad.

Puede prepararse posteriormente el diagnóstico mínimo con fixtures y las
consultas ya [agrupadas en 84-D](reconciliacion_evidencias_pnda_paso84d.md#4-consultas-técnicas-a-senamhi-para-revisión-futura),
ajustadas por el [84-E](brechas_diccionario_pnda_paso84e.md#5-balance-y-dudas-que-permanecen-para-senamhi).
No se envían ahora. No se hacen fusiones de estaciones, asignaciones de CRS/zona,
normalización HORA/UBIGEO, conversiones, QA/QC científico o interpretación de datos.
