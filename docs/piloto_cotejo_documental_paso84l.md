# PASO 84-L — Piloto de cotejo documental PNDA/SENAMHI

Fecha: **2026-11-08**. Resultado: **cinco coincidencias literales**, con integridad
y referencias comprobadas en el alcance descrito. **APTO CON RESTRICCIONES**
para revisión documental, sin permiso operativo, científico o jurídico.
La [arquitectura y auditoría](vinculacion_evidencia_paso84l.md) explica el control
previo independiente, los estados, las pruebas y los límites de confianza.

## Fuentes y control previo

Git inicial limpio, **feature/suadc-http**, HEAD **f6c2a36**, PASO 84-K registrado.
Los cinco IDs se conservan del [piloto 84-K](piloto_afirmaciones_pnda_paso84k.md),
sin sobrescribir sus objetos, documentos o estados históricos. No son nuevas
adquisiciones ni códigos institucionales.

El responsable fijó dos ControlArchivo antes de construir las afirmaciones,
usando tamaño/SHA de la **sección 5 de la solicitud 84-L**. Cada control conserva
ReferenciaCientifica y ProcedenciaCatalogo existentes con ese antecedente.
No se derivó el SHA esperado del archivo recién leído ni de la afirmación.
Las rutas solo seleccionan qué abrir; no se usan como prueba suficiente.

| Control / documento | Archivo exacto autorizado | Bytes esperados = observados | SHA esperado = calculado físicamente |
|---|---|---:|---|
| control-xlsx-84l / XLSX-PNDA-84K | C:\Users\Propietario\SPICA_EVIDENCIAS_PNDA_84E\diccionario-1851039a07682a3f202314f6f8811fc616cb4ca2a486c9e737fd8cea62a4b4dd.xlsx | **10815** | `1851039a07682a3f202314f6f8811fc616cb4ca2a486c9e737fd8cea62a4b4dd` |
| control-docx-84l / DOCX-PNDA-84K | C:\Users\Propietario\SPICA_EVIDENCIAS_PNDA_84F\metadatos-pnda.docx | **20664** | `7b9dcbd71c4d00798d1795edfd5ba0d15ad0aaab0297a7f0aba91532437a0d18` |

La ruta X se obtuvo de **copia** en el manifiesto privado
`SPICA_EVIDENCIAS_PNDA_84E\procedencia.json`, después de comprobar sus
**930 bytes** y SHA-256
`cc3159b4d5c23f4013a9d22b757259d8247bc4616a7342743f48e69bf2e361ae`.
No se siguió el campo origen temporal ni se abrió su antiguo catálogo.
No se abrió el manifiesto DOCX, pues su ruta/control ya estaban autorizados
explícitamente. No se buscó en otras carpetas documentales.

Último recorrido con el componente final:
**2026-11-08T22:45:36.100983+00:00** a
**2026-11-08T22:45:36.794840+00:00**, Python **3.15.1 de .venv**, -B.
El ensayo inicial satisfactorio fue de **22:42:39.236536** a **22:42:39.733738 UTC**;
la confirmación final conservó el mismo conjunto de cinco afirmaciones, no diez.

Se comprobaron rutas contenidas, archivos regulares y ausencia de symlinks,
junctions o reparse points mediante la API existente. Cada cotejo leyó un
snapshot en rb, comprobó descriptor/firma, calculó SHA real y lo interpretó en
memoria. Al terminar volvió a validar ruta/leer/hash/firma, sin cambios.
El arnés externo verificó además ambos originales y el manifiesto X antes y
después: **tres archivos físicamente cotejados**, con las mismas firmas y hashes.
Los inventarios de las dos raíces mantuvieron sus nombres exactos: 3 y 6.
No se atribuyen hashes actuales a los seis auxiliares que no se releyeron.
Comprobación adicional de cierre, después de las pruebas y de redactar los
informes: **2026-11-08T22:51:45.329207+00:00**. Los tres tamaños/hashes y firmas
volvieron a coincidir; inventarios 3/6, cinco referencias y 35 diagnósticos
coherentes con el resumen; banderas de autorización False y guardia en cero.

## Inspección estructural y límites conservados

| Fuente | Inspector empleado | Resultado | Omisiones conservadas |
|---|---|---|---|
| X | diagnostico_xlsx_84e, **0.1.0**, inspeccionar_bytes | SATISFECHA en el perfil existente, celda B14 de DiccionarioDatos encontrada una vez | Formatos no renderizados; fórmulas/nombres no ejecutados; no validación OOXML/XSD completa |
| D | inspector_docx, **0.2.1**, inspeccionar_docx_bytes | DOCUMENTO_VALIDADO_EN_ALCANCE, referencias únicas y con ID/hash/contexto correctos | Destinos externos omitidos/no consultados, formato auxiliar sin renderizar, declaración MC no procesada, IDs Word 2010 no interpretados y otros metadatos no publicados |

Se aplicaron los límites ZIP/XML/texto anteriores y snapshot máximo de **1 MiB**,
con bloques de **65536 bytes**. No se ejecutaron Word/Excel, macros, campos,
fórmulas o vínculos; no se extrajo ZIP a disco. No se amplió el perfil para
obtener coincidencias. Los límites son cooperativos, no garantía de RSS fijo
o interrupción de una llamada bloqueada del sistema de archivos.

## Cinco afirmaciones realmente cotejadas

Las afirmaciones conservan naturaleza **DOCUMENTAL**, nivel **DECLARADA**,
presencia **CON_VALOR**, forma **LITERAL** y vigencia **DESCONOCIDA**. No se
declara verdadero el contenido institucional por coincidir con el documento.
En los objetos de este ensayo, integridad/inspección/autenticidad/correspondencia
de FuenteDocumental permanecen **None**. Las comprobaciones se registran en
ResultadoVinculacion, sin convertirlo automáticamente en Respaldo ni modificar
fuentes históricas. Objetivo/versiones de producto siguen None; versión de
documento X desconocida y D `1.0` declarada, no edición aplicable acreditada.

Las cinco referencias se heredaron del expediente 84-K y se resolvieron contra
la inspección del snapshot actual. D usa **word/document.xml** y namespace
`w = http://schemas.openxmlformats.org/wordprocessingml/2006/main`.
T/F/C/p/P = tabla/fila/celda XML/párrafo local/ordinal global; no página ni
columna renderizada. Ruta D:
`/w:document[1]/w:body[1]/w:tbl[T]/w:tr[F]/w:tc[C]/w:p[p]`, expandida a Clark.
X usa hoja **DiccionarioDatos**, parte **xl/worksheets/sheet1.xml**.
Todos los localizadores están asociados al ID/hash del documento de la tabla.

| Afirmación | Referencia estructural comprobada | Contenido, literal corto o resumen marcado | Resultado físico / estructural / literal | Restricción que sigue abierta |
|---|---|---|---|---|
| K02 — Fecha de creación | D: T1/F7/C2/p1/P34 | Literal `2024-05-30` | Control y conservación SATISFECHA; referencia encontrada; COINCIDE | R04 parcial: fecha civil de la ficha, no vigencia, fecha de observación o edición CSV |
| K04 — Licencia mencionada | D: T1/F11/C2/p1/P42 | Literal `Open Data Commons Attribution License` | Control y conservación SATISFECHA; referencia encontrada; COINCIDE | R05 parcial: términos, edición, atribución y alcance no acreditados; no redistribuir |
| K06 — Validación declarada | D: T1/F3/C2/p5/P13 | Resumen: SENAMHI declara datos horarios validados de temperatura, humedad relativa y precipitación mediante GBON/RBON | Control y conservación SATISFECHA; referencia encontrada; COINCIDE con el párrafo completo, no solo la palabra validados | V07 parcial: sin evidencia independiente de controles, flags, nivel o aplicación al CSV |
| K09 — PP del diccionario | X: DiccionarioDatos!B14 | Literal `Precipitación total horaria (unidad: milimetros por hora)` | Control y conservación SATISFECHA; celda única; COINCIDE | V03: magnitud/unidad/ventana y edición aplicable sin resolver; se conserva milimetros por hora |
| K10 — Precipitación general | D: T1/F3/C2/p9/P17 | Resumen: precipitación medida en milímetros, como altura acumulada; incluye explicación de equivalencia física declarada | Control y conservación SATISFECHA; referencia encontrada; COINCIDE con todo el párrafo | La definición general no demuestra correspondencia exacta con PP o una ventana; no se calculó ni aplicó una conversión |

Ejemplo Clark completo de K10, ordinal global **17**:

```text
/{http://schemas.openxmlformats.org/wordprocessingml/2006/main}document[1]/{http://schemas.openxmlformats.org/wordprocessingml/2006/main}body[1]/{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tbl[1]/{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tr[3]/{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tc[2]/{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p[9]
```

El objeto CotejoAfirmacion conserva tanto la afirmación original como el literal
observado, fuera del repr y de la salida pública. Los textos completos se
compararon por igualdad exacta; aquí se abrevian dos para evitar reproducir
innecesariamente contenido institucional. No se evaluó fidelidad de paráfrasis
automática, no se normalizaron acentos/espacios y no se cambió unidad alguna.

Las cinco conservan las restricciones comunes: identidad institucional,
edición y derechos no comprobados, y procesamiento científico no validado.
K09 conserva también unidad ambigua y convención temporal desconocida; K10,
unidad ambigua. Todas mantienen incertidumbres y pendientes documentales.

K09–K10 conserva una relación **DIFERENCIA_AMBITO**: definición del campo PP
frente a descripción general. No se declara contradicción física inequívoca,
igualdad de magnitudes o equivalencia editorial. Las dos contradicciones
históricas HORA/UBIGEO se conservan en la matriz, sin lectura actual del CSV.

## Diagnósticos, determinismo y barreras

Por cada recorrido se hicieron **dos llamadas de cotejo** (D con cuatro
afirmaciones, X con una) y se repitió cada una invirtiendo su selección.
Resultados completos iguales, con el mismo registro de controles y archivos
sin cambios. Son **cinco resultados individuales únicos**, con dos resultados
de documento y repeticiones de comprobación; no se suman como tests unitarios.
Las fechas UTC pertenecen al arnés, no se introducen como reloj variable en
el algoritmo de diagnóstico. No se hace una promesa de determinismo ante
cambios concurrentes del archivo o de los controles.

| Comprobación actual | Resultado |
|---|---|
| Tamaño/SHA frente a controles previos | 2/2 SATISFECHA |
| Inspección en alcance | 2/2 SATISFECHA |
| Conservación física final | 2/2 SATISFECHA |
| Referencias únicas encontradas | 5/5 SATISFECHA |
| Comparación literal | 5/5 COINCIDE, código literal_coincidente |
| Fallos técnicos del piloto | 0; se conservan todas las limitaciones |
| Autorizaciones/operaciones científicas | **0** |

Para comprobar que el cotejo no promociona fuentes ni habilita ejecución se
evaluaron además las siete OperacionUso del núcleo sobre los cinco objetos:
**35 diagnósticos**, todos con requisitos documentales no satisfechos y
**ejecucion_autorizada=False / operacion_ejecutada=False**. No se usó un
diagnóstico como permiso o entrada a un ejecutor.

Incluso las cinco consultas conservan `integridad_no_acreditada` e
`inspeccion_no_acreditada` en el evaluador anterior: sus campos Respaldo siguen
None deliberadamente. No es un retroceso de las 13 consultas del 84-K ni una
negación del cotejo físico actual; son objetos de ensayo nuevos con el puente
automático deshabilitado. Acreditar o persistir respaldos en un consumidor
requiere diseño y revisión propios. La consulta humana del informe sí puede
usar la evidencia técnica delimitada de este recorrido.

En usos no consultivos se mantienen, entre otros:
`edicion_o_correspondencia_no_acreditada`, identidad institucional no acreditada,
vigencia/aplicabilidad/corroboración no acreditadas; para K04/redistribución,
`falta.derechos_para_el_uso`; para K06/calidad, `falta.validacion_cientifica`;
para K09/K10/interpretación, unidad/significado/validación sin acreditar.
No se asigna una versión de producto, zona horaria, CRS o código de estación.

Los fallos se ensayaron solo en sintéticos: SHA/tamaño incorrecto o archivo
alterado detiene antes de B/C; referencia inexistente/ambigua no se acepta;
texto diferente devuelve DIFIERE; inspección parcial/rechazada no coteja;
fallo final invalida cotejos manteniendo traza; contradicción explícita continúa
registrada aun con cita literal coincidente. El piloto real no fabricó fallos
ni modificó un original para probar esas ramas.

## Evidencia conservada, límites y cierre

El resumen saneado del recorrido final tiene **36729 bytes**, sin originales
binarios, XML íntegro, datos del CSV, contactos, autores o destinos hyperlink:

```text
%TEMP%\spica-84l-j0m0xk7b\piloto-final.py
%TEMP%\spica-84l-j0m0xk7b\piloto-final.json
%TEMP%\spica-84l-j0m0xk7b\piloto-final.log
```

La carpeta temporal privada también conserva el primer ensayo y las pruebas.
No es una nueva evidencia institucional, copia de seguridad o registro
operativo. Su retención temporal no sustituye una política futura de archivo.
Guardia final del piloto: **0 red, 0 SQLite, 0 procesos, 0 escrituras prohibidas
y 0 accesos operativos**. Solo se escriben artefactos propios fuera de Git;
no se alteran permisos, manifiestos, originales o resultados históricos.
La lectura puede actualizar atime por decisión del SO; no se restaura.

Persisten TOCTOU bajo sustitución maliciosa por propietario, dependencia de
APIs privadas y perfiles OOXML limitados. El hash local esperado acredita
coincidencia con controles previos, no autoría, vigencia editorial o veracidad
del contenido. El llamador confiable debe conservar la legitimidad de esos
controles; una procedencia textual fabricada no es una aprobación comprobada.
No hay firma/certificado ni aislamiento frente a Python hostil.

Balance intacto de **29 brechas**: **2 resueltas documentalmente, 17 parciales,
8 pendientes, 2 contradicciones, 0 no evaluables y 27 abiertas**. R04, R05,
V03 y V07 conservan su estado. Las matrices anteriores permanecen sin cambios.

Cero conexiones, GET, descargas, vínculos abiertos, Word/Excel, instalaciones,
migraciones, commits o push. Sin acceso al CSV, RAW, staging o SQLite operativos,
sin conversiones, reconstrucción de HORA/UBIGEO, asignación de coordenadas,
normalización temporal o QA/QC científico. No se afirma una huella nueva de
almacenes que no se abrieron ni control sobre escrituras de terceros.

**APTO CON RESTRICCIONES** para auditar la vinculación experimental. Cinco citas
técnicamente cotejadas continúan sin autorización de uso científico, jurídico,
redistribución, equivalencia editorial o procesamiento del CSV. No se avanza
a otra etapa.
