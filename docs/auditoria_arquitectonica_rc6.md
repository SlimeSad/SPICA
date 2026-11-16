# RC6 — Auditoría de conservación experimental

Fecha de elaboración: 2026-11-16, America/Lima. Base inicial
27a9224b043d36fe7e414e14782b543de6f65614, feature/suadc-http, árbol limpio.
RC5 está registrado. No se realizan commits.

## Decisión previa al código

Se revisaron los tres documentos RC5, las recomendaciones RC4, contratos
RC1–RC4, materializador RC5, codec/índice/recuperación 85-J, respaldo 85-K,
amenazas/portabilidad 85-L y hoja de ruta 85-M. El siguiente perfil versionado
recomendado por RC5 coincide con el encargo. La etiqueta RC6 de la hoja 85-M
designaba medición/mantenimiento; el encargo vigente selecciona explícitamente
conservación experimental. No se interpreta como cierre de esa hoja ni como
autorización operativa. No existe contradicción crítica que obligue a romper APIs.

A: reutilización directa; B: adaptador pequeño; C: extensión versionada;
D: contrato incompatible para este uso; E: fuera de alcance.

| Necesidad | Clase / mecanismo | Decisión |
|---|---|---|
| Descriptor, identidad/revisión, contenido y linaje RC4 | A | Conservar el inventario tipado y recalcular inspeccionar_linaje; conservar restricciones y diagnósticos resultantes para cotejo |
| Contextos RC1, perfiles RC2 y composición RC3 | A | Mantener instantáneas del perfil admitido y referencias compartidas, sin ejecutar operaciones |
| Evidencia física RC5 | A/B | Conservar informes históricos; verificar nuevamente antes de copiar; separar comprobación de la copia y referencias externas |
| SHA/tamaño/rutas | A/B | Reutilizar huella, firma, segura y base_temporal del adaptador RC5; adaptador plano limitado a la generación |
| Codec 85-J | D/C | Lista cerrada G/H, sin RC4/RC5 ni identidad compartida de objetos RC3. Nuevo perfil explícito RC6; no alterar ese codec |
| Índice SQLite 85001 | D/E | Cuatro roles G/H y DDL exacto. No añadir tablas ni otro catálogo SQL |
| Manifiesto/respaldo 85-K | D/B | Su formato queda intacto. Reutilizar patrón de copia por bloques, enlace exclusivo y relectura; no importar herramientas desde src |
| Identidad y cierre de generación | C | Manifiesto y sello propios, versionados, limitados a TEMP; sin servicio general de almacenamiento |
| Portabilidad 85-L L03 | B/C | Nombres relativos generados; las referencias RC5 históricas son inertes durante recuperación. Otra raíz TEMP del mismo equipo no es custodia independiente |
| Almacenamiento operativo, exportación científica, permisos y autenticidad | E | No implementados ni habilitados |

Los contratos públicos históricos, JSON QA 0.1.0, índice 85001 y manifiesto K
permanecen intactos. Una generación RC6 no se presenta como generación J/K.
La recuperación solo reconstruye el perfil efectivamente conservado; no abre
localizadores documentales ni archivos externos para completar información.

## Verificaciones y cierre

Se agregan siete archivos y se mantiene intacto todo archivo anterior:

| Archivo | Responsabilidad |
|---|---|
| [conservacion.py](../src/spica/artefactos/conservacion.py) | Unidad/control/informe tipados, publicación, recuperación y copia de generación |
| [_codec_rc6.py](../src/spica/artefactos/_codec_rc6.py) | Perfil de serialización cerrado, determinista y con referencias compartidas |
| [_generacion_rc6.py](../src/spica/artefactos/_generacion_rc6.py) | Adaptador de primitivas RC5 para archivos planos de generación |
| [test_conservacion_rc6.py](../tests/test_conservacion_rc6.py) | 60 ensayos funcionales/adversariales, productor y lector en procesos separados |
| [conservacion_versionada_artefactos_rc6.md](conservacion_versionada_artefactos_rc6.md) | Contrato, formato, inventario, publicación y seguridad |
| [recuperacion_linaje_artefactos_rc6.md](recuperacion_linaje_artefactos_rc6.md) | Recuperación, traslado, estados, evidencia y limitaciones |
| auditoria_arquitectonica_rc6.md | Este informe |

La dependencia nueva es conservacion → codec/generacion → materializacion RC5 y
contratos RC1–RC4; adaptador RC5 → primitivas RAW. No hay imports inversos desde
módulos previos ni ciclos que involucren RC6. No se importan herramientas/tests
desde src. No se modifican dependencias, main.py, .gitignore ni .venv.
Los tres archivos de código suman 842 líneas; no incluyen otro índice SQLite,
motor de ejecución, almacén RAW ni algoritmo de hash de cuerpos alternativo.
Las adaptaciones físicas reutilizan las primitivas RC5; la copia es el patrón
de K acotado a los nombres/versiones de este perfil.

## Decisiones y hallazgos

| Hallazgo / decisión | Gravedad y tratamiento |
|---|---|
| Codec J e índice 85001 no admiten RC4/RC5 | Incompatibilidad de alcance documentada antes de crear código; perfil RC6 independiente, sin romper lectores ni migrar |
| Identidad compartida RC1–RC3 necesaria en RC4 | Se conserva con tabla de referencias; una serialización por valor que reconstruyera copias iguales perdería los cotejos canónicos |
| Alcance de recuperación semántica | Perfil descriptivo completo, sin cierres QA/registros; tipos no admitidos se rechazan, sin pérdida silenciosa |
| Fuente externa con evidencia histórica íntegra | Se conserva como historia; comprobación actual NO_DISPONIBLE. No abre un activo operativo o raíz RC5 histórica |
| Informe RC5 parcial y contenido incompleto | Puede conservarse como historia externa; no se copia su temporal ni se finge archivo incluido verificado |
| Windows/TEMP, autenticidad y custodia | Restricciones vigentes: entorno cooperativo, no ACL acreditadas, misma cuenta/equipo, sin referencia protegida ni durabilidad eléctrica |

No se detectó necesidad de romper contratos estables ni bloqueo crítico que
exigiera acceder a información operativa. Los límites son requisitos explícitos
del perfil experimental, no capacidades implementadas de una plataforma general.

La primera pasada RC6 ejecutó 49 pruebas, todas aprobadas. La revisión añadió
coherencia de evidencias aun si son externas, tipos estrictos, límites de contadores,
ciclos/revisiones/resultados inexistentes, mutaciones y rechazo de enlaces.
Se comprobó que el lector no confunde False con tamaño 0 en JSON. La última
revisión normalizó el rechazo de un Decimal malformado y comprobó conservación
de fechas civiles/UTC y representación decimal sin conversiones.

## Pruebas y entorno

Intérprete .venv: Python **3.15.1**, HTTPX **0.28.1**, SQLite **3.53.4**.
No se instalaron paquetes. PYTHONPATH se ajusta solo en el proceso:

```powershell
$env:PYTHONPATH = (Join-Path $PWD 'src') + ';' + (Join-Path $PWD 'tests') + ';' + $PWD.Path
$env:PYTHONDONTWRITEBYTECODE = '1'
.\.venv\Scripts\python.exe -B -m unittest test_conservacion_rc6 test_materializacion_rc5 test_artefactos_rc4 test_contextos_rc1 test_perfiles_informacion_rc2 test_coordinacion_rc3 -q
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -B -m pip check
git diff --check
git status --short
```

Dirigidas finales, código 0:

```text
Ran 366 tests in 54.719s

OK
```

**366 aprobadas, 0 fallidas, 0 errores** = 60 RC6 + 56 RC5 + 52 RC4 +
60 RC1 + 79 RC2 + 59 RC3. No se suman pasadas como pruebas adicionales.
Los ensayos usan exclusivamente fixtures sintéticas TEMP. Se ejecuta Python fuera
del sandbox por los permisos privados Windows de esas carpetas, sin cambiar ACL
ni autorizar red. El lector nuevo independiente instala una barrera antes de
importar SPICA que prohíbe escritura, sockets, SQLite y acceso a SPICA_DATOS.

El productor A finaliza normalmente; B reconstruye mediante el lector real,
sin importar factories. El traslado copia la generación a una raíz nueva y se
retira únicamente la fuente creada por nuestra prueba. Otro B confirma los mismos
IDs, estados, restricciones y SHA, sin raíz productora/RC5 disponible. Los hashes
y contenidos son los indicados en el informe de recuperación. No se ensaya otro
equipo/cuenta/SO ni un dominio de fallo independiente.

La única suite completa final se inició después de cerrar código y pruebas.
Durante su ejecución solo se completa documentación y verificaciones de lectura.
Resultado de la **única suite completa final**, código de salida 0:

```text
Ran 2250 tests in 980.679s

OK
```

**2250 aprobadas, 0 fallidas, 0 errores y 0 omitidas**: las 2190 anteriores y
60 nuevas. Desde su inicio no se modificó código ni pruebas, solo documentación.
Incluye los ensayos históricos H/J/K y sus lectores/formatos sin cambios.
Registro fuera de Git:
`%TEMP%/spica-rc6-suite-7f37f21e699e42e2948f0daac8b1bc1b.log`.

pip check: **No broken requirements found.** Compilación/AST sin bytecode de los
cuatro Python nuevos: sintaxis, definiciones y espacios correctos. Las versiones
se cotejan en constructores/codec; ningún lector anterior se modifica.
Los tres Markdown tienen **19 enlaces locales existentes**, UTF-8, salto final,
cercos y espacios correctos. Se revisan directamente los siete archivos nuevos
porque git diff --check no incluye archivos sin seguimiento. Comprobación final:
**0 raíces TEMP RC6, 0 RC5, 0 CSV RC3 y 0 directorios .suadc-test-* en el repositorio**.
No se necesitó limpieza correctiva manual ni borrado recursivo.

Git final: feature/suadc-http, HEAD
**27a9224b043d36fe7e414e14782b543de6f65614**, sin cambios de índice ni de archivos
anteriores. git diff --check y git diff --name-only HEAD: sin salida, código 0.
git status --short:

```text
?? docs/auditoria_arquitectonica_rc6.md
?? docs/conservacion_versionada_artefactos_rc6.md
?? docs/recuperacion_linaje_artefactos_rc6.md
?? src/spica/artefactos/_codec_rc6.py
?? src/spica/artefactos/_generacion_rc6.py
?? src/spica/artefactos/conservacion.py
?? tests/test_conservacion_rc6.py
```

Son siete archivos nuevos pendientes de revisión; no se añade nada al índice ni
se ejecutan commits/push. Los contratos/documentos previos permanecen intactos.

## Arquitectura integral, restricciones y pendientes

Se conservan las definiciones originales de las matrices
[85-F](matriz_dependencias_integracion_paso85f.md) y
[85-M](matriz_diseno_implementacion_paso85m.md), sin cambiar su estado:

| Conexión original | Estado tras RC6 |
|---|---|
| M03 C08 → C09/C02, ejecutor PlanConsulta y traducción institucional de selectores a HTTP con mecanismo/presupuesto/autorización | **P**, no implementado por esta generación |
| M16 C12 → C02/C11, decisión de readquisición → GET/ingesta mediante hook/ejecutor aprobado | **P**, recomendar no activa efectos |
| M26 C20 → C21/C24/C19, evidencia documental → QA/aplicabilidad/operación mediante vínculo revisado | **P**, hashes y codec no aprueban ciencia |
| M32 resultados futuros → almacenamiento/exportación científica, derivados y linaje | **P**, avance parcial RC4/RC5/RC6 de contratos y conservación descriptiva sintética. Faltan perfil operativo/exportación científica y ejecución pertinente; no se cierra la conexión original |

Las [29 brechas PNDA](brechas_reconciliadas_pnda_paso84i.md) siguen: 2
RESUELTA_CON_EVIDENCIA, 17 PARCIALMENTE_DOCUMENTADA, 8 PENDIENTE_DE_EVIDENCIA,
2 CONTRADICCIÓN_DOCUMENTADA. No se abre el CSV ni evidencia institucional privada;
no se modifica ese expediente ni se resuelve una brecha por esta implementación.
INGEMMET /query permanece NO AUTORIZADO.

Cero conexiones externas, GET, descargas, instalaciones, migraciones o escritura
operativa. No se abre RAW/staging/SQLite operativo para volver a calcular un hash
real o comprobar su conservación: se informa ausencia de acceso, sin inventar una
auditoría física nueva de los originales permanentes. Los ensayos antiguos de la
suite mantienen sus fixtures históricas; no se cambia su código ni su alcance.

Riesgos residuales: retención TEMP, SO/filesystem con enlaces duros, confianza en
proceso/entorno/control aportados, ventanas TOCTOU, concurrencia solo cooperativa,
ausencia de referencia protegida/custodia independiente, límites locales sin
reserva de espacio/RSS/CPU, formato de perfil cerrado y reloj local. La lectura
detecta cambios observados, sin prometer resistencia a manipulación coordinada.
No hay migración, reparación/reanudación automática, atomicidad global, resistencia
eléctrica o recuperación integral de contenido externo.

El siguiente incremento recomendado, tras auditoría, es revisar el perfil de
conservación contra los consumidores realmente necesarios y acordar política de
retención/control protegido y compatibilidad de recuperación antes de cualquier
destino operativo o datos únicos. No requiere introducir un segundo catálogo,
cloud, firma o núcleo científico por inercia. RC6 no autoriza esas funciones.

Dictamen definitivo: **APTO CON RESTRICCIONES** para conservación/recuperación
versionada del perfil descriptivo sintético TEMP. No quedan correcciones
obligatorias conocidas dentro de ese alcance tras las verificaciones. No habilita
datos únicos operativos, custodia independiente, instituciones o ciencia.
No se inicia RC7 ni se declara terminada la arquitectura integral. El incremento
queda pendiente de auditoría del equipo, sin atribuir esa aprobación por el total
de pruebas ni por este dictamen técnico.
