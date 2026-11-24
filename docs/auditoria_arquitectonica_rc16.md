# RC16 — Auditoría del primer uso documental M26

Fecha: **2026-11-24**, America/Lima.
[Criterios y contrato](criterios_primer_uso_m26_rc16.md),
[matriz de 17 criterios y piloto](evidencias_y_restricciones_m26_rc16.md).

## Estado inicial y fuentes

Git inicial limpio, rama **feature/suadc-http**, HEAD
**e989a7219a709303b35ca97b89073aa73d022a2a**. RC15 consolidado:

```text
e989a72 SPICA: vinculo documental experimental M26 RC15
2cfb3a4 SPICA: integracion opcional de precondiciones no QA RC14
0e8b759 SPICA: precondicion productora no QA experimental RC13
43ff570 SPICA: auditoria transversal y hoja de ruta arquitectonica RC12
128ada9 SPICA: dictamen experimental de dependencia no QA RC11
```

Se revisaron los tres documentos RC15:
[contrato](contrato_vinculo_documental_rc15.md),
[piloto](piloto_vinculo_documental_rc15.md),
[auditoría](auditoria_arquitectonica_rc15.md), su
[adaptador](../herramientas/vinculo_documental_rc15.py) y
[pruebas](../tests/test_vinculo_documental_rc15.py); la
[matriz original 85-F](matriz_dependencias_integracion_paso85f.md), las
[responsabilidades C19/C20/C21/C24](auditoria_arquitectura_integral_paso85f.md),
la [auditoría 85-M](auditoria_continuidad_arquitectonica_paso85m.md) y la
[matriz RC12](matriz_trazabilidad_conexiones_rc12.md), especialmente M26.
Se contrastaron modelos de catálogo/afirmaciones/restricciones/informes,
evaluar_uso, ExpedienteProducto y la construcción de ProductoCatalogo en PNDA.

M26 conserva **C20 → C21/C24/C19** y la definición literal:

> evaluar_uso es diagnóstico; no conversor a formato QA, AfirmacionAplicabilidad o permiso

La aceptación histórica requiere vínculo explícito revisado y evidencia
pertinente; COINCIDE/VERIFICADO no equivalen a aprobación. RC15 demostró un
vínculo C20 → C24 para PRODUCTO DECLARADA con un DOCX sintético y pendientes,
sin revisión humana legítima o autenticidad institucional acreditadas. No se
redefine esa historia. ERS/actas/H0/FUT/G0 y el protocolo formal siguen no
localizados según las auditorías disponibles; se aplican las instrucciones del
encargo actual sin certificar cumplimiento formal de documentos ausentes.

## Decisión y alcance implementado

Se conserva el producto catalogado SENAMHI–PNDA GBON/RBON y la finalidad
`revision_documental_identidad_producto_pnda`. El ID nominal se toma del código;
todo el documento, proyecto, recurso, edición y revisión del piloto son
sintéticos. No se comprueban datos institucionales actuales.

Antes de programar se compararon A/B/C. A basta para representar y mantener un
InformeVinculoRC15, pero no había una entrada que exigiera recibirlo completo y
cotejara posibles omisiones. **B elegida**: adaptador pequeño de recepción, con
composición tipada de las referencias originales y del nuevo resultado RC15.
**C se mantiene** para acreditar un uso real o persistir un perfil no admitido:
faltan evidencias/contratos y no se fuerza esa implementación.

El adaptador vuelve a llamar a RC15; no copia su política de identidad/edición,
evaluar_uso, unión de restricciones, lector, inspector o cotejo. No se crea otro
sistema de informes, procedencia, permisos, revisión humana o metadatos. No se
modifican APIs anteriores ni se extienden silenciosamente los codecs.

La única función nueva es comprobar_primer_uso_m26(informe, *, solicitud_esperada,
cotejador). Exige el informe nativo completo y lo conserva como **el mismo objeto**.
ComprobacionPrimerUsoM26 contiene solicitud esperada, informe aportado, nuevo
informe actual opcional y diagnósticos nativos propios. Conserva causas, bloqueos,
orígenes y expedientes de ambas lecturas. No hay una salida de expediente aislado
que sustituya a la composición completa.

El estado de coherencia combina ambos informes y el contraste. Un faltante
anterior no desaparece si una lectura nueva es favorable. Una contradicción
prevalece. La acreditación del uso permanece pendiente incluso con coherencia
APTO_ESTRUCTURALMENTE: las fixtures no prueban legitimidad humana o uso real.
Los flags uso/revisión humana/autenticidad/ciencia/permiso son False y no
configurables por constructor. No se crea una afirmación científica favorable:
el expediente nuevo, si existe, procede exclusivamente de RC15 y sigue DECLARADA.

## Reutilización y fronteras

| Componente previo | Uso o decisión RC16 |
|---|---|
| MD/RC1, RC2 y RC4 | Mantener proyecto/contexto, entrada canónica, objeto/revisión, perfil, artefacto, operación y restricciones; no otro modelo equivalente |
| ProductoCatalogo/ProcedenciaCatalogo/C19 | Conservar literal de versión/desconocidos, identidad/recurso, revisión de metadatos y procedencia aportada |
| C20 y cotejador 84-L | RC15 vuelve a invocar consulta/cotejo seguro; física solo del documento controlado, no del CSV o catálogo operativo |
| C24 | Reutilizar ExpedienteProducto y afirmaciones nativas, manteniendo nivel/pending y los informes que contienen el resto de las restricciones |
| RC3/RC7/RC14 | No se cambian ni se usan como admisión de documentos o aprobación de M26 |
| RC5/RC6/RC10, 85-J/K | Mantener perfiles existentes; no hay un codec para conservar esta composición completa y no se promete recuperación durable |
| RC8/RC9/RC11/RC13 | Sus cierres/cotejos técnicos no acreditan revisión documental humana o científica; no se reinterpretan como permisos |

ProductoCatalogo.version es opcional y no impone semántica editorial universal.
El descubridor no lo asigna. None es desconocimiento legítimo, no identidad
perdida ni edición contradictoria. Con None el piloto conserva el ID y puede
ejecutar la consulta documental y, separadamente, la física del DOCX. El vínculo
RC15 permanece pendiente por su requisito de edición conocida, conservado sin
cambios. El catálogo, revisión local, fecha o SHA no proporcionan una versión
institucional automáticamente. El mecanismo futuro de obtención legítima se
describe en los criterios; RC16 no realiza conexiones para resolverlo.

La recepción completa se exige en la entrada nueva, **no en todas las APIs de
SPICA**. El verificador C24 previo sigue aceptando ExpedienteProducto. Otro
llamador puede omitir voluntariamente RC16: eso queda fuera del perfil y no
acredita M26. No se atribuye seguridad frente a Python hostil o autenticidad
independiente a dataclasses, controles o registros de revisión aportados.

## Piloto y evidencia disponible

Los escenarios A–L están descritos con resultado en la matriz enlazada:
coherencia, versión desconocida/conocida ficticia, revisión incompatible,
documento alterado, finalidad incompatible, bloqueos, informe ausente, expediente
insuficiente, revisión humana no acreditada, procedencia no autenticada y
contenido idéntico con identidades diferentes. Se usan fabricantes nativos;
no se fabrica un escenario científicamente aprobado.

Se comprueban además pérdida de campos/diagnósticos, restricciones suprimidas,
causas previas, desconocidos de licencia, determinismo y resumen público seguro.
El cotejo físico real se realiza en DOCX de TEMP. Un documento alterado conserva
la lectura anterior y el fallo actual por separado. No se afirma una comprobación
de los originales operativos, que deliberadamente no se abren.

El piloto adicional A/C frente a B confirmó los mismos 1308 bytes/hash del DOCX
controlado, preservación de ambos informes/restricciones y del None original.
Con edición ficticia se prepara expediente; con None no se prepara, aunque una
lectura física independiente satisfaga el control. Ningún caso acredita uso real
o revisión humana. La limpieza del TEMP propio se comprobó al salir; no se cuenta
como pruebas unitarias adicionales. El cotejo nativo no aporta un timestamp UTC
de ejecución propio y no se inventa ese dato.

Los dos órdenes de importación se ejercen en procesos aislados con hooks contra
red/SQLite/nuevos procesos, lectura operativa y escrituras ajenas al TEMP. No
se presentan esos hooks como un sandbox universal o certificación de SO. Los
contextos de las pruebas comprueban su propia limpieza.

## Archivos y compatibilidad

| Estado | Archivo | Responsabilidad |
|---|---|---|
| Nuevo | [primer_uso_m26_rc16.py](../herramientas/primer_uso_m26_rc16.py) | Recepción específica y composición tipada efímera, versión 0.1.0 |
| Nuevo | [test_primer_uso_m26_rc16.py](../tests/test_primer_uso_m26_rc16.py) | 16 pruebas con escenarios reales del alcance y fixtures sintéticas |
| Nuevo | [criterios_primer_uso_m26_rc16.md](criterios_primer_uso_m26_rc16.md) | Decisión, contrato, tratamiento de None y criterios |
| Nuevo | [evidencias_y_restricciones_m26_rc16.md](evidencias_y_restricciones_m26_rc16.md) | Matriz de 17 criterios, responsables funcionales y piloto A–L |
| Nuevo | Este documento | Auditoría, comprobaciones y dictamen |

Sin cambios a archivos históricos, incluidos RC15, su test y descubridor PNDA.
No se modifica src, main.py, .gitignore, .venv, dependencias o las 29 brechas.
JSON QA 0.1.0, RC6, RC10, 85-J/K y SQLite 85001 conservan contratos/formatos.
La composición RC16 no se introduce en ningún registro de persistencia.

## Verificaciones ejecutadas

Python **3.15.1 de .venv**, HTTPX **0.28.1**, SQLite **3.53.4**. Se usan -B,
PYTHONDONTWRITEBYTECODE=1 y PYTHONPATH solo en el proceso, apuntando a src/tests.
Las pruebas con TEMP privado se ejecutan con el acceso necesario fuera del
sandbox restringido; siguen siendo fixtures sin red ni almacenamiento operativo.

Primera ejecución RC16/RC15: **43 aprobadas, cero fallidas/errores**, 29.636 s.
Antes del cierre se retiró una cota arbitraria sobre las tuplas del informe nativo
para no reducir su contrato; se conservó la validación estricta de tipos. Se
repitieron las dirigidas sobre el código definitivo:

```powershell
.\.venv\Scripts\python.exe -B -m unittest test_primer_uso_m26_rc16 test_vinculo_documental_rc15 test_metadatos_documentales test_metadatos_compatibilidad_docx test_vinculacion_documental test_aplicabilidad_cientifica test_confianza_documental test_contextos_rc1 test_artefactos_rc4 -v
```

```text
Ran 307 tests in 32.872s
OK
```

**307 aprobadas**, 16 nuevas y 291 regresiones, cero fallidas/errores/omitidas.
Log completo fuera de Git:
`%TEMP%\spica-rc16-dirigidas-91be5d786b32487eba1edc302aa50ed8.log`.

Análisis AST/compilación en memoria: **211 Python**, 129 src, 11 herramientas y
71 test_, sin errores o definiciones duplicadas por ámbito. **2576 IDs test_
estáticos únicos**, sin atribuir aprobación por ese recuento. Ningún import
explícito src→herramientas/tests; src no cambia. La nueva herramienta depende
de RC15/componentes previos sin import de retorno, por lo que no añade un ciclo
explícito. Se conservan los grupos diferidos históricos documentados en RC12/14;
no se afirma aciclicidad universal de todos los recorridos dinámicos.

Los tres Markdown se revisaron como UTF-8/EOF, sin conflictos, espacios finales
o bloques abiertos: **ocho tablas**, **30 enlaces locales** existentes y criterios
U01–U17 únicos. Se contaron directamente los 29 IDs de la matriz PNDA y sus
estados 2/17/8/2, sin cambios. Ningún enlace externo se consultó.

Huellas de los dos archivos Python definitivos antes de la suite completa:

```text
herramientas/primer_uso_m26_rc16.py
cb8af79e16ca33cc9b32d405f3c4bc16f3b6632b24e2b0ef655ee43d4ded6d34
tests/test_primer_uso_m26_rc16.py
f0f183e48e9d6285204341a884151816678b12d4c563b0c633ab1fca3dd7363e
```

Suite completa final sobre esas mismas huellas de código:

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
```

```text
Ran 2576 tests in 1805.647s
OK
```

**2576 aprobadas: 2560 anteriores y 16 nuevas; cero fallidas, cero errores y cero
omitidas.** Salida del proceso 0. Log completo de 830650 bytes fuera de Git:
`%TEMP%\spica-rc16-suite-final-db4f5f59d763481ba418d1b56ad26c24.log`.
El log dirigido final tiene 105788 bytes. Ambos se revisaron: sin FAIL, ERROR,
skipped o ResourceWarning. Las huellas posteriores coinciden con las congeladas;
durante la suite solo se completó documentación, sin cambiar Python/pruebas.

```powershell
.\.venv\Scripts\python.exe -B -m pip check
git diff --check
git diff HEAD --exit-code
git diff --cached --exit-code
git status --short
```

pip check: **No broken requirements found.**, salida 0. Se deshabilitaron solo en
su proceso la consulta de versión de pip y los índices mediante
PIP_DISABLE_PIP_VERSION_CHECK=1 y PIP_NO_INDEX=1, sin cambiar configuraciones.
Los tres comandos diff: sin salida y código 0. Los archivos registrados y el
índice permanecen intactos; la revisión explícita de los cinco archivos nuevos
complementa diff --check, que por sí solo no los cubre.

TEMP: **113 directorios spica-* antes y después**, cero nuevos restantes y cero
previos ausentes. Se compararon solo nombres, sin leer o modificar contenido
ajeno. Los contextos de las pruebas y piloto comprobaron su limpieza. Los logs
se conservan deliberadamente como archivos fuera de Git; no son datos operativos.

Git final: misma rama y HEAD inicial, sin commits ni cambios preparados. Solo
cinco archivos nuevos sin seguimiento:

```text
?? docs/auditoria_arquitectonica_rc16.md
?? docs/criterios_primer_uso_m26_rc16.md
?? docs/evidencias_y_restricciones_m26_rc16.md
?? herramientas/primer_uso_m26_rc16.py
?? tests/test_primer_uso_m26_rc16.py
```

## Estado M26 y siguientes dependencias

| Frontera | Cobertura y pendiente |
|---|---|
| C20 → C24 | RC15 prepara identidad PRODUCTO DECLARADA; RC16 añade recepción del informe completo y nuevo cotejo, preservando restricciones y pendientes. Experimental, un producto/uso, sin acreditación institucional/científica |
| C20 → C21 | Pendiente de selección/fundamento/revisión pertinentes; no convertir documentación a configuración QA o cierre ficticio |
| C20 → C19 | Pendiente del campo/uso y evidencia aplicables; no promover datos documentales a unidades, tiempo, espacio o respaldo científico verificados |
| M26 global | **PENDIENTE**, con avance acotado de recepción; no se cambia su fila histórica a RESUELTA |

M03 sigue siendo plan/selectores → conector/transporte, sin ejecutor/traductor
institucional. M16 sigue siendo recomendación de readquisición → efecto, sin
hook/permiso/ejecución nuevos. M32 sigue siendo resultado científico futuro →
almacenamiento/exportación, sin productor/formato/cadena científicos. Las tres
permanecen pendientes según sus definiciones originales.

Las [29 brechas PNDA](brechas_reconciliadas_pnda_paso84i.md) mantienen dos resueltas,
17 parcialmente documentadas, ocho pendientes y dos contradicciones documentadas.
Ni el ID nominal de producto ni un DOCX inventado cambian sus estados. INGEMMET
/query sigue NO AUTORIZADO. Ningún núcleo científico o RC17 se inicia.

## Riesgos, garantías y dictamen

| Riesgo residual | Gravedad condicionada / tratamiento |
|---|---|
| Confundir coherencia con acreditación/permiso | Alta para ese uso; estados separados, flags False y finalidad única |
| Omitir el receptor o extraer el expediente de la composición | Alta si se pretende acreditar M26; entrada nueva lo rechaza, pero no modifica todos los consumidores históricos ni defiende contra código hostil |
| Control/revisión bajo autoridad local cooperativa | Alta si se exige autenticidad independiente; no firma o revisión legítima real demostrada |
| Confundir edición ficticia, revisión o hash con versión real | Alta para aplicar documentación; None legítimo y bloqueo conservados, sin inferencias |
| Nueva lectura favorable que oculte causas anteriores | Controlado en el perfil: ambos informes y sus causas siguen presentes; no se reescribe historia |
| Persistencia, TOCTOU y recursos | Media; composición efímera y física limitada a la lectura del ensayo, sin timestamp UTC propio del cotejo, perfil durable, custodia o plazo global nuevo |
| Fuentes formales ausentes | Impide homologación formal; no reconstruir ERS/actas por inferencia |

Garantías demostradas: recepción tipada completa, conservación de las referencias
nativas, identificación del snapshot esperado, recálculo RC15, restricciones y
diagnósticos sin rebaja, manejo de None y escenarios incompatibles/pendientes,
sin permisos o ciencia automáticos. No demostradas: identidad institucional,
legitimidad humana, edición real, aplicabilidad/condiciones reales pertinentes,
custodia o persistencia durable del informe.

Prioridad propuesta: **preparar el expediente de evidencia de edición y revisión
humana para este mismo producto/uso**, con documentos exactos, alcance aplicable,
responsable legítimo y condiciones de revisión. Si no hay versión institucional,
obtener evidencia de su política sin inventar una. Cualquier acceso real requiere
un procedimiento posterior autorizado. Resolver el perfil de conservación solo
si el uso exige prometer durabilidad; no crear un almacén general por defecto.
No se inicia automáticamente RC17 ni un núcleo científico.

Dictamen del incremento: **APTO CON RESTRICCIONES**, para revisión de los criterios,
matriz y recepción experimental del informe completo. M26 sigue pendiente y la
arquitectura integral abierta; no es acreditación de un uso institucional real,
aptitud científica o conformidad con las fuentes formales no disponibles.

Cero conexiones/GET/descargas/instalaciones/migraciones/commits/push. No se lee
CSV PNDA real, RAW o SQLite operativo ni documentos institucionales privados;
no se accede o modifica staging operativo. Esta confirmación describe nuestras
acciones, no una verificación física actual de originales no inspeccionados.
Se espera auditoría antes de continuar.
