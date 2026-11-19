# RC8 — Cierre específico del exportador técnico JSON

Fecha: 2026-11-19, America/Lima. Contrato local en memoria **0.1.0**.
[Auditoría](auditoria_arquitectonica_rc8.md), [piloto](piloto_cierre_productor_rc8.md).

## Productor y fronteras

Se selecciona exclusivamente
[exportar_resultado_json](../src/spica/calidad/exportacion.py), versión de
exportación 0.1.0. Recibe ResultadoQA y ContextoExportacionQA nativos y devuelve
un str JSON. No evalúa reglas QA ni produce un resultado científico nuevo.
El JSON QA 0.1.0 no se modifica para insertar campos RC8.

La entrada QA se conserva mediante VinculoResultadoQA de RC1; no se fabrica
InformeQA o CierreQA para representar la exportación. El piloto obtiene la
entrada ejecutando evaluar_registro existente sobre una fila inventada. Eso
demuestra un resultado puntual, no un recorrido completo o un cierre QA de lote.

El artefacto de entrada identifica el ResultadoQA suministrado, con entrada_id
igual a su referencia_resultado y tipo_recurso resultado_qa_nativo. Su descriptor
ORIGINAL significa raíz de este inventario acotado en memoria; no un original
RAW confirmado. No se presenta al CSV de procedencia como el argumento exportado.
El origen QA y su vínculo se mantienen aparte: RC4 no acepta fingir un dataset
derivado mediante una producción de tipo QA_NIVEL0.

## Contratos y operaciones explícitas

El módulo [cierre_exportacion.py](../src/spica/artefactos/cierre_exportacion.py)
añade tres dataclasses congeladas con slots:

| Contrato | Información |
|---|---|
| SolicitudExportacionTecnica | Inventario RC4, composicion_id, operacion_id, referencia/revisión de salida, vínculo QA de entrada, LimitesComposicion, LimitesExportacionQA y versión |
| EvidenciaExportacion | Solicitud, snapshot de operación observada, str nativo o ausencia, indicador productor_invocado, tamaño/hash de bytes UTF-8 en memoria, diagnósticos y versiones/identidad del productor |
| InformeCierreExportacion | Evidencia, informes nativos RC4/RC3 y de consumo JSON, restricciones unidas, diagnósticos y garantías explícitamente separadas |

ejecutar_exportacion_tecnica invoca una vez el productor fijo cuando se llama
explícitamente y cumple sus condiciones. No recibe funciones, nombres dinámicos,
endpoints o rutas. No ejecuta planes ni operaciones dependientes, no reintenta,
publica archivos o persiste evidencia. El llamador debe aportar una operación
DESCRIPCION_ESTRUCTURAL ya INICIADA y una producción 1→1 correspondiente.
El método y versión RC4 deben coincidir exactamente con el exportador seleccionado.

La composición, operación, entradas, salida PREPARADO/application/json y revisión
deben corresponder; se reutilizan inspeccionar_linaje, inspección RC3 y validadores
RC1. El perfil de salida describe las claves técnicas, sin inventar variables,
unidades o estaciones. El uso explícito es exportar_json_qa0_rc8.

inspeccionar_cierre_exportacion coteja evidencia ya aportada, sin despachar una
operación ni evaluar QA. Usa consumir_exportaciones para el esquema, identidad,
huella, coherencia y restricciones JSON. Ese consumidor **reserializa internamente**
como contraste nativo; no es una nueva invocación de operación registrada ni una
reevaluación. Se reutiliza _Conversion del exportador para cotejar resultado y
contexto originales, sin un codec o parser de clases alternativo.

## Declaración, captura y comprobación

Una evidencia construida externamente o copiada mediante dataclasses.replace
puede ser contractualmente coherente, pero no acredita invocación observada.
La captura interna vincula el snapshot, solicitud y salida que obtuvo esta llamada;
captura_local_coherente comprueba que no cambiaron esos datos.

Este testigo privado no se exporta ni conserva, no es firma ni defensa contra
Python hostil. Un proceso que modifica deliberadamente objetos privados o el
código puede falsearlo. No se implementan autenticación, identidad del operador,
reloj certificado, permiso efectivo o garantía de ejecución única por operacion_id.
La coordinación de IDs/repeticiones sigue siendo responsabilidad del llamador.

cierre_tecnico_comprobado exige captura local coherente, invocación observada,
operación observada CONCLUIDA, consumidor nativo conforme, correspondencia con
la entrada y ausencia de pendientes/contradicciones en ese cotejo específico.
No existe un estado universal valido. EstadoAptitud se reutiliza para los
diagnósticos, EstadoOperacion para los snapshots y EstadoConsumoQA para el JSON.
Los informes nativos RC3/RC4 pendientes se conservan separados, sin suplantarlos.

## Estados y restricciones

| Situación | Tratamiento |
|---|---|
| DECLARADA, PLANIFICADA o terminal aportada | No se invoca ni se promueve; CONCLUIDA declarada no es cierre |
| INICIADA y productor devuelve salida | Nuevo snapshot observado CONCLUIDA; todavía debe superar el cotejo técnico |
| Excepción del productor o salida de tipo/tamaño inadmisibles | FALLIDA, sin salida completa ni cierre; causa sanitizada |
| Event antes de invocar | CANCELADA si estaba INICIADA, sin invocación |
| KeyboardInterrupt durante la llamada | CANCELADA, con invocación observada y sin salida completa |
| Event observado tras obtener salida | PARCIAL para el cierre, conservando la salida y su referencia; no se afirma que el JSON esté truncado |
| Artefacto o estado inicial parcial/fallido/cancelado | Se conserva, sin reabrir o concluir la operación |

El exportador es atómico en memoria y no acepta Event; no se puede interrumpir
cooperativamente dentro de su codificación. No hay timeout forzoso, reanudación
o prefijos recuperables. Las transiciones usan cambiar_estado y producen otros
snapshots; no modifican el inventario histórico, tiempos u operadores.

Se unen las restricciones del contexto, vínculo QA, entrada/salida RC4 y
propagadas por RC3/linaje. Un bloqueo aplicable impide invocar. Una finalidad
no declarada queda pendiente. Los bloqueos de otros usos se conservan y no
impiden por sí solos una exportación permitida en este ensayo. La envolvente RC8
conserva restricciones adicionales RC1/RC4 que el JSON histórico no representa;
entregar solo ese JSON no equivale a entregar todo el cierre y sus condiciones.
Ante un código con variantes contradictorias se reutiliza la unión conservadora
RC7: ambas variantes permanecen en el informe y no se invoca el exportador.

## RC3–RC7, materialización y conservación

La evidencia RC8 no es CierreQA ni un cierre no QA admitido por RC3. No modifica
su informe ni habilita dependencias. El consumidor hipotético del piloto continúa
pendiente en RC3 y RC7, aun cuando la exportación específica se compruebe.

El SHA de EvidenciaExportacion corresponde a los bytes en memoria. No demuestra
existencia física. El piloto entrega **esa salida realmente generada** a RC5,
que materializa y relee mediante sus APIs. Esas comprobaciones físicas permanecen
en informes RC5 separados. La captura histórica no promete disponibilidad futura:
si se elimina/corrompe la copia TEMP, la lectura física lo detecta y el hecho
de que la función hubiera generado el JSON sigue siendo histórico.

RC6 puede conservar el inventario descriptivo y los bytes incluidos; no conserva
EvidenciaExportacion, su testigo o InformeCierreExportacion. La entrada QA lógica
externa sigue sin bytes comprobados por esa generación. Recuperar el JSON no
recupera el cierre técnico ni una evaluación QA. No cambia rc6.generacion.0.1.0.

## Límites y confianza

Se mantienen las cotas nativas de exportación: 1 MiB por defecto, máximo 4 MiB,
texto/nodos/profundidad explícitos. RC8 procesa un resultado, no datasets grandes.
La medición RC3 recorre la solicitud antes de inspeccionar. Se aplica el mínimo
de sus límites y los de la composición; RC3 aplica las cuotas de la composición.
El consumo JSON es acotado a un documento y al tamaño autorizado para exportar.
No se mide RSS/CPU ni se reserva espacio; RC5/RC6 mantienen sus límites propios.

No se conceden permisos ni se afirman validez científica, autenticidad institucional,
aplicabilidad documental, original RAW, custodia o durabilidad. Permanecen cerrados
JSON QA 0.1.0, formatos 85-J/K, SQLite 85001 y RC6; no hay migraciones o contratos
públicos anteriores modificados. Los errores usan códigos, sin copiar excepciones
del productor que puedan contener rutas o credenciales.
