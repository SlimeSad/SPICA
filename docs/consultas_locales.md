# PASO 70: consultas civiles locales y diagnóstico HORA/UBIGEO

## Contrato y alcance

`spica.adquisicion.consultas_locales` añade selección progresiva sobre `LectorCSV`.
No crea otro parser, cambia el núcleo, descarga recursos ni ejecuta planificación.
El perfil inicial admite exclusivamente el encabezado exacto de 16 campos del CSV
SENAMHI GBON/RBON documentado en [csv_streaming.md](csv_streaming.md). Un esquema
ajeno, incompleto, reordenado o con columnas adicionales no se interpreta.

`ConsultaLocal` requiere uno o más nombres literales de ESTACION, variables
explícitas TEMP/HR/PP y dos objetos `date` inclusivos. Rechaza `datetime`, cadenas,
intervalos invertidos, selecciones vacías y repetidas. No recorta nombres ni cambia
mayúsculas. No hay filtros adicionales, búsquedas aproximadas ni códigos de estación
inferidos. Máximo 128 nombres de 256 caracteres y tres variables; conserva su orden.

FECHA se interpreta únicamente como fecha civil aaaammdd válida en el calendario.
No identifica un instante ni se convierte a UTC. `SolicitudAdquisicion` y los tramos
del planificador necesitan instantes con zona: no se debilitan esos contratos para
representar este producto cuya zona sigue sin documentarse. HORA permanece textual.

```python
from datetime import date
from spica.adquisicion.consultas_locales import (
    ConsultaLocal, ConsultorLocalCSV, LimitesConsulta, ProcedenciaLocal,
)
from spica.adquisicion.nucleo import Fuente

consulta = ConsultaLocal(("IMATA",), ("TEMP",), date(2015, 1, 1), date(2015, 1, 3))
# Proporcionar los identificadores reales del recurso/activo consultado.
procedencia = ProcedenciaLocal(Fuente("SENAMHI", "SENAMHI"), recurso_id, asset_id)
with ConsultorLocalCSV(ruta_csv, consulta, procedencia,
                       limites=LimitesConsulta(max_resultados=256)) as operacion:
    for observacion in operacion:
        consumir(observacion)  # No acumular todas las observaciones.
informe = operacion.informe  # Evaluar después del cierre.
```

Cada resultado es una fila real por variable solicitada, en orden del archivo y
de las variables. Incluye `ProcedenciaLocal` (Fuente, recurso_id, asset_id y hash
declarado opcional), número lógico y líneas físicas, los 16 campos originales,
variable, texto, indicador `presente` y fecha civil. Los textos son los valores
entregados por el parser CSV: conserva espacios, ceros y saltos interiores; no son
una copia de las comillas de serialización. IDs repetidos no eliminan filas.

`presente` significa exclusivamente texto distinto de `""`. Un espacio, `NaN`,
un centinela o un número no vacío no se declaran mediciones válidas. No se asignan
unidades, convierten números, reconstruyen horas ni normalizan códigos.
ID identifica el registro según el diccionario, ESTACION es nombre literal y
UBIGEO es información territorial declarada. Ninguno crea identidad física estable.

## Límites, cierre y reproducibilidad

Se conservan los límites de `PoliticaLecturaCSV`: 128 MiB por archivo, bloques de
64 KiB, dos millones de registros incluidos encabezado, campo de 65.536 caracteres,
línea de 262.144 y registro de 1.048.576; muestra inicial de 64 KiB. Son configurables
con sus topes previos. El nuevo máximo de resultados es 10.000 (tope dos millones).
Tres variables de una fila consumen tres resultados y el límite puede cortar esa
fila entre variables. Incluso si coincide con el último resultado no se presume EOF.

Solo conserva fila actual, encabezado, filtros acotados, diagnósticos del lector y
caché de hasta 4.096 claves de fecha de ocho caracteres. La memoria no crece con
el número de observaciones. Los presupuestos no son cuotas exactas de memoria del SO;
el consumidor puede excederlos si acumula los resultados. Una prueba compara 1.000
y 15.000 filas consumidas secuencialmente y exige pico Python inferior a 4 MiB para
esa fixture, sin prometer ese pico para cualquier configuración o consumidor.

Usar siempre `with`. `cancelar()` o un `threading.Event` externo detienen la operación
cooperativamente, también entre variables pendientes. `break`, excepciones del
consumidor, límites, errores, cambios detectados o fechas civiles inválidas conservan
alcance incompleto. KeyboardInterrupt se propaga tras cerrar. `completa` requiere
agotamiento del iterador, EOF, estado CSV COMPATIBLE, encabezado exacto, cero fechas
inválidas y cierre con identidad estable. La política es conservadora: una fecha
inválida incluso de otra estación impide afirmar búsqueda completa.

`ausencia_comprobada` solo permite afirmar cero coincidencias en esta versión local
después de una búsqueda completa; no ausencia institucional. Los resultados entregados
antes del informe final son provisionales. Sin EOF no hay totales del archivo.
Se comunica conteo de resultados y filas coincidentes, sin confundirlos.

La misma versión del archivo y filtros produce iguales valores, orden y posiciones;
la fecha técnica del informe del lector cambia. `sha256_declarado` no verifica el
archivo ni prueba autenticidad. La comprobación inode/tamaño/mtime del lector ayuda
a detectar cambios, pero no crea snapshot ni protege contra escritores hostiles que
restauren metadatos. Para evidencia física se necesita hash externo antes y después,
directorios controlados y ausencia de escritores. No se cambia el estado del activo RAW.

## Diagnóstico documental acotado

`diagnosticar_csv` reutiliza el mismo lector y perfil. Cuenta HORA por longitud,
literal y patrón: seis dígitos con rangos hhmmss compatibles, seis fuera de rango,
cinco dígitos, vacío u otro texto. Es comparación léxica, sin asignar una hora real.
UBIGEO distingue seis dígitos, dígitos con sufijo `.0`, vacío u otro literal. No se
elimina el sufijo ni rellena nada. Cuenta relaciones literales de ESTACION, UBIGEO,
longitud, latitud, altitud, departamento, provincia, distrito y red. No valida INEI.

Un índice SQLite **temporal desechable**, fuera del directorio del CSV, cuenta igualdad
exacta `(ESTACION, FECHA, HORA)`, incluso con filas desordenadas. No usa ID ni almacena
valores meteorológicos; no abre el catálogo operativo. Distingue claves repetidas de
repeticiones adicionales. Cinco y seis caracteres no se fusionan. Una repetición
literal no acredita duplicación de instantes; ausencia de repetición tampoco demuestra
continuidad ni ausencia de colisiones después de una hipotética normalización.

Presupuestos predeterminados: 500.000 claves, índice 64 MiB, caché SQLite de 1 MiB,
256 horas distintas, 2.048 relaciones, literales agregados de hasta 512 caracteres y
20 ejemplos de duplicados/vacíos. Hay topes de configuración. Las longitudes/patrones
tienen cardinalidad acotada por esos presupuestos. Ejemplos truncados no truncan conteos;
exceso de claves, horas, relaciones, longitud, bytes o espacio sí detiene y declara
incompleto con código explícito. La fila que disparó el límite puede haber sido leída
pero no incorporada a los agregados. Al detenerse por límites, los conteos describen
solo el prefijo procesado.
Si se omiten filas de anchura incorrecta, los conteos corresponden únicamente a
las filas efectivamente procesadas y el resultado sigue siendo incompleto.

El temporal usa nombre aleatorio exclusivo, comprueba padre sin symlinks/junctions y
espacio libre de índice más 2 MiB de margen; no es una reserva. `max_page_count` acota
el índice; `journal_mode=OFF` evita otro archivo del tamaño del índice. No hay garantía
de durabilidad: cualquier error descarta ese índice, que nunca se recupera ni reutiliza.
Solo se eliminan el archivo propio y su carpeta vacía, sin borrado recursivo. Un fallo
de limpieza se informa e impide declarar completo; no se borran objetos preexistentes.
También se intenta limpiar ante KeyboardInterrupt/SystemExit. Una terminación forzosa
del proceso puede dejar residuos temporales, sin recuperación automática.

En POSIX se solicita directorio 0700; Windows hereda las ACL del padre sin modificarlas.
Se requiere directorio temporal controlado y privado según el entorno: el módulo no
certifica ACL Windows ni ofrece aislamiento frente a otros procesos del mismo usuario.
Las excepciones de E/S/SQLite se convierten en códigos sin rutas o mensajes backend.
Los resultados sí contienen los literales solicitados; el llamador controla su difusión.

## Verificación operativa

Los resultados de la consulta real, diagnóstico y comprobaciones de conservación se
registran a continuación tras aprobar las pruebas sintéticas. No se exportan CSV,
escriben informes en RAW/staging, modifican catálogos ni realizan conexiones externas.

### Consulta IMATA/TEMP

Comprobación del 2026-10-29. Activo `71df55229ee947fb8e7fed8b1403289e`, recurso
identificado por la URL pública ya persistida en su declaración RAW (no consultada
por HTTP). El intervalo **civil inclusivo 2015-01-01 a 2015-01-03** devuelve **72
filas y 72 resultados TEMP**. Búsqueda completa hasta EOF, cero fechas inválidas,
cero errores de estructura y límites no alcanzados (máximo de resultados 256).
Fin de consulta: 23:06:55 UTC. Se recorrieron los 416.274 registros, incluido el
encabezado; una selección pequeña requiere escanear todo el archivo sin índice
de consultas persistente ni presunción de orden. No acredita continuidad horaria.

Muestra acotada de valores originales; las comillas indican texto, no conversiones:

| Registro lógico | ID | ESTACION | FECHA | HORA | TEMP | UBIGEO |
| ---: | --- | --- | --- | --- | --- | --- |
| 166511 | `166510` | `IMATA` | `20150101` | `00000` | `-0.6` | `40514.0` |
| 166512 | `166511` | `IMATA` | `20150101` | `10000` | `-1.3` | `40514.0` |
| 166513 | `166512` | `IMATA` | `20150101` | `20000` | `-1.4` | `40514.0` |

Cada resultado conservó también los demás campos: longitud `-71.0906`, latitud
`-15.8427`, altitud `4475.0`, RED `RBON`, DEPARTAMENTO `AREQUIPA`, PROVINCIA `CAYLLOMA`,
DISTRITO `SAN_ANTONIO_DE_CHUCA` y FECHA_CORTE `20240630`, además de HR/PP originales
de cada fila. No se asignaron unidades ni zonas por el código de consulta.

### Diagnóstico completo

Terminó a las 23:08:19 UTC, recorriendo **416.273 filas de datos hasta EOF**, con cero
fechas inválidas, sin exceder presupuestos y con el índice temporal eliminado.
Cobertura civil observada del archivo: **2015-01-01 a 2024-06-30**; es distinta
del intervalo seleccionado para IMATA y no demuestra continuidad.

HORA: **170.400** valores de cinco caracteres y **245.873** de seis. Los primeros
son exactamente `00000`, `10000`, `20000`, `30000`, `40000`, `50000`, `60000`,
`70000`, `80000`, `90000`, cada uno con 17.040 apariciones. Los otros cumplen la
forma y rangos léxicos hhmmss. Hay 34 literales en total. Se registran **416.273
claves exactas distintas y cero claves repetidas/repeticiones adicionales** por
ESTACION, FECHA y HORA. No se fusionan literales de cinco y seis caracteres; por
ello no se descartan colisiones bajo interpretaciones que aquí no se realizan.

Evidencia: el diccionario anterior declara HORA hhmmss, y esos 170.400 textos
carecen de la anchura declarada. **Hipótesis pendiente:** pérdida de ceros iniciales
durante una serialización numérica. Es compatible con la forma de los literales,
pero el archivo no demuestra esa causa ni autoriza una reconstrucción. No se
rellenan ceros, asigna zona horaria ni afirma periodicidad u horas ausentes.

Los **416.273 UBIGEO** observados cumplen el patrón léxico dígitos seguidos de `.0`.
Las relaciones entre nombre y ubicación declarada son las cinco ya inventariadas;
se conservan sin correcciones. La tabla explicita formato y asociación literal:

| ESTACION | UBIGEO original | Longitud del texto | Filas |
| --- | --- | ---: | ---: |
| CANDARAVE | `230201.0` | 8 | 83.256 |
| CARANIA | `151007.0` | 8 | 83.253 |
| IMATA | `40514.0` | 7 | 83.253 |
| MATUCANA | `150701.0` | 8 | 83.255 |
| SAN_JOSE_DE_UZUNA | `40114.0` | 7 | 83.256 |

Evidencia: sufijo decimal literal y discordancia con el formato de seis caracteres
del diccionario. **Hipótesis pendiente:** representación numérica previa, posiblemente
con pérdida de ceros. No se retira `.0`, rellena códigos, consulta INEI ni afirma
que estos textos equivalgan a códigos administrativos oficiales. Una relación única
observada por nombre no acredita identidad física inmutable de estación.

### Caso vacío comprobado y conservación

No aparecieron TEMP vacías en las 72 coincidencias de IMATA seleccionadas. El
diagnóstico identificó una fila vacía en CANDARAVE, y una segunda consulta completa
de TEMP para **2015-01-04** devolvió 24 resultados, con un vacío: registro lógico
**95**, ID `94`, FECHA `20150104`, HORA `210000`, TEMP `""`, `presente=False`,
UBIGEO `230201.0`. En esa misma fila HR y PP también son textos vacíos. El resultado
conserva sus 16 campos y la misma procedencia/activo. No se imputa ni elimina nada.

Operación de lectura: **2026-10-29 23:05:45 a 23:09:44 UTC** (hora técnica del proceso,
sin relación con la zona de las observaciones). Original utilizado:

```text
C:\Users\Propietario\SPICA_DATOS\raw\sha256\3d\3d3e8a0a75e070d0b8111faf921be17140c3a0f9db2b4c25d72d99a15a950eab
```

Antes y después: **50.474.012 bytes**, SHA-256 físico calculado por bloques:

```text
3d3e8a0a75e070d0b8111faf921be17140c3a0f9db2b4c25d72d99a15a950eab
```

El inventario previo/posterior coincide en rutas de archivos/directorios, tamaños,
hashes, inode, mtime y enlaces. No se compara atime, que el sistema puede actualizar
al leer. Se comprueban CSV, original sintético, marcador, catálogo y único archivo
de staging. El sintético conserva 57 bytes y SHA-256
`82c649098a927a255181c8b05d18aec30594fa89571bad2792464f3ba255f4cb`.
RAW/temporales permanece vacío y staging conserva únicamente `paso64-sintetico.bin`.

SQLite operativo se abrió únicamente con `mode=ro&immutable=1`, `query_only=ON`,
`trusted_schema=OFF`, tras descartar WAL/SHM/journal y marcador de inicialización.
Se reconoció el esquema real y su integridad técnica con las comprobaciones existentes.
Sigue en v2, **dos activos incorporados y diez eventos**. Catálogo de 32.768 bytes,
SHA-256 antes/después `946d2512795c5ae3a68113f63438110be66dee32488ad02e86d550da040d4a0d`.
No se llamó a APIs RAW que registran verificaciones o eventos. No se modificaron
RAW, staging o SQLite operativo ni se exportaron copias del original.

La comprobación de procesos no encontró otros Python/pythonw/sqlite3 conocidos,
pero no equivale a un bloqueo ni excluye escritores desconocidos. Se mantiene el
modelo secuencial. La comparación final física es evidencia de conservación durante
esta ejecución, no certificación científica ni garantía contra toda concurrencia.

### Dictamen y pendientes

**APTO CON RESTRICCIONES** para selección local literal y civil de este perfil.
Permanecen pendientes confirmación documental de HORA y UBIGEO, zona horaria,
identidad estable de estaciones, semántica de centinelas y calidad/completitud de
observaciones. La recuperación de ceros, normalización, análisis meteorológico,
indexación persistente y soporte de otros esquemas requieren trabajo posterior.
No se avanzó a ninguna de esas capacidades ni se cambió el estado científico del RAW.

`git diff --check` termina con código 0. Los archivos son nuevos y aún no rastreados;
también se comprobaron sus espacios finales mediante lectura directa, sin problemas.
Estado final comprobado, sin commits ni cambios en archivos previamente rastreados:

```text
?? docs/consultas_locales.md
?? src/spica/adquisicion/consultas_locales/
?? tests/test_consultas_locales.py
```

## Verificación automatizada

Python 3.15.1, HTTPX 0.28.1 y SQLite 3.53.4, utilizando exclusivamente `.venv`.
Las **51 pruebas nuevas** usan fixtures sintéticas fuera del RAW permanente. Cubren
filtros exactos y asociaciones reales, fechas inclusivas/inválidas/bisiestas,
vacíos y espacios, identificadores repetidos, literales de hora/UBIGEO, preservación,
límites, EOF, cancelación, interrupción, archivo grande y consumo de memoria.
El diagnóstico añade duplicados desordenados, presupuestos de cardinalidad y disco,
falta de espacio, errores SQLite sin mensajes sensibles, limpieza y protección ante
colisión con un temporal preexistente. Se conserva incertidumbre de codificación.

Antes de leer el original operativo se ejecutó:

```text
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
Ran 678 tests in 53.814s
OK

.\.venv\Scripts\python.exe -B -m pip check
No broken requirements found.
```

Resultado: **678 aprobadas (627 anteriores y 51 nuevas), cero fallos y cero errores**.
No se añaden dependencias. Git inicial limpio en `feature/suadc-http`, commit
`32db6c2`; los cambios del PASO 70 son exclusivamente archivos nuevos del paquete,
sus pruebas y este documento. No se modifica `LectorCSV`, contratos anteriores,
conector, configuración, `main.py`, `.gitignore` ni `.venv`.
