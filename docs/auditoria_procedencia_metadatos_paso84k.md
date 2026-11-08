# PASO 84-K — Auditoría de procedencia del núcleo documental

Fecha: **2026-11-08**. Dictamen: **APTO CON RESTRICCIONES**, exclusivamente
para representación documental experimental y revisión humana. No autoriza
integración al catálogo, procesamiento científico o una etapa posterior.
El [piloto trazable](piloto_afirmaciones_pnda_paso84k.md) registra las fuentes,
afirmaciones y diagnósticos reales de este paso.

## Recuperación y alcance

Git comenzó limpio en **feature/suadc-http**, HEAD **1c06125**, «SUADC:
contratos experimentales de metadatos documentales». El PASO 84-J está registrado.
Historial comprobado con `git log -5 --oneline`:

```text
1c06125 SUADC: contratos experimentales de metadatos documentales
ef17ad4 SUADC: reconciliacion documental de metadatos PNDA
b3c2748 SUADC: compatibilidad OOXML y extraccion documental PNDA
ca08d73 SUADC: inspeccion segura de hipervinculos OOXML
944151a SUADC: adquisicion controlada y evidencia DOCX PNDA
```

Se revisaron los dos informes 84-J:
[transiciones](auditoria_transiciones_pnda_paso84j.md) y
[contratos](contratos_metadatos_documentales_paso84j.md),
los [modelos](../src/spica/metadatos_documentales/modelos.py),
[evaluador](../src/spica/metadatos_documentales/evaluacion.py), exportaciones y
[pruebas](../tests/test_metadatos_documentales.py). Se contrastaron los contratos
reutilizados y los antecedentes
[XLSX 84-E](inspeccion_diccionario_pnda_paso84e.md),
[DOCX 84-HC](auditoria_estructuras_docx_paso84hc.md),
[reconciliación 84-I](reconciliacion_xlsx_docx_pnda_paso84i.md), su
[matriz](brechas_reconciliadas_pnda_paso84i.md) y
[evidencias](evidencias_consultas_pnda_paso84i.md).
Estos documentos históricos permanecen sin cambios.

La separación necesaria ya existe. Se corrigió un defecto de evaluación y se
cubrieron seis riesgos sintéticos. No se necesita un importador, serializador,
verificador OOXML nuevo ni ampliación de modelos para este ensayo.

## Responsabilidades y límites de confianza

| Nivel | Trabajo realizado en 84-K | Garantía y límite |
|---|---|---|
| A. Verificación externa | Rutas autorizadas, tamaño/hash físicos, firmas, inspección con las API existentes y cotejo del contenido localizado | Conservación y lectura local en el perfil admitido; no autentica al emisor ni certifica ciencia |
| B. Representación | Dos FuenteDocumental, 12 AfirmacionDocumental, referencias reales y tres relaciones, en un ExpedienteMetadatos | Coherencia nominal/estructural y conservación de literales, ámbitos y restricciones; no lee archivos |
| C. Diagnóstico | evaluar_uso sobre las siete operaciones propuestas, con comparación determinista | Requisitos sobre clasificaciones aportadas; no ejecuta ninguna operación ni concede autorización |

Se reutilizaron `ReferenciaCientifica`, `EvidenciaDocumental`, `Respaldo`,
`ProcedenciaCatalogo` y `ReferenciaDOCX`. El arnés puntual quedó únicamente en
un temporal privado, fuera de Git. No se creó una segunda estructura de
procedencia ni se introdujeron constantes institucionales en el núcleo o los tests.

**Un SHA-256 válido no promueve integridad o inspección.** Una fuente construida
solo con ese hash conserva ambos respaldos en None y bloquea incluso consulta.
Un localizador sintácticamente correcto tampoco acredita existencia o contenido.
El llamador puede aportar explícitamente un Respaldo VERIFICADO con procedencia:
el núcleo comprueba su tipo/coherencia, no la verdad de esa declaración. Por eso
siempre informa `clasificaciones_aportadas_no_autenticadas_por_el_nucleo`.
En el piloto, esos dos respaldos proceden de comprobaciones físicas realmente
ejecutadas en A, no del nombre del archivo o una afirmación textual de la fuente.

## Auditoría y controles

| Área | Comprobación y resultado |
|---|---|
| Identidad | IDs de fuente/afirmación únicos por expediente; el mismo ID local con otro hash se rechaza, tanto en registro como al atribuir una afirmación a la fuente anterior |
| SHA-256 | Obligatorio, 64 caracteres hexadecimales minúsculos; no se calcula o valida contra disco dentro del núcleo |
| Referencias | Tipo XLSX/DOCX/sección compatible, ID/hash concordantes y evidencia vinculada a la misma referencia. Un localizador DOCX no puede emplearse como XLSX |
| Localización efectiva | Debe comprobarse externamente. En el piloto, siete párrafos y cinco celdas/rangos conducen al contenido representado; se cotejó además la última actualización visible |
| Inmutabilidad ordinaria | Asignaciones directas a modelos, referencias y respaldos anidados rechazadas; colecciones tuple y tipos exactos. No se aceptan listas mutables como pendientes o restricciones |
| Desconocidos | Versiones, objetivo de producto, autenticidad y correspondencia desconocidos permanecen None; no se infieren desde propiedades OOXML |
| Ausencia/nulo | AUSENTE exige contenido None, nivel desconocido y pendiente que delimite alcance; NULO_DECLARADO exige declaración explícita preservada; el literal NULL no se convierte |
| Relaciones | Extremos presentes, pares sin duplicación, justificación obligatoria; coincidencia literal no equivale a edición común. Distinto ámbito no es contradicción genuina |
| Contradicciones | Relaciones contradictorias incidentes bloquean aunque solo se seleccione un extremo. Tras la corrección, también bloquea cualquier contradicción explícita de la evidencia aunque no se haya reclasificado el nivel |
| Diagnósticos | Trazas ID/hash/localizador, selección y orden deterministas; no incluyen el texto completo. El núcleo no decide equivalencia semántica por lenguaje natural |
| Autorización | Constructor y dataclasses.replace rechazan configurar ambas banderas; asignación ordinaria congelada. Las siete operaciones devuelven ejecucion_autorizada=False y operacion_ejecutada=False; bool(resultado) no es un permiso |
| Exportación | No existe interfaz de carga o exportación admitida. asdict conserva las restricciones del caso sintético pero no produce un objeto reconstruible mediante el constructor; se rechazan los dict anidados y las banderas init=False |
| Aislamiento | Importación fresca del núcleo sin SQLite, HTTPX o módulos operativos; evaluación sin I/O. Construir contratos heredados sigue cargando sus inicializadores anteriores, sin que esto autorice operaciones |

**Inmutabilidad cooperativa, no aislamiento frente a código hostil.** Las
dataclasses frozen de este núcleo y de contratos anteriores tienen `__dict__`.
En un ensayo exclusivamente sintético se demostró que modificar directamente
el diccionario de una ReferenciaCientifica altera su título. Tampoco ofrecen
defensa contra `object.__setattr__`, manipulación de clases o módulos.
No se construyó una autorización verdadera ni se alteraron los objetos reales
del piloto mediante esas vías. La garantía de False se refiere al constructor,
evaluador y operaciones admitidas en un intérprete confiable. No es una frontera
de seguridad frente a Python arbitrario, deserialización insegura o plugins
hostiles. No se rediseñan ahora todos los contratos heredados; una integración
con ejecutores o consumidores no confiables exigiría revisión arquitectónica.

## Hallazgo corregido y riesgos residuales

| ID y gravedad | Evidencia | Tratamiento |
|---|---|---|
| K-A01 — Alta, corregido | Una EvidenciaDocumental válida con nivel DECLARADA, contradicciones no vacías y demás respaldos positivos producía requisitos satisfechos sin bloqueos; ejecución seguía False | El evaluador emite evidencia_contradictoria si el nivel es contradictorio **o** existe cualquier contradicción explícita. Se aplica a las siete operaciones y no borra evidencia |
| K-A02 — Media, límite de confianza | Respaldo VERIFICADO es una clasificación aportada; una referencia plausible puede no existir físicamente | Verificación A obligatoria, trazabilidad y aviso persistente. Prohibido interpretar el diagnóstico como autenticación o permiso |
| K-A03 — Media, límite de aislamiento | frozen evita mutación por la API ordinaria, pero no manipulación de __dict__/objetos/clases en Python | Intérprete y llamador confiables; no usar estos objetos como credenciales o frontera de autorización |
| K-A04 — Media, documental/científica/jurídica | Edición aplicable, autenticidad, derechos, convención horaria, CRS, identidad física y controles científicos insuficientes | Se conservan restricciones; usos no consultivos bloqueados. No se cierran brechas ni normalizan datos |
| K-A05 — Baja, evolución pendiente | Perfil DOCX limitado al cuerpo/tablas no anidadas; rangos XLSX no resueltos por el núcleo; no hay serializador seguro ni selección temporal de edición | Posponer una ampliación hasta diseño y revisión propios; no suplir con supuestos |

K-A01 se reprodujo **antes** del cambio, solo en memoria: un conflicto registrado,
`bloqueos=[]`, requisitos satisfechos True y ejecución False. Corrección mínima
en el evaluador, sin nuevos campos, firmas, enumeraciones o contratos públicos.
Solo cambia el diagnóstico de un estado incoherente que antes pasaba inadvertido.
Se mantiene la versión experimental 0.1.0; la revisión se identifica por el diff
y este expediente, sin fingir una edición científica nueva.
SHA-256 del evaluador auditado en esta copia de trabajo:
`8bad26b75e01de93e8879dc8f6bff3cad688bda48760d27acbda9bcc3359dda3`.
Identifica estos bytes de código, no la autenticidad de documentos o resultados.

No se interpreta automáticamente todo texto en incertidumbres o pendientes como
una contradicción: son campos distintos. La suficiencia de un ámbito, paráfrasis,
procedencia o constatación continúa dependiendo del revisor. No existe firma
digital del resultado, corroboración automática, carga de reglas o ejecución
de expresiones provenientes de archivos.

## Pruebas realmente ejecutadas

Se añadieron **seis tests sintéticos** al archivo existente; no se introdujeron
documentos reales ni fixtures institucionales:

1. Contradicciones explícitas con niveles DECLARADA/VERIFICADA/INFERIDA, en las
   siete operaciones, bloquean aunque no se haya reclasificado el nivel.
2. Intentos de configurar banderas en constructor, replace y asignación ordinaria.
3. Inmutabilidad cooperativa de referencias/respaldos anidados y rechazo de listas.
4. Mismo ID local con otro documento/hash y referencia DOCX atribuida a XLSX.
5. Referencia sintáctica sin comprobación física, sin promoción de SHA o existencia.
6. asdict/constructor rechazados como carga implícita; replace conserva restricciones.

Los 31 tests anteriores ya cubrían ausencia/nulo, edición, unidades, temporalidad,
espacio, licencia, calidad declarada, conflictos relacionales, determinismo y
ausencia de I/O. No se duplicaron para incrementar el contador.

Comandos con **Python 3.15.1 de .venv**, HTTPX **0.28.1**:

```powershell
$env:PYTHONPATH="$PWD\src;$PWD\tests;$PWD"
.\.venv\Scripts\python.exe -B -m unittest test_metadatos_documentales -v
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -B -m pip check
git diff --check
git status --short
```

**Dirigidas finales: 37 aprobadas, 0 fallos y 0 errores, 0.717 s.**
El primer ensayo de esos 37 tests tuvo 14 errores de subcaso dentro de un único
test nuevo: se esperaba ValueError de replace, pero Python 3.15.1 rechaza campos
init=False con TypeError. Se corrigió la expectativa del test; no se alteró
el producto para aceptar el intento. Esa corrida inicial no fue satisfactoria.

**Suite completa: 1574 aprobadas, 0 fallos, 0 errores y 0 omitidas, 153.968 s,
código 0, salida OK.** Son **1568 anteriores + 6 nuevas**, no un total histórico.
Las 37 dirigidas y los subcasos son parte de ese acumulado, no se suman otra vez.
`pip check`: **No broken requirements found.**, código 0.

La suite añadió temporalmente una guardia a PYTHONPATH, antes de src/tests/raíz:
bloqueo de conexiones/DNS y ubicaciones operativas; solo procesos Python/Git
para tests. Se usó el contexto del propietario para sus fixtures privados
Windows, sin cambiar ACL previas. pip usó PIP_NO_INDEX=1 y
PIP_DISABLE_PIP_VERSION_CHECK=1, con guardia de red/rutas y permitiendo su
consulta local de versión Windows. Ambos terminaron con **0 red, 0 accesos a
rutas operativas, 0 SQLite operativos y 0 procesos no admitidos**. SQLite de
fixtures/memoria no es SQLite operativo.

Arnés, resumen saneado y log verbose quedan fuera de Git:

```text
%TEMP%\spica-84k-hwvqivlk\piloto84k.py
%TEMP%\spica-84k-hwvqivlk\piloto-saneado.json
%TEMP%\spica-84k-hwvqivlk\suite-completa.log
%TEMP%\spica-84k-hwvqivlk\guardia\sitecustomize.py
```

El resumen tiene **714088 bytes**: referencias, fragmentos seleccionados y
diagnósticos, sin contacto personal, destinos hyperlink, binarios completos o
CSV. No es un manifiesto institucional, fixture permanente o nueva evidencia
primaria. Su retención temporal no sustituye una política de conservación.

## Cierre y restricciones

Se mantienen **29 brechas: 2 resueltas documentalmente, 17 parciales, 8 pendientes,
2 contradicciones, 0 no evaluables; 27 abiertas**. No se modificaron estados,
matrices, informes, manifiestos o evidencias anteriores.

Git final conserva rama/HEAD e índice sin cambios. Único alcance:

```text
 M src/spica/metadatos_documentales/evaluacion.py
 M tests/test_metadatos_documentales.py
?? docs/auditoria_procedencia_metadatos_paso84k.md
?? docs/piloto_afirmaciones_pnda_paso84k.md
```

Los documentos nuevos se revisan directamente, pues git diff --check no cubre
archivos sin seguimiento. Se comprueban sintaxis en memoria de los Python
modificados, enlaces locales, tablas, UTF-8, referencias y balance de brechas.
Resultado: **dos informes, ocho tablas y 12 enlaces locales correctos**;
los dos Python modificados compilan en memoria y no tienen definiciones
duplicadas. `git diff --check`, comprobación del índice y diff de los informes
84-I/84-J y modelos/exportaciones conservados: código 0, sin diferencias.
Git solo advierte la normalización futura LF/CRLF de los dos Python; no es
un error de whitespace ni se modifica su configuración.

Cero conexiones externas, GET, descargas, enlaces abiertos, Word/Excel,
instalaciones, migraciones, commits o push. Ningún acceso al CSV operativo,
RAW, staging o SQLite operativo; no hubo escrituras en ellos. No se publican
huellas nuevas de almacenes no inspeccionados ni se atribuye a esta sesión
control sobre cambios de terceros. Los dos originales documentales y sus
siete auxiliares sí se verifican físicamente, como detalla el piloto.

No se hicieron conversiones, normalización temporal, asignaciones espaciales,
QA/QC científico o inferencias de contaminación. La configuración experimental
no habilita ejecutores: **ejecucion_autorizada == False** en todos los resultados
obtenidos por la API. El piloto y la corrección quedan para auditoría humana;
no se avanza a otra etapa.
