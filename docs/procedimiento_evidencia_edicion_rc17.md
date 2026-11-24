# RC17 — Procedimiento de evidencia de edición del primer uso M26

Elaboración: **2026-11-24**, America/Lima. Especificación para revisión; no es
una revisión humana efectuada ni una comprobación institucional actual.
[Protocolo humano](protocolo_revision_humana_m26_rc17.md),
[auditoría y verificaciones](auditoria_arquitectonica_rc17.md).

## Alcance y decisión

Se conserva M26 **C20 → C21/C24/C19** y su restricción histórica:

> evaluar_uso es diagnóstico; no conversor a formato QA, AfirmacionAplicabilidad o permiso

Fuentes: [matriz original](matriz_dependencias_integracion_paso85f.md),
[condiciones RC12](matriz_trazabilidad_conexiones_rc12.md),
[criterios RC16](criterios_primer_uso_m26_rc16.md) y sus
[17 condiciones U01–U17](evidencias_y_restricciones_m26_rc16.md).
RC17 prepara evidencia para la misma relación experimental C20 → C24, sin
extenderla a C21/C19. M26 sigue **PENDIENTE**.

**A**: los contratos actuales permiten representar declaraciones, referencias,
relaciones y antecedentes. **C**: faltan edición acreditada, correspondencia
editorial y revisión legítima. **D**: autenticar identidades o dar custodia
independiente requiere otra decisión. No se elige B: no se identifica una
integración pequeña necesaria para redactar este procedimiento. No hay código
nuevo, registro de revisión realizado ni piloto nuevo de integración.

Producto: SENAMHI–PNDA GBON/RBON, `FUENTE_SENAMHI` y
`PRODUCTO_GBON_RBON_ID` de los [modelos PNDA](../src/spica/adquisicion/conectores/senamhi/modelos.py).
El identificador nominal exacto, sin decodificar ni normalizar, es:

```text
variables-meteorologicas-de-las-estaciones-autom%C3%A1ticas-de-intercambio-internacional-servicio
```

Finalidad única: **`revision_documental_identidad_producto_pnda`**. Ese nombre
del código identifica el producto esperado; no prueba existencia remota actual,
autoría institucional, edición o derechos. No se selecciona una adquisición real.

## Matriz de identidades y tiempos

E = código inspeccionado ahora; H = antecedente documental del repositorio;
D = declaración, sin autenticación independiente; P = evidencia pendiente.
Las referencias H no implican releer archivos operativos en RC17.

| Elemento | Contrato / origen | Disponible y estado | Restricción y evidencia faltante |
|---|---|---|---|
| Identificador del producto | Fuente + ProductoCatalogo.identificador | E: constantes nominales PNDA; H: descripción del producto en 84-I | Conservar ID exacto; falta autenticar el origen para el caso de uso |
| Edición del producto | ProductoCatalogo.version; ContextoEntrada.version_contenido; RecursoInteroperable.version_institucional | E: literal opcional; descubridor no asigna version, queda None. El positivo RC15 usa una edición ficticia | P: edición institucional pertinente y correspondencia entre esos campos; no usar la fixture en datos reales |
| Revisión documental local | RegistroCatalogo.revision; RecursoInteroperable.revision_metadatos; ContextoEntrada.revision | E: control de revisiones de descripciones; no se consulta catálogo operativo | Una revisión local puede cambiar sin nueva edición institucional; no sustituye version |
| Revisión de la relación | RevisionVinculoRC15.solicitud, responsable_ref, procedencia | E: solicitud completa y antecedente aportado; H: solo ensayo sintético RC15–RC16 | P: realización, responsabilidad e identidad acreditadas; una referencia textual no las demuestra |
| Versión del documento | ReferenciaCientifica.version_documento / fecha_documento | H: 84-I localiza en D09 la declaración 1.0 y creación/actualización 2024-05-30 en la ficha DOCX | No acredita edición del CSV, del XLSX o del producto. Preservar el ámbito de la declaración |
| Versión de formato / software | VERSION_RC15, VERSION_RC16; formatos cerrados RC6/RC10/JSON QA/85-J/K | E: versiones contractuales propias, distintas de la versión documental | No usar 0.1.0 de software o AppVersion OOXML como edición SENAMHI |
| Identidad del recurso | IdentidadRecurso; RecursoCatalogo; FuenteDocumental.producto | E: fuente, producto, recurso y localizador diferenciados; H: 84-I conserva referencias documentales | P: correspondencia editorial explícita de cada distribución; compartir título o producto no basta |
| Fecha de consulta | ProcedenciaCatalogo.revisada_utc y antecedente de adquisición/lectura pertinente | E: campo aportado normalizado a UTC; H: 84-I documenta lectura el 2026-11-08 | No se hizo consulta externa ahora. El campo no acredita por sí mismo el evento ni fecha de publicación |
| Fecha de publicación | Declaración institucional localizada y con alcance conocido | P: no acreditada para la edición del dataset seleccionable | Las fechas D09 son campos de creación/actualización de la ficha; no renombrarlas como publicación |
| Evidencia institucional | FuenteDocumental, Respaldo, ProcedenciaCatalogo y referencias 84-I | H/D: atribución, fechas, versión y licencia nombradas; no autenticación independiente RC17 | P: origen legítimo, relación entre originales y vigencia para el uso; no afirmar inexistencia de evidencia externa |

[Catálogo de evidencias 84-I](evidencias_consultas_pnda_paso84i.md): D09 se
localiza en `D:T1/F7/C2/p1/P34`, `D:T1/F9/C2/p1/P38` y
`D:T1/F10/C2/p1/P40`. X11/D15 son propiedades técnicas editables, distintas de
esos campos visibles. D15 contiene revisión técnica 19: no es una edición
institucional. D12 nombra Open Data Commons Attribution License y acceso Público;
sus términos y cobertura no se comprueban aquí. La
[reconciliación 84-I](reconciliacion_xlsx_docx_pnda_paso84i.md) no demuestra
igualdad ni diferencia de ediciones XLSX–DOCX–CSV.

| Clase de evidencia | Situación delimitada en RC17 |
|---|---|
| Disponible | Contratos, informes históricos en documentación y referencias X/D de 84-I dentro del repositorio; las copias operativas no se abren |
| Declarada | Atribución institucional, 1.0/fechas de la ficha y licencia nombrada; no equivalen a hechos autenticados |
| Físicamente verificada | Antecedentes H de 84-I con su alcance original; ahora solo DOCX sintéticos en las regresiones RC15–RC16. No se verifica físicamente un original institucional en RC17 |
| Institucionalmente autenticada | Ninguna acreditación nueva; no deducirla de integridad, URL, nombre o metadatos aportados |
| Ausente del expediente suficiente | Edición del producto y vínculo editorial acreditados, realización/identidad legítimas de revisión y condiciones pertinentes al uso real |
| Contradictoria | Mantener causas y antecedentes de la matriz histórica y del caso; 2 contradicciones PNDA siguen documentadas. Desconocer una edición no prueba una contradicción editorial |

## Evidencia exigible para una edición futura

| Condición | Aporte admisible para examinar | Representación reutilizable / límite |
|---|---|---|
| Producto y recurso exactos | Publicación o comunicación legítima que identifique fuente, producto y distribuciones concretas | ProductoCatalogo, IdentidadRecurso, RecursoCatalogo; no deducir existencia por URL |
| Edición y política | Literal institucional de edición, alcance, sustituciones y significado de sus fechas; o declaración de que no se versiona | version solo cuando esté respaldada. Si no se versiona, mantener None y revisar posteriormente el requisito de RC15 |
| Documento de procedencia | Referencia completa, emisor declarado, versión/fecha cuando se conozcan, localizador del pasaje y antecedente de obtención | ReferenciaCientifica + FuenteDocumental + EvidenciaDocumental; no confundir referencia con autenticación |
| Relación editorial | Manifiesto o aclaración que vincule documento y edición del producto/recurso con alcance y limitaciones | FuenteDocumental.producto/version_producto y correspondencia_editorial; Respaldo es aportado, no una firma |
| Integridad | Control previo legítimo y comprobación física pertinente de bytes, tamaño, SHA y conservación | ControlArchivo/CotejadorDocumental y resultado completo; un hash declarado no es una lectura física |
| Publicación y condiciones | Texto y edición de condiciones aplicables, atribución y alcance por recurso/uso; fecha acreditada si existe | Campos de licencia/condiciones y restricciones nativas; no dictamen jurídico automático |
| Revisión | Examen humano del conjunto exacto, observaciones, alcance, responsable identificable y evidencia de realización | RevisionVinculoRC15 y protocolo enlazado; identidad/legitimidad requieren evidencia externa |

Una declaración institucional puede ser documentalmente pertinente y seguir sin
autenticación acreditada. Una copia físicamente íntegra puede corresponder a otra
edición. Una evidencia contradictoria debe conservar ambos antecedentes y su
alcance: no resolverla por fecha más reciente, mayoría de menciones o SHA igual.
Ausencia en una búsqueda acotada no prueba inexistencia de documentos oficiales.

## Procedimiento futuro, sin ejecución en RC17

1. Fijar proyecto, objeto/revisión, producto, recurso, finalidad y alcance temporal
   de la relación solicitada. Inventariar desconocidos y causas U01–U17.
2. Pedir a su responsable evidencia ya disponible por un canal autorizado. Si
   requiere web, descarga o consulta institucional, proponer primero el recurso,
   método, límites, destino y autorización específica. No enviar solicitudes aquí.
3. Identificar las copias recibidas y separar declaración de fuente, edición del
   documento, edición del producto y política de publicación. No seguir enlaces
   ni leer almacenes operativos como efecto de este procedimiento.
4. Bajo un procedimiento de lectura autorizado, fijar control y comprobar
   físicamente las copias pertinentes con el lector existente; conservar todos
   los resultados y límites. No declarar comprobados archivos no leídos.
5. Registrar los pasajes y relaciones que respaldan cada afirmación, con
   contradicciones, incertidumbres, restricciones y fechas de distinto significado
   separadas. No fabricar una versión desde hash, nombre, descarga o FECHA_CORTE.
6. Someter el paquete completo al protocolo humano. Una fuente nueva favorable
   agrega evidencia; no borra diagnósticos previos. Resolver una causa exige
   respuesta explícita trazable y conserva el antecedente.
7. Revisar la compatibilidad antes de una integración real: **RC15 solo admite
   naturaleza SINTETICA** y exige edición conocida. RC17 no elimina esas barreras.
   Documentos reales o una política institucional sin versiones requieren una
   evolución posterior aprobada y sus pruebas; no cambiar naturaleza a SINTETICA.
8. Mantener M26 pendiente hasta revisar evidencia y destino concretos. No producir
   configuraciones QA, permisos, metadatos científicos ni cierres automáticos.

## Asociación y conservación

El producto y la finalidad siguen en SolicitudVinculoRC15; el expediente nativo
está en solicitud.expediente. InformeVinculoRC15 conserva solicitud, revisión,
ResultadoUso, cotejo, expediente de producto opcional, restricciones y diagnósticos.
ComprobacionPrimerUsoM26 conserva solicitud esperada, **el mismo informe aportado**,
el nuevo informe actual opcional y sus propias causas.

La evidencia de edición se describe con las referencias/afirmaciones nativas.
La constancia humana futura se asocia documentalmente al conjunto exacto y a su
finalidad, sin suplantar ninguno de esos informes. No se crea un objeto monolítico,
un resumen de aptitud sustitutivo o un sistema de evidencias paralelo. La
unidad de entrega continúa siendo el informe completo y la recepción completa.

RC16 conserva referencias **en memoria y bajo uso cooperativo**. No implica
custodia independiente, registro durable o protección ante modificación deliberada
de objetos Python; véase la auditoría. No hay codec aprobado para persistir este
paquete completo en RC6/RC10/85-J/K/JSON QA. No se fuerza su serialización ni se
promete conservarlo entre sesiones. Los registros humanos futuros necesitan un
medio de conservación y control de acceso acordado antes de prometer custodia.

Continúan pendientes edición y relación editorial reales, revisión realizada e
identidad legítima del revisor, autenticidad pertinente, condiciones aplicables y
decisión sobre conservación. Integridad técnica, disponibilidad, coherencia,
autenticidad, revisión, diagnóstico de uso, aplicabilidad, permiso y validación
científica siguen siendo hechos diferentes.
