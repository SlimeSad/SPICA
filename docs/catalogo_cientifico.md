# Paso 55: catálogo dinámico de descubrimiento científico

El paquete `spica.adquisicion.catalogo` registra metadatos de descubrimiento y sus
revisiones. No consulta internet, no descarga, no valida observaciones científicas
ni planifica adquisiciones. Es dinámico porque admite registros y revisiones
controladas, no porque se actualice automáticamente desde instituciones.

## Separación de arquitectura y almacenamiento

`CatalogoCientifico(ruta_sqlite)` requiere una ruta explícita en un directorio
existente y controlado. No crea un catálogo operativo en el repositorio. La ubicación
preferente es externa, por ejemplo `C:\Users\Propietario\SPICA_DATOS\catalogo\descubrimiento.sqlite3`;
este ejemplo es local, no un servicio o endpoint. El operador prepara permisos y
respaldo. Usar con `with` o llamar `close()`.

La base es independiente de `catalogo.sqlite3` de RAW. Tiene `application_id=0x53554341`
y `user_version=1`, propios del catálogo de descubrimiento; no son versiones MD-01
ni el esquema RAW v1/v2. Rechaza una base RAW o ajena antes de crear tablas/adoptarla.
No migra ni modifica el almacenamiento RAW, los contratos de adquisición o HTTP→RAW.

Se reutiliza `Fuente` del núcleo como espacio de identidad y el filtro conservador
de rutas/metadatos públicos existente. No se duplica el transporte ni se inventan
esquemas de proyecto/objeto/activo. El PASO 65 incorpora instantáneas documentales
en cada adquisición RAW, conservando los IDs públicos originales y sus revisiones,
sin confundir un producto catalogado con un asset_id adquirido. No hay claves
externas ni transacción global entre archivos SQLite diferentes.
Las reglas y limitaciones están en [Registro y evidencias](registro_evidencias.md).

## Entidades e identidad

| Entidad tipada | Identidad y metadatos |
| --- | --- |
| FuenteCatalogo | Fuente(proveedor, identificador), nombre declarado/oficial, tipo de organización, referencia oficial conocida, revisión y estado de verificación |
| ProductoCatalogo | ID original dentro de Fuente, nombre/descripción, familia, formatos declarados, versión, acceso, licencia, autenticación requerida y descripción sin secretos; uso de estaciones opcional |
| EstacionCatalogo | ID original dentro de Fuente/producto; red declarada, nombre, tipo, x/y, altitud, CRS y estado operativo conocidos |
| VariableCatalogo | ID interno independiente global, Fuente/producto, código/nombre originales opcionales, descripción, unidad/frecuencia/tipo declarados y versión/procedencia del diccionario |
| DisponibilidadCatalogo | ID de registro dentro de Fuente/producto, estación/variable opcionales, intervalo, precisión/zona/frecuencia, cobertura parcial opcional, estado y comprobación |
| CapacidadCatalogo | ID dentro de Fuente/producto, mecanismo, estado, comprobación y descripción de mecanismos adicionales |
| RecursoCatalogo (PASO 65) | Fuente/producto/ID original, localizador, publicación, título, formato y licencia declarados; revisiones en el diario existente, sin representar disponibilidad |

Los IDs se conservan sin recortar espacios, cambiar mayúsculas o mapear códigos.
Un ID de estación/producto repetido entre fuentes no colisiona. Estaciones se
identifican por su asociación al producto; no se afirma que registros iguales en
varios productos correspondan a un único punto físico. El mismo código original de
variable puede repetirse entre fuentes/productos. En un producto se rechaza un
segundo ID interno con el mismo código conocido, evitando fusiones silenciosas.
Cuando el código se desconoce puede haber varias variables con IDs internos distintos.

Los campos ausentes quedan en None o en una colección vacía de metadatos. Una
colección vacía no afirma inexistencia de datos. Las coordenadas requieren x/y
juntos y valores finitos, pero no se asume latitud/longitud, CRS, unidad de altitud
ni se realiza conversión espacial. Formatos y unidades son declarados, no detectados.

No hay una relación universal estación-variable: cada registro de disponibilidad
declara su alcance concreto. La presencia de una variable en el diccionario no
demuestra presencia en todas las estaciones. Una ficha actual de estación tampoco
describe automáticamente su instrumentación durante toda la historia. Las revisiones
conservan fichas anteriores; no se reconstruye aún una historia de instrumentos.

## Procedencia y estados

Toda entidad requiere `ProcedenciaCatalogo(referencia, revisada_utc, metodo,
evidencia=None)`. Referencia y método son explícitos; la revisión tiene zona conocida
y se normaliza a UTC. El sistema registra separadamente la fecha UTC informática
de persistencia de cada revisión. Ninguna es una fecha de observación, publicación
o descarga. Las fechas de publicación/descarga no se inventan en este catálogo.

`EstadoVerificacion` distingue DESCONOCIDO, DECLARADO y VERIFICADO. Fuente,
disponibilidad y capacidad usan estos estados. VERIFICADO exige fecha de comprobación
y evidencia en la procedencia; el método también es obligatorio. Esto valida la
coherencia del registro de evidencia proporcionado por el llamador: el catálogo no
realiza la verificación remota ni certifica la autenticidad de esa evidencia.

Los mecanismos son API_REST, HTTP_DIRECTO, PORTAL_ASISTIDO, GEOESPACIAL, MANUAL,
INSTITUCIONAL y OTRO con descripción obligatoria. Pueden registrarse como pendientes
o declarados sin convertirlos en mecanismos comprobados ni ejecutarlos.

Solo se aceptan metadatos públicos. Se reutiliza el filtro existente para rechazar
credenciales, consultas URL, autoridades ambiguas y patrones sensibles en cualquier
texto, incluidos requisitos de autenticación, referencias, evidencia y motivos de
revisión. No se almacenan claves, cabeceras o contraseñas. Los errores no reproducen
los valores rechazados. El filtro es conservador y no detecta universalmente tokens
opacos: el llamador debe revisar lo declarado como público; SQLite no está cifrado.

## Persistencia y revisión controlada

Las tablas son fuentes, productos, estaciones, variables, disponibilidades,
capacidades y revisiones. Las claves externas compuestas impiden vincular una estación
o variable de otra fuente/producto a una disponibilidad. Los IDs/vínculos se guardan
en columnas relacionales y el resto de la entidad tipada en JSON. La API genera ambos
desde la misma entidad; no admite JSON arbitrario como entrada. No se pretende
resistencia frente a edición maliciosa directa de SQLite.

- `registrar(entidad)` crea revisión 1. Repetir el mismo registro es idempotente.
  Cambiar su contenido mediante registro ordinario se rechaza como contradicción.
- `actualizar(entidad, revision_esperada=..., motivo=...)` exige revisión actual,
  motivo público y procedencia con fecha estrictamente posterior. Autoriza expresamente
  revisar metadatos conservando el estado anterior en el historial.
- Identidad, código original y asociaciones no se reasignan mediante actualización.
  Corregirlos requiere registrar otra identidad con la procedencia correspondiente;
  no hay API de borrado, fusión ni corrección automática de vínculos.
- `historial(entidad)` devuelve las entidades y números de revisión anteriores.
  El motivo y fecha informática también se conservan en la tabla revisiones.
- `registrar_documental(entidad)` es una política optativa para fuente, producto,
  recurso y capacidad: NUEVO, IDENTICO, REVISION_DOCUMENTAL o CONTRADICCION.
  Conserva `registrar` y `actualizar` sin cambiar sus firmas ni su comportamiento.
  `consultar_revision(entidad, revision)` recupera una versión histórica concreta;
  `consultar_recurso(..., revision=None)` y `listar_recursos` consultan recursos.
  Véanse los campos protegidos y la política de fechas en el contrato del PASO 65.

El registro y su historial se confirman en una única transacción BEGIN IMMEDIATE.
Un escritor con revisión obsoleta se rechaza tras obtener el bloqueo SQLite. Se
activan claves foráneas y synchronous=FULL. Uso previsto: operaciones secuenciales
por conexión; timeout de bloqueo de cinco segundos. No se ha probado durabilidad
ante corte eléctrico, concurrencia distribuida o manipulación externa del catálogo.
No hay migraciones de descubrimiento: versiones no admitidas se rechazan.

## Consulta y búsqueda

Las consultas puntuales son `consultar_fuente`, `consultar_producto`,
`consultar_estacion`, `consultar_variable`, `consultar_disponibilidad` y
`consultar_capacidad`. Devuelven `RegistroCatalogo(entidad, revision)`.
`listar(tipo, fuente=None, producto_id=None)` permite explorar cada clase registrada.
Un registro ausente produce metadato_no_identificado, no una afirmación de inexistencia.

`buscar(FiltroCatalogo(...))` admite colecciones de fuentes, IDs originales de
productos/estaciones, IDs internos o códigos originales de variables, frecuencias,
mecanismos y un período solicitado. Cada colección combina sus valores con OR;
los distintos filtros se combinan para evaluar el alcance registrado. Los IDs
internos y códigos de variable, si se proporcionan ambos, deben corresponder.
No hay búsqueda difusa ni traducción de variables/unidades/frecuencias.

El resultado contiene productos candidatos, evaluaciones por registro temporal,
capacidades compatibles y señales `sin_evidencia_del_alcance`/`mecanismo_desconocido`.
Las búsquedas son exploratorias: si un método o asociación no se ha identificado,
se conserva el candidato con esa incertidumbre, aunque existan referencias de otros
métodos. La lista de capacidades no se considera exhaustiva. Un producto declarado
sin estaciones se excluye de una consulta que exige estaciones.

Un registro general con estación/variable/frecuencia desconocida no demuestra
el filtro específico: se devuelve con alcance_exacto=False. Un registro explícito
de otra estación o variable no se propaga al alcance solicitado. Una consulta
multiestación/multivariable no genera un producto cartesiano de disponibilidades
ni demuestra cobertura para todas las combinaciones solicitadas.

### Semántica temporal provisional

Cada disponibilidad representa un intervalo independiente. Puede haber múltiples
intervalos discontinuos, extremos desconocidos o cobertura parcial. Nunca se fusionan
para afirmar continuidad entre ellos. `cobertura_parcial` se conserva aunque los
extremos del intervalo contengan el período solicitado.

Los extremos conocidos son datetime. Pueden ser locales sin zona cuando esta es
desconocida: en ese caso no se inventa UTC y la comparación con una consulta de
instantes devuelve DESCONOCIDA. No se convierten zonas declaradas por nombre ni
se deduce una zona a partir de coordenadas. Un período solicitado exige dos extremos
con zona conocida y orden válido; se usan extremos inclusivos en esta versión.

Las evaluaciones distinguen SIN_FILTRO, DESCONOCIDA, CONTIENE_PERIODO,
SOLAPAMIENTO_PARCIAL y FUERA_COBERTURA_CONOCIDA. Si la disponibilidad tiene estado
DESCONOCIDO, no se promueven sus límites a cobertura conocida. Un intervalo abierto
queda desconocido salvo que un límite conocido ya demuestre que está fuera de la
consulta. Los registros fuera de cobertura se devuelven etiquetados, no como
evidencia de que el recurso no exista.

CONTIENE_PERIODO significa que los extremos registrados contienen la consulta:
no prueba observaciones completas, frecuencia cumplida, ausencia de huecos ni calidad
científica. El estado DECLARADO/VERIFICADO y la cobertura parcial siguen visibles.

## Garantías comprobadas y límites

Las pruebas usan exclusivamente SQLite y metadatos sintéticos temporales. Cubren
relaciones, IDs repetidos, varias variables por estación, asociaciones parciales,
intervalos discontinuos/desconocidos, frecuencias, recursos sin estaciones,
revisiones contradictorias, historial, persistencia, filtros y rechazo de secretos.
La base RAW sintética ajena no se adopta ni modifica; los componentes previos siguen
probándose en la suite completa.

No se implementan conectores, comprobaciones remotas, inventario institucional real,
descargas, interfaz gráfica, planificador, búsqueda espacial, conversiones científicas,
consultas históricas as-of ni asociación automática a activos RAW. Las búsquedas
recorren metadatos en memoria, no los archivos científicos: deben revisarse paginación,
índices de búsqueda y límites antes de grandes inventarios. El catálogo requiere un
directorio privado, respaldo y una política de revisión humana para discrepancias.

```powershell
& .\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
& .\.venv\Scripts\python.exe -B -m pip check
```
