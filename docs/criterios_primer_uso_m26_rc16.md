# RC16 — Criterios del primer uso documental M26

Fecha: **2026-11-24**, America/Lima. Base `e989a72`, RC15 consolidado.
[Matriz de evidencias y piloto](evidencias_y_restricciones_m26_rc16.md),
[auditoría](auditoria_arquitectonica_rc16.md).

## Definición y propósito conservados

La [matriz original 85-F](matriz_dependencias_integracion_paso85f.md), fila M26,
define **C20 → C21/C24/C19**:

> evaluar_uso es diagnóstico; no conversor a formato QA, AfirmacionAplicabilidad o permiso

Su estado es P para una vinculación explícita revisada. La
[auditoría 85-M](auditoria_continuidad_arquitectonica_paso85m.md) conserva esa
frontera; la [matriz RC12](matriz_trazabilidad_conexiones_rc12.md), apartado M26,
exige identidad documental/producto/revisión/período aplicable, selección,
revisión humana trazable, contradicciones y destino preciso. Ninguna de esas
fuentes autoriza convertir una coincidencia literal en fundamento aprobado.

C20 representa afirmaciones, expedientes y cotejos; C21, QA0; C24, catálogo de
reglas y aplicabilidad documental; C19, interoperabilidad y perfiles. El
[contrato RC15](contrato_vinculo_documental_rc15.md) implementa solo un vínculo
experimental C20 → C24, con PRODUCTO DECLARADA y pendientes. RC16 conserva ese
alcance. No inicia C20 → C21/C19 ni completa M26 con otro significado.

Producto único: **producto catalogado SENAMHI–PNDA GBON/RBON**, identificado por
FUENTE_SENAMHI y PRODUCTO_GBON_RBON_ID de los
[modelos PNDA](../src/spica/adquisicion/conectores/senamhi/modelos.py).
Se mantiene exactamente el ID original, sin normalización ni nuevos códigos.
Finalidad única: **`revision_documental_identidad_producto_pnda`**.

La finalidad permite preparar y revisar una relación documental de identidad.
No comprende interpretación de variables, equivalencia editorial, reconstrucción
de HORA/UBIGEO, aplicación científica, redistribución o permiso de operación.
En el piloto únicamente la identidad nominal procede del código existente:
proyecto, recurso descrito, DOCX, edición y revisión son sintéticos.

## Decisión previa sobre código

| Opción | Evidencia y decisión |
|---|---|
| A: contratos suficientes, solo auditoría | InformeVinculoRC15 ya conserva todos los componentes, pero no había una entrada de recepción que exigiera esa unidad y contrastara omisiones. Suficiente para representación, insuficiente para esa integración concreta |
| B: integración mínima | **Elegida**: receptor de checkout que exige el informe RC15 completo, lo conserva por referencia y vuelve a llamar a RC15 con la solicitud esperada. No duplica sus cotejos |
| C: falta evidencia o contrato | Se aplica al uso institucional/científico y a la persistencia de la nueva composición. No se inventan revisión humana, versión, autenticidad o codec para superar esos bloqueos |

No se cambia ninguna API anterior, la finalidad RC15, el descubridor, el esquema
de catálogo o las políticas RC3/RC7/RC14. No hay sistema general de permisos,
revisión humana, informes o documentación. Una sola composición tipada enlaza
contratos existentes, sin copiarlos a otro modelo de procedencia.

## Qué representa version y qué permite None

[ProductoCatalogo.version](../src/spica/adquisicion/catalogo/modelos.py) es un
literal opcional del producto. El contrato no impone una sintaxis o semántica
editorial universal ni certifica que ese literal sea institucional. No equivale
a la revisión transaccional del catálogo, la revisión local de ContextoEntrada,
revision_metadatos, un SHA, una fecha o la versión de un contrato de software.

**None es legítimo**: expresa desconocimiento. El
[descubridor PNDA](../src/spica/adquisicion/conectores/senamhi/pnda.py) construye
ProductoCatalogo sin asignar version, y RC16 no lo modifica. La identidad
Fuente/producto/recurso puede conservarse sin versión; no pierde su ID porque
falte una edición conocida.

Con None se pueden cotejar los identificadores nominales y la coherencia de
sus referencias/contextos, ejecutar CONSULTA_DOCUMENTAL sobre un expediente
válido y comprobar físicamente un DOCX controlado mediante el cotejador nativo.
Esas comprobaciones son separadas y no acreditan correspondencia con una edición
del producto. RC15 exige una edición conocida y coherente para su vínculo a C24;
RC16 mantiene ese requisito y devuelve la evaluación pendiente, no una versión
inventada. Su llamada RC15 no lee el archivo si ese faltante bloquea el vínculo.

La exigencia procede del perfil RC15, no de una prohibición universal de consultar
metadatos sin versión. La prueba independiente del DOCX no fuerza la admisión
del vínculo. No se deduce una edición de un nombre, fecha de descarga, propiedades
OOXML, revisión de catálogo o hash. Tampoco se usan valores como 0, actual o
sin_version para sustituir silenciosamente a None.

Una edición real requeriría una declaración verificable del publicador que
identifique producto/recurso y documento correspondientes, su edición o política
de versionado y alcance aplicable, con procedencia y revisión legítima. Su
obtención futura podrá basarse en documentación pública o respuesta institucional
por un procedimiento expresamente autorizado, o evidencia aportada por su
responsable. RC16 no ejecuta ese procedimiento. Si el publicador no versiona,
la evidencia de esa política requerirá otra decisión contractual; no se cambia
automáticamente el significado de None. Las ediciones ficticias solo se usan
dentro de fixtures identificadas como tales.

## Interfaz y unidad de entrega

Acceso experimental:
[herramientas/primer_uso_m26_rc16.py](../herramientas/primer_uso_m26_rc16.py),
versión propia **0.1.0**. Sin CLI general ni reexportación desde src.

```python
comprobar_primer_uso_m26(informe, *, solicitud_esperada, cotejador)
```

Exige InformeVinculoRC15 completo, SolicitudVinculoRC15 esperada y
CotejadorDocumental nativo. Rechaza None, ExpedienteProducto aislado, diccionarios,
booleanos/callbacks y componentes anidados de tipos ajenos antes de leer el DOCX.
La solicitud esperada liga proyecto/contexto, objeto/revisión, recurso/producto,
finalidad, operación, afirmación/documento, edición y control por sus contratos
nativos. Un informe de otro snapshot no se reinterpreta como el esperado.

El resultado **ComprobacionPrimerUsoM26** contiene referencias tipadas a:

- solicitud_esperada, sin duplicar sus campos;
- aportado, el informe completo recibido, **el mismo objeto**, sin reescribirlo;
- actual, el informe completo nuevo producido por RC15, o None si el rechazo
  anterior impide iniciar ese cotejo;
- diagnosticos propios de recepción, en DiagnosticoAdaptacion nativo.

Se vuelve a invocar vincular_producto_rc15; no se acepta la clasificación del
informe aportado como sustituto de esa comprobación. Se contrastan restricciones
y diagnóstico documental con el recálculo. En casos estructuralmente aptos se
contrastan también los diagnósticos nativos, expediente y cotejo. Un cotejo no
reproducido queda pendiente; no se inventa una acusación de autoría o manipulación.

No se elimina una causa adversa previa porque una nueva lectura sea favorable.
El receptor no redefine los estados RC15 ni relaja sus condiciones. Si falta el
informe completo se rechaza la entrada: no se reconstruye a partir del expediente.

## Restricciones y diagnósticos sin pérdida

ExpedienteProducto solo contiene producto, documentos y afirmaciones. No contiene
la operación/contexto/artefacto completos, revisión aportada, cotejo físico,
restricciones estructuradas con orígenes ni todos los diagnósticos RC15.
Los pendientes textuales de la afirmación no sustituyen esos datos.

El resultado RC16 conserva **ambos informes íntegros**. Su vista restricciones
concatena los conjuntos originales; no fusiona, rebaja, elimina o convierte en
notas un BLOQUEO_USO_DEL_RESULTADO. La repetición entre lecturas no es una segunda
evidencia independiente. Los contextos, fuentes, licencias y restricciones
documentales permanecen asimismo en sus objetos nativos dentro de los informes.

diagnosticos_completos incluye causas aportadas, propias de RC16 y actuales.
La contradicción prevalece sobre faltantes; la presencia de un faltante impide
APTO_ESTRUCTURALMENTE. Un expediente o informe con restricciones suprimidas no
supera el contraste. Las causas adicionales del informe anterior se conservan,
aunque no sean necesarias para producir el diagnóstico actual.

Esta obligación se garantiza **en la entrada explícita RC16**. No se altera el
contrato general del verificador C24, que sigue aceptando ExpedienteProducto.
No se afirma que sea imposible para otro llamador extraerlo y omitir el receptor;
ese uso queda fuera del perfil y no acredita M26. No hay un control universal
de permisos o protección frente a código Python hostil.

## Estados y fronteras

| Dimensión | Regla del alcance |
|---|---|
| estado_coherencia | EstadoAptitud nativo: APTO_ESTRUCTURALMENTE, PENDIENTE_DE_EVIDENCIA o INCOMPATIBLE según ambos informes y el contraste |
| estado_uso | INCOMPATIBLE si la coherencia lo es; en los demás casos PENDIENTE_DE_EVIDENCIA: las fixtures no acreditan un uso real revisado |
| Uso/revisión humana/autenticidad/ciencia/permiso | Flags False no configurables por constructor; no hay una vía de aprobación automática |
| Expediente C24 | El generado por RC15 sigue con PRODUCTO DECLARADA y pendientes; RC16 no crea una afirmación científica favorable |

Identidad nominal declarada, coherencia contractual, documento disponible,
integridad física contra control, procedencia aportada, autenticidad institucional,
revisión humana legítima, diagnóstico documental, afirmación de aplicabilidad,
permiso y ciencia son dimensiones separadas. La matriz enlazada asigna evidencias,
pendientes, responsables funcionales y consecuencias sin sustituirlas entre sí.

La revisión sintética no prueba intervención humana. El cotejo SHA/literal no
prueba autoría o equivalencia editorial. Un APTO de coherencia no autoriza otra
finalidad. El resumen público solo muestra estados, versión, cantidad de causas
y flags fijos; no textos/rutas/referencias recibidas. El informe completo es
interno y no debe publicarse como log o credencial. La conversión a bool se rechaza.

## Conservación y límites

Las referencias nativas inmutables conservan la unidad **en memoria del proceso**.
No se promete persistencia entre sesiones o recuperación tras apagado. RC6/RC10
y 85-J/K tienen perfiles cerrados que no incluyen InformeVinculoRC15 ni la
composición RC16; no se añade un tipo, se aplana a JSON QA o modifica SQLite 85001.
No existe un serializador durable aprobado para este informe completo. Esa
responsabilidad queda pendiente antes de prometer conservación durable.

RC1/RC2/RC4 aportan contexto, perfil, artefacto y restricciones. El cotejador y
RC15 hacen las comprobaciones existentes. RC8/RC9/RC14 describen otros cierres o
precondiciones y no sustituyen fundamento documental o humano. No se crean
almacenes, catálogos, un segundo grafo, parser o infraestructura de procedencia.

M26 sigue **PENDIENTE**, con recepción experimental acotada C20 → C24. Los usos
que exigen edición real, revisión humana legítima, autenticidad pertinente o
contrato durable no disponible permanecen pendientes. C20 → C21/C19 no se
implementan en RC16. No se inicia ningún núcleo científico ni RC17.
