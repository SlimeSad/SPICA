# PASO 75: evaluador experimental de límites numéricos

## Arquitectura y decisión de compatibilidad

Estado inicial: Git limpio en `feature/suadc-http`, HEAD `7a25216`, PASO 74
registrado. Se inspeccionaron catálogo científico, contratos Nivel 0, motor,
interpretación numérica, expediente y fixture documental.

Hay una incompatibilidad concreta con utilizar directamente ResultadoCientifico
para este ensayo: sus estados ejecutados requieren revisión APROBADA y evidencia
de ejecución. Construirlas para comparar fixtures exigiría simular una aprobación
que este paso prohíbe. Se detuvo esa integración; no se amplía ni altera la interfaz
del catálogo científico ni se producen resultados de ese contrato.

Se incorpora `spica.calidad.experimental`, un componente numérico puntual con
contratos propios. Reutiliza `interpretar_numero`, `LimitesPerfil` y los estados
de evaluación existentes. No duplica el parser, lector CSV, perfilador o registro
de reglas Nivel 0. El motor anterior continúa sin cambios. La integración futura
con ejecución científica queda pendiente de diseño y autorización específicos.

Archivos nuevos:

- `src/spica/calidad/experimental/modelos.py`: contratos sintéticos inmutables.
- `src/spica/calidad/experimental/limites.py`: comparación puntual sin I/O.
- `src/spica/calidad/experimental/__init__.py`: exports del laboratorio.
- `tests/test_limites_sinteticos.py`: pruebas con datos inventados y dobles de contrato.
- Este documento y [las fichas condicionadas TEMP-LIM/HR-LIM](especificaciones_temp_hr_lim.md).

No se modifican los archivos anteriores ni la fixture documental del PASO 74.

## Contrato y barreras de uso

Contrato/evaluador experimental **1.0.0**; interpretación numérica compartida
**1.0.0**. La versión de cada regla de ensayo se conserva como texto explícito
y acotado; no se ordenan versiones ni se selecciona una versión «actual» implícita.

| Contrato | Contenido y alcance |
| --- | --- |
| EvidenciaSintetica | ID `FIXTURE-...`, versión, descripción y tipo fijo de evidencia sintética sin aprobación científica |
| ObservacionSintetica | ID lógico, variable, texto original, unidad, modalidad, frecuencia y evidencia de fixture |
| ReglaLimitesSintetica | ID `EXP-LIM-...`, versión, variable, unidad/modalidad/frecuencia esperadas, dos Decimal, inclusividad explícita, evidencia y política numérica |
| ResultadoLimiteSintetico | Observación y regla completas, Decimal interpretado cuando procede, estado/motivo, versiones, identificación sintética y autorización operativa fija en False |

Los IDs no se calculan a partir de hashes. La observación y configuración se
conservan completas e inmutables, incluyendo evidencia, valores originales y
ambos extremos utilizados. No hay conversión de unidad ni normalización de textos.
Unidad, variable, modalidad y frecuencia deben coincidir literalmente.

La API acepta **exclusivamente los tipos exactos de ensayo**. Rechaza descriptores
ReglaCientifica, RevisionReglaCientifica, HabilitacionCientifica, registros/lectores
de adquisición, rutas y diccionarios. Los identificadores L0/L1 no son IDs de
ensayo; una referencia documental o un estado APROBADA no habilitan esta función.
La evidencia de parámetros debe ser de tipo EvidenciaSintetica; su fixture y
versión deben corresponder a las de los datos. Falta de evidencia produce NO_EVALUADO.

No se añade un cargador de reglas, conversiones desde el expediente, callbacks,
plugins, código por configuración, eval o exec. No se cambian
`HabilitacionCientifica.ejecucion_autorizada=False` ni sus políticas. El resultado
experimental tiene su propio `ejecucion_operativa_autorizada=False`: la comparación
de ensayo puede haberse completado sin autorizar ninguna operación científica.

**Alcance de la barrera:** es separación estructural para uso confiable de la
biblioteca, no un sistema de autenticación. Python no puede demostrar que un
llamador inventó una cadena en lugar de copiarla de datos reales. No se introducen
tokens, firmas o revisores simulados para fingir esa garantía. El flujo admitido
y probado construye solamente fixtures; no hay un puente desde fuentes reales.
Un uso deliberado que reetiquete observaciones reales queda fuera de esta API
experimental y de la autorización del PASO 75.

## Evaluación y resultados

`evaluar_limites_sinteticos(regla, observacion, *, cancelacion=None)` evalúa una
sola observación. No abre archivos, consulta bases, registra eventos, descarga
recursos o acumula lotes. El consumidor puede iterar sus fixtures y conservar
cada resultado; este paso no emite un informe global de finalización de un archivo.

Secuencia: validación de tipos, cancelación, evidencia, variable, unidad,
modalidad/frecuencia, interpretación Decimal y comparación con extremos.
Una comparación exige que las precondiciones anteriores hayan sido satisfechas.

| Estado | Significado limitado |
| --- | --- |
| CONDICION_SATISFECHA | Se satisface el intervalo inventado del ensayo |
| CONDICION_NO_SATISFECHA | No se satisface ese intervalo; no demuestra medición inválida |
| NO_EVALUADO_EVIDENCIA | No hay evidencia sintética de parámetros o no corresponde a la fixture/versión |
| NO_EVALUADO_VARIABLE | La variable no coincide; no se infieren equivalencias |
| NO_EVALUADO_UNIDAD | Unidad desconocida o distinta; no se convierte |
| NO_EVALUADO_MODALIDAD | Modalidad desconocida o distinta; instantáneo no equivale a promedio |
| NO_EVALUADO_FRECUENCIA | Frecuencia desconocida o distinta; no se reinterpreta una etiqueta |
| EVALUACION_INCOMPLETA | Cancelación o presupuesto numérico agotado |
| ERROR_TECNICO | Vacío, literal no numérico/no finito o fallo Decimal controlado |

Los motivos distinguen desconocimiento de incompatibilidad y los extremos excluidos
de valores estrictamente por debajo/encima. La interpretación finita conserva
Decimal exacto: no utiliza float, redondeo de contexto ni transforma el original.
NaN/Infinity no se comparan y no son observaciones científicamente rechazadas.
Los diagnósticos son códigos fijos, sin interpolar mensajes de excepciones.

`estado_evaluacion` reutiliza el enum existente: comparaciones completadas dan
COMPLETA; requisitos faltantes dan NO_EVALUADA; cancelación/presupuestos/error
técnico dan INCOMPLETA. Son estados individuales del ensayo, no de un archivo
ni de la calidad científica. Ningún registro se elimina.

Errores de configuración o de uso de la API se rechazan antes de evaluar mediante
TypeError/ValueError: límites invertidos, no finitos, presupuesto excesivo,
inclusividad no booleana o contratos incorrectos. Un intervalo puntual con ambos
extremos inclusivos es válido; si excluye ese único punto, se rechaza como vacío.

## Presupuestos y cancelación

Se usa la política numérica existente: por defecto 128 caracteres, 64 dígitos de
mantisa y exponente explícito absoluto hasta 1.000. Sus topes configurables siguen
siendo los del perfilador; aquí solo se usa su parte numérica, sin ejecutar lectura,
perfilado o índices. La observación admite hasta 65.536 caracteres originales; el
parser puede detenerse por su presupuesto menor y devolver ejecución incompleta.
Los límites de configuración también deben caber en ese presupuesto antes de usarse.

La cancelación usa threading.Event y es cooperativa: se comprueba antes de evaluar,
después de interpretar y después de comparar. No interrumpe una instrucción Decimal
en curso. KeyboardInterrupt se propaga. No quedan recursos de archivo que cerrar.
No hay reloj, aleatoriedad ni fechas variables en el resultado; para los mismos
datos/configuración y sin interferencia de cancelación el resultado es reproducible.

## Parámetros del ensayo y evidencia científica

Las pruebas usan `VAR_SINTETICA`, `u_sintetica`, modalidades/frecuencias de ensayo
y, como intervalo base inventado, **[−2,5; 7,5]**. No son parámetros meteorológicos
ni se presentan como límites oficiales. Las pruebas verifican cambios de versión,
límites puntuales, extremos inclusivos/exclusivos, datos especiales y presupuestos.
Las condiciones institucionales de TEMP/HR están solo en el documento de
especificación: no hay constantes normativas cargadas en el motor ni en las pruebas.

Los ensayos sobre estados del catálogo emplean dobles de contrato, sin registrar
decisiones humanas o aprobaciones ficticias. Se comprueba además el rechazo de las
14 propuestas reales del expediente declarativo y la preservación de Nivel 0.
Las pruebas anteriores conservan sus fixtures y no se alteran en este paso.

Una prueba prohíbe open/io.open, stat/scandir y sqlite3.connect durante el cálculo.
La suite completa utiliza los directorios temporales aislados ya existentes; el
caso de configuración por defecto sustituye Path.home por un directorio de prueba.
No se utilizan rutas RAW/staging operativas para comprobar preservación: acceder
a ellas, incluso solo para calcular hashes, está fuera de la autorización actual.

## Limitaciones y siguiente revisión

No hay ejecución sobre observaciones reales, activación, autorización operativa,
autenticación, aprobación de reglas, persistencia, cargador desde archivos,
orquestador de lotes, agregación temporal o controles espaciales. No se asignan
zonas, reconstruyen HORA/UBIGEO o modifican los datos originales.

El resultado requiere interpretación de alcance: fuera del intervalo inventado
significa únicamente condición experimental no satisfecha. El motor no diagnostica
contaminación, origen antropogénico, falla instrumental o validez de una medición.
La documentación/metadatos pendientes de TEMP-LIM/HR-LIM deben resolverse antes
de un diseño revisado y autorizado de piloto científico con datos reales.

Dictamen: **APTO CON RESTRICCIONES**, para revisión del laboratorio y de las
especificaciones. Ninguna regla científica real queda autorizada para ejecución.

## Verificación final

Se utilizó Python **3.15.1 de `.venv`**, con `-B`:

```text
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
Ran 872 tests in 89.363s
OK

.\.venv\Scripts\python.exe -B -m pip check
No broken requirements found.

git diff --check
Sin salida; código de salida 0.

git status --short
?? docs/especificaciones_temp_hr_lim.md
?? docs/evaluador_limites_sinteticos.md
?? src/spica/calidad/experimental/
?? tests/test_limites_sinteticos.py
```

**872 aprobadas: 832 anteriores + 40 nuevas; cero fallos, errores u omisiones.**
Se compararon los IDs completos de las 832 anteriores con el registro del PASO 74:
coincidencia exacta. Los seis archivos nuevos se revisaron directamente por sintaxis,
conflictos y whitespace, porque Git aún no los incluye en `diff --check`.
No hay diferencias en archivos rastreados ni cambios de commit/ramas/índice.

La suite se lanzó con una guardia temporal fuera del repositorio, activada solo
para el proceso de prueba mediante PYTHONPATH. Bloquea accesos Python a las rutas
operativas conocidas, conexiones SQLite correspondientes y conexiones reales de
red; comprueba también stat/lstat/access/readlink. No realiza consultas a esas
rutas para instalarse: las compara léxicamente. Registró **cero intentos bloqueados**.
No es una política de seguridad del sistema frente a código malicioso o alias
de archivos; es evidencia complementaria al aislamiento de fixtures y al examen
de las rutas de código. No se alteraron ACL ni configuración persistente.

Evidencia auxiliar en `%TEMP%`:

```text
spica-paso75-eab0607fc61c4a7aac0f9509a3ce8e79
```

`unittest.log` conserva las 872 pruebas, `resultado.json` el intérprete/comando,
conteos y comparación de IDs, y `guardia_resultado.json` la guardia instalada sin
intentos operativos o de red. La guardia no forma parte del código de SPICA.

RAW permanente, staging y SQLite operativo permanecieron **sin utilizar**. No se
hicieron inventarios, hashes o comprobaciones físicas sobre ellos en este paso:
no se declara una revalidación de integridad que habría requerido el acceso
expresamente prohibido. Las comprobaciones documentales se limitaron al repositorio
y al PDF/imagen temporal del manual ya conservados, sin abrir observaciones reales.
No hubo descargas, migraciones, instalaciones, commits o push.
