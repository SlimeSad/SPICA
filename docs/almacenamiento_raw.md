# Almacenamiento RAW experimental del SUADC

El paquete `spica.adquisicion.almacenamiento` conserva copias locales sin transformar
los bytes y registra trazabilidad técnica en SQLite. No descarga, procesa valores
científicos ni certifica autenticidad institucional. Solo usa biblioteca estándar.
No modifica los contratos del núcleo ni los transportes existentes.

## Identidad y organización provisional

Se implementa la compatibilidad estructural con los campos de MD-01/02/03
proporcionados en el paso 51. No presupone conformidad científica ni requisitos
adicionales de documentos no disponibles en el repositorio.

- Proyecto: identificador lógico declarado, independiente de carpetas.
- Objeto: identificador lógico declarado, vinculado a un proyecto, independiente
  del hash de cualquier archivo. En esta versión su ID es único en el catálogo;
  no puede cambiarse de proyecto mediante una incorporación.
- Activo/incorporación: UUID nuevo por operación, incluso para el mismo recurso
  y contenido. El nombre original no se usa como identidad.
- Contenido físico: `sha256/<dos primeros caracteres>/<hash completo>`.

Dos activos pueden compartir contenido físico y conservar su propia procedencia.
La igualdad se decide mediante tamaño y SHA-256 reales; se presupone la resistencia
a colisiones de SHA-256. No hay comparación científica ni equivalencia semántica.

El directorio RAW debe existir, ser dedicado y estar bajo control del llamador.
Contiene `catalogo.sqlite3`, `temporales/` y `sha256/`. Ubicación operativa preferente:
`C:\Users\Propietario\SPICA_DATOS\raw`, fuera del repositorio. El operador debe
prepararla con permisos privados y pasarla explícitamente al constructor: no hay
una ruta predeterminada ni creación automática de ese directorio.

La alternativa interna convencional es `<repositorio>/datos/raw/`. `.gitignore`
excluye únicamente `/datos/raw/`, incluyendo catálogo, journals, contenido y temporales.
No excluye todo `datos/`, archivos SQLite globalmente ni código/documentación/pruebas.
Una ubicación interna diferente no queda protegida por esa regla. La exclusión
evita adiciones ordinarias accidentales, no `git add -f` ni archivos ya versionados.
No se creó almacenamiento operativo ni se movieron/eliminaron datos existentes.

## API

Preparar directorios de entrada y RAW separados y existentes. El constructor
`AlmacenRAW(directorio, raices_entrada, *, max_bytes=10*1024**3,
tamano_bloque=65536, claves_parametros_publicos=())` autoriza explícitamente los
directorios desde los que se podrán incorporar archivos. Los bloques son de hasta
1 MiB y el tamaño máximo se aplica a **nuevas incorporaciones**, tanto por metadatos
como contando bytes reales. No limita la verificación de originales ya catalogados.
Usar `with` o `close()` para cerrar el catálogo.

`DeclaracionRAW` incluye proyecto, objeto, `Fuente` existente, identificador original
del recurso, procedencia pública y parámetros públicos opcionales, formato declarado
y tipo de medio declarado. Los identificadores aceptados se conservan exactamente;
no se recortan espacios ni se cambian códigos. Formato y tipo de medio se etiquetan
como **declarados**; no se deducen del nombre ni se registran como comprobados.

- `incorporar(archivo, declaracion) -> ActivoRAW`: copia, comprueba y publica.
- `metadatos(activo_id)`: devuelve una instantánea persistente del catálogo;
  por sí sola no garantiza que el archivo siga intacto.
- `verificar(activo_id) -> ComprobacionRAW`: relee el contenido y registra el
  resultado y la fecha UTC. Una discrepancia física, ausencia o referencia insegura
  marca el activo como inconsistente. Un error técnico o de política no equivale
  a corrupción: lanza `verificacion_no_disponible` y conserva el registro anterior.
- `recuperar(activo_id) -> Path`: exige incorporación completada y comprobación
  física satisfactoria en ese momento. No devuelve operaciones incompletas.
- `diagnosticar() -> DiagnosticoRAW`: comprueba activos incorporados y enumera
  operaciones incompletas/fallidas, inconsistencias, archivos sin referencia a una
  incorporación disponible y temporales. No elimina ni promueve registros.

La ruta de un informe del descargador HTTP podrá entregarse a `incorporar()` si su
directorio fue autorizado. En esta fase no hay automatización de esa integración:
el almacén vuelve a calcular las evidencias y no confía en el hash de un informe.
Se reutiliza `Fuente`; no se fabrica un `Integridad.VERIFICADA` o un estado del
recurso `CONFIRMADO`. Almacenamiento incorporado no significa calidad científica.

## Secuencia y estados persistentes

1. **PREPARADA**: se asigna el UUID y se confirman metadatos públicos en una transacción.
2. Se valida entrada local autorizada, regular y sin symlinks/junctions. Se copia
   por bloques a un temporal exclusivo en `temporales/`, sin escribir en el original.
3. Se comprueban tamaño, identidad y fecha de modificación antes/después de la
   lectura. Se ejecutan flush/fsync y se relee el temporal para contrastar tamaño
   y SHA-256 con los bytes copiados.
4. **VERIFICADA** (`verificada_localmente`): se persisten hash, tamaño y ruta prevista.
   Este estado todavía no habilita la recuperación del archivo.
5. Se publica mediante enlace duro exclusivo. Un destino existente se reutiliza
   únicamente tras comprobar físicamente su tamaño y SHA-256. No se sobrescribe
   ni se repara silenciosamente un contenido corrupto. Se comprueba también el
   archivo publicado y se retira el temporal.
6. **INCORPORADA**: se registra en SQLite después de la publicación y comprobación.
7. Una verificación posterior contradictoria marca **INCONSISTENTE**. Una falla
   de incorporación marca **FALLIDA** cuando SQLite permite registrar la transición.

Cada transición y su evento se confirman en la misma transacción SQLite. El catálogo
se versiona con `user_version=2` para catálogos nuevos (se mantiene lectura/escritura
RAW básica de v1), activa claves foráneas, usa `synchronous=FULL`,
journal DELETE y timeout de bloqueo de cinco segundos. No se adopta una base ajena
con tablas preexistentes sin versión ni una versión de esquema desconocida.

El catálogo conserva fecha UTC de preparación y última comprobación, tamaño real,
SHA-256, ruta relativa controlada, estados, códigos de error, advertencias y eventos.
Los errores almacenados son códigos técnicos, no mensajes de excepciones o rutas
de entrada. Las identidades de proyectos y objetos se mantienen en tablas separadas;
la declaración pública de cada adquisición se conserva como JSON.

## Compatibilidad estructural MD-01, MD-02 y MD-03 (paso 51)

| Modelo | Campos públicos | Persistencia |
| --- | --- | --- |
| MD-01 `ProyectoCientifico` | project_id, schema_version, nombre, contexto, estado | proyectos: id y columnas homónimas de metadatos |
| MD-02 `ObjetoCientifico` | object_id, project_id, family, kind, created_at, state | objetos: id, proyecto_id y columnas homónimas |
| MD-03 `ActivoRAW` | asset_id, object_id, sha256, size_bytes, media_detected, storage_ref | activos: id, objeto_id, sha256, tamano, media_detected, ruta_interna |

Los nombres MD-03 asset_id, object_id, size_bytes y storage_ref son propiedades
de lectura sobre los datos existentes. No crean IDs o valores duplicados; se
conservan los atributos activo_id, declaracion, tamano y ruta_interna anteriores.
media_detected es un campo opcional añadido al final del dataclass, compatible
con constructores posicionales anteriores. No hay detector de formato implementado:
permanece None en las incorporaciones nuevas y en las migradas, aunque la extensión
sea .csv o exista un tipo_medio_declarado. No se copia un dato declarado a comprobado.

Proyecto y objeto solo requieren sus identidades (y la relación objeto-proyecto).
Los metadatos desconocidos son None/NULL. schema_version es una etiqueta textual
opcional del esquema del proyecto, declarada por el llamador: no se rellena a partir
de user_version de SQLite ni se asume una versión por defecto.

estado del proyecto y state del objeto son textos opcionales declarados; no usan
EstadoIncorporacion ni cambian al adquirir/verificar archivos. No se inventan
vocabularios de estado, familias ni tipos científicos. created_at es la fecha
explícita de creación de la entidad lógica, con zona horaria y persistida en UTC.
No se rellena con fecha de incorporación, fecha de migración ni fecha de observación
científica. En registros anteriores sigue siendo desconocida.

`AlmacenRAW.registrar_proyecto()` y `registrar_objeto()` permiten registrar los modelos;
`consultar_proyecto()` y `consultar_objeto()` recuperarlos. Se aplican los filtros de
metadatos públicos existentes. Un objeto explícito necesita un proyecto registrado.
Las incorporaciones antiguas siguen creando automáticamente solo identidades y
relaciones desconocidas, sin inventar el resto de campos.

El registro es idempotente: permite completar campos NULL explícitamente, pero no
sobrescribe metadatos conocidos contradictorios ni reasigna un objeto a otro proyecto.
Registrar otra vez la misma identidad se refiere a la misma entidad; no se crea
otra con ese ID. No hay API de borrado o reutilización ni edición del ciclo de vida.
Una futura política para cambiar estados/metadatos requerirá diseño separado.
Los IDs no contienen la ruta y se mantienen al trasladar una copia cerrada del
almacén. Su asignación única entre instalaciones independientes sigue correspondiendo
al llamador; no se implementa sincronización de catálogos.

### Evolución del catálogo: v1 a v2

La evolución es aditiva: cuatro columnas TEXT opcionales en proyectos
(schema_version, nombre, contexto, estado), cuatro en objetos (family, kind,
created_at, state) y una en activos (media_detected). No se borran/reconstruyen
tablas ni se cambian registros existentes, JSON de declaraciones, hashes, rutas,
relaciones, IDs o eventos. Los nuevos valores de filas anteriores son NULL.

Abrir un catálogo v1 **no ejecuta una migración automática**. Continúan funcionando
las incorporaciones RAW, comprobaciones, recuperación y consultas de identidades.
Intentar registrar metadatos nuevos en v1 genera migracion_explicita_requerida.
Un catálogo nuevo vacío se crea directamente con la capacidad v2 mediante la
inicialización y evolución del esquema vacío, sin migrar datos previos.

Se prepara la función pública `migrar_a_v2(conexion_sqlite)`, que exige autorización
explícita del llamador. No abre rutas ni busca catálogos por su cuenta. Rechaza una
transacción activa para no confirmar cambios ajenos. Ejecuta BEGIN IMMEDIATE,
comprueba claves externas, añade columnas y cambia user_version en la misma
transacción. Un fallo revierte DDL y versión. Repetir sobre v2 no altera filas ni
esquema. Versiones no admitidas o relaciones rotas se rechazan sin modificarlas.

Solo se ejecutó esta función sobre bases temporales sintéticas en las pruebas.
No se migró ningún almacén operativo. Antes de una migración real se requiere
aprobar el procedimiento, detener otros escritores y preparar un respaldo verificable.
No se añadió una CLI, búsqueda automática, mecanismo de reparación ni downgrade.

El dictamen de esta fase se limita a compatibilidad **estructural** con los campos
indicados. INCORPORADA sigue significando comprobación técnica local y persistencia
según las garantías existentes; no confirma autenticidad institucional ni calidad
científica, ni añade integración HTTP→RAW.

## Consistencia, interrupciones y recuperación

SQLite y el sistema de archivos no forman una sola transacción. Si se publica y
después falla SQLite, puede quedar un contenido sin una incorporación disponible.
Si también falla el registro del error, la última preparación/verificación ya
persistida permite detectar la operación pendiente después de reabrir el catálogo.
Nunca se interpreta `VERIFICADA` como incorporación completada.

Ante errores o KeyboardInterrupt/SystemExit se cierra el archivo y se intenta retirar
solo el temporal propio. Si falla la retirada, su prefijo contiene el UUID y el
diagnóstico lo enumera. No se elimina contenido ya publicado: podría pertenecer a
otro activo. Las interrupciones se propagan; las excepciones técnicas normales
se envuelven en `ErrorAlmacenamientoRAW(codigo, activo_id)`.

`diagnosticar()` implementa detección, no reparación: no confirma automáticamente
activos pendientes, no borra huérfanos y no retira cuarentenas. Aunque se restaure
manualmente un archivo inconsistente y vuelva a coincidir su hash, el activo
permanece inconsistente hasta una futura política de recuperación aprobada.

## Protección de rutas y metadatos sensibles

Se rechazan `..`, entradas externas a las raíces autorizadas, archivos internos
del propio almacén como entrada, recursos no regulares, symlinks y junctions.
Las rutas de contenido se derivan de un SHA-256 hexadecimal validado; la ruta
guardada en SQLite debe coincidir exactamente. El nombre del archivo de entrada
no controla el destino ni se persiste como identificador.

Los parámetros se guardan solo si el llamador autoriza sus claves mediante una
lista pública exacta. Se omiten claves sensibles reconocidas, valores con patrones
de credenciales y valores URL, con advertencia sin registrar su texto. La lista
predeterminada vacía no conserva parámetros. La procedencia HTTP(S) pierde usuario,
contraseña, consulta y fragmento; queda advertencia de esa reducción. Una referencia
opaca pública se conserva si no presenta patrones sensibles. Identificadores con
credenciales o URLs con consulta/usuario se rechazan en vez de alterarse.

Se reconocen también autoridades sin esquema (`//usuario:clave@host/recurso`) y
se rechazan, incluso sin credenciales: no se supone un esquema ni se consideran
identificadores opacos seguros. Se rechazan barras invertidas, controles, formas
HTTP(S) sin autoridad válida, puertos inválidos y referencias con `@` ambiguas.
La inspección de escapes porcentuales es conservadora y acotada a tres pasadas;
no se usan las formas decodificadas para reescribir identificadores científicos.
DOI, URN y códigos opacos admitidos se conservan exactamente, incluidos sus espacios.
Las URLs completas HTTP(S) declaradas por el llamador se sanean sin visitarlas:
se retiran usuario, contraseña, consulta y fragmento y se emite advertencia genérica.
Esto no constituye autorización de acceso remoto ni prueba de autenticidad.
Errores de análisis y advertencias no reproducen la referencia ni los secretos.

Estas medidas **no son un detector universal de secretos**. Un token opaco en una
ruta URL o un valor aparentemente público no puede identificarse automáticamente.
El llamador debe aprobar los metadatos como públicos antes de entregarlos, incluidas
las rutas de procedencia. No se guardan cabeceras HTTP ni cadenas de excepción.
Las causas encadenadas de una excepción pueden revelar detalles: no registrar trazas
completas indiscriminadamente. SQLite no está cifrado y requiere permisos de acceso.

## Separación entre incorporación, verificación y disponibilidad

Reducir `max_bytes` al reabrir el almacén solo restringe nuevas entradas. La
verificación lee por bloques y contrasta el tamaño/hash con los valores persistidos,
sin usar ese límite de incorporación. El tamaño catalogado acota la lectura y
permite rechazar crecimiento inesperado sin acumular el archivo en memoria.

Un archivo ausente, tamaño/hash contradictorios, tipo no regular, enlace no autorizado
o referencia de catálogo inconsistente justifican `INCONSISTENTE`. Permisos denegados,
errores de lectura, falta de memoria o errores de política sin evidencia física
producen `ErrorAlmacenamientoRAW('verificacion_no_disponible', activo_id)` y no
actualizan estado, fecha de última comprobación ni eventos del activo. Tampoco
permiten recuperar el archivo: el error se propaga. Una incorporación histórica
conservada en metadatos no implica una comprobación actual satisfactoria.

No se añadieron estados, campos ni migraciones. El cambio de comportamiento es
explícito: los llamadores deben distinguir una comprobación negativa por inconsistencia
de una excepción por imposibilidad de comprobar. `diagnosticar()` también puede
propagar esa imposibilidad y no debe interpretarse como un diagnóstico completo.
No se repara ni se vuelve a habilitar automáticamente un activo inconsistente.

## Garantías y límites técnicos

Comprobado con pruebas: copia exacta, hash por lectura real, detección de corrupción
posterior (incluso con igual tamaño), deduplicación sin pérdida de identidades,
conservación del original, fallos de lectura/escritura/SQLite, interrupciones,
estados incompletos detectables, consulta persistente y comprobación al recuperar.

La relectura puede servirse de la caché del sistema operativo: no certifica el medio
físico ni garantiza conservación futura. Se detectan cambios observables durante
la lectura, pero no se obtiene una instantánea bloqueada frente a escritores
adversarios que restauren metadatos. `ctime` no se usa como comparación portable
entre ruta y descriptor por diferencias observadas en Windows.

Los enlaces duros requieren soporte del volumen; si no existe, se falla sin una
copia alternativa insegura. La publicación del nombre no sobrescribe y aparece con
contenido completo en sistemas compatibles. No se sincronizan directorios ni se
ha probado resistencia a cortes eléctricos. Un cierre forzado puede dejar temporales
o contenidos sin un resultado retornado. El catálogo no es inmutable ni está firmado.

Uso previsto: operaciones secuenciales y directorios privados en un volumen local.
SQLite serializa sus escrituras, pero no hay bloqueo coordinado de toda la operación
ni garantía probada entre varios procesos. Las comprobaciones de rutas no eliminan
carreras si un tercero puede sustituir carpetas. Deduplicar comparte un archivo:
una modificación externa afecta a todos los activos que lo referencian y se detecta
al verificar/diagnosticar, no de forma continua. Recuperar devuelve una ruta, no un
descriptor que impida modificaciones posteriores a la comprobación.

## Decisiones abiertas

- Revisar vocabularios de family/kind/estados y el alcance global de IDs al disponer
  de especificaciones adicionales de MD-01/02/03.
- Política de recuperación, cuarentena, huérfanos, respaldo/migración y retención.
- Permisos de solo lectura/inmutabilidad, concurrencia, volúmenes de red y durabilidad.
- Evidencia externa de procedencia/autenticidad, formatos comprobados y validación
  científica, sin confundirlas con SHA-256 local.
- Integración automática HTTP, edición del ciclo de vida de proyectos/objetos y consulta avanzada.

## Verificación

Las pruebas usan exclusivamente bytes sintéticos pequeños, SQLite real y directorios
efímeros dentro del proyecto que se retiran al finalizar. No generan grandes archivos
ni conexiones externas. Las pruebas de symlinks/junctions simulan la detección para
no exigir privilegios especiales de Windows; las carreras hostiles y cortes eléctricos
no están comprobados.

```powershell
& .\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
& .\.venv\Scripts\python.exe -B -m pip check
```
