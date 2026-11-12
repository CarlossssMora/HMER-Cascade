# Métricas completas de TSDNet, SAN y PosFormer

Resultados ejecutados sobre CROHME 2014 con 986 muestras válidas por modelo. El hardware y entorno registrados fueron una NVIDIA GeForce RTX 4050 Laptop GPU de 6 GB, Python 3.8.10, PyTorch 2.0.1+cu118 y CUDA 11.8. Los modelos conservaron sus pesos preentrenados y realizaron tres ejecuciones de calentamiento.

## 1. Métricas de reconocimiento de expresiones

Para SAN y PosFormer, la comparación principal usa las mismas 986 imágenes, alineadas por identificador y verificadas como idénticas mediante SHA-256. Ambos modelos se comparan contra la referencia de Modelo2 después de normalizar espacios y retirar únicamente el token de presentación `\limits`.

| Modelo | Muestras válidas | ExpRate | Distancia ≤1 | Distancia ≤2 | CER micro | CER macro | Distancia total | Tokens de referencia | Errores |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **SAN** | 986 | 56.80 % (560) | 74.04 % (730) | 79.51 % (784) | 12.88 % | 12.14 % | 2,046 | 15,882 | 0 |
| **PosFormer** | 986 | **62.68 % (618)** | **79.01 % (779)** | **84.69 % (835)** | **7.88 %** | **8.00 %** | **1,252** | 15,882 | 0 |
| **TSDNet** | 986 | 56.19 % (554) | No medida | No medida | No medido | No medido | No medida | No medidos | 0 |

Las métricas de SAN y PosFormer usan distancia de Levenshtein sobre tokens LaTeX separados por espacios. El CER micro divide la suma de las distancias entre el total de tokens de referencia; el CER macro promedia el CER de cada expresión. En TSDNet, el acierto es estructural y compara conjuntamente nodos, relaciones y padres con su representación nativa, por lo que su porcentaje no es estrictamente equivalente al ExpRate LaTeX común.

### Complementariedad entre SAN y PosFormer

Las cuatro categorías se determinan mediante ExpRate sobre la referencia común normalizada; `≤1` y `≤2` no modifican la categoría de una muestra.

| Resultado pareado | Instancias | Porcentaje |
|---|---:|---:|
| Ambos aciertan | 511 | 51.83 % |
| Solo SAN acierta | 49 | 4.97 % |
| Solo PosFormer acierta | 107 | 10.85 % |
| Ambos fallan | 319 | 32.35 % |
| Oracle: acierta al menos uno | 667 | 67.65 % |

El *oracle* representa únicamente un límite superior experimental construido con las etiquetas; no constituye una regla permitida para decidir la derivación durante la inferencia real.

## 2. Latencia de inferencia

SAN y PosFormer tienen tres corridas completas e independientes. Cada celda con `±` informa la media y la desviación estándar de la estadística obtenida en las tres corridas. TSDNet conserva una sola corrida, por lo que todavía no dispone de variabilidad entre repeticiones.

| Modelo | Corridas | Latencia media (ms) | Mediana (ms) | p95 (ms) | Suma de inferencias (s) | Rendimiento (imágenes/s) |
|---|---:|---:|---:|---:|---:|---:|
| **SAN** | 3 | **89.96 ± 1.22** | **87.07 ± 1.69** | **171.78 ± 2.39** | **88.70 ± 1.21** | **11.12 ± 0.15** |
| **TSDNet** | 1 | 248.80 | 221.98 | 476.48 | 245.32 | 4.02 |
| **PosFormer** | 3 | 411.26 ± 5.35 | 266.66 ± 4.03 | 915.59 ± 47.48 | 405.51 ± 5.28 | 2.43 ± 0.03 |

La latencia mide únicamente la llamada de inferencia con la entrada ya residente en GPU. Excluye lectura, preprocesamiento, conversión de la predicción, métricas y escritura. La suma de inferencias no es el tiempo de pared completo del notebook.

PosFormer conserva una muestra extrema, `505_em_51`, con una latencia media de 54.77 s entre las tres corridas. La consistencia del valor atípico en las tres repeticiones indica que está asociado con el comportamiento de decodificación de esa muestra y no con una perturbación aislada. Por ello, la mediana y el p95 describen mejor el comportamiento habitual que la media o el máximo.

## 3. Tamaño del modelo y memoria GPU

| Modelo | Parámetros (M) | Pesos + buffers (MiB) | Memoria del modelo (MiB) | Pico total (MiB) | Incremento máximo (MiB) | Imágenes redimensionadas |
|---|---:|---:|---:|---:|---:|---:|
| **SAN** | **7.996** | **30.55** | **30.70** | **210.31** | **169.13** | 0 |
| **PosFormer** | 9.632 | 37.77 | 37.94 | 1,977.32 | 1,930.02 | 9 |
| **TSDNet** | 11.413 | 43.59 | 43.75 | 370.99 | 318.21 | 0 |

La memoria del modelo se registra después de cargar los pesos. El pico total incorpora las activaciones, estados de decodificación y tensores temporales creados durante la inferencia; no representa memoria permanentemente ocupada. El incremento máximo es la diferencia entre el pico y la memoria base inmediatamente anterior a la inferencia de la muestra.

## 4. Estimación de FLOPs

| Modelo | GFLOPs medios | GFLOPs mediana | GFLOPs p95 | Total estimado (TFLOPs) |
|---|---:|---:|---:|---:|
| **SAN** | **9.76** | **5.80** | **29.07** | **9.63** |
| **PosFormer** | 219.54 | 69.11 | 764.99 | 216.46 |
| **TSDNet** | No medidos | No medida | No medido | No medido |

Los FLOPs se obtuvieron en notebooks independientes mediante `torch.profiler`. Son estimaciones para los operadores que PyTorch sabe contabilizar, principalmente convoluciones y multiplicaciones matriciales, y no constituyen un conteo analítico exhaustivo de toda la búsqueda autorregresiva.

## 5. Verificación técnica de probabilidades de SAN

Se ejecutó SAN mediante la instrumentación de SANv2 sobre una muestra técnica reproducible de 25 expresiones, con semilla 2026. El checkpoint y el vocabulario de SAN y SANv2 resultaron idénticos por SHA-256; activar `return_probabilities=True` no modificó ninguna predicción.

| Indicador | Resultado |
|---|---:|
| Muestras válidas | 25/25 |
| Errores de ejecución | 0 |
| Incumplimientos de esquema o rango | 0 |
| Pasos totales de decodificación | 312 |
| Decisiones de símbolos | 228 |
| Controles estructurales `struct` | 31 |
| Decisiones de terminación | 53 |
| Decisiones relacionales evaluadas | 217 |
| Relaciones aceptadas (`p > 0.5`) | 59 |
| Relaciones descartadas (`p ≤ 0.5`) | 158 |
| Decisiones de relleno | 0 |
| Referencias usadas para inferencia o probabilidades | No |

La prueba confirma que están disponibles la distribución `softmax` completa de tokens, la probabilidad del token seleccionado y las siete probabilidades `sigmoid` de relaciones. También permite conservar `p` para relaciones aceptadas y `1-p` para descartadas. Esta verificación demuestra disponibilidad y coherencia técnica, pero no demuestra todavía que las medidas de confianza separen adecuadamente aciertos y errores; además, el tamaño de 25 muestras es una configuración técnica pendiente de validación metodológica.

## 6. Alcance, comparabilidad y pendientes

- SAN y PosFormer ya cumplen el requisito de mediciones temporales repetidas con calentamiento y sincronización de GPU. TSDNet todavía cuenta con una sola corrida temporal.
- Las condiciones se ejecutaron en el mismo hardware y entorno registrado, pero el campo descriptivo `execution_conditions` permanece como `PENDIENTE_DE_DOCUMENTAR` en los nuevos JSON. Debe completarse antes de considerar cerrada la trazabilidad experimental.
- Los tiempos del notebook de comparación SAN–PosFormer son auxiliares y no sustituyen los benchmarks repetidos de latencia.
- La normalización de LaTeX se limita a la comparación; no modifica las anotaciones ni las salidas originales guardadas.
- Las métricas de TSDNet no son uniformes con el protocolo LaTeX común y deben interpretarse como referencia estructural separada.
- Los resultados de reconocimiento, memoria y FLOPs no cambiaron por separar el perfilado de la medición temporal; la actualización principal de cómputo corresponde a las tres corridas independientes de latencia.

## Fuentes

- [Comparación pareada de SAN y PosFormer](comparacion_san_posformer_crohme_2014.ipynb)
- [Notebook de latencia de SAN](benchmark_san_gpu_latencia.ipynb)
- [Notebook de FLOPs de SAN](benchmark_san_gpu_flops.ipynb)
- [Notebook de TSDNet](benchmark_tsdnet_gpu.ipynb)
- [Notebook de latencia de PosFormer](benchmark_posformer_gpu_latencia.ipynb)
- [Notebook de FLOPs de PosFormer](benchmark_posformer_gpu_flops.ipynb)
- [Verificación de probabilidades de SAN](verificacion_probabilidades_san.ipynb)
- [Resumen de comparación SAN–PosFormer](resultados/resumen_comparacion_san_posformer_crohme_2014.json)
- [Resumen repetido de latencia de SAN](resultados/resumen_san_latencia_crohme_2014_repeticiones.json)
- [Resumen de FLOPs de SAN](resultados/resumen_san_flops_crohme_2014.json)
- [Resumen de TSDNet](resultados/resumen_tsdnet_crohme_2014.json)
- [Resumen repetido de latencia de PosFormer](resultados/resumen_posformer_latencia_crohme_2014_repeticiones.json)
- [Resumen de FLOPs de PosFormer](resultados/resumen_posformer_flops_crohme_2014.json)
- [Resumen de verificación de probabilidades](resultados/resumen_verificacion_probabilidades_san_crohme_2014.json)
