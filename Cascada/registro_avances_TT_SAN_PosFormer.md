# Registro de avances — Trabajo Terminal
## Cascada basada en confianza con SAN + PosFormer para HMER

**Fecha de corte:** 2026-09-05  
**Entorno principal:** Python 3.8.10, PyTorch 2.0.1+cu118  
**GPU:** NVIDIA GeForce RTX 4050 Laptop GPU (~6 GB VRAM)

---

## 1. Idea general del Trabajo Terminal

El objetivo es construir una **arquitectura en cascada basada en confianza** para reconocimiento de expresiones matemáticas manuscritas (HMER), utilizando:

- **SAN** como modelo de primera etapa (más rápido / ligero en inferencia).
- **PosFormer** como modelo de respaldo (más costoso, pero con mayor precisión).
- **Sin reentrenar ninguno de los dos modelos**.
- Ambos modelos permanecen congelados y se utilizan únicamente en inferencia.

La lógica propuesta es:

```text
Imagen
  |
  v
 SAN
  |
  +--> predicción
  |
  +--> confianza C(x)
          |
          v
      C(x) >= tau ?
        /       \
      sí         no
      |           |
 salida SAN   PosFormer
                  |
                  v
               salida
```

La hipótesis de trabajo es:

> Es posible acercarse al desempeño de PosFormer reduciendo el costo promedio de inferencia, ejecutando PosFormer únicamente cuando SAN presenta baja confianza.

---

## 2. Motivación computacional

Se midieron ambos modelos en el mismo equipo.

### Tamaño de modelos

| Modelo | Parámetros | Pesos | Buffers | Total |
|---|---:|---:|---:|---:|
| SAN | 7,996,103 | 30.50 MiB | 0.05 MiB | 30.55 MiB |
| PosFormer | 9,632,236 | 36.74 MiB | 1.03 MiB | 37.77 MiB |

### Modelos cargados simultáneamente

```text
Allocated : 68.64 MiB
Reserved  : 82.00 MiB
```

Conclusión:

- Ambos modelos pueden permanecer residentes simultáneamente en GPU.
- No es necesario cargar/descargar PosFormer dinámicamente.
- La cascada debe ahorrar **tiempo de inferencia**, no memoria de pesos.

---

## 3. Prueba controlada sobre una imagen

Imagen utilizada:

```text
18_em_0_0.bmp
```

Dimensiones:

```text
85 x 464
```

Ground truth:

```text
x _ { k } x x _ { k } + y _ { k } y x _ { k }
```

Ambos modelos produjeron exactamente la misma predicción correcta.

### Resultados

| Métrica | SAN | PosFormer |
|---|---:|---:|
| Tiempo | 28.379 ms | 247.275 ms |
| Pico VRAM | 211.56 MiB | 249.45 MiB |
| Incremento VRAM | 134.31 MiB | 172.19 MiB |
| Correcto | Sí | Sí |

Relación de tiempos:

```text
PosFormer / SAN = 8.71x
```

En esta muestra, SAN fue aproximadamente 88.52% más rápido.

---

## 4. Benchmark completo de CROHME 2014

Se creó un benchmark sobre todo el conjunto de prueba CROHME 2014 utilizando:

- Las mismas imágenes para SAN y PosFormer.
- Preprocesamiento nativo de cada modelo.
- Ambos modelos residentes en GPU.
- Sin preprocessing CPU dentro del tiempo de inferencia.

Archivo generado:

```text
01_seleccion/resultados/benchmark_crohme_2014.csv
```

### Resultados obtenidos

```text
Muestras solicitadas : 986
Muestras válidas      : 986
Errores               : 0
```

### Exact Match usando inicialmente las anotaciones de SAN

| Sistema | ExpRate | Aciertos |
|---|---:|---:|
| SAN | 56.59% | 558/986 |
| PosFormer | 57.91% | 571/986 |
| Oracle | 66.33% | 654/986 |

### Complementariedad

| Caso | Muestras | Porcentaje |
|---|---:|---:|
| Ambos correctos | 475 | 48.17% |
| Solo SAN | 83 | 8.42% |
| Solo PosFormer | 96 | 9.74% |
| Ambos fallan | 332 | 33.67% |

PosFormer rescata:

```text
96 / 428 = 22.43%
```

de los errores de SAN.

### Latencias

#### SAN

```text
Media   : 82.347 ms
Mediana : 80.073 ms
p95     : 154.263 ms
```

#### PosFormer

```text
Media   : 318.188 ms
Mediana : 181.149 ms
p95     : 745.645 ms
```

Relación usando medias:

```text
PosFormer / SAN = 3.86x
```

Mediana del ratio por muestra:

```text
2.77x
```

### Referencia teórica de escalamiento

Con latencias medias:

```text
r_max ≈ 0.7412
```

Es decir, mientras menos de aproximadamente 74.12% de las muestras se envíen a PosFormer, la cascada debería seguir siendo más rápida en promedio que ejecutar PosFormer siempre, ignorando por ahora el costo del gate y preprocessing.

---

## 5. Validación oficial de PosFormer

Se ejecutó el flujo oficial de evaluación de PosFormer sobre CROHME 2014.

Resultado:

```text
Validation ExpRate: 0.6274111866950989
2014 exprate [62.74111675126903, ...]
```

Por lo tanto:

```text
PosFormer oficial CROHME 2014 = 62.74%
```

Esto confirmó que:

- El checkpoint funciona correctamente.
- El entorno unificado Python 3.8 / PyTorch 2.0.1 no está rompiendo PosFormer.
- La diferencia observada en nuestro benchmark no era causada por la inferencia.

---

## 6. Comparación entre las distribuciones SAN y PosFormer

Se creó:

```text
02_adaptacion/compare_crohme_sources.py
```

y se compararon:

- IDs
- imágenes
- ground truths
- predicciones oficiales de PosFormer
- predicciones de PosFormer dentro del benchmark conjunto

### Hallazgos

#### IDs y filtro

```text
SAN captions              : 986
PosFormer captions        : 986
Predicciones oficiales    : 985
```

La muestra filtrada por PosFormer es:

```text
505_em_51
```

Razón:

```text
label_len > 200
area > 320000
311 x 1224
204 tokens
```

#### Imágenes

Resultado muy importante:

```text
Misma forma                 : 986 / 986
Píxeles exactamente iguales : 986 / 986
MAE pixel medio             : 0.0000
```

Conclusión:

> Las imágenes utilizadas por SAN y PosFormer son idénticas píxel por píxel.

#### Predicciones PosFormer

En las 985 muestras comunes:

```text
Predicción exacta sin cambiar: 985 / 985
```

Esto significa que PosFormer produce exactamente la misma predicción usando nuestro benchmark conjunto que usando su flujo oficial.

---

## 7. Problema detectado: diferencias de ground truth

Aunque las imágenes son idénticas, las anotaciones no lo son.

Sobre las 985 muestras evaluables:

```text
GT iguales      : 900 / 985 = 91.37%
GT diferentes   : 85 / 985 = 8.63%
```

### Evaluación usando GT de SAN

| Sistema | ExpRate |
|---|---:|
| SAN | 56.65% |
| PosFormer | 57.97% |
| Oracle | 66.40% |

Complementariedad:

```text
Ambos correctos : 475
Solo SAN        : 83
Solo PosFormer  : 96
Ambos fallan    : 331
```

### Evaluación usando GT de PosFormer

| Sistema | ExpRate |
|---|---:|
| SAN | 52.69% |
| PosFormer | 62.74% |
| Oracle | 67.11% |

Complementariedad:

```text
Ambos correctos : 476
Solo SAN        : 43
Solo PosFormer  : 142
Ambos fallan    : 324
```

### Cambio de aciertos al cambiar ground truth

```text
SAN gana aciertos       : 1
SAN pierde aciertos     : 40
PosFormer gana aciertos : 47
PosFormer pierde        : 0
```

Esto demostró que no era correcto comparar cada modelo con un ground truth diferente dentro del experimento principal.

---

## 8. Análisis de las diferencias de anotación

Se creó:

```text
02_adaptacion/classify_ground_truth_differences.py
```

Resultado sobre las 85 discrepancias:

```text
single_edit_block        : 59 (69.41%)
minor_lexical_difference : 23 (27.06%)
structural_difference    : 3  (3.53%)
```

Cambio más frecuente:

```text
insert [] -> [\limits] : 105 veces
```

Hallazgo principal:

> La mayor parte de la discrepancia proviene de la presencia del token LaTeX `\limits`.

---

## 9. Normalización exclusiva de `\limits`

Se probó una normalización deliberadamente conservadora:

```text
Eliminar únicamente el token \limits
```

La regla se aplica por igual a:

- ground truth
- predicción SAN
- predicción PosFormer
- futura predicción de la cascada

No se modifican:

- `^`
- `_`
- `{ }`
- operadores
- símbolos
- orden de tokens
- estructura matemática

### Resultado

Antes:

```text
GT iguales: 900 / 985 = 91.37%
```

Después de quitar `\limits`:

```text
GT iguales: 979 / 985 = 99.39%
```

Discrepancias residuales:

```text
6
```

### Evaluación normalizada contra GT PosFormer

| Sistema | Aciertos | ExpRate |
|---|---:|---:|
| SAN | 560/985 | 56.85% |
| PosFormer | 618/985 | 62.74% |
| Oracle | 667/985 | 67.72% |

Complementariedad:

```text
Ambos correctos : 511
Solo SAN        : 49
Solo PosFormer  : 107
Ambos fallan    : 318
```

Este escenario muestra un margen real para la cascada:

```text
SAN        : 56.85%
Oracle     : 67.72%
```

---

## 10. Seis discrepancias residuales

Después de eliminar `\limits`, quedaron seis IDs:

```text
RIT_2014_51
RIT_2014_133
RIT_2014_191
RIT_2014_216
RIT_2014_217
RIT_2014_225
```

Las diferencias incluyen:

- `\pi` vs `\Pi`
- errores de cierre de llaves alrededor de límites
- comas convertidas en subíndices
- diferencias de agrupación

Estas diferencias parecen ser errores o convenciones de serialización/anotación, no diferencias de imagen.

---

## 11. Descubrimiento de carpetas symLg

Los conjuntos de PosFormer/CoMER incluyen:

```text
data/2014/symLg
data/2016/symLg
data/2019/symLg
```

Los archivos `symLg` representan expresiones matemáticas como grafos de símbolos y relaciones.

El flujo oficial de CoMER para evaluación precisa utiliza:

```text
predicción LaTeX
      |
      v
  tex2symlg
      |
      v
 symLG predicho
      |
      v
    LgEval
      |
      v
symLG ground truth
```

Se intentó preparar la evaluación SAN con estas herramientas.

Se creó:

```text
02_adaptacion/evaluate_san_symlg.py
```

El script preparó correctamente:

```text
985 predicciones SAN
985 ground truths symLg
02_adaptacion/resultados/san_result_2014.zip
```

Las herramientas fueron encontradas dentro de CoMER:

```text
CoMER/convert2symLG/tex2symlg
CoMER/lgeval/bin/evaluate
```

Sin embargo, estas herramientas están diseñadas para Unix/Bash y no se ejecutaron directamente desde Windows.

Por simplicidad y por el tiempo disponible para el protocolo, se decidió **no depender por ahora de WSL/LgEval como requisito central del TT**.

---

## 12. Decisión metodológica actual para el protocolo

Para evitar depender de las anotaciones publicadas por SAN, se propone usar una única distribución de datos para todo el experimento:

```text
data_crohme.zip de CoMER/PosFormer
```

Esta distribución contiene:

```text
CROHME 2014
CROHME 2016
CROHME 2019
```

### Uso de cada conjunto

```text
CROHME 2014
    |
    +--> conjunto de calibración/desarrollo
         - selección de medida de confianza
         - selección de umbral tau

CROHME 2016
    |
    +--> test final

CROHME 2019
    |
    +--> test final
```

Una vez seleccionado el umbral con 2014:

```text
tau* queda congelado
```

No se utiliza 2016 ni 2019 para seleccionar hiperparámetros de la cascada.

---

## 13. Criterio de evaluación propuesto

Para los experimentos principales del TT:

- Misma distribución de datos para todos.
- Mismas imágenes para SAN, PosFormer y cascada.
- Mismo ground truth.
- Mismo criterio de Exact Match.
- Eliminación uniforme del token tipográfico `\limits` antes de comparar.

Conceptualmente:

```python
def canonical_latex(text):
    tokens = text.split()
    tokens = [t for t in tokens if t != r"\limits"]
    return " ".join(tokens)
```

La comparación será:

```text
canonical(predicción) == canonical(ground_truth)
```

Esto se aplicará de la misma forma a:

```text
SAN
PosFormer
Cascada
```

### Importante

La comparación justa del TT **no requiere que ambos modelos hayan sido entrenados bajo exactamente las mismas condiciones**.

La pregunta de investigación no será:

> ¿Qué arquitectura es mejor si se entrena bajo condiciones idénticas?

La pregunta será:

> ¿Puede una cascada de modelos preentrenados reducir el costo promedio de inferencia manteniendo un desempeño cercano al modelo pesado?

Por ello, la condición de justicia experimental es que durante la evaluación:

```text
mismas muestras
mismo ground truth
misma métrica
mismo hardware
```

---

## 14. Resultados que respaldan la viabilidad de la cascada

### Diferencia de costo

```text
SAN media        : 82.347 ms
PosFormer media  : 318.188 ms
```

PosFormer es aproximadamente:

```text
3.86x más lento
```

### Complementariedad bajo protocolo común normalizado

```text
Solo SAN        : 49
Solo PosFormer  : 107
```

Esto significa que existen 107 expresiones que SAN falla pero PosFormer sí puede resolver.

### Techo oracle

```text
SAN     : 56.85%
Pos     : 62.74%
Oracle  : 67.72%
```

Existe por tanto un margen potencial suficiente para investigar un gate de confianza.

---

## 15. Arquitectura experimental propuesta

```text
                     imagen
                       |
                       v
                      SAN
                       |
             +---------+----------+
             |                    |
        predicción           confianza C
                                  |
                                  v
                              C >= tau ?
                              /       \
                            sí         no
                            |           |
                       salida SAN    PosFormer
                                         |
                                         v
                                      salida
```

Ambos modelos permanecerán cargados simultáneamente en GPU.

No se modificarán pesos.

No se realizará fine-tuning.

No se realizará reentrenamiento.

---

## 16. Próximo bloque de trabajo: confianza de SAN

El siguiente objetivo técnico es modificar SAN únicamente para observabilidad de inferencia.

Actualmente SAN calcula internamente:

```python
word_prob = self.word_convert(word_out_state)
_, word = word_prob.max(1)
```

La idea es conservar la predicción original y extraer además las distribuciones de probabilidad.

Por cada token:

```text
logits
  |
softmax
  |
p_max
```

A partir de estos valores se probarán medidas de confianza como:

### Media de máxima probabilidad

```text
C_mean = mean(p_t)
```

### Mínimo de máxima probabilidad

```text
C_min = min(p_t)
```

### Log-probabilidad promedio

```text
C_log = mean(log(p_t))
```

### Entropía promedio

```text
C_entropy = mean(H_t)
```

### Margen top-1 / top-2

```text
C_margin = mean(p1_t - p2_t)
```

También se podrá estudiar posteriormente la confianza de las decisiones estructurales de SAN.

---

## 17. Estrategia para seleccionar el gate

En CROHME 2014 se guardará por expresión:

```text
sample_id
ground_truth
san_prediction
san_correct
san_confidence
san_time_ms
posformer_prediction
posformer_correct
posformer_time_ms
```

Después se podrá barrer el umbral offline:

```text
tau = 0.00 ... 1.00
```

sin volver a ejecutar los modelos.

Para cada umbral:

```text
si confianza SAN >= tau:
    usar SAN
si confianza SAN < tau:
    usar PosFormer
```

---

## 18. Baselines recomendados

Se planea comparar:

### 1. SAN solo

```text
100% SAN
0% PosFormer
```

### 2. PosFormer solo

```text
0% SAN
100% PosFormer
```

### 3. Cascada por confianza

```text
SAN siempre
PosFormer sólo cuando C < tau
```

### 4. Random routing

Enviar aleatoriamente a PosFormer el mismo porcentaje de muestras que la cascada.

Objetivo:

> demostrar que la mejora viene de la confianza y no simplemente de ejecutar PosFormer algunas veces.

### 5. Oracle

Usar ground truth únicamente como límite superior diagnóstico.

Objetivo:

> medir cuánto potencial de complementariedad existe entre SAN y PosFormer.

---

## 19. Métricas principales propuestas

### Precisión

```text
ExpRate / Exact Match
```

### Costo

```text
latencia media
latencia mediana
p95
```

### Escalamiento

```text
porcentaje enviado a PosFormer
```

### Curvas principales

```text
ExpRate vs % enviado a PosFormer
```

y:

```text
ExpRate vs latencia promedio
```

---

## 20. Fórmula aproximada de costo de la cascada

Si:

```text
T_SAN = costo medio de SAN
T_POS = costo medio de PosFormer
r     = fracción enviada a PosFormer
```

entonces:

```text
T_cascade ≈ T_SAN + r * T_POS
```

Con las medias medidas:

```text
T_SAN = 82.347 ms
T_POS = 318.188 ms
```

Para ser más rápida que PosFormer siempre:

```text
r < 1 - T_SAN / T_POS
```

Resultado aproximado:

```text
r < 0.7412
```

es decir:

```text
r < 74.12%
```

sin considerar todavía el costo del gate y preprocessing.

---

## 21. Riesgos / amenazas a la validez identificadas

### A. Diferencias de ground truth

Mitigación:

- usar una sola distribución para los tres sistemas;
- aplicar la misma normalización a todos;
- documentar explícitamente la diferencia de `\limits`.

### B. Diferencias de entrenamiento entre SAN y PosFormer

No invalidan el objetivo de la cascada porque ambos modelos se utilizan como checkpoints preentrenados y congelados.

No se afirmará que PosFormer es mejor que SAN exclusivamente por arquitectura.

### C. Selección del umbral sobre test

Mitigación:

```text
CROHME 2014 -> calibración
CROHME 2016 -> test
CROHME 2019 -> test
```

El umbral se congela antes de evaluar 2016/2019.

### D. Latencia dependiente de longitud y complejidad

Mitigación:

- medir sobre todo el conjunto;
- reportar media, mediana y p95;
- no depender de una sola imagen.

### E. Beam search de PosFormer

PosFormer tiene una distribución de latencia con cola larga.

Resultados observados:

```text
media   : 318.188 ms
mediana : 181.149 ms
p95     : 745.645 ms
```

Por tanto, conviene reportar más de una estadística de tiempo.

---

## 22. Scripts creados hasta ahora

### `01_seleccion/measure_vram.py`

Objetivo:

- cargar SAN + PosFormer simultáneamente;
- medir pesos;
- medir VRAM;
- medir una imagen;
- comparar latencias.

---

### `01_seleccion/benchmark_crohme.py`

Objetivo:

- recorrer CROHME 2014 completo;
- inferir SAN y PosFormer;
- guardar resultados por muestra;
- medir complementariedad;
- medir tiempos y VRAM.

Salida:

```text
01_seleccion/resultados/benchmark_crohme_2014.csv
```

---

### `02_adaptacion/compare_crohme_sources.py`

Objetivo:

- comparar las distribuciones SAN y PosFormer;
- verificar IDs;
- verificar ground truth;
- verificar imágenes;
- comparar predicciones oficiales.

Salidas:

```text
02_adaptacion/resultados/compare_crohme_sources_2014.csv
02_adaptacion/resultados/compare_crohme_sources_2014_summary.txt
```

---

### `02_adaptacion/analyze_ground_truth.py`

Objetivo:

- evaluar SAN y PosFormer cruzando GT SAN y GT PosFormer;
- cuantificar el sesgo introducido por cada convención.

Salidas:

```text
02_adaptacion/resultados/ground_truth_cross_evaluation_2014.csv
02_adaptacion/resultados/ground_truth_differences_2014.csv
02_adaptacion/resultados/ground_truth_analysis_2014_summary.txt
```

---

### `02_adaptacion/classify_ground_truth_differences.py`

Objetivo:

- clasificar las 85 discrepancias;
- encontrar patrones de tokens;
- identificar `\limits` como principal diferencia.

Salidas:

```text
02_adaptacion/resultados/ground_truth_difference_classification_2014.csv
02_adaptacion/resultados/ground_truth_token_changes_2014.csv
02_adaptacion/resultados/ground_truth_difference_classification_2014_summary.txt
```

---

### `02_adaptacion/analyze_limits_normalization.py`

Objetivo:

- probar exclusivamente la eliminación de `\limits`;
- medir cuánto se reconcilian los ground truths;
- recalcular Exact Match.

Salidas:

```text
02_adaptacion/resultados/limits_normalization_cross_evaluation_2014.csv
02_adaptacion/resultados/limits_normalization_residual_gt_differences_2014.csv
02_adaptacion/resultados/limits_normalization_2014_summary.txt
```

---

### `02_adaptacion/evaluate_san_symlg.py`

Objetivo:

- preparar las predicciones SAN para evaluación symLG/LgEval;
- extraer los ground truths `.lg`;
- intentar usar herramientas oficiales de CoMER.

Estado:

- preparación correcta;
- ejecución de LgEval pendiente por incompatibilidad Unix/Windows;
- no es requisito inmediato para continuar el TT.

---

## 23. Estado actual del proyecto

### Ya comprobado

- [x] SAN funciona en el entorno unificado.
- [x] PosFormer funciona en el entorno unificado.
- [x] PosFormer reproduce 62.74% en CROHME 2014.
- [x] SAN y PosFormer pueden coexistir en GPU.
- [x] SAN es significativamente más rápido.
- [x] Las imágenes SAN/PosFormer son idénticas.
- [x] La inferencia PosFormer del benchmark reproduce 985/985 predicciones oficiales.
- [x] Se detectaron y analizaron diferencias de ground truth.
- [x] Se identificó `\limits` como principal discrepancia.
- [x] Se comprobó complementariedad entre SAN y PosFormer.
- [x] Se definió CROHME 2014 como calibración.
- [x] Se reservan CROHME 2016 y 2019 como test final.

### Pendiente

- [ ] Congelar formalmente el protocolo de evaluación del TT.
- [ ] Modificar SAN para extraer confianza sin cambiar sus predicciones.
- [ ] Ejecutar SAN + PosFormer sobre CROHME 2014 guardando confianza.
- [ ] Comparar medidas de confianza.
- [ ] Seleccionar `tau`.
- [ ] Congelar gate.
- [ ] Evaluar SAN / PosFormer / Cascada en CROHME 2016.
- [ ] Evaluar SAN / PosFormer / Cascada en CROHME 2019.
- [ ] Comparar contra random routing.
- [ ] Reportar oracle.
- [ ] Construir curvas precisión-costo.

---

## 24. Próximo paso recomendado

El siguiente paso técnico es:

> **Modificar SAN de forma mínima para devolver estadísticas de confianza durante inferencia, sin alterar pesos ni predicción.**

Después, sobre CROHME 2014:

```text
SAN
 |
 +--> predicción
 |
 +--> p(token)
 |
 +--> métricas de confianza
```

Se guardarán las métricas por muestra y el diseño del gate podrá estudiarse completamente offline.

---

## 25. Formulación provisional de la contribución

> Se propone una arquitectura de inferencia dinámica en cascada para reconocimiento de expresiones matemáticas manuscritas, utilizando SAN como primera etapa y PosFormer como modelo de respaldo. La decisión de escalamiento se realiza mediante una medida de confianza obtenida directamente de las distribuciones de salida de SAN, manteniendo congelados los parámetros de ambos modelos preentrenados. La evaluación se realiza sobre conjuntos CROHME comunes y bajo un protocolo homogéneo, con CROHME 2014 como conjunto de calibración y CROHME 2016/2019 como conjuntos de prueba final.

---

## 26. Pregunta de investigación provisional

> ¿En qué medida una estrategia de enrutamiento basada en la confianza de SAN permite reducir el uso de PosFormer y el costo promedio de inferencia, manteniendo un desempeño cercano al modelo de mayor costo en reconocimiento de expresiones matemáticas manuscritas?

---

## 27. Hipótesis provisional

> Una arquitectura en cascada que utilice SAN como modelo de primera etapa y active PosFormer únicamente en muestras de baja confianza puede mantener una precisión cercana a PosFormer, con una reducción significativa del costo promedio de inferencia.

---

## 28. Nota para el protocolo escrito

Conviene distinguir claramente entre:

### Reproducción de modelos

Resultados obtenidos con los protocolos nativos de cada repositorio para verificar que los checkpoints funcionan.

### Evaluación del TT

Comparación de:

```text
SAN
PosFormer
Cascada
```

bajo:

```text
mismas muestras
mismo ground truth
misma métrica
mismo hardware
```

Esta separación evita confundir la reproducción de los papers con el protocolo experimental propio del Trabajo Terminal.

---

## 29. Prueba de symLG en WSL (2026-09-16)

Se ejecutó la cadena oficial de CoMER dentro de Ubuntu mediante WSL 2 en el mismo equipo Windows. Se instalaron Pandoc y el módulo Perl XML::LibXML, y se ajustaron a LF los scripts Bash necesarios. Una prueba con `18_em_0` convirtió la predicción SAN a symLG y LgEval reportó cero errores frente al grafo oficial.

### Evaluación SAN sobre CROHME 2014

- Predicciones SAN convertidas a symLG: **985/985**.
- Grafos oficiales comparados: **985/985**.
- Archivos vacíos o faltantes: **0**.
- ExpRate symLG de SAN: **546/985 = 55.43%**.
- Resumen oficial de LgEval: `02_adaptacion/resultados/san_symlg_eval_2014/Results_pred_symlg/Summary.txt`.

### ¿symLG reconcilia los ground truths SAN y PosFormer?

Se convirtieron por separado las dos anotaciones de cada una de las 85 muestras discrepantes y se compararon con LgEval:

| Tipo de discrepancia | Muestras | symLG iguales | symLG distintos |
|---|---:|---:|---:|
| Solo inserción de `\limits` | 79 | 0 | 79 |
| Otras diferencias | 6 | 0 | 6 |

En `18_em_5`, la anotación SAN representa el límite como relación `Sub`, mientras que la de PosFormer con `\limits` lo representa como `Below`. El symLG oficial de esa muestra coincide con la versión SAN. Por tanto, **la conversión a symLG no elimina automáticamente el sesgo de sintaxis causado por `\limits`**: en estos datos lo transforma en una diferencia estructural evaluada por LgEval.

La normalización uniforme del token `\limits` antes de Exact Match sigue siendo el criterio principal propuesto para el TT. symLG puede reportarse como métrica estructural complementaria, aclarando que mide otra representación y no reconcilia por sí sola las dos convenciones.

Archivos generados: `02_adaptacion/resultados/ground_truth_symlg_comparison_2014.csv` y `02_adaptacion/resultados/ground_truth_symlg_comparison_2014_summary.txt`.

---

## 30. Organización del proyecto (2026-09-20)

El trabajo de la cascada se agrupa en cuatro etapas: `01_seleccion` para pruebas de modelos candidatos, `02_adaptacion` para comparar y normalizar anotaciones y métricas, `03_analisis` para estudiar la confianza de SAN y elegir el criterio de enrutamiento, y `04_evaluacion` para medir la cascada final. Cada etapa contiene una carpeta `resultados` para sus salidas.

---

## 31. Comparación del conjunto BTTR con SAN y PosFormer (2026-09-20)

Se descargó el `data.zip` del repositorio oficial de BTTR y se extrajo en `data/BTTR`. La comparación por ID y anotación de `data/Modelo1` (SAN), `data/Modelo2` (PosFormer) y BTTR mostró que **BTTR 2014 coincide exactamente con SAN 2014**: 986/986 anotaciones y 986/986 archivos BMP. Por eso, BTTR reproduce las 85 diferencias de anotación frente a PosFormer observadas en 2014.

En 2016, BTTR y PosFormer comparten 1147 IDs e imágenes BMP idénticas; 76 anotaciones difieren solo por `\limits` y otras 50 siguen siendo distintas tras retirarlo. En 2019, comparten 1199 IDs; 96 difieren solo por `\limits` y 59 siguen siendo distintas. En 2019, **ninguno de los BMP de BTTR es idéntico al BMP correspondiente de PosFormer** y solo tres pares conservan las mismas dimensiones. La evaluación deberá usar imágenes y ground truth comunes.

El informe completo, los CSV por muestra y el script reproducible están en `02_adaptacion/resultados/comparacion_BTTR_SAN_PosFormer.md` y `02_adaptacion/compare_bttr_datasets.js`. Las etiquetas de BTTR 2019 pueden servir para estudiar la convención que coincide con SAN en 2014, sin atribuirle a SAN una publicación de etiquetas de 2019.

---

## 32. Comparación del conjunto TAMER (2026-09-20)

Se comparó el conjunto local `data/TAMER` con SAN, BTTR y PosFormer. **TAMER y PosFormer tienen `caption.txt` idénticos byte por byte y los mismos píxeles en todas las imágenes** del entrenamiento (8834) y de CROHME 2014 (986), 2016 (1147) y 2019 (1199). TAMER guarda las imágenes en `images.pkl`; PosFormer las guarda como BMP. No faltan IDs ni imágenes.

Frente a SAN 2014, TAMER presenta las mismas 85 diferencias de anotación que PosFormer: 79 debidas solo a `\limits` y 6 residuales, aunque las 986 imágenes son iguales. Frente a BTTR hay 85 diferencias de anotación en 2014, 126 en 2016 y 155 en 2019. En este último año ninguna imagen TAMER–BTTR tiene los mismos píxeles. En entrenamiento, BTTR tiene una muestra adicional (`MfrDB0104`); sobre las 8834 comunes hay 755 diferencias solo por `\limits` y 71 residuales, con píxeles idénticos.

El informe y los conteos reproducibles están en `02_adaptacion/resultados/comparacion_TAMER.md`, `02_adaptacion/resultados/tamer_datasets_summary.json` y `02_adaptacion/compare_tamer_datasets.js`. La coincidencia de datos permite una comparación TAMER–PosFormer con los mismos insumos, pero aún no mide complementariedad ni costo de los modelos.

---

## 33. Comparación del conjunto ABM (2026-09-20)

Se comparó `data/ABM` con SAN, BTTR y PosFormer. **ABM y BTTR tienen anotaciones idénticas byte por byte e imágenes con los mismos píxeles** en entrenamiento (8835 muestras) y en CROHME 2014 (986), 2016 (1147) y 2019 (1199). ABM utiliza archivos pickle con arreglos de imagen `1 × alto × ancho`; BTTR utiliza BMP. `offline-test.pkl` de ABM es copia exacta de `offline-2014-test.pkl`.

ABM coincide con SAN 2014 en las 986 anotaciones e imágenes. Frente a PosFormer/TAMER, reproduce las diferencias de BTTR: 85 anotaciones distintas en 2014, 126 en 2016 y 155 en 2019. En 2019, ningún par de imágenes ABM–PosFormer comparte píxeles idénticos. En entrenamiento, ABM/BTTR incluyen una muestra adicional, `MfrDB0104`, y en las 8834 muestras comunes con PosFormer/TAMER hay 755 diferencias solo por `\limits` y 71 residuales.

El informe, los CSV por muestra, los conteos y el script están en `02_adaptacion/resultados/comparacion_ABM.md`, `02_adaptacion/resultados/ABM-*-*.csv`, `02_adaptacion/resultados/abm_datasets_summary.json` y `02_adaptacion/compare_abm_datasets.js`.

---

## 34. Evaluación SAN y PosFormer sobre las mismas imágenes CROHME 2019 (2026-09-20)

Se ejecutaron los dos checkpoints congelados sobre los **1199 BMP de `data/Modelo2/2019/img`**, con el ground truth de `data/Modelo2/2019/caption.txt` y el preprocesamiento de inferencia propio de cada modelo. Se procesaron los 1199 IDs sin errores. PosFormer redimensionó internamente 12 imágenes; SAN procesó directamente todas las imágenes originales.

| Criterio | SAN | PosFormer | Oráculo |
|---|---:|---:|---:|
| Exact Match directo | 617/1199 (51.46 %) | 779/1199 (64.97 %) | 824/1199 (68.72 %) |
| Exact Match sin `\limits` | 651/1199 (54.30 %) | 779/1199 (64.97 %) | 826/1199 (68.89 %) |

Con la normalización uniforme de `\limits`, ambos acertaron 604 expresiones, solo SAN acertó 47, solo PosFormer 175 y ambos fallaron 373. La normalización recuperó 34 aciertos de SAN. El oráculo es un límite superior y no equivale a una cascada implementada. La latencia media de inferencia fue 104.336 ms para SAN y 311.136 ms para PosFormer, sin lectura ni preprocesamiento CPU.

Los resultados están en `04_evaluacion/resultados/evaluacion_crohme_2019_imagenes_comunes.md` y en los CSV/JSON de `04_evaluacion/resultados/benchmark_crohme_2019_common_images*`. El benchmark de `01_seleccion/benchmark_crohme.py` ahora admite `--year 2019`. Esta prueba demuestra el rendimiento de SAN sobre la rasterización de PosFormer 2019, pero no cuantifica la diferencia respecto de ejecutar SAN sobre la rasterización BTTR 2019 ni selecciona el umbral de la cascada.

---

## 35. SAN en los tres test de BTTR (2026-09-20)

Se ejecutó el checkpoint congelado de SAN sobre todos los BMP de BTTR 2014, 2016 y 2019, evaluando contra las anotaciones de BTTR. Hubo **0 errores de inferencia**.

| Test | Exact Match BTTR | Sin `\limits` |
|---|---:|---:|
| 2014 | 558/986 = 56.59 % | 558/986 = 56.59 % |
| 2016 | 594/1147 = 51.79 % | 594/1147 = 51.79 % |
| 2019 | 640/1199 = 53.38 % | 642/1199 = 53.54 % |

Las 986 predicciones de 2014 reproducen exactamente el benchmark anterior. Al evaluar las mismas predicciones con las anotaciones de PosFormer y quitar `\limits`, SAN obtiene 560/986 (56.80 %) en 2014, 615/1147 (53.62 %) en 2016 y 669/1199 (55.80 %) en 2019. Esto refleja el cambio de ground truth, no una nueva inferencia.

La comparación pareada de SAN en 2019 con BMP de BTTR y con BMP de PosFormer usa los mismos 1199 IDs, checkpoint y GT PosFormer normalizado: ambas imágenes producen un acierto en 536 casos, solo BTTR en 133, solo PosFormer en 115 y ninguna en 415. Así, SAN obtiene 669/1199 con las imágenes BTTR frente a 651/1199 con las imágenes PosFormer, **18 aciertos más** con BTTR. El análisis y las predicciones por muestra están en `04_evaluacion/resultados/evaluacion_SAN_BTTR_2014_2016_2019.md`, `04_evaluacion/resultados/san_bttr_*.csv` y `04_evaluacion/resultados/san_bttr_summary.json`.

Los scripts y resultados existentes se trasladaron a selección y adaptación según su función. Análisis y evaluación están preparados para los experimentos pendientes. Las rutas de entrada y salida de los scripts trasladados se actualizaron para esta estructura. Los directorios de SAN, PosFormer y CoMER siguen en la raíz del proyecto.
