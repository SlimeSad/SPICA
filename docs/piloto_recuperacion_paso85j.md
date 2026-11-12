# PASO 85-J — Piloto de recuperación y verificación

Fecha: **2026-11-12, America/Lima**. Git inicial limpio, rama
feature/suadc-http, HEAD **2efc9f7**, «SUADC: arquitectura de persistencia y
recuperacion de linaje». Se verificó la consolidación del 85-I y se leyeron sus
tres informes antes de programar. Arquitectura implementada:
[contrato experimental](implementacion_persistencia_paso85j.md).
Pendientes: [brechas](brechas_persistencia_paso85j.md).

## 1. Ensayo real entre procesos independientes

Ejecución métrica entre **2026-11-12T06:07:33.722463+00:00** y
**2026-11-12T06:07:54.086965+00:00**. Son fechas técnicas del ensayo, no fechas
ambientales o prueba de un sello temporal independiente.

El proceso escritor **PID 16248** ejecutó el arnés sintético existente, obtuvo
informe/traza/control y conservó la evidencia. Cerró el conservador y terminó
con código 0 antes de iniciar el lector **PID 8584**, otro intérprete Python.
El lector recibió únicamente raíz de prueba e ID; no recibió objetos Python del
escritor ni ejecutó el arnés. Recuperó el informe tipado y realizó el cotejo 85-H.
Los resúmenes de ambas ejecuciones fueron idénticos.

| Evidencia medida | Resultado |
|---|---|
| Ejecución | ejecucion-85j |
| Identidad de conservación | 260344c87ceb4e53ada54ccedc548aca |
| asset_id sintético histórico | ab50c625725a4b5dbf2f74633d1447b3 |
| Entrada real de la fixture | 572 bytes; dos filas ficticias |
| SHA del activo comprobado durante el arnés | 6894bcce331d4af7db8e4a2f6008a8617604d01e8dbf4cc9805dc8cf37e8ee1b |
| Estado histórico / conservación / recuperación | concluida_estructuralmente / conservada / verificada_en_alcance |
| QA por reproducción A/B | 22 reglas, 60 resultados: 34 comprobacion_satisfecha y 26 no_evaluado |
| Restricciones por reproducción | 60 informativas y 206 bloqueantes, recuperadas sin modificación |
| Cotejo del lector | Informe tipado + traza + control recuperados; coherente_en_alcance=True |
| Huérfanos / temporales / marcador de escritor al terminar | Ninguno |
| Cambios producidos por lector | Ninguno: inventario y SHA de todos los archivos iguales antes/después |
| Fin del ensayo | El padre propietario eliminó exclusivamente su temporal de prueba después de cerrar ambos procesos |

Los 60 resultados proceden de **2 × (18 + 4 × 3)**, no son 60 observaciones.
Las dos reproducciones corresponden al mismo activo y contexto; no se declaran
120 observaciones independientes. Los conteos proceden del motor y sus informes,
no de constantes inyectadas para obtener éxito.

## 2. Artefactos físicos conservados y recuperados

| Rol | Bytes | SHA-256 físico cotejado al recuperar |
|---|---:|---|
| Informe tipado | 3151956 | 256f6eba34be7d11554af021ea1e74a99a07b1c9ccf1e294245b1e7b2f60c0f3 |
| Traza 85-H | 840251 | 39d7c1e1a11235a8e935462fd7577766bd12d241266342fef3543f04f2942002 |
| Referencia de control | 183 | 5934deba83830d18338e305ae6ea04695e839171874d9171d836880c000753f9 |
| Manifiesto | 1494 | 535f47d234a5252162efc5577ccfc18231899eb41b6ff48f22403b33d10b49ac |

Cada cuerpo se publicó bajo contenido/prefijo/hash dentro de la raíz temporal.
Además existieron catalogo.sqlite3 y piloto.json; seis archivos en total al
terminar escritor y lector. El control de traza es su SHA 39d7c1e1...; el SHA del
archivo referencia corresponde al JSON que conserva ese control, son distintos.
No se conserva otro CSV dentro del almacén de ejecuciones.

El informe contiene datos necesarios para los nativos, capturas y JSON ya
emitidos. La redundancia acotada respecto a la traza histórica es explícita;
el volumen de estos cuatro cuerpos no representa consumo RSS ni eficiencia de
escala. La representación conservada depende de IDs/fechas/activo de este
ensayo: no debe igualar el SHA de otra ejecución con la misma entrada.

El activo RAW del arnés ya había sido eliminado antes de conservar. Su SHA
histórico acredita los controles realizados entonces en la fixture, **no una
relectura del RAW después del reinicio**. Las rutas históricas solo se restituyen
como campos inertes del informe para permitir el cotejo exacto del 85-H.

## 3. Pruebas y corrección de auxiliares

Se implementan **50 métodos nuevos** en
[test_conservacion_linaje_85j.py](../tests/test_conservacion_linaje_85j.py).
No se cuentan subcasos o corridas dirigidas como pruebas nuevas adicionales.

La primera corrida ejecutó 46 métodos antes de los cuatro casos finales:
cero fallos de aserción y **32 incidencias de error**, incluidos subcasos,
en 516.027 s. La causa fue el cierre incompleto de conexiones creadas por
auxiliares de las pruebas: with sqlite3.connect confirma/revierte pero no cierra.
Windows impedía eliminar el catálogo del temporal. Un caso aislado reprodujo
ese bloqueo. Se añadió closing explícito a todos esos auxiliares, sin cambiar
contratos estables, ignorar errores de limpieza o desactivar la verificación.

Después aprobaron **8 pruebas dirigidas**, cero fallos/errores, **43.853 s**:
control incorrecto/ausente, informe completo, incompleto, SQLite después de
publicar, prefijo JSON real, dos procesos independientes y las nueve fronteras
de interrupción. Las huellas de los cuatro archivos Python nuevos se cotejaron
antes/después de esa corrida. Se reutilizó el cotejo ya calculado del lector
para evitar una repetición idéntica, conservando las mismas comprobaciones.

| Grupo realmente ensayado | Evidencia exigida por las pruebas |
|---|---|
| Concluida, incompleta, cancelada y fallida | Informe recuperado igual al original, estados independientes y ausencia de promoción científica |
| Nativos parciales y exportación interrumpida | Diez nativos sin JSON inventado; otro fallo conserva 60 nativos y el prefijo real de dos exportaciones, sin consumo ficticio |
| Integridad y ausencias | Relectura/file_digest, control incorrecto o faltante, informe ausente, truncamiento/ampliación y modificación de bytes detectados |
| SQL/versiones/identidad | Esquema 85001, v1 intacto, rechazo de estructura ajena/versiones, inventario roto, conflicto de identidad e idempotencia |
| Publicación/disco/permisos | Destino preexistente intacto, error SQLite tras publicar, ENOSPC/permiso/escritura corta inyectados; residuos conservados |
| Rutas y entrada no confiable | Traversal/raíz operativa rechazados antes de acceso, IDs CON/con sin rutas físicas, symlink/junction simulados, firmas de descriptor distintas, JSON estricto y sin imports arbitrarios |
| Cancelación y recursos | Cancelación previa/durante escritura, plazo cooperativo, presupuestos, segundo escritor rechazado, cierre y limpieza del árbol propio |
| Pureza del lector | Sin QA/red/lecturas históricas; archivos y SQLite sin cambios; resumen sin rutas privadas o permisos |

Las nueve fronteras inyectadas son intención, escritura parcial, temporal
completo, relectura SHA, publicación de artefacto, publicación de manifiesto,
referencias dentro de SQL, confirmación y cierre. Antes de confirmar, el lector
devuelve conservación incompleta con residuos reales; después, recupera el cierre
confirmado. No ejecuta de nuevo la tarea original.

Otra prueba termina un subproceso con os._exit(37) después del primer artefacto:
la intención, el huérfano y el marcador permanecen, se informa INCOMPLETA y se
rechaza escribir nuevamente. El lector no libera el marcador por PID ni borra
evidencia. Es terminación de proceso controlada, **no ensayo de corte eléctrico**.
Los enlaces/junctions adversariales se simulan en las funciones de inspección;
no se acredita defensa universal ante sustituciones hostiles reales.

## 4. Verificación completa y seguridad

La suite completa y pip check se ejecutaron con el Python .venv y registros
íntegros fuera de Git. Las 1791 anteriores se volvieron a ejecutar; no se suman
las corridas dirigidas a la suite completa.

| Verificación final realmente ejecutada | Resultado |
|---|---|
| Entorno del piloto | Python 3.15.1 / HTTPX 0.28.1 / SQLite 3.53.4 |
| Suite completa | **1841 aprobadas, 0 fallos, 0 errores, 0 omitidas**, 743.134 s, código 0, OK |
| Desglose | **1791 anteriores + 50 nuevas** |
| Identidades de pruebas | 1841 esperadas por AST, 1841 observadas y únicas en el log; cero faltantes/inesperadas |
| Código durante suite | SHA-256 de las tres herramientas y la prueba iguales antes/después |
| pip check | **No broken requirements found.**, código 0 |
| Imports experimentales en ambos órdenes | Código 0, sin ejecutar pilotos o inicializar almacenes al importar |
| Sintaxis y duplicación | Cuatro Python nuevos compilables en memoria, sin definiciones repetidas en el mismo ámbito |
| Documentación | UTF-8, tablas/bloques/espacios y destinos locales comprobados directamente; sin abrir URLs |

Se completó la limpieza de **33 temporales exclusivos** identificados en los
errores de las pruebas iniciales y en el caso aislado. Cada objetivo se verificó
por nombre y ruta absoluta resuelta dentro del TEMP autorizado y por ausencia
de enlaces antes de retirarlo, después de terminar el proceso con conexiones
abiertas. Se conserva el inventario de esa limpieza. No fue una reparación
mediante borrado de evidencia operativa ni un algoritmo de GC; el propietario
terminó la limpieza de sus fixtures sintéticas fallidas. Las pruebas corregidas
y el piloto cerraron sus recursos y temporales sin ese fallo.

```powershell
$env:PYTHONPATH="$env:TEMP\spica-85j-auditoria-najgd1ex\guardia;$PWD\src;$PWD;$PWD\tests"
$env:PYTHONIOENCODING='utf-8'
$env:PIP_NO_INDEX='1'
$env:PIP_DISABLE_PIP_VERSION_CHECK='1'
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -B -m pip check
git diff --check
git status --short
```

Se conservaron en `%TEMP%/spica-85j-auditoria-najgd1ex/` la guardia,
dirigidas-inicial.log, dirigidas-corregidas.log, suite-completa.log, pip-check.log,
piloto-metricas.json, verificacion-suite.json e inventario de limpieza de fixtures.
Son registros técnicos/controles del ensayo; no RAW, bases operativas o un
respaldo general de SPICA. Los artefactos del piloto se eliminaron con su temporal
después de demostrar la recuperación entre procesos.

La guardia externa de Python bloquea conexiones/DNS y acceso a rutas operativas
conocidas; los hijos heredan la guardia. No es aislamiento OS ni protección ante
código nativo/Python hostil o aliases desconocidos. MockTransport del arnés
intercambia un GET **simulado**, no un GET externo; no hubo conexiones o descargas
institucionales. El recuperador no llama al transporte ni al motor QA.

No se abrieron RAW/staging/SQLite operativos, CSV institucional o evidencias PNDA.
La afirmación de no modificación se basa en ausencia de acceso/control de rutas,
no en haber vuelto a comprobar físicamente originales mantenidos cerrados. No
controla cambios de terceros. No se instalan librerías ni cambian ACL.

## 5. Archivos, Git y dictamen

Nuevos: tres herramientas experimentales, una prueba y estos tres documentos:

```text
docs/brechas_persistencia_paso85j.md
docs/implementacion_persistencia_paso85j.md
docs/piloto_recuperacion_paso85j.md
herramientas/_catalogo_linaje_85j.py
herramientas/_codec_linaje_85j.py
herramientas/conservacion_linaje_85j.py
tests/test_conservacion_linaje_85j.py
```

No hay modificaciones de src/spica, arnés/traza anteriores, main.py, .gitignore,
requirements.txt, .venv, pruebas previas o documentación histórica. El índice y
los archivos registrados permanecen sin diferencias respecto a HEAD. La rama y
HEAD siguen en feature/suadc-http / 2efc9f7; no se registra este trabajo en Git.

git diff --check, git diff --exit-code HEAD y git diff --cached --exit-code
terminan con código 0, sin salida. Los nuevos archivos sin seguimiento se revisan
directamente porque git diff --check no incluye su contenido. Estado final de
git status --short:

```text
?? docs/brechas_persistencia_paso85j.md
?? docs/implementacion_persistencia_paso85j.md
?? docs/piloto_recuperacion_paso85j.md
?? herramientas/_catalogo_linaje_85j.py
?? herramientas/_codec_linaje_85j.py
?? herramientas/conservacion_linaje_85j.py
?? tests/test_conservacion_linaje_85j.py
```

Las 29 brechas PNDA conservan 2 resueltas, 17 parciales, 8 pendientes y 2
contradicciones. No se ejecutan QA1, ciencia, GIS, IA, normalizaciones, migraciones
operativas o autorizaciones institucionales. No hay commits ni push.

**Dictamen: APTO CON RESTRICCIONES para el piloto experimental offline de
conservación y recuperación de evidencia entregada.** Se comprobó recuperación
física de artefactos y cotejo 85-H en un proceso independiente. No se acredita
custodia operativa, autenticidad independiente, validez científica, atomicidad
global o resistencia a pérdida eléctrica. Antes de custodia única se recomienda
priorizar respaldo/restauración consistente y versiones bajo un nuevo alcance.
No se integra a ciencia ni se inicia el siguiente incremento. Se espera revisión.
