# PASO 83-E: consolidación de referencias oficiales de INGEMMET

## 1. Alcance y recuperación del estado

Elaboración: **2026-11-04**, reloj del entorno local. Git inicial limpio, rama
`feature/suadc-http`, HEAD **`d0a3e3f`**, `SUADC: evaluacion de alternativas y
derechos de uso INGEMMET`. El PASO 83-D está registrado con sus tres documentos.

Este incremento consolida exclusivamente documentos. **Piloto `/query`:
NO AUTORIZADO**, pendiente de revisión del usuario y de evidencia adicional.
No se implementa código ni se consulta ningún servicio. Las URLs y el correo
se conservan como referencias, sin comprobar disponibilidad, contenido vigente,
redirecciones, TLS, identidad del publicador o recepción de mensajes.

La [comparación REST/GIS del PASO 83-D](alternativas_adquisicion_ingemmet_paso83d.md),
su [auditoría de derechos](derechos_uso_ingemmet_paso83d.md) y el
[protocolo del piloto](protocolo_piloto_arcgis_paso83d.md) conservan su alcance
histórico. Esta consolidación añade procedencia por servidor, no equivalencias
ni autorización. La [consulta y seguimiento](consulta_institucional_ingemmet_paso83e.md)
es un borrador no enviado.

## 2. Registro documental de las referencias

Los IDs D83E-* son etiquetas de este expediente, no IDs institucionales,
adquisiciones, activos RAW o registros de una base de datos.

| Referencia | Localizador exacto | Procedencia y estado |
|---|---|---|
| D83E-01 | [Servicio integrado en geocatmin](https://geocatmin.ingemmet.gob.pe/arcgis/rest/services/SERV_GEOLOGIA_50K_INTEGRADA/MapServer) | Encargo 83-E: refiere descripción pública con actualización a agosto de 2025 y 1057 mapas 1:50 000. Contexto suministrado; no comprobado por SPICA |
| D83E-02 | [Servicio integrado en geocatminnube](https://geocatminnube.ingemmet.gob.pe/arcgis/rest/services/SERV_GEOLOGIA_50K_INTEGRADA/MapServer) | Encargo y expediente anterior. La evidencia histórica documentada por SPICA pertenece a este servidor; no es una comprobación nueva |
| D83E-02-C7 | [Capa 7 del servidor previamente inspeccionado](https://geocatminnube.ingemmet.gob.pe/arcgis/rest/services/SERV_GEOLOGIA_50K_INTEGRADA/MapServer/7) | Ruta histórica del [informe de metadatos](validacion_metadatos_ingemmet_paso82.md#25-resultado-final-offline-y-metadatos-esenciales-reales), E-06. Se revisa el informe versionado, sin abrir el archivo primario |
| D83E-03 | [Servicio de mapas geológicos y distribuciones](https://geocatmin.ingemmet.gob.pe/arcgis/rest/services/SERV_MAPAS_GEOLOGICOS/MapServer) | Encargo 83-E: referencias a productos descargables Shapefile. No se aporta ni comprueba un archivo completo del producto integrado |
| D83E-04 | [Condiciones de uso GEOCATMIN](https://geocatminapp.ingemmet.gob.pe/complementos/Descargas/Licencia.html) | Referencia aportada, ya recogida en 83-D; texto íntegro, vigencia y aplicación a cada recurso pendientes |
| D83E-05 | [consultasdgr@ingemmet.gob.pe](mailto:consultasdgr@ingemmet.gob.pe) | Contacto de la Dirección de Geología Regional suministrado por el usuario. Destinatario propuesto, sin validación independiente ni envío |

La fecha de elaboración de este documento no es fecha de consulta del servidor,
recepción institucional, vigencia de licencia o actualización de datos. No se
generan hashes de páginas no recuperadas ni se inventa una revisión documental
numérica de la fuente.

## 3. Matriz de identidades y procedencia

Las rutas de la tabla son HTTPS. Los nombres de servicio son identificadores
textuales de las rutas aportadas; no se presentan como identidades institucionales
persistentes. INGEMMET es el publicador referido por el contexto/expediente, no
una autenticidad nuevamente certificada por este paso.

| Ref. | Dominio y ruta | Institución publicadora referida | Identificador de servicio | Producto descrito | Capa | Fecha o versión declarada | Evidencia de identidad | Correspondencias demostradas en su alcance | Correspondencias no demostradas |
|---|---|---|---|---|---|---|---|---|---|
| D83E-01 | `geocatmin.ingemmet.gob.pe` + `/arcgis/rest/services/SERV_GEOLOGIA_50K_INTEGRADA/MapServer` | INGEMMET, según contexto aportado | `SERV_GEOLOGIA_50K_INTEGRADA` | Mapa Geológico Integrado del Perú, 1057 mapas a escala 1:50 000, según descripción referida | No identificada en el material de este servidor | Actualizado a **agosto de 2025**, según contexto; día, edición formal y comprobación externa desconocidos | Referencia y descripción suministradas en 83-E, sin primario recuperado aquí | Coincidencia textual del nombre de servicio con D83E-02 | Misma edición, contenido, capas, esquema, CRS, OID, licencia, réplica o sincronización con geocatminnube |
| D83E-02 | `geocatminnube.ingemmet.gob.pe` + `/arcgis/rest/services/SERV_GEOLOGIA_50K_INTEGRADA/MapServer` | INGEMMET, según expediente histórico | `SERV_GEOLOGIA_50K_INTEGRADA` | Producto integrado candidato del expediente anterior | Capa 7 documentada separadamente en D83E-02-C7 | Edición/fecha geológica del servicio no acreditadas | Referencias históricas del [expediente](expediente_ingemmet_geologia_50k.md); la comprobación completa servicio/capa sigue pendiente | Dominio/ruta coinciden con los documentados por SPICA y el protocolo anterior | Equivalencia con D83E-01; herencia de agosto de 2025/1057; vigencia o publicación inmutable |
| D83E-02-C7 | `geocatminnube.ingemmet.gob.pe` + `/arcgis/rest/services/SERV_GEOLOGIA_50K_INTEGRADA/MapServer/7` | INGEMMET, según expediente histórico | `SERV_GEOLOGIA_50K_INTEGRADA`, ámbito capa | `Litologia`, Feature Layer del producto candidato | **7**, nombre literal `Litologia` | E-06 evaluada offline el **2026-10-30T20:43:25.499524Z**; `currentVersion=11.2` es versión técnica declarada, no edición geológica | Informe local E-06: ID/nombre, OID `objectid`, Polygon y metadatos esenciales de ese archivo | Asociación de la evidencia histórica con esta URL/capa; subruta 7 del servicio D83E-02 | Igualdad con una capa 7 en otro host, fecha de datos, totalidad/estabilidad de entidades, coherencia completa entre primarios servicio/capa |
| D83E-03 | `geocatmin.ingemmet.gob.pe` + `/arcgis/rest/services/SERV_MAPAS_GEOLOGICOS/MapServer` | INGEMMET, según contexto aportado | `SERV_MAPAS_GEOLOGICOS` | Mapas geológicos con referencias de distribución Shapefile, según encargo | No identificada | Fecha/versión no aportadas | Referencia y función descritas en 83-E, sin primario recuperado aquí | Mismo dominio que D83E-01 y nombre/ruta de servicio distintos; anuncio de distribuciones aportado | Archivo integrado único o completo, correspondencia con capa 7 de geocatminnube, edición/cobertura/CRS/licencia de cada descarga |

En particular, E-06 documenta anuncios de `maxRecordCount=2000`, formatos
`JSON, geoJSON, PBF`, capacidades `Map,Query,Data` y `supportsPagination=true`.
Se mantienen asociados **a la capa y evidencia histórica de geocatminnube**.
No se trasladan al servicio geocatmin ni se presentan como pruebas funcionales.
El CRS de origen `4326 / 4326` y el de extensión `102100 / 3857` también conservan
ese ámbito; no acreditan un CRS de salida ni el de archivos desconocidos.

No se ha identificado aquí la capa 7 en geocatmin, ni se construye su URL o una
nueva ruta `/query` por analogía. El contraste completo servicio/capa permanece
desconocido (`None` en el informe previo); una relación jerárquica en el texto
de las URLs no lo sustituye.

## 4. Correspondencia de productos y distribuciones

| Relación evaluada | Lo que permite el expediente | Lo que falta |
|---|---|---|
| Dos hosts con `SERV_GEOLOGIA_50K_INTEGRADA` | Referencias a servicios de nombre coincidente en dominios distintos | Acreditar si son réplicas, migración, publicaciones independientes o ediciones diferentes; no se elige ninguna hipótesis |
| Descripción de agosto de 2025 y 1057 mapas | Declaración aportada para D83E-01, con precisión de mes y conteo de mapas | Texto primario, alcance, edición, cobertura y vínculo con capa 7 del otro host. No convertir el mes en una fecha con día inventado |
| 1057 mapas frente a entidades o archivos | Conteo referido de mapas integrantes | No es total de entidades, cantidad de descargas disponibles, cobertura exhaustiva ni manifiesto de un paquete |
| Mapas individuales frente al producto integrado | D83E-03 y la referencia de Carta Geológica Nacional del 83-D sugieren explorar distribuciones individuales | No acreditan un paquete completo de la integración, mismo esquema/topología/edición o disponibilidad de cada mapa |
| Archivo GIS frente a servicio REST | Dos vías potencialmente complementarias | Referencia oficial de distribución exacta, vínculo de producto/capa, fecha/edición, componentes, CRS, diccionario, integridad y derechos |

**No se acredita todavía una distribución GIS completa del producto integrado.**
Esto no demuestra que no exista. Tampoco se reconstruye una integración mediante
unión de hojas: sería otro proceso, con decisiones y validaciones propias, no una
descarga del original integrado. La escala nominal no mide precisión posicional.

Los tres documentos del PASO 83-D conservan sus conclusiones: no hay elección
operativa justificada por este nuevo contexto, y no se convierte el anuncio de
Shapefile en una URL de descarga o un recurso catalogado. Una futura equivalencia
documentada no implica igualdad de bytes, licencia común o autorización de red.

## 5. Licencias y preparación de la comunicación

La [matriz de diez operaciones de uso del 83-D](derechos_uso_ingemmet_paso83d.md#2-matriz-de-operaciones-y-permisos)
sigue vigente como evaluación de evidencia disponible. El contexto adicional no
resuelve vigencia, aplicación por host/producto/capa, permiso de automatización,
conservación local, investigación, transformaciones, mapas derivados o
redistribución de originales/derivados, ni fórmula exacta de atribución.
No se deduce permiso común por compartir institución, nombre o portal de licencia.

Se prepara una comunicación a la Dirección de Geología Regional, con el correo
propuesto aportado, agrupando las 12 preguntas Q-01 a Q-12 en seis consultas.
El [expediente de seguimiento](consulta_institucional_ingemmet_paso83e.md) contiene
fecha, borrador, correspondencia con las preguntas originales y plantillas para
respuestas/evidencias. **No enviado; sin respuesta institucional registrada.**

## 6. Decisión y trabajo independiente posible

No toda incertidumbre requiere necesariamente una respuesta por correo: puede
resolverse con documentación primaria aplicable obtenida o aportada por una vía
posteriormente autorizada. Si el alcance de los términos o la equivalencia sigue
ambiguo, se necesita aclaración institucional. Ninguna respuesta o documentación
autoriza automáticamente la ejecución: se mantiene la revisión del usuario.

| Área | Qué podría avanzar sin respuesta institucional | Qué necesita evidencia adicional / decisión |
|---|---|---|
| Identidad y procedencia | Diseño offline de registro por URL exacta, host, servicio, capa y evidencia; estados de correspondencia desconocida/documentada | Fusionar o declarar equivalentes recursos/ediciones exige vínculo documental verificable |
| Transporte y robustez | Revisar políticas existentes y diseñar futuras pruebas sintéticas de límites, errores y cancelación | Conectar a cualquier host/ruta, incluso metadatos, requiere un alcance nuevo expresamente autorizado |
| Validación GIS | Diseñar contratos, límites de contenedores, separación de CRS y fixtures inventadas, conservando originales | Interpretar geometrías institucionales requiere formato/esquema/CRS/diccionario y permisos aplicables |
| Integridad y readquisición | Diseñar trazabilidad de adquisición/activo/hash, manifiestos y pruebas sintéticas sin datos operativos | Declarar edición, cobertura, completitud o cambios institucionales necesita antecedentes reales acreditados |
| Permisos y seguimiento | Completar el borrador y criterios de revisión de evidencias; mantener desconocidos explícitos | Aprobar usos o redistribución exige términos aplicables; envío también requiere instrucción posterior |
| Piloto mínimo | Conservar el simulador y revisar documentalmente sus siete parámetros, sin habilitar HTTP | Límite remoto de una entidad, ruta/soporte vigentes, derechos mínimos, evidencia privada, ejecutor revisado y autorización del usuario pendientes |

La tabla delimita **posibles encargos posteriores**; no implementa ninguno en
83-E. Se reutilizaría la infraestructura común de SPICA, sin crear otro cliente,
almacén o conector por cada host. Su reutilización tampoco concede acceso a datos.

**Estado operativo final: `/query` NO AUTORIZADO en ambos servidores.** El
protocolo candidato existente permanece vinculado exclusivamente a geocatminnube,
sin sustitución de host ni traslado de autorizaciones históricas. Aún faltan
equivalencia/edición/distribución, términos aplicables y garantías del microensayo.
No se activan RAW, staging, SQLite, ingesta, QA/QC ni procesamiento geológico.

## 7. Verificación y dictamen del incremento

Se crean este documento y el expediente de consulta; se añaden notas de continuidad
a los tres documentos del 83-D, conservando su historia. No se modifica código,
pruebas, configuración, dependencias ni infraestructura operativa.

Se ejecutaron `git diff --check`, `git status --short`, inventario
de nuevos archivos y revisión de UTF-8, espacios, tablas, enlaces/anclas y cobertura
de las 12 aclaraciones. Los enlaces HTTPS y mailto se revisan solo como texto:
no se abre navegador, servicio ArcGIS, correo o archivo GIS.

Resultado: cinco documentos revisados, sin errores de formato, tablas, bloques o
espacios; **36 enlaces locales con sus anclas**, **7 URLs HTTPS distintas** y
**1 mailto distinto** comprobados exclusivamente como texto/localizadores.
Las **12 preguntas originales** están cubiertas una vez cada una en la matriz de
**6 consultas**; los **7 parámetros** del borrador coinciden con las constantes
del contrato 83-C, por lectura estática sin importar SPICA. La comprobación local
usó el Python de `.venv` con `-B`, sin ejecutar pruebas unitarias ni llamadas de red.

Git final: misma rama y HEAD iniciales; los tres documentos del 83-D solo reciben
notas al final, **40 líneas añadidas y ninguna eliminada**, y dos documentos nuevos:

```text
 M docs/alternativas_adquisicion_ingemmet_paso83d.md
 M docs/derechos_uso_ingemmet_paso83d.md
 M docs/protocolo_piloto_arcgis_paso83d.md
?? docs/consulta_institucional_ingemmet_paso83e.md
?? docs/fuentes_oficiales_ingemmet_paso83e.md
```

`git diff --check` sin hallazgos; los archivos nuevos se revisan por separado,
ya que ese comando no los incluye. No se modifica código, pruebas ni configuración.

No se repite la suite ni pip check: el incremento es documental. **0 pruebas
nuevas; 1331 aprobadas es la referencia histórica del PASO 83-C**, no una ejecución
del PASO 83-E. No se reabre evidencia primaria, RAW, staging o SQLite operativos,
ni se comparan sus hashes. No hubo instalaciones, migraciones, commits o push.

**Dictamen: APTO CON RESTRICCIONES para revisión documental y de la comunicación
propuesta.** No autoriza envío, consultas institucionales o adquisición.
