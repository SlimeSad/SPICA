# PASO 84-J — Núcleo experimental de metadatos documentales

Fecha: **2026-11-08**. Contrato **0.1.0**, offline y **no operativo**.
La [auditoría previa de las cinco transiciones](auditoria_transiciones_pnda_paso84j.md)
fue satisfactoria con restricciones. Se conservan R02/R04/R05/V04/V07 y los
29 IDs del 84-I, sin modificar sus documentos ni aplicar estados al catálogo.

## Arquitectura y reutilización

Paquete nuevo y aislado:
[`spica.metadatos_documentales`](../src/spica/metadatos_documentales/__init__.py).
No tiene dependencia de PNDA/SENAMHI, archivos institucionales, transporte,
almacenamiento, importadores o ejecución científica.

Se revisaron los contratos anteriores antes de diseñarlo:

| Contrato existente | Reutilización / límite que motiva el complemento |
|---|---|
| [ReferenciaCientifica](../src/spica/calidad/modelos_cientificos.py) | Identificador, procedencia, título, localizador, versión, fecha y SHA del documento. Se exige SHA en la composición nueva; no se copia su clase ni se cambia su contrato opcional anterior |
| [EvidenciaDocumental de aplicabilidad](../src/spica/calidad/aplicabilidad/modelos.py) | Se conserva el mismo objeto: referencia, localización, naturaleza, nivel, vigencia y pendientes/contradicciones. Sus estados no se redefinen ni se interpretan como permiso |
| AfirmacionAplicabilidad, del mismo módulo | Sigue sirviendo al verificador de reglas/dimensiones. No representa por sí sola IDs de cláusulas, referencias estructuradas generales, relaciones o nulo institucional expreso; no se la reemplaza ni se fuerza ese significado en su campo valor |
| [Respaldo / IdentidadRecurso / PeriodoTemporal](../src/spica/interoperabilidad/modelos.py) | Se componen sin modificación para clasificaciones aportadas por propiedad, identidad objetivo y períodos civiles/temporales ya tipados |
| [ProcedenciaCatalogo / EstadoVerificacion](../src/spica/adquisicion/catalogo/modelos.py) | Se usan a través del Respaldo existente, con su fecha/método/referencia/evidencia. No se abre CatalogoCientifico ni se crea otra persistencia |
| [ReferenciaDOCX](../src/spica/adquisicion/verificacion/docx/modelos.py) | Se acepta el DTO exacto existente. El módulo nuevo comprueba la coherencia estructural del perfil mínimo; no cambia el inspector ni lee XML |

No se encontró un contrato previo que cubriera simultáneamente cláusulas generales,
referencias estructuradas, ausencia frente a nulo, relaciones y restricciones
por uso. El paquete añade esa composición, no un segundo verificador QA/QC,
catálogo operativo o sistema de confianza general.

### Aislamiento de importaciones

Los inicializadores heredados cargan módulos de persistencia al importar algunos
modelos. Para no modificar esos paquetes ni cargar SQLite desde este núcleo,
los imports de contratos existentes están bajo `TYPE_CHECKING`; las anotaciones
son diferidas. En ejecución se comprueba identidad nominal contra las clases
que **ya aportó/cargó el llamador**, consultando `sys.modules` con nombres fijos.
No se importa un módulo indicado por datos, no se carga un plugin ni se ejecuta
una expresión de configuración. Subclases o imitaciones no se admiten.

Una importación fresca de este paquete no carga `sqlite3`, HTTPX, catálogo,
adquisición, calidad o interoperabilidad. Un test usa un intérprete aislado con
esos imports prohibidos para comprobarlo. El cliente que construya instancias
de los contratos heredados conserva sus inicializadores anteriores; este paso
no los transforma en interfaces perezosas ni cambia sus efectos de importación.
La comprobación nominal presupone un entorno Python confiable, no módulos
manipulados por código hostil. La introspección de anotaciones diferidas requiere
que el consumidor aporte el espacio de nombres de esos contratos; no hay un
resolvedor dinámico o deserializador nuevo.

## Modelos e invariantes

Implementación:
[`modelos.py`](../src/spica/metadatos_documentales/modelos.py) y
[`evaluacion.py`](../src/spica/metadatos_documentales/evaluacion.py).
Dataclasses congeladas y colecciones tuple, con tipos exactos y tamaños acotados.
No se normalizan cadenas originales, códigos, unidades o versiones.

| Modelo | Contenido | Invariante principal |
|---|---|---|
| FuenteDocumental | ReferenciaCientifica; tipo XLSX/DOCX/OTRO; identidad objetivo y versión de producto opcionales; respaldos separados de integridad, inspección, autenticidad y correspondencia editorial | SHA sintáctico obligatorio. Tener SHA no acredita ninguna otra propiedad. Correspondencia verificada exige objetivo y ambas versiones conocidas |
| ReferenciaCelda | ID/hash del documento, hoja y celda/rango A1 | Hoja no vacía; coordenadas canónicas y ordenadas dentro de XFD/1048576; sin fórmulas, conversión de valores o resolución de archivos |
| ReferenciaDOCX existente | ID/hash, parte, ruta Clark, párrafo y contexto de tabla/fila/celda | Perfil actual: word/document.xml, párrafos directos o tablas no anidadas del cuerpo; campos consistentes con la ruta. Ordinal global positivo, sin inventarlo desde la ruta local |
| ReferenciaSeccion | ID/hash y sección aportada | Para OTRO; no supone un inspector de PDF u otro formato ni calcula páginas |
| AfirmacionDocumental | ID estable, fuente, referencia estructural, EvidenciaDocumental, concepto, ámbito, presencia, contenido, forma literal/paráfrasis, unidad, vigencia, restricciones y constataciones | Fuente/hash/tipo/localización deben coincidir. No se aceptan afirmaciones sin procedencia o referencias. Contenido oculto del repr; no hay logging automático |
| ConstatacionAspecto | Aspecto explícito, descripción y Respaldo existente opcional | Clasificación aportada por aspecto, no inferida desde texto. Unidad acreditada requiere unidad declarada; aplicabilidad acreditada requiere objetivo |
| RelacionAfirmaciones | Dos IDs distintos, tipo y justificación | Coincidencia, complementariedad, contradicción, diferencia de ámbito o correspondencia no demostrada; no fusiona afirmaciones ni promueve corroboración |
| ExpedienteMetadatos | Fuentes, afirmaciones y relaciones inmutables | IDs únicos, fuentes idénticas a las registradas, extremos existentes, un vínculo por par; no mezcla fixtures sintéticos con evidencia documental |
| DiagnosticoUso | Código, IDs, referencias y carácter bloqueante | Traza por fuente, SHA y localizador; no publica el contenido literal |
| ResultadoUso | Expediente, operación propuesta, selección y diagnósticos deterministas | Recalcula coherencia de trazas; no admite resultado vacío. ejecucion_autorizada y operacion_ejecutada siempre False, no configurables |

Las referencias se validan **sintáctica e internamente**, no contra un archivo.
No se comprueba aquí existencia de hoja/párrafo, contenido citado, hash físico,
autoría o veracidad de los respaldos. El ordinal global DOCX no puede verificarse
desde una ruta local sin el árbol completo. La inspección autorizada y sus
referencias reales siguen siendo un paso externo previo.
Encabezados/pies, notas y tablas DOCX anidadas están fuera de este perfil mínimo;
se rechazan, sin rediseñar o ampliar el inspector existente.

Unidades o versiones desconocidas permanecen `None`; no se asigna un código
de producto/recurso para satisfacer la estructura. `producto` representa la
IdentidadRecurso objetivo existente; si no puede identificarse, se conserva None.
Un ID distinto con el mismo hash no se deduplica ni cuenta automáticamente como
evidencia independiente.

## Ausencia, nulo y representación

`PresenciaInformacion` es obligatoria, separada del contenido:

| Presencia | Contenido requerido | Semántica |
|---|---|---|
| CON_VALOR | Texto literal o paráfrasis controlada no vacía | La cadena se conserva sin convertirla. El literal NULL no se interpreta automáticamente como nulo |
| AUSENTE | None, nivel de evidencia DESCONOCIDA y pendientes no vacíos | No localizado en el ámbito inspeccionado; no afirma inexistencia institucional |
| NULO_DECLARADO | Marcador/declaración textual preservado, nivel DECLARADA o VERIFICADA | La institución declara expresamente un nulo; no se permite deducirlo por inferencia |

La propiedad `valor` devuelve None para ausencia y nulo; **no debe consumirse
sin presencia/contenido**, que conservan la diferencia. Un nulo declarado puede
consultarse documentalmente, pero no se transforma en valor científico.
No se admite contradicción por mera ausencia frente a un valor, ni entre dos
marcadores de nulo expreso. Tampoco coincidencia positiva por dos ausencias.

`FormaDeclaracion` distingue literal de paráfrasis controlada; no verifica por
algoritmo la fidelidad de la paráfrasis. `NivelEvidencia`, `NaturalezaEvidencia`
y `VigenciaDocumento` siguen perteneciendo al contrato anterior, sin equivalencia
con un resultado meteorológico. Los None de campos opcionales describen
información no aportada; un nulo institucional se registra como afirmación
expresa, no convirtiendo todos los None en declaraciones del emisor.

## Dimensiones independientes

La fuente contiene cuatro respaldos independientes: integridad física aportada,
inspección estructural aportada, identidad/autenticidad y correspondencia editorial.
La afirmación conserva su extracción/evidencia y puede aportar constataciones de:
aplicabilidad al producto, corroboración independiente, convención temporal,
identidad espacial, referencia espacial, significado de variable, unidad,
validación científica y derechos para el uso.

Cada respaldo tiene clasificación/procedencia propias. No se deriva un aspecto
de otro, ni se crea un indicador «confiable». Leer «validado» no crea una
constatación de validación; mencionar una licencia no crea una de derechos.
Repetir el mismo texto o una declaración institucional tampoco crea corroboración.
Las procedencias de respaldo son **aportadas por el llamador**, no autenticadas
por este núcleo. Las garantías se limitan a coherencia de contratos y bloqueos.

## Evaluación y bloqueos

`evaluar_uso(expediente, operacion, seleccion)` es pura. Requiere selección tuple
no vacía, sin duplicados y con IDs existentes. Ordena la selección y diagnósticos,
incluye ID/hash/localizador y devuelve una instantánea. No ejecuta la operación.
Incluso un diagnóstico sin bloqueos mantiene **ejecucion_autorizada=False** y
**operacion_ejecutada=False**. `bool(resultado)` produce TypeError para evitar
tratarlo accidentalmente como permiso.

| Operación propuesta | Requisitos documentales comprobados sobre metadatos aportados |
|---|---|
| CONSULTA_DOCUMENTAL | Integridad e inspección clasificadas VERIFICADO; información presente o nulo expreso, sin conflicto bloqueante. Inferencias, vigencia desconocida y restricciones se señalan sin otorgar aptitud científica |
| CONVERSION_TEMPORAL | Base no consultiva y constataciones acreditadas de convención temporal y validación científica |
| ASIGNACION_ESPACIAL | Base no consultiva e identidad espacial, referencia espacial y validación científica acreditadas |
| INTERPRETACION_VARIABLE | Base no consultiva, significado, unidad aplicable y validación científica acreditados; unidad declarada presente |
| EQUIVALENCIA_EDITORIAL | Base no consultiva; al menos dos documentos distintos, mismo objetivo/versión de producto y comparación explícita coincidente para cada par seleccionado |
| ACREDITACION_CALIDAD | Base no consultiva y constatación acreditada de validación científica; palabra o nivel de evidencia documental insuficientes |
| REDISTRIBUCION | Integridad/inspección, identidad institucional y correspondencia/versiones acreditadas, vigencia clasificada vigente, aplicabilidad y derechos acreditados; no exige validación científica como sustituto de autorización jurídica |

**Base no consultiva**: condiciones técnicas de consulta, valor no nulo,
vigencia clasificada vigente, autenticidad y correspondencia editorial
VERIFICADO, versiones conocidas y constataciones de aplicabilidad/corroboración
VERIFICADO. Redistribución usa aplicabilidad/derechos, sin exigir corroboración
científica. La consulta de un nulo no satisface la condición de valor no nulo.

En cualquier uso no consultivo, una restricción explícita activa bloquea la
evaluación aunque existan respaldos positivos. Restricciones tipadas: identidad
institucional no comprobada, edición no comprobada, unidad ambigua, convención
temporal desconocida, identidad espacial desconocida, derecho no comprobado y
procesamiento no validado. Es una política conservadora por afirmación; no intenta
inferir automáticamente que una restricción sea irrelevante para cierto uso.

Conflictos declarados de evidencia o entre afirmaciones bloquean. Un conflicto
incidente no desaparece seleccionando solo uno de sus extremos: el diagnóstico
incluye ambos y sus referencias. Correspondencia no demostrada bloquea usos
no consultivos. Complementariedad no fusiona hechos, unidades, versiones o fuentes.
Para declarar contradicción se requieren conceptos/ámbitos coincidentes y
declaraciones distintas, no ausencia o dos nulos. La justificación semántica sigue
siendo responsabilidad del revisor; el validador no interpreta lenguaje natural.

Entre los códigos: `integridad_no_acreditada`, `inspeccion_no_acreditada`,
`informacion_ausente`, `nulo_declarado_no_es_valor_cientifico`,
`vigencia_no_acreditada`, `edicion_o_correspondencia_no_acreditada`,
`falta.convencion_temporal`, `falta.identidad_espacial`, `falta.referencia_espacial`,
`falta.significado_variable`, `falta.unidad_aplicable`, `falta.validacion_cientifica`,
`falta.derechos_para_el_uso` y `contradiccion_entre_afirmaciones`.
Siempre se incluyen las limitaciones de núcleo experimental y clasificaciones
aportadas no autenticadas. No se emiten contenidos ni se abren localizadores.

No se calcula vigencia respecto de un reloj o fecha de observación: el período
se conserva y la clasificación se exige como dato de evidencia aportado. Una
futura selección por época necesita diseño/revisión propios. No se interpreta
HORA, convierte PP, resuelve CRS, asigna coordenadas o valida observaciones.

## Pruebas y verificaciones

[test_metadatos_documentales.py](../tests/test_metadatos_documentales.py) contiene
**31 pruebas nuevas**, sin documentos reales. Sus fixtures son sintéticos,
con referencias/respaldos declarados como tales, sin fingir hash físico o QC real.
Cubre fuente/SHA/procedencia, referencias ausentes/incompatibles, hoja/celda y
contexto DOCX, inmutabilidad, IDs/relaciones, ausencia/nulo/literal NULL, niveles y
vigencia, complementariedad/contradicción, ediciones desconocidas, unidad,
tiempo/espacio/derechos, calidad documental frente a científica, restricciones,
equivalencia editorial positiva/negativa, trazas y determinismo.

La importación fresca se prueba en un Python aislado con SQLite, HTTPX y módulos
operativos prohibidos. Los modelos y evaluación se ensayan con apertura de
archivos, red, SQLite y subprocesos bloqueados. El subproceso del test de
importación es únicamente Python con su propia guardia, nunca una operación
productiva. No se crean tests vacíos ni se copian archivos institucionales.

Primer ensayo: 31 ejecutadas, una aprobada y 30 errores por un **único fallo del
fixture compartido**, que invocaba Fuente con un argumento en vez de proveedor e
identificador. Se corrigió el fixture usando la firma real, sin cambiar el contrato
anterior. Esa corrida no se declara aprobada. Los resultados finales se indican
en el cierre; los subcasos y repeticiones no aumentan el total de pruebas nuevas.

Ensayo dirigido final previo a la suite completa, con Python **3.15.1** de `.venv`:

```powershell
$env:PYTHONPATH="$PWD\src;$PWD\tests;$PWD"
.\.venv\Scripts\python.exe -B -m unittest test_metadatos_documentales test_aplicabilidad_cientifica test_interoperabilidad_modelos test_interoperabilidad_evaluador test_adaptadores_interoperabilidad -v
```

**170 aprobadas, 0 fallos y 0 errores, 2.043 s**: 31 nuevas y 139 anteriores.
Son un subconjunto de la suite completa, no se suman otra vez al acumulado.

## Límites y condiciones de integración futura

No hay serializador/deserializador, persistencia, registro automático de los
29 estados, importador institucional, evaluador de observaciones o interfaz.
Las cadenas nunca se ejecutan ni se importan como código. Una futura exportación
requiere un contrato y revisión de privacidad propios: no volcar asdict/repr
íntegros de objetos aportados, que pueden contener información sensible.

Cotas actuales: 64 fuentes, 256 afirmaciones, 512 relaciones; 64 restricciones
por tuple sin repetición (el enum actual tiene siete), 16 constataciones únicas,
8192 diagnósticos, textos generalmente hasta 4096 caracteres e IDs hasta 128.
No se promete una cuota de RSS ni aislamiento frente a código Python hostil.
La validación nominal depende de nombres públicos de clases/módulos anteriores;
una reorganización futura requiere pruebas de compatibilidad, no importación
automática de otra implementación.

Antes de integrar: auditar este contrato, política de usos y perfiles de referencia;
comprobar físicamente/documentalmente cada evidencia real con sus procedimientos;
acreditar autenticidad, ediciones, aplicabilidad por recurso/período, corroboración,
controles científicos y derechos por separado; diseñar cualquier adaptador y
persistencia con autorización y revisión propias. No se activan módulos científicos
por la presencia de un objeto o un diagnóstico sin bloqueos.

## Cierre

Se ejecutó con Python **3.15.1** de `.venv`:

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -B -m pip check
git diff --check
git status --short
```

**Suite completa actual: 1568 aprobadas, 0 fallidas, 0 errores y 0 omitidas,
164.158 s, código 0.** Total: **1537 anteriores + 31 nuevas**. Las 170 dirigidas
son un subconjunto y no se suman otra vez. No se modificaron tests anteriores;
la suite no encontró regresiones en los contratos/evaluadores previos.
`pip check`: **No broken requirements found.**, código 0; sin instalaciones.
Se usaron `PIP_NO_INDEX=1` y `PIP_DISABLE_PIP_VERSION_CHECK=1`.

La suite tuvo PYTHONPATH temporal con guardia de red y ubicaciones operativas,
permitiendo solo procesos Python/Git para pruebas. Se usó el contexto normal del
propietario por los temporales privados Windows de la suite anterior, sin cambiar
ACL de datos previos. `pip check` mantuvo guardia de red/rutas, permitiendo su
consulta local de versión Windows. Contadores finales de ambas comprobaciones:
**0 red, 0 rutas operativas, 0 SQLite operativos, 0 procesos no admitidos**.
La suite anterior usa SQLite de fixtures/memoria; eso no es SQLite operativo.

Registro verbose y guardia, sin documento institucional, fuera de Git:

```text
%TEMP%\spica-84j-verificacion-8e9ecb3e91ec42e59e07830a42ae9f79\suite-completa.log
%TEMP%\spica-84j-verificacion-8e9ecb3e91ec42e59e07830a42ae9f79\guardia\sitecustomize.py
```

Verificación adicional: cuatro archivos Python nuevos con sintaxis/compilación
en memoria, definiciones sin duplicados y exportaciones coherentes; dos informes,
**seis tablas y 17 enlaces locales** correctos; UTF-8, bloques y finales sin
incidencias. La matriz 84-I conserva **29 IDs únicos y balance 2/17/8/2/0**.
`git diff --check`, diff registrado y diff del índice: código 0, sin salida.
Los archivos sin seguimiento se revisaron directamente.

Git inicial/final: rama **feature/suadc-http**, HEAD
**ef17ad41b68815b6c9edb7a924ec6bade59e74b6**, sin commits o push. Se crean
exclusivamente seis archivos:

```text
docs/auditoria_transiciones_pnda_paso84j.md
docs/contratos_metadatos_documentales_paso84j.md
src/spica/metadatos_documentales/__init__.py
src/spica/metadatos_documentales/modelos.py
src/spica/metadatos_documentales/evaluacion.py
tests/test_metadatos_documentales.py
```

`git status --short` agrupa el paquete nuevo como directorio:

```text
?? docs/auditoria_transiciones_pnda_paso84j.md
?? docs/contratos_metadatos_documentales_paso84j.md
?? src/spica/metadatos_documentales/
?? tests/test_metadatos_documentales.py
```

No se modificaron módulos, contratos, inspectores, evaluadores, adaptadores,
dependencias, configuraciones, informes o matrices anteriores. No se escribieron
evidencias primarias, RAW, staging o SQLite operativos, ni se accedió al CSV.
Cero conexiones, GET, descargas, migraciones y activaciones científicas.
La conservación física actual del DOCX está registrada en la auditoría; no se
presentan huellas nuevas del XLSX o de almacenes que no se abrieron.

**APTO CON RESTRICCIONES** para revisar el prototipo aislado y la auditoría;
sin integración operativa ni autorización de otra etapa. Permanecen pendientes
ediciones/aplicabilidad, corroboración independiente, validación científica y
derechos reales. Se espera auditoría humana antes de continuar.
