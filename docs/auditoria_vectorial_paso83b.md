# PASO 83-B: auditoría offline de precisión e integridad vectorial

Dictamen del incremento: **APTO CON RESTRICCIONES** para revisión del protocolo.
No autoriza ni prepara un ejecutor de solicitudes institucionales.

## 1. Estado inicial y método

Git limpio, rama `feature/suadc-http`, HEAD **f8b3df9**: el PASO 83-A está registrado.
Entorno comprobado con `.venv`: Python 3.15.1, HTTPX 0.28.1, SQLite 3.53.4.
La suite de referencia es de 1272 pruebas. Antes de editar aprobaron las 108
pruebas vectoriales y las 103 del inspector ArcGIS, exclusivamente con fixtures
sintéticas. No se abrió evidencia real ni almacenamiento operativo.

Se revisaron el lector compartido, los modelos, validador, coordinador y transporte
sintético, inspector anterior, ambas suites vectoriales y su documentación. Se
añaden regresiones solo para vacíos observados; no se duplican los escenarios de
orden, OID repetidos, páginas vacías, cancelación y cuotas ya cubiertos.

## 2. Hallazgos reproducidos

| Hallazgo | Gravedad y evidencia anterior | Corrección y garantía actual |
|---|---|---|
| 83B-01: un cierre inexistente podía aceptarse | **Alta.** Un anillo con primer punto `[0,0]` y último `[1e-999,0]` se aceptó como `estructura_valida`: `float` convirtió el último X en cero. También `1.00000000000000000000001` colapsa a `1.0` | Lectura decimal temporal y comparación exacta del cierre; el modo compatible rechaza subdesbordamiento. Nunca se repara el anillo |
| 83B-02: eco fuera del presupuesto | **Media.** Con cuota auxiliar de 10000, un eco inesperado con `where` de 8000 caracteres quedaba retenido en el recibo aunque su costo lógico era mayor | Se contabiliza el eco distinto antes de conservarlo; si no cabe se omite con código explícito, sin ocultar la contradicción |
| Precisión binaria documentada | **Limitación conocida, no defecto documental nuevo.** `0.123456789012345678901234567890123456789` se devolvía como `0.12345678901234568` | Modo decimal exacto optativo; el modo anterior conserva sus tipos y queda identificado como aproximado |

Los dos primeros son defectos corregidos, no afirmaciones sobre INGEMMET. El
tercero ya estaba advertido en el PASO 83-A; ahora dispone de una alternativa
controlada. No se convierten estos hallazgos en evidencias de calidad institucional.

## 3. Decisión de compatibilidad y precisión

Se conservan contratos anteriores del núcleo, catálogo, HTTP, RAW e inspector de
metadatos. La ampliación vectorial es compatible con llamadas previas:

```python
validar_featureset(respuesta_sintetica, contrato)  # salida int/float, como antes
validar_featureset(respuesta_sintetica, contrato,
                  precision=PrecisionNumerica.DECIMAL_EXACTA)
```

`precision` es un argumento opcional tipado, también en `coordinar`; consta en la
página y resultado, incluso si la operación termina antes del análisis. Es política
de interpretación, no parámetro de servidor. No altera `ConsultaVector.huella`,
la versión del esquema 0.1 ni el hash de la respuesta. Los mapas de atributos ya
estaban tipados como `object`; se admite Decimal finito sin retirar los tipos previos.

| Aspecto | Garantía |
|---|---|
| OID e integer JSON | `int` exacto, sin paso por float ni Decimal. OID admite 0 a 2^63−1; por encima se rechaza según el contrato existente |
| Enteros de más de 32 caracteres | Rechazo previo, como antes; no se interpreta que la fuente carezca de otros tipos |
| Modo DECIMAL_EXACTA | Decimal construido directamente desde el token, sin redondeo del contexto; conserva su valor finito y signo del cero dentro de las cuotas |
| Modo BINARIA_COMPATIBLE | Salida `int`/`float` para compatibilidad. Puede perder cifras o colapsar vértices cercanos; no ofrece preservación matemática exacta |
| Comparación de cierre | Siempre sobre el árbol numérico decimal anterior a la salida binaria; no se toleran diferencias pequeñas ni se añaden vértices |
| Subdesbordamiento binario | Decimal no nulo que se convertiría a cero: INVALIDA con `json_subdesbordamiento_binario` |
| NaN/Infinity | Rechazados en ambos modos mediante el parser estándar y sus controles |
| Booleanos | Nunca se aceptan como OID, enteros, coordenadas o atributos numéricos |
| Nulos | Se conservan cuando el contrato los admite; ausencia no se sustituye por null |
| Rango científico/IEEE | No se acredita: un decimal finito como `1e999` cabe en el modo exacto pero no en float. No prueba que el campo institucional almacene ese valor ni que una coordenada sea plausible |

El lector temporal decimal se activa solo para vectores. El camino predeterminado
del lector compartido continúa usando float para metadatos. Se mantienen sus
topes y se ejecutan sus regresiones anteriores.

No se realizan sumas científicas, redondeos, reproyecciones o cambios de unidades.
`Decimal(texto)` y sus inspecciones de finitud/exponente no dependen de
`getcontext().prec`. Un cálculo posterior con Decimal **sí** necesitaría su propia
política de contexto; este incremento no lo implementa.

## 4. Valor matemático, notación y bytes

Decimal no equivale a conservar texto: `1.2300E+02` se puede mostrar como `123.00`.
Mayúsculas del exponente, espacios, orden de propiedades y codificación tampoco se
reconstruyen reserializando. Dos números matemáticamente iguales pueden tener
representaciones originales distintas.

La evidencia de representación es `RespuestaSintetica.contenido`, bytes inmutables
originales, vinculados a su solicitud/respuesta, origen declarado y fechas. Se
calcula SHA-256 de esos bytes dentro del presupuesto. No se ofrece un serializador
Decimal; `json.dumps` lo rechaza por defecto. Usar `default=float` puede perder
valor y usar texto cambia el tipo JSON: ninguna opción reconstruye el original.

En el coordinador se descartan los cuerpos tras cada página y se guardan recibos
acotados; no existe conservación durable. Un hash sin cuerpo conservado no permite
reconstruir la evidencia. El futuro piloto exige guardar bytes primarios antes de
interpretarlos y verificar físicamente su copia, mediante un diseño posterior
aprobado. Aquí no se ha verificado físicamente un archivo institucional o RAW.

## 5. Auditoría geométrica

Se mantienen Polygon lineal XY, anillos simples/múltiples con al menos cuatro
posiciones y cierre explícito, coordenadas numéricas finitas y orden original.
Ausencia, null y geometría presente siguen diferenciadas. Se conserva el CRS
declarado; no se deducen aliases, unidades, datum o ejes ni se completa una referencia.

Se rechazan curvas, Z/M, cuantización y geometrías fuera del subconjunto. Las
cuotas de anillos, posiciones por entidad/página, JSON y snapshot se mantienen.
El modo exacto preserva numéricamente los vértices originales dentro de sus límites;
el modo binario sigue siendo una representación aproximada por compatibilidad.

Persisten limitaciones: sin topología, orientación, clasificación de huecos,
intersecciones, validez espacial, áreas, distancias, precisión instrumental ni
interpretación litológica. Una autointersección puede tener estructura válida.
La cantidad de decimales no acredita exactitud geológica.

## 6. Paginación, completitud y recuperación

La auditoría y las pruebas anteriores mantienen las tres estrategias sintéticas:
offset ordenado por OID, lotes objectIds y offset con conteo documentado. Se
detectan repeticiones, duplicados, omisiones contrastables con IDs, orden inestable,
vacíos con continuación, contradicciones de conteos/instantánea y agotamiento de
cuotas. No se interpreta un hueco numérico entre OID como entidad omitida.

Una página corta no termina por sí sola. `exceededTransferLimit` conserva sus tres
posibilidades: true, false o ausente. False no acredita una colección; true impide
declarar fin y puede contradecir un lote de IDs ya agotado. Los estados siguen:

- COMPLETA_COMPROBADA: únicamente IDs exactos y evidencia sintética coherente de
  consulta, cronología, instantánea y fin; el modo exacto no relaja estas barreras.
- PARCIAL: interrupción/cancelación o agotamiento de fixture tras recibir entidades.
- INCOMPLETA_POR_LIMITES: presupuestos agotados sin prueba suficiente.
- INCONSISTENTE: contradicciones o estructura inválida detectadas.
- DESCONOCIDA: evidencia insuficiente, aunque coincidan conteos.

No hay reanudación. Reutilizar el mismo transporte consume su secuencia restante,
pero una nueva llamada comienza en offset cero y no recupera recibos/IDs anteriores.
La regresión comprueba que el resto de una operación interrumpida no se presenta
como adquisición completa. No se implementan checkpoints o recuperación tras apagado.

El modelo sigue siendo secuencial, sin bloqueos ni transacciones multirrespuesta.
Concurrencia remota: un conteo estable, orden monótono o IDs coincidentes no excluyen
ediciones de atributos/geometrías. La garantía de instantánea es un dato del escenario
inventado, no una evidencia institucional verificada. No existe ruta HTTP ejecutable
en el prototipo; no se habilita completitud institucional con un cambio de configuración.

## 7. Presupuestos, errores y límites de confianza

Se mantienen 8 MiB de respuesta **offline**, 500000 nodos, profundidad 32, 2000
entidades por página, 100 páginas, 20000 entidades agregadas y 8 MiB auxiliares,
además de las cuotas de atributos, anillos, posiciones y bytes totales documentadas
en la [arquitectura](adquisicion_vectorial_offline.md#8-presupuestos-de-seguridad).

Los nuevos topes solo pueden reducirse: token decimal de 256 caracteres y exponente
absoluto máximo 4096, tanto escrito como almacenado en Decimal. Se comprueban antes
de construir el coeficiente o convertir a binario. Un exceso produce LIMITADA,
sin confundirlo con JSON plenamente validado. No son límites ambientales. No se
aceptan funciones de evaluación provenientes de archivos de reglas.

La cuota auxiliar también considera ecos distintos; al agotarla se conserva solo
el recibo mínimo y se declara la omisión. Los diagnósticos no copian mensajes de
error, parámetros o cuerpos. Las cantidades de bytes observados/admitidos siguen
separadas. No se prometen límites de RSS: una página produce cuerpo, texto, árbol y
snapshot; Decimal añade memoria. Las cuotas de bytes/nodos/tokens acotan ese trabajo.

La cancelación es cooperativa en los puntos anteriores; `json.loads`, la conversión
y los snapshots no son instantáneamente interrumpibles. El número de páginas y las
cuotas evitan bucles infinitos. Las fixtures son Python de confianza, no un sandbox
para generadores maliciosos; no se amplía ese límite de confianza.

## 8. Preparación institucional y permisos

La revisión documental se limita a los expedientes del repositorio y al encargo;
no se consulta la licencia externa ni se reclasifican evidencias institucionales.
La [matriz de permisos y protocolo](protocolo_piloto_arcgis_paso83b.md) propone un
único ensayo de atributos sin geometría, sujeto a revisión y autorización futura.

Faltan acreditar condiciones de acceso/retención y vincularlas al servicio exacto;
preparar validación offline del sobre mínimo sin inventar CRS ausentes; y revisar
el ejecutor limitado y la conservación de evidencia. El adaptador HTTP→RAW no se
implementa. Ninguna capacidad anunciada se eleva a comprobada funcionalmente.

## 9. Verificación final

Con el mismo Python 3.15.1 de `.venv`, y `src/` más la guardia aislada añadidos al
`PYTHONPATH` solo de los procesos de prueba, se ejecutaron:

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -B -m pip check
git diff --check
git status --short
git status --short --untracked-files=all
```

Resultado final: **1293 pruebas ejecutadas y aprobadas, 0 fallidas, 0 errores**, en
141.598 segundos. Las **1272 anteriores** aparecen una vez cada una en la salida
aprobada, contrastadas con los identificadores del commit inicial. Se añaden **21**
regresiones en [test_vectorial_precision.py](../tests/test_vectorial_precision.py).
No se modificaron las pruebas vectoriales anteriores ni se omitieron métodos.

Los casos nuevos cubren precisión decimal y contexto, enteros mayores de 2^53,
límites OID, cierre perdido por redondeo, signos/cero/notación, memoria numérica,
representación textual/serialización, perfiles, ecos y ausencia de reanudación.
El resto de garantías se conserva mediante las pruebas existentes. No se afirma
conformidad científica por aprobarlas.

`pip check`: **No broken requirements found.** `git diff --check`: sin hallazgos.
Se comprobaron sintaxis/compilación en memoria sin `.pyc`, nombres duplicados,
espacios finales y enlaces locales, incluidos los archivos nuevos. La salida
unittest completa se conserva en `suite_completa.log` dentro del directorio
temporal aislado del PASO 83-B, fuera de Git.

Git final: misma rama y HEAD **f8b3df9**, seis archivos modificados y tres nuevos:

```text
 M docs/adquisicion_vectorial_offline.md
 M src/spica/adquisicion/_json_acotado.py
 M src/spica/adquisicion/vectorial/__init__.py
 M src/spica/adquisicion/vectorial/coordinador.py
 M src/spica/adquisicion/vectorial/modelos.py
 M src/spica/adquisicion/vectorial/validador.py
?? docs/auditoria_vectorial_paso83b.md
?? docs/protocolo_piloto_arcgis_paso83b.md
?? tests/test_vectorial_precision.py
```

La guardia de los procesos instrumentados registró **cero intentos prohibidos** de
red/acceso protegido. No hubo conexiones externas, GET institucionales, apertura
de evidencia real, acceso a RAW/staging/SQLite operativos, instalaciones, migraciones,
QA/QC científico, commits o push. Las pruebas RAW anteriores usan sus propios
directorios sintéticos `.suadc-test-*`, que se limpiaron al finalizar la suite;
no son el almacenamiento operativo. No se verificaron hashes de datos operativos
porque su acceso estaba excluido.

El inspector de metadatos, transporte HTTP, almacenamiento e integración, así como
`main.py` y `.gitignore`, permanecen sin cambios respecto al commit inicial. No se
modificó `.venv`. No existe adaptador vectorial HTTP→RAW ni ejecutor nuevo de red.

**APTO CON RESTRICCIONES:** correcciones offline verificadas y protocolo disponible
para revisión. Antes de un ensayo real deben resolverse los permisos, acreditar
la ruta/parámetros candidatos, preparar la validación del sobre mínimo y su
conservación privada y recibir autorización expresa. El modo binario mantiene su
limitación de precisión; topología, instantánea institucional y durabilidad siguen
fuera de lo demostrado. No se continúa con el piloto en este paso.
