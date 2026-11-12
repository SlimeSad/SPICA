# PASO 85-K — Respaldo y restauración experimental de evidencias

Elaboración: 2026-11-12, America/Lima. Rama `feature/suadc-http`, base
`d7d7b8c`; repositorio inicialmente limpio. Ámbito exclusivo: fixtures en TEMP.
Resultados ejecutados: [piloto](piloto_respaldo_restauracion_paso85k.md).
Límites: [brechas de custodia](brechas_custodia_paso85k.md).

## Auditoría y puerta de viabilidad

Se revisan la [arquitectura 85-I](arquitectura_persistencia_linaje_paso85i.md),
su [protocolo](protocolo_recuperacion_ejecuciones_paso85i.md) y
[plan](plan_implementacion_persistencia_paso85i.md), la
[implementación 85-J](implementacion_persistencia_paso85j.md), su
[piloto](piloto_recuperacion_paso85j.md) y
[brechas](brechas_persistencia_paso85j.md), herramientas y pruebas asociadas.
85-J está registrado en el commit de base. Sus 1841 aprobadas son un antecedente;
la ejecución de este incremento se informa separadamente en el piloto.

85-J ya recupera el trío informe tipado/traza/referencia, valida esquema SQL,
huellas físicas, identidades y cotejo 85-H. No respalda el conjunto ni puede
regenerar un artefacto desaparecido. `escritor.lock` coordina operaciones
cooperativas, pero SQLite y el sistema de archivos no forman una transacción.
Un manifiesto publicado sin confirmación SQL tampoco es una conservación completa.

Es viable capturar una **instancia temporal inactiva con una sola ejecución
conservada**, manteniendo ese marcador durante toda la captura. El esquema
85001, base v1 más cuatro tablas, se conserva exactamente. No hay migración ni
segundo catálogo lógico: el SQLite del respaldo es la imagen del mismo catálogo.
No se implementa respaldo general de SPICA, RAW operativo o almacenes multiejecución.

| Componente | Uso en 85-K |
|---|---|
| [Conservador y lector 85-J](../herramientas/conservacion_linaje_85j.py) | Validación previa/final; coordinación del escritor y recuperación restaurada |
| [Índice 85001](../herramientas/_catalogo_linaje_85j.py) | Validación exacta de DDL, versión, application_id, FK y quick_check; conexiones cerradas explícitamente |
| [Codec 85-J](../herramientas/_codec_linaje_85j.py) | JSON estricto y reconstrucción tipada, sin imports elegidos por el archivo |
| [Cotejo 85-H](../herramientas/traza_cierre_85h.py) | Contrasta la traza original con el informe y su control previo |
| [Adaptador nuevo](../herramientas/respaldo_linaje_85k.py) | Captura, copias independientes, inventario, control y restauración TEMP |
| [Pruebas nuevas](../tests/test_respaldo_linaje_85k.py) | Custodia, corrupción, interrupción, límites y procesos independientes |

No se modifica ningún componente anterior. Se usan interfaces privadas de las
herramientas experimentales para no ampliar contratos estables. La comprobación
cerrada del manifiesto 85-J en el respaldo reproduce su proyección declarativa;
su aceptación definitiva al restaurar depende del lector 85-J, no de un motor
alternativo de ejecución. Ese acoplamiento de formato exige pruebas de compatibilidad.

## Contratos y versiones

Formato de respaldo/control: **0.1.0**. Conservación y codec 85-J: **0.1.0**.
SQLite: **85001**, sin cambios. Traza, ejecución, QA y documentos conservan las
versiones históricas de sus cuerpos; no se les atribuye una revisión nueva.

`LimitesRespaldo85K` establece presupuestos explícitos. `ControlRespaldo85K`
contiene `respaldo_id`, `generacion_sha256` y `manifiesto_sha256` y debe entregarse
explícitamente al restaurador; este no lo toma del archivo que intenta verificar.
`Restauracion85K` entrega una identidad nueva para la operación y el resultado
real del lector 85-J. Ambos rechazan coerción booleana; no son autorizaciones.
`ErrorRespaldo85K` devuelve códigos cerrados sin mensajes originales de SO/SQLite.
Interrupciones BaseException se propagan después de cerrar recursos contextuales.

El gestor ofrece `respaldar`, `verificar_respaldo` y `restaurar`. Solo acepta
raíces `TEMP/spica-85j-*/conservacion` y `TEMP/spica-85k-*/respaldo` creadas por
los contextos del piloto. El propietario de esos contextos decide su eliminación
al terminar el ensayo, después de inspeccionar y registrar resultados. El gestor
no elimina parciales ni reintenta sobre un destino existente, aunque sea idéntico.

## Punto de captura y generación

1. Validar con el lector 85-J: CONSERVADA, sin residuos, huérfanos ni escritor.
2. Adquirir exclusivamente el marcador de escritor y volver a validar. Durante
   la captura solo se admite REVISION_NECESARIA causado exactamente por **nuestro**
   marcador; no se acepta una revisión genérica o heredada.
3. Exigir SQLite DELETE sin archivos `-wal`, `-shm` o `-journal`, una ejecución,
   cuatro referencias obligatorias, eventos acotados y las siete tablas base vacías.
   Rechazar archivos y directorios ajenos, incluso fuera del inventario 85-J.
4. Calcular la generación lógica de las filas completas de las cuatro tablas de
   linaje, ordenadas por sus claves, esquema y versión de formato. No es el SHA de
   los bytes de SQLite, una fecha ni una propiedad del directorio físico.
5. Crear un destino exclusivo; registrar intención. Usar **Connection.backup**
   para la imagen SQLite, con comprobación de plazo/tamaño en el avance. Copiar
   marcador y cuatro cuerpos a archivos nuevos por bloques, flush/fsync, relectura.
6. Contrastar generación del snapshot y del origen con la inicial, volver a pasar
   el lector bajo nuestro marcador y cotejar los cuerpos con 85-H.
7. Publicar el manifiesto final únicamente después de completar el inventario.
   Liberar el marcador propio y verificar el respaldo completo antes de devolver
   su control al llamador. No se registra una adquisición ni se vuelve a ejecutar QA.

Escritores no cooperativos quedan fuera de la garantía. El marcador no impide a
un proceso hostil modificar archivos; la comparación final detecta cambios
ordinarios, no una sustitución coordinada seguida de restitución.

## Formato físico y publicación

```text
respaldo/
  intencion.json
  catalogo.sqlite3
  piloto.json
  contenido/<dos hex>/<sha256>  # cuatro artefactos originales de 85-J
  trabajo/                    # vacío solo si la operación terminó sin residuos
  respaldo.json               # sello final, publicado el último
```

El inventario final tiene siete entradas: intención, SQLite, marcador y cuatro
artefactos. Cada una registra rol, ruta relativa fija/derivada, tamaño y SHA-256
físico. Se rechazan roles repetidos, rutas distintas de las calculadas, extras,
versiones desconocidas y contradicciones con SQL, cuerpos o control.
Se incluyen identidades, estados históricos y de conservación, diagnósticos y
restricciones originales, condiciones de restauración y limitaciones de confianza
cerradas por la versión. Omitir o contradecir estas condiciones impide aceptar el
respaldo aunque se recalcule su hash. Los indicadores ciencia/autorización/autenticidad son False.

La intención dice PREPARADA; el manifiesto final dice PUBLICADA. Su coexistencia
es un protocolo, no dos estados finales contradictorios. Un respaldo sin sello o
con residuos no es utilizable. Fallos posteriores a publicar pueden dejar un
respaldo físicamente íntegro sin que el llamador reciba éxito/control: se informa
error o interrupción; requiere inspección, nunca repetición automática.

Grafo sin ciclos: cuerpos/snapshot/intención → inventario en manifiesto → SHA del
manifiesto en el control del llamador. El manifiesto no incluye su propio hash.
La generación lógica agrupa filas y referencias, y se coteja con todos los cuerpos.
No equivale a autenticidad institucional. Reescribir coherentemente respaldo y
control bajo los mismos permisos no queda detectado por una custodia independiente.

Se escribe primero una **copia física nueva** en `trabajo`, se verifica y se
publica mediante enlace exclusivo dentro del destino. El temporal propio se
desvincula y el publicado se relee con nlink=1. Nunca se enlazan bytes del almacén
de origen ni del respaldo al restaurado. No se usa replace ni sobrescritura.
El volumen debe admitir enlaces exclusivos; el fallo queda como parcial revisable.
Los directorios pueden verse antes del sello. No hay publicación atómica de todo
el árbol, transacción global ni garantía portable de fsync de directorio en Windows.

## Restauración y conservación de significado

Primero se verifica el respaldo contra el control explícito, inventario físico,
esquema, generación, trío y restricciones. Solo después se reserva una **raíz nueva
diferente**. No se llama al creador 85-J, porque produciría otra identidad.
Se crea una intención en `temporales` y un marcador propio de escritor. Se copian
independientemente el snapshot cerrado, marcador y cuatro cuerpos, conservando
los hashes exactos. Se validan generación y metadatos y se utiliza el lector 85-J
con cotejo 85-H. Solo se admite la revisión atribuida al lock e intención propios.

Tras validar todo, se elimina únicamente nuestra intención comprobada y se
libera nuestro lock. El lector 85-J debe devolver VERIFICADA_EN_ALCANCE sin
residuos; de lo contrario se propaga un error. Una interrupción anterior conserva
la intención y los archivos, y el lector no presenta la restauración como cerrada.
Tras un apagado abrupto puede quedar también el marcador: no se borra para reparar.

Se preservan instancia, ejecución, conservación, proyecto, entrada, evaluación y
activo históricos, nativos parciales, errores, estados, versiones, restricciones
y controles anteriores. CANCELADA/FALLIDA/INCOMPLETA como historia no se convierten
en éxito científico por haberse conservado/restaurado correctamente. La nueva
identidad identifica solo la operación de restauración. No se bifurca una
instancia para admitir simultáneamente dos escritores.

Las rutas históricas siguen siendo metadatos inertes del informe privado. No
localizan archivos actuales ni abren originales. El RAW sintético del arnés 85-G
ya fue eliminado por su contrato; restaurar su evidencia **no restaura ese RAW**.
La lectura 85-J recupera una evidencia; el respaldo la copia a otro conjunto;
la restauración vuelve a materializarla. Ninguno reconstruye contenido ausente.

## Límites y privacidad

Valores por defecto: archivo 8 MiB, SQLite 16 MiB, conjunto 48 MiB, manifiesto
64 KiB, siete entradas y árbol máximo 32 elementos, 128 eventos, bloque 64 KiB,
margen libre 1 MiB y plazo cooperativo 180 s. Límites máximos y tipos son cerrados.
El espacio previo es una estimación conservadora, nunca reserva. No hay prueba
de ACL ni alteración de permisos: crear/escribir/fsync prueba la capacidad efectiva.
Fallos de disco/permisos y escrituras cortas impiden declarar cierre.
La intención persistida y los parciales permiten inspección; el código del fallo
se devuelve al llamador para su registro. No hay bitácora durable garantizada de
errores si la escritura de diagnósticos o el proceso también falla.

I/O físico por bloques; el cotejo lógico reutilizado materializa artefactos
acotados (hasta cuatro de 8 MiB y presupuestos propios de 85-J), no CSV científicos
grandes. El codec limita profundidad/nodos. No se promete un límite duro de RAM
del intérprete. El plazo y cancelación se comprueban en fronteras y bloques,
incluido avance SQLite; no interrumpen una llamada de SO bloqueada. La verificación
final es una fase separada con su propio plazo.

Se rechazan `..`, UNC, destinos fuera del TEMP admitido, componentes protegidos,
symlinks/junctions, archivos no regulares y hardlinks ajenos. Las rutas del JSON
no se siguen libremente. Se comparan stat del nombre/descriptor antes y después.
Subsisten TOCTOU, permisos compartidos, aliases no detectados y Python/SO hostil.
Las salidas técnicas no imprimen rutas privadas ni cuerpos; las evidencias privadas
sí contienen los metadatos históricos necesarios. No hay saneamiento universal
de secretos ni nueva custodia, firma o cifrado.
