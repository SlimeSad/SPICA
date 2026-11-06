# PASO 84-H: adquisición controlada DOCX PNDA/SENAMHI

Actualización offline **84-HB**, 2026-11-06: véase el
[diagnóstico de relaciones y reevaluación](auditoria_relaciones_docx_paso84hb.md)
y la sección 9. Los resultados del GET y del inspector 0.1.0 que siguen son el
registro histórico del 84-H; no se reemplazan sus manifiestos privados.

Fecha: **2026-11-06**. Dictamen: **APTO CON RESTRICCIONES para conservación de
evidencia técnica; no habilitado para reconciliación del contenido documental**.
Se completó una adquisición HTTP y su conservación física. El inspector devolvió
**DOCUMENTO_RECHAZADO**, causa **relacion_externa_no_admitida**. No se relajó el
perfil, no se siguió la relación ni se extrajo contenido por otra vía.

## 1. Autorización y recuperación

La instrucción expresa del PASO 84-H autorizó un único GET a la URL literal
indicada abajo, con conservación privada fuera de Git/RAW/staging, sin catálogo
o SQLite operativo. No fue necesario solicitar otra autorización al usuario.
Las elevaciones de ejecución se limitaron a pruebas con temporales privados,
creación del directorio autorizado, operación única y auditoría local de lectura.

Git comenzó limpio en **feature/suadc-http**, HEAD
**32a7355a0da174c70a76ae7d65ef2616784b4a3b**, mensaje
`SUADC: auditoria y correcciones de seguridad del inspector DOCX`.
Este commit consolidó el 84-G sobre el WIP `85a8c22`.

Se revisaron el [expediente 84-F](preparacion_docx_pnda_paso84f.md), su
[protocolo](protocolo_docx_pnda_paso84f.md), el
[mapa de brechas](mapa_brechas_docx_paso84f.md), el
[inspector 84-G](inspector_docx_paso84g.md),
[`ClienteHTTP`](../src/spica/adquisicion/transportes/http.py) y
[`descargar_archivo`](../src/spica/adquisicion/transportes/descargas.py).
Entorno comprobado: Python **3.15.1**, HTTPX **0.28.1**, intérprete de `.venv`.

Las dos copias de la URL en el 84-F coinciden exactamente con la autorización:
**283 caracteres**, conservados también al construir la URL de HTTPX.
No se hizo descubrimiento remoto, HEAD o comprobación de disponibilidad adicional.

```text
https://www.datosabiertos.gob.pe/sites/default/files/Metadatos_Variables%20Meteorologicas%20de%20las%20Estaciones%20autom%C3%A1ticas%20de%20intercambio%20internacional%20-%20%5BServicio%20Nacional%20de%20Meteorolog%C3%ADa%20e%20Hidrolog%C3%ADa%20del%20Per%C3%BA%20-%20SENAMHI%5D.docx
```

## 2. Preparación y controles efectivos

Se utilizó la carpeta exacta propuesta en el 84-F:
**`C:\Users\Propietario\SPICA_EVIDENCIAS_PNDA_84F`**.
Su sufijo identifica el expediente de preparación; la adquisición corresponde al
84-H. Estaba ausente y se creó una sola vez, sin reutilizar evidencias anteriores.

La creación exclusiva mediante CreateDirectoryW aplicó desde el comienzo una DACL
protegida con FullControl únicamente para propietario, SYSTEM y administradores.
Se comprobaron propietario, tres reglas permitidas, protección de herencia de la
raíz y ACL heredadas de cada archivo. No se modificaron ACL de archivos anteriores.
Se rechazaron symlinks/reparse points en componentes de las rutas. La carpeta
está separada del repositorio, RAW, staging y bases operativas.

Probes propios de tres bytes comprobaron escritura, flush/fsync, lectura,
hardlink y rechazo de publicación sobre un destino existente; solo esos dos
archivos nuevos de prueba se retiraron antes del GET. Espacio libre previo:
**18844143616 bytes**, frente al mínimo del protocolo de **67108864 bytes
(64 MiB)**; comprobación puntual, sin reserva de espacio.

El arnés de operación se creó y ensayó en un temporal aislado; no se añadieron
herramientas productivas o módulos Python al repositorio. Una copia exacta del
procedimiento quedó privada para trazabilidad. Se reutilizó el cliente existente,
sin modificar sus políticas globales ni introducir otro backend de red.

| Control | Aplicación |
|---|---|
| Operación | Una llamada a `ClienteHTTP.descargar`, URL exacta, parámetros `None`, destino local fijo `metadatos-pnda.docx` |
| Autorización HTTP | Solo origen HTTPS PNDA; coincidencia literal de ruta comprobada por el arnés |
| TLS/proxy | Verificación TLS activada; `trust_env=False`, sin proxy configurado |
| Intentos/redirecciones | `PoliticaReintentos(max_intentos=1, jitter=0)`; backend HTTPX estándar con retries=0; follow_redirects=False |
| Credenciales | Cliente nuevo de un solo uso, sin auth ni cookies previas/enviadas, sin reutilización de sesión; no se registran Set-Cookie o cabeceras arbitrarias |
| Cuerpo | Límite de descarga 4194304 bytes; bloques de hasta 65536; streaming raw y Accept-Encoding identity; rechazo de Content-Encoding distinto de identity |
| Tamaños | Control incremental y de Content-Length; no se acepta un bloque que exceda el límite. La cota no representa una cuota de buffers TCP/TLS del SO |
| Timeouts | Conexión 10 s, lectura 15 s, escritura 10 s, pool 5 s; `get()` conserva su límite de 1 MiB |
| Cancelación | Event compartido y Timer de 60 s, cancelado y unido al terminar; mecanismo cooperativo, no deadline rígido |
| Reanudación | Sin Range; HTTP 206 rechazado |
| Publicación | Temporal exclusivo, fsync, relectura/hash y hardlink exclusivo; limpieza del temporal propio |
| Reejecución | `intento-iniciado.json` se publica antes del GET. Una segunda ejecución encuentra un estado no admisible y se detiene antes de conectar |

La guardia del arnés bloquea red fuera de la fase de descarga, SQLite y lecturas
de ubicaciones operativas. Durante la inspección no se habilitó red.

## 3. Resultado HTTP e integridad física

| Campo | Resultado observado |
|---|---|
| Inicio de operación UTC | **2026-11-06T12:33:14.558860+00:00** |
| Publicación según InformeDescarga UTC | **2026-11-06T12:33:15.786120+00:00** |
| Fin de operación/manifiesto UTC | **2026-11-06T12:33:18.146774+00:00** |
| Método / solicitudes | **GET / 1 intento de aplicación**, sin segunda solicitud, HEAD, redirección o recurso relacionado |
| Código HTTP | **200** |
| Content-Type disponible | **application/vnd.openxmlformats-officedocument.wordprocessingml.document**, MIME saneado por InformeDescarga; no se conservan parámetros ni cabecera bruta |
| Content-Length | **20664 bytes** |
| Bytes recibidos/almacenados completos | **20664 bytes**, coincidentes con el tamaño físico |
| SHA-256 físico | **7b9dcbd71c4d00798d1795edfd5ba0d15ad0aaab0297a7f0aba91532437a0d18** |
| Estado de transferencia | **COMPLETA**, historial de un intento con resultado exito y espera 0 |
| Temporal restante | **None** |
| Archivo primario | **C:\Users\Propietario\SPICA_EVIDENCIAS_PNDA_84F\metadatos-pnda.docx** |
| Identificador de inspección | **DOCX-PNDA-84H**, identificador local; no es asset_id, estación o adquisición RAW |

El transporte comparó SHA de bytes escritos con relectura del temporal. Tras
cerrar/publicar se volvió a abrir el archivo `rb`, comparando tamaño, SHA y firma
del descriptor/archivo. El inspector repitió la comprobación física antes y
después, con **conservacion_comprobada=True**. Otra auditoría posterior, de solo
lectura, volvió a cotejar la huella con el manifiesto y el informe de inspección.

Esto demuestra coherencia y conservación local en esas comprobaciones. No hay
hash independiente o firma del publicador con los que autenticar el documento.
HTTPS, el hostname y la atribución SENAMHI/PNDA no demuestran por sí solos
autoría, vigencia, equivalencia editorial o aplicabilidad científica.

## 4. Resultado ZIP/OOXML y extracción

Se aplicó el inspector **0.1.0** del 84-G, sin modificar su perfil o presupuestos.
Las pruebas previas comprobaron ZIP/XML, CRC, tamaños falsificados, macros,
relaciones externas, DEFLATE sin marcador final, cancelación y conservación.

El documento real alcanzó el preflight ZIP y la pasada compartida de verificación;
el diagnóstico contabiliza **137506 bytes descomprimidos** en esa pasada. La
pasada DOCX se detuvo por una relación externa no admitida, tras tres XML y
3621 bytes descomprimidos de controles. Se conservaron tres relaciones internas
comprobadas, sin publicar destinos externos. El código terminal no incluye parte
o ruta XML: no se inventa una localización o el tipo de la relación externa.

**Resultado: DOCUMENTO_RECHAZADO / relacion_externa_no_admitida**.
No se afirma validación completa del ZIP/OOXML, de todos los finales DEFLATE,
ausencia de macros u otros contenidos que requerían terminar el recorrido.
La pasada compartida y sus contadores no sustituyen la finalización del perfil
reforzado. El inventario canónico de partes no fue promovido: **0 partes**.

Presupuestos predeterminados: archivo 4 MiB; 128 entradas; central 128 KiB;
2 MiB por entrada/XML; 16 MiB descomprimidos por pasada; expansión 100:1;
64 XML; 100000 nodos/profundidad 32; 8 MiB auxiliares contables; 5 s cooperativos;
10000 párrafos, 100 tablas, 10000 celdas y 524288 caracteres emitidos.
Pico auxiliar contable observado: **52869 bytes**, distinto de una medida RSS.
Los límites completos y contadores constan en `inspeccion.json`.

La comprobación reforzada DEFLATE depende de `_decompressor` y `_compress_left`
de ZipExtFile en CPython 3.15.1; se verificó con sintéticos antes del ensayo.
Esta dependencia privada requiere regresiones al actualizar Python. No se
declara ejercida satisfactoriamente sobre todas las entradas reales del DOCX.

**Párrafos extraídos: 0; tablas: 0; propiedades: 0.** No se rescataron textos,
títulos, celdas o fechas mediante otro parser, Word o inspección manual del ZIP.
El rechazo es una política conservadora; no demuestra que el archivo sea
malicioso o carezca de información. Las referencias disponibles identifican
el archivo/hash y el diagnóstico técnico; no existen citas de contenido o páginas.

## 5. Evidencia privada e inventario final

Los seis archivos siguientes se conservaron. La auditoría final comprobó su
lectura física, SHA-256 y ACL privada; no hubo temporales o archivos inesperados.

| Archivo privado | Bytes | Función |
|---|---:|---|
| `metadatos-pnda.docx` | 20664 | Evidencia primaria completa e inalterada |
| `preparacion.json` | 936 | Autorización por huella, commit, URL, límites, ACL y probes |
| `procedimiento84h.py` | 16116 | Copia del arnés local utilizado, no documento institucional |
| `intento-iniciado.json` | 410 | Marca previa que impide repetir el GET |
| `inspeccion.json` | 2427 | Resultado estructurado real, límites, consumo y rechazo |
| `procedencia.json` | 3398 | Fechas, política, historial único, descarga, hash físico y vínculo al diagnóstico |

SHA-256 del diagnóstico privado:
`9f6f5b2e47145e19f0bc097a9f66f468ab5837d7de5b944d3e17af9e9b389e9f`.
SHA-256 de `procedencia.json` comprobado al cierre:
`4f16e90aa47d06119bd559e9939a96683da579b032ff6c574b90ad0ce977f0b1`.
La lista `archivos_presentes` dentro de ese manifiesto es la instantánea anterior
a su propia publicación; el inventario final anterior sí lo incluye.

Los JSON se escribieron exclusivamente con `xb`, flush/fsync y relectura:
manifiesto hasta 64 KiB, diagnóstico hasta 2 MiB, sin truncamiento en este caso.
No se serializaron cookies, credenciales, cabeceras completas o destinos externos.
La licencia aplicable y fecha/versión editorial permanecen **None**, sin fabricar
revisiones. No se asignó identidad RAW ni se registró el documento en el catálogo.

## 6. Relación preliminar con las 29 brechas

La [matriz histórica del 84-E](brechas_diccionario_pnda_paso84e.md) permanece
sin cambios: **1 resuelta, 13 parciales, 12 pendientes, 2 contradicciones y
1 no evaluable**. En particular, R02 no se cambia automáticamente aunque ahora
exista evidencia física identificada. Su revisión corresponde a otro incremento.

| Grupo / IDs relacionados | Evidencia nueva y límite |
|---|---|
| Conservación y documento, R01–R02 | Tamaño/hash y rechazo técnico del DOCX. No sustituye el cierre previo de R01 relativo al XLSX ni acredita suficiencia de contenido |
| Correspondencia y versiones, R03–R04 / V08 | No evaluadas en contenido. El nombre/URL y coenumeración histórica no prueban equivalencia CSV–XLSX–DOCX o vigencia |
| Uso y procedencia, R05–R06 | URL HTTPS y adquisición registradas; atribución SENAMHI/PNDA declarada, autenticidad independiente y licencia aplicable pendientes |
| Identidad, códigos y redes, S01–S03 | Ninguna afirmación literal extraída; no evaluadas |
| Coordenadas, CRS y altitud, S04–S05 | Ninguna afirmación literal extraída; no asignar CRS, coordenadas o referencia vertical |
| Historia, instrumentos y UBIGEO, S06–S08 | Sin lectura admitida; no reinterpretar códigos o resolver contradicciones previas |
| FECHA, HORA, zona y resolución temporal, T01–T05 | Sin lectura admitida; no reconstruir HORA, convertir zonas o inferir ventanas |
| FECHA_CORTE, huecos, duplicados y revisiones, T06–T07 | Sin lectura admitida; no inferir política de procesamiento |
| TEMP, HR y PP, V01–V03 | Sin definiciones extraídas; no interpretar unidades, promedios o acumulados |
| Ausentes, metrología, procesamiento y QC, V04–V07 | Sin lectura admitida; no inferir centinelas, controles institucionales o equivalencia con QA/QC SPICA |

**Afirmaciones literales observadas del cuerpo: ninguna.** Metadatos técnicos
observados: HTTP, MIME saneado, tamaños, huellas y diagnóstico. Interpretaciones
documentales: pendientes. Contradicciones nuevas: no evaluables con esta
extracción. Propiedades no encontradas: no puede afirmarse ausencia; el rechazo
impidió buscarlas de forma admitida. No se abrió el CSV o XLSX para contrastarlos.

## 7. Pruebas y verificaciones finales

Se ejecutaron con `.venv\Scripts\python.exe -B`, sin instalar dependencias:

| Verificación | Resultado de esta sesión |
|---|---|
| Inspector + transporte + descargas + reintentos | **136 aprobadas**, 0 fallos/errores, 1.588 s; subconjunto de la suite |
| Arnés temporal, MockTransport y fixtures propios | **11 aprobadas**, 0 fallos/errores, última corrida 0.659 s |
| Suite completa del repositorio | **1501 aprobadas**, 0 fallos, 0 errores, 0 omitidas, **161.204 s** |
| `python -B -m pip check` | **No broken requirements found.**, código 0 |
| `git diff --check` | Sin errores, código 0 |

El arnés se probó sin sockets reales: URL/método/cabeceras/timeouts, HTTP
incompatible y transitorio sin reintento, TLS/timeout, compresión/truncamiento/
exceso, vacío/HTML/otros 2xx, cancelación, originales existentes, JSON exclusivo
y acotado y ledger que bloquea una segunda adquisición incluso después de fallo.
Las 11 pruebas auxiliares no se incorporaron a tests/ ni se suman como nuevas
pruebas permanentes. Las 136 dirigidas se solapan con las 1501 históricas.

La suite completa se ejecutó antes del GET, con la guardia reutilizada del 84-G,
PYTHONPATH temporal y contexto del propietario para temporales privados; registró
**0 eventos de red, 0 accesos operativos, 0 SQLite operativos y 0 procesos no
admitidos**. Sus logs y las pruebas auxiliares están en
`%TEMP%\spica-84h-arnes-c3209958ba2445e5ba8fa4f310dbf732`.
La operación real habilitó red solo durante el único GET autorizado y cerró el
cliente antes de inspeccionar. No hubo otro GET o conexión institucional.

En Git se creó únicamente este informe. HEAD sigue en **32a7355** y la rama
en **feature/suadc-http**. Estado final comprobado:

```text
?? docs/adquisicion_docx_pnda_paso84h.md
```

No se modificaron fuentes Python, pruebas, configuraciones, dependencias o archivos
anteriores del repositorio. El DOCX, JSON privados y auxiliares de ejecución no
se incorporaron a Git. No hubo commits o push.

## 8. Riesgos y condiciones de continuidad

La publicación exclusiva no es una transacción conjunta con los manifiestos,
una garantía absoluta ante apagados o una copia de seguridad. No hay bloqueo
contra un propietario malicioso o concurrencia arbitraria. El uso admitido
fue secuencial, con rutas controladas y sin escritores concurrentes conocidos;
no se afirma una auditoría de todos los procesos del sistema.

La inspección conserva el bloqueo previsto para relaciones externas, incluso
legítimas. No se conoce aquí su destino o finalidad. Cualquier revisión offline
de ese alcance requiere nueva instrucción y pruebas, sin relajar automáticamente
controles, ejecutar Word o repetir la adquisición. Si se autoriza un trabajo
posterior, puede partir de estos mismos bytes conservados y cotejados por hash.

Antes de reconciliar contenido se requiere una inspección admitida o un nuevo
procedimiento seguro revisado, citas localizadas y revisión humana de edición,
vigencia, correspondencia entre recursos y condiciones de uso. Nada de este paso
habilita QA/QC científico, transformación temporal, asignación de estaciones o CRS.

No se accedió al CSV/XLSX institucional, RAW, staging o SQLite operativos. No se
hicieron migraciones o escrituras en ellos ni se revalidaron sus huellas: esta
confirmación describe las operaciones de la sesión, no cambios de terceros.
Se conserva la evidencia y se espera revisión, sin integración científica automática.

## 9. Actualización 84-HB: relaciones externas y límite nuevo

El 84-H quedó registrado en **944151a**, desde el que comenzó limpio el 84-HB.
Sin conexiones o descargas adicionales se cotejaron los seis archivos originales:
tamaños, SHA-256 y posteriormente firmas/modos permanecieron coincidentes.
No se escribió en su directorio ni se cambiaron los JSON históricos.

El diagnóstico acotado encontró tres relaciones de tipo exacto OOXML `hyperlink`,
`TargetMode="External"`, en `word/_rels/document.xml.rels`, origen
`word/document.xml`. La primera externa en el orden XML era **rId7 (mailto)**;
las otras eran **rId6 (HTTP)** y **rId5 (HTTPS)**. Todas se usan en elementos
`w:hyperlink` de párrafos locales dentro de la primera tabla. Los destinos no
se resolvieron ni publicaron. La política 0.1.0 rechazaba cualquier External,
incluidos estos enlaces pasivos; no era una prueba de contenido malicioso.

Tras **19 pruebas nuevas** y las **58 anteriores** del inspector, y una suite
completa de **1520 aprobadas, 0 fallos/errores**, se reevaluó una vez el mismo
archivo con el inspector **0.2.0**. La excepción nueva es cerrada a hipervínculos
pasivos coherentes de tipo/origen/uso verificados, con destinos HTTP/HTTPS o
mailto de perfil limitado, omitidos sin URI en el resultado. Imágenes, plantillas,
OLE, contenido alternativo y relaciones desconocidas siguen bloqueados.

Reevaluación UTC: **2026-11-06T12:58:47.540932+00:00** a
**2026-11-06T12:58:47.670684+00:00**. Resultado:
**INSPECCION_INCOMPLETA**, diagnóstico
`campos_revisiones_o_caracteristicas_no_interpretadas` en **word/document.xml**.
Se observaron 12 partes, 9 relaciones internas y 3 enlaces externos omitidos;
**0 párrafos, 0 tablas y 5 propiedades técnicas**, sin publicar sus valores o
convertirlos en edición/vigencia. La conservación física fue comprobada.

Se detuvo el trabajo sobre el documento ante esta restricción nueva, sin modificar
otros controles o volver a inspeccionarlo para conseguir aceptación. El código
genérico no permite afirmar si la causa es un campo, revisión u otra extensión;
no se inventa una causa más específica ni se afirma ausencia de información.

La descarga original sigue **COMPLETA** y la inspección del contenido sigue sin
ser satisfactoria. **APTO CON RESTRICCIONES**, sin habilitación para reconciliación
documental. Las 29 brechas conservan sus estados. El
[informe 84-HB](auditoria_relaciones_docx_paso84hb.md) detalla controles, referencias,
pruebas y condiciones de revisión; no se autorizó procesamiento científico.
