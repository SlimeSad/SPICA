# RC5 — Materialización experimental de bytes sintéticos

Inicio **2026-11-15**, cierre documental **2026-11-16**, America/Lima.
Base **1024158**, rama feature/suadc-http,
inicialmente limpia. RC4 está registrado. Versión experimental RC5 **0.1.0**.

## Auditoría previa a la implementación

Se revisaron los tres documentos RC4, los contratos RC1–RC3, los mecanismos RAW,
H/J/K, sus pruebas y la auditoría/hoja de ruta 85-M. RC5 en la hoja de ruta incluye
conservación operativa y custodia; **el encargo actual solo selecciona publicación
y comprobación de bytes sintéticos en TEMP**. No se cierra esa etapa completa.

Clasificación: A directa, B adaptación compatible, C parcial, D ausente, E excluida.

| Capacidad / fuente | Clase | Decisión |
|---|---|---|
| [_huella](../src/spica/adquisicion/almacenamiento/raw.py) | A | Reutilizar tamaño/SHA incremental para recepción y relecturas, sin copiar el bucle de hash |
| _segura y AlmacenRAW._identidad | B | Adaptador interno pequeño: conservar control de ancestros y firma dev/ino/tamaño/mtime; agregar rechazo de reparse points y enlaces duros |
| Publicación RAW/descargas mediante os.link | B | Reutilizar el patrón exclusivo, sin crear AlmacenRAW ni llamar HTTP; no existe una función pública independiente que publique bytes arbitrarios |
| Copia/incorporación RAW | E | Depende de entrada física y catálogo, y atribuye semántica RAW. No convertir preparados/derivados en originales |
| [_destino_seguro](../src/spica/adquisicion/transportes/descargas.py) | C | Referencia de validación de componentes. No importar transporte para abrir una descarga; destinos RC5 se derivan de identidades, sin rutas del llamador |
| [85-J](../herramientas/conservacion_linaje_85j.py) | C | Patrón de raíz TEMP, marcador de escritor y publicación; codec/índice acoplados a G/H, no copiar el conservador |
| [85-K](../herramientas/respaldo_linaje_85k.py) | C | Referencia de firmas antes/después y comprobación posterior al enlace; no importar herramientas desde src |
| [RC4](contrato_artefactos_derivados_rc4.md) | A | Referencias y linaje completos. Añadir informe externo: RC4 continúa inmutable y con evidencia aportada |
| Estados/diagnósticos/restricciones | A | EstadoOperacion para el resultado técnico RC5, EstadoLocal/EstadoIntegridad para comprobación; no cambiar estados de operaciones declaradas |
| Evidencia física de preparados/derivados vinculada a RC4 | D | Informe tipado nuevo, distinto de EvidenciaLocal RAW y de custodia/autenticidad |
| Persistencia J, SQLite 85001, manifiesto K, JSON QA | E | Ningún cambio. Se requiere futuro perfil versionado para conservar estos tipos |

Las dependencias privadas RAW se concentran en un adaptador interno y se prueban
directamente. No se modifica ninguna API histórica ni se duplica almacenamiento
RAW, SQLite, codec, respaldo u orquestación.

## Contratos experimentales 0.1.0

API en [materializacion.py](../src/spica/artefactos/materializacion.py); adaptador
interno en [_archivos_rc5.py](../src/spica/artefactos/_archivos_rc5.py). No se cambia
el __init__.py público RC4. Se importan los símbolos desde el módulo nuevo.

| Contrato | Contenido y responsabilidad |
|---|---|
| LimitesMaterializacion | max_bytes predeterminado 1 MiB, tope 16 MiB; tamano_bloque predeterminado 65536, tope 1 MiB. Enteros positivos, sin bool |
| SolicitudMaterializacion | Inventario RC4, referencia de artefacto/revisión, tamaño esperado, SHA esperado opcional, límites y versión. Recalcula y conserva InformeLinaje; contradicciones impiden construir la solicitud |
| ReferenciaFisica | ID de instancia TEMP, dispositivo/inodo de raíz, proyecto, referencia RC4, contenido_id, huella_vinculo, tamaño y SHA recibido, versión. No acepta una ruta de destino |
| InformeVerificacion | Solicitud y referencia, fecha UTC real, EstadoLocal, bytes leídos, tamaño observado, SHA físico, lectura_completa y diagnósticos. autenticidad_acreditada/custodia_independiente siempre False |
| InformeMaterializacion | Solicitud, fecha UTC, estado_tecnico, estado de publicación, contadores recibidos/escritos, SHA recibido y del temporal releído, referencia, verificación final, temporales y diagnósticos. productor_ejecutado/persistencia_durable siempre False |
| MaterializadorExperimental | Controlador pequeño de recursos TEMP, sin ejecutar métodos productores ni gestionar proyectos. Se obtiene mediante entorno_materializacion |

Las cinco dataclasses son congeladas con slots. La solicitud requiere un
contenido_id explícito y referencia RC4 única. Un linaje PENDIENTE_DE_EVIDENCIA
puede comprobarse físicamente; uno INCOMPATIBLE se detiene antes de escribir.
Se contrastan tamaño/SHA conocidos del descriptor y de comprobaciones aportadas;
no se sustituyen silenciosamente. Los desconocidos no se inventan.

## Identidad y destinos

La raíz es una nueva carpeta plana bajo TEMP: spica-rc5- + UUID hexadecimal.
Se solicita creación exclusiva privada con mode=0o700; no se cambian ACL existentes
ni se inspecciona/autentica una política DACL completa. El ID no es un secreto.
La base viene de TEMP/TMP de Windows, sin la sonda de escritura de gettempdir().
El entorno del proceso es confiable en este modelo; no es un sistema de permisos.
Un lector con otra base TEMP no busca raíces históricas en otras ubicaciones.

Se rechazan base relativa, UNC, traversal, componentes internos Git/configuración,
SPICA_DATOS y una base dentro del repositorio. Se cotejan symlinks, junctions y
FILE_ATTRIBUTE_REPARSE_POINT en ancestros, y dispositivo/inodo de la raíz.

El nombre final es a- + SHA-256 de una clave técnica proyecto/object_id/revisión
con longitudes explícitas + .bin. Ese digest **no es el hash del contenido**.
IDs literales con sintaxis de rutas permanecen metadatos, nunca componentes de
destino. Dos proyectos/objetos con bytes iguales tienen archivos diferentes.
Un destino ocupado se rechaza aunque sus bytes coincidan. No hay deduplicación RAW.
La unicidad lógica se coteja dentro del inventario aportado; este entorno no es
un catálogo global de objetos entre inventarios independientes.

huella_vinculo vincula identidades, revisión, tipo/estado lógico, entrada, recurso
conocido, perfil/versión, método/versión, operación/ejecución declarada, parámetros
y restricciones seleccionadas. No serializa ni autentica el descriptor completo,
no es una firma ni una referencia independiente. El informe conserva la solicitud
completa y su linaje, incluidas incertidumbres/marcos no resumidos en esa huella.

## Procedimiento de publicación

1. Validar solicitud, linaje y restricciones para los usos técnicos exactos
   materializar_sintetico_rc5 y verificar_fisicamente_rc5. Son ámbitos de cotejo,
   nunca permisos efectivos. Un bloqueo conocido de relectura impide publicar.
2. Comprobar cancelación y raíz; crear escritor.lock de forma exclusiva. Un
   marcador previo se conserva y bloquea la operación, sin reparación/reintento.
3. Rechazar destino existente. Abrir un temporal t-UUID.tmp con xb en la misma raíz.
4. Recibir un iterable explícito de bloques bytes no vacíos. EOF se expresa al
   finalizar el iterable. Cada bloque debe respetar la cota configurada; se limita
   el acumulado antes de escribir. Escritura corta es fallo, no éxito.
5. Reutilizar _huella mediante un lector que escribe los bloques: calcula tamaño
   y SHA **recibidos**, solo completos al alcanzar EOF. Cerrar tras flush/fsync.
6. Contrastar tamaño, hash esperado y coherencia con identidades compartidas
   declaradas o ya observadas durante este entorno. No fusionar identidades.
7. Reabrir el temporal y reutilizar _huella por bloques. Contrastar con recepción;
   comparar firmas antes/después y antes de publicación.
8. Publicar mediante os.link exclusivo; registrar únicamente los nombres/inodos
   propios. Retirar el alias temporal propio; no usar replace, rename con
   sobrescritura ni adoptar un destino existente.
9. Reabrir el destino y comprobar nuevamente tamaño, SHA y firmas. Solo una
   verificación final íntegra produce VERIFICADA (publicada_y_releida) y conclusión técnica.
10. Cerrar recursos y liberar únicamente el marcador propio reconocido. Un fallo
    de liberación conserva diagnóstico y evita un resultado técnico concluido.

La fuente de bloques es código cooperativo suministrado por el llamador, sin
expresiones evaluadas desde archivos. El componente no adquiere propiedad de
recursos externos de ese iterable. La condición de contenido sintético es una
obligación del llamador autorizado; no se infiere del contenido ni concede permiso.
Cancelación Event se comprueba entre bloques;
no puede interrumpir por fuerza un next(), lectura o llamada del SO bloqueados.

El filesystem debe admitir enlaces duros. Si falla el enlace, no existe fallback
permisivo ni reintento. La exclusividad evita sobrescribir el nombre final bajo
las garantías del SO; no acredita durabilidad ante corte eléctrico, atomicidad
global, seguridad concurrente absoluta o resistencia total a TOCTOU.

## Estados separados

EstadoPublicacion: NO_PUBLICADA, TEMPORAL, PUBLICADA, VERIFICADA. TEMPORAL significa
no publicado, no necesariamente que todos los bytes estén incompletos: puede
contener una respuesta completa que contradice el tamaño/hash esperado.

estado_tecnico reutiliza EstadoOperacion para **este componente RC5**. CONCLUIDA
solo significa bytes sintéticos publicados y releídos; PARCIAL retiene un prefijo
o una publicación sin cierre; FALLIDA representa fallo sin salida técnica completa;
CANCELADA conserva el estado físico alcanzado. No se asigna ese estado a RC3.

InformeVerificacion reutiliza EstadoLocal: INTEGRO, INCONSISTENTE, AUSENTE y
NO_DISPONIBLE. Su integridad deriva VERIFICADA, FALLIDA o PENDIENTE: solo discrepancia
técnica comprobada de tamaño/hash da FALLIDA. Ausencia, bloqueo, cancelación,
lectura imposible o medición inestable no inventan un fallo de hash.

Descriptor RC4 y su evidencia aportada permanecen iguales. La comprobación RC5
es externa, fechada y real; no confirma RAW, revisión científica, conservación
durable ni conclusión de la operación productora. bool(informes) se rechaza y
autoriza_operacion siempre es False.

## Temporales, interrupciones y límites

Un escritor cooperativo por raíz. Los lectores externos rechazan escritor.lock,
incluido un posible marcador de interrupción. No hay reanudación ni reconciliación
de raíces abandonadas. Los temporales de una operación fallida se conservan para
inspección **durante la vida del entorno**; no se reintenta ni borra para reparar.
KeyboardInterrupt/SystemExit propagan su excepción con informe_rc5 adjunto.

Al salir del entorno se comprueban raíz, archivos/inodos propios y sus enlaces,
y se retiran solo esos nombres; luego se elimina la carpeta vacía. Sin recursión.
Archivos ajenos, directorios, enlaces ajenos o sustituciones detienen la limpieza
y preservan la raíz. Un error de limpieza no enmascara una interrupción activa.
Esto es disposición explícita de fixtures TEMP, no borrado de originales RAW.

Hasta 128 nombres propios por entorno; memoria de lectura/escritura incremental,
sin cargar archivos completos para su hash. La memoria ya usada por el iterable
del llamador queda fuera de esa cota. No hay reserva de espacio, cuotas globales
de CPU/RAM/disco, plazo forzoso o gestión durable. Errores de disco se diagnostican;
fsync no es una prueba de resistencia del hardware.

Véanse [verificación y piloto](verificacion_fisica_artefactos_rc5.md) y
[auditoría](auditoria_arquitectonica_rc5.md).
