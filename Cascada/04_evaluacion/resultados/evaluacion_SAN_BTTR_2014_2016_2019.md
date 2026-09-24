# SAN sobre los tres test de BTTR

Fecha: 2026-09-20.

Se ejecutó el checkpoint congelado `SAN/checkpoints/SAN_decoder/best.pth` sobre los BMP y `caption.txt` de `data/BTTR/2014`, `2016` y `2019`. SAN recibió cada BMP en escala de grises, dividido entre 255, con máscara de unos, siguiendo la inferencia usada en el benchmark anterior. Se procesaron todos los IDs, sin errores ni exclusiones. El resultado principal es Exact Match frente a las etiquetas de **BTTR**; «sin `\limits`» elimina solo ese token de etiqueta y predicción después de inferir.

| Test BTTR | Muestras | Exact Match | Sin `\limits` |
|---|---:|---:|---:|
| CROHME 2014 | 986 | 558/986 = **56.59 %** | 558/986 = **56.59 %** |
| CROHME 2016 | 1147 | 594/1147 = **51.79 %** | 594/1147 = **51.79 %** |
| CROHME 2019 | 1199 | 640/1199 = **53.38 %** | 642/1199 = **53.54 %** |

Como comprobación, las **986 predicciones de 2014** son idénticas a las del benchmark previo de SAN, cuyas imágenes también coinciden byte por byte con BTTR 2014.

## Efecto de la anotación

Las mismas predicciones de SAN se evaluaron también contra `data/Modelo2/{año}/caption.txt`. Estos resultados cambian únicamente el ground truth; las imágenes y las predicciones permanecen iguales.

| Año | Exact Match con GT PosFormer | Con GT PosFormer sin `\limits` |
|---|---:|---:|
| 2014 | 519/986 = 52.64 % | 560/986 = 56.80 % |
| 2016 | 585/1147 = 51.00 % | 615/1147 = 53.62 % |
| 2019 | 625/1199 = 52.13 % | 669/1199 = 55.80 % |

El denominador 2014 es 986 aquí; el análisis anterior sobre PosFormer usó 985 al excluir una muestra por el filtro de su evaluación oficial. Cambiar el ground truth cambia los conteos aunque SAN produzca exactamente las mismas predicciones.

## Efecto de usar BMP de BTTR o PosFormer en 2019

La evaluación anterior ejecutó **el mismo checkpoint SAN** sobre los 1199 BMP de PosFormer 2019. Para aislar el efecto de la imagen se compararon ambas ejecuciones por ID, contra el **mismo ground truth de PosFormer**, con la misma normalización de `\limits`:

| Resultado pareado | Muestras |
|---|---:|
| Correcto con ambas imágenes | 536 |
| Correcto solo con BMP de BTTR | 133 |
| Correcto solo con BMP de PosFormer | 115 |
| Incorrecto con ambas imágenes | 415 |

Con BMP de BTTR, SAN acertó **669/1199 = 55.80 %**; con BMP de PosFormer, **651/1199 = 54.30 %**. La diferencia neta es **18 muestras, o 1.50 puntos porcentuales**, a favor de los BMP de BTTR bajo este criterio. Las predicciones LaTeX fueron exactamente iguales en 658 muestras y cambiaron en 541. Esto mide el efecto de la fuente de imagen en este checkpoint y este test; no convierte una rasterización en referencia universal ni implica reentrenamiento.

## Reproducibilidad

- Predicciones por muestra: `san_bttr_2014.csv`, `san_bttr_2016.csv`, `san_bttr_2019.csv`.
- Conteos y comparación pareada: `san_bttr_summary.json`.
- Inferencia: `Cascada/04_evaluacion/evaluate_san_bttr.py`.
- Verificación y resumen: `node Cascada/04_evaluacion/analyze_san_bttr.js`.
