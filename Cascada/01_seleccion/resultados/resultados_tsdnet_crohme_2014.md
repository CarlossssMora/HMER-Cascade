# Resultados de TSDNet en CROHME 2014

Benchmark ejecutado sobre las 986 muestras válidas de la partición de prueba, sin errores, en una NVIDIA GeForce RTX 4050 Laptop GPU de 6 GB.

| Métrica | Resultado |
|---|---:|
| Exact match estructural | 56.19 % (554/986) |
| Latencia media | 335.85 ms |
| Latencia mediana | 275.55 ms |
| Latencia p95 | 641.88 ms |
| Latencia mínima | 71.04 ms |
| Tiempo total de inferencia | 331.15 s (5.52 min) |
| Parámetros | 11.413 M |
| Pesos + buffers | 43.59 MiB |
| Pico total de VRAM | 371.99 MiB |
| Pico incremental máximo | 318.21 MiB |

La latencia mide solo la inferencia con la entrada ya residente en GPU; excluye lectura de disco y preprocesamiento en CPU. Se realizaron tres ejecuciones de calentamiento y se usó búsqueda con ancho 1, `max_len=200` y sin normalización por longitud, igual que la evaluación predeterminada del repositorio.

La muestra `501_em_18` alcanzó el límite de decodificación y tardó 21.27 s, por lo que eleva la media. La mediana y el p95 describen mejor el comportamiento habitual. El resultado de exact match compara conjuntamente nodos, relaciones y padres del árbol, siguiendo el criterio del código oficial de TSDNet.

Entorno: Python 3.11.9, PyTorch 2.11.0+cu126 y CUDA 12.6.
