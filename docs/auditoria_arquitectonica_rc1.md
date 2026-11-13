# RC1 — Auditoría del incremento de contextos comunes

Fecha: **2026-11-13, America/Lima**. Entorno de ejecución: Python **3.15.1**
de .venv. Base y HEAD inicial **ce4218b**, rama feature/suadc-http.

## 1. Recuperación y alcance autorizado

Se ejecutaron git status, git status --short, git branch --show-current,
git log -5 --oneline y git show --stat --oneline HEAD. Árbol inicial limpio;
85-M consolidado en ce4218b con sus tres documentos. Historial inicial:

```text
ce4218b SPICA: auditoria de continuidad arquitectonica paso 85-M
d8742fc SUADC: custodia y evaluacion de madurez arquitectonica paso 85-L
d3372a0 SUADC: respaldo y restauracion experimental de linaje paso 85-K
d7d7b8c SUADC: persistencia experimental y recuperacion verificable de linaje
2efc9f7 SUADC: arquitectura de persistencia y recuperacion de linaje
```

Se leyeron las tres piezas de 85-M, la matriz original de conexiones y los DTO,
consumidores y pruebas pertinentes. RC1 corresponde a la sección 3 de la
[hoja de ruta](hoja_ruta_continuidad_arquitectonica_paso85m.md): composición mínima
de contexto proyecto/objeto, entrada/versión/activo y operación/resultado, sin
otro motor, cliente, almacén o modelo MD paralelo. El encargo ratifica este
incremento local. No ratifica cierre arquitectónico ni inicio científico.

ERS original, actas B1/DA1 y matriz formal H0/FUT/G0 siguen sin estar disponibles
en las fuentes locales recuperadas en 85-M. No se inventan requisitos formales,
aprobaciones o conformidad integral. No se sobrescriben 85-F–85-M.

## 2. Decisión de composición y dependencias

Se crea spica.contextos por ser una responsabilidad transversal, fuera de
adquisición, QA o almacenamiento definitivo. Los cinco nuevos DTO son envolventes
pequeñas; no redefinen MD, Fuente, RecursoInteroperable, EvidenciaLocal,
ConfiguracionQA, LimitesQA, RestriccionQA, ResultadoQA o ContextoExportacionQA.
La [tabla de contratos](contrato_contexto_comun_rc1.md) justifica capacidad
reutilizada, ausencia y adaptación. Sus consumidores anteriores quedan intactos.

modelos depende de DTO existentes; relaciones depende de modelos; adaptadores_qa
depende de modelos y QA existente. Ningún módulo previo depende del paquete nuevo,
ni src importa herramientas/tests. No se añade ciclo que vuelva desde un módulo
previo hacia contextos. Las importaciones diferidas y ciclos previos descritos
en F/M no se refactorizan ni se declaran eliminados.

EstadoOperacion distingue declaración, planificación, inicio y terminales
estructurales; no sustituye estados de RAW/QA/plan ni agrega un ejecutor. Reutilizar
el enum G importando herramientas desde src sería incompatible con su condición
de arnés de checkout. Los estados nuevos están versionados dentro de RC1.

No se detectó necesidad de romper interfaces públicas previas, cambiar JSON QA,
migrar SQLite o usar datos institucionales. No se activó ninguna puerta que
requiera suspender esta implementación acotada o pedir aprobación de red/datos.

## 3. Hallazgos 85-M y prioridades conservadas

| Hallazgo | Prioridad heredada | Resultado de RC1 / pendiente |
|---|---|---|
| AM01, documentación original/actas | P1 de trazabilidad | Encargo local ratificado y referencias recuperadas; conformidad global con diseño original no evaluable |
| AM02, contexto de plataforma | P1 | Contexto e identidades compuestos; no gestor de proyectos, usuarios o ciclo completo |
| AM03, ejecución/permisos dispersos | P1 | Declaración, pertenencia, estados y referencia QA comunes; sin orquestador ni autorización de efectos. RC3 pendiente |
| AM04, perfiles/unidades/observaciones | P1 antes de familias nuevas | Se conserva RecursoInteroperable y perfil declarado; adaptación QA limitada. RC2 pendiente, sin conversiones |
| AM05, preparados/derivados | P1 al abrir ese flujo | No se amplía ResultadoCientifico ni almacenamiento; RC4 pendiente |
| AM06, conservación portable TEMP/codec | P1 antes de operativo | J/K y esquema 85001 intactos. RC1 no es serializable por ese codec ni prueba portabilidad |
| AM07, recursos | P1 composición / P2 medición | Reutiliza presupuesto QA y acota referencias. Sin presupuesto conjunto, reserva de disco o medición RSS/CPU |
| AM08, API/importaciones | P2 actual / P1 al promover API | Frontera nueva mínima; sin imports de herramientas/tests. Dos órdenes reales probados. No refactoriza auxiliares previos |
| AM09, custodia/consistencia | P1 antes de datos únicos | No abre o escribe almacenes; no mejora atomicidad FS+SQL, retención o custodia. RC5 pendiente |
| AM10, política/seguridad | P1 para efectos | Contextos no conceden permiso; errores fijos y sin efectos. No IAM, autenticación ni nueva política HTTP |
| AM11, recomendación L no ratificada | Decisión, no bug | Continúa arquitectura conforme al encargo; no asume cierre o etapa científica automática |
| AM12, guía RAW temporalmente ambigua | P2 documental | Informes previos preservados. La frase histórica no se usa como diagnóstico de inexistencia del almacén actual |

P0 sigue siendo condicional ante pérdida de identidad/restricción o promoción
sin permiso. Los conflictos probados se rechazan; no se reinterpretan pendientes
de otras áreas como defectos nuevos de esta implementación.

## 4. Identidades, estados, restricciones e integración

- Proyecto MD, contexto de aplicación, objeto lógico, entrada contextual, recurso
  institucional, contenido y activo son referencias diferentes.
- object_id mantiene unicidad entre proyectos como en catálogo RAW; la pertenencia
  es declarada y cotejada, sin consultar catálogo operativo.
- Dos operaciones sobre una entrada y dos proyectos con igual SHA no se fusionan.
  El resultado asociado a otro contexto/operación es rechazado en el cotejo de lote.
- Propósito/configuración no son usuario, permiso o autorización. autoriza_operacion
  siempre False; no se permiten usos booleanos ambiguos.
- Estado y referencias son declaraciones coherentes, no prueba de ejecución real.
  Se conservan parciales, causas, resultados incompletos y restricciones; no se
  implementa cancelación efectiva o gestión de recursos prestados del motor.
- La composición preserva el resultado QA original. Nuevas restricciones RC1
  permanecen en el vínculo; el JSON QA nativo conserva solo su política previa.
  Esa frontera explícita impide prometer exportación/persistencia RC1 ya resuelta.

La [integración](integracion_contextos_rc1.md) usa el generador QA0, exportador,
consumidor y conciliador reales con fixtures en memoria. Se ejercitan dos
proyectos, tres operaciones y dos filas en escenarios separados, perfiles,
versiones, pertenencia y linaje contextual. No se fabrica un informe 85-G/H.

## 5. Correcciones durante el incremento y límites de confianza

La primera ejecución dirigida tuvo 54 pruebas: 52 aprobadas y dos errores en las
expectativas de excepciones de pruebas nuevas. Se corrigieron las expectativas y
se distinguió TypeError por tipo de ValueError por cota. No eran fallos de suites
anteriores. La revisión añadió casos para IDs MD globales, tipo de resultado,
conflicto de fila y posición explícita.

Se detectó antes del cierre una incompatibilidad semántica en la adaptación WIP:
el consumidor QA espera entrada_id por fila. Se corrigió solo el adaptador nuevo
para mapear ID de entrada RC1 + ':' + numero_registro original explícito, siguiendo
85-G. Se probaron dos filas dentro del mismo lote. No se cambió el contrato QA.

La coherencia de DTO no autentica hechos. SHA declarado no equivale a SHA físico
comprobado; EvidenciaLocal es comprobación aportada, no ejecutada en RC1. Tampoco
se garantiza que un ResultadoQA recibido fue producido por el método declarado.
El ensayo sí llama al método real, pero no convierte ese caso en garantía contra
un llamador hostil o evidencia falsificada. No hay credenciales, cuentas, código
configurable, efectos institucionales o supuestas autorizaciones científicas.

## 6. Conexiones pendientes, según su definición original

Definiciones recuperadas de la
[matriz 85-F](matriz_dependencias_integracion_paso85f.md), ratificadas en la
[matriz 85-M](matriz_diseno_implementacion_paso85m.md):

| Conexión | Definición original | Estado después de RC1 |
|---|---|---|
| M03, C08 → C09/C02 | Ejecutor de PlanConsulta / traducción institucional de selectores a HTTP, con mecanismo, presupuesto y autorización | **P**. RC1 no consume planes ni traduce parámetros o genera endpoints |
| M16, C12 → C02/C11 | Decisión de readquisición → GET/ingesta; hook y ejecutor autorizado | **P**. ResultadoDecision continúa autoriza_red=False, sin efecto |
| M26, C20 → C21/C24/C19 | Evidencia documental → QA/aplicabilidad/operación, mediante vínculo explícito revisado | **P**. Una referencia genérica de procedencia o vínculo QA sintético no selecciona/ratifica evidencia institucional aplicable |
| M32, resultados futuros → almacenamiento/exportación | Contrato transversal de derivados y linaje científico; no JSON QA0 como resultado científico | **P**. No se persisten contextos/derivados ni se modifica almacenamiento |

No se cuentan los enlaces RC1 como cierre artificial de estas M. Las otras cifras
85-M (28 D acotadas, cuatro P y una O) siguen siendo inventario histórico delimitado,
no 28 integraciones completas o una nueva medición de madurez global.

## 7. Archivos y verificaciones de cierre

Se crean exclusivamente:

```text
src/spica/contextos/__init__.py
src/spica/contextos/modelos.py
src/spica/contextos/relaciones.py
src/spica/contextos/adaptadores_qa.py
tests/test_contextos_rc1.py
docs/contrato_contexto_comun_rc1.md
docs/integracion_contextos_rc1.md
docs/auditoria_arquitectonica_rc1.md
```

No se modifican archivos previos, dependencias, main.py, .gitignore o .venv.
El alcance nuevo es independiente y queda sin registrar para revisión.

Comandos de pruebas con ruta src configurada solo en el proceso PowerShell:

```powershell
$env:PYTHONPATH = (Join-Path $PWD 'src') + ';' + (Join-Path $PWD 'tests') + ';' + $PWD.Path
.\.venv\Scripts\python.exe -B --version
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p test_contextos_rc1.py -v
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -B -m pip check
git diff --check
git status --short
```

La primera pasada completa dentro del sandbox ejecutó 1944 pruebas en 146.670 s:
unittest informó 49 fallos y 309 errores, incluidos errores múltiples de subtests
y limpieza. Los rastros muestran permisos denegados sobre temporales sintéticos
recién creados, entre ellos los de 85-G/J/K. No se deduce el número de métodos
aprobados restando esos eventos al total ni se atribuye una regresión a RC1.

Una sonda con TemporaryDirectory, escritura/lectura de cuatro bytes sintéticos
y limpieza pasó fuera del sandbox con .venv, sin tocar ACL o datos operativos.
Por esa incidencia se autorizó mediante la herramienta una segunda pasada del
mismo comando fuera del sandbox, sin cambiar código, tests o configuración
permanente. Terminó en 668.503 s con **1942 aprobadas, dos fallos y cero errores**.
Los dos fallos fueron ModuleNotFoundError de test_conservacion_linaje_85j en
procesos hijos: la variable PYTHONPATH del comando solo incluía src, aunque esas
pruebas anteriores importan un helper de tests en otro proceso. No fue un cambio
del contrato o de su código. La primera configuración de esa variable fue
insuficiente para esos consumidores.

Se corrigió exclusivamente PYTHONPATH del proceso, incluyendo src, tests y la
raíz del checkout, como en el comando anterior. Se verificaron de forma dirigida
test_escritor_finaliza_y_otro_proceso_recupera y
test_terminacion_forzada_deja_intencion_y_marcador: **dos aprobadas en 30.468 s**,
sin fallos/errores. Después se lanzó la pasada completa final con ese entorno.
Son tres pasadas completas por incidencias de entorno, no una sola ni tres suites
sumadas. Los tres logs íntegros se conservan en TEMP como evidencia.

La primera pasada dejó 179 directorios vacíos de fixtures 85-G/J/K por el fallo
de permisos. Se identificaron y verificaron individualmente bajo el TEMP esperado,
con nombres acotados, fecha de creación dentro de esa pasada, sin reparse points
y sin contenido. Se retiraron **179 directorios vacíos**, sin borrado recursivo
ni modificación de ACL; no se eliminaron archivos o directorios con contenido.
No se recorrió RAW ni se barrió indiscriminadamente TEMP. La sonda de permisos
también cerró y eliminó su único temporal.

Las pruebas dirigidas finales ejecutaron **60 pruebas, 60 aprobadas, cero fallos,
cero errores**, en 3.842 s. Se distribuyen en 21 de modelos, 13 de relaciones,
cinco de estados, 17 de adaptación QA y cuatro de integración transversal.
Los subtests y procesos hijos no se suman como pruebas adicionales. Se analizó
también sintaxis por AST, sin compilar a archivos ni añadir herramientas.

La tercera pasada terminó correctamente: **1944 pruebas aprobadas en 669.850 s,
cero fallos, cero errores y cero omitidas**, código de salida 0. Son las **1884
anteriores más 60 nuevas**; no se suman las repeticiones ni las dos dirigidas.
Ningún archivo de código cambió entre las pasadas completas; solo se corrigió
el entorno temporal de ejecución y se terminó la documentación.

| Verificación final | Resultado observado |
|---|---|
| RC1 dirigido con .venv y -B | 60 aprobadas, cero fallos/errores, 3.842 s |
| Dos procesos de recuperación anteriores, con ruta corregida | Dos aprobadas, cero fallos/errores, 30.468 s; incluidas también en la suite definitiva |
| Suite completa definitiva, .venv Python 3.15.1 | 1944 aprobadas, cero fallos/errores/omitidas, 669.850 s |
| pip check con el mismo intérprete | Código 0: No broken requirements found. |
| Sintaxis y duplicaciones | Cinco archivos Python nuevos válidos por AST; sin definiciones duplicadas en el mismo ámbito ni marcadores de conflicto |
| Documentación y enlaces | Tres documentos, nueve tablas, 28 enlaces locales existentes, UTF-8 y bloques/columnas/espacios revisados; cero errores |
| Dependencias nuevas | Solo contratos de src y biblioteca estándar; sin import src→herramientas/tests; dos órdenes de importación/composición probados sin E/S |
| Git | diff --check, diff --exit-code HEAD y diff --cached --exit-code: código 0, sin salida; solo ocho archivos nuevos |
| Recursos temporales | RC1 en memoria; dos procesos hijos auditados, uno por orden de importación; sonda eliminada y 179 directorios vacíos de la pasada fallida retirados sin borrar contenido |

Los logs íntegros quedan fuera de Git, en TEMP del usuario, con el sufijo común
7e99d258a27b4fa28c5ad187f477e505.log:

```text
spica-rc1-suite-7e99d258a27b4fa28c5ad187f477e505.log
spica-rc1-suite-fuera-sandbox-7e99d258a27b4fa28c5ad187f477e505.log
spica-rc1-suite-final-7e99d258a27b4fa28c5ad187f477e505.log
```

No se afirma que el TEMP general esté vacío; solo se comprueban recursos propios.
Estado final de git status --short:

```text
?? docs/auditoria_arquitectonica_rc1.md
?? docs/contrato_contexto_comun_rc1.md
?? docs/integracion_contextos_rc1.md
?? src/spica/contextos/
?? tests/test_contextos_rc1.py
```

La rama permanece feature/suadc-http y HEAD ce4218b. El índice y todos los archivos
previamente registrados están intactos. Los cinco renglones representan ocho
archivos, porque Git agrupa el nuevo paquete en una carpeta. No hay commits/push.

## 8. Diseño disponible, restricciones y dictamen

Se mantienen modularidad, identidades estables, contratos tipados/versionados,
procedencia y originales, separación adquisición/almacenamiento/procesamiento,
offline, cotas y posibilidad de crecer por perfiles. Las envolventes pequeñas
usan referencias y slots sin cargar datasets; no se atribuye rendimiento medido.
No se incorpora IA, GIS, autenticación, cuentas o pagos; la ciencia determinista
sigue independiente de ellos. El contraste con Etapa 1 se limita a decisiones
disponibles; no acredita H0/G0 completos sin fuentes.

Las 29 brechas PNDA permanecen **2 resueltas, 17 parciales, ocho pendientes y dos
contradicciones**. Los expedientes previos no cambian. No se convierte coincidencia
documental, aptitud, aprobación declarativa o integridad técnica en permiso
científico. /query INGEMMET sigue sin autorización.

Cero conexiones/GET externos, descargas o instalaciones. No se accede al CSV,
RAW/staging/SQLite operativos o evidencia institucional privada; no se inicializa
almacén, migra, toca ACL, crea base operativa ni se hacen commits/push. La afirmación
de ausencia de escrituras nuestras se basa en este alcance y los ensayos, no en
haber abierto los originales para verificarlos físicamente otra vez.

Pendientes: gestor de proyecto y autorización de efectos; observación/perfiles
comunes RC2; composición y presupuesto global RC3; exportación/persistencia de
contextos y preparados/derivados RC4; conservación/custodia RC5 y medición RC6.
Las dependencias legacy y el ámbito de unicidad local requieren atención al
promover nuevas fronteras, sin refactorización masiva ahora.

**Siguiente incremento recomendado: RC2, perfiles de información/observaciones,
con un perfil sintético adicional y adaptación explícita**, sujeto a un nuevo
encargo tras auditar RC1. RC3 permanece otra dependencia posterior para efectos;
no se inicia ninguno automáticamente ni se selecciona algoritmo científico.

**Dictamen: APTO CON RESTRICCIONES para el alcance experimental RC1.** Las pruebas
finales pasan y no aparecen regresiones de código. Quedan expresamente limitados
la confianza en declaraciones, unicidad del inventario, estado sin prueba de
ejecución, perfil QA0 y conservación de la envolvente en memoria. No se declara
completa la gestión de proyectos ni la arquitectura integral. Se espera auditoría
del usuario antes de cualquier siguiente incremento o módulo científico.
