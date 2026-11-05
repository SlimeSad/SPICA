# PASO 84-E: inspección offline del diccionario PNDA/SENAMHI

Fecha: **2026-11-05**. Resultado para revisión: **APTO CON RESTRICCIONES** para
conservar evidencia y preparar metadatos declarados localizados. No acredita
identidad física, aptitud espacio-temporal, vigencia editorial ni calidad científica.
No incorpora metadatos al catálogo ni cambia resultados de interoperabilidad.

Entregables: [matriz de 29 brechas y consultas pendientes](brechas_diccionario_pnda_paso84e.md),
[diagnóstico aislado](../herramientas/inspeccionar_xlsx_84e.py) y
[pruebas sintéticas](../tests/test_diagnostico_xlsx_84e.py).
El inventario de campos está en la sección 4 de este informe. La matriz histórica
y las decisiones del [84-D](auditoria_metadatos_pnda_paso84d.md) se conservan intactas.

## 1. Git, alcance y evidencia identificada

Git inicial limpio, rama `feature/suadc-http`, HEAD **`5b73fcc`**,
`SUADC: auditoria documental y brechas de metadatos PNDA`. El 84-D está registrado.
Se revisaron sus tres documentos: [auditoría](auditoria_metadatos_pnda_paso84d.md),
[matriz](brechas_metadatos_pnda_paso84d.md) y
[reconciliación](reconciliacion_evidencias_pnda_paso84d.md).

Se autorizó leer exclusivamente el XLSX ya identificado en aquel expediente,
preservar una copia exacta si era seguro y examinar su OOXML. No se buscaron otros
auxiliares en el equipo. No se abrió el CSV, el informe temporal histórico,
RAW permanente, staging o SQLite operativo. La lectura del XLSX situado bajo un
antiguo RAW **temporal** se limita al archivo exacto autorizado, sin abrir su catálogo.

**X84E** identifica en ambos documentos nuevos el mismo archivo de **10815 bytes**:

```text
SHA-256: 1851039a07682a3f202314f6f8811fc616cb4ca2a486c9e737fd8cea62a4b4dd
Origen: C:\Users\Propietario\AppData\Local\Temp\SPICA-SUADC-piloto-PNDA-soacxq6v\raw\sha256\18\1851039a07682a3f202314f6f8811fc616cb4ca2a486c9e737fd8cea62a4b4dd
Asset histórico: b6aa17105088497296147feb3c8f06e3
```

La comprobación inicial, a **2026-11-05T06:12:25.962456+00:00**, coincidió con
tamaño/hash documentados. Se comprobó archivo regular y se rechazaron symlinks,
junctions y componentes inesperados mediante `_segura` y `_huella` existentes.
Las lecturas comparan dispositivo/inode/tamaño/mtime y descriptor abierto.
El hash se calculó físicamente; no se tomó del nombre como prueba de integridad.
No se afirma resistencia frente a un propietario malicioso que sustituya rutas
concurrentemente: es el modelo secuencial y de directorios controlados del proyecto.

Origen editorial atribuido en los antecedentes: PNDA/SENAMHI, recurso diccionario
de la publicación *Variables Meteorologicas de las Estaciones automáticas de
intercambio internacional*. La URL publicada exacta permanece en el
[inventario de recursos del 84-D](auditoria_metadatos_pnda_paso84d.md#2-inventario-del-producto-y-recursos).
Se conserva como referencia histórica, **sin GET ni comprobación actual remota**.
Hash e integridad local no autentican al emisor ni acreditan vigencia.

## 2. Preservación documental privada

La ubicación original es temporal y susceptible de limpieza. Se creó exclusivamente
esta carpeta persistente, fuera del repositorio y de `SPICA_DATOS`:

```text
C:\Users\Propietario\SPICA_EVIDENCIAS_PNDA_84E
  diccionario-1851039a07682a3f202314f6f8811fc616cb4ca2a486c9e737fd8cea62a4b4dd.xlsx
  procedencia.json
  inspeccion.json
```

Se exigió carpeta inicialmente inexistente, ruta sin enlaces y directorio nuevo
privado (`os.mkdir(..., 0o700)` en este Python/Windows). Su DACL protegida admite
propietario, SYSTEM y administradores; se comprobó propietario actual y ausencia
de permisos Allow para otras identidades. Los tres archivos heredan esa política.
No se modificaron permisos del original ni de directorios existentes.

Copia realizada a **2026-11-05T06:26:39.339460+00:00**. Se escribió un archivo
propio `.part` con creación exclusiva `xb`, bloques de 65536 bytes y límite de
1 MiB; se cerró con `flush`/`fsync`, se verificó físicamente y se publicó mediante
`os.link` dentro de la misma carpeta. El enlace falla si el destino existe;
no hay reemplazo. Tras cotejar el archivo publicado se retiró solo el temporal
propio. La copia tiene identidad física distinta del original; **no es un hardlink
al original**. No quedó `.part`.

| Archivo privado | Bytes | SHA-256 comprobado |
|---|---|---|
| `diccionario-1851039a07682a3f202314f6f8811fc616cb4ca2a486c9e737fd8cea62a4b4dd.xlsx` | 10815 | `1851039a07682a3f202314f6f8811fc616cb4ca2a486c9e737fd8cea62a4b4dd` |
| `procedencia.json` | 930 | `cc3159b4d5c23f4013a9d22b757259d8247bc4616a7342743f48e69bf2e361ae` |
| `inspeccion.json` | 41036 | `07c9eb73066af4f9593a2f1d498fe47a304996adcdd521f6b77edcaed1a05887` |

El manifiesto registra origen/copia, fecha UTC, bytes, SHA, asset histórico,
antecedente y controles; el inventario privado conserva las celdas y partes
inspeccionadas. Son evidencia documental auxiliar: no se registró un asset nuevo,
se reutilizó almacenamiento operativo ni se cambió una instantánea de adquisición.
El informe temporal histórico no se copió ni reabrió; su hash está en el 84-D.

Garantías limitadas a este sistema de archivos local y la ejecución comprobada:
publicación exclusiva y bytes cotejados, sin prometer transacción entre manifiesto
y copia, sincronización de directorio portable en Windows, resistencia a apagados
en cualquier punto, protección frente al propietario/administrador o copia de
seguridad independiente. No se reintentaron operaciones inciertas. La copia
persistente reduce el riesgo de limpieza temporal; no es una política de backup.

## 3. Método, presupuestos y resultado técnico

Se usó exclusivamente Python **3.15.1 de `.venv`**, biblioteca estándar y los
controles ya existentes en
[`verificacion/_xlsx.py`](../src/spica/adquisicion/verificacion/_xlsx.py).
No se instaló un lector Excel ni se abrió Excel. El diagnóstico reutiliza
`inspeccionar_zip`, `_XML` y `_relaciones`; añade captura de texto al constructor
seguro de XML para el inventario. Importar el módulo no abre recursos. Sus
funciones devuelven datos en memoria; no escriben informes ni actualizan catálogos.
El arnés puntual de esta sesión escribió los dos JSON solo en la carpeta privada.

| Presupuesto explícito | Límite aplicado |
|---|---|
| Snapshot comprimido en memoria | 1 MiB; lectura acotada y cotejo de SHA antes de interpretar |
| Directorio ZIP | 64 entradas; central de 65536 bytes; sin ZIP64 |
| Lectura individual / acumulada del contenedor | Hasta 65557 bytes / 8 MiB por pasada, incluyendo relecturas |
| Descompresión | 4 MiB acumulados por pasada; 512 KiB por entrada; expansión máxima 100:1 |
| Árboles XML retenidos | Entrada XML total acotada a 4 MiB, 20000 nodos acumulados por pasada, profundidad 32; token pendiente acotado por el verificador existente |
| Inventario en memoria | 8 hojas, 2048 celdas, 4096 cadenas compartidas; 8192 caracteres por texto literal; 131072 caracteres de literales de celdas |
| Estilos | Hasta 512 estilos y 512 formatos personalizados; no se renderizan |
| Tiempo de análisis | Plazo cooperativo de 5 segundos, comprobado entre lecturas y recorridos |

Los presupuestos de memoria limitan snapshot, volumen de XML, nodos e inventario;
**no son una cuota de RSS del sistema operativo**. El overhead de objetos, parser
y buffers no equivale a los bytes XML. `tracemalloc` observó un pico de **1180572
bytes** de asignaciones Python y **0.146079 s** de recorrido total en esta ejecución;
son medidas, no topes garantizados de RAM/tiempo. El plazo no puede interrumpir
una llamada bloqueada del sistema de archivos o de una extensión C. Dos pasadas
ZIP están acotadas por separado; no se promete un sandbox de procesos hostiles.

Inspección iniciada a **2026-11-05T06:27:23.530145+00:00**. Se cotejaron hash/firma
antes y después de leer el original y el snapshot interpretado. Resultado:

| Parte ZIP | Comprimidos | Declarados = reales | CRC-32 cotejado |
|---|---|---|---|
| `[Content_Types].xml` | 351 | 1168 | `1102414c` |
| `_rels/.rels` | 244 | 588 | `233055b5` |
| `xl/workbook.xml` | 913 | 2254 | `93177b90` |
| `xl/_rels/workbook.xml.rels` | 243 | 698 | `97943e81` |
| `xl/worksheets/sheet1.xml` | 1458 | 5706 | `f08a4d9a` |
| `xl/theme/theme1.xml` | 1870 | 8390 | `be1017c1` |
| `xl/styles.xml` | 1041 | 4219 | `86a84096` |
| `xl/sharedStrings.xml` | 1033 | 2908 | `1600fbc2` |
| `docProps/core.xml` | 449 | 844 | `75874a10` |
| `docProps/app.xml` | 239 | 394 | `8b5d9b1f` |

Son **10 entradas**, todas DEFLATE, 7841 bytes comprimidos de payload y **27169
bytes reales descomprimidos**. Los 10815 bytes del archivo incluyen también
cabeceras/directorio. Expansión máxima por entrada **4.486632:1**, inferior a 100:1.
CRC y tamaños coincidieron en todas las entradas; rutas y relaciones internas
válidas para los controles aplicados. No se encontraron entradas cifradas, macros,
partes binarias o partes inesperadas entre las diez listadas. No hubo extracción
a disco, DTD/entidades admitidas, apertura de referencias externas ni ejecución.
No es una certificación exhaustiva de toda la especificación Excel/OOXML.

Se localizaron **46 cadenas compartidas**, todas referenciadas. Los 115 elementos
de celda son 63 de tipo OOXML `s` y 52 `n`; 36 de estos últimos no tienen valor.
Hay **79 literales**: 63 textos y 16 representaciones numéricas, retenidas como
cadenas sin convertir códigos ni ceros. No se aplican formatos de Excel. Se
distingue el tipo OOXML de una celda del tipo de dato que el diccionario declara
para un campo. **0 fórmulas**, **0 relaciones externas**, **0 nombres definidos**.
El diagnóstico separa fórmula/cache/literal si aparecieran; no ejecuta ninguno.

## 4. Inventario localizado: hojas y campos

Todas las referencias de esta sección heredan **archivo X84E y su SHA completo
de la sección 1**. Estado de comprobación: **contenido literal leído y cotejado
localmente**, sin autenticar emisor ni aprobar aplicación a una edición del CSV.
No se reproduce el XLSX completo en Git; el inventario técnico íntegro queda privado.

Una única hoja, nombre literal **`DiccionarioDatos`**, `sheetId="2"`, visible,
parte `xl/worksheets/sheet1.xml`. El ID 2 no significa que haya dos hojas.
Dimensión declarada **A2:F28**, **24 filas XML**, **18 con literales**: 2, 4 y 5–20.
Las filas 21 y 24–28 contienen únicamente celdas vacías/estilo; la dimensión no
equivale a 28 registros. Hay **16 definiciones**, filas 5–20, sin observaciones.
No hay celdas combinadas, objetos de tabla OOXML ni relaciones entre hojas.

A2/B2 contienen etiqueta y título del dataset con atribución SENAMHI. B2 termina
en un espacio, preservado en el inventario privado. No proporciona código de
edición, versión de producto ni correspondencia de hashes de recursos (R03/R06).
La tabla documental es A4:F20. Encabezados literales A4:F4:
`Variable`, `Descripción`, `Tipo de dato`, `Tamaño`, `Recurso relacionado`,
`Información Adicional ` (este último conserva espacio final).

En la tabla siguiente, los nombres/tipos/tamaños se transcriben sin normalizar.
Los tamaños son declaraciones de la columna D, **no resolución instrumental,
precisión decimal ni validaciones ejecutadas del CSV**. Las descripciones
abreviadas están marcadas como resumen; las comillas indican texto literal.
Las columnas C/D describen el campo del producto, no el tipo OOXML de sus celdas.

| Celda/intervalo en DiccionarioDatos | Campo literal | Descripción B, literal o resumen indicado | Tipo C / tamaño D | E/F y alcance documental | Brechas |
|---|---|---|---|---|---|
| A5:F5 | `ID` | “Identificador unico de registro” | `Numérico` / `10` | E/F vacías; no es código de estación | S01, T07 |
| A6:F6 | `ESTACION` | “Nombre de la Estación Meteorológica Automática para intercambio internacional” | `Texto` / `20` | E/F vacías; no contiene lista de estaciones o códigos | S01, S02, S06 |
| A7:F7 | `FECHA` | Resumen: fecha en que se realiza la medición en la estación automática para intercambio internacional | `Numérico` / `8` | F7: `Formato: aaaammdd` | T01, T03, T04 |
| A8:F8 | `HORA` | Resumen: hora en que se realiza la medición en la misma clase de estación | `Alfanumerico` / `6` | F8: `Formato: hhmmss` | T02–T04 |
| A9:F9 | `LONGITUD` | Resumen: distancia en grados, minutos y segundos respecto al meridiano de Greenwich (0º), eje X | `Numérico` / `20` | E/F vacías; definición en B9 sin datum/CRS ni regla de serialización | S04 |
| A10:F10 | `LATITUD` | Resumen: distancia en grados, minutos y segundos respecto al ecuador (0º), norte/sur, eje Y | `Numérico` / `20` | E/F vacías; definición en B10 sin datum/CRS | S04 |
| A11:F11 | `ALTITUD` | “Medida que indica la altura de un punto en relación al nivel medio del mar. En metros sobre nivel del mar (msnm)” | `Numérico` / `10` | E/F vacías; unidad y referencia genérica sí presentes; datum/realización no indicados | S05 |
| A12:F12 | `TEMP` | “Temperatura promedio horaria (unidad: °C)” | `Numérico` / `10` | E/F vacías | V01, T04, T05 |
| A13:F13 | `HR` | “Humedad relativa promedio horaria (unidad: %)” | `Numérico` / `10` | E/F vacías | V02, T04, T05 |
| A14:F14 | `PP` | “Precipitación total horaria (unidad: milimetros por hora)” | `Numérico` / `10` | E/F vacías; conservar unidad literal | V03, T04, T05 |
| A15:F15 | `RED` | “Estaciones pertenecientes a la Red Global de Observación Basica (GBON, por sus siglas en ingles) o Red Regional de Observación Básica (RBON, por sus siglas en ingles)” | `Texto` / `4` | E/F vacías; define siglas, no membresía individual vigente | S03 |
| A16:F16 | `DEPARTAMENTO` | Resumen: departamento de ubicación de la estación automática para intercambio internacional | `Texto` / `20` | E16: `Catálogo del INEI` | S04, S08 |
| A17:F17 | `PROVINCIA` | Resumen: provincia de ubicación de la misma clase de estación | `Texto` / `20` | E17: `Catálogo del INEI` | S04, S08 |
| A18:F18 | `DISTRITO` | Resumen: distrito de ubicación de la misma clase de estación | `Texto` / `25` | E18: `Catálogo del INEI` | S04, S08 |
| A19:F19 | `UBIGEO` | “Código de ubicación geográfica donde se encuentra ubicada la Estación Meteorológica Automática para intercambio internacional” | `Alfanumerico` / `6` | E19: `Catálogo del INEI`; sin edición, URL o correspondencias | S08 |
| A20:F20 | `FECHA_CORTE` | “Día en que se generó el dataset” | `Numérico` / `8` | F20: `Formato: aaaammdd` | T06, R03, R04 |

E16:E19 son **menciones textuales**, no enlaces consultados ni un catálogo INEI
verificado. E5:E15 y E20 están vacías; F solo tiene literales en F7/F8/F20.
No se hallaron notas metodológicas adicionales fuera de estos textos en las
79 celdas con valor; todas las cadenas compartidas están usadas. Este alcance
de ausencia se refiere a **este documento**, no a los recursos de SENAMHI en general.

### Procedencia y fechas internas

En `docProps/core.xml`, `created` declara `2021-07-05T17:23:13Z` y `modified`
`2024-05-31T20:33:08Z`; `revision` no contiene valor. En `docProps/app.xml`,
`Application` dice `Microsoft Excel Online` y `AppVersion` `16.0300`.
Son propiedades técnicas editables del contenedor, **no una versión/fecha editorial
autenticada, vigencia o fecha de publicación** (R04/V08). Los nombres personales
de autor/último editor no se publican; solo se conserva su presencia. El título
en B2 atribuye SENAMHI; no constituye prueba independiente de autoría (R06).
Versión editorial y vigencia permanecen desconocidas, sin sustituirlas por la
versión `0.1.0` del diagnóstico o por fechas de adquisición/inspección.

## 5. Estaciones, tiempo y variables: interpretación acotada

**Estaciones.** B5 diferencia registro de estación; B6 ofrece el nombre del campo,
sin un solo código institucional o padrón de estaciones. No se crean identidades
físicas ni relaciones entre homónimos. B15 explica las redes GBON/RBON, sin ficha
de membresía/época. B9/B10 describen ejes X/Y y referencia geográfica genérica,
pero no un CRS/datum, precisión ni enlace a instalación. Su mención de grados,
minutos y segundos requiere aclarar la serialización frente a los decimales del
perfil histórico; no se demuestra otra contradicción numérica ni se convierte nada.
B11 aporta **msnm y nivel medio del mar**; no identifica datum vertical realizado,
método, incertidumbre o vigencia. No hay operación, traslados, sensores o calibración.

**FECHA/HORA.** B7/F7 definen fecha de medición y `aaaammdd`; B8/C8/D8/F8 declaran
hora de medición, `Alfanumerico`, tamaño `6`, `hhmmss`. No explican cinco posiciones,
horas especiales o incompletas, zona, cambios de reloj, inicio/cierre o inclusividad.
Se conserva la discrepancia con los conteos **históricos**, no recalculados, del
[84-D](auditoria_metadatos_pnda_paso84d.md): 170400 representaciones de cinco
caracteres y 245873 de seis. No se rellenan ceros ni se asigna UTC/UTC−5.
El tamaño D no especifica por sí solo tolerancia o algoritmo de reparación.

**FECHA_CORTE.** B20/F20 aportan semántica documental y formato: día de generación
del dataset. Esto mejora T06, pero no establece cuándo se publicó/revisó el CSV,
su correspondencia exacta de ediciones o cómo se fija una observación horaria.
No se confunde con FECHA, adquisición RAW, inspección o instante de publicación.
El literal histórico `20240630` no se leyó ni reinterpretó en este paso.

**TEMP/HR/PP.** Las filas 12–14 declaran tipo numérico, tamaño 10 y periodicidad
horaria; TEMP y HR dicen promedio, PP total. Las unidades literales son `°C`, `%`
y **`milimetros por hora`**. No hay muestreo, ponderación, completitud de ventana,
centinelas, tratamiento de errores, resolución/rango de sensor, incertidumbre,
nivel de procesamiento o controles efectivamente aplicados al producto. La
expresión de PP requiere aclaración entre total e intensidad; no prueba por sí
sola una incompatibilidad física ni se corrige a mm/mm/h. “Horaria” no demuestra
cadencia instrumental, publicación, continuidad o ventanas alineadas. Los vacíos
de metadatos en el XLSX no son una política de vacíos del CSV. No se incorporan
rangos, banderines ni niveles del manual a estas variables.

**UBIGEO.** C19/D19/E19 confirman alfanumérico, seis y referencia genérica INEI.
Continúa la discrepancia representacional histórica con sufijo `.0` y longitudes
7/8 del CSV; no se demuestra causa, código falso, catálogo aplicable ni geocodificación.
No se recorta, completa o reconstruye UBIGEO.

## 6. Brechas e impacto sobre los contratos

La [matriz nueva](brechas_diccionario_pnda_paso84e.md) mantiene 29 IDs y el estado
anterior literal del 84-D. Estados propuestos: **1 RESUELTA_CON_EVIDENCIA**
(R01, conservación y localización del XLSX exclusivamente), **13 PARCIALMENTE_DOCUMENTADA**,
**12 PENDIENTE_DE_EVIDENCIA**, **2 CONTRADICCIÓN_DOCUMENTADA** (S08/T02) y
**1 NO_EVALUABLE** (R02, DOCX no inspeccionado). Quedan **28 sin resolver**;
parcial no equivale a permiso, verificación científica o cierre de toda la propiedad.
La vigencia, autenticidad, ediciones y licencia siguen pendientes. R01 no cierra
R02 ni certifica conservación de todo auxiliar posible.

| Clase de metadato | Incorporación futura posible, sujeta a revisión |
|---|---|
| Listo como **declaración documental localizada** | Identificadores de campos, descripciones/tipos/tamaños; unidades literales y promedio/total horario; definición de RED; altitud msnm genérica; FECHA_CORTE como día de generación. Conservar archivo/hash/celda y edición desconocida |
| Disponible pero ambiguo | PP total frente a unidad por hora; semántica y ventana horaria; serialización espacial frente a definición DMS; aplicación del XLSX a cada edición CSV; referencia vertical sin realización |
| Contradictorio en representación histórica | HORA de cinco/seis posiciones frente a tamaño/formato declarado; UBIGEO frente a seis caracteres. Conservar ambas evidencias, sin reparación |
| No presente suficientemente | Código/padrón/identidad física y vigencia de estación, CRS, zona horaria, instrumentos, faltantes, procesamiento/QC e historial de definiciones |
| Necesita confirmación institucional | Correspondencias/ediciones, significado y causas de las discrepancias, aplicabilidad por estación/período, condiciones de uso y metrología |

No se demostró incompatibilidad nueva que exija cambiar los contratos públicos.
`VariableCatalogo` puede conservar descripción, unidad/frecuencia/tipo **declarados**,
procedencia y `version_diccionario=None`; la cadena PP no se normaliza.
`ProcedenciaCatalogo` puede citar este expediente/hash/celdas, sin marcar vigencia
o autenticidad por haber leído una celda. `EstacionCatalogo` no adquiere un código
por la definición del campo ESTACION ni representa por separado unidad/datum
vertical y todas sus vigencias. B11 debe mantenerse como afirmación documental,
sin insertar clandestinamente unidad en un campo numérico de altitud.

`adaptar_catalogo`/`adaptar_meteorologia` y el evaluador existentes se reutilizarían
posteriormente; no se invocaron para recalcular el piloto. Los límites del 84-D
siguen vigentes: `DisponibilidadCatalogo` exige datetime y `PeriodoTemporal` admite
date; no se inventa medianoche para adaptar cobertura civil. La selección automática
de fichas por época, reconciliación de identidad y verificación por propiedad
no se resuelven con este diccionario. Nuevos respaldos requieren composición
explícita, evidencia suficiente y revisión. Los resultados espaciales/temporales
históricos `PENDIENTE_DE_EVIDENCIA` del 84-C permanecen intactos.

## 7. Verificación, seguridad y cierre

Se crearon únicamente los cuatro archivos del repositorio enlazados al inicio.
Los dos módulos nuevos son diagnóstico y pruebas aislados, no un lector de
observaciones ni script de producción. Ningún módulo estable, contrato, fixture,
dependencia, configuración, `main.py` o `.gitignore` se modifica.

Pruebas ejecutadas con Python de `.venv`, sobre libros ficticios y temporales:

```powershell
$env:PYTHONPATH="$aux\guardia;$PWD\src;$PWD\tests;$PWD"
$env:SPICA_84C_AUDIT="$aux\auditoria"
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -B -m unittest test_diagnostico_xlsx_84e test_verificacion_formatos -v
```

`$aux` fue la carpeta temporal de guardia ya preparada para 84-C,
`C:\Users\Propietario\AppData\Local\Temp\spica-paso84c-398b9bf12b9e4e5a9e832bdd420f634f`;
no es un dato operativo ni una dependencia del diagnóstico. Una ejecución posterior
puede utilizar únicamente `src;tests;raíz` en PYTHONPATH para estos fixtures aislados.
La guardia del ensayo niega recursos reales y conexiones; los temporales de tests
se crean y limpian aparte, nunca en staging operativo.

Resultado: **63 pruebas en 3.273 s, todas aprobadas, 0 fallidas y 0 errores**:
**12 nuevas** del diagnóstico y **51 existentes** de verificación de formatos.
Incluyen texto/códigos/estilos sin conversión, fórmulas/cache, referencias externas,
DTD/entidades/profundidad, rutas/cifrado/macros/CRC, expansión/volumen, índices,
límites de inventario/plazo, privacidad, ausencia de I/O en el análisis de bytes
y conservación física del archivo ante errores. Son controles técnicos, sin
declarar conformidad científica. No se repitió la suite completa ni `pip check`:
**1431 aprobadas** es el antecedente del 84-C; no se presenta **1443** como suite
completa ejecutada en 84-E. No se añaden dependencias.

Las lecturas reales y la preservación usaron guardia puntual que rechaza sockets,
subprocesos, cualquier conexión SQLite, acceso al árbol `SPICA_DATOS`, escritura
fuera de la evidencia privada y acceso a otros archivos del piloto temporal.
Contadores de intentos de conexión/SQLite/escritura operativa: **0/0/0**. La
ejecución no accedió a RAW/staging/SQLite operativos; por no abrirlos no se calcula
ni afirma aquí una nueva huella de esos almacenes ni se auditan cambios de terceros.
Solo se lee el XLSX autorizado. Los informes no publican autores personales,
destinos externos, credenciales ni cuerpos de observaciones.

Comprobación física final a **2026-11-05T06:36:49.433247+00:00**: original y copia
siguen siendo archivos regulares sin enlaces, de **10815 bytes**, con el mismo
SHA-256 X84E. La carpeta privada contiene exactamente los tres archivos previstos,
sin `.part`. No se borró o sustituyó el original. Las verificaciones de los cuatro
archivos nuevos comprueban UTF-8, sintaxis Python mediante AST/compilación en memoria,
nombres superiores sin duplicación, finales de línea y ausencia de espacios finales.
Se cotejan **29 estados anteriores literales**, los cinco estados propuestos,
**10 tablas**, **15 enlaces locales**, incluidas **2 anclas**, y los campos/partes
citados contra el inventario privado. Las URL históricas se revisan solo como texto.

`git diff --check`, diff de archivos registrados e índice terminan con código 0,
sin salida. Los archivos nuevos se revisan directamente porque no aparecen en el
diff de archivos registrados. Rama/HEAD se conservan y el estado final es:

```text
?? docs/brechas_diccionario_pnda_paso84e.md
?? docs/inspeccion_diccionario_pnda_paso84e.md
?? herramientas/inspeccionar_xlsx_84e.py
?? tests/test_diagnostico_xlsx_84e.py
```

No se efectúan migraciones, GET, descargas, consultas institucionales, QA/QC
científico, commits o push. El DOCX sigue sin adquisición local acreditada.
La consulta propuesta está en la matriz; no se envía.

**Dictamen: APTO CON RESTRICCIONES.** Se conserva y localiza evidencia para
descripciones declaradas futuras. La incorporación operativa, equivalencia de
estaciones, interpretación temporal completa, conversiones y uso científico
requieren evidencia y revisión adicionales. No se avanza a esas operaciones.
