# PASO 85-F — Auditoría integral de arquitectura de SPICA

Fecha: **2026-11-11, America/Lima**. Base inspeccionada: **720c0f9**, rama
**feature/suadc-http**, árbol inicialmente limpio. Dictamen: **APTO CON
RESTRICCIONES para preparar integración experimental offline**. No acredita una
plataforma científica integrada, producción, derechos institucionales o una nueva
autorización. Solo se crean los tres documentos del PASO 85-F.

La [matriz de integración](matriz_dependencias_integracion_paso85f.md) identifica
conexiones, pruebas y pendientes; la [hoja de ruta](hoja_ruta_arquitectonica_paso85f.md)
ordena su resolución. Los IDs C, R, H y M son referencias **de esta auditoría**,
no identificadores oficiales de requisitos históricos.

## 1. Recuperación, método y límites de evidencia

Antes de escribir se ejecutaron git status, git log -5 --oneline y
git branch --show-current. El PASO 85-E está consolidado:

```text
720c0f9 SUADC: cierre experimental QAQC nivel 0 y conciliacion entre lotes
7515d75 SUADC: consumidor seguro de exportaciones QAQC nivel 0
ce2bf49 SUADC: exportacion trazable QAQC nivel 0
b2c0171 SUADC: versionado y restricciones QAQC estructural nivel 0
3535a47 SUADC: auditoria y piloto QAQC estructural nivel 0
```

Se inventariaron archivos seguidos por Git y las carpetas públicas del proyecto;
no se recorrieron directorios privados, .venv, .git o almacenes operativos.
Se examinaron contratos, implementaciones, imports, inicializadores, herramientas,
pruebas representativas e informes históricos. El análisis AST lee código como
texto y compila en memoria, **sin importar ni ejecutar módulos de SPICA**.

Inventario en HEAD: **100 archivos Python**, **24 inicializadores de paquete**,
**15537 líneas** bajo src/spica; **52 archivos test_*.py con 1709 métodos test_**,
tres herramientas Python y 78 Markdown históricos en docs. Los conteos de líneas
incluyen comentarios y blancos; no son métricas de completitud o cobertura.
La detección estática de métodos no sustituye unittest discover.

Entorno reconfirmado con el intérprete .venv: **Python 3.15.1**, **HTTPX 0.28.1**
(metadatos de distribución), **SQLite 3.53.4** (módulo estándar, sin conexión).
La única dependencia directa de requirements.txt es httpx==0.28.1. Sus requisitos
básicos declarados son anyio, certifi, httpcore==1.* e idna; se observaron anyio
4.15.1, certifi 2026.10.23, httpcore 1.0.9, idna 3.20 y h11 0.16.0 instalados.
Los extras HTTPX no equivalen a capacidades implementadas de SPICA. No se hizo
una auditoría de vulnerabilidades, compatibilidad entre plataformas o benchmark.

Esta etapa es documental: **cero pruebas unitarias nuevas o ejecutadas**;
**1709 aprobadas, cero fallos/errores/omitidas** es el resultado histórico del
[85-E](cierre_experimental_qaqc_paso85e.md), no una ejecución del 85-F. Tampoco se
repitió pip check: su resultado favorable pertenece al 85-E. Se comprobarán los
tres archivos nuevos directamente y mediante git diff --check y git status --short.

## 2. Especificaciones recuperadas y trazabilidad de decisiones

No se encontró una SRS global, un documento titulado arquitectura aprobada de la
Etapa 1 ni el Protocolo de Desarrollo Acelerado en los archivos versionados. La
búsqueda textual de esas denominaciones en docs tampoco encontró coincidencias.
Esto limita la trazabilidad global; **no demuestra que esos documentos no existan
fuera del repositorio**. No se buscaron en carpetas ajenas ni se inventó su contenido.

Referencias de trabajo realmente disponibles:

| Bloque / referencia local revisada | Decisión o alcance conservado |
|---|---|
| [Contrato de adquisición](contrato_adquisicion.md), [tiempo](politica_temporal.md), [transporte](transporte_http.md), [descargas](descargas_http.md), [reintentos](reintentos_http.md) | Descubrir, transferir, comprobar y confirmar son fases distintas; GET controlado y tiempos conocidos |
| [RAW / MD-01/02/03](almacenamiento_raw.md), [HTTP→RAW](integracion_http_raw.md), [registro de evidencias](registro_evidencias.md) | Proyecto, objeto, adquisición, activo y contenido físico son identidades diferentes; uso secuencial |
| [Catálogo](catalogo_cientifico.md), [planificación](planificacion_consultas.md), [auditoría 78](auditoria_adquisicion_multiinstitucional.md), [manual](ingesta_manual.md), [readquisición](readquisicion.md) | Plan y recomendación no ejecutan mecanismos ni conceden permisos; entrega manual no simula HTTP |
| [Inspector ArcGIS 82](validacion_metadatos_ingemmet_paso82.md), [vectorial 83-A](adquisicion_vectorial_offline.md), [83-B](auditoria_vectorial_paso83b.md), [83-C](simulacion_piloto_arcgis_paso83c.md), [83-D](alternativas_adquisicion_ingemmet_paso83d.md), [83-E](fuentes_oficiales_ingemmet_paso83e.md) | Metadatos y prototipos offline no demuestran acceso a entidades, equivalencia de servidores ni licencia; /query NO AUTORIZADO |
| [Interoperabilidad 84-A](interoperabilidad_espaciotemporal.md), [84-B](adaptadores_interoperabilidad_offline.md), [84-C](integracion_local_pnda_paso84c.md) | Adaptación documental no ejecuta asociaciones GIS ni resuelve tiempo desconocido |
| [Reconciliación 84-I](reconciliacion_xlsx_docx_pnda_paso84i.md), [contratos 84-J](contratos_metadatos_documentales_paso84j.md), [84-K](auditoria_procedencia_metadatos_paso84k.md), [84-L](vinculacion_evidencia_paso84l.md) | Declaración, cotejo literal, correspondencia editorial, evidencia independiente y derechos permanecen separados |
| [Nivel 0](calidad_nivel0.md), [85-A](inventario_qaqc_nivel0_paso85a.md), [85-B](auditoria_contratos_qaqc_paso85b.md), [85-C](contrato_exportacion_qaqc_paso85c.md), [85-D](contrato_consumo_qaqc_paso85d.md), [85-E](auditoria_lotes_qaqc_paso85e.md) | Estados y restricciones viajan juntos; aceptación de JSON y coincidencia de lotes no certifican ciencia |
| [Catálogo de reglas científicas](catalogo_reglas_cientificas.md), [aplicabilidad](verificador_aplicabilidad_cientifica.md), [confianza](auditoria_confianza_documental.md), [experimento sintético](evaluador_limites_sinteticos.md) | Catálogo declarativo, revisión y aplicabilidad no habilitan un ejecutor institucional |
| Encargo explícito 85-F | IA híbrida futura: local principal, APIs opcionales, ciencia independiente de IA; equipos modestos y trabajo offline. Decisión suministrada por el usuario, sin implementación ni documento previo identificado |

Se aplica el protocolo suministrado en el encargo: reutilizar estas decisiones,
agrupar pendientes por frontera, no reabrir contratos estables sin contradicción,
y detener usos bloqueados. No se atribuye aprobación formal a un informe por estar
registrado en Git. El protocolo orienta esta auditoría; no se implementa un proceso
automático de aprobación.

| Requisito identificado | Responsable / evidencia real | Prueba localizada | Cumplimiento y dependencia pendiente |
|---|---|---|---|
| R01: adquisición multifuente, multivariable y multiestación sin inventar códigos | C01/C07/C08; Fuente y SolicitudAdquisicion, disponibilidades explícitas | test_adquisicion_nucleo.py; test_planificacion.py | Contratos/plan implementados; ejecución institucional general pendiente |
| R02: transporte limitado, TLS, orígenes y reintentos controlados | C02–C04 | test_transporte_http.py; test_descargas_http.py; test_reintentos_http.py | Implementado; política genérica permite excepciones que un flujo aprobado debe excluir, H04 |
| R03: originales preservados, identidad y persistencia técnica | C05/C06/C10/C11; MD-01/02/03 | test_modelos_md_raw.py; test_almacenamiento_raw.py; test_integracion_http_raw.py | Integración sintética probada; concurrencia, durabilidad y respaldo no generales |
| R04: metadatos versionados y procedencia | C07/C12/C20 | test_catalogo_cientifico.py; test_registro_evidencias.py; test_metadatos_documentales.py | Parcial para plataforma: no hay equivalencia/autenticidad inferida ni puente científico general |
| R05: espacial/temporal con incertidumbre | C01/C18/C19 | test_temporal.py; test_vectorial_precision.py; test_integracion_interoperabilidad.py | Contratos y controles probados; sin GIS operativo o conversión de marcos desconocidos |
| R06: QA estructural trazable conservando restricciones | C21–C23 | test_calidad_nivel0.py; pruebas 85-A…85-E | Ciclo experimental probado; especializado en perfil PNDA, sin ejecución científica |
| R07: revisión de reglas científicas y aplicabilidad | C24 | test_reglas_cientificas.py; test_aplicabilidad_cientifica.py; test_confianza_documental.py | Contratos y barreras implementados; ejecutor científico institucional ausente |
| R08: ejecución autorizada, recuperable y reproducible de toda la cadena | Estados/cancelación locales C02–C06/C15/C21 | Pruebas de componentes y fallos por fase | Parcial: no tarea global, diario común, autorización ni ensayo vertical completo, H02/H03 |
| R09: trabajo offline y recursos modestos | Streaming C03/C13/C15/C21, cuotas e índice temporal C16 | Tests de límites, cancelación y limpieza | Viable en perfiles acotados; sin mediciones de memoria/plazo global, H07 |
| R10: resultados derivados y exportación científica | ResultadoCientifico declarativo C24; JSON QA C22 | test_reglas_cientificas.py; test_exportacion_qaqc_85c.py | JSON existente solo QA0; no repositorio de derivados o intercambio científico general, H06 |
| R11: expansión ambiental e IA opcional | Contratos C01/C07/C19/C20/C24; decisión explícita del encargo | Fixtures multifuente/espaciales/documentales | Núcleos reutilizables; adaptadores por disciplina y puertos IA todavía propuestos, H05/H09 |
| R12: seguridad y separación de autorizaciones | Validaciones/estados y controles de rutas existentes | test_regresiones_altas.py; test_vinculacion_documental.py; tests 85-D/E | Controles locales dentro de proceso confiable, no aislamiento de plugins hostiles, H01/H04 |

Los nombres test_ de esta tabla se refieren a archivos reales de tests; la matriz
incluye enlaces y ejemplos de funciones. Cumplimiento local no equivale a cerrar
el requisito global. Las decisiones de interfaz final, automatización global, IA,
derivados y ciencia operativa aún no están reflejadas como funcionalidades.

## 3. Inventario real y madurez

Categorías: **A** implementado y probado aisladamente; **B** implementado y probado
en integración; **C** experimental; **D** parcial; **E** diseñado sin implementación;
**F** no evaluable por falta de evidencia. C puede tener integración sintética
comprobada; la columna de prueba distingue ese hecho. Ninguna categoría certifica
producción ni declara una prueba ejecutada hoy.

| ID / componente y archivos | Responsabilidad e interfaces reales; entrada → salida | Estado / evidencia de prueba |
|---|---|---|
| C01 [nucleo](../src/spica/adquisicion/nucleo/modelos.py), [temporal](../src/spica/adquisicion/nucleo/temporal.py) | Fuente, SolicitudAdquisicion, ResultadoRecurso/ResultadoAdquisicion; validar_intervalo/instante_utc. Identidades/fechas → contratos y validación | A; 32 tests de núcleo y 42 temporales; no E/S |
| C02 [http.py](../src/spica/adquisicion/transportes/http.py) | ClienteHTTP.get; URL y parámetros públicos → RespuestaHTTP acotada. Una política _abrir común | B; 17 transporte, compartido por pruebas HTTP→RAW |
| C03 [descargas.py](../src/spica/adquisicion/transportes/descargas.py) | ClienteHTTP.descargar / descargar_archivo; GET → archivo staging e InformeDescarga | B; 24 tests, tamaños/hash reales en fixtures |
| C04 [reintentos.py](../src/spica/adquisicion/transportes/reintentos.py) | PoliticaReintentos/GestorReintentos; GET callable → resultado o ErrorTransporteHTTP e historial | B; 37 tests y prueba de reintento en integración |
| C05 [raw.py](../src/spica/adquisicion/almacenamiento/raw.py), [catalogo RAW](../src/spica/adquisicion/almacenamiento/catalogo.py), [modelos MD](../src/spica/adquisicion/almacenamiento/modelos.py) | AlmacenRAW.incorporar, recuperar, verificar, metadatos, diagnosticar; archivo autorizado → activo/estado y referencia física | B, secuencial; 50 RAW, 22 MD, integración y regresiones |
| C06 [configuracion.py](../src/spica/adquisicion/almacenamiento/configuracion.py), [inspeccion.py](../src/spica/adquisicion/almacenamiento/inspeccion.py), [migraciones.py](../src/spica/adquisicion/almacenamiento/migraciones.py) | ConfiguracionRAW.validar/abrir/inicializar, AlmacenOperativoRAW.adaptador_http; ubicación/política → almacén reconocido. Migración separada | B experimental; 30 configuración, 37 cierre y regresiones; no se invocan ahora |
| C07 [catálogo científico](../src/spica/adquisicion/catalogo/persistencia.py), [documental](../src/spica/adquisicion/catalogo/documental.py), [evidencias](../src/spica/adquisicion/catalogo/evidencias.py) | CatalogoCientifico.registrar_documental/leer_acotado/consultar_revision, EvidenciaDocumental; entidades → registros/historial/instantáneas | B; 40 catálogo y 42 registro; sin autenticación del editor |
| C08 [planificacion](../src/spica/adquisicion/planificacion/planificador.py) | Planificador.planificar(SolicitudCientifica) → PlanConsulta con operaciones propuestas | A para preparación; 50 tests con catálogo temporal; plan.ejecutable=False |
| C09 [SENAMHI PNDA](../src/spica/adquisicion/conectores/senamhi/pnda.py) | descubrir, registrar_catalogo, adquirir; HTML público → recursos; adquisición solo diccionario XLSX en este piloto | B experimental; 36 tests con MockTransport; no filtros estación/variable/período remotos |
| C10 [http_raw.py](../src/spica/adquisicion/integracion/http_raw.py) | AdaptadorHTTPRAW.adquirir/adquirir_documentado → ResultadoHTTPRAW y estructura | B experimental; 25 integración y 11 formatos; presta cliente/almacén |
| C11 [manual](../src/spica/adquisicion/manual/ingesta.py) | IngestorManual.ingestar; SolicitudIngestaManual → ResultadoIngestaManual/recibo, vía RAW existente | B experimental; 51 tests con archivos locales sintéticos |
| C12 [readquisicion](../src/spica/adquisicion/readquisicion/motor.py), [antecedentes](../src/spica/adquisicion/readquisicion/antecedentes.py) | antecedente_desde_raw y decidir_readquisicion; instantáneas/restricciones → recomendación, autoriza_red=False | A; 72 tests en memoria; no conexión automática al cliente |
| C13 [verificación general](../src/spica/adquisicion/verificacion/inspector.py), [lector CSV](../src/spica/adquisicion/verificacion/csv_streaming.py) | verificar_archivo y LectorCSV; archivo regular → ResultadoEstructura / RegistroCSV e informe de cierre | B; 51 formatos, 42 CSV; inspección de formato no es inspección semántica total |
| C14 [inspector DOCX](../src/spica/adquisicion/verificacion/docx/inspector.py), [XLSX 84-E](../herramientas/inspeccionar_xlsx_84e.py) | inspeccionar_docx_archivo/inspeccionar_docx_bytes e inspeccionar_bytes; ZIP/XML acotado → inventario/referencias | C, integración acotada; 58 DOCX, 19 hipervínculos, 17 compatibilidad y 12 XLSX |
| C15 [consultas locales](../src/spica/adquisicion/consultas_locales/consulta.py), [diagnóstico](../src/spica/adquisicion/consultas_locales/diagnostico.py) | ConsultorLocalCSV y diagnosticar_csv; CSV/perfil/consulta → ObservacionLocal e informe | B en perfil SENAMHI; 51 tests, lector compartido; no consulta institucional |
| C16 [perfilado](../src/spica/perfilado/meteorologico.py), [_indice](../src/spica/perfilado/_indice.py) | perfilar_csv e interpretar_numero; flujo local → perfil representacional e índice temporal | A; 48 tests, perfiles TEMP/HR/PP; no análisis climático |
| C17 [inspección ArcGIS](../src/spica/adquisicion/inspeccion_arcgis/inspector.py), [ensayo](../src/spica/adquisicion/inspeccion_arcgis/ensayo.py) | inspeccionar_metadatos; EnsayoMetadatosArcGIS.consultar_servicio/consultar_capa → IntentoMetadatos | C; 44+34+25 tests; capacidad HTTP de metadatos, no adquisición de entidades |
| C18 [vectorial](../src/spica/adquisicion/vectorial/coordinador.py), [validador](../src/spica/adquisicion/vectorial/validador.py), [piloto](../src/spica/adquisicion/piloto_arcgis/simulador.py) | coordinar/validar_featureset y SimuladorEnsayo.ejecutar; RespuestaSintetica → recibos/completitud | C; 49+59+21 vectoriales, 28+10 piloto/evidencia; transporte exclusivamente sintético |
| C19 [interoperabilidad](../src/spica/interoperabilidad/modelos.py), [adaptadores](../src/spica/interoperabilidad/adaptadores.py), [operaciones](../src/spica/interoperabilidad/operaciones.py) | adaptar_catalogo/meteorologia/vectorial, evaluar_aptitud/evaluar_operacion; snapshots → aptitud/restricciones | C; 16+41+19+13 tests; no asociación efectiva GIS/temporal |
| C20 [metadatos documentales](../src/spica/metadatos_documentales/modelos.py), [evaluación](../src/spica/metadatos_documentales/evaluacion.py), [cotejador](../herramientas/vinculacion_documental.py) | localizar/evaluar_uso y CotejadorDocumental.cotejar; afirmaciones/control previo → diagnóstico/cotejo literal | C; 37 núcleo y 32 vinculación; salidas sin autorización |
| C21 [QA0](../src/spica/calidad/motor.py), [reglas](../src/spica/calidad/reglas.py), [restricciones](../src/spica/calidad/restricciones.py) | EvaluadorNivel0/evaluar_registro/restricciones_resultado; registros/configuración → ResultadoQA/InformeQA/anotaciones | C con integración local; 53 Nivel0, 8 piloto y 12 contratos 85-B |
| C22 [exportación](../src/spica/calidad/exportacion.py), [consumo](../src/spica/calidad/consumo.py) | exportar_resultado_json/consumir_exportaciones; ResultadoQA+contexto → JSON 0.1.0 → InformeConsumoQA | C con ida/vuelta probada; 25 y 33 tests |
| C23 [conciliación](../src/spica/calidad/conciliacion_lotes.py) | conciliar_lotes(tuple[LoteQA]) → InformeConciliacionQA; revalida documentos en memoria | C; 25 tests y piloto histórico 85-E; no fusión/persistencia |
| C24 [modelos científicos](../src/spica/calidad/modelos_cientificos.py), [catálogo](../src/spica/calidad/catalogo_cientifico.py), [aplicabilidad](../src/spica/calidad/aplicabilidad/verificador.py), [sintéticos](../src/spica/calidad/experimental/limites.py) | Registro/revisión de reglas, verificar_aplicabilidad, evaluar_limites_sinteticos; contratos documentales o fixtures → diagnósticos | C; 46 reglas, 7 expediente, 63 aplicabilidad, 3 confianza y 40 sintéticos; no se ejecutan ahora |
| C25 [main.py](../main.py) y capacidades futuras | main solo imprime inicio. Orquestación global, derivados científicos, UI, GIS operativo e IA híbrida no implementados | D para entrada mínima; E para diseño futuro del encargo; F para especificación global no recuperada |

Los recuentos por componente permiten localizar evidencia, **no deben sumarse**:
las pruebas de integración/regresión aparecen en más de una responsabilidad.
Los 39 tests de regresiones altas y los 11 de integración local PNDA complementan
los anteriores. El total estático único sigue siendo 1709 en 52 archivos.

## 4. Arquitectura de adquisición, persistencia y ejecución

Hay integración de bytes y conservación física, no un SUADC multiinstitucional
automatizado. C09 usa C02/C10 y puede registrar metadatos C07; el CSV y DOCX
históricos se adquirieron mediante procedimientos expresamente autorizados del
adaptador común, **no mediante una ampliación implícita del método adquirir XLSX**.
No existen conectores ANA/OEFA/INGEMMET de entidades. C17 sabe pedir metadatos;
C18 no acepta un cliente de red. El /query de INGEMMET sigue bloqueado.

El camino HTTP→staging→RAW→recuperación→inspección se encuentra en C10 y tiene
pruebas físicas con MockTransport. C11 reutiliza RAW para entrega local y registra
MANUAL. C08 prepara planes a partir de evidencia catalogada y C12 recomienda
reutilización/readquisición: **ninguno invoca al transporte como consecuencia de
PREPARADA, RECOMENDAR_NUEVA o una capacidad VERIFICADA**.

RAW conserva un archivo por contenido SHA-256, pero un activo distinto por
incorporación; adquisiciones idénticas no desaparecen. Proyecto y objeto tienen
identidad independiente de ruta/hash. PREPARADA→VERIFICADA→INCORPORADA registra
fases técnicas; FALLIDA/INCONSISTENTE conservan fallos. VERIFICADA aún no es
publicación definitiva. Incorporar y recuperar releen bytes, tamaño y SHA; consultar
metadatos no los relee. Recuperar/verificar/diagnosticar pueden escribir eventos
SQLite: **no son API genérica de lectura inocua**.

La publicación mediante enlace duro es exclusiva y evita reemplazar un contenido
existente; se compara físicamente antes de compartirlo. No hay inmutabilidad
impuesta por el sistema operativo, transacción atómica archivo+SQLite ni garantía
frente a un escritor hostil del mismo usuario. Una interrupción puede dejar
residuos/fases pendientes que diagnosticar detecta sin repararlos automáticamente.
No existe respaldo/restauración general ensayado ni recuperación automática de
operaciones globales. synchronous=FULL y fsync del archivo no prueban durabilidad
de todo el árbol tras pérdida de energía; Windows carece de fsync portable de
directorio en esta implementación.

ConfiguracionRAW deriva su ubicación de Path.home(), protege código/Git/rutas,
reconoce marcador e intención incompleta y sondea escritura/enlaces al abrir.
Inspección RAW reconoce esquemas reales v1/v2; WAL necesita copia privada y
presupuesto explícito. Solo un catálogo RAW **nuevo y vacío** evoluciona a v2 al
crearse; abrir uno existente no lo migra. CatalogoCientifico es otra base y versión:
puede crear su esquema cuando recibe una base vacía y requiere directorio de
confianza. No confundir ese constructor con el reconocimiento estricto RAW.
No se invocó ninguno sobre datos operativos durante este paso.

Los estados de tareas son locales: HTTP tiene historial de la última operación,
reintentos y cancelación cooperativa; CSV/QA tienen recorrido y motivo de cierre;
RAW registra transiciones persistentes. Falta identidad/estado global de una tarea,
propagación común de cancelación/plazo, resultado de flujo y política de recuperación.
No hay scheduler, cola, proceso distribuido o ejecutor científico escondido en main.
El próximo paso puede componer funciones secuencialmente sin construir todo eso.

## 5. Metadatos, ciencia y compatibilidad ambiental

| Concepto parecido | Diferencia que debe conservarse |
|---|---|
| EvidenciaDocumental de catálogo / de aplicabilidad | La primera asocia recurso/publicación/licencia/capacidad; la segunda clasifica referencia/naturaleza/vigencia y pendientes de una regla. No son intercambiables |
| IdentidadRecurso de readquisición / interoperabilidad / vectorial | Readquisición incluye proyecto/objeto y política de uso; interoperabilidad identifica fuente/producto/recurso/localizador; vectorial agrega servicio/capa. Requieren correspondencia explícita, no igualdad por nombre de clase |
| Revisión SQLite / versión institucional / versión de regla / versión de código | Son ejes diferentes; ninguno rellena el desconocido de otro. No ordenar ediciones por timestamp técnico |
| Hash RAW / huella JSON / huella de consulta | Bytes persistidos comprobados / representación declarativa canónica / parámetros de consulta. Ninguno autentica al emisor o prueba ciencia |
| Integridad / inspección / cotejo / correspondencia editorial | Bytes coherentes / estructura admitida / literal localizado / pertenencia de ediciones. La cadena no implica automáticamente el siguiente eslabón |
| Licencia mencionada / derecho de uso / autorización operativa | Declaración documental / revisión aplicable al uso / decisión independiente para ejecutar. No hay promoción silenciosa |

C19 admite marcos espaciales, temporales e identidades genéricos; conserva CRS por
geometría/extensión/origen, fechas civiles o instantes conocidos, incertidumbre y
contradicciones. APTO_ESTRUCTURALMENTE prepara condiciones documentales; no
intersecta geometrías, localiza horas, transforma CRS o verifica estaciones.
C20 conserva afirmaciones, nulo/ausencia/valor, localizadores y restricciones sin
depender de PNDA. Su tipado diferido consulta clases ya cargadas en sys.modules;
no es un cargador de código ni una frontera contra un intérprete malicioso.

La entrada general C01/C07/RAW es multiformato y puede sostener meteorología,
hidrología, hidrogeoquímica, calidad del agua, geología y suelos. **Los lectores
de observaciones y QA0 actuales no son universales**: C15 exige 16 columnas SENAMHI,
C21 adapta ese encabezado y ConfiguracionQA restringe TEMP/HR/PP; el perfilador y
adaptar_meteorologia están especializados. Nuevas disciplinas necesitan adaptadores
con pruebas y semántica propia, no columnas SENAMHI ficticias. Raster puede
representarse documentalmente, pero no tiene evaluador espacial implementado.

Existen descriptores de unidad, medición, frecuencia, método e incertidumbre en
catálogo/reglas/afirmaciones; **no existe un contrato transversal de observación
científica y conversión de unidades validada**. Una cadena como unidad no acredita
dimensión física, agregado, instrumento o ventana. Antes de un método concreto
se debe reutilizar esos contratos y completar solamente su frontera faltante.
No se debe crear preventivamente un diccionario universal ni fusionar modelos.

Las [29 brechas PNDA](brechas_reconciliadas_pnda_paso84i.md) mantienen sus IDs y
estados: **2 resueltas documentalmente, 17 parciales, 8 pendientes, 2 contradicciones**;
27 abiertas. Se leyeron sus informes, no originales. No se reconstruyó HORA/UBIGEO,
convirtió PP, activó Nivel 1 o infirió contaminación, errores instrumentales o clima.

## 6. QA/QC, exportación y procedencia

Las 22 reglas de C21 existen: 1 EST, 4 VAL, 4 TMP, 5 ID y 8 PROV. Son condiciones
estructurales/documentales, no límites meteorológicos. Con tres variables producen
18 + 4×3 = 30 resultados por fila: las 744 filas históricas explican **22320
resultados**, no 22320 observaciones. El piloto 85 selecciona siete definiciones:
13 entradas en 12 escenarios × (4 + 3×3) = **169 resultados**.

El 85-E documenta 119 satisfechos, 3 alertas, 2 problemas, 29 no evaluados y
16 incompletos; 169 anotaciones informativas y 566 bloqueantes por lote. Se
inspeccionaron las pruebas que conservan esos conteos y la ida/vuelta de documentos.
restricciones_resultado no forma parte de asdict(ResultadoQA): la exportación
oficial las calcula e incorpora. El consumidor exige igualdad con esa política y
rechaza el lote completo si faltan o se adulteran; la conciliación revalida cada
informe/documento, conserva los dos lotes y no deduplica conflictos.

QA y regla tienen versión 1.0.0, emisor Nivel0 1.0.1, política de restricciones
1.0.0, JSON/consumo/conciliación 0.1.0. El consumidor admite un perfil más estrecho
que el exportador, como ya documentó 85-E; no existe negociación/migración de
versiones ni un formato de exportación científica general. La coincidencia de
lotes usa contexto y documento completo; evaluaciones independientes sin mapa
externo siguen NO_COMPARABLE aunque coincidan métricas o valores.

C24 ya contiene registro de revisiones de reglas, control de estado y verificador
documental de aplicabilidad; no debe duplicarse. Hay un evaluador separado de
límites **exclusivamente sintéticos**, que no consume los contratos de observación
real o habilitación del catálogo. No se ejecutó aquí. APROBADA, VERIFICADO,
COMPROBACION_SATISFECHA, COINCIDE y JSON válido no se convierten en permisos.
No hay un puente automático del cotejador documental a aprobación o ejecución QA.

## 7. Fronteras de confianza y hallazgos

Se considera confiable el código/intérprete y el responsable de raíces, orígenes,
controles y políticas. Se consideran no confiables red/cuerpos, archivos/documentos,
metadatos aportados y JSON recibido. frozen, SHA y tipos exactos aportan controles
cooperativos; no aíslan código Python hostil o un usuario que sustituye archivos.
Los filtros de secretos son conservadores, no detectores completos. No registrar
automáticamente cuerpos, URLs parametrizadas, objetos request, trazas o literales
científicos. SQLite/archivos no están cifrados por estos componentes.

P0 bloquea una integración que amenaza integridad/validez; P1 completa su frontera;
P2 mejora operación/mantenibilidad; P3 corresponde a hitos posteriores. La gravedad
no es una probabilidad medida. **No se demostró un defecto crítico nuevo en código
estable** mediante esta revisión estática. Las condiciones P0 siguientes son
bloqueos de uso conocidos, no bugs reproducidos ahora ni motivo para reescribir.

| ID / prioridad / gravedad | Evidencia y consecuencia | Corrección o condición exigida |
|---|---|---|
| H01 — P0 condicional, crítica para ciencia institucional | 27 brechas abiertas; autenticidad, aplicabilidad y derechos no inferibles de SHA/JSON; barreras vigentes C19/C20/C24 | Mantener bloqueados usos sin evidencia/permiso. Determinar requisitos del método elegido; no exigir resolver 29 para un ensayo sintético ni promover declaraciones |
| H02 — P1, importante | C08.ejecutable=False; C12.autoriza_red=False; estados locales sin contrato de ejecución común | Definir alcance autorizado, identidad de ejecución, límites/cancelación y resultado por fase; composición secuencial mínima, no orquestador general |
| H03 — P1, importante | Hay dos cadenas integradas pero no una prueba común que una adquisición sintética, snapshot de procedencia, lectura física y el ciclo completo C21–C23 | Añadir prueba vertical con componentes existentes y trazas explícitas; no inferir integración por imports o firmas compatibles |
| H04 — P1, importante | C02 permite HTTP autorizado y verificar_tls=False para get; C03/C09/C10 exigen flag TLS, que no convierte HTTP en HTTPS. Origen autorizado lo decide el llamador | Flujo con exigencia TLS debe exigir también esquema HTTPS y política revisada antes de E/S. No duplicar el cliente ni cambiar política genérica sin necesidad aprobada; proteger registros y raíces privadas |
| H05 — P1, importante por disciplina | C15/C21 acoplados a 16 campos y TEMP/HR/PP; contratos de unidad/metrología dispersos y declarativos | Adaptador/perfil y aplicabilidad explícitos para el próximo método. No universalizar por renombrar campos ni convertir valores implícitamente |
| H06 — P1 antes de persistir derivados, importante | RAW conserva originales y evidencia; ResultadoCientifico es declarativo; no hay almacén/contrato de linaje duradero de transformaciones ni exportación científica | Definir origen/ejecución/versión/parámetros/restricciones y publicación separada de derivados. Primer ensayo puede ser en memoria sin nuevo almacenamiento |
| H07 — P2, importante al crecer | Lecturas/hash repetidos, catálogos/listados completos, conciliación revalida y materializa lotes, sin presupuesto global de tiempo/RAM/disco | Medir y fijar alcance; índices/paginación/cancelación por fases solo con evidencia de necesidad. No quitar relecturas de integridad para optimizar |
| H08 — P2 en uso secuencial; P0 si se exige concurrencia hostil/durabilidad fuerte | Ciclos diferidos, imports privados, dos SQLite y archivos sin transacción global; locks/copia de seguridad/restauración generales ausentes | Mantener un escritor privado secuencial y revisión manual de incertidumbre. Aprobar respaldo/recuperación y revisar dependencia antes de otro modelo |
| H09 — P3, menor para próximo hito | main imprime inicio; UI, GIS operativo, IA híbrida y distribución de producto no implementados | Desarrollar después con puertos opcionales; ninguna IA puede producir evidencia o permiso por sí sola |
| H10 — P1 documental, importante | SRS/arquitectura aprobada Etapa 1 no localizadas; informes y commits no acreditan aprobación formal | Recuperar referencia aprobada o aceptar explícitamente el alcance mínimo trazado R01–R12; conservar decisiones, no inventar una SRS retrospectiva |

P2 adicionales: empaquetado reproducible (sin pyproject/instalación de biblioteca
en el árbol), imports desde herramientas/checkout, pruebas que importan helpers
privados y otros tests, ausencia de CI/medición de cobertura en los archivos
versionados inspeccionados. No equivalen a fallos funcionales actuales ni justifican
instalar herramientas durante esta auditoría. El mapa de ciclos y acoplamientos
concretos está en la matriz, con su límite de análisis.

## 8. Equipos modestos, offline e IA futura

Streaming a disco y lectores progresivos evitan cargar CSV científicos completos;
QA itera resultados. El perfilador utiliza un índice SQLite temporal con cuotas.
Inspectores JSON/OOXML materializan documentos/inventarios **acotados**, no procesan
cualquier tamaño con RAM constante. Conciliación acepta dos a ocho lotes y por
defecto 256 documentos/4 MiB por lote, además de copias/árboles de validación;
bytes de entrada no son consumo real de RAM. HTTP get conserva 1 MiB por defecto,
configurable; streaming usa límite propio, bloques 64 KiB por defecto y tope 1 MiB.

Timeout HTTP es por fase/actividad, no plazo total; cancelación es cooperativa y
no atraviesa toda copia RAW/inspección de inmediato. Reintento de transferencia
reinicia desde cero, no usa Range ni checkpoint global. Procesamiento diferido
puede hacerse secuencialmente con el material disponible; no existe una cola
persistente que reanude tareas tras apagado. Las sondas de espacio/permisos no
reservan recursos. Debe dimensionarse el pico de staging + copia RAW + temporales,
sin confundir deduplicación posterior con ahorro durante la transferencia.

Optimización propuesta: medir tiempo, RAM máxima y bytes temporales por fase en
fixtures representativas; paginar historial si el volumen lo exige; limitar lotes
de exportación manteniendo contexto/identidad; compartir políticas y cancelación
por composición. No se ejecutó un benchmark ni se eliminó comprobación alguna.

La arquitectura puede recibir IA **por fuera** del núcleo: un futuro adaptador local
y otro API opcional deberían producir recomendaciones trazables y revisables,
con proveedor/modelo/versión/entradas/limitaciones. No hay esos puertos en código
ni evidencia de desempeño en laptops. Las funciones científicas esenciales deben
seguir siendo deterministas y utilizables sin IA, GPU, nube o conexión permanente.
Una recomendación no puede marcar metadatos como verificados, resolver brechas,
aprobar reglas o sustituir decisiones humanas. Riesgos de instrucciones en
documentos y filtración a APIs requieren modelo de amenaza futuro, no un sistema
de certificación implementado preventivamente.

## 9. Dictamen y cierre de esta auditoría

**APTO CON RESTRICCIONES** para revisar el expediente y preparar el PASO 85-G:
contrato mínimo de ejecución estructural y prueba vertical offline que reutilice
las dos cadenas existentes. No se identificó razón técnica demostrada para una
refactorización integral. Falta integración/plataforma, no otro transporte, RAW,
catálogo científico o motor QA0. Los módulos científicos quedan pendientes de
condiciones específicas de la hoja de ruta y de una nueva instrucción.

No se accedió a RAW/CSV/SQLite operativos ni staging, tampoco para inventarios,
diagnósticos o hashes de comprobación. No se afirma una auditoría física nueva
de recursos mantenidos cerrados ni control de cambios de terceros. Cero conexiones,
GET, descargas, instalaciones, migraciones, cambios científicos, commits o push.
Ninguna función de SPICA se ejecutó. Se preservan contratos, fuentes, pruebas,
documentos históricos, documentos institucionales y estados de las 29 brechas.

La comprobación final y el estado Git de los tres entregables se consignan en la
hoja de ruta. No se avanza automáticamente al PASO 85-G; se espera auditoría.
