# Comparación del conjunto local de ABM

Fecha: 2026-09-20. Fuente local: `data/ABM`. Se compararon los archivos de entrenamiento y de CROHME 2014, 2016 y 2019 con SAN, BTTR y PosFormer. La equivalencia ya verificada entre TAMER y PosFormer permite extender a TAMER los resultados de esa comparación.

Los `caption.txt` de ABM tienen nombres distintos (`train_caption.txt` y `test-caption-{año}.txt`), pero son **idénticos byte por byte** a los de BTTR. El archivo `offline-test.pkl` también es idéntico byte por byte a `offline-2014-test.pkl`. Las imágenes de ABM se guardan como arreglos `1 × alto × ancho` en archivos pickle; se leyeron sin ejecutar constructores Python y se compararon por dimensiones y por cada valor de gris con los BMP de los otros conjuntos. Se verificó la paleta gris de identidad de los BMP.

| Año y comparación | IDs comunes | Anotaciones iguales | Solo `\limits` | Otras diferencias | Imágenes con píxeles idénticos |
|---|---:|---:|---:|---:|---:|
| 2014, ABM–SAN | 986 | 986 | 0 | 0 | 986 |
| 2014, ABM–BTTR | 986 | 986 | 0 | 0 | 986 |
| 2016, ABM–BTTR | 1147 | 1147 | 0 | 0 | 1147 |
| 2019, ABM–BTTR | 1199 | 1199 | 0 | 0 | 1199 |
| Entrenamiento, ABM–BTTR | 8835 | 8835 | 0 | 0 | 8835 |
| 2014, ABM–PosFormer/TAMER | 986 | 901 | 79 | 6 | 986 |
| 2016, ABM–PosFormer/TAMER | 1147 | 1021 | 76 | 50 | 1147 |
| 2019, ABM–PosFormer/TAMER | 1199 | 1044 | 96 | 59 | 0 |
| Entrenamiento, ABM–PosFormer/TAMER | 8834 | 8008 | 755 | 71 | 8834 |

En 2019, solo tres pares de imágenes ABM–PosFormer tienen iguales dimensiones; ninguno tiene los mismos píxeles. En entrenamiento, ABM y BTTR contienen 8835 muestras, una más que PosFormer y TAMER. La adicional es `MfrDB0104`.

**Conclusión:** ABM sigue la misma convención de anotación y la misma rasterización que BTTR en todos los conjuntos disponibles. Sus diferencias frente a PosFormer/TAMER son las ya medidas para BTTR. Esta equivalencia de datos no prueba que los modelos ABM y BTTR hagan las mismas predicciones ni que tengan rendimientos equivalentes.

Análisis reproducible: `Cascada/02_adaptacion/compare_abm_datasets.js`. Conteos: `abm_datasets_summary.json`. Detalle por ID, con anotaciones, dimensiones e igualdad de píxeles: `ABM-*-*.csv`.
