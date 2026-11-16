# RC6 — Conservación versionada de artefactos sintéticos

Fecha: 2026-11-16, America/Lima. Base: 27a9224, feature/suadc-http.
Formato **rc6.generacion.0.1.0**, distinto de 85-J/K aunque estos usen 0.1.0.
[Auditoría y reutilización](auditoria_arquitectonica_rc6.md),
[recuperación y pruebas](recuperacion_linaje_artefactos_rc6.md).

## Perfil admitido y frontera

Se conservan inventarios [RC4](contrato_artefactos_derivados_rc4.md), contextos
RC1, perfiles RC2, composiciones RC3 e informes históricos
[RC5](materializacion_experimental_rc5.md). Las instantáneas del perfil admitido
son completas, compartiendo referencias de objetos; no se guardan únicamente sus
nombres. El linaje y sus restricciones se recalculan con el inspector existente.

Perfil inicial: operaciones DESCRIPCION_ESTRUCTURAL, sin CierreQA ni registros
QA en las composiciones. Otras clases/zonas datetime con objetos de zona nombrada
son rechazadas explícitamente; no se eliminan campos para hacerlas encajar.
QA Nivel 0, JSON QA 0.1.0, resultados científicos, codecs J/K y lectores previos
permanecen intactos. La recuperación semántica se limita a este perfil.

Todos los cuerpos son sintéticos pequeños, suministrados explícitamente por el
llamador cooperativo. El componente no puede autenticar esa condición. No lee
archivos institucionales ni se conecta a HTTP/SQLite. No se instancia AlmacenRAW.
No es un almacén operativo de derivados ni un exportador científico.

## API y responsabilidades

API en [conservacion.py](../src/spica/artefactos/conservacion.py), importada
explícitamente, sin modificar el __init__.py histórico de RC4.

| Contrato | Función |
|---|---|
| UnidadConservacion | Inventario RC4, informes RC5 y referencias externas explícitas; clausura de linaje calculada una vez |
| ControlGeneracion | generacion_id y manifiesto_sha256, ambos obligatorios; referencia suministrada, sin autoridad independiente |
| ComprobacionContenido | Referencia RC4, contenido_id, nombre relativo o None, estado actual, tamaño/SHA realmente comprobados y lectura_completa |
| RecuperacionGeneracion | Estado actual del conjunto, fecha UTC, control, unidad recuperada cuando esté disponible, comprobaciones y diagnósticos |
| entorno_conservacion | Crea una raíz TEMP exclusiva; disposición por defecto al salir, limitada a nombres/inodos propios |
| ConservadorExperimental.conservar | Verifica el perfil y orígenes RC5, copia por bloques y publica un cierre nuevo |
| ConservadorExperimental.copiar_de | Copia una generación cerrada y verificable a otra raíz nueva, conservando su identidad/control |
| recuperar_generacion | Lectura independiente, sin escrituras ni resolución de orígenes históricos |

Las dataclasses nuevas son congeladas con slots. El informe rechaza bool();
autoriza_operacion, autenticidad_acreditada, custodia_independiente y
persistencia_durable permanecen False. Un control/hash autoconsistente no prueba
autoría institucional ni resistencia a una sustitución coordinada del conjunto.

## Identidades e inventario

Cada descriptor mantiene proyecto/contexto, object_id, revisión literal, tipo
ORIGINAL/PREPARADO/DERIVADO, contenido_id, entrada, perfil/versión, recurso y
procedencias originales, incertidumbres, diagnósticos y restricciones.
Las operaciones mantienen identidad, método/versión, parámetros, referencias
de ejecución, estados y relaciones N→M. No se crea relación por un nombre o SHA.

Dos proyectos/objetos con contenido igual permanecen dos entradas y dos copias
de inodos distintos. Coincidir en SHA no deduplica ni fusiona identidades. Las
contradicciones de contenido entre declaraciones conocidas y evidencias físicas
incluidas bloquean el cierre. La unicidad corresponde al inventario, no a un
registro global entre generaciones independientes.

Todos los descriptores deben tener cobertura explícita: copia incluida procedente
de un informe RC5 coherente CONCLUIDA/VERIFICADA, o referencia externa. Un informe
fallido/parcial/cancelado puede conservarse como historia si su artefacto se marca
externo; sus temporales históricos no se copian ni se abren. Un informe histórico
contradictorio no se acepta por marcarlo externo.

Una generación solo de referencias externas puede estar cerrada **en ese alcance**.
Sus cuatro comprobaciones, por ejemplo, indicarán NO_DISPONIBLE, nombre/tamaño/hash
actuales None y lectura_completa=False. No significa que el contenido esté presente
o que se haya comprobado su ausencia. Los informes antiguos siguen siendo historia.

## Representación y archivos

Raíz plana: TEMP/spica-rc6-UUID hexadecimal. El ID de esa raíz física es distinto
del generacion_id lógico. Una copia en otra raíz conserva el segundo.

| Archivo | Contenido |
|---|---|
| intencion.json | Formato, identidad, fecha UTC de creación y estado preparada, inmutable |
| datos-000.bin, datos-001.bin… | Copias independientes, por posición explícita del inventario físico |
| metadatos.json | Grafo tipado: inventario, informes RC5, referencias externas y resumen del linaje/restricciones/diagnósticos |
| manifiesto.json | Formato, identidad, fecha, estado cerrada_en_alcance, tamaño/SHA de metadatos, inventario físico y externos |
| cierre.json | Formato, identidad, SHA del manifiesto y estado de cierre |
| escritor.lock / t-UUID.tmp | Preparación o interrupción; impiden declarar recuperación verificada |

El manifiesto asocia cada copia con object_id/revisión/contenido_id/tamaño/SHA.
El lector regenera los nombres relativos desde el inventario tipado, coteja la
igualdad exacta y no abre una ruta proporcionada por el JSON. No se guardan rutas
absolutas de conservación; las referencias RC5 históricas, locales documentales y
storage_ref declarados no se usan para E/S durante recuperación.

[_codec_rc6.py](../src/spica/artefactos/_codec_rc6.py) usa JSON UTF-8 determinista:
claves ordenadas, separadores sin espacios, ensure_ascii=False, allow_nan=False,
sin salto añadido. No pretende ser el estándar JCS ni normalizar Unicode.
Rechaza claves duplicadas, no finitos, campos desconocidos/faltantes, tipos
incorrectos (bool no es int), clases y versiones fuera de lista y registros ocultos.

Una tabla de objetos con referencias enteras conserva identidad compartida de
las instantáneas RC1–RC3, necesaria para los cotejos is de RC4. No permite ciclos
de construcción. No importa clases elegidas por el documento ni usa pickle/eval.
El tipo de cada campo se coteja con anotaciones del código confiable registrado.
Fechas civiles, offsets y Decimal finitos permanecen literales, sin conversiones.
Solo SolicitudMaterializacion.linaje se omite de esa tabla: se recalcula por el
constructor RC5 y se compara con la clausura guardada. Constantes init=False,
versiones y revisión científica se preservan y contrastan.

## Publicación y fallo

1. Cotejar unidad, límites, restricciones de conservar_sintetico_rc6 y
   recuperar_sintetico_rc6, perfil del codec y tamaño de metadatos antes de escribir.
2. Exigir raíz propia vacía; crear escritor.lock exclusivo. No adoptar/reintentar
   una raíz ocupada, ni siquiera si contiene los mismos bytes.
3. Publicar intención. Revalidar cada origen con verificar_fisicamente RC5,
   incluyendo sus restricciones. Copiar el archivo por bloques a un temporal propio,
   cotejando firmas antes/después y tamaño/SHA con la evidencia esperada.
4. flush/fsync/cierre, lectura física del temporal, enlace duro exclusivo al nombre
   final, retirar únicamente el alias propio y relectura física del destino.
   Nunca enlazar directamente el inode del origen; nunca usar replace o fallback.
5. Publicar metadatos y manifiesto con el mismo patrón; sello al final. Liberar
   únicamente el marcador propio reconocido. Recuperar mediante el lector público.
6. Devolver éxito solo si el conjunto se verifica. Cualquier excepción/interrupción
   preserva el estado alcanzado dentro de la vida de la raíz, sin reparar/reanudar.

No hay transacción global archivos+metadatos, fsync portable de directorio ni
garantía frente a pérdida eléctrica. El filesystem debe admitir enlaces duros;
si no los admite, se detiene. Los puntos de fallo de prueba son métodos inertes
del código, nunca expresiones/callbacks cargados desde documentos.

## Seguridad, recursos y disposición

[_generacion_rc6.py](../src/spica/artefactos/_generacion_rc6.py) adapta ArchivosTEMP
RC5: base ambiental validada sin sondeo de escritura, rutas/ancestros sin symlink,
junction o reparse points, identidad dev/ino, archivos regulares sin enlaces duros
adicionales, publicación exclusiva y disposición no recursiva de nombres propios.
No modifica ACL. mode=0700 no equivale a una auditoría DACL en Windows.

Límites fijos del perfil: 16 descriptores/informes/externos, 16 MiB por copia,
64 MiB acumulados de contenido, bloque 65536 bytes, 2 MiB por metadato leído,
50000 nodos del codec/JSON, profundidad 64 y hasta 80 nombres inspeccionados.
La infraestructura RC5 limita 128 nombres propios incluyendo preparación.
Solo metadatos acotados entran completos en RAM; cuerpos se leen/escriben por
bloques y jamás se acumulan para el hash. No son reserva de disco/RSS ni SLA.

Un escritor cooperativo por raíz. Event permite cancelación entre bloques/pasos;
no interrumpe llamadas del SO bloqueadas. Errores usan códigos fijos sin rutas o
credenciales. No se sanitizan silenciosamente metadatos: el llamador debe aportar
solo información pública/sintética adecuada; el formato no aporta confidencialidad.

entorno_conservacion(disponer_al_salir=False) retiene explícitamente la raíz TEMP
también ante excepción, para un lector posterior. No equivale a custodia durable.
La disposición predeterminada retira únicamente archivos propios comprobados,
después el directorio vacío; nombres/inodos/enlaces ajenos detienen la limpieza.
No borra para reparar ni cambia permisos. La retención necesita un responsable de
disposición de fixtures, y no debe utilizarse para conservar información única real.
