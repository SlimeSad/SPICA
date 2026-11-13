# RC3 — Ensayo transversal y conexiones comprobadas

Fecha **2026-11-13**, base **496c740**. Contrato **0.1.0**.
[Contrato](contrato_composicion_operaciones_rc3.md),
[auditoría](auditoria_arquitectonica_rc3.md),
[pruebas](../tests/test_coordinacion_rc3.py).

## Qué se ejecutó y qué se inspeccionó

Se ejecutaron el lector CSV y EvaluadorNivel0 **existentes**, con la regla
L0-EST-001, sobre un encabezado de 16 campos y una fila completamente sintética.
El archivo temporal exclusivo se cerró y eliminó. Se obtuvo InformeQA y un
ResultadoQA reales del componente; luego se construyeron vínculos RC1, perfiles
RC2 y composiciones. No se fabricó un Informe85G/H ni se volvió a recorrer
HTTP→RAW. Construir o inspeccionar RC3 no llamó al lector ni al motor.

Las pruebas reutilizan fabricantes RC1/RC2. Sus huellas son declaraciones de
ensayo, sin atribuirles verificación física. Para comprobar además una entrada
con bytes/huella coincidentes se ejecutó un piloto puntual separado, sin cambiar
código ni añadir datos institucionales:

| Comprobación física, exclusivamente de fixture TEMP | Resultado |
|---|---|
| Tamaño CSV preparado y almacenado | **214 bytes**, contenido idéntico |
| SHA-256 calculado sobre esos bytes y contrastado con el archivo temporal | `8cf7000e1e36ee04e44d3b6eafc5a95fa1a172df1c9bc45a007bbf725023470c` |
| Metadatos de entrada del piloto puntual | SHA/tamaño declarados coincidentes con esa fixture |
| QA0 realmente ejecutado | 1 registro examinado/finalizado y 1 resultado; recorrido COMPLETA/eof |
| Cuotas declaradas QA | 4 registros, 8 resultados |

Esta verificación física pertenece al **ensayo**, no es una función nueva del
inspector RC3 ni verificación del RAW. Ningún archivo PNDA fue abierto. Después
de ejecutar QA se instaló una barrera de auditoría que rechaza red, SQLite y
escrituras durante construcción/cotejo de las composiciones.

## Escenario principal

Proyecto A conserva una entrada con una huella declarada; dos perfiles locales del
encabezado sintético, versiones fixture-1 y fixture-2, describen el campo ID sin
atribuirlo a un producto institucional aprobado. El propósito selecciona solo
TIPO; no inventa unidades, frecuencias, HORA, UBIGEO ni aplicabilidad científica.

| Operación A | Estado RC1 conservado | Dependencia | Evidencia / resultado de coordinación |
|---|---|---|---|
| qa-previo | CONCLUIDA, declarada después de la ejecución en el ensayo | Ninguna | InformeQA y vínculo cotejados; cierre completo coherente aportado. No se vuelve a habilitar para ejecutar |
| independiente | DECLARADA | Ninguna | Habilitada declarativamente para describir; no ejecutada |
| comparar | DECLARADA | qa-previo y su referencia resultado-0 | RC2 recalculado apto; cierre técnico de la predecesora aportado; habilitada declarativamente, no ejecutada |

Orden observado: **independiente, qa-previo, comparar**. Habilitadas declarativamente:
**independiente, comparar**. El orden incluye la operación ya cerrada como
precedencia, sin proponer su repetición.

Las restricciones se conservan por código con sus referencias de origen:
alcance_estructural, bloqueo-fixture, sin_equivalencia_editorial y
sin_validacion_cientifica. El diagnóstico apto no concede permisos para usos
excluidos. Al declarar acreditar_aptitud_cientifica como uso de comparar, el
bloqueo QA heredado impide su habilitación.

Proyecto B usa contexto/objeto/entrada independientes y la misma huella declarada
de contenido sintético; su composición descriptiva permanece separada. Mezclar
una operación B en la composición A produce diagnóstico de contexto incompatible.
No se transfieren permisos, responsabilidades o identidad por compartir bytes/hash.

## Variantes y rechazos

| Caso | Resultado comprobado |
|---|---|
| Perfiles respaldados coincidentes | APTO_ESTRUCTURALMENTE para la finalidad seleccionada |
| Tipo distinto en segundo perfil | INCOMPATIBLE; independiente sigue habilitada |
| Tipo desconocido | PENDIENTE_DE_EVIDENCIA; no se eleva a apto |
| Predecesora solo lista/PLANIFICADA | Dependiente pendiente; no basta el orden del DAG |
| CONCLUIDA y referencia inventada, sin cierre técnico | Dependiente pendiente; referencia declarada no es evidencia de ejecución |
| Informe con conteo o EOF contradictorio | Cierre rechazado; no satisface dependencia |
| Informe/vínculo de otro proyecto, operación o snapshot | Rechazado; no se realinea por igual SHA |
| Ejecución QA interrumpida por max_resultados=1 | Informe INCOMPLETA, estado PARCIAL, resultado emitido y referencia conservados; dependiente no habilitada |
| Etiquetar ese prefijo como CONCLUIDA | Contradicción operación_concluida_con_qa_incompleta |
| Cierres técnicos de operaciones descriptivas | No hay adaptador aprobado en RC3; dependientes pendientes |
| Nodo, arista, extremo inexistente o autoarista duplicados; ciclo | Error global explícito, orden vacío y sin habilitaciones |
| Cuota de nodos/aristas/profundidad/descriptores o suma QA excedida | Sin habilitación; sin reservar recursos ni eliminar resultados |
| Bloqueo con alcance de uso desconocido | Aplicabilidad pendiente; no se descarta la restricción |
| Cancelación previa o durante cotejo | Sin habilitación, estados RC1 intactos, cierres y resultados RC2 ya obtenidos conservados |

La comparación y el cotejo de cierres no son autenticación. Un conjunto de DTO
falsificados coherentemente por código hostil no se convierte aquí en prueba
criptográfica. El ensayo demuestra llamadas reales con fixtures y conservación
de relaciones, no veracidad universal de cualquier objeto recibido.

## Evidencia de integración y recursos

Se probaron los tres estados RC2, entradas canónicas por referencia, dos proyectos,
propagación transitiva, restricciones alteradas, presupuestos comparables y
separación de cuotas/contadores aportados. ResultadoQA y JSON QA 0.1.0 permanecen
idénticos antes y después del cotejo; HORA=10000 y UBIGEO=01234.0 se conservan
literalmente. No hay transformaciones ni ejecución de QA/QC científico.

Los procesos de importación/cotejo en dos órdenes instalan una barrera antes de
importar SPICA: niegan sockets, sqlite3.connect, lecturas operativas reconocibles
y aperturas de escritura. Otros casos niegan explícitamente llamadas al motor QA,
planificador y transporte durante inspección. No son una sandbox general para
Python hostil, pero ejercitan las rutas implementadas sin efectos.

Los temporales sintéticos usan with y se comprueba su ausencia al salir. La
primera pasada dentro del sandbox dejó un único directorio privado vacío por
PermissionError; se verificó su ruta, ausencia de enlaces y contenido vacío y se
retiró sin recursión ni cambios de permisos. Las pasadas posteriores usaron el
intérprete fuera del sandbox; no se tocó RAW, staging o SQLite operativos.

El alcance no incluye transporte, almacenamiento, persistencia de composición,
autorización o exportación de estas envolventes. Los resultados técnicos previos
pueden relacionarse; no se publican nuevos derivados ni se conserva una traza
operativa general. El registro de cierre de pruebas está en la auditoría RC3.
