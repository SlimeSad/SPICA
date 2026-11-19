# RC8 — Auditoría de cierre técnico de un productor no QA

Fecha de elaboración: 2026-11-19, America/Lima. Rama feature/suadc-http.
Inicio limpio; HEAD c1b224ed58e7227d7bd057ed8f54684a6b84509b. RC7 registrado.
Se comprobaron git status, log -5, rama y HEAD antes de cambiar archivos.

## Compatibilidad previa a la implementación

Se revisaron los tres documentos RC7, auditorías RC3–RC6, hoja 85-M, contextos
RC1, inspectores RC3/RC4/RC7, contratos RC5/RC6 y matrices originales 85-F/85-M.
RC7 recomienda seleccionar un productor no QA concreto y definir su evidencia
pertinente antes de ampliar la admisión de dependencias. El encargo actual coincide;
no autoriza cambiar esa admisión, formatos persistentes o iniciar ciencia.

| Candidato existente | Contratos, entrada/salida, pruebas y riesgos | Decisión |
|---|---|---|
| calidad.exportacion.exportar_resultado_json | ResultadoQA + ContextoExportacionQA → str JSON QA 0.1.0. Exportador determinista, acotado, offline, con consumidor nativo y pruebas 85-C/D; no evalúa reglas. Requiere distinguir la operación exportadora del QA que produjo su entrada | Seleccionado: un único productor técnico no QA |
| interoperabilidad.adaptadores.adaptar_meteorologia | Catálogo y ObservacionLocal → ResultadoAdaptacion/RecursoInteroperable; contratos/pruebas de interoperabilidad existentes, sin E/S. No produce archivo ni tiene perfil de conservación de su informe; más correspondencias documentales y de observación | Adecuado como adaptación, menos directo para este piloto de salida comprobable |
| artefactos.materializacion, materializar_sintetico | Bloques explícitos → archivo e InformeMaterializacion. RC5 ya verifica bytes, identidad y publicación, con pruebas propias | Reutilizable para la salida, pero seleccionarlo como transformación confundiría copiar bytes con ejecutar su productor |

La entrada del exportador será un resultado QA nativo realmente obtenido sobre
una fixture, vinculado por RC1. El productor RC8 es solo el exportador: no QA0,
ni una transformación científica nueva. Su salida conserva el JSON existente.
La entrada lógica de exportación identifica ese ResultadoQA aportado; no se
presenta al CSV de origen como el objeto que recibió la función exportadora.

Se necesita una captura específica en memoria y su cotejo, no un nuevo inspector
de operaciones. Se reutilizarán RC1/RC3/RC4, consumo/exportación nativos y cotas
existentes. RC1 permite DESCRIPCION_ESTRUCTURAL; no se añadirá otro TipoOperacion.
La invocación será explícita, únicamente del exportador fijo, sin callbacks,
despacho de componentes o ejecución desde los inspectores RC3/RC7.

RC3 solo admite determinados cierres QA. El cierre técnico RC8 no satisfará una
dependencia RC3/RC7; se conservará como evidencia aparte y se probará el pendiente.
RC6 conserva descripción y bytes, no esta captura ni su cierre. No se cambiarán
APIs previas, SQLite 85001, codecs 85-J/K, RC6 o JSON QA 0.1.0.

La captura local distingue invocación observada de evidencia aportada; no es
firma, autenticación o permiso. El proceso Python cooperativo sigue siendo parte
del modelo de confianza. Los estados históricos no se modificarán en el inventario.

## Verificaciones finales

La única suite completa final se ejecutó después de cerrar código y pruebas:
**2332 aprobadas, 0 fallidas, 0 errores**, en 899.040 s. Incluye las 2294
anteriores y 38 nuevas; no se suman pasadas dirigidas o subtests al total.

## Reutilización e integración

| Componente | Uso y compatibilidad |
|---|---|
| RC1 | Contextos y vínculos nativos, validaciones y cambiar_estado. La fuente QA aporta un resultado, sin afirmar cierre completo de su evaluación. La operación exportadora es distinta y ya debe estar INICIADA |
| RC2 | Perfiles técnicos del resultado nativo y JSON; los requisitos declarados se mantienen en RC3, sin otro comparador o metadatos científicos inventados |
| RC3 | Inspección/precedencia/políticas/cuotas existentes. Si las cotas RC8 son más estrictas se usa el inspector nativo con una copia que cambia solo límites, sin otro grafo |
| RC4 | Una producción 1→1, referencias/revisiones y linaje nativos. El resultado QA es entrada lógica del inventario exportador; no se simula como una producción de dataset de tipo QA |
| RC5 | Solo materializa la salida realmente generada. Publicación exclusiva, lectura/hash físicos y estados permanecen en sus informes separados |
| RC6 | Conserva inventario y bytes, con entrada lógica externa explícita. No conserva la captura RC8, su testigo o cierre |
| RC7 | Se usa su unión conservadora de políticas y se prueba su inspector sin alterar admisión de dependencias. El consumidor hipotético sigue pendiente |
| Exportación/consumo 85-C/D | JSON QA nativo sin cambios, comprobación de esquema, identidad, huella y restricciones por el consumidor existente; contraste con los argumentos originales mediante _Conversion |

Se crean cinco archivos y no se modifica ninguno anterior:

| Archivo | Función |
|---|---|
| [cierre_exportacion.py](../src/spica/artefactos/cierre_exportacion.py) | Tres DTO, invocación explícita del productor fijo y cotejo específico |
| [test_cierre_exportacion_rc8.py](../tests/test_cierre_exportacion_rc8.py) | 38 pruebas del productor real, fronteras de evidencia y compatibilidad |
| [contrato_cierre_tecnico_noqa_rc8.md](contrato_cierre_tecnico_noqa_rc8.md) | Productor, contratos, estados, garantías y límites |
| [piloto_cierre_productor_rc8.md](piloto_cierre_productor_rc8.md) | Datos sintéticos, ejecución, evidencia física y casos adversariales |
| auditoria_arquitectonica_rc8.md | Este informe |

La dependencia es una hoja: artefactos.cierre_exportacion → RC7/RC4/RC3/RC1 y
exportación/consumo existentes. Ningún módulo anterior la importa. No hay ciclo
que involucre RC8 en el grafo AST de 122 módulos. Las utilidades privadas de
texto, medición, diagnósticos, unión y conversión quedan localizadas; no se crea
un codec o infraestructura paralela ni se amplía una API estable por conveniencia.

## Evidencia obtenida y límites de admisión

La variante base realmente genera 3852 bytes UTF-8, SHA de bytes en memoria
8a9ed4f6977f1c25c2d230589666947fcca6bf50d7c3b2fff4ecc9a4c606eb07.
El ID nativo es
qa0-734e241e0153c936862cd3ec0c902f0788bd4186b5616418368be52a200f470a.
La captura observa la invocación, resultado y un nuevo snapshot CONCLUIDA,
manteniendo INICIADA la declaración histórica. Consumir/exportar un diagnóstico
no demuestra evaluación de un lote ni calidad científica de sus observaciones.

RC5 materializa esos bytes, coteja igualdad y hash físicos. Otra prueba corrompe
o retira solo su copia propia y verifica que ya no está íntegra. La captura sigue
siendo evidencia histórica de generación, sin prometer disponibilidad actual.
La publicación repetida preserva inodo y contenido del archivo previo.

La conservación/recuperación RC6 usa sus APIs y formato existentes. La entrada
QA lógica es externa; no se inventa archivo suyo. La copia JSON se recupera y
RC7 mantiene pendientes las asociaciones/dependencias que no puede acreditar.
No se inserta un cierre QA o no QA en el codec para forzar aceptación.

Dos proyectos MD distintos producen los mismos bytes al forzar deliberadamente
el mismo espacio contextual nominal en inventarios separados. El JSON no lleva
project_id MD: su unicidad depende del llamador. RC8 conserva cada contexto MD y
rechaza intercambiar capturas, incluso con resultado_id, SHA y tamaño iguales.
No se deduce identidad de proyecto, linaje o permiso del contenido compartido.

La unión reutilizada de RC7 conserva variantes de políticas contradictorias y
bloquea el efecto; no devuelve una lista vacía que oculte restricciones. Se
mantienen los bloqueos heredados, incluidos los que solo limitan usos científicos
y permiten esta exportación técnica. El JSON no incorpora restricciones RC1/RC4
ajenas a su formato: la envolvente conserva esa información por separado.

El informe técnico puede comprobar este cierre específico mientras RC3/RC7
permanecen pendientes. No se modifica su informe, política o habilitación. No hay
permisos efectivos, autenticación del productor u operador, validez científica,
firma de origen, reloj acreditado o garantía de una sola invocación por ID.

## Ensayos y correcciones durante desarrollo

La primera pasada RC8 ejecutó 32 métodos: 29 sin error y 3 con errores, con cuatro
registros de error por subtests; 0 fallos de aserción. Dos pruebas referían
estado_actual en vez del atributo RC5 real estado_local. La tercera fixture era
rechazada por RC2 antes de alcanzar la asociación prevista. Se corrigieron los
tests, conservando el rechazo nativo, y se comprobó también una referencia QA
incompatible que sí alcanza el cotejo específico.

Se añadieron casos de restricciones del descriptor, alcance desconocido, hash
declarado de salida, tipo/versión nativa y conservación de publicación anterior.
La pasada siguiente ejecutó 447 pruebas: 37 RC8 y 410 RC1–RC7; todas aprobaron,
en 158.522 s. La auditoría final añadió una prueba de conflicto de restricciones,
reutilizó la unión conservadora RC7 y revalidó constructores/versiones nativas.

La última pasada dirigida ejecutó **448 pruebas en 102.318 s: 448 aprobadas,
0 fallidas y 0 errores**. Son 38 nuevas y 410 de RC1–RC7. No se suman repeticiones
ni subtests al total. Sintaxis, importaciones, espacios, ausencia de duplicaciones
y enlaces se comprobaron expresamente también sobre archivos sin seguimiento.

Las pruebas cubren éxito real, entrada inválida, proyectos/operaciones/productores
equivocados, versiones, resultado incompatible/alterado/ausente, declaración sin
invocación, parcialidad, fallo, cancelación, restricciones heredadas/conflictivas,
hash/tamaño, publicación exclusiva, conservación/recuperación y ausencia de
habilitación QA o automática. Las barreras de memoria niegan sockets, archivos y
SQLite; la inspección no despacha operaciones ni evalúa QA. El consumidor usa su
contraste de serialización nativo, no se presenta como una nueva operación.

## Comandos y resultados finales

Todo Python usa .venv y -B; las rutas solo cambian en el proceso. Los tests que
requieren TEMP privado Windows se ejecutan fuera del sandbox por sus permisos,
sin modificar ACL ni conceder acceso a datos operativos.

```powershell
$env:PYTHONPATH = (Join-Path $PWD 'src') + ';' + (Join-Path $PWD 'tests') + ';' + $PWD.Path
$env:PYTHONDONTWRITEBYTECODE = '1'
.\.venv\Scripts\python.exe -B -m unittest test_cierre_exportacion_rc8 test_integracion_artefactos_rc7 test_conservacion_rc6 test_materializacion_rc5 test_artefactos_rc4 test_contextos_rc1 test_perfiles_informacion_rc2 test_coordinacion_rc3 -q
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -B -m pip check
git diff --check
git status --short
```

Versiones comprobadas: Python 3.15.1, HTTPX 0.28.1 y SQLite 3.53.4. No se
instalaron paquetes. La suite completa terminó con código 0:

```text
Ran 2332 tests in 899.040s

OK
```

| Comprobación final | Resultado |
|---|---|
| Dirigidas RC1–RC8 | 448 aprobadas, 0 fallidas, 0 errores; 102.318 s |
| Suite completa | 2332 aprobadas, 0 fallidas, 0 errores y 0 omitidas |
| pip check, después de la suite | No broken requirements found.; salida 0 |
| Sintaxis, duplicaciones, importaciones y espacios | Correctos, incluidos los Python nuevos sin seguimiento |
| Grafo AST | 122 módulos; sin ciclo que incluya RC8 ni imports anteriores hacia el adaptador |
| TEMP | Cero directorios residuales spica-rc3-qa-*, spica-rc5-* y spica-rc6-* |
| Raíces de tests en repositorio | Cero directorios .suadc-test-* residuales |
| git diff --check | Sin salida, código 0; complementado por inspección directa de archivos nuevos |
| Archivos registrados e índice | git diff --name-only HEAD y git diff --cached --name-only sin salida |

El código y las pruebas no se editaron desde el inicio de la suite final; solo
se completó documentación. Registro verbose completo conservado fuera de Git:
`%TEMP%/spica-rc8-suite-final-2a5443b7681e460eb3584cc31c3b73af.log`.
No se necesitó limpieza correctiva de temporales, borrado recursivo o reparación.
Los enlaces locales y cercas se comprobaron sin conexiones externas.

Git final: feature/suadc-http, mismo HEAD
c1b224ed58e7227d7bd057ed8f54684a6b84509b; cinco archivos nuevos sin seguimiento:

```text
?? docs/auditoria_arquitectonica_rc8.md
?? docs/contrato_cierre_tecnico_noqa_rc8.md
?? docs/piloto_cierre_productor_rc8.md
?? src/spica/artefactos/cierre_exportacion.py
?? tests/test_cierre_exportacion_rc8.py
```

No se modificó ningún archivo anterior ni el índice. No hubo commits o push.

## Conexiones originales y datos institucionales

Se conservan las definiciones de [85-F](matriz_dependencias_integracion_paso85f.md)
y [85-M](matriz_diseno_implementacion_paso85m.md):

| Conexión | Estado tras RC8 |
|---|---|
| M03, C08 → C09/C02: ejecutor PlanConsulta / selectores institucionales → HTTP, mecanismo/presupuesto/autorización | **P**, no hay ejecutor o solicitud institucional |
| M16, C12 → C02/C11: decisión de readquisición → GET/ingesta mediante hook y ejecutor aprobado | **P**, una recomendación no activa efectos |
| M26, C20 → C21/C24/C19: evidencia documental → QA/aplicabilidad/operación con vínculo revisado | **P**, un diagnóstico sintético y su JSON no aprueban documentación institucional |
| M32, resultados futuros → almacenamiento/exportación científica, derivados y linaje | **P**, avance parcial RC4–RC8 en contratos/conservación/asociación y cierre técnico específico. Exportar JSON QA existente no resuelve la conexión científica original |

Las [29 brechas PNDA](brechas_reconciliadas_pnda_paso84i.md) permanecen intactas:
2 RESUELTA_CON_EVIDENCIA, 17 PARCIALMENTE_DOCUMENTADA, 8 PENDIENTE_DE_EVIDENCIA,
2 CONTRADICCIÓN_DOCUMENTADA. INGEMMET /query sigue NO AUTORIZADO. No se abre
el CSV PNDA, RAW, staging, SQLite operativo o evidencia institucional privada.
No se vuelven a medir originales reales para afirmar nueva integridad física:
se informa ausencia de acceso/escritura operativos en este incremento.

Cero conexiones externas, descargas, instalaciones, migraciones, commits o push.
No se cambia main.py, .gitignore, .venv, dependencias, formatos 85-J/K, SQLite
85001, JSON QA 0.1.0 o rc6.generacion.0.1.0. Todos los cuerpos nuevos son sintéticos.

## Riesgos, prioridad siguiente y dictamen

Persisten confianza en proceso Python y evidencia de entrada, falta de
autenticación, unicidad contextual externa, captura solo local y ausencia de
durabilidad/custodia del cierre. Copiar una evidencia como DTO no conserva su
testigo. El hash de memoria no garantiza un archivo; el hash físico fechado no
garantiza disponibilidad futura. Las barreras de test no son un sandbox hostil.
Hay cotas locales, sin reserva de recursos/RSS/CPU o interrupción dentro del
exportador atómico. RC5/RC6 conservan sus riesgos TOCTOU, retención y concurrencia.

Tras revisión, se recomienda auditar un consumidor concreto de este cierre y
decidir explícitamente su política de admisión y requisitos de conservación de
evidencia antes de ampliar RC3/RC7 o codecs. No crear un motor universal de cierres
ni otro ejecutor; mantener retención/control protegido antes de datos únicos o
destino operativo. No se inicia RC9 ni ciencia automáticamente.

Dictamen final: **APTO CON RESTRICCIONES** para el cierre técnico específico de
este exportador en memoria, con ensayos sintéticos offline. No quedan fallos o
correcciones bloqueantes conocidos para ese alcance. La admisión en dependencias,
conservación del cierre, autenticidad, permisos y usos operativos siguen pendientes.
La arquitectura integral no está terminada y cualquier continuación requiere
la auditoría del equipo. No se inicia RC9 ni un núcleo científico.
