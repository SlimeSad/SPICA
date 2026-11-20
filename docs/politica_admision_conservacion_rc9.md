# RC9 — Política de admisión y requisitos de conservación

Propuesta experimental 0.1.0, 2026-11-19, America/Lima.
Se aplica exclusivamente al consumidor JSON QA nativo descrito en el
[contrato RC9](contrato_consumo_evidencia_rc9.md). No es una política general
de aceptación de datos científicos ni de permisos.

## Decisiones de admisión

| Situación comprobada | Decisión |
|---|---|
| JSON dentro del perfil nativo; captura RC8 local coherente; productor realmente invocado y observado CONCLUIDA; identidades y bytes esperados; sin bloqueo del uso | APTO_ESTRUCTURALMENTE, admisible en memoria |
| Caso anterior más relectura RC5 actual requerida, con archivo íntegro y vínculo correcto | Admisible incluyendo esa comprobación física puntual |
| JSON inválido, raíz/esquema/versiones incompatibles o restricciones internas adulteradas | INCOMPATIBLE |
| Proyecto/contexto, operación, entrada, resultado, artefacto/revisión o contenido contradictorios | INCOMPATIBLE |
| Bytes diferentes de la salida capturada, aunque el JSON siga siendo válido | INCOMPATIBLE |
| Hash/tamaño capturados contradictorios o corrupción física actual | INCOMPATIBLE |
| Restricción bloqueante para `consumir_json_qa0_rc9` o variantes contradictorias | INCOMPATIBLE, conservando restricciones |
| Finalidad o consumidor fuera del perfil específico | INCOMPATIBLE |
| JSON coherente sin captura RC8 o captura construida/copiada por el llamador | PENDIENTE_DE_EVIDENCIA |
| Contenido ausente, presupuesto insuficiente o cierre RC8 no demostrado | PENDIENTE_DE_EVIDENCIA, salvo contradicción ya demostrada |
| Productor parcial/cancelado sin contradicciones adicionales | PENDIENTE_DE_EVIDENCIA; no se promueve a CONCLUIDA |
| Productor fallido | Nunca admisible; conserva su diagnóstico nativo. Una contradicción RC8 comprobada puede determinar INCOMPATIBLE |
| Integridad física requerida sin referencia, archivo ausente, lectura no disponible o materialización histórica sin cierre | PENDIENTE_DE_EVIDENCIA |
| RC6 recupera bytes, pero no se aporta la captura RC8 todavía disponible localmente | PENDIENTE_DE_EVIDENCIA |

La precedencia es contradicción > evidencia faltante > comprobación apta. Un
JSON rechazado sigue rechazado aunque también falte RC8. La ausencia de una
propiedad no se rellena para conseguir un resultado positivo. Las instancias
mal tipadas de la propia API son errores del llamador, no JSON reparables.

La misma huella SHA no fusiona proyectos, revisiones, entradas ni autorizaciones.
Un proyecto distinto puede tener los mismos bytes; debe contrastarse su propio
contexto completo y sus referencias. La unicidad global de los espacios nominales
requiere una coordinación futura y no se declara resuelta.

## Restricciones y niveles de evidencia

Se preservan las restricciones del proyecto esperado, del vínculo QA nativo,
de la operación exportadora, del linaje RC4 y de los antecesores propagados que
RC8 obtiene mediante los inspectores existentes. La unión RC7 conserva ambas
variantes ante conflictos; no elige silenciosamente la más permisiva.

Las restricciones internas del paquete JSON se validan mediante la política
85-B existente en el consumidor. Las restricciones RC1/RC4/RC8 adicionales se
conservan en el informe y su contexto; no se añaden a un esquema histórico
cerrado. Con evidencia insuficiente no se declara exhaustividad del linaje.

La inspección acotada puede producir un informe nativo de coherencia antes de
que la política de uso rechace la admisión. No equivale a publicar, distribuir,
autorizar otra operación o retirar un bloqueo. Incluso con admisión positiva
permanecen las prohibiciones de acreditar aptitud científica o equivalencia
editorial y las demás restricciones aplicables.

| Dimensión | Qué permite afirmar RC9 |
|---|---|
| Resultado realmente producido | Solo con captura RC8 coherente obtenida en el proceso cooperativo |
| Evidencia aportada | Se contrasta; una dataclass coherente no es observación independiente |
| Histórico RC5 | Describe lo observado entonces; no asegura disponibilidad ahora |
| Integridad actual | Solo tras la relectura RC5 solicitada y dentro de su fecha/alcance |
| Consumo estructural | Perfil JSON nativo satisfecho, identidades esperadas y política técnica cumplidas |
| Cierre QA | Ninguno nuevo; solo conserva un cierre QA nativo genuino cuando existe |
| Cierre técnico RC8 | Específico del exportador, separado de QA |
| Habilitación RC3/RC7 | Ninguna nueva |
| Autenticidad/revisión científica/permisos | No acreditados ni concedidos |

## Dependencia concreta pendiente en RC3/RC7

El piloto tiene `exportar → consumidor`, con la salida JSON como entrada
declarada. RC8 observa la exportación y RC9 admite su consumo específico,
pero RC3 solo reconoce el cierre QA previsto en su contrato. Declarar la
operación exportadora CONCLUIDA no satisface esa dependencia. RC7 tampoco
convierte integridad física, recuperación o admisión en cierre QA.

Necesidad real futura: permitir que una dependencia no QA exija un **tipo de
cierre técnico explícito** de un productor concreto, sin usar `CierreQA`.
La evidencia existente incluye invocación RC8 local, salida, estado observado,
identidades, restricciones, consumo RC9 y, opcionalmente, relectura RC5.
Faltan un contrato público de admisión de cierres por RC3, persistencia de la
evidencia necesaria y una política aprobada de confianza/actualidad/uso.

Evolución compatible propuesta, no implementada:

1. Diseñar un contrato separado y versionado de cierre técnico no QA, con
   productor y versiones permitidos, identidad de ejecución no inferida,
   operación/entrada/salida/revisión, contenido, estado completo y alcance.
2. Definir un requisito explícito por arista/nodo que distinga cierre QA de
   cierre técnico permitido y no equipare uno con otro.
3. Admitir ese cierre solo mediante inspección específica, sin ejecutar productores
   ni dar permisos; conservar la precedencia de restricciones y faltantes.
4. Versionar la ampliación pública de NodoOperacion/DependenciaOperacion y los
   informes de inspección RC3 si la decisión aprobada requiere esos campos.
   RC7 necesitaría un adaptador explícito a ese requisito, no una habilitación global.
5. Mantener el comportamiento histórico por defecto y rechazar cierres nuevos
   en lectores antiguos. Revisar antes los ciclos de importación y presupuestos.

Las interfaces exactas y el número de versión requieren revisión; estas notas
no son un diseño aprobado. En RC9 no cambia ninguno de esos contratos, campos,
criterios de cierre, nodos ni aristas. No se implementa RC10.

## Análisis de conservación A–F

| Grupo | Información | Reconstrucción y límites |
|---|---|---|
| A. Desde bytes | Longitud, SHA-256 de esos bytes, sintaxis, esquema/versión, identidades y restricciones internas JSON | Se pueden recalcular con el consumidor compatible. No recuperan identidad MD externa, ejecución del exportador, permisos ni autenticidad |
| B. Requiere datos de ejecución | Productor y versión realmente invocados, estado observado, entrada nativa asociada, salida capturada, causas de fallo/cancelación y límites aplicados | Deben conservarse como observaciones con procedencia, no reconstruirse porque el JSON sea válido |
| C. Contexto referenciado | Proyecto/configuración, operación, entrada/resultado lógico, artefacto/revisión, contenido, linaje, restricciones propagadas y generación RC6 | Referencias solo son suficientes si el contexto exacto versionado sigue disponible e íntegro. Ni nombres ni SHA sustituyen identidades |
| D. Se pierde sin almacenamiento explícito | Comprobación RC9 y finalidad, consumidor/versión/límites, diagnósticos exactos, restricciones contextuales externas al JSON, vínculo de la captura con el resultado de admisión | RC6 vigente no conserva estos objetos. La marca local de Python no sobrevive ni debe serializarse como prueba de ejecución |
| E. Autenticidad no acreditada | Procedencia declarada, institución, supuesta revisión documental, observaciones locales y hashes históricos | Persistirlos no los autentica. Se necesita una política de confianza y, si se exige, evidencia externa aprobada |
| F. Histórico frente a actual | Fecha/alcance de lectura RC5, recuperación RC6 y decisión RC9 | Un registro histórico conserva lo observado; una comprobación posterior requiere volver a leer y evaluar lo que corresponda, sin sustituir ni reescribir la anterior |

El JSON permite reconstruir la coherencia de datos recibidos y sus declaraciones;
no permite demostrar retrospectivamente que una función se invocó. RC8 no
registra un instante UTC de ejecución del productor ni una identidad autenticada
de proceso: no se inventan para completar un expediente. La fecha RC5 no se
reutiliza como fecha de exportación. La comprobación RC9 en memoria no posee
un reloj propio de ejecución. Si son necesarios, esos campos requerirán una
captura prospectiva y un contrato aprobado, no una fecha retrospectiva estimada.

## Perfil mínimo futuro, únicamente propuesto

Propuesta de un perfil separado y explícitamente versionado de **observaciones
de exportación y admisión**, sin asignarle un número operativo ni alterar el
formato `rc6.generacion.0.1.0` vigente. Datos mínimos a revisar:

| Grupo | Campos candidatos |
|---|---|
| Identificación del perfil | Versión de perfil, identificador de observación, tipo RC8/RC9 y vínculo entre ambas |
| Versiones y alcance | Productor, consumidor, formato, contratos, finalidad y presupuestos efectivos |
| Contexto inmutable | Proyecto/contexto/configuración, operación, entrada, resultado, artefacto/revisión, contenido y referencia/hash del contexto exacto |
| Bytes | Referencia controlada, tamaño y SHA-256 comprobados; no usar la huella como identidad lógica |
| Observación | Estado técnico, invocación observada, resultado/causa y método de captura; fecha solo cuando se haya observado realmente |
| Políticas | Restricciones completas, orígenes, variantes conflictivas y diagnósticos nativos |
| Física | Referencia y fecha/alcance de verificación, comprobaciones realizadas/no realizadas y estado histórico |
| Confianza | Evidencia declarada u observada, autenticidad no acreditada, permisos no concedidos y límites de revalidación |
| Conservación | Generación y control de integridad del expediente; referencias externas explícitas y disponibilidad separada |

No conservar objetos Python ejecutables, testigos privados, rutas operativas
de origen como localizadores automáticos, credenciales ni mensajes arbitrarios
de excepción. Un perfil futuro debe ser acotado, de datos conocidos, cerrado por
versión, verificable y con lectores que no ejecuten código recibido. El control
de integridad no basta para acreditar autenticidad o custodia independiente.

Debe definirse antes: identidad y privacidad del contexto, evidencia histórica
admisible tras reinicio, política de firmas si procede, captura temporal real,
retención, copia/restauración y confianza del consumidor. Un lector posterior
no puede recrear el testigo local RC8/RC9 a partir de metadatos y llamar a eso
ejecución observada; necesita una política distinta de admisión histórica aprobada.

Esta propuesta no crea almacén, base de datos, serializador, manifiesto,
migración ni nuevos tipos en el codec RC6. Tampoco modifica 85-J, 85-K,
SQLite 85001 o JSON QA 0.1.0. Su eventual relación con RC6 debe revisarse
expresamente y conservar la compatibilidad con los lectores anteriores.

## Decisiones pendientes

Revisar el perfil de conservación, los requisitos concretos de dependencia no QA,
la confianza tras reinicio y la privacidad de los contextos. La arquitectura
integral sigue abierta. M03, M16, M26, M32 y las brechas PNDA mantienen el
estado que registra la [auditoría RC9](auditoria_arquitectonica_rc9.md).
