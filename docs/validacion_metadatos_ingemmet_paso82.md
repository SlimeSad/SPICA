# PASO 82 — Ensayo de metadatos ArcGIS REST de INGEMMET

**Dictamen: REQUIERE CORRECCIONES antes de validar la capa o avanzar a entidades.**
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
