# RC4 — Linaje declarativo e integración

Fecha: **2026-11-15**. Base **5b5b7d4**, contrato **0.1.0**.
[Contrato](contrato_artefactos_derivados_rc4.md),
[implementación](../src/spica/artefactos/linaje.py),
[pruebas](../tests/test_artefactos_rc4.py).

## Grafo y semántica

ProduccionArtefactos es una relación explícita N→M: las entradas declaradas
contribuyen a todas las salidas declaradas de una operación. Cada par origen/destino
tiene la misma operación, método/versión, respaldo, diagnósticos y restricciones de
esa relación; su tipo_vinculo es produccion_declarada y su versión RC4 es 0.1.0.
El tipo del destino distingue preparado y derivado. No se infiere la relación
por SHA, nombre, formato, proximidad temporal o posición de archivo.

Una salida con otro conjunto de entradas necesita otra operación productora;
una revisión no es una sustitución destructiva. El inspector no resuelve
conflictos ni fusiona salidas de operaciones distintas.

```mermaid
flowchart LR
  OA[Proyecto A: original r1] --> P[Operación declarada: preparar]
  P --> PA[Preparado r1: descriptor]
  PA --> D[Operación parcial: derivar]
  D --> DA[Derivado r1: descriptor parcial]
  OB[Proyecto B: otro original] -. mismo contenido declarado .- OA
```

La línea de contenido compartido no es una arista de procedencia ni dependencia.
El grafo real cotejado se expande únicamente desde las entradas/salidas explícitas.
El orden por capas, con desempate literal object_id/revision, sirve para inspección
y propagación, nunca para ejecutar operaciones. Un ciclo deja orden_linaje vacío.

El DAG de artefactos difiere del DAG de operaciones RC3. Para entradas producidas
por otra operación se exige dependencia RC3 explícita dentro de la misma
composición. Compartir un ancestro no inventa una dependencia. Una precedencia
válida no acredita que la operación haya terminado o escrito una salida.

## Integraciones y preservación

| Contrato | Cotejo realizado | Frontera |
|---|---|---|
| RC1 | Contextos/entradas canónicos por referencia; validar_relaciones; pertenencia MD; entradas exactas de la productora y referencias_resultado | Sin registro, transición o permiso nuevo. Una revisión necesita entrada distinguible |
| RC2 | EntradaPerfil íntegro; misma versión de perfil no admite definiciones distintas. RC3 ejecuta su comparador real cuando hay requisitos | Se preservan variables, unidades, marcos, incertidumbre y finalidad; no se exige equivalencia semántica no declarada ni se transforma contenido |
| RC3 | Se recalculan informes con inspeccionar_composicion. Productora es el mismo ContextoOperacion, no una copia alineada por ID | Se conservan requisitos/resultados RC2, restricciones QA, condiciones de cierre y dependencias. No se ejecuta motor ni nuevo orquestador |
| Integridad RAW aportada | RC1 contrasta activo, hash y tamaño declarados/observados | RC4 no abre rutas ni comprueba vigencia física; preparado/derivado no puede hacerse pasar por RAW |

Los informes RC3 originales calculados se mantienen completos. No se duplica su
algoritmo de cierre QA o comparador de perfiles. En RC4, una producción sin
composición está pendiente; si se aporta una composición que omite la productora,
hay contradicción. Una composición incompatible impide un informe global apto,
incluso si contiene otros nodos independientes coherentes.

## Restricciones y diagnósticos

Las restricciones locales provienen de EntradaPerfil (proyecto/entrada/perfil) y
de las adicionales del descriptor. Las heredadas incluyen operación, relación,
composición, compatibilidades, QA previo y todos los artefactos antecesores.
EvidenciaLocal no tiene un campo nativo de restricciones; cualquier política
adicional aportada con esa evidencia permanece explícita en la envolvente RC1
o en las adicionales del descriptor, sin deducir ni inventar permisos.

El resultado conserva dos grupos y ofrece una unión por código. Misma política
repetida se cuenta una vez, conservando orígenes descriptivos; esas etiquetas no
son pruebas independientes. Un código con contratos distintos produce excepción,
sin degradar un bloqueo. No se ofrece un campo para borrar políticas heredadas.

Se coteja el alcance exacto contra usos_declarados del nodo productor RC3. Si el
alcance es desconocido, se registra aplicabilidad pendiente. Un bloqueo aplicable
da contradicción estructural/política, sin diagnóstico científico. Los otros usos
mantienen políticas, sin convertirse en permisos. Ante ciclo se retienen todas
las políticas conocidas de forma conservadora: ese conjunto no acredita un linaje
válido. Los pendientes/contradicciones de un antecesor también llegan al destino.

## Piloto reproducible y evidencia realmente obtenida

La función piloto de las pruebas crea **cuatro descriptores**, dos proyectos
independientes, dos producciones y una composición RC3. Ambos originales comparten
un contenido explícito; el preparado/derivado solo proponen representaciones, con
contenido aún desconocido. La segunda producción es PARCIAL; su salida también.
Se conserva bloqueo-rc4 hasta el derivado. Todas las disponibilidades permanecen
DESCONOCIDA; el resultado global es PENDIENTE_DE_EVIDENCIA.

Se calculó realmente SHA-256 sobre **58 bytes ficticios en memoria**, sin archivo:

```text
e752ac22c40f261aa6f6d15f7e874ec2552120bf3191bb46c2c68cce66b507c9
```

Este cálculo prueba la identidad de esa cadena sintética; en ContextoEntrada es
una huella declarada, no comprobación de un activo físico. No hubo transformación,
original RAW nuevo, materialización, persistencia o ciencia en ese piloto.

Otra prueba llama al lector CSV y QA0 existentes mediante qa_real de RC3, sobre
un TEMP sintético propio retirado al salir. Vincula su informe real previamente
producido a RC3, conserva las restricciones QA hasta la salida RC4 y comprueba que
el ResultadoQA y su JSON nativo no cambian. Inspeccionar RC4 no ejecuta QA. Las
huellas de fabricantes históricos son declaraciones, sin atribuirles lectura
física del CSV. Esa prueba no convierte el informe QA en dataset derivado.

Las fixtures de EvidenciaLocal INTEGRO/AUSENTE/INCONSISTENTE simulan comprobaciones
aportadas para ensayar coherencia. RC4 no las produce ni autentica. Un tamaño cero
coherente se admite; una referencia histórica ausente no se promueve por su hash.

## Casos rechazados y diagnósticos

| Caso | Resultado |
|---|---|
| ID/tipo/versión/cota no admitidos, colecciones mutables | Excepción explícita, sin modificar entradas |
| Duplicado de object_id/revision, productora, ejecución o snapshot contradictorio | Inventario incompatible, conservando las declaraciones originales |
| Mismo contenido con hash/tamaño contradictorio; mismo hash con tamaños distintos | Contradicción; no fusiona ni corrige datos |
| Productora ausente, referencia inexistente o revisión no localizada | Contradicción; no busca una revisión parecida |
| Autoarista, ciclo o proyecto/contexto ajeno | Contradicción; sin linaje válido ni realineación por contenido |
| PREPARADO con identidad lógica del ORIGINAL | Contradicción incluso si cambia la revisión |
| Operación final sin evidencia de relación o sin cierre técnico admitido | Pendiente; FINAL_DECLARADO sin soporte declarativo suficiente es contradictorio |
| Salida final de operación parcial, fallida o cancelada | Contradicción; no se fabrica éxito |
| Política omitida en la salida | Se hereda desde ancestros; no se permite eliminarla |
| Bloqueo rebajado, perfil redefinido o referencia de resultado incorrecta | Excepción por conflicto de política o diagnóstico contradictorio según contrato |
| Unidad/tipo incompatible en requisito RC2 | Se conserva el resultado nativo incompatible; no se normaliza |

## Conservación y evolución pendiente

85-H tiene una traza de cierre de G; 85-J conserva informe/traza/referencia/manifiesto
de ese perfil, con codec de lista cerrada y SQLite 85001. El manifiesto 85-K exige
roles y campos exactos. Ninguno admite los tipos RC4 actuales: no se codifican,
guardan o restauran como si fueran G/H. JSON QA 0.1.0 tampoco representa este
inventario, sus identidades o restricciones adicionales.

Una etapa posterior necesitará un perfil versionado explícito, cierre completo
de referencias RC1–RC4, codec seguro con límites, tabla/esquema aprobados si fueran
necesarios, controles de publicación exclusiva, comprobación física, recuperación
y política de respaldo/custodia. Debe conservar lectores de versiones previas y
no migrar implícitamente los catálogos operativos. No se implementa esa evolución.

La historia aquí solo existe en los objetos aportados en memoria. No hay garantía
ante apagado, escritor concurrente, sustitución hostil de evidencia, eliminación
de originales ni durabilidad del descriptor. No se modifica el alcance H/J/K.
