# Resumen de resultados: análisis exploratorio de CROHME 2014

## Alcance

Este documento sintetiza los resultados de los tres notebooks de la etapa exploratoria:

1. [`eda_crohme_2014.ipynb`](eda_crohme_2014.ipynb): test ubicado en `data/Modelo2/2014`.
2. [`eda_crohme_2014_modelo1.ipynb`](eda_crohme_2014_modelo1.ipynb): test ubicado en `data/Modelo1/2014`.
3. [`comparacion_crohme_2014_modelo1_vs_modelo2.ipynb`](comparacion_crohme_2014_modelo1_vs_modelo2.ipynb): comparación pareada de ambos tests.

Los tres notebooks fueron ejecutados completamente. Las tablas y resúmenes derivados se encuentran en [`resultados/`](resultados/).

## Resumen ejecutivo

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

### Advertencia sobre la métrica de tinta

Los BMP tienen **fondo negro y trazos blancos**. En los notebooks, `fraccion_tinta` se calculó como la proporción de píxeles con intensidad menor que 250. Su mediana fue 0.91995, pero este valor representa principalmente el fondo oscuro, no la tinta blanca. Por la misma razón, la caja delimitadora calculada con esa máscara ocupa el 100 % del lienzo en todas las imágenes.

Por tanto:

- las dimensiones, relaciones de aspecto, tamaños de archivo, hashes y comparaciones visuales son válidos;
- `fraccion_tinta`, `tinta_media` y `ocupacion_bbox` no deben interpretarse como ocupación real de los trazos en su formulación actual;
- para medir los trazos debe invertirse la polaridad, por ejemplo usando una máscara de píxeles claros sobre fondo negro.

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
7. **Las métricas de ocupación visual deben corregirse antes de usarlas.** La polaridad negro–blanco invalida la interpretación actual de tinta y caja delimitadora.

## Conclusión

Modelo1 y Modelo2 representan esencialmente el mismo test visual de CROHME 2014. La diferencia sustantiva está en la convención de las anotaciones: Modelo2 añade `\limits` de forma sistemática y corrige algunos casos puntuales de estructura, puntuación o símbolo. Para comparaciones justas entre modelos se recomienda usar una única versión canónica de las etiquetas, documentar cualquier normalización y conservar los IDs como clave de correspondencia.

La evidencia no respalda considerar los dos directorios como conjuntos de prueba visualmente distintos. Sí respalda tratarlos como **dos variantes de anotación sobre las mismas 986 imágenes**.
