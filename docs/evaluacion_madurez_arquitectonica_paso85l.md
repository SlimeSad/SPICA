# PASO 85-L — Madurez arquitectónica y criterios de cierre básico

Fecha: **2026-11-12, America/Lima**. Rama `feature/suadc-http`, HEAD inicial
**d3372a0**, «SUADC: respaldo y restauracion experimental de linaje paso 85-K».
Git inicialmente limpio; 85-K consolidado. Este es un dictamen documental para
revisión, sin implementación, nuevas pruebas, autorización científica o acceso
operativo. Véanse [custodia](arquitectura_custodia_independiente_paso85l.md) y
[amenazas/dominios](modelo_amenazas_dominio_fallo_paso85l.md).

## 1. Método, evidencia y decisiones recuperadas

Se inspeccionan texto/código y pruebas existentes como texto/AST; no se importan
módulos de SPICA, abren bases, ejecutan pilotos o consultan registros privados de
las sesiones anteriores. Se distingue evidencia histórica de prueba, inspección
estática actual y propuesta todavía no implementada. Un commit prueba registro
de archivos, no aprobación científica, jurídica o global de arquitectura.

Documentos revisados y conservados, sin sobrescribirlos:

| Paso / fuentes locales | Evidencia y decisiones que aporta |
|---|---|
| 85-F: [auditoría integral](auditoria_arquitectura_integral_paso85f.md), [matriz](matriz_dependencias_integracion_paso85f.md), [hoja de ruta](hoja_ruta_arquitectonica_paso85f.md) | C01–C25, R01–R12, H01–H10, M01–M33; alcance básico, datos originales, separación de permisos, integración por caso y recursos modestos |
| 85-G: [contrato](contrato_ejecucion_integrada_paso85g.md), [piloto](piloto_integracion_vertical_paso85g.md), [brechas](brechas_integracion_paso85g.md) | Flujo vertical fijo sintético, estados/presupuesto/cancelación, procedencia, QA0→exportación→consumo→conciliación; M18 obtiene evidencia acotada |
| 85-H: [contrato de cierre](contrato_trazabilidad_cierre_paso85h.md), [piloto final, sección 7](piloto_cierre_ejecucion_paso85h.md), [brechas](brechas_persistencia_linaje_paso85h.md) | Prefijos/nativos, cierre efectivo, traza y cotejo por enlaces; no ciencia por CONCLUIDA |
| 85-I: [arquitectura](arquitectura_persistencia_linaje_paso85i.md), [protocolo](protocolo_recuperacion_ejecuciones_paso85i.md), [plan](plan_implementacion_persistencia_paso85i.md) | Diseño híbrido mínimo con SQLite existente, artefactos/manifiesto, confirmación lógica y compatibilidad explícita; no otra base de ejecuciones |
| 85-J: [implementación](implementacion_persistencia_paso85j.md), [piloto](piloto_recuperacion_paso85j.md), [brechas](brechas_persistencia_paso85j.md) | Perfil experimental 85001, codec tipado, conservación/recuperación y lectura entre procesos; el RAW temporal del arnés no sobrevive |
| 85-K: [arquitectura](arquitectura_respaldo_restauracion_paso85k.md), [piloto](piloto_respaldo_restauracion_paso85k.md), [custodia pendiente](brechas_custodia_paso85k.md) | Backup API, copias físicas independientes, control explícito y restauración TEMP; sin dominio físico independiente o custodia protegida |

Referencias de decisión de base: [adquisición](contrato_adquisicion.md),
[tiempo](politica_temporal.md), [RAW/MD-01/02/03](almacenamiento_raw.md),
[catálogo](catalogo_cientifico.md), [plan](planificacion_consultas.md),
[interoperabilidad](interoperabilidad_espaciotemporal.md),
[QA0](calidad_nivel0.md), [JSON QA](contrato_exportacion_qaqc_paso85c.md) y
[aplicabilidad](verificador_aplicabilidad_cientifica.md).
Mantienen identidades lógicas distintas de ruta/hash, valores originales,
desconocidos explícitos y descubrimiento/transferencia/comprobación/confirmación
separados. Offline, bloques, dependencias mínimas, IA opcional y ausencia de GPU
obligatoria son además requisitos expresos del encargo 85-L, coherentes con 85-F.

No se localiza una **ERS/SRS global versionada y formalmente aprobada** en los
archivos/búsquedas del repositorio; las menciones encontradas remiten a esa carencia
en 85-F/G. Esto no demuestra que no exista fuera. No se busca en datos privados ni
se inventa una ERS retrospectiva. Para el próximo caso basta aceptar explícitamente
su alcance trazado a estos contratos; no se atribuye aprobación por estar en Git.

Inventario estático actual: **100 módulos src, 9 herramientas Python y 56 archivos
test_ con 1884 métodos/IDs únicos**. Una dependencia directa en requirements:
`httpx==0.28.1`. Contar métodos no ejecuta pruebas ni demuestra cobertura completa.
El total aprobado de **1884, 0 fallos/errores/omitidas**, corresponde al 85-K;
no se vuelve a presentar como corrida de 85-L. Tampoco se repite pip check.

Versiones contrastadas en código: conservación, codec y respaldo **0.1.0**;
extensión experimental SQLite **85001**; JSON QA **0.1.0**. El catálogo científico
estable conserva v1; los esquemas RAW reconocidos no se confunden con 85001.
No se ejecuta migración ni se amplían lectores estables.

## 2. Matriz de madurez actual

Las columnas A–F siguientes son las dimensiones solicitadas en **85-L**, no las
categorías excluyentes A–F de la auditoría histórica 85-F. C/D indican evidencia
histórica localizada, no pruebas ejecutadas hoy. «Sí» siempre conserva el alcance
indicado; ninguna fila declara producción o validación institucional.

| Subsistema / vínculo 85-F | A: diseñado | B: implementado | C: probado aisladamente | D: integración sintética | E: integración operativa pendiente | F: validación científica pendiente |
|---|---|---|---|---|---|---|
| Adquisición, C01/C09–C12 | Contratos, fuente/recurso, fases | HTTP→RAW, manual, PNDA acotado, decisión de readquisición | [Núcleo](../tests/test_adquisicion_nucleo.py), manual y conector | Sí, ruta fija 85-G; no conector institucional universal | M03/M16 sin ejecutor; autorización/mecanismo por recurso | Acceso/capacidad no acreditan ciencia; nuevos productos requieren evidencia propia |
| Transporte, C02–C04 | Políticas de origen, límites, timeout/TLS y GET | GET pequeño, streaming/hash, reintentos/cancelación | [HTTP](../tests/test_transporte_http.py), descarga/reintentos | Sí, MockTransport y HTTP→RAW | Perfil HTTPS/TLS obligatorio según flujo; política genérica permite HTTP/get sin TLS. No se probó red aquí | Técnica, no valida contenido o medición |
| RAW/configuración, C05/C06 | MD-01/02/03 y uso privado secuencial | Archivos/SQLite, publicación exclusiva, inspección y configuración | [RAW](../tests/test_almacenamiento_raw.py), configuración/regresiones | Sí, originales de fixture comprobados durante 85-G | Antecedente de inicialización operativa no reinspeccionado; respaldo completo/concurrencia/durabilidad pendientes | Integridad de bytes no es conformidad ambiental |
| Catálogos, C07 | Metadatos, revisiones, evidencias | Catálogo científico estable v1 y catálogo de activos separado | [Catálogo](../tests/test_catalogo_cientifico.py) | Sí, snapshot enlazado al activo 85-G | Sin FK global entre DB/archivos; 85001 no es migración v1 aprobada | Declaraciones/versiones no autentican fuente ni metrología |
| Planificación, C08/C12 | Consultas multivariable/multiestación y recomendaciones | Plan y decisión declarativos | [Plan](../tests/test_planificacion.py), readquisición | No ejecuta planes; tarea_ref 85-G es referencia | M03/M16 siguen previstos; ejecutable/autoriza_red no conceden permiso | Selectores no prueban cobertura ni aplicabilidad científica |
| Metadatos, C13/C14/C20 | Declaración, referencia, restricciones y cotejo separados | Inspectores CSV/OOXML y cotejador documental | [Vinculación](../tests/test_vinculacion_documental.py) | Fixtures y cotejos acotados, distintos de identidad editorial | Expediente específico vigente, derechos y contradicciones pertinentes | 29 brechas PNDA sin cambios; no promover cotejo literal a aprobación |
| Interoperabilidad, C19 | Espacio/tiempo/unidad declarados, aptitud por operación | Snapshots y adaptadores offline | [Adaptadores](../tests/test_adaptadores_interoperabilidad.py) | Sí, [integración](../tests/test_integracion_interoperabilidad.py); no asociación GIS efectiva | Nuevos perfiles/CRS y vínculo autorizado por caso | Tiempo/espacio desconocidos bloquean solo métodos que los necesitan; ninguna inferencia implícita |
| QA/QC Nivel 0, C21 | Reglas/versiones/estados/restricciones | 22 definiciones y evaluación representacional del perfil | [Nivel 0](../tests/test_calidad_nivel0.py) | Sí, lectura→QA→JSON→consumo→conciliación 85-G/H | Perfil no universal; puente al método nuevo debe revisarse | COMPROBACION_SATISFECHA no valida ciencia; no activar QA1 |
| Ejecución, C25 + 85-G | Contrato/fases/identidad/presupuesto | Arnés fijo de checkout, no motor global | [Vertical](../tests/test_integracion_vertical_85g.py) | Sí, cancelación/límites/fallos y dos reproducciones | No scheduler, permisos globales, checkpoint de motor ni exactamente-una-vez | El arnés no produce ResultadoCientifico institucional |
| Linaje, 85-H | Captura/cierre y cotejo de enlaces | Traza 0.1.0 y verificador puro | [Cierre](../tests/test_traza_cierre_85h.py) | Sí, informe/nativos/JSON/estados/errores/restricciones | Identidad global y linaje de nuevos derivados no generalizados | Coherencia de traza no prueba autor ni verdad ambiental |
| Persistencia, 85-J | Híbrido mínimo, confirmación lógica | I/T/R/manifiesto + catálogo 85001 en TEMP | [Conservación](../tests/test_conservacion_linaje_85j.py) | Sí, evidencia sintética recibida y estados históricos | Codec/perfil de checkout, nuevas bases vacías; sin custodia operativa o RAW incluido | No es almacenamiento general de resultados científicos |
| Recuperación, 85-J | Estados separados; no reparar | Lector físico/semántico con cotejo 85-H | Mismo [ensayo 85-J](../tests/test_conservacion_linaje_85j.py) | Sí, proceso nuevo en el mismo perfil | Portabilidad entre cuentas/equipos y tratamiento manual de residuos pendientes | Recuperar FALLIDA/INCOMPLETA no las convierte en éxito |
| Respaldo/restauración, 85-K | Generación/inventario/control y raíz nueva | Backup API y copias físicas verificadas de una ejecución TEMP | [Respaldo](../tests/test_respaldo_linaje_85k.py) | Sí, procesos distintos y cortes abruptos documentados | Dominio físico, control protegido, cierre RAW y portabilidad no probados | Restaurar evidencia no restaura el RAW ya eliminado ni autentica institución |
| Seguridad, transversal | Código/responsable confiables, entradas no confiables | Validadores, estados, saneamiento acotado, marcadores y rechazo de rutas | [Regresiones](../tests/test_regresiones_altas.py), parsers y rutas | Sí en perfiles G–K; guardias de ensayo, no sandbox OS | Permisos/custodia/dispositivo/entorno de recuperación por revisar; TOCTOU residual | Autorización/aplicabilidad separadas; firmas/actor hostil fuera de garantía |
| Recursos, transversal | Cotas por operación/lote, bloques y cancelación | HTTP/CSV/QA y límites J/K; estimación de espacio | Pruebas de cuotas, plazos y errores de componentes | Sí, fixtures acotadas G–K | No cuota RSS ni reserva de disco/plazo forzoso global; medir antes de ampliar | Presupuesto técnico no umbral científico ni garantía de escala |
| Extensibilidad, C01/C19/C20/C24 | Núcleos y adaptaciones explícitas | Contratos tipados y puertos concretos; sin plugins de código desde JSON | Fixtures de [reglas](../tests/test_reglas_cientificas.py)/aplicabilidad y adaptadores | Parcial, perfil fijo y contratos ambientales diversos | Promoción de APIs/paquetes y adaptadores por nuevo caso; no instituciones genéricas | Meteorología, hidrología, hidrogeoquímica, geología/suelos requieren método/metadatos propios |

No se suman pruebas de filas: una misma prueba puede cubrir varias fronteras.
Los núcleos de ciencia declarativa y el [evaluador de límites sintéticos](../src/spica/calidad/experimental/limites.py)
existen; no equivalen a un primer módulo científico integrado ni a umbrales
institucionales aprobados. Main sigue siendo una entrada mínima, sin esa ejecución.

## 3. Cambio desde la matriz 85-F y dependencias que siguen abiertas

| Referencia histórica | Situación actual para el alcance concreto | Pendiente, sin reescribir la matriz anterior |
|---|---|---|
| H02/H03, M18 | 85-G/H aportan contrato, fases, puente activo→QA y ciclo vertical con cierre cotejado | PlanConsulta/ResultadoDecision no ejecutados; no repetir ese puente como si faltara, ni generalizarlo a toda SPICA |
| H04 | Perfil fijo 85-G usa HTTPS/TLS declarados y MockTransport | No prueba TLS real ni elimina opciones genéricas. Validar perfil antes de una adquisición autorizada futura |
| H06/G07/H85-05 | 85-J conserva evidencia recibida y 85-K la respalda/restaura en TEMP | No checkpoints del motor, originales supervivientes ni repositorio/exportación de derivados científicos |
| H08/J04/J09 | Marcador cooperativo, generación lógica, copias independientes y restauración comprobada en el perfil | Custodia protegida, otro dominio, portabilidad y durabilidad fuerte no cerrados |
| H01/H05, M26/M30/M32 | Barreras documentales y contratos de aplicabilidad siguen vigentes | Método, magnitud/unidad/tiempo/espacio pertinentes, salida científica y permiso separados |
| H07/H09/H10 | Límites locales, arquitectura ligera y decisiones locales disponibles | Medición global solo cuando necesaria; UI/IA postergables; ERS formal no localizada y alcance del próximo caso por revisar |

## 4. Prioridades P0–P3 y agrupación mínima

| Prioridad / condición | Requisito y evidencia que lo justifica | Tratamiento / vínculo |
|---|---|---|
| P0 si se pretende el uso bloqueado | Ciencia institucional o promoción de estados con evidencia contradictoria/perdida, identidad o permisos ausentes; H01 y barreras G–K | Bloquear solo el uso afectado. No activar por JSON válido, hash, plan o estado APROBADA; no defecto crítico nuevo demostrado |
| P0 si se pretende otro modelo | Custodia única «segura», escritor hostil/multiusuario, respaldo RAW completo o resistencia eléctrica sin soporte/evidencia; L02/L04/L05 | No prometer esas garantías. Conservar uso privado secuencial y alcance de evidencia |
| P1 para el próximo caso sintético | Especificación de un método y su entrada/salida, metadatos pertinentes, revisión y permiso delimitados; H05/H06/H10/L06 | Un solo expediente de caso y pruebas de aceptación; reutilizar contratos, no otro motor |
| P1 antes de operación | Referencia protegida/canal aceptado, destino/dispositivo verificados, conjunto completo y restauración portable; L01/L02/L03/L05 | Agrupar en un futuro caso de custodia con ensayo extremo a extremo, sin nuevo catálogo paralelo |
| P1 antes de datos institucionales | Identidad editorial/metrología/licencia y brechas pertinentes del producto/método; M26/M30/M32 | Evidencia y autorización propias; las 29 brechas no se cierran por este documento |
| P2 en perfil actual | TOCTOU residual, errores de diagnóstico, retención manual, cotas/consumo y acoplamientos privados; H07/H08/J01/J05/J06 | Medir/estabilizar cuando el caso lo exija; no refactorización general ni quitar relecturas |
| P3 | UI final, IA avanzada, APIs comerciales, nube/sincronización distribuida, GIS operativo y ampliaciones | No prerrequisitos; funciones científicas esenciales offline, sin GPU o nube obligatorias |

Las condiciones operativas no son bloqueantes universales de un ensayo sintético
descartable. No se identifica una incompatibilidad que obligue a rediseñar el flujo
sintético actual; sí hay límites estáticos que impiden extrapolarlo, especialmente
L03 para otro TEMP/equipo. No se confunde esa conclusión con una prueba de desastre.

## 5. Bloqueantes del primer módulo científico sintético

Estos criterios son **puertas de aceptación del caso elegido**, no una declaración
de que un método todavía no especificado ya las cumple. G–K aportan base estructural;
unidad/método/aplicabilidad y salida del futuro caso requieren revisión propia.
La arquitectura básica puede ser suficiente sin implementar todos los productos.

| ID | Criterio medible antes de ejecutar el caso | Base existente / evidencia por completar |
|---|---|---|
| B01 | Entrada tipada/versionada, fixture explícitamente sintética y alcance revisado; rechazo de otros tipos/código desde configuración | Núcleo/G y evaluador sintético; fijar exactamente la entrada del caso |
| B02 | IDs de entrada/evaluación/método/versiones y control esperado concordantes; ruta/hash no sustituyen identidad | Procedencia/MD y cotejos H; definir contexto del experimento, sin institución inventada |
| B03 | Magnitud, unidad y tipo de medición explícitos si el método los necesita; incompatibilidad produce rechazo/no evaluación | Contratos científicos/aplicabilidad; documentar método, parámetros e incertidumbre, sin umbrales sin fuente |
| B04 | Tiempo/espacio/instrumento requeridos identificados o declarados no aplicables; desconocidos no convertidos | Núcleos temporal/interoperabilidad; no reconstruir HORA/UBIGEO, estaciones o CRS |
| B05 | QA estructural del perfil usado, cierre y conteos reales, con distinción satisfecho/no evaluado/incompleto | QA0/G–H; no imponer el perfil SENAMHI a otra disciplina |
| B06 | Restricciones originales y del método conservadas hasta la salida, y pruebas que rechacen su omisión/promoción | QA/JSON/consumo/H; definir cuáles impiden evaluar el caso; ciencia no autorizada por QA0 |
| B07 | Flujo seleccionado reproducible sobre la misma fixture/contexto con igualdad de resultados esperados y efectos delimitados | Ruta estructural G–H probada; el futuro enlace al método aún no existe, se prueba al implementarlo |
| B08 | Éxito, fallo, incompletitud y cancelación claramente diferenciados; un fallo no crea etapas/resultados ausentes | Estados G–H como precedente; no apropiarse de un estado de descarga para describir toda la ciencia |
| B09 | Cancelación cooperativa en fronteras pertinentes y cierre de recursos en los fallos previstos | Event y cierres existentes; especificar puntos del caso, no prometer interrupción de toda llamada OS |
| B10 | Presupuesto explícito de entrada/filas/salida/tiempo pertinente y pruebas de límite; registro de alcance materializado | G/J/K y componentes; usar fixtures pequeñas, no atribuir RAM constante o cuota RSS |
| B11 | Relación verificable entrada→método/versión/parámetros→resultado, con originales intactos y diagnóstico | Traza H es precedente estructural; no etiquetar resultado científico como JSON QA0 |
| B12 | Elegir pérdida aceptada de resultados reconstruibles en memoria o persistencia compatible verificada; no una ruta a un archivo ya borrado | J/K solo conservan evidencia del perfil 85-G. Persistir un nuevo resultado necesita contrato/codec revisado, no adopción silenciosa |
| B13 | Salida tipada con unidades/estado/restricciones/versión; si hay exportación, ida/vuelta o cotejo exacto de ese contrato | JSON QA0 ya tiene pruebas; una exportación científica distinta necesita definición propia solo si se requiere |
| B14 | Desconocidos, errores y contradicciones generan diagnóstico sin reparación científica implícita | Controles existentes; incluir casos extremos y prohibir inferir contaminación/falla instrumental de una sola excedencia |
| B15 | Autorización humana específica del experimento y efectos; capacidad, plan, integridad o regla propuesta no la sustituyen | Barreras actuales; pendiente instrucción posterior. Este informe no ejecuta ni aprueba un método |

No se exige cerrar toda ERS, las 29 brechas PNDA, geoprocesamiento, UI, IA, claves,
un sistema de tareas o respaldo de datos únicos para formular ese caso sintético.
Tampoco se pueden omitir los requisitos científicos que el propio método necesite.
Si el resultado es único o se exige supervivencia al equipo, deja de servir la
excepción de fixture prescindible y aplican las puertas operativas siguientes.

## 6. Necesarios antes de uso operativo

| ID | Criterio de aceptación operativo, además de B01–B15 aplicables | Estado hoy |
|---|---|---|
| O01 | Recurso/uso/autorización concretos, originales y documentación pertinente comprobados; derechos de copia privada y distribución evaluados por separado | No revisados/otorgados por 85-L |
| O02 | Generación consistente del cierre completo pertinente (originales y catálogos/evidencia/derivados requeridos), bytes presentes y ausencia de referencias rotas | 85-K solo evidencia de una ejecución; no RAW/general |
| O03 | Referencia aceptada y protegida, disponible desde canal separado; sustitución/pérdida/referencia antigua detectadas sin autocertificación | Diseño en este paso, sin mecanismo implementado |
| O04 | Dispositivo físico/dominio identificado y copia verificada con exposición distinta, incluyendo pérdida de equipo/lugar si se promete | No se inspeccionó ni utilizó otro medio; TEMP no lo acredita |
| O05 | Restauración en nuevo equipo/perfil con origen y respaldo desconectados tras copiar; lector/versiones disponibles, IDs/estados/restricciones iguales | Mismo perfil entre procesos probado históricamente; L03 pendiente antes de prometer otro equipo |
| O06 | Versiones/compatibilidad y dependencias conservadas; rechazo de formatos desconocidos, sin migración automática ni reinterpretación de historial | Versiones cerradas actuales; política/ensayo de portabilidad operativa pendientes |
| O07 | Modelo secuencial/permisos/raíces, tratamiento manual de parciales/locks, confidencialidad y retención aprobados para la instalación | Controles locales implementados; custodia/retención operativa no cerradas |
| O08 | Pérdida máxima aceptable y tiempo de recuperación acordados/medidos, capacidad/espacio comprobados y garantías eléctricas declaradas solo con evidencia | No hay RPO/RTO numéricos ni prueba de hardware; límites del perfil no son garantías de desastre |

No hace falta resolver concurrencia hostil si se conserva y acepta el modelo de
un escritor privado. Si se exige, cambiar la frontera con autorización y pruebas,
sin presentar el marcador cooperativo como aislamiento. Antes de cualquier retirada
de evidencia se aplica el cierre de referencias y revisión del diseño de custodia.

## 7. Postergables y dependencias agrupadas

Pueden posponerse UI final, modelos IA/APIs comerciales, sincronización, cloud,
multiusuario, scheduler, catálogo universal de variables, GIS/raster y optimización
sin cuello medido. Firma digital independiente solo es requisito si se pretende
su garantía; no es condición universal de un experimento local sintético.

Agrupación para evitar refactorizaciones: (1) caso científico mínimo, entrada/salida,
metadatos/aplicabilidad y aceptación juntos; (2) cuando haya necesidad de custodia
real, cierre de originales/índices, perfil externo/portabilidad y control protegido
en un único ensayo. Reutilizar transporte, RAW y catálogos; no duplicar cliente,
motor QA, índice de ejecuciones o sistema de backups. Promover herramientas a src
solo si la nueva frontera demuestra esa necesidad y conserva versiones/contratos.

<a id="decision"></a>

## 8. Decisión sobre el siguiente paso

**Opción C recomendada: arquitectura experimental básica suficiente para comenzar,
tras revisión, el diseño/desarrollo de un módulo científico enteramente sintético
y delimitado, manteniendo los bloqueos operativos.** No se inicia aquí. El próximo
encargo mínimo debería elegir un método y aprobar su expediente/aceptación B01–B15;
no crear otro incremento de infraestructura solo para continuar la numeración.

Motivo: desde 85-F se añadieron unión vertical, cierre cotejado, persistencia,
recuperación y respaldo/restauración suficientes para probar contratos en el perfil
acotado. Los pendientes L01–L05 no aportan validez científica y no son necesarios
para reconstruir una fixture prescindible en memoria. Mantenerlos como puerta
operativa evita tanto una falsa garantía de custodia como infraestructura previa
innecesaria. No se declara que un método ausente ya cumpla los criterios.

La opción A es pertinente antes de custodia única, agrupada con destino completo
y recuperación portable: implementar solo otro archivo de hashes no cubriría
L02/L03/L05. La opción B no es previa al caso sintético actual: la incompatibilidad
de TEMP afecta al cambio de perfil/equipo; sí debe resolverse antes de O05. No se
ignora ni se modifica para que una prueba pase. No se elige otra opción D.

Dependencias del próximo caso: alcance/permiso explícitos, referencia metodológica
pertinente revisada, metadatos de fixture conocidos, contratos de entrada/salida y
restricciones. Reutilizar núcleos de QA, aplicabilidad, límites sintéticos cuando
correspondan, exportación/consumo solo en su contrato real, y trazabilidad como
precedente; no inyectar código desde un archivo de reglas.

Aceptación mínima futura: positivo y casos límite del método, unidad/medición
incompatibles o desconocidas, evidencia/aplicabilidad insuficiente, pérdida de
restricciones, identidad/contexto distintos, fallo/cancelación/límites, repetición
determinista y cero efectos fuera del ensayo. Si necesita persistencia/exportación
nueva, añadir cotejo reversible y versiones para ese tipo; no fingir compatibilidad
con codec/JSON existentes. Primero dirigir esas pruebas y luego regresión completa
con .venv y pip check si cambia código, bajo el nuevo alcance aprobado.

## 9. Verificaciones, Git y dictamen de 85-L

Se crean únicamente los tres documentos solicitados. El registro de verificaciones
de cierre procede de lectura/AST con **Python 3.15.1 de .venv y -B**, biblioteca
estándar y comandos Git. No se guardan scripts o pruebas ejecutables nuevas.
No se ejecuta suite o pip check: no cambia código ni dependencias.

| Verificación realizada en 85-L | Resultado |
|---|---|
| Tres documentos nuevos | UTF-8, salto final, sin espacios finales, caracteres de sustitución, conflictos o bloques abiertos |
| Matrices y referencias | 17 tablas con columnas coherentes; 60 enlaces locales existentes, incluida la referencia al ancla de decisión; ninguna URL abierta |
| Contratos representativos | 12 interfaces en 7 archivos contrastadas por AST, incluidos conservar/recuperar/validar informe, respaldar/verificar/restaurar y los tres campos del control |
| Versiones e inventario | 0.1.0/85001 y JSON QA 0.1.0 contrastados; 100 módulos src, 9 herramientas y 56 archivos test_, 1884 IDs estáticos únicos; no corrida nueva |
| Brechas PNDA | 29 IDs únicos de grupos R/S/T/V; 2/17/8/2 en la columna de estado, sin modificarla |
| Coherencia de alcance | 10 amenazas A–J, 6 alternativas de dominio, 16 subsistemas, 15 puertas sintéticas, 8 operativas y 10 comprobaciones conceptuales |
| `git diff --check` | Código 0, sin salida; además se revisa directamente el contenido nuevo sin seguimiento que el comando no incluye |
| `git diff --exit-code HEAD` | Código 0, sin salida; ningún archivo registrado modificado, incluidos código, pruebas y documentación histórica |
| `git diff --cached --exit-code` | Código 0, sin salida; índice sin cambios |
| Rama y HEAD | `feature/suadc-http` / `d3372a0`, sin cambios |

El primer contador auxiliar de brechas solo seleccionó el grupo R; se corrigió
la selección del verificador ad hoc para incluir R/S/T/V. No fue un fallo del
catálogo ni se alteraron datos/documentos fuente para obtener el conteo esperado.

Comandos de cierre:

```powershell
git diff --check
git diff --exit-code HEAD
git diff --cached --exit-code
git status --short
```

Estado inicial: limpio. Estado final de `git status --short`, código 0:

```text
?? docs/arquitectura_custodia_independiente_paso85l.md
?? docs/evaluacion_madurez_arquitectonica_paso85l.md
?? docs/modelo_amenazas_dominio_fallo_paso85l.md
```

Son los únicos archivos creados; no hay otro cambio de trabajo o índice. Las
comprobaciones documentales no prueban funcionamiento de nuevos controles de
custodia, otros dispositivos o portabilidad: esos mecanismos no se implementaron.

No se accedió a RAW/staging/SQLite operativos, CSV PNDA o evidencias privadas;
no se inspeccionó ningún medio externo. No hay conexiones, GET (tampoco simulados),
descargas, instalación, claves/firmas, migraciones, respaldos reales, cambios de
ACL, módulos científicos, IA/GIS operativo, commits o push. Los originales quedan
sin escrituras nuestras por ausencia de acceso, no por una reinspección física
ni por una afirmación sobre acciones de terceros.

Las [29 brechas PNDA](brechas_reconciliadas_pnda_paso84i.md) conservan sus IDs y
estados: **2 resueltas, 17 parciales, 8 pendientes y 2 contradicciones**. No se
resuelve ninguna con documentación de arquitectura ni se autoriza `/query`.

**Dictamen: APTO CON RESTRICCIONES** para revisar este diseño y preparar el caso
sintético recomendado. No aptitud operativa de custodia, conformidad científica
institucional o cierre global de SPICA. Se espera auditoría; no se continúa
automáticamente con la implementación de control independiente ni con ciencia.
