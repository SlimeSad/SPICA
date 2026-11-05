# PASO 84-D: auditoría documental PNDA/SENAMHI

## Alcance, Git y dictamen

Fecha: **2026-11-05**. Rama `feature/suadc-http`, HEAD **`e6e8bc5`**,
`SUADC: integracion local PNDA con interoperabilidad espaciotemporal`.
Git comenzó limpio; el PASO 84-C está registrado.

**APTO CON RESTRICCIONES para consolidación documental y preparación de evidencia
futura.** La identidad física de estaciones, la interpretación temporal completa
y la aplicabilidad científica siguen pendientes. Los estados espacial y temporal
`PENDIENTE_DE_EVIDENCIA` del 84-C permanecen como resultados históricos, sin
recalcularlos ni reemplazarlos en esta auditoría.

Entregables complementarios:

- [Matriz de brechas y condiciones de cierre](brechas_metadatos_pnda_paso84d.md).
- [Reconciliación, contratos y consultas pendientes](reconciliacion_evidencias_pnda_paso84d.md).

Se revisaron documentación y código del repositorio; además, únicamente el informe
y la huella binaria del diccionario en la ubicación temporal previamente conocida.
No se reabrieron CSV, RAW permanente, staging ni SQLite operativo. No se consultó
internet, descargaron recursos, cambiaron permisos o ejecutaron migraciones.
No se modifican módulos Python, dependencias, pruebas, fixtures ni datos originales.

## 1. Evidencia nueva y antecedentes

| Referencia interna de este informe | Naturaleza y alcance |
|---|---|
| E-60 | [Piloto XLSX](conector_senamhi_pnda.md#resultado-de-la-prueba-externa-controlada): adquisición histórica, IDs, hash y ubicación de `informe.json` |
| E-69 | [Inspección del CSV y diccionario](csv_streaming.md): estructura, textos y discrepancias; comprobaciones históricas |
| E-70 | [Consultas locales](consultas_locales.md): FECHA civil, conservación de HORA/UBIGEO y selección literal |
| E-71 | [Perfilado meteorológico](perfilado_meteorologico.md): nombres/redes/ubicaciones, períodos y vacíos históricos |
| E-74 | [Expediente documental](fundamentacion_qa_nivel1.md#diccionario-comprobado-y-contexto-real-disponible): hoja/celdas del XLSX y alcance del manual MT-DRD-002 |
| E-77 | [Auditoría de confianza](auditoria_confianza_documental.md): identificación, inspección, integridad, autenticidad, vigencia, aplicabilidad, aprobación y autorización son condiciones independientes |
| E-84C | [Piloto local](integracion_local_pnda_paso84c.md): última comprobación física del CSV y catálogo; seis descripciones de dos filas |
| E-84D | Lectura actual de `informe.json` y SHA-256 del único XLSX que ese informe identifica, descrita a continuación |

Los códigos E-* son referencias locales del expediente, no identificadores
institucionales, nuevos recursos de catálogo o estados científicos.

### Comprobación local estrictamente acotada

Se utilizó `.venv/Scripts/python.exe -B` y la función `_huella` del arnés auditado
del [84-C](../herramientas/piloto_pnda_84c.py), sin llamar a `ejecutar()`.
La necesidad fue establecer disponibilidad local e identidades exactas de los
auxiliares; los informes del repositorio no acreditaban su presencia actual.

Único informe consultado, sin enumerar su directorio ni buscar archivos privados:

```text
%TEMP%\SPICA-SUADC-piloto-PNDA-soacxq6v\informe.json
```

Disponible: **2744 bytes**, SHA-256:

```text
9e1f8f26c7047bcd803ab75dc66f2b36f9a7d0127ffd519fc63dd4e2a79420df
```

La comprobación principal se ejecutó entre **2026-11-05 05:50:37.825146 y
05:50:37.872622 UTC**. Se cotejó el informe con la huella obtenida al identificarlo;
sus bytes y firma de archivo coincidieron antes/después de la consulta.
Se leyó su JSON con límite de 1 MiB. El informe proporcionó la ruta del XLSX;
se exigió que permaneciera dentro del mismo piloto, sin enlaces/junctions ni `..`,
con nombre igual al hash esperado, antes de leerlo por bloques de 64 KiB.

XLSX físico identificado:

```text
%TEMP%\SPICA-SUADC-piloto-PNDA-soacxq6v\raw\sha256\18\1851039a07682a3f202314f6f8811fc616cb4ca2a486c9e737fd8cea62a4b4dd
```

La ruta real del informe está bajo `C:\Users\Propietario\AppData\Local\Temp`.
Se comprobaron **10815 bytes** y SHA-256:

```text
1851039a07682a3f202314f6f8811fc616cb4ca2a486c9e737fd8cea62a4b4dd
```

Coinciden con E-60/E-69/E-74; la firma dispositivo/inode/tamaño/mtime se mantuvo
estable durante la lectura. No se abrió el contenedor ZIP/XML, reinterpretaron
celdas, copiaron originales o consultó el SQLite de ese piloto. La presencia e
integridad local están comprobadas hoy; las transcripciones de contenido siguen
siendo las inspecciones históricas E-69/E-74. El hash no acredita autenticidad,
vigencia ni aplicabilidad a una edición determinada del CSV.

Los procesos de esta consulta instalaron una guardia que bloqueaba conexiones,
SQLite, escrituras y enumeraciones/mutaciones del piloto y del árbol operativo.
No hubo intentos bloqueados ni aperturas de otros documentos institucionales.
Se necesitaron permisos normales del propietario para leer el piloto protegido;
no se amplió ni modificó su ACL. Las lecturas pueden actualizar atime del SO,
que no se restaura ni se presenta como inalterado.

## 2. Inventario del producto y recursos

Publicación histórica común:
[producto PNDA](https://www.datosabiertos.gob.pe/dataset/variables-meteorologicas-de-las-estaciones-autom%C3%A1ticas-de-intercambio-internacional-servicio).
Este enlace y los siguientes se transcriben de evidencia local; **no se abrieron**.
Fuente declarada `Fuente("SENAMHI", "SENAMHI")`, PNDA como publicación/distribución;
no constituye autenticación independiente del emisor.

ID de producto literal:
`variables-meteorologicas-de-las-estaciones-autom%C3%A1ticas-de-intercambio-internacional-servicio`.

| Recurso | Identidad y disponibilidad | Versión/fecha y alcance comprobado |
|---|---|---|
| CSV de observaciones | asset_id `71df55229ee947fb8e7fed8b1403289e`; adquisición `ff8e7846a9b14568aad924aa8ca93f74`; disponible en RAW según comprobación E-84C | **50474012 bytes**, hash `3d3e8a0a75e070d0b8111faf921be17140c3a0f9db2b4c25d72d99a15a950eab`; última lectura física 2026-11-05 05:15:33–05:15:34 UTC, sin nueva comprobación 84-D. Edición institucional desconocida |
| Diccionario XLSX | asset_id `b6aa17105088497296147feb3c8f06e3` según informe del piloto; presencia y hash comprobados hoy en E-84D, fuera del RAW permanente | **10815 bytes**, hash anterior; hoja `DiccionarioDatos` inspeccionada en E-69/E-74. Versión y fecha documental desconocidas. Comprobación histórica del activo `2026-10-29T07:38:47.823590+00:00` |
| Metadatos DOCX | URL y rol `metadatos` identificados en el informe histórico; **sin adquisición local acreditada ni copia conocida disponible para esta inspección** | Versión, fecha documental, tamaño, hash, asset_id y contenido desconocidos. No se hizo GET del archivo ni se buscó por el equipo |

Que el DOCX no esté disponible en este expediente no demuestra que no exista en
otro lugar o que carezca de información. Su extensión y rol son declaraciones de
publicación, no detección del formato ni comprobación del contenido remoto.

URLs exactas del manifiesto histórico:

```text
CSV
https://www.datosabiertos.gob.pe/sites/default/files/Variables%20Meteorologicas%20de%20las%20Estaciones%20autom%C3%A1ticas%20de%20intercambio%20internacional%20-%20%5BServicio%20Nacional%20de%20Meteorolog%C3%ADa%20e%20Hidrolog%C3%ADa%20del%20Per%C3%BA%20-%20SENAMHI%5D_0.csv

XLSX
https://www.datosabiertos.gob.pe/sites/default/files/Diccionario_Datos_Variables%20Meteorologicas%20de%20las%20Estaciones%20autom%C3%A1ticas%20de%20intercambio%20internacional%20-%20%5BServicio%20Nacional%20de%20Meteorolog%C3%ADa%20e%20Hidrolog%C3%ADa%20del%20Per%C3%BA%20-%20SENAMHI%5D.xlsx

DOCX
https://www.datosabiertos.gob.pe/sites/default/files/Metadatos_Variables%20Meteorologicas%20de%20las%20Estaciones%20autom%C3%A1ticas%20de%20intercambio%20internacional%20-%20%5BServicio%20Nacional%20de%20Meteorolog%C3%ADa%20e%20Hidrolog%C3%ADa%20del%20Per%C3%BA%20-%20SENAMHI%5D.docx
```

El informe conserva fecha técnica propia `2026-10-29T07:38:46.220610+00:00` y una
comprobación de publicación posterior `2026-10-29T07:38:47.488818+00:00`. No se
usa la primera como prueba de que todas las operaciones ya habían finalizado:
ambas son campos técnicos del informe, no fechas editoriales. El HTTP 200
registrado corresponde al XLSX adquirido entonces, no al DOCX ni a acceso vigente.

### Derechos y relaciones acreditadas

El informe E-60 usa la clave `licencia_declarada` para el enlace
`http://opendefinition.org/licenses/odc-by/`. E-84C conserva el mismo enlace en
`referencia_licencia`, con `licencia_declarada=None`. Es una diferencia histórica
de representación; no demuestra dos licencias incompatibles ni ausencia de toda
referencia. No se leyó aquí el texto de licencia, confirmó su edición, alcance,
atribución o redistribución aplicable a los tres recursos. No se autoriza publicar
el cuerpo del CSV o los auxiliares por inferencia a partir de ese enlace.

Está acreditado documentalmente que los tres enlaces fueron enumerados bajo el
mismo producto en E-60; la URL CSV coincide con la identidad de E-84C. E-69/E-74
informan coincidencia del encabezado de 16 campos con el diccionario. **No está
acreditada una correspondencia de ediciones** XLSX–CSV–DOCX ni su vigencia por
estación/período. Compartir página, nombre o columnas no prueba esa correspondencia.
La adquisición del XLSX y la del CSV fueron operaciones distintas, con varios
horarios técnicos; no se fusionan activos, versiones o evidencia.

Otros antecedentes: MT-DRD-002 v02, aprobación visible 28-12-2022, hash histórico
`4f92172b99b351705b684f3a97c98ca16bb055174f0fe9253e9e65336a7ac9f8`, según E-74.
No se comprobó hoy su copia física, vigencia o aplicabilidad al CSV. Los índices
OMM citados no aportan capítulos inspeccionados ni nuevos hechos en este paso.

## 3. Identidad, red y ubicación de estaciones

E-69/E-74 transcriben `ID` como identificador **del registro** (B5) y `ESTACION`
como nombre de estación automática (B6). No hay un código institucional de estación
acreditado en esos extractos. `SENAMHI` identifica procedencia declarada; `GBON` y
`RBON` son literales de RED, sin demostrar identidad física o equivalencia entre redes.

Los cinco nombres históricos y su RED son CANDARAVE/RBON, CARANIA/GBON, IMATA/RBON,
MATUCANA/GBON y SAN_JOSE_DE_UZUNA/RBON, según
[ubicaciones del perfil E-71](perfilado_meteorologico.md).
Allí se conservan LONGITUD, LATITUD y ALTITUD como textos, junto a divisiones
administrativas y UBIGEO. No se vuelven a copiar como un catálogo oficial de
estaciones ni se transforman en coordenadas verificadas.

Ejemplo documental, sin nueva lectura CSV: CANDARAVE tiene los literales
LONGITUD `-70.2541`, LATITUD `-17.268`, ALTITUD `3410.0`, RED `RBON` en E-71.
No están acreditados CRS/datum, ejes/unidades, referencia vertical, precisión,
emplazamiento/instrumento ni validez temporal de ese conjunto. No se asigna WGS84,
unidad de altitud o localidad por el parecido de los valores.

El intervalo civil observado 2015-01-01–2024-06-30 en E-69/E-71 es cobertura del
archivo, no período de operación de la estación o vigencia de su identificador.
Un nombre con una ubicación textual constante no prueba continuidad física,
ausencia de traslados o equivalencia con otra ficha institucional.

## 4. Convención temporal y ausencias

| Propiedad | Evidencia y clasificación | Decisión conservada |
|---|---|---|
| FECHA | E-74: F7 declara `aaaammdd`; E-69/E-71 verificaron fechas civiles válidas en aquel recorrido | Se admite la interpretación civil del consultor; falta relación exacta con inicio/cierre de la ventana |
| HORA | E-74: F8 declara `hhmmss`; E-69/E-71 observaron cinco y seis caracteres | Conservar originales; discrepancia de formato acreditada históricamente, sin regla de reparación |
| Cinco caracteres | E-69: 170400 valores, literales `00000` a `90000` por saltos textuales documentados | Pérdida de ceros en una serialización numérica es hipótesis, no causa demostrada |
| Seis caracteres | E-69: 245873 valores con forma/rangos léxicos compatibles con hhmmss | Compatibilidad léxica no establece zona, instante, completitud o ausencia de colisiones bajo otra interpretación |
| Zona y cambios históricos | No acreditados por la documentación examinada | No asignar UTC, UTC−5 o una zona por ubicación nacional |
| Etiquetado y extremos | No se acredita inicio/cierre, ventana, inclusividad o referencia del intervalo | No desplazar HORA, construir medianoches ni fijar límites implícitos |
| Cadencias | Declaración horaria para agregados; muestreo instrumental, integración y publicación no suficientemente definidos | Separar frecuencia declarada, resolución y cadencia efectiva; no deducirlas de 24 filas |
| Faltantes | E-71 registra vacíos TEMP/HR/PP y búsquedas léxicas de centinelas | Vacío no significa automáticamente ND, error, cero o no medido; política institucional pendiente |
| Fecha técnica y observación | E-84C distingue registro RAW y comprobación HTTP de 2026 frente a FECHA civil de 2015 | No convertir adquisición, actualización o revisión en fecha de observación |
| FECHA_CORTE | E-69 observa el literal `20240630` en ese original | No acredita por su nombre fecha de publicación, descarga, observación o cierre de cada agregado |

E-84C solo releyó dos filas con HORA `00000` y `10000`; no volvió a comprobar
todos los conteos. Tampoco se hace aquí. El contraste de UBIGEO es análogo:
E-74 C19/D19 describe seis caracteres alfanuméricos; E-71 informó sufijo `.0`
y longitudes 7/8. Se acredita discrepancia representacional, no códigos
administrativos falsos ni una reconstrucción única.

## 5. Variables TEMP, HR y PP

Las siguientes son transcripciones/interpretaciones **documentales históricas**
E-69/E-71/E-74, no una nueva lectura de celdas ni validación científica.

| Propiedad | TEMP | HR | PP |
|---|---|---|---|
| Código original | `TEMP` | `HR` | `PP` |
| Nombre/descripción disponible | Temperatura promedio horaria, según los extractos | Humedad relativa promedio horaria, según los extractos | Precipitación total horaria, según los extractos |
| Localización del diccionario | `DiccionarioDatos`, B12 | B13 | B14 |
| Unidad conservada | `°C` | `%` | Texto literal `milimetros por hora` |
| Definición suficiente | Promedio declarado; muestreo, estadístico y ventana exacta pendientes | Promedio declarado; referencia, muestreo y saturación pendientes | Total declarado; magnitud, ventana, reinicios y relación con intensidad pendientes |
| Periodicidad | Horaria declarada, sin continuidad demostrada | Igual | Igual |
| Resolución instrumental/publicada | No acreditada; los decimales del CSV no la establecen | No acreditada | No acreditada |
| Faltantes y centinelas | Vacíos observados; semántica oficial pendiente | Igual | Igual |
| Nivel de procesamiento institucional | No acreditado para este CSV | No acreditado | No acreditado |
| Controles de calidad aplicados | No acreditados por publicar el producto o citar el manual | Igual | Igual |
| Rango instrumental, exactitud e incertidumbre | No acreditados | No acreditados | No acreditados |
| Versión y vigencia de la definición | Diccionario sin versión/fecha acreditadas | Igual | Igual |

Un rango de aceptación de un manual no es un rango de sensor. La diferencia
entre el total horario de PP y la unidad textual requiere aclaración semántica;
no demuestra por sí sola magnitudes incompatibles. No se sustituye ese literal
por mm, mm/h ni intensidad instantánea. Los conceptos de temperatura del aire y
HR del manual no se trasladan automáticamente a los promedios del producto.

El Nivel I/II institucional y los códigos C/D/M/ND/SC descritos en E-74 pertenecen
al ámbito del manual. No prueban el nivel de procesamiento del CSV ni equivalen
al Nivel 0/1 de SPICA. Todas las reglas científicas continúan sin activación.

## 6. Conclusiones y comprobaciones de cierre

Las contradicciones de formato HORA/UBIGEO se distinguen de desconocidos sobre
zona, identidad, CRS, versiones y calidad. La posible pérdida de ceros sigue siendo
hipótesis. La relación de ediciones y la semántica de PP requieren documentación
adicional. No hay una respuesta institucional nueva ni una reconciliación física
de estaciones completada por este paso.

La [propuesta de reconciliación](reconciliacion_evidencias_pnda_paso84d.md) reutiliza
historiales, referencias y resultados inmutables. Se identificaron límites de
representación/automatización que se documentan para una futura necesidad real;
no se demostró una necesidad actual de cambiar código o crear otra base.

**No se ejecutó de nuevo la suite ni `pip check`**: solo se crean tres documentos.
La última suite **reportada y ejecutada en E-84C** es de **1431 aprobadas, 0 fallidas
y 0 errores**; no es un resultado de 84-D. Pruebas unitarias nuevas en este paso: 0.
Las comprobaciones ejecutadas aquí son lectura documental, hashes locales acotados,
inspección estática y controles de coherencia/enlaces, `git diff --check` y
`git status --short`. La compatibilidad se sustenta en no modificar código,
contratos, dependencias, configuración o fixtures; no en una nueva corrida funcional.

Git final conserva rama y HEAD, sin cambios en archivos previamente registrados
ni en el índice. Solo se crean:

```text
docs/auditoria_metadatos_pnda_paso84d.md
docs/brechas_metadatos_pnda_paso84d.md
docs/reconciliacion_evidencias_pnda_paso84d.md
```

Los documentos nuevos se revisan directamente porque no aparecen en el diff de
archivos ya registrados. Resultado de cierre: **29 brechas únicas** cubiertas por
**7 grupos de consultas**, **27 enlaces locales/anclas** válidos y **12 tablas**
con columnas coherentes; UTF-8, bloques y finales sin incidencias. El enlace
externo Markdown se revisó solo como texto, sin abrirlo; las URLs de los recursos
se transcriben del informe local. `git diff --check`, diff de archivos registrados
y diff del índice terminaron con código 0 y sin salida.

Estado final de `git status --short`:

```text
?? docs/auditoria_metadatos_pnda_paso84d.md
?? docs/brechas_metadatos_pnda_paso84d.md
?? docs/reconciliacion_evidencias_pnda_paso84d.md
```

No se ejecutan commits o push. No se envían consultas.
INGEMMET `/query`, GIS real y QA/QC científico siguen sin autorización.
