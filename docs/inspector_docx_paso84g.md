# PASO 84-G: inspector seguro DOCX offline

Fecha: **2026-11-05**. Dictamen: **APTO CON RESTRICCIONES** para el perfil local
implementado y su revisión. No autoriza adquirir el DOCX institucional ni integra
HTTP/RAW. Un documento validado dentro del alcance no acredita autenticidad,
vigencia, equivalencia de ediciones o corrección científica.

## 1. Estado inicial y arquitectura

Git comenzó limpio en `feature/suadc-http`, HEAD **`3ce6443`**,
`SUADC: preparacion de metadatos DOCX PNDA`. El 84-F está registrado. Se revisaron
los expedientes [84-D](auditoria_metadatos_pnda_paso84d.md),
[84-E](inspeccion_diccionario_pnda_paso84e.md) y
[84-F](preparacion_docx_pnda_paso84f.md), su
[protocolo propuesto](protocolo_docx_pnda_paso84f.md) y los controles ZIP/XML,
evidencias y referencias existentes. Entorno comprobado: Python **3.15.1** de
`.venv`, HTTPX **0.28.1**. No se necesita HTTPX para este componente.

Se añade el subpaquete `spica.adquisicion.verificacion.docx` sin modificar la API
del verificador anterior, su criterio `utilizable_documentalmente`, transporte,
RAW, catálogo o contratos científicos. Los contratos DOCX son nuevos y locales.
La importación en un proceso nuevo no carga HTTPX, SQLite, transportes, integración
o almacenamiento. No depende de scripts de `herramientas`.

| Archivo nuevo | Responsabilidad |
|---|---|
| [__init__.py](../src/spica/adquisicion/verificacion/docx/__init__.py) | Exportaciones explícitas del nuevo subpaquete |
| [modelos.py](../src/spica/adquisicion/verificacion/docx/modelos.py) | Contratos inmutables y política validada de límites |
| [inspector.py](../src/spica/adquisicion/verificacion/docx/inspector.py) | API bytes/archivo autorizado, SHA, conservación y resultados estructurados |
| [_control.py](../src/spica/adquisicion/verificacion/docx/_control.py) | Plazo, cancelación, lectura ZIP y presupuestos contables |
| [_paquete.py](../src/spica/adquisicion/verificacion/docx/_paquete.py) | Perfil de partes/MIME, relaciones, grafo y reutilización de verificadores |
| [_extraccion.py](../src/spica/adquisicion/verificacion/docx/_extraccion.py) | Texto, estilos, tablas, propiedades y localizadores Clark |
| [test_inspector_docx.py](../tests/test_inspector_docx.py) | Fixtures OOXML generados y pruebas adversariales, sin documentos reales |
| Este informe | Arquitectura, garantías, pruebas, límites y condiciones futuras |

La infraestructura reutilizada es
[`verificacion/_xlsx.py`](../src/spica/adquisicion/verificacion/_xlsx.py):
`_directorio_previo`, `inspeccionar_zip`, `_XML`, `_tipos` y `_relaciones`, más
[`PoliticaEstructura`](../src/spica/adquisicion/verificacion/modelos.py).
No se copia su parser ni se cambia su comportamiento histórico. Se configura
su Expat existente para retener datos de texto y rechazar instrucciones XML;
sus callbacks rechazan DTD, declaraciones de entidades y resolución externa.
Los visitantes del árbol son extracción estructural, no otro parser XML.
Los helpers son privados: futuras modificaciones requieren regresiones.

El lector físico nuevo es mínimo y específico de esta API. Evita una dependencia
de producción hacia el arnés 84-C, que también importa SQLite y almacenamiento;
conserva los controles de firma/descriptor/huella y agrega raíz explícita. No se
implementa otro transporte, almacén o reconciliador de evidencia.

## 2. API y contratos públicos

Importación explícita, sin modificar exportaciones históricas:

```python
from spica.adquisicion.verificacion.docx import (
    LimitesDOCX, inspeccionar_docx_bytes, inspeccionar_docx_archivo,
)
```

`inspeccionar_docx_bytes(datos: bytes, *, identificador="memoria", limites=None,
cancelacion=None, reloj=time.monotonic)` recibe exclusivamente un snapshot bytes
inmutable. Rechaza tipos de entrada no admitidos, verifica longitud antes de
procesar y calcula SHA-256 por bloques. La memoria que el llamador ya hubiese
asignado a una entrada excesiva no puede desasignarse desde esta función.
No abre archivos y no denomina físico a un hash calculado solo sobre bytes.

`inspeccionar_docx_archivo(ruta: Path, *, directorio_autorizado: Path,
identificador="archivo_local", tamano_esperado=None, sha256_esperado=None,
limites=None, cancelacion=None, reloj=time.monotonic)` exige ruta/raíz absolutas,
archivo regular estrictamente dentro de esa raíz y componentes sin enlaces,
junctions/reparse points, `..`, ADS, dispositivos Windows o terminaciones inseguras.
Se inspeccionan ancestros antes de la hoja para evitar atravesar un enlace
ya presente. El llamador debe autorizar la lectura del archivo exacto: suministrar
una ruta no autentica una autorización institucional.

Los valores esperados son opcionales y se cotejan cuando se aportan; su presencia
no se inventa para una adquisición desconocida. Los errores de argumentos/política
producen TypeError/ValueError con códigos fijos. Los fallos de archivo/paquete,
límites y cancelación producen resultados estructurados sin mensajes internos.

| Contrato | Contenido y alcance |
|---|---|
| `IdentidadDOCX` | Identificador lógico neutro del llamador, origen memoria/archivo, tamaño y SHA medido o `None` si no se pudo completar. No crea asset_id o identidad de estación |
| `ResultadoDOCX` | Estado, identidad, límites, partes, relaciones, párrafos, tablas, propiedades, advertencias, rechazos, omisiones, conservación, consumo y versión del inspector `0.1.0` |
| `ParteDOCX` | Nombre del perfil, MIME, bytes comprimidos/declarados/observados y CRC. Solo se publican estas observaciones tras la pasada completa compartida de CRC/tamaños; pueden ser parciales respecto al inventario del perfil si luego se detiene |
| `RelacionDOCX` | Parte .rels, ID original acotado, tipo admitido y destino interno. Nunca se devuelve un destino externo no admitido |
| `ReferenciaDOCX` | Archivo/hash, parte, ruta Clark con índices, ordinal de párrafo, tabla, fila y celda cuando correspondan |
| `ParrafoDOCX` | Referencia, texto, origen cuerpo/encabezado/pie/nota, estilo original y reconocimiento de título por estilo |
| `TablaDOCX`, `FilaDOCX`, `CeldaDOCX` | Referencias, filas/celdas, párrafos canónicos, tablas anidadas y literales gridSpan/vMerge; sin renderizar grilla |
| `PropiedadDOCX` | Nombre, valor y localizador; naturaleza explícita de propiedad técnica editable, sin convertirla en vigencia editorial |
| `DiagnosticoDOCX` | Código fijo y localizador seguro opcional; sin reproducir rutas locales, XML, excepciones, destinos o credenciales |
| `ConsumoDOCX` | Lecturas de preflight y ambas pasadas, descompresión por pasada, XML/nodos de extracción y pico auxiliar contable |

`diagnostico_publico()` devuelve exclusivamente estado/versión, tamaño/hash,
conteos y códigos. El resultado completo contiene texto documental privado;
no debe volcarse íntegramente en logs/Git o tratarse como HTML/Markdown confiable.
La API no escribe ni serializa informes. Una exportación futura deberá escapar
el contenido y aplicar el presupuesto JSON del 84-F, antes de persistirlo.

### Estados inequívocos

| Estado | Significado |
|---|---|
| `DOCUMENTO_VALIDADO_EN_ALCANCE` | Terminó el perfil admitido y su extracción prevista sin rechazos o incertidumbres bloqueantes. No significa seguridad absoluta o contenido científicamente correcto |
| `DOCUMENTO_RECHAZADO` | Paquete/estructura incoherente, contenido prohibido/no admitido, acceso o integridad fallidos. Sin texto, tablas o propiedades promovidos desde un recorrido abortado |
| `INSPECCION_INCOMPLETA` | Cancelación/plazo/presupuesto o parte semánticamente no interpretable. No se declara completitud; campos/revisiones/extensiones omiten toda su parte textual. Otras partes seguras pueden conservarse con ese estado |

Un rechazo ya demostrado no se reemplaza por mera cancelación si la comprobación
física final no pudo ejecutarse: se conserva la causa y se añade la omisión.
Una falla física final descarta los fragmentos. Los inventarios de partes/relaciones
ya comprobados no convierten un resultado rechazado/incompleto en válido.
Las marcas son informes del procedimiento, no autorizaciones o certificados.

## 3. ZIP, XML y contenido admitido

Secuencia implementada:

1. Snapshot acotado y SHA; firma ZIP inicial, preflight compartido del directorio
   antes de construir ZipFile; componentes esenciales y cantidad XML.
2. Perfil cerrado de nombres, flags y extras. Coherencia adicional entre cabeceras
   locales y central, incluidos nombres/método/tamaños cuando no hay descriptor.
3. Pasada compartida completa: rangos/solapamientos, rutas/alias, tipo de entrada,
   cifrado/método, expansión, bytes realmente descomprimidos, CRC y XML.
4. Pasada DOCX: tipos de contenido, relaciones internas y grafo alcanzable,
   raíces de partes y detección de actividad antes de aceptar su extracción.
   Se procesa un árbol por contexto, liberando sus referencias antes del siguiente.
5. Comprobación final de presupuesto/cancelación y, para archivos, reapertura y
   huella/firma posterior. El original solo se abre `rb`; no se extrae ZIP a disco.

Se rechazan ZIP inválidos/truncados, CRC/tamaños inconsistentes, duplicados exactos
o ambiguos, rutas inseguras, enlaces/archivos especiales, cifrado, métodos distintos
de STORED/DEFLATED, ZIP64/multivolumen, partes incrustadas/anidadas, macros/VBA,
ActiveX/OLE, scripts/plantillas/altChunk y partes/MIME fuera del perfil. Los datos
se leen con ZipFile, sin `extract`/`extractall` o ejecución de contenido.

El DOCX debe ser Transitional: MIME principal
`application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml`,
`_rels/.rels` coherente y raíz `word/document.xml` en
`http://schemas.openxmlformats.org/wordprocessingml/2006/main`.
Una extensión, MIME HTTP, firma PK o ausencia de macros por sí solos no bastan.
No se implementa validación exhaustiva XSD de toda la norma OOXML.

| Parte admitida | Comprobación y tratamiento |
|---|---|
| `[Content_Types].xml`, relaciones | Tipos declarados coherentes; IDs únicos, principal única, destinos existentes y alcanzables, tipos de relación permitidos |
| `word/document.xml` | Cuerpo único; estructura textual mínima coherente y extracción literal |
| `word/styles.xml`, settings/fontTable/webSettings/numbering | MIME/raíz definidos en el perfil; sin ejecutar formato, herencia o numeración. Ambigüedad global de estilos/settings omite texto de todas las partes |
| `word/headerN.xml`, `word/footerN.xml` | Nombre/MIME/raíz/relación coherentes; se extrae cada parte una vez, sin decidir dónde se vería en páginas/secciones |
| `word/footnotes.xml`, `word/endnotes.xml` | Notas por ID literal, referencias y párrafos; separadores no interpretados |
| `word/comments.xml` | Presencia/estructura comprobadas; comentarios no extraídos y resultado incompleto |
| `docProps/core.xml`, app/custom | Raíz/tipo definidos; solo propiedades técnicas seleccionadas. Autor/último editor y otros datos no se publican. Propiedades custom no reconocidas quedan omitidas |
| `word/theme/themeN.xml` | Tema pasivo, sin renderizar. El perfil de nombres exacto está en `_paquete.py` |
| `word/media/imageN.png/jpg/jpeg` | MIME y firma básica, tamaño y CRC; no decodificar, renderizar, OCR o extraer afirmaciones. No se certifica el formato gráfico completo ni se descarta todo posible políglota |

**Toda relación External bloquea**, incluso un hipervínculo legítimo. Se detiene
sin resolver su URL o publicar el destino. Relajar el perfil requiere revisión,
no una repetición automática de descarga. Los fragmentos URI en relaciones también
están fuera del perfil. Las referencias r:id conocidas deben existir y tener
el tipo coherente; notas referenciadas ausentes se rechazan.

DTD/entidades, XML malformado, instrucciones de procesamiento XML y XInclude se
rechazan. XML con namespaces/atributos o estructuras de texto no contemplados
no se aplana: omite la parte con inspección incompleta o se rechaza si contradice
la estructura admitida. Los controles se aplican aunque el paquete contenga los
marcadores DOCX que acepta el verificador básico anterior.

## 4. Presupuestos de seguridad efectivos

Valores predeterminados por operación. `LimitesDOCX` admite configuración explícita
validada, con techos de seguridad; no modifica `PoliticaEstructura` o límites HTTP
globales. Un límite alcanzado produce inspección incompleta, sin ampliación automática.

| Recurso | Presupuesto predeterminado |
|---|---|
| Snapshot físico/comprimido | 4194304 bytes (4 MiB) |
| Entradas / central ZIP | 128 / 131072 bytes |
| Descompresión | 2097152 bytes por entrada; 16777216 por pasada completa; expansión 100:1 |
| Lectura ZIP | Bloques de 65536; constructor/directorio hasta 131072 por lectura. 33554432 bytes por preflight/pasada, con hasta un byte de detección de exceso |
| XML | 64 partes; 2 MiB por parte; 100000 nodos acumulados por pasada; profundidad 32 y token pendiente 65536 |
| Carga auxiliar contable | 8388608 bytes: fuente XML equivalente retenida, cadenas/índice de localizadores y datos de resultado contabilizados |
| Párrafos / tablas / celdas | 10000 / 100 / 10000 |
| Texto | 8192 caracteres por fragmento, 524288 caracteres totales emitidos; códigos y ceros no se convierten |
| Relaciones / estilos / propiedades | 2048 / 512 / 128 |
| Diagnósticos/omisiones | 64 combinados, más causa terminal acotada; no se copian mensajes arbitrarios |
| Imagen pasiva | 1 MiB por parte, incluida en los límites ZIP |
| Plazo / cancelación | 5 s cooperativos, Event y reloj monotónico inyectable; controles en lectura y recorridos |

La carga contable **no equivale a heap/RSS**: no incluye todo el overhead de
ZipInfo, nodos, diccionarios, objetos Python y buffers del intérprete. Estos se
acotan adicionalmente por entradas/nodos/texto/partes. El snapshot tiene su
presupuesto separado; su lectura física puede tener copias transitorias acotadas.
No hay cuota del sistema operativo ni watchdog que interrumpa una syscall/C
bloqueada. El plazo no es una garantía rígida de tiempo total. Cancelación no
simula verificaciones finales que no ocurrieron.

Ensayo medido exclusivamente con un fixture de **206557 bytes**, **100 párrafos**
y **200000 caracteres**: pico observado de asignaciones Python **1064448 bytes**,
duración **0.099759 s**, pico contable **512704 bytes**. Tres XML y 308 nodos en la
pasada de extracción. Son medidas de ese caso, no prueba de memoria/tiempo máximos
para cualquier documento. La prueba de memoria usa un umbral amplio de 32 MiB
para ese fixture y verifica también el rechazo por presupuesto contable pequeño.

## 5. Extracción conservadora y referencias

Se concatena el texto de runs conservando espacios, ceros, tabulaciones y saltos
explícitos; se representa la información de `w:t`, `w:tab`, `w:br`, `w:cr` y guiones
explícitos admitidos. Son valores XML decodificados: las reglas XML de entidades
de carácter y saltos de línea corresponden al parser, no a una normalización
científica o conservación byte a byte del fragmento. Los bytes originales quedan
identificados y preservados para cotejar cualquier cita.

Los títulos se reconocen solo por estilos de párrafo declarados con outlineLvl
0–8 o nombres Title/Subtitle, o un nivel explícito de párrafo. No se resuelve
herencia de estilos y un falso en `titulo_por_estilo` no demuestra que no sea
un título visual. No se certifica el carácter oficial de una tabla o definición.

Tablas: cada párrafo aparece una vez en la colección canónica. Las celdas remiten
a esos mismos objetos; las tablas anidadas tienen referencia separada. `CeldaDOCX.texto`
es una representación con LF entre sus párrafos directos; sus literales originales
están en cada párrafo. No incorpora el texto anidado dos veces. Columnas son
ordinales de `w:tc`, sin reconstruir una grilla. gridSpan se retiene como cadena
positiva del perfil; vMerge conserva su atributo literal, `""` si el elemento
carece de valor y `None` si está ausente. No se replican valores por combinaciones;
hMerge queda fuera de alcance. Numeración automática y formato no se renderizan.

La referencia contiene identificador/hash, parte y ruta XML **Clark** con ordinales
entre hermanos del mismo QName, desde uno. Ejemplo estructural sintético:

```text
/{http://schemas.openxmlformats.org/wordprocessingml/2006/main}document[1]/{http://schemas.openxmlformats.org/wordprocessingml/2006/main}body[1]/{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p[1]
```

Ordinal de párrafo y tabla se reinician por parte; fila/celda por su tabla. La parte
y ruta completa desambiguan encabezados y tablas anidadas. No se inventan páginas.
Las pruebas resuelven las referencias en el XML sintético y cotejan texto/hash.
Misma entrada/política produce los mismos resultados y referencias; no se mezclan
fechas técnicas volátiles en ellos.

Campos simples/complejos, instrucciones y caches, revisiones, ocultación y contenido
no comprendido omiten **toda la parte textual** y producen inspección incompleta.
Así no se rescata un cache en otro párrafo cuando un campo atraviesa varios.
No se ejecuta o interpreta una fórmula. Propiedades created/modified/revision o
AppVersion se marcan técnicas/editables: no se convierten en fecha/versión científica.
Identificación editorial en el cuerpo queda como texto localizado para revisión,
sin inferencia automática. No se normalizan unidades, HORA/UBIGEO o estaciones.

## 6. Conservación y alcance de integridad

Para un archivo autorizado se mide tamaño/hash al leer el snapshot y nuevamente
al reabrir después del análisis, comparando firma de dispositivo/inode/tamaño/mtime
y descriptor. No se escribe, renombra, borra, cambia permisos, ejecuta touch o
persiste un resultado. La lectura puede actualizar atime por política del sistema
de archivos; no se promete inmutabilidad de ese metadato controlado por el SO.

`conservacion_comprobada=True` solo significa huella/firma inicial y final
coincidentes en la ejecución. False indica fallo final conocido; None indica que
no se completó o que se inspeccionó memoria. El valor esperado del llamador es
una condición opcional distinta de conservar el archivo. SHA/CRC no autentican
al emisor, no comparan con una firma externa inexistente ni confirman un RAW.

Modelo secuencial de directorios controlados. No hay bloqueo del sistema de
archivos, resistencia absoluta a TOCTOU de un propietario malicioso, detección de
todo hardlink externo o garantía de durabilidad/backups. Una raíz autorizada por
el llamador no demuestra el permiso institucional de lectura. No se amplía este
paso a ACL, autenticación o almacenamiento permanente.

## 7. Ensayos y verificación final

Se construyen todos los ZIP/XML en código de prueba, con nombres/fechas sintéticos;
no se añaden binarios institucionales a Git. Archivos locales solo en directorios
temporales `spica-docx-84g-*`, con limpieza de su raíz propia verificada.

**53 pruebas nuevas** cubren los 30 grupos solicitados, agrupando variantes
adversariales en subtests. Incluyen documento válido/vacío/sin tablas; runs,
títulos, varias tablas/anidadas, encabezados/pies, notas y propiedades; ZIP/CRC,
duplicados/rutas/enlaces/cifrado/métodos/tamaños/expansión/ZIP64; MIME/raíces,
relaciones rotas/externas, macros/OLE/ActiveX/paquetes; XML malformado/DTD/entidades,
PI/XInclude/extensiones; límites de XML/texto/memoria/inventario; cancelación/plazo,
conservación física y referencia determinista. Mocks prohíben archivos/red/DNS,
SQLite, subprocesos y extracción a disco en la API de bytes. No son pruebas
de suficiencia científica, documentos maliciosos ilimitados o la norma OOXML completa.

Antes de la suite completa, aprobaron **115 pruebas dirigidas en 3.404 s**:
52 del inspector en ese momento y 63 anteriores de formato/XLSX. El último caso
de PI/XInclude/extensiones se incluyó posteriormente en la suite completa.
Las comprobaciones estáticas compilan AST en memoria, revisan duplicaciones de
nombres, UTF-8/finales y prohíben importaciones operativas, eval/exec y funciones
de extracción/escritura en los seis módulos nuevos.

Comandos de verificación con el intérprete de `.venv`:

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -B -m pip check
git diff --check
git status --short
```

La suite usa PYTHONPATH temporal de guardia, `src`, `tests` y raíz del repositorio,
sin modificar archivos para configurar importación. La guardia bloquea red y
apertura/mutación de ubicaciones operativas; SQLite solo puede usarse por pruebas
sintéticas, nunca en el almacén real. Pip se ejecuta con `PIP_NO_INDEX=1` y
`PIP_DISABLE_PIP_VERSION_CHECK=1`. No se instalan paquetes.

La primera corrida, dentro del sandbox, ejecutó **1496 tests en 153.441 s** y
terminó con **1 fallo y 33 errores**. Se identificaron denegaciones de acceso a
temporales privados 0700 de tests anteriores y un error de la guardia auxiliar al
interpretar executable=None de subprocess en Windows. Las pruebas nuevas DOCX
aprobaron. Se corrigió exclusivamente esa guardia temporal, sin tocar pruebas
anteriores/ACL/código estable, y se repitió la suite con el contexto normal del
propietario para comprobar los temporales privados. No se oculta esa primera
ejecución como aprobada. Los resultados finales se registran tras el cierre.

`pip check`: **No broken requirements found.**, código 0. La última suite completa
histórica reportada era 1431; el repositorio ya contiene 12 pruebas del 84-E,
de modo que la base previa a 84-G es **1443** y las **53 nuevas** llevan el total
descubierto a **1496**. No se suman otra vez las pruebas dirigidas que se solapan.

## 8. Condiciones del futuro ensayo institucional y riesgos pendientes

El DOCX real no se descargó o abrió. No se leyó el CSV/XLSX operativo, original
temporal del diccionario, evidencia privada del 84-E, RAW, staging o SQLite
operativos. No se computan nuevas huellas de esos almacenes ni se auditan cambios
de terceros. No se modifican las 29 brechas: R02 sigue NO_EVALUABLE y el balance
del 84-E sigue 1 resuelta/13 parciales/12 pendientes/2 contradicciones/1 no evaluable.

Antes de un ensayo real se requiere:

1. Revisar esta implementación, perfil, límites y resultados, con autorización
   expresa posterior para la URL/operación exactas del 84-F. Este informe no la otorga.
2. Preparar/probar el **arnés de adquisición documental** todavía pendiente del
   84-F: un GET, sin reintentos/redirecciones/auth/cookies, carpeta privada nueva,
   publicación exclusiva y manifiesto. Las pruebas del inspector no sustituyen
   esos controles del arnés ni una autorización de red.
3. No relajar automáticamente el perfil si el DOCX usa Strict, campos, contenido
   activo, relaciones externas, características no admitidas o excede límites.
   Conservar resultado real, detener y revisar. No usar Word o convertirlo para
   eludir un rechazo, ni repetir la descarga para corregirlo.
4. Cotejar huellas y localizar cada afirmación con contexto y edición/desconocido
   explícitos. Evaluar autenticidad, vigencia y correspondencia CSV–XLSX–DOCX por
   separado; contenido sintético no cierra una brecha institucional.
5. Mantener deshabilitada la incorporación operativa al catálogo/RAW, GIS y QA/QC
   científico. Ningún resultado de este inspector habilita cálculos, conversiones,
   identidad física o interpretación temporal.

Riesgos residuales principales: perfil deliberadamente limitado y posible rechazo
de DOCX legítimos; ausencia de validación XSD/renderizado completo; imágenes y
propiedades omitidas; RSS y plazo cooperativos; TOCTOU bajo dueño malicioso;
dependencia de helpers privados y ausencia de evidencia institucional real.
**APTO CON RESTRICCIONES** para el alcance demostrado. Cero GET/descargas,
instalaciones, migraciones, escrituras operativas, commits o push.
