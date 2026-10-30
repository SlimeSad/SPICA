# PASO 76: aplicabilidad documental TEMP-LIM y HR-LIM

**Dictamen documental actual para ambos: INFORMACION_INSUFICIENTE.** Pueden
continuar hacia revisión científica humana; no están autorizados para ejecución.
La recomendación condicionada de los PASOS 74/75 no significa que hoy cumplan
los requisitos de COMPATIBILIDAD_DOCUMENTAL_DEMOSTRADA del verificador.

## Evidencia local reutilizada

Se utiliza exclusivamente el [expediente del PASO 74](fundamentacion_qa_nivel1.md),
su [fixture documental](fixtures/criterios_qa_nivel1.json) y las
[fichas del PASO 75](especificaciones_temp_hr_lim.md). No se volvieron a abrir el
CSV, XLSX, RAW, staging o SQLite operativo; tampoco se consultó internet.
Las conclusiones siguientes son un análisis de esa documentación registrada,
no una nueva comprobación física ni una ejecución sobre datos.

El expediente identifica el manual SENAMHI **MT-DRD-002 v02**, aprobación visible
28-12-2022: §6.3.1.1(a,b), p.11; resumen p.23; alcance §3, p.5. Fuente oficial
referenciada previamente: <https://www.senamhi.gob.pe/load/file/00711SENA-95.pdf>.
La lectura y transcripción fueron verificadas en los pasos anteriores; la vigencia
actual y autenticidad criptográfica continúan sin acreditarse.

Los límites candidatos son **−40 °C ≤ T_h ≤ 60 °C** y
**0 % ≤ HR_h ≤ 100 %**, ambos inclusivos según la fuente revisada. Solo se
transcriben documentalmente. No se convierten en parámetros ejecutables, pruebas
numéricas ni reglas activadas. El JSON anterior conserva `valor: null`.

El diccionario GBON/RBON declara TEMP y HR como **promedio horario**, con unidades
literales `°C` y `%` (B12/B13). PP declara **total horario**, unidad literal
`milimetros por hora` (B14). No se sustituye por `mm/h` ni se interpreta como
intensidad instantánea. La versión y fecha documental del diccionario permanecen
desconocidas. La fecha de adquisición no las suple.

## Matriz de aplicabilidad pendiente

O = obligatorio para justificar este traslado documental; C = condicional según
el método/alcance finalmente revisado. Son requisitos de revisión de SPICA,
no afirmaciones de que SENAMHI exija todos esos campos para esta subregla.

| Requisito | Tipo | TEMP-LIM | HR-LIM | Evidencia faltante o límite |
| --- | --- | --- | --- | --- |
| Identidad de variable | O | T_h frente a TEMP del producto | HR_h frente a HR del producto | Correspondencia formal entre notación del manual y variable publicada; coincidencia nominal no basta |
| Unidad literal | O | °C coincide documentalmente | % coincide documentalmente | Mantener literal; falta completar versión/fecha del documento del producto |
| Modalidad | O | Fuente dice temperatura del aire horaria | Fuente dice humedad relativa horaria | No se acredita que esas subreglas respalden expresamente el promedio GBON/RBON |
| Agregación | O | Promedio declarado en B12 | Promedio declarado en B13 | Definición de muestras, estadístico, intervalo de integración y porcentaje de datos válidos |
| Frecuencia/cadencia | O/C | Etiqueta horaria | Etiqueta horaria | Hora declarada no demuestra continuidad. Para una prueba puntual no se necesita reconstruir una secuencia; sí resolver la modalidad horaria |
| Producto y alcance institucional | O | No demostrados completamente | No demostrados completamente | Correspondencia GBON/RBON con datos/procedimientos del centro de procesamiento cubierto por el manual |
| Versión y vigencia | O | Manual v02 conocido; vigencia no verificada | Igual | Confirmación de vigencia/edición y diccionario versionado/fechado |
| Instrumento y tipo de estación | O | Automática declarada; sensor no identificado | Automática declarada; sensor y referencia de HR no identificados | Metadatos pertinentes, exposición, resolución, calibración y alcance por instrumento; no se inventan modelos |
| Identidad de estación/serie | O/C | Identidad estable y cambios no acreditados | Igual | Necesaria para vincular evidencia instrumental/local a una serie; continuidad adicional para métodos temporales o condicionados por estación |
| Cobertura geográfica/ambiental | O/C | Alcance nacional del manual, pertenencia concreta no demostrada | Igual | Demostrar pertenencia al ámbito; si una condición no restringe una dimensión, justificarlo documentalmente |
| Parámetros e inclusividad | O | Intervalo fuente documentado | Intervalo fuente documentado | Revisión humana de correspondencia, versión y pertinencia; no parametrizado para el producto |
| Incertidumbre | O | No cuantificada para el producto | No cuantificada; referencia y saturación sin aclarar | Política de tratamiento, tolerancias y evaluación cerca de extremos, sin inventar bandas |
| Zona horaria | C | No necesaria por sí sola para rango puntual | Igual | Sí puede ser necesaria para ventanas, retardos o comparaciones temporales; ninguna asignación automática |
| Contradicciones | O | No resolver promedio/instantánea por analogía | Igual | Falta de equivalencia no demuestra incompatibilidad; conservar cualquier respuesta documental contradictoria |
| Aprobación y operación | Separadas | Ninguna concedida | Ninguna concedida | Este diagnóstico no crea aprobaciones ni permisos |

No se declara INCOMPATIBILIDAD_DOCUMENTADA entre el manual y el promedio: no se
ha comprobado que la definición de T_h/HR_h excluya ese promedio. Tampoco se
declara una equivalencia por compartir unidad y etiqueta horaria. La mención de
valor instantáneo en la descripción general de paso no prueba la semántica de
estas subreglas de límites. Por ello falta información, no corresponde escoger
una interpretación ni ejecutar para decidirla.

Una afirmación institucional documentalmente verificada sigue referida a su
alcance; no acredita automáticamente la correspondencia con otro producto.
SHA-256 solo identifica la copia registrada. No demuestra autenticidad del emisor,
vigencia ni aprobación de SPICA por SENAMHI.

## Información que el CSV no permite inferir

El ID del registro no es código físico de estación; un nombre o UBIGEO no acredita
identidad, emplazamiento ni continuidad. No se reconstruyen HORA/UBIGEO ni se
deducen códigos. No se infieren sensor, muestreo, exposición, reemplazos,
calibración, incertidumbre, reloj, zona horaria o controles institucionales
superados a partir de decimales, frecuencia declarada o ausencia de banderines.

Los criterios que dependan de estación requieren vinculación estable a
emplazamiento/instrumento, historial de cambios y alcance documental. Los límites
puntuales no requieren por sí solos una serie continua. Paso, persistencia,
ventanas y límites locales sí pueden requerir cadencia, calendario, política de
duplicados/faltantes y continuidad acreditadas. No se presupone que UTC sea la
única representación posible; aquí no se acredita ni asigna una alternativa.

## Documentos y aclaraciones que solicitar a SENAMHI

1. Confirmación de edición vigente y alcance aplicable de MT-DRD-002; anexos,
   modificaciones o sustituciones que afecten las subreglas de TEMP/HR.
2. Diccionario GBON/RBON con versión y fecha documental, identificación del
   producto/recurso y correspondencia formal de TEMP/HR/PP con las variables del
   manual. No solicitar credenciales ni información personal innecesaria.
3. Especificación de promedio horario: muestras, integración, referencia del
   intervalo, completitud mínima, estadístico, redondeo y tratamiento de faltantes.
   Aclarar expresamente si las subreglas de límites se aplican a ese producto.
4. Catálogo estable de estaciones/series y vinculación a los instrumentos
   pertinentes, cambios de emplazamiento/sensor y períodos de validez de metadatos.
5. Especificaciones instrumentales pertinentes: tipo, exposición, resolución,
   calibración, incertidumbre y tolerancias; para HR, definición/referencia y
   tratamiento de saturación; para TEMP, definición de medición del aire.
6. Alcance geográfico/ambiental y excepciones del criterio; justificación de las
   dimensiones que no impongan restricciones para esta subregla.
7. Política de incertidumbre y decisión cerca de extremos, representación de
   faltantes y significado de banderines institucionales por observación/producto.
8. Para futuras reglas temporales: reloj/zona, calendario, cadencia real,
   continuidad y política de duplicados/interrupciones, sin reparar HORA localmente.
9. Para PP antes de avanzar: aclaración de total/acumulación frente a intensidad,
   intervalo, reinicios y unidad literal. Los antecedentes no autorizan su conversión.

Estas son solicitudes propuestas, **no se enviaron mensajes** ni se atribuye
una respuesta, autorización o aprobación institucional inexistente. Los capítulos
OMM científicos pendientes del expediente tampoco se consideran verificados por
estar citados en el manual.

## Recomendación de continuidad

TEMP-LIM y HR-LIM pueden continuar hacia revisión científica humana por tener
una condición puntual identificada y transcrita de una fuente institucional.
Esa revisión deberá resolver primero la modalidad/agregación, el alcance y la
evidencia metrológica pertinente. No conviene desbloquearlos solo por conocer
los extremos numéricos. No se aprueban ni descartan observaciones por excedencias.

PP-LIM mantiene un bloqueo adicional de semántica/unidad; los criterios de paso,
persistencia, blandos y ventanas conservan los bloqueos del expediente anterior.
No se implementan durante este paso. Una futura aprobación científica deberá
mantenerse separada de una autorización operativa expresamente revisada.

Dictamen del PASO 76: **APTO CON RESTRICCIONES** para diagnóstico documental.
TEMP/HR: **APTO PARA REVISIÓN CIENTÍFICA**, con información insuficiente para
demostrar aplicabilidad al producto y sin ejecución autorizada.
