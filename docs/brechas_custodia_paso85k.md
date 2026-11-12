# PASO 85-K — Brechas de custodia y límites de restauración

Fecha: 2026-11-12, America/Lima. Complementa el
[diseño](arquitectura_respaldo_restauracion_paso85k.md) y el
[piloto](piloto_respaldo_restauracion_paso85k.md). No sustituye ni modifica el
[inventario 85-J](brechas_persistencia_paso85j.md) ni las
[29 brechas documentales PNDA](brechas_reconciliadas_pnda_paso84i.md).

## Balance del incremento

La recuperación 85-J ya verifica evidencia conservada. 85-K añade una copia
independiente de una generación admitida y su restauración verificable a otra
raíz temporal. El cierre depende de todos los archivos, SQL, IDs, estados,
restricciones y control explícito; no basta un sello aislado o un hash correcto.
Los resultados efectivamente comprobados y fallos están en el piloto.

| Brecha de custodia | Tratamiento en 85-K | Pendiente |
|---|---|---|
| Pérdida de artefactos conservados | Copia física independiente; restaurar en raíz nueva | Custodia fuera del mismo volumen/dominio de fallo |
| Captura mezclada SQL/archivos | Escritor cooperativo excluido, snapshot API, generación antes/después, hashes y cotejo | Escritores hostiles, transacción global FS+SQL |
| Corrupción accidental | Hash físico por bloques, inventario estricto, DDL/FK/quick_check y lector 85-J | Ataques coordinados o defectos que alteren controles también |
| Interrupciones | Parciales/intención/marker visibles, rechazo de reutilización | Recuperación asistida aprobada; no auto reparación |
| Versiones | Esquema 85001/formatos cerrados, incompatibilidad explícita | Migraciones futuras revisadas y formatos archivísticos a largo plazo |
| Identidad/restauración | Mismos IDs históricos, nuevo ID de operación, sin ciencia/permiso | Política para clones y cambios de custodia |
| Tamaño/tiempo | Presupuestos/bloques/plazo cooperativo/espacio estimado | Reserva real, cuota OS y límite duro de RAM/tiempo |
| Autenticidad | Control explícito fuera de la entrada leída | Custodio independiente, firmas, claves, sellado externo si se aprueba |
| Privacidad | Códigos cerrados; rutas solo en evidencia histórica privada | ACL auditada, cifrado/retención y análisis integral de secretos |
| Retención/limpieza | Ninguna eliminación automática del gestor | Política autorizada y registro de custodia; no GC oportunista |
| Durabilidad ante apagado | Flush/fsync de archivos, publicación exclusiva, detección al abrir | fsync de directorios portable, ensayos de energía/hardware, backup externo |

## Restricciones que no deben relajarse

- Solo TEMP, una ejecución conservada, tablas base vacías, perfil DELETE sin
  auxiliares. WAL activo, multiejecución y almacenes operativos quedan bloqueados.
- Un escritor cooperativo; los marcadores inciertos no se borran para continuar.
  No hay comparación y sustitución atómica frente a un proceso malicioso.
- Un destino existente siempre se rechaza. No se restaura sobre el original ni
  se sobrescriben catálogos, cuerpos, marcadores o parciales.
- El control no se obtiene del respaldo al restaurar. Aun separado como argumento
  en otro proceso, sigue siendo un control local del mismo dominio de confianza.
- Copias independientes, con enlaces exclusivos solo para publicar el temporal
  propio dentro de su destino. El volumen debe soportarlos; no se usa replace.
- Cancelación/plazos en puntos seguros; llamadas de SO bloqueadas no son
  cancelables de forma forzada. No se promete éxito ante falta de espacio concurrente.
- Un error posterior al sello puede coexistir con archivos publicados: revisar
  la evidencia, nunca inferir éxito del retorno ausente ni repetir automáticamente.
- Guardias de Python, stat y comprobaciones de rutas no son un sandbox frente a
  Python/SO hostil. No se garantiza resistencia TOCTOU ni aliases desconocidos.

## Ciencia, instituciones y permisos

Restaurar evidencia no valida la ciencia ni autentica a SENAMHI/INGEMMET/ANA/OEFA.
No se vuelve a ejecutar QA, no se restaura RAW borrado por el arnés, no se
normalizan HORA/UBIGEO/PP, no se activan reglas científicas, GIS o IA.
Las 29 brechas mantienen sus estados históricos (2 resueltas, 17 parciales,
8 pendientes y 2 contradicciones), sin nueva evidencia institucional.
El primer `/query` INGEMMET sigue NO AUTORIZADO. No se concede permiso por
conservación, restauración, un campo de manifiesto o un test aprobado.

## Prioridad posterior, sujeta a revisión

Antes de que esto sea custodia única, diseñar la protección independiente del
control y una copia en otro dominio de fallo, junto con un procedimiento manual
auditado de tratamiento de parciales. Después evaluar versiones, durabilidad,
ubicaciones y modelo de concurrencia con pruebas específicas. No integrar ahora
en RAW, catálogo productivo ni automatización de adquisiciones. No iniciar otro
incremento sin revisión del presente expediente.
