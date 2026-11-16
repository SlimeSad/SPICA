# RC6 — Recuperación de linaje y comprobación física

Fecha: 2026-11-16, America/Lima. Perfil **rc6.generacion.0.1.0**.
[Contrato/formato](conservacion_versionada_artefactos_rc6.md),
[auditoría](auditoria_arquitectonica_rc6.md),
[pruebas](../tests/test_conservacion_rc6.py).

## Protocolo independiente

El llamador aporta raíz **actual** y ControlGeneracion tipado. El lector:

1. Comprueba léxicamente raíz bajo la base TEMP validada y nombre spica-rc6-UUID,
   después ancestros, tipo/identidad física. Nunca abre una raíz arbitraria.
2. Inspecciona un inventario físico acotado. Marcador escritor o temporales implican
   INCOMPLETA, sin borrar, reparar, reanudar o intentar crear un sello.
3. Exige intención, manifiesto, metadatos y cierre; lee realmente por bloques,
   coteja tamaños/canonicalidad, formato, identidad y hash contra el control aportado.
4. Decodifica el grafo tipado de lista cerrada, preservando referencias compartidas.
   Recalcula linaje RC4 y composiciones RC3, sin ejecutar productores ni QA.
5. Coteja clausura de restricciones/diagnósticos/orden con la guardada. Las
   contradicciones de identidades, revisiones, proyectos, productores, resultados,
   ciclos o enlaces faltantes impiden el éxito. Los pendientes documentales se
   conservan, sin confundirse con una generación físicamente incompleta.
6. Regenera inventario físico y nombres seguros; coteja exactamente con manifiesto.
   Rechaza archivos extra, referencias inseguras, versiones/campos/tipos desconocidos.
7. Por cada contenido incluido: existencia, regularidad, ausencia de enlaces,
   tamaño y SHA-256 mediante lectura estable. Contrasta con informe RC5 y descriptor.
8. Separa las referencias externas: NO_DISPONIBLE, sin ruta relativa, tamaño/hash
   actual ni lectura. No se busca una raíz histórica ni se abre un RAW externo.
9. Revalida inventario, ausencia de escritor, metadatos/sello y firmas de contenidos
   ya leídos para detectar cambios observados. No promete una instantánea atómica.

La lectura desde un proceso recién iniciado no escribe sondas TEMP, índices,
SQLite, marcadores ni bytecode. El piloto lector utiliza .venv con -B y una barrera
antes de importar SPICA: niega sockets, sqlite3.connect, escritura, mutaciones de
filesystem y apertura de SPICA_DATOS. Esto comprueba los caminos del ensayo;
no es un sandbox hostil de producción ni autenticación independiente.

## Estados actuales e históricos

| Dimensión | Conservación / interpretación |
|---|---|
| Lógica | Descriptor RC4 DESCRITO/PARCIAL/FINAL_DECLARADO intacto |
| Operativa | ContextoOperacion y estado_tecnico RC5 intactos, con significado diferente |
| Física histórica | EstadoPublicacion e informe RC5 tal como fueron aportados |
| Física actual | ComprobacionContenido: INTEGRO, INCONSISTENTE, AUSENTE o NO_DISPONIBLE |
| Integridad | SHA/tamaño actuales solo cuando realmente medidos; ausencia/acceso fallido no inventan hash fallido |
| Conservación | Intención/sello históricos separados de EstadoRecuperacion actual |
| Científica | NO_EVALUADA, sin promoción por recuperar bytes o conseguir hashes iguales |

EstadoRecuperacion: VERIFICADA significa cerrado/verificado **en alcance**;
INCOMPLETA significa raíz/metadatos/copia obligatoria ausentes o preparación sin
cierre; CORRUPTA requiere discrepancia física comprobada de tamaño/hash;
INCOMPATIBLE representa contratos, controles o relaciones contradictorias;
NO_DISPONIBLE indica cancelación, lectura imposible o estado que requiere revisión.
Un hash de metadatos discrepante impide confianza estructural; no se presenta como
prueba de que un archivo científico fue validado. Los diagnósticos precisan la causa.

Para tamaño distinto, se registra tamaño real y sha256_fisico=None,
lectura_completa=False. Para corrupción de igual tamaño se relee todo y se registra
el SHA realmente obtenido. Ninguna recuperación cambia el inventario original ni
concluye operaciones parciales/canceladas/fallidas. Recuperar no concede permisos.

## Piloto y traslado

La prueba productor_terminado_traslado_y_lector_independiente ejecuta:

1. Python A crea cuatro cuerpos sintéticos con RC5, dos proyectos, dos productores
   y linaje RC4; conserva la generación y su control. Cierra y dispone la raíz RC5.
2. A termina normalmente dejando solo la generación TEMP retenida explícitamente.
3. Python B, sin factories de tests ni objetos de A, usa el lector público y la
   barrera de solo lectura; reconstruye identidades, estados, restricciones y hashes.
4. Se copia a otra raíz TEMP nueva, por bloques y con publicación exclusiva. El
   generacion_id y control se conservan; el ID físico de raíz cambia.
5. Se dispone únicamente la raíz fuente creada por nuestro hijo, comprobando sus
   nombres exactos/regulares antes de unlink, sin recursión. Un nuevo lector B
   recupera el destino sin la raíz RC5 ni la generación fuente disponibles.
6. Los dos resultados B deben coincidir; la disposición del destino comprueba
   propiedad de archivos y raíz mediante el entorno experimental.

Este traslado no modifica 85-J, no utiliza sus rutas históricas y no demuestra
portabilidad entre cuentas, equipos o SO. Ambos TEMP comparten host, cuenta y
dominio de fallo. La barrera confirma ausencia de acceso operativo/red en el lector.

El contenido del piloto continúa siendo el de las fixtures RC4/RC5:

| Referencia | Bytes | SHA-256 esperado y contrastado físicamente |
|---|---:|---|
| objeto-original/r1, proyecto-A | 58 | e752ac22c40f261aa6f6d15f7e874ec2552120bf3191bb46c2c68cce66b507c9 |
| objeto-original-B/r1, proyecto-B | 58 | e752ac22c40f261aa6f6d15f7e874ec2552120bf3191bb46c2c68cce66b507c9 |
| objeto-preparado/r1 | 43 | 514bb28a1b15c2ca9768a5018f45f467255470ee86b16685232ae4f869ad64d4 |
| objeto-derivado/r1 | 48 | 2909df4a3b4dfb87811a2e4aaa8c55504fc87f09ff68067a9e1571cda4b2587b |

El bloqueo heredado bloqueo-rc4 permanece en preparado/derivado. El segundo
productor y su salida siguen PARCIAL; todos conservan revisión NO_EVALUADA.
Dos hashes iguales mantienen archivos distintos; no hay deduplicación de objetos.

## Casos adversos y límites

Se ensayan generación válida, vacía, solo externa, parcial externa, corrupta,
ausente, incompleta y ya retirada; versión/control/hash/tamaño erróneos; rutas
inyectadas; duplicaciones, proyectos incompatibles, ciclo, resultados inexistentes,
restricciones omitidas, operación cancelada y evidencia histórica incoherente.
Se incluyen interrupción antes del sello y tras el enlace, cancelación, ocupación
del destino, fallo de fsync/lectura y mutación de metadatos durante lectura.

La corrupción afecta solo una copia de la fixture; se comprueban originales
sintéticos RC5 y demás copias intactos, sin reparación. Los errores OSError y
reparse/junction se inyectan; el enlace duro adicional se prueba físicamente.
No se simula un corte eléctrico real ni se acredita seguridad concurrente hostil.

Las pruebas del codec cubren claves duplicadas, no finitos/profundidad, referencias
de objetos cíclicas, registros ocultos, campos/versiones/clases desconocidos, tipos
incorrectos y ausencia de ejecución de un literal de código. No se usa pickle.

Limitaciones: perfil descriptivo acotado, entorno cooperativo confiable, ventanas
TOCTOU residuales, reloj local, ausencia de ancla protegida/custodia independiente,
retención y durabilidad operativas, respaldo en otro dispositivo y manejo general
de derivados/exportación. La conservación de metadatos externos no recupera sus
archivos ni su vigencia. No se deshabilita un bloqueo para completar el piloto.
