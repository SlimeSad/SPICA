# RC10 — Conservación de evidencias técnicas

Elaboración: 2026-11-20, America/Lima. Perfil experimental
**rc10.evidencias.0.1.0**, exclusivamente para memoria y TEMP sintético.
[Auditoría](auditoria_arquitectonica_rc10.md) y
[recuperación](recuperacion_evidencias_tecnicas_rc10.md).

## Decisión de compatibilidad

El expediente es el contenido de un artefacto RC4 independiente. Su publicación,
relectura, conservación, inventario, cierre y traslado usan **RC5 y RC6 existentes**.
No se implementa otro almacén, manifiesto, catálogo SQL o motor de recuperación
física. No se agregan campos al formato `rc6.generacion.0.1.0` ni clases a su
registro. Un lector RC6 antiguo puede verificar el artefacto como bytes; para
interpretarlo necesita explícitamente el perfil RC10. Una generación antigua no
adquiere evidencias nuevas por usar el lector RC10.

Se mantienen intactos RC1–RC9, JSON QA 0.1.0, codec 85-J, manifiesto 85-K y
SQLite 85001. No hay migraciones ni cambios en `__init__.py` históricos.
La importación de los dos módulos nuevos es explícita.

## Contratos y referencias

API en [conservacion_evidencias.py](../src/spica/artefactos/conservacion_evidencias.py).

| Contrato | Datos y responsabilidad |
|---|---|
| ExpedienteEvidencias | evidencia_id, proyecto RC1 completo, fecha UTC real de captura del expediente, cierre RC8 completo o None, admisión RC9 completa o None, hechos históricos y versión de perfil |
| HechosHistoricos | Captura RC8 observada, estado y cierre específico entonces; comprobación RC9 observada, estado efectivo y admisión específica entonces. Son observaciones conservadas, no testigos restaurados |
| ControlEvidencias | ControlGeneracion RC6, referencia RC4 del portador con revisión, project_id esperado, evidencia_id esperado y perfil. Debe llegar por un canal que el llamador considere confiable |
| RecuperacionEvidencias | Recuperación física RC6 actual, expediente histórico cuando supera el contraste, informe de consumo actual separado, diagnósticos y garantías no concedidas |

Se conservan **todos los campos públicos de los contratos nativos admitidos**:
solicitudes, inventario, proyecto/configuración, operación productora y snapshot
observado, entrada QA nativa con su contexto, resultado, productor/versión,
consumidor/versión/finalidad/límites, identidad de contenido, artefacto/revisión,
informes RC3/RC4, consumo nativo, restricciones y sus orígenes, diagnósticos,
referencias físicas e informes RC5 aportados. Las constantes derivadas también
se recalculan y contrastan. No se reemplazan por un DTO resumido de éxito.

La fecha nueva corresponde a `capturar_evidencias`, no a la exportación ni al
consumo anteriores, que no tenían reloj propio. Las fechas físicas nativas se
preservan con su alcance original. No se inventa identidad institucional.

Identidades distintas: generación lógica RC6, UUID de raíz TEMP, evidencia,
proyecto/contexto, operación QA fuente, resultado QA, operación exportadora,
artefacto/revisión, contenido y huella. Un mismo SHA no fusiona proyectos.
No se atribuye al nodo consumidor RC3 una ejecución que RC9 no registró.

## Perfil cerrado y serialización

[_codec_evidencias_rc10.py](../src/spica/artefactos/_codec_evidencias_rc10.py)
proyecta los contratos admitidos en tablas de datos y referencias enteras.
Delega JSON, codificación de escalares/fechas/Decimal y presupuestos al codec RC6
sin modificarlo. La envolvente explícita tiene exactamente `perfil` y `cuerpo`;
el cuerpo usa la representación de datos RC6 como primitiva, con una raíz RC10
distinta. No es una evolución silenciosa de los metadatos RC6.

Registro literal: tipos admitidos por RC6 y tipos concretos adicionales de
RC8/RC9, informes RC3/RC4, vínculo RC1, resultado/configuración QA, consumidor y
presupuestos. No se buscan clases a partir de imports aportados por el archivo.
Otros tipos anidados se rechazan; no se descartan campos para hacerlos encajar.
En particular, este perfil no conserva cierres QA de composiciones ni un lote
científico general. La entrada puntual QA del exportador sí se conserva completa.

Los dos únicos campos privados excluidos son `_captura` RC8 y `_comprobacion`
RC9. Después de reconstruir las dataclasses permanecen None. Las referencias
compartidas de los campos públicos se mantienen, incluidas las que recalculan los
constructores, después de comprobar su igualdad. No se restaura un testigo True.

Las cadenas y bytes iguales usan una tabla común de contenido UTF-8/hexadecimal;
las referencias conservan la distinción str/bytes. No se repite el documento
para cada informe que lo referencia. El resultado pequeño es parte del contenido
del expediente, **no de su descriptor**. No se guardan datasets en descriptores.
La información QA nativa y su representación JSON son evidencias distintas.

Límites fijos: expediente serializado hasta 2 MiB; texto/bytes únicos hasta
2 MiB antes de proyectar; hasta 50000 visitas/nodos y profundidad de proyección
48, más los límites JSON RC6 de profundidad 64/50000 nodos. El hexadecimal y
las tablas consumen el presupuesto serializado: no se promete aceptar un JSON
QA de 2 MiB. Los presupuestos nativos de exportación/consumo no se amplían.
Materialización del portador: máximo 2 MiB, bloques de 65536 bytes.

Se rechazan claves duplicadas, no finitos, clases/campos desconocidos, tipos
incorrectos, bool donde se exige int, ciclos, objetos ocultos, constantes
discrepantes y representaciones no canónicas. Se exige igualdad con la
recodificación determinista. Sin pickle, eval, expresiones ni carga de código.
No se declara equivalencia con JCS o normalización Unicode.

## Conservación

1. `capturar_evidencias(evidencia, admision, evidencia_id=..., proyecto=...)`
   recibe resultados reales explícitos; no invoca al productor. El inspector RC8
   existente contrasta su evidencia. RC8/RC9 ausentes se conservan como None.
2. `codificar_expediente` contrasta informes, identidades, estados, restricciones,
   diagnósticos, tipos, constantes y presupuestos antes de escribir. No confunde
   un resultado negativo correctamente registrado con corrupción del expediente.
3. El llamador aporta un inventario RC4 portador con un único descriptor, sin
   producciones/composiciones ficticias: mismo proyecto completo, contenido_id
   igual a evidencia_id y formato igual al perfil. ORIGINAL significa raíz de ese
   inventario documental acotado; nunca original RAW confirmado.
4. El portador debe conservar todas las restricciones conocidas. No se elige una
   variante permisiva. Si sus restricciones no son representables coherentemente
   por RC4/RC6, se rechaza antes de conservar; no se promete persistencia universal
   de informes conflictivos. Los informes nativos dentro del expediente no se editan.
5. `conservar_evidencias` materializa el expediente con RC5 y SHA esperado de sus
   bytes, y llama a RC6 con esa materialización. RC6 vuelve a verificar el origen,
   copia, relee, publica exclusivamente y sella su generación.
6. La raíz RC5 se dispone al terminar. La raíz RC6 pertenece al contexto del
   llamador; retenerla entre procesos requiere la opción nativa explícita.

El expediente incluye su salida JSON pequeña cuando existe. No incorpora archivos
externos QA ni copia automáticamente los localizadores RC5 históricos. Las
referencias de entrada del inventario fuente permanecen externas; la salida sin
resultado también permanece externa. Un archivo RC5 histórico íntegro no se busca
ni se presenta como disponible después del reinicio.

## Recuperación y confianza

`recuperar_evidencias(raiz, control)` exige el control tipado y primero delega
integridad física, versión, inventario y cierre en `recuperar_generacion` RC6.
Selecciona únicamente el portador esperado, lee su nombre generado nativo,
coteja tamaño/SHA, reconstruye el perfil cerrado y contrasta proyecto/evidencia,
restricciones y correspondencias nativas. Recomprueba la generación al final.

El contraste histórico reutiliza el inspector RC8 y la política RC9 en memoria,
deshabilitando expresamente la lectura física de la solicitud histórica. Las
causas y asociaciones de sus comprobaciones físicas se cotejan como metadatos;
no se vuelve a abrir su referencia ni se llama al verificador RC5 histórico.
Los faltantes debidos exclusivamente a los testigos perdidos se separan de los
diagnósticos originales mediante los hechos históricos explícitos. No se ignoran
las restantes contradicciones. La admisión nativa usada como contraste interno
se descarta y no se entrega como nueva admisión del cierre recuperado.

El consumidor nativo vuelve a validar el contenido incorporado y su informe
aparece como `consumo_actual`, separado de ambos informes históricos. Su
contraste interno de codificación no despacha una operación RC8 ni evalúa QA.
No se ejecuta `ejecutar_exportacion_tecnica` para reproducir una captura pasada.

`recuperada_en_alcance` significa expediente reconstruido y portador verificado,
no admisión actual ni estado científico. Los estados físicos detallados de RC6
y los diagnósticos RC10 permanecen separados: una generación de bytes verificada
puede contener un expediente de perfil incompatible y no ser recuperable por RC10.
`externos_actuales` informa NO_DISPONIBLE, nunca AUSENTE por inferencia.

Los estados históricos apto/incompatible/pendiente y los snapshots
DECLARADA/PLANIFICADA/INICIADA/CONCLUIDA/PARCIAL/FALLIDA/CANCELADA se preservan.
Un expediente íntegro puede documentar exportación bloqueada, salida parcial,
admisión rechazada o evidencia faltante. Eso no los promueve.

Permanecen False: nueva comprobación local RC8, nueva admisión RC9, habilitación
RC3/RC7, autenticidad, validación científica y autorización. Los informes rechazan
bool genérico. Un control y su SHA no autentican productor/consumidor ni impiden
sustituir coordinadamente expediente y control bajo la misma autoridad.

## Seguridad y límites no ampliados

Se reutilizan las barreras TEMP de RC5/RC6: base validada, raíces exclusivas,
rechazo de symlinks/junctions/reparse points, rutas léxicas y nombres cerrados,
identidades de directorio/archivo, archivos regulares, publicación exclusiva y
limpieza no recursiva de nombres/inodos propios. Un escritor cooperativo por raíz.
Event se delega en las fases físicas; no interrumpe la codificación en memoria.
No hay garantía eléctrica, custodia independiente o exclusión frente a Python
hostil. fsync de archivo no equivale a transacción de directorio o respaldo.

No se modifican ACL ni se asegura confidencialidad de un contexto que el llamador
incluya. Las excepciones/diagnósticos nuevos usan códigos, no rutas o mensajes
del productor. No se admiten datos privados/institucionales en este incremento.

RC3/RC7 necesitarían una evolución posterior aprobada de requisito por arista,
tipo de cierre no QA admitido, productor/versiones/alcance, confianza histórica,
actualidad y evidencia exigida. RC10 no modifica esos contratos ni incorpora un
segundo inspector de dependencias. La arquitectura integral permanece abierta.
