# PASO 78: auditoría del subsistema de adquisición multiinstitucional

Dictamen: **APTO CON RESTRICCIONES para preparar incrementos offline y revisar
especificaciones. No autoriza otra adquisición ni una integración institucional real.**

## Estado inicial, método y alcance

Git inicial limpio, rama `feature/suadc-http`, HEAD `fb34162`:
`SPICA: aplicabilidad cientifica y auditoria de confianza documental`.
El commit contiene los diez archivos de los PASOS 76/77, incluida la corrección
de parámetros sin procedencia. Se verifica que esa etapa está registrada.

Se inventariaron **41 módulos Python** bajo `src/spica/adquisicion`, revisando
contratos, interfaces y flujos principales de transporte, reintentos, streaming,
RAW/configuración/inspección, catálogo/revisiones/evidencias, integración,
planificación, conector y lectura/verificación local. Se contrastaron sus pruebas
y documentación. Es una auditoría de capacidades y límites, no una certificación
exhaustiva de seguridad o conformidad científica.

No se consultó internet, usaron credenciales reales ni abrieron almacenes
operativos. La evidencia institucional procede de informes locales anteriores,
sin repetir sus operaciones. No se identificó un defecto compartido reproducible
que requiera corregir código para este diagnóstico. Las carencias siguientes
requieren especificación y revisión, no cambios preventivos del núcleo estable.
**El PASO 78 añade únicamente tres documentos; no cambia Python ni pruebas.**

## Componentes reutilizables y fronteras

| Componente | Reutilización comprobable en código | Frontera relevante |
| --- | --- | --- |
| `nucleo/modelos.py`, `temporal.py` | Fuente, recurso, solicitud multiestación/multivariable, estados separados y validación temporal | Fuente es identidad declarada; solicitud exige dos instantes con zona. No fabrica filtros institucionales ni representa autorización |
| `transportes/http.py` | GET pequeño y apertura común para streaming; orígenes, timeouts, HTTP y compresión | No es una API científica ni un ejecutor de POST, autenticación o paginación |
| `transportes/reintentos.py` | Política explícita, backoff, jitter, Retry-After, historial y cancelación | Solo última operación en memoria; no diario duradero ni reanudación |
| `transportes/descargas.py` | Escritura por bloques, comprobación física, publicación exclusiva y limpieza | Staging, no conservación definitiva; requiere volumen compatible con enlaces duros |
| `almacenamiento/*` | Incorporación de archivos regulares, MD-01/02/03, hash/tamaño, deduplicación física, recuperación y diagnóstico | Uso secuencial; sin transacción global archivos/SQLite, respaldo o autenticidad institucional |
| `catalogo/modelos.py`, `persistencia.py` | Instituciones/productos/estaciones/variables/disponibilidad/capacidades, procedencia, historial y lectura acotada | Metadatos registrados no equivalen a acceso vigente, permiso ni observaciones adquiridas |
| `catalogo/documental.py`, `evidencias.py` | Revisiones por recurso e instantánea de una adquisición HTTP vinculada al activo | La evidencia de adquisición persistida es específica de HTTP; no debe simular una entrega manual |
| `integracion/http_raw.py` | Coordina el mismo cliente con staging, RAW, recuperación e inspección estructural | No ejecuta planes, no modifica observaciones y no proporciona atomicidad global |
| `conectores/senamhi/*` | Descubrimiento HTML PNDA y adquisición acotada de diccionarios XLSX | Fuente SENAMHI fija, un origen y estructura HTML concretos; no es conector PNDA multiinstitucional |
| `planificacion/*` | Propuestas acotadas sobre solicitudes y evidencia catalogada, sin producto cartesiano inventado | `PlanConsulta.ejecutable` es siempre False; PREPARADA no es autorización ni disponibilidad remota actual |
| `verificacion/*` | Inspector técnico CSV/XLSX y lector CSV secuencial genérico, con presupuestos | Muestreo/estructura no prueban semántica ni integridad institucional; no hay validación GIS |
| `consultas_locales/*` | Selección local conservando valores y fechas civiles | Perfil SENAMHI de 16 campos y TEMP/HR/PP; no consulta remota ni lector científico universal |

Los `__init__.py` exponen esas interfaces; no se agregan motores alternativos.
Los contratos y motores QA/QC posteriores se conservan separados y no se activan.

## Correspondencia del contrato con la integración futura

| Necesidad | Representación existente | Resultado de auditoría |
| --- | --- | --- |
| Institución, producto, recurso | `Fuente`; `ProductoCatalogo`; `RecursoDescubierto`/`RecursoCatalogo`; declaración RAW | Identidades separadas y literales. La identidad institucional no se autentica por el nombre o dominio |
| Mecanismo de acceso | `MecanismoAdquisicion`, `CapacidadCatalogo`, modalidad textual | HTTP_DIRECTO tiene ejecución. Otros valores del enum no implementan sus protocolos |
| Permisos y restricciones | Licencia/referencia declarada, `autenticacion_requerida`, descripción y procedencia | Sirven para documentar condiciones; no hay contrato ejecutable de permisos, acuerdos, vencimientos o identidad del usuario |
| Procedencia | Referencias y fechas de consulta; declaración pública; evidencia HTTP vinculada al activo | Se diferencia evidencia declarada y comprobación técnica. No conservar consultas puede impedir reproducir por completo un recurso parametrizado |
| Versiones documentales | Versión de producto/diccionario opcional y revisiones históricas locales | Revisión local no es edición del documento institucional. Los desconocidos permanecen None |
| Declarado frente a observado | Estados de verificación, formato/MIME declarado, SHA/tamaño físicos e informe estructural aparte | Un HTTP 200, extensión, MIME o marca VERIFICADO no certifican todo el producto ni validación científica |
| Fallos y desconocidos | Errores HTTP/RAW, estados por recurso, disponibilidad desconocida y planes condicionados | Un fallo previo a preparar RAW no deja diario persistente de todos los intentos de red; un catálogo vacío no prueba ausencia de datos |
| Variables y estaciones | Códigos originales por fuente/producto, asociaciones explícitas, opcionalidad de estaciones | No hay armonización universal de unidades, nombres, frecuencias, instrumentos o estaciones |
| Recursos no temporales | Recurso y adquisición directa sin pasar por solicitud científica temporal | `SolicitudAdquisicion` exige fechas: no inventar un período para un diccionario, capa estática o entrega manual; revisar un caso real antes de ampliar el contrato |
| Evitar descargas injustificadas | Historial de recursos y adquisiciones, metadatos e integridad RAW | No hay política previa de readquisición. IDENTICO evita otra revisión, no otro GET. Deduplicación física ocurre después de recibir/copiar bytes |

`VariableCatalogo.id_interno` es único en el catálogo y distinto del código original;
su asignación debe evitar colisiones entre fuentes. Las identidades originales de
fuentes diferentes no se unifican por compartir nombre o código. La elección de
`family`/`kind` en MD-02 sigue declarada, sin vocabulario científico inventado.

## Seguridad: garantías reales y límites

| Control | Implementación inspeccionada | Restricción para futuras integraciones |
| --- | --- | --- |
| TLS y esquema | Verificación TLS predeterminada; descarga e integración rechazan `verificar_tls=False`; PNDA exige HTTPS | El cliente genérico acepta orígenes HTTP explícitos y permite desactivar TLS en GET pequeño. TLS activado no cifra una URL HTTP. Exigir HTTPS y configuración verificada en el producto que lo necesite; no se cambia esa política aquí |
| Orígenes | Comparación de esquema, host y puerto; sin proxies del entorno | No autentica institución ni aplica aislamiento de IP/DNS; lista configurada por operador de confianza |
| Redirecciones | Automáticas desactivadas y respuestas 3xx rechazadas | Cambio de origen o URL requiere revisión. 304 tampoco es una respuesta admitida por la política actual |
| Autenticación | URLs sin userinfo; sin API pública de login, OAuth, API-key o renovación | Parámetros GET son texto y pueden ser sensibles; no usarlos como una implementación improvisada de autenticación |
| Secretos | Errores públicos acotados, referencias filtradas, consultas/fragmentos omitidos de evidencia HTTP y claves RAW autorizadas | Filtros conservadores, no detector universal. No registrar cuerpos, cabeceras, objetos de petición o trazas arbitrarias; SQLite no está cifrado y los archivos privados requieren control de acceso |
| Tamaño y RAM | GET por defecto 1 MiB configurable; streaming con máximo por operación y conteo real; bloque por defecto 64 KiB, máximo 1 MiB | Configurar límites coherentes en transporte/adaptador/RAW/inspector. No existe cuota total de RAM/disco impuesta por el SO |
| Compresión y parciales | Solicita identity; rechaza Content-Encoding distinto de identity y HTTP 206 | No hay descompresión HTTP ni reanudación/Range. ZIP dentro de XLSX se inspecciona bajo límites separados |
| Reintentos | Un intento por defecto; recuperables 408/429/500/502/503/504 y errores de red seleccionados; 401/403/404/TLS no se reintentan | Solo GET; máximo configurable hasta 100. Retry-After excesivo detiene en vez de adelantarlo. No hay plazo total de operación; timeout es por fase/actividad |
| SHA-256 | Hash de bytes escritos, relectura del staging y nuevas comprobaciones durante incorporación/recuperación RAW | Integridad local, no firma del proveedor ni validez científica; recuperar entrega una ruta que puede cambiar después |
| Publicación | Temporales propios, rechazo de enlaces/junctions y enlace duro exclusivo sin sobrescritura | Volumen local compatible y uso secuencial privado. No elimina carreras frente a terceros con capacidad de sustituir rutas |
| Procedencia y errores | Evidencia por adquisición y errores por fase; recursos, activos y hashes separados | No hay transacción conjunta HTTP–dos SQLite–archivos; un fallo posterior puede dejar un activo o residuo que requiere revisión |
| Cancelación | Cooperativa en intentos, esperas y bloques HTTP; cancelación propia del lector CSV | No interrumpe inmediatamente una llamada síncrona bloqueada ni existe un Event único para toda la copia RAW/inspección. No afirmar cancelación de extremo a extremo |

La validación de `ConfiguracionRAW` considera rutas, permisos y espacio; abrir un
almacén operativo también hace sondas de escritura/publicación. Por ello **no se
llamaron `validar`, `abrir`, `diagnosticar`, `verificar` o `recuperar` sobre el RAW
real durante esta auditoría**. No se ejecutaron migraciones. La inspección de WAL
puede necesitar una copia temporal con su presupuesto y privacidad existentes.

## Riesgos y compatibilidad institucional

| Riesgo/carencia | Situación confirmada | Acción previa a integrar |
| --- | --- | --- |
| Ampliar PNDA cambiando solo la URL | El conector conserva Fuente SENAMHI y no autentica el editor de una página alternativa | No reutilizarlo como conector de ANA/OEFA/INGEMMET; verificar atribución y especificación real |
| Supuesta API científica | Solo GET y parámetros genéricos; sin filtros remotos verificados, paginación o contrato institucional de consulta | Obtener documentación oficial de cada producto antes de programar traducción de selectores |
| Entrega manual presentada como HTTP | `incorporar_documentado`/paquete de evidencia afirman capacidad HTTP_DIRECTO | Usar incorporación básica para bytes si se autoriza; diseñar recibo manual sin inventar HTTP ni migrar RAW automáticamente |
| Repetición innecesaria | Es posible solicitar/incorporar otra vez el mismo recurso; los activos distintos se preservan | Definir decisión y justificación previa, sin perder adquisiciones legítimas de contenido idéntico |
| Cambios de licencia/acceso | Se guardan declaraciones y revisiones; no se valida jurídicamente el permiso | Revisión del documento y alcance del acceso, sin convertir enlace/licencia en autorización automática |
| Información espacial | Coordenadas/CRS declarados y almacenamiento opaco disponibles; sin geometría ni validación espacial | Documentar CRS, ejes, unidad, cobertura, escala/resolución y piezas del recurso; no inferir transformación o formato por extensión |
| Escala y concurrencia | Planificador tiene lectura acotada; varias consultas/listados históricos recuperan colecciones completas; uso RAW secuencial | Revisar volumen, índices/paginación y exclusión de escritores antes de otro patrón de uso |
| Confianza y calidad | Marcas documentales aportadas por el llamador, sin autorización científica operativa | Conservar las barreras 76/77; ninguna adquisición activa QA/QC Nivel 1 |

La insuficiencia de evidencia local para ANA/OEFA/INGEMMET no demuestra que carezcan
de datos, portales o APIs. Su mecanismo, URL, filtros, permisos y disponibilidad
están **pendientes de verificación institucional**, sin inventar endpoints.

La [matriz](matriz_capacidades_adquisicion.md) separa evidencia externa histórica,
pruebas sintéticas y capacidades ausentes. El [plan](plan_adquisicion_multiinstitucional.md)
propone tres incrementos, sujetos a revisión y sin ejecución durante este paso.

## Cierre tras la reanudación del 2026-10-30

La interrupción encontró completados el inventario y diagnóstico de adquisición,
la matriz A–G, la distinción de evidencias/pruebas, la priorización institucional,
los riesgos y el plan de tres incrementos. Ya estaban creados los tres documentos
y ejecutadas la suite completa y las comprobaciones de dependencias/formato.
Quedaban pendientes incorporar el resultado final al informe y entregarlo para
revisión. Se conservaron los avances; no se reinició la auditoría ni se implementó
ningún incremento del plan.

Al retomar, Git mostraba únicamente esos tres documentos sin seguimiento, con
HEAD `fb34162` e índice sin cambios. Se recuperaron `baseline.json`,
`inventario.json`, `resultado.json` y `unittest.log` del directorio temporal
`spica-paso78-a56fa52b03e144faa4c33111e8a7be4f`, fuera de Git y de los almacenes.
La instantánea confirma que todos los archivos Python de `src/` y `tests/`
conservan exactamente los bytes de la ejecución completada, sin altas ni bajas.

Resultado conservado de esa ejecución con Python de `.venv`:

```text
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
Ran 938 tests in 105.564s
OK
```

**938 aprobadas, cero fallos, errores u omisiones; ninguna prueba nueva.** Los
identificadores coinciden exactamente con las 938 del PASO 77. Se verificaron
también las 938 líneas de éxito y el cierre OK del log, no solo el contador del
resumen. Al no haber cambios de código/pruebas, no se repitió la suite al retomar.
Su resultado no se presenta como una nueva ejecución posterior a la interrupción.

La suite utilizó `PYTHONPATH` temporal para `src` y una guardia que bloquea accesos
Python a las rutas operativas conocidas y conexiones de red; el registro conserva
cero intentos bloqueados. Esa guardia no es un sandbox del sistema operativo ni
una garantía frente a alias, hardlinks o código nativo hostil. No se abrieron
RAW, staging o SQLite operativos, tampoco para inventarios o hashes actuales.

Durante el cierre se ejecutaron nuevamente:

```text
.\.venv\Scripts\python.exe -B -m pip check
No broken requirements found.

git diff --check
Código 0, sin errores de whitespace.

git diff --cached --check
Código 0, sin errores de whitespace.
```

Entorno reconfirmado: Python **3.15.1**, HTTPX **0.28.1**, SQLite **3.53.4**.
Git emitió un aviso de conversión futura LF→CRLF para `main.py`, sin diferencias
de contenido registradas por `git diff`. No se modificó ese archivo ni la
configuración Git para suprimir el aviso.

Los archivos nuevos se comprobaron directamente porque `git diff --check` no los
inspecciona: UTF-8, salto final, espacios finales, ausencia de conflictos y enlaces
locales, incluidos sus apartados de destino. También se comprobó la sintaxis de
los 41 módulos de adquisición sin ejecutarlos ni generar bytecode. Se contrastó
la coherencia de los tres documentos con el diagnóstico y el código ya auditados.

Estado final:

```text
?? docs/auditoria_adquisicion_multiinstitucional.md
?? docs/matriz_capacidades_adquisicion.md
?? docs/plan_adquisicion_multiinstitucional.md
```

Misma rama y HEAD; ningún cambio en el índice, fuentes, pruebas, dependencias,
contratos RAW o reglas QA/QC. No hubo conexiones externas, descargas,
instalaciones, migraciones, commits o push. No se inició el flujo manual, una
readquisición ni la investigación externa de INGEMMET. Los tres incrementos
permanecen propuestos y pendientes de revisión del usuario.
