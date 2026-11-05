# PASO 84-C: integración local controlada PNDA/SENAMHI

## Alcance y antecedentes

Fecha de elaboración: **2026-11-05**. Git inicial limpio en `feature/suadc-http`,
HEAD **`8263b86`**, `SUADC: adaptadores offline de interoperabilidad cientifica`:
el PASO 84-B está registrado. Se conserva íntegro ese trabajo.

Este paso comprueba la adaptación de metadatos y una muestra pequeña del activo
local ya autorizado. No adquiere recursos, certifica mediciones ni realiza GIS.
Se conservan las restricciones de los [adaptadores del 84-B](adaptadores_interoperabilidad_offline.md)
y del [núcleo del 84-A](interoperabilidad_espaciotemporal.md).

La autorización se limita al activo **`71df55229ee947fb8e7fed8b1403289e`** y los
metadatos estrictamente necesarios del catálogo RAW. Su identidad histórica y la
huella esperada constan en [consultas locales](consultas_locales.md) y
[perfilado meteorológico](perfilado_meteorologico.md). No se buscan productos o
archivos privados adicionales.

## Arquitectura y procedimiento de lectura

Se añade [un arnés manual](../herramientas/piloto_pnda_84c.py), separado de los
módulos estables. No es un nuevo lector CSV, API de almacenamiento ni permiso
para ejecutar otros activos. El llamador debe aportar la identidad y huella del
expediente autorizado. El arnés devuelve objetos en memoria; no guarda informes.
Se añaden [pruebas sintéticas del procedimiento](../tests/test_integracion_local_pnda.py).

Componentes reutilizados:

- `_lectura_sqlite` de la inspección RAW, exclusivamente su rama
  `mode=ro&immutable=1`, tras rechazar WAL, SHM, journal y marcador de inicialización.
- `ActivoRAW`, `DeclaracionRAW` y el desempaquetado/validación existente de
  `EvidenciaAdquisicion`: no se redefine identidad o procedencia científica.
- `ConsultorLocalCSV`, `LectorCSV`, `ConsultaLocal`, `LimitesConsulta` y
  `ProcedenciaLocal`: conservan campos originales, posiciones, cancelación y alcance.
- `RecursoCatalogo`, `adaptar_catalogo`, `adaptar_meteorologia`,
  `OperacionPropuesta` y `evaluar_operacion`: las versiones anteriores no cambian.

`CatalogoRAW` y `ConfiguracionRAW.abrir` no se utilizan: su apertura operativa
admite escritura y no es adecuada para este ensayo. Tampoco se llama a verificación
RAW que registre comprobaciones o eventos. No se ejecutan migraciones, ni siquiera
para construir esquemas de referencia en memoria.

Antes de interpretar:

1. Comprobar rutas controladas, ausencia de symlinks/junctions, tipo regular y
   ausencia de auxiliares SQLite o inicialización incierta. No listar el almacén.
2. Calcular la huella binaria del catálogo, con límite de 1 MiB, bloques de 64 KiB
   y firma de dispositivo/inode/tamaño/mtime estable.
3. Abrir la primitiva inmutable. Activar `query_only` y desactivar `trusted_schema`;
   un autorizador SQL admite selección/lectura y consulta de versión, rechaza
   escrituras, DDL, ATTACH, funciones y PRAGMA de modificación.
4. Exigir versión 2 y tabla `activos` real. Seleccionar por el `asset_id` exacto,
   sin listar otros activos, y recuperar declaración y evidencia persistidas.
   Este control acotado no pretende certificar toda la estructura SQLite.
5. Exigir fuente, estado incorporado, formato CSV, tamaño, hash y referencia interna
   canónica coincidentes con el expediente. Desempaquetar la evidencia existente.
6. Calcular tamaño y SHA-256 físicos del CSV por bloques acotados. Solo una
   coincidencia con el catálogo y la referencia permite iniciar el consultor.
7. Seleccionar CANDARAVE, fecha civil inclusiva **2015-01-01**, variables
   **TEMP, HR, PP**, máximo **6 resultados** y **33 registros CSV incluido el
   encabezado**. El resultado esperado del piloto es dos filas por tres variables;
   si no se obtiene la muestra dentro del presupuesto, detenerse sin ampliarlo.
8. Adaptar las seis observaciones y evaluar las descripciones TEMP de las dos filas
   seleccionadas por separado en dimensión espacial y temporal.
9. En `finally`, recalcular CSV y catálogo, comparar también identidad/tamaño/mtime
   y volver a rechazar auxiliares. Esa comprobación final no se cancela a mitad:
   puede necesitar una nueva lectura binaria tras solicitar cancelación.

Las dos pasadas SHA-256 leen todos los bytes del activo para comprobar integridad;
no analizan todas sus observaciones. La consulta interpreta únicamente una muestra
y puede preleer un bloque de 64 KiB además de la muestra inicial de 64 KiB.
No carga el archivo completo en memoria ni supone EOF a partir del prefetch.

Los errores producen códigos fijos, sin backend, rutas ni cuerpos en el mensaje.
Una anomalía no provoca reintentos, reparaciones, borrados o apertura alternativa.
El control de caminos y firmas requiere uso secuencial y directorios controlados;
no proporciona aislamiento frente a un escritor hostil. No se modifican permisos.

## Correspondencia y desconocidos

| Dato | Tratamiento |
|---|---|
| Fuente, producto, recurso, activo y adquisición | Identificadores persistidos, conservados literalmente |
| Declaración RAW y evidencia documental | Instancias existentes reconstruidas desde la única fila consultada |
| Procedencia del recurso | Procedencia documental persistida, sin sustituirla por la fecha del ensayo |
| Identidad local de cada descripción | Revisión técnica `paso84c-local:<asset_id>:registro-<n>:<variable>`, sin crear códigos de estación/serie |
| Nombre ESTACION y ubicación textual | Originales declarados; no identifican por sí solos una estación física |
| Variable | Nombre de columna original; no se asignan unidades ni se interpretan valores |
| FECHA | Fecha civil obtenida por el consultor existente, sin convertirla en instante |
| HORA y UBIGEO | Textos literales; sin ceros reconstruidos, normalización o localización |
| Coordenadas textuales de CSV | Permanecen en originales; no se convierten en coordenadas verificadas |
| Coordenadas numéricas, código físico de estación y CRS | Desconocidos en la descripción: no se crea una estación catalogada ficticia |
| Zona, convención, resolución e incertidumbres | Desconocidas si las entradas no las acreditan |
| Registro RAW, adquisición HTTP y observaciones | Ámbitos distintos; fechas técnicas conservadas separadamente en el informe |

Los perfiles históricos documentan cobertura civil observada **2015-01-01 a
2024-06-30**, tres variables y una frecuencia horaria declarada en el diccionario.
Son antecedentes del mismo hash, no comprobaciones integrales nuevas ni garantía
de continuidad o de interpretación de cada HORA. No se repite el perfilado.

`DisponibilidadCatalogo` exige extremos datetime; el antecedente citado solo
acredita fechas civiles. No se inventan medianoches para introducir ese período
en el adaptador. Al no aportarse disponibilidad documentada bajo ese contrato,
el período de observaciones queda desconocido. La resolución de disponibilidad,
la frecuencia declarada del diccionario y la cadencia efectiva siguen siendo
conceptos distintos. Ninguno se deduce de contar filas.

## Evidencia real y resultados

Ejecución real **2026-11-05, 05:15:33.783275–05:15:34.292940 UTC**. Son horas
técnicas del ensayo, sin localizar las observaciones. Un único ensayo, sin reintentos.
Los tests sintéticos descritos posteriormente constituyen una evidencia distinta.

| Identidad | Valor leído y comprobado |
|---|---|
| Fuente | Proveedor `SENAMHI`, identificador `SENAMHI` |
| asset_id | `71df55229ee947fb8e7fed8b1403289e` |
| adquisicion_id | `ff8e7846a9b14568aad924aa8ca93f74` |
| producto_id | `variables-meteorologicas-de-las-estaciones-autom%C3%A1ticas-de-intercambio-internacional-servicio` |
| Estado RAW persistido | `incorporada`, sin error; no se modifica ese estado |
| Fecha de registro RAW | `2026-10-29T22:23:57.073988+00:00` |
| Comprobación HTTP histórica | `2026-10-29T22:23:57.063861+00:00`; no es una solicitud nueva |
| Fecha de la procedencia documental | `2026-10-29T22:23:30.743532+00:00` |
| Estado documental persistido | `DECLARADO` |
| Método y evidencia documentales | `GET_publico_HTML`; `HTTP_200_pagina;enlaces_declarados_dcat:Distribution;sin_comprobar_archivos` |
| Revisiones institucionales numéricas | Documental, producto y fuente: `None`, conservadas sin inventar versiones |

Identificador literal del recurso persistido, no consultado por HTTP:

```text
https://www.datosabiertos.gob.pe/sites/default/files/Variables%20Meteorologicas%20de%20las%20Estaciones%20autom%C3%A1ticas%20de%20intercambio%20internacional%20-%20%5BServicio%20Nacional%20de%20Meteorolog%C3%ADa%20e%20Hidrolog%C3%ADa%20del%20Per%C3%BA%20-%20SENAMHI%5D_0.csv
```

La referencia de publicación persistida es la ruta `/dataset/` del mismo producto
en `https://www.datosabiertos.gob.pe`. No se volvió a consultar esa publicación.
`licencia_declarada=None`, pero existe la referencia histórica
`http://opendefinition.org/licenses/odc-by/`. Se conserva esa diferencia: el enlace
no se abre, se completa con una etiqueta inventada ni acredita por sí solo alcance
jurídico o autorización de redistribución. El diagnóstico de condiciones de uso
desconocidas no significa que no exista esa referencia.

### Integridad física

Original consultado:

```text
C:\Users\Propietario\SPICA_DATOS\raw\sha256\3d\3d3e8a0a75e070d0b8111faf921be17140c3a0f9db2b4c25d72d99a15a950eab
```

| Archivo | Tamaño antes / después | SHA-256 antes y después |
|---|---:|---|
| CSV autorizado | **50474012 / 50474012** bytes | `3d3e8a0a75e070d0b8111faf921be17140c3a0f9db2b4c25d72d99a15a950eab` |
| `raw/catalogo.sqlite3` | **32768 / 32768** bytes | `946d2512795c5ae3a68113f63438110be66dee32488ad02e86d550da040d4a0d` |

El CSV coincide con el tamaño y hash de la fila catalogada y con los antecedentes
autorizados. Dispositivo/inode, tamaño y mtime coinciden antes/después para ambos
archivos. No aparecieron WAL, SHM, journal ni marcador de inicialización.
La base se abrió una sola vez, mediante URI inmutable y selección por el único ID.
No se consultaron otros activos ni eventos ni se reafirma un conteo global SQLite.

### Selección y adaptación

Se interpretaron **tres registros CSV**: encabezado y dos filas de datos, líneas
físicas 1–3. Dos filas por TEMP/HR/PP producen **6 resultados de consulta y
6 descripciones**, sin contar seis observaciones temporales independientes.
Todas conservan el recurso, activo y procedencia originales. No se publican sus
valores meteorológicos en este informe.

| Registro CSV | Nombre original | Fecha civil | HORA literal | Variables seleccionadas |
|---:|---|---|---|---|
| 2 | `CANDARAVE` | `2015-01-01` | `00000` | TEMP, HR, PP |
| 3 | `CANDARAVE` | `2015-01-01` | `10000` | TEMP, HR, PP |

Lectura de consulta: muestra inicial **65536 bytes** y prelectura del recorrido
**65536 bytes**, sin acumular el CSV. `completa=False`, motivo de consulta
`limite_resultados`; lector `incompleta_por_limites`, motivo
`consumidor_detuvo_lectura`, EOF no alcanzado. Cero fechas inválidas y cero registros
problemáticos en la selección. La codificación usada es UTF-8, pero
`codificacion_confirmada=False` para esta lectura parcial; no se promueve a una
verificación integral de codificación o estructura basada en dos filas.

Catálogo adaptado y las seis descripciones: `PARCIAL`. Los nombres de variable,
FECHA, HORA, UBIGEO y ubicación textual se mantienen sin conversión. Identificador
de estación, coordenadas numéricas, CRS, zona, convención, resolución, incertidumbre
y período en el contrato permanecen desconocidos. Las coordenadas textuales que
contengan los originales no constituyen coordenadas físicas verificadas.

### Evaluaciones A–E

El par evaluado está formado por TEMP del registro 2 y TEMP del registro 3 del
**mismo activo**. Este autoensayo prueba integración de contratos, no independencia
de fuentes, equivalencia entre estaciones o correspondencia con una capa geológica.

| Aspecto solicitado | Resultado real |
|---|---|
| A. Información espacial | `PENDIENTE_DE_EVIDENCIA` |
| B. Información temporal | `PENDIENTE_DE_EVIDENCIA` |
| C. Procedencia | Referencia, fecha, método y evidencia documental disponibles; estado documental `DECLARADO`, conservado. No constituye validación geográfica o científica |
| D. Operación futura que exige precisión espacial | Núcleo pendiente y **6 faltantes adicionales** de operación; condiciones documentales no satisfechas |
| E. Comparación temporal futura | Núcleo pendiente; condiciones documentales no satisfechas. Quitar el marco espacial reproduce el mismo estado y faltantes temporales |

La dimensión espacial devuelve **14 faltantes**: para cada entrada, coordenadas,
declaración CRS de geometría, identidad de ubicación no ambigua, cobertura observada,
precisión, incertidumbre y verificación de calidad posicional. La operación exige
adicionalmente precisión, incertidumbre y respaldo de calidad por entrada.

La dimensión temporal devuelve **12 faltantes**: para cada entrada, verificación de
interpretación, resolución, zona declarada, convención, incertidumbre y período de
observaciones. No hay faltantes espaciales en ese resultado temporal.

Diagnósticos estructurados del adaptador, conservados para las seis descripciones:

```text
condiciones_uso_desconocidas
estacion_catalogada_no_aportada
nombre_literal_no_acredita_identidad_fisica
periodo_documentado_incompleto
identificador_disponibilidad_no_es_identificador_serie
convencion_limites_e_incertidumbre_no_documentados
zona_horaria_no_documentada
hora_original_no_localizada_ni_reconstruida
precision_incertidumbre_y_cobertura_no_inferidas
```

No se detectaron contradicciones adicionales entre las entradas aportadas a este
par. Eso no descarta problemas en el resto del CSV ni resuelve las discrepancias
documentales históricas de HORA/UBIGEO. Ninguna entrada se convirtió a UTC ni se
reconstruyeron ceros. `operacion_ejecutada=False`,
`verificacion_espacial_efectiva=False` y `confiabilidad_cientifica="no_evaluada"`
en ambos resultados. Evaluador y política de operación: **0.1.0**; adaptadores:
**0.1.0**. La repetición en memoria con las mismas entradas devolvió el mismo
resultado temporal. No se repitió el acceso físico para esa comprobación.

Las revisiones técnicas distinguen registro/variable dentro de un mismo recurso;
no se presenta el cambio de fila como una versión institucional del producto.
Las descripciones y resultados inmutables no alteran registros históricos. La
conservación de revisiones frente a evidencia nueva contradictoria se comprobó
con pruebas sintéticas; no se creó una contradicción institucional ficticia.

### Ausencia de escrituras y límites de la evidencia

La guardia del proceso real registró exactamente: lectura binaria del catálogo,
apertura SQLite inmutable, tres aperturas de lectura del CSV (hash previo,
consultor, hash posterior) y lectura binaria final del catálogo. **Cero operaciones
prohibidas, conexiones externas o intentos de escritura operativa**.

No se accedió a staging, al activo sintético ni a archivos institucionales ajenos.
No se afirma una nueva verificación física del sintético: no se repitió un
inventario completo del almacén. La ausencia de intervención de este proceso se sustenta
en la guardia y las operaciones realizadas; la conservación física comprobada
directamente se limita al CSV y catálogo autorizados. No se cambiaron permisos.

Los metadatos técnicos de ejecución, diagnósticos y registro de la guardia quedan
en `resultado_real.json` y `auditoria/real-*.json`, bajo el temporal específico
`spica-paso84c-398b9bf12b9e4e5a9e832bdd420f634f`, fuera del repositorio. No contienen
un volcado de las mediciones ni una copia del CSV. Este informe conserva las
conclusiones y huellas esenciales; los temporales no sustituyen conservación
permanente aprobada ni copias de seguridad.

## Pruebas, riesgos y condiciones futuras

Las **11 pruebas nuevas** usan documentos y observaciones ficticios en directorios
temporales. Una prueba emplea `Fuente("SENAMHI", "SENAMHI")` con un documento
explícitamente ficticio para comprobar que el nombre institucional no verifica
geografía. No se usa contenido RAW como fixture ni se copia al repositorio.

Se cubren identidad, fuente, procedencia, atributos desconocidos, cancelación,
acceso denegado con mensaje fijo, corrupción previa, cambio simulado detectado al
cerrar, rechazo de auxiliares antes de SQLite, límites de selección, autorizador
SQL, conservación de archivos y revisiones y aptitud temporal independiente de
coordenadas. Las revisiones contradictorias se simulan sin modificar evidencia real.

Las primeras ejecuciones de desarrollo requirieron corregir las fixtures
(referencia pública ficticia compatible, conversión explícita de parámetros
inmutables a JSON y cierre de las conexiones de preparación). El aislamiento de
Windows impedía acceder a `TemporaryDirectory` privado de Python 3.15; las pruebas
se ejecutan con permisos normales y una guardia que bloquea red y datos operativos.
Ninguno de esos fallos implicó acceso al activo real.

El piloto sigue sin autorizar comparación científica, asignación de coordenadas,
geocodificación, reproyección, intersección, distancias, áreas, mapas, QA/QC nivel 1
o inferencias ambientales. INGEMMET `/query` continúa **NO AUTORIZADO**.

Para avanzar se necesita documentar identidad física de estaciones, CRS y calidad
posicional, convenciones de HORA y zonas, resolución e incertidumbres, y requisitos
del algoritmo científico concreto. Una huella local coincidente no demuestra
autenticidad institucional, calibración, completitud ni validez meteorológica.

Las lecturas pueden actualizar atime del sistema; no se compara ni modifica
deliberadamente ese metadato. Las firmas y hashes antes/después detectan cambios
ordinarios y conservación de bytes, sin proporcionar bloqueo exclusivo, durabilidad
del soporte ni prueba de que nunca hubo una modificación transitoria revertida.

## Verificación final y dictamen

Entorno comprobado: Python **3.15.1**, HTTPX **0.28.1**, SQLite **3.53.4**, mediante
`.venv/Scripts/python.exe` y `-B`, con `src` y raíz del proyecto en `PYTHONPATH`.
La suite se ejecutó antes de abrir datos reales y con una guardia distinta que
bloquea todo el árbol operativo. No hubo cambios de código tras esa ejecución.
La comprobación previa no encontró otros procesos Python/pythonw/SQLite conocidos;
eso no equivale a un bloqueo exclusivo ni excluye escritores de otro tipo.

Para identificar el código no registrado utilizado, SHA-256 de
`herramientas/piloto_pnda_84c.py`:

```text
98cfe2c28fcce5c9bfb8ef0e17f3fec52d0c2d638b30ff75dcbb10a348df90df
```

Invocación reproducible del arnés, exclusivamente bajo la autorización y los
controles de lectura descritos, con la guardia instalada antes de importar:

```python
from pathlib import Path
from herramientas.piloto_pnda_84c import ejecutar
from spica.adquisicion.nucleo import Fuente

resultado = ejecutar(
    Path(r"C:\Users\Propietario\SPICA_DATOS\raw"),
    asset_id="71df55229ee947fb8e7fed8b1403289e",
    tamano_esperado=50_474_012,
    sha256_esperado="3d3e8a0a75e070d0b8111faf921be17140c3a0f9db2b4c25d72d99a15a950eab",
    fuente_esperada=Fuente("SENAMHI", "SENAMHI"),
)
```

```text
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
Ran 1431 tests in 169.224s
OK

.\.venv\Scripts\python.exe -B -m pip check
No broken requirements found.
```

**1431 aprobadas: 1420 anteriores y 11 nuevas; 0 fallidas y 0 errores.** Se cotejaron
los identificadores de las pruebas anteriores con HEAD: cero ausentes y cero
identificadores duplicados. Los temporales sintéticos de las ejecuciones iniciales
fallidas se limpiaron exclusivamente dentro de Temp y después de verificar sus
rutas; no se borraron archivos operativos.

Git permanece en `feature/suadc-http` / `8263b86`, sin cambios en archivos
previamente registrados o en el índice. Se crean únicamente:

```text
docs/integracion_local_pnda_paso84c.md
herramientas/piloto_pnda_84c.py
tests/test_integracion_local_pnda.py
```

`git diff --check` sin incidencias. Los archivos sin registrar se inspeccionan
directamente, además del diff, incluyendo sintaxis, finales y enlaces locales.
No se realizan commits, instalaciones, descargas o migraciones.

**Dictamen: APTO CON RESTRICCIONES para el ensayo local de lectura y adaptación.**
Se comprobó integración real de contratos y conservación física del activo, sin
autorizar operaciones científicas pendientes. Se espera la auditoría del usuario
antes de cualquier ampliación o integración GIS.
