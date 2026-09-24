# Evaluación SAN–PosFormer con imágenes comunes de CROHME 2019

Fecha: 2026-09-20.

## Protocolo

- Se usaron los **1199 BMP** de `data/Modelo2/2019/img` como imágenes de entrada para ambos modelos. Los IDs y el ground truth se tomaron de `data/Modelo2/2019/caption.txt`.
- Se conservaron los checkpoints de SAN (`SAN/checkpoints/SAN_decoder/best.pth`) y PosFormer (`PosFormer/lightning_logs/version_0/checkpoints/best.ckpt`), sin reentrenamiento ni ajuste de parámetros.
- SAN recibió cada BMP en escala de grises, dividido entre 255, con máscara de unos, según su inferencia. PosFormer recibió el mismo BMP de origen con su transformación de evaluación `ScaleToLimitRange(16,1024,16,256)` y `ToTensor`. Esa transformación redimensionó 12 de 1199 imágenes antes de entrar en PosFormer.
- El benchmark recorrió cada muestra por ID, con ambos modelos cargados a la vez en una RTX 4050 Laptop GPU. El tiempo registrado mide la inferencia y excluye lectura y preparación de imágenes en CPU.
- Se reporta Exact Match directo frente al ground truth de PosFormer y Exact Match tras eliminar únicamente el token `\limits` tanto del ground truth como de cada predicción. La segunda evaluación se calculó después de inferir, sin cambiar imágenes ni modelos.
- Los 1199 IDs se procesaron sin errores. No hubo exclusiones por el límite de PosFormer de 200 tokens o 320 000 píxeles cuadrados en los archivos originales.

## Resultados

| Criterio | SAN | PosFormer | Oráculo de los dos modelos |
|---|---:|---:|---:|
| Exact Match directo | 617/1199 = 51.46 % | 779/1199 = 64.97 % | 824/1199 = 68.72 % |
| Exact Match sin `\limits` | 651/1199 = 54.30 % | 779/1199 = 64.97 % | 826/1199 = 68.89 % |

| Complementariedad | Directo | Sin `\limits` |
|---|---:|---:|
| Ambos correctos | 572 | 604 |
| Solo SAN | 45 | 47 |
| Solo PosFormer | 207 | 175 |
| Ambos fallan | 375 | 373 |

La normalización recuperó **34 aciertos de SAN** y no cambió ningún acierto de PosFormer. El oráculo normalizado supera a PosFormer por **47 muestras, o 3.92 puntos porcentuales**. Es un límite superior que requeriría elegir correctamente el modelo por muestra; no es el rendimiento medido de una regla de enrutamiento.

La latencia media de inferencia fue **104.336 ms** para SAN y **311.136 ms** para PosFormer (2.98 veces la de SAN). Las medianas fueron 100.298 y 230.908 ms; los percentiles 95 fueron 194.975 y 794.624 ms. Estas cifras excluyen lectura, preprocesamiento y la decisión de enrutamiento.

## Alcance

SAN procesó todas las imágenes de PosFormer 2019 sin fallo de formato ni falta de memoria. Esta ejecución demuestra su precisión con esa rasterización y un ground truth común. **Por sí sola no mide el efecto de cambiar de rasterización**, porque usa una única fuente de BMP.

Una evaluación posterior sí ejecutó SAN sobre los BMP de BTTR 2019 y comparó ambas rasterizaciones por ID con el mismo ground truth. Véase `evaluacion_SAN_BTTR_2014_2016_2019.md`. Esta evaluación de dos modelos sigue sin medir una cascada real ni seleccionar un umbral sobre el test de 2019.

## Archivos

- Predicciones, tiempos y estado por muestra: `benchmark_crohme_2019_common_images.csv`.
- Aciertos por muestra tras normalización: `benchmark_crohme_2019_common_images_normalized.csv`.
- Conteos verificables: `benchmark_crohme_2019_common_images_summary.json`.
- Ejecución: `Cascada/01_seleccion/benchmark_crohme.py --year 2019`.
- Resumen reproducible: `node Cascada/04_evaluacion/analyze_common_benchmark.js`.
