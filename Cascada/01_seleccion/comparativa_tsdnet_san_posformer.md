# Comparativa de TSDNet, SAN y PosFormer

Resultados medidos sobre las 986 muestras válidas de CROHME 2014. Los tres benchmarks se ejecutaron en una NVIDIA GeForce RTX 4050 Laptop GPU de 6 GB, con Python 3.8.10, PyTorch 2.0.1+cu118, CUDA 11.8 y tres ejecuciones de calentamiento.

| Modelo | Exact match (%) | Latencia media (ms) | Mediana (ms) | p95 (ms) | Máxima (ms) | Inferencia total (s / min) | Parámetros (M) | Pesos + buffers (MiB) | Pico total VRAM (MiB) | Pico incremental VRAM (MiB) | Errores |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **SAN** | 56.59 | **120.05** | **115.99** | **233.01** | **448.08** | **118.36 / 1.97** | **7.996** | **30.55** | **210.31** | **169.13** | 0 |
| **TSDNet** | 56.19 | 248.80 | 221.98 | 476.48 | 4,658.76 | 245.32 / 4.09 | 11.413 | 43.59 | 370.99 | 318.21 | 0 |
| **PosFormer** | **62.68** | 450.98 | 280.41 | 1,010.05 | 63,834.68 | 444.67 / 7.41 | 9.632 | 37.77 | 1,977.32 | 1,930.02 | 0 |

## Lectura rápida

- **SAN** es el modelo más rápido y ligero. Su latencia media es aproximadamente 2.07 veces menor que la de TSDNet y 3.76 veces menor que la de PosFormer.
- **PosFormer** obtiene el mejor exact match, con una ventaja de 6.09 puntos porcentuales sobre SAN, pero presenta el mayor costo temporal y de memoria.
- **TSDNet** queda entre SAN y PosFormer en latencia y VRAM, aunque en esta ejecución su exact match fue ligeramente menor que el de SAN.
- PosFormer tuvo una muestra atípica de 63.83 s y TSDNet una de 4.66 s. Por ello, la mediana y el p95 describen mejor la latencia habitual que la media o el máximo.

## Consideraciones metodológicas

- La latencia y el tiempo total contabilizan únicamente la inferencia con la entrada ya residente en GPU; excluyen lectura de disco y preprocesamiento en CPU.
- SAN y PosFormer calculan exact match sobre la secuencia LaTeX normalizada. TSDNet usa el exact match estructural de su representación de nodos, relaciones y padres. Los porcentajes son útiles para selección experimental, pero esta diferencia debe documentarse al presentarlos como una comparación directa.
- PosFormer redimensionó 9 de las 986 imágenes mediante su transformación oficial. SAN y TSDNet conservaron su preprocesamiento correspondiente.

## Archivos fuente

- [Notebook de SAN](benchmark_san_gpu.ipynb)
- [Notebook de TSDNet](benchmark_tsdnet_gpu.ipynb)
- [Notebook de PosFormer](benchmark_posformer_gpu.ipynb)
- [Resumen de SAN](resultados/resumen_san_crohme_2014.json)
- [Resumen de TSDNet](resultados/resumen_tsdnet_crohme_2014.json)
- [Resumen de PosFormer](resultados/resumen_posformer_crohme_2014.json)
