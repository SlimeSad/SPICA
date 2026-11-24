# RC17 — Auditoría de evidencia de edición y revisión humana M26

Elaboración: **2026-11-24**, America/Lima. Dictamen del incremento documental:
**APTO CON RESTRICCIONES**. No acredita edición institucional, revisión humana,
permisos, aplicabilidad científica ni el cierre de M26.
[Procedimiento de edición](procedimiento_evidencia_edicion_rc17.md),
[protocolo humano](protocolo_revision_humana_m26_rc17.md).

## Git recuperado y condición de partida

Rama **feature/suadc-http**, HEAD
**e989a7219a709303b35ca97b89073aa73d022a2a**. RC15 está registrado; **RC16 no
tiene commit**. Los cinco archivos RC16 ya estaban preparados en el índice:

```text
A  docs/auditoria_arquitectonica_rc16.md
A  docs/criterios_primer_uso_m26_rc16.md
A  docs/evidencias_y_restricciones_m26_rc16.md
A  herramientas/primer_uso_m26_rc16.py
A  tests/test_primer_uso_m26_rc16.py
```

No había diferencias sin preparar entre índice y árbol de trabajo. Este estado
se comunicó antes de continuar. No se confunde estar preparado con estar
registrado, ni se escribe un commit para corregir el contexto. Se preservan
los cinco archivos y el índice; la revisión RC17 usa esa base WIP explícita.

```text
e989a72 SPICA: vinculo documental experimental M26 RC15
2cfb3a4 SPICA: integracion opcional de precondiciones no QA RC14
0e8b759 SPICA: precondicion productora no QA experimental RC13
43ff570 SPICA: auditoria transversal y hoja de ruta arquitectonica RC12
128ada9 SPICA: dictamen experimental de dependencia no QA RC11
```

Comandos iniciales: `git status`, `git status --short`,
`git branch --show-current`, `git rev-parse HEAD`, `git log -5 --oneline`,
`git diff --stat`, `git diff --cached --stat` y `git ls-files --stage`.
Se capturaron además SHA-256 de los cinco archivos RC16 para contrastarlos al
final sin cambiar su estado. Ningún cambio inesperado se sobrescribe.

## Fuentes, contratos y responsabilidades contrastadas

Se revisaron los tres documentos RC15 y los tres RC16, herramientas y pruebas,
la definición M26 en 85-F, las responsabilidades originales, RC12 y su hoja de
ruta, y las 17 condiciones U01–U17. La inspección del código es selectiva por
responsabilidad y recorrido; no se presenta como certificación de cada instrucción.

| Componente / fuente | Contrato o responsabilidad real | Decisión RC17 |
|---|---|---|
| [Matriz original 85-F](matriz_dependencias_integracion_paso85f.md), [responsabilidades](auditoria_arquitectura_integral_paso85f.md) y [85-M](auditoria_continuidad_arquitectonica_paso85m.md) | M26 = C20 → C21/C24/C19; no convertir evaluar_uso en permiso o fundamento aprobado | Conservar significado, participantes y estado pendiente |
| [Auditoría RC12](auditoria_transversal_arquitectura_rc12.md), [trazabilidad](matriz_trazabilidad_conexiones_rc12.md), [decisión](decision_evolucion_cierres_noqa_rc12.md), [prioridades](hoja_ruta_priorizada_rc12.md) | Evidencia pertinente, producto/edición/uso y revisión trazable antes de ciencia | No iniciar ejecutores, núcleos o una plataforma general |
| [Contrato RC15](contrato_vinculo_documental_rc15.md), [piloto](piloto_vinculo_documental_rc15.md), [auditoría](auditoria_arquitectonica_rc15.md), [herramienta](../herramientas/vinculo_documental_rc15.py) | Solicitud, revisión aportada e informe completo; vínculo PRODUCTO DECLARADA, solo naturaleza SINTETICA | Mantener perfil y finalidad; impedir interpretar el ensayo como revisión legítima |
| [Criterios RC16](criterios_primer_uso_m26_rc16.md), [U01–U17](evidencias_y_restricciones_m26_rc16.md), [auditoría](auditoria_arquitectonica_rc16.md), [receptor](../herramientas/primer_uso_m26_rc16.py) | Referencia original + nuevo informe RC15; diagnósticos y restricciones de ambos; uso pendiente | Mantener la unidad completa y precisar límites de inmutabilidad/custodia |
| [Catálogo](../src/spica/adquisicion/catalogo/modelos.py) y [registro documental](../src/spica/adquisicion/catalogo/documental.py) | ProductoCatalogo.version opcional; ProcedenciaCatalogo aportada; revisiones locales distintas de edición | None legítimo, sin inferencia por hash o fecha; no consultar SQLite |
| [PNDA](../src/spica/adquisicion/conectores/senamhi/pnda.py) y [constantes](../src/spica/adquisicion/conectores/senamhi/modelos.py) | Descubridor construye ProductoCatalogo sin version; fuente institucional registrada como DECLARADO | No cambiar descubridor ni inventar versión institucional |
| [C20 modelos](../src/spica/metadatos_documentales/modelos.py), [evaluación](../src/spica/metadatos_documentales/evaluacion.py), [cotejador](../herramientas/vinculacion_documental.py) | Fuentes, afirmaciones, relaciones, localizadores y restricciones; evaluar_uso puro; física separada | Reutilizar referencias y controles; no otro lector, parser o autoridad |
| [C24 expediente](../src/spica/calidad/aplicabilidad/modelos.py) y [verificador](../src/spica/calidad/aplicabilidad/verificador.py) | ExpedienteProducto: producto, documentos, afirmaciones; no todas las restricciones RC15 | El expediente aislado y el resumen no sustituyen el informe completo |
| [Revisión científica](../src/spica/calidad/modelos_cientificos.py) | RevisionCientifica/RevisionReglaCientifica describen decisiones aportadas sobre reglas; no autentican personas | No emplearlas como aprobación humana ficticia de la identidad del producto |
| [C21 modelos](../src/spica/calidad/modelos.py), [motor](../src/spica/calidad/motor.py), [reglas](../src/spica/calidad/reglas.py) | QA0 estructural, estados técnicos y restricciones; no conversión automática desde documentos | C20 → C21 no implementado por RC17 |
| [C19 modelos](../src/spica/interoperabilidad/modelos.py), [adaptadores](../src/spica/interoperabilidad/adaptadores.py), [evaluador](../src/spica/interoperabilidad/evaluador.py) | Identidades, marcos, respaldos y aptitud con evidencia aportada; no interpretación científica automática | C20 → C19 no implementado por RC17 |
| [Contextos](../src/spica/contextos/modelos.py), [perfiles](../src/spica/interoperabilidad/perfiles/modelos.py), [artefactos](../src/spica/artefactos/modelos.py), [restricciones](../src/spica/coordinacion/modelos.py) | Snapshots, identidad contextual, entrada canónica y restricciones con orígenes | Sin cambios RC1/RC2/RC3/RC4/RC7; ninguna autorización por igualdad de contenido |

Las búsquedas de revisión/intervención humana localizaron RevisionVinculoRC15,
flags negativos RC16 y RevisionCientifica. No se encontró un servicio que
acredite identidad o realización humana para M26. La ausencia se limita a las
fuentes revisadas; no afirma inexistencia de actores o evidencia externos.
El protocolo formal original, ERS/actas/H0/FUT/G0 siguen no localizados según
85-M/RC12; se aplican los criterios del encargo sin certificar esas fuentes.

## Decisión A/C/D y compatibilidad futura

**A** para representación y auditoría: los contratos bastan para conservar
declaraciones, identidades, antecedentes, informes y restricciones. **C** para
edición/correspondencia y revisión legítimas: su evidencia no se obtiene en este
bloque offline. **D** para acreditar identidad, custodia o autoridad independiente:
excede RC17 y requiere alcance/actores definidos. No se desarrolla B por defecto,
ni un modelo de aprobación que transforme datos aportados en hechos acreditados.

Los tres documentos nuevos especifican qué recibir, quién debe revisar, cómo
asociar las piezas, qué registrar y qué no decidir. No son un nuevo codec o
formato ejecutable. No hay código, tests nuevos o piloto RC17 de integración.
Las ejecuciones de fixtures RC15–RC16 son regresiones actuales del código previo,
no una revisión humana nueva ni un piloto institucional.

**Incompatibilidad futura explícita:** RC15 exige edición conocida y evidencia
SINTETICA. Un documento institucional real o una política institucional sin
versionado no se admite simplemente rellenando campos o cambiando su naturaleza.
Antes de ese uso se necesita revisar el perfil, evidencia y pruebas bajo otro
encargo; no se modifica ahora. None sigue válido en el catálogo. El dato visible
1.0 de D09 no rellena ProductoCatalogo.version. La fecha civil 2024-05-30 no
se convierte en UTC, fecha de publicación del dataset o fecha de descarga.

## Auditoría de mutabilidad y recepción en memoria

Se inspeccionaron 29 clases dataclass del recorrido: solicitud/revisión/informe
RC15, receptor RC16, producto/procedencia/fuente, expediente/afirmaciones, resultado
documental, restricciones, contextos, artefacto/perfiles, identidad/recurso y
control/cotejo. Todas declaran frozen=True; algunas usan slots y otras no.
Las colecciones del recorrido producido por las funciones nativas son tuplas;
RC1 valida también las operaciones de restricciones. Eso no es una demostración
de inmutabilidad absoluta de cualquier objeto que pueda construirse manualmente.

Comprobación efectivamente ejecutada con Python de .venv, **solo en RAM**, sobre
un ProductoCatalogo inventado nuevo, sin documento ni almacenamiento:

```text
Clases dataclass frozen inspeccionadas: 29
Asignacion ordinaria rechazada: FrozenInstanceError
replace crea objeto distinto; original.version sigue None
__dict__ permite eludir frozen: no hay inmutabilidad absoluta ni custodia
Sin documentos fisicos, archivos de salida o revision humana efectuada
```

El ensayo altera deliberadamente solo el __dict__ de ese objeto inventado; no
modifica constantes, archivos, objetos operativos ni un informe recibido real.
No ejecuta pruebas de identidad humana ni autenticación institucional.

| Riesgo examinado | Evidencia del código y ensayos | Garantía / límite |
|---|---|---|
| Sustituir informe original | ComprobacionPrimerUsoM26 frozen con slots; prueba RC16 verifica aportado is informe y nuevo actual distinto | Asignación ordinaria bloqueada; replace produce otra composición, no modifica la original |
| Pérdida de restricciones/diagnósticos al recibir | _informe exige tipos nativos y tuplas directas; recálculo RC15 compara restricciones y detecta causas omitidas en su recorrido | Regresiones negativas aprobadas; no es un validador universal de todos los objetos anidados construibles |
| Correspondencia con la comprobación nueva | Snapshot esperado, revisión y finalidad contrastados; informe actual completo conservado | Otro proyecto/finalidad o revisión no se admiten como el caso esperado |
| Causas previas | diagnosticos_completos concatena aportado/propios/actual; restricciones conserva ambos conjuntos | Nueva lectura favorable no borra pendientes anteriores dentro del uso cooperativo |
| Modificación del documento | Nuevo cotejo físico detecta cambio, conserva resultado previo y actual | Garantía de esas lecturas, no continuidad futura ni integridad del CSV |
| Eludir frozen en objetos anidados | ProductoCatalogo, ProcedenciaCatalogo y otras clases tienen __dict__; también existe object.__setattr__ | Un llamador que eluda el contrato puede cambiar datos compartidos y no hay sello independiente ni aviso universal posterior |

Por tanto, la expresión histórica «referencias nativas inmutables» de RC16 debe
entenderse como **restricción de la API cooperativa**, no como custodia o una
instantánea independiente resistente a cambios deliberados. No se sobrescribe
la documentación histórica: esta auditoría precisa su alcance.

No se ha demostrado una mutación ordinaria de un contenedor admitido que genere
una recepción favorable en el recorrido nativo. El bypass demostrado requiere
eludir frozen desde el intérprete, ya excluido por RC15–RC16. No se promete
resolverlo con una copia, hash local o más flags bajo la misma autoridad. Esas
medidas podrían detectar algunos cambios accidentales, pero no aportar custodia
independiente o conservar por sí solas las causas originales ante esa manipulación.
No se identifica una corrección pequeña necesaria dentro del modelo admitido;
se limita el uso y se deja la frontera de custodia como dependencia D.

Condiciones de uso: proceso cooperativo confiable y secuencial; no modificar
objetos mediante __dict__/object.__setattr__, ni mezclar código o callbacks no
confiables. Si hay sospecha de alteración posterior o pérdida de referencias,
detener el uso y conservar el antecedente disponible; no entregar el resumen o
expediente como sustituto. Una nueva recepción exige el informe completo y nueva
comprobación, y no reconstruye una historia perdida. No usar RC16 como prueba
de custodia en procesos hostiles, concurrentes o entre sesiones.

## Verificaciones ejecutadas

Entorno comprobado: **Python 3.15.1 de .venv**, **HTTPX 0.28.1** y
**SQLite 3.53.4**. Importar sqlite3 para consultar su versión no abre una base.
PYTHONPATH y PYTHONDONTWRITEBYTECODE se configuraron solo en el proceso.

```powershell
$env:PYTHONPATH=(Join-Path $PWD 'src')+';'+(Join-Path $PWD 'tests')
$env:PYTHONDONTWRITEBYTECODE='1'
.\.venv\Scripts\python.exe -B -m unittest test_vinculo_documental_rc15 test_primer_uso_m26_rc16 -v
```

```text
Ran 43 tests in 18.746s
OK
```

**43 aprobadas: 27 RC15 + 16 RC16; 0 fallidas, 0 errores, 0 omitidas.** Salida 0.
Se ejecutaron con acceso a TEMP privado aislado, sin cambiar código o expectativas.
Las pruebas comprueban la limpieza de sus propios directorios. No se borraron
temporales ajenos ni se creó un nuevo piloto físico fuera de esas regresiones.

Cubren versión None/ajena, producto/finalidad/revisión incompatibles, documento
alterado, evidencia/procedencia insuficientes, informe ausente/expediente aislado,
restricciones/diagnósticos omitidos, bloqueos y causas previas, falta de
acreditación humana/institucional/científica y permisos, determinismo, identidad
del informe, dos proyectos con mismos bytes y barreras de proceso/importación.
Las barreras niegan socket/SQLite, lectura operativa y escritura fuera del TEMP
del ensayo; no certifican aislamiento universal del SO.

No se añaden pruebas para aumentar el contador. **2576 pruebas completas RC16
son un antecedente histórico**; no se ejecuta discover completo en RC17 porque
solo se crean tres Markdown y ningún código, dependencia o contrato cambia.
Las 43 regresiones ejecutadas ahora no renuevan la cifra completa ni se suman
como pruebas nuevas. Compatibilidad histórica sustentada en ausencia de cambios
de código/formatos, inspección y regresión acotada, no en una suite completa nueva.

```powershell
$env:PIP_DISABLE_PIP_VERSION_CHECK='1'
$env:PIP_NO_INDEX='1'
.\.venv\Scripts\python.exe -B -m pip check
```

Resultado: **No broken requirements found.**, salida 0, sin consultas externas.
Lectura/AST/compilación en memoria de **211 archivos Python**: sintaxis correcta,
sin definiciones repetidas en un mismo bloque de instrucciones inspeccionado.
Un primer arnés de inspección abortó al tratar body de una expresión AST como
lista; se corrigió únicamente el comando en memoria y se repitió con salida 0.
Ese fallo del arnés no es un error de las pruebas ni un cambio al repositorio.
Al no cambiar código o imports, RC17 no introduce dependencias o ciclos nuevos;
no se certifica que todo el grafo histórico sea acíclico.

Validación de los tres Markdown nuevos: UTF-8, EOF, ausencia de conflictos y
espacios finales, bloques cerrados, tablas consistentes y destinos de enlaces
locales existentes. La comprobación de enlaces solo accede al repositorio, no
abre los destinos institucionales ni los archivos operativos citados por documentos
históricos. El recuento de brechas confirmó 29 IDs únicos y estados 2/17/8/2.

## Archivos y estado final

Únicos archivos creados en RC17:

- [procedimiento_evidencia_edicion_rc17.md](procedimiento_evidencia_edicion_rc17.md): identidades, edición, evidencias y procedimiento futuro.
- [protocolo_revision_humana_m26_rc17.md](protocolo_revision_humana_m26_rc17.md): insumos, responsables propuestos, criterios, estados y ficha sin completar.
- Este documento: auditoría, mutabilidad, decisión, verificaciones y límites.

Ningún archivo previo se modifica. Se contrastaron SHA-256 de los cinco archivos
RC16: **todos coinciden**. La captura inicial/final de git ls-files --stage y
de diferencias preparadas/sin preparar coincide: **índice preservado**. En
particular, las huellas del receptor y pruebas RC16 permanecen:

```text
cb8af79e16ca33cc9b32d405f3c4bc16f3b6632b24e2b0ef655ee43d4ded6d34  herramientas/primer_uso_m26_rc16.py
f0f183e48e9d6285204341a884151816678b12d4c563b0c633ab1fca3dd7363e  tests/test_primer_uso_m26_rc16.py
```

Rama y HEAD se conservan. git diff --check y git diff --cached --check terminan
sin salida, código 0. No hay diferencias sin preparar en archivos registrados.
La revisión explícita de los Markdown nuevos complementa esos comandos, que no
examinan por sí solos contenido sin seguimiento. git status --short:

```text
A  docs/auditoria_arquitectonica_rc16.md
A  docs/criterios_primer_uso_m26_rc16.md
A  docs/evidencias_y_restricciones_m26_rc16.md
A  herramientas/primer_uso_m26_rc16.py
A  tests/test_primer_uso_m26_rc16.py
?? docs/auditoria_arquitectonica_rc17.md
?? docs/procedimiento_evidencia_edicion_rc17.md
?? docs/protocolo_revision_humana_m26_rc17.md
```

RC16 continúa preparado y no registrado; los tres documentos RC17 quedan sin
seguimiento. No se cambia el índice ni se afirma que el repositorio esté limpio.
main.py, .gitignore, .venv, código estable, coordinación RC3/RC7 y formatos
85-J/K, RC6, RC10 y JSON QA 0.1.0 permanecen sin cambios.

## Riesgos, pendientes y dictamen

| Hallazgo | Gravedad para el uso afectado | Tratamiento / dependencia |
|---|---|---|
| RC16 preparado pero no registrado | Media de trazabilidad | Conservar WIP e índice; registro queda para decisión del usuario, sin commit automático |
| Edición real y correspondencia editorial no acreditadas | Alta para aplicar documentación al dataset | Mantener None y pendientes; obtener evidencia legítima por procedimiento posterior autorizado |
| Persona, encargo y revisión real no acreditados | Alta para pretender uso revisado | Procedimiento y ficha propuestos; falta designación, acto y evidencia externa |
| RC15 solo sintético | Bloqueo del futuro ingreso real por ese perfil | Evolución contractual posterior explícita; no simular naturaleza ni revisión |
| Referencias en memoria alterables al eludir el contrato | Alta si se exige custodia o hay código no confiable | Limitar a proceso cooperativo secuencial; no afirmar inmutabilidad absoluta; dependencia D fuera de este incremento |
| Expediente/resumen aislado no transporta todas las causas | Alta si se presenta como aprobación | Informe RC15 y recepción RC16 completos obligatorios en el perfil; consumidor general C24 no se cambia |
| Conservación durable / identidad independiente no implementadas | Condicional al uso que las exija | No extender RC6/RC10/85-J/K/JSON QA; acordar medio y custodia antes de prometer persistencia |
| Condiciones/licencia/vigencia incompletas y fuentes formales ausentes | Pendiente del uso, alta para redistribución o ciencia | No inferir permisos ni homologación formal; conservar antecedentes y límites |

No hay cambios incompatibles ni código nuevo. Las correcciones de evidencia
necesarias antes del uso real son edición/correspondencia, revisión legítima,
responsabilidad acreditada y condiciones pertinentes, además de la decisión sobre
el perfil real y conservación exigida. No se solucionan rellenando fixtures.

M26 sigue **PENDIENTE**, con avance documental RC17 y recepción experimental
C20 → C24 de RC15–RC16. C20 → C21/C19 y los criterios originales de fundamento,
identidad/edición/período y revisión pertinentes no se declaran resueltos.
M03 (plan → conector/transporte), M16 (recomendación de readquisición → efecto)
y M32 (resultados científicos futuros → conservación/exportación) siguen
pendientes según sus definiciones originales. Las 29 brechas PNDA conservan
**2 resueltas, 17 parciales, 8 pendientes y 2 contradicciones**; no se alteran.

Prioridad propuesta para revisión: obtener evidencia legítima de edición o de
política de no versionado y designar responsable/alcance de la revisión de este
mismo producto y finalidad. Cualquier acceso real y evolución del perfil exigen
otra instrucción. No comenzar RC18, núcleos científicos, GIS operativo o IA.
La arquitectura integral sigue abierta.

**APTO CON RESTRICCIONES** como procedimiento/documentación para auditoría;
no es aptitud de un uso real, aprobación científica o autorización efectiva.
No hubo conexiones, descargas, instalaciones, migraciones, commits o push.
No se accedió a CSV PNDA real, RAW/staging/SQLite operativos o documentos
institucionales privados. Los originales no fueron abiertos: no se declara
una comprobación física nueva de su integridad. Se espera revisión del usuario.
