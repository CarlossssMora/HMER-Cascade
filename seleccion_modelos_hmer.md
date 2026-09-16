# Selección preliminar de modelos para el Trabajo Terminal

## Objetivo

Este documento propone una estructura inicial para documentar la **búsqueda, filtrado y selección de modelos candidatos** para una arquitectura en cascada de reconocimiento de expresiones matemáticas manuscritas (HMER).

La selección se divide en dos roles:

- **Modelo de primera etapa:** debe priorizar bajo costo de inferencia, precisión razonable, reproducibilidad y posibilidad de obtener una medida de confianza.
- **Modelo de respaldo:** debe priorizar mayor precisión, capacidad de rescatar errores del modelo ligero, reproducibilidad y viabilidad computacional dentro del hardware disponible.

> **Nota:** Las tablas siguientes son una plantilla de trabajo. Los valores ya medidos para SAN y PosFormer provienen del entorno experimental actual del proyecto. Los demás modelos deben verificarse y, cuando sea posible, ejecutarse bajo el mismo protocolo antes de tomar una decisión final.

---

# 1. Modelos candidatos a considerar

| Modelo | Año | Rol candidato | Motivo para considerarlo | Prioridad preliminar |
|---|---:|---|---|---|
| **SAN** | 2022 | Ligero | Ya reproducido en el proyecto; baja latencia relativa; precisión razonable; permite extraer distribuciones de salida para estimar confianza | Muy alta |
| **CoMER** | 2022 | Ligero / intermedio | Transformer reproducible y referencia importante dentro de HMER; útil como punto intermedio entre modelos ligeros y más costosos | Muy alta |
| **ICAL** | 2024 | Intermedio / pesado | Modelo reciente con resultados competitivos; potencial candidato de respaldo | Alta |
| **TAMER** | 2025 | Pesado | Modelo reciente orientado a mejorar el reconocimiento estructural; candidato fuerte para respaldo | Muy alta |
| **PosFormer** | 2024 | Pesado | Ya reproducido; mayor precisión que SAN en el protocolo actual; costo de inferencia claramente superior | Muy alta |
| **NAMER** | 2024 | Ligero | Interesante por su enfoque no autorregresivo y orientación a inferencia rápida | Alta, sujeto a reproducibilidad |
| **CAN** | 2022 | Ligero / intermedio | Arquitectura contemporánea y potencialmente eficiente; útil como candidato comparativo | Media |
| **BTTR** | 2021 | Referencia / intermedio | Transformer relevante históricamente dentro de HMER; puede servir como punto de comparación | Media |
| **DWAP / DenseWAP-TD** | 2018–2020 | Referencia ligera | Modelo anterior y relativamente ligero; útil como antecedente histórico, aunque su implementación es más antigua | Baja / referencia |

---

# 2. Tabla de revisión y elegibilidad

Esta tabla documenta el proceso previo al benchmark. La intención es demostrar que la selección de SAN y PosFormer no fue arbitraria, sino resultado de una búsqueda de candidatos seguida de un filtro técnico y metodológico.

## Criterios de elegibilidad sugeridos

Un modelo puede pasar al benchmark si cumple, idealmente, con los siguientes criterios:

1. Evalúa sobre CROHME o puede adaptarse razonablemente a la misma distribución.
2. Existe código fuente disponible.
3. Existen pesos preentrenados o un checkpoint reproducible.
4. Puede ejecutarse en el hardware disponible.
5. Su entorno puede integrarse sin modificaciones desproporcionadas.
6. Su inferencia puede medirse bajo un protocolo comparable.
7. Su rol potencial dentro de la cascada está claramente definido.

## Plantilla

| Modelo | Año | CROHME | Código disponible | Checkpoint disponible | Compatible / adaptable al entorno | Ejecutable en RTX 4050 6 GB | Rol potencial | Pasa a benchmark | Motivo / observaciones |
|---|---:|---|---|---|---|---|---|---|---|
| **SAN** | 2022 | Sí | Sí | Sí | Sí | Sí | Ligero | **Sí** | Ya reproducido en Python 3.8.10 + PyTorch 2.0.1+cu118 |
| **CoMER** | 2022 | Sí | Sí | Sí | Por verificar | Por verificar | Ligero / intermedio | **Candidato** | Conviene probarlo por ser una referencia Transformer reproducible |
| **ICAL** | 2024 | Sí | Sí | Sí | Por verificar | Por verificar | Intermedio / pesado | **Candidato** | Evaluar compatibilidad y costo real de inferencia |
| **TAMER** | 2025 | Sí | Sí | Sí | Por verificar | Por verificar | Pesado | **Candidato** | Candidato reciente para modelo de respaldo |
| **PosFormer** | 2024 | Sí | Sí | Sí | Sí | Sí | Pesado | **Sí** | Ya reproducido y validado en el entorno unificado |
| **NAMER** | 2024 | Sí | Por verificar | Por verificar | Por verificar | Por verificar | Ligero | **Condicionado** | Interesante por velocidad, pero depende de disponibilidad reproducible de implementación y pesos |
| **CAN** | 2022 | Sí | Sí | Por verificar | Por verificar | Por verificar | Ligero / intermedio | **Condicionado** | Verificar checkpoint y facilidad de reproducción |
| **BTTR** | 2021 | Sí | Por verificar | Por verificar | Por verificar | Por verificar | Intermedio / referencia | **Opcional** | Puede aportar contexto, pero no es prioritario si aumenta demasiado el alcance |
| **DWAP / DenseWAP-TD** | 2018–2020 | Sí | Por verificar | Por verificar | Potencialmente antigua | Por verificar | Ligero / referencia | **Opcional** | Útil principalmente como antecedente histórico de modelos ligeros |

### Posibles estados para la columna “Pasa a benchmark”

- **Sí:** ya es reproducible y debe incluirse.
- **Candidato:** parece viable y conviene intentar reproducirlo.
- **Condicionado:** depende de disponibilidad de pesos, compatibilidad o esfuerzo de integración.
- **Opcional:** puede omitirse si no añade suficiente valor al análisis.
- **No:** descartado por falta de reproducibilidad, incompatibilidad o inviabilidad computacional.

---

# 3. Tabla de benchmark de candidatos reproducibles

Esta tabla debe llenarse **únicamente con los modelos que superen la etapa de revisión y elegibilidad**.

Idealmente, todos los valores deben obtenerse bajo:

- el mismo hardware;
- las mismas muestras;
- el mismo ground truth;
- la misma métrica de Exact Match / ExpRate;
- un protocolo homogéneo de medición de latencia;
- un criterio consistente de preprocesamiento y exclusión del tiempo de CPU;
- versiones de software documentadas.

## Plantilla de benchmark

| Modelo | Rol candidato | ExpRate / Exact Match (%) | Latencia media (ms) | Mediana (ms) | p95 (ms) | Parámetros (M) | Pesos + buffers (MiB) | Pico VRAM (MiB) | GFLOPs / muestra | Observaciones |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| **SAN** | Ligero | 56.85* | 82.347 | 80.073 | 154.263 | 7.996 | 30.55 | Por consolidar | Por medir | Actualmente es el candidato principal para primera etapa |
| **CoMER** | Ligero / intermedio | — | — | — | — | — | — | — | — | Pendiente de reproducción homogénea |
| **ICAL** | Intermedio / pesado | — | — | — | — | — | — | — | — | Pendiente de reproducción homogénea |
| **TAMER** | Pesado | — | — | — | — | — | — | — | — | Pendiente de reproducción homogénea |
| **PosFormer** | Pesado | 62.74* | 318.188 | 181.149 | 745.645 | 9.632 | 37.77 | Por consolidar | Por medir | Actualmente es el candidato principal para respaldo |

\* Valores correspondientes al protocolo común normalizado actualmente utilizado en el proyecto.

---

## 3.1 Métricas mínimas recomendadas

Para la selección final conviene considerar como mínimo:

### Precisión
- ExpRate / Exact Match.

### Costo temporal
- Latencia media.
- Mediana.
- p95.

### Complejidad y memoria
- Número de parámetros.
- Tamaño de pesos y buffers.
- Pico de VRAM.
- GFLOPs por muestra, si puede medirse de manera consistente.

### Reproducibilidad
- Código disponible.
- Checkpoint disponible.
- Dependencias compatibles.
- Facilidad de integración dentro del entorno experimental.

### Adecuación al rol

Para el modelo ligero:

- baja latencia;
- precisión suficiente;
- costo bajo;
- capacidad de generar una medida de confianza útil.

Para el modelo pesado:

- mayor precisión;
- capacidad de rescatar errores del modelo ligero;
- costo suficientemente mayor como para justificar no ejecutarlo siempre;
- viabilidad de mantenerse residente en GPU.

---

# 4. Posible criterio de selección final

La elección no debería reducirse a seleccionar el modelo con menor latencia y el modelo con mayor precisión de forma independiente.

Para la primera etapa interesa un equilibrio entre:

```text
precisión
+ baja latencia
+ reproducibilidad
+ confianza utilizable
+ bajo costo de inferencia
```

Para el modelo de respaldo interesa:

```text
precisión superior
+ complementariedad con el modelo ligero
+ reproducibilidad
+ costo computacional justificadamente mayor
+ viabilidad en GPU
```

La pareja final debe ser adecuada para estudiar la pregunta central del TT:

> ¿Puede una cascada de modelos preentrenados reducir el costo promedio de inferencia manteniendo un desempeño cercano al modelo de mayor costo?

---

# 5. Estructura metodológica sugerida

```text
Revisión bibliográfica de modelos HMER
                |
                v
      Identificación de candidatos
                |
                v
      Revisión de elegibilidad
   - código
   - checkpoint
   - CROHME
   - compatibilidad
   - recursos
                |
                v
   Benchmark de modelos reproducibles
   - ExpRate
   - latencia media
   - mediana
   - p95
   - parámetros
   - VRAM
   - GFLOPs
                |
                v
       Selección por rol
        /              \
       /                \
modelo ligero       modelo pesado
       \                /
        \              /
         v            v
         Arquitectura en cascada
```

---

## Estado preliminar

Actualmente, SAN y PosFormer ya cuentan con evidencia experimental suficiente para considerarse candidatos fuertes:

- SAN funciona como candidato ligero por su menor costo de inferencia.
- PosFormer funciona como candidato pesado por su mayor precisión y mayor costo computacional.
- Ambos pueden permanecer simultáneamente cargados en GPU.
- Existe complementariedad entre sus predicciones.

Sin embargo, antes de presentar la selección como definitiva, conviene intentar reproducir algunos candidatos adicionales —principalmente **CoMER, ICAL y TAMER**— y documentar explícitamente por qué otros modelos fueron descartados o no llegaron a la etapa de benchmark.
