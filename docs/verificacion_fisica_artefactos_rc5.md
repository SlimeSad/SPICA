# RC5 — Verificación física y piloto sintético

Fecha **2026-11-16**, America/Lima. Base **1024158**, contrato **0.1.0**.
[Materialización](materializacion_experimental_rc5.md),
[pruebas](../tests/test_materializacion_rc5.py),
[auditoría](auditoria_arquitectonica_rc5.md).

## Propiedades comprobadas y fronteras

| Evidencia | Cómo se obtiene | Qué no demuestra |
|---|---|---|
| A: hash declarado | Solicitud/entrada RC4 o referencia recibida | Que el archivo exista o su emisor sea auténtico |
| B: hash de bytes recibidos | _huella sobre bloques aceptados y escritos completamente hasta EOF | Persistencia física durable ni autenticidad de esos bytes |
| C: hash por relectura | Lectura real del temporal cerrado y del destino reabierto, con límites y firmas | Custodia independiente o resistencia al corte eléctrico |
| D: referencia independiente | **No implementada** | Una huella del llamador no se transforma en autoridad independiente |
| E: autenticidad del origen | **No implementada** | SHA correcto no autentica institución ni significado científico |

verificar_fisicamente usa referencia/solicitud tipadas y una raíz TEMP derivada,
no rutas de origen históricas ni storage_ref operativos. No crea carpetas, archivos
o marcadores. Su primera llamada desde un proceso nuevo tampoco escribe una sonda
para resolver TEMP. La prueba independiente instala la barrera antes de importar
SPICA y niega sockets, SQLite, escrituras y lecturas de SPICA_DATOS.

La comprobación exige vinculación compatible, ausencia de escritor conocido,
archivo regular sin enlaces/reparse points, tamaño, hash y firmas estables del
nombre/descriptor antes/después. Una alteración concurrente observada deja medición
no disponible; no se presenta un prefijo como hash completo. bytes_leidos conserva
el prefijo efectivamente leído cuando falla o se cancela una lectura.

Una discrepancia de tamaño se puede demostrar mediante stat sin leer el cuerpo:
en ese caso sha256_fisico=None y lectura_completa=False. Hash diferente tras
relectura completa sí representa fallo comprobado. Si falta el archivo, no se
confunde esa ausencia con una comprobación de hash fallida.

La evidencia es histórica a fecha_utc. Después de modificar o retirar el archivo,
un informe anterior no garantiza disponibilidad actual: debe repetirse la lectura.
Al cerrar el entorno TEMP, la referencia no recrea su raíz y una nueva comprobación
devuelve AUSENTE. No se promete recuperación persistente.

## Piloto realmente ejecutado

Se reutilizó la fixture RC4 con dos proyectos independientes, cuatro descriptores,
perfiles RC2, contextos RC1, dos operaciones y una composición RC3. Los preparados
y derivados recibieron contenido sintético explícito; **no se ejecutó ninguna
transformación para producirlo**. Cada publicación fue leída de nuevo físicamente.

| Proyecto / objeto / revisión | Tipo lógico | Bytes físicos | SHA-256 físico |
|---|---|---:|---|
| proyecto-A / objeto-original / r1 | ORIGINAL, DESCRITO | 58 | e752ac22c40f261aa6f6d15f7e874ec2552120bf3191bb46c2c68cce66b507c9 |
| proyecto-B / objeto-original-B / r1 | ORIGINAL, DESCRITO | 58 | e752ac22c40f261aa6f6d15f7e874ec2552120bf3191bb46c2c68cce66b507c9 |
| proyecto-A / objeto-preparado / r1 | PREPARADO, DESCRITO | 43 | 514bb28a1b15c2ca9768a5018f45f467255470ee86b16685232ae4f869ad64d4 |
| proyecto-A / objeto-derivado / r1 | DERIVADO, PARCIAL | 48 | 2909df4a3b4dfb87811a2e4aaa8c55504fc87f09ff68067a9e1571cda4b2587b |

UTC de las cuatro verificaciones finales, respectivamente:

```text
2026-11-16T05:05:35.582955+00:00
2026-11-16T05:05:35.650346+00:00
2026-11-16T05:05:35.719103+00:00
2026-11-16T05:05:35.790599+00:00
```

Son fixtures, no adquisiciones institucionales ni activos RAW. Ambos originales
tienen archivos e identidades distintos a pesar del contenido compartido. Se
comprobó que permanecían intactos durante la variante corrupta del preparado.
El bloqueo heredado bloqueo-rc4 llega a preparado/derivado. RC3 conserva su
operación PARCIAL y RC4 su salida PARCIAL; la conclusión técnica RC5 solo describe
la escritura/relectura completa del prefijo suministrado. Revisión científica:
NO_EVALUADA. Las disponibilidades nativas RC4 no se modifican automáticamente.

Un segundo proceso Python de .venv leyó el preparado y obtuvo **43 bytes** y
SHA **514bb28a1b15c2ca9768a5018f45f467255470ee86b16685232ae4f869ad64d4**.
Se ejecutó con la barrera de solo lectura; autenticidad/custodia no acreditadas.
Comparte cuenta, equipo y dominio de fallo con el escritor: no es custodia
independiente ni recuperación del cierre integral RC1–RC4.

La variante corrupta reemplazó solo los 43 bytes del preparado ficticio por Z:

```text
SHA físico: 4587a2535bc507ba17c302e7fd1e46a8028d13c6528ed84d89b9e2794072d632
Estado local: INCONSISTENTE
Integridad: FALLIDA
Diagnóstico: hash_fisico_incorrecto
```

No se reparó ni restauró automáticamente. La raíz principal se liberó al finalizar
su contexto, según la política de disposición de fixtures, sin tocar RAW.

En otra raíz nueva, una fuente que emitió b'prefijo' y luego se interrumpió produjo
**7 bytes recibidos/escritos**, estado técnico PARCIAL, temporal de 7 bytes,
sha256_recibido=None, sin referencia publicada, con fuente_sintetica_interrumpida.
Se inspeccionó el temporal antes de cerrar; la segunda raíz también se liberó.

## Fallos e interrupciones ejercitados

- Recepción correcta, vacío, respuesta por bloques de 2162688 bytes, relectura
  repetida y segundo proceso sin escrituras.
- Archivo ausente, corrupción de igual tamaño, tamaño físico distinto, referencia
  de hash incorrecta, lectura no disponible y cambio observado durante lectura.
- Tamaño/hash recibido incorrectos, límite acumulado excedido antes de escribir
  el bloque adicional, bloques vacíos/tipo incorrecto/superiores a la cota.
- Escritura corta, OSError de disco, fallo fsync y fuente interrumpida. Son fallos
  simulados, sin alegar disco lleno real, ensayo eléctrico o daño de hardware.
- Cancelación previa, durante escritura, durante relectura y después de publicar;
  KeyboardInterrupt propagado con informe. Recursos cerrados y sin éxito ficticio.
- Fallo tras enlace, con ambos nombres conservados dentro del entorno hasta su
  cierre; verificador rechaza ese estado incompleto, no lo reanuda.
- Temporal corrupto antes de su relectura; temporal alterado antes de publicación;
  destino corrupto entre ambas relecturas, sin reparación automática.
- Destino ocupado y colisión de publicación simulada; sin sobrescritura/fallback
  o reintentos. Marcador de escritor existente y lector bloqueado durante escritor
  cooperativo; no se deduce seguridad completa de concurrencia hostil.
- Rutas externas/traversal, nombres Windows/ADS, symlink/junction/reparse simulados,
  y enlace duro real dentro de nuestra fixture, cuyo alias de prueba se retiró.
- Proyecto, revisión, contenido y método productor incompatibles; política heredada
  bloqueante; contradicción del linaje o evidencia aportada; no realineación por SHA.
- Limpieza rechazada ante archivo ajeno de fixture, conservándolo; sin borrado
  recursivo. Errores de creación se convierten en códigos sin exponer rutas.

La suite automatizada contiene 56 pruebas nuevas. Se conservan todos los informes
RC4, perfiles, operaciones y restricciones por referencia. No se cambia JSON QA,
no se llama HTTP ni se instancia AlmacenRAW o un motor durante materialización.

## Límites de las garantías

No se ensayó pérdida eléctrica real, muerte forzada en todas las instrucciones,
filesystem remoto, ACL bajo otra cuenta ni atacante con privilegios del proceso.
UUID, firmas stat y marcador de escritor no son autenticación o referencia
independiente. Existen ventanas TOCTOU; las comprobaciones detectan cambios
observados y no justifican resistencia absoluta.

La raíz se dispone al salir: no hay durabilidad, respaldo independiente, archivo
institucional preservado, codec RC5 o recuperación integral. Futuros controles
requieren versión/alcance y autorización separados; no se activan por este piloto.
