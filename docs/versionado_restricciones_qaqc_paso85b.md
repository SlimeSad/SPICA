# PASO 85-B — Versionado y restricciones por resultado QA/QC

Fecha local: **2026-11-08, America/Lima**. El ensayo corresponde al
**2026-11-09 UTC**. Complementa la
[auditoría de cardinalidad y contratos](auditoria_contratos_qaqc_paso85b.md).
No aprueba reglas científicas ni autoriza operaciones.

## Dimensiones de versión auditadas

| Dimensión | Antes del 85-B | Decisión actual y significado |
|---|---|---|
| ReglaQA.version | 1.0.0 por cada una de las 22 reglas | Se conserva: condiciones, estados y significado científico limitado no cambiaron |
| VERSION_CONTRATO_QA | 1.0.0, en ResultadoQA/InformeQA | Se conserva: campos, tipos y constructores no cambian; no había versión explícita de catálogo ni motor en este número |
| VERSION_INTERPRETACION | 1.0.0 | Se conserva: gramática, presupuesto y clasificadores compartidos no cambian |
| Emisión/trazabilidad Nivel 0 | Sin versión explícita propia | VERSION_EVALUADOR_NIVEL0=1.0.1, en reglas.py y en el par evaluador_nivel0 de parametros de cada resultado nuevo |
| Anotaciones de restricciones | No existían como política reutilizable | VERSION_RESTRICCIONES_QA=1.0.0 para la función nueva; se exporta aparte con sus anotaciones |
| Catálogo Nivel 0 | Tupla cerrada de descriptores sin versión global | Se conserva; commit/huella de código identifican su distribución, no se inventa equivalencia con otras versiones |

La separación de versión de motor y contrato tiene precedente en readquisición.
Los contratos científicos, experimental y metadatos documentales tienen sus
propias versiones; compartir el literal 1.0.0 no los hace equivalentes. No se
cambian sus constantes, revisiones ni políticas de aprobación.

## Decisión sobre el parche 85-A

85A-01 modificó únicamente la atribución de VAL incompletas en estructura
incoherente: antes cada emisión exponía toda la fila; ahora mantiene su objetivo
TEMP/HR/PP. No cambió número de resultados, criterio de validación, formato,
estado, diagnóstico ni significado de un estado. No cambió la firma o conjunto
de campos de ResultadoQA; sí cambió el **contenido** de valores_originales de
esas emisiones. Un contenido distinto no es por sí mismo un esquema nuevo.

Se introduce **1.0.1 para emisión/trazabilidad**, identificando la conducta
corregida sin declarar 22 reglas nuevas. La primera versión explícita de este
componente se llama 1.0.1 por la corrección localizada; no se afirma que exista
un componente 1.0.0 publicado y marcado en resultados históricos.
El nombre no versiona todo EvaluadorNivel0 ni sus dependencias de lectura.

Los resultados nuevos agregan exactamente el par
`("evaluador_nivel0", "1.0.1")` a parametros, incluidas las emisiones I/N.
Los parámetros anteriores se conservan. Los resultados construidos con el
constructor previo no reciben ese par automáticamente: su emisor sigue
**desconocido**, no se les asigna retrospectivamente 1.0.1.

Los informes 85-A, sus resultados y versiones históricas permanecen intactos.
Para distinguir la conducta histórica se usa HEAD 3535a47 y la huella allí
registrada; no basta el 1.0.0 individual de una regla. No hay resultados
operativos persistidos ni migraciones ejecutadas en este paso.

Política para cambios futuros: modificar una condición requiere revisar la
versión individual afectada; cambiar incompatiblemente campos/estados exige
propuesta de contrato y migración, sin implementarla automáticamente. Una
corrección de atribución manteniendo condiciones se identifica en el emisor.
Modificar el alcance de las anotaciones requiere cambiar su política propia.
Ninguna revisión documental se inventa desde una versión técnica.

## Compatibilidad comprobada

Se evita ampliar la dataclass: ResultadoQA conserva ocho argumentos originales
y version_contrato init=False; InformeQA no cambia. Tampoco cambian modelos,
adaptador o motor. Dataclasses.fields y asdict mantienen las claves previas.
Se comprueba construcción posicional anterior, lectura de parámetros anteriores
y ausencia de atributos obligatorios nuevos.

restricciones_resultado(resultado) es una **consulta pura separada** sobre el
mismo ResultadoQA: devuelve una tupla de RestriccionQA, no un segundo resultado
ni un informe sustituto. Cada anotación tiene codigo, tipo, operaciones y motivo.
No escribe en el resultado, su entrada, ConfiguracionQA o el expediente documental.
No recibe fórmulas, scripts, expresiones ni rutas. Política cerrada en
[restricciones.py](../src/spica/calidad/restricciones.py).

No se incorpora esa tupla en asdict(resultado). Al exportarla, el consumidor debe
conservar también VERSION_RESTRICCIONES_QA y el contexto de la ejecución. Un
consumidor antiguo puede seguir leyendo estados y parámetros; **eso no garantiza
que conserve restricciones en una exportación propia**. No se implementa un
serializador/persistencia ni se promete compatibilidad con sistemas externos.
InformeQA no incorpora una versión nueva de motor por defecto; la versión del
emisor se conoce en sus resultados y el expediente, no debe inferirse de su
version_contrato. No se agregan metadatos de ejecución a informes históricos.

La comparación reproducida con el código HEAD 3535a47 confirmó igualdad de los
169 resultados al excluir solo el par nuevo de parámetros. La suite anterior
es la verificación de consumidores internos, no una certificación científica.

## Política conservadora por resultado

Los tipos son **INFORMATIVA** y **BLOQUEO_USO_DEL_RESULTADO**. El primero explica
alcance sin lista de operaciones. El segundo dice para qué afirmaciones u
operaciones **no sirve este resultado como evidencia**. No autoriza ni deniega
una operación global: la decisión corresponde a otro mecanismo con evidencia,
aplicabilidad y autorización suficientes. No hay atributo autorizado ni ejecutor.
La ausencia de un bloqueo concreto tampoco concede permiso.

| Disparador | Código de anotación | Uso que este diagnóstico no acredita |
|---|---|---|
| Todo ResultadoQA | alcance_estructural, informativa | Describe solo la condición técnica/documental indicada |
| Todo ResultadoQA | sin_validacion_cientifica | Acreditar aptitud científica |
| Todo ResultadoQA | sin_equivalencia_editorial | Afirmar equivalencia editorial de archivos |
| HORA entre los objetivos | hora_sin_transformacion | Construir instantes, asignar zona o completar HORA por inferencia |
| UBIGEO entre los objetivos | ubigeo_sin_interpretacion | Normalizar sufijo, asignar coordenadas o inferir identidad territorial |
| PP entre los objetivos | pp_sin_conversion | Convertir mm↔mm/h o inferir acumulación/intensidad |
| TEMP/HR entre los objetivos | numero_sin_metrologia | Plausibilidad, calidad instrumental o condiciones de medición |
| Regla L0-PROV-* | referencia_sin_verificacion | Verificación física, autenticidad documental o permiso de redistribución |
| Regla L0-ID-* | identidad_ubicacion_no_verificadas | Estación física, CRS o ubicación espacial comprobada |
| Estado NO_EVALUADO | condicion_no_evaluada | Dar la condición por evaluada; motivo exacto del diagnóstico |
| Estado EVALUACION_INCOMPLETA | condicion_incompleta | Dar la condición por concluida; impedimento exacto del diagnóstico |

Los objetivos se leen de valores_originales, no se buscan en un archivo. En
S06, las VAL conservan su único campo, mientras otras reglas reciben toda la
fila como contexto y acumulan restricciones conservadoras sobre ese contexto.
No se infiere que cada uno de esos campos haya sido evaluado. Los códigos son
únicos y el orden de anotaciones es fijo, independiente de iteraciones de sets.

Las anotaciones describen límites de Nivel 0, no certifican que todo metadato
sea desconocido en otros sistemas. Aun con zona/formato declarados, este motor
no asigna instantes; aun con unidad declarada, no convierte precipitación.
No existe un paso automático desde referencias ficticias o declaradas hasta
reglas científicas aplicables. Un ResultadoQA creado por el llamador tampoco
es evidencia autenticada por ser una instancia de la dataclass.

Ejemplo real de la fixture S10: VAL-002/PP, literal **1.50**, estado
COMPROBACION_SATISFECHA, diagnostico numero_finito_interpretable. La consulta
conserva ese estado y añade pp_sin_conversion y sin_validacion_cientifica.
S08 mantiene HORA **12345**, sin completar ceros; S09 mantiene UBIGEO **007777.0**.
TEMP **-9999** y HR **500** pueden satisfacer gramática y conservar
numero_sin_metrologia: no se crean límites ni conclusiones meteorológicas.

## Motivos de no evaluación y límites del contexto

| Diagnóstico existente | Lectura admisible y metadato/impedimento |
|---|---|
| formato_documental_no_disponible | NO_EVALUADO: no se suministró el formato esperado con referencia; no es aprobación |
| zona_horaria_desconocida | NO_EVALUADO: referencia de zona no aportada; no asignar zona por geografía |
| instante_no_determinable_sin_zona / conversion_de_instantes_fuera_alcance | NO_EVALUADO: falta de referencia o conversión deliberadamente fuera de alcance |
| identidad_fisica_no_acreditada | NO_EVALUADO: no hay mapping literal pertinente; no inventar código |
| referencia_desconocida / documento_no_disponible | NO_EVALUADO: procedencia/documento faltante, sin buscarlo por red o RAW |
| licencia_desconocida_o_documento_no_aplicable | NO_EVALUADO: no hay mención pertinente; no autorizar redistribución |
| entrada_sin_procedencia_propia_para_contrastar | NO_EVALUADO: no hay segunda referencia para contraste |
| vacio_sin_numero / vacio_sin_formato_comprobable | NO_EVALUADO: literal vacío; no se supone medición ni causa |
| no_finito_tratado_por_regla_especifica / sin_numero_para_comprobar_finitud | NO_EVALUADO: delegación o precondición ausente; no duplicar como aprobación |
| campo_no_disponible | INCOMPLETA: campo no aportado en la entrada; no afirmar ausencia en un original no leído |
| estructura_no_evaluable | INCOMPLETA: entrada estructuralmente incoherente; conservar tupla bruta y objetivo |
| presupuesto_numerico_excedido | INCOMPLETA: límite de recursos, no número científicamente erróneo |
| nombre_estacion_no_disponible / metadatos_incompletos | El estado diferencia campo ausente (I) de texto vacío (P); no decidir solo desde el código |

Los motivos se copian sin reemplazarlos por mensajes genéricos o aprobaciones.
Alerta documental, problema técnico y N/I siguen siendo estados diferentes.
La etiqueta informal CUMPLE corresponde a COMPROBACION_SATISFECHA; NO_EVALUABLE
no es un enum nuevo. Una evaluación individual completa no exige que todas las
otras condiciones o dimensiones científicas estén resueltas. Un InformeQA con
motivo eof puede ser INCOMPLETA: comprobar siempre estado y alcance.

## Condiciones para ampliar el sistema

Se mantienen separados QA estructural, cotejo de procedencia documental,
interpretación de metadatos, QA científico y decisión operacional. No se modifican
metadatos_documentales, inspectores XLSX/DOCX, HTTP, RAW o SQLite; no se activan
reglas Nivel 1. No hay umbrales, outliers, clima, comparación espacial, estaciones
vecinas, transformaciones temporales, normalización, corrección o imputación.

La política de límites es reutilizable como explicación, pero el evaluador actual
sigue especializado en el esquema SENAMHI. No se declara soporte de observaciones
ANA, OEFA, INGEMMET u otras disciplinas por compartir anotaciones. Para nuevos
productos se necesitan contratos/adaptadores y aplicabilidad documentados.

Antes de ampliar o persistir resultados: revisar identidad con contexto estable,
configuración/versión de emisor, exportación explícita de restricciones, gramática
de nuevos perfiles y sus consumidores. Si exige nuevos campos obligatorios,
deserialización o migración, preparar propuesta separada. No convertir la consulta
de restricciones en un motor de permisos. Ninguna de las 29 brechas se cierra aquí.

**APTO CON RESTRICCIONES** para revisar trazas y política de anotaciones offline.
Pendientes: revisión de la política por los responsables, estrategia futura de
exportación/contexto, documentación científica aplicable y autorización de cada
operación. No se avanza al PASO 85-C.
