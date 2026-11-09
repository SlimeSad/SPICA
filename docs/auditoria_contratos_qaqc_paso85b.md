# PASO 85-B — Auditoría de cardinalidad y contratos QA/QC Nivel 0

Elaboración: **2026-11-08, America/Lima**; piloto técnico ejecutado el
**2026-11-09 UTC**. Dictamen: **APTO CON RESTRICCIONES**, para revisión de este
incremento offline. No autoriza el PASO 85-C ni QA/QC científico.
Complemento: [versionado y restricciones](versionado_restricciones_qaqc_paso85b.md).

## Estado recuperado y arquitectura

Git inicial limpio, rama **feature/suadc-http**, HEAD **3535a47**,
«SUADC: auditoria y piloto QAQC estructural nivel 0». El 85-A está consolidado.
Historial comprobado con git status, git log -5 --oneline y git branch --show-current:

```text
3535a47 SUADC: auditoria y piloto QAQC estructural nivel 0
496976d SUADC: vinculacion verificable de evidencia documental
f6c2a36 SUADC: auditoria de procedencia y piloto documental PNDA
1c06125 SUADC: contratos experimentales de metadatos documentales
ef17ad4 SUADC: reconciliacion documental de metadatos PNDA
```

Se revisaron el [inventario de 22 reglas](inventario_qaqc_nivel0_paso85a.md),
el [piloto 85-A](piloto_qaqc_estructural_paso85a.md),
los [contratos](../src/spica/calidad/modelos.py),
[reglas](../src/spica/calidad/reglas.py), [motor](../src/spica/calidad/motor.py),
[53 tests Nivel 0](../tests/test_calidad_nivel0.py),
[ocho tests 85-A](../tests/test_piloto_qaqc_estructural_85a.py),
el [diseño del PASO 72](calidad_nivel0.md), la
[cardinalidad del PASO 73](catalogo_reglas_cientificas.md) y consumidores.

Flujo conservado: LectorCSV/ConsultorLocalCSV → adaptar_registro → RegistroQA →
evaluar_registro → ResultadoQA; EvaluadorNivel0 controla lectura, límites,
cancelación y cierre, y produce InformeQA agregado. El piloto puro recibe
RegistroQA directamente. No hay otro motor ni parser; se reutiliza la
[interpretación compartida](../src/spica/perfilado/interpretacion.py).

Consumidores comprobados por búsqueda en src/, herramientas/ y tests/:
motor y pruebas Nivel 0/85-A; contratos científicos reutilizan RegistroQA,
ProcedenciaQA y EstadoEvaluacionQA, no deserializan ResultadoQA. Aplicabilidad y
evaluador científico experimental permanecen separados. No se encontró un
serializador persistente de ResultadoQA ni consumidor que exija igualdad exacta
del conjunto de parámetros. Esto acredita compatibilidad en este repositorio,
no en consumidores externos desconocidos.

## Inventario de contratos y límites de representación

| Contrato/campo existente | Qué representa | Límite comprobado |
|---|---|---|
| ReglaQA | ID, versión, categoría y descripción | 22 definiciones cerradas; no ejecuta expresiones configuradas |
| RegistroQA | Número lógico, líneas, ID/nombre literales, campos textuales, tupla CSV bruta y procedencia propia opcional | No es identidad física de estación ni evento; estructura_correcta es declaración del adaptador |
| ConfiguracionQA | Reglas/variables, formatos con referencia, zona, mappings y presupuesto numérico | Solo TEMP/HR/PP; ausencia de una declaración no demuestra ausencia institucional |
| ProcedenciaQA | Fuente/recurso/adquisición/activo/hash/documento declarados | None sigue desconocido; no abre ni comprueba originales |
| ResultadoQA.estado / estado_evaluacion | Condición concreta y grado de evaluación | Completa no significa científicamente apta |
| valores_originales | Campos objetivo y textos/None utilizados | En fila incoherente, VAL identifica cada variable; las otras reglas conservan contexto de fila |
| evidencia / parametros | Referencias efectivamente utilizadas y política/formatos aplicados | Una referencia suministrada no acredita autenticidad o aplicabilidad editorial |
| diagnostico | Motivo de estado, ausencia, ambigüedad o interrupción de condición | Se conserva literal; no es autorización ni una lista exhaustiva de metadatos |
| InformeQA | Configuración, límites, alcance y conteos del recorrido | Los agregados no se vuelven a contar como resultados individuales |

Metadatos requeridos/disponibles/faltantes se reconstruyen desde la definición
de regla, configuración del ensayo, referencias y diagnóstico, no desde un campo
nuevo obligatorio. VAL-004 necesita formato NUMERO_ASCII, TMP-001 AAAAMMDD,
TMP-002 HHMMSS e ID-004 anchura documentada; TMP-003 necesita referencia de zona;
ID-002 necesita mapping literal con evidencia; PROV requiere las referencias
correspondientes. El [inventario 85-A](inventario_qaqc_nivel0_paso85a.md) detalla
las 22 condiciones. ResultadoQA aislado no contiene toda ConfiguracionQA: para
reproducirlo hay que conservar InformeQA o el expediente del ensayo puro.
Unidades, ventanas, instrumento y vigencias no se completan desde los valores.

## Las 22 reglas y la multiplicidad real

Las 22 conservan versión individual **1.0.0**, condiciones y estados. En la
columna «por entrada» se supone selección de todas y tres variables. «85-B»
cuenta solo el piloto de siete definiciones; cero no significa regla inexistente.

| Regla | Objetivo | Por entrada | Emisiones 85-B |
|---|---|---:|---:|
| L0-EST-001 | Estructura recibida | 1 | 13 |
| L0-VAL-001 | Presencia TEMP/HR/PP | 3 | 39 |
| L0-VAL-002 | Gramática finita TEMP/HR/PP | 3 | 39 |
| L0-VAL-003 | No finitos TEMP/HR/PP | 3 | 0 |
| L0-VAL-004 | Formato numérico documental TEMP/HR/PP | 3 | 39 |
| L0-TMP-001 | FECHA civil documental | 1 | 0 |
| L0-TMP-002 | Formato HORA | 1 | 13 |
| L0-TMP-003 | Zona documentada disponible | 1 | 0 |
| L0-TMP-004 | Instante absoluto no determinado | 1 | 0 |
| L0-ID-001 | Nombre literal de estación | 1 | 0 |
| L0-ID-002 | Mapping literal de identidad | 1 | 13 |
| L0-ID-003 | LONGITUD/LATITUD presentes | 1 | 0 |
| L0-ID-004 | Anchura documental UBIGEO | 1 | 13 |
| L0-ID-005 | Ocho metadatos de ubicación | 1 | 0 |
| L0-PROV-001 | Fuente declarada | 1 | 0 |
| L0-PROV-002 | Recurso declarado | 1 | 0 |
| L0-PROV-003 | Adquisición declarada | 1 | 0 |
| L0-PROV-004 | Activo declarado | 1 | 0 |
| L0-PROV-005 | SHA de referencia | 1 | 0 |
| L0-PROV-006 | Asociación de documento | 1 | 0 |
| L0-PROV-007 | Mención/referencia de licencia | 1 | 0 |
| L0-PROV-008 | Coherencia de procedencias | 1 | 0 |
| **Total** | **22 definiciones; siete seleccionadas** | **30** | **169** |

Hay **13 invocaciones originales de evaluar_registro**, una por entrada.
Cada una visita siete definiciones: **91 visitas regla–entrada**. En cada visita
a una VAL se itera sobre tres campos y se emite un resultado por objetivo.
Así, las tres VAL producen 39 emisiones cada una, las otras cuatro 13 cada una:

```text
13 × (4 + 3 × 3) = 169 = 91 + 13 × 3 × (3 − 1)
3 × 39 + 4 × 13 = 117 + 52 = 169
```

No son 169 observaciones independientes ni siete llamadas a funciones de regla
por fila: las reglas son descriptores y ramas del mismo generador. Las condiciones
de presencia, finitud y formato se solapan deliberadamente; el parser numérico
se reutiliza por celda. Una fila puede emitir problema de gramática y alerta de
formato sin duplicar una misma clave de comprobación.

## Reconstrucción exacta del piloto

Se reutilizan sin cambios las 12 fixtures, sus configuraciones y los literales
del 85-A. S12 tiene dos registros con contenido igual y posiciones distintas.
S02 es un RegistroQA parcial en memoria, no un supuesto CSV institucional.

| Escenario | Entradas | Resultados | Satisfechas | Alertas | Problemas | No evaluadas | Incompletas |
|---|---:|---:|---:|---:|---:|---:|---:|
| S01 | 1 | 13 | 11 | 0 | 0 | 2 | 0 |
| S02 | 1 | 13 | 8 | 0 | 0 | 2 | 3 |
| S03 | 1 | 13 | 8 | 0 | 1 | 4 | 0 |
| S04 | 1 | 13 | 11 | 0 | 0 | 2 | 0 |
| S05 | 1 | 13 | 9 | 1 | 1 | 2 | 0 |
| S06 | 1 | 13 | 0 | 0 | 0 | 0 | 13 |
| S07 | 1 | 13 | 11 | 1 | 0 | 1 | 0 |
| S08 | 1 | 13 | 11 | 0 | 0 | 2 | 0 |
| S09 | 1 | 13 | 10 | 1 | 0 | 2 | 0 |
| S10 | 1 | 13 | 11 | 0 | 0 | 2 | 0 |
| S11 | 1 | 13 | 7 | 0 | 0 | 6 | 0 |
| S12 | 2 | 26 | 22 | 0 | 0 | 4 | 0 |
| **Total** | **13** | **169** | **119** | **3** | **2** | **29** | **16** |

| Regla | Visitas regla–entrada | Resultados | S | A | P | N | I |
|---|---:|---:|---:|---:|---:|---:|---:|
| L0-EST-001 | 13 | 13 | 12 | 0 | 0 | 0 | 1 |
| L0-VAL-001 | 13 | 39 | 34 | 0 | 1 | 0 | 4 |
| L0-VAL-002 | 13 | 39 | 33 | 0 | 1 | 1 | 4 |
| L0-VAL-004 | 13 | 39 | 30 | 1 | 0 | 4 | 4 |
| L0-TMP-002 | 13 | 13 | 0 | 0 | 0 | 12 | 1 |
| L0-ID-002 | 13 | 13 | 0 | 1 | 0 | 11 | 1 |
| L0-ID-004 | 13 | 13 | 10 | 1 | 0 | 1 | 1 |
| **Total** | **91** | **169** | **119** | **3** | **2** | **29** | **16** |

Cada combinación VAL–variable produce exactamente **13 resultados**. Las 16 I
son tres por TEMP ausente en S02 y trece por estructura incoherente en S06.
**119 + 3 + 2 + 29 + 16 = 169.** Las repeticiones de determinismo y pruebas
complementarias no se suman. No se emiten agregados dentro de esta serie pura.
El antecedente de 744 × 30 = 22320 es histórico; no se reabre su CSV operativo.

## Identidad, trazabilidad y regresión

Clave local reproducible del expediente:

```text
(escenario, numero_registro, linea_inicial, linea_final,
 regla_id, version_regla, campos_objetivo_ordenados)
```

**169 claves únicas, cero duplicaciones accidentales y cero resultados omitidos**
en el producto cartesiano previsto. Cambiar orden de escenarios, registros,
selección de reglas y variables conserva el diccionario clave→resultado.
Los IDs S01…S12 son nombres de ensayos fijos, no IDs aleatorios ni operativos.

El contexto es indispensable: S01 y la primera fila de S12 pueden producir
ResultadoQA iguales por contenido; siguen siendo ejecuciones independientes.
Dentro de S12, número/líneas distinguen las dos entradas con igual contenido.
No se usa ID original, nombre, fecha/HORA o hash de valor como identidad de
evento meteorológico. No existe una clave global nativa de resultado; una
persistencia futura necesitará contexto/configuración/versiones y revisión de
su contrato. No se implementa ahora ni se inventa un identificador universal.

S06 conserva los objetivos TEMP/HR/PP en cada VAL incompleta y la tupla bruta de
17 valores. La prueba 85-B extiende esa regresión a las **cuatro** VAL: treinta
resultados con todas las reglas, treinta claves distintas. No reaparece 85A-01.

Se compararon **169/169 resultados** con evaluar_registro del código registrado
en HEAD 3535a47: igualdad completa tras retirar únicamente el nuevo parámetro
evaluador_nivel0. Estados, diagnósticos, referencias, campos, textos y versiones
previas se conservan. No se reescriben los informes históricos.

Cada traza del artefacto propio contiene clave, ResultadoQA nativo completo,
configuración, restricciones del escenario y anotaciones con versión de política.
Ensayo UTC: **2026-11-09T00:21:28.581777+00:00** a
**2026-11-09T00:21:28.669223+00:00**. Estos tiempos son técnicos, no fechas de
observación. Artefacto exclusivamente sintético fuera de Git:

```text
%TEMP%\spica-85b-3jh3y70x\piloto-sintetico.json
1411767 bytes
SHA-256: 16339b27abd5c4c7009594465b3704fd76ecae958f42eaec479507ab9bd26ebc
```

## Hallazgos y cambios acotados

| ID | Gravedad | Evidencia y resolución |
|---|---|---|
| 85B-01 | Media | La atribución corregida en 85-A no tenía versión técnica propia; ahora se identifica emisión/trazabilidad como evaluador_nivel0=1.0.1 en parametros. Reglas y esquema permanecen 1.0.0 |
| 85B-02 | Media | Las restricciones residían solo en el expediente de fixture; nueva función pura restricciones_resultado devuelve anotaciones conservadoras del ResultadoQA existente, con política 1.0.0. No añade campos ni un segundo resultado |
| 85B-03 | Media, limitación residual | El resultado aislado no contiene escenario/configuración completa ni clave global. El expediente sintético los conserva; no publicar resultados descontextualizados ni prometer identidad global |
| 85B-04 | Media, limitación residual | Referencias declaradas y asociación documental no autentican evidencia ni demuestran aplicabilidad. Se preservan diagnósticos y restricciones; no se conecta autorización científica |

No se detectó un defecto crítico nuevo de cardinalidad. No hacen falta migración,
rediseño, cambio de estados o aumento de versiones de las 22 reglas.
La política, el alcance de compatibilidad y los motivos de no evaluación se
detallan en el [segundo informe](versionado_restricciones_qaqc_paso85b.md).

## Pruebas y cierre

Se añaden [12 tests](../tests/test_contratos_qaqc_85b.py), con subcasos de
cardinalidad por escenario/regla/campo, identidad estable, cuatro VAL incompletas,
versionado/constructor/esquema previo, S con restricciones, I con impedimento,
N con motivo, HORA/UBIGEO intactos, TEMP/HR extremos finitos, referencias sin
verificación, ausencia de efectos y prohibición de red/archivos/SQLite/ciencia.
No se cuenta cada restricción, subcaso o repetición como otra prueba.

**Dirigidas realmente ejecutadas: 73 aprobadas, cero fallos y errores, 14.809 s**:
53 anteriores + ocho 85-A + doce 85-B.

**Suite completa realmente ejecutada: 1626 aprobadas, cero fallos, errores y
omitidas, 159.765 s, código 0, salida OK**: 1614 anteriores + doce nuevas.
Las dirigidas no se suman otra vez. Se conservan las regresiones previas,
incluida la cardinalidad de 744 filas sintéticas/22320 resultados. No se vuelve
a ejecutar el piloto institucional histórico. Entorno comprobado: Python
**3.15.1**, HTTPX **0.28.1**, SQLite **3.53.4**, intérprete de .venv.

Comandos ejecutados; PYTHONPATH y opciones de pip son temporales al proceso,
sin cambiar archivos ni dependencias:

```powershell
$env:PYTHONPATH="$env:TEMP\spica-85b-3jh3y70x\guardia;$PWD\src;$PWD\tests;$PWD"
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -B -m unittest test_calidad_nivel0 test_piloto_qaqc_estructural_85a test_contratos_qaqc_85b -v
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
$env:PIP_NO_INDEX='1'
$env:PIP_DISABLE_PIP_VERSION_CHECK='1'
$env:SPICA_85B_PIP_CHECK='1'
.\.venv\Scripts\python.exe -B -m pip check
git diff --check
git status --short
```

La salida completa de unittest se redirigió a los logs privados. pip check:
**No broken requirements found.**, código 0; no consulta índices. Se permite su
consulta local de versión Windows sin desactivar la guardia de red/rutas.
Guardia final de suite y pip: **0 red, 0 rutas operativas, 0 SQLite operativos,
0 procesos no admitidos**. SQLite temporal/memoria de fixtures no es el operativo.
La suite se ejecutó como propietario para que Python 3.15 pueda acceder a sus
temporales privados; no se cambiaron ACL.

Los registros de verificación quedan en el temporal propio indicado:
dirigidas.log, suite-completa.log y guardia/sitecustomize.py. Guardia del piloto:
**cero red, SQLite, procesos durante evaluación y escrituras fuera de ese temporal**;
guardia de rutas operativas también cero. La comparación histórica usa únicamente
git show del repositorio antes de entrar a la evaluación pura bloqueada.

La [matriz de brechas](brechas_reconciliadas_pnda_paso84i.md) conserva sus **29**
IDs y estados: **2 resueltas documentalmente, 17 parciales, 8 pendientes,
2 contradicciones; 27 abiertas**. No se cambia ningún estado ni correspondencia
XLSX–DOCX–CSV. No se localizó una muestra PNDA independiente autorizada y no se
buscó abriendo RAW, evidencias privadas ni el CSV operativo.

No se accede al CSV operativo, RAW permanente, staging ni SQLite operativo.
No se afirma inspección física nueva de recursos que permanecen cerrados ni
control sobre cambios de terceros. Cero conexiones/GET/descargas/instalaciones,
migraciones, commits o push. Las pruebas históricas usan sus propias fixtures
temporales, no los almacenes operativos.

Estado final de Git, sin cambios en rama, HEAD o índice:

```text
 M src/spica/calidad/__init__.py
 M src/spica/calidad/reglas.py
?? docs/auditoria_contratos_qaqc_paso85b.md
?? docs/versionado_restricciones_qaqc_paso85b.md
?? src/spica/calidad/restricciones.py
?? tests/test_contratos_qaqc_85b.py
```

Dos archivos modificados y cuatro nuevos; no se sobrescribe trabajo anterior.
git diff --check e índice comprobados sin errores. Git avisa futura conversión
LF/CRLF en los dos archivos seguidos; no se cambia esa configuración.
También se revisaron los archivos nuevos sin seguimiento: cuatro Python con
sintaxis compilada en memoria y sin definiciones duplicadas; dos documentos,
ocho tablas y 17 enlaces locales válidos, sin abrir enlaces externos. Se
comprueban UTF-8, ausencia de caracteres de reemplazo y espacios finales.

Riesgos: especialización SENAMHI, confianza cooperativa de dataclasses frozen,
presupuesto a cargo del consumidor de la función pura, falta de serializador
versionado con contexto y ausencia de evidencia científica aplicable. Son límites
explícitos; ninguna anotación autoriza operaciones ni resuelve esos pendientes.
Recomendación para un eventual 85-C: revisar primero la política de exportación
de contexto/restricciones y su consumo, siempre con fixtures, sin activar QA
científico ni normalizar HORA/UBIGEO/PP. **Esperar revisión.**
