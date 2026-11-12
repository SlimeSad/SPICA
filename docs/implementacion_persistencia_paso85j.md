# PASO 85-J — Persistencia experimental de evidencias de ejecución

Fecha: **2026-11-12, America/Lima**. Base **2efc9f7**, rama
feature/suadc-http, Git inicialmente limpio. Ese commit consolida los tres
documentos del 85-I: [arquitectura](arquitectura_persistencia_linaje_paso85i.md),
[protocolo](protocolo_recuperacion_ejecuciones_paso85i.md) y
[plan](plan_implementacion_persistencia_paso85i.md).

Se implementa exclusivamente un conservador/lector de checkout para evidencia
sintética en temporales aislados. No es persistencia general de SPICA ni un
almacén operativo. Resultados reales del incremento:
[piloto y verificaciones](piloto_recuperacion_paso85j.md).
Límites y pendientes: [brechas](brechas_persistencia_paso85j.md).

## 1. Puerta arquitectónica y reutilización

Se inspeccionaron el arnés 85-G, la traza 85-H, RAW, HTTP→RAW, configuración,
inspección SQLite/WAL y catálogo científico. El catálogo científico estable
admite application_id propio, user_version=1 y un DDL exacto; RAW admite sus
esquemas reconocidos v1/v2. Añadir tablas silenciosamente rompería esa validación.

La solución mantiene **intacto todo src/spica**: un catálogo sintético nuevo se
crea con CatalogoCientifico existente y se extiende explícitamente a **85001**.
Un lector experimental reconoce exactamente base v1 + cuatro tablas nuevas.
El lector estable sigue aceptando v1 y rechazando 85001. No se ofrece migración
bidireccional ni compatibilidad del lector antiguo con la extensión.

El creador no acepta una base preexistente: la raíz y el archivo SQLite se crean
exclusivamente, se valida v1 y se exige que sus siete tablas estén vacías. La
extensión y user_version se confirman en una transacción. Abrir una instancia
existente solo valida; no inicializa, migra o adopta un estado incierto.

No hay otra base de ejecuciones junto al catálogo científico: las tablas nuevas
conviven en ese catálogo temporal. No se colocan trazas en RAW ni se modifican
sus contratos MD-01/02/03. El contenido original del arnés continúa siendo RAW
temporal y se elimina según su contrato original.

| Componente | Reutilización / responsabilidad |
|---|---|
| [Arnés 85-G](../herramientas/piloto_integracion_85g.py) | Produce el informe real con MockTransport, RAW, catálogo, lector, QA0, exportaciones, consumo y conciliación existentes |
| [Traza 85-H](../herramientas/traza_cierre_85h.py) | Construcción y cotejo originales, sin modificar; el lector recupera el informe tipado necesario |
| [Codec cerrado](../herramientas/_codec_linaje_85j.py) | Lista explícita de tipos conocidos, preservación de tuplas, mapas, fechas UTC, enums, campos fijos, valores originales, nativos y prefijos JSON |
| [Índice experimental](../herramientas/_catalogo_linaje_85j.py) | Reutiliza el DDL v1, añade esquema 85001 y valida estructura, versión, FK y quick_check; conexiones separadas por operación |
| [Conservador](../herramientas/conservacion_linaje_85j.py) | Raíz temporal, presupuesto, marcador de escritor, publicación exclusiva, confirmación lógica, lector sin efectos y diagnósticos |
| [Pruebas](../tests/test_conservacion_linaje_85j.py) | Evidencia real sintética, fallos inyectados, procesos nuevos y protección de contratos anteriores |

El único acoplamiento privado adicional de DDL es
CatalogoCientifico._crear(conexion=...) para construir la referencia en memoria,
no _conexion de una instancia ni una modificación del validador productivo.
Se reutiliza _segura para rutas. Son dependencias experimentales de checkout,
pendientes de estabilización si una necesidad posterior justifica una API común.
No se añade un motor científico, cliente HTTP, scheduler o ejecutor de planes.

## 2. Contratos y versiones

Formato de conservación, codec y manifiesto: **0.1.0**; esquema SQL experimental:
**85001**. Se conservan traza 85-H/ejecución 85-G/JSON QA en sus versiones
originales. Cambiar la versión SQLite no cambia versiones de reglas o documentos.

Contratos nuevos acotados: LimitesConservacion85J, Artefacto85J y Recuperacion85J,
además de estados independientes de conservación y recuperación. Recuperacion85J
rechaza bool; su resumen expone estados/capacidades, nunca concede permisos.

| Artefacto obligatorio | Contenido |
|---|---|
| informe | InformeEjecucion85G tipado reversible, incluidos nativos parciales, documentos realmente emitidos, captura previa, diagnósticos y restricciones |
| traza | Bytes UTF-8 exactos de TrazaCierre85H.canonico |
| referencia | SHA de traza recibido obligatoriamente del llamador, versión y naturaleza control_local_previo_del_ensayo; autenticidad independiente False |
| manifiesto | Identidades de instancia/ejecución/conservación, inventario/tamaños/SHA físicos, relaciones, estado de publicación, restricciones y limitaciones |

El cotejo 85-H se realiza antes de escribir; el codec también demuestra igualdad
del informe codificado/decodificado. No se acepta un diccionario como informe,
un hash arbitrario como control suficiente o un estado CONCLUIDA aislado.
La referencia procede del responsable de la fixture y se establece antes de
conservar. Sigue siendo un control local del mismo dominio de confianza, no
una aprobación institucional ni un ancla independiente contra un atacante.

**Ajuste acotado respecto al diseño 85-I:** para recuperar exactamente el informe
tipado, el codec conserva sus rutas temporales históricas como metadatos privados
inertes. Solo admite rutas bajo el temporal 85-G declarado. Nunca las resuelve,
abre o usa para localizar artefactos; el resumen público las omite. Se mantiene
el informe original, en vez de inventar rutas/valores que pasen el verificador.
Este ajuste no modifica contratos públicos ni habilita recuperación de RAW borrado.

No se usa pickle, eval, exec, carga de clases nombradas por el archivo, expresiones
o código configurable. El registro de clases está definido por código confiable.
Se rechazan claves JSON duplicadas, tipos desconocidos, campos adicionales o
ausentes, campos init=False contradictorios, versiones no admitidas, excesos de
profundidad/nodos y números no finitos. El perfil no admite todos los contextos
documentales o zonas temporales posibles de SPICA: es el del piloto sintético.

## 3. Estados separados y representación de integridad

Se preserva EstadoEjecucion85G: PLANIFICADA/INICIADA como estados no terminales;
CONCLUIDA/INCOMPLETA/FALLIDA/CANCELADA en los informes conservables. Una ejecución
FALLIDA o CANCELADA puede tener conservación completa y cotejo coherente.

Conservación: PREPARADA → ESCRIBIENDO → PUBLICADA → REFERENCIAS_CONFIRMADAS →
CONSERVADA. Los dos últimos pasos se confirman juntos en una transacción SQL.
Los errores reconocidos antes del cierre dejan FALLIDA o INCOMPLETA con causa;
si SQLite no permite escribir el error, queda la intención/último estado observado.
Una interrupción BaseException/terminación forzada no inventa un evento final.

Recuperación: VERIFICADA_EN_ALCANCE, INCOMPLETA, ARTEFACTO_AUSENTE,
ARTEFACTO_CORRUPTO, CONFLICTO_DE_IDENTIDAD, VERSION_INCOMPATIBLE y
REVISION_NECESARIA, con diagnósticos explícitos. No muta el estado histórico ni
repara archivos. Un cierre verificado con residuos/marcador pendiente exige
revisión aunque su cotejo contractual todavía sea satisfactorio.

Grafo implementado de huellas, sin modificar el formato histórico de la traza:

```text
informe I -> H_I
traza T original -> H_T
referencia R contiene el control H_T -> H_R
manifiesto M referencia H_I, H_T y H_R -> H_M
SQLite confirma H_M y las cuatro referencias
```

M no contiene su propio hash y T no se reescribe para apuntar a M. El manifiesto
registra publicada_pendiente_confirmacion_sqlite porque se escribe antes del
commit. El estado CONSERVADA procede de SQLite y se coteja con el manifiesto;
no se cambia retroactivamente el archivo para afirmar una transacción futura.
Referencia SHA del cuerpo R y control H_T son conceptos distintos.

Igualdad de SHA permite compartir un cuerpo cotejado, no fusionar ejecuciones.
La clave de ejecución y su contexto de conservación completo controlan duplicación:
misma evidencia ya CONSERVADA es idempotente; otra evidencia con el mismo ID
produce conflicto; una conservación previa incompleta requiere revisión. No
repite adquisición, QA o acciones institucionales.

## 4. Publicación y transacciones

1. Validar contratos, cotejo 85-H, codec reversible y presupuestos; reconocer raíz
   y catálogo antes de escribir el marcador de escritor.
2. Adquirir marcador exclusivo por creación xb con nonce; un segundo escritor
   cooperativo o marcador abandonado bloquea nuevas escrituras.
3. Confirmar intención PREPARADA y registrar ESCRIBIENDO en transacciones cortas.
4. Escribir cada artefacto en temporal propio por bloques, comprobando escritura
   corta; flush/fsync y cerrar manejador.
5. Releer físicamente y comprobar bytes/tamaño/SHA; publicar con os.link sin
   sobrescritura. Un destino existente se coteja byte a byte; si difiere se
   detiene. No hay fallback a os.replace o copia que sobrescriba.
6. Releer publicación, retirar únicamente el temporal ya publicado y comprobar
   el siguiente artefacto. Los temporales fallidos quedan para diagnóstico.
7. Publicar manifiesto, registrar PUBLICADA y confirmar las cuatro referencias,
   H_M, eventos y estado CONSERVADA en una transacción SQLite local.
8. Cerrar conexiones, liberar solo el marcador propio cotejado y recuperar para
   verificar el cierre. Un retorno perdido tras commit se consulta/idempotiza;
   no autoriza robar marcadores o repetir una ejecución incompleta.

Las tablas linaje_instancia, linaje_ejecuciones, linaje_artefactos y linaje_eventos
incluyen unicidad, checks y referencias internas. Se usan parámetros SQL, FK,
synchronous=FULL y timeout local; el perfil admite DB sin WAL/SHM/journal
pendientes. No intenta recuperación SQLite modificadora al abrir para lectura:
usa mode=ro&immutable=1, query_only y trusted_schema=OFF sobre el perfil sin
escritores admitido. Auxiliares inesperados requieren revisión, no se eliminan.

No hay transacción global de archivos/SQLite. Una publicación puede quedar sin
fila; una fila confirmada puede perder después su archivo. El inventario acotado
informa huérfanos y temporales y el lector bloquea evidencia incompleta/corrupta.
No adopta ni elimina huérfanos automáticamente ni promueve incompleta a concluida.

## 5. Seguridad, recursos y límites

La raíz debe ser conservacion bajo un spica-85j-* del TEMP comprobado por el
arnés, fuera del código/Git y raíces operativas conocidas. Se rechazan traversal,
UNC, componentes internos, symlinks y junctions. Los nombres físicos se generan
como UUID/hash hex en minúsculas; IDs/URLs nunca forman paths, evitando nombres
reservados, ADS y colisiones por caso en esos nombres generados.

Se comparan descriptor/stat/tamaño/mtime y se revalidan rutas antes/después de
leer/publicar. Una raíz privada confiable y un escritor cooperativo son requisitos;
persisten TOCTOU frente a sustituciones hostiles, aliases desconocidos o código
Python/OS con control. El marcador no es lock multiusuario ni se limpia por TTL/PID.
Windows hereda permisos; mode=0o700 no acredita una auditoría de ACL.

Predeterminados: cuatro artefactos; 8 MiB por artefacto; 24 MiB total de cuerpos;
profundidad 48; 250000 nodos; 128 referencias de inventario; bloques 65536 bytes;
plazo cooperativo 120 segundos. Hay topes de configuración. El límite total no
es cuota física de disco ni incluye un límite RSS: informe/JSON/captura/traza
ya se materializan acotadamente. No se procesan CSV grandes en este incremento.
Las cotas no reservan espacio; ENOSPC se trata como fallo sin borrar evidencia.

Cancelación se comprueba entre bloques/fases; el plazo no interrumpe de inmediato
una llamada SQLite/fsync o un cotejo puro. Los errores devuelven códigos fijos,
sin mensajes arbitrarios/credenciales/tracebacks en el resumen. Los cuerpos del
informe son privados y pueden contener metadatos históricos; no son exportación
pública autorizada. No existe cifrado ni autenticidad independiente.

Visibilidad exclusiva de un archivo no garantiza durabilidad ante pérdida de
energía. No hay fsync portable de directorios Windows en este patrón, backup
general, GC, restauración, checkpoints de ejecución en curso, Range o reintentos
automáticos. La limpieza final del árbol corresponde exclusivamente al padre
propietario del ensayo temporal; no a un algoritmo que borre evidencia operativa.
