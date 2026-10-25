# Reintentos GET del SUADC

`PoliticaReintentos` y el gestor común de `transportes/reintentos.py` se integran
en `ClienteHTTP`. El gestor no crea conexiones: ejecuta nuevamente la operación
GET usando el cliente existente. Las interfaces de `get()` y `descargar()` no
cambian. Tampoco cambian los contratos del núcleo, la validación científica ni
el significado de descarga completa o integridad pendiente.

## Configuración explícita

El constructor de `ClienteHTTP` admite `politica_reintentos`, `espera`, `aleatorio`,
`reloj` y `cancelacion` como argumentos opcionales por nombre. Para habilitar tres
intentos totales, proporcionar `PoliticaReintentos(max_intentos=3)`.

| Parámetro de política | Predeterminado | Validación |
| --- | --- | --- |
| max_intentos | 1 | Entero de 1 a 100, incluye el primer intento |
| espera_inicial | 1 segundo | Finita, no negativa y no mayor que espera_maxima |
| espera_maxima | 60 segundos | Finita, entre 0 y 3600 segundos |
| jitter | 0.2 | Finito, entre 0 y 1 |

El valor predeterminado de un intento conserva el comportamiento anterior;
los reintentos son optativos. Configurar cero segundos permite reintentos inmediatos
acotados por el número de intentos; debe evitarse para servicios bajo carga.

Tras el intento fallido n, la espera es:

```
base = min(espera_maxima, espera_inicial * 2**(n - 1))
retroceso = min(espera_maxima, base * (1 + jitter * U))
espera = max(retroceso, Retry-After válido)
```

`U` está entre 0 y 1. Se puede inyectar una función `aleatorio()` para reproducir
las pruebas; un valor fuera de rango produce ValueError. La espera se invoca solo
antes de otro intento, nunca después del último. No hay presupuesto global de tiempo
o bytes: las esperas y límites de transferencia se aplican por intento. El máximo
teórico de espera entre intentos es `(max_intentos - 1) * espera_maxima`, además
del tiempo de red, escritura y verificación de cada intento.

## Clasificación

Se reintentan únicamente operaciones GET autorizadas que fallen por:

- HTTP 408, 429, 500, 502, 503 y 504.
- ConnectError sin diagnóstico TLS y timeouts HTTPX de conexión, lectura, escritura
  o pool, siempre que no haya evidencia de error TLS.
- ReadError, WriteError y RemoteProtocolError sin diagnóstico TLS.
- Un flujo que termina con menos bytes que Content-Length (truncamiento).

Son definitivos los demás estados, incluidos 401, 403, 404, 3xx, 206 y otros 5xx
como 501; errores de protocolo local o protocolo no admitido; longitud inválida,
exceso de bytes respecto a la longitud declarada, límite excedido, compresión,
error de disco, publicación, destino existente, integridad local contradictoria
o fallo de limpieza del temporal. No se reintentan configuración o autorización
inválidas, cancelación, KeyboardInterrupt ni SystemExit.

Los fallos TLS/certificados se detectan por SSLError en las cadenas de causas y
contextos; como respaldo, se reconocen diagnósticos textuales de certificado/TLS/SSL.
Se marcan `TipoErrorHTTP.TLS` y no se reintentan ni se desactiva la verificación TLS.
Esta clasificación es conservadora, pero depende de que el backend conserve un
diagnóstico reconocible. Un ConnectError opaco no permite distinguir con certeza
una falla permanente de DNS de una temporal; queda acotado por max_intentos.

No existe API POST ni una política para otras operaciones. Orígenes, TLS, timeouts,
redirecciones desactivadas y límites se vuelven a aplicar en cada intento.

## Retry-After

En los estados HTTP recuperables se acepta un entero ASCII no negativo en segundos
o una fecha HTTP, incluidos los formatos históricos RFC 850 y asctime. Los valores
inválidos se ignoran y se aplica el retroceso. Fechas pasadas equivalen a cero.
Las fechas usan el reloj UTC inyectable del gestor; no se ajusta con la cabecera Date.

El plazo del servidor es un mínimo: el jitter no puede adelantarlo. Si supera
espera_maxima, se propaga el error sin nuevo intento y se registra `limite_espera`.
No se recorta el plazo para solicitar antes de lo indicado. No se conserva ni
registra el texto original de la cabecera. La interpretación de fechas depende
del reloj del sistema; un desfase puede alterar la espera efectiva.

## Descargas y cancelación

Cada intento de descarga crea su propio temporal y reinicia la recepción desde
cero; no concatena bytes ni utiliza Range. El intento anterior cierra la respuesta
y el archivo e intenta eliminar su temporal antes de autorizar otro intento.
Si deja un temporal residual, el error se vuelve definitivo para evitar acumular
fragmentos. Un destino publicado satisfactoriamente no se vuelve a descargar,
incluso si no se pudo retirar su nombre temporal. El destino existente o creado
durante la espera se conserva; la publicación sigue siendo exclusiva.

`cliente.cancelar()` activa una señal persistente. También se puede inyectar un
`threading.Event` mediante `cancelacion`. Se comprueba antes de iniciar operaciones,
entre bloques de recepción/relectura y antes de publicar. La espera predeterminada
usa Event.wait, por lo que se interrumpe cuando se activa la señal. Una función
`espera(segundos)` inyectada debe proporcionar su propia capacidad de interrupción;
se vuelve a comprobar la señal antes de otro intento.

La cancelación es cooperativa: no interrumpe inmediatamente una llamada bloqueada
de red o disco. Los timeouts existentes limitan algunas de esas esperas. Si la
señal llega después de publicar el archivo, puede retornarse éxito; no se elimina
un archivo ya publicado. Para nuevas operaciones tras cancelar, crear otro cliente
o gestionar explícitamente el Event externo cuando no exista una operación activa.

## Registro y agotamiento

`cliente.historial_intentos` expone una tupla inmutable de `RegistroIntento` de la
última operación: número, resultado, categoría de causa, código HTTP y espera
planificada. Los resultados son exito, reintento, definitivo, agotado, limite_espera
o cancelado. No hay URLs, consultas, credenciales, cuerpos ni texto de excepción.
No se emiten logs ni se crea un catálogo. Una cancelación antes de solicitar se
registra con número cero; una cancelación entre intentos no cuenta una solicitud nueva.

Al agotar los intentos se propaga el último ErrorTransporteHTTP (o ErrorDescargaArchivo),
con `agotados=True`, `intentos` e `historial`. No se cambia la clase del error original
ni se oculta su causa técnica. Un fallo definitivo tiene `agotados=False`; el último
registro diferencia el límite de espera del agotamiento. La excepción de descarga
conserva su informe técnico del último intento. Los errores de configuración previos
a una solicitud no generan registros de intentos HTTP.

Las causas originales pueden incluir datos sensibles; no registrar indiscriminadamente
la traza completa. El historial se reemplaza en cada operación y no es un registro
duradero. El cliente/gestor se diseña para operaciones secuenciales, sin aislamiento
de historial o cancelación para varias operaciones concurrentes.

## Verificación y límites pendientes

Las pruebas usan MockTransport, esperas simuladas, reloj UTC fijo y flujos/archivos
temporales; no realizan conexiones reales ni demoras de retroceso. Cubren estados
transitorios y definitivos, TLS, Retry-After, topes, jitter, agotamiento, cancelación,
reinicio de streaming, limpieza y conservación de originales.

Siguen pendientes reanudación, autenticación institucional, presupuesto global,
coordinación de límites entre clientes, circuit breaker, observabilidad persistente,
operaciones asíncronas, conectores, evidencia externa de integridad y validación
científica. Los reintentos pueden aumentar tráfico, tiempo y uso de disco; no
garantizan que dos respuestas GET contengan la misma versión del recurso.
