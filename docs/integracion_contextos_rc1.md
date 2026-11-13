# RC1 — Integración sintética de contextos

Fecha: **2026-11-13, America/Lima**. Base **ce4218b**, feature/suadc-http.
Implementación descrita en el [contrato RC1](contrato_contexto_comun_rc1.md);
resultados de cierre en la [auditoría](auditoria_arquitectonica_rc1.md).

## Tramo implementado

Se selecciona el tramo de estructura QA0 en memoria. No hace falta repetir
HTTP→RAW→persistencia para demostrar el vínculo de identidades. No se ejecutan
85-G/H/J/K ni se fabrican informes suyos; se reutiliza su frontera de diseño,
incluida la distinción entre entrada de archivo y posición de fila.

```text
ProyectoCientifico / ObjetoCientifico + RecursoInteroperable + restricciones
        ↓ composición sin E/S
ContextoProyecto → ContextoEntrada → ContextoOperacion
                                         ↓ declaración de inicio
RegistroQA sintético → evaluar_registro existente → ResultadoQA nativo
                                         ↓ vínculo puro RC1
VinculoResultadoQA + ContextoExportacionQA + restricciones completas RC1
                              ↓ JSON QA nativo en el ensayo
exportar_resultado_json → consumir_exportaciones → conciliar_lotes
       [solo alcance QA0; envolvente RC1 retenida por separado]
```

No se agrega un motor de evaluación o ejecución. El generador existente evalúa
una condición estructural seleccionada por ConfiguracionQA. Los contextos y
adaptadores únicamente preparan/cotejan referencias recibidas; no llaman al
evaluador, al exportador ni al consumidor por construirlos.

## Escenario transversal realmente probado

La prueba
test_dos_proyectos_dos_operaciones_mismo_contenido_y_linaje_no_alineado de
[test_contextos_rc1.py](../tests/test_contextos_rc1.py) construye:

| Elemento | Proyecto/contexto A | Proyecto/contexto B |
|---|---|---|
| MD-01 / contexto | proyecto-A / contexto-A | proyecto-B / contexto-B |
| MD-02 | objeto-proyecto-A, kind=dataset explícito | objeto-proyecto-B, kind=dataset explícito |
| Entrada local | entrada-1 en contexto-A | entrada-1 en contexto-B |
| Identidad de recurso declarada | Fuente SPICA-SINTETICA/fixture-rc1, producto-ficticio, recurso literal con espacios | Misma identidad declarada; no se atribuye publicación institucional |
| Contenido declarado | SHA compartido de bytes inventados en memoria; sin verificación física | Mismo SHA declarado; no fusiona entradas/proyectos |
| Operaciones | operacion-1 y operacion-2 | operacion-1 dentro de otro contexto |
| Presupuesto por operación | LimitesQA: 4 registros y 8 resultados | Mismos límites, independientes |
| Regla del ensayo | L0-EST-001 del registro QA0 existente | Misma regla, ejecución independiente |
| Restricciones | bloqueo-fixture heredado + restricciones QA nativas | Mismos tipos; nunca permisos transferidos |

Cada llamada real al generador QA0 produce un diagnóstico de la regla elegida.
Se vincula por referencia, declara cierre con una referencia y coteja el lote.
Después se usa el exportador y consumidor existentes: tres documentos aceptados
en sus respectivos ámbitos, con tres resultado_id diferentes, aunque los
ResultadoQA nativos sean iguales. El conciliador devuelve NO_COMPARABLE al
comparar las evaluaciones independientes, sin alinearlas ni fusionarlas.

Eso demuestra composición contextual y conservación en memoria de restricciones,
no ejecución de las 22 reglas en ese escenario, cobertura de un CSV, equivalencia
de observaciones ni validación científica. La regresión completa ejercita las
pruebas previas por separado; sus cantidades no se suman a los tres resultados
de esta fixture como si fueran nuevas observaciones.

La prueba test_dos_filas_se_exportan_y_consumen_con_identidades_distintas usa dos
registros y produce entrada-1:1 / entrada-1:2 en ContextoExportacionQA. Un único
lote con dos documentos es aceptado por el consumidor, sin colisión de entrada.
El ID RC1 del recurso permanece entrada-1. Esta distinción se comprobó leyendo
el consumidor y la adaptación ya usada por 85-G antes de cerrar el incremento.

Otros ensayos conservan distinto origen declarado para igual SHA, contextos
distintos de un mismo proyecto, resultados parciales e identidad de activo
separada del contenido. Las pruebas de EvidenciaLocal construyen metadatos
inventados de comprobación: no afirman haber comprobado un archivo real.

## Evidencia adversarial

| Riesgo | Comprobación implementada / rechazo observado |
|---|---|
| Proyecto inválido, ausente o redefinido | Tipo/ID; inventario de contextos; discrepancias de descripción MD |
| Entrada inconsistente, revisión distinta o sin inventario | Pertenencia a contexto completo y cotejo contra la instantánea de entrada |
| Colisión de IDs | Contexto, entrada y operación duplicados; object_id global y activo atribuido a objetos distintos |
| Igual contenido en proyectos distintos | Entradas y evaluaciones conservadas; SHA no se utiliza como clave lógica |
| Repetición de operación o diagnóstico | Operacion_id duplicado se diagnostica; referencias/resultados repetidos no inflan el lote |
| Versiones/perfiles incompatibles | Versiones RC1 exactas, perfil/revisión QA soportados y versiones previas conservadas |
| Estado contradictorio | No resultado antes de inicio, cierre sin referencia, conclusión con faltante o resultado incompleto |
| Parcial, fallo, cancelación | Causa obligatoria, referencias preservadas; terminales no reabren. No se simula cancelación de un motor |
| Restricción omitida o alterada | Herencia derivada; conflicto de código/tipo/operaciones/motivo bloquea construcción del vínculo |
| Procedencia desconocida / metadatos insuficientes | None y diagnósticos conservados; no se vincula QA si falta recurso/procedencia/perfil o hay contradicción |
| Origen/hash/activo QA contradictorios | Cotejo del resultado y procedencia original contra la entrada; no física nueva |
| Parámetros/presupuesto incompatibles | QA exige contratos existentes tipados; rechaza parámetros opacos y cotas inválidas/excedidas |
| Resultado de otro proyecto/contexto/operación | validar_vinculos_qa rechaza el vínculo ajeno, aunque el contenido sea igual |
| Misma fila con otros datos o líneas | Se rechaza una descripción de RegistroQA contradictoria bajo la misma posición |
| Mutación accidental | Dataclasses nuevas congeladas; tuplas tipadas; referencias a objetos originales; resultado y JSON previo idénticos tras adaptación |
| Red, SQLite o escrituras por RC1 | Procesos hijos con auditoría Python instalada antes de importar, que deniega socket.*, sqlite3.connect, aperturas de escritura y operaciones de archivos/directorios del ensayo |
| Orden de importaciones | Procesos independientes: primero spica.contextos; primero calidad/interoperabilidad. Composición y exportación sin efectos en ambos |

Las pruebas no constituyen sandbox de seguridad para código hostil. Un llamador
puede mentir en un DTO o desprender la envolvente deliberadamente; RC1 no acredita
hechos a partir de declaraciones autocertificadas. Las barreras de efectos y
autorización de ejecución siguen pendientes de RC3.

## Recursos y límites

Las envolventes usan referencias y slots, sin asdict/deepcopy, contenido de
archivo o carga de datasets. Configuración y listas de referencias tienen cotas;
el lote QA también contrasta los límites QA de resultados y registros. No hay
promesa de memoria constante del motor previo, presupuesto conjunto, reserva de
espacio, SLA o escalabilidad medida. El cotejo puede reconstruir pequeñas tuplas
de restricciones/diagnósticos; no mantiene un índice global persistente.

Una comprobación con sys.getsizeof en Python 3.15.1 de .venv midió los siguientes
tamaños superficiales de las envolventes de la fixture:

| Objeto | Bytes superficiales |
|---|---:|
| ConfiguracionContexto | 80 |
| ContextoProyecto | 72 |
| ContextoEntrada | 152 |
| ContextoOperacion | 136 |
| VinculoResultadoQA | 88 |

Las cinco carecen de __dict__ y conservan por identidad las referencias de
proyecto/entrada/operación. Es una medida de estos objetos en ese intérprete,
**no memoria total**, tamaño de objetos referenciados, RSS o benchmark de escala.
No se ha copiado ni medido un dataset operativo.

Los contextos no reciben descriptores abiertos ni instancias de motores: no los
abren o cierran. La propiedad de lectura/cierre sigue en el llamador y los motores
existentes; RC1 no añade un gestor de recursos prestados o cancelación efectiva.
Los ensayos RC1 son en memoria. Los procesos hijos se esperan con timeout y sin
archivos auxiliares propios. Los temporales sintéticos del resto de la suite
son propiedad de sus fixtures previas; no se borran datos para transformar un
fallo en éxito. La limpieza de 179 directorios vacíos identificados de la primera
pasada, sin barrido general, se documenta en la auditoría. El registro de
verificación es solo un log temporal, ajeno a RAW y a documentos institucionales.

No se accede al CSV PNDA, RAW, staging, SQLite operativo o evidencia privada.
No se añade dependencia, descarga o conexión. Las rutas operativas conocidas en
tests previos son casos negativos de rechazo, no destinos usados por RC1.

## Compatibilidad y frontera de exportación

Los contratos anteriores no cambian. El esquema JSON QA sigue 0.1.0; el resultado
QA y la política de restricciones conservan 1.0.0. La envolvente RC1 conserva
restricciones adicionales y relaciones que ese JSON no puede representar.
El ensayo las retiene en VinculoResultadoQA: pasar únicamente el JSON a otro
proceso **no transportaría el contexto RC1 completo**. No existe exportador o
persistencia RC1, ni se promueve ese JSON como exportación científica general.

La referencia de linaje está demostrada en memoria y en el ámbito QA existente.
No se afirma integración con el codec J, catálogo 85001, restauración K o custodia
operativa. Tampoco se han ejecutado ContratoEjecucion85G ni InformeEjecucion85G:
importar herramientas desde src sería una inversión de dependencia innecesaria.

Las conexiones M03/M16/M26/M32 conservan su significado y estado pendiente;
la tabla exacta y el cierre de verificaciones constan en la
[auditoría RC1](auditoria_arquitectonica_rc1.md).
