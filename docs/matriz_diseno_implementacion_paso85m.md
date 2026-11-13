# PASO 85-M — Matriz de diseño disponible frente a implementación

Fecha: **2026-11-13, America/Lima**. Base **d8742fc**, feature/suadc-http.
Complementa la [auditoría](auditoria_continuidad_arquitectonica_paso85m.md) y
la [hoja de ruta](hoja_ruta_continuidad_arquitectonica_paso85m.md).
IM01–IM28 son identificadores **locales de esta auditoría**, no requisitos de ERS.
A–H son los bloques del encargo 85-M; **no se les asigna 1.1–1.8** sin el original.

## 1. Leyendas y trazabilidad documental

Estado documental: **A** requisito aprobado con soporte; **B** aprobado con
reservas documentadas; **C** propuesta/contrato candidato; **D** decisión provisional;
**E** pendiente de ratificación; **F** documento o aprobación no localizados.
Ningún estado A/B formal se atribuye sin acta. C/D no rebajan aprobaciones históricas
desconocidas ni describen la estabilidad técnica del código. Una implementación
local puede estar probada aunque su correspondencia con la ERS permanezca F.

Estados de software, acumulables según alcance: **D = DISEÑADO**,
**I = IMPLEMENTADO**, **PA = PROBADO AISLADAMENTE**,
**IS = PROBADO EN INTEGRACIÓN SINTÉTICA**, **IO = INTEGRADO OPERATIVAMENTE**,
**P = PENDIENTE**, **NE = NO EVALUABLE POR FALTA DE EVIDENCIA**.
Son un eje distinto del documental y de D/P/O de las conexiones M.
Pruebas citadas se localizaron como texto; no se ejecutan en este paso.
No se asigna IO vigente a una plataforma completa por antecedentes particulares.
Cuando hay un procedimiento real documentado se indica **IO histórico acotado**,
sin inferir vigencia actual del servicio o del almacén mantenido cerrado.

| Referencia de diseño | Soporte disponible / estado | Regla para el cruce |
|---|---|---|
| Etapa 1, ERS v1.0/revisiones, apartados 1.1–1.8 | F: contenido original no localizado | Apartado original de todas las filas IM: no determinable; los bloques son del encargo actual |
| B1/DA1, H0/FUT, reservas y límites de G0 | F: actas/matriz formal no localizadas | No inventar A/B, asignar horizontes formales ni declarar G0 cerrado |
| C01–C25/R01–R12/H01–H10/M01–M33 de [85-F](auditoria_arquitectura_integral_paso85f.md) | Referencias locales disponibles; no ERS maestra | Se preservan sus IDs y se indica el cambio de alcance tras G–L |
| Contratos técnicos versionados/MD | Disponibles en código/docs; estado global de aprobación F, decisiones provisionales/candidatas según documento local | Contrastar campos/versiones/uso real, no homologar al Diseño Integral ausente |
| Diseño 85-I y custodia 85-L | C/D: propuestas delimitadas; ejecución posterior J/K solo donde documentada | El diseño de control independiente de L sigue sin implementar |
| Encargo 85-M | Instrucción vigente de continuidad arquitectónica | No es acta retrospectiva de los apartados originales ni autorización científica |

## 2. Responsabilidad, propietario funcional y contrato existente

Las dos tablas IM se unen por ID: esta identifica objetivo/código/interfaz/contrato
y dependencia; la siguiente añade pruebas, integración, restricciones y pendiente.
«Propietario» es responsabilidad de software; no se inventan personas aprobadoras.
Se contrastaron 35 clases/interfaces en 14 archivos y las exportaciones explícitas
de siete paquetes mediante AST. Las fachadas de núcleo/transportes/RAW/catálogo/
plan/QA/interoperabilidad son distintas de los auxiliares de herramientas;
un helper privado o una clase del arnés no se convierte en API pública instalada.

| ID / bloque | Objetivo y propietario funcional | Fuente local / estado documental | Código e interfaz comprobables | Contrato y dependencia |
|---|---|---|---|---|
| IM01 / A | Identidad y ciclo de proyectos/objetos; gestión de plataforma y RAW en su frontera | MD-01/02, R03; F global, campos locales documentados | [Modelos RAW](../src/spica/adquisicion/almacenamiento/modelos.py): ProyectoCientifico/ObjetoCientifico; CatalogoRAW | IDs proyecto/objeto, alias y metadatos; no servicio global de proyectos. Depende de identidad/versiones compartidas |
| IM02 / A | Contexto de usuario, responsabilidades, permisos y administración; futura aplicación | R12 y encargo; F original, E alcance global | [Main](../main.py) y validadores existentes; sin módulo IAM/administración | Responsable confiable declarado no equivale a usuario autenticado o autorización. Reutilizar controles, acordar modelo privado |
| IM03 / A | Contexto/tareas/configuración de aplicación; futura coordinación | R08/H02 y contrato G; C/D locales, E integración | [Arnés G](../herramientas/piloto_integracion_85g.py): ContratoEjecucion85G/ejecutar_piloto_85g; plan declarativo | Proyecto/entrada/evaluación/tarea_ref, fases; no tarea global. Depende de IM01/02/04/05 |
| IM04 / A | Presupuesto/cancelación y configuración explícita; operación/componentes | R09/H07; D de cotas por perfil | [Configuración RAW](../src/spica/adquisicion/almacenamiento/configuracion.py), LimitesQA y Presupuesto85G | Configuraciones/límites ya existentes; falta composición de efectos/tiempo/disco. Depende del alcance de IM03 |
| IM05 / B | Conjunto, recurso, revisión, activo y procedencia; gestión de información | R01/R04/MD; contratos locales disponibles, F global | [Catálogo](../src/spica/adquisicion/catalogo/modelos.py), [recurso](../src/spica/adquisicion/catalogo/documental.py), [snapshot](../src/spica/interoperabilidad/modelos.py) | Producto/Recurso/RegistroRecurso/RecursoInteroperable y ActivoRAW; ninguno es por sí solo dataset general. Reutilizar IDs sin nuevo catálogo paralelo |
| IM06 / B | Observación común y relaciones entre observaciones; futura frontera de perfiles | R05/H05, F original; E contrato transversal | [ObservacionLocal](../src/spica/adquisicion/consultas_locales/modelos.py), [RegistroQA](../src/spica/calidad/modelos.py) | Literales/posición/procedencia conservados; especialización SENAMHI. Depende de IM05/07/08/09, sin inventar estaciones |
| IM07 / B | Unidad/dimensión/medición, faltantes e incertidumbre; contexto de información | R04/R07/H05; C/D declarativos, F original | VariableCatalogo.unidad_declarada/tipo_medicion, [modelos científicos](../src/spica/calidad/modelos_cientificos.py) | Unidades literales e IncertidumbreCientifica/aplicabilidad; sin álgebra dimensional/metrología universal. Requiere evidencia/estado, no conversiones implícitas |
| IM08 / B | Tiempo/espacio y referencias conocidas o desconocidas; interoperabilidad | R05 y [política temporal](politica_temporal.md); D local | [Temporal](../src/spica/adquisicion/nucleo/temporal.py), MarcoTemporal/MarcoEspacial/CRSDeclarado | Instantes/civiles y CRS por ámbito; adaptar sin asociar/converter marcos. Depende de perfil/operación elegidos |
| IM09 / B | Metadatos, procedencia documental, contradicciones y restricciones; núcleo documental | R04/R07; [84-J](contratos_metadatos_documentales_paso84j.md), C/D locales | [Metadatos](../src/spica/metadatos_documentales/modelos.py), evaluar_uso, [cotejador](../herramientas/vinculacion_documental.py) | Afirmaciones/referencias y cotejo; no identidad editorial/aplicabilidad automática. Depende de fuentes revisadas y permiso separado |
| IM10 / C | Transporte, descarga, integridad y reintentos; transporte común | R02; contratos HTTP/descargas/reintentos, D de políticas | [ClienteHTTP](../src/spica/adquisicion/transportes/http.py), [descargas](../src/spica/adquisicion/transportes/descargas.py), [reintentos](../src/spica/adquisicion/transportes/reintentos.py) | RespuestaHTTP/InformeDescarga/RegistroIntento, TLS/origen/cuotas; depende de perfil autorizado y destino controlado |
| IM11 / C | Descubrimiento y acceso institucional; conector por producto | R01/H01, capacidades/expedientes locales; F para aprobación global | [PNDA](../src/spica/adquisicion/conectores/senamhi/pnda.py): descubrir/registrar_catalogo/adquirir | Producto fijo, adquirir piloto XLSX; CSV/DOCX históricos por procedimiento no amplían esa interfaz. Depende de IM09/10/13 |
| IM12 / C | Importación local y recomendación de readquisición; ingesta/decisión | R01/R12; [manual](ingesta_manual.md), [decisión](readquisicion.md) | [IngestorManual](../src/spica/adquisicion/manual/ingesta.py), [decidir_readquisicion](../src/spica/adquisicion/readquisicion/motor.py) | Recibo local/ResultadoDecision.autoriza_red=False; no efecto automático. Depende de archivo autorizado/antecedente real |
| IM13 / C | Staging/RAW y confirmación técnica de originales; almacenamiento/adaptador | R03/MD; contratos locales | [HTTPRAW](../src/spica/adquisicion/integracion/http_raw.py), [RAW](../src/spica/adquisicion/almacenamiento/raw.py) | DeclaracionRAW/ActivoRAW, publicación/hash/estados; privado secuencial, no transacción global. Depende de IM01/10/24 |
| IM14 / C | Catálogo y planificación multiestación/multivariable; metadata/planificador | R01/R04, M01–M03; D local | [CatalogoCientifico](../src/spica/adquisicion/catalogo/persistencia.py), [PlanConsulta](../src/spica/adquisicion/planificacion/modelos.py), [planificador](../src/spica/adquisicion/planificacion/planificador.py) | Esquema v1, revisiones/capacidad; ejecutable=False. Depende de metadatos; no genera endpoints ni periodos inventados |
| IM15 / D | Lectura/estructura y entradas incompatibles; lectores/inspectores | R06, contratos CSV/XLSX/DOCX | [LectorCSV](../src/spica/adquisicion/verificacion/csv_streaming.py), [inspector](../src/spica/adquisicion/verificacion/inspector.py), [DOCX](../src/spica/adquisicion/verificacion/docx/inspector.py) | RegistroCSV/InformeLectura/ResultadoEstructura; EOF/alcance, no semántica científica. Depende de archivo físicamente comprobado |
| IM16 / D | QA0 y propagación de restricciones; calidad estructural | R06/H01 y 85-A–E, contratos locales | [Motor](../src/spica/calidad/motor.py), [reglas](../src/spica/calidad/reglas.py), [restricciones](../src/spica/calidad/restricciones.py) | RegistroQA/ResultadoQA/InformeQA y 22 reglas; dependencia explícita de consultas SENAMHI. Depende de IM06/09/15 |
| IM17 / D | Preparación y transformaciones no destructivas; futuro procesamiento | R10/H06, E transversal, F original | [Perfilado](../src/spica/perfilado/meteorologico.py) diagnostica; no servicio de datos preparados | Hace falta vínculo versión/entrada→salida y estado/restricciones; no convertir perfiles diagnósticos en datasets preparados. Depende de IM05/06/21/24 |
| IM18 / E | Ejecución estructural controlada y cierre; composición G/H | R08/H02/H03, contrato G/H 0.1.0 | [Arnés G](../herramientas/piloto_integracion_85g.py), [cotejo H](../herramientas/traza_cierre_85h.py) | InformeEjecucion85G/estados/TrazaCierre85H; perfil fijo, no ejecutor de planes. Depende de componentes IM10–IM16/19 |
| IM19 / E | Exportación/consumo/reproducción de resultados QA; calidad | R06/R10, contratos 85-C/D/E | [Exportar JSON](../src/spica/calidad/exportacion.py), [consumo](../src/spica/calidad/consumo.py), [conciliación](../src/spica/calidad/conciliacion_lotes.py) | ContextoExportacionQA/LoteQA; JSON QA 0.1.0. No exportación científica universal; conserva restricciones/errores |
| IM20 / E | Linaje, conservación y recuperación de evidencia; herramientas J/H | R08/R10, [85-J](implementacion_persistencia_paso85j.md), C/D experimental | [Conservador](../herramientas/conservacion_linaje_85j.py), [codec](../herramientas/_codec_linaje_85j.py), [índice](../herramientas/_catalogo_linaje_85j.py) | I/T/R/manifiesto, 0.1.0 y 85001; no checkpoint de motor o codec general. Depende de Informe85G válido recibido |
| IM21 / E | Resultados científicos tipados y derivados reproducibles; futuro análisis/publicación | R10/H06 y modelos declarativos; C/E | [ResultadoCientifico](../src/spica/calidad/modelos_cientificos.py), EvidenciaEjecucionCientifica | Referencia a RegistroQA/ProcedenciaQA y método/contexto; no derivado universal ni ejecución real acreditada. Depende de IM05/07/09/17/26 |
| IM22 / F | Recuperación, respaldo y restauración; conservación J/K | R03/R08 y 85-K, D experimental | [GestorRespaldo85K](../herramientas/respaldo_linaje_85k.py): respaldar/verificar_respaldo/restaurar | ControlRespaldo85K y copia SQLite API; solo una ejecución TEMP, sin RAW. Depende de IM20 y esquema admitido |
| IM23 / F | Custodia, retención y referencias protegidas; futura conservación | [Diseño 85-L](arquitectura_custodia_independiente_paso85l.md), C/D; aceptación E | Sin gestor general implementado; control K solo triple esperado | Dominio de fallo/autoridad/canal distintos, inventario de dependencias y eliminación aprobada; sin TTL/GC. Depende de IM22/24 |
| IM24 / F | Ciclo de artefactos/originales/preparados/índices y consistencia; almacenamiento/información | R03/R10/H06/H08, D parcial/E común | [Catálogo RAW](../src/spica/adquisicion/almacenamiento/catalogo.py) y [catálogo científico](../src/spica/adquisicion/catalogo/persistencia.py), sin coordinador global | Estados/versiones propios y referencias; falta cierre transversal/derivados. No otra DB o transacción distribuida por defecto |
| IM25 / G | Métodos versionados, parámetros, referencias y aplicabilidad; calidad declarativa | R07/H01/H05, [catálogo de reglas](catalogo_reglas_cientificas.md) | [CatalogoReglasCientificas](../src/spica/calidad/catalogo_cientifico.py), [verificador](../src/spica/calidad/aplicabilidad/verificador.py) | ReglaCientifica/ContextoCientifico/HabilitacionCientifica; no permiso de ejecución. Depende de evidencia revisada, metadatos y contexto |
| IM26 / G | Entrada/salida y extensión de métodos sin mezclar cálculo e interpretación; futura frontera de análisis | R11/R10, E integración; F diseño original | [Evaluador sintético](../src/spica/calidad/experimental/limites.py) solo fixtures; no anfitrión científico general | Reutilizar descriptores, no cargar código de archivos; puente metodológico/observaciones/resultados pendiente. No seleccionar algoritmo |
| IM27 / H | GIS, visualización e interfaz; futuras capacidades con perfiles | R05/H09, propuestas 83/84 y encargo; sin homologación H0/FUT | [Vectorial](../src/spica/adquisicion/vectorial/coordinador.py), [interoperabilidad](../src/spica/interoperabilidad/operaciones.py), main mínimo | Estructura/simulación y operacion_ejecutada=False; sin mapa/GUI/análisis GIS operativo. Ampliación según caso y autorización |
| IM28 / H | IA híbrida opcional, comercio/servicios futuros; futura aplicación | R11/H09 y decisión expresa del usuario; sin clasificación formal FUT disponible | No adaptadores IA/modelos/pagos en src; requirements sin esas dependencias | IA local principal como apoyo, API opcional; determinismo/funciones esenciales sin IA/nube/GPU; freemium no degrada calidad |

## 3. Evidencia, integración y trabajo pendiente por responsabilidad

P0 solo bloquea un uso que viole garantías, no todo componente incompleto. Los
pendientes enlazan AM01–AM12 de la auditoría y los bloques RC de la hoja de ruta.

| ID | Prueba/evidencia disponible | Estado real y restricción | Pendiente / prioridad / dependencia |
|---|---|---|---|
| IM01 | [MD](../tests/test_modelos_md_raw.py), RAW | I/PA/IS en RAW; no gestor global | Contexto/proyecto reutilizable, sin duplicar MD; P1 RC1/AM02 |
| IM02 | [Regresiones](../tests/test_regresiones_altas.py), controles de rutas; sin tests IAM | Controles I/PA/IS; administración global P, ERS NE | Responsable/alcance explícitos para modelo privado; IAM multiusuario no exigido ahora; P1 RC1, ampliación P3 |
| IM03 | [Vertical G](../tests/test_integracion_vertical_85g.py), [plan](../tests/test_planificacion.py) | Arnés I/IS; contexto/tarea transversal P | Operación delimitada y política de efectos; P1 RC1/RC3, no activar planes |
| IM04 | [Cuotas HTTP](../tests/test_descargas_http.py), G/J/K y [QA](../tests/test_calidad_nivel0.py) | I/PA/IS por operación, sin cuota global RAM/disco | Componer presupuestos y cierre; P1 RC1/RC3, medir escala P2 |
| IM05 | [Catálogo](../tests/test_catalogo_cientifico.py), [registro](../tests/test_registro_evidencias.py), adaptadores | I/PA/IS en DTO; dataset general P | Mapear recurso/versión/activo/conjunto y estados; P1 RC1/RC2 |
| IM06 | [Consultas](../tests/test_consultas_locales.py), [adaptadores](../tests/test_adaptadores_interoperabilidad.py) | I/IS de perfil; observación común P | Adaptación explícita original/representación/procedencia/relaciones; P1 RC2, no variables/estaciones inventadas |
| IM07 | [Reglas científicas](../tests/test_reglas_cientificas.py), [aplicabilidad](../tests/test_aplicabilidad_cientifica.py) | I/PA declarativo/sintético; dimensión/metrología común P | Distinguir magnitud/unidad/medición e incertidumbre; P1 RC2, sin cálculo de conversiones |
| IM08 | [Tiempo](../tests/test_temporal.py), [interoperabilidad](../tests/test_interoperabilidad_evaluador.py) | I/PA/IS; no CRS/zonas desconocidas convertidos | Conectar contexto requerido de cada operación; P1 RC2, GIS efectivo posterior |
| IM09 | [Metadatos](../tests/test_metadatos_documentales.py), [vinculación](../tests/test_vinculacion_documental.py) | I/PA/IS acotada; no promoción de confianza | Puentes revisados y evidencia de uso M26, P1 RC2/RC4; P0 si se elude bloqueo |
| IM10 | [HTTP](../tests/test_transporte_http.py), [reintentos](../tests/test_reintentos_http.py), G | I/PA/IS; get genérico permite excepciones de TLS/HTTP | Conservar API y aplicar perfil explícito antes de efecto; P1 RC3/AM10 |
| IM11 | [PNDA](../tests/test_conector_senamhi_pnda.py), informes históricos de adquisición | I/PA/IS e IO histórico acotado en procedimientos concretos; vigencia actual NE | Autorización/evidencia por recurso, no generalizar XLSX a CSV; P1 al ampliar, fuera de RC1 |
| IM12 | [Manual](../tests/test_ingesta_manual.py), [readquisición](../tests/test_readquisicion.py) | Manual IS; decisión PA sin ejecución | M16 P y autorización previa; P1 al integrar efecto, reutilizar recibo/decisión |
| IM13 | [HTTPRAW](../tests/test_integracion_http_raw.py), [RAW](../tests/test_almacenamiento_raw.py), antecedentes 69/84-C | I/IS y uso RAW histórico acotado; estado operativo actual no reinspeccionado, sin garantía eléctrica/global | Política del ciclo de artefactos; P1 RC4/RC5 para operación, no refactorizar copia/hash |
| IM14 | Catálogo/plan y G | I/PA; snapshot integrado; M03 no ejecutada | Preparación/decisión distintas de ejecución; P1 RC1/RC3, mantener historia/versiones |
| IM15 | [Formatos](../tests/test_verificacion_formatos.py), [CSV](../tests/test_csv_streaming.py), [DOCX](../tests/test_inspector_docx.py) | I/PA/IS acotada; EOF/alcance reales | Interfaz de lectura por perfil sin filtrar incertidumbre; RC2/RC3, robustez P2 |
| IM16 | QA0, [contratos](../tests/test_contratos_qaqc_85b.py), G/H | I/PA/IS; no QA1 institucional | Evitar acoplar toda nueva disciplina a SENAMHI; P1 RC2/RC3; reglas intactas |
| IM17 | Perfilado probado; sin prueba de almacén/pipeline de preparados general | Descriptores D parcial, implementación transversal P | Estado/contrato/entrada→salida no destructivos; P1 RC4 cuando se abra preparación |
| IM18 | G/H, cancelación/cierre/fallos por fase | I/IS del arnés fijo; sin motor global | Composición reusable con contexto y resultados, sin segundo motor; P1 RC1/RC3 |
| IM19 | [Exportación](../tests/test_exportacion_qaqc_85c.py), [consumo](../tests/test_consumo_qaqc_85d.py), [lotes](../tests/test_conciliacion_qaqc_85e.py) | I/PA/IS para QA0; no exportación científica | Preservar formato y contratos; resultado nuevo se define antes de persistir; P1 RC4 |
| IM20 | [Conservación](../tests/test_conservacion_linaje_85j.py), procesos históricos J | I/PA/IS de evidencia; originales de G no incluidos | Compatibilidad/codec de entradas nuevas, no checkpoints inventados; P1 RC3/RC4/RC5 según alcance |
| IM21 | Tests de modelos científicos; no flujo de derivados científicos | Descriptor I/PA; operación/almacén P | Tipos y linaje separados de QA/original; P1 RC2/RC4; ningún algoritmo ahora |
| IM22 | [Respaldo](../tests/test_respaldo_linaje_85k.py), prueba histórica entre procesos | I/PA/IS TEMP; no otro dominio de fallo o cuenta probado | Portabilidad/destino/control/cierre completo; P1 RC5 antes de custodia única |
| IM23 | Diseño L; sin implementación/prueba de custodia protegida/retención | D y P; autoridad compartida sigue | Referencia separada/protegida y política manual de referencias; P1 RC5 según uso |
| IM24 | RAW y [configuración](../tests/test_configuracion_raw.py), J/K | I/IS de catálogos propios; sin transacción global/preparados | Ciclo de vida y diagnóstico transversal, no DB adicional; P1 RC4/RC5 |
| IM25 | Reglas/aplicabilidad/[confianza](../tests/test_confianza_documental.py) | I/PA de contratos, no ejecución científica institucional | Versiones/revisión de método y evidencia pertinentes, M30 sin permiso; P1 antes de ampliación analítica |
| IM26 | [Límites sintéticos](../tests/test_limites_sinteticos.py); solo fixtures | I/PA del evaluador específico; anfitrión común P | Contratos y frontera revisados con IM06/07/21, P1 RC2/RC4; método futuro no elegido |
| IM27 | [Vectorial](../tests/test_vectorial_coordinacion.py), [aptitud](../tests/test_integracion_interoperabilidad.py) | I/IS de estructura/DTO; GIS/UI/visualización P | Nuevos efectos/productos por alcance; P2/P3, no reclasificar horizonte formal FUT |
| IM28 | No implementación ni prueba IA/comercio localizada | D parcial por decisiones, P de código; ERS NE | Puertos opcionales/privacidad futuros, P3; no GPU/pagos como dependencia básica |

## 4. Las 33 conexiones heredadas, sin confundirlas con 33 flujos completos

**D:** relación demostrada en su alcance; **P:** prevista/no implementada para ese
efecto; **O:** opcional futura. El código src no cambió desde 85-F; los refuerzos
G–K se añaden mediante composición/cotejo/persistencia en herramientas. Se conserva
la [matriz histórica](matriz_dependencias_integracion_paso85f.md), aquí solo el delta.

| Conexión | Relación / estado en 85-F | Estado observado hasta 85-M | Cambio, evidencia o restricción pendiente |
|---|---|---|---|
| M01 | Núcleo→solicitud/plan, D | D | Sin cambio; fechas obligatorias no autorizan inventar periodo para recurso estático |
| M02 | Catálogo→planificador, D | D | Sin cambio; leer disponibilidad no prueba cobertura ni ejecuta |
| M03 | Plan→conector/HTTP, P | P | No hay ejecutor universal; tarea_ref G no consume PlanConsulta |
| M04 | Conector→cliente, D | D | Misma fuente/producto PNDA y parser fijo; no nueva API institucional |
| M05 | Conector→registro documental, D | D | Persistencia de evidencias específica, no transacción global de plataforma |
| M06 | PNDA XLSX→HTTPRAW, D | D | Método adquirir sigue acotado; procedimiento CSV/DOCX no amplía ese conector |
| M07 | Reintentos↔GET/streaming, D | D | G usa un intento; controles existentes no se duplican; sin Range |
| M08 | HTTP→descarga común, D | D | Misma política y helpers internos; no segundo cliente |
| M09 | Descarga→adaptador, D | D reforzada | G/H cotejan estados/tamaño/hash reales de fixture; no TLS externo probado |
| M10 | Adaptador→RAW/metadatos, D | D reforzada | G comprueba enlace activo/catalogación; no FK/transacción global |
| M11 | Recuperación→inspección, D | D reforzada | G/H verifican entrada antes/cierre y alcance; no relectura del RAW borrado tras G |
| M12 | Configuración→RAW/adaptador, D | D | Sin cambio; abrir/validar puede tener efectos; no lectura operativa inocua |
| M13 | RAW↔SQLite/archivos, D | D reforzada | G ejercita originales/estados; J/K no son un respaldo RAW completo |
| M14 | Manual→RAW, D | D | Integración propia; vía manual no se ejecuta en el flujo HTTP fijo G |
| M15 | Antecedente→readquisición, D en memoria | D | Sin cambio; metadato no es verificación física actual |
| M16 | Decisión→GET/ingesta, P | P | Recomendar no activa efectos ni permiso |
| M17 | CSV/local→QA, D | D reforzada | G/H comprueban identidad y cierre; conserva perfil SENAMHI |
| M18 | Activo→snapshot/lectura/ciclo QA, P | D acotada | G/H demuestran la ruta HTTP simulada completa; variantes manuales/productos distintos pendientes |
| M19 | CSV→perfilado, D | D | Sin cambio; diagnóstico no dataset preparado ni análisis climático |
| M20 | ArcGIS metadatos→HTTP/parser, D | D | Solo metadatos; /query no autorizado |
| M21 | Vector sintético→validación/adaptación, D | D | No servidor de entidades, publicación RAW o asociación geológica operativa |
| M22 | Simulación→evidencia temporal, D | D | No adquisición institucional o custodia independiente |
| M23 | Catálogo/local/vector→interoperabilidad, D | D | Snapshots/atributos documentales; no conversiones silenciosas |
| M24 | Aptitud→propuesta de operación, D | D | operacion_ejecutada=False, no autoriza ni asocia datos |
| M25 | Inspector/cotejador→afirmaciones, D | D | Cotejo literal y control local, sin promoción editorial/científica |
| M26 | Evidencia documental→QA/aplicabilidad/operación, P | P | Hace falta vínculo explícito revisado; G no lo implementa con documentos institucionales |
| M27 | QA→exportador oficial, D | D reforzada | G/H/J preservan nativos/JSON/versiones/restricciones; no usar asdict directo |
| M28 | JSON→consumidor, D | D reforzada | Cotejo en G/H y conservación J; aceptar JSON no certifica ciencia |
| M29 | Consumos→conciliación, D | D reforzada | Dos reproducciones completas/casos parciales; contexto no se fusiona por hash |
| M30 | Catálogo de reglas→aplicabilidad/ejecución, D contractual | D solo contractual/diagnóstica | Ejecución y permiso siguen pendientes; no interpretar la D como ejecutor científico |
| M31 | Contratos sintéticos→evaluador, D aislada | D aislada | Sin cambio; no acepta observaciones institucionales, ni se ejecuta aquí |
| M32 | Resultado futuro→almacén/exportación científica, P | P | J/K conservan Informe85G, no resuelven derivados generales |
| M33 | IA→aplicación, O | O | Decisión de IA opcional sin implementación; no horizonte formal FUT ratificado |

Resultado por relación, no por subsistema ni porcentaje: **28 D acotadas,
4 P (M03/M16/M26/M32) y 1 O (M33)**. En 85-F eran 27 D/5 P/1 O; el cambio de
categoría es M18. «Reforzada» añade evidencia de alcance, no una integración nueva
contable. Los ensayos locales anteriores no se presentan como vigencia de servicios.

Extensiones posteriores que no se añaden artificialmente a las 33:

| Relación auxiliar | Estado / alcance |
|---|---|
| Informe G→captura/traza/cotejo H | D en memoria, incluyendo estados/errores/prefijos y comprobación de cierre |
| Informe/traza/referencia H→conservador J | D en TEMP y proceso confiable; codec cerrado del informe conocido |
| Instancia conservada J→respaldo K | D, una ejecución, snapshot SQLite y copias independientes; no RAW |
| Restauración K→lector J/cotejo H | D en otro proceso mismo perfil; portabilidad de TEMP entre equipos no acreditada |
| Control K→custodia independiente propuesta L | P; control como argumento no implementa protección/canal independiente |

Los 25 componentes de F agrupan código, las 33 M son relaciones, los 16 subsistemas
de L son responsabilidades agregadas y estas 28 IM separan objetivos transversales.
Son vistas distintas del mismo árbol: sus cardinalidades no son una contradicción
ni justifican crear servicios nuevos para igualarlas.

## 5. Infraestructura de información científica: mínimo común y límites

| Elemento | Qué existe realmente | Ausencia transversal / decisión de continuidad |
|---|---|---|
| Conjunto/observación | RecursoCatalogo, ActivoRAW, ObservacionLocal, RegistroQA y snapshots documentales | Perfil de entrada común con correspondencias explícitas; no un modelo ambiental universal por decreto |
| Identidad/versiones/procedencia | Fuente/producto/recurso/activo/revisión/evaluación y controles | Hacer explícita su composición y diferencias; no equiparar revisión documental con contenido o ejecución |
| Valor original/faltante | Campos literales, presencia y diagnósticos de interpretación/QA | Conservar valor/estado original; una representación preparada no puede ocultar desconocidos o sustituir el original |
| Magnitud/unidad/dimensión/medición | Unidad y frecuencia declaradas, tipo_medicion, condiciones de aplicabilidad | Falta perfil transversal de medición/dimensión y su evidencia; no conversiones ni metrología inventadas |
| Tiempo | Contratos civil/naive/aware/UTC y marcos temporales | Requerimientos por operación, no convertir zona desconocida ni reconstruir HORA |
| Espacio | CRS por ámbito y datos vectoriales sintéticos | No GIS operativo ni correspondencia de estaciones por aproximación; no fabricar UBIGEO/códigos |
| Incertidumbre/calidad | Descriptores IncertidumbreCientifica, QA0, estados y restricciones | Propagar desconocidos/evidencia; no inventar precisión instrumental o validar ciencia por QA satisfecho |
| Relaciones entre observaciones | Posición/origen de fila/contexto de evaluación | No modelo general de muestreo/serie/relaciones; definir solo relaciones necesarias del perfil siguiente |
| Método y conjunto de datos | Descriptores de método/contexto/aplicabilidad | Vínculo entrada→método/versión/parámetros→resultado todavía no generalizado, sin anfitrión científico |
| Derivado/reproducibilidad | JSON QA/conciliación y traza estructural | Contrato/ciclo de preparado o derivado no destructivo, separado de RAW y de JSON QA |
| Estado/diagnóstico | Estados locales y errores por fase; informe G/H | Composición estable sin perder causas/parciales ni confundir verificación no realizada con fallo probado |
| Conservación | J/K evidencias del perfil fijo | No se acepta otro tipo en el codec sin revisión/versiones; no inventar bytes que nunca fueron conservados |

No todos estos elementos requieren implementación simultánea. Contexto e identidad
del flujo seleccionado van primero; los perfiles de información, preparados y
conservación se amplían según dependencias. Interpretación ambiental, simulación,
inferencia causal, conversiones y algoritmos permanecen fuera de 85-M.
