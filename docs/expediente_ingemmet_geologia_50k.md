# PASO 81 — Expediente técnico INGEMMET: geología integrada 1:50.000

Estado: **expediente documental preliminar, sin acceso remoto desde SPICA**.
El producto se selecciona para preparar una comprobación de metadatos; no existe
todavía autorización de consulta, adquisición de entidades ni conector operativo.

Documentos asociados: [matriz GIS](matriz_interoperabilidad_ingemmet.md) y
[plan de validación del PASO 82](plan_validacion_ingemmet_paso82.md).

## 1. Registro de evidencia y límites de confianza

| Evidencia | Procedencia | Qué permite afirmar |
|---|---|---|
| E-01 | Encargo del PASO 81 facilitado por el usuario; describe una revisión externa de páginas públicas de INGEMMET | Referencias y propiedades identificadas externamente, transcritas en este expediente |
| E-02 | Inspección local del repositorio, rama `feature/suadc-http`, HEAD `f3dac77` | Componentes, contratos y limitaciones de SPICA descritos en la matriz |
| E-03 | [Informe del PASO 80](readquisicion.md#resultado-de-verificación-del-paso-80) | Última suite reportada: 1.061 aprobadas; ejecución histórica, no repetida en el PASO 81 |

E-01 **no incluye una respuesta HTTP/JSON conservada en SPICA**, fecha de consulta
externa, identidad del revisor, hash, versión publicada ni extractos verificables
de términos de uso. La fecha de aquella revisión permanece desconocida. Las URLs
son referencias institucionales candidatas aportadas por el usuario, no endpoints
descubiertos o comprobados por este trabajo. No se visitaron enlaces.

Se distinguen los estados de la matriz: documentación primaria de la fuente,
identificación externa, comprobación local, verificación pendiente y capacidad no
disponible. **Ninguna propiedad del servicio se eleva aquí a comprobada en SPICA.**
Las decisiones de diseño son propuestas internas, no afirmaciones institucionales.

Los informes del [PASO 78](auditoria_adquisicion_multiinstitucional.md) reflejan
su evidencia histórica: entonces INGEMMET no tenía un producto espacial verificado.
E-01 aporta ahora un candidato concreto, sin invalidar ni reescribir esos informes.

## 2. Identificación del producto, servicio y capa

| Campo | Dato aportado / situación |
|---|---|
| Institución responsable declarada | INGEMMET, según E-01; autoría técnica, responsables de publicación y contactos aún no acreditados |
| Producto prioritario | Mapa Geológico Integrado del Perú a escala 1:50.000, según E-01 |
| Descripción de trabajo | Producto cartográfico geológico integrado candidato para contexto ambiental; no se ha inspeccionado su descripción institucional íntegra |
| Servicio | `SERV_GEOLOGIA_50K_INTEGRADA` |
| Tecnología identificada | Servicio con referencia ArcGIS REST `MapServer`; edición del software, versión y configuración no comprobadas |
| Capa prioritaria | `Litologia`, ID `7`, conservando el nombre e identificador aportados |
| Geometría declarada externamente | `esriGeometryPolygon` |
| Referencia espacial declarada externamente | Par `102100 / 3857`; definición completa y correspondencia de propiedades aún pendientes |
| Escala de origen declarada | `1:50.000`; no es una medición de precisión posicional |
| Cobertura espacial | El título refiere Perú; extensión numérica, continuidad, vacíos, hojas efectivamente integradas y ámbito de la capa 7 desconocidos |
| Publicación / actualización | Fechas, edición, revisión, historial y frecuencia desconocidos |
| Referencias científicas | Memorias explicativas, hojas, autores, metodologías, diccionario y bibliografía no aportados todavía |
| Condiciones de uso | Licencia, atribución exigida, redistribución y usos permitidos pendientes de documentación |

Referencias exactas aportadas en E-01:

- R-01 — [Servicio MapServer](https://geocatminnube.ingemmet.gob.pe/arcgis/rest/services/SERV_GEOLOGIA_50K_INTEGRADA/MapServer).
- R-02 — [Capa Litologia, ID 7](https://geocatminnube.ingemmet.gob.pe/arcgis/rest/services/SERV_GEOLOGIA_50K_INTEGRADA/MapServer/7).

No se construyen referencias `FeatureServer`, WFS, WMS, exportación o consultas de
entidades por analogía. La presencia de `MapServer` no acredita ninguno de esos
servicios ni una descarga vectorial completa. Tampoco acredita acceso anónimo
efectivo, ausencia de CAPTCHA o términos que autoricen automatización.

## 3. Propiedades de consulta identificadas externamente

| Propiedad referida en E-01 | Interpretación limitada | Falta para comprobarla |
|---|---|---|
| Formatos JSON, GeoJSON y PBF | Soporte de consulta declarado externamente; no hay una respuesta obtenida para ninguno | Metadatos primarios, ámbito servicio/capa, parámetros, representación y prueba autorizada independiente |
| Paginación | Capacidad anunciada externamente; no demuestra estabilidad, orden ni acceso completo | Propiedad concreta, documentación aplicable, comportamiento por capa y prueba acotada posterior |
| `MaxRecordCount` de `2000` | Límite de resultados anunciado; **no es el total de entidades** ni una garantía de que se devuelvan 2.000 | Valor y ámbito exactos en el JSON del servicio/capa; posibles otros límites |
| `esriGeometryPolygon` | Tipo de geometría referido; no demuestra topología, validez, completitud o dimensionalidad de cada entidad | Esquema, geometrías originales, variantes admitidas y comprobación estructural posterior |
| `102100 / 3857` | Identificadores de referencia espacial reportados | Objeto espacial original, namespace, correspondencia `wkid`/`latestWkid` si existen, WKT, datum, unidades y ejes |

Una respuesta HTTP 200 o JSON sintácticamente válido puede ser metadatos, un error
del servicio o un subconjunto de entidades. No prueba integridad de la colección,
vigencia de la cartografía ni éxito de una adquisición científica.

El expediente no determina cómo consultar por espacio, hoja, atributo o fecha.
La sintaxis real, parámetros admitidos, operadores, límites de geometría y
condiciones de acceso siguen pendientes. No se supone que un período de consulta
meteorológica sea aplicable a una capa geológica estática.

## 4. Atributos e identidad de entidades

Lista **no exhaustiva** de campos identificados externamente en E-01:

| Nombre original | Tratamiento en SPICA propuesto |
|---|---|
| `objectid` | Candidato a identificador técnico; confirmar si es el campo OID, tipo y estabilidad al republicar |
| `codi` | Código opaco; significado, dominio y unicidad desconocidos |
| `codiunihoja` | Identificador opaco; no deducir significado o relación con hojas sin diccionario |
| `etiqueta` | Atributo original; semántica y dominio pendientes |
| `unidad` | Atributo original; no confundir automáticamente con una unidad de medida |
| `tipo_unidad` | Atributo original; clasificación pendiente de diccionario |
| `litologia` | Atributo original; no traducir códigos ni normalizar categorías sin referencia verificada |
| `descrip` | Atributo original; conservar valores, nulos y codificación sin completar texto |

No se conocen todavía tipos, alias, longitudes, nulabilidad, dominios, claves,
campos de geometría, valores ni relaciones. La lista no demuestra que todos los
campos estén accesibles en una consulta ni que exista una clave persistente.

La identidad propuesta tiene niveles separados:

1. Institución/producto y referencia del servicio.
2. Recurso/capa identificado por servicio y ID `7`, contextualizado en publicación.
3. Entidad original identificada dentro de esa capa e instantánea adquirida.
4. Evento de adquisición y activo RAW, independientes del SHA-256 del contenido.

Hasta documentar una clave estable, `objectid` solo puede tratarse como referencia
técnica de una instantánea: no como código geológico global, código de estación o
identidad permanente entre publicaciones. Los códigos no se reconstruyen.

## 5. CRS, escala y limitaciones cartográficas

Se conserva literalmente el par `102100 / 3857` como información de E-01. No se
asigna automáticamente `EPSG:102100` ni se deduce qué identificador ocupa cada
propiedad del servicio. Aún falta una definición autorizada del CRS, datum,
unidades, orden de ejes, dimensionalidad y, cuando corresponda, referencia vertical
o época. Tampoco se conoce la referencia de salida de cada formato de consulta.

Escala cartográfica, resolución y precisión posicional son conceptos distintos:

- `1:50.000` describe la escala de origen referida, no una tolerancia geodésica.
- La resolución espacial o grado de detalle de las entidades no está documentado.
- No se ha aportado incertidumbre posicional cuantificada ni método de estimación.
- Zoom de visualización, teselas o cantidad de decimales no aportan por sí solos
  mayor exactitud de los límites cartografiados.

No se infiere precisión en metros, exactitud de contactos, cobertura completa ni
idoneidad para decisiones a escala de parcela. Se necesitarán metodología,
generalización, procedencia por hoja, revisión y condiciones de uso de cada mapa.
La integración puede combinar fuentes de distinta fecha/criterio: comprobarlo,
no asumir homogeneidad por el título del producto.

No se reproyecta, simplifica, corrige topología ni convierte geometría. Una futura
derivación deberá conservar originales, transformación/documentación, versiones,
parámetros, área de validez, incertidumbre y relación con los activos de origen.

## 6. Aplicaciones ambientales potenciales

| Aplicación futura | Evidencia y cautelas adicionales |
|---|---|
| Contexto de una estación o punto de muestreo | Coordenadas/CRS y precisión del punto, escala e incertidumbre del mapa, ubicación respecto a contactos y fecha de referencia |
| Identificación cartográfica de unidades litológicas | Diccionario y memoria verificados; conservar código y nombre originales junto a cualquier interpretación |
| Contextualización de anomalías geoquímicas | Métodos analíticos, QA/QC, unidades, matrices, condiciones de muestreo, línea base y contexto hidrogeológico |
| Contraste entre fuentes naturales y actividades antropogénicas | Evidencia independiente de actividades, mineralogía, transporte, temporalidad y otras hipótesis; coincidencia espacial no demuestra causalidad |
| Estudios hidrogeoquímicos | Hidrología, acuíferos, estructuras, permeabilidad, suelos, clima, química y escala adecuada, según el problema |

Estas aplicaciones **no están implementadas** por el PASO 81. Un polígono no
demuestra la litología puntual del subsuelo, la conectividad hidráulica ni una
fuente de contaminación. El mapa no prueba contaminación ni ausencia de impacto.
No se ejecutan cruces espaciales, análisis causal ni QA/QC científico.

## 7. Condiciones abiertas y dictamen

Antes del acceso: aprobar finalidad, rutas y parámetros exactos, origen, presupuesto
y conservación de evidencia. Antes de adquirir vectores: documentar derechos de
consulta/descarga/redistribución, identidad de publicación, CRS, esquema y criterio
de completitud; diseñar pruebas del mecanismo realmente publicado.

No se ha comprobado una licencia abierta ni autorización institucional. Que una
página sea pública no implica libertad de descarga masiva o redistribución. La
falta de términos aportados no demuestra prohibición ni ausencia de datos: exige
documentación y decisión separada. No se presupone una versión o frecuencia.

**Dictamen: APTO CON RESTRICCIONES para revisión documental y preparación del
PASO 82.** No es una declaración de aptitud para adquisición vectorial o uso
científico. El siguiente plan requiere aprobación independiente y no se ejecuta
en este paso.

## 8. Verificación del entregable

Se crean únicamente este expediente, la matriz GIS y el plan del PASO 82.
No se modifica código, dependencias, listas de orígenes ni contratos. Se revisan
UTF-8, coherencia de los metadatos, enlaces relativos y correspondencia con E-01/E-02.
Los enlaces externos se comprueban solo como texto, **sin solicitudes HTTP**.

Se ejecutan `git diff --check` y `git status --short`, junto con comprobación
separada de los tres archivos nuevos sin seguimiento. Los archivos previos
permanecen intactos respecto a `f3dac77`. Las 1.061 pruebas y versiones del entorno
son las reportadas por el PASO 80; no son una ejecución nueva de este paso documental.

No se accede a RAW, staging ni SQLite operativos, ni se verifican físicamente sus
archivos. No hay descargas, instalaciones, migraciones, incorporación de capas,
conectores, mapas definitivos, commits o push.
