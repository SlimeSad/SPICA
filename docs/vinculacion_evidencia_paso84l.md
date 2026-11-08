# PASO 84-L — Vinculación experimental de evidencia documental

Fecha: **2026-11-08**. Dictamen: **APTO CON RESTRICCIONES** para ensayos offline
dirigidos por un responsable confiable. Sin integración operativa, autenticación
institucional, certificación científica o habilitación de ejecutores.
El [piloto de cinco afirmaciones](piloto_cotejo_documental_paso84l.md) documenta
la comprobación real; los casos adversariales usan exclusivamente fixtures.

## Recuperación y auditoría de capacidades

Git comenzó limpio en **feature/suadc-http**, HEAD **f6c2a36**, «SUADC:
auditoria de procedencia y piloto documental PNDA». El commit consolida 84-K:
dos informes, corrección de contradicciones y seis tests. Historial consultado:

```text
f6c2a36 SUADC: auditoria de procedencia y piloto documental PNDA
1c06125 SUADC: contratos experimentales de metadatos documentales
ef17ad4 SUADC: reconciliacion documental de metadatos PNDA
b3c2748 SUADC: compatibilidad OOXML y extraccion documental PNDA
ca08d73 SUADC: inspeccion segura de hipervinculos OOXML
```

Se revisaron [reconciliación 84-I](reconciliacion_xlsx_docx_pnda_paso84i.md),
[evidencias](evidencias_consultas_pnda_paso84i.md),
[matriz](brechas_reconciliadas_pnda_paso84i.md),
[transiciones 84-J](auditoria_transiciones_pnda_paso84j.md),
[contratos 84-J](contratos_metadatos_documentales_paso84j.md),
[auditoría 84-K](auditoria_procedencia_metadatos_paso84k.md) y
[piloto 84-K](piloto_afirmaciones_pnda_paso84k.md), además del código y los tests.
No se sobrescribió ninguno. El bloqueo de contradicciones explícitas continúa
en el evaluador anterior, sin modificación.

| Capacidad existente | Reutilización y alcance auditado |
|---|---|
| ReferenciaCientifica y ProcedenciaCatalogo | Identifican el control documental previo y su antecedente; no se inventa otra estructura de procedencia institucional |
| FuenteDocumental, AfirmacionDocumental, ExpedienteMetadatos | Conservan fuente, hash declarado, referencia, literal/forma, ámbito, evidencia, restricciones y relaciones; no resuelven referencias contra archivos |
| localizar y validaciones del núcleo | Coherencia sintáctica, tipos, identidad, SHA y traza; localizar no abre ni encuentra un fragmento |
| docx.inspector._ruta_autorizada | Ruta absoluta contenida, archivo regular, rechazo de symlinks/reparse points, componentes inseguros y escapes |
| docx.inspector._control / _leer | Lectura acotada, SHA físico, firma previa/descriptor/posterior y cierre del descriptor. Se conserva el snapshot exacto de esa lectura |
| herramientas/inspeccionar_xlsx_84e.inspeccionar_bytes | ZIP/XML, hoja/celdas y literales sin fórmulas ejecutadas o formatos aplicados; límites y omisiones existentes |
| inspeccionar_docx_bytes, 0.2.1 | ZIP/XML y párrafos con referencias canónicas, estados completos/incompletos/rechazados, diagnósticos y destinos omitidos |
| evaluar_uso | Política documental anterior y bloqueo permanente de ejecución; no se cambia ni se alimenta automáticamente con nuevos respaldos |

No se encontró un resolvedor común que vinculara el resultado de una lectura
física con una afirmación. El arnés 84-K hacía cotejos puntuales. La capacidad
faltante se limita a orquestar lectura/inspección existentes y buscar en sus
inventarios. No requiere reescribir inspectores o modificar módulos estables.

## Arquitectura mínima implementada

Nuevo componente experimental de checkout:
[herramientas/vinculacion_documental.py](../herramientas/vinculacion_documental.py),
versión **0.1.0**. No se añade un import al núcleo ni una CLI automática.
Requiere src y la raíz del repositorio en la ruta de importación; no se presenta
como una biblioteca instalada autónoma. El import de herramientas/inspectores
carga sus dependencias heredadas, incluso módulos con contratos SQLite; no
abre una conexión ni autoriza persistencia. El núcleo conserva su import puro.

| Elemento | Responsabilidad |
|---|---|
| ControlArchivo | Configuración de un archivo exacto: ID de control, ruta/raíz, tipo, ReferenciaCientifica con SHA esperado, tamaño y ProcedenciaCatalogo del control previo |
| CotejadorDocumental | Recibe al construirse una tuple de controles, con IDs de control/documento únicos. No acepta un conjunto vacío |
| cotejar(control_id, expediente, seleccion) | Recibe solo el ID registrado, un expediente existente y sus IDs de afirmación; no recibe rutas, hashes, inventarios, callbacks, verificado=True o permisos desde la afirmación |
| CotejoAfirmacion | Conserva la misma AfirmacionDocumental, referencia encontrada, estado de comparación, literal observado y códigos. No muta ni promueve su fuente o evidencia |
| ResultadoVinculacion | Registra control, tamaños/hash, estado por fase, inspector/versión, conservación, firmas, cotejos, diagnósticos y limitaciones. Sin indicador global de documento confiable |
| diagnostico_publico | Proyección determinista sin literales, rutas locales, firmas de archivo, textos de procedencia o mensajes de excepción; no es certificado o formato admitido de importación |

Las banderas de ejecución son init=False y permanecen **False**. bool(resultado)
se rechaza para evitar su uso accidental como permiso. Los resultados son
registros de la ejecución de la función, no objetos que se acepten de vuelta
para acreditar verificaciones. Construir o alterar manualmente un DTO no
constituye una comprobación del componente.

### Flujo de las cuatro fases

1. **A — Física:** valida identidad de fuente contra el control registrado antes
   de abrir; valida ruta; lee en rb con _leer, hasta 1 MiB y bloques de 65536
   bytes. Calcula tamaño/SHA de los bytes leídos y los compara con el control.
   Una discrepancia impide inspeccionar y cotejar. No decide formato por extensión.
2. **B — Estructura:** entrega el mismo bytes snapshot a la API XLSX o DOCX.
   No vuelve a abrir el archivo para interpretar otro contenido. DOCX exige
   DOCUMENTO_VALIDADO_EN_ALCANCE y coteja ID/tamaño/hash del snapshot que el
   inspector devuelve. XLSX exige retorno satisfactorio del diagnóstico existente.
   Se conservan códigos de omisiones/rechazos y límites del perfil.
3. **C — Documento:** resuelve una celda XLSX o un párrafo DOCX en el inventario,
   con coincidencia única. DOCX exige igualdad de la referencia completa, incluido
   ordinal global y contexto. Compara cadenas exactamente, sin strip, cambios
   Unicode, unidades, símbolos, zonas o interpretación semántica.
4. **D — Traza:** ordena selección/códigos, conserva la afirmación original y sus
   restricciones. En finally repite validación de ruta, lectura y SHA; compara
   dispositivo/inode/tamaño/mtime y bytes. Si falla o no concluye, invalida el
   cotejo, retira literales/estados positivos y conserva la información de que
   la referencia sí se había encontrado cuando corresponde.

No hay un resultado positivo de cotejo apoyado solamente en un campo declarativo
de la fuente. Los respaldos integridad/inspeccion aportados al núcleo se ignoran
como sustitutos de A/B: siempre se ejecuta la lectura real cuando el control
y la identidad lo permiten. No se copia el resultado a esos respaldos.
COINCIDE solo acredita igualdad del contenido literal localizado: no acredita
que las etiquetas de concepto, ámbito, unidad declarada o aplicabilidad
aportadas por el llamador sean semánticamente correctas. Esos campos se
conservan, sin inferir sus constataciones científicas desde la coincidencia.

## Modelo de confianza: categorías que no se equiparan

| Categoría | Tratamiento |
|---|---|
| A. SHA declarado | Metadato de FuenteDocumental; debe identificar la misma fuente que el control, pero no basta para aprobar nada |
| B. SHA calculado | Devuelto por _leer sobre el archivo abierto; None si la lectura no concluyó. Nunca se obtiene del nombre |
| C. SHA esperado previo | Viene del registro de controles establecido por el responsable antes de recibir afirmaciones. Se conserva su ReferenciaCientifica y ProcedenciaCatalogo |
| D. Estructura | Resultado del inspector existente aplicado al snapshot físico, con versión y perfil limitados |
| E. Referencia | Encuentro único de hoja/celda o parte/ruta/párrafo/contexto; una referencia sintáctica puede no existir |
| F. Contenido | COINCIDE, DIFIERE o NO_COTEJABLE; solo se automatiza igualdad literal de una afirmación CON_VALOR y LITERAL |
| G. Procedencia declarada | Conservada en la fuente y en el antecedente de control, sin promoverla |
| H. Autenticidad institucional | No evaluada/acreditada por esta herramienta; el hash local no identifica al autor |
| I. Validación científica | No realizada; coincidir con el original no prueba ciencia, aplicabilidad, derechos o correspondencia editorial |

**La aprobación del control es una responsabilidad externa.** Exigir un registro
con referencia, SHA y antecedente de evidencia evita un modo de operación sin
control, pero no verifica que un texto libre de procedencia sea una aprobación
legítima. Un administrador que fabricara el registro desde el mismo archivo
o copiara el hash de una afirmación estaría incumpliendo el modelo de confianza;
el componente no puede descubrir por criptografía la historia de ese dato.
No tiene una interfaz que genere controles aprobados desde afirmaciones o
apruebe automáticamente un hash recién calculado. En el piloto, los dos valores
esperados proceden de la sección 5 de la solicitud 84-L, previamente establecidos.

No hay firmas digitales, certificados, secretos compartidos, autenticación de
emisores, carga arbitraria de expresiones o plugins. Un llamador que controle
el intérprete puede alterar dataclasses, diccionarios, clases o funciones. frozen
es protección cooperativa, no aislamiento. También se necesita revisión de
privacidad de IDs/localizadores antes de publicar datos aportados por terceros.

## Estados y fallos

Cada fase usa **NO_REALIZADA, SATISFECHA, FALLIDA o INCOMPLETA**. Son estados
de comprobación técnica, no reglas científicas. EstadoCotejo es independiente.

| Situación | Resultado y actuación |
|---|---|
| Configuración/selección inválida | TypeError/ValueError con código fijo antes de abrir: sin controles, duplicados, hash ausente, tamaño fuera del perfil, ruta fuera de raíz, selección ajena o repetida |
| Fuente no coincide con control | identidad_de_afirmacion_no_corresponde_al_control; no se abre el archivo ni se acepta un hash de sustitución |
| Ruta/archivo no disponible o inseguro | Ruta fallida y fases posteriores no realizadas; mensajes de SO y rutas no se reflejan |
| Lectura interrumpida, excesiva o no concluida | Comparación incompleta y hash None; no se declara hash físico de una lectura parcial |
| Tamaño/SHA distinto del control | Comparación fallida; estructura y cotejo no realizados. La conservación del archivo observado se informa aparte |
| DOCX incompleto/rechazado | Estructura INCOMPLETA/FALLIDA respectivamente; no se usa el texto parcial o la caché como cotejo positivo |
| Error del diagnóstico XLSX | Estructura INCOMPLETA y sin cotejo. Su API de excepción no separa todas las causas de rechazo y límite; no se inventa una clasificación más precisa ni se afirma corrupción |
| Referencia inexistente/ambigua o contexto incorrecto | Referencia fallida; no cotejable. No se elige una aparición por aproximación |
| Celda con fórmula o sin literal | La celda puede existir, pero no hay literal cotejable; no se usa el caché ni se infiere un nulo |
| Rango, paráfrasis, ausencia o nulo declarado | No se certifican automáticamente; se conserva el contenido observado cuando existe y se exige revisión humana |
| Literal distinto | Referencia encontrada, DIFIERE; no se modifica ni normaliza ninguno de los textos |
| Contradicción explícita o relación contradictoria incidente | Se conserva el aviso aun si la cita coincide. La coincidencia no resuelve el conflicto; el evaluador anterior sigue bloqueándolo |
| Dos afirmaciones sobre el mismo fragmento | Se conservan ambas identidades y resultados; aviso de referencia compartida, sin convertirlo en corroboración independiente |
| Conservación final fallida/incompleta | Cotejo invalidado, NO_COTEJABLE, sin literal positivo; no se borra que se había encontrado una referencia. Si nunca se llegó a C, figura no realizada |
| KeyboardInterrupt | Se cierran descriptores y se intenta la comprobación final si había lectura inicial completa; se propaga la interrupción, sin inventar un resultado completado |

No se reintenta, sustituye, repara o borra un archivo para resolver fallos.
No se escriben temporales desde el componente. Un error ajeno al perfil se
devuelve como comprobacion_no_completada, sin cuerpos, rutas o notas de excepción.

## Riesgos y límites auditados

| Riesgo / gravedad | Mitigación y límite residual |
|---|---|
| Control fabricado por quien configura la política — Media | Llamador confiable y antecedente previo obligatorio; no se afirma aprobación criptográfica. Sin ese responsable, no usar el componente como verificador de confianza |
| TOCTOU / sustitución concurrente — Media | Validación de cada componente, lstat/descriptor, snapshot único acotado, hash previo/posterior y firma final; pruebas de sustitución y cambio. No son apertura atómica de toda la jerarquía o defensa absoluta contra propietario malicioso |
| Intérprete comprometido — Media | Datos/clases congelados no son frontera de seguridad. No hay ejecutor ni integración, y todas las banderas admitidas son False |
| Identidad/editorial/ciencia/derechos no acreditados — Media | Restricciones originales intactas; ni licencia nombrada ni validado conceden permisos |
| Dependencias privadas y de checkout — Baja | _leer/_control/_ruta_autorizada y el diagnóstico XLSX se fijan por esta revisión y tests. Reorganizar esos módulos exige revisión; no se publican como API estable |
| Cobertura parcial OOXML — Baja | Se mantienen perfiles y omisiones existentes. Una celda individual y párrafos del cuerpo/tablas no anidadas del núcleo; no rangos, renderizado, notas o resolución semántica |
| Recursos y sistema de archivos — Baja | Snapshot máximo 1 MiB; límites ZIP/XML/texto anteriores y plazos cooperativos de cinco segundos, no cuota RSS ni interrupción de llamadas C/FS bloqueadas. No hay descarga grande o soporte genérico de formatos |
| Volúmenes Windows — Baja | Se rechazan rutas UNC/dispositivos y se exige letra de unidad. Eso no demuestra que una unidad mapeada sea local; el responsable debe establecer un volumen local controlado. El piloto usa exclusivamente los C: autorizados |

No se halló necesidad de modificar contratos públicos o módulos operativos.
No se añade integración al catálogo, respaldo persistente, serializador seguro,
revisión semántica de paráfrasis, selección editorial por fecha o certificación.
Esas capacidades requieren diseño y autorización propios.

## Pruebas y verificación

[test_vinculacion_documental.py](../tests/test_vinculacion_documental.py) añade
**32 pruebas**, reutilizando constructores de fixtures DOCX/XLSX y del núcleo.
No contiene originales institucionales ni sus hashes/valores como fixtures.
Cubre los 20 grupos de riesgo solicitados: integridad, alteración, controles,
existencia/rutas, reparse simulado, sustitución, referencias, identidad, texto,
inspecciones parciales/rechazadas, contradicciones, duplicaciones, omisiones,
límites, autorización, privacidad, lectura sin red/SQLite/procesos, conservación
y cierre bajo interrupción. La prueba de reparse es simulada; no se presenta
como creación y ataque de una junction Windows real.

Comandos, con Python **3.15.1 de .venv**, HTTPX **0.28.1**:

```powershell
$env:PYTHONPATH="$PWD\src;$PWD\tests;$PWD"
.\.venv\Scripts\python.exe -B -m unittest test_vinculacion_documental test_metadatos_documentales -v
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -B -m pip check
git diff --check
git status --short
```

Dirigidas finales: **69 aprobadas, 0 fallos y 0 errores, 1.533 s**: 32 nuevas y
37 anteriores. El primer ensayo con 30 nuevas aprobó 67; luego se cubrieron dos
fallos adicionales. La primera suite completa aprobó **1606**, sin fallos/errores,
en **157.913 s**. Tras precisar el diagnóstico de cotejo invalidado se repite
la suite: **1606 aprobadas, 0 fallos, 0 errores y 0 omitidas, 156.517 s,
código 0, salida OK**. Total real **1574 anteriores + 32 nuevas**. Las
dirigidas, repeticiones y subcasos no se suman de nuevo. La cifra histórica
1574 no se presenta como ejecución actual separada.
`pip check`: **No broken requirements found.**, código 0, sin instalaciones.

La suite usa temporalmente una guardia antes de src/tests/raíz en PYTHONPATH,
bloqueando red/DNS, datos operativos y procesos ajenos a Python/Git. Se necesita
el contexto normal del propietario para los temporales privados Windows de los
tests anteriores; no se cambian sus ACL. pip usa PIP_NO_INDEX=1,
PIP_DISABLE_PIP_VERSION_CHECK=1 y permite su consulta local de versión Windows,
manteniendo la guardia de red/rutas. Los contadores observados terminan en cero.
SQLite de fixtures/memoria es distinto del operativo, que permanece cerrado.

Registros locales fuera de Git:

```text
%TEMP%\spica-84l-j0m0xk7b\dirigidas-finales.log
%TEMP%\spica-84l-j0m0xk7b\suite-final.log
%TEMP%\spica-84l-j0m0xk7b\guardia\sitecustomize.py
%TEMP%\spica-84l-j0m0xk7b\piloto-final.py
%TEMP%\spica-84l-j0m0xk7b\piloto-final.json
```

La revisión de código identificada por este piloto tiene SHA-256:
`8b58a7bbcab7580ea907657920dd0bcf00fe089eaba3821d3885b5c0e319625c`.
Es una huella de estos bytes del componente, no firma o certificado del resultado.

## Alcance final y dictamen

Se crean exclusivamente cuatro archivos, sin modificar archivos registrados:

```text
?? docs/vinculacion_evidencia_paso84l.md
?? docs/piloto_cotejo_documental_paso84l.md
?? herramientas/vinculacion_documental.py
?? tests/test_vinculacion_documental.py
```

Rama/HEAD e índice se conservan. No se modifican núcleo, transporte, planificador,
adaptadores PNDA, evaluadores, inspectores, dependencias, main.py o .gitignore.
Los archivos nuevos se revisan directamente además de git diff --check.
Verificación documental: **dos informes, nueve tablas y 12 enlaces locales
correctos**; UTF-8, bloques y finales sin incidencias; ambos Python compilan
en memoria, sin definiciones duplicadas. Cotejo de referencias y cantidades
con el resumen saneado; balance de las 29 brechas comprobado. Diff de archivos
registrados y del índice vacío; git diff --check sin errores.

Balance intacto: **29 brechas: 2 resueltas documentalmente, 17 parciales,
8 pendientes, 2 contradicciones, 0 no evaluables; 27 abiertas**.
Cero conexiones, GET, descargas, enlaces abiertos, Word/Excel, instalaciones,
migraciones, commits o push. No se accede al CSV, RAW, staging o SQLite
operativos ni se escriben evidencias/manifiestos previos. No se atribuyen
huellas nuevas a esos almacenes que no se abrieron.

**APTO CON RESTRICCIONES** para auditar este mecanismo y su piloto. Ningún
resultado autoriza HORA/zonas, UBIGEO, coordenadas, conversión PP, redistribución,
equivalencia editorial, QA/QC, procesamiento del CSV o una etapa posterior.
