# PASO 72: motor QA/QC Nivel 0

## Alcance y arquitectura

`spica.calidad` evalúa consistencia técnica, documental y trazabilidad. Es una capa
separada de adquisición y del perfilado descriptivo; no certifica observaciones ni
implementa QA/QC científico de niveles 1/2. No cambia contratos previos, RAW,
conectores, planificador ni modelos científicos.

La inspección inicial encontró Git limpio en `feature/suadc-http`, HEAD **b4c2c38**,
commit del PASO 71. Se revisaron `LectorCSV`, consultas, verificación CSV, núcleo,
`EvidenciaDocumental` y el perfilador. La única carencia para reutilizar el parser
numérico era su interfaz privada: se añade `spica.perfilado.interpretacion`, una
fachada pública que delega en `_interpretar`, `_dia` y `_patron_hora` ya existentes.
No se copia ni modifica su semántica, ni se ejecuta nuevamente el perfilador agregado.
La interpretación tiene versión **1.0.0** y conserva `Decimal` exacto y sus límites.

## Contratos versionados

Contrato QA **1.0.0**, reglas **1.0.0**. Una modificación futura de las condiciones
de una regla debe distinguirse mediante versión. Los identificadores son propios de
SPICA, sin atribuirlos al productor institucional.

- `ProcedenciaQA`: Fuente, recurso, adquisición, asset_id, SHA-256 de referencia y
  `EvidenciaDocumental` opcional. Los desconocidos siguen como `None`.
- `ReferenciaDocumentalQA`: referencia, descripción, hash documental y revisión
  opcionales. Un hash de referencia no acredita comprobación física del documento.
- `FormatoDocumentadoQA`: campo y uno de cuatro formatos cerrados, con referencia
  explícita. No admite expresiones regulares ni código aportado por configuración.
- `ConfiguracionQA`: categorías, reglas, variables TEMP/HR/PP, formatos, zona o
  identidades documentadas y política numérica compartida con el perfilador.
- `RegistroQA`: fila lógica y líneas físicas, ID original, ESTACION literal,
  campos originales y procedencia propia de la entrada si está disponible. ID no
  es código de estación. Las filas CSV defectuosas conservan también su tupla bruta.
- `ResultadoQA`: regla/version/categoría, registro y procedencia, campos/valores
  originales, referencias documentales, parámetros, estado y código diagnóstico.
  No incluye un indicador de validez científica. Varios resultados pueden referir
  a la misma fila y todos conservan los textos originales.
- `InformeQA`: alcance final, registros examinados/finalizados, resultados emitidos,
  evaluaciones incompletas, conteos por categoría/estado, reglas con resultados
  emitidos, procedencia, configuración y límites para reproducibilidad.

Estados individuales:

| Estado | Significado limitado |
| --- | --- |
| COMPROBACION_SATISFECHA | Se cumplió la condición concreta de esa regla |
| ALERTA_DOCUMENTAL | El literal discrepa con un formato/documento explícito |
| PROBLEMA_TECNICO | Se detectó un problema técnico, no un rechazo científico |
| NO_EVALUADO | Falta evidencia/valor pertinente o la operación está fuera de alcance |
| EVALUACION_INCOMPLETA | La comprobación no pudo terminar bajo sus condiciones/límites |

`ResultadoQA.estado_evaluacion` distingue COMPLETA, INCOMPLETA y NO_EVALUADA según
el estado individual. El informe global es COMPLETA si se agotaron las reglas y
la fuente confirmó su alcance completo, incluso si hubo alertas o NO_EVALUADO.
Es INCOMPLETA si hay límites, interrupciones, fuente incompleta o reglas con estado
EVALUACION_INCOMPLETA. Una fuente completa sin filas produce NO_EVALUADA. Ninguno
de esos estados significa que todas las observaciones sean científicamente válidas.

## Registro cerrado de reglas

Todas las reglas siguientes tienen versión **1.0.0**:

| Identificador | Categoría | Comprobación |
| --- | --- | --- |
| L0-EST-001 | estructura | Coherencia del registro tabular recibido |
| L0-VAL-001 | valores | Vacío frente a valor literal presente |
| L0-VAL-002 | valores | Número finito interpretable bajo la política técnica |
| L0-VAL-003 | valores | NaN/Infinity y otros literales no finitos reconocidos |
| L0-VAL-004 | valores | Formato numérico documental explícito |
| L0-TMP-001 | temporales | Formato AAAAMMDD y calendario civil |
| L0-TMP-002 | temporales | Formato HORA hhmmss y rangos léxicos |
| L0-TMP-003 | temporales | Disponibilidad de referencia documental de zona |
| L0-TMP-004 | temporales | Incertidumbre de instante absoluto; no construye instantes |
| L0-ID-001 | identidad/ubicación | Nombre literal presente |
| L0-ID-002 | identidad/ubicación | Identidad física referenciada o no acreditada |
| L0-ID-003 | identidad/ubicación | LONGITUD/LATITUD declaradas presentes o ausentes |
| L0-ID-004 | identidad/ubicación | UBIGEO frente a seis caracteres, solo con evidencia |
| L0-ID-005 | identidad/ubicación | Presencia de ocho metadatos de ubicación |
| L0-PROV-001 | procedencia | Referencia de institución/fuente |
| L0-PROV-002 | procedencia | Identidad declarada de recurso |
| L0-PROV-003 | procedencia | Identificador de adquisición |
| L0-PROV-004 | procedencia | Referencia de activo RAW |
| L0-PROV-005 | procedencia | SHA-256 de referencia |
| L0-PROV-006 | procedencia | Documento disponible y asociado a fuente/recurso |
| L0-PROV-007 | procedencia | Licencia declarada/referenciada o desconocida |
| L0-PROV-008 | procedencia | Coherencia con la procedencia propia de ObservacionLocal |

Las cuatro reglas de valores se aplican a cada variable seleccionada; con tres
variables hay **30 resultados por fila**, procedentes de 22 definiciones. La selección
por categorías e IDs mantiene orden canónico del registro cerrado, no el orden de
una configuración arbitraria. IDs desconocidos, selecciones contradictorias y formatos
no enumerados se rechazan. No hay eval, exec, plugins ni importación dinámica de reglas.

## Semántica de las comprobaciones

Un vacío es exactamente `""`; se informa problema técnico de contenido, sin inferir
ausencia de medición. Los espacios permanecen presentes y pueden ser no interpretables.
NaN/Infinity tienen regla específica; no se convierten en extremos, vacíos o rechazos
científicos. Exceder el presupuesto de interpretación produce EVALUACION_INCOMPLETA,
no un número declarado inválido. No se excluyen extremos o centinelas numéricos.
Se reutiliza la gramática decimal ASCII y presupuestos del PASO 71, una vez por celda.

Los formatos institucionales no se infieren de la frecuencia de los valores. Si no
se proporciona evidencia explícita, L0-VAL-004, L0-TMP-001/002 y L0-ID-004 devuelven
NO_EVALUADO. Se admiten número ASCII finito, AAAAMMDD, hhmmss y texto de seis caracteres.
Una fecha con ocho dígitos y calendario imposible es PROBLEMA_TECNICO; discrepancias
de representación son ALERTA_DOCUMENTAL. Un formato vacío es NO_EVALUADO y la regla
de presencia mantiene su propio diagnóstico. No se rellenan ceros de HORA/UBIGEO.

Documentar una zona solo satisface su presencia documental: no se asigna a filas.
L0-TMP-004 conserva NO_EVALUADO incluso con zona porque la construcción de instantes
está fuera de este nivel. No se usa UTC o America/Lima por ubicación o suposición.
ID, ESTACION y UBIGEO conservan sus diferentes significados. Una identidad física
solo puede referenciarse con correspondencia literal y evidencia suministradas;
varios identificadores para un nombre generan alerta de ambigüedad. No se verifica
físicamente una instalación. Coordenadas presentes no equivalen a coordenadas
interpretables, CRS conocido o geodesia validada; esa regla solo comprueba disponibilidad.

Asset_id, adquisición y SHA satisfacen únicamente presencia de referencias, sin
abrir RAW ni verificar archivos. El documento se contrasta con Fuente/recurso;
un documento ajeno produce problema técnico y no se usa para licencia. Una referencia
de licencia no acredita su texto, vigencia, permisos de redistribución o conformidad
jurídica. La evidencia documental original se conserva con sus revisiones desconocidas.

## Motor, límites y cierre

```python
from spica.adquisicion.verificacion import LectorCSV
from spica.calidad import EvaluadorNivel0, ProcedenciaQA, ConfiguracionQA

# entrada y procedencia se construyen con las referencias reales del recurso.
entrada = LectorCSV(ruta_csv, delimitador=",", campos_esperados=16)
with EvaluadorNivel0(entrada, procedencia, configuracion=ConfiguracionQA()) as motor:
    for resultado in motor:
        consumir(resultado)  # No acumular todas las filas/resultados.
informe = motor.informe  # Solo definitivo tras cierre y comprobación de la fuente.
```

El motor posee un contexto de `LectorCSV` o `ConsultorLocalCSV` creado pero no abierto,
una ejecución por instancia. En lectura directa comprueba el encabezado exacto del
perfil SENAMHI y omite esa fila como encabezado. Una consulta debe seleccionar una
sola variable para representar cada fila una vez; conserva sus 16 campos y QA evalúa
las variables configuradas realmente presentes. La selección multivariable de consulta
se rechaza para no duplicar filas ni deduplicar silenciosamente. IDs repetidos en
filas diferentes se conservan. Los números lógicos deben aumentar; no se confunden
con el orden cronológico de FECHA, que no se exige para la evaluación.

`evaluar_registro()` es una operación pura sobre `RegistroQA`, sin certificar alcance
de un archivo. `adaptar_registro()` conserva el registro y sus campos, sin parser nuevo.
Una estructura incoherente impide presentar las reglas de esa fila como satisfechas.
Una procedencia contradictoria queda preservada en contexto y registro, con su alerta.

Límites del motor: **10.000 registros**, **100.000 resultados**, 65.536 caracteres por
celda y 1.048.576 por registro. Topes configurables: dos millones de registros y cinco
millones de resultados. La fuente conserva además sus límites de bytes, muestra,
líneas, registros y campos. La política numérica mantiene 128 caracteres, 64 dígitos
de mantisa y exponente absoluto de hasta 1.000 de forma predeterminada. Se acotan
categorías, reglas, variables, formatos y correspondencias documentales de identidad.

Se retiene una fila, la interpretación de hasta tres celdas, el resultado actual y
conteos de cardinalidad fija por reglas/categorías/estados. No hay catálogo/índice QA,
SQL ni ficheros de resultados automáticos. El consumidor controla su propia acumulación.
Los presupuestos no constituyen cuota exacta de memoria del SO. El informe no conserva
todas las filas ni todos los resultados.

`cancelar()` o un Event externo detienen cooperativamente, incluso entre resultados
de una fila. `break`, excepciones, límites y cancelación cierran la fuente y mantienen
estado incompleto; KeyboardInterrupt se propaga. El límite de resultados puede cortar
una fila y es conservador aun si coincide con el último resultado: no presume EOF.
El límite de registros puede leer una fila adicional antes de detener la evaluación.
`registros_examinados` y `registros_finalizados` distinguen la fila parcialmente evaluada.
Los resultados individuales emitidos conservan su alcance; el informe global debe
revisarse antes de afirmar que la evaluación del subconjunto terminó.

Para la misma versión del archivo, referencias y configuración se mantienen orden,
versiones, valores y resultados. No se incorporan fechas de evaluación variables al
resultado. La fuente comprueba identidad al cierre; no hay snapshot, bloqueo frente
a escritores ni prueba de autenticidad institucional. La comprobación física de hashes
en el piloto es externa al motor y se informa separadamente.

## Verificación y piloto

Se verificaron **53 pruebas nuevas** con archivos sintéticos aislados, sin acceder
a RAW/staging/SQLite operativo. Se cubren estados y reglas, ausencia de evidencia,
límites, cancelación, cierre, determinismo, memoria y conservación de valores/extremos.
Una prueba confirma una sola llamada al parser numérico compartido por celda. Otra
impide imponer dígitos cuando UBIGEO solo tiene documentada una anchura de seis caracteres.
La prueba de memoria consume 300 y 10.000 filas sin acumular resultados, exige pico
Python menor de 5 MiB y crecimiento menor de 1 MiB para esas fixtures; no promete ese
pico para cualquier consumidor, política o configuración.

Los resultados de la suite completa y del piloto autorizado se incorporan tras
comprobarlos. El piloto se limita al nombre literal IMATA y enero civil de 2015.

Entorno comprobado: **Python 3.15.1, HTTPX 0.28.1 y SQLite 3.53.4**, usando `.venv`
y `-B`. Antes de acceder al original operativo se ejecutó:

```text
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
Ran 779 tests in 184.734s
OK

.\.venv\Scripts\python.exe -B -m pip check
No broken requirements found.
```

**779 aprobadas (726 anteriores y 53 nuevas), cero fallos y cero errores.** No se
instalaron dependencias. Todas las pruebas automatizadas usan fixtures sintéticas;
no abren el almacenamiento operativo ni requieren conexiones externas.

El cierre final se conservó además en un registro temporal fuera de Git, después
de que una sesión de herramientas perdiera su salida. Se repitió la suite para
obtener evidencia recuperable, no para ocultar pruebas fallidas. `resultado.json`
registra código de salida 0 y `unittest.log` conserva el detalle de las 779 pruebas.
La regla UBIGEO final comprueba solo anchura de seis caracteres; no exige dígitos.

## Piloto final IMATA: enero de 2015

Ejecución técnica del **2026-10-29, 21:09:14–21:10:34 (America/Lima, UTC−05)**,
equivalente a **2026-10-30, 02:09:14–02:10:34 UTC**. Estas horas describen el proceso,
no asignan zona a las observaciones. Se repitió el piloto de solo lectura después
de precisar la anchura documental de UBIGEO; se informa aquí la ejecución final.

Selección exacta: **IMATA**, fechas civiles inclusivas **2015-01-01–2015-01-31**.
La consulta seleccionó TEMP para entregar una sola observación local por fila,
conservando los 16 campos; QA evaluó TEMP/HR/PP originales de esas mismas filas.
Límites: 1.000 resultados de consulta, 1.000 registros QA y 30.000 resultados QA.
No se alcanzaron. El lector mantuvo 128 MiB, bloques de 64 KiB y dos millones de
registros como presupuestos de origen.

Resultado: **744 filas examinadas y finalizadas**, **22.320 resultados individuales**,
**22 reglas/versiones ejecutadas**, **cero EVALUACION_INCOMPLETA**. Informe global
COMPLETA, motivo `eof`. La fuente recorrió 50.474.012 bytes más su muestra inicial
de 65.536 bytes, 416.274 registros incluido encabezado, hasta EOF, con ASCII
comprobado y cero anomalías de estructura. La evaluación QA se limitó a las 744
filas seleccionadas; el recorrido del origen completo permite acreditar la selección
sin presumir orden cronológico del archivo.

### Resultados por categoría

| Categoría | Satisfecha | Alerta documental | Problema técnico | No evaluado | Incompleta |
| --- | ---: | ---: | ---: | ---: | ---: |
| Estructura | 744 | 0 | 0 | 0 | 0 |
| Valores | 6567 | 0 | 43 | 2318 | 0 |
| Temporales | 1178 | 310 | 0 | 1488 | 0 |
| Identidad/ubicación | 2232 | 744 | 0 | 744 | 0 |
| Procedencia | 5952 | 0 | 0 | 0 | 0 |
| **Total** | **16673** | **1054** | **43** | **4550** | **0** |

Estos son conteos de resultados de reglas, **no números de observaciones válidas**.
Una fila puede tener varias alertas. Una comprobación satisfecha no elimina las
incertidumbres ni anula los demás resultados de esa fila.

### Hallazgos de contenido y documentación

- **43 celdas vacías**: TEMP **13**, HR **17**, PP **13**, conservadas sin imputación
  ni exclusión. Son celdas, no 43 filas distintas ni mediciones ausentes demostradas.
- Los **2.189 valores no vacíos** resultaron finitos e interpretables bajo la política
  numérica técnica. No hubo NaN/Infinity ni números no interpretables en este piloto.
  No se aplicaron rangos físicos, cambios de unidades o exclusiones de extremos.
- **310 alertas HORA**, por literales de cinco posiciones frente a hhmmss. Los otros
  **434** satisfacen la condición léxica de seis posiciones. No se reconstruye nada.
- **744 alertas UBIGEO**, texto literal `40514.0`, de siete caracteres frente a los
  seis documentados. Se compara anchura, no pertenencia a INEI ni exigencia de dígitos.
- **744 NO_EVALUADO** por zona desconocida y **744** por instante no determinable sin
  zona; ninguna fecha/hora se convierte a UTC o America/Lima.
- **744 NO_EVALUADO** por identidad física no acreditada. `ESTACION=IMATA` y los ID
  originales de registros no se convierten en códigos de estación.
- **2.232 NO_EVALUADO** para formato numérico institucional: no se inventa una gramática
  normativa de representación ASCII/exponentes a partir del simple tipo numérico
  declarado. La interpretación técnica sí se comprueba mediante otras reglas.
- Los vacíos producen además **86 NO_EVALUADO** en las dos comprobaciones numéricas,
  al no existir número pertinente. Junto con los anteriores suman los 4.550 resultados.
- Nombre y metadatos de ubicación están presentes en las 744 filas. No se validan
  geodesia, CRS, precisión, identidad física ni plausibilidad meteorológica.

Muestra acotada de trazabilidad real:

| Registro lógico de origen | ID original | Regla | Campo / valor original | Resultado |
| ---: | --- | --- | --- | --- |
| 166511 | `166510` | L0-TMP-002 | HORA `00000` | ALERTA_DOCUMENTAL |
| 166511 | `166510` | L0-ID-004 | UBIGEO `40514.0` | ALERTA_DOCUMENTAL |
| 166511 | `166510` | L0-VAL-004 | TEMP `-0.6` | NO_EVALUADO: formato institucional no disponible |
| 166624 | `166623` | L0-VAL-001 | TEMP `""` | PROBLEMA_TECNICO: vacío |

Se conservan los campos originales completos en cada referencia de registro;
no se renumeran las filas por su posición dentro del subconjunto.

### Procedencia y evidencia realmente utilizadas

- Fuente original: `Fuente("SENAMHI", "SENAMHI")`.
- Adquisición: `ff8e7846a9b14568aad924aa8ca93f74`.
- Asset RAW: `71df55229ee947fb8e7fed8b1403289e`.
- Recurso: URL CSV oficial ya persistida, conservada exactamente con sus escapes.
  No se hizo solicitud HTTP.
- Se recuperó y validó el paquete documental existente mediante el deserializador
  del catálogo. Su estado sigue **DECLARADO**; publicación, capacidades y fecha de
  descubrimiento conservan sus valores históricos.
- Existe referencia de licencia `http://opendefinition.org/licenses/odc-by/`;
  `licencia_declarada=None`. Se comprueba disponibilidad de esa referencia, no el
  texto, vigencia ni alcance jurídico de la licencia. No se consultó el enlace.
- `revision_documental`, `revision_producto` y `revision_fuente` siguen **None**.
- FECHA/HORA/UBIGEO usaron como antecedente la inspección del diccionario en el PASO
  69, SHA de referencia `1851039a07682a3f202314f6f8811fc616cb4ca2a486c9e737fd8cea62a4b4dd`.
  No se abrió ni verificó físicamente ese XLSX de nuevo. La regla de UBIGEO usa su
  anchura de seis caracteres, sin imponer composición numérica no demostrada.

Las reglas de procedencia satisfechas solo constatan referencias y coherencia de
metadatos. La comprobación física del CSV siguiente es una operación separada.

### Integridad física y ausencia de escrituras operativas

Original autorizado:

```text
C:\Users\Propietario\SPICA_DATOS\raw\sha256\3d\3d3e8a0a75e070d0b8111faf921be17140c3a0f9db2b4c25d72d99a15a950eab
```

Antes y después: **50.474.012 bytes**, SHA-256 calculado leyendo los bytes por bloques:

```text
3d3e8a0a75e070d0b8111faf921be17140c3a0f9db2b4c25d72d99a15a950eab
```

El inventario de RAW/staging coincide en archivos, directorios, tamaños, hashes,
inode, mtime y enlaces. No se compara atime, que el sistema puede actualizar al leer.
Se preservaron el original CSV, el sintético, el marcador, catálogo y archivo previo
de staging. RAW/temporales sigue vacío; staging solo contiene `paso64-sintetico.bin`.

SQLite operativo se abrió exclusivamente con `mode=ro&immutable=1`, `query_only=ON`
y `trusted_schema=OFF`, sin WAL/SHM/journal. Se comprobó esquema conocido, y se
consultó la evidencia existente sin APIs RAW que registren eventos/verificaciones.
La lectura encontró **v2, dos activos y diez eventos**. El catálogo de 32.768 bytes
conserva antes/después SHA-256
`946d2512795c5ae3a68113f63438110be66dee32488ad02e86d550da040d4a0d`.
No se creó evidencia nueva, cambiaron estados RAW ni persistieron resultados QA.

Los únicos registros auxiliares del procedimiento están en un directorio temporal
de control fuera de Git, RAW y staging:

```text
C:\Users\Propietario\AppData\Local\Temp\spica-paso72-validacion-d23273d0a7354420855ffa1e9521b5ce
```

Contiene `unittest.log`, `resultado.json`, el guion temporal `piloto.py` y
`piloto_resultado.json`. Son evidencia técnica de verificación, no copias del CSV
ni nuevos originales científicos. No se modificaron ACL ni dependencias.

## Limitaciones y dictamen

**APTO CON RESTRICCIONES** para QA/QC Nivel 0. Deben resolverse documentalmente
HORA/UBIGEO, zona, identidad estable, convenciones textuales institucionales y
significado de faltantes/sentinelas antes de normalizar o añadir reglas científicas.
La referencia de licencia disponible requiere revisión independiente de sus condiciones.
Los resultados satisfechos no acreditan calibración, plausibilidad, completitud o
representatividad científica. No hay exclusión automática de observaciones.

No hay soporte de otros encabezados sin adaptación explícita, índices QA persistentes,
evaluación distribuida, bloqueo frente a escritores ni transacción global de resultados.
Se requiere uso secuencial y revisión del informe final; los resultados ya emitidos
pueden pertenecer a un recorrido parcial. Las referencias documentales son aportadas
por el operador: su autenticidad no se demuestra por existir un identificador/hash.
No se implementaron niveles 1/2 ni análisis climático o ambiental.

## Estado final de Git

Se crearon siete archivos: `calidad/__init__.py`, `modelos.py`, `reglas.py`, `motor.py`,
`perfilado/interpretacion.py`, `tests/test_calidad_nivel0.py` y este documento. No se
modificaron archivos previamente rastreados, `main.py`, `.gitignore` ni `.venv`.
La rama y HEAD siguen en `feature/suadc-http` / `b4c2c38`. No hubo commits ni push.

`git diff --check`: código de salida 0. Los archivos nuevos, aún no rastreados,
también se revisaron directamente para detectar espacios finales, sin problemas.

```text
git status --short
?? docs/calidad_nivel0.md
?? src/spica/calidad/
?? src/spica/perfilado/interpretacion.py
?? tests/test_calidad_nivel0.py
```
