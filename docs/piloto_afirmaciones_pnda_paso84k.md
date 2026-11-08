# PASO 84-K — Piloto de afirmaciones documentales PNDA/SENAMHI

Fecha: **2026-11-08**. **APTO CON RESTRICCIONES** para consulta documental,
comparación manual y preparación de preguntas institucionales. Sin integración
operativa, equivalencia editorial o autorización científica. La
[auditoría del núcleo](auditoria_procedencia_metadatos_paso84k.md) registra
el defecto corregido, los tests, Git y los límites de confianza.

## A. Fuentes físicamente verificadas

Recorrido satisfactorio del piloto: **2026-11-08T22:11:44.274704+00:00** a
**2026-11-08T22:11:44.840755+00:00**, con Python **3.15.1 de .venv**, offline.

| Fuente local | Ruta original autorizada | Bytes | SHA-256 físico antes/después |
|---|---|---:|---|
| XLSX-PNDA-84K, X | C:\Users\Propietario\SPICA_EVIDENCIAS_PNDA_84E\diccionario-1851039a07682a3f202314f6f8811fc616cb4ca2a486c9e737fd8cea62a4b4dd.xlsx | 10815 | `1851039a07682a3f202314f6f8811fc616cb4ca2a486c9e737fd8cea62a4b4dd` |
| DOCX-PNDA-84K, D | C:\Users\Propietario\SPICA_EVIDENCIAS_PNDA_84F\metadatos-pnda.docx | 20664 | `7b9dcbd71c4d00798d1795edfd5ba0d15ad0aaab0297a7f0aba91532437a0d18` |

Los IDs son locales al ensayo; no son códigos institucionales ni identificadores
nuevos de producto o adquisición. Se verificó primero el manifiesto privado
X `procedencia.json`: **930 bytes**, SHA
`cc3159b4d5c23f4013a9d22b757259d8247bc4616a7342743f48e69bf2e361ae`.
La ruta X se recuperó de **copia**, no se abrió el origen temporal histórico.

Se comprobaron rutas absolutas contenidas, archivos regulares y ausencia de
symlinks/junctions/reparse points en componentes, usando `_ruta_autorizada`
existente. Se reutilizó `_huella` para lectura acotada, descriptor y firmas
dispositivo/inode/tamaño/mtime, sin invocar funciones de adquisición o catálogo.
Los **nueve archivos originales** (3 en 84-E, 6 en 84-F) conservaron tamaño,
hash y firmas; inventarios exactos sin añadidos/eliminaciones. Sus siete
auxiliares se leyeron solo para huella, salvo el manifiesto X. No se ejecutó
el procedimiento histórico 84-H ni se reescribió un control.
Comprobación adicional de cierre, después de la suite y de redactar los
informes: **2026-11-08T22:17:08.908926+00:00**. Los nueve tamaños/hashes e
inventarios 3/6 volvieron a coincidir; las 86 banderas de autorización y
ejecución del resumen se comprobaron False, con todos los contadores de
guardia en cero. No se reejecutó la evaluación ni se abrió un recurso externo.

| Inspector reutilizado | Resultado actual y alcance |
|---|---|
| herramientas/inspeccionar_xlsx_84e.py, 0.1.0 | 10 partes, una hoja DiccionarioDatos, parte xl/worksheets/sheet1.xml, 115 celdas XML, 79 literales, 0 fórmulas; conservación antes/después True |
| adquisicion/verificacion/docx, 0.2.1 | DOCUMENTO_VALIDADO_EN_ALCANCE; conservación True; 12 partes, 55 párrafos canónicos, una tabla de 17 filas/34 celdas, 3 destinos externos omitidos |

La extracción no ejecuta fórmulas, instrucciones, macros o vínculos ni extrae
archivos ZIP a disco. Mantiene los límites previos de snapshot/ZIP/XML/texto y
plazo cooperativo de cinco segundos; no promete RSS fijo, renderizado o XSD
OOXML completo. DOCX admite su perfil limitado, no semántica científica.
No se publican contactos, autores, destinos o documentos binarios en Git.

Dos recorridos iniciales del arnés se detuvieron antes de evaluar usos por una
aserción de fidelidad de unidad: la tubería PowerShell había codificado `°C`
como `?C` en el arnés temporal. Se corrigió exclusivamente la codificación de
ese arnés, leyendo la unidad TEMP del literal y preservando Unicode para D.
No era una discrepancia entre originales, no se cambió su contenido ni se
relajó la aserción. Los inspectores cotejaron conservación en esas lecturas;
el recorrido satisfactorio volvió a comprobar los nueve controles al final.

Guardia del recorrido satisfactorio: **0 red, 0 SQLite, 0 procesos, 0 escrituras
prohibidas y 0 accesos operativos**. Solo se escribió un resumen saneado en el
temporal privado indicado en la auditoría. La lectura puede actualizar atime
por decisión del SO; no se restauró ese metadato ni se modificaron ACL.
Modelo secuencial con directorios controlados; sin prometer aislamiento ante
sustitución concurrente maliciosa por propietario/administrador.

## B. Representación: 12 afirmaciones y sus referencias

Se construyeron **dos FuenteDocumental, 12 AfirmacionDocumental y tres
RelacionAfirmaciones** en un solo ExpedienteMetadatos, usando los contratos
existentes. Son objetos de ensayo en memoria, sin registro en catálogo o SQLite.

Todas las afirmaciones tienen naturaleza **DOCUMENTAL**, nivel **DECLARADA**,
presencia **CON_VALOR** y vigencia **DESCONOCIDA**. Nivel DECLARADA describe
lo que afirma el documento: no niega la lectura física comprobada ni promueve
la verdad científica de su texto. Integridad e inspección de ambas fuentes
se registran VERIFICADO mediante Respaldo/ProcedenciaCatalogo existentes,
con fecha UTC del recorrido, método, tamaño/hash y versión del inspector.

Autenticidad y correspondencia editorial permanecen **None**; producto objetivo
y versión de producto **None** en ambas fuentes. No se inventa un código para
llenar la identidad. `version_documento` de X es None; la de D conserva **1.0**
como declaración visible, sin acreditar aplicación a X o al CSV. La fecha civil
queda como contenido literal, no como timestamp ni vigencia. Todas las
constataciones científicas/jurídicas están vacías y `vigencia` temporal no aportada.

**Convención de referencias D:** todas pertenecen a **word/document.xml** y
namespace `w = http://schemas.openxmlformats.org/wordprocessingml/2006/main`.
`T/F/C/p/P` significa tabla, fila, celda XML, párrafo local y ordinal global
devueltos por el inspector. No es página, columna renderizada o estación.
La ruta se expande como
`/w:document[1]/w:body[1]/w:tbl[T]/w:tr[F]/w:tc[C]/w:p[p]`, sustituyendo
cada `w:nombre` por `{URI}nombre` para obtener Clark. Ejemplo K06:

```text
/{http://schemas.openxmlformats.org/wordprocessingml/2006/main}document[1]/{http://schemas.openxmlformats.org/wordprocessingml/2006/main}body[1]/{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tbl[1]/{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tr[3]/{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tc[2]/{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p[5]
```

Referencias X: hoja literal **DiccionarioDatos**, parte
**xl/worksheets/sheet1.xml**. ID/hash se heredan de X/D anteriores. Se cotejó
la existencia y el contenido de cada celda/rango/párrafo contra el inventario
actual del inspector; las referencias del núcleo no se usaron como verificador.

En la tabla, «resumen» identifica abreviación del informe; el objeto conserva
el literal completo salvo K11/K12, marcados como paráfrasis controlada.

| ID | Fuente y referencia comprobada | Declaración representada | Ámbito y alcance | Pendiente o restricción específica |
|---|---|---|---|---|
| K01 | D, T1/F1/C2/p1/P5 | Resumen: título del producto de variables meteorológicas de estaciones automáticas de intercambio internacional, atribuido a SENAMHI | Título visible de la ficha. La existencia/lectura del DOCX se acredita en A, no como si fuera una declaración del emisor | R02 solo disponibilidad local; no autentica producto, edición o CSV |
| K02 | D, T1/F7/C2/p1/P34 | Literal `2024-05-30` | Fecha de creación declarada en la ficha | R04 parcial; no fecha de observación, generación CSV o vigencia |
| K03 | D, T1/F10/C2/p1/P40 | Literal `1.0` | Versión declarada de la ficha | R04/R03: falta correspondencia editorial y aplicabilidad |
| K04 | D, T1/F11/C2/p1/P42 | Literal `Open Data Commons Attribution License` | Nombre de licencia mencionado | R05 parcial; términos/destino no abiertos, edición, atribución, cobertura y derechos no comprobados |
| K05 | D, T1/F3/C2/p13/P21 | Resumen: se indica filtrar registros vacíos para analizar temperatura, humedad relativa y precipitación | Recomendación en descripción general; no se ejecuta | V04 parcial; causas, centinelas, criterio por variable/conjunto y agregados parciales desconocidos |
| K06 | D, T1/F3/C2/p5/P13 | Resumen: SENAMHI declara disponer de datos horarios validados de las tres variables mediante GBON/RBON | Afirmación genérica de validación | V07 parcial; controles, flags, nivel, evidencia de aplicación y corroboración no acreditados |
| K07 | X, B12; código TEMP cotejado en A12 | Literal `Temperatura promedio horaria (unidad: °C)` | Descripción del campo TEMP; unidad literal °C | V01/T04: muestreo, ventana, instrumento y aplicabilidad pendientes; convención temporal desconocida |
| K08 | X, B13; código HR cotejado en A13 | Literal `Humedad relativa promedio horaria (unidad: %)` | Descripción del campo HR; unidad literal % | V02/T04: método/promedio, ventana, condiciones y aplicabilidad pendientes; convención temporal desconocida |
| K09 | X, B14; código PP cotejado en A14 | Literal `Precipitación total horaria (unidad: milimetros por hora)` | Campo PP total horario; unidad literal milimetros por hora | V03: ambigüedad de magnitud/unidad y ventana; no cambiar a mm o intensidad |
| K10 | D, T1/F3/C2/p9/P17 | Resumen: precipitación medida en milímetros como altura de lluvia acumulada; conserva la explicación literal completa | Definición general, sin correspondencia exacta con PP/ventana | V03: unidad literal milímetros, distinta de K09; no demuestra equivalencia o contradicción física inequívoca |
| K11 | X, A8:F8 | Paráfrasis controlada: concatena literalmente HORA, descripción, tipo Alfanumerico, tamaño 6 y Formato: hhmmss, con etiqueta de celda | Especificación documental del campo; no consulta registros | T02/T03: no hay zona/offset, extremos o reparación acreditados; no reconstruir HORA |
| K12 | X, A19:F19 | Paráfrasis controlada: concatena literalmente UBIGEO, descripción, tipo Alfanumerico, tamaño 6 y Catálogo del INEI, con etiqueta de celda | Código de ubicación declarado; no identidad física de instalación ni geocodificación | S08/S02/S04: interpretación representacional, edición INEI, estación/época y CRS pendientes; no reconstruir UBIGEO |

En K11/K12 se concatenaron únicamente celdas con literal, conservando valores
y coordenadas; las vacías no se transformaron en nulos institucionales. Los
tamaños son declaraciones de campos, no precisión o resolución instrumental.
También se comprobó **D T1/F9/C2/p1/P38**, última actualización `2024-05-30`;
no se creó una afirmación número 13. En total, **12 referencias principales
distintas** (7 D y 5 X), más ese párrafo y tres etiquetas A12:A14 de apoyo.

Todos los contenidos de objeto proceden de la extracción actual. Las unidades
no vacías se cotejaron como subcadenas exactas del literal, sin normalizar
acentos, símbolos o denominaciones. No se infirieron unidades para campos de
fecha, licencia, códigos, hora o declaraciones generales.

Restricciones comunes a los 12 objetos: **identidad institucional no comprobada,
edición no comprobada, derechos no comprobados y procesamiento científico no
validado**. Se conserva la razón de incertidumbre y pendientes en EvidenciaDocumental.
Adicionales: convención temporal desconocida en K07/K08/K09/K11; unidad ambigua
en K09/K10; identidad espacial desconocida en K12. No se fabrican constataciones
de aplicabilidad, corroboración, CRS, unidad acreditada, calidad o derechos.

### Relaciones y contradicciones

| Par | Tipo representado | Justificación y consecuencia |
|---|---|---|
| K09–K10 | DIFERENCIA_AMBITO | Campo PP del diccionario frente a definición general. Se conserva la tensión de unidades, sin convertirla en contradicción genuina o equivalencia |
| K01–K07 | CORRESPONDENCIA_NO_DEMOSTRADA | El título de D y una definición de X no acreditan edición común ni aplicación al CSV. Su vínculo bloquea usos no consultivos, sin borrar las afirmaciones |
| K02–K03 | COMPLEMENTARIEDAD | Fecha civil y versión visible son campos distintos de la ficha; no prueban vigencia o edición aplicable |

No se declaró una contradicción nueva genuina entre las 12 afirmaciones. Las
contradicciones históricas **S08/UBIGEO y T02/HORA** siguen en la matriz 84-I,
basadas en el contraste con el CSV histórico. No se representaron como una
lectura actual del CSV ni se fabricó evidencia CSV en este expediente.
La prueba de contradicción genuina usa exclusivamente objetos sintéticos.

## C. Diagnósticos de aptitud realmente obtenidos

Se evaluaron las siete OperacionUso sobre cada afirmación por separado:
**12 × 7 = 84 resultados**. Se añadieron una consulta conjunta de las 12 y
una propuesta de equivalencia editorial K09/K10: **86 resultados**, no 86
afirmaciones ni tests nuevos. Cada llamada se repitió comparando igualdad del
resultado y selección invertida; esas repeticiones no se suman al contador.

| Operación propuesta | Evaluaciones | Requisitos satisfechos | Bloqueadas | Ejecuciones autorizadas o realizadas |
|---|---:|---:|---:|---:|
| Consulta documental individual y conjunta | 13 | 13 | 0 | 0 |
| Conversión temporal | 12 | 0 | 12 | 0 |
| Asignación espacial | 12 | 0 | 12 | 0 |
| Interpretación de variable | 12 | 0 | 12 | 0 |
| Equivalencia editorial individual y par PP | 13 | 0 | 13 | 0 |
| Acreditación de calidad | 12 | 0 | 12 | 0 |
| Redistribución | 12 | 0 | 12 | 0 |
| Total | **86** | **13** | **73** | **0** |

Los siete diagnósticos por afirmación verifican que los bloqueos sobreviven
también a propuestas irrelevantes para su tema: no se pretende que todas las
operaciones tengan significado científico sobre una fecha o título. Son pruebas
de las barreras, no un análisis meteorológico. Consulta sin bloqueo técnico
permite describir/comparar manualmente el contenido y preparar preguntas,
manteniendo advertencias de vigencia/restricciones. No es licencia de ejecución,
redistribución o inferencia.

Bloqueos comunes no consultivos: `identidad_institucional_no_acreditada`,
`edicion_o_correspondencia_no_acreditada`, `vigencia_no_acreditada`,
`falta.aplicabilidad_al_producto` y las cuatro restricciones comunes. Se añaden
corroboración y los requisitos del uso. Ejemplos obtenidos:

- K11/tiempo: `falta.convencion_temporal`, restricción temporal y falta de
  validación científica; no se asignó zona horaria.
- K12/espacio: `falta.identidad_espacial`, `falta.referencia_espacial` y falta
  de validación científica; no se asignaron códigos, CRS o coordenadas.
- K07–K10/interpretación: `falta.significado_variable`, `falta.unidad_aplicable`
  y `falta.validacion_cientifica`; una unidad literal no es una unidad acreditada.
- K06/calidad: `falta.validacion_cientifica`; «validados» sigue siendo declaración.
- K04/redistribución: `falta.derechos_para_el_uso`; la licencia nombrada no acredita
  términos, edición, cobertura o permiso aplicable.
- K09/K10/equivalencia: `productos_o_ediciones_no_correspondientes` y
  `equivalencia_sin_comparacion_explicita`; no hay relación de coincidencia ni
  objetivo de producto/edición acreditados. Este código expresa falta de prueba,
  no demuestra que pertenezcan a productos distintos.

Todos los resultados incluyen trazas **fuente@SHA#localizador**, aviso de
clasificaciones aportadas no autenticadas y carácter experimental. Conservan
**ejecucion_autorizada=False** y **operacion_ejecutada=False**, aunque los
requisitos documentales de consulta sean True. No se usó bool(resultado)
como permiso ni se activó un ejecutor.

## Correspondencia editorial, brechas y límites

Hay atribución y producto nominal compatibles en los antecedentes, no una
autenticación institucional independiente. No se demostró la misma edición
X–D–CSV, aplicabilidad por período, integridad científica, controles QC o
derechos. La versión declarada 1.0 no se asigna al CSV ni al diccionario.
No se usan fechas técnicas OOXML o AppVersion como edición o vigencia.

La insuficiencia espacial se expresa como restricción de K12 y falta de
constataciones; este conjunto no incluye una afirmación sobre coordenadas.
La convención horaria desconocida y las ediciones no acreditadas son
incertidumbres/restricciones, no falsas citas positivas del emisor. No se
crearon afirmaciones AUSENTE o NULO_DECLARADO reales: las vacías del archivo
y el silencio sobre una política no justifican un nulo institucional.

Límites del contrato: una referencia por afirmación; no hay modelo de párrafo
compuesto de varias ubicaciones no contiguas o de una búsqueda negativa
multidocumento. La fecha de actualización quedó en A como comprobación
adicional, separada de K02. No se inventó un localizador para agruparlo todo.
No se calculó vigencia ni se integró el expediente al catálogo.

Se conserva exactamente la matriz histórica de **29 IDs**:
**2 resueltas documentalmente, 17 parciales, 8 pendientes, 2 contradicciones,
0 no evaluables y 27 abiertas**. R02 conserva su cierre específico de lectura;
R04/R05/V04/V07 siguen parciales. El piloto no modifica sus estados.

Sin CSV, RAW, staging o SQLite operativos; sin conexiones, GET, descargas,
hipervínculos abiertos, Word/Excel, instalaciones, migraciones, commits o push.
No se realizó conversión de unidades/zonas, reconstrucción de HORA/UBIGEO,
asignación espacial, análisis climático o QA/QC científico. No se atribuye a
esta sesión una nueva huella de los almacenes que se mantuvieron cerrados.

**APTO CON RESTRICCIONES** para revisar el ensayo documental y su trazabilidad.
Antes de cualquier uso científico/jurídico u operativo siguen siendo necesarios
autenticidad, edición y aplicabilidad, controles independientes y derechos
documentados, además de autorización expresa para la operación. No se avanza
a otra etapa.
