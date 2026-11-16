# RC4 — Contrato de artefactos y fronteras de confianza

Fecha: **2026-11-15**, America/Lima. Base: **5b5b7d4**, rama
feature/suadc-http, inicialmente limpia. RC3 está registrado en ese commit.

## Auditoría previa a las clases nuevas

Se revisaron los tres documentos de cada bloque RC1–RC3, los modelos y sus
pruebas, y la [hoja de ruta 85-M](hoja_ruta_continuidad_arquitectonica_paso85m.md).
La sección RC4 prevé preparación y resultados trazables; el encargo actual
selecciona **descriptores y cotejo en memoria**, sin la transformación sintética
opcional ni publicación, exportación o conservación de derivados.

A = uso directo; B = adaptación pequeña; C = capacidad parcial; D = ausencia;
E = fuera del incremento. Esta clasificación se documenta antes de implementar.

| Capacidad / contrato inspeccionado | Clase | Decisión |
|---|---|---|
| Proyecto y objeto lógico MD-01/02, [modelos RAW](../src/spica/adquisicion/almacenamiento/modelos.py) | A | Reutilizar los objetos de ContextoEntrada. object_id será la identidad lógica del artefacto; no introducir otro ID equivalente |
| Contenido SHA-256 y tamaño; ActivoRAW MD-03 | B | Conservar declaraciones de RC1 y comprobación aportada EvidenciaLocal. Un ID de contenido explícito no identifica institución, proyecto ni objeto |
| Entradas, proyectos, operación y parámetros [RC1](contrato_contexto_comun_rc1.md) | A | Conservar instantáneas; validar_relaciones y combinar_restricciones; sin nuevos DTO MD ni estados de operación |
| Perfiles y comparación [RC2](contrato_perfiles_informacion_rc2.md) | A | EntradaPerfil completo, versiones, unidades y marcos sin normalización |
| Composiciones, restricciones y diagnósticos [RC3](contrato_composicion_operaciones_rc3.md) | A | Inspeccionar con la función existente y conservar su informe; no otro planificador |
| Estado lógico del artefacto y referencias de revisión | D | Contrato mínimo diferente de ejecución, disponibilidad e integridad |
| Integridad y disponibilidad | C | EvidenciaLocal describe comprobación RAW aportada. RC4 no lee archivos; no existe adaptador físico aprobado de preparados/derivados |
| DiagnosticoAdaptacion, EstadoAptitud y EstadoIntegridad | A | Reutilizar vocabulario para cotejo e integridad aportada, sin booleano universal de validez |
| RestriccionQA / RestriccionPropagada | A | Unión por código y orígenes descriptivos; nunca contar copias como evidencia independiente |
| ResultadoCientifico | E | Es resultado de una regla sobre RegistroQA con revisión y aplicabilidad; no representa un dataset ni sirve como artefacto genérico |
| [Traza H](../herramientas/traza_cierre_85h.py) | C | Cierre del informe G y referencia SHA suministrada; no grafo general de artefactos |
| [Conservación J](../herramientas/conservacion_linaje_85j.py), [codec cerrado](../herramientas/_codec_linaje_85j.py) | C | Solo G/H y cuatro roles; tipos nuevos no admitidos. No importar herramientas desde src |
| [Índice 85001](../herramientas/_catalogo_linaje_85j.py), [respaldo K](../herramientas/respaldo_linaje_85k.py) | E | DDL/manifiesto exactos. No añadir tablas, codec ni migraciones; evolución futura versionada y aprobada |
| Revisión/versionado de descriptores | B | Revisión literal de ContextoEntrada, distinta de versiones de perfil, contrato, método, ejecución y generación |
| Grafo explícito de procedencia múltiples entradas/salidas | D | Validación acotada, sin orquestación ni reconstrucción por nombres |

No se ha encontrado una necesidad de romper APIs previas. El paquete nuevo
dependerá de los anteriores; no se introducirán dependencias en sentido inverso.

## Alcance seleccionado

Original, preparado y derivado son clases de descriptor; ninguna crea bytes.
Un informe o JSON QA mantiene su semántica previa y no se convierte en dataset.
La presencia histórica de asset_id, storage_ref o una generación no demuestra
disponibilidad actual, autenticidad del emisor, custodia independiente ni ciencia.

## API experimental 0.1.0

El paquete [spica.artefactos](../src/spica/artefactos/__init__.py) añade tres módulos
y seis dataclasses congeladas con slots. No acepta mapas mutables, callbacks,
expresiones ejecutables, datasets o bytes dentro de sus campos nuevos.

| Modelo | Campos / responsabilidad |
|---|---|
| ReferenciaArtefacto | object_id MD-02 + revision literal de ContextoEntrada + version_contrato. Clave de una revisión, sin ruta física |
| DescriptorArtefacto | entrada_perfil: EntradaPerfil, tipo, contenido_id opcional, estado_logico, formato opcional, generacion_conservacion_ref opcional, restricciones_adicionales, incertidumbres, diagnosticos, version_contrato. revision_cientifica es NO_EVALUADA, no configurable |
| ProduccionArtefactos | operacion: ContextoOperacion, metodo_id, metodo_version, entradas y salidas: tuplas de ReferenciaArtefacto, ejecucion_id opcional, respaldo: Respaldo, restricciones_adicionales, diagnosticos, version_contrato. parametros se obtiene de RC1, sin copia ni evaluación |
| InventarioArtefactos | artefactos, producciones, composiciones RC3, version_contrato. Inventario aportado acotado, sin registro global o persistente |
| InformeArtefacto | descriptor, diagnosticos, restricciones_locales y restricciones_heredadas con orígenes. restricciones calcula su unión sin pérdida |
| InformeLinaje | inventario original, informes por artefacto, informes RC3 completos, diagnosticos globales, orden_linaje, version_inspector. ejecucion_realizada, comprobacion_fisica_realizada y persistencia_realizada son siempre False |

La función [inspeccionar_linaje](../src/spica/artefactos/linaje.py) no ejecuta
productores. Los informes reutilizan DiagnosticoAdaptacion/NivelDiagnostico y
EstadoAptitud. APTO_ESTRUCTURALMENTE expresa coherencia del inventario examinado;
no demuestra transformación, observación válida, permiso o materialización.
autoriza_operacion siempre es False; bool(descriptor/informe) se rechaza.

## Tipos y dimensiones de estado

TipoArtefacto contiene ORIGINAL, PREPARADO y DERIVADO. ORIGINAL puede describir
una entrada sintética o una referencia histórica sin afirmar preservación actual.
PREPARADO representa una futura operación estructural; DERIVADO, un producto
nuevo declarado. Ninguno implica método implementado. El tipo es estable entre
revisiones de un object_id; un preparado o derivado necesita otra identidad
lógica que la de su original.

| Dimensión | Representación | Garantía real |
|---|---|---|
| Ejecución | EstadoOperacion RC1 en la producción | Declaración; RC3 conserva sus condiciones y cierres admitidos |
| Lógica | EstadoArtefacto: DESCRITO, PARCIAL, FINAL_DECLARADO | No identifica existencia física. FINAL_DECLARADO requiere soporte declarativo coherente, sin autenticarlo |
| Disponibilidad física | DisponibilidadArtefacto: DESCONOCIDA, PRESENTE_SEGUN_EVIDENCIA, AUSENTE_SEGUN_EVIDENCIA, NO_COMPROBABLE | Se deriva únicamente de EvidenciaLocal aportada, referida a su comprobada_utc, sin relectura ni vigencia actual garantizada |
| Integridad | EstadoIntegridad PENDIENTE / VERIFICADA en integridad_aportada | VERIFICADA solo por EvidenciaLocal INTEGRO coherente; sufijo aportada obligatorio para interpretar este resultado |
| Conservación | EstadoVerificacion DESCONOCIDO / DECLARADO | Una generación referenciada nunca se marca verificada o conservada por RC4 |
| Revisión científica | EstadoEvaluacionQA.NO_EVALUADA | RC4 no evalúa ni aprueba ciencia |

EvidenciaLocal.INCONSISTENTE mantiene el diagnóstico contradictorio de RC1,
pero no basta para atribuir fallo a una comprobación pertinente de hash. AUSENTE
y NO_DISPONIBLE tampoco son integridad fallida. No hay conversión automática a
EstadoIntegridad.FALLIDA. Una comprobación íntegra de cero bytes es admisible.

sha256_declarado y size_bytes_declarado permanecen en la entrada RC1.
sha256_comprobado_aportado y size_bytes_comprobado_aportado solo exponen las
observaciones de EvidenciaLocal INTEGRO. RC4 no obtiene esas huellas por lectura.
Los originales sin esa evidencia, incluidos los de descriptor completo, quedan
pendientes. Un ORIGINAL FINAL_DECLARADO sin ella es contradictorio.

EvidenciaLocal/asset_id tienen semántica RAW. Se rechazan en preparados/derivados
los asset_id y comprobaciones no desconocidas: aún no existe un adaptador físico
aprobado para ellos. Su disponibilidad e integridad quedan desconocida/pendiente;
no se inventa un MD-03 ni otro DTO físico por comodidad.

## Identidades, revisión e historia

- project_id, contexto_id, object_id, entrada_id y la identidad de recurso siguen
  en sus contratos nativos. Una referencia de artefacto es object_id/revision,
  global en el inventario conforme al alcance MD del catálogo, sin ruta.
- Dos revisiones de un objeto usan referencias diferentes y entradas RC1 con IDs
  distinguibles. RC1 no admite dos descripciones de una entrada con igual clave
  contextual en el mismo inventario. No se modifica esa API para esconder historia.
- contenido_id es explícito y opaco. Identificar bytes por SHA no identifica un
  recurso, institución, estación, proyecto, variable, revisión o permiso.
- Un contenido compartido admite varios objetos y proyectos. Hash/tamaño conocidos
  contradictorios bajo un contenido_id se diagnostican; desconocidos no se rellenan.
  Igual SHA declarado con tamaños conocidos distintos también es contradicción.
- La versión RC4 es 0.1.0 y se rechazan otras. revision es una etiqueta local
  literal, no un número secuencial ni una versión institucional deducida.
- Las versiones RC1, RC2 y RC3, revisión de perfil, contenido, documentación y
  metodo_version conservan sus responsabilidades. La admisión de una versión no
  autentica su procedencia ni autoriza el método.
- operacion_id pertenece a su contexto; ejecucion_id identifica una ejecución
  declarada distinta. Reusar un ejecucion_id en dos producciones o registrar dos
  producciones para una operación es conflicto. No se reabre un terminal RC1.
- generacion_conservacion_ref es una referencia histórica inerte, distinta de todas
  las identidades anteriores. No se abre ni valida J/K a partir de ella.

Duplicados no se corrigen ni sobrescriben: el inventario original se conserva en
InformeLinaje y se diagnostica. No se ofrece un catálogo histórico durable.

## Estados de producción y fronteras de evidencia

PREPARADO/DERIVADO requieren una producción explícita. ORIGINAL no puede ser
salida de una producción de preparado/derivado. Solo se vinculan operaciones
DESCRIPCION_ESTRUCTURAL: un ResultadoQA no es automáticamente dataset derivado.
El método y sus parámetros son datos; nunca se evalúan, importan o despachan.

FINAL_DECLARADO necesita operación CONCLUIDA, ejecucion_id y Respaldo VERIFICADO
aportado. Esto solo admite la **declaración lógica**, sin materialización. RC3
todavía no tiene un cierre técnico admitido de operaciones descriptivas; ese
pendiente permanece visible incluso con un respaldo aportado coherente.

PARCIAL/FALLIDA/CANCELADA solo admiten salidas PARCIAL; su prefijo identificado
puede describirse sin convertirlo en éxito. Una operación INICIADA tampoco soporta
FINAL_DECLARADO. Para estados con resultados, cada salida debe aparecer en
referencias_resultado mediante el entrada_id explícito de la salida. No se
construyen IDs a partir del nombre de archivo ni se adivinan alias.

Hash aportado, comprobación física aportada, autenticidad del emisor, custodia
independiente y validez científica son propiedades distintas. Respaldo VERIFICADO
exige la procedencia nativa correspondiente; no convierte DTO del llamador en
evidencia auténtica. El modelo de confianza es código cooperativo, no Python hostil.

## Recursos, errores y límites

Inventario: hasta 64 descriptores, 32 producciones, 16 composiciones, 64 nodos RC3
en total y 1024 pares de linaje. Producción: hasta 16 entradas y 16 salidas.
Cada literal nuevo tiene como máximo 512 caracteres sin controles; 32
incertidumbres y 64 diagnósticos por descriptor/relación. Se reutilizan cotas
RC1 de políticas y relaciones, y las de medición/inspección RC3 por composición.
Son límites locales, sin reserva de memoria/disco, plazo forzoso o cuota global.

Tipo/versión/cota incorrecta o políticas contradictorias producen excepción
explícita y segura, sin resultado positivo ni truncamiento silencioso. Los errores
de grafo/identidad/estado se conservan como diagnósticos. Un informe por artefacto
no sustituye el diagnóstico global del inventario. No se interpolan rutas,
parámetros, credenciales o errores del sistema en los códigos nuevos. Los DTO
pueden contener metadatos aportados sensibles: no deben registrarse íntegramente.

Véanse el [modelo de linaje](modelo_linaje_artefactos_rc4.md) y la
[auditoría](auditoria_arquitectonica_rc4.md) para integración, pruebas y pendientes.
