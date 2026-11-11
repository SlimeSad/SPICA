# PASO 85-E — Auditoría del perfil y consistencia entre lotes

Fecha: **2026-11-11, America/Lima**. Conciliación experimental **0.1.0**.
Dictamen y pruebas: [cierre experimental](cierre_experimental_qaqc_paso85e.md).
No autentica procedencia ni autoriza operaciones científicas.

## Recuperación y alcance de auditoría

Git inicial limpio, rama **feature/suadc-http**, HEAD **7515d75**, «SUADC:
consumidor seguro de exportaciones QAQC nivel 0»; PASO 85-D consolidado.
Se revisaron [exportador](../src/spica/calidad/exportacion.py),
[consumidor](../src/spica/calidad/consumo.py),
[contrato de consumo](contrato_consumo_qaqc_paso85d.md),
[piloto 85-D](piloto_consumo_qaqc_paso85d.md),
[modelos QA](../src/spica/calidad/modelos.py),
[restricciones](../src/spica/calidad/restricciones.py),
[motor](../src/spica/calidad/motor.py) y pruebas 85-A…85-D.
No existía una función equivalente de comparación entre informes.

Se crea [conciliacion_lotes.py](../src/spica/calidad/conciliacion_lotes.py) y
[sus pruebas](../tests/test_conciliacion_qaqc_85e.py), sin cambiar contratos
anteriores, exportador, consumidor, motor, reglas o restricciones. No se cambia
el JSON 0.1.0 para ocultar incompatibilidades ni se crea persistencia.

## Perfil aceptado frente al generado

El consumidor reconstruye únicamente contratos de datos conocidos y exige
igualdad del documento recibido con una reexportación real. Por construcción,
la representación canónica aceptada debe ser generable por el exportador con
esos datos; no se encontró una ampliación estructural inadvertida. Esta es una
propiedad del perfil y pruebas actuales, no prueba de autenticidad ni garantía
de cobertura adversarial absoluta.

| Aspecto auditado | Diferencia observada | Impacto y decisión |
|---|---|---|
| Versiones | Exportador admite emisor null y versiones semánticas de descriptores; consumidor exige QA/regla 1.0.0, emisor 1.0.1, política 1.0.0, JSON 0.1.0 | Perfil más estrecho, deliberado y documentado en 85-D; sin migración |
| ID de regla | Exportador representa IDs hasta su presupuesto textual/validación de 4096; consumidor exige máximo 128 | Restricción técnica adicional, baja; las 22 reglas existentes caben |
| Coherencia de valores | Exportador puede representar una declaración cuyo objetivo contradiga el registro; consumidor la rechaza | Restricción adicional, media y favorable a la consistencia; no se altera el sobre histórico |
| Configuración declarada | Exportador no demuestra que se utilizara; consumidor exige pertenencia de regla/campo si se aporta | Perfil más estrecho, media; tampoco demuestra ejecución efectiva |
| Estado y derivados | Cinco estados nativos, estado de evaluación, diagnóstico, detalle y campos derivados se preservan y contrastan | Sin ampliación; no hay conversión a aprobación científica |
| Restricciones | Igualdad de grupos, códigos, tipos, operaciones, motivos y orden frente a política 85-B | Sin ampliación; no se reconstruye silenciosamente una omisión |
| Huellas e identidad | Se recalculan mediante el exportador existente | Coherencia técnica, no prueba de origen o integridad física |
| Cardinalidad | Un paquete por resultado; duplicados canónicos se contabilizan sin duplicar aceptados | No acredita que un productor haya emitido todas las condiciones previstas |
| Unknown/null | Configuración, escenario e inventarios pueden ser desconocidos según su contrato | Desconocimiento conservado, no completitud o aplicabilidad demostrada |
| Límites | Consumidor agrega presupuestos de lote, objetos, nodos y restricciones | Más estrecho que la representación aislada del exportador |
| Espacios, orden de claves y escapes JSON | Pueden diferir de los bytes literales emitidos y conservar los mismos datos canónicos | Compatibilidad sintáctica explícita, baja; no amplía campos/tipos ni normaliza observaciones |
| Descriptor ficticio o declaración fabricada coherente | Puede pasar ambos componentes si respeta el perfil | Limitación de confianza, media; ninguno acredita registro, ejecución o autenticidad institucional |

Se ejecutaron casos diferenciales concretos: base aceptada; emisor desconocido,
regla 1.0.1, ID de 129 caracteres, objetivo contradictorio y configuración ajena
exportables pero rechazados por consumo. Las variantes sintácticas recuperaron
el mismo JSON canónico. Pruebas nuevas verifican también claves superiores
cerradas y rechazo de un campo autorizado añadido.
No se identificó un defecto crítico que exigiera rediseño o corrección de los
componentes anteriores. Las diferencias no se ocultan cambiando el esquema.

## API y revalidación de los informes

```python
from spica.calidad.conciliacion_lotes import LoteQA, conciliar_lotes

# a y b son InformeConsumoQA recibidos explícitamente, sin cargar archivos.
informe = conciliar_lotes((LoteQA("lote-A", a), LoteQA("lote-B", b)))
```

La función recibe una tupla explícita de **dos a ocho** LoteQA, etiquetas lógicas
ASCII de hasta 128 caracteres y un InformeConsumoQA por lote. Usa los límites de
consumo existentes; pueden aportarse límites tipados de revalidación. No recibe
rutas ni inventa un formato JSON nuevo para transportar lotes.

No confía solo en estado=VALIDO. Comprueba tipo exacto, versiones, conteos enteros
sin booleanos, documentos y metadatos acotados, ausencia de problemas y coherencia
aritmética. Vuelve a llamar consumir_exportaciones sobre los documentos aceptados
y exige coincidencia del informe, sus documentos canónicos y restricciones.
Los documentos adulterados bajo un informe marcado válido se rechazan como
comparación no disponible; no se reparan.

Los duplicados exactos originales ya no están en los documentos únicos. Su número
solo se contrasta aritméticamente (recibidos = aceptados + duplicados), con los
topes del consumidor; el historial de transporte no se autentica. El resumen
los llama **recibidos_declarados/duplicados_declarados**. La revalidación demuestra
coherencia actual, no que el informe provenga de una llamada histórica auténtica.

Cada lote conserva documentos completos y restricciones en un ResumenLoteQA
inmutable, incluso si existe un conflicto. No se devuelve un lote fusionado,
no se suprime evidencia contradictoria ni se guarda estado entre llamadas.
Hasta ocho revalidaciones están acotadas por LimitesConsumoQA: con valores
predeterminados, cada lote tiene máximo 256 documentos y 4 MiB de entrada.
La comparación examina pares de lotes y sus índices; no construye un registro
general de identidad. MemoryError/RecursionError producen no comparabilidad.

## Identidades y equivalencia experimental

| Identidad | Definición y límite |
|---|---|
| Evaluación | (espacio_id, evaluacion_id) declarado; otra ejecución independiente requiere otro ID |
| Lote | Etiqueta declarada de una colección inmutable, separada de evaluación; huella SHA de sus documentos canónicos únicos ordenados |
| Escenario | escenario_id dentro de evaluación; null se conserva sin inventarlo |
| Entrada | Evaluación + escenario + entrada_id; registro y posiciones deben ser coherentes al reutilizarla |
| Resultado | resultado_id 85-C, que incorpora contexto, entrada/posición, regla/campo y versiones |
| Regla/campo/versión | Identifican la comprobación dentro de su entrada; no son identidad de estación o evento ambiental |

La huella de lote es SHA-256 de los JSON canónicos ordenados por resultado_id,
unidos con LF y sin LF final. No incluye su etiqueta ni duplica miembros por
repeticiones de transporte. Se calcula progresivamente, sin archivo. No es una
identidad institucional ni firma de origen. La igualdad se decide comparando
**documentos completos**, no solo hashes, códigos o valores literales.

Equivalencia de representación requiere mismo resultado_id y el mismo JSON
canónico completo. Dos lotes coinciden totalmente si contienen exactamente los
mismos documentos únicos. Esa coincidencia admite configuración desconocida
idéntica, pero no acredita que una evaluación pueda reproducirse científicamente.
Una entrada con contenido igual y otro ID sigue siendo otra entrada.

Entre evaluaciones distintas no hay un mapa de correspondencias acreditado:
no se alinean filas por número, ID original, valores, estación o hash. Si sus
ámbitos difieren, se informa no comparabilidad, conservando las coincidencias
parciales o conflictos que sí pudieron observarse. La misma comprobación con
contextos completos distintos tampoco se iguala; null no equivale a inventario
declarado vacío. Una comparación futura necesitaría correspondencia explícita
y revisada, fuera de este incremento.

## Política de colisiones y estados

| Caso | Tratamiento |
|---|---|
| A: lotes idénticos repetidos | COINCIDENCIA; se conservan ambos resúmenes, incluso con etiqueta repetida |
| B: resultado reproducido legítimamente en lotes parcialmente solapados | Coincidencia de ese resultado; conjuntos distintos pueden ser COMPATIBLES, sin afirmar completitud |
| C: mismo resultado_id, contenido distinto | CONFLICTO, ambos documentos preservados |
| D: misma entrada con reglas diferentes | COMPATIBLES si registro/ámbito son coherentes; no equivalentes |
| E: regla/campo de evaluaciones distintas | NO_COMPARABLE sin correspondencia, no coincidencia inferida |
| F: versión no admitida | Informe no utilizable al revalidar; NO_COMPARABLE, sin migración |
| G: restricciones diferentes bajo mismo resultado_id | CONFLICTO cuando ambos son válidos individualmente; si fueron adulteradas fuera del perfil, NO_COMPARABLE al revalidar |
| H: entradas distintas, valores iguales | Se conservan y pueden coexistir como COMPATIBLES; no se deduplican |
| I: lotes válidos separados con entrada/resultado contradictorio | CONFLICTO entre lotes; validez individual no implica coherencia conjunta |
| J: contexto insuficiente o declaraciones distintas | NO_COMPARABLE para equivalencia, sin completar metadatos |

COMPATIBLES expresa coexistencia sin conflicto observado en un ámbito común, no
igualdad de observaciones o cobertura completa. Se contrastan también registros
reutilizados y la etiqueta de lote: misma etiqueta con otros miembros es conflicto.
Los hallazgos de coincidencia se cuentan **por par de lotes y resultado**, no como
nuevas evaluaciones ambientales; tres copias generan tres pares de comparación.

Precedencia global: **CONFLICTO > NO_COMPARABLE > COINCIDENCIA > COMPATIBLES**,
con COINCIDENCIA reservada a colecciones idénticas. No comparabilidad o un lote
inválido no elimina un conflicto ya observado. InformeConciliacionQA conserva
resúmenes, suma de documentos examinados por lote, coincidencias, conflictos,
causas de no comparabilidad y límites de confianza; no devuelve permiso científico.

## Procedencia independiente y cierre

Se distingue sintaxis JSON, contrato aceptado, coherencia de IDs, coincidencia
entre lotes y huella técnica de evidencia física independiente, ejecución real,
autenticidad, validez científica y autorización. Las primeras verificaciones no
demuestran las últimas. No se implementan firmas digitales, certificados,
registros remotos o servidores de confianza.

Una futura integración necesitaría, bajo autorización separada: original y
persistencia técnicamente comprobados; publicación, edición/licencia y alcance
editorial revisados; correspondencia independiente de recurso/entrada/contexto;
registro de ejecución efectivo con versiones/configuración/entradas; aplicabilidad
y revisión científica de la regla; y autorización concreta del uso. Recalcular
hashes del JSON no sustituye esas evidencias. Nada se verifica físicamente ahora.

El [informe de cierre](cierre_experimental_qaqc_paso85e.md) evalúa los criterios
observados y recomienda el alcance de un eventual 86-A. No modifica las 29
brechas, datos originales ni habilitaciones anteriores.
