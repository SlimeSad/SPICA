# PASO 85-G — Alcance demostrado y brechas de integración restantes

Fecha: **2026-11-11, America/Lima**. Base **13744ab**, feature/suadc-http.
Se complementan el [contrato mínimo](contrato_ejecucion_integrada_paso85g.md) y
el [informe del piloto](piloto_integracion_vertical_paso85g.md); no se reescribe
la [matriz de 33 conexiones](matriz_dependencias_integracion_paso85f.md).
Las prioridades se aplican al siguiente incremento, sin implementar nada más.

## 1. Qué se completa realmente

El código nuevo se limita a un arnés y sus DTO de checkout. La cadena positiva
ejecuta ClienteHTTP/descargas, AdaptadorHTTPRAW, AlmacenRAW/CatalogoRAW,
CatalogoCientifico, recuperación, LectorCSV, EvaluadorNivel0, exportador oficial,
consumidor y conciliador. Únicamente el backend de red se simula con MockTransport.
No se presenta un GET simulado como solicitud institucional efectivamente enviada.

M18 pasa de propuesta a **integración experimental demostrada en el perfil fijo
85-G**: un archivo ficticio, dos filas, RAW y catálogo efímeros, dos reproducciones
del mismo activo y una traza de ejecución. M09–M11/M13/M17/M27–M29 se reutilizan
y comprueban dentro de esa cadena. No se modifica el estado histórico de la matriz
85-F, ni se eleva la madurez de toda la plataforma por ese único caso.

H02 se cubre parcialmente mediante contrato/estado/presupuesto/cancelación y
errores por fase. H03 obtiene evidencia vertical acotada. H04 se aplica al perfil
simulado mediante URL HTTPS fija y flag TLS: **TLS real sigue sin comprobarse**.
El núcleo, las 22 reglas y JSON 0.1.0 permanecen intactos.

## 2. Hallazgos de implementación y correcciones acotadas

| Hallazgo | Tratamiento en el código/prueba nuevos | Alcance de la evidencia |
|---|---|---|
| Fases de descarga/QA no cubrían el ciclo completo | EstadoEjecucion85G e InformeEjecucion85G componen estados/informes existentes | No unifica todos los enums ni crea un sistema de tareas |
| Una referencia de catálogo compatible por nombre no bastaba | Se registra y consulta el recurso; se compara entidad completa, revisión e identidad fuente/producto/recurso con RAW/contrato | Vínculo comprobado por esta llamada, no FK global entre bases |
| Un informe marcado válido podría perder restricciones al cambiar de componente | Comparación entre conteos nativos y consumidos, además de validación real/revalidación del consumidor/conciliador | Omisión de restricciones rechaza; una pérdida simulada en el enlace impide conclusión |
| Presupuesto del consumidor no equivale a rechazo | VALIDACION_INCOMPLETA se propaga como ejecución INCOMPLETA, conservando el informe real | No habilita salida aceptada parcial o conciliación satisfactoria |
| Validación temporal resolvía innecesariamente la referencia a una raíz prohibida | Se eliminó esa resolución del auxiliar; rechazo léxico antes de inspección y prueba específica contra Path.resolve de esa referencia | Sin cambio a seguridad/contratos RAW estables; no se inspeccionan originales operativos |
| Prueba inicial esperaba otra excepción de dataclasses.replace | Se exige TypeError real de Python 3.15 al cambiar un campo init=False | Error de fixture, no se alteró un contrato para ocultarlo |
| Guardia temporal no contemplaba executable=None en subprocess Windows | Extracción del ejecutable implícito antes de aplicar la lista permitida | Corrección de instrumentación externa al repositorio; no ampliar acceso a red o datos |

Los fallos adversariales no se corrigen borrando archivos anteriores o reintentando
la operación. Los únicos árboles eliminados son temporales creados por cada ensayo.
Un fallo de componente conserva fase/estado y no se presenta como éxito global.

## 3. Impedimentos que no justifican cambiar contratos estables ahora

| ID / prioridad | Evidencia y límite | Condición necesaria / propuesta posterior |
|---|---|---|
| G01 — P1 | El auxiliar no ejecuta PlanConsulta ni ResultadoDecision; M03/M16 continúan previstas | Si se necesita ejecutar una propuesta, especificar autorización concreta y adaptación de selectores. No conectar PREPARADA o RECOMENDAR_NUEVA directamente a HTTP |
| G02 — P1 | El ID de ejecución no tiene diario persistente ni coordinación global; repetir la llamada crea otro temporal/activo | Definir control explícito de reproducciones y vínculo a entrada/contexto en el próximo caso. No prometer exactamente una ejecución o idempotencia global |
| G03 — P1 | adquirir básico no produce adquisicion_id/evidencia documental independiente; estos campos QA siguen None | Para adquisición institucional, usar el procedimiento documentado autorizado y evidencia real. Nunca suplir el ID con ejecucion_id o inventar capacidad HTTP verificada |
| G04 — P1 | Conexión catálogo↔activo es un enlace validado en memoria y evidencia textual técnica; no existe FK entre bases | Antes de persistencia de flujos, especificar una referencia mínima/versión y consulta compatible. No añadir tablas o un repositorio general de linaje en este paso |
| G05 — P1 | Lectura de archivo y cuerpo QA están especializados en el perfil de 16 columnas y TEMP/HR/PP | Adaptador/perfil por producto cuando exista caso de uso. No fabricar columnas o unidades para otras disciplinas |
| G06 — P1 | No se crea resultado científico o almacenamiento/exportación de derivados | Revisar contratos científicos existentes, unidades/medición, evidencia de método y restricciones antes de un experimento; no relabelar JSON QA0 |
| G07 — P2 | Temporales se destruyen al cerrar; la traza queda en el objeto devuelto. No hay recuperación después de apagado | Una política futura de registro/residuos debe ser explícita y separada de RAW. No declarar durabilidad por usar SQLite y fsync |
| G08 — P2 | Cancelación cooperativa por fases, HTTP/CSV/QA/exportación; no interrumpe instantáneamente toda copia RAW | Si se necesita un plazo/cancelación de extremo a extremo, definir sus puntos de control y tratamiento de interrupciones antes de ampliar |
| G09 — P2 | Se materializan dos conjuntos de resultados y sus JSON, con presupuestos lógicos; no cuota RSS/disco global | Medir escala y fragmentar lotes con contexto explícito si el caso lo requiere; no optimizar eliminando controles físicos |
| G10 — P2 / P0 si se pretende otro modelo | RAW privado secuencial y dos SQLite sin atomicidad global/aislamiento de escritor hostil | Conservar ese modelo. Concurrencia, respaldo/restauración y garantías frente a apagados necesitan procedimiento y pruebas específicos |
| G11 — P1 documental | ERS global y arquitectura aprobada de Etapa 1 no recuperadas; encargo 85-G autoriza solo este ensayo | Mantener trazabilidad de decisiones y buscar/validar la referencia bajo alcance propio; no registrar una aprobación retrospectiva |
| G12 — P3 | UI, GIS operativo e IA no participan en la cadena | Permanecen opcionales y posteriores; no son prerrequisitos para cerrar una integración estructural sintética |

No se encontró una incompatibilidad mayor que exigiera detener el tramo sintético
o refactorizar paquetes. Las limitaciones anteriores impiden extrapolar el éxito
a integración institucional, ejecución científica o plataforma completa.

## 4. Bloqueos científicos y jurídicos conservados

P0 **condicional al uso propuesto**, no defecto nuevo de los motores: no ejecutar
ciencia o usar/publicar datos institucionales sin evidencia, identidad/integridad,
aplicabilidad y autorización correspondientes. JSON válido, SHA local, coincidencia
de lote y COMPROBACION_SATISFECHA no satisfacen esas condiciones por sí solos.

Las [29 brechas PNDA](brechas_reconciliadas_pnda_paso84i.md) conservan sus IDs y
estados: **2 resueltas documentalmente, 17 parciales, 8 pendientes y 2 contradicciones**;
27 abiertas. No se usaron el CSV PNDA, XLSX/DOCX institucionales o sus manifiestos.
HORA/UBIGEO/PP permanecen literales ficticios, sin normalización o conversiones.
El primer /query INGEMMET sigue no autorizado; no se ejecutó ni simuló un recurso
institucional concreto como si hubiera sido adquirido.

El origen de la fixture y el control esperado son responsabilidad del ensayo.
Existe comprobación física de **los bytes ficticios almacenados**, no autenticidad
del autor, equivalencia editorial o metrología. Las restricciones científicas no
se borran al cambiar de componente; las anotaciones QA se mantienen en JSON y
lotes, y las limitaciones globales de ejecución se conservan en el informe auxiliar.
No se inyectan campos nuevos al JSON 0.1.0 para simular permisos.

## 5. Recomendación para el PASO 85-H

Proponer, después de revisión, **un cierre de identidad y trazabilidad de ejecución
estructural** sobre el mismo perfil sintético, sin ciencia ni nuevas adquisiciones:

1. Revisar las responsabilidades del contrato 85-G y su correspondencia ejecución /
   evaluación / reproducción / entrada / adquisición / activo. Seleccionar un
   único caso que realmente necesite conservar el enlace después de cerrar.
2. Evaluar si basta una proyección acotada del informe existente para el expediente
   técnico de una ejecución. Definir referencias, versiones, restricciones y
   resultados fallidos/incompletos antes de crear persistencia nueva. No duplicar
   catálogo, RAW o JSON QA0, ni convertir ese expediente en permiso.
3. Comprobar repetición correcta con mismo activo/control y la separación de otra
   adquisición/evaluación. La igualdad de valores no debe producir equivalencia
   falsa; conflictos y faltantes deben sobrevivir cierre/lectura si se conserva
   un expediente. Elegir la mínima interfaz nueva solo ante necesidad demostrada.
4. Mantener presupuestos, rutas temporales, rechazo de red y pruebas de fallos.
   Si no se necesita persistencia, cerrar G02/G04 documentalmente para ese alcance
   y evitar otro incremento de almacenamiento por anticipación.

Criterio de aceptación propuesto: identidad/linaje y restricciones conservados
sin depender de un booleano aportado; diagnóstico de contradicciones/repeticiones;
revisión de cierre/incompletitud, regresiones aprobadas y cero efectos operativos.
No construir cola distribuida, servicio de confianza o autenticación criptográfica.

Los módulos científicos seguirán esperando su expediente metodológico y una
instrucción específica. No hace falta resolver UI, IA o todos los productos para
formular luego un experimento sintético; tampoco basta este piloto para autorizarlo.

## 6. Dictamen

**APTO CON RESTRICCIONES para la integración vertical estructural sintética
descrita.** El dictamen se apoya en los resultados finales de verificación
registrados en el informe del piloto. No certifica producción, adquisición real,
validez científica, seguridad contra código hostil o recuperación tras apagados.
No se avanza automáticamente al PASO 85-H. Se espera auditoría.
