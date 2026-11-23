# RC13 — Precondición productora local de exportación JSON QA

Fecha de elaboración: **2026-11-23**, America/Lima. Base `43ff570`.
Escenario sintético offline, proceso Python cooperativo. No autorización institucional.

## Matriz previa a la implementación

| Contrato requerido | Disponible / evidencia existente | Evidencia insuficiente | Integración propuesta | Riesgo y prueba necesaria |
|---|---|---|---|---|
| Identidad y operación productora | RC1/RC4 y captura RC8 del exportador fijo | Nombre de función o CONCLUIDA declarada | Reutilizar RC11 y RC8 completos | Operación, proyecto, versión, resultado o linaje ajenos deben impedir satisfacción |
| Consumidor y operación prevista | RC9 valida el JSON; RC3 declara el nodo y la arista | RC9 no identifica una ejecución de la operación dependiente | Política externa enlazada al nodo y su entrada canónica | Rechazar otra entrada, otro consumidor y otra operación; no acreditar su cierre |
| Restricciones y finalidad | RC11 reúne restricciones con procedencia | APTO no es permiso ni cierre nativo | Conservar RC11 íntegro, sin quitar diagnósticos | Bloqueos aplicables, conflictos y aplicabilidad desconocida impiden satisfacción |
| Física actual | RC5 y relectura RC11 cuando se exige | Hash en memoria o verificación histórica | Reutilizar la relectura existente | Archivo alterado/ausente y exigencia no demostrada |
| Historia | RC10 conserva campos públicos; omite testigos | Integridad del portador no prueba ejecución actual | Recuperación nativa y caso negativo | No restaurar capturas, seguir rutas históricas ni cambiar codecs |
| RC3 | Solo CierreQA, sin puerto de admisión no QA | RC8 no puede ocupar cierre_qa | Informe nativo adjunto sin modificarlo | Defaults, orden y contadores QA idénticos |
| RC7 | Requiere el cierre QA; coteja una recuperación RC6 | RC10 contiene otro inventario: el del portador | Inspección nativa de una generación descriptiva original compatible | No usar el portador como inventario original ni fabricar una habilitación |

## Decisión de compatibilidad previa

RC12 propuso estudiar una entrada lateral. Las interfaces actuales no la ofrecen:
[RC3](../src/spica/coordinacion/inspeccion.py) y
[RC7](../src/spica/artefactos/coordinacion.py) exigen cierre QA. RC13 ordena limitar
el piloto a una política externa verificable si admitirla exige cambiar una
interfaz estable. **Se detiene esa integración efectiva**. No se modifica ningún
contrato previo, recorrido, estado, contador ni formato. El dictamen local puede
ser satisfactorio y la dependencia nativa seguir pendiente: son ámbitos distintos.

El diseño seleccionado conserva el [dictamen RC11](../src/spica/artefactos/dependencia_exportacion.py)
completo y lo contrasta con la política específica, sin otro grafo, parser,
ejecutor o almacenamiento. La operación dependiente sigue declarada/planificada;
la validación RC9 no se atribuye a una ejecución registrada de ese nodo.

## Contrato implementado

Módulo explícito: [precondicion_productora.py](../src/spica/artefactos/precondicion_productora.py).
No se añade a los exportadores de los paquetes estables.

| Elemento | Contenido y regla |
|---|---|
| Versión RC13 | `0.1.0`, independiente de versiones QA, RC6 y RC10 |
| Perfil cerrado | `rc13.exportacion_json_qa0_a_consumo_local` |
| Clase de cierre | `rc8.exportacion_json_qa0`; no es CierreQA |
| Confianza admitida | `proceso_cooperativo_captura_local`, seleccionada expresamente; no autenticidad independiente |
| PoliticaPrecondicionProductora | Vínculo PoliticaDependenciaExportacion RC11 completo, entrada_consumidora_id, perfil, clase, confianza y versión |
| SolicitudPrecondicionProductora | Solicitud RC11, política RC13 opcional e inspección RC7 opcional mediante SolicitudIntegracion nativa |
| DictamenPrecondicionProductora | Solicitud, dictamen RC11 íntegro, informe RC7 opcional, diagnósticos estables y contraste local efímero; ofrece informe RC3 y restricciones nativas |
| Examen | `examinar_precondicion_productora(solicitud)`; no llama al despachador RC8 ni a admitir_exportacion_tecnica |

Se identifican **dos operaciones** mediante la dependencia explícita RC3 del
vínculo RC11: predecesora y dependiente. El inventario esperado, composición,
proyecto/contexto completo, entradas, productor/versión, consumidor/versión,
finalidad, artefacto/revisión e identidad de contenido se cotejan con RC11.
La política RC13 debe contener el mismo vínculo y la entrada canónica de salida
debe pertenecer al nodo consumidor. No bastan nombres de función, ruta o hash.

Productor fijo: `spica.calidad.exportacion.exportar_resultado_json`, versión
`0.1.0`, operación DESCRIPCION_ESTRUCTURAL iniciada explícitamente antes de RC8.
RC8 debe observar CONCLUIDA, resultado JSON QA `0.1.0`, tamaño/SHA UTF-8 coherentes,
entrada ResultadoQA nativa, salida PREPARADO `application/json` y captura local.
La declaración histórica del productor no se reescribe a CONCLUIDA.

Consumidor fijo: `spica.calidad.consumo.consumir_exportaciones`, versión `0.1.0`,
finalidad `consumir_json_qa0_rc9`. RC9 debe haber ejecutado realmente la validación
nativa de los mismos bytes y conservar comprobación local coherente. La operación
dependiente prevista es DESCRIPCION_ESTRUCTURAL DECLARADA o PLANIFICADA. RC9 no
contiene su operacion_id: RC13 lo enlaza como **destino previsto** a través de la
arista, sin atribuirle la invocación RC9 como cierre registrado. Su conclusión no
es requisito para examinar su entrada y no se inventa una captura de consumidor.

## Estados y evidencias

Se reutiliza DecisionDependencia de RC11. La nueva decisión solo describe la
precondición **local externa**. No se cambia la propiedad decision de RC11.

| Condición | Decisión RC13 |
|---|---|
| Contradicción comprobada en los cotejos, identidad, resultado, linaje, física o bloqueo aplicable | NO_SATISFECHA; prevalece sobre faltantes y políticas no admitidas |
| Política ausente/desconocida, clase/confianza/versión fuera del perfil, o historia RC10 como fuente | NO_ADMISIBLE por este perfil; conserva cualquier faltante nativo en el informe |
| Perfil admitido pero faltan captura, admisión, aplicabilidad, física/autenticidad/externos exigidos, o la comprobación local del dictamen | PENDIENTE |
| Perfil seleccionado, correspondencias coherentes, RC8/RC9 locales comprobados y ninguna condición desfavorable | SATISFECHA dentro del alcance técnico local; no admisión nativa |

La función produce un testigo privado unido al snapshot completo de su informe.
Un constructor o `dataclasses.replace` no lo obtiene. No se admite como entrada
un dictamen RC11/RC13 favorable del llamador: RC11 se calcula mediante su API.
No se serializa el testigo ni se agrega a los registros RC6/RC10. Frente a un
proceso Python malicioso capaz de manipular privados no se promete autenticidad.

| Frontera de confianza | Lo realmente acreditable |
|---|---|
| A: ejecución observada | Invocación explícita del exportador nativo en el piloto, capturada por RC8; consumidor realmente invocado por RC9 |
| B: RC8 | Snapshot/bytes/identidad y testigo cooperativo; SHA de memoria |
| C: RC9 | Validación técnica de entrada y testigo cooperativo; no cierre del nodo dependiente |
| D: RC10 | Hechos históricos y portador verificado; sin testigos actuales |
| E: RC5 actual | Relectura física de la misma salida cuando se exige; fechada, no garantía futura |
| F: declaración | Contexto esperado/operaciones/política no prueban por sí mismos una ejecución |
| G: QA genuino | CierreQA nativo permanece separado; la exportación no evalúa reglas ni cambia sus contadores |
| H/I/J: autenticidad, permisos, ciencia | No acreditados ni concedidos. Si se exige autenticidad independiente, permanece pendiente |

## Restricciones, física y compatibilidad

Las restricciones son exactamente la unión RC11 con procedencia, que conserva
proyecto, entradas, perfiles, operaciones, QA, artefactos, linaje, RC8/RC9 y RC10
si corresponde. RC5 conserva además sus diagnósticos en verificacion_actual.
Restricciones de política RC11 solo pueden restringir el uso; RC13 no las
sobrescribe ni cuenta copias como evidencias independientes. Bloqueos para
exportar/consumir y contradicciones impiden satisfacción. Usos desconocidos no
se consideran autorización. Los informes nativos desfavorables se adjuntan
íntegros: RC11 ya distingue sus límites contractuales conocidos de sus cotejos;
RC13 no añade otra lista de diagnósticos para ocultarlos.

El consumo en memoria está expresamente admitido por el perfil. No implica hash
físico. Si RC11 o RC9 exigen física, se reutiliza la relectura RC5 de RC11: una
verificación anterior de RC9 no sustituye la comprobación actual. Archivo ausente
o corrupto no se promueve. Entradas externas/autenticidad exigidas no acreditadas
dejan pendiente. No se siguen referencias físicas históricas de RC10.

RC3 se obtiene del linaje RC11. RC7, si se solicita, se ejecuta con su API
predeterminada. Se exige coincidencia del inventario descriptivo original,
composición, finalidad y único vínculo a la entrada consumidora; una recuperación
del portador RC10 no sirve. Cualquier contradicción nativa RC7 impide satisfacción;
sus faltantes de admisión no QA permanecen visibles y no se sustituyen.
**SATISFECHA no cambia esas dependencias pendientes** ni un estado de operación.

El determinismo se refiere a la decisión y sus causas bajo los mismos hechos.
Una nueva lectura RC5 incorpora su fecha de comprobación nativa: no se presenta
como el mismo informe histórico ni como garantía de integridad futura.

Todas las capacidades de habilitación RC3/RC7, ejecución automática, permiso,
autenticidad y validación científica permanecen False. La conversión del informe
a bool está prohibida. No hay callbacks, expresiones, carga de código, parser,
recorrido de grafo, tabla SQLite ni nuevo almacenamiento. Se reutilizan límites
nativos de composición, documentos RC8/RC9 y expedientes RC10; no se promete
memoria constante, plazo forzoso global o reserva de RAM/disco.

Los códigos nuevos no interpolan rutas, contenido o mensajes externos. Los DTO
nativos pueden contener metadatos aportados; no se promete un saneamiento universal
para publicarlos. Los ensayos usan exclusivamente datos inventados.
