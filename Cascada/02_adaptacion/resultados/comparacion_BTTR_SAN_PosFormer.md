# Comparación de los conjuntos CROHME de SAN, BTTR y PosFormer

Fecha: 2026-09-20.

Fuente de BTTR: [repositorio oficial Green-Wood/BTTR](https://github.com/Green-Wood/BTTR), archivo [`data.zip`](https://github.com/Green-Wood/BTTR/blob/main/data.zip). Se descargó como `data/BTTR_data.zip` y se extrajo en `data/BTTR`, junto a `data/Modelo1` (SAN) y `data/Modelo2` (PosFormer). SHA-256 del ZIP: `E6404E6AE6DB7D7D93A10C75F1EDC3E6D81BDA100F42A0A67A3944A0965A05CE`.

La comparación se hizo por ID, tras normalizar solo espacios en las anotaciones. «Solo `\limits`» significa que ambas cadenas quedan iguales al retirar ese token. Las imágenes se compararon por SHA-256 de los archivos BMP y por dimensiones. Los detalles por muestra están en los CSV `SAN-BTTR-2014.csv`, `SAN-PosFormer-2014.csv` y `BTTR-PosFormer-{2014,2016,2019}.csv`; los conteos también están en `bttr_datasets_summary.json`. El análisis es reproducible con `node Cascada/02_adaptacion/compare_bttr_datasets.js` desde la raíz del proyecto.

| Comparación | IDs comunes | Anotaciones iguales | Solo `\limits` | Otras diferencias | BMP idénticos | Mismas dimensiones |
|---|---:|---:|---:|---:|---:|---:|
| SAN–BTTR 2014 | 986 | 986 | 0 | 0 | 986 | 986 |
| SAN–PosFormer 2014 | 986 | 901 | 79 | 6 | 986 | 986 |
| BTTR–PosFormer 2014 | 986 | 901 | 79 | 6 | 986 | 986 |
| BTTR–PosFormer 2016 | 1147 | 1021 | 76 | 50 | 1147 | 1147 |
| BTTR–PosFormer 2019 | 1199 | 1044 | 96 | 59 | 0 | 3 |

No faltan IDs ni imágenes en estas cinco comparaciones. En todos los casos clasificados como «solo `\limits`», el token adicional está en PosFormer.

## Interpretación

- **2014:** BTTR reproduce exactamente las anotaciones y los BMP de SAN. Frente a PosFormer reaparecen las mismas 85 discrepancias ya registradas: 79 debidas solo a `\limits` y 6 residuales. En las 986 muestras, retirar `\limits` deja 980 anotaciones iguales. El registro anterior reportaba 979 de 985 porque excluía una muestra filtrada por PosFormer.
- **2016:** BTTR y PosFormer comparten 1147 IDs y los BMP son idénticos. Hay 126 discrepancias de anotación (10.99 %): 76 se resuelven retirando `\limits` y 50 permanecen. Tras esa normalización coinciden 1097 de 1147 anotaciones (95.64 %).
- **2019:** BTTR y PosFormer comparten 1199 IDs. Hay 155 discrepancias de anotación (12.93 %): 96 se resuelven retirando `\limits` y 59 permanecen. Tras esa normalización coinciden 1140 de 1199 anotaciones (95.08 %). Entre las residuales hay diferencias de llaves en argumentos de `\frac` y funciones, y del orden de subíndices y superíndices. Por ejemplo, `ISICal19_1201_em_750` contiene `\frac 1 { 1 9 2 }` en BTTR y `\frac { 1 } { 1 9 2 }` en PosFormer.
- **Imágenes de 2019:** Ningún par de BMP con el mismo ID es idéntico byte por byte; solo tres pares tienen las mismas dimensiones. La mediana del área es 41 860 píxeles en BTTR y 30 550 en PosFormer. Esta prueba no determina si las trazas subyacentes son las mismas, pero sí muestra que las entradas rasterizadas no son intercambiables sin controlar el preprocesamiento.

BTTR es una fuente directa de anotaciones con la misma convención que SAN en **2014**. Sus anotaciones de **2019** permiten estudiar esa convención frente a PosFormer, pero no son anotaciones publicadas por SAN para 2019. Para comparar resultados de modelos en 2019 habrá que fijar un único conjunto de imágenes, un único ground truth y la misma normalización para todos; no se debe atribuir una diferencia de rendimiento solo al modelo si cambian también las imágenes.
