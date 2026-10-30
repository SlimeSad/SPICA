# PASO 82 — Ensayo de metadatos ArcGIS REST de INGEMMET

**Actualización offline del PASO 82-B:** véase la [sección 10](#10-paso-82-b-recuperación-y-causa-comprobada).
La capa real permanece **PENDIENTE**; no se hicieron nuevos GET. Las secciones
1–9 conservan la historia y el dictamen del ensayo anterior, sin sustituir evidencia
institucional por fixtures sintéticas.

**Dictamen histórico del PASO 82: REQUIERE CORRECCIONES antes de validar la capa o avanzar a entidades.**
La lectura del servicio fue coherente. La respuesta HTTP de capa llegó dentro del
límite de bytes, pero su validación se detuvo por el límite de complejidad JSON.
Se consumieron exactamente los dos GET autorizados; no se aumentaron límites ni
se realizaron nuevas consultas para completar los campos faltantes.

Referencias del trabajo: [expediente del PASO 81](expediente_ingemmet_geologia_50k.md),
[matriz actualizada](matriz_interoperabilidad_ingemmet.md#7-actualización-observada-en-el-paso-82)
y [plan previo](plan_validacion_ingemmet_paso82.md).

## 1. Estado inicial y arquitectura

Git inicial limpio, rama `feature/suadc-http`, HEAD `f168e57`:
`SPICA: expediente geoespacial INGEMMET y plan de validacion`.
Se inspeccionaron los tres documentos del PASO 81 y el transporte antes de escribir
código o realizar conexiones. No se modificó código estable ni la lista global de
orígenes; no se inicializó almacenamiento ni catálogo.

Se añade `adquisicion.inspeccion_arcgis`:

- `modelos.py`: objetivo explícito de servicio/capa y resultados técnicos inmutables.
- `inspector.py`: MIME, JSON acotado, esquema de metadatos, CRS declarado, nombres,
  campos, estados y errores de aplicación. No hace red ni escribe archivos.
- `ensayo.py`: usa exclusivamente `ClienteHTTP.get()` de SPICA. Solo admite una
  consulta por cada una de las dos rutas del objetivo y exige servicio coherente
  antes de consultar capa. Un fallo consume la ruta; no hay reintentos.
- `__init__.py`: API pública de inspección, sin conector de adquisición vectorial.

El objetivo valida rutas HTTPS MapServer de un mismo origen, sin credenciales,
fragmentos, consultas incrustadas ni métodos de entidades. En este ensayo se
utilizaron exclusivamente las rutas autorizadas de INGEMMET y `f=json`.

Cada petición utiliza una instancia nueva del **mismo cliente común**, con TLS
verificado, sin redirecciones y `trust_env=False`. No se implementó otro transporte.
La separación de instancias evita enviar cookies recibidas en una petición
anterior; no se proporcionaron cookies, credenciales ni autenticación.

Límites aplicados: 1.048.576 bytes por respuesta, lectura HTTP por bloques de hasta
65.536 bytes, un intento por ruta y timeouts de conexión/lectura/escritura/pool de
10/30/30/10 segundos. Estos timeouts no son un plazo total de la operación.
Se reutilizaron el rechazo de HTTP 206, compresión y redirecciones y los errores
seguros del transporte existente.

El inspector añade límites independientes: profundidad JSON 32, presupuesto
preliminar de 20.000 unidades —cadenas, contenedores y separadores— y recorrido
posterior de hasta 20.000 nodos. Rechaza claves duplicadas, números no finitos,
enteros excesivos y textos de más de 65.536 caracteres. El límite de bytes no
equivale a un límite exacto de memoria del árbol JSON.

## 2. Pruebas previas al acceso real

Se implementaron **44 pruebas sintéticas** con `httpx.MockTransport`, metadatos
inventados y memoria. Cubren servicio/capa coherentes, errores ArcGIS dentro de
HTTP 200, JSON/HTML/MIME inesperados, identidad, geometría/CRS, campos/tipos,
MaxRecordCount, paginación declarada/ausente, tamaño y Content-Length, TLS,
conexión, timeout, redirecciones, HTTP 206, compresión, cancelación antes/durante
lectura y entre peticiones, ausencia de cookies reutilizadas y falta de acceso
a RAW/SQLite. También comprueban determinismo e inmutabilidad del inspector.

Antes de cualquier GET real se ejecutó con Python **3.15.1** de `.venv`:

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -B -m pip check
```

Resultado: **1.105 aprobadas: 1.061 anteriores + 44 nuevas**, cero fallidas, errores
u omitidas; `unittest` informó **106.876 s**. Se compararon los IDs anteriores con
el registro del PASO 80: coinciden, sin IDs duplicados. `pip check`:
`No broken requirements found.` HTTPX **0.28.1**, SQLite **3.53.4**.
La guardia de pruebas registró cero accesos operativos y cero conexiones reales.
La suite pasó antes del ensayo; no se alteró el código para aceptar la respuesta
que luego excedió la complejidad admitida.

## 3. Conservación y preparación local

La carpeta temporal heredada mostró un permiso adicional al comprobar su ACL.
La preparación de un subdirectorio privado no pudo completarse/verificarse con
los permisos efectivos de ejecución. Se detuvo esa preparación: el registro y
la guardia confirman **0 DNS, 0 conexiones TCP y 0 GET** en ella. No se cambió la
ACL de directorios existentes ni se reintentó una petición HTTP.

Se optó por validar los cuerpos pequeños **solo en memoria**, modalidad compatible
con el límite autorizado. Se conservaron temporalmente únicamente códigos y
resúmenes técnicos filtrados fuera del repositorio. Un registro local de inicio
impidió reiniciar accidentalmente el ensayo, incluso ante una interrupción.

Los SHA-256 siguientes se calcularon sobre los bytes exactos devueltos al completar
`get()`. **No hubo archivo de respuesta releído ni verificación física de esos
cuerpos en disco.** Los cuerpos completos no se incorporaron a Git, RAW o SQLite.
El resumen no incluye cabeceras completas, cookies, mensajes privados o simbología.

## 4. Solicitudes reales y evidencia

| Dato | Servicio | Capa candidata 7 |
|---|---|---|
| Método | GET | GET |
| Inicio UTC local | `2026-10-30T09:23:12.879413Z` | `2026-10-30T09:23:13.927468Z` |
| Fin UTC local | `2026-10-30T09:23:13.919139Z` | `2026-10-30T09:23:15.625737Z` |
| Intentos GET | 1 | 1 |
| Estado HTTP | 200 | 200 |
| Content-Type | `application/json; charset=UTF-8` | `application/json; charset=UTF-8` |
| Content-Length expuesto | 3.663 bytes | No disponible |
| Bytes recibidos | **3.663** | **983.697** |
| Resultado de validación | `metadatos_coherentes` | `revision_necesaria` |
| Diagnóstico | Sin error de esquema en el alcance comprobado | `json_demasiados_elementos` |

URLs exactas ejercidas:

- [GET del servicio](https://geocatminnube.ingemmet.gob.pe/arcgis/rest/services/SERV_GEOLOGIA_50K_INTEGRADA/MapServer?f=json).
- [GET de capa 7](https://geocatminnube.ingemmet.gob.pe/arcgis/rest/services/SERV_GEOLOGIA_50K_INTEGRADA/MapServer/7?f=json).

SHA-256 del cuerpo HTTP del servicio, calculado en memoria:

```text
3235d31d1fcec71d11d92c8add2655a42ac9fdb3c425ac6d3e219cdc73c76a95
```

SHA-256 del cuerpo HTTP de capa, calculado en memoria:

```text
21f85c366686bcfe08a102abf775e0edc05de1fe30f567a73ec98cbf3aa80e39
```

Total recibido: **987.360 bytes**. La guardia de ejecución observó **2 resoluciones
DNS y 2 conexiones TCP**, exclusivamente hacia el host autorizado por HTTPS;
cero intentos bloqueados de acceso operativo o red ajena. Las dos rutas, métodos,
parámetros y conteos de aplicación proceden además del registro del ensayo.
Los instantes son mediciones locales UTC de la operación, no fechas del servidor.

La capa terminó sin error de transferencia detectable por el cliente. Su hash
describe el cuerpo HTTP recibido hasta fin normal del flujo; **no demuestra que
sea JSON válido, una capa verificada ni una colección completa**. Al detenerse el
control preliminar de complejidad, no se ejecutaron sus validaciones de esquema.
No se atribuye el exceso a una sección concreta: no se comprobó si fue simbología
u otro componente de esos metadatos.

## 5. Metadatos observados del servicio

| Propiedad recibida | Valor / alcance |
|---|---|
| Ruta del servicio | `SERV_GEOLOGIA_50K_INTEGRADA/MapServer` |
| `mapName` | `_SERV_GEOLOGIA_50K_INTEGRADA` |
| `serviceName` | No expuesto en el resumen validado; la identidad se vinculó a ruta y capas, sin tratar `mapName` como ID institucional |
| `currentVersion` | `11.2`; versión técnica declarada, no edición cartográfica demostrada |
| `units` | `esriMeters`, declaración del servicio |
| `maxRecordCount` | `2000`, límite anunciado, no total de entidades |
| `supportedQueryFormats` | `JSON, geoJSON, PBF`, respetando la forma recibida |
| `capabilities` | `Map,Query,Data`, solo anuncio; se ejerció lectura de metadatos |
| `supportsPagination` | No anunciado en los metadatos del servicio examinados; no se infiere `False` ni falta de soporte de la capa |
| `minScale` / `maxScale` | `0` / `0`; no se convierten en escala de origen o precisión |
| `copyrightText` | Cadena vacía |
| `documentInfo.Title` | `Untitled.aprx` |
| `documentInfo.Author` | Cadena vacía |
| `documentInfo.Version` | `3.2.0`; no se interpreta como versión del producto geológico |

Capas anunciadas, sin consultar sus entidades ni rutas adicionales:

| ID | Nombre recibido |
|---|---|
| 0 | `Punto de observacion` |
| 1 | `Estructura Volcanica Point` |
| 2 | `Fallas` |
| 3 | `Pliegues` |
| 4 | `Estructura Volcanica Line` |
| 5 | `Dique` |
| 6 | `Geoformas` |
| 7 | `Litologia` |

El ID `7` y nombre `Litologia` están confirmados como **anuncio del servicio**.
No sustituyen la validación independiente de la respuesta de capa que quedó
pendiente. No se presupone una identidad estable de entidades o publicaciones.

## 6. Referencia espacial y extensión observadas

El objeto `spatialReference` del **servicio** declara exactamente:

- `wkid = 102100`.
- `latestWkid = 3857`.
- Unidades del servicio: `esriMeters`.

Su `fullExtent` declara:

| Propiedad | Valor recibido |
|---|---|
| `xmin` | `-9072538.49965179` |
| `ymin` | `-2078636.9217961072` |
| `xmax` | `-7661750.568505581` |
| `ymax` | `-331952.0320098707` |

El objeto espacial de esa extensión declara también `wkid=102100`,
`latestWkid=3857`. Otros valores presentes incluyen `xyTolerance=0.001`,
`zTolerance=0.001`, `mTolerance=0.001` y `xyUnits=10000`; son parámetros declarados
del objeto, **no una precisión posicional ni resolución científica acreditadas**.
La extensión inicial de visualización se mantuvo distinta de `fullExtent`.

No se asignó un datum o orden de ejes no contrastado, no se interpretó el código
102100 como `EPSG:102100` ni se hizo una verificación independiente de definiciones
CRS. No se convirtieron coordenadas ni se reproyectaron geometrías. La extensión
de servicio no prueba cobertura exhaustiva ni extensión efectiva de la capa 7.

La escala nominal 1:50.000 sigue siendo información externa del PASO 81: no se
confirmó como precisión, resolución o edición de la cartografía mediante estos GET.

## 7. Campos y propiedades de capa pendientes

| Campo esperado según PASO 81 | Presencia/tipo comprobados en la respuesta de capa |
|---|---|
| `objectid` | Pendiente; no se verificó tipo OID ni estabilidad |
| `codi` | Pendiente |
| `codiunihoja` | Pendiente |
| `etiqueta` | Pendiente |
| `unidad` | Pendiente |
| `tipo_unidad` | Pendiente |
| `litologia` | Pendiente |
| `descrip` | Pendiente |

Tampoco se confirmaron localmente en ese cuerpo el ID/nombre, tipo de capa,
`esriGeometryPolygon`, CRS/extent, ObjectID, longitudes, dominios, MaxRecordCount,
formatos, capacidades avanzadas o edición. Se conserva la identificación externa
anterior como tal; no se completaron estos campos a partir de las fixtures.

## 8. Diferencias respecto del PASO 81 y acciones necesarias

Confirmado ahora, solo en el servicio: lectura puntual por SPICA, capa 7 anunciada,
par `wkid/latestWkid`, unidades, extensión y anuncios de formatos/límite. La
paginación de capa, geometría y ocho campos siguen sin verificación local.

La respuesta de capa es cercana al límite de 1 MiB y excede la complejidad JSON
admitida. Corregir/revisar offline la estrategia de inspección de metadatos extensos
antes de otro ensayo: por ejemplo, diseñar extracción acotada de propiedades
relevantes y descarte controlado de secciones no necesarias, con pruebas adversas.
No implementar ese cambio ni elevar automáticamente los límites para este acceso.
Los cuerpos solo existieron en memoria; este informe no permite reconstruirlos
desde sus hashes. Otra lectura del servidor necesitará nueva autorización.

La nueva estrategia deberá mantener contabilidad de bytes, complejidad, campos y
alcance, distinguir sección no inspeccionada de propiedad ausente y volver a pasar
la suite antes de la siguiente operación real. No será un conector vectorial ni
deberá habilitar paginación, filtros o métodos adicionales de forma implícita.

Derechos pendientes: licencia, atribución, consulta automatizada más amplia,
descarga y redistribución. Los campos examinados no aportaron una licencia ni
autoría suficiente; no se concluye que no existan condiciones en otras fuentes.
No se buscó otra página ni se derivaron WFS/WMS/FeatureServer. La disponibilidad
de dos respuestas públicas no constituye permiso de uso científico o masivo.

## 9. Cierre y límites

Se ejecutan `git diff --check` y `git status --short`, y se revisan por separado los
archivos nuevos: UTF-8, sintaxis Python, enlaces documentales y whitespace. Solo
se modifica la matriz del PASO 81 para añadir el estado respaldado por este ensayo;
los contratos y componentes anteriores permanecen intactos.

No hubo consultas a `/query`, `/export` ni a otras capas; no se descargaron
polígonos, imágenes renderizadas ni conjuntos vectoriales. No se crearon mapas,
cruces espaciales, estaciones derivadas, inferencias geoquímicas ni QA/QC científico.
No se accedió ni escribió en RAW, staging o SQLite operativos; la guardia no
registró intentos. No se verificó físicamente el almacén real para afirmarlo.

No hubo instalaciones, migraciones operativas, cambios de orígenes globales,
commits o push. Tras contrastar tiempos, URLs, tamaños y hashes con este informe,
se eliminaron los auxiliares temporales propios, incluidos scripts, registros y el
subdirectorio privado vacío. No quedaron residuos de ese directorio de ensayo;
no hubo borrado recursivo ni cambios de ACL de carpetas existentes. El resumen
reproducible se conserva aquí, sin cuerpos completos o archivos RAW.

El ensayo finaliza en revisión: no autoriza consultas de entidades ni otro GET.

## 10. PASO 82-B: recuperación y causa comprobada

Git inicial limpio, rama `feature/suadc-http`, HEAD `3a635cb`,
`WIP: inspeccion ArcGIS INGEMMET paso 82 pendiente de correccion`. El commit
conserva los siete archivos del PASO 82; no había cambios posteriores pendientes.
Se revisaron modelos, inspector, ensayo, las 44 pruebas y ambos documentos. No se
descartó ningún avance. Antes de editar se inventariaron **1.105 IDs de pruebas
únicos**, para contrastarlos después con la ejecución completa.

El código anterior aplicaba dos controles distintos con el mismo tope y diagnóstico:

1. Antes de `json.loads`, contaba cada comilla de apertura (clave o valor cadena),
   apertura de objeto/lista y coma fuera de cadenas. No contaba directamente
   valores numéricos, booleanos o nulos. Era una aproximación, no un conteo de nodos.
2. Tras materializar el JSON, contaba contenedores, claves y valores durante un
   recorrido completo. Usaba `pila.extend` con todos los hijos, cuya frontera
   crecía con la cardinalidad. Después, `ValidacionMetadatos` congelaba/copiaba
   **todo** el árbol, incluso secciones no necesarias para validar la capa.

Ambos límites eran 20.000, pero no equivalentes. No había topes generales separados
para listas u objetos; la cardinalidad quedaba limitada indirectamente por esos
conteos. El esquema sí limitaba a 1.024 capas y 2.048 campos. Profundidad: 32;
cadenas decodificadas: 65.536 caracteres. El control de cadenas era posterior al
parseo y no impedía su asignación inicial.

En el ensayo real, el control preliminar detuvo la inspección de los 983.697 bytes
antes del esquema. El tamaño transferido cabía en 1 MiB, lo cual no garantizaba
que cupiera en la complejidad anterior. **No se conoce la distribución del cuerpo
real**, que no se conservó. No se atribuye su fallo a simbología, campos ni otra
sección determinada, ni se intenta reconstruirlo desde su hash.

La fixture inventada `extensa()` permite reproducir una causa posible: 2.600
entradas de simbología, 727.078 bytes de JSON, **46.976 unidades preliminares y
39.147 nodos** según los algoritmos anteriores. Ambos exceden 20.000. Esto demuestra
la limitación local con datos conocidos; no identifica el contenido institucional.

## 11. Estrategia elegida y justificación de presupuestos

Se adopta **A + B**: presupuestos separados y selección de propiedades esenciales,
manteniendo la validación estructural del documento completo con `json.loads` de
Python. No se implementa un parser JSON propio ni evaluación de código de reglas.

La alternativa C, parseo incremental de secciones, exigiría un parser adicional o
una implementación propia para manejar correctamente escapes, duplicados, números,
cancelación y cierres. Para documentos de hasta 1 MiB, la complejidad añadida no se
justifica con las pruebas actuales. Tampoco se usa regex para extraer campos ni se
detiene el análisis después de encontrar las propiedades requeridas.

El presupuesto global se deriva de un **modelo orientativo de 32 MiB de sobrecarga
estructural / 256 bytes por unidad = 131.072 unidades**. El factor contempla objetos
Python, referencias y holgura de contenedores; se contrasta con mediciones locales,
no con el tamaño desconocido de la respuesta institucional. Es un presupuesto
de admisión, **no una cota matemática de memoria total, reserva de RAM ni límite
de RSS**: texto, buffers, cadenas, copias temporales, intérprete y transporte añaden
memoria. El documento sigue materializándose una vez en el parser estándar.

La prelectura ahora suma aperturas de cadenas/contenedores, dos unidades por `[`
—contenedor y primer hijo potencial—, una por `:` —valor potencial— y una por coma.
Ignora puntuación dentro de cadenas y reconoce escapes. Es una sobreestimación
estructural para documentos JSON válidos compuestos; el recorrido posterior cuenta
los nodos reales y vuelve a imponer el presupuesto. No sustituye la gramática de
`json.loads`, que también rechaza contenido posterior al cierre del documento.

Se comprueban profundidad, cardinalidad por contenedor y presupuesto global **antes
del parseo**. Este recorrido utiliza una pila de profundidad máxima 32. Después,
el recorrido de validación usa iteradores con frontera O(profundidad), sin copiar
todos los hijos a una pila. Se seleccionan referencias a propiedades esenciales,
se comprueba su presupuesto propio y se libera el resto antes de congelar la salida.
Las secciones omitidas se validan estructuralmente, pero no se evalúa su semántica
ArcGIS. No se conservan en `datos` ni se congelan por segunda vez.

| Control | WIP anterior | PASO 82-B |
|---|---|---|
| Transferencia por respuesta | 1.048.576 bytes | **Igual**, sin modificar HTTP global |
| Profundidad | 32 | **Igual** |
| Prelectura global | 20.000 unidades heterogéneas | 131.072 unidades conservadoras, algoritmo descrito arriba |
| Árbol completo | 20.000 nodos | 131.072 nodos; comprobación adicional a prelectura |
| Propiedades esenciales | Sin presupuesto separado | **20.000 nodos**, incluidas claves y contenido anidado |
| Una lista JSON | Implícito por conteos globales | 20.000 elementos como máximo |
| Un objeto JSON | Implícito por conteos globales | 4.096 propiedades como máximo |
| Capas / campos | 1.024 / 2.048 | **Igual**, además de los presupuestos anteriores |
| Cadena decodificada | 65.536 caracteres | **Igual**, también en secciones omitidas |
| Entero | 32 caracteres de literal | **Igual**; booleanos no son enteros de esquema |
| Duplicados / números no finitos | Rechazados | **Igual**, en todo el documento |
| Salida inmutable | Copia completa | Solo selección esencial acotada |

`LimitesInspeccion` solo permite **reducir** esos topes; rechaza booleanos,
cero y valores superiores. No ofrece un mecanismo para ampliar el límite HTTP.
El rechazo por presupuesto queda como inspección incompleta, no como evidencia
de que el JSON o la información científica sean erróneos.
También se corrige la llamada directa con más de 1 MiB: se rechaza antes del parser
y no se calcula SHA-256 recorriendo todo ese cuerpo. Solo en ese caso `sha256`
es `None` (ampliación conservadora del tipo anterior `str` a `str | None`);
los cuerpos admitidos conservan su huella exacta en memoria. No se altera el
contrato HTTP ni el de integridad RAW, ni se declara verificación física en disco.

## 12. Estados, alcance y coherencia

Se conservan las interfaces posicionales anteriores y `EstadoMetadatos`
(`metadatos_coherentes` / `revision_necesaria`). Se añaden campos con valores
predeterminados conservadores; el nombre histórico «coherente» se limita al esquema
esencial, **nunca a todo ArcGIS o al contenido científico**.

| Eje | Estados y significado |
|---|---|
| `estado_json` | `NO_INICIADO`: no comenzó; `PARCIAL`: recorrido iniciado sin completar; `COMPLETO`: todo el documento terminó el parseo estricto y los controles JSON; `INVALIDO`: defecto comprobado de sintaxis, codificación, claves o números |
| `alcance` | `ESENCIALES`: propiedades requeridas comprobadas, semántica ArcGIS parcial; `INCOMPLETO`: límite o cancelación; `INVALIDO`: respuesta/esquema/contexto incompatible |
| `secciones_omitidas` | Nombres de propiedades raíz no evaluadas semánticamente; no expuestos en `repr` ni confundidos con propiedades ausentes |
| `estadisticas` | Unidades de prelectura, nodos completos/esenciales y profundidad observada; no mediciones de RAM |
| `coherencia_servicio_capa` | `True` solo con contexto de servicio validado para el mismo objetivo y contraste superado; `None` si no se comprobó o hubo fallo |

Ejemplos: exceso de presupuesto global → JSON parcial/inspección incompleta;
exceso de presupuesto esencial después del parseo → JSON completo/inspección
incompleta; geometría contradictoria → JSON completo/respuesta inválida; éxito
con `drawingInfo` omitido → JSON completo/esenciales comprobados, **inspección
semántica parcial**. No existe estado que declare comprobada toda la semántica.
Los fallos mantienen `revision_necesaria`, datos públicos vacíos y OID/coherencia
sin confirmación. Los diagnósticos son códigos, sin mensajes remotos o credenciales.
`permite_continuar` exige además JSON completo y esquema esencial comprobado:
una etiqueta histórica `COHERENTE` aislada no habilita el siguiente paso.

La selección mantiene identidad de servicio/ruta y capa 7 `Litologia`, tipo
`Feature Layer`, geometría `esriGeometryPolygon`, CRS y extensión declarados,
campos/tipos/nulabilidad/longitudes/dominio declarado, exactamente un campo OID y
coherencia de `objectIdField`/`objectIdFieldName` cuando se anuncien, MaxRecordCount,
formatos, capacidades y paginación anunciada. Los tipos de campo se reconocen por
nombre explícito; un prefijo `esriFieldType` inventado ya no basta. Se conservan los
ocho nombres prioritarios, sin añadirles semántica, tipos esperados o unidades
inventadas. Un dominio solo se reconoce como objeto; no se valida todo su significado.

El ensayo ahora pasa el resultado del servicio al inspector de capa. Se exige el
mismo objetivo y un resultado de servicio con JSON completo y esquema esencial
coherente; se contrasta la capa anunciada y, si se anuncian, tipo/geometría. Ambos
CRS se contrastan contra el mismo par esperado 102100/3857, admitiendo sus formas
declaradas. Una diferencia de versión técnica se advierte sin inventar una edición
geológica. **No** se fuerza igualdad de extensiones, capacidades o MaxRecordCount
entre ámbitos distintos. Sin contexto de servicio se deja la coherencia sin comprobar.
El contraste no demuestra simultaneidad ni que la publicación no haya cambiado.

No se atribuye estabilidad histórica a ObjectID, funcionamiento real a la
paginación ni completitud a MaxRecordCount. Simbología, etiquetas, plantillas,
descripciones y cualquier otra propiedad raíz no seleccionada quedan sin evaluación
semántica; derechos, autoría y significado de campos continúan pendientes.

## 13. Cancelación, memoria y riesgos residuales

El inspector recibe opcionalmente el mismo `Event` de cancelación del ensayo.
Comprueba cancelación antes del trabajo, cada 4.096 caracteres de prelectura,
en cada objeto decodificado y cada 256 nodos del recorrido, además de antes de
publicar el resultado. No entrega datos utilizables después de cancelarse.
No hay cancelación dura dentro de una operación C de `json.loads` ni durante una
única cadena; el límite de 1 MiB y los presupuestos reducen ese tramo. Tampoco
se implementa un plazo total o aislamiento por proceso.

Medición puntual con Python 3.15.1, `tracemalloc`, cuerpo extendido hasta exactamente
1 MiB con espacios válidos, después de crear la fixture:

| Fixture sintética | JSON sin relleno | Prelectura actual / nodos reales / esenciales | Pico de asignaciones Python | Tiempo local con instrumentación |
|---|---|---|---|---|
| Simbología de 2.600 entradas | 727.078 bytes | 62.647 / 39.147 / 139 | 3.126.641 bytes | 0,8254 s |
| 5.000 objetos con valores pequeños | 115.130 bytes | 55.237 / 40.141 / 139 | 2.550.878 bytes | 0,8966 s |
| Comprobación adicional: 11.500 objetos, próxima al presupuesto global | 266.130 bytes | 126.737 / 92.141 / 139 | 4.606.647 bytes | 3,9101 s |

La prueba de regresión exige picos menores de 32 MiB en las dos primeras fixtures, sin
pretender que cubran todos los documentos posibles o el RSS nativo. Otra fixture
de simbología tiene **1.039.078 bytes de JSON real**, más del 99 % del límite,
y se prueba también rellenada hasta 1 MiB y con un byte final inválido. El control
comprueba el documento completo, no solo un prefijo útil.
La tercera fila es una comprobación puntual adicional, con aserciones, fuera del
conteo de métodos unitarios: ocupa más del 96 % del presupuesto estructural y
también exige un pico inferior a 32 MiB. No prueba una cota universal.

Siguen siendo límites deliberados: se rechazan documentos con listas enormes,
dominios esenciales que agoten su presupuesto, cadenas largas o más complejidad
global aunque quepan en bytes. No se conoce aún si la capa real cabe en estos
presupuestos. No se promete parseo incremental, memoria constante, tiempo máximo
de pared ni aceptación de cualquier metadato institucional. Un nuevo exceso
obligará a revisión offline, sin ampliar límites automáticamente.

## 14. Pruebas y verificación del PASO 82-B

Se añaden **34 pruebas** en `tests/test_inspeccion_arcgis_extensa.py`; permanecen
intactas las 44 anteriores. Cubren los 22 grupos requeridos: respuestas pequeñas
y extensas, cercanía a 1 MiB, simbología, cardinalidad, profundidad, duplicados
críticos/escapados/omitidos, ausencias esenciales, geometría/CRS/OID contradictorios,
truncamiento, malformación, UTF-8 inválido, NaN/Infinity, error ArcGIS en HTTP 200,
exceso de bytes, ambos presupuestos, cancelación, memoria medida, determinismo
y compatibilidad. Incluyen los bordes exactos de presupuestos, lista, objeto y
profundidad, contexto de servicio y contraste mediante `MockTransport`.

La guardia temporal de ejecución bloquea DNS/conexiones reales y cualquier acceso
al árbol operativo `SPICA_DATOS`, incluidos `stat`, listados, apertura y SQLite.
Se emplean solo fixtures inventadas, memoria y temporales aislados. No se leen
ni verifican físicamente RAW, staging o SQLite operativos para hacer esta afirmación.

## 15. Condiciones de una futura validación controlada

Este paso **no autoriza ni ejecuta red**. Antes de otra solicitud se requiere
revisión de estos cambios y autorización expresa para **un solo GET de capa**:

`https://geocatminnube.ingemmet.gob.pe/arcgis/rest/services/SERV_GEOLOGIA_50K_INTEGRADA/MapServer/7?f=json`

Mantener 1 MiB, el presupuesto local documentado, TLS verificado, origen exacto,
sin autenticación, cookies reutilizadas, redirecciones, compresión ni reintentos;
rechazar HTTP 206, cambios de ruta, errores HTTP/ArcGIS y respuestas inesperadas.
Debe definirse previamente dónde y cómo conservar evidencia primaria verificable,
con privacidad y limpieza controladas, y registrar estados, bytes, tiempos, hash
y alcance real. Ningún hash histórico permite reconstruir el cuerpo perdido.

No iniciar un `EnsayoMetadatosArcGIS` nuevo de dos rutas para repetir el servicio:
su interfaz sigue exigiendo ese GET previo y no es un permiso para consumir otra
petición. Un procedimiento futuro de capa única deberá reutilizar `ClienteHTTP`
y el inspector, sin fabricar un contexto validado a partir del informe o fixtures.
Si no existe un resultado primario de servicio conservado, dejar el contraste
entre respuestas como no comprobado y documentar la antigüedad del anuncio E-04.
No conseguirlo mediante un GET de servicio adicional no autorizado.

La respuesta de capa real sigue **PENDIENTE**. Sus campos, OID, CRS, geometría,
capacidades y paginación no se promueven a comprobados por estas pruebas. Aunque
un GET futuro supere el inspector, no habilitará `/query`, vectores, paginación,
RAW, catálogo operativo, QA/QC científico ni atribuciones sobre licencia o completitud.

## 16. Resultado final del PASO 82-B

Con Python **3.15.1** de `.venv`, HTTPX **0.28.1** y SQLite **3.53.4**:

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -B -m pip check
git diff --check
git status --short
```

La ruta `src/` y la guardia se configuraron únicamente mediante `PYTHONPATH` del
proceso. La última suite se ejecutó sin cambios de código posteriores:

```text
Ran 1139 tests in 115.977s
OK
```

**1.139 aprobadas, 0 fallidas, 0 errores, 0 omitidas.** El registro completo se
contrastó por ID con el inventario previo: **1.105 preservadas + 34 nuevas**,
ningún ID faltante ni duplicado. Permanecen las 44 pruebas del inspector inicial.
`pip check`: `No broken requirements found.`; salida 0. `git diff --check`: sin
errores. Se revisó además el archivo nuevo que ese comando no incluye: UTF-8,
sintaxis Python, definiciones duplicadas por ámbito y whitespace, todo correcto.
Los enlaces documentales locales y sus anclas también se comprobaron offline.

Archivos: seis modificados y uno nuevo, todos dentro del alcance:

- `src/spica/adquisicion/inspeccion_arcgis/modelos.py`: presupuestos, estados y
  alcance explícito, contadores, puerta de continuación y hash opcional solo
  para entrada directa que exceda el límite.
- `src/spica/adquisicion/inspeccion_arcgis/inspector.py`: controles de documento,
  selección acotada, cancelación y contraste de contexto.
- `src/spica/adquisicion/inspeccion_arcgis/ensayo.py`: transmite el contexto del
  servicio y el evento al mismo inspector; sin otro cliente HTTP.
- `src/spica/adquisicion/inspeccion_arcgis/__init__.py`: exportaciones locales.
- `tests/test_inspeccion_arcgis_extensa.py`: **nuevo**, 34 pruebas sintéticas.
- Este informe y `docs/matriz_interoperabilidad_ingemmet.md`: actualización
  separada de la historia institucional anterior.

Estado final de Git, HEAD sin cambios en `3a635cb`:

```text
 M docs/matriz_interoperabilidad_ingemmet.md
 M docs/validacion_metadatos_ingemmet_paso82.md
 M src/spica/adquisicion/inspeccion_arcgis/__init__.py
 M src/spica/adquisicion/inspeccion_arcgis/ensayo.py
 M src/spica/adquisicion/inspeccion_arcgis/inspector.py
 M src/spica/adquisicion/inspeccion_arcgis/modelos.py
?? tests/test_inspeccion_arcgis_extensa.py
```

**Cero conexiones externas y cero GET externos nuevos.** Las peticiones de pruebas
usan exclusivamente `MockTransport`. Los registros de guardia revisados contienen
cero eventos de red o acceso operativo bloqueados. No se accedió a RAW, staging
o SQLite operativos, no se modificaron sus archivos ni se hicieron migraciones.
Las pruebas de almacenamiento previas usan temporales aislados. No hubo cambios
en transporte global, conectores, contratos del núcleo, dependencias, `main.py`,
`.gitignore` o `.venv`; tampoco instalaciones, QA/QC científico, commits o push.
Los auxiliares de auditoría y registros de pruebas quedan en temporal fuera de
Git; un directorio auxiliar vacío de preparación fallida se retiró sin recursión,
sin cambiar ACL ni tocar originales.

**Dictamen: APTO PARA NUEVA VALIDACIÓN CONTROLADA**, sujeto a revisión y a la nueva
autorización limitada descrita en la sección 15. Es un dictamen sobre el inspector
local y sus controles probados, **no una validación institucional**. La capa real
7 `Litologia` permanece **PENDIENTE**. No se ejecuta el siguiente paso.
