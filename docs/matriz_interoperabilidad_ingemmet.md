# PASO 81 — Matriz de interoperabilidad y requisitos GIS de INGEMMET

Ámbito: servicio `SERV_GEOLOGIA_50K_INTEGRADA`, capa `Litologia`, ID `7`.
Véanse el [expediente y sus evidencias E-01/E-02](expediente_ingemmet_geologia_50k.md)
y el [plan del PASO 82](plan_validacion_ingemmet_paso82.md).

**Actualización del PASO 82:** el servicio se leyó y validó; la transferencia HTTP
de capa terminó, pero su inspección se detuvo por complejidad JSON. Las secciones
1–6 conservan el balance histórico del PASO 81. El estado observado posterior,
con sus límites, figura en la [sección 7](#7-actualización-observada-en-el-paso-82).

## 1. Estados de evidencia

| Estado | Significado y alcance |
|---|---|
| Documentada por la fuente | Existe documento/respuesta primaria identificado y conservado con procedencia; no basta el relato externo. Aún no se asigna este estado a las propiedades remotas de INGEMMET |
| Identificada externamente, sin verificación local | Dato suministrado en E-01; no hay consulta ni respuesta conservada en SPICA |
| Comprobada en SPICA | Evidencia local concreta. Aquí se limita a inspección del código/documentación; la suite del PASO 80 es antecedente histórico, no prueba de INGEMMET |
| Pendiente de verificación | Información ausente, alcance incierto o comportamiento aún no probado |
| No disponible | Capacidad no implementada en SPICA, salvo evidencia explícita de otro ámbito. No equivale a que INGEMMET no la ofrezca |

Una propiedad declarada por un servidor y su funcionamiento probado son evidencias
distintas. Tras una futura consulta de metadatos podrían coexistir «documentada por
la fuente» para un anuncio y «pendiente» para su ejecución o completitud.

## 2. Viabilidad por capacidad

| Capacidad | Evidencia remota actual | Componente SPICA inspeccionado | Viabilidad / brecha |
|---|---|---|---|
| Referencias de servicio/capa | Identificada externamente: dos URLs, ID `7` | `Fuente`, `ProductoCatalogo`, `RecursoCatalogo`, procedencia | Reutilizables como contratos; no registrar capacidades verificadas ni capas operativas todavía |
| Descubrimiento de metadatos | Referencias identificadas; acceso, esquema y versión pendientes | `ClienteHTTP.get()` acotado | Transporte comprobable por código; falta validar semántica ArcGIS y HTTP 200 con error de aplicación |
| Tipo de geometría | Identificada externamente: `esriGeometryPolygon` | RAW conserva bytes opacos | Sin modelo ni validador GIS específico disponible en SPICA |
| CRS | Identificado externamente: `102100 / 3857` | `EstacionCatalogo.sistema_referencia` es texto opcional de una estación | No constituye un contrato de CRS/geométrico de capa; definición, datum/ejes/unidades pendientes |
| Escala | Identificada externamente: `1:50.000` | Descripción/procedencia documental genéricas | Faltan metadatos GIS tipados de escala, resolución e incertidumbre |
| Atributos | Ocho nombres aportados, lista no exhaustiva | Catálogo documental y referencias | Tipos, dominios, claves, nulos y diccionario pendientes; no son variables meteorológicas |
| Identidad de entidades | `objectid` identificado; estabilidad desconocida | Identidad lógica/adquisición/activo/contenido separados | Falta identidad por entidad y publicación, sin convertir OID en clave global |
| Consulta por capa | Capa `7` identificada; parámetros no probados | GET con query params públicos | Un GET genérico no es un ejecutor de consulta espacial |
| Filtros espaciales/atributos | Pendiente de verificación | Planificador científico trabaja estaciones/variables/tiempo | BBOX, predicados, geometrías de filtro, CRS y alcance no disponibles como contrato GIS |
| Paginación | Identificada externamente como capacidad | No hay paginador ArcGIS | Orden estable, cursores/offsets, fin, duplicados y cambios concurrentes pendientes |
| Límite por consulta | `MaxRecordCount=2000` identificado externamente | Límites de bytes y operaciones ya existentes | No confundir bytes, entidades por página y total; faltan límites de colección y completitud |
| JSON | Formato identificado externamente | Reconocimiento genérico de sintaxis JSON en inspector | No valida una capa, un conjunto de entidades ni su completitud |
| GeoJSON | Formato de consulta identificado externamente | Sin validador geoespacial específico disponible | Falta confirmar representación, CRS/ejes, esquema, geometrías y atributos concretos |
| PBF | Formato de consulta identificado externamente | Descarga de bytes opacos posible por transporte | Decodificación y validación PBF no disponibles; no instalar dependencias en este paso |
| Descarga vectorial completa | Pendiente de verificación | Streaming + RAW reutilizables para bytes | Falta contrato de colección/paquete y prueba de completitud; no basta un mapa visible |
| WFS/WMS/FeatureServer | Pendiente de verificación; no se aportaron referencias | Ningún conector de esos mecanismos | No derivar rutas ni afirmar indisponibilidad institucional |
| Derechos / autenticación | Pendiente de documentación | Restricciones declarativas y manejo HTTP de errores | No hay permiso inferible ni autenticación institucional implementada |
| Actualizaciones | Versión/fechas/frecuencia desconocidas | Motor de readquisición del PASO 80 | Puede evaluar evidencia explícita futura; no la obtiene ni realiza red |

## 3. Representación GIS requerida, todavía no implementada

Esta tabla es un **diseño documental**. No añade modelos ni modifica el catálogo.
Los nombres de conceptos no son campos institucionales comprobados.

| Requisito | Representación propuesta | Evidencia/validación necesaria |
|---|---|---|
| Geometrías originales | Bytes RAW exactos y, en una futura capa derivada, coordenadas, partes, anillos y atributos preservados | Especificación del formato efectivamente recibido; no reparar ni simplificar al adquirir |
| Coordenadas y datum | Objeto CRS de origen conservado, identificadores con namespace, definición/WKT si existe, ejes, unidades y dimensión | Definición autorizada; distinguir CRS anunciado de CRS de salida |
| Transformaciones | Derivado separado con origen/destino, operación, parámetros, versiones, recursos auxiliares, área de validez e incertidumbre | Justificación técnica y científica aprobada; no se ejecuta ahora |
| Escala | Escala de origen declarada y procedencia por capa/hoja | No convertirla en resolución o precisión por una fórmula arbitraria |
| Cobertura | Extensión declarada y extensión observada separadas, CRS, hojas incluidas, vacíos y alcance del filtro | No deducir cobertura nacional continua del título; no confundir vista actual con alcance del producto |
| Metadatos por capa | Institución, producto, servicio, capa, título, geometría declarada, campos, derechos, edición y fechas con evidencia | Instantánea primaria fechada y vinculada al evento; valores desconocidos explícitos |
| Atributos geológicos | Código/nombre original, tipo, nulabilidad, dominio, diccionario/versiones y procedencia | No traducir categorías ni inventar unidades, estaciones o semántica de códigos |
| Identidad de entidades | ID original contextualizado en servicio/capa/publicación e instantánea | Verificar OID/clave persistente y comportamiento al republicar; no usar nombre ni hash como identidad lógica |
| Versión | Etiqueta institucional opaca, revisión documental interna y fecha de consulta separadas | Una fecha de consulta, versión del software o hash local no es una edición geológica |
| Autoría | Institución productora, autores cartográficos, fuente por hoja y responsables de publicación cuando consten | No atribuir autoría científica por el nombre del host solamente |
| Incertidumbre posicional | Valor/método/ámbito documentados o desconocido | No estimar precisión por decimales, escala o tamaño del polígono |
| Limitaciones de escala | Uso previsto, generalización, contactos y ámbito de decisión | Evaluación por problema; no presentar resultados puntuales como certeza geológica |
| Historial | Recursos, páginas/paquetes y eventos separados con sus activos | Mantener adquisiciones legítimas de contenido idéntico, sin sobrescribir |
| Integridad física | Tamaño/hash observados y verificación física por el flujo aprobado | SHA-256 no demuestra autenticidad, validez geométrica ni completitud de colección |
| Derivados | Manifestación explícita de activos padres, método, parámetros, herramientas/versiones y evaluación de incertidumbre | Nueva identidad para el derivado; conservar original y relaciones de procedencia |

No se fuerza una capa dentro de `EstacionCatalogo`, `VariableCatalogo` ni
`SolicitudAdquisicion` inventando coordenadas de estación, unidades o fechas.
El planificador temporal actual no es un planificador espacial. El requisito GIS
se aprobará con evidencia concreta, sin rediseñar anticipadamente el núcleo.

## 4. Conservación y completitud de una futura adquisición

El transporte, almacenamiento y validación espacial resuelven problemas distintos:

1. **Transferencia:** cuerpo recibido dentro del límite, estado HTTP permitido,
   sin compresión/redirección incompatible y con recursos cerrados.
2. **Integridad física:** bytes persistidos, tamaño y SHA-256 contrastados.
3. **Estructura GIS:** formato, esquema, geometría/CRS y atributos reconocidos en
   un alcance delimitado; todavía no hay un verificador de este tipo.
4. **Completitud:** evidencia de que se obtuvo la colección o subconjunto
   solicitado, con límites, filtros, identidad de entidades y estado de publicación.
5. **Validez científica:** aplicabilidad, incertidumbre y significado para un
   problema ambiental; independiente de las cuatro anteriores.

Para una futura paginación se necesitará un plan autorizado y acotado: filtros
exactos, orden estable, identificadores, huella de publicación, tamaño de página,
presupuesto total de bytes/entidades/peticiones, criterio de fin y manifestación de
cada página. Deben detectarse páginas repetidas, IDs duplicados/ausentes, conteos
incompatibles y cambios entre páginas. Una página corta, un límite de 2.000 o la
ausencia de una bandera de truncamiento no prueban por sí solos que no falten datos.

No se implementan consultas de conteo o IDs ni se presupone que estén soportadas.
Si no hay evidencia suficiente de completitud, el resultado futuro deberá quedar
parcial o incierto, conservando las respuestas originales y el alcance efectivo.
No se confunde la suma de páginas con una instantánea coherente si hubo ediciones
concurrentes; harán falta garantías del servicio o una limitación explícita.

GeoJSON y JSON de ArcGIS no se tratan como representaciones idénticas ni se copia
automáticamente el CRS de la capa al archivo de salida. La referencia de salida,
orden de ejes y posibles cambios de representación requieren especificación y
comprobación. PBF sería inicialmente un original opaco, sin validación científica.

## 5. Seguridad y componentes reutilizables

| Control existente | Reutilización propuesta y límite |
|---|---|
| `ClienteHTTP` / `ConfiguracionHTTP` | Mantener un único cliente, origen explícito, TLS, timeouts, sin redirecciones/proxies del entorno; no ampliar orígenes en el PASO 81 |
| `PoliticaReintentos` | Reintentos solo GET recuperables dentro de política; el primer piloto de metadatos propone un intento por URL, sin reintentos |
| `get()` pequeño | Presupuesto de 1 MiB para metadatos del piloto; no usarlo para cargar colecciones grandes completas en RAM |
| `descargar()` | Streaming, conteo real y SHA-256 para futuras respuestas grandes autorizadas; no certifica entidades ni colección completa |
| `AlmacenRAW` | Publicación exclusiva, comprobación de contenido y deduplicación física sin perder activos; no sobrescribe originales |
| Límites RAW | No es inmutabilidad impuesta por el sistema operativo: siguen pendientes ACL/inmutabilidad, respaldo, durabilidad y coordinación multiproceso |
| Staging | Directorios controlados, temporales propios, limpieza acotada y estados inciertos explícitos; sin usar staging operativo ahora |
| Evidencia documental / catálogo | Conservar origen de cada afirmación y desconocidos, con historia; no inventar fecha de publicación, licencia o versión |
| `AdaptadorHTTPRAW` | Reutilizable para transferencia/incorporación futura; su inspector/utilidad documental actual se orienta a CSV/XLSX, no valida vectores ni certifica JSON geoespacial |
| Ingesta manual | Alternativa si se obtiene una entrega legítima documentada; no sustituye permisos ni acredita autoría por un nombre de archivo |
| Motor del PASO 80 | Recomendación pura con evidencia explícita, sin autorizar red ni afirmar vigencia por hash/URL |

HTTP 401/403, CAPTCHA, sesión o requisitos no previstos obligarán a detener el
piloto; no se intentarán credenciales ni vías alternativas. No se registrarán
tokens, cookies, cuerpos privados ni trazas indiscriminadas. Un error ArcGIS dentro
de HTTP 200 requiere validación semántica futura: el transporte genérico no basta.

No se inventa una segunda base GIS/RAW, un cliente nuevo ni un conector adaptando
SENAMHI por cambio de URL. Concurrencia secuencial, falta de atomicidad global y
límites de confianza actuales siguen vigentes.

## 6. Decisiones necesarias antes de avanzar

- Confirmar documentación primaria, términos de consulta y alcance de conservación
  de metadatos; separar acceso técnico y derechos de reutilización/redistribución.
- Aprobar el [piloto de metadatos](plan_validacion_ingemmet_paso82.md), presupuesto,
  rutas exactas, formato y conservación temporal de evidencia.
- Revisar definiciones GIS y un contrato espacial solo tras observar metadatos
  reales; mantener el producto como candidato, fuera del catálogo operativo.
- Antes de vectores, especificar paginación, límites y completitud, diccionario,
  CRS, publicación y verificación estructural independiente.

La viabilidad es **condicionada para un piloto de metadatos**, no demostrada para
adquisición vectorial. No se ha probado conexión ni funcionalidad institucional.

## 7. Actualización observada en el PASO 82

E-04: [informe del ensayo real](validacion_metadatos_ingemmet_paso82.md),
30 de octubre de 2026, entre `09:23:12.879413Z` y `09:23:15.625737Z`.
Exactamente dos GET con `f=json`, uno por ruta, ambos HTTP 200. No hubo consultas
de entidades. SHA-256 y resúmenes proceden de cuerpos recibidos completamente en
memoria; no se archivaron respuestas completas ni se verificaron archivos en disco.

| Capacidad/propiedad | Estado respaldado por E-04 | Límite pendiente |
|---|---|---|
| Acceso al servicio | Comprobada en SPICA: 3.663 bytes, JSON y esquema mínimos coherentes | Solo esa ruta/fecha; no disponibilidad futura ni autenticidad independiente |
| Referencia de capa | Comprobada en SPICA como anuncio del servicio: ID `7`, nombre `Litologia` | La respuesta de capa requiere revisión; no promueve sus campos a comprobados |
| Acceso HTTP a capa 7 | Comprobada en SPICA la transferencia de 983.697 bytes y HTTP 200 | `json_demasiados_elementos`; JSON/esquema de capa no validados |
| CRS del servicio | Documentado por respuesta de la fuente y observado localmente: `wkid=102100`, `latestWkid=3857`, unidades `esriMeters` | No confirma CRS de capa, datum/ejes, definición autoritativa o precisión |
| Extensión | `fullExtent` declarado del servicio, valores en E-04 | No prueba cobertura exhaustiva ni extensión de entidades/capa |
| MaxRecordCount | `2000`, documentado/observado en servicio | No es total de entidades; valor de capa pendiente |
| Formatos | Servicio anuncia `JSON, geoJSON, PBF` | Solo se ejerció lectura JSON de metadatos; no GeoJSON, PBF ni vectores |
| Capacidades | Servicio anuncia `Map,Query,Data` | No se ejercieron consultas de entidades, exportaciones o mapas |
| Paginación | El servicio examinado no anuncia `supportsPagination`; la identificación externa sobre capa sigue pendiente | No inferir falta de soporte ni probarla mediante nuevas peticiones |
| Geometría, atributos y OID | Identificación externa E-01, sin nueva verificación local de capa | Detención por complejidad antes del esquema; no rellenar desde fixtures |
| Inspector local | Implementación mínima de metadatos, 44 pruebas sintéticas; suite completa 1.105 aprobadas | No valida vectores; necesita revisión offline para metadatos de capa extensos |
| Versiones | `currentVersion=11.2`, `documentInfo.Version=3.2.0` observados | No son una edición geológica demostrada |
| Derechos/autoría | Campos examinados insuficientes; `copyrightText` y autor vacíos | Licencia, atribución y permisos de adquisición/redistribución desconocidos |

Estado final: **REQUIERE CORRECCIONES/revisión antes de validar capa o consultar
entidades**. El presupuesto de dos GET se agotó sin reintentos; no se ampliaron
límites. Se conserva la historia anterior, sin afirmar que todo INGEMMET carece
de capacidades ni atribuir completitud a una respuesta HTTP íntegra.

## 8. Corrección offline del PASO 82-B

Se conserva íntegramente la evidencia histórica E-04 de la sección 7. **No hay
nueva evidencia remota**: cero conexiones, cero GET y capa 7 todavía **PENDIENTE**.
Véase el [informe técnico y sus límites](validacion_metadatos_ingemmet_paso82.md#10-paso-82-b-recuperación-y-causa-comprobada).

El inspector local ahora separa sintaxis JSON completa, esquema esencial y
secciones sin evaluación semántica. Utiliza el parser estándar, presupuestos
estructurales y esenciales independientes, salida seleccionada y cancelación.
No duplica las secciones opcionales completas; no implementa parseo incremental.
El presupuesto estructural se justifica y mide con fixtures inventadas; **no**
se conoce si la respuesta institucional perdida cabe en él. El límite HTTP se
mantiene en 1 MiB y los controles globales no cambian.

El contraste servicio/capa requiere contexto validado del mismo objetivo. Las
pruebas sintéticas no confirman los ocho campos, geometría, CRS, ObjectID ni
paginación de INGEMMET; tampoco prueban estabilidad histórica de OID o completitud.
No se añaden conectores, consultas GIS, activos RAW o entradas del catálogo.

Una futura validación necesita revisión y autorización de **un solo GET de capa**,
sin repetir el servicio ni usar fixtures como evidencia institucional. Si no existe
contexto primario de servicio conservado, se dejará el contraste entre respuestas
sin comprobar. Condiciones y preservación de evidencia: sección 15 del informe.
