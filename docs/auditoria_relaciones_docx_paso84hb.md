# PASO 84-HB: relaciones externas DOCX y reevaluación offline

Fecha: **2026-11-06**. **APTO CON RESTRICCIONES** para la corrección limitada
demostrada; el documento permanece **sin habilitación para reconciliación**.
El inspector 0.2.0 omitió tres hipervínculos pasivos, pero devolvió
**INSPECCION_INCOMPLETA** por otra característica fuera del perfil textual.
No se realizaron ajustes sucesivos para aceptar el archivo.

## 1. Recuperación e integridad inicial

Git comenzó limpio en **feature/suadc-http**, HEAD **944151a**,
`SUADC: adquisicion controlada y evidencia DOCX PNDA`. Se comprobó que este
commit registra el [informe del 84-H](adquisicion_docx_pnda_paso84h.md).
Se revisaron inspector, modelos, pruebas y diagnóstico histórico antes de editar.

Evidencia primaria exacta:

```text
C:\Users\Propietario\SPICA_EVIDENCIAS_PNDA_84F\metadatos-pnda.docx
20664 bytes
SHA-256 7b9dcbd71c4d00798d1795edfd5ba0d15ad0aaab0297a7f0aba91532437a0d18
```

El inventario comprobado contiene **seis archivos en total**: el DOCX y cinco
auxiliares, no seis auxiliares adicionales. Se verificaron contra las huellas
del cierre del 84-H:

| Archivo original | Bytes | SHA-256 verificado |
|---|---:|---|
| `metadatos-pnda.docx` | 20664 | `7b9dcbd71c4d00798d1795edfd5ba0d15ad0aaab0297a7f0aba91532437a0d18` |
| `inspeccion.json` | 2427 | `9f6f5b2e47145e19f0bc097a9f66f468ab5837d7de5b944d3e17af9e9b389e9f` |
| `procedencia.json` | 3398 | `4f16e90aa47d06119bd559e9939a96683da579b032ff6c574b90ad0ce977f0b1` |
| `preparacion.json` | 936 | `bfca2294044f2d5c3ef8b03646d0a76976c767279deed3e9ca5c054c8c4086e4` |
| `intento-iniciado.json` | 410 | `d5ff6cae61f17591cfff196e51b2e0394bf6da9dfa93f21250489875a5cf8b46` |
| `procedimiento84h.py` | 16116 | `c878f1778e775bab3be5ae90878eeb12eac59eeed82101e95a533c1c8cdd2f71` |

Las rutas se verificaron sin symlinks/reparse y dentro de la raíz autorizada.
Los archivos se abrieron exclusivamente `rb`; el procedimiento antiguo solo se
leyó para calcular su hash, nunca se importó o ejecutó. No se creó, cambió o
eliminó nada en ese directorio. Se conservaron los JSON del rechazo 0.1.0.

## 2. Diagnóstico forense acotado

Se reutilizaron preflight, límites, lector ZIP, CRC/XML compartidos y
[`arbol`/`entrada_observable`](../src/spica/adquisicion/verificacion/docx/_paquete.py).
La inspección forense recorrió todas las partes `.rels` y localizó sus usos
mediante rutas Clark sobre XML ya leído con los presupuestos del inspector.
No se construyó otro parser ni se extrajo ZIP a disco. Las clasificaciones se
refieren a estructura y papel de la relación, no a confianza en su destino.

Las tres relaciones externas tienen estos valores comunes:

- Parte: **word/_rels/document.xml.rels**; origen: **word/document.xml**.
- Tipo exacto: `http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink`.
- TargetMode: **External**.
- Uso: **w:hyperlink/@r:id**, hijo directo de **w:p**; contenido local en **w:r/w:t**.
- Ningún destino es necesario para leer esos nodos locales. No se resolvió,
  consultó o verificó el destino, ni se lanzó un navegador o cliente de correo.

| ID original | Tipo de destino | Localizador abreviado del uso | Clasificación |
|---|---|---|---|
| **rId7** | mailto, sin parámetros o fragmento | `document/body/tbl[1]/tr[17]/tc[2]/p[1]/hyperlink[1]` | **A: enlace pasivo omitible** |
| **rId6** | HTTP, sin credenciales, consulta o fragmento | `document/body/tbl[1]/tr[11]/tc[2]/p[1]/hyperlink[1]` | **A: enlace pasivo omitible** |
| **rId5** | HTTPS, sin credenciales, consulta o fragmento | `document/body/tbl[1]/tr[2]/tc[2]/p[1]/hyperlink[1]` | **A: enlace pasivo omitible** |

Los destinos completos y direcciones de correo no se publican. Se conserva el
archivo/hash y sus IDs/localizadores para cotejo autorizado. El tipo OOXML
anterior es un identificador de esquema, no un destino seguido.

**Causa precisa del rechazo anterior:** la primera External en el orden XML
era **rId7**. La condición de aborto 0.1.0 rechazaba cualquier External antes de
clasificar su papel. rId6 y rId5 también quedaban bloqueadas por la misma regla.
La correspondencia se determinó por el orden observado y el código anterior;
no se cambió de versión o reejecutó la descarga para demostrarla.

En el inventario completo de relaciones externas no se observaron categorías
B (imagen/multimedia), C (plantilla), D (OLE/objeto), E (contenido alternativo),
F (desconocida) o G (malformada/contradictoria). Sus pruebas sintéticas continúan
exigiendo rechazo. Esa clasificación no certifica la semántica de todo el OOXML.

### Referencias reproducibles

Las referencias completas usan el identificador **DOCX-PNDA-84HB**, el SHA-256
anterior y la parte **word/document.xml**. Índices entre hermanos del mismo QName,
desde uno, no páginas o grilla renderizada. Ejemplo completo de rId7:

```text
/{http://schemas.openxmlformats.org/wordprocessingml/2006/main}document[1]/{http://schemas.openxmlformats.org/wordprocessingml/2006/main}body[1]/{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tbl[1]/{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tr[17]/{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tc[2]/{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p[1]/{http://schemas.openxmlformats.org/wordprocessingml/2006/main}hyperlink[1]
```

rId5/rId6 usan exactamente la misma estructura, con `tr[2]` y `tr[11]`.
Las referencias registran la presencia/uso del enlace; no son citas de sus
valores ni evidencia científica de lo que un destino pudiera contener.

## 3. Corrección mínima: política cerrada, inspector 0.2.0

El modelo anterior `RelacionDOCX` representa destinos internos del paquete.
Se conservó sin cambios. Se añadió **HipervinculoOmitidoDOCX** y una colección
final opcional **ResultadoDOCX.hipervinculos_omitidos**, vacía por defecto.
No se desplazan los argumentos anteriores del resultado ni se cambian HTTP,
RAW, catálogo o contratos científicos. `diagnostico_publico()` añade solo un
conteo; la versión **0.2.0** distingue este comportamiento del histórico 0.1.0.

El registro nuevo contiene parte `.rels`, ID, tipo exacto, TargetMode, parte de
origen, clase de destino y referencias locales. **No tiene URI, dirección,
href, objeto activable o instrucciones de apertura.** El texto del documento
sigue siendo texto no confiable: cualquier consumidor debe mostrarlo como texto,
escapando HTML/Markdown y sin activar automáticamente enlaces. No se implementa UI.

Condiciones conjuntas:

1. Tipo exacto Transitional **hyperlink** y TargetMode exacto **External**.
   No se acepta un modo inválido o un hyperlink interno contradictorio.
2. Origen dentro de partes textuales ya admitidas: documento, encabezado/pie
   numerado o notas. Nunca raíz de relaciones, estilos, settings o partes ajenas.
   El grafo de relaciones internas sigue acreditando las partes del paquete.
3. IDs únicos y acotados; referencias existentes. Se exige al menos un uso local
   coherente. Una relación externa no utilizada se rechaza, aunque declare hyperlink.
4. Uso exacto `w:hyperlink/@r:id` bajo `w:p`, con runs locales de texto/formato
   admitido. Se rechazan otros atributos r:*, usos en imagen/objeto o combinación
   ambigua con anchor/docLocation. Los demás atributos admitidos del enlace son
   únicamente `w:history`, `w:tooltip` y `w:tgtFrame`, que no se ejecutan o exportan.
5. Destino de hasta **2048 caracteres**, sintaxis acotada y solo esquemas
   **http/https/mailto**. HTTP(S) exige host y puerto sintácticamente válidos, sin
   usuario/clave; mailto se limita a un buzón simple sin query, fragmento o destinatarios
   múltiples. No se valida que el host/buzón exista. Otras URI, archivos, UNC,
   javascript/data/FTP, controles, espacios y escapes ambiguos se rechazan.
6. Consultas/fragmentos de HTTP(S) nunca se devuelven; tampoco se registra la URI
   sin ellos. Una prueba con token confirma que no aparece en resultados/diagnósticos.
7. La URI se descarta. Se registra **destino_hipervinculo_externo_no_consultado**;
   solo se extrae XML local cuando la parte supera también los demás controles.
8. No hay `allow_external=True` ni bandera global para admitir otros tipos.
   No se cambia el parser o el comportamiento del verificador compartido XLSX.

Se preservan todos los controles ZIP/XML/CRC/DEFLATE, grafo, contenido activo,
complejidad, plazo, cancelación y conservación. El máximo de relaciones cuenta
internas y externas; los usos externos tienen además un máximo independiente
igual a **max_referencias** (2048 por defecto). Índices y referencias retenidas
se incluyen en la carga auxiliar contable. No es una cuota RSS del SO.

## 4. Archivos de código y pruebas

| Archivo | Cambio |
|---|---|
| [_hipervinculos.py](../src/spica/adquisicion/verificacion/docx/_hipervinculos.py) | Nuevo módulo local: clasificación cerrada, comprobación de usos y registro sin destino |
| [_paquete.py](../src/spica/adquisicion/verificacion/docx/_paquete.py) | Integra candidatos con relaciones/grafo y recorrido completo, sin eximir otras partes |
| [_extraccion.py](../src/spica/adquisicion/verificacion/docx/_extraccion.py) | Verifica QName, atributo y tipo de uso hyperlink; conserva extracción literal |
| [modelos.py](../src/spica/adquisicion/verificacion/docx/modelos.py) | DTO aditivo, colección y versión 0.2.0 |
| [_control.py](../src/spica/adquisicion/verificacion/docx/_control.py) | Almacena únicamente registros sin destinos |
| [inspector.py](../src/spica/adquisicion/verificacion/docx/inspector.py) | Incluye registros en resultados estructurados |
| [__init__.py](../src/spica/adquisicion/verificacion/docx/__init__.py) | Exporta el contrato local nuevo |
| [test_hipervinculos_docx.py](../tests/test_hipervinculos_docx.py) | 19 pruebas nuevas con variantes sintéticas |

No se modificaron las 58 pruebas anteriores del inspector o módulos ajenos a él.
Los otros cambios son este informe y la actualización histórica del 84-H.
No hay documentos institucionales como fixtures o archivos binarios nuevos en Git.

## 5. Ensayos previos y regresiones

Antes de reevaluar el archivo real:

- **77 pruebas dirigidas aprobadas**, 0 fallos/errores, **1.414 s**:
  58 anteriores y 19 nuevas.
- **1520 pruebas completas aprobadas**, 0 fallos, 0 errores y 0 omitidas,
  **151.902 s**. Total: **1501 anteriores + 19 nuevas**; no se suman otra vez las
  77 dirigidas o los 11 ensayos temporales históricos del 84-H.
- `.venv\Scripts\python.exe -B -m pip check`: **No broken requirements found.**, código 0.

Las pruebas nuevas cubren documento sin externas; HTTP/HTTPS/mailto pasivos;
párrafo/tabla, múltiples IDs/usos y referencias deterministas; externa sin uso;
imagen, plantilla, OLE, altChunk y tipo desconocido; modo/ID/ref/origen contradictorios;
DTD/XML malformado; destinos sensibles o inseguros; ausencia de red/archivos
externos/SQLite/procesos; CRC/límites/DEFLATE, cancelación e inmutabilidad.
Un fixture con campo no interpretado comprueba que un enlace pasivo no convierte
una inspección incompleta en validada. No se debilitaron controles para aprobar.

La suite usó guardia temporal y contexto del propietario para temporales privados,
sin cambiar ACL de datos anteriores. Guardia: **0 red, 0 rutas operativas,
0 SQLite operativos, 0 procesos no admitidos**. Compilación AST en memoria de
siete módulos y las pruebas nuevas: sin errores, definiciones duplicadas o ciclos
locales. Importación aislada sin HTTPX, SQLite, HTTP/RAW o integración.

## 6. Reevaluación real, una sola vez y offline

Inicio UTC: **2026-11-06T12:58:47.540932+00:00**.
Fin UTC: **2026-11-06T12:58:47.670684+00:00**.
Se exigieron tamaño/hash esperados en `inspeccionar_docx_archivo`, con raíz exacta.

| Resultado | Observación |
|---|---|
| Estado | **INSPECCION_INCOMPLETA**, versión **0.2.0** |
| Rechazos estructurales terminales | Ninguno en esta ejecución; no equivale a validación completa de contenido |
| Restricción bloqueante | **campos_revisiones_o_caracteristicas_no_interpretadas**, parte **word/document.xml** |
| Inventario | **12 partes, 9 relaciones internas, 3 hipervínculos omitidos** |
| Texto/tablas | **0 párrafos, 0 tablas** extraídos |
| Propiedades | **5 técnicas**, sin publicar valores o atribuir edición/vigencia |
| Conservación física | **True**; tamaño/hash coincidentes antes/después |
| Controles del programa supervisor | **0 red, 0 escrituras, 0 SQLite, 0 procesos** |

El código de restricción agrupa campos, revisiones o características no
interpretadas: **no permite afirmar cuál de ellas existe**. Se detuvo el
incremento sobre el documento, sin otro análisis de esa característica,
modificación de controles o ejecución adicional para conseguir aceptación.
La ausencia de párrafos extraídos no implica ausencia de una tabla o texto en el
archivo: las referencias de enlaces ya localizan nodos de la primera tabla.

Controles técnicos recorridos: preflight/nombres/rangos/tamaños del ZIP, pasada
compartida de CRC/XML, tipos, relaciones/grafo, lecturas observables y finales
DEFLATE de las partes, restricciones de contenido activo y verificación física.
Se contabilizaron **137506 bytes descomprimidos en cada pasada**, **12 XML**,
**3106 nodos** y **55078 bytes auxiliares contables de pico**. No hay validación
XSD exhaustiva o renderizado. La completitud semántica del cuerpo no se superó.

Omisiones registradas: metadatos no seleccionados de core/app; cuerpo no
interpretable; formato auxiliar de fontTable, numbering, settings, theme y
webSettings; tres destinos pasivos no consultados. No se recuperaron valores
del cuerpo con otro parser o Microsoft Word.

El resultado técnico sin texto ni destinos se conservó solo en
`%TEMP%\spica-84hb-auditoria-d41f62efb4454470bb5a32ef73ce353f\reevaluacion-resumen.json`;
la salida verbose de la suite está en `suite-completa.log`, en ese mismo temporal.
No se exportó el contenido íntegro ni se escribió un nuevo resultado dentro de
la carpeta original de evidencia.

## 7. Integridad final, brechas y restricciones científicas

Los **seis archivos originales** volvieron a verificarse después: inventario,
tamaños y SHA-256 coinciden con la tabla inicial; firmas de dispositivo/inode,
tamaño/mtime y modos permanecen iguales. No se cambiaron permisos ni se
reescribió el rechazo histórico. La lectura puede actualizar atime según el SO;
no se promete conservar ese metadato controlado por el sistema.

La [matriz de 29 brechas](brechas_diccionario_pnda_paso84e.md) no cambia:
**1 resuelta, 13 parciales, 12 pendientes, 2 contradicciones y 1 no evaluable**.
No hay extracción satisfactoria para proponer nuevas secciones documentales de
contenido como evidencia. Los localizadores de enlaces no acreditan identidad
de estaciones, CRS, coordenadas, zona, HORA, unidades, calidad, licencia o
equivalencia editorial CSV–XLSX–DOCX. Las propiedades técnicas no sustituyen
afirmaciones editoriales localizadas.

No se accedió a CSV/XLSX institucionales, RAW, staging o SQLite operativos;
no se hicieron migraciones, descargas, instalaciones, Word, macros o QA/QC.
La autorización de un GET del 84-H **no se reutilizó** en este paso: hubo **0 GET**.

## 8. Git final y dictamen

Se ejecutaron `git diff --check` y la revisión directa de archivos nuevos,
enlaces locales y coherencia de tablas, sin errores. El HEAD permanece
**944151a**, rama **feature/suadc-http**, sin commits o push. Cambios finales:

```text
 M docs/adquisicion_docx_pnda_paso84h.md
 M src/spica/adquisicion/verificacion/docx/__init__.py
 M src/spica/adquisicion/verificacion/docx/_control.py
 M src/spica/adquisicion/verificacion/docx/_extraccion.py
 M src/spica/adquisicion/verificacion/docx/_paquete.py
 M src/spica/adquisicion/verificacion/docx/inspector.py
 M src/spica/adquisicion/verificacion/docx/modelos.py
?? docs/auditoria_relaciones_docx_paso84hb.md
?? src/spica/adquisicion/verificacion/docx/_hipervinculos.py
?? tests/test_hipervinculos_docx.py
```

**APTO CON RESTRICCIONES**: la separación de destinos pasivos y XML local quedó
demostrada con sintéticos y registrada en el archivo conservado. El documento
**no está habilitado para reconciliación documental**, porque el cuerpo sigue
fuera del alcance interpretado. La restricción nueva requiere otro diagnóstico
offline expresamente revisado, no ampliar controles sucesivamente o repetir GET.

Riesgos residuales: perfil cerrado con posibles falsos rechazos de documentos
legítimos; dependencia privada de CPython para DEFLATE; plazo/memoria cooperativos;
ausencia de validación XSD/renderizado completo y aislamiento frente a cambios de
un propietario malicioso. Omitir enlaces no autentica el emisor o destino.
Se espera revisión antes de cualquier reconciliación o interpretación científica.
