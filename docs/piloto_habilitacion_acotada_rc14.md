# RC14 — Piloto de habilitación estructural acotada

Fecha de elaboración: **2026-11-23**, America/Lima. Base `0e8b759`.
[Decisión e interfaces](evolucion_interfaz_coordinacion_rc14.md),
[auditoría y resultados de pruebas](auditoria_arquitectonica_rc14.md).

## Construcción reproducible

[test_coordinacion_precondicion_rc14.py](../tests/test_coordinacion_precondicion_rc14.py)
reutiliza fabricantes RC8/RC9/RC11 y el QA genuino RC3, sin importar TestCase
previos ni duplicar descubrimiento. Todos los valores y archivos son sintéticos.

| Elemento | Valor / evidencia |
|---|---|
| Proyecto A | proyecto-RC8, contexto-RC11, nombres heredados de la fixture |
| Proyecto B | proyecto-RC14-B, en inventario independiente aunque el JSON tenga los mismos bytes |
| Composición | composicion-RC8; nodos exportar, consumidor e independiente |
| Arista seleccionada | exportar→consumidor, referencia salida-exportacion |
| Operación independiente | DESCRIPCION_ESTRUCTURAL DECLARADA sobre la entrada QA sintética; no se ejecuta |
| Fuente QA | ResultadoQA nativo previo; entrada resultado-qa-fuente y raíz lógica sintética ORIGINAL, nunca activo RAW |
| Salida | PREPARADO application/json, objeto-salida-exportacion-{project_id}, revisión r1, contenido salida-json-fixture |
| Productor | Exportador JSON QA0 nativo ejecutado mediante captura RC8 |
| Consumidor | Consumidor JSON nativo invocado mediante RC9; no cierre registrado del nodo consumidor |
| Políticas | Vínculo RC11, selección RC13 nativa y SeleccionPrecondicionRC14 explícita |

Para RC7 se conservan **ambos contenidos** mediante RC5/RC6. La fuente física es
una representación JSON QA nativa del ResultadoQA previo, codificada con el
exportador existente; la salida procede de la captura RC8. Su contenido puede
coincidir, pero mantienen identidades lógicas distintas. El perfil de fuente
describe el contrato QA 1.0.0 y su contenedor declarado es JSON QA 0.1.0.
No se inventa un serializador científico ni se afirma que RC8 haya leído ese
archivo: recibe el ResultadoQA en memoria mediante su interfaz existente.

La generación RC6 conserva el inventario descriptivo original, sin CierreQA
en su composición. Los vínculos RC7 incluyen las entradas de exportar, consumidor
e independiente; no se utiliza una generación del portador documental RC10 como
si fuera ese inventario. Las raíces TEMP se comprueban inexistentes al cerrar los
contextos experimentales; no hay conservación operativa.

Además de unittest se ejecutó el piloto completo de ambos proyectos, con barreras
contra red, SQLite y apertura de rutas operativas. Resultados registrados:

| Proyecto | RC3/RC7 sin selección | RC3/RC7 con selección | Cruce de proyecto en RC7 | RC6 / contenidos incluidos | Limpieza |
|---|---|---|---|---|---|
| proyecto-RC8 | independiente | independiente, consumidor | No admitido | VERIFICADA; dos INTEGRO de 3853 bytes | Ambas raíces TEMP ausentes al salir |
| proyecto-RC14-B | independiente | independiente, consumidor | No admitido | VERIFICADA; dos INTEGRO de 3853 bytes | Ambas raíces TEMP ausentes al salir |

Las dos salidas JSON tienen el SHA-256 en memoria
`096a53b91c4c7d23b83feb572ebb6bd700a6726a39c1b2c923fa35913d39a483`.
Ese mismo hash/tamaño fue calculado físicamente por las API RC5/RC6 sobre cada
contenido sintético incluido, dentro del alcance de sus lecturas. RC11 permanece
NO_ADMISIBLE y RC13 SATISFECHA para cada vínculo propio; los cruces se rechazan.
Consumidor permanece DECLARADA, permiso=False y ejecución_realizada=False.
La tabla conserva el orden nativo de habilitaciones, no otro orden de coordinación.
Es una ejecución adicional del piloto, no un incremento del contador unittest.

## Comparación obligatoria A–H

| Escenario | Precondición / dependencia | Operaciones habilitadas y bloqueadas |
|---|---|---|
| A: sin RC14 | Resultado predeterminado idéntico; cierre no QA no admitido | Independiente habilitada; consumidor bloqueado |
| B: selección explícita, evidencia actual admisible y condiciones completas | RC13 SATISFECHA; arista específica estructuralmente apta mediante RC14 | Consumidor e independiente habilitados declarativamente en RC3 y RC7; no ejecución |
| C: segunda dependencia pendiente | La arista seleccionada puede ser apta; la otra permanece pendiente | Consumidor bloqueado en ambos recorridos |
| C, variante fallida | Se conservan fallo/causa de la otra operación; RC13 no se promociona si deja pendiente el conjunto | Consumidor bloqueado; operación fallida sin promoción |
| D: solo historia RC10 | Recuperación documental real, pero sin testigos actuales; NO_ADMISIBLE por RC13 | Sin admisión RC14 ni habilitación del consumidor |
| E: proyecto, composición o consumidor incorrectos | Contradicción del cotejo correspondiente o del vínculo de integración | No se reutiliza evidencia/habilitación ajena |
| F: parcial, fallida o cancelada observada | Event/fallo controlado en el productor real; no cierre ficticio | Consumidor bloqueado, estados conservados |
| G: restricción bloqueante | Restricción y procedencia conservadas; precondición no satisfecha | Consumidor bloqueado |
| H: perfil/versión RC14 desconocidos, o política RC13 no admitida | No se prepara aporte de admisión | Comportamiento predeterminado; consumidor bloqueado |

En B, la productora conserva INICIADA declarada y CONCLUIDA observada separada;
consumidor e independiente permanecen DECLARADAS. Ambos recorridos conservan
cierre_qa_coherente_completo=False para los nodos no QA y contadores QA sin
consumo nuevo. La composición puede seguir pendiente por su declaración histórica,
sin impedir esa habilitación específica del consumidor cuando cumple sus condiciones.

Los tests comparan informes completos predeterminados con las interfaces anteriores,
antes/después del cotejo, y conservan orden y resultados QA genuinos. El productor
y consumidor se envuelven con spies para comprobar las invocaciones reales en
RC8/RC9. RC14 nunca despacha el productor ni una nueva admisión RC9; los inspectores
pueden validar el JSON mediante funciones nativas puras, sin registrar operaciones.

## Evidencias adicionales y barreras

- RC13 se vuelve a cotejar. Un dictamen favorable aportado o una copia sin testigo
  no sirve como entrada ni restaura una comprobación local.
- Dos proyectos con JSON/SHA idénticos se evalúan separadamente; cruzarlos produce
  rechazo, no deduplicación de permisos o identidad.
- Otra arista de la misma productora conserva su regla anterior, aun requiriendo
  la misma referencia de resultado. No se habilitan globalmente sus dependientes.
- Entrada/resultado/revisión/contenido, versión, operaciones, perfil RC2, límites,
  causa propia de la productora y estado terminal del consumidor no se omiten.
- Se prueba un diagnóstico aportado que usa el mismo código del faltante de estado
  del inspector: aunque RC13 resulte satisfactorio en su ámbito, RC14 no lo oculta
  ni lo compensa. SATISFECHA no equivale a habilitación.
- Se propagan restricciones adicionales admitidas al consumidor y descendientes,
  conservando orígenes y bloqueando el uso afectado; las copias no se cuentan como
  pruebas independientes.
- Con fuente QA externa no disponible, RC7 mantiene pendiente la arista. Con
  salida consumidora externa, su entrada mantiene bloqueada la operación aunque
  se reconozca la clase de cierre de la productora.
- Una relectura RC5 contradictoria después de RC9 impide admisión; una recuperación
  RC6 releída como corrupta tampoco es compensada por RC13.
- La cancelación previa evita el cotejo RC13; los recorridos conservan sus controles
  cooperativos y no habilitan operaciones canceladas.
- Un proceso aislado con audit hook prohíbe sockets, SQLite, lectura operativa y
  cualquier escritura/mutación; el recorrido RC3 en memoria termina con
  RC14_SIN_EFECTOS. No es una certificación general del SO o de procesos hostiles.

RC10 conserva un expediente real mediante sus API previas, recuperado como
historia. RC11 sigue NO_ADMISIBLE según su contrato; no se reescriben sus flags
ni los de RC13. El informe nuevo expresa la evaluación RC14 por separado.

## Garantías y límites

La habilitación es declarativa, local, específica y explícita. No concede permiso,
autenticidad institucional, cierre de ejecución del consumidor ni validez científica.
La física RC5 solo se relee si se exige; RC7 usa una recuperación RC6 fechada y
no promete una nueva lectura física por cada inspección. No se afirma integridad
actual de originales operativos, que no se abren.

No se han implementado scheduler, reanudación, motor de plugins, permisos efectivos,
nuevo almacenamiento, migración o método científico. No se amplían formatos
históricos. El registro de comandos, resultados exactos y verificación final
se conserva en la auditoría enlazada; los conteos estáticos no sustituyen unittest.
