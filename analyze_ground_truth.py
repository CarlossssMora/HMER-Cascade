import csv
from pathlib import Path


# ============================================================
# Configuracion
# ============================================================

ROOT = Path(__file__).resolve().parent

BENCHMARK_CSV = ROOT / "benchmark_crohme_2014.csv"
COMPARE_CSV = ROOT / "compare_crohme_sources_2014.csv"

OUTPUT_CASES = ROOT / "ground_truth_differences_2014.csv"
OUTPUT_ALL = ROOT / "ground_truth_cross_evaluation_2014.csv"
OUTPUT_SUMMARY = ROOT / "ground_truth_analysis_2014_summary.txt"


# ============================================================
# Utilidades
# ============================================================

def normalize_ws(text):
    return " ".join(str(text).strip().split())


def canonical_id(name):
    name = str(name).replace("\\", "/")
    name = name.rsplit("/", 1)[-1]

    lower = name.lower()

    for ext in [".jpg", ".jpeg", ".png", ".bmp", ".txt", ".inkml"]:
        if lower.endswith(ext):
            name = name[:-len(ext)]
            break

    return name


def bool_from_csv(value):
    return str(value).strip().lower() in [
        "true", "1", "yes", "si", "sí"
    ]


def pct(n, d):
    if d == 0:
        return 0.0
    return 100.0 * float(n) / float(d)


def exact(pred, gt):
    return normalize_ws(pred) == normalize_ws(gt)


def outcome(san_ok, pos_ok):
    if san_ok and pos_ok:
        return "both_correct"
    if san_ok and not pos_ok:
        return "san_only"
    if (not san_ok) and pos_ok:
        return "posformer_only"
    return "both_wrong"


# ============================================================
# Verificar archivos
# ============================================================

print("=" * 72)
print("ANALISIS DE GROUND TRUTH - CROHME 2014")
print("=" * 72)

for path in [BENCHMARK_CSV, COMPARE_CSV]:
    if not path.exists():
        raise FileNotFoundError(
            "No existe el archivo requerido:\n{}".format(path)
        )

print("Benchmark :", BENCHMARK_CSV)
print("Comparacion:", COMPARE_CSV)


# ============================================================
# Leer benchmark
# ============================================================

benchmark = {}

with open(
    BENCHMARK_CSV,
    "r",
    encoding="utf-8-sig",
    newline=""
) as f:

    reader = csv.DictReader(f)

    for row in reader:
        if row.get("status", "ok").strip().lower() not in ["", "ok"]:
            continue

        sid = canonical_id(row["sample_id"])
        benchmark[sid] = row


# ============================================================
# Leer comparacion de fuentes
# ============================================================

compare = {}

with open(
    COMPARE_CSV,
    "r",
    encoding="utf-8-sig",
    newline=""
) as f:

    reader = csv.DictReader(f)

    for row in reader:
        sid = canonical_id(row["sample_id"])
        compare[sid] = row


# ============================================================
# Construir conjunto comun oficial de PosFormer
#
# Se excluye cualquier muestra sin prediccion oficial.
# En este caso deberia excluir 505_em_51.
# ============================================================

common_ids = []

for sid in sorted(set(benchmark) & set(compare)):

    c = compare[sid]

    in_official = bool_from_csv(
        c.get("in_official_result_zip", "")
    )

    if in_official:
        common_ids.append(sid)


print()
print("Muestras comunes evaluables:", len(common_ids))


# ============================================================
# Evaluacion cruzada
# ============================================================

rows_all = []
rows_diff = []

counts = {
    "gt_san": {
        "san": 0,
        "pos": 0,
        "oracle": 0,
        "both_correct": 0,
        "san_only": 0,
        "posformer_only": 0,
        "both_wrong": 0,
    },
    "gt_pos": {
        "san": 0,
        "pos": 0,
        "oracle": 0,
        "both_correct": 0,
        "san_only": 0,
        "posformer_only": 0,
        "both_wrong": 0,
    },
}

gt_equal_count = 0
gt_diff_count = 0

# Cambios de correccion al pasar de GT SAN -> GT PosFormer
san_gains = 0
san_losses = 0
pos_gains = 0
pos_losses = 0

for sid in common_ids:

    b = benchmark[sid]
    c = compare[sid]

    gt_san = normalize_ws(
        c.get("san_ground_truth", "")
    )

    gt_pos = normalize_ws(
        c.get("posformer_ground_truth", "")
    )

    san_pred = normalize_ws(
        b.get("san_prediction", "")
    )

    pos_pred = normalize_ws(
        b.get("posformer_prediction", "")
    )

    gt_equal = (
        gt_san == gt_pos
    )

    if gt_equal:
        gt_equal_count += 1
    else:
        gt_diff_count += 1

    # --------------------------------------------------------
    # Evaluar contra GT SAN
    # --------------------------------------------------------

    san_ok_san_gt = exact(
        san_pred,
        gt_san
    )

    pos_ok_san_gt = exact(
        pos_pred,
        gt_san
    )

    oracle_ok_san_gt = (
        san_ok_san_gt
        or pos_ok_san_gt
    )

    outcome_san_gt = outcome(
        san_ok_san_gt,
        pos_ok_san_gt
    )

    if san_ok_san_gt:
        counts["gt_san"]["san"] += 1

    if pos_ok_san_gt:
        counts["gt_san"]["pos"] += 1

    if oracle_ok_san_gt:
        counts["gt_san"]["oracle"] += 1

    counts["gt_san"][outcome_san_gt] += 1

    # --------------------------------------------------------
    # Evaluar contra GT PosFormer
    # --------------------------------------------------------

    san_ok_pos_gt = exact(
        san_pred,
        gt_pos
    )

    pos_ok_pos_gt = exact(
        pos_pred,
        gt_pos
    )

    oracle_ok_pos_gt = (
        san_ok_pos_gt
        or pos_ok_pos_gt
    )

    outcome_pos_gt = outcome(
        san_ok_pos_gt,
        pos_ok_pos_gt
    )

    if san_ok_pos_gt:
        counts["gt_pos"]["san"] += 1

    if pos_ok_pos_gt:
        counts["gt_pos"]["pos"] += 1

    if oracle_ok_pos_gt:
        counts["gt_pos"]["oracle"] += 1

    counts["gt_pos"][outcome_pos_gt] += 1

    # --------------------------------------------------------
    # Como cambia cada modelo al cambiar el GT
    # --------------------------------------------------------

    if (not san_ok_san_gt) and san_ok_pos_gt:
        san_gains += 1

    if san_ok_san_gt and (not san_ok_pos_gt):
        san_losses += 1

    if (not pos_ok_san_gt) and pos_ok_pos_gt:
        pos_gains += 1

    if pos_ok_san_gt and (not pos_ok_pos_gt):
        pos_losses += 1

    row = {
        "sample_id": sid,
        "ground_truth_equal": gt_equal,
        "ground_truth_san": gt_san,
        "ground_truth_posformer": gt_pos,
        "san_prediction": san_pred,
        "posformer_prediction": pos_pred,

        "san_correct_gt_san": san_ok_san_gt,
        "posformer_correct_gt_san": pos_ok_san_gt,
        "oracle_correct_gt_san": oracle_ok_san_gt,
        "outcome_gt_san": outcome_san_gt,

        "san_correct_gt_posformer": san_ok_pos_gt,
        "posformer_correct_gt_posformer": pos_ok_pos_gt,
        "oracle_correct_gt_posformer": oracle_ok_pos_gt,
        "outcome_gt_posformer": outcome_pos_gt,

        "san_changes_correctness": (
            san_ok_san_gt != san_ok_pos_gt
        ),

        "posformer_changes_correctness": (
            pos_ok_san_gt != pos_ok_pos_gt
        ),
    }

    rows_all.append(row)

    if not gt_equal:
        rows_diff.append(row)


# ============================================================
# Guardar CSV completo
# ============================================================

fieldnames = [
    "sample_id",
    "ground_truth_equal",
    "ground_truth_san",
    "ground_truth_posformer",
    "san_prediction",
    "posformer_prediction",

    "san_correct_gt_san",
    "posformer_correct_gt_san",
    "oracle_correct_gt_san",
    "outcome_gt_san",

    "san_correct_gt_posformer",
    "posformer_correct_gt_posformer",
    "oracle_correct_gt_posformer",
    "outcome_gt_posformer",

    "san_changes_correctness",
    "posformer_changes_correctness",
]

with open(
    OUTPUT_ALL,
    "w",
    encoding="utf-8-sig",
    newline=""
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=fieldnames
    )

    writer.writeheader()
    writer.writerows(rows_all)


# ============================================================
# Guardar solo ground truths diferentes
# ============================================================

with open(
    OUTPUT_CASES,
    "w",
    encoding="utf-8-sig",
    newline=""
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=fieldnames
    )

    writer.writeheader()
    writer.writerows(rows_diff)


# ============================================================
# Resumen
# ============================================================

n = len(common_ids)

summary = []

def out(text=""):
    print(text)
    summary.append(str(text))


out()
out("=" * 72)
out("RESUMEN FINAL")
out("=" * 72)

out("Muestras evaluadas                    : {}".format(n))
out(
    "Ground truths iguales                : {} ({:.2f}%)".format(
        gt_equal_count,
        pct(gt_equal_count, n)
    )
)
out(
    "Ground truths diferentes             : {} ({:.2f}%)".format(
        gt_diff_count,
        pct(gt_diff_count, n)
    )
)

out()
out("EVALUACION USANDO GROUND TRUTH DE SAN")
out("-" * 72)

out(
    "SAN        : {:.4f} ({}/{})".format(
        counts["gt_san"]["san"] / float(n),
        counts["gt_san"]["san"],
        n
    )
)

out(
    "PosFormer  : {:.4f} ({}/{})".format(
        counts["gt_san"]["pos"] / float(n),
        counts["gt_san"]["pos"],
        n
    )
)

out(
    "Oracle     : {:.4f} ({}/{})".format(
        counts["gt_san"]["oracle"] / float(n),
        counts["gt_san"]["oracle"],
        n
    )
)

out(
    "  Ambos correctos : {}".format(
        counts["gt_san"]["both_correct"]
    )
)

out(
    "  Solo SAN        : {}".format(
        counts["gt_san"]["san_only"]
    )
)

out(
    "  Solo PosFormer  : {}".format(
        counts["gt_san"]["posformer_only"]
    )
)

out(
    "  Ambos fallan    : {}".format(
        counts["gt_san"]["both_wrong"]
    )
)

out()
out("EVALUACION USANDO GROUND TRUTH DE POSFORMER")
out("-" * 72)

out(
    "SAN        : {:.4f} ({}/{})".format(
        counts["gt_pos"]["san"] / float(n),
        counts["gt_pos"]["san"],
        n
    )
)

out(
    "PosFormer  : {:.4f} ({}/{})".format(
        counts["gt_pos"]["pos"] / float(n),
        counts["gt_pos"]["pos"],
        n
    )
)

out(
    "Oracle     : {:.4f} ({}/{})".format(
        counts["gt_pos"]["oracle"] / float(n),
        counts["gt_pos"]["oracle"],
        n
    )
)

out(
    "  Ambos correctos : {}".format(
        counts["gt_pos"]["both_correct"]
    )
)

out(
    "  Solo SAN        : {}".format(
        counts["gt_pos"]["san_only"]
    )
)

out(
    "  Solo PosFormer  : {}".format(
        counts["gt_pos"]["posformer_only"]
    )
)

out(
    "  Ambos fallan    : {}".format(
        counts["gt_pos"]["both_wrong"]
    )
)

out()
out("CAMBIO DE CORRECCION AL CAMBIAR EL GROUND TRUTH")
out("-" * 72)

out(
    "SAN gana aciertos                  : {}".format(
        san_gains
    )
)

out(
    "SAN pierde aciertos                : {}".format(
        san_losses
    )
)

out(
    "PosFormer gana aciertos            : {}".format(
        pos_gains
    )
)

out(
    "PosFormer pierde aciertos          : {}".format(
        pos_losses
    )
)

out()
out("ARCHIVOS GENERADOS")
out("-" * 72)

out(
    "Todas las muestras : {}".format(
        OUTPUT_ALL
    )
)

out(
    "Solo GT diferentes : {}".format(
        OUTPUT_CASES
    )
)

out(
    "Resumen             : {}".format(
        OUTPUT_SUMMARY
    )
)


with open(
    OUTPUT_SUMMARY,
    "w",
    encoding="utf-8"
) as f:

    f.write(
        "\n".join(summary)
    )

    f.write("\n")


print()
print("Analisis terminado.")
