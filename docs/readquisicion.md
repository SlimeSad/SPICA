# PASO 80 — Decisión previa de readquisición

Estado: implementación experimental desacoplada. El motor **recomienda**, no
autoriza ni ejecuta una adquisición. No utiliza HTTP, archivos, SQLite, relojes
del sistema, tareas programadas ni callbacks suministrados por el usuario.

## Inspección y compatibilidad

Git comenzó limpio, en `feature/suadc-http`, HEAD `b87e575` (PASO 79 registrado).
Se inspeccionaron núcleo, catálogo RAW, evidencia HTTP v1, recibo MANUAL v2,
adaptador HTTP→RAW, ingesta manual y planificador antes de modificar código.

Se conservaron todos los archivos anteriores. Se añade únicamente el paquete
`spica.adquisicion.readquisicion`, sus pruebas y este documento. No hay cambios
de contratos públicos anteriores, DDL, migraciones ni nuevas dependencias.

Se reutilizan `Fuente`, `MecanismoAdquisicion`, `EstadoDescarga`,
`EstadoIncorporacion`, `ProcedenciaCatalogo`, `ActivoRAW`, `EvidenciaAdquisicion`,
`ReciboIngestaManual`, la validación temporal común y el filtro de metadatos.

La idempotencia manual conserva la regla del PASO 79: repetir un evento requiere
ID, metadatos y contenido coincidentes. HTTP documentado genera un evento por
incorporación; la deduplicación posterior no evita el GET previo. Este motor no
reemplaza ninguna de esas políticas ni registra eventos.

`AlmacenRAW.metadatos()` devuelve una instantánea. `verificar()` y `recuperar()`
comprueban físicamente **y escriben** un evento/comprobación en SQLite; por eso el
motor no los llama. Tampoco inspecciona tablas privadas ni incorpora una consulta
global de adquisiciones: recibe antecedentes explícitos y acotados.

## Contratos v1

Todos son dataclasses congeladas, con `version_contrato="1"`. Las colecciones son
tuplas de contratos conocidos; no se aceptan configuraciones ejecutables.

| Contrato | Función |
|---|---|
| `IdentidadRecurso` | Proyecto, objeto, recurso, fuente y producto declarados |
| `AntecedenteAdquisicion` | IDs de adquisición/activo, mecanismo y estados existentes, interrupción, fechas, tamaño/hash catalogados, evidencia local, versiones, indicios y restricciones históricas |
| `EvidenciaLocal` | Activo comprobado, estado, instante, procedencia y tamaño/hash observados cuando existen |
| `IndiciosHTTP` | URL/nombre públicos declarados, Content-Length, ETag y Last-Modified opcionales |
| `EvidenciaActualizacion` | Alcance, procedencia, relación documental, adquisición base y versiones previa/nueva; documentación e indicios opcionales |
| `RestriccionesAcceso` | Alcance por proyecto/recurso/fuente/producto/mecanismo, evidencia y permisos separados para adquirir, reutilizar, publicar y redistribuir |
| `PoliticaReadquisicion` | Modo de consulta y antigüedad máxima aceptada de la comprobación local |
| `SolicitudDecision` | Identidad, mecanismo previsto, evaluación UTC explícita, antecedentes, alcance del historial, actualizaciones, restricciones, política y uso previsto |
| `ResultadoDecision` | Solicitud completa, decisión, justificación, faltantes, limitaciones, actualización documentada y activos candidatos |

El resultado identifica además `version_motor="1.0.0"`,
`autoriza_red=False` y `vigencia_remota_comprobada=False`. No contiene un método de
ejecución, cliente, función diferida, credencial o ruta de almacenamiento.

Las identidades conservan sus caracteres originales. Fuente/producto desconocidos
son `None`, **no comodines**: solo se utilizan antecedentes cuya identidad completa
coincide. Los antecedentes fuera de alcance se conservan en la solicitud del
resultado y se señalan como no aplicados. La autorización de un proyecto o de un
mecanismo no se traslada a otro.

La adquisición, el activo y el SHA-256 son identidades diferentes. Se conserva
cada adquisición aunque comparta bytes; no se deduplican antecedentes por hash,
URL o nombre. IDs de adquisición o activo repetidos se consideran ambiguos y
exigen revisión, sin eliminarlos silenciosamente.

Un historial vacío no prueba que nunca existió una adquisición.
`historial_completo=True` es una declaración explícita del llamador respecto al
recurso solicitado; el motor no la certifica consultando el catálogo.

## Semántica de evidencia

### Copia local

`EstadoLocal` distingue `DESCONOCIDO`, `INTEGRO`, `INCONSISTENTE`, `AUSENTE` y
`NO_DISPONIBLE`. Una ausencia comprobada no es un error de permisos ni una
verificación no disponible. `existencia_comprobada` devuelve `True` para íntegro,
`False` para ausencia y `None` en los otros casos.

Una comprobación declarada exige activo, fecha y procedencia con evidencia. Para
`INTEGRO` requiere tamaño y SHA-256 observados; ambos deben coincidir con el
catálogo y con el activo evaluado. El motor comprueba **coherencia de evidencia
aportada**, no vuelve a leer bytes ni acredita la veracidad de una afirmación del
llamador. Un hash/fecha de catálogo aislados no se promueven a prueba física.

Se considera reutilización únicamente de activos INCORPORADA, con evidencia
coincidente y admisible según la antigüedad configurada. PARCIAL, FALLIDA,
PREPARADA y VERIFICADA no equivalen a una incorporación completa. La interrupción
se conserva separadamente; un estado INCORPORADA contradictorio con transferencia
parcial/fallida/interrumpida exige revisión.

Por defecto se aceptan comprobaciones de hasta **24 horas**, incluido el límite.
Es una política técnica provisional y configurable, no un plazo institucional ni
una garantía de inmutabilidad. `None` desactiva esa caducidad, pero no los demás
controles. Una comprobación no puede ser posterior a la evaluación ni anterior a
la adquisición/incorporación. Se comparan instantes UTC con el criterio temporal
común, sin asignar zonas a fechas desconocidas.

### Versiones, documentación y fechas

Las versiones del recurso son **opacas**: no se ordenan como números, texto ni
semver. `POSTERIOR_DOCUMENTADA` es una relación explícitamente aportada, con
procedencia/evidencia y una adquisición base identificable cuya versión previa
coincide. Etiquetas diferentes por sí solas no demuestran posterioridad.

Una revisión de catálogo HTTP no se convierte en versión del recurso. La versión
del fundamento de uso manual tampoco: se conserva como `version_documental`.
`fecha_adquisicion`, `fecha_incorporacion_raw`, `fecha_recepcion_civil`,
`fecha_documental`, `fecha_observacion` y `evaluada_utc` tienen significados
distintos. Las fechas civiles permanecen `date`; no se inventan horas, zonas,
períodos ni fechas de observaciones.

La actualización puede estar DESCONOCIDA, DOCUMENTADA o ser CONTRADICTORIA.
Faltantes de base/versiones/fundamento mantienen incertidumbre; afirmaciones
incompatibles producen revisión. Se detectan versiones previas que contradicen
la base, posterioridad con etiquetas iguales, igualdad con etiquetas diferentes,
contradicción explícita y cambio/permanencia incompatibles para la misma base y
fecha de revisión. Varias versiones posteriores sin un orden demostrado exigen
revisión, sin escoger la mayor etiqueta ni la revisión más reciente como verdad.
No es un reconciliador general de documentación: períodos históricos distintos y
conflictos de autoridad complejos requieren revisión externa.

Si una versión posterior documentada ya está disponible y comprobada localmente,
puede considerarse esa copia; no se vuelve a proponer adquirirla por la sola
presencia de la actualización. Una copia de otra versión no comparable no se
declara antigua ni se degrada automáticamente.

### Indicios HTTP

| Indicio | Interpretación en este paso |
|---|---|
| Misma URL | Localizador coincidente; no identidad lógica ni prueba de contenido |
| Mismo nombre | Etiqueta; no prueba de igualdad |
| Content-Length | Tamaño declarado; igualdad de tamaños no implica igualdad de bytes |
| ETag débil | Validador de equivalencia semántica declarada; no igualdad byte a byte |
| ETag fuerte | Validador de una representación en su contexto HTTP; no SHA-256, permiso ni prueba universal de actualidad |
| Last-Modified | Instante declarado por servidor, opcional y sujeto a precisión/confiabilidad; no fecha documental u observacional |

El motor no implementa comparación condicional de representaciones. Se conserva
la distinción débil/fuerte sin convertir una coincidencia o cambio de ETag en
autenticidad, vigencia o nueva versión científica. La ausencia de estos indicios
tampoco demuestra ausencia de cambios.

## Matriz de escenarios y precedencias

| Caso | Condiciones | Decisión |
|---|---|---|
| A. Recurso sin antecedente | Historial declarado completo | ADQUISICION_INICIAL, con controles de autorización/acceso pendientes |
| B. Copia íntegra | RAW completo, prueba local admisible y reutilización permitida | REUTILIZAR_LOCAL; vigencia remota desconocida |
| C. Actualización documentada | Relación posterior coherente con una base; versión aún no disponible | RECOMENDAR_NUEVA, condicionada a controles independientes |
| D. Estado remoto desconocido | Política EXIGIR_VIGENCIA | EVIDENCIA_INSUFICIENTE, aunque el hash local coincida |
| E. RAW inconsistente/ausente | Problema local documentado | REVISION_MANUAL; sin reparación ni nueva adquisición automática |
| F. Parcial/fallida/interrumpida | Sin otra copia elegible | REVISION_MANUAL; conserva cada estado e identidad |
| G. Adquisiciones múltiples | Contenido físico compartido | Conserva todas; evalúa cada prueba ligada a su activo |
| H. Entrega manual | Recibo MANUAL | Sin URL, cabeceras o actualización HTTP inferidas; reutilización local sujeta a permisos |
| I. Nueva adquisición explícita | Modo SOLICITAR_NUEVA | Recomienda un evento nuevo, preservando antecedentes y controles |
| J. Restricción conocida | Permiso requerido negativo | BLOQUEADA para esa operación/uso |
| Historial incompleto | Vacío sin declaración de exhaustividad | EVIDENCIA_INSUFICIENTE; no afirma que sea la primera adquisición |
| Permiso de reutilización desconocido | Copia íntegra | REVISION_MANUAL |
| Condiciones textuales | Actuales o del candidato histórico | REVISION_MANUAL; no se interpretan ni ejecutan |
| Contradicción o identidad ambigua | Evidencia incompatible | REVISION_MANUAL, sin elegir silenciosamente un antecedente |

Los controles de alcance, fechas y uso se aplican antes de recomendar una
operación. Problemas locales/contradicciones no se eluden con SOLICITAR_NUEVA.
Un antecedente fallido no elimina otro completo y elegible. Una nueva adquisición
pedida explícitamente o sustentada en actualización documentada puede recomendarse
conservando el antecedente incompleto; ello no reconcilia ni reintenta ese evento.

Adquirir y reutilizar son operaciones distintas: prohibir acceso nuevo no prohíbe
por sí mismo una reutilización local expresamente permitida. Publicación y
redistribución se evalúan según `UsoPrevisto`. Un permiso actual positivo no
revoca automáticamente una prohibición histórica del activo. Debe documentarse
y revisarse esa eventual sustitución antes de cambiar los antecedentes aportados.

Una recomendación de adquisición inicial/nueva puede incluir permiso desconocido,
siempre como **faltante explícito**, junto a comprobar mecanismo/acceso actuales y
obtener autorización operativa independiente. No es una orden ejecutable ni una
aprobación de permisos. Permisos positivos sin evidencia se tratan como desconocidos;
los negativos se conservan de forma restrictiva. Las restricciones textuales no
se interpretan como reglas programables.

## Uso, procedencia y seguridad

API pública: `decidir_readquisicion(SolicitudDecision(...))`. No recibe ni devuelve
clientes o conexiones. Normaliza UTC y ordena las tuplas para obtener resultados
deterministas con entradas equivalentes, preservando el historial íntegro aportado.
La justificación y los faltantes son códigos estables, sin cadenas de excepción.

`antecedente_desde_raw(activo, procedencia, evidencia=..., local=...,
version_recurso=...)` proyecta **objetos ya obtenidos** por un llamador autorizado.
No recibe `AlmacenRAW`, no abre catálogos y no comprueba archivos. Conserva el ID
del activo y, cuando existe, el ID del evento; no inventa uno para adquisiciones
sin recibo. Rechaza recibos de otro activo/incompatibles con la instantánea.

En MANUAL conserva proveedor desconocido como `None`, versión/fecha del fundamento
como documentación y permisos/restricciones históricos, sin trasladarlos como
autorización actual. No exporta rutas del origen, nombre del entregante ni otros
datos personales del recibo. En HTTP conserva URL pública y fecha técnica
disponibles, pero no inventa ETag, Last-Modified, versión o estado de transferencia.

Se reutiliza el filtro conservador de metadatos: rechaza secretos reconocibles,
rutas Windows ambiguas y referencias con credenciales; no normaliza destructivamente
IDs. No detecta todos los secretos ni datos personales. Las referencias aprobadas
y los metadatos del resultado también deben tratarse según su confidencialidad;
no se recomienda volcar objetos completos en logs.

No existe carga de archivos de políticas, evaluación de expresiones, `eval`,
`exec`, plugins ejecutables ni callbacks de reglas. Los estados documentales y
permisos son declaraciones aportadas, no autenticación institucional demostrada.

## Integración futura antes de GET

Se necesitará un orquestador aprobado que:

1. Obtenga antecedentes por interfaces públicas acotadas y declare correctamente
   el alcance del historial, sin acceder a tablas privadas ni inventar exhaustividad.
2. Reúna evidencia documental y una comprobación local autorizada; reconozca que
   la verificación RAW actual escribe un evento y necesita permiso para ello.
3. Construya la solicitud con alcance, uso, política y evaluación explícitos.
4. Presente la recomendación y resuelva faltantes/bloqueos. Obtenga autorización
   operativa independiente; vuelva a comprobar las condiciones antes de usar bytes
   o iniciar GET, evitando una carrera entre decisión y ejecución.
5. Solo tras aprobación, utilice el cliente/adaptador existentes, con sus orígenes,
   TLS, límites, redirecciones y trazabilidad; conserve los eventos históricos.

Este paso no introduce ese orquestador, ningún hook HTTP ni planificación de tareas.
HEAD, GET condicional, HTTP 304, caché, nuevos encabezados, orígenes y capacidades
institucionales requieren revisión específica. No se afirma soporte de esos
mecanismos en ningún servidor.

## Verificación y riesgos pendientes

Las pruebas nuevas utilizan únicamente dataclasses y evidencia inventada en
memoria. Hay pruebas que bloquean apertura de archivos, SQLite, sockets,
verificación/recuperación RAW y ejecución HTTP, comprobando que no se invocan.
No se creó una nueva adquisición, un RAW o una base operativa como fixture.

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -B -m pip check
git diff --check
git status --short
```

Quedan pendientes la aprobación de caducidad/políticas por producto, autoridades
de confianza documental, revocación/sustitución de permisos, reconciliación compleja
de versiones, historial completo acotado y coordinación con ejecución posterior.
La prueba local es una instantánea histórica: no bloquea archivos, no proporciona
aislamiento frente a escritores concurrentes ni garantiza durabilidad futura.

La política es multiinstitucional y no contiene condiciones propias de SENAMHI,
ANA, OEFA, INGEMMET, laboratorios o estaciones privadas. No activa reglas
científicas ni interpreta observaciones.

## Resultado de verificación del PASO 80

Comprobado con Python **3.15.1** de `.venv`, HTTPX **0.28.1** y SQLite **3.53.4**:

- **1 061 pruebas aprobadas: 989 anteriores + 72 nuevas**. Cero fallidas, errores
  u omitidas. Tiempo informado por `unittest`: **125.624 segundos**.
- Se compararon los IDs de las 989 pruebas anteriores con el registro del PASO 79:
  coinciden; no hay IDs de prueba duplicados en la suite completa.
- `pip check`: `No broken requirements found.`
- `git diff --check`: correcto. Se revisaron además los seis archivos nuevos sin
  seguimiento mediante comprobación independiente de whitespace, UTF-8 y sintaxis.
- Sintaxis correcta en los 67 archivos Python de `src/` y los 28 de `tests/`, sin
  generar bytecode. Sin definiciones duplicadas en los archivos nuevos.
- Todos los archivos seguidos permanecen intactos respecto a HEAD `b87e575`.
- La suite completa se ejecutó con una guardia temporal externa que bloquea
  accesos al almacenamiento operativo y conexiones/DNS reales. Instalada en ambos
  procesos de verificación: **cero intentos de acceso operativo o red**.

Git inicial: limpio. Git final: solamente `docs/readquisicion.md`, el paquete nuevo
`src/spica/adquisicion/readquisicion/` y `tests/test_readquisicion.py` sin seguimiento.
Son seis archivos nuevos; ninguno anterior modificado. No hubo commits, descargas,
instalaciones, nuevas adquisiciones ni migraciones operativas. No se accedió a RAW,
staging o SQLite operativos para producir este diagnóstico; no se afirma haber
verificado físicamente sus archivos.

El log completo y las evidencias de aislamiento de esta ejecución se conservan
en el directorio temporal de auditoría de la sesión, fuera del repositorio.

**Dictamen: APTO CON RESTRICCIONES.** El motor está comprobado como capa de
recomendación offline. Requiere revisar las políticas provisionales y aprobar
por separado un orquestador, la obtención de evidencia y cualquier operación real.
No se ha conectado al cliente HTTP ni se han habilitado descargas automáticas.
