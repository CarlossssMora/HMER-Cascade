# Comparación del conjunto local de TAMER

Fecha: 2026-09-20. Fuente local: `data/TAMER.zip`, extraída en `data/TAMER`. SHA-256 del ZIP: `BC4566959A70BB8F85ED55252C397BC41B739F9FAE98A8F78A7BD2FC0C8D686D`.

Se compararon los IDs y el texto de `caption.txt` de entrenamiento y de los años 2014, 2016 y 2019. Para las imágenes, se leyeron los arreglos de píxeles de `images.pkl` mediante un analizador de datos pickle que no ejecuta constructores Python. Se compararon las dimensiones y cada píxel con los BMP de los otros conjuntos; se comprobó que la paleta BMP es una escala de grises de identidad. El código reproducible es `Cascada/02_adaptacion/compare_tamer_datasets.js`; los conteos están en `tamer_datasets_summary.json` y el detalle de imágenes por ID en `TAMER-*-images.csv`.

| Año y comparación | IDs comunes | Anotaciones iguales | Solo `\limits` | Otras diferencias | Imágenes con píxeles idénticos |
|---|---:|---:|---:|---:|---:|
| 2014, TAMER–PosFormer | 986 | 986 | 0 | 0 | 986 |
| 2016, TAMER–PosFormer | 1147 | 1147 | 0 | 0 | 1147 |
| 2019, TAMER–PosFormer | 1199 | 1199 | 0 | 0 | 1199 |
| 2014, TAMER–SAN | 986 | 901 | 79 | 6 | 986 |
| 2014, TAMER–BTTR | 986 | 901 | 79 | 6 | 986 |
| 2016, TAMER–BTTR | 1147 | 1021 | 76 | 50 | 1147 |
| 2019, TAMER–BTTR | 1199 | 1044 | 96 | 59 | 0 |
| Entrenamiento, TAMER–PosFormer | 8834 | 8834 | 0 | 0 | 8834 |
| Entrenamiento, TAMER–BTTR | 8834 | 8008 | 755 | 71 | 8834 |

En las cuatro comparaciones TAMER–PosFormer, los `caption.txt` también son idénticos byte por byte. No faltó ningún ID ni imagen. En 2019, solo tres imágenes de TAMER y BTTR tienen las mismas dimensiones, y ninguna tiene los mismos píxeles. BTTR tiene **8835** IDs de entrenamiento: incluye `MfrDB0104`, ausente de TAMER y PosFormer. Los otros 8834 IDs son comunes.

**Conclusión:** el conjunto local de TAMER es equivalente al de PosFormer en entrenamiento y en las tres pruebas, en anotaciones e imágenes, aunque uno guarda los píxeles en `images.pkl` y el otro en BMP. TAMER comparte con PosFormer las diferencias de anotación frente a SAN/BTTR. Esto facilita evaluar TAMER y PosFormer sobre exactamente las mismas muestras e imágenes; la complementariedad de sus predicciones, velocidad y uso de memoria requieren una evaluación de los modelos, no se deducen del conjunto de datos.
