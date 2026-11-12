# PASO 85-H — Contrato de trazabilidad y cierre en memoria

El incremento parte de Git limpio, rama `feature/suadc-http`, commit **4ea000d**,
que registra el PASO 85-G. Se revisaron su [contrato](contrato_ejecucion_integrada_paso85g.md),
[piloto](piloto_integracion_vertical_paso85g.md) y [brechas](brechas_integracion_paso85g.md).
No se reescriben esos documentos históricos.

La reanudación parte del WIP **c259b62**, inicialmente limpio. Se conservan el
modelo y las interfaces anteriores; se completa el cotejo de estados internos
descrito abajo. El historial de ensayos de la sesión inicial se distingue de la
nueva verificación en la sección 7 del informe del piloto.

## 1. Auditoría y necesidad acotada

InformeEjecucion85G ya retiene el contrato, ActivoRAW/ResultadoHTTPRAW,
RegistroRecurso, ResultadoQA/InformeQA, InformeLecturaCSV, InformeConsumoQA e
InformeConciliacionQA. Después del cierre sobreviven estos valores mientras el
llamador los conserve; desaparecen los bytes de RAW/staging, las bases SQLite,
sus índices/historial y los manejadores. Las rutas devueltas son históricas.

Se identificaron pérdidas concretas: el prefijo JSON desaparecía si fallaba la
exportación; tuple(qa) descartaba los resultados ya producidos si el iterador
lanzaba una excepción; el informe no distinguía manejadores adquiridos y cerrados;
no existía captura previa al cierre para contrastar la evidencia posterior.
El auxiliar de checkout se amplía exclusivamente para cubrirlas. No se modifican
contratos estables de src/spica, JSON QA 0.1.0, reglas, transportes o bases.

[traza_cierre_85h.py](../herramientas/traza_cierre_85h.py) es un componente puro:
sin E/S, reloj, generación de IDs, red o ejecución QA. Reutiliza el consumidor y
conciliador para cotejar evidencia. No es un almacén, importador de trazas ajenas,
orquestador, sistema de permisos o implementación criptográfica nueva.

## 2. Contrato y proyección

Versión experimental **0.1.0**. Dos DTO congelados: TrazaCierre85H(canonico,
sha256) y VerificacionTraza85H(coherente_en_alcance, cadena_completa,
diagnosticos, comprobaciones, limitaciones). bool de ambos se rechaza. Sus campos
no conceden autorización. Congelación de dataclasses no aísla Python hostil.

| Grupo de la representación | Información conservada / procedencia |
|---|---|
| Contrato | Ejecución, entrada, evaluación, tarea declarada, proyecto/objeto/producto/recurso, configuración y presupuestos de 85-G |
| Activo observado | ID real del temporal, SHA y tamaño del informe RAW; fecha/estado/comprobación, separados de controles esperados |
| Transporte simulado | Origen sanitizado, bytes, SHA, estado HTTP, intentos y fase del adaptador; no credenciales ni ruta absoluta |
| Catálogo | RegistroRecurso completo y revisión local consultada, incluida procedencia técnica declarada |
| Recuperaciones | Nombres de las recuperaciones que retornaron correctamente; incluye controles posteriores a QA y antes del cierre |
| QA | Huella del contenido nativo, regla/versión, posición, campos objetivo, estado, diagnóstico, procedencia y restricciones por resultado; informes y lecturas reales |
| Exportaciones | JSON oficial por lote, incluido prefijo producido antes de un fallo; no reconstruir exportaciones no realizadas |
| Consumo | Estado, conteos, problemas, comprobaciones, limitaciones y huellas de los documentos aceptados; sin duplicar su texto |
| Conciliación | Estado, versiones, resúmenes/huellas de lotes, coincidencias, conflictos y no comparables; conserva IDs de hallazgos |
| Cierre | Eventos originales, estados explícitos por etapa, recursos adquiridos/liberados, eliminación y huella de captura previa |
| Error HTTP parcial | Código/fase/estado HTTP e intentos públicos de ErrorIntegracionHTTPRAW, incluso cuando no retornó un ResultadoHTTPRAW |
| Limitaciones | Incidencias/discontinuidades, restricciones globales, operaciones no realizadas, ciencia y autorización False |

No se inventa adquisicion_id: el adaptador básico no lo produce. En QA tanto
adquisicion_id como documento siguen None. Ejecucion_id, evaluacion_id,
entrada_id, asset_id y resultado_id tienen funciones distintas. No se reemplazan
entre sí ni se crea un ID de cierre que los componentes no hayan emitido.

El JSON QA existente incluye los valores originales necesarios para sus controles;
se conserva por exportación, sin añadir el CSV completo ni otro cuerpo nativo
redundante. La proyección de nativos conserva su huella, referencias y restricciones.
Los presupuestos técnicos pueden contener float finitos; las observaciones siguen
textuales. La proyección excluye rutas físicas absolutas de resultados HTTP/RAW.

## 3. Orden de cierre y estados

1. Terminar las operaciones o conservar el fallo/cancelación/límite detectado.
2. Conservar resultados ya emitidos, informes y prefijos JSON.
3. Si existe ResultadoHTTPRAW, recuperar/verificar físicamente el activo de prueba
   una vez más antes del cierre; si falla, conservar el error e impedir conclusión.
4. Capturar canónicamente la evidencia aún disponible con los manejadores abiertos.
5. ExitStack invoca cierres en orden inverso; solo se registra una liberación
   después de que el respectivo __exit__ retorne.
6. TemporaryDirectory elimina exclusivamente el árbol propio.
7. Completar estado/diagnósticos de cierre y construir la traza final en memoria.
8. Cotejar captura previa, enlaces, JSON, restricciones, consumidor y conciliación.

La captura previa contiene la evidencia material. El sello final se construye
después del cierre: el hecho de la eliminación todavía no existía antes. El
componente puro comprueba relaciones contractuales retenidas; no simula una
lectura física posterior. Si falla la captura o limpieza, nunca se declara éxito.

| Estado global reutilizado | Transición / alcance |
|---|---|
| PLANIFICADA | Solicitud validada; no es un estado final de traza |
| INICIADA | Evento de entrada en fase; tampoco es un cierre final |
| CONCLUIDA | Cadena estructural completa, dos reproducciones compatibles, referencias y restricciones cotejadas, recursos liberados |
| INCOMPLETA | Presupuesto o recorrido incompleto; conserva evidencia disponible y causa |
| FALLIDA | Fallo técnico, contradicción, rechazo o cierre no confirmado; no equivale a ausencia de evidencia |
| CANCELADA | Cancelación reconocida en frontera cooperativa; conserva fases anteriores |

El arnés síncrono transita PLANIFICADA → INICIADA → uno de los cuatro estados
finales. Una cancelación previa puede no iniciar ninguna etapa. Las fases siguen
un prefijo fijo (validación, adquisición simulada, catálogo, recuperación/QA/
exportación/consumo A y B, conciliación). Se conservan los eventos y se clasifican
las fases como no_iniciada, concluida_en_alcance, estado terminal o sin confirmación.
El cierre de recursos puede ser correcto aunque la ejecución haya fallado.
No hay transición automática de un estado final a otra ejecución ni reanudación.

KeyboardInterrupt/SystemExit se propagan después de los contextos. No se promete
un informe final para ellos, terminación forzada, fallos de memoria o apagado.
Una causa de cierre adicional se agrega sin borrar el diagnóstico anterior.

## 4. Relaciones de linaje

| Enlace | Cotejo / límite de confianza |
|---|---|
| Entrada → activo | SHA/tamaño observado contra control esperado; IDs proyecto/objeto/recurso/fuente y activo conocido |
| Transferencia → activo | SHA/tamaño HTTP y RAW; origen del doble, HTTP 200, descarga COMPLETA, fase COMPLETADA, sin error o temporal restante; RAW INCORPORADA sin error; no autenticidad TLS |
| Activo → catálogo | Fuente/producto/recurso/localizador, revisión y evidencia técnica enlazan asset_id; sin FK global |
| Activo → recuperación | Retorno real de recuperar durante el ensayo; registro histórico no relectura posterior |
| Recuperación → QA | Recuperación de esa pasada, procedencia fuente/recurso/activo/SHA de cada resultado; sin documento/adquisición inventados |
| QA → JSON | Huella nativa, configuración y contexto/posición corresponden a documentos revalidados; reglas únicas/conteos/procedencia del informe se contrastan con los nativos, sin suponer orden del consumidor |
| JSON → consumo | Consumidor real acotado y comparación del informe completo; unicidad, restricciones oficiales y conteos |
| Consumos → conciliación | Reconstrucción con LoteQA A/B y comparación del informe real; sin fusionar ni suprimir conflictos |

Cada enlace se clasifica coherente o discontinuidad. Una contradicción disponible
se conserva como incidencia; un tramo no iniciado no se inventa. Un cierre parcial
puede ser una representación coherente de una cadena incompleta. CONCLUIDA con
datos esenciales ausentes, enlaces contradictorios o restricciones perdidas se
rechaza. Una traza del fallo de SHA conserva ambos controles y la discrepancia.

Para aceptar CONCLUIDA, ambas evaluaciones deben estar COMPLETA, con recorrido
completo, motivo EOF, filas examinadas/finalizadas correspondientes a los nativos,
cero evaluaciones incompletas y los límites previstos por el contrato. Ambos
lectores deben declarar COMPATIBLE, recorrido completo y EOF, sin registro
interrumpido o problemático; sus conteos incluyen encabezado y filas de datos y
sus bytes corresponden al tamaño físico registrado. Un evento de éxito no
sustituye estas comprobaciones. En un cierre parcial se conserva el estado real
sin exigir falsamente que hayan terminado las fases posteriores.

## 5. Canonicalización, límites y modelo de confianza

JSON UTF-8 sin BOM, claves ordenadas, separadores compactos, ensure_ascii=False,
allow_nan=False. Se respeta el orden de eventos y de resultados producidos; el
consumidor establece su propio orden canónico. SHA-256 se calcula sobre los bytes
UTF-8 de la representación final. No usa reloj nuevo, ruta temporal aleatoria,
repr de objetos, eval, importación de clases elegidas por JSON o código de reglas.

Tope de representación: **8 MiB**, reducible por el llamador; rechazo explícito
si se excede. Se conservan los presupuestos 85-G de entrada/QA/JSON y los del
consumidor. Son límites lógicos, no cuota RSS, tiempo global o reserva de disco.
El informe, su captura y la traza coexistirán en memoria: no es streaming de trazas.
Si el presupuesto impide producir una representación, se rechaza explícitamente;
no se publica una traza truncada como completa. El informe auxiliar puede seguir
reteniendo evidencia y el diagnóstico de captura fallida. No hay fallback durable.

construir_traza_85h recibe exclusivamente un InformeEjecucion85G del ensayo.
verificar_traza_85h exige **traza, informe y referencia_sha256 conservada por
separado**. Recalcula la proyección y cotejos; no deserializa/importa un expediente
arbitrario recibido ni acepta únicamente el hash que trae el propio DTO. Cambiar
una traza y recalcular su hash no la hace corresponder con el informe retenido.

La referencia separada y el informe son anclas locales de un proceso confiable,
no evidencia independiente. Si un atacante sustituye ambos o ejecuta Python
hostil, no existe autenticación. Se necesitan los tres valores para el cotejo
completo de esta API; perder el informe reduce la capacidad de cotejo y no se
ofrece importación posterior desde el texto como sustituto.

La referencia al tipo de informe se importa de forma diferida dentro del componente
puro: el arnés define sus DTO antes de invocar la captura. No hay importación
inversa durante inicialización ni ejecución de pilotos al importar. Se conserva
esta dependencia auxiliar acotada para evitar extraer/redefinir contratos históricos;
si se promueve a paquete estable, corresponde revisar su dirección de dependencias.
El modelo de uso sigue siendo secuencial; no hay snapshot atómico contra mutaciones
concurrentes o código hostil del mismo intérprete.

| Garantía | Qué se acredita |
|---|---|
| A — Física durante ejecución | Copia/hash/recuperación real de bytes sintéticos; controles antes y después de QA y antes del cierre |
| B — Coherencia de traza | Correspondencia contractual de IDs, etapas, estados, contenido y restricciones en el perfil fijo |
| C — Integridad de representación | Canonicalización y SHA contra control separado, proyección cotejada con informe |
| D — Reproducibilidad | A/B del mismo activo/contexto y reconstrucción determinista de la misma evidencia |
| E — Después del cierre | Informe, traza y control siguen utilizables mientras el proceso/llamador los conserve |
| F — Durabilidad | No implementada |
| G — Recuperación tras apagado | No implementada |
| H — Autenticidad independiente | No implementada; SHA no es firma institucional |
| I — Validación científica | No ejecutada ni autorizada por el cierre estructural |

## 6. Efectos y restricciones

Solo la frontera HTTP es MockTransport cerrado: se procesa un GET simulado por
adquisición sintética, **cero GET externos y cero descargas institucionales**.
No se acepta un transporte de red del llamador. No se prueba handshake TLS.
RAW/catálogos nuevos se crean dentro de temporales exclusivos, siguiendo los
constructores existentes que preparan esquemas vacíos/referencias en memoria.
No se migran almacenes preexistentes u operativos. No se cambia ese mecanismo
estable para ocultar llamadas internas de inicialización.

No se accede a SPICA_DATOS, CSV/documentos institucionales, staging/SQLite
operativos o manifiestos privados. No se toca main.py, .gitignore, .venv,
dependencias ni las 29 brechas PNDA. No hay ciencia, GIS, IA, autorización,
normalización de HORA/UBIGEO/PP, commits o push.

Resultados y verificaciones: [piloto 85-H](piloto_cierre_ejecucion_paso85h.md).
Pendientes: [persistencia y linaje](brechas_persistencia_linaje_paso85h.md).
