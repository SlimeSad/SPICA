# PASO 67: política temporal y corrección SUADC-04

## Defecto reproducido antes de corregir

En Python 3.15.1, dos `datetime` con el mismo objeto `tzinfo` se comparan por
sus componentes civiles, ignorando `fold`. En una hora repetida, `01:30 fold=0`
y `01:30 fold=1` pueden resultar iguales y su resta directa dar cero, aunque
sus instantes UTC estén separados por una hora. Entre zonas diferentes también
hay reglas especiales de igualdad durante una repetición; la igualdad directa
de objetos no es el criterio de identidad de instante del SUADC.

Se reprodujo con `zoneinfo.ZoneInfo` real leyendo un TZif sintético en memoria:
transiciones explícitas en 2020-03-29 01:00 UTC (0 a +01:00) y
2020-10-25 01:00 UTC (+01:00 a 0). Estos desplazamientos pertenecen exclusivamente
a la fixture; no se asignan a SENAMHI ni a otro registro real.

Las primeras 11 pruebas, ejecutadas sobre la implementación anterior, produjeron
`FAILED (failures=8, errors=3)`, contando los dos subtests de hora inexistente.
Mostraron solicitudes, filtros y disponibilidades válidos rechazados, intervalos
realmente invertidos aceptados, intersecciones falsas y un hueco real perdido.
La suite previa de 543 pruebas había aprobado antes de añadir estas regresiones.

## Semántica por tipo de fecha

| Uso | Regla |
| --- | --- |
| Solicitud, filtro temporal y `TramoTemporal` | Instantes absolutos con desplazamiento conocido; orden en UTC. Se acepta un intervalo puntual. |
| Extremos aware de disponibilidad | Instantes declarados: se validan existencia local y orden en UTC, incluso si comparten `tzinfo`. |
| Extremos naive de disponibilidad | Hora/fecha civil documental, orden civil entre ambos extremos. No demuestran cobertura absoluta; su evaluación sigue `DESCONOCIDA`. |
| Precisión, zona y frecuencia textuales | Metadatos originales; no localizan fechas, convierten frecuencias ni completan extremos ausentes. |
| Procedencia, revisión y comprobación del catálogo | Instantes validados y normalizados a UTC como antes. Su orden directo ya es inequívoco. |
| Metadatos RAW, HTTP y verificación estructural | Sin cambios: marcas técnicas generadas en UTC o persistidas con desplazamiento, sin intersecciones de cobertura. |

No se mezclan extremos aware y naive. Que una fecha sea naive significa que aquí
no se dispone de un instante absoluto, no que deba interpretarse como UTC. Una
fecha civil con precisión de día tampoco representa automáticamente todo un día
en una zona concreta. No se asigna `America/Lima`, aunque el registro sea peruano.

`nucleo.temporal.instante_utc()` devuelve una clave UTC para comparar, ordenar,
seleccionar mínimos/máximos y comprobar igualdad de instantes. No reemplaza el
datetime original. `validar_intervalo()` aplica ese criterio a los contratos y
solo admite orden civil cuando se solicita explícitamente para metadatos.

## Horas repetidas e inexistentes

- Con zona conocida, se respetan el desplazamiento y el `fold` del datetime
  entregado: `fold=0` y `fold=1` seleccionan las dos apariciones cuando existen.
- Python no registra si `fold=0` fue indicado expresamente o quedó por defecto.
  El contrato recibe un datetime ya localizado; el llamador debe justificar esa
  elección mediante la procedencia. No hay localización automática de texto civil.
- Se comprueba la ida y vuelta local → UTC → zona original comparando componentes
  civiles y desplazamiento, sin igualdad aware. Si no coinciden se rechaza la hora
  inexistente/incoherente, para ambos folds. No se desplaza a la siguiente hora.
- Un `fold=1` redundante fuera de una repetición no crea otro instante cuando el
  desplazamiento es el mismo. Se conserva el valor original al persistir.
- Un desplazamiento fijo explícito identifica un instante, pero no permite
  comprobar reglas de verano de una zona geográfica no suministrada.
- Se rechazan instantes cuya conversión UTC desborde el rango de `datetime`.
  No se introducen marcas de tiempo de punto flotante en las comparaciones.

## Catálogo y planificación

La búsqueda, intersección y clasificación de parcialidad comparan claves UTC.
Los extremos aplicables conservan los objetos originales elegidos de solicitud
o cobertura. En caso de igualdad de instante, la intersección prefiere el extremo
de la solicitud, manteniendo su representación. Los extremos son inclusivos.

Cada intervalo explícito sigue generando su propia propuesta y evidencia. La
unión se usa únicamente para calcular el complemento por asociación registrada,
sin mezclar estaciones ni variables. Se recorta al período solicitado, ordena en
UTC y respeta los indicadores de inclusión. Un punto excluido por ambos tramos
adyacentes sigue siendo un hueco; no se suman segundos ni días para representarlo.
Los intervalos discontinuos y sus operaciones permanecen separados.

Un hueco sigue siendo desconocimiento. No se produce `AUSENCIA_DOCUMENTADA` ni
se infiere disponibilidad científica por haber corregido las comparaciones.
Las frecuencias se comparan exactamente, sin agregación o conversión. Los códigos
originales multivariables y multiestación no se normalizan. Para la misma solicitud,
reglas de zona e instantánea, el plan sigue siendo determinista y declarativo.

## Persistencia temporal sin migración

El JSON anterior `{"__fecha__": "...ISO..."}` sigue siendo legible. ISO conserva
un desplazamiento conocido, pero no permite recuperar una clave de zona o un fold
que nunca se guardaron; no se inventan retrospectivamente.

Las nuevas fechas `ZoneInfo` añaden `__zona__`, `__fold__` y `__nombre_zona__`,
conservando también el ISO original y su desplazamiento. Para un desplazamiento
fijo se conserva el nombre si es distinto del generado por ISO, y el fold si es 1.
Las fechas UTC usuales siguen usando exactamente la representación anterior.
No cambia el DDL, `application_id`, `user_version` ni el historial previo.

Al escribir y leer una zona nombrada se exige que esté disponible localmente y que sus reglas
reconstruyan el desplazamiento, nombre y hora existentes. Si falta o contradice
esos metadatos, se lanza `ErrorCatalogo` con diagnóstico genérico. Los datos
persistidos permanecen intactos: no se migra, adivina ni sustituye por UTC.
No se consulta internet para resolver zonas. Un `ZoneInfo` sin clave o una clase
`tzinfo` personalizada no persistible se rechaza, evitando perder información.
También se rechaza antes de escribir un `ZoneInfo.from_file` cuya clave no permita
reconstruir los metadatos: no se introduce a sabiendas una fila ilegible.

Compatibilidad: este lector admite las filas anteriores; versiones anteriores del
código no entienden los nuevos sobres con zona/fold. No se autoriza retroceder de
versión sobre un catálogo que ya los contenga. Antes de usar zonas nombradas con
datos reales debe aprobarse cómo proporcionar y versionar sus reglas localmente.
El entorno auditado no tiene una base IANA disponible. Las pruebas preparan su
propia base TZif sintética en un directorio temporal y restauran `TZPATH`/caché.

## Inspección del resto de comparaciones

Se revisaron núcleo, catálogo, planificador, evidencias, RAW, transporte y formatos.
Las comparaciones de revisión en `catalogo.persistencia` y `catalogo.documental`
se mantienen: ambos operandos ya están normalizados a UTC y ahora también se valida
la existencia de la fecha original. `Retry-After` interpreta fechas HTTP de zona
fija y usa un reloj UTC por defecto: no tiene la combinación de zona con transición
compartida que causa SUADC-04. Su semántica de espera no se cambió. Los contadores
de bytes, posiciones ZIP, estados y textos de frecuencia no son instantes.

## Verificación y límites pendientes

Las 42 regresiones de `tests/test_temporal.py` cubren el comportamiento real de
Python, ambos folds, zonas diferentes, horas inexistentes, naive/aware, extremos
puntuales, orden inválido, intersecciones, uniones, huecos, metadatos y reapertura
SQLite, determinismo y ausencia de modificaciones al planificar. Se usan memoria
y directorios temporales aislados, sin acceder a RAW/staging operativos.

La validación es cronológica y de coherencia de metadatos. No demuestra que una
fuente haya documentado correctamente su zona, fold, frecuencia o cobertura. No
se captura una versión completa de tzdb ni todas sus reglas en SQLite; cambios de
reglas ajenos a los extremos guardados no son detectables. Falta aprobar esa
gestión, la localización asistida de horas civiles ambiguas y un modelo específico
de fechas civiles si los productos lo necesitan. Los `==` de dataclasses conservan
su comportamiento de Python y no deben usarse como comparador de instantes.
No se añadieron descarga, procesamiento científico, dependencias ni migraciones.
