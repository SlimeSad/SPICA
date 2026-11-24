# RC16 — Evidencias, restricciones y piloto del primer uso M26

Fecha: **2026-11-24**, America/Lima. Base `e989a72`.
[Criterios y contrato](criterios_primer_uso_m26_rc16.md),
[auditoría y verificaciones](auditoria_arquitectonica_rc16.md).

## Lectura de la matriz

Producto y finalidad conservados: SENAMHI–PNDA GBON/RBON /
`revision_documental_identidad_producto_pnda`. M26 original **C20 → C21/C24/C19**
exige vínculo explícito revisado, sin convertir evaluar_uso en permiso.
Se estudia solo la recepción del informe completo C20 → C24 de RC15.

La columna disponible distingue **código/contrato inspeccionado** y **fixture
efectivamente ejecutada**. Ninguna columna implica una comprobación institucional
actual. VERIFICADA/SATISFECHA se limita al objeto y alcance indicado; DECLARADA
conserva el dato aportado; PENDIENTE_DE_EVIDENCIA expresa insuficiencia; INCOMPATIBLE
expresa contradicción demostrada en los contratos. Un bloqueo conserva además su
tipo nativo BLOQUEO_USO_DEL_RESULTADO; no se inventa otro estado del contrato.

Los responsables pendientes son **roles funcionales propuestos**, no personas
designadas ni responsables autenticados. No se afirma que hayan revisado algo.

## Matriz de 17 criterios

| Criterio | Contrato de origen | Evidencia requerida | Evidencia disponible | Evidencia ausente | Estado de comprobación | Restricción aplicable | Diagnóstico / causa | Responsable funcional pendiente | Consecuencia para la finalidad |
|---|---|---|---|---|---|---|---|---|---|
| U01 Identidad del producto | Fuente/ProductoCatalogo, identidad RC1/C19 | Fuente e ID exactos y vínculo al recurso | Constantes PNDA y coincidencia contractual en fixture | Autenticidad actual del publicador | DECLARADA nominal; APTO_ESTRUCTURALMENTE en el cotejo sintético | No inferir autoría por nombre o ID | RC15 rechaza producto_fuera_del_perfil_pnda_rc15 | Custodio de metadatos y revisor documental | Mantener ID; no acreditar producto institucional por la fixture |
| U02 Proyecto | MD-01/02, ContextoProyecto/Entrada | Proyecto/contexto/objeto y entrada canónica esperados | Dos proyectos sintéticos, mismos bytes y vínculos separados | Confirmación de un caso operativo real | APTO_ESTRUCTURALMENTE propio; INCOMPATIBLE al cruzar | No compartir admisión por SHA | informe_de_otro_snapshot_para_el_uso | Responsable del proyecto | El informe ajeno no sustituye al esperado |
| U03 Institución declarada | Fuente, FuenteDocumental, ProcedenciaCatalogo | Identificación del publicador y respaldo pertinente | Fuente nominal SENAMHI del código; documento de emisor ficticio | Procedencia institucional autenticada | DECLARADA; autenticidad=False | Física no autentica institución | Flag RC15/RC16 de autenticidad False | Custodio institucional/revisor legítimo | No convertir el DOCX sintético en documento SENAMHI |
| U04 Recurso catalogado | IdentidadRecurso/RecursoInteroperable | Recurso/producto concretos, revisión y procedencia | Recurso urn:fixture:recurso-catalogado-rc15 y snapshot en memoria | Referencia verificada al recurso real de la edición | DECLARADA; coherente solo en fixture | No abrir/seguir localizadores | identidad_producto_destino_contradictoria si difiere | Responsable de catálogo | Conservar referencia exacta sin atribuir existencia remota actual |
| U05 Versión | ProductoCatalogo.version, RC1/C19, FuenteDocumental | Declaración de edición o política de versionado pertinente | None legítimo en modelo/descubridor; edición ficticia en positivo | Versión institucional real y correspondencia con documento | PENDIENTE_DE_EVIDENCIA con None | No sustituir por fecha/hash/revisión | version_producto_desconocida | Publicador/custodio y revisor documental | Identidad nominal persiste; vínculo RC15 no se admite |
| U06 Revisión | ContextoEntrada, metadatos, RevisionVinculoRC15 | Snapshot completo revisado, distinto de edición | Revisión sintética y comparación exacta; cambio de revisión rechazado | Legitimidad del responsable/antecedente real | DECLARADA; INCOMPATIBLE ante revisión ajena | Una revisión local no es versión institucional | revision_de_otro_snapshot / informe_de_otro_snapshot_para_el_uso | Responsable de revisión del caso | No reciclar una revisión para otros objetos o estados |
| U07 Finalidad | Solicitud/operación RC15 | Clave única y propósito coherentes | Finalidad RC15 exacta conservada; prueba de finalidad ajena | Aprobación de otros usos, no solicitada | APTO_ESTRUCTURALMENTE para la clave; INCOMPATIBLE si cambia | Sin expansión de alcance | perfil_o_finalidad_rc15_no_admitidos | Responsable del caso/revisor de alcance | No habilita interpretación, ciencia o redistribución |
| U08 Identidad documental | ReferenciaCientifica/ReferenciaDOCX/ControlArchivo | Referencia completa, hash, tamaño y localizador | DOCX sintético 1308 bytes; control y párrafo cotejados | Identidad/editorial institucional independiente | SATISFECHA contra control de fixture | Control aportado no es firma | Cotejo nativo conserva referencia/sha/tamaño | Custodio del documento y revisor | Solo identidad relativa al control aportado |
| U09 Relación documento-producto | AfirmacionDocumental, RC15/C24 | Literal, producto/recurso/edición/ámbito y revisión pertinentes | Literal del ID coincidente en fixture; PRODUCTO DECLARADA | Correspondencia editorial real y aplicabilidad revisada | APTO_ESTRUCTURALMENTE sintético; uso real PENDIENTE | COINCIDE no es aprobación | vínculo RC15 y recálculo; expediente_aportado_no_corresponde_al_recalculo si difiere | Revisor documental del producto | Transportar la afirmación con sus pendientes, sin promoción |
| U10 Integridad física | CotejadorDocumental/inspector DOCX | Lectura física nueva y conservación final contra control | DOCX sintético comprobado; alteración detectada entre lecturas | Integridad del CSV/producto operativo, no inspeccionados | SATISFECHA solo para documento/lectura; falla actual conservada aparte | No extrapolar a autoría/ciencia/producto | comparacion_control FALLIDA ante alteración; cotejo_fisico_literal_no_satisfactorio | Responsable de evidencia física | Conservar antecedente y resultado actual sin reescribir historia |
| U11 Procedencia | ProcedenciaCatalogo/FuenteDocumental | Referencia, método, fecha y evidencia de origen/revisión | Procedencias inventadas explícitas, datos nativos conservados | Comprobación de legitimidad institucional/humana | DECLARADA; sin autenticación | Respaldo VERIFICADO aportado no autentica | Diagnóstico nativo clasificaciones_aportadas_no_autenticadas_por_el_nucleo | Custodio y revisor legítimos | No convertir trazabilidad sintáctica en procedencia autenticada |
| U12 Restricciones heredadas | RestriccionQA/RestriccionPropagada, RC1/RC4/15 | Tipo, operaciones, motivo y orígenes íntegros | Informativas y bloqueos de proyecto/artefacto/operación ensayados | Evaluación de condiciones reales aún no aportadas | Conservadas; INCOMPATIBLE con bloqueo aplicable | BLOQUEO_USO_DEL_RESULTADO sigue siendo bloqueante | restriccion_bloquea_finalidad_rc15; discrepancia del recálculo rechazada | Responsable del proyecto y de la restricción | El expediente aislado es insuficiente; no se rebaja el bloqueo |
| U13 Diagnósticos existentes | ResultadoUso/InformeVinculoRC15, D/N | Causas históricas, actuales y de recepción | Preservación completa; prueba de pendiente previo y lectura nueva favorable | Fuentes que resuelvan legítimamente cada causa | FALTANTE mantiene PENDIENTE; CONTRADICCION prevalece | No filtrar causas para fabricar aptitud | diagnosticos_nativos_omitidos_del_informe_aportado si se suprimen | Responsable de la causa/revisión | Una nueva lectura no borra un pendiente anterior |
| U14 Afirmaciones | EvidenciaDocumental/AfirmacionAplicabilidad/ExpedienteProducto | Dimensión, literal, fuente, nivel, incertidumbres y pendientes | PRODUCTO DECLARADA nativa; expediente y datos originales retenidos | Revisión científica/aplicabilidad de las otras dimensiones | DECLARADA, no VERIFICADA por RC16 | Sin afirmación científica favorable automática | Pendientes RC15 originales y contraste del expediente | Revisor de aplicabilidad del uso futuro | No tratar la salida C24 como fundamento aprobado |
| U15 Revisión humana acreditada | RevisionVinculoRC15 y antecedente aportado | Responsable legítimo, alcance/evidencia revisados y decisión trazable | Solo registro de revisión sintético | Legitimidad, competencia pertinente e intervención humana real | PENDIENTE_DE_EVIDENCIA; flag False | No inventar personas/firmas/aprobaciones | revision_legitima_y_uso_real_no_acreditados_por_fixtures | Responsable humano que se designe para el caso | Uso real no acreditado; no se implementa sistema de autoridad |
| U16 Condiciones/licencia | ProductoCatalogo y RestriccionUso/AspectoUso | Condiciones aplicables al producto/edición/finalidad cuando proceda | None de licencia preservado; restricción de derecho no comprobado ensayada | Términos, alcance, atribución y evidencia del caso real | Desconocida/DECLARADA según aporte; sin permiso | No interpretar silencio o mención de licencia como autorización | restriccion.derecho_no_comprobado en evaluar_uso | Custodio/revisor de condiciones de uso | Consulta técnica no concede redistribución; conservar desconocidos |
| U17 Aplicabilidad científica | C24, evaluar_uso y frontera M26 | Requisitos pertinentes al método/datos y revisión legítima | Solo barreras/contratos; ningún método seleccionado aquí | Fundamento/variable/unidad/medición/frecuencia/cobertura pertinentes | PENDIENTE_DE_EVIDENCIA; validación=False | No iniciar núcleos o umbrales científicos | estado_uso pendiente y flags False | Responsable científico del caso futuro | No acreditar ciencia por coherencia documental |

## Informe y expediente: información que debe viajar

El informe RC15 contiene solicitud, revisión, diagnóstico documental, cotejo,
ExpedienteProducto opcional, restricciones estructuradas y diagnósticos. El
expediente solo contiene producto, documentos y afirmaciones. Transportar solo
este último omite contexto/operación/artefacto/revisión, física, bloqueos con
orígenes y causas completas. El texto de pendientes no reemplaza esas estructuras.

RC16 conserva los objetos aportado y actual completos; restricciones y diagnósticos
se presentan sin eliminar causas ni degradar bloqueos. El informe aportado conserva
incluso el resultado de una lectura anterior que hoy no se reproduce. El actual
refleja el nuevo cotejo y no se usa para editar el anterior. No se normaliza None,
se cambian niveles documentales o se atribuye una revisión humana por construir
una dataclass. La recepción de un expediente aislado se rechaza antes de la E/S.

## Piloto efectivo A–L

Fabricantes y APIs nativas reutilizados desde
[tests RC15](../tests/test_vinculo_documental_rc15.py) y comprobados en
[tests RC16](../tests/test_primer_uso_m26_rc16.py). No se importan TestCase previos
en el espacio de descubrimiento del módulo nuevo. Todos los documentos, recursos,
proyectos y ediciones del ensayo son inventados; el ID nominal PNDA es el ya
implementado, no una consulta actual. Las fechas sintéticas RC15 de 2026-11-23
y 2000-01-01 se conservan como fixtures; no son una nueva revisión humana RC16.

| Escenario | Resultado comprobado |
|---|---|
| A Producto documentalmente coherente | Ambos informes nativos íntegros y cotejo nuevo; coherencia APTO_ESTRUCTURALMENTE, uso PENDIENTE_DE_EVIDENCIA |
| B version=None | Identidad conservada, consulta documental válida; vínculo pendiente y sin expediente nuevo. La física del DOCX comprobada por separado no rellena la edición |
| C Versión sintética conocida | Edición ficticia RC15 coherente permite su vínculo técnico; no es edición real. A y C usan el mismo escenario positivo, sin duplicar conteos |
| D Revisión incompatible | Revisión RC15 ajena o snapshot esperado distinto: INCOMPATIBLE; ninguna reinterpretación como revisión legítima |
| E Documento alterado | Cotejo anterior SATISFECHA y actual FALLIDA retenidos; coherencia pendiente y sin salida C24 actual |
| F Finalidad incompatible | INCOMPATIBLE; rechazo de snapshot antes de leer, o rechazo nativo del perfil si ambos informes pertenecen a esa finalidad ajena |
| G Restricción bloqueante | Proyecto/artefacto/operación ensayados: INCOMPATIBLE, tipo bloqueante y orígenes intactos |
| H Informe completo ausente | TypeError de frontera; no se inventa informe ni se lee documento |
| I Expediente sin todas las restricciones | Se demuestra esa insuficiencia; expediente aislado rechazado. Restricciones suprimidas o sustituidas del informe provocan INCOMPATIBLE y se conservan ambos conjuntos |
| J Revisión humana no acreditada | Flag False incluso en A/C; uso sigue pendiente |
| K Procedencia institucional no autenticada | Flag False, procedencia solo aportada; no autenticidad por SHA/control |
| L Contenido idéntico con identidades distintas | Cruce de proyectos rechazado antes del nuevo cotejo; cada proyecto propio puede ser coherente sin compartir acreditación |

También se ejercen campos truncados, diagnósticos nativos suprimidos, causas
previas no resueltas por una lectura favorable, restricciones documentales de
derechos, licencia desconocida, tipos ajenos, determinismo y resumen sin datos
sensibles. No se crea un escenario científicamente aprobado.

En procesos separados se comprueban órdenes directo/inverso de importación y
hooks contra socket/SQLite/nuevos procesos, lectura de SPICA_DATOS y escritura
fuera del TEMP propio. El piloto devuelve
`RC16_INFORME_COMPLETO_SIN_EFECTOS_OPERATIVOS` después de comprobar el archivo y
la limpieza. Son barreras del ensayo, no aislamiento universal del SO o defensa
contra un intérprete hostil. El producto y los almacenes operativos no se abren.

Se ejecutó además el piloto A/C y B fuera del contador unittest. En ambos se
comprobó por separado un DOCX de **1308 bytes**, SHA-256 físico
`1cf89bc7bec857ad3da26213a6c87d00924762780981a3cb1839bafe2e21d1a9`.
Con la edición ficticia: coherencia APTO_ESTRUCTURALMENTE, expediente/cotejo
actual presentes. Con None: coherencia PENDIENTE_DE_EVIDENCIA, expediente y
cotejo del vínculo ausentes, aunque la lectura física independiente satisface
su control. En ambos, el informe aportado conserva su identidad de objeto, hay
una restricción en cada informe y uso/revisión humana permanecen no acreditados.
Los bytes se conservaron y se comprobó la limpieza del TEMP propio al terminar.
No se suman estas ejecuciones al número de pruebas unitarias.

ResultadoVinculacion no añade un instante UTC propio de ejecución. La fecha de
estos documentos es de elaboración y la de ProcedenciaCatalogo es un antecedente
aportado. Las firmas de archivo no son una fecha editorial ni un registro UTC de
inspección. No se inventa un timestamp persistido que el contrato no contiene.

## Qué puede decidir el código y qué queda pendiente

Automáticamente se comprueban tipos, snapshot esperado, coherencia según RC15,
física documental dentro del control, conservación de campos/restricciones y
causas, discrepancias y estados. No se decide legitimidad humana, autoridad
institucional, equivalencia editorial, licencia aplicable o corrección científica.

Para el caso real faltan edición y correspondencia documental respaldadas,
revisión legítima del alcance y condiciones pertinentes; su obtención requerirá
un procedimiento posterior autorizado. Si ese uso exige conservación durable,
falta además un perfil admitido para el informe completo. RC6/RC10/85-J/K no se
extienden en silencio. No se modifican las 29 brechas PNDA por ejecutar fixtures.
M26 sigue pendiente, con cobertura experimental de recepción C20 → C24; C21/C19
continúan fuera de esta implementación y ningún resultado es un permiso.
