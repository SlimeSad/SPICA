# RC10 — Auditoría de conservación y recuperación de evidencias

Elaboración: 2026-11-20, America/Lima. Alcance experimental offline.
[Contrato](contrato_conservacion_evidencias_rc10.md),
[piloto y recuperación](recuperacion_evidencias_tecnicas_rc10.md).

## Estado inicial y prioridad

Rama `feature/suadc-http`, HEAD
`424e585f9f02f5f89febbe9283ee532d86e284e5`; árbol e índice limpios.
RC9 está registrado: `424e585 SPICA: admision controlada de evidencias de exportacion RC9`.
Antecesores: RC8 `246bbec`, RC7 `c1b224e`, RC6 `367e95f`, RC5 `27a9224`.
Se ejecutaron git status, rama, HEAD y log -5 antes de modificar archivos.

Entorno comprobado en esta sesión con `.venv -B`: Python 3.15.1, HTTPX 0.28.1,
SQLite 3.53.4. No se instala ni se abre un catálogo para consultar versiones.

Se revisaron los tres documentos RC9 y su recuperación tras el bloqueo, los
documentos RC8, contratos y código RC3–RC7, codec/manifiestos 85-J/K, hoja 85-M
y definiciones originales de las conexiones 85-F. RC9 recomienda **primero**
definir la confianza histórica y el expediente mínimo después de reiniciar;
solo después evaluar admisión no QA por dependencia. RC10 coincide con esa
prioridad, sin anticipar la modificación de RC3/RC7.

## Auditoría de reutilización previa al código

| Necesidad | Estado previo | Decisión RC10 |
|---|---|---|
| Identidad de proyecto, entradas, operaciones | Cubierta por RC1 | Conservar contratos completos, sin identificar por ruta/hash |
| Artefactos/revisiones/contenido | Cubierta por RC4 | Portador documental independiente y referencias originales dentro del expediente |
| Linaje/producción/restricciones | Cubierta para el perfil RC4/RC6 | Reutilizar informes e inspectores, preservar fuentes y orígenes |
| Física/publicación exclusiva | Cubierta por RC5 | Materializar el expediente, releer y comprobar SHA; no otro escritor |
| Generaciones/manifiestos/control | Cubierta por RC6 | Usar su formato actual para los bytes del portador |
| Codec RC6 para RC8/RC9 | Parcial: rechaza esos tipos | Proyección explícita RC10 sobre sus primitivas de datos acotados, sin cambiar registro/formato RC6 |
| Resultado QA/vínculo/consumo nativos | Adaptable a perfil cerrado | Registrar tipos concretos en RC10; no importar codec de herramientas desde src |
| Capturas/cierres/admisión históricos | Pendiente en RC9 | Conservar campos públicos completos y hechos históricos separados |
| Testigos privados después del reinicio | Fuera del alcance de conservación | Excluir; nunca reconstruir como prueba local |
| SHA/traslado/lector independiente | Cubierta por RC6 | Reutilizar recuperar_generacion y copiar_de |
| Versiones desconocidas, rutas y límites | Adaptable | Validación RC6 más envolvente/perfil RC10 y controles de asociación |
| Cierres no QA admitidos por RC3/RC7 | Pendiente | Sin cambios ni habilitación implícita |
| Autenticidad/custodia/permisos/ciencia | Fuera del alcance | No acreditados/concedidos |

Se comprobó en memoria que `codec_rc6.codificar` sobre un informe RC9 nativo
rechaza `tipo_fuera_del_perfil_rc6`. El codec 85-J está igualmente cerrado y
su lector exige InformeEjecucion85G; el manifiesto 85-K inventaría sus roles y
esquema 85001 específicos. No sirven como contenedor genérico de RC8/RC9.
No se los amplía ni se crea otra base.

Solución compatible: un artefacto RC4 cuyo **contenido** tiene perfil
`rc10.evidencias.0.1.0`, conservado íntegramente por RC6. No se necesita una
refactorización del almacenamiento ni cambiar contratos públicos anteriores.
Los únicos adaptadores nuevos son el perfil de datos y el vínculo específico
del expediente con el portador. No hay otro inspector de dependencias.

## Componentes y garantías

Se crean seis archivos; no se modifica ningún archivo registrado:

| Archivo | Función |
|---|---|
| [conservacion_evidencias.py](../src/spica/artefactos/conservacion_evidencias.py) | Captura, expediente/hechos/control/informe, coherencia, vínculo y delegación RC5/RC6 |
| [_codec_evidencias_rc10.py](../src/spica/artefactos/_codec_evidencias_rc10.py) | Perfil cerrado y versionado sobre primitivas RC6; referencias compartidas y contenido literal deduplicado |
| [test_conservacion_evidencias_rc10.py](../tests/test_conservacion_evidencias_rc10.py) | 29 pruebas nuevas con contratos reales y fixtures sintéticas |
| contrato_conservacion_evidencias_rc10.md | Formatos, API, identidades, versiones, restricciones y seguridad |
| recuperacion_evidencias_tecnicas_rc10.md | Pilotos, procesos, traslado y límites de interpretación |
| auditoria_arquitectonica_rc10.md | Este informe y sus verificaciones |

Los informes RC8/RC9 conservan solicitudes, argumentos nativos, resultados,
productor/consumidor/versiones, identidad de proyecto/operación/entrada/artefacto/
revisión/contenido, diagnósticos, restricciones, linaje y comprobaciones físicas
aportadas. El SHA no sustituye las identidades. RC10 no inventa fecha de ejecución
RC8/RC9 ni institución: registra una fecha nueva de captura del expediente.

Se distinguen observación del proceso, datos históricos, integridad física actual
del portador, contenido JSON incorporado y referencias externas. Los testigos
privados quedan ausentes y las propiedades locales de los DTO no se promueven.
El informe de consumo actual está separado de la admisión histórica y no
autoriza reutilizarla. Los resultados bloqueados/pendientes/incompatibles y los
estados parciales/fallidos/cancelados permanecen negativos.

La coherencia de los metadatos físicos históricos se coteja sin abrir sus rutas.
La lectura física actual y los hashes de la generación se obtienen mediante
RC6, sin implementarlos por segunda vez. Se recompone la generación al final
para detectar cambios observados en la ventana. No elimina el riesgo TOCTOU.

## Piloto y pruebas

Las pruebas nuevas usan el exportador RC8, consumidor RC9 y evaluador puntual
reales. La variante física obtiene materialización y relectura RC5 reales.
El ensayo entre procesos termina el productor A antes de iniciar al lector B;
usa dos proyectos independientes, copia cada generación mediante RC6 a otra
raíz, retira la fuente propia y exige el mismo resultado desde el destino.
B niega red, SQLite, escrituras, lectura operativa, despacho del productor y
apertura de referencias físicas históricas. No utiliza factories de tests.

La cobertura adversarial se detalla en el documento de recuperación: versiones,
clases/campos/tipos/constantes, duplicados/no finitos/profundidad/tamaño,
relaciones e identidades, ausencia de evidencia, rechazo, bloqueos/restricciones,
estados terminales y parcial real, física histórica, corrupción/pérdida/hash,
rutas, control, no sobrescritura, cancelación y ausencia de promoción RC3/RC7.

Incidencias intermedias resueltas durante el desarrollo: fixtures con argumentos
de RestriccionQA invertidos y declaraciones/perfil RC2 incorrectos; un envío
inicial del expediente en un solo bloque excedía el tamaño de bloque RC5; una
aserción comparaba una etiqueta inventada en lugar del enum EstadoLocal nativo.
Se corrigieron exclusivamente el adaptador nuevo y sus fixtures. No se atribuyen
esas ejecuciones intermedias a una suite aprobada.

El primer proceso piloto fallido dejó una raíz propia vacía
`spica-rc6-c5152b92b7e94699b45bfb0d31e3fecc`. Se comprobó su ubicación,
identidad y ausencia de nombres, y se dispuso con la primitiva nativa sin
recursión. El piloto incorpora limpieza de sus raíces propias ante excepción.
No se borró ningún directorio ajeno, original o recurso operativo.

## Comandos y resultados de verificación

```powershell
$env:PYTHONPATH=(Join-Path $PWD 'src')+';'+(Join-Path $PWD 'tests')
$env:PYTHONDONTWRITEBYTECODE='1'
.\.venv\Scripts\python.exe -B -m unittest test_conservacion_evidencias_rc10 test_materializacion_rc5 test_conservacion_rc6 test_integracion_artefactos_rc7 test_cierre_exportacion_rc8 test_admision_exportacion_rc9 -v
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -B -m pip check
git diff --check
git status --short
```

Dirigidas finales realmente ejecutadas: **268 aprobadas, 0 fallidas, 0 errores
y 0 omitidas**, `Ran 268 tests in 180.682s`, `OK`. Incluyen las 29 nuevas RC10
y 239 de RC5–RC9. No se suman subtests o repeticiones al total.

Sintaxis/compilación en memoria de los tres Python nuevos, sin definiciones
duplicadas; importación explícita de ambos módulos correcta. Grafo AST: 80
dependencias alcanzables desde el perfil y 81 desde el adaptador; sin ciclos que
incluyan RC10 ni importaciones desde módulos históricos hacia RC10. El perfil
solo es importado por el adaptador nuevo. No se afirma aciclicidad absoluta de
todo módulo histórico a partir de ese control acotado.

Los seis archivos nuevos superaron lectura UTF-8, EOF, espacios finales,
marcadores de conflicto, cercas Markdown y sus **16 enlaces locales** válidos.
Se examinaron directamente porque git diff --check no cubre archivos sin
seguimiento. Git diff HEAD y diff cached permanecieron vacíos.

Código y pruebas congelados para la suite completa final:

| Archivo | SHA-256 antes de la suite |
|---|---|
| _codec_evidencias_rc10.py | ad017a706848e839ee322db24ecbeb212824ccd000133297f230e4f0ea131662 |
| conservacion_evidencias.py | 831dce78ea59c9c48aeebed25e92fe665eb8f7f4b65e7c214fc0690398350367 |
| test_conservacion_evidencias_rc10.py | c73acccfbeae2ed338d02812adc0479bf8ae494677437f9eba914cbeab2c0e63 |

La suite completa nueva terminó sobre esos archivos. Registro verbose íntegro
fuera de Git:
`%TEMP%/spica-rc10-suite-final-f8842f3802a1427e986243f5fa7c3437.log`.

```text
Ran 2402 tests in 978.094s

OK
```

**2402 aprobadas, 0 fallidas, 0 errores y 0 omitidas**. Incluye las 2373
anteriores y las 29 nuevas; no se suman las dirigidas al total. Se leyó y
comprobó el registro completo, sin ResourceWarning ni fallos. El resultado
corresponde a esta ejecución nueva, no a la suite histórica RC9.

Después de terminarla, `.venv -B -m pip check` devolvió exactamente
`No broken requirements found.`, código 0. git diff --check, diff HEAD y diff
cached: código 0, sin salida. Se volvieron a calcular los tres SHA de la tabla:
idénticos a los anteriores a la suite; no cambió código o pruebas durante ella.

La revisión final de TEMP mediante lstat, sin seguir enlaces ni abrir datos
ajenos, encontró **cero directorios residuales RC3/RC5/RC6** y cero
`.suadc-test-*` en el repositorio. No hizo falta limpieza correctiva final.
Se conservaron los registros de prueba fuera de Git y los tres directorios
`spica-config-test-*` del 2026-10-29 ya documentados en RC9, consultando solo
metadatos. No se adoptó ni eliminó ninguna raíz ajena.

Control final de log, hashes y temporales:
`2026-11-20T05:26:23.213101+00:00`. La creación del registro fue
`2026-11-20T05:09:31 UTC`; no es un instante de exportación RC8.
Un sondeo auxiliar de hora usó inicialmente el parámetro Get-Date -AsUTC,
no disponible en este PowerShell; se sustituyó por DateTime.UtcNow. Esa
incidencia de monitorización no fue un fallo de la suite ni cambió código.

## Compatibilidad y conexiones originales

RC1/RC2 conservan identidades/perfiles y desconocidos. RC3 no recibe cierres
nuevos. RC4 sigue describiendo; RC5 materializa y verifica dentro de TEMP; RC6
conserva únicamente los contratos que admite y los bytes del portador; RC7 no
admite dependencias no QA nuevas. RC8/RC9 siguen siendo contratos locales con
testigos no persistibles. Sus APIs/versiones, JSON QA 0.1.0 y 85-J/K/85001
permanecen intactos. No se vuelve operativo ninguno de esos experimentos.

| Conexión original de la [matriz 85-F](matriz_dependencias_integracion_paso85f.md) | Estado tras RC10 |
|---|---|
| M03, C08→C09/C02: ejecutar PlanConsulta/traducir selectores institucionales a HTTP | P; ningún ejecutor, mecanismo, presupuesto o autorización institucional nuevo |
| M16, C12→C02/C11: recomendación de readquisición→GET/ingesta con hook/ejecutor aprobado | P; no se añade hook ni efecto |
| M26, C20→C21/C24/C19: evidencia documental→QA/aplicabilidad/operación por vínculo revisado | P; conservar un diagnóstico sintético no aprueba evidencia institucional |
| M32, resultados futuros→almacenamiento/exportación científica y linaje transversal | P; este expediente técnico no es un resultado científico futuro ni su almacén operativo |

La [hoja 85-M](hoja_ruta_continuidad_arquitectonica_paso85m.md) mantiene su
alcance y prioridades; no se equipara su agrupación original con la numeración
de incrementos posteriores. Las [29 brechas PNDA](brechas_reconciliadas_pnda_paso84i.md)
permanecen: 2 resueltas, 17 parcialmente documentadas, 8 pendientes y 2
contradicciones documentadas. INGEMMET `/query` continúa NO AUTORIZADO.

## Riesgos, límites y siguiente decisión

Persisten proceso Python cooperativo, contexto declarado, control sin firma,
confianza del canal del control y posibilidad de sustitución coordinada bajo
una autoridad. La captura conservada no autentica productor/consumidor, no
prueba QA por tercero ni concede licencias, permisos o validez científica.

Perfil cerrado pequeño: no todo grafo QA o evidencia documental futura está
registrado. Los tipos no admitidos y los conflictos que RC4/RC6 no puedan
representar en el portador se rechazan, sin truncar o aplanar informes. No se
afirma recuperación universal. Los contratos completos se preservan únicamente
dentro del perfil explícitamente admitido.

Se mantiene un escritor cooperativo por raíz, publicación exclusiva y limpieza
propia. No hay transacción global, reserva de espacio/RSS/CPU, concurrencia hostil,
garantía frente a pérdida eléctrica, retención operativa o respaldo independiente.
Event no interrumpe la proyección JSON en memoria. TEMP/0700 no acredita DACL
Windows; no se cambian ACL ni se promete confidencialidad de datos aportados.

La proyección usa utilidades internas RC6 de tipos/presupuestos, y el contraste
histórico conoce las causas físicas nativas RC9. El acoplamiento está localizado
y requiere revisión/versionado si cambian esos contratos; no se extrae un
framework por anticipado. La política específica de datos históricos necesita
aprobación antes de usarse para otra finalidad.

Siguiente incremento recomendado para revisión: acordar el alcance y confianza
admisibles de esta evidencia histórica y después diseñar el requisito no QA de
la arista exportar→consumidor, manteniendo QA, física, historial y permisos
separados. No se inicia RC11 ni se implementa esa habilitación en RC10.

Cero conexiones/GET/descargas, instalaciones, migraciones, commits o push.
No se accede al CSV PNDA, RAW, staging o SQLite operativos ni a información
institucional privada. No se emite una comprobación nueva de originales reales.
La arquitectura integral sigue abierta; se espera revisión del equipo.

## Estado final y dictamen

Rama y HEAD iguales al inicio: `feature/suadc-http` /
`424e585f9f02f5f89febbe9283ee532d86e284e5`. Árbol registrado e índice intactos.
Salida de git status --short:

```text
?? docs/auditoria_arquitectonica_rc10.md
?? docs/contrato_conservacion_evidencias_rc10.md
?? docs/recuperacion_evidencias_tecnicas_rc10.md
?? src/spica/artefactos/_codec_evidencias_rc10.py
?? src/spica/artefactos/conservacion_evidencias.py
?? tests/test_conservacion_evidencias_rc10.py
```

**Dictamen: APTO CON RESTRICCIONES para conservación y recuperación
experimental del perfil RC10 documentado.** Se implementa y prueba la
recuperación de los contratos admitidos desde procesos y raíces diferentes,
con preservación de identidades, relaciones, restricciones, diagnósticos y
estados. Se comprueba físicamente el portador, se rechazan incompatibilidades
y se separa la historia de la comprobación actual. No se detectaron regresiones
en la suite nueva completa.

No quedan correcciones bloqueantes conocidas para ese perfil experimental.
Persisten los límites y exclusiones enumerados, en particular confianza del
control sin firma, ausencia de custodia/durabilidad operativa, tipos fuera del
perfil y admisión no QA por dependencia aún pendiente. No se promete recuperación
de cualquier informe nativo futuro, ni se transforman datos históricos en una
captura local nueva o cierre QA. El uso operativo y cualquier ampliación requieren
otra decisión explícita. No se inicia automáticamente el siguiente bloque.
