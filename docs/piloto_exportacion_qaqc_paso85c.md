# PASO 85-C — Piloto offline de exportación trazable

Fecha local: **2026-11-08, America/Lima**; ensayo técnico **2026-11-09 UTC**.
**APTO CON RESTRICCIONES** para revisión, sin permisos científicos u operativos.
Contrato: [exportación experimental 0.1.0](contrato_exportacion_qaqc_paso85c.md).

## Git y alcance recuperados

Estado inicial: limpio, rama **feature/suadc-http**, HEAD **b2c0171**. PASO 85-B
consolidado. Historial inicial comprobado:

```text
b2c0171 SUADC: versionado y restricciones QAQC estructural nivel 0
3535a47 SUADC: auditoria y piloto QAQC estructural nivel 0
496976d SUADC: vinculacion verificable de evidencia documental
f6c2a36 SUADC: auditoria de procedencia y piloto documental PNDA
1c06125 SUADC: contratos experimentales de metadatos documentales
```

Se crean únicamente un módulo experimental, sus pruebas y estos dos informes.
No se modifican modelos estables, reglas, motor, restricciones 85-B, catálogos,
inspectores, transportes, main.py, .gitignore ni dependencias. No se crea otro
motor QA, almacenamiento o integración operacional.

## Piloto sintético y contexto explícito

Se reutilizan las [fixtures 85-A](../tests/test_piloto_qaqc_estructural_85a.py):
**12 escenarios, 13 entradas, siete definiciones y 169 emisiones**. No existe
una muestra PNDA independiente autorizada para este piloto y no se busca en
RAW ni se abre el CSV operativo. Las pruebas unitarias adicionales usan un
registro MAGNITUD/001.20 y descriptores ficticios independientes de instituciones.

Contexto del piloto exportado: espacio_id **spica:piloto:85c**, evaluacion_id
**regresion-001**, escenario_id S01…S12 y entrada_id **entrada-N**, donde N es
el número lógico original de cada fixture. Se aporta la configuración sintética
exacta y las incertidumbres/restricciones del expediente de cada escenario.
Metadatos requeridos y ausentes quedan **null**: el 85-A no aportaba inventario
formal exhaustivo y no se inventa uno. ProcedenciaQA desconocida se conserva.
Las referencias de formatos son ficticias; no se presentan como evidencia SENAMHI.

La evaluación por cada entrada se conserva: cuatro reglas por fila y tres VAL
por tres variables. **13 × (4 + 3 × 3) = 169**, no 169 observaciones ambientales.
Hay 91 visitas regla–entrada con expansión de campos, sin diagnósticos añadidos.

| Escenario | Entradas | Exportaciones | Satisfechas | Alertas | Problemas | No evaluadas | Incompletas |
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

VAL-001, VAL-002 y VAL-004: **39 exportaciones cada una**. EST-001, TMP-002,
ID-002 e ID-004: **13 cada una**. Se conservan **169 resultado_id distintos**,
sin duplicados u omisiones respecto de la cardinalidad prevista.
Cada campo objetivo, diagnóstico, estado y versión coincide con el resultado
nativo; el exportador no calcula condiciones nuevas ni altera las anteriores.

## Identidades, diagnóstico y restricciones

Todos los paquetes conservan regla **1.0.0**, QA **1.0.0**, emisor **1.0.1**,
política de restricciones **1.0.0** y exportación **0.1.0**. Las pruebas también
confirman emisor null cuando no se declaró; no se reconstruye desde la versión QA.

S06 conserva TEMP/HR/PP separadas y el valor CSV extra; S02 mantiene TEMP no
aportado y campo_no_disponible. S08 conserva HORA 12345, formato no disponible
y no evaluación. S09 conserva UBIGEO 007777.0 y alerta representacional.
S10 conserva PP 1.50 y gramática satisfecha sin conversión. S07 no elige una
identidad física entre los dos mappings; S12 mantiene ambas filas de igual
contenido con identidades contextuales/posiciones distintas. No se deduplica.

restricciones_resultado se invoca automáticamente una vez por exportación.
Se preservan **tipo, código, operaciones y motivo** de cada anotación, sin
confundirlas con nuevas evaluaciones o permisos:

| Código de anotación | Apariciones en los 169 paquetes |
|---|---:|
| alcance_estructural, informativa | 169 |
| sin_validacion_cientifica | 169 |
| sin_equivalencia_editorial | 169 |
| numero_sin_metrologia | 82 |
| pp_sin_conversion | 43 |
| hora_sin_transformacion | 16 |
| ubigeo_sin_interpretacion | 16 |
| identidad_ubicacion_no_verificadas | 26 |
| condicion_no_evaluada | 29 |
| condicion_incompleta | 16 |
| **Total de anotaciones** | **735** |

Son **169 informativas y 566 bloqueantes de usos del resultado**, dentro de los
169 diagnósticos. Las restricciones de campo incluyen el contexto de fila completa
en las emisiones no VAL de S06: eso explica 82/43/16/16 en vez de contar solo
objetivos de filas bien formadas. No implica que se evaluaran sus condiciones.
Las referencias PROV se prueban aparte: no forman parte de las siete seleccionadas.

Satisfecha sigue siendo una condición estructural y puede conservar bloqueos.
Las 29 N mantienen motivo; las 16 I mantienen impedimento. No se convierten en
aprobación silenciosa ni existe autorización de ejecutar ciencia.

## Reproducibilidad y presupuesto observado

Ensayo UTC: **2026-11-09T00:40:33.483163+00:00** a
**2026-11-09T00:40:36.482587+00:00**. Tiempos de auditoría, no de observación.
Se repite el piloto, se invierte el orden de escenarios/emisiones y se comprueba
igualdad exacta del diccionario resultado_id→JSON. Entradas originales intactas.
Las repeticiones de determinismo no se suman al total ni a las pruebas.

Tamaño UTF-8 por paquete: **3837–6789 bytes**, todos bajo 1 MiB; suma **888887
bytes**. Para reproducibilidad se forma únicamente en memoria el lote de JSON
ordenados por resultado_id, unidos por LF y sin LF final: **889055 bytes**.
SHA-256 de esa representación sintética:

```text
8bb1a3662edc96b674886fba64b7aa8488e1cefc9d650e4597b5bd95077d6af5
```

No es SHA de un archivo científico ni evidencia de verificación física.
No se guardan las 169 exportaciones por defecto. El arnés guarda solo métricas
en el log privado; la función de exportación no escribe. La guardia del arnés
prohíbe toda escritura en el proceso, SQLite, red y procesos adicionales;
contadores **0/0/0/0**. El log de consola combina métricas y aviso de guardia;
PowerShell puede representar stderr como NativeCommandError, aunque el arnés
terminó con código **0**, sin excepción de Python ni una operación bloqueada.

## Pruebas y regresiones

[25 tests nuevos](../tests/test_exportacion_qaqc_85c.py), con subcasos: cinco
estados, S con bloqueos, inventarios desconocidos/declarados, HORA/UBIGEO/PP
intactos, metrología no acreditada, versiones separadas, IDs por contexto/campo/
regla/versión/posición, filas iguales, huella de contenido, JSON estricto, Unicode,
límites exactos UTF-8, tipos rechazados, contratos previos, procedencia declarada,
sin mutaciones/permisos/efectos y regresión completa de las 169 exportaciones.
La recuperación por json.loads conserva estructura y restricciones; no se
reconstruyen objetos ejecutables ni se valida JSON externo para uso operativo.

Ensayo inicial: **24 tests nuevos aprobados, cero fallos/errores, 1.824 s**.
Se añadió una prueba de rechazo de contexto/tipos externos y se reforzó la
comparación completa de restricciones. **Dirigidas finales: 98 aprobadas,
cero fallos/errores, 14.987 s**: 53 Nivel 0 + ocho 85-A + doce 85-B + 25 nuevas.
**Suite completa realmente ejecutada: 1651 aprobadas, cero fallos, cero errores,
cero omitidas, 158.209 s, código 0, salida OK**. Son 1626 anteriores + 25 nuevas;
no se suman de nuevo las dirigidas, subcasos o repeticiones. Se conservan las
regresiones Nivel 0 y posteriores, incluido el ensayo de 744 filas sintéticas/
22320 resultados, sin reejecutar el piloto institucional histórico.

Entorno verificado: **Python 3.15.1**, HTTPX **0.28.1**, SQLite **3.53.4**,
intérprete de .venv. Comandos, con ruta de importación temporal y sin cambiar
archivos de configuración:

```powershell
$env:PYTHONPATH="$env:TEMP\spica-85c-ycxau5rk\guardia;$PWD\src;$PWD\tests;$PWD"
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -B -m unittest test_calidad_nivel0 test_piloto_qaqc_estructural_85a test_contratos_qaqc_85b test_exportacion_qaqc_85c -v
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
$env:PIP_NO_INDEX='1'
$env:PIP_DISABLE_PIP_VERSION_CHECK='1'
$env:SPICA_85C_PIP_CHECK='1'
.\.venv\Scripts\python.exe -B -m pip check
git diff --check
git status --short
```

La salida completa de unittest se conservó en los logs privados. pip check:
**No broken requirements found.**, código 0; no se consultaron índices. Se
permite su consulta local de versión Windows sin desactivar guardia de red/rutas.
Guardia final de suite, dirigidas y pip: **0 red, 0 rutas operativas, 0 SQLite
operativos y 0 procesos no admitidos**. SQLite temporal de pruebas no es operativo.
Se ejecutaron las pruebas como propietario para acceso a los temporales privados
de Python 3.15, sin cambios de ACL.

## Seguridad, Git y pendientes

Estado final, misma rama/HEAD e índice sin modificaciones:

```text
?? docs/contrato_exportacion_qaqc_paso85c.md
?? docs/piloto_exportacion_qaqc_paso85c.md
?? src/spica/calidad/exportacion.py
?? tests/test_exportacion_qaqc_85c.py
```

Cuatro archivos nuevos y **cero archivos seguidos modificados**, comprobados con
git diff --exit-code HEAD e índice. git diff --check sin errores. Se revisan
también los cuatro archivos sin seguimiento: dos Python compilados en memoria,
sin definiciones duplicadas; dos informes, tres tablas y 14 enlaces locales
correctos, sin consultas externas. UTF-8, finales de línea y ausencia de espacios
finales comprobados. Los ejemplos documentales usan solo memoria.

Los logs propios quedan fuera de Git:

```text
%TEMP%\spica-85c-ycxau5rk\nuevas.log
%TEMP%\spica-85c-ycxau5rk\dirigidas.log
%TEMP%\spica-85c-ycxau5rk\suite-completa.log
%TEMP%\spica-85c-ycxau5rk\piloto.log
%TEMP%\spica-85c-ycxau5rk\guardia\sitecustomize.py
```

No se accedió al CSV operativo, RAW permanente, staging, SQLite operativo ni
evidencias PNDA. No se afirma una inspección física nueva de recursos que se
mantuvieron cerrados ni se controla actividad de terceros. Cero conexiones/GET,
descargas, instalaciones, migraciones, commits o push. Las pruebas históricas
usan fixtures y bases temporales aisladas; no los recursos operativos.

La [matriz de 29 brechas](brechas_reconciliadas_pnda_paso84i.md) conserva IDs y
estados: **2 resueltas documentalmente, 17 parciales, 8 pendientes y
2 contradicciones; 27 abiertas**. No se actualiza evidencia, aplicabilidad o
equivalencia editorial. No se normaliza HORA/UBIGEO, convierte PP, procesa clima
o activa Nivel 1. Este piloto no acredita conformidad científica.

Riesgos residuales: contexto declarado sin autenticación, unicidad global
condicionada al espacio/ejecución coordinados, ausencia de lector contractual
para JSON ajeno y de consumidor persistente que detecte reutilización de IDs.
Las exportaciones podrían contener información sensible suministrada por el
llamador: no se publican ni registran automáticamente. No se modifica ningún
consumidor para interpretar JSON como permiso.

Recomendación para un eventual **85-D**: auditoría de esquema/identidad y diseño
de consumidor offline que conserve contexto, versiones y restricciones, y detecte
misma identidad con huella distinta sin sobrescribir. Requiere revisión previa;
no se implementa ahora ni habilita operaciones científicas.

**APTO CON RESTRICCIONES. Esperar auditoría antes de continuar.**
