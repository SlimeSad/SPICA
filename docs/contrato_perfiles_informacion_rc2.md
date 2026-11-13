# RC2 — Contrato de perfiles comunes de información

Elaborado el **2026-11-13**, America/Lima. Base: **ac9c6fd**, rama
feature/suadc-http. Contrato y comparador experimental **0.1.0**.
Resultados y auditoría: [compatibilidad](compatibilidad_estructural_rc2.md) y
[auditoría RC2](auditoria_arquitectonica_rc2.md).

## Alcance y responsabilidades

Se recupera la sección 4 de la [hoja de ruta 85-M](hoja_ruta_continuidad_arquitectonica_paso85m.md):
AM04, perfiles/adaptación y correspondencias declaradas, conservando originales,
unidades, faltantes, referencias y restricciones. Un método que no necesita una
referencia no obliga a inventarla. La relación con M23/M26 no significa su cierre.

RC2 aborda descripción estructural, semántica declarada y compatibilidad para
una finalidad. Identidades y procedencia se **componen** de contratos anteriores;
no se implementan transformación ni validación científica. Tampoco se describen
observaciones con otro DTO que compita con RegistroQA u ObservacionLocal.

El paquete [interoperabilidad.perfiles](../src/spica/interoperabilidad/perfiles/__init__.py)
solo trabaja con objetos ya construidos. No lee datasets o evidencia, resuelve
URLs, comprueba hashes, persiste perfiles, carga reglas ni ejecuta expresiones.
No cambia RC1, motores QA/QC, transporte, almacenamiento o JSON QA 0.1.0.

## Inventario y justificación de las adiciones

Se revisaron los contratos y sus consumidores antes de definir la nueva frontera.

| Necesidad | Contrato existente | Clasificación | Decisión RC2 |
|---|---|---|---|
| Proyecto, objeto, entrada y contenido | [ContextoEntrada y ContextoProyecto](../src/spica/contextos/modelos.py), MD-01/02, referencia asset_id y EvidenciaLocal | Reutilizable mediante adaptador | EntradaPerfil conserva el ContextoEntrada completo por referencia; no redefine contenido, activo ni proyecto |
| Identidad del recurso y publicación | [RecursoInteroperable / IdentidadRecurso](../src/spica/interoperabilidad/modelos.py) | Reutilizable directamente | Se accede por entrada.recurso; no se agrupan localizadores ni servidores |
| Variables y estaciones | [VariableCatalogo / EstacionCatalogo](../src/spica/adquisicion/catalogo/modelos.py) | Reutilizable directamente / mediante marcos existentes | CampoInformacion referencia VariableCatalogo; MarcoEspacial conserva identidad de sitio, coordenadas y respaldos. No se copia otro catálogo |
| Campos y tipos genéricos | atributos_declarados, RegistroQA y FormatoDocumentadoQA | Insuficiente | Atributos solo da nombres; los formatos QA son específicos. Se añade CampoInformacion, sin universalizar los 16 campos SENAMHI |
| Unidad literal, frecuencia y medición | VariableCatalogo | Reutilizable directamente, insuficiente para estados de unidad | Se conservan sus literales; UnidadPerfil distingue cinco estados. respaldo_variable se aporta expresamente; no se eleva la confianza del catálogo automáticamente |
| Significado, tipo, ámbito, agregación y calendario | [AfirmacionDocumental](../src/spica/metadatos_documentales/modelos.py), DatoContextoCientifico y DatoDocumentadoQA | Reutilizable como evidencia de origen; insuficiente para descriptor genérico | Son afirmaciones/localizadores documentales, dimensiones científicas o formatos QA específicos. DeclaracionPerfil solo une literal opcional con Respaldo existente; no sustituye sus evidencias ni las autentica |
| Dimensión física documentada | No hay catálogo general de magnitudes/unidades acreditadas | No disponible | Solo un literal con referencia aportada y Respaldo VERIFICADO; no hay ontología ni inferencia dimensional |
| Tiempo y espacio | MarcoTemporal, PeriodoTemporal, MarcoEspacial, CRSDeclarado, Respaldo, evaluar_aptitud | Reutilizable directamente | El comparador delega referencias en el evaluador existente y conserva su ResultadoAptitud |
| Faltantes documentados | PerfilVariable y LimitesPerfil del [perfilador](../src/spica/perfilado/modelos.py) | Insuficiente | Esos conteos y marcadores candidatos son observaciones/heurísticas, no una convención acreditada. Se añade una tupla opcional de literales y respaldo, sin ejecutar reemplazos |
| Procedencia y confianza | ProcedenciaCatalogo, Respaldo, EstadoVerificacion | Reutilizable directamente | No se introduce otro estado de autenticidad ni se convierte una referencia en verificación física |
| Restricciones y finalidad de operación | RestriccionQA, combinar_restricciones, ContextoOperacion | Reutilizable mediante adaptador | Unión conservadora; operación opcional retenida, sin transición de estado ni autorización |
| Perfil versionado y finalidad de cotejo | ConfiguracionContexto y OperacionPropuesta | Insuficiente | Son configuración de contexto o preparación espacial/temporal; no describen campos ni requisitos de cotejo. Se añaden PerfilInformacion y FinalidadCompatibilidad |
| Conversión, GIS, QA1, persistencia y permisos efectivos | Subsistemas específicos / trabajo futuro | Fuera del alcance | No se implementan ni activan |

No se detectó contradicción entre contratos que obligue a romper una interfaz.
Las contradicciones de las fixtures se conservan como diagnósticos; no justifican
reescribir los modelos estables. El diseño original completo/actas no disponibles
localmente en 85-M siguen sin sustituirse por requisitos inventados.

## Contratos nuevos

Definiciones en [modelos.py](../src/spica/interoperabilidad/perfiles/modelos.py):
dataclasses congeladas con slots, tuplas tipificadas y validación acotada.

| Contrato | Campos y responsabilidad |
|---|---|
| DeclaracionPerfil | valor opcional y Respaldo. Sirve para tipo literal extensible, significado, dimensión, ámbito, calendario y agregación; no es un tipo Python ejecutable |
| UnidadPerfil | estado, literal, respaldo, dimension_fisica y contradicciones. Un conflicto explícito necesita causas y una referencia de su constatación aportada |
| CampoInformacion | nombre original, tipo, variable opcional, respaldo_variable, significado, unidad, valores_ausentes, respaldo_ausentes, agregacion y calendario. Frecuencia/tipo de medición se toman del VariableCatalogo referenciado |
| PerfilInformacion | identificador, version local, tipo_recurso, campos, ambito, restricciones, incertidumbres y version_contrato |
| FinalidadCompatibilidad | identificador de finalidad, descripcion, pares de campos requeridos, pares de perfil/versión admitidos, aspectos cerrados, dimensión espacial/temporal opcional y requisitos explícitos de igualdad de recurso/contenido/sitio |
| EntradaPerfil | entrada RC1 y perfil; verifica el vínculo, sin copiar las identidades ni alterar metadatos desconocidos |
| ResultadoCompatibilidad | ambas entradas/perfiles, finalidad, diagnósticos, restricciones completas, ResultadoAptitud delegado y operación RC1 opcionales; versión/limitaciones fijas y estado derivado |

AspectoCampo enumera TIPO, VARIABLE, SIGNIFICADO, UNIDAD, DIMENSION_FISICA,
TIPO_MEDICION, FRECUENCIA, AUSENTES, AGREGACION y CALENDARIO. TIPO es obligatorio;
SIGNIFICADO exige VARIABLE y DIMENSION_FISICA exige UNIDAD. La correspondencia
de nombres de campo es explícita y uno a uno. No interpreta mappings como
correspondencias científicas entre variables ni admite callbacks.

Un perfil puede ser parcial o estar vacío; la falta de un campo requerido produce
incompatibilidad para esa finalidad. No se certifica que las columnas existan en
un archivo: se comparan descripciones. Cuando RecursoInteroperable declara una
lista no vacía de atributos, no se permite vincular campos ajenos a esa lista.

## Identidad, versiones y procedencia

Se distinguen identificador/versión de perfil, versión de contrato RC2, revisión
de entrada RC1, revisión de metadatos del recurso, versión institucional,
version_contenido, objeto, asset_id y SHA/tamaño. Ninguno sustituye a otro.
Una versión local es un literal requerido, sin inventar la versión institucional
desconocida. Se admiten únicamente los pares de perfil/versión enumerados por
la finalidad; admitir dos versiones no evita comparar sus campos.

Dos perfiles con el mismo identificador y versión deben tener la misma definición,
incluidos respaldos/restricciones. Cambiar esa definición requiere otra versión.
Solo se detectan conflictos entre los objetos suministrados: no hay registro de
unicidad global, historia, migrador o persistencia.

La identidad de variable conserva fuente, producto, id_interno y codigo_original.
La unidad no puede contradecir silenciosamente la del catálogo. Un nombre o
significado similar no acredita correspondencia entre variables de productos
distintos; no se implementa aún un catálogo de equivalencias.

## Unidades, faltantes e incertidumbres

| EstadoUnidad | Invariante y tratamiento |
|---|---|
| ACREDITADA | Literal y Respaldo VERIFICADO con evidencia aportada; no implica autenticación independiente |
| DECLARADA | Literal y Respaldo DECLARADO; insuficiente para un cotejo de unidades positivo |
| DESCONOCIDA | Sin literal, con estado DESCONOCIDO; nunca se rellena desde el nombre de la variable |
| CONTRADICTORIA | Causas no vacías y Respaldo VERIFICADO de la constatación aportada; impide compatibilidad si la finalidad evalúa unidad |
| NO_APLICABLE | Sin literal ni dimensión, con justificación documental aportada VERIFICADA; diferente de desconocida |

La dimensión física solo se declara con Respaldo VERIFICADO. Unidad y dimensión
coincidentes no demuestran equivalencia de variables o condiciones de medición.
Una dimensión puede estar documentada mientras la unidad siga desconocida: se
conservan ambos estados y el cotejo de unidades permanece indeterminado.
No hay conversión Celsius/Kelvin, mm/mm/h, concentración, escala o dimensión.

valores_ausentes=None significa convención desconocida; () significa declaración
de ausencia de marcadores; ("",) incluye el vacío literal. Se cotejan conjuntos
de marcadores exactos, conservando su orden original en cada descriptor. No se
infieren centinelas del perfilador ni se reemplazan valores.

Las incertidumbres textuales RC1/perfil se retienen completas en las referencias
del resultado. No se evalúan como expresiones, reglas o números. Los respaldos
insuficientes de aspectos requeridos producen indeterminación. Un texto libre
no se interpreta automáticamente como bloqueo; las restricciones de uso deben
expresarse con RestriccionQA y operaciones afectadas.

## Tiempo y espacio

MarcoTemporal conserva instante/fecha, intervalo, resolución, zona, convención,
incertidumbre y roles de publicación/adquisición/vigencia separados. Un literal
es tiempo declarado; interpretación/periodo respaldados y referencias suficientes
permiten cotejo; datetime sin zona, interpretación incompleta o contradicciones
mantienen su diagnóstico; marco ausente es desconocido. No se introduce otro reloj
ni enum que compita con los estados de respaldo y aptitud existentes.

Frecuencia del catálogo, calendario y agregación son declaraciones distintas de
la resolución y de la frecuencia de publicación. No se usan unas para completar
otras. El evaluador anterior contrasta instantes con offsets explícitos cuando
corresponde; RC2 no genera fechas convertidas, asigna zonas ni cambia valores.
Resoluciones acreditadas distintas son incompatibles para la alineación literal
sin agregación elegida en RC2; se conserva además el diagnóstico nativo anterior.

MarcoEspacial conserva geometría, CRS de cada ámbito, coordenadas, extensión,
precisión, incertidumbre, ubicación y respaldos. Se reutilizan todos sus controles;
no se repite un algoritmo GIS. Un resultado positivo solo significa preparación
documental, no coincidencia espacial. Si se exige el mismo sitio, se coteja la clave
fuente/producto/identificador_ubicacion respaldada y no ambigua; no se interpretan
nombres ni UBIGEO ni se inventan correspondencias entre productos.

## Integración RC1 y límites

EntradaPerfil verifica tipo de recurso e identificador de perfil conocido, y
ámbito fuente/producto de las variables cuando está declarado. Un producto
desconocido en el recurso no se trata como contradictorio ni se completa desde
el producto conocido de una variable: la comparación queda pendiente de evidencia.
Un perfil desconocido en RC1 sigue
desconocido y diagnosticado, no se completa por efecto del vínculo. Se retienen
contexto/proyecto, objeto, entrada/revisión, recurso/procedencia, activo,
hash/tamaño, evidencia local, contenido y versiones por referencia.

Se conserva y exige respaldo del ámbito declarado de cada perfil. La admisión
de versiones por una finalidad no verifica aplicabilidad científica común entre
sus ámbitos ambientales; no se infieren correspondencias geográficas o normativas.

comparar_perfiles acepta opcionalmente una ContextoOperacion descriptiva que
contenga **los mismos objetos de entrada** y cuyo proposito coincida exactamente
con la descripcion de finalidad. Conserva esa operación y sus restricciones.
No cambia su estado ni la configuración QA. La comparación entre proyectos
distintos es posible sin una operación conjunta RC1 y no fusiona sus identidades.

La unión estable de restricciones de proyecto, entradas, perfiles y operación
rechaza códigos conflictivos; jamás reduce un bloqueo. Un bloqueo se aplica al
identificador exacto de finalidad presente en sus operaciones. Los bloqueos de
otras operaciones se retienen, sin reinterpretar comodines o conceder permiso.
ResultadoCompatibilidad.autoriza_operacion siempre es False y bool(resultado)
se rechaza. Los DTO aportados no son una frontera de seguridad contra código
Python hostil ni una firma de aprobación documental.

Cada perfil tiene hasta 64 campos; cada finalidad, 64 pares de campos y 64 pares
de versiones; 32 marcadores por campo y 32 incertidumbres por descriptor. Literales
nuevos: hasta 512 caracteres, sin controles; marcador vacío permitido. Un resultado
admite hasta 4096 diagnósticos y la unión de hasta 128 restricciones según RC1.
Exceder una cota o conflicto de estructura provoca excepción explícita, sin
truncar evidencia ni generar un resultado positivo. Son cotas locales de objetos
en memoria, no límites globales de RAM/CPU ni de grafos heredados.

No hay persistencia, serializador, registro global de perfiles, permisos efectivos,
presupuesto compuesto ni motor general de procesamiento. Toda extensión de
equivalencias, formatos especiales o evidencia institucional necesita revisión.
