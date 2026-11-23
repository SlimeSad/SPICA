# RC15 — Auditoría arquitectónica del vínculo documental M26

Fecha: **2026-11-23**, America/Lima.
[Contrato y definición literal](contrato_vinculo_documental_rc15.md),
[piloto, identidades y casos](piloto_vinculo_documental_rc15.md).

## Recuperación y fuentes

Estado inicial: `git status` limpio, rama **feature/suadc-http**, HEAD
**2cfb3a45774e37298ce3d194ab5e65dc60491576**. RC14 registrado:

```text
2cfb3a4 SPICA: integracion opcional de precondiciones no QA RC14
0e8b759 SPICA: precondicion productora no QA experimental RC13
43ff570 SPICA: auditoria transversal y hoja de ruta arquitectonica RC12
128ada9 SPICA: dictamen experimental de dependencia no QA RC11
98094c1 SPICA: conservacion versionada de evidencias tecnicas RC10
```

Se revisaron los tres documentos RC14:
[interfaces](evolucion_interfaz_coordinacion_rc14.md),
[piloto](piloto_habilitacion_acotada_rc14.md) y
[auditoría](auditoria_arquitectonica_rc14.md); los cuatro RC12:
[auditoría](auditoria_transversal_arquitectura_rc12.md),
[matriz](matriz_trazabilidad_conexiones_rc12.md),
[decisión](decision_evolucion_cierres_noqa_rc12.md) y
[hoja de ruta](hoja_ruta_priorizada_rc12.md); y la
[auditoría original 85-M](auditoria_continuidad_arquitectonica_paso85m.md) con su
[matriz](matriz_diseno_implementacion_paso85m.md) y la
[definición original 85-F](matriz_dependencias_integracion_paso85f.md).

La fila M26 original dice literalmente:

> evaluar_uso es diagnóstico; no conversor a formato QA, AfirmacionAplicabilidad o permiso

Participantes originales **C20 → C21/C24/C19**. Estado **P para una vinculación
explícita revisada**, conservado por 85-M/RC12/RC14. C20 produce afirmaciones y
cotejos; C21 es QA0; C24, reglas/aplicabilidad; C19, interoperabilidad. La matriz
RC12 exige revisión trazable por producto/uso, no promoción de confianza por
coincidencia. La puerta de definición tiene evidencia suficiente para ensayar
una relación concreta; no para dar por acreditados sus usos científicos futuros.

Las fuentes formales ERS/actas/H0/FUT/G0 siguen no localizadas según RC12/85-M.
No se reconstruyen ni se certifica cumplimiento formal. El encargo actual es la
autorización del alcance sintético, no una aprobación institucional o científica.

## Decisión e implementación

Se selecciona el producto catalogado **SENAMHI–PNDA GBON/RBON**, ya soportado por
el conector. La finalidad única es `revision_documental_identidad_producto_pnda`:
preparar la dimensión PRODUCTO de un ExpedienteProducto C24, con referencia
documental explícita. Se preserva el ID oficial exacto desde sus constantes.

La descripción, edición, DOCX, revisión y proyectos del piloto son inventados.
No constituyen una versión o metadatos nuevos del producto institucional real.
Las ediciones reales desconocidas permanecen None y bloquearían este perfil.
No se accede al CSV o documentos operativos para rellenarlas.
La inspección del código del conector confirma que su descubrimiento actual no
asigna ProductoCatalogo.version. Ese bloqueo real permanece: el caso positivo
usa una edición explícitamente ficticia y no demuestra que una salida actual
del conector pueda superar RC15 sin nueva evidencia pertinente.

Los contratos existentes cubren ambos extremos, pero no la relación revisada con
proyecto/artefacto/finalidad. Se añade un **adaptador de checkout**, sin trasladar
el cotejador a src ni introducir importaciones src→herramientas. No se crea otro
parser, infraestructura de procedencia, gestor documental, catálogo o DAG.

La solicitud conserva ProductoCatalogo, DescriptorArtefacto RC4, operación RC1 y
ExpedienteMetadatos. La revisión aporta responsable/procedencia y fija el snapshot
completo. El adaptador vuelve a evaluar el uso nativo y ejecuta el cotejador físico
existente; no acepta un DTO favorable como comprobación. Produce una salida C24
nativa, solo PRODUCTO, **DECLARADA**, con referencia original y pendientes.

Se reutilizan MD/RC1, perfiles RC2, descriptor RC4, RestriccionPropagada y la unión
nativa de restricciones, sin nuevos modelos equivalentes. El único helper privado
reutilizado de RC4 es `_unir_origenes`; este acoplamiento de checkout se documenta,
sin convertirlo en API pública ni copiarlo.

RC5/RC6 se inspeccionaron como evidencia física/conservación: no hay necesidad de
publicar/conservar el snapshot del producto en este piloto descartable. El DOCX
se comprueba con el cotejador específico existente (máximo 1 MiB). No se añade
un almacén RC5 o generación RC6. RC8/RC9 prueban otra responsabilidad (exportación
y consumo JSON QA0), y no sustituyen el documento/revisión. RC14 aporta la
separación conceptual entre habilitación y permiso; no se modifica ni se usa para
forzar la admisión documental.

## Evidencia, restricciones y límites del resultado

| Dimensión | Comprobación RC15 / límite |
|---|---|
| Producto/proyecto/objeto/revisión | Correspondencia de snapshots nativos y entrada canónica; no identidad por igualdad SHA |
| Operación productora | El conector soporta el producto, pero no se ejecuta ahora. La operación RC1 del piloto describe la revisión y permanece DECLARADA; no prueba producción institucional |
| Documento disponible | DOCX físico sintético en TEMP, leído de nuevo por el cotejador |
| Identidad/integridad documental | Referencia completa frente a control, tamaño/SHA reales, estructura y conservación final del archivo controlado |
| Relación literal | Localizador DOCX y texto del identificador exacto; no inferencia semántica |
| Procedencia/revisión | Antecedente trazable aportado y sintético; responsable y legitimidad no autenticados |
| Restricciones | Contexto/proyecto/artefacto/operación con orígenes; expediente y producto originales conservan restricciones documentales/licencia |
| Salida C24 | ProductoCatalogo y EvidenciaDocumental originales, AfirmacionAplicabilidad PRODUCTO DECLARADA con incertidumbres y pendientes explícitos |
| Integridad del producto meteorológico | No comprobada: no se lee ni materializa el CSV o el snapshot de catálogo |
| Ciencia/permiso/autenticidad | No acreditados ni concedidos; flags False |

No existe un campo de restricciones estructuradas en ExpedienteProducto. Se
mantienen en el **informe completo**, junto al expediente original; la salida
incluye pendientes que impiden tratarla como fundamento aprobado aislado.
No se amplía silenciosamente ese contrato ni se descartan restricciones para que
quepa una prueba positiva. Esta limitación condiciona cualquier consumidor futuro.

Estados: APTO_ESTRUCTURALMENTE solo para la relación del perfil; faltantes dejan
PENDIENTE_DE_EVIDENCIA; contradicciones/bloqueos, INCOMPATIBLE. Salida None salvo
caso coherente. Edición desconocida no se presenta como contradicción; ausencia
del archivo no se presenta como corrupción física. Artefactos/operaciones
parciales/fallidas/canceladas no se promueven.

## Archivos y compatibilidad

| Estado | Archivo | Responsabilidad |
|---|---|---|
| Nuevo | [vinculo_documental_rc15.py](../herramientas/vinculo_documental_rc15.py) | Contrato específico y adaptador de checkout, versión 0.1.0 |
| Nuevo | [test_vinculo_documental_rc15.py](../tests/test_vinculo_documental_rc15.py) | 27 pruebas sintéticas y barreras de proceso |
| Nuevo | [contrato_vinculo_documental_rc15.md](contrato_vinculo_documental_rc15.md) | Fuentes, selección, contrato y fronteras |
| Nuevo | [piloto_vinculo_documental_rc15.md](piloto_vinculo_documental_rc15.md) | Identidades, escenarios y evidencias |
| Nuevo | Este documento | Auditoría y resultados finales |

Ningún archivo histórico se modifica. Firmas/APIs predeterminadas RC3/RC7/RC14,
modelos, estados, reglas, QA y restricciones anteriores permanecen intactos. Sin
cambios a main.py, .gitignore, .venv, dependencias, SQLite 85001, 85-J/K,
rc6.generacion.0.1.0, rc10.evidencias.0.1.0 o JSON QA 0.1.0. No se añade un tipo
RC15 a codecs ni un nuevo formato durable.

## Verificaciones efectivamente ejecutadas

Python **3.15.1 de .venv**, HTTPX **0.28.1**, SQLite **3.53.4**. Se utiliza -B,
PYTHONDONTWRITEBYTECODE=1 y PYTHONPATH temporal del proceso para src/tests.

La ejecución inicial de 24 casos dentro del sandbox produjo **48 errores** de
preparación/limpieza por permisos de TEMP privado; no evaluó el adaptador ni se
cuenta aprobada. Se repitió con acceso a TEMP: 23 aprobadas y un error de prueba
por esperar ValueError en vez de TypeError de dataclasses.replace de Python 3.15.
Se corrigió esa expectativa, sin relajar la protección init=False. Después
aprobaron 24/24 y 26/26 al añadir barreras/traspaso. Las regresiones dirigidas
intermedias aprobaron 492. La revisión final añadió la distinción de ediciones
desconocidas, sin clasificar la ausencia de evidencia como contradicción.

Los 24 directorios vacíos del primer intento se retiraron únicamente tras
verificar nombres exactos, padre absoluto TEMP, intervalo de creación, ausencia
de enlaces y contenido vacío, sin borrado recursivo. No se tocaron temporales
ajenos. Los contextos de las ejecuciones válidas comprueban su propia limpieza.

Pruebas dirigidas finales:

```powershell
.\.venv\Scripts\python.exe -B -m unittest test_vinculo_documental_rc15 test_metadatos_documentales test_metadatos_compatibilidad_docx test_vinculacion_documental test_aplicabilidad_cientifica test_confianza_documental test_contextos_rc1 test_perfiles_informacion_rc2 test_artefactos_rc4 test_cierre_exportacion_rc8 test_admision_exportacion_rc9 test_coordinacion_precondicion_rc14 -v
```

```text
Ran 493 tests in 42.620s
OK
```

**493 aprobadas**, 27 nuevas y 466 regresiones, cero fallidas/errores/omitidas.
Log completo fuera de Git:
`%TEMP%\spica-rc15-dirigidas-final-60da416608464b4bb95d102436ea852b.log`.

Revisión estática: **209 Python**, 129 src, diez herramientas y 70 test_,
parseados/compilados en memoria sin errores ni definiciones duplicadas por ámbito;
**2560 IDs test_ estáticos únicos**, sin atribuir ejecución por contarlos. Ningún
import explícito src→herramientas/tests. Al no cambiar src y depender la herramienta
solo de componentes previos, no se añade ciclo de retorno. Se ensayan dos órdenes
de importación en procesos aislados; no se certifica todo recorrido dinámico.
El subgrafo src conserva los grupos diferidos históricos de transporte y
almacenamiento/catálogo/integración ya documentados en RC12/RC14; no se afirma
que todas las dependencias históricas sean acíclicas.

Se comprobó además la coherencia de los tres Markdown: UTF-8/EOF, sin espacios
finales, conflictos o bloques abiertos, **nueve tablas** con columnas consistentes
y **27 enlaces locales** existentes. No se consultan URLs externas. El recuento
directo de la matriz PNDA conserva 29 IDs únicos y sus estados 2/17/8/2.
Los dos pilotos físicos adicionales generan un DOCX de 1308 bytes con el mismo
SHA indicado en el piloto, salida nativa declarada y limpieza de ambos TEMP.
No se suman esas ejecuciones al contador unittest.

Huellas del código definitivo congeladas antes de la suite completa:

```text
herramientas/vinculo_documental_rc15.py
2de0841e9fd977eee700ebede10db116cdb84647f0f405cbf3052a6484e31846
tests/test_vinculo_documental_rc15.py
d375939942f2de7595ea8c2bd84f1b4d852aef7eed29add7343bbb0e8a14d3fa
```

Suite completa final ejecutada después de congelar el código:

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
```

```text
Ran 2560 tests in 954.772s
OK
```

**2560 aprobadas: 2533 anteriores y 27 nuevas; cero fallidas, cero errores y cero
omitidas.** Salida del proceso 0. Log completo de 824920 bytes fuera de Git:
`%TEMP%\spica-rc15-suite-final-5e257781c9ff4d14bae13873351d5ef2.log`.
Se revisaron ese log y el dirigido final: sin FAIL, ERROR, skipped o ResourceWarning.
Las dos huellas posteriores coinciden con las congeladas. Durante la suite se
completó únicamente documentación, sin cambiar el código o las pruebas.

```powershell
.\.venv\Scripts\python.exe -B -m pip check
git diff --check
git diff HEAD --exit-code
git diff --cached --exit-code
git status --short
```

pip check: **No broken requirements found.**, salida 0. Los tres comandos diff:
sin salida y código 0. No hay cambios en archivos registrados ni en el índice.
La validación explícita de los cinco archivos nuevos complementa diff --check,
que por sí solo no examina archivos sin seguimiento.

Contraste TEMP antes/después de la suite: **113 directorios spica-* en ambos
inventarios, cero nuevos restantes y cero previos ausentes**. Se compararon solo
nombres de esos directorios ajenos, sin inspeccionar/modificar su contenido.
Los logs de verificación se conservan deliberadamente como archivos fuera de
Git. La limpieza de raíces propias se comprueba además dentro de las pruebas.

Git final: misma rama y HEAD inicial, sin commits. Solo cinco archivos nuevos:

```text
?? docs/auditoria_arquitectonica_rc15.md
?? docs/contrato_vinculo_documental_rc15.md
?? docs/piloto_vinculo_documental_rc15.md
?? herramientas/vinculo_documental_rc15.py
?? tests/test_vinculo_documental_rc15.py
```

## Estado fundamentado de M26 y conexiones originales

| Responsabilidad M26 | Estado acreditado por RC15 |
|---|---|
| Definición/fuentes/participantes | Recuperados literalmente de 85-F y precisados por 85-M/RC12 |
| Selección por producto, finalidad, documento y revisión | Implementada para el perfil sintético de identidad PNDA |
| C20 → AfirmacionAplicabilidad/ExpedienteProducto C24 | Traspaso nativo demostrado, nivel DECLARADA y pendientes; no solo dictamen externo |
| Disponibilidad/integridad/literal del documento | Comprobación real del DOCX sintético controlado, en el alcance de su lectura |
| Revisión legítima, pertinencia científica, edición real y derechos | Pendientes; no autenticados por el piloto |
| Otras dimensiones/destinos/métodos | Pendientes; no se integra automáticamente QA, campos RC2 o reglas científicas |
| Conformidad formal con ERS/actas | No comprobable con las fuentes actualmente disponibles |
| Cierre total M26 | **PENDIENTE**, avance parcial experimental acotado; no se cambia la fila histórica a RESUELTA |

M03 conserva su definición (plan/selectores → conector/HTTP): sin ejecutor o
traducción institucional nuevos. M16 (recomendación de readquisición → efecto)
sigue sin hook/permiso/ejecutor. M32 (resultado científico → almacenamiento/
exportación) sigue sin productor/formato/cadena científicos, con avances previos
contractuales/físicos; JSON QA no la resuelve. Las tres permanecen pendientes.

Las [29 brechas PNDA](brechas_reconciliadas_pnda_paso84i.md) conservan dos resueltas,
17 parcialmente documentadas, ocho pendientes y dos contradicciones documentadas.
No se cambia una brecha por usar su producto nominal en una fixture. INGEMMET
/query permanece NO AUTORIZADO. No se inician núcleos científicos.

## Riesgos, dependencias pendientes y dictamen

| Riesgo | Gravedad condicionada / tratamiento |
|---|---|
| Confundir APTO con ciencia o permiso | Alta para ese uso; nivel DECLARADA, pendientes, flags False y finalidad única |
| Revisión/control aportados bajo la misma autoridad | Alta si se exige autenticidad independiente; no firmas ni revisión humana real acreditada; mantener ese uso bloqueado |
| Extraer ExpedienteProducto sin las restricciones del informe | Alta si se usa como fundamento; unidad de entrega es informe completo, sin consumidor científico aprobado |
| Confundir archivo íntegro con producto/semántica correctos | Alta para ciencia; cotejo literal y hash solo del DOCX sintético, sin identidad institucional o lectura CSV |
| Acoplamiento al cotejador/helper privado de checkout | Media; APIs históricas sin cambios, adaptador pequeño y regresiones; no se presenta como API pública estable |
| Temporalidad, TOCTOU y recursos | Media; comprobación fechada, conservación final nativa y límites del inspector; sin reserva/RSS/plazo global o custodia |
| Requisitos formales ausentes | Impide homologación formal; no reconstruir ERS/actas mediante esta auditoría |

Para cerrar el uso científico pertinente de M26 faltan evidencia real autorizada,
ediciones/coberturas aplicables, revisión humana legítima del método/producto y
dimensiones necesarias (variable, unidad, medición, frecuencia, etc.), junto a un
destino que preserve estructuradamente restricciones y no confunda diagnóstico
con autorización. Harían falta positivos/negativos con esas fuentes revisadas y
aceptación expresa; este piloto no los sustituye.

Próximo incremento propuesto: **revisar el expediente y los criterios de revisión
del primer uso concreto de M26**, incluida la entrega completa de restricciones,
sin implementar aún un algoritmo ni un gestor documental. Recuperar las fuentes
formales pertinentes cuando se solicite conformidad, sin acceder a carpetas
privadas por iniciativa propia. No se inicia automáticamente RC16.

Dictamen del incremento: **APTO CON RESTRICCIONES** para revisar el vínculo
experimental de identidad y su piloto offline. M26 y la arquitectura integral
permanecen abiertas; no es un dictamen de aptitud operativa o científica.

Cero conexiones externas/GET/descargas/instalaciones/migraciones/commits/push.
No se lee CSV PNDA, RAW o SQLite operativo ni información institucional privada;
no se accede a staging operativo. La confirmación describe nuestras acciones,
no una verificación física actual de originales deliberadamente no abiertos.
Se espera auditoría antes de continuar.
