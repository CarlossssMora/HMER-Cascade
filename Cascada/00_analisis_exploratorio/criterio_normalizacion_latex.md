# Criterio de normalización de LaTeX para la comparación de modelos

## Propósito

Este documento define la normalización conservadora seleccionada para compatibilizar las secuencias LaTeX utilizadas por Modelo1 y Modelo2. La regla se aplica únicamente durante la comparación de referencias y predicciones; no modifica los archivos originales, las imágenes, los conjuntos de datos ni los parámetros de los modelos.

El criterio sigue la sección **Compatibilización y normalización de los datos** de `METODOLOGIA_CASCADA.md`: cualquier transformación debe preservar el contenido matemático y las relaciones estructurales, aplicarse de manera uniforme y quedar documentada.

## Evidencia observada

En los tests CROHME 2014 de ambos modelos se encontraron 986 imágenes idénticas y 85 pares con anotaciones diferentes. De esas diferencias, 79 quedan explicadas únicamente por la presencia de `\limits` en Modelo2.

La auditoría del entrenamiento de PosFormer también mostró que la convención forma parte de sus anotaciones:

- `\limits` aparece 1,046 veces en 907 expresiones de entrenamiento;
- representa el 10.27 % de las expresiones del conjunto;
- sus 1,046 apariciones están inmediatamente después de `\sum`, `\int` o `\lim`;
- en el test 2014 de Modelo2 aparece 105 veces en 81 expresiones, equivalentes al 8.22 % del conjunto.

Estos resultados muestran una diferencia sistemática de representación entre las anotaciones de los modelos. En los casos observados, `\limits` controla la colocación visual de los límites de operadores grandes y no introduce por sí mismo un símbolo matemático nuevo.

## Regla seleccionada

La única normalización automática será eliminar los tokens que sean **exactamente iguales** a `\limits`.

La eliminación se realizará después de separar la secuencia por tokens y se aplicará de la misma manera a:

- las referencias de evaluación;
- las predicciones de SAN;
- las predicciones de PosFormer;
- cualquier otra predicción que se compare bajo el mismo protocolo.

Ejemplo:

```text
Original:    \sum \limits _ { i = 1 } ^ { n } i
Normalizada: \sum _ { i = 1 } ^ { n } i
```

Una implementación de referencia es:

```python
def normalizar_latex(secuencia: str) -> str:
    r"""Elimina únicamente el token exacto \limits para fines de comparación."""
    tokens = secuencia.split()
    tokens_normalizados = [token for token in tokens if token != r"\limits"]
    return " ".join(tokens_normalizados)
```

La comparación debe hacerse sobre las secuencias tokenizadas resultantes. No se debe eliminar una subcadena contenida dentro de otro token ni aplicar reemplazos generales sobre el texto crudo.

## Transformaciones excluidas

No se normalizarán automáticamente las otras seis diferencias detectadas entre las anotaciones de CROHME 2014. En particular, quedan fuera de la regla:

- `_ { , }` frente a `,`;
- cambios en la posición o cierre de llaves;
- `\pi` frente a `\Pi`;
- cualquier sustitución, inserción o eliminación de símbolos matemáticos;
- cualquier cambio que pueda alterar subíndices, superíndices o relaciones estructurales.

`_ { , }` y `,` no son estructuralmente equivalentes: el primer caso coloca la coma como subíndice y el segundo la mantiene en la línea base. Aunque una inspección visual pueda sugerir un error de anotación en una muestra concreta, no existe evidencia suficiente para convertirlo en una sustitución global.

Los seis casos restantes pueden revisarse individualmente y, si se adopta alguna adjudicación, deberá registrarse por identificador con su justificación. Esa revisión no debe incorporarse silenciosamente a la función general de normalización.

## Tratamiento de referencias repetidas

Las referencias LaTeX repetidas no se consideran un problema de normalización. En el entrenamiento de PosFormer, 4,449 muestras pertenecen a grupos con el mismo *ground truth*, pero 441 de los 447 grupos repetidos contienen imágenes con dimensiones diferentes. Esto indica que, en general, son realizaciones manuscritas distintas de la misma expresión y deben conservarse como muestras independientes.

Los duplicados exactos de imagen constituyen un fenómeno diferente y deben documentarse por separado; no justifican cambios en las secuencias LaTeX ni la eliminación retroactiva de datos utilizados por un modelo preentrenado.

## Reporte de métricas

Para hacer visible el efecto de la compatibilización, se conservarán dos resultados:

1. **Métrica estricta:** compara las secuencias originales sin normalización.
2. **Métrica compatible:** elimina únicamente `\limits` de referencias y predicciones antes de comparar.

Los resultados deben indicar expresamente qué versión de la métrica se está reportando. La regla se define a partir del análisis de CROHME 2014 y debe permanecer fija si se utiliza posteriormente en CROHME 2016 o CROHME 2019; no se deben añadir transformaciones a partir de los resultados de evaluación final.

## Restricciones de reproducibilidad

- No modificar `caption.txt` ni otros archivos originales.
- No usar las referencias normalizadas como entrada para calcular confianza o decidir la derivación de la cascada.
- Aplicar exactamente la misma función a las predicciones y referencias.
- Registrar la versión del código y la cantidad de secuencias afectadas en cada conjunto.
- Mantener disponibles las secuencias originales para auditoría.
- Documentar por separado cualquier exclusión o adjudicación manual por identificador.

## Decisión

Con la evidencia disponible, retirar exclusivamente `\limits` es la normalización automática más conservadora y defendible. Esta decisión compatibiliza la principal diferencia sistemática observada sin extender la transformación a casos que podrían cambiar la estructura o el significado matemático.
