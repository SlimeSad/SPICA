# RC11 — Auditoría de la dependencia técnica de exportación

Fecha: **2026-11-20**, America/Lima. Alcance: memoria y TEMP sintético.
[Contrato](contrato_dependencia_noqa_rc11.md) y
[piloto reproducible](piloto_dependencia_tecnica_rc11.md).

## Estado inicial y compatibilidad de la decisión

Rama `feature/suadc-http`, HEAD
`98094c1eb7bd7cf679a2f13547fde2be4919dc0c`. `git status` inicialmente limpio.
RC10 está registrado; no se reanuda un WIP ni se sobrescriben implementaciones.

```text
98094c1 SPICA: conservacion versionada de evidencias tecnicas RC10
424e585 SPICA: admision controlada de evidencias de exportacion RC9
246bbec SPICA: cierre tecnico verificable de exportacion RC8
c1b224e SPICA: integracion de artefactos y coordinacion RC7
367e95f SPICA: conservacion y recuperacion versionada de artefactos RC6
```

Se revisaron los tres documentos RC10: [contrato](contrato_conservacion_evidencias_rc10.md),
[recuperación](recuperacion_evidencias_tecnicas_rc10.md) y
[auditoría](auditoria_arquitectonica_rc10.md), incluida su recomendación final.
También se inspeccionaron las API RC3/RC7 efectivas, contratos RC8/RC9, operaciones
RC1, perfiles RC2, linaje RC4, física RC5, conservación RC6, la
[hoja 85-M](hoja_ruta_continuidad_arquitectonica_paso85m.md) y las definiciones
originales de conexiones. La recomendación RC10 es acordar confianza y estudiar
esta arista, sin convertir la historia en una captura actual ni cierre QA.

La arista real seleccionada es exclusivamente `exportar_resultado_json →
consumir_exportaciones`. Ambos componentes ya existen y se invocan realmente
en fixtures. Se puede describir la relación mediante contextos y arista RC3;
no existe una vía contractual para que su cierre RC8 satisfaga esa dependencia.
El consumidor RC9 tampoco registra un cierre propio de operación RC3.

Antes de implementar se informó esta incompatibilidad. Se eligió el dictamen
externo que el encargo permite expresamente. Se suspendió la habilitación
efectiva RC3/RC7; no se modificó ninguna API estable para aparentar satisfacción.

## Cambios y reutilización

Se crean únicamente cinco archivos; ningún archivo histórico cambia:

| Archivo nuevo | Responsabilidad |
|---|---|
| [dependencia_exportacion.py](../src/spica/artefactos/dependencia_exportacion.py) | Política tipada específica, asociación de una arista ya existente y dictamen externo con diagnósticos deterministas |
| [test_dependencia_noqa_rc11.py](../tests/test_dependencia_noqa_rc11.py) | 44 pruebas nuevas, fixtures nativos y TEMP aislado; sin TestCase importados duplicados |
| [contrato_dependencia_noqa_rc11.md](contrato_dependencia_noqa_rc11.md) | Política, identidades, evidencias, restricciones, estados y límites |
| [piloto_dependencia_tecnica_rc11.md](piloto_dependencia_tecnica_rc11.md) | Invocaciones reales y escenarios locales/históricos, sin una variante positiva artificial |
| Este documento | Auditoría, verificaciones, conexiones, riesgos y dictamen |

| Componente reutilizado | Uso efectivo RC11 | Límite conservado |
|---|---|---|
| RC1 | ContextoProyecto, ContextoOperacion, VinculoResultadoQA, validación de restricciones y literales | Identidades declaradas; no permiso ni ejecución certificada |
| RC2 | EntradaPerfil y perfiles nativos de los artefactos; resultados de compatibilidad declarados siguen en RC3/RC4 | No se inventa una comparación entre disciplinas o variables |
| RC3 | Informe nativo obtenido mediante inspeccionar_linaje, operaciones y arista existentes | Ningún cierre no QA admitido ni estado promovido |
| RC4 | Inventario, referencia/revisión, producción, contenido y restricciones/orígenes | Descriptores intactos; preparado no se convierte en RAW |
| RC5 | Relectura física actual mediante la política física RC9 existente | TEMP controlado; no localizadores históricos libres ni custodia |
| RC6 | Conservación/recuperación física del portador vía RC10 | Perfil cerrado sin nuevos tipos, campos o formatos |
| RC7 | Unión de restricciones; prueba real de inspeccionar_integracion | El portador RC10 no reemplaza el inventario original; no se habilita el consumidor |
| RC8 | Inspección nativa de captura, productor/versión, estado y JSON de salida | Captura local cooperativa, sin firma |
| RC9 | Informe de consumo/admisión existente, testigo local y helper físico | No se vuelve a despachar la operación consumidora desde el dictamen |
| RC10 | Recuperación nativa nueva del expediente y portador; hechos históricos íntegros | Sin testigos restaurados, admisión actual ni promoción de historia |

No se agrega motor QA, exportador, consumidor, parser, codec, grafo de operación,
scheduler, almacén de evidencias, tabla SQL, autenticador o sistema de permisos.
El módulo nuevo se importa explícitamente; no cambia ningún `__init__.py`.

## Evidencias y resultado del piloto ejecutado

Piloto adicional ejecutado con `.venv` el 2026-11-20; cortes de informe a las
**05:56:51 y 05:56:52 UTC**. Proyectos `proyecto-RC8` y `proyecto-RC11-B`.
Cada exportación produjo **3853 bytes UTF-8** en memoria, con la misma huella:

```text
096a53b91c4c7d23b83feb572ebb6bd700a6726a39c1b2c923fa35913d39a483
```

La huella se volvió a comprobar físicamente en RC5 para las salidas sintéticas.
No es el hash de un archivo SENAMHI ni de un original operativo. Los proyectos,
objetos y expedientes se mantuvieron independientes. Los temporales de ambos
proyectos se retiraron al terminar sus respectivos contextos.

| Hecho observado | Resultado en ambos proyectos |
|---|---|
| Cierre RC8 / admisión RC9 locales | Comprobados para su finalidad técnica propia |
| Correspondencias RC11 | APTO_ESTRUCTURALMENTE |
| Estado global RC3 / RC4 | PENDIENTE_DE_EVIDENCIA; informes conservados |
| Decisión de dependencia local | NO_ADMISIBLE por política RC3/RC7 |
| Variante sin RC9 | PENDIENTE_DE_EVIDENCIA |
| Variante con bloqueo aplicable | NO_SATISFECHA |
| Física actual RC5 correcta | comprobado_localmente; decisión sigue NO_ADMISIBLE |
| Recuperación histórica RC10 | cerrada_verificada_en_alcance; decisión sigue NO_ADMISIBLE |
| Testigos RC8 / RC9 recuperados | False / False; no restaurados |
| Prueba nativa RC7 sobre portador | PENDIENTE_DE_EVIDENCIA; habilitadas vacías |
| Restricciones heredadas del caso base | Tres, conservadas con procedencia |

SATISFECHA no se implementa como resultado alcanzable: falta el contrato de
admisión no QA. Esta ausencia se declara y prueba; no se inventa un cierre QA ni
una autorización. La dependencia puede tener correspondencias comprobadas y
seguir sin ser admisible. El caso de un fallo histórico conserva su incumplimiento.

El dictamen separa estado declarado de operación, snapshot observado, admisión
local, artefacto lógico, materialización, integridad física actual, historia,
estado de dependencia y revisión científica. La captura no se autentica por
preservar su JSON. Una física correcta no convierte un cierre en admisible.

Las restricciones heredadas y nuevas conservan orígenes. Bloqueos aplicables
causan rechazo; usos desconocidos dejan pendientes; los no aplicables a este
consumo permanecen visibles. Una repetición no cuenta como evidencia adicional.
Contradicciones documentales/estructurales no se suprimen por tener bytes válidos.

## Verificación ejecutada

Intérprete comprobado: **Python 3.15.1**, HTTPX **0.28.1**, SQLite **3.53.4**.
Se usó exclusivamente `.venv\Scripts\python.exe -B`; no se instalaron paquetes.
PYTHONPATH se configuró solo en el proceso con `src` y `tests`, sin archivos de
configuración ni cambios al entorno virtual.

Comandos dirigidos realmente ejecutados:

```powershell
.\.venv\Scripts\python.exe -B -m unittest test_dependencia_noqa_rc11 test_coordinacion_rc3 test_integracion_artefactos_rc7 test_cierre_exportacion_rc8 test_admision_exportacion_rc9 test_conservacion_evidencias_rc10 -v
.\.venv\Scripts\python.exe -B -m unittest test_dependencia_noqa_rc11 -v
```

Primera combinación aprobada: **250 pruebas**, 172.372 s, 0 fallidas/errores.
Incluía las 39 RC11 entonces existentes y 211 regresiones RC3/RC7/RC8/RC9/RC10.
Tras dos controles adicionales y cinco casos nuevos, la ejecución dirigida
definitiva RC11 aprobó **44 pruebas**, 23.810 s, 0 fallidas/errores. No se suman
ejecuciones repetidas como pruebas distintas. Dos ejecuciones preliminares
detectaron problemas de los fixtures/clasificación propios y fueron corregidos;
no se presentan como aprobadas.

Las 2402 pruebas anteriores dejaron de ser solo un antecedente: se ejecutaron
de nuevo, junto con las 44 nuevas, sobre el código definitivo sin cambios
durante la ejecución. Las huellas de ambos archivos Python coincidieron antes
y después de la suite.

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -B -m pip check
git diff --check
git status --short
```

Resultado íntegro final de unittest, código de salida **0**:

```text
----------------------------------------------------------------------
Ran 2446 tests in 1009.124s

OK
```

**2446 aprobadas, 0 fallidas, 0 errores, 0 omitidas.** Sin ResourceWarning.
El total corresponde a 2402 anteriores más 44 nuevas, no a la suma de
ejecuciones dirigidas repetidas. El registro íntegro de 784302 bytes se
conserva fuera de Git en TEMP:
`spica-rc11-suite-final-3d9664b3588b45f4902f62017167d16a.log`.

Después de la suite se ejecutó `pip check` con el mismo intérprete, salida **0**:

```text
No broken requirements found.
```

`git diff --check` y `git diff HEAD --exit-code`: salida 0, sin texto.
Índice y archivos históricos registrados intactos. Los cinco archivos nuevos
sin seguimiento se examinaron expresamente; no dependen de que git diff los
incluya. UTF-8, fin de archivo, espacios, delimitadores Markdown y **21 enlaces
locales** correctos; ninguna comprobación de enlaces hizo conexiones externas.

Los contextos nativos retiraron sus directorios propios. Al terminar no quedó
ningún directorio TEMP `spica-*` creado el 2026-11-20. El registro de pruebas se
conserva deliberadamente como archivo de diagnóstico. No se borraron ni
examinaron los contenidos de directorios TEMP históricos ajenos al incremento.

Comprobaciones estáticas ya ejecutadas: AST, compilación en memoria sin pyc,
UTF-8, fin de archivo, espacios finales, nombres duplicados dentro del mismo
ámbito e importación explícita RC11 correctos. La búsqueda de referencias al
módulo nuevo solo encuentra el propio módulo y sus pruebas; ningún módulo
estable lo importa, por lo que no introduce un ciclo de importación de retorno.
No hay expresiones de reglas, plugins dinámicos ni código desde archivos.

Huellas de código congelado antes de iniciar la suite completa:

```text
dependencia_exportacion.py
f5642aad33a6027c27fe23e31ba39907a80981464bd4033add4b931949eff5db
test_dependencia_noqa_rc11.py
e7cde52fc569127a77412ef58cba9f3c8d235b13ea0e37e3e70d503a5088b083
```

## Conexiones arquitectónicas y exclusiones

Las definiciones se recuperaron de la
[matriz original 85-F](matriz_dependencias_integracion_paso85f.md), sin renumerar
ni interpretar la hoja 85-M como si sus grupos fueran los incrementos RC actuales.

| Conexión original | Estado después de RC11 |
|---|---|
| M03, C08→C09/C02: PlanConsulta→ejecutor/selectores HTTP | P; no se crea un ejecutor ni se autoriza GET |
| M16, C12→C02/C11: recomendación de readquisición→GET/manual con hook/ejecutor aprobado | P; ningún hook operativo |
| M26, C20→C21/C24/C19: evidencia documental→QA/aplicabilidad/operación mediante vínculo revisado | P; el dictamen técnico sintético no aprueba evidencia institucional |
| M32, resultados científicos futuros→almacenamiento/exportación científica y linaje transversal | P; JSON QA Nivel 0 y expediente técnico no son resultados científicos futuros |

Las [29 brechas PNDA](brechas_reconciliadas_pnda_paso84i.md) permanecen intactas:
2 resueltas con evidencia, 17 parcialmente documentadas, 8 pendientes y 2
contradicciones documentadas. INGEMMET `/query` sigue NO AUTORIZADO.

JSON QA 0.1.0, SQLite 85001, 85-J/K, `rc6.generacion.0.1.0` y
`rc10.evidencias.0.1.0` no cambian. No se alteran contextos, observaciones,
originales ni estados históricos. El dictamen nuevo no se serializa dentro de
perfiles históricos. Cero conexiones, GET, descargas, instalaciones, migraciones,
commits o push. Cero lecturas del CSV PNDA, RAW, staging o SQLite operativos.
No se ofrece una nueva comprobación de integridad de originales reales que no
se abrieron. Las pruebas y el piloto solo escriben fixtures TEMP propios.

## Riesgos y decisiones pendientes

| Gravedad / ámbito | Hallazgo y tratamiento |
|---|---|
| Bloqueante para habilitación efectiva | RC3/RC7 solo reconocen determinados cierres QA. Se detuvo esa parte; RC11 emite exclusivamente dictamen externo |
| Alta para uso operativo o autenticado | Testigos cooperativos y controles RC10 sin firma no acreditan identidad independiente, permiso o protección ante Python hostil. Exigir autenticidad deja pendiente |
| Media, mantenimiento | Acoplamiento localizado a `_fisica` RC9, unión RC7, ordenado de diagnósticos RC3 y códigos nativos proyectados. Revisión/versionado si cambian; pruebas protegen comportamiento actual |
| Media, temporalidad | La relectura física describe ese instante. No se garantiza integridad futura ni disponibilidad de referencias externas |
| Límite experimental heredado | Uso secuencial cooperativo, sin concurrencia hostil, transacción global, custodia independiente o durabilidad ante apagado |
| Límite de privacidad heredado | TEMP/0700 no demuestra DACL Windows ni confidencialidad del contenido; no se cambian ACL |

No se amplía este dictamen a otros productores, disciplinas, instituciones o
reglas científicas. La aptitud de una observación o autorización de redistribución
no se deduce de consumo JSON, SHA ni pruebas unitarias.

Antes de una eventual admisión efectiva hay que revisar qué clase de cierre
no QA aceptaría RC3, qué identidad de ejecución dependiente debe capturarse,
cuál es la confianza mínima y cómo distinguir una evidencia histórica de una
nueva comprobación. RC7 necesitaría también una asociación explícita del
inventario original con las evidencias, sin tratar el portador como ese inventario.
Estas decisiones quedan propuestas para revisión; no se implementa RC12 ni se
inician núcleos científicos.

## Estado final y dictamen

Rama y HEAD iguales al inicio: `feature/suadc-http` /
`98094c1eb7bd7cf679a2f13547fde2be4919dc0c`. No hay cambios en archivos
registrados ni en el índice. Salida final de `git status --short`:

```text
?? docs/auditoria_arquitectonica_rc11.md
?? docs/contrato_dependencia_noqa_rc11.md
?? docs/piloto_dependencia_tecnica_rc11.md
?? src/spica/artefactos/dependencia_exportacion.py
?? tests/test_dependencia_noqa_rc11.py
```

**Dictamen: APTO CON RESTRICCIONES para el dictamen externo experimental RC11.**
Se comprueban las correspondencias de la arista concreta, se preservan contratos,
restricciones y estados, se distinguen capturas locales de historia y se rechazan
contradicciones y faltantes sin fabricar satisfacción. La suite definitiva no
detectó regresiones. No quedan correcciones bloqueantes conocidas para este
alcance externo, acotado y cooperativo.

**La habilitación efectiva de la dependencia no QA continúa bloqueada** por los
contratos RC3/RC7. No se declara implementada ni aprobada. Antes de modificar
esa frontera debe revisarse la clase de cierre, la identidad del consumidor y
el nivel de confianza exigido. Se mantienen las exclusiones operativas y los
riesgos documentados. No se autoriza ninguna operación adicional ni se declara
terminada la arquitectura integral. Se espera revisión del equipo; no se inicia
RC12 ni los núcleos científicos y no se realizan commits.
