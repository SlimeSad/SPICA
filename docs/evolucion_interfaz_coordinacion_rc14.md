# RC14 — Evolución opcional de coordinación

Fecha de elaboración: **2026-11-23**, America/Lima. Base `0e8b759`.
Decisión previa a la implementación. Escenario local cooperativo y sintético.

## Alternativas y decisión

| Alternativa | API / complejidad / reutilización | Identidad, seguridad y restricciones | Mantenimiento y pruebas | Decisión |
|---|---|---|---|---|
| A: adaptador externo sobre resultados previos | Mínima; ya existe RC13 | Conserva cotejos, pero no cambia la evaluación real de la arista | Compatible; no resuelve el objetivo RC14 | Insuficiente |
| B: parámetro opcional en inspectores actuales | Aditiva, pero requeriría distinguir informes/semántica de dos modalidades en la API estable | Viable con cotejo previo y recorrido compartido | Exige actualizar el contrato de retorno y probar todos los consumidores | No seleccionada |
| C: interfaces específicas y recorridos internos compartidos | Dos entradas explícitas, sin cambiar firmas anteriores ni duplicar inspectores | RC13 se calcula antes; aporte privado efímero ligado a la composición/arista, sin callback | Informe RC14 versionado separado, con original y vista opcional; regresiones de defaults | **Seleccionada** |

Las interfaces anteriores son `inspeccionar_composicion(composicion, *,
cancelacion=None)` y `inspeccionar_integracion(solicitud, *, cancelacion=None)`.
Se mantienen también los campos/versiones de InformeComposicion e
InformeIntegracion y todos los codecs. Las entradas nuevas se publican únicamente
en un módulo específico RC14; ninguna selección se obtiene de configuración global.

La implementación deberá extraer el recorrido RC3 a una función interna compartida
y añadir un aporte privado opcional al recorrido RC7 existente. Los wrappers
anteriores lo invocarán sin aporte. No se copiará el DAG ni se creará un scheduler.

## Inspección previa y consumidores

RC3 exige aptitud estructural de la predecesora y cierre_qa_coherente_completo.
Ante evidencia no QA deja `dependencia_sin_cierre_tecnico_compatible_aportado`.
RC7 agrega el cotejo de recuperación y
`productor_no_qa_sin_cierre_ejecucion_admitido`, y vuelve a comprobar las aristas
en el orden de RC3. RC8/RC11/RC13 llaman a inspectores predeterminados: invocarlos
recursivamente desde el recorrido produciría reentrada y no es la solución.

Consumidores fuente localizados: inicializadores/modelos/inspector RC3;
modelos/linaje/inspector RC7, cierre RC8, codec RC10 y precondición RC13.
Las llamadas de pruebas están en RC3, RC7, RC8, RC9, RC11 y RC13. No se encontraron
llamadas desde herramientas. No se cambian sus argumentos ni sus contratos de
retorno. Las construcciones/lecturas de informes por codecs siguen intactas.

## Invariantes de la extensión

- Selección explícita, tipificada y versionada para la clase RC13 de exportación
  JSON QA0 hacia el consumidor nativo, no una opción global de cierres no QA.
- El llamador aporta una SolicitudPrecondicionProductora, nunca un dictamen
  SATISFECHA como sustituto. Se vuelve a ejecutar el cotejo nativo RC13.
- Proyecto/contexto completo, composición, dos operaciones, arista, entrada,
  resultado, artefacto/revisión, contenido, versiones y finalidad deben coincidir.
- Se preservan por separado el informe predeterminado y la evaluación opcional.
  No se borran diagnósticos históricos ni se reescriben estados de operación.
- Solo se admite el cierre observado por RC8, validado por RC9 y reconocido por
  RC13 dentro del proceso cooperativo. RC11 mantiene su decisión anterior.
- El estado INICIADA declarado de la productora no cambia: su CONCLUIDA observada
  satisface únicamente esa precondición, sin fabricar un CierreQA.
- Ningún otro faltante, contradicción, presupuesto, dependencia anterior o bloqueo
  de la productora se compensa por esa evidencia. El consumidor cumple además
  todas sus condiciones y dependencias; una arista satisfecha no basta para habilitarlo.
- RC7 conserva sus comprobaciones físicas/relacionales de cada entrada. Admitir
  la clase de cierre no suple bytes externos ausentes ni una recuperación defectuosa.
- Restricciones con procedencia y diagnósticos nativos completos se conservan.
  Toda restricción admitida se propaga hacia el consumidor y sus descendientes.
- RC10 no restaura testigos; física no prueba autenticidad; habilitación
  declarativa no concede permiso, ejecuta una operación ni valida ciencia.

## Interfaces implementadas

Módulo de acceso explícito:
[spica.artefactos.coordinacion_precondicion](../src/spica/artefactos/coordinacion_precondicion.py).
No se añaden reexportaciones a los inicializadores anteriores.

```python
inspeccionar_composicion_rc14(composicion, *, seleccion=None, cancelacion=None)
inspeccionar_integracion_rc14(solicitud, *, seleccion=None, cancelacion=None)
```

| Contrato RC14 | Contenido / regla |
|---|---|
| SeleccionPrecondicionRC14 | SolicitudPrecondicionProductora nativa RC13; perfil `rc14.precondicion_exportacion_json_qa0`, versión `0.1.0` |
| Perfil admitido | Exactamente el anterior y la política RC13 admitida; no código/callback cargado por configuración |
| InformeCoordinacionRC14 | Selección, cotejo RC13 nuevo, informe predeterminado, vista opcional, estados de dependencias, restricciones con origen y diagnósticos; versión `0.1.0` separada |
| decision_precondicion | Decisión RC13 conservada, o pendiente/no admisible si no se pudo cotejar; no afirma habilitación |
| arista_admitida_por_rc14 | Solo la arista seleccionada con cotejo RC13 satisfactorio, vínculos correctos y evaluación estructural apta en ese recorrido |
| habilitadas_declarativamente | Operaciones DECLARADAS/PLANIFICADAS que cumplen todas sus condiciones en la vista opcional; no permiso ni ejecución |

El nuevo informe conserva un testigo efímero de su comprobación: construir o
copiar un DTO no produce habilitación mediante sus propiedades. Su conversión
a bool está prohibida. Los informes no se aceptan como entrada para sustituir
una solicitud/evidencia: RC13 se vuelve a cotejar mediante su API nativa.

Productor fijo: `spica.calidad.exportacion.exportar_resultado_json`, `0.1.0`.
Consumidor fijo: `spica.calidad.consumo.consumir_exportaciones`, `0.1.0`.
Clase RC13: `rc8.exportacion_json_qa0`; finalidad `consumir_json_qa0_rc9`.
Confianza: `proceso_cooperativo_captura_local`. El vínculo RC11/RC13 identifica
proyecto/contexto completo, composición, productora y dependiente, referencias de
resultado, entrada canónica, artefacto/revisión e identidad de contenido; no solo
funciones, IDs aislados, formato compatible o SHA coincidente.

## Recorrido y alcance de la resolución

RC3 mantiene su único algoritmo y orden de precedencias en
[inspeccion.py](../src/spica/coordinacion/inspeccion.py). La interfaz anterior
invoca ese recorrido sin aporte y devuelve exactamente InformeComposicion. El
recorrido también registra estados de aristas para el nuevo informe RC14, sin
agregar campos al contrato antiguo. RC7 conserva sus bucles existentes y sus
comprobaciones sobre el linaje/recuperación.

El [aporte privado](../src/spica/coordinacion/_precondicion_rc14.py) se prepara
fuera del recorrido, solo si el examen RC13 actual es SATISFECHA y coincide con
el objetivo de inspección. Su testigo y snapshot están ligados a la composición,
arista, entrada, referencia y restricciones. No existe un flag público de admisión
general. Coordinación no importa RC8/RC11/RC13 ni llama recursivamente a ellos.

RC3 y RC7 usan **el mismo predicado** para esa arista. Permite compensar únicamente
el faltante propio `estado_declarado_no_es_cierre_completo` emitido por el inspector
para la productora INICIADA, cuyo cierre observado RC8 se ha cotejado. Se exige
además que el contexto productor no contenga diagnósticos propios desfavorables:
una causa aportada por el llamador no se oculta por compartir ese código reservado.
Toda otra causa desfavorable, referencia incorrecta o condición anterior mantiene
el bloqueo. El estado de la productora y su flag QA siguen intactos.

La dependencia satisfecha se registra en la vista opcional con información
explícita RC14 en vez del faltante de cierre específico resuelto. El informe
predeterminado conserva **todos** los diagnósticos anteriores, incluido ese
faltante. No se alteran registros históricos ni se filtran listas genéricas de
causas para fabricar aptitud. Los contadores QA permanecen iguales.

Las restricciones admitidas por RC13 se unen con procedencia a las del consumidor
y se propagan por los ancestros del recorrido RC3 a sus descendientes. Las
restricciones de cotejos rechazados también se conservan en el nuevo informe,
sin conceder habilitación. Se usa la unión nativa RC7 para conservar conflictos
y procedencias; las copias no son nuevas evidencias independientes.

RC7 comprueba que la recuperación corresponda al inventario original de la
política, no al portador RC10. Puede aportar todos los vínculos que requiere el
contrato RC7. Para ese caso la solicitud RC13 puede omitir su campo integracion:
RC14 vincula la solicitud RC7 inspeccionada al inventario/composición cotejados.
Si RC13 ya contiene una solicitud RC7, debe ser la misma, y se mantienen sus
reglas previas, incluido su perfil más estrecho de vínculos. No se modifica RC13.

RC7 reconoce la clase de cierre para la entrada exacta y vuelve a evaluar las
dependencias, sin ignorar ausencia/corrupción/indisponibilidad de contenidos,
perfiles, vínculos, restricciones, estados o límites. Una fuente QA externa sin
comprobación recuperada sigue impidiendo resolver la arista. Si falta únicamente
el contenido recuperado del consumidor, puede reconocerse la precondición
productora y, aun así, el consumidor queda sin habilitación por su propia entrada.

RC7 puede reducir las cotas de la misma composición; nunca ampliarlas para
reutilizar el aporte. Una cancelación observada impide habilitación. El cotejo
RC13 se omite si ya se canceló; su fase interna no incorpora un nuevo protocolo
de cancelación y no se promete interrupción forzosa ni plazo global.

## Fronteras de confianza e historia

| Dimensión | Tratamiento |
|---|---|
| Ejecución observada / RC8 | Exportación explícita previa y testigo local; no se despacha desde RC14 |
| RC9 | Consumo nativo real previo; valida entrada, no registra cierre de operación consumidora |
| RC10 | Historia preservada; no restaura testigos ni admisión actual |
| Física | RC5 actual solo si la política la exige; RC7 utiliza el snapshot RC6 fechado y no relee archivos por sí mismo |
| RC11 | Mantiene NO_ADMISIBLE bajo su contrato; no se reescribe para el nuevo perfil |
| RC13 | SATISFECHA es necesaria, no suficiente: no sustituye el resto del recorrido |
| RC14 | Dependencia estructural específica, con selección expresa; nuevo ámbito frente al predeterminado |
| Autenticidad / permiso / ciencia | No acreditados ni concedidos; física o habilitación no los sustituyen |

Los flags históricos RC13 de no habilitación siguen describiendo su contrato
externo. La nueva evaluación RC14 se expresa en su propio informe, sin reescribir
el anterior. La composición completa puede seguir PENDIENTE por el estado
INICIADA declarado de la productora y habilitar declarativamente al consumidor:
no se presenta como composición ejecutada ni concluida.

La confianza es cooperativa local; los testigos no son firmas ni resisten a
Python hostil. Si se exige autenticidad independiente no disponible, RC13 queda
pendiente y no se crea aporte. Decisiones/causas son deterministas ante iguales
hechos; una nueva lectura física tiene su propia fecha. No se promete validez
futura de una comprobación fechada, custodia o durabilidad operativa.

No se alteran RC6, RC10, JSON QA, 85-J/K o SQLite 85001. La evidencia nueva es
efímera, sin formato persistido ni tipos añadidos a codecs. Las cotas nativas no
son reserva RAM/disco o medición RSS. Los detalles de ejecución, límites y cierre
están en el [piloto](piloto_habilitacion_acotada_rc14.md) y la
[auditoría](auditoria_arquitectonica_rc14.md).
