# RC15 — Vínculo documental acotado para revisión de aplicabilidad

Fecha: **2026-11-23**, America/Lima. Base `2cfb3a4`, RC14 registrado.
[Piloto](piloto_vinculo_documental_rc15.md),
[auditoría y verificaciones](auditoria_arquitectonica_rc15.md).

## Definición recuperada, sin cambio de significado

La fila M26 de la [matriz original 85-F](matriz_dependencias_integracion_paso85f.md)
define literalmente el emisor/destinos **C20 → C21/C24/C19** y su situación:

> evaluar_uso es diagnóstico; no conversor a formato QA, AfirmacionAplicabilidad o permiso

Su estado era **P para una vinculación explícita revisada**. La condición de esa
fila es evitar puentes que conviertan COINCIDE/VERIFICADO en aprobación y
seleccionar evidencia pertinente y revisada. No prescribe convertir todos los
documentos a QA ni exige implementar simultáneamente todos los destinos.

La [auditoría 85-M](auditoria_continuidad_arquitectonica_paso85m.md) mantiene M26
prevista. La [trazabilidad RC12](matriz_trazabilidad_conexiones_rc12.md), apartado
M26, precisa selección/localizadores, identidad documental/producto/revisión,
período aplicable, revisión humana trazable, contradicciones y destino preciso.
Su aceptación requiere que la evidencia pertinente alimente únicamente el campo
y uso revisados, sin reconstruir HORA, UBIGEO, unidades o permisos. RC14 recomienda
esta frontera sin resolverla con su habilitación técnica.

Los componentes son C20 (afirmaciones, expedientes, evaluación de uso y cotejo),
C21 (QA0), C24 (catálogo de reglas y aplicabilidad documental) y C19
(interoperabilidad y perfiles). RC15 toma **solo C20 → C24**, preparando la
dimensión PRODUCTO de un ExpedienteProducto. C21/C19 y el fundamento científico
de un método no se declaran integrados por este incremento.

## Selección de producto y finalidad

| Candidato implementado | Correspondencia con M26 | Decisión |
|---|---|---|
| ProductoCatalogo SENAMHI–PNDA GBON/RBON y su descripción contextual | Tiene identidad fuente/producto y destino nativo ExpedienteProducto en C24 | Seleccionado para vincular identidad, no magnitudes ni calidad del CSV |
| ResultadoQA / exportación JSON QA0, contratos existentes RC8/RC9 | Acredita producción/consumo técnico; no contiene un campo de fundamento documental científico revisado | No forzar el esquema JSON QA ni presentar una exportación como ciencia |
| PerfilInformacion / RecursoInteroperable de C19 | Puede describir campos/respaldos, pero introducir ahora interpretación de unidades o tiempo requeriría otra selección y evidencia | Pospuesto; sin conversión ni equivalencia inferida |

Producto nominal existente:
`PRODUCTO_GBON_RBON_ID` de
[modelos PNDA](../src/spica/adquisicion/conectores/senamhi/modelos.py), con
`FUENTE_SENAMHI`. Se conserva exactamente el identificador publicado, incluido
su escape porcentual. El adaptador rechaza otro producto/fuente.

Finalidad única: **`revision_documental_identidad_producto_pnda`**.
Destino único: **DimensionAplicabilidad.PRODUCTO**, para preparar una posterior
revisión de aplicabilidad. No es INTERPRETACION_VARIABLE, autorización de ciencia,
equivalencia editorial, redistribución ni ejecución de una regla.

El piloto usa la identidad nominal real y **solo instancias/metadatos sintéticos**.
`edicion-ficticia-rc15` no es una versión SENAMHI acreditada. No se selecciona
ninguna revisión institucional real ni se leen las adquisiciones operativas.
Una versión desconocida real debe permanecer None y bloquea esta preparación.
El descubridor PNDA existente construye ProductoCatalogo sin asignar `version`:
su salida actual no supera esa condición por sí sola. No se rellena a partir de
la revisión de metadatos, del hash o de la edición ficticia del ensayo.

## Contratos reutilizados y necesidad mínima

El núcleo documental ya representa la afirmación y su evaluación, y C24 ya
representa la salida. Falta el vínculo explícito entre ambos con proyecto,
artefacto/revisión, finalidad y antecedente de revisión. No se modifican esos
contratos: un adaptador de checkout compone sus APIs públicas.

| Contrato existente | Uso RC15 |
|---|---|
| MD-01/02 y ContextoProyecto/ContextoEntrada RC1 | Proyecto/contexto, objeto lógico, entrada canónica y versiones separadas; identidad independiente del hash/ruta |
| ProductoCatalogo, ProcedenciaCatalogo | Snapshot del producto y antecedente trazable, sin abrir catálogos SQL |
| IdentidadRecurso/RecursoInteroperable | Fuente, recurso y producto exactos, revisión de metadatos y edición declarada |
| EntradaPerfil/DescriptorArtefacto RC2/RC4 | Referencia object_id/revisión y contenido_id de la descripción; estado lógico, restricciones y diagnósticos |
| ContextoOperacion RC1 | Operación descriptiva declarada para esta finalidad; no productor institucional observado |
| ExpedienteMetadatos/AfirmacionDocumental/FuenteDocumental | Referencia completa, localizador, literal, nivel, naturaleza, incertidumbres, relaciones y restricciones originales |
| evaluar_uso / ResultadoUso | Nuevo diagnóstico CONSULTA_DOCUMENTAL, conservado íntegro; no permiso |
| ControlArchivo/CotejadorDocumental 84-L | Control previo confiable y cotejo físico/literal nuevo; reutiliza lector seguro e inspector DOCX existentes |
| RestriccionPropagada y unión nativa RC4 | Conserva restricciones RC1/RC4/operación con orígenes y sus conflictos |
| AfirmacionAplicabilidad/ExpedienteProducto C24 | Salida nativa con una dimensión PRODUCTO y su EvidenciaDocumental original, sin nueva infraestructura de procedencia |

RC5/RC6 fueron revisados: publican/conservan bytes sintéticos y perfiles cerrados.
Este caso **no necesita publicar ni conservar un artefacto**, por lo que no se
crea una generación RC6 o un almacén RC5 redundante. El documento se comprueba
con el cotejador físico específico existente, limitado a 1 MiB. La descripción
del producto no se materializa y su integridad física no se afirma.

RC8/RC9 capturan exportación/consumo JSON QA0; no acreditan esta relación
documental ni revisión humana. RC14 tampoco la acredita y no se invoca para
admitir documentos. Sus APIs/políticas siguen intactas.

## Interfaz experimental de checkout

Acceso: [herramientas/vinculo_documental_rc15.py](../herramientas/vinculo_documental_rc15.py).
Sin reexportaciones en src, CLI general, configuración global o base de datos.
Versión propia **0.1.0**, no versión institucional ni formato persistido.

```python
vincular_producto_rc15(solicitud, *, revision, cotejador)
```

SolicitudVinculoRC15 contiene producto, descriptor del artefacto, operación,
expediente opcional, ID de afirmación, ID de control, finalidad y versión.
RevisionVinculoRC15 contiene **la solicitud completa revisada**, referencia de
responsable y ProcedenciaCatalogo con antecedente. Cambiar proyecto, documento,
artefacto, revisión, producto, operación, selección o finalidad invalida esa
revisión aportada. No se acepta un booleano de aprobación o código ejecutable.

InformeVinculoRC15 conserva solicitud/revisión, diagnóstico documental, cotejo
nuevo, salida nativa opcional, restricciones con orígenes y diagnósticos. Su
conversión a bool se rechaza. Los campos sensibles no se incluyen en repr.
`diagnostico_publico()` publica estado, versión, cantidad de diagnósticos y flags
fijos; omite rutas, textos, responsables, referencias e identificadores recibidos.
El informe completo es interno y no debe volcarse como log o credencial.

## Condiciones y estados

Se cotejan la identidad fija PNDA, contexto/entrada canónica de la operación,
edición del catálogo/entrada/recurso y documento, literal/concepto/ámbito,
referencia completa frente al control, revisión aportada y restricciones. Se
exige operación descriptiva DECLARADA/PLANIFICADA, contenido_id presente y
artefacto no PARCIAL. Diagnósticos desfavorables nativos no se compensan.

Perfil documental único: DOCX, afirmación literal CON_VALOR sobre
`identificador_producto` y ámbito igual a la finalidad. Exige evidencia SINTETICA,
nivel DECLARADA o VERIFICADA, vigencia aportada VIGENTE, sin pendientes ni
contradicciones, y versión/fecha documental conocidas. No se inventan valores.
Una segunda afirmación con el mismo localizador se rechaza como duplicación.

Solo después de esas comprobaciones se llama de nuevo al cotejador. Ruta,
tamaño/SHA contra control, estructura y conservación final deben ser
SATISFECHA, sin diagnósticos de error y con exactamente un cotejo COINCIDE.
No se recibe un ResultadoVinculacion favorable como sustituto del cotejador.

| Estado | Significado acotado |
|---|---|
| APTO_ESTRUCTURALMENTE | Relación coherente según revisión aportada y cotejo físico/literal efectuado; salida nativa preparada |
| PENDIENTE_DE_EVIDENCIA | Falta documento, control, revisión, vigencia, edición o comprobación física/literal suficiente; salida None |
| INCOMPATIBLE | Identidad/finalidad/versión conocida contradictorias, duplicación, restricción bloqueante o clase no admitida; salida None |

La contradicción prevalece sobre faltantes. Una edición desconocida es faltante,
no evidencia de una edición distinta. Se conserva el detalle del cotejo: no se
declara corrupción física por la sola ausencia de un documento.

La salida nunca asciende automáticamente a VERIFICADA: contiene **DECLARADA**,
referencia original e incertidumbres sin recortar y pendientes explícitos de
revisión de aplicabilidad, autenticidad y restricciones del informe. El documento
original conserva su nivel aportado; comprobar bytes no lo reclasifica.

ExpedienteProducto no tiene un campo de RestriccionPropagada. Por ello **el
informe completo es la unidad de entrega**: extraer únicamente su salida no
transfiere todos los bloqueos. No se autoriza tal extracción como fundamento
aprobado. Las restricciones documentales y de licencia permanecen además en
la solicitud y el producto originales, sin convertir desconocidos en permisos.

## Fronteras de confianza y límites

Documento aportado, presencia física, identidad contra control, integridad de
bytes, coherencia de la relación, procedencia declarada, autenticidad
institucional, ejecución productora, ciencia y permisos son hechos distintos.
El cotejo acredita solo su lectura/alcance fechado y control aportado; no autoría,
semántica científica, licencia ni continuidad futura de los bytes.

La revisión de la fixture es un registro inventado del escenario. No hubo una
revisión humana o aprobación institucional real. La legitimidad del responsable
y del control proviene del llamador cooperativo y no se autentica aquí. Python
hostil puede alterar objetos o funciones; no se promete resistencia a ello.

Los flags autenticidad_institucional, validacion_cientifica, ejecucion_autorizada,
producto_leido y operacion_ejecutada son False y no configurables por constructor.
La comprobación técnica sí se ejecuta; no se ejecuta la operación RC1 declarada.
No se inicia un algoritmo, regla, descarga, migración o núcleo científico.

No hay gestor documental, registro persistido de revisiones, firma, IAM,
transformación de datos, conservación durable ni nuevo parser OOXML. La
cancelación y las cotas son las existentes del cotejador/inspector; no hay nuevo
plazo global, reserva de recursos o promesa de escala. Todos los ensayos usan
TEMP propios y datos sintéticos. M26 global sigue **PENDIENTE**, con cobertura
experimental parcial de esta única relación; no se cambia su fila histórica.
