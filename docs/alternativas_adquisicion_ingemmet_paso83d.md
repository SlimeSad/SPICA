# PASO 83-D: alternativas de adquisición geoespacial de INGEMMET

## 1. Alcance, estado y decisión

Fecha de auditoría local: **2026-11-04**. Dictamen: **APTO CON RESTRICCIONES para
revisión documental**. No se autoriza ni ejecuta adquisición institucional.

Git comenzó limpio en `feature/suadc-http`, HEAD **`4e49a61`**,
`SUADC: simulacion segura de piloto vectorial ArcGIS`: PASO 83-C registrado.
Se conservan contratos, pruebas y decisiones anteriores. No se identificó en
esta revisión documental un defecto concreto y reproducible que requiera código.

**No se selecciona una vía operativa prioritaria con la evidencia disponible.**
REST tiene mayor preparación local para revisar un microensayo de atributos,
pero sus parámetros no se han probado en el servidor y falta justificar el
máximo remoto de una entidad. La distribución GIS sería una candidata a evaluar
para una base local reproducible **si** se acredita un archivo oficial del
producto/edición/cobertura exactos; ese archivo todavía no está identificado.
No se sustituye el producto integrado por hojas de otro producto.

Entregables relacionados:

- A: matriz comparativa y decisión, en este documento.
- B y D: [derechos y aclaraciones para INGEMMET](derechos_uso_ingemmet_paso83d.md).
- C: [protocolo revisado del primer piloto](protocolo_piloto_arcgis_paso83d.md).

## 2. Evidencia disponible y límites de verificación

Las páginas oficiales siguientes son **referencias identificadas**, no fuentes
consultadas en este paso. No se verifican actualidad, respuesta HTTP, redirecciones
ni texto completo. Toda comprobación externa necesaria queda pendiente. Los
hallazgos locales se respaldan en documentos versionados, sin reabrir evidencia
institucional del PASO 82-C ni almacenamiento operativo.

| ID de esta auditoría | Referencia y evidencia disponible | Estado y límite |
|---|---|---|
| D83D-01 | Encargo del PASO 83-D: [Query de capa MapServer, Esri](https://developers.arcgis.com/rest/services-reference/enterprise/query-map-service-layer/) | El encargo identifica funciones de selección, geometría y paginación; no se leyó el texto íntegro ni su versión. No acredita soporte específico en INGEMMET |
| D83D-02 | Encargo y protocolo anterior: [licencia GEOCATMIN](https://geocatminapp.ingemmet.gob.pe/complementos/Descargas/Licencia.html) | El encargo refiere un texto sobre uso, obras derivadas y reconocimiento de INGEMMET; no se dispone aquí de cláusulas verificadas, fecha/versión o vínculo con capa 7 |
| D83D-03 | Encargo: [Carta Geológica Nacional](https://portal.ingemmet.gob.pe/web/guest/carta-geologica-nacional) | Informa, según la referencia aportada, de determinadas descargas Shapefile desde GEOCATMIN. No identifica un archivo del Mapa Geológico Integrado exacto |
| D83D-04 | [Expediente](expediente_ingemmet_geologia_50k.md), [matriz GIS, sección 10](matriz_interoperabilidad_ingemmet.md#10-diagnóstico-y-validación-offline-del-paso-82-d) e [informe local, sección 25](validacion_metadatos_ingemmet_paso82.md#25-resultado-final-offline-y-metadatos-esenciales-reales) | E-01 identifica externamente el producto; E-06 registra inspección histórica de metadatos de capa, no consultas de entidades. No es una nueva verificación del servidor |
| D83D-05 | [Arquitectura vectorial](adquisicion_vectorial_offline.md), [auditoría 83-B](auditoria_vectorial_paso83b.md), [protocolo 83-B](protocolo_piloto_arcgis_paso83b.md), [simulación 83-C](simulacion_piloto_arcgis_paso83c.md) y sus módulos | Contratos y controles sintéticos revisados estáticamente; pruebas históricas, no ejercicio institucional |

Los IDs D83D-* identifican entradas de este informe; no son registros nuevos de
catálogo, adquisiciones, activos o evidencias primarias. No se inventa hash de
las páginas, fecha de consulta externa, licencia o revisión documental numérica.

### Metadatos históricos relevantes

E-06, evaluación final offline de **2026-10-30T20:43:25.499524Z**, registra para
la capa `7`, nombre literal `Litologia`, tipo `Feature Layer`:

- `geometryType=esriGeometryPolygon`, 39 descriptores y un único campo OID
  `objectid` de tipo `esriFieldTypeOID`.
- `maxRecordCount=2000`, `supportedQueryFormats="JSON, geoJSON, PBF"`,
  `capabilities="Map,Query,Data"` y
  `advancedQueryCapabilities.supportsPagination=true` **anunciados**.
- `currentVersion=11.2`: versión técnica declarada; no edición geológica.
- CRS de origen declarado `4326 / 4326`; CRS de extensión `102100 / 3857`.
  Son ámbitos distintos; ninguno acredita por sí solo el CRS de una consulta
  futura. No se completan datum, ejes, unidades o transformaciones desconocidos.

El informe no acredita `supportsOrderBy` ni estabilidad de publicación/OID para
el piloto; no se infiere que el servidor carezca de ellos. El contraste completo
servicio/capa permanece `None` por falta del primario histórico del servicio.
Las declaraciones de metadatos no son prueba de parámetros, paginación efectiva,
completitud o derechos. El estado actual de la publicación es desconocido.

## 3. Correspondencia entre productos

| Elemento | Identificado | No acreditado |
|---|---|---|
| Producto objetivo | Mapa Geológico Integrado del Perú a escala 1:50.000, según E-01 | Edición, fecha, cobertura efectiva, continuidad, precisión y composición de hojas |
| Servicio/capa objetivo | `SERV_GEOLOGIA_50K_INTEGRADA`, `7 — Litologia` | Correspondencia vigente entre publicación, servicio y una distribución de archivo |
| Carta Geológica Nacional / descargas referidas | Anuncio externo de determinados mapas Shapefile en D83D-03 | Que sean la misma integración, los mismos atributos, geometrías, edición o cobertura de capa 7 |
| Archivo GIS del producto exacto | Ninguno identificado en el material revisado | URL oficial de distribución, recurso, formato concreto, paquete, versión, CRS y licencia aplicable |

Nombre parecido, escala común, institución y acceso desde GEOCATMIN no demuestran
equivalencia. La extensión de metadatos no prueba cobertura exhaustiva. Un
Shapefile referido no se registra como copia de la capa ni como revisión de su
recurso sin un vínculo documental explícito. Si es otro producto, deberá mantener
identidad/procedencia propias en una integración futura autorizada.

## 4. Matriz comparativa

Riesgos y costos siguientes son **evaluaciones de arquitectura**, no fallos
observados del servidor ni mediciones de rendimiento.

| Criterio | A. ArcGIS REST de la capa objetivo | B. Archivo GIS oficial del producto exacto, todavía no identificado |
|---|---|---|
| Producto | Servicio/capa concretos identificados históricamente | Debe acreditarse equivalencia; el anuncio de Carta Geológica Nacional no basta |
| Evidencia oficial | Metadatos históricos resumidos en E-06 y referencia Esri aportada | Anuncio aportado de descargas de determinados mapas, sin distribución exacta acreditada |
| Mecanismo | GET candidato de atributos; geometrías/colecciones serían otro alcance | Descarga HTTP directa únicamente si hay URL oficial acreditada; entrega manual documentada si corresponde. Portal interactivo no equivale a API |
| Atributos y geometrías | Microensayo: solo `objectid`, geometría prohibida. Geometría futura exige contrato y permisos separados | Conservar paquete entregado; atributos, componentes y geometrías concretos aún desconocidos |
| Compatibilidad SPICA | Lector acotado, OID exacto, FeatureSet Polygon XY y coordinación de páginas, todos sintéticos; sin adaptador institucional operativo | HTTP streaming, evidencia, ingesta manual y RAW genérico reutilizables tras autorización; sin lector/validador GIS de archivos específico acreditado |
| Restricciones | Un GET futuro, 64 KiB, sin geometría/reintentos/redirecciones/autenticación; origen y TLS controlados; ningún acceso actual | No descargar ni inventar URL. Fijar tamaño, espacio, formato y política antes de adquirir; no aplicar por analogía el límite del microensayo |
| Riesgo de incompletitud | Una página, conteo o flag de límite no prueban conjunto completo; incluso IDs coincidentes no garantizan atributos/geometrías de una instantánea | Archivo íntegro no prueba cobertura geológica completa; requiere alcance y manifiesto institucional. Evita coordinación entre páginas solo si existe una distribución coherente acreditada |
| Riesgo de cambio de versión | Ediciones entre páginas, OID reutilizados o republicación; orden estable no acredita instantánea | URL o archivo pueden sustituirse; sin edición/manifiesto no se conoce equivalencia. No se presume inmutabilidad de la distribución |
| Paginación y transferencia | Soporte anunciado, no ejercido; `maxRecordCount=2000` no es total ni prueba del límite solicitado de una fila | No requiere paginar entidades si hay un paquete único, pero se desconoce su forma y tamaño reales |
| CRS | Conservar declaración de respuesta y distinguir origen/extensión/salida; no reproyectar ni elegir CRS por analogía | Solicitar definición y componentes entregados; no inferir CRS por nombre, coordenadas o extensión |
| Bytes e historial | Conservar cada cuerpo primario y solicitud exacta antes de interpretar; el coordinador actual retiene recibos, no archivo durable de todas las páginas | Conservar bytes originales del paquete, documentos/manifiesto y procedencia; extracción/reconstrucción serían derivados distintos |
| Facilidad de verificación | Sintaxis y esquema acotados disponibles; integridad física institucional, conjunto e instantánea todavía no preparados/probados | Hash/tamaño y lectura física comunes serían reutilizables; inventario, estructura GIS, CRS y cobertura siguen pendientes |
| Readquisición / cambios | Mismo query puede producir otros bytes sin nueva edición; diferenciar cambio de representación, contenido e identidad | Hash nuevo acredita cambio de bytes, no causa ni edición; ETag/Last-Modified serían indicios si existen, nunca versión científica automática |
| Mantenimiento | Gestión de API, esquema, límites, precisión, páginas y consistencia remota; controles propios aún por integrar | Gestión de publicación, paquete/componentes, versiones y validación del formato; no hay garantía de menor costo global |
| Condiciones de uso | Consulta automatizada, conservación y reutilización pendientes de alcance aplicable | Descarga, conservación, uso y redistribución pendientes para el archivo exacto |
| Documentación faltante | Endpoint/capacidades vigentes, orden/límite, edición/instantánea, diccionario, derechos y autorización | Distribución exacta, identidad, versión/fecha, cobertura, CRS, diccionario, manifiesto/integridad y derechos |
| Recomendación | Mantener como candidato de microensayo documentalmente condicionado; no adquirir una colección por extrapolación | Investigar primero existencia/correspondencia documental antes de elegirla para una base local; no sustituir producto |

### Reglas comunes de integridad y readquisición

Un hash calculado localmente acredita los bytes observados; no es firma del
editor, permiso de uso, completitud espacial o validación científica. Un hash
institucional publicado y autenticado permitiría otro contraste, pero aquí no
se conoce tal evidencia. Tampoco se han contrastado físicamente archivos GIS.

Para cualquier vía futura: mantener institución/producto/recurso/edición,
adquisición, objeto lógico, activo y SHA-256 separados; conservar eventos de
adquisición aunque compartan contenido. Un mismo hash no demuestra que dos
productos o licencias sean equivalentes; un hash distinto no demuestra una nueva
edición geológica. Cambios de empaquetado o serialización también cambian bytes.

El [motor de readquisición](readquisicion.md) solo recomienda con antecedentes
explícitos; no descubre URLs ni autoriza descargas. No se invoca en este paso.
No se abren catálogos para comprobar antecedentes.

## 5. Coexistencia futura sin duplicar infraestructura

Si los derechos y la finalidad justifican ambas vías, podrían coexistir:
un archivo oficial versionado para la base local y REST para consultas puntuales
o contrastes documentados. Es una opción de diseño, no una relación ya acreditada
entre archivos y capa. No se mezclan versiones ni se deduplica por OID global.

Se reutilizarían `ClienteHTTP`, streaming, políticas de origen/TLS/tamaño/errores,
evidencia documental, catálogo y el único almacenamiento RAW, después de otra
revisión y autorización. La [ingesta manual](ingesta_manual.md) documentaría una
entrega local legítima sin inventarle respuesta HTTP. Los componentes vectoriales
seguirían separados de transporte, persistencia y procesamiento científico.

Los verificadores [XLSX/CSV](verificacion_formatos.md) y el reconocimiento de ZIP
no equivalen a validar Shapefile u otro formato GIS. Antes de interpretar archivos
harían falta inventario de componentes, validación de estructura/CRS y tratamiento
acotado y seguro de contenedores; no se extraen archivos ni se añade esa función.
La preparación de una conservación RAW futura no habilita el adaptador HTTP→RAW
para el microensayo: ese piloto queda expresamente fuera del RAW operativo.

## 6. Hallazgos y condiciones de continuidad

| Hallazgo | Importancia | Acción requerida |
|---|---|---|
| Derechos sin alcance acreditado para capa/producto | Bloqueante para autorizar el uso propuesto | Obtener texto aplicable, versión y vinculación; separar operaciones de uso |
| `resultRecordCount=1` no demuestra límite remoto | Bloqueante para el piloto estricto actual | Documentar soporte aplicable y evaluar garantía razonable, sin consulta preliminar no autorizada |
| Archivo oficial del producto exacto no identificado | Bloqueante para elegir/ejecutar alternativa B | Acreditar distribución y correspondencia; desconocido no significa inexistente |
| Anuncio `supportsPagination=true` puede confundirse con prueba | Riesgo alto de sobreafirmación | Conservar su fecha/ámbito y estado anunciado; no convertirlo en completitud |
| Edición, cobertura, diccionario y CRS de salida pendientes | Bloqueante para integración científica posterior | Resolver separadamente del microensayo técnico |
| Evidencia institucional durable y adaptador REST no preparados | Bloqueante para ejecución | Revisión posterior del ejecutor y conservación privada, sin activar el simulador |

La lista precisa de aclaraciones y la matriz de diez operaciones de uso están
en la [auditoría de derechos](derechos_uso_ingemmet_paso83d.md). No se envía ninguna
consulta institucional. No se elige una alternativa para evitar estos bloqueos.

## 7. Verificación de este incremento

Solo se crean los tres documentos de este PASO 83-D; ningún archivo previo,
contrato, prueba, configuración o dependencia requiere modificación. Se ejecutaron
`git diff --check`, `git status --short` y
`git ls-files --others --exclude-standard`, más revisión de UTF-8, espacios,
tablas, enlaces locales/anclas y correspondencia entre documentos/parámetros.
Los enlaces externos se revisan como texto, sin solicitudes de red.

Resultado: `git diff --check` sin hallazgos; los tres archivos nuevos se comprobaron
por separado. Formato UTF-8 sin BOM, finales de archivo, tablas y bloques correctos;
**19 enlaces locales con sus anclas válidos**, **3 referencias externas revisadas
solo como texto**, y los **7 parámetros** coinciden con las constantes del contrato
83-C, contrastadas por lectura AST sin importar ni ejecutar SPICA. La comprobación
documental usó `.venv\Scripts\python.exe -B` por entrada estándar, con bloqueo de
sockets/SQLite/ruta operativa: cero intentos de esas operaciones. No es una prueba
unitaria nueva ni un ensayo del servicio.

**Pruebas nuevas: 0. No se ejecuta la suite ni pip check en esta etapa documental.**
Las **1331 aprobadas, 0 fallidas y 0 errores** corresponden al PASO 83-C,
según su informe versionado; no son resultados de una ejecución nueva del 83-D.
No se vuelve a abrir su log temporal para acreditarlos.

Git final contiene únicamente estos tres documentos nuevos, con la misma
rama `feature/suadc-http` y HEAD `4e49a61` iniciales:

```text
?? docs/alternativas_adquisicion_ingemmet_paso83d.md
?? docs/derechos_uso_ingemmet_paso83d.md
?? docs/protocolo_piloto_arcgis_paso83d.md
```

Se verifica por separado su contenido sin seguimiento porque
`git diff --check` por sí solo no los incluye. No hubo conexiones, descargas,
apertura de evidencia institucional, acceso a RAW/staging/SQLite operativos,
instalaciones, migraciones, activación QA/QC, commits o push. No se comparan hashes
operativos: eso requeriría abrir datos excluidos. Esta afirmación describe las
acciones de la auditoría, no certifica actividad de otros procesos.
