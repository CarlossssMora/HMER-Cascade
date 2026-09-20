import os
import sys
import gc
import glob
import csv
import time
import statistics
from pathlib import Path

import cv2
import torch
import torchvision.transforms as tvt


# ============================================================
# Configuracion
# ============================================================

ROOT = Path(__file__).resolve().parents[2]
SAN_DIR = ROOT / "SAN"
POSFORMER_DIR = ROOT / "PosFormer"

DEVICE = torch.device("cuda")
MB = 1024 ** 2

OUTPUT_CSV = Path(__file__).resolve().parent / "resultados" / "benchmark_crohme_2014.csv"
WARMUP_RUNS = 3
PROGRESS_EVERY = 25

# None = todo el conjunto.
# Para una prueba corta puede cambiarse temporalmente a 10.
MAX_SAMPLES = None


# ============================================================
# Utilidades
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
    print("=" * 70)
    print(title)
    print("=" * 70)
    print("Allocated : {:10.2f} MiB".format(allocated))
    print("Reserved  : {:10.2f} MiB".format(reserved))
    print("Peak      : {:10.2f} MiB".format(peak))
    print("GPU free  : {:10.2f} MiB".format(free / MB))
    print("GPU total : {:10.2f} MiB".format(total / MB))


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
    n_params = sum(p.numel() for p in model.parameters())

    print()
    print(name)
    print("  Parametros : {:,}".format(n_params))
    print("  Pesos      : {:.2f} MiB".format(params / MB))
    print("  Buffers    : {:.2f} MiB".format(buffers / MB))
    print("  Total      : {:.2f} MiB".format((params + buffers) / MB))


def percentile(values, percent):
    if not values:
        return float("nan")

    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]

    position = (len(ordered) - 1) * (percent / 100.0)
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower

    return (
        ordered[lower] * (1.0 - fraction)
        + ordered[upper] * fraction
    )


def benchmark_inference(inference_fn):
    """
    Mide solo inferencia: los tensores de entrada ya deben estar en GPU.
    No incluye lectura de disco ni preprocessing CPU.
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
    elapsed_ms = (time.perf_counter() - start) * 1000.0

    peak = torch.cuda.max_memory_allocated()
    final = torch.cuda.memory_allocated()

    return {
        "output": output,
        "time_ms": elapsed_ms,
        "baseline": baseline,
        "peak": peak,
        "final": final,
    }


def warmup(inference_fn, runs):
    with torch.inference_mode():
        for _ in range(runs):
            output = inference_fn()
            sync()
            del output

    gc.collect()
    sync()


# ============================================================
# Conversion de salida SAN a secuencia LaTeX
# ============================================================

def san_prediction_to_latex(prediction):
    if prediction is None or len(prediction) <= 1:
        return "<sin prediccion>"

    children = {}

    for item in prediction:
        if len(item) < 4:
            continue

        try:
            node_id = int(item[1])
            parent_id = int(item[2])
        except (TypeError, ValueError):
            continue

        relation = str(item[3])
        children.setdefault(parent_id, []).append(
            (node_id, relation)
        )

    def walk(node_id):
        if node_id < 0 or node_id >= len(prediction):
            return ["<invalid>"]

        symbol = str(prediction[node_id][0])
        kids = children.get(node_id, [])

        if not kids:
            return [symbol]

        result = [symbol]

        if symbol == "\\frac":
            for child_id, relation in kids:
                if relation == "Above":
                    result += ["{"] + walk(child_id) + ["}"]

            for child_id, relation in kids:
                if relation == "Below":
                    result += ["{"] + walk(child_id) + ["}"]

            for child_id, relation in kids:
                if relation == "Right":
                    result += walk(child_id)

            for _, relation in kids:
                if relation not in ("Above", "Below", "Right"):
                    result.append("illegal")

            return result

        for child_id, relation in kids:
            if relation == "l_sup":
                result += ["["] + walk(child_id) + ["]"]

        for child_id, relation in kids:
            if relation == "Inside":
                result += ["{"] + walk(child_id) + ["}"]

        for child_id, relation in kids:
            if relation in ("Sub", "Below"):
                result += ["_", "{"] + walk(child_id) + ["}"]

        for child_id, relation in kids:
            if relation in ("Sup", "Above"):
                result += ["^", "{"] + walk(child_id) + ["}"]

        for child_id, relation in kids:
            if relation == "Right":
                result += walk(child_id)

        return result

    try:
        return " ".join(walk(1))
    except Exception as exc:
        return "<error SAN: {}>".format(exc)


# ============================================================
# Carga de una muestra
# ============================================================

def parse_label_line(line):
    parts = line.strip().split()

    if not parts:
        return None

    raw_name = parts[0]
    ground_truth = " ".join(parts[1:])

    name = raw_name
    if name.endswith(".jpg"):
        name = name.split(".")[0]

    return name, ground_truth


def load_grayscale(image_path):
    img = cv2.imread(str(image_path))

    if img is None:
        raise FileNotFoundError(
            "No se pudo cargar {}".format(image_path)
        )

    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


# ============================================================
# Preparacion de entradas
# ============================================================

def prepare_san_input(img):
    image = torch.Tensor(img) / 255.0
    image = image.unsqueeze(0).unsqueeze(0)
    mask = torch.ones(image.shape)

    return image.to(DEVICE), mask.to(DEVICE)


def prepare_posformer_input(img, transform):
    original_h, original_w = img.shape

    image = transform(img)
    image = image.unsqueeze(0)

    _, _, pos_h, pos_w = image.shape

    mask = torch.zeros(
        (1, pos_h, pos_w),
        dtype=torch.bool
    )

    resized = (
        original_h != pos_h
        or original_w != pos_w
    )

    return (
        image.to(DEVICE),
        mask.to(DEVICE),
        pos_h,
        pos_w,
        resized,
    )


# ============================================================
# Inicio
# ============================================================

if not torch.cuda.is_available():
    raise RuntimeError("CUDA no esta disponible.")

print("=" * 70)
print("BENCHMARK CROHME 2014: SAN vs PosFormer")
print("=" * 70)
print("Python  : {}".format(sys.version.split()[0]))
print("PyTorch : {}".format(torch.__version__))
print("GPU     : {}".format(torch.cuda.get_device_name(0)))
print("CSV     : {}".format(OUTPUT_CSV))


torch.cuda.empty_cache()
torch.cuda.reset_peak_memory_stats()


# ============================================================
# Cargar SAN
# ============================================================

print()
print("Cargando SAN...")

sys.path.insert(0, str(SAN_DIR))
old_cwd = os.getcwd()

try:
    os.chdir(SAN_DIR)

    from utils import load_config, load_checkpoint
    from infer.Backbone import Backbone
    from dataset import Words

    params = load_config("14.yaml")
    params["device"] = DEVICE

    words = Words(params["word_path"])
    params["word_num"] = len(words)
    params["struct_num"] = 7
    params["words"] = words

    san = Backbone(params)
    san = san.to(DEVICE)

    load_checkpoint(
        san,
        None,
        params["checkpoint"]
    )

finally:
    os.chdir(old_cwd)

san.eval()
san.requires_grad_(False)

report_model_size("SAN", san)


# ============================================================
# Cargar PosFormer
# ============================================================

print()
print("Cargando PosFormer...")

sys.path.insert(0, str(POSFORMER_DIR))

from Pos_Former.lit_posformer import LitPosFormer
from Pos_Former.datamodule.transforms import ScaleToLimitRange
from Pos_Former.datamodule import vocab

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
        "No encontre checkpoint de PosFormer."
    )

best = [
    path
    for path in checkpoints
    if Path(path).name == "best.ckpt"
]

checkpoint = best[0] if best else checkpoints[0]

print("Checkpoint PosFormer:")
print(checkpoint)

posformer = LitPosFormer.load_from_checkpoint(
    checkpoint,
    map_location="cpu"
)

posformer = posformer.to(DEVICE)
posformer.eval()
posformer.requires_grad_(False)

report_model_size("PosFormer", posformer)
report_vram("SAN + PosFormer cargados")


# ============================================================
# Transform oficial de evaluacion de PosFormer
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


# ============================================================
# Leer lista CROHME 2014 desde SAN
# ============================================================

label_file = SAN_DIR / "data" / "test_caption.txt"
image_dir = SAN_DIR / "data" / "14_test_images"

with open(label_file, "r", encoding="utf-8") as handle:
    label_lines = [
        line.strip()
        for line in handle
        if line.strip()
    ]

if MAX_SAMPLES is not None:
    label_lines = label_lines[:MAX_SAMPLES]

if not label_lines:
    raise RuntimeError("No hay muestras para evaluar.")

print()
print("Muestras a evaluar: {}".format(len(label_lines)))


# ============================================================
# Warm-up unico para cada modelo usando la primera muestra
# ============================================================

first_parsed = parse_label_line(label_lines[0])
first_name = first_parsed[0]
first_path = image_dir / "{}_0.bmp".format(first_name)
first_img = load_grayscale(first_path)

print()
print("Warm-up SAN: {} ejecuciones".format(WARMUP_RUNS))

warm_san_image, warm_san_mask = prepare_san_input(first_img)

warmup(
    lambda: san(warm_san_image, warm_san_mask),
    WARMUP_RUNS
)

del warm_san_image
del warm_san_mask
gc.collect()
sync()

print("Warm-up PosFormer: {} ejecuciones".format(WARMUP_RUNS))

(
    warm_pos_image,
    warm_pos_mask,
    _,
    _,
    _,
) = prepare_posformer_input(first_img, pos_transform)

warmup(
    lambda: posformer.approximate_joint_search(
        warm_pos_image,
        warm_pos_mask
    ),
    WARMUP_RUNS
)

del warm_pos_image
del warm_pos_mask
del first_img
gc.collect()
sync()

report_vram("Despues del warm-up")


# ============================================================
# CSV
# ============================================================

fieldnames = [
    "index",
    "sample_id",
    "image_file",
    "status",
    "error",
    "height",
    "width",
    "posformer_height",
    "posformer_width",
    "posformer_resized",
    "ground_truth",
    "san_prediction",
    "san_correct",
    "san_time_ms",
    "san_base_mib",
    "san_peak_total_mib",
    "san_peak_increment_mib",
    "posformer_prediction",
    "posformer_correct",
    "posformer_time_ms",
    "posformer_base_mib",
    "posformer_peak_total_mib",
    "posformer_peak_increment_mib",
    "outcome",
]

san_times = []
pos_times = []
san_peaks = []
pos_peaks = []
time_ratios = []

both_correct = 0
san_only = 0
posformer_only = 0
both_wrong = 0
resized_count = 0
error_count = 0


# ============================================================
# Benchmark completo
# ============================================================

print()
print("=" * 70)
print("INICIANDO BENCHMARK")
print("=" * 70)

with open(
    OUTPUT_CSV,
    "w",
    newline="",
    encoding="utf-8"
) as csv_file:

    writer = csv.DictWriter(
        csv_file,
        fieldnames=fieldnames
    )
    writer.writeheader()

    for index, line in enumerate(label_lines, start=1):
        parsed = parse_label_line(line)

        if parsed is None:
            continue

        name, ground_truth = parsed
        image_path = image_dir / "{}_0.bmp".format(name)

        row = {
            "index": index,
            "sample_id": name,
            "image_file": image_path.name,
            "status": "",
            "error": "",
            "height": "",
            "width": "",
            "posformer_height": "",
            "posformer_width": "",
            "posformer_resized": "",
            "ground_truth": ground_truth,
            "san_prediction": "",
            "san_correct": "",
            "san_time_ms": "",
            "san_base_mib": "",
            "san_peak_total_mib": "",
            "san_peak_increment_mib": "",
            "posformer_prediction": "",
            "posformer_correct": "",
            "posformer_time_ms": "",
            "posformer_base_mib": "",
            "posformer_peak_total_mib": "",
            "posformer_peak_increment_mib": "",
            "outcome": "",
        }

        try:
            img = load_grayscale(image_path)
            height, width = img.shape

            row["height"] = height
            row["width"] = width

            # ------------------------------------------------
            # SAN
            # ------------------------------------------------

            san_image, san_mask = prepare_san_input(img)

            san_result = benchmark_inference(
                lambda: san(san_image, san_mask)
            )

            san_prediction_raw = san_result["output"]
            san_prediction = san_prediction_to_latex(
                san_prediction_raw
            )

            san_correct_flag = (
                san_prediction.strip()
                == ground_truth.strip()
            )

            san_increment = (
                san_result["peak"]
                - san_result["baseline"]
            ) / MB

            row["san_prediction"] = san_prediction
            row["san_correct"] = int(san_correct_flag)
            row["san_time_ms"] = "{:.6f}".format(
                san_result["time_ms"]
            )
            row["san_base_mib"] = "{:.6f}".format(
                san_result["baseline"] / MB
            )
            row["san_peak_total_mib"] = "{:.6f}".format(
                san_result["peak"] / MB
            )
            row["san_peak_increment_mib"] = "{:.6f}".format(
                san_increment
            )

            current_san_time = san_result["time_ms"]
            current_san_peak = san_increment

            san_result["output"] = None
            del san_prediction_raw
            del san_image
            del san_mask
            del san_result

            gc.collect()
            sync()

            # ------------------------------------------------
            # PosFormer
            # ------------------------------------------------

            (
                pos_image,
                pos_mask,
                pos_h,
                pos_w,
                pos_resized,
            ) = prepare_posformer_input(
                img,
                pos_transform
            )

            row["posformer_height"] = pos_h
            row["posformer_width"] = pos_w
            row["posformer_resized"] = int(pos_resized)

            pos_result = benchmark_inference(
                lambda: posformer.approximate_joint_search(
                    pos_image,
                    pos_mask
                )
            )

            pos_hyps = pos_result["output"]

            if pos_hyps is not None and len(pos_hyps) > 0:
                pos_prediction = vocab.indices2label(
                    pos_hyps[0].seq
                )
            else:
                pos_prediction = "<sin hipotesis>"

            pos_correct_flag = (
                pos_prediction.strip()
                == ground_truth.strip()
            )

            pos_increment = (
                pos_result["peak"]
                - pos_result["baseline"]
            ) / MB

            row["posformer_prediction"] = pos_prediction
            row["posformer_correct"] = int(pos_correct_flag)
            row["posformer_time_ms"] = "{:.6f}".format(
                pos_result["time_ms"]
            )
            row["posformer_base_mib"] = "{:.6f}".format(
                pos_result["baseline"] / MB
            )
            row["posformer_peak_total_mib"] = "{:.6f}".format(
                pos_result["peak"] / MB
            )
            row["posformer_peak_increment_mib"] = "{:.6f}".format(
                pos_increment
            )

            current_pos_time = pos_result["time_ms"]
            current_pos_peak = pos_increment

            pos_result["output"] = None
            del pos_hyps
            del pos_image
            del pos_mask
            del pos_result
            del img

            gc.collect()
            sync()

            # ------------------------------------------------
            # Complementariedad
            # ------------------------------------------------

            if san_correct_flag and pos_correct_flag:
                outcome = "both_correct"
                both_correct += 1

            elif san_correct_flag and not pos_correct_flag:
                outcome = "san_only"
                san_only += 1

            elif (not san_correct_flag) and pos_correct_flag:
                outcome = "posformer_only"
                posformer_only += 1

            else:
                outcome = "both_wrong"
                both_wrong += 1

            row["outcome"] = outcome
            row["status"] = "ok"

            san_times.append(current_san_time)
            pos_times.append(current_pos_time)
            san_peaks.append(current_san_peak)
            pos_peaks.append(current_pos_peak)

            if current_san_time > 0:
                time_ratios.append(
                    current_pos_time / current_san_time
                )

            if pos_resized:
                resized_count += 1

        except Exception as exc:
            error_count += 1
            row["status"] = "error"
            row["error"] = repr(exc)

            print()
            print(
                "ERROR en muestra {} ({}): {}".format(
                    index,
                    name,
                    exc
                )
            )

            # Un OOM CUDA puede dejar el proceso en un estado poco fiable.
            if "out of memory" in str(exc).lower():
                writer.writerow(row)
                csv_file.flush()
                raise

            gc.collect()
            sync()

        writer.writerow(row)
        csv_file.flush()

        if (
            index == 1
            or index % PROGRESS_EVERY == 0
            or index == len(label_lines)
        ):
            valid_so_far = (
                both_correct
                + san_only
                + posformer_only
                + both_wrong
            )

            if valid_so_far > 0:
                san_right_so_far = both_correct + san_only
                pos_right_so_far = both_correct + posformer_only

                san_rate = san_right_so_far / valid_so_far
                pos_rate = pos_right_so_far / valid_so_far

                print(
                    "[{}/{}] validas={} errores={} | "
                    "SAN={:.4f} PosFormer={:.4f}".format(
                        index,
                        len(label_lines),
                        valid_so_far,
                        error_count,
                        san_rate,
                        pos_rate
                    )
                )


# ============================================================
# Resumen
# ============================================================

valid_count = (
    both_correct
    + san_only
    + posformer_only
    + both_wrong
)

print()
print("=" * 70)
print("RESUMEN FINAL")
print("=" * 70)
print("Muestras solicitadas : {}".format(len(label_lines)))
print("Muestras validas      : {}".format(valid_count))
print("Errores                : {}".format(error_count))
print("CSV                    : {}".format(OUTPUT_CSV))

if valid_count > 0:
    san_correct_count = both_correct + san_only
    pos_correct_count = both_correct + posformer_only
    oracle_correct_count = valid_count - both_wrong

    san_exprate = san_correct_count / valid_count
    pos_exprate = pos_correct_count / valid_count
    oracle_exprate = oracle_correct_count / valid_count

    print()
    print("Exact Match / ExpRate")
    print("  SAN        : {:.4f} ({}/{})".format(
        san_exprate,
        san_correct_count,
        valid_count
    ))
    print("  PosFormer  : {:.4f} ({}/{})".format(
        pos_exprate,
        pos_correct_count,
        valid_count
    ))
    print("  Oracle     : {:.4f} ({}/{})".format(
        oracle_exprate,
        oracle_correct_count,
        valid_count
    ))

    print()
    print("Complementariedad")
    print("  Ambos correctos : {:5d} ({:6.2f}%)".format(
        both_correct,
        100.0 * both_correct / valid_count
    ))
    print("  Solo SAN        : {:5d} ({:6.2f}%)".format(
        san_only,
        100.0 * san_only / valid_count
    ))
    print("  Solo PosFormer  : {:5d} ({:6.2f}%)".format(
        posformer_only,
        100.0 * posformer_only / valid_count
    ))
    print("  Ambos fallan    : {:5d} ({:6.2f}%)".format(
        both_wrong,
        100.0 * both_wrong / valid_count
    ))

    if san_correct_count < valid_count:
        san_wrong_count = valid_count - san_correct_count
        rescue_rate = posformer_only / san_wrong_count

        print()
        print(
            "PosFormer rescata {:.2f}% de los errores de SAN "
            "({}/{})".format(
                100.0 * rescue_rate,
                posformer_only,
                san_wrong_count
            )
        )

    print()
    print("Resize PosFormer")
    print("  Redimensionadas : {} / {} ({:.2f}%)".format(
        resized_count,
        valid_count,
        100.0 * resized_count / valid_count
    ))

if san_times and pos_times:
    san_mean = statistics.mean(san_times)
    san_median = statistics.median(san_times)
    san_p95 = percentile(san_times, 95.0)

    pos_mean = statistics.mean(pos_times)
    pos_median = statistics.median(pos_times)
    pos_p95 = percentile(pos_times, 95.0)

    print()
    print("Latencia de inferencia (preprocessing CPU excluido)")
    print("  SAN")
    print("    media   : {:.3f} ms".format(san_mean))
    print("    mediana : {:.3f} ms".format(san_median))
    print("    p95     : {:.3f} ms".format(san_p95))

    print("  PosFormer")
    print("    media   : {:.3f} ms".format(pos_mean))
    print("    mediana : {:.3f} ms".format(pos_median))
    print("    p95     : {:.3f} ms".format(pos_p95))

    if san_mean > 0:
        print()
        print(
            "PosFormer / SAN usando medias: {:.2f}x".format(
                pos_mean / san_mean
            )
        )

    if time_ratios:
        print(
            "Mediana del ratio por muestra: {:.2f}x".format(
                statistics.median(time_ratios)
            )
        )

    if pos_mean > 0:
        r_max = 1.0 - (san_mean / pos_mean)

        print()
        print("Referencia teorica para la cascada")
        print("  r_max aproximado: {:.4f} ({:.2f}%)".format(
            r_max,
            100.0 * r_max
        ))
        print(
            "  Usa latencias medias y no incluye gate ni preprocessing."
        )

if san_peaks and pos_peaks:
    print()
    print("Pico incremental de VRAM")
    print("  SAN media       : {:.2f} MiB".format(
        statistics.mean(san_peaks)
    ))
    print("  SAN maximo      : {:.2f} MiB".format(
        max(san_peaks)
    ))
    print("  PosFormer media : {:.2f} MiB".format(
        statistics.mean(pos_peaks)
    ))
    print("  PosFormer maximo: {:.2f} MiB".format(
        max(pos_peaks)
    ))

report_vram("Estado final de GPU")

print()
print("Benchmark terminado.")
