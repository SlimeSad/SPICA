# PASO 85-D — Piloto de ida y vuelta y pruebas adversariales

Fecha: **2026-11-11, America/Lima**. **APTO CON RESTRICCIONES** para revisión.
Contrato: [consumo offline 0.1.0](contrato_consumo_qaqc_paso85d.md).
No integra datos al catálogo ni autoriza QA científico o PASO 85-E.

## Estado recuperado y cambios

Git inicial limpio, rama **feature/suadc-http**, HEAD **ce2bf49**. PASO 85-C
consolidado; historial inicial:

```text
ce2bf49 SUADC: exportacion trazable QAQC nivel 0
b2c0171 SUADC: versionado y restricciones QAQC estructural nivel 0
3535a47 SUADC: auditoria y piloto QAQC estructural nivel 0
496976d SUADC: vinculacion verificable de evidencia documental
f6c2a36 SUADC: auditoria de procedencia y piloto documental PNDA
```

Únicamente se crean [consumo.py](../src/spica/calidad/consumo.py),
[sus pruebas](../tests/test_consumo_qaqc_85d.py) y los dos informes de 85-D.
Se conserva exportador, lector JSON compartido, modelos, motor, reglas,
restricciones, inspectores, transportes y demás componentes estables intactos.

## Ida y vuelta realmente ejecutada

Se reutilizan [12 escenarios ficticios 85-A](../tests/test_piloto_qaqc_estructural_85a.py)
y el contexto de [85-C](piloto_exportacion_qaqc_paso85c.md). Trece entradas se
evalúan con siete definiciones: cuatro por fila y tres VAL × TEMP/HR/PP.
**13 × (4 + 3 × 3) = 169 diagnósticos**, no observaciones ambientales validadas.
Se exportan, consumen y comparan con la estructura completa recibida.

Contexto sintético explícito: espacio **spica:piloto:85c**, evaluación
**regresion-001**, escenarios S01…S12, entrada **entrada-N** con N lógico original,
configuración y motivos del expediente ficticio. Se conserva el mismo contexto
para demostrar identidad estable; no se inventa procedencia institucional.
Los inventarios no aportados siguen null. No se usa muestra PNDA real.

Ensayo final UTC: **2026-11-11T23:21:04.781146+00:00** a
**2026-11-11T23:21:21.488482+00:00**. Son tiempos de auditoría, no observación.
Estado: **CONTRATO_VALIDO_EN_ALCANCE**, 169 recibidos, 169 aceptados únicos,
cero duplicados y ninguna reparación de restricciones.

| Escenario | Entradas | Aceptados | Satisfechos | Alertas | Problemas | No evaluados | Incompletos |
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

Los conteos se derivaron de los documentos devueltos. Cada identidad, versión,
campo, literal, diagnóstico y referencia coincide con el paquete exportado.
Se conservan las versiones QA/regla 1.0.0, emisor 1.0.1, política 1.0.0 y
esquema 0.1.0. No se alteran estados esperados para aprobar pruebas.

## Restricciones conservadas

**735 anotaciones**, calculadas desde las listas aceptadas: **169 informativas**
y **566 bloqueantes de usos del resultado**. No son diagnósticos adicionales.

| Código | Apariciones |
|---|---:|
| alcance_estructural | 169 |
| sin_validacion_cientifica | 169 |
| sin_equivalencia_editorial | 169 |
| numero_sin_metrologia | 82 |
| pp_sin_conversion | 43 |
| hora_sin_transformacion | 16 |
| ubigeo_sin_interpretacion | 16 |
| identidad_ubicacion_no_verificadas | 26 |
| condicion_no_evaluada | 29 |
| condicion_incompleta | 16 |
| **Total** | **735** |

Se contrastan grupo/tipo, código, operaciones, motivo y orden, sin sustituir
listas recibidas por listas reconstruidas. Las emisiones de S06 no VAL conservan
contexto de fila completa y sus restricciones conservadoras; no se afirma que
esos campos fueran evaluados. TEMP/HR/PP incompletas siguen diferenciadas.
HORA 12345, UBIGEO 007777.0 y PP 1.50 se conservan, sin normalizar o convertir.
Satisfecha no equivale a aptitud científica; N/I mantienen motivos e impedimentos.

## Identidad, reproducibilidad y alteraciones

El lote se repite invirtiendo el orden de documentos; InformeConsumoQA y los
JSON canónicos ordenados por resultado_id permanecen iguales. Las entradas
nativas originales también permanecen iguales. La representación de paquetes
unidos por LF, sin LF final, ocupa **889055 bytes**, la misma del PASO 85-C:

```text
SHA-256: 8bb1a3662edc96b674886fba64b7aa8488e1cefc9d650e4597b5bd95077d6af5
```

Es una huella de representación **sintética en memoria**, no un hash físico ni
verificación de archivo científico. Presupuesto observado: **501 nodos máximo
por documento, 66126 en el lote y profundidad máxima 6**. Se mantienen los
límites configurados, sin escribir las exportaciones a disco.

Añadir una copia del primer documento produjo **170 recibidos, 169 únicos y
un duplicado exacto**, con las mismas restricciones, sin sumar otra observación.
Los tests distinguen además filas con contenido igual e identidades legítimas
distintas: ambas se conservan. El consumidor no deduplica eventos ambientales.

| Alteración deliberada | Resultado real | Código observado |
|---|---|---|
| Identificador cambiado | Lote rechazado, cero aceptados | identidad_incoherente |
| Bloqueos omitidos | Lote rechazado, cero aceptados | restricciones_omitidas_o_adulteradas |
| Versión incompatible | Lote rechazado, cero aceptados | version_no_admitida |
| Nuevo diagnóstico reexportado bajo el mismo contexto/ID | Lote rechazado, cero aceptados | identidad_reutilizada_contradictoria |

Estos rechazos no prueban autenticidad: una falsificación internamente coherente
aislada puede pasar este contrato. Las pruebas conservan incluso un estado
documental VERIFICADO suministrado como fixture, manteniendo autenticidad y
verificación independiente explícitamente fuera de alcance.

## Pruebas nuevas, dirigidas y suite

**33 tests nuevos** con subcasos adversariales: sintaxis, duplicación de claves,
campos desconocidos/faltantes, tipos estrictos y booleanos, versiones, NaN/
Infinity/floats, UTF-8/BOM/surrogates, límites previos al parser, profundidad,
nodos/objetos/cadenas/restricciones/lote, memoria/recursión simuladas, identidades,
duplicados exactos/contradictorios, restricciones omitidas/adulteradas/desconocidas,
cinco estados, literales y procedencia declarada, determinismo, inmutabilidad,
ausencia de efectos y piloto completo. Rechazar correctamente es un resultado
de prueba satisfactorio, no una prueba omitida.

Primera ejecución: **31 nuevas aprobadas**, cero fallos/errores, **6.497 s**.
Se añadieron dos pruebas para precedencia del error crítico y tipos/IDs acotados,
y se separó el presupuesto de contraste del presupuesto léxico de entrada.
**Dirigidas finales: 131 aprobadas**, cero fallos y errores, **18.329 s**:
53 Nivel 0 + ocho 85-A + doce 85-B + 25 85-C + 33 nuevas.

**Suite completa realmente ejecutada: 1684 aprobadas, cero fallos, cero errores,
cero omitidas, 155.047 s, código 0, salida OK**. Son 1651 anteriores + 33 nuevas;
no se suman otra vez las dirigidas, subcasos o repeticiones. Se conservan las
regresiones anteriores, incluida cardinalidad sintética de 744 filas/22320
resultados, sin reabrir el CSV institucional.

Entorno comprobado: Python **3.15.1** de .venv, HTTPX **0.28.1**, SQLite **3.53.4**.
Comandos, con variables de importación temporales y logs fuera de Git:

```powershell
$env:PYTHONPATH="$env:TEMP\spica-85d-xbw3g9s7\guardia;$PWD\src;$PWD\tests;$PWD"
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -B -m unittest test_calidad_nivel0 test_piloto_qaqc_estructural_85a test_contratos_qaqc_85b test_exportacion_qaqc_85c test_consumo_qaqc_85d -v
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
$env:PIP_NO_INDEX='1'
$env:PIP_DISABLE_PIP_VERSION_CHECK='1'
$env:SPICA_85D_PIP_CHECK='1'
.\.venv\Scripts\python.exe -B -m pip check
git diff --check
git status --short
```

pip check: **No broken requirements found.**, código 0. No se consultan índices
ni se instala nada; se permite su consulta local de versión Windows, manteniendo
guardias de red y rutas. Suite, dirigidas y pip: contadores finales **0 red,
0 rutas operativas, 0 SQLite operativos y 0 procesos no admitidos**. Las pruebas
usan contexto propietario por los temporales privados Python 3.15, sin cambiar ACL.

## Instrumentación y seguridad

El arnés inicial se detuvo porque su guardia exec bloqueó la carga diferida del
códec estándar utf-8-sig; no era una instrucción del JSON ni un defecto del
consumidor. Se precargó ese códec antes de instalar la guardia y se repitió el
arnés, conservando el log inicial. Ensayo final: **0 red, 0 SQLite, 0 procesos,
0 escrituras y 0 ejecución dinámica** en el proceso. Las pruebas también bloquean
eval/exec, archivos, red, SQLite, procesos y motores QA/científicos; strings con
instrucciones, URLs y rutas ficticias permanecen datos sin ejecutarse.

Logs propios privados, sin las 169 exportaciones persistidas:

```text
%TEMP%\spica-85d-xbw3g9s7\nuevas.log
%TEMP%\spica-85d-xbw3g9s7\dirigidas.log
%TEMP%\spica-85d-xbw3g9s7\suite-completa.log
%TEMP%\spica-85d-xbw3g9s7\piloto-final.log
%TEMP%\spica-85d-xbw3g9s7\guardia-piloto-final.log
%TEMP%\spica-85d-xbw3g9s7\guardia-piloto.log
%TEMP%\spica-85d-xbw3g9s7\guardia\sitecustomize.py
```

No se accede al CSV operativo, RAW permanente, staging, SQLite operativo ni
evidencias PNDA. No se afirma una nueva inspección física de recursos que se
mantuvieron cerrados ni control de cambios de terceros. Cero conexiones/GET,
descargas, instalaciones, migraciones, commits o push. Las bases temporales de
fixtures de la suite son distintas de las operativas.

La [matriz de 29 brechas](brechas_reconciliadas_pnda_paso84i.md) conserva sus IDs
y estados: **2 resueltas documentalmente, 17 parciales, 8 pendientes y
2 contradicciones; 27 abiertas**. No se cambia evidencia, aplicabilidad o
equivalencia editorial; no se activa ciencia, normaliza HORA/UBIGEO o convierte PP.

## Git final y comprobación documental

Misma rama **feature/suadc-http** y HEAD **ce2bf49**, índice intacto:

```text
?? docs/contrato_consumo_qaqc_paso85d.md
?? docs/piloto_consumo_qaqc_paso85d.md
?? src/spica/calidad/consumo.py
?? tests/test_consumo_qaqc_85d.py
```

**Cuatro archivos nuevos, cero archivos seguidos modificados**. git diff --check,
git diff --exit-code HEAD e índice sin errores. Se revisaron expresamente los
archivos sin seguimiento: dos Python con sintaxis compilada en memoria y sin
definiciones duplicadas; dos informes, seis tablas y 17 enlaces locales correctos.
UTF-8, bloques Markdown y espacios finales comprobados. Los conteos del informe
se cotejaron con métricas y logs privados completos, sin abrir enlaces externos.
No se alteraron código previo ni informes históricos.

## Pendientes y dictamen

El consumidor demuestra coherencia limitada, no autenticidad, verificación física,
ejecución real de reglas o aptitud científica. La coordinación de IDs sigue siendo
externa; no hay estado entre lotes, catálogo, migración ni persistencia operacional.
El agotamiento se maneja en proceso, sin garantía frente a terminación por el SO.

Para un eventual **85-E**, revisar primero el perfil aceptado, las políticas entre
lotes, privacidad y procedencia independiente; cualquier persistencia requiere
diseño y autorización propios. No integrar automáticamente al catálogo ni al
procesamiento científico. **APTO CON RESTRICCIONES. Esperar auditoría.**
