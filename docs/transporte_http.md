# Transporte HTTP común del SUADC

`transportes/http.py` implementa `ClienteHTTP`, un cliente síncrono GET con HTTPX
0.28.1. La única dependencia directa está fijada en `requirements.txt`.
No importa ni modifica modelos de adquisición o científicos.

## Uso y autorización

El llamador debe autorizar previamente cada recurso y proporcionar los orígenes
permitidos al constructor. No hay destinos predeterminados ni endpoints institucionales.
Un origen incluye esquema, host y puerto; no admite ruta, consulta, credenciales
o fragmento. `get(url, parametros=...)` exige una URL HTTP(S) absoluta de uno de
esos orígenes y admite parámetros texto/texto. No se normalizan sus valores.
HTTPX realiza la codificación de consulta; si se pasan parámetros a una URL con
consulta existente, aplica su semántica de sustitución de consulta. Conviene pasar
la consulta íntegra mediante `parametros`.

La lista de orígenes limita destinos; no verifica permisos del usuario, legitimidad
de recursos ni seguridad de direcciones resueltas por DNS. HTTP sin TLS solo se
permite si se autoriza explícitamente ese origen. No es una protección completa SSRF.

Usar el cliente con `with ClienteHTTP(...) as cliente:` o llamar `close()`.
El cliente es dueño del transporte, incluso si se inyecta para pruebas.

## Configuración y lectura

`ConfiguracionHTTP` es inmutable. Valores predeterminados:

| Opción | Valor |
| --- | --- |
| Timeout de conexión | 10 segundos |
| Timeout de lectura | 30 segundos |
| Timeout de escritura | 30 segundos |
| Timeout de pool | 10 segundos |
| Verificación TLS | activada |
| Límite de cuerpo | 1 MiB (1 048 576 bytes) |

Los timeouts deben ser positivos y finitos. Son límites de operación/inactividad
de HTTPX, no un plazo total de solicitud. Desactivar TLS exige configuración
explícita; no debe usarse en producción. Con un transporte inyectado, la seguridad
de red corresponde a ese transporte; MockTransport no ejecuta TLS.

Las redirecciones están desactivadas y se devuelven como error, sin una segunda
petición. `trust_env=False` desactiva proxies y configuración de certificados del
entorno. No hay seguimiento automático de destinos no autorizados.

Se usa `Client.stream` e `iter_raw` para leer incrementalmente; el buffer del cuerpo
no supera el límite configurado. Se rechaza anticipadamente un Content-Length que
supere el límite y también se cuenta lo recibido si falta o miente esa cabecera.
Al finalizar se compara el tamaño con Content-Length, si existe. Esa comparación
es de transporte y no demuestra integridad científica ni autenticidad del archivo.

La respuesta exitosa contiene código HTTP, cabeceras de solo lectura y bytes del
cuerpo pequeño. Convertir el buffer a bytes implica una copia acotada; también
existen buffers internos de HTTPX y del transporte. No se llama `read()` para
acumular respuestas sin límite. No aumentar el límite para archivos científicos
grandes: todavía no existe una API para descargarlos a disco.

Se solicita `Accept-Encoding: identity` y se rechazan cuerpos comprimidos, sin
descomprimirlos. Esto evita expandir datos antes de aplicar el límite. El alcance
actual es la lectura de respuestas pequeñas, no una descarga RAW completa.

## Errores

`ErrorTransporteHTTP` expone `tipo` y, para estados rechazados, `codigo_http`.
No guarda el cuerpo de error ni incluye URL o parámetros en su mensaje. Conserva
la excepción HTTPX como causa: no registrar indiscriminadamente trazas que puedan
contener datos sensibles.

- 401: no autenticado; 403: prohibido; 404: no encontrado.
- 429: límite de solicitudes; no se interpreta Retry-After ni se reintenta.
- 5xx: error del servidor; otros estados no exitosos: error HTTP general.
- 3xx: redirección rechazada; 206: respuesta parcial rechazada.
- Timeout, conexión y otros errores HTTPX de transporte tienen categorías distintas.
- Tamaño excesivo, compresión no admitida, longitud inválida o discrepante generan
  errores técnicos. Se cierra la respuesta tanto en éxito como en error.

Una respuesta 2xx aceptada no se convierte en `Descarga`, `Integridad` o estado
`CONFIRMADO`. No se escribe ni verifica físicamente ningún archivo.

## Pruebas y pendientes

Todas las solicitudes de las pruebas usan `httpx.MockTransport` y destinos
ficticios `.invalid`. Los flujos simulados permiten verificar el corte de lectura,
cierre, discrepancias y errores durante la transferencia sin internet ni archivos.

```powershell
& .\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
& .\.venv\Scripts\python.exe -B -m pip check
```

Quedan pendientes descargas por streaming a disco, escritura atómica, reanudación,
reintentos, autenticación, gestión de cookies, redirecciones autorizadas,
descompresión acotada, soporte asíncrono y verificación física de archivos/hashes.
El cliente HTTPX mantiene cookies de sesión recibidas por su comportamiento estándar;
no se implementa una política específica de sesión. Usar clientes separados cuando
se necesite aislar sesiones. La lectura incremental interna y la inyección de
transporte permiten extender la implementación sin acoplarla a instituciones.
