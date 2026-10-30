# PASO 82 — Ensayo de metadatos ArcGIS REST de INGEMMET

**Estado actual, PASO 82-D: resultado A — VALIDACIÓN COMPLETA DE METADATOS
ESENCIALES del archivo conservado. Dictamen: APTO CON RESTRICCIONES.** La
reevaluación offline terminó con sintaxis completa, 131.042 nodos y 680 nodos
esenciales, sin ampliar topes. No valida entidades, definiciones autoritativas
de CRS, funcionamiento de consultas o calidad geológica. Véase la
[sección 22](#22-paso-82-d-integridad-y-diagnóstico-instrumental-offline).

**Antecedente al cierre del PASO 82-C: REQUIERE CORRECCIONES.** Se realizó un único GET
autorizado de capa y se preservó evidencia primaria exacta fuera de Git. La
inspección se detuvo en 131.073 unidades frente al presupuesto de 131.072,
antes del parser; la capa permanece **PENDIENTE**. Véase la
[sección 17](#17-paso-82-c-preparación-y-alcance-del-ensayo).
Las conclusiones anteriores se conservan como antecedentes fechados por paso.

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

## 17. PASO 82-C: preparación y alcance del ensayo

Git inicial limpio, rama `feature/suadc-http`, HEAD **`0210ff3`**,
`SUADC: correccion de inspeccion ArcGIS JSON extenso`. El PASO 82-B está
registrado con sus siete archivos. Se revisaron el inspector corregido, modelos,
ensayo, pruebas, informes y políticas efectivas de `ClienteHTTP`. No se cambió
código Python, configuración, dependencias ni presupuestos.

La autorización se limita a **un GET** de la ruta exacta de capa de la sección 18.
No se utilizó un ensayo de dos rutas ni se repitió la consulta de servicio. Se
orquestaron `ClienteHTTP.get()` e `inspeccionar_metadatos()` desde un auxiliar
local fuera del repositorio; no se implementó un segundo transporte.

Antes de red se volvieron a ejecutar **78 pruebas** del inspector y ensayo:

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p 'test_inspeccion_arcgis*.py' -v
```

**78 aprobadas, 0 fallidas, 0 errores, 7,422 s.** Se comprobaron además cinco
simulaciones puntuales con `MockTransport`: respuesta correcta, exactamente 1 MiB,
error ArcGIS en HTTP 200, redirección y exceso de tamaño. Se verificaron copia
exacta/reapertura/hash de los cuerpos admitidos, rechazo de sobrescritura y de
repetición del procedimiento en un directorio consumido. Estas simulaciones no
añaden métodos a la suite ni constituyen evidencia institucional.

El directorio exclusivo de evidencia se creó fuera de Git, RAW y staging:

```text
C:\Users\Propietario\AppData\Local\SPICA-evidencia-paso82c-20261030T201204Z-d64783fdf74f
```

Se comprobaron componentes sin symlinks/junctions/reparse points, ausencia de
redirección de ruta, directorio inicialmente vacío, espacio disponible y creación
exclusiva de archivos. Una prueba sintética de 64 bytes se escribió con `fsync`,
se cerró/releyó y se retiró antes de recibir evidencia institucional. Espacio
libre previo: **20.881.661.952 bytes**, superior al mínimo local de 32 MiB; no es
una reserva. Los nombres de archivo son locales fijos, no proceden de cabeceras.

Incidencia de preparación, sin red: el primer comparador de ACL rechazó el SID
`S-1-3-4` por no incluirlo entre los permitidos. Windows lo identificó localmente
como **DERECHOS DE PROPIETARIO**. Se corrigió solo esa comparación auxiliar:
propietario igual al usuario actual, DACL protegida y reglas únicamente para
derechos del propietario, SYSTEM y Administradores. Se verificó de nuevo el
mismo directorio antes de cualquier GET; no hubo cambio de ACL, traslado ni nueva
creación del directorio. `privacidad.json` registra el resultado y la corrección.
La preparación terminó satisfactoriamente con **0 GET y 0 conexiones previas**.

La instancia del cliente común mantuvo TLS verificado, `trust_env=False`,
redirecciones deshabilitadas, sin autenticación/cookies, `Accept-Encoding: identity`,
timeouts de conexión/lectura/escritura/pool de 10/30/30/10 s, máximo 1.048.576 bytes
y bloques de hasta 65.536 bytes. Política explícita: `max_intentos=1`. Los timeouts
no constituyen un plazo total. Se añadieron controles puntuales de solicitud exacta
y una guardia de DNS/TCP/accesos operativos; no se modificó la política global.
Un marcador creado exclusivamente antes de solicitar impide reutilizar la carpeta
para repetir el GET. Nunca se intentó otra URL o un segundo GET tras el resultado.

## 18. Único GET y evidencia primaria del PASO 82-C

URL exacta utilizada:

```text
https://geocatminnube.ingemmet.gob.pe/arcgis/rest/services/SERV_GEOLOGIA_50K_INTEGRADA/MapServer/7?f=json
```

| Dato | Resultado observado |
|---|---|
| Método / intentos | GET / **1**, sin reintento |
| Inicio UTC | `2026-10-30T20:14:58.525392Z` |
| Fin HTTP UTC | `2026-10-30T20:15:01.319357Z` |
| Fin del procedimiento UTC | `2026-10-30T20:15:01.687146Z` |
| Estado HTTP | **200** |
| Content-Type | `application/json; charset=UTF-8` |
| Content-Length | **No proporcionado**; no se inventa a partir del tamaño local |
| Content-Encoding | No proporcionado; se solicitaron y conservaron bytes sin descompresión |
| Bytes admitidos por el transporte | **983.697**; fin normal del flujo dentro de 1 MiB |
| Tamaño físico conservado | **983.697 bytes**, comprobado al reabrir |
| Red observada | **1 DNS y 1 conexión TCP**, únicamente para el destino autorizado |
| Redirecciones / consultas adicionales | **0** |
| Accesos operativos de la guardia | **0** |

Archivo primario: `capa7.json`, dentro del directorio privado de la sección 17.
El nombre/extensión y el MIME no constituyen una declaración de sintaxis válida.
SHA-256 de los bytes transferidos y del archivo físicamente reabierto:

```text
21f85c366686bcfe08a102abf775e0edc05de1fe30f567a73ec98cbf3aa80e39
```

La escritura fue exclusiva, con cierre y `fsync`; se reabrió el archivo, se
compararon sus bloques con los bytes devueltos por `get()` y se recalculó tamaño
y hash. Primera comprobación física: `2026-10-30T20:15:01.365362Z`. Otra lectura
offline independiente confirmó después el mismo tamaño y SHA-256. Se comprobaron
archivo regular, un solo enlace y ausencia de reparse points, así como identidad,
tamaño y fecha de modificación estables durante la primera lectura. No se alteró
el cuerpo, no se parseó/reserializó para guardarlo ni se incorporó al RAW.

Esto acredita **integridad local de la copia recibida**, no autenticidad
institucional independiente, firma digital, edición geológica, completitud de
entidades ni validez científica. La conexión utilizó la verificación TLS habitual;
no se hizo una certificación externa del contenido o de la publicación.

Archivos conservados, sin borrado automático de evidencia:

| Archivo privado | Bytes | Función |
|---|---|---|
| `capa7.json` | 983.697 | Cuerpo HTTP exacto; JSON todavía sin validar completamente |
| `inicio_get.json` | 194 | Marcador UTC de consumo de la única operación |
| `preparacion.json` | 880 | Rutas, espacio, presupuestos y huella del auxiliar revisado |
| `privacidad.json` | 476 | Comprobación de ACL y corrección del comparador local |
| `resultado.json` | 1.800 | Hechos HTTP, hash/tamaño físicos, estados y contadores |
| `auditoria_red.json` | 77 | Un DNS, un TCP, sin destinos ajenos ni accesos operativos |

Se verificaron las ACL del directorio y de los seis archivos, sin modificarlas.
Los resúmenes omiten el mapa completo de cabeceras, cookies y mensajes privados.
El directorio no está en Git ni en una carpeta temporal de borrado automático.
Sigue bajo control del usuario: `fsync` y hash no sustituyen copia de seguridad,
protección frente a cambios futuros del propietario ni garantías de durabilidad
ante toda interrupción. Las inspecciones offline futuras deben volver a comprobar
esta huella y conservar el original sin sobrescribirlo.

## 19. Inspección real de capa y límites del resultado

El presupuesto vigente **no se amplió**. El inspector se detuvo en la prelectura:

| Campo de resultado | Valor / interpretación |
|---|---|
| `estado` | `revision_necesaria` |
| `estado_json` | `json_parcialmente_inspeccionado` |
| `alcance` | `inspeccion_incompleta` |
| Diagnóstico | `json_presupuesto_documento_agotado` |
| Unidades de prelectura al detenerse | **131.073**, frente a 131.072 permitidas |
| Nodos del documento / esenciales recorridos | **0 / 0**; el parser y el esquema no se ejecutaron |
| Profundidad observada | **10 en el prefijo inspeccionado**; no demuestra la profundidad máxima de todo el cuerpo |
| `campo_oid` | `None`, sin confirmación |
| `coherencia_servicio_capa` | `None`, sin contraste completo entre respuestas |
| Datos esenciales devueltos | Vacíos; no se reconstruyeron desde fixtures |

No se ha confirmado la sintaxis JSON completa, ausencia de claves duplicadas o
números no finitos en todo el cuerpo, ni ausencia de un objeto ArcGIS de error.
No se puede calificar el cuerpo como JSON inválido: **faltó completar el examen**.
Que no se devolvieran advertencias o secciones omitidas tampoco significa que no
existan: el código no alcanzó esa fase. No se atribuye el exceso a simbología,
dominios ni otra sección específica sin un análisis posterior autorizado.

Los siguientes son **objetivos o antecedentes**, no propiedades ahora comprobadas
en el cuerpo de capa:

| Propiedad | Estado tras el PASO 82-C |
|---|---|
| ID `7`, nombre `Litologia` | Ruta solicitada y anuncio histórico del servicio; pendientes en el JSON de capa |
| Tipo de capa / geometría | Pendientes; no se confirma `Feature Layer` o `esriGeometryPolygon` |
| `wkid` / `latestWkid`, CRS completo | Pendientes; no se traslada el CRS histórico del servicio a la capa |
| Unidades / extensión | Pendientes; no se infieren del título, servicio o EPSG |
| `objectid` | Presencia, tipo, atributos y declaración OID pendientes |
| `codi` | Presencia y tipo pendientes |
| `codiunihoja` | Presencia y tipo pendientes |
| `etiqueta` | Presencia y tipo pendientes |
| `unidad` | Presencia y tipo pendientes |
| `tipo_unidad` | Presencia y tipo pendientes |
| `litologia` | Presencia y tipo pendientes |
| `descrip` | Presencia y tipo pendientes |
| `maxRecordCount` | No comprobado en capa; el `2000` anterior correspondía al servicio |
| Paginación declarada / funcional | Ninguna comprobada en capa; no hubo paginación real |
| Formatos / capacidades anunciadas | No comprobados en este cuerpo; no se ejercieron consultas de entidades |

No se hizo un segundo parseo con presupuestos mayores ni extracción alternativa
para completar esta tabla. No se atribuye estabilidad histórica a ObjectID,
funcionalidad a la paginación, licencia a una respuesta pública ni completitud a
un flujo HTTP terminado.

## 20. Contraste, riesgos y dictamen del PASO 82-C

El tamaño y SHA-256 actuales coinciden con los registrados para la **capa** en el
PASO 82. Es una coincidencia con el resumen histórico, no una comparación física
de dos originales: el cuerpo anterior no está disponible. El diagnóstico ahora
es más específico y el presupuesto local es distinto del utilizado entonces;
ninguno de los dos ensayos completó la validación de capa.

El servicio anterior anunció capa 7 `Litologia`, CRS 102100/3857, `esriMeters`,
MaxRecordCount 2000 y formatos/capacidades recogidos en las secciones 5–6.
**Esos anuncios históricos no se convierten en propiedades actuales de capa.**
No se conserva el primario del servicio ni se lo volvió a solicitar. No hay
contraste completo entre respuestas, prueba de simultaneidad o evidencia de que
el servicio/publicación permaneciera sin cambios entre ambos ensayos. Tampoco
se demostró una contradicción geométrica o documental: esas comprobaciones no
llegaron a realizarse.

La evidencia conservada permite preparar un futuro diagnóstico offline, sujeto a
revisión, sin necesitar otra descarga para localizar la complejidad del cuerpo.
Este paso no modifica el inspector, no eleva límites y no implementa ese trabajo
adicional. Antes del diseño vectorial deben resolverse de manera segura la
inspección de metadatos reales, los campos/OID, CRS, extensión, límites/capacidades
y el alcance de sus anuncios. Cualquier nueva técnica requerirá justificación,
pruebas adversariales, contabilidad explícita y una salida que distinga lo no
inspeccionado; no basta aumentar el presupuesto hasta aceptar el archivo.

Siguen pendientes derechos de consulta, reutilización, atribución, adquisición
vectorial y redistribución. No se infiere licencia por el acceso sin autenticación.
Escala nominal, precisión, cobertura, significado de atributos, edición y
aplicabilidad a decisiones ambientales no están acreditados por esta lectura.
No se deben deducir condiciones locales del terreno, contaminación, riesgo o
certeza de contactos geológicos a partir del nombre de la capa o del servicio.

**Dictamen: REQUIERE CORRECCIONES antes de declarar la capa validada o pasar al
diseño vectorial.** La transferencia y conservación técnica terminaron; la
inspección JSON/esencial quedó incompleta. La capa continúa **PENDIENTE**.
No se autoriza ni ejecuta recuperación de entidades, `/query`, `/export`,
paginación, descarga de polígonos, RAW operativo ni QA/QC científico.

## 21. Verificación final y archivos del PASO 82-C

Se ejecutó de nuevo la suite completa, después de la operación institucional,
con Python **3.15.1** de `.venv`, HTTPX **0.28.1** y SQLite **3.53.4**. `src/`
y la guardia offline se configuraron mediante `PYTHONPATH` solo para los procesos
de comprobación; no se cambió configuración del proyecto.

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -B -m pip check
git diff --check
git status --short
```

```text
Ran 1139 tests in 127.770s
OK
No broken requirements found.
```

**1.139 aprobadas, 0 fallidas, 0 errores, 0 omitidas.** Se contrastaron los IDs
de esta ejecución con el registro completo del PASO 82-B: las **1.139 anteriores**
están presentes, sin faltantes o duplicadas. No se añadieron pruebas unitarias ni
código del proyecto. Las 78 pruebas previas y cinco simulaciones de conservación
son comprobaciones repetidas/adicionales de preparación, **no se suman** a 1.139.
Los 115,977 s de la sección 16 corresponden al antecedente del PASO 82-B;
127,770 s es la ejecución nueva del PASO 82-C. Los comandos terminaron con salida 0.

`git diff --check` terminó sin errores. Se revisaron UTF-8, whitespace y enlaces
documentales locales/anclas. Los únicos archivos modificados son este informe y
`docs/matriz_interoperabilidad_ingemmet.md`. No hay archivos nuevos dentro de Git
ni cuerpos institucionales añadidos al repositorio. El estado final es:

```text
 M docs/matriz_interoperabilidad_ingemmet.md
 M docs/validacion_metadatos_ingemmet_paso82.md
```

Rama `feature/suadc-http`, HEAD **`0210ff3`**, sin commits o push en esta sesión.
No se modificaron archivos Python, pruebas, contratos, dependencias, `main.py`,
`.gitignore` o `.venv`. Los auxiliares de ejecución y registros de pruebas quedan
fuera de Git, en temporal; los seis archivos de evidencia primaria y control
permanecen en el directorio privado documentado, sin eliminación automática.

Las guardias de preparación, suite y comprobaciones offline bloquearon red y el
árbol operativo `SPICA_DATOS`; los registros revisados no muestran intentos. La
guardia del único ensayo real registró **1 DNS, 1 TCP y 0 accesos operativos**;
el control de aplicación registró **1 GET** y ningún reintento. No hubo consultas
a otras rutas ni otra solicitud después del límite. No se accedió ni modificó
RAW, staging o SQLite operativos; no se verificó físicamente ese almacenamiento
para formular esta conclusión. Las pruebas de almacenamiento/SQLite existentes
usan temporales aislados. No se realizaron migraciones operativas, instalaciones,
transformaciones de datos ni activación científica.

Se cierra el PASO 82-C con evidencia íntegra conservada y resultado de inspección
incompleto. Se espera revisión antes de cualquier corrección posterior, nuevo
GET, diseño vectorial o recuperación de entidades.

## 22. PASO 82-D: integridad y diagnóstico instrumental offline

Estado inicial: rama `feature/suadc-http`, HEAD **`0210ff3`**, dos documentos
modificados y sin registrar por el PASO 82-C. Se conservaron esos avances y los
resultados históricos; no se restauró ni descartó trabajo. Antes de modificar
el inspector se revisaron código, límites y los seis archivos de evidencia.

Se abrió `capa7.json` **solo para lectura**, verificando componentes de ruta sin
symlinks/junctions/reparse points, archivo regular, un solo enlace y coincidencia
de identidad, tamaño y fecha de modificación antes/después de leer. Se verificaron
también los cinco controles, cuyos JSON, tamaños y hashes coinciden con el inventario
del PASO 82-C. El primario conserva **983.697 bytes** y SHA-256:

```text
21f85c366686bcfe08a102abf775e0edc05de1fe30f567a73ec98cbf3aa80e39
```

No se escribió en el directorio original. Las guardias bloquearon toda red,
escritura/mutación del primario y acceso al árbol operativo `SPICA_DATOS`.
Los resultados se guardaron en otro directorio privado, con propietario verificado,
DACL protegida y acceso limitado a propietario, SYSTEM y Administradores:

```text
C:\Users\Propietario\AppData\Local\SPICA-diagnostico-paso82d-7c6fcc89881f495fa883abdd191f08ff
```

El procedimiento **instrumental separado** no es una ruta pública de validación.
Se ejecutó antes de cambiar límites o lógica productiva, mediante biblioteca
estándar, `json.loads` estricto y un proceso hijo acotado:

| Control diagnóstico | Presupuesto |
|---|---|
| Entrada | 1.048.576 bytes, huella esperada obligatoria |
| Unidades heurísticas anteriores | 524.288, exclusivamente instrumental |
| Nodos instrumentales | 262.144 |
| Profundidad / lista / objeto / cadena | 32 / 20.000 / 4.096 / 65.536, iguales a los controles productivos |
| Asignaciones Python trazadas | Comprobación de pico de 32 MiB durante las fases |
| Job Object de Windows | Máximo 256 MiB de memoria privada del proceso; 30 s de CPU de usuario |
| Tiempo de pared del hijo | 60 s, controlado por el lanzador |

Los topes instrumentales permiten medir el exceso de la heurística sin tocar la
política productiva. El modelo de sobrecarga de 256 bytes por nodo da 64 MiB para
262.144 nodos; existe además el límite nativo del proceso. La comprobación de
`tracemalloc` es por fases/intervalos, no una barrera universal de RSS; el límite
del Job corresponde a memoria privada, no a RSS. Ninguno es una reserva de RAM.
Si un tope se hubiera agotado, el resultado habría quedado incompleto.

Se completó la medición el **2026-10-30T20:34:11.997344Z**: 5,7388 s y pico trazado
de **6.893.548 bytes** en ese proceso. El tamaño/hash/identidad/mtime de los seis
originales coincidieron antes y después. No se guardó otra copia completa del
JSON ni se reprodujeron sus bytes, etiquetas o imágenes en Git/terminal.

## 23. Causa exacta y estructuras responsables

El contador de 131.073 del PASO 82-C era **un corte por límite**, no una medición
completa. Se reproduce en el índice **574.761 de caracteres decodificados, base
cero**; ese índice no es una posición de bytes UTF-8. El corte ocurre dentro de
`drawingInfo`. La medición completa de la misma heurística es **218.540**:

| Contribución a la heurística del PASO 82-B/C | Unidades |
|---|---:|
| Aperturas de cadenas, incluidas claves | 75.375 |
| Aperturas de contenedores | 24.437 |
| Reserva adicional por apertura de arreglo | 12.121 |
| Comas fuera de cadenas | 59.233 |
| Dos puntos fuera de cadenas | 47.374 |
| **Total heurístico** | **218.540** |

El árbol real tiene **131.042 apariciones de nodos**, incluidas claves y valores:

| Categoría | Apariciones |
|---|---:|
| Objetos | 12.316 |
| Arreglos | 12.121 |
| Cadenas, incluidas claves | 75.375 |
| Números | 25.074 |
| Booleanos | 48 |
| Nulos | 6.108 |
| **Total** | **131.042** |

Hay **47.374 claves**, ya incluidas en las cadenas/nodos anteriores, y **36.293
elementos de arreglos**; no deben sumarse otra vez al total. La diferencia
heurística es **87.498 unidades**: puntuación y reservas contaban repetidamente
estructuras cuyos nodos ya aparecían en el recorrido posterior. El archivo cabe
en el tope de **131.072 nodos** que ya existía, con margen de solo **30**.

| Estructura real | Nodos de su subárbol | Unidades heurísticas anteriores |
|---|---:|---:|
| `drawingInfo` | 130.218 | 217.118 |
| `drawingInfo.renderer` | 130.210 | 217.106 |
| `drawingInfo.renderer.uniqueValueGroups` | 71.168 | 120.694 |
| `drawingInfo.renderer.uniqueValueInfos` | 58.963 | 96.285 |
| `fields` | 556 | 985 |
| `advancedQueryCapabilities` | 43 | 63 |
| `extent` | 35 | 51 |
| `sourceSpatialReference` | 25 | 36 |

Los subárboles se solapan: no sumar filas padre/hijo. Esta vez se demuestra que
la estructura de renderizado concentra el consumo, en lugar de asumirlo por el
nombre del producto. Se observaron **3.050** objetos con claves
`label, description, symbol, values` en clases y **3.050** con
`symbol, value, label` en la otra representación. No se eliminaron ni declararon
duplicaciones accidentales; no se probó correspondencia semántica entre ambas.

Profundidad máxima completa: **10**. Mayor arreglo: **3.050 elementos**, en
`drawingInfo.renderer.uniqueValueGroups[0].classes`. Mayor objeto: **55 propiedades**,
la raíz. Mayor cadena: **2.176 caracteres**, en
`drawingInfo.renderer.uniqueValueGroups[0].classes[1409].symbol.imageData`;
no se decodificó ni interpretó esa imagen. Todo ello cabe en sus topes específicos.

Clasificación de las **55 propiedades raíz** observadas; la clasificación no
certifica su semántica ni el funcionamiento de las capacidades:

| Función | Nombres literales presentes |
|---|---|
| Identidad / organización de capa | `id`, `name`, `type`, `geometryType`, `parentLayer`, `subLayers` |
| Versiones técnicas / descripción | `currentVersion`, `cimVersion`, `description`, `copyrightText`, `hasMetadata` |
| Referencia espacial / geometría | `sourceSpatialReference`, `extent`, `geometryField`, `hasGeometryProperties`, `geometryProperties`, `supportsDatumTransformation`, `supportsCoordinatesQuantization` |
| Atributos / subtipos / relaciones | `displayField`, `typeIdField`, `subtypeFieldName`, `subtypeField`, `defaultSubtypeCode`, `fields`, `indexes`, `subtypes`, `relationships`, `hasAttachments` |
| Consulta / anuncios de acceso | `capabilities`, `maxRecordCount`, `supportsStatistics`, `supportsExceedsLimitStatistics`, `supportsAdvancedQueries`, `supportedQueryFormats`, `ownershipBasedAccessControlForFeatures`, `useStandardizedQueries`, `supportedSpatialRelationships`, `advancedQueryCapabilities`, `advancedQueryAnalyticCapabilities` |
| Visualización / información secundaria | `minScale`, `maxScale`, `referenceScale`, `drawingInfo`, `defaultVisibility`, `htmlPopupType`, `canModifyLayer`, `canScaleSymbols`, `hasLabels`, `supportsDynamicLegends` |
| Tiempo / edición / archivo | `isDataVersioned`, `dateFieldsTimeReference`, `preferredTimeReference`, `datesInUnknownTimezone`, `isDataArchived`, `archivingInfo` |

No están presentes las propiedades raíz `types`, `domains`, `objectIdField`,
`objectIdFieldName`, `spatialReference` o `units`. Existen dominios dentro de
descriptores de `fields`; no se les atribuye significado geológico.

## 24. Corrección mínima y presupuestos productivos

Se descartó aumentar el límite global (alternativa A): el árbol ya cabe en el
tope posterior. Se mantiene la separación sintaxis/esquema esencial (B), corrigiendo
la medida de admisión. Un parser incremental nuevo (C) no se justifica para este
archivo de hasta 1 MiB: se completó el parser estándar con memoria medida acotada.

La prelectura ahora cuenta **una aparición por apertura de contenedor, apertura
de cadena —también claves— o inicio de primitivo numérico/booleano/nulo**. Comas,
dos puntos y cierres no añaden nodos; siguen controlando cardinalidad y estructura
de la pila. Para JSON válido esta medida coincide con el árbol posterior. No es
un parser de gramática propio: `json.loads` conserva la validación de todo el
documento, escapes, claves duplicadas, números y contenido posterior al cierre.

| Control productivo | Antes | Ahora |
|---|---|---|
| Cuerpo HTTP | 1 MiB | **Igual** |
| Tope de prelectura | 131.072 unidades de heurística sobreestimadora | **131.072 apariciones de nodos**, misma medida del recorrido posterior |
| Recorrido posterior | 131.072 nodos | **Igual** |
| Nodos esenciales | 20.000 | **Igual** |
| Profundidad / lista / objeto / cadena | 32 / 20.000 / 4.096 / 65.536 | **Iguales** |
| Capas / campos / literal entero | 1.024 / 2.048 / 32 caracteres | **Iguales** |

La admisión cambia de manera deliberada para documentos sobreestimados, sin elevar
el presupuesto de nodos que el parser ya tenía autorizado. Las estadísticas
históricas de heurística no se reinterpretan como nodos. `LimitesInspeccion` sigue
permitiendo solo reducir topes; no hay ampliación automática ni opción para
deshabilitar controles. Se mantienen cancelación, salida inmutable seleccionada,
rechazo de JSON malformado/truncado/no finito, errores ArcGIS y datos vacíos ante
fallo. No cambian firmas públicas, enumeraciones, transporte HTTP o contratos RAW.

Se incluye además `sourceSpatialReference` entre las propiedades esenciales.
Una evaluación intermedia rechazó `4326/4326` al aplicarle erróneamente el CRS
esperado de la extensión. Esa comprobación añadida se corrigió antes de aceptar
la solución: **origen nativo y extensión tienen ámbitos distintos**. Se conservan
y verifican estructuralmente los identificadores de origen, sin imponer igualdad
con el mapa ni certificar sus definiciones. La extensión y un `spatialReference`
raíz, si existe, mantienen el contraste contra el objetivo de representación.
Una advertencia explícita indica que falta comprobación autoritativa del CRS de origen.

`validacion_offline.json` conserva el resultado intermedio en el directorio
diagnóstico separado; `validacion_offline_final.json` conserva el resultado final.
No se sobrescribió ninguno de los controles originales del PASO 82-C.

## 25. Resultado final offline y metadatos esenciales reales

Evaluación final: **2026-10-30T20:43:25.499524Z**, desde el mismo archivo, sin GET.
Se utilizaron estado HTTP/MIME del control histórico guardado; no son una nueva
respuesta del servidor. El inspector corregido devuelve:

| Resultado | Valor |
|---|---|
| Criterio del PASO 82-D | **A — VALIDACIÓN COMPLETA DE METADATOS ESENCIALES** de esta evidencia |
| `estado` / `estado_json` | `metadatos_coherentes` / `json_completamente_validado` |
| `alcance` | `propiedades_esenciales_comprobadas` |
| Diagnósticos | Ninguno |
| Prelectura / árbol completo | **131.042 / 131.042** |
| Nodos esenciales / profundidad | **680 / 10** |
| Error ArcGIS en HTTP 200 | Ausente en la raíz comprobada |
| Esquema | `Feature Layer`, ID **7**, nombre literal **`Litologia`** |
| Geometría declarada | **`esriGeometryPolygon`** |
| Campo OID | **`objectid`**, único descriptor con tipo `esriFieldTypeOID` |
| Coherencia completa servicio/capa | **No comprobada**, `None`; falta el primario de servicio |

La sintaxis, codificación admitida, duplicados y límites se comprobaron sobre todo
el documento. La semántica ArcGIS se limita a la selección esencial; **43 propiedades
raíz**, incluida la simbología, quedan fuera de esa evaluación semántica. La ausencia
de `objectIdField`/`objectIdFieldName` no se rellenó: OID procede del descriptor
tipado de `fields`, no de una propiedad raíz inventada ni de estabilidad histórica.

Referencias declaradas, conservadas por separado:

| Ámbito | `wkid` | `latestWkid` | Alcance de comprobación |
|---|---:|---:|---|
| `sourceSpatialReference` | **4326** | **4326** | Identificadores originales positivos, sin certificación externa de definición |
| `extent.spatialReference` | **102100** | **3857** | Coincide con el par esperado para esta representación |

`extent` declarado: `xmin=-9072538.49965179`, `ymin=-2078636.9217961072`,
`xmax=-7661750.568505581`, `ymax=-334111.1712904824`. Los valores son finitos y
están ordenados. No se verificó extensión de entidades ni cobertura exhaustiva.
El `ymax` difiere del `fullExtent` histórico del servicio (`-331952.0320098707`):
son ámbitos distintos; no se prueba por ello contradicción, edición o pérdida de datos.

No existe `units` raíz. En una lectura instrumental acotada, la declaración
secundaria `geometryProperties` contiene `units="esriDecimalDegrees"`,
`mapUnits={"uwkid":9102}`, `shapeAreaFieldName="st_area(shape)"` y
`shapeLengthFieldName="st_length(shape)"`. Se registran como declaraciones en ese
contexto: **no** se trasladan como unidad de `extent`, no se calculan áreas/longitudes
y no se certifica la semántica de esos campos. Parámetros como `xyUnits`,
`xyTolerance` o `zUnits` tampoco acreditan precisión o incertidumbre científica.
No se convierte 102100 en `EPSG:102100`, no se inventan datum/ejes o unidades, ni
se determina el CRS de salida de consultas aún no realizadas.

Se comprobaron **39 descriptores de campos**; los ocho prioritarios son:

| Nombre literal | Tipo literal | Alias | Longitud declarada |
|---|---|---|---:|
| `objectid` | `esriFieldTypeOID` | `OBJECTID` | No declarada |
| `codi` | `esriFieldTypeInteger` | `CODI` | No declarada |
| `codiunihoja` | `esriFieldTypeString` | `CODFORM` | 20 |
| `etiqueta` | `esriFieldTypeString` | `ETIQUETA` | 100 |
| `unidad` | `esriFieldTypeString` | `UNIDAD` | 200 |
| `tipo_unidad` | `esriFieldTypeString` | `TIP_UNIDAD` | 30 |
| `litologia` | `esriFieldTypeString` | `LITOLOGIA` | 120 |
| `descrip` | `esriFieldTypeString` | `DESCRIP` | 500 |

En esos ocho descriptores `domain=null`; no se anuncia `nullable`. Se conserva el
desconocido y no se infiere nulabilidad, significado de códigos o unidades físicas
del campo llamado `unidad`. No se convirtieron atributos en variables científicas.

Capacidades **anunciadas en esta respuesta**, no probadas funcionalmente:

- `maxRecordCount=2000`, límite por consulta, no conteo total de entidades.
- `supportedQueryFormats="JSON, geoJSON, PBF"`.
- `capabilities="Map,Query,Data"`.
- `advancedQueryCapabilities.supportsPagination=true`; no se ejecutó paginación.
- `currentVersion=11.2` es versión técnica declarada, no edición geológica demostrada.

La evaluación final midió **6.895.353 bytes** de pico Python trazado y **2,5149 s**
en el proceso acotado. Es una observación local, no un límite universal de RSS.
El archivo y los cinco controles mantuvieron hashes/tamaños/identidades/mtime
antes y después de cada inspección real. El primario no se usó como fixture de tests.

## 26. Pruebas, restricciones y siguiente incremento GIS

Se añaden **25 pruebas sintéticas** en `tests/test_inspeccion_arcgis_presupuesto.py`.
Comprueban el conteo contra árboles inventados y 200 árboles aleatorios reproducibles,
JSON grande, representaciones secundarias extensas, presupuestos de documento y
esenciales independientes, profundidad/cardinalidad/cadenas, duplicados críticos
tardíos y escapados, truncamiento, codificación, números no finitos, error ArcGIS,
ausencias, OID, distinción de CRS, cancelación, inmutabilidad y determinismo.
Incluyen **131.072 nodos admitidos y el siguiente rechazado antes del parser**, y
una medición de regresión de memoria próxima al límite, inferior a 32 MiB.

La prueba previa de agotamiento global conserva su ID y aserción de rechazo antes
del parser; su fixture pasa de 10.000 a 12.000 objetos (**132.141 nodos**). Con
10.000 cabía en el presupuesto real y solo agotaba la heurística antigua: mantener
ese rechazo habría perpetuado el defecto. No se relajó el control ni se eliminaron
pruebas anteriores. La última ejecución focalizada fue **103 aprobadas, 0 fallidas,
0 errores, 17,133 s**: 78 anteriores y 25 nuevas.

Siguen pendientes definiciones autoritativas de CRS, unidades por ámbito, datum/ejes,
operaciones de transformación, diccionario geológico, licencia/atribución, edición,
precisión, cobertura y semántica de códigos. `copyrightText` está vacío; no se
infiere permiso de reutilización/redistribución. Tampoco hay prueba funcional de
consultas/paginación, completitud, identidad estable al republicar o calidad/topología
de geometrías. Falta el primario histórico de servicio; no se fabricó contexto
validado ni se afirmó que la publicación siga sin cambios.

El archivo usa **131.042 de 131.072 nodos**, margen de solo 30: una respuesta futura
ligeramente distinta puede volver a rechazarse. El procesamiento sigue materializando
un árbol acotado; no promete memoria constante, aceptación de todo ArcGIS o plazo
de pared universal. Las pruebas trazadas no sustituyen límites del sistema operativo.
No se ampliará automáticamente el presupuesto ante otra respuesta.

**Dictamen: APTO CON RESTRICCIONES.** Existe base técnica para revisar un diseño
vectorial separado, con origen, representación y salida diferenciados, identidad,
filtros, orden/paginación, fin, cambios de publicación, límites y manifestación de
completitud explícitos. Ese diseño requerirá revisión antes de implementar o
autorizar red. El resultado A se limita a metadatos esenciales de esta evidencia:
no confirma datos geológicos ni autoriza recuperar entidades, `/query` o `/export`.

## 27. Cierre y verificación del PASO 82-D

Se ejecutó de nuevo, con Python **3.15.1** de `.venv`:

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -B -m pip check
git diff --check
git status --short
```

```text
Ran 1164 tests in 103.282s
OK
No broken requirements found.
```

**1.164 aprobadas, 0 fallidas, 0 errores, 0 omitidas: 1.139 anteriores y 25 nuevas.**
La comparación de IDs con el registro del PASO 82-C confirmó las 1.139 previas,
sin faltantes ni duplicadas. Se documenta expresamente el ajuste de una fixture
anterior en la sección 26. Las ejecuciones focalizadas no se suman al total.
HTTPX sigue en **0.28.1**, SQLite en **3.53.4**; no se instaló ninguna dependencia.
No hubo cambios funcionales después de esta ejecución.

Se comprobaron también UTF-8, sintaxis de Python, ausencia de definiciones
duplicadas por ámbito, whitespace y enlaces locales/anclas. El archivo nuevo
se revisó por separado, porque `git diff --check` no lo incluye sin registrar.
Se conservaron los textos históricos del PASO 82-C, actualizando únicamente las
leyendas de estado para distinguir antecedentes del resultado nuevo.

Archivos modificados en este paso:

- `src/spica/adquisicion/inspeccion_arcgis/inspector.py`: conteo léxico de nodos y
  tratamiento separado de referencia espacial de origen.
- `src/spica/adquisicion/inspeccion_arcgis/modelos.py`: solo documentación de la
  medida; mismos tipos, campos y topes.
- `tests/test_inspeccion_arcgis_extensa.py`: fixture de agotamiento global ajustada.
- `tests/test_inspeccion_arcgis_presupuesto.py`: **nuevo**, 25 pruebas sintéticas.
- Este informe y `docs/matriz_interoperabilidad_ingemmet.md`: conservan los cambios
  pendientes del PASO 82-C y añaden diagnóstico y evidencia E-06.

Estado final de Git:

```text
 M docs/matriz_interoperabilidad_ingemmet.md
 M docs/validacion_metadatos_ingemmet_paso82.md
 M src/spica/adquisicion/inspeccion_arcgis/inspector.py
 M src/spica/adquisicion/inspeccion_arcgis/modelos.py
 M tests/test_inspeccion_arcgis_extensa.py
?? tests/test_inspeccion_arcgis_presupuesto.py
```

Rama `feature/suadc-http`, HEAD **`0210ff3`**, sin commits/push. No se modificaron
transporte/políticas HTTP, conectores, contratos RAW, `main.py`, `.gitignore`,
dependencias o `.venv`. Ningún byte del primario se incorporó a Git o a una fixture.

Cierre de integridad: **2026-10-30T20:52:18.744081Z**. El inventario final de los
seis archivos originales coincide con el inicial en tamaño, hash, identidad y
mtime. Los cinco controles no se reescribieron; su resultado histórico incompleto
del PASO 82-C permanece intacto. `cierre_integridad.json` y los informes de este
paso están en el directorio diagnóstico separado de la sección 22, nunca en el
directorio primario. Los auxiliares de ejecución/registros de tests quedan fuera
de Git; no se generaron copias completas innecesarias del cuerpo.

**Cero conexiones, cero GET y cero accesos operativos.** Las guardias revisadas
no registran intentos de red, mutación del primario o acceso al árbol operativo.
No se abrieron RAW, staging o SQLite operativos; las pruebas existentes de
almacenamiento y SQLite usan temporales aislados. No hubo migraciones operativas,
instalaciones, activación de QA/QC científico, recuperación de entidades o cálculos
geológicos. Este cierre describe operaciones realizadas y guardias revisadas;
no constituye una auditoría física del almacén operativo, que no se abrió.

Se espera revisión del resultado **A**, del dictamen **APTO CON RESTRICCIONES** y
de la propuesta de siguiente incremento antes de continuar.
