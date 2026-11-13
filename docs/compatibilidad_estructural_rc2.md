# RC2 — Compatibilidad estructural para una finalidad

Fecha: **2026-11-13**. Contrato/comparador **0.1.0**, base **ac9c6fd**.
Véanse [contrato](contrato_perfiles_informacion_rc2.md),
[auditoría](auditoria_arquitectonica_rc2.md) y
[pruebas sintéticas](../tests/test_perfiles_informacion_rc2.py).

## Operación implementada

`comparar_perfiles(primero, segundo, finalidad, *, operacion=None)` compara dos
EntradaPerfil. Retiene sus ContextoEntrada, perfiles y finalidad completos.
No compara registros o archivos y no elabora un dataset combinado.

Una finalidad fija correspondencias uno a uno de campos, versiones admitidas,
aspectos requeridos y referencias opcionales. Comparar solo tipos no exige
unidades o espacio; comparar semántica no permite omitir identidad de variable.
Cambiar la finalidad genera otro diagnóstico, nunca una autorización.

## Estados y criterios

Se reutiliza EstadoAptitud en lugar de inventar un enum equivalente:

| Concepto solicitado | Estado devuelto RC2 | Condición |
|---|---|---|
| COMPATIBLE | APTO_ESTRUCTURALMENTE | Todos los requisitos seleccionados y sus respaldos están satisfechos por las declaraciones aportadas |
| INCOMPATIBLE | INCOMPATIBLE | Falta un campo requerido, versión no admitida, diferencia acreditada, definición contradictoria o restricción aplicable que impide esa finalidad |
| INDETERMINADO | PENDIENTE_DE_EVIDENCIA | No hay incompatibilidad demostrada para la finalidad, pero faltan declaraciones, respaldos o referencias suficientes |

La precedencia es incompatibilidad, luego indeterminación, luego compatibilidad.
Un resultado puede conservar faltantes aunque también tenga incompatibilidades.
DiagnosticoAdaptacion aporta código, campo y nivel. Su nivel CONTRADICCION se
usa también para un requisito contradicho por la estructura o política de la
finalidad; **no afirma una contradicción científica o institucional nueva**.

| Requisito seleccionado | Comparación | Límite |
|---|---|---|
| Campo y tipo | Presencia en el perfil y literal de tipo exacto con respaldo VERIFICADO | No se leen celdas, parsean números ni ensanchan entero a decimal |
| Variable y significado | Identidad fuente/producto/id_interno/codigo_original y significado literal respaldados | Igual nombre/columna no demuestra equivalencia. No hay correspondencias entre namespaces distintos |
| Medición y frecuencia | Literales de VariableCatalogo con respaldo_variable aportado | No se deducen de la unidad, cadencia de publicación o nombre |
| Unidad y dimensión | Estados coherentes y literales exactos con evidencia aportada; no aplicabilidad documental explícita | Diferentes unidades no son comparables directamente en esta finalidad, aunque una conversión futura pudiera existir |
| Faltantes | Conjuntos de marcadores documentados | No equivale None a vacío, no hay imputación, filtro ni sustitución |
| Calendario/agregación | Literales exactos con respaldo | No se construyen ventanas o series |
| Espacio/tiempo | Llamada al evaluar_aptitud existente con la dimensión solicitada | Se conserva ResultadoAptitud completo, incluidas evidencias, faltantes, restricciones y NO_EVALUABLE nativo |
| Identidad de recurso | Igualdad de IdentidadRecurso solo cuando la finalidad la exige | Recursos de nombres parecidos o mismo contenido no se fusionan |
| Identidad de contenido | Hash/tamaño declarados y evidencia INTEGRO aportada coherentes cuando se exige | RC2 no abre el archivo ni recalcula/verifica físicamente esos bytes |
| Identidad de sitio | Clave fuente/producto/código, respaldo y ausencia de ambigüedad, si se exige | No basta el mismo nombre o coordenadas. No ejecuta asociación GIS |
| Versiones/restricciones | Pares perfil/versión admitidos, definición consistente y unión sin rebajar restricciones | No es un registro global ni un sistema de permisos |

Para referencias ausentes el resumen RC2 usa PENDIENTE_DE_EVIDENCIA y mantiene
NO_EVALUABLE dentro de aptitud_referencias. Para resoluciones distintas respaldadas,
RC2 añade incompatibilidad de alineación literal; el evaluador previo puede dar
PENDIENTE_DE_EVIDENCIA por correspondencia no documentada. Son finalidades con
alcances distintos, ambos resultados se conservan sin alterar el evaluador.

## Escenarios ejecutados

Todas las referencias, códigos, unidades y respaldos de estas fixtures son
**inventados**. Estado VERIFICADO en ellas simula evidencia aportada, no revisión
de una institución. El hash `a` repetido es una declaración de ensayo, no un hash
calculado sobre un original. No se accedió a CSV, XLSX o DOCX PNDA.

| Caso sintético | Finalidad / condición | Resultado observado |
|---|---|---|
| A | Dos perfiles completos con diez aspectos coincidentes y respaldados | APTO_ESTRUCTURALMENTE |
| B | Campo requerido omitido de un perfil | INCOMPATIBLE, campo_requerido_ausente |
| C | Tipo decimal-literal frente a texto con respaldo | INCOMPATIBLE; sin conversión |
| D | u-ficticia frente a otra-u; misma dimensión ficticia | INCOMPATIBLE para cotejo directo |
| E | Unidad desconocida o solamente declarada | PENDIENTE_DE_EVIDENCIA |
| F | Instantes, periodos y convención UTC sintéticos completos | APTO_ESTRUCTURALMENTE; se retiene el resultado del evaluador anterior |
| G | HORA literal sin interpretación / datetime sin zona | PENDIENTE_DE_EVIDENCIA; originales intactos |
| H | Resolución horaria frente a diaria respaldadas | INCOMPATIBLE; no se agrega ni reinterpreta tiempo |
| I | Marcos espaciales documentados, incluso con coordenadas diferentes | APTO_ESTRUCTURALMENTE para preparación; no se exige ni declara coincidencia geométrica |
| J | Marco espacial ausente | PENDIENTE_DE_EVIDENCIA; nativo NO_EVALUABLE |
| K | Restricción bloqueante para la finalidad exacta | INCOMPATIBLE; restricción conservada |
| L | Versión local no admitida | INCOMPATIBLE; admitirla expresamente aún exige cotejar los campos |
| M | Proyectos distintos con SHA declarado compartido | Perfiles compatibles para estructura; identidades separadas. Exigir mismo contenido sin evidencia física aportada queda pendiente |
| N | Recursos de nombres similares con IDs distintos | Se conservan diferentes; INCOMPATIBLE cuando se exige mismo recurso |
| O | Unidad contradictoria con constatación aportada | INCOMPATIBLE aunque el literal coincida |
| P | NO_APLICABLE documentada en ambos perfiles | Compatible en ese aspecto; desconocida no sustituye NO_APLICABLE |
| Q | Variable de otro producto con el mismo nombre | INCOMPATIBLE para equivalencia semántica; no hay correspondencia acreditada |
| R | Mismo código de sitio en otro producto | INCOMPATIBLE al exigir mismo sitio; no se asocia por texto |
| S | Solo tipos requeridos, sin unidad/tiempo conocidos | Compatible para esa proyección estructural, sin afirmación semántica o científica |
| T | Encabezado QA0 existente en fixture, sin tipos acreditados | PENDIENTE_DE_EVIDENCIA; resultado y JSON QA anteriores sin cambios |
| U | Dimensión documentada con unidad desconocida | Se conserva la dimensión; PENDIENTE_DE_EVIDENCIA para cotejar unidades |
| V | Producto del recurso desconocido, producto de variable conocido | PENDIENTE_DE_EVIDENCIA; no se infiere el producto del recurso ni se declara un conflicto |

Además se comprobaron tipos de entrada inválidos, cotas, dataclasses congeladas,
determinismo, versión de contrato desconocida, campos duplicados, marcadores
reordenados, cambio de finalidad, conflicto de restricciones, procedencia faltante,
ámbitos, ambigüedad de sitio, catálogos fuera del recurso e integración RC1.

## Uso e interpretación

Las funciones `vinculo`, `perfil`, `campo` y `finalidad` del archivo de pruebas
son fabricantes de fixtures, no API de producción ni perfiles institucionales.
La finalidad completa usa diez aspectos; la variante estructural selecciona solo
TIPO. Las referencias temporales/espaciales se piden por separado y no son requisitos
implícitos de toda información ambiental.

Una finalidad estrecha no elimina restricciones ni transforma un recurso en
apto para otra finalidad. El resultado siempre conserva perfiles, entradas,
incertidumbres y restricciones; autoriza_operacion=False. Tampoco valida que
el consumidor futuro haya seleccionado una finalidad científicamente suficiente.
Ese control y cualquier aplicación institucional requieren revisión posterior.

El repertorio es deliberadamente conservador: sinónimos acreditables, traducciones,
unidades convertibles, distintos CRS o variantes de un tipo pueden requerir una
futura correspondencia documental. RC2 no las inventa ni resuelve metrología,
aplicabilidad científica, calidad de una observación, causalidad o equivalencia
editorial entre originales.
