# PASO 71: perfilado descriptivo de consistencia meteorológica

## Responsabilidad y evidencia disponible

El paquete nuevo `spica.perfilado` se ubica fuera de `spica.adquisicion`. Describe
contenido local ya adquirido; no ejecuta adquisiciones, modifica contratos anteriores,
normaliza observaciones ni certifica QA/QC científico. No se introduce otro parser:
usa `LectorCSV`, el encabezado y las variables públicas de `consultas_locales`, y
su `ProcedenciaLocal`. No utiliza sus helpers privados ni debilita contratos de
instantes con zona para representar fechas civiles.

Se inspeccionaron el lector secuencial, inspector estructural, consultas locales,
`VariableCatalogo`, `EvidenciaDocumental` y la integración HTTP→RAW. Los resultados
estructurales y estados RAW permanecen separados del nuevo perfil. La procedencia
conserva fuente, recurso, asset_id y SHA declarado; admite opcionalmente una
`EvidenciaDocumental` compatible con la misma fuente/recurso, sin inventar revisiones.

El diccionario oficial examinado en el PASO 69 identifica ID como registro,
ESTACION como nombre, FECHA como aaaammdd y HORA como hhmmss. Declara TEMP como
temperatura promedio horaria (°C), HR como humedad relativa promedio horaria (%) y
PP como precipitación total horaria («milimetros por hora», texto original). No se
reinterpretan esas unidades ni se asigna zona horaria. Los detalles y la huella del
diccionario están en [csv_streaming.md](csv_streaming.md); en este paso no se vuelve
a descargar ni abrir ese recurso. No existe código estable de estación en el CSV.

## API y contratos

```python
from spica.perfilado import perfilar_csv, LimitesPerfil

informe = perfilar_csv(ruta_csv, procedencia,
    limites=LimitesPerfil(), directorio_temporal=directorio_controlado)
```

`InformePerfil` contiene procedencia, documento opcional, huellas físicas antes y
después, estado/motivo de finalización, contadores por estación/variable, metadatos
de ubicación, horas, días, períodos mensuales, resumen temporal, hallazgos, límites
y el informe original de lectura. El propio perfilador calcula SHA-256 por bloques
y comprueba el hash declarado cuando existe. El hash no prueba autenticidad de origen.

Se exige el encabezado exacto de 16 campos del perfil SENAMHI GBON/RBON. Los grupos
usan ESTACION literalmente, sin strip, cambios de mayúsculas ni equivalencia de ID
o UBIGEO. TEMP/HR/PP se procesan solamente donde aparecen en las filas reales.
Los contadores por variable particionan todas sus celdas en vacío, finito, no finito,
no interpretable y fuera del presupuesto numérico. `no_vacios` incluye los últimos
cuatro grupos. Espacios no equivalen a vacío.

La gramática finita acepta dígitos ASCII, signo opcional, punto decimal y exponente
opcional. No interpreta coma decimal, separadores de miles, guiones bajos, dígitos
Unicode o espacios externos. Clasifica por separado exponenciales, puntos sin parte
entera/fraccionaria y ceros iniciales. Cuenta signos/puntos en valores finitos.
NaN, sNaN (y cargas decimales), Inf/Infinity con signo y distintas mayúsculas son
literales no finitos; no se comparan con extremos.

`Decimal(texto)` se ejecuta solo tras verificar longitud, cantidad de dígitos de
mantisa y exponente explícito. Su construcción y comparación son exactas, sin float,
operaciones aritméticas ni redondeo según el contexto decimal global. Los extremos
retienen Decimal, texto original, fila y FECHA/HORA literales. Empates conservan la
primera aparición. No se aplican umbrales físicos ni exclusiones por improbabilidad.
La lista de marcadores es explícita y configurable; una coincidencia es léxica,
no una declaración de faltante. Un marcador numérico sigue participando en extremos.

Los extremos describen únicamente finitos admitidos. Un valor fuera del presupuesto
se cuenta y alerta; `extremos_comparables_completos=False`. Ese caso no transforma
silenciosamente el valor en vacío o no numérico. Un recorrido completo puede contener
anomalías o fechas inválidas: `completo` acredita ejecución técnica del perfil,
no calidad científica. La cobertura temporal indica por separado si todas las fechas
fueron interpretables. Una ejecución parcial nunca declara completos los extremos.

## HORA, ubicación y tiempo civil

HORA se cuenta por literal, longitud y patrón por estación, con cobertura civil
mínima/máxima por literal y distribución conjunta por estación/mes civil. Para seis
dígitos se comparan rangos de fragmentos hh/mm/ss; para cinco se examina si sus
fragmentos son compatibles con la hipótesis de un único cero inicial omitido.
No se construye la cadena reconstruida. También se informan fragmentos de caracteres
de cinco y seis posiciones, de modo que horas y minutos no se confundan en el informe.
La compatibilidad con una hipótesis no es evidencia de que esa causa ocurrió.

Por nombre se cuentan todos los literales distintos de RED, LONGITUD, LATITUD,
ALTITUD, DEPARTAMENTO, PROVINCIA, DISTRITO y UBIGEO, sus tuplas conjuntas y cambios
consecutivos en el orden del archivo. Un cambio léxico no demuestra traslado físico.
Un nombre con varias tuplas se marca ambiguo; una sola tupla tampoco demuestra que
solo exista una instalación. No se convierten coordenadas ni se valida INEI.

FECHA se interpreta estrictamente como fecha civil de ocho dígitos y calendario
válido. Se cuentan filas por estación/día, HORA literales distintas y repeticiones
exactas. Las filas desordenadas no se pierden: los agregados usan claves, no una
presunción de orden cronológico. También se cuentan retrocesos de fecha en el orden
original. Por estación se devuelven cobertura, distribución de cantidad de filas
diarias, días con varias HORA y saltos entre fechas vecinas observadas. Esos saltos
describen fechas no representadas en el archivo, sin afirmar ausencia de mediciones.
Ni 24 filas ni 24 HORA distintas acreditan continuidad horaria o instantes UTC.

## Límites, recursos y fallos

Los límites son configurables, con topes rígidos y rechazo de bool como cantidad:

| Presupuesto predeterminado | Límite |
| --- | ---: |
| Archivo / bloque / registros del lector | 128 MiB / 64 KiB / 2.000.000 incluido encabezado |
| Nombres de estación | 64 |
| Variantes por campo de ubicación / tuplas por estación | 16 / 32 |
| HORA distintas por estación | 128 |
| Claves estación–FECHA–HORA | 500.000 |
| Claves estación–día / estación–mes–HORA | 20.000 / 20.000 |
| Literales no vacíos distintos por estación–variable, total global | 50.000 |
| Índice SQLite / caché SQLite | 64 MiB / 1 MiB |
| Texto agregado / texto numérico | 512 / 128 caracteres |
| Dígitos de mantisa / exponente explícito absoluto | 64 / 1.000 |
| Ejemplos por grupo / literales repetidos destacados | 20 / 10 |

Se conservan los límites previos de campo/línea/registro del lector. No hay lista
de observaciones ni todos los valores individuales en memoria. Los índices guardan
claves agregadas y conteos, no series de observaciones; los valores distintos también
están acotados. El informe conserva días y grupos mensuales hasta sus límites, no
todas las filas. Los repetidos destacados tienen conteos exactos y se ordenan por
frecuencia descendente y literal en empates; no se presentan como lista exhaustiva.
La memoria depende de cardinalidades y longitudes configuradas, no es una cuota del SO.

El índice efímero está fuera del directorio del CSV, en un padre controlado sin
symlinks/junctions. Nombre aleatorio y creación exclusiva; nunca se adopta un archivo
preexistente. Se comprueba espacio para el índice más 2 MiB de margen, sin reservarlo.
`max_page_count` limita tamaño, caché explícita, consultas por PK sin sorts globales,
commits cada 1.000 filas y `journal_mode=OFF`: no hay garantía de durabilidad del
índice, que siempre se descarta y nunca se reabre o recupera tras una interrupción.

Al fallar/cancelarse el recorrido o la construcción del informe, se omiten **todos**
los agregados derivados del índice y se marca `agregados_indexados_disponibles=False`.
Evita publicar conteos de un índice con una fila o transacción parcialmente escrita.
Los contadores en RAM describen solo las filas completamente procesadas. Un límite
explica su motivo; no hay truncamiento silencioso. Los ejemplos sí son muestras
acotadas, y su truncamiento no cambia los conteos. `KeyboardInterrupt` se propaga
tras cerrar y limpiar; un Event permite cancelación cooperativa durante lectura,
hashes y resumen. Una terminación forzosa puede dejar residuos temporales.

Se eliminan exclusivamente archivo propio y directorio vacío; nunca borrado recursivo.
Una colisión no se elimina. Un fallo de limpieza impide declarar completo y se informa.
POSIX solicita 0700; Windows hereda ACL del padre sin modificarlas. El operador debe
garantizar privacidad de ese padre; no hay certificación automática de ACL Windows.
Los errores públicos de E/S/SQLite contienen códigos, sin mensajes backend ni rutas.
Los resultados contienen literales del recurso y el llamador controla su difusión.

La reproducibilidad cubre valores, orden de grupos y posiciones para la misma versión
del archivo/política; la fecha técnica del informe de lectura cambia. Se comprueban
identidad del lector y hashes inicial/final, pero no hay snapshot ni bloqueo frente
a escritores hostiles que modifiquen y restauren el archivo durante la lectura.
Se exige uso secuencial y directorios controlados. Ninguna API RAW registra eventos.

## Validación y resultados reales

Primero se ejecutan fixtures sintéticas; el perfilado operativo solo comienza tras
aprobar la suite completa. Las pruebas no acceden a RAW/staging/SQLite permanentes.
El detalle de ejecución y resultados descriptivos se incorpora después de comprobarlos.

Entorno comprobado con `.venv`: Python **3.15.1**, HTTPX **0.28.1**, SQLite **3.53.4**.
Las **48 pruebas nuevas** aprobaron primero de forma aislada (17,948 s). Después,
antes de acceder al original operativo, se ejecutó:

```text
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
Ran 726 tests in 72.065s
OK

.\.venv\Scripts\python.exe -B -m pip check
No broken requirements found.
```

**726 aprobadas: 678 anteriores y 48 nuevas; cero fallos y cero errores.** Se cubren
partición de celdas, decimal exacto independiente del contexto, no finitos, marcadores,
notaciones, extremos, coordenadas/identificadores ambiguos, fechas repetidas y
desordenadas, horas de cinco/seis posiciones, límites de registros/bytes/grupos,
memoria, cancelación, interrupción, fuente modificada, integridad y procedencia.
También errores/espacio/límite físico SQLite, conservación de objetos ajenos,
limpieza y lecturas binarias con tamaño explícito. Las pruebas de memoria consumen
500 y 15.000 filas sin acumular observaciones; exigen pico Python menor de 8 MiB
para esas fixtures y crecimiento menor de 1 MiB. No miden toda la memoria nativa
de SQLite ni prometen ese pico para cualquier cardinalidad.

Git inicial limpio, rama `feature/suadc-http`, commit **315fe7d** del PASO 70.
No se modifica código, pruebas ni documentos previos; se añaden el paquete de
perfilado, sus pruebas y este informe. No se instalan dependencias ni crean commits.


## Perfilado real de solo lectura

Ejecución del **2026-10-29, 23:30:29–23:33:26 UTC**, hora técnica del proceso.
Activo `71df55229ee947fb8e7fed8b1403289e`; Fuente `SENAMHI`/`SENAMHI` y URL del
recurso CSV conservadas en `ProcedenciaLocal`, sin solicitud HTTP. `documento=None`:
no se crea una nueva instantánea institucional ni se inventan revisiones. La base
documental previa permanece en el repositorio y en sus antecedentes de adquisición.

Se procesaron **416.273 filas de datos**, más encabezado (416.274 registros/líneas),
hasta EOF, con repertorio ASCII comprobado y cero anomalías de sintaxis/anchura.
`completo=True`, motivo `eof`, agregados indexados disponibles y temporal eliminado.
Se generaron 17.345 grupos estación–día y 570 grupos estación–mes, dentro de límites.
No se aplicó ninguna regla científica. No se transformó un estado RAW.

### Variables: conteos y extremos observados

Todos los no vacíos fueron interpretables como decimales finitos. En cada uno de
los 15 grupos: cero no interpretables, cero NaN/Infinity, cero valores fuera del
presupuesto y cero notaciones clasificadas como inesperadas. Todos los finitos
contienen punto decimal. No aparecieron los marcadores explícitos buscados; esto
no descarta otros centinelas no documentados ni valida los números.

Los extremos siguientes son **textos originales**, no umbrales ni errores declarados.
El informe de la API conserva además fila y FECHA/HORA originales para cada extremo.

| ESTACION | Variable | Total | Vacíos | Finitos/no vacíos | Con signo | Mínimo literal | Máximo literal | Literales distintos |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- | ---: |
| CANDARAVE | TEMP | 83256 | 1875 | 81381 | 104 | `-2.5` | `21.7` | 239 |
| CANDARAVE | HR | 83256 | 2143 | 81113 | 0 | `5.0` | `100.0` | 98 |
| CANDARAVE | PP | 83256 | 1898 | 81358 | 0 | `0.0` | `12.6` | 65 |
| CARANIA | TEMP | 83253 | 1586 | 81667 | 27 | `-1.7` | `21.9` | 225 |
| CARANIA | HR | 83253 | 1682 | 81571 | 0 | `5.0` | `100.0` | 96 |
| CARANIA | PP | 83253 | 1610 | 81643 | 0 | `0.0` | `10.9` | 80 |
| IMATA | TEMP | 83253 | 4082 | 79171 | 24197 | `-16.7` | `18.0` | 339 |
| IMATA | HR | 83253 | 4252 | 79001 | 0 | `5.0` | `100.0` | 100 |
| IMATA | PP | 83253 | 5006 | 78247 | 0 | `0.0` | `13.3` | 73 |
| MATUCANA | TEMP | 83255 | 4951 | 78304 | 0 | `7.1` | `26.3` | 183 |
| MATUCANA | HR | 83255 | 4984 | 78271 | 0 | `7.0` | `100.0` | 94 |
| MATUCANA | PP | 83255 | 5033 | 78222 | 0 | `0.0` | `12.7` | 70 |
| SAN_JOSE_DE_UZUNA | TEMP | 83256 | 849 | 82407 | 598 | `-3.9` | `24.0` | 269 |
| SAN_JOSE_DE_UZUNA | HR | 83256 | 1060 | 82196 | 0 | `6.0` | `100.0` | 98 |
| SAN_JOSE_DE_UZUNA | PP | 83256 | 893 | 82363 | 0 | `0.0` | `32.5` | 140 |

Vacíos totales: TEMP **13.343**, HR **14.121**, PP **14.440**. Los extremos no se
excluyen ni califican científicamente. No se aplicó un rango físico de HR ni se
convirtió la descripción de PP; esa interpretación necesita criterio documental.

### Patrones repetidos

Cada celda de la tabla muestra el literal más frecuente y su conteo exacto por
estación/variable; es una selección descriptiva, sin atribuir saturación o fallo.
La API conserva hasta diez literales repetidos por grupo.

| ESTACION | TEMP: literal (n) | HR: literal (n) | PP: literal (n) |
| --- | --- | --- | --- |
| CANDARAVE | `7.9` (928) | `100.0` (4983) | `0.0` (78971) |
| CARANIA | `5.8` (1319) | `100.0` (18549) | `0.0` (74606) |
| IMATA | `2.3` (653) | `100.0` (14859) | `0.0` (72612) |
| MATUCANA | `13.3` (1235) | `100.0` (8000) | `0.0` (73686) |
| SAN_JOSE_DE_UZUNA | `8.7` (643) | `100.0` (11227) | `0.0` (79022) |

La frecuencia de HR `100.0` o PP `0.0` no prueba dato inválido, censura, repetición
instrumental ni completitud de observaciones. Se requieren códigos y procedimientos
de calidad del productor antes de atribuirles ese significado.

### HORA: estación, período y fragmentos

| ESTACION | Cinco caracteres | Seis caracteres | Literales distintos |
| --- | ---: | ---: | ---: |
| CANDARAVE | 34080 | 49176 | 34 |
| CARANIA | 34080 | 49173 | 34 |
| IMATA | 34080 | 49173 | 34 |
| MATUCANA | 34080 | 49175 | 34 |
| SAN_JOSE_DE_UZUNA | 34080 | 49176 | 34 |

Total: **170.400** de cinco y **245.873** de seis, 34 literales globales. Solo se
observaron dos patrones: cinco dígitos compatibles con omisión de un cero inicial,
y seis con forma/rangos léxicos hhmmss. No hay otros caracteres, vacíos o rangos
léxicos incompatibles. Los diez literales de cinco caracteres son `00000`, `10000`,
`20000`, `30000`, `40000`, `50000`, `60000`, `70000`, `80000`, `90000`: cada uno
aparece 3.408 veces por estación, 17.040 en el conjunto.

Para seis posiciones, los fragmentos segundo y tercero (mm/ss según el formato
documentado) son siempre `00`; para cinco, los fragmentos de las posiciones 2–3
y 4–5 también son siempre `00`. El primer fragmento de cinco posiciones es un
solo dígito 0–9; el de seis es un par de caracteres entre `00` y `23`. No se
registran fragmentos de minutos o segundos distintos de `00` bajo esas divisiones.
Eso no demuestra que el campo represente instantes o una cadencia horaria efectiva.

Cobertura literal en **cada** nombre:

- `00000`–`90000` (los diez literales enumerados): **2015-01-01–2024-04-30**.
- `000000`, `010000`, …, `090000`: **2024-05-01–2024-06-30**.
- `100000`, `110000`, …, `230000`: **2015-01-01–2024-06-30**.

La API conserva distribución por cada estación/mes. Resumen anual del conjunto:

| Año civil | Cinco caracteres | Seis caracteres |
| --- | ---: | ---: |
| 2015 | 18250 | 25550 |
| 2016 | 18300 | 25620 |
| 2017 | 18250 | 25550 |
| 2018 | 18250 | 25550 |
| 2019 | 18250 | 25550 |
| 2020 | 18300 | 25620 |
| 2021 | 18250 | 25550 |
| 2022 | 18250 | 25550 |
| 2023 | 18250 | 25550 |
| 2024 | 6050 | 15783 |

Hasta 2023, por estación: 3.650/5.110 en cada año de 365 días; 3.660/5.124 en
2016 y 2020. En 2024, cada estación tiene 1.210 literales de cinco posiciones;
los de seis son 3.158 (CANDARAVE y SAN_JOSE_DE_UZUNA), 3.155 (CARANIA e IMATA)
y 3.157 (MATUCANA). Detalle mensual de la transición:

| ESTACION | Abril 2024: cinco/seis | Mayo 2024: cinco/seis | Junio 2024: cinco/seis |
| --- | --- | --- | --- |
| CANDARAVE | 300/420 | 0/744 | 0/720 |
| CARANIA | 300/420 | 0/741 | 0/720 |
| IMATA | 300/420 | 0/743 | 0/718 |
| MATUCANA | 300/420 | 0/744 | 0/719 |
| SAN_JOSE_DE_UZUNA | 300/420 | 0/744 | 0/720 |

**Evidencia comprobada:** anchura discordante con hhmmss antes de la frontera civil,
fragmentos finales `00`, y cambio coincidente en los cinco nombres el 2024-05-01.
**Hipótesis:** una serialización pudo haber omitido ceros iniciales; los fragmentos
son compatibles con ello y no aparecen patrones de cinco posiciones que lo refuten.
**Conclusión limitada:** la forma varía con el período y requiere aclaración del
productor. La coincidencia no prueba el mecanismo causante ni justifica rellenar,
reconstruir, convertir a datetime o asignar zona. Se necesita una regla oficial,
registro del cambio de exportación y contraste autorizado con observaciones de origen.

### Identidad y ubicación

Cada nombre presenta un único literal por cada uno de los ocho campos y una sola
tupla conjunta, con cero cambios consecutivos observados. Se conservan coordenadas
como texto; no se comprobaron CRS, precisión geodésica o identidad de instalaciones.

| ESTACION | RED | LONGITUD | LATITUD | ALTITUD | DEPARTAMENTO / PROVINCIA / DISTRITO | UBIGEO |
| --- | --- | --- | --- | --- | --- | --- |
| CANDARAVE | `RBON` | `-70.2541` | `-17.268` | `3410.0` | `TACNA` / `CANDARAVE` / `CANDARAVE` | `230201.0` |
| CARANIA | `GBON` | `-75.8722` | `-12.3444` | `3840.0` | `LIMA` / `YAUYOS` / `CARANIA` | `151007.0` |
| IMATA | `RBON` | `-71.0906` | `-15.8427` | `4475.0` | `AREQUIPA` / `CAYLLOMA` / `SAN_ANTONIO_DE_CHUCA` | `40514.0` |
| MATUCANA | `GBON` | `-76.378` | `-11.8391` | `2421.0` | `LIMA` / `HUAROCHIRI` / `MATUCANA` | `150701.0` |
| SAN_JOSE_DE_UZUNA | `RBON` | `-71.3284` | `-16.581` | `3269.0` | `AREQUIPA` / `AREQUIPA` / `POLOBAYA` | `40114.0` |

Los 416.273 UBIGEO tienen sufijo `.0`; textos de longitud 7 en IMATA y
SAN_JOSE_DE_UZUNA y 8 en los otros tres nombres. No coinciden con los seis caracteres
del diccionario. Es evidencia de formato, no de códigos administrativos incorrectos.
La representación numérica previa y pérdida de ceros son hipótesis; no se quita el
sufijo ni se rellena. Hace falta correspondencia oficial con códigos INEI, versión
territorial aplicable y un catálogo estable de estaciones. Igual nombre o ubicación
constante no demuestra instalación única. ID no participa en la agrupación.

### Perfil temporal civil

Los cinco nombres comparten extremos **2015-01-01 y 2024-06-30**, con **3.469 fechas
civiles observadas** cada uno. No hay fechas ilegibles, retrocesos en el orden del
archivo, intervalos entre fechas observadas no consecutivas ni repeticiones de HORA
literal por nombre y fecha. Todas esas fechas tienen varias HORA literales distintas.
El resultado no asegura continuidad horaria, completitud de variables ni mediciones.

| ESTACION | Días de 24 filas | Días de 23 filas | Días de 21 filas |
| --- | ---: | ---: | ---: |
| CANDARAVE | 3469 | 0 | 0 |
| CARANIA | 3468 | 0 | 1 |
| IMATA | 3466 | 3 | 0 |
| MATUCANA | 3468 | 1 | 0 |
| SAN_JOSE_DE_UZUNA | 3469 | 0 | 0 |

Los cinco grupos estación–día con cantidades diferentes de 24 son:

| ESTACION | Fecha civil | Filas | HORA literales distintas |
| --- | --- | ---: | ---: |
| CARANIA | 2024-05-29 | 21 | 21 |
| IMATA | 2024-05-31 | 23 | 23 |
| IMATA | 2024-06-02 | 23 | 23 |
| IMATA | 2024-06-19 | 23 | 23 |
| MATUCANA | 2024-06-26 | 23 | 23 |

La diferencia de cantidades es una observación descriptiva, **no siete mediciones
ausentes demostradas**. No se construye una grilla horaria esperada ni se declara
que las horas presentes correspondan a UTC. La ausencia de fechas enteras omitidas
tampoco corrige los 41.904 campos vacíos en TEMP/HR/PP.

### Conservación física y restricciones

Antes y después, el CSV conserva **50.474.012 bytes** y SHA-256 físico:

```text
3d3e8a0a75e070d0b8111faf921be17140c3a0f9db2b4c25d72d99a15a950eab
```

Ruta autorizada:

```text
C:\Users\Propietario\SPICA_DATOS\raw\sha256\3d\3d3e8a0a75e070d0b8111faf921be17140c3a0f9db2b4c25d72d99a15a950eab
```

El inventario previo/posterior de RAW y staging coincide en archivos/directorios,
contenido SHA-256, tamaños, inode, mtime y enlaces; no se compara atime del SO.
Original sintético y staging conservan 57 bytes y hash
`82c649098a927a255181c8b05d18aec30594fa89571bad2792464f3ba255f4cb`.
El marcador sigue intacto y RAW/temporales vacío. No aparecieron WAL/SHM/journal
ni archivos inesperados. Staging solo contiene `paso64-sintetico.bin`.

El catálogo operativo **no se abrió con SQLite**, tampoco para lectura: se comparó
como archivo binario de 32.768 bytes, con SHA-256 antes/después
`946d2512795c5ae3a68113f63438110be66dee32488ad02e86d550da040d4a0d`.
Durante la ejecución se restringió además sqlite3.connect al índice temporal del
perfilador fuera de RAW. No se reafirman mediante nuevas consultas SQL los conteos
históricos de activos/eventos; la evidencia actual es conservación física del catálogo.

No se detectaron otros procesos Python/pythonw/sqlite3 conocidos al comenzar, sin
pretender que ello equivalga a un bloqueo exclusivo. No hubo descargas, conexiones
externas, escrituras operativas, migraciones, instalación de dependencias ni commits.

### Dictamen

**APTO CON RESTRICCIONES** para continuar con inspección descriptiva. Siguen pendientes
resolución documental de HORA/UBIGEO, zona, identificadores estables de estaciones,
códigos de calidad/sentinelas y criterio científico para interpretar valores, extremos
y diferencias de registros diarios. La repetición de números o consistencia interna
no demuestra calibración, exactitud meteorológica o completitud de observaciones.
No se normalizó tiempo ni se inició QA/QC, análisis climático o procesamiento ambiental.

## Estado final de Git

`git diff --check`: código de salida 0. También se comprobaron directamente los
espacios finales de los seis archivos nuevos, sin problemas; todavía no están
rastreados y por eso no aparecen en el diff de archivos previamente registrados.
La rama y HEAD permanecen en `feature/suadc-http` / `315fe7d`.

```text
git status --short
?? docs/perfilado_meteorologico.md
?? src/spica/perfilado/
?? tests/test_perfilado_meteorologico.py
```

Se crearon `perfilado/__init__.py`, `modelos.py`, `_indice.py`, `meteorologico.py`,
`tests/test_perfilado_meteorologico.py` y este documento. No se modificaron archivos
previamente rastreados, contratos anteriores, dependencias, `main.py`, `.gitignore`
ni `.venv`. No se hicieron commits ni push.

