# PASO 85-D — Consumo offline de exportaciones QA/QC no confiables

Fecha: **2026-11-11, America/Lima**. Contrato experimental de consumo **0.1.0**.
**APTO CON RESTRICCIONES**, para auditoría offline; no autoriza ciencia ni el
PASO 85-E. Resultados: [piloto y verificaciones](piloto_consumo_qaqc_paso85d.md).

## Arquitectura y revisión inicial

Git inicial limpio, rama **feature/suadc-http**, HEAD **ce2bf49**,
«SUADC: exportacion trazable QAQC nivel 0»; PASO 85-C consolidado.
Se revisaron [exportador](../src/spica/calidad/exportacion.py),
[pruebas 85-C](../tests/test_exportacion_qaqc_85c.py),
[contrato 85-C](contrato_exportacion_qaqc_paso85c.md),
[piloto 85-C](piloto_exportacion_qaqc_paso85c.md),
[modelos QA](../src/spica/calidad/modelos.py),
[motor](../src/spica/calidad/motor.py),
[restricciones 85-B](../src/spica/calidad/restricciones.py),
[su política](versionado_restricciones_qaqc_paso85b.md), modelos de procedencia
y las rutas de serialización/lectura existentes.

No existía un consumidor de este esquema. Se reutiliza el
[lector JSON acotado](../src/spica/adquisicion/_json_acotado.py), compartido por
inspección ArcGIS y validación vectorial: usa json.loads de biblioteca estándar,
presupuesto léxico previo, detección de claves duplicadas y recorrido posterior.
No se invocan servicios GIS ni los otros consumidores. Las rutas de catálogo
persistente se revisaron como contexto, sin abrir bases ni reutilizar su E/S.

Módulo nuevo: [calidad/consumo.py](../src/spica/calidad/consumo.py), importación
experimental explícita. No cambia calidad/__init__.py, exportador, restricciones,
modelos, reglas o consumidores anteriores. No agrega dependencias o migraciones.

Flujo: bytes/texto explícitos → límites del lote → lector JSON acotado → esquema
cerrado y tipos → contratos nativos de datos conocidos → coherencia → reexportación
propia para contraste → identidades/restricciones/duplicados → InformeConsumoQA.
No se llama al evaluador QA, inspectores, cotejador documental, motor científico,
HTTP, RAW, archivos o SQLite. No hay un segundo motor de reglas/restricciones.

## Modelo de confianza

Todo JSON recibido es no confiable. Un resultado positivo significa únicamente
**coherencia contractual dentro del perfil aceptado**. Se comprueban sintaxis,
estructura, tipos, versiones, identidad reproducible y la parte de las
restricciones que permite contrastar la política cerrada 85-B.

Contexto y procedencia siguen declarados. No se acredita emisor, institución,
ejecución real de la regla, integridad física, equivalencia editorial, validez
científica o permiso. Un remitente puede fabricar un paquete completamente
coherente y recalcular hashes: **SHA-256 no es firma ni autentica el origen**.
Las discrepancias entre dos paquetes pueden detectarse; no se ofrece protección
contra falsificación de origen ni unicidad global sin coordinación externa.

El estado documental VERIFICADO, si se aporta de forma estructuralmente coherente,
se conserva como una declaración recibida; el consumidor no realiza su verificación
independiente. No se reemplaza por una afirmación de autenticidad propia.

## Entrada, API y esquema aceptado

```python
from spica.calidad.consumo import consumir_exportaciones, LimitesConsumoQA

# texto_85c es una cadena JSON 0.1.0 recibida explícitamente.
informe = consumir_exportaciones(texto_85c)
# Para un lote: tupla explícita de documentos individuales, no archivo o generador.
informe_lote = consumir_exportaciones((texto_85c, texto_85c))
```

Se acepta bytes UTF-8 estrictos, str o una tupla de esos documentos. Una raíz
JSON es un objeto del esquema 85-C. No se introduce un contenedor JSON nuevo,
JSON Lines, rutas automáticas, listas Python o carga de archivos. La tupla es
solo el contenedor de transporte en memoria. Entrada/lote vacío se rechaza.

Las **13 claves** superiores del esquema 85-C son obligatorias y cerradas:
version_esquema, resultado_id, huella_contenido, naturaleza_identidad, contexto,
campos_objetivo, versiones, resultado, estado_evaluacion, detalle_diagnostico,
campos_objetivo_no_aportados, restricciones y limitaciones.
También se exigen claves exactas en los objetos anidados conocidos.

| Ubicación real | Valor admitido |
|---|---|
| version_esquema | 0.1.0 |
| versiones.contrato_qa y resultado.version_contrato | 1.0.0 |
| resultado.regla.version | 1.0.0 |
| versiones.evaluador y único par evaluador_nivel0 en resultado.parametros | 1.0.1 |
| versiones.restricciones | 1.0.0 |
| InformeConsumoQA.version_contrato | 0.1.0, versión independiente del informe de consumo |

85-C puede representar emisor desconocido/null y otras versiones semánticas de
descriptores. **Este consumidor admite un perfil más estrecho**, con las versiones
indicadas; null o una versión futura se rechazan, sin inferir ni migrar. No se
cambia retroactivamente la validez general del exportador ni sus pruebas.

Los decodificadores son tablas fijas del programa para dataclasses de datos QA,
procedencia, configuración y presupuestos ya existentes. No se resuelven clases
por un nombre del JSON. Los pares/listas recuperan sus tipos nativos mediante
validación explícita; no hay eval, exec, pickle o deserialización ejecutable.
Fechas documentales ISO se decodifican como datetime consciente; no se buscan
zonas ni se convierten fechas/HORA de observaciones.

No se coaccionan booleanos o strings a enteros, ni números a observaciones
textuales. Se rechazan float (incluso finitos), NaN/Infinity, enteros técnicos
fuera de ±(2^53−1), Unicode inválido y surrogate aislado, aun escapado. Strings
literales "NaN"/"Infinity" siguen siendo textos, sin aprobación numérica.
UTF-8 con BOM se rechaza en este perfil. No se normaliza Unicode ni se rellenan
ceros. URLs, rutas o instrucciones dentro de strings se tratan solo como datos.

## Límites antes y después del parser

| Presupuesto | Predeterminado | Tope configurable |
|---|---:|---:|
| Bytes por documento | 1048576 | 4194304 |
| Bytes por lote | 4194304 | 16777216 |
| Documentos/resultados recibidos | 256 | 1024 |
| Profundidad de contenedores JSON | 20 | 24 |
| Nodos por documento, incluidas claves | 20000 | 50000 |
| Nodos acumulados del lote | 200000 | 1000000 |
| Caracteres por string | 65536 | 65536 |
| Elementos por lista | 4096 | 4096 |
| Propiedades por objeto | 64 | 128 |
| Objetos por documento | 2048 | 8192 |
| Restricciones por documento | 32 | 128 |
| Restricciones acumuladas recibidas | 4096 | 16384 |

Todos positivos, enteros reales y acotados; bool no es un límite válido.
La cantidad de documentos y los bytes se comprueban antes de json.loads. En
str se comprueba longitud antes de codificar y tamaño UTF-8 después. El lector
compartido cuenta profundidad, elementos y nodos antes del parser; json.loads
valida toda la gramática y rechaza claves duplicadas también en objetos anidados.
Se cuentan nodos y objetos y se revisa Unicode/tipos tras el parseo.

IDs de contexto: patrón y máximo 128 del contrato 85-C; regla_id máximo 128 en
este perfil; resultado_id qa0- seguido de 64 hex minúsculas; huella 64 hex.
Otros identificadores originales conservan los límites nativos/textuales
acotados del esquema, sin inventar códigos institucionales.

El contraste propio usa el presupuesto máximo ya permitido por el exportador
(4 MiB, 50000 nodos, profundidad de conversión 24), separado del presupuesto
léxico de entrada: cuentan unidades diferentes. No se desactiva ningún límite
de entrada. No se ejecuta trabajo adicional después de agotar un presupuesto.
RecursionError/MemoryError se capturan como validación incompleta; no hay garantía
frente a terminación del proceso por el sistema operativo ni aislamiento de CPU.

## Coherencia, identidad y restricciones

Se reconstruyen únicamente contratos conocidos para contrastarlos con
exportar_resultado_json. Su salida propia es acotada; no se sustituye con ella
el documento recibido. Deben coincidir identidad, huella, versiones, campos
derivados, estado de evaluación, detalle, limitaciones y restricciones completas.

Se contrastan además los literales objetivo que estén presentes en el registro,
ID/ESTACION cuando ambos estén aportados, el estado incompleto ante estructura
incoherente y la pertenencia de regla/campo a la configuración declarada, cuando
existe. Son controles de consistencia, no reevaluación científica o de las reglas.
No se comprueba el mérito de toda descripción/diagnóstico recibido ni se afirma
que el descriptor fuera registrado y ejecutado realmente.

La política 85-B se obtiene indirectamente mediante el exportador, que llama su
función pura una sola vez. Las restricciones deben coincidir en **grupo, código,
tipo, operaciones, motivo y orden**. Omitidas, adulteradas, duplicadas o no
comprobables se rechazan; no se completan silenciosamente. Los documentos
aceptados se canonizan desde el **JSON recibido**, conservando su información,
no desde una reparación del contraste.

El resultado_id se contrasta con el algoritmo 85-C: contexto declarado completo,
entrada/posición, regla y versión, emisor, QA, política, esquema y campos objetivo.
No depende solo del contenido literal. Dentro de un lote se compara también el
registro completo asociado a cada (espacio, evaluación, escenario, entrada).
Reutilizar esa entrada con otro registro/posición se rechaza. Filas iguales con
identidades legítimas distintas se conservan; no son duplicados científicos.

Duplicado exacto significa **misma identidad y mismo JSON canónico completo**,
aunque difieran espacios/orden de claves. Política idempotente: se acepta una
vez, se cuentan las repeticiones y no se duplican restricciones ni diagnósticos.
Las repeticiones recibidas sí consumen presupuesto de trabajo. Misma identidad
con contenido distinto rechaza el lote, aunque ambos hashes fueran recalculados.
No se compara solo la huella para decidir igualdad ni se sobrescribe un resultado.
La caché existe solo durante la llamada, no entre lotes ni globalmente.

## Informe y aceptación atómica

| Estado | Significado y datos devueltos |
|---|---|
| CONTRATO_VALIDO_EN_ALCANCE | Todos los documentos superaron el perfil; entrega JSON canónicos únicos ordenados por resultado_id, conservando restricciones |
| CONTRATO_RECHAZADO | Se observó un error crítico; cero aceptados y sin documentos entregados |
| VALIDACION_INCOMPLETA | Un límite o recurso impidió terminar sin un error crítico ya demostrado; cero aceptados y sin documentos entregados |

Un error crítico prevalece sobre agotamiento posterior. No hay aceptación parcial
de un lote rechazado/incompleto. InformeConsumoQA es inmutable, con versión,
candidatos recibidos, únicos aceptados, duplicados exactos observados, etapas,
problemas por índice base uno, JSON aceptados, conteos de restricciones y límites
de confianza. «Recibidos» cuenta candidatos de transporte, aun si alguno no era
un diagnóstico válido; no inventa diagnósticos parseados.

comprobaciones_realizadas enumera etapas completadas para todos los documentos;
comprobaciones_no_realizadas incluye las no completadas para todo el lote y
las dimensiones siempre fuera de alcance. Los problemas explican rechazos;
un presupuesto incompleto no conserva marcas de etapas parciales como completas.
No se autentican instituciones, originales o contexto; no se reevalúan reglas,
validez científica, permisos, exhaustividad de metadatos o unicidad global.
No se devuelve un booleano global de confiabilidad o una autorización.

HORA, UBIGEO, PP, TEMP/HR y procedencia conservan las restricciones científicas
85-B, incluso en COMPROBACION_SATISFECHA. NO_EVALUADO e INCOMPLETA conservan
motivos, sin transformarse en aprobación. El esquema sigue siendo declarativo.

## Compatibilidad y condiciones futuras

No se modifica el exportador ni contratos estables. Importar consumo es una
elección explícita; no se integra al catálogo operativo o procesamiento científico.
Parámetros de límites mal tipados son errores del llamador (TypeError/ValueError);
datos recibidos inválidos o excesivos producen un informe controlado.
Los problemas no incluyen valores recibidos ni trazas con rutas/credenciales.
Los paquetes aceptados pueden contener información sensible declarada; no se
publican ni escriben automáticamente. Canonizar JSON no valida su procedencia.

Riesgos pendientes: remitente capaz de fabricar contenido coherente, coordinación
externa del espacio/ejecuciones, ausencia de memoria persistente entre lotes,
consumidor de un perfil estrecho y límites dentro de un proceso de confianza.
Antes de integrar, auditar políticas de conservación/contexto e idempotencia
entre lotes, privacidad, versiones y cualquier operación de persistencia. Nada
de ello activa usos científicos o cierra brechas documentales en este paso.
