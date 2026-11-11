# PASO 85-E — Cierre experimental provisional del ciclo QA/QC estructural

Fecha: **2026-11-11, America/Lima**. Dictamen: **APTO PARA PROPONER CIERRE
EXPERIMENTAL PROVISIONAL CON RESTRICCIONES**, sujeto a auditoría. No es
certificación de producción ni autorización de ciencia o del PASO 86-A.
Perfil, identidades y política: [auditoría entre lotes](auditoria_lotes_qaqc_paso85e.md).

## Git recuperado y alcance

Estado inicial limpio, rama **feature/suadc-http**, HEAD **7515d75**. PASO 85-D
registrado. Historial comprobado:

```text
7515d75 SUADC: consumidor seguro de exportaciones QAQC nivel 0
ce2bf49 SUADC: exportacion trazable QAQC nivel 0
b2c0171 SUADC: versionado y restricciones QAQC estructural nivel 0
3535a47 SUADC: auditoria y piloto QAQC estructural nivel 0
496976d SUADC: vinculacion verificable de evidencia documental
```

Se crean [comparador puro](../src/spica/calidad/conciliacion_lotes.py),
[25 pruebas nuevas](../tests/test_conciliacion_qaqc_85e.py) y los dos informes
85-E. No se modifican exportador, consumidor, reglas, motor, modelos, inspectores,
catálogos, transportes, dependencias, main.py, .gitignore ni .venv.
No se ejecuta un congelado mediante tag, commit, bloqueo de código o publicación;
se propone una base experimental para revisión.

## Piloto ejecutado y conservación del ciclo

Se reutilizan las fixtures de [85-A](../tests/test_piloto_qaqc_estructural_85a.py)
y el contexto de [85-C](piloto_exportacion_qaqc_paso85c.md), con el
[consumidor 85-D](piloto_consumo_qaqc_paso85d.md). Cada ciclo evalúa **13 entradas
sintéticas en 12 escenarios**, siete definiciones de regla y tres variables.
**13 × (4 + 3 × 3) = 169 resultados**, no 169 observaciones científicamente válidas.

Ensayo final UTC: **2026-11-11T23:47:00.819352+00:00** a
**2026-11-11T23:47:35.175762+00:00**. Tiempos de auditoría técnica, no de observación.
Los ciclos A y B se ejecutan por separado con el mismo contexto declarado de
reproducibilidad: espacio spica:piloto:85c, evaluación regresion-001, escenarios
S01…S12 y entrada-N. C declara otra evaluación: ejecucion-independiente-C.
D es una copia sintética separada con un diagnóstico deliberadamente diferente,
reexportada y validada; no se modifica A para forzar el conflicto.

| Lote | Satisfechos | Alertas | Problemas | No evaluados | Incompletos | Diagnósticos | Informativas | Bloqueantes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A | 119 | 3 | 2 | 29 | 16 | 169 | 169 | 566 |
| B | 119 | 3 | 2 | 29 | 16 | 169 | 169 | 566 |
| C, evaluación independiente | 119 | 3 | 2 | 29 | 16 | 169 | 169 | 566 |
| D, variante conflictiva | 119 | 3 | 2 | 29 | 16 | 169 | 169 | 566 |

Conteos derivados de los paquetes aceptados, no fabricados como salidas del
comparador. Los 735 elementos por lote son **anotaciones** dentro de 169
diagnósticos. Regla y QA conservan 1.0.0, emisor 1.0.1, restricciones 1.0.0,
JSON y consumo 0.1.0; la nueva conciliación tiene su propia versión 0.1.0.
Los desconocidos siguen sin inventarse y ninguna brecha se resuelve con esos números.

## Comparaciones observadas

| Comparación | Estado real | Coincidencias por resultado | Conflictos / limitaciones |
|---|---|---:|---|
| A–B, mismo contexto reproducido | COINCIDENCIA | 169 | Ningún conflicto |
| A–C, ejecuciones lógicas independientes | NO_COMPARABLE | 0 | ambitos_de_evaluacion_sin_correspondencia |
| A–D, identidad reutilizada con otro diagnóstico | CONFLICTO | 168 | Un identidad_resultado_reutilizada; ambos documentos preservados |

Cada comparación examina 338 representaciones (169 por lote), no 338
observaciones independientes. A–C tiene los mismos conteos agregados y valores
sintéticos, pero contexto/identidad diferentes: no se inventa un vínculo entre
ejecuciones. El estado NO_COMPARABLE es una barrera correcta, no una pérdida de
datos ni un defecto crítico de cierre. Comparar métricas iguales no acredita
igualdad de eventos o identidad institucional.

Las comparaciones se repiten invirtiendo los lotes y producen informes iguales.
Se comprueba que los informes originales A/B/C permanecen intactos. El informe
de conflicto conserva los dos conjuntos completos, sin deduplicar el conflicto,
fusionar datos o descartar restricciones. Pruebas específicas cubren también
restricciones diferentes coherentes individualmente bajo un mismo resultado_id:
se registra restricciones_discrepantes además del conflicto de identidad.

Huellas técnicas observadas de lotes canónicos, ordenados por resultado_id y
unidos con LF sin LF final:

```text
A/B: 8bb1a3662edc96b674886fba64b7aa8488e1cefc9d650e4597b5bd95077d6af5
C:   0013bdcf8b4459c27f7ec359cc09511d87a6f109a98af20e3e5baacfc9b8181c
D:   cbf7da00925c5c94f5401428ea5d4113738b051993e2f27a7219473bd59eb54e
```

A/B conserva la representación del piloto 85-C/85-D. Son hashes de datos
sintéticos **en memoria**; no verificación física de archivos ni autenticación.
No se persisten los lotes o sus JSON como datos operativos.

## Pruebas y regresiones realmente ejecutadas

Las **25 pruebas nuevas** cubren perfil diferencial/cerrado, equivalencia
sintáctica, lotes idénticos y parcialmente solapados, duplicados exactos y
contradictorios, etiqueta de lote reutilizada, entradas/reglas/campos/escenarios,
evaluaciones independientes, desconocidos, reportes rechazados/incompletos o
adulterados, versiones incompatibles, restricciones omitidas/alteradas,
determinismo, inmutabilidad, límites, ausencia de efectos/autorización y piloto.

Ensayo inicial: 25 pruebas, **24 aprobadas y un error de fixture**, 23.057 s.
dataclasses.replace no admite cambiar un campo init=False; se corrigió la
simulación de informe adulterado usando una copia independiente y alteración
explícita de ese campo. No cambió un contrato estable ni una expectativa para
ocultar un defecto del producto.

**Dirigidas finales: 156 aprobadas, cero fallos y errores, 41.316 s**:
53 Nivel 0 + ocho 85-A + doce 85-B + 25 85-C + 33 85-D + 25 nuevas.
**Suite completa: 1709 aprobadas, cero fallos, cero errores y cero omitidas,
180.571 s, código 0, salida OK**: las 1684 anteriores más 25 nuevas.
Las dirigidas, subcasos y ciclos no se suman otra vez. Se conservaron regresiones
previas, incluida cardinalidad sintética de 744 filas/22320 resultados; no se
reabrió su CSV institucional.

Entorno comprobado con .venv: Python **3.15.1**, HTTPX **0.28.1**, SQLite **3.53.4**.
Comandos, con variables temporales de importación y sin cambiar configuración:

```powershell
$env:PYTHONPATH="$env:TEMP\spica-85e-_r6j8oq5\guardia;$PWD\src;$PWD\tests;$PWD"
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -B -m unittest test_calidad_nivel0 test_piloto_qaqc_estructural_85a test_contratos_qaqc_85b test_exportacion_qaqc_85c test_consumo_qaqc_85d test_conciliacion_qaqc_85e -v
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
$env:PIP_NO_INDEX='1'
$env:PIP_DISABLE_PIP_VERSION_CHECK='1'
$env:SPICA_85E_PIP_CHECK='1'
.\.venv\Scripts\python.exe -B -m pip check
git diff --check
git status --short
```

pip check: **No broken requirements found.**, código 0, sin consultar índices.
Se permite su consulta local de versión Windows, conservando las guardias de
red/rutas. Dirigidas, suite y pip: **0 red, 0 rutas operativas, 0 SQLite operativos
y 0 procesos no admitidos**. Los temporales privados de Python 3.15 requieren
ejecución como propietario; no se cambiaron ACL.

## Estado final de Git y comprobaciones estáticas

Rama **feature/suadc-http**, HEAD **7515d75**, sin cambios respecto al inicio.
No hay diferencias en archivos registrados ni cambios preparados en el índice:
git diff --exit-code HEAD y git diff --cached --exit-code terminan con código 0.
git diff --check también termina con código 0. Estado final:

```text
?? docs/auditoria_lotes_qaqc_paso85e.md
?? docs/cierre_experimental_qaqc_paso85e.md
?? src/spica/calidad/conciliacion_lotes.py
?? tests/test_conciliacion_qaqc_85e.py
```

Se comprobaron expresamente los cuatro archivos sin seguimiento. Los dos Python
compilan en memoria y no contienen definiciones duplicadas; el comparador no
llama eval, exec, open ni importación dinámica. Los dos documentos contienen seis
tablas y 18 enlaces locales válidos. Los cuatro archivos son UTF-8, sin caracteres
de sustitución ni espacios finales y con salto final; los bloques Markdown están
cerrados. No se abrieron enlaces externos. La suite corresponde al código final;
después solo se completó esta documentación.

## Criterios objetivos de cierre

| Criterio | Evidencia observada | Evaluación |
|---|---|---|
| Exportación reproducible | A/B idénticos, misma huella técnica y 169 coincidencias | Satisfecho en el perfil |
| Consumo contractual seguro y acotado | Revalidación real, pruebas adversariales, esquemas/versiones cerrados | Satisfecho experimentalmente, no garantía absoluta |
| Identidades y restricciones conservadas | 169 IDs y 169/566 anotaciones por lote, documentos completos retenidos | Satisfecho |
| Conflictos entre lotes con contexto suficiente | A/D y casos de entrada/etiqueta/restricciones contradictorias | Satisfecho |
| Comparación explícita | COINCIDENCIA, COMPATIBLES, CONFLICTO y NO_COMPARABLE, con causas | Satisfecho |
| Versiones documentadas | No se mezclan versión de regla, emisor, QA, JSON, política, consumo y conciliación | Satisfecho |
| Diagnósticos trazables | Identidad/contexto/entrada/campo y texto nativo preservados | Satisfecho dentro de declaraciones |
| Límites de confianza | Sin autenticidad, evidencia física, prueba de ejecución o permisos implícitos | Satisfecho como delimitación |
| Regresiones/adversariales | 1709 pruebas finales aprobadas | Satisfecho para la suite ejecutada |
| Ausencia de efectos operativos | Instrumentación y mocks, recursos operativos cerrados | Satisfecho en esta ejecución |

No se observó un defecto crítico pendiente que impida **proponer** el cierre
experimental del Nivel 0. La estabilidad es provisional y está limitada por el
perfil, versiones, fixtures y presupuestos comprobados. No certifica producción,
ciencia, institución o infraestructura operativa, ni autoriza una etapa nueva.

## Seguridad y evidencia de ejecución

El arnés inicial se detuvo porque la guardia exec bloqueó la importación diferida
de copy por asdict en la instrumentación externa. Se cambió ese snapshot por
copias inmutables con replace y se repitió, sin modificar el comparador.
Log inicial conservado. En el ensayo final: **0 red, 0 SQLite, 0 procesos,
0 escrituras y 0 ejecución dinámica**. Las pruebas también bloquean archivos,
red, SQLite, procesos, eval/exec y motores QA/científicos durante la conciliación.

Logs y métricas sintéticas privados, fuera de Git:

```text
%TEMP%\spica-85e-_r6j8oq5\nuevas.log
%TEMP%\spica-85e-_r6j8oq5\dirigidas.log
%TEMP%\spica-85e-_r6j8oq5\suite-completa.log
%TEMP%\spica-85e-_r6j8oq5\piloto-final.log
%TEMP%\spica-85e-_r6j8oq5\guardia-piloto-final.log
%TEMP%\spica-85e-_r6j8oq5\guardia-piloto.log
%TEMP%\spica-85e-_r6j8oq5\guardia\sitecustomize.py
```

No se accedió a CSV operativo, RAW, staging, SQLite operativo o evidencias PNDA.
No se afirma una nueva inspección física de recursos mantenidos cerrados ni
control de cambios de terceros. Cero conexiones/GET, descargas, instalaciones,
migraciones, commits o push. Las bases de fixtures temporales no son operativas.
No se implementan autenticación criptográfica, firmas, servidores o registro remoto.

Las [29 brechas](brechas_reconciliadas_pnda_paso84i.md) conservan IDs y estados:
**2 resueltas documentalmente, 17 parciales, 8 pendientes y 2 contradicciones;
27 abiertas**. No cambian evidencia, unidades, HORA/UBIGEO, PP, ciencia o permisos.

## Condiciones concretas para proponer el PASO 86-A

1. Revisar y aprobar primero este cierre, su perfil estrecho y la política de
   correspondencias. Mantener el ciclo Nivel 0 separado de resultados científicos.
2. Definir una única pregunta metodológica sobre **una regla de temperatura y
   observaciones exclusivamente sintéticas**, sin asumir aplicabilidad a SENAMHI.
   La elección de TEMP evita convertir PP o resolver HORA/UBIGEO por inferencia.
3. Preparar expediente de referencia científica verificable: edición, vigencia,
   variable/unidad, tipo de medición, instrumento, ambiente, método e incertidumbre.
   No fijar umbrales hasta documentación y revisión expresas. Una propuesta no
   se promueve automáticamente a regla aprobada.
4. Especificar fixtures con entradas originales preservadas y contexto explícito;
   casos de condición satisfecha, excedencia como alerta/sospecha, metadatos
   insuficientes y no evaluación. Un extremo no es un error por sí solo.
5. Evaluar los contratos científicos existentes antes de diseñar la salida del
   experimento: no relabelar JSON QA Nivel 0 como certificado científico ni
   eliminar bloqueos para hacerlo pasar al consumidor. Si requiere otro contrato,
   documentarlo y revisarlo por separado.
6. Diseñar trazabilidad de ejecución real, revisión de aplicabilidad y evidencia
   independiente; distinguirlas de hashes autodeclarados. Mantener el experimento
   en memoria/temporales aislados, sin acceso operativo o conexiones por defecto.
7. Solicitar una instrucción específica para ejecutar ese alcance. Las pruebas de
   este paso no habilitan ciencia, datos institucionales o nuevas adquisiciones.

Pendientes residuales: confianza cooperativa del proceso, fabricación coherente
de JSON por remitentes, coordinación externa de IDs, correspondencias entre
evaluaciones y ausencia de historia/persistencia entre llamadas. No se presenta
la ausencia de conflictos como autenticidad o validez científica.

**Se propone cierre experimental provisional con restricciones. Esperar auditoría;
no avanzar automáticamente al PASO 86-A.**
