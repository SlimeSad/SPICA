# PASO 83-E: consulta propuesta y expediente de seguimiento a INGEMMET

## 1. Control del expediente

| Campo | Valor |
|---|---|
| Identificación interna del expediente | PASO 83-E / consulta documental INGEMMET; no es un número de trámite institucional |
| Fecha de elaboración | **2026-11-04T09:13:13Z**, reloj del entorno; corresponde a preparación local |
| Destinatario propuesto | Dirección de Geología Regional, INGEMMET |
| Correo propuesto | [consultasdgr@ingemmet.gob.pe](mailto:consultasdgr@ingemmet.gob.pe), aportado por el usuario; no validado independientemente |
| Remitente / datos de respuesta | Pendientes de completar y aprobar por el usuario |
| Estado de la comunicación | **BORRADOR PARA REVISIÓN — NO ENVIADO** |
| Fecha de envío / recepción | — / —; no ha ocurrido ninguna de ellas en este procedimiento |
| Número de trámite, respuesta o documento institucional | Desconocido; no se inventa |
| Respuestas y evidencias nuevas recibidas | Ninguna |
| Estado del piloto | **NO AUTORIZADO**, sin consultas `/query` |

La [consolidación de fuentes](fuentes_oficiales_ingemmet_paso83e.md) distingue
servidores, productos y niveles de evidencia. Este expediente no valida el correo,
abre sus enlaces ni autoriza el envío. La fecha de elaboración no acredita
vigencia de documentos o fecha de actualización institucional.

## 2. Comunicación concisa propuesta

**Asunto:** Consulta documental sobre el Mapa Geológico Integrado 1:50 000,
distribuciones GIS y condiciones de uso para SPICA.

**Para:** Dirección de Geología Regional — INGEMMET.

Estimados señores:

Desarrollamos SPICA, Plataforma de Investigación Científica Ambiental. Estamos
evaluando documentalmente una incorporación trazable de información geológica
y agradeceremos su orientación y referencias oficiales sobre seis puntos:

1. **Identidad del producto y servidores.** ¿Cuál es su identificación/edición
   oficial y qué relación existe entre los
   servicios `SERV_GEOLOGIA_50K_INTEGRADA` de `geocatmin.ingemmet.gob.pe` y
   `geocatminnube.ingemmet.gob.pe`? La referencia suministrada del primero describe
   actualización a agosto de 2025 y 1057 mapas 1:50 000; la evidencia histórica de
   SPICA corresponde al segundo, capa `7 — Litologia`. ¿Comparten producto,
   edición y cobertura o son publicaciones distintas?
2. **Distribución GIS.** ¿Existe un archivo o conjunto oficial completo de esa
   misma integración/capa? ¿Cómo se relaciona con los mapas y Shapefiles referidos
   por `SERV_MAPAS_GEOLOGICOS`? Solicitamos referencias de distribución, formato, edición,
   cobertura/hojas/vacíos, componentes y manifiesto de completitud.
3. **Condiciones de uso.** ¿Qué texto, versión y fecha de licencia/términos
   vigentes se aplican a cada
   servicio y distribución? Agradeceremos precisar consulta automática de
   atributos, descarga de geometrías, conservación local e investigación,
   transformaciones/mapas derivados, redistribución de originales y derivados,
   restricciones de terceros y atribución exacta. ¿La página GEOCATMIN indicada
   abajo cubre esos recursos y usos? ¿Qué cuotas u otras condiciones de acceso rigen?
4. **Microensayo de atributos.** Para MapServer Query de la capa 7 de
   geocatminnube, ¿está documentado
   el soporte conjunto de `f=json`, `where=1=1`, `outFields=objectid`,
   `returnGeometry=false`, `resultOffset=0`, `resultRecordCount=1` y
   `orderByFields=objectid ASC`? ¿Puede justificarse un máximo remoto de una
   entidad sin consulta preliminar? La propuesta para revisión es un único GET,
   64 KiB, sin autenticación, reintentos, redirecciones o geometrías y con
   evidencia privada. No existe autorización para ejecutarla.
5. **Estabilidad e historial.** ¿Cómo se identifica una edición/instantánea y se
   documentan cambios o sustitución de archivos? ¿Qué verificadores de integridad
   se publican? ¿Los OID se mantienen
   al editar o republicar y existe una clave institucional persistente?
6. **Referencia espacial y científica.** ¿Dónde están la definición autoritativa de CRS de
   origen/representación/salida, datum, ejes y unidades, el diccionario de
   atributos/códigos, memoria, escala y limitaciones de precisión?

Referencias a contrastar:

- [Servicio integrado, geocatmin](https://geocatmin.ingemmet.gob.pe/arcgis/rest/services/SERV_GEOLOGIA_50K_INTEGRADA/MapServer).
- [Servicio integrado, geocatminnube](https://geocatminnube.ingemmet.gob.pe/arcgis/rest/services/SERV_GEOLOGIA_50K_INTEGRADA/MapServer).
- [Mapas geológicos y distribuciones](https://geocatmin.ingemmet.gob.pe/arcgis/rest/services/SERV_MAPAS_GEOLOGICOS/MapServer).
- [Condiciones de uso GEOCATMIN](https://geocatminapp.ingemmet.gob.pe/complementos/Descargas/Licencia.html).

Agradeceremos documentación o indicación del área competente para resolver estas
consultas. La finalidad es definir una vía de adquisición y usos acordes con las
condiciones institucionales, preservando procedencia y originales.

Atentamente,

Equipo del proyecto SPICA

*Nombre del remitente y datos de respuesta pendientes de completar antes de
cualquier envío autorizado.*

## 3. Cobertura de las 12 aclaraciones anteriores

Las [preguntas Q-01 a Q-12 del PASO 83-D](derechos_uso_ingemmet_paso83d.md#4-aclaraciones-propuestas-no-enviadas)
se conservan sin borrar ni sustituir su registro histórico. Se agrupan así:

| Consulta agrupada | Preguntas originales cubiertas | Cobertura conservada y ampliación de contexto |
|---|---|---|
| C-01 / punto 1 | Q-01 | Identidad, edición/fecha, producto y capa; ahora distingue explícitamente los dos servidores y la descripción aportada de agosto de 2025/1057 mapas |
| C-02 / punto 2 | Q-02, Q-03 | Archivo exacto, equivalencia, cobertura, hojas/vacíos, componentes y completitud; separa mapas individuales de integración completa |
| C-03 / punto 3 | Q-04, Q-05, Q-06, Q-07, Q-08 | Vigencia/alcance de términos, automatización, cuotas, geometrías, archivo local, investigación, terceros, transformaciones, mapas, ambas redistribuciones y atribución |
| C-04 / punto 4 | Q-09 | Ruta/capa, siete parámetros exactos y justificación de límite remoto; ningún GET preliminar ni OID inventado |
| C-05 / punto 5 | Q-10, Q-12 | Instantánea, edición, claves/OID persistentes, cambios, reemplazos y evidencia de integridad |
| C-06 / punto 6 | Q-11 | CRS por ámbito, datum/ejes/unidades, diccionario, memoria y restricciones de escala/precisión |

## 4. Seguimiento por consulta

Estado inicial de todas las filas: sin envío y sin respuesta. Un guion indica
campo reservado, no una evidencia ni un valor institucional recibido.

| Consulta | Estado actual | Fecha de respuesta | Documento/emisor atribuible | Referencia de evidencia | Conclusión revisada / faltantes |
|---|---|---|---|---|---|
| C-01 | Pendiente de revisión del borrador | — | — | — | — |
| C-02 | Pendiente de revisión del borrador | — | — | — | — |
| C-03 | Pendiente de revisión del borrador | — | — | — | — |
| C-04 | Pendiente de revisión del borrador | — | — | — | — |
| C-05 | Pendiente de revisión del borrador | — | — | — | — |
| C-06 | Pendiente de revisión del borrador | — | — | — | — |

### Plantilla de incorporación futura de una respuesta

**Sin registros incorporados.** Completar únicamente cuando haya una respuesta
real recibida por un procedimiento autorizado; no usar la fecha de elaboración
como recepción ni inventar un número de expediente o una aprobación.

| Campo reservado | Valor futuro |
|---|---|
| Fecha real de recepción y precisión/zona conocidas | — |
| Emisor, cargo/área y canal; comprobación de atribución | — |
| Asunto, referencia/número y fecha del documento, si existen | — |
| Consultas C-01 a C-06 efectivamente respondidas | — |
| Servidor, servicio, capa, producto y edición cubiertos | — |
| Referencia autorizada de evidencia primaria y comprobación de integridad, si procede | — |
| Condiciones, excepciones y asuntos no resueltos | — |
| Revisor, fecha de revisión y conclusión con su fundamento | — |
| Decisión posterior del usuario y alcance autorizado, si llega a existir | — |

La respuesta se evalúa por su alcance y atribución, no solo por una dirección
de correo o un enlace. Si aporta nuevas URLs, versiones o términos, registrar
su procedencia y mantener separados los hosts. Una equivalencia institucional
de productos no prueba necesariamente identidad de bytes o instantánea.

No publicar correo completo, cabeceras sensibles, datos personales o adjuntos
en Git por defecto. Definir una conservación privada autorizada y mantener aquí
solo referencias/resúmenes permitidos. No escribir en RAW/SQLite operativo ni
archivar respuestas inexistentes para completar esta plantilla. Todo hash o
verificación futura debe corresponder a evidencia realmente disponible.

## 5. Decisión actual y siguientes controles

Una respuesta futura puede cerrar solo parte de las consultas; el silencio,
una referencia general o el nombre compartido del servicio no resuelven el resto.
Documentación primaria aplicable también podría aportar evidencia sin respuesta
por correo, bajo un procedimiento posterior permitido.

Antes de avanzar se necesita revisión del borrador, confirmación del destinatario
y remitente y una instrucción posterior de envío; no se contacta a la institución
en el PASO 83-E. Resolver derechos mínimos y límite remoto no sustituye la revisión
del ejecutor y evidencia privada ni la autorización operativa del usuario.

**Piloto `/query`: NO AUTORIZADO en ambos servidores.** Se conservan sin activar
las restricciones del [protocolo 83-D](protocolo_piloto_arcgis_paso83d.md).
El expediente está **APTO CON RESTRICCIONES para revisión**, sin envío ni
respuesta institucional y sin elección de una vía operativa.
