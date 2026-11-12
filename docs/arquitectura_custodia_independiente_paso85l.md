# PASO 85-L — Custodia independiente y respaldo offline: diseño para revisión

Fecha: **2026-11-12, America/Lima**. Base **d3372a0**, rama
`feature/suadc-http`, Git inicialmente limpio; el commit consolida 85-K.
Este documento propone políticas y contratos conceptuales. **No implementa una
referencia nueva, no genera claves, no realiza respaldos ni autoriza ciencia.**
Los otros entregables son el [modelo de amenazas y dominios de fallo](modelo_amenazas_dominio_fallo_paso85l.md)
y la [evaluación de madurez y cierre](evaluacion_madurez_arquitectonica_paso85l.md).

## 1. Base comprobada y alcance de las garantías

Se contrastaron los [tres documentos de 85-K](arquitectura_respaldo_restauracion_paso85k.md),
su [piloto](piloto_respaldo_restauracion_paso85k.md) y sus
[brechas](brechas_custodia_paso85k.md), con el
[conservador 85-J](../herramientas/conservacion_linaje_85j.py),
[índice 85001](../herramientas/_catalogo_linaje_85j.py),
[codec](../herramientas/_codec_linaje_85j.py) y
[gestor 85-K](../herramientas/respaldo_linaje_85k.py).
Las referencias y decisiones anteriores se enumeran en el tercer entregable.
1884 aprobadas es la evidencia histórica del 85-K; no se ejecuta otra suite aquí.

| Propiedad | Evidencia existente | Alcance que sigue pendiente |
|---|---|---|
| Integridad física local | Tamaño/SHA por relectura, inventario, DDL/FK/quick_check y cotejo 85-H | No atribuye autoría ni protege un control reescrito junto a los bytes |
| Consistencia de generación | Una ejecución conservada, tablas base vacías, SQLite DELETE sin auxiliares, marcador cooperativo, backup API y generación antes/después | No snapshot atómico global ni escritores hostiles; no respaldo RAW/general |
| Restauración | Copias independientes, raíz nueva y lector 85-J en otro proceso, mismas identidades/estados/restricciones | No otro dispositivo, cuenta, equipo o volumen de fallo probado |
| Interrupción | Parciales/intenciones/marcadores detectables; pruebas y cierres abruptos documentados | No recuperación automática ni resistencia eléctrica demostrada |
| Control explícito | ControlRespaldo85K recibido por argumento fuera del manifiesto | No existe mecanismo que acredite su custodia/protección independiente |

No se usa la cadena «archivo → SHA → manifiesto → SQLite» como si fuera una firma.
85-J conserva I/T/R; su manifiesto M registra sus hashes y SQLite confirma H_M y
referencias. 85-K toma un snapshot de ese SQLite y los cuerpos, y su manifiesto B
inventaría siete archivos; ControlRespaldo85K conserva H_B y la generación lógica.
El SHA de SQLite y la generación lógica de sus filas son controles diferentes.

## 2. Niveles de confianza que no deben confundirse

| Mecanismo | Lo que permite bajo sus supuestos | Lo que no demuestra |
|---|---|---|
| Hash interno | Contrastar bytes con el hash suministrado, detectar discrepancias accidentales | Que el hash esperado sea previo, independiente o auténtico |
| Referencia conservada separadamente | Comparar con una copia previamente aceptada fuera del expediente leído | Protección si la misma cuenta/programa puede reescribir ambas copias |
| Control protegido contra modificación | Detectar sustitución respecto de un ancla cuya protección y custodia se comprobaron | Autor institucional del recurso, fecha ambiental o validez científica |
| Firma digital con clave independiente | En un diseño futuro, verificar firma y vínculo de clave conforme a su política | Que la clave pertenezca a SENAMHI o que el contenido firmado sea científicamente correcto |
| Autenticidad institucional | Requeriría evidencia del emisor/canal/clave o procedimiento institucional aplicable y revisado | No se deriva de los mecanismos locales anteriores |

La independencia tiene tres dimensiones: **ubicación física, autoridad de escritura
y origen de confianza**. Cambiar carpeta o proceso solo cambia algunas de ellas.
Un usuario individual puede separar la exposición de sus copias, pero no se
convierte por ello en un custodio institucional independiente. No se propone PKI,
gestión de claves, servicio permanente, nube obligatoria o una segunda base lógica.

## 3. Referencia externa mínima propuesta

Preferencia: una referencia breve por generación aceptada, legible offline,
conservada fuera de la raíz respaldada y fuera de su exposición de escritura.
Se propone una representación documental **0.1.0 para revisión**, todavía sin
parser, archivo generado o compatibilidad de lectura declarada. No modifica los
formatos existentes 0.1.0 ni el esquema 85001.

| Campo conceptual | Procedencia y regla |
|---|---|
| Identidad y versión de referencia | Identidad lógica propia; no nombre de archivo, ruta o letra de unidad |
| Inventario de controles | Una entrada inicial; unicidad por respaldo y generación. Cada entrada contiene exactamente el triple existente respaldo_id/generacion_sha256/manifiesto_sha256 |
| Identidades vinculadas | Instancia, ejecución y conservación obtenidas del conjunto validado; deben concordar con B, nunca reemplazar sus valores |
| Versiones de interpretación | Respaldo, conservación, codec y SQLite esperados; una versión desconocida produce incompatibilidad, no migración |
| Alcance del conjunto | Evidencias 85-K y exclusiones explícitas, especialmente RAW no incluido; no llamarlo respaldo completo de SPICA |
| Fecha UTC declarada | Metadato técnico del registro, con su procedencia; no sello independiente, orden causal seguro o prueba de autenticidad |
| Referencias de confianza previamente aceptadas | ID de control/acta anterior y su relación, si existe. Ausencia explícita; no fabricar una cadena retrospectiva |
| Registro de aceptación y custodia | Responsable referido sin credenciales, medio opaco, protección comprobada, dominio de fallo y decisión humana documentada |
| Restricciones | Mismo alcance y límites del conjunto validado; ni el registro ni la referencia conceden permiso operativo o científico |

Los campos descriptivos duplicados deben cotejarse con B; no constituyen una
segunda autoridad para corregir B/SQL. El inventario puede relacionar controles
individuales existentes; no necesita otro catálogo SQLite, copiar todos los cuerpos
al control o cargar todos los respaldos en RAM. Una futura lectura requerirá
esquema estricto, cotas de bytes/entradas/profundidad, versiones cerradas y cero
expresiones/imports ejecutables. Esas cotas se acordarán para el caso; no se crean
valores operativos nuevos en esta auditoría.

Relación acíclica propuesta:

```text
I/T/R → manifiesto 85-J → confirmación SQLite
snapshot SQLite + cuerpos + intención + marcador → B → H_B
(respaldo_id, generación, H_B, versiones, alcance) → referencia externa aceptada
referencia externa → custodia física/protección revisadas por el responsable
```

No hay hash autocontenido que certifique su propio origen. La cadena termina en
una referencia aceptada bajo una protección ajena al escritor, no en otro JSON
reescribible junto al primero. Guardar el control en Git del mismo equipo no lo
protege de la misma cuenta ni acredita licencia para publicar sus metadatos.

### Aceptación, sustitución y pérdida del control

Tras verificar físicamente una captura en un entorno confiable, el responsable
contrasta el triple completo y las versiones, registra el alcance y conserva la
referencia separada. Para el usuario individual, un registro impreso comprobado y
guardado aparte puede separar el ancla de la escritura del equipo. Alternativa:
medio desconectado con protección de escritura efectiva comprobada. «Solo lectura»
en una etiqueta o una segunda carpeta no acredita esa protección. No se imprime,
escribe en medios ni configura permisos en este paso.

Una futura verificación toma el control del canal previamente aceptado, no lo
recalcula desde el respaldo candidato. Coincidencia local con referencia ausente
se informa como **integridad local sin cotejo independiente**. Si no es legible,
se perdió o discrepa, se detiene la afirmación de integridad independiente. Nunca
se actualiza automáticamente el hash esperado para aceptar los nuevos bytes.

Una copia antigua íntegra no demuestra ser la última aceptada. El responsable
necesita un inventario/recibo previo de generaciones aceptadas y relaciones de
sustitución o revocación. No elegir por mtime, nombre, mayor fecha o un campo
«aprobada» aportado por el archivo. Corregir un error de transcripción o sustituir
una referencia requiere revisión y registro conservando el control anterior y la
causa. Una cadena local de hashes puede ser reescrita entera: no sustituye al ancla.

## 4. Respaldo offline mínimo para un usuario individual

**Propuesta, no procedimiento disponible para datos operativos.** Conservar la
copia de trabajo local, una generación verificada en una unidad física externa
desconectable y una referencia aceptada fuera de su exposición conjunta. Para
tolerar pérdida/robo de la computadora, esa copia debe guardarse fuera de ella;
para un suceso del lugar, también en otro lugar. La separación debe probarse,
sin presumirla por la letra del volumen. Véase la matriz del segundo entregable.
La custodia de una segunda copia de control reduce riesgo de pérdida de referencia;
no se prescribe aquí un calendario ni un plazo de retención.

Secuencia conceptual:

1. Acordar alcance y derechos de copia privada, responsable y destinos autorizados.
   Declarar qué originales, documentos, resultados e índices deben sobrevivir.
2. Identificar dispositivo/dominio, soporte de publicación exclusiva, espacio y
   permisos efectivos. No seguir rutas/órdenes contenidas en el manifiesto.
3. Detener escritores cooperativos y fijar un corte lógico de todos los componentes
   incluidos. Usar mecanismos SQLite soportados; no copiar DB activa omitiendo WAL.
   El perfil actual rechaza auxiliares; no se les aplica limpieza automática.
4. Crear una generación exclusiva con copias independientes y lectura por bloques;
   verificar tamaño/SHA, referencias, estados, versiones, restricciones e inventario.
   Un disco lleno/copia incompleta deja parcial diagnosticable, nunca reemplaza la
   última generación aceptada. No se reintenta sobre el destino incierto.
5. Registrar y cotejar la referencia externa, cerrar todos los manejadores y
   retirar/desconectar el medio de forma controlada. No inferir persistencia física
   de un retorno exitoso o de un único fsync.
6. Ensayar restauración autorizada a otra raíz; comprobar usando lectores existentes,
   después retirar la disponibilidad del respaldo de entrada y volver a leer la
   restauración. No confundir referencias históricas con localizadores actuales.
7. Registrar resultados/limitaciones y generaciones pendientes de respaldo; conservar
   las anteriores hasta resolver sus dependencias y aprobar cualquier retirada.

El respaldo «completo» es siempre **completo respecto de un alcance explícito**.
85-K copia evidencia de una ejecución, no su RAW, todo el catálogo científico,
documentos institucionales o una instalación. Antes de custodia operativa debe
especificarse el cierre de referencias pertinente: bytes originales y catálogos
que los identifican, evidencia documental necesaria y derivados si los hay.
Una lista de asset_id/SHA en una traza no conserva los bytes ausentes.

**Límite de compatibilidad actual:** _raiz_respaldo y _raiz 85-J solo admiten TEMP.
Además _validar_informe exige que la raíz histórica tenga como padre el TEMP del
lector. Otra cuenta/equipo con TEMP distinto no tiene portabilidad acreditada y
puede ser rechazado aunque los bytes estén íntegros. Esta condición se deduce de
inspección, no de una prueba nueva entre equipos. La estrategia externa necesita
un perfil de destino y portabilidad revisados y probados antes de implementarse;
no basta pasar una nueva ruta a 85-K o desactivar sus validaciones.

### Qué automatizar y qué debe acreditar el responsable

| Verificable por un programa dentro de su alcance | Acción/evidencia del responsable |
|---|---|
| Esquema/versiones/IDs, tamaño y SHA, inventario, estados y restricciones | Que la referencia esperada procede de la custodia aceptada y no del candidato |
| Cotas de I/O, cancelación por fronteras, espacio observado, destino exclusivo | Autorizar alcance/ubicación; espacio libre no es una reserva |
| Lector independiente, independencia de archivos y ausencia de dependencia de la copia de entrada | Identificar dispositivo físico, desconectar, guardar fuera del equipo/lugar y dejar constancia |
| Registrar discrepancia/error/incompletitud sin reparar | Determinar causa, permisos de uso, aceptación/revocación y recuperación manual autorizada |

RPO propuesto como criterio, no valor numérico: inventariar exactamente qué
generaciones/entradas únicas quedarían sin recuperación desde el último respaldo
aceptado y aceptar explícitamente esa pérdida máxima antes de uso operativo.
RTO: medir tiempo de restauración/verificación en el equipo/medio de destino y
acordar objetivo. No se fijan horas, costes, periodicidades o SLA sin ese caso.
RAM, disco y tiempo tienen presupuestos por etapa; el pico incluye origen,
snapshot, copias, parciales y restauración. Las cotas 85-K no son cotas RAW ni RSS.

### Protocolo conceptual de verificación

Este protocolo es diseño, no una operación ejecutada sobre datos reales. Cada
paso conserva evidencia de alcance, versión y resultado. No se da éxito global
si una comprobación requerida no pudo realizarse.

| ID | Comprobación y criterio | Capacidad actual / evidencia adicional |
|---|---|---|
| V01 | La generación existe: identidad/versión, intención y confirmación lógica pertenecen al mismo conjunto; ausencia no se rellena | Perfil 85-J/K comprobado históricamente en TEMP; ampliar el cierre de referencia requiere perfil propio |
| V02 | Todos los archivos obligatorios están presentes, son regulares y accesibles; inventario cerrado, sin extras/residuos incompatibles | Lector/arbolado acotados existentes; permiso denegado no demuestra corrupción |
| V03 | Tamaño y SHA físicos de cada archivo y del manifiesto coinciden con controles esperados, mediante bloques y cotas | Implementado en 85-K; no basta comparar nombres o hashes declarados |
| V04 | El triple de respaldo/generación/H_B coincide con la referencia previamente aceptada desde el canal protegido | Comparación del triple existe; custodia/protección/canal y control antiguo/perdido son diseño pendiente, no capacidades acreditadas |
| V05 | Instancia, ejecución, conservación y demás IDs históricos son coherentes; la restauración solo crea ID de su operación | Contraste J/K e igualdad tipada probados; no confundir asset_id con hash o nueva adquisición |
| V06 | SQLite corresponde a la generación: esquema/application_id/versión, FK, comprobación de consistencia, filas y referencias coinciden | Snapshot API 85001 y generación lógica comprobados; solo perfil inactivo aceptado, auxiliares incompatibles bloquean |
| V07 | Estado de conservación, recuperación e historia están separados; no promover FALLIDA/INCOMPLETA/CANCELADA por restaurar bien | Lectores/cotejo existentes; no se reanuda QA ni se cambia la historia |
| V08 | Restricciones, errores, incertidumbres, versiones y campos desconocidos sobreviven íntegros en informe/traza/salida | Igualdad y controles J/K probados; no convertir coherencia en permiso o ciencia |
| V09 | La copia restaurada vuelve a leerse cuando el respaldo de entrada está indisponible; sin enlaces a sus únicos bytes | Independencia física de archivos probada en TEMP; retirada de otro dispositivo y portabilidad en otro perfil aún requieren ensayo autorizado |
| V10 | Corrupción, ausencia, incompatibilidad, falta de permiso, presupuesto y cierre incierto producen diagnóstico diferenciado y parada, sin reparación silenciosa | Errores/estados del perfil existentes; registro durable universal y tratamiento manual operativo pendientes |

Un programa puede comparar contra un control que recibió; no puede acreditar por
esa sola comparación que su canal era independiente. Otro proceso en TEMP permite
V01–V03/V05–V08 y fallos sintéticos de V10; V04 necesita aceptación/protección reales,
y la tolerancia de V09 a fallo de disco/equipo requiere separación física y lector
compatible. Ningún resultado de esta tabla prueba metrología o autor institucional.

## 5. Custodia, retención y eliminación

| Objeto | Conservación y relaciones que deben mantenerse |
|---|---|
| Evidencia primaria/original | Bytes exactos, identidad de activo/adquisición y controles; no sustituir por una traza, derivado o nombre SHA |
| Evidencia derivada | Entrada, método/código/versión/parámetros, unidades, alcance, incertidumbre y restricciones; separada de originales |
| Traza | Relaciones y eventos observados, fallos y límites; no prueba por sí sola que sobreviva la entrada |
| Informe | Valores tipados, nativos/prefijos y estados reales necesarios para cotejo; sin rellenar etapas no ejecutadas |
| Manifiesto | Inventario cerrado y referencias de su generación, sin actualización silenciosa |
| Referencia de control | Conservación separada, protección/aceptación y registro de cambios/pérdidas; no una credencial |
| Índice SQLite | Mismo corte lógico y versión que los archivos; no se presume reconstruible automáticamente desde blobs |
| Copia de respaldo | Generación y alcance completos verificados, control y ensayo de restauración; no una carpeta informal de copias |
| Temporal/parcial | Propietario y estado conocidos. Un parcial incierto o referenciado queda pendiente de revisión; no es basura por su antigüedad |

No se aprueban plazos arbitrarios, TTL, GC o eliminación automática. Una retirada
futura requerirá inventario de referencias entrantes/salientes y dependencias
transitivas, incluyendo originales compartidos, adquisiciones distintas con el
mismo contenido, informes, derivados y controles de generaciones anteriores.
Un SHA compartido no permite eliminar identidades ni historial de adquisiciones.

Antes de retirar algo: comprobar obligaciones de conservación y derechos aplicables,
ausencia de bloqueo de revisión/incidente, sustitución realmente verificada y
restaurable, preservación de registros/controles necesarios y aprobación explícita
del alcance de eliminación. No se elimina la única copia íntegra para liberar
espacio. Si el espacio no alcanza, detener y revisar; no reciclar evidencia incierta.
Eliminación lógica no acredita borrado forense/seguro de un medio; no se diseña ni
ejecuta ese procedimiento aquí.

La copia privada autorizada y la entrega/publicación a terceros son usos distintos.
Una licencia declarada, un recurso públicamente visible o un test aprobado no
demuestran permiso universal para copiar, redistribuir o divulgar metadatos.
Si no puede acreditarse un derecho necesario, registrar y bloquear ese uso; no
inventar una autorización jurídica. No se revisan condiciones externas en 85-L.

## 6. Diseño preferido y límite de decisión

Se prefiere custodia offline sencilla: generación verificable, control breve
protegido/separado y copia desconectada en un dominio identificado, con revisión
manual de incidentes. Sin nueva base, servicios distribuidos, GUI o automatización.
Esto **sigue diseñado, no implementado**. Tampoco se transforma la copia TEMP en
respaldo de desastre por describirla así.

La [decisión C](evaluacion_madurez_arquitectonica_paso85l.md#decision) propone
avanzar, tras revisión, al expediente de un experimento científico enteramente
sintético y delimitado. La custodia operativa no es su prerrequisito si todas las
entradas son reconstruibles y sus resultados son prescindibles/en memoria.
Sí lo es antes de confiar datos únicos o una instalación permanente al mecanismo.
No se activa ningún módulo, ejecuta ciencia o inicia otro incremento en este paso.
