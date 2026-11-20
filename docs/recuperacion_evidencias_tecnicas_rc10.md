# RC10 — Recuperación experimental de evidencias técnicas

Fecha: 2026-11-20, America/Lima.
[Contrato](contrato_conservacion_evidencias_rc10.md),
[auditoría y resultados finales](auditoria_arquitectonica_rc10.md),
[pruebas](../tests/test_conservacion_evidencias_rc10.py).

## Piloto que ejecutan las pruebas

El piloto usa los fabricantes sintéticos existentes RC1/RC2/RC8/RC9,
importando funciones y nunca sus TestCase. La fuente QA es un registro inventado,
realmente evaluado por el evaluador puntual existente. No se fabrica InformeQA
de lote ni CierreQA para la exportación.

Dos proyectos independientes, `proyecto-RC10-A` y `proyecto-RC10-B`, comparten
intencionalmente el contexto nominal `contexto-RC10` en inventarios separados.
Los object_id de sus artefactos incluyen el project_id. Eso no resuelve unicidad
global de espacios nominales ni permite intercambiar sus contextos por hash.

| Fase | Componente realmente usado |
|---|---|
| Entrada QA | Registro ficticio de las fixtures RC1, resultado de evaluar_registro existente |
| Exportación | ejecutar_exportacion_tecnica RC8 invoca el exportador JSON fijo |
| Cierre específico | inspeccionar_cierre_exportacion y sus informes completos RC3/RC4/consumo |
| Consumo/admisión | admitir_exportacion_tecnica RC9 con el consumidor nativo |
| Captura | capturar_evidencias con los objetos reales y fecha UTC prospectiva |
| Portador documental | Descriptor RC4 independiente, proyecto correcto, contenido_id=evidencia_id, revisión r1, todas las restricciones conocidas |
| Física del expediente | materializar_sintetico RC5, bloques de 65536, relectura y SHA reales |
| Generación | ConservadorExperimental RC6, copias independientes y manifiesto/cierre nativos |
| Recuperación | recuperar_evidencias, lector RC6 y perfil RC10 cerrado |
| Traslado | ConservadorExperimental.copiar_de, sin un copiador nuevo |

La variante física adicional materializa **los bytes JSON realmente producidos**
mediante RC5 y solicita a RC9 una segunda lectura real. Conserva esa referencia y
ambos informes como historia. Sale del contexto RC5 y retira su raíz antes de
reconstruir el expediente. Durante la reconstrucción se bloquea el verificador
físico RC9: la prueba exige que no intente resolver la referencia histórica.
Esa variante no se atribuye retroactivamente a todos los proyectos del piloto.

## Procesos terminados y traslado

`test_productor_terminado_lector_independiente_dos_proyectos_y_otra_raiz` ejecuta
un **proceso Python A independiente** con el intérprete `.venv -B`. A produce,
admite y conserva una generación por proyecto, emite controles e identidades de
sus archivos propios y termina. El padre espera su salida correcta antes de
iniciar cualquier lector; no conserva objetos RC8/RC9 de A en memoria.

Python B inicia después. Instala una barrera de auditoría antes de importar
SPICA: niega sockets, SQLite, lecturas operativas, escrituras y mutaciones.
No importa fabricantes de pruebas. Recibe solo raíz TEMP y control esperado,
recupera los contratos mediante el lector real y contrasta identidades, estados,
restricciones, contenido y garantías. Una barrera adicional niega el despacho
del exportador RC8 y la apertura de referencias físicas históricas desde RC9.

El padre copia cada generación a una raíz TEMP exclusiva con `copiar_de` RC6,
dispone la fuente propia y vuelve a iniciar un lector B sobre el destino. Exige
igualdad de sus resultados con los de B antes del traslado. La raíz de origen
ya no existe en ese segundo ensayo. El generacion_id/control son los mismos;
la ubicación física cambia. Las referencias RC5 de la generación son historia
y no se usan como localizadores actuales.

La disposición de la fuente usa nombres/dev/ino emitidos por el hijo propio y
`ArchivosGeneracion.limpiar`, sin recursión. Un archivo ajeno, sustitución o
enlace impide limpiarla. El destino lo dispone su contexto RC6 propietario.
Los procesos heredan la misma cuenta/equipo/TEMP; no son custodia independiente
ni prueba entre sistemas operativos o dominios de fallo.

Comprobación adicional realmente ejecutada por stdin, solo en memoria, después
de las dirigidas y sin modificar código:

| Propiedad de la variante A | Valor observado |
|---|---|
| evidencia_id | evidencia-RC10 |
| Proyecto / contexto | proyecto-RC10-A / contexto-RC10 |
| Fecha UTC de captura del expediente | 2026-11-20T05:11:20.834510+00:00 |
| Operación exportadora / entrada lógica | exportar / resultado-qa-fuente |
| Artefacto JSON / revisión | objeto-salida-exportacion-proyecto-RC10-A / r1 |
| Tamaño de la salida UTF-8 | 3853 bytes |
| SHA-256 de esos bytes en memoria | a4d5c2dfc342af3a5b3bc48a0be2eb12ed16531391db5095aec3e512dc0ca41b |
| Tamaño del expediente serializado | 84812 bytes |
| Estados históricos RC8 / RC9 | APTO_ESTRUCTURALMENTE / APTO_ESTRUCTURALMENTE |
| Testigos locales tras reconstrucción | False / False |
| Restricciones conocidas | alcance_estructural, sin_validacion_cientifica, sin_equivalencia_editorial |

El tamaño/hash de la tabla corresponden a esa variante contextual, no a los
3852 bytes del piloto RC8 original ni a un archivo institucional. Su hash de
JSON **no es** el hash físico del expediente completo. La fecha de captura es
real, pero no se renombra como instante de ejecución del exportador.

## Interpretación de los resultados

| Evidencia recuperada | Qué se puede afirmar |
|---|---|
| Hechos históricos RC8 positivos | El expediente conserva que la captura cooperativa había comprobado esa exportación; no se observa una invocación nueva |
| Hechos históricos RC9 positivos | El expediente conserva que se admitió ese consumo con sus límites y política entonces |
| Testigos privados reconstruidos | Permanecen ausentes. Las propiedades locales de cierre/admisión de los DTO reconstruidos no se vuelven positivas |
| Integridad física RC6 actual | Tamaño/SHA reales del archivo portador leído en esta recuperación, dentro de su fecha y alcance |
| JSON incorporado | Se conserva literal dentro del expediente, se coteja con su captura histórica y se comprueba por el consumidor nativo en memoria |
| consumo_actual | Informe actual del contenido incorporado; no demuestra nuevamente la ejecución exportadora ni aprueba dependencias |
| Referencias externas | NO_DISPONIBLE: no se abren ni se afirma ausencia física |
| Informes físicos RC5 históricos | Se conservan fechas, tamaños, hashes y asociaciones; no se usan para afirmar disponibilidad actual de esas ubicaciones |

El SHA físico actual corresponde al **portador RC10 completo**. El SHA de la
salida JSON se conserva y contrasta sobre el texto incorporado; no se presenta
como una relectura actual de un archivo JSON separado. No se extrae/publica
automáticamente ese JSON en otra ubicación.

La generación puede ser íntegra y contener evidencia histórica negativa.
PARCIAL conserva la salida obtenida sin promover su cierre; FALLIDA/CANCELADA
mantienen su causa; un bloqueo se mantiene; una admisión incompatible sigue
incompatible. Ningún hash soluciona los faltantes de ejecución o de confianza.

## Casos adversariales

Las pruebas ejercitan conservación y recuperación completas, referencias
compartidas, versiones desconocidas y rechazo por lectores antiguos; JSON con
claves repetidas, no finitos, exceso de profundidad/tamaño, clase/campo no
admitido y tipos incorrectos; ausencia de RC8/RC9, captura copiada insuficiente,
admisión rechazada y sustitución de contenido; proyecto/operación/productor/
consumidor/entrada/artefacto/revisión/contenido contradictorios; diagnósticos,
restricciones o estados adulterados.

También cubren bloqueo de exportación y de consumo, restricciones científicas
heredadas, parcial observado después del retorno, fallo/interrupción reales del
productor, terminales declarados, materialización histórica y física requerida
sin referencia; generación sin sello, archivo ausente, corrupción con igual
tamaño, control SHA incorrecto, control de otro proyecto/evidencia/revisión,
rutas inseguras, publicación repetida sin sobrescritura y cancelación física.

La prueba de pureza niega sockets, SQLite, despacho del productor y evaluación
QA nueva durante la recuperación. La prueba entre procesos añade la barrera de
no escritura y de acceso operativo. Es un ensayo cooperativo, no una caja de
aislamiento contra código hostil. Los validadores nativos pueden contrastar
codificación; eso no es una ejecución de operación productora registrada.

Los resultados cuantitativos finales, tiempos y comandos están en la
[auditoría RC10](auditoria_arquitectonica_rc10.md). No se suman subtests,
proyectos, lectores o repeticiones dirigidas al total de tests únicos.

## Límites y continuidad

Perfil pequeño, cerrado y experimental; no JSON de tamaño arbitrario, lotes QA
con cierres nativos completos o persistencia operativa. No se preserva un
testigo Python después de reiniciar; se preservan contratos y hechos como datos
históricos contrastables. No hay firma, identidad autenticada del proceso,
aprobación científica o nueva autorización.

Un informe con variantes de restricciones que el portador RC4/RC6 no pueda
representar coherentemente se rechaza antes de conservar; no se aplana ni se
afirma recuperación universal. La extensión de perfiles necesita otra revisión.

No hay transacción global, reserva de espacio/RSS/CPU, garantía de pérdida
eléctrica, fsync portable del directorio, recuperación de escritura interrumpida
ni respaldo independiente. Un marcador o temporal impide declarar cierre;
no se repara borrando ni se reintenta una raíz incierta.

No se toca RAW/staging/SQLite operativo ni CSV PNDA. No se emite un dictamen
nuevo sobre la integridad actual de originales que deliberadamente no se abren.
RC3/RC7 no reciben una política nueva de admisión: la dependencia exportar →
consumidor continúa pendiente. No se inicia el siguiente incremento ni ciencia.
