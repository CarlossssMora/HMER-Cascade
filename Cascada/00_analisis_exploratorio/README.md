# 00 — Análisis exploratorio y auditoría de datos

Esta carpeta reúne los análisis exploratorios, las comparaciones de anotaciones y las auditorías de solapamiento realizadas antes de implementar y evaluar la arquitectura en cascada.

Los notebooks estudian las distribuciones de datos utilizadas por **SAN (Modelo1)**, **PosFormer (Modelo2)** y **WAP**. Su propósito es comprobar inventarios, correspondencia entre identificadores e imágenes, convenciones LaTeX, referencias repetidas, duplicados exactos y posibles solapamientos entre entrenamiento y evaluación.

Las decisiones metodológicas deben interpretarse junto con [`METODOLOGIA_CASCADA.md`](../../METODOLOGIA_CASCADA.md). En particular, CROHME 2016 y CROHME 2019 se reservan para evaluación final y no deben utilizarse para ajustar parámetros o umbrales.

## Estructura general

```text
00_analisis_exploratorio/
├── README.md
├── eda_crohme_2014_modelo1.ipynb
├── eda_crohme_2014_modelo2.ipynb
├── comparacion_crohme_2014_modelo1_vs_modelo2.ipynb
├── auditoria_entrenamiento_posformer.ipynb
├── demostracion_normalizacion_limits_san_vs_posformer.ipynb
├── auditoria_solapamiento_train_posformer_vs_2016_2019.ipynb
├── auditoria_datos_wap.ipynb
├── comparacion_wap_san_2014_y_solapamiento_wap_2016.ipynb
├── criterio_normalizacion_latex.md
├── resumen_resultados_eda_crohme_2014.md
└── resultados/
    ├── archivos CSV de detalle
    ├── resúmenes JSON
    └── figuras exportadas
```

## Notebooks

| Archivo | Descripción |
|---|---|
| [`eda_crohme_2014_modelo1.ipynb`](eda_crohme_2014_modelo1.ipynb) | EDA del test CROHME 2014 preparado para Modelo1/SAN. Revisa inventario, dimensiones, proporción estimada de trazo, caja delimitadora, tokens LaTeX, longitudes, rareza de tokens y referencias repetidas. |
| [`eda_crohme_2014_modelo2.ipynb`](eda_crohme_2014_modelo2.ipynb) | EDA equivalente para el test CROHME 2014 de Modelo2/PosFormer. Permite contrastar su preparación y convención de anotación con SAN. |
| [`comparacion_crohme_2014_modelo1_vs_modelo2.ipynb`](comparacion_crohme_2014_modelo1_vs_modelo2.ipynb) | Alinea ambos tests por ID y compara orden, nombres, archivos, píxeles y anotaciones. Identifica diferencias explicadas por `\limits` y separa los casos que requieren inspección visual. |
| [`auditoria_entrenamiento_posformer.ipynb`](auditoria_entrenamiento_posformer.ipynb) | Audita `data/Modelo2/train`: correspondencia entre captions, BMP y LG; características visuales; tokens; uso de `\limits`; ground truth repetido; duplicados exactos y solapamiento con CROHME 2014. |
| [`demostracion_normalizacion_limits_san_vs_posformer.ipynb`](demostracion_normalizacion_limits_san_vs_posformer.ipynb) | Muestra las imágenes y los ground truth de SAN y PosFormer antes y después de retirar exclusivamente el token `\limits`. Conserva aparte las diferencias no resueltas por esta regla. |
| [`auditoria_solapamiento_train_posformer_vs_2016_2019.ipynb`](auditoria_solapamiento_train_posformer_vs_2016_2019.ipynb) | Comprueba si los tests CROHME 2016/2019 de PosFormer aparecen en su entrenamiento mediante IDs, SHA-256 de archivo, SHA-256 de píxeles y candidatos perceptuales dHash. |
| [`auditoria_datos_wap.ipynb`](auditoria_datos_wap.ipynb) | Audita los datos WAP usados por SAN. Lee directamente los `.tar.gz`, cuantifica duplicados internos y compara WAP train con WAP/Modelo2 2016 y Modelo2 2019. |
| [`comparacion_wap_san_2014_y_solapamiento_wap_2016.ipynb`](comparacion_wap_san_2014_y_solapamiento_wap_2016.ipynb) | Compara WAP train con SAN 2014, WAP 2014 con SAN 2014 y WAP train con WAP 2016. La última comparación utiliza solo IDs e imágenes porque WAP 2016 no contiene ground truth local. |

Los notebooks conservan comentarios explicativos y generan sus salidas reproducibles dentro de [`resultados/`](resultados/). Al volver a ejecutarlos, algunos archivos de resultados pueden sobrescribirse.

## Documentos Markdown

| Archivo | Descripción |
|---|---|
| [`criterio_normalizacion_latex.md`](criterio_normalizacion_latex.md) | Documenta la normalización conservadora seleccionada: retirar únicamente el token exacto `\limits` al comparar referencias y predicciones, sin modificar los datos originales. También enumera las transformaciones excluidas. |
| [`resumen_resultados_eda_crohme_2014.md`](resumen_resultados_eda_crohme_2014.md) | Resume los resultados de los EDA de CROHME 2014 y de la auditoría del entrenamiento de PosFormer, junto con sus principales implicaciones metodológicas. |

## Carpeta `resultados/`

Los archivos CSV contienen tablas detalladas y los JSON almacenan resúmenes fáciles de consumir desde código. Un CSV de coincidencias con solo encabezados —o prácticamente vacío— indica que no se encontraron pares bajo ese criterio; no debe confundirse con un error de ejecución.

### EDA de SAN / Modelo1

| Archivo | Descripción |
|---|---|
| [`muestras_crohme_2014_modelo1.csv`](resultados/muestras_crohme_2014_modelo1.csv) | Registro por muestra del test SAN 2014, con anotación y características visuales. |
| [`frecuencias_tokens_modelo1.csv`](resultados/frecuencias_tokens_modelo1.csv) | Frecuencia y proporción de los tokens LaTeX de SAN 2014. |
| [`resumen_eda_modelo1.json`](resultados/resumen_eda_modelo1.json) | Resumen estructurado de los principales conteos y estadísticas del EDA de SAN. |

### EDA de PosFormer / Modelo2

| Archivo | Descripción |
|---|---|
| [`muestras_crohme_2014.csv`](resultados/muestras_crohme_2014.csv) | Registro por muestra del test PosFormer 2014, con anotación y características visuales. |
| [`frecuencias_tokens.csv`](resultados/frecuencias_tokens.csv) | Frecuencia y proporción de los tokens LaTeX de PosFormer 2014. |
| [`resumen_eda.json`](resultados/resumen_eda.json) | Resumen estructurado del EDA de PosFormer 2014. |

### Comparación SAN 2014 vs. PosFormer 2014

| Archivo | Descripción |
|---|---|
| [`comparacion_pareada_modelo1_modelo2.csv`](resultados/comparacion_pareada_modelo1_modelo2.csv) | Comparación completa alineada por ID, con anotaciones y clasificaciones de diferencia. |
| [`diferencias_anotaciones_modelo1_modelo2.csv`](resultados/diferencias_anotaciones_modelo1_modelo2.csv) | Subconjunto de pares cuyos ground truth difieren. Incluye operaciones de edición sobre tokens. |
| [`comparacion_tokens_modelo1_modelo2.csv`](resultados/comparacion_tokens_modelo1_modelo2.csv) | Contraste de frecuencia y proporción de cada token entre ambos modelos. |
| [`comparacion_imagenes_modelo1_modelo2.csv`](resultados/comparacion_imagenes_modelo1_modelo2.csv) | Comparación de dimensiones, hashes y contenido visual de los BMP pareados. |
| [`resumen_comparacion_modelo1_modelo2.json`](resultados/resumen_comparacion_modelo1_modelo2.json) | Resumen de inventario, igualdad visual y diferencias de anotación. |
| [`comparacion_crohme_2014.png`](resultados/comparacion_crohme_2014.png) | Figura exportada con una síntesis gráfica de la comparación. |

### Auditoría del entrenamiento de PosFormer

| Archivo | Descripción |
|---|---|
| [`auditoria_train_posformer_muestras.csv`](resultados/auditoria_train_posformer_muestras.csv) | Tabla por muestra con anotación, dimensiones, proporción de trazo, caja delimitadora y hashes. |
| [`auditoria_train_posformer_tokens.csv`](resultados/auditoria_train_posformer_tokens.csv) | Frecuencias, proporciones y presencia por expresión de los tokens del entrenamiento. |
| [`auditoria_train_posformer_referencias_repetidas.csv`](resultados/auditoria_train_posformer_referencias_repetidas.csv) | Grupos que comparten ground truth, con IDs, dimensiones y cantidad de imágenes exactas. |
| [`auditoria_train_posformer_variantes_limits.csv`](resultados/auditoria_train_posformer_variantes_limits.csv) | Variantes que se volverían iguales al retirar exclusivamente `\limits`. |
| [`auditoria_train_posformer_tokens_vs_2014.csv`](resultados/auditoria_train_posformer_tokens_vs_2014.csv) | Comparación de la distribución de tokens entre entrenamiento y test 2014. |
| [`auditoria_train_posformer_solapamientos_2014.csv`](resultados/auditoria_train_posformer_solapamientos_2014.csv) | Coincidencias exactas de imagen detectadas entre entrenamiento y CROHME 2014. |
| [`auditoria_train_posformer_resumen.json`](resultados/auditoria_train_posformer_resumen.json) | Conteos principales de la auditoría del entrenamiento y su comparación con 2014. |

### Solapamiento de PosFormer train con CROHME 2016/2019

| Archivo | Descripción |
|---|---|
| [`auditoria_solapamiento_posformer_inventario.csv`](resultados/auditoria_solapamiento_posformer_inventario.csv) | Inventario de captions, imágenes y LG en train, 2016 y 2019. |
| [`auditoria_solapamiento_posformer_ground_truth.csv`](resultados/auditoria_solapamiento_posformer_ground_truth.csv) | Conteo auxiliar de referencias LaTeX compartidas; no implica repetición de imagen. |
| [`auditoria_solapamiento_posformer_resumen.csv`](resultados/auditoria_solapamiento_posformer_resumen.csv) | Resumen de IDs, archivos, píxeles exactos y candidatos perceptuales por test. |
| [`auditoria_solapamiento_posformer_resumen.json`](resultados/auditoria_solapamiento_posformer_resumen.json) | Versión JSON del resumen y de los parámetros diagnósticos. |
| [`auditoria_solapamiento_posformer_revision_manual.csv`](resultados/auditoria_solapamiento_posformer_revision_manual.csv) | Tabla para clasificar visualmente los candidatos perceptuales. |
| [`auditoria_solapamiento_posformer_train_vs_2016_archivo.csv`](resultados/auditoria_solapamiento_posformer_train_vs_2016_archivo.csv) | Pares train–2016 con SHA-256 de archivo idéntico. |
| [`auditoria_solapamiento_posformer_train_vs_2016_pixeles.csv`](resultados/auditoria_solapamiento_posformer_train_vs_2016_pixeles.csv) | Pares train–2016 con dimensiones y píxeles idénticos. |
| [`auditoria_solapamiento_posformer_train_vs_2016_perceptual.csv`](resultados/auditoria_solapamiento_posformer_train_vs_2016_perceptual.csv) | Candidatos train–2016 seleccionados por dHash. |
| [`auditoria_solapamiento_posformer_train_vs_2019_archivo.csv`](resultados/auditoria_solapamiento_posformer_train_vs_2019_archivo.csv) | Pares train–2019 con SHA-256 de archivo idéntico. |
| [`auditoria_solapamiento_posformer_train_vs_2019_pixeles.csv`](resultados/auditoria_solapamiento_posformer_train_vs_2019_pixeles.csv) | Pares train–2019 con dimensiones y píxeles idénticos. |
| [`auditoria_solapamiento_posformer_train_vs_2019_perceptual.csv`](resultados/auditoria_solapamiento_posformer_train_vs_2019_perceptual.csv) | Candidatos train–2019 seleccionados por dHash para revisión visual. |

### Auditoría general de WAP

| Archivo | Descripción |
|---|---|
| [`auditoria_wap_resumen_hashes.csv`](resultados/auditoria_wap_resumen_hashes.csv) | Cantidad de muestras y hashes únicos en WAP train, 2014 y 2016. |
| [`auditoria_wap_duplicados_train.csv`](resultados/auditoria_wap_duplicados_train.csv) | Grupos de imágenes duplicadas dentro del entrenamiento WAP. |
| [`auditoria_wap_ground_truth_vs_2016_2019.csv`](resultados/auditoria_wap_ground_truth_vs_2016_2019.csv) | Coincidencias auxiliares de anotaciones entre WAP train y los tests finales. |
| [`auditoria_wap_solapamientos_resumen.csv`](resultados/auditoria_wap_solapamientos_resumen.csv) | Resumen de solapamientos exactos y candidatos perceptuales de WAP. |
| [`auditoria_wap_resumen.json`](resultados/auditoria_wap_resumen.json) | Resumen JSON de duplicados internos y parámetros diagnósticos. |
| [`auditoria_wap_revision_manual.csv`](resultados/auditoria_wap_revision_manual.csv) | Tabla para adjudicar los candidatos perceptuales de WAP. |
| [`auditoria_wap_vs_modelo2_fuentes_2016.csv`](resultados/auditoria_wap_vs_modelo2_fuentes_2016.csv) | Correspondencia por ID, archivo y píxeles entre las preparaciones WAP y PosFormer de 2016. |
| [`auditoria_wap_train_vs_wap_2016_archivo.csv`](resultados/auditoria_wap_train_vs_wap_2016_archivo.csv) | Coincidencias de archivo exacto entre WAP train y el TAR WAP 2016. |
| [`auditoria_wap_train_vs_wap_2016_pixeles.csv`](resultados/auditoria_wap_train_vs_wap_2016_pixeles.csv) | Coincidencias de píxeles exactos entre WAP train y WAP 2016. |
| [`auditoria_wap_train_vs_modelo2_2016_archivo.csv`](resultados/auditoria_wap_train_vs_modelo2_2016_archivo.csv) | Coincidencias exactas de archivo entre WAP train y Modelo2/2016. |
| [`auditoria_wap_train_vs_modelo2_2016_pixeles.csv`](resultados/auditoria_wap_train_vs_modelo2_2016_pixeles.csv) | Coincidencias exactas de píxeles entre WAP train y Modelo2/2016. |
| [`auditoria_wap_train_vs_modelo2_2019_archivo.csv`](resultados/auditoria_wap_train_vs_modelo2_2019_archivo.csv) | Coincidencias exactas de archivo entre WAP train y Modelo2/2019. |
| [`auditoria_wap_train_vs_modelo2_2019_pixeles.csv`](resultados/auditoria_wap_train_vs_modelo2_2019_pixeles.csv) | Coincidencias exactas de píxeles entre WAP train y Modelo2/2019. |
| [`auditoria_wap_train_vs_2016_perceptual.csv`](resultados/auditoria_wap_train_vs_2016_perceptual.csv) | Candidatos perceptuales entre WAP train y 2016. |
| [`auditoria_wap_train_vs_2019_perceptual.csv`](resultados/auditoria_wap_train_vs_2019_perceptual.csv) | Candidatos perceptuales entre WAP train y 2019. |

### Comparación WAP–SAN y WAP 2016

| Archivo | Descripción |
|---|---|
| [`comparacion_wap_san_inventario.csv`](resultados/comparacion_wap_san_inventario.csv) | Inventario de WAP train, WAP 2014, WAP 2016 y SAN 2014. |
| [`comparacion_wap_san_resumen.csv`](resultados/comparacion_wap_san_resumen.csv) | Resumen de las tres comparaciones principales por ID, archivo y píxeles. |
| [`comparacion_wap_san_resumen.json`](resultados/comparacion_wap_san_resumen.json) | Metadatos de las comparaciones y parámetros perceptuales utilizados. |
| [`comparacion_wap_2014_vs_san_2014_por_id.csv`](resultados/comparacion_wap_2014_vs_san_2014_por_id.csv) | Correspondencia uno a uno de WAP 2014 y SAN 2014, alineada por ID. |
| [`comparacion_wap_san_ground_truth.csv`](resultados/comparacion_wap_san_ground_truth.csv) | Comparación auxiliar de referencias LaTeX disponibles. |
| [`solapamientos_wap_train_vs_san_2014_pixeles.csv`](resultados/solapamientos_wap_train_vs_san_2014_pixeles.csv) | Pares de píxeles exactos entre WAP train y SAN 2014. |
| [`solapamientos_wap_train_vs_wap_2016_pixeles.csv`](resultados/solapamientos_wap_train_vs_wap_2016_pixeles.csv) | Pares de píxeles exactos entre WAP train y WAP 2016. |
| [`candidatos_wap_train_vs_san_2014.csv`](resultados/candidatos_wap_train_vs_san_2014.csv) | Candidatos perceptuales entre WAP train y SAN 2014. |
| [`candidatos_wap_train_vs_wap_2016.csv`](resultados/candidatos_wap_train_vs_wap_2016.csv) | Candidatos perceptuales entre WAP train y WAP 2016. |
| [`comparacion_wap_san_revision_manual.csv`](resultados/comparacion_wap_san_revision_manual.csv) | Tabla para documentar la inspección visual de candidatos WAP–SAN. |

### Archivo de control

| Archivo | Descripción |
|---|---|
| [`resultados/.gitkeep`](resultados/.gitkeep) | Mantiene la carpeta `resultados/` en el control de versiones cuando no contiene salidas generadas. |

## Convenciones de interpretación

- Un **hash de archivo igual** significa que dos archivos son idénticos byte a byte.
- Un **hash de píxeles igual** significa que sus dimensiones y contenido raster son idénticos.
- Un **candidato perceptual** es solo una sugerencia para inspección visual; dHash puede producir falsos positivos.
- Un **ground truth repetido** no implica que se haya reutilizado la misma imagen.
- Los cruces globales por hash pueden producir más filas que muestras cuando un mismo contenido está duplicado en ambos lados. Para correspondencias uno a uno debe preferirse la alineación por ID y reportarse también la cantidad de imágenes únicas implicadas.
- La normalización de `\limits` se aplica únicamente al comparar referencias y predicciones; nunca modifica los archivos originales ni participa en el cálculo de confianza o en la decisión de derivación.

## Orden de lectura sugerido

1. Leer [`resumen_resultados_eda_crohme_2014.md`](resumen_resultados_eda_crohme_2014.md).
2. Consultar los EDA individuales de SAN y PosFormer.
3. Revisar la comparación pareada de CROHME 2014.
4. Leer [`criterio_normalizacion_latex.md`](criterio_normalizacion_latex.md).
5. Revisar las auditorías de entrenamiento y solapamiento.
6. Consultar los CSV de `resultados/` cuando se necesite trazabilidad por muestra.
