# PASO 84-D: reconciliación de evidencia PNDA/SENAMHI

Fecha: **2026-11-05**. Propuesta para revisión; no registra respuestas, aprobaciones,
estaciones nuevas ni cambios de catálogo. Acompaña al
[inventario auditado](auditoria_metadatos_pnda_paso84d.md) y la
[matriz de brechas](brechas_metadatos_pnda_paso84d.md).

## 1. Evaluación de los contratos existentes

Se inspeccionaron los modelos, persistencia y política documental de catálogo,
los modelos de aplicabilidad científica y los adaptadores/evaluador de
interoperabilidad. **No se demostró una necesidad actual de implementar código.**
La información todavía no acreditada no justifica rellenar campos, crear tablas
de correspondencias o relajar el evaluador. Las limitaciones que requieren una
necesidad futura concreta se indican expresamente.

| Aspecto | Componente reutilizable | Alcance real y límite |
|---|---|---|
| Original recibido y procedencia de adquisición | `ActivoRAW`, `DeclaracionRAW`, `EvidenciaAdquisicion` | Separan activo, adquisición, hash, recurso y documento. La instantánea antigua no se reescribe con evidencia nueva; no se abre el almacén para aplicar esta propuesta |
| Referencia documental de catálogo | `ProcedenciaCatalogo` | Referencia, revisión UTC, método y evidencia textual. La fecha de revisión no es vigencia científica ni fecha del documento; las marcas del llamador no autentican emisor |
| Recurso y edición | `RecursoCatalogo`, `ProductoCatalogo`, `adquisicion.catalogo.EvidenciaDocumental` | Representan publicación, producto/recurso, versión y revisiones opcionales, capacidades y licencia/referencia. No incluyen un manifiesto relacional que certifique qué edición XLSX se aplica a qué CSV |
| Referencia científica localizada | `calidad.modelos_cientificos.ReferenciaCientifica` | Permite versión/fecha documental opcionales y SHA de referencia. Un SHA aportado no realiza verificación física |
| Contenido, interpretación y desconocidos | `calidad.aplicabilidad.modelos.EvidenciaDocumental` y `AfirmacionAplicabilidad` | Conservan localización, naturaleza documental/sintética, nivel, incertidumbres, contradicciones y pendientes. Es una clase distinta de la evidencia de adquisición, aunque comparten nombre |
| Estación y variable | `EstacionCatalogo`, `VariableCatalogo` | Fuente/producto e IDs literales, red/nombre, coordenadas/CRS/altitud, unidad/frecuencia/tipo y diccionario. No crean identidad física, historial de instrumentos o vigencia por propiedad |
| Descripción espacial/temporal | `MarcoEspacial`, `CRSDeclarado`, `Respaldo`, `MarcoTemporal`, `PeriodoTemporal` | Separan originales y declaración/verificación por aspecto; admiten fechas civiles, vigencia de metadatos y límites explícitos. Es representabilidad, no acreditación del dato |
| Nueva revisión | `RecursoInteroperable.revision_metadatos`, `sustituye_revision`, `version_institucional`, `correspondencias` | Retienen instantáneas y referencias. `correspondencias` es declarativa; no demuestra equivalencia física ni es una tabla automática estación–código |
| Contradicción y resultado anterior | `contradicciones_declaradas`, `ResultadoAptitud`, `ResultadoOperacion` | Bloquean nuevas aptitudes contradictorias y retienen entradas/evidencia/versiones. No modifican el resultado anterior ni conceden autorización científica |

Fuentes de implementación:
[catálogo](../src/spica/adquisicion/catalogo/modelos.py),
[persistencia](../src/spica/adquisicion/catalogo/persistencia.py),
[política documental](../src/spica/adquisicion/catalogo/documental.py),
[referencias científicas](../src/spica/calidad/modelos_cientificos.py),
[aplicabilidad](../src/spica/calidad/aplicabilidad/modelos.py),
[contratos de interoperabilidad](../src/spica/interoperabilidad/modelos.py),
[adaptadores](../src/spica/interoperabilidad/adaptadores.py) y
[evaluador](../src/spica/interoperabilidad/evaluador.py).

### Historial y actualización: capacidades y límites

El [catálogo científico existente](catalogo_cientifico.md) conserva entidades y
su diario de revisiones. `actualizar(entidad, revision_esperada=..., motivo=...)`
exige revisión vigente y procedencia estrictamente posterior, mantiene historial
y rechaza cambios de identidad, código original o vínculos. No equivale a una
actualización autorizada en esta auditoría: es una descripción estática de su API.

`registrar_documental` solo admite fuente, producto, recurso y capacidad. No es
una API genérica para reconciliar estaciones o variables. Cambios materiales
protegidos se devuelven como `CONTRADICCION` sin reemplazar lo vigente; otros
cambios documentales permitidos pueden generar una revisión histórica. La API
no decide por sí sola si una corrección es científicamente verdadera.

Si aparece un código institucional nuevo para un nombre antes ambiguo, no debe
reutilizarse el ID de registro CSV ni renombrarse una identidad anterior para
simular continuidad. Registrar otra identidad, o documentar una relación explícita
entre identidades existentes, requiere evidencia y procedimiento aprobado. No
existe hoy un servicio automático de reconciliación física de estaciones.

### Vigencia y períodos civiles

`MarcoTemporal.vigencia_metadatos` puede expresar un intervalo, pero el evaluador
actual solo conserva sus referencias: **no selecciona automáticamente una ficha
de estación/instrumento según la fecha de observación ni verifica su aplicabilidad
temporal**. Un campo presente no demuestra que ese control se haya ejecutado.
Se necesita seleccionar explícitamente la evidencia válida por época antes de
una operación dependiente de ella, bajo revisión humana; su automatización futura
requiere diseño y pruebas propios.

`DisponibilidadCatalogo` requiere extremos datetime, mientras `PeriodoTemporal`
admite date o datetime. El período civil histórico del CSV no puede introducirse
en el adaptador meteorológico como disponibilidad sin inventar una hora. Sigue
siendo un límite de adaptación identificado en 84-C, no un motivo para asignar
UTC o una medianoche. Cuando se apruebe adaptar perfiles civiles, deberá tratarse
la correspondencia de tipos con una necesidad y regresiones concretas.

El adaptador actual traslada las coordenadas catalogadas como **declaradas**;
su entrada `EstacionCatalogo` no expresa por separado verificación de identidad,
coordenadas y calidad. Recibir una ficha institucional no promoverá automáticamente
esos respaldos a verificados. Una integración futura de respaldos y vigencias
detallados puede necesitar un adaptador adicional o una composición explícita de
los contratos existentes; no se afirma que ese paso ya esté implementado.

Los campos específicos de vigencia de código, vida operativa, instrumento,
referencia vertical, resolución/rango y control de calidad pueden preservarse en
el documento identificado y sus afirmaciones. No todos tienen representación
estructurada ni evaluador especializado en los modelos actuales. No se crean
ahora campos o modelos sin una evidencia concreta que consumir.

## 2. Reglas para reconciliar sin borrar historia

| Clase de información | Tratamiento propuesto |
|---|---|
| Dato original | Conservar cuerpo, identificadores, FECHA/HORA/UBIGEO y unidad literal. Ninguna corrección documental lo transforma retroactivamente |
| Metadato declarado | Conservar valor, fuente, localización y alcance; la declaración no es una comprobación científica |
| Evidencia documental | Identificar documento/copia, fecha de recepción, versión/fecha editorial conocida o desconocida, hash comprobado y apartados. Mantener por separado contenido, integridad y autenticidad |
| Interpretación | Explicitar método, revisión y premisas. No tratar hipótesis de ceros perdidos o equivalencia de estaciones como evidencia institucional |
| Validación | Describir qué control se ejecutó y qué propiedad acredita. Hash, lectura de celda, vigencia y validación científica tienen alcances diferentes |
| Contradicción | Conservar las afirmaciones enfrentadas y sus alcances. No elegir por mayor fecha de descarga, palabra VERIFICADO o parecido de nombres |
| Información sustituida | Crear revisión distinguible y relación de sustitución local, con motivo y evidencia. La revisión y sus resultados anteriores siguen accesibles |
| Información desconocida | Mantener `None`/estado desconocido y pregunta pendiente. Una respuesta ausente o documento no disponible no demuestra inexistencia institucional |

Propuesta de expediente de recepción, **documental y no ejecutable**, para futuras
respuestas autorizadas:

| Campo de seguimiento | Registro requerido |
|---|---|
| Emisor y referencia | Institución/custodio acreditado, número o localizador original si existe; no inventar expediente |
| Identidad documental | Título, edición, fecha, localización, copia/hash y fuente de adquisición; separar fecha de recepción de vigencia |
| Alcance | Producto/recurso, variable, código/nombre de estación, instrumento, red y períodos que la respuesta realmente cubra |
| Afirmación literal | Texto/celda/página concreta; distinguir cita, resumen e interpretación del revisor |
| Contraste | Afirmación anterior, referencia/revisión y coincidencia, corrección, contradicción o información adicional |
| Impacto | Filas R/S/T/V afectadas de la matriz y dimensión del contrato; pendientes que permanecen |
| Decisión humana | Rol revisor, fecha, justificación y suficiencia para el uso específico, sin atribuir aprobación institucional a SPICA |
| Historia | Identificadores de revisiones anteriores/nuevas, resultados conservados y versiones del evaluador utilizadas |
| Autorización | Estado operativo independiente; una aclaración documental no autoriza descarga, escrituras, GIS ni QA/QC científico |

Este cuadro no crea otra base, archivo de reglas, expresión ejecutable o mecanismo
de autorización. No se registran en él respuestas ficticias.

## 3. Secuencia futura propuesta, no ejecutada

1. Recibir/obtener la evidencia por un mecanismo previamente autorizado; identificar
   emisor, copia, referencia y alcance. No realizar ahora solicitudes ni descargas.
2. Verificar técnicamente la copia con límites y procedimiento adecuados a su
   formato. No usar la extensión para declarar contenido compatible.
3. Localizar la afirmación y distinguir su versión/fecha editorial, vigencia,
   recepción, inspección e integridad. Si falta una versión, conservar `None`;
   una nueva recepción local sí puede tener revisión técnica propia.
4. Vincularla a producto/recurso/estación/variable/período **solo hasta el alcance
   acreditado**. Una afirmación para otro producto queda fuera de aplicación,
   sin alterar la descripción del producto PNDA.
5. Comparar con las revisiones conservadas. Diferente fecha/vigencia puede indicar
   épocas distintas, no necesariamente contradicción. Si ambos documentos hablan
   de la misma propiedad/época con valores excluyentes, conservar el conflicto.
6. Revisar qué brechas se cierran y cuáles siguen pendientes. La recepción del DOCX
   no cierra por defecto todas las filas; un catálogo de códigos no verifica
   coordenadas ni calibra instrumentos.
7. Preparar una nueva instantánea y evaluación en memoria, con revisiones y
   respaldo explícitos. No mutar la evidencia de adquisición ni los resultados
   utilizados en 84-C. Conservar tanto `ResultadoAdaptacion` como `ResultadoAptitud`
   si se requieren originales adicionales y reproducción de la decisión.
8. Antes de persistir o ejecutar operaciones, revisar el cambio y su autorización.
   Utilizar posteriormente el historial existente bajo sus restricciones; no
   inferir permisos de una etiqueta de aprobación o consistencia documental.

Las fechas/revisiones hipotéticas del procedimiento no son registros reales. No
se ejecuta ninguna actualización, migración o simulación sobre SQLite operativo.

## 4. Consultas técnicas a SENAMHI para revisión futura

Se conserva el [borrador técnico ya preparado](solicitud_tecnica_senamhi_borrador.md).
No se reescribe, envía ni presume presentado. El destinatario concreto, fecha,
canal institucional y número de trámite siguen pendientes. El siguiente índice
consolida su cobertura y añade el vínculo explícito CSV–XLSX–DOCX y derechos:

| Consulta agrupada | Preguntas para revisión | Brechas |
|---|---|---|
| Q1. Ediciones y auxiliares | ¿Qué edición del CSV corresponde a cada diccionario y documento de metadatos? ¿Pueden aportar el DOCX aplicable o aclarar su disponibilidad, con versión/fecha y relación de recursos? ¿Qué sustituciones afectan cada período? | R01–R04, V08 |
| Q2. Identidad y vigencia | ¿Cuáles son los códigos originales de estación y su correspondencia con ESTACION, ID de registro y redes? ¿Cómo se delimitan instalación física, homónimos, renombramientos, traslados y períodos de operación/validez? | S01–S03, S06 |
| Q3. Localización y metrología | ¿Qué CRS/datum, ejes/unidades, referencia vertical, fecha y calidad corresponden a LONGITUD/LATITUD/ALTITUD? ¿Cómo se relacionan sensores, calibración e incertidumbre con estación y época? ¿Cuál es la codificación/versión de UBIGEO y su representación en el CSV? | S04–S08, V05 |
| Q4. Referencia temporal | ¿Qué significan FECHA y ambas longitudes de HORA? ¿Qué zona/reglas históricas, ventana, etiqueta y extremos aplican? ¿Cómo se distinguen registro institucional, FECHA_CORTE, publicación, revisión, duplicados, reloj e interrupciones? | T01–T07 |
| Q5. Variables y faltantes | ¿Cuál es la definición, muestreo, agregación, resolución y redondeo de TEMP/HR/PP? ¿Qué magnitud/unidad representa el total horario de PP? ¿Cómo se informan reinicios, acumulados parciales, vacíos y centinelas por edición? | V01–V05, T04–T05 |
| Q6. Procesamiento y QC | ¿Qué etapas y controles se aplicaron a este producto/revisión, y qué códigos o banderines pueden vincularse a sus registros? ¿Qué alcance y vigencia de MT-DRD-002 corresponden a los promedios publicados? | V06–V08, R04 |
| Q7. Procedencia y condiciones de uso | ¿Quién custodia y emite las definiciones? ¿Qué texto/edición de licencia se aplica a cada distribución y copia/revisión, con qué atribución y condiciones para el uso/redistribución previstos? | R05–R06 |

No se presupone que SENAMHI disponga de todo historial, catálogo o certificado
enumerado. Una respuesta que identifique una limitación también es evidencia de
su alcance; no permite suplir lo desconocido. No se solicita información personal,
tokens, credenciales o acceso a servicios no autorizados.

## 5. Decisiones que permanecen abiertas

Pueden continuar, con revisión, la organización del expediente, localización de
afirmaciones y diseño de casos sintéticos para necesidades futuras. Requieren
evidencia adicional y autorización las fusiones de identidades, selección automática
por vigencia, localización temporal, conversiones, procesamiento científico,
persistencia de nuevas revisiones o adquisición del DOCX.

El esquema vigente permite preservar los antecedentes sin modificar el núcleo;
no implementa toda la reconciliación científica prevista. Esta auditoría deja
esa diferencia explícita y conserva las brechas como pendientes. No se activa
ninguna regla científica ni se modifica un resultado histórico.
