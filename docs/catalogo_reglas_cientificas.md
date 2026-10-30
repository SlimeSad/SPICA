# PASO 73: catálogo declarativo QA/QC Nivel 1

## Alcance y estado inicial

Se comprobó Git limpio en `feature/suadc-http`, HEAD `f72b587`, commit del PASO 72.
La base anterior contiene 779 pruebas. Este paso agrega contratos y un catálogo
en memoria, inicialmente vacío. No incorpora reglas institucionales, umbrales,
algoritmos científicos ni mecanismos de ejecución Nivel 1. No modifica contratos
públicos anteriores, observaciones, adquisición, RAW, staging ni SQLite operativo.

Se añaden `spica.calidad.modelos_cientificos`, `catalogo_cientifico`, sus pruebas
y este documento. Los imports son explícitos desde esos módulos; no se modifica
la superficie pública anterior de `spica.calidad`.

## Auditoría de los 22.320 resultados Nivel 0

Se revisaron el registro cerrado de 22 reglas, el motor y los resúmenes por regla
y categoría de `piloto_resultado.json` conservado por el PASO 72. No se repitió
el piloto real ni se extrajeron observaciones del original para este diseño.

Cada fila tiene **18 comprobaciones no repetidas por variable** y **cuatro reglas
de valores aplicadas a tres variables**. Por tanto:

```text
22 definiciones = 18 reglas por fila + 4 reglas por variable
30 resultados por fila = 18 + (4 × 3)
22.320 resultados = 744 × 30
```

Esta fórmula supone selección de las 22 reglas y las tres variables, sin corte
por límites o cancelación. Otra selección o una ejecución parcial requiere sus
propios conteos y revisión del informe de alcance, sin extrapolar ese total.

La consulta seleccionó TEMP como mecanismo para representar cada fila una vez,
pero conservó los 16 campos originales. QA evaluó TEMP, HR y PP en esas mismas
filas. No se hicieron tres consultas ni se deduplicaron observaciones.

| Regla, versión 1.0.0 | Campos o referencias comprobados | Por fila | Piloto |
| --- | --- | ---: | ---: |
| L0-EST-001 | Estructura de la fila recibida | 1 | 744 |
| L0-VAL-001 | TEMP, HR, PP: presencia literal | 3 | 2.232 |
| L0-VAL-002 | TEMP, HR, PP: número finito interpretable | 3 | 2.232 |
| L0-VAL-003 | TEMP, HR, PP: finitud / NaN / Infinity | 3 | 2.232 |
| L0-VAL-004 | TEMP, HR, PP: formato documental | 3 | 2.232 |
| L0-TMP-001 | FECHA | 1 | 744 |
| L0-TMP-002 | HORA | 1 | 744 |
| L0-TMP-003 | FECHA/HORA y referencia de zona | 1 | 744 |
| L0-TMP-004 | FECHA/HORA, instante no determinado | 1 | 744 |
| L0-ID-001 | ESTACION literal | 1 | 744 |
| L0-ID-002 | ESTACION y correspondencia documental de identidad | 1 | 744 |
| L0-ID-003 | LONGITUD, LATITUD | 1 | 744 |
| L0-ID-004 | UBIGEO | 1 | 744 |
| L0-ID-005 | RED, LONGITUD, LATITUD, ALTITUD, DEPARTAMENTO, PROVINCIA, DISTRITO, UBIGEO | 1 | 744 |
| L0-PROV-001 | FUENTE.PROVEEDOR, FUENTE.ID | 1 | 744 |
| L0-PROV-002 | RECURSO_ID | 1 | 744 |
| L0-PROV-003 | ADQUISICION_ID | 1 | 744 |
| L0-PROV-004 | ASSET_ID | 1 | 744 |
| L0-PROV-005 | SHA256_REFERENCIA | 1 | 744 |
| L0-PROV-006 | Asociación documento/Fuente/recurso en procedencia | 1 | 744 |
| L0-PROV-007 | LICENCIA, REFERENCIA_LICENCIA | 1 | 744 |
| L0-PROV-008 | Procedencia propia de ObservacionLocal frente al contexto | 1 | 744 |
| **Total** | **22 definiciones** | **30** | **22.320** |

En las reglas agrupadas, una comprobación puede referirse a varios campos y
seguir produciendo un solo resultado. VAL-001/002/003 comparten muchos valores
pero comprueban condiciones diferentes; la repetición de referencias de procedencia
en filas distintas es intencionada. No son votos independientes de validez científica.

Conciliación histórica por regla:

- VAL-001: 2.189 satisfechas + 43 problemas técnicos = 2.232.
- VAL-002 y VAL-003: cada una, 2.189 satisfechas + 43 no evaluadas = 2.232.
- VAL-004: 2.232 no evaluadas, por falta de gramática institucional explícita.
- TMP-002: 434 satisfechas + 310 alertas = 744.
- ID-004: 744 alertas; TMP-003/004 e ID-002: cada una, 744 no evaluadas.
- Cada regla restante tiene 744 comprobaciones satisfechas.

Los totales son 16.673 satisfechas, 1.054 alertas documentales, 43 problemas
técnicos, 4.550 no evaluadas y cero incompletas. Suman 22.320. Los 43 problemas
son **celdas vacías**, no 43 observaciones distintas ni fallas instrumentales.
NO_EVALUADO cuenta como resultado explícito; no es un resultado omitido.

Una prueba nueva usa el motor existente con 744 filas sintéticas y verifica
22.320 claves únicas `(numero_registro, regla_id, campos_objetivo)`: exactamente
744 resultados para cada combinación regla-variable y 744 para cada otra regla.
También comprueba que registrar propuestas Nivel 1 no cambia los resultados Nivel 0.

**Límite de la evidencia histórica:** el piloto conservó agregados y muestras,
no todas las claves individuales. Los agregados concuerdan con la cardinalidad
y con el comportamiento reproducido, sin evidencia de omisiones o duplicaciones.
No permiten demostrar retrospectivamente la unicidad de cada emisión del piloto.
Un futuro registro de ejecuciones deberá identificar cada resultado y su alcance
sin interpretar los conteos como número de observaciones científicamente válidas.

## Contrato científico 1.0.0

`ReglaCientifica` es inmutable y contiene ID estable `L1-...`, versión
`mayor.menor.parche`, nombre, ámbito, procedencia normativa, referencias,
aplicabilidad, parámetros, método, incertidumbre y contradicciones declaradas.
El espacio L1 no colisiona con los identificadores L0.

`ReferenciaCientifica` conserva ID, institución/procedencia, título, localizador
verificable por un revisor, versión documental, fecha civil y SHA de referencia
opcional. Las versiones y fechas desconocidas siguen como `None` en propuestas;
impiden documentar/aprobar. El localizador es un dato: nunca se abre ni se consulta.
Un SHA de referencia no acredita comprobación física, autenticidad ni vigencia.

La aplicabilidad usa once dimensiones explícitas: disciplina, variable, unidad,
tipo de medición, frecuencia, institución, producto, tipo de estación, instrumento,
geografía y ambiente. Cada `CondicionAplicabilidad` enumera valores literales
permitidos o declara `sin_restriccion=True`, siempre con referencias para aprobar.
Una dimensión ausente significa desconocimiento; nunca ausencia implícita de
restricción. No hay inferencia geográfica, interpretación de predicados ni GIS.

Ámbitos:

- UNIVERSAL: requiere justificar igualmente las once dimensiones. No significa
  que una propuesta sea aplicable a cualquier observación.
- INSTITUCIONAL: exige una restricción explícita de institución.
- PRODUCTO: exige restricciones explícitas de institución y producto.
- INSTRUMENTO: exige una restricción explícita de instrumento.

La unidad y las demás dimensiones se comparan por igualdad literal con
`ContextoCientifico`, cuyos datos requieren referencias documentales. No se
normalizan unidades ni se presume compatibilidad dimensional. Una unidad diferente
queda bloqueada, aun si pudiera convertirse físicamente. Si una regla documenta
independencia de unidad, debe declararlo expresamente con evidencia y revisión.
No hay catálogo implícito de variables, estaciones, instrumentos o frecuencias.

`ParametroCientifico` admite escalares de datos acotados: texto, entero, booleano
o Decimal finito, con unidad opcional y referencias. No admite floats, callbacks
ni objetos arbitrarios. No se introducen parámetros científicos reales en este paso.
`MetodoCientifico` es un símbolo, versión, descripción y referencias; no es una
ruta importable ni una función. `IncertidumbreCientifica` conserva descripción y
referencias; no calcula ni inventa incertidumbre cuantitativa.

`ResultadoCientifico` reutiliza `RegistroQA`, `ProcedenciaQA` y los estados de
evaluación de Nivel 0. Conserva la revisión exacta de la regla, todos los valores
originales del registro, unidad declarada, diagnóstico y evidencia de ejecución.
Distingue comprobación satisfecha, alerta, sospecha, problema demostrado, no
evaluado e incompleto. Son categorías distintas; una excedencia no demuestra por
sí sola contaminación, falla instrumental ni origen antropogénico.

Los originales y sus unidades declaradas se conservan. Un extremo no se considera
erróneo por su magnitud. No se asigna zona horaria desconocida, reconstruye HORA o
UBIGEO, inventan códigos de estación, excluyen extremos ni convierten unidades.

Los estados que describen ejecución requieren una revisión aprobada y
`EvidenciaEjecucionCientifica` del método/versión exactos, con fecha UTC posterior
o igual a la aprobación, ejecutor versionado, referencias, detalle y contexto.
Estos contratos **pueden representar metadatos declarados de una ejecución futura
o externa**. Construir una instancia no ejecuta una regla ni verifica que la evidencia
sea verdadera. Ninguna función de este paso produce resultados científicos ejecutados.
Los únicos ejemplos de esas representaciones están en pruebas completamente ficticias.

## Registro, revisiones y aprobación

`CatalogoReglasCientificas` registra solamente descriptores, siempre como PROPUESTA
en revisión 1. No acepta una aprobación aportada como estado inicial. La clave
`(ID, versión)` es única; duplicarla, incluso con contenido idéntico, genera error.
No se sobrescriben versiones ni se modifican las revisiones ya emitidas.

Una nueva versión debe ser numéricamente mayor. Mantiene nombre/ámbito del ID
estable; cambios de identidad requieren otro ID. Toda versión nueva empieza como
propuesta, sin heredar decisiones. Las versiones anteriores permanecen consultables;
el consumidor debe seleccionar una versión explícita, nunca una «última aprobada»
implícita. Cambiar el contenido de una versión registrada exige otra versión.

Transiciones admitidas:

```text
PROPUESTA -> DOCUMENTADA -> APROBADA -> SUSPENDIDA
                              ^             |
                              |             v
                              +------ DOCUMENTADA
Cualquier estado no obsoleto -> OBSOLETA (terminal)
```

Cada transición exige la revisión esperada y una `RevisionCientifica` con referencia
de responsable/rol, fecha UTC, informe y referencias revisadas. El historial se
incrementa sin saltos; se rechazan revisiones desactualizadas y fechas regresivas.
Suspender u obsoletar también deja decisión. Reactivar exige pasar de nuevo por
documentación y aprobación. No se modifica el contenido para «resolver» contradicciones
dentro de la misma versión: se registra una versión corregida.

Documentar exige referencias con versión/fecha conocidas y revisadas, sin
contradicciones declaradas o estructurales detectadas. Aprobar exige además:

- Procedencia normativa, once dimensiones explícitas y evidencia por condición.
- Restricciones coherentes con el ámbito declarado.
- Método, incertidumbre y cada parámetro referenciados.
- Revisión de todas las referencias, sin referencias ajenas ni contradicciones.
- Declaración explícita de aplicabilidad demostrada.
- Documentación no posterior a la revisión.

Se rechazan IDs de referencia duplicados, dimensiones o parámetros duplicados y
referencias no resueltas. Se detectan versiones/fechas/hashes incompatibles de un
mismo localizador. Las contradicciones semánticas entre fuentes diferentes deben
ser identificadas por revisión humana; el software no interpreta el texto científico.

Una referencia y una declaración de revisión son requisitos necesarios, no una
prueba automática de autoridad científica. La API confía en el operador autorizado:
no autentica revisores ni verifica firmas, documentos o permisos de acceso.
La aprobación del catálogo no autoriza ejecutar código.

## Deshabilitación y reutilización del motor

`comprobar_habilitacion()` devuelve elegibilidad **documental** y motivos fijos.
PROPUESTA, DOCUMENTADA, SUSPENDIDA y OBSOLETA no son elegibles. Para una APROBADA,
se comprueba el contexto exacto de cada condición restringida y su evidencia.
La falta de datos o incompatibilidad se informa sin convertir ni corregir datos.

**Siempre devuelve `ejecucion_autorizada=False` y estado NO_EVALUADA**, incluso
si todos los requisitos documentales se cumplen. No existe registro de funciones
ejecutables, carga de archivos de reglas, eval, exec, importación dinámica ni dispatcher
científico. Un texto que parezca código solo es un literal y nunca se interpreta.

Nivel 0 continúa utilizando `EvaluadorNivel0`, su lector, interpretación numérica,
límites, cancelación y cierre. Los nuevos contratos reutilizan su representación
de registros y procedencia. No se construye un segundo motor. Ejecutar Nivel 1
requerirá aprobar un punto de extensión del motor y métodos implementados mediante
código confiable y pruebas propias, sin cargar código desde las configuraciones.
Esa integración ejecutable queda fuera de este paso.

## Reglas pendientes y compatibilidad ambiental

No se registró ninguna regla científica real, propuesta institucional ni umbral.
Quedan pendientes fuentes y aplicabilidad aprobadas para controles de plausibilidad,
rangos instrumentales, continuidad temporal, coherencia entre variables y otros
controles que se decida incorporar. Una mención temática no es una regla aprobada.

El contrato no restringe variables/unidades a TEMP/HR/PP ni disciplinas a meteorología.
Permite describir procedencia SENAMHI, ANA, OEFA u otra institución, y productos de
meteorología, hidrología, hidrogeoquímica, geología y suelos. Esto es compatibilidad
del modelo declarativo; no certifica compatibilidad con formatos, normas, unidades,
instrumentos o conectores institucionales todavía no analizados.
`RegistroQA` conserva por ahora los límites tabulares existentes. Soportar datos
no tabulares, ventanas temporales o relaciones entre múltiples registros requerirá
un diseño adicional, sin forzar esos casos a una regla de una sola observación.

## Restricciones y verificaciones

El catálogo es experimental, secuencial y en memoria: no tiene persistencia,
SQLite, migraciones, almacenamiento de documentos, firmas, control de roles,
bloqueo concurrente, historial duradero ni recuperación tras reiniciar el proceso.
El control de revisión esperada evita actualizaciones obsoletas en el uso secuencial;
no garantiza atomicidad entre hilos/procesos. La elegibilidad no es una reserva ni
autorización reutilizable. La incertidumbre y condiciones son datos documentales;
su validez científica sigue requiriendo revisión independiente.

No se accedió a internet, instalaron dependencias ni realizaron descargas. El
inventario operativo previo coincide con el del PASO 72; se compara nuevamente
al terminar mediante lectura binaria de hashes, tamaños y metadatos. No se abre
SQLite operativo mediante una API que pueda registrar eventos o recuperar journals.
Los registros auxiliares se conservan fuera de Git en un directorio temporal.

Verificación final con Python **3.15.1** de `.venv` y `-B`:

```text
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
Ran 825 tests in 86.019s
OK

.\.venv\Scripts\python.exe -B -m pip check
No broken requirements found.

git diff --check
Sin diferencias de whitespace; código de salida 0.

git status --short
?? docs/catalogo_reglas_cientificas.md
?? src/spica/calidad/catalogo_cientifico.py
?? src/spica/calidad/modelos_cientificos.py
?? tests/test_reglas_cientificas.py
```

**825 aprobadas: 779 anteriores + 46 nuevas; cero fallos, errores u omisiones.**
Se compararon los identificadores completos de las 779 pruebas previas con el
registro del PASO 72: coincidencia exacta. Las nuevas cubren versionado, referencias,
aprobación, contexto/unidades, contradicciones, suspensión, obsolescencia, determinismo,
seguridad declarativa, representación de resultados y preservación de Nivel 0.

Durante el trabajo se detectó y corrigió una colisión con el nombre del archivo
de pruebas del catálogo de adquisición. Ese archivo quedó restaurado con sus
bytes y fecha de modificación anteriores; no hay diferencias rastreadas en Git.
Una ejecución intermedia incompleta de 785 pruebas detectó además un error en una
fixture nueva: reutilizaba un ID documental con metadatos contradictorios. Se
separó el identificador de esa fixture, conservando el rechazo de contradicciones
en una prueba específica. Esa ejecución no se tomó como verificación final.

Los cinco archivos operativos y cuatro directorios coinciden antes/después en
inventario, tamaños, hashes, mtime, identificadores de archivo y enlaces. No se
compara atime, que puede cambiar al leer. CSV: 50.474.012 bytes,
SHA-256 `3d3e8a0a75e070d0b8111faf921be17140c3a0f9db2b4c25d72d99a15a950eab`;
sintético: 57 bytes, SHA-256
`82c649098a927a255181c8b05d18aec30594fa89571bad2792464f3ba255f4cb`.
SQLite: 32.768 bytes, SHA-256
`946d2512795c5ae3a68113f63438110be66dee32488ad02e86d550da040d4a0d`.
Marcador y archivo previo de staging también se conservaron. No aparecieron
WAL, SHM, journal ni residuos; RAW/temporales sigue vacío. Son comprobaciones
físicas de preservación de bytes, sin implicar validación científica.

Evidencia auxiliar fuera del repositorio:

```text
C:\Users\Propietario\AppData\Local\Temp\spica-paso73-9b06bc15ffe04c90b3e5cf2d409bfe53
```

`unittest_final.log` y `resultado_final.json` conservan la ejecución completa;
`descubrimiento_final.json` verifica las 779 pruebas previas;
`operativo_antes.json`, `operativo_despues.json` y `operativo_comparacion.json`
documentan la preservación. Se mantienen también el registro intermedio y el
resumen del piloto usado para la auditoría. No son datos científicos nuevos.
Los cuatro archivos nuevos se revisaron directamente por sintaxis, espacios finales
y conflictos, porque `git diff --check` no incluye archivos sin seguimiento.

El dictamen se limita al diseño y controles declarativos: **APTO CON RESTRICCIONES**
para revisión. Ninguna regla científica de Nivel 1 queda activa.
