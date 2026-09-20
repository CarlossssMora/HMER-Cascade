import os
import sys
import gc
import glob
import time
from pathlib import Path

import cv2
import torch
import torchvision.transforms as tvt


# ============================================================
# Configuración general
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

SAN_DIR = ROOT / "SAN"
POSFORMER_DIR = ROOT / "PosFormer"

if not torch.cuda.is_available():
    raise RuntimeError("CUDA no está disponible.")

DEVICE = torch.device("cuda")

MB = 1024 ** 2

# Número de inferencias previas antes de medir.
WARMUP_RUNS = 3


# ============================================================
# Utilidades CUDA / memoria
# ============================================================

def sync():
    torch.cuda.synchronize()


def report_vram(title):
    sync()

    allocated = torch.cuda.memory_allocated() / MB
    reserved = torch.cuda.memory_reserved() / MB
    peak = torch.cuda.max_memory_allocated() / MB

    free, total = torch.cuda.mem_get_info()

    print()
    print("=" * 60)
    print(title)
    print("=" * 60)

    print(
        "Allocated : {:10.2f} MiB".format(
            allocated
        )
    )

    print(
        "Reserved  : {:10.2f} MiB".format(
            reserved
        )
    )

    print(
        "Peak      : {:10.2f} MiB".format(
            peak
        )
    )

    print(
        "GPU free  : {:10.2f} MiB".format(
            free / MB
        )
    )

    print(
        "GPU total : {:10.2f} MiB".format(
            total / MB
        )
    )


def model_size(model):

    param_bytes = sum(
        p.numel() * p.element_size()
        for p in model.parameters()
    )

    buffer_bytes = sum(
        b.numel() * b.element_size()
        for b in model.buffers()
    )

    return param_bytes, buffer_bytes


def report_model_size(name, model):

    params, buffers = model_size(model)

    n_params = sum(
        p.numel()
        for p in model.parameters()
    )

    print()
    print(name)

    print(
        "  Parámetros : {:,}".format(
            n_params
        )
    )

    print(
        "  Pesos      : {:.2f} MiB".format(
            params / MB
        )
    )

    print(
        "  Buffers    : {:.2f} MiB".format(
            buffers / MB
        )
    )

    print(
        "  Total      : {:.2f} MiB".format(
            (params + buffers) / MB
        )
    )


# ============================================================
# Warm-up
# ============================================================

def warmup(name, inference_fn, runs=WARMUP_RUNS):

    print()
    print("=" * 60)
    print("WARM-UP {}".format(name))
    print("=" * 60)

    print(
        "Ejecuciones: {}".format(
            runs
        )
    )

    with torch.inference_mode():

        for _ in range(runs):

            output = inference_fn()

            sync()

            del output

    gc.collect()

    sync()


# ============================================================
# Benchmark de inferencia
# ============================================================

def benchmark_inference(name, inference_fn):
    """
    Mide la inferencia del modelo.

    Los datos ya deben estar preparados y transferidos a GPU.

    Incluye:
      - ejecución CUDA
      - lógica Python del decoder
      - beam search cuando corresponda

    No incluye:
      - lectura de disco
      - preprocessing CPU
    """

    gc.collect()

    sync()

    baseline = torch.cuda.memory_allocated()

    torch.cuda.reset_peak_memory_stats()

    sync()

    start = time.perf_counter()

    with torch.inference_mode():

        output = inference_fn()

    sync()

    elapsed_ms = (
        time.perf_counter()
        - start
    ) * 1000.0

    peak = torch.cuda.max_memory_allocated()

    final = torch.cuda.memory_allocated()

    print()
    print("=" * 60)
    print("BENCHMARK {}".format(name))
    print("=" * 60)

    print(
        "Tiempo       : {:10.3f} ms".format(
            elapsed_ms
        )
    )

    print(
        "Base VRAM    : {:10.2f} MiB".format(
            baseline / MB
        )
    )

    print(
        "Pico VRAM    : {:10.2f} MiB".format(
            peak / MB
        )
    )

    print(
        "Incremento   : {:10.2f} MiB".format(
            (peak - baseline) / MB
        )
    )

    print(
        "Final VRAM   : {:10.2f} MiB".format(
            final / MB
        )
    )

    return {
        "output": output,
        "time_ms": elapsed_ms,
        "baseline": baseline,
        "peak": peak,
        "final": final,
    }


# ============================================================
# Conversión SAN -> LaTeX
#
# Basada en la función convert() del inference.py oficial
# ============================================================

def san_convert(nodeid, gtd_list):

    isparent = False

    child_list = []

    for i in range(len(gtd_list)):

        if gtd_list[i][2] == nodeid:

            isparent = True

            child_list.append(
                [
                    gtd_list[i][0],
                    gtd_list[i][1],
                    gtd_list[i][3],
                ]
            )

    if not isparent:

        return [
            gtd_list[nodeid][0]
        ]

    # ========================================================
    # Caso especial: fracción
    # ========================================================

    if gtd_list[nodeid][0] == "\\frac":

        return_string = [
            gtd_list[nodeid][0]
        ]

        # Numerador
        for i in range(len(child_list)):

            if child_list[i][2] == "Above":

                return_string += (
                    ["{"]
                    + san_convert(
                        child_list[i][1],
                        gtd_list
                    )
                    + ["}"]
                )

        # Denominador
        for i in range(len(child_list)):

            if child_list[i][2] == "Below":

                return_string += (
                    ["{"]
                    + san_convert(
                        child_list[i][1],
                        gtd_list
                    )
                    + ["}"]
                )

        # Elementos a la derecha
        for i in range(len(child_list)):

            if child_list[i][2] == "Right":

                return_string += san_convert(
                    child_list[i][1],
                    gtd_list
                )

        # Relaciones inesperadas
        for i in range(len(child_list)):

            if child_list[i][2] not in [
                "Right",
                "Above",
                "Below",
            ]:

                return_string += [
                    "illegal"
                ]

        return return_string

    # ========================================================
    # Símbolos generales
    # ========================================================

    return_string = [
        gtd_list[nodeid][0]
    ]

    # l_sup
    for i in range(len(child_list)):

        if child_list[i][2] in [
            "l_sup"
        ]:

            return_string += (
                ["["]
                + san_convert(
                    child_list[i][1],
                    gtd_list
                )
                + ["]"]
            )

    # Inside
    for i in range(len(child_list)):

        if child_list[i][2] == "Inside":

            return_string += (
                ["{"]
                + san_convert(
                    child_list[i][1],
                    gtd_list
                )
                + ["}"]
            )

    # Subíndice
    for i in range(len(child_list)):

        if child_list[i][2] in [
            "Sub",
            "Below",
        ]:

            return_string += (
                ["_", "{"]
                + san_convert(
                    child_list[i][1],
                    gtd_list
                )
                + ["}"]
            )

    # Superíndice
    for i in range(len(child_list)):

        if child_list[i][2] in [
            "Sup",
            "Above",
        ]:

            return_string += (
                ["^", "{"]
                + san_convert(
                    child_list[i][1],
                    gtd_list
                )
                + ["}"]
            )

    # Derecha
    for i in range(len(child_list)):

        if child_list[i][2] in [
            "Right"
        ]:

            return_string += san_convert(
                child_list[i][1],
                gtd_list
            )

    return return_string


# ============================================================
# Inicio
# ============================================================

print("=" * 60)
print("INICIO")
print("=" * 60)

print(
    "Python  :",
    sys.version.split()[0]
)

print(
    "PyTorch :",
    torch.__version__
)

print(
    "GPU     :",
    torch.cuda.get_device_name(0)
)


torch.cuda.empty_cache()

torch.cuda.reset_peak_memory_stats()


report_vram(
    "1. CUDA inicial"
)


# ============================================================
# Cargar SAN
# ============================================================

print()
print("Cargando SAN...")


sys.path.insert(
    0,
    str(SAN_DIR)
)


old_cwd = os.getcwd()


try:

    os.chdir(
        SAN_DIR
    )

    from utils import load_config, load_checkpoint
    from infer.Backbone import Backbone
    from dataset import Words


    params = load_config(
        "14.yaml"
    )


    params["device"] = DEVICE


    words = Words(
        params["word_path"]
    )


    params["word_num"] = len(
        words
    )

    params["struct_num"] = 7

    params["words"] = words


    san = Backbone(
        params
    )


    san = san.to(
        DEVICE
    )


    load_checkpoint(
        san,
        None,
        params["checkpoint"]
    )


finally:

    os.chdir(
        old_cwd
    )


san.eval()

san.requires_grad_(
    False
)


report_model_size(
    "SAN",
    san
)


report_vram(
    "2. SAN cargado"
)


# ============================================================
# Cargar PosFormer
# ============================================================

print()
print("Cargando PosFormer...")


sys.path.insert(
    0,
    str(POSFORMER_DIR)
)


from Pos_Former.lit_posformer import LitPosFormer

from Pos_Former.datamodule.transforms import (
    ScaleToLimitRange
)

from Pos_Former.datamodule import vocab


# ============================================================
# Buscar checkpoint
# ============================================================

checkpoints = glob.glob(
    str(
        POSFORMER_DIR
        / "lightning_logs"
        / "version_0"
        / "checkpoints"
        / "*.ckpt"
    )
)


if not checkpoints:

    raise FileNotFoundError(
        "No encontré ningún checkpoint de PosFormer."
    )


# Preferir best.ckpt
best = [
    p
    for p in checkpoints
    if Path(p).name == "best.ckpt"
]


if best:

    checkpoint = best[0]

else:

    checkpoint = checkpoints[0]


print()
print("Checkpoint PosFormer:")
print(checkpoint)


# ============================================================
# Cargar primero en CPU
# ============================================================

posformer = LitPosFormer.load_from_checkpoint(
    checkpoint,
    map_location="cpu"
)


posformer = posformer.to(
    DEVICE
)


posformer.eval()


posformer.requires_grad_(
    False
)


report_model_size(
    "PosFormer",
    posformer
)


report_vram(
    "3. SAN + PosFormer cargados simultáneamente"
)


# ============================================================
# Seleccionar imagen de CROHME
# ============================================================

label_file = (
    SAN_DIR
    / "data"
    / "test_caption.txt"
)


image_dir = (
    SAN_DIR
    / "data"
    / "14_test_images"
)


with open(
    label_file,
    encoding="utf-8"
) as f:

    first_line = (
        f.readline()
        .strip()
    )


if not first_line:

    raise RuntimeError(
        "test_caption.txt está vacío."
    )


parts = first_line.split()


name = parts[0]


ground_truth = " ".join(
    parts[1:]
)


if name.endswith(
    ".jpg"
):

    name = name.split(
        "."
    )[0]


image_path = (
    image_dir
    / "{}_0.bmp".format(
        name
    )
)


print()
print("=" * 60)
print("IMAGEN DE PRUEBA")
print("=" * 60)


print("Archivo:")

print(
    image_path
)


print()

print(
    "Ground truth:"
)

print(
    ground_truth
)


# ============================================================
# Leer la imagen UNA sola vez
# ============================================================

img = cv2.imread(
    str(
        image_path
    )
)


if img is None:

    raise FileNotFoundError(
        "No se pudo cargar la imagen:\n{}".format(
            image_path
        )
    )


img = cv2.cvtColor(
    img,
    cv2.COLOR_BGR2GRAY
)


original_h, original_w = (
    img.shape
)


print()

print(
    "Dimensiones originales: {} x {}".format(
        original_h,
        original_w
    )
)


# ============================================================
# Preparar entrada SAN
#
# Igual al inference.py oficial:
#
# grayscale -> Tensor -> /255 -> [1,1,H,W]
# mask = unos
# ============================================================

san_image = (
    torch.Tensor(
        img
    )
    / 255.0
)


san_image = (
    san_image
    .unsqueeze(0)
    .unsqueeze(0)
)


san_mask = torch.ones(
    san_image.shape
)


san_image = san_image.to(
    DEVICE
)


san_mask = san_mask.to(
    DEVICE
)


print()

print(
    "Tensor SAN       :",
    tuple(
        san_image.shape
    )
)


print(
    "Rango SAN        : {:.4f} a {:.4f}".format(
        san_image.min().item(),
        san_image.max().item()
    )
)


# ============================================================
# Preparar entrada PosFormer
#
# Pipeline oficial de test:
#
# ScaleToLimitRange
# ToTensor
# ============================================================

pos_transform = tvt.Compose(
    [
        ScaleToLimitRange(
            w_lo=16,
            w_hi=1024,
            h_lo=16,
            h_hi=256,
        ),

        tvt.ToTensor(),
    ]
)


# Partimos exactamente de la misma imagen grayscale
pos_image = pos_transform(
    img
)


# [1,H,W] -> [1,1,H,W]
pos_image = pos_image.unsqueeze(
    0
)


_, _, pos_h, pos_w = (
    pos_image.shape
)


# ============================================================
# Máscara PosFormer
#
# False = región válida
# True  = padding
#
# Como tenemos batch_size = 1 y no hay padding:
# toda la máscara es False
# ============================================================

pos_mask = torch.zeros(
    (
        1,
        pos_h,
        pos_w,
    ),
    dtype=torch.bool
)


pos_image = pos_image.to(
    DEVICE
)


pos_mask = pos_mask.to(
    DEVICE
)


print()

print(
    "Tensor PosFormer :",
    tuple(
        pos_image.shape
    )
)


print(
    "Máscara PosFormer: {} {}".format(
        tuple(
            pos_mask.shape
        ),
        pos_mask.dtype
    )
)


print(
    "Rango PosFormer  : {:.4f} a {:.4f}".format(
        pos_image.min().item(),
        pos_image.max().item()
    )
)


# ============================================================
# Verificar resize de PosFormer
# ============================================================

if (
    original_h != pos_h
    or original_w != pos_w
):

    print()

    print(
        "PosFormer redimensionó la imagen:"
    )

    print(
        "  {} x {} -> {} x {}".format(
            original_h,
            original_w,
            pos_h,
            pos_w
        )
    )

else:

    print()

    print(
        "PosFormer NO necesitó redimensionar esta imagen."
    )


# ============================================================
# Estado antes de inferencia
# ============================================================

report_vram(
    "4. Ambos modelos + entradas preparados"
)


# ============================================================
# Warm-up SAN
# ============================================================

warmup(
    "SAN",

    lambda: san(
        san_image,
        san_mask
    )
)


# ============================================================
# Benchmark SAN
# ============================================================

san_result = benchmark_inference(

    "SAN",

    lambda: san(
        san_image,
        san_mask
    )
)


san_prediction = (
    san_result["output"]
)


# ============================================================
# Convertir SAN a LaTeX
# ============================================================

san_latex = " ".join(
    san_convert(
        1,
        san_prediction
    )
)


print()

print(
    "Predicción SAN:"
)

print(
    san_latex
)


# ============================================================
# Warm-up PosFormer
# ============================================================

warmup(

    "PosFormer",

    lambda: posformer.approximate_joint_search(
        pos_image,
        pos_mask
    )
)


# ============================================================
# Benchmark PosFormer
# ============================================================

pos_result = benchmark_inference(

    "PosFormer",

    lambda: posformer.approximate_joint_search(
        pos_image,
        pos_mask
    )
)


pos_hyps = (
    pos_result["output"]
)


# ============================================================
# Convertir PosFormer a LaTeX
# ============================================================

if (
    pos_hyps is not None
    and len(pos_hyps) > 0
):

    pos_latex = vocab.indices2label(
        pos_hyps[0].seq
    )

else:

    pos_latex = (
        "<sin hipótesis>"
    )


print()

print(
    "Predicción PosFormer:"
)

print(
    pos_latex
)


# ============================================================
# Exact Match contra Ground Truth
# ============================================================

san_correct = (
    san_latex.strip()
    ==
    ground_truth.strip()
)


pos_correct = (
    pos_latex.strip()
    ==
    ground_truth.strip()
)


# ============================================================
# Incrementos de VRAM
# ============================================================

san_increment = (
    san_result["peak"]
    - san_result["baseline"]
) / MB


pos_increment = (
    pos_result["peak"]
    - pos_result["baseline"]
) / MB


# ============================================================
# Resultados
# ============================================================

print()
print()

print("=" * 60)
print("RESULTADOS")
print("=" * 60)


print()

print(
    "Imagen:"
)

print(
    image_path.name
)


print()

print(
    "Ground truth:"
)

print(
    ground_truth
)


# ============================================================
# SAN
# ============================================================

print()

print("-" * 60)
print("SAN")
print("-" * 60)


print(
    "Predicción:"
)

print(
    san_latex
)


print()


print(
    "Correcta     : {}".format(
        "SÍ"
        if san_correct
        else "NO"
    )
)


print(
    "Tiempo       : {:.3f} ms".format(
        san_result[
            "time_ms"
        ]
    )
)


print(
    "Base VRAM    : {:.2f} MiB".format(
        san_result[
            "baseline"
        ] / MB
    )
)


print(
    "Pico VRAM    : {:.2f} MiB".format(
        san_result[
            "peak"
        ] / MB
    )
)


print(
    "Incremento   : {:.2f} MiB".format(
        san_increment
    )
)


# ============================================================
# PosFormer
# ============================================================

print()

print("-" * 60)
print("PosFormer")
print("-" * 60)


print(
    "Predicción:"
)

print(
    pos_latex
)


print()


print(
    "Correcta     : {}".format(
        "SÍ"
        if pos_correct
        else "NO"
    )
)


print(
    "Tiempo       : {:.3f} ms".format(
        pos_result[
            "time_ms"
        ]
    )
)


print(
    "Base VRAM    : {:.2f} MiB".format(
        pos_result[
            "baseline"
        ] / MB
    )
)


print(
    "Pico VRAM    : {:.2f} MiB".format(
        pos_result[
            "peak"
        ] / MB
    )
)


print(
    "Incremento   : {:.2f} MiB".format(
        pos_increment
    )
)


# ============================================================
# Comparación directa
# ============================================================

san_time = (
    san_result[
        "time_ms"
    ]
)


pos_time = (
    pos_result[
        "time_ms"
    ]
)


print()

print("=" * 60)
print("COMPARACIÓN")
print("=" * 60)


if san_time > 0:

    ratio = (
        pos_time
        / san_time
    )

    print(
        "PosFormer / SAN (tiempo): {:.2f}x".format(
            ratio
        )
    )


if pos_time > 0:

    saving = (
        1.0
        - san_time / pos_time
    ) * 100.0

    print(
        "SAN tarda aproximadamente {:.2f}% "
        "menos que PosFormer".format(
            saving
        )
    )


print()


print(
    "SAN correcto       :",
    san_correct
)


print(
    "PosFormer correcto :",
    pos_correct
)


# ============================================================
# Referencia para futura cascada
# ============================================================

print()

print("=" * 60)
print("CASCADA - REFERENCIA")
print("=" * 60)


print(
    "T_SAN       = {:.3f} ms".format(
        san_time
    )
)


print(
    "T_PosFormer = {:.3f} ms".format(
        pos_time
    )
)


if pos_time > 0:

    max_routing = (
        1.0
        - san_time / pos_time
    )

    print()

    print(
        "Fracción teórica máxima aproximada "
        "enviada a PosFormer"
    )

    print(
        "para que la cascada siga siendo más "
        "rápida que PosFormer solo:"
    )

    print(
        "r < {:.4f}".format(
            max_routing
        )
    )

    print(
        "r < {:.2f}%".format(
            max_routing
            * 100.0
        )
    )

    print(
        "(ignorando por ahora el costo del gate)"
    )


# ============================================================
# Liberar únicamente outputs
#
# Los modelos continúan residentes en GPU
# ============================================================

del san_prediction

san_result[
    "output"
] = None


del pos_hyps

pos_result[
    "output"
] = None


gc.collect()

sync()


# ============================================================
# Estado final
# ============================================================

report_vram(
    "5. Estado final: "
    "SAN + PosFormer continúan residentes"
)


free, total = (
    torch.cuda.mem_get_info()
)


print()

print("=" * 60)
print("RESUMEN FINAL")
print("=" * 60)


print(
    "VRAM física total : {:.2f} MiB".format(
        total / MB
    )
)


print(
    "VRAM libre final  : {:.2f} MiB".format(
        free / MB
    )
)


print()

print(
    "SAN y PosFormer continúan cargados en GPU."
)
