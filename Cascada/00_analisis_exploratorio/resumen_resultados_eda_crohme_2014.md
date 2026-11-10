# Resumen de resultados: análisis exploratorio de CROHME y auditoría de datos

## Alcance

Este documento sintetiza los resultados disponibles y el estado de los cuatro notebooks de la etapa exploratoria:

1. [`eda_crohme_2014_modelo2.ipynb`](eda_crohme_2014_modelo2.ipynb): test ubicado en `data/Modelo2/2014`.
2. [`eda_crohme_2014_modelo1.ipynb`](eda_crohme_2014_modelo1.ipynb): test ubicado en `data/Modelo1/2014`.
3. [`comparacion_crohme_2014_modelo1_vs_modelo2.ipynb`](comparacion_crohme_2014_modelo1_vs_modelo2.ipynb): comparación pareada de ambos tests.
4. [`auditoria_entrenamiento_posformer.ipynb`](auditoria_entrenamiento_posformer.ipynb): auditoría del conjunto de entrenamiento ubicado en `data/Modelo2/train`.

Los cuatro notebooks fueron ejecutados completamente y sin errores. Las tablas y resúmenes derivados se encuentran en [`resultados/`](resultados/).

| Notebook | Conjunto | Estado |
|---|---|---|
| `eda_crohme_2014_modelo2.ipynb` | `data/Modelo2/2014` | Ejecutado |
| `eda_crohme_2014_modelo1.ipynb` | `data/Modelo1/2014` | Ejecutado |
| `comparacion_crohme_2014_modelo1_vs_modelo2.ipynb` | Ambos tests de 2014 | Ejecutado |
| `auditoria_entrenamiento_posformer.ipynb` | `data/Modelo2/train` | Ejecutado |

## Resumen ejecutivo

Los resultados cuantitativos de esta sección corresponden exclusivamente a los tres notebooks ejecutados sobre CROHME 2014.

Los dos directorios contienen las mismas **986 expresiones manuscritas**. Existe una correspondencia completa entre imágenes y anotaciones, sin archivos corruptos ni muestras faltantes. Las 986 imágenes son idénticas byte a byte y píxel a píxel; las diferencias entre los tests se concentran en el nombre de los archivos, el orden de las muestras y las anotaciones LaTeX.

De las 986 anotaciones, **901 (91.38 %) son idénticas** y **85 (8.62 %) cambian**. En 79 de esos 85 casos, la diferencia queda explicada únicamente por la incorporación de `\limits` en Modelo2. Los seis casos restantes incluyen correcciones en llaves o comas y un cambio de `\pi` a `\Pi`.

| Indicador | Modelo1 | Modelo2 |
|---|---:|---:|
| Imágenes BMP | 986 | 986 |
| Anotaciones | 986 | 986 |
| Parejas válidas | 986 | 986 |
| Imágenes corruptas | 0 | 0 |
| Tokens totales | 15,897 | 15,987 |
| Tamaño del vocabulario | 108 | 110 |
| Media de tokens por ecuación | 16.123 | 16.214 |
| Mediana de tokens por ecuación | 13 | 13 |
| Percentil 95 de longitud | 40 | 41 |
| Longitud máxima | 204 | 204 |
| Tokens con una sola aparición | 1 | 2 |
| Tokens con frecuencia menor o igual que 5 | 6 | 7 |
| Ecuaciones con algún token raro | 10 | 11 |
| Ecuaciones con llaves no balanceadas | 0 | 0 |
| Profundidad máxima de llaves | 4 | 4 |
| Expresiones distintas repetidas | 13 | 13 |

## 1. Resultados comunes de las imágenes

Las propiedades geométricas son exactamente las mismas en ambos tests porque su contenido visual no cambia.

| Propiedad | Resultado |
|---|---:|
| Ancho mínimo | 46 px |
| Ancho mediano | 256 px |
| Ancho medio | 303.55 px |
| Ancho P95 | 715 px |
| Ancho máximo | 1,734 px |
| Alto mínimo | 54 px |
| Alto mediano | 94 px |
| Alto medio | 105.05 px |
| Alto P95 | 179.75 px |
| Alto máximo | 311 px |
| Área mediana | 26,208 píxeles |
| Área máxima | 380,664 píxeles |
| Relación de aspecto mediana | 2.486 |
| Relación de aspecto máxima | 9.892 |

El conjunto presenta una variación considerable de ancho y relación de aspecto. Esto favorece el uso de redimensionamiento que conserve proporciones, *padding* dinámico y agrupación de muestras por tamaño. Un límite basado únicamente en la mediana descartaría expresiones válidas; para establecer límites de entrada conviene estudiar al menos P95 y P99.

### Métricas de tinta y caja delimitadora

Los BMP tienen **fondo negro y trazos blancos**. Los notebooks corregidos consideran como trazo los píxeles claros cuya intensidad es mayor que 20 en la escala de grises de 0 a 255. `tinta_media` se calcula como el promedio de `gris/255`, mientras que `fraccion_tinta` representa la proporción de píxeles que supera ese umbral.

Como las imágenes son idénticas en ambos tests, Modelo1 y Modelo2 producen exactamente las mismas métricas visuales:

| Métrica | Media | Mediana | P95 | Mínimo | Máximo |
|---|---:|---:|---:|---:|---:|
| Intensidad media de los trazos (`tinta_media`) | 0.08154 | 0.08005 | 0.12463 | 0.02429 | 0.16748 |
| Fracción del lienzo ocupada por píxeles de trazo (`fraccion_tinta`) | 8.15 % | 8.00 % | 12.46 % | 2.43 % | 16.75 % |
| Área relativa de la caja delimitadora (`ocupacion_bbox`) | 67.00 % | 69.06 % | 82.56 % | 32.49 % | 90.86 % |

La expresión típica ocupa aproximadamente el **8 % de los píxeles del lienzo**. No obstante, el rectángulo mínimo que contiene todos sus trazos ocupa cerca del **69 % del área total**, porque incluye los espacios internos existentes entre símbolos. La caja delimitadora mediana mide 233 × 71 píxeles; esto confirma que las imágenes conservan márgenes apreciables y que un recorte basado en los trazos podría reducir el área procesada sin eliminar contenido manuscrito.

## 2. Resultados de las anotaciones de Modelo1

Modelo1 contiene 15,897 tokens distribuidos entre 108 tipos. La secuencia típica tiene 13 tokens y el 95 % de las ecuaciones tiene 40 tokens o menos. La longitud máxima, 204 tokens, muestra que existe una cola de expresiones considerablemente más complejas que la muestra mediana.

Los tokens más frecuentes son las llaves `{` y `}`, con 2,297 apariciones cada una (14.45 % por token). Después aparecen `1`, `2`, `_`, `+`, `^`, `x`, `-`, los paréntesis y `=`. `\frac` aparece 423 veces y representa aproximadamente 2.66 % del corpus.

No se encontraron llaves desbalanceadas. La profundidad máxima de anidamiento fue 4. Sólo seis tipos tienen frecuencia menor o igual que cinco, y diez ecuaciones contienen al menos uno de estos tokens raros. Esto indica un vocabulario pequeño, aunque con una cola escasa que debe conservarse al diseñar el vocabulario del modelo.

## 3. Resultados de las anotaciones de Modelo2

Modelo2 contiene 15,987 tokens y 110 tipos, es decir, 90 apariciones y dos tipos más que Modelo1. La mediana se mantiene en 13 tokens, pero la media aumenta ligeramente a 16.214 y P95 pasa de 40 a 41.

Las llaves `{` y `}` siguen siendo los tokens más frecuentes, con 2,292 apariciones cada una (14.34 % por token). El resto de los símbolos dominantes conserva prácticamente el mismo orden: `1`, `2`, `+`, `_`, `^`, `x`, `-`, paréntesis, `=` y `\frac`.

La estructura permanece bien formada: no existen llaves desbalanceadas y la profundidad máxima es 4. Hay siete tipos con frecuencia menor o igual que cinco y once ecuaciones con tokens raros.

## 4. Comparación directa entre Modelo1 y Modelo2

### Inventario y orden

Los cuatro inventarios —anotaciones e imágenes de ambos modelos— comparten exactamente los mismos 986 IDs. Sin embargo, ningún ID ocupa la misma posición en los dos archivos de anotaciones. El desplazamiento absoluto mediano es de 274 posiciones y el máximo de 978.

En consecuencia, los tests deben alinearse por ID y nunca por número de fila. Además, Modelo1 añade `_0` al nombre de cada BMP, mientras que Modelo2 usa directamente el ID como nombre base.

### Contenido visual

| Resultado de la comparación de imágenes | Cantidad |
|---|---:|
| Pares comparados | 986 |
| Mismo SHA-256 | 986 |
| Mismos píxeles | 986 |
| Diferencias visuales | 0 |

Esto demuestra que ambos tests reutilizan exactamente las mismas entradas visuales. No se trata de imágenes parecidas ni de otra codificación equivalente: los archivos completos son idénticos byte a byte. La diferencia en nombres (`ID_0.bmp` frente a `ID.bmp`) es sólo administrativa.

### Contenido de las anotaciones

| Estado | Cantidad | Proporción |
|---|---:|---:|
| Imagen y anotación iguales | 901 | 91.38 % |
| Imagen igual y anotación diferente | 85 | 8.62 % |
| Imagen diferente y anotación igual | 0 | 0 % |
| Imagen y anotación diferentes | 0 | 0 % |

La distancia de edición acumulada entre las anotaciones es de 125 tokens, con un máximo de seis ediciones en una sola ecuación. Modelo2 contiene 90 tokens netos adicionales.

El cambio dominante es `\limits`:

- aparece 105 veces en Modelo2 y no aparece en Modelo1;
- explica por sí solo 79 de las 85 anotaciones diferentes;
- puede aparecer más de una vez en una misma expresión;
- modifica la secuencia objetivo y la presentación de límites en operadores grandes, aunque normalmente no cambia el significado matemático de la expresión.

Los únicos tipos cuya frecuencia cambia son:

| Token | Modelo1 | Modelo2 | Diferencia M2 − M1 |
|---|---:|---:|---:|
| `\limits` | 0 | 105 | +105 |
| `_` | 630 | 625 | −5 |
| `{` | 2,297 | 2,292 | −5 |
| `}` | 2,297 | 2,292 | −5 |
| `\Pi` | 0 | 1 | +1 |
| `\pi` | 68 | 67 | −1 |

La distancia de variación total entre las distribuciones de tokens es 0.00663 y la divergencia Jensen–Shannon es 0.00332 bits. Por tanto, las distribuciones globales son muy similares; la diferencia es pequeña pero sistemática y afecta la evaluación exacta.

### Seis diferencias no explicadas únicamente por `\limits`

| ID | Diferencia principal |
|---|---|
| `RIT_2014_225` | Modelo1 codifica dos comas como subíndices (`_ { , }`); Modelo2 usa comas directas. |
| `RIT_2014_51` | Modelo1 codifica dos separadores decimales como subíndices; Modelo2 usa comas directas. |
| `RIT_2014_191` | Modelo2 agrega `\limits` y cierra antes la llave del límite, separando correctamente `(z - 1) x(z)`. |
| `RIT_2014_216` | Modelo2 agrega `\limits` y corrige el cierre de la condición `y \rightarrow x`. |
| `RIT_2014_217` | Modelo1 representa dos comas como subíndices; Modelo2 las normaliza como comas directas. |
| `RIT_2014_133` | Modelo1 usa `\pi`; Modelo2 usa `\Pi`. Este cambio debe revisarse visualmente porque distingue pi minúscula de pi mayúscula. |

## 5. Implicaciones para entrenamiento y evaluación

1. **No deben tratarse como dos tests visuales independientes.** Las entradas son idénticas; combinar ambos conjuntos duplicaría las mismas imágenes con objetivos parcialmente distintos.
2. **La evaluación debe alinearse por ID.** El orden de las 986 muestras cambia completamente entre archivos.
3. **Se necesita una convención LaTeX única.** Sin normalización, una predicción puede ser matemáticamente equivalente y aun así fallar una métrica de coincidencia exacta por la presencia o ausencia de `\limits`.
4. **Las seis excepciones requieren una decisión explícita.** Cinco parecen correcciones de estructura o puntuación; `\pi` frente a `\Pi` podría alterar el símbolo matemático y debe contrastarse con la imagen.
5. **Conviene conservar dos niveles de evaluación:** coincidencia exacta de tokens y coincidencia después de una normalización documentada de comandos de presentación.
6. **Los límites de tamaño deben basarse en percentiles.** El ancho máximo de 1,734 px y la longitud máxima de 204 tokens están muy por encima de las medianas.
7. **Las métricas de ocupación visual ya consideran la polaridad correcta.** Los trazos ocupan una mediana del 8.00 % de los píxeles y su caja delimitadora una mediana del 69.06 % del lienzo; estos valores pueden orientar el recorte y el *padding* del preprocesamiento.

## 6. Auditoría del entrenamiento de PosFormer

### Integridad e inventario

La auditoría encontró **8,834 registros válidos**, 8,834 imágenes `.bmp` y 8,834 archivos `.lg`. Los identificadores son únicos y existe correspondencia completa entre las tres fuentes: no hay anotaciones sin imagen, imágenes sin anotación, anotaciones sin archivo `.lg` ni archivos `.lg` sin anotación. Tampoco se encontraron líneas mal formadas, referencias vacías o llaves desbalanceadas.

| Indicador | Resultado |
|---|---:|
| Registros válidos | 8,834 |
| IDs únicos | 8,834 |
| Imágenes BMP | 8,834 |
| Archivos LG | 8,834 |
| Líneas con error | 0 |
| IDs duplicados | 0 |
| Referencias vacías | 0 |
| Expresiones con llaves desbalanceadas | 0 |

La distribución de entrenamiento contiene dos muestras menos que las 8,836 expresiones citadas como referencia ilustrativa en la metodología para la distribución de CoMER. Esto no demuestra por sí mismo una pérdida de datos, porque se está auditando la distribución preparada para PosFormer, pero la diferencia debe quedar documentada al describir los datos utilizados.

### Propiedades de las imágenes

| Propiedad | Media | Mediana | P95 | Mínimo | Máximo |
|---|---:|---:|---:|---:|---:|
| Ancho (px) | 314.36 | 268 | 731.70 | 26 | 2,116 |
| Alto (px) | 103.77 | 93 | 177 | 54 | 481 |
| Relación de aspecto | 3.075 | 2.505 | 7.571 | 0.248 | 18.798 |
| Proporción estimada de trazo | 7.70 % | 7.53 % | 11.65 % | 1.47 % | 17.97 % |
| Ocupación de la caja delimitadora | 65.95 % | 69.02 % | 82.43 % | 6.62 % | 90.84 % |

La variación de tamaño es mayor que en el test de 2014: el entrenamiento alcanza 2,116 px de ancho y una relación de aspecto de 18.798. Estos extremos refuerzan la necesidad de conservar proporciones y utilizar criterios de redimensionamiento o agrupación basados en percentiles. La proporción de trazo mantiene la misma interpretación usada en los EDA del test: es una aproximación digital de los píxeles que difieren del fondo, no una medición física de tinta.

### Anotaciones y tokens

El entrenamiento contiene **137,733 tokens**, 109 tipos y 4,832 referencias LaTeX únicas. La longitud media es 15.591 tokens, la mediana es 13, P95 es 38, P99 es 56 y el máximo es 97. El vocabulario es compacto: el único token con frecuencia menor o igual que cinco es `\exists`, con cuatro apariciones.

Los tokens más frecuentes son `{` y `}`, con 19,976 apariciones cada uno, seguidos de `1`, `2`, `^`, `+`, `x`, `_`, `-`, los paréntesis, `\frac` y `=`. Esta distribución es consistente con la presencia abundante de superíndices, subíndices, fracciones y agrupaciones estructurales.

### Uso de `\limits`

`\limits` aparece **1,046 veces en 907 expresiones**, equivalentes al **10.27 %** del entrenamiento. Todas sus apariciones tienen inmediatamente antes uno de tres operadores:

| Contexto | Apariciones de `\limits` |
|---|---:|
| Después de `\sum` | 391 |
| Después de `\int` | 368 |
| Después de `\lim` | 287 |
| **Total** | **1,046** |

En el test de Modelo2, `\limits` aparece 105 veces y está presente en 81 de las 986 expresiones, es decir, 8.22 %. Por tanto, la convención también existe en entrenamiento y es ligeramente más frecuente por expresión que en el test.

No se encontraron dentro del entrenamiento dos referencias originales distintas que se volvieran iguales al retirar exclusivamente `\limits`. Esto indica que el archivo de entrenamiento no contiene simultáneamente ambas variantes de una misma secuencia, pero **no valida por sí solo la eliminación del token**. La decisión debe seguir siendo conservadora y limitarse a la comparación, después de revisar que no cambie el significado ni las relaciones estructurales.

### Referencias repetidas e imágenes duplicadas

Se identificaron **447 referencias LaTeX repetidas**, que agrupan 4,449 muestras, equivalentes al **50.36 %** del entrenamiento. Las 4,385 muestras restantes tienen una referencia que aparece una sola vez. El grupo más grande contiene 58 imágenes con el mismo *ground truth*.

La repetición de la referencia no implica que las entradas sean copias. De los 447 grupos repetidos, **441 presentan más de una dimensión de imagen**, lo que confirma que, en la gran mayoría de los casos, corresponden a realizaciones visuales diferentes de la misma expresión. Por ello, no procede eliminarlas únicamente porque compartan la anotación.

La comparación SHA-256 encontró 8,792 imágenes únicas y **42 grupos de duplicados exactos**, cada uno formado por dos archivos. En total hay 84 archivos implicados y 42 copias adicionales. Todos los pares idénticos comparten también la misma referencia LaTeX; no se detectó una misma imagen exacta asociada con anotaciones distintas. Estos duplicados exactos deben documentarse y podrían analizarse por separado si se estudia su efecto, pero su eliminación cambiaría la distribución empleada por el modelo preentrenado y no debe hacerse de manera unilateral.

### Separación respecto de CROHME 2014

No se encontraron identificadores compartidos entre entrenamiento y el test 2014 de PosFormer. Tampoco se encontraron imágenes idénticas byte a byte mediante SHA-256, incluso permitiendo nombres diferentes. Esta evidencia descarta solapamientos exactos de archivo entre ambas particiones, aunque no pretende detectar imágenes visualmente similares sometidas a transformaciones o recodificación.

La auditoría se mantiene separada del entrenamiento del modelo: no ajustó pesos, no modificó anotaciones y no convirtió automáticamente los hallazgos en reglas de normalización.

## Conclusión

Modelo1 y Modelo2 representan esencialmente el mismo test visual de CROHME 2014. La diferencia sustantiva está en la convención de las anotaciones: Modelo2 añade `\limits` de forma sistemática y corrige algunos casos puntuales de estructura, puntuación o símbolo. Para comparaciones justas entre modelos se recomienda usar una única versión canónica de las etiquetas, documentar cualquier normalización y conservar los IDs como clave de correspondencia.

La evidencia no respalda considerar los dos directorios como conjuntos de prueba visualmente distintos. Sí respalda tratarlos como **dos variantes de anotación sobre las mismas 986 imágenes**.

La auditoría del entrenamiento confirma que la convención `\limits` observada en Modelo2 también está presente en los datos de entrenamiento y siempre sigue a `\sum`, `\int` o `\lim`. Esto aporta evidencia a favor de tratarla como una diferencia de representación al comparar las salidas de los modelos, pero todavía no demuestra que retirarla sea una normalización suficiente para todos los casos.

También confirma que el ground truth repetido es una característica importante del entrenamiento de PosFormer: afecta a poco más de la mitad de las muestras, pero en casi todos los grupos las imágenes tienen dimensiones diferentes y representan realizaciones visuales distintas. En consecuencia, estas muestras deben conservarse en el análisis descriptivo y no considerarse duplicados únicamente por compartir la referencia. Los 42 pares idénticos detectados constituyen un fenómeno separado que debe documentarse sin alterar retroactivamente el conjunto usado por el modelo preentrenado.
