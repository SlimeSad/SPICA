# PASO 85-H — Piloto de cierre verificable en memoria

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

## 4. Resultados de verificación

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

Verificación **definitiva**, después del último cambio de código:

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

## 6. Estado Git, revisión y dictamen

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
