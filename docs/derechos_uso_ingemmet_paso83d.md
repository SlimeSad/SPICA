# PASO 83-D: derechos de uso y aclaraciones para INGEMMET

## 1. Naturaleza y procedencia de la revisión

Auditoría documental offline de **2026-11-04**, no dictamen jurídico ni
autorización institucional. Producto objetivo: Mapa Geológico Integrado del Perú
a escala 1:50.000; servicio `SERV_GEOLOGIA_50K_INTEGRADA`, capa `7 — Litologia`.
La disponibilidad pública, un anuncio de Query o una respuesta técnica correcta
no se convierten automáticamente en derechos de conservación o redistribución.

La [auditoría de alternativas](alternativas_adquisicion_ingemmet_paso83d.md)
define D83D-01 a D83D-05. Se conservan los niveles de evidencia anteriores:

- D83D-02 identifica la [página de licencia GEOCATMIN](https://geocatminapp.ingemmet.gob.pe/complementos/Descargas/Licencia.html).
  El encargo refiere un texto relacionado con uso y obras derivadas, con
  reconocimiento de INGEMMET. Es un indicio documental aportado; no se aportó
  aquí un texto íntegro con cláusulas, versión/fecha y alcance comprobados.
- D83D-03 identifica la [Carta Geológica Nacional](https://portal.ingemmet.gob.pe/web/guest/carta-geologica-nacional)
  y el anuncio aportado de ciertos mapas Shapefile. No establece la licencia o
  identidad de un archivo del producto integrado exacto.
- E-06, reflejada en documentos locales D83D-04, registra metadatos históricos
  de capa. El informe mantiene licencia/atribución pendientes y
  `copyrightText` vacío; vacío no significa dominio público ni prohibición.
- Las autorizaciones históricas del usuario para metadatos no cubren una nueva
  consulta de entidades. Las pruebas sintéticas del 83-C no conceden derechos.

No se consulta ninguna de esas páginas ni se reabre evidencia institucional.
No se cita texto literal de una licencia no leída. Su vigencia, autoridad y
aplicabilidad específica siguen pendientes; tampoco se afirma que no haya permiso.

## 2. Matriz de operaciones y permisos

Los estados describen qué puede sostener SPICA con este expediente. Un estado
pendiente no es una prohibición institucional y tampoco es un permiso implícito.

| Operación | Evidencia disponible | Límite de esa evidencia | Estado y condición previa |
|---|---|---|---|
| 1. Consulta pública | Accesos históricos puntuales a metadatos documentados en E-04/E-05/E-06 | No prueban acceso vigente ni autorizan otras rutas/entidades | Acceso histórico acreditado en su alcance; nueva operación pendiente de revisión y autorización |
| 2. Consulta automática de atributos | Query anunciado y OID documentado; referencia Esri y candidato sintético | Capacidad técnica no acredita permiso, cuotas ni aceptación de parámetros | Pendiente para capa 7: términos de automatización, límites, alcance y autorización del ensayo |
| 3. Descarga de geometrías | Polygon anunciado; D83D-03 refiere archivos de determinados mapas | No vincula geometrías concretas con producto/edición ni establece derechos aplicables | Pendiente; expresamente fuera del microensayo sin geometría |
| 4. Conservación local | Uso/obras derivadas referido en D83D-02 y retención histórica de metadatos bajo alcances específicos | No determina condiciones de archivo local, plazo, acceso o copia de entidades | Pendiente de cláusulas y retención autorizada para el recurso exacto |
| 5. Uso en investigación | Indicio general sobre uso en D83D-02 | No hay cláusula verificada específica de investigación, usos admitidos o exclusiones | Pendiente; finalidad científica/académica no sustituye permiso aplicable |
| 6. Transformación de información | Indicio referido sobre obras derivadas en D83D-02 | No delimita reproyección, recorte, unión, conversión o modificación de atributos | Pendiente de alcance y obligaciones; ninguna transformación se ejecuta aquí |
| 7. Elaboración de mapas derivados | Indicio sobre obras derivadas y reconocimiento en D83D-02 | No acredita modalidad, publicación, escala, avisos ni atribución exigida para esta capa | Pendiente de texto aplicable y condiciones de presentación |
| 8. Redistribución de archivos originales | Archivo exacto y permiso específico no identificados | Acceso/descarga o autorización para derivados no implican redistribución de originales | Pendiente de autorización o cláusula aplicable explícita |
| 9. Redistribución de productos derivados | Indicio referido sobre derivados en D83D-02 | Elaborar no equivale a redistribuir; desconocidos medios, públicos y restricciones | Pendiente de alcance, condiciones y obligaciones aplicables |
| 10. Requisitos de atribución | El encargo refiere reconocimiento de INGEMMET | Se desconoce fórmula exigida, editores/autores, edición, URL, avisos y ubicación | Reconocimiento referido, contenido exacto pendiente; no inventar una fórmula presentada como oficial |

No se marca una licencia abierta, permiso de redistribución, versión jurídica o
fecha de comprobación del servidor. Los campos desconocidos seguirían `None` en
contratos que los admiten; no se llena una aprobación mediante texto libre.

## 3. Evidencia necesaria para cerrar permisos

Solicitar o incorporar por una vía posteriormente autorizada el documento
íntegro aplicable, emisor y autoridad, versión/fecha y vigencia, su vínculo con
producto/servicio/capa/distribución, operaciones admitidas y excluidas, obligaciones
de atribución/avisos, restricciones y posibles condiciones de terceros.

Si no es posible determinar ese alcance, se necesita aclaración institucional
por un canal oficial verificado. La ausencia de respuesta no concede permiso.
No se fabrica contacto, aceptación de términos o autorización por silencio.
Permiso operativo del usuario, fundamento de uso institucional, capacidad técnica
y validez científica son decisiones distintas.

Antes de autorizar un futuro piloto bastaría resolver los derechos propios de
ese alcance mínimo (consulta automática de un atributo y conservación privada de
su evidencia), junto con los bloqueos técnicos. No se presenta la resolución de
geometrías, derivados o redistribución como requisito de un uso que no los realiza;
estos seguirían pendientes y prohibidos por el alcance del piloto.

## 4. Aclaraciones propuestas, no enviadas

**Borrador para revisión humana. No se enviaron mensajes ni solicitudes.** No
se inventa destinatario, dirección de correo, contacto o canal institucional.
Se pide documentación o una respuesta institucional atribuible, no datos reales
de entidades ni un GET preliminar para descubrir identificadores.

| ID | Pregunta precisa | Decisión que permitiría resolver |
|---|---|---|
| Q-01 | ¿Cuál es la identificación oficial, edición y fecha del Mapa Geológico Integrado 1:50.000, y cómo se vincula con `SERV_GEOLOGIA_50K_INTEGRADA`, capa `7 — Litologia`? | Identidad del producto y publicación, sin confundir versión de ArcGIS con edición geológica |
| Q-02 | ¿Existe un archivo GIS oficial de esa misma edición/capa? Solicitar referencia oficial de distribución, formato y constancia de correspondencia; si no es equivalente, identificar diferencias | Selección entre archivo y REST sin sustituir productos |
| Q-03 | ¿Qué cobertura, hojas, fechas y vacíos incluye cada distribución y la capa integrada? ¿Hay manifiesto de componentes y criterio institucional de completitud? | Alcance espacial/temporal e integridad de conjunto |
| Q-04 | ¿Qué texto de licencia/términos, versión y fecha se aplica al servicio, capa y archivo? ¿La página GEOCATMIN indicada es aplicable y vigente? | Fundamento y ámbito documental del uso |
| Q-05 | ¿Se permite la consulta automática no autenticada de un atributo y la conservación privada de su respuesta? ¿Qué cuotas, horarios o límites rigen? | Derechos y condiciones del microensayo |
| Q-06 | ¿Cuáles son los términos para descargar geometrías/archivos, conservarlos localmente y utilizarlos en investigación, incluidas restricciones de terceros? | Uso local futuro, separado del piloto actual |
| Q-07 | ¿Se permiten transformaciones y mapas derivados? ¿Qué límites y avisos se exigen? | Diseño de procesamiento y productos derivados futuros |
| Q-08 | ¿Qué condiciones independientes rigen la redistribución de originales y la de derivados, y cuál es la atribución exacta exigida? | Publicación sin extrapolar permiso de consulta o creación |
| Q-09 | ¿Está documentada para esta capa la operación MapServer Query y la combinación exacta de siete parámetros de nuestro protocolo? ¿Respeta `resultRecordCount=1` con `resultOffset=0`, `where=1=1`, OID ordenado y geometría deshabilitada? | Correspondencia de ruta, orden y límite remoto de una entidad sin consulta previa |
| Q-10 | ¿Qué mecanismo documentado permite fijar edición/instantánea y evitar cambios durante una adquisición? ¿Son estables los OID al editar o republicar y existe una clave institucional persistente? | Consistencia multipágina e identidad, sin convertir OID en clave global |
| Q-11 | ¿Cuál es la definición autoritativa de los CRS de origen, representación y salida, datum, ejes y unidades? ¿Dónde están el diccionario de atributos/códigos, memoria y restricciones de precisión/escala? | Interpretación espacial y científica posterior |
| Q-12 | ¿Qué historial de cambios, fechas/ediciones, manifiestos y verificadores de integridad publica la institución? ¿Cómo distingue reemplazos de archivo y revisiones de contenido? | Readquisición verificable, sin inferir edición por ETag/hash |

Q-09 se limita a pedir aclaración documental. No propone activar red, inventar
un OID, ejecutar `returnIdsOnly` ni flexibilizar el máximo de una entidad.
Una respuesta insuficiente mantiene el bloqueo; cambios de alcance requerirían
otra revisión y autorización.

## 5. Dictamen documental

**APTO CON RESTRICCIONES para revisión.** Existe un indicio aportado de términos
sobre uso/derivados y reconocimiento, pero su aplicación a la capa y a cada
operación no está demostrada. No se aprueba adquisición ni reutilización.
El [protocolo del piloto](protocolo_piloto_arcgis_paso83d.md) conserva la autorización
pendiente y las barreras del PASO 83-C; este documento no las sustituye.

## 6. Continuidad documental del PASO 83-E

El [expediente de consulta y seguimiento](consulta_institucional_ingemmet_paso83e.md)
conserva Q-01 a Q-12 agrupadas en seis consultas y añade el destinatario propuesto
aportado por el usuario, Dirección de Geología Regional. Es borrador no enviado;
el contacto no ha sido validado independientemente y no hay respuestas registradas.

La [matriz de fuentes por servidor](fuentes_oficiales_ingemmet_paso83e.md)
no altera la evaluación de permisos: la vigencia y aplicación de la licencia a
cada host, producto, capa y distribución siguen pendientes, incluida redistribución
y atribución. No se extiende un permiso por compartir servicio o publicador.
La preparación de la consulta no autoriza envío ni adquisición.
