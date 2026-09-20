import csv
import io
import os
import sys
import zipfile
from pathlib import Path

import cv2
import numpy as np


# ============================================================
# Configuracion
# ============================================================

ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = Path(__file__).resolve().parent / "resultados"

SAN_DIR = ROOT / "SAN"
POSFORMER_DIR = ROOT / "PosFormer"

YEAR = "2014"

SAN_CAPTION = SAN_DIR / "data" / "test_caption.txt"
SAN_IMAGE_DIR = SAN_DIR / "data" / "14_test_images"

POS_DATA_ZIP = POSFORMER_DIR / "data_crohme.zip"

BENCHMARK_CSV = ROOT / "Cascada" / "01_seleccion" / "resultados" / "benchmark_crohme_2014.csv"

OUTPUT_CSV = RESULTS_DIR / "compare_crohme_sources_2014.csv"
OUTPUT_SUMMARY = RESULTS_DIR / "compare_crohme_sources_2014_summary.txt"

# Reglas del data_iterator oficial de PosFormer
POS_MAX_LABEL_LEN = 200
POS_MAX_IMAGE_AREA = 320000


# ============================================================
# Utilidades
# ============================================================

def normalize_ws(text):
    return " ".join(str(text).strip().split())


def canonical_id(name):
    """
    Normaliza un ID sin alterar sufijos que puedan ser
    semanticamente relevantes, por ejemplo '18_em_0'.
    """
    name = str(name).replace("\\", "/")
    name = name.rsplit("/", 1)[-1]

    lower = name.lower()

    for ext in [".jpg", ".jpeg", ".png", ".bmp", ".txt", ".inkml"]:
        if lower.endswith(ext):
            name = name[:-len(ext)]
            break

    return name


def read_text_auto(raw_bytes):
    for encoding in ["utf-8", "utf-8-sig", "latin-1"]:
        try:
            return raw_bytes.decode(encoding)
        except UnicodeDecodeError:
            pass

    return raw_bytes.decode("utf-8", errors="replace")


def decode_gray_from_bytes(raw_bytes):
    arr = np.frombuffer(raw_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)

    if img is None:
        raise RuntimeError("OpenCV no pudo decodificar una imagen BMP del ZIP.")

    return img


def load_gray_from_disk(path):
    img = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)

    if img is None:
        raise FileNotFoundError(
            "No se pudo leer la imagen SAN: {}".format(path)
        )

    return img


def find_result_zip():
    candidates = [
        POSFORMER_DIR / "result.zip",
        ROOT / "result.zip",
        POSFORMER_DIR / "Pos_Former" / "result.zip",
    ]

    for path in candidates:
        if path.exists():
            return path

    found = []

    for base in [POSFORMER_DIR, ROOT]:
        if base.exists():
            try:
                for path in base.rglob("result.zip"):
                    if path.is_file():
                        found.append(path)
            except Exception:
                pass

    if not found:
        return None

    found = sorted(
        set(found),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )

    return found[0]


def locate_posformer_year_dir(zip_f, year):
    """
    El repositorio oficial espera:
        data/{year}/caption.txt
        data/{year}/img/{id}.bmp

    Aun asi, se busca de forma robusta por si el ZIP tiene
    un prefijo adicional.
    """
    names = zip_f.namelist()

    exact = "data/{}/caption.txt".format(year)

    if exact in names:
        return "data/{}".format(year)

    suffix = "/{}/caption.txt".format(year)

    matches = [
        name
        for name in names
        if name.endswith(suffix)
    ]

    if len(matches) == 1:
        return matches[0][:-len("/caption.txt")]

    # Ultimo intento: cualquier caption.txt cuyo padre termine en YEAR
    matches = []

    for name in names:
        normalized = name.rstrip("/")
        if not normalized.endswith("/caption.txt"):
            continue

        parent = normalized.rsplit("/", 1)[0]
        if parent.rsplit("/", 1)[-1] == str(year):
            matches.append(parent)

    matches = sorted(set(matches))

    if len(matches) == 1:
        return matches[0]

    raise RuntimeError(
        "No pude identificar de forma unica el directorio de CROHME {} "
        "dentro de data_crohme.zip.\nCandidatos: {}".format(
            year,
            matches
        )
    )


def resolve_san_image(sample_id, benchmark_row=None):
    candidates = []

    if benchmark_row is not None:
        image_file = benchmark_row.get("image_file", "").strip()
        if image_file:
            candidates.append(SAN_IMAGE_DIR / image_file)

    candidates.extend([
        SAN_IMAGE_DIR / "{}_0.bmp".format(sample_id),
        SAN_IMAGE_DIR / "{}.bmp".format(sample_id),
    ])

    seen = set()

    for path in candidates:
        key = str(path).lower()

        if key in seen:
            continue

        seen.add(key)

        if path.exists():
            return path

    return None


def parse_pos_result_text(text):
    """
    result.zip oficial:
        %sample_id
        $prediccion$
    """
    lines = text.splitlines()

    if not lines:
        return ""

    body = "\n".join(lines[1:]).strip()

    if body.startswith("$") and body.endswith("$") and len(body) >= 2:
        body = body[1:-1]

    return normalize_ws(body)


def bool_from_csv(value):
    return str(value).strip().lower() in [
        "true", "1", "yes", "si", "sí"
    ]


def pct(n, d):
    if d == 0:
        return 0.0
    return 100.0 * float(n) / float(d)


# ============================================================
# Verificar archivos
# ============================================================

print("=" * 72)
print("COMPARACION DE FUENTES CROHME 2014")
print("=" * 72)

required = [
    SAN_CAPTION,
    POS_DATA_ZIP,
    BENCHMARK_CSV,
]

for path in required:
    if not path.exists():
        raise FileNotFoundError(
            "No existe el archivo requerido:\n{}".format(path)
        )

RESULT_ZIP = find_result_zip()

if RESULT_ZIP is None:
    raise FileNotFoundError(
        "No encontre result.zip de la evaluacion oficial de PosFormer.\n"
        "Ejecuta primero su test oficial y conserva el result.zip generado."
    )

print("SAN captions       :", SAN_CAPTION)
print("SAN images         :", SAN_IMAGE_DIR)
print("PosFormer dataset  :", POS_DATA_ZIP)
print("PosFormer result   :", RESULT_ZIP)
print("Benchmark conjunto :", BENCHMARK_CSV)


# ============================================================
# Leer benchmark conjunto
# ============================================================

benchmark = {}

with open(BENCHMARK_CSV, "r", encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)

    for row in reader:
        if row.get("status", "ok").strip().lower() not in ["ok", ""]:
            continue

        sid = canonical_id(row["sample_id"])
        benchmark[sid] = row

print()
print("Filas validas benchmark conjunto:", len(benchmark))


# ============================================================
# Leer SAN captions
# ============================================================

san_labels = {}
san_raw_ids = {}

with open(SAN_CAPTION, "r", encoding="utf-8") as f:
    for line in f:
        parts = line.strip().split()

        if not parts:
            continue

        raw_id = parts[0]
        sid = canonical_id(raw_id)
        label = normalize_ws(" ".join(parts[1:]))

        san_labels[sid] = label
        san_raw_ids[sid] = raw_id

print("Muestras SAN caption             :", len(san_labels))


# ============================================================
# Leer PosFormer data_crohme.zip
# ============================================================

pos_labels = {}
pos_image_members = {}
pos_sizes = {}
pos_filtered_reason = {}

with zipfile.ZipFile(POS_DATA_ZIP, "r") as zf:
    pos_year_dir = locate_posformer_year_dir(zf, YEAR)
    caption_member = "{}/caption.txt".format(pos_year_dir)

    caption_text = read_text_auto(zf.read(caption_member))

    for line in caption_text.splitlines():
        parts = line.strip().split()

        if not parts:
            continue

        raw_id = parts[0]
        sid = canonical_id(raw_id)
        label_tokens = parts[1:]
        label = normalize_ws(" ".join(label_tokens))

        image_member = "{}/img/{}.bmp".format(
            pos_year_dir,
            raw_id
        )

        if image_member not in zf.namelist():
            # Intento usando ID canonico
            image_member_alt = "{}/img/{}.bmp".format(
                pos_year_dir,
                sid
            )

            if image_member_alt in zf.namelist():
                image_member = image_member_alt
            else:
                raise FileNotFoundError(
                    "No encontre imagen PosFormer para {} dentro del ZIP.".format(
                        raw_id
                    )
                )

        raw_img = zf.read(image_member)
        img = decode_gray_from_bytes(raw_img)
        h, w = img.shape

        pos_labels[sid] = label
        pos_image_members[sid] = image_member
        pos_sizes[sid] = (h, w)

        reasons = []

        if len(label_tokens) > POS_MAX_LABEL_LEN:
            reasons.append("label_len>{}".format(POS_MAX_LABEL_LEN))

        if h * w > POS_MAX_IMAGE_AREA:
            reasons.append("area>{}".format(POS_MAX_IMAGE_AREA))

        if reasons:
            pos_filtered_reason[sid] = ";".join(reasons)

print("Muestras PosFormer caption       :", len(pos_labels))
print("Filtradas por data_iterator      :", len(pos_filtered_reason))

if pos_filtered_reason:
    for sid in sorted(pos_filtered_reason):
        h, w = pos_sizes[sid]
        print(
            "  {} -> {} | {}x{} | tokens={}".format(
                sid,
                pos_filtered_reason[sid],
                h,
                w,
                len(pos_labels[sid].split())
            )
        )


# ============================================================
# Leer result.zip oficial de PosFormer
# ============================================================

official_preds = {}

with zipfile.ZipFile(RESULT_ZIP, "r") as zf:
    for member in zf.namelist():
        if member.endswith("/"):
            continue

        if not member.lower().endswith(".txt"):
            continue

        sid = canonical_id(member)
        text = read_text_auto(zf.read(member))
        official_preds[sid] = parse_pos_result_text(text)

print("Predicciones oficiales result.zip:", len(official_preds))


# ============================================================
# Alineacion de IDs
# ============================================================

san_ids = set(san_labels)
pos_ids = set(pos_labels)
bench_ids = set(benchmark)
official_ids = set(official_preds)

common_san_pos = san_ids & pos_ids
common_all = san_ids & pos_ids & bench_ids & official_ids

print()
print("=" * 72)
print("ALINEACION DE IDs")
print("=" * 72)

print("SAN ∩ PosFormer captions :", len(common_san_pos))
print("Comunes en las 4 fuentes :", len(common_all))

missing_in_pos = sorted(san_ids - pos_ids)
missing_in_san = sorted(pos_ids - san_ids)
missing_in_official = sorted(pos_ids - official_ids)
missing_in_benchmark = sorted(pos_ids - bench_ids)

print("En SAN pero no PosFormer :", len(missing_in_pos))
print("En PosFormer pero no SAN :", len(missing_in_san))
print("Sin pred oficial         :", len(missing_in_official))
print("Sin benchmark conjunto   :", len(missing_in_benchmark))

if missing_in_pos:
    print("  Ej. SAN no PosFormer:", missing_in_pos[:10])

if missing_in_san:
    print("  Ej. PosFormer no SAN:", missing_in_san[:10])

if missing_in_official:
    print("  Sin pred oficial:", missing_in_official[:10])


# ============================================================
# Comparar muestra por muestra
# ============================================================

rows = []

labels_equal_count = 0

same_shape_count = 0
pixel_exact_count = 0
binary_exact_count = 0
binary_inverted_exact_count = 0

official_both_correct = 0
official_only_correct = 0
benchmark_only_correct = 0
both_wrong = 0

prediction_same_count = 0

official_correct_total = 0
benchmark_pos_correct_total_common = 0

mae_values = []
binary_disagreement_values = []

with zipfile.ZipFile(POS_DATA_ZIP, "r") as pos_zip:

    all_ids = sorted(san_ids | pos_ids | bench_ids | official_ids)

    for sid in all_ids:

        san_label = san_labels.get(sid, "")
        pos_label = pos_labels.get(sid, "")

        labels_equal = (
            sid in san_labels
            and sid in pos_labels
            and normalize_ws(san_label) == normalize_ws(pos_label)
        )

        if labels_equal:
            labels_equal_count += 1

        benchmark_row = benchmark.get(sid)

        benchmark_pred = ""
        benchmark_correct = None

        if benchmark_row is not None:
            benchmark_pred = normalize_ws(
                benchmark_row.get("posformer_prediction", "")
            )

            benchmark_correct = bool_from_csv(
                benchmark_row.get("posformer_correct", "")
            )

        official_pred = normalize_ws(
            official_preds.get(sid, "")
        )

        official_correct = None

        if sid in official_preds and sid in pos_labels:
            official_correct = (
                official_pred
                == normalize_ws(pos_label)
            )

        prediction_same = None

        if sid in official_preds and benchmark_row is not None:
            prediction_same = (
                official_pred
                == benchmark_pred
            )

            if prediction_same:
                prediction_same_count += 1

        # ----------------------------------------------------
        # Comparacion de imagenes
        # ----------------------------------------------------

        san_image_path = resolve_san_image(
            sid,
            benchmark_row
        )

        san_h = ""
        san_w = ""
        pos_h = ""
        pos_w = ""

        same_shape = None
        pixel_exact = None
        mae = ""
        inverted_mae = ""
        binary_exact = None
        binary_inverted_exact = None
        binary_disagreement = ""

        if sid in pos_sizes:
            pos_h, pos_w = pos_sizes[sid]

        if (
            san_image_path is not None
            and sid in pos_image_members
        ):
            san_img = load_gray_from_disk(san_image_path)

            raw_pos = pos_zip.read(
                pos_image_members[sid]
            )

            pos_img = decode_gray_from_bytes(
                raw_pos
            )

            san_h, san_w = san_img.shape
            pos_h, pos_w = pos_img.shape

            same_shape = (
                san_img.shape
                == pos_img.shape
            )

            if same_shape:
                same_shape_count += 1

                pixel_exact = bool(
                    np.array_equal(
                        san_img,
                        pos_img
                    )
                )

                if pixel_exact:
                    pixel_exact_count += 1

                diff = np.abs(
                    san_img.astype(np.float32)
                    - pos_img.astype(np.float32)
                )

                mae_value = float(
                    diff.mean()
                )

                mae = "{:.6f}".format(
                    mae_value
                )

                mae_values.append(
                    mae_value
                )

                inv_diff = np.abs(
                    san_img.astype(np.float32)
                    - (
                        255.0
                        - pos_img.astype(np.float32)
                    )
                )

                inverted_mae = "{:.6f}".format(
                    float(inv_diff.mean())
                )

                san_bin = san_img >= 128
                pos_bin = pos_img >= 128

                binary_exact = bool(
                    np.array_equal(
                        san_bin,
                        pos_bin
                    )
                )

                if binary_exact:
                    binary_exact_count += 1

                binary_inverted_exact = bool(
                    np.array_equal(
                        san_bin,
                        np.logical_not(pos_bin)
                    )
                )

                if binary_inverted_exact:
                    binary_inverted_exact_count += 1

                binary_disagreement_value = float(
                    np.mean(
                        san_bin != pos_bin
                    )
                )

                binary_disagreement = "{:.8f}".format(
                    binary_disagreement_value
                )

                binary_disagreement_values.append(
                    binary_disagreement_value
                )

        # ----------------------------------------------------
        # Cambio de acierto PosFormer:
        # oficial vs entrada comun basada en SAN
        # ----------------------------------------------------

        transition = ""

        if (
            official_correct is not None
            and benchmark_correct is not None
        ):

            if official_correct:
                official_correct_total += 1

            if benchmark_correct:
                benchmark_pos_correct_total_common += 1

            if official_correct and benchmark_correct:
                transition = "both_correct"
                official_both_correct += 1

            elif official_correct and not benchmark_correct:
                transition = "official_only"
                official_only_correct += 1

            elif (not official_correct) and benchmark_correct:
                transition = "benchmark_only"
                benchmark_only_correct += 1

            else:
                transition = "both_wrong"
                both_wrong += 1

        rows.append({
            "sample_id": sid,
            "in_san_caption": sid in san_labels,
            "in_posformer_caption": sid in pos_labels,
            "in_benchmark_csv": sid in benchmark,
            "in_official_result_zip": sid in official_preds,
            "posformer_filtered_reason": pos_filtered_reason.get(sid, ""),
            "san_ground_truth": san_label,
            "posformer_ground_truth": pos_label,
            "ground_truth_equal": labels_equal,
            "san_image_file": (
                str(san_image_path)
                if san_image_path is not None
                else ""
            ),
            "posformer_image_member": pos_image_members.get(sid, ""),
            "san_height": san_h,
            "san_width": san_w,
            "posformer_height": pos_h,
            "posformer_width": pos_w,
            "same_shape": same_shape,
            "pixel_exact": pixel_exact,
            "pixel_mae": mae,
            "pixel_inverted_mae": inverted_mae,
            "binary_exact_threshold_128": binary_exact,
            "binary_inverted_exact_threshold_128": binary_inverted_exact,
            "binary_disagreement_fraction": binary_disagreement,
            "official_posformer_prediction": official_pred,
            "benchmark_posformer_prediction": benchmark_pred,
            "prediction_equal": prediction_same,
            "official_posformer_correct": official_correct,
            "benchmark_posformer_correct": benchmark_correct,
            "correctness_transition": transition,
        })


# ============================================================
# Guardar CSV
# ============================================================

fieldnames = [
    "sample_id",
    "in_san_caption",
    "in_posformer_caption",
    "in_benchmark_csv",
    "in_official_result_zip",
    "posformer_filtered_reason",
    "san_ground_truth",
    "posformer_ground_truth",
    "ground_truth_equal",
    "san_image_file",
    "posformer_image_member",
    "san_height",
    "san_width",
    "posformer_height",
    "posformer_width",
    "same_shape",
    "pixel_exact",
    "pixel_mae",
    "pixel_inverted_mae",
    "binary_exact_threshold_128",
    "binary_inverted_exact_threshold_128",
    "binary_disagreement_fraction",
    "official_posformer_prediction",
    "benchmark_posformer_prediction",
    "prediction_equal",
    "official_posformer_correct",
    "benchmark_posformer_correct",
    "correctness_transition",
]

with open(
    OUTPUT_CSV,
    "w",
    encoding="utf-8-sig",
    newline=""
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=fieldnames
    )

    writer.writeheader()
    writer.writerows(rows)


# ============================================================
# Resumen
# ============================================================

common_label_ids = san_ids & pos_ids

same_shape_total = 0

for row in rows:
    if row["same_shape"] is True:
        same_shape_total += 1

comparison_correctness_total = (
    official_both_correct
    + official_only_correct
    + benchmark_only_correct
    + both_wrong
)

summary_lines = []

def out(text=""):
    print(text)
    summary_lines.append(str(text))


out()
out("=" * 72)
out("RESUMEN DEL DIAGNOSTICO")
out("=" * 72)

out("SAN captions                    : {}".format(len(san_ids)))
out("PosFormer captions              : {}".format(len(pos_ids)))
out("Benchmark conjunto              : {}".format(len(bench_ids)))
out("Predicciones oficiales          : {}".format(len(official_ids)))
out("IDs comunes SAN/PosFormer       : {}".format(len(common_san_pos)))
out("IDs comunes en las 4 fuentes    : {}".format(len(common_all)))

out()
out("Ground truth")
out(
    "  Iguales SAN vs PosFormer       : {} / {} ({:.2f}%)".format(
        labels_equal_count,
        len(common_label_ids),
        pct(labels_equal_count, len(common_label_ids))
    )
)

out()
out("Filtro oficial PosFormer")
out(
    "  Muestras filtradas             : {}".format(
        len(pos_filtered_reason)
    )
)

for sid in sorted(pos_filtered_reason):
    out(
        "    {} -> {}".format(
            sid,
            pos_filtered_reason[sid]
        )
    )

out()
out("Imagenes SAN vs PosFormer")
out(
    "  Misma forma                    : {} / {}".format(
        same_shape_count,
        len(common_san_pos)
    )
)
out(
    "  Pixeles exactamente iguales    : {} / {} ({:.2f}%)".format(
        pixel_exact_count,
        same_shape_total,
        pct(pixel_exact_count, same_shape_total)
    )
)
out(
    "  Binarias iguales (thr=128)     : {} / {} ({:.2f}%)".format(
        binary_exact_count,
        same_shape_total,
        pct(binary_exact_count, same_shape_total)
    )
)
out(
    "  Binarias invertidas exactas    : {} / {} ({:.2f}%)".format(
        binary_inverted_exact_count,
        same_shape_total,
        pct(binary_inverted_exact_count, same_shape_total)
    )
)

if mae_values:
    out(
        "  MAE pixel medio                : {:.4f}".format(
            float(np.mean(mae_values))
        )
    )
    out(
        "  MAE pixel mediano              : {:.4f}".format(
            float(np.median(mae_values))
        )
    )

if binary_disagreement_values:
    out(
        "  Desacuerdo binario medio       : {:.4f}%".format(
            100.0 * float(np.mean(binary_disagreement_values))
        )
    )
    out(
        "  Desacuerdo binario mediano     : {:.4f}%".format(
            100.0 * float(np.median(binary_disagreement_values))
        )
    )

out()
out("Prediccion PosFormer: oficial vs entrada comun SAN")

if comparison_correctness_total > 0:
    out(
        "  IDs comparables                : {}".format(
            comparison_correctness_total
        )
    )
    out(
        "  Aciertos oficiales             : {} ({:.2f}%)".format(
            official_correct_total,
            pct(
                official_correct_total,
                comparison_correctness_total
            )
        )
    )
    out(
        "  Aciertos con entrada SAN       : {} ({:.2f}%)".format(
            benchmark_pos_correct_total_common,
            pct(
                benchmark_pos_correct_total_common,
                comparison_correctness_total
            )
        )
    )
    out(
        "  Ambos correctos                : {}".format(
            official_both_correct
        )
    )
    out(
        "  Solo evaluacion oficial        : {}".format(
            official_only_correct
        )
    )
    out(
        "  Solo entrada SAN               : {}".format(
            benchmark_only_correct
        )
    )
    out(
        "  Ambos incorrectos              : {}".format(
            both_wrong
        )
    )
    out(
        "  Prediccion exacta sin cambiar  : {} / {} ({:.2f}%)".format(
            prediction_same_count,
            comparison_correctness_total,
            pct(
                prediction_same_count,
                comparison_correctness_total
            )
        )
    )

out()
out("Archivos generados")
out("  Detalle : {}".format(OUTPUT_CSV))
out("  Resumen : {}".format(OUTPUT_SUMMARY))

with open(
    OUTPUT_SUMMARY,
    "w",
    encoding="utf-8"
) as f:
    f.write("\n".join(summary_lines))
    f.write("\n")

print()
print("Diagnostico terminado.")
