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
| **SAN** | 86.77 | 82.72 | 163.09 | 13.84 | 372.43 | 85.56 / 1.43 | 9.76 | 5.80 | 29.07 | 9.63 | **7.996** | **30.55** | **30.70** | **210.31** | **169.13** | 0 |
| **TSDNet** | 248.80 | 221.98 | 476.48 | 46.80 | 4,658.76 | 245.32 / 4.09 | No medidos | No medida | No medido | No medido | 11.413 | 43.59 | 43.75 | 370.99 | 318.21 | 0 |
| **PosFormer** | 373.72 | 240.43 | 792.19 | 45.55 | 55,753.59 | 368.49 / 6.14 | 219.54 | 69.11 | 764.99 | 216.46 | 9.632 | 37.77 | 37.94 | 1,977.32 | 1,930.02 | 9 |

### Alcance y comparabilidad

- La latencia excluye lectura de disco, preprocesamiento en CPU, decodificación y cálculo de métricas; mide únicamente la inferencia con la entrada ya residente en GPU.
- Las latencias de SAN y PosFormer proceden de notebooks aislados que no importan ni ejecutan `torch.profiler`. Esto evita la interferencia térmica, de potencia, CPU y memoria producida por perfilar una segunda inferencia después de cada muestra.
- Los FLOPs se obtuvieron en notebooks independientes mediante `torch.profiler`. Son estimaciones para los operadores que PyTorch sabe contabilizar, principalmente convoluciones y multiplicaciones matriciales, y no constituyen un conteo analítico exhaustivo de toda la búsqueda.
- La separación no modificó las métricas de reconocimiento, tamaño del modelo, memoria ni FLOPs: esos valores coincidieron exactamente con los obtenidos previamente.
- PosFormer conserva una muestra extrema (`505_em_51`) cuya inferencia aislada tardó aproximadamente 55.75 s y cuya estimación alcanza 28,015.16 GFLOPs. Por ello, la media y el máximo son más sensibles a valores atípicos que la mediana.

## Fuentes

- [Notebook de latencia de SAN](benchmark_san_gpu_latencia.ipynb)
- [Notebook de FLOPs de SAN](benchmark_san_gpu_flops.ipynb)
- [Notebook de TSDNet](benchmark_tsdnet_gpu.ipynb)
- [Notebook de latencia de PosFormer](benchmark_posformer_gpu_latencia.ipynb)
- [Notebook de FLOPs de PosFormer](benchmark_posformer_gpu_flops.ipynb)
- [Resumen de latencia de SAN](resultados/resumen_san_latencia_crohme_2014.json)
- [Resumen de FLOPs de SAN](resultados/resumen_san_flops_crohme_2014.json)
- [Resumen de TSDNet](resultados/resumen_tsdnet_crohme_2014.json)
- [Resumen de latencia de PosFormer](resultados/resumen_posformer_latencia_crohme_2014.json)
- [Resumen de FLOPs de PosFormer](resultados/resumen_posformer_flops_crohme_2014.json)
