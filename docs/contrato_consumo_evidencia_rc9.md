# RC9 — Consumo técnico respaldado por evidencia de exportación

Contrato experimental **0.1.0**, elaborado el 2026-11-19, America/Lima.
Alcance: un documento JSON QA Nivel 0 en memoria, producido mediante RC8,
para el consumidor nativo existente. La [política de admisión y conservación](politica_admision_conservacion_rc9.md)
y la [auditoría](auditoria_arquitectonica_rc9.md) delimitan su uso.

## Reutilización y responsabilidades

| Componente real | Responsabilidad reutilizada |
|---|---|
| [Consumidor 85-D](../src/spica/calidad/consumo.py), `consumir_exportaciones` | Parseo acotado, perfil cerrado, identidades internas, contraste nativo, restricciones, informe y presupuestos |
| [Contrato del consumidor](contrato_consumo_qaqc_paso85d.md) | Perfil de entrada y límites de confianza existentes |
| [Exportador 85-C](../src/spica/calidad/exportacion.py), `exportar_resultado_json` | Productor real invocado explícitamente por RC8 durante el piloto |
| [Cierre RC8](../src/spica/artefactos/cierre_exportacion.py) | Captura local y comprobación de invocación, estado, entrada nativa, salida y políticas |
| [Contrato RC8](contrato_cierre_tecnico_noqa_rc8.md) | Fronteras entre exportación, QA, declaraciones y pruebas físicas |
| [Contextos RC1](../src/spica/contextos/modelos.py) | Proyecto, entradas, operación e identidad independiente de rutas |
| [Artefactos RC4](../src/spica/artefactos/modelos.py) y linaje | Object_id, revisión, identidad de contenido y restricciones heredadas |
| [Materialización RC5](../src/spica/artefactos/materializacion.py) | Referencia física controlada y relectura actual opcional |
| [Coordinación RC7](../src/spica/artefactos/coordinacion.py) | Unión de restricciones que conserva variantes ante conflictos |
| [Consumidor RC9](../src/spica/artefactos/admision_exportacion.py) | Adaptador específico de admisión; no añade otro parser |

El adaptador recibe bytes/texto y evidencia explícitos. No busca rutas, archivos,
catálogos ni productores; no dispone de callbacks, nombres de clases ejecutables
o un registro dinámico. Su importación experimental es explícita, sin modificar
los `__init__.py` estables. No se agrega un consumidor, exportador o motor QA.

## API y datos

`admitir_exportacion_tecnica(SolicitudAdmisionExportacion) -> InformeAdmisionExportacion`.

`SolicitudAdmisionExportacion` es una dataclass inmutable con:

| Atributo | Significado |
|---|---|
| contenido | Un único `bytes` UTF-8 o `str`; `None` expresa ausencia. No admite rutas, listas ni lotes |
| evidencia | `EvidenciaExportacion` RC8 o `None`; se vuelve a inspeccionar, no se admite un informe positivo aportado en su lugar |
| proyecto | ContextoProyecto RC1 esperado completo, incluido project_id MD, contexto, configuración y restricciones |
| operacion_productora_id | Identidad explícita de la operación exportadora esperada |
| entrada_resultado_id | Referencia lógica del resultado QA que entró al exportador; no es el asset RAW ni el ID de la fila CSV |
| artefacto | ReferenciaArtefacto RC4 esperada: object_id y revisión literal |
| contenido_id | Identidad lógica de contenido esperada, distinta de SHA-256 |
| consumidor_id | Identidad fija `spica.calidad.consumo.consumir_exportaciones` |
| version_consumidor | Versión admitida del contrato de consumo: 0.1.0 |
| finalidad | Único uso admitido: `consumir_json_qa0_rc9` |
| limites | LimitesConsumoQA nativos, con sus máximos duros |
| exigir_integridad_fisica | Booleano explícito; predeterminado False para consumo en memoria |
| materializacion | InformeMaterializacion RC5 opcional, con solicitud y referencia controladas; no se usa su veredicto histórico como prueba actual |
| version_contrato | Versión RC9 0.1.0; no es una versión institucional |

Los tipos incorrectos, versiones no soportadas de la propia solicitud y límites
mal configurados son errores del llamador: TypeError/ValueError con códigos
fijos. Un JSON recibido erróneo, incompatible o excesivo produce un informe
nativo y diagnósticos RC9. No se rellenan propiedades desconocidas.
Las identidades esperadas deben proceder del contexto que el llamador pretende
contrastar. Copiarlas de una fuente no confiable y compararlas consigo mismas
no establece confianza ni autorización externa; el adaptador no las autentica.

`InformeAdmisionExportacion` conserva la solicitud, el consumo nativo, la
inspección RC8, la verificación física actual si se realizó, todas las restricciones
conocidas y los diagnósticos ordenados. Conserva las declaraciones y la evidencia
sin convertirlas en acreditación independiente. No contiene un nuevo formato
serializado, control de permisos ni representación de originales RAW.

Estados reutilizados de EstadoAptitud:

| Estado nativo | Interpretación específica RC9 |
|---|---|
| APTO_ESTRUCTURALMENTE | Admisible para este consumo técnico, dentro del alcance efectivamente comprobado |
| INCOMPATIBLE | Inadmisible: contradicción o incumplimiento comprobado |
| PENDIENTE_DE_EVIDENCIA | Falta evidencia o una comprobación no terminó |

Una contradicción prevalece sobre faltantes. `admisible_para_consumo_tecnico`
exige el estado apto, cierre RC8 comprobado y consumo nativo positivo; además,
integridad física actual cuando se solicitó. `bool(informe)` genera TypeError.
`autoriza_operacion`, `autorizacion_concedida`, `validacion_cientifica_realizada`
y `habilitacion_rc3_concedida` permanecen False.

## Procedimiento real

1. Comprobar contratos tipados, versión propia, consumidor fijo y finalidad.
2. Invocar `consumir_exportaciones` sobre el documento recibido con sus límites.
3. Inspeccionar la evidencia RC8 mediante su función existente.
4. Comparar proyecto completo, operación, entrada lógica, artefacto/revisión e
   identidad de contenido esperados. RC8 contrasta la operación observada, el
   productor y su versión y la entrada QA nativa.
5. Comparar los bytes recibidos con la salida UTF-8 capturada, después de los
   presupuestos y la validación nativa. El JSON resultado_id y su huella internos
   se contrastan en el consumidor y su asociación con la entrada en RC8.
6. Unir restricciones del proyecto esperado y del cierre RC8 mediante la unión
   existente RC7. Conservar las variantes contradictorias y rechazarlas.
7. Aplicar bloqueos del uso `consumir_json_qa0_rc9`. Una restricción científica
   heredada no desaparece porque el uso técnico esté admitido.
8. Si se exige integridad física y las precondiciones anteriores son aptas,
   comprobar la asociación RC5 y llamar a `verificar_fisicamente`. No se lee ante
   identidad contradictoria, captura faltante, consumo incompleto o uso bloqueado.
9. Devolver el informe y registrar su comprobación local cooperativa, sin
   modificar estados previos ni habilitar dependencias.

Hay dos llamadas de validación nativa con responsabilidades distintas: RC9
valida el documento recibido con el presupuesto solicitado; el inspector RC8
valida su propia salida capturada y su correspondencia con la entrada. No existe
un segundo parser ni reglas JSON implementadas en el adaptador RC9. El
consumidor nativo reexporta datos conocidos como contraste puro de codificación;
eso no despacha una operación productora ni reevalúa reglas QA.

La igualdad exigida es literal UTF-8: agregar espacios puede conservar un JSON
estructuralmente válido, pero produce bytes distintos del resultado capturado y
se rechaza para esta política. No se normalizan valores, unidades, identificadores,
HORA, UBIGEO ni zonas horarias. No se modifica el paquete JSON QA.

## Versiones, límites y diagnósticos

No se añaden versiones científicas por inferencia. El consumidor nativo admite
JSON QA 0.1.0, contrato QA/reglas 1.0.0, evaluador 1.0.1 y restricciones 1.0.0.
RC8 y su productor exportador deben ser 0.1.0. Las identidades y versiones del
consumidor son constantes contrastadas, nunca nombres para resolver código.

Se mantienen todos los presupuestos nativos: por defecto 1 MiB por documento,
4 MiB por lote, profundidad 20, 20000 nodos/documento, strings hasta 65536
caracteres y 32 restricciones/documento; sus topes configurables siguen en
LimitesConsumoQA. RC9 solo admite un documento y no aumenta esos límites.
RC8 mantiene sus cotas de exportación/descriptores y RC5 sus cotas físicas.
La comparación UTF-8 se realiza después de validar tamaños. Los presupuestos
de RC9 y RC8 son independientes; un faltante no se convierte en aceptación.

Diagnósticos propios destacados: `consumidor_o_version_no_admitidos`,
`proyecto_esperado_no_corresponde`, `operacion_productora_no_corresponde`,
`entrada_resultado_no_corresponde`, `artefacto_o_revision_no_corresponde`,
`identidad_contenido_no_corresponde`, `contenido_distinto_de_captura_rc8`,
`evidencia_rc8_no_aportada`, `cierre_rc8_no_comprobado`,
`restriccion_impide_consumo_rc9`, `integridad_fisica_contradictoria` y
`integridad_fisica_no_comprobada`. Los informes nativos completos preservan
el detalle de sus propias comprobaciones y problemas. No se copian mensajes
de excepciones ni valores recibidos en estos códigos.

Sin captura RC8, se conservan las restricciones tipadas del proyecto conocido
y el informe nativo con los JSON aceptados y sus restricciones internas. No se
inventa una reconstrucción RC4 ni se reparan restricciones ausentes. Las
restricciones del contexto RC4/RC8 no se insertan retroactivamente en JSON 0.1.0.

## Evidencia física y frontera de confianza

La verificación opcional solo usa referencias RC5 de TEMP controlado; no recibe
una ruta arbitraria. Compara inventario, proyecto, artefacto/revisión, contenido,
tamaño y hash con RC8. Una materialización histórica sin estado CONCLUIDA
queda pendiente. RC5 vuelve a comprobar el vínculo y relee el archivo con sus
controles de raíz, identidad, archivo regular, límites y SHA-256 físico.

Archivo ausente o lectura no disponible: pendiente. Bytes corruptos: inadmisible.
No se sustituyen estas comprobaciones con `InformeMaterializacion.verificacion`.
La fecha UTC de InformeVerificacion es la de esa lectura y no garantiza que el
archivo siga igual después. RC9 no escribe archivos. La escritura/materialización
del piloto se hace explícitamente mediante RC5 y se limpia en sus contextos TEMP.

Sin exigencia física, un informe RC5 aportado permanece como contexto histórico:
no genera relectura implícita ni una afirmación de disponibilidad actual. Una
salida admitida en memoria puede carecer de archivo físico disponible.

La captura local RC8 debe permanecer coherente; construir o copiar su dataclass
no acredita ejecución observada. Análogamente, un informe RC9 construido o
copiado pierde su testigo local y su estado efectivo incorpora un faltante;
`comprobacion_local_coherente` permite distinguirlo. El faltante calculado para
ese caso no reescribe la tupla histórica de diagnósticos. El testigo no se
serializa ni se admite como firma. Los informes se obtienen llamando a las APIs.

Estos controles protegen contra atribuciones accidentales en un proceso Python
cooperativo. No son una barrera frente a código hostil que modifica objetos,
intercepta funciones o accede a detalles internos del proceso. No acreditan
autenticidad institucional, independencia de custodia, ejecución QA por un tercero,
revisión científica, licencias ni permisos. Proyecto y procedencia siguen siendo
contextos declarados contrastados, sin autenticación externa.

## Integración admitida y pendiente

RC9 no convierte InformeCierreExportacion en CierreQA. Si existe un cierre QA
nativo genuino, conserva su contrato y su alcance anterior; no se fabrica uno
para la exportación. RC3/RC7 siguen considerando pendiente la dependencia del
productor no QA, aunque el consumo técnico RC9 haya sido apto.
Invocar la función nativa para inspeccionar el documento no concluye el nodo
de operación `consumidor` descrito en la composición del piloto. No se modifica
esa operación ni se acredita su ejecución bajo un contrato de coordinación.

RC6 puede conservar los bytes y el inventario históricos que admite su perfil
actual; no conserva directamente las capturas RC8/RC9 ni vuelve a observar una
ejecución. Recuperar una generación no recupera esos testigos ni demuestra
disponibilidad de referencias externas. La evolución propuesta y no implementada
se describe en la [política](politica_admision_conservacion_rc9.md).

La arquitectura integral, la autorización operativa, la incorporación de nuevos
productores y la conservación de esta evidencia permanecen pendientes de revisión.
