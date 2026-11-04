# PASO 83-D: protocolo revisado del primer piloto de atributos

## 1. Estado y relación con los pasos anteriores

**NO EJECUTADO. BLOQUEADO. PENDIENTE DE REVISIÓN Y AUTORIZACIÓN EXPRESA.**
Propuesta documental de 2026-11-04, no ejecutor ni configuración de red. Conserva
los siete parámetros y los controles del [protocolo 83-B](protocolo_piloto_arcgis_paso83b.md)
y de la [simulación 83-C](simulacion_piloto_arcgis_paso83c.md). No modifica su código
ni reclasifica sus resultados sintéticos como evidencia de INGEMMET.

Finalidad eventual: observar un único OID como máximo, sin geometría, para una
comprobación técnica puntual de atributos. No adquirir una colección, inventario
de IDs, muestra geológica representativa o prueba de completitud.

## 2. Evaluación de compatibilidad documental

La [matriz de alternativas](alternativas_adquisicion_ingemmet_paso83d.md) distingue
la referencia general de Esri (D83D-01), anuncios históricos de capa E-06 y prueba
funcional. La documentación Esri se identifica por el encargo, **sin nueva lectura
externa del texto completo**. La combinación no presenta contradicción nominal
con las funciones allí referidas; no constituye una certificación íntegra de su
sintaxis, condiciones por versión o funcionamiento en INGEMMET.

| Parámetro cerrado | Función pretendida / correspondencia nominal | Evidencia específica y límite |
|---|---|---|
| `f=json` | Solicitar JSON | E-06 anuncia JSON; operación concreta no ejercida |
| `where=1=1` | Selección sin restricción selectiva de entidades, constante fija | No permite SQL de usuario. No limita por sí sola filas y su aceptación no está probada |
| `outFields=objectid` | Un solo atributo OID | E-06 registra ese descriptor; no comprueba que la selección efectiva respete outFields |
| `returnGeometry=false` | Solicitar ausencia de geometría | Función referida por Esri; respuesta específica no probada. Rechazar incluso `geometry:null` conforme al contrato sintético |
| `resultOffset=0` | Inicio de la selección; sin página siguiente | E-06 anuncia `supportsPagination=true`; no demuestra funcionamiento del offset |
| `resultRecordCount=1` | Pedir una fila como máximo | Función referida por Esri y anuncio de paginación; no acredita que esta combinación se respete o no tenga excepciones |
| `orderByFields=objectid ASC` | Orden solicitado para la selección | OID documentado; soporte específico de ordenación no establecido en el resumen local. Una respuesta de una fila no lo demostraría |

`maxRecordCount=2000` es un anuncio histórico de límite, no total ni garantía de
que solicitar uno devuelva uno. `currentVersion=11.2` es versión técnica histórica,
no edición de datos ni prueba de compatibilidad de cada opción. No se confunde
la falta de una afirmación en el resumen con una capacidad inexistente del servidor.

## 3. Destino y alcance cerrados propuestos

Institución objetivo INGEMMET, producto referido Mapa Geológico Integrado del
Perú a escala 1:50.000; servicio `SERV_GEOLOGIA_50K_INTEGRADA`, capa `7 — Litologia`.
URL candidata exacta, **sin verificación funcional nueva**:

```text
https://geocatminnube.ingemmet.gob.pe/arcgis/rest/services/SERV_GEOLOGIA_50K_INTEGRADA/MapServer/7/query
```

Los parámetros son exactamente los siete de la sección 2, sin parámetros
adicionales ni ausentes. No incluir `objectIds`: no hay un identificador de entidad
acreditado. No añadir `returnIdsOnly`, conteos, filtros espaciales, outSR,
estadísticas, callback, tokens o expresiones SQL arbitrarias. No cambiar método,
host, capa, servicio o ruta. No realizar HEAD ni GET previo para averiguar soporte.

### Bloqueo del máximo de una entidad

Pedir una fila puede formularse sin conocer OID y sin consulta preliminar, pero
su efectividad remota no está acreditada por la evidencia local. El rechazo de
un cuerpo con más de una entidad ocurre **después de recibirlo**; no garantiza
que solo se haya transferido una. La cota de 64 KiB tampoco lo garantiza.

Antes de ejecutar, se necesita evidencia documental aplicable al servicio/capa y
a esta combinación, y revisar si ofrece una garantía razonable del límite. El
anuncio de paginación reduce incertidumbre sobre la capacidad anunciada, pero
no sustituye esa evaluación. Si no puede justificarse, no se ejecuta el piloto
bajo este alcance. No se cambia silenciosamente a un ensayo con más entidades;
cualquier alcance distinto exige otra decisión. No se inventa un OID real.

## 4. Condiciones previas y presupuestos

| Control | Condición propuesta; no activada |
|---|---|
| Permisos | Acreditar consulta automática del atributo y conservación privada de evidencia para esta capa; demás usos siguen fuera de alcance |
| Autorización | Expresa, posterior, para endpoint, siete parámetros, presupuesto y ubicación de evidencia exactos |
| Operaciones | Un único GET, un intento; cero reintentos, paginación, fallback o consultas preliminares |
| Cuerpo | Máximo 65536 bytes efectivos, sin confiar solo en Content-Length; no elevar el presupuesto tras error |
| Entidades | Máximo una entidad y un atributo `objectid`, cero geometrías; recepción mayor obliga a revisión y no autoriza su uso |
| TLS y origen | HTTPS, certificado verificado y origen exclusivo del host candidato; sin redirecciones, autenticación ni proxies del entorno |
| Representación | JSON, `Accept-Encoding: identity`; rechazar compresión, MIME inesperado y HTTP 206 |
| Transporte futuro | Reutilizar `ClienteHTTP.get()`, límite de respuesta 65536 y `PoliticaReintentos(max_intentos=1)` tras implementar/revisar un ejecutor autorizado; nunca activar el simulador |
| Timeouts previstos | Conexión 10 s, lectura/escritura 30 s, pool 10 s; no son un plazo total garantizado |
| Parser | Profundidad 16, nodos 10000, listas/propiedades 64, cadenas 4096; política decimal exacta, token máximo 256 y exponente absoluto 4096 |
| Evidencia | Privada, destino y retención previamente aprobados fuera de Git/RAW/staging/SQLite operativos; publicación exclusiva y comprobación física de lo escrito |
| Espacio | Propuesta heredada: mínimo 16 MiB libres, sin reserva ni garantía futura; error de escritura detiene |
| Ejecución | Secuencial y cancelable; sin operaciones adicionales automáticas |

Los límites del cuerpo no prometen cota de cabeceras, tráfico TLS, RSS o tiempo
total. No se exige resolver derechos de redistribución para un piloto que no
redistribuye; esos usos permanecen pendientes y fuera de su autorización.

## 5. Evidencia primaria y validación prevista

El escritor de fixtures del 83-C es efímero, se limpia al salir y solo acepta
procedencia sintética. **No se reutiliza directamente para evidencia institucional**
ni se crea un `EscenarioSintetico` con una respuesta real. Falta diseñar y revisar
la conservación institucional privada, su retención y manejo de interrupciones.
No se usa RAW operativo para resolver ese faltante.

Conservar únicamente los bytes originales efectivamente disponibles dentro del
presupuesto, sin reserializarlos. Registrar identidad técnica del ensayo real
separada de los IDs sintéticos, endpoint y parámetros aprobados exactos,
inicio/fin UTC, código HTTP, intentos, longitud declarada disponible, bytes reales,
tipo/codificación permitidos, SHA-256 calculado y versión de código/políticas.
No registrar credenciales, cookies o cabeceras arbitrarias. Fecha de licencia,
edición, cobertura o identificadores desconocidos no se inventan.

Cerrar/reabrir el archivo y contrastar bytes/tamaño/hash antes de declarar su
verificación física. Si hay bytes parciales, el hash solo acredita esos bytes;
no convierte recepción incompleta en completa ni es firma institucional.
Si `ClienteHTTP` solo devuelve un error, registrar únicamente datos disponibles;
no afirmar conservación de un cuerpo/hash ni repetir el GET para obtenerlo.

Validación propuesta: HTTP 200 completo, longitud coherente cuando exista, MIME y
codificación admitidos; JSON íntegro sin duplicados/NaN, sin error ArcGIS;
`features` con cero o una entidad, esquema acotado y OID entero exacto válido.
Solo un resultado de una entidad satisface el objetivo mínimo. `fields`, capa o
CRS ausentes se registran como ausentes; no se rellenan desde metadatos para
afirmar recepción. Una identidad declarada contradictoria se rechaza.

`exceededTransferLimit` se conserva como true, false o ausente. True con una
entidad informa selección parcial y termina sin otra operación; false/ausencia
tampoco prueban completitud institucional. Vacío con continuación es contradictorio.
La respuesta sin geometría no prueba capacidad geométrica, CRS de salida o calidad
geológica. Los CRS de origen y extensión históricos no se trasladan a una salida.

## 6. Detención, interpretación y revisión humana

No ejecutar si falta algún bloqueo previo: ruta/parámetros no acreditados,
derechos mínimos pendientes, máximo remoto no justificable, ubicación/retención
no aprobadas, ejecutor institucional no revisado o autorización ausente.

Si posteriormente se autoriza un ensayo, detenerlo ante destino diferente,
TLS/autenticación, redirección, HTTP inesperado/206, compresión, exceso de bytes,
Content-Length incoherente, truncamiento, error ArcGIS/JSON, cancelación, error
de persistencia, más de una entidad, geometría, atributos inesperados u OID/capa
incompatibles. Sin reintentos, corrección mediante borrados ni cambio de parámetros.
Conservar solo la evidencia disponible bajo una política previamente aprobada.

- **No ejecutado:** estado actual; no afirma inexistencia de servicio o datos.
- **Vacío coherente:** distinto de error, pero objetivo no demostrado; revisión.
- **Recepción/estructura fallida o limitada:** no es resultado válido del objetivo.
- **Éxito técnico limitado futuro:** una entidad/OID sin geometría, bajo alcance
  autorizado y con evidencia primaria físicamente comprobada. No prueba respeto
  general de parámetros por una coincidencia puntual, paginación, colección,
  estabilidad de OID, licencia, topología o validez científica.

Todo resultado requerirá revisión humana antes de otra etapa. Sin almacenamiento
RAW operativo, adquisición GIS, geometrías, procesamiento científico o QA/QC.
Los permisos y aclaraciones están en la [auditoría documental](derechos_uso_ingemmet_paso83d.md).
El dictamen del PASO 83-D es **APTO CON RESTRICCIONES para revisión documental**,
no autorización del GET ni selección de una vía operativa.
