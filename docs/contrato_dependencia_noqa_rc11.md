# RC11 — Dictamen externo de la dependencia de exportación

Elaborado el **2026-11-20**, America/Lima. Contrato experimental **0.1.0**.
Base: `98094c1`, rama `feature/suadc-http`. Este documento complementa el
[piloto](piloto_dependencia_tecnica_rc11.md) y la
[auditoría](auditoria_arquitectonica_rc11.md).

## Decisión de alcance anterior a la implementación

La [auditoría RC10](auditoria_arquitectonica_rc10.md) recomienda acordar la
confianza admisible y estudiar la arista exportar→consumidor. Se revisaron las
API reales: [RC3](../src/spica/coordinacion/inspeccion.py) exige determinados
cierres QA nativos y [RC7](../src/spica/artefactos/coordinacion.py) conserva esa
exigencia. Ninguna recibe un cierre RC8 como clase de cierre admitida. Tampoco
una RecuperacionEvidencias RC10 es la RecuperacionGeneracion de un inventario
original que requiere SolicitudIntegracion RC7: el portador RC10 es otro objeto.

Se aplica la alternativa expresamente prevista en el encargo: **dictamen externo
específico, de solo lectura**. Se detiene la habilitación de esa dependencia.
No se extienden RC3/RC7, sus estados, formatos ni reglas de cierre. El dictamen
puede comprobar correspondencias técnicas y conservar un bloqueo correcto; no
puede emitir SATISFECHA bajo los contratos vigentes. Esto es una limitación
contractual explícita y comprobada, no una dependencia satisfecha encubierta.

## Una sola dependencia y una finalidad

| Elemento | Identidad y alcance |
|---|---|
| Productor existente | `spica.calidad.exportacion.exportar_resultado_json`, 0.1.0 |
| Consumidor existente | `spica.calidad.consumo.consumir_exportaciones`, 0.1.0 |
| Finalidad | `consumir_json_qa0_rc9`: consumo técnico del JSON QA Nivel 0 nativo |
| Operación productora | ContextoOperacion RC1 DESCRIPCION_ESTRUCTURAL identificado en una composición RC3 |
| Operación dependiente | Otro ContextoOperacion DESCRIPCION_ESTRUCTURAL, con la salida como entrada canónica y finalidad declarada |
| Arista | DependenciaOperacion presente exactamente una vez, con la referencia de entrada de salida exigida explícitamente |
| Entrada del productor | VinculoResultadoQA RC1, conservando ResultadoQA y contexto de exportación nativos |
| Salida | ReferenciaArtefacto RC4, object_id/revisión, contenido_id y perfil JSON nativo |

En el piloto las operaciones se llaman `exportar` y `consumidor`, y la composición
`composicion-RC8`. Son identificadores sintéticos locales. El consumidor se
declara con su finalidad antes de ejecutar RC8. La llamada RC9 efectivamente
consume el JSON, pero no acredita un cierre de esa operación RC3: RC9 no
captura una operación dependiente con identidad/cierre admitidos por RC3.
No se deduce una ejecución RC3 de una simple llamada a función.

## API mínima, sin nuevos formatos persistentes

Importación experimental explícita desde
[dependencia_exportacion.py](../src/spica/artefactos/dependencia_exportacion.py).
No se modifican los `__init__.py` públicos.

| Contrato | Contenido |
|---|---|
| PoliticaDependenciaExportacion | Inventario esperado RC4, composición, arista RC3, artefacto/revisión, entrada lógica de resultado QA, contenido_id, productor/consumidor y versiones, finalidad, exigencias físicas/de autenticidad/de externos y restricciones adicionales |
| SolicitudDependenciaExportacion | Política más evidencia RC8/admisión RC9 locales, o raíz TEMP y ControlEvidencias RC10; fuentes mutuamente excluyentes |
| DictamenDependenciaExportacion | Solicitud, InformeLinaje completo con RC3, cierre RC8, informe RC9, recuperación RC10 cuando se realizó, verificación física actual separada, restricciones con orígenes y diagnósticos propios |

`dictaminar_dependencia_exportacion(solicitud)` no despacha productor, consumidor
dependiente, QA, planes ni red. Reutiliza el inspector RC8, que a su vez hace
contrastes puros con el consumidor/codificación nativos. No se duplica el parser.
El informe RC9 local ya ejecutado debe conservar su comprobación cooperativa.

Los objetos son dataclasses congeladas. El inventario esperado debe proceder
del contexto que se pretende contrastar; copiar identidades de una fuente no
confiable y compararlas consigo mismas no autentica esa fuente. El código
verifica tipos, versión propia y exigencias booleanas; las incoherencias de
configuración producen TypeError/ValueError con códigos fijos.

Las dos fuentes posibles son:

- **Local:** RC8 se inspecciona de nuevo; RC9 conserva su informe nativo y su
  testigo privado coherente. Una copia sin testigo no constituye captura local.
- **Histórica:** se invoca `recuperar_evidencias` RC10 con raíz/control para
  comprobar físicamente la generación TEMP actual. Se conservan los hechos y
  resultados históricos; no se restauran testigos ni admisión local RC9. No se
  acepta un DTO de recuperación positivo aportado como sustituto de la lectura.

La política de tipos, rutas y presupuestos históricos sigue en RC10/RC6; no se
crea otro codec, almacenamiento, tabla, localizador o algoritmo de hash.

## Estados, prioridades y barrera de admisión

Se reutiliza EstadoAptitud para `estado_correspondencia`. Este estado describe
el cotejo específico RC11 y **no sustituye el estado global RC3/RC4**. Un nuevo
enum de decisión expresa otra dimensión: incluye la inadmisibilidad por clase de
evidencia, que no tiene un equivalente exacto en EstadoAptitud.

| Decisión | Condición y comportamiento |
|---|---|
| NO_SATISFECHA | Contradicción comprobada, asociación ajena, bytes/hash contradictorios, ejecución observada no completada, bloqueo aplicable o linaje contradictorio; prevalece sobre faltantes |
| PENDIENTE | Sin contradicción, pero falta evidencia, captura local, comprobación, finalidad declarada, disponibilidad exigida o autenticidad independiente |
| NO_ADMISIBLE | Correspondencias sin contradicciones/faltantes en este alcance; la clase de cierre no QA carece de admisión RC3/RC7. También se identifica un perfil de política fuera del único perfil reconocido |
| SATISFECHA | Solo sería legítima con admisión contractual expresa y todas las condiciones comprobadas. **Ninguna ruta de RC11 0.1.0 devuelve este valor** |

La decisión se calcula; el llamador no aporta un estado positivo. Incluso
construir/copiar un Dictamen con diagnósticos vacíos devuelve NO_ADMISIBLE.
`satisfecha`, `habilitacion_rc3_rc7`, `autoriza_operacion`, `ejecucion_automatica`,
`autenticidad_acreditada` y `validacion_cientifica` no se convierten en True.
`bool(dictamen)` produce TypeError. El enum no promete una funcionalidad de
habilitación futura implementada.

Los informes nativos permanecen íntegros. Para separar correspondencias RC11 de
límites nativos ya conocidos, estos códigos no se proyectan como faltantes propios:

```text
estado_declarado_no_es_cierre_completo
conclusion_declarada_sin_cierre_tecnico_admitido
dependencia_sin_cierre_tecnico_compatible_aportado
composicion_con_condiciones_no_satisfechas
sin_comprobacion_fisica_aportada
relacion_sin_evidencia_ejecucion_suficiente
productora_sin_conclusion_declarada
antecesor_pendiente_de_evidencia
```

No se borran de InformeLinaje ni de sus composiciones/artefactos. Su exclusión
de esta proyección únicamente evita confundir la falta de cierre RC3 o física
global con una identidad contradictoria. Las causas particulares restantes
siguen prevaleciendo y la decisión nunca pasa a SATISFECHA. Si cambia la
semántica de esos códigos, habrá que revisar/versionar esta proyección.

## Restricciones y condiciones físicas

Se reutilizan RestriccionQA, RestriccionPropagada y la unión RC7. Se propagan las
restricciones de proyecto/entradas/operaciones, compatibilidad RC2 cuando está
declarada, linaje RC4, resultado QA, cierre RC8, admisión RC9 y expediente RC10.
Las adicionales de política solo restringen. No se omiten diagnósticos adversos
de las fuentes, conservadas en sus informes originales.

`restricciones_heredadas`, `restricciones_nuevas` y `restricciones_bloqueantes`
son vistas de la misma unión con orígenes. Una restricción repetida entre fuentes
no constituye otra evidencia ni suma garantías. Un código redefinido conserva
ambas variantes y provoca contradicción; códigos repetidos dentro de una fuente
de política son rechazados por el validador RC1 existente.

Un bloqueo para el uso de exportación o consumo impide el dictamen favorable de
correspondencias. Restricciones científicas de otros usos permanecen visibles
como no aplicables **a esta finalidad técnica**, sin levantarse. Si los usos del
nodo son desconocidos, queda pendiente su aplicabilidad. No se crea una nueva
taxonomía de restricciones ni permisos.

La física es opcional para contenido local en memoria. Si RC9 ya la exigía, RC11
no puede rebajar esa exigencia. Con precondiciones coherentes, reutiliza `_fisica`
RC9: contrasta asociaciones, conserva el estado de materialización y llama a
`verificar_fisicamente` RC5 para una relectura actual. El veredicto histórico RC9
no se reutiliza como resultado actual. Archivos alterados se rechazan; ausencia
comprobada no se confunde con comprobación no disponible.

El hash físico del portador RC10 solo acredita los bytes de ese expediente
durante la lectura. No comprueba la disponibilidad actual de un archivo JSON
independiente ni la del CSV/entrada externa. Si se exigen esos hechos y faltan,
la decisión queda pendiente. Nunca se siguen localizadores RC5 históricos.

## Confianza y compatibilidad

La captura RC8 y comprobación RC9 son cooperativas en un proceso confiable;
no constituyen autenticación independiente. Exigir esta última deja pendiente
la evaluación: no hay firmas ni una autoridad verificadora implementadas.

La consulta RC11 puede releer TEMP mediante RC5/RC10, sin escribir ni reparar.
Las funciones de conservación/materialización son llamadas explícitas del
piloto, no efectos del dictamen. Se preservan publicación exclusiva, uso
secuencial y limpieza propia existentes; no se amplían garantías de concurrencia,
durabilidad ante apagados, custodia independiente, DACL Windows o respaldo.

Permanecen intactos JSON QA 0.1.0, SQLite 85001, formatos 85-J/K,
`rc6.generacion.0.1.0` y `rc10.evidencias.0.1.0`. No hay puentes operativos,
RAW/staging, científicos, institucionales, GIS o de IA nuevos. La arquitectura
integral sigue abierta. Cualquier admisión efectiva posterior necesita revisión
de confianza e interfaces y un incremento separado autorizado.
