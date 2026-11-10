# Instrucciones para Codex — Trabajo Terminal HMER

## 1. Propósito y fuente metodológica

Este repositorio desarrolla y evalúa una **arquitectura de inferencia en cascada** para el reconocimiento de expresiones matemáticas manuscritas (*Handwritten Mathematical Expression Recognition*, HMER).

**Antes de iniciar cualquier tarea de análisis, implementación, depuración, refactorización o evaluación, lee `METODOLOGIA_CASCADA.md` y consulta las subsecciones relacionadas con el trabajo solicitado.** Este documento es la referencia metodológica principal del proyecto. Vuelve a consultarlo cuando una decisión técnica afecte el diseño experimental, las métricas, el enrutamiento o la interpretación de resultados.

Si el archivo no existe o no se puede leer, informa de ello antes de tomar decisiones metodológicas. Si una instrucción puntual del usuario difiere del documento, indica la discrepancia y pide confirmación antes de modificar el diseño científico. No alteres silenciosamente la metodología.

## 2. Resumen del diseño que debe respetarse

- **Arquitectura de dos etapas:** un modelo ligero predice primero y el modelo de mayor capacidad procesa de forma independiente la **imagen original** solo cuando corresponde derivar la muestra. La segunda predicción **sustituye** a la primera; no se fusionan salidas.
- **Modelos preliminares:** SAN como modelo ligero y PosFormer como modelo de mayor capacidad. Su asignación definitiva depende de la caracterización experimental. No supongas que esta elección ya quedó validada si el código o los resultados no lo demuestran.
- **Pesos preentrenados:** no entrenar, afinar ni modificar parámetros de los modelos, salvo autorización explícita y actualización metodológica acordada.
- **Conjuntos de datos:** CROHME 2014 se usa para desarrollo, comparación de estrategias, cálculo de parámetros Min-Max y definición de umbrales. CROHME 2016 y CROHME 2019 quedan reservados para evaluación final **sin reajustar parámetros ni umbrales**.
- **Compatibilización:** verificar identificadores, imágenes y referencias. Cualquier normalización de LaTeX debe ser conservadora, limitarse a la comparación y no modificar el significado matemático ni las relaciones estructurales.
- **Confianza de SAN:** obtener probabilidades de decisiones de símbolos y relaciones estructurales de la decodificación, excluyendo elementos de relleno. No usar las expresiones de referencia para calcular las puntuaciones de confianza durante la inferencia.
- **Relaciones estructurales:** la estrategia principal contempla tanto relaciones aceptadas como descartadas: `p` para aceptadas y `1 - p` para descartadas, según el umbral de decisión descrito en la metodología. Las alternativas de análisis deben conservarse separadas de la estrategia principal.
- **Medidas de confianza:** Chow-Sum, Chow-Average y Chow-Quantile-0, calculadas por separado para símbolos y relaciones, y combinadas de acuerdo con las reglas de `METODOLOGIA_CASCADA.md`.
- **Combinación principal:** normalización Min-Max independiente por fuente y medida, seguida del promedio de símbolos y relaciones con pesos iguales. Los mínimos y máximos se calculan **solo en CROHME 2014**, permanecen fijos y pueden producir valores fuera de `[0, 1]` en la evaluación final. Si mínimo = máximo, usar `0.5`. Respetar la regla documentada cuando no existan decisiones estructurales definidas.
- **Umbrales:** percentiles del 1 al 99 de las puntuaciones en CROHME 2014, además de los extremos de aceptación total y derivación total. No escoger un único umbral óptimo a partir de CROHME 2016/2019.
- **Evaluación:** ExpRate, métricas `≤ 1` y `≤ 2`, tasa de derivación, tiempo de inferencia y memoria. Distinguir los tiempos **estimados a partir de registros** de los **medidos con ejecuciones reales**.
- **Referencias:** comparar con ambos modelos individuales, derivación aleatoria con la misma cantidad de muestras derivadas y múltiples semillas, y un *oracle* que maximice aciertos para una cantidad fija de derivaciones. El *oracle* puede usar etiquetas únicamente para construir un límite superior experimental, nunca para tomar decisiones de inferencia real.

Este resumen es una guía rápida; **si hay alguna diferencia de detalle o una omisión, prevalece el texto íntegro de `METODOLOGIA_CASCADA.md`**.

## 3. Reglas de implementación y reproducibilidad

1. **Inspecciona el código existente antes de cambiarlo.** Identifica estructura, puntos de entrada, configuración, formatos de entrada/salida, dependencias y pruebas disponibles; no inventes rutas ni interfaces.
2. Implementa cambios **pequeños, verificables y trazables**, sin reescribir componentes no relacionados ni introducir dependencias nuevas sin justificarlo.
3. Mantén separadas las fases de: inferencia individual, extracción de probabilidades, cálculo de confianza, ajuste de parámetros en CROHME 2014, simulación de decisiones de derivación y evaluación final.
4. Conserva registros por expresión siempre que aplique: identificador, conjunto CROHME, referencia para evaluación, predicciones de ambos modelos, probabilidades disponibles de SAN, confianza por medida, decisión de derivación y tiempos individuales. Nunca confundas etiquetas de evaluación con entradas permitidas al enrutador.
5. Fija y registra semillas cuando se emplee aleatoriedad. Documenta hardware, software, versiones relevantes, condiciones de ejecución y configuración experimental.
6. Para medir tiempos en GPU, realiza calentamiento y sincronización según corresponda; registra mediciones repetidas e informa promedio, mediana y percentil 95. No presentes estimaciones como tiempos medidos.
7. Para los métodos de referencia aleatorios, utiliza el **mismo número de derivaciones** que la configuración de la cascada y resume promedio y variabilidad entre semillas.
8. Asegura que la evaluación final no filtre información de CROHME 2016/2019 al cálculo de normalizadores, selección de umbrales o elección de estrategias.
9. Si un detalle no está especificado (por ejemplo, formatos exactos, semillas o número de repeticiones), no lo presentes como decisión metodológica ya aprobada. Propón una opción razonable y márcala como pendiente de validación.

## 4. Validación antes de dar una tarea por terminada

- Ejecuta las pruebas pertinentes disponibles; si faltan, crea pruebas acotadas cuando proceda y sea viable.
- Comprueba expresamente los casos límite relevantes: confianza sin relaciones estructurales, denominador Min-Max nulo, valores fuera de `[0, 1]`, extremos de derivación 0 % y 100 %, empates y cantidades fijas de derivaciones.
- Verifica que las predicciones y las métricas se calculen con la **misma correspondencia de muestras** en ambos modelos.
- No afirmes que un resultado experimental fue obtenido si no fue ejecutado. Distingue entre código implementado, validación local, resultados reales y resultados esperados.

## 5. Forma de trabajar y reportar cambios

- Responde y documenta preferentemente **en español**; conserva los nombres técnicos, símbolos matemáticos, nombres de modelos y API cuando corresponda.
- Antes de una modificación significativa, indica qué subsección de `METODOLOGIA_CASCADA.md` la fundamenta y cuál será el alcance del cambio.
- Después de cada tarea, resume archivos modificados, comportamiento implementado, pruebas ejecutadas y asuntos pendientes o discrepancias detectadas.
- No edites `METODOLOGIA_CASCADA.md` ni cambies supuestos experimentales sin solicitud expresa. Si detectas inconsistencias, **repórtalas con ubicación precisa y una propuesta**, en vez de corregirlas unilateralmente.
- No elimines datos, resultados o archivos existentes sin autorización. No subas credenciales, datos privados ni artefactos pesados al control de versiones.

## 6. Referencia operativa

Archivo central: [`METODOLOGIA_CASCADA.md`](METODOLOGIA_CASCADA.md)

Este `AGENTS.md` define cómo debe trabajar Codex dentro del proyecto; la metodología define **qué debe implementarse y cómo debe evaluarse**. Ambos archivos deben mantenerse juntos, preferentemente en la raíz del repositorio.
