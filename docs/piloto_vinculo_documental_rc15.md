# RC15 — Piloto de vínculo documental C20 → C24

Fecha: **2026-11-23**, America/Lima. Base `2cfb3a4`.
[Contrato](contrato_vinculo_documental_rc15.md),
[auditoría y resultados finales](auditoria_arquitectonica_rc15.md).

## Escenario reproducible y producto

[test_vinculo_documental_rc15.py](../tests/test_vinculo_documental_rc15.py)
construye el escenario con contratos nativos y fabricantes existentes, importando
solo funciones de fixtures, sin importar TestCase anteriores ni sumar sus pruebas
de nuevo. No se ejecuta el conector institucional, HTTP, lectura del CSV o RAW.

El producto elegido es el **producto catalogado SENAMHI–PNDA GBON/RBON** ya
soportado. Su fuente/ID se toman de constantes del conector existente. Todo el
documento, recurso descrito, proyecto, edición y revisión del ensayo son
sintéticos: no acreditan documentación actual de SENAMHI ni una edición real.

| Identidad / contrato | Valor o condición del ensayo |
|---|---|
| Fuente y producto | FUENTE_SENAMHI / PRODUCTO_GBON_RBON_ID, sin normalización |
| Proyecto A / contexto | proyecto-rc15-A / contexto-proyecto-rc15-A |
| Proyecto B / contexto | proyecto-rc15-B / contexto-proyecto-rc15-B; mismos bytes documentales, revisión distinta |
| Recurso | urn:fixture:recurso-catalogado-rc15, referencia inventada, no endpoint |
| Edición de producto | edicion-ficticia-rc15, declarada solo en el mundo de la fixture |
| Objeto/revisión | objeto-{project_id} / descripcion-1, MD-02 y ContextoEntrada nativos |
| Artefacto | PREPARADO, DESCRITO, contenido descripcion-catalogo-fixture-rc15; descripción de catálogo, no original RAW |
| Perfil | perfil-producto-rc15 / r1; tipo producto_catalogado, sin valores de observaciones |
| Operación | revision-documental-rc15, DESCRIPCION_ESTRUCTURAL, DECLARADA |
| Finalidad | revision_documental_identidad_producto_pnda |
| Documento | doc-sintetico-rc15, emisor-ficticio-no-SENAMHI, DOCX generado con fabricantes OOXML existentes |
| Edición/fecha documental | doc-edicion-fixture / 2000-01-01, datos expresamente inventados |
| Afirmación | identidad-producto; concepto identificador_producto, ámbito igual a la finalidad, literal exacto del ID |
| Localizador | ReferenciaDOCX nativa a word/document.xml, primer párrafo directo del cuerpo |
| Control | control-rc15, referencia completa, tamaño y SHA del documento fijados antes del cotejo |
| Revisión | Referencia de responsable ficticia, ProcedenciaCatalogo sintética de 2026-11-23 UTC y solicitud completa |
| Restricciones | Informativa de fixture heredada del proyecto; variantes con bloqueo exacto de finalidad |

Los bytes se generan en memoria y se escriben exclusivamente en un directorio
`spica-rc15-*` de TEMP. El cotejador existente lee ese archivo, calcula tamaño/SHA,
inspecciona DOCX y verifica su conservación final. No se crea un activo MD-03 ni
un catálogo operativo. Los contextos comprueban la eliminación del TEMP propio.

Se ejecutó también el escenario completo de ambos proyectos fuera del contador
unittest. En ambos: DOCX de **1308 bytes**, SHA-256 físico
`1cf89bc7bec857ad3da26213a6c87d00924762780981a3cb1839bafe2e21d1a9`,
estado APTO_ESTRUCTURALMENTE y una afirmación PRODUCTO DECLARADA. Se cotejó el
hash del informe con una lectura física del archivo sintético y se comprobó su
limpieza al salir de cada contexto. Las restricciones conservan los orígenes
artefacto_rc15 y operacion_rc15; la operación permanece DECLARADA. La igualdad de
bytes no permite cruzar revisiones entre proyectos, como verifica el caso adverso.

## Secuencia efectivamente ensayada

1. Construcción de la descripción del producto en RC1/RC2/RC4 y del expediente
   C20; no ejecución de una producción institucional.
2. Construcción explícita de la revisión sintética ligada a ese snapshot.
3. Evaluación documental nativa CONSULTA_DOCUMENTAL y cotejos de identidad/uso.
4. Nuevo CotejadorDocumental.cotejar sobre el DOCX controlado; una prueba espía
   comprueba su invocación real, sin reemplazar el algoritmo por un éxito falso.
5. Preparación de ExpedienteProducto y AfirmacionAplicabilidad nativos C24,
   dimensión PRODUCTO, nivel DECLARADA y pendientes de revisión conservados.
6. Inspección del resultado, flags y restricciones; operación sigue DECLARADA,
   sin ejecución o aprobación científica. Limpieza comprobada del TEMP propio.

No hay un método científico o regla con umbrales seleccionado. El resultado
positivo prueba el traspaso contractual de una identidad revisada en la fixture;
no prueba aplicabilidad científica al producto meteorológico real.

## Casos y resultados

| Caso ensayado | Resultado real esperado/comprobado por las pruebas finales |
|---|---|
| Coherente, revisión explícita, DOCX disponible, literal/control correctos | APTO_ESTRUCTURALMENTE; salida nativa DECLARADA, no aprobación |
| Producto inexistente/ajeno o identidad de recurso contradictoria | INCOMPATIBLE; sin salida |
| Otro proyecto o copia no canónica de la entrada | INCOMPATIBLE; no se comparte revisión por tener el mismo SHA |
| Finalidad, versión de contrato o propósito de operación distintos | INCOMPATIBLE, antes de leer el documento |
| Revisión ausente | PENDIENTE_DE_EVIDENCIA; sin cotejo o salida |
| Revisión de otro snapshot | INCOMPATIBLE; no se reutiliza la revisión anterior |
| Expediente, afirmación o control ausentes | PENDIENTE_DE_EVIDENCIA; sin salida |
| Archivo ausente | PENDIENTE_DE_EVIDENCIA, sin SHA calculado; no declara corrupción |
| Edición de producto/documento conocida distinta | INCOMPATIBLE |
| Producto o edición desconocidos | PENDIENTE_DE_EVIDENCIA, sin inventar una contradicción |
| Referencia alterada con el mismo ID/hash, pero otro título/edición | INCOMPATIBLE; comparación de referencia completa |
| DOCX alterado tras un primer resultado coherente | Nuevo cotejo detecta tamaño/hash diferentes; sin nueva salida |
| SHA correcto pero párrafo inexistente | Integridad del documento comprobada contra control; vínculo literal no satisfecho |
| Integridad/inspección aportadas insuficientes o procedencia del recurso ausente | PENDIENTE_DE_EVIDENCIA |
| Restricción exacta heredada del proyecto, local del artefacto o de la operación | INCOMPATIBLE; conserva bloqueo y orígenes |
| Evidencia declarada o clasificada VERIFICADA por el llamador | Ninguna asciende automáticamente la afirmación de salida: DECLARADA |
| Segundo ID apuntando al mismo localizador | INCOMPATIBLE por duplicación; no corroboración independiente |
| Relación contradictoria con una afirmación no seleccionada | INCOMPATIBLE; mantiene diagnóstico nativo y contradicción |
| Artefacto PARCIAL u operación PARCIAL/FALLIDA/CANCELADA | INCOMPATIBLE; sin promover estados |
| Referencia aportada sin autenticidad | Puede preparar relación sintética coherente; autenticidad_institucional=False |
| Vigencia desconocida, pendientes, inferencia o naturaleza DOCUMENTAL real | Sin salida; el piloto solo admite naturaleza SINTETICA |
| Conservación final incompleta | Sin salida; cotejo favorable parcial no compensa el faltante |
| Dos ejecuciones con los mismos hechos | Informes iguales; no cambia contextos ni acumula relaciones |
| 64 incertidumbres originales y restricción documental de derechos | Conserva todas, mantiene pendientes y no inventa licencia/permiso |

La prueba de conservación incierta simula únicamente esa condición negativa del
informe nativo. El positivo utiliza el cotejo físico real. Ninguna ejecución
interrumpida o con errores se cuenta como aprobada en el informe final.
«Producto inexistente» en la prueba significa una identidad ajena al perfil
implementado: no se consulta un catálogo persistido o servicio para demostrar
existencia actual. La existencia nominal del producto seleccionado procede del
código y las referencias históricas del repositorio.

## Barreras y garantías observadas

Dos procesos aislados prueban órdenes directo/inverso de importación. Sus hooks
rechazan eventos socket/SQLite y nuevos subprocesos, lecturas de SPICA_DATOS y
escrituras de archivos fuera de su raíz TEMP. Ambos imprimen
`RC15_TEMP_VERIFICADO_SIN_EFECTOS_OPERATIVOS` tras ejecutar el escenario y
comprobar su limpieza. Otras pruebas añaden mocks de red/SQLite.

La lectura de código/imports es necesaria y permitida por esas barreras; no se
afirma aislamiento de SO o resistencia a un proceso Python malicioso. El
adaptador no abre el producto catalogado, RAW o SQLite, ni sigue URLs documentales.
El control de archivo se aporta explícitamente por el llamador confiable.

La integridad física comprobada corresponde **únicamente al DOCX sintético
controlado en esa lectura**. La procedencia del catálogo, revisión y niveles
documentales son aportados. Los respaldos sintéticos de FuenteDocumental no se
presentan como comprobaciones históricas reales de SENAMHI. No se modifica su
nivel después del cotejo ni se promociona la revisión a aprobación humana real.

La salida es solo una dimensión; no contiene variable/unidad/tipo de medición,
frecuencia, instrumento, cobertura, zona horaria, licencia o fundamento de un
método. No reconstruye HORA/UBIGEO o códigos de estación. El informe completo
debe acompañarla porque conserva las restricciones no representables en C24.

## Alcance de cierre

El puente C20 → C24 se demuestra para la **preparación documental de la identidad
de un producto y una finalidad**, con revisión aportada y cotejo físico/literal.
M26 permanece **PENDIENTE globalmente**, con avance parcial experimental. No se
declaran cubiertos el fundamento científico revisado, las demás dimensiones o
destinos, autenticidad, permisos ni persistencia/custodia del expediente.

Las pruebas nuevas y regresiones, la suite completa realmente ejecutada y los
comandos/resultados finales se registran en la auditoría enlazada. Las cifras
históricas RC14 no se presentan como nuevas ejecuciones RC15.
