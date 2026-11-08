# PASO 84-I — Reconciliación documental XLSX–DOCX PNDA/SENAMHI

Fecha: **2026-11-08**. **APTO CON RESTRICCIONES** para presentar esta
reconciliación documental a auditoría humana. No acredita calidad científica,
autenticidad independiente, vigencia aplicable ni habilita integración operativa.

Entregables complementarios:

- [Matriz trazable de 29 brechas](brechas_reconciliadas_pnda_paso84i.md).
- [Evidencias localizadas y consultas institucionales](evidencias_consultas_pnda_paso84i.md).

## Recuperación y corpus autorizado

Git inicial limpio, rama **feature/suadc-http**, HEAD
**b3c27481f827ab06b08389f8fd88d28f38b85c1c** (`b3c2748`, «SUADC:
compatibilidad OOXML y extraccion documental PNDA»). `git show --stat` confirma
que consolida los seis archivos del PASO 84-HC. Los cinco commits consultados:

```text
b3c2748 SUADC: compatibilidad OOXML y extraccion documental PNDA
ca08d73 SUADC: inspeccion segura de hipervinculos OOXML
944151a SUADC: adquisicion controlada y evidencia DOCX PNDA
32a7355 SUADC: auditoria y correcciones de seguridad del inspector DOCX
85a8c22 WIP: desarrollo parcial del inspector DOCX paso 84-G
```

Se revisaron los expedientes
[84-D](auditoria_metadatos_pnda_paso84d.md),
[reconciliación 84-D](reconciliacion_evidencias_pnda_paso84d.md),
[84-E](inspeccion_diccionario_pnda_paso84e.md),
[84-F](preparacion_docx_pnda_paso84f.md),
[protocolo 84-F](protocolo_docx_pnda_paso84f.md),
[mapa 84-F](mapa_brechas_docx_paso84f.md),
[84-G](inspector_docx_paso84g.md),
[84-H](adquisicion_docx_pnda_paso84h.md),
[84-HB](auditoria_relaciones_docx_paso84hb.md) y
[84-HC](auditoria_estructuras_docx_paso84hc.md), además de las matrices previas
y los inspectores existentes. No se modifican informes históricos.

Los resultados de 84-H (rechazo 0.1.0), 84-HB (incompleta 0.2.0) y 84-HC
(validada en alcance 0.2.1) siguen representando sus ejecuciones. La lectura de
84-I es otra comprobación; no sobrescribe sus JSON ni borra los rechazos anteriores.

## Comprobación física y lectura segura actual

Solo se autorizaron las dos raíces documentales conocidas. Se leyó primero
`C:\Users\Propietario\SPICA_EVIDENCIAS_PNDA_84E\procedencia.json`, verificando sus
**930 bytes** y SHA-256
`cc3159b4d5c23f4013a9d22b757259d8247bc4616a7342743f48e69bf2e361ae`.
La ruta XLSX se obtuvo de su campo **copia**; el campo origen temporal no se abrió.
No se buscó otro archivo ni se accedió al catálogo del piloto antiguo.

| Documento | Ruta exacta | Bytes y SHA-256 físicos antes/después |
|---|---|---|
| X, diccionario | `C:\Users\Propietario\SPICA_EVIDENCIAS_PNDA_84E\diccionario-1851039a07682a3f202314f6f8811fc616cb4ca2a486c9e737fd8cea62a4b4dd.xlsx` | **10815**; `1851039a07682a3f202314f6f8811fc616cb4ca2a486c9e737fd8cea62a4b4dd` |
| D, metadatos | `C:\Users\Propietario\SPICA_EVIDENCIAS_PNDA_84F\metadatos-pnda.docx` | **20664**; `7b9dcbd71c4d00798d1795edfd5ba0d15ad0aaab0297a7f0aba91532437a0d18` |

Recorrido actual: **2026-11-08T20:42:51.948413+00:00** a
**2026-11-08T20:42:52.418958+00:00**, usando Python **3.15.1** de `.venv`, con
`-B`. Se comprobó archivo regular, ruta absoluta dentro de la raíz autorizada,
sin enlaces simbólicos/junctions/reparse points ni escapes. Se reutilizaron
`_ruta_autorizada`, `_huella` y las API de inspección existentes; no se invocó
el piloto operativo ni el arnés de adquisición HTTP.

Se cotejaron los **nueve archivos originales**: tres de 84-E y seis de 84-F.
Inventarios exactos, tamaño, SHA-256 y firmas de dispositivo/inode/tamaño/mtime,
modos y atributos de archivo coincidieron antes/después del recorrido. Los
auxiliares se leyeron solo para su huella, salvo el manifiesto XLSX. La copia
histórica del procedimiento 84-H nunca se ejecutó o importó. La lectura puede
actualizar atime por decisión del SO; no se restaura ni se promete conservarlo.
Se volvió a comprobar la integridad al cierre del paso.

| Inspección actual | Resultado y límites relevantes |
|---|---|
| XLSX: diagnóstico 84-E **0.1.0** | 10 partes ZIP, una hoja **DiccionarioDatos**, 115 celdas XML y 79 con literal; **16 definiciones**, A5:F20; **0 fórmulas**, sin ejecución de formatos o celdas |
| DOCX: inspector **0.2.1** | **DOCUMENTO_VALIDADO_EN_ALCANCE**, conservación física True; 12 partes XML, **55 párrafos**, una tabla, **17 filas y 34 celdas**, tres destinos externos omitidos |
| Texto DOCX revisado | 53 párrafos incluidos vacíos: tabla filas 1–16 y cuatro párrafos directos. Dos párrafos de contacto se omiten de la revisión pública; no se publican autores/correos/destinos |
| Referencias | Hoja/celda para X; parte WordprocessingML y rutas Clark con tabla/fila/celda/párrafo para D. Los párrafos de tabla no se cuentan otra vez como nuevas observaciones |
| Fuera de alcance | Renderizado/XSD completos, destinos hyperlink, semántica del formato auxiliar, autenticación institucional independiente y aplicabilidad científica |

No hubo fórmulas ejecutadas, Word/Excel, extracción ZIP a disco o interpretación
de campos/revisiones. Se mantienen los controles y omisiones 0.2.1, sin relajar
el perfil para reconciliar. Los 55 párrafos no son 55 definiciones, ni las
34 celdas DOCX son 34 variables: X tiene 16 definiciones de campos y D una ficha
de metadatos del producto. No se suman esos conteos como resultados científicos.

El resumen saneado, sin copia binaria ni destinos o contactos, queda únicamente
en un temporal privado de esta sesión:

```text
%TEMP%\spica-84i-documental-6ae9f0550c214b91903eead8c0037a2b\evidencia-saneada.json
```

Tiene **131960 bytes**; contiene inventario X, fragmentos D saneados, referencias
y controles, no una nueva evidencia institucional ni un componente productivo.
La carpeta se creó con modo privado 0700. Durante el recorrido, la guardia
bloqueaba red, SQLite, procesos, mutaciones de originales y acceso operativo:
**0 intentos de red, 0 SQLite, 0 procesos, 0 escrituras prohibidas y 0 accesos
operativos**. Se permitió una escritura exclusiva de ese JSON temporal; sus
contadores se serializaron antes de abrirlo y la salida final contó esa escritura.
No se cambiaron ACL de carpetas previas ni se añadieron archivos a las evidencias.

## Correspondencia editorial

Los IDs de evidencia siguientes remiten al
[catálogo localizado](evidencias_consultas_pnda_paso84i.md), con los hashes X/D
completos y las referencias reales. Las paráfrasis no reemplazan los originales.

| Pregunta | Conclusión permitida | Evidencia y límite |
|---|---|---|
| ¿Misma publicación? | Coenumeración **histórica** bajo la misma página PNDA, no nueva comprobación remota | Expediente 84-D; campo URL D presente, destino no abierto ni autenticado. No se establece aquí igualdad de destinos o estado actual de la web |
| ¿Mismo producto descrito? | Coincidencia nominal y conceptual documentada: mismo título sustantivo, SENAMHI, redes y variables | X01/D01, X05/D02, X07/X08/D03–D05. X01 conserva un espacio final adicional; no se modificaron literales para comparar |
| ¿Misma edición? | **No demostrada** | D09 declara versión 1.0 y fechas; X no tiene edición editorial acreditada. No existe manifiesto de hashes/correspondencias aplicable a ambos originales |
| ¿Versiones diferentes? | Tampoco demostradas como dos ediciones incompatibles | Versión desconocida de X no significa una versión distinta de 1.0; fechas internas de archivos no son versiones editoriales |
| ¿Complementarios? | Sí, por su contenido documental | X define 16 campos; D aporta contexto, fuente, fechas, actualización y condiciones nombradas. Complementariedad no prueba equivalencia ni aplicación automática |
| ¿Correspondencia con el CSV operativo? | **Pendiente** | D13 describe Dataset/CSV y D14 cobertura Perú 2015–2024; no identifica por hash el CSV operativo ni la vigencia del diccionario para cada período |

La versión visible `1.0` se conserva como texto declarado en la ficha. No se
confunde con el inspector 0.2.1, AppVersion 16.0000 ni revision técnica 19.
Las fechas visibles `2024-05-30` no se convierten a UTC o timestamps de observación.
X11/D15 conservan fechas técnicas distintas, sin asumir otro producto,
sustitución editorial o contradicción por esa diferencia.

## Estaciones, coordenadas y temporalidad

**Identidad:** X02 distingue ID de registro y nombre ESTACION; D06 afirma que
cada registro es una medición en estación automática. No hay catálogo de códigos,
instalaciones, homónimos, traslados, instrumentos o vigencias acreditado en los
bloques revisados. GBON/RBON tienen definiciones compatibles (X05/D02), sin
membresía individual demostrada. No se inventan códigos ni fusionan nombres.

**Espacio:** X03 describe DMS, ejes X/Y y referencias geográficas genéricas; D08
enumera ubicación. No se acredita CRS/datum, precisión o serialización aplicable
al CSV. X04 sí declara msnm respecto al nivel medio del mar, sin realización
vertical ni vínculo por estación/época. No se asigna WGS84 ni coordenadas por
similitud de nombres. La cobertura D14 es de producto, no vida operativa.

**Tiempo:** FECHA y HORA conservan las especificaciones X06. D08 solo las enumera;
no resuelve cinco/seis posiciones, zona, cambios de reloj, extremos, etiqueta o
alineación de la ventana. FECHA_CORTE es el día de generación declarado X10;
D09 no lo define ni vincula con la edición del CSV. No se confunde con observación,
adquisición, creación o actualización de la ficha.

**Frecuencias:** horario en X07/X08/D03 se refiere a datos/agregados; mensual en
D11 a actualización del producto. Son etapas distintas: **no hay contradicción
por esa diferencia**. Tampoco se prueba su cadencia efectiva, continuidad o
muestreo de sensores. No se construyen timestamps, zonas o grillas esperadas.

## Variables, calidad y diferencias documentales

| Tema | Reconciliación permitida | Restricción conservada |
|---|---|---|
| TEMP | X07 declara promedio horario y °C; D04 aporta concepto general de temperatura, D03 horariedad | No se acredita muestreo, estadístico completo, ventana, instrumento o aplicabilidad de umbrales |
| HR | X07 declara promedio horario y %; D04 aporta relación porcentual conceptual y D03 humedad relativa horaria | No fija método del promedio, referencia instrumental, saturación, exposición o tolerancias |
| PP | X08 dice total horario con unidad literal **milimetros por hora**; D05 explica precipitación en **milímetros** como altura acumulada | Se conservan ambas declaraciones. No hay equivalencia demostrada ni una contradicción física inequívoca: la descripción general D no identifica explícitamente el código PP, método o ventana |
| Vacíos | D07 indica filtrar registros vacíos para el análisis de las tres variables | Es una instrucción documental no ejecutada; no define centinelas, causas, criterio conjunto/por variable o ventanas parciales. No autoriza eliminar originales |
| Validación | D03 contiene la afirmación institucional declarada «validados» | No se verificaron controles, etapas, flags, registros, ejecución, nivel de procesamiento o aplicabilidad del manual. No acredita validación científica por SPICA |
| Resolución y metrología | Tamaño de campo 10 en X no es especificación del sensor | No se infieren resolución, rango, precisión, incertidumbre o calibración desde decimales o definiciones |

Coincidencias de institución, redes, variables y horariedad no son evidencia
científica independiente: ambos auxiliares se atribuyen a SENAMHI. Se distingue
texto comprobado localmente de metadato declarado, interpretación provisional
y propiedad no verificada. La autenticidad no se deduce de hash, HTTPS o dominio
gubernamental; no se revisaron firmas o respaldo institucional independiente.

**Contradicciones conservadas:** S08/UBIGEO y T02/HORA contrastan las especificaciones
X con representaciones del **CSV histórico H01**. No se abrió el CSV ni se
recalcularon esos conteos. El DOCX no explica su causa; la hipótesis de ceros
perdidos no se convierte en reparación. No se reconstruyen HORA o UBIGEO.

**Tensiones y omisiones:** PP requiere aclaración de magnitud/unidad/ventana y
edición; no se fuerza su clasificación como contradicción o solución. D omite
ID/FECHA_CORTE de su enumeración general, lo que no contradice las 16 definiciones
X. Versiones/fechas desconocidas o distintas no son conflicto demostrado. Que
el corpus no documente una propiedad no significa que SENAMHI carezca de ella.

**Derechos:** D12 nombra licencia y acceso público; mejora la localización de una
declaración. No se abrió su destino o leyó el texto de términos ni se comprobó
edición, atribución y alcance por recurso/revisión. No se autoriza redistribuir
originales o dar por verificadas condiciones jurídicas a partir de ese nombre.

## Resultado de las 29 brechas y consultas

La matriz nueva propone **2 RESUELTA_CON_EVIDENCIA, 17 PARCIALMENTE_DOCUMENTADA,
8 PENDIENTE_DE_EVIDENCIA, 2 CONTRADICCIÓN_DOCUMENTADA y 0 NO_EVALUABLE**.
Total **29 IDs únicos**, con **27 brechas sin resolver**.

R01 permanece resuelta técnicamente para el XLSX. R02 pasa a resuelta por copia
DOCX identificada, íntegra e inspeccionada con fecha/versión declaradas y límites.
R04/R05/V04/V07 pasan a parciales por fechas/versión, licencia, recomendación sobre
vacíos y declaración de validación, respectivamente. **Cinco cambios y 24 estados
conservados**; no se alteró la matriz 84-E ni se aplicaron estos estados al sistema.
Las justificaciones, diferencias, contradicciones, consecuencias y evidencia
adicional de cada ID constan en las once columnas de la matriz.

La consulta para obtener una primera copia del DOCX ya no es necesaria. Continúan
Q1–Q7 con alcance ajustado: correspondencia de ediciones; estaciones/redes;
CRS/datum/metrología/UBIGEO; referencia temporal/HORA; métodos de variables,
PP y vacíos; qué significa validado y qué se aplicó; procedencia y términos de uso.
Fechas, versión, fuente, licencia nombrada y actualización se conocen como
declaraciones; se pide confirmación de alcance, no repetir preguntas ya contestadas.
No se envió correo o consulta ni se inventó una respuesta.

## Implicaciones y verificación de cierre

Puede continuar, previa revisión, la organización de afirmaciones y referencias
documentales. No se demostró necesidad de modificar contratos o crear componentes
productivos. Una integración futura deberá mantener la edición desconocida del
XLSX/CSV, la versión declarada de la ficha separada de vigencia, la literalidad de
PP, los estados pendientes y la historia de procedencia. No se actualizaron
catálogo, adaptadores, núcleo de interoperabilidad, reglas o resultados QA/QC.

Verificaciones actuales: identidades físicas, nueve controles originales,
coincidencia de los 29 IDs/estados anteriores con 84-E, ausencia de duplicados,
cinco transiciones justificadas, sumas de estados, referencias de hoja/celda y
WordprocessingML contra inventarios extraídos, enlaces locales, tablas,
codificación/finales y alcance exclusivo de tres archivos nuevos. Los informes
históricos y los archivos registrados permanecen sin diferencias con HEAD.

Resultado del cotejo automático: **28 evidencias X/D**, más el antecedente H01;
**10 referencias X y 22 D distintas** comprobadas contra el inventario, incluidas
rutas Clark y SHA; **13 tablas y 27 enlaces locales** correctos. Siete consultas
cubren las 27 brechas abiertas. El cotejo físico final concluyó a
**2026-11-08T20:56:12.912306+00:00**: nueve hashes/tamaños originales coincidentes,
inventarios 3/6 sin elementos inesperados y guardia final con todos sus contadores
en cero. No se atribuye al CSV histórico esa comprobación física actual.

Se ejecutan al cierre:

```powershell
git diff --check
git status --short
```

`git diff --check`: sin errores. Solo se crea documentación: **0 pruebas nuevas
y 0 tests unitarios ejecutados en 84-I**; no se repite suite o `pip check`.
Las **1537 pruebas aprobadas, 0 fallos/errores**, son el resultado **histórico de
84-HC**, no una corrida actual. Las comprobaciones documentales de este paso no
se suman como pruebas de la suite ni demuestran conformidad científica.

Git final conserva rama y HEAD, sin cambios de índice, commits o push:

```text
?? docs/brechas_reconciliadas_pnda_paso84i.md
?? docs/evidencias_consultas_pnda_paso84i.md
?? docs/reconciliacion_xlsx_docx_pnda_paso84i.md
```

**Cero conexiones externas, GET, descargas, instalaciones, Word/Excel, migraciones
o escrituras operativas.** No se accedió a RAW/staging/SQLite operativo ni al CSV;
por ello no se afirma una nueva huella de esos almacenes o una auditoría de
cambios de terceros. Se mantuvieron originales, literales y restricciones de
concurrencia/TOCTOU del modelo secuencial, sin reescribir fuentes ni controles.

**APTO CON RESTRICCIONES**: expediente documental listo para revisión, con
brechas y derechos pendientes. No integra metadatos automáticamente ni habilita
interpretación científica, conversiones, filtrado, QA/QC superior o siguiente paso.
