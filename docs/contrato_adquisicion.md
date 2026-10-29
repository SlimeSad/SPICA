# Contrato mínimo de adquisición SUADC

Primera versión provisional, sin conectores, red, lectura de archivos ni cálculos
científicos. Utiliza únicamente la biblioteca estándar de Python.

## Estructura

- `src/spica/adquisicion/nucleo/modelos.py`: modelos y validaciones.
- `src/spica/adquisicion/nucleo/__init__.py`: API pública del núcleo.
- `tests/test_adquisicion_nucleo.py`: pruebas con datos ficticios.

`Fuente` identifica un proveedor y una fuente mediante sus identificadores originales.
No se normalizan espacios, mayúsculas ni códigos; se rechazan textos vacíos.
No hay catálogos ni inferencias de estaciones, variables o unidades.

`SolicitudAdquisicion` admite varias estaciones y variables, ambas opcionales,
un intervalo temporal y parámetros específicos del proveedor. Las fechas son
`datetime` con zona horaria; se acepta un intervalo de duración cero. Los parámetros
son pares texto/texto: se copian y se exponen como un mapa de solo lectura.
Las colecciones se convierten en tuplas y los modelos son dataclasses congeladas.

El PASO 67 valida el orden por instantes UTC, distingue `fold` en horas repetidas
y rechaza horas locales inexistentes. Las fechas originales permanecen intactas;
no se asigna zona a fechas civiles. Véase la [política temporal](politica_temporal.md)
para las reglas compartidas con catálogo y planificación y sus límites.

`RecursoDescubierto` describe una referencia opaca mediante identificador y
localizador. El localizador no tiene que ser una URL. Formato y tipo de medio son
textos opcionales, sin enumeración cerrada: pueden representar archivos binarios,
documentos, archivos comprimidos u otros recursos. No se exige CSV ni DataFrame.

`Descarga` registra estado, ruta local, bytes recibidos y posible error.
`Integridad` registra por separado estado, tamaño esperado, algoritmo, hashes
esperado y observado, procedencia de la evidencia y posible error.
`ResultadoRecurso.estado` se deriva de ambas etapas para evitar un indicador de
confirmación independiente que pueda contradecir la evidencia:

| Condición | Estado del recurso |
| --- | --- |
| Descarga pendiente, integridad pendiente | descubierto |
| Descarga parcial, integridad pendiente | parcial |
| Descarga completa, integridad pendiente | descargado |
| Descarga completa y evidencia de integridad validada | confirmado |
| Descarga o integridad fallida | fallido |

### Reglas de transferencia

- `PENDIENTE`: sin ruta local, sin error y con bytes desconocidos (`None`) o cero.
- `PARCIAL`: ruta local y bytes estrictamente positivos, sin error. La transferencia
  no se declara terminada. Si hay tamaño esperado, los bytes no pueden excederlo.
  Alcanzar exactamente ese tamaño no cambia el estado automáticamente: puede faltar
  finalizar la transferencia. Cero bytes sin terminación se representa como pendiente
  o como fallo si hubo un error, sin conservar una ruta en el caso pendiente.
- `COMPLETA`: el ejecutor declara terminación de la transferencia, con ruta local,
  bytes no negativos y sin error. Si existe tamaño esperado, debe coincidir con los
  bytes recibidos, incluso cuando la integridad todavía está pendiente.
- `FALLIDA`: exige error de transferencia y permite conservar bytes y ruta. Los bytes
  positivos siempre requieren ruta. No exige que coincidan con el tamaño esperado:
  puede representar truncamiento o exceso de bytes.

Todos los tamaños son enteros no negativos; se rechazan booleanos. No se infiere
terminación a partir del contador de bytes. Si no existe tamaño esperado, la
declaración de transferencia completa depende del ejecutor y no permite confirmar
por sí sola la integridad.

### Reglas de integridad y contradicciones

- Una descarga pendiente, parcial o fallida solo admite integridad pendiente y
  ningún hash observado. Puede conservar metadatos esperados para una futura
  verificación. No se comparan hashes de fragmentos como si fueran del recurso entero.
- Un hash observado requiere algoritmo, hash esperado y procedencia de evidencia.
  Si ambos hashes difieren, el estado debe ser `FALLIDA`; no se permite ocultar
  la contradicción bajo `PENDIENTE`.
- `FALLIDA` exige error, descarga completa y evidencia de hashes distintos con
  algoritmo y procedencia. Un mensaje de error aislado no demuestra fallo de integridad.
- `VERIFICADA` exige descarga completa, tamaños esperado y recibido coincidentes,
  algoritmo, hashes idénticos y procedencia, sin error. Solo entonces el estado del
  recurso es `CONFIRMADO`. La comparación de hashes es textual y exacta.
- `PENDIENTE` no admite error; puede conservar evidencia coincidente todavía no
  aprobada. La coincidencia no cambia el estado automáticamente ni confirma el recurso.

En esta versión una discrepancia de tamaño se representa como fallo de transferencia,
con integridad pendiente; la integridad fallida se reserva a discrepancias de hashes
del recurso cuya transferencia terminó. Un error al intentar calcular el hash no
demuestra corrupción: debe mantenerse la integridad pendiente y registrarse el error
general en `ResultadoAdquisicion.errores`. No hay un estado específico para ese caso.

Un archivo de cero bytes puede confirmarse si la descarga está completa, el tamaño
esperado es cero y existe evidencia de hashes coincidentes con algoritmo y origen.
El contrato no evalúa su utilidad científica.

Los modelos validan coherencia de declaraciones; **no comprueban la existencia del
archivo ni calculan hashes**. Un futuro ejecutor deberá obtener los bytes y aportar
evidencia real. Declarar un algoritmo no valida todavía su soporte o seguridad.
`VERIFICADA` y `CONFIRMADO` expresan coherencia de metadatos declarados en este
contrato, no una verificación física realizada por estos modelos. Tampoco se valida
la sintaxis del hash ni la autenticidad del origen de evidencia.

`ResultadoAdquisicion` contiene la solicitud, resultados por recurso y errores
generales (por ejemplo, de descubrimiento). Admite resultados parciales y vacíos.
No declara un éxito global: una colección vacía no equivale a descarga confirmada.
Todos los recursos deben pertenecer a la fuente solicitada.

## Decisiones pendientes de aprobación

1. Semántica de inclusión de los extremos del intervalo, precisión de las fechas
   y tratamiento de recursos sin cobertura temporal. Hoy ambas fechas son obligatorias.
2. Espacios de nombres oficiales de fuentes y mapeos de variables, estaciones y
   unidades, siempre conservando los identificadores originales.
3. Política de integridad por proveedor: hoy se exigen tamaño y hash esperados
   con procedencia. Definir qué hacer si el proveedor no publica esa evidencia,
   cuáles son los algoritmos aceptados y cómo se valida su procedencia. Un hash
   calculado solo sobre la copia local no demuestra coincidencia con el origen.
4. Parámetros del proveedor más ricos que texto/texto, serialización/versionado
   del contrato y semántica de parámetros desconocidos.
5. Errores estructurados, reintentos, cancelación, paginación, progreso,
   duplicados, persistencia y política de rutas locales. Hoy los errores son texto
   y no hay máquina de transiciones ni historial de operaciones.
6. Interfaces de descubrimiento/descarga/verificación y política de ejecución;
   esta versión define únicamente los datos que intercambiarán esas etapas.
7. Aprobar la clasificación provisional de discrepancias de tamaño como fallos
   de transferencia, y decidir si se necesita un estado para verificación no ejecutada
   por error técnico. Verificación de fragmentos y ciclos de reintento quedan fuera
   del contrato actual.

## Compatibilidad con la primera versión

Se mantienen las clases y atributos existentes. Se añaden los valores `PARCIAL` a
`EstadoDescarga` y `EstadoRecurso`. Se endurecen las validaciones: registros pendientes
con bytes positivos, hashes contradictorios pendientes o integridad fallida sin
comparación ya no son válidos. Los consumidores deberán usar un estado y evidencia
coherentes. No se implementa una migración ni se modifica la estructura de solicitudes.

## Ejecutar pruebas desde la raíz (PowerShell)

```powershell
& .\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
```

Las pruebas añaden `src` al camino de importación sin instalar paquetes. `-B`
evita generar bytecode. Los identificadores y hashes de prueba son ficticios y
no representan datos, catálogos ni servicios de una institución real.
