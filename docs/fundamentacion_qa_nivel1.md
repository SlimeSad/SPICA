# PASO 74: expediente documental para QA/QC Nivel 1

## Dictamen y límites

**DOCUMENTACIÓN PARCIAL, REQUIERE COMPLEMENTOS.** Existe fundamento SENAMHI
comprobado para formular propuestas, especialmente límites puntuales de TEMP y
HR. No existe todavía evidencia suficiente para aprobar su aplicabilidad al
producto, activar algoritmos o presentar observaciones como científicamente válidas.
Los capítulos científicos de OMM no pudieron verificarse en este entorno.

Git inicial: limpio, rama `feature/suadc-http`, HEAD `2bbb5b4`, PASO 73 registrado.
Se revisaron los dos módulos científicos, Nivel 0 y los informes del diccionario.
No se modifican contratos, reglas, motor, conectores, dependencias o datos operativos.

Este expediente y [la matriz completa en JSON](fixtures/criterios_qa_nivel1.json)
son documentación, no configuración ejecutable. Las recomendaciones y bloqueos de
SPICA se distinguen de lo que afirma cada fuente. No se procesaron observaciones
reales ni se repitió el piloto del CSV.

## Fuentes, versiones y comprobaciones

Consulta realizada el 29 de octubre de 2026, hora local de Lima. Las fechas de
adquisición/comprobación no se usan como versiones ni fechas documentales.

| Referencia | Edición/fecha | Comprobación y alcance |
| --- | --- | --- |
| [SENAMHI MT-DRD-002](https://www.senamhi.gob.pe/load/file/00711SENA-95.pdf) | 02; aprobación visible 28-12-2022, p.2 | PDF oficial obtenido y leído; páginas críticas cotejadas como imágenes. Vigencia actual y firma criptográfica **NO VERIFICADAS** |
| Diccionario GBON/RBON ya adquirido | Versión y fecha documental desconocidas | XLSX local comprobado físicamente; hoja `DiccionarioDatos`, celdas referidas abajo |
| [Índice oficial WMO-No.8](https://community.wmo.int/site/knowledge-hub/programmes-and-initiatives/instruments-and-methods-of-observation-programme-imop/guide-instruments-and-methods-of-observation-wmo-no-8) | Encabezado declara 2021/2018 | Página e índice comprobados. El contenido de sus capítulos **NO VERIFICADO** |
| [Presentación provisional WMO-No.8](https://community.wmo.int/site/knowledge-hub/programmes-and-initiatives/instruments-and-methods-of-observation-programme-imop/guide-instruments-and-methods-of-observation-wmo-no-8-0/provisional-2026-edition-of-guide-instruments-and-methods-of-observation-wmo-no8) | 2026 provisional; página actualizada 02-10-2026 | Presentación comprobada; no equivale a una edición publicada aprobada ni a consultar los capítulos |

El navegador de investigación agotó la espera al abrir SENAMHI. Una consulta
HTTP puntual posterior obtuvo HTTP 200, `application/pdf`, **1.324.023 bytes**:

```text
SHA-256: 4f92172b99b351705b684f3a97c98ca16bb055174f0fe9253e9e65336a7ac9f8
```

Fue un GET con TLS verificado, sin redirecciones ni reintentos, tope 8 MiB,
conservado en un directorio temporal documental fuera de Git/RAW/staging. Se
usaron renderizado PDF y OCR disponibles en Windows, sin instalar dependencias.
El OCR solo ayudó a localizar contenido: las tablas sensibles se cotejaron
visualmente. La paginación PDF coincide con la numeración 1–30 del documento.
Se revisaron especialmente pp.2, 5, 7–20, 23 y 25; no se verificó autenticidad
criptográfica por observar una representación de firma digital.

La presentación OMM indica que los capítulos no modificados remiten a ediciones
publicadas **2024 para I/II/III y 2023 para V**. También presenta 2026 como
provisional sometida a aprobación. El índice general conserva una referencia más
antigua: no se mezclan esas ediciones ni se deduce cuál es la última vigente.
No se verificó una decisión posterior de aprobación de 2026.
[Evidencia: presentación oficial de la edición provisional](https://community.wmo.int/site/knowledge-hub/programmes-and-initiatives/instruments-and-methods-of-observation-programme-imop/guide-instruments-and-methods-of-observation-wmo-no-8-0/provisional-2026-edition-of-guide-instruments-and-methods-of-observation-wmo-no8).

Los enlaces de la biblioteca para los volúmenes [I](https://library.wmo.int/viewer/68695/?offset=3),
[III](https://library.wmo.int/viewer/68661/?offset=31) y
[V](https://library.wmo.int/viewer/68663/?offset=2) solo mostraron una envoltura HTML.
Una comprobación HTTP puntual del enlace público de descarga del volumen I también
dio **200, text/html**, no PDF; no se consideró una descarga científica comprobada.
Dos enlaces de capítulos provisionales examinados dirigieron a autenticación:
se detuvo esa vía sin credenciales ni intentos de superar el acceso. No se guardan
en el expediente URLs transitorias de sesión o autorización.

No se adjudican a OMM tablas, tolerancias, incertidumbres numéricas o umbrales cuyo
texto no fue leído. Su índice verifica dónde buscar: volumen I, capítulos 1, 2, 4 y
6; volumen III, capítulo 1; volumen V, capítulos 1–4. Allí quedan pendientes los
fundamentos de temperatura, humedad, precipitación, estaciones automáticas,
muestreo, gestión de calidad, reducción de datos y calibración.
[Evidencia: índice oficial WMO-No.8](https://community.wmo.int/site/knowledge-hub/programmes-and-initiatives/instruments-and-methods-of-observation-programme-imop/guide-instruments-and-methods-of-observation-wmo-no-8).

## Diccionario comprobado y contexto real disponible

Se leyó exclusivamente el diccionario anterior, sin descargarlo ni abrir sus
catálogos SQLite. Tamaño **10.815 bytes**, SHA-256:

```text
1851039a07682a3f202314f6f8811fc616cb4ca2a486c9e737fd8cea62a4b4dd
```

| Campo | Celda de descripción | Declaración conservada |
| --- | --- | --- |
| TEMP | B12 | Promedio horario; °C |
| HR | B13 | Promedio horario; % |
| PP | B14 | Total horario; unidad literal «milimetros por hora» |
| FECHA | F7 | aaaammdd |
| HORA | F8 | hhmmss |
| ID | B5 | Identificador del registro |
| ESTACION | B6 | Nombre de la estación automática |
| UBIGEO | C19/D19 | Alfanumérico de seis caracteres |

No documenta zona horaria, código físico estable, instrumento, calibración,
incertidumbre, período exacto de integración, política de faltantes o banderines
de calidad por observación. La frecuencia declarada no acredita continuidad.
El texto de PP no se sustituye por mm, intensidad instantánea o un acumulado
de otra duración. Se conserva la diferencia literal frente a `mm/h` del manual.

Los hallazgos previos de HORA de cinco/seis posiciones, UBIGEO decimal, extremos,
vacíos y falta de identidad física siguen siendo antecedentes del [PASO 71](perfilado_meteorologico.md)
y [Nivel 0](calidad_nivel0.md). No fueron recalculados aquí. Un nombre igual no
acredita continuidad de emplazamiento o instrumento. No se crean asociaciones
estación-variable ni se infieren códigos a partir de nombres o ID.

## Lectura del manual y distinción de niveles

El alcance institucional está en §3, p.5: datos automáticos meteorológicos e
hidrológicos del centro de procesamiento, a escala nacional. Incluye TEMP/HR/PP
y otras cinco variables; nomenclatura/unidades en §6.2.1, p.8. Su actualización
02 respecto de 01 se describe en §7, p.25; no demuestra vigencia en 2026.

La figura de p.7 y §§6.2.4–5, pp.8–10, separan automatización de intervención
especializada. Los límites duros y blandos se detallan en §§6.3.1.1–2, pp.11–14;
paso/persistencia en §§6.3.2.1–2, pp.14–19; revisión interna, espacial y satelital
en §§6.3.2.3–5, pp.20–22. Los umbrales locales requieren contexto de estación,
hora o sector/mes; no se recalculan para suplir tablas institucionales ausentes.
[Fuente: MT-DRD-002, versión 02](https://www.senamhi.gob.pe/load/file/00711SENA-95.pdf).

| SENAMHI | SPICA: relación limitada |
| --- | --- |
| Nivel I automático | No equivale al Nivel 1 interno de SPICA: las fronteras y alcances son diferentes |
| Nivel II manual | Requiere especialista y auxiliares; no se traduce a una regla automática de una fila |
| C / D / M / ND / SC, §6.2.2 p.8 | Conforme / dudoso / malo / no dato / sin control, según SENAMHI; no se convierten automáticamente a estados SPICA |

Nivel 0 de SPICA comprueba técnica/documentación; no demuestra que el producto
haya pasado el control institucional. Tampoco la ausencia de columnas de banderines
demuestra ausencia o éxito de controles anteriores. Un vacío no se convierte
automáticamente en ND, ni un resultado satisfecho en C institucional global.
Una discrepancia frente a un límite tampoco acredita por sí sola problema demostrado,
contaminación, fallo de sensor o causa antropogénica.

## Matriz de criterios candidatos

Cada fila es un tema candidato; sus IDs son provisionales de SPICA, sin atribuirlos
a SENAMHI u OMM. La [matriz JSON](fixtures/criterios_qa_nivel1.json) contiene por
fila: variable, prueba, fuentes/ediciones enlazadas por ID, localización, unidad,
resolución, condiciones, parámetros requeridos, criterio, resultado esperado,
interpretaciones incorrectas, auxiliares, compatibilidad, incertidumbres, estado y
recomendación. Permite comprobar esos campos sin una tabla de 18 columnas ilegible.

En la tabla siguiente se omite el prefijo común `L1-CAND-`. **CONDICIONADO** significa
que puede avanzar a diseño/revisión documental, nunca a ejecutar. **NO APLICABLE**
se refiere al uso actual con este CSV o a la automatización propuesta, no a que la
técnica sea científicamente inútil en otro contexto.

| Sufijo ID | Variable | Prueba / fuente verificada | Unidad / resolución | Compatibilidad y decisión |
| --- | --- | --- | --- | --- |
| TEMP-LIM | TEMP | MT §6.3.1.1(a), p.11, resumen p.23 | °C / horaria | CONDICIONADO: revisión de T_h frente al promedio y vigencia |
| HR-LIM | HR | MT §6.3.1.1(b), p.11, resumen p.23 | % / horaria | CONDICIONADO: definición, sensor, incertidumbre |
| PP-LIM | PP | MT §6.3.1.1(c), p.11, resumen p.23 | mm/h / horaria | CONDICIONADO: aclarar acumulación e intervalo |
| PP-24H | PP | MT §6.3.1.1(c), p.11 | mm/24h / período precedente | CONDICIONADO: ventana íntegra y notación P_h/PT_h |
| BLANDOS | TEMP, HR, PP | MT §6.3.1.2(a–c), pp.12–14 | Por variable / hora o mes según escala | CONDICIONADO: identidad, tablas y sector autorizados |
| TEMP-PASO | TEMP | MT §6.3.2.1(a), pp.14–15 | °C / retardos horarios | CONDICIONADO: reloj, cadencia y semántica de medición |
| HR-PASO | HR | MT §6.3.2.1(c), p.15 | % / horaria | CONDICIONADO: revisar adaptación temporal de la fuente |
| PERSISTENCIA | TEMP, HR | MT §6.3.2.2(a), pp.17–18 | °C, % / horas consecutivas | CONDICIONADO: resolver ambigüedades y resolución del sensor |
| EXTREMOS-INTERNOS | TEMP, HR | MT §6.3.2.1(b,d), p.15 | Por variable / misma hora | NO APLICABLE actual: faltan máximos y mínimos auxiliares |
| PP-TEMPORAL | PP | MT p.16(e) y p.19(e) | No define paso/persistencia para PP | NO APLICABLE: no extender por analogía |
| REVISION-HUMANA | TEMP, HR, PP | MT p.10 y pp.20–22 | Dependiente del caso | NO APLICABLE como regla automática de una fila |
| OMM-METROLOGIA | TEMP, HR, PP | Índices oficiales; capítulos científicos NO VERIFICADOS | Unidades del diccionario; resolución normativa desconocida | CONDICIONADO a obtener texto/edición y contexto metrológico |

Los parámetros requeridos están enumerados **sin valores**, vinculados a la fuente.
Los intervalos del manual se comprobaron como parte de la lectura de contexto,
pero no se transcriben como umbrales de GBON/RBON: su aplicabilidad al tipo exacto
de medición sigue pendiente. No hay límites numéricos en la fixture ni parámetros
ejecutables. Esto evita convertir una tabla institucional en exclusión universal.
Las recomendaciones instrumentales OMM, una vez obtenidas, deberán tratarse como
tales, separadas de requisitos operativos y reglas de calidad de observaciones.

## Aplicabilidad, auxiliares e incertidumbre

- **Puntuales TEMP/HR:** son los primeros temas para revisión. Un límite puntual
  no necesita convertir a UTC ni reconstruir HORA; sí necesita confirmar definición
  de variable, unidad, tipo de medición, contexto y autoridad documental. La
  incertidumbre y las tolerancias no se inventan ni se deducen de decimales escritos.
- **PP puntual:** antes debe aclararse total frente a intensidad, duración de
  integración, reinicios del sensor y unidad. El pluviómetro y sus correcciones,
  resolución y exposición son información pendiente, no hechos conocidos del CSV.
- **Ventanas y paso:** filas contiguas no prueban horas contiguas. Hace falta un
  reloj documentado, calendario, tratamiento de duplicados/faltantes y vinculación
  estable de serie e instrumento. No toda comparación temporal exige UTC si hay
  un tiempo civil coherente acreditado; hoy tampoco se acredita ese supuesto.
- **Persistencia:** constancia no demuestra avería. Se necesitan resolución,
  redondeo, ventana y política para secuencias parcialmente repetidas/saturación.
- **Blandos:** la identidad física, sectores, horarios y tablas oficiales son
  precondiciones. UBIGEO no se repara ni sustituye una sectorización climática.
  No se calculan estadísticas nuevas con el CSV ni se crean límites propios.
- **Extremos internos y revisión manual:** no se inventan auxiliares ausentes,
  estaciones vecinas, semejanza climática ni relaciones causales. Se requiere
  revisión humana o institucional; no se etiqueta automáticamente un extremo.

No hay base para declarar ninguna regla científica **directamente ejecutable hoy**.
No se propone excluir observaciones o alterar originales en la siguiente etapa.

## Riesgos y contradicciones que requieren respuesta

1. **Persistencia:** p.17 describe una secuencia completamente igual; p.18 usa una
   cadena de desigualdades y un «de lo contrario» que no constituye una partición
   lógica inequívoca para casos mixtos. HR incorpora además un caso de saturación.
   Se necesita interpretación institucional; no se escoge una fórmula por conveniencia.
2. **PP acumulada:** la nomenclatura de p.8 y la suma escrita en pp.11/23 requieren
   aclarar qué representa cada término P_h/PT_h. Una suma de acumulados ya agregados
   podría contar repetidamente; aquí no se decide ni ejecuta esa interpretación.
   El límite de una acumulación es una categoría distinta de la prueba de paso:
   no contradice por sí solo que PP carezca de la segunda en este manual.
3. **Muestreo y agregación:** el diccionario declara promedios y total horario;
   la descripción general de paso en p.9 menciona un valor instantáneo. No se
   presupone identidad de métodos de medición, integración o estadísticos.
4. **Vigencia y fuente primaria:** publicación en un dominio oficial y firma
   visible no prueban vigencia actual. Las referencias citadas por el manual no
   se consideran verificadas por haber sido citadas; no se les atribuyen umbrales.
5. **OMM:** el índice general y la presentación provisional refieren ediciones
   diferentes. Los capítulos no accesibles quedan NO VERIFICADOS; una fecha de
   actualización web no es fecha de aprobación del capítulo ni de su método.
6. **Transcripción:** el OCR no es autoridad para signos, subíndices o unidades.
   La futura especificación deberá conservar cita exacta y validación humana de
   cada fórmula antes de convertirla en parámetros o código.

No son errores demostrados de las observaciones. Son bloqueos de traducción
documental, adecuación del método y trazabilidad científica de SPICA.

## Registro declarativo y pruebas aisladas

Se usa el catálogo actual sin modificar sus contratos. La fixture contiene
**12 criterios**, nueve de ellos representables como propuestas aisladas.
Separarlos por variable produce **14 descriptores**; así no se mezcla una lista
de variables con otra de unidades sin conservar la correspondencia. Esto no
genera asociaciones estación-variable ni incorpora reglas a un catálogo operativo.

Cada registro comienza en PROPUESTA, versión interna `0.1.0`, con referencias,
condiciones parciales e incertidumbres. `parametros=()` y `metodo=None`. Las
fechas/versiones desconocidas permanecen `None`. Los tres temas no aplicables
se documentan, sin registrarlos como reglas por analogía.

El estado de verificación de cada fuente se conserva en la fixture documental:
el contrato actual no tiene un campo estructurado equivalente en ReferenciaCientifica.
En su representación aislada se mantienen el texto `2026 provisional`, la fecha
desconocida y contradicciones explícitas. No se inventa aprobación para suplir esa
limitación ni se amplía el contrato. Los descriptores nunca son la única evidencia
del expediente y no hay importación automática de esta fixture en producción.

Las siete pruebas nuevas verifican referencias/parametrización pendiente, registro
sin ejecución, bloqueo por metadatos ausentes, unidades literales, estado provisional,
contradicciones preservadas y exclusión de temas no aplicables. No realizan
solicitudes externas, operaciones RAW/SQLite ni evalúan observaciones.

## Decisiones para la siguiente etapa

Pueden avanzar **a especificación y revisión**, manteniéndose deshabilitados,
TEMP-LIM y HR-LIM. PP-LIM requiere primero la aclaración de semántica/unidad.
Ventanas, paso y persistencia quedan detrás de los bloqueos temporales y de
instrumento; blandos requieren tablas y correspondencias oficiales. No se
solicita implementar PP-TEMPORAL ni suplir máximos/mínimos inexistentes.

Antes de escribir algoritmos deberán obtenerse: confirmación de vigencia del MT,
correspondencia formal de sus variables con GBON/RBON, diccionario versionado,
reloj e integración documentados, identificación del instrumento/estación,
incertidumbre pertinente, respuesta a las ambigüedades y capítulos OMM de edición
publicada comprobados. Después corresponderá revisión científica explícita de
aplicabilidad y aprobación independiente de cualquier autorización de ejecución.

## Verificación técnica y preservación

Se ejecutó con Python **3.15.1 de `.venv`**, sin bytecode:

```text
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
Ran 832 tests in 90.618s
OK

.\.venv\Scripts\python.exe -B -m pip check
No broken requirements found.

git diff --check
Sin salida; código de salida 0.

git status --short
?? docs/fixtures/
?? docs/fundamentacion_qa_nivel1.md
?? tests/test_expediente_qa_nivel1.py
```

**832 aprobadas: 825 anteriores + siete nuevas; cero fallos, errores u omisiones.**
Se compararon los identificadores completos de las 825 anteriores con el registro
final del PASO 73: coincidencia exacta. No hay diferencias en archivos rastreados.
JSON, sintaxis de la prueba y whitespace de los tres archivos nuevos se comprobaron
directamente, pues `git diff --check` no incorpora archivos sin seguimiento.

El inventario de cinco archivos y cuatro directorios RAW/staging coincide antes
y después en tamaños, SHA-256 físicos, mtime, identificadores de archivo y enlaces;
también coincidía con el cierre anterior. Se excluye atime, que puede cambiar al leer.
CSV: **50.474.012 bytes**, SHA-256
`3d3e8a0a75e070d0b8111faf921be17140c3a0f9db2b4c25d72d99a15a950eab`.
Sintético: **57 bytes**, SHA-256
`82c649098a927a255181c8b05d18aec30594fa89571bad2792464f3ba255f4cb`.
SQLite: **32.768 bytes**, SHA-256
`946d2512795c5ae3a68113f63438110be66dee32488ad02e86d550da040d4a0d`.
El marcador y el archivo previo de staging también siguen intactos. RAW/temporales
permanece vacío, sin WAL, SHM, journal o residuos nuevos. Se leyó el catálogo
solamente como archivo binario, sin abrir una conexión SQLite operativa.

La evidencia auxiliar se conserva bajo `%TEMP%` en
`spica-paso74-246a70a9c0c4485f8faa7378c4b665bc`: PDF consultado, imágenes/OCR,
resultados de acceso, `unittest.log`, `resultado.json`, inventarios antes/después
y `preservacion.json`. No es almacenamiento definitivo de fuentes normativas ni
prueba de respaldo duradero. No se incorporan esos binarios al repositorio.

No se modificaron RAW permanente, staging o SQLite operativo ni se ejecutaron
migraciones, descargas del CSV, cálculos científicos, cambios de ACL, instalaciones,
commits o push. Las únicas consultas externas fueron documentales públicas,
puntuales y sin credenciales. Ningún criterio científico fue aprobado ni activado.
