# PASO 85-I — Protocolo propuesto de conservación y recuperación offline

Elaboración: **2026-11-12, America/Lima**. Base **a044b49**,
feature/suadc-http. **Especificación para revisión; no procedimiento ejecutado ni
recuperador disponible.** Léase con la
[arquitectura](arquitectura_persistencia_linaje_paso85i.md) y el
[plan](plan_implementacion_persistencia_paso85i.md). No se abrieron almacenes
operativos ni se prepararon copias, carpetas o bases de prueba en este paso.

## 1. Tres dimensiones que no deben confundirse

Se conservan los estados de ejecución del
[contrato 85-G](contrato_ejecucion_integrada_paso85g.md): PLANIFICADA, INICIADA,
CONCLUIDA, INCOMPLETA, FALLIDA y CANCELADA. Sus valores reales se mantienen sin
renombrarlos dentro de JSON históricos. CONCLUIDA significa cadena estructural
cerrada en su alcance; no validación científica. INCOMPLETA, FALLIDA y CANCELADA
también pueden tener su evidencia correctamente conservada.

Propuesta de estados **de conservación**, independientes del resultado del motor:

| Estado propuesto | Hecho mínimo requerido |
|---|---|
| PREPARADA | Intención SQL identificada y confirmada, contexto/versión/presupuesto registrados; todavía no hay artefactos completos garantizados |
| ESCRIBIENDO | Escritura iniciada; puede existir un prefijo o temporal. No entregar como expediente conservado |
| PUBLICADA | Se observaron los artefactos obligatorios publicados y releídos; todavía falta confirmación lógica del inventario en SQL |
| CONSERVADA | Una transacción SQL confirmó inventario, manifiesto y referencias tras los cotejos; habilita consulta con revalidación, no certifica ciencia/durabilidad absoluta |

La fase ESCRIBIENDO/PUBLICADA se registra mediante eventos cortos; tras una caída
el último evento puede ir retrasado respecto a los archivos. **CONSERVADA no se
infiere por encontrar un manifiesto**. El protocolo admite completar la
conservación de un resultado terminal, no hacer que el motor complete fases.

El **estado de recuperación** se emite por comprobación, con causas separadas:

| Estado propuesto | Interpretación |
|---|---|
| PENDIENTE | No se ha podido comprobar este alcance/generación |
| COHERENTE_EN_ALCANCE | Cotejos necesarios realizados y sin discrepancia; se enumeran alcances y dependencias no revalidadas |
| INCOMPLETA | Evidencia/confirmación requerida no disponible; no hay prueba suficiente para el cotejo completo |
| REVISION_NECESARIA | Contradicción, conflicto, corrupción demostrada, referencia rota o estado ambiguo que exige intervención |

Causas explícitas: temporal parcial, artefacto ausente, hash no coincidente,
índice inconsistente, versión incompatible, permiso de lectura denegado, control
independiente ausente, recurso externo no disponible, terminación no observada,
entre otras de un registro cerrado. Un permiso denegado impide verificar, no
demuestra corrupción. Un estado no admite evaluación científica por sí mismo.

El resultado histórico de la ejecución es inmutable. Una recuperación que
descubre corrupción añade un evento y bloquea la disponibilidad actual; no
reescribe CONCLUIDA como si QA hubiera fallado entonces. Si el proceso terminó
sin informar un estado terminal, se conserva **INICIADA como último observado**
con terminacion_no_observada e INCOMPLETA/REVISION_NECESARIA de recuperación;
no se inventa FALLIDA, CANCELADA o CONCLUIDA para el motor.

Ejemplos válidos: ejecución FALLIDA + conservación CONSERVADA + recuperación
COHERENTE_EN_ALCANCE; ejecución CONCLUIDA + CONSERVADA histórica + recuperación
REVISION_NECESARIA por pérdida posterior de un artefacto. Los errores técnicos
de custodia tienen su propio código y no alteran retroactivamente la ciencia.

## 2. Precondiciones y presupuesto

Antes de cualquier futura escritura, un operador confiable deberá autorizar raíz,
catálogo y alcance sintético; comprobar identidad de instancia/esquema reconocido,
ausencia de inicialización incierta, espacio, capacidad de escritura/publicación
exclusiva y ausencia de escritores conocidos. Se rechazan raíces dentro de código,
RAW/staging, Git/controles internos, rutas enlazadas o de red fuera del perfil
admitido. No adoptar directorios/bases ajenos ni migrarlos al abrir.

Un único escritor de conservación para cada conjunto raíz/índice; el control
local deberá cubrir el ciclo de archivos y SQL, no solo una transacción. Una
segunda operación se rechaza/espera con límite y cancelación explícitos; no se
roba una intención porque un PID parezca ausente. Una caída deja revisión offline.
Ninguno de estos controles globales existe hoy por usar BEGIN IMMEDIATE.

Para el perfil cooperativo local se propone un marcador de escritor creado
exclusivamente en control, con nonce/identidad y versión, manteniéndolo durante
todo el ciclo. La creación exclusiva rechaza una segunda apertura; no es un lock
distribuido ni impide escritores que ignoren el protocolo. Solo el propietario
puede retirar su marcador después de cerrar y revalidar ruta/nonce. Si queda
abandonado, la inspección sin efectos puede informar, pero liberar el marcador
requiere revisión y autorización: no se usa un TTL/PID para borrarlo o reintentar.
Este mecanismo también deberá probarse antes de ofrecer la garantía cooperativa.

Presupuesto a especificar en el futuro contrato:

- Límites por artefacto, número de resultados/documentos/entradas y total de
  escritura por ejecución; límite de temporales y margen para DB/journal/WAL.
- Pico de espacio incluyendo temporal + publicación/copia si la estrategia la
  exige + archivos previos referenciados + posible snapshot de inspección.
- Reserva operativa mínima acordada por el responsable, sin inventar umbral
  universal. Una sonda de espacio es una observación, no una reserva ni cuota SO.
- Cancelación por bloques/fases/transacciones cortas; si falla escribir el propio
  diagnóstico, devolver un código acotado y conservar lo ya existente.

El MVP utilizará las cotas sintéticas revisadas del 85-G/H; no habilita archivos
arbitrariamente grandes ni convierte cotas de bytes JSON en un límite RSS. Los
contenidos grandes futuros requerirán partición explícita, conservando contexto,
orden y restricciones. No descartar evidencia para ajustar un conteo.

## 3. Protocolo de conservación propuesto

La implementación deberá ofrecer puntos de fallo observables para ensayos
sintéticos. El orden de confirmación es obligatorio; las transacciones no quedan
abiertas durante hashing, transferencia o evaluación QA.

| Paso | Operación propuesta | Confirmación y tratamiento del fallo |
|---|---|---|
| 0. Comprobar | Precondiciones, contrato, versiones, límites, identidad/idempotencia y coordinación local | Sin escritura de evidencia ante rechazo; no ejecutar motores, red o migraciones |
| 1. Preparar | Transacción SQLite corta registra intención, clave de ejecución/generación, contexto y artefactos esperados, sin afirmar hashes físicos aún no calculados | PREPARADA solo después de commit. SQL falla: detener, no publicar cuerpos |
| 2. Escribir | Temporal exclusivo generado dentro de la raíz autorizada/mismo volumen; escribir cuerpos realmente recibidos por bloques, comprobar escritura corta, calcular SHA y tamaño | ESCRIBIENDO; cancelar conserva causa/prefijo según política, nunca publicar parcial como completo |
| 3. Verificar y publicar | flush, fsync del archivo, cierre y relectura física; publicar sin sobrescribir, comprobar destino. Construir informe, envolvente de traza y manifiesto en el orden acíclico del documento de arquitectura | Enlace duro exclusivo donde esté soportado y comprobado. Si existe destino, cotejar contenido/identidad; no reemplazarlo. Fallo exige detener y conservar evidencia |
| 4. Registrar referencias | Tras publicar y releer todos los obligatorios, registrar el evento PUBLICADA y preparar inventario/restricciones/referencias verificables | SQL no disponible: quedan archivos posibles huérfanos y la intención; no afirmar CONSERVADA |
| 5. Confirmar lógicamente | Una transacción SQL compara contexto/intención, registra inventario, enlaces y H_M, comprueba unicidad/FK y marca CONSERVADA con su evento | Commit SQL único del cierre lógico; no una transacción del filesystem. Rechazar versión, conflicto o evidencia contradictoria |
| 6. Cerrar | Cerrar descriptores/SQLite y liberar coordinación; limpiar solo temporales propios ya clasificados como prescindibles | Error de cierre/limpieza queda como incidencia; no borrar evidencia para forzar éxito. Devolver estado explícito y alcance de verificación |
| 7. Reabrir | Nuevo proceso lee el índice/manifiesto y relee artefactos; coteja hashes, versiones, estados y restricciones | Evento nuevo de recuperación; nunca sustituye el historial por una nueva ejecución supuesta |

La estrategia de publicación propuesta deriva del patrón existente os.link:
requiere soporte y mismo volumen para temporal/destino; FileExistsError preserva
lo anterior. Si no hay publicación exclusiva admitida, detener sin fallback a
sobrescritura. Enlaces duros dejan el mismo inode compartido hasta retirar el
temporal: los descriptores de escritura deben estar cerrados y no volver a
escribirlo. No es protección frente al propietario que modifique el archivo.
Si se propone otra primitiva, acreditar su comportamiento sin reemplazo por
plataforma; no asumir que os.replace o rename genérico conserva originales.

La sincronización del archivo y SQLite FULL son defensas locales. La
implementación RAW actual no ofrece fsync portable de directorio en Windows;
la persistencia de entradas de directorio depende del SO/filesystem/controlador
y hardware. Una publicación indivisible para otros lectores no prueba que los
bytes sobrevivan a un apagado. La primera versión no admitirá un filesystem de
red o un volumen cuya publicación exclusiva no esté comprobada.

## 4. Matriz de fallos e idempotencia

| Frontera / evidencia observada | Diagnóstico y acción admisible |
|---|---|
| Antes del commit PREPARADA | No hay ejecución conservada; no inventar registro. Si hubo un error al confirmar y no se conoce el resultado, consultar antes de repetir |
| Intención sin archivos | Conservación incompleta; conservar intención/causa, no reconstruir resultados o descargar entradas |
| Temporal corto/escritura interrumpida | Temporal parcial, nunca artefacto final; inventariar tamaño/hash observado si puede leerse, sin confundirlo con el hash esperado |
| Archivo publicado antes de referencias SQL | Posible huérfano; contrastar con intención/manifiesto/IDs. No adoptar ni eliminar automáticamente |
| SQL apunta a archivo ausente | Referencia rota, REVISION_NECESARIA; conservar fila/manifiesto y bloquear entrega íntegra. No recrear por nombre o HTTP |
| Archivo presente sin ninguna intención | Huérfano de origen no demostrado; mantener aislado lógicamente y pedir revisión. Un nombre SHA válido no demuestra pertenencia |
| Bytes presentes con hash/tamaño distintos | Corrupción/discrepancia demostrada; conservar ambos controles y causa, no actualizar el hash esperado para que coincida |
| SQLite ilegible/quick_check/FK/esquema incompatible | Detener escritura; diagnóstico acotado y recuperación desde respaldo autorizado, no recrear base vacía ni modificar sqlite_master para aceptarla |
| Manifiesto contradice SQL o informe | REVISION_NECESARIA; no elegir silenciosamente el que indique éxito ni sobreescribir el otro |
| Publicados obligatorios, falta commit de cierre | No CONSERVADA; candidato a finalización de custodia solo tras revisión y cotejo completo. No significa reanudar QA ni concluir el motor |
| Commit efectuado, retorno al llamador interrumpido | Consulta idempotente con la misma clave; si inventario/contexto coinciden y bytes revalidados, devolver la conservación existente sin ejecutar de nuevo |
| Misma clave, inventario o estado diferente | Conflicto de identidad; no overwrite ni nuevo activo por reintento implícito. Guardar evidencia del conflicto sin cambiar lo anterior |
| Hash compartido por dos ejecuciones | Compartir solo cuerpo cotejado y referencias; mantener ambas identidades, restricciones y adquisiciones. No fusionar resultados científicos |
| Permiso/error de lectura o límite de inspección | Comprobación no disponible/INCOMPLETA, no corrupción acreditada. Detener sin cambiar permisos o ampliar límites automáticamente |
| Fallo al registrar diagnóstico por disco/SQLite | Puede no existir último evento. Comunicar incertidumbre; al reabrir usar intención, inventario y bytes, no asumir cierre por ausencia de error |

Idempotencia se limita a **conservar o consultar la misma evidencia**. La clave
incluye identidad de ejecución/espacio y generación de conservación; una nueva
ejecución tiene otra clave. H_M/contexto completos permiten cotejar duplicación;
no comparar solo SHA de entrada. Una nueva comprobación añade su propio evento,
sin cambiar los bytes del manifiesto cerrado. Una recuperación o informe de
incidencia se conserva como generación/evento posterior, nunca editando el cierre.
Una consulta sin efectos puede reconocer un cierre ya confirmado aunque se haya
perdido su retorno; si hay marcador abandonado, no autoriza una nueva escritura
ni la liberación automática del control. Se informa si no pudo registrar el
evento por no disponer de coordinación/permiso.

## 5. Procedimiento de recuperación offline propuesto

1. Acordar alcance, detener escritores y comprobar raíces/identidades sin seguir
   rutas de manifiestos ajenos. No abrir ConfiguracionRAW como supuesto lector
   puro ni invocar recuperar/verificar RAW sin autorización de sus efectos.
2. Reconocer esquema/versiones y generar una vista coherente del catálogo. No
   aceptar una base incompleta por tener application_id correcto. Leer WAL exige
   procedimiento compatible y acotado; una copia ingenua del .sqlite no basta.
3. Leer intenciones y cierres acotadamente; inventariar solo el árbol autorizado.
   No recorrer RAW/staging operativo o otras raíces buscando archivos perdidos.
4. Validar manifiesto/codec estricto y relaciones; releer tamaño/SHA de cada
   artefacto requerido y comparar con las referencias esperadas. No aceptar el
   hash que acompaña al propio archivo como control independiente.
5. Validar QA0 con consumidores/conciliador existentes cuando versiones y
   evidencia lo permitan. Una repetición de validación es nueva comprobación,
   no evidencia de que una evaluación histórica ausente fue ejecutada.
6. Separar evidencia estructural conservada de revalidación física del original:
   si RAW es externo/no autorizado/desapareció, registrar ese límite. No obtener
   otra copia para presentarla como el activo histórico.
7. Clasificar con los estados de la sección 1 y causas de la sección 4. Registrar
   alcance, controles disponibles, operador/versión y fecha técnica real. Si falta
   permiso de escritura, emitir diagnóstico sin fingir que se persistió.
8. Elaborar una propuesta de intervención, sin ejecutar efectos: restauración,
   finalización de custodia o nueva ejecución. Una posible reanudación requiere
   entradas intactas, versiones y política de idempotencia/autorización propias.
   En el MVP no hay reanudación automática de QA, HTTP o motores.

Una ejecución INCOMPLETA no pasa a CONCLUIDA porque todos sus diez resultados
parciales estén guardados. Una CANCELADA sigue cancelada tras una recuperación
correcta. Tras terminación forzada puede haber solo intención/prefijo sin informe
final: conservar lo recibido y declarar que el resto no es reconstruible.

La cobertura comienza en la intención de conservación confirmada. Si el productor
solo entrega su informe al terminar, los resultados anteriores que vivían en su
RAM no están protegidos contra una muerte del proceso. Un diario de ejecución en
curso requerirá que el productor entregue checkpoints observados a esta misma
frontera, con secuencia/versión y confirmación explícitas; no se pueden obtener
retroactivamente desde una huella. El primer MVP del plan conserva informes ya
entregados y no afirma recuperar el interior de una llamada 85-G interrumpida.

La recuperación compensatoria identifica y registra; no borra originales,
reescribe valores, modifica restricciones, resuelve brechas documentales o emite
autorizaciones. No ejecuta GET ni acciones institucionales, aunque una intención
incluya una URL. Repetir una descarga exige autorización nueva para ese recurso.

## 6. Retención y limpieza propuestas

La política tendrá responsable, versión, finalidad, ámbito de producto/licencia,
categoría de artefacto, condición de conservación, bloqueos científicos/jurídicos,
referencias compartidas, cuota y procedimiento de autorización de eliminación.
**No se asignan plazos arbitrarios. Por defecto no habrá eliminación automática.**

| Categoría | Política propuesta antes de autorizar limpieza |
|---|---|
| Trazas completas e informes de cierre | Conservar inventario/controles/contexto/restricciones juntos; no retirar uno que haga incotejable al resto |
| Trazas parciales y fallos/cancelaciones | Evidencia primaria de lo ocurrido; no caducar por parecer inútil. Clasificar causa y referencias antes de cualquier decisión |
| Resultados QA y JSON | Retener originales emitidos, restricciones/versiones y vínculo al nativo/contexto; un resumen o recálculo no sustituye evidencia histórica |
| RAW | Bajo su política propia y autorización; el gestor de ejecuciones no borra ni duplica originales. Referencia científica activa impide limpieza automática |
| Documentos institucionales/referencias externas | Revisar restricciones por producto/uso. Licencia desconocida no significa libre redistribución, retención ilimitada ni permiso para borrar evidencia de una investigación |
| Temporales propios | Borrado solo tras clasificación: no referenciados, sin evidencia irremplazable, ruta/propiedad verificadas y política autorizada. Un temporal parcial incierto se conserva y señala |
| Logs/errores técnicos | Minimización, sin credenciales/cuerpos; eliminar solo con política aprobada y si no son evidencia única de fallo |
| Huérfanos | Inventario y retención precautoria para revisión; no GC automático por antigüedad o ausencia de FK |
| Cuerpos compartidos | Eliminar únicamente con inventario de todas las generaciones/referencias, sin bloqueos y autorización explícita. Un contador aislado puede estar desactualizado tras caída |

Una cuota agotada bloquea nueva conservación; no desencadena borrado de originales
o referencias previas. Las cuotas lógicas deben contar tanto cuerpos como DB,
journals, temporales y residuos. Avisar antes de agotar espacio y conservar margen
para diagnóstico no constituye reserva física. La compactación SQL/GC tendrá un
incremento y pruebas propios; no forma parte del MVP del 85-J.

La futura eliminación requeriría plan revisable, referencias comprobadas,
respaldo/retenciones legales aplicables y eventos/tombstones persistidos antes
de actuar. Ante interrupción del borrado debe ser posible saber qué se autorizó
y qué falta. No se especifica aquí un borrador ejecutable ni se realizan limpiezas.

## 7. Respaldo y restauración propuestos

**Recuperación de ejecución** diagnostica/conserva lo presente después de una
interrupción. **Restauración** repone una generación desde un respaldo previamente
conservado; no repite HTTP o QA, ni demuestra que una ejecución incompleta terminó.
No hay hoy gestor general de respaldo/restauración en esta cadena.

Plan mínimo para un futuro respaldo consistente, bajo autorización específica:

1. Seleccionar generación y bloquear nuevos cambios del escritor. Fijar el
   inventario de ejecuciones y las referencias a originales externos que se
   incluirán o quedarán expresamente fuera; no copiar RAW incidentalmente.
2. Obtener snapshot SQLite con mecanismo compatible, por ejemplo sqlite3.backup
   bajo coordinación; es una propuesta, no función integrada ya disponible.
   Considerar WAL/journal mediante SQLite, no copiar solo el archivo principal
   mientras hay commits. No usar inspección RAW como respaldo atómico global.
3. Copiar por bloques los artefactos inmutables de esa generación, conservar
   manifiestos/controles/esquemas/versiones y referencias; impedir GC durante la
   captura. Registrar tamaño/hash físico de cada copia y cotejar con inventario.
4. Cerrar y verificar la copia en aislamiento; registrar generación, alcance,
   fecha técnica, resultado y faltantes. Si faltan dependencias externas, el
   respaldo es incompleto para revalidarlas, aunque las trazas estén intactas.
5. Mantener el respaldo fuera del dominio de fallo cuando se requiera resiliencia.
   Una copia en el mismo disco no cubre su pérdida; si el escritor puede alterar
   copia y controles, tampoco aporta autenticidad independiente. Ubicación,
   custodia, frecuencia y plazos necesitan aprobación, no se inventan aquí.

Restauración prevista: seleccionar respaldo y control confiables, autorizar raíz
vacía aislada, comprobar espacio/permisos/esquema sin migración implícita, restaurar
DB y cuerpos de la **misma generación**, releer hashes y verificar estructura/FK,
inventario, referencias, estados/restricciones y compatibilidad de lectores.
Detectar fuentes RAW externas no incluidas; no declarar que fueron restauradas.
Solo después de ensayo/revisión se plantearía activar una ubicación operativa;
no sobreescribir una base/original existente para reparar. Incompatibilidad de
versión bloquea y conserva evidencia; migración/restauración son actos distintos.

La batería sintética futura incluye restauración, pero no se ha ejecutado y no
autoriza respaldo operativo. Hasta implementarla y ensayarla, el MVP quedará
limitado a evidencia experimental prescindible y reconstrucción autorizada;
no será custodia única de evidencia irremplazable.

## 8. Límites de garantía y decisiones de revisión

El modelo inicial es privado, secuencial y con código/usuario/OS confiables.
SQLite protege sus propias transacciones conforme a su configuración y soporte;
no sincroniza automáticamente archivos RAW, el otro catálogo y artefactos. Las
comparaciones físicas detectan discrepancias observables; no certifican historia,
autoría, exactitud científica, derechos o ausencia de alteración coherente de todo
el expediente. Un control independiente necesita custodia realmente independiente.

Simular errores OSError/SQLite, matar un subproceso y reiniciarlo prueba fronteras
de proceso en un equipo/fixture; **no demuestra resistencia a corte eléctrico**,
cachés de hardware, sectores defectuosos o modificaciones hostiles. No efectuar
apagados reales ni presentar pruebas unitarias como ese ensayo.

Antes de 85-J se deben revisar: ampliación versionada del catálogo científico,
esquema del codec y manifiesto, límites/single-writer, política de temporales y
alcance de recuperación sin original disponible. Custodia independiente,
respaldo operativo, concurrencia multiusuario, GC y durabilidad fuerte quedan
pendientes. Ninguna decisión abre /query INGEMMET, QA1 o adquisiciones PNDA.
