# RC2 — Auditoría arquitectónica del incremento de perfiles

Elaborada el **2026-11-13**, America/Lima. Base/HEAD inicial **ac9c6fd**,
rama **feature/suadc-http**. Contrato experimental **0.1.0**.
Se complementa con el [contrato](contrato_perfiles_informacion_rc2.md) y los
[criterios y escenarios](compatibilidad_estructural_rc2.md).

## Estado recuperado y alcance

Estado inicial limpio. Se ejecutaron git status, git log -5 --oneline,
git branch --show-current y comprobación de HEAD. RC1 está consolidado:

```text
ac9c6fd SPICA: contextos comunes de proyecto entrada y operacion RC1
ce4218b SPICA: auditoria de continuidad arquitectonica paso 85-M
d8742fc SUADC: custodia y evaluacion de madurez arquitectonica paso 85-L
d3372a0 SUADC: respaldo y restauracion experimental de linaje paso 85-K
d7d7b8c SUADC: persistencia experimental y recuperacion verificable de linaje
```

Se revisaron [contrato RC1](contrato_contexto_comun_rc1.md),
[integración RC1](integracion_contextos_rc1.md),
[auditoría RC1](auditoria_arquitectonica_rc1.md) y sección RC2 de la
[hoja de ruta 85-M](hoja_ruta_continuidad_arquitectonica_paso85m.md).
El alcance ratificado aquí es descripción de campos y semántica declarada con
compatibilidad conservadora para finalidad explícita, no interoperabilidad
científica completa, ontología, procesamiento o nuevos núcleos ambientales.

## Implementación y dependencia

Se crean siete archivos; no se modifica ningún archivo preexistente:

| Archivo nuevo | Responsabilidad |
|---|---|
| [modelos.py](../src/spica/interoperabilidad/perfiles/modelos.py) | Descriptores inmutables, estados de unidad, finalidad, vínculo RC1 y resultado |
| [comparador.py](../src/spica/interoperabilidad/perfiles/comparador.py) | Función pura de cotejo; delegación real de referencias al evaluador existente |
| [__init__.py](../src/spica/interoperabilidad/perfiles/__init__.py) | API explícita del subpaquete; sin modificar exports de RC1 o interoperabilidad anterior |
| [test_perfiles_informacion_rc2.py](../tests/test_perfiles_informacion_rc2.py) | 79 pruebas sintéticas, integración, adversarios y procesos sin efectos |
| [contrato_perfiles_informacion_rc2.md](contrato_perfiles_informacion_rc2.md) | Inventario de reutilización, invariantes, campos y cotas |
| [compatibilidad_estructural_rc2.md](compatibilidad_estructural_rc2.md) | Criterios por finalidad y resultados sintéticos |
| [auditoria_arquitectonica_rc2.md](auditoria_arquitectonica_rc2.md) | Evidencia de revisión, verificaciones y límites |

Dependencia nueva: perfiles → contextos RC1, interoperabilidad, catálogo y
restricciones existentes. Ninguno de esos módulos importa perfiles; no se añade
una dependencia de src hacia herramientas/tests ni un ciclo con este paquete.
No se cambia un contrato público anterior. Se conserva el evaluador original;
el resumen RC2 interpreta sus estados dentro de su finalidad y guarda el objeto
nativo completo. No hay un segundo cliente, motor QA, catálogo de estaciones,
modelo de observación, motor temporal o implementación GIS.

La matriz de inventario en el contrato documenta las ausencias concretas que
justifican descriptores de campo, estados de unidad, perfil versionado y finalidad.
Las estructuras genéricas solo contienen literales, referencias y políticas
cerradas; no cargan código desde configuración ni aplican umbrales.

## Evidencia y riesgos revisados

| Revisión | Resultado / límite |
|---|---|
| Identidad y procedencia | RC1/MD y RecursoInteroperable se conservan por referencia; se exige procedencia con evidencia para un positivo; no hay autenticación independiente |
| Versionado | Contrato 0.1.0 cerrado; perfiles/versiones admitidos expresamente; conflicto de definición para misma identidad/versión detectado en el par suministrado |
| Unidad/magnitud | Cinco estados y dimensión solo documentada; comparación exacta respaldada; ninguna equivalencia textual aproximada o conversión |
| Tiempo | Delega marcos y periodos, mantiene roles originales; ambigüedad diagnosticada; frecuencia/calendario/agregación no se infieren |
| Espacio | Delega controles espaciales; sitio con namespace fuente/producto, respaldo y sin ambigüedad; no transforma, geocodifica ni asocia estaciones |
| Restricciones | Unión RC1 conserva todas; códigos contradictorios fallan explícitamente; bloqueos de finalidad impiden positivo sin convertirse en permisos efectivos |
| Integración RC1 | EntradaPerfil no copia contexto/contenido; operación descriptiva opcional queda DECLARADA; mismos objetos y proposito verificados; cross-project sin fusión |
| QA existente | Prueba de encabezado sintético conserva literales HORA/UBIGEO, ResultadoQA y exportación JSON; no afirma tipos o semántica no respaldados |
| Equipos modestos | Máximo 64 campos por perfil y cotas locales de literales/referencias/diagnósticos; sin datos completos, librerías nuevas, benchmarks o presupuesto global prometido |
| Efectos | Proceso hijo bloquea socket, sqlite3.connect y operaciones de escritura antes de importar; construye y compara fixtures en dos órdenes de importación |

No se necesitó un cambio estructural incompatible ni se abrió una puerta que
requiriera datos institucionales. Las diferencias sin correspondencia se dejan
incompatibles para cotejo directo o pendientes de evidencia según el caso.

## Verificación ejecutada

Python de `.venv`: **3.15.1**. Para descubrir también los helpers de pruebas y los
subprocesos históricos se configuró únicamente el entorno del proceso:

```powershell
$env:PYTHONPATH = (Join-Path $PWD 'src') + ';' + (Join-Path $PWD 'tests') + ';' + $PWD.Path
.\.venv\Scripts\python.exe -B -m unittest test_perfiles_informacion_rc2 test_contextos_rc1 -v
.\.venv\Scripts\python.exe -B -m unittest test_perfiles_informacion_rc2 test_contextos_rc1 -q
```

Resultado dirigido final, ejecutado con `-q`: **139 pruebas aprobadas**,
**0 fallidas, 0 errores** en **8.295 s**: 79 de RC2 y 60 de RC1. La ejecución
dirigida previa con `-v` aprobó 137 pruebas en 9.521 s. La primera ejecución
RC2, anterior a los controles finales adicionales, aprobó 73 pruebas en 4.675 s.

La suite completa se ejecuta con el mismo intérprete y PYTHONPATH:

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -B -m pip check
git diff --check
git status --short
```

Una primera ejecución completa aprobó **2021 pruebas en 704.739 s**, sin fallos
ni errores. La revisión de cierre añadió dos casos: producto del recurso
desconocido no equivale a contradicción ni se infiere desde la variable; dimensión
documentada puede coexistir con unidad desconocida. Se repite la suite para
verificar **la versión final** y sus 79 pruebas RC2. Esta segunda ejecución
terminó con código 0 y la siguiente salida:

```text
Ran 2023 tests in 683.446s

OK
```

**2023 aprobadas, 0 fallidas, 0 errores, 0 omitidas**. Incluye las 1944 pruebas
anteriores y las 79 nuevas; no se sustituyó la suite por una colección dirigida.
No se cambió código durante esta segunda ejecución.

La suite utiliza fixtures y temporales aislados. Se ejecuta fuera del sandbox
porque los permisos Windows de algunos temporales privados de pruebas anteriores
no funcionan en él; no se modifica ACL ni se habilita ninguna operación de red.
La salida detallada final se conserva fuera del repositorio en
`%TEMP%/spica-rc2-suite-final-2b5e0cc4df724c32a23c4777c925136c.log`.
La primera pasada queda en
`%TEMP%/spica-rc2-suite-2b5e0cc4df724c32a23c4777c925136c.log`.
Son registros temporales de pruebas, no evidencia institucional ni persistencia
operativa de perfiles.

`pip check`: **No broken requirements found.** `git diff --check`: sin salida,
código 0. Se comprobaron AST/sintaxis con Python -B, ausencia de definiciones
duplicadas, importaciones del nuevo paquete, UTF-8, ausencia de espacios finales
y todos los enlaces locales de los tres documentos. Las pruebas de importación
y composición en procesos nuevos pasaron en ambos órdenes, con efectos denegados.

HEAD y rama finales permanecen **ac9c6fd / feature/suadc-http**. Ningún archivo
preexistente está modificado (`git diff --name-only HEAD` vacío); el estado final
contiene exclusivamente los siete archivos nuevos descritos arriba:

```text
?? docs/auditoria_arquitectonica_rc2.md
?? docs/compatibilidad_estructural_rc2.md
?? docs/contrato_perfiles_informacion_rc2.md
?? src/spica/interoperabilidad/perfiles/
?? tests/test_perfiles_informacion_rc2.py
```

## Pendientes y restricciones que permanecen

La [matriz 85-M](matriz_diseno_implementacion_paso85m.md) conserva las definiciones
de la [matriz original 85-F](matriz_dependencias_integracion_paso85f.md):

| Pendiente | Definición original y estado tras RC2 |
|---|---|
| M03 | C08 → C09/C02: PlanConsulta → conector/HTTP con selectores, presupuesto y autorización: **P**; comparar perfiles no ejecuta planes |
| M16 | C12 → C02/C11: decisión de readquisición → GET/ingesta autorizada: **P**; no se introduce hook ni ejecutor aprobado |
| M26 | C20 → C21/C24/C19: evidencia documental → QA/aplicabilidad/operación con vínculo explícito revisado: **P**; referencias sintéticas y Respaldo aportado no aprueban documentos institucionales ni activan ciencia |
| M32 | Resultado científico futuro → almacén/exportación general: **P**; no se cambia JSON QA, J/K ni se publica un derivado |

Las [29 brechas PNDA](brechas_reconciliadas_pnda_paso84i.md) permanecen intactas:
2 RESUELTA_CON_EVIDENCIA, 17 PARCIALMENTE_DOCUMENTADA, 8 PENDIENTE_DE_EVIDENCIA y
2 CONTRADICCIÓN_DOCUMENTADA, conforme al estado propuesto 84-I. Es un inventario
documental local: no se cierran 27 pendientes por añadir perfiles ni se amplían
sus conclusiones. El piloto INGEMMET /query sigue NO AUTORIZADO.

No se realizaron conexiones externas, solicitudes GET, descargas, instalaciones,
commits o push. No se accedió al CSV PNDA, evidencias institucionales privadas,
RAW/staging/SQLite operativos ni se ejecutaron migraciones. Las verificaciones
físicas de pruebas corresponden exclusivamente a sus fixtures temporales. No se
reabrieron almacenes operativos para sustentar esta afirmación; la garantía es
el alcance de las acciones ejecutadas y las pruebas sin efectos de la nueva capa.

Quedan pendientes autenticación/vigencia de evidencia, perfiles institucionales
aprobados, correspondencias entre variables/unidades/versiones, representación de
formatos más ricos, persistencia y unicidad global, presupuesto compuesto,
autorizaciones efectivas y aplicabilidad científica. Las cotas no garantizan RSS,
CPU o memoria total de grafos heredados. Un llamador puede aportar metadatos falsos
o escoger una finalidad insuficiente: la compatibilidad no es un permiso ni una
validación de su suficiencia científica.

## Dictamen y siguiente incremento

Dictamen: **APTO CON RESTRICCIONES**
para descriptores y cotejo documental sintético acotado por finalidad. No acredita
la arquitectura integral ni interoperabilidad científica o institucional completa.
No quedaron correcciones obligatorias conocidas dentro de este incremento tras
la revisión y las verificaciones ejecutadas; los límites anteriores permanecen.

Se recomienda someter estos contratos y finalidades a revisión. El siguiente
incremento arquitectónico propuesto es RC3, composición de una operación
estructural con política explícita de efectos y presupuesto, solo tras nueva
instrucción. No se inicia RC3 ni un núcleo científico en este bloque.
