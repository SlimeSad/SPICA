# PASO 84-B: adaptadores científicos offline y auditoría de interoperabilidad

## 1. Alcance y recuperación del estado

Informe elaborado el **2026-11-04**. Estado inicial: árbol limpio en
`feature/suadc-http`, HEAD **`41332a0`**, `SUADC: nucleo de interoperabilidad
espaciotemporal`. El PASO 84-A está registrado. Se mantiene ese commit y no se
alteran los archivos registrados previamente.

Entorno comprobado con `.venv`: Python **3.15.1**, HTTPX **0.28.1**, SQLite
**3.53.4**. Este incremento incorpora exclusivamente objetos sintéticos en memoria.
No se leen CSV, geometrías, archivos institucionales ni evidencia real conservada.
El piloto INGEMMET `/query` sigue **NO AUTORIZADO**. La respuesta institucional y
las condiciones de uso continúan pendientes.

Se conserva íntegro el [núcleo del PASO 84-A](interoperabilidad_espaciotemporal.md).
La auditoría sintética no encontró un defecto reproducible que justifique
modificar sus contratos, evaluador o exportaciones.

## 2. Arquitectura y archivos nuevos

| Archivo | Responsabilidad |
|---|---|
| [adaptadores.py](../src/spica/interoperabilidad/adaptadores.py) | Adaptación de catálogo, meteorología y metadatos vectoriales, diagnósticos e instantáneas originales |
| [operaciones.py](../src/spica/interoperabilidad/operaciones.py) | Requisitos explícitos de una operación propuesta, sin ejecutar operaciones científicas |
| [test_adaptadores_interoperabilidad.py](../tests/test_adaptadores_interoperabilidad.py) | Correspondencias, desconocidos, contradicciones, conservación y ausencia de I/O |
| [test_integracion_interoperabilidad.py](../tests/test_integracion_interoperabilidad.py) | Escenarios A–H, auditoría temporal, revisiones y límites de las conclusiones |
| Este documento | Diseño, auditoría, resultados y condiciones pendientes |

Importaciones explícitas:

```python
from spica.interoperabilidad.adaptadores import (
    adaptar_catalogo, adaptar_meteorologia, adaptar_vectorial,
)
from spica.interoperabilidad.operaciones import (
    OperacionPropuesta, evaluar_operacion,
)
```

Se reutilizan `Fuente`, `ProcedenciaCatalogo`, `EstadoVerificacion`,
`RecursoCatalogo`, `ProductoCatalogo`, `EvidenciaDocumental`, `EstacionCatalogo`,
`DisponibilidadCatalogo`, `VariableCatalogo`, `ObservacionLocal`, `RecursoVector`,
`ValidacionMetadatos`, `ReferenciaEspacial` y los contratos del núcleo. No se crea
un segundo modelo de estación, serie, geometría o procedencia.

Los adaptadores reutilizan las validaciones del núcleo y el congelador de valores
vectoriales existente. Los modelos temporales continúan usando los validadores
de intervalos y UTC del proyecto. No se duplican conversores horarios.

Dependencias transitivas: catálogo carga definiciones de almacenamiento; el
paquete del inspector ArcGIS carga definiciones del transporte y HTTPX. Importar
los adaptadores no instancia clientes, abre almacenes ni ejecuta I/O. No se
añaden dependencias. La importación independiente de `spica.interoperabilidad`
conserva el comportamiento del 84-A y no carga los adaptadores automáticamente.

## 3. Resultado y diagnósticos

`ResultadoAdaptacion` contiene `estado`, `recurso` opcional, `diagnosticos`,
`originales` y `version_adaptador="0.1.0"`. Cada diagnóstico tiene un código fijo,
campo y nivel: información, faltante o contradicción. No incluye valores de
entrada, excepciones de disco, credenciales ni rutas operativas.

| Estado de adaptación | Significado |
|---|---|
| `DESCRITO` | Descripción construida; no afirma aptitud ni verificación científica |
| `PARCIAL` | Existe descripción, pero faltan datos o evidencia |
| `CONTRADICTORIO` | Existe identidad conservada y contradicciones explícitas; también se incorporan al recurso para que el evaluador las bloquee |
| `NO_REPRESENTABLE` | No se produce recurso; inspección incompleta, estructura inválida o límites excedidos |

Las identidades y cadenas se conservan literalmente, incluidos espacios. Un
objeto de otro tipo o una revisión local inválida producen errores de contrato;
los adaptadores no intentan adivinar interfaces. Los datos representables de
entradas contradictorias se conservan, aunque no se combinen sus marcos.

`originales` es una copia profunda e inmutable para auditoría, no un archivo RAW,
un esquema de persistencia ni una nueva fuente de evidencia. Conserva los campos
de los objetos recibidos, sus estados y procedencias. Las fechas se describen
mediante tipo, ISO original y, para datetime, `fold` y clave de zona si existe.
No se convierten a UTC ni se altera el objeto temporal trasladado al núcleo.
No reconstruye bytes de un archivo ni serializa íntegramente reglas de una zona.
Para reproducir esas reglas deben conservarse también los objetos/evidencias
aportados; las referencias no se resuelven automáticamente.

Presupuestos: 100000 nodos y profundidad 32 en la captura, textos y claves de
hasta 65536 caracteres, además de los límites conservadores del congelador y del
núcleo (por ejemplo, 64 atributos declarados y textos del núcleo de 4096).
No se trunca para simular éxito. Si la captura no es posible, se informa
`NO_REPRESENTABLE` con originales vacíos y un diagnóstico explícito: el llamador
debe conservar las entradas fuera del adaptador. No se permite código arbitrario.
No debe imprimirse ni publicarse el contenido de `originales` sin revisión de
privacidad: puede contener los metadatos sensibles que el llamador aportó.

## 4. Correspondencia con catálogo y procedencia

| Entrada existente | Destino o tratamiento |
|---|---|
| `RecursoCatalogo.fuente / identificador / producto_id / localizador` | `IdentidadRecurso`, sin normalización |
| `RecursoCatalogo.procedencia` | Procedencia principal; su fecha de revisión no es observación, publicación ni adquisición |
| `ProductoCatalogo.version` | Versión institucional, solo si fuente y producto coinciden |
| `ProductoCatalogo.restricciones_licencia` | Condiciones declaradas de producto si el recurso no las declara; procedencia y alcance originales conservados |
| Licencia del recurso / evidencia documental | Se conservan ambas; textos diferentes requieren aclaración de alcance, sin inferir equivalencia ni prohibición jurídica |
| `EvidenciaDocumental.estado / revisiones / capacidades / procedencia` | Conservados en la instantánea; no verifican coordenadas, períodos o autenticidad física |
| Metadatos espaciales/temporales ausentes | Marcos ausentes y diagnóstico; no se construyen a partir del título o localizador |

No se acepta silenciosamente producto o evidencia de otra fuente/recurso. Una
referencia textual de evidencia permite documentar una declaración; no demuestra
por sí misma que un documento sea auténtico o científicamente suficiente.

## 5. Correspondencia meteorológica

`adaptar_meteorologia` recibe un recurso de catálogo y, opcionalmente, estación,
disponibilidad, variable y observación ya construidas. Verifica la coincidencia
literal de fuente/producto y los vínculos de estación, variable y recurso.

| Entrada existente | Destino o límite |
|---|---|
| `EstacionCatalogo.identificador` | `espacial.identificador_ubicacion`; no es el nombre de la estación |
| `coordenada_x / coordenada_y` | Par original numérico, estado DECLARADO: el modelo no aporta verificación específica de coordenadas |
| `sistema_referencia` | Declaración textual del CRS de geometría; sin inventar definición, ejes o unidades |
| `ObservacionLocal.campos_originales` | Pares originales del marco temporal; ubicación literal también conservada en el marco espacial |
| `ObservacionLocal.fecha_civil` | Fecha civil ya interpretada por el modelo de entrada; no se convierte en instante |
| `DisponibilidadCatalogo.inicio / fin / estado / procedencia` | Período documentado con su respaldo original; no se cambia declarado por verificado |
| `precision_temporal / zona_horaria` | Resolución y zona declaradas, incluidas las ausencias |
| `frecuencia_declarada` | Conservada separadamente en originales; no se sustituye resolución por frecuencia |
| `VariableCatalogo.codigo_original / unidad_declarada / tipo_medicion` | Código como atributo declarado; demás metadatos completos en originales |
| `DisponibilidadCatalogo.identificador` | Identidad de disponibilidad en originales, nunca identificador científico de serie |
| `ProcedenciaLocal.asset_id / sha256_declarado / líneas` | En originales; no se abre ni verifica físicamente el activo |

No existe un contrato estable de serie con identificador propio entre estas
entradas. Se documenta ese desconocido; no se sintetiza un ID concatenando
estación y variable. Tampoco hay campos de inclusividad, convención o incertidumbre
temporal en disponibilidad: quedan desconocidos y bloquean la alineación.

La revisión del catálogo o la comprobación de disponibilidad no pasan a ser
publicación ni adquisición. Un período marcado verificado no verifica por
extensión la interpretación de `HORA`, que queda declarada y sin localización.
El offset de los extremos, si existe, se conserva; no se deduce de él una zona
institucional no documentada.

`HORA="10000"`, `UBIGEO="12345.0"` y coordenadas textuales conservan exactamente
esos valores. No se completan ceros, parsean coordenadas, reconstruyen códigos,
geocodifican nombres ni equiparan estaciones entre fuentes. Igualdad de nombres
solo permite reconocer una coincidencia literal; la identidad física no queda
verificada. Una fecha imposible aportada como cadena en `fecha_civil` no se
interpreta: resultado no representable. El adaptador no vuelve a parsear FECHA
ni certifica la interpretación previa de un consultor.

## 6. Correspondencia vectorial

Se acepta `RecursoVector` junto con una inspección completa de capa, JSON completo,
alcance esencial y estado coherente. Se conserva el vínculo servicio/capa del
objetivo; identificadores, nombres u hosts contradictorios no se unifican.

| Entrada existente | Destino o límite |
|---|---|
| Fuente, producto, recurso, servicio y capa | Identidad y originales exactos; el objetivo aporta el localizador de capa si no se aporta catálogo |
| `geometryType` | Geometría DECLARADA, sin entidades vectoriales inspeccionadas |
| `spatialReference` | CRS de GEOMETRIA exclusivamente |
| `extent.spatialReference` | CRS de EXTENSION exclusivamente |
| `sourceSpatialReference` | CRS de ORIGEN exclusivamente |
| `extent.xmin/ymin/xmax/ymax` | Extensión anunciada estructurada, DECLARADA; no cobertura observada |
| `fields[].name` | Atributos declarados literales; estructura y tipos íntegros en originales |
| `currentVersion` | Versión técnica del servidor en originales; nunca edición científica del producto |
| `ValidacionMetadatos.sha256 / bytes_recibidos / advertencias / objetivo` | Evidencia técnica declarada conservada; el adaptador no calcula ese hash ni verifica un archivo |
| Revisión local exigida al llamador | `revision_metadatos`, independiente de los campos ArcGIS |
| Licencia del catálogo opcional | Condiciones de uso declaradas, sin autorización implícita |

La extensión no se usa como CRS de geometría si falta el CRS de geometría. Los
pares `wkid/latestWkid` se mantienen literalmente; no se resuelven alias, orden
de ejes ni equivalencias. Una definición CRS sin WKID se conserva en originales
con diagnóstico, sin convertir WKT. No se asignan unidades globales del servicio
a ámbitos o ejes no acreditados.

El contrato del inspector esencial no aporta una cobertura textual verificada,
edición del producto o licencia. `cobertura_anunciada` textual permanece ausente;
la extensión anunciada se conserva en su campo estructurado. La escala, aun si
fuese aportada entre otros metadatos, no constituye precisión posicional. Las
coordenadas, cobertura, precisión y calidad geográfica no quedan verificadas por
un JSON coherente, por su hash o por el nombre de un servicio.

## 7. Auditoría temporal y de incertidumbre

El evaluador **0.1.0** permanece intacto. Las pruebas nuevas integran sus controles
con las descripciones y políticas de operación; las pruebas anteriores conservan
la cobertura de validadores, `fold`, límites civiles y horas inexistentes.

| Situación sintética | Resultado comprobado |
|---|---|
| Instantes equivalentes con offsets UTC, −05:00 y +03:00 y respaldo completo explícito | Aptitud temporal estructural; se preservan objetos, offsets y textos distintos |
| Horas locales naive o zona/convención desconocidas | Pendiente; no se realiza comparación absoluta suficiente para declarar aptitud |
| Intervalo puntual con ambos extremos incluidos | Admitido cuando el contrato y la evidencia son coherentes |
| Intervalos que se tocan | Soporte común solo si ambos incluyen el extremo compartido |
| Intervalos separados o contacto excluido | Incompatible para la alineación directa planteada |
| Solo publicación/adquisición disponibles | No sustituyen al período de observaciones; pendiente |
| Fecha fuera del período o zona declarada UTC incompatible con el offset | Contradicción y estado incompatible |
| Fecha imposible o intervalo invertido | Rechazo del contrato; sin reparación automática |

La inclusividad es una pareja explícita por período. Si el modelo de entrada no
la documenta, queda `None`: el adaptador no presupone intervalos cerrados.
Las fechas civiles no pasan a horas y los datetime naive no reciben una zona.
Los cálculos internos de UTC se limitan a instantes ya localizados y no alteran
los registros originales.

La falta de precisión espacial **no bloquea una evaluación exclusivamente
temporal** cuando sus requisitos temporales están satisfechos. El evaluador
espacial del 84-A exige precisión, incertidumbre y sus respaldos en toda evaluación
espacial que actualmente admite; no ofrece una política espacial relajada.
La incertidumbre temporal sigue siendo necesaria para la aptitud temporal.

`OperacionPropuesta` exige identificador, dimensión y decisión booleana explícita
`requiere_precision_posicional`. `evaluar_operacion` conserva el resultado del
núcleo y añade faltantes de la operación cuando se exige precisión. Declarar
`False` no elimina controles del núcleo. Una propuesta exclusivamente temporal
con precisión posicional exigida se rechaza por incoherencia de alcance.

`condiciones_documentales_satisfechas` solo es verdadera con núcleo apto y sin
faltantes adicionales. Es una comprobación de requisitos declarados, no una
conclusión sobre idoneidad científica universal: todavía no existe un catálogo
de requisitos por algoritmo. En todos los casos `operacion_ejecutada=False`,
`verificacion_espacial_efectiva=False` y `confiabilidad_cientifica="no_evaluada"`.

## 8. Escenarios de integración y revisiones

| Escenario | Resultado real de la simulación |
|---|---|
| A. Estación sin coordenadas y capa con CRS | Pendiente; no se ubica la estación por nombre |
| B. Fechas aparentemente compatibles sin zona documentada | Pendiente temporal; ninguna equivalencia absoluta afirmada |
| C. Información espacial declarada, no verificada | Pendiente; declaraciones conservadas sin promoción |
| D. CRS de geometría y extensión distintos | Ámbitos conservados; pendiente con los respaldos insuficientes aportados, sin reproyección ni homogeneización |
| E. Nueva evidencia contradice estación vinculada | Nueva revisión incompatible; revisión, evidencia y resultado anteriores inalterados |
| F. Evidencia completa exclusivamente inventada | Apto estructuralmente incluso con coordenadas distintas; no afirma superposición |
| G. Procedencia sin evidencia suficiente | Pendiente con faltante explícito de procedencia |
| H. Operación que exige precisión ausente | Bloqueada; declarar que no la exige tampoco relaja la política espacial del núcleo |

En F se aporta **una nueva descripción sintética con respaldo explícito** mediante
los contratos existentes; el adaptador no transforma metadatos declarados en
verificados. En A–H no se ejecuta ninguna operación científica y la confiabilidad
permanece sin evaluar.

Una revisión futura se obtiene adaptando entradas nuevas con otra revisión local,
conservando ambos `ResultadoAdaptacion`. El vínculo `sustituye_revision` se puede
explicitar con `dataclasses.replace` del recurso existente. No se muta el anterior.
Cada `ResultadoAptitud` retiene sus dos descripciones, evidencias y versión del
evaluador. Para conservar todos los campos originales adicionales debe guardarse
también el `ResultadoAdaptacion`; el resultado del núcleo no agrega esos campos.
La prueba E reproduce el resultado con entradas y versiones iguales e incorpora
una respuesta futura ficticia sin reescribir la evidencia anterior. No se añade
persistencia, registro global ni historial SQLite.

## 9. Verificación y seguridad

Pruebas nuevas: **32** (19 de adaptadores y 13 de integración/auditoría). Se usan
únicamente fixtures sintéticas, con institución, producto, campos y WKID
explícitamente inventados. No son ejemplos oficiales ni recomendaciones GIS.

Comandos de cierre con el intérprete `.venv`, `-B` y `src` en `PYTHONPATH`:

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -B -m pip check
git diff --check
git status --short
```

La suite se ejecuta con una guardia temporal externa al repositorio que bloquea
red, el árbol operativo `SPICA_DATOS` y los directorios conocidos de evidencia
institucional local. Los subprocesos heredan esa guardia. Los tests históricos
pueden usar MockTransport, memoria y sus propios directorios temporales aislados;
eso no constituye GET externo ni acceso operativo. Los adaptadores nuevos además
se prueban con apertura de archivos, sockets y SQLite sustituidos por errores.

Se comprobó además que un indicador `coherencia_servicio_capa=False` conserve una
contradicción explícita, incluso si un objeto construido manualmente conserva
otros indicadores positivos. Ese refuerzo del adaptador tiene regresión propia;
no cambia el inspector ni el núcleo. Durante el desarrollo se corrigieron dos
errores de las pruebas nuevas: el nombre real `version_evaluador` y el tipo de
excepción de `dataclasses.replace` para un campo `init=False` en Python 3.15.

Resultado final del comando de pruebas:

```text
Ran 1420 tests in 154.217s

OK
```

| Comprobación | Resultado |
|---|---|
| Pruebas aprobadas | **1420**: las **1388** anteriores y **32** nuevas |
| Fallidas / errores | **0 / 0** |
| Pruebas anteriores omitidas o sin aprobar | **0**, cotejando los identificadores con los tests registrados en HEAD |
| Identificadores de pruebas duplicados | **0** |
| `pip check` | `No broken requirements found.` |
| `git diff --check` | Código 0, sin salida |
| Sintaxis de los cuatro Python nuevos | Compilación en memoria correcta; sin crear bytecode |
| Revisión estática y documental | Sin definiciones duplicadas, truncamientos, espacios finales ni enlaces locales rotos |
| Guardia de los procesos finalizados | Instalada; **0 accesos prohibidos registrados** |
| Cambios en archivos previamente registrados o en el índice | Ninguno |

Estado Git final:

```text
?? docs/adaptadores_interoperabilidad_offline.md
?? src/spica/interoperabilidad/adaptadores.py
?? src/spica/interoperabilidad/operaciones.py
?? tests/test_adaptadores_interoperabilidad.py
?? tests/test_integracion_interoperabilidad.py
```

Los cinco archivos nuevos fueron inspeccionados explícitamente: `git diff` no
incluye archivos sin registrar. Los temporales de la suite se limpiaron. Los
logs detallados y la guardia auxiliar quedan en un directorio temporal de esta
verificación fuera de Git, sin datos institucionales. No se realizaron commits,
instalaciones, descargas ni migraciones.

No se accedió a RAW, staging o SQLite operativos. No se ejecutan inventarios
físicos de RAW para demostrar ausencia de cambios: hacerlo violaría la prohibición
de acceso de este paso. La afirmación se sustenta en la ausencia de operaciones
contra esas ubicaciones y en la guardia, no en un nuevo cotejo de hashes reales.

## 10. Limitaciones, pendientes y dictamen

Implementados: tres adaptadores puros, instantáneas y diagnósticos, requisitos
documentales explícitos por operación y escenarios sintéticos. No se modifica la
API pública anterior ni se corrigen módulos operativos.

Pendientes antes de una integración operativa:

- Documentar identidad de serie, correspondencia física de estaciones, CRS por
  ámbito, unidades de ejes y procedencia de cada interpretación faltante.
- Acreditar convenciones y zonas temporales, inclusividad e incertidumbres; las
  ambigüedades de HORA, UBIGEO y nombres no se resuelven aquí.
- Obtener evidencias geográficas y requisitos específicos por operación, sin
  confundir preparación documental con confiabilidad de un resultado GIS.
- Diseñar, si se aprueba, adaptadores para contratos distintos de los tres
  cubiertos y preservación persistente de las revisiones; no se incluyen lectores
  de CSV, adquisición de geometrías, raster, serialización ni automatización RAW.
- Revisar el acoplamiento a validadores internos reutilizados si esos módulos
  cambian de versión; esta entrega mantiene sus implementaciones y pruebas.
- Resolver identidad y equivalencia de productos INGEMMET, condiciones de uso y
  respuesta institucional. El primer `/query` sigue bloqueado.

No se ejecutan reproyecciones, intersecciones, geocodificación, distancias, áreas,
topología, interpretación de litologías ni reglas QA/QC científicas. Una alerta
documental o aptitud estructural no demuestra superposición, contaminación,
causalidad ni validez científica.

Dictamen de alcance: **APTO CON RESTRICCIONES para integración experimental
offline de contratos**. No habilita pilotos
institucionales ni uso científico operativo. Se espera revisión antes de avanzar.
