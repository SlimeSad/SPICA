# PASO 83-C: preparación y simulación del piloto vectorial

## 1. Alcance y dictamen

**APTO CON RESTRICCIONES para revisión offline. El GET institucional continúa
bloqueado y no se ha ejecutado.** La preparación no autoriza red, consulta de
entidades, publicación RAW ni uso científico. Las simulaciones prueban controles
locales, sin acreditar que INGEMMET admita la operación o sus parámetros.

Estado inicial comprobado: rama `feature/suadc-http`, árbol limpio, HEAD `19e8fcc`
(`SUADC: precision numerica y auditoria vectorial ArcGIS`, PASO 83-B). Anteriores:
`f8b3df9` y `313363e`. No se modifican los módulos estables ni sus contratos.

Revisión exclusivamente local del
[expediente](expediente_ingemmet_geologia_50k.md), la
[matriz GIS](matriz_interoperabilidad_ingemmet.md), el
[informe de metadatos](validacion_metadatos_ingemmet_paso82.md) y el
[protocolo 83-B](protocolo_piloto_arcgis_paso83b.md). Sus referencias E-01/E-06
respaldan la identificación del producto y anuncios de metadatos; no demuestran
consultas de entidades. No se abrió la evidencia institucional del PASO 82-C,
ni se consultaron sitios o documentación externos.

## 2. Archivos y arquitectura

| Archivo | Responsabilidad |
|---|---|
| `src/spica/adquisicion/piloto_arcgis/modelos.py` | Contratos congelados, candidato cerrado, estados y presupuestos |
| `src/spica/adquisicion/piloto_arcgis/simulador.py` | Un intercambio sintético, validación acotada y diagnósticos |
| `src/spica/adquisicion/piloto_arcgis/evidencia.py` | Evidencia temporal sintética, reapertura y comprobación física |
| `src/spica/adquisicion/piloto_arcgis/__init__.py` | Exportaciones del paquete separado |
| `tests/test_piloto_arcgis.py` | Preparación, simulaciones y barreras de ejecución |
| `tests/test_evidencia_piloto_arcgis.py` | Integridad, privacidad, errores y limpieza de temporales |
| `docs/simulacion_piloto_arcgis_paso83c.md` | Informe y protocolo consolidado del PASO 83-C |
| `docs/protocolo_piloto_arcgis_paso83b.md` | Anotación de continuidad, sin reescribir la evidencia histórica |

Los primeros siete son nuevos; únicamente el último modifica un archivo previo.
No se cambia `ClienteHTTP`, RAW, SQLite, catálogo, QA/QC ni el coordinador vectorial.

Reutilización comprobada:

- El lector JSON común controla bytes, profundidad, nodos, cardinalidad, texto,
  duplicados y números antes/durante la materialización. Se usa precisión decimal
  exacta con límites de token/exponente del PASO 83-B.
- Se reutilizan `RespuestaSintetica`, `CampoVector`, el control de valor tipado
  OID y `EntidadVector` con atributos inmutables. El OID sigue siendo `int` exacto,
  sin convertirse a float ni en identidad lógica de un objeto científico.
- El validador FeatureSet existente exige un contrato geométrico y CRS. Un sobre
  mínimo de atributos puede omitirlos: se añade una validación específica de ese
  sobre, reutilizando el lector y los tipos, sin fabricar un CRS ni debilitar el
  validador estable. No valida geometrías o sistemas de referencia.
- El coordinador de páginas se inspeccionó y se conserva. No se invoca: podría
  continuar una colección y sus solicitudes utilizan identidad de adquisición.
  El ensayo usa identidad propia, no una adquisición institucional ficticia.
- Se inspeccionaron los controles de `ClienteHTTP`: origen, TLS, identity,
  timeouts, ausencia de redirecciones y política de intentos. Se reutilizarían
  después de otra revisión y autorización. El simulador no lo importa ni acepta
  un backend HTTP; no se añade otro cliente.

`PreparacionEnsayo` fija institución/producto objetivo, servicio/capa, identidad
`ensayo-sintetico-*`, objetivo, GET, host/ruta candidata, parámetros copiados a un
mapa inmutable, máximo de bytes/entidades, prohibición de geometría, evidencia,
diagnósticos, motivos de detención y autorización pendiente. Solo puede reducirse
el presupuesto de bytes. No existe un estado de autorización aprobada.

`SolicitudSimulada` tiene destino literal `fixture://spica/piloto-arcgis/atributos`.
La URL institucional es texto declarativo en la preparación y en el registro,
sin consumidor que pueda ejecutarla. `EscenarioSintetico` contiene exactamente
una respuesta inventada o un fallo enumerado; no acepta callbacks, transportes,
iterables de páginas ni identidades de adquisición/instantánea.

`SimuladorEnsayo.ejecutar()` consume la instancia una sola vez, incluso con fallo
o cancelación. Sin segunda operación, reintentos, paginación ni fallback. Es un
modelo secuencial por instancia, no un registro global de ensayos ni un mecanismo
de exclusión entre procesos. Python confiable puede crear otra instancia: eso no
añade capacidad de red. No se pretende aislar código Python malicioso.

## 3. Solicitud candidata y límite remoto pendiente

Institución objetivo: INGEMMET. Producto referido en el expediente: Mapa Geológico
Integrado del Perú a escala 1:50.000. Servicio `SERV_GEOLOGIA_50K_INTEGRADA`, capa
`Litologia`, ID `7`. No se inventa un identificador oficial del producto.

Endpoint candidato **no verificado funcionalmente**:

```text
https://geocatminnube.ingemmet.gob.pe/arcgis/rest/services/SERV_GEOLOGIA_50K_INTEGRADA/MapServer/7/query
```

Lista cerrada, idéntica al protocolo 83-B:

| Parámetro | Valor literal |
|---|---|
| `f` | `json` |
| `where` | `1=1` |
| `outFields` | `objectid` |
| `returnGeometry` | `false` |
| `resultOffset` | `0` |
| `resultRecordCount` | `1` |
| `orderByFields` | `objectid ASC` |

`where` es una constante cerrada, nunca una expresión suministrada por el usuario.
Se rechazan parámetros adicionales o ausentes, `objectIds`, tokens, cambios de
host/ruta/método, geometría, offset siguiente y tamaños de página mayores.

**Sin ObjectID de entidad previamente acreditado**, puede formularse la petición
de una fila anterior, sin consulta preliminar, pero no garantizar que el servicio
aplique `resultRecordCount`. No se ha probado ni documentado aquí ese soporte.
`orderByFields` tampoco garantiza un orden o instantánea estables. No se inventa
un OID, no se solicita una lista de IDs ni se presume soporte de estos parámetros.

El cliente puede limitar bytes y aceptar como máximo una entidad **después de
recibir el cuerpo**. Ese rechazo no impide haber recibido varias entidades ni
acredita un límite de transferencia de una entidad. Por tanto, la propuesta
todavía **no cumple una garantía remota razonable de máximo una entidad**. El
GET permanece bloqueado hasta acreditar el límite con evidencia aplicable y
revisar el protocolo. Si eso exige ampliar el alcance o consultar previamente,
hará falta otra decisión expresa; no se ejecuta una comprobación para averiguarlo.

## 4. Barreras, resultados y presupuestos

No hay importación de HTTPX, transporte común, integración HTTP→RAW, sockets o
almacenamiento en el paquete nuevo. Tampoco argumentos para activarlos. La barrera
no depende del booleano informativo `autoriza_red=False`: la ruta de ejecución
institucional no existe en este prototipo.

El presupuesto del cuerpo es como máximo **65536 bytes**; puede reducirse, nunca
ampliarse. El parser limita profundidad a 16, nodos a 10000, elementos de listas
a 64, propiedades a 64 y cadenas a 4096. Los límites numéricos heredados son
256 caracteres y exponente absoluto 4096. Un OID válido es entero no negativo
de hasta 64 bits con signo, preservado exactamente.

Los presupuestos no representan una cota de tráfico HTTP/TLS, cabeceras, RSS o
memoria que use el llamador para construir una fixture excesiva. La simulación
no es un receptor streaming: recibe `bytes` ya existentes y no retiene ni calcula
hash de cuerpos superiores a la cota. No se prometen estas garantías de red.

Estados independientes:

| Dimensión | Estados y significado |
|---|---|
| Ensayo | Coherente, vacío sin demostrar el objetivo, requiere revisión, fallo sintético, cancelado |
| Recepción | Sin respuesta, completa sintética, incompleta, presupuesto excedido |
| Validación | No realizada, coherente, vacía, rechazada, limitada por presupuesto |
| Autorización | Siempre pendiente, sin permiso operativo |
| Completitud institucional | Siempre desconocida |

Una recepción completa no implica JSON válido. Un JSON completo no implica un
sobre compatible. Un sobre compatible no demuestra operación institucional,
licencia, validez científica o completitud de una colección. El contrato rechaza
hash/tamaño contradictorios, HTTP 206 o longitud discrepante como recepción
completa y éxito sin validación/sintaxis/entidad correspondientes.

Los cuerpos completos dentro de la cota se conservan sin reserializar; los
parciales se conservan identificados como parciales. Una respuesta excesiva solo
produce metadatos del exceso, sin archivo de cuerpo ni hash inventado. Sin
respuesta no se inventan código HTTP, bytes, entidad o hash. Capa/servicio
declarados se contrastan; su ausencia no se rellena como si hubiera sido recibida.
La identidad de capa contradictoria se conserva en el diagnóstico observado.

`exceededTransferLimit=true` con una entidad se registra como selección parcial,
sin continuar y sin declarar completitud. `false` o ausencia tampoco prueban
completitud institucional. Vacío con continuación anunciada se rechaza por
contradicción. Un resultado vacío coherente se distingue de un error, pero no
demuestra que el servicio o la capa real estén vacíos ni satisface el objetivo.

## 5. Simulaciones y comprobaciones

Todos los datos se construyen en memoria en las pruebas. Por ejemplo, el entero
`9007199254740993` es **inventado**, elegido para detectar redondeo sobre 2^53;
no procede de una entidad real. No se reutilizan IDs, hashes o archivos de una
adquisición ni evidencia real como fixture.

| Caso sintético | Resultado esperado y comprobado |
|---|---|
| 200, FeatureSet de atributos, una entidad sin geometría | Coherente, OID exacto; capacidad institucional no demostrada |
| Sobre mínimo sin fields/CRS/capa | Validación contra el contrato y diagnóstico de ausencias; no se inventan metadatos |
| 200 con `error` ArcGIS | Rechazado; código fijo sin imprimir mensaje del cuerpo |
| Features vacío | Estado vacío separado; objetivo no demostrado |
| Más de una entidad | Rechazado, ninguna entidad promovida |
| Geometría, incluso `null` | Rechazado |
| JSON inválido, truncado, claves duplicadas, NaN | Rechazado; no se confunde con recepción de bytes incompleta |
| Exceso de complejidad o presupuesto numérico | Validación limitada, ninguna entidad promovida |
| Exactamente 64 KiB / 64 KiB + 1 | Primero admisible si válido; segundo excedido sin hash/copia retenida/parseo |
| Content-Length discrepante | Recepción incompleta, sin evaluación de entidades |
| Redirección, error HTTP, compresión, MIME ajeno | Revisión, sin segunda operación ni descompresión |
| Error de conexión o timeout | Fallo sintético, sin respuesta o hash ficticios |
| Cancelación previa o durante validación | Cancelado, sin entidades; instancia consumida |
| HTTP 206, transferencia incompleta o interrupción | Recepción incompleta, no se acepta como completa |
| Atributo extra / OID ausente o inválido | Rechazado, sin conversiones silenciosas |
| Identidad de capa, servicio o descriptor incompatible | Rechazado; no se rellena con valores esperados |
| Repetición o continuación | RuntimeError de operación consumida |
| Corrupción de archivo temporal, hash o tamaño contradictorio | Detención sin entregar evidencia verificada |
| Error de escritura o interrupción de contexto | Limpieza del temporal propio; mensaje técnico fijo |

Se comprueban determinismo con fecha/identidad fijas, importación sin cliente
HTTP, ausencia de backend, restricciones de host/ruta/parámetros y ausencia de
llamadas del simulador a red, archivos y SQLite. La persistencia temporal se
prueba por separado; las pruebas unitarias previas conservan sus fixtures propias.

## 6. Evidencia sintética, privacidad y límites de persistencia

`conservar_evidencia(resultado)` es un contexto sin argumento de destino. Crea un
subdirectorio exclusivo de `tempfile.gettempdir()`, con los permisos privados que
establece `TemporaryDirectory` en Python 3.15. No modifica ACL existentes. Rechaza
bases relativas o UNC, el repositorio de código, componentes `.git`/`.venv`, la
raíz personal `SPICA_DATOS` y sus descendientes **antes de inspeccionarlos**;
rechaza symlinks/junctions de la base
y sus ancestros. No admite nombres de archivo del servidor.

Nombres fijos: `respuesta.bin` (solo si existen bytes dentro de la cota) y
`registro.json` (máximo 32768 bytes). Ambos se crean con modo exclusivo `xb`.
Se cierran y reabren; el cuerpo se compara byte por byte y por SHA-256 con los
bytes de la fixture, y el registro se compara con sus bytes escritos y se hashea.
La comprobación física corresponde únicamente a esos archivos sintéticos.
No es firma institucional, comprobación de archivo RAW ni validación científica.
Un cuerpo parcial puede verificarse físicamente sin declarar completa la recepción.

El registro distingue destino simulado de candidato declarativo y contiene:
identidad sintética, parámetros exactos, estado HTTP sintético, tamaño observado,
longitud declarada, hash disponible, fecha de evaluación UTC, estados, sintaxis,
OID/capa observados, precisión, completitud desconocida, restricciones, diagnósticos
y fecha/comprobación física. Declara capacidad institucional y TLS ejercido como
falsos. No conserva cookies, autorización ni cabeceras arbitrarias; no se registran
credenciales o mensajes de error institucional. Las excepciones técnicas de disco
no imprimen rutas o mensajes internos; no deben publicarse tracebacks completos.

Los archivos **solo existen dentro del contexto**: limpieza en salida normal,
excepción e interrupción Python. No se promete limpieza tras corte de energía,
terminación forzada, fallo de permisos o antivirus. No hay fsync, par transaccional,
reserva de espacio, respaldo, preservación forense persistente o recuperación de
temporales huérfanos. Un error de limpieza se propaga, sin reparar borrando datos
ajenos. La prueba de escritura no es una reserva de espacio futuro.

Modelo de seguridad: usuario y configuración TEMP confiables, directorios
controlados, uso secuencial y ausencia de cambios concurrentes de rutas. No se
garantiza defensa contra administradores, ACL ajenas, sustituciones TOCTOU,
hardlinks maliciosos o aliases desconocidos de un almacén personalizado. No se
acepta un destino RAW ni se publica mediante el adaptador. La privacidad efectiva
y retención para **evidencia institucional futura** necesitan otra aprobación;
el escritor efímero de fixtures no debe reutilizarse automáticamente para ello.

## 7. Derechos: revisión local, sin autorización inferida

| Uso | Evidencia local disponible | Estado |
|---|---|---|
| Consulta de atributos | OID anunciado en E-06; protocolo candidato 83-B | Pendiente de condiciones aplicables y autorización del ensayo |
| Consulta de geometrías | Polygon anunciado, sin adquisición de geometrías | Pendiente y fuera del piloto |
| Conservación de resultados de entidades | Conservación histórica de metadatos de alcance específico | No extensible automáticamente; retención y permiso pendientes |
| Uso interno | Ningún término aplicable acreditado para entidades | Pendiente |
| Uso académico | Ningún término aplicable acreditado | Pendiente; la finalidad académica no concede permiso |
| Elaboración de derivados | Sin licencia/metodología aplicable acreditada | Pendiente |
| Redistribución | Sin permiso aplicable acreditado | Pendiente; no publicar resultados institucionales |

El protocolo anterior señala una página externa de licencia, no leída en esta
etapa. Se desconocen texto, versión/fecha, vigencia y vinculación con servicio y
capa. No se afirma licencia abierta ni prohibición. Un anuncio de Query, acceso
público o autorización de un ensayo anterior no resuelve estos permisos. Los
resultados sintéticos no cambian la confianza documental de esas referencias.

## 8. Protocolo consolidado para un GET futuro, no ejecutable aquí

1. Acreditar correspondencia de endpoint/capa y condiciones de consulta/conservación,
   usando documentación aplicable y sin extender permisos históricos.
2. Resolver el bloqueo del máximo remoto de una entidad. Revisar íntegramente el
   endpoint y los siete parámetros de la sección 3; no inventar `objectIds`.
3. Obtener autorización expresa de ese único GET. La preparación y este informe
   no la conceden. No existe un adaptador institucional activable en el simulador.
4. Tras otra implementación/revisión autorizada, reutilizar `ClienteHTTP.get()` con
   `ConfiguracionHTTP(max_bytes_respuesta=65536, verificar_tls=True)` y
   `PoliticaReintentos(max_intentos=1)`. Origen exclusivo HTTPS del host candidato,
   ruta cerrada, sin credenciales/proxies del entorno, redirecciones ni fallback.
5. Timeouts previstos: conexión 10 s, lectura/escritura 30 s, pool 10 s. No equivalen
   a plazo total. Contar bytes efectivos, no confiar solo en Content-Length;
   rechazar 206, compresión, longitud incoherente, MIME ajeno y cualquier exceso.
6. Definir y aprobar antes la carpeta privada, espacio (propuesta: mínimo 16 MiB,
   sin reserva), retención y manejo de evidencia inesperada. Conservar bytes
   primarios disponibles, URL/parámetros exactos aprobados, fechas UTC, estado,
   intentos, hash real y versión/políticas. Verificar físicamente solo lo escrito.
7. Aplicar el sobre mínimo probado: JSON completo sin duplicados, máximo una
   entidad/OID exacto y ningún otro atributo o geometría. Ausencias no se rellenan.
   No afirmar completitud, validación científica o derechos por un resultado coherente.
8. Detener ante destino distinto, permisos pendientes, autenticación, TLS, HTTP
   inesperado, respuesta parcial, exceso, incoherencia, vacío, error ArcGIS/JSON,
   identidad incompatible, geometría, atributos extra, fallo de persistencia o
   cancelación. No segunda petición, cambios de parámetros, paginación ni reparación.
9. Si el transporte entrega solo un error y no bytes, registrar únicamente esa
   evidencia disponible. No modificar el cliente ni repetir GET para recuperarla.
10. Revisar el resultado humano antes de cualquier etapa posterior. Sin RAW,
    SQLite operativo, geometrías, colección, QA/QC o procesamiento científico.

## 9. Verificación final

Python 3.15.1, HTTPX 0.28.1 y SQLite 3.53.4 comprobados con `.venv`. No se instalan paquetes.
Se ejecuta Python con `-B` y ruta `src/` temporal en el entorno, sin editar configuración.

El aislamiento de Codex denegó el acceso a temporales privados `0700` de Python
3.15 en el primer pase focalizado. La repetición con permisos normales del usuario
aprobó los casos, conservando la guardia de red/rutas operativas; no se cambiaron
ACL ni se sustituyeron permisos privados por permisos más amplios.

Comandos ejecutados, usando `PYTHONPATH=src/` temporal y la guardia adicional:

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -B -m pip check
git diff --check
git status --short
git ls-files --others --exclude-standard
```

La ejecución verbose se conserva completa en un log temporal externo al repositorio.
Se comparan los IDs de las pruebas anteriores obtenidos de `git show HEAD:tests/...`
con las pruebas ejecutadas: **1293 anteriores + 38 nuevas = 1331 aprobadas**,
**0 fallidas, 0 errores, 0 IDs anteriores ausentes, 0 IDs duplicados**.
`pip check`: `No broken requirements found.` Los seis archivos Python nuevos
compilan en memoria, sin bytecode, y no contienen definiciones duplicadas en un
mismo ámbito. Se revisan también UTF-8, finales de archivo, espacios y enlaces
locales de la documentación. `git diff --check` no cubre archivos sin seguimiento:
estos se inspeccionan por separado.

Último pase completo: **1331 pruebas en 154.828 s, OK**, después de añadir el
rechazo de bases TEMP dentro del repositorio o UNC. El log verbose, el resumen
JSON y los registros de guardia se conservan para revisión en el temporal
`%TEMP%\spica-paso83c-a38fe12f34094c4282c713d2ca1a7aad`. No son evidencia de
adquisición institucional. Los ocho directorios vacíos que dejó el pase inicial
bloqueado por el aislamiento se inspeccionaron y retiraron exclusivamente por
sus nombres/rutas verificadas, sin recursión ni modificación de ACL. Los contextos
de evidencia de las pruebas completadas se limpian normalmente.

Git final conserva rama y HEAD iniciales. Único archivo previo modificado:
`docs/protocolo_piloto_arcgis_paso83b.md`; siete archivos nuevos enumerados en la
sección 2. No hay cambios en módulos estables, pruebas anteriores, `main.py`,
`.gitignore` o dependencias. No se hace commit, push, instalación ni migración.

Durante las comprobaciones Python se instala una guardia temporal de auditoría
que bloquea sockets/DNS y accesos a `SPICA_DATOS` y a la evidencia institucional
anterior. La guardia genera registros por proceso, fuera de Git. No se usa una
comparación de hashes operativos: requeriría abrir los originales prohibidos.
La afirmación se limita a ausencia de accesos de nuestros comandos y pruebas,
sin certificar actividad ajena o el estado físico actual de los almacenes.

El nuevo paquete usa helpers internos del lector y del validador: cambios futuros
en ellos requieren mantener estas regresiones. La API del ensayo es experimental;
no es un adaptador listo para añadirle una URL o activar un booleano de red.

El piloto real permanece bloqueado por permisos, soporte del límite remoto,
correspondencia de ruta/parámetros, implementación operativa revisada, política
de evidencia institucional y autorización expresa. Estas tareas no se completan
por simulación ni se adelantan en este paso.
