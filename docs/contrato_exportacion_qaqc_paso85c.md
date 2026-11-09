# PASO 85-C — Contrato experimental de exportación QA/QC estructural

Fecha local: **2026-11-08, America/Lima**. Ensayo técnico: **2026-11-09 UTC**.
Versión de exportación: **0.1.0**. **APTO CON RESTRICCIONES** para revisión offline;
no habilita QA científico, permisos ni el PASO 85-D.
Resultados: [piloto y verificaciones](piloto_exportacion_qaqc_paso85c.md).

## Revisión previa y riesgo comprobado

Git inicial limpio, rama **feature/suadc-http**, HEAD **b2c0171**, «SUADC:
versionado y restricciones QAQC estructural nivel 0»; 85-B consolidado.
Se revisaron [inventario 85-A](inventario_qaqc_nivel0_paso85a.md),
[piloto 85-A](piloto_qaqc_estructural_paso85a.md),
[auditoría 85-B](auditoria_contratos_qaqc_paso85b.md),
[versionado 85-B](versionado_restricciones_qaqc_paso85b.md),
[modelos](../src/spica/calidad/modelos.py), [motor](../src/spica/calidad/motor.py),
[reglas](../src/spica/calidad/reglas.py),
[restricciones](../src/spica/calidad/restricciones.py), procedencia y consumidores.

asdict(ResultadoQA) produce nueve claves: regla, registro, procedencia,
valores_originales, evidencia, parametros, estado, diagnostico y version_contrato.
No incorpora estado_evaluacion (propiedad), restricciones calculadas, escenario,
identidad contextual de ejecución ni configuración completa. Tampoco convierte
Enums/fechas automáticamente a JSON. Una exportación parcial perdería límites
científicos, incluso en comprobaciones satisfechas.

La búsqueda en src/, herramientas/ y pruebas no encontró una exportación pública
JSON de ResultadoQA ya implementada. Los tests 85-B usan asdict para comprobar
inmutabilidad/esquema, no como permiso. Motor y tests Nivel 0/85-A/85-B consumen
los modelos nativos; los contratos científicos reutilizan RegistroQA,
ProcedenciaQA y EstadoEvaluacionQA, sin esta ruta de exportación. Los diarios
documentales manual/HTTP poseen JSON propio con otros contratos y persistencia:
se revisaron como precedentes de tipos/versiones, no se invocan ni reutilizan
sus efectos operativos, UUID o almacenamiento.

## API y separación de responsabilidades

Módulo nuevo: [calidad/exportacion.py](../src/spica/calidad/exportacion.py).
Importación explícita experimental, sin cambiar calidad/__init__.py:

```python
from spica.calidad.exportacion import (
    ContextoExportacionQA, LimitesExportacionQA, exportar_resultado_json,
)
```

exportar_resultado_json(resultado, contexto, *, limites=None) devuelve **str**
JSON estricto en memoria. Reutiliza ResultadoQA y restricciones_resultado del
85-B; no evalúa de nuevo reglas, no crea otro modelo de resultado ni otro motor.
No abre archivos, red, SQLite, inspectores o cotejadores; no usa reloj o azar.
Guardar/publicar la cadena corresponde a una operación futura separada.

ContextoExportacionQA exige espacio_id, evaluacion_id y entrada_id. Admite
escenario_id, configuracion QA nativa, metadatos_requeridos, metadatos_ausentes
e incertidumbres declaradas. No impone institución, producto, columnas o
variables; no requiere SENAMHI para exportar. Si se aporta ConfiguracionQA,
esta conserva su especialización actual sin ampliarla a otras disciplinas.

Los IDs de contexto son ASCII explícito de 1–128 caracteres, patrón
`[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}`. No son URLs autenticadas ni identidades
institucionales comprobadas. Los textos originales admiten Unicode, sin
normalización, recorte, interpretación numérica o relleno de ceros.

## Esquema JSON 0.1.0

Todas las claves siguientes se emiten; desconocidos justificados son null,
no cadenas inventadas. Las claves de objetos se ordenan lexicográficamente;
las listas conservan el orden literal significativo de los contratos nativos.

| Campo | Tipo JSON | Significado y límite |
|---|---|---|
| version_esquema | string | Literal 0.1.0, independiente del contrato QA |
| resultado_id | string | qa0- y 64 caracteres hex SHA-256 de identidad contextual |
| huella_contenido | string | SHA-256 del resultado nativo serializado; no es hash físico del original |
| naturaleza_identidad | string | contextual_declarada_no_verificada |
| contexto | object | espacio_id/evaluacion_id/entrada_id, escenario_id string o null, configuración object o null, inventarios y motivos declarados |
| campos_objetivo | array de strings | Nombres de valores_originales; vacío significa que no hay campo individual en la emisión |
| versiones | object | contrato_qa string, evaluador string o null, restricciones string |
| resultado | object | Las nueve claves nativas completas, incluidos registro/brutos, regla/categoría, evidencia, parámetros y procedencia |
| estado_evaluacion | string | completa, incompleta o no_evaluada, derivado del estado nativo |
| detalle_diagnostico | string | Descripción existente de la regla, hasta 4096 caracteres; no inventa una explicación científica |
| campos_objetivo_no_aportados | array de strings | Solo objetivos cuyo valor nativo es None; no confunde vacío con ausencia |
| restricciones | object | Listas informativas y bloqueantes, calculadas automáticamente por la política 85-B |
| limitaciones | array de strings | Alcance de identidad/procedencia, verificación física, equivalencia editorial, ciencia, autorización e inventario |

Dentro de contexto, metadatos_requeridos/metadatos_ausentes son arrays de strings
o null. null indica inventario no aportado; [] inventario declarado vacío. Si se
declaran ausencias, debe existir inventario requerido y aquellas ser subconjunto
de este. No se certifica exhaustividad ni se inspeccionan documentos para
comprobarlo. incertidumbres es un array de motivos declarados. Cada inventario
o lista de motivos admite hasta 32 textos únicos de hasta 512 caracteres.

resultado conserva sus tipos nativos convertidos explícitamente: tuplas y pares
→ arrays, enums conocidos → strings value, datetime documental consciente →
ISO 8601 con su referencia temporal. Los valores de observación siguen siendo
strings o null. No se convierten fechas/HORA observacionales ni zonas desconocidas.
El código de diagnóstico permanece en resultado.diagnostico; su estado no se
reemplaza por un indicador global de dato válido/confiable.

## Identidad global condicionada al contexto

El llamador coordina un **espacio de identidad**, un ID de evaluación distinto
para cada ejecución independiente y un ID de entrada estable dentro de su
escenario. Una repetición de reproducibilidad reutiliza el mismo contexto;
otra adquisición/ejecución debe declararse como tal con otro evaluacion_id.
El exportador no genera identidades aleatorias ni verifica un registro global.

La base de resultado_id es JSON canónico de:

```text
contexto completo,
numero_registro, linea_inicial, linea_final,
regla_id, version_regla, version_evaluador,
version_contrato_qa, version_restricciones, version_esquema,
campos_objetivo ordenados
```

Se aplica SHA-256 a UTF-8, sin concatenaciones ambiguas. No depende del orden
en que lleguen las emisiones ni únicamente del contenido/ID original del registro.
Dos filas iguales se distinguen por identidad de entrada y posiciones legítimas;
reglas, campos, versiones, escenarios, espacios y ejecuciones diferentes quedan
separados. La configuración **literal** aportada también participa: no se afirma
equivalencia semántica de dos configuraciones con listas ordenadas de otro modo.

La unicidad global depende de no reutilizar contexto indebidamente; no acredita
identidad institucional del registro o estación. Colisiones criptográficas no
son una imposibilidad matemática, aunque no se observaron en el piloto.
Reutilizar contexto para una condición con diagnóstico/contenido diferente puede
mantener resultado_id y cambiar huella_contenido: es una contradicción detectable,
no un resultado que deba sobrescribirse. Un futuro consumidor deberá rechazarla.
No se implementan ahora registro global, lote persistente o deduplicación.

## Versiones y fidelidad

Exportación **0.1.0**, QA **1.0.0**, regla individual **1.0.0** para las 22
existentes, emisor **1.0.1** y restricciones **1.0.0** son dimensiones distintas.
El emisor se lee del único parámetro evaluador_nivel0; si falta, se conserva null.
No se asigna retrospectivamente 1.0.1. Duplicación de ese parámetro, versión
malformada o contrato QA incompatible se rechazan. No se modifica ninguna regla,
estado, constructor o salida anterior. Una regla ficticia puede representarse
como descriptor nativo: exportarla no acredita su registro, ejecución o aprobación.

Se preservan evidencia utilizada, referencias declaradas, revisión desconocida,
estado documental aportado, parámetros repetidos legítimos de identidad y
procedencia desconocida. SHA de referencia y estado documental declarado no
se convierten en comprobación física o autenticación por el exportador.
huella_contenido solo sirve para comparar representaciones técnicas.

## Restricciones automáticas y separación científica

Cada anotación conserva codigo, tipo, operaciones y motivo exactos del 85-B.
Se separan INFORMATIVA y BLOQUEO_USO_DEL_RESULTADO en listas del mismo paquete,
con versión explícita de política. No requiere una segunda llamada del usuario.
Los bloqueos indican para qué uso no basta ESTE diagnóstico como evidencia;
no son una decisión global de permiso. Ausencia de un bloqueo tampoco autoriza.

HORA mantiene el límite de no construir instantes, asignar zona ni completar
ceros; UBIGEO no se normaliza, geocodifica ni valida territorialmente; PP no se
convierte mm↔mm/h ni se interpreta como acumulación/intensidad. TEMP/HR no ganan
plausibilidad o calidad instrumental por tener gramática numérica válida.
La procedencia no autentica originales, ni una coincidencia representa
equivalencia editorial o permiso de redistribución.

NO_EVALUADO conserva motivo y bloqueo de dar por evaluada la condición;
EVALUACION_INCOMPLETA conserva impedimento y bloqueo de darla por concluida.
Una COMPROBACION_SATISFECHA puede coexistir con ambos límites científicos
generales y los del campo. Estas anotaciones expresan alcance del nivel 0,
no afirman como hecho que un metadato no exista en otra fuente.
No hay campo autorizado, dato válido, dato confiable ni ejecutor científico.

## Validaciones y límites de recursos

Se admiten clases nativas y enums conocidos, valores JSON elementales y fechas
documentales conscientes. No hay default=str, evaluación de expresiones,
callbacks de serialización, objetos externos o carga de módulos desde JSON.
Se reusan validaciones de contratos nativos, sobre copias, y se comprueban estado,
versión, pares tipados y objetivos únicos antes de producir salida.

Se rechazan float (también finitos), Decimal, bytes, paths y otros objetos: no
se silencian NaN/Infinity ni se redondean mediciones. Los literales textuales
"NaN"/"Infinity" se conservan como strings, sin declararlos números válidos.
Enteros técnicos admitidos: intervalo exacto interoperable ±(2^53−1).
UTF-8 estricto conserva ceros y formas Unicode originales; un surrogate aislado
se rechaza. JSON escapa controles; no se normaliza ni censura texto científico.

LimitesExportacionQA: **1 MiB por resultado**, 65536 caracteres por texto,
20000 nodos y profundidad 20. Configurables hasta 4 MiB, 65536, 50000 y 24,
respectivamente; valores positivos, bool rechazado. Se controla el recorrido,
texto acumulado y bytes finales UTF-8 incluidos escapes, claves y restricciones.
Codificación incremental en memoria; no se entrega un JSON parcial al exceder
presupuesto. El límite es por resultado, no una autorización de lotes ilimitados.

La API no recibe JSON ni ofrece deserialización a objetos ejecutables. Las
pruebas recuperan estructuras con json.loads y comparan estados, restricciones
y literales; eso demuestra ida/vuelta de representación, no validación de JSON
ajeno ni autorización para usarlo. Un lector contractual de entradas externas,
si se necesita, requerirá diseño y revisión separados.

## Ejemplo exclusivamente sintético

El test usa un descriptor ficticio y un ResultadoQA construido para probar
serialización; no afirma ejecución institucional ni una regla científica aprobada:

```python
import json
from spica.calidad import (
    CategoriaQA, EstadoResultadoQA, ProcedenciaQA, RegistroQA, ReglaQA, ResultadoQA,
)
from spica.calidad.exportacion import ContextoExportacionQA, exportar_resultado_json

entrada = RegistroQA(1, "0007", None, 1, 1, (("MAGNITUD", "001.20"),), True)
regla = ReglaQA("EJEMPLO-001", "1.0.0", CategoriaQA.ESTRUCTURA, "Fixture estructural")
r = ResultadoQA(regla, entrada, ProcedenciaQA(), (("MAGNITUD", "001.20"),), (),
                (("evaluador_nivel0", "1.0.1"),),
                EstadoResultadoQA.COMPROBACION_SATISFECHA, "condicion_ficticia")
c = ContextoExportacionQA("spica:ejemplo", "ensayo-001", "entrada-001")
texto = exportar_resultado_json(r, c)  # Solo memoria.
datos = json.loads(texto)
assert datos["resultado"]["valores_originales"][0][1] == "001.20"
assert datos["restricciones"]["bloqueantes"]  # Satisfecha conserva restricciones.
```

## Compatibilidad, seguridad y pendientes

No cambia asdict, ResultadoQA, InformeQA, el motor, las 22 reglas, restricciones
85-B o consumidores anteriores. No se añaden dependencias. La salida nueva se
solicita explícitamente desde el módulo experimental. No se integran escrituras,
almacenamiento definitivo o sistemas científicos.

Los objetos Python son de confianza cooperativa, no una barrera frente a código
malicioso en el mismo proceso. La función no autentica contexto/configuración ni
prueba que correspondan a la ejecución; no sustituye evidencia de aplicabilidad.
El JSON fiel puede contener metadatos sensibles aportados por el llamador: no se
registra ni publica automáticamente; su futura difusión requiere revisión.
Las excepciones son acotadas y no interpolan valores/rutas originales.

Pendientes para revisión: coordinación del espacio de identidades, detección de
reutilización contradictoria por un consumidor, transporte/persistencia de paquetes
y eventual lector de esquema. Ninguno se implementa operativamente en este paso.
El eventual 85-D debe comenzar por auditoría del contrato y consumidor offline;
no avanzar sin revisión ni activar ciencia.
