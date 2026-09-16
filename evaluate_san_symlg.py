import csv
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent

BENCHMARK_CSV = ROOT / "benchmark_crohme_2014.csv"
COMPARE_CSV = ROOT / "compare_crohme_sources_2014.csv"

POSFORMER_DIR = ROOT / "PosFormer"
DATA_ZIP = POSFORMER_DIR / "data_crohme.zip"

WORK_DIR = ROOT / "san_symlg_eval_2014"
TEX_DIR = WORK_DIR / "tex"
PRED_SYMLG_DIR = WORK_DIR / "pred_symlg"
GT_SYMLG_DIR = WORK_DIR / "gt_symlg"

SAN_RESULT_ZIP = ROOT / "san_result_2014.zip"

YEAR = "2014"


def normalize_ws(text):
    return " ".join(str(text).strip().split())


def bool_from_csv(value):
    return str(value).strip().lower() in [
        "true", "1", "yes", "si", "sí"
    ]


def canonical_id(name):
    name = str(name).replace("\\", "/")
    name = name.rsplit("/", 1)[-1]

    lower = name.lower()

    for ext in [".jpg", ".jpeg", ".png", ".bmp", ".txt", ".inkml", ".lg"]:
        if lower.endswith(ext):
            name = name[:-len(ext)]
            break

    return name


def reset_dir(path):
    if path.exists():
        shutil.rmtree(path)

    path.mkdir(parents=True, exist_ok=True)


def find_executable(command_name, candidates):
    found = shutil.which(command_name)

    if found:
        return Path(found)

    for candidate in candidates:
        candidate = Path(candidate)

        if candidate.exists():
            return candidate

    return None


def run_command(command, cwd=None):
    print()
    print("Ejecutando:")
    print(" ".join(str(x) for x in command))
    print()

    completed = subprocess.run(
        [str(x) for x in command],
        cwd=str(cwd) if cwd else None,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )

    print(completed.stdout)

    if completed.returncode != 0:
        raise RuntimeError(
            "El comando termino con codigo {}.".format(
                completed.returncode
            )
        )

    return completed.stdout


def locate_symlg_prefix_in_zip(zf, year):
    names = zf.namelist()
    candidates = []

    exact = "data/{}/symLg/".format(year)

    for name in names:
        normalized = name.replace("\\", "/")

        if normalized.startswith(exact):
            candidates.append(exact)
            continue

        marker = "/{}/symLg/".format(year)

        if marker in normalized:
            prefix = normalized.split(marker)[0]
            candidates.append(
                prefix + "/{}/symLg/".format(year)
            )

    candidates = sorted(set(candidates))

    if not candidates:
        raise RuntimeError(
            "No encontre data/{}/symLg dentro de {}.".format(
                year,
                DATA_ZIP
            )
        )

    if exact in candidates:
        return exact

    return candidates[0]


print("=" * 72)
print("PREPARACION Y EVALUACION SAN CON symLG / LgEval")
print("=" * 72)

for required in [BENCHMARK_CSV, COMPARE_CSV, DATA_ZIP]:
    if not required.exists():
        raise FileNotFoundError(
            "No existe el archivo requerido:\n{}".format(
                required
            )
        )

print("Benchmark SAN/PosFormer :", BENCHMARK_CSV)
print("Comparacion de fuentes  :", COMPARE_CSV)
print("data_crohme.zip         :", DATA_ZIP)


official_ids = set()

with open(
    COMPARE_CSV,
    "r",
    encoding="utf-8-sig",
    newline=""
) as f:

    reader = csv.DictReader(f)

    for row in reader:
        if bool_from_csv(
            row.get("in_official_result_zip", "")
        ):
            official_ids.add(
                canonical_id(row["sample_id"])
            )

print()
print("IDs oficiales comparables:", len(official_ids))


san_predictions = {}

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

        sid = canonical_id(
            row["sample_id"]
        )

        if sid not in official_ids:
            continue

        prediction = normalize_ws(
            row.get("san_prediction", "")
        )

        san_predictions[sid] = prediction


missing = sorted(
    official_ids - set(san_predictions)
)

if missing:
    raise RuntimeError(
        "Faltan predicciones SAN para {} IDs. Ejemplos: {}".format(
            len(missing),
            missing[:10]
        )
    )

print("Predicciones SAN cargadas:", len(san_predictions))


WORK_DIR.mkdir(parents=True, exist_ok=True)
reset_dir(TEX_DIR)
reset_dir(PRED_SYMLG_DIR)
reset_dir(GT_SYMLG_DIR)


for sid in sorted(san_predictions):
    prediction = san_predictions[sid]

    output_path = TEX_DIR / "{}.txt".format(sid)

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as f:
        f.write("%{}\n".format(sid))
        f.write("${}$\n".format(prediction))

print()
print(
    "Archivos TEX SAN generados:",
    len(list(TEX_DIR.glob("*.txt")))
)


if SAN_RESULT_ZIP.exists():
    SAN_RESULT_ZIP.unlink()

with zipfile.ZipFile(
    SAN_RESULT_ZIP,
    "w",
    compression=zipfile.ZIP_DEFLATED
) as zf:

    for file_path in sorted(TEX_DIR.glob("*.txt")):
        zf.write(
            file_path,
            arcname=file_path.name
        )

print("ZIP SAN generado:", SAN_RESULT_ZIP)


with zipfile.ZipFile(DATA_ZIP, "r") as zf:
    prefix = locate_symlg_prefix_in_zip(
        zf,
        YEAR
    )

    extracted = 0

    for member in zf.namelist():
        normalized = member.replace("\\", "/")

        if not normalized.startswith(prefix):
            continue

        if normalized.endswith("/"):
            continue

        if not normalized.lower().endswith(".lg"):
            continue

        filename = Path(normalized).name
        sid = canonical_id(filename)

        if sid not in official_ids:
            continue

        target = GT_SYMLG_DIR / filename

        with zf.open(member) as src:
            with open(target, "wb") as dst:
                shutil.copyfileobj(src, dst)

        extracted += 1

print()
print("Ground truths symLg extraidos:", extracted)

if extracted != len(official_ids):
    print(
        "ADVERTENCIA: esperaba {} archivos y extraje {}.".format(
            len(official_ids),
            extracted
        )
    )


tex2_candidates = [
    ROOT / "CoMER" / "convert2symLG" / "bin" / "tex2symlg",
    ROOT / "CoMER" / "convert2symLG" / "tex2symlg",
    ROOT / "convert2symLG" / "bin" / "tex2symlg",
    ROOT / "convert2symLG" / "tex2symlg",
]

evaluate_candidates = [
    ROOT / "CoMER" / "lgeval" / "bin" / "evaluate",
    ROOT / "lgeval" / "bin" / "evaluate",
]

tex2symlg = find_executable(
    "tex2symlg",
    tex2_candidates
)

evaluate = find_executable(
    "evaluate",
    evaluate_candidates
)


print()
print("=" * 72)
print("HERRAMIENTAS")
print("=" * 72)

print(
    "tex2symlg :",
    tex2symlg if tex2symlg else "NO ENCONTRADO"
)

print(
    "evaluate  :",
    evaluate if evaluate else "NO ENCONTRADO"
)


if tex2symlg is None or evaluate is None:
    print()
    print("=" * 72)
    print("PREPARACION COMPLETA")
    print("=" * 72)

    print()
    print(
        "Las predicciones SAN y los GT symLg ya quedaron preparados."
    )

    print()
    print("Predicciones TEX:")
    print(TEX_DIR)

    print()
    print("Ground truth symLg:")
    print(GT_SYMLG_DIR)

    print()
    print("result.zip compatible:")
    print(SAN_RESULT_ZIP)

    print()
    print(
        "Faltan tex2symlg/evaluate en PATH o en una carpeta "
        "CoMER local."
    )

    print()
    print(
        "Clona CoMER dentro de Programas/CoMER o instala las "
        "herramientas oficiales y vuelve a ejecutar este script."
    )

    sys.exit(0)


try:
    run_command(
        [
            tex2symlg,
            TEX_DIR,
            PRED_SYMLG_DIR,
        ],
        cwd=ROOT
    )

except Exception as direct_exc:
    bash = shutil.which("bash")

    if bash is None:
        raise RuntimeError(
            "No pude ejecutar tex2symlg directamente y tampoco "
            "encontre bash.\nError original:\n{}".format(
                direct_exc
            )
        )

    reset_dir(PRED_SYMLG_DIR)

    run_command(
        [
            bash,
            tex2symlg,
            TEX_DIR,
            PRED_SYMLG_DIR,
        ],
        cwd=ROOT
    )


pred_lg_files = list(
    PRED_SYMLG_DIR.glob("*.lg")
)

print(
    "symLG predichos generados:",
    len(pred_lg_files)
)


try:
    run_command(
        [
            evaluate,
            PRED_SYMLG_DIR,
            GT_SYMLG_DIR,
        ],
        cwd=WORK_DIR
    )

except Exception as direct_exc:
    bash = shutil.which("bash")

    if bash is None:
        raise RuntimeError(
            "No pude ejecutar evaluate directamente y tampoco "
            "encontre bash.\nError original:\n{}".format(
                direct_exc
            )
        )

    run_command(
        [
            bash,
            evaluate,
            PRED_SYMLG_DIR,
            GT_SYMLG_DIR,
        ],
        cwd=WORK_DIR
    )


print()
print("=" * 72)
print("EVALUACION symLG TERMINADA")
print("=" * 72)

print()
print("Directorio de trabajo:")
print(WORK_DIR)

print()
print(
    "Pasa la salida de consola y el listado de archivos "
    "generados en san_symlg_eval_2014 para interpretar ExpRate."
)
