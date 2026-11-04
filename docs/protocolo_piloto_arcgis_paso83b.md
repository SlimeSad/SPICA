# PASO 83-B: protocolo propuesto de ensayo institucional mínimo

**NO EJECUTADO. PENDIENTE DE REVISIÓN Y AUTORIZACIÓN EXPRESA.**
Este documento no crea un cliente, no configura un origen ni autoriza solicitudes.

## 1. Evidencia disponible y finalidad

El [expediente](expediente_ingemmet_geologia_50k.md) contiene la referencia aportada
de `SERV_GEOLOGIA_50K_INTEGRADA`, capa Litologia 7. La
[matriz, sección 10](matriz_interoperabilidad_ingemmet.md#10-diagnóstico-y-validación-offline-del-paso-82-d)
registra E-06: inspección offline de metadatos previamente conservados, campo
`objectid`, geometría anunciada Polygon, campos y capacidades anunciadas. Eso no
comprueba consultas de entidades, estabilidad de IDs, paginación ni derechos.
No se volvió a abrir el archivo de evidencia.

Finalidad del ensayo futuro: comprobar puntualmente una respuesta de **como máximo
un atributo OID de una entidad**, sin geometrías ni adquisición de colección.
No se busca un inventario de IDs ni una primera página de una descarga automatizada.

## 2. Elección entre IDs y atributos

| Alternativa | Ventaja | Riesgo y decisión |
|---|---|---|
| `returnIdsOnly=true` | Evitaría geometrías y atributos amplios si el servicio lo admite | Podría devolver una lista de tamaño desconocido, sin respetar el tamaño de página esperado. No se conoce el total ni su funcionamiento aquí. **No es la primera opción** |
| OID como único atributo, `returnGeometry=false`, tamaño solicitado 1 | Permite intentar una respuesta mínima y observar un identificador, si los parámetros se aceptan | El límite y la forma del sobre no están comprobados; controlar bytes reales y detener si devuelve más de una entidad. **Propuesta preferida** |

Si el servidor no admite lo propuesto, se detiene. No se cambia automáticamente a
IDs, conteo, otra capa, otra ruta, offset siguiente o geometrías.

## 3. Ruta candidata exacta, todavía sin verificación funcional

R-P1, solo texto sujeto a validación documental y autorización posterior:

```text
https://geocatminnube.ingemmet.gob.pe/arcgis/rest/services/SERV_GEOLOGIA_50K_INTEGRADA/MapServer/7/query
```

Se propone añadiendo el nombre de operación ArcGIS a R-02 del expediente. **No
se presenta como endpoint operativo comprobado**: falta acreditar su correspondencia
con el servicio específico mediante documentación aplicable o revisión autorizada.
No se accede a esta ruta en el PASO 83-B y no se prueba mediante HEAD u otro método.
Si no se puede acreditar la ruta, no se solicita autorización de ejecución todavía.

Parámetros propuestos, lista cerrada para revisión:

| Parámetro | Valor literal propuesto | Estado |
|---|---|---|
| `f` | `json` | JSON anunciado; aceptación de esta operación no comprobada |
| `where` | `1=1` | Expresión declarativa candidata, sin evaluación local ni prueba remota |
| `outFields` | `objectid` | Campo OID documentado en metadatos; selección efectiva no comprobada |
| `returnGeometry` | `false` | Exclusión solicitada, por verificar en la respuesta |
| `resultOffset` | `0` | No acredita soporte real de paginación |
| `resultRecordCount` | `1` | Límite solicitado, no garantía; rechazar más de una entidad |
| `orderByFields` | `objectid ASC` | Orden solicitado; una sola entidad no prueba ordenación estable |

No se incluyen `returnIdsOnly`, `objectIds`, conteos, filtros espaciales, outSR,
estadísticas, tokens, callbacks, exportaciones ni parámetros adicionales. No se
deducen códigos desconocidos. La lista final debe aprobarse íntegramente antes
de materializar una petición.

## 4. Presupuesto propuesto, no autorizado ni configurado

| Control | Propuesta |
|---|---|
| Solicitudes | **Un único GET**, un intento; máximo una respuesta/cuerpo |
| Reintentos/paginación | Desactivados; no segunda solicitud aunque se anuncie continuación |
| Cuerpo máximo y total | **65536 bytes (64 KiB)**, contados realmente; no usar 8 MiB del prototipo |
| Alcance del presupuesto | Bytes de cuerpo, sin prometer cota de cabeceras, tráfico TLS o RSS |
| Entidades/atributos | Máximo una entidad y un atributo (`objectid`), cero geometrías presentes |
| JSON propuesto | Profundidad 16, 10000 nodos, listas 64, propiedades 64, cadenas 4096; adaptar solo tras revisión previa de fixtures del sobre esperado |
| Transporte futuro | Reutilizar `ClienteHTTP.get()` y `PoliticaReintentos(max_intentos=1)`; no un segundo cliente |
| Seguridad | TLS verificado, sin redirecciones, sin autenticación, proxies del entorno desactivados, codificación identity; rechazar HTTP 206/compresión |
| Timeouts | Conexión 10 s, lectura 30 s, escritura 30 s, pool 10 s; no equivalen a plazo total garantizado |
| Ejecución | Secuencial y cancelable, sin ejecución automática posterior |
| Evidencia | Directorio privado temporal aprobado fuera de Git/RAW/staging/SQLite operativos; ruta y período de retención todavía pendientes |
| Espacio previo | Propuesta de mínimo 16 MiB libres, sin reserva; fallo de escritura obliga a detener sin otra descarga |

El límite de 64 KiB reduciría el límite existente para esa instancia; no modifica
configuración actual. Si el servidor ignora `resultRecordCount`, el transporte
detiene al exceder bytes; si llega un cuerpo menor con más entidades, el análisis
lo rechaza. No se amplía el presupuesto para intentar hacerlo funcionar.

## 5. Condiciones previas obligatorias

1. Revisar la matriz de permisos siguiente y acreditar la consulta y conservación
   previstas, incluida la vinculación de términos al producto/capa.
2. Aprobar la ruta exacta, los siete parámetros, un GET y sus presupuestos.
3. Diseñar y probar offline el manejo del sobre mínimo de atributos. El validador
   Polygon actual exige CRS/tipo y descriptores; una respuesta sin geometría podría
   omitirlos. **No rellenarlos desde metadatos para fingir que fueron recibidos.**
   No existe todavía ese ejecutor/validador mínimo preparado para el piloto.
4. Revisar seguridad y capacidad de la ubicación privada de evidencia; aprobar
   retención y política de respuestas inesperadas sin sobrescrituras.
5. Ejecutar regresiones y comprobar Git; el piloto no incorpora RAW ni SQLite.
6. Obtener autorización expresa de ejecución; este protocolo no la sustituye.

## 6. Conservación primaria y validación futura

Guardar los bytes originales completos dentro del presupuesto, sin reserializar.
Registrar URL y parámetros aprobados exactos, ID técnico del ensayo, inicio/fin UTC,
estado HTTP, un intento, longitud declarada si existe, tamaño observado, SHA-256,
versión de código y política numérica. No inferir identidad científica permanente.

Cabeceras solo mediante lista técnica permitida: tipo de contenido, longitud y
codificación efectivamente disponibles. Excluir cookies, autorización y metadatos
sensibles; no imprimir cuerpos de error. Cerrar/reabrir el archivo temporal y
comparar tamaño/hash antes de afirmar verificación física de esa evidencia. No
atribuir una firma institucional al hash calculado localmente.

Si `ClienteHTTP` rechaza la respuesta antes de entregar cuerpo o cabeceras, registrar
únicamente el error técnico y la evidencia realmente disponibles. No afirmar que
se conservó un cuerpo o se calculó su hash; no modificar el cliente ni realizar
otro GET para recuperar esa información. El ensayo queda detenido para revisión.

Validar sintaxis completa, duplicados, errores ArcGIS con HTTP 200, esquema mínimo,
OID entero exacto, límites y ausencia de geometría. Registrar campos/CRS ausentes
como ausentes. Propuesta numérica: `DECIMAL_EXACTA`; el OID continúa siendo int.
No se declaran cobertura, total, completitud remota ni instantánea estable. Un
`exceededTransferLimit=true` puede indicar que la selección es solo parcial:
registrarlo y terminar tras esa única respuesta, sin solicitar otra página.

## 7. Detención, éxito y fracaso

Detener por ruta/origen distintos, autenticación requerida, TLS fallido, redirección,
206, compresión, error HTTP/ArcGIS, MIME inesperado, exceso de bytes/estructura,
JSON truncado/ambiguo, más de una entidad, OID inválido, geometría presente, campos
ajenos no aprobados, incoherencia, error de persistencia o cancelación. No borrar
evidencia para reparar, reintentar o cambiar parámetros.

Una respuesta mínima sin entidades no demuestra que la capa esté vacía: queda
**requiere revisión**. Una respuesta con más datos de los autorizados tampoco se
promueve a evidencia utilizable del objetivo, aunque se conserve privadamente.

**Éxito limitado propuesto:** un GET autorizado con respuesta coherente de una
entidad y su OID, sin geometría, bajo límites y evidencia primaria verificada.
Solo acredita esa observación puntual y capacidad ejercida; no paginación, lista
completa, integridad de geometrías, estabilidad de OID, licencia o validez científica.

**Fracaso/revisión:** cualquiera de las anomalías anteriores o evidencia insuficiente.
**No ejecutado:** preparación, permisos o autorización pendientes; no significa
que el servicio no exista o carezca de datos. Si el servidor ignora un parámetro
y aun así devuelve casualmente una entidad, no se declara comprobado que lo respete.

## 8. Matriz de permisos y procedencia

Fuentes offline: expediente E-01, registros E-04/E-05/E-06 en el
[informe de metadatos](validacion_metadatos_ingemmet_paso82.md), matriz GIS y encargo
83-B. Se conserva su alcance histórico; no se reclasifica confianza documental.

| Uso | Evidencia disponible | Situación y requisito pendiente |
|---|---|---|
| Consulta de metadatos | Accesos puntuales anteriores autorizados y documentados | No es autorización general ni futura; términos de uso vinculados al servicio pendientes |
| Consulta de identificadores | Anuncios de consulta; ninguna prueba de entidades | Sin autorización para este paso; acreditar mecanismo/términos y pedir aprobación de un ensayo distinto si se elige |
| Consulta de atributos | Campo OID documentado en metadatos | Propuesta de esta sección; consulta efectiva y permiso específico pendientes |
| Consulta de geometrías | Tipo Polygon anunciado | No autorizada en el piloto propuesto; derechos y protocolo vectorial separado pendientes |
| Conservación interna | Conservación previa de metadatos bajo alcance específico | No extender a entidades; definir y aprobar retención privada del ensayo |
| Uso académico | Sin términos aplicables acreditados en el expediente | Desconocido; no inferir permiso por finalidad académica |
| Productos derivados | Sin licencia/método aplicable acreditados | Desconocido; requiere revisión de condiciones y atribución |
| Redistribución | Sin permiso aplicable acreditado | Desconocido; no publicar evidencia institucional o derivados por acceso público |

Referencia externa señalada por el usuario:

```text
https://geocatminapp.ingemmet.gob.pe/complementos/Descargas/Licencia.html
```

No consultada en esta etapa. Su contenido, versión/fecha, vigencia, alcance,
autoridad y vinculación con `SERV_GEOLOGIA_50K_INTEGRADA`/capa 7 permanecen pendientes.
No se cita un texto que no se leyó, no se afirma licencia abierta y tampoco se
deduce prohibición. El permiso del usuario para una operación y los derechos
institucionales de reutilización son evidencias diferentes.

## 9. Continuidad del PASO 83-C: simulación sin autorización

El [informe del PASO 83-C](simulacion_piloto_arcgis_paso83c.md) añade contratos y
un ejecutor exclusivamente sintético. Resuelve offline la preparación del sobre
mínimo de atributos señalada en la sección 5, sin modificar el validador estable
ni habilitar `ClienteHTTP`. No demuestra capacidades institucionales ni permisos.

Se mantiene la lista candidata de siete parámetros. **Pedir una fila y rechazar
localmente más de una no garantiza haber recibido como máximo una entidad.** Sin
ObjectID previamente acreditado ni evidencia aplicable de que el servicio respete
el límite propuesto, el piloto real permanece bloqueado. No se hace un GET previo
para averiguarlo, no se inventa un ObjectID y no se amplía el alcance.

El control de 64 KiB limita el cuerpo, no el número de entidades transferidas.
La sección 3 continúa siendo una propuesta no verificada funcionalmente. Los
permisos, retención de evidencia institucional y autorización de ejecución siguen
pendientes. No hay consultas reales a `/query` en el PASO 83-C.
