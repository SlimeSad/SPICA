# PASO 85-G — Contrato mínimo de ejecución estructural experimental

Fecha: **2026-11-11, America/Lima**. Base: **13744ab**, rama feature/suadc-http,
Git inicialmente limpio. El commit registra los tres documentos del 85-F.
Se conservan la [auditoría](auditoria_arquitectura_integral_paso85f.md), su
[matriz](matriz_dependencias_integracion_paso85f.md) y la
[hoja de ruta](hoja_ruta_arquitectonica_paso85f.md). No se modifica ningún contrato
estable, regla, consumidor o conciliador.

## 1. Alcance y necesidad del auxiliar

Se crea únicamente un arnés de checkout:
[herramientas/piloto_integracion_85g.py](../herramientas/piloto_integracion_85g.py).
No se añade un paquete de ejecución global, scheduler, CLI automática, adaptador
institucional o almacenamiento de derivados. Requiere src y la raíz del checkout
en PYTHONPATH. Las [pruebas](../tests/test_integracion_vertical_85g.py) componen
motores existentes y usan datos ficticios pequeños.

Los contratos anteriores cubren partes de la ejecución: FaseHTTPRAW/ResultadoHTTPRAW,
EstadoIncorporacion/ActivoRAW, InformeLecturaCSV, InformeQA, ContextoExportacionQA,
InformeConsumoQA e InformeConciliacionQA. Ninguno representa por sí solo una tarea
planificada y su ejecución efectiva a través de todas esas fases. PlanConsulta
es declarativo y no ejecutable; un enum de descarga no describe una evaluación QA.
Reutilizarlos como permiso o éxito global sería incorrecto.

La carencia se limita a **tres DTO y un enum auxiliares**, versión 0.1.0:
Presupuesto85G, ContratoEjecucion85G, InformeEjecucion85G y EstadoEjecucion85G.
No se crea una segunda familia de resultados QA. El informe
compone directamente los contratos existentes. La función ejecutar_piloto_85g
tiene flujo fijo y no interpreta un plan, nombre de método, expresión o callback.

## 2. Solicitud planificada y presupuesto

| Campo de ContratoEjecucion85G | Significado y límite |
|---|---|
| ejecucion_id | Identidad declarada de esta llamada/piloto, coordinada por el responsable; no unicidad global ni ID de adquisición |
| proyecto_id, objeto_id | Identidades lógicas sintéticas para DeclaracionRAW; distintas de ruta, hash y asset_id |
| entrada_id | Identidad declarada del archivo sintético. Cada resultado usa entrada_id:numero_registro como entrada de fila |
| evaluacion_id | Contexto de reproducibilidad QA compartido por las dos pasadas del mismo activo |
| tarea_ref | Referencia declarada al ensayo. No se consume ni se afirma ejecutado un PlanConsulta |
| producto_id, recurso_id | Identidades originales de la fixture, propagadas al catálogo y RAW |
| tamano_esperado, sha256_esperado | Control explícito suministrado por el responsable de la fixture, contrastado contra bytes físicamente incorporados |
| presupuesto | Presupuesto85G, positivo y acotado; no cuota de memoria/disco del SO |
| configuracion | ConfiguracionQA existente; selección de reglas, variables y metadatos. Por defecto las 22 reglas y TEMP/HR/PP |
| estado, version, naturaleza, dependencias | PLANIFICADA, 0.1.0, simulacion_sintetica_offline y conexiones seleccionadas; no configurables por el constructor |

Las identidades son ASCII de 1–64 caracteres, sin rutas o expresiones. La función
acepta exclusivamente este contrato, bytes y un Event opcional de cancelación.
No recibe rutas, clientes, transportes externos, conexiones SQLite o funciones de
usuario. El cuerpo debe declararse sintético por un llamador confiable; el código
no puede probar criptográficamente su historia o impedir que Python hostil lo falsifique.

| Presupuesto por ejecución | Predeterminado | Tope configurable |
|---|---:|---:|
| Bytes de entrada | 65536 | 1048576 |
| Filas de datos por reproducción | 8 | 32 |
| Resultados por reproducción/lote | 256 | 256 |
| Bytes UTF-8 JSON por lote | 1048576 | 4194304 |

Se realizan exactamente dos reproducciones. El arnés conserva resultados/documentos
acotados en memoria; **no promete RAM constante ni límite RSS**. El límite CSV
incluye holgura para encabezado/EOF, mientras LimitesQA limita filas de datos.
Igualar el límite de resultados sin comprobar EOF sigue produciendo incompletitud
conforme al motor existente. Los presupuestos son técnicos, no umbrales científicos.

## 3. Estados de ejecución y alcance de los resultados

| Estado auxiliar | Evidencia y significado |
|---|---|
| PLANIFICADA | Existe un contrato validado; todavía no se ejecutó transporte ni almacenamiento |
| INICIADA | Entrada en una fase registrada en la traza; no implica éxito de las siguientes |
| CONCLUIDA | Cadena estructural cerrada, ambas evaluaciones completas en su alcance, consumo válido y coincidencia reproducible; temporales eliminados |
| INCOMPLETA | Límite o evaluación/lectura incompleta: se conservan informes reales y resultados emitidos, sin presentarlos como cadena satisfactoria |
| FALLIDA | Discrepancia de control/identidad, rechazo contractual, pérdida de restricciones, conflicto inesperado o error de componente/cierre |
| CANCELADA | Event activado en una frontera cooperativa o cancelación HTTP reconocida; no es una descarga confirmada ni un resultado científico |

El contrato original conserva PLANIFICADA; la función devuelve otro objeto con
estado de ejecución y traza ordenada. No se muta la solicitud para fingir que un
plan fue ejecutado. INICIADA aparece como evento mientras trabaja la llamada
síncrona; no hay servicio de consulta de tareas en curso o registro persistente.

Resultado estructural y ejecución son dimensiones distintas: InformeQA puede
estar COMPLETA con muchos NO_EVALUADO. No se han ejecutado las condiciones
documentalmente desconocidas. El piloto puede concluir técnicamente conservando
esa limitación; no produce ResultadoCientifico. ejecucion_cientifica y
autorizacion_operativa permanecen False y no son argumentos del constructor.
bool(contrato) y bool(informe) se rechazan: consultar explícitamente el estado
tampoco concede permiso.

InformeEjecucion85G conserva contrato, estado/fase, diagnósticos fijos, traza,
el activo_id conocido incluso en un error parcial, ResultadoHTTPRAW,
RegistroRecurso, resultados nativos, InformeQA y lecturas,
consumos, conciliación y número de solicitudes **simuladas**. Conserva también
la referencia histórica del temporal y si fue eliminado. Las rutas del resultado
HTTP/RAW dejan de existir al cerrar: **no son entregables persistidos**.
Los campos voluminosos y la ruta temporal se omiten del repr del informe; los
objetos completos siguen accesibles explícitamente para auditar la fixture.

## 4. Conexiones P1 seleccionadas y responsabilidades

No se intenta resolver las 33 conexiones del 85-F. Se cubren M09/M10/M11/M13/M17,
la unión experimental M18 y M27/M28/M29. Las columnas de esta tabla describen
llamadas reales, no compatibilidad supuesta de parámetros.

| Emisor → receptor / conexión | Contrato / entrada → salida | Identidad y restricciones / error / efecto / aceptación |
|---|---|---|
| MockTransport → transporte/HTTPRAW, M09–M11 | Bytes de fixture → InformeDescarga/ResultadoHTTPRAW y ActivoRAW | Red simulada; cliente, descarga, staging, copia/hash y recuperación reales. Un solo intento. Rechazo o error impide QA; SHA/tamaño esperado deben coincidir |
| RAW ↔ catálogo de activos, M13 | DeclaracionRAW → contenido SHA y activo | Proyecto/objeto/recurso conservados; sin transacción global. Error o corrupción no se repara borrando originales |
| Activo → catálogo científico → snapshot, M18 | FuenteCatalogo/ProductoCatalogo/RecursoCatalogo → RegistroRecurso leído | Base temporal distinta; entidad completa y revisión 1 contrastadas, evidencia técnica enlaza asset_id. No se registra capacidad institucional verificada |
| Recuperación → lector → motor, M17/M18 | Ruta RAW físicamente comprobada → RegistroCSV/RegistroQA → ResultadoQA/InformeQA | ProcedenciaQA conserva fuente/recurso/asset/SHA; cuerpo y encabezado del perfil deben ser admitidos. Cierre incompleto detiene exportación; nueva recuperación comprueba original después |
| QA → exportador, M27 | ResultadoQA + ContextoExportacionQA → JSON 0.1.0 | Identidad de archivo/fila/evaluación, configuración e incertidumbres explícitas; restricciones oficiales por resultado. Sin serialización asdict improvisada |
| JSON → consumidor, M28 | Tupla acotada → InformeConsumoQA | Aceptación atómica, rechazo/incompletitud explícitos. Conteos nativos de restricciones se contrastan con los consumidos; una pérdida es fallo de integración |
| Dos consumos → conciliador, M29 | LoteQA A/B → InformeConciliacionQA | Revalidación real, documentos completos y restricciones conservados; coincidencia exigida solo para reproducciones del mismo activo/contexto |

La prueba positiva ejecuta los componentes internos; solo la frontera de red es
un doble. Las pruebas adversariales inyectan fallos puntuales de disco, SQLite,
lectura o enlace y no sustituyen toda la cadena por un éxito fabricado.

## 5. Identidad, procedencia y correspondencia de reproducciones

Fuente fija **SPICA-SINTETICA / fixture-85g**. El dominio .invalid y la URL de
fixture son destinos ficticios del MockTransport, nunca endpoints institucionales.
La referencia de procedencia es urn:spica:85g:simulacion y su método declara
MockTransport_sin_red. Se usa adquirir básico, no adquirir_documentado: no se
persiste una supuesta evidencia HTTP_DIRECTO verificada. adquisicion_id y documento
de ProcedenciaQA permanecen **None**. ejecucion_id no se inserta para suplirlos.

El asset_id real de prueba y su SHA enlazan el resultado de adquisición, el
registro de catálogo, la procedencia QA y los JSON. La relación de proyecto/objeto
se conserva en DeclaracionRAW y el contrato; no se atribuye al catálogo científico
un campo de proyecto que no tiene. No hay FK entre ambas bases: el enlace lo
comprueba esta llamada y queda en su informe, no como índice global persistido.

A y B ejecutan dos veces EvaluadorNivel0 y LectorCSV contra **el mismo activo y
snapshot**, con idéntico contexto de reproducibilidad. No representan dos
observaciones ambientales ni dos adquisiciones independientes. Su correspondencia
se establece por el control del arnés y las recuperaciones físicas, no solo por
tener valores iguales en JSON. Otra evaluación con ID diferente no se alinea
automáticamente. Otra adquisición requiere nueva identidad de evaluación; reutilizar
el mismo contexto con una procedencia distinta puede generar conflicto legítimo.

## 6. Seguridad, almacenamiento y cierre

El cliente se construye internamente con MockTransport cerrado, origen HTTPS
ficticio, verificar_tls=True, timeouts existentes, un intento y las políticas
heredadas sin redirección, compresión HTTP o 206. El arnés no permite sustituir
ese backend. **No se acredita un handshake TLS, certificado o servidor HTTPS**.
Un futuro flujo real deberá comprobar de nuevo esquema, TLS, origen, límites,
timeouts, redirecciones, cancelación y autorización; no se cambia el cliente global.

Se valida TEMP/TMP antes de crear un directorio exclusivo: se rechazan raíces
operativas conocidas, código, controles internos, UNC y enlaces/junctions. Las
referencias protegidas se comparan léxicamente, sin resolverlas ni sondearlas.
Los únicos directorios de entrada RAW pertenecen al temporal de esta llamada.
No se aceptan rutas del llamador ni se abre ConfiguracionRAW operativo.

RAW nuevo crea su esquema de prueba usando la inicialización existente, que
evoluciona una base **vacía y temporal** a v2; su inspección genera referencias
de esquema en memoria. No se ejecuta una migración sobre un almacén preexistente
u operativo ni se cambia ese mecanismo para forzar la integración. La suite
anterior conserva también sus pruebas de esquemas/migración en fixtures aisladas.
Esta distinción no debe sustituirse por la afirmación de que ninguna función
interna denominada migración fue llamada.

ExitStack y TemporaryDirectory cierran cliente/SQLite y eliminan únicamente el
árbol propio. Los fallos se devuelven con fase y códigos fijos, sin conservar
mensajes arbitrarios de excepción, credenciales o cuerpos. Un fallo de limpieza
impide declarar conclusión y deja revisión explícita. KeyboardInterrupt/SystemExit
se propagan después de la limpieza de los contextos. Terminación forzada del
proceso/apagado no garantiza traza final, limpieza ni recuperación automática.

Cancelación cooperativa antes de fases, en HTTP/CSV/QA y exportación; no interrumpe
instantáneamente todas las copias RAW o llamadas síncronas. No hay reintentos de
la operación global, Range, reanudación, paralelismo o historia entre llamadas.
Identidades, raíces y código dependen de un proceso confiable; dataclasses y
hashes no aíslan un intérprete hostil ni certifican origen.

Resultados y verificaciones realmente ejecutadas:
[piloto](piloto_integracion_vertical_paso85g.md). Pendientes y condiciones del
siguiente incremento: [brechas de integración](brechas_integracion_paso85g.md).
