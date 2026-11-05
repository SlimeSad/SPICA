# PASO 84-A: núcleo de interoperabilidad espacial y temporal offline

## 1. Alcance y antecedentes

Git inicial limpio en `feature/suadc-http`, HEAD **`00fc44b`**,
`SUADC: consolidacion documental de fuentes INGEMMET`: PASO 83-E registrado.
Entorno comprobado con `.venv`: Python **3.15.1**, HTTPX **0.28.1**, SQLite **3.53.4**.

Se añade `spica.interoperabilidad`, sin alterar HTTP, RAW, catálogo, planificador,
consultas locales, vectorial, inspector ArcGIS o QA/QC. Se evalúan dos instantáneas
documentales aportadas, no registros/archivos institucionales. No hay consultas,
almacenamiento, parsing de observaciones, operaciones GIS o asociaciones ejecutadas.

El usuario informa en el encargo 84-A que el investigador envió la consulta a
INGEMMET. No se aportan fecha/copia del envío ni respuesta registrada. Se conserva
ese estado como información contextual, sin inventar comprobantes ni reescribir
el [borrador histórico del 83-E](consulta_institucional_ingemmet_paso83e.md).
El piloto `/query` continúa **NO AUTORIZADO** en ambos servidores.

## 2. Arquitectura y reutilización

| Componente | Responsabilidad |
|---|---|
| `interoperabilidad/modelos.py` | Contratos congelados, validaciones de estructura, originales e identidades |
| `interoperabilidad/evaluador.py` | Función pura `evaluar_aptitud(a, b, dimension)`, sin reloj, I/O o reglas institucionales |
| `interoperabilidad/__init__.py` | Exportaciones explícitas de la API experimental |
| `tests/test_interoperabilidad_modelos.py` | Fixtures inventadas, inmutabilidad, metadatos, revisiones y compatibilidad |
| `tests/test_interoperabilidad_evaluador.py` | Estados, faltantes, contradicciones y barreras del evaluador |

Se reutilizan directamente:

- `Fuente`, sin modificar ni normalizar sus identificadores originales.
- `ProcedenciaCatalogo` y `EstadoVerificacion`: referencia, método, evidencia y
  fecha técnica de revisión. Esa fecha no pasa a ser fecha de observación.
- `ReferenciaEspacial` vectorial para conservar exactamente `wkid/latestWkid`.
  El contrato nuevo también admite una declaración textual sin resolverla.
- `instante_utc` y `validar_intervalo`: validan instantes ya localizados, orden
  absoluto, horas inexistentes y `fold`. No localizan fechas desconocidas.
- Estrategia de revisiones/evidencia documental del catálogo, **solo como
  infraestructura futura de integración**; este paquete no abre ni escribe catálogos.

El catálogo importa transitivamente definiciones de persistencia/RAW existentes.
Importar el núcleo nuevo no instancia almacenes, no conecta SQLite y no carga
HTTPX, transporte HTTP o integración HTTP→RAW. No se añade un segundo catálogo,
cliente, diario o sistema de versionado. El código nuevo solo usa biblioteca estándar.

## 3. Contratos nuevos

| Contrato | Campos y significado |
|---|---|
| `IdentidadRecurso` | Fuente, ID original de recurso, ID de producto opcional y localizador opcional. El localizador distingue publicaciones/hosts; nunca se abre o normaliza |
| `Respaldo` | Estado desconocido/declarado/verificado y procedencia opcional. Verificado exige procedencia con referencia de evidencia |
| `CRSDeclarado` | Ámbito GEOMETRIA/EXTENSION/ORIGEN, declaración original textual o ReferenciaEspacial, referencia de definición, unidades de los dos ejes y respaldo |
| `MarcoEspacial` | Representación puntual/vectorial/raster/desconocida, geometría declarada, ubicación original, identidad/ambigüedad, coordenadas XY, CRS por ámbito, extensión, cobertura anunciada/observada, precisión, incertidumbre y respaldos separados |
| `PeriodoTemporal` | Extremos homogéneos date o datetime, respaldo y límites inclusivos explícitos u omitidos como desconocidos |
| `MarcoTemporal` | Pares originales de fecha/hora, fecha interpretada opcional, resolución, zona y convención declaradas, períodos de observación/publicación/vigencia, adquisición, incertidumbre y respaldo de la interpretación |
| `RecursoInteroperable` | Identidad, revisión local de metadatos y procedencia, marcos opcionales, versión institucional, atributos, condiciones de uso, referencias de correspondencia, revisión sustituida y contradicciones aportadas |
| `ResultadoAptitud` | Las dos instantáneas originales, dimensión, estado, referencias disponibles, motivos, faltantes, contradicciones, restricciones y versión del evaluador **0.1.0** |

Los contratos son `dataclass(frozen=True)` y exigen tuplas tipadas; no retienen
listas o diccionarios mutables. Las cadenas se validan sin recortarlas. Se
preservan valores Decimal/int/float finitos sin convertirlos, y se rechazan bool,
NaN o infinitos como coordenadas. No se imponen rangos geográficos con CRS desconocido.
Los pares originales preservan incluso valores vacíos y ceros; no reconstruyen
la serialización de un archivo, que sigue siendo otra evidencia.

Validaciones: extremos temporales coherentes y ordenados, extensión no invertida,
ámbitos de CRS únicos, estados sin afirmar coordenadas ausentes como verificadas,
intervalos puntuales/civiles no vacíos y fechas de adquisición con offset conocido.
Las referencias permanecen opacas; no se descargan ni se comprueba físicamente
la evidencia apuntada. El código no certifica su autenticidad o suficiencia jurídica.

Límites de entrada: textos de 4096 caracteres; colecciones documentales de hasta
64 elementos, tres ámbitos CRS, dos coordenadas, cuatro límites de extensión,
16 referencias de correspondencia por recurso. El resultado admite hasta 64
referencias de evidencia. Son presupuestos técnicos, no umbrales científicos.

## 4. Estados y criterio de evaluación

El objetivo específico de esta versión es **preparar una posible alineación
directa posterior**, no demostrar que los recursos coincidan en lugar/tiempo ni
aprobar cualquier comparación científica. Los recursos deben identificar su
producto y tener procedencia con referencia de evidencia para alcanzar aptitud.

| Estado | Cuándo se devuelve |
|---|---|
| `APTO_ESTRUCTURALMENTE` | Se satisfacen los requisitos documentales del subconjunto evaluado, sin faltantes o contradicciones. No ejecuta asociación ni aprueba uso científico |
| `PENDIENTE_DE_EVIDENCIA` | El marco existe pero hay valores, verificación, incertidumbre o correspondencias necesarias pendientes |
| `INCOMPATIBLE` | Contradicciones documentales detectadas o períodos documentados sin soporte común para la alineación directa planteada |
| `NO_EVALUABLE` | Falta alguno de los marcos de la dimensión solicitada o se pide evaluar raster, todavía fuera del subconjunto |

Precedencia para AMBAS: incompatibilidad/contradicción, no evaluable, pendiente,
apto. Se preservan los faltantes y motivos secundarios; una dimensión apta no
oculta otra pendiente. Una dimensión no seleccionada no introduce requisitos
espaciales/temporales adicionales; identidad/procedencia y contradicciones del
recurso siguen siendo controles comunes.

Los motivos y faltantes son códigos con prefijos `r0`/`r1`, correspondientes al
orden de entrada. No se imprimen nombres, cuerpos o mensajes institucionales.
Las contradicciones aportadas se referencian por índice; su descripción original
permanece en la instantánea. Orden y resultados son deterministas para las mismas
entradas; no hay reloj ni consulta de estado externo.

Dos instantáneas de la misma identidad y revisión local con distinto contenido
son incompatibles. El contraste documental distingue isoformat, fold y clave
de zona: no usa la igualdad datetime de Python para ocultar diferencias de fold.
Un localizador distinto mantiene separadas las publicaciones aunque coincidan
los identificadores originales. Aptitud no significa equivalencia entre ellas.

## 5. Política espacial y CRS

Para preparación puntual se requieren coordenadas documentadas como verificadas.
Para vectorial se requieren geometría declarada y extensión documentadas como
verificadas; eso solo prepara metadatos, no inspecciona vértices o archivos.
Toda coordenada aportada, incluso en un marco vectorial, necesita su respaldo.
Raster puede representarse en el contrato, pero no obtiene aptitud en esta versión.

Ambos casos requieren cobertura **observada** respaldada, precisión e incertidumbre
documentadas, y CRS de geometría con definición/unidades/respaldo. La identidad de
ubicación ambigua queda pendiente; afirmar a la vez verificación y ambigüedad de
esa identidad es una contradicción. No se crea un código de estación por nombre.
Puede prepararse un punto sin identificador de estación si su posición está
documentada; eso no le atribuye identidad física permanente.

Si se aporta extensión, se comprueban su respaldo y su CRS de EXTENSION. No se
usa como sustituto del CRS de GEOMETRIA. Los CRS de geometría, extensión y origen
pueden ser diferentes legítimamente; no se comparan coordenadas entre esos ámbitos.
El CRS de ORIGEN se conserva documentalmente, sin asignarlo a la salida.

Las declaraciones de CRS de geometría de ambos recursos deben coincidir
literalmente para la preparación directa. Si difieren, queda pendiente una
correspondencia: no se resuelven aliases como 102100/3857, códigos EPSG, WKT o
transformaciones. Dos declaraciones idénticas con unidades de ejes contradictorias
se señalan como incompatibles. Referencias documentales de definición distintas
no se consideran por sí solas definiciones diferentes.

No se calculan distancias, áreas, intersecciones, reproyecciones o geocodificación.
No se comprueba solapamiento de extensiones o pertenencia de puntos a polígonos.
Igual distrito/UBIGEO, nombre o coordenadas declaradas no acreditan asociación.
La escala de producto no llena precisión o incertidumbre faltantes. Sus descripciones
son documentación aportada, no medidas calculadas o umbrales interpretados por el motor.

## 6. Política temporal

Los originales se mantienen separados de `fecha_observacion` y de los intervalos
interpretados. No hay parser HORA/FECHA en este núcleo, reconstrucción de ceros,
inferencia de calendario, zona o código de estación. Un adaptador futuro debe
aportar interpretación explícita y evidencia; ninguno se implementa aquí.

Para aptitud se requieren período de **observaciones**, interpretación y límites
respaldados, resolución, convención, zona declarada e incertidumbre documentadas.
Adquisición, publicación y vigencia de metadatos no rellenan observaciones ausentes.
No se exige que sus fechas coincidan ni se compara un GET con la fecha de medida.

- `date` sigue siendo fecha civil: no se transforma en datetime/UTC. Solo se
  prepara alineación civil si las convenciones, resolución y zona documentadas
  coinciden; límites exclusivos se evalúan como fechas discretas.
- Un datetime naive no se localiza aunque exista una etiqueta de zona: queda
  pendiente de una interpretación resuelta. No se asignan UTC, UTC-5 o America/Lima.
- Para datetime aware se reutilizan claves UTC **solo de instantes ya resueltos**,
  conservando objetos, offset y fold originales. La etiqueta de zona debe estar
  vinculada literalmente al nombre/key del tzinfo; aliases no resueltos quedan
  pendientes. Declarar UTC con desplazamiento distinto de cero es contradictorio.
- Distintas convenciones, resoluciones o representaciones date/datetime quedan
  pendientes de correspondencia; no se agregan frecuencias ni se transforma una
  aparente igualdad de fecha en equivalencia temporal.

Con convenciones compatibles y períodos respaldados, se comprueba únicamente si
sus límites admiten soporte temporal común. Si no lo admiten, INCOMPATIBLE para
esa alineación; no significa que los datos sean erróneos ni que una investigación
de cambios entre épocas sea imposible. No se materializa una intersección ni se
asocian observaciones. Una fecha interpretada fuera de su período declarado sí
produce una contradicción documental. Los límites de horas repetidas se contrastan
en orden absoluto, sin colapsar folds.

`vigencia_metadatos` se almacena separadamente, pero la vigencia **actual** no se
evalúa sin reloj/política adicional. Todos los resultados declaran esa limitación.
La validez científica, derechos y actualización vigente del recurso tampoco se
aprueban automáticamente por obtener APTO_ESTRUCTURALMENTE.

## 7. PNDA/SENAMHI e independencia institucional

Se revisaron [consultas civiles locales](consultas_locales.md),
[perfilado de estaciones](perfilado_meteorologico.md) y la
[política temporal](politica_temporal.md). ESTACION es un nombre literal, UBIGEO
territorio declarado y HORA conserva ambigüedades de anchura/interpretación.
Una tupla de ubicación estable no demuestra instalación física única; una cadena
de cinco caracteres no autoriza recuperar un cero o fijar una zona.

Las pruebas nuevas usan encabezados/textos inventados, sin abrir el CSV o diccionario
institucionales. No se transfieren coordenadas, fechas o estaciones reales al núcleo.
No hay reglas de INGEMMET, SENAMHI, ANA u OEFA ni deducciones a partir de sus nombres.
Cada fuente, producto, localizador y revisión mantiene su ámbito independiente.

La [consolidación INGEMMET](fuentes_oficiales_ingemmet_paso83e.md) continúa aplicándose:
los dos servidores no son equivalentes automáticamente, una fecha declarada en uno
no pasa al otro, y los mapas individuales no acreditan una integración completa.

## 8. Incorporación posterior de evidencia y revisión

Estrategia implementada en memoria: crear una nueva `RecursoInteroperable` o usar
`dataclasses.replace` con nueva `revision_metadatos`, procedencia y, cuando proceda,
`sustituye_revision`. Los resultados retienen las instantáneas anteriores completas;
no se modifican al reevaluar. La revisión local no sustituye `version_institucional`,
que puede seguir desconocida. No se implementan auto-incrementos ni un diario nuevo.

Procedimiento futuro, **no ejecutado**:

1. Recibir la respuesta/documento por una vía autorizada y revisar atribución,
   alcance, producto, host, edición y cláusulas; no convertir correo en permiso global.
2. Registrar las referencias y revisiones pertinentes mediante la infraestructura
   de [evidencia y catálogo existente](registro_evidencias.md), respetando sus tipos,
   política de cambios y conservación. No escribir contratos nuevos en tablas privadas.
3. Un adaptador revisado construiría la nueva instantánea con las afirmaciones
   realmente respaldadas; condiciones/versiones/CRS/precisión siguen siendo datos.
4. Reevaluar la pareja y conservar ambos resultados y el motivo del reemplazo.
   Los controles de historial y conflictos del catálogo siguen siendo responsabilidad
   de esa integración; este núcleo no garantiza unicidad global de revisiones.

No hay persistencia/serializador nuevo de estos contratos, ni adaptador de respuestas
institucionales, vectorial o estaciones. La persistencia de los metadatos nuevos
requiere un mapeo posterior revisado, sin afirmar que el catálogo ya admite sus campos.
Las referencias de correspondencia se conservan, pero no se interpretan para resolver
alias o ejecutar transformaciones. Una futura regla de equivalencia necesitaría
contrato y evaluación propios, no una excepción institucional en HTTP/RAW.

## 9. Pruebas y verificación

Fixtures exclusivamente sintéticas; no se utilizan datos institucionales como
fixtures. Se cubren coordenadas verificadas/declaradas/ausentes, definición y
ámbito CRS, cobertura, precisión/incertidumbre, contradicciones, procedencia,
fuentes/hosts distintos, ambigüedad de identidad, zonas/convenios, períodos y
límites, fold, originales preservados, revisiones, determinismo y ausencia de I/O.

Se ejecutan con Python de `.venv`, `-B` y PYTHONPATH temporal hacia `src/`:

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -B -m pip check
git diff --check
git status --short
git ls-files --others --exclude-standard
```

La suite completa contrasta sus IDs con los **1331 anteriores** del HEAD inicial,
detectando faltantes o duplicación de IDs. Su log verbose y resumen quedan en el
directorio temporal de comprobación del PASO 84-A, fuera de Git. La guardia Python
bloquea sockets/DNS y accesos a SPICA_DATOS/evidencia institucional histórica,
incluidos los hijos que heredan el entorno. Las pruebas RAW previas utilizan sus
propios temporales sintéticos; no se ejecutan sobre el almacenamiento operativo.

Se ejecuta la suite con permisos normales del usuario para respetar los temporales
privados de Python 3.15, sin cambiar ACL. Se revisan aparte sintaxis, duplicados,
archivos sin seguimiento, enlaces, formato y cambios fuera del alcance.

Resultado final: **1388 pruebas ejecutadas y aprobadas, 0 fallidas y 0 errores**,
en **154.919 s**. Son **1331 anteriores + 57 nuevas**; todos los IDs anteriores
aparecen una vez, sin faltantes ni IDs duplicados. `pip check`:
**No broken requirements found.** El segundo pase completo incluye la regresión
que exige respaldo de coordenadas aportadas también en un marco vectorial.

Se comprobaron sintaxis/compilación en memoria sin `.pyc`, definiciones no
duplicadas, UTF-8, espacios, finales y enlaces locales de los seis archivos nuevos.
`git diff --check` no presenta hallazgos; no incluye archivos sin seguimiento,
que se inspeccionaron explícitamente. Los registros de guardia de los procesos
terminados registran cero accesos prohibidos de red o rutas operativas. No se
comparan hashes de archivos operativos porque su apertura está excluida.

Log verbose y resumen JSON: `%TEMP%\spica-paso84a-f1af5b25ef9d463ab1edba2791ffb1ec`.
Son registros de comprobación, sin adquisición institucional. Git final mantiene
rama y HEAD iniciales `00fc44b`, con únicamente estos seis archivos nuevos:

```text
?? docs/interoperabilidad_espaciotemporal.md
?? src/spica/interoperabilidad/__init__.py
?? src/spica/interoperabilidad/evaluador.py
?? src/spica/interoperabilidad/modelos.py
?? tests/test_interoperabilidad_evaluador.py
?? tests/test_interoperabilidad_modelos.py
```

Los archivos previamente versionados permanecen intactos. No hubo conexiones,
GET, acceso a evidencia real o RAW/staging/SQLite operativos, instalaciones,
migraciones, commits o push. La guardia controla nuestros procesos Python; no
certifica actividad ajena al procedimiento ni la integridad actual del RAW.

## 10. Restricciones y dictamen

APTO_ESTRUCTURALMENTE es un resultado de preparación documental, no validación
científica o espacial. El evaluador confía en las afirmaciones revisadas aportadas;
no lee documentos, autentica emisor, prueba precisión instrumental ni audita la
interpretación de cada texto. La inspección estructural no sustituye QA/QC.
Python y tzinfo aportados se consideran de confianza, no código hostil aislado.

Antes de GIS real siguen pendientes permisos/autorización, identidad/edición y
correspondencia, datos originales realmente adquiridos, CRS y transformaciones
aplicables, escala/precisión apropiadas al objetivo, geometrías/formatos soportados,
topología, método científico y control explícito de incertidumbre/validez temporal.
No se ejecutan inferencias ambientales, causalidad, litología, contaminación,
mapas, comparaciones de observaciones o QA/QC Nivel 1.

El dictamen del incremento se limita a **APTO CON RESTRICCIONES para auditoría del
núcleo offline**, con las verificaciones anteriores aprobadas. No autoriza
conexiones, `/query`, RAW, staging, SQLite operativo, migraciones o procesamiento.
