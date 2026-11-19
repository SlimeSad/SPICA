# RC8 — Piloto sintético de exportación técnica

Fecha: 2026-11-19, America/Lima. [Contrato](contrato_cierre_tecnico_noqa_rc8.md),
[auditoría](auditoria_arquitectonica_rc8.md),
[pruebas](../tests/test_cierre_exportacion_rc8.py).

## Ejecución real

El fabricante de pruebas reutiliza evaluar_registro existente para generar un
ResultadoQA L0-EST-001 sobre una fila ficticia de 16 campos. No hay lectura del
CSV PNDA, ni InformeQA/CierreQA construido para simular un lote completo.
Su vínculo RC1 conserva procedencia, valores y contexto; la operación fuente QA
sigue INICIADA, sin atribuirle un cierre que este ensayo no acredita.

La entrada lógica de la exportación es resultado-qa-fuente, un resultado nativo
aportado. Su salida lógica es salida-exportacion, un PREPARADO application/json
con revisión r1; no un activo RAW. Los perfiles RC2 son exclusivamente técnicos.
La composición contiene exportar y un consumidor hipotético dependiente.

El piloto invoca realmente spica.calidad.exportacion.exportar_resultado_json
0.1.0 mediante ejecutar_exportacion_tecnica. La prueba con wraps verifica una
llamada explícita y los argumentos nativos; ningún cuerpo esperado se introduce
manualmente como salida de la función. La comparación posterior del consumidor
incluye su contraste de codificación, sin una nueva operación o evaluación QA.

Evidencia de la variante base reproducible, obtenida de la salida real en memoria:

| Propiedad | Resultado |
|---|---|
| Proyecto / contexto | proyecto-RC8 / contexto-RC8 |
| Operación exportadora | exportar |
| Snapshot de inventario | INICIADA, permanece intacto |
| Snapshot observado tras retorno | CONCLUIDA |
| Tamaño UTF-8 generado | 3852 bytes |
| SHA-256 de esos bytes en memoria | 8a9ed4f6977f1c25c2d230589666947fcca6bf50d7c3b2fff4ecc9a4c606eb07 |
| resultado_id JSON nativo | qa0-734e241e0153c936862cd3ec0c902f0788bd4186b5616418368be52a200f470a |
| Consumo nativo | CONTRATO_VALIDO_EN_ALCANCE |
| Cierre técnico específico | Comprobado dentro del proceso cooperativo |
| Habilitadas RC3 | Ninguna; consumidor pendiente |

El ID JSON identifica el diagnóstico QA contextual; no se renombra como ID de la
operación exportadora o de una observación científica nueva. La referencia RC4 y
la captura relacionan la salida con esa exportación sin cambiar JSON QA 0.1.0.
HORA=10000 y UBIGEO=01234.0 se preservan literalmente. No se reconstruyen estaciones,
tiempo, unidades o datos faltantes. La salida de otro resultado, aunque sea JSON
nativo válido, se rechaza por no corresponder al argumento que se debe exportar.

## Archivo y recuperación

Las pruebas entregan los bytes generados a materializar_sintetico de RC5 en dos
bloques. Comprueban igualdad byte por byte, tamaño/hash e integridad mediante
verificar_fisicamente. La huella en memoria y la lectura física son evidencias
distintas; InformeCierreExportacion declara comprobacion_fisica_realizada=False.

Se prueban pérdida y corrupción de esa copia TEMP y se observa el estado físico
no íntegro. La captura no se convierte en garantía de lectura posterior. La
publicación repetida conserva el archivo previo e impide sobrescribirlo.

RC6 conserva el inventario sin modificar sus snapshots y la salida materializada;
la entrada QA lógica se declara externa, sin inventar un archivo suyo. La
recuperación real comprueba la copia JSON. RC7 reconstruye las asociaciones y
mantiene el consumidor pendiente. No se conserva ni simula la captura RC8 en RC6.
Todos los archivos de estas pruebas pertenecen a TEMP privados y se disponen
mediante los contextos existentes, sin tocar almacenamiento permanente.

## Casos adversariales

Se ensayan entrada, proyecto, operación, productor, versión, salida y perfiles
incompatibles; resultado de otra entrada; captura externa o alterada; hash/tamaño
incorrectos; ausencia de resultado; linaje contradictorio; restricciones omitidas
del contexto o heredadas; límites; fallo; cancelación y estado parcial.

La cancelación antes de llamar no ejecuta el productor. Una interrupción dentro
de la llamada no aporta salida completa. Event después del retorno conserva el
JSON, pero deja PARCIAL el cierre. Un estado terminal aportado no se reabre.
Excepciones con mensajes sensibles solo producen códigos sanitizados.

Dos proyectos MD distintos generan intencionalmente los mismos bytes al usar
espacios contextuales nominales iguales en inventarios separados: el JSON no
incluye el project_id MD. Se conserva esa limitación de identidad declarada,
sin afirmar unicidad global. Las capturas retienen proyectos distintos y se
rechaza intercambiarlas, aunque coincidan SHA, tamaño y resultado_id JSON.

Las barreras de pruebas niegan sockets, SQLite y apertura de archivos durante
la exportación en memoria y su cotejo. La inspección no despacha la operación
exportadora ni evalúa QA. Los informes y diagnósticos son deterministas.

Resultados finales: 448 pruebas dirigidas aprobadas (38 RC8 + 410 RC1–RC7),
2332 en la única suite completa final (2294 anteriores + 38 nuevas), sin fallos,
errores u omisiones. pip check no encontró incompatibilidades. No quedaron
directorios TEMP RC3/RC5/RC6 o .suadc-test-*; no se necesitó limpieza correctiva.
La auditoría conserva comandos, tiempos y registro. No se usan conteos AST como
aprobación de pruebas, autenticidad o conformidad científica.
