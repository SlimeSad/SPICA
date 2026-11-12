# PASO 85-I — Plan de implementación y aceptación de persistencia

Elaboración: **2026-11-12, America/Lima**. Revisión base **a044b49**, rama
feature/suadc-http, árbol inicialmente limpio. **Plan pendiente de revisión; no
implementado ni ejecutado.** Complementa la
[arquitectura](arquitectura_persistencia_linaje_paso85i.md) y el
[protocolo](protocolo_recuperacion_ejecuciones_paso85i.md). La implementación
propuesta no inicia el PASO 85-J por sí misma.

## 1. Alcance mínimo recomendado para 85-J

Un solo incremento experimental: **conservar y recuperar en otro proceso una
evidencia sintética acotada**, con índice SQLite reutilizado y artefactos
inmutables, sin ejecutar motores durante la recuperación. Cubrir cierre completo,
fallido, incompleto y cancelado con los contratos/restricciones reales.

No crear otro transporte, RAW, motor QA, consumidor, conciliador, catálogo de
fuentes, scheduler o ejecutor de PlanConsulta. No persistir derivados científicos
ni activar reglas Nivel 1. No usar RAW/staging/SQLite operativos para el ensayo.

El MVP cubre interrupciones desde que el conservador recibe la evidencia y
confirma su intención; no protege resultados anteriores que solo existan en RAM
del productor. Incorporar checkpoints durante la ejecución, si se requiere esa
garantía, será una ampliación posterior de la misma frontera, con alcance y
pruebas propios. No presentarlo como diario durable de toda la cadena 85-G.

El ensayo conservará el informe/evidencia realmente emitidos por el perfil
85-G/H, mediante un **codec explícito nuevo y acotado**, y su traza histórica
cuando exista. Es necesario conservar resultados nativos parciales, no solamente
sus huellas. Guardar diez nativos no autoriza afirmar diez JSON exportados si
la exportación no comenzó. Los consumidores oficiales siguen validando únicamente
documentos producidos y las versiones que realmente admiten.

El arnés actual elimina su entrada RAW: el primer ensayo de persistencia puede
reabrir **artefactos de ejecución**, no ese original eliminado. Deberá declarar
referencia histórica no revalidable, conservando SHA/tamaño como evidencia de una
lectura pasada. No cambiar temporales_eliminados para simular que el arnés retuvo
un almacén ni recrear bytes con el mismo SHA y atribuirles el antiguo asset_id.

Si un ensayo posterior exige revalidar también la entrada, su propietario de
temporales deberá conservar un RAW sintético existente con vida independiente
entre procesos, mediante las APIs RAW actuales. Esa composición mínima necesita
revisión propia, sin duplicar el motor vertical ni cambiar el contrato 85-G para
ocultar su semántica de eliminación. Las referencias externas de la arquitectura
admiten ambos casos y registran el alcance de lectura permitido. No es condición
para conservar una traza histórica poder volver a ejecutar su entrada.

## 2. Prioridades y dependencias

P0 identifica condiciones que bloquean una conservación engañosa o pérdida de
evidencia; P1 completa el MVP; P2 amplía robustez/operación; P3 queda fuera del
perfil secuencial. Son prioridades del plan, no defectos nuevos demostrados.

| ID / prioridad | Trabajo / criterio esencial | Dependencia |
|---|---|---|
| P0-01 | Preservar nativos parciales, JSON realmente producido, desconocidos, restricciones, errores y estados; nada se promueve a ciencia/permiso | Auditoría I01/I02, contrato de artefactos |
| P0-02 | Publicación exclusiva y rutas controladas, sin sobrescribir ni borrar evidencia ajena; rechazar cambio de raíz/conflicto | Modelo privado de escritor único y política de publicación |
| P0-03 | Cierre lógico solo después de cotejo físico, inventario y referencias; detectar archivo/fila huérfanos sin falsa atomicidad o autenticidad | Protocolo y DAG de hashes |
| P1-01 | Codec/manifiesto versionados, parser cerrado y cuerpos referenciados con tamaños/hashes; diferenciar fuente declarada de observada | P0-01; revisión de formatos/compatibilidad |
| P1-02 | Extensión explícita del catálogo científico: instancia, intenciones, inventario, referencias y eventos; esquema antiguo reconocido y nunca migrado al abrir | P0-03; decisión de versión/lector DDL |
| P1-03 | Adaptador de conservación/publicación sobre SQLite y filesystem locales; presupuestos/cancelación y control de un escritor | P0-02, P1-01/02 |
| P1-04 | Reapertura/diagnóstico offline, idempotencia de conservación y conflictos sin reparación automática | P1-03; estados ortogonales |
| P1-05 | Pruebas sintéticas de proceso y fallos, regresiones y revisión de evidencia; límites operativos explícitos | P1-01 a P1-04 |
| P2-01 | Implementar/ensayar respaldo y restauración consistentes por generación, primero sintéticos | MVP revisado; antes de ofrecer custodia única o uso operativo |
| P2-02 | Medir RAM/disco/tiempo, paginar índices y fragmentar lotes si se necesita; no quitar relecturas de integridad | Volumen y hardware representativos acordados |
| P2-03 | Retención configurable aprobada, cuotas de largo plazo, GC/limpieza y tombstones ante interrupción | Inventario íntegro, referencias compartidas, obligaciones de cada producto y respaldo probado |
| P2-04 | Revalidación de fuentes externas autorizadas, conservación de RAW sintético entre procesos y cancelación más fina donde falte | Alcance separado; no modifica la evidencia del piloto histórico |
| P2-05 | Checkpoints observados durante la ejecución para proteger prefijos antes de que el productor retorne | Contrato de entrega/secuencia y pruebas de interrupción por fase; reutilizar el mismo conservador, sin otra arquitectura de diario |
| P3-01 | Varios escritores/usuarios, coordinación ampliada y fronteras de proceso/OS | Modelo de amenaza, autorización y pruebas nuevos |
| P3-02 | Autenticidad independiente automatizada, firmas/custodia de claves si se requieren | Política de confianza/custodios aprobada; sin PKI ahora |
| P3-03 | Derivados científicos, UI/GIS/IA opcionales, ejecución institucional y distribución | Contratos/evidencia/aplicabilidad/autorización propios; no dependencias del MVP offline |

El respaldo se sitúa en P2 **solo para un MVP sintético prescindible**. Si se
pretende almacenar evidencia única o declarar preparación operativa, P2-01 es
prerrequisito de aceptación de ese uso. Eliminar evidencia o soportar escritores
hostiles tampoco es una extensión implícita del MVP.

## 3. Secuencia mínima y contratos afectados

| Bloque | Implementación futura propuesta | Reutilización y compatibilidad exigida |
|---|---|---|
| A. Fijar perfil/formatos | Revisar campos de ContextoConservacion, InformeConservable, EvidenciaParcial, ManifiestoCierre y eventos del 85-I; elegir versiones y límites explícitos | Mantener DTO 85-G/85-H, EstadoEjecucion85G, versiones QA/JSON y estados anteriores; no convertir diseño en nueva aprobación |
| B. Frontera de serialización | Codec de tipos conocidos, snapshot sin rutas sensibles, referencias a cuerpos; lectura estricta con capacidades de cotejo declaradas | Usar exportar_resultado_json/consumir_exportaciones/conciliar_lotes para sus contratos. Nada de pickle/imports arbitrarios. No acoplar src a herramientas ni copiar parsers privados de consumo |
| C. Índice versionado | Tablas conceptuales de identidad de instancia, intenciones de conservación, artefactos, referencias y eventos dentro del catálogo científico ampliado | Justificación I03: validador actual solo admite DDL exacto v1. Cambiar versión/validador bajo prueba, no agregar tablas a v1 ni a RAW. Nuevo esquema únicamente en base sintética vacía; migraciones de bases preexistentes fuera del MVP |
| D. Publicación/commit | Un adaptador de persistencia con política de rutas/presupuesto y transacciones cortas; publicar cuerpos/manifiesto y confirmar inventario conforme al protocolo | Patrón de publicación RAW reutilizable, no almacenar trazas mediante incorporar como si fueran originales. Extraer un helper común solo si se demuestra necesario, con regresiones y alcance revisados |
| E. Consulta/recuperación | Lector offline y diagnóstico, con devolución de estados/capacidades/causas, idempotencia limitada a conservación | No repetir GET/QA, no llamar APIs RAW con efectos como supuesto modo lectura, no reconstruir informe 85-G inventado para pasar el cotejo 85-H |
| F. Ensayos/cierre | Subproceso de escritura termina y otro abre/verifica; errores inyectados por frontera y guardias de no acceso; revisión del informe | Directorios temporales aislados, datos sintéticos, MockTransport solo si el ensayo crea la evidencia inicial. Ninguna conexión externa ni almacenamiento operativo |

La ubicación del adaptador nuevo deberá acordarse como una única frontera de
persistencia de ejecución, sin otro orquestador. El puente desde herramientas
traduce su informe al contrato persistible; la biblioteca no debe importar el
arnés para ejecutar pilotos. Si la compatibilidad exige extraer un contrato
auxiliar, justificarlo antes de cambiar interfaces anteriores y probar imports.

La ampliación SQLite necesitará una API transaccional explícita para intenciones,
referencias y cierre. No permitir acceso del nuevo dominio a _conexion ni DDL
definido por un archivo de reglas. El historial de fuentes/revisiones y el
inventario de ejecuciones conservarán responsabilidades distintas dentro de la
misma base; no falsear recursos o revisiones documentales para guardar estados.

Las identidades entre RAW y catálogo permanecen referencias comprobadas, sin FK
ficticia entre bases. Proponer un catalogo_instance_id nuevo no permite inferirlo
de application_id o de la ruta de un catálogo antiguo. Lectores v1 actuales no
leerán el esquema ampliado: compatibilidad debe documentarse por versión y
operación, no prometer compatibilidad bidireccional automática. No hay migración
operativa autorizada por este expediente.

## 4. Batería sintética diseñada, no ejecutada

Los T01–T21 cubren los 21 casos solicitados; T22–T26 añaden fronteras reveladas
por la auditoría. Son escenarios de aceptación propuestos, **no métodos unittest
implementados ni un número nuevo de pruebas aprobadas**. Cada escenario podrá
necesitar varios métodos/subcasos; no se suma al resultado histórico de 1791.

| ID / prioridad | Preparación futura / fallo controlado | Evidencia de aceptación |
|---|---|---|
| T01 / P1 | Conservar informe completo sintético y traza original | Inventario/bytes/hashes/contexto/restricciones recuperables; estado de motor y conservación diferenciados; fuente eliminada se declara no revalidable |
| T02 / P1 | Límite QA deja nativos parciales, sin exportación | Recuperar todos los emitidos, causa y ausencias; nunca JSON ni cierre QA inventados; ejecución INCOMPLETA |
| T03 / P1 | Cancelación antes y después de producir evidencia | CANCELADA conservada con prefijo real, sin fases/activo inventados; cancelación durante conservación no pierde evidencia previa |
| T04 / P1 | Escritor y lector en procesos distintos, temporal administrado por el padre del ensayo | El segundo reconstruye evidencia/versiones/restricciones desde archivos/SQL sin objetos Python vivos del primero; no usar rutas del RAW que 85-G borró |
| T05 / P1 | Interrumpir escritura de un artefacto | Temporal parcial identificado, no publicado/entregado como completo, intención preservada y recuperación INCOMPLETA |
| T06 / P1 | Referencia SQL confirmada cuya copia de artefacto de prueba se retira | Referencia rota y REVISION_NECESARIA; no sustituir archivo ni modificar control esperado |
| T07 / P1 | Publicar archivo y fallar antes de referencias, o archivo totalmente ajeno en raíz de prueba | Huérfano inventariado; no adopción/borrado automático; distinguir con/sin intención |
| T08 / P1 | Alterar bytes manteniendo control esperado o aportar hash declarado falso | Relectura SHA/tamaño detecta discrepancia, conserva ambos valores y bloquea entrega íntegra |
| T09 / P1 | SQLite falla en preparación, registro de referencias o commit final | No falso CONSERVADA; rollback de fila/evento juntos; archivos publicados visibles para diagnóstico |
| T10 / P1 | ENOSPC y escritura corta inyectados en cuerpo/manifiesto/evento | Error explícito, original previo intacto, no borrado para ganar espacio; incertidumbre si no pudo persistirse diagnóstico |
| T11 / P1 | Permiso denegado en lectura/escritura/publicación/cierre | Comprobación no disponible diferenciada de corrupción; sin modificar ACL y sin ruta/secretos en el error |
| T12 / P1 | Cambiar ancestro por symlink/junction o sustituir archivo durante lectura en fixture | Rechazo o discrepancia observable, sin escape/escritura fuera de raíz. Si la plataforma impide crear enlaces, documentar cobertura no ejercida; no declarar defensa contra atacante universal |
| T13 / P1 | Repetir conservación tras perder retorno del commit | Misma clave/inventario devuelve evidencia existente tras cotejo, sin segunda ejecución, adquisición o archivo sobrescrito |
| T14 / P1 | Reutilizar clave de ejecución con otro inventario/contexto | Conflicto explícito sin alterar anterior; dos ejecuciones distintas con mismo SHA siguen separadas |
| T15 / P1 | Esquema/codec/traza/QA de versión no admitida | Rechazo con causa, no migración ni importación dinámica. Lectura del catálogo v1 histórico preservada, sin añadirle tablas de ejecución |
| T16 / P1 | JSON truncado, claves duplicadas, tipos/IDs/referencias/estados contradictorios o DB dañada | Lectura estricta bloqueada o REVISION_NECESARIA; ninguna reparación silenciosa ni adopción por application_id |
| T17 / P2 | Respaldar y restaurar generación sintética coherente en raíz aislada | DB/artefactos/restricciones/hashes coinciden, referencias externas excluidas explícitas; mezcla de generaciones o versión incompatible rechaza |
| T18 / P1 | Omitir/cambiar restricciones en artefacto/informe/manifiesto o consumo | Rechazo; bloqueo y diagnóstico sobreviven reinicio. Restricciones oficiales por resultado no sustituidas por solo totales |
| T19 / P1 | Manifiesto válido afirma ciencia/permiso o autocertifica su SHA | Sin promoción a ciencia/autenticidad/permiso. Control procedente del propio documento no cuenta como aprobación independiente |
| T20 / P1 | Guardias de socket/DNS/HTTP real durante conservación/recuperación | Cero red y cero GET en recuperación; URLs se tratan como referencias. Crear evidencia con MockTransport sigue etiquetado como simulación |
| T21 / P1 | Guardia de rutas operativas y sqlite3.connect, E/S limitada al árbol temporal del ensayo | Ningún acceso a RAW/staging/SQLite/CSV/evidencia PNDA operativos; no usar inventario/hash de esos recursos como prueba de no acceso |
| T22 / P1 | Fallar exportación después de un prefijo y conservar nativos sin documento | Todos los nativos emitidos y JSON exactos realmente producidos sobreviven; no IDs de resultado exportado inventados; codec no pierde None/orden/valores |
| T23 / P1 | Cambiar informe o traza conservando referencia previa, después cambiar los tres coherentemente | Primer caso detecta alteración; segundo demuestra límite del dominio local, sin afirmar autenticidad independiente. DAG sin hash autorreferente |
| T24 / P1 | Dos solicitantes cooperativos intentan conservar en la misma raíz | Segundo rechazado/espera acotada, sin doble publicación o cierre. Ensayo no acredita multiusuario hostil; intención abandonada no se roba por PID |
| T25 / P1 | Cuota total/límite de artefactos y cancelación por fases | Límites explícitos, sin truncar cierre ni limpiar evidencia referenciada; presupuesto de bytes no declarado como máximo RSS |
| T26 / P2 | Referencia RAW externa sintética conservada por el padre, y luego lectura no autorizada/archivo ausente | Revalidación física solo cuando permitida y disponible, evento nuevo sin alterar original; ausencia o falta de permiso no dispara HTTP ni cambia el asset_id |

T04 y los fallos entre pasos se deben poder combinar con terminación forzada de
un subproceso en puntos conocidos. Eso acredita recuperación ante **interrupción
de proceso simulada**, no corte eléctrico real, cachés del controlador, pérdida
del disco o ausencia de toda carrera. No apagar equipos para estas pruebas.
Las guardias Python son instrumentación cooperativa, no sandbox contra código
nativo/Python hostil. No instalar herramientas para ampliar esa afirmación.

## 5. Criterios de cierre del próximo incremento

Antes de declarar cerrado el MVP, comprobar conjuntamente:

1. Formatos, ampliación versionada y perfil sintético revisados; ninguna base
   preexistente/operativa migrada o adoptada implícitamente. Cotas y propietario
   de raíces/recursos explícitos; un escritor y filesystem local compatible.
2. Una evidencia completa, fallida, incompleta y cancelada recuperables en otro
   proceso con inventario físico cotejado. Si falta original histórico o codec
   suficiente para un cotejo 85-H, el alcance lo expresa, no simula el resultado.
3. Publicación sin sobrescritura, commit lógico veraz y matriz de fallos cubierta
   por los escenarios P1. Orfandad/conflicto/corrupción visibles sin pérdida
   automática ni repetición de efectos. Restricciones y valores exactos intactos.
4. Idempotencia de conservación demostrada, no promesa de exactamente una
   ejecución. Contextos distintos no se fusionan por SHA o coincidencia de datos.
5. Ningún booleano/estado/hash concede ciencia/autenticidad/permiso; control local
   se distingue de custodia independiente. No se implementan firmas o PKI.
6. Regresiones completas con .venv y pip check al cambiar código, además de
   verificaciones estáticas y de Git. Preservar las 1791 anteriores y registrar
   el total real; no contabilizar subtests/escenarios de este plan como nuevas.
7. Informe de límites: sin recuperación eléctrica garantizada, respaldo operativo,
   limpieza/retención automática, multiusuario, reanudación de descarga/QA o
   repositorio científico. No uso como única custodia de evidencia irremplazable.

Un criterio no demostrado queda pendiente; no se rebaja para declarar éxito.
Los ensayos P2 de restauración y fuente externa deberán aprobarse antes de
ofrecer esas capacidades. No hace falta implementar P3 para cerrar el MVP.

## 6. Verificación documental del 85-I y estado Git

Comprobaciones de este paso: lectura de código/pruebas/informes y del encargo,
contraste de referencias/estados/versiones, revisión del grafo de hashes y
comprobación estática de los tres Markdown. No se importan módulos de SPICA ni
se ejecutan motores, pruebas planificadas, suite completa o pip check. Las
**1791 aprobadas pertenecen al 85-H**; no son resultado de una corrida del 85-I.

Comandos de cierre ejecutados conforme al encargo:

```powershell
git diff --check
git status --short
```

También se cotejan diferencias de archivos registrados e índice y directamente
los archivos nuevos: git diff --check no incluye documentos sin seguimiento.
El control de enlaces comprueba destinos locales y anclas sin abrir URLs.

Los únicos archivos creados por el 85-I son:

```text
docs/arquitectura_persistencia_linaje_paso85i.md
docs/protocolo_recuperacion_ejecuciones_paso85i.md
docs/plan_implementacion_persistencia_paso85i.md
```

Resultados de las comprobaciones locales ejecutadas:

| Comprobación | Resultado del 85-I |
|---|---|
| Tres Markdown nuevos | UTF-8, salto final, sin espacios finales, conflictos de merge o bloques sin cerrar; tablas coherentes |
| Enlaces y referencias | Destinos locales existentes, dentro del checkout; sin abrir enlaces externos. Interfaces/versiones contrastadas por lectura del código |
| Coherencia entre documentos | Misma alternativa C, estados ortogonales, DAG sin autorreferencia, alcance de conservación y prioridades; propuestas separadas de garantías actuales |
| git diff --check | Código 0, sin salida; complementado con revisión directa de documentos nuevos sin seguimiento |
| git diff --exit-code HEAD | Código 0, sin salida: cero archivos registrados modificados |
| git diff --cached --exit-code | Código 0, sin salida: ningún cambio en el índice |
| Rama y HEAD | feature/suadc-http / a044b49, sin cambios |
| Suite, pip check y escenarios propuestos | No ejecutados; solo documentación. 1791 aprobadas es el antecedente 85-H |

Estado final de git status --short, código 0:

```text
?? docs/arquitectura_persistencia_linaje_paso85i.md
?? docs/plan_implementacion_persistencia_paso85i.md
?? docs/protocolo_recuperacion_ejecuciones_paso85i.md
```

El estado inicial era limpio; el final contiene únicamente esos tres documentos
nuevos, sin modificar código, pruebas o informes previos. La comprobación textual
se ejecuta con .venv y -B, biblioteca estándar, sin importar SPICA o abrir SQLite;
no genera archivos auxiliares en el proyecto. No se modificó .venv.

Cero conexiones, GET, descargas, instalaciones, migraciones, commits o push.
No se accedió a RAW/staging/SQLite operativos, CSV ni evidencias privadas PNDA;
por ausencia de acceso no hubo escrituras nuestras allí. No se inspeccionaron
físicamente esos recursos cerrados ni se afirma controlar cambios de terceros.
Las 29 brechas y todos los documentos anteriores siguen sin cambios en Git.

## 7. Riesgos residuales, decisiones y dictamen

Quedan pendientes de revisión: versión/DDL/API de ampliación de CatalogoCientifico,
formato/codec y alcance del cotejo 85-H importado, parámetros de espacio/tiempo,
coordinación local y ubicación de prueba. Las reglas de retención, custodia de
controles, respaldo operativo y resistencia a apagados no quedan aprobadas por
este diseño. No existe aún persistencia de ejecución ni recuperación ejecutable.

No se modifican contratos estables, las 22 reglas, JSON QA, las
[29 brechas PNDA](brechas_reconciliadas_pnda_paso84i.md), almacenamiento operativo,
observaciones o condiciones de uso. No se resuelven documentación institucional,
metrología, unidades, tiempo, identidad de estaciones, derechos o validación
científica guardando una traza. /query INGEMMET permanece NO AUTORIZADO.

**Dictamen de diseño: APTO CON RESTRICCIONES para revisión y preparación del
incremento experimental descrito.** La recomendación concreta para 85-J es
implementar P0/P1 como una sola frontera de conservación/lectura offline con
catálogo científico versionado y artefactos acotados en temporales aislados,
después de revisar las decisiones anteriores. No autoriza inicializar un almacén
operativo, migrar, adquirir recursos o pasar a producción. Se espera revisión;
no se comienza 85-J ni se realizan commits.
