# PASO 85-K — Piloto de respaldo y restauración

Fecha de elaboración: 2026-11-12, America/Lima. Base `d7d7b8c`, rama
`feature/suadc-http`, árbol inicialmente limpio. Arquitectura y protocolos:
[diseño](arquitectura_respaldo_restauracion_paso85k.md). Riesgos:
[custodia](brechas_custodia_paso85k.md).

## Alcance y evidencia de ensayo

Solo fixtures sintéticas del arnés existente 85-G y directorios TEMP exclusivos.
No se abre RAW/staging/SQLite operativo, CSV institucional o evidencia PNDA real.
La guardia de Python heredada por procesos hijos bloquea conexiones/DNS y acceso
a rutas operativas conocidas. No es una frontera OS ni cubre código nativo hostil.
El adaptador 85-K no llama a HTTP ni ejecuta QA. La preparación de ciertas fixtures
y las pruebas históricas usan MockTransport del arnés: solicitudes simuladas, sin
GET externo, red o descarga. La fixture cancelada no llega a esa simulación.

El ensayo conserva la evidencia realmente producida, la respalda, cierra el
productor y restaura en otro proceso/raíz. La comprobación final usa el lector
85-J y cotejo 85-H, no repite la adquisición ni el motor al restaurar.
Los hashes se calculan por lectura física de archivos, incluido el snapshot
producido por la API SQLite backup; no son solo comparaciones de metadatos.

Las raíces de datos se eliminan al salir de sus contextos propietarios tras
comprobar éxito o inspeccionar parciales. El gestor no repara ni borra evidencia
incierta. Los registros técnicos del ensayo quedan en el TEMP privado de auditoría,
separados del repositorio y de cualquier almacenamiento operativo.

## Matriz adversarial

Los siguientes casos se ejercitaron en las pruebas dirigidas. Disco/permisos,
sustitución de descriptor y enlaces lógicos se inyectan de forma controlada;
no se afirma haber llenado un volumen o atacado un sistema real.

| Situación | Comprobación ejercitada |
|---|---|
| Conservación antes de commit | Rechazar captura antes de reservar destino |
| Ausencia/corrupción en origen | Lector 85-J bloquea; no reconstruir ni descargar |
| WAL/SHM/journal, SQLite corrupto/versión distinta | Rechazar perfil, sin migración |
| Varias ejecuciones, archivos huérfanos/ajenos o marcador pendiente | Rechazar generación ambigua; conservar originales |
| Copias físicas | Inodos independientes origen→respaldo→restauración; una alteración posterior no se propaga |
| Alterar/borrar archivos del respaldo | Rechazar por tamaño/SHA/inventario antes de crear destino |
| Cambiar SQL y recalcular su SHA | Rechazar por generación lógica distinta |
| Cambiar identidades, restricciones o errores del manifiesto | Rechazar contra cuerpos/SQL aunque se reselle su hash local |
| JSON duplicado/profundo o versión desconocida | Rechazar sin ejecución de código desde archivos |
| Rutas ajenas, ADS, escape, symlink/junction, hardlink externo | Rechazar; pruebas de enlaces lógicos por inyección, hardlink físico real en TEMP |
| Destino existente, incluido parcial | No sobrescribir, adoptar ni reintentar automáticamente |
| Espacio/permisos/disco y escritura corta | Detener; no publicar cierre; diagnósticos cerrados |
| Cancelación y plazo | Interrumpir cooperativamente sin esperas artificiales |
| Interrupción antes del sello de respaldo | Conservar intención/archivos; sin manifiesto final |
| Interrupción tras enlace exclusivo | Conservar ambos nombres pendientes; no declarar cierre |
| Restauración interrumpida antes de publicar | Conservar intención propia y copias; lector sin VERIFICADA |
| Cambio SQL durante captura | Rechazar diferencia de generación y dejar parcial |
| Segundo escritor cooperativo | No entra mientras captura mantiene el marcador |
| Historias cancelada, fallida y parcial | Recuperar estados/errores/nativos exactos sin promoción |
| Productor terminado, restaurador nuevo | Recuperar trío/IDs/estados/restricciones sin repetir ejecución |

Los casos inyectados no acreditan una pérdida eléctrica real, un ataque concurrente
o permisos de todo sistema Windows. No se resuelve automáticamente un parcial.
No hay retención, reanudación, deduplicación entre backups ni catálogo de respaldos.
Nuevas capturas de la misma generación tienen IDs de respaldo distintos. Repetir
en la misma raíz siempre se rechaza: no se promete idempotencia de escritura.

## Piloto medido y procesos independientes

Además de la prueba unitaria entre procesos, un arnés de medición privado en TEMP
registró los cuerpos/controles y conteos reales de una ejecución sintética completa.
No se modificó código para producir estas cifras. Captura, según reloj local UTC:
**2026-11-12T07:09:53.304731+00:00**. No es un sello de tiempo independiente.
Productor/responsable del respaldo: **PID 1872**, terminado antes de iniciar el
restaurador **PID 11008**. El restaurador tiene bloqueado el ejecutor del arnés;
lee evidencia, no repite su producción.

| Identidad | Valor preservado o creado |
|---|---|
| Instancia de origen y restaurada | `d6b239df75c84130a5bf30014e419c60` |
| Ejecución | `ejecucion-85k-medicion` |
| Conservación | `188631abb169443db0e40afd620f9050` |
| Activo histórico de la fixture | `0072a5fd6bfc4ca8960c7be5f250fb23` |
| Proyecto / entrada / evaluación | `proyecto-ficticio-85g` / `entrada-85k` / `evaluacion-85k` |
| Respaldo nuevo | `2e34d431cccb4eb8bffd80d82d995edc` |
| Operación de restauración nueva | `9828f1d1e4d643f1a62f3a4303240c55` |

Generación lógica:
`2aca94c12895f89a46c50a834b48ce8acbd45f7d52940f286a08808e5f996829`.
SHA del manifiesto de respaldo entregado como control:
`049614b310ae7a44f6b85e8c973910a7d810a51fc5c7da272e0e8d03205e371b`.
Son controles locales, no autenticidad independiente.

Inventario físico medido en el respaldo y contrastado durante restauración:

| Rol | Bytes | SHA-256 |
|---|---:|---|
| Intención | 137 | `9827ee05d270da6e0c5db25f3d11f839ddc5cf3059e1dc19b16b5efde6c6cfac` |
| SQLite | 110592 | `e08805567adfe6aa7377d0a1151c295c0c5d03815f2a6ecb2b4c2cfb32db4b4b` |
| Marcador | 103 | `c7165effbe2f6e7d0c957b38795b18d6188744043f60fc093c25bbac61a1309a` |
| Informe tipado | 3151974 | `0cc7dcacce73da82c47daa47f88cdf7b2fc5abb474d44518d7f2c35bcd3147e6` |
| Traza | 840260 | `7f9b67f629548726f1f32f24b1082c38bcca980e340eb2054199053654337aee` |
| Referencia | 183 | `087e67cb7b3efb89d0598c0eacfbcfcf4f324e7eb9b8ff86ce5d7dbaf51637d0` |
| Manifiesto 85-J | 1503 | `41925b9645b65a3219a1e9efa6eb7eece0d56dd716978202a84c00197a09cbf2` |

El SQLite es el snapshot producido por la API backup. Los bytes de la intención
de respaldo se verifican pero no se incorporan como un artefacto nuevo al almacén
restaurado. Los otros seis archivos sí se copian con hashes exactos.
La generación lógica y la igualdad física son comprobaciones diferentes.

Resultado de ambas reproducciones en origen y restauración, calculado desde los
nativos e informes, no mediante contadores constantes:

| Medida | Reproducción A | Reproducción B |
|---|---:|---:|
| Registros examinados | 2 | 2 |
| Reglas ejecutadas | 22 | 22 |
| Resultados individuales | 60 | 60 |
| Comprobación satisfecha | 34 | 34 |
| No evaluado | 26 | 26 |
| Restricciones informativas | 60 | 60 |
| Restricciones bloqueantes | 206 | 206 |

Las reglas pueden emitir resultados por campo: 22 reglas no significan 22
resultados por registro. Las dos reproducciones reutilizan las mismas dos filas;
120 resultados emitidos no equivalen a 120 observaciones distintas.
El lector restaurado devolvió `verificada_en_alcance`, historia
`concluida_estructuralmente`, conservación `conservada`, cotejo 85-H coherente,
sin huérfanos ni temporales. Todas las restricciones globales coinciden; permisos,
autenticidad y ciencia siguen False. Los otros estados históricos se comprueban
en pruebas dirigidas, con igualdad completa del informe, incluidos errores.

El contrato histórico conserva 572 bytes y SHA
`6894bcce331d4af7db8e4a2f6008a8617604d01e8dbf4cc9805dc8cf37e8ee1b`.
Ese RAW ya fue eliminado por 85-G: **no se recuperó ni revalidó físicamente a
partir de la traza**. Se restauraron los artefactos de evidencia, no aquel original.
Tras medir, el propietario eliminó únicamente las tres raíces TEMP del ensayo;
el registro técnico confirma su ausencia. No quedó un almacén permanente nuevo.

## Interrupciones de proceso reproducidas

Además de BaseException inyectadas en pruebas, dos procesos propios terminaron
mediante `os._exit`, sin ejecutar sus bloques de cierre:

| Corte | Salida | Evidencia inspeccionada después |
|---|---:|---|
| Antes de publicar el respaldo | 71 | Intención y copias conservadas, sin sello; lock de origen conservado, lector `revision_necesaria` |
| Antes de publicar la restauración | 72 | Lock e intención del destino conservados; lector `revision_necesaria`; respaldo de entrada sigue verificable |

No se retiraron marcadores para continuar ni se reintentó la operación. Después
de registrar el estado, los contextos propietarios eliminaron sus fixtures TEMP.
Esto no es GC del gestor ni un procedimiento autorizado para datos operativos.
No se reprodujo una pérdida eléctrica, corrupción de hardware o recuperación
automática. Un proceso puede terminar sin flush/fsync de metadatos de directorio;
esa durabilidad permanece sin demostrar.

## Verificaciones ejecutadas

Intérprete confirmado: **Python 3.15.1**, `.venv`, HTTPX **0.28.1**, SQLite
**3.53.4**. Se usa `-B` y `PYTHONPATH` temporal con `src`, raíz del checkout,
`tests` y guardia externa; no se cambia ningún archivo de configuración.

Pruebas dirigidas ejecutadas antes de la suite:

| Ejecución | Resultado | Duración |
|---|---|---|
| Inicial, 36 métodos | 35 aprobados, 1 fallo, 0 errores | 133.603 s |
| Corrección y ampliación, 42 métodos | 42 aprobados, 0 fallos/errores | 145.989 s |
| Código final congelado, 43 métodos | 43 aprobados, 0 fallos/errores | 141.845 s |

El fallo inicial era una expectativa de diagnóstico: el caso multiejecución fue
rechazado por exceso de referencias antes de clasificarse como generación ambigua.
Se ordenó esa comprobación para producir el diagnóstico específico. No se aceptó
una captura inconsistente. Después se completaron las condiciones/limitaciones
del manifiesto y la comparación explícita de identidades entre procesos.
La última tanda verifica con SHA que herramienta y pruebas no cambiaron durante
la ejecución. No se añadieron métodos para aumentar artificialmente el total:
los escenarios relacionados se ejercitan en subTests sin contarlos como métodos.

Comando dirigido (salida completa en log TEMP):

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p test_respaldo_linaje_85k.py -v
```

La suite final se ejecutó **una sola vez**, con el mismo código congelado de
las últimas dirigidas. Resultado completo:

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
```

```text
Ran 1884 tests in 859.341s

OK
```

**1884 aprobadas, 0 fallos, 0 errores y 0 omitidas**. Se identificaron estáticamente
1841 métodos históricos y 43 nuevos; los 1884 IDs realmente ejecutados coinciden
exactamente, sin duplicados, faltantes o inesperados. No se informa la base
histórica como si se hubiese ejecutado por inferencia: sus IDs están en el log.
Las huellas SHA del código de src, herramientas, tests y archivos de configuración
controlados coinciden antes y después. No se cambió código tras las dirigidas.

```powershell
.\.venv\Scripts\python.exe -B -m pip check
```

```text
No broken requirements found.
```

Código de salida 0 en ambos comandos. `PIP_NO_INDEX=1` y comprobación de versión
de pip deshabilitada para esta ejecución; no hay instalación ni consulta remota.
Un verificador externo al checkout ejecutó estos comandos como subprocesos del
intérprete `.venv` y conservó su salida completa. No se sustituye unittest por un
recuento propio ni se cambia su descubrimiento.

Registros locales técnicos en `%TEMP%/spica-85k-auditoria-4k75sr4n/`:
`dirigidas-inicial.log`, `dirigidas-final.log`, `dirigidas-codigo-congelado.log`,
`dirigidas-control.json`, `suite-completa.log`, `verificacion-suite.json`,
`pip-check.log`, `procesos-85k.json`, `piloto-metricas.json` y
`cortes-proceso.json`, además de guardia y arneses de comprobación. Son registros
del ensayo, no respaldo operativo o custodia independiente. Los datos de las
fixtures se eliminaron mediante sus contextos después de comprobarlos.

## Archivos del incremento

```text
docs/arquitectura_respaldo_restauracion_paso85k.md
docs/piloto_respaldo_restauracion_paso85k.md
docs/brechas_custodia_paso85k.md
herramientas/respaldo_linaje_85k.py
tests/test_respaldo_linaje_85k.py
```

No se modifican componentes previos, contratos públicos, reglas, dependencias,
main.py, .gitignore, .venv, informes históricos o las 29 brechas PNDA. No hay
commits/push. La ausencia de cambios operativos se establece por ausencia de
acceso en este trabajo y guardia de rutas conocidas; no por una reinspección de
datos que debían permanecer cerrados ni por controlar acciones de terceros.

Comprobaciones finales locales:

| Comprobación | Resultado |
|---|---|
| Sintaxis y definiciones | Dos archivos Python analizados; sin errores ni definiciones duplicadas |
| Documentación nueva | Tres UTF-8, salto final, sin espacios finales/conflictos/bloques abiertos; 20 enlaces locales existentes, sin abrir URLs |
| `git diff --check` | Código 0, sin salida; complementado por revisión directa de los cinco archivos nuevos, que este comando no incluye |
| `git diff --exit-code HEAD` | Código 0, sin salida: los archivos registrados permanecen intactos |
| `git diff --cached --exit-code` | Código 0, sin salida: índice sin cambios |
| Rama / HEAD | `feature/suadc-http` / `d7d7b8c`, sin cambios |

Estado final de `git status --short`, código 0:

```text
?? docs/arquitectura_respaldo_restauracion_paso85k.md
?? docs/brechas_custodia_paso85k.md
?? docs/piloto_respaldo_restauracion_paso85k.md
?? herramientas/respaldo_linaje_85k.py
?? tests/test_respaldo_linaje_85k.py
```

El estado inicial era limpio; los únicos cambios finales son esos cinco archivos
nuevos sin seguimiento. Se mantienen las 29 brechas PNDA y todos los documentos
históricos, sin nueva evidencia institucional ni modificaciones de sus estados.

## Dictamen

**APTO CON RESTRICCIONES**, exclusivamente para el respaldo/restauración
experimental offline de una ejecución conservada en el perfil TEMP descrito.
Se comprobaron generación coherente, copias físicas independientes, restauración
desde otro proceso, conservación de restricciones/errores/IDs/versiones y rechazo
de corrupción, residuos y sobrescritura. No quedan fallos reproducibles abiertos
en el alcance probado; las limitaciones documentadas no se convierten en garantías.

No es custodia única ni integración operativa. Persisten TOCTOU, escritor hostil,
dominio de fallo compartido, control sin custodia independiente, versiones
cerradas, ausencia de atomicidad global y durabilidad eléctrica no demostrada.
El siguiente requisito recomendado es diseñar la protección independiente del
control y la recuperación desde otro dominio de fallo, además del tratamiento
manual auditado de parciales; **sin implementarlo ahora**. No se integra a RAW,
no se autoriza ciencia, GIS, IA o adquisiciones, y `/query` sigue NO AUTORIZADO.
No hay commits/push. Se espera revisión antes de cualquier incremento posterior.
