# Paso 60: piloto SENAMHI–PNDA GBON/RBON

El conector descubre recursos publicados y adquiere un diccionario XLSX por medio
de los componentes SUADC existentes. No interpreta observaciones ni depende de una
lista cerrada de variables ambientales. No implementa un motor HTTP adicional.

## Referencia y autorización

Producto oficial:
https://www.datosabiertos.gob.pe/dataset/variables-meteorologicas-de-las-estaciones-autom%C3%A1ticas-de-intercambio-internacional-servicio

Solo se consulta el origen explícito `https://www.datosabiertos.gob.pe`, usando
`ClienteHTTP`. La página se lee con `get()` (máximo 1 MiB). Se reconocen enlaces
`a.data-link` dentro de bloques `dcat:Distribution`; enlaces del pie, scripts,
formularios, enlaces de previsualización y APIs no se ejecutan ni se consideran
recursos descargables. La URL del archivo no se construye a partir de su nombre:
se resuelve exclusivamente el href publicado mediante la URL de la página.

El alcance de este piloto acepta archivos bajo `/sites/default/files/` en el mismo
origen HTTPS. Consultas, fragmentos, credenciales, referencias ambiguas y orígenes
adicionales se rechazan/omiten con advertencias seguras. Las redirecciones se
rechazan por la política común, incluso si apuntan al mismo origen. Un cambio de
estructura HTML sin recursos reconocibles falla explícitamente y revoca el último
descubrimiento; nunca intenta rutas alternativas ni autenticación.

La identidad local de la fuente es `Fuente("SENAMHI", "SENAMHI")`, espacio de
nombres institucional, no código de estación. El identificador del producto es el
slug original de `/dataset/`, conservando mayúsculas y escapes; la URL completa
permanece como referencia pública y procedencia. No se presenta ese slug como el
UUID DCAT. Esta elección permite persistir `producto_id` en los parámetros públicos
de RAW: su política existente omite URLs como valores de parámetros, y no se debilitó.
Si cambia el slug o la publicación, se requiere revisión explícita de identidad;
no hay reconciliación automática entre alias o versiones.

## Componentes

- `modelos.py`: `RecursoPublicado`, `CatalogoRecursos`, `AdquisicionPNDA`, roles
  documentales, referencias oficiales y errores seguros.
- `pnda.py`: `ConectorSENAMHIPNDA.descubrir()`, `registrar_catalogo()` y `adquirir()`.
- `__init__.py`: interfaz pública del paquete institucional.

`RecursoDescubierto` del núcleo representa la identidad original de cada archivo
(URL resuelta), separada del producto y de cada adquisición RAW. `href_original`
conserva además el enlace tal como fue publicado. Las fechas de comprobación son
UTC y pertenecen al acceso técnico, no a observaciones ni fechas de publicación.

La extensión del enlace constituye un formato declarado, no detección física de
tipo. Se representan CSV, XLSX, DOCX y otras extensiones sin whitelist de formatos
del modelo. La clasificación documental utiliza el título publicado. Una extensión
XLSX sin un título que identifique diccionario no autoriza su adquisición.

El conector no tiene filtros de estaciones, variables o fechas. No crea estaciones,
diccionarios científicos, unidades, zonas horarias ni disponibilidad temporal.
Configuración alternativa de producto se admite dentro de la PNDA para extensiones
posteriores; el operador debe comprobar previamente su pertenencia a SENAMHI.

## Catálogo y alcance de las evidencias

`descubrir()` devuelve un catálogo de recursos tipado y acotado en memoria: máximo
100 distribuciones/recursos por defecto, máximo configurable 1000, ocho enlaces
por distribución y 256 elementos de anidación HTML. Los enlaces repetidos se
conservan una sola vez y producen advertencia. No se añade un esquema SQLite.

`registrar_catalogo(catalogo)` registra explícitamente fuente, producto, licencia
declarada (URL publicada) y capacidad HTTP_DIRECTO DECLARADA. Se reutilizan las
reglas del catálogo: la misma evidencia es idempotente y una revisión distinta no
se sobrescribe automáticamente. Son tres registros, sin transacción conjunta;
un conflicto posterior puede dejar registros previos ya guardados. El llamador
debe revisar conflictos y usar las revisiones controladas existentes.

Una adquisición completa devuelve una `capacidad_recurso` VERIFICADA, con referencia
al archivo concreto y al asset persistido. **No se registra esa capacidad como
garantía de todos los archivos del producto en el catálogo del planificador**:
su contrato actual no delimita capacidades por recurso. El conjunto de recursos y
la evidencia específica se entregan al llamador; su persistencia adicional requiere
un informe externo explícito, no una migración automática de los catálogos actuales.

HTTP 200 de la página comprueba acceso público a metadatos, no a cada archivo. La
licencia y formatos permanecen declarados. Los mocks prueban el comportamiento
local; no son evidencia de disponibilidad del servicio real. Los planes existentes
siguen condicionados y no se convierten en ejecutables automáticamente.

## Adquisición y garantías

El constructor recibe un `ClienteHTTP` prestado y, opcionalmente, su mismo
`AdaptadorHTTPRAW`. Comprueba TLS habilitado, límites de hasta 1 MiB y la clave
pública `producto_id` autorizada por el almacén. El llamador configura los orígenes
y los reintentos; para la prueba externa se exige `PoliticaReintentos(max_intentos=1)`.
No se cambia la política de un cliente prestado ni se cierran sus componentes.

`adquirir(recurso_id, proyecto_id=..., objeto_id=...)` solo acepta un recurso del
descubrimiento actual clasificado como diccionario XLSX. **CSV, DOCX y otros roles
no están autorizados para este piloto**, aunque aparezcan en el catálogo. No hay
descarga automática ni adquisición de todos los enlaces. El límite de transferencia
lo impone el adaptador, con un máximo de 1 MiB. No se incluyen parámetros remotos.

La operación delega íntegramente a `AdaptadorHTTPRAW`: streaming al staging, tamaño
real y Content-Length cuando exista, SHA-256 calculado/releído físicamente,
incorporación sin sobrescritura, persistencia y recuperación física desde RAW. Se
conservan el original, su fuente, recurso, proyecto/objeto y producto. El hash local
no es una firma de SENAMHI ni se compara con un hash oficial inexistente en la
evidencia. No se inspecciona ni valida internamente el formato XLSX, ni se transforma
su contenido; `media_detected` permanece desconocido. Un HTTP 200 con contenido
erróneo podría preservarse técnicamente: la validación de formato queda pendiente.

Se mantienen los errores comunes, limpieza/residuos informados, rechazo de HTTP
206, compresión HTTP y redirecciones. El contenedor ZIP propio de XLSX no es
compresión HTTP y no se descomprime. Fallos de descarga no generan una capacidad
verificada. Si falla después de persistir RAW, pueden existir activos/eventos
recuperables: no hay transacción global entre red, archivos y catálogos.

Dos adquisiciones idénticas conservan asset_id distintos y pueden compartir bytes
solo después de las comprobaciones RAW existentes. No hay caché HTTP, deduplicación
preventiva de solicitudes ni comprobación automática de novedades del proveedor.

## Uso controlado

```python
from spica.adquisicion.transportes import ClienteHTTP, PoliticaReintentos
from spica.adquisicion.integracion import AdaptadorHTTPRAW
from spica.adquisicion.conectores.senamhi import (
    ORIGEN_PNDA, ConectorSENAMHIPNDA, RolRecurso,
)

# almacen y staging son privados, externos al repositorio y preparados por el
# operador. AlmacenRAW debe autorizar claves_parametros_publicos=("producto_id",).
with ClienteHTTP((ORIGEN_PNDA,),
                 politica_reintentos=PoliticaReintentos(max_intentos=1)) as cliente:
    adaptador = AdaptadorHTTPRAW(cliente, almacen, staging, max_bytes=1_048_576)
    conector = ConectorSENAMHIPNDA(cliente, adaptador)
    publicacion = conector.descubrir()
    candidatos = [r for r in publicacion.recursos
                  if r.rol is RolRecurso.DICCIONARIO and r.recurso.formato == "xlsx"]
    if len(candidatos) != 1:
        raise RuntimeError("Seleccion del diccionario requiere revision")
    resultado = conector.adquirir(candidatos[0].recurso.identificador,
                                  proyecto_id=proyecto_id, objeto_id=objeto_id)
```

El ejemplo realiza una descarga si se ejecuta: no debe colocarse en importaciones
ni en las pruebas unitarias. Debe detenerse ante cambios de origen/autenticación,
redirecciones o errores, sin repetir automáticamente la operación.

## Pruebas y pendientes

Las pruebas unitarias usan SQLite efímero, `httpx.MockTransport` y un ZIP sintético;
no contactan PNDA. Cubren procedencia, identidad, catálogo, límites, errores,
interrupciones, duplicados, credenciales y compatibilidad con el planificador.

Quedan pendientes persistencia específica/versionada de recursos, evidencia HTML
durable del descubrimiento, validación técnica del formato, caducidad de enlaces,
reconciliación de identificadores, descarga aprobada de datos y lectura científica.
La detección conservadora de secretos no identifica universalmente valores opacos:
el llamador solo debe proporcionar identificadores y metadatos públicos revisados.
No se implementan autenticación institucional, CAPTCHA, navegador automatizado,
filtrado remoto, otras instituciones ni análisis científico.

## Resultado de la prueba externa controlada

El 2026-10-29, tras aprobar la suite simulada y recibir autorización explícita
para la operación externa, el conector descubrió tres recursos en la publicación
oficial. Se adquirió **únicamente el diccionario XLSX**, con un solo intento y
límite de 1 MiB. CSV y DOCX no se descargaron.

| Evidencia | Resultado |
| --- | --- |
| HTTP del archivo | 200 |
| Tamaño real y Content-Length | 10815 bytes, coincidentes |
| SHA-256 de bytes persistidos y releídos | `1851039a07682a3f202314f6f8811fc616cb4ca2a486c9e737fd8cea62a4b4dd` |
| asset_id | `b6aa17105088497296147feb3c8f06e3` |
| Comprobación RAW UTC | `2026-10-29T07:38:47.823590+00:00` |
| Temporales de transferencia restantes | Ninguno |
| Validación científica / formato interno XLSX | No ejecutadas |

Los originales, SQLite y `informe.json` quedaron exclusivamente en la carpeta
externa `SPICA-SUADC-piloto-PNDA-soacxq6v`, bajo el directorio temporal del usuario.
Su ACL está protegida y solo concede control al propietario (OWNER RIGHTS), SYSTEM
y administradores. El entorno restringido no podía acceder a ella; se verificaron
los permisos y se ejecutó la prueba autorizada fuera de ese aislamiento sin ampliar
la ACL. La carpeta temporal puede ser limpiada por el sistema y no sustituye una
ubicación de conservación operativa aprobada ni un respaldo.

`informe.json` conserva las URLs exactas publicadas, licencia declarada, fecha de
comprobación, identidades de producto/recurso/activo y resultado técnico. La
capacidad verificada corresponde exclusivamente al archivo descargado. No se
publicó una garantía de acceso a todos los archivos ni de cobertura temporal.

Verificación de esta versión: 333 pruebas aprobadas (297 anteriores y 36 nuevas),
0 fallos y 0 errores; `pip check`: `No broken requirements found.`
