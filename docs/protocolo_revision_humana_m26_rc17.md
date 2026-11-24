# RC17 — Protocolo propuesto de revisión humana M26

Elaboración: **2026-11-24**, America/Lima. **Procedimiento diseñado, revisión
humana no acreditada; ninguna persona designada o revisión solicitada por RC17.**
[Evidencia de edición](procedimiento_evidencia_edicion_rc17.md),
[auditoría](auditoria_arquitectonica_rc17.md).

## Objeto e insumos

Revisar únicamente la relación de identidad del producto catalogado SENAMHI–PNDA
GBON/RBON para **`revision_documental_identidad_producto_pnda`**, conservando
producto/recurso, proyecto/objeto/revisión y documentos precisos. No revisar la
aptitud meteorológica del CSV ni certificar una institución.

La persona que revise deberá recibir:

1. SolicitudVinculoRC15 completa y snapshot esperado: producto, artefacto, entrada
   canónica, operación, finalidad, afirmación y control seleccionados.
2. Documentos exactos y referencias completas, pasajes/localizadores, procedencia,
   edición/fecha documental, evidencia de edición de producto y correspondencia.
   Lo desconocido conserva None; la edición del documento no rellena el dataset.
3. InformeVinculoRC15 completo, con ResultadoUso, cotejo y salida C24 opcionales,
   revisión aportada, restricciones estructuradas y diagnósticos sin filtrar.
4. ComprobacionPrimerUsoM26 completa: informe aportado y actual por separado,
   solicitud esperada, diagnósticos propios, estado_coherencia y estado_uso.
   Un resultado actual favorable no suprime un faltante anterior.
5. Matriz U01–U17, antecedentes H de 84-I/RC15/RC16 identificados como históricos,
   incertidumbres y contradicciones, condiciones de uso conocidas y desconocidas,
   límites de lectura física y de los contratos.

Un resumen público favorable, un bool, un expediente aislado, una captura de
pantalla del estado o un SHA no sustituyen ese conjunto. No recibir documentos
privados, credenciales o datos personales innecesarios por este procedimiento.

## Responsabilidades propuestas, todavía sin designación

| Función | Responsabilidad | Lo que no puede acreditarse por su sola declaración |
|---|---|---|
| Responsable del caso | Delimitar producto/finalidad/entradas y solicitar revisión por canal aprobado | No autoriza red o ciencia por adjuntar una solicitud |
| Custodio de evidencia | Entregar referencias y copias pertinentes con controles, antecedentes y límites; conservar integridad y acceso según política acordada | Custodiar localmente una copia no demuestra autoría institucional |
| Revisor documental | Examinar el conjunto exacto, registrar qué comprobó y qué no, observaciones, restricciones, fecha real y resultado acotado | Una cadena responsable_ref no acredita identidad, competencia o realización |
| Responsable de acreditar identidad y encargo | Verificar por un canal legítimo quién revisó, su función, encargo y responsabilidad para este alcance | No confundir a la persona revisora con SENAMHI o PNDA como publicadores |
| Responsable científico / de autorización pertinente | Evaluar separadamente aplicabilidad o permisos cuando se soliciten y exista fundamento | No recibe una aprobación automática de esta revisión documental |

Son funciones propuestas, no personas ni autoridades constituidas. No se crean
revisores, firmas o credenciales. Una verificación de identidad futura debe
conservar referencia al antecedente y su responsable, sin publicar datos sensibles.
Si no hay canal de acreditación disponible, registrar esa limitación; no afirmar
que RevisionVinculoRC15 o RevisionCientifica autentican a una persona.

## Secuencia y criterios de examen

1. Comprobar mandato y alcance: distinguir quién publica, quién entrega, quién
   revisa y quién podría autorizar otro uso. Si faltan insumos, registrar lo
   recibido y lo pendiente; no declarar iniciada o concluida una revisión inexistente.
2. Fijar el conjunto exacto sometido a examen. Un cambio de producto, proyecto,
   revisión, finalidad, documento o evidencia requiere nueva revisión o adenda
   explícita, manteniendo el registro anterior.
3. Contrastar U01–U04 (identidades y proyecto), U05–U07 (edición, revisión y
   finalidad), U08–U11 (documento, relación, física y procedencia), U12–U14
   (restricciones, causas y afirmaciones) y U15–U17 (persona, derechos y frontera
   científica). La matriz original conserva sus 17 IDs y consecuencias.
4. Examinar si el pasaje citado respalda precisamente el producto/recurso/edición
   y ámbito solicitado. Una persona puede comprobar lectura, localizar un literal
   o detectar una discrepancia; eso no autentica institucionalmente la copia.
5. Distinguir controles ejecutados de metadatos aportados. Si no se hizo una nueva
   comprobación física, conservar la anterior como histórica, con su alcance.
   Un documento alterado exige registrar el fallo actual junto al antecedente.
6. Registrar observaciones y evidencias por criterio, incluyendo contradicciones,
   desconocidos, restricciones informativas y bloqueantes con sus orígenes. No
   concluir favorablemente por ausencia de observaciones o por no haber buscado.
7. Documentar la realización y sus límites solo si efectivamente ocurrió. Acreditar
   identidad/responsabilidad por separado. Si una dimensión no se comprobó,
   conservarla pendiente aunque otras sean satisfactorias.
8. Entregar el registro completo junto con informes y antecedentes. Una nueva
   evidencia no elimina causas previas: cada resolución necesita justificación
   individual, referencia, responsable e historial. No editar informes históricos.

## Estados: conceptos del procedimiento y categorías de código

No se añade un enum ni un estado favorable de revisión humana al software.
EstadoAptitud describe coherencia/evidencia; no es un registro de intervención.

| Situación documental | Registro o categoría nativa pertinente | Consecuencia |
|---|---|---|
| Revisión no solicitada | Anotación documental de ausencia de solicitud; no hay un enum humano nativo | No afirmar participación; situación de este procedimiento RC17 |
| Revisión pendiente | RevisionVinculoRC15 ausente produce FALTANTE / PENDIENTE_DE_EVIDENCIA en el perfil | Mantener alcance pendiente, sin salida favorable por silencio |
| Evidencia incompleta | Diagnósticos FALTANTE; estado pendiente en RC15/RC16 | Identificar faltantes concretos, sin inventar datos o corrupción |
| Revisión efectivamente realizada | Constancia externa y antecedentes pertinentes; RevisionVinculoRC15 representa solo la revisión aportada | No hay flag automático de revisión humana legítima; RC16 mantiene revision_humana_acreditada=False |
| Observaciones o restricciones | Diagnósticos nativos, incertidumbres y restricciones con tipo/orígenes; registro humano complementario | Conservar todas; un bloqueo aplicable no se rebaja a informativa |
| Revisión no acreditada | Distinguir constancia declarada de legitimidad comprobada; estado_uso RC16 sigue pendiente salvo incompatibilidad | Una referencia de revisor o fecha aportada no acredita la persona ni el acto |
| Evidencia contradictoria | CONTRADICCION / INCOMPATIBLE para contradicción del perfil; pendientes específicos si aún falta comprobar | Detener el uso afectado; conservar ambos antecedentes y alcance |

APTO_ESTRUCTURALMENTE puede describir coherencia de una fixture, nunca prueba
que una persona real revisó. No trasladar automáticamente un resultado narrativo
al estado de una operación RC1 ni marcarla CONCLUIDA. RC15 conserva su perfil
solo sintético; el procedimiento real no puede ejecutarse por él sin revisión
contractual posterior. No falsear la naturaleza de la evidencia para admitirla.

## Ficha de revisión futura: especificación sin completar

Esta lista es una **plantilla de requisitos**, no una revisión registrada ni un
nuevo formato de persistencia. Todos sus valores de caso quedan sin aportar.

| Campo a completar cuando exista el acto | Evidencia que debe acompañarlo |
|---|---|
| Referencia de solicitud y versión del procedimiento empleado | Encargo, alcance y finalidad exacta; no inventar número de expediente |
| Producto, edición conocida o None, recurso y proyecto/objeto/revisión | Snapshots y relaciones nativas completas; distinguir versiones locales |
| Documentos, versiones, fechas y pasajes examinados | Referencias completas, copias autorizadas y controles/lecturas realmente realizados |
| Informe RC15 y recepción RC16 completos | Ambos informes, estados, restricciones con orígenes y diagnósticos íntegros |
| Persona/función revisora y responsable de acreditación | Referencia verificable al encargo y canal legítimo que acredite identidad/responsabilidad; sin datos personales innecesarios |
| Inicio/fin real y fecha de constancia, si se conocen | Evidencia de realización y zona conocida; no convertir una fecha civil o zona desconocida a UTC |
| Acciones realizadas, selección y criterio por criterio | Qué se comprobó, método, evidencias vistas y qué no fue evaluado |
| Observaciones, contradicciones y resolución trazable de cada causa | Antecedente original, nuevo soporte, motivo, responsable y restricciones que persisten |
| Resultado documental y límites | Puede declarar lo examinado; no permiso, autenticidad institucional o ciencia implícitos |
| Medio de conservación y acceso acordados | Localización/control de la constancia y anexos completos; retención/custodia a definir antes de prometer durabilidad |

ProcedenciaCatalogo.revisada_utc puede describir un antecedente **aportado** con
referencia/método/evidencia; no prueba por sí misma la fecha del acto. El cotejador
no contiene un timestamp UTC de ejecución propio. Las firmas de archivo y la
fecha de elaboración de estos documentos tampoco sustituyen esa evidencia.

RevisionCientifica pertenece a la revisión de reglas científicas. No se reutiliza
para fabricar una aprobación de identidad del dataset. Un string de firma, rol
o informe no constituye autenticación; este protocolo no especifica una plataforma
IAM, firma digital, canal de envío o sistema de custodia independiente.

## Fronteras de confianza y decisiones que quedan fuera

| Hecho | Alcance que puede sostener | Inferencia prohibida |
|---|---|---|
| Correspondencia estructural | Coherencia de contratos y snapshot del caso | Integridad física o revisión humana |
| Integridad física | Bytes/tamaño/SHA contra control, en la lectura ejecutada | Autoría, edición o validez científica |
| Evidencia de edición | Declaración localizada y relación respaldada, con sus límites | Autenticidad institucional por nombre/hash |
| Autenticidad institucional | Evidencia independiente pertinente, pendiente aquí | Revisión efectuada o permiso universal |
| Revisión realizada | Acto y alcance acreditados cuando existan | Identidad/competencia por una referencia textual |
| Identidad del revisor | Evidencia de persona/función/encargo legítimos | Ausencia de errores o aprobación institucional del producto |
| Diagnóstico evaluar_uso | Requisitos documentales según información aportada | AfirmacionAplicabilidad, ejecución o permiso |
| Afirmación de aplicabilidad | Dimensión, fuente, nivel y pendientes nativos | Aplicabilidad aprobada de todas las dimensiones |
| Permiso efectivo | Decisión expresa de quien corresponda y con fundamento | Resultado de coherencia o de una prueba sintética |
| Validación científica | Fundamento, aplicabilidad y evaluación científica pertinentes | Resultado de una revisión de identidad o una sola coincidencia |

No reconstruir HORA, UBIGEO, unidades, estaciones o zona horaria; no ejecutar QA
científico, interpretar extremos ni evaluar contaminación. No redistribuir por
una mención de licencia. Acceso a fuentes externas, lectura de originales reales,
persistencia operativa, uso científico y permisos requieren procedimientos y
decisiones adicionales. RC17 no los solicita, ejecuta ni autoriza.
