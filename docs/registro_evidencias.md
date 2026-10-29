# PASO 65: registro institucional y evidencia por adquisición

Alcance: SUADC-03 y SUADC-06. Se reutilizan el catálogo científico, su diario de
revisiones, el adaptador HTTP→RAW y el catálogo RAW existentes. No hay un segundo
catálogo ni otro motor de descarga. Las pruebas utilizan exclusivamente datos
sintéticos, SQLite temporal y MockTransport, sin acceder al RAW permanente.

## Defectos reproducidos antes de la corrección

Cuatro pruebas nuevas fallaron sobre la implementación anterior: redescubrimiento
del mismo producto, registro de dos productos de SENAMHI, cambio posterior de
licencia y recuperación de evidencia tras cerrar/reabrir RAW. Los tres primeros
producían `registro_contradictorio_requiere_revision`; el cuarto carecía de una
operación para recuperar evidencia persistida por adquisición.

La suite base ejecutada antes de corregirlos aprobó sus 439 pruebas.

## Identidades y registros documentales

| Entidad | Identidad lógica |
| --- | --- |
| Institución/fuente | `Fuente(proveedor, identificador)` |
| Producto | Fuente + identificador original del producto |
| Recurso | Fuente + producto + identificador original del recurso |
| Adquisición documentada | UUID propio, diferente del activo y del hash |
| Activo MD-03 | `asset_id` existente, vinculado al objeto MD-02 y proyecto MD-01 |
| Contenido físico | SHA-256 y tamaño; puede compartirse entre varios activos |

Se conservan exactamente espacios, mayúsculas, escapes y códigos originales. Los
identificadores locales de instituciones o productos diferentes no colisionan.
No se inventan estaciones, variables, unidades, disponibilidad ni filtros remotos.

`RecursoCatalogo` añade localizador, procedencia, publicación, título, formato,
tipo de medio y licencia opcionales. Es documentación, no disponibilidad de
observaciones. No se convierte en una capacidad del producto para el planificador.
Su consulta devuelve `RegistroRecurso(entidad, revision)`; las entidades anteriores
siguen devolviendo `RegistroCatalogo` sin modificar ese contrato.

La política optativa `CatalogoCientifico.registrar_documental` devuelve
`ResultadoRegistroDocumental(estado, registro, motivo)`:

| Estado | Regla y efecto |
| --- | --- |
| NUEVO | Identidad ausente: registra revisión 1 |
| IDENTICO | Mismo documento, aunque cambie solo la fecha de reconsulta: conserva revisión y contenido anteriores |
| REVISION_DOCUMENTAL | Cambio documental permitido, con procedencia estrictamente posterior: agrega revisión sin borrar historia |
| CONTRADICCION | Cambio material protegido o fecha no posterior: devuelve registro vigente y motivo, sin modificarlo |

No se actualiza silenciosamente una fecha por una reconsulta idéntica. La fecha
de cada descubrimiento utilizado se conserva separadamente en su adquisición.
La política compara documentos completos salvo `procedencia.revisada_utc` y, para
fuentes, `revisada_utc`. Un cambio de referencia, evidencia o método sí es documental.

Campos materiales protegidos cuando ya son conocidos:

- Fuente: nombre, tipo de organización y estado de verificación.
- Producto: familia, modalidad de acceso, autenticación requerida y uso de estaciones.
- Recurso: localizador, formato y tipo de medio.
- Capacidad: mecanismo, estado de verificación y descripción de otro mecanismo.

Completar un campo material desconocido (`None`) se admite con evidencia posterior;
reemplazar o retirar un valor material conocido requiere evaluación explícita.
Licencia, referencias documentales, versiones, títulos, descripciones y formatos
declarados del producto pueden revisarse con historia. Una licencia nueva no se
aplica retroactivamente a adquisiciones antiguas ni equivale a asesoría jurídica.

`registrar()` conserva su rechazo estricto de contenido diferente. `actualizar()`
conserva su revisión esperada y motivo explícitos para las entidades previas. No
se ha añadido una resolución automática de contradicciones de recursos.

Consultas nuevas: `consultar_recurso(fuente, producto_id, recurso_id, revision=None)`,
`listar_recursos(fuente, producto_id)` y `consultar_revision(entidad, revision)`.

## PNDA e identidad institucional

La fuente permanece `Fuente("SENAMHI", "SENAMHI")`. Su procedencia institucional
usa `urn:spica:fuente:SENAMHI`, referencia local de una identidad declarada por el
conector. No es un endpoint ni acredita una consulta institucional. Su referencia
oficial queda desconocida en lugar de atribuirle una página de producto.

Un registro anterior que usaba la página del producto como referencia institucional
puede conservarse como revisión histórica al corregirse documentalmente esa
procedencia. La corrección exige fecha posterior y no cambia la identidad.
No se recorren ni actualizan bases operativas.

`registrar_catalogo()` sigue retornando los tres registros fuente/producto/capacidad.
Además registra cada recurso y expone todos los resultados en `registros_documentales`.
Cada entidad y su historial se confirman juntos. El lote entero no es atómico:
un fallo puede dejar un prefijo persistido. El conector bloquea adquisiciones
después de un registro fallido o contradictorio hasta completar satisfactoriamente
el registro. Repetirlo aplica idempotencia; no borra datos ni reintenta red.

Configurar otro producto PNDA exige comprobar su pertenencia a SENAMHI: el parser
no autentica esa atribución. El piloto sigue autorizando solo diccionarios XLSX
del descubrimiento actual; no adquiere CSV ni otros roles.

## Evidencia persistente en RAW

`EvidenciaDocumental` es una instantánea inmutable con fuente, producto/recurso,
referencia pública de publicación, descubrimiento UTC, licencia y referencia de
licencia, revisiones documental/producto/fuente, procedencia, estado de evidencia
y capacidades documentadas. Cada dato ausente permanece `None`, DESCONOCIDO o
colección vacía. No hay una revisión numérica inventada para recursos no registrados.

El conector conserva la URL de licencia publicada; no obtiene ni inventa su texto.
El estado documental del enlace continúa DECLARADO aunque la adquisición tenga una
comprobación HTTP propia. La pertenencia de la licencia y el recurso al documento
se conserva en la instantánea y en la revisión del recurso correspondiente.

`AdaptadorHTTPRAW.adquirir_documentado` comparte la implementación de `adquirir()`.
Valida antes del HTTP que la evidencia corresponda a la fuente, recurso y producto
de la declaración, y acota el documento a 60 000 bytes JSON UTF-8 (paquete ≤64 KiB).
Las declaraciones y resultados anteriores no cambian sus campos ni sus firmas.
`AlmacenRAW.incorporar_documentado` reutiliza la incorporación existente y exige
tamaño/hash esperados de la transferencia. No descarga ni verifica HTTP por sí mismo:
esa evidencia técnica es aportada por el ejecutor, normalmente el adaptador.

La preparación inserta, en la misma fila/transacción del activo, una extensión
JSON `_evidencia_adquisicion` con `version=1`, UUID de adquisición, documento,
URL solicitada pública, marca de saneamiento, comprobación HTTP UTC y la capacidad
HTTP_DIRECTO efectivamente ejercida por esa operación. Ninguna transición posterior
reescribe el documento. El identificador de activo es la PK de esa misma fila;
no existe una relación separada que pueda quedar huérfana.

`consultar_evidencia(asset_id)` devuelve `EvidenciaAdquisicion` con esa información,
SHA-256/tamaño físicos registrados y estado actual del activo. No relee el archivo:
se debe usar `recuperar`/`verificar` para comprobar su estado físico presente.
`consultar_adquisicion(adquisicion_id)` recupera la misma asociación persistida.
UUID diferentes preservan adquisiciones distintas aunque el recurso y sus bytes
sean idénticos. La deduplicación física conserva las comprobaciones anteriores.

Los registros antiguos sin paquete devuelven `None`; no se reconstruye evidencia
histórica a partir de metadatos actuales. Una adquisición PNDA sin registro previo
del catálogo conserva su documento, pero deja las revisiones desconocidas. Para
obtener referencias numéricas al historial hay que registrar antes de adquirir.

## SQLite, seguridad y fallos parciales

No cambia DDL, `application_id` ni `user_version`, y no se ejecuta una migración.
Los recursos usan la tabla `revisiones` existente con tabla lógica `recursos` y
clave compuesta serializada. El vínculo a un producto se exige dentro del bloqueo
SQLite por la API; no hay una nueva FK física sobre claves JSON ni API de borrado.
La apertura del catálogo científico compara su estructura con el DDL existente
reconstruido en memoria y verifica claves externas; rechaza bases ajenas,
incompletas o con objetos SQLite adicionales. No adopta variantes desconocidas.
La inspección estricta RAW SUADC-02 y los límites/rutas previos no se modifican.

Se probó la evidencia sobre RAW v1 y v2 temporales, incluyendo reapertura sin
migración. La nueva versión lee declaraciones antiguas sin paquete. Un ejecutable
anterior podría no entender declaraciones con la extensión JSON: no se debe usar
para leer o escribir nuevas adquisiciones documentadas. Es compatibilidad de
lectura hacia atrás, no una promesa de lectura por versiones anteriores del código.

No se conserva HTML original, encabezados HTTP, consultas, fragmentos ni credenciales.
Las referencias documentales sensibles se rechazan. La URL solicitada se conserva
sin credenciales/consulta/fragmento y `url_saneada` informa la omisión, incluidos
parámetros separados. Los IDs originales sensibles se rechazan, no se reescriben.
El cliente sigue rechazando credenciales y fragmentos en solicitudes. No cambian
orígenes autorizados, TLS, redirecciones, límites, reintentos ni publicación exclusiva.
La detección conservadora no reconoce cualquier secreto opaco: el llamador debe
aportar únicamente metadatos públicos revisados. SQLite permanece sin cifrado.

Si falla la preparación SQLite, no hay fila ni evidencia de adquisición confirmada.
Si falla después, el documento puede persistir con estado PREPARADA, VERIFICADA,
FALLIDA o INCONSISTENTE y tamaño/hash desconocidos cuando no se midieron. La
comprobación HTTP de una transferencia completa no convierte ese activo en disponible.
No se permite agregar ni corregir retrospectivamente su instantánea por esta API.
`diagnosticar()` sigue detectando operaciones incompletas, inconsistencias y residuos;
no repara, elimina ni confirma automáticamente. La integración informa el activo
cuando existe y cualquier staging restante; se preservan los originales previos.
Un fallo HTTP anterior a la preparación RAW no crea una adquisición persistida;
no se ha implementado un diario duradero de todos los intentos de red.

Uso secuencial, directorios privados y respaldo externo siguen siendo necesarios.
No hay transacción global entre red, los dos SQLite y archivos, ni garantía nueva
ante corte eléctrico o concurrencia hostil. La búsqueda por adquisición JSON y el
listado del diario carecen de índices específicos; su escalabilidad queda pendiente.

## Garantías y pendientes

Las pruebas comparan contenido físico, hashes, estados, identidades y revisiones;
no se limitan a ausencia de excepciones. Incluyen persistencia tras reapertura,
recursos e instituciones distintas, duplicados físicos, archivo vacío, evidencia
incompleta, secretos, errores SQLite, interrupción, datos previos y planificador.

La garantía técnica permanece: copia/lectura física, SHA-256 y tamaño locales,
publicación exclusiva y persistencia comprobadas en escenarios sintéticos. No
certifica autenticidad de SENAMHI, validez de licencia, estructura XLSX/CSV,
observaciones completas ni calidad científica. El éxito de MockTransport no
acredita disponibilidad actual de un servidor institucional.

Pendientes de aprobación: resolución de contradicciones de recursos, retención del
documento original, caducidad de evidencia, normalización relacional e índices si
crece el volumen, despliegue compatible de lectores, respaldo/restauración y pruebas
de durabilidad/concurrencia. No se accedió al RAW operativo ni se descargaron datos.

## Verificación final del PASO 65

Entorno comprobado: Python 3.15.1, HTTPX 0.28.1 y SQLite 3.53.4, usando
exclusivamente el intérprete de `.venv` con `-B`. La importación empezando por el
catálogo, seguida de RAW e integración, también aprobó; se añadió `src` a
`sys.path` únicamente en memoria para esa comprobación.

Estado inicial: rama `feature/suadc-http`, commit `4199e67`, árbol limpio. Estado
final: misma rama/commit, nueve archivos modificados y cuatro nuevos, sin commits.

```text
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
Ran 481 tests in 45.334s
OK

.\.venv\Scripts\python.exe -B -m pip check
No broken requirements found.

git diff --check
Código de salida: 0; sin errores de espacios.
Git avisa de conversión LF a CRLF futura en archivos modificados.

git status --short
 M docs/catalogo_cientifico.md
 M docs/conector_senamhi_pnda.md
 M docs/integracion_http_raw.md
 M src/spica/adquisicion/almacenamiento/catalogo.py
 M src/spica/adquisicion/almacenamiento/raw.py
 M src/spica/adquisicion/catalogo/__init__.py
 M src/spica/adquisicion/catalogo/persistencia.py
 M src/spica/adquisicion/conectores/senamhi/pnda.py
 M src/spica/adquisicion/integracion/http_raw.py
?? docs/registro_evidencias.md
?? src/spica/adquisicion/catalogo/documental.py
?? src/spica/adquisicion/catalogo/evidencias.py
?? tests/test_registro_evidencias.py
```

Resultado: 439 pruebas anteriores y 42 nuevas aprobadas; total 481, cero fallos,
cero errores y sin avisos de recursos abiertos en la suite final. Las cuatro
reproducciones inicialmente fallidas forman parte de las 42 nuevas. No se alteraron
las pruebas previas ni las correcciones de seguridad SUADC-01/SUADC-02.

Dictamen: **APTO CON RESTRICCIONES**, dentro del uso experimental secuencial y con
lectores actualizados. No se accedió, inicializó, migró ni modificó el RAW permanente
o su staging; no se inspeccionó su activo sintético. No hubo conexiones externas,
descargas reales, instalaciones, modificaciones de main.py/.venv ni commits/push.
La siguiente etapa y cualquier operación sobre almacenamiento permanente requieren
la revisión del usuario; esta verificación no las ejecuta ni las autoriza.
