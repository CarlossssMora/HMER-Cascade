"""Prepare and summarize the SAN/PosFormer ground-truth symLG comparison."""

import argparse
import csv
from pathlib import Path


RESULTS_DIR = Path(__file__).resolve().parent / "resultados"
SOURCE = RESULTS_DIR / "compare_crohme_sources_2014.csv"
WORK = RESULTS_DIR / "san_symlg_eval_2014"


def discrepant_rows():
    with SOURCE.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return [
        row for row in rows
        if row["in_official_result_zip"].strip().lower() == "true"
        and row["san_ground_truth"].split() != row["posformer_ground_truth"].split()
    ]


def without_limits(text):
    return [token for token in text.split() if token != r"\limits"]


def prepare(rows):
    for source, field in (("san", "san_ground_truth"), ("posformer", "posformer_ground_truth")):
        directory = WORK / ("gt_diff_" + source + "_tex")
        directory.mkdir(parents=True, exist_ok=True)
        for row in rows:
            content = "%{}\n${}$\n".format(row["sample_id"], row[field])
            (directory / (row["sample_id"] + ".txt")).write_text(content, encoding="utf-8")
        print("{}: {} archivos".format(directory, len(rows)))


def report(rows):
    metrics_path = WORK / "Results_gt_diff_san_symlg" / "FileMetrics.csv"
    with metrics_path.open(encoding="utf-8-sig", newline="") as handle:
        metrics = {
            Path(row["File"].strip()).stem: row
            for row in csv.DictReader(handle)
        }
    ids = {row["sample_id"] for row in rows}
    if set(metrics) != ids:
        raise ValueError("IDs sin evaluar: {}; IDs inesperados: {}".format(
            sorted(ids - set(metrics)), sorted(set(metrics) - ids)))

    output = []
    for row in rows:
        sid = row["sample_id"]
        only_limits = without_limits(row["san_ground_truth"]) == without_limits(row["posformer_ground_truth"])
        metric = metrics[sid]
        output.append({
            "sample_id": sid,
            "difference_only_limits": only_limits,
            "symLG_equal": metric["Result"].strip() == "Correct",
            "D_B": metric["D_B"],
            "ground_truth_san": row["san_ground_truth"],
            "ground_truth_posformer": row["posformer_ground_truth"],
        })

    report_path = RESULTS_DIR / "ground_truth_symlg_comparison_2014.csv"
    with report_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(output[0]))
        writer.writeheader()
        writer.writerows(output)

    summary = ["GT discrepantes: {}".format(len(output))]
    for group_name, group in (("Solo \\limits", [r for r in output if r["difference_only_limits"]]),
                              ("Otras diferencias", [r for r in output if not r["difference_only_limits"]])):
        equal = [r for r in group if r["symLG_equal"]]
        summary.append("{}: {} muestras, {} symLG iguales, {} distintos".format(
            group_name, len(group), len(equal), len(group) - len(equal)))
    summary.append("Los IDs y las distancias D_B estan en el CSV.")
    summary_path = RESULTS_DIR / "ground_truth_symlg_comparison_2014_summary.txt"
    summary_path.write_text("\n".join(summary) + "\n", encoding="utf-8")
    print("\n".join(summary))
    print(report_path)
    print(summary_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "report"))
    args = parser.parse_args()
    rows = discrepant_rows()
    if not rows:
        raise ValueError("No se encontraron discrepancias de ground truth")
    if args.action == "prepare":
        prepare(rows)
    else:
        report(rows)
