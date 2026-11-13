# PASO 85-M — Auditoría de continuidad arquitectónica integral

Fecha: **2026-11-13, America/Lima**. Rama **feature/suadc-http**, HEAD
**d8742fc**, Git inicialmente limpio. El commit consolida los tres documentos
del 85-L. Esta auditoría conserva todos los archivos anteriores y crea únicamente
este informe, la [matriz diseño/implementación](matriz_diseno_implementacion_paso85m.md)
y la [hoja de ruta de continuidad](hoja_ruta_continuidad_arquitectonica_paso85m.md).

**Decisión vigente del usuario:** continuar fortaleciendo la arquitectura integral.
85-M no la da por terminada, no ratifica el inicio científico ni inicia Etapa 86.
La opción C recomendada en 85-L permanece como antecedente condicionado, no como
aprobación. No se reescribe ese informe para cambiar su historia.

## 1. Alcance, método y límites de evidencia

Se revisan Git, documentación, contratos y fuentes/pruebas como texto y AST con
Python de .venv y -B. No se importan módulos de SPICA, ejecutan pruebas/pilotos,
abren almacenes o consultan evidencias privadas. Se consultaron los **64 commits
alcanzables desde HEAD**, sin equiparar un commit a una aprobación formal.
La búsqueda adicional en historiales locales accesibles no aportó los originales
de ERS/actas. No se buscó en unidades externas o carpetas de datos del usuario.

Fuentes principales: [auditoría 85-F](auditoria_arquitectura_integral_paso85f.md),
[33 conexiones](matriz_dependencias_integracion_paso85f.md),
[ruta 85-F](hoja_ruta_arquitectonica_paso85f.md), contratos/pilotos/brechas de
85-G/H/I/J/K, y los tres informes de 85-L:
[custodia](arquitectura_custodia_independiente_paso85l.md),
[amenazas](modelo_amenazas_dominio_fallo_paso85l.md) y
[madurez](evaluacion_madurez_arquitectonica_paso85l.md).
Se complementan con los contratos de adquisición, RAW, catálogo, tiempo,
interoperabilidad, QA, metadatos y sus pruebas localizadas en la matriz nueva.

Se separan tres clases de evidencia: **inspección estática actual**, **ensayo
histórico documentado** y **propuesta sin implementar**. La última suite completa
documentada es la del 85-K: **1884 aprobadas, cero fallos/errores/omitidas**.
No se vuelve a ejecutar ni se informa como resultado de 85-M. Número de pruebas
no mide por sí solo madurez, cobertura o conformidad con la ERS no disponible.

## 2. Diseño Integral: qué puede recuperarse y qué no

| Fuente requerida | Disponibilidad y estado documental | Consecuencia de trazabilidad |
|---|---|---|
| ERS-SPICA v1.0 y revisiones, Etapa 1 | **F: documento no localizado** en árbol ni historial local consultado | No se reconstruyen texto, identificadores, prioridades o congelación de la ERS |
| Apartados originales 1.1–1.8 | Referidos por el encargo; títulos y contenido original **no disponibles** | No corresponden automáticamente a A–H de este encargo ni a números PASO |
| Actas B1/DA1, aprobaciones con reservas | **F: soporte no localizado** | No asignar A/B a un requisito por estar codificado o tener dictamen APTO |
| Matriz maestra H0/FUT, reservas y G0 | **F: clasificación formal no localizada** | Conservar estados desconocidos. No transformar P1 en H0, P3 en FUT ni resultados sintéticos en cierre de G0 |
| Protocolo de Desarrollo Acelerado original | **F: documento formal no localizado**; criterios suministrados en el encargo actual | Auditar reutilización, bloques, contradicciones, responsables y aceptación conforme al alcance actual; no certificar un protocolo ausente |
| MD-01/02/03 | Campos suministrados en el PASO 51 y contratos locales implementados/documentados | Correspondencia estructural verificable, no reconstrucción de toda la ERS o acta de aprobación |
| Contratos técnicos y matrices locales | Disponibles: adquisición, RAW, catálogo, tiempo, interoperabilidad, QA y C/R/H/M de 85-F | Trazabilidad local comprobable por código/pruebas; no reemplazan la matriz maestra original |
| Diseño de procesamiento/análisis/resultados/IA/administración global | Hay decisiones locales y candidatos parciales; no expediente global original recuperado | No puede certificarse cumplimiento integral; distinguir ausencia de código observado de requisito original no evaluable |
| Encargo 85-M y decisiones expresas del usuario | Disponibles y vinculantes para esta tarea | Continuidad modular/offline, preservación, IA local principal y APIs opcionales, sin ciencia ni pagos ahora |

«No localizado» no significa inexistente fuera del repositorio. El encargo alude
a expedientes históricos: su disponibilidad pendiente debe resolverse mediante
aportación explícita de las versiones/actas pertinentes, no accediendo a archivos
privados. La única aparición previa de FUT localizada es también un nodo de
diagrama del 85-F; no constituye una clasificación formal de requisitos FUT.
No se halló respaldo para reclasificar H0, FUT o las reservas de G0.

Estados documentales A–F y estados de software se mantienen en ejes distintos
en la matriz. Ninguna aprobación histórica cambia en 85-M. El alcance actual
no permite certificar qué fracción del Diseño Integral original está cumplida.

## 3. Reconstrucción histórica útil por responsabilidad

Los grupos siguientes enlazan hitos verificables, no enumeran todos los commits
ni inventan pasos intermedios. «Registrado» significa consolidado en Git;
«probado» remite al informe/pruebas del alcance, no a aprobación de Etapa 1.

| Bloque / anclas Git | Objetivo y componentes/contratos desarrollados | Dependencias, decisiones y correcciones documentadas | Evidencia / estado actual y pendiente |
|---|---|---|---|
| Inicio y transporte: 43584b2 → 3288484 | Entorno/main mínimo; Fuente/Solicitud/Resultado, GET, streaming y reintentos | Biblioteca estándar, HTTPX; fases de transferencia/integridad separadas, TLS/orígenes, tamaño real, temporales y SHA, GET idempotente | Núcleo/HTTP/descargas/reintentos con pruebas; sin plataforma global de tareas. El primer contrato registrado ya incorpora el refuerzo de estados; no se inventa un número PASO inicial |
| RAW, MD y puente: c807173 → 88c1cce | AlmacenRAW/CatalogoRAW, ProyectoCientifico/ObjetoCientifico/ActivoRAW, compatibilidad v2 y HTTP→RAW | Identidad distinta de ruta/hash; originales y adquisiciones idénticas se preservan. Correcciones de integridad/rutas y reconocimiento de esquemas | Pruebas RAW/MD/HTTPRAW; uso privado secuencial, sin atomicidad global ni ciclo de vida de derivados |
| Catálogo, planificación, PNDA y configuración: 9d89217 → 4199e67 | Catálogo científico v1, revisiones/disponibilidad, PlanConsulta, conector fijo PNDA, ConfiguracionRAW | Plan declarativo, fuente/recurso documentados; sondeos y apertura con efectos. [SUADC-01/02](correcciones_auditoria_altas.md) corrigen exposición de errores y reconocimiento SQLite | Pruebas de catálogo/plan/conector/configuración. Acceso institucional acotado por procedimiento; no ejecutor universal o permisos globales |
| Evidencias, formatos y lectura: 1730ef7 → b4c2c38 | Registro documental, CSV/XLSX, tiempo UTC, lector streaming, consultas locales y perfil representacional | No normalizar tiempo ambiguo; límites/EOF reales y conservación de literales; tamaño/hash y revisión documental distintos | Pruebas e informes locales; perfil de 16 campos SENAMHI, no modelo de observación ambiental general |
| QA y contratos científicos: f72b587 → fb34162 | QA0, catálogo declarativo de reglas, referencias, límites exclusivamente sintéticos y aplicabilidad | 22 definiciones, resultados por campo, estados/restricciones; aprobación documental no autoriza ejecución | Contratos y evaluador de fixtures probados; no núcleo científico institucional integrado. 744×30=22320 es antecedente del piloto, no filas leídas aquí |
| Ampliación de adquisición: 6e1a0ec → f3dac77 | Auditoría multiinstitucional, IngestorManual y decisión de readquisición | Recepción manual no HTTP; recomendación sin red; mantener evidencia de procedencia | Manual integrado a RAW en fixtures, readquisición pura; no automatización de planes o conectores ANA/OEFA |
| INGEMMET/ArcGIS y vectorial: f168e57 → 00fc44b | Expediente, inspección de metadatos, FeatureSet, paginación/precisión y simulación | WIP 3a635cb corregido por límites JSON extenso/validación offline; separar servidores/productos/licencias y metadatos de entidades | Pruebas sintéticas y auditorías 82/83; primer /query sigue NO AUTORIZADO, sin GIS operativo |
| Interoperabilidad: 41332a0 → e6e8bc5 | Snapshots espaciales/temporales, aptitud, adaptadores y piloto local 84-C | Desconocidos y CRS por ámbito preservados; adaptación documental no realiza asociación GIS | Pruebas aisladas/integradas de DTO y antecedente local específico; no geoprocesamiento o normalización universal |
| Confianza y documentación: 5b73fcc → 496976d | Auditoría XLSX/DOCX, inspector OOXML, reconciliación, afirmaciones y cotejo de evidencia | WIP 85a8c22 corregido; hipervínculos pasivos, compatibilidad y extracciones acotadas; literal/edición/autoría/aplicabilidad distintos | Inspección/vinculación probadas, 29 brechas conservadas; no aprobación científica por COINCIDE |
| Ciclo estructural QA: 3535a47 → 720c0f9 | Inventario/versionado, JSON QA, consumidor y conciliación entre lotes | Contexto y restricciones incluidos; coincidencia no equivale a una nueva observación ni a ciencia | 85-A–E: integración estructural; exportación científica general y almacenamiento de preparados/derivados pendientes |
| Arquitectura y unión vertical: 13744ab → a044b49 | 85-F inventaría 25 componentes/33 conexiones; 85-G crea arnés; 85-H conserva prefijos y coteja cierre/enlaces | WIP c259b62 consolidado con comprobación de QA/EOF/estados contradictorios. Se reutilizan motores, no otro cliente/QA | Históricos: 1745 en G y 1791 en cierre H. M18 se demuestra en perfil fijo; no núcleo transversal para toda la aplicación |
| Conservación y custodia: 2efc9f7 → d8742fc | Diseño I, conservador/codec/85001 J, respaldo/restauración K, diseño de custodia/madurez L | Confirmación lógica, controles locales y copias independientes; portabilidad TEMP y dominios/autoridad de escritura distintos | 1841 en J y 1884 en K; I/L documentales. Evidencia de una ejecución sintética, no RAW completo o custodia operativa |

La historia puede contener autorización de un procedimiento concreto sin aprobar
todo un subsistema. Los pilotos reales de PNDA y configuración son antecedentes
documentales: no se vuelven a abrir ni se verifica su disponibilidad actual.
Un WIP no se presenta como cierre; se indican las correcciones/consolidación
posteriores. Los recuentos de suites no se suman entre pasos o subcasos.

## 4. Arquitectura realmente observada

Inventario estático: **100 módulos src, 9 herramientas de checkout y 56 archivos
test_ con 1884 IDs únicos**. requirements declara únicamente `httpx==0.28.1` como
dependencia directa. Main solo imprime el mensaje de inicio. El historial
`13744ab..HEAD -- src/spica` no contiene cambios: desde 85-F se añadieron o
reforzaron herramientas y documentos, no un paquete global de gestión/ejecución.

```text
HTTP/streaming/reintentos ─┐
manual local ─────────────┴→ HTTPRAW/manual → RAW + catálogo de activos
                                               ↓ recuperación/lectura
catálogo científico → PlanConsulta         CSV → QA0 → JSON → consumo → conciliación
                       [no ejecuta]               ↑
metadatos/observaciones/ArcGIS → snapshots → aptitud [sin operación GIS]

arnés fijo 85-G → traza/cotejo 85-H → conservación 85-J → respaldo 85-K
                                            [TEMP, una ejecución por respaldo]
```

Son cadenas reales en sus perfiles, no todas las flechas de un Diseño Integral.
Faltan servicios transversales de contexto/proyecto/configuración de aplicación,
usuario/permisos, preparación/derivados y ejecución reutilizable con autorización
y presupuesto comunes. Los DTO de proyecto o resultado no constituyen esos
servicios. La matriz IM01–IM28 detalla archivos, interfaces y responsabilidades.

Las 33 conexiones se evalúan individualmente en la matriz: **28 D acotadas,
4 P y 1 O** en el inventario heredado. No son 28 integraciones completas. M18
pasa de P a D solo para la ruta HTTP simulada/perfil 85-G; la vía manual completa
y otros perfiles siguen sin esa demostración. M03/M16/M26/M32 permanecen previstas;
M33 es opcional. Las conexiones nuevas G→H→J→K se describen aparte, sin renumerar
las M ni confundir los 16 subsistemas agregados de 85-L con 25 componentes de F.

## 5. Garantías conservadas y fronteras abiertas

Implementado/probado en alcances delimitados: separación de fases, preservación
de originales, IDs distintos de hash/ruta, streaming/verificación técnica,
lectores acotados, revisiones de catálogo, QA0 con restricciones, reproducción,
errores/estados parciales, cotejo y recuperación de evidencia recibida, y copias
TEMP independientes. Son base reutilizable; no requieren reescritura por estilo.

Fronteras que no se deben borrar al ampliar:

- RAW.verificar/recuperar/diagnosticar y abrir una configuración pueden escribir
  eventos o sondas. No son lecturas administrativas inocuas.
- Plan PREPARADA, recomendación de readquisición, aptitud, firma/hash o regla
  APROBADA no conceden permiso de operación ni científico.
- Una revisión de metadatos no es versión del contenido; igualdad SHA no fusiona
  adquisiciones, ejecuciones o muestras; alias project_id/proyecto_id requieren
  mapeo, no otra entidad por conveniencia.
- Informe CONCLUIDA, conservación CONSERVADA y recuperación verificada describen
  dimensiones distintas. Los fallos históricos no se promueven al restaurar.
- SQLite científico v1, RAW v1/v2 y extensión de evidencia 85001 tienen contratos
  distintos. El lector v1 rechaza 85001; no se mezclan tablas ni migran en silencio.
- Archivo, conjunto de datos, observación, resultado QA y derivado científico
  son responsabilidades distintas. No basta renombrar RegistroQA o ActivoRAW.

## 6. Brechas/contradicciones: hechos frente a ampliaciones propuestas

| ID local 85-M | Evidencia y tipo de hallazgo | Consecuencia / prioridad |
|---|---|---|
| AM01 | ERS/actas/matriz formal no disponibles; hecho de disponibilidad, no inexistencia del diseño | P1 de trazabilidad antes de afirmar conformidad; recuperar fuentes o ratificar alcance local acotado |
| AM02 | ProyectoCientifico y ObjetoCientifico residen en RAW; no contexto de aplicación/usuario o ciclo de proyecto común | P1 estructural: componer IDs/configuración/responsabilidades sin duplicar MD |
| AM03 | ContratoEjecucion85G es perfil fijo de herramienta; PlanConsulta/ResultadoDecision no ejecutan ni gestionan autorización/efectos comunes | P1 estructural: frontera de operación y contexto reutilizable; no un segundo orquestador general |
| AM04 | ObservacionLocal/RegistroQA especializados; unidad declarada y aplicabilidad existen, dimensión física/modelo común de medición/relaciones no | P1 antes de nuevas familias de datos: perfil mínimo/adaptación explícitos, no conversión o universalización de TEMP/HR/PP |
| AM05 | ResultadoCientifico es descriptor vinculado a RegistroQA; no preparado/derivado con ciclo de vida, exportación y linaje transversales | P1 al abrir ese flujo: contrato/publicación no destructiva, sin guardar derivados como originales |
| AM06 | J/K solo TEMP/codec de informe conocido; _validar_informe liga padre histórico a TEMP del lector; 85001 no es v1 | P1 antes de custodia portable/operativa; incompatibilidad del uso ampliado demostrada estáticamente, no fallo nuevo del perfil vigente |
| AM07 | Cotas locales, materialización de informes/lotes y cancelación cooperativa; no reserva/cuota RSS/plazo forzoso general | P1 para composición de presupuestos; medición/optimización por escala P2. No prometer memoria constante |
| AM08 | Imports diferidos/ciclos acotados y helpers privados, más codec cerrado de checkout; no import src→herramientas explícito encontrado | P2 dentro del perfil, P1 al extraer frontera pública: evitar inversión de dependencia o nuevo contrato duplicado |
| AM09 | Referencias, marcadores y archivos bajo autoridad local, sin atomicidad FS+SQL o custodia/retención general | P1 antes de datos únicos; mantener límites actuales. Riesgo residual, no prueba de ataque ocurrido |
| AM10 | Cliente genérico permite HTTP y get sin TLS; saneamiento es acotado, no IAM/sandbox de usuario hostil | P1 de perfil de seguridad para flujos comunes; P0 solo si se ejecuta/declara una garantía incompatible |
| AM11 | Recomendación C de 85-L vs decisión expresa de continuidad del encargo 85-M | Se conserva como propuesta histórica no ratificada; la directiva vigente prevalece, sin reclasificar aprobaciones |
| AM12 | Guía RAW afirma «No se ha inicializado…», pero [CSV 69](csv_streaming.md) y [84-C](integracion_local_pnda_paso84c.md) documentan activo/almacén usado | P2 documental: frase de alcance temporal ambiguo, no diagnóstico del estado actual. No se cambia la guía ni se abren datos para resolverlo aquí |

AM11 no es un bug de software. AM12 se acredita por dos textos de épocas/alcances
distintos; no demuestra pérdida o inexistencia de RAW hoy. Los estados históricos
deben conservar fecha/alcance en una futura guía vigente. No se detecta un defecto
crítico nuevo reproducido: no se ejecutó código. Las ausencias transversales y
compatibilidades sí están sustentadas por inspección, no son gustos de estilo.

### Dependencias y contratos que conviene preservar

La matriz de F describe dos grupos de ciclos con imports diferidos en transporte
y almacenamiento/catálogo/integración. El código src no cambió desde ese inventario;
no se reinterpreta su análisis como ausencia universal de ciclos. El muestreo AST
actual de imports explícitos añade dependencias entre herramientas, incluido
G↔H con retorno diferido; no hay import src→herramientas explícito. No se ejecutaron
importaciones para probar todos los órdenes. Existe evidencia histórica de esos
órdenes en H, no garantía para una API futura.

Nombres iguales no bastan para declarar duplicación semántica: IdentidadRecurso
de readquisición e interoperabilidad describen contextos distintos; Respaldo
documental tampoco es el backup físico. Fuente/procedencia/registros ya existentes
deben adaptarse con correspondencias explícitas antes de crear otra familia DTO.
La promoción de herramientas a API exige contrato/cierre/versionado, sin hacer
que src dependa del arnés o de helpers de tests.

## 7. Protocolo de desarrollo y decisiones preservadas

| Criterio suministrado en el encargo | Evidencia actual / pendiente |
|---|---|
| Reutilizar decisiones | Contratos y fronteras conservados; no nuevos clientes, QA o catálogos por esta auditoría |
| Agrupar por dependencias | Hoja de ruta agrupa contexto/operación, información, derivados y conservación; no un paso por DTO |
| Auditoría por bloques | Historia por responsabilidad, IM01–IM28 y las 33 M; categorías/documentación comparables explícitamente |
| Control de contradicciones | AM01–AM12 y puertas de aceptación; no corregir falsificando evidencia o estados |
| Matriz maestra | Matriz local trazable disponible; matriz oficial/ERS/aprobaciones no recuperadas, por tanto cumplimiento global no evaluable |
| Pendientes y responsables | Propietarios funcionales por componente en matriz/ruta; no asignar personas o aprobadores que no consten |
| Separar diseño/aceptación | Propuestas, implementación, pruebas históricas y autorización diferenciadas; no congelar ERS o cerrar G0 |

Modularidad, adquisición/almacenamiento/procesamiento/análisis separados,
originales, procedencia, calidad, seguridad, contratos versionados y restricciones
permanecen. Offline y equipos modestos no equivalen a prohibir toda materialización,
sino a cotas explícitas y medición pertinente. IA híbrida futura: apoyo local
principal y APIs externas opcionales, sin alterar ciencia determinista ni exigir
GPU/nube; freemium no reduce calidad esencial ni obliga a pagos ahora.

## 8. Verificación y dictamen

El cierre de verificaciones y Git se registra en la hoja de ruta tras revisar
las tres piezas, sus tablas, fuentes, versiones e identificadores. Solo se crean
Markdown; no se repite la suite/pip check ni se añaden pruebas ejecutables.

No hubo conexiones/GET, descargas, instalaciones, cambios de contratos/código,
acceso a RAW/staging/SQLite operativos, CSV o documentos institucionales privados,
migraciones, ciencia, IA/GIS operativo, commits o push. La ausencia de escrituras
nuestras se basa en no acceder, no en una comprobación física de datos cerrados.
Las 29 brechas PNDA siguen 2 resueltas, 17 parciales, 8 pendientes y 2 contradicciones;
no se modifica ese expediente ni se autoriza /query INGEMMET.

**Dictamen: APTO CON RESTRICCIONES como expediente de continuidad arquitectónica.**
La comparación con el Diseño Integral original sigue parcialmente no evaluable
por disponibilidad documental. Hay infraestructura reutilizable e integración
sintética real, y responsabilidades transversales pendientes. No se declara
completa la arquitectura, no se selecciona algoritmo ni se inicia otro paso.
