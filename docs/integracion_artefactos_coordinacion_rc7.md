# RC7 — Integración de artefactos recuperados y coordinación

Fecha: 2026-11-16, America/Lima. Base 367e95f, feature/suadc-http.
Contrato de inspección **0.1.0**; no introduce un formato persistente.
[Auditoría](auditoria_arquitectonica_rc7.md),
[evidencias y límites](evidencias_cierre_operaciones_rc7.md).

## Alcance y reutilización

El adaptador en [coordinacion.py](../src/spica/artefactos/coordinacion.py) recibe
un resultado de recuperación RC6, una composición RC3, asociaciones explícitas
de entradas con artefactos y una finalidad textual de inspección. No abre archivos,
calcula hashes, llama al motor QA, conserva un catálogo ni ejecuta operaciones.

Se reutilizan:

| Componente | Uso |
|---|---|
| RC1 | ContextoProyecto/Entrada/Operacion, estados, pertenencia y metadatos |
| RC2 | Requisitos de compatibilidad ya declarados en NodoOperacion, evaluados por RC3 con su comparador existente |
| RC3 | Único grafo, orden de precedencia, cuotas, inspección y cierre QA nativo |
| RC4 | Inventario, descriptores, productores, inspeccionar_linaje y unión de restricciones con orígenes |
| RC5 | Informes históricos conservados por RC6; nunca se convierten en InformeQA |
| RC6 | ControlGeneracion, unidad, comprobaciones físicas fechadas y distinción incluido/externo |

Los formatos rc6.generacion.0.1.0, JSON QA 0.1.0 y 85-J/K, SQLite 85001 y los
contratos públicos previos permanecen intactos. No se importan herramientas/tests
desde src. No hay dependencia inversa desde coordinación hacia este adaptador.

## Contratos mínimos

Cuatro dataclasses congeladas con slots; no hay enum nuevo de estados.

| Contrato | Atributos |
|---|---|
| VinculoEntradaRecuperada | operacion_id, entrada_id, ReferenciaArtefacto y version_contrato |
| SolicitudIntegracion | recuperación RC6, composición RC3, vínculos, finalidad, LimitesComposicion reutilizados, max_vinculos y versión |
| RelacionRecuperada | Vínculo, InformeArtefacto RC4 cuando exista, ComprobacionContenido RC6, productor histórico único cuando corresponda y diagnósticos |
| InformeIntegracion | Solicitud original, linaje recalculado, inspección RC3 nativa, vista coordinada conservadora, relaciones, estados de dependencias, diagnósticos, cuotas medidas y cancelación |

inspeccionar_integracion(solicitud, cancelacion=None) es una función de solo
lectura sobre objetos. El informe expone el mismo control de generación y la
fecha de la comprobación física aportada. ejecucion_realizada=False,
comprobacion_fisica_realizada=False y autoriza_operacion=False. bool(informe)
se rechaza: no es un permiso ni una certificación.

La finalidad es un literal explícito, sin evaluación de expresiones. No sustituye
los usos_declarados de los nodos ni las finalidades RC2: se siguen cotejando sus
propósitos, campos, versiones y restricciones mediante los mecanismos nativos.

## Identidades y correspondencias

Una composición pertenece a un ContextoProyecto completo. Los vínculos asocian
**entradas** de operaciones con referencias object_id/revisión RC4; no atribuyen
salidas a un productor nuevo. Esa producción se obtiene exclusivamente de las
relaciones históricas RC4 y debe ser única. No se infiere mediante nombre o SHA.

Se comprueban:

- Proyecto/contexto completo, operación existente y no ambigua, entrada perteneciente
  a esa operación y artefacto/revisión existentes.
- Snapshot de entrada completo igual al recuperado, incluyendo objeto, revisión,
  recurso, procedencias, versiones, declaraciones e incertidumbres.
- Perfiles usados en requisitos RC2 iguales a los conservados para esas entradas.
  El comparador nativo determina su compatibilidad para la finalidad seleccionada.
- Productor/contexto con un ID histórico: no se permite redefinir su estado,
  propósito, parámetros, entradas, referencias o restricciones bajo ese mismo ID.
- Una composición que usa un ID histórico debe conservar su definición. Una
  composición candidata con operaciones nuevas usa otro ID, sin sobrescribir historia.
- Entre operaciones históricas presentes en la candidata no se pueden omitir o
  redefinir sus dependencias conocidas.

Entre procesos se comparan snapshots por **valor tipado**: no se espera que los
objetos Python del productor sobrevivan. Dentro de cada composición, RC3 conserva
sus exigencias de canonicidad por referencia. No se realinean vínculos QA ajenos
por igualdad de hashes ni por un ID parecido.

Cada entrada de cada operación candidata requiere un vínculo explícito. Los
duplicados/contradicciones se diagnostican; no se elige silenciosamente una versión.
Una operación nueva sin identidad histórica puede describirse como consumidora:
eso no crea un evento previo, identidad de operador o ejecución certificada.

## Recuperación y prueba física aportada

Se validan formato/control/fecha, estado de recuperación, inventario completo de
comprobaciones, unicidad de referencias y correspondencia con los incluidos y
externos. Un incluido INTEGRO debe tener tamaño/SHA/lectura completa compatibles
con su informe RC5 y nombre relativo generado. Una bandera VERIFICADA con datos
contradictorios no basta. Una generación incompleta/corrupta/incompatible no
habilita operaciones relacionadas.

El linaje se recalcula mediante RC4 y se contrasta con el aportado, sin aceptar
una caché alterada como fuente de verdad. Se conservan todos los descriptores,
estados, diagnósticos y productores, aunque el cotejo rechace su uso.
Si el inventario no está disponible, la asociación queda pendiente; no se afirma
que el artefacto sea inexistente. Un inventario disponible que no contiene la
referencia/revisión solicitada sí permite diagnosticar esa incompatibilidad.

Las relaciones distinguen contenido incluido y leído por RC6, contenido externo,
ausente, inconsistente y no comprobable. Un externo permanece NO_DISPONIBLE:
no se abre RAW ni se inventa su disponibilidad. Un informe RC5 histórico no
rellena una comprobación RC6 ausente. Tampoco se restaura una ruta histórica.

La comprobación física pertenece a **recuperacion.fecha_utc**, no al momento de
inspección RC7. Si se requiere comprobar disponibilidad posterior debe llamarse
otra vez al lector RC6 autorizado. No se añade una vigencia temporal inventada ni
se ejecuta ese efecto desde el adaptador. Una inspección posterior al retiro de
la raíz sigue siendo una inspección de evidencia histórica fechada; no promete
que un ejecutor futuro pueda abrir el archivo.

## Coordinación conservadora y restricciones

Se llama una vez al inspector RC3 para la composición candidata. Se conserva su
InformeComposicion completo como inspeccion_rc3. La vista coordinacion_integrada
reutiliza los mismos nodos, requisitos, resultados RC2, cierres QA y estados,
añadiendo diagnósticos y restricciones. Nunca habilita una operación que el
inspector nativo hubiera rechazado.

Se recorre **su orden** y las aristas originales: no hay otro algoritmo de orden,
grafo, scheduler o dependencia inventada. El cotejo añade las condiciones de las
asociaciones y propaga las restricciones recuperadas por esas mismas aristas.
Una predecesora rechazada por las nuevas condiciones tampoco acredita a su
dependiente, aunque conserve un cierre QA histórico coherente.

Las restricciones del artefacto incluyen las heredadas por su linaje, y se unen a
las nativas sin rebajar tipos, motivos o usos. Se agrega referencia de origen a la
generación; esa repetición no es evidencia independiente. Si hay variantes de un
código se conservan las fuentes/variantes y se diagnostica incompatibilidad.
No se transfieren políticas entre proyectos u objetos por compartir contenido.

Los usos literales se cotejan como en RC3: bloqueo aplicable implica INCOMPATIBLE;
alcance desconocido con bloqueo implica PENDIENTE_DE_EVIDENCIA. Los nodos
independientes no afectados pueden seguir habilitados declarativamente. Un error
global de identidad, generación, grafo o presupuesto impide todas las habilitaciones.

Las dependencias se informan como pares (DependenciaOperacion, EstadoAptitud):
APTO_ESTRUCTURALMENTE exige la evidencia de cierre admitida por RC3, referencias
existentes y predecesora apta también tras RC7; INCOMPATIBLE representa un bloqueo
o contradicción; PENDIENTE_DE_EVIDENCIA indica requisitos no demostrados. No se
introduce otro estado equivalente ni un algoritmo alternativo de cierre QA.

## Cuotas, versiones y límites

Se aplica el mínimo campo por campo entre LimitesComposicion de la solicitud y
de la composición. Se reutiliza la medición RC3 sobre la solicitud completa:
visitas/texto/profundidad interna acotados antes de inspeccionar. El inspector
nativo aplica las cuotas efectivas de operaciones/aristas/profundidad/sumas QA.
Si los límites efectivos difieren, solo se crea una copia de composición con
esas cotas; la composición original permanece en SolicitudIntegracion, sin cambios.

Vínculos: 64 por defecto, tope duro 128. Se mantienen los demás topes nativos
RC3. La medición cuenta ocurrencias, no memoria RSS o bytes de datasets. No hay
reserva de disco, carga de cuerpos, timeout forzoso ni autenticación del proceso.
Event permite cancelación cooperativa; no cancela componentes externos ni cambia
estados RC1. Si se agota la cuota previa no se simula una inspección RC3 terminada.

Las dependencias privadas de validación/medición/unión están localizadas en este
adaptador y cubiertas por pruebas. No se amplía la API estable para crear una
infraestructura transversal nueva. Un cambio posterior de esos contratos exige
revisar compatibilidad y sus ensayos.
