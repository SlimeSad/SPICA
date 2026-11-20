# RC9 — Auditoría arquitectónica y consumo técnico

Fecha de elaboración: 2026-11-19, America/Lima. Incremento experimental offline.

## Auditoría previa a la implementación

Git inicial: `feature/suadc-http`, HEAD
`246bbeca1e34b74495d883d42b1f851eb7a7cba6`, árbol limpio. RC8 está registrado
como `246bbec SPICA: cierre tecnico verificable de exportacion RC8`.
Antecesores: RC7 `c1b224e`, RC6 `367e95f`, RC5 `27a9224`, RC4 `1024158`.
Entorno comprobado: Python 3.15.1 del `.venv`, HTTPX 0.28.1, SQLite 3.53.4.

Se revisaron los tres documentos RC8, las auditorías RC3–RC7, la hoja de ruta
85-M, exportador, consumidor y sus pruebas, restricciones, contextos, linaje,
materialización RC5, recuperación RC6 y coordinación RC7. Las referencias y
los contratos detallados se recogen en el [contrato RC9](contrato_consumo_evidencia_rc9.md).

Consumidor seleccionado: `spica.calidad.consumo.consumir_exportaciones`.
Existe y se invoca realmente en RC8. No es necesario crear un consumidor.

| Dimensión | Garantía existente | Carencia que debe respetarse |
|---|---|---|
| A. Sintaxis | Lector JSON acotado, tipos, claves duplicadas | No autentica al emisor |
| B. Formato | Perfil JSON QA 0.1.0 cerrado | No acepta cualquier salida del exportador |
| C. Estructura | Contraste nativo, versiones y datos derivados | No reevalúa reglas QA |
| D. Identidades | Identidad contextual interna y huella reproducible | No exige el proyecto/operación/artefacto esperado por otro subsistema |
| E. Bytes | Coherencia de huella interna del paquete | No relee archivos físicos |
| F. Exportación | RC8 comprueba su captura local específica | El consumidor por sí solo no exige RC8 |
| G. QA | Conserva declaraciones y resultados recibidos | Consumir no acredita ejecución QA independiente |
| H. Autenticidad | Ninguna acreditación institucional | Hash y captura local no son firma |
| I. Ciencia | Conserva limitaciones y restricciones | No valida ciencia |
| J. Permisos | Comprueba las restricciones internas de la exportación | No resuelve permisos ni aplica una finalidad externa específica |

Decisión previa: desarrollar un adaptador externo pequeño para contrastar el
contenido recibido con una captura RC8 y con identidades esperadas explícitas,
aplicar las restricciones del uso técnico concreto y, opcionalmente, solicitar
una relectura RC5 actual. El parseo y la validación JSON siguen exclusivamente
en el consumidor nativo. La inspección RC8 se reutiliza sin cambios.

No hace falta romper contratos públicos ni modificar RC3, RC7, RC8, RC6,
85-J/K, JSON QA 0.1.0 o SQLite 85001. La necesidad futura de admitir cierres
no QA en dependencias y de conservar su evidencia se documentará, sin ejecutarla.
No se detectó una puerta de detención que impida este adaptador aislado.

## Incremento implementado y compatibilidad

Se creó [admision_exportacion.py](../src/spica/artefactos/admision_exportacion.py),
un módulo hoja experimental con una función pública, dos dataclasses de solicitud/informe
y constantes de versión, consumidor y finalidad. Los auxiliares solo comparan
identidades, delimitan la lectura RC5 y producen diagnósticos. No existe parser
JSON, exportador, registro de ejecución, base de datos u orquestador nuevo.

El consumidor sigue siendo `consumir_exportaciones`, no un consumidor ficticio.
Su informe nativo está dentro del informe RC9. El inspector RC8 se invoca sin
cambios para contrastar su evidencia; su validación interna vuelve a usar el
mismo consumidor, sobre la salida capturada. Los presupuestos respectivos se
mantienen separados. El contraste de codificación puro del consumidor tampoco
es despacho automático de una operación ni ejecución de reglas QA.

La admisión específica usa EstadoAptitud: apto estructuralmente, incompatible o
pendiente de evidencia. Contrasta productor/versión y cierre RC8; consumidor y
versión; proyecto/configuración; operación; entrada de resultado; artefacto y
revisión; contenido lógico; resultado nativo y bytes literales. No usa el hash
para fusionar identidades. Conserva restricciones internas y contextuales en sus
contenedores correspondientes y aplica el único uso `consumir_json_qa0_rc9`.

Los errores comprobados rechazan; los faltantes o presupuestos agotados dejan
pendiente; ninguna falta se completa por inferencia. Los informes propios
construidos/copiados por un llamador no acreditan una comprobación local RC9.
Los testigos RC8/RC9 son trazabilidad cooperativa en memoria, no firmas ni
protección frente a un intérprete hostil. No se acepta un InformeQA artificial.

Las políticas y contratos anteriores permanecen intactos, incluidos RC1–RC8,
JSON QA 0.1.0, `rc6.generacion.0.1.0`, codec 85-J, manifiesto 85-K y SQLite
85001. No se cambia ningún `__init__.py`, módulo Python anterior, configuración,
dependencia, main.py, .gitignore o .venv. La función nueva no se incorpora por
importación automática a otros subsistemas.

## Piloto sintético efectivamente ejecutado

Se ejecutaron las pruebas del [piloto RC9](../tests/test_admision_exportacion_rc9.py)
y un arnés efímero por stdin con Python `.venv -B`; el arnés no se escribió como
herramienta, no abrió datos institucionales y usó solo las fábricas de fixtures
anteriores. El exportador real fue invocado por `ejecutar_exportacion_tecnica`;
su salida real se entregó al consumidor nativo mediante RC9. Las pruebas con
`wraps` comprueban ambas invocaciones, sin sustituir sus resultados exitosos.

| Dato base observado | Valor |
|---|---|
| Operación exportadora | `exportar` |
| Entrada lógica del exportador | `resultado-qa-fuente`, resultado del evaluador nativo sobre registro ficticio |
| Artefacto/revisión | `objeto-salida-exportacion-proyecto-RC8`, `r1` |
| Contenido lógico | `salida-json-fixture` |
| Tamaño UTF-8 | 3852 bytes |
| SHA-256 de la salida en memoria | `8a9ed4f6977f1c25c2d230589666947fcca6bf50d7c3b2fff4ecc9a4c606eb07` |
| resultado_id JSON | `qa0-734e241e0153c936862cd3ec0c902f0788bd4186b5616418368be52a200f470a` |
| Estado histórico en inventario | INICIADA; permanece intacto |
| Estado observado por RC8 | CONCLUIDA |
| Estado RC9 | APTO_ESTRUCTURALMENTE |
| Restricciones heredadas | alcance_estructural, sin_validacion_cientifica, sin_equivalencia_editorial |
| Habilitadas declarativamente por RC3 | Tupla vacía |
| Permiso, ciencia y habilitación RC3 nuevos | False |

La variante física escribió explícitamente esos bytes mediante RC5 en TEMP
privado y luego RC9 invocó de nuevo el verificador existente. Observación actual:
`2026-11-19T10:29:25.635435+00:00`, 3852 bytes leídos, estado INTEGRO,
SHA-256 físico igual al indicado arriba y contenido almacenado igual a la salida.
El informe de lectura actual es distinto del informe histórico de publicación.
El contexto retiró el temporal y su raíz al salir. No se promete persistencia
de este archivo de ensayo ni disponibilidad posterior.

| Variante real del piloto | Consumo nativo | Admisión RC9 |
|---|---|---|
| Salida base, identidad y captura correctas | Válido en alcance | Admisible en memoria |
| Entrada esperada distinta | Válido en alcance | Incompatible |
| Sin captura RC8 | Válido en alcance | Pendiente; el JSON aceptado conserva sus restricciones internas |
| Bytes con un espacio añadido | Válido en alcance | Incompatible por no ser los bytes capturados |
| Cancelación observada después de producir, estado PARCIAL | Válido en alcance | Pendiente; no se promueve el estado |
| Proyectos independientes RC9-A y RC9-B | Válido en ambos | Admisible por separado con su propia evidencia |
| Evidencia B presentada para la solicitud A | Válido en alcance | Incompatible |
| Archivo RC5 correspondiente y relectura exigida | Válido en alcance | Admisible con integridad física puntual |

Se forzó una colisión nominal de contexto `colision-fixture` en dos inventarios
independientes: los bytes fueron idénticos y los project_id distintos. Esto
demuestra que la igualdad de contenido no identifica un proyecto ni transfiere
autorizaciones; no se declara resuelta la unicidad global de espacios nominales.

En el caso RC6, ejecutado dentro de las pruebas, se conservaron bytes sintéticos
y el inventario admitido por su perfil. La recuperación dio VERIFICADA para la
generación; la entrada externa quedó NO_DISPONIBLE. Los bytes recuperados sin
RC8 dejaron pendiente RC9; aportando además la captura local aún disponible se
admitió el consumo en memoria. RC7 no habilitó `consumidor`, no recuperó cierres
QA ni RC8 y la operación histórica permaneció INICIADA. No se atribuye ese
resultado positivo a una captura conservada por RC6.

Un caso adicional ejecuta el EvaluadorNivel0 real sobre un CSV ficticio TEMP,
obtiene su cierre QA nativo completo y exporta uno de sus resultados mediante
RC8/RC9. El cierre QA permanece independiente y no se añade un CierreQA a la
operación exportadora. No se reemplazan informes nativos por DTO fabricados.

## Archivos del incremento

| Archivo nuevo | Contenido |
|---|---|
| [admision_exportacion.py](../src/spica/artefactos/admision_exportacion.py) | Solicitud/informe de admisión, contrastes específicos y relectura RC5 opcional |
| [test_admision_exportacion_rc9.py](../tests/test_admision_exportacion_rc9.py) | 41 pruebas sintéticas del adaptador y sus fronteras |
| [contrato_consumo_evidencia_rc9.md](contrato_consumo_evidencia_rc9.md) | APIs reutilizadas, garantías, versiones y límites |
| [politica_admision_conservacion_rc9.md](politica_admision_conservacion_rc9.md) | Política, análisis A–F y evolución futura propuesta |
| `auditoria_arquitectonica_rc9.md` | Este informe, piloto, verificación y dictamen |

No hay modificaciones de archivos previamente registrados ni del índice Git.
No se sobrescribió documentación histórica ni se crearon herramientas auxiliares
persistentes. Los arneses efímeros solo se enviaron por stdin al intérprete.

## Pruebas adversariales

Se añadieron **41 pruebas**, sin importar clases TestCase de otros módulos.
Las fábricas reutilizadas generan datos sintéticos y resultados nativos. Los
casos cubren los 31 temas solicitados dentro del alcance de este consumidor:

| Frontera | Evidencia de prueba |
|---|---|
| Admisión y formato | Productor/consumidor reales, bytes UTF-8, JSON inválido, raíz no soportada, versión desconocida y presupuesto insuficiente |
| Identidades | Consumidor/productor/versiones, proyecto y contexto, operación, entrada/fila, artefacto/revisión, contenido y cruce de proyectos con bytes iguales |
| Captura y alteración | Cierre ausente, captura copiada, productor no invocado, contenido ausente, bytes cambiados, hash/tamaño contradictorios y Unicode inválido |
| Restricciones | Bloqueo específico del consumo, restricciones científicas heredadas, bloqueo conocido sin captura y conservación de variantes contradictorias |
| Estados | Parcial realmente observado por cancelación posterior, fallo del productor, cancelación anterior y estado histórico intacto |
| Física | Relectura actual real sin cierre QA, archivo ausente, corrupción, referencia de otro proyecto, referencia faltante y materialización histórica parcial |
| Conservación | Recuperación RC6 real, referencia externa no disponible, bytes sin captura y RC7 pendiente |
| Límites de confianza | Cierre QA genuino separado, dependencia RC3 no habilitada, informe propio copiado no observado, ausencia de permisos/ciencia y bool genérico rechazado |
| Efectos y determinismo | Sin despacho RC8 desde la admisión, sin evaluación QA, sin red, archivos o SQL en la rama de memoria; dos inspecciones iguales |

La prueba sin E/S intercepta `builtins.open`, sockets y `sqlite3.connect`; las
ramas físicas usan las referencias RC5 y los contextos TEMP existentes. Esas
barreras de prueba no constituyen aislamiento hostil del proceso. Los tests de
física solo alteran/eliminan los archivos de ensayo que acaban de crear, dentro
de la misma raíz TEMP, para comprobar su detección y limpieza.

## Verificaciones y comandos

Se usó exclusivamente `.venv\Scripts\python.exe -B`. PYTHONPATH y
PYTHONDONTWRITEBYTECODE se configuraron en el proceso de verificación, sin
modificar archivos de entorno:

```powershell
$env:PYTHONPATH=(Join-Path $PWD 'src')+';'+(Join-Path $PWD 'tests')+';'+$PWD.Path
$env:PYTHONDONTWRITEBYTECODE='1'
.\.venv\Scripts\python.exe -B -m unittest test_admision_exportacion_rc9 -q
```

Resultado final dirigido RC9: `Ran 41 tests in 3.204s`, `OK`.

Regresiones seleccionadas: test_integracion_artefactos_rc7,
test_cierre_exportacion_rc8, test_coordinacion_rc3, test_artefactos_rc4,
test_consumo_qaqc_85d y test_exportacion_qaqc_85c: **251 aprobadas**, sin
fallos de prueba. RC5/RC6 se comprobaron con sus nombres reales:

```powershell
.\.venv\Scripts\python.exe -B -m unittest test_materializacion_rc5 test_conservacion_rc6 -q
```

Resultado: `Ran 116 tests in 45.748s`, `OK`. Total de regresiones nativas
distintas de esos grupos: **367 aprobadas**. No se suman estas ejecuciones
repetidas a la cantidad de tests únicos de la suite completa.

Incidencias intermedias, resueltas antes del cierre: el primer grupo RC9 tuvo
37 aprobadas y un error en la prueba nueva que consultaba `estado_local` en vez
del atributo RC6 real `estado_actual`; se corrigió esa referencia. El comando
inicial de regresiones incluyó dos nombres de módulos inexistentes, produjo dos
errores del cargador y ejecutó correctamente las otras 251 pruebas. Se corrigió
la selección y se ejecutaron los 116 tests RC5/RC6 reales. Ninguno de estos
errores exige cambiar módulos históricos. Una comprobación AST efímera necesitó
importar explícitamente importlib.util; no fue un error de código del proyecto.

Comando único de suite completa final, después de cerrar código/pruebas:

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -B -m pip check
git diff --check
git status --short
```

La salida verbose se redirige íntegra a un registro fuera de Git:
`%TEMP%/spica-rc9-suite-final-cc1217ed9cba4f1289117c0b5f800d92.log`.
La única suite completa final terminó con código 0:

```text
Ran 2373 tests in 1042.028s

OK
```

**2373 aprobadas, 0 fallidas, 0 errores y 0 omitidas**: las 2332 anteriores y
41 nuevas RC9. No se suman subtests, llamadas del piloto ni reejecuciones
dirigidas. El registro no contiene fallos ni ResourceWarning.

Comprobación estática ya ejecutada: AST/compilación en memoria de ambos Python
nuevos, sin definiciones duplicadas; 41 métodos de prueba únicos; importación
explícita RC9 correcta; grafo AST de 123 módulos, 79 dependencias alcanzadas
desde RC9, ninguna importación inversa ni ciclo que incluya el módulo nuevo.
UTF-8, EOF, espacios finales y marcadores de conflicto revisados directamente
en los cinco archivos nuevos, que no cubre `git diff --check` por estar sin
seguimiento. Los enlaces locales y cercas se revisan sin ninguna conexión
externa; la limpieza de temporales se comprueba después de terminar la suite.

`pip check` ejecutado con el mismo intérprete: `No broken requirements found.`,
código 0. Git diff --check sin salida, código 0; sin diferencias de archivos
registrados o del índice. La última escritura de código/pruebas fue
10:24:29/10:24:30 UTC, anterior al registro de suite final creado a las
10:29:48 UTC. Durante la suite solo se completa esta documentación.

Comprobación final de temporales: cero directorios `spica-rc3-qa-*`,
`spica-rc5-*`, `spica-rc6-*` y cero `.suadc-test-*` en el repositorio.
El registro de verificación se conserva intencionadamente fuera de Git.
No se necesitó borrado correctivo ni limpieza recursiva.

Una inspección ampliada encontró tres carpetas `spica-config-test-*` creadas y
modificadas el **2026-10-29**, antes de RC9: sufijos
`05082aab04fb4eae87578b104d8c5f08`, `1f0c74b2d06a4374b85cd29c53bed889`
y `e030203d09ad4860a488caec28a4f1d6`. El primer control ampliado asumió que no
existía ninguna y se detuvo; la comprobación posterior de fechas/atributos
permitió clasificarlas como preexistentes, sin symlinks/junctions. Solo se
leyeron esos metadatos: no se abrieron sus contenidos ni se borraron archivos.
No se atribuyen a esta suite ni se incluye su mantenimiento en RC9.

Git final: `feature/suadc-http`, mismo HEAD
`246bbeca1e34b74495d883d42b1f851eb7a7cba6`; cinco archivos nuevos sin seguimiento:

```text
?? docs/auditoria_arquitectonica_rc9.md
?? docs/contrato_consumo_evidencia_rc9.md
?? docs/politica_admision_conservacion_rc9.md
?? src/spica/artefactos/admision_exportacion.py
?? tests/test_admision_exportacion_rc9.py
```

Ningún archivo previamente registrado modificado; índice sin cambios. No se
realizaron commits o push. Git diff --check se complementa con la inspección
directa de los cinco archivos sin seguimiento y de sus enlaces locales.

## Conexiones originales, privacidad y alcance

Se preservan las definiciones originales de la
[matriz 85-F](matriz_dependencias_integracion_paso85f.md) y su relación con la
[hoja de ruta 85-M](hoja_ruta_continuidad_arquitectonica_paso85m.md). Sus grupos
RC originales son una propuesta de responsabilidades y no una homologación
automática de la numeración de incrementos posteriores. La arquitectura integral
permanece abierta; no se inventan aprobación ERS, actas o nuevos horizontes.

| Conexión original | Estado tras este alcance RC9 |
|---|---|
| M03, C08 → C09/C02: ejecutor PlanConsulta y traducción de selectores institucionales a parámetros HTTP | **P**; siguen faltando mecanismo, presupuesto y autorización por recurso. RC9 no ejecuta planes ni HTTP |
| M16, C12 → C02/C11: recomendación de readquisición → GET/ingesta con hook y ejecutor aprobado | **P**; no se añade hook ni se convierte una recomendación en efecto |
| M26, C20 → C21/C24/C19: evidencia documental → QA/aplicabilidad/operación mediante vínculo explícito revisado | **P**; consumir un diagnóstico sintético no aprueba evidencia institucional ni su aplicabilidad |
| M32, resultados futuros → almacenamiento/exportación científica y contrato transversal de derivados/linaje | **P**; RC4–RC9 aportan contratos, conservación experimental y una frontera de consumo técnico específica. JSON QA0 no es el resultado científico futuro ni resuelve su almacenamiento operativo |

Las [29 brechas PNDA](brechas_reconciliadas_pnda_paso84i.md) no se modifican:
2 RESUELTA_CON_EVIDENCIA, 17 PARCIALMENTE_DOCUMENTADA, 8 PENDIENTE_DE_EVIDENCIA
y 2 CONTRADICCIÓN_DOCUMENTADA. No se accede al CSV PNDA ni a evidencia privada.
INGEMMET `/query` permanece NO AUTORIZADO.

Se mantienen cero conexiones externas, GET externos, descargas, instalaciones,
migraciones, commits o push. No se abre RAW operativo, staging ni SQLite
operativo; no se miden originales reales para prometer nueva integridad física.
Se informa ausencia de acceso/escritura operativos en este incremento. El
piloto y las pruebas nuevas usan memoria y TEMP sintético, sin permisos nuevos.

Los informes conservan contenido/contexto potencialmente sensible aportado por
el llamador, pero no se publican ni escriben automáticamente. Los diagnósticos
nuevos son códigos fijos y no reproducen credenciales o rutas de excepciones.
Revisar privacidad antes de cualquier conservación, distribución o log operativo.

## Conservación y evolución no ejecutada

La [política A–F](politica_admision_conservacion_rc9.md) diferencia bytes
recomprobables, observaciones de ejecución que deben conservarse, contextos
referenciados, información irrecuperable si no se registra, autenticidad no
acreditada y estados históricos frente a comprobaciones actuales.

Propone revisar un perfil versionado de observaciones con identidad, productor,
consumidor, versiones, finalidad, límites, contexto exacto, salida, restricciones,
causas, fechas realmente observadas y confianza. No se serializan testigos
privados, no se inventan fechas de ejecución y no se convierte metadato recuperado
en una nueva captura local. No se implementa el perfil, codec, base o almacén.

La dependencia concreta pendiente es `exportar → consumidor`: para habilitarla
RC3/RC7 necesitarían admitir un tipo explícito de cierre técnico no QA, con
condiciones por arista, restricciones y evidencia suficiente. La política enumera
los contratos públicos potencialmente afectados y deja su diseño/versionado
pendiente de revisión. No cambia RC3/RC7 ni existe autorización implícita.

## Riesgos residuales y siguiente prioridad

Persisten confianza en un proceso Python cooperativo, contexto declarado sin
autenticación, unicidad nominal externa y pérdida de testigos al copiar o reiniciar.
Una captura local no certifica una institución; un JSON coherente puede ser
fabricado por un remitente y un hash no autentica a su autor. El consumidor solo
admite su perfil cerrado, sin probar ejecución QA ni mérito científico.

Las cotas son locales y no una reserva conjunta de CPU/RSS/disco o garantía ante
terminación del proceso. La admisión compara bytes en memoria dentro de los
presupuestos, no ofrece streaming de JSON grande. La comprobación RC5 es
puntual, con riesgos históricos de TOCTOU, concurrencia cooperativa y ausencia
de custodia/durabilidad operativa. RC6 no incorpora el cierre RC8/RC9; su
recuperación no asegura entradas externas. No se eleva ninguna garantía previa.

El adaptador reutiliza auxiliares internos RC7/RC3 y depende de sus versiones de
checkout; extraer una API pública solo debe plantearse cuando otro caso aprobado
lo necesite. No se crea preventivamente un framework. La interpretación de la
finalidad técnica y la confianza histórica necesitan revisión antes de otro uso.

Siguiente prioridad recomendada para revisión: decidir la política de confianza
y el expediente mínimo de conservación de cierres/consumos técnicos después de
reiniciar. Solo después de aprobar esa frontera, evaluar una admisión no QA
específica por dependencia RC3/RC7, manteniendo QA y permisos separados. Esta
recomendación no inicia RC10, persistencia operativa ni núcleos científicos.

Dictamen final: **APTO CON RESTRICCIONES** para la admisión técnica específica
del JSON QA nativo respaldado por RC8, en memoria y con relectura RC5 opcional
en el entorno experimental admitido. No quedan fallos ni correcciones
bloqueantes conocidos para ese alcance. No es una política universal, un cierre
QA, autorización, validación científica ni habilitación de dependencias RC3/RC7.
La evidencia histórica de conservación, la confianza tras reinicio, los permisos,
la custodia independiente y el uso operativo continúan pendientes de revisión.
La arquitectura integral no está finalizada. No se inicia el siguiente bloque
ni el desarrollo de núcleos científicos; se entrega para revisión del equipo.

## Recuperación tras bloqueo — 2026-11-19, America/Lima

Esta sección registra la revisión posterior solicitada tras el bloqueo de la
laptop. Los resultados y la referencia a una única suite completa final de las
secciones anteriores corresponden al desarrollo inicial de RC9. Se conservan
sin sustituirlos por las nuevas verificaciones de recuperación.

### Diagnóstico antes de continuar

Git inicial de la recuperación: rama `feature/suadc-http`, HEAD
`246bbeca1e34b74495d883d42b1f851eb7a7cba6`; los mismos cinco archivos RC9
sin seguimiento. Ningún archivo registrado modificado; índice sin cambios.
RC8 está registrado en HEAD; RC9 sigue pendiente de revisión y registro.

Se leyeron completos el adaptador, sus pruebas y los tres documentos RC9, y se
contrastaron con la solicitud original. No se detectaron archivos truncados,
marcadores de conflicto, errores de sintaxis, cuerpos sin implementar ni
funciones/clases duplicadas. Ambos Python compilan en memoria, sin escribir
bytecode. Hay 41 métodos de prueba nuevos únicos y 26 enlaces locales válidos.
Los archivos son regulares, sin symlinks ni junctions. La importación explícita
funciona; el grafo de 123 módulos no presenta ciclos que incluyan RC9 ni imports
anteriores hacia él, con 79 dependencias alcanzadas desde el adaptador.

| Apartado RC9 | Estado encontrado y conservado |
|---|---|
| Auditoría de reutilización y consumidor real | Completo; consumidor nativo 85-D y responsabilidades documentados |
| Solicitud, informe y política específica | Implementados; estados existentes apto/incompatible/pendiente |
| Identidades, versiones y bytes | Contrastes explícitos implementados, sin fusionar proyectos por hash |
| Evidencia RC8 y restricciones | Inspección nativa y unión existente, sin fabricar cierres QA ni perder variantes |
| Integridad física opcional | Relectura RC5 actual, separada del informe histórico |
| Piloto y adversariales | Implementados con datos sintéticos, dos proyectos y 41 pruebas nuevas |
| Conservación A–F y evolución versionada | Documentadas como propuesta; no se implementa persistencia nueva |
| RC3/RC7, RC6 y formatos históricos | Sin ampliación o modificación; sus pendientes requieren otra decisión |
| Documentos e informe inicial | Los tres documentos completos; no faltaba su cierre |

Se recuperó y leyó el registro previo completo:
`%TEMP%/spica-rc9-suite-final-cc1217ed9cba4f1289117c0b5f800d92.log`.
Contiene `Ran 2373 tests in 1042.028s` y termina en `OK`, sin fallos. Por tanto,
no hay evidencia de que las pruebas anteriores quedaran sin terminar. Este
resultado es histórico y no se usa como sustituto de la ejecución nueva.

No se identificó implementación pendiente de RC9 ni un riesgo crítico de
recuperación que justifique reescribir código. Las tareas actuales se limitan a
revalidar, comprobar conservación del trabajo y registrar esta revisión. No se
recuperan testigos privados en memoria desde los documentos o logs: las nuevas
pruebas obtienen capturas nuevas mediante ejecuciones sintéticas reales.

### Verificaciones nuevas solicitadas

Entorno nuevamente comprobado: Python 3.15.1 de `.venv`, HTTPX 0.28.1 y
SQLite 3.53.4. Una consulta opcional de procesos mediante CIM devolvió acceso
denegado; se utilizó `Get-Process`, que no identificó procesos Python activos
antes de iniciar las pruebas. No se cambiaron permisos ni se detuvieron procesos.

```powershell
$env:PYTHONPATH=(Join-Path $PWD 'src')+';'+(Join-Path $PWD 'tests')+';'+$PWD.Path
$env:PYTHONDONTWRITEBYTECODE='1'
.\.venv\Scripts\python.exe -B -m unittest test_admision_exportacion_rc9 test_cierre_exportacion_rc8 test_integracion_artefactos_rc7 -v
```

Resultado dirigido realmente ejecutado: `Ran 123 tests in 130.012s`, `OK`;
123 aprobadas, cero fallidas y cero errores. Incluye las 41 RC9, 38 RC8 y
44 RC7; las invocaciones reales, referencias físicas TEMP y casos adversariales
se ejercitan mediante esas pruebas, sin otro piloto o implementación paralela.

`pip check` nuevo: `No broken requirements found.`, código 0. Git diff --check
sin salida y sin diferencias de archivos registrados o del índice.

Aunque el código no requiere cambios, se ejecuta una suite completa nueva por
la instrucción expresa de recuperación:

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
```

Registro independiente:
`%TEMP%/spica-rc9-recuperacion-suite-5bf06393d37e44c786dbf50f531b1066.log`.
El resultado de esta ejecución y los controles finales se consignan en el cierre
de recuperación que sigue, sin sumar ejecuciones repetidas a los tests únicos.

Solo se añade esta sección a la auditoría. Se verifica que sus 22934 bytes
anteriores permanezcan idénticos, con SHA-256
`cb3bc32d1305d1a98d35bfef96f0c7ab650b3def9d52e5c595c60be53e650fe2`.
El adaptador, las pruebas, el contrato y la política se conservan sin cambios
respecto al inicio de esta recuperación. No se modifica ningún archivo Python.

### Cierre verificado de la recuperación

La suite completa nueva terminó con código 0, sobre el código definitivo
conservado sin modificaciones:

```text
Ran 2373 tests in 1074.835s

OK
```

**2373 aprobadas, 0 fallidas, 0 errores y 0 omitidas**, incluidas las 2332
anteriores a RC9 y sus 41 pruebas nuevas. No se agregaron pruebas durante la
recuperación ni se suman las 123 dirigidas a este total. El registro nuevo no
contiene fallos ni ResourceWarning. Se verificó su final completo en disco;
los resultados no se deducen de la ejecución histórica.

| Comprobación de recuperación | Resultado |
|---|---|
| Dirigidas RC9/RC8/RC7 | 123 aprobadas, cero fallidas/errores; 130.012 s |
| Suite completa nueva | 2373 aprobadas, cero fallidas/errores/omitidas; 1074.835 s |
| pip check nuevo con `.venv -B` | No broken requirements found.; código 0 |
| Sintaxis, definición de pruebas, importación y grafo RC9 | Correctos; 41 pruebas nuevas únicas y ningún ciclo RC9 |
| Adaptador y pruebas | SHA-256 idénticos a los observados al iniciar la recuperación |
| Contrato y política RC9 | SHA-256 idénticos a los observados al iniciar la recuperación |
| Texto anterior de la auditoría | Sus 22934 bytes conservados exactamente; solo se añadieron anexos |
| Temporales de ensayo | Cero directorios residuales spica-rc3-qa-*, spica-rc5-*, spica-rc6-* y .suadc-test-* |
| Git | Misma rama/HEAD; mismos cinco archivos sin seguimiento, sin cambios registrados ni del índice |

SHA-256 del código preservado:

- `admision_exportacion.py`:
  `fb8a2ba56d95855e58a0c5ddceb76d8f0b1a937832cef7fc0d6fe7cb78db3e50`.
- `test_admision_exportacion_rc9.py`:
  `3fb951b3a8f4dcf9b5fc8b58a81516aced7e69c7bd08728daa2974512c235160`.

La nueva suite comenzó a registrar salida el
`2026-11-20T04:17:17.252739+00:00`; control final del registro y temporales:
`2026-11-20T04:36:38.752032+00:00`. Son fechas UTC; la fecha de elaboración
según el contexto del cliente America/Lima es 2026-11-19.

El primer control de temporales de esta recuperación incluyó todos los nombres
con prefijo RC5/RC6 y señaló dos archivos `.log`. Se verificaron tipo y fechas
con lstat, sin seguir enlaces, distinguiendo registros de prueba de directorios
residuales. Son registros del **2026-11-16**, anteriores a RC9; se conservaron
sin leer su contenido ni borrarlos. También se comprobaron únicamente los
metadatos de las tres carpetas `spica-config-test-*` del **2026-10-29** ya
identificadas en la auditoría inicial, dejándolas intactas. No hubo limpieza
correctiva de archivos de trabajo o residuos heredados. La limpieza normal de
las pruebas se limitó a sus propias fixtures temporales sintéticas.

La inspección inicial de procesos mediante CIM no estaba disponible por
permisos; la alternativa de consulta utilizada y la clasificación corregida de
registros TEMP fueron incidencias de verificación, no fallos del producto ni
motivos para modificar código. No se pidió acceso operativo ni se alteraron ACL.

No se hallaron implementaciones pendientes, duplicadas o parcialmente escritas
atribuibles al bloqueo en los archivos revisados. No se reescribió ni se volvió
a implementar RC9. El único cambio de esta recuperación es el anexo en esta
auditoría, con los textos previos preservados. Las comprobaciones finales de
Markdown, UTF-8, espacios, enlaces y git diff --check se realizan sobre este
informe completo, incluidos los archivos que siguen sin seguimiento.

Se mantuvieron cero conexiones externas, instalaciones, descargas, commits,
push y migraciones. No se accedió a RAW, staging, SQLite operativo ni al CSV
PNDA. La revisión del repositorio no constituye una comprobación de integridad
del almacenamiento operativo tras el apagado: no se abrió para hacerla ni se
emite un nuevo dictamen físico o científico sobre sus originales.

Los formatos históricos, las 29 brechas PNDA y las políticas RC3/RC7 permanecen
sin cambios. Los pendientes de conservación del cierre, confianza tras reinicio,
permisos y admisión de dependencias no QA siguen sujetos a revisión; no son
implementaciones inconclusas que deba completar esta recuperación.

Dictamen de recuperación: **TRABAJO RC9 CONSERVADO Y VERIFICADO**. Se mantiene
**APTO CON RESTRICCIONES** para su alcance técnico experimental. No se detectó
un problema de archivos o ejecución que requiera corregir el código por el
bloqueo. No se inician RC10 ni núcleos científicos. Se entrega para revisión.

Control documental final: los cinco archivos RC9 superaron UTF-8, EOF, espacios,
marcadores de conflicto, sintaxis Python y cercas Markdown; sus 26 enlaces
locales son válidos. Los encabezados de recuperación y cierre son únicos. El
primer comprobador efímero de unicidad recibió los acentos con la codificación
predeterminada de la consola; se repitió con UTF-8 explícito y terminó con
código 0. No era un defecto del documento ni requirió modificar código SPICA.
