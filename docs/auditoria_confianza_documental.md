# PASO 77: auditoría focalizada de confianza documental

Dictamen: **APTO CON RESTRICCIONES para revisión documental y preparación de la
solicitud. Sin autorización de ejecución científica Nivel 1.**

## Estado inicial y alcance

Rama `feature/suadc-http`, HEAD `e9f9b32` (PASO 75). **Git no comenzó limpio y el
PASO 76 no está registrado en un commit.** Sus seis archivos están añadidos al
índice: dos documentos, tres módulos de aplicabilidad y su archivo de pruebas.
Inicialmente no había diferencias entre esos archivos preparados y el árbol de
trabajo. Se informó esta discrepancia antes de continuar. No se hicieron commits,
no se descartó trabajo ni se modificó el índice para resolverla.

Se auditan las instantáneas disponibles de los PASOS 73–76. El informe no certifica
el requisito de que el PASO 76 esté registrado en Git. La corrección de este paso
queda en el árbol de trabajo; **el índice conserva la versión previa preparada**.
Una eventual revisión/registro deberá contemplar ambas capas, sin asumir que el
contenido preparado ya contiene la corrección. No se ejecutó `git add`.

Se revisaron `modelos_cientificos.py`, `catalogo_cientifico.py`, los contratos y
evaluador experimentales, `calidad/aplicabilidad`, sus pruebas y los expedientes
documentales existentes. No se consultó internet, abrieron RAW/staging/SQLite
operativos ni se reprodujeron cálculos sobre observaciones reales.

## Ocho condiciones independientes

| Condición | Representación o evidencia disponible | Qué no permite concluir |
| --- | --- | --- |
| A. Documento identificado | `ReferenciaCientifica`: ID, procedencia, título, localizador, versión/fecha opcionales | Identificar un documento no acredita haberlo leído ni que sea auténtico |
| B. Contenido inspeccionado | Expedientes 74/75 con páginas/celdas y alcance de la inspección; `EvidenciaDocumental.localizacion` y nivel aportado | VERIFICADA es una clasificación del llamador; la clase no abre ni inspecciona el documento |
| C. Integridad física comprobada | Los expedientes anteriores registran hashes y tamaños de copias; la referencia conserva un SHA opcional | Un campo SHA no ejecuta una comprobación; un hash local comprobado tampoco prueba autoría institucional |
| D. Autenticidad de la fuente acreditada | Se conservan procedencia y referencias oficiales examinadas anteriormente | No hay contrato de acreditación independiente del emisor ni verificación de firma institucional; URL oficial y etiquetas no la sustituyen |
| E. Vigencia confirmada | `VigenciaDocumento` expresa la clasificación aportada; versión/fecha del manual están identificadas | Fecha de aprobación visible o URL oficial no confirman vigencia actual; el verificador no consulta al emisor ni calcula intervalos de vigencia |
| F. Aplicabilidad demostrada | Comparación de requisitos con afirmaciones y documentos, con diagnóstico y restricciones | COMPATIBILIDAD_DOCUMENTAL_DEMOSTRADA es consistencia documental según las entradas; no prueba la verdad externa, completitud del expediente o aplicabilidad científica por sí sola |
| G. Aprobación científica humana acreditada | `RevisionCientifica`/historial conservan una decisión declarada, rol, fecha y referencias | La clase no autentica al revisor ni acredita competencia, firma o aprobación institucional. La fecha de aprobación del manual no aprueba una regla de SPICA |
| H. Autorización operativa | Diagnóstico y `HabilitacionCientifica` mantienen `ejecucion_autorizada=False`; no hay ejecutor operativo Nivel 1 | Ninguna de A–G, ni APROBADA declarativa, constituye un permiso de ejecución |

No hay una cadena automática A→B→C→D→E→F→G→H. Las fechas de adquisición,
comprobación, documento, revisión y observación tampoco son intercambiables.
La marca VERIFICADA aparece en contextos distintos: acceso HTTP o integridad RAW
no equivalen a verificación científica de una afirmación.

## Evidencia suficiente e insuficiente

Según los expedientes existentes, son suficientes para identificar asuntos y
preparar preguntas: el manual MT-DRD-002 v02, sus apartados de TEMP/HR y la
transcripción condicionada; las celdas B12/B13/B14 del diccionario con promedio
TEMP/HR, total PP y unidades literales; la declaración de FECHA/HORA/UBIGEO.
Los registros de inspección y de integridad pertenecen a los pasos anteriores:
**no se volvieron a comprobar físicamente durante esta auditoría**.

No son suficientes para acreditar: vigencia actual y autenticidad independiente,
equivalencia entre las modalidades del manual y el producto, metrología y vínculo
estación–instrumento–serie, continuidad/cadencia, política temporal, semántica de
PP o aplicación completa de procedimientos institucionales al CSV. Tampoco existe
aprobación científica u operativa de TEMP-LIM/HR-LIM en estos expedientes.

Véanse el [expediente 74](fundamentacion_qa_nivel1.md), las
[fichas 75](especificaciones_temp_hr_lim.md) y la
[matriz 76](aplicabilidad_temp_hr_lim.md). No se atribuye contenido científico a
capítulos OMM no inspeccionados por estar citados en otro documento.

## Hallazgos y corrección mínima

| ID / gravedad actual | Reproducción y efecto observado | Tratamiento |
| --- | --- | --- |
| CD-01 / MEDIA, corregido | Una regla con dos parámetros, uno sin `referencias`, podía recibir COMPATIBILIDAD_DOCUMENTAL_DEMOSTRADA si el requisito genérico PARAMETROS_ESPECIFICOS coincidía. El resultado seguía sin ejecución autorizada | Se añade un hallazgo INSUFICIENTE `parametros_sin_procedencia_documental` cuando cualquier parámetro carece de referencias. No se cambian modelos, API, catálogo ni estados |
| CD-02 / MEDIA, límite confirmado | Un llamador puede aportar VERIFICADA/VIGENTE sin prueba independiente o reclasificar deliberadamente todos los metadatos inventados como DOCUMENTAL. Puede obtener consistencia documental, nunca autorización | Se documenta que las marcas son afirmaciones no autenticadas; no se construye autenticación ficticia ni se integra la salida con permisos. Nueva prueba de reclasificación total |
| CD-03 / MEDIA, límite confirmado | Etiquetas geográficas idénticas verificadas por el llamador satisfacen un requisito literal aunque no haya geometría. No se valida contención territorial | Nueva prueba de este alcance. Exigir la evidencia espacial pertinente o una relación documental explícita antes de una aplicación dependiente de geografía |
| CD-04 / MEDIA, pendiente de procedimiento | PASO 76 preparado pero sin commit; la corrección local del 77 no está en el índice | Mantener diferencias visibles y solicitar revisión; no declarar limpio/registrado ni ejecutar commits automáticamente |

CD-01 era un defecto de consistencia del diagnóstico, no una ejecución científica
no autorizada. El catálogo ya rechazaba parámetros sin referencias al aprobar
mediante `_problemas_aprobacion`; el verificador documental necesitaba el mismo
resguardo para no sobreafirmar su propio diagnóstico. Los candidatos TEMP/HR del
expediente continúan sin parámetros ejecutables y sin activación.

La corrección añade un único control en `verificar_aplicabilidad`. Conserva las
prioridades: si además hay contradicciones o incompatibilidades, estas prevalecen
en el estado global y el hallazgo por parámetro ausente sigue visible. No se
introduce otro motor, otra base de datos ni un mecanismo de aprobación.

Que un parámetro cite una referencia solo acredita su enlace declarativo; este
verificador no comprueba que esa fuente respalde su valor, unidad o uso. Esa
revisión de contenido sigue siendo científica/documental, no se sustituye por
un ID válido ni por un parámetro genérico favorable.

## Salvaguardas y riesgos hipotéticos

Se mantienen: contratos congelados; comparaciones literales; referencias
identificadas; ausencia de normalización de unidades; diagnóstico de faltantes,
contradicciones y obsolescencia; condiciones anteriores no omitibles; separación
de procedencia sintética/documental; rechazo de tipos de observaciones, rutas,
revisiones o habilitaciones como entradas del verificador; ausencia de callbacks,
evaluación de expresiones o importación dinámica de algoritmos.

El diagnóstico no es callable, rechaza `bool(diagnostico)` y mantiene una marca
fija de ejecución no autorizada. No cambia el catálogo ni genera decisiones
humanas. El evaluador del PASO 75 solo acepta sus contratos sintéticos exactos.
`ResultadoCientifico` describe resultados futuros/externos; instanciarlo no prueba
una ejecución de SPICA. No hay un productor operativo que se active aquí.

Riesgos **hipotéticos futuros**, sin salto operativo reproducido en esta auditoría:
usar el diagnóstico como permiso, confiar en una aprobación declarada como si
estuviera autenticada, importar configuración externa elevando niveles sin revisión,
o interpretar etiquetas como pruebas espaciales/metrológicas. Tendrían impacto
alto al conectar un ejecutor real. Su prevención requiere revisión de evidencia y
autorización independiente antes de esa integración, no un booleano añadido ahora.

La biblioteca no es un sandbox frente a Python hostil que fabrique o altere
metadatos. Tampoco la coincidencia documental significa completitud de las
dimensiones elegidas por el autor del plan. No se afirma que existan firmas,
sellos, controles de acceso o validaciones institucionales que no están implementados.

## Cobertura adversarial sin duplicar la suite previa

| Escenario solicitado | Comprobación reutilizada o añadida | Resultado relevante |
| --- | --- | --- |
| 1. VERIFICADA sin respaldo independiente | Inspección de contratos y reproducción con la fixture completa del 76 | El nivel es aportado, no autenticado; restricción explícita y ejecución siempre falsa |
| 2. Versión desconocida | `test_documento_regla_sin_version`, `test_documento_producto_sin_version_o_fecha` | INFORMACION_INSUFICIENTE |
| 3. Vigencia desconocida | `test_vigencia_desconocida` | COMPATIBILIDAD_CONDICIONADA |
| 4. Fuente contradictoria | `test_documento_con_contradiccion_explicita`, `test_referencias_contradictorias` | EVIDENCIA_CONTRADICTORIA |
| 5–6. Unidad coincidente, modalidad distinta; promedio/instantánea | `test_modalidad_distinta`, `test_promedio_no_equivale_a_instantanea` | INCOMPATIBILIDAD_DOCUMENTADA sin conversiones |
| 7. Instrumento ausente | `test_instrumento_desconocido` | INFORMACION_INSUFICIENTE |
| 8. Identidad de estación ambigua | `test_identidad_estacion_ambigua` | EVIDENCIA_CONTRADICTORIA |
| 9. Territorio como etiqueta | Nueva `test_etiqueta_territorial_igual_no_certifica_relacion_espacial` | Solo coincidencia literal, sin permiso ni prueba geométrica |
| 10. APROBADA declarativa | `test_etiqueta_aprobada_no_habilita_ejecucion` | Revisión no admitida como entrada; habilitación sin ejecución |
| 11. Fixture presentada como documental | Nueva `test_reclasificacion_total_de_fixture_no_acredita_origen_ni_autoriza` y barrera de mezcla del 76 | Reetiquetado deliberado no autenticado; nunca permiso |
| 12. Parámetros sin fuente | Nueva `test_parametros_sin_procedencia_no_se_suplen_con_afirmacion_generica` | INSUFICIENTE; una referencia válida en otro parámetro no lo oculta. Control positivo con ambos documentados |
| 13. Versiones diferentes | `test_distintos_ids_mismo_localizador_y_version_conflictiva` | EVIDENCIA_CONTRADICTORIA |
| 14. Metadatos ausentes | Pruebas existentes de unidad, frecuencia, instrumento, continuidad y cobertura | No se inventan valores para cerrar requisitos |
| 15. Diagnóstico como permiso | `test_diagnostico_no_se_usa_como_booleano_o_permiso_del_catalogo`, barrera del PASO 75 | TypeError, sin autorización ni ejecución |

Las tres pruebas nuevas reutilizan la fixture sintética del 76 mediante su módulo,
sin importar su TestCase al espacio de descubrimiento. No se duplican sus 63
pruebas. No se construyen aprobaciones humanas para superar barreras.

## Bloqueos y expediente institucional

TEMP-LIM y HR-LIM mantienen INFORMACION_INSUFICIENTE respecto del producto.
Pueden continuar hacia revisión científica humana, no hacia ejecución. PP-LIM
mantiene bloqueos de total/unidad/integración; paso, persistencia, ventanas y
límites locales siguen bloqueados por evidencia temporal, metrológica o de estación.
No se activan estos ni otros candidatos del expediente.

Se preparan una [matriz de información faltante](matriz_evidencias_senamhi.md) y
un [borrador de solicitud](solicitud_tecnica_senamhi_borrador.md). Este último no
tiene destinatario personal, correo, número de expediente o representación
institucional inventados. No se envió ninguna comunicación.

## Verificación final y conservación del trabajo previo

Con Python **3.15.1 de `.venv`**, SQLite **3.53.4**:

```text
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
Ran 938 tests in 103.265s
OK

.\.venv\Scripts\python.exe -B -m pip check
No broken requirements found.

git diff --check
Código 0, sin errores de whitespace.

git diff --cached --check
Código 0, sin errores de whitespace.
```

Git avisó que LF será reemplazado por CRLF cuando vuelva a escribir la copia de
trabajo del verificador; es un aviso de finales de línea, no un error de pruebas
o sintaxis. No se cambió configuración Git para suprimirlo.

**938 aprobadas: 935 anteriores y tres nuevas; cero fallos, errores u omisiones.**
Los identificadores completos de las 935 anteriores coinciden exactamente con
el registro del PASO 76. No hay duplicación accidental por reutilizar su fixture.
Las tres nuevas también aprobaron por separado.

La ejecución completa utilizó una guardia temporal fuera del repositorio, cargada
mediante `PYTHONPATH` transitorio junto con `src`. Bloquea accesos Python a las
rutas operativas conocidas bajo SPICA_DATOS y conexiones reales; registró cero
intentos bloqueados. No es un sandbox del sistema operativo ni garantiza detección
de alias/hardlinks o código nativo hostil. No se abrieron RAW, staging ni SQLite
operativos, tampoco para inventarios o comprobaciones físicas de conservación.

La evidencia técnica queda en el directorio temporal
`spica-paso77-824ade6d174d4299b26d804d62918b9c`, fuera de Git y de los almacenes:
`baseline.json`, `adversarial_antes.json`, `unittest.log`, `resultado.json` y la
guardia. Contiene la reproducción anterior al arreglo y el resultado de la suite.
No se altera su clasificación sintética ni se presenta como evidencia institucional.

Se comprobaron por separado UTF-8, sintaxis mediante compilación en memoria,
espacios finales, salto final, marcadores de conflicto y enlaces Markdown locales
de los archivos nuevos/modificados. Los blobs del índice coinciden exactamente
con la instantánea inicial. Los otros cinco archivos del PASO 76 conservan también
sus bytes iniciales; solo el verificador difiere en el árbol de trabajo.

Estado final de Git, con HEAD y rama sin cambios:

```text
A  docs/aplicabilidad_temp_hr_lim.md
A  docs/verificador_aplicabilidad_cientifica.md
A  src/spica/calidad/aplicabilidad/__init__.py
A  src/spica/calidad/aplicabilidad/modelos.py
AM src/spica/calidad/aplicabilidad/verificador.py
A  tests/test_aplicabilidad_cientifica.py
?? docs/auditoria_confianza_documental.md
?? docs/matriz_evidencias_senamhi.md
?? docs/solicitud_tecnica_senamhi_borrador.md
?? tests/test_confianza_documental.py
```

En este paso se crearon cuatro archivos y se corrigió uno. Los seis añadidos
previamente al índice siguen pendientes de commit; `AM` distingue el archivo
preparado de su corrección local. La suite acredita el árbol de trabajo probado,
no que el contenido preparado incluya esa corrección.

No se modificaron observaciones, contratos públicos, controles Nivel 0,
autorizaciones, dependencias o datos operativos. No hubo descargas, migraciones,
instalaciones, comunicaciones externas, commits o push. Permanece pendiente la
revisión del expediente y del estado Git antes de decidir cómo registrar el trabajo.
