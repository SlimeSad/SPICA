# RC12 — Auditoría transversal de arquitectura de SPICA

Fecha: **2026-11-20**, America/Lima. Rama `feature/suadc-http`, base/HEAD
`128ada9a8f1f75c926cb4372e519197c94777029`. **Auditoría documental**, sin
implementación, importación de SPICA, pruebas funcionales ni acceso operativo.

Documentos asociados:
[33 conexiones](matriz_trazabilidad_conexiones_rc12.md),
[decisión de cierres no QA](decision_evolucion_cierres_noqa_rc12.md) y
[hoja de ruta](hoja_ruta_priorizada_rc12.md).
La arquitectura integral continúa abierta; no se autoriza ciencia ni RC13.

## Estado recuperado, método y límites

`git status` inicial: árbol limpio. RC11 consolidado en HEAD:

```text
128ada9 SPICA: dictamen experimental de dependencia no QA RC11
98094c1 SPICA: conservacion versionada de evidencias tecnicas RC10
424e585 SPICA: admision controlada de evidencias de exportacion RC9
246bbec SPICA: cierre tecnico verificable de exportacion RC8
c1b224e SPICA: integracion de artefactos y coordinacion RC7
```

Se contrastaron las auditorías RC1–RC11, contratos, declaraciones y recorridos
seleccionados del código con pruebas fuente. Se recuperaron la
[auditoría 85-M](auditoria_continuidad_arquitectonica_paso85m.md), su
[matriz IM/M](matriz_diseno_implementacion_paso85m.md), la
[hoja original](hoja_ruta_continuidad_arquitectonica_paso85m.md) y la
[matriz 85-F](matriz_dependencias_integracion_paso85f.md) de la que proceden las M.
Se conservan sus IDs y fechas; no se reescriben estados históricos.

La lectura/AST actual abarca **126 archivos Python de src, nueve herramientas
y 67 archivos test_**, sin errores de sintaxis ni definiciones repetidas en el
mismo ámbito. Se localizaron **2446 métodos test_ con IDs estáticos únicos**.
Ese recuento no ejecuta tests ni demuestra cobertura. La última suite ejecutada
sigue siendo la [de RC11](auditoria_arquitectonica_rc11.md): 2446 aprobadas,
0 fallidas/errores/omitidas, 1009.124 s, **antecedente histórico**. No se repiten
unittest ni pip check al cambiar únicamente documentación.

Se distinguen **E:** inspección estática actual, **H:** ensayo/adquisición histórica
documentados y **P:** propuesta no implementada. La inspección es transversal y
selectiva de contratos/recorridos, no una revisión de cada instrucción ni una
certificación de seguridad. No se comprobaron servicios vivos, archivos privados,
salud actual de RAW ni vigencia de evidencias institucionales.

## Matriz de capacidades: 28 responsabilidades heredadas

IM01–IM28 proceden de 85-M; no son requisitos originales de ERS. Las dos tablas
se unen por ID: conjuntamente registran responsabilidad, subsistema, código,
contrato, prueba/evidencia, implementación, integración, restricciones, riesgo,
dependencias y próxima acción. Un enlace de tests significa fuente inspeccionada,
no una ejecución RC12. Una capacidad sintética no se convierte en institucional.

### Inventario y evidencia concreta

| ID | Responsabilidad / subsistema | Código real y contrato relacionado | Pruebas fuente y evidencia delimitada |
|---|---|---|---|
| IM01 | Identidad de proyecto y contexto / plataforma | [MD](../src/spica/adquisicion/almacenamiento/modelos.py), [contextos RC1](../src/spica/contextos/modelos.py): ProyectoCientifico, ObjetoCientifico, ContextoProyecto | [MD](../tests/test_modelos_md_raw.py), [RC1](../tests/test_contextos_rc1.py); IDs independientes de ruta/hash, contextos y pertenencia E/H |
| IM02 | Acceso, propietario y permisos / seguridad | [configuración RAW](../src/spica/adquisicion/almacenamiento/configuracion.py), [rutas RC5](../src/spica/artefactos/_archivos_rc5.py), ContextoProyecto.autoriza_operacion=False | [configuración](../tests/test_configuracion_raw.py), [RC5](../tests/test_materializacion_rc5.py); controles de rutas/propiedad local, no IAM E/H |
| IM03 | Configuración y estado de operaciones / plataforma | ContextoOperacion, ConfiguracionContexto y [relaciones RC1](../src/spica/contextos/relaciones.py) | [RC1](../tests/test_contextos_rc1.py); versiones, cambios permitidos, parciales y aislamiento; ninguna transición prueba ejecución E/H |
| IM04 | Presupuesto y cancelación / recursos | [LimitesComposicion](../src/spica/coordinacion/modelos.py), [_presupuesto](../src/spica/coordinacion/_presupuesto.py), límites HTTP/QA/RC5/RC6 | [RC3](../tests/test_coordinacion_rc3.py), [reintentos](../tests/test_reintentos_http.py); cuotas y Event locales, no RSS/reserva global E/H |
| IM05 | Dataset/recurso/versión / información | [catálogo](../src/spica/adquisicion/catalogo/modelos.py), ContextoEntrada y [artefactos RC4](../src/spica/artefactos/modelos.py) | [catálogo](../tests/test_catalogo_cientifico.py), [RC4](../tests/test_artefactos_rc4.py); revisión/contexto/contenido distintos, sin inventar dataset universal E/H |
| IM06 | Observación y representación original / información | [ObservacionLocal](../src/spica/adquisicion/consultas_locales/modelos.py), [RegistroQA](../src/spica/calidad/modelos.py), [perfiles RC2](../src/spica/interoperabilidad/perfiles/modelos.py) | [consultas](../tests/test_consultas_locales.py), [RC2](../tests/test_perfiles_informacion_rc2.py); perfiles y correspondencias generales, lector QA especializado SENAMHI E/H |
| IM07 | Unidad, medición y magnitud / metadatos | UnidadPerfil/CampoInformacion, [comparador RC2](../src/spica/interoperabilidad/perfiles/comparador.py), VariableCatalogo | [RC2](../tests/test_perfiles_informacion_rc2.py); comparación literal de unidad/dimensión/tipo/frecuencia con respaldo aportado; sin metrología/conversión E/H |
| IM08 | Referencias temporales/espaciales / interoperabilidad | [temporal](../src/spica/adquisicion/nucleo/temporal.py), [marcos](../src/spica/interoperabilidad/modelos.py), [evaluador](../src/spica/interoperabilidad/evaluador.py) | [tiempo](../tests/test_temporal.py), [aptitud](../tests/test_interoperabilidad_evaluador.py); civil/naive/aware y CRS por ámbito, sin transformar desconocidos E/H |
| IM09 | Evidencia y restricciones documentales / procedencia | [metadatos](../src/spica/metadatos_documentales/modelos.py), [evaluar_uso](../src/spica/metadatos_documentales/evaluacion.py), [cotejador](../herramientas/vinculacion_documental.py) | [metadatos](../tests/test_metadatos_documentales.py), [cotejo](../tests/test_vinculacion_documental.py); referencias/localizadores y contradicciones; no aprobación automática E/H |
| IM10 | GET, streaming, SHA y reintentos / transporte | [HTTP](../src/spica/adquisicion/transportes/http.py), [descargas](../src/spica/adquisicion/transportes/descargas.py), [gestor](../src/spica/adquisicion/transportes/reintentos.py) | [HTTP](../tests/test_transporte_http.py), [streaming](../tests/test_descargas_http.py), [reintentos](../tests/test_reintentos_http.py); MockTransport, límites, errores/TLS, relectura y publicación exclusiva E/H |
| IM11 | Descubrimiento y conector institucional / adquisición | [ConectorSENAMHIPNDA](../src/spica/adquisicion/conectores/senamhi/pnda.py), CatalogoRecursos/AdquisicionPNDA | [conector](../tests/test_conector_senamhi_pnda.py), [expediente](conector_senamhi_pnda.md); producto fijo y adquirir limitado a diccionario XLSX E/H; vigencia externa actual NE |
| IM12 | Ingesta manual y readquisición / adquisición | [IngestorManual](../src/spica/adquisicion/manual/ingesta.py), [motor de decisión](../src/spica/adquisicion/readquisicion/motor.py) | [manual](../tests/test_ingesta_manual.py), [readquisición](../tests/test_readquisicion.py); recibo manual→RAW y recomendación pura sin GET; sin hook común E/H |
| IM13 | Staging, RAW y originales / almacenamiento | [AlmacenRAW](../src/spica/adquisicion/almacenamiento/raw.py), [HTTPRAW](../src/spica/adquisicion/integracion/http_raw.py), DeclaracionRAW/ActivoRAW | [RAW](../tests/test_almacenamiento_raw.py), [integración](../tests/test_integracion_http_raw.py); relectura tamaño/SHA, activos distintos para contenido compartido, estados por fase E/H |
| IM14 | Catálogo y planificación multivariable/multiestación | [persistencia](../src/spica/adquisicion/catalogo/persistencia.py), [planificador](../src/spica/adquisicion/planificacion/planificador.py), [PlanConsulta](../src/spica/adquisicion/planificacion/modelos.py) | [registro](../tests/test_registro_evidencias.py), [plan](../tests/test_planificacion.py); revisiones/transacciones locales y propuestas sin cartesiano; ejecutable=False E/H |
| IM15 | Lectura e inspección estructural / formatos | [CSV](../src/spica/adquisicion/verificacion/csv_streaming.py), [inspector general](../src/spica/adquisicion/verificacion/inspector.py), [DOCX](../src/spica/adquisicion/verificacion/docx/inspector.py) | [CSV](../tests/test_csv_streaming.py), [formatos](../tests/test_verificacion_formatos.py), [DOCX](../tests/test_inspector_docx.py); presupuestos, EOF/alcance y omisiones, sin semántica científica E/H |
| IM16 | QA0 y límites de interpretación / calidad | [motor](../src/spica/calidad/motor.py), [22 reglas](../src/spica/calidad/reglas.py), [restricciones](../src/spica/calidad/restricciones.py) | [QA0](../tests/test_calidad_nivel0.py), [contratos](../tests/test_contratos_qaqc_85b.py); cinco estados de resultado, parciales y multiplicidad por campo conservados E/H |
| IM17 | Preparados y transformaciones no destructivas / procesamiento | [RC4](../src/spica/artefactos/modelos.py), [RC5](../src/spica/artefactos/materializacion.py); [perfilado](../src/spica/perfilado/meteorologico.py) es diagnóstico, no productor general | [RC4](../tests/test_artefactos_rc4.py), [RC5](../tests/test_materializacion_rc5.py); descripciones/bytes sintéticos publicados, sin servicio general de preparación E/H |
| IM18 | Coordinación y evidencia de cierre / operaciones | [RC3](../src/spica/coordinacion/inspeccion.py), [RC7](../src/spica/artefactos/coordinacion.py), [RC8](../src/spica/artefactos/cierre_exportacion.py), [RC11](../src/spica/artefactos/dependencia_exportacion.py) | [RC3](../tests/test_coordinacion_rc3.py), [RC7](../tests/test_integracion_artefactos_rc7.py), [RC11](../tests/test_dependencia_noqa_rc11.py); cierres QA específicos y bloqueo no QA; no ejecutor E/H |
| IM19 | Exportación, consumo y conciliación QA / resultados técnicos | [exportación](../src/spica/calidad/exportacion.py), [consumo](../src/spica/calidad/consumo.py), [lotes](../src/spica/calidad/conciliacion_lotes.py), [RC9](../src/spica/artefactos/admision_exportacion.py) | [JSON](../tests/test_exportacion_qaqc_85c.py), [consumo](../tests/test_consumo_qaqc_85d.py), [lotes](../tests/test_conciliacion_qaqc_85e.py), [RC9](../tests/test_admision_exportacion_rc9.py); perfil 0.1.0, restricciones/versiones, conflictos sin fusión E/H |
| IM20 | Linaje y conservación de evidencias / artefactos | [linaje RC4](../src/spica/artefactos/linaje.py), [RC6](../src/spica/artefactos/conservacion.py), [RC10](../src/spica/artefactos/conservacion_evidencias.py), [85-J](../herramientas/conservacion_linaje_85j.py) | [RC6](../tests/test_conservacion_rc6.py), [RC10](../tests/test_conservacion_evidencias_rc10.py), [J](../tests/test_conservacion_linaje_85j.py); perfiles cerrados y lectores entre procesos E/H |
| IM21 | Resultado científico / análisis futuro | [ResultadoCientifico/EvidenciaEjecucionCientifica](../src/spica/calidad/modelos_cientificos.py) | [modelos/reglas](../tests/test_reglas_cientificas.py); validación de DTO vinculado a RegistroQA y revisión, no productor/almacén científico E |
| IM22 | Respaldo y restauración / conservación | [85-K](../herramientas/respaldo_linaje_85k.py), copiar_de/recuperar_generacion RC6 | [K](../tests/test_respaldo_linaje_85k.py), [RC6](../tests/test_conservacion_rc6.py); copia/SQLite backup del perfil J y traslado TEMP; no backup RAW integral ni otro dominio de fallo E/H |
| IM23 | Custodia independiente y retención / conservación futura | [diseño 85-L](arquitectura_custodia_independiente_paso85l.md), ControlRespaldo85K/ControlGeneracion son argumentos de cotejo | Sin gestor de custodia/retención probado; [amenazas](modelo_amenazas_dominio_fallo_paso85l.md) documenta autoridad/dominio/canal compartidos E/P |
| IM24 | Ciclo transversal de artefactos/catálogos / almacenamiento | [catálogo RAW](../src/spica/adquisicion/almacenamiento/catalogo.py), catálogo científico, RC4–RC6 y HTTPRAW | [configuración](../tests/test_cierre_configuracion_raw.py), [regresiones](../tests/test_regresiones_altas.py), [RC4](../tests/test_artefactos_rc4.py); consistencias locales, sin transacción global entre archivos/SQL/catálogos E/H |
| IM25 | Método, revisión y aplicabilidad científica / calidad documental | [catálogo de reglas](../src/spica/calidad/catalogo_cientifico.py), [verificador](../src/spica/calidad/aplicabilidad/verificador.py), HabilitacionCientifica | [reglas](../tests/test_reglas_cientificas.py), [aplicabilidad](../tests/test_aplicabilidad_cientifica.py); aprobación/revisión aportadas, elegibilidad documental y ejecucion_autorizada=False E/H |
| IM26 | Entrada/salida de métodos científicos / análisis futuro | [evaluador sintético](../src/spica/calidad/experimental/limites.py) solo acepta ObservacionSintetica/ReglaLimitesSintetica | [límites sintéticos](../tests/test_limites_sinteticos.py); prueba aislada, no anfitrión de métodos ni integración de observaciones institucionales E/H |
| IM27 | GIS, interfaz y visualización / aplicación futura | [vectorial offline](../src/spica/adquisicion/vectorial/coordinador.py), [metadatos ArcGIS](../src/spica/adquisicion/inspeccion_arcgis/ensayo.py), [main](../main.py) mínimo | [vectorial](../tests/test_vectorial_coordinacion.py), [ArcGIS](../tests/test_inspeccion_arcgis.py); estructura/simulación, sin GIS operativo/UI; /query no autorizado E/H |
| IM28 | IA opcional, servicios/comercio / aplicación futura | Sin componentes IA/pagos en src; [requirements](../requirements.txt) solo declara HTTPX directamente | Inventario/imports E; no implementación ni ensayo IA/comercio; no condición para funciones deterministas |

### Implementación, integración y trabajo pendiente

Categorías: **I = IMPLEMENTADA Y PROBADA EN SU ALCANCE** (pruebas H, no nuevas);
**P = IMPLEMENTADA PARCIALMENTE**; **C = CONTRATO DECLARATIVO**;
**D = DISEÑADA, NO IMPLEMENTADA**; **N = PENDIENTE**;
**B = BLOQUEADA**; **F = FUERA DEL ALCANCE ACTUAL**.
La clasificación se refiere a la responsabilidad indicada, no a la plataforma
entera. Una categoría I admite ampliaciones pendientes fuera de su alcance.

| ID | Implementación | Integración actual | Restricción / riesgo | Dependencias pertinentes | Próxima acción |
|---|---|---|---|---|---|
| IM01 | I | Contextos RC1→RC2/RC3/RC4 y RAW | Identidad declarada local; no gestor de proyectos global | MD y contexto canónico | Preservar IDs/versiones, no otro modelo MD |
| IM02 | P | Controles locales; permisos solo declarativos | Proceso confiable; sin IAM/DACL auditada | IM01/13/24 | Exigir alcance explícito por efecto; IAM solo si cambia el modelo |
| IM03 | P | Declaración común, sin ejecución general | Estado no prueba ejecución ni permiso | IM01/04/18 | Separar precondición, llamada real y cierre |
| IM04 | P | Cotas de descriptores y QA declaradas compuestas; efectos independientes | Sin RSS/reserva/plazo forzoso conjunto | Perfil/operación y SO | Medir caso pertinente; mantener agotamiento parcial |
| IM05 | I | Catálogo→plan/perfil/contexto/artefacto | Metadatos no acreditan disponibilidad ni contenido actual | IM01/09/14 | Reusar snapshots/versiones y contenido_id sin confundir SHA |
| IM06 | P | RC2 general; lectura/QA0 de perfil SENAMHI | Sin observación de carga útil universal ni adaptador científico revisado | IM05/07/08/15 | Perfil y correspondencias del futuro caso, sin normalización implícita |
| IM07 | I | Comparación estructural/documental RC2 | Literal respaldado no prueba metrología | IM05/09/25 | Revisar unidad/medición/frecuencia para cada método |
| IM08 | I | Marcos y aptitud documental | Zona desconocida/CRS por ámbito; no asociación efectiva | Procedencia y evidencia pertinentes | Mantener desconocidos y transformaciones deshabilitadas |
| IM09 | P | Cotejo→afirmaciones, sin puente M26 revisado | Coincidencia/integridad no aprueban contenido o licencia | Documentos/control/revisión confiables | Diseñar vínculo explícito para el uso seleccionado |
| IM10 | I | Transporte común→streaming/reintentos→HTTPRAW | HTTP/get sin TLS configurables; perfil estricto debe imponerse antes del efecto | Origen/permiso/límite/destino | No duplicar cliente; revisar perfil HTTPS del flujo futuro |
| IM11 | P | PNDA→HTTP/catálogo/RAW limitado a XLSX | Parser/producto fijos; autenticación/filtros remotos no implementados | IM09/10/13 | No ampliar por antecedentes CSV/DOCX; nueva autorización si se solicita |
| IM12 | P | Manual→RAW; decisión sin hook M16 | Recomendar no descarga ni acredita vigencia | Antecedente, restricción y archivo autorizados | Integrar política previa solo después de contrato de efectos |
| IM13 | I | HTTP/manual→RAW y formato separado | Privado/secuencial; no atomicidad global ni backup integral | IM02/10/15/24 | Preservar originales/adquisiciones; operación real exige procedimiento propio |
| IM14 | P | Metadatos persistidos y plan declarativo; M03 P | PREPARADA no ejecuta; ausencia de evidencia no es ausencia de datos | IM05/09/11 | Mantener propuestas; no inventar traducciones a HTTP |
| IM15 | I | Lectores/inspectores→consulta/QA/documental | Muestras/omisiones explícitas, perfiles cerrados | Archivo autorizado, límites e integridad pertinente | Conservar alcance/EOF y lecturas por perfil |
| IM16 | I | CSV/local→QA0→JSON/restricciones | 22 reglas estructurales, no calidad ambiental | IM06/09/15/19 | Mantener cardinalidad por regla/campo y original literal |
| IM17 | P | Descriptor/linaje/publicación sintética disponibles | Sin servicio de transformaciones/derivado científico | IM01/05/18/20 | Definir salida del caso antes de cualquier preparación real |
| IM18 | P | RC3/RC7 declarativos; cierre QA específico; arista no QA B | Sin cierre no QA admitido, scheduler o permiso | IM01/03/04/09/19/20 | Siguiente bloque propuesto: precondición no QA acotada |
| IM19 | I | Exportación→consumo→conciliación, RC8/RC9 específicos | Perfil QA, testigos cooperativos; no formato científico universal | QA/contexto/identidades/restricciones | Reusar interfaces; no asdict ni nuevo parser |
| IM20 | I | RC4→RC5→RC6 y portador RC10; J perfil propio | Recupera solo contenido incluido; testigos no persistidos | IM01/05/17/19, control esperado | Versionar solo ante nueva necesidad; historia nunca actual por defecto |
| IM21 | C | DTO científico, sin productor/flujo/codec | Acoplado a RegistroQA; no resultado ambiental demostrado | IM06/07/09/17/25/26 | Contrato metodológico y salida específica antes de M32 |
| IM22 | P | Respaldo/restauración J/K y copia RC6 en TEMP | No RAW completo, custodia independiente o portabilidad entre equipos acreditada | IM20/23/24 | No ampliar garantías sin ensayo y alcance de conservación aprobados |
| IM23 | D | Control aportado, sin canal/autoridad independientes | Datos únicos y pérdida de control no cubiertos | IM20/22 y política de retención | Resolver antes de prometer custodia operativa o copia única |
| IM24 | P | Estados/consistencia locales, sin coordinador global | Publicación FS y SQL no son una transacción única | IM13/17/18/20/22 | Delimitar cierre/diagnóstico; no otra DB por defecto |
| IM25 | C | Catálogo/verificador ejecutan diagnósticos documentales | Aprobación/elegibilidad no autorizan ciencia; M26 P | Evidencia revisada y contexto del método | Revisar expediente pertinente; sin umbrales activos |
| IM26 | N | Solo evaluador aislado de fixtures | No anfitrión científico, contrato de carga útil o efecto aprobado | IM06/07/17/21/25 | Diseñar tras gates de preparación; no elegir algoritmo ahora |
| IM27 | F | Metadatos/vector offline disponibles; GIS/UI operativos excluidos | /query bloqueado, equivalencia/licencias pendientes | Autorización/producto/perfil y caso GIS | Posponer efectos, interfaz y ciencia GIS |
| IM28 | F | Sin integración IA/comercio | No introducir dependencia de nube/GPU/pagos | Necesidad futura y revisión de privacidad | Posponer; mantener ciencia determinista independiente |

Recuento de estas 28 responsabilidades: **10 I, 12 P, dos C, una D, una N y
dos F**. La arista no QA bloqueada está dentro de IM18; no se añade como otra
responsabilidad para inflar el inventario. Son categorías de alcance, no un
porcentaje de finalización ni de conformidad científica.

## Adquisición, RAW y catálogos

Los contratos [del núcleo](../src/spica/adquisicion/nucleo/modelos.py) conservan
fuentes e identificadores originales, múltiples estaciones/variables, estaciones
opcionales y formatos abiertos. SolicitudAdquisicion exige intervalo: un recurso
documental estático usa su vía explícita, sin inventar un período.

El transporte usa orígenes permitidos, proxies/redirecciones desactivados,
timeouts y respuestas pequeñas de 1 MiB por defecto. Streaming procesa bloques,
controla bytes reales y Content-Length, rechaza 206/compresión y publica mediante
enlace exclusivo después de fsync/relectura SHA. No es confirmación RAW ni ciencia.
Reintentos solo GET, por defecto uno, hasta 100 configurables; retroceso/jitter,
Retry-After y Event. TLS/401/403/404 no se reintentan. No hay Range, descarga
reanudable ni plazo total de operación.

RAW conserva adquisiciones como activos distintos aunque compartan bytes, y
comprueba contenido existente antes de deduplicar. PREPARADA→VERIFICADA→INCORPORADA
se separa de anomalías. Errores de disponibilidad no se convierten sin evidencia
en corrupción. `recuperar`, `verificar` y `diagnosticar` pueden registrar eventos;
`ConfiguracionRAW.abrir` hace sondas y `validar` con WAL puede copiar DB/WAL a TEMP.
**No se llamó a ninguna de esas operaciones en RC12.**

La configuración deriva de Path.home(), separa RAW/staging del código y rechaza
repositorios/enlaces/estados inciertos; no migra automáticamente. Hay límites de
espacio/inspección, que no reservan recursos. [Esquemas RAW v1/v2](../src/spica/adquisicion/almacenamiento/inspeccion.py),
catálogo científico v1 y extensión experimental 85001 tienen alcances distintos.
Las transacciones locales y publicación exclusiva no forman atomicidad global.

PNDA es un conector específico de descubrimiento HTML/dcat y adquisición XLSX.
Las adquisiciones CSV/DOCX históricas por procedimiento no amplían `adquirir`.
No se comprueban ahora URL, licencia, disponibilidad o estaciones/variables
remotas. Otros conectores institucionales y ArcGIS de entidades no están
implementados como adquisición operativa autorizada. M03/M16 siguen pendientes.

## Persistencia y recuperación: qué sobrevive

| Etapa | Contenido incluido / recuperable | Contenido externo y garantías ausentes |
|---|---|---|
| 85-J | Informe85G, traza H, referencia y metadatos admitidos por codec fijo; índice experimental 85001 y archivos releídos | No original RAW del piloto, contexto arbitrario o checkpoint. Validación conserva condiciones de TEMP del perfil histórico |
| 85-K | Respaldo de una ejecución J, snapshot SQLite mediante API backup y archivos; restauración comprobada entre procesos del mismo perfil | No respaldo RAW global, nuevo equipo/cuenta o dominio de fallo independiente probado |
| RC4 | Identidades, revisiones, estados lógicos, producción y restricciones en memoria | No almacén, bytes o acreditación de ejecución por tener linaje |
| RC5 | Publicación/relectura real de bytes sintéticos y referencia controlada TEMP | No durable por defecto, no ejecuta el productor, no confirma RAW |
| RC6 | Generación cerrada de 1–16 artefactos descriptivos: metadatos tipados más bytes explícitamente incluidos; recuperación desde raíz actual, traslado y otro proceso en fixtures | Cierres QA fuera de su codec; externos vuelven como NO_DISPONIBLE, sin seguir rutas históricas RC5 |
| RC10 | Portador documental sobre RC5/RC6 con contratos RC8/RC9 públicos, resultado/JSON pequeños y hechos históricos; verificación física actual del portador | Testigos privados omitidos; entrada externa/original y archivo JSON separado no recuperados automáticamente; no nueva captura/admisión |

Estados históricos fallidos/parciales se reconstruyen como tales. Un expediente
de fallo puede estar íntegro. La relectura detecta cambios observados; no acredita
autenticidad frente a sustitución coordinada de datos y control. No hay custodia
independiente, retención/GC operativo, transacción global ni garantía eléctrica.
RC6 mejora el desacoplamiento de la raíz histórica para su perfil; no migra J/K
ni elimina sus restricciones. La [decisión específica](decision_evolucion_cierres_noqa_rc12.md)
detalla qué tendría que evolucionar; ningún formato cambia aquí.

## Calidad, restricciones y seguridad científica

QA0 conserva valores originales y cinco estados de resultado; InformeQA separa
recorrido completo de evaluaciones incompletas y presupuesto/cancelación. Sus 22
reglas pueden emitir varios resultados por campos: no equivalen a 22 observaciones
ni a 22 resultados por fila. El cierre QA coteja la cardinalidad real, no un
porcentaje obtenido de la cantidad de tests.
Las versiones tienen responsabilidades distintas: contrato/reglas QA0 **1.0.0**,
emisión del evaluador **1.0.1**, política de restricciones **1.0.0** y JSON QA
**0.1.0**. No se tratan como una sola versión institucional o científica.

Exportación/consumo oficiales preservan restricciones 1.0.0; asdict del resultado
no las incorpora por sí solo. Conciliación conserva conflictos/lotes y no fusiona
ejecuciones por hash. RC1–RC11 propagan restricciones y separan declaraciones,
comprobaciones y permisos. El nuevo dictamen RC11 no elimina los diagnósticos
RC3/RC4: su APTO de correspondencias tiene un alcance distinto del cierre global.

No reconstruir HORA/UBIGEO, deducir códigos físicos de nombres, convertir mm/mm/h
o una zona desconocida. Integridad/estructura no acreditan plausibilidad,
instrumentación, ausencia de contaminación ni anomalía ambiental. El catálogo
científico y su verificador solo expresan revisión/aplicabilidad aportadas;
HabilitacionCientifica.ejecucion_autorizada=False. El evaluador de límites es
exclusivo de fixtures sintéticas. M26/M32 no se cierran mediante esas barreras.

## Hallazgos y riesgos actuales

No se reprodujo mediante ejecución un defecto crítico nuevo: RC12 es estático.
Los siguientes límites y bloqueos sí tienen evidencia de código; no se convierten
en una afirmación de ausencia total de defectos o ataques.

| ID RC12 | Gravedad condicionada / evidencia | Consecuencia y corrección o decisión necesaria |
|---|---|---|
| AT01 | Bloqueante para admisión no QA: RC3.cierre_qa y RC7._dependencia no aceptan RC8 | Mantener bloqueo. Aprobar una política específica/versionada y su prueba antes de extender la admisión |
| AT02 | Alta para ciencia: evaluar_uso, aplicabilidad y perfiles no proporcionan puente M26 revisado | No promover coincidencia documental a aprobación; vínculo por producto/uso/evidencia pertinente |
| AT03 | Alta para salida científica: ResultadoCientifico es DTO, no flujo/codec de M32 | Definir método/entrada/resultado/linaje y formato del caso antes de producir/conservar ciencia |
| AT04 | Alta para datos únicos/uso operativo: FS+SQL/catálogos sin atomicidad global; controles/custodia bajo autoridad local | No prometer recuperación integral o resistencia eléctrica; inventario, control protegido y ensayo de respaldo del alcance pertinente antes de ese uso |
| AT05 | Media antes de efectos externos: get genérico admite HTTP/verificar_tls=False; TLS activo no cifra una URL HTTP | Perfil HTTPS/TLS/origen/permiso explícito del flujo futuro; no cambiar el cliente genérico por esta auditoría |
| AT06 | Media: cotas de bytes/nodos/registros y Event no son reservas RSS/disco ni timeout forzoso global | Presupuesto del caso y medición reproducible antes de ampliar escala; no prometer memoria constante para informes/JSON |
| AT07 | Media de mantenimiento: helpers privados y cotejos de cierre entre capas; códigos nativos proyectados en RC11 | Evolución mínima con regresión/defaults preservados; no framework ni lógica paralela de admisión |
| AT08 | Bloqueante para conformidad formal: ERS/actas/H0/FUT/G0 no localizadas | Solicitar fuentes cuando se someta un hito a aprobación o ratificar alcance local; no reconstruir requisitos inventados |
| AT09 | Baja documental: guía RAW dice «No se ha inicializado el almacén operativo permanente», mientras hay antecedentes de uso | Conservar la frase como antecedente fechado y preparar una guía vigente en alcance futuro; no sondear RAW para resolverla aquí |
| AT10 | Alta si se exige autenticidad independiente: DTO/testigos cooperativos y controles sin firma | Mantener pendiente ese uso; una captura/JSON coherente o física correcta no satisface autenticidad/permiso |

AT09 conserva el hallazgo AM12 de 85-M: la [guía](almacenamiento_raw.md) y los
[antecedentes locales](integracion_local_pnda_paso84c.md) no permiten emitir un
diagnóstico actual del almacén. No es evidencia de pérdida, corrupción o ausencia.
El saneamiento de códigos públicos no es una política universal de confidencialidad
de todos los DTO/tracebacks aportados; al publicar un flujo se revisará su superficie
de errores sin registrar contenido, consultas, credenciales o rutas innecesarias.

## Dependencias, reutilización y posibles duplicaciones

El análisis AST actual de imports explícitos encuentra **482 aristas internas,
456 inmediatas**, sin componentes cíclicos en ese subgrafo inmediato. El grafo
completo conserva dos grupos con imports diferidos/tipos: HTTP↔descargas/reintentos,
y almacenamiento/configuración/RAW↔catálogo/documental/evidencias/persistencia↔
integración/manual. No hay imports explícitos src→herramientas/tests y el único
paquete externo directo localizado fuera de stdlib es HTTPX, coherente con
requirements. El análisis no modela todos los imports implícitos de paquetes,
sys.modules o recorridos dinámicos: no certifica todos los órdenes de carga.

No se detectaron definiciones repetidas en el mismo ámbito; eso no demuestra
ausencia de duplicación semántica. J/K y RC6 son perfiles diferentes, no dos
almacenes operativos intercambiables; RC10 reutiliza RC6, no añade otro.
Los hashes/relecturas de transferencia, incorporación y publicación protegen
fronteras/propiedades diferentes. No eliminarlos por semejanza superficial.

Riesgos de duplicación futuros: copiar el DAG RC3 en un adaptador, añadir otra
decisión de admisión en RC7, escribir otro parser JSON, duplicar RAW como almacén
de derivados o crear un DTO de observación que oculte el original. Reutilizar
fronteras actuales y extraer helpers solo por una necesidad demostrada.

## Requisitos disponibles y límites de homologación

| Fuente | Disponibilidad actual y consecuencia |
|---|---|
| ERS-SPICA y revisiones formales | No localizadas como documentos fuente en rutas registradas/históricas consultadas; no se evalúa cumplimiento formal |
| Actas B1/DA1, H0/FUT/G0 y reservas | No localizadas; menciones en auditorías no son actas ni aprobación. Un commit tampoco lo es |
| Protocolo original de desarrollo | No localizado como fuente formal; se aplican las instrucciones explícitas del encargo actual |
| MD-01/02/03 y contratos locales | Campos y relaciones contrastables en modelos/pruebas; no sustituyen la ERS global |
| Matrices 85-F/85-M y auditorías RC | Disponibles y contrastadas; son trazabilidad técnica local con alcances/fechas, no homologación normativa |
| Encargo RC12 y decisiones de continuidad | Alcance vigente: auditoría documental, arquitectura abierta, ciencia/efectos no autorizados |

Se buscaron nombres candidatos ERS/actas/H0/FUT/G0 en `git ls-files` y rutas
históricas de `git log --all --name-only`, y se contrastaron las referencias
de 85-M. «No localizado» no significa inexistente fuera del repositorio. No se
accede a carpetas privadas ni se reclasifican horizontes formales por inferencia.

Las [29 brechas PNDA](brechas_reconciliadas_pnda_paso84i.md) mantienen 29 IDs
únicos: **2 resueltas, 17 parcialmente documentadas, 8 pendientes y 2
contradicciones documentadas**. Ninguna cambia por RC12. Las resueltas se limitan
a sus condiciones documentales; no habilitan estaciones, tiempo o ciencia.

## Verificación y dictamen

Se crea exclusivamente este documento y los otros tres enlazados. Sin cambios
Python, tests, dependencias, formatos JSON QA/85-J/K/RC6/RC10, SQLite o contratos
RC3/RC7. El resultado final de comprobaciones documentales/Git y la matriz de
preparación científica se registran en la hoja de ruta asociada.

**Dictamen: APTO CON RESTRICCIONES para continuar el desarrollo arquitectónico
acotado y someter este expediente a revisión.** No es un APTO operativo, una
validación contra la ERS ausente ni una autorización de núcleos científicos.
Los bloqueos AT01–AT04/AT08/AT10 se aplican al uso que requiera esas garantías.
La hoja de ruta selecciona un único bloque siguiente propuesto; no lo inicia.

Cero conexiones, GET, descargas, instalaciones, migraciones, commits o push.
No se accedió a RAW, staging, SQLite operativo o CSV PNDA. La ausencia de acceso
es el alcance de nuestras acciones; Git o los tests históricos no certifican la
integridad física actual de los originales que no se abrieron.
