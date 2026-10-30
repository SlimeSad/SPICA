# PASO 75: especificación preliminar TEMP-LIM y HR-LIM

**Estado de ambas especificaciones: PROPUESTA CONDICIONADA. Sin autorización de
ejecución sobre observaciones reales.** Este documento no registra aprobaciones,
no parametriza el catálogo y no cambia la fixture del PASO 74.

## Evidencia utilizada y alcance

Se reutiliza exclusivamente la documentación comprobada en el
[expediente del PASO 74](fundamentacion_qa_nivel1.md). No hubo nuevas consultas
externas ni descargas. Se cotejó la imagen local conservada de la página 11 del
PDF institucional, fuera del RAW operativo. La copia PDF documental conserva
1.324.023 bytes y SHA-256
`4f92172b99b351705b684f3a97c98ca16bb055174f0fe9253e9e65336a7ac9f8`.

Fuente: [SENAMHI MT-DRD-002, versión 02](https://www.senamhi.gob.pe/load/file/00711SENA-95.pdf),
§6.3.1.1(a,b), página 11, subreglas 1 y 2; tabla resumen en p.23. La fecha visible
de aprobación es 28-12-2022. La vigencia actual y autenticidad criptográfica siguen
sin verificar. El ámbito institucional es el centro de procesamiento de datos
automáticos meteorológicos e hidrológicos, conforme a §3, p.5.

La transcripción matemática siguiente describe esa fuente en su contexto, sin
demostrar que la misma modalidad sea aplicable al producto GBON/RBON. No se
incorpora ningún valor numérico normativo al motor, parámetros de prueba o fixture.
Las referencias OMM citadas por SENAMHI no se consideran consultadas por esa sola
cita; las limitaciones documentales del PASO 74 permanecen abiertas.

## Fichas condicionadas

| Aspecto | TEMP-LIM | HR-LIM |
| --- | --- | --- |
| ID candidato SPICA | L1-CAND-TEMP-LIM | L1-CAND-HR-LIM |
| Variable original | TEMP | HR |
| Medición declarada por GBON/RBON | Temperatura promedio horaria | Humedad relativa promedio horaria |
| Unidad literal del diccionario | °C | % |
| Concepto del manual | Temperatura del aire horaria, T_h | Humedad relativa horaria, HR_h |
| Frecuencia de referencia | Horaria | Horaria |
| Agregación/integración del manual | Equivalencia con el promedio del producto no acreditada | Equivalencia con el promedio del producto no acreditada |
| Fuente y apartado | MT-DRD-002 v02, §6.3.1.1(a), p.11, subregla 1 | MT-DRD-002 v02, §6.3.1.1(b), p.11, subregla 2 |
| Condición institucional documentada | −40 °C ≤ T_h ≤ 60 °C | 0 % ≤ HR_h ≤ 100 % |
| Extremo inferior | Inclusivo | Inclusivo |
| Extremo superior | Inclusivo | Inclusivo |
| Estación/instrumento | Estación automática dentro del alcance institucional; modelo de sensor desconocido para el producto | Estación automática dentro del alcance institucional; modelo de sensor desconocido para el producto |
| Resultado de esta subregla en la fuente | C si satisface, M si no satisface | C si satisface, M si no satisface |
| Resultado actual en SPICA | No ejecutada; propuesta condicionada | No ejecutada; propuesta condicionada |
| Compatibilidad documental | Coinciden nombre/unidad y referencia horaria; faltan modalidad y aplicabilidad completas | Coinciden nombre/unidad y referencia horaria; faltan modalidad y aplicabilidad completas |

Los valores del diccionario proceden de la hoja `DiccionarioDatos`, celdas B12
y B13, con SHA-256 de referencia
`1851039a07682a3f202314f6f8811fc616cb4ca2a486c9e737fd8cea62a4b4dd`.
En este paso no se abre nuevamente ese original ni su almacenamiento. Fecha y
versión documental siguen desconocidas, como consta en el expediente anterior.

**Promedio horario no significa medición instantánea.** Que ambos conceptos usen
la misma unidad y una etiqueta horaria no demuestra que tengan igual muestreo,
integración, exposición o significado instrumental. La descripción general de
paso en p.9 tampoco autoriza trasladar un criterio instantáneo al promedio.
Ninguna transformación temporal se realiza para obtener esa supuesta equivalencia.

Los códigos institucionales se citan para trazabilidad. Satisfacer una subregla
no significa haber superado el conjunto de controles. Un incumplimiento no se
traduce automáticamente a una medición científicamente inválida, problema demostrado
o causa instrumental. No se descartan extremos ni se modifican valores.

## Condiciones de aplicabilidad pendientes

Para ambos criterios debe establecerse explícitamente:

1. Correspondencia entre la variable institucional y la modalidad concreta del
   producto: promedio, muestras que lo componen e intervalo de integración.
2. Alcance de la norma y vigencia de la versión; correspondencia del producto con
   las estaciones automáticas y procesos cubiertos.
3. Instrumento, exposición y configuración pertinentes, resolución, calibración,
   tolerancias e incertidumbre. No se atribuye un modelo, altura o exactitud al CSV.
4. Identificación suficiente de estación/serie y cambios de sensor o ubicación,
   sin convertir ID del registro, nombre o UBIGEO en identidad física acreditada.
5. Política para faltantes, no finitos, incertidumbre cerca del extremo y evidencia
   insuficiente. El intervalo transcrito no aporta por sí solo una banda de guarda.

Para HR se necesita además aclarar la definición instrumental de humedad relativa,
su referencia y el tratamiento pertinente de saturación/incertidumbre. Para TEMP
se debe documentar la medición de aire y las condiciones de exposición pertinentes.
Estos son requisitos de revisión de SPICA, no datos que se afirmen presentes en el
CSV ni recomendaciones instrumentales OMM que se hayan verificado.

Un límite puntual no exige ordenar una serie ni convertir a UTC. La zona horaria
desconocida y HORA discrepante permanecen sin resolver; no se reconstruyen para
esta especificación ni se convierten observaciones instantáneas en promedios.
Una futura prueba dependiente de ventanas requeriría evidencia temporal adicional.

## Qué falta para autorizar un piloto real

La futura autorización debe separar revisión documental, aplicabilidad y permiso
de ejecución. Será necesario un expediente que contenga:

- Fuente y versión vigentes comprobadas, localización de la condición e inclusividad.
- Diccionario y documentación de modalidad/instrumento suficientes, con las
  dimensiones aplicables justificadas y las incertidumbres sin inventar.
- Resolución explícita de contradicciones y aprobación científica por quien tenga
  competencia, identificando regla, versión, parámetros, unidad y alcance.
- Un diseño revisado de autorización operativa independiente del estado APROBADA.
  El presente paso no incorpora ese diseño ejecutable ni un interruptor de activación.
- Autorización nueva del usuario para un piloto acotado, con datos/activo de origen,
  variables y recursos autorizados, presupuestos y criterios de detención explícitos.
- Conservación del original, trazabilidad de resultados, no exclusión automática
  y comprobaciones técnicas correspondientes al procedimiento futuro autorizado.

Los campos `valor: null` de la fixture anterior continúan pendientes de
parametrización autorizada. Conocer los números escritos en la fuente no acredita
su aplicabilidad ni permite sustituir esos desconocidos automáticamente.

## Relación con el laboratorio experimental

El [evaluador sintético](evaluador_limites_sinteticos.md) prueba únicamente
comparaciones numéricas genéricas. Sus límites inventados no son los de estas
fichas y su variable no se denomina TEMP ni HR. No hay adaptador desde estos
candidatos, cargador de sus parámetros ni productor operativo de ResultadoCientifico.

Dictamen de las fichas: **APTO PARA REVISIÓN CIENTÍFICA**, con aplicabilidad
pendiente. Ninguna de ellas ha sido aprobada o activada para el CSV de SENAMHI.
