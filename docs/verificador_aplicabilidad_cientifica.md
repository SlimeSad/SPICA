# PASO 76: verificador documental de aplicabilidad científica

Estado: **experimental, APTO CON RESTRICCIONES**. No ejecuta reglas ni concede
autorizaciones. La compatibilidad documental no es aprobación científica,
validación de observaciones ni habilitación operativa.

## Auditoría previa y decisión de arquitectura

Git inicial limpio, rama `feature/suadc-http`, HEAD `e9f9b32`, PASO 75 registrado.
Se revisaron los contratos y catálogo del PASO 73, el expediente y JSON del 74,
las fichas TEMP/HR y la separación experimental del 75. No se abrieron datos
operativos. No se modifican esos componentes ni sus interfaces.

`ReferenciaCientifica` ya contiene identidad, procedencia/emisor, título,
localizador, versión, fecha civil y SHA-256 opcional. `CondicionAplicabilidad`
ya representa dimensiones, valores literales y referencias de una regla.
Se reutilizan ambos tipos y `ReglaCientifica`; no se crea otro catálogo ni
otra representación de aprobación. Se conserva `DimensionAplicabilidad` intacta.

La adquisición ya representa `ProductoCatalogo`, `VariableCatalogo` (código,
unidad, tipo de medición y frecuencia declarados), `EstacionCatalogo` (identidad,
tipo, coordenadas y referencia espacial), `DisponibilidadCatalogo` (cobertura y
zona horaria opcionales) y `ProcedenciaCatalogo`. El expediente reutiliza una
instantánea `ProductoCatalogo` con su fuente/identificador originales.
Esos metadatos no se elevan automáticamente de declarados a verificados.
No hay un adaptador que consulte SQLite o importe observaciones para completarlos.

Existe también `adquisicion.catalogo.evidencias.EvidenciaDocumental`, usada para
publicación, licencia, recurso, revisiones y capacidades de adquisición. No contiene
identidad/versión/fecha de una referencia científica, nivel inferido/contradictorio
ni condiciones de aplicabilidad. La nueva clase homónima pertenece exclusivamente
a `calidad.aplicabilidad`, compone `ReferenciaCientifica` y no sustituye ni convierte
la evidencia de adquisición. Se mantienen nombres calificados al combinar ambos
dominios; no se añade otra estructura de licencias, recursos o capacidades HTTP.

Los tipos anteriores no distinguen información inferida, desconocida o
contradictoria, agregación temporal, continuidad de serie ni condiciones de
activación. El paquete nuevo `spica.calidad.aplicabilidad` complementa esas
carencias sin modificar el contrato anterior. Las dimensiones adicionales son
solo las ausentes: agregación, identidad de estación, continuidad, cobertura de
aplicación, vigencia de aplicación, restricción institucional, parámetros,
incertidumbre y zona horaria.

**No se integra la salida con `HabilitacionCientifica`, `ResultadoCientifico`,
`RevisionCientifica` ni el evaluador del PASO 75.** Esos contratos no representan
este diagnóstico ni aportan una autorización independiente. Su conversión sería
una integración peligrosa y queda expresamente fuera del paso.

## Contratos

Todos son dataclasses congeladas, con tuplas tipadas/acotadas y sin callbacks.

| Contrato | Contenido y finalidad |
| --- | --- |
| `EvidenciaDocumental` | Referencia científica existente, sección/página, naturaleza, nivel, vigencia, incertidumbres, contradicciones y pendientes |
| `AfirmacionAplicabilidad` | Dimensión, valor literal opcional, nivel, referencias y salvedades sobre un producto |
| `CondicionAdicional` | Condición de valores exactos para una dimensión nueva; las anteriores siguen usando `CondicionAplicabilidad` |
| `RequisitoAplicabilidad` | ID único, condición, tipo obligatorio/condicional y, solo para el segundo, condición declarativa de activación |
| `EspecificacionAplicabilidad` | Descriptor `ReglaCientifica`, requisitos y evidencia documental de sus referencias |
| `ExpedienteProducto` | `ProductoCatalogo`, documentos y afirmaciones; no contiene observaciones |
| `HallazgoAplicabilidad` | Requisito/dimensión, estado, motivos y referencias involucradas |
| `DiagnosticoAplicabilidad` | Estado global, hallazgos, motivos, restricciones, versión del verificador y las dos entradas completas |

`NivelEvidencia`: VERIFICADA, DECLARADA, INFERIDA, DESCONOCIDA, CONTRADICTORIA.
`NaturalezaEvidencia`: DOCUMENTAL o SINTETICA; no se mezclan en un diagnóstico.
`VigenciaDocumento`: VIGENTE, DESCONOCIDA u OBSOLETO, según evidencia aportada.
Una afirmación desconocida conserva `None`. La verificada necesita referencias;
una contradicción clasificada como tal necesita explicación.

Verificar que el manual contiene una afirmación no demuestra que esta describa
un producto particular. Son dos evidencias distintas. Tampoco un SHA-256 local
prueba autoría, vigencia, firma institucional ni aplicabilidad. El hash se conserva
en la referencia y no provoca ninguna elevación del nivel de evidencia.

## Comparación y diagnóstico

API única y pura:

```python
diagnostico = verificar_aplicabilidad(especificacion, expediente)
# Consultar diagnostico.estado, hallazgos, motivos y restricciones.
# Nunca usarlo como permiso: bool(diagnostico) produce TypeError.
```

No hay lectura de archivos, consultas de catálogo, reloj implícito, red, importación
dinámica de métodos, evaluación numérica ni escritura. Una cadena que parezca
código sigue siendo texto literal. No se admiten rutas, lectores, diccionarios,
revisiones del catálogo o habilitaciones en lugar de los contratos exactos.

Se comprueban identidad de variable/producto, unidad, modalidad, frecuencia y
las demás dimensiones que la especificación declare pertinentes. La agregación
se representa separadamente. No se normalizan identificadores, unidades ni
frecuencias; no se equipara promedio con instantánea. No se infiere que la cadencia
declarada acredite continuidad o identidad instrumental.

Todas las condiciones ya presentes en `ReglaCientifica.aplicabilidad` deben
conservarse como obligatorias, idénticas. No pueden omitirse o volverse
condicionales. Si la regla tiene parámetros, exige un requisito obligatorio de
correspondencia documental; este verificador no calcula ni ejecuta esos parámetros.
Un plan vacío o sin referencias produce información insuficiente.

Las coberturas geográficas, períodos de aplicación, restricciones y correspondencia
de parámetros se comparan mediante etiquetas literales sustentadas en documentos.
**No hay cálculo de intersección, contención geográfica, intervalos de vigencia
ni conversiones temporales.** Esa relación debe documentarse explícitamente con
valores compatibles; no se deduce de una etiqueta mayor o de la fecha del sistema.
`VIGENTE` describe la evidencia aportada, no una comprobación actual del emisor.

Política conservadora:

- Una coincidencia demuestra el requisito solo con afirmaciones y documentos
  clasificados como verificados, con versión, fecha y vigencia conocida, sin
  incertidumbres o pendientes relevantes.
- Una coincidencia declarada/inferida, vigencia desconocida o pendientes produce
  condicionamiento. Un valor distinto no verificado tampoco demuestra una
  incompatibilidad: queda condicionado para revisión.
- Un requisito obligatorio sin valor/documento, nivel desconocido o documento
  sin versión/fecha produce información insuficiente.
- Un valor verificado incompatible o un documento clasificado como verificado
  y obsoleto produce incompatibilidad documentada.
- Valores discrepantes para la misma dimensión, evidencia explícitamente
  contradictoria, contradicciones de la regla, metadatos diferentes para el mismo
  documento o ediciones distintas en el mismo localizador se conservan como
  contradicción. No se escoge la fuente favorable. Alias de una misma referencia
  y distintas secciones de un mismo documento no son contradicciones por sí solos.
- El ID del producto afirmado debe coincidir con el de `ProductoCatalogo`.
  No se inventan códigos de estación ni identidades de serie.

Un requisito condicional se activa solo si la condición está demostrada. Si el
valor activador es verificado e incompatible, el requisito se informa NO_APLICA.
Una condición desconocida, declarada o inferida no se desactiva silenciosamente:
queda condicionada. Una vez activado, el requisito necesita evidencia igual que
uno obligatorio. Su hallazgo conserva también las referencias de activación.

La zona horaria desconocida no bloquea un límite estático que no la exige.
Sí bloquea un requisito temporal que la declare obligatoria. No se asigna UTC,
se reconstruye HORA/UBIGEO ni se repara la información temporal.

Estados globales, en orden de prioridad si coexisten hallazgos:

1. EVIDENCIA_CONTRADICTORIA.
2. INCOMPATIBILIDAD_DOCUMENTADA.
3. INFORMACION_INSUFICIENTE.
4. COMPATIBILIDAD_CONDICIONADA.
5. COMPATIBILIDAD_DOCUMENTAL_DEMOSTRADA.

La prioridad no oculta hallazgos: todos se conservan. Se audita todo el expediente
aportado, incluso documentos adversos no utilizados en el cotejo. Por ello un
documento ajeno sin versión añadido al expediente puede impedir un diagnóstico
demostrado: el llamador debe delimitar un expediente pertinente, sin descartar
evidencia desfavorable. Los motivos son códigos fijos, sin interpolar valores.
La traza sí conserva los metadatos aportados: no deben incluir credenciales,
tokens, datos personales o rutas privadas innecesarias.

## Barreras y límites de confianza

El resultado mantiene `ejecucion_autorizada=False` sin parámetro de activación,
no es callable, no es una habilitación y rechaza su conversión booleana.
Conserva explícitamente `naturaleza_evidencia=SINTETICA` en ensayos. Una
`EvidenciaSintetica` del PASO 75 no se convierte en referencia documental.
No hay función para aprobar reglas, crear decisiones humanas, activar métodos,
conectar con un ejecutor o importar una configuración ejecutable. Una etiqueta
APROBADA tampoco habilita la API; la revisión no se acepta como entrada.

La verdad de una clasificación documental es responsabilidad del expediente y
su revisión humana. Esta biblioteca no autentica al usuario ni al emisor y no
es una barrera contra código Python hostil que fabrique contratos o cambie sus
metadatos deliberadamente. No existe un mecanismo criptográfico que impida
reetiquetar manualmente una fixture. Por esa incompatibilidad no se conecta el
diagnóstico a ninguna autorización: **ni siquiera evidencia declarada como
DOCUMENTAL y VERIFICADA puede generar aquí un permiso operativo**.

La extensión multiinstitucional se apoya en identificadores y referencias
explícitos. Puede describir meteorología, hidrología, agua, hidrogeoquímica,
suelos, geología y aire, sin tablas precargadas ni equivalencias atribuidas a
SENAMHI, ANA, OEFA, INGEMMET o entidades privadas. No incorpora sus procedimientos.

## Pruebas y comprobaciones

Las pruebas nuevas usan únicamente documentos, productos, variables y fuentes
inventados. VERIFICADA/VIGENTE significan verdaderas solo dentro de esa fixture.
No crean aprobaciones humanas reales ni instancian lectores de datos operativos.
Cubren compatibilidad, incompatibilidades, faltantes, agregación, estación,
geografía, continuidad, versiones, vigencia, contradicciones, condiciones,
incertidumbre, trazabilidad, determinismo, inmutabilidad y presupuestos.

Se prueba que el diagnóstico no habilita el catálogo ni el PASO 75, no ejecuta
código de cadenas y funciona con I/O, SQLite, red y evaluador numérico bloqueados.
Se comparan resultados de Nivel 0 antes/después sobre una fila sintética.
La suite anterior permanece sin cambios.

El informe final registra los resultados de la suite completa y las comprobaciones
de dependencias, sintaxis y whitespace, incluyendo los archivos sin seguimiento.
No se accede al RAW, staging ni SQLite operativo, tampoco para inventarios o hashes.

Véase la [matriz TEMP/HR y solicitudes documentales](aplicabilidad_temp_hr_lim.md).

## Resultado final de verificación

Entorno comprobado: Python 3.15.1 de `.venv`, HTTPX 0.28.1 y SQLite 3.53.4.

```text
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
Ran 935 tests in 109.740s
OK

.\.venv\Scripts\python.exe -B -m pip check
No broken requirements found.

git diff --check
Sin salida; código 0.

git status --short
?? docs/aplicabilidad_temp_hr_lim.md
?? docs/verificador_aplicabilidad_cientifica.md
?? src/spica/calidad/aplicabilidad/
?? tests/test_aplicabilidad_cientifica.py
```

**935 aprobadas: 872 anteriores y 63 nuevas; cero fallos, errores u omisiones.**
Los identificadores completos de las 872 anteriores coinciden exactamente con el
registro del PASO 75. La prueba focalizada también aprobó sus 63 casos.

La suite se ejecutó con `PYTHONPATH` temporal para `src` y una guardia de pruebas
fuera del repositorio. La guardia bloquea accesos Python a las rutas operativas
conocidas bajo `SPICA_DATOS` y conexiones de red; registró cero intentos bloqueados.
No es un sandbox del sistema operativo ni demuestra cobertura de alias, hardlinks
o código nativo hostil. Se revisaron también las referencias de rutas de las
pruebas: las dos menciones de SPICA_DATOS/staging son ubicaciones virtuales en
fixtures de configuración. No hubo inventario, apertura, hash o comprobación de
persistencia del RAW/staging/SQLite operativo en este paso.

El log completo, resultado JSON y guardia quedan en el directorio temporal de
verificación `spica-paso76-753a7662d21945509a6ddcc698ca8f6f`, fuera de Git y de
las raíces operativas. Dos preparaciones previas del ayudante temporal con
`tempfile.mkdtemp` encontraron WinError 5 al crear un subdirectorio, antes de
iniciar pruebas. Se utilizó un directorio temporal nuevo con el patrón de creación
0755 ya empleado por las pruebas del proyecto, sin cambiar ACL existentes.
No son fallos de la suite ni se intentó corregirlos accediendo al almacenamiento.

Se comprobó directamente UTF-8, sintaxis mediante compilación en memoria, salto
final, ausencia de espacios finales y marcadores de conflicto de los seis archivos
nuevos. `git diff --name-only` continúa vacío: no hay modificaciones a archivos
previamente registrados. HEAD permanece `e9f9b32`, rama `feature/suadc-http`.
No se instalaron dependencias, hicieron descargas, migraciones, commits o push.
