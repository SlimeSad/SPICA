# RC14 — Auditoría de integración opcional de precondición

Fecha de elaboración: **2026-11-23**, America/Lima.
[Decisión e interfaces](evolucion_interfaz_coordinacion_rc14.md),
[piloto](piloto_habilitacion_acotada_rc14.md).

## Recuperación y alcance autorizado

Git inicial limpio, rama `feature/suadc-http`, HEAD
`0e8b75992d722ff053eec389dbc533679c54175c`:

```text
0e8b759 SPICA: precondicion productora no QA experimental RC13
43ff570 SPICA: auditoria transversal y hoja de ruta arquitectonica RC12
128ada9 SPICA: dictamen experimental de dependencia no QA RC11
98094c1 SPICA: conservacion versionada de evidencias tecnicas RC10
424e585 SPICA: admision controlada de evidencias de exportacion RC9
```

RC13 quedó registrado. Se revisaron sus tres documentos:
[contrato](contrato_precondicion_productora_rc13.md),
[piloto](piloto_admision_dependencia_rc13.md),
[auditoría](auditoria_arquitectonica_rc13.md), además de la
[auditoría RC12](auditoria_transversal_arquitectura_rc12.md) y su
[decisión propuesta](decision_evolucion_cierres_noqa_rc12.md).
Se contrastaron las firmas, consumidores, estados, restricciones, pruebas y
recorridos RC3/RC7 con los contratos RC1/RC2, artefactos/linaje RC4,
materialización RC5, conservación RC6 y la cadena RC8–RC13.

La autorización RC14 permite evolucionar de modo aditivo y opcional esta única
precondición; no permite admisión universal, permisos, ciencia, efectos externos,
formatos nuevos o migraciones. No se reconstruyen ERS, actas o matrices formales
no localizadas. Se aplican las instrucciones explícitas del bloque actual.

## Alternativas e interfaces

Se compararon A/B/C antes de editar código. A ya daba el dictamen externo RC13,
sin resolver la dependencia. B requería introducir una nueva modalidad de retorno
en una API estable. Se eligió **C**, dos entradas específicas RC14 con informe
versionado propio y reutilización de los recorridos internos existentes.
La comparación completa está en la decisión enlazada.

| Frontera | Cambio real / compatibilidad |
|---|---|
| API RC3 anterior | Firma y retorno InformeComposicion conservados; llama al recorrido compartido sin aporte |
| Recorrido RC3 | Extracción a función privada; aporte específico opcional, misma estructura/orden, cierre QA y cuotas; registra estados de aristas para RC14 |
| API RC7 anterior | Firma y retorno InformeIntegracion conservados; llama a su recorrido sin aporte |
| Recorrido RC7 | Misma integración de recuperación/relaciones/restricciones y orden RC3; reconoce el aporte únicamente en la entrada y arista exactas |
| API RC14 nueva | inspeccionar_composicion_rc14 / inspeccionar_integracion_rc14, con seleccion=None por defecto y cancelación Event opcional |
| Informe RC14 | Predeterminado íntegro y vista opcional diferenciados, cotejo RC13, dependencias y restricciones con procedencia; no formato durable |
| RC1/RC2/RC4–RC13 y modelos RC3/RC7 | Sin cambios a sus campos, contratos, políticas o versiones |

Antes del cambio se buscaron todas las referencias fuente a los dos inspectores
y a InformeComposicion/InformeIntegracion. Se localizaron consumidores en
inicializadores/modelos/inspección RC3, modelos/linaje/inspección RC7, cierre RC8,
codec RC10 y precondición RC13; las llamadas de tests estaban en RC3/RC7/RC8/RC9/
RC11/RC13. No había llamadas desde herramientas. Sus argumentos y lecturas de
informes no necesitan modificación. Se añaden solo el módulo y las pruebas RC14.

Se compararon las AST de argumentos y anotaciones de retorno de las funciones
públicas anteriores contra `git show HEAD:<archivo>`: idénticas. Las pruebas
comprueban además inspect.signature. No se cambian inicializadores públicos,
__all__, InformeComposicion/InformeIntegracion ni registros de codecs.

## Reutilización, identidad y restricciones

La selección RC14 `0.1.0`, perfil `rc14.precondicion_exportacion_json_qa0`, contiene
la **solicitud RC13**, nunca un dictamen favorable aportado. Se vuelve a cotejar
RC13 antes de entrar al recorrido. El aporte privado solo se prepara si el
dictamen es SATISFECHA y su testigo, composición, proyecto e inventario concuerdan.
Las versiones/productor/consumidor/finalidad/operaciones/entradas/resultados/
artefacto/revisión/contenido siguen contrastándose mediante RC13/RC11/RC8/RC9,
sin duplicar su lógica o añadir otro parser.

El módulo de coordinación no importa artefactos ni ejecuta RC13 desde el bucle.
El aporte es una comprobación efímera con snapshot/testigo cooperativo, específica
de una arista. El mismo predicado se usa en RC3 y RC7. No hay callbacks,
despacho por nombres, registro de plugins, segundo grafo ni orquestador.

La única causa compensable es el estado INICIADA **declarado** de la productora,
frente a su CONCLUIDA observada por RC8. No se promociona el nodo ni se activa
su cierre QA. Los diagnósticos propios desfavorables del contexto productor no
se compensan, aunque reutilicen ese código de estado. La prueba adversarial
demuestra que RC13 SATISFECHA no basta en ese caso: la arista sigue pendiente.

La vista opcional registra la resolución específica con información RC14; el
predeterminado conserva el faltante y los demás diagnósticos anteriores. No se
borra evidencia, se reescribe historia ni se marca una exportación como CierreQA.
El resto de las dependencias conserva su regla previa. El consumidor solo se
habilita declarativamente si cumple también todos sus requisitos, restricciones,
compatibilidad RC2, estado y presupuestos. Otra dependencia pendiente/fallida
lo mantiene bloqueado; otra arista de la misma productora no recibe el aporte.

Las restricciones RC13 se conservan con procedencia. Las admitidas se propagan
al consumidor y sus descendientes por el recorrido RC3 existente. Las rechazadas
y sus conflictos permanecen en el informe nuevo, sin habilitación. Se reutiliza
la unión nativa RC7; duplicar una restricción no genera evidencia independiente.

## Piloto y resultados del alcance

Los escenarios y límites detallados están en el piloto enlazado. Se ejecutan
realmente el QA sintético previo, exportador mediante RC8 y consumidor mediante
RC9. La composición contiene exportar, consumidor e independiente. Hay dos
proyectos independientes con contenido idéntico, sin compartir vínculos o
habilitaciones por SHA.

Sin RC14, los informes y habilitaciones coinciden con los inspectores anteriores:
consumidor bloqueado, independiente declarativamente habilitada. Con política
expresa y evidencia local admisible, RC3 reconoce la arista y habilita al
consumidor. Con todos los contenidos sintéticos incluidos y recuperados en RC6,
**RC7 también reconoce la arista y habilita al consumidor**, sin escribir estados
históricos o fabricar un cierre QA. No es únicamente un dictamen externo.

RC7 sigue comprobando recuperación y vínculos. Una fuente externa no disponible
mantiene pendiente la arista; una entrada consumidora externa mantiene bloqueada
la operación aunque se reconozca la precondición productora. Una recuperación
releída como corrupta no se compensa. No se usa el portador RC10 como inventario
original y no se afirma una relectura física actual realizada por el inspector
RC7 puro.

RC10 se conserva y recupera realmente como historia; no restaura testigos o
admisión actual. RC11 permanece NO_ADMISIBLE bajo su contrato. Los flags de
RC13 siguen describiendo su ámbito externo; la habilitación opcional nueva se
expresa en RC14, no alterando los informes anteriores.

Se rechazan proyectos/composiciones/operaciones/consumidores ajenos, versiones,
revisiones y contenidos incompatibles, políticas desconocidas y DTO sin testigo.
Ausencias o incertidumbres exigidas mantienen pendiente la evaluación. Parcial,
fallida, cancelada y CONCLUIDA solo declarada no se convierten en cierres admitidos.
La física contradictoria detectada actualmente por RC5 impide admisión.

## Archivos y alcance de las modificaciones

| Estado | Archivo | Responsabilidad |
|---|---|---|
| Modificado | [coordinacion/inspeccion.py](../src/spica/coordinacion/inspeccion.py) | Recorrido RC3 compartido; resolución opcional y traza de dependencias |
| Modificado | [artefactos/coordinacion.py](../src/spica/artefactos/coordinacion.py) | Recorrido RC7 compartido, misma regla específica y condiciones recuperadas |
| Nuevo | [_precondicion_rc14.py](../src/spica/coordinacion/_precondicion_rc14.py) | Aporte privado y predicado único, sin importar artefactos |
| Nuevo | [coordinacion_precondicion.py](../src/spica/artefactos/coordinacion_precondicion.py) | Selección, cotejo previo e interfaces/informe RC14 |
| Nuevo | [test_coordinacion_precondicion_rc14.py](../tests/test_coordinacion_precondicion_rc14.py) | 44 pruebas con fabricantes nativos y TEMP sintético |
| Nuevo | [evolucion_interfaz_coordinacion_rc14.md](evolucion_interfaz_coordinacion_rc14.md) | Decisión y contrato |
| Nuevo | [piloto_habilitacion_acotada_rc14.md](piloto_habilitacion_acotada_rc14.md) | Escenarios, evidencias, habilitaciones y límites |
| Nuevo | Este documento | Auditoría, comprobaciones y dictamen |

El diff de los dos archivos registrados es de **48 inserciones y 13 eliminaciones**;
git diff --stat no incluye los nuevos. Se restableció CRLF en esos dos archivos
antes de congelar sus huellas, sin cambios funcionales a lo probado. No se toca
main.py, .gitignore, .venv, dependencias, modelos públicos ni formatos históricos.

## Verificaciones ejecutadas

Intérprete confirmado: Python **3.15.1** de `.venv`, HTTPX **0.28.1**, SQLite
**3.53.4**. PYTHONPATH solo se configura en el proceso con src y tests; se usa
`-B` y PYTHONDONTWRITEBYTECODE=1. No se instala nada ni se cambian configuraciones.
Las pruebas con TEMP protegido se ejecutan fuera del sandbox restringido, manteniendo
las barreras de datos sintéticos y ausencia de red/almacenamiento operativo.

Se ejecutó primero el piloto inicial de **10/10** pruebas en 3.930 s; después
**41/41** en 20.986 s. La revisión añadió tres casos, incluido el diagnóstico
propio con código coincidente, sin ocultarlo como límite del inspector.

Pruebas dirigidas sobre la implementación final:

```powershell
.\.venv\Scripts\python.exe -B -m unittest test_coordinacion_precondicion_rc14 test_coordinacion_rc3 test_integracion_artefactos_rc7 test_cierre_exportacion_rc8 test_admision_exportacion_rc9 test_conservacion_evidencias_rc10 test_dependencia_noqa_rc11 test_precondicion_productora_rc13 -v
```

```text
Ran 342 tests in 222.932s
OK
```

**342 aprobadas, cero fallidas/errores/omitidas**, incluidas **44 nuevas** y 298
regresiones RC3/RC7/RC8–RC13. Log completo fuera de Git:
`%TEMP%\spica-rc14-dirigidas-3897f031ed1e4c34847a48d0ba361b8a.log`.

Revisión estática: **207 archivos Python** (129 src, nueve herramientas, 69 test_)
parseados/compilados en memoria, sin errores de sintaxis ni definiciones repetidas
en el mismo ámbito. **2533 métodos test_ únicos estáticos**, no pruebas aprobadas
por ese recuento. Grafo de imports explícitos: **129 módulos, 478 aristas inmediatas,
cero ciclos inmediatos**. Con diferidos/tipos: 504 aristas y los mismos dos grupos
históricos documentados en RC12/RC13, sin un grupo nuevo RC14. El análisis AST no
certifica todos los recorridos dinámicos del proceso; dos órdenes de importación
se ejecutan además en intérpretes separados.

Se ejercen barreras de proceso contra red, SQLite, lectura operativa y escrituras:
el piloto de coordinación RC3 en memoria produce RC14_SIN_EFECTOS. Los contextos
RC5/RC6 comprueban su limpieza. No se atribuyen esas barreras a una certificación
del SO o una defensa frente a Python hostil.

Huellas SHA-256 de los cinco archivos Python congelados antes de la suite:

```text
src/spica/coordinacion/inspeccion.py
8676248d28b1d1a2a903e037ce5332cc3b365bc8a51986d13483bb223842d57a
src/spica/artefactos/coordinacion.py
c26be1c870574bf5f3c95a9d844c65a161f84bd16d77c21dd2f1fae478d123ac
src/spica/coordinacion/_precondicion_rc14.py
b1d627263dc3d82c2c5334dba4745228b23677858644230e36beab74370d186a
src/spica/artefactos/coordinacion_precondicion.py
d62203c1e28db923197d9a03e58fdd889e3be1cdffe9956a697914fcba65f515
tests/test_coordinacion_precondicion_rc14.py
908b2ede6330dccb3a20dcb86c98a3733bab564f252a7f19393d39a7ba7a0738
```

Suite completa final, ejecutada sobre esas mismas huellas de código:

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
```

```text
Ran 2533 tests in 1086.282s
OK
```

**2533 aprobadas, cero fallidas, cero errores y cero omitidas**: las 2489
anteriores y 44 nuevas. El log completo tiene 815270 bytes y se conserva fuera
de Git en `%TEMP%\spica-rc14-suite-final-0cffc05c547140ae9e3af09d3abc24c4.log`.
Ambos logs finales se revisaron: sin FAIL, ERROR, skipped o ResourceWarning.
Las cinco huellas posteriores coinciden con las congeladas; durante la suite
solo se completó documentación, sin modificar Python ni pruebas.

```powershell
.\.venv\Scripts\python.exe -B -m pip check
git diff --check
git status --short
```

pip check: **No broken requirements found.**, salida 0. git diff --check:
sin salida, código 0. Los tres documentos se comprobaron como UTF-8, con cierre
de bloques, tablas y enlaces locales válidos; ninguna URL externa se consultó.

El contraste de nombres de directorios TEMP `spica-*` conserva los 113 existentes
al iniciar la suite: cero directorios nuevos restantes y cero previos ausentes.
Los contextos propios del piloto comprueban además su eliminación. Esta revisión
de metadatos no certifica el contenido de temporales ajenos ni los modifica.
Se conservan deliberadamente los logs de verificación fuera del repositorio.

Git final: misma rama y HEAD inicial, sin commits ni cambios preparados. Estado:

```text
 M src/spica/artefactos/coordinacion.py
 M src/spica/coordinacion/inspeccion.py
?? docs/auditoria_arquitectonica_rc14.md
?? docs/evolucion_interfaz_coordinacion_rc14.md
?? docs/piloto_habilitacion_acotada_rc14.md
?? src/spica/artefactos/coordinacion_precondicion.py
?? src/spica/coordinacion/_precondicion_rc14.py
?? tests/test_coordinacion_precondicion_rc14.py
```

Los ocho archivos de este incremento fueron revisados, incluidos los seis sin
seguimiento. No hay otros archivos modificados o nuevos visibles en Git.

## Conexiones y preparación científica

Las definiciones se contrastaron con la [matriz original 85-F](matriz_dependencias_integracion_paso85f.md)
y la [trazabilidad RC12](matriz_trazabilidad_conexiones_rc12.md):

| Conexión | Estado después del alcance implementado |
|---|---|
| M03 C08→C09/C02, ejecutor PlanConsulta/traducción de selectores a HTTP | PENDIENTE; ninguna traducción o efecto GET nuevo |
| M16 C12→C02/C11, recomendación de readquisición→efecto | PENDIENTE; no hook, ejecución o autorización por una recomendación |
| M26 C20→C21/C24/C19, evidencia documental→uso revisado QA/aplicabilidad | PENDIENTE; no conversión de coincidencia documental en aprobación o permiso |
| M32 resultados científicos→almacenamiento/exportación | PENDIENTE con avances contractuales/físicos previos; ningún productor, formato o flujo científico nuevo |

La frontera auxiliar RC8→RC9→RC13→coordinación avanza **solo en el perfil opcional
aprobado RC14**. El bloqueo AT01 de RC12 se resuelve para esa arista local, no
para cualquier cierre no QA ni para la plataforma completa. No se renumeran las
28 responsabilidades, 33 conexiones o seis grupos auxiliares históricos.

Las [29 brechas PNDA](brechas_reconciliadas_pnda_paso84i.md) mantienen dos resueltas,
17 parcialmente documentadas, ocho pendientes y dos contradicciones documentadas.
No se modifican sus estados ni se comprueban fuentes institucionales actuales.
Las 17 condiciones PC de RC12 siguen aplicándose al futuro método pertinente;
ninguna habilitación técnica sustituye fundamento científico, entrada/salida,
aplicabilidad, unidades/referencias, conservación requerida o revisión. INGEMMET
/query sigue NO AUTORIZADO. No se inicia ningún núcleo científico.

## Riesgos y dictamen del alcance

| Hallazgo / gravedad condicionada | Tratamiento |
|---|---|
| R14-01, alta si se confunde habilitación con ejecución/permiso | Flags efectivos de permiso/ejecución/autenticidad/ciencia False; consumidor permanece DECLARADA. RC9 no identifica una ejecución registrada de ese nodo |
| R14-02, alta si se exige autenticidad independiente | Testigos cooperativos efímeros; no firma o resistencia frente a Python hostil. Exigencia no acreditada sigue pendiente por RC13 |
| R14-03, media de mantenimiento | Aporte privado y predicado de estado muy específico, usado por ambos recorridos; no registro extensible de cierres. Toda nueva clase necesita otra decisión y regresiones |
| R14-04, media al extrapolar física o persistencia | RC7 coteja snapshot RC6 fechado, no relee por sí mismo; no custodia, reserva de recursos o durabilidad operativa. No conservar el informe RC14 como credencial histórica |
| R14-05, media de cancelación/recursos | Cancelación cooperativa antes/durante los recorridos; RC13 no añade Event interno ni plazo global. Cotas nativas, no garantía RSS o reserva de disco |

No se identificó un riesgo crítico que obligara a romper API, migrar, duplicar
el inspector, relajar controles o detener esta vía compatible. Esto no certifica
ausencia de defectos fuera de los recorridos ensayados. Los conflictos y fallos
no se resuelven mediante borrados ni promociones de estado.

Siguiente prioridad propuesta para revisión: **definir el vínculo documental
revisado M26 para un único producto y finalidad**, con evidencia y aprobación
explícitas, sin ejecutar ciencia. La captura de cierre de la operación consumidora,
los permisos/efectos M03/M16 y la salida científica M32 siguen pendientes cuando
un uso concreto los requiera. No se inicia automáticamente RC15.

Dictamen del incremento: **APTO CON RESTRICCIONES para revisión del piloto y las
interfaces opcionales específicas**. No es autorización de ejecución, aptitud
operativa, homologación formal ni validación científica; SPICA permanece abierta.

Cero conexiones/GET/descargas/instalaciones/migraciones/commits/push. No se abre
CSV PNDA, RAW, staging o SQLite operativo ni información institucional privada.
No se modifica SQLite 85001, formatos 85-J/K, RC6, RC10 o JSON QA. La confirmación
describe nuestras acciones y pruebas, no un diagnóstico físico actual de originales
que deliberadamente no se inspeccionaron. Se espera auditoría antes de continuar.
