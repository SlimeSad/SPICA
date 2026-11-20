# RC12 — Decisión propuesta para la frontera de cierres no QA

Fecha: **2026-11-20**, America/Lima. Base `128ada9`.
**Diseño para revisión; ninguna evolución se implementa o autoriza en RC12.**
[Auditoría transversal](auditoria_transversal_arquitectura_rc12.md),
[conexiones](matriz_trazabilidad_conexiones_rc12.md) y
[prioridades](hoja_ruta_priorizada_rc12.md).

## Hechos contrastados con código

| Frontera | Evidencia que realmente existe | Lo que no acredita |
|---|---|---|
| Exportador nativo | [exportar_resultado_json](../src/spica/calidad/exportacion.py), JSON QA 0.1.0 desde ResultadoQA y ContextoExportacionQA | Evaluación QA nueva, archivo físico, identidad institucional o resultado científico |
| RC8 | [EvidenciaExportacion e inspector](../src/spica/artefactos/cierre_exportacion.py): invocación capturada, snapshot observado, salida UTF-8, tamaño/SHA en memoria, correspondencia de entrada, versión y restricciones | SHA físico, autenticidad independiente o permiso. Copiar el DTO pierde el testigo privado |
| RC9 | [Solicitud/InformeAdmisionExportacion](../src/spica/artefactos/admision_exportacion.py): consumidor fijo 0.1.0, validación nativa del JSON, vínculo a RC8, identidades y restricciones; RC5 opcional releído | Cierre de una operación dependiente RC3: la solicitud identifica la productora, pero no un operacion_id del consumidor |
| RC10 | [Expediente y recuperación](../src/spica/artefactos/conservacion_evidencias.py): campos públicos nativos, hechos históricos, fechas/restricciones y bytes pequeños dentro de un portador RC4 conservado por RC5/RC6 | No restaura `_captura` ni `_comprobacion`; no relee archivos RC5 históricos ni convierte el hash del portador en hash actual de cada original externo |
| RC11 | [Dictamen externo](../src/spica/artefactos/dependencia_exportacion.py): coteja una arista declarada y evidencias locales o recuperadas; preserva el linaje y los diagnósticos nativos | No devuelve SATISFECHA: su propiedad decision solo puede retornar NO_SATISFECHA, PENDIENTE o NO_ADMISIBLE; no habilita RC3/RC7 |
| RC3 | [NodoOperacion/CierreQA](../src/spica/coordinacion/modelos.py), [inspector](../src/spica/coordinacion/inspeccion.py) y [revisión QA](../src/spica/coordinacion/_qa.py) | No hay puerto actual para un cierre no QA. El campo cierre_qa no admite un informe de exportación |
| RC7 | [inspeccionar_integracion/_dependencia](../src/spica/artefactos/coordinacion.py) exige aptitud y cierre_qa_coherente_completo de la predecesora | Un preparado recuperado carece de cierre no QA admitido; física y conclusión declarada no sustituyen ese cierre |

RC3 comprueba identidad contextual, referencias, configuración, conteos, reglas,
EOF, ausencia de evaluaciones incompletas y conclusión coherente para los cierres
QA admitidos. Ese cotejo de evidencia aportada tampoco autentica al ejecutor.
RC7 conserva las restricciones y el grafo existente: no es un segundo ejecutor.

La evidencia física del expediente RC10 puede estar comprobada hoy y sus hechos
RC8/RC9 seguir siendo históricos. Su RecuperacionGeneracion contiene el
inventario del **portador documental**, distinto del inventario original de la
composición exportar→consumidor. Extraer los datos internos no autoriza sustituir
el inventario ni redefinir una composición histórica.

Las pruebas fuente que delimitan estos hechos incluyen
[RC8](../tests/test_cierre_exportacion_rc8.py),
[RC9](../tests/test_admision_exportacion_rc9.py),
[RC10](../tests/test_conservacion_evidencias_rc10.py),
[RC11](../tests/test_dependencia_noqa_rc11.py) y
[RC7](../tests/test_integracion_artefactos_rc7.py).
Se inspeccionaron; **no se ejecutan en RC12**. Los ensayos positivos/negativos de
RC11 y su suite de 2446 son antecedentes fechados, no una nueva ejecución.

## Decisión arquitectónica propuesta

**Una sola política de admisión de precondición técnica**, para la arista
`exportar_resultado_json → consumir_exportaciones`, dentro de un proceso Python
cooperativo confiable y de una composición explícita, sintética y offline.
La aprobación de ese modelo de confianza deberá ser expresa antes del piloto.
No se propone una admisión global de productores no QA.

La precondición se refiere al resultado de la **predecesora**. No debe exigir que
la operación dependiente ya haya terminado para permitir examinar su entrada:
eso introduciría una dependencia circular conceptual. Una comprobación RC9 puede
servir de validación técnica de entrada; no se reinterpretará como cierre o
ejecución registrada del nodo consumidor. Si un alcance posterior necesita
acreditar esa ejecución, requerirá captura explícita de su identidad y resultado,
separada de esta precondición.

### Datos mínimos del vínculo propuesto

Son requisitos de diseño, no nuevas clases Python o formatos ya disponibles:

| Dato | Regla de correspondencia |
|---|---|
| Perfil/versión de admisión | Clave cerrada específica y versión independiente; no nombre de función ejecutable, callback o expresión de configuración |
| Proyecto/contexto | ContextoProyecto completo esperado, con restricciones; no solo igualdad de project_id o SHA |
| Composición y arista | Composición original, identidad de predecesora y dependiente, referencias requeridas exactas, sin agregar/omitir aristas |
| Productor | Identidad fija y versión nativas RC8; operación observada perteneciente a la productora declarada y realmente completada |
| Consumidor previsto | Identidad fija, versión, finalidad y operacion_id del nodo dependiente declarados; relación explícita con su entrada canónica |
| Entrada/salida | Referencia lógica del resultado QA de entrada, object_id/revisión de salida, contenido_id y bytes nativos; versiones preservadas |
| Cotejos | Evidencia RC8 y comprobación RC9 coherentes en el proceso actual; inspección de identidad/versión/restricciones, sin un nuevo parser |
| Física | Opcional solo si la política aprobada admite consumo en memoria; si se exige, relectura actual RC5 y vínculo a esos mismos bytes |
| Confianza | Captura local cooperativa explícitamente admitida; autenticidad independiente no disponible permanece pendiente si se exige |
| Restricciones/causas | Unión con procedencia y conservación de contradicciones, faltantes y parciales; sin usar el resumen APTO RC11 como cierre universal |

Un DTO construido por el llamador con un booleano positivo no puede satisfacer
la precondición. Una eventual comprobación efímera debe proceder del cotejo
específico de evidencias nativas y quedar vinculada al snapshot completo, con
controles cooperativos de alteración comparables a RC8/RC9. No es una firma ni
una defensa frente a Python hostil; no se serializa su testigo.

### Punto de extensión y compatibilidad

1. Mantener las entradas, salidas y comportamientos predeterminados actuales
   de RC3/RC7 y la semántica de CierreQA. Un cierre de exportación **nunca** hace
   verdadero cierre_qa_coherente_completo ni incrementa contadores de QA.
2. Añadir, solo tras revisión, una entrada lateral optativa y versionada para
   la política específica de la arista. El resultado de admisión se expresa en
   un informe/versionado de inspección nuevo o compatible explícito; no como
   una operación CONCLUIDA reescrita. La forma exacta de API se decidirá al
   comprobar consumidores y codecs, antes de editar código estable.
3. RC3 y RC7 deben consumir **el mismo cotejo específico** y usar el mismo
   recorrido de precedencias existente. Se conserva un único grafo/inspector
   de coordinación; no se copia su bucle en un adaptador paralelo.
4. Separar la preparación del cotejo y el recorrido: RC8/RC11 llaman hoy a
   inspeccionar_linaje/RC3. Invocarlos recursivamente desde una nueva rama del
   mismo inspector produciría reentrada. El futuro diseño debe preparar la
   evidencia con los inspectores nativos predeterminados, fuera de ese recorrido,
   y comprobar el vínculo al consumirla. No añadir un import inmediato inverso
   de coordinación hacia artefactos que cierre ciclos de inicialización.
5. Una arista sin política expresa conserva exactamente su comportamiento
   anterior. Otras productoras, referencias, versiones o finalidades quedan
   rechazadas o pendientes; ningún fallback permisivo.
6. El dato nuevo será inicialmente **efímero**. No agregar clases a los registros
   cerrados RC6/RC10, campos a JSON QA, tablas a 85001 o lecturas de una ruta
   histórica para hacer encajar el piloto. Persistir el nuevo resultado requeriría
   otro perfil compatible y una decisión posterior, solo si existe esa necesidad.

Para el piloto RC7 se necesitará una RecuperacionGeneracion RC6 del **inventario
descriptivo original compatible**, con los bytes sintéticos de salida incluidos
por RC5/RC6 y las referencias externas declaradas como tales. No reutilizar la
generación del portador RC10 como ese inventario. Primero debe verificarse que
el caso seleccionado cabe en el perfil RC6 vigente, sin cierres QA u otros tipos
excluidos; si no cabe, detener esa parte, sin aplanar contratos ni modificar el
codec para forzar una prueba positiva. La evidencia RC8/RC9 local seguirá
aportándose aparte: recuperar el inventario no restaura su captura.

Las utilidades privadas compartidas no se convierten por este texto en API
pública. Cualquier extracción necesaria debe ser pequeña, probada y mantener los
contrastes de identidad, límites y causas; no crear un framework de cierres.

## Política de decisión que debe conservarse

| Situación | Decisión propuesta de esa precondición |
|---|---|
| Política expresa aprobada, evidencia local completa, asociaciones y restricciones compatibles | SATISFECHA solo para esa arista y esa finalidad, sin ejecutar ni autorizar al dependiente |
| Incumplimiento demostrado, identidad ajena, hash contradictorio o bloqueo aplicable | NO SATISFECHA; prevalece sobre faltantes |
| Captura/admisión ausente, comprobación incompleta, disponibilidad o autenticidad exigidas sin acreditar | PENDIENTE DE EVIDENCIA |
| Evidencia coherente de clase fuera de la política, incluido historial RC10 sin nueva comprobación admitida | NO ADMISIBLE POR POLÍTICA |

Esta tabla describe **el diseño futuro**. RC11 vigente sigue sin una ruta
SATISFECHA y sus informes históricos no cambian. Aprobar una precondición no
aprueba el resultado científico, no concede autorización institucional y no
implica ejecución automática, autenticación, conservación operativa o custodia.

## Alternativas descartadas y orden de trabajo

| Alternativa | Motivo de rechazo |
|---|---|
| Introducir InformeCierreExportacion en cierre_qa o marcar su flag QA True | Mezcla responsabilidades y falsifica evidencia/conteos QA |
| Admitir cualquier CONCLUIDA, APTO, SHA correcto o informe RC11 sin faltantes | Estados de otras dimensiones no constituyen el cierre autorizado |
| Restaurar los testigos desde RC10 o admitir historia como observación actual | Atribuye confianza/ejecución nueva inexistentes |
| Añadir un ejecutor/segundo DAG para esta arista | Duplica coordinación y amplía efectos sin necesidad |
| Crear otro almacén o extender codecs cerrados en silencio | RC5/RC6/RC10 ya resuelven sus perfiles; admisión no es una necesidad de almacenamiento nueva |
| Exigir firma/custodia empresarial para todo ensayo local | No está justificado para fixtures cooperativas; sí debe detenerse un uso que exija esas garantías no implementadas |

Se recomienda estudiar e implementar, si se aprueba, **esta única precondición
local antes de activar los efectos pendientes M03/M16**: permite comprobar el
contrato de coordinación sin red ni datos únicos. También precede a una nueva
integración de resultados científicos M32, que necesita además su semántica y
formato propios. M26 puede avanzar documentalmente en paralelo, pero su cierre
funcional revisado no se sustituye con esta admisión técnica; seguirá siendo una
precondición independiente del uso científico concreto.

No es necesario resolver custodia, IA o GIS para este piloto de memoria/TEMP.
Sí es necesario resolverlos antes de prometer esas capacidades o conservar
datos únicos bajo sus garantías. El bloque siguiente, aceptación y riesgos se
detallan en la hoja de ruta. Ninguna propuesta de este documento inicia RC13.
