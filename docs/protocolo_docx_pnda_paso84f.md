# PASO 84-F: protocolo propuesto de inspección documental DOCX

Fecha: **2026-11-05**. **Diseño, no inspector implementado ni prueba de un DOCX
real.** Complementa el [expediente y autorización propuesta](preparacion_docx_pnda_paso84f.md).
La inspección futura es offline, posterior al único GET autorizado y sobre sus
bytes identificados. No autoriza ejecutarlo. Ningún estado del motor se cambia.

## 1. Perfil mínimo y componentes reutilizables

El verificador existente aporta directorio ZIP acotado, rutas, duplicados,
compresión/cifrado, CRC/tamaños y XML sin DTD/entidades. Su reconocimiento DOCX
es básico: no extrae texto/tablas ni aplica los controles de contenido activo
de la rama XLSX a Word. La propiedad pública de uso documental excluye DOCX.
No se equiparará un resultado `COMPATIBLE` a seguridad completa o aprobación.

El futuro diagnóstico deberá reutilizar los controles de
[`verificacion/_xlsx.py`](../src/spica/adquisicion/verificacion/_xlsx.py),
[`PoliticaEstructura`](../src/spica/adquisicion/verificacion/modelos.py) y la
verificación física acotada del [arnés 84-C](../herramientas/piloto_pnda_84c.py)
sin llamar a su piloto operativo. Podrá seguir la separación texto/estructura del
[diagnóstico XLSX](../herramientas/inspeccionar_xlsx_84e.py), sin pasárselo como XLSX,
copiar su parser entero o relajar sus límites. Los helpers privados requieren
pruebas propias ante futuras modificaciones. No se necesita conversor Word,
renderizador, LibreOffice, COM, navegador, nuevas dependencias o intérprete de campos.

**Condición pendiente:** implementar y probar el diagnóstico mínimo en aislamiento
antes de usar una descarga para extraer afirmaciones; verificar también el arnés
del GET sin red. No se declara ese trabajo realizado en 84-F. Si no se prepara
o cambia el perfil, se detiene la operación para revisión, sin usar Word como
alternativa. La futura inspección debe carecer de rutas de red y escritura.

## 2. Presupuestos iniciales propuestos

Cotas del ensayo, no tamaños/estructuras atribuidos al documento desconocido.
No se aumentan ni se cambia de perfil automáticamente ante un límite.

| Recurso | Cota propuesta |
|---|---|
| Archivo comprimido físico / snapshot | 4194304 bytes (4 MiB); lectura/hash antes y después, sin carga ilimitada |
| Directorio ZIP | 128 entradas, central 131072 bytes, sin ZIP64 ni archivos multidisco |
| Lectura | Bloques 65536; lecturas de cabecera/directorio acotadas por el mayor de 131072/65557; 32 MiB de lecturas comprimidas acumuladas por pasada |
| Descompresión real | 16777216 bytes (16 MiB) totales por pasada; 2097152 (2 MiB) por entrada; expansión máxima 100:1 |
| XML | 2 MiB por parte; 100000 nodos acumulados por pasada; profundidad 32; token pendiente 65536 |
| Partes gráficas pasivas | Solo PNG/JPEG declarados, hasta 1 MiB por parte, incluidos en el total; contar/CRC, sin decodificar o renderizar |
| Estructura retenida en memoria | Snapshot hasta 4 MiB; árbol de una parte por vez hasta 2 MiB de XML; índice de 128 partes; no mantener árboles de todo el paquete |
| Extracción | Hasta 10000 párrafos, 100 tablas, 10000 celdas; 8192 caracteres por bloque literal y 524288 caracteres de texto emitido total; referencias/atributos localizados también acotados por XML/nodos |
| Resultados privados | JSON UTF-8 máximo 2 MiB, comprobado antes de escritura exclusiva; truncamiento por límite expresamente identificado, sin afirmar ausencia en lo no examinado |
| Tiempo/cancelación | Plazo cooperativo 5 s por inspección, Event y reloj monotónico en bucles/lecturas; comprobación antes de publicar un resultado completo |

Presupuestos de memoria estructurales, **sin prometer una cuota de RSS**: objetos,
buffers, Unicode y parser tienen overhead. Medir pico de asignaciones y duración
con sintéticos al implementar. El deadline no interrumpe una llamada bloqueada
del sistema/extensión; si se exige un máximo rígido se revisa aislamiento antes
de ejecutar. No se afirmarán límites efectivos hasta que se prueben.

## 3. Comprobaciones obligatorias antes de extraer texto

1. **Identidad física:** archivo regular dentro de la carpeta documental exacta,
   sin symlinks/junctions en componentes. Cotejar tamaño/hash con InformeDescarga,
   identidad del descriptor y firma antes/después. Un hash obtenido tras descarga
   no equivale a hash independiente del publicador. Rechazar archivo de cero bytes
   como DOCX, aunque su hash técnico sea calculable.
2. **ZIP:** cabeceras, EOCD/directorio y rangos locales coherentes, sin solapamientos,
   entradas duplicadas o ambiguas (casefold/decodificación), rutas absolutas,
   `..`, barras inversas, ADS/dispositivos o escapes. No llamar `extract`/`extractall`.
   Rechazar enlaces/archivos especiales, cifrado ZIP y métodos distintos de
   STORED/DEFLATED. Contar bytes reales y CRC de todas las partes, incluso las
   no interpretadas; nunca confiar solo en tamaños declarados.
3. **OOXML:** `[Content_Types].xml`, `_rels/.rels`, relación interna officeDocument
   única y parte principal `word/document.xml`, con MIME DOCX no habilitado para
   macros y raíz/namespaces WordprocessingML reconocidos. El perfil inicial
   usará Transitional `http://schemas.openxmlformats.org/wordprocessingml/2006/main`;
   Strict u otra estructura no probada se detiene como fuera de alcance, sin convertir.
   Contrastar tipos, nombres y relaciones; no aceptar solo por extensión o PK.
4. **Contenido activo, antes de aceptar DOCX:** revisar todo el inventario de nombres,
   MIME, relaciones y elementos. Rechazar VBA, paquetes macroEnabled, ActiveX,
   OLE/objetos incrustados, adjuntos/paquetes anidados, scripts, plantillas externas,
   altChunk/importaciones HTML y partes/tipos no contemplados. Las imágenes pasivas
   permitidas no se ejecutan; no hay OCR ni interpretación de gráficos.
5. **Relaciones:** validar IDs únicos, destino interno existente y normalizado
   dentro del paquete. Inventariar todas las `.rels`, no solo la principal.
   El primer perfil propuesto **detiene la extracción ante cualquier TargetMode
   External**, incluidos hipervínculos: registrar solo parte/ID/tipo y motivo,
   sin abrir destinos ni publicar URLs potencialmente sensibles. Es una restricción
   local deliberada, no prueba de contenido malicioso. Relajarla requiere revisión
   offline separada, sin repetir GET. Textos que parecen URL tampoco se abren.
6. **XML:** Expat con rechazo explícito de DTD, entidades y resolución externa,
   límites globales de nodos/profundidad/token/bytes y cancelación. Parsear datos
   como texto; no `eval`, comandos, transformaciones XSLT o generadores ejecutables.
   XML malformado, referencias rotas o parte inesperada detienen el resultado completo.
7. **Campos y revisiones:** no evaluar `w:fldSimple`, `w:fldChar`, `w:instrText`,
   DDE, fórmulas o resultados almacenados como valores oficiales. Registrar su
   presencia/localización, separar instrucciones/cache y excluirlos de afirmaciones
   confirmadas. Si no puede delimitarse un campo complejo, omitir el bloque y
   declarar incertidumbre. Cambios seguidos, comentarios, texto oculto o controles
   de contenido no justifican escoger una versión final: registrar presencia y
   alcance omitido; revisar antes de cerrar una brecha dependiente de ellos.
8. **Finalización:** verificar de nuevo hash/firma del mismo original, cobertura,
   presupuestos, ausencia de cancelación y errores. Emitir resultado técnico con
   alcance real, separado de integridad, autoría, vigencia y aplicabilidad. Toda
   limitación conserva pendientes y no se convierte en “no existe información”.

Perfil permitido previsto: documento, propiedades, relaciones, estilos,
numeración, settings, tema, encabezados/pies y notas referenciados, más imágenes
pasivas acotadas. Cada parte requiere nombre/MIME/relación coherentes; el perfil
exacto se concretará y probará en el diagnóstico, con rechazo por defecto de
partes no contempladas. No se extraerá texto de imágenes o contenedores embebidos.
El rechazo de contenido fuera del perfil no altera o limpia el archivo original.

## 4. Extracción conservadora y citas verificables

Se conservarán estructura y literales sin convertir códigos, unidades, HORA,
UBIGEO, zonas o fechas científicas. `xml:space`, tabulaciones y saltos se registran
sin reconstrucción editorial. La extracción no debe normalizar silenciosamente
espacios, guiones, ceros iniciales o caracteres de las definiciones.

| Elemento | Tratamiento mínimo previsto |
|---|---|
| Títulos/encabezados | Texto visible y estilo/posición declarados; un estilo no certifica título oficial. Encabezados/pies en sus partes propias, con relación a secciones cuando esté declarada |
| Párrafos | Identificador/localizador XML y secuencia de runs/textos/saltos; no renderizar o fusionar párrafos por apariencia |
| Tablas | Posición de tabla/fila/celda y párrafos propios; conservar gridSpan/vMerge u omitir con límite expreso, sin replicar contenido en celdas combinadas |
| Múltiples tablas/notas | Recorrer por estructura y orden original; no asumir que toda tabla es diccionario. Notas por ID/parte; separar autor/comentario de texto principal |
| Referencias | Citar texto visible si pasa el perfil y localización; no seguir vínculos o considerar probado un documento citado que no se inspeccionó |
| Identificación editorial | Extraer título/versión/fecha **solo donde estén declarados**. Propiedades created/modified/revision de OOXML son técnicas y editables; no vigencia editorial automática |
| Variables, estaciones y tiempo | Candidatos a afirmación literal con su contexto/unidad/alcance; no inferir código físico, frecuencia efectiva, zona o método por nombre parecido |
| Procesamiento/calidad | Mantener términos institucionales literales y alcance; sin equivalencias automáticas con QA/QC 0/1 SPICA |

Para evitar conteos engañosos, cada párrafo se emite **una vez** con su origen:
el recorrido de tablas remite a esos párrafos, sin duplicarlos mediante otro
recorrido `.//w:p`. Una parte de encabezado usada por varias secciones se extrae
una vez y conserva las referencias de uso. Conteos de párrafos, celdas y
afirmaciones no se suman como si fueran hechos distintos del mismo texto.

Cada registro de evidencia propuesto incluirá archivo/hash/tamaño, parte ZIP,
namespace, localizador estructural determinista, texto literal, contexto/párrafo
o tabla, estado técnico/alcance, interpretación separada, brechas relacionadas y
versión del diagnóstico. Ejemplo **sintético**, no ubicación real acreditada:

```text
word/document.xml#/w:document[1]/w:body[1]/w:tbl[2]/w:tr[3]/w:tc[1]/w:p[2]
w = http://schemas.openxmlformats.org/wordprocessingml/2006/main
```

Los índices cuentan hermanos del mismo nombre, desde uno. Registrar IDs OOXML
originales cuando existan, sin sustituir el localizador. No inventar páginas:
la paginación Word depende del renderizador y no se determina aquí. Un resumen
de revisor cita los bloques de los que deriva y no sustituye al literal.
El informe público debe escapar Markdown/HTML de texto no confiable, omitir
datos personales innecesarios y no crear enlaces activos automáticos.
El texto íntegro y los destinos externos no se publican en Git.

## 5. Pruebas sintéticas de aceptación, aún no ejecutadas

No se crea un inspector en 84-F; esta es la lista verificable exigida para su
implementación futura. Libros/documentos institucionales reales no serán fixtures.
Las pruebas deben usar memoria o temporales aislados, mocks y guardias de socket,
SQLite y escrituras fuera de fixtures; limpiar solo temporales propios.

| Grupo | Casos de aceptación/rechazo a demostrar |
|---|---|
| DOCX mínimo | Paquete válido con main/rels/MIME correctos; MIME/raíz/relación incorrectos, parte principal ausente o varios officeDocument |
| Texto y tablas | Párrafos, espacios/ceros/saltos, encabezados/pies, varias tablas, anidamientos, celdas combinadas y notas; sin doble conteo |
| Vacíos | Archivo de cero bytes rechazado; paquete vacío rechazado; DOCX estructural con body vacío distinguido como sin afirmaciones, sin inventar contenido |
| ZIP/CRC | No ZIP, directorio/cabeceras truncados, CRC alterado, tamaños falsos, rangos solapados, duplicados exactos/casefold/codificados y rutas peligrosas |
| Cifrado/expansión | Cifrado y métodos no admitidos; entradas/central/bytes declarados y reales/ratio/ZIP64; límites probados tanto en metadatos como en lectura |
| XML | Malformado, DTD, entidades internas/externas, profundidad/nodos/token/bytes excesivos; rechazo sin resolución de recursos |
| Relaciones/actividad | Referencias rotas, destinos externos con secreto ficticio, macro/ActiveX/OLE/altChunk/plantilla y contenido activo en **paquete que sí cumple marcadores básicos DOCX**; no basta probar solo nombres aislados |
| Campos/revisiones | Fórmula/DDE y cache no evaluados o promovidos; estado incompleto cuando no se delimiten; texto oculto/revisiones no elegido silenciosamente |
| Cancelación/límites | Antes de abrir, entre bloques/partes y antes del resultado final; plazo cooperativo con reloj inyectado; sin esperas reales y con cobertura declarada |
| Conservación | Identidad/hash antes/después iguales; modificación concurrente detectada, cierre de descriptores y ausencia de extracción/escritura sobre original |
| Determinismo/privacidad | Misma entrada/política produce igual inventario y localizadores; tiempos técnicos separados. Sin autor personal, credenciales o destinos sensibles en diagnósticos públicos |
| Sin red | Socket/HTTP/Word/subprocesos prohibidos durante inspección; ningún enlace externo provoca conexiones |
| Arnés de adquisición | MockTransport confirma una URL/GET, cero auth/cookies/range, identity y un intento; 3xx/206/429/5xx/TLS/timeout/HTML/vacío/tamaño/truncamiento/cancelación sin reintento, preservación exclusiva y estado real del manifiesto |

Las 1431 pruebas históricas y las 63 dirigidas del 84-E **no acreditan** estos
controles específicos de DOCX. No se declara ninguna de estas pruebas ejecutada
ahora. La suite pertinente y la revisión del arnés constituyen una condición
de detención si faltan antes del ensayo autorizado.
