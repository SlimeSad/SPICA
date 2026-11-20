# RC12 — Trazabilidad de conexiones arquitectónicas

Fecha: **2026-11-20**, America/Lima. Base `128ada9`.
[Auditoría](auditoria_transversal_arquitectura_rc12.md),
[evolución propuesta](decision_evolucion_cierres_noqa_rc12.md) y
[prioridades](hoja_ruta_priorizada_rc12.md).

## Fuente e identidad de las conexiones

Se recuperaron las **33 conexiones originales M01–M33** de la
[matriz 85-F](matriz_dependencias_integracion_paso85f.md), sección 2, y su delta
en la [matriz 85-M](matriz_diseno_implementacion_paso85m.md), sección 4.
85-M no creó otros significados para M03/M16/M26/M32. Las 28 IM, 25 componentes C
y grupos RC originales son vistas distintas; no se igualan sus cardinalidades.

Estados heredados: **D** demostrada dentro del alcance indicado; **P** prevista
sin implementación del efecto requerido; **O** opcional futura. D puede describir
solo un contrato/diagnóstico o un ensayo sintético, no un flujo institucional
completo. En RC12 las pruebas se inspeccionan como texto; no se ejecutan.
La columna de prioridad propone trabajo, no cambia aprobaciones históricas.

## Las 33 relaciones contrastadas

| ID y relación original | 85-F → 85-M → RC12 | Contrato/código actual contrastado | Prueba fuente, condición y próxima acción |
|---|---|---|---|
| M01 C01→C08, núcleo→solicitud/plan | D → D → D | [SolicitudAdquisicion/ConsultaProducto](../src/spica/adquisicion/planificacion/modelos.py) | [núcleo](../tests/test_adquisicion_nucleo.py), [plan](../tests/test_planificacion.py); multivariable/multiestación e intervalo; sin inventar fechas para documentos estáticos. Mantener |
| M02 C07→C08, catálogo→plan | D → D → D | [leer_acotado](../src/spica/adquisicion/catalogo/persistencia.py), [Planificador](../src/spica/adquisicion/planificacion/planificador.py) | [plan](../tests/test_planificacion.py); transacción acotada, asociaciones sin cartesiano; cobertura catalogada no acredita disponibilidad remota. Mantener |
| M03 C08→C09/C02, plan→conector/HTTP | P → P → P | [PlanConsulta.ejecutable=False](../src/spica/adquisicion/planificacion/modelos.py); ningún traductor institucional o ejecutor de planes | [test_plan_no_genera_localizadores](../tests/test_planificacion.py); RC1/RC3 describen operaciones, no activan GET. P1 condicionado a un efecto aprobado |
| M04 C09→C02, conector→cliente | D → D → D | [descubrir](../src/spica/adquisicion/conectores/senamhi/pnda.py)→ClienteHTTP.get | [PNDA](../tests/test_conector_senamhi_pnda.py); parser HTML/dcat fijo que falla cerrado; sin servicio vivo comprobado en RC12. Mantener |
| M05 C09→C07, registro documental | D → D → D | registrar_catalogo→[registrar_documental](../src/spica/adquisicion/catalogo/documental.py) | [registro](../tests/test_registro_evidencias.py), [PNDA](../tests/test_conector_senamhi_pnda.py); revisiones/contradicciones por registro, no transacción global. P2 al ampliar lotes |
| M06 C09→C10, piloto XLSX→HTTPRAW | D → D → D | [adquirir](../src/spica/adquisicion/conectores/senamhi/pnda.py) exige rol DICCIONARIO/formato xlsx y adaptador compartido | [PNDA](../tests/test_conector_senamhi_pnda.py); CSV/DOCX no autorizados por ese método. Antecedentes por otro procedimiento no cambian su API. Mantener |
| M07 C04↔C02/C03, reintentos GET | D → D → D | [GestorReintentos](../src/spica/adquisicion/transportes/reintentos.py), get/descargar | [reintentos](../tests/test_reintentos_http.py), [HTTPRAW](../tests/test_integracion_http_raw.py); parcial descartado antes de reiniciar, Event y Retry-After; sin Range/diario/plazo global. Mantener |
| M08 C02→C03, streaming común | D → D → D | [ClienteHTTP.descargar/_abrir/_bloques](../src/spica/adquisicion/transportes/http.py)→descargar_archivo | [descargas](../tests/test_descargas_http.py); misma política/origen y límite de bytes efectivos. No duplicar cliente. Mantener |
| M09 C03→C10, informe de transferencia | D → D reforzada → D acotada | [InformeDescarga/AdaptadorHTTPRAW](../src/spica/adquisicion/integracion/http_raw.py); estado/ruta propia/tamaño/SHA | [HTTPRAW](../tests/test_integracion_http_raw.py), [85-G](../tests/test_integracion_vertical_85g.py); informes falsos no evitan relectura. Mantener regresión al evolucionar cierre |
| M10 C10→C05/C07, incorporación/evidencia | D → D reforzada → D acotada | adquirir_documentado→[incorporar_documentado](../src/spica/adquisicion/almacenamiento/raw.py) | [HTTPRAW](../tests/test_integracion_http_raw.py), [registro](../tests/test_registro_evidencias.py); continuidad física y evidencia de recurso; sin atomicidad entre todos los catálogos. P1 antes de prometerla |
| M11 C05→C10→C13, recuperación/formato | D → D reforzada → D acotada | recuperar→[verificar_archivo](../src/spica/adquisicion/verificacion/inspector.py) | [formatos integrados](../tests/test_integracion_formatos.py); HTML inesperado puede conservarse sin ser XLSX útil; CSV vacío no implica ciencia. Mantener |
| M12 C06→C05/C10, configuración compartida | D → D → D | [ConfiguracionRAW.abrir/inicializar/adaptador_http](../src/spica/adquisicion/almacenamiento/configuracion.py) | [configuración](../tests/test_configuracion_raw.py), [cierre](../tests/test_cierre_configuracion_raw.py); no doble almacén; abrir sondea escritura/WAL puede usar TEMP. No invocarlo en auditoría operativa sin permiso |
| M13 C05↔SQLite/archivos, originales | D → D reforzada → D acotada | [CatalogoRAW](../src/spica/adquisicion/almacenamiento/catalogo.py), publicación exclusiva y MD | [RAW](../tests/test_almacenamiento_raw.py), [MD](../tests/test_modelos_md_raw.py), [altas](../tests/test_regresiones_altas.py); activos separados con contenido compartido; uso secuencial. P1 si se exige recuperación integral |
| M14 C11→C05, manual→RAW | D → D → D | [IngestorManual.ingestar](../src/spica/adquisicion/manual/ingesta.py)→incorporar_manual_documentado | [manual](../tests/test_ingesta_manual.py); recibo MANUAL no es GET/autenticidad; no copia definitiva paralela. Mantener |
| M15 C05/C07/C11→C12, antecedentes | D en memoria → D → D en memoria | [antecedente_desde_raw](../src/spica/adquisicion/readquisicion/antecedentes.py) y EvidenciaLocal aportada | [readquisición](../tests/test_readquisicion.py); versión documental no es versión de contenido; metadato RAW no relectura actual. Mantener |
| M16 C12→C02/C11, decisión→efecto | P → P → P | [ResultadoDecision.autoriza_red=False](../src/spica/adquisicion/readquisicion/modelos.py), motor puro | [readquisición](../tests/test_readquisicion.py); sin hook/ejecutor aprobado. RC3/RC11 no lo añaden. P1 al abrir readquisición efectiva |
| M17 C13→C15/C21, CSV/local→QA | D → D reforzada → D acotada | [adaptar_registro/EvaluadorNivel0](../src/spica/calidad/motor.py) y lectores existentes | [QA0](../tests/test_calidad_nivel0.py), [consultas](../tests/test_consultas_locales.py); perfil de 16 campos, una variable de consulta evita multiplicar filas. P1 antes de otro perfil QA |
| M18 C05/C10/C11→C15/C21/C22, ciclo vertical | P → D acotada → D acotada | [piloto 85-G](../herramientas/piloto_integracion_85g.py), [cierre H](../herramientas/traza_cierre_85h.py) | [G](../tests/test_integracion_vertical_85g.py), [H](../tests/test_traza_cierre_85h.py); HTTP simulado→RAW→QA→JSON/consumo/conciliación. Manual completo y otros productos siguen fuera de esa demostración |
| M19 C15/C13→C16, perfilado | D → D → D | [perfilar_csv](../src/spica/perfilado/meteorologico.py), interpretar_numero compartido | [perfilado](../tests/test_perfilado_meteorologico.py); diagnóstico con índice temporal acotado, no dataset preparado/ciencia. P2 medición cuando cambie escala |
| M20 C17→C02/parser, ArcGIS metadatos | D → D → D para metadatos | [EnsayoMetadatosArcGIS](../src/spica/adquisicion/inspeccion_arcgis/ensayo.py) e inspector acotado | [inspector](../tests/test_inspeccion_arcgis.py), [presupuesto](../tests/test_inspeccion_arcgis_presupuesto.py); metadatos no prueban entidades ni /query. Bloqueo institucional intacto |
| M21 C18→parser/C19, vector offline | D sintética → D → D sintética | [coordinar](../src/spica/adquisicion/vectorial/coordinador.py), [validador](../src/spica/adquisicion/vectorial/validador.py), adaptar_vectorial | [FeatureSet](../tests/test_vectorial_featureset.py), [vector](../tests/test_vectorial_coordinacion.py); sin puente de entidades HTTP→RAW o GIS operativo. Fuera del bloque siguiente |
| M22 C18→evidencia temporal | D → D → D sintética | [simulación](../src/spica/adquisicion/piloto_arcgis/simulador.py), [conservación de evidencia](../src/spica/adquisicion/piloto_arcgis/evidencia.py) | [piloto](../tests/test_piloto_arcgis.py), [evidencia](../tests/test_evidencia_piloto_arcgis.py); conservación TEMP no prueba institucional ni custodia. Mantener |
| M23 C07/C15/C17/C18→C19, adaptadores | D → D → D sobre DTO | [adaptadores](../src/spica/interoperabilidad/adaptadores.py), RecursoInteroperable/ResultadoAdaptacion | [adaptadores](../tests/test_adaptadores_interoperabilidad.py), [integración](../tests/test_integracion_interoperabilidad.py); RC2 añade perfiles, no conversiones ni correspondencias científicas por nombre. Mantener |
| M24 C19→operación propuesta | D → D → D diagnóstica | [evaluar_operacion](../src/spica/interoperabilidad/operaciones.py) y evaluar_aptitud | [aptitud](../tests/test_interoperabilidad_evaluador.py), [integración](../tests/test_integracion_interoperabilidad.py); operacion_ejecutada=False. P0 condicional si se usa como permiso/asociación efectiva |
| M25 C14→C20, cotejo→afirmaciones | D acotada → D → D acotada | [CotejadorDocumental](../herramientas/vinculacion_documental.py), modelos documentales | [vinculación](../tests/test_vinculacion_documental.py); control esperado, hash/localizador y texto literal, sin autoría/equivalencia semántica automáticas. Mantener |
| M26 C20→C21/C24/C19, evidencia→uso revisado | P → P → P | [evaluar_uso](../src/spica/metadatos_documentales/evaluacion.py), aplicabilidad y perfiles solo diagnostican | [metadatos](../tests/test_metadatos_documentales.py), [confianza](../tests/test_confianza_documental.py); no adaptador que seleccione/apruebe fundamento científico o convierta permiso. P1 para el caso científico |
| M27 C21→C22, QA→exportación oficial | D → D reforzada → D con cierre RC8 específico | [exportar_resultado_json](../src/spica/calidad/exportacion.py), [RC8](../src/spica/artefactos/cierre_exportacion.py) | [exportación](../tests/test_exportacion_qaqc_85c.py), [RC8](../tests/test_cierre_exportacion_rc8.py); preserva nativos/política/versiones; no asdict directo, ciencia ni permiso. Mantener |
| M28 JSON→C22, consumo contractual | D → D reforzada → D con admisión RC9 específica | [consumir_exportaciones](../src/spica/calidad/consumo.py), [RC9](../src/spica/artefactos/admision_exportacion.py) | [consumo](../tests/test_consumo_qaqc_85d.py), [RC9](../tests/test_admision_exportacion_rc9.py); perfil cerrado, captura ligada y física opcional. No satisface RC3 por sí sola |
| M29 C22→C23, conciliación | D → D reforzada → D acotada | [conciliar_lotes](../src/spica/calidad/conciliacion_lotes.py) revalida y conserva documentos/conflictos | [lotes](../tests/test_conciliacion_qaqc_85e.py); 2–8 lotes, sin fusión de ejecuciones ni unicidad global. No sustituir por agregados/conteos |
| M30 C24→aplicabilidad/ejecución | D contractual → D diagnóstica → D solo contractual/diagnóstica | [catálogo](../src/spica/calidad/catalogo_cientifico.py), [verificador](../src/spica/calidad/aplicabilidad/verificador.py) | [reglas](../tests/test_reglas_cientificas.py), [aplicabilidad](../tests/test_aplicabilidad_cientifica.py); elegibilidad no ejecuta, no existe ejecutor científico autorizado. P1 antes de ciencia |
| M31 C24 sintético→resultados | D aislada → D aislada → D aislada | [evaluar_limites_sinteticos](../src/spica/calidad/experimental/limites.py) | [límites](../tests/test_limites_sinteticos.py); tipos exclusivos de fixtures, sin observaciones reales ni catálogo como permiso. No se ejecuta en RC12 |
| M32 resultados futuros→almacenamiento/exportación | P → P → P con avance contractual/físico parcial | [ResultadoCientifico](../src/spica/calidad/modelos_cientificos.py), [RC4](../src/spica/artefactos/modelos.py), [RC5/RC6](../src/spica/artefactos/conservacion.py) | [modelos](../tests/test_reglas_cientificas.py), [RC4](../tests/test_artefactos_rc4.py), [RC6](../tests/test_conservacion_rc6.py); faltan productor, formato/codec científico y cadena pertinente. JSON QA/portador RC10 no la cierran |
| M33 IA local/API→aplicación futura | O → O → O | Ningún puerto/adaptador IA/modelos en src; [requirements](../requirements.txt) | Sin prueba funcional IA; no se añaden dependencias ni se condiciona ciencia a nube/GPU/pagos. P3 si existe necesidad aprobada |

Resultado de clasificación actual: **28 D acotadas, cuatro P y una O**, como
85-M. En 85-F eran 27 D/cinco P/una O: M18 cambió históricamente en 85-G/H,
no en RC12. RC1–RC11 añaden evidencia/contratos dentro de alcances específicos,
no otro cierre contable de las cuatro P. No se detectó una contradicción estática
que obligue a rebajar una D en su alcance original; **no se ejecutaron regresiones
para afirmar funcionamiento actual** ni se validó un servicio externo.

## Cuatro conexiones prioritarias: definición original y condición de cierre

### M03 — Plan a conector/transporte

Definición textual recuperada de 85-F, emisor **C08 → C09/C02**:

> No existe ejecutor de PlanConsulta ni traducción institucional de selectores a parámetros HTTP

Participan Planificador/PlanConsulta, ConectorSENAMHIPNDA y ClienteHTTP.
RC1 proporciona contexto/operación y RC3 precedencia/recursos/diagnóstico; ninguno
consume un PlanConsulta para ejecutar un recurso. El conector sigue publicando
recursos estáticos específicos, sin traducción remota estación/variable/período.
La prueba `test_plan_no_genera_localizadores` solo demuestra esa ausencia de efecto.

**P → P → P. Prioridad P1 cuando se autorice ese efecto.** Requiere mapeo explícito
de una OperacionPlanificada a un recurso/mecanismo comprobados, contexto,
presupuesto y permiso separado. Prueba futura de aceptación: fixture de producto
realmente soportado, selección exacta y autorización acotada producen la llamada
esperada con MockTransport y continuidad RAW; sin autorización, traducción,
capacidad o presupuesto, **cero solicitudes**. Debe conservar parciales y no
inventar endpoints/filtros. Un núcleo que trabaje con entrada local no necesita
cerrar M03 para su ensayo offline.

### M16 — Decisión de readquisición a efecto

Definición textual recuperada de 85-F, emisor **C12 → C02/C11**:

> ResultadoDecision es recomendación; autoriza_red=False

Participan decidir_readquisicion/ResultadoDecision, ClienteHTTP e IngestorManual.
El motor puro examina evidencia aportada/actualización/restricciones, no archivos
ni red. RC3/RC11 no incorporan un hook previo a esos efectos. REUTILIZAR_LOCAL,
RECOMENDAR_NUEVA o ADQUISICION_INICIAL no constituyen autorización efectiva.

**P → P → P. Prioridad P1 antes de automatizar readquisición.** Necesita una
decisión enlazada a identidad/revisión de recurso y una política independiente
de operación/permiso, con vigencia pertinente y tratamiento de incertidumbre.
Aceptación futura: dos adquisiciones del mismo contenido permanecen distintas;
el efecto no se inicia por recomendación sola, historial incompleto, restricciones
ajenas/desconocidas o ausencia de autorización. Probar cancelación/error antes
y después del efecto, sin doble activo por reintento. No agregar E/S al motor puro.

### M26 — Evidencia documental a QA/aplicabilidad/operación

Definición textual recuperada de 85-F, emisor **C20 → C21/C24/C19**:

> evaluar_uso es diagnóstico; no conversor a formato QA, AfirmacionAplicabilidad o permiso

Participan ExpedienteMetadatos/AfirmacionDocumental/ResultadoUso, QA0,
verificador de aplicabilidad y RecursoInteroperable. RC2 compara campos/unidades
con respaldo aportado; RC3 y RC11 propagan restricciones. No existe el vínculo
revisado por producto/versión/uso que convierta un expediente pertinente en
configuración científica aprobada. La equivalencia editorial sigue siendo otro
hecho por acreditar, no un efecto de coincidir texto.

**P → P → P. Prioridad P1 y gate obligatorio del caso científico que dependa de
esa evidencia.** Contratos necesarios: selección de afirmaciones/localizadores,
identidad de documento/producto/revisión/período aplicable, revisión humana
trazable, contradicciones y destino de uso preciso; no una conversión universal.
Aceptación futura: evidencia sintética revisada y pertinente alimenta solo el
campo/uso aprobado conservando la traza; referencia ausente/contradictoria,
edición ajena, temporalidad desconocida o revisión no aportada bloquean. No
reconstruir HORA/UBIGEO/unidad ni otorgar ejecución por COINCIDE/VERIFICADO.

### M32 — Resultados científicos futuros a conservación/exportación

Definición textual recuperada de 85-F, emisor **resultados futuros → almacenamiento/exportación**:

> ResultadoCientifico/EvidenciaEjecucionCientifica existen como descripciones; no contrato transversal de derivados/linaje

Ese texto describe el estado de 85-F. **Hoy sí existen descriptores/linaje RC4 y
bytes sintéticos RC5/RC6**: no se repite la ausencia histórica como si fueran cero
avances actuales. Falta la integración científica pertinente: ResultadoCientifico
sigue vinculado a RegistroQA, no hay productor del primer método, formato de
salida científica ni perfil admitido para conservar/recuperar toda esa cadena.
RC10 conserva evidencia de exportación QA, no sustituye un resultado ambiental.

**P → P → P con avance parcial. Prioridad P1 antes de producir/prometer conservar
un resultado científico del caso seleccionado.** Reutilizar identidad, método/
versión/parámetros, incertidumbre, evidencia, restricciones y RC4–RC6. No almacenar
un derivado como original RAW ni agregar tipos a un codec cerrado en silencio.
Prueba futura: entrada sintética inmutable→operación pertinente→salida/versionado/
linaje→perfil explícito→recuperación en otro proceso, con restricciones completas;
parcial/cancelado/fallido jamás se recupera como resultado final. El método y sus
criterios científicos deben aprobarse aparte; no se elige ni ejecuta aquí.

## Fronteras auxiliares posteriores, sin renumerar las M

| Grupo auxiliar examinado | Estado real y evidencia |
|---|---|
| Contextos RC1→perfiles RC2→composición RC3 | D descriptiva; [RC1](../tests/test_contextos_rc1.py), [RC2](../tests/test_perfiles_informacion_rc2.py), [RC3](../tests/test_coordinacion_rc3.py). No efectos automáticos |
| Composición/linaje RC4→materialización RC5 | D acotada; [RC4](../tests/test_artefactos_rc4.py), [RC5](../tests/test_materializacion_rc5.py). Describir producción no ejecuta el método |
| RC5→RC6→RC7 | D para conservación/recuperación e inspección del perfil descriptivo; [RC6](../tests/test_conservacion_rc6.py), [RC7](../tests/test_integracion_artefactos_rc7.py). No cierre no QA ni vigencia física nueva aportada por RC7 |
| RC8→RC9→RC10→RC11→RC3/RC7 | Captura/admisión/historia/dictamen D en su ámbito; **última admisión bloqueada**. [RC11](../tests/test_dependencia_noqa_rc11.py), [RC10](../tests/test_conservacion_evidencias_rc10.py). No prueba positiva fingida |
| G→H→J→K y restauración K→J/H | D del perfil experimental de checkout, con pruebas [H](../tests/test_traza_cierre_85h.py), [J](../tests/test_conservacion_linaje_85j.py), [K](../tests/test_respaldo_linaje_85k.py). No conservación de RAW completo |
| Control K/RC6/RC10→custodia independiente 85-L | P/diseñada, [amenazas](modelo_amenazas_dominio_fallo_paso85l.md); pasar un control esperado no implementa otro canal/autoridad/dominio de fallo |

Se examinan **33 conexiones M y seis grupos auxiliares**, sin sumar estos grupos
como otras seis conexiones históricas equivalentes. Las pruebas de aceptación
faltantes son propuestas; ninguna se declara ejecutada en RC12. Las 29 brechas
PNDA y la negativa de autorización de `/query` INGEMMET siguen intactas.
