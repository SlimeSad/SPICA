# RC11 — Piloto sintético de una dependencia técnica

Fecha: **2026-11-20**, America/Lima. Base `98094c1`.
[Contrato](contrato_dependencia_noqa_rc11.md) y
[auditoría con verificaciones finales](auditoria_arquitectonica_rc11.md).
Todos los datos de este piloto son inventados; no se abre el CSV institucional.

## Componentes ejecutados y correspondencias

[test_dependencia_noqa_rc11.py](../tests/test_dependencia_noqa_rc11.py) reutiliza
fabricantes de fixtures existentes, sin importar sus TestCase ni duplicar pruebas.
`evaluar_registro` Nivel 0 evalúa una fila sintética con `L0-EST-001` y produce
un ResultadoQA nativo. Este resultado puntual no se presenta como InformeQA de
lote. Otra prueba usa `qa_real` RC3, que recorre realmente un CSV sintético TEMP
con el evaluador existente, para comprobar que un CierreQA genuino de otra
operación no sirve de cierre de exportación. No se fabrica un InformeQA.

Antes de ejecutar se declara la composición RC3 existente con dos operaciones
DESCRIPCION_ESTRUCTURAL y la arista `exportar → consumidor`. El consumidor se
declara para `consumir_json_qa0_rc9` y recibe la entrada canónica de la salida.
La composición es una declaración; RC11 no la despacha ni la reescribe.

Se llama explícitamente a `ejecutar_exportacion_tecnica` RC8, que invoca una vez
`exportar_resultado_json`; después a `admitir_exportacion_tecnica` RC9, que llama
al consumidor nativo. Los spies del piloto comprueban ambas llamadas reales.
El dictamen posterior inspecciona los resultados, sin repetir esas operaciones.
Los contrastes internos puros del consumidor/exportador siguen en sus módulos.

| Identidad del piloto | Valor o relación |
|---|---|
| Proyectos MD-01 | `proyecto-RC8` y `proyecto-RC11-B`; contextos independientes pese al literal de contexto compartido `contexto-RC11` |
| Composición | `composicion-RC8`, con ámbito de proyecto |
| Productora / dependiente | `exportar` / `consumidor`, con ámbito de contexto/proyecto |
| Entrada lógica de resultado QA | `resultado-qa-fuente`; distinta de registro CSV y activo RAW |
| Entrada de salida | `salida-exportacion` |
| Objeto de salida A | `objeto-salida-exportacion-proyecto-RC8`, revisión `r1` |
| Objeto de salida B | `objeto-salida-exportacion-proyecto-RC11-B`, revisión `r1` |
| Contenido de salida | `salida-json-fixture`, solo dentro de su inventario contextual |
| Expediente histórico | `expediente-RC11`, identificado además por proyecto y generación |

Ambos proyectos pueden producir bytes JSON idénticos: el JSON QA histórico no
incluye project_id MD. La igualdad de SHA no fusiona proyectos, objetos,
operaciones, expedientes, generaciones o permisos. El cruce de evidencias entre
proyectos es rechazado tanto localmente como después de recuperación RC10.

## Estados y resultados que el piloto distingue

| Dimensión | Caso local coherente | Caso histórico recuperado |
|---|---|---|
| Declaración RC1 del productor | INICIADA, permanece intacta | Snapshot histórico INICIADA, intacto |
| Operación observada por RC8 | CONCLUIDA en la captura | CONCLUIDA registrada históricamente |
| Captura privada RC8 | Coherente en el proceso actual | No se restaura |
| Comprobación privada RC9 | Coherente para ese consumo local | No se restaura |
| Operación RC3 del dependiente | DECLARADA, sin cierre admitido | No se promueve a ejecutada |
| Artefacto lógico RC4 de salida | PREPARADO/DESCRITO | Misma descripción histórica |
| Física de la salida | Solo si se solicita y relee RC5 | No se deduce del portador |
| Física del expediente | No es necesaria en memoria | RC10/RC6 verifica el portador actual |
| Historia | No sustituye la captura | Se conserva explícitamente como historia |
| Dependencia RC11 | NO_ADMISIBLE por RC3/RC7 vigentes | NO_ADMISIBLE; la historia tampoco habilita |
| Ciencia / permiso / autenticidad | No acreditados | No acreditados |

El cierre local RC8 y la admisión RC9 pueden ser correctos para sus propias
finalidades y coexistir con RC3/RC4 pendientes. RC11 conserva esas diferencias.
No existe una variante SATISFECHA legítima para esta arista bajo RC3/RC7 0.1.0.
La prueba demuestra ese bloqueo en vez de añadir un cierre QA ficticio.

## Variantes verificadas

| Variante | Resultado exigido |
|---|---|
| Captura RC8 y admisión RC9 locales coherentes | Correspondencias APTO_ESTRUCTURALMENTE; decisión NO_ADMISIBLE |
| Relectura física RC5 correcta de la salida | Mismo bloqueo contractual; no satisface por tener SHA correcto |
| Captura/admisión ausentes o copias sin testigo | PENDIENTE, salvo asociaciones contradictorias |
| Resultado, productor, versión, operación, proyecto, entrada, contenido o revisión ajenos | NO_SATISFECHA |
| Bloqueo heredado o adicional para consumo | NO_SATISFECHA, sin quitar la restricción |
| Restricciones con mismo código y distinta definición | Ambas variantes conservadas; NO_SATISFECHA |
| Restricción para otra finalidad científica | Conservada y no levantada; no bloquea por sí sola este consumo técnico |
| Usos desconocidos o autenticidad independiente exigida | PENDIENTE |
| Externos cuya disponibilidad actual se exige | PENDIENTE; no se inventa su presencia o ausencia |
| Física obligatoria sin referencia | PENDIENTE |
| Archivo sintético modificado después de RC9 | Nueva relectura detecta inconsistencia; NO_SATISFECHA |
| Archivo sintético retirado después de RC9 | AUSENTE comprobado, distinto de NO_DISPONIBLE; NO_SATISFECHA |
| Materialización de otro proyecto/salida | Rechazo de asociación sin abrir ese archivo |
| Fallo real, cancelación o resultado parcial del exportador | Estado observado conservado; NO_SATISFECHA |
| Operación solamente declarada CONCLUIDA | No se toma por ejecutada ni satisfecha |
| Cierre QA genuino de otra operación | No sustituye el cierre no QA; se rechaza la asociación |
| Linaje contradictorio | Informe nativo adverso conservado; NO_SATISFECHA |
| Expediente RC10 sin cierre o admisión suficientes | PENDIENTE; no promoción de historia |
| Expediente RC10 de un fallo real | Fallo histórico permanece como incumplimiento |
| Portador corrupto o hash de control incorrecto | NO_SATISFECHA, sin reparar ni regenerar |
| Generación incompleta | PENDIENTE, sin crear el cierre faltante |
| Física RC9 histórica, incluso si fue correcta | No se relee su ruta histórica; física actual de salida pendiente |
| DTO con diagnósticos vacíos construido por llamador | Nunca SATISFECHA; no hay un argumento de habilitación |

## Conservación, recuperación y prueba RC7

El piloto llama expresamente a `capturar_evidencias`, conserva con RC10 sobre
RC5/RC6 y recupera mediante la API RC10. El portador es un artefacto documental
con inventario acotado propio; no se le atribuye un activo RAW. Se ejercitan dos
proyectos y generaciones independientes con salida JSON compartida.

La prueba de RC7 llama realmente a `inspeccionar_integracion` con la generación
del portador y la composición original. El consumidor no queda habilitado y el
informe no es APTO: la generación del expediente no contiene el inventario
original que RC7 necesita. Se documenta la incompatibilidad, sin insertar sus
datos internos en el formato RC6 ni redefinir la composición histórica.
La prueba RC3 comprueba que sus diagnósticos y habilitaciones son idénticos
antes y después del dictamen. RC11 no se conecta como autorización a esas API.

La inspección repetida de un expediente no cambia sus archivos. Al salir de los
contextos nativos se limpian únicamente los TEMP propios. No se borran carpetas
preexistentes ni se usan rutas operativas. La prueba de proceso independiente
prohíbe socket, SQLite, escrituras y acceso a SPICA_DATOS para el caso en memoria.

El resultado está sujeto a proceso Python cooperativo y controles sin firma.
Se comprueba integridad de fixtures y portadores en momentos concretos; no se
acreditan durabilidad permanente, custodia independiente, ejecución única,
autenticidad institucional, licencias ni calidad científica. El resultado final
de pruebas y el estado Git se registran en la auditoría, sin extrapolarlos a
originales institucionales que no se abrieron.
