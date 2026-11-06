# PASO 84-HC — Auditoría forense offline de WordprocessingML

Fecha: **2026-11-06**. Inspector resultante: **0.2.1**.
Dictamen: **APTO PARA RECONCILIACIÓN DOCUMENTAL**, exclusivamente sobre el
texto literal y sus referencias estructurales. No se ejecutó reconciliación,
validación científica ni actualización de las brechas PNDA.

## 1. Estado recuperado y alcance

Git inicial: rama **feature/suadc-http**, repositorio limpio, HEAD
**ca08d736923a441c46625a8f1c238af8f227dff0** (`ca08d73`, «SUADC: inspeccion
segura de hipervinculos OOXML»). El PASO 84-HB está registrado. Commits anteriores:
`944151a` (adquisición DOCX) y `32a7355` (auditoría del inspector).

Se conservaron sin cambios los informes históricos de
[84-H](adquisicion_docx_pnda_paso84h.md) y
[84-HB](auditoria_relaciones_docx_paso84hb.md). El resultado histórico
`INSPECCION_INCOMPLETA` de 0.2.0 sigue siendo evidencia de aquella ejecución;
no se reemplazó por el resultado nuevo.

Este paso comprende diagnóstico estructural, una corrección acotada, pruebas
sintéticas y **una única reevaluación real** después de aprobar las pruebas.
No hubo conexiones, GET, apertura de destinos, Word, macros, campos ejecutados,
descargas, instalaciones, migraciones, QA/QC, commits o push. No se accedió a RAW,
staging, SQLite operativo ni al CSV/XLSX institucional.

## 2. Evidencia primaria y controles de conservación

Raíz autorizada, exclusivamente para lectura:
`C:\Users\Propietario\SPICA_EVIDENCIAS_PNDA_84F`.
Documento: `metadatos-pnda.docx`, **20664 bytes**, SHA-256:

```text
7b9dcbd71c4d00798d1795edfd5ba0d15ad0aaab0297a7f0aba91532437a0d18
```

Se exigieron rutas absolutas dentro de la raíz, sin symlinks, junctions/reparse
points ni escapes. Se comprobaron firmas de dispositivo/inode, tamaño y mtime,
modo y atributos de archivo, incluidas comparaciones del descriptor abierto.
El inventario exacto de **seis archivos** se verificó antes y después del
diagnóstico y de la reevaluación. No se ejecutó ni importó el procedimiento
histórico. Los controles se abrieron en `rb`, sin publicar su contenido.

| Archivo original | Bytes | SHA-256 antes y después |
|---|---:|---|
| metadatos-pnda.docx | 20664 | `7b9dcbd71c4d00798d1795edfd5ba0d15ad0aaab0297a7f0aba91532437a0d18` |
| inspeccion.json | 2427 | `9f6f5b2e47145e19f0bc097a9f66f468ab5837d7de5b944d3e17af9e9b389e9f` |
| procedencia.json | 3398 | `4f16e90aa47d06119bd559e9939a96683da579b032ff6c574b90ad0ce977f0b1` |
| preparacion.json | 936 | `bfca2294044f2d5c3ef8b03646d0a76976c767279deed3e9ca5c054c8c4086e4` |
| intento-iniciado.json | 410 | `d5ff6cae61f17591cfff196e51b2e0394bf6da9dfa93f21250489875a5cf8b46` |
| procedimiento84h.py | 16116 | `c878f1778e775bab3be5ae90878eeb12eac59eeed82101e95a533c1c8cdd2f71` |

Resultado: seis identidades y firmas coincidentes, sin archivos añadidos o
eliminados en la raíz original. Su ACL permaneció igual; no se modificaron
permisos. La lectura puede actualizar atime por decisión del sistema operativo;
no se promete preservar ese metadato ni aislamiento frente a un propietario
malicioso que sustituya rutas concurrentemente.

## 3. Causa exacta del diagnóstico de 0.2.0

En [detectar](../src/spica/adquisicion/verificacion/docx/_extraccion.py),
una bandera `ambigua` agrupa varias causas: campos, revisiones, texto oculto,
dibujos, elementos desconocidos y atributos fuera de los namespaces admitidos
en partes textuales. El llamador en
[_paquete.py](../src/spica/adquisicion/verificacion/docx/_paquete.py) registra
`campos_revisiones_o_caracteristicas_no_interpretadas` y omite la extracción de
la parte afectada. Ese diagnóstico **no prueba por sí solo la presencia de un
campo o una revisión**.

En este archivo, la condición activada fue la de **namespace de atributo fuera
del perfil**, por tres QNames. No aparecieron elementos problemáticos nuevos.
La primera condición aparece en el atributo `mc:Ignorable` de `w:document`.
No es un rechazo temprano: el recorrido sigue examinando los nodos y atributos,
acumula la bandera y omite después el cuerpo. Un fallo activo o de límite sí
puede interrumpir un recorrido; no fue la causa observada.

Convenciones de las tablas siguientes, con identidades de namespace exactas:

| Prefijo explicativo | Namespace |
|---|---|
| w | `http://schemas.openxmlformats.org/wordprocessingml/2006/main` |
| mc | `http://schemas.openxmlformats.org/markup-compatibility/2006` |
| w14 | `http://schemas.microsoft.com/office/word/2010/wordml` |

Los prefijos son abreviaturas de lectura, no identidades. En el resultado se
conservan rutas Clark completas, con ordinal entre hermanos del mismo QName.

| Característica observada | Parte | Cantidad | Ubicación y valor saneado | Riesgo y tratamiento |
|---|---|---:|---|---|
| Atributo `mc:Ignorable` | word/document.xml | 1 | Raíz `/w:document[1]`; lista `w14 w15 w16se w16cid w16 w16cex wp14` | Declaración de compatibilidad, no texto ni contenedor. No se aplica un procesador MC ni se habilitan extensiones |
| Atributo `w14:paraId` | word/document.xml | 72 | Los 55 `w:p` y 17 `w:tr`; ocho dígitos hexadecimales en cada caso, valores omitidos | Identificador opaco de edición; no se usa para identidad científica, revisión vigente o deduplicación |
| Atributo `w14:textId` | word/document.xml | 72 | Los mismos 55 `w:p` y 17 `w:tr`; ocho dígitos hexadecimales en cada caso, valores omitidos | Metadato opaco; no se interpreta como hash del texto, fecha o autoridad documental |

Total: **145 atributos** causantes de la bandera, **tres QNames distintos**.
Las dos clases de IDs están presentes sobre cada uno de los 72 nodos señalados.
Rutas de ubicación, usando los prefijos anteriores:

- Primera causa: `/w:document[1]`.
- Primer párrafo con ambos IDs: `/w:document[1]/w:body[1]/w:p[1]`.
- Párrafos directos: `/w:document[1]/w:body[1]/w:p[k]`, `k=1..4`.
- Tabla única: `/w:document[1]/w:body[1]/w:tbl[1]`.
- Filas con ambos IDs: esa tabla seguida de `/w:tr[i]`, `i=1..17`.
- Los restantes 51 párrafos están en sus 34 celdas, con rutas
  `/w:tr[i]/w:tc[j]/w:p[k]` relativas a la tabla. `j` es ordinal de celda XML,
  no una coordenada de grilla renderizada.

Ejemplo Clark completo de la primera causa:

```text
/{http://schemas.openxmlformats.org/wordprocessingml/2006/main}document[1]
```

Se comprobó el enlace de cada prefijo **en la raíz real**, utilizando los
eventos de namespace del mismo parser seguro, sin inferirlo del nombre:

| Prefijo presente | URI declarada en la raíz |
|---|---|
| w14 | `http://schemas.microsoft.com/office/word/2010/wordml` |
| w15 | `http://schemas.microsoft.com/office/word/2012/wordml` |
| w16se | `http://schemas.microsoft.com/office/word/2015/wordml/symex` |
| w16cid | `http://schemas.microsoft.com/office/word/2016/wordml/cid` |
| w16 | `http://schemas.microsoft.com/office/word/2018/wordml` |
| w16cex | `http://schemas.microsoft.com/office/word/2018/wordml/cex` |
| wp14 | `http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing` |

Las URI son identificadores XML; no se accedió a ellas. Esta inspección acredita
lo declarado en el archivo; no constituye una comprobación normativa externa.

## 4. Inventario positivo y ausencia comprobada de estructuras ambiguas

El diagnóstico seguro examinó las **12 partes XML** del paquete. Los elementos
expresamente solicitados tienen los siguientes conteos, con los namespaces
`w` y `mc` definidos arriba:

| Elemento | Apariciones |
|---|---:|
| w:fldSimple | 0 |
| w:fldChar | 0 |
| w:instrText | 0 |
| w:ins | 0 |
| w:del | 0 |
| w:moveFrom | 0 |
| w:moveTo | 0 |
| w:pPrChange | 0 |
| w:rPrChange | 0 |
| w:sdt | 0 |
| mc:AlternateContent | 0 |

Otros elementos **realmente presentes** en `word/document.xml`, todos del
namespace `w`, agrupados sin confundir una declaración con contenido ejecutable:

| Grupo | Nombres y cantidades |
|---|---|
| Estructura y texto literal | document=1, body=1, p=55, r=123, t=123 |
| Tabla | tbl=1, tblPr=1, tblStyle=1, tblW=1, tblLook=1, tblGrid=1, gridCol=2, tr=17, tc=34, tcPr=34, tcW=34, vAlign=18 |
| Propiedades de párrafo/run | pPr=55, rPr=177, rFonts=177, jc=17, b=21, bCs=21, sz=41, szCs=41, u=2, color=92, kern=15, lang=48 |
| Estilos y numeración | rStyle=3, pStyle=5, numPr=5, ilvl=5, numId=5, spacing=1 |
| Marcadores y enlaces | proofErr=16, hyperlink=3, lastRenderedPageBreak=1 |
| Sección y página | sectPr=1, pgSz=1, pgMar=1, cols=1, docGrid=1 |

Los atributos `w:rsidR`=129, `w:rsidRPr`=125, `w:rsidRDefault`=55,
`w:rsidP`=54, `w:rsidTr`=17 y `w:rsidSect`=1 son metadatos de sesiones de
edición ya contemplados por el perfil anterior. **Su presencia no demuestra
que exista texto insertado/eliminado ni permite reconstruir revisiones.**

Política semántica aplicada:

| Clase | Situación observada y decisión |
|---|---|
| A. Formato pasivo | Propiedades de formato, marcadores e IDs opacos: se conserva el literal sin renderizar; no se calcula su significado científico |
| B. Contenedores locales | document/body/p/r/t y tbl/tr/tc admitidos por el perfil existente. Hyperlink conserva únicamente sus runs locales; destino omitido |
| C. Campos e instrucciones/caché | No observados. En sintéticos, simples/complejos permanecen incompletos; nunca se ejecuta la instrucción o promueve la caché |
| D. Revisiones | No observadas. En sintéticos se omite la parte textual, sin escoger versión, aceptar inserciones o hacer vigente texto eliminado |
| E. Alternativas | No observadas. MC AlternateContent y sus ramas siguen sin seleccionar ni activar |
| F. Desconocido | No se admite un elemento/atributo nuevo por aparecer su namespace en Ignorable. Persiste la inspección incompleta o el rechazo de contenido activo |

`mc:Ignorable` es una **declaración de compatibilidad**, separada del formato
pasivo ordinario. No convierte automáticamente en seguros sus elementos
asociados. No hay en este documento una instrucción de campo que ejecutar ni
un estado de revisión que resolver, dentro del recorrido realizado.

## 5. Dos contratos limitados y justificación separada

### 5.1. IDs opacos de Word 2010

Solo se reconocen los atributos de QName exacto `{w14}paraId` y `{w14}textId`
en elementos de QName exacto `{w}p` o `{w}tr`, con valor de **ocho caracteres
ASCII hexadecimales**. Cualquier otro contexto o formato se rechaza con
`identificador_word2010_fuera_del_perfil`. Un prefijo parecido con otra URI no
obtiene esa autorización.

No se añaden elementos, hijos o rutas de extracción. Se mantienen íntegros los
validadores existentes de párrafos/filas y todos sus descendientes. Los IDs se
descartan del DTO y de los diagnósticos; se registra
`identificadores_word2010_no_interpretados`, una vez por parte. No deciden qué
texto es vigente, no deduplican párrafos y no autentican documentos. Esta
omisión es neutral respecto de los caracteres de `w:t`.

### 5.2. Declaración raíz MC, sin implementar MC

Solo se admite el atributo de QName exacto `{mc}Ignorable` en la raíz exacta
`{w}document`. Su valor debe contener entre uno y siete prefijos únicos,
ASCII, longitud máxima 32, sintaxis `[A-Za-z_][A-Za-z0-9_.-]*`; cada prefijo
debe estar declarado en esa raíz y resolver a una de las siete URI de la tabla.
No se hereda una declaración desde otra parte ni se sustituye la raíz con una
redeclaración de un descendiente. Un alias válido se evalúa por su URI.

Se reutiliza `_XML` con un evento de declaración de namespace. Se guardan como
máximo **64 declaraciones raíz**, cargadas al presupuesto auxiliar y liberadas
al salir del árbol, también ante error. No se añade parser ni resolución de URI,
y siguen activos DTD/entidades/instrucciones XML prohibidas, límites, CRC y
comprobaciones finales DEFLATE.

La declaración no se **aplica** para descartar elementos desconocidos. Todos los
nodos y atributos siguen recorriéndose. Se registra
`declaracion_mc_ignorable_sin_procesamiento`. No se permiten nuevos hijos ni
atributos `mc:ProcessContent`, `MustUnderstand`, `PreserveElements` o
`PreserveAttributes`. `AlternateContent`, `sdt`, campos, revisiones y extensiones
no implementadas continúan bloqueando una extracción completa; el contenido
activo mantiene el rechazo previo.

La necesidad de ambos contratos se demostró antes de modificarlos: el primero
cubre 144 atributos sin texto; el segundo, una lista raíz cuyo procesamiento
no es necesario para el literal soportado. No se habilitó ninguna familia
adicional mediante ensayos sucesivos sobre el archivo real.

Este es un **perfil experimental cerrado**, no una implementación general de
OOXML/MC ni una validación XSD. No se consultó documentación externa en este
paso. No se declara equivalencia con Microsoft Word, numeración renderizada,
formato visual, paginación, vigencia editorial o todas las funciones de esas URI.

## 6. Archivos y pruebas

| Archivo | Cambio |
|---|---|
| [_extraccion.py](../src/spica/adquisicion/verificacion/docx/_extraccion.py) | Dos reconocimientos exactos de atributos; omisiones explícitas, sin ignorar extensiones |
| [_paquete.py](../src/spica/adquisicion/verificacion/docx/_paquete.py) | Contexto de namespace raíz acotado, sobre el parser seguro existente |
| [modelos.py](../src/spica/adquisicion/verificacion/docx/modelos.py) | Versión del inspector 0.2.0 → 0.2.1; sin cambios en campos de DTO o firmas públicas |
| [test_hipervinculos_docx.py](../tests/test_hipervinculos_docx.py) | Únicamente expectativa literal de versión actualizada |
| [test_metadatos_compatibilidad_docx.py](../tests/test_metadatos_compatibilidad_docx.py) | **17 pruebas nuevas**, con múltiples subcasos adversariales sintéticos |
| Este informe | Inventario, decisión y evidencia del PASO 84-HC |

Las 17 pruebas cubren: documento sin metadatos; texto/orden e IDs en párrafos y
filas; IDs repetidos sin deduplicación; alias correctos; declaraciones raíz;
contextos y valores inválidos; prefijos falsos/reasignados/de otra parte;
atributos/extensiones MC no admitidos; campos simples y complejos/caché;
inserciones, eliminaciones, movimientos y cambios de propiedades; sdt,
alternativas y anidación desconocida; XML malformado/DTD; límite de namespaces;
enlaces pasivos y externas prohibidas; CRC, DEFLATE y presupuestos; cancelación;
ausencia de I/O externo; conservación del original sintético y determinismo.

Primer ensayo dirigido: **94 ejecutadas, 1 fallo de fixture**, sin error del
intérprete. El caso de atributo en `w:t` no se había insertado porque el nodo
incluía `xml:space="preserve"`. Se corrigió el fixture y se añadió una aserción
que acredita la mutación antes de evaluar. No se cambió el producto para
satisfacer ese caso.

Resultados definitivos, con Python **3.15.1** de `.venv`, antes de la reevaluación:

```powershell
$env:PYTHONPATH="$PWD\src;$PWD\tests;$PWD"
.\.venv\Scripts\python.exe -B -m unittest test_inspector_docx test_hipervinculos_docx test_metadatos_compatibilidad_docx -v
```

**94 pruebas aprobadas**, 0 fallos, 0 errores; **1.452 s**. Incluye las 58 pruebas
originales del inspector, las 19 del 84-HB y las 17 nuevas.

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
```

**1537 aprobadas, 0 fallidas, 0 errores, 0 omitidas**, **143.220 s**, salida `OK`,
código 0. Total real: **1520 anteriores + 17 nuevas**. Las dirigidas y los
subcasos no se suman de nuevo al acumulado.

La suite completa usó `PYTHONPATH` temporal con una guardia de auditoría antes de
`src`, `tests` y raíz. Se ejecutó como propietario normal para los temporales
privados de Windows, sin modificar ACL anteriores. La guardia bloqueó red,
rutas operativas y procesos ajenos a Python/Git: contadores finales **todos 0**.

```powershell
$env:PIP_NO_INDEX='1'
$env:PIP_DISABLE_PIP_VERSION_CHECK='1'
.\.venv\Scripts\python.exe -B -m pip check
```

Resultado: **No broken requirements found.**, código 0. La primera ejecución
con guardia de procesos había bloqueado la consulta local de versión Windows
que utiliza `platform`, no detectado un conflicto de dependencias. Se repitió
con guardia de red y rutas operativas, permitiendo esa consulta local; sus
contadores fueron 0. No se instaló ni actualizó ningún paquete.

## 7. Única reevaluación real con 0.2.1

Inicio UTC: **2026-11-06T13:34:16.440176+00:00**.
Fin UTC: **2026-11-06T13:34:16.603858+00:00**.
Se llamó una vez a `inspeccionar_docx_archivo` con la raíz exacta,
`identificador='DOCX-PNDA-84HC'` y tamaño/hash esperados. No se repitió GET.

| Resultado | Valor observado |
|---|---|
| Estado | **DOCUMENTO_VALIDADO_EN_ALCANCE**, inspector **0.2.1** |
| Rechazos / advertencias | 0 / 0 |
| Paquete | 12 partes XML, 9 relaciones internas, 3 destinos externos omitidos |
| Párrafos | **55**: 4 directos del cuerpo y 51 dentro de celdas |
| Tablas | **1**, con **17 filas** y **34 celdas** |
| Doble conteo | 0 referencias de párrafo duplicadas; los párrafos de celda son los mismos objetos canónicos de la lista global |
| Propiedades técnicas seleccionadas | 5; valores no publicados ni atribuidos a una edición oficial |
| Conservación del original | **True**; 20664 bytes y SHA-256 esperado antes y después |
| Nuevos bloqueos | Ninguno en esta ejecución; no se encadenaron excepciones adicionales |

Las referencias contienen ID local, SHA-256, parte y ruta Clark con ordinales.
La tabla está en `/w:document[1]/w:body[1]/w:tbl[1]`; párrafos directos `p[1..4]`.
Los ordinales globales de esos cuatro párrafos son **1, 2, 3 y 55** porque los
51 párrafos de tabla se intercalan en el orden del cuerpo. No se duplican
como nuevas observaciones al acceder a la tabla. No son números de página.

Se conservaron los localizadores de los 55 párrafos, la tabla, las 34 celdas y
los usos locales de los tres enlaces. No se exportó el texto completo, autores,
correos, destinos o valores de propiedades. El literal de `w:t` se mantuvo en
memoria durante la operación. No se obtuvo texto de una caché de campo ni de una
revisión: esas estructuras no fueron observadas.

Omisiones reales, explícitas y compatibles con este alcance:

- Metadatos no seleccionados de `docProps/app.xml` y `docProps/core.xml`.
- Declaración MC no procesada e IDs opacos no interpretados en el cuerpo.
- Formato auxiliar sin renderizar de fontTable, numbering, settings, theme1 y
  webSettings.
- Los tres destinos hyperlink de tipo HTTPS, HTTP y mailto, sin consultarlos.

El diagnóstico de cuerpo no interpretado del 84-HB no aparece en esta ejecución.
Esto no vuelve interpretadas las funciones de formato/compatibilidad omitidas
ni acredita completitud semántica, científica o visual del documento.

Consumo registrado: **137506 bytes descomprimidos por pasada**, 12 XML,
3106 nodos, **738150 bytes auxiliares contables de pico**; lecturas ZIP de
preflight/verificación/extracción: **24436 / 40428 / 18852 bytes**.
El presupuesto auxiliar no es una medición del RSS y el plazo es cooperativo.

El supervisor de esta reevaluación prohibió sockets, procesos secundarios,
SQLite, mutaciones de archivos y acceso a las rutas operativas. Contadores:
**0 red, 0 escrituras, 0 SQLite, 0 procesos, 0 rutas operativas**. La captura
de salida saneada se escribió por el supervisor fuera de la raíz original.

Artefactos técnicos temporales, sin copia del DOCX ni contenido íntegro:

```text
%TEMP%\spica-84hc-auditoria-47de0eab6b7e4fb0b0a720dc3d7eda8f\
    inventario-estructural.json
    reevaluacion-resumen.json
    suite-completa.log
```

Incluyen QNames, cantidades y referencias estructurales saneadas, no texto o
destinos. En la misma raíz quedan el supervisor local y guardias reproducibles;
no forman parte de Git ni sustituyen los seis originales de evidencia. Su
retención es temporal; el informe conserva los resultados necesarios para revisión.

## 8. Restricciones y dictamen

La [matriz de 29 brechas](brechas_diccionario_pnda_paso84e.md) permanece intacta:
**1 resuelta, 13 parciales, 12 pendientes, 2 contradicciones y 1 no evaluable**.
No se infirieron zona horaria, HORA, estaciones, CRS, unidades, frecuencias,
vigencia, licencia o equivalencia editorial entre CSV/XLSX/DOCX. No se
modificaron observaciones ni se hizo QA/QC científico.

No se leyó el almacenamiento operativo para «demostrar» su inmutabilidad:
se impidió su acceso durante las pruebas y la reevaluación. No hubo escrituras
operativas; SQLite de las pruebas utiliza únicamente memoria o temporales.
La evidencia primaria se comprobó físicamente, sin convertir su SHA-256 en prueba
de autenticidad institucional o de corrección del contenido.

Pendientes: revisión humana del texto literal con sus referencias; aplicabilidad
y aprobación de cualquier reconciliación futura; documentación normativa
independiente si se pretende ampliar el perfil; cobertura OOXML general,
renderizado/XSD completos y aislamiento frente a sustituciones maliciosas.
La dependencia privada del final DEFLATE de CPython sigue declarada y no cambió.

**APTO PARA RECONCILIACIÓN DOCUMENTAL** dentro del perfil literal comprobado.
No equivale a autorización para reconciliación científica, resolución de las
29 brechas, ejecución de campos o aceptación de revisiones. Se espera revisión.

## 9. Git final y verificación de entrega

Se comprobaron sintaxis en memoria, archivos nuevos, enlaces relativos y
coherencia de cantidades. `git diff --check`: sin errores.
HEAD permanece en **ca08d73**; no se ejecutaron commits ni push.
Únicamente estos seis archivos tienen cambios:

```text
 M src/spica/adquisicion/verificacion/docx/_extraccion.py
 M src/spica/adquisicion/verificacion/docx/_paquete.py
 M src/spica/adquisicion/verificacion/docx/modelos.py
 M tests/test_hipervinculos_docx.py
?? docs/auditoria_estructuras_docx_paso84hc.md
?? tests/test_metadatos_compatibilidad_docx.py
```

No se modificaron los informes históricos 84-H/84-HB, la matriz de brechas,
`main.py`, `.gitignore`, `.venv`, dependencias, transportes, RAW o contratos
públicos anteriores.
