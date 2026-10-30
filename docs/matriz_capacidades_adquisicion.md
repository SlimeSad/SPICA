# PASO 78: matriz de capacidades y evidencia de adquisición

## Cómo interpretar los estados

- **Implementada y comprobada**: existe código y evidencia de la operación concreta.
  Se identifica si la comprobación es física local o una operación externa histórica.
- **Implementada, solo sintética**: comportamiento probado offline con contenido
  inventado/MockTransport; no acredita funcionamiento del servicio institucional.
- **Diseñada, no implementada**: existe representación o diseño declarativo, no ejecutor.
- **Pendiente de verificación institucional**: faltan evidencia y especificación de
  un producto real. No significa indisponibilidad en la institución.
- **No disponible en SPICA**: no existe esa capacidad operativa en el código actual.

Los estados se aplican a una función/producto, no se extienden a una institución
entera. Pueden coexistir código probado sintéticamente y acceso institucional no
verificado. No se contactaron servicios durante el PASO 78.

## Mecanismos A–G

| Mecanismo | Capacidad local comprobada | Evidencia institucional disponible | Falta concreta | Estado resultante |
| --- | --- | --- | --- | --- |
| A. Descarga pública directa | GET pequeño, streaming a disco, integración HTTP→RAW, comprobación física y errores | Piloto XLSX PNDA documentado en paso 60; antecedentes CSV ya adquirido y examinado en pasos 69/74 | Política de readquisición, vigencia del recurso y autorización nueva para cualquier GET real | Implementada y comprobada para esas operaciones históricas; nuevos recursos pendientes |
| B. API pública documentada | GET admite query params texto; núcleo representa variables/estaciones/períodos | No se verificó en estos expedientes una API institucional de consulta científica para los cuatro organismos | Contrato real de endpoints, filtros, paginación, formato, límites y evidencia de acceso | Diseñada en catálogo (`API_REST`); conector API no disponible; verificación institucional pendiente |
| C. API autenticada | Metadatos pueden declarar que requiere autenticación; 401/403 manejados | Ningún flujo autenticado institucional acreditado aquí | Esquema real, permisos, gestión de secretos, renovación/revocación y pruebas autorizadas | Descripción diseñada; ejecución autenticada no disponible |
| D. Portal con solicitud/acuerdo | `PORTAL_ASISTIDO`/`INSTITUCIONAL`, restricciones y referencias documentales | No hay expediente de procedimiento específico de ANA/OEFA/INGEMMET revisado en este paso | Condiciones, pasos humanos, permiso y forma de entrega reales | Mecanismo declarable; tramitación/automatización no disponibles |
| E. Archivo institucional manual | `AlmacenRAW.incorporar` copia un archivo local autorizado y verifica tamaño/hash; catálogo registra procedencia/recursos | Pruebas con archivos sintéticos; no se acredita una entrega manual nueva por esas instituciones | Flujo coordinado y recibo documental manual vinculado al activo, sin fingir HTTP | Incorporación básica implementada; flujo institucional manual completo diseñado, no implementado |
| F. Estación privada autorizada | Fuente, estaciones y variables arbitrarias; incorporación local y procedencia declarada | No hay estación privada real ni permiso examinado | Identidad y acuerdo reales, confidencialidad, unidades, instrumento, tiempo, alcance de uso y entrega | Contratos parcialmente reutilizables; integración real pendiente; autenticación/permiso ejecutable no disponibles |
| G. Fuente espacial/geográfica | RAW conserva bytes opacos; estación admite coordenadas, altitud y CRS declarado; enum `GEOESPACIAL` | No se verificó aquí un producto/servicio espacial de esos organismos | Contrato de descarga/servicio, identidad de capa/revisión, CRS/ejes, cobertura, formatos y piezas del recurso | Almacenamiento genérico implementado; cliente GIS y verificación espacial no disponibles; fuente pendiente |

Guardar un archivo espacial no equivale a leer sus geometrías, validar un CRS,
consumir un servicio geoespacial ni ejecutar GIS. GET de una URL tampoco prueba
que exista una API, un filtro remoto o acceso a todos los recursos de un producto.

## Evidencia externa histórica y su límite

| Evidencia registrada | Qué respalda | Qué no respalda |
| --- | --- | --- |
| [Piloto PNDA del paso 60](conector_senamhi_pnda.md#resultado-de-la-prueba-externa-controlada): un XLSX, HTTP 200, 10.815 bytes, tamaño y SHA-256 releídos, autorización puntual | Funcionamiento de esa descarga e incorporación en aquella operación; descubrimiento de recursos publicado en el informe | Disponibilidad actual, todas las distribuciones, filtros remotos, autenticidad criptográfica o licencia jurídicamente validada |
| [Inspección CSV del paso 69](csv_streaming.md#inspección-real): copia ya adquirida de 50.474.012 bytes, lectura completa y controles físicos registrados | Existencia y lectura local de esa copia, sus valores/estructura en el alcance del informe | Que el método `ConectorSENAMHIPNDA.adquirir` soporte CSV o que se haya probado una API por estación/fecha |
| [Expediente 74](fundamentacion_qa_nivel1.md): PDF del manual obtenido y diccionario inspeccionado, con hashes documentados | Identificación de documentos y contenido revisado según páginas/celdas | Vigencia actual, autenticidad independiente, aplicabilidad científica completa o aprobación de SPICA |
| [Auditoría 77](auditoria_confianza_documental.md) | Separación de confianza documental y ejecución; corrección de parámetros sin fuente y suite offline | Nueva verificación institucional, adquisición o certificación del emisor |

El PASO 78 no abre esos originales ni repite sus hashes o descargas. La prueba
externa puntual autorizada en otro paso no constituye permiso vigente para nuevas
operaciones. Una versión histórica de documentación puede describir un piloto más
limitado; para la capacidad actual se contrasta siempre el código de `adquirir`.

## Qué comprueban las pruebas existentes

| Grupo de archivos en tests/ | Evidencia de las pruebas | Límite de la conclusión |
| --- | --- | --- |
| `test_adquisicion_nucleo.py`, `test_temporal.py` | Coherencia de estados, múltiples IDs, fechas/zonas y preservación literal | Contratos; no adquisición remota |
| `test_transporte_http.py`, `test_reintentos_http.py`, `test_descargas_http.py` | MockTransport/streams inventados, errores HTTP/TLS/timeouts simulados, límites, cancelación; archivos físicos temporales | No prueba handshake TLS, DNS, respuesta o límites actuales de una institución |
| `test_almacenamiento_raw.py`, `test_modelos_md_raw.py`, configuración/cierre/regresiones | Copias y hashes físicos sobre contenido sintético, SQLite real efímero, integridad, fallos, reapertura y rutas | No prueba corte eléctrico, concurrencia hostil, respaldo ni estado presente del RAW operativo |
| `test_catalogo_cientifico.py`, `test_registro_evidencias.py`, `test_planificacion.py` | SQLite temporal, historia, metadatos inventados, relaciones, evidencia y planes condicionados | No inventario institucional ni disponibilidad remota observada |
| `test_integracion_http_raw.py`, `test_integracion_formatos.py`, `test_conector_senamhi_pnda.py` | HTTP simulado, HTML/archivos inventados y continuidad física con RAW efímero | No habilita otro proveedor por cambiar la página ni acredita CSV en el método del conector |
| `test_verificacion_formatos.py`, `test_csv_streaming.py`, `test_consultas_locales.py`, `test_perfilado_meteorologico.py` | Lectura real de fixtures físicas, formatos, límites y perfil SENAMHI | No parsers científicos universales, GIS o calidad científica del producto real |
| QA/QC Nivel 0, catálogo científico, expediente, límites sintéticos y aplicabilidad/confianza | Reglas/contratos documentales y barreras sobre datos inventados | No ejecución científica Nivel 1 ni aprobación institucional |

«Sintética» describe el origen de los datos y la simulación remota, no que SQLite,
hashes o archivos físicos estén simulados en todas las pruebas. Las sondas de
errores/permisos/enlaces incluyen simulaciones y casos locales: no son una auditoría
general de seguridad del sistema operativo.

## Instituciones: situación verificable y prioridad

| Institución | Situación comprobable en el repositorio | Conector y filtros | Prioridad propuesta / requisito |
| --- | --- | --- | --- |
| SENAMHI | Expediente GBON/RBON, descubrimiento PNDA, piloto XLSX y antecedentes CSV locales | Conector público acotado XLSX; sin filtros remotos por estación/variable/período. Consulta local TEMP/HR/PP es otra función | Consolidar el flujo ya conocido y evidencia faltante; no ampliar automáticamente CSV o QA/QC |
| ANA | Núcleo/catálogo/RAW genéricos reutilizables; sin expediente de acceso ni conector ANA localizado | API, portal, autenticación, URLs y filtros: pendientes de verificación | Investigar un producto concreto cuando se autorice; no asumir mecanismos por pertenencia institucional |
| OEFA | Mismos componentes comunes, sin expediente de acceso ni conector OEFA localizado | Mecanismos, permisos, unidades y contratos: pendientes | Seleccionar producto y documentación real antes de programar; sin atribuirle un procedimiento |
| INGEMMET | Componentes genéricos y necesidad de contexto espacial; sin producto/conector geoespacial verificado localmente | Servicio/descarga, CRS, permisos y filtros: pendientes | Priorizar un expediente espacial por la necesidad de GIS, condicionado a evidencia; no asumir un estándar o endpoint |

La preferencia de investigación de INGEMMET es una decisión provisional de SPICA
por necesidad de contexto espacial, no una afirmación de mayor disponibilidad o
facilidad de acceso frente a ANA/OEFA. No se asignan puntuaciones de disponibilidad
sin evidencia. Las tres instituciones permanecen pendientes de verificación.

Véanse el [diagnóstico de contratos y seguridad](auditoria_adquisicion_multiinstitucional.md)
y el [plan de tres incrementos](plan_adquisicion_multiinstitucional.md).
