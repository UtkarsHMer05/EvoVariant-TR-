#!/usr/bin/env python3
"""Generate the final README dashboards from frozen, hash-checked artifacts.

This is deliberately dependency-free.  It never trains, tunes, or reads the
801-row holdout; it only derives presentation metrics from the already-frozen
946-row joined prediction artifact and the registered Phase 14 receipt.
"""

# ruff: noqa: E501

from __future__ import annotations

import csv
import hashlib
import json
import math
import shutil
import subprocess
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
FINAL_RECEIPT = "artifacts/phase14/phase14_locked_evo2_20260922.json"
JOINED_PREDICTIONS = "research/runs/formal_cpu_20260922/phase14_locked_evo2/predictions_with_local_labels.jsonl"
PROOF = "research/adaptation_attempt/artifacts/caduceus_partial_small_finetune_smoke.json"
OUT = ROOT / "research/figures/final"
SOURCE = OUT / "source"
ADAPTATION_FIGURES = ROOT / "research/adaptation_attempt/figures"
FINAL_REPORTS = ROOT / "research/reports"
AUDITS = ROOT / "artifacts/audits"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(relative: str) -> dict:
    value = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{relative} must contain an object")
    return value


def read_jsonl(relative: str) -> list[dict]:
    rows = [json.loads(line) for line in (ROOT / relative).read_text(encoding="utf-8").splitlines() if line.strip()]
    if not all(isinstance(row, dict) for row in rows):
        raise ValueError(f"{relative} contains a non-object row")
    return rows


def finite(value: object) -> float:
    result = float(value)  # type: ignore[arg-type]
    if not math.isfinite(result):
        raise ValueError(f"non-finite value: {value!r}")
    return result


def text(x: float, y: float, value: object, *, size: int = 16, anchor: str = "start", fill: str = "#172033", weight: str = "400", rotate: int | None = None) -> str:
    transform = f' transform="rotate({rotate} {x:g} {y:g})"' if rotate is not None else ""
    return f'<text x="{x:g}" y="{y:g}" text-anchor="{anchor}" font-family="Arial, sans-serif" font-size="{size}px" font-weight="{weight}" fill="{fill}"{transform}>{escape(str(value))}</text>'


def rect(x: float, y: float, width: float, height: float, fill: str, *, stroke: str = "none", opacity: float = 1.0) -> str:
    return f'<rect x="{x:g}" y="{y:g}" width="{width:g}" height="{height:g}" fill="{fill}" stroke="{stroke}" opacity="{opacity:g}" rx="4"/>'


def line(x1: float, y1: float, x2: float, y2: float, *, stroke: str = "#9aa4b2", width: float = 1.0, dash: str | None = None) -> str:
    extra = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1:g}" y1="{y1:g}" x2="{x2:g}" y2="{y2:g}" stroke="{stroke}" stroke-width="{width:g}"{extra}/>'


def wrap_label(value: object, limit: int = 18) -> str:
    rendered = str(value)
    return rendered if len(rendered) <= limit else rendered[: limit - 1] + "…"


def chart_svg(title: str, subtitle: str, rows: list[dict], *, y_max: float = 1.0, footer: str = "") -> str:
    width, height = 1400, 820
    left, top, plot_width, plot_height = 120, 150, 1210, 510
    body = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="820" viewBox="0 0 1400 820">',
        rect(0, 0, width, height, "#ffffff"),
        text(55, 52, title, size=28, weight="700"),
        text(55, 84, subtitle, size=14, fill="#526070"),
    ]
    for tick in (0.0, 0.25, 0.5, 0.75, 1.0):
        y = top + plot_height - tick * plot_height
        body.extend([line(left, y, left + plot_width, y, stroke="#d8dee8", dash="4 5"), text(left - 12, y + 5, f"{tick:.2f}", size=12, anchor="end", fill="#526070")])
    body.extend([line(left, top, left, top + plot_height, stroke="#526070"), line(left, top + plot_height, left + plot_width, top + plot_height, stroke="#526070")])
    slot = plot_width / max(len(rows), 1)
    bar_width = slot * 0.62
    colors = ["#2563eb", "#059669", "#9333ea", "#d97706", "#0891b2", "#db2777", "#dc2626"]
    for index, row in enumerate(rows):
        value = finite(row["value"])
        value = max(0.0, min(value, y_max))
        x = left + slot * index + (slot - bar_width) / 2
        y = top + plot_height - (value / y_max) * plot_height
        body.extend([
            rect(x, y, bar_width, max(1.0, top + plot_height - y), colors[index % len(colors)], opacity=0.9),
            text(x + bar_width / 2, y - 10 - (index % 2) * 18, f"{finite(row['value']):.6f}", size=12, anchor="middle", fill="#334155"),
            text(x + bar_width / 2, top + plot_height + 28, wrap_label(row["label"]), size=12, anchor="middle", rotate=-28),
        ])
    body.extend([
        text(left + plot_width / 2, height - 68, "metric", size=14, anchor="middle"),
        text(28, top + plot_height / 2, "value", size=14, anchor="middle", rotate=-90),
        text(55, height - 28, footer, size=11, fill="#697586"),
        "</svg>",
    ])
    return "\n".join(body) + "\n"


def proof_svg(proof: dict) -> str:
    width, height = 1400, 820
    encoder_delta = finite(proof["encoder_delta_norm"])
    frozen_delta = finite(proof["frozen_control_delta_norm"])
    scale = 930 / max(encoder_delta, 1e-12)
    body = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="820" viewBox="0 0 1400 820">',
        rect(0, 0, width, height, "#ffffff"),
        text(55, 52, "Controlled encoder-update feasibility proof", size=28, weight="700"),
        text(55, 84, "Recovered PASS evidence; this is not a completed fine-tuning experiment", size=14, fill="#526070"),
        text(55, 145, "Partial-small regime: blocks 12–15 trainable; blocks 0–11 frozen", size=18, weight="700"),
        line(170, 650, 1230, 650, stroke="#526070"),
        rect(230, 650 - min(500, encoder_delta * scale), 260, min(500, encoder_delta * scale), "#2563eb"),
        rect(820, 650 - min(500, frozen_delta * scale), 260, max(1, min(500, frozen_delta * scale)), "#94a3b8"),
        text(360, 690, "encoder parameter", size=16, anchor="middle"),
        text(360, 715, "delta norm", size=16, anchor="middle"),
        text(950, 690, "frozen control", size=16, anchor="middle"),
        text(950, 715, "delta norm", size=16, anchor="middle"),
        text(360, 625 - min(500, encoder_delta * scale), f"{encoder_delta:.15g}", size=16, anchor="middle", fill="#1d4ed8", weight="700"),
        text(950, 625, f"{frozen_delta:.1f}", size=16, anchor="middle", fill="#475569", weight="700"),
        text(55, 770, f"status={proof['status']} · total={proof['total_parameters']:,} · trainable={proof['trainable_parameters']:,} · holdout evaluated={proof['holdout_evaluated']}", size=12, fill="#526070"),
        "</svg>",
    ]
    return "\n".join(body) + "\n"


def workflow_svg() -> str:
    width, height = 1600, 700
    stages = [
        ("frozen\nhead", "PASS", "#059669"),
        ("trial 0\nHPO", "INCOMPLETE", "#d97706"),
        ("partial\nsmall", "NOT STARTED", "#94a3b8"),
        ("partial\nlarge", "NOT STARTED", "#94a3b8"),
        ("full", "DEFERRED", "#94a3b8"),
        ("selection", "OPEN", "#d97706"),
        ("801", "CLOSED", "#059669"),
    ]
    body = ['<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="700" viewBox="0 0 1600 700">', rect(0, 0, width, height, "#ffffff"), text(55, 58, "Post-hoc Caduceus adaptation workflow state", size=28, weight="700"), text(55, 91, "TRAIN-only adaptation remains separate from the frozen temporal baseline", size=14, fill="#526070")]
    start_x, box_w, gap, y = 60, 190, 35, 260
    for index, (label, status, color) in enumerate(stages):
        x = start_x + index * (box_w + gap)
        if index:
            body.append(line(x - gap + 5, y + 55, x - 8, y + 55, stroke="#94a3b8", width=3))
            body.append(f'<polygon points="{x - 8},{y + 55} {x - 23},{y + 47} {x - 23},{y + 63}" fill="#94a3b8"/>')
        body.extend([rect(x, y, box_w, 125, color, opacity=0.14, stroke=color), text(x + box_w / 2, y + 42, label.replace("\n", " / "), size=18, anchor="middle", weight="700"), text(x + box_w / 2, y + 82, status, size=13, anchor="middle", fill=color, weight="700")])
    body.extend([text(60, 520, "Locked boundaries", size=18, weight="700"), text(60, 555, "801-row validation was not opened. The historical 946-row temporal cohort was not used for adaptation selection.", size=15, fill="#334155"), text(60, 595, "The only retained encoder evidence is a one-step feasibility proof with a nonzero encoder delta and zero frozen-control delta.", size=15, fill="#334155"), "</svg>"])
    return "\n".join(body) + "\n"


def write_figure(stem: str, svg: str, source: dict, directory: Path) -> list[str]:
    directory.mkdir(parents=True, exist_ok=True)
    svg_path = directory / f"{stem}.svg"
    svg_path.write_text(svg, encoding="utf-8")
    outputs = [str(svg_path.relative_to(ROOT))]
    converter = shutil.which("rsvg-convert")
    if converter:
        for suffix, option in ((".png", "--format=png"), (".pdf", "--format=pdf")):
            target = directory / f"{stem}{suffix}"
            result = subprocess.run([converter, option, "-o", str(target), str(svg_path)], capture_output=True, text=True, check=False)
            if result.returncode == 0 and target.is_file():
                outputs.append(str(target.relative_to(ROOT)))
    source = dict(source)
    source["outputs"] = outputs
    source["output_sha256"] = {path: sha256(ROOT / path) for path in outputs}
    source_path = directory / f"{stem}.json" if directory != OUT else SOURCE / f"{stem}.json"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text(json.dumps(source, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return outputs + [str(source_path.relative_to(ROOT))]


def main() -> int:
    receipt = read_json(FINAL_RECEIPT)
    rows = read_jsonl(JOINED_PREDICTIONS)
    proof = read_json(PROOF)
    if len(rows) != 946 or {row.get("split") for row in rows} != {"LOCKED_TEST"}:
        raise SystemExit("joined predictions are not exactly the 946-row locked cohort")
    if any(row.get("remote_labels_transported") is not False for row in rows):
        raise SystemExit("joined predictions contain transported labels")
    if any("label" not in row or "prediction" not in row or "calibrated_score" not in row for row in rows):
        raise SystemExit("joined predictions lack required local fields")
    labels = [int(row["label"]) for row in rows]
    predictions = [int(row["prediction"]) for row in rows]
    probabilities = [finite(row["calibrated_score"]) for row in rows]
    tp = sum(label == 1 and pred == 1 for label, pred in zip(labels, predictions, strict=True))
    tn = sum(label == 0 and pred == 0 for label, pred in zip(labels, predictions, strict=True))
    fp = sum(label == 0 and pred == 1 for label, pred in zip(labels, predictions, strict=True))
    fn = sum(label == 1 and pred == 0 for label, pred in zip(labels, predictions, strict=True))
    precision = tp / (tp + fp)
    recall = tp / (tp + fn)
    specificity = tn / (tn + fp)
    negative_f1 = 2 * tn / (2 * tn + fp + fn)
    positive_f1 = 2 * precision * recall / (precision + recall)
    probability_mae = sum(abs(label - probability) for label, probability in zip(labels, probabilities, strict=True)) / len(labels)
    metrics = {
        "AUROC": finite(receipt["metrics"]["auroc"]),
        "AUPRC": finite(receipt["metrics"]["auprc"]),
        "Accuracy": finite(receipt["metrics"]["probability_metrics"]["accuracy"]),
        "Balanced Accuracy": (recall + specificity) / 2,
        "Precision": precision,
        "Recall": recall,
        "Specificity": specificity,
        "F1": positive_f1,
        "MCC": (tp * tn - fp * fn) / math.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)),
        "Brier": finite(receipt["metrics"]["probability_metrics"]["brier"]),
        "NLL": finite(receipt["metrics"]["probability_metrics"]["nll"]),
        "ECE": finite(receipt["metrics"]["probability_metrics"]["ece"]),
        "Probability MAE": probability_mae,
    }
    expected = {"TP": 333, "TN": 465, "FP": 71, "FN": 77}
    observed = {"TP": tp, "TN": tn, "FP": fp, "FN": fn}
    if observed != expected:
        raise SystemExit(f"confusion counts changed: expected {expected}, observed {observed}")
    if abs(metrics["F1"] - 0.8181818181818182) > 1e-12:
        raise SystemExit("derived F1 does not match the registered frozen result")
    if proof.get("status") != "PASS" or proof.get("completed_fine_tuning_experiment") is not False:
        raise SystemExit("adaptation proof record is not explicitly a PASS feasibility proof")

    source_hashes = {path: sha256(ROOT / path) for path in (FINAL_RECEIPT, JOINED_PREDICTIONS, PROOF)}
    base_source = {"generator": "scripts/generate_final_readme_figures.py", "source_sha256": source_hashes, "locked_test_rows": len(rows), "holdout_used_for_derivation": False}
    table_rows = [{"metric": name, "value": value, "source": FINAL_RECEIPT if name not in {"Balanced Accuracy", "Precision", "Recall", "Specificity", "F1", "MCC", "Probability MAE"} else JOINED_PREDICTIONS} for name, value in metrics.items()]
    table_payload = {"status": "PASS", "source_sha256": source_hashes, "confusion": observed, "metrics": table_rows, "derivation": "registered receipt plus fixed-threshold calculations over frozen joined predictions; no retuning"}
    FINAL_REPORTS.mkdir(parents=True, exist_ok=True)
    (FINAL_REPORTS / "final_metrics_table.json").write_text(json.dumps(table_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with (FINAL_REPORTS / "final_metrics_table.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["metric", "value", "source"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(table_rows)

    final_figures = []
    final_figures += write_figure("final_classification_metrics", chart_svg("Frozen temporal baseline: classification metrics", "946 locked rows · threshold and predictions are frozen", [{"label": key, "value": metrics[key]} for key in ("Accuracy", "Balanced Accuracy", "Precision", "Recall", "Specificity", "F1", "MCC")], footer=f"TP={tp} · TN={tn} · FP={fp} · FN={fn}"), {**base_source, "figure_id": "final_classification_metrics", "metrics": metrics}, OUT)
    final_figures += write_figure("final_probability_quality", chart_svg("Frozen temporal baseline: probability quality", "946 locked rows · source values are the registered Phase 14 receipt", [{"label": key, "value": metrics[key]} for key in ("AUROC", "AUPRC", "Brier", "NLL", "ECE", "Probability MAE")], y_max=1.0, footer="Lower is better for Brier, NLL, ECE, and probability MAE; no post-test tuning"), {**base_source, "figure_id": "final_probability_quality", "metrics": metrics}, OUT)
    negative_support, positive_support = tn + fp, tp + fn
    f1_rows = [{"label": "negative F1", "value": negative_f1}, {"label": "positive F1", "value": positive_f1}, {"label": "macro F1", "value": (negative_f1 + positive_f1) / 2}, {"label": "weighted F1", "value": (negative_support * negative_f1 + positive_support * positive_f1) / len(rows)}, {"label": "micro F1", "value": metrics["Accuracy"]}]
    final_figures += write_figure("final_f1_metrics", chart_svg("Frozen temporal baseline: F1 metrics", "Derived from the frozen local labels and predictions at the registered threshold", f1_rows, footer="No threshold search or post-test retuning was performed"), {**base_source, "figure_id": "final_f1_metrics", "f1_metrics": f1_rows}, OUT)

    adaptation_base = {"generator": "scripts/generate_final_readme_figures.py", "source_sha256": {PROOF: source_hashes[PROOF]}, "holdout_used": False}
    adaptation_figures = []
    adaptation_figures += write_figure("encoder_update_proof", proof_svg(proof), {**adaptation_base, "figure_id": "encoder_update_proof", "status": proof["status"], "interpretation": "controlled encoder-update feasibility proof; not completed fine-tuning"}, ADAPTATION_FIGURES)
    adaptation_figures += write_figure("adaptation_workflow", workflow_svg(), {**adaptation_base, "figure_id": "adaptation_workflow", "workflow_status": "HPO incomplete; selection open; 801 closed"}, ADAPTATION_FIGURES)

    inventory = {
        "schema_version": "final-project-polish-v1",
        "status": "PASS",
        "inherited_phase17_inventory": "research/reports/phase17/FIGURE_INVENTORY.json",
        "inherited_rendered_family_count": 39,
        "new_final_figures": sorted({path.rsplit("/", 1)[-1].rsplit(".", 1)[0] for path in final_figures if path.endswith(".svg")}),
        "new_adaptation_figures": sorted({path.rsplit("/", 1)[-1].rsplit(".", 1)[0] for path in adaptation_figures if path.endswith(".svg")}),
        "source_hashes": source_hashes,
        "notes": "Existing Phase 17 figures remain unchanged; this inventory records the final polish additions and their source-derived outputs.",
    }
    AUDITS.mkdir(parents=True, exist_ok=True)
    (AUDITS / "FINAL_FIGURE_INVENTORY.json").write_text(json.dumps(inventory, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    gallery = ["<!doctype html><meta charset='utf-8'><title>EvoVariant final polish figures</title><h1>Final polish additions</h1>"]
    for path in sorted(set(final_figures + adaptation_figures)):
        if path.endswith(".svg"):
            gallery.append(f"<h2>{escape(path)}</h2><img src='../../{escape(path)}' style='max-width:100%;border:1px solid #ddd'>")
    (AUDITS / "final_polish_gallery.html").write_text("\n".join(gallery) + "\n", encoding="utf-8")
    (AUDITS / "final_polish_contact_sheet.svg").write_text("\n".join(["<svg xmlns='http://www.w3.org/2000/svg' width='1200' height='500' viewBox='0 0 1200 500'>", rect(0, 0, 1200, 500, "#ffffff"), text(35, 45, "Final polish figure inventory", size=24, weight="700"), text(35, 75, "See final_polish_gallery.html for the rendered additions", size=14, fill="#526070"), *[rect(45 + (index % 3) * 380, 120 + (index // 3) * 150, 330, 100, "#eef2ff", stroke="#2563eb") + text(210 + (index % 3) * 380, 165 + (index // 3) * 150, label, size=15, anchor="middle", weight="700") for index, label in enumerate(inventory["new_final_figures"] + inventory["new_adaptation_figures"])], "</svg>"]), encoding="utf-8")
    print(json.dumps({"status": "PASS", "metrics": str(FINAL_REPORTS / "final_metrics_table.json"), "final_figures": inventory["new_final_figures"], "adaptation_figures": inventory["new_adaptation_figures"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
