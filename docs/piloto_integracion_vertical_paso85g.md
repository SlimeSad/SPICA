# PASO 85-G — Piloto vertical estructural sintético ejecutado

Fecha: **2026-11-11, America/Lima**. Se revisaron los tres informes 85-F y las
interfaces reales antes de editar. Git inicial limpio, rama feature/suadc-http,
HEAD **13744ab**, «SUADC: auditoria integral de arquitectura y dependencias».
El 85-F quedó consolidado. Contrato y límites:
[contrato mínimo](contrato_ejecucion_integrada_paso85g.md). Dictamen y pendientes:
[brechas de integración](brechas_integracion_paso85g.md).

## 1. Ensayo previo y archivos creados

Antes de crear el auxiliar se ejecutó una composición con los componentes
existentes, sin modificar sus archivos. Produjo una fixture de 572 bytes,
dos evaluaciones de 60 resultados, 60 coincidencias y temporales eliminados.
Eso descartó una incompatibilidad mayor; el incremento solo añade la envolvente
de ejecución, comprobaciones de enlace y pruebas de errores.

Archivos nuevos:

- [herramientas/piloto_integracion_85g.py](../herramientas/piloto_integracion_85g.py).
- [tests/test_integracion_vertical_85g.py](../tests/test_integracion_vertical_85g.py).
- [contrato_ejecucion_integrada_paso85g.md](contrato_ejecucion_integrada_paso85g.md).
- Este informe.
- [brechas_integracion_paso85g.md](brechas_integracion_paso85g.md).

No se cambia src/spica, main.py, .gitignore, requirements.txt, .venv, las reglas,
JSON 0.1.0, consumidor, conciliador o documentos históricos. No hay cliente HTTP,
parser, motor QA o almacenamiento definitivo alternativos.

## 2. Entrada, operación y linaje realmente observados

El piloto métrico se ejecutó entre **2026-11-12T00:59:38.916771+00:00** y
**2026-11-12T00:59:49.989329+00:00** (11 de noviembre en America/Lima).
Son tiempos técnicos del ensayo, no fechas de observaciones. Se usó la fixture
generada por fixture_csv_85g: encabezado de 16 columnas del perfil existente y
dos filas declaradamente ficticias. HORA=hora-incierta, UBIGEO=UBIGEO-INCIERTO,
TEMP=+001.250, HR=56.75 y PP=4.00 permanecen literales; no se asignan unidades.

| Identidad / evidencia | Valor observado en ejecución principal |
|---|---|
| Ejecución | piloto-cierre-85g |
| Proyecto / objeto | proyecto-ficticio-85g / objeto-ficticio-85g |
| Entrada de archivo | csv-ficticio-85g |
| Evaluación reproducida | evaluacion-cierre-85g, espacio spica:experimental:85g |
| Tarea declarada | paso85g-cierre; ningún planificador ejecutó un plan |
| Fuente | SPICA-SINTETICA / fixture-85g |
| Producto / recurso | producto-ficticio-85g / recurso-ficticio-85g |
| URL ficticia del doble | `https://spica-85g.invalid/fixture.csv`; nunca conectada |
| Solicitudes simuladas | Una por llamada, método GET de MockTransport, estado 200; cero solicitudes externas |
| Bytes declarados / almacenados | 572 / 572 |
| SHA-256 físico RAW | 6894bcce331d4af7db8e4a2f6008a8617604d01e8dbf4cc9805dc8cf37e8ee1b |
| asset_id de prueba | 24d72ce198df4b2d96dba755792ff00a |
| Catálogo de prueba | Recurso consultado, revisión local 1; método MockTransport_sin_red, evidencia técnica enlaza ese asset_id |
| adquisicion_id / documento QA | None / None; no se inventa registro HTTP documental |
| Estado final | concluida_estructuralmente, fase cierre |
| Ejecución científica / autorización operativa | False / False |

Ubicación **histórica, eliminada al cerrar**, bajo TEMP privado:

```text
spica-85g-jqf0wn4b/raw/sha256/68/6894bcce331d4af7db8e4a2f6008a8617604d01e8dbf4cc9805dc8cf37e8ee1b
```

Los bytes atravesaron ClienteHTTP.descargar y el staging real del adaptador,
la copia/publicación física de AlmacenRAW y sus verificaciones de recuperación.
La prueba física además relee la ruta publicada, compara el contenido exacto con
la fixture y calcula SHA-256 con hashlib.file_digest; observa al menos cinco
recuperaciones reales. No se afirma verificación de ningún original institucional.

El catálogo científico es otra base temporal. Guarda fuente/producto/recurso,
no una disponibilidad remota o capacidad institucional VERIFICADA. Se consulta
después y se contrasta la entidad completa/revisión/identidad. ProcedenciaQA
recibe fuente/recurso/asset/SHA mediante ProcedenciaLocal; no se convierte esa
referencia en una comprobación física realizada por QA. Esta existe separadamente
en el tramo RAW. Las fechas técnicas no se usan para localizar FECHA/HORA.

La función hace dos pasadas contra el mismo activo. Después de cada evaluación
cerrada vuelve a recuperar/verificar RAW. La segunda ejecución del piloto utiliza
otra evaluación y otro temporal/activo: **671b379a9e0c4f4380f9a82a7a0d9d58**,
mismo SHA/tamaño. Son dos adquisiciones simuladas separadas; no identidad de
observación ni prueba de deduplicación física entre almacenes diferentes.

## 3. Resultados QA0 y restricciones por reproducción

| Resultado por pasada A o B | Cantidad |
|---|---:|
| Filas de datos / reglas seleccionadas | 2 / 22 |
| Resultados individuales | 60 |
| COMPROBACION_SATISFECHA | 34 |
| NO_EVALUADO | 26 |
| ALERTA_DOCUMENTAL / PROBLEMA_TECNICO / EVALUACION_INCOMPLETA | 0 / 0 / 0 |
| Restricciones informativas | 60 |
| Restricciones bloqueantes | 206 |
| Bytes JSON UTF-8 aceptados, lote principal | 277884 |

**2 × (18 + 4×3) = 60**, no 60 observaciones. Cada definición VAL produce un
resultado por TEMP/HR/PP y fila; las otras 18 definiciones producen uno por fila.
No se suman las dos reproducciones para afirmar 120 observaciones. InformeQA
COMPLETA significa recorrido y evaluación concluida en su alcance, incluidos
los 26 NO_EVALUADO que conservan la falta de evidencia o barrera de alcance.

| Regla original | Satisfechos | No evaluados |
|---|---:|---:|
| L0-EST-001 | 2 | 0 |
| L0-VAL-001 | 6 | 0 |
| L0-VAL-002 | 6 | 0 |
| L0-VAL-003 | 6 | 0 |
| L0-VAL-004 | 0 | 6 |
| L0-TMP-001 | 0 | 2 |
| L0-TMP-002 | 0 | 2 |
| L0-TMP-003 | 0 | 2 |
| L0-TMP-004 | 0 | 2 |
| L0-ID-001 | 2 | 0 |
| L0-ID-002 | 0 | 2 |
| L0-ID-003 | 2 | 0 |
| L0-ID-004 | 0 | 2 |
| L0-ID-005 | 2 | 0 |
| L0-PROV-001 | 2 | 0 |
| L0-PROV-002 | 2 | 0 |
| L0-PROV-003 | 0 | 2 |
| L0-PROV-004 | 2 | 0 |
| L0-PROV-005 | 2 | 0 |
| L0-PROV-006 | 0 | 2 |
| L0-PROV-007 | 0 | 2 |
| L0-PROV-008 | 0 | 2 |
| Total | 34 | 26 |

Ambos lectores llegaron a EOF y cerraron. El arnés conserva InformeLecturaCSV e
InformeQA reales, versiones y reglas ejecutadas. Exporta cada ResultadoQA con
ContextoExportacionQA, sin asdict directo, y contrasta las restricciones oficiales
con los conteos del consumidor. Las pruebas también comparan códigos por resultado,
no solo totales. Los desconocidos documentales siguen declarados ausentes.

## 4. Exportación, comparación y confianza

| Comparación observada | Estado | Coincidencias | Evidencia / límite |
|---|---|---:|---|
| A/B del activo principal | COINCIDENCIA | 60 | Dos llamadas reales a QA/lector; mismo activo y contexto; documentos completos idénticos |
| A/C, evaluación independiente | NO_COMPARABLE | 0 | ambitos_de_evaluacion_sin_correspondencia; no se alinean valores iguales |
| A/D, diagnóstico sintético alterado | CONFLICTO | 59 | Un identidad_resultado_reutilizada; ambos lotes válidos individualmente y conservados |

D es una **variante adversarial reexportada**, no una nueva ejecución QA real
demostrada. Se modifica una copia del diagnóstico y se valida con el consumidor;
el lote A original permanece intacto. Esto demuestra por qué JSON aceptado no
prueba ejecución efectiva. La conciliación compara 120 representaciones por par,
no 120 eventos científicos, y no elimina el conflicto mediante deduplicación.

Huella de representación canónica del lote A/B principal:

```text
7e356767ba08d0f447e17b30a5b4fddea31e7921a0889fc50091c7ff27ef3c6d
```

Es distinta del SHA físico del CSV. Incluye datos del contexto/procedencia: otra
adquisición con nuevo asset_id no tiene por qué reproducirla. En la evaluación
independiente se observaron 278304 bytes por lote y otra huella. Ninguna huella
es firma de origen, identidad institucional o autorización.

Traza real principal, resumida sin omitir el cierre:

```text
PLANIFICADA
validacion → adquisicion_simulada: bytes_incorporados_y_controlados
catalogo: recurso_consultado_sin_capacidad_institucional
recuperacion_A → qa_A: evaluacion_cerrada_y_original_recomprobado
exportacion_A → consumo_A: restricciones_nativas_y_consumidas_coinciden
recuperacion_B → qa_B: evaluacion_cerrada_y_original_recomprobado
exportacion_B → consumo_B: restricciones_nativas_y_consumidas_coinciden
conciliacion: reproducciones_del_mismo_activo_coinciden
cierre: temporales_eliminados → concluida_estructuralmente
```

## 5. Pruebas adversariales y correcciones realizadas

Las pruebas nuevas usan motores reales y fallos puntuales controlados:

| Situación | Resultado exigido y comprobado por las pruebas |
|---|---|
| Control SHA/tamaño distinto del físico | FALLIDA antes de catálogo/QA; no autocorregir el control |
| Corrupción del contenido RAW de prueba | Recuperación real detecta discrepancia; fase COMPROBACION; se conserva el activo_id conocido aunque la adquisición no retorne |
| Transferencia interrumpida / escritura staging fallida | FALLIDA con fase DESCARGA; un intento simulado, sin consumidores aceptados |
| SQLite o identidad de catálogo incompatible | FALLIDA; activo de prueba no equivale a éxito de toda la cadena |
| Campo estructural ausente / lectura incompleta | INCOMPLETA; informes y resultados nativos preservados; sin exportar un lote completo ficticio |
| Restricción documental no satisfecha | Evaluación estructural puede concluir con NO_EVALUADO; ciencia/autorización siguen False |
| Restricciones omitidas en JSON | Consumidor real rechaza el lote atómicamente |
| Conteo bloqueante perdido en el enlace | Fallo de integración restricciones_no_conservadas; no conciliación satisfactoria |
| Límite QA, JSON o del consumidor | INCOMPLETA; se distingue de rechazo contractual |
| Cancelación previa, entre fases o en HTTP | CANCELADA, no FALLIDA por defecto ni CONCLUIDA; cierre de temporales |
| KeyboardInterrupt | Se propaga tras cerrar y eliminar el temporal propio |
| TEMP operativo o resolución de raíz prohibida | Rechazo antes de inspección; comprobación específica de que no se resuelve esa referencia |
| Red/backend HTTP real/procesos/ciencia | Mocks de prohibición y guardia; caso positivo debe seguir concluyendo mediante los componentes internos |

La primera ejecución de las 34 pruebas iniciales produjo **33 aprobadas y un error
de fixture**, 21.321 s: Python 3.15 exige TypeError para replace de init=False.
Se corrigió la expectativa, no un contrato estable. Se añadieron después pruebas
para no resolver la referencia operativa y para propagar validación incompleta,
hasta **36 pruebas nuevas**. Los subcasos no aumentan ese contador.

Se completó la traza del auxiliar para conservar el ID de activo informado por
ErrorIntegracionHTTPRAW en fallos posteriores a publicación. No se reconstruye un
ActivoRAW inexistente, inventa su estado ni se modifica el error del adaptador.
Se volvieron a ejecutar las verificaciones después de ese último ajuste.

Una invocación del driver externo falló antes de ejecutar unittest porque la
guardia no admitía executable=None de subprocess en Windows. Se corrigió esa
instrumentación temporal y se conservaron los registros; no se contabiliza como
una suite aprobada o un fallo de los motores. La primera preparación de guardia
en sandbox encontró permisos de temporales privados de Python 3.15; las corridas
se hicieron como propietario, sin cambiar ACL.

## 6. Verificación final

| Verificación realmente ejecutada | Resultado |
|---|---|
| Dirigidas de integración antes de añadir el ID parcial al informe | 208 aprobadas, 0 fallos/errores, 76.049 s |
| Pruebas nuevas sobre el código final | **36 aprobadas**, 0 fallos/errores, **25.456 s** |
| Suite completa final, después del último cambio de código | **1745 aprobadas**, 0 fallos, 0 errores y 0 omitidas, **205.460 s**, código 0, salida OK |
| Conservación de pruebas anteriores | IDs reales del log contrastados con AST de tests: **1709 anteriores + 36 nuevas**, 1745 IDs únicos, sin faltantes |
| pip check con .venv, sin índices | **No broken requirements found.**, código 0 |
| Guardia de nuevas/dirigidas/suite/pip/piloto | Cero conexiones/DNS, accesos a rutas operativas conocidas, SQLite operativo o procesos no admitidos |
| git diff --check | Código 0, sin salida |
| git diff --exit-code HEAD / git diff --cached --exit-code | Código 0, sin diferencias en archivos registrados o índice |

Hubo una primera suite de 1745 aprobadas en 196.121 s; se repitió por el ajuste
de linaje de fallos. El resultado de cierre es el de **205.460 s**. No se suman
corridas, dirigidas o subcasos. El antecedente de 1709 del 85-E se distingue de
las **1745 efectivamente ejecutadas en este paso**. Después de la suite final
solo se completó documentación, sin cambiar Python ni dependencias.

Comandos usados, con ruta de importación temporal y logs en carpeta privada:

```powershell
$env:PYTHONPATH="$env:TEMP\spica-85g-auditoria-t05v0bnc\guardia;$PWD\src;$PWD\tests;$PWD"
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -B -m unittest test_integracion_vertical_85g -v
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
$env:PIP_NO_INDEX='1'
$env:PIP_DISABLE_PIP_VERSION_CHECK='1'
$env:SPICA_85G_PIP_CHECK='1'
.\.venv\Scripts\python.exe -B -m pip check
git diff --check
git diff --exit-code HEAD
git diff --cached --exit-code
git status --short
```

Las pruebas se invocaron mediante un driver externo con subprocess y los mismos
argumentos, para conservar stdout/stderr UTF-8 completos sin el formato de errores
nativos de PowerShell. La guardia se heredó en los procesos Python. Para pip se
admitió únicamente su consulta local de versión Windows además de Python/Git;
no se permitieron conexiones. No es un permiso general para comandos de shell.

Se conservan, fuera de Git:

```text
%TEMP%/spica-85g-auditoria-t05v0bnc/guardia/sitecustomize.py
%TEMP%/spica-85g-auditoria-t05v0bnc/nuevas-inicial.log
%TEMP%/spica-85g-auditoria-t05v0bnc/dirigidas-final.log
%TEMP%/spica-85g-auditoria-t05v0bnc/dirigidas-cierre.log
%TEMP%/spica-85g-auditoria-t05v0bnc/nuevas-final.log
%TEMP%/spica-85g-auditoria-t05v0bnc/suite-completa.log
%TEMP%/spica-85g-auditoria-t05v0bnc/suite-completa-final.log
%TEMP%/spica-85g-auditoria-t05v0bnc/piloto-cierre.json
```

El directorio vacío creado por la primera preparación fallida de guardia se
comprobó y retiró con rmdir no recursivo, verificando nombre/padre y ausencia de
contenido; no era RAW ni contenía datos previos. La carpeta de auditoría indicada
conserva deliberadamente registros para revisión, no originales operativos.

Estado final de git status --short:

```text
?? docs/brechas_integracion_paso85g.md
?? docs/contrato_ejecucion_integrada_paso85g.md
?? docs/piloto_integracion_vertical_paso85g.md
?? herramientas/piloto_integracion_85g.py
?? tests/test_integracion_vertical_85g.py
```

Rama feature/suadc-http, HEAD 13744ab e índice sin cambios. Se revisan también
los cinco archivos sin seguimiento directamente: UTF-8, espacios, salto final,
sintaxis en memoria/definiciones Python y enlaces/tablas Markdown. git diff
--check por sí solo no comprueba esos archivos nuevos. No se abren URLs externas.

## 7. Seguridad, temporales y dictamen

El piloto y las verificaciones se ejecutan con una guardia externa que rechaza
conexiones/DNS y E/S a las rutas operativas conocidas, además de procesos no
permitidos. No es un sandbox del SO ni una prueba contra alias/código nativo hostil;
las comprobaciones del arnés y tests son complementarias. MockTransport demuestra
la integración local, **no un handshake HTTPS/TLS ni disponibilidad institucional**.

Los temporales RAW/staging/catálogos del piloto principal e independiente se
eliminaron al cerrar; las referencias a sus rutas son históricas. Solo se conservan
logs de verificación, guardia y métricas sintéticas en el temporal privado de
auditoría fuera de Git, sin copia del CSV institucional ni lotes JSON operativos.

No se accedió a RAW permanente, CSV PNDA, staging/SQLite operativos, documentos
institucionales o manifiestos privados. No se afirma comprobar físicamente esos
originales mantenidos cerrados ni controlar cambios de terceros. No hubo red,
GET externos, descargas, instalaciones, migraciones de almacenes preexistentes,
commits o push. La creación de esquemas vacíos temporales y referencias en memoria
se describe explícitamente en el contrato; no equivale a migrar datos operativos.

Las 29 brechas conservan **2 resueltas, 17 parciales, 8 pendientes y 2 contradicciones**.
Ninguna fuente, metadato o resultado estructural habilita una regla científica.

**Dictamen: APTO CON RESTRICCIONES para el tramo vertical sintético demostrado.**
No es integración completa de SPICA, certificación de producción, validación
científica o autorización de una adquisición. Se espera auditoría antes del 85-H.
