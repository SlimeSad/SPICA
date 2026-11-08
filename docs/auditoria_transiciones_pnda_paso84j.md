# PASO 84-J — Auditoría de cinco transiciones documentales

Fecha: **2026-11-08**. **Auditoría satisfactoria con restricciones** para continuar
el núcleo experimental del [contrato documental](contratos_metadatos_documentales_paso84j.md).
No se aprueban datos meteorológicos, términos jurídicos o integración operativa.

## Recuperación y procedimiento

Git comenzó limpio en **feature/suadc-http**, HEAD **ef17ad4**, «SUADC:
reconciliacion documental de metadatos PNDA». El commit consolida los tres
informes del 84-I. Se revisaron la
[reconciliación](reconciliacion_xlsx_docx_pnda_paso84i.md), su
[matriz](brechas_reconciliadas_pnda_paso84i.md) y sus
[evidencias/consultas](evidencias_consultas_pnda_paso84i.md), junto con las
condiciones del [84-D](brechas_metadatos_pnda_paso84d.md) y los estados del
[84-E](brechas_diccionario_pnda_paso84e.md).

Las definiciones originales delimitan la auditoría: disponibilidad/lectura del
DOCX (R02), vigencia/fechas (R04), licencia/redistribución (R05), significado de
faltantes (V04), controles de calidad y banderines aplicados (V07). Un estado
parcial del expediente no acredita la propiedad completa.

Se reabrió solo el DOCX autorizado, con el inspector existente **0.2.1**:

```text
C:\Users\Propietario\SPICA_EVIDENCIAS_PNDA_84F\metadatos-pnda.docx
20664 bytes
SHA-256 7b9dcbd71c4d00798d1795edfd5ba0d15ad0aaab0297a7f0aba91532437a0d18
```

Recorrido: **2026-11-08T21:07:16.481930+00:00** a
**2026-11-08T21:07:16.625088+00:00**. Se exigieron raíz exacta, tamaño/hash,
archivo regular y ausencia de symlinks/reparse points; lectura `rb`, con huella
y firma antes/después. Resultado: **DOCUMENTO_VALIDADO_EN_ALCANCE**,
conservación **True**, 55 párrafos, tabla de 17 filas/34 celdas y tres destinos
externos omitidos. No se abrió ninguno ni se escribieron nuevos controles.

El XLSX **no se reabrió en 84-J**. Sus 10815 bytes y SHA-256
`1851039a07682a3f202314f6f8811fc616cb4ca2a486c9e737fd8cea62a4b4dd`, las 16
definiciones y su cotejo físico son antecedentes 84-E/84-I, no una medición
actual. No es necesario reinterpretarlo para auditar estas cinco declaraciones D.
No se abrió el CSV, RAW, staging o SQLite operativo. Guardia del recorrido:
**0 red, 0 escrituras, 0 SQLite, 0 procesos, 0 accesos operativos**.

## Referencias comprobadas

Documento D y SHA anteriores. Todas son de **word/document.xml** y namespace
`w = http://schemas.openxmlformats.org/wordprocessingml/2006/main`.
`T/F/C/p/P` identifica tabla, fila, celda XML, párrafo local y ordinal canónico
global. No es una página ni una columna renderizada.

| Referencia | Declaración comprobada, resumida salvo literales cortos |
|---|---|
| T1/F1/C2/p1/P5 | Título del producto meteorológico de estaciones automáticas, con atribución SENAMHI |
| T1/F3/C2/p5/P13 | Afirmación de disponibilidad de datos horarios «validados» de tres variables |
| T1/F3/C2/p13/P21 | Instrucción de filtrar registros vacíos para analizar las tres variables |
| T1/F7/C2/p1/P34 | Fecha de creación: `2024-05-30` |
| T1/F9/C2/p1/P38 | Última actualización: `2024-05-30` |
| T1/F10/C2/p1/P40 | Versión visible: `1.0` |
| T1/F11/C2/p1/P42 | `Open Data Commons Attribution License` |
| T1/F13/C2/p1/P46 | Acceso: `Público` |

Se cotejaron los ocho ordinales y las rutas Clark con las referencias devueltas
por el inspector. Ejemplo P13, con ID local **DOCX-PNDA-84J** y SHA D:

```text
/{http://schemas.openxmlformats.org/wordprocessingml/2006/main}document[1]/{http://schemas.openxmlformats.org/wordprocessingml/2006/main}body[1]/{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tbl[1]/{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tr[3]/{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tc[2]/{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p[5]
```

## Dictamen individual

| ID | Estado anterior 84-E | Propuesta 84-I | Brecha y condición de cierre | Evidencia y documento | Referencia estructural | Alcance | Restricciones | Conclusión justificada | Decisión auditada |
|---|---|---|---|---|---|---|---|---|---|
| R02 | NO_EVALUABLE | RESUELTA_CON_EVIDENCIA | Documento DOCX: entrega/adquisición autorizada, integridad, lectura acotada, fecha/versión y alcance, o constancia institucional de indisponibilidad | D01/D09, DOCX identificado; adquisición histórica 84-H y lectura actual 0.2.1 | P5 y P34/P38/P40; inventario/huellas de esta sección | Copia local identificada y contenido en el perfil admitido; campos visibles fechados/versionados | No acredita autenticidad independiente, vigencia, correspondencia editorial ni suficiencia de cada tema | Sí, exclusivamente para disponibilidad, conservación e inspección delimitadas; omisiones siguen registradas | CONSERVAR; no ampliar a resolución científica de otras brechas |
| R04 | PENDIENTE_DE_EVIDENCIA | PARCIALMENTE_DOCUMENTADA | Vigencia/fechas: edición e historia aplicables y selección revisada para período concreto | D09, DOCX; X11/D15 son propiedades técnicas distintas | T1/F7/C2/p1/P34, F9/P38, F10/P40 | Existencia de fechas y versión explícitas en la ficha | No hay manifiesto de correspondencias, fecha editorial de X acreditada ni vigencia por serie; no convertir propiedades OOXML en edición | Sí para mejora parcial; no para cerrar vigencia | CONSERVAR parcial; edición aplicable pendiente |
| R05 | PENDIENTE_DE_EVIDENCIA | PARCIALMENTE_DOCUMENTADA | Licencia/redistribución: términos/edición, recursos cubiertos, atribución y uso previsto | D12, DOCX | T1/F11/C2/p1/P42 y F13/P46 | Nombre de licencia y acceso declarados | Texto/destino no abiertos; sin verificación jurídica de condiciones, edición o alcance de redistribución | Sí como declaración localizada, sin permiso jurídico | CONSERVAR parcial; redistribución no autorizada por esta evidencia |
| V04 | PENDIENTE_DE_EVIDENCIA | PARCIALMENTE_DOCUMENTADA | Faltantes por variable: política que vincule representaciones con significado y vigencia | D07, DOCX | T1/F3/C2/p13/P21 | Recomendación documental de filtrar registros vacíos | No define causa, centinelas, criterio por variable/conjunto o ventanas parciales; no se ejecutó filtrado | Sí, evidencia pertinente pero insuficiente para política completa | CONSERVAR parcial; originales y vacíos intactos |
| V07 | PENDIENTE_DE_EVIDENCIA | PARCIALMENTE_DOCUMENTADA | QC/banderines: procedimiento/edición y evidencia de aplicación al producto, con revisión/permiso independientes | D03, DOCX | T1/F3/C2/p5/P13 | Existe una afirmación institucional declarada de datos validados | No se localizan controles/flags o prueba de ejecución vinculada al CSV; el adjetivo no constituye corroboración ni validación científica | Sí solo como ampliación del expediente de declaraciones. Sería injustificado convertirla en verificación de QC | CONSERVAR parcial con esta limitación explícita; no habilitar reglas científicas |

No se encontró una transición injustificada que requiera cambiar la matriz 84-I.
En especial, **V07 no se convierte en nivel verificado**: parcial describe
documentación, no proporción de controles cumplidos. V06 sigue pendiente porque
ni siquiera se identifica el nivel/etapa de procesamiento aplicado. La condición
de cierre de V07 continúa incumplida.

No hay contradicción crítica nueva en la clasificación que impida diseñar el
núcleo aislado. La tensión PP y las discrepancias históricas HORA/UBIGEO siguen
siendo asuntos distintos, sin resolución en este paso. No se modificó ninguna
matriz histórica ni los tres informes del 84-I.

## Consecuencias, estado y límites

Se conserva el balance de **29 IDs**: **2 resueltas documentalmente, 17 parciales,
8 pendientes, 2 contradicciones y 0 no evaluables**; 27 abiertas. Las resueltas
R01/R02 se refieren a conservación/localización del XLSX y disponibilidad/lectura
del DOCX, respectivamente, no a propiedades meteorológicas certificadas.

El diseño debe separar integridad, inspección, extracción, aplicabilidad, edición,
corroboración, validación científica y derechos. No se crean datos institucionales
en el módulo: solo fixtures sintéticos. Ninguna palabra de un documento concede
por sí sola una acreditación positiva o permiso de ejecución.

Riesgos residuales: procedencia/autenticidad, vigencia y correspondencia exactas
no demostradas; falta de procedimientos QC; textos de licencia no inspeccionados;
perfil OOXML limitado, TOCTOU bajo propietario malicioso y presupuestos cooperativos.
Las comprobaciones actuales no renuevan evidencia remota ni auditan cambios de
terceros en almacenes que no se abrieron.

El [informe del núcleo](contratos_metadatos_documentales_paso84j.md) registra la
arquitectura, pruebas y verificaciones finales. Esta auditoría documental no
se suma al contador de tests ni autoriza la siguiente etapa, descargas o escrituras.
