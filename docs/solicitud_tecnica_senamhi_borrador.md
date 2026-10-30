# Borrador de solicitud técnica a SENAMHI

**Documento para revisión. No enviado.** Antes de presentarlo, completar únicamente
la fecha e identificación del solicitante que correspondan. No se ha designado
destinatario personal, cargo, dirección electrónica o número de expediente. Este
borrador no acredita representación ni autorización de una institución.

---

[Fecha de presentación]

Señores
Servicio Nacional de Meteorología e Hidrología del Perú — SENAMHI

**Asunto: solicitud de aclaraciones técnicas y documentación del producto de
variables meteorológicas de estaciones automáticas GBON/RBON publicado en la PNDA**

De nuestra consideración:

Con fines académicos y de investigación científica ambiental, en el marco del
desarrollo de SPICA — Plataforma de Investigación Científica Ambiental, solicitamos
aclaraciones sobre el conjunto «Variables meteorológicas de las estaciones
automáticas de intercambio internacional», publicado por SENAMHI en la Plataforma
Nacional de Datos Abiertos y referido en nuestros antecedentes como GBON/RBON.

La página de referencia del conjunto es:
<https://www.datosabiertos.gob.pe/dataset/variables-meteorologicas-de-las-estaciones-autom%C3%A1ticas-de-intercambio-internacional-servicio>.
La consulta concierne al recurso CSV y al diccionario cuya hoja se identifica como
`DiccionarioDatos`. Si existen varios recursos o revisiones, agradeceremos indicar
la identificación y edición a las que corresponda la documentación proporcionada.

Nuestro propósito es interpretar correctamente las observaciones, conservar sus
valores y unidades originales y evitar asignarles significados temporales,
instrumentales o de calidad que no estén documentados. En particular, buscamos
distinguir las definiciones del producto de las condiciones de aplicación del
manual MT-DRD-002 versión 02, sin asumir su equivalencia automática.

Agradeceremos las siguientes precisiones, cuando la información esté disponible:

**1. Identidad y ubicación de estaciones e instrumentos**

- Código institucional estable de estación y correspondencia con los campos
  ESTACION e ID del recurso, distinguiendo identificador de registro e identidad física.
- Identificación de las instalaciones y, si existe, historial de cambios de nombre,
  reubicaciones y sustituciones instrumentales, con sus períodos de validez.
- Características instrumentales pertinentes para TEMP, HR y PP, y su relación
  con estaciones y períodos: tipo, configuración, exposición, resolución y
  documentación de calibración e incertidumbre que resulte aplicable.
- Coordenadas, datum/sistema de referencia, unidades y referencia vertical de la
  altitud, así como la fecha o período al que corresponden los metadatos de ubicación.
- Significado, catálogo y formato oficial de UBIGEO. En nuestros antecedentes de
  inspección se registraron representaciones decimales; agradeceremos aclarar su
  interpretación sin presuponer una corrección de los valores originales.

**2. Referencia temporal y continuidad**

- Formato y significado de FECHA y HORA, incluida la interpretación de valores
  de HORA de cinco y seis caracteres registrados en nuestros antecedentes.
- Zona horaria o referencia temporal y, cuando corresponda, cambios históricos.
- Convención de etiquetado horario: inicio, cierre u otra referencia del intervalo.
- Tratamiento de horas repetidas, ausentes, interrupciones y registros revisados.
- Frecuencia de medición, agregación y publicación, y forma de documentar
  continuidad o interrupciones por estación/serie.
- Significado y formato de FECHA_CORTE y su relación con las fechas de
  observación, actualización o revisión del recurso.

**3. Definición de variables y agregados**

- Definición del promedio horario de TEMP y HR: muestreo, estadístico, ventana,
  alineación, requisitos de muestras válidas y reglas de redondeo/publicación.
- Definición del total horario de PP y su unidad oficial exacta. El diccionario
  examinado declara «milimetros por hora»; solicitamos aclarar la magnitud,
  integración y relación entre total e intensidad, sin asumir una conversión.
- Tratamiento de acumulaciones, reinicios y ventanas incompletas de PP, cuando corresponda.
- Convenciones para faltantes, centinelas, no medidos, inválidos y agregados
  parciales, distinguiendo significados por variable/campo y versión del producto.
- Definición/referencia instrumental de HR, tratamiento de saturación y
  condiciones de medición de la temperatura del aire que resulten pertinentes.

**4. Documentación y control de calidad**

- Diccionario oficial aplicable, versionado y fechado, con historial de cambios
  disponible y correspondencia con los recursos publicados.
- Confirmación de vigencia y alcance de MT-DRD-002 versión 02 y de los documentos
  que lo modifiquen, complementen o sustituyan para este producto.
- Aclaración expresa sobre la aplicabilidad de sus subreglas de límites de TEMP
  y HR a los promedios horarios GBON/RBON, incluidas condiciones instrumentales,
  territoriales o ambientales y posibles excepciones.
- Procedimientos de control de calidad efectivamente aplicados al producto antes
  de publicarlo y forma de documentar sus revisiones.
- Significado y vinculación con los registros de códigos o banderines de calidad,
  si existen en este producto o en recursos complementarios.
- Documentación pertinente sobre incertidumbre, tolerancias y política de
  interpretación cerca de los extremos de los criterios, si se dispone de ella.

Solicitamos, de ser posible, respuesta en formato digital y referencias a
documentación oficial con versión, fecha y apartados aplicables. Para tablas de
estaciones, instrumentos o correspondencias, agradeceremos un formato digital
estructurado disponible. Si alguna información no está disponible o no corresponde
al producto, agradeceremos indicarlo y señalar documentación alternativa pertinente.

No solicitamos credenciales de acceso ni información personal innecesaria. Esta
consulta solicita aclaraciones documentales; no presupone errores en las
observaciones ni aprobación institucional de SPICA o de sus reglas de calidad.

Agradecemos la atención a esta solicitud.

Atentamente,

[Identificación del solicitante, por completar antes de su presentación]

---

Referencia interna para revisar el borrador:
[matriz de información faltante y prioridades](matriz_evidencias_senamhi.md).
No adjuntar datos operativos, credenciales ni información privada sin una revisión
específica. No se enviaron comunicaciones durante la preparación de este documento.
