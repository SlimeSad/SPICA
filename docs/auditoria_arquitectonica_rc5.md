# RC5 — Auditoría arquitectónica y cierre experimental

Fecha de cierre documental **2026-11-16**, America/Lima. Contrato **0.1.0**.
[Contrato y reutilización](materializacion_experimental_rc5.md),
[verificación y piloto](verificacion_fisica_artefactos_rc5.md).

## Recuperación y alcance

Se ejecutaron git status, git log -5 --oneline, git branch --show-current y
git rev-parse HEAD. Inicio limpio, feature/suadc-http, HEAD
**1024158ee5ec1b8229c043b88b534c573580fdf6**. RC4 está consolidado:

```text
1024158 SPICA: contratos y linaje de artefactos RC4
5b5b7d4 SPICA: coordinacion estructural y composicion de operaciones RC3
496c740 SPICA: perfiles comunes y compatibilidad estructural RC2
ac9c6fd SPICA: contextos comunes de proyecto entrada y operacion RC1
ce4218b SPICA: auditoria de continuidad arquitectonica paso 85-M
```

Se revisaron RC1–RC4, mecanismos físicos RAW, trazabilidad H, codec/índice J y
respaldo K con sus pruebas; se documentó la reutilización antes de las clases
nuevas. La [auditoría 85-M](auditoria_continuidad_arquitectonica_paso85m.md) y su
[hoja de ruta](hoja_ruta_continuidad_arquitectonica_paso85m.md) sitúan RC5 en
conservación/portabilidad/custodia. El encargo actual autoriza solo materialización
y verificación sintéticas TEMP. **No se cierra toda esa etapa**, AM06/AM09 ni L01–L05.

No se detectó necesidad de romper contratos estables, acceder a datos reales,
migrar SQLite o introducir otro almacén RAW. La nueva evidencia física se agrega
en informes externos: la semántica de RC4 sigue íntegra.

## Componentes y compatibilidad

Se crean seis archivos; ninguno anterior se modifica:

| Archivo | Responsabilidad |
|---|---|
| [materializacion.py](../src/spica/artefactos/materializacion.py) | Solicitud/referencia/informes tipados, estados técnicos, integración RC4, publicación y lector público |
| [_archivos_rc5.py](../src/spica/artefactos/_archivos_rc5.py) | Adaptador de _segura/_huella/firma RAW, raíz exclusiva, relectura y limpieza no recursiva |
| [test_materializacion_rc5.py](../tests/test_materializacion_rc5.py) | 56 pruebas adversariales y fixtures sintéticas; verificador en segundo Python |
| [materializacion_experimental_rc5.md](materializacion_experimental_rc5.md) | Contratos, reutilización, procedimiento y seguridad |
| [verificacion_fisica_artefactos_rc5.md](verificacion_fisica_artefactos_rc5.md) | Evidencia real del piloto y límites de los fallos simulados |
| [auditoria_arquitectonica_rc5.md](auditoria_arquitectonica_rc5.md) | Este informe |

Dependencia: RC5 → contratos RC4 → RC1/RC2/RC3; adaptador RC5 → primitivas RAW.
No hay importación src→herramientas/tests ni modificación de dependencias anteriores.
No se carga código de métodos desde documentos ni se ejecuta un productor.
La dependencia privada RAW es intencional, localizada y cubierta por pruebas;
un cambio posterior de esas funciones requerirá comprobar este adaptador.

La huella de recepción y las relecturas delegan en la misma _huella RAW, sin otro
algoritmo de integridad. La publicación adapta os.link porque las operaciones
existentes incorporan catálogo RAW, HTTP o codec G/H, incompatibles con este alcance.
No se instancian esos subsistemas para simular un almacenamiento de derivados.

## Integración RC1–RC4

| Contrato | Preservación comprobada |
|---|---|
| RC1 | Proyecto, objeto, entrada, estados/propósito/parámetros de operación y versiones; ninguna transición implícita |
| RC2 | Perfil/versiones, variables/unidades, marcos e incertidumbres dentro de las instantáneas conservadas; sin conversión o validación científica |
| RC3 | Referencias y dependencias declaradas conservadas; publicar bytes no ejecuta ni concluye la operación productora |
| RC4 | Artefacto/revisión/contenido, linaje e informes íntegros; políticas locales y heredadas siguen disponibles en informes físicos |

La conclusión técnica RC5 es del componente físico, no del método declarado. El
piloto mantiene la salida/operación PARCIAL y revisión científica NO_EVALUADA.
Un bloqueo técnico aplicable detiene escritura/relectura; otros bloqueos permanecen
sin reinterpretarse como permisos. Alcances desconocidos RC4 no se borran ni elevan
a aprobación por conseguir un SHA coincidente.

## Verificaciones y correcciones del incremento

Entorno comprobado con .venv: Python **3.15.1**, HTTPX **0.28.1**, SQLite **3.53.4**.
Sin instalaciones. Rutas de importación solo en el proceso, con -B y bytecode
deshabilitado para los subprocesos de pruebas históricas:

```powershell
$env:PYTHONPATH = (Join-Path $PWD 'src') + ';' + (Join-Path $PWD 'tests') + ';' + $PWD.Path
$env:PYTHONDONTWRITEBYTECODE = '1'
.\.venv\Scripts\python.exe -B -m unittest test_materializacion_rc5 test_artefactos_rc4 test_contextos_rc1 test_perfiles_informacion_rc2 test_coordinacion_rc3 -q
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -B -m pip check
git diff --check
git status --short
```

Primera pasada RC5: 46 pruebas, **45 aprobadas y un fallo**, cero errores. La
barrera del segundo proceso detectó que gettempdir() intentaba crear una sonda al
resolver TEMP. Se corrigió el componente lector para usar la base ambiental
explícita validada, sin relajar la barrera. Fue un defecto de la ruta nueva,
no una regresión previa ni un fallo de hardware.

La revisión añadió coherencia con evidencia aportada, referencia tras cierre,
bloqueo del lector, lectura fallida/cancelada, escritor cooperativo, corrupción
del temporal y linaje contradictorio. Pasaron 304 dirigidas. El cierre añadió
cancelación posterior al enlace y privacidad en errores de creación/limpieza.

Dirigidas finales: **306 aprobadas, 0 fallidas, 0 errores, en 27.909 s**:
56 RC5 + 52 RC4 + 60 RC1 + 79 RC2 + 59 RC3. No se suman pasadas como pruebas distintas.
AST/compilación sin bytecode, definiciones duplicadas y espacios: tres archivos
correctos. Se inspeccionan también directamente los archivos sin seguimiento.

La suite completa final se inició una vez tras cerrar código/pruebas; durante
ella solo se completan documentos y se ejecuta el piloto separado. Se usa el
intérprete fuera del sandbox por los permisos privados Windows de TEMP, sin
cambiar ACL o habilitar conexiones. Resultado de la **única suite completa final**,
código de salida 0:

```text
Ran 2190 tests in 863.405s

OK
```

**2190 aprobadas, 0 fallidas, 0 errores y 0 omitidas**: las **2134 anteriores y
56 nuevas**. No se atribuye una suite histórica a una ejecución nueva. Desde el
inicio de esta suite no se modificó código o pruebas, solo estos documentos;
el piloto separado utilizó exactamente ese código ya cerrado.
Registro fuera de Git:
`%TEMP%/spica-rc5-suite-458a1b455ee14d469b220b189ac73f85.log`.

pip check: **No broken requirements found.** Los tres documentos tienen
**25 enlaces locales existentes**, UTF-8, cercos y espacios correctos. La revisión
estática no detectó ciclos que involucren RC5 ni imports inversos desde módulos
anteriores. Comprobaciones finales: **cero raíces TEMP RC5**, cero temporales CSV
de fixtures RC3/RC4/RC5 y cero directorios .suadc-test-* en el repositorio. No hizo
falta limpieza correctiva manual ni borrado recursivo.

git diff --check: sin salida, código 0. git diff --name-only HEAD: vacío, sin
modificaciones de archivos anteriores. Rama/HEAD finales permanecen
**feature/suadc-http / 1024158ee5ec1b8229c043b88b534c573580fdf6**.
Estado final de git status --short:

```text
?? docs/auditoria_arquitectonica_rc5.md
?? docs/materializacion_experimental_rc5.md
?? docs/verificacion_fisica_artefactos_rc5.md
?? src/spica/artefactos/_archivos_rc5.py
?? src/spica/artefactos/materializacion.py
?? tests/test_materializacion_rc5.py
```

Son seis archivos nuevos sin registrar. No se añade nada al índice ni se realiza
commit/push. main.py, .gitignore, .venv y los contratos/documentos anteriores
permanecen intactos.

## Garantías y límites físicos

Comprobado: recepción limitada por bloques, SHA incremental, relecturas físicas
antes/después de enlace, rechazo de sobrescritura, corrupción/ausencia/tamaño,
vinculación de identidad, cierres de recursos, cancelación cooperativa, políticas
heredadas, disposición no recursiva de archivos propios y lector desde otro Python.
Los hashes físicos, fechas UTC y variantes están en el informe del piloto.

No demostrado: pérdida eléctrica, atomicidad global, durabilidad, autenticidad,
referencia independiente, respaldo/custodia independientes, resistencia absoluta
TOCTOU, escritor hostil o cuotas globales. Solo un escritor cooperativo por raíz;
un marcador abandonado exige revisión, sin reanudación/reparación automática.
Las pruebas de OSError/escritura corta y reparse son inyecciones controladas;
el enlace duro sí se ejercita físicamente con nuestra fixture.

El directorio privado es propiedad del entorno experimental y su limpieza retira
sus propias fixtures al cerrar. No se aplica esa política a originales RAW ni
raíces históricas. Ante contenido ajeno se preserva el entorno y se requiere revisión.

## Conservación J/K y conexiones originales pendientes

El codec J de lista cerrada no admite los nuevos contratos RC5/RC4; el índice
85001 y el manifiesto K esperan roles/estructuras exactos. Permanecen intactos,
igual que JSON QA 0.1.0 y SQLite operativo. Ninguna referencia física RC5 es un
manifiesto de conservación o una generación restaurable.

Una evolución posterior requiere perfil/codec versionados, cierre de referencias
RC1–RC5, esquema aprobado si fuese necesario, publicación y recuperación ante
interrupciones, lector compatible y política de custodia. Debe mantener el lector
anterior y evitar migración implícita. Esa evolución no se implementa ni simula.

Definiciones de las matrices [85-F](matriz_dependencias_integracion_paso85f.md)
y [85-M](matriz_diseno_implementacion_paso85m.md):

| Conexión | Estado tras RC5 |
|---|---|
| M03, C08 → C09/C02: ejecutor PlanConsulta / traducción institucional de selectores a HTTP con mecanismo, presupuesto y permiso | **P**; no hay ejecución de planes ni HTTP |
| M16, C12 → C02/C11: decisión de readquisición → GET/ingesta mediante hook y ejecutor autorizado | **P**; sin efectos institucionales |
| M26, C20 → C21/C24/C19: evidencia documental → QA/aplicabilidad/operación mediante vínculo revisado | **P**; bytes sintéticos íntegros no aprueban documentos científicos |
| M32, resultados futuros → almacenamiento/exportación, derivados y linaje transversal | **P**, avance parcial de contrato RC4 y materialización física TEMP RC5. Faltan conservación/exportación versionadas y ejecución pertinente; no se cierra la conexión original |

Las [29 brechas PNDA](brechas_reconciliadas_pnda_paso84i.md) siguen sin cambios:
2 RESUELTA_CON_EVIDENCIA, 17 PARCIALMENTE_DOCUMENTADA, 8 PENDIENTE_DE_EVIDENCIA y
2 CONTRADICCIÓN_DOCUMENTADA. No se modifica evidencia institucional ni se abre
el CSV. INGEMMET /query permanece NO AUTORIZADO.

Cero conexiones externas, GET externos, descargas o instalaciones. Sin acceso a
RAW, staging o SQLite operativos, datos institucionales privados, migraciones,
commits o push. No se vuelve a medir un original operativo para afirmar su
integridad; se mantiene ausencia de acceso operativo. Todo cuerpo nuevo es ficticio.

## Dictamen y siguiente incremento

Dictamen tras las verificaciones: **APTO CON RESTRICCIONES** para
publicación/verificación sintética TEMP. No se habilita adquisición institucional,
ciencia, custodia o almacenamiento durable ni se declara terminada la arquitectura.
No quedan correcciones obligatorias conocidas en este alcance tras el cierre;
los límites de entorno confiable, concurrencia, evidencia y conservación siguen
siendo restricciones explícitas, sin presentarlos como capacidades implementadas.

Tras auditoría se recomienda definir un perfil versionado del cierre de evidencias
RC1–RC5 para conservación y recuperación, reutilizando J/K donde sea compatible,
antes de cualquier destino operativo. No se inicia RC6 u otro bloque automáticamente.
