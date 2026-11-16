# RC7 — Auditoría de integración entre recuperación y coordinación

Fecha de elaboración: 2026-11-16, America/Lima. Rama feature/suadc-http.
Estado inicial limpio, HEAD **367e95fe007d275f69564252fdb120c0724ff70c**.
RC6 está registrado; se comprobaron git status, log -5, rama y HEAD.

## Decisión anterior al código

La recomendación exacta de [RC6](auditoria_arquitectonica_rc6.md) es revisar el
perfil contra consumidores necesarios y acordar retención/control protegido y
compatibilidad antes de un destino operativo o datos únicos. RC7 examina un
consumidor estructural en memoria, con datos sintéticos TEMP: no abre ese destino
ni necesita resolver antes la custodia operativa. No se identifica un bloqueo
crítico distinto que exija limitar todo el incremento a documentación.

Se revisaron los tres documentos RC6, contratos/pruebas RC1–RC2, documentos e
inspectores RC3–RC5, InformeQA/VinculoResultadoQA, interfaces RC6, matrices
85-F/85-M y hoja de ruta 85-M. La arquitectura integral permanece abierta.

A: directa; B: adaptación; C: parcial; D: ausente; E: fuera de alcance.

| Necesidad | Clase / reutilización | Decisión |
|---|---|---|
| Recuperación, identidad/control, archivos incluidos/externos | A, RecuperacionGeneracion RC6 | Recibir el resultado real y su fecha, sin reabrir raíces ni repetir hashes |
| Descriptores/productores/linaje/restricciones | A, RC4 e inspeccionar_linaje | Recalcular correspondencia contractual; no modificar el grafo conservado |
| Contextos/entradas y versiones | A/B, RC1 | Cotejar snapshots por valor entre procesos, manteniendo canonicidad por referencia dentro de cada composición |
| Requisitos de perfiles | A, comparar_perfiles por inspector RC3 | Mantener resultados completos, sin nuevo comparador |
| Dependencias, precedencia y cierre QA | A, inspeccionar_composicion RC3 | Conservar informe nativo; solo añadir condiciones recuperadas, nunca habilitar algo rechazado por RC3 |
| Unión de restricciones con origen | B, unión interna RC4 | Adaptar políticas de artefactos y propagarlas sobre aristas existentes, sin segundo grafo |
| Asociación explícita generación/artefacto/entrada/operación | D | Adaptador ligero de solo lectura; contrato nuevo mínimo para esa asociación |
| QA genuino e InformeQA | A/C, contratos nativos RC1/RC3 | Admitir evidencia adicional en memoria; RC6 no conserva esos cierres y no se amplía su codec |
| Cierre de productor descriptivo/no QA | C | Falta contrato de cierre pertinente; archivo íntegro y CONCLUIDA declarada no lo sustituyen |
| Ejecutor, almacenamiento, permisos, ciencia, autenticidad | E | No implementados |

No hay incompatibilidad que obligue a cambiar contratos públicos. Se mantiene
rc6.generacion.0.1.0, codecs/manifiestos 85-J/K, SQLite 85001 y JSON QA 0.1.0.
La integración no convierte evidencia física fechada en vigencia actual, cierre
de ejecución, aprobación científica o autenticidad institucional.

## Verificaciones y cierre

Se crean cinco archivos; no se modifica ninguno anterior:

| Archivo | Función |
|---|---|
| [coordinacion.py](../src/spica/artefactos/coordinacion.py) | Cuatro DTO mínimos, cotejo puro, integración conservadora y diagnósticos |
| [test_integracion_artefactos_rc7.py](../tests/test_integracion_artefactos_rc7.py) | 44 pruebas nuevas con fixtures y componentes nativos |
| [integracion_artefactos_coordinacion_rc7.md](integracion_artefactos_coordinacion_rc7.md) | API, correspondencias, linaje, restricciones y límites |
| [evidencias_cierre_operaciones_rc7.md](evidencias_cierre_operaciones_rc7.md) | Garantías, QA admisible, estados, piloto y casos insuficientes |
| auditoria_arquitectonica_rc7.md | Este informe |

No hay paquete, índice, almacenamiento o grafo general nuevo. La dependencia es
artefactos.coordinacion → RC6/RC4 y coordinación RC3 → contratos RC1/RC2/QA.
Los módulos anteriores no importan el adaptador; la revisión estática no detecta
ciclos que lo involucren. No hay imports src→herramientas/tests.

Se reutilizan las utilidades internas existentes de texto, orden de diagnósticos,
medición de descriptores y unión de restricciones. Esa dependencia privada queda
localizada y cubierta por pruebas; no se introduce una utilidad general paralela
ni se amplían APIs estables por conveniencia.

## Integración y evidencias

El adaptador conserva el informe RC3 nativo y una vista que solo agrega condiciones.
Utiliza su orden y aristas, sin otro algoritmo topológico. Se mantienen nodos,
requisitos/resultados RC2, CierreQA, estados y referencias; los vínculos de entrada
son explícitos y la producción procede únicamente de relaciones RC4 comprobadas.

La recuperación se identifica mediante ControlGeneracion y su versión; se
contrasta el inventario y las comprobaciones con los descriptores/informes RC5.
El linaje se recalcula con RC4. Un resultado físico no se sustituye por el hash
histórico RC5, ni se vuelve a leer un archivo desde este adaptador.

La evidencia física se atribuye a recuperacion.fecha_utc. RC7 no declara nueva
vigencia tras esa fecha, ni disponibilidad actual de un externo. Una finalidad
posterior que necesite disponibilidad requiere nueva recuperación autorizada.
Las habilitaciones siguen siendo declarativas y condicionadas a evidencia aportada,
no permiso, lanzamiento o garantía de lectura futura.

RC6 no conserva InformeQA/CierreQA. El piloto adicional lee mediante LectorCSV y
EvaluadorNivel0 existentes el archivo realmente conservado, produce InformeQA y
vínculos nativos, y los aporta a una composición candidata distinta en memoria.
No se cambia el codec para persistirlos o forzar un cierre inexistente.

Cada archivo sintético tiene **218 bytes** y SHA físico contrastado
**e5f6011f37be1ce0b1cda080b846ca1c42c5d787eab12b0568067fbccbdc3429**.
Los cinco contenidos iguales mantienen objetos, revisiones, proyectos y archivos
distintos. Son fixtures suministradas explícitamente, no productos de un método
científico ejecutado. Se usa solo L0-EST-001: un registro finalizado, un resultado,
COMPLETA/eof. HORA y UBIGEO originales permanecen sin normalización.

Con QA genuino, independiente/comparar son habilitadas declarativamente; preparar
CONCLUIDA sin cierre admitido y derivar PARCIAL permanecen pendientes. Los estados
FALLIDA/CANCELADA se ensayan en variantes sin promoverlos. Las restricciones de
descriptores/vínculos se heredan aun cuando el contexto candidato las omita.
Bloquear la QA en la vista impide acreditar su dependiente, sin borrar su cierre.

El productor Python A termina normalmente tras conservar y retirar RC5. Un B
independiente recupera e inspecciona con barrera antes de imports: sin sockets,
SQLite, escrituras/mutaciones o acceso a SPICA_DATOS. Solo independiente queda
habilitada en esa composición histórica sin QA. Se copia a otra raíz TEMP,
se retira exclusivamente la fuente propia sin recursión y otro B debe devolver
el mismo resultado. No se afirma otra cuenta/equipo/SO o dominio de fallo.

## Revisión adversarial y correcciones

La primera pasada RC7 ejecutó 37 pruebas: **35 aprobadas, 2 fallidas, 0 errores**.
El recopilador del test no incluía los diagnósticos de RelacionRecuperada, que sí
se conservaban. El caso QA con otra identidad dejaba una dependencia inexistente,
y RC3 detenía correctamente el cotejo antes de revisar el cierre. Se corrigieron
las fixtures para observar las categorías/caminos previstos, sin relajar rechazos.

Se añadieron comprobaciones de control/versiones, dependencia histórica omitida,
QA coherente sin hash vinculante, restricción aplicada a QA cerrada y cancelación
durante inspección. La siguiente pasada de 42 pruebas aprobó íntegramente.
La revisión final añadió productor contradictorio y redefinición de composición,
y amplió cuotas/comprobaciones ausentes: 44 pruebas nuevas en total.

Después de una pasada dirigida de 410 aprobadas, una revisión adicional detectó
un diagnóstico demasiado fuerte cuando faltaba el inventario de recuperación:
se utilizaba el mismo rechazo que para una referencia ausente en un inventario
disponible. Se corrigió el adaptador: **sin inventario → pendiente de evidencia**,
sin afirmar inexistencia. Se añadió esa distinción al test de generación incompleta.

La pasada completa ya iniciada se interrumpió antes de finalizar, sin usarla como
suite aprobada. Registro parcial fuera de Git:
`%TEMP%/spica-rc7-suite-a832fe2fdb9e4b779e1d7eca966feba5.log`.
Se confirmó que no quedaba un proceso de esa suite antes de editar código.
La única suite completa final se ejecutó tras cerrar nuevamente el código y las
pruebas dirigidas. La última pasada dirigida ejecutó **410 pruebas en 109.410 s:
410 aprobadas, 0 fallidas, 0 errores** (44 RC7 y 366 RC1–RC6). No se suman
pasadas ni subtests como pruebas adicionales.

Cobertura: generación íntegra/incompleta/corrupta, incluidos ausentes, externos,
identidades/revisiones/productores/linaje, cierres QA nativos e insuficientes,
estados terminales no concluidos, perfiles incompatibles/pendientes, políticas
omitidas/contradictorias, dependencias, versiones, cuotas, cancelación, pureza y
lectura/traslado entre procesos. Una prueba conserva exactamente JSON QA 0.1.0
antes/después del cotejo. El adaptador no llama al motor, transporte, archivos o SQL.

## Comandos y resultados

Todo Python ejecutado corresponde a .venv, con -B. PYTHONPATH solo se cambia en
el proceso y PYTHONDONTWRITEBYTECODE evita bytecode en procesos hijos.
Los ensayos con carpetas privadas Windows se ejecutan fuera del sandbox por sus
permisos TEMP, sin modificar ACL o ampliar el acceso a datos operativos.

```powershell
$env:PYTHONPATH = (Join-Path $PWD 'src') + ';' + (Join-Path $PWD 'tests') + ';' + $PWD.Path
$env:PYTHONDONTWRITEBYTECODE = '1'
.\.venv\Scripts\python.exe -B -m unittest test_integracion_artefactos_rc7 test_conservacion_rc6 test_materializacion_rc5 test_artefactos_rc4 test_contextos_rc1 test_perfiles_informacion_rc2 test_coordinacion_rc3 -q
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -B -m pip check
git diff --check
git status --short
```

Intérprete verificado: Python **3.15.1**, HTTPX **0.28.1**, SQLite **3.53.4**.
pip check: **No broken requirements found.** No se instalaron paquetes.
Las comprobaciones de sintaxis/AST sin bytecode, duplicaciones y espacios revisan
también los archivos sin seguimiento; git diff --check solo no bastaría.
Se comprobaron importaciones y el grafo AST de 121 módulos: ningún ciclo incluye
RC7 y ningún módulo anterior importa el adaptador. Los tres documentos contienen
14 enlaces locales válidos, comprobados sin conexiones.

La interrupción dejó una raíz TEMP de la fixture histórica RC6 entre procesos:
spica-rc6-0d67987bb21a4b5891cd6ab4ba9d7c25. Se cotejaron nombres, ubicación,
ausencia de enlaces, inventario y cuatro cuerpos sintéticos exactos (58, 58, 43
y 48 bytes), usando recuperación nativa y SHA físicos. El control observado fue
734eaabbd30748998a3f6c2b32b7a7d6 /
9268e94c2baf76bb63c37b673c4402f9dfce8eda5a72860f19909da354b75d89.
Solo tras esas comprobaciones se retiraron sus ocho archivos y su directorio,
sin recursión, con controles de identidad antes de cada retirada. No se adoptaron
nombres ajenos ni se cambió código para resolverlo.

Una lectura auxiliar inicial rechazó la representación expandida de la ruta TEMP
porque no coincidía léxicamente con la base ambiental admitida por RC6. Se usó
la base nativa y se comprobó que ambas resolvían a la misma carpeta; no se relajó
el control de rutas. Esa lectura fallida no escribió ni borró archivos y no es
un fallo de la suite. El estado TEMP final se comprueba tras finalizarla.

| Verificación final | Resultado |
|---|---|
| Dirigidas RC1–RC7 | 410 aprobadas, 0 fallidas, 0 errores; 109.410 s |
| Suite completa final | **2294 aprobadas, 0 fallidas, 0 errores**; 847.295 s; salida 0, OK |
| Regresión acumulada | 2250 anteriores + 44 nuevas, sin sumar repeticiones |
| pip check con .venv | No broken requirements found.; salida 0 |
| Sintaxis/importaciones/duplicaciones/espacios | Correctos en los dos Python nuevos, también sin seguimiento |
| Grafo de importaciones | 121 módulos examinados, sin ciclo que incluya RC7 ni importaciones anteriores hacia el adaptador |
| Documentación | Tres documentos UTF-8, cercas completas y 14 enlaces locales válidos; sin consultas externas |
| TEMP final | Cero directorios residuales spica-rc5-* o spica-rc6-* |
| Raíces de tests en repositorio | Cero directorios .suadc-test-* residuales |
| git diff --check | Sin salida, código 0 |
| Archivos registrados e índice | git diff --name-only HEAD y git diff --cached --name-only sin salida |

Registro verbose completo fuera de Git:
`%TEMP%/spica-rc7-suite-final-482cf616679149778691be742ef624db.log`.
El registro parcial de la pasada interrumpida se conserva separado; no es un
resultado aprobado y no se suma al conteo final.

Estado Git final: feature/suadc-http, HEAD sin cambios
367e95fe007d275f69564252fdb120c0724ff70c. Solo cinco archivos nuevos sin seguimiento:

```text
?? docs/auditoria_arquitectonica_rc7.md
?? docs/evidencias_cierre_operaciones_rc7.md
?? docs/integracion_artefactos_coordinacion_rc7.md
?? src/spica/artefactos/coordinacion.py
?? tests/test_integracion_artefactos_rc7.py
```

No se modifica ningún archivo previo ni el índice; no hay commits o push.

## Conexiones originales y restricciones

Se mantienen las definiciones de las matrices
[85-F](matriz_dependencias_integracion_paso85f.md) y
[85-M](matriz_diseno_implementacion_paso85m.md):

| Conexión | Estado tras RC7 |
|---|---|
| M03, C08 → C09/C02, ejecutor PlanConsulta / traducción institucional de selectores a HTTP con mecanismo/presupuesto/autorización | **P**, no hay ejecutor ni solicitudes |
| M16, C12 → C02/C11, decisión de readquisición → GET/ingesta mediante hook/ejecutor aprobado | **P**, no se activan efectos por una recomendación |
| M26, C20 → C21/C24/C19, evidencia documental → QA/aplicabilidad/operación mediante vínculo revisado | **P**, un QA0 sintético no aprueba documentación institucional |
| M32, resultados futuros → almacenamiento/exportación científica, derivados y linaje | **P**, con avance parcial RC4–RC7 de descriptores, conservación y asociación estructural. Faltan perfiles/ejecución pertinentes y exportación científica; no se cierra la conexión original |

Las [29 brechas PNDA](brechas_reconciliadas_pnda_paso84i.md) permanecen: **2**
RESUELTA_CON_EVIDENCIA, **17** PARCIALMENTE_DOCUMENTADA, **8**
PENDIENTE_DE_EVIDENCIA y **2** CONTRADICCIÓN_DOCUMENTADA. INGEMMET /query sigue
NO AUTORIZADO. No se altera evidencia institucional ni se abre el CSV PNDA.

Cero conexiones externas, GET, descargas, instalaciones, migraciones, commits o
push. Sin acceso a RAW, staging o SQLite operativos ni evidencia privada. No se
vuelven a medir originales permanentes para afirmar integridad física nueva;
se informa ausencia de acceso/escritura en este trabajo. main.py, .gitignore,
.venv, formatos y contratos históricos permanecen intactos.

## Riesgos, prioridad siguiente y dictamen

Persisten evidencia aportada no autenticada, proceso/alcance declarativo confiables,
disponibilidad posterior no revalidada, cierre no QA ausente y límites locales
sin cuotas globales/RSS/reserva/timeout. La retención, custodia, concurrencia y
durabilidad de RC6 no mejoran por un informe RC7. La barrera de ensayo no es un
sandbox contra Python hostil ni un mecanismo de permisos efectivos.

Tras auditoría se recomienda seleccionar un componente no QA concreto y diseñar
su contrato pertinente de cierre técnico antes de ampliar la admisión de
dependencias; mantener la revisión de retención/control protegido de RC6 antes
de datos únicos o destino operativo. No crear un certificador universal ni un
segundo ejecutor por esta limitación. No se inicia RC8 ni ciencia automáticamente.

Dictamen final: **APTO CON RESTRICCIONES** para integración declarativa de
evidencia recuperada, con datos sintéticos offline y alcance fechado. No quedan
fallos de pruebas o correcciones bloqueantes detectadas para ese alcance.
No habilita explotación operativa, permisos efectivos, cierre universal de
productores, ciencia o autenticidad. La arquitectura integral continúa abierta;
queda necesaria la auditoría del equipo antes de otro incremento.
