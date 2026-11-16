# RC7 — Evidencias de cierre, piloto y limitaciones

Fecha: 2026-11-16, America/Lima. Contrato RC7 0.1.0.
[Integración](integracion_artefactos_coordinacion_rc7.md),
[auditoría](auditoria_arquitectonica_rc7.md),
[pruebas](../tests/test_integracion_artefactos_rc7.py).

## Garantías distintas

| Categoría | Qué se conserva/comprueba | Qué no acredita |
|---|---|---|
| Declaración | Contextos, descriptores, método/versión/parámetros, estado y referencias aportados | Que el método se ejecutó |
| Consistencia contractual | Identidades, revisiones, snapshots, productor, linaje, vínculos y políticas compatibles | Autenticidad de quienes los proporcionan |
| Integridad física | Lectura/tamaño/SHA realizada por RC6 a su fecha; metadatos coherentes reusados por RC7 | Vigencia posterior, conclusión del productor o significado científico |
| Evidencia de ejecución | Resultado nativo aportado de un componente identificable, con correspondencias y límites de su contrato | Certificación universal o resistencia a falsificación coordinada |
| Cierre QA | InformeQA y vínculos que cumplen las reglas de RC1/RC3 | Calidad científica de todas las observaciones o ejecución de todas las reglas posibles |
| Validez científica | Requiere criterios/aplicabilidad/evidencia científica propios | No se obtiene de un hash ni de RC7 |
| Autenticidad | Requiere mecanismo adicional de confianza | No se implementa con DTO congelados, control de generación o SHA |

RC6 conserva exclusivamente operaciones descriptivas y no incorpora cierres QA.
Su recuperación exitosa no puede fabricarlos. RC7 admite como evidencia
**adicional en memoria** un CierreQA nativo ya producido y aportado en RC3; no
lo inserta retroactivamente en el inventario o codec RC6.

## Evidencia QA admisible

Se delega en inspeccionar_composicion y sus validadores existentes:

- Identidad exacta operación/snapshot de los vínculos, pertenencia y procedencia,
  reglas/configuración/límites, referencias, duplicados y cuotas.
- Correspondencia entre InformeQA, resultados emitidos, registros, conteos,
  reglas ejecutadas y evaluaciones incompletas.
- Cierre completo: operación CONCLUIDA, informe COMPLETA, recorrido completo,
  motivo eof, registros finalizados iguales a examinados y resultados vinculados.

RC7 contrasta además el hash de referencia del QA aportado con el contenido
realmente verificado por RC6 para las entradas vinculadas. Un cierre nativo
coherente con hash desconocido no demuestra esa asociación: el cierre se conserva
como historia, pero la dependencia queda pendiente en esta integración.

Ni siquiera un conjunto coherente de DTO demuestra por sí mismo que el motor
leyó ese archivo. El ensayo sí invoca el lector y motor sobre la copia conservada;
el modelo de proceso confiable y ausencia de autenticidad siguen explícitos.

Sin InformeQA/vínculos, el diagnóstico rc6_no_aporta_cierre_qa_nativo informa el
límite. Una operación QA futura puede estar preparada estructuralmente sin tener
aún resultados; sus dependientes no quedan acreditadas por esa preparación.
CONCLUIDA declarada sin cierre admitido conserva el pendiente nativo RC3.

Para productores no QA falta un contrato pertinente de cierre: identidad de
componente/método/versión, ejecución, entradas/salidas/revisiones y evidencia
comprobable del resultado técnico, límites y finalización. No basta añadir una
bandera de éxito o reutilizar InformeQA como certificado universal. RC7 no diseña
un ejecutor ni implementa ese contrato futuro.

## Estados y restricciones conservados

Se mantienen separados ejecución histórica RC1, estado lógico RC4, publicación
RC5, integridad a fecha de recuperación RC6, conservación, revisión científica y
habilitación declarativa RC3. La vista RC7 solo añade condiciones; no altera los
contextos, los resultados QA ni los informes históricos.

PARCIAL, FALLIDA y CANCELADA no se convierten en CONCLUIDA. Una salida PARCIAL
puede tener bytes técnicamente completos y SHA correcto: eso no completa su
producción ni su significado científico. Un cierre QA admitido tampoco vuelve
a habilitar su operación ya concluida para repetirla.

Los bloqueos de QA y artefactos se conservan con origen y pasan a dependientes.
Un bloqueo nuevo en la vista de una QA con cierre coherente impide satisfacer
la dependencia, sin borrar ese informe ni negar el hecho histórico registrado.
Recuperación o traslado no conceden permisos ni acreditan revisión científica.

## Piloto sintético

Se usan cinco artefactos: originales independientes A/B, una copia lógica A,
preparado y derivado parcial A. Los cinco cuerpos son la misma fixture CSV
suministrada explícitamente; no son salidas de una transformación ambiental ni
se ejecuta el método productor declarado. Cada archivo se materializa por RC5 y
se incorpora a una generación RC6 con nombre/inodo propio. No se fusionan por SHA.

| Cuerpo sintético | Evidencia |
|---|---|
| Encabezado de 16 campos + una fila ficticia | 218 bytes |
| SHA-256 esperado y contrastado con lecturas físicas RC5/RC6 | e5f6011f37be1ce0b1cda080b846ca1c42c5d787eab12b0568067fbccbdc3429 |
| Regla QA0 seleccionada | L0-EST-001, estructura recibida coherente |
| Informe realmente producido sobre datos-000.bin de la generación | 1 registro examinado/finalizado, 1 resultado, COMPLETA/eof |
| Valores originales | HORA=10000, UBIGEO=01234.0; sin reconstrucción ni normalización |

Proyecto B comparte contenido, con identidad/contexto/objeto propios. Se mantiene
fuera de la composición A; no se transfiere identidad, política o permiso por SHA.
La composición candidata usa otro ID que la histórica, preservando sus productores
y dependencias, y añade QA previa/comparación explícitas sin persistirlas en RC6.

| Operación | Estado histórico/declarado | Evidencia y resultado |
|---|---|---|
| preparar | CONCLUIDA | Declarada, sin cierre técnico no QA admitido; no satisface derivar |
| derivar | PARCIAL | Estado/salida parcial permanecen, aunque el archivo se verifica físicamente |
| independiente | DECLARADA | Original A con otra identidad; habilitada declarativamente para inspección |
| qa-previo | CONCLUIDA tras ejecutar el motor existente en el ensayo | Cierre completo nativo aportado y cotejado, sin volver a habilitar QA para ejecución |
| comparar | DECLARADA | Perfiles RC2 compatibles y dependencia QA con evidencia admisible; habilitada declarativamente |

En la variante con QA genuino, las habilitadas son **independiente y comparar**.
El informe global puede permanecer PENDIENTE_DE_EVIDENCIA por las otras ramas;
eso no oculta la rama válida ni convierte en aptas las pendientes. Sin QA, esa
dependencia no se acredita: descriptor, archivo y hash no sustituyen resultados.

## Procesos y traslado

Un Python A crea/conserva las fixtures y termina normalmente, retirando su raíz
RC5. Python B inicia después, recupera por la API RC6 y construye vínculos desde
los contratos recuperados, sin factories de tests. Inspecciona la composición
histórica: **solo independiente** queda habilitada; no inventa QA inexistente.

La barrera de B se instala antes de importar SPICA y rechaza sockets, SQLite,
escrituras/mutaciones y acceso a SPICA_DATOS. Se copia la generación a otra raíz
TEMP, se dispone únicamente la fuente propia con comprobación de nombres y sin
recursión, y otro B debe producir el mismo resultado. Ambos TEMP comparten equipo,
cuenta y dominio de fallo; no se acredita portabilidad entre SO o custodia externa.

El ensayo QA genuino es independiente de esa limitación: se ejecuta en memoria
del proceso de ensayo sobre el archivo conservado y se aporta a la candidata.
No se altera el formato RC6 para que B recupere un InformeQA que no contiene.

## Escenarios adversos y límites

Se ensayan generación íntegra/incompleta/corrupta, archivo incluido ausente,
referencia externa no comprobable, comprobaciones omitidas/duplicadas/incoherentes,
identidades de proyecto/operación/entrada/artefacto/revisión incompatibles, productor
redefinido/ambiguo y linaje alterado, estados parciales/fallidos/cancelados y
dependencias históricas omitidas.

Los cierres QA se prueban con otra identidad, conteos/EOF contradictorios,
recorrido parcial, ausencia de cierre y hash desconocido. Se incluyen bloqueos
omitidos del contexto candidato, conflictos de restricciones, usos desconocidos,
perfiles incompatibles/pendientes/redefinidos y referencias no emitidas.

Los límites/cancelación/versiones y lectura entre procesos se prueban sin red.
La prueba de pureza niega E/S, SQLite, sockets y llamadas al motor desde el
adaptador; los resultados y JSON QA nativo deben permanecer idénticos.

Persisten confianza en evidencia aportada, reloj/proceso, disponibilidad posterior,
controles de acceso, autenticidad, TOCTOU/durabilidad del almacén experimental y
necesidad de un contrato de cierre no QA. Una comprobación fechada no es una
garantía de lectura futura. No se abre RAW/staging/SQLite operativo para afirmar
integridad nueva ni se promueve el cierre de arquitectura por aprobar pruebas.
