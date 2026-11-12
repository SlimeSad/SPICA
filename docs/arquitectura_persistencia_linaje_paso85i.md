# PASO 85-I — Arquitectura propuesta de persistencia y linaje

Elaboración: **2026-11-12, America/Lima**. Rama **feature/suadc-http**, HEAD
**a044b49**, «SUADC: auditoria y cierre verificable de trazabilidad paso 85-H».
Git inicialmente limpio; el commit consolida el cierre del 85-H sobre el WIP
c259b62. **Diseño para revisión, sin implementación ni autorización operativa.**

Este expediente consta de este documento, el
[protocolo de recuperación](protocolo_recuperacion_ejecuciones_paso85i.md) y el
[plan de implementación](plan_implementacion_persistencia_paso85i.md).
Las denominaciones de contratos, estados y tablas futuras son propuestas locales
del 85-I; no describen interfaces disponibles en SPICA.

## 1. Base auditada y garantías actuales

Se revisaron los tres informes de cada incremento:
[auditoría 85-F](auditoria_arquitectura_integral_paso85f.md),
[matriz 85-F](matriz_dependencias_integracion_paso85f.md),
[hoja de ruta 85-F](hoja_ruta_arquitectonica_paso85f.md),
[contrato 85-G](contrato_ejecucion_integrada_paso85g.md),
[piloto 85-G](piloto_integracion_vertical_paso85g.md),
[brechas 85-G](brechas_integracion_paso85g.md),
[contrato 85-H](contrato_trazabilidad_cierre_paso85h.md),
[piloto 85-H](piloto_cierre_ejecucion_paso85h.md) y
[brechas 85-H](brechas_persistencia_linaje_paso85h.md).
Prevalece la sección 7 del piloto 85-H para su resultado final histórico:
**1791 pruebas aprobadas**, no ejecutadas otra vez en esta etapa documental.
Ese piloto documenta 572 bytes y dos filas ficticias: cada reproducción produce
2 × (18 + 4 × 3) = **60 resultados** con 22 definiciones de regla, 60 restricciones
informativas y 206 bloqueantes. A/B son dos pasadas del mismo activo, no 120
observaciones independientes. Son cifras históricas, no medidas hoy.

| Subsistema inspeccionado como texto | Garantía implementada y límite real |
|---|---|
| [RAW](../src/spica/adquisicion/almacenamiento/raw.py) y [modelos MD](../src/spica/adquisicion/almacenamiento/modelos.py) | Copia por bloques, tamaño/SHA calculados y relectura física; publicación por enlace duro exclusivo, cotejo de un contenido preexistente antes de compartirlo. Proyecto, objeto y activo distintos del hash. Uso privado secuencial; no atomicidad con SQLite |
| [Catálogo RAW](../src/spica/adquisicion/almacenamiento/catalogo.py) | Preparación y transiciones con evento en transacciones SQLite, foreign_keys y synchronous=FULL. PREPARADA/VERIFICADA pueden sobrevivir a un fallo posterior; no equivalen a INCORPORADA |
| [Configuración](../src/spica/adquisicion/almacenamiento/configuracion.py) e [inspección](../src/spica/adquisicion/almacenamiento/inspeccion.py) | Raíz derivada de Path.home, rutas fuera de código/Git, rechazo de symlinks/junctions, marcador/intención y sondas exclusivas. Validar WAL puede copiar DB+WAL a un temporal; abrir sondea escritura. No son APIs generales sin efectos |
| [Catálogo científico](../src/spica/adquisicion/catalogo/persistencia.py) y [documental](../src/spica/adquisicion/catalogo/documental.py) | Base distinta de RAW, application_id propio, user_version=1, esquema exacto, revisiones e historial; registros y snapshots transaccionales. No catálogo de ejecuciones ni identidad global de instancia |
| [Streaming](../src/spica/adquisicion/transportes/descargas.py) e [HTTP→RAW](../src/spica/adquisicion/integracion/http_raw.py) | Tamaño efectivo, SHA, temporales propios y errores por fase; el adaptador presta cliente/almacén y no los cierra. Limpia su staging; puede fallar después de publicar un activo. No transacción entre los dos catálogos y los archivos |
| [Arnés 85-G](../herramientas/piloto_integracion_85g.py) | Contrato/estado/presupuesto 0.1.0 y dos reproducciones sobre la misma entrada sintética. ExitStack/TemporaryDirectory liberan recursos y eliminan el árbol propio antes de devolver el informe. Sin recuperación entre procesos |
| [Traza 85-H](../herramientas/traza_cierre_85h.py) | Proyección canónica 0.1.0, máximo 8 MiB, cotejo puro con informe tipado y SHA separado. Conserva JSON y referencias nativas; no serializador reversible de InformeEjecucion85G, importador de terceros o persistencia |
| [QA0](../src/spica/calidad/motor.py), [exportación](../src/spica/calidad/exportacion.py), [consumo](../src/spica/calidad/consumo.py), [conciliación](../src/spica/calidad/conciliacion_lotes.py) | Resultados/versiones/restricciones y comparación contextual. Aceptar JSON o COINCIDENCIA no certifica ejecución, ciencia o permiso. Componentes en memoria acotados, no RAM constante general |

RAW.verificar, recuperar y diagnosticar pueden registrar eventos y modificar
estados del catálogo. No deben usarse como lectura operativa inocua durante una
auditoría que prohíba escrituras. Ninguno se invocó en el 85-I.
La inspección RAW exige ausencia de escritores y detecta cambios ordinarios de
stat; no es snapshot seguro ante un atacante concurrente. Su presupuesto de
copia incluye DB+WAL, margen y holgura proporcional; la limpieza comunica fallos.
No sustituye un procedimiento de respaldo consistente.

Las pruebas existentes localizadas incluyen
[fallo SQLite después de publicar y reapertura RAW](../tests/test_almacenamiento_raw.py),
[interrupción de inicialización y copia WAL](../tests/test_cierre_configuracion_raw.py),
[auxiliares huérfanos y esquemas ajenos](../tests/test_regresiones_altas.py),
[streaming interrumpido/KeyboardInterrupt](../tests/test_descargas_http.py),
[cierre vertical](../tests/test_integracion_vertical_85g.py) y
[coherencia de trazas parciales/estados](../tests/test_traza_cierre_85h.py).
Se leyeron pruebas representativas; no se ejecutaron. Reapertura de un objeto en
una prueba no demuestra recuperación de toda la ejecución tras reiniciar Python;
inyectar KeyboardInterrupt no simula una pérdida eléctrica real.

## 2. Hallazgos de compatibilidad antes de extender

| ID del 85-I / relevancia | Evidencia / consecuencia para el diseño |
|---|---|
| I01 — Alta si se promete recuperación | 85-H necesita traza, InformeEjecucion85G y control separado. Su proyección sustituye parte de los nativos por huellas; perder el informe impide repetir el cotejo completo actual. Guardar solo canonico+sha256 no basta |
| I02 — Alta si se prometen originales recuperables | El arnés destruye RAW y ambos catálogos temporales. Persistir esas rutas no conserva bytes. Retener una traza histórica y verificar nuevamente la entrada son capacidades distintas |
| I03 — Alta ante una extensión silenciosa | CatalogoRAW admite estructuras v1/v2 reconocidas; CatalogoCientifico compara sqlite_master con su DDL exacto v1. Agregar tablas de ejecución sin versión/validador compatibles haría rechazar la base |
| I04 — Alta si se atribuye atomicidad o autenticidad | Archivos y SQLite se confirman separadamente; todos los controles del 85-H están en un proceso confiable. FULL/fsync y hashes locales no cierran esas brechas |
| I05 — Media para escala y mantenimiento | Informe, captura, traza, JSON y conciliación materializan datos acotados. También hay imports privados y dependencias diferidas entre herramientas. Persistir no convierte esos componentes en streaming ni en API estable |

Son límites e incompatibilidades de la ampliación propuesta, no nuevos bugs
reproducidos en producción. No se alteran las correcciones del 85-H. Una extensión
de esquema o extracción de una API necesitará alcance y pruebas propios en 85-J;
la presencia de este diseño en Git no sería aprobación de una migración.

## 3. Alternativas y elección provisional

**A:** archivos inmutables por contenido y manifiestos por ejecución; sin índice SQL.
**B:** ampliar el catálogo SQLite existente como autoridad de índices/estados;
artefactos separados, manifiesto reconstruible desde las filas.
**C:** híbrido mínimo sobre esa misma ampliación SQLite: artefactos separados y
un manifiesto inmutable de cierre, además del índice transaccional. B y C comparten
motor/base: C añade un inventario conservable y contrastable si se pierde el índice.
No se propone una tercera base SQLite.

| Criterio | A: archivos/manifiestos | B: índice SQLite existente | C: híbrido mínimo preferido |
|---|---|---|---|
| Reutilización | Patrones RAW, nuevo índice por recorrido | Reutiliza SQLite, revisiones y validación; extensión de esquema explícita | Igual B más patrón de manifiesto, sin otro catálogo paralelo |
| Integridad | Hash físico/inventario; referencias distribuidas | Filas/FK y hashes físicos; SQL no comprueba archivos | Cotejo inventario↔filas↔bytes; no autenticidad independiente |
| Recuperación | Escanear todo y resolver conflictos | Detectar operaciones pendientes por filas; pérdida del índice exige más evidencia | Intención SQL y manifiesto permiten comparar ambos lados; adopción manual ante incertidumbre |
| Complejidad | Baja al escribir, mayor al buscar/recuperar | Transacciones conocidas; riesgo de índice único insustituible | Algo más de redundancia controlada, protocolo explícito |
| Atomicidad real | Publicación individual, nunca de todo el árbol | Transacción SQL solamente | Misma frontera; confirmación lógica después de publicar y cotejar |
| Rendimiento | Escaneos crecen con ejecuciones | Índices/paginación; no guardar cuerpos enormes en filas | Índices más lectura acotada de manifiesto; hashes por bloques |
| RAM | Acotar parser y recorrido | Consultas acotadas, no fetchall ilimitado futuro | Igual B; las APIs QA/85-H conservan sus límites en memoria |
| Disco | Un cuerpo por hash, manifiestos repetidos pequeños | Cuerpos más DB/journal y referencias | Añade inventario cerrado pequeño; cuota incluye todas las copias temporales |
| Mantenimiento | Evolución de archivos y buscador propio | Versionar DDL/lectores existentes | Versionar DDL, manifiesto y codec con matriz explícita |
| Portabilidad | Depende de publicación exclusiva del filesystem | SQLite más mismas dependencias de archivos | Igual B; sin promesa sobre red/volúmenes sin enlaces duros |
| Offline | Sí | Sí | Sí, sin servicios externos |
| Corrupción | Un manifiesto dañado puede perder asociación | DB dañada puede inutilizar índice entero | Conserva evidencia para diagnóstico/restauración, sin autorreparación |
| Seguridad | Raíz privada y parser estricto | Añade superficie SQL, usar parámetros y esquema conocido | Dos fuentes que deben cotejarse; discrepancia bloquea, ninguna se impone por sí sola |
| Extensión | Relaciones complejas más costosas | Natural para índices/versiones/eventos | Igual B con cierre portable; no repositorio científico general |

**Se recomienda C para revisión.** Reutilizar CatalogoCientifico para un espacio
versionado de ejecuciones es razonable: ya indexa recursos, revisiones y evidencia
documental. Mantener el catálogo RAW dedicado a originales y MD-01/02/03 evita
convertir una traza QA en un original institucional. La alternativa A es viable
para un archivo aislado, pero encarece referencias compartidas e idempotencia.
No se necesita otro motor, nube, GPU o base nueva.

Condición indispensable: una futura versión del catálogo científico debe admitir
explícitamente las estructuras antiguas y nuevas; el lector actual v1 rechazará
la nueva. No añadir tablas bajo user_version=1, reutilizar tablas de recursos para
simular ejecuciones ni ejecutar una migración al abrir. La versión numérica nueva
queda por acordar; el primer ensayo usará **catálogos nuevos sintéticos**. La
compatibilidad de bases preexistentes y su migración explícita requerirán revisión
antes de cualquier uso operativo. Si se rechaza esta ampliación, revisar A; no
crear otra base por defecto para eludir esa decisión.

## 4. Ubicación y responsabilidades

La futura raíz de artefactos se designa aquí como **raiz_ejecuciones_autorizada**:
un parámetro, no una ruta aprobada ni un directorio creado. Debe estar fuera del
checkout, de Git y de los árboles internos RAW/staging. El catálogo científico
que la referencia tendrá una identidad de instancia y vinculación explícita a esa
raíz. No se deduce una autorización de ConfiguracionRAW ni de una ruta del JSON.

Distribución conceptual, todavía inexistente:

```text
raiz_ejecuciones_autorizada/
  contenido/sha256/<prefijo>/<huella>   cuerpos inmutables de artefactos de ejecución
  temporales/<id_interno>/            escritura propia acotada, mismo volumen
  control/                           identificación de raíz y coordinación local
catálogo científico existente        índice y estados mediante ampliación versionada
RAW existente                        originales y su catálogo, sin duplicar CSV
```

Los nombres físicos se generan internamente desde UUID/hash validados; no desde
URL, Content-Disposition, estación o identificador institucional. Los contratos
persistidos contienen referencias lógicas, no rutas absolutas ejecutables. Un
registro de raíces controlado por el operador resuelve referencias, nunca el
manifiesto recibido. No crear automáticamente una raíz operativa en 85-J.

Reutilización: RAW para originales, HTTP→RAW si un procedimiento futuro autoriza
adquisición, catálogo para recurso/revisión, QA/exportador/consumidor/conciliador
sin otro motor. Lo nuevo se limita al codec de evidencia conservable, manifiesto,
adaptador de índice/publicación y lector de recuperación. Los helpers privados
de RAW no son por ello una API pública de publicación de derivados.

## 5. Contratos propuestos y clasificación de artefactos

A = imprescindible para el alcance declarado; B = reconstruible **solo si sus
dependencias/versiones siguen disponibles**; C = opcional; D = evidencia sin
eliminación automática; E = referencia externa de disponibilidad no garantizada.
Las categorías pueden solaparse. Un artefacto no producido se registra ausente
con causa; no se rellena como vacío ni se afirma que fue ejecutado.

| Contrato / artefacto propuesto | Contenido mínimo | Clase / política |
|---|---|---|
| ContextoConservacion | Esquema, raíz/catalogo_instance_id, ejecucion_id original y espacio de custodia, generación de conservación, versiones de código/configuración, límites, naturaleza sintética, fechas técnicas UTC, permiso referenciado sin secretos | A/D; una referencia a permiso no concede permiso |
| IdentidadesEntrada | Entrada, proyecto/objeto, fuente/producto/recurso originales, revisión local conocida o None, activo/adquisición si existen, SHA/tamaño esperados separados de observados, identidad de almacén RAW | A/D/E; no copiar CSV, no fabricar adquisición ni versión |
| EvidenciaParcial | Eventos ordenados, fase, resultados nativos emitidos y su procedencia/valores/restricciones completos, informes reales, prefijo JSON realmente producido, causa de detención y campos ausentes | A/D en fallo/incompleta/cancelación; conservar aunque no pueda construirse cierre |
| InformeConservable | Estado de ejecución, etapas, configuración/contrato, informes de lectura/QA, transporte y catálogo observados, recuperaciones históricas, errores codificados, recursos liberados y limitaciones; referencias a cuerpos, sin rutas privadas | A/D; nuevo esquema explícito, no asdict genérico ni supuesta copia reversible del informe 85-G |
| DocumentosQA | Bytes UTF-8 exactos de cada exportación oficial 0.1.0 y contexto/lote; restricciones completas y desconocidos | A/D si se produjeron; no reexportar nativos para afirmar una exportación pasada |
| Resultado de consumo/conciliación | Informe real resumido sin perder conflictos/restricciones y referencias a documentos exactos; versiones y límites | Informe histórico A/D si se produjo; comprobación repetida B y registrada como evento nuevo |
| Traza conservada | Traza 85-H original cuando exista, con su versión/limitaciones; o evidencia parcial identificada como tal, sin fingir una traza 85-H válida | A/D para lo producido; nunca eliminar las limitaciones históricas de 85-H |
| ManifiestoCierre | Inventario de roles, referencias, tamaños y SHA, cardinalidades, estado histórico, completitud de conservación, restricciones y hash de informe/traza; campos ausentes y causas | A/D; sin hash propio dentro del contenido que se calcula |
| ReferenciaIntegridad | Huella esperada de manifiesto/traza, origen y alcance del control, custodio/fecha de aprobación si realmente existen; control local separado del independiente | A para cotejo local; D si control aprobado; no autocertificar por un booleano |
| EventoConservacion/Recuperacion | Secuencia, estado previo, hecho observado, versión del lector, UTC técnica, alcance de comprobación, incidencias, cancelación y vínculo a generación; error fijo sin traceback sensible | A/D; append-only lógico, no invulnerable al dueño de SQLite |
| Métricas y registros auxiliares | Duración/bytes/uso técnico medidos, sin cuerpos, tokens o rutas innecesarias | C; no inventar métricas ni depender de logs para reconstruir evidencia obligatoria |
| Referencias documentales/RAW externas | Identidades y controles del recurso/documento realmente usados, con fecha y restricciones | A/D/E según ejecución; si desaparecen, conservar referencia y declarar revalidación no disponible |

La versión inicial del nuevo formato se acordará antes de codificar; es distinta
de JSON QA 0.1.0, traza 85-H 0.1.0 y user_version SQLite. No sustituye a
ResultadoCientifico ni a sus futuros contratos disciplinares.

**Frontera del codec:** la API 85-H exige tipos exactos, no acepta JSON importado.
El futuro codec deberá mapear exclusivamente tipos/campos/versiones conocidos,
preservar None frente a vacío, orden y valores originales; rechazar extras,
duplicados, profundidades/cantidades/tamaños excesivos y números no finitos.
Nada de pickle, eval, exec, imports nombrados por el archivo o expresiones.
No guardar únicamente huellas de nativos parciales: sin JSON producido no hay
cuerpo desde el cual recuperarlos. Guardarlos una vez y referenciarlos evita la
pérdida. Un puente al verificador 85-H requerirá demostrar compatibilidad; no
reconstruir un InformeEjecucion85G ficticio ni suplantar rutas/flags para que pase.
El lector nuevo distinguirá cotejo físico, validación contractual y cotejo 85-H
realmente disponible. Registrar esa capacidad aunque el cotejo completo falte.
Los roles obligatorios son condicionales al alcance: una cancelación previa
carece legítimamente de activo, nativos o exportaciones, pero debe conservar
contexto, estado y ausencia motivada. La falla de captura puede impedir una traza
85-H válida; conservar el resto no permite inventar esa traza.

La traza histórica 85-H ya incorpora JSON. Si se guardan también los documentos
por separado, existe redundancia de compatibilidad explícita y acotada, que debe
contarse en el presupuesto; no se promete deduplicar subdocumentos dentro de sus
bytes intactos. El formato nuevo referencia cuerpos una vez; no reescribe una
traza antigua para simular esa optimización. No se duplica el archivo RAW.

## 6. Identidades, relaciones y versiones

| Identidad | Regla de conservación |
|---|---|
| Ejecución | Clave cualificada por espacio de custodia y ejecucion_id; conservar el ID declarado del 85-G. Nueva ejecución real necesita nuevo ID aunque use los mismos bytes |
| Instancia de catálogo/almacén | Identidad estable separada de ruta, hash de DB y application_id; propuesta nueva para referencias entre almacenes. Una copia de respaldo conserva identidad con generación de copia; un fork intencional requiere decisión explícita |
| Lote/reproducción | Identidad cualificada por ejecución y pasada A/B, sin confundir dos pasadas con dos adquisiciones. Conservar IDs de LoteQA existentes |
| Proyecto/objeto/activo/adquisición | Mantener MD-01/02/03 y adquisiciones independientes; el hash común comparte bytes, no borra activos/eventos ni sustituye sus IDs |
| Resultado QA | Conservar resultado_id y contexto/versión originales cuando fueron exportados. Antes de exportar conservar posición/regla/campos y huella nativa sin inventar resultado_id |
| Artefacto | Identidad de contenido SHA + tamaño + formato/versiones; un mismo cuerpo puede tener varios roles y referencias. No es identidad de ejecución ni evidencia de autoría |
| Revisión/versión | Revisión local de catálogo, edición institucional, esquema persistible, código, regla, evaluador y política de restricciones son ejes independientes; desconocidos siguen None |

Relaciones mínimas: ejecución→entrada/activo/recurso; ejecución→fases y lotes;
lote→nativos/documentos→consumo→conciliación; informe→artefactos;
traza→informe/evidencia; manifiesto→inventario. Solo la misma SQLite puede imponer
FK reales. Los enlaces RAW/catálogos externos exigen comprobación y conservan
resultado/fecha; no son FK entre bases ni disponibilidad perpetua.

Reglas de conflicto: misma clave de conservación y mismo inventario/contexto
verificado permite repetición de **conservación**, sin nuevo efecto; misma clave
con contenido/estado distinto rechaza y registra conflicto sin sobrescribir.
Dos ejecuciones con el mismo SHA permanecen separadas. Una evaluación independiente
sin correspondencia explícita sigue NO_COMPARABLE. Un resultado_id repetido con
distinto documento se conserva como conflicto; no se deduplica por conteo o valor.
Un huérfano no se adopta por nombre/hash: requiere identidad, esquema, cierre y
decisión registradas. El algoritmo no ofrece unicidad global sin coordinación.

## 7. Integridad, dependencias de huellas y confianza

| Nivel solicitado | Evidencia necesaria / alcance |
|---|---|
| A: hash declarado | Campo recibido; no prueba lectura de bytes |
| B: hash físico | SHA calculado al escribir y al releer archivo regular acotado; fecha/alcance de lectura observados |
| C: comparación con control aprobado | Referencia previa, custodio y aprobación realmente disponibles; control externo a la entrada contrastada |
| D: consistencia interna | Coinciden esquema, IDs, estados, inventario, filas, bytes y restricciones; no prueba que el autor sea SENAMHI |
| E: conservación tras reinicio | Otro proceso reabre archivos/índice, verifica controles y recupera la evidencia disponible; todavía por implementar/probar |
| F: autenticidad independiente | Requiere custodia/protección separada verificable; no la aportan SHA, SQLite, dataclasses o campos aprobada=True |
| G: validez científica | Método, aplicabilidad y evidencia científica propios; QA0 o conservación correcta no bastan |
| H: autorización operativa | Decisión independiente para acción/recurso/ubicación; no se deriva del manifiesto, de un estado o de un hash |

Grafo acíclico propuesto, distinto del formato histórico intacto de 85-H:

```text
D1..Dn = cuerpos de evidencia/documentos realmente producidos        -> H_Di
I = informe conservable con referencias H_Di, sin hash de T ni M    -> H_I
T = envolvente de traza con H_I, H_Di y traza 85-H original si existe -> H_T
M = manifiesto con H_I, H_T, inventario y cierre, sin su propia hash -> H_M
SQLite = intención/eventos + confirmación que referencia H_M
Control independiente, si se establece, conserva H_M y su contexto por otra custodia
```

Cada huella cubre bytes exactos del artefacto según su esquema, nunca una
representación que incluya recursivamente su propio hash. Los JSON QA conservan
sus bytes; el nuevo JSON técnico tendrá canonicalización fija documentada y
versionada, no se recalculará una forma distinta para aceptar un archivo alterado.
Las referencias entre archivos son huellas/roles, no incorporación recursiva de
cuerpos. La envolvente nueva no convierte las limitaciones de la traza antigua en
garantías cumplidas. El hash de captura previa del 85-H sigue referido a su propia
proyección histórica, sin añadirle un enlace inverso al manifiesto.

SQLite conservaría el control local que permite detectar corrupción accidental
del archivo. Ese control y los artefactos pertenecen al mismo dominio de escritura:
si se sustituyen ambos coherentemente, no hay detección independiente. Para exigir
detección de alteraciones no autorizadas se necesita un control previamente
aprobado bajo otra custodia o protección de escritura efectiva, por ejemplo un
inventario revisado conservado fuera del dominio modificable por el escritor.
Otra carpeta con los mismos permisos, otro campo o un respaldo igualmente
reescribible no bastan. No se selecciona ni se implementa PKI/firma/gestión de claves.

## 8. Consistencia, seguridad y límites de extensión

La confirmación SQL seguirá a publicación y relectura de todos los artefactos
obligatorios. Puede haber archivos publicados sin confirmación o filas que después
pierdan su archivo. El protocolo compensatorio está en el segundo documento:
**sin transacción global**, sin promoción automática de incompleta a concluida,
sin recuperación de bytes mediante una descarga no autorizada.

| Amenaza / fallo | Mitigación propuesta y límite |
|---|---|
| Rutas arbitrarias, ADS, dispositivos, symlinks/junctions | Raíz autorizada por operador, componentes generados, comprobación de ancestros/archivo regular/contención antes de operar; no usar paths del manifiesto. Rechazar volúmenes incompatibles |
| TOCTOU, sustitución, hardlinks ajenos | Comparar descriptor/stat/tamaño/SHA y revalidar al publicar/leer; raíz privada y escritor único. No prueba aislamiento ante otro proceso hostil con permisos de escritura |
| JSON/manifiesto no confiable | Parser estricto acotado, versiones cerradas, sin código, URLs no ejecutables, inventario cotejado con bytes y SQL; no importar clases desde nombres aportados |
| Duplicados/colisiones | Publicación exclusiva sin reemplazo; existente se relee y compara tamaño/hash y, ante colisión/conflicto, se detiene. SHA-256 supone resistencia criptográfica, no garantía matemática de ausencia de colisiones |
| Disco/permisos/cancelación | Presupuesto total y preflight sin prometer reserva; escrituras cortas verificadas, errores codificados, conservación de parciales y cancelación cooperativa en fronteras seguras |
| Concurrencia | Primera versión un escritor confiable; BEGIN IMMEDIATE solo coordina SQL. Coordinación local adicional deberá abarcar archivos/índice y rechazar una segunda operación, no asumir que SQLite bloquea todo |
| Apagado/corrupción | flush/fsync/relectura/publicación exclusiva y FULL, detección al reabrir y respaldo separado; Windows no tiene fsync portable de directorio en el mecanismo actual. No prometer durabilidad absoluta |
| Secretos/metadatos sensibles | Lista explícita de campos, códigos sin mensajes arbitrarios, referencias opacas de raíces y URLs públicas saneadas. No volcar cuerpos, credenciales, rutas privadas o traceback en logs; los cuerpos de evidencia necesarios quedan bajo custodia privada y restricciones. Filtros existentes no detectan todo secreto |
| Python/SO hostil | Fuera del aislamiento actual; requiere otra frontera de proceso/OS/custodia. Un audit hook o dataclass frozen no es sandbox |

Trabajo offline en hardware modesto: cuerpos grandes por bloques, consultas y
lotes acotados, presupuesto separado de RAM lógica/disco/tiempo y cancelación;
medir antes de ampliar. No duplicar RAW dentro de trazas ni cargar CSV completo.
La traza 85-H sigue materializada y limitada a 8 MiB; no se amplía para simular
escalabilidad. Al exceder presupuesto se conserva el parcial disponible y se
declara el límite, sin truncar silenciosamente un cierre.

Persistir no ejecuta QA1, GIS, IA o análisis ambiental. Las
[29 brechas PNDA](brechas_reconciliadas_pnda_paso84i.md) permanecen sin cambios,
el primer /query INGEMMET sigue NO AUTORIZADO y las identidades/unidades/zonas
horarias desconocidas no se completan. No hay acceso a originales o evidencias
privadas en esta auditoría. Las afirmaciones de código proceden de inspección
local; no se prueba hoy disponibilidad institucional, integridad física operativa
ni ausencia de cambios de terceros en almacenes mantenidos cerrados.
