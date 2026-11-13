# RC3 — Contrato de composición declarativa de operaciones

Fecha: **2026-11-13**, America/Lima. Base **496c740**, feature/suadc-http.
Versión experimental **0.1.0**. Véanse [integración](integracion_coordinacion_rc3.md)
y [auditoría](auditoria_arquitectonica_rc3.md).

## Responsabilidad e inventario previo

La sección 5 de la [hoja de ruta 85-M](hoja_ruta_continuidad_arquitectonica_paso85m.md)
propone composición, política de efectos y presupuesto, conservando la separación
entre preparación, autorización y ejecución. Este encargo delimita RC3 a
**coordinación estructural sin efectos**. No completa el ejecutor/flujo operativo
planteado en esa hoja de ruta, M03/M16 ni la arquitectura integral.

| Existente | Capacidad reutilizada | Responsabilidad faltante / decisión |
|---|---|---|
| [RC1](contrato_contexto_comun_rc1.md): ContextoProyecto, ContextoEntrada, ContextoOperacion | Identidades MD/contextuales, snapshots, estados declarados, propósito, configuración, cuotas QA y restricciones | Falta conjunto de operaciones y grafo de dependencias. Se envuelven los mismos objetos; no se amplían sus campos |
| validar_relaciones / cambiar_estado | Cotejo de inventarios, pertenencia y transiciones declaradas | Se llama al cotejo; no se introducen otras transiciones ni historial ficticio |
| [RC2](contrato_perfiles_informacion_rc2.md): perfiles y comparar_perfiles | Compatibilidad para finalidad explícita, con razones, evidencia y restricciones | El nodo declara requisitos; el inspector los recalcula y conserva resultados completos. No recibe un booleano de aprobación |
| [PlanConsulta / Planificador](../src/spica/adquisicion/planificacion/modelos.py) | Propuestas de adquisición según catálogo; ejecutable=False | No coordina ContextoOperacion ni ejecuta HTTP. No se reimplementa ni se convierte su preparación en permiso |
| [QA0](../src/spica/calidad/motor.py), InformeQA y LimitesQA | Ejecución secuencial, cierre/EOF, contadores, cancelación y cuotas propias | El inspector no llama al motor. Solo contrasta evidencia previamente producida; el ensayo sí ejecuta el componente existente |
| [VinculoResultadoQA / validar_vinculos_qa](../src/spica/contextos/adaptadores_qa.py) | Pertenencia, procedencia, referencias de cierre, duplicados y cuotas | El adaptador RC3 añade cotejo con InformeQA; un cierre contextual solo no satisface una dependencia |
| [85-G](../herramientas/piloto_integracion_85g.py) y [85-H](../herramientas/traza_cierre_85h.py) | Piloto de ejecución fija, traza, captura y verificación de su linaje | Herramientas de checkout con efectos simulados/TEMP, no una API de coordinación de src. No se importan ni duplican sus fases, eventos, informes o verificador |
| RestriccionQA / combinar_restricciones | Unión conservadora por código, sin rebajar bloqueos | Se añaden referencias de origen y propagación por dependencias, sin contarlas como evidencias independientes |
| Event estándar | Cancelación cooperativa | Solo detiene esta inspección; no cancela motores ajenos ni altera estados de operaciones |

No se encontró un coordinador equivalente ni una incompatibilidad que requiriera
cambiar contratos públicos. Los originales RC1/RC2/QA0, JSON QA 0.1.0, RAW,
catálogos, J y K permanecen intactos.

## Modelos

Paquete [spica.coordinacion](../src/spica/coordinacion/__init__.py), dataclasses
congeladas y slots, sin persistencia, registro global, callbacks o payload binario.

| Contrato | Contenido / consumidor |
|---|---|
| ComposicionOperaciones | identificador, proyecto RC1, operaciones, dependencias, finalidad, límites, restricciones adicionales y versión. Solo describe el inventario |
| NodoOperacion | contexto RC1 original, usos_declarados opcionales, requisitos RC2 y cierre QA opcional. Permite conservar entradas, presupuestos, propósito, estados y referencias sin otra identidad de operación |
| DependenciaOperacion | predecesora, dependiente y referencias de resultado requeridas. Todas las aristas son obligatorias; tupla vacía de referencias exige igualmente cierre técnico completo |
| RequisitoCompatibilidad | dos EntradaPerfil y FinalidadCompatibilidad existentes. El resultado se obtiene al inspeccionar, no se admite una aprobación manual |
| CierreQA | InformeQA y tupla de VinculoResultadoQA previamente producidos. No contiene una bandera de éxito aportada por el llamador |
| LimitesComposicion | cuotas declaradas de nodos, aristas, profundidad, visitas de descriptores, bytes textuales y suma de máximos QA comparables |
| RestriccionPropagada | restricción original y referencias de origen; una sola entrada por código |
| InspeccionOperacion | nodo, diagnósticos, restricciones propagadas, resultados RC2 completos y diagnóstico de coherencia de cierre QA |
| InformeComposicion | composición, inspecciones, diagnósticos globales, orden, restricciones, cuotas, contadores QA aportados, medición textual y cancelación de inspección |

Los resultados guardan referencias a objetos existentes, incluidos los literales
que ya retienen resultados QA; no cargan datasets ni copian sus bytes. El inspector
puede rechazar un grafo de descriptores demasiado grande aunque sus objetos
individuales fueran admitidos por otros subsistemas.

## Identidades y dependencias

Una composición pertenece a **un ContextoProyecto completo**. Su identificador
no sustituye project_id, contexto_id, operacion_id, entrada_id, object_id,
asset_id o SHA. Dos proyectos con contenido compartido usan composiciones
independientes. Una dependencia entre proyectos no se admite mediante este contrato.

Las operaciones tienen ID único dentro de la composición/contexto. Dos operaciones
sobre la misma entrada siguen siendo distintas. Un ID de entrada repetido entre
operaciones debe referenciar **el mismo objeto ContextoEntrada**; otro snapshot,
aunque compare igual, se rechaza como no canónico. Esto evita sustituciones
silenciosas y concuerda con el vínculo por referencia exigido en RC2.

Se detectan vacío, duplicados, extremos inexistentes, autoaristas, aristas repetidas,
ciclos y profundidad excedida. Orden de precedencia: algoritmo acotado por capas
topológicas, con IDs originales ordenados lexicográficamente dentro de cada capa.
No es un orden de ejecución. Ante un grafo inválido se devuelve orden vacío y
ninguna habilitación; no se presenta un prefijo acíclico como solución completa.

Una dependencia se satisface, **según evidencia aportada**, únicamente si su
predecesora tiene diagnóstico estructural apto y un cierre QA completo coherente,
y si las referencias requeridas pertenecen a ese cierre. Estar lista, PLANIFICADA,
INICIADA o simplemente declarada CONCLUIDA no equivale a haber producido resultados.
En esta versión no hay adaptador de cierre técnico para operaciones descriptivas
u otros componentes: sus dependientes quedan pendientes, sin inventar evidencia.

## RC1, RC2 y cierres QA

Se reutilizan los siete estados RC1 sin promoverlos ni modificarlos. DECLARADA y
PLANIFICADA pueden aparecer como habilitadas declarativamente. INICIADA, PARCIAL,
FALLIDA y CANCELADA no se relanzan; conservan causas y referencias. CONCLUIDA solo
puede aportar cierre técnico si el adaptador lo contrasta; nunca se vuelve a lanzar.
La composición usa EstadoAptitud como diagnóstico estructural y no tiene un estado
de ejecución inventado. No crea eventos ni reconstruye un historial.

Por requisito se verifica pertenencia por referencia de ambas entradas y coincidencia
de propósito/finalidad. Se llama a comparar_perfiles y se retiene ResultadoCompatibilidad
completo. El resumen RC3 no eleva PENDIENTE_DE_EVIDENCIA ni ignora INCOMPATIBLE.
Se utiliza su interfaz sin operación opcional: RC2 solo admite operaciones descriptivas
en ese argumento, mientras el nuevo requisito puede pertenecer también a QA0.
RC3 conserva el contexto propietario y aplica además sus restricciones.

Antes de declarar lista una QA se cotejan la configuración con seleccionar_reglas,
el perfil qa0-senamhi-16/revisión 1.0.0 y metadatos mínimos del adaptador RC1.
Un perfil desconocido queda pendiente; uno conocido no admitido es incompatible.
No se fabrican filas para preparar una identidad de exportación. La habilitación
no garantiza lectura, exportación o cierre futuros: esos componentes conservan
sus validaciones y sus responsabilidades al ejecutarse.

El cierre QA contrasta versiones, operación/snapshot exactos de los vínculos,
validar_vinculos_qa, configuración, límites, procedencia, número de registros y
resultados, conteos por categoría/estado, reglas ejecutadas y evaluaciones incompletas.
Un cierre completo requiere informe COMPLETA, recorrido completo, motivo eof,
registros finalizados iguales a examinados, resultados vinculados y operación
CONCLUIDA. Un reporte parcial no satisface la dependencia. Una alerta o problema
detectado por QA puede coexistir con un recorrido técnico completo: no se convierte
en aprobación de la observación ni se borra su restricción.

Este cotejo **no autentica el informe ni prueba el archivo fuente**. Un llamador
hostil que falsifique coherentemente informe y resultados queda fuera del modelo
de proceso confiable heredado. Los ensayos llaman realmente al motor; el contrato
no transforma esa prueba en una garantía contra falsificación.

## Restricciones, estados y cancelación

Se conservan proyecto, composición, contextos de operación, entradas/perfiles y
vínculos QA. Una restricción con mismo código y contenido idéntico se conserva una
vez, con referencias de origen ordenadas; esas copias no aumentan la confianza.
Una variante de tipo, operaciones o motivo provoca rechazo explícito. Las
restricciones se propagan transitivamente por todas las dependencias, aun si falta
evidencia para satisfacerlas. En grafos inválidos se conserva el inventario global
completo de restricciones, sin habilitar operaciones.

usos_declarados es el alcance literal del cotejo, **no permiso**. Una intersección
exacta con las operaciones de un bloqueo causa incompatibilidad. Si el alcance
es None y hay bloqueos, su aplicabilidad queda pendiente. Los bloqueos para otros
usos se retienen; no se interpretan comodines ni se evalúa lenguaje normativo.
El llamador sigue siendo responsable de declarar un alcance suficiente y veraz.

Precedencia del diagnóstico: INCOMPATIBLE, PENDIENTE_DE_EVIDENCIA,
APTO_ESTRUCTURALMENTE. Un nodo incompatible no borra los diagnósticos ni la
habilitación de nodos independientes válidos; un error global de grafo, identidad
o presupuesto impide todas las habilitaciones. El nivel CONTRADICCION también
indica un requisito estructural/político incumplido, sin afirmar conflicto científico.
Ante un error global no se recalculan requisitos RC2 ni se cotejan cierres QA:
se conservan los requisitos/evidencias originales en la composición y el diagnóstico
que impidió inspeccionarlos. cierre_qa_coherente_completo=False significa que
esta inspección no acreditó ese cierre; puede no haberlo inspeccionado, sin negar
el contenido del informe aportado. Los diagnósticos distinguen esos casos.

Las etiquetas de origen son referencias descriptivas, no claves de un catálogo
global. Los snapshots completos y sus versiones siguen accesibles en composición,
perfiles y vínculos; no se ofrece una traza persistente o exportación de este grafo.

La función acepta solo Event estándar o None. Comprueba cancelación durante la
medición y entre cotejos; puede terminar la comprobación acotada en curso. Conserva
los resultados RC2 ya obtenidos y los cierres aportados; no cambia un estado RC1.
Con cancelación no hay habilitaciones, aunque alguna parte hubiera sido inspeccionada.
Sin Event la inspección es reproducible para las mismas entradas. No hay espera,
plazo forzoso, ejecución concurrente o cancelación de motores externos.

autoriza_operacion=False, ejecucion_realizada=False y recursos_reservados=False
son invariantes del informe. bool(composición/informe) se rechaza.

## Presupuestos y límites

| Cuota | Predeterminado | Tope de contrato |
|---|---:|---:|
| Operaciones | 16 | 32 |
| Dependencias | 64 | 128 |
| Profundidad del DAG, raíz=1 | 16 | 32 |
| Visitas a descriptores | 100000 | 200000 |
| Bytes UTF-8 de campos textuales | 4194304 | 8388608 |
| Suma de max_registros QA | 100000 | 64000000 |
| Suma de max_resultados QA | 1000000 | 160000000 |

Por nodo: hasta ocho requisitos RC2, 16 usos y 128 resultados por cierre QA.
El inventario de entradas distintas tiene el tope 256 de validar_relaciones RC1.
Los topes duros se rechazan al construir; exceder un límite declarado se diagnostica
sin habilitación. Versiones desconocidas se rechazan, sin migraciones.

La medición recorre referencias **por ocurrencia**, sin deduplicar por interning
o compartir objetos; es una cota reproducible de validación, no tamaño físico en RAM.
Solo cuenta bytes de str, procesa su UTF-8 en fragmentos y limita visitas/profundidad
interna a 64. No serializa el contrato. Si se interrumpe por cuota o cancelación,
bytes_texto_descriptores=None; no se presenta un prefijo como medición total.

Se suman máximos de registros/resultados **por operación QA**; dos evaluaciones de
la misma fila cuentan dos veces como trabajo declarado, no como observaciones
únicas. No se suman cotas por celda/registro, bytes HTTP, tiempos o magnitudes de
otro significado. Los contadores QA aportados se mantienen separados por operación;
no constituyen consumo global medido, reserva de disco o control de CPU/RSS.

No hay ejecutor, cola, workers, persistencia, permisos efectivos ni nuevos motores
científicos. La fuente de verdad de cada efecto futuro sigue siendo su componente
y la autorización concreta, fuera de este incremento.
