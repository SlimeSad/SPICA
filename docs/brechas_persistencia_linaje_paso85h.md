# PASO 85-H — Brechas de persistencia, linaje y recuperación

Este documento complementa el [contrato](contrato_trazabilidad_cierre_paso85h.md)
y el [piloto](piloto_cierre_ejecucion_paso85h.md). Conserva el alcance histórico de
las [brechas 85-G](brechas_integracion_paso85g.md) y la
[auditoría de arquitectura 85-F](auditoria_arquitectura_integral_paso85f.md).

## 1. Cambios de alcance demostrables

G02/G04 quedan cubiertas parcialmente para **un proceso confiable y el perfil
sintético fijo**: identidad declarada de ejecución/evaluación/entrada, enlace con
activo/catalogación/resultados y evidencia de cierre se cotejan en memoria.
No se crea coordinación de identidades, historia persistente, FK entre bases o
un repositorio de linaje. G07 continúa abierta para apagados y pérdida del proceso.

Se corrige la pérdida de prefijos JSON y resultados QA ya emitidos ante excepción.
Un informe parcial puede conservar evidencia útil sin declararse científicamente
apto. Una captura anterior al cierre se compara con la proyección posterior.
Los originales temporales se comprueban físicamente antes de borrarse; sus bytes
ya no pueden verificarse al cerrar. El sello de traza no sustituye al original.

## 2. Hallazgos y tratamiento

| ID / gravedad en el alcance actual | Hallazgo | Tratamiento / pendiente |
|---|---|---|
| H85-01 — Media, corregida | Pérdida de JSON parcial al fallar exportación | Prefijo acotado retenido por lote; no aceptación ficticia |
| H85-02 — Media, corregida | Pérdida de resultados emitidos si tuple(qa) lanzaba excepción | Acumulación progresiva y retención en finally junto a informes reales |
| H85-03 — Media, corregida | Cierre sin relación explícita de manejadores liberados | Registro después de __exit__, contraste adquiridos/liberados y estado de limpieza |
| H85-04 — Media, cubierta en memoria | Evidencia dependía del informe sin una representación canónica final | Captura previa y traza acotada cotejada con informe y control separado |
| H85-05 — Alta si se atribuye durabilidad, abierta | Terminación del proceso pierde traza/controles locales | Persistencia y recuperación requieren un incremento autorizado propio |
| H85-06 — Alta si se atribuye autenticidad, abierta | Un emisor puede fabricar un informe coherente y recalcular hashes | Ninguna promoción de confianza; no importador/autocertificación de trazas ajenas |
| H85-07 — Media, abierta | Fallo antes del retorno de un componente puede ocultar detalles internos | Conservar evidencia realmente recibida, fase y causa; no inventar bytes o etapas no observadas |
| H85-08 — Media, abierta | Cancelación cooperativa y limpieza no resisten terminación forzada | Documentar ausencia de cierre garantizado; no implementar recuperación automática |
| H85-09 — Media, corregida | Error del adaptador después de publicar comunica ID sin devolver el activo completo | Capturar ese ID antes del cierre y conservar error/fase/intentos; SHA observado desconocido permanece ausente |
| H85-10 — Media, corregida | Un resumen QA declarado podría contradecir los nativos/JSON | Cotejar configuración, reglas únicas, conteos, procedencia y contexto, además de la huella |
| H85-11 — Alta en el contrato experimental, corregida en la reanudación | CONCLUIDA podía coexistir con QA INCOMPLETA o recorrido/filas contradictorios | Cotejar estados, EOF, cardinalidad de filas y límites efectivos; regresiones de metadatos contradictorios |
| H85-12 — Alta en el contrato experimental, corregida en la reanudación | Un lector sin EOF/COMPATIBLE podía acompañar una cadena completa | Exigir cierre efectivo de ambas lecturas, conteos y bytes coherentes |
| H85-13 — Alta en el contrato experimental, corregida en la reanudación | Descarga PARCIAL, fase no final o RAW inconsistente podían pasar por huellas coincidentes | Exigir estados operativos terminales pertinentes y ausencia de evidencia contradictoria |

Las gravedades condicionales no convierten limitaciones declaradas en defectos
de los contratos estables. No se ha identificado necesidad de refactorización
extensa para este incremento. El cierre sigue siendo auxiliar de checkout.

## 3. Requisitos antes de persistencia futura

| Área pendiente | Decisión y evidencia necesarias antes de implementarla |
|---|---|
| Registro durable de ejecución | Ubicación autorizada separada de RAW, formato/versiones, política de publicación exclusiva, autorización y responsables |
| Recuperación tras interrupciones | Estados recuperables, fronteras de confirmación, detección de huérfanos, tratamiento de resultados parciales; jamás borrar originales para reparar |
| Integridad tras reinicios | Retener bytes/evidencias necesarias y controles de referencia confiables; cotejar contenido físico y metadatos después de reabrir |
| Coordinación de IDs | Espacios de nombres, identidad de ejecución/evaluación/reproducción, duplicación/reintento y concurrencia; igualdad de SHA no une observaciones |
| Datos derivados | Contrato científico, método/versión, unidades y aplicabilidad aprobadas, enlace a originales y restricciones heredadas; JSON QA0 no se convierte en derivado científico |
| Retención de evidencia | Qué originales, documentos, reglas, exportaciones, diagnósticos y controles se conservan; privacidad, volumen, plazos y eliminación autorizada |
| Respaldo/restauración | Procedimiento verificable para bytes y SQLite, consistencia, alcance temporal, copias independientes y ensayo de restauración |
| Confianza/autenticidad | Custodio, procedencia independiente, identidad del emisor, controles anclados fuera del mismo expediente; no basta el SHA autocontenido |
| Transacciones y concurrencia | Modelo explícito de escritor secuencial o coordinación; límites entre filesystem/RAW/catálogo científico/ejecución, sin prometer atomicidad global |
| Escalabilidad | Medición de RAM/tiempo, lotes acotados y referenciación; no resolver volumen perdiendo restricciones o controles físicos |
| Importación de expedientes | Esquema estricto y lector acotado, versiones, cotejo con fuentes y política de confianza propia; esta API no importa trazas de terceros |

Nada de esta tabla está implementado en el PASO 85-H. SQLite temporal, fsync,
dataclasses congeladas y hash de un JSON no resuelven por sí solos esos requisitos.

## 4. Límites científicos e institucionales

Las 29 [brechas PNDA](brechas_reconciliadas_pnda_paso84i.md) mantienen sus IDs y
estados: **2 resueltas, 17 parciales, 8 pendientes y 2 contradicciones**, 27 abiertas.
Este incremento no introduce evidencia institucional nueva ni resuelve ninguna.
No se acceden originales o manifiestos para revisar ese conteo documental.

No hay identificador de adquisición documental, autenticación institucional,
aprobación QA1, GIS operativo o uso del CSV real. El primer /query INGEMMET sigue
NO AUTORIZADO. HORA, UBIGEO y PP de la fixture se mantienen literales. Ningún estado
de ejecución, coincidencia o validación contractual habilita ciencia.

## 5. Propuesta para el siguiente incremento

Después de la revisión humana, especificar una única política de retención y
recuperación experimental, con un caso sintético y sus condiciones de autorización,
antes de crear tablas, archivos de trazas u otro almacenamiento. Decidir qué
evidencia debe sobrevivir y cuál puede reproducirse; separar registro de ejecución,
originales RAW, catálogo documental y derivados. Mantener explícito el anclaje de
confianza y las restricciones en cada frontera.

No es necesario crear ahora infraestructura distribuida, PKI, scheduler,
autenticación institucional, ciencia, GIS o IA. La persistencia necesita encargo
y auditoría propios. No se continúa automáticamente al siguiente incremento.
