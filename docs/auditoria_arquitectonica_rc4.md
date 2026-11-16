# RC4 — Auditoría arquitectónica de artefactos y linaje

Fecha **2026-11-15**, America/Lima. Contrato experimental **0.1.0**.
[Contrato y reutilización](contrato_artefactos_derivados_rc4.md),
[linaje e integración](modelo_linaje_artefactos_rc4.md).

## Estado recuperado y alcance

Git inicial limpio, rama feature/suadc-http, HEAD
**5b5b7d46d13d0c82a5982cdc9dcb09336547965a**. Comandos ejecutados: git status,
git log -5 --oneline, git branch --show-current, git rev-parse HEAD.

```text
5b5b7d4 SPICA: coordinacion estructural y composicion de operaciones RC3
496c740 SPICA: perfiles comunes y compatibilidad estructural RC2
ac9c6fd SPICA: contextos comunes de proyecto entrada y operacion RC1
ce4218b SPICA: auditoria de continuidad arquitectonica paso 85-M
d8742fc SUADC: custodia y evaluacion de madurez arquitectonica paso 85-L
```

RC3 está consolidado. Se recuperó RC4 de la
[hoja de ruta 85-M](hoja_ruta_continuidad_arquitectonica_paso85m.md): AM05/M32,
original/preparado/derivado y trazabilidad de resultados. El encargo actual
restringe la implementación a contratos y cotejos, excluyendo transformaciones,
serialización, publicación y persistencia. No se declara completado todo IM17/21/24
ni la arquitectura. La matriz A–E se escribió antes de introducir clases nuevas.

Se inspeccionaron modelos MD, recursos/catálogos/procedencia, contratos RAW,
contextos, perfiles, composiciones, QA científico, H/J/K y sus pruebas. No se
detectó necesidad de romper APIs previas, migrar SQLite ni leer datos reales.
La incompatibilidad de conservación J se documenta y se mantiene fuera del alcance.

## Archivos y dependencias

Se crean siete archivos; ninguno previo se modifica:

| Archivo | Responsabilidad |
|---|---|
| [artefactos/__init__.py](../src/spica/artefactos/__init__.py) | API explícita de 11 símbolos |
| [artefactos/modelos.py](../src/spica/artefactos/modelos.py) | Seis dataclasses congeladas, tres enums, cotas e interpretación de evidencia aportada |
| [artefactos/linaje.py](../src/spica/artefactos/linaje.py) | Inspección pura, pertenencia, grafo, estados y propagación |
| [test_artefactos_rc4.py](../tests/test_artefactos_rc4.py) | 52 pruebas nuevas y piloto sintético reproducible |
| [contrato_artefactos_derivados_rc4.md](contrato_artefactos_derivados_rc4.md) | Reutilización, identidades, versiones, estados y confianza |
| [modelo_linaje_artefactos_rc4.md](modelo_linaje_artefactos_rc4.md) | Relaciones N→M, integración, pilotos y persistencia pendiente |
| [auditoria_arquitectonica_rc4.md](auditoria_arquitectonica_rc4.md) | Este informe de cierre |

Dependencias: artefactos → RC1/RC2/RC3 y contratos nativos MD/QA/interoperabilidad.
No hay importaciones src→herramientas/tests ni módulos previos→artefactos. No se
duplican modelos MD, comparador RC2, cierre QA, transporte, orquestador o codec.
El algoritmo de DAG nuevo corresponde a procedencia de artefactos, distinta de
precedencia de operaciones. No se ejecuta una fase al obtener un orden.

## Revisión y pruebas adversariales

| Riesgo revisado | Comprobación y límite |
|---|---|
| Identidades | Claves MD/revisión, duplicados, mismos bytes en proyectos diferentes, SHA/tamaño contradictorios, referencias de otra revisión y pertenencia incompatible |
| Tipos/historia | Original no se convierte en preparado bajo el mismo object_id; dos revisiones del preparado permanecen distinguibles e inmutables |
| Estados | CONCLUIDA sola no acredita efecto; parcial/fallida/cancelada no producen final ficticio; evidencia insuficiente se mantiene pendiente |
| Integridad | Huella real solo de bytes sintéticos en memoria; evidencia local aportada separada; vacío legítimo admitido; inconsistencia no inventa una prueba de hash fallida |
| Grafo | N→M, productoras inexistentes/contradictorias, ausencia/redefinición RC3, autoaristas, ciclos, dependencias ausentes y versiones incompatibles |
| Restricciones | Herencia transitiva, omisión en salida, conflicto rechazado, unión sin duplicar evidencia y alcance desconocido explícito; políticas de relación/composición y QA conservadas |
| RC2 | Comparador real conserva compatibilidad/incompatibilidad, finalidad y perfiles completos; sin convertir variables, unidades o marcos |
| QA0 | Fixture temporal real mediante RC3, mismo informe/resultado/JSON antes y después; no dataset QA ficticio |
| Efectos | Importación y piloto con barrera de auditoría que niega socket/SQLite/escrituras y lectura de SPICA_DATOS; mocks niegan transporte, RAW y motor QA durante inspección |
| Recursos | Cotas de inventario/relación, tuplas tipadas, limpieza de TEMP de fixture; no reserva global ni garantías de CPU/RSS |

Primera ejecución RC4: 41 aprobadas. La revisión añadió casos relevantes hasta
52: identidad original/preparado, vacío, revisiones encadenadas, RC2 real,
preservación QA, políticas y snapshots. No se suman pasadas como pruebas distintas.
La revisión también extendió el diagnóstico de parcial a originales, no solo a
salidas, y conservó diagnósticos de antecesores en descendientes.

## Verificaciones

Entorno comprobado con .venv: Python **3.15.1**, HTTPX **0.28.1**, SQLite **3.53.4**.
Sin instalaciones. PYTHONPATH solo en el proceso PowerShell, con las tres rutas
necesarias para los subprocesos de pruebas históricas:

```powershell
$env:PYTHONPATH = (Join-Path $PWD 'src') + ';' + (Join-Path $PWD 'tests') + ';' + $PWD.Path
$env:PYTHONDONTWRITEBYTECODE = '1'
.\.venv\Scripts\python.exe -B -m unittest test_artefactos_rc4 test_contextos_rc1 test_perfiles_informacion_rc2 test_coordinacion_rc3 -q
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -B -m pip check
git diff --check
git status --short
```

Dirigidas finales: **250 aprobadas, 0 fallidas, 0 errores, en 16.606 s**:
52 RC4 + 60 RC1 + 79 RC2 + 59 RC3. La pasada dirigida anterior aprobó 243.
La suite completa se inició una vez tras cerrar código y pruebas; durante ella
solo se completa documentación y verificaciones sin modificar módulos Python.
Se ejecuta fuera del sandbox por los permisos privados Windows de TEMP de fixtures
históricas; sin cambiar ACL ni habilitar red.

Resultado de la única suite completa final, código de salida 0:

```text
Ran 2134 tests in 843.639s

OK
```

**2134 aprobadas, 0 fallidas, 0 errores y 0 omitidas**. Incluye las **2082 anteriores
y 52 nuevas**. No se atribuye una ejecución histórica a esta comprobación.
Durante la suite no se modificó código ni pruebas; solo los documentos RC4.
Registro íntegro fuera de Git:
`%TEMP%/spica-rc4-suite-3265e21d5b604868a16af17b1aaf6b01.log`.

pip check: **No broken requirements found.** Sintaxis/AST/compilación sin bytecode
y definiciones duplicadas: cuatro archivos correctos. Importación coordinación→
artefactos comprobada, además del orden artefactos→coordinación ejercitado con
barrera. Los tres documentos tienen **30 enlaces locales existentes**, UTF-8,
cercos y espacios correctos. El grafo estático no contiene ciclos RC4 ni imports
inversos desde módulos anteriores. Los temporales CSV RC3/RC4 y los directorios
.suadc-test-* del repositorio tienen conteo final **cero**, sin limpieza correctiva
manual, cambios de ACL ni residuos propios conocidos. No se crean datos operativos.

git diff --check: sin salida, código 0. git diff --name-only HEAD: vacío; no hay
cambios en archivos anteriores. HEAD y rama finales siguen **5b5b7d4 /
feature/suadc-http**. Estado final de git status --short:

```text
?? docs/auditoria_arquitectonica_rc4.md
?? docs/contrato_artefactos_derivados_rc4.md
?? docs/modelo_linaje_artefactos_rc4.md
?? src/spica/artefactos/
?? tests/test_artefactos_rc4.py
```

Son siete archivos nuevos sin registrar, tres agrupados en el paquete. No se añade
nada al índice ni se realizan commits. main.py, .gitignore, .venv, contratos previos
y documentación histórica permanecen sin cambios.

## Pendientes originales, conservación y seguridad

Se mantienen las definiciones de las matrices
[85-F](matriz_dependencias_integracion_paso85f.md) y
[85-M](matriz_diseno_implementacion_paso85m.md):

| Conexión | Estado tras RC4 |
|---|---|
| M03, C08 → C09/C02: ejecutor PlanConsulta / traducción institucional a HTTP con mecanismo, presupuesto y autorización | **P**. No se consumen planes ni ejecutan conectores |
| M16, C12 → C02/C11: decisión de readquisición → GET/ingesta mediante hook y ejecutor autorizado | **P**. No se activan efectos |
| M26, C20 → C21/C24/C19: evidencia documental → QA/aplicabilidad/operación con vínculo revisado | **P**. Respaldo aportado y fixtures no aprueban documentos institucionales |
| M32, resultados futuros → almacenamiento/exportación, derivados y linaje transversal | **P**, con avance contractual parcial: descriptor y linaje en memoria comprobados; faltan perfil persistente, exportación, recuperación y ejecución pertinente. No se cierra por renombrar JSON QA0 |

Las [29 brechas PNDA](brechas_reconciliadas_pnda_paso84i.md) no se alteran:
2 RESUELTA_CON_EVIDENCIA, 17 PARCIALMENTE_DOCUMENTADA, 8 PENDIENTE_DE_EVIDENCIA,
2 CONTRADICCIÓN_DOCUMENTADA, según estado propuesto 84-I. Ninguna fixture constituye
evidencia institucional nueva. INGEMMET /query continúa NO AUTORIZADO.

Cero conexiones externas/GET, descargas, instalaciones, migraciones, commits o
push. No se accede al CSV PNDA, RAW, staging, SQLite operativos ni datos privados.
No se vuelven a calcular hashes de originales reales para afirmar que no cambiaron;
la garantía de este incremento es ausencia de acceso operativo en sus rutas.
No se cambian JSON QA 0.1.0, índice 85001, manifiesto K o contratos estables.

Persisten confianza en DTO aportados, vigencia/autenticidad de comprobaciones,
custodia independiente, validación científica, control de efectos y recursos
globales, persistencia, seguridad concurrente y durabilidad ante apagado. RC4 es
secuencial y puro; no implementa un escritor concurrente ni un almacén durable.

## Dictamen y continuación

Dictamen tras las verificaciones: **APTO CON RESTRICCIONES** para
descriptores y linaje offline en memoria. No se acredita arquitectura terminada,
autorización institucional o núcleo científico. Las limitaciones de persistencia
y evidencia física son explícitas, sin una sustitución paralela improvisada.
No quedan correcciones obligatorias conocidas en el alcance implementado; las
capacidades excluidas siguen pendientes, sin convertirlas en garantías actuales.

Tras revisión, se recomienda diseñar un perfil versionado de conservación del
cierre RC1–RC4 y un adaptador de evidencia física de preparados/derivados, con sus
propias pruebas de recuperación. Eso requiere alcance aprobado y no se inicia
RC5 ni otro bloque automáticamente.
