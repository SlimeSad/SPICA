# PASO 69: lectura CSV secuencial e inventario preliminar

## Alcance y arquitectura

`spica.adquisicion.verificacion.LectorCSV` es una API aditiva, independiente de
HTTP, conectores, RAW y SQLite. Abre un archivo regular exclusivamente con `rb`.
No crea temporales, modifica catálogos, transforma valores ni evalúa fórmulas.
El inspector `verificar_archivo()` conserva sus límites de muestreo y su contrato;
no se eleva su muestra para cargar un archivo completo en memoria.

Se comparten con el muestreo las codificaciones y delimitadores admitidos, la
selección provisional de dialecto y la transición de estados de comillas de
`_csv.py`. Se conserva el rechazo de HTML/JSON reconocibles. La lectura completa
usa decoder incremental estricto, separación acotada de líneas físicas, control
de comillas/campos/longitudes antes de entregar cada línea a `csv.reader(strict=True)`
y una fila lógica por iteración. No modifica `csv.field_size_limit`, global al
proceso: si otro componente lo reduce, informa una inspección incompleta.

```python
from pathlib import Path
from spica.adquisicion.verificacion import LectorCSV, PoliticaLecturaCSV

with LectorCSV(Path("archivo-local.csv"), politica=PoliticaLecturaCSV()) as lector:
    for registro in lector:
        # Consumir sin acumular todas las filas. Los valores siguen siendo str.
        numero = registro.numero
informe = lector.informe  # Consultar después del cierre y comprobación de identidad.
```

`RegistroCSV` conserva número lógico (base 1), líneas físicas inicial/final,
valores y coherencia de anchura. Los separadores CR/LF/CRLF y los saltos dentro de
campos entrecomillados se preservan. No se recortan espacios, convierten números,
fechas, unidades ni zonas horarias. `encabezado_declarado` no se infiere y nunca
descarta la primera fila. El consumidor decide si puede interpretarla como encabezado.

`InformeLecturaCSV` devuelve estado reutilizando `EstadoEstructura`, motivo de fin,
EOF, recorrido completo, bytes de muestra/recorrido, líneas físicas, registros
completos/correctos/problemáticos, registro interrumpido, primera fila, anchura,
codificación, BOM, dialecto, diagnósticos y límites. La primera fila y los valores
devueltos pertenecen al llamador; el módulo no los imprime ni persiste automáticamente.

## Límites y memoria

| Presupuesto predeterminado | Límite |
| --- | ---: |
| Archivo | 134.217.728 bytes |
| Bloque binario | 65.536 bytes |
| Muestra de selección inicial | 65.536 bytes |
| Línea física, incluidos terminadores | 262.144 caracteres |
| Registro lógico, incluida sintaxis CSV | 1.048.576 caracteres |
| Campo decodificado | 65.536 caracteres |
| Campos por registro | 1.024 |
| Registros completos | 2.000.000 |
| Diagnósticos detallados | 20 |

Hay topes de configuración para muestra (256 KiB), bloque/línea (1 MiB), registro
(8 Mi caracteres), campo (65.536), campos (4.096) y diagnósticos (1.000). No se
admiten booleanos como cantidades. Los límites son presupuestos técnicos, no
valores del diccionario científico ni una garantía de memoria residente exacta.

La memoria depende de muestra, bloque, línea, primera fila y fila actual, más los
diagnósticos acotados; no del número total de registros. No hay `read()` ilimitado,
listas globales de filas ni DataFrames. El consumidor debe imponer sus propios
límites a agregados y cardinalidades. No hay cuotas de SO ni aislamiento de CPU.

## Codificación y dialecto

Un BOM coherente o una codificación explícita justifican el decoder seleccionado.
No se eligen CP1252/Latin-1 para hacer desaparecer errores. En ausencia de evidencia,
UTF-8 se usa únicamente como prueba compatible provisional, nunca como atribución
institucional. Si todo el archivo es ASCII, se acredita ese repertorio completo;
no se identifica retrospectivamente el codec utilizado por el productor.

Si hay texto no ASCII compatible con UTF-8 sin BOM/declaración, se permite recorrer
hasta EOF, pero el estado permanece `INCIERTA` y la codificación no se confirma.
Si hay bytes inválidos, se detiene sin reemplazarlos. Una codificación explícita
inválida es un fallo pertinente de decodificación; sin evidencia suficiente se
conserva incertidumbre. Se informa posición de byte de base 1 cuando está disponible,
además de línea/columna. El prefijo válido anterior a un error no se pierde por
prefetch del decoder.

La selección automática reutiliza una muestra limitada y puede ser incierta si
hay varios delimitadores posibles o se corta un campo. El llamador puede declarar
un delimitador documentado. Se admiten coma, punto y coma, tabulador y barra vertical;
comillas dobles, duplicación de comillas, sin escape adicional ni recorte de espacios.

## Errores, alcance y cierre

- Solo alcanzar EOF por el iterador y comprobar identidad permite afirmar recorrido
  completo. Leer por adelantado todos los bytes no basta. Un `break`, cancelación,
  límite o error de E/S conserva alcance incompleto y motivo explícito.
- Un límite de registros alcanzado se detiene antes de solicitar el siguiente.
  Incluso si coincide con el último registro, no se presume EOF sin haberlo observado.
- Anchuras distintas se cuentan por registro y permiten continuar hasta el límite
  de diagnósticos. Una sintaxis grave detiene sin adivinar dónde comienza el siguiente.
- `registros_completos` cuenta filas entregadas por el parser, incluidas las de
  anchura incorrecta. `registros_problematicos` incluye también un registro fatal
  parcialmente interpretado, identificado mediante `registro_interrumpido`; no se
  presenta ese contador como total del archivo cuando no se llegó al final.
- Un recorrido completo con anchuras incorrectas sigue siendo estructuralmente
  problemático; EOF no equivale a compatibilidad. Vacío, dialecto o codificación
  desconocidos no reciben estado compatible.
- Los diagnósticos contienen códigos y posiciones, sin copiar celdas ni mensajes
  del backend. La fecha del informe es técnica y no localiza las observaciones.
- El contexto cierra el descriptor incluso ante excepciones del consumidor. Se
  rechazan symlinks/junctions y componentes `..`; se comparan dispositivo, inode,
  tamaño y mtime al cerrar. Se necesitan directorios controlados y uso secuencial:
  no hay aislamiento frente a un escritor hostil ni un snapshot del sistema de archivos.

## Pruebas

Las 42 pruebas nuevas utilizan exclusivamente archivos sintéticos temporales.
Cubren comillas, escapes, multilínea, BOM, decodificación estricta, dialectos,
anchuras, campos/líneas/registros largos, límites, EOF, cancelación, reapertura,
contenido intacto, rutas, E/S, cambios concurrentes simulados y protección ante
HTML/JSON. Un guardián verifica que todas las lecturas tienen tamaño explícito.
`tracemalloc` compara 1.000 y 50.000 registros consumidos sin acumularlos y exige
un pico inferior a 4 MiB para esas fixtures; no es una promesa de ese pico para
todos los límites configurables.

Antes de acceder al CSV operativo aprobó la suite completa: **625 pruebas**
(585 anteriores y 40 nuevas), cero fallos y cero errores. La revisión posterior
añade dos regresiones sobre interrupción de apertura y error de E/S durante el recorrido.
Las pruebas automatizadas
no leen ni escriben RAW permanente, staging o SQLite operativo.

## Inspección real

El resultado del muestreo del PASO 68 permanece como antecedente: 1.000 registros,
256 KiB de muestra y estado incompleto. El PASO 69 no reescribe esa evidencia.
La nueva inspección usa el original autorizado, consulta SQLite con
`mode=ro&immutable=1` y `query_only=ON`, y compara hashes e identidad de todos los
archivos RAW/staging antes y después. No llama a `recuperar()`, `verificar()` ni
`diagnosticar()` de RAW porque pueden registrar eventos o comprobaciones.

El diccionario oficial adquirido previamente se consulta en modo lectura, sin
internet y sin cambiar su ACL. Se comprueba su SHA-256 histórico
`1851039a07682a3f202314f6f8811fc616cb4ca2a486c9e737fd8cea62a4b4dd`.
Documenta `ID` como identificador del registro, `ESTACION` como nombre, `FECHA`
como aaaammdd y `HORA` como hhmmss. No documenta una zona para esas columnas.
`PP` se describe literalmente como precipitación total horaria, «milimetros por
hora»; no se convierte ni reinterpreta su unidad.

### Resultado del original autorizado

Inspección del 2026-10-29, entre 22:44:14 y 22:45:54 UTC. Activo
`71df55229ee947fb8e7fed8b1403289e`, adquisición `ff8e7846a9b14568aad924aa8ca93f74`.
Antes y después: **50.474.012 bytes**, SHA-256
`3d3e8a0a75e070d0b8111faf921be17140c3a0f9db2b4c25d72d99a15a950eab`.
Coinciden además inode/mtime, hashes de todos los archivos RAW/staging y estado
SQLite: v2, dos activos y diez eventos, sin escrituras ni copias completas.

El lector recorrió 50.474.012 bytes hasta EOF, además de 65.536 bytes de muestra
inicial releídos. Resultado `COMPATIBLE`, recorrido completo: **416.274 registros
lógicos y líneas físicas**, incluidos encabezado y **416.273 filas de datos**.
Todos tienen 16 campos, con cero registros de sintaxis/anchura problemáticas.
Se comprobó repertorio ASCII en todo el archivo, sin BOM; delimitador coma.
Se mantuvieron comillas dobles, duplicación de comillas y espacios originales.

El encabezado observado coincide exactamente con las 16 variables del diccionario:

```text
ID,ESTACION,FECHA,HORA,LONGITUD,LATITUD,ALTITUD,TEMP,HR,PP,RED,DEPARTAMENTO,PROVINCIA,DISTRITO,UBIGEO,FECHA_CORTE
```

No se impuso un encabezado al lector. Su identificación procede de esa coincidencia
documental posterior, y la fila permanece incluida en los conteos del informe.

Cinco nombres literales distinguibles en `ESTACION`, cada uno con una única tupla
observada de longitud/latitud/altitud/UBIGEO/red. Son agrupaciones por nombre, sin
convertirlas en códigos o garantizar identidad física universal:

| ESTACION exacta | Filas de datos | TEMP no vacía | HR no vacía | PP no vacía | UBIGEO literal |
| --- | ---: | ---: | ---: | ---: | --- |
| CANDARAVE | 83.256 | 81.381 | 81.113 | 81.358 | `230201.0` |
| CARANIA | 83.253 | 81.667 | 81.571 | 81.643 | `151007.0` |
| IMATA | 83.253 | 79.171 | 79.001 | 78.247 | `40514.0` |
| MATUCANA | 83.255 | 78.304 | 78.271 | 78.222 | `150701.0` |
| SAN_JOSE_DE_UZUNA | 83.256 | 82.407 | 82.196 | 82.363 | `40114.0` |

Las columnas TEMP, HR y PP aparecen realmente en las filas. Celdas vacías:
TEMP **13.343**, HR **14.121**, PP **14.440**; las otras 13 columnas no tienen celdas
vacías. No se observaron celdas compuestas solo por espacios. Todos los valores no
vacíos de estas tres variables cumplen una sintaxis numérica léxica, sin convertirlos
ni evaluar su plausibilidad. «No vacío» no significa medición válida.

No aparecieron en TEMP/HR/PP los candidatos literales buscados `NA`, `N/A`, `NULL`,
`null`, `NaN`, `nan`, `S/D`, `s/d`, `-999`, `-999.0`, `-9999`, `-9999.0`, `-99.9`,
`9999`. La aparición de `9999` en ID se conserva como identificador, sin atribuirle
significado de faltante. Esta búsqueda no descarta otros centinelas numéricos.

FECHA tiene ocho caracteres y todas sus filas cumplen aaaammdd y el calendario:
mínimo **2015-01-01**, máximo **2024-06-30**, también para cada nombre. El primer
valor del archivo es `20150101` y el último `20240630`. FECHA_CORTE es `20240630`
en las 416.273 filas. Es cobertura civil observada, no una promesa de continuidad.

HORA presenta **170.400 valores de cinco caracteres**, no conformes al formato
hhmmss de seis caracteres documentado. Son diez literales (`00000`, `10000`,
`20000`, `30000`, `40000`, `50000`, `60000`, `70000`, `80000`, `90000`) con 17.040
apariciones cada uno. No se rellenaron ceros ni se convirtieron horas a UTC.
Los otros 245.873 valores cumplen la forma hhmmss. Se observaron 34 literales
de hora en total. El diccionario declara variables horarias; no se infirió una
periodicidad observada inequívoca ni se evaluaron huecos/duplicados temporales.

UBIGEO contiene sufijo `.0` y no tiene la forma textual de seis caracteres del
diccionario. No se retiró el sufijo ni se restauraron ceros supuestamente perdidos.
ID sigue siendo identificador del registro, no de estación. RED contiene GBON
en 166.508 filas y RBON en 249.765. No se excedió ningún límite de cardinalidad.

Dictamen limitado a sintaxis y estructura tabular: **CSV ESTRUCTURALMENTE COMPROBADO**.
Las discrepancias HORA/UBIGEO requieren revisión antes de normalizar o interpretar
temporalmente las observaciones. El resultado no modifica evidencia ni estado RAW.

El inventario operativo acota nombres a 512, variantes de metadatos por nombre a
4, horas a 256, fechas de corte a 64 y redes a 16. Cualquier exceso se comunica
explícitamente: no se publica como completo un agregado truncado. La caché de fechas
civiles tiene como máximo 4.096 claves y no afecta los conteos al agotarse.
Los marcadores se cuentan por literal; su significado de dato faltante no se infiere.
Las agrupaciones por nombre no demuestran identidad física única de estaciones.

Una compatibilidad CSV completa no acredita autenticidad institucional, ausencia
de duplicados, completitud meteorológica, periodicidad ni validez científica.
Permanecen pendientes la identidad estable de estaciones, significado de marcadores,
zona horaria, resolución de discrepancias documentales y persistencia versionada de
informes. No se amplía el conector ni se inicia procesamiento ambiental.

## Verificación final del PASO 69

Entorno: Python 3.15.1, HTTPX 0.28.1 y SQLite 3.53.4, usando `.venv` y `-B`.

```text
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
Ran 627 tests in 52.394s
OK

.\.venv\Scripts\python.exe -B -m pip check
No broken requirements found.

git diff --check
Código de salida 0. Avisos de futura conversión LF a CRLF en archivos modificados.
```

Resultado: 585 pruebas anteriores y 42 nuevas aprobadas, cero fallos y cero errores.
Git inicial limpio, rama `feature/suadc-http`, commit `71a6dd7`. Quedan modificados
`verificacion/_csv.py` y `verificacion/__init__.py`; son nuevos `csv_streaming.py`,
`tests/test_csv_streaming.py` y este documento. No hubo commits, instalaciones,
conexiones externas ni modificaciones al conector, RAW, staging o SQLite operativos.
