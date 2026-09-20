# Cascada para reconocimiento de expresiones matemáticas manuscritas

Este proyecto estudia una arquitectura en cascada para el reconocimiento de expresiones matemáticas manuscritas (HMER). Un modelo ligero procesa cada imagen primero; cuando su confianza es baja, la muestra pasa a un modelo de respaldo. El objetivo es comparar la precisión y el costo de inferencia bajo un mismo protocolo experimental.

Actualmente se ha probado SAN como modelo ligero y PosFormer como candidato de respaldo. CoMER se conserva como implementación y conjunto de herramientas de referencia. La elección final del modelo pesado y de la medida de confianza sigue abierta.

## Organización

- [`SAN/`](SAN/), [`PosFormer/`](PosFormer/) y [`CoMER/`](CoMER/): implementaciones de los modelos y herramientas originales.
- [`Cascada/01_seleccion/`](Cascada/01_seleccion/): pruebas de carga, memoria, velocidad y viabilidad de modelos candidatos.
- [`Cascada/02_adaptacion/`](Cascada/02_adaptacion/): comparación y normalización de anotaciones, y métricas de los modelos bajo un criterio común.
- [`Cascada/03_analisis/`](Cascada/03_analisis/): comparación de medidas de confianza de SAN y selección del criterio de enrutamiento.
- [`Cascada/04_evaluacion/`](Cascada/04_evaluacion/): evaluación final de precisión y costo de la cascada frente a sus modelos base.

Cada etapa guarda sus salidas en su propia carpeta `resultados/`. Las etapas 03 y 04 están preparadas para el trabajo pendiente.

El procedimiento, las decisiones y los resultados obtenidos se documentan en el [registro de avances](Cascada/registro_avances_TT_SAN_PosFormer.md). La [revisión de modelos candidatos](Cascada/01_seleccion/seleccion_modelos_hmer.md) reúne los criterios preliminares de selección.

## Entorno y datos

Los archivos `requirements-*.txt` de la raíz describen los entornos utilizados. Los conjuntos de datos y checkpoints permanecen dentro de los directorios de los modelos. Los scripts de `Cascada/` resuelven las rutas de esos archivos desde la ubicación del proyecto.
