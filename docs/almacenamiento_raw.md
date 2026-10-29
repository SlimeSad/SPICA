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

La capa operativa `ConfiguracionRAW` propone `Path.home() / "SPICA_DATOS" / "raw"`,
independiente del nombre del usuario Windows. El staging es un directorio hermano,
`raw-staging`; contiene descargas efímeras, no otro catálogo. RAW contiene
`catalogo.sqlite3`, `temporales/` y `sha256/`, además del marcador operativo.
Crear una configuración o importar el paquete no crea esos directorios.

La ubicación operativa debe ser externa al código, dedicada y privada. Se rechazan
el repositorio y sus ancestros, otros checkouts/worktrees, componentes internos
`.git`, `.venv`, `.codex`, `.agents`, rutas relativas, `..`, symlinks y junctions.
Los permisos efectivos deben revisarse antes del uso real; en Windows los directorios
operativos heredan ACL y no se declara privacidad auditada automáticamente.

`.gitignore` conserva la protección histórica `/datos/raw/`, pero esta regla no
autoriza una ubicación interna para `ConfiguracionRAW`. Tampoco protege frente a
adiciones forzadas o archivos ya versionados. El constructor de bajo nivel
`AlmacenRAW` sigue recibiendo directorios ya existentes y autorizados explícitamente.
No se ha inicializado el almacén operativo permanente.

## Configuración e inicialización explícita (PASO 62-D)

```python
from pathlib import Path
from spica.adquisicion.almacenamiento import ConfiguracionRAW
from spica.adquisicion.almacenamiento.inspeccion import PoliticaInspeccionRAW

config = ConfiguracionRAW()  # Solo configura; no escribe ni abre el almacén.
personalizada = ConfiguracionRAW(
    Path.home() / "SPICA_DATOS" / "laboratorio" / "raw",
    inspeccion=PoliticaInspeccionRAW(max_bytes_temporales=256 * 1024**2),
)
```

`validar()` inspecciona rutas, marcador, estructura SQLite, permisos básicos y
espacio. No crea el almacén ni hace sondas de escritura en él; una inspección WAL
puede crear una copia temporal privada fuera de los originales. `abrir()` exige
un almacén reconocido, comprueba publicación exclusiva mediante sondas pequeñas
y devuelve `AlmacenOperativoRAW`. `inicializar()` es la acción explícita que crea
una raíz inexistente. Un directorio existente sin marcador válido, aunque esté
vacío, no se adopta. Un staging ajeno tampoco se reutiliza.

`ValidacionUbicacionRAW.estado` distingue `no_inicializado` e `inicializado`.
Una incertidumbre, estructura incompatible o inicialización interrumpida produce
una excepción cuyo `estado` es `revision_necesaria`; nunca un resultado operativo.
`abrir()` sobre una raíz ausente genera `almacen_raw_no_inicializado` con estado
`no_inicializado`. Permisos y espacio observados no son reservas ni bloqueos.

El protocolo para una raíz nueva es:

1. Crear exclusivamente los directorios y `.spica-raw.inicializando`. Escribir,
   hacer flush/fsync de esa intención y sincronizar el directorio donde se admite.
2. Comprobar escritura de staging, publicación exclusiva y limpieza de sondas;
   crear el catálogo nuevo. No se migran catálogos existentes.
3. Escribir el JSON en `.spica-marcador-<uuid>.tmp`, hacer flush/fsync, cerrar y
   releer su contenido completo de forma acotada. Una escritura corta no se publica.
4. Publicar `spica-raw.json` mediante enlace duro exclusivo al archivo completo;
   nunca reemplazar un marcador que haya aparecido. Sincronizar el directorio
   cuando la plataforma lo permite. Retirar el nombre temporal propio.
5. Retirar la intención como última operación necesaria para habilitar el almacén.
   No hay más escrituras requeridas después de ese punto.

Mientras exista la intención, `validar()` y `abrir()` rechazan el almacén con
`inicializacion_raw_requiere_revision`, incluso si ya existe un JSON final válido.
Un fallo antes de publicar conserva una inicialización pendiente; un fallo tras
publicar conserva el marcador y el catálogo para revisión. No se eliminan originales,
catálogos ni marcadores finales como compensación. No hay recuperación automática:
detener el uso y revisar estructura, catálogo y archivos antes de autorizar un
procedimiento separado. No retirar la intención a ciegas.

Si el sistema retira efectivamente la intención pero devuelve un error, se exige
un nuevo reconocimiento completo antes de devolver éxito, con la advertencia
`retiro_intencion_confirmado_tras_error`. Si no puede comprobarse, se propaga el
error. Inicializar de nuevo un almacén reconocido lo abre con `nuevo=False`.
Los marcadores válidos del PASO 62 conservan el mismo formato JSON v1 y se admiten
si no existe una intención pendiente; esto no acredita durabilidad histórica.

En POSIX se usa fsync del directorio antes de crear el catálogo y después de
publicar el marcador. En Windows no hay fsync portable del directorio en esta
implementación: el resultado nuevo advierte `sincronizacion_directorio_no_disponible`.
No se fuerza una alternativa insegura ni se promete resistencia a apagados. No se
exige sincronizar la retirada final de la intención: si reaparece tras un corte,
el reconocimiento exige revisión. La ausencia o corrupción del marcador también
impide reconocer el almacén. No hay una transacción global SQLite–archivos.

Cada limpieza de sonda es independiente. Solo se intentan retirar nombres propios
registrados al crearlos y bajo directorios controlados. Los fallos se devuelven
como pares técnicos `fallos_limpieza`, por ejemplo
`("sonda_publicada", "eliminacion_no_disponible")`, sin rutas ni texto del sistema.
Un error principal conserva su código; si únicamente falla la limpieza se devuelve
`limpieza_sondas_incompleta` o `limpieza_marcador_incompleta`. No se declara limpieza
completa con residuos. Las sondas `.sonda-*` no son archivos RAW catalogados.

Las fronteras `validar`, `abrir`, `inicializar` e `inspeccionar_catalogo` publican
excepciones nuevas compatibles con `ErrorAlmacenamientoRAW`, con código, fase,
estado y limpieza estructurada. No conservan args, causas, contextos, notas ni
documentos JSON del backend. `diagnostico_publico()` selecciona esos campos para
logging; también se comprueban las trazas estándar y `exc_info=True`. Esto no borra
secretos de memoria ni autoriza registrar frames, variables locales o componentes
privados. Las excepciones del motor RAW de bajo nivel mantienen sus límites previos.

## Presupuesto de inspección SQLite/WAL

Sin WAL no vacío se inspecciona mediante `mode=ro&immutable=1`, sin snapshot ni
auxiliares nuevos. Con WAL se copian exclusivamente DB y WAL por bloques a
`TemporaryDirectory`; SQLite crea allí su SHM, sin usar ni modificar el original.
Los journals de rollback exigen revisión, sin recuperación automática.

`PoliticaInspeccionRAW` configura:

- `max_bytes_temporales`: 512 MiB por defecto, para copia más margen previsto.
- `margen_bytes`: 16 MiB por defecto; mínimo 64 KiB para SHM y trabajo adicional.
- `tamano_bloque`: hasta 1 MiB, configurable y comprobado durante la copia.
- `directorio_temporal`: padre absoluto ya existente y sin enlaces; por defecto
  se usa el temporal del sistema. La configuración operativa rechaza un padre
  personalizado dentro del código o de componentes internos.

El preflight requiere `DB + WAL + margen_bytes + ceil((DB + WAL) / 20)` bytes tanto
en el presupuesto como en el espacio libre del volumen temporal. Se comprueba
el padre real y el directorio temporal creado antes de copiar. Se vuelve a aplicar
el presupuesto al contar bytes copiados. Los archivos se acotan al tamaño observado
al inicio de cada copia; se detectan cambios ordinarios de identidad/tamaño/mtime.
El margen es una estimación conservadora, no una cuota dura del sistema operativo
ni una reserva de espacio. No se limita CPU/tiempo de SQLite. Se exige ausencia
de otros escritores y un volumen local con permisos adecuados.

Una copia, validación o limpieza fallida impide un resultado satisfactorio. Se
conserva el error principal y se adjunta el rol `snapshot_sqlite` si queda pendiente
su eliminación. La política se propaga desde `ConfiguracionRAW.inspeccion` hasta
la apertura del motor y su catálogo; no se sustituye por el presupuesto por defecto
en la segunda inspección. Las bases originales rechazadas permanecen intactas.

Se comprobó `TemporaryDirectory` real: el sandbox de Codex rechazó acceso y limpieza
de su directorio privado. Se retiró únicamente ese temporal de prueba mediante
una ejecución autorizada fuera del sandbox. Otra prueba fuera del sandbox, con
SQLite/WAL sintético, ejecutó la inspección real sin reemplazar TemporaryDirectory:
aceptó v2, conservó DB/WAL/SHM y eliminó todos los temporales. Esto comprueba acceso
y limpieza bajo ese usuario, no una auditoría de ACL frente a otros usuarios.
Las pruebas unitarias de WAL usan contenedores sintéticos con permisos heredados;
producción conserva el temporal privado y rechaza la operación si no puede usarlo.

## Preparación de una inicialización real posterior

Después de revisar estos cambios, aprobar por separado la ruta y la inicialización.
Comprobar ACL, exclusión del código, volumen local, espacio de staging/RAW y volumen
temporal, soporte de enlaces duros y ausencia de otros procesos. Ejecutar primero
`validar()`; solo con autorización explícita llamar a `inicializar()`, revisar sus
advertencias y cerrar el resultado. Reabrir y comprobar con un archivo sintético
en una prueba separada y autorizada antes de adquirir datos ambientales.
Ante cualquier error conservar el diagnóstico y los residuos para revisión.

Persistencia local no equivale a respaldo. Este módulo no crea copias de seguridad,
no protege frente a pérdida del volumen y no proporciona recuperación automática.
Respaldo, retención y recuperación requieren su propio procedimiento aprobado.

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
  Admite además `tamano_esperado` y `sha256_esperado` opcionales (ambos juntos),
  contrastados con la copia físicamente releída antes de publicarla. Una discrepancia
  deja FALLIDA la incorporación, no un activo disponible. Las llamadas previas no cambian.
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

La ruta de un informe del descargador HTTP puede entregarse a `incorporar()` si su
directorio fue autorizado. El [adaptador experimental del paso 53](integracion_http_raw.md)
automatiza esa coordinación: el almacén vuelve a calcular las evidencias y exige
que la copia física coincida con tamaño y SHA-256 del informe anterior.
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
journal DELETE para bases nuevas y timeout de bloqueo de cinco segundos. Las bases
existentes se reconocen en solo lectura antes de abrirlas para operar; conservan
su modo de diario, incluido WAL. No se adoptan archivos vacíos preexistentes,
bases ajenas ni esquemas incompletos. Véase el procedimiento y las limitaciones
de reconocimiento histórico en [PASO 62-B](correcciones_auditoria_altas.md).

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
científica. La coordinación HTTP→RAW del paso 53 se documenta por separado.

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
predeterminada vacía de `AlmacenRAW` no conserva parámetros; `ConfiguracionRAW`
autoriza por defecto únicamente `producto_id`. La procedencia HTTP(S) pierde usuario,
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

No se añadieron estados, campos ni migraciones a los contratos científicos. El cambio de comportamiento es
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
contenido completo en sistemas compatibles. La incorporación de contenidos RAW
no sincroniza directorios; la sincronización limitada del marcador de configuración
se describe arriba. No se ha probado resistencia a cortes eléctricos. Un cierre forzado puede dejar temporales
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
- Endurecimiento de la integración experimental HTTP, edición del ciclo de vida y consulta avanzada.

## Verificación

Las pruebas usan bytes sintéticos, SQLite real y directorios efímeros que se retiran
al finalizar. Las pruebas de configuración e inspección se aíslan fuera del checkout;
otras pruebas históricas usan temporales dentro del proyecto. No hay conexiones
externas. Hay pruebas de detección de enlaces simulada y sondas adicionales de
symlinks/junctions reales en Windows. Las carreras hostiles y cortes eléctricos
no están comprobados. Las pruebas previas del PASO 62 y SUADC-01/02 se conservan.

```powershell
& .\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
& .\.venv\Scripts\python.exe -B -m pip check
```

Verificación del PASO 62-D con Python 3.15.1, HTTPX 0.28.1 y SQLite 3.53.4:
439 pruebas aprobadas (402 anteriores + 37 nuevas), 0 fallidas y 0 con errores;
suite completa en 41.285 s. `pip check`: `No broken requirements found.`;
`git diff --check`: código 0, con avisos de conversión LF/CRLF. Las seis regresiones
básicas se ejecutaron antes de corregir el código y fallaron de la forma esperada.
Los archivos de las 30 pruebas del PASO 62 y de las 39 regresiones SUADC-01/02
permanecen intactos. No se inicializó almacenamiento permanente ni hubo descargas,
conexiones externas, migraciones operativas, commits o push.
