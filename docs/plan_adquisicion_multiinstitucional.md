# PASO 78: plan de tres incrementos de adquisición

**Propuesta para revisión; no implementada ni autorizada para operaciones reales.**
Se apoya en la [auditoría](auditoria_adquisicion_multiinstitucional.md) y la
[matriz de capacidades](matriz_capacidades_adquisicion.md). No se proponen nuevos
endpoints ni credenciales. Las reglas científicas Nivel 1 continúan deshabilitadas.

## Selección del próximo incremento

Recomendación: **flujo común de ingesta manual documentada de un archivo público
institucional, recibido de forma autorizada**, con pruebas únicamente sintéticas
en su primera implementación. Es una composición del almacén y catálogo actuales,
no un nuevo motor de copia ni un conector institucional ficticio.

| Alternativa | Reutilización/evidencia | Complejidad o riesgo pendiente | Decisión |
| --- | --- | --- | --- |
| Ingesta manual documentada | Incorporación física y metadatos comunes ya disponibles; no depende de red/auth | Evidencia HTTP actual no sirve como recibo manual; se debe revisar el vínculo documental | Primero: permite nuevas variables y formatos sin fingir filtros, estaciones o APIs |
| Decisión previa de readquisición pública | Recursos, revisiones, activos e integridad existentes; producto PNDA conocido | No hay relación automática completa de frescura/versionado remoto; evitar bloquear adquisiciones legítimas | Segundo: reduce repeticiones injustificadas y conserva trazabilidad |
| Ampliar inmediatamente el conector SENAMHI a CSV | Hay un antecedente real y adaptador reusable | El método actual solo autoriza XLSX; permisos/tamaño/selección deben revisarse. No resuelve diversidad institucional | Posponer como ampliación explícita; una descarga antigua no es permiso permanente |
| Conector API de ANA/OEFA/INGEMMET | Contratos generales de selectores y GET | Especificación institucional y mecanismo desconocidos; autenticación no implementada | No programar sin expediente; no seleccionar por una API supuesta |
| Integración espacial | Necesidad ambiental contextual y conservación opaca de archivos | Producto, CRS, mecanismo, licencia y formato todavía no comprobados | Tercero: preparar primero un expediente concreto de INGEMMET, con barrera de implementación |

La entrega manual no demuestra autoría por sí sola ni el permiso de una estación
privada. Se comienza por archivos públicos con documentación revisable; fuentes
privadas solo podrán incorporarse después de definir alcance de autorización,
confidencialidad y acceso a metadatos/contenido. No se implementa autenticación
ficticia ni se considera una casilla de configuración como prueba de permiso.

## Incremento 1 — Ingesta manual documentada sin atribuir HTTP

**Problema concreto:** `AlmacenRAW.incorporar` conserva archivos de una entrada
autorizada, pero el flujo de evidencia vinculado a adquisición existente requiere
URL/fecha HTTP y declara HTTP_DIRECTO. No es un recibo manual multiinstitucional.

Entrada futura: archivo regular en raíz local autorizada, declaración de proyecto,
objeto, fuente/producto/recurso y documentación pública revisada de la entrega y
sus restricciones. Conservar desconocidos, identificadores originales y formato
declarado; no inventar fechas de observación para archivos no temporales.

Reutilizar `DeclaracionRAW`, `AlmacenRAW.incorporar`, comprobación/recuperación
física y el registro documental del catálogo. Separar el recibo de entrega de
una comprobación de autenticidad o autorización. El vínculo persistente entre
recibo/revisión y activo debe especificarse y aprobarse antes de implementar:
no usar campos HTTP con valores ficticios ni crear un segundo almacén/SQLite.
Priorizar el catálogo/diario existente; cualquier extensión incompatible del RAW
queda fuera del incremento hasta su revisión explícita.

Salida esperada: activo preservado y comprobado, recibo documental explícitamente
manual y resultado con evidencia/restricciones; ninguna capacidad HTTP verificada.

Aceptación offline:

- Bytes copiados/releídos y SHA-256 coincidentes en directorios temporales; original
  conservado y sin sobrescritura de contenidos previos.
- Reapertura del vínculo documental y activo sin inventar URL, fecha HTTP,
  revisión institucional, estación, variable, unidad o modalidad.
- Dos entregas legítimas de bytes idénticos conservan sus identidades; no se
  confunden deduplicación física y deduplicación de eventos.
- Rechazo de evidencia de otro producto, referencias sensibles, entrada externa,
  archivo alterado, exceso de tamaño y fallo de persistencia; fallos parciales
  informados sin promover activos ni borrar originales.
- Ninguna lectura de rutas operativas, conexión externa, migración o QA/QC científico.

Punto de revisión: acordar primero el recibo y su persistencia. Después autorizar
una implementación limitada y sintética. La primera prueba real requerirá archivo,
fuente, permiso, raíces, límites y procedimiento aprobados por separado.

## Incremento 2 — Decisión de readquisición antes del GET

**Problema concreto:** catálogo documental idempotente y contenido deduplicado no
evitan una segunda descarga. La misma URL puede cambiar, y bytes iguales pueden
corresponder a adquisiciones distintas que deben conservarse.

Reutilizar identidad fuente/producto/recurso, revisiones documentales y consultas
existentes por activo/adquisición. Definir una decisión revisable previa a red,
aportando explícitamente la adquisición anterior pertinente si no existe una
consulta pública acotada por recurso. No acceder a detalles privados del catálogo
RAW para construir un ejecutor paralelo ni añadir una consulta ilimitada como
solución de escala.

Resultados propuestos del procedimiento: reutilizar una referencia comprobada,
solicitar revisión por evidencia/frescura insuficiente, o proponer una adquisición
con motivo explícito. Ningún resultado concede por sí mismo permiso para GET.
Debe poder justificarse otra adquisición idéntica; no bloquearla ni eliminarla
globalmente por hash o URL. Una comprobación física sobre el almacén real también
necesita autorización para escribir su resultado de verificación.

Aceptación offline:

- Recurso/revisión idénticos no producen automáticamente una llamada HTTP.
- Cambio de revisión, recurso inconsistente, licencia/acceso cambiantes o
  evidencia insuficiente llevan a revisión o propuesta justificada.
- Ausencia de ETag/Last-Modified no se interpreta como ausencia de cambios;
  hash local no demuestra frescura remota.
- Si se aprueba un nuevo evento con bytes idénticos, conserva ID y documento propios.
- Pruebas con MockTransport y RAW efímero verifican ausencia/número de GET y
  conservación de activos, sin ampliar permisos o políticas HTTP.

No introducir en este incremento HEAD, Range, caché HTTP, headers de autenticación,
If-None-Match/If-Modified-Since ni soporte de 304: el cliente no expone actualmente
esa interfaz/semántica. Una futura negociación condicional requiere especificación
y revisión separadas; no se deduce que ya exista por recibir cabeceras en GET.

## Incremento 3 — Expediente de un producto espacial institucional

Seleccionar **un producto de contexto espacial de INGEMMET** únicamente después
de obtener documentación institucional verificable. La elección de la institución
es provisional por la necesidad de GIS; no se afirma que exista un servicio,
formato, licencia o API determinados. Si no se obtiene evidencia suficiente, el
entregable se cierra como expediente incompleto y no genera conector.

Entregables concretos:

1. Identificación de institución, producto, recurso/capa, versión y fuente oficial;
   URL exacta observada/documentada, nunca construida por analogía.
2. Contrato de acceso: descarga, servicio, API, portal o entrega manual; permiso,
   autenticación, restricciones, límites, paginación y actualización si corresponden.
3. Contrato del recurso: formato/paquete, piezas requeridas, identificadores,
   CRS, orden de ejes, unidades, extensión, escala/resolución y vigencia declarados.
   Lo desconocido permanece desconocido; no se transforma ni valida geometría aquí.
4. Fixture sintética de metadatos/respuesta coherente con la documentación obtenida
   y especificación de pruebas offline. No usar un servicio real como prueba unitaria.
5. Decisión de viabilidad para reutilizar HTTP/RAW y el flujo manual; lista exacta
   de capacidades faltantes. Solo entonces proponer el primer adaptador acotado.

No se instala una biblioteca GIS, inventa un cliente OGC ni generaliza el conector
SENAMHI cambiando su URL. Un archivo espacial podría conservarse como original
opaco mediante los flujos existentes/autorizados; eso no constituye soporte GIS.
ANA y OEFA seguirán el mismo procedimiento de selección de producto y evidencia,
sin atribuirles el acceso o semántica de INGEMMET/SENAMHI.

Punto de revisión: la búsqueda externa y cualquier comprobación pública puntual
pertenecen a una etapa posterior autorizada; están prohibidas en el PASO 78.
Tampoco se inicia el conector real después del expediente sin revisión del usuario.

## Condiciones comunes para los tres incrementos

Mantener un único transporte y almacén, uso secuencial, TLS/orígenes/límites y
publicación exclusiva, evidencia por recurso y autorización explícita de operaciones.
Conservar el original, su procedencia y desconocidos. Ningún mecanismo transforma
unidades/zonas, inventa catálogos o activa QA/QC Nivel 1. Las aprobaciones científicas
y autorizaciones de ejecución siguen fuera de los planes de adquisición.

El plan no reserva operaciones, inicia trabajo futuro, concede permisos, promete
disponibilidad institucional ni sustituye especificaciones reales. Requiere la
revisión del usuario antes de implementar cualquiera de los incrementos.
