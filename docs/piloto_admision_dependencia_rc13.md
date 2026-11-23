# RC13 — Piloto offline de admisión de precondición productora

Fecha de elaboración: **2026-11-23**, America/Lima. Base `43ff570`.
[Contrato](contrato_precondicion_productora_rc13.md) y
[auditoría](auditoria_arquitectonica_rc13.md).

## Escenario reproducible y operaciones

[test_precondicion_productora_rc13.py](../tests/test_precondicion_productora_rc13.py)
reutiliza **solo fabricantes**, nunca TestCase importados, de RC3 y RC8–RC11.
No se agrega herramienta de operación real ni ejecutor automático.

| Elemento | Valor sintético / fuente |
|---|---|
| Proyecto A | `proyecto-RC8`, contexto `contexto-RC11` del fabricante previo |
| Proyecto B | `proyecto-RC13-B`, mismo espacio nominal contextual en inventario independiente |
| Composición | `composicion-RC8`; nodos `exportar` y `consumidor` |
| Arista | `exportar → consumidor`, referencia requerida `salida-exportacion` |
| Entrada del exportador | `resultado-qa-fuente`, ResultadoQA generado por evaluador QA0 nativo, no InformeQA inventado |
| Salida / entrada prevista | `objeto-salida-exportacion-{project_id}`, revisión `r1`, entrada `salida-exportacion`, contenido `salida-json-fixture` |
| Productor | exportar_resultado_json nativo mediante ejecutar_exportacion_tecnica RC8 |
| Consumidor | consumir_exportaciones nativo mediante admitir_exportacion_tecnica RC9 |
| Confianza | Perfil específico RC13, proceso local cooperativo, sin autenticidad institucional |

Ambos proyectos pueden exportar bytes idénticos: el project_id MD no forma parte
del JSON QA de esta fixture, que conserva su contexto de exportación propio. El
ensayo comprueba igualdad de JSON/hash y separación de inventarios, proyecto y
dictamen; cruzar sus capturas/admisiones se rechaza. No hay deduplicación de
identidades, permisos ni ejecuciones por hash.

Además de unittest se ejecutó el piloto en memoria, con barrera de auditoría
contra red/SQLite/escrituras y lectura operativa, para registrar estos hechos:

| Proyecto | Bytes UTF-8 | RC8 / RC9 locales | RC11 | RC13 externo | RC3 nativo |
|---|---|---|---|---|---|
| proyecto-RC8 | 3853 | Captura coherente / admisión técnica comprobada | NO_ADMISIBLE | SATISFECHA | PENDIENTE_DE_EVIDENCIA |
| proyecto-RC13-B | 3853 | Captura coherente / admisión técnica comprobada | NO_ADMISIBLE | SATISFECHA | PENDIENTE_DE_EVIDENCIA |

SHA-256 **en memoria** común a las dos salidas sintéticas:
`096a53b91c4c7d23b83feb572ebb6bd700a6726a39c1b2c923fa35913d39a483`.
En ambos casos `exportar` queda INICIADA declarado/CONCLUIDA observado y
`consumidor` permanece DECLARADA; habilitacion_rc3_rc7=False. Esa ejecución en
memoria no materializa archivos ni se presenta como comprobación física.

Los spies envuelven las funciones nativas: una invocación al productor dentro de
la captura RC8 y una al consumidor dentro de RC9. El examen posterior reutiliza
inspectores que pueden validar de nuevo el JSON mediante el consumidor; esas
validaciones puras no son nuevas operaciones registradas ni ejecución del grafo.
No se atribuye a RC9 un cierre de la operación `consumidor`.

## Componentes realmente ejercidos

- RC1/RC2/RC3: contextos, perfiles, arista, orden, usos y restricciones canónicos.
- RC4: inventario descriptivo de dos artefactos y relación productora.
- QA0: resultado sintético real previo a exportar; otro ensayo conserva CierreQA
  genuino y sus contadores mediante el fabricante nativo de RC3.
- RC8/RC9: ejecución explícita del exportador/consumidor y sus testigos locales.
- RC11/RC13: cotejos de correspondencia y decisión local específica.
- RC5: publicación y relectura en TEMP propio cuando se exige física; alteración
  posterior y ausencia controlada no se aceptan como integridad actual.
- RC6/RC7: bytes de salida incluidos, entrada lógica QA declarada externa y
  generación recuperada del inventario descriptivo **original**. Se coteja el
  vínculo del consumidor con RC7 sin habilitar su dependencia.
- RC10: captura/conservación/recuperación del expediente histórico en otro TEMP
  propio. No se usa su portador como inventario de la composición original.

El caso cabe en RC6 vigente porque las operaciones de la composición son
DESCRIPCION_ESTRUCTURAL y no contienen CierreQA. El ResultadoQA aportado está
en RC8/RC9 y no se agrega al codec RC6. No se aplana ni migra ningún contrato.
La recuperación RC6 conserva al productor INICIADA declarado; RC8 separadamente
mantiene su CONCLUIDA observada. Su entrada externa sigue no disponible físicamente.

## Variantes y decisiones comprobadas

| Variante del encargo | Resultado del perfil externo | Alcance conservado |
|---|---|---|
| A: evidencia local completa y coherente | SATISFECHA local | RC11 NO_ADMISIBLE; RC3/RC7 no habilitan consumidor |
| B/C: productor/consumidor incorrectos | NO_SATISFECHA ante evidencia incompatible | No despacho de productor desconocido ni identificación por nombre solamente |
| D/E: proyecto/resultado alterados | NO_SATISFECHA | Incluye resultado, bytes, tamaño, hash y revisión |
| F: bloqueo aplicable | NO_SATISFECHA | Prevalece sobre faltantes; restricciones con origen conservadas |
| G/H/I: parcial, fallida o cancelada observada | NO_SATISFECHA | Se provocan en el productor real mediante Event/fallo controlado; no DTO de éxito |
| J: historia RC10 coherente sin ejecución actual | NO_ADMISIBLE por perfil | Portador íntegro y hechos históricos no restauran testigos |
| K: testigos locales ausentes/copias | PENDIENTE | Construir/copiar un informe favorable no acredita cotejo |
| L: política ausente/desconocida | NO_ADMISIBLE | Defaults nativos idénticos |
| M: CONCLUIDA declarada sin evidencia | No satisfecha; conserva faltantes/contradicciones nativas | RC8 no despacha desde esa declaración |
| N: proyectos con contenido idéntico | SATISFECHA para cada vínculo propio; cruce NO_SATISFECHA | Independencia lógica y ningún permiso adquirido |

Otros casos: entrada/arista/composición ajenas, versiones, finalidad, linaje,
políticas discordantes, autenticidad/externos/física exigidos no acreditados,
restricciones heredadas, determinismo y tipado. La física opcional no abre archivos.
El perfil no exige que el consumidor haya terminado para examinar su entrada.

## RC3/RC7 y límites de integración

Los informes nativos antes/después del cotejo son iguales. Permanecen el código
`dependencia_sin_cierre_tecnico_compatible_aportado`, el cierre QA False para
ambos nodos no QA y los contadores QA vacíos. RC7 mantiene la dependencia pendiente,
sin habilitación declarativa de `consumidor`, aun con bytes RC6 íntegros.

La prueba negativa de portador RC10 como inventario RC7 produce rechazo, sin
reescribir la recuperación. La inspección RC7 incluida en RC13 es la existente:
no se ha implementado una política dentro del recorrido ni un segundo DAG.
La admisión efectiva nativa queda detenida por la incompatibilidad documentada.

Se ejercen barreras con mocks y un proceso separado que prohíbe sockets, SQLite,
apertura de rutas SPICA_DATOS y cualquier escritura/mutación. El piloto en memoria
termina con `RC13_SIN_EFECTOS`. Eso comprueba ese recorrido; no es una certificación
del SO o de todas las funcionalidades de SPICA.

## Registro de verificación

Los comandos, números finales, incidencias de entorno, limpieza y dictamen se
registran en la [auditoría](auditoria_arquitectonica_rc13.md). Las aserciones de
limpieza verifican que desaparezcan las raíces TEMP creadas por RC5/RC6 tras los
contextos; no se borran carpetas ajenas ni se inspeccionan originales operativos.

No se demuestra autenticidad independiente, registro de ejecución del consumidor
RC3, permiso efectivo, durabilidad operativa ni validez científica. El resultado
positivo es exclusivamente una precondición local externa de este perfil.
