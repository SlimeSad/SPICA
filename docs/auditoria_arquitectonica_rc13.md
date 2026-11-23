# RC13 — Auditoría arquitectónica y cierre del piloto externo

Fecha de elaboración: **2026-11-23**, America/Lima. Alcance experimental offline.
[Contrato y matriz previa](contrato_precondicion_productora_rc13.md),
[piloto y variantes](piloto_admision_dependencia_rc13.md).

## Recuperación y alcance de RC12

Git inicial: rama `feature/suadc-http`, HEAD
`43ff570170f77de970a0e30a437a3555848fed63`, árbol limpio, sin cambios pendientes.

```text
43ff570 SPICA: auditoria transversal y hoja de ruta arquitectonica RC12
128ada9 SPICA: dictamen experimental de dependencia no QA RC11
98094c1 SPICA: conservacion versionada de evidencias tecnicas RC10
424e585 SPICA: admision controlada de evidencias de exportacion RC9
246bbec SPICA: cierre tecnico verificable de exportacion RC8
```

Se revisaron los cuatro documentos RC12:
[auditoría](auditoria_transversal_arquitectura_rc12.md),
[matriz](matriz_trazabilidad_conexiones_rc12.md),
[decisión contractual](decision_evolucion_cierres_noqa_rc12.md) y
[hoja de ruta](hoja_ruta_priorizada_rc12.md).
Se contrastaron contextos RC1, perfiles RC2, coordinación RC3, linaje RC4,
física RC5, recuperación RC6, integración RC7, cierre RC8, admisión RC9,
historia RC10 y dictamen RC11 con sus implementaciones y fixtures.

La prioridad seleccionada fue una **precondición productora** de la arista
exportar_resultado_json→consumir_exportaciones, sin ejecutor ni ciencia.
La propuesta RC12 de una entrada lateral no es una API ya disponible: RC13
dispone detener la integración si requiere cambiar interfaces estables.
Se explicó esa incompatibilidad **antes de editar código** y se optó por un
adaptador externo que no habilita los inspectores nativos.

Las 17 condiciones PC01–PC17 de RC12 permanecen como puertas del futuro caso
científico, no se declaran satisfechas por este piloto. En particular, perfil/
carga útil del método, metadatos/aplicabilidad, salida científica, linaje del
método y fundamento revisado siguen pendientes. La evolución local de PC11 no
implementa el anfitrión científico, permisos, custodia o el cierre nativo general.
ERS/actas/H0/FUT/G0 no localizadas en RC12 no se reconstruyen ni se homologan aquí.

## Reutilización y cambios

Se crean **cinco archivos**; ningún archivo histórico se modifica:

| Archivo | Responsabilidad |
|---|---|
| [precondicion_productora.py](../src/spica/artefactos/precondicion_productora.py) | Contrato/versionado y selección explícita de perfil, vínculo consumidor y dictamen externo |
| [test_precondicion_productora_rc13.py](../tests/test_precondicion_productora_rc13.py) | Piloto nativo, adversarios, compatibilidad y barreras de efectos |
| [contrato_precondicion_productora_rc13.md](contrato_precondicion_productora_rc13.md) | Matriz previa, identidades, decisiones, confianza y límites |
| [piloto_admision_dependencia_rc13.md](piloto_admision_dependencia_rc13.md) | Componentes ejercidos y variantes A–N |
| Este documento | Evidencia de verificación, riesgos y dictamen |

El adaptador llama a RC11 con su SolicitudDependenciaExportacion tipificada;
no acepta un dictamen favorable del llamador como evidencia. RC11 vuelve a
inspeccionar RC8, contrasta RC9, reúne restricciones y relee RC5/RC10 cuando se
ha solicitado. El informe RC11 permanece completo y con su decisión original.
No se copian sus cotejos, su lista de límites nativos ni el recorrido RC3.

RC13 agrega únicamente la selección versionada y el vínculo con la operación
consumidora **prevista**, entrada y escenario declarados. Si se aporta RC7,
invoca el inspector nativo y verifica que su recuperación pertenezca al inventario
original, composición y vínculo seleccionados. No declara cierre del consumidor.
No se llama recursivamente a RC8/RC11 desde un recorrido RC3: no hay reentrada.

Ningún cambio en RC3, RC7, CierreQA, inicializadores públicos de paquetes,
dependencias, JSON QA `0.1.0`, `rc6.generacion.0.1.0`,
`rc10.evidencias.0.1.0`, formatos 85-J/K o SQLite 85001. No hay nueva tabla,
codec, parser, almacenamiento, scheduler, despachador ni expresión ejecutable.

## Resultados funcionales y confianza

Existe un positivo legítimo **exclusivamente local externo**: RC8 observado,
RC9 válido, capturas locales coherentes, identidades/finalidad/vínculos precisos,
restricciones conservadas y política admitida. El dictamen reutiliza el enum
DecisionDependencia; no cambia la decisión NO_ADMISIBLE del informe RC11.

RC3/RC7 continúan bloqueando la dependencia no QA y sin habilitar `consumidor`.
Se conserva la operación productora INICIADA declarada, su CONCLUIDA observada
separada y la dependiente DECLARADA. Ninguna exportación marca
cierre_qa_coherente_completo=True o introduce contadores QA.

Contradicciones, parciales/fallos/cancelaciones observados, alteración de bytes,
proyectos cruzados y bloqueos aplicables impiden satisfacción. Falta de evidencia
actual/aplicabilidad/física requerida deja pendiente. Historia RC10 íntegra queda
fuera del perfil actual; no se restauran sus testigos. Un DTO positivo o copia
sin comprobación local no satisface la precondición. Exigir autenticidad
independiente o disponibilidad externa no demostrada no produce un positivo.

RC5 demuestra relectura física actual solo en los casos que la exigen, con
bytes/tamaño/SHA cotejados contra la salida. El positivo en memoria no acredita
archivo físico. RC6 comprueba contenido incluido al recuperar; no acredita que
las referencias externas sigan disponibles ni que RC8 se haya ejecutado de nuevo.
RC10 verifica su portador, no transforma hechos históricos en hechos actuales.

## Verificación ejecutada

Intérprete confirmado mediante `.venv\Scripts\python.exe -B`: Python **3.15.1**,
HTTPX **0.28.1**, SQLite **3.53.4**. No se instala ni actualiza ningún paquete.
PYTHONPATH se configura exclusivamente en el entorno del proceso, con `src` y
`tests`; PYTHONDONTWRITEBYTECODE=1. No se editan archivos de configuración.

Pruebas dirigidas sobre el código definitivo:

```powershell
.\.venv\Scripts\python.exe -B -m unittest test_precondicion_productora_rc13 test_coordinacion_rc3 test_integracion_artefactos_rc7 test_cierre_exportacion_rc8 test_admision_exportacion_rc9 test_conservacion_evidencias_rc10 test_dependencia_noqa_rc11 -v
```

```text
Ran 298 tests in 190.070s
OK
```

**298 aprobadas, cero fallidas/errores/omitidas**, incluidas **43 nuevas RC13**
y 255 regresiones pertinentes. Log completo fuera de Git:
`%TEMP%\spica-rc13-dirigidas-2ee66a34cb794e00acc1f1cd7255ec19.log`.

Incidencia previa de entorno: un primer ensayo de 42 pruebas, antes de añadir
la barrera de proceso RC13, terminó con **34 aprobadas, una fallida y siete
errores** por acceso denegado al TEMP protegido desde el sandbox. Se repitió
fuera del sandbox: **42/42, 9.955 s**, sin modificar los controles ni omitir
casos. Después se añadió la barrera y se ejecutaron las 298 anteriores.
No se contabiliza el primer ensayo como aprobado.

Los 12 directorios vacíos de aquel ensayo se identificaron por sus nombres,
ventana UTC de creación y ausencia de contenido/enlaces. Una primera comprobación
de limpieza se detuvo sin borrar por comparación de hora local/UTC; se corrigió
el comando a límites UTC explícitos. Se retiraron solo esos 12 directorios vacíos,
sin borrado recursivo ni tocar temporales ajenos. Los tests que usan RC5/RC6
comprueban además la desaparición de sus raíces al salir de los contextos.

Revisión estática actual: **204 archivos Python** (127 src, nueve herramientas y
68 test_) parseados/compilados en memoria, sin errores de sintaxis ni definiciones
duplicadas en el mismo ámbito. **2489 métodos test_ únicos estáticos**, que no se
presentan como pruebas aprobadas por ese recuento. Grafo AST de imports explícitos
inmediatos: **127 módulos, 463 aristas, cero ciclos**; ningún módulo estable
importa el adaptador RC13. No se promete ausencia de ciclos de imports diferidos
en todo SPICA: RC12 ya documenta dos grupos históricos. Se prueban dos órdenes de
importación en intérpretes separados.

Huellas del código congelado antes de la suite completa:

```text
src/spica/artefactos/precondicion_productora.py
3589b9e3861eb07af1356abd5f1d2eb6311253dd9c2e929b58459ffcb6377eec
tests/test_precondicion_productora_rc13.py
94ac3a5904bd89468cc91c9791f870de3b7c4b86559c92d6cec93e2b4d44ec9b
```

Suite completa ejecutada después de congelar el código y terminar las dirigidas:

```powershell
$env:PYTHONPATH=(Join-Path $PWD 'src')+';'+(Join-Path $PWD 'tests')
$env:PYTHONDONTWRITEBYTECODE='1'
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -B -m pip check
git diff --check
git status --short
```

```text
Ran 2489 tests in 1104.126s
OK

No broken requirements found.
```

**2489 aprobadas, cero fallidas, cero errores y cero omitidas**. Se ejecutaron
realmente las 2446 anteriores y las 43 nuevas, no solo su recuento estático.
La suite final terminó con código 0; no fue interrumpida. `pip check` código 0.
Log íntegro fuera de Git:
`%TEMP%\spica-rc13-suite-final-b054181f1c8840ac81188a1eff68b42b.log`
(798998 bytes). El log dirigido tiene 102980 bytes. Ninguno contiene marcadores
FAIL/ERROR/skip ni ResourceWarning. Las huellas de ambos archivos Python nuevos
coinciden antes/después de la suite. Solo se editó documentación durante ella.

El contraste de nombres TEMP antes/después de la suite encontró los mismos
**113 directorios SPICA previos**, cero nuevos residuales y cero previos ausentes.
No se abrió su contenido ni se eliminaron. Los dos logs de esta verificación
se conservan deliberadamente como archivos en TEMP, fuera de Git.

Los cinco archivos nuevos se revisan expresamente, pues git diff --check no
incluye los no registrados: UTF-8, fin de archivo, blancos finales, conflictos,
sintaxis, fences/tablas Markdown y enlaces locales. No se comprueban enlaces
externos ni se realiza navegación. El expediente contiene tres documentos,
diez tablas y 21 enlaces locales a archivos existentes.

Estado final: misma rama y HEAD del inicio. `git diff --check`,
`git diff HEAD --exit-code` y `git diff --cached --exit-code` terminan sin salida,
código 0. No hay cambios a archivos registrados ni al índice. Resultado completo
de `git status --short`:

```text
?? docs/auditoria_arquitectonica_rc13.md
?? docs/contrato_precondicion_productora_rc13.md
?? docs/piloto_admision_dependencia_rc13.md
?? src/spica/artefactos/precondicion_productora.py
?? tests/test_precondicion_productora_rc13.py
```

## Conexiones y condiciones que siguen abiertas

Las definiciones se recuperaron de la [matriz original 85-F](matriz_dependencias_integracion_paso85f.md)
y la [trazabilidad RC12](matriz_trazabilidad_conexiones_rc12.md):

| Conexión original | Estado y efecto de RC13 |
|---|---|
| M03 C08→C09/C02: ejecutor PlanConsulta/traducción de selectores a HTTP | PENDIENTE; RC13 no traduce ni ejecuta planes |
| M16 C12→C02/C11: recomendación de readquisición→efecto | PENDIENTE; no hook GET/ingesta ni permiso efectivo |
| M26 C20→C21/C24/C19: evidencia documental→uso QA/aplicabilidad revisado | PENDIENTE; diagnóstico no se transforma en fundamento aprobado o permiso |
| M32 resultados científicos→almacenamiento/exportación | PENDIENTE con avances contractuales/físicos RC4–RC6 previos; no productor, formato ni cadena científica nueva |

Las [29 brechas PNDA](brechas_reconciliadas_pnda_paso84i.md) mantienen **2 resueltas,
17 parcialmente documentadas, 8 pendientes y 2 contradicciones documentadas**;
no se altera ninguna fila ni se verifica evidencia institucional privada.
INGEMMET `/query` sigue NO AUTORIZADO. Las 28 responsabilidades, 33 conexiones
y seis grupos auxiliares RC12 no se renumeran ni se convierten en un porcentaje.

## Riesgos, puertas y recomendación

| Hallazgo / gravedad condicionada | Evidencia y tratamiento |
|---|---|
| R13-01, bloqueante para admisión efectiva nativa | RC3 solo CierreQA y RC7 exige su flag: se detiene esa integración. El positivo externo no cierra AT01 de RC12 |
| R13-02, alta si se exige autenticidad independiente | Capturas y snapshot privados solo cooperativos; no resistencia frente a Python hostil, firma o identidad institucional. Pendiente/no admisible según política |
| R13-03, media de mantenimiento | Dependencia de APIs/helpers nativos RC11 y de sus códigos/semántica. No se copia su lógica; pruebas de regresión y formatos históricos intactos |
| R13-04, media al extrapolar recursos/persistencia | Cotas nativas no son reserva RSS/disco ni plazo forzoso; TEMP en la misma cuenta/dominio, sin garantía eléctrica/custodia. No prometer uso operativo |
| R13-05, alta si se atribuye cierre al consumidor | RC9 valida entrada pero no captura operacion_id dependiente. RC13 solo identifica destino previsto; no acredita ni reescribe su ejecución |

No se detecta un defecto crítico nuevo del código estable mediante este piloto.
No se elimina por ello la posibilidad de defectos fuera de los recorridos
ensayados. Los límites científicos, efectos externos, custodia, permisos y
fuentes formales de RC12 siguen pendientes cuando el uso los requiera.

Siguiente prioridad propuesta: **someter a revisión la evolución explícita de
las interfaces RC3/RC7 para una entrada lateral única de esta precondición**,
con versión/semántica de informe acordadas, recorrido compartido y preparación
de evidencia fuera de él. No implementar silenciosamente esa evolución ni otro
dictamen paralelo. M26 mantiene su revisión independiente antes del uso científico.
No se inicia RC14 ni se autorizan efectos M03/M16 o núcleos científicos.

Dictamen del alcance implementado: **APTO CON RESTRICCIONES para revisión del
piloto externo**; admisión nativa no QA aún bloqueada. No se declara terminada
SPICA ni conformidad científica o formal.

Cero conexiones/GET/descargas/instalaciones/migraciones/commits/push. No se accede
a CSV PNDA, RAW operativo, staging ni SQLite operativo. Esta confirmación describe
las acciones y barreras del trabajo: no es un diagnóstico físico actual de
originales que deliberadamente no se abrieron.
