# PASO 66 — Comprobación estructural acotada de XLSX y CSV

SUADC-05 añade `spica.adquisicion.verificacion`, independiente de HTTP, SQLite y
los modelos científicos. Solo usa biblioteca estándar. No transforma los datos,
no ejecuta contenido de documentos y no crea archivos auxiliares ni extrae ZIP.

## API y resultados

`verificar_archivo(ruta, *, formato_declarado=None, tipo_medio_sugerido=None,
nombre_sugerido=None, codificacion=None, delimitador=None,
encabezado_declarado=None, politica=None)` abre un archivo regular en modo lectura.
Rechaza symlinks/junctions en sus componentes y comprueba identidad/tamaño/mtime
antes y después de inspeccionar. Requiere directorios controlados: estas comprobaciones
no sustituyen aislamiento frente a un atacante con escritura concurrente.

`ResultadoEstructura` separa formato declarado, sugerencias de extensión y HTTP,
formato/tipo de medio identificados, fecha UTC, tamaño, bytes leídos/descomprimidos,
alcance completo, comprobaciones realizadas, diagnósticos y política aplicada.
`DetalleCSV` conserva codificación, BOM, delimitador y conteos técnicos, sin copiar
encabezados o valores de celdas. Los nombres de archivo, URLs y errores originales
no forman parte del resultado. Las sugerencias se reducen a etiquetas conocidas.

| Estado | Significado |
| --- | --- |
| COMPATIBLE | Estructura reconocida y coincidente con el formato declarado |
| INCOMPATIBLE | Se reconoce otro formato; no es el recurso documental declarado |
| SIN_DECLARACION | Formato reconocido sin declaración con la cual compararlo |
| NO_RECONOCIDA | No se identifica un formato admitido o la política rechaza su contenido |
| INCIERTA | Faltan pruebas suficientes, por ejemplo de codificación o delimitador |
| INCOMPLETA | Los límites o el alcance técnico impiden completar la inspección |
| ILEGIBLE_O_CORRUPTA | No se puede leer el archivo o se detectan incoherencias pertinentes de ZIP/XML/CSV |

`utilizable_documentalmente` solo es verdadero para XLSX/CSV COMPATIBLE con alcance completo.
Reconocer ZIP, DOCX, HTML o JSON para distinguir respuestas inesperadas no amplía
el conjunto de formatos habilitados para uso documental en esta etapa.
La palabra «utilizable» se refiere a este contrato estructural básico: no certifica
un libro semánticamente correcto ni datos científicamente válidos. HTML se identifica
mediante firma textual, sin abrirlo; no se promete validar toda su sintaxis. JSON
se reconoce si la muestra contiene un documento completo con sintaxis válida.

## XLSX y contenedores

Antes de construir `ZipFile`, se comprueban el fin del ZIP, los rangos del directorio
central, su volumen y su número real de registros. No se confía únicamente en el
contador declarado: un contador falsificado no evita los límites de memoria.

Después se comprueban nombres originales/normalizados, duplicados y alias,
componentes `..`, rutas absolutas, barras inversas, autoridades Windows/ADS,
controles y escapes sospechosos. No se admiten entradas de enlaces ni dispositivos,
cifrado, ZIP multivolumen o métodos distintos de almacenamiento y DEFLATE. ZIP64
se devuelve incompleto, sin intentar su procesamiento. Los rangos locales no deben
solaparse ni alcanzar el directorio central.

Se leen todas las entradas admitidas por bloques, comprobando CRC mediante ZipFile,
tamaños reales y presupuesto descomprimido. Para OOXML se comprueban:

- `[Content_Types].xml`, tipos por parte y referencias a componentes existentes.
- Relación principal `_rels/.rels` y su destino local.
- `xl/workbook.xml`, namespace, hojas e identificadores de relaciones.
- `xl/_rels/workbook.xml.rels` y sus destinos de hojas, tipos de contenido y raíces XML.
- Coherencia básica de los demás `.rels` y buena formación de los XML del paquete.

Solo se conserva un árbol pequeño para XML de control. Las hojas se analizan por
eventos y se descarta su texto: no se crea un árbol de celdas. Expat rechaza DTD y
entidades, también si el XML usa UTF-16. Se acotan profundidad, nodos y bytes
pendientes para evitar acumular atributos o tokens gigantes. No se resuelven
recursos externos: referencias externas opcionales producen el diagnóstico
`relaciones_externas_no_abiertas`. Una parte principal/hoja externa no satisface
los requisitos de un libro local comprobado.

DOCX se distingue por sus componentes, tipo principal, relación y raíz Word; no se
implementa una validación completa de DOCX. Un ZIP genérico no es XLSX. Macros
reconocibles y tipos de hoja fuera del subconjunto admitido no se avalan como XLSX
utilizable. Nunca se ejecutan macros, fórmulas, scripts, consultas o vínculos.
La ausencia de marcadores conocidos no es un análisis antivirus.

## CSV conservador

Se lee una muestra de bytes limitada, no todo un archivo grande. Un archivo solo
se declara compatible si se inspeccionó completo dentro de los presupuestos y se
observaron al menos dos registros de dos o más campos con anchura regular.
Un CSV de una columna, solo encabezado o vacío queda incierto.

Se reconocen BOM UTF-8/16/32. Sin BOM, ASCII se identifica como subconjunto probado;
texto no ASCII compatible con UTF-8 mantiene incertidumbre si nadie declaró su
codificación. No se adivina Latin-1 ni CP1252. El llamador puede proporcionar una
codificación de la lista explícita admitida. Un BOM contradictorio no se ignora.
La decodificación es estricta e incremental para no confundir un corte de muestra
en medio de un carácter con corrupción del archivo completo.

Se prueban coma, punto y coma, tabulador y barra vertical, sin preferir una coma.
Si varios delimitadores producen estructuras regulares, se devuelve incertidumbre;
el llamador puede declarar uno. `csv.reader(strict=True)` y una comprobación
conservadora de comillas examinan campos escapados, CRLF/LF y campos multilínea.
No se aceptan comillas literales en campos sin entrecomillar ni anchuras variables.
Filas vacías intercaladas pueden impedir esta comprobación conservadora.

Un corte por muestra o registros produce INCOMPLETA, aunque termine dentro de un
campo entrecomillado. Los nulos/controles binarios se detectan después de decodificar,
permitiendo los bytes nulos propios de UTF-16/32 con BOM. HTML/JSON inesperados no
se confunden con CSV. No se infiere que la primera fila sea un encabezado: su estado
solo procede de `encabezado_declarado`; se informa el conteo de campos inicial.
No se comprueban columnas GBON/RBON, fechas, unidades, estaciones ni zonas horarias.

## Límites por defecto

| Recurso | Límite |
| --- | ---: |
| Entradas ZIP / directorio central | 512 / 2 MiB |
| Total descomprimido / una entrada | 64 MiB / 16 MiB |
| Relación de expansión por entrada | 100:1 |
| XML de control / XML pendiente de análisis | 512 KiB / 64 KiB, con un bloque de detección |
| Nodos XML, sumados en el paquete / profundidad | 20 000 / 64 |
| Muestra CSV | 256 KiB, más un byte para detectar el corte |
| Registros CSV / campos por registro / caracteres por campo | 1000 / 1024 / 65 536 |
| Bloque de lectura | 64 KiB |

`PoliticaEstructura` es inmutable y configurable con valores positivos. Existen
topes de configuración para las asignaciones principales: directorio 16 MiB,
XML de control 4 MiB, muestra CSV 8 MiB y bloque/XML pendiente 1 MiB. Las lecturas
de metadatos ZIP están también acotadas. El límite global `csv.field_size_limit`
del intérprete no se cambia; si es más restrictivo puede impedir completar una
inspección. No se ha implementado un plazo máximo de CPU ni aislamiento de proceso.

## Integración y política de conservación

`InformeDescarga` añade `tipo_medio_sugerido` opcional. Solo conserva MIME conocidos,
sin parámetros ni encabezados arbitrarios. No cambian solicitudes, límites HTTP,
orígenes, TLS, redirecciones, streaming ni reintentos. HTTP 200 y Content-Type no
confirman el formato.

`AdaptadorHTTPRAW` recibe opcionalmente `politica_estructura`. Reutiliza la misma
descarga, incorporación y recuperación física; después inspecciona el archivo RAW
de solo lectura y devuelve `ResultadoHTTPRAW.estructura`. La fase COMPLETADA sigue
describiendo la transferencia/incorporación, no la aceptación documental. El
resultado estructural puede ser negativo sin convertir una transferencia íntegra
en fallo de integridad física.

**Política elegida: conservar respuestas inesperadas como evidencia RAW**, con su
procedencia, licencia conocida, adquisición, activo, tamaño y SHA-256 anteriores.
No se transforma, sobrescribe ni elimina el original para solucionar una discrepancia.
El consumidor debe consultar `utilizable_documentalmente` y el informe estructural
antes de usarlo como documento del formato declarado. La retención y el acceso a
una respuesta inesperada corresponden al almacén privado y a la revisión del operador.

`AdquisicionPNDA` expone `estructura` y `utilizable_documentalmente`. Su capacidad
HTTP comprobada solo acredita esa transferencia; la procedencia técnica informa
también el estado estructural. No se promociona a una capacidad científica ni a
todos los recursos del producto. Su validación científica permanece desconocida.
El piloto mantiene sus roles autorizados y su límite de 1 MiB; no adquiere el CSV.

No cambia SQLite, el JSON documental ni los modelos científicos. `media_detected`
de MD-03 continúa desconocido: el nuevo tipo identificado pertenece al informe
estructural. Dicho informe se devuelve en memoria y **no se persiste todavía**.
Tras reabrir RAW se conserva la evidencia anterior y se puede repetir la inspección;
no se debe reconstruir un éxito estructural a partir de la extensión o del hash.

## Alcance comprobado y pendientes

Las pruebas nuevas usan unittest, archivos sintéticos, directorios temporales y
MockTransport. Incluyen ZIP corrupto/truncado, CRC erróneo, DOCX, HTML, JSON, rutas
hostiles, enlaces ZIP, contadores falsos, bombas de expansión, DTD/XXE, tokens XML
grandes, macros, XML incoherente, CSV ambiguo/malformado y conservación de originales.
Dos casos de aproximadamente 2 y 4 MiB verifican lectura acotada y un pico de asignaciones
Python inferior a 8 MiB en esos escenarios; no es una garantía de RAM universal.

Quedan pendientes validación OOXML semántica/XSD, todas las variantes de libros,
CSV completo por streaming más allá de la muestra, otros formatos, persistencia
versionada del informe, caducidad de comprobaciones y aislamiento/plazos de CPU.
No hay autenticidad institucional, firma oficial, evaluación de fórmulas ni calidad
científica demostrada. Los mocks no prueban la disponibilidad de SENAMHI.

## Cierre y verificación

Estado inicial: árbol limpio, rama `feature/suadc-http`, commit `1730ef7`.
Estado final: misma rama/commit, siete archivos modificados y ocho nuevos. No hubo
commits ni push. No se modificaron modelos científicos, catálogos SQLite, contratos
de integridad, `main.py`, `.gitignore`, `.venv` ni dependencias.

Archivos nuevos:

- `src/spica/adquisicion/verificacion/__init__.py`
- `src/spica/adquisicion/verificacion/modelos.py`
- `src/spica/adquisicion/verificacion/inspector.py`
- `src/spica/adquisicion/verificacion/_xlsx.py`
- `src/spica/adquisicion/verificacion/_csv.py`
- `tests/test_verificacion_formatos.py`
- `tests/test_integracion_formatos.py`
- `docs/verificacion_formatos.md`

Archivos modificados:

- `src/spica/adquisicion/transportes/descargas.py`
- `src/spica/adquisicion/integracion/http_raw.py`
- `src/spica/adquisicion/conectores/senamhi/modelos.py`
- `src/spica/adquisicion/conectores/senamhi/pnda.py`
- `docs/conector_senamhi_pnda.md`
- `docs/integracion_http_raw.md`
- `docs/registro_evidencias.md`

Entorno comprobado con `.venv`: Python 3.15.1, HTTPX 0.28.1 y SQLite 3.53.4.
La suite base aprobó 481 pruebas antes de adaptar los componentes existentes.
La suite final incluye 51 pruebas nuevas de formatos y 11 de integración:

```text
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
Ran 543 tests in 50.320s
OK

.\.venv\Scripts\python.exe -B -m pip check
No broken requirements found.

git diff --check
Código de salida 0; sin errores de espacios.
Git avisa de futura conversión LF a CRLF en archivos modificados.

git status --short
 M docs/conector_senamhi_pnda.md
 M docs/integracion_http_raw.md
 M docs/registro_evidencias.md
 M src/spica/adquisicion/conectores/senamhi/modelos.py
 M src/spica/adquisicion/conectores/senamhi/pnda.py
 M src/spica/adquisicion/integracion/http_raw.py
 M src/spica/adquisicion/transportes/descargas.py
?? docs/verificacion_formatos.md
?? src/spica/adquisicion/verificacion/
?? tests/test_integracion_formatos.py
?? tests/test_verificacion_formatos.py
```

Resultado final: **543 aprobadas, 0 fallidas, 0 con errores**. Las pruebas negativas
comprueban estados y diagnósticos esperados; su aprobación no significa aceptar los
archivos deliberadamente incorrectos. No hubo avisos de recursos abiertos en la
ejecución final.

Dictamen: **APTO CON RESTRICCIONES**, para inspección estructural experimental con
los límites anteriores. No se accedió ni modificó el RAW permanente o su staging,
no se descargaron recursos reales, no hubo conexiones externas ni instalaciones,
y no se ejecutaron migraciones. La adquisición del CSV GBON/RBON y la siguiente
etapa permanecen pendientes de revisión del usuario.
