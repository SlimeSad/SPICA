# PASO 85-H — Piloto de cierre verificable en memoria

**Reanudación:** se recuperó el WIP **c259b62** con Git limpio. Las secciones
1–6 conservan los ensayos y el estado de la sesión inicial; sus cifras no son una
nueva ejecución de pruebas. La auditoría y verificación de esta reanudación se
registran en la sección 7, que prevalece para el dictamen actual.

Base inicial: rama **feature/suadc-http**, HEAD **4ea000d**, Git limpio. El commit
«SUADC: integracion vertical estructural sintetica SPICA» registra los cinco
archivos del 85-G. Se auditaron sus tres informes, código, contratos, controles
físicos y 36 pruebas. La suite histórica reportada era de 1745 pruebas.

Alcance: [contrato de cierre](contrato_trazabilidad_cierre_paso85h.md).
Dictamen y pendientes: [brechas](brechas_persistencia_linaje_paso85h.md).

## 1. Archivos y componentes

Se modifica únicamente [piloto_integracion_85g.py](../herramientas/piloto_integracion_85g.py)
para conservar evidencia parcial, verificar antes del cierre y registrar recursos.
Se añaden [traza_cierre_85h.py](../herramientas/traza_cierre_85h.py),
[test_traza_cierre_85h.py](../tests/test_traza_cierre_85h.py) y los tres documentos 85-H.
No se cambian contratos de src/spica, reglas o versiones estables ni dependencias.

Se reutilizan MockTransport, ClienteHTTP/descargar, AdaptadorHTTPRAW, AlmacenRAW,
catálogos SQLite temporales, recuperación real, LectorCSV, EvaluadorNivel0,
exportador, consumidor y conciliador. Solo el intercambio de red se simula.
Los constructores preparan esquemas nuevos vacíos y referencias en memoria;
no se migra un almacén preexistente u operativo. No hay GET externos.

## 2. Evidencia después de liberar temporales

La proyección anterior al cierre conserva activo, catálogo, QA, lecturas,
exportaciones y consumo/conciliación. Se comprueba una nueva recuperación física
antes de capturar. Tras cerrar cliente y SQLite y eliminar el árbol propio, se
construye la traza final y se coteja con la evidencia retenida, sin abrir rutas.

| Clasificación | Ejemplos y límite |
|---|---|
| COMPROBABLE DESDE LA TRAZA y el informe/control retenidos | IDs, versiones, conteos, diagnósticos, restricciones, JSON, referencias, estados, huella de representación, conciliación contractual |
| COMPROBADO DURANTE LA EJECUCIÓN | Bytes y SHA físicos de la fixture; recuperación RAW; registro y consulta del catálogo temporal; cierre de manejadores y eliminación |
| NO VERIFICABLE FÍSICAMENTE TRAS EL CIERRE | Recalcular SHA del archivo borrado, consultar de nuevo el catálogo eliminado o demostrar la historia real solo a partir de declaraciones |
| NO IMPLEMENTADO | Persistencia duradera, recuperación tras apagado, autenticidad independiente y autorización científica |

La prueba posterior prohíbe Path.open, Path.exists y sqlite3.connect y exige que
la revalidación pura siga funcionando. Otra prueba comprueba FileNotFoundError
al intentar abrir exclusivamente la ruta histórica del activo sintético eliminado.
No se usa esa excepción para afirmar una revalidación física exitosa.

## 3. Repetición y casos adversariales

A/B ejecutan QA dos veces contra el mismo activo/contexto. La construcción de
traza sobre la misma evidencia debe producir texto y huella idénticos. Una nueva
adquisición temporal produce otro asset_id y nuevas fechas técnicas; no se exige
igualdad de huella final ni se normalizan esos datos para obtenerla artificialmente.

La variante contradictoria reexporta un único diagnóstico de una copia, pasa por
el consumidor real y se concilia sin perder el conflicto. No es una nueva ejecución
QA demostrada. El original y su traza permanecen intactos. Otro contexto conserva
NO_COMPARABLE; valores o hash iguales no prueban correspondencia.

Las pruebas nuevas cubren traza completa/parcial, fases fallidas, cancelación,
presupuestos, identidades SHA/activo/catálogo, versiones, resultados duplicados,
restricciones omitidas o adulteradas, JSON ajeno al nativo, estados contradictorios,
linaje discontinuo, captura anterior al cierre, pureza posterior, conflictos y red.
Las regresiones 85-G cubren adicionalmente streaming interrumpido, corrupción RAW,
error de disco, límites del consumidor, TEMP inseguro y KeyboardInterrupt.

Los errores se conservan con códigos fijos; los mensajes arbitrarios de excepciones
no pasan a informes o trazas. No se ejecuta código aportado por archivos de reglas.
Un fallo de cierre o control físico final impide conclusión aunque QA haya terminado.

## 4. Resultados de verificación de la sesión inicial

Ensayo métrico ejecutado entre **2026-11-12T01:51:35.901397+00:00** y
**2026-11-12T01:51:53.240130+00:00** (11 de noviembre, America/Lima). Son fechas
técnicas de la auditoría, no fechas ambientales ni certificación temporal externa.

| Control / identidad | Valor realmente observado |
|---|---|
| Ejecución / evaluación | piloto-cierre-85h / evaluacion-cierre-85h |
| Entrada | entrada-ficticia-85h |
| Contexto | Sintético, perfil 85-G, dos filas ficticias, tres variables literales |
| asset_id principal | eb7bd6aa731e4a43aeb9549c0be7256d |
| Bytes incorporados | 572 |
| SHA físico | 6894bcce331d4af7db8e4a2f6008a8617604d01e8dbf4cc9805dc8cf37e8ee1b |
| Relecturas físicas observadas por instrumentación | 6; tamaño, SHA y contenido exacto correctos en todas |
| Recuperaciones explícitas del arnés | recuperacion_A, post_qa_A, recuperacion_B, post_qa_B, pre_cierre; la sexta es interna del adaptador |
| Registro de catálogo | Revisión 1; origen técnico MockTransport_sin_red |
| adquisicion_id / documento QA | None / None |
| Estado final | concluida_estructuralmente; 12 etapas de trabajo concluidas en alcance y cierre liberado |
| Enlaces cotejados | 11 coherentes, sin incidencias en la ejecución principal |
| Captura previa | 839071 bytes UTF-8 |
| SHA de captura previa | 3230196356385d16a7f0dc529dd3977af1fd7298708392d954c5e61862fc588e |
| Traza final | 842196 bytes UTF-8, contrato 0.1.0 |
| SHA de traza final | b9e2b8973910c09057f8f0b44a5580f956877d7f2e6b995915bf7eaecb2c0b31 |
| Cotejo después del cierre | Coherente en alcance; sin Path.open, Path.exists o sqlite3.connect |
| Repetición sobre la misma evidencia | Texto/huella idénticos; informe original conservado tras las variantes |

Las dos reproducciones producen cada una **60 resultados, 34 satisfechos y
26 NO_EVALUADO**, con **22 reglas**, **60 restricciones informativas y 206
bloqueantes**. Los 60 se derivan de 2 × (18 + 4 × 3), no de 60 observaciones.
Hay 278124 bytes JSON UTF-8 por lote aceptado en este contexto; son distintos del
piloto 85-G porque cambian los IDs de contexto/procedencia. Ninguna cifra se
inyecta como resultado del motor para satisfacer el ensayo.

| Comparación real después del cierre | Estado y conteos |
|---|---|
| A/B del mismo activo | COINCIDENCIA; 120 representaciones examinadas, 60 coincidencias |
| A/D, copia con diagnóstico EST-001 modificado | CONFLICTO; 59 coincidencias, una identidad y un hallazgo identidad_resultado_reutilizada |
| Nueva adquisición con el mismo contrato declarado | Nuevo asset_id b7c26e292e92409bba5dbbc6f1a74559; 60 identidades en conflicto, cero coincidencias; no equivalencia por SHA |
| Otra evaluación declarada | asset_id 5e70854733e14e6eb51f6646f4a0492e; NO_COMPARABLE, ambitos_de_evaluacion_sin_correspondencia |

La traza de la nueva adquisición con el mismo contrato tiene SHA
98542532d156df785066fc232270e2421e857ca6980a5c44b23b1cf1ca6d597b.
Su diferencia es legítima: activo y fechas técnicas distintos. No se manipulan
identidades para obtener una igualdad falsa. La repetición determinista exigida
es la de evidencia/contexto equivalentes, demostrada por A/B y la reconstrucción
del cierre sobre los mismos valores retenidos.

Se ejercieron además en el ensayo métrico:

- INCOMPLETA por límite QA: 10 resultados reales conservados, causa
  evaluacion_estructural_incompleta; sin exportación o consumo ficticios. SHA de
  esa traza: a74ff7ec9cc6e157d061735fdb2eac067c1bc8e76aba4a39cd19be1403b2f0c0.
- CANCELADA antes de iniciar: cancelacion_solicitada, sin activo, recursos o
  etapas inventadas. SHA de traza:
  6d41af828d24836ffd0555927158d27838f32d558d54b4b54ad978480f7674ae.

Las cinco llamadas del ensayo (principal, repetición con nueva adquisición, otro
contexto, incompleta y cancelada) terminaron sin temporales propios restantes.
Cuatro alcanzaron la adquisición MockTransport; cada una un GET **simulado**, cero
GET externos. La cancelada no adquirió nada. Se registró liberación en orden
catálogo científico → cliente Mock → RAW SQLite. La referencia histórica principal
spica-85g-f5skjjw8 ya está eliminada; no es un entregable recuperable.

La primera corrida dirigida ejecutó **73 pruebas: 72 aprobadas, un fallo de
expectativa y cero errores**, 146.309 s. La prueba elegía el primer JSON ordenado
por resultado_id; resultó ser NO_EVALUADO. Cambiar su diagnóstico cambia también
el texto de su restricción: aparecieron dos hallazgos sobre una identidad, ambos
correctos. Se corrigió la fixture para seleccionar EST-001 satisfecho y comprobar
un conflicto único, sin alterar el conciliador. Se añadieron tres pruebas más.
Cuatro casos finales dirigidos aprobaron en **20.679 s**, sin fallos ni errores.

Durante la revisión final se añadieron dos regresiones más, hasta **42 nuevas**:
coherencia del resumen/configuración QA y conservación del ID comunicado por el
adaptador después de publicar pero antes de retornar el activo. En este último
caso la captura previa debe contener el ID conocido; el SHA físico observado
queda ausente si el componente no retornó su evidencia. Se evita una discrepancia
artificial entre la captura y el informe final sin inventar un activo completo.
El cotejo de resumen/configuración junto al caso positivo aprobó **2 pruebas en
18.234 s**; la regresión del ID parcial aprobó **1 en 4.479 s**. La suite se repite
después de esos controles finales. Son corridas separadas, no un contador sumado.

| Cierre parcial realmente ejercido en pruebas | Evidencia retenida / estado |
|---|---|
| Antes de almacenar | CANCELADA o INCOMPLETA por bytes; cero recursos/activo/QA |
| Escritura staging / streaming interrumpido | FALLIDA; fase, causa e intentos públicos, sin activo inventado |
| Después de publicar, fallo de comprobación | FALLIDA; ID conocido, sin DTO/hash observado ficticio ni QA |
| Catálogo | FALLIDA; activo observado retenido, catálogo no confirmado, sin QA |
| Recuperación | FALLIDA; catálogo/activo disponibles, sin evaluación inventada |
| QA interrumpido por excepción | FALLIDA; 3 resultados emitidos e informe incompleto conservados |
| Exportación interrumpida | FALLIDA; 60 nativos y prefijo real de 2 JSON, sin consumo |
| Consumidor lanza excepción | FALLIDA; 60 JSON preservados, sin informe aceptado ficticio |
| Conciliación lanza excepción | FALLIDA; ambos consumos disponibles, sin conciliación fabricada |
| Cancelación después de RAW/catálogo | CANCELADA; evidencia anterior conservada, QA no iniciada |
| Presupuesto QA | INCOMPLETA; 10 resultados emitidos, sin exportación |
| Error de cierre / control físico final | FALLIDA; resultados anteriores retenidos, diagnóstico adicional y cierre/control no confirmado |

Las primeras sondas también detectaron dos supuestos incorrectos de la proyección:
el origen HTTP omite la ruta y el consumidor ordena por identidad. Se corrigieron
para respetar contratos reales. Se admiten floats finitos de políticas técnicas
sin transformar observaciones textuales. Ninguna corrección cambió src/spica.

La primera suite completa ejecutó **1785 pruebas, 1784 aprobadas, cero fallos y
un error de instrumentación**, 285.337 s: la guardia admitía git.exe pero rechazó
el nombre local git en la prueba histórica de check-ignore. Se corrigió únicamente
la guardia temporal; esa prueba aprobó en 0.328 s. La siguiente corrida de 1785
aprobó completa en **270.655 s**, sin errores y con contadores de guardia en cero.
Esa corrida precede al último refuerzo de configuración/ID parcial y sus dos
regresiones; no se presenta como la suite del código definitivo.

Verificación de la **sesión inicial**, después de su último cambio de código:

| Comprobación | Resultado real |
|---|---|
| Python / HTTPX / SQLite | 3.15.1 / 0.28.1 / 3.53.4 |
| Suite completa | **1787 aprobadas, 0 fallos, 0 errores, 0 omitidas**, 262.819 s, código 0, OK |
| Pruebas históricas / nuevas | **1745 + 42**, 1787 IDs únicos del log contrastados con AST; sin faltantes o casos inesperados |
| Código durante suite | SHA de los dos auxiliares y la prueba nuevo contrastados antes/después; sin cambios |
| pip check de .venv | **No broken requirements found.**, código 0, sin índices |
| Guardia de la suite definitiva / pip | Red 0, rutas operativas 0, SQLite operativo 0, procesos no admitidos 0 |

Las corridas históricas, iniciales, dirigidas e intermedias no se suman al total
definitivo. Los 42 casos nuevos se ejecutaron de nuevo como parte de la suite
completa; no se presenta la corrida dirigida inicial fallida como aprobada.
La única modificación posterior al último arranque definitivo es documentación.

Comandos utilizados, con ruta de importación configurada solo para los procesos:

```powershell
$env:PYTHONPATH="$env:TEMP\spica-85h-auditoria-6zdfg0q0\guardia;$PWD\src;$PWD\tests;$PWD"
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -B -m unittest test_traza_cierre_85h test_integracion_vertical_85g -v
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
$env:PIP_NO_INDEX='1'
$env:PIP_DISABLE_PIP_VERSION_CHECK='1'
$env:SPICA_85H_PIP_CHECK='1'
.\.venv\Scripts\python.exe -B -m pip check
git diff --check
git status --short
```

La corrida dirigida con ambos módulos es la inicial de 73 casos descrita arriba;
los casos posteriores se invocaron individualmente por sus nombres completos.
Las suites completas/pip se ejecutaron con subprocess desde el mismo Python .venv,
con esos argumentos, para conservar stdout/stderr UTF-8 completos fuera de Git.
La guardia se hereda en el hijo. Solo para pip se permite su consulta local de
versión Windows mediante cmd.exe. No se cambian ACL, Python o dependencias.

Evidencias de auditoría conservadas en el temporal privado
`%TEMP%/spica-85h-auditoria-6zdfg0q0/`:

- guardia/sitecustomize.py.
- dirigidas-inicial.log.
- suite-completa-final.log (primer error de instrumentación).
- suite-completa-cierre.log (1785 aprobadas, antes del último refuerzo).
- suite-completa-definitiva.log (**1787 aprobadas**, código definitivo).
- pip-check-final.log y pip-check-definitivo.log.
- piloto-cierre-metricas.json y verificacion-final.json.

Son registros técnicos y métricas, sin traza completa serializada, originales
operativos o bases RAW/SQLite. No constituyen un sistema de persistencia de
ejecuciones o recuperación tras reiniciar el proceso.

## 5. Seguridad y límites

Los ensayos se ejecutan con guardia externa de Python que rechaza conexiones/DNS,
E/S a rutas operativas conocidas y SQLite operativo. No es un sandbox del SO ni
protección frente a Python/código nativo hostil o alias desconocidos. Las pruebas
incluyen prohibición del backend HTTP real; MockTransport no acredita TLS real.

No se accede a RAW permanente, CSV, staging, SQLite o documentos institucionales.
Esta afirmación se basa en el alcance ejecutado y los controles de no acceso, no
en inspeccionar físicamente los originales ni en controlar cambios de terceros.
No se instalan paquetes, migran almacenes existentes, realizan commits o push.

Las 29 brechas PNDA permanecen en 2 resueltas, 17 parciales, 8 pendientes y
2 contradicciones. No hay autorización científica, procesamiento científico,
normalización de HORA/UBIGEO/PP, GIS ni IA. El cierre vive solo en memoria.

## 6. Estado Git y dictamen de la sesión inicial

Estado final previsto y cotejado al cerrar la auditoría:

```text
 M herramientas/piloto_integracion_85g.py
?? docs/brechas_persistencia_linaje_paso85h.md
?? docs/contrato_trazabilidad_cierre_paso85h.md
?? docs/piloto_cierre_ejecucion_paso85h.md
?? herramientas/traza_cierre_85h.py
?? tests/test_traza_cierre_85h.py
```

Rama feature/suadc-http y HEAD 4ea000d sin cambios; índice vacío de diferencias.
Un archivo registrado modificado y cinco nuevos; no hay cambios en src/spica,
main.py, .gitignore, requirements.txt, pruebas anteriores o documentación histórica.
git diff --check termina sin errores. Git avisa que LF se convertirá a CRLF al
volver a escribir el auxiliar según la configuración del checkout; no es un fallo
de espacios/sintaxis ni se altera la configuración para silenciarlo.

Se revisan directamente también los archivos nuevos (git diff --check no los
incluye): UTF-8, salto final, espacios, sintaxis en memoria, ausencia de definiciones
duplicadas, tablas y destinos de enlaces locales. No se abre ningún enlace externo.

**Dictamen: APTO CON RESTRICCIONES**, exclusivamente para cierre y linaje del
perfil sintético dentro de un proceso confiable y secuencial. Se acreditan controles
físicos durante ejecución y coherencia de la representación retenida. No se
acreditan autenticidad independiente, durabilidad, recuperación tras apagado,
concurrencia hostil o autorización científica. Deben conservarse traza, informe y
referencia separados en memoria para repetir el cotejo completo de esta API.

Siguiente propuesta: revisar requisitos de retención y recuperación de un caso
experimental antes de implementar persistencia. No se avanza automáticamente,
no se autoriza adquisición ni se ejecutan commits. Se espera revisión humana.

## 7. Reanudación desde el WIP c259b62

Git inicial: feature/suadc-http, HEAD c259b62, «WIP: desarrollo parcial de
trazabilidad y cierre paso 85-H», árbol limpio. Su padre es 4ea000d, que consolida
85-G. Se compararon los seis archivos con el padre y se inspeccionaron completos.
El WIP conserva la implementación y documentación, pero por sí solo no acredita
el cierre del paso. No hubo archivos truncados, errores de sintaxis o duplicación
de implementaciones detectados en esa recuperación.

La interrupción anterior ocurrió durante una comprobación adicional de los
registros privados de auditoría: la revisión automática no pudo autorizarla por
límite de uso. La acción no se ejecutó. El código ya incluía los DTO congelados,
proyección canónica, SHA de traza, captura previa, resultados/exportaciones
parciales, cierre de recursos y 42 pruebas. Se conserva ese trabajo. La nueva
verificación utiliza otra carpeta temporal privada y no depende de recuperar
los objetos en memoria de la sesión anterior.

### 7.1. Auditoría, defectos reproducidos y corrección

El WIP ya incluía evidencia_85h, capturar_evidencia_85h, construir_traza_85h,
verificar_traza_85h y el cierre del arnés, con sus cuerpos completos. El defecto
reproducido se localizó en _auditar: faltaban predicados de estados/recorridos,
no código truncado. La rama de fallo de captura existía y funcionaba, pero carecía
de una regresión directa; ahora se comprueba también conservación y limpieza.
Las importaciones diferidas se mantienen sin reestructurar paquetes estables.

Primero se ejecutaron **78 pruebas existentes** (42 del WIP y 36 verticales
85-G): **78 aprobadas, 0 fallos, 0 errores**, 155.655 s, código 0. No se
contabilizan las 1745 históricas como ejecutadas hasta la nueva suite completa.

Se reprodujeron seis informes contradictorios que el WIP aceptaba con
cadena_completa=True: QA INCOMPLETA, cero filas finalizadas, recorrido QA
incompleto, lector sin EOF, transferencia PARCIAL y adaptador en COMPROBACION.
La huella/identidad podía coincidir aunque esos estados no respaldaran una cadena
concluida. Esto es una omisión del cotejo técnico, no evidencia de un fallo o
modificación de un original operativo.

Se añadieron **cuatro métodos de prueba**, con subcasos de estados/recorridos y
un caso de fallo de captura. Antes de corregir, la corrida de esos cuatro métodos
produjo **19 subpruebas fallidas y cero errores**; el fallo de captura ya estaba
correctamente gestionado. El contador de métodos no se incrementa por subcasos.

Se corrigió únicamente _auditar en el componente puro: coteja descarga COMPLETA,
fase COMPLETADA, RAW INCORPORADA sin error, estados/recorridos QA, EOF, filas y
límites efectivos, y cierre/conteos/bytes del lector. Conserva estados parciales
y evidencia sin exigir etapas futuras completas. La implementación de captura y
liberación en piloto_integracion_85g.py permanece idéntica al WIP.

Después aprobaron **5 pruebas dirigidas** (las cuatro nuevas y el caso positivo),
**0 fallos y 0 errores**, 63.987 s. No se cambian modelos estables, reglas,
formatos de exportación o dependencias. El contrato de traza continúa en 0.1.0:
se refuerza el cotejo sin cambiar su representación ni su interfaz.

### 7.2. Piloto, suite y comprobaciones de cierre

El piloto de reanudación se ejecutó entre **2026-11-12T04:53:34.740791+00:00** y
**2026-11-12T04:53:50.618620+00:00** (11 de noviembre en America/Lima). La fecha
técnica del intercambio simulado fue 2026-11-12T04:53:34.804994+00:00; no acredita
una adquisición institucional ni una fecha de observación meteorológica.

| Evidencia actual | Resultado observado |
|---|---|
| Ejecución / evaluación / entrada | cierre-85h-reanudacion / evaluacion-85h-reanudacion / entrada-85h-reanudacion |
| asset_id sintético | e47f6bd722754589906573e33de7fd33 |
| Tamaño / SHA físico | 572 / 6894bcce331d4af7db8e4a2f6008a8617604d01e8dbf4cc9805dc8cf37e8ee1b |
| Comprobaciones físicas observadas | 6 relecturas; SHA y bytes idénticos a la fixture en todas |
| Estado | concluida_estructuralmente; 12 etapas de trabajo y cierre liberado |
| QA por reproducción | 2 filas, 22 reglas, 60 resultados: 34 satisfechos y 26 NO_EVALUADO |
| Restricciones por reproducción | 60 informativas y 206 bloqueantes |
| Captura previa SHA | b1bb8f3835c4b403d846adad1b4842ad9dffaef58559819fe77ecb7b6849aed8 |
| Traza final | 843164 bytes; SHA c5509034f4d54c40cd795c7f8ab0b2cc417e3c852765b8c1e38f9b6fba308e54 |
| Después del cierre | Cotejo coherente con Path.open/Path.exists/sqlite3.connect prohibidos; reconstrucción determinista |
| A/B | 120 representaciones, 60 coincidencias, cero conflictos |
| Variante de diagnóstico EST-001 | 59 coincidencias y un conflicto identidad_resultado_reutilizada |
| Otra evaluación | NO_COMPARABLE; ambitos_de_evaluacion_sin_correspondencia |
| Límite QA | INCOMPLETA, 10 resultados preservados, evaluacion_estructural_incompleta |
| Cancelación previa | CANCELADA, sin activo, cancelacion_solicitada |
| Recursos | Catálogo científico, cliente Mock y RAW cerrados en orden inverso; temporales de las cuatro llamadas eliminados |
| Documento / adquisicion_id QA | None / None, sin inventar identidades institucionales |

Los conteos se derivaron de los resultados reales del motor. La variante es una
copia adversarial reexportada, no una reevaluación QA demostrada. La traza original
permanece intacta. Se conserva A–E en el alcance del contrato; F–I no se acreditan.
Las rutas y bytes temporales ya no existen; los cotejos posteriores son en memoria.

Verificación actual, ejecutada después de las correcciones:

| Comprobación de la reanudación | Resultado real |
|---|---|
| Python / HTTPX / SQLite | 3.15.1 / 0.28.1 / 3.53.4, intérprete .venv |
| Suite completa | **1791 aprobadas, 0 fallos, 0 errores, 0 omitidas**, 384.057 s, código 0, OK |
| Desglose contrastado con AST y log | **1745 anteriores + 42 recuperadas del WIP + 4 nuevas**; 1791 IDs únicos, cero faltantes/inesperados |
| Código durante la suite | SHA de ambos auxiliares y la prueba contrastados antes/después; sin cambios |
| pip check | **No broken requirements found.**, código 0 |
| Importación de auxiliares en ambos órdenes | Código 0 en ambos, sin ejecutar pilotos ni inicializar almacenes al importar |
| Guardia de suite, pip, importaciones y piloto | Cero red/DNS, accesos a rutas operativas conocidas, SQLite operativo o procesos no admitidos |

Los antecedentes de las secciones anteriores permanecen identificados como
históricos. Las pruebas dirigidas y subcasos no se suman a la suite completa.
Después de la suite solo se completa documentación; no se modifica código.

Comandos actuales, con importaciones configuradas solo en el entorno del proceso:

```powershell
$env:PYTHONPATH="$env:TEMP\spica-85h-reanudacion-eefgosro\guardia;$PWD\src;$PWD\tests;$PWD"
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -B -m unittest test_traza_cierre_85h test_integracion_vertical_85g -v
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
$env:PIP_NO_INDEX='1'
$env:PIP_DISABLE_PIP_VERSION_CHECK='1'
$env:SPICA_85HR_PIP_CHECK='1'
.\.venv\Scripts\python.exe -B -m pip check
git diff --check
git status --short
```

La primera invocación dirigida es la del WIP sin modificar (78 casos). Los cinco
casos posteriores se invocaron por sus nombres completos. Se usaron drivers del
mismo Python .venv con stdout/stderr completos en UTF-8 y guardia heredada; para
pip se permitió únicamente su consulta local de versión Windows mediante cmd.exe.
No se instalan dependencias ni se modifican ACL. La inicialización de esquemas
vacíos/referencias en memoria de las fixtures reutiliza los constructores
existentes; no se migran almacenes preexistentes u operativos.

La carpeta privada `%TEMP%/spica-85h-reanudacion-eefgosro/` conserva:

- guardia/sitecustomize.py.
- wip-dirigidas.log (78 aprobadas antes de modificar).
- reproduccion-wip.json (seis contradicciones aceptadas antes de corregir).
- regresiones-antes.log (19 subfallos reproducidos).
- regresiones-corregidas.log (5 aprobadas).
- suite-completa.log (**1791 aprobadas**, código definitivo).
- pip-check.log, verificacion-final.json y piloto-metricas.json.

Se enumeró su contenido al terminar las verificaciones: solo guardia, logs y
métricas; sin RAW, staging, SQLite o trazas completas persistidas. Los recursos
de los pilotos se eliminaron. Se conserva información de auditoría para revisión,
no un mecanismo de recuperación del objeto traza tras terminar el proceso.

### 7.3. Git final, restricciones y dictamen actual

El HEAD y la rama se mantienen en c259b62 / feature/suadc-http. Se modifican
únicamente el cotejador, sus pruebas y los tres documentos de este paso:

```text
 M docs/brechas_persistencia_linaje_paso85h.md
 M docs/contrato_trazabilidad_cierre_paso85h.md
 M docs/piloto_cierre_ejecucion_paso85h.md
 M herramientas/traza_cierre_85h.py
 M tests/test_traza_cierre_85h.py
```

No hay archivos nuevos respecto al WIP. El arnés piloto_integracion_85g.py, los
contratos estables de src/spica, las pruebas anteriores, main.py, .gitignore,
requirements.txt y las 29 brechas PNDA permanecen sin cambios. Se comprueban
sintaxis, definiciones duplicadas, UTF-8, espacios, tablas y los 16 destinos de
enlaces locales. git diff --check no presenta errores; los avisos LF/CRLF
corresponden a la configuración existente y no se la modifica.

No se accedió a CSV/documentos institucionales, RAW permanente o staging/SQLite
operativos; no hubo conexiones, GET externos, descargas, instalaciones, commits
o push. Solo intercambios GET simulados en MockTransport y recursos sintéticos.
No se inspeccionan originales cerrados para sostener esta afirmación ni se
atribuye control sobre acciones de otros procesos.

Las 29 brechas mantienen **2 resueltas, 17 parciales, 8 pendientes y 2
contradicciones**. No se normalizan HORA/UBIGEO/PP, ni se activan ciencia, GIS, IA
o permisos operativos. La traza sigue requiriendo informe y control de referencia
conservados en un proceso confiable y secuencial. No hay persistencia duradera,
recuperación tras apagado, autenticidad institucional o validación científica.

**Dictamen actual: APTO CON RESTRICCIONES** para el cierre experimental descrito.
Los defectos reproducidos están corregidos y verificados. Para el siguiente
incremento se recomienda revisar requisitos y política de retención/recuperación
antes de implementar persistencia. No se continúa automáticamente; se espera
auditoría humana.
