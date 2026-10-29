# PASO 62-B: SUADC-01 y SUADC-02

Esta corrección preserva el trabajo pendiente de configuración operativa del PASO
62. No inicializa la ubicación operativa, no cambia modelos científicos ni añade
versiones, columnas, tablas o identidades persistentes. No implementa los hallazgos
medios ni la corrección pendiente del puerto 0.

## SUADC-01: frontera pública de errores HTTP

Las primeras regresiones reprodujeron errores de conexión/lectura/TLS con mensajes,
notas y causas sintéticas sensibles. Limpiar `str(error)` no limpiaba el traceback.

`ClienteHTTP.get()` y `descargar()` dejan que las capas internas clasifiquen errores,
apliquen reintentos y limpien temporales. En su frontera pública construyen un error
nuevo y copian solo los campos técnicos previstos: tipo, código HTTP, condición
recuperable, espera calculada, intentos, agotamiento e historial. La descarga conserva
su clase `ErrorDescargaArchivo` y su informe técnico, sin incluir la request HTTPX.
Los mensajes son canónicos y no copian texto libre del backend.

`fase` distingue las operaciones `get` y `descargar`; no pretende identificar el
paso interno exacto de un backend. `diagnostico_publico()` devuelve una selección
de campos serializables para logging. No incluye URL, parámetros, cabeceras,
credenciales, cuerpos ni notas de excepciones originales.

No basta `raise ... from None`: Python conserva `__context__` incluso cuando lo
oculta al imprimir. La publicación captura su excepción nueva, elimina el contexto
que Python haya añadido y la relanza sin causas. Esto también cubre un contexto
previo del llamador. La traducción de `httpx.InvalidURL` a ValueError aplica el
mismo criterio, manteniendo la clase pública de configuración.

Las pruebas inspeccionan `str`, atributos, `__cause__`, `__context__`, notas,
`traceback.format_exception` y logging con `exc_info=True`. Comprueban además TLS sin
reintento, agotamiento con historial, descarga interrumpida y limpieza.

### Garantía y límites

La garantía corresponde a las excepciones públicas generadas por estas operaciones
y al diagnóstico explícito; no es una promesa de borrado de memoria. HTTPX, el
intérprete, las conexiones, los callbacks del llamador y los frames pueden conservar
datos internos. Depuradores, volcados y herramientas que capturen variables locales
pueden exponer secretos. Tampoco puede sanearse código fuente del llamador que
contenga credenciales literales y sea mostrado por un formateador de trazas.
Las interfaces privadas del transporte siguen siendo internas. No registrar
indiscriminadamente requests/responses, cookies o todo el estado del cliente.

## SUADC-02: reconocimiento SQLite antes de modificar

`almacenamiento.inspeccion.inspeccionar_catalogo(ruta)` no crea una base ausente.
Reconoce versiones 1/2 mediante:

- `application_id` histórico 0 y `user_version` admitido; ninguno basta por sí solo.
- Tablas RAW completas, nombres/tipos de columnas, nulabilidad y claves primarias.
- Relaciones foráneas y restricciones DDL conocidas, incluidos estados y tamaño.
- Columnas MD-01/MD-02/MD-03 obligatorias de v2.
- `foreign_key_check` sobre datos y `quick_check(1)`.

Se rechazan tablas, vistas, triggers y restricciones desconocidas. Se admiten
índices adicionales no únicos sobre las tablas reconocidas. Solo se excluye el
prefijo interno literal `sqlite_`; un nombre parecido como `sqliteXajeno` no
queda oculto por comodines de `LIKE`. El reconocimiento del DDL normaliza
espacios/keywords, pero conserva los literales: no considera
equivalentes estados con distinto contenido. DDL desconocido, aunque pudiera ser
semánticamente equivalente, necesita revisión explícita; no se intenta repararlo.

La declaración histórica v1 se comparte con la creación de bases nuevas; la
referencia v2 se deriva en memoria usando la migración ya existente. Las regresiones
utilizan una fixture SQL independiente y definen manualmente sus columnas v2.

### Bases nuevas, compatibles y ambiguas

`CatalogoRAW` crea un archivo inexistente de forma exclusiva y lo abre con
`mode=rw`. SQLite no puede crear otra base si la ruta desaparece entre ambas
operaciones. Un archivo vacío ya existente no se interpreta como autorización para
inicializarlo. WAL/SHM/journal huérfanos requieren revisión. Un fallo de creación
puede dejar una inicialización incompleta propia: no se elimina ni adopta de nuevo
automáticamente.

Se conserva la compatibilidad con el esquema histórico v1 completo, sin migrarlo.
Para mantener también las interfaces previas del PASO 62 se admite el caso v1 con
el conjunto completo de columnas aditivas v2: se reconoce exactamente esa estructura
conocida, pero continúa siendo v1 y sus operaciones MD siguen requiriendo migración
explícita. Una v2 parcial se rechaza. No se admiten combinaciones arbitrarias de
columnas ni se cambia `user_version` al abrir.

Los catálogos antiguos no poseen una marca criptográfica de procedencia. La
coincidencia exacta del esquema acredita compatibilidad estructural, no quién creó
la base ni la autenticidad de sus registros. Versión aislada, objetos adicionales,
restricciones distintas o estructuras parciales son insuficientes y se rechazan.
Su reconocimiento/importación futura necesita aprobación explícita, fuera de esta
corrección; no hay una opción de omitir la validación.

La configuración operativa usa esta misma inspección y conserva su marcador de
almacén. RAW valida el catálogo antes de crear sus subdirectorios. Solo después
del reconocimiento abre para operar, activa claves foráneas y synchronous FULL.
DELETE se establece exclusivamente en bases nuevas. El modo de diario de una
base existente válida no se cambia, incluido WAL.

### Inspección de WAL sin tocar auxiliares originales

Sin WAL activo se usa `mode=ro&immutable=1`, evitando recuperación o creación de
archivos auxiliares. Si existe un WAL no vacío, se copian la base y su WAL por
bloques a un temporal privado. Allí SQLite puede interpretar los commits y crear
su propio SHM; el SHM original no se utiliza ni se modifica. La copia está acotada
al tamaño observado al inicio, para no seguir indefinidamente un WAL creciente.
El temporal se cierra y elimina al terminar. No se copian archivos científicos RAW.

Se requiere una inspección sin escritores activos. Tamaño, identidad y mtime de
DB/WAL se contrastan para detectar cambios ordinarios; esto no sustituye un protocolo
de exclusión entre procesos ni protege contra un proceso hostil que controle las
rutas. Un journal de rollback requiere revisión previa, sin recuperación automática.
Falta de acceso, espacio temporal o imposibilidad de comprobar provoca rechazo,
sin forzar otro modo de diario ni debilitar permisos.

La inspección puede consumir E/S, espacio temporal proporcional a DB+WAL y tiempo
de comprobación. No es un respaldo ni verificación de los originales científicos.
Lecturas pueden actualizar tiempos de acceso del sistema de archivos: la garantía
de no escritura se refiere al contenido SQLite, configuración persistente y archivos
auxiliares originales, no a metadatos de acceso que gestione el sistema operativo.

## Regresiones y entorno

Las pruebas usan únicamente SQLite temporal, MockTransport y marcadores sintéticos.
Comprueban igualdad de bytes y conjuntos de archivos de bases rechazadas, incluidos
WAL/SHM; también reconocimiento de v1/v2, operaciones legítimas y rechazo de v2
incompleto. No se migran ni inspeccionan bases operativas reales.

En el entorno restringido de Codex para Windows, las pruebas WAL inyectan un
contenedor temporal de fixtures con ACL heredada: el sandbox no puede reabrir el
directorio privado creado por `TemporaryDirectory`. DB, WAL, SHM y la validación
SQLite son reales. La implementación de producción mantiene el temporal privado;
no se relajan permisos del sistema para superar esa restricción.

Se conservan las 30 pruebas previas del PASO 62 sin modificar su archivo. Los
hallazgos SUADC-03 a SUADC-09 permanecen pendientes de su propia revisión.

## Verificación del 29 de octubre de 2026

Intérprete exclusivo: `.venv/Scripts/python.exe`, Python 3.15.1; HTTPX 0.28.1
y SQLite 3.53.4. Las regresiones se incorporaron antes de las correcciones y
reprodujeron la exposición de marcadores sintéticos y la aceptación de bases
ajenas/incompletas. Durante la revisión también se reprodujo y corrigió la
omisión de tablas/triggers `sqliteX...` por el comodín `_` de `LIKE`.

Resultados finales, sin fallos ni errores:

- SUADC-01: 9 pruebas aprobadas.
- SUADC-02: 30 pruebas aprobadas.
- Configuración previa del PASO 62: sus 30 pruebas aprobadas, archivo intacto.
- Suite completa: 402 pruebas aprobadas en 31.374 segundos (363 previas + 39 nuevas).
- `python -B -m pip check`: `No broken requirements found.`
- `git diff --check`: código 0; solo avisos de conversión LF/CRLF de Git.

Comando de suite: `.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v`.
No se realizaron conexiones externas, cambios en datos operativos, inicialización
RAW permanente, commits ni push. Los resultados no constituyen validación científica.
