# PASO 79 — Ingesta manual documentada

Implementación experimental y secuencial. Recibe un **archivo local expresamente
autorizado** y conserva sus bytes mediante el almacenamiento RAW existente. No
acredita autenticidad institucional, validez jurídica del permiso, estructura del
formato ni calidad científica. No utiliza el transporte HTTP.

## Alcance y extensión mínima

El PASO 78 quedó registrado en `6e1a0ec`; el repositorio estaba limpio antes de
esta implementación. Se reutilizan `DeclaracionRAW`, `AlmacenRAW`, sus identidades
MD-01/02/03, las transiciones, SHA-256, publicación exclusiva, deduplicación,
verificación física y diario SQLite. No se cambia la política HTTP ni se migra
un catálogo existente.

La evidencia anterior presupone una adquisición HTTP. Reutilizarla directamente
para una entrega local inventaría una URL, una fecha de respuesta o capacidad
HTTP. La extensión se explicó antes de modificar el núcleo:

- Nuevo paquete `adquisicion.manual`, independiente del transporte y conectores.
- `AlmacenRAW.incorporar_manual_documentado(...)` valida el recibo y delega en
  `_incorporar`, sin duplicar su copia, publicación ni comprobación física.
- Recibo JSON **v2**, discriminado por `mecanismo="importacion_manual"`, guardado
  junto al activo PREPARADA en `_evidencia_adquisicion`, ya existente.
- `consultar_evidencia()` y `consultar_adquisicion()` reconocen el recibo MANUAL
  además de la evidencia HTTP v1. Las respuestas HTTP existentes conservan su tipo
  y contenido. Los llamadores que mezclen mecanismos deben distinguir los tipos.
- `consultar_adquisicion(..., permitir_ausente=True)` devuelve `None` solo si no
  existe el evento. Una identificación ambigua sigue siendo un error. La llamada
  anterior sin la opción mantiene su comportamiento.

No se añaden tablas, columnas, estados RAW, índices ni migraciones. La versión
del **paquete JSON** no es la versión del **esquema SQLite**. El lector actualizado
conserva compatibilidad HTTP v1; un lector antiguo no entenderá recibos MANUAL v2.
No se garantiza compatibilidad de lectura en sentido inverso.

## Contratos

| Modelo | Información |
|---|---|
| `SolicitudIngestaManual` | Proyecto, objeto lógico, recurso, archivo local, procedencia y adquisición; mecanismo MANUAL fijo |
| `DocumentoManual` | Referencia autorizada, versión, fecha civil y descripción opcionales |
| `FundamentoUsoManual` | Documento de fundamento; permisos declarados para incorporación, publicación y redistribución; restricciones |
| `ProcedenciaManual` | Fuente/proveedor y producto declarados, entregante permitido, fechas de recepción/recurso, medio de entrega, documentos, privacidad, formato/MIME declarados y SHA-256 externo opcional |
| `PoliticaIngestaManual` | Tamaño máximo, bloque de lectura, margen de espacio y aceptación de vacíos |
| `ReciboIngestaManual` | Adquisición, instantánea del activo RAW y procedencia persistida; autenticidad NO_ACREDITADA |
| `ResultadoIngestaManual` | Recibo, ruta físicamente comprobada, instante UTC, resultado e integridad local |
| `ErrorIngestaManual` | Código y fase, adquisición, activo si se conoce y temporal pendiente si existe |

Los identificadores científicos conservan exactamente sus caracteres. El ID de
adquisición es un UUID hexadecimal de 32 caracteres, generado por defecto o
aportado para repetir explícitamente el mismo evento. No es el hash ni el activo.

Los metadatos institucionales desconocidos permanecen `None`. Se usan fechas
civiles `date`, sin inventar una hora ni zona; el instante técnico de incorporación
y de comprobación procede de RAW y sí lleva UTC. Las fechas civiles no expresan
precisión horaria. Un SHA-256 externo se acepta en hexadecimal minúsculo de 64
caracteres; no se normalizan silenciosamente valores mal formados.

`DeclaracionRAW` exige una `Fuente`. Si el proveedor es desconocido se utiliza
`Fuente("SPICA", "recepcion-manual-local")` **como identidad del procedimiento
local**, mientras `fuente_declarada` permanece `None` en la evidencia. No se
atribuye el archivo a SPICA como institución productora ni se deduce una fuente
por su nombre.

Se exige un documento de fundamento y la declaración explícita
`permite_incorporacion=True`. El documento puede ser una referencia local opaca
aprobada; no necesita una URL. Su existencia externa, autenticidad y alcance legal
no se comprueban. La publicación/redistribución son permisos independientes:
`None` significa desconocido, nunca autorización implícita. Un entregante solo se
admite con `registro_entregante_permitido=True`. La marca `privado` y las
restricciones son metadatos declarados; no constituyen control de acceso técnico.

No se persisten ruta del origen, nombre original, URL ficticia, estado HTTP,
cabeceras, sesión, servidor ni evidencia de autenticación. La referencia documental
se conserva, pero este paso no archiva automáticamente los documentos asociados.

## Flujo y uso de recursos

`IngestorManual` recibe un `AlmacenRAW` abierto, raíces de origen explícitas y un
staging **ya preparado**, autorizado por ese almacén. No inicializa ni migra RAW,
no crea las raíces y no configura permisos operativos.

1. Valida contrato, fundamento declarado y metadatos no sensibles.
2. Comprueba autorización de ruta, archivo regular, tamaño y política de vacíos.
3. Busca el evento anterior y aplica la política de idempotencia.
4. Comprueba espacio libre en staging y RAW. Si comparten volumen estima dos
   copias del tamaño inicial más margen; en volúmenes distintos, una por volumen.
5. Crea un subdirectorio aleatorio exclusivo `suadc-manual-*` y `contenido.bin`
   con creación `xb`. No usa el nombre del archivo entregado para publicar.
6. Lee bloques acotados, copia, cuenta bytes, calcula SHA-256 y detecta cambios
   observables de identidad/tamaño/mtime entre ruta y descriptor.
7. Vacía buffers y ejecuta `fsync` sobre la copia. Contrasta el hash externo
   únicamente si existe; una discrepancia impide la incorporación.
8. RAW recibe tamaño/hash esperados y el recibo. Relee la copia, comprueba su
   continuidad, publica por su mecanismo exclusivo y registra las transiciones.
9. `recuperar()` verifica físicamente el contenido publicado. Se relee la evidencia
   persistida, comprobando identificadores, metadatos, estado, tamaño y hash.
10. Se limpia exclusivamente el temporal propio; solo entonces se devuelve éxito.

Por defecto: máximo 128 MiB, bloque 65 536 bytes y margen 16 MiB; los vacíos se
aceptan. El máximo manual no puede superar el del almacén. Estos valores son
políticas locales revisables, no condiciones atribuidas a una institución. El
límite de respuestas pequeñas de HTTP `get()` permanece en 1 MiB.

Hay una copia de staging y la copia temporal que necesita la incorporación RAW;
no una tercera copia completa añadida. Las verificaciones releen por bloques. El
espacio libre es una estimación previa, **no una reserva**; crecimiento concurrente,
metadatos SQLite y consumo ajeno aún pueden provocar errores. No se deduplica
saltando la lectura o confirmando únicamente metadatos.

## Seguridad y privacidad

- Orígenes limitados a raíces absolutas explícitas y disjuntas de RAW y entradas.
  No se permite una raíz que contenga RAW/staging ni la raíz de un volumen.
- El archivo no puede estar en RAW ni en ninguna raíz de entrada configurada.
  Se rechazan `..`, UNC, ADS de Windows y rutas ambiguas antes de abrir el archivo.
- Se inspeccionan ruta y antecesores: symlinks, junctions y otros reparse points
  se rechazan. Se exige archivo regular y un único enlace duro en el origen.
- El origen se abre solo como bytes de lectura. No se ejecuta, importa, interpreta
  ni convierte el contenido; su extensión/formato declarado no prueba estructura.
- La publicación, comprobación del contenido preexistente y protección frente a
  sobrescritura son las de RAW; la ingesta no introduce una publicación alternativa.
- El filtro de metadatos existente rechaza credenciales/URL ambiguas reconocibles.
  No es un detector universal de secretos. Las referencias deben revisarse antes
  de suministrarlas y ser apropiadas para persistencia en un catálogo sin cifrar.
- `diagnostico_publico()` omite rutas y texto de excepciones subyacentes. La ruta
  física del resultado y `temporal_restante` son datos para recuperación privada;
  no se deben registrar automáticamente ni volcar objetos completos en logs.

En Windows se evita el modo especial `0700` de Python 3.15 para crear el temporal,
siguiendo el comportamiento comprobado de los fixtures/RAW del proyecto. El modo
de creación no acredita privacidad: **staging, orígenes y RAW deben estar bajo
permisos privados previamente administrados**. Este paso no cambia ACL.

## Estados, integridad y autenticidad

`INCORPORADA` es un evento nuevo completado y recomprobado; `YA_REGISTRADA` es el
mismo evento recuperado y recomprobado. Ambos resultados tienen
`COMPROBADA_LOCALMENTE`. Un archivo vacío legítimo tiene tamaño cero y el SHA-256
real del contenido vacío, no una excepción a las comprobaciones.

El recibo consultado es una **instantánea de metadatos**, no una nueva prueba
física. El resultado positivo proviene del flujo con `recuperar()`. Los errores
de lectura, permisos, disco, cancelación o SQLite no se presentan como corrupción:
el error manual usa `NO_COMPROBADA`. Solo una comparación externa realmente
efectuada y discrepante usa `HASH_EXTERNO_DISCREPANTE`. RAW conserva su diagnóstico
específico para corrupción/ausencia detectadas; el envoltorio no inventa evidencia
adicional. `hash_externo_coincide` es `None` cuando falta hash externo.

La autenticidad sigue **NO_ACREDITADA** incluso si el hash externo coincide. Una
fuente, permiso, formato o documento declarados no se convierten en verificación
institucional o científica.

## Deduplicación, idempotencia y recuperación

Dos adquisiciones con IDs distintos conservan activos y documentos separados. Si
coinciden bytes, RAW comprueba y comparte contenido físico por SHA-256. No se
reescribe ni elimina la adquisición anterior. Un contenido preexistente corrupto
provoca error; no se sustituye para aparentar una deduplicación satisfactoria.

Repetir el mismo ID exige declaración y procedencia idénticas, fuente local
presente con los mismos bytes y activo INCORPORADA. Se releen origen y RAW, sin
otra copia completa ni nueva adquisición. Cambiar contenido o procedencia exige
un nuevo evento legítimo, no la alteración silenciosa del anterior.

| Situación | Comportamiento y recuperación |
|---|---|
| Error antes de preparar RAW | Limpieza del temporal; sin evento persistido. Puede hacerse un nuevo intento explícito una vez resuelta la causa |
| Hash externo discrepante | No incorpora; informa comparación negativa y limpia staging |
| Fallo en copia RAW o SQLite | Propaga código, adquisición y activo si existe; no declara éxito |
| Fallo tras preparar/publicar | Conserva el recibo y los bytes publicados cuando existan; estado FALLIDA/PREPARADA/VERIFICADA exige revisión; repetir el ID no reinicia automáticamente |
| Cancelación | `threading.Event`, comprobado antes de abrir, entre bloques de copia y alrededor de RAW; no interrumpe internamente la copia RAW existente |
| Cancelación después de incorporar | Puede existir activo completo aunque no haya resultado exitoso. Consultar el evento; su repetición explícita puede recomprobarlo sin duplicarlo |
| `KeyboardInterrupt`/`SystemExit` | Limpia staging en lo posible y propaga la interrupción; consultar el ID para conocer si RAW llegó a preparar/incorporar |
| Limpieza imposible o archivo ajeno en temporal | No devuelve éxito. Informa temporal privado pendiente; no borra contenido ajeno ni originales |

Reconciliación **manual**, no automática: consultar la adquisición, sus metadatos,
`diagnosticar()` y los temporales propios; verificar físicamente lo recuperable y
decidir la reparación con autorización. No se debe borrar el catálogo, promover
estados ni generar IDs nuevos para ocultar una operación incierta.

No hay atomicidad global entre archivos y SQLite. No hay unicidad SQL nueva del
ID de adquisición ni bloqueo coordinado multiproceso: la idempotencia es para el
modelo **secuencial**. La detección de ambigüedad falla de forma conservadora.

## Verificación y limitaciones pendientes

`tests/test_ingesta_manual.py` usa exclusivamente bytes inventados y SQLite en
directorios temporales aislados. Cubre integridad, persistencia/reapertura,
desconocidos, entrega privada, permisos declarados, tamaño, vacíos, copia acotada,
errores/interrupción, fuente cambiante, rutas/enlaces, duplicación histórica,
idempotencia, fallos antes/después de publicación, residuos y ausencia de red.
Las pruebas de symlink/junction/reparse simulan su detección; la de enlace duro
utiliza un enlace real dentro del fixture. No certifican todas las carreras del SO.

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -B -m pip check
git diff --check
git status --short
```

La protección frente a modificaciones observables no es una instantánea bloqueada.
Un escritor hostil puede alterar/restaurar metadatos o sustituir directorios entre
comprobaciones; se presupone control privado y uso secuencial. No se demuestra
resistencia a cortes eléctricos, durabilidad de directorios, inmutabilidad,
concurrencia, firma documental ni preservación futura. Un cierre forzado puede
dejar temporales; no hay barrido automático al iniciar ni reintentos automáticos.

Quedan pendientes la aprobación operativa de permisos/retención, cifrado y control
de acceso para privados, recuperación coordinada, firmas institucionales y una
representación de fechas con precisión horaria si un caso aprobado lo requiere.
ANA, OEFA, INGEMMET, laboratorios y estaciones privadas pueden ser fuentes
**declaradas** del mismo contrato; no se implementan reglas ni se atribuyen
formatos o autorizaciones oficiales a esas entidades.

No se implementan GUI, autenticación institucional, verificación estructural,
extracción de observaciones, conversiones, procesamiento científico, QA/QC Nivel 1,
readquisición HTTP ni integración espacial. No se hizo una ingesta de datos reales
ni se accedió al RAW, staging o SQLite operativo durante esta implementación.

## Resultado de la verificación del PASO 79

Verificado el 30 de octubre de 2026 con Python **3.15.1** del entorno `.venv`,
HTTPX **0.28.1** y SQLite **3.53.4**:

- Suite completa: **989 aprobadas**, 0 fallidas, 0 con errores y 0 omitidas;
  `unittest` informó **118.553 s**.
- **938 anteriores + 51 nuevas**. Se compararon los identificadores de las 938
  pruebas con el registro del PASO 78: coinciden, sin IDs duplicados en la suite.
- `python -B -m pip check`: `No broken requirements found.`
- `git diff --check`: correcto; Git avisa de la conversión LF/CRLF configurada.
  También se revisaron por separado los seis archivos nuevos sin seguimiento:
  UTF-8, sintaxis Python y espacios al final de línea.
- Sintaxis válida en los 63 archivos Python de `src/` y los 27 de `tests/`, sin
  generar bytecode. Los tests anteriores y los archivos seguidos fuera del alcance
  permanecen intactos respecto a HEAD.
- La suite completa se ejecutó con una guardia temporal externa al repositorio
  que bloquea operaciones sobre `SPICA_DATOS` y conexiones/DNS reales: instalada
  en ambos procesos de verificación, **cero intentos bloqueados**. La declaración
  de no acceso no se basa en abrir o hashear los archivos operativos.

Git inicial: rama `feature/suadc-http`, HEAD `6e1a0ec`, limpio. Al terminar hay
cuatro archivos modificados y seis nuevos correspondientes a este paso; no se
realizaron commits. El informe completo de pruebas y los resultados de la guardia
se conservan en el directorio temporal de auditoría de la sesión, fuera de Git.

**Dictamen: APTO CON RESTRICCIONES.** Implementación experimental comprobada con
datos sintéticos, para operación secuencial sobre directorios privados. Requiere
revisión de permisos, privacidad y recuperación antes de autorizar archivos reales.
No autoriza por sí misma una operación sobre el almacén permanente.
