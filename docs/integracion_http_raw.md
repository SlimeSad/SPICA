# Paso 53: integración experimental HTTP → RAW

`spica.adquisicion.integracion.AdaptadorHTTPRAW` coordina el `ClienteHTTP` y el
`AlmacenRAW` existentes. No crea otro cliente, no cambia sus políticas y no migra
catálogos. No incorpora conectores institucionales ni transformaciones científicas.

El PASO 65 añade `adquirir_documentado(url, declaracion, evidencia, *, parametros=None)`
sin modificar `adquirir()`. Comparte exactamente la misma descarga, comprobación,
incorporación y limpieza. Conserva una instantánea documental por adquisición junto
al activo RAW, sin migrar SQLite. `AlmacenRAW.consultar_evidencia(asset_id)` y
`consultar_adquisicion(adquisicion_id)` recuperan sus metadatos después de reabrir;
`recuperar(asset_id)` sigue siendo necesario para comprobar los bytes actuales.
Véanse [las garantías y límites](registro_evidencias.md).

El PASO 66 añade un resultado `estructura` y la propiedad `utilizable_documentalmente`.
La inspección local se realiza después de recuperar/verificar físicamente RAW, con
una `politica_estructura` opcional en el adaptador. Las respuestas inesperadas se
conservan sin sobrescribir originales, con un estado estructural independiente del
éxito HTTP y de la integridad SHA-256. No se guarda todavía este informe en SQLite
ni se modifica `media_detected`. Véase [Verificación de formatos](verificacion_formatos.md).

## API y directorios

El constructor recibe `cliente`, `almacen`, `directorio_temporal`, `max_bytes`
obligatorio y `tamano_bloque` opcional (64 KiB por defecto, máximo 1 MiB).
Los componentes son prestados: el llamador los configura y cierra. El límite HTTP
por descarga y el límite de incorporación RAW permanecen independientes; ambos
deben admitir el archivo para que la operación termine satisfactoriamente.

El staging debe existir dentro de una raíz de entrada autorizada de AlmacenRAW,
fuera del directorio RAW. Se rechazan symlinks/junctions. El operador debe asegurar
permisos privados sobre esa raíz. Cada operación crea exclusivamente una subcarpeta
con UUID: POSIX usa modo 0700; Windows hereda ACL del padre, sin asumir que chmod
pueda demostrar privacidad. No se inspeccionan automáticamente ACL de Windows.
No se creó un staging operativo durante esta tarea, solo directorios de prueba.

`adquirir(url, declaracion, *, parametros=None)` acepta `DeclaracionRAW` y parámetros
de consulta texto/texto. La procedencia declarada debe estar vacía o coincidir con
la URL de solicitud. RAW registra la versión pública saneada de esa URL mediante
el filtro existente, sin usuario, contraseña, consulta ni fragmento. No se conserva
una segunda URL potencialmente sensible. Los parámetros científicos públicos solo
se conservan si el llamador los declara explícitamente y RAW autoriza sus claves;
no se inventan estaciones, variables, unidades ni fechas de observación.

## Secuencia y continuidad de bytes

1. Se valida la declaración pública antes de descargar, sin persistirla todavía.
2. `ClienteHTTP.descargar()` ejecuta GET en la subcarpeta propia. Conserva la lista
   de orígenes, TLS, timeouts, redirecciones desactivadas, límite de bytes, rechazo
   de 206/compresión y política de reintentos. Su nombre local fijo es descarga.bin;
   ningún nombre de la URL o del servidor decide rutas.
3. El informe debe declarar descarga completa, ruta exactamente esperada y tamaño
   y SHA-256 válidos. El informe HTTP no equivale a un activo RAW incorporado.
4. RAW copia el archivo a su propio temporal y lo relee físicamente, como antes.
   Se añaden a `AlmacenRAW.incorporar()` dos argumentos opcionales por nombre:
   `tamano_esperado` y `sha256_esperado`. Ambos se exigen juntos, con formato válido.
   Se contrastan con el tamaño/hash de la copia releída **antes** de publicar y de
   declarar INCORPORADA. Una discrepancia genera evidencia_entrada_no_coincidente,
   un registro FALLIDA cuando SQLite lo permite y ninguna publicación de ese intento.
5. RAW publica sin sobrescribir, registra el activo y conserva la deduplicación.
6. El adaptador contrasta los metadatos retornados con el informe HTTP y llama
   `recuperar()`, que vuelve a comprobar físicamente el archivo publicado. Solo
   entonces devuelve `ResultadoHTTPRAW` con fase COMPLETADA.

No se trata solo de comparar dos hashes declarados: HTTP calcula/relee el archivo
descargado, RAW calcula/relee su copia y la recuperación comprueba el archivo final.
Modificar el staging entre etapas, incluso conservando su tamaño, impide la publicación
si los bytes ya no coinciden con la evidencia HTTP. Modificar el archivo RAW después
de publicarlo impide el éxito de la comprobación final.

Los nuevos argumentos RAW son compatibles con todas las llamadas anteriores, que
pueden omitirlos. No cambian los contratos del núcleo ni el esquema SQLite. La
evidencia HTTP es un enlace técnico entre etapas locales, no un checksum firmado
por una institución y no produce `Integridad.VERIFICADA` o validez científica.

## Resultado, identidades y persistencia

El resultado contiene el informe HTTP, el ActivoRAW, la ruta comprobada, una copia
del historial técnico de intentos HTTP y la ruta de staging residual si no pudo
limpiarse. El informe HTTP es histórico: su ruta local normalmente habrá sido
eliminada. Para usar el activo se debe emplear la referencia RAW, no esa ruta HTTP.

La identidad de proyecto, objeto, recurso externo y SHA-256 conserva su significado.
En el modelo actual cada adquisición/incorporación se identifica por un nuevo
asset_id; no se añade un ID persistente separado de operación HTTP. Dos ejecuciones
con el mismo contenido conservan activos y procedencias individuales, compartiendo
solo el contenido físico. Los metadatos MD-01/02 existentes no se sobrescriben.

Funciona con SQLite v1 y v2 mediante las operaciones RAW compatibles. No requiere
registrar metadatos nuevos de proyecto/objeto ni invoca migraciones. El catálogo
guarda declaración pública y eventos RAW; el informe y el historial HTTP se devuelven
en memoria y no se añaden a nuevas tablas. Antes de la incorporación, un fallo HTTP
no crea un activo ficticio ni un registro RAW confirmado.

## Errores, estados incompletos y limpieza

`ErrorIntegracionHTTPRAW` expone un código seguro, fase (VALIDACION, DESCARGA,
INCORPORACION o COMPROBACION), asset_id si estuvo disponible, código HTTP, historial
de intentos y staging residual. No conserva URL/consulta/cabeceras ni la excepción
de red como causa visible en la traza pública. No emite logs. Se utilizan únicamente
credenciales sintéticas para comprobar esta protección en las pruebas.

Errores HTTP, timeout, truncamiento, 206, compresión y límites impiden incorporar.
Errores RAW de tamaño/hash, escritura, SQLite o publicación impiden devolver éxito.
Una falla de persistencia tras publicar puede dejar una operación incompleta o un
contenido sin incorporación disponible: `AlmacenRAW.diagnosticar()` permite detectarlo.
No se elimina ni se repara ese contenido, que podría pertenecer a otra adquisición.

La limpieza retira solo la subcarpeta propia, previa comprobación de su ruta absoluta
y pertenencia a la raíz de staging. Una colisión al crearla no autoriza borrar una
carpeta preexistente. Nunca se elimina la ruta RAW ni se sigue una ruta arbitraria
devuelta por un informe. Incluye los residuos del descargador dentro de esa operación;
RAW gestiona sus propios temporales y los diagnostica si no pudo retirarlos.

Ante un error, la limpieza se intenta antes de propagarlo. KeyboardInterrupt/SystemExit
se propagan tras el mismo intento. Si la limpieza falla se informa temporal_restante;
si RAW ya se incorporó y verificó, el resultado sigue siendo COMPLETADA con ese residuo
indicado. No se implementa eliminación automática en el siguiente inicio. Un cierre
forzado puede dejar la subcarpeta y no permitir retornar un informe: el operador debe
gestionar esos residuos sin confundirlos con originales RAW.

## Garantías comprobadas y límites

Las pruebas emplean MockTransport, archivos sintéticos y SQLite temporal: éxito,
vacío, más de 1 MiB, tamaño/hash reales, alteración entre etapas, errores HTTP,
timeout, truncamiento, escritura, SQLite, deduplicación, destino corrupto existente,
procedencia pública, credenciales, limpieza, interrupciones, estados incompletos,
cancelación, reutilización de reintentos y funcionamiento v1 sin migración.

No hay atomicidad global entre red, disco y SQLite. La lectura puede servirse desde
caché; no prueba el medio físico ni la preservación futura. No se impide que un actor
con permisos de escritura altere el archivo después de devolver la ruta. El diseño
requiere componentes confiables, directorios privados y operaciones secuenciales;
no resiste carreras hostiles de sustitución de carpetas ni verifica automáticamente ACL.

El adaptador no reintenta toda la incorporación RAW: solo reutiliza los reintentos
del transporte. La cancelación HTTP es cooperativa durante la descarga, no una
cancelación transaccional de RAW. El filtrado de metadatos no detecta universalmente
secretos opacos. La procedencia debe aprobarse como pública. No certifica autenticidad
institucional, media_detected ni calidad científica.

Pendientes: recuperación operativa, respaldo, concurrencia, durabilidad frente a
cortes eléctricos, persistencia del informe HTTP y conectores institucionales.
