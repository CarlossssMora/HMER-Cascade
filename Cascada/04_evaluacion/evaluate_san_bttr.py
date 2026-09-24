"""Evalúa SAN congelado en los tres test de BTTR, sin alterar las imágenes."""

import argparse
import csv
import gc
import os
import sys
import time
from pathlib import Path

import cv2
import torch


ROOT = Path(__file__).resolve().parents[2]
SAN_DIR = ROOT / "SAN"
BTTR_DIR = ROOT / "data" / "BTTR"
POS_DIR = ROOT / "data" / "Modelo2"
OUT_DIR = Path(__file__).resolve().parent / "resultados"
YEARS = ("2014", "2016", "2019")


def parse_captions(path):
    captions = {}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            sample_id, label = line.rstrip("\r\n").split("\t", 1)
            if sample_id in captions:
                raise ValueError("ID repetido en {}: {}".format(path, sample_id))
            captions[sample_id] = " ".join(label.split())
    return captions


def without_limits(text):
    return " ".join(token for token in text.split() if token != "\\limits")


def san_prediction_to_latex(prediction):
    # Misma conversión que 01_seleccion/benchmark_crohme.py.
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
        children.setdefault(parent_id, []).append((node_id, str(item[3])))

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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", choices=YEARS + ("all",), default="all")
    parser.add_argument("--max-samples", type=int, default=None)
    parser.add_argument("--suffix", default="")
    args = parser.parse_args()
    years = YEARS if args.year == "all" else (args.year,)

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA no está disponible")
    device = torch.device("cuda")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    sys.path.insert(0, str(SAN_DIR))
    old_cwd = os.getcwd()
    try:
        os.chdir(SAN_DIR)
        from utils import load_config, load_checkpoint
        from infer.Backbone import Backbone
        from dataset import Words

        params = load_config("14.yaml")
        params["device"] = device
        words = Words(params["word_path"])
        params["word_num"] = len(words)
        params["struct_num"] = 7
        params["words"] = words
        model = Backbone(params).to(device)
        load_checkpoint(model, None, params["checkpoint"])
    finally:
        os.chdir(old_cwd)

    model.eval()
    model.requires_grad_(False)
    print("GPU: {}".format(torch.cuda.get_device_name(0)), flush=True)
    print("Checkpoint: SAN/checkpoints/SAN_decoder/best.pth", flush=True)

    fields = ["sample_id", "status", "error", "height", "width", "ground_truth_bttr",
              "ground_truth_posformer", "san_prediction", "bttr_exact", "bttr_no_limits",
              "posformer_exact", "posformer_no_limits", "time_ms"]

    with torch.inference_mode():
        for year in years:
            bttr_gt = parse_captions(BTTR_DIR / year / "caption.txt")
            pos_gt = parse_captions(POS_DIR / year / "caption.txt")
            if set(bttr_gt) != set(pos_gt):
                raise RuntimeError("Los IDs de BTTR y PosFormer no coinciden en {}".format(year))
            ids = list(bttr_gt)
            if args.max_samples is not None:
                ids = ids[:args.max_samples]
            output = OUT_DIR / "san_bttr_{}{}.csv".format(year, args.suffix)
            counts = {"valid": 0, "errors": 0, "bttr_exact": 0, "bttr_no_limits": 0,
                      "posformer_exact": 0, "posformer_no_limits": 0}

            first = cv2.imread(str(BTTR_DIR / year / (ids[0] + ".bmp")), cv2.IMREAD_GRAYSCALE)
            if first is None:
                raise RuntimeError("Falta primera imagen de {}".format(year))
            warm = torch.as_tensor(first, dtype=torch.float32, device=device)[None, None] / 255.0
            warm_mask = torch.ones_like(warm)
            for _ in range(3):
                model(warm, warm_mask)
            torch.cuda.synchronize()
            del warm, warm_mask, first

            print("{}: {} muestras, salida {}".format(year, len(ids), output), flush=True)
            with output.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                for index, sample_id in enumerate(ids, start=1):
                    row = {key: "" for key in fields}
                    row["sample_id"] = sample_id
                    row["ground_truth_bttr"] = bttr_gt[sample_id]
                    row["ground_truth_posformer"] = pos_gt[sample_id]
                    try:
                        image_path = BTTR_DIR / year / (sample_id + ".bmp")
                        image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
                        if image is None:
                            raise FileNotFoundError(str(image_path))
                        row["height"], row["width"] = image.shape
                        tensor = torch.as_tensor(image, dtype=torch.float32, device=device)[None, None] / 255.0
                        mask = torch.ones_like(tensor)
                        torch.cuda.synchronize()
                        start = time.perf_counter()
                        prediction = model(tensor, mask)
                        torch.cuda.synchronize()
                        row["time_ms"] = "{:.6f}".format((time.perf_counter() - start) * 1000.0)
                        latex = san_prediction_to_latex(prediction)
                        row["san_prediction"] = latex
                        row["bttr_exact"] = int(latex == bttr_gt[sample_id])
                        row["bttr_no_limits"] = int(without_limits(latex) == without_limits(bttr_gt[sample_id]))
                        row["posformer_exact"] = int(latex == pos_gt[sample_id])
                        row["posformer_no_limits"] = int(without_limits(latex) == without_limits(pos_gt[sample_id]))
                        row["status"] = "ok"
                        counts["valid"] += 1
                        for key in ("bttr_exact", "bttr_no_limits", "posformer_exact", "posformer_no_limits"):
                            counts[key] += row[key]
                        del tensor, mask, prediction, image
                    except Exception as exc:
                        row["status"] = "error"
                        row["error"] = repr(exc)
                        counts["errors"] += 1
                        print("ERROR {} {}: {}".format(year, sample_id, exc), flush=True)
                        if "out of memory" in str(exc).lower():
                            writer.writerow(row)
                            handle.flush()
                            raise
                    writer.writerow(row)
                    handle.flush()
                    if index == 1 or index % 100 == 0 or index == len(ids):
                        print("{} [{}/{}] válidas={} errores={} BTTR={}/{}".format(
                            year, index, len(ids), counts["valid"], counts["errors"],
                            counts["bttr_exact"], counts["valid"]), flush=True)
            print("{} resumen: {}".format(year, counts), flush=True)
            gc.collect()


if __name__ == "__main__":
    main()
