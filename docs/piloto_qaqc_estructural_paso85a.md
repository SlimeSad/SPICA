# PASO 85-A — Piloto aislado QA/QC estructural Nivel 0

Fecha: **2026-11-08**. **APTO CON RESTRICCIONES** para revisar el ensayo
estructural y su corrección de traza. Sin datos institucionales nuevos,
persistencia operativa o habilitación científica. El
[inventario de las 22 reglas](inventario_qaqc_nivel0_paso85a.md) distingue
implementación real, requisitos, pruebas y limitaciones.

## Alcance y arquitectura reutilizada

Git inicial limpio: **feature/suadc-http**, HEAD **496976d**, PASO 84-L consolidado.
Se reutilizan RegistroQA, ConfiguracionQA, ProcedenciaQA, ResultadoQA,
evaluar_registro, adaptar_registro y, para admisión tabular, EvaluadorNivel0
con LectorCSV. No se crea un motor, parser o validador paralelo.

Se seleccionan **siete reglas existentes**:
L0-EST-001, L0-VAL-001, L0-VAL-002, L0-VAL-004, L0-TMP-002,
L0-ID-002 y L0-ID-004. Cubren estructura recibida, presencia, gramática numérica,
formato explícito, ausencia de especificación de HORA, ambigüedad de identidad y
anchura UBIGEO. No se seleccionan reglas de interpretación espacial o temporal,
ni se activan reglas científicas superiores. Las otras quince reglas Nivel 0
siguen en código y se verifican en las regresiones anteriores.

La única corrección de producto es el objetivo de cada VAL incompleta en una
fila incoherente: ahora identifica TEMP/HR/PP por separado sin alterar la fila
bruta o el estado. El [inventario](inventario_qaqc_nivel0_paso85a.md) conserva
la reproducción previa del defecto 85A-01 y su alcance.

## Datos y metadatos del ensayo

Fixtures permanentes, exclusivamente ficticias, en
[test_piloto_qaqc_estructural_85a.py](../tests/test_piloto_qaqc_estructural_85a.py).
No contienen copias, hashes o mediciones de archivos institucionales.
Se reutilizan los nombres de columna del contrato existente, no valores reales.

La fila base usa ID `fila-ficticia-001`, ESTACION `ESTACION_FICTICIA_A`,
TEMP `+001.250`, HR `56.75`, PP `4.00`, HORA `reloj-no-acreditado` y UBIGEO
`ABC123`. Los otros campos están presentes como cadenas vacías; no se aportan
coordenadas, altitudes, zonas, frecuencias o unidades supuestas.
«Correcta» en S01 significa estructura tabular/textos coherentes bajo las reglas
seleccionadas, no completitud ambiental de todos sus metadatos.

La configuración base aporta una ReferenciaDocumentalQA explícitamente ficticia
para formato numérico ASCII de TEMP/HR/PP y anchura de seis caracteres de UBIGEO.
No se aporta formato HORA, zona, unidad PP o código territorial real. Estos
formatos sintéticos no se trasladan a SENAMHI ni se consideran documentos
físicamente cotejados. S07 aporta dos correspondencias de identidad ficticias
para mostrar la ambigüedad; ninguna se elige como identidad real.

El motor puro recibe ProcedenciaQA desconocida: los None se conservan, sin
inventar adquisiciones, activos o comprobaciones. Cada resultado conserva
regla/versión, registro/líneas, valores afectados, procedencia, evidencia cuando
se usa, parámetros, diagnóstico y estado. Las restricciones científicas globales
se conservan en el expediente de cada fixture, pues ResultadoQA no tiene un
campo general de restricciones o permisos.

No se usa la muestra PNDA 84-C. El expediente identifica resultados y metadatos,
no una muestra independiente autorizada con los seis valores. No se abrió el
CSV original ni se reejecutó el arnés 84-C o sus consultas RAW/SQLite.

## Doce escenarios y diagnósticos reales

Por entrada: **cuatro reglas por fila + tres VAL por tres variables = 13 resultados**.
S12 contiene dos entradas: **13 entradas en 12 escenarios, 169 resultados**.
Los resultados focales no son el único diagnóstico de cada fila.

| Escenario | Entrada o condición ficticia | Regla/campo focal | Estado y diagnóstico reales | Límite de interpretación |
|---|---|---|---|---|
| S01 | Fila tabular base, 16 campos textuales | EST-001 | COMPROBACION_SATISFECHA / estructura_recibida_coherente | Mantiene HORA e identidad no evaluadas; no declara validez meteorológica |
| S02 | TEMP no aportado en RegistroQA parcial | VAL-001 / TEMP | EVALUACION_INCOMPLETA / campo_no_disponible | No demuestra que un original no leído omitiera la variable ni permite reconstruirla |
| S03 | TEMP literalmente vacío | VAL-001 / TEMP | PROBLEMA_TECNICO / campo_vacio_sin_inferir_medicion | No infiere ausencia instrumental, causa o valor faltante correcto |
| S04 | TEMP `-3.125e1` | VAL-002 / TEMP | COMPROBACION_SATISFECHA / numero_finito_interpretable | Gramática finita, sin rango físico, unidad o plausibilidad |
| S05 | TEMP `1,25` | VAL-002 / TEMP | PROBLEMA_TECNICO / numero_no_interpretable | Gramática ASCII usada no admite coma; no se convierte. VAL-004 emite además alerta documental |
| S06 | Fila con 17 valores; adaptador la marca incoherente | EST-001 | EVALUACION_INCOMPLETA / estructura_no_evaluable | Sus 13 resultados quedan incompletos; valor extra preservado, VAL diferenciadas por variable |
| S07 | Dos IDs ficticios para el mismo nombre literal | ID-002 / ESTACION | ALERTA_DOCUMENTAL / identidad_documental_ambigua | No se selecciona un código ni se verifica una instalación física |
| S08 | HORA `12345`, sin formato acreditado | TMP-002 / HORA | NO_EVALUADO / formato_documental_no_disponible | No completa ceros, interpreta zona, construye timestamp o supone ventana |
| S09 | UBIGEO `007777.0` frente a anchura ficticia seis | ID-004 / UBIGEO | ALERTA_DOCUMENTAL / representacion_documental_discrepante | Conserva sufijo y ceros; no geocodifica ni decide código correcto |
| S10 | PP `1.50`, unidad desconocida/ambigua | VAL-002 / PP | COMPROBACION_SATISFECHA / numero_finito_interpretable | La prueba es lexical; no hay regla L0 de equivalencia mm–mm/h. Restricción PP se conserva en el expediente |
| S11 | Formatos no aportados en configuración | VAL-004 / TEMP | NO_EVALUADO / formato_documental_no_disponible | No inventa metadatos desde frecuencia o apariencia de valores |
| S12 | Dos filas con igual tupla de valores y posiciones lógicas distintas | EST-001 / ambas | Dos COMPROBACION_SATISFECHA / estructura_recibida_coherente | Igualdad literal no prueba mismo instante/evento. Se conservan ambas filas; no se añade una regla de duplicación inexistente |

Los prefijos cortos de la tabla conservan los IDs completos L0-... de las siete
reglas seleccionadas. En S02 no se usa un CSV supuesto: es una entrada parcial
en memoria con valores_csv_originales=None. En S06 la tupla bruta de 17 valores
sí se conserva; el decimoséptimo no se pierde por zip al adaptar los 16 nombres.

### Totales por escenario

| Escenario | Entradas | Resultados | Satisfechas | Alertas documentales | Problemas técnicos | No evaluadas | Incompletas |
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

Por regla, las tres VAL emiten **39 cada una**; EST/TMP/las dos ID emiten
**13 cada una**: **3×39 + 4×13 = 169**. Ninguna de las 169 claves
`(escenario, numero_registro, regla_id, campos_objetivo)` se repite. El escenario
se incluye porque sus entradas son ensayos independientes, no un único archivo.
Las 16 incompletas son tres por TEMP ausente en S02 y trece por estructura de
S06. Las dos P se refieren a vacío y representación no interpretable, no a dos
fenómenos ambientales anómalos. Las tres alertas no son rechazos científicos.

La distinción objetivo/campo en S06 es la corrección demostrada: antes se emitían
tres VAL idénticas por regla; ahora cada una conserva su variable. No se suprime
ninguna emisión ni se presenta como evaluado lo que es incompleto.

## Admisión tabular y pruebas complementarias

Además de los 169 resultados puros, se ensayan dos CSV pequeños creados en un
TemporaryDirectory propio, usando LectorCSV/EvaluadorNivel0, sin datos reales:

- Encabezado con COLUMNA_FICTICIA: **cero resultados**, informe INCOMPLETA y
  `encabezado_no_admitido`; no asigna las columnas por aproximación.
- Encabezado correcto y fila de 17 valores: **13 resultados incompletos**,
  fila bruta intacta e informe INCOMPLETA. Motivo `eof` del lector no equivale
  a QA completa; no se infiere EOF compatible o éxito desde ese código solo.

Ambos conservan bytes y mtime del archivo sintético. Son comprobaciones
complementarias, no otros registros institucionales ni parte del total 169.
Un valor Python float en campos_originales y nombres de campo repetidos se
rechazan en el contrato antes de evaluar; no se coaccionan a texto.

Otro test usa EvidenciaDocumental de catálogo con estados DESCONOCIDO,
DECLARADO y VERIFICADO, todos **suministrados como fixtures**. PROV-006 conserva
cada estado y solo comprueba asociación fuente/recurso. Su S no acredita que
la clasificación aportada haya sido físicamente verificada por QA. No se llama
al mecanismo 84-L, no se transforma una coincidencia literal en una licencia,
formato aplicable o permiso, y no se eliminan restricciones.

La igualdad literal de S12 es una comparación de tuplas de la fixture, con
posiciones distintas; no se usa ESTACION/fecha/HORA como identidad física.
No se deduplican resultados ni se ejecuta un índice SQLite de duplicaciones.
El diagnóstico de claves literales existente en consultas_locales queda fuera
del piloto; su existencia se registra en el inventario, sin copiarlo.

## Reproducibilidad, límites y seguridad

Se comparó cada resultado con una segunda ejecución sobre las mismas entradas,
configuración, evidencia y versiones, sin modificar campos, representaciones o
tuplas brutas. Las repeticiones no incrementan el total del piloto ni los tests.
Las versiones son de regla/contrato **1.0.0**. SHA-256 de los bytes de reglas.py
utilizados tras corregir la traza:

```text
95ff76d1cdd997623efe97bc38948459e9a1f1dad7b3d07ac56bab3fe6604c36
```

El registro externo del piloto en memoria se hizo entre
**2026-11-08T23:41:16.881468+00:00** y
**2026-11-08T23:41:16.892172+00:00**. El tiempo describe ejecución técnica;
no asigna fecha/zona a observaciones. El resumen privado, **102028 bytes**, queda en:

```text
%TEMP%\spica-85a-cenrhbd_\piloto-sintetico.json
```

Contiene fixtures, trazas, parámetros/referencias, restricciones del expediente
y conteos, no datos institucionales. Guardia final del piloto: **0 red,
0 SQLite, 0 procesos, 0 accesos operativos y 0 escrituras prohibidas**. La única
escritura permitida es el artefacto propio en ese temporal. El componente puro
se probó también con archivos, red, SQLite, procesos, cotejador documental y
evaluador científico sintético bloqueados mediante mocks; no se invocaron.

Entradas acotadas: 12 escenarios/13 registros, 169 resultados; hasta 17 textos
breves por registro, perfil de 16 columnas y dos mappings
ficticios para ambigüedad. La configuración de las siete reglas es estática.
La admisión CSV suplementaria usa máximo 4096 bytes, cinco registros de lector,
tres registros QA y 100 resultados. La API pura no aplica los límites de
archivo/registro del motor: el arnés debe acotar sus entradas. El presupuesto
numérico sí es el compartido con el perfilador; no se amplía ni duplica.

No hay un campo de ejecución científica en ResultadoQA; no se inventa uno.
Se verifica ausencia de llamadas superiores y no hay ejecutor conectado. Los
NO_EVALUADO, alertas o S no levantan restricciones por unidades, espacio o tiempo.
No se determina magnitud PP, zona horaria, código territorial, CRS, plausibilidad,
outlier climático, tendencia, homogeneidad, calidad instrumental o contaminación.

## Pruebas y verificaciones actuales

Se añaden **ocho tests**, con subcasos para las doce situaciones, y se reutilizan
las 53 pruebas existentes de Nivel 0. Comandos con Python **3.15.1 de .venv** y
HTTPX **0.28.1**:

```powershell
$env:PYTHONPATH="$PWD\src;$PWD\tests;$PWD"
.\.venv\Scripts\python.exe -B -m unittest test_calidad_nivel0 test_piloto_qaqc_estructural_85a -v
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -B -m pip check
git diff --check
git status --short
```

**Dirigidas: 61 aprobadas, 0 fallos y 0 errores, 13.831 s**, 53 anteriores + 8
nuevas. Antes se probaron las ocho nuevas: primer ensayo con un fallo de
expectativa del test suplementario, que esperaba motivo de reglas incompletas
en lugar del eof real del lector. Se corrigió la expectativa conservando la
exigencia de informe INCOMPLETA, sin cambiar el motor para forzar el resultado.
Ensayo posterior: **8 aprobadas**, 0 fallos/errores, 1.217 s.

**Suite completa realmente ejecutada: 1614 aprobadas, 0 fallos, 0 errores y
0 omitidas, 159.718 s, código 0, salida OK.** Son **1606 anteriores + 8 nuevas**;
las dirigidas, subcasos y repeticiones no se suman otra vez. Se incluyen las
regresiones de cardinalidad de 744 filas/22320 resultados sintéticos y la
compatibilidad de Nivel 0 con los contratos posteriores. No se detectaron
regresiones en las pruebas anteriores.

La suite completa usó guardia temporal de red, rutas operativas y procesos
ajenos a Python/Git: contadores finales **0 red, 0 rutas operativas,
0 SQLite operativos y 0 procesos no admitidos**. SQLite de fixtures/memoria
de la suite anterior es diferente del operativo, que permanece cerrado.
`pip check`: **No broken requirements found.**, código 0, con PIP_NO_INDEX=1
y PIP_DISABLE_PIP_VERSION_CHECK=1; sin instalaciones. Se permite únicamente su
consulta local de versión Windows manteniendo la guardia de red y rutas.
Las guardias observadas terminaron en cero; no se cambian ACL de temporales previos.

Los logs quedan fuera de Git en el mismo temporal:
`dirigidas.log`, `suite-completa.log` y `guardia/sitecustomize.py`.
Las 1606 pruebas del contexto inicial son un antecedente; no se presentan como
la suite ejecutada ahora. Los resultados del piloto y repeticiones no se suman
como pruebas unitarias ni nuevas reglas.

## Git final, riesgos y condiciones para continuar

Único alcance de cambios:

```text
 M src/spica/calidad/reglas.py
?? docs/inventario_qaqc_nivel0_paso85a.md
?? docs/piloto_qaqc_estructural_paso85a.md
?? tests/test_piloto_qaqc_estructural_85a.py
```

Rama/HEAD e índice se conservan; no se modifican modelos públicos, motores,
inspectores, transportes, adaptadores, dependencias, main.py, .gitignore o .venv.
Se revisan también los nuevos archivos sin seguimiento, no cubiertos por diff.
Comprobaciones de cierre: ambos Python con sintaxis compilada en memoria y
sin definiciones duplicadas; **dos informes, cinco tablas y 17 enlaces locales
correctos**; 22 IDs únicos representados en ambas matrices y todos los tests
citados existentes. Conteos y diagnósticos del informe cotejados con el resumen
sintético, y balance de brechas verificado. git diff --check e índice sin
errores. Git advierte normalización futura LF/CRLF en reglas.py; no se cambia
esa configuración ni se considera un error de whitespace.

No se accedió al CSV operativo, RAW, staging, SQLite operativo o documentos
institucionales. No hubo escrituras en esos recursos. No se calculan nuevas
huellas de almacenes que se mantuvieron cerrados ni se afirma control sobre
cambios de terceros. Cero conexiones externas, GET, descargas, enlaces abiertos,
instalaciones, migraciones, commits o push.

Se conservan **29 brechas: 2 resueltas documentalmente, 17 parciales,
8 pendientes y 2 contradicciones; 27 abiertas**. No se cambia ninguna matriz
ni se demuestra equivalencia editorial XLSX–DOCX–CSV.

Riesgos residuales: perfil SENAMHI cerrado, evidencia declarativa sin
autenticación automática, ausencia de restricciones genéricas por resultado,
necesidad de acotar consumidores puros, versionado técnico de correcciones y
frozen como inmutabilidad cooperativa. No se requieren ampliaciones ahora.
Para un eventual 85-B debe revisarse primero el inventario, la traza, las
restricciones por ejecución y la aplicabilidad de metadatos; no activar reglas
científicas, normalización o duplicaciones de instantes sin contrato/evidencia.

**APTO CON RESTRICCIONES** para revisión del piloto y corrección puntual de
trazabilidad. No se avanza al PASO 85-B.
