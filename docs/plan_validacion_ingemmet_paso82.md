# Propuesta de PASO 82 — Validación controlada de metadatos INGEMMET

Estado: **plan pendiente de revisión y autorización; no ejecutado**.
No constituye permiso de red ni habilita un conector operativo.

Se apoya en el [expediente del servicio](expediente_ingemmet_geologia_50k.md)
y la [matriz de interoperabilidad y requisitos GIS](matriz_interoperabilidad_ingemmet.md).

## 1. Objetivo y frontera

Comprobar si desde la infraestructura de SPICA se pueden obtener metadatos
públicos coherentes del servicio `SERV_GEOLOGIA_50K_INTEGRADA` y de la capa
`Litologia`, ID `7`. La accesibilidad y las propiedades siguen sin comprobarse.

El piloto no solicitará entidades, geometrías, conteos, IDs, filtros espaciales,
exportaciones, mapas, teselas, ficheros adjuntos o páginas vectoriales. No ejecutará
HEAD, GET condicional, autenticación, transformaciones ni consultas de datos.

Las únicas rutas candidatas, suministradas en E-01, son:

- [R-01: metadatos del servicio](https://geocatminnube.ingemmet.gob.pe/arcgis/rest/services/SERV_GEOLOGIA_50K_INTEGRADA/MapServer).
- [R-02: metadatos de la capa 7](https://geocatminnube.ingemmet.gob.pe/arcgis/rest/services/SERV_GEOLOGIA_50K_INTEGRADA/MapServer/7).

No se construirán otras rutas ni se seguirán enlaces anunciados por la respuesta.
El parámetro de formato `f=json` se propone para esas dos rutas, sujeto a revisión
de la especificación y aprobación previa; **su aceptación no está comprobada**.
No se utilizarán endpoints de consulta de entidades ni parámetros adicionales.

## 2. Etapa A — Preparación offline anterior a cualquier acceso

1. Comprobar Git y el registro del PASO 81; conservar los avances y cambios ajenos.
2. Resolver con documentación primaria o revisión humana suficiente si las rutas,
   formato propuesto, acceso sin cuenta y conservación de metadatos son admisibles.
   No resolver la duda mediante solicitudes exploratorias adicionales sin permiso.
3. Preparar una validación mínima de metadatos JSON como herramienta acotada del
   piloto, reutilizando `ClienteHTTP`; no un conector GIS completo. Revisar su diseño
   y cualquier cambio necesario antes de ejecutarlo. Este paso 81 no la implementa.
4. Ejecutar las pruebas sintéticas de la sección 4 antes de solicitar acceso real.
5. Presentar para autorización las dos URLs exactas y el único parámetro previsto,
   origen, límites, timeouts, número de GET y política de conservación.
6. Proponer un directorio temporal privado aislado fuera de Git y del almacenamiento
   operativo para la evidencia. Revisar ruta, permisos heredados, espacio y limpieza;
   no crearlo como almacén permanente ni inicializar/migrar RAW.

Datos todavía necesarios para aprobar la etapa real: confirmación del formato y
condiciones de consulta, autorización de esas solicitudes, ubicación temporal y
período de retención, política para errores de aplicación e informe de pruebas
offline satisfactorio. Se necesita autorización separada si esos límites cambian.
No se infiere licencia abierta ni permiso de redistribución de una mera respuesta.

## 3. Presupuesto propuesto para una futura etapa B autorizada

| Parámetro | Propuesta revisable |
|---|---|
| Finalidad | Solo metadatos de servicio y capa, sin datos vectoriales |
| Solicitudes | Máximo dos GET secuenciales: uno a R-01 y otro a R-02 |
| Intentos | Un intento por ruta; `PoliticaReintentos(max_intentos=1)` |
| Orden | Servicio primero; capa únicamente si la respuesta es coherente y la lista identifica la capa 7; si falta o contradice, detener sin solicitar otra capa |
| Origen | Únicamente `https://geocatminnube.ingemmet.gob.pe`, autorizado para ese piloto; no ampliar listas persistentes |
| Transporte | `ClienteHTTP.get()` existente; sin segundo cliente ni solicitudes directas por otra librería |
| TLS / redirecciones | TLS verificado, redirecciones desactivadas; no aceptar otro host, esquema o ruta |
| Proxies / autenticación | Mantener proxies del entorno desactivados; sin credenciales, sesiones o CAPTCHA |
| Respuesta máxima | 1.048.576 bytes por GET; hasta 2.097.152 bytes de cuerpos en total, sin contar sobrecarga HTTP ni memoria del análisis JSON |
| Timeouts | Conexión 10 s, lectura 30 s, escritura 30 s, pool 10 s, configurados explícitamente; no son un plazo total garantizado de la operación |
| Compresión / parcial | Mantener política existente: pedir identidad y rechazar compresión incompatible, HTTP 206 y redirecciones |
| Ejecución | Secuencial, cancelable según mecanismo existente, sin tareas automáticas |
| Conservación | Solo evidencia temporal privada autorizada; fuera de Git, RAW, staging y SQLite operativos |

Si la respuesta supera 1 MiB, detener; no aumentar límites ni pasar automáticamente
a streaming. Si una ruta falla, no repetir ni intentar rutas alternativas. La
segunda solicitud no se realiza si la primera exige revisar el acceso o la identidad.

El cuerpo de metadatos pequeño puede procesarse con `get()` dentro de su límite.
Esto no autoriza cargar colecciones grandes en RAM. La validación JSON necesitará
sus propios límites de complejidad/profundidad/campos y manejo de errores; el
límite de bytes no equivale a un límite exacto de memoria del árbol decodificado.

## 4. Pruebas sintéticas previas al acceso real

Usar `httpx.MockTransport`, JSON inventado y memoria/directorios temporales
aislados. Ninguna fixture se presentará como respuesta real de INGEMMET.

| Grupo | Escenarios mínimos | Resultado esperado |
|---|---|---|
| Identidad | Servicio válido inventado con capa 7, capa ausente, ID/nombre divergentes | Solo permitir segunda solicitud en el caso coherente; no elegir otro ID automáticamente |
| Formato | JSON objeto válido, JSON truncado, HTML/login con HTTP 200, lista o escalar inesperados | Clasificación explícita; no aceptar éxito por HTTP 200/MIME solamente |
| Error de aplicación | Objeto de error ArcGIS con HTTP 200 o cuerpo inesperado | Registrar diagnóstico seguro y detener, sin promover a metadatos válidos |
| Esquema | Campos conocidos presentes, ausentes, tipos equivocados, nombres nuevos | Conservar desconocidos/diferencias; no rellenar valores desde el expediente |
| CRS | Par declarado, identificadores distintos, solo WKT, referencia ausente | Registrar el objeto recibido y la diferencia; no reproyectar ni asignar datum/ejes |
| Capacidades | JSON/GeoJSON/PBF anunciados, sin paginación, límites distintos o ausentes | Registrar como anuncios; no ejecutar formatos, filtros ni paginación |
| Tamaño | Justo en el límite, mayor que el límite, Content-Length falso/ausente | Contar bytes reales; fallo sin ampliar presupuesto |
| Seguridad | Otro origen, TLS fallido, 3xx, 206, compresión, credenciales inesperadas | Rechazar sin seguir redirecciones, autenticar o relajar controles |
| Errores | 401, 403, 404, 429, 5xx, timeout, conexión interrumpida, cancelación | Un intento por ruta; sin reintentos ni segunda solicitud tras anomalía |
| Complejidad | Profundidad/cantidad de elementos excesivas, claves duplicadas, números no admitidos | Fallo controlado; sin ejecutar expresiones ni afirmar un esquema válido |
| Evidencia | Hash del cuerpo exacto, ruta temporal segura, error de escritura y limpieza | No sobrescribir evidencia, informar residuos; SHA-256 no acredita autoría ni completitud vectorial |
| Aislamiento | Bloqueo de red real, RAW/staging/SQLite operativos sin acceso | Pruebas reproducibles y sin nuevas adquisiciones operativas |

Los valores alternativos son sintéticos y no prueban propiedades del servidor real.
Si se desarrolla código del piloto en el PASO 82, ejecutar entonces la suite completa
y `pip check` con `.venv`, además de las pruebas específicas y comprobaciones Git.

## 5. Comprobaciones de la respuesta real, solo tras autorización

Para cada GET autorizado, conservar en el entorno temporal aprobado:

- URL/ruta y parámetros públicos exactos, fecha UTC y orden/intento real.
- Estado HTTP, tamaño observado y declarado cuando esté disponible, hash del
  cuerpo original y método de conservación. No atribuir al servidor el hash local.
- Resultado de transporte, sintaxis y esquema, incluyendo faltantes y diferencias.
- Referencia cruzada servicio/capa, nombre e ID, tipo de geometría y objeto de
  referencia espacial completo cuando consten.
- Lista real de campos, tipos y propiedades declaradas; OID y otros identificadores
  solo cuando estén explícitamente definidos, sin inferir estabilidad histórica.
- Formatos/capacidades/límites y su ubicación exacta en el JSON del servicio o capa.
  No copiar automáticamente un anuncio del servicio a todas las capas.
- Metadatos de publicación, autoría, versiones y derechos **solo si aparecen**,
  distinguiendo el nombre de una propiedad de un permiso jurídicamente suficiente.

La conservación de cabeceras debe limitarse a valores técnicos públicos aprobados
y realmente expuestos por el cliente. No serializar `RespuestaHTTP.cabeceras`
completa: puede contener cookies u otros datos sensibles. Si un valor no está
disponible, registrar desconocido; no inventarlo ni cambiar el cliente sin revisión.

Una futura lectura física del cuerpo guardado permitirá comprobar tamaño/SHA-256
de esa evidencia temporal, sin usar el RAW operativo. Si no se guarda o relee, el
informe deberá decir exactamente que se calculó en memoria, sin alegar verificación
física. Ni una ni otra modalidad certifica autenticidad documental.

No marcar el producto, formatos, entidades o colección como adquiridos/verificados
por obtener metadatos. «Confirmar CRS» en este piloto significa contrastar la
declaración recibida y conservarla; no certificar datum, transformación o exactitud
posicional de geometrías que todavía no se han obtenido.

## 6. Criterios de detención y salida

Detener ante identidad distinta, origen/ruta no previstos, redirección, necesidad de
autenticación, errores HTTP/TLS, exceso de tamaño, JSON de error, esquema insuficiente
o contradicciones con E-01. Conservar la evidencia permitida y diagnosticar; no
corregir el expediente por suposición, repetir descargas o elegir otra capa.

Salidas posibles del piloto:

- **Metadatos obtenidos coherentes:** acceso puntual y anuncios comprobados en el
  alcance de las respuestas conservadas; vectores y funcionamiento de capacidades
  continúan pendientes.
- **Requiere revisión:** discrepancias, faltantes, restricciones o errores; sin
  reparación, ampliación de consultas o incorporación operativa automática.
- **No ejecutado:** falta autorización o preparación suficiente; no se interpreta
  como indisponibilidad del servicio institucional.

El informe del PASO 82 deberá incluir peticiones efectivas, estados, bytes, hashes
y alcance de su comprobación, propiedades observadas, diferencias, condiciones de
uso, residuos temporales y Git. Cualquier autorización para datos vectoriales,
catálogo operativo, RAW permanente o análisis espacial pertenecerá a otro incremento.

## 7. Estado al cerrar el PASO 81

Solo se ha diseñado este plan. No se ha preparado un cliente con el origen
candidato, hecho una petición, creado evidencia remota ni escrito en RAW/staging/
SQLite operativos. No se implementó el validador del piloto ni un conector.
El PASO 82 espera revisión y aprobación independiente.
