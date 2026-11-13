# RC1 — Contrato común de proyecto, entrada y operación estructural

Fecha de elaboración: **2026-11-13, America/Lima**. Base: **ce4218b**, rama
feature/suadc-http. Contrato experimental **0.1.0**, en proceso confiable y uso
secuencial. El encargo actual ratifica este alcance local de la
[hoja de ruta 85-M](hoja_ruta_continuidad_arquitectonica_paso85m.md).
No ratifica una ERS ausente ni inicia módulos científicos.

## Responsabilidad y reutilización

El paquete [spica.contextos](../src/spica/contextos/__init__.py) describe relaciones
en memoria. Crear o cotejar un contexto no abre archivos, catálogos, red o motores.
No es un gestor de proyectos, registro persistente, ejecutor de planes ni sistema
de permisos. No se modifican interfaces previas, JSON QA 0.1.0 o esquemas SQLite.

Antes de introducir las envolventes se inspeccionaron los contratos y consumidores:

| Contrato existente y consumidores | Capacidad reutilizada | Ausencia que resuelve RC1 |
|---|---|---|
| [ProyectoCientifico / ObjetoCientifico / ActivoRAW](../src/spica/adquisicion/almacenamiento/modelos.py), catálogo RAW y pruebas MD | MD-01 identifica proyecto; MD-02 objeto y pertenencia; MD-03 activo físico separado del objeto/hash | MD no contiene contexto de aplicación, configuración o referencias de operación. Se componen los DTO; asset_id solo es referencia opcional, no otro activo |
| [RecursoInteroperable](../src/spica/interoperabilidad/modelos.py), adaptadores y evaluador | Identidad de recurso/Fuente, revisión, procedencia, versiones institucionales y marcos originales | No relaciona proyecto/objeto con una entrada contextual o evaluación. Se conserva la instantánea por referencia |
| [EvidenciaLocal](../src/spica/adquisicion/readquisicion/modelos.py), decisión de readquisición | Estado, activo, fecha, tamaño/hash observados y procedencia de comprobación aportada | RC1 contrasta metadatos si se aporta evidencia, sin repetir ni autenticar la comprobación |
| [ConfiguracionQA / LimitesQA / ResultadoQA](../src/spica/calidad/modelos.py), motor/exportación/consumo | Configuración cerrada, presupuesto de QA y resultado nativo | No ofrecen contexto de proyecto ni relación entre operaciones independientes. No se añade otro evaluador |
| [RestriccionQA](../src/spica/calidad/restricciones.py), política y consumidor QA | Código, tipo, operaciones afectadas y motivo | Se reutiliza como anotación de límites de uso del resultado; la envolvente agrega restricciones sin inventar un sistema de autorización |
| [ContextoExportacionQA](../src/spica/calidad/exportacion.py), consumidor y conciliador | Espacio, evaluación, entrada de fila, configuración e incertidumbres | Adaptación explícita de IDs RC1, conservando su semántica de fila; no otra identidad de exportación |
| [PlanConsulta](../src/spica/adquisicion/planificacion/modelos.py) y ResultadoDecision | Propuestas; ejecutable=False / autoriza_red=False | Permanecen independientes y declarativos. RC1 no traduce selectores a HTTP ni activa readquisición |
| [OperacionPropuesta / ResultadoOperacion](../src/spica/interoperabilidad/operaciones.py) | Condiciones documentales de una asociación espacial/temporal; operacion_ejecutada=False | No contienen proyecto, entradas/versiones ni ciclo de operación común. Se mantienen con su propósito, sin reutilizar dimensión GIS como tipo de ejecución |
| [ContextoCientifico](../src/spica/calidad/modelos_cientificos.py), catálogo y habilitación documental | Datos de aplicabilidad con referencias científicas | No es contexto de aplicación, usuario o proyecto; no se usa para otorgar ejecución o reemplazar contexto RC1 |
| [ContratoEjecucion85G](../herramientas/piloto_integracion_85g.py) y traza H | Referencia de diseño de estados, presupuesto y linaje acotados | Contrato de herramienta fijo, sin DECLARADA; no se importa desde src ni se promueve a API general |

MD significa aquí los tres modelos de datos documentados e implementados en RAW,
no módulos de gestión completos ni una aprobación integral recuperada de la ERS.
La inspección de [catalogo.py](../src/spica/adquisicion/almacenamiento/catalogo.py)
confirma que object_id es único en ese catálogo, incluso entre proyectos. La nueva
comprobación en memoria conserva esa condición.

## Envolventes y campos

Solo se añaden cinco dataclasses congeladas con slots y dos enumeraciones. Las
referencias a objetos existentes no duplican tablas, observaciones o datasets.
Las declaraciones literales se validan sin normalizarlas.

| Envolvente | Campos principales | Significado / frontera |
|---|---|---|
| ConfiguracionContexto | perfil, revision, parametros, max_entradas, max_referencias_resultado, version_contrato | Configuración estructural opaca. Tupla de pares textuales, sin expresiones ejecutables. Cotas de referencias, no cuota global de memoria/CPU/disco |
| ContextoProyecto | contexto_id, proyecto: ProyectoCientifico, configuracion, restricciones, version_contrato | Identidad del contexto separada de project_id. proyecto conserva schema_version/nombre/contexto/estado originales, incluidos desconocidos |
| ContextoEntrada | entrada_id, proyecto, objeto: ObjetoCientifico, recurso: RecursoInteroperable o None, revision, tipo_recurso, perfil_estructural, version_contenido, asset_id, sha256_declarado, size_bytes_declarado, evidencia_local, restricciones_adicionales, incertidumbres, version_contrato | Identifica una entrada y su descripción local, sin leer contenido. El objeto puede representar un dataset cuando kind lo declara; no se atribuye esa clase a todo archivo |
| ContextoOperacion | operacion_id, proyecto, entradas, tipo, proposito, parametros, limites_qa, configuracion_qa, restricciones_adicionales, estado, diagnosticos, referencias_resultado, version_contrato | Declaración de operación. QA_NIVEL0 compone límites/configuración QA existentes; DESCRIPCION_ESTRUCTURAL no acepta presupuesto QA ajeno. Ningún tipo tiene un despachador automático |
| VinculoResultadoQA | operacion, entrada_id, referencia_resultado, resultado: ResultadoQA; contexto_exportacion y restricciones derivados; version_contrato | Relación explícita con un resultado ya recibido. Conserva el resultado nativo por referencia y restricciones de todos los antecesores más las nativas QA |

No se añade un DTO de proyecto/objeto/activo/fuente, observación, resultado QA,
usuario, autorización, linaje persistente o presupuesto científico paralelo.
EstadoAdaptacion y DiagnosticoAdaptacion/NivelDiagnostico también se reutilizan.
TipoOperacion y EstadoOperacion son necesarios para la declaración transversal:
los estados de descarga, incorporación, preparación de plan o evaluación QA
describen otras dimensiones; el enum de la herramienta G no es API de src.

## Identidades, versiones y pertenencia

- project_id pertenece al modelo MD. contexto_id distingue configuraciones y
  escenarios de trabajo del mismo proyecto; no autentica a una persona.
- object_id conserva su pertenencia MD y unicidad en el inventario cotejado.
  asset_id no es object_id, entrada_id, ruta o SHA; no se atribuye un activo a dos
  objetos diferentes. La existencia real del catálogo no se consulta.
- entrada_id y operacion_id tienen ámbito contexto_id. Repetir el mismo ID dentro
  del mismo inventario contextual es conflicto, incluso si el contenido coincide.
- Dos proyectos pueden tener entradas con igual SHA y procedencia distinta.
  No se fusionan ni heredan permisos. Dos operaciones sobre una entrada mantienen
  sus propias identidades de evaluación; no se alinean automáticamente.
- Todas las envolventes aceptan exactamente version_contrato=0.1.0. Una versión
  diferente se rechaza, sin conversión o negociación implícita.
- schema_version del proyecto, revision de configuración/entrada, revisión de
  metadatos, versión de contenido y versión institucional siguen separadas.
  Una versión desconocida permanece None; no se sustituye por la versión RC1.

[validar_relaciones](../src/spica/contextos/relaciones.py) coteja inventarios
explícitos y acotados: contextos ausentes, duplicados, proyecto/objeto redefinido,
activo atribuido a objetos distintos y entrada ausente o revisada de otra forma.
Una operación debe usar entradas con el mismo contexto completo, no solo con el
mismo project_id. El diagnóstico no crea registros ni resuelve conflictos.
No hay unicidad global, detección concurrente o comprobación de existencia fuera
del inventario aportado. Para mantener historia se requieren otros servicios.
Los diagnósticos del cotejo agrupan códigos/campos repetidos: no son un conteo
de cada entidad afectada ni un inventario forense completo. Las instantáneas
aportadas permanecen disponibles para localizar las relaciones concretas.

## Preparación e integridad de entrada

estado se deriva como DESCRITO, PARCIAL o CONTRADICTORIO de EstadoAdaptacion.
DESCRITO significa descripción construida, sin afirmar aptitud. Ausencia de
recurso, procedencia, perfil o versión de contenido produce diagnóstico FALTANTE;
contradicciones documentales o evidencia local INCONSISTENTE se conservan como
contradicción. El perfil no se deduce de las columnas o la institución.

Un hash/tamaño declarado no constituye integridad comprobada. Si se aporta una
EvidenciaLocal INTEGRO, su activo debe corresponder y los valores declarados
conocidos deben coincidir con los observados aportados. Esto **solo valida
coherencia de metadatos**. RC1 no calcula hashes de archivos, abre storage_ref,
confirma RAW, prueba autenticidad documental ni verifica vigencia de la evidencia.
Un tamaño cero es admisible; nunca se infiere que un recurso existe por su hash.

La instantánea original mantiene condiciones de uso, incertidumbres, unidades,
tiempos y coordenadas disponibles. None sigue desconocido. No se interpreta
automáticamente texto legal ni se convierten unidades/zonas; no se reconstruyen
HORA, UBIGEO, códigos de estación o atributos científicos.

## Estados declarados, errores y restricciones

EstadoOperacion tiene DECLARADA, PLANIFICADA, INICIADA, CONCLUIDA, PARCIAL, FALLIDA y
CANCELADA. [cambiar_estado](../src/spica/contextos/relaciones.py) devuelve otro
snapshot; no modifica el anterior ni ejecuta/cancela un motor.

```text
DECLARADA → PLANIFICADA → INICIADA → CONCLUIDA / PARCIAL / FALLIDA / CANCELADA
DECLARADA / PLANIFICADA → CANCELADA
```

Los terminales no se reabren. Una repetición necesita otro ID de operación.
No se permiten referencias de resultado antes del inicio. CONCLUIDA requiere
referencias y ningún diagnóstico faltante/contradictorio de la operación;
PARCIAL requiere causa y resultados identificados; FALLIDA/CANCELADA requieren
causa y pueden conservar referencias de un prefijo. Un resultado QA incompleto
no puede vincularse como parte de una operación concluida. Estas reglas detectan
contradicciones, **no certifican ejecución, EOF, cobertura completa de reglas o
veracidad del historial**. No sustituyen InformeQA o evidencia de un ejecutor.

restricciones es una unión derivada de proyecto, entradas y operación. Un código
repetido con idéntico contrato se conserva una vez; si cambia tipo, operaciones o
motivo, se rechaza como contradicción. No existe un parámetro para borrar las
restricciones heredadas. Los resultados agregan la política QA existente y
rechazan también conflictos con ella. Los diagnósticos son tipados y los errores
estructurales usan códigos fijos sin interpolar secretos o rutas del llamador.

## Adaptación QA, presupuesto y confianza

[adaptadores_qa.py](../src/spica/contextos/adaptadores_qa.py) acepta solo el perfil
qa0-senamhi-16, revisión estructural 1.0.0. Requiere recurso/procedencia explícitos y
sin contradicciones. Los parámetros QA deben expresarse en ConfiguracionQA;
parámetros opacos en proyecto/operación se rechazan en ese perfil. Configurarlos
no llama a reglas. Una versión de contenido desconocida no impide comprobar
literales QA0: se conserva como incertidumbre, sin atribuir evidencia científica.

Correspondencia con el linaje de exportación existente:

| Campo QA 0.1.0 | Referencia RC1 |
|---|---|
| espacio_id | contexto_id, no identidad autenticada de usuario ni project_id implícito |
| evaluacion_id | operacion_id dentro del contexto |
| entrada_id | entrada_id RC1 + ':' + numero_registro original explícito, patrón de 85-G |
| configuracion / incertidumbres | ConfiguracionQA y declaraciones/faltantes disponibles |

La posición es una referencia estructural de fila, no un código científico
inventado. Se valida la compatibilidad ASCII/longitud del DTO QA; no se recortan
ni transforman IDs incompatibles. El proyecto MD y la revisión RC1 permanecen
en la envolvente, fuera de un JSON que no tiene esos campos.

El vínculo contrasta fuente/recurso/asset/hash declarados, procedencia original
cuando existe, regla seleccionada y estado. validar_vinculos_qa comprueba lote,
referencias de cierre, presupuesto QA de registros/resultados, duplicaciones y
descripciones contradictorias de una misma fila. No demuestra correspondencia
con bytes de un archivo que no se ha leído. Las cotas de contexto son 16 entradas
y 256 referencias por defecto, con topes 64/4096; inventarios de cotejo admiten
128 contextos y 256 entradas/operaciones. No equivalen a RSS, reserva de disco,
plazo forzoso o presupuesto compuesto entre operaciones. No hay dataset cargado
para construir estas envolventes.

**El JSON QA estable solo exporta las restricciones QA nativas.** Las adicionales
RC1 permanecen en VinculoResultadoQA, junto con proyecto/entrada/operación. No se
ofrece exportación RC1 ni persistencia del vínculo: transferir solo ese JSON
no transfiere todo el contrato RC1. Un futuro consumidor transversal debe conservar
la envolvente o diseñar un formato aprobado; no puede declarar que heredó todas
las restricciones por recibir únicamente el JSON QA. No se modifica ese esquema
ni se habilita un uso operativo para ocultar esta frontera.

Un ID válido, un contexto, un estado o resultado estructural **no es permiso**.
autoriza_operacion es siempre False y bool(contexto/operación/vínculo) se rechaza.
Identidad de usuario, cuentas, roles, permisos y autorización concreta quedan
fuera; un responsable declarado tampoco sería autenticación. El código opera
en un proceso confiable: frozen/slots y cotejos no son sandbox contra Python
hostil, falsificación de evidencias o cambios forzados de objetos. No se registran
valores ni se incorpora un detector universal de credenciales: los llamadores
deben aportar metadatos públicos y no secretos.

Pruebas y evidencia: [integración RC1](integracion_contextos_rc1.md),
[auditoría RC1](auditoria_arquitectonica_rc1.md) y
[pruebas ejecutables](../tests/test_contextos_rc1.py).
