import csv
import difflib
import re
from collections import Counter
from pathlib import Path


# ============================================================
# Configuracion
# ============================================================

ROOT = Path(__file__).resolve().parent

INPUT_CSV = ROOT / "ground_truth_differences_2014.csv"

OUTPUT_CSV = ROOT / "ground_truth_difference_classification_2014.csv"
OUTPUT_SUMMARY = ROOT / "ground_truth_difference_classification_2014_summary.txt"
OUTPUT_TOKEN_CHANGES = ROOT / "ground_truth_token_changes_2014.csv"


# ============================================================
# Utilidades basicas
# ============================================================

def normalize_ws(text):
    return " ".join(str(text).strip().split())


def tokenize(text):
    """
    Los captions ya estan separados por espacios en CROHME.
    Esta funcion conserva esa tokenizacion.
    """
    return normalize_ws(text).split()


def remove_tokens(tokens, removable):
    return [
        tok for tok in tokens
        if tok not in removable
    ]


def sequence_ratio(a, b):
    return difflib.SequenceMatcher(
        a=a,
        b=b,
        autojunk=False
    ).ratio()


def opcode_summary(a, b):
    """
    Resume las operaciones necesarias para transformar A -> B.
    """
    matcher = difflib.SequenceMatcher(
        a=a,
        b=b,
        autojunk=False
    )

    counts = Counter()
    details = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue

        counts[tag] += 1

        details.append(
            "{}: [{}] -> [{}]".format(
                tag,
                " ".join(a[i1:i2]),
                " ".join(b[j1:j2]),
            )
        )

    return counts, " | ".join(details)


def pct(n, d):
    if d == 0:
        return 0.0
    return 100.0 * float(n) / float(d)


# ============================================================
# Conjuntos de tokens para diagnostico
#
# IMPORTANTE:
# Estas reglas SOLO clasifican diferencias.
# No se usan todavia para evaluar ExpRate.
# ============================================================

BRACE_TOKENS = {
    "{", "}", "[", "]"
}

LATEX_LAYOUT_TOKENS = {
    "\\left",
    "\\right",
    "\\!",
    "\\,",
    "\\:",
    "\\;",
    "\\quad",
    "\\qquad",
}

SCRIPT_TOKENS = {
    "^",
    "_",
}

CORE_STRUCTURE_TOKENS = {
    "\\frac",
    "\\sqrt",
    "\\sum",
    "\\prod",
    "\\int",
    "\\lim",
}

RELATION_TOKENS = {
    "=",
    "<",
    ">",
    "\\leq",
    "\\geq",
    "\\neq",
    "\\approx",
    "\\sim",
}

DELIMITER_TOKENS = {
    "(",
    ")",
    "[",
    "]",
    "\\{",
    "\\}",
    "|",
}

OPERATOR_TOKENS = {
    "+",
    "-",
    "\\times",
    "\\cdot",
    "\\div",
    "/",
}


# ============================================================
# Normalizaciones diagnosticas conservadoras
# ============================================================

def strip_layout(tokens):
    return remove_tokens(
        tokens,
        LATEX_LAYOUT_TOKENS
    )


def strip_braces(tokens):
    return remove_tokens(
        tokens,
        BRACE_TOKENS
    )


def strip_layout_and_braces(tokens):
    return strip_braces(
        strip_layout(tokens)
    )


# ============================================================
# Clasificacion
# ============================================================

def classify_difference(gt_san, gt_pos):
    a = tokenize(gt_san)
    b = tokenize(gt_pos)

    a_set = Counter(a)
    b_set = Counter(b)

    # --------------------------------------------------------
    # 1. Solo tokens de formato LaTeX
    # --------------------------------------------------------
    if strip_layout(a) == strip_layout(b):
        return (
            "layout_only",
            "Difieren solo en tokens de formato LaTeX "
            "(por ejemplo, \\left, \\right o espaciado).",
            "baja"
        )

    # --------------------------------------------------------
    # 2. Solo agrupacion por llaves/corchetes
    # --------------------------------------------------------
    if strip_braces(a) == strip_braces(b):
        return (
            "grouping_tokens_only",
            "Difieren solo en llaves/corchetes usados para agrupacion.",
            "media"
        )

    # --------------------------------------------------------
    # 3. Layout + agrupacion
    # --------------------------------------------------------
    if strip_layout_and_braces(a) == strip_layout_and_braces(b):
        return (
            "layout_and_grouping_only",
            "Difieren solo en tokens de layout y agrupacion.",
            "media"
        )

    # --------------------------------------------------------
    # 4. Mismos tokens, distinto orden
    # --------------------------------------------------------
    if a_set == b_set:
        return (
            "same_tokens_different_order",
            "Tienen exactamente el mismo multiconjunto de tokens, "
            "pero en orden distinto.",
            "alta"
        )

    # --------------------------------------------------------
    # 5. Cambios estructurales fuertes
    # --------------------------------------------------------
    structural_union = (
        SCRIPT_TOKENS
        | CORE_STRUCTURE_TOKENS
    )

    a_struct = [
        tok for tok in a
        if tok in structural_union
    ]

    b_struct = [
        tok for tok in b
        if tok in structural_union
    ]

    if a_struct != b_struct:
        return (
            "structural_difference",
            "Cambian tokens estructurales como ^, _, \\frac, \\sqrt, "
            "\\sum, \\int, etc.",
            "muy_alta"
        )

    # --------------------------------------------------------
    # 6. Cambios en relaciones
    # --------------------------------------------------------
    a_rel = [
        tok for tok in a
        if tok in RELATION_TOKENS
    ]

    b_rel = [
        tok for tok in b
        if tok in RELATION_TOKENS
    ]

    if a_rel != b_rel:
        return (
            "relation_difference",
            "Cambian operadores relacionales (=, <, >, \\leq, ...).",
            "muy_alta"
        )

    # --------------------------------------------------------
    # 7. Cambios en delimitadores
    # --------------------------------------------------------
    a_delim = [
        tok for tok in a
        if tok in DELIMITER_TOKENS
    ]

    b_delim = [
        tok for tok in b
        if tok in DELIMITER_TOKENS
    ]

    if a_delim != b_delim:
        return (
            "delimiter_difference",
            "Cambian parentesis, corchetes, barras u otros delimitadores.",
            "alta"
        )

    # --------------------------------------------------------
    # 8. Cambios en operadores
    # --------------------------------------------------------
    a_op = [
        tok for tok in a
        if tok in OPERATOR_TOKENS
    ]

    b_op = [
        tok for tok in b
        if tok in OPERATOR_TOKENS
    ]

    if a_op != b_op:
        return (
            "operator_difference",
            "Cambian operadores aritmeticos.",
            "muy_alta"
        )

    # --------------------------------------------------------
    # 9. Diferencia corta: una sola edicion
    # --------------------------------------------------------
    counts, _ = opcode_summary(a, b)

    total_edit_blocks = (
        counts["replace"]
        + counts["insert"]
        + counts["delete"]
    )

    if total_edit_blocks == 1:
        return (
            "single_edit_block",
            "La diferencia se concentra en un solo bloque de edicion.",
            "alta"
        )

    # --------------------------------------------------------
    # 10. Diferencia lexical/general
    # --------------------------------------------------------
    ratio = sequence_ratio(a, b)

    if ratio >= 0.90:
        return (
            "minor_lexical_difference",
            "Secuencias muy parecidas, pero con diferencias lexicales.",
            "alta"
        )

    return (
        "complex_difference",
        "Diferencia compleja o multiple; requiere revision manual.",
        "muy_alta"
    )


# ============================================================
# Leer entrada
# ============================================================

if not INPUT_CSV.exists():
    raise FileNotFoundError(
        "No existe el archivo requerido:\n{}".format(
            INPUT_CSV
        )
    )

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
print("CLASIFICACION DE DIFERENCIAS DE GROUND TRUTH")
print("=" * 72)
print("Archivo de entrada :", INPUT_CSV)
print("Casos               :", len(rows_in))


# ============================================================
# Analizar
# ============================================================

rows_out = []

category_counts = Counter()
priority_counts = Counter()

token_change_counts = Counter()

for row in rows_in:

    sid = row["sample_id"]

    gt_san = normalize_ws(
        row["ground_truth_san"]
    )

    gt_pos = normalize_ws(
        row["ground_truth_posformer"]
    )

    san_pred = normalize_ws(
        row["san_prediction"]
    )

    pos_pred = normalize_ws(
        row["posformer_prediction"]
    )

    a = tokenize(gt_san)
    b = tokenize(gt_pos)

    category, explanation, priority = classify_difference(
        gt_san,
        gt_pos
    )

    category_counts[category] += 1
    priority_counts[priority] += 1

    counts, edit_details = opcode_summary(
        a,
        b
    )

    matcher = difflib.SequenceMatcher(
        a=a,
        b=b,
        autojunk=False
    )

    # --------------------------------------------------------
    # Registrar cambios de tokens para estadisticas globales
    # --------------------------------------------------------
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():

        if tag == "equal":
            continue

        left = " ".join(a[i1:i2])
        right = " ".join(b[j1:j2])

        token_change_counts[
            (
                tag,
                left,
                right
            )
        ] += 1

    # --------------------------------------------------------
    # Flags de impacto sobre los modelos
    # --------------------------------------------------------
    san_correct_san_gt = (
        san_pred == gt_san
    )

    san_correct_pos_gt = (
        san_pred == gt_pos
    )

    pos_correct_san_gt = (
        pos_pred == gt_san
    )

    pos_correct_pos_gt = (
        pos_pred == gt_pos
    )

    favors_san = (
        san_correct_san_gt
        and not san_correct_pos_gt
    )

    favors_pos = (
        pos_correct_pos_gt
        and not pos_correct_san_gt
    )

    affects_either_model = (
        san_correct_san_gt
        != san_correct_pos_gt
        or
        pos_correct_san_gt
        != pos_correct_pos_gt
    )

    row_out = {
        "sample_id": sid,
        "category": category,
        "review_priority": priority,
        "explanation": explanation,

        "ground_truth_san": gt_san,
        "ground_truth_posformer": gt_pos,

        "san_prediction": san_pred,
        "posformer_prediction": pos_pred,

        "san_correct_gt_san": san_correct_san_gt,
        "san_correct_gt_posformer": san_correct_pos_gt,

        "posformer_correct_gt_san": pos_correct_san_gt,
        "posformer_correct_gt_posformer": pos_correct_pos_gt,

        "favors_san_annotation": favors_san,
        "favors_posformer_annotation": favors_pos,
        "affects_model_correctness": affects_either_model,

        "token_count_san": len(a),
        "token_count_posformer": len(b),

        "sequence_similarity": "{:.4f}".format(
            sequence_ratio(a, b)
        ),

        "replace_blocks": counts["replace"],
        "insert_blocks": counts["insert"],
        "delete_blocks": counts["delete"],

        "edit_details": edit_details,
    }

    rows_out.append(
        row_out
    )


# ============================================================
# Ordenar:
# prioridad alta primero, luego por similitud menor
# ============================================================

priority_order = {
    "muy_alta": 0,
    "alta": 1,
    "media": 2,
    "baja": 3,
}

rows_out.sort(
    key=lambda r: (
        priority_order.get(
            r["review_priority"],
            99
        ),
        float(
            r["sequence_similarity"]
        ),
        r["sample_id"],
    )
)


# ============================================================
# Guardar clasificacion
# ============================================================

fieldnames = [
    "sample_id",
    "category",
    "review_priority",
    "explanation",

    "ground_truth_san",
    "ground_truth_posformer",

    "san_prediction",
    "posformer_prediction",

    "san_correct_gt_san",
    "san_correct_gt_posformer",

    "posformer_correct_gt_san",
    "posformer_correct_gt_posformer",

    "favors_san_annotation",
    "favors_posformer_annotation",
    "affects_model_correctness",

    "token_count_san",
    "token_count_posformer",
    "sequence_similarity",

    "replace_blocks",
    "insert_blocks",
    "delete_blocks",

    "edit_details",
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
    writer.writerows(
        rows_out
    )


# ============================================================
# Guardar cambios de tokens mas frecuentes
# ============================================================

with open(
    OUTPUT_TOKEN_CHANGES,
    "w",
    encoding="utf-8-sig",
    newline=""
) as f:

    writer = csv.writer(f)

    writer.writerow([
        "operation",
        "san_fragment",
        "posformer_fragment",
        "count",
    ])

    for (
        operation,
        left,
        right
    ), count in token_change_counts.most_common():

        writer.writerow([
            operation,
            left,
            right,
            count,
        ])


# ============================================================
# Resumen
# ============================================================

summary = []


def out(text=""):
    print(text)
    summary.append(
        str(text)
    )


out()
out("=" * 72)
out("RESUMEN")
out("=" * 72)

out(
    "Casos analizados : {}".format(
        len(rows_out)
    )
)

out()
out("Categorias")

for category, count in category_counts.most_common():

    out(
        "  {:30s}: {:3d} ({:6.2f}%)".format(
            category,
            count,
            pct(
                count,
                len(rows_out)
            )
        )
    )


out()
out("Prioridad de revision")

for priority in [
    "muy_alta",
    "alta",
    "media",
    "baja",
]:

    count = priority_counts[
        priority
    ]

    out(
        "  {:10s}: {:3d} ({:6.2f}%)".format(
            priority,
            count,
            pct(
                count,
                len(rows_out)
            )
        )
    )


affects = sum(
    1
    for row in rows_out
    if row["affects_model_correctness"]
)

favors_san = sum(
    1
    for row in rows_out
    if row["favors_san_annotation"]
)

favors_pos = sum(
    1
    for row in rows_out
    if row["favors_posformer_annotation"]
)


out()
out("Impacto en Exact Match")

out(
    "  Cambian correccion de algun modelo : {} / {} ({:.2f}%)".format(
        affects,
        len(rows_out),
        pct(
            affects,
            len(rows_out)
        )
    )
)

out(
    "  Favorecen especificamente a SAN    : {}".format(
        favors_san
    )
)

out(
    "  Favorecen especificamente PosFormer: {}".format(
        favors_pos
    )
)


out()
out("Cambios de tokens mas frecuentes")

for (
    operation,
    left,
    right
), count in token_change_counts.most_common(15):

    out(
        "  {:7s} {:3d}x : [{}] -> [{}]".format(
            operation,
            count,
            left,
            right
        )
    )


out()
out("Archivos generados")

out(
    "  Clasificacion : {}".format(
        OUTPUT_CSV
    )
)

out(
    "  Cambios token : {}".format(
        OUTPUT_TOKEN_CHANGES
    )
)

out(
    "  Resumen       : {}".format(
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
print("Clasificacion terminada.")
