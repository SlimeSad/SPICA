# PASO 85-L — Amenazas, dominios de fallo y evidencia de mitigación

Fecha: **2026-11-12, America/Lima**. Base **d3372a0**, feature/suadc-http.
Auditoría estática/documental, sin dispositivos inspeccionados, conexiones,
respaldos, pruebas nuevas o acceso a datos operativos. Complementa el
[diseño de custodia](arquitectura_custodia_independiente_paso85l.md) y la
[evaluación de madurez](evaluacion_madurez_arquitectonica_paso85l.md).

## 1. Activos, frontera de confianza y criterio de riesgo

Activos: bytes originales y su identidad lógica, documentos fuente, resultados
derivados, informes/trazas, manifiestos, catálogos SQLite, controles previamente
aceptados, restricciones y registros de custodia/recuperación. Un descriptor de
activo sin sus bytes no es una copia de ese original. Una copia sin catálogo o
evidencia necesaria puede no ser recuperable en el alcance esperado.

El perfil actual confía en el intérprete/código y en un responsable individual
que controla raíces privadas y un escritor cooperativo. Trata archivos, JSON y
metadatos recibidos como entradas que deben comprobarse. No aísla código Python
malicioso ni protege contra el propietario que pueda sustituir bytes y controles.
Las amenazas H/I son relevantes precisamente para no atribuir autenticidad a SHA
o frozen; no se afirma que haya ocurrido un ataque. Robo/fallo de disco son
relevantes al confiar información única a una laptop; no bloquean una fixture
prescindible y reconstruible. No se asignan probabilidades ni porcentajes de avance.

Prioridades: P0 bloquea una acción que violaría integridad/validez/seguridad; P1
es indispensable para el hito que se declara; P2 mejora robustez/mantenimiento;
P3 es ampliación futura. Una condición P0 no es un defecto crítico nuevo demostrado.
Las prioridades siguientes se refieren al paso a custodia operativa; el experimento
sintético mantiene las restricciones y no necesita resolver toda la matriz.

## 2. Modelo de amenazas A–J

| ID / escenario y relevancia | Activos / consecuencia | Protección existente | Protección faltante | Riesgo residual | Prioridad condicionada | Evidencia necesaria para acreditar mitigación |
|---|---|---|---|---|---|---|
| A — Corrupción accidental, al escribir/copiar o conservar bytes | Cuerpos, SQL y controles; lectura imposible o contenido distinto | Relectura/SHA/tamaño, inventario, esquema/FK/quick_check y cotejo 85-H; rechazo de corrupción en 85-K | Copia/control fuera del fallo que alteró el original y ensayo de recuperación del alcance completo | Corrupción de todas las copias o del control; coherencia local no descubre toda alteración coordinada | P2 sintético; P1 antes de custodia única | Alteraciones sintéticas detectadas y recuperación desde copia conservada; registrar alcance/errores; no inferir tasa de fallo de hardware |
| B — Error humano/eliminación accidental, uso cotidiano | Originales, generaciones, referencias; pérdida de evidencia/historial | Publicación exclusiva y rechazo de destino existente; identidad distinta del hash | Retención aprobada, inventario de dependencias y copia no accesible al borrado habitual | El mismo usuario puede borrar todas las carpetas conectadas; no hay borrado reversible general | P1 antes de datos únicos; P2 para fixtures | Retirada simulada de una copia propia y restauración autorizada desde otra; comprobar referencias y no confundir deduplicación con eliminación de adquisiciones |
| C — Fallo del programa durante escritura | Archivo parcial, índice/intención; éxito falso o desajuste FS/SQL | Temporales exclusivos, cierre lógico separado, estados/error, presupuesto y sello final | Procedimiento aprobado para clasificación y tratamiento manual de parciales; registro de incidentes puede fallar | No transacción global; evento final puede no persistir por disco/SQL | P1 para promoción operativa; mitigado en perfil sintético | Fallos por fase, disco/permisos/escritura corta y retorno perdido: ninguna promoción de estado ni reparación por borrado |
| D — Cierre inesperado del proceso | Lock, intención, copias o SQL sin cierre; nueva operación sobre estado incierto | 85-K documenta os._exit antes del sello/restauración: marcador conservado y revision_necesaria | Revisión asistida y criterio de desbloqueo bajo autorización; no reanudación de tareas | El marcador abandonado bloquea incluso con PID inexistente; no asegura relato completo | P2 en laboratorio; P1 antes de operación | Cierres abruptos sintéticos y reapertura separada, conservando marcadores; no llamarlos corte eléctrico |
| E — Pérdida de energía, relevante en laptop sin continuidad garantizada | Cachés/entradas de directorio/SQLite; generación perdida o corrupta | Flush/fsync de archivos, FULL en escritor SQLite; diagnóstico al abrir | Durabilidad del conjunto en SO/filesystem/hardware y copia previa separada verificadas | Visibilidad exclusiva no implica persistencia eléctrica; no fsync portable de directorio en el patrón Windows actual | P1 si se exige durabilidad; P0 si se promete sin evidencia | Ensayo específico autorizado con fixtures y copia previa en hardware representativo; registrar pérdidas, sin tocar originales únicos; no ejecutado aquí |
| F — Fallo de unidad de almacenamiento | Todas las carpetas/particiones del dispositivo; pérdida conjunta | Copias 85-K independientes de inodo, comprobadas en TEMP | Copia verificada en dispositivo físico distinto y restaurador compatible | Otra letra/partición puede ser el mismo dispositivo; control/copia pueden compartir fallo | P1 antes de custodia única; no bloquea síntesis descartable | Identidad física/topología constatadas y restauración con origen indisponible; TEMP solo prueba archivos independientes |
| G — Robo o pérdida de computadora | Discos internos, controles locales y código/configuración necesarios; indisponibilidad y posible exposición | Ninguna tolerancia a pérdida de equipo demostrada; datos privados no publicados por el piloto | Copia/control fuera del equipo, lector/versiones disponibles y portabilidad entre perfiles; protección de confidencialidad según riesgo | Disco externo en la misma mochila puede perderse junto al equipo; no cifrado nuevo ni protección física acreditados | P1 antes de confiar datos únicos; medidas de confidencialidad según caso | Recuperar en otro equipo/perfil con copia autorizada y control separado; evaluar custodia física, sin asumirla; no realizado |
| H — Sustitución coordinada de artefactos, manifiesto e índice | Evidencia histórica falsa pero internamente coherente | Control explícito de 85-K detecta cambios si el triple esperado permanece intacto | Ancla previamente aceptada y protegida fuera del mismo dominio de escritura | Si también se reemplaza el control, el conjunto puede seguir coherente; hash no autentica autor | P1 para integridad independiente; P0 si se afirma autenticidad por SHA | Mantener referencia protegida y cambiar coherentemente candidato/SQL/manifiestos: rechazo contra el control original; pérdida del ancla produce incertidumbre, no aceptación |
| I — Código malicioso con permisos del usuario | Archivos conectados, controles y resultados del verificador; posible fuga/sustitución | Validadores de rutas/JSON, sin ejecución desde archivos, guardias de ensayo | Frontera OS/proceso/custodia distinta si ese modelo es necesario; entorno de verificación confiable | Python hostil puede falsificar salidas, hooks o lecturas; disco conectado vuelve a exponerse | Fuera del modelo actual; P0 para ejecutarlo como confiable; P1 si se amplía la amenaza | Protección efectiva del medio/control y verificación en entorno confiable separado; no se demuestra aislamiento con unit tests ni dataclasses |
| J — Pérdida/alteración de la referencia separada, incluido error de transcripción o referencia antigua | Ancla de integridad; falso rechazo o aceptación de generación equivocada | K exige control explícito; no lo deriva del candidato | Registro de aceptación/sustitución, protección y disponibilidad de referencias; cotejo íntegro | Un registro antiguo auténtico no prueba actualidad; sin referencia quedan solo controles locales | P1 para cotejo independiente; P2 para fixtures | Control distinto, ilegible, perdido y generación antigua: diagnósticos diferenciados, sin regenerar el control desde el candidato; ensayo pendiente |

Las pruebas citadas de 85-J/K son **históricas y acotadas**, revisadas mediante
documentos/código. Las nuevas mitigaciones y pruebas de la última columna son
requisitos de diseño, no ensayos efectuados en 85-L. Permiso denegado o presupuesto
agotado implican verificación no realizada/incompleta, no corrupción demostrada.

## 3. Dominios de fallo: independencia por escenario

Un dominio es un conjunto expuesto a una misma causa de pérdida; no una ruta.
Se debe describir para qué causa se pretende independencia y cómo se identificó.
La separación física tampoco garantiza separación de autoridad de escritura.

| Ubicación propuesta | Corrupción/borrado de un archivo | Fallo físico del disco original | Robo/pérdida del equipo | Suceso común del lugar | Programa malicioso con permisos del usuario | Evaluación y evidencia necesaria |
|---|---|---|---|---|---|---|
| Otra carpeta del mismo disco | Puede conservar bytes si no se afectan ambas | No | No | No | Expuesta si ambas son accesibles | Útil para copia lógica, no dominio de disco/equipo independiente; TEMP 85-K pertenece aquí, sin topología de hardware comprobada |
| Otra partición del mismo disco | Separación lógica, no frente a todo borrado | No | No | No | Normalmente expuesta mientras accesible | Letra distinta no prueba dispositivo distinto; documentar relación partición/dispositivo antes de afirmar separación |
| Otra unidad física interna | Puede tolerar fallo localizado | Puede, si es realmente otra unidad y el fallo es localizado | No | No | Expuesta si está conectada/accesible | Puede compartir controlador, energía y equipo; comprobar dispositivo físico y restauración, no asumir independencia total |
| Unidad externa desconectable | Copia independiente si fue completa/verificada | Puede, en otro dispositivo | Solo si no se pierde junto al equipo | No si permanece en el mismo lugar afectado | Menor exposición mientras está desconectada; vulnerable al conectarla sin protección | Comprobar identidad física, soporte de publicación y verificación; registrar desconexión/ubicación. La propia unidad externa también puede fallar |
| Medio externo guardado en otro lugar | Puede conservar otra generación | Puede | Puede si no viaja con el equipo | Reduce un fallo común del lugar de origen; no elimina todos los fallos correlacionados | Menor exposición al estar separado; al conectarlo requiere entorno confiable | Candidato offline preferido para pérdida de equipo/lugar; trazabilidad de custodia y ensayo en otro entorno pendientes |
| Almacenamiento remoto opcional | Depende de versiones/protección y permisos | Puede | Puede | Depende de independencia real del proveedor/ubicación | Credenciales robadas o sincronización de borrado pueden afectar ambas copias | Solo si se aprueban privacidad, derechos, coste, disponibilidad y recuperación; sincronización no es automáticamente respaldo. No obligatorio ni implementado |

Todas las columnas expresan **capacidad condicionada**, no certificación de un
medio real. No se consultaron letras, discos, números de serie, controladores,
ACL, dispositivos externos o servicios remotos. Cambiar de carpeta TEMP o proceso
no acredita ninguna independencia física; tampoco hacerlo en otra partición.
Un registro de dispositivo deberá evitar publicar números de serie o rutas privadas
innecesarios; bastan referencias opacas y evidencia privada disponible al custodio.

## 4. Garantías existentes y brechas relevantes para un desastre

| Hallazgo 85-L | Evidencia estática / consecuencia | Clasificación |
|---|---|---|
| L01 — Separación del argumento sin custodia | ControlRespaldo85K contiene tres strings; verificar_respaldo compara contra ellos. No administra custodios, protección o canal de entrega | P1 antes de afirmar integridad independiente; no fallo del contrato local |
| L02 — Destinos solo TEMP y alcance de evidencia | _raiz_respaldo y p._raiz exigen sus raíces TEMP; una ejecución, cuatro artefactos y base científica vacía. No se respalda RAW | P1 antes de copia externa/operativa completa; no se habilita cambiando una ruta |
| L03 — Portabilidad del informe histórico condicionada | ConservadorLinaje85J._validar_informe compara base.parent con h._base_temporal(); el codec conserva Path histórico. Otro TEMP puede rechazarse | P1 antes de recuperación en otra cuenta/equipo; incompatibilidad del alcance ampliado, sin prueba entre equipos ni modificación aquí |
| L04 — Modelo cooperativo y durabilidad limitada | Marcador xb/nonce, stat antes/después y fsync, sin transacción FS+SQL o aislamiento hostil | P2 dentro del perfil; P1 según exigencia operativa; P0 si se atribuye garantía inexistente |
| L05 — Retención y cierre de referencias no operativos | No gestor de retención ni respaldo de originales; referencias a RAW eliminado son históricas | P1 antes de custodia única o eliminación; diseño de 85-L no implementa esa capacidad |
| L06 — Fuentes de arquitectura y método | Matrices 85-F y contratos locales disponibles; no ERS global aprobada localizada ni nuevo método documentado por este paso | P1 para acordar el siguiente caso; no inventar aprobación retrospectiva ni exigir toda SPICA para un ensayo |

Son límites verificables del alcance, no nuevos defectos reproducidos que obliguen
a reescribir contratos estables. L03 sí exige una decisión de compatibilidad antes
de prometer restauración tras pérdida del equipo. Preservar rutas históricas como
datos inertes y validar locadores físicos actuales son responsabilidades distintas:
un futuro perfil portable debe separarlas sin abrir rutas del informe ni relajar
las protecciones de E/S. No se propone hacerlo en 85-L.

## 5. Qué se puede probar y qué requiere otro medio

| Entorno de aceptación futuro | Casos que podría acreditar | Lo que todavía no acredita |
|---|---|---|
| Memoria/fixtures y TEMP aislados | Esquemas, versiones, IDs, hashes, propagación de estados/restricciones; corrupción, parciales, límites, no sobrescritura y controles discrepantes | Disponibilidad después de perder el disco/equipo, ACL real o durabilidad eléctrica |
| Otro proceso en el mismo perfil | Cierre/reapertura sin objetos del productor y copias independientes de los archivos de entrada | Otra cuenta, TEMP distinto, sistema operativo distinto o dispositivo físico diferente |
| Otro perfil/equipo de prueba autorizado | Portabilidad del lector/codec, versiones y referencias históricas; restauración sin directorios del equipo original | Protección del ancla o tolerancia de hardware por el mero cambio de proceso |
| Otro dispositivo físico verificado, con origen indisponible | Restauración desde una copia ubicada fuera del dispositivo perdido y lector disponible | Robo conjunto, malware sobre ambos medios conectados o pérdida del control |
| Custodia/control protegidos por separado | Detección de sustitución respecto de la referencia aceptada, dentro de la protección demostrada | Autor institucional, verdad científica o actualidad de una referencia sin historial |
| Ensayo de energía/hardware específico | Comportamiento observado en esa configuración bajo un protocolo autorizado, con fixtures recuperables | Garantía universal o permiso para someter originales únicos a un fallo |

La recomendación ligera agrupa L01/L02/L03/L05 en un solo futuro caso de custodia
operativa: generación completa pertinente, destino comprobado, control protegido
y recuperación portable. Resolverlos en varios mecanismos/índices paralelos
aumentaría fronteras sin evidencia de necesidad. L04 conserva su modelo cooperativo;
seguridad contra Python hostil requiere otra frontera y no se promete por anticipación.

## 6. Restricciones conservadas

Sin claves, firmas, cifrado nuevo, configuración de permisos, nube, dispositivos
externos o copias reales en este paso. No se inspeccionan datos operativos ni
evidencia institucional privada. Las [29 brechas PNDA](brechas_reconciliadas_pnda_paso84i.md)
mantienen 2 resueltas, 17 parciales, 8 pendientes y 2 contradicciones; 27 abiertas.
El primer `/query` INGEMMET sigue NO AUTORIZADO. No se infieren estaciones,
HORA/UBIGEO/PP, unidades, ciencia, derechos de redistribución o permisos de los
controles de integridad. El dictamen documental no permite utilizar una copia
como evidencia institucional autenticada.
