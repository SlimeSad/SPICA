# RC12 — Hoja de ruta priorizada y preparación arquitectónica

Fecha: **2026-11-20**, America/Lima. Base `128ada9`.
[Auditoría](auditoria_transversal_arquitectura_rc12.md),
[matriz de conexiones](matriz_trazabilidad_conexiones_rc12.md) y
[decisión contractual propuesta](decision_evolucion_cierres_noqa_rc12.md).
**Propuestas para revisión.** Ninguna fila inicia RC13 o un núcleo científico.

## Criterio de prioridad

Primero integridad, seguridad e interpretación científica; después dependencias
y reutilización, impacto transversal, complejidad, comprobación, compatibilidad
y recursos externos. No se ordena por cantidad de tests, commits o archivos.
P0 es un bloqueo del **uso afectado**, no una declaración de fallo global de SPICA.
P1/P2/P3 no son clasificaciones formales H0/FUT sin sus fuentes.

| Orden / prioridad | Trabajo y evidencia | Riesgo/dependencia | Complejidad y comprobación | Decisión |
|---|---|---|---|---|
| 0 / P0 condicional | AT01–AT04/AT10: impedir promoción de parciales, omisión de restricciones, efectos sin permiso, datos únicos sin conservación exigida o autenticidad inventada | Integridad/seguridad/ciencia del uso concreto | Barreras ya existentes; aceptación adversarial pertinente antes de cambiar el uso | Mantener bloqueo; ningún efecto nuevo en RC12 |
| 1 / P1, precondición documental | AT08: recuperar ERS/actas pertinentes si se aportan, o ratificar el alcance local de la siguiente decisión sin homologación formal | Requisitos/aprobación desconocidos | Trazabilidad y alcance verificables, sin acceso privado o red | Incorporar a la revisión del siguiente bloque; no otro subsistema ni reconstrucción de ERS |
| 2 / P1, siguiente bloque único | AT01/AT07, IM18: admisión de una precondición no QA concreta con RC3/RC7, RC8/RC9 locales y política expresa | Cierra una frontera transversal antes de extender efectos/resultados, sin resolver M03/M16 por atajo | Complejidad media por compatibilidad/reentrada/codecs; comprobable completamente con fixtures offline | **RC13 propuesto**, sujeto a nueva autorización y criterios de este documento |
| 3 / P1, gate científico | AT02, M26/IM09/IM25: vínculo documental revisado para un producto/uso/método seleccionados | Fuente, unidad, medición, frecuencia, temporalidad y aplicabilidad; no delegable al cierre técnico | Media; positivos/negativos sintéticos y revisión humana; evidencia institucional solo por procedimiento posterior permitido | Puede prepararse documentalmente; imprescindible antes del uso científico que dependa de ella |
| 4 / P1, gate de resultado | AT03, M32/IM17/IM21/IM26: contrato de entrada/salida y linaje del primer caso científico, antes de implementar su método | Dependiente de alcance/evidencia de 3, contextos y cierre pertinente; no JSON QA universal | Media; recorrido sintético y recuperación si el caso exige conservar | Diseñar después de revisar la frontera técnica; no seleccionar algoritmo en RC12 |
| 5 / P1 condicionado a efectos | M03/M16 y AT05: mapeo plan/recomendación→operación autorizada | Recurso/mecanismo demostrado, perfil HTTPS/TLS, permiso, presupuesto y propietario del cierre | Media/alta; cero solicitudes sin autorización, MockTransport y continuidad RAW | Después de la admisión específica; no necesario para un ensayo científico exclusivamente local |
| 6 / P1 para datos únicos, P2 para fixtures | AT04/AT10, IM22/23/24: alcance de conservación, control protegido, respaldo/restauración y retención pertinentes | Dominio de fallo/autoridad, referencia externa y contenido realmente incluido | Media/alta; ensayo de pérdida del origen/control y recuperación bajo alcance aprobado | Resolver antes de prometer destino operativo/custodia o conservar una única copia; no otra DB por defecto |
| 7 / P2, integrado con el uso | AT06/AT07: medir recursos, estabilizar helpers solo donde se necesiten, revisar importaciones y guías vigentes AT09 | RAM/CPU/disco no medidos; acoplamiento privado y documentación temporal | Baja/media según caso; fixture/equipo/budget acordados, regresión de API/errores | Acompañar la frontera seleccionada, no refactorizar todo ni crear un framework |
| 8 / P3 o fuera del alcance | IM27/28: GIS/UI/IA/comercio/cloud/multiusuario generales | Sin necesidad ni autorización actuales; no dependencia de calidad científica esencial | Necesidades/efectos futuros, sin estimar alcance inexistente | Posponer; /query INGEMMET NO AUTORIZADO, IA opcional y desacoplada |

Los órdenes 3–6 son dependencias condicionadas por el uso, no una secuencia de
implementaciones automáticamente encargadas. Si aparece un defecto crítico
reproducible que afecte la siguiente frontera, su corrección precede al piloto.
RC12 no identificó mediante ejecución un defecto nuevo de ese tipo.

## Único bloque siguiente recomendado

**RC13 propuesto: piloto offline de admisión específica de la precondición
productora de exportación JSON QA0.** No se inicia aquí.

Objetivo: permitir, únicamente bajo una política expresamente revisada, que
la evidencia local pertinente de `exportar_resultado_json` se considere suficiente
para la **arista declarada hacia el consumidor nativo**. La operación dependiente
puede seguir DECLARADA/PLANIFICADA; satisfacer una precondición no la ejecuta ni
acredita su cierre. No se acepta un DTO de éxito ni un cierre QA inventado.

Justificación: RC8/RC9 ya tienen productor/consumidor reales y capturas locales;
RC11 ya coteja identidades/restricciones y demuestra el bloqueo. Reutilizar esos
componentes permite probar una evolución transversal con bajo coste externo y
sin archivos institucionales. Añadir otro respaldo o un algoritmo no resuelve
la frontera de admisión que queda explícitamente abierta.

Componentes/contratos afectados, **solo si se aprueba el bloque**:

- Política y vínculo específicos del resultado/entrada de la arista; contexto,
  IDs, versiones y finalidad esperados explícitos, no predicados cargados de archivos.
- RC3/RC7: punto lateral de admisión versionado y recorrido compartido existente,
  con comportamientos predeterminados actuales preservados; sin segundo grafo.
- RC8/RC9/RC11: reutilizar los cotejos y controles cooperativos sin despachar
  otra operación ni reinterpretar sus informes como autorización.
- RC4/RC5 para las asociaciones y física **solo cuando sea exigida**.
  RC10 sirve como caso histórico negativo, sin modificar su perfil ni restaurar testigos.

Se debe resolver antes de codificar la separación preparación/recorrido para
evitar reentrada RC3→RC8/RC11→RC3, así como la compatibilidad de versiones de
inspectores e informes. No se añaden tipos a codecs cerrados ni campos a JSON QA,
SQLite 85001, RC6 o RC10. El resultado de admisión será inicialmente efímero.
La propuesta de datos mínimos está en la decisión contractual asociada; no se
declara disponible una API nueva por escribir este diseño.

### Pruebas y aceptación propuestas

Estas pruebas **no existen como ejecución RC12 ni se suman a la suite histórica**:

1. Una arista del perfil expresamente aprobado, RC8 local completo, RC9 coherente,
   IDs/versión/entrada/salida/finalidad correctos y restricciones compatibles
   satisface solo esa precondición. Probarla en RC3 y RC7 usando la misma política.
   Si el contrato mínimo no puede expresarlo legítimamente, detener la ampliación
   y conservar el bloqueo, sin forzar la prueba positiva.
2. Otras aristas/productores/usos/versiones no se admiten automáticamente; sin
   política expresa el resultado anterior de RC3/RC7 es idéntico al histórico.
3. Referencia/proyecto/contexto/composición/operación/resultado ajenos, captura
   alterada, hash contradictorio o bloqueo heredado/adicional impiden satisfacción.
4. Ausencia de captura o admisión, física exigida no disponible, evidencia parcial,
   fallida, cancelada o solo declarada CONCLUIDA conservan causas y no se promueven.
5. DTO positivo construido/copiado o historia RC10 íntegra no adquieren captura
   local; el control sin firma no acredita autenticidad. Exigir una confianza
   independiente no disponible deja pendiente/inadmisible, sin inventarla.
6. Dos proyectos con bytes idénticos mantienen identidades y permisos separados;
   cierre QA genuino de otra operación no sustituye exportación. Los conteos QA
   y cierre_qa_coherente_completo no cambian por admitir la precondición no QA.
7. Contratos/recuperaciones históricos conservan perfiles y estados; el portador
   RC10 nunca se usa como inventario original. El caso RC7 debe aportar la
   recuperación RC6 compatible de su inventario descriptivo y contenido incluido,
   más las comprobaciones locales separadas; si no cabe en el perfil vigente,
   detenerlo sin modificar codecs. Sin parser, almacén o DAG paralelo.
8. Determinismo de decisión/diagnósticos bajo iguales hechos, restricciones con
   orígenes completas, recursos/limpieza propios y cero ejecución automática,
   red, permisos efectivos, ciencia o escrituras operativas.
9. Pruebas dirigidas y suite completa **sobre el código definitivo** si se cambia
   Python, con números/errores reales y revisión de importaciones/compatibilidad.

Riesgos del bloque: semántica demasiado amplia, requisitos circulares para el
consumidor, confianza en DTO, pérdida de restricciones, efectos por un resultado
positivo, ciclos/reentrada y evolución silenciosa de formatos. La aceptación
requiere política cerrada y controles de esas fronteras; no más infraestructura.

Restricciones propuestas: fixtures en memoria/TEMP propios, cero red/instalaciones/
datos institucionales/RAW operativo/staging/SQLite operativo, sin umbrales,
núcleos, IA/GIS, cambios de perfiles históricos, commits o activación automática.
No se elimina el permiso independiente para una operación futura.

## Preparación antes del primer núcleo científico

Esta matriz contiene **17 condiciones de preparación** del caso futuro, no 17
funciones nuevas ni requisitos de una ERS reconstruida. «Obligatoria» se aplica
a su necesidad concreta; una dimensión no pertinente requiere justificación
explícita, nunca un dato inventado. No hace falta implementar toda función futura
de SPICA para evaluar un caso local, pero tampoco basta contar tests.

| ID | Dimensión / capacidades | Mínimo antes del núcleo seleccionado | Qué puede posponerse bajo restricción | Estado actual de preparación |
|---|---|---|---|---|
| PC01 | Contrato de entrada, IM05/06/15 | Obligatorio: perfil, carga útil y lector/adaptador explícitos; original preservado | Universalidad de disciplinas/formatos | Infraestructura parcial; perfil científico aún no seleccionado/revisado |
| PC02 | Proyecto/contexto, IM01/03 | Obligatorio: IDs, versión/configuración, pertenencia y alcance canónicos | Gestor empresarial de proyectos/usuarios | RC1 aporta contratos; aplicación y aprobación del caso pendientes |
| PC03 | Procedencia, IM09/13 | Obligatorio: recurso/versión/asset cuando proceda, snapshot, evidencia y confianza pertinentes | Consulta remota si se trabaja offline | Infraestructura disponible; sin nueva comprobación de originales operativos en RC12 |
| PC04 | Perfiles, IM06/07 | Obligatorio: campos/variable/unidad/medición/frecuencia documentados o desconocidos bloqueados según el método | Ontología ambiental universal | RC2 aporta descriptores; perfil/método científico pendiente |
| PC05 | Compatibilidad, IM07/08 | Obligatorio cuando haya comparación/asociación: finalidad y dimensiones pertinentes demostradas | Conversión general de unidades/CRS/zonas | Cotejo literal/documental disponible; equivalencia científica no acreditada |
| PC06 | QA/QC, IM16/25 | Obligatorio: QA requerido por el método, estados, cobertura/EOF y límites; revisión científica pertinente | Catálogo universal de reglas/métodos | QA0 disponible; no valida ciencia integral ni activa QA1 |
| PC07 | Restricciones, IM09/16/19 | Obligatorio: propagación sin pérdida y bloqueos/contradicciones respetados | Sistemas de políticas empresariales | Infraestructura existente; revisión de suficiencia y uso del caso pendiente |
| PC08 | Artefacto de salida, IM17/21 | Obligatorio: tipo/identidad/revisión, valores originales separados, estado e incertidumbre | Exportación universal/almacén de todos los derivados | RC4 parcial; contrato de resultado científico específico pendiente M32 |
| PC09 | Linaje, IM20/24 | Obligatorio: entrada→método/versión/parámetros→salida, restricciones y causas | Grafo global distribuido | RC4 aporta base; cadena del método futuro aún no implementada |
| PC10 | Coordinación, IM03/18 | Obligatorio: propietario, secuencia/efectos autorizados y resultado/errores explícitos | Scheduler, reanudación y orquestador global | RC3/RC7 declarativos; no autoridad ni ejecutor del núcleo |
| PC11 | Evidencia de cierre, IM18/19 | Obligatorio: cierre pertinente por operación y fallos/parciales sin promoción. Si se usa admisión RC3/RC7 no QA, resolver su bloqueo específico | Cierres universales/firmas para toda fixture | QA específico/RC8 disponibles; admisión no QA actual bloqueada |
| PC12 | Conservación, IM20/22/23 | Obligatoria si se conservan datos únicos/resultados: contenido incluido, perfil admitido, control y política de retención claros | Almacén operativo para un ensayo descartable en memoria/TEMP | Perfiles experimentales disponibles; no conservación operativa científica acreditada |
| PC13 | Recuperación, IM20/22 | Obligatoria cuando se prometa persistencia: otro proceso y ausencia del origen, versión/externos/restricciones comprobados | Recuperación universal entre equipos/dominios si no se exige | RC6/RC10 en perfiles cerrados; resultado científico fuera de esos perfiles requiere decisión |
| PC14 | Seguridad, IM02/10/13 | Obligatorio: alcance/permiso separado, rutas/no sobrescritura, confianza y errores seguros | IAM hostil/multiusuario para un ensayo privado secuencial | Controles locales disponibles; ningún resultado técnico concede permiso |
| PC15 | Fundamento científico, IM09/21/25/26 | Obligatorio: método/referencia/versión/parámetros/incertidumbre/aplicabilidad revisados y autorización expresa | Métodos de otras disciplinas | M26 y expediente del primer método pendientes; ninguna aprobación se deduce de esta auditoría |
| PC16 | Uso offline, IM10/26/28 | Obligatorio para el caso local: funciones esenciales deterministas sin red/IA/GPU/pagos | IA, nube, servicios, GIS/UI operativos | Capas locales permiten ese diseño; no hay núcleo aprobado/implementado |
| PC17 | Recursos, IM04/15/18 | Obligatorio: límites y cancelación/alcance del caso, manejo de agotamiento; medición si se afirma escala | Reserva global/RSS/plazo forzoso si el alcance no los promete | Cotas locales existentes; presupuesto/medición del método futuro pendientes |

No están satisfechos los gates científicos PC01/04/08/09/15 de un método aún
no seleccionado y autorizado. PC10/11 requieren el alcance apropiado: resolver
esta arista no QA no equivale a resolver todos los cierres científicos. M03/M16
no son obligatorios para una entrada exclusivamente local; M26/M32 pertinentes
no pueden omitirse por ese motivo. La custodia se vuelve obligatoria antes de
las garantías de datos únicos/operativas que la necesiten, no por exigir cloud.

**No se autoriza iniciar los núcleos científicos.** La decisión posterior debe
seleccionar el caso y contrastar estos mínimos con evidencia y requisitos
disponibles, sin declarar terminada por ello la arquitectura de SPICA.

## Verificaciones documentales y estado final

Las verificaciones de lectura/AST, inventario/imports, fuentes históricas y PNDA
se describen en la auditoría. Se usó únicamente Python **3.15.1 de .venv** con
`-B`, programas efímeros por entrada estándar y biblioteca estándar. No se
importó SPICA ni se ejecutaron pruebas unitarias o pip check nuevos. Las 2446
aprobadas siguen siendo evidencia histórica RC11; el recuento AST no las ejecuta.

Verificaciones efectivamente realizadas:

| Comprobación | Resultado y límite |
|---|---|
| Git inicial y consolidación | Árbol limpio; RC11 registrado en 128ada9, rama feature/suadc-http |
| Lectura/AST y compilación en memoria | 126 archivos src, nueve herramientas y 67 test_: **202 Python**, sin errores; ninguna aplicación/import ejecutado |
| Definiciones/test IDs | Sin definiciones repetidas en el mismo ámbito; 2446 IDs test_ estáticos únicos, sin afirmar ejecución |
| Contratos seleccionados | Campos RC3/RC9/RC10/RC11 contrastados por AST; falta identidad de operación dependiente en SolicitudAdmisionExportacion actual, y garantías actuales no concedidas |
| Imports explícitos | 482 aristas internas/456 inmediatas, sin ciclo explícito inmediato; dos grupos diferidos documentados. No imports src→herramientas/tests. Sin prueba universal de órdenes de carga |
| Fuentes formales | Búsqueda de rutas registradas/históricas ERS/actas/H0/FUT/G0 y contraste 85-M: fuentes no localizadas, sin inferir inexistencia fuera del repositorio |
| PNDA | 29 IDs únicos y estados 2 resueltas/17 parciales/8 pendientes/2 contradicciones, sin cambios |
| Cuatro Markdown nuevos | UTF-8/EOF, sin espacios finales, caracteres de sustitución, conflictos o cercas abiertas; revisión directa de archivos sin seguimiento |
| Matrices y referencias | **14 tablas** con columnas coherentes, **265 enlaces locales** existentes; IM01–28 en ambas tablas, M01–33 únicos, seis grupos auxiliares y PC01–17 únicos |
| Coherencia semántica | Cuatro M pendientes en todos los documentos; SATISFECHA futura propuesta distinguida del RC11 actual; ningún resultado positivo científico u operativo nuevo |
| Recursos propios | Auditoría de lectura/memoria, sin crear entornos de prueba TEMP ni abrir almacenes o conexiones |
| git diff --check | Salida 0, sin texto; complementado por revisión explícita de los Markdown nuevos, que Git todavía no incluye en diff |
| git diff HEAD --exit-code / git diff --cached --exit-code | Salida 0, sin texto; archivos registrados e índice intactos, sin cambios funcionales |

Comandos Git de recuperación y cierre:

```powershell
git status
git log -5 --oneline
git branch --show-current
git rev-parse HEAD
git diff --check
git diff HEAD --exit-code
git diff --cached --exit-code
git status --short
```

También se consultaron `git ls-files` y `git log --all --name-only --format=`
para nombres candidatos de fuentes formales; `rg` y lecturas de código/docs
para contrastar llamadas/contratos. Una búsqueda inicial sin coincidencias de
AGENTS no altera el resultado limpio de Git. Las referencias de tests/funciones
son evidencia inspeccionada, no tests ni servicios invocados en este bloque.

Rama/HEAD finales iguales al inicio: `feature/suadc-http` /
`128ada9a8f1f75c926cb4372e519197c94777029`. Estado final comprobado
en el cierre documental, con **solo cuatro archivos nuevos**:

```text
?? docs/auditoria_transversal_arquitectura_rc12.md
?? docs/decision_evolucion_cierres_noqa_rc12.md
?? docs/hoja_ruta_priorizada_rc12.md
?? docs/matriz_trazabilidad_conexiones_rc12.md
```

**Dictamen: APTO CON RESTRICCIONES para continuar la arquitectura y revisar la
propuesta de un único bloque siguiente.** No es conformidad formal con una ERS
ausente, garantía operativa o autorización científica. Los contratos bloqueados
se mantienen bloqueados; ninguna funcionalidad se implementó durante RC12.
No se declara terminada la arquitectura integral. Se espera auditoría del equipo.

Cero conexiones/GET/descargas, instalaciones, acceso a RAW/staging/SQLite operativo,
migraciones, commits o push. Ninguna propuesta de esta hoja inicia RC13 ni los
núcleos científicos, altera las 29 brechas PNDA o autoriza `/query` INGEMMET.
