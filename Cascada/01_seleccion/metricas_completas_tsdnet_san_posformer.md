# Métricas completas de TSDNet, SAN y PosFormer

Resultados obtenidos sobre CROHME 2014 con 986 muestras válidas por modelo. El entorno común fue una NVIDIA GeForce RTX 4050 Laptop GPU de 6 GB, Python 3.8.10, PyTorch 2.0.1+cu118, CUDA 11.8 y tres ejecuciones de calentamiento.

## 1. Métricas de reconocimiento de expresiones

| Modelo | Muestras válidas | Exact match | Distancia ≤1 | Distancia ≤2 | CER micro | CER macro | Distancia total | Tokens de referencia | Errores de ejecución |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **SAN** | 986 | 56.59 % (558) | 73.94 % (729) | 79.31 % (782) | 12.98 % | 12.20 % | 2,064 | 15,897 | 0 |
| **TSDNet** | 986 | 56.19 % (554) | No medida | No medida | No medido | No medido | No medida | No medidos | 0 |
| **PosFormer** | 986 | **62.68 % (618)** | **79.01 % (779)** | **84.69 % (835)** | **7.83 %** | **7.98 %** | **1,252** | 15,987 | 0 |

Las métricas de SAN y PosFormer usan distancia de Levenshtein sobre tokens LaTeX separados por espacios. El CER micro se calcula como la suma de todas las distancias dividida entre el total de tokens de referencia; el CER macro es el promedio del CER de cada expresión. En TSDNet, el exact match es estructural y compara nodos, relaciones y padres, por lo que no es estrictamente equivalente al exact match LaTeX de los otros dos modelos.

## 2. Métricas de desempeño de cómputo

| Modelo | Latencia media (ms) | Mediana (ms) | p95 (ms) | Mínima (ms) | Máxima (ms) | Inferencia total (s / min) | GFLOPs medios | GFLOPs mediana | GFLOPs p95 | Total estimado (TFLOPs) | Parámetros (M) | Pesos + buffers (MiB) | VRAM del modelo (MiB) | Pico total VRAM (MiB) | Pico incremental VRAM (MiB) | Imágenes redimensionadas |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **SAN** | 161.60 | 166.22 | 300.82 | 18.39 | 697.77 | 159.34 / 2.66 | 9.76 | 5.80 | 29.07 | 9.63 | **7.996** | **30.55** | **30.70** | **210.31** | **169.13** | 0 |
| **TSDNet** | 248.80 | 221.98 | 476.48 | 46.80 | 4,658.76 | 245.32 / 4.09 | No medidos | No medida | No medido | No medido | 11.413 | 43.59 | 43.75 | 370.99 | 318.21 | 0 |
| **PosFormer** | 1,427.71 | 670.09 | 4,998.81 | 49.16 | 72,245.20 | 1,407.72 / 23.46 | 219.54 | 69.11 | 764.99 | 216.46 | 9.632 | 37.77 | 37.94 | 1,977.32 | 1,930.02 | 9 |

### Alcance y comparabilidad

- La latencia excluye lectura de disco y preprocesamiento en CPU; mide la inferencia con la entrada ya residente en GPU.
- Los FLOPs son estimaciones de `torch.profiler` para los operadores que PyTorch sabe contabilizar, principalmente convoluciones y multiplicaciones matriciales. No constituyen un conteo analítico exhaustivo de toda la búsqueda.
- SAN y PosFormer realizaron una segunda inferencia perfilada por muestra para calcular FLOPs. Aunque el bloque perfilado no está incluido directamente en `time_ms`, la carga sostenida afecta temperatura, potencia y CPU. Por ello, estas latencias no deben compararse directamente con una corrida aislada sin profiler.
- Como referencia, antes de añadir el profiler SAN obtuvo 120.05 ms de media, 115.99 ms de mediana, 233.01 ms de p95 y 118.36 s totales. PosFormer obtuvo 450.98 ms de media, 280.41 ms de mediana, 1,010.05 ms de p95 y 444.67 s totales.
- La última corrida de PosFormer mostró una progresión fuerte por complejidad y carga sostenida: las primeras 100 muestras promediaron 230.63 ms y las últimas 100 acumularon 588.30 s.

## Fuentes

- [Notebook de SAN](benchmark_san_gpu.ipynb)
- [Notebook de TSDNet](benchmark_tsdnet_gpu.ipynb)
- [Notebook de PosFormer](benchmark_posformer_gpu.ipynb)
- [Resumen de SAN](resultados/resumen_san_crohme_2014.json)
- [Resumen de TSDNet](resultados/resumen_tsdnet_crohme_2014.json)
- [Resumen de PosFormer](resultados/resumen_posformer_crohme_2014.json)
