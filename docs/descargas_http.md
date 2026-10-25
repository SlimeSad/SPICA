# Descarga HTTP a disco de staging

La operación `ClienteHTTP.descargar(url, directorio, nombre, *, max_bytes,
tamano_bloque=65536, parametros=None)` reutiliza el mismo `httpx.Client`, timeouts,
autorización de orígenes, clasificación de errores y control de redirecciones
que `get()`. No crea otro cliente ni modifica los contratos del núcleo.
No hay endpoints institucionales ni solicitudes reales en las pruebas.

## Límites y política de red

`max_bytes` es obligatorio y positivo, independiente del límite de 1 MiB de `get()`.
El bloque es configurable entre 1 byte y 1 MiB; por defecto, 64 KiB. La lectura de
red y la relectura local son incrementales y nunca acumulan el archivo completo.
También existen buffers internos del transporte; un transporte inyectado es
responsable de no entregar bloques gigantes desde su propia implementación.

La descarga rechaza clientes configurados con TLS desactivado. Mantiene la política
de orígenes existente: HTTP sin cifrado solo es posible si el llamador autoriza
expresamente un origen HTTP; TLS se verifica para HTTPS. No se implementa validación
de DNS/IP contra SSRF. Redirecciones automáticas desactivadas; 3xx y 206 se rechazan.
Los timeouts de HTTPX no representan un plazo global máximo de descarga.

Se solicita `Accept-Encoding: identity` y se rechaza cualquier Content-Encoding
distinto de identity. No se descomprime ni transforma el contenido. Se valida
Content-Length si existe y se cuentan siempre los bytes efectivos. Se rechazan
cabeceras inválidas, cuerpos truncados o mayores de lo declarado y excesos del
límite, incluso sin Content-Length. Un corte de red informado por HTTPX es un fallo.
Sin tamaño declarado o hash externo no puede detectarse un truncamiento que el
servidor presente como un final normal de la respuesta.

## Directorio, nombres y publicación sin sobrescritura

El llamador debe preparar un directorio de staging existente, dedicado y con
permisos que impidan modificaciones por usuarios no confiables. Se resuelve su
ruta y se rechazan enlaces simbólicos y junctions en sus componentes.
El nombre es un único componente ASCII portable de hasta 100 caracteres: comienza
con letra o dígito y continúa con letras, dígitos, puntos, guiones o guiones bajos.
Se rechazan separadores, nombres de dispositivos Windows, puntos finales y ADS.
No se usa el nombre de la URL ni Content-Disposition.

1. Se crea exclusivamente un temporal aleatorio `.suadc-*.tmp` en ese directorio.
2. Se escribe por bloques, verificando el resultado de cada escritura y calculando
   SHA-256 de los bytes entregados correctamente al archivo.
3. Se ejecutan flush y fsync, se relee el archivo por bloques, y se contrastan tamaño
   y SHA-256 reales de esa relectura con lo escrito. No basta comparar metadatos.
4. Se cierran archivo y respuesta antes de publicar mediante `os.link(temporal, destino)`.
   La creación del enlace duro falla si el destino existe, incluso si fue creado
   por otro proceso después de comprobar inicialmente su ausencia.
5. Se elimina el nombre temporal; el destino sigue apuntando al archivo completo.

No se usa `replace`, ni una copia con sobrescritura, ni un fallback menos seguro.
Si el sistema de archivos no admite enlaces duros, falla sin publicar. En sistemas
locales compatibles, la aparición del nombre final es atómica y no expone contenido
parcial. Temporal y destino pertenecen al mismo sistema de archivos.

La garantía depende de las semánticas de enlaces del sistema de archivos; debe
revisarse para volúmenes de red. No se garantiza durabilidad del nombre ante caída
eléctrica (no se sincroniza el directorio), inmutabilidad posterior ni protección
frente a un actor que pueda sustituir directorios/temporales durante la operación.
Las comprobaciones de rutas no sustituyen permisos de acceso adecuados: existe
una ventana entre comprobación y uso. La API no debe usarse sobre directorios
modificables por adversarios. Un cierre forzado del proceso puede dejar temporales
o un destino completo sin informe retornado. No hay una transacción con catálogo.

## Informe técnico, errores y limpieza

`InformeDescarga` contiene origen (solo esquema/host/puerto), fecha UTC del resultado,
estado, bytes almacenados, tamaño declarado cuando estuvo disponible, SHA-256 local,
ruta publicada, código HTTP y posible tipo de error y temporal restante. No conserva
ruta remota, consulta, credenciales, cabeceras ni cuerpo de error. El informe se
devuelve en memoria: no se implementa un catálogo ni un archivo de metadatos.

En errores de red/disco/publicación se lanza `ErrorDescargaArchivo`, subclase de
`ErrorTransporteHTTP`, con su informe `FALLIDA`. Su hash es None y no hay ruta
publicada. En fallos, el contador registra escrituras aceptadas antes del error,
no una garantía de persistencia; los bytes se eliminan normalmente con el temporal.
Errores de configuración/autorización se propagan como ValueError/TypeError.
Una interrupción KeyboardInterrupt/SystemExit se propaga después de intentar limpiar.

La limpieza intenta eliminar únicamente el temporal propio. Si falla, se informa
su ruta en `temporal_restante` para gestión explícita. Si el destino ya fue publicado,
el resultado sigue siendo `COMPLETA`, con el temporal residual indicado: ambos nombres
pueden apuntar al mismo archivo. No modificar ese temporal; solo retirar su nombre.
Ante interrupciones propagadas, un fallo de limpieza se añade como nota a la excepción.
No se incorpora limpieza automática de residuos de ejecuciones anteriores.
Las causas originales de excepciones pueden incluir información sensible; no registrar
trazas indiscriminadamente. La implementación no emite logs ni persiste credenciales.

## Alcance real de integridad

El hash retornado se calcula releyendo bytes del archivo después de flush/fsync;
comprueba que esa lectura coincide con los bytes escritos y el tamaño recibido.
La relectura puede servirse desde la caché del sistema operativo: no es una auditoría
del medio físico ni una prueba de conservación futura. Un archivo vacío es válido
si la transferencia finaliza sin discrepancias; se calcula su SHA-256 real.

`informe.como_descarga()` permite construir `Descarga.COMPLETA` solo para éxitos.
Al asociarla a `ResultadoRecurso`, su integridad permanece pendiente y el recurso
queda `DESCARGADO`, nunca confirmado automáticamente. La asociación con el recurso
correcto corresponde al llamador, pues el informe omite URLs sensibles.

El contrato `Integridad` exige hash esperado y procedencia para un hash observado;
un hash local por sí solo no cumple esa condición. Por eso el SHA-256 local se
mantiene en el informe técnico: no se inventa un hash externo ni se declara una
integridad científica. No se compara todavía con checksums confiables del proveedor.

## Pruebas y pendientes

La suite cubre éxito, vacío, más de 1 MiB, límite exacto y excedido, longitudes
incorrectas, interrupciones, errores de escritura/fsync, corrupción simulada en
relectura, destino existente y concurrente, publicación no soportada, 206, compresión,
errores HTTP y timeout, rutas inseguras y residuos de limpieza. Usa MockTransport
y directorios efímeros, con permisos heredados para compatibilidad con Windows.

Pendientes: política de evidencia externa, validación científica, almacenamiento
definitivo, catálogo duradero, recuperación tras cierre forzado, reintentos,
reanudación, autenticación institucional y conectores. Ninguno se implementa aquí.
