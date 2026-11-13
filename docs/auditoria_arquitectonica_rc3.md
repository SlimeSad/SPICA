# RC3 — Auditoría de coordinación estructural

Fecha **2026-11-13**, America/Lima. Base/HEAD inicial **496c740**,
feature/suadc-http. Versión **0.1.0**.
[Contrato](contrato_composicion_operaciones_rc3.md) e
[integración](integracion_coordinacion_rc3.md).

## Recuperación y responsabilidad seleccionada

Se ejecutaron git status, git log -5 --oneline, git branch --show-current y
git rev-parse HEAD. Árbol inicial limpio; RC2 está consolidado. Historial inicial:

```text
496c740 SPICA: perfiles comunes y compatibilidad estructural RC2
ac9c6fd SPICA: contextos comunes de proyecto entrada y operacion RC1
ce4218b SPICA: auditoria de continuidad arquitectonica paso 85-M
d8742fc SUADC: custodia y evaluacion de madurez arquitectonica paso 85-L
d3372a0 SUADC: respaldo y restauracion experimental de linaje paso 85-K
```

Se revisaron los tres documentos RC2, los de RC1, los contratos/consumidores de
contextos, perfiles, planificador, QA0 y las fronteras de ejecución/trazabilidad
85-G/H. La [sección RC3 de 85-M](hoja_ruta_continuidad_arquitectonica_paso85m.md)
incluye futura coordinación de efectos; el encargo actual selecciona su parte
**declarativa**, sin executor, HTTP, persistencia ni permiso. No se declara completo
el flujo autorización→efecto ni toda AM03/AM07/AM10.

La matriz de reutilización del contrato explica por qué PlanConsulta no sustituye
un conjunto de ContextoOperacion y por qué importar 85-G/H desde src sería una
dependencia equivocada. No se detectó una puerta que exigiera modificar contratos
estables, datos institucionales, migraciones o un nuevo sistema de ejecución.

## Archivos y dependencias

Se crean nueve archivos y no se modifica ninguno preexistente:

| Archivo | Función |
|---|---|
| [coordinacion/__init__.py](../src/spica/coordinacion/__init__.py) | API explícita experimental |
| [coordinacion/modelos.py](../src/spica/coordinacion/modelos.py) | Contratos de composición, límites, dependencias y diagnósticos; referencias a RC1/RC2 |
| [coordinacion/inspeccion.py](../src/spica/coordinacion/inspeccion.py) | Grafo, relaciones, cotejos, propagación y habilitación declarativa; no despacha tareas |
| [coordinacion/_qa.py](../src/spica/coordinacion/_qa.py) | Adaptación de precondiciones RC1 y coherencia de InformeQA/vínculos, sin ejecutar reglas |
| [coordinacion/_presupuesto.py](../src/spica/coordinacion/_presupuesto.py) | Recorrido textual acotado de descriptores, sin serializar o reservar recursos |
| [test_coordinacion_rc3.py](../tests/test_coordinacion_rc3.py) | 59 pruebas RC3, componentes reales con fixtures y barreras sin efectos |
| [contrato_composicion_operaciones_rc3.md](contrato_composicion_operaciones_rc3.md) | Responsabilidades, contratos y límites |
| [integracion_coordinacion_rc3.md](integracion_coordinacion_rc3.md) | Escenarios y evidencia realmente obtenida |
| [auditoria_arquitectonica_rc3.md](auditoria_arquitectonica_rc3.md) | Verificaciones, riesgos y pendientes |

Dependencia: coordinación → contextos, perfiles/interoperabilidad y contratos QA
existentes. No hay importaciones src→herramientas/tests ni aristas desde esos
módulos previos hacia coordinación. Se prueban dos órdenes reales de importación.
No se duplica un motor, planificador, modelo MD o formato de resultados científicos.
Los helpers de pruebas se reutilizan desde tests, nunca desde src.

## Revisión de corrección y confianza

| Aspecto | Evidencia / límite |
|---|---|
| Grafo | Vacío, identidad/arista duplicada, extremos inexistentes, autoarista, ciclo, profundidad y orden por capas probados |
| Pertenencia | validar_relaciones real; entradas canónicas compartidas por referencia; inventario superior a 256 diagnosticado antes del cotejo RC1 |
| RC2 | Comparador real, resultado completo retenido, finalidad/entradas comprobadas; incompatible y pendiente no habilitan |
| Estados | RC1 conservado; no transiciones automáticas; una conclusión declarada sola no satisface una dependencia |
| QA previo | Informe, contadores, reglas, procedencia, límites, EOF y vínculos contrastados; no se fabrica un historial ni se autentica al llamador |
| Presupuestos | Cotas de objetos/texto y sumas de cuotas QA comparables; UTF-8 por ocurrencia probado; sin reservas/consumo global/RSS prometidos |
| Restricciones | Unión por código, origen conservado, propagación transitiva, conflicto rechazado y aplicabilidad desconocida pendiente |
| Cancelación | Event de inspección; preserva referencias previas, diagnósticos y resultados RC2 ya obtenidos; no cancela un servicio o tarea externa |
| Efectos | Se niegan motor/planificador/transporte durante cotejo y se auditan importaciones sin escrituras/red/SQLite |
| Piloto | QA0 real sobre fixture temporal; piloto adicional de 214 bytes con SHA físico coincidente, dos proyectos separados y tres estados estructurales |

Durante la primera prueba dirigida se detectó un AttributeError del fabricante
de entrada inválida (antes de llegar al constructor) y PermissionError del
sandbox al escribir/limpiar un temporal privado. Se corrigió el fabricante y se
retiró únicamente ese directorio vacío, sin ACL ni recursión. No se modificó código
anterior para ocultar problemas del entorno.

Las 51 pruebas iniciales pasaron fuera del sandbox. La revisión añadió controles
de perfil QA admitido/desconocido, regla inexistente, inventario RC1, UTF-8, cierre
parcial etiquetado como completo y cancelación con evidencia previa. La preparación
QA usa constantes/precondiciones del contrato RC1; no se crea una fila para
probar exportabilidad ni se reimplementan reglas QA. No se atribuye validez física
a los hashes declarados de fabricantes históricos de pruebas.

## Verificaciones

Se usa exclusivamente Python **3.15.1 de .venv**, con -B. PYTHONPATH solo se modifica
en el proceso para descubrir src y helpers/subprocesos históricos de tests:

```powershell
$env:PYTHONPATH = (Join-Path $PWD 'src') + ';' + (Join-Path $PWD 'tests') + ';' + $PWD.Path
.\.venv\Scripts\python.exe -B -m unittest test_coordinacion_rc3 test_contextos_rc1 test_perfiles_informacion_rc2 -q
```

Dirigidas finales: **198 aprobadas, 0 fallidas, 0 errores, en 14.170 s**:
59 RC3 + 60 RC1 + 79 RC2. La ejecución anterior de esos tres módulos aprobó
194 pruebas; no se suman entre pasadas como pruebas distintas.

La suite completa final se ejecuta **una vez** después de cerrar el código:

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -B -m pip check
git diff --check
git status --short
```

Resultado final, código de salida 0:

```text
Ran 2082 tests in 700.936s

OK
```

**2082 aprobadas, 0 fallidas, 0 errores y 0 omitidas**. Incluye las **2023 pruebas
anteriores y 59 nuevas**. Se ejecutó la suite completa una vez en RC3, después
del cierre de código; durante ella solo se escribieron los documentos y se
realizó el ensayo sintético puntual descrito en integración. No se modificó
código durante esta ejecución ni se sustituyó por la colección dirigida.

Se ejecuta fuera del sandbox para admitir permisos privados Windows de temporales
de las pruebas previas y del CSV sintético. No se cambian ACL ni se habilita red.
La salida íntegra queda fuera de Git en
`%TEMP%/spica-rc3-suite-905936fe89d34e248db8997ab0f5e86a.log`.
También se activa PYTHONDONTWRITEBYTECODE=1 en esa ejecución para sus subprocesos.

`pip check`: **No broken requirements found.** `git diff --check`: sin salida,
código 0. AST/compilación sin bytecode, definiciones duplicadas, importaciones,
UTF-8, espacios finales y **29 enlaces locales** de los tres documentos correctos.
Los temporales CSV propios se liberan y se comprueba su ausencia; el directorio
vacío de la primera pasada fallida también fue retirado de forma controlada.

HEAD y rama finales permanecen **496c740 / feature/suadc-http**. El diff de archivos
preexistentes está vacío. Estado final de git status --short, con los cinco
archivos del paquete agrupados en una carpeta:

```text
?? docs/auditoria_arquitectonica_rc3.md
?? docs/contrato_composicion_operaciones_rc3.md
?? docs/integracion_coordinacion_rc3.md
?? src/spica/coordinacion/
?? tests/test_coordinacion_rc3.py
```

Son nueve archivos nuevos sin registrar; no se añade nada al índice ni se realiza
un commit. Los contratos RC1/RC2, QA0, JSON QA y módulos operativos permanecen intactos.

## Pendientes originales y datos operativos

Se conservan las definiciones de la
[matriz 85-F](matriz_dependencias_integracion_paso85f.md) y
[matriz 85-M](matriz_diseno_implementacion_paso85m.md):

| Conexión | Estado tras RC3 |
|---|---|
| M03: C08 → C09/C02, ejecutor PlanConsulta / traducción institucional a HTTP con mecanismo, presupuesto y permiso | **P**. El grafo de ContextoOperacion no consume planes ni ejecuta conectores |
| M16: C12 → C02/C11, hook decisión de readquisición → GET/ingesta autorizada | **P**. Una recomendación o habilitación declarativa no activa efectos |
| M26: C20 → C21/C24/C19, evidencia documental → QA/aplicabilidad/operación con vínculo pertinente revisado | **P**. El cierre QA sintético y los respaldos RC2 no aprueban evidencia institucional |
| M32: resultados futuros → almacenamiento/exportación científica y linaje transversal | **P**. No hay derivado nuevo, formato general, persistencia o cambio de JSON QA0 |

Las [29 brechas PNDA](brechas_reconciliadas_pnda_paso84i.md) permanecen intactas:
2 RESUELTA_CON_EVIDENCIA, 17 PARCIALMENTE_DOCUMENTADA, 8 PENDIENTE_DE_EVIDENCIA y
2 CONTRADICCIÓN_DOCUMENTADA según estado propuesto 84-I. No se cierran pendientes
por contar conexiones declarativas. INGEMMET /query sigue NO AUTORIZADO.

Cero conexiones/GET externos, descargas o instalaciones. No se accedió al CSV
PNDA, RAW, staging, SQLite operativos o evidencia institucional privada; no hubo
migraciones, commits o push. Las comprobaciones físicas nuevas solo corresponden
a la fixture sintética de TEMP. No se abrieron los originales para repetir hashes
ni se usa Git como prueba física de integridad del almacén.

## Riesgos y dictamen

Persisten autenticación de evidencia y permisos efectivos, reserva/medición global
de recursos, efectos externos, persistencia, trazas de ejecución general y
adaptadores de cierre de componentes diferentes de QA0. Un llamador puede declarar
un alcance insuficiente o falsificar DTO coherentes: el cotejo no es una frontera
contra Python hostil. Los topes son locales; no garantizan CPU/RSS/disco ni éxito
futuro de lectura, exportación o ejecución.

Dictamen: **APTO CON RESTRICCIONES**
para coordinación estructural offline de inventarios acotados. No se implementa
un orquestador general ni se declara terminada la arquitectura.
No quedan correcciones obligatorias conocidas en el alcance implementado tras
las verificaciones ejecutadas; se mantienen las limitaciones de confianza,
evidencia, presupuestos y efectos documentadas arriba.

Siguiente incremento propuesto: revisar RC3 y, si se ratifica abrir preparados o
derivados, diseñar el contrato de artefacto/linaje de RC4 reutilizando estos
contextos y resultados. Antes de cualquier efecto operativo sigue haciendo falta
política y autorización específicas. No se inicia RC4 ni ciencia automáticamente.
