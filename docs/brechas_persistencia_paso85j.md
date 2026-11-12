# PASO 85-J — Límites y pendientes de conservación experimental

Fecha: **2026-11-12, America/Lima**. Base **2efc9f7**, feature/suadc-http.
Se complementan [implementación](implementacion_persistencia_paso85j.md) y
[evidencia del piloto](piloto_recuperacion_paso85j.md). No se reescriben los
informes históricos ni las prioridades de todo SPICA.

## 1. Qué se cubre y qué no

La conservación cubre un informe realmente recibido y su traza/control locales,
desde la intención confirmada. Una interrupción anterior que pierda objetos
solo existentes en RAM no se recupera retroactivamente. El arnés 85-G conserva
su contrato: elimina RAW/staging/catálogos propios. Recuperar la evidencia de
ejecución no vuelve a verificar físicamente ese original desaparecido.

Los lectores no ejecutan tareas ni descargan entradas faltantes. Un informe
FALLIDO/INCOMPLETO/CANCELADO sigue en ese estado después de recuperar bien su
evidencia. No existe promoción científica, permiso institucional o reanudación.

## 2. Brechas y orden de atención

| ID / prioridad | Límite actual | Condición antes de ampliar |
|---|---|---|
| J01 / P1 para promoción de API | Herramientas de checkout y codec de tipos explícitos del piloto, no formato general de SPICA | Revisar perfiles/compatibilidad y dependencia de contratos auxiliares antes de mover a src; no imports arbitrarios |
| J02 / P1 antes de bases existentes | Esquema 85001 solo en catálogo sintético nuevo vacío, lector estable v1 lo rechaza | Política de versiones/compatibilidad y migración explícita revisada; ninguna migración operativa queda autorizada |
| J03 / P1 si se promete recuperación del motor | No hay checkpoints durante adquisición/QA; la cobertura comienza al entregar evidencia al conservador | Entrega observada y versionada de prefijos al mismo conservador, cancelación y pruebas por fase; no otro diario paralelo |
| J04 / P2 para este MVP; requisito antes de custodia única | No gestor de respaldo/restauración ni ensayo de recuperación del disco | Generaciones consistentes DB/artefactos, copia independiente y restauración sintética verificada antes de uso operativo |
| J05 / P2 | Retención/GC/cuota de largo plazo no implementados; residuos exigen revisión | Política aprobada por tipo/producto/licencia, referencias compartidas y bloqueos científicos/jurídicos; no TTL arbitrario |
| J06 / P2 | Cuerpos JSON/informe/captura/traza redundantes pero acotados; no límite RSS o benchmark de escala | Medir RAM/disco/tiempo y codec referenciado compatible sin perder nativos parciales ni restricciones |
| J07 / P2 | Original sintético 85-G borrado al cerrar; referencias físicas históricas inertes | Si se requiere revalidación futura del original, vida independiente de un RAW sintético autorizado; no recrear su asset_id |
| J08 / P3; bloqueo para modelo hostil | Un escritor cooperativo, controles de rutas con TOCTOU residual, sin aislamiento de Python hostil | Coordinación y frontera OS/proceso/custodia revisadas antes de multiusuario; no prometer protección por frozen o audit hooks |
| J09 / P3 o requisito si se exige autenticidad | Control, DB y artefactos pertenecen al mismo dominio de escritura | Custodia/protección realmente independiente y política de controles; hashes locales y manifiesto no son firma |
| J10 / fuera de este incremento | Sin ciencia QA1, derivados, GIS/IA o autorización institucional | Evidencia/aplicabilidad/método/contratos y permiso propios; persistencia no los sustituye |

## 3. Estados que requieren intervención

No recuperables como cierre completo: informe/control/artefacto requerido ausente,
bytes con SHA/tamaño contradictorios, versión no admitida, DB ilegible/ajena,
inventario/IDs incoherentes o conservación sin confirmación SQL. El lector devuelve
causa y conserva lo presente; no actualiza hashes esperados ni crea una base vacía.

Un marcador de escritor abandonado bloquea escritura aunque el PID ya no exista.
Un lector puede informar la evidencia presente, pero no lo retira ni reanuda
acciones. Un archivo huérfano no se adopta por su nombre hash. Permiso denegado
significa verificación no disponible, no corrupción científicamente demostrada.

Errores de diagnóstico también pueden impedir persistir un evento final. La
intención y los residuos permiten detectar incertidumbre; no garantizan narración
completa de un proceso terminado abruptamente. No se puede prometer recuperación
de bytes que nunca fueron entregados/escritos.

## 4. Restricciones institucionales intactas

Las [29 brechas PNDA](brechas_reconciliadas_pnda_paso84i.md) conservan sus IDs y
estados: 2 resueltas, 17 parciales, 8 pendientes y 2 contradicciones. No se añade
evidencia documental institucional ni se accede a CSV, XLSX/DOCX o manifiestos
privados. El primer /query INGEMMET continúa NO AUTORIZADO.

No se convierten PP, HORA, UBIGEO, unidades o zonas horarias. Las 22 reglas QA0,
JSON 0.1.0, inspectores, fuentes, contratos públicos y datos originales permanecen
sin cambios. Identidades/SHA o aceptación de documentos no autentican instituciones,
no resuelven aplicabilidad y no conceden ciencia o permiso operativo.

## 5. Recomendación de continuación

Después de revisar el piloto, decidir primero si el caso siguiente necesita
custodia duradera de evidencia única o solo fixtures prescindibles. Para custodia
real, priorizar respaldo/restauración consistente y política de versiones/ubicación,
antes de ampliar instituciones o métodos científicos. Para ejecución recuperable,
definir checkpoints de evidencia realmente entregada, sin repetir efectos.

No iniciar migraciones, almacenes permanentes, GC, reanudación de tareas o módulos
científicos por aprobar un JSON o por registrar este incremento en Git.
El dictamen y los resultados finales se consignan en el informe del piloto;
se espera revisión antes de continuar.
