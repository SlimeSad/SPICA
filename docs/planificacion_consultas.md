# Paso 57: planificación declarativa de consultas científicas

`spica.adquisicion.planificacion` prepara propuestas a partir de una instantánea
del catálogo científico. No ejecuta transporte, descargas, almacenamiento ni
validación científica. No genera endpoints, URLs, parámetros de API o muestras.

## Estructura y uso

- `modelos.py`: solicitudes, límites, evaluaciones, operaciones y resultado.
- `evaluacion.py`: evaluación temporal y complemento de intervalos.
- `planificador.py`: consulta acotada del catálogo y construcción del plan.

`ConsultaProducto` reutiliza `SolicitudAdquisicion` del núcleo: fuente, fechas con
zona conocida, estaciones, variables originales y parámetros del proveedor. Añade
producto original opcional y frecuencia opcional. Producto `None` explora productos
de esa fuente. `SolicitudCientifica` agrupa consultas con un identificador explícito;
cada consulta mantiene su ámbito fuente/producto, período y parámetros. Así admite
varias instituciones y productos sin mezclar espacios de identidad. No es un
intérprete de lenguaje natural. Para seleccionar una institución se usa su `Fuente`
registrada, no una búsqueda aproximada por nombre.

```python
from spica.adquisicion.nucleo import SolicitudAdquisicion
from spica.adquisicion.planificacion import (
    ConsultaProducto, SolicitudCientifica, Planificador,
)

# fuente, inicio y fin son valores proporcionados por el llamador.
consulta = ConsultaProducto(
    SolicitudAdquisicion(fuente, inicio, fin,
                        estaciones=estaciones_originales,
                        variables=codigos_originales),
    producto_id=producto_original, frecuencia=frecuencia_declarada,
)
plan = Planificador(catalogo).planificar(
    SolicitudCientifica("identificador-publico-solicitud", (consulta,))
)
```

Colecciones vacías no imponen estaciones ni variables y no significan que no
existan. Los códigos originales se resuelven mediante `VariableCatalogo`, sin
recortar espacios, normalizar nombres ni convertir unidades/frecuencias. Los IDs
internos de variable se conservan en la evidencia; no sustituyen el código original
en una operación. Si este código se desconoce, la operación queda condicionada.
Los parámetros se preservan, pero requieren validación futura del conector. No se
interpretan como parámetros HTTP. Se reutiliza el detector conservador de metadatos
públicos del catálogo, también sobre pares clave=valor. No es un detector universal
de secretos: solo se deben proporcionar datos públicos revisados por el llamador.

## Evidencia y asociaciones

Solo cada registro explícito de disponibilidad respalda su propia asociación.
Una fila E1–V1 y otra E2–V2 nunca generan E1–V2 ni E2–V1. Las filas sin estación o
variable no prueban el alcance particular de selectores solicitados. La pertenencia
al diccionario tampoco demuestra disponibilidad.

`EvaluacionProducto` conserva las evaluaciones y revisiones, capacidades,
selectores individuales sin evidencia aplicable y advertencias. Que todos los
selectores individuales aparezcan no demuestra todas sus combinaciones: se mantiene
la advertencia de que la cobertura total de la solicitud no está garantizada.

Se reutilizan `EstadoVerificacion.DESCONOCIDO`, `DECLARADO` y `VERIFICADO`, siempre
con su procedencia original. VERIFICADO significa que existe evidencia registrada;
el planificador no la vuelve a comprobar ni certifica datos. Las contradicciones de
frecuencia quedan visibles sin conversiones. No se propagan disponibilidades entre
fuentes/productos aunque compartan el mismo código original.

**Limitación explícita:** el catálogo actual no tiene un modelo de evidencia
negativa. `AUSENCIA_DOCUMENTADA` está reservado y no se emite. Un registro fuera del
período se etiqueta `FUERA_COBERTURA_CONOCIDA`, no como prueba de inexistencia de
datos. Incorporar afirmaciones negativas, su alcance, vigencia y resolución de
contradicciones requiere aprobar un contrato futuro; no se migró el esquema.

## Tiempo

Los intervalos catalogados y solicitados tienen extremos inclusivos `[inicio, fin]`.
Se permite una solicitud puntual. Se comparan datetimes conscientes de zona por
su instante, sin cambiar las fechas originales conservadas en solicitud/evidencia.
Una zona textual no localiza automáticamente fechas naive del catálogo; extremos
desconocidos o sin zona producen evaluación desconocida.

Cada operación usa la intersección con su registro explícito. Los intervalos
discontinuos permanecen en operaciones distintas. No se crea una operación por
observación ni se infiere resolución a partir de una frecuencia textual. Las
frecuencias se comparan exactamente; ausencia de frecuencia no autoriza conversiones.

Los vacíos se calculan por asociación registrada (estación, ID interno de variable),
usando envolventes declaradas/verificadas compatibles. Se unen solapamientos solo
para calcular su complemento; las operaciones y evidencias no se fusionan. El
complemento de `[a,b]` y `[c,d]` contiene `(b,c)`, representado mediante indicadores
de inclusión, sin sumar segundos/días arbitrariamente. Vacíos y alcances sin
evidencia siguen siendo desconocidos. Una envolvente parcial puede contener huecos
internos no localizables: nunca afirma continuidad ni completitud de mediciones.

Cobertura parcial `True` o desconocida (`None`) impide tratar la envolvente como
completa. Una intersección que solo cubre parte del período también queda marcada
parcial. Declaración, verificación, parcialidad y coincidencia temporal son
dimensiones distintas, conservadas en el resultado.

## Operaciones y preparación

Una propuesta se genera por registro aplicable, sin expansión cartesiana. Filas
repetidas o solapadas pueden generar propuestas distintas: aún no hay identidad de
recurso remoto con la que deduplicarlas de forma segura. Si no hay registros
aplicables, se genera una única propuesta condicionada de descubrimiento por
producto; sus selectores solicitados no constituyen asociaciones confirmadas.
Un producto no identificado genera una advertencia, sin inventar una ficha.

`PREPARADA` exige, para esa operación, disponibilidad verificada, alcance exacto,
envolvente no parcial y suficiente para el período, frecuencia compatible,
capacidad verificada, requisitos de acceso explícitamente sin autenticación y
ausencia de parámetros aún no interpretados. En los demás casos queda
`CONDICIONADA` con dependencias explícitas. Se elige determinísticamente la primera
capacidad verificada disponible, o la primera registrada en el orden estable de
la instantánea; todas quedan disponibles en la evaluación, sin afirmar preferencia
científica ni eficiencia. Una capacidad manual preparada sigue necesitando operador.

`operaciones_propuestas` cuenta exactamente las propuestas generadas.
`estimacion_operaciones_ejecucion` es `None`: sin conectores no se conoce la
paginación, agrupación, fragmentación ni cantidad real de peticiones.
`plan.ejecutable` permanece `False`: preparado según metadatos no significa que
exista un ejecutor institucional. El plan no confirma disponibilidad real ni RAW.

## Límites y consistencia

`LimitesPlanificacion` predeterminados:

| Límite | Valor |
| --- | ---: |
| Operaciones propuestas | 1000 |
| Registros de catálogo / evaluaciones de intervalos | 10000 |
| Contenido JSON UTF-8 del catálogo | 8 MiB |
| Consultas agrupadas | 128 |
| Selectores y pares de parámetros | 10000 |
| Textos de solicitud inspeccionados | 2 MiB |

Los límites son configurables y positivos. Excederlos lanza `LimitePlanificacion`;
no devuelve planes truncados que aparenten estar completos. Los límites de bytes
no equivalen al tamaño exacto de objetos Python en RAM, pero acotan la entrada
deserializada y las colecciones generadas. Los modelos de entrada pertenecen al
llamador y ya existen al invocar el planificador.

La API aditiva `CatalogoCientifico.leer_acotado()` cuenta filas y bytes antes de
deserializar, dentro de una transacción de lectura SQLite consistente. Lee solo
tablas de metadatos actuales, sin historial; no modifica la base ni el esquema.
Se filtra fuente/producto; los demás filtros se evalúan posteriormente para no
ocultar evidencia incompatible. Una selección de varias fuentes/productos puede
leer un superconjunto conservador antes de separar cada consulta y alcanzar el
límite antes: en ese caso se debe reducir el alcance, no aumentar ilimitadamente
los topes. El orden de contenido persistido y la numeración secuencial producen
planes deterministas para la misma solicitud e instantánea, sin UUID ni reloj.

## Pendiente de revisión

Quedan pendientes evidencia negativa explícita, detección/resolución de evidencia
contradictoria o caducada, prioridades entre mecanismos, selección de la revisión
histórica, deduplicación remota, estimaciones reales de volumen y autorización de
ejecución. Escanear SQLite sigue teniendo coste de CPU/E/S aunque la memoria esté
acotada: faltan índices de consulta especializados y presupuestos de tiempo.
No hay conversión científica, paralelismo, descarga ni conectores.

Las pruebas usan datos sintéticos y SQLite efímero. Las interfaces previas del
catálogo y del núcleo se conservan; HTTP, RAW y bases operativas no se modifican.
