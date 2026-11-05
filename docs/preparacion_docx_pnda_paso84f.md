# PASO 84-F: preparación documental DOCX PNDA/SENAMHI

Fecha de preparación: **2026-11-05**. **APTO CON RESTRICCIONES** para revisión
del expediente y solicitud posterior. **GET NO AUTORIZADO NI EJECUTADO.** No se
certifica una URL operativa, un DOCX válido, una edición o una licencia aplicable.

Entregables complementarios:

- [Protocolo de inspección OOXML y extracción mínima](protocolo_docx_pnda_paso84f.md).
- [Mapa de las 29 brechas y evidencia potencial](mapa_brechas_docx_paso84f.md).

## 1. Recuperación y alcance de esta auditoría

Git comenzó limpio en `feature/suadc-http`, HEAD **`69235a7`**,
`SUADC: inspeccion documental y brechas del diccionario PNDA`. Ese commit registra
los dos documentos, diagnóstico y pruebas del 84-E. Se revisaron los tres
documentos del 84-D y los dos del 84-E, más los mecanismos HTTP, descarga,
catálogo, evidencia y verificación del repositorio. Python de `.venv`: **3.15.1**;
HTTPX importado localmente: **0.28.1**.

Este paso produce únicamente tres documentos. No necesita implementar un
inspector para identificar la URL, definir el ensayo y describir controles.
La futura implementación mínima y sus pruebas quedan como condición previa a
usar un DOCX para extraer afirmaciones. No se crea otro cliente ni se refactoriza
adquisición. No se abre ningún CSV, XLSX privado, DOCX, RAW, staging o SQLite
operativo. No se crea ahora el directorio de adquisición propuesto.

## 2. Documento candidato y cadena de procedencia

Fuente primaria **local**: [84-D, inventario del producto y recursos](auditoria_metadatos_pnda_paso84d.md#2-inventario-del-producto-y-recursos),
que transcribe las URLs del informe histórico E-60. Ese informe fue leído y
comprobado en 84-D: 2744 bytes, SHA-256
`9e1f8f26c7047bcd803ab75dc66f2b36f9a7d0127ffd519fc63dd4e2a79420df`.
No se reabre ni se calcula otra huella de ese informe en 84-F. Es evidencia de
procedencia histórica de la referencia, no verificación HTTP actual del DOCX.

**DOCX84F** es un localizador documental interno para esta URL exacta candidata:

```text
https://www.datosabiertos.gob.pe/sites/default/files/Metadatos_Variables%20Meteorologicas%20de%20las%20Estaciones%20autom%C3%A1ticas%20de%20intercambio%20internacional%20-%20%5BServicio%20Nacional%20de%20Meteorolog%C3%ADa%20e%20Hidrolog%C3%ADa%20del%20Per%C3%BA%20-%20SENAMHI%5D.docx
```

No es un nuevo recurso registrado o asset_id. El análisis de la cadena confirma
HTTPS, host `www.datosabiertos.gob.pe`, puerto implícito 443, sin usuario,
contraseña, consulta o fragmento. La ruta codificada se conserva literalmente:
no se vuelve a codificar ni se elige una variante por similitud. La búsqueda
acotada en documentación/código/pruebas solo encontró esta URL institucional
DOCX; `/sites/default/files/metadatos.docx` en una prueba es un **fixture sintético**,
no alternativa autorizable. No se encontraron direcciones institucionales
contradictorias en ese alcance; no se afirma inexistencia de otras en PNDA.

| Atributo | Evidencia y estado |
|---|---|
| Institución atribuida | SENAMHI; no autenticada independientemente en este paso |
| Portal publicador/distribuidor | Plataforma Nacional de Datos Abiertos, según el antecedente local |
| Publicación | `https://www.datosabiertos.gob.pe/dataset/variables-meteorologicas-de-las-estaciones-autom%C3%A1ticas-de-intercambio-internacional-servicio` |
| Producto asociado | Variables meteorológicas de estaciones automáticas de intercambio internacional; ID literal de producto igual al segmento después de `/dataset/` anterior |
| Recurso anunciado | Rol histórico `metadatos`; basename de URL con prefijo `Metadatos_Variables` y extensión `.docx`. El título interno de Word es desconocido |
| Tipo anunciado | DOCX por extensión/rol; tipo detectado, MIME recibido y estructura desconocidos |
| Relación GBON/RBON | Asociación histórica con el producto auditado; B15 del XLSX define GBON/RBON. No se ha leído tal declaración en el DOCX |
| Relación con CSV/XLSX | Coenumeración en una publicación histórica. No hay manifiesto de equivalencia editorial ni correspondencia por período |
| Versión/fecha editorial | Desconocidas; no se rellenan con fechas de adquisición, inspección, propiedades del XLSX o versión del software |
| Tamaño/hash/asset DOCX | Desconocidos; no se asigna el hash del XLSX al DOCX ni un ID operativo nuevo |
| Acceso/autenticación actuales | No comprobados. El ensayo propuesto exige acceso público sin sesión; no intentará autenticarse |
| Derechos | Referencia histórica `http://opendefinition.org/licenses/odc-by/`; texto, edición, alcance a los tres recursos y redistribución no acreditados |

El enlace de licencia se conserva como texto histórico, sin acceder a él o
interpretarlo como permiso de redistribución. No se publicará el cuerpo DOCX en
Git por inferencia. La autorización operativa del usuario y las condiciones de
uso institucionales son cuestiones separadas.

## 3. Matriz de correspondencia CSV–XLSX–DOCX

Los valores siguientes proceden de documentos del repositorio, **sin releer
los originales en 84-F**. Las URLs CSV/XLSX exactas se conservan en el inventario
del 84-D enlazado arriba; DOCX84F coincide literalmente con su tercera URL.

| Recurso | Identidad histórica y evidencia | Relación demostrada documentalmente | Correspondencia no demostrada |
|---|---|---|---|
| CSV | Asset `71df55229ee947fb8e7fed8b1403289e`, adquisición `ff8e7846a9b14568aad924aa8ca93f74`; 50474012 bytes; SHA-256 `3d3e8a0a75e070d0b8111faf921be17140c3a0f9db2b4c25d72d99a15a950eab`, comprobados en 84-C | URL histórica del CSV coincide con la identidad documentada en 84-C; 16 campos contrastados en antecedentes | Edición institucional, alcance del diccionario por revisión/período y relación con contenido DOCX |
| XLSX | Asset histórico `b6aa17105088497296147feb3c8f06e3`; 10815 bytes; SHA-256 `1851039a07682a3f202314f6f8811fc616cb4ca2a486c9e737fd8cea62a4b4dd`; copia/lectura comprobadas en 84-E | Hoja DiccionarioDatos, 16 definiciones; B2 nombra el producto; B15 define GBON/RBON. Copia documental privada acreditada entonces | Sus fechas técnicas internas no prueban edición/vigencia ni aplicabilidad a todos los períodos del CSV |
| DOCX | DOCX84F y rol `metadatos`, según E-60 transcrito en 84-D; sin adquisición o contenido local acreditados | El enlace fue enumerado bajo la misma publicación que los otros dos recursos | Todo contenido, formato real, edición, versión, fechas, hash, tamaño y relación editorial con los originales |

**Compartir página, título o campos no prueba compartir edición.** La atribución
al mismo portal/institución no fusiona los tres recursos, sus activos, revisiones,
licencias o capacidades. Un HTTP 200 histórico del XLSX no comprueba el DOCX.
Si una futura respuesta aporta una edición distinta o una contradicción, se
conservan ambas afirmaciones y se detiene su incorporación; no se elige la más
reciente por fecha de descarga. Se siguen las
[reglas de reconciliación del 84-D](reconciliacion_evidencias_pnda_paso84d.md#2-reglas-para-reconciliar-sin-borrar-historia).

## 4. Infraestructura reutilizable y límites comprobados por lectura

| Componente | Reutilización futura y límite |
|---|---|
| [ClienteHTTP y ConfiguracionHTTP](../src/spica/adquisicion/transportes/http.py) | Una sola política de origen, TLS, redirecciones, compresión, tamaños y errores; `descargar()` permite destino privado y límite propio. `get()` conserva su 1 MiB global |
| [PoliticaReintentos / GestorReintentos](../src/spica/adquisicion/transportes/reintentos.py) | `max_intentos=1` explícito; Event compartido y `cancelar()`. El transporte HTTPX instalado tiene `retries=0` por defecto; no se inyectará otro backend |
| [descargar_archivo / InformeDescarga](../src/spica/adquisicion/transportes/descargas.py) | Temporal exclusivo, streaming raw, límite real, cotejo de Content-Length, SHA de transferencia y relectura física, fsync, publicación exclusiva con hardlink y limpieza propia. No incorpora RAW |
| [Catálogo y procedencia](../src/spica/adquisicion/catalogo/modelos.py) / [recurso documental](../src/spica/adquisicion/catalogo/documental.py) | Describen fuente/producto/recurso, declaraciones y revisiones; referencia URL no es capacidad probada. No se abre ni registra nada en SQLite |
| [Evidencias](../src/spica/adquisicion/catalogo/evidencias.py) | Distinguen declaración documental de adquisición vinculada a un activo. Aquí se usaría un manifiesto privado auxiliar, sin fabricar EvidenciaAdquisicion/asset RAW o llamar `empaquetar()` como si ya se hubiese adquirido |
| [AdaptadorHTTPRAW](../src/spica/adquisicion/integracion/http_raw.py) | No se invocará: su finalidad incluye incorporación RAW, fuera del ensayo documental |
| [Conector PNDA](../src/spica/adquisicion/conectores/senamhi/pnda.py) | Descubre recursos/roles, pero `adquirir()` restringe el piloto a diccionario XLSX. No se amplía, no se invoca descubrimiento web y no se disfraza el DOCX como diccionario |
| [Verificador](../src/spica/adquisicion/verificacion/inspector.py) / [controles ZIP/XML](../src/spica/adquisicion/verificacion/_xlsx.py) | CRC, límites, rutas y marcadores básicos DOCX reutilizables. No extraen el documento ni implementan la política DOCX completa propuesta |

**Carencia concreta, sin modificar producción:** `inspeccionar_zip` puede devolver
`docx` tras reconocer relación principal, MIME y raíz `word/document.xml`; el
control explícito de macros está en la rama XLSX posterior. No debe usarse ese
retorno como prueba de ausencia de contenido activo en DOCX. Además,
`ResultadoEstructura.utilizable_documentalmente` admite únicamente XLSX/CSV.
No se cambia esa propiedad ni se fuerza su resultado. Se necesita un diagnóstico
DOCX aislado con controles antes de extraer afirmaciones, conforme al protocolo
complementario. El diagnóstico XLSX del 84-E conserva su alcance propio.

No se requiere cambiar contratos científicos para preparar esta solicitud.
Los metadatos eventualmente extraídos seguirán siendo declaraciones localizadas
con versión desconocida cuando corresponda, no resultados científicos aprobados.

## 5. Parámetros propuestos del futuro GET

**Propuesta sin ejecución**, aplicable únicamente tras autorización nueva y
revisión del arnés mínimo de operación. No altera límites globales.

| Control | Valor propuesto y justificación |
|---|---|
| Recurso/método | Solo DOCX84F exacta; `ClienteHTTP.descargar(url, directorio, "metadatos-pnda.docx", max_bytes=4194304, tamano_bloque=65536, parametros=None)` |
| Origen permitido | Solo `https://www.datosabiertos.gob.pe`; el llamador comprueba además la ruta exacta, pues la whitelist del cliente es por origen |
| Transporte | HTTPS/TLS verificado; cliente nuevo, backend estándar sin reintentos, `trust_env=False` y redirecciones automáticas deshabilitadas por el cliente existente |
| Intentos | `PoliticaReintentos(max_intentos=1, jitter=0)`; como máximo un GET de aplicación. Cero HEAD, sondeos, GET de publicación/licencia o comprobaciones externas previas; cero repetición tras fallo |
| Credenciales | Sin auth, usuario/clave, cookies previas, cabeceras añadidas, sesión reutilizada ni credenciales de entorno. Cliente de un solo uso; un Set-Cookie recibido no se registra ni se reutiliza |
| Cuerpo | Máximo **4194304 bytes (4 MiB)**; bloques **65536**. Cota conservadora del ensayo para metadatos de tamaño desconocido, no predicción del tamaño remoto. Si no cabe, detener; no ampliarla automáticamente |
| Timeouts de ConfiguracionHTTP | conexión **10 s**, lectura **15 s**, escritura **10 s**, pool **5 s**; TLS verdadero y `max_bytes_respuesta=1048576` sin cambios |
| Cancelación | Event compartido / `ClienteHTTP.cancelar()`, revisión entre bloques y relecturas; cierre por contexto y manejo de interrupción. Objetivo cooperativo de **60 s**, a verificar en arnés mediante temporizador que active el Event |
| Compresión / reanudación | Accept-Encoding identity; rechazar otra Content-Encoding. Rechazar 206; sin Range, reanudación ni compresión HTTP. La compresión ZIP interna es una fase posterior con sus límites propios |
| Estado esperado | **200**. El cliente rechaza 3xx/206/errores; otros 2xx pueden pasar el transporte, pero el arnés debe clasificarlos como respuesta inesperada, detener inspección y no declarar DOCX utilizable |
| Tipo sugerido en InformeDescarga | Solo MIME DOCX o genéricos `application/octet-stream` / `application/zip` permiten pasar a comprobación ZIP; ninguno demuestra formato. HTML/JSON/texto u otra sugerencia implican detención y evidencia privada. `None` también detiene: el informe saneado no permite distinguir ausencia de MIME de un tipo fuera de su whitelist |
| Espacio previo | **64 MiB libres** en el volumen de destino; margen frente a 4 MiB de cuerpo y auxiliares. Es un mínimo de comprobación, no reserva ni garantía de escritura |
| Destino | Directorio nuevo privado `Path.home() / "SPICA_EVIDENCIAS_PNDA_84F"`, que en este entorno corresponde a `C:\Users\Propietario\SPICA_EVIDENCIAS_PNDA_84F`; fuera de Git, RAW y staging |

**Límite de tiempo real:** los timeouts HTTPX son por fase/inactividad, no un
deadline total. El Event no interrumpe necesariamente una lectura activa; un
flujo lento que no entregue un bloque completo puede retrasar su observación.
El objetivo de 60 s no es garantía rígida, ni se promete “60+15 s” como máximo.
Si se requiere plazo total estricto, hay que revisar un aislamiento/supervisor
antes de autorizar ejecución; no se añade ahora. No se usará una cancelación
forzada como prueba de limpieza exitosa. Operación futura secuencial y supervisada.

## 6. Secuencia futura y conservación privada

1. Revisar autorización exacta vigente, URL y parámetros contra este expediente.
   Comprobar firmas reales y pruebas sintéticas del arnés/inspector. Rechazar
   otros recursos, direcciones contradictorias, incertidumbre de estado o escritores
   conocidos. No resolver esas condiciones con conexiones de prueba.
2. Validar rutas absolutas sin symlinks/junctions/reparse inesperados en componentes;
   fuera del repositorio y `SPICA_DATOS`. La carpeta propuesta debe estar ausente.
   Si existe, **detener sin reutilizar, limpiar o elegir otra automáticamente**.
   No se toca la carpeta del 84-E.
3. Tras la autorización, crear solo esa carpeta con ACL privada verificada:
   propietario, SYSTEM y administradores, sin otras concesiones Allow. Comprobar
   permiso de escritura, espacio libre y publicación exclusiva con archivos de
   prueba propios mínimos, antes del GET; retirarlos de forma controlada. Si el
   sistema de archivos no soporta el hardlink exclusivo, detener, sin fallback
   a reemplazo. No alterar ACL de archivos/directorios existentes.
4. Ejecutar una sola llamada a `descargar()` con cliente nuevo. El descargador
   existente crea su temporal `.suadc-*.tmp` dentro del destino privado, controla
   bytes reales aunque falte Content-Length, compara tamaño si está declarado,
   calcula SHA y relee físicamente antes de publicar sin sobrescritura.
5. Revisar informe y número de intentos. Ante 3xx, TLS, timeout, error HTTP,
   exceso, truncamiento, fallo de disco, cancelación o temporal restante, detener
   sin repetir. El descargador intenta retirar su temporal propio en fallos;
   si no lo logra, conservar la referencia para revisión, sin barridos/borrados.
   Una transferencia incompleta no produce un DOCX válido ni un SHA confirmado.
6. Para una respuesta publicada, exigir HTTP 200, longitud física positiva,
   coherencia del tamaño y cotejar hash/inode/firma después de cerrar/reabrir.
   Un cuerpo vacío conserva su hash técnico si lo hay, pero no es DOCX válido.
   Aplicar el protocolo OOXML solo si la sugerencia de tipo y demás controles
   lo permiten; no acceder al cliente interno para recuperar cabeceras arbitrarias
   cuando el tipo saneado sea `None`. Si es HTML/otro formato o falla inspección, preservar los bytes
   ya publicados como evidencia privada, marcar respuesta no admitida y detener.
7. Crear `procedencia.json` privado y exclusivo, con escritura acotada a **64 KiB**,
   flush/fsync y sin sobrescritura. Si procede, `inspeccion.json` exclusivo de
   hasta **2 MiB**, según el protocolo. El manifiesto enlaza hash/nombre del
   informe de inspección cuando exista; si no existe, `None` y motivo real.
   Verificar ambos por relectura. Fallo de manifiesto deja estado pendiente de
   revisión, no éxito ni autorización para repetir el GET o borrar la evidencia.
8. Comprobar carpeta con solo archivos previstos/temporales explícitamente
   registrados, cerrar recursos, verificar Git y entregar informe. Ninguna
   llamada a RAW, SQLite, registro de catálogo o adaptación científica.

El manifiesto propuesto separa: identidad local de operación (no asset_id),
referencia a este plan/commit/autorización; URL exacta solicitada, publicación e
institución atribuidas; UTC inicio/fin; política aplicada; intentos y diagnóstico
público; HTTP recibido, bytes declarados o `None`, bytes reales; hash físico,
archivo/localización privada; integridad/inspección realizadas y limitaciones;
licencia solo referenciada; versión/fecha editorial `None` salvo texto localizado;
origen de cada afirmación y relación de ediciones aún no acreditada. No almacena
cookies, Set-Cookie, Authorization, cuerpos de error remotos, trazas de excepción,
cabeceras completas o datos personales innecesarios. Los IDs y fechas no se
inventan en esta preparación; solo se generarían/medirían al ejecutar.

Publicación por hardlink es exclusiva en el volumen local, no una transacción
conjunta con manifiesto/inspección ni garantía total ante apagados. No se promete
fsync portable del directorio en Windows o backup independiente. Tras interrupción
incierta: inventario puntual y revisión humana, sin reinicializar ni reintentar.
Integridad local no demuestra hash de origen independiente, firma institucional,
vigencia o validez científica.

## 7. Solicitud propuesta para autorización posterior

**Texto propuesto, no autorización recibida ni pregunta de ejecución en este turno.**
Requiere revisar primero los controles pendientes del protocolo y el arnés mínimo;
no habilita conexiones mientras esos controles no estén preparados y probados.

> Autorizo un único intento GET, sin HEAD ni otros sondeos, exclusivamente a:
>
> https://www.datosabiertos.gob.pe/sites/default/files/Metadatos_Variables%20Meteorologicas%20de%20las%20Estaciones%20autom%C3%A1ticas%20de%20intercambio%20internacional%20-%20%5BServicio%20Nacional%20de%20Meteorolog%C3%ADa%20e%20Hidrolog%C3%ADa%20del%20Per%C3%BA%20-%20SENAMHI%5D.docx
>
> Autorizo crear exclusivamente `C:\Users\Propietario\SPICA_EVIDENCIAS_PNDA_84F`,
> hoy solo propuesta, y los archivos privados necesarios para el ensayo descrito:
> probes propios de seguridad/publicación, temporal propio de descarga,
> `metadatos-pnda.docx`, `procedencia.json` e `inspeccion.json` si la inspección
> resulta admisible. Si la carpeta existe o hay rutas, ACL, espacio o estados
> inesperados, detener sin reutilizar, borrar o cambiar de ubicación.
>
> Límite del cuerpo 4194304 bytes, bloques 65536, mínimo previo 64 MiB libres,
> HTTPS/TLS verificado, origen exacto, sin redirecciones, reintentos, autenticación,
> cookies enviadas o credenciales. Timeouts conexión/lectura/escritura/pool
> 10/15/10/5 segundos y objetivo de cancelación cooperativa a 60 segundos, con
> sus limitaciones expresas; no se autoriza prolongar o repetir automáticamente.
>
> Autorizo cotejo físico de bytes/SHA-256 y la inspección local acotada del
> protocolo 84-F, previamente probada con sintéticos; no ejecutar Word, macros,
> campos o enlaces externos ni extraer ZIP al sistema de archivos. Conservar
> las respuestas inesperadas ya publicadas solo como evidencia privada no
> utilizable, detener ante anomalías y documentar residuos sin borrados correctivos.
>
> No incorporar RAW, usar staging operativo, abrir SQLite, registrar catálogo,
> migrar, modificar originales, interpretar observaciones o habilitar QA/QC.
> No descargar CSV/XLSX/licencias u otros recursos. No instalar, commit o push.
> Esta autorización operativa no certifica licencia, identidad editorial ni
> correspondencia entre recursos; cualquier incorporación posterior requiere revisión.

## 8. Verificación y resultado de este paso

Se comprueban directamente los tres documentos sin seguimiento: UTF-8, finales,
tablas, enlaces locales/anclas, URL literal contra el 84-D y cobertura/estados de
los 29 IDs contra el 84-E. Los enlaces externos se validan solo sintácticamente,
sin resolución DNS o HTTP. No se crean herramientas o pruebas nuevas: **0 tests
unitarios ejecutados en 84-F**, suite completa histórica **1431 aprobadas** y
ensayo dirigido del 84-E **63 aprobadas**, sin presentarlos como corridas actuales.
No se repite `pip check` porque no cambia código o dependencias.

Comprobaciones realizadas con `.venv\Scripts\python.exe -B`: **24 enlaces locales,
4 anclas y 8 tablas coherentes**, UTF-8 y finales sin incidencias; **29 IDs y
estados del 84-E idénticos**; ambas copias de la URL DOCX en este documento
coinciden literalmente con el 84-D. El análisis AST del cliente confirma los
argumentos reales de `descargar()` usados por el plan, sin instanciarlo ni abrir
HTTP. La guardia de esa comprobación registró **0 eventos de red/SQLite/subproceso**.
Son comprobaciones documentales, no tests funcionales del futuro inspector.

`git diff --check`, `git diff --exit-code` y `git diff --cached --exit-code`
terminaron con **código 0 y sin salida**. Se revisan los archivos nuevos
directamente porque no figuran en el diff registrado. Rama/HEAD se mantienen;
ningún archivo previamente registrado o del índice cambió. Estado final:

```text
?? docs/mapa_brechas_docx_paso84f.md
?? docs/preparacion_docx_pnda_paso84f.md
?? docs/protocolo_docx_pnda_paso84f.md
```

Archivos Python creados/modificados: **0**. No se revalidan hashes físicos de
CSV/XLSX ni almacenes que no se abrieron; los antecedentes están identificados
como tales y no se auditan cambios de terceros sobre datos operativos.

**Riesgos pendientes:** disponibilidad/tamaño/formato/acceso remotos, licencia y
edición no verificados; documento posiblemente insuficiente para las brechas;
inspector DOCX y arnés mínimo aún por implementar/probar en otro paso antes del
uso real; cancelación cooperativa; concurrencia local y durabilidad limitadas.
El GET permanece bloqueado hasta revisión y autorización expresa. Cero conexiones,
descargas, acceso/escrituras operativas, migraciones, instalaciones, commits o push.
