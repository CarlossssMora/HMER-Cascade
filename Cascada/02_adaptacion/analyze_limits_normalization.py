import csv
from pathlib import Path


# ============================================================
# Configuracion
# ============================================================

RESULTS_DIR = Path(__file__).resolve().parent / "resultados"

INPUT_CSV = RESULTS_DIR / "ground_truth_cross_evaluation_2014.csv"

OUTPUT_ALL = RESULTS_DIR / "limits_normalization_cross_evaluation_2014.csv"
OUTPUT_RESIDUAL = RESULTS_DIR / "limits_normalization_residual_gt_differences_2014.csv"
OUTPUT_SUMMARY = RESULTS_DIR / "limits_normalization_2014_summary.txt"


# ============================================================
# Utilidades
# ============================================================

def normalize_ws(text):
    return " ".join(str(text).strip().split())


def tokens(text):
    return normalize_ws(text).split()


def remove_limits(text):
    """
    Normalizacion deliberadamente conservadora:
    SOLO elimina el token LaTeX \\limits.

    No modifica:
      - ^ o _
      - llaves
      - parentesis
      - operadores
      - simbolos
      - orden de tokens
    """
    return " ".join(
        tok
        for tok in tokens(text)
        if tok != "\\limits"
    )


def exact(a, b):
    return normalize_ws(a) == normalize_ws(b)


def outcome(san_ok, pos_ok):
    if san_ok and pos_ok:
        return "both_correct"
    if san_ok and not pos_ok:
        return "san_only"
    if (not san_ok) and pos_ok:
        return "posformer_only"
    return "both_wrong"


def pct(n, d):
    if d == 0:
        return 0.0
    return 100.0 * float(n) / float(d)


# ============================================================
# Verificar entrada
# ============================================================

if not INPUT_CSV.exists():
    raise FileNotFoundError(
        "No existe el archivo requerido:\n{}".format(
            INPUT_CSV
        )
    )


# ============================================================
# Leer datos
# ============================================================

rows_in = []

with open(
    INPUT_CSV,
    "r",
    encoding="utf-8-sig",
    newline=""
) as f:

    reader = csv.DictReader(f)

    for row in reader:
        rows_in.append(row)


print("=" * 72)
print("ANALISIS DE NORMALIZACION EXCLUSIVA DE \\\\limits")
print("=" * 72)
print("Archivo :", INPUT_CSV)
print("Muestras:", len(rows_in))


# ============================================================
# Contadores
# ============================================================

n = len(rows_in)

raw_gt_equal = 0
norm_gt_equal = 0

gt_san_has_limits = 0
gt_pos_has_limits = 0
san_pred_has_limits = 0
pos_pred_has_limits = 0

counts_san_gt = {
    "san": 0,
    "pos": 0,
    "oracle": 0,
    "both_correct": 0,
    "san_only": 0,
    "posformer_only": 0,
    "both_wrong": 0,
}

counts_pos_gt = {
    "san": 0,
    "pos": 0,
    "oracle": 0,
    "both_correct": 0,
    "san_only": 0,
    "posformer_only": 0,
    "both_wrong": 0,
}

# Solo casos donde ambos GT se vuelven exactamente iguales
common_canonical = {
    "n": 0,
    "san": 0,
    "pos": 0,
    "oracle": 0,
    "both_correct": 0,
    "san_only": 0,
    "posformer_only": 0,
    "both_wrong": 0,
}

rows_all = []
residual_rows = []


# ============================================================
# Procesar
# ============================================================

for row in rows_in:

    sid = row["sample_id"]

    gt_san_raw = normalize_ws(
        row["ground_truth_san"]
    )

    gt_pos_raw = normalize_ws(
        row["ground_truth_posformer"]
    )

    san_pred_raw = normalize_ws(
        row["san_prediction"]
    )

    pos_pred_raw = normalize_ws(
        row["posformer_prediction"]
    )

    if exact(gt_san_raw, gt_pos_raw):
        raw_gt_equal += 1

    if "\\limits" in tokens(gt_san_raw):
        gt_san_has_limits += 1

    if "\\limits" in tokens(gt_pos_raw):
        gt_pos_has_limits += 1

    if "\\limits" in tokens(san_pred_raw):
        san_pred_has_limits += 1

    if "\\limits" in tokens(pos_pred_raw):
        pos_pred_has_limits += 1

    gt_san = remove_limits(
        gt_san_raw
    )

    gt_pos = remove_limits(
        gt_pos_raw
    )

    san_pred = remove_limits(
        san_pred_raw
    )

    pos_pred = remove_limits(
        pos_pred_raw
    )

    gt_equal_after = exact(
        gt_san,
        gt_pos
    )

    if gt_equal_after:
        norm_gt_equal += 1

    # --------------------------------------------------------
    # Evaluacion normalizada contra GT SAN normalizado
    # --------------------------------------------------------

    san_ok_san = exact(
        san_pred,
        gt_san
    )

    pos_ok_san = exact(
        pos_pred,
        gt_san
    )

    oracle_ok_san = (
        san_ok_san
        or pos_ok_san
    )

    out_san = outcome(
        san_ok_san,
        pos_ok_san
    )

    if san_ok_san:
        counts_san_gt["san"] += 1

    if pos_ok_san:
        counts_san_gt["pos"] += 1

    if oracle_ok_san:
        counts_san_gt["oracle"] += 1

    counts_san_gt[out_san] += 1

    # --------------------------------------------------------
    # Evaluacion normalizada contra GT PosFormer normalizado
    # --------------------------------------------------------

    san_ok_pos = exact(
        san_pred,
        gt_pos
    )

    pos_ok_pos = exact(
        pos_pred,
        gt_pos
    )

    oracle_ok_pos = (
        san_ok_pos
        or pos_ok_pos
    )

    out_pos = outcome(
        san_ok_pos,
        pos_ok_pos
    )

    if san_ok_pos:
        counts_pos_gt["san"] += 1

    if pos_ok_pos:
        counts_pos_gt["pos"] += 1

    if oracle_ok_pos:
        counts_pos_gt["oracle"] += 1

    counts_pos_gt[out_pos] += 1

    # --------------------------------------------------------
    # Protocolo canonico solo si ambos GT ya coinciden
    # --------------------------------------------------------

    if gt_equal_after:

        common_canonical["n"] += 1

        san_ok = exact(
            san_pred,
            gt_san
        )

        pos_ok = exact(
            pos_pred,
            gt_san
        )

        oracle_ok = (
            san_ok
            or pos_ok
        )

        out_common = outcome(
            san_ok,
            pos_ok
        )

        if san_ok:
            common_canonical["san"] += 1

        if pos_ok:
            common_canonical["pos"] += 1

        if oracle_ok:
            common_canonical["oracle"] += 1

        common_canonical[out_common] += 1

    row_out = {
        "sample_id": sid,

        "ground_truth_san_raw": gt_san_raw,
        "ground_truth_posformer_raw": gt_pos_raw,

        "ground_truth_san_no_limits": gt_san,
        "ground_truth_posformer_no_limits": gt_pos,

        "gt_equal_raw": exact(
            gt_san_raw,
            gt_pos_raw
        ),

        "gt_equal_after_remove_limits": gt_equal_after,

        "san_prediction_raw": san_pred_raw,
        "posformer_prediction_raw": pos_pred_raw,

        "san_prediction_no_limits": san_pred,
        "posformer_prediction_no_limits": pos_pred,

        "san_correct_normalized_gt_san": san_ok_san,
        "posformer_correct_normalized_gt_san": pos_ok_san,
        "outcome_normalized_gt_san": out_san,

        "san_correct_normalized_gt_posformer": san_ok_pos,
        "posformer_correct_normalized_gt_posformer": pos_ok_pos,
        "outcome_normalized_gt_posformer": out_pos,
    }

    rows_all.append(
        row_out
    )

    if not gt_equal_after:
        residual_rows.append(
            row_out
        )


# ============================================================
# Guardar CSV
# ============================================================

fieldnames = [
    "sample_id",

    "ground_truth_san_raw",
    "ground_truth_posformer_raw",

    "ground_truth_san_no_limits",
    "ground_truth_posformer_no_limits",

    "gt_equal_raw",
    "gt_equal_after_remove_limits",

    "san_prediction_raw",
    "posformer_prediction_raw",

    "san_prediction_no_limits",
    "posformer_prediction_no_limits",

    "san_correct_normalized_gt_san",
    "posformer_correct_normalized_gt_san",
    "outcome_normalized_gt_san",

    "san_correct_normalized_gt_posformer",
    "posformer_correct_normalized_gt_posformer",
    "outcome_normalized_gt_posformer",
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
    writer.writerows(
        rows_all
    )


with open(
    OUTPUT_RESIDUAL,
    "w",
    encoding="utf-8-sig",
    newline=""
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=fieldnames
    )

    writer.writeheader()
    writer.writerows(
        residual_rows
    )


# ============================================================
# Resumen
# ============================================================

summary = []


def out(text=""):
    print(text)
    summary.append(
        str(text)
    )


def print_eval(title, counts, total):
    out()
    out(title)
    out("-" * 72)

    out(
        "SAN        : {:.4f} ({}/{})".format(
            counts["san"] / float(total),
            counts["san"],
            total
        )
    )

    out(
        "PosFormer  : {:.4f} ({}/{})".format(
            counts["pos"] / float(total),
            counts["pos"],
            total
        )
    )

    out(
        "Oracle     : {:.4f} ({}/{})".format(
            counts["oracle"] / float(total),
            counts["oracle"],
            total
        )
    )

    out(
        "  Ambos correctos : {}".format(
            counts["both_correct"]
        )
    )

    out(
        "  Solo SAN        : {}".format(
            counts["san_only"]
        )
    )

    out(
        "  Solo PosFormer  : {}".format(
            counts["posformer_only"]
        )
    )

    out(
        "  Ambos fallan    : {}".format(
            counts["both_wrong"]
        )
    )


out()
out("=" * 72)
out("RESUMEN")
out("=" * 72)

out(
    "Muestras                         : {}".format(
        n
    )
)

out(
    "GT iguales antes                 : {} / {} ({:.2f}%)".format(
        raw_gt_equal,
        n,
        pct(
            raw_gt_equal,
            n
        )
    )
)

out(
    "GT iguales tras quitar \\\\limits : {} / {} ({:.2f}%)".format(
        norm_gt_equal,
        n,
        pct(
            norm_gt_equal,
            n
        )
    )
)

out(
    "Discrepancias residuales         : {}".format(
        len(
            residual_rows
        )
    )
)


out()
out("Presencia de \\\\limits")

out(
    "  GT SAN          : {}".format(
        gt_san_has_limits
    )
)

out(
    "  GT PosFormer    : {}".format(
        gt_pos_has_limits
    )
)

out(
    "  Prediccion SAN  : {}".format(
        san_pred_has_limits
    )
)

out(
    "  Prediccion Pos  : {}".format(
        pos_pred_has_limits
    )
)


print_eval(
    "NORMALIZADO CONTRA GT SAN SIN \\\\limits",
    counts_san_gt,
    n
)

print_eval(
    "NORMALIZADO CONTRA GT POSFORMER SIN \\\\limits",
    counts_pos_gt,
    n
)


if common_canonical["n"] > 0:

    print_eval(
        "SUBCONJUNTO DONDE AMBOS GT COINCIDEN TRAS QUITAR \\\\limits",
        common_canonical,
        common_canonical["n"]
    )


out()
out("Archivos generados")

out(
    "  Evaluacion completa : {}".format(
        OUTPUT_ALL
    )
)

out(
    "  GT residuales       : {}".format(
        OUTPUT_RESIDUAL
    )
)

out(
    "  Resumen             : {}".format(
        OUTPUT_SUMMARY
    )
)


with open(
    OUTPUT_SUMMARY,
    "w",
    encoding="utf-8"
) as f:

    f.write(
        "\n".join(
            summary
        )
    )

    f.write("\n")


print()
print("Analisis terminado.")
