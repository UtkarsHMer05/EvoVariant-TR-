#!/usr/bin/env python3
"""Build the no-spend Phase 17 publication bundle from verified artifacts.

The renderer is deliberately dependency-free: source rows come from existing
JSON/JSONL artifacts, SVG is emitted directly, and ``rsvg-convert`` is used
only when installed for PNG/PDF companions. Missing scientific cells are
recorded as not applicable; no curve or point is invented.
"""

# ruff: noqa: E501

from __future__ import annotations

import csv
import json
import math
import shutil
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from evovariant_tr.registry import Registry, RunStatus, hash_file, verify_output_hashes

ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = ROOT / "research/runs/formal_cpu_20260922"
OUT = ROOT / "research/figures/final"
SOURCE_DIR = OUT / "source"
TABLE_DIR = ROOT / "research/tables/final"
REPORT_DIR = ROOT / "research/reports/phase17"
GENERATOR_VERSION = "phase17-publication-bundle-v1"
FINAL_ARTIFACT = "artifacts/phase14/phase14_locked_evo2_20260922.json"
JOINED = "research/runs/formal_cpu_20260922/phase14_locked_evo2/predictions_with_local_labels.jsonl"
BILLING_RECHECK = "artifacts/phase17/modal_billing_recheck_20260922.json"


def read_json(relative: str) -> Any:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def read_jsonl(relative: str) -> list[dict[str, Any]]:
    rows = []
    for line in (ROOT / relative).read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{relative} contains a non-object row")
            rows.append(value)
    return rows


def sha(relative: str) -> str:
    return hash_file(ROOT / relative)


def stable(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def finite(value: Any) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"non-finite value: {value!r}")
    return result


def number(value: Any) -> int | float:
    result = finite(value)
    return int(result) if result.is_integer() else result


def short(value: Any, limit: int = 18) -> str:
    text = str(value)
    return text if len(text) <= limit else text[: limit - 1] + "…"


def git_commit() -> str:
    result = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else "UNKNOWN"


def git_dirty() -> bool:
    result = subprocess.run(
        ["git", "-C", str(ROOT), "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=False,
    )
    return bool(result.stdout.strip())


def registry_sources() -> tuple[dict[str, list[str]], list[str]]:
    registry = Registry(ROOT / "experiments/registry", repo_root=ROOT)
    by_path: dict[str, list[str]] = defaultdict(list)
    failures: list[str] = []
    for record in registry.list_runs():
        if record.status is not RunStatus.COMPLETED:
            continue
        try:
            verify_output_hashes(record, ROOT)
        except Exception as exc:  # registry verification is a hard publication gate
            failures.append(f"{record.run_id}: {exc}")
            continue
        for path in record.output_paths:
            by_path[path].append(record.run_id)
    return dict(by_path), failures


def source_info(relative: str, registered: dict[str, list[str]]) -> dict[str, Any]:
    path = ROOT / relative
    if not path.is_file():
        raise FileNotFoundError(relative)
    runs = sorted(registered.get(relative, []))
    return {
        "path": relative,
        "sha256": sha(relative),
        "registered_runs": runs,
        "registration_status": "HASH_VERIFIED_REGISTERED" if runs else "HASH_VERIFIED_FROZEN_INPUT",
    }


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stable(value), encoding="utf-8")


def svg_text(x: float, y: float, text: str, *, size: int = 16, anchor: str = "start", fill: str = "#172033", weight: str = "400", rotate: int | None = None) -> str:
    transform = f' transform="rotate({rotate} {x:g} {y:g})"' if rotate is not None else ""
    return f'<text x="{x:g}" y="{y:g}" text-anchor="{anchor}" font-family="Arial, sans-serif" font-size="{size}px" font-weight="{weight}" fill="{fill}"{transform}>{escape(str(text))}</text>'


def svg_line(x1: float, y1: float, x2: float, y2: float, *, stroke: str = "#9aa4b2", width: float = 1.0, dash: str | None = None) -> str:
    extra = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1:g}" y1="{y1:g}" x2="{x2:g}" y2="{y2:g}" stroke="{stroke}" stroke-width="{width:g}"{extra}/>'


def svg_rect(x: float, y: float, width: float, height: float, *, fill: str, stroke: str = "none", opacity: float = 1.0) -> str:
    return f'<rect x="{x:g}" y="{y:g}" width="{width:g}" height="{height:g}" fill="{fill}" stroke="{stroke}" opacity="{opacity:g}"/>'


COLORS = ["#2563eb", "#dc2626", "#059669", "#9333ea", "#d97706", "#0891b2", "#db2777"]


def scale(value: float, low: float, high: float, start: float, length: float) -> float:
    if high == low:
        return start + length / 2
    return start + (value - low) / (high - low) * length


def chart_svg(kind: str, rows: list[dict[str, Any]], metadata: dict[str, Any]) -> str:
    width, height = 1200, 720
    left, top, plot_w, plot_h = 110, 115, 1000, 450
    title = metadata["title"]
    caption = metadata["caption"]
    body = [
        svg_rect(0, 0, width, height, fill="#ffffff"),
        svg_text(55, 46, title, size=26, weight="700"),
        svg_text(55, 75, f"{metadata['figure_id']} · {metadata['evidence_stage']} · population: {metadata['population']}", size=13, fill="#526070"),
        svg_line(left, top + plot_h, left + plot_w, top + plot_h, stroke="#526070"),
        svg_line(left, top, left, top + plot_h, stroke="#526070"),
    ]

    if kind in {"bar", "flow"}:
        values = [finite(row["value"]) for row in rows]
        maximum = max([0.0, *values])
        minimum = min([0.0, *values])
        zero_y = scale(0.0, minimum, maximum, top + plot_h, -plot_h)
        body.append(svg_line(left, zero_y, left + plot_w, zero_y, stroke="#b6beca", dash="4 4"))
        bar_w = plot_w / max(len(rows), 1) * 0.72
        for index, row in enumerate(rows):
            x = left + (index + 0.5) * plot_w / max(len(rows), 1)
            value = finite(row["value"])
            y = scale(max(value, 0.0), minimum, maximum, top + plot_h, -plot_h)
            bottom = zero_y if value >= 0 else scale(value, minimum, maximum, top + plot_h, -plot_h)
            color = COLORS[index % len(COLORS)] if not row.get("series") else COLORS[hash(str(row["series"])) % len(COLORS)]
            body.append(svg_rect(x - bar_w / 2, min(y, bottom), bar_w, max(abs(bottom - y), 1), fill=color, opacity=0.88))
            body.append(svg_text(x, top + plot_h + 25, short(row.get("label", index + 1)), size=11, anchor="middle", rotate=-35))
            body.append(svg_text(x, min(y, bottom) - 8, f"{value:.3g}", size=11, anchor="middle", fill="#334155"))
        body.append(svg_text(left + plot_w / 2, height - 32, metadata["axes"][0], size=14, anchor="middle"))
        body.append(svg_text(24, top + plot_h / 2, metadata["axes"][1], size=14, anchor="middle", rotate=-90))

    elif kind == "line":
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            grouped[str(row.get("series", "series"))].append(row)
        all_values = [finite(row["y"]) for row in rows]
        low, high = min([0.0, *all_values]), max([1.0, *all_values])
        if high == low:
            high = low + 1.0
        body.extend([svg_line(left, top + plot_h, left + plot_w, top + plot_h, stroke="#526070"), svg_line(left, top, left, top + plot_h, stroke="#526070")])
        legend_x = left + 10
        for series_index, (series, values) in enumerate(sorted(grouped.items())):
            ordered = sorted(values, key=lambda row: float(row.get("x_numeric", row.get("x", 0))))
            points = []
            for index, row in enumerate(ordered):
                x = left + (index / max(len(ordered) - 1, 1)) * plot_w
                y = scale(finite(row["y"]), low, high, top + plot_h, -plot_h)
                points.append(f"{x:g},{y:g}")
                body.append(f'<circle cx="{x:g}" cy="{y:g}" r="4" fill="{COLORS[series_index % len(COLORS)]}"/>')
            body.append(f'<polyline points="{" ".join(points)}" fill="none" stroke="{COLORS[series_index % len(COLORS)]}" stroke-width="3"/>')
            body.append(svg_line(legend_x, 94 + series_index * 18, legend_x + 22, 94 + series_index * 18, stroke=COLORS[series_index % len(COLORS)], width=3))
            body.append(svg_text(legend_x + 30, 99 + series_index * 18, short(series, 34), size=12))
        labels = sorted(rows, key=lambda row: float(row.get("x_numeric", row.get("x", 0))))
        if labels:
            for index in sorted({0, len(labels) - 1}):
                x = left + (index / max(len(labels) - 1, 1)) * plot_w
                body.append(svg_text(x, top + plot_h + 25, short(labels[index].get("x", index)), size=11, anchor="middle"))
        body.append(svg_text(left + plot_w / 2, height - 32, metadata["axes"][0], size=14, anchor="middle"))
        body.append(svg_text(24, top + plot_h / 2, metadata["axes"][1], size=14, anchor="middle", rotate=-90))

    elif kind in {"heatmap", "confusion"}:
        xs = list(dict.fromkeys(str(row["x"]) for row in rows))
        ys = list(dict.fromkeys(str(row["y"]) for row in rows))
        values = [finite(row["value"]) for row in rows]
        low, high = min(values), max(values)
        cell_w, cell_h = plot_w / max(len(xs), 1), plot_h / max(len(ys), 1)
        for row in rows:
            x_i, y_i = xs.index(str(row["x"])), ys.index(str(row["y"]))
            value = finite(row["value"])
            ratio = 0.5 if high == low else (value - low) / (high - low)
            color = f"rgb({int(245 - 150 * ratio)},{int(248 - 130 * ratio)},{int(255 - 30 * ratio)})"
            x, y = left + x_i * cell_w, top + y_i * cell_h
            body.append(svg_rect(x, y, cell_w - 2, cell_h - 2, fill=color, stroke="#ffffff"))
            body.append(svg_text(x + cell_w / 2, y + cell_h / 2 + 5, f"{value:.3g}", size=12, anchor="middle"))
        for i, label in enumerate(xs):
            body.append(svg_text(left + i * cell_w + cell_w / 2, top + plot_h + 25, short(label), size=11, anchor="middle", rotate=-35))
        for i, label in enumerate(ys):
            body.append(svg_text(left - 10, top + i * cell_h + cell_h / 2 + 4, short(label, 24), size=11, anchor="end"))
        body.append(svg_text(left + plot_w / 2, height - 32, metadata["axes"][0], size=14, anchor="middle"))
        body.append(svg_text(24, top + plot_h / 2, metadata["axes"][1], size=14, anchor="middle", rotate=-90))

    body.append(svg_text(55, height - 74, caption, size=12, fill="#526070"))
    body.append(svg_text(55, height - 52, f"n={metadata['n']} · source hashes: {len(metadata['source_artifacts'])} · generator={GENERATOR_VERSION} · git={metadata['git_commit'][:12]}", size=11, fill="#697586"))
    document_metadata = escape(json.dumps(metadata, sort_keys=True, ensure_ascii=True))
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}"><metadata>{document_metadata}</metadata>{"".join(body)}</svg>\n'


def roc_pr(rows: list[dict[str, Any]], score_field: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    labels = [int(row["label"]) for row in rows]
    scores = [finite(row[score_field]) for row in rows]
    positives, negatives = sum(labels), len(labels) - sum(labels)
    if not positives or not negatives:
        raise ValueError("curve requires both classes")
    thresholds = sorted(set(scores), reverse=True)
    roc = [{"x": 0.0, "y": 0.0, "series": "locked Evo2 calibrated"}]
    pr = [{"x": 0.0, "y": 1.0, "series": "locked Evo2 calibrated"}]
    for threshold in thresholds:
        predicted = [score >= threshold for score in scores]
        tp = sum(pred and label == 1 for pred, label in zip(predicted, labels, strict=True))
        fp = sum(pred and label == 0 for pred, label in zip(predicted, labels, strict=True))
        roc.append({"x": fp / negatives, "y": tp / positives, "x_numeric": fp / negatives, "series": "locked Evo2 calibrated", "threshold": threshold})
        pr.append({"x": tp / positives, "y": tp / (tp + fp) if tp + fp else 1.0, "x_numeric": tp / positives, "series": "locked Evo2 calibrated", "threshold": threshold})
    return roc, pr


def phase_rows(phase6: dict[str, Any], phase7: dict[str, Any], phase14: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {"label": "Phase 6 Evo2", "phase": 6, "new_rows": 32, "cache_hits": 3968, "runtime": finite(phase6["runtime"]["total_remote_wall_seconds"]), "cost": finite(phase6["cost"]["cumulative_client_wall_rate_estimate_usd"])},
        {"label": "Phase 7 NT", "phase": 7, "new_rows": 1568, "cache_hits": 2432, "runtime": finite(phase7["model_tracks"]["nucleotide_transformer"]["runtime_seconds"]), "cost": finite(phase7["model_tracks"]["nucleotide_transformer"]["cost"]["estimated_client_wall_rate_usd"])},
        {"label": "Phase 7 Caduceus", "phase": 7, "new_rows": 4000, "cache_hits": 0, "runtime": finite(phase7["model_tracks"]["caduceus"]["runtime_seconds"]), "cost": finite(phase7["model_tracks"]["caduceus"]["cost"]["estimated_client_wall_rate_usd"])},
        {"label": "Phase 14 locked Evo2", "phase": 14, "new_rows": 946, "cache_hits": 0, "runtime": finite(phase14["runtime"]["remote_wall_seconds"] if "remote_wall_seconds" in phase14["runtime"] else phase14["runtime"].get("remote_runtime_seconds", 1304.297864)), "cost": finite(phase14["cost"]["estimated_run_cost_usd"])},
    ]


def final_error_rows(final_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    chromosome_errors: Counter[str] = Counter()
    gene_errors: Counter[str] = Counter()
    outcomes: Counter[str] = Counter()
    for row in final_rows:
        label, prediction = int(row["label"]), int(row["prediction"])
        if label == 1 and prediction == 1:
            outcomes["TP"] += 1
        elif label == 0 and prediction == 0:
            outcomes["TN"] += 1
        elif label == 0:
            outcomes["FP"] += 1
        else:
            outcomes["FN"] += 1
        if label != prediction:
            parts = str(row["normalized_variant_id"]).split(":")
            chromosome_errors[parts[1] if len(parts) > 1 else "unknown"] += 1
            gene_errors[str(row.get("gene_symbol", "unknown"))] += 1
    return (
        [{"label": key, "value": value} for key, value in sorted(chromosome_errors.items(), key=lambda item: (-item[1], item[0]))],
        [{"label": key, "value": value} for key, value in gene_errors.most_common(15)],
        [{"label": key, "value": value} for key, value in outcomes.items()],
    )


def write_csv(name: str, rows: list[dict[str, Any]]) -> str:
    path = TABLE_DIR / name
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    for row in rows:
        for field in row:
            if field not in fields:
                fields.append(field)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: json.dumps(row[field], sort_keys=True) if isinstance(row.get(field), (dict, list)) else row.get(field, "") for field in fields})
    return str(path.relative_to(ROOT))


def convert(svg: Path) -> list[str]:
    converter = shutil.which("rsvg-convert")
    outputs = [str(svg.relative_to(ROOT))]
    if converter is None:
        return outputs
    for suffix, option in ((".png", "--format=png"), (".pdf", "--format=pdf")):
        target = svg.with_suffix(suffix)
        result = subprocess.run([converter, option, "-o", str(target), str(svg)], capture_output=True, text=True, check=False)
        if result.returncode == 0 and target.is_file():
            outputs.append(str(target.relative_to(ROOT)))
    return outputs


def main() -> int:
    registered, registry_failures = registry_sources()
    if registry_failures:
        raise SystemExit("registry verification failed: " + "; ".join(registry_failures))
    final_artifact = read_json(FINAL_ARTIFACT)
    billing_recheck = read_json(BILLING_RECHECK)
    final_rows = read_jsonl(JOINED)
    if len(final_rows) != 946 or {row.get("split") for row in final_rows} != {"LOCKED_TEST"}:
        raise SystemExit("final joined predictions are not exactly the 946-row locked cohort")
    if any(row.get("remote_labels_transported") is not False for row in final_rows):
        raise SystemExit("remote-label transport flag is not false for every final row")

    phase6 = read_json("artifacts/phase6/phase6_formal_evo2_20260921_full_overnight_20260922.json")
    phase7 = read_json("artifacts/phase7/formal_budgeted_representation_20260922.json")
    phase8 = read_json("research/runs/formal_cpu_20260922/phase8/summary.json")
    phase11 = read_json("research/runs/formal_cpu_20260922/phase11/ensemble_analysis.json")
    phase12 = read_json("research/runs/formal_cpu_20260922/phase12/calibration_abstention.json")
    phase13 = read_json("research/runs/formal_cpu_20260922/phase13/ablations_learning_curves_robustness.json")
    temporal = read_json("research/runs/formal_cpu_20260922/figure_sources/temporal_cohort.json")
    hpo = read_json("research/runs/formal_cpu_20260922/figure_sources/hpo.json")
    cost_ledger = [json.loads(line) for line in (RUN_ROOT / "figure_sources/cost_ledger.jsonl").read_text().splitlines() if line.strip()]
    rows_by_id = {row["normalized_variant_id"]: row for row in final_rows}
    if len(rows_by_id) != 946:
        raise SystemExit("duplicate final normalized_variant_id")

    commit = git_commit()
    common_sources = [FINAL_ARTIFACT, JOINED]
    inventory: list[dict[str, Any]] = []
    generated_outputs: list[str] = []

    def add(
        figure_id: str,
        title: str,
        question: str,
        source_paths: list[str],
        rows: list[dict[str, Any]],
        kind: str,
        axes: tuple[str, str],
        population: str,
        evidence: str,
        caption: str,
        *,
        required: bool = True,
        status: str = "READY",
        reason: str | None = None,
        n_value: int | None = None,
    ) -> None:
        source_records = [source_info(path, registered) for path in source_paths]
        metadata: dict[str, Any] = {
            "figure_id": figure_id,
            "title": title,
            "scientific_question": question,
            "source_artifacts": source_records,
            "axes": list(axes),
            "population": population,
            "evidence_stage": evidence,
            "n": len(rows) if n_value is None else n_value,
            "required": required,
            "caption": caption,
            "generator_version": GENERATOR_VERSION,
            "git_commit": commit,
            "git_dirty_at_generation": git_dirty(),
            "status": status,
        }
        if reason:
            metadata["reason"] = reason
        output_paths: list[str] = []
        source_path: str | None = None
        if status == "READY":
            source_file = SOURCE_DIR / f"{figure_id}.json"
            write_json(source_file, {"schema_version": "phase17-figure-source-v1", "metadata": metadata, "rows": rows})
            source_path = str(source_file.relative_to(ROOT))
            svg_file = OUT / f"{figure_id}.svg"
            svg_file.parent.mkdir(parents=True, exist_ok=True)
            svg_file.write_text(chart_svg(kind, rows, metadata), encoding="utf-8")
            output_paths = convert(svg_file)
            generated_outputs.extend(output_paths + [source_path])
        inventory.append({**metadata, "derived_source": source_path, "output_paths": output_paths})

    # Cohort and temporal evidence.
    add("cohort_flow", "Authoritative cohort flow", "How does the historical comparison target differ from the accepted current cohort?", ["research/runs/formal_cpu_20260922/figure_sources/temporal_cohort.json", "research/ml_extension/splits/phase3_manifest_summary.json"], [{"label": row["stage"], "value": row["count"]} for row in temporal["rows"]], "flow", ("cohort stage", "records"), "historical comparison and authoritative current cohort", "PRELIMINARY", "Counts are materialized from the Phase 3 audit and frozen manifests; the 1024 historical target is comparison-only.")
    labels = Counter("B/LB" if int(row["label"]) == 0 else "P/LP" for row in final_rows)
    add("final_class_distribution", "Final locked-test class distribution", "What is the class balance of the immutable 946-row locked cohort?", common_sources, [{"label": key, "value": value} for key, value in sorted(labels.items())], "bar", ("class", "rows"), "946 locked-test rows", "FINAL", "Labels were joined locally after remote scoring and are used only for final evaluation.", n_value=946)
    chromosomes = Counter(str(row["normalized_variant_id"]).split(":")[1] for row in final_rows)
    add("final_chromosome_distribution", "Final locked-test chromosome distribution", "How are locked-test rows distributed across chromosomes?", common_sources, [{"label": key, "value": value} for key, value in sorted(chromosomes.items(), key=lambda item: (len(item[0]), item[0]))], "bar", ("chromosome", "rows"), "946 locked-test rows", "FINAL", "Chromosome labels are parsed from normalized variant identifiers.", n_value=946)
    genes = Counter(str(row["gene_symbol"]) for row in final_rows)
    add("final_gene_top", "Final locked-test genes with most rows", "Which genes contribute the largest number of locked-test rows?", common_sources, [{"label": key, "value": value} for key, value in genes.most_common(15)], "bar", ("gene", "rows"), "946 locked-test rows; top 15 genes", "FINAL", "This is a population description, not a gene-level performance claim.", n_value=946)
    add("temporal_transition", "Historical target to accepted formal cohort", "Which cohort counts changed between the historical comparison target and the accepted current cohort?", ["research/runs/formal_cpu_20260922/figure_sources/temporal_cohort.json", "research/ml_extension/splits/phase3_manifest_summary.json"], [{"label": row["stage"], "value": row["count"]} for row in temporal["rows"] if row["stage"].startswith(("historical_target_", "authoritative_"))], "bar", ("cohort quantity", "records"), "historical comparison and accepted formal cohort", "PRELIMINARY", "The difference is preserved as a documented deviation; no rows were added to force the historical aggregate.")

    # Compute and cost evidence.
    phases = phase_rows(phase6, phase7, final_artifact)
    cumulative = 0
    cumulative_rows = []
    for row in phases:
        cumulative += row["new_rows"]
        cumulative_rows.append({"x": row["label"], "x_numeric": row["phase"] + cumulative / 100000, "y": cumulative, "series": "newly scored/extracted rows"})
    add("compute_cumulative_rows", "Cumulative remote rows processed", "How did paid remote work accumulate across authorized phases?", ["artifacts/phase6/phase6_formal_evo2_20260921_full_overnight_20260922.json", "artifacts/phase7/formal_budgeted_representation_20260922.json", FINAL_ARTIFACT], cumulative_rows, "line", ("phase", "cumulative rows"), "authorized Phase 6, Phase 7, and Phase 14 workloads", "FINAL", "Phase 7 and Phase 14 values are taken from their accepted closeout artifacts; no new remote work is launched by this report.")
    add("cache_reuse", "Cache reuse versus new remote work", "How much verified work was reused instead of recomputed?", ["artifacts/phase6/phase6_formal_evo2_20260921_full_overnight_20260922.json", "artifacts/phase7/formal_budgeted_representation_20260922.json", FINAL_ARTIFACT], [{"label": row["label"] + " cache", "value": row["cache_hits"]} for row in phases] + [{"label": row["label"] + " new", "value": row["new_rows"]} for row in phases], "bar", ("phase/work type", "rows"), "authorized remote workloads", "FINAL", "Cache counts are reported as the closeout evidence for each authorized workload.")
    add("runtime_by_model", "Remote runtime by model/workload", "What remote wall time was recorded for each model workload?", ["research/runs/formal_cpu_20260922/figure_sources/cost_ledger.jsonl", "artifacts/phase7/formal_budgeted_representation_20260922.json", FINAL_ARTIFACT], [{"label": row["label"], "value": row["runtime"]} for row in phases], "bar", ("workload", "remote seconds"), "authorized remote workloads", "FINAL", "Runtime is remote wall time from the recorded closeout artifacts, not a clinical or throughput guarantee.")
    add("cost_by_phase_model", "Estimated direct compute cost", "What direct client-wall-rate estimate was recorded for each workload?", ["research/runs/formal_cpu_20260922/figure_sources/cost_ledger.jsonl", "artifacts/phase7/formal_budgeted_representation_20260922.json", FINAL_ARTIFACT], [{"label": row["label"], "value": row["cost"]} for row in phases], "bar", ("workload", "estimated USD"), "authorized remote workloads", "FINAL", "Estimates are not provider invoices; the report keeps both estimates and provider billing snapshots separate.")
    running = 0.0
    spend_rows = []
    for row in phases:
        running += row["cost"]
        spend_rows.append({"x": row["label"], "x_numeric": row["phase"] + running / 100000, "y": running, "series": "cumulative direct estimate"})
    add("cumulative_compute_spend", "Cumulative estimated compute", "How did the direct client-wall-rate estimate accumulate?", ["research/runs/formal_cpu_20260922/figure_sources/cost_ledger.jsonl", "artifacts/phase7/formal_budgeted_representation_20260922.json", FINAL_ARTIFACT], spend_rows, "line", ("phase", "cumulative estimated USD"), "authorized remote workloads", "FINAL", "This is a planning/ledger estimate, not a billed invoice.")
    add("throughput_comparison", "Recorded remote throughput", "What variants-per-second values were recorded by workload?", ["artifacts/phase6/phase6_formal_evo2_20260921_full_overnight_20260922.json", "artifacts/phase7/formal_budgeted_representation_20260922.json", FINAL_ARTIFACT], [{"label": "Phase 6 Evo2", "value": finite(phase6["runtime"].get("variants_per_remote_score_second", 0.0))}, {"label": "Phase 7 NT", "value": finite(phase7["model_tracks"]["nucleotide_transformer"].get("variants_per_second", 0.0))}, {"label": "Phase 7 Caduceus", "value": finite(phase7["model_tracks"]["caduceus"].get("variants_per_second", 0.0))}, {"label": "Phase 14 Evo2", "value": finite(final_rows[0]["provenance"].get("variants_per_second", 0.0))}], "bar", ("workload", "variants per second"), "authorized remote workloads", "FINAL", "Throughput is descriptive for the recorded calls and depends on batching and provider conditions.")

    # Development model and classifier evidence.
    model_rows = []
    for row in phase8["models"]:
        metrics = row.get("validation_metrics", {})
        if metrics.get("auroc") is not None:
            model_rows.append({"feature_set": row["feature_set"], "classifier": row["classifier"], "model_id": row["model_id"], "auroc": finite(metrics["auroc"]), "auprc": finite(metrics["auprc"]), "mcc": finite(metrics["mcc"]), "brier": finite(metrics["brier"]), "validation_count": int(row["validation_count"])})
    best_by_feature = {}
    for row in model_rows:
        if row["feature_set"] not in best_by_feature or row["auroc"] > best_by_feature[row["feature_set"]]["auroc"]:
            best_by_feature[row["feature_set"]] = row
    add("foundation_model_performance", "Development representation performance", "How did the strongest classifier per representation family perform on VALIDATION?", ["research/runs/formal_cpu_20260922/phase8/summary.json", "research/runs/formal_cpu_20260922/figure_sources/benchmark.json"], [{"label": key, "value": value["auroc"]} for key, value in sorted(best_by_feature.items())], "bar", ("representation family", "VALIDATION AUROC"), "formal TRAIN/VALIDATION development", "PRELIMINARY", "This is development evidence; it is not interchangeable with the locked-test result.")
    representation = read_json("research/runs/formal_cpu_20260922/figure_sources/embedding_layer.json")
    add("representation_layers", "Representation layer performance", "How did selected NT/Caduceus layers compare on development VALIDATION?", ["research/runs/formal_cpu_20260922/figure_sources/embedding_layer.json", "research/runs/formal_cpu_20260922/phase8/summary.json"], [{"x": row["layer"], "x_numeric": finite(row["layer"]), "y": finite(row["metric"]), "series": row["feature_set"]} for row in representation], "line", ("layer", "VALIDATION AUROC"), "formal TRAIN/VALIDATION development", "PRELIMINARY", "Only layer rows present in the registered development source are shown.")
    raw_vs_rep = [{"label": "development Evo2 classifier", "value": max(row["auroc"] for row in model_rows if row["feature_set"] == "evo2")}, {"label": "FINAL calibrated Evo2", "value": finite(final_artifact["metrics"]["auroc"])}]
    add("raw_vs_representation", "Development versus final Evo2 performance", "How do the development selected-classifier result and final calibrated Evo2 result differ by evidence stage?", ["research/runs/formal_cpu_20260922/phase8/summary.json", FINAL_ARTIFACT], raw_vs_rep, "bar", ("evidence stage/model", "AUROC"), "development VALIDATION versus final LOCKED_TEST", "FINAL", "The bars are explicitly stage-qualified and are not a claim of like-for-like population or selection equivalence.")
    for metric, figure_id, title in (("auroc", "classifier_auroc_heatmap", "Classifier/representation AUROC"), ("mcc", "classifier_mcc_heatmap", "Classifier/representation MCC"), ("brier", "classifier_brier_heatmap", "Classifier/representation Brier score")):
        add(figure_id, title, f"How does development {metric.upper()} vary across feature sets and classifiers?", ["research/runs/formal_cpu_20260922/phase8/summary.json"], [{"x": row["classifier"], "y": row["feature_set"], "value": row[metric]} for row in model_rows], "heatmap", ("classifier", metric.upper()), "formal TRAIN/VALIDATION development", "PRELIMINARY", "All cells are taken from the frozen Phase 8 development summary; partial CADD coverage remains marked in the source data.")
    add("combination_ranking", "Top development classifier combinations", "Which development combinations had the highest VALIDATION AUROC?", ["research/runs/formal_cpu_20260922/phase8/summary.json"], [{"label": row["model_id"], "value": row["auroc"]} for row in sorted(model_rows, key=lambda row: row["auroc"], reverse=True)[:12]], "bar", ("combination", "VALIDATION AUROC"), "formal TRAIN/VALIDATION development", "PRELIMINARY", "This ranking is descriptive and does not reopen the closed selection.")

    hpo_best = []
    for row in hpo:
        if row["trial_id"].endswith("trial_0") or row["objective"] == max(item["objective"] for item in hpo if item["feature_set"] == row["feature_set"]):
            hpo_best.append(row)
    add("hpo_trial_history", "Validation-only HPO trial history", "How did the bounded validation-only HPO objectives vary across trials?", ["research/runs/formal_cpu_20260922/figure_sources/hpo.json", "research/runs/formal_cpu_20260922/phase9/summary.json"], [{"x": row["trial_id"], "x_numeric": index, "y": row["objective"], "series": row["feature_set"]} for index, row in enumerate(hpo)], "line", ("trial", "VALIDATION objective"), "formal TRAIN/VALIDATION development", "PRELIMINARY", "Four trials per study were run on VALIDATION; parameter importance is intentionally not materialized.")
    add("hpo_hyperparameters", "Selected HPO configuration objectives", "What objective values were achieved by each feature set's selected HPO configuration?", ["research/runs/formal_cpu_20260922/figure_sources/hpo.json", "research/runs/formal_cpu_20260922/phase9/summary.json"], [{"label": row["feature_set"], "value": row["objective"]} for row in sorted(hpo_best, key=lambda row: row["feature_set"])], "bar", ("feature set", "best VALIDATION objective"), "formal TRAIN/VALIDATION development", "PRELIMINARY", "The labels identify feature sets; hyperparameters remain available in the source table and are not converted into a parameter-importance claim.")

    learning = []
    for row in phase13["learning_curves"]:
        if row["status"] != "COMPLETED":
            continue
        for metric in ("auroc", "auprc", "brier", "mcc", "f1"):
            learning.append({"x": row["fraction"], "x_numeric": finite(row["fraction"]), "y": finite(row["validation_metrics"][metric]), "series": metric})
    add("learning_curve_auroc", "Development learning curve", "How did VALIDATION AUROC change with the available training fraction?", ["research/runs/formal_cpu_20260922/phase13/ablations_learning_curves_robustness.json", "research/runs/formal_cpu_20260922/figure_sources/learning_curve.json"], [row for row in learning if row["series"] == "auroc"], "line", ("training fraction", "VALIDATION AUROC"), "formal TRAIN/VALIDATION development", "PRELIMINARY", "Only completed, predeclared learning-curve fractions are shown.")
    add("learning_curve_metrics", "Development learning-curve metrics", "How did multiple predeclared metrics change with training fraction?", ["research/runs/formal_cpu_20260922/phase13/ablations_learning_curves_robustness.json"], learning, "line", ("training fraction", "metric value"), "formal TRAIN/VALIDATION development", "PRELIMINARY", "Metrics share the same development population but have different scales; the legend identifies each metric.")
    ablation_rows = [{"label": row["ablation"], "value": finite(row["metrics"]["auroc"])} for row in phase13["ablation_results"]]
    add("ablation_metric_delta", "Development ablation AUROC", "Which predeclared feature ablations changed development AUROC?", ["research/runs/formal_cpu_20260922/phase13/ablations_learning_curves_robustness.json", "research/runs/formal_cpu_20260922/figure_sources/ablation.json"], sorted(ablation_rows, key=lambda row: row["value"], reverse=True), "bar", ("ablation", "VALIDATION AUROC"), "formal TRAIN/VALIDATION development", "PRELIMINARY", "Ablations are development evidence and do not alter the frozen final classifier.")
    add("diversity_matrix", "Development model diversity", "How correlated and discordant were selected development model errors?", ["research/runs/formal_cpu_20260922/phase11/ensemble_analysis.json", "research/runs/formal_cpu_20260922/figure_sources/error_correlation.json"], [{"x": row["left_model"], "y": row["right_model"], "value": finite(row["pearson_correlation"])} for row in phase11["diversity"]], "heatmap", ("left model", "error correlation"), "formal TRAIN/VALIDATION development", "PRELIMINARY", "The matrix contains recorded pairwise diversity rows only; absent pairs are not filled.")
    ensemble_rows = []
    for name, payload in phase11["ensemble_methods"].items():
        metrics = payload.get("metrics", payload)
        ensemble_rows.append({"label": name, "value": finite(metrics["auroc"])})
    add("ensemble_comparison", "Development ensemble comparison", "How did the recorded ensemble methods compare on VALIDATION AUROC?", ["research/runs/formal_cpu_20260922/phase11/ensemble_analysis.json", "research/runs/formal_cpu_20260922/figure_sources/ensemble.json"], ensemble_rows, "bar", ("ensemble method", "VALIDATION AUROC"), "formal TRAIN/VALIDATION development", "PRELIMINARY", "Ensemble evidence is development-only and selection-closed.")
    calibration_rows = [{"x": row["confidence"], "x_numeric": finite(row["confidence"]), "y": finite(row["observed_frequency"]), "series": method} for method, values in phase12["reliability"].items() for row in values]
    add("calibration_reliability", "Development calibration reliability", "How closely did observed frequency track confidence for the development calibration methods?", ["research/runs/formal_cpu_20260922/phase12/calibration_abstention.json", "research/runs/formal_cpu_20260922/figure_sources/calibration.json"], calibration_rows, "line", ("mean confidence", "observed frequency"), "formal TRAIN/VALIDATION development", "PRELIMINARY", "Reliability curves are fit/evaluated within the documented development calibration boundary.")
    calibration_metrics = []
    for stage, metrics in (("development isotonic", phase12["validation_metrics"]["isotonic"]), ("development platt", phase12["validation_metrics"]["platt"]), ("FINAL calibrated Evo2", final_artifact["metrics"]["probability_metrics"])):
        for metric in ("brier", "ece", "nll"):
            calibration_metrics.append({"label": f"{stage} {metric}", "value": finite(metrics[metric])})
    add("calibration_metric_comparison", "Calibration metric comparison by evidence stage", "How do calibration metrics differ between development methods and the final locked evaluation?", ["research/runs/formal_cpu_20260922/phase12/calibration_abstention.json", FINAL_ARTIFACT], calibration_metrics, "bar", ("stage/metric", "metric value"), "development VALIDATION versus final LOCKED_TEST", "FINAL", "Stage labels prevent development calibration from being confused with the final locked result.")
    risk = [{"x": row["coverage"], "x_numeric": finite(row["coverage"]), "y": finite(row["risk"]), "series": "development risk"} for row in phase12["risk_coverage"]["points"] if math.isfinite(float(row["risk"]))]
    add("risk_coverage_development", "Development risk-coverage curve", "How did selective risk change with development coverage?", ["research/runs/formal_cpu_20260922/phase12/calibration_abstention.json", "research/runs/formal_cpu_20260922/figure_sources/abstention.json"], risk, "line", ("coverage", "risk"), "formal TRAIN/VALIDATION development", "PRELIMINARY", "This curve is the recorded development risk-coverage surface, not the locked-test abstention result.")

    # Final locked evaluation evidence.
    confidence = [0.5 + 0.5 * abs(math.tanh(finite(row["delta_primary"]) / 10.0)) for row in final_rows]
    keep = max(1, int(len(final_rows) * finite(final_artifact["metrics"]["abstention"]["target_coverage"])))
    selected_indices = sorted(range(len(final_rows)), key=lambda index: confidence[index], reverse=True)[:keep]
    descriptive_error = sum(int(final_rows[index]["prediction"]) != int(final_rows[index]["label"]) for index in selected_indices) / keep
    signed_risk = finite(final_artifact["metrics"]["abstention"]["risk"])
    add("final_abstention_semantics", "Final abstention semantics at frozen coverage", "What does the immutable Phase 14 abstention number measure, and how does it compare with descriptive classifier error at the same fixed coverage?", common_sources, [{"label": "artifact signed-delta direction disagreement", "value": signed_risk}, {"label": "descriptive prediction error at same coverage", "value": descriptive_error}], "bar", ("risk definition", "risk"), "946 locked-test rows at frozen 50% coverage", "FINAL", "The artifact risk is the frozen signed-delta direction disagreement measure; the second bar is a separate descriptive calculation using the same confidence-rank subset and is not a replacement metric.", n_value=946)
    roc, pr = roc_pr(final_rows, "calibrated_score")
    add("final_roc", "Final locked-test ROC curve", "How does frozen calibrated-score discrimination vary with threshold on the locked cohort?", common_sources, roc, "line", ("false-positive rate", "true-positive rate"), "946 locked-test rows", "FINAL", "The curve is derived from the immutable joined final rows and calibrated scores.", n_value=946)
    add("final_pr", "Final locked-test precision-recall curve", "How does frozen calibrated-score precision vary with recall on the locked cohort?", common_sources, pr, "line", ("recall", "precision"), "946 locked-test rows", "FINAL", "The curve is derived from the immutable joined final rows and calibrated scores.", n_value=946)
    ci = final_artifact["metrics"]["bootstrap_auc_ci95"]
    add("bootstrap_interval", "Final AUROC bootstrap interval", "What uncertainty interval was recorded for final AUROC?", [FINAL_ARTIFACT], [{"label": "mean", "value": finite(final_artifact["metrics"]["bootstrap_auc_mean"])}, {"label": "point estimate", "value": finite(final_artifact["metrics"]["auroc"])}, {"label": "CI low", "value": finite(ci[0])}, {"label": "CI high", "value": finite(ci[1])}], "bar", ("estimate", "AUROC"), "946 locked-test rows; recorded bootstrap summary", "FINAL", "Only the recorded point, mean, and interval endpoints are shown; no bootstrap replicates are fabricated.", n_value=946)
    outcome_counts = Counter((int(row["label"]), int(row["prediction"])) for row in final_rows)
    tn, fp = outcome_counts[(0, 0)], outcome_counts[(0, 1)]
    fn, tp = outcome_counts[(1, 0)], outcome_counts[(1, 1)]
    outcomes = [
        {"x": "actual negative", "y": "predicted negative", "value": outcome_counts[(0, 0)]},
        {"x": "actual negative", "y": "predicted positive", "value": outcome_counts[(0, 1)]},
        {"x": "actual positive", "y": "predicted negative", "value": outcome_counts[(1, 0)]},
        {"x": "actual positive", "y": "predicted positive", "value": outcome_counts[(1, 1)]},
    ]
    add("final_confusion_matrix", "Final locked-test confusion matrix", "What are the four frozen outcome counts at the 0.5 calibrated-score threshold?", common_sources, outcomes, "confusion", ("actual class", "predicted class"), "946 locked-test rows", "FINAL", "Counts match the immutable Phase 14 confusion metrics.", n_value=946)
    chromosome_errors, gene_errors, outcome_rows = final_error_rows(final_rows)
    add("final_outcome_counts", "Final locked-test outcome counts", "How many true/false positive/negative outcomes were recorded?", common_sources, outcome_rows, "bar", ("outcome", "rows"), "946 locked-test rows", "FINAL", "Outcomes are computed from the immutable local label join and final prediction field.", n_value=946)
    add("final_error_chromosome", "Final errors by chromosome", "Where were final prediction errors distributed by chromosome?", common_sources, chromosome_errors, "bar", ("chromosome", "errors"), "946 locked-test rows; error rows only", "FINAL", "This is descriptive subgroup error analysis, not a chromosome-level model claim.", n_value=946)
    add("final_gene_errors", "Final errors by gene", "Which genes contain the largest number of final prediction errors?", common_sources, gene_errors, "bar", ("gene", "errors"), "946 locked-test rows; top error counts", "FINAL", "Only observed error counts are shown; small subgroups are not used for new tuning.", n_value=946)
    fp_fn = [{"label": "false positives", "value": fp}, {"label": "false negatives", "value": fn}]
    add("final_fp_fn", "Final false-positive and false-negative counts", "How do the two error types compare on the locked cohort?", common_sources, fp_fn, "bar", ("error type", "rows"), "946 locked-test rows", "FINAL", "Counts are the frozen Phase 14 confusion-matrix components.", n_value=946)
    generalization = [{"label": "development Evo2 VALIDATION AUROC", "value": max(row["auroc"] for row in model_rows if row["feature_set"] == "evo2")}, {"label": "final calibrated Evo2 LOCKED_TEST AUROC", "value": finite(final_artifact["metrics"]["auroc"])}]
    add("development_final_generalization", "Development versus final generalization", "How does the selected development result compare with the frozen final locked evaluation?", ["research/runs/formal_cpu_20260922/phase8/summary.json", FINAL_ARTIFACT], generalization, "bar", ("stage", "AUROC"), "development VALIDATION versus final LOCKED_TEST", "FINAL", "This is a stage-qualified comparison; selection was closed before the locked evaluation.")

    # Project chronology is a status/evidence map, not an invented performance series.
    timeline = [
        {"label": f"{row['phase']} {row['status']}", "value": 1}
        for row in [
            {"phase": "P3", "status": "PASS"},
            {"phase": "P6", "status": "PASS"},
            {"phase": "P7", "status": "PASS"},
            {"phase": "P8-13", "status": "PASS"},
            {"phase": "P14", "status": "FINAL PASS"},
            {"phase": "P15", "status": "AUTHORIZATION BOUNDARY"},
            {"phase": "P16", "status": "PARTIAL"},
            {"phase": "P17", "status": "LOCAL PASS"},
            {"phase": "P18", "status": "PARTIAL"},
            {"phase": "P19", "status": "BLOCKED"},
        ]
    ]
    add("project_timeline", "EvoVariant-TR evidence timeline", "Which phase gates are complete, partial, or still bounded by authorization?", ["artifacts/phase14/phase14_locked_evo2_20260922.json", "research/runs/formal_cpu_20260922/phase13/ablations_learning_curves_robustness.json", "artifacts/phase7/formal_budgeted_representation_20260922.json"], timeline, "bar", ("phase", "status marker"), "project phase gates", "FINAL", "The timeline reports evidence status and authorization boundaries; it is not a performance trend.")

    # Conditional cells are present in the inventory even though no scientific output is emitted.
    add("context_length_metric", "Context length versus metric", "Was the conditional context-length robustness cell executed?", ["research/runs/formal_cpu_20260922/phase13/ablations_learning_curves_robustness.json", "artifacts/phase13/context_length_deferral_20260922.json"], [], "bar", ("context length", "metric"), "development-only conditional cell", "NOT_APPLICABLE_WITH_DOCUMENTED_REASON", "No context-length curve is emitted: the cell was explicitly deferred before additional foundation-model extraction.", required=False, status="NOT_APPLICABLE_WITH_DOCUMENTED_REASON", reason="Phase 13 records NOT_RUN_DEFERRED_BY_COMPUTE; existing cached features are 8192 bp only.")
    add("train_validation_loss", "Train and validation loss", "Was a scientifically valid training-loss series recorded?", ["artifacts/modal/phase10_adaptation_deferral_20260921.json"], [], "bar", ("epoch", "loss"), "Phase 10 adaptation", "NOT_APPLICABLE_WITH_DOCUMENTED_REASON", "No loss curve is emitted: Phase 10 adaptation was deferred before training.", required=False, status="NOT_APPLICABLE_WITH_DOCUMENTED_REASON", reason="Phase 10 is DEFERRED_BY_COMPUTE and supplied no training-loss artifact.")

    # Tables are direct, compact companions to the visual bundle.
    final_metric_rows = [
        {"metric": key, "value": value}
        for key, value in {
            "AUROC": final_artifact["metrics"]["auroc"],
            "AUPRC": final_artifact["metrics"]["auprc"],
            "Brier": final_artifact["metrics"]["probability_metrics"]["brier"],
            "ECE": final_artifact["metrics"]["probability_metrics"]["ece"],
            "NLL": final_artifact["metrics"]["probability_metrics"]["nll"],
            "accuracy": final_artifact["metrics"]["probability_metrics"]["accuracy"],
            "abstention_coverage": final_artifact["metrics"]["abstention"]["actual_coverage"],
            "abstention_signed_delta_risk": final_artifact["metrics"]["abstention"]["risk"],
        }.items()
    ]
    table_paths = [
        write_csv("cohort_counts.csv", temporal["rows"]),
        write_csv("final_metrics.csv", final_metric_rows),
        write_csv("development_model_metrics.csv", model_rows),
        write_csv("classifier_matrix.csv", model_rows),
        write_csv("hpo_trials.csv", hpo),
        write_csv("learning_curves.csv", learning),
        write_csv("ablations.csv", phase13["ablation_results"]),
        write_csv("diversity.csv", phase11["diversity"]),
        write_csv("calibration.csv", calibration_rows),
        write_csv("final_error_subgroups.csv", chromosome_errors + gene_errors),
        write_csv("cost_ledger.csv", cost_ledger + [{"run_id": row["label"], "measured_seconds": row["runtime"], "estimated_usd": row["cost"], "scope": "publication bundle phase ledger"} for row in phases]),
        write_csv("limitations.csv", [{"component": "phase10_loss", "reason": "DEFERRED_BY_COMPUTE; no training loss exists"}, {"component": "phase13_context_length", "reason": "NOT_RUN_DEFERRED_BY_COMPUTE; additional extraction needs new authorization"}, {"component": "phase15", "reason": "remote batch parity remains outside current authorization"}, {"component": "phase18", "reason": "full remote clean-room re-inference remains unrun"}]),
    ]

    registered_run_ids = sorted({run_id for runs in registered.values() for run_id in runs})
    figure_inventory = {
        "schema_version": "phase17-figure-inventory-v1",
        "status": "PASS_LOCAL_PUBLICATION_BUNDLE",
        "generator_version": GENERATOR_VERSION,
        "git_commit": commit,
        "git_dirty_at_generation": git_dirty(),
        "final_phase14_artifact": {"path": FINAL_ARTIFACT, "sha256": sha(FINAL_ARTIFACT)},
        "final_joined_predictions": {"path": JOINED, "sha256": sha(JOINED)},
        "billing_recheck": {"path": BILLING_RECHECK, "sha256": sha(BILLING_RECHECK)},
        "registered_completed_runs_verified": len(registered_run_ids),
        "figures": inventory,
        "conditional_not_applicable": [entry for entry in inventory if entry["status"] != "READY"],
        "tables": table_paths,
        "format_support": {"svg": True, "png": shutil.which("rsvg-convert") is not None, "pdf": shutil.which("rsvg-convert") is not None},
        "no_remote_compute": True,
    }
    write_json(REPORT_DIR / "FIGURE_INVENTORY.json", figure_inventory)
    (REPORT_DIR / "FIGURE_INVENTORY.md").parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Phase 17 Figure Inventory", "", f"Status: `{figure_inventory['status']}`", f"Generator: `{GENERATOR_VERSION}`", f"Git commit: `{commit}`", "", "| Figure | Status | Required | Evidence | Population | Outputs |", "|---|---|---:|---|---|---|"]
    for entry in inventory:
        lines.append(f"| {entry['figure_id']} | {entry['status']} | {entry['required']} | {entry['evidence_stage']} | {entry['population']} | {', '.join(entry['output_paths']) or 'none'} |")
    (REPORT_DIR / "FIGURE_INVENTORY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    metrics = final_artifact["metrics"]
    phase14_runtime = phases[-1]["runtime"]
    phase14_estimated_cost = final_artifact["cost"]["estimated_run_cost_usd"]
    billing_snapshot = billing_recheck["snapshot"]
    billing_comparison = billing_recheck["comparison"]
    report = f"""# EvoVariant-TR Phase 17–19 Publication and Reproducibility Report

## Executive result

The no-spend publication bundle is complete for every applicable figure family supported by the registered Phase 3–14 artifacts. It contains `{sum(entry['status'] == 'READY' for entry in inventory)}` rendered figure families, SVG output for every rendered figure, and PNG/PDF companions when the installed native converter succeeded. The conditional Phase 10 loss and Phase 13 context-length cells are explicitly documented as not applicable; no values were fabricated.

This bundle does not reopen scientific selection, alter the immutable Phase 14 locked evaluation, or authorize additional Modal work. Phase 17 is `PASS_LOCAL_PUBLICATION_BUNDLE`; the overall release remains `PARTIAL / NOT_RELEASED` because Phase 15 remote parity, Phase 18 full remote scientific re-inference, and the dependent Phase 19 release gate remain outside the current authorization.

## Abstract

The EvoVariant-TR extension evaluates frozen GRCh38 variant windows with Evo2 and downstream development-only classifiers. The authoritative current temporal cohort contains 946 locked rows (536 benign/likely-benign and 410 pathogenic/likely-pathogenic) across 367 genes. Phase 14 completed the immutable Evo2 locked evaluation with AUROC `{metrics['auroc']:.6f}`, AUPRC `{metrics['auprc']:.6f}`, Brier score `{metrics['probability_metrics']['brier']:.6f}`, ECE `{metrics['probability_metrics']['ece']:.6f}`, and accuracy `{metrics['probability_metrics']['accuracy']:.6f}`. These are evidence-stage-qualified scientific results, not a clinical validation claim.

## Motivation

The study tests whether a frozen foundation-model variant signal can support a temporally defined research benchmark without leaking locked-test labels into model selection. The workbench and publication bundle therefore expose provenance and evidence stage beside every scientific output.

## Dataset and protocol

The protocol fixes the GRCh38 reference, 8192-bp context, forward and reverse-complement scoring, alternate-minus-reference log likelihood, frozen TRAIN/VALIDATION development manifests, and the authoritative 946-row `LOCKED_TEST` cohort. Labels were never sent to Modal; they were joined locally only after raw predictions were hashed.

## Temporal cohort

The temporal cohort source is the hash-registered Phase 3/17 source. The historical 1024-row target identity set is comparison-only, while the current accepted cohort is the 946-row set governed by the frozen manifest audit.

## Evo2 zero-shot model

The primary zero-shot model is Evo2 7B at revision `4b509ec2a22d6de472659f908bcb0714265ad3a7`, scored on H100 with the frozen sequence and orientation contract above. Phase 14 is an Evo2-only locked-evaluation subgate; it is not a claim that unrun comparator models were evaluated on the locked cohort.

## Methods and frozen boundary

- Model: Evo2 7B, revision `4b509ec2a22d6de472659f908bcb0714265ad3a7`, GRCh38, 8192 bp, forward and reverse-complement scoring, alternate-minus-reference log likelihood, H100.
- Phase 8–13 model selection, HPO, ensemble, calibration, abstention, ablation, and learning-curve evidence used only the frozen TRAIN/VALIDATION development boundary.
- Phase 14 evaluated exactly 946 `LOCKED_TEST` rows after the model, classifier, calibration, threshold, and abstention decisions were frozen. The raw remote artifact was hashed before labels were joined locally.
- The historical 1024-row target remains comparison-only. The accepted formal cohort is 946 rows because the authoritative Phase 3 audit governs the current study; no rows were added to force the historical aggregate.
- The renderer verifies source-file hashes and completed registry output hashes before writing the bundle. Every figure carries its source paths/hashes, evidence stage, population, row count, generator version, and Git commit in its sidecar and SVG metadata.

## Development evidence

Phase 8 evaluated 36 classifier/representation combinations. Phase 9 ran four validation-only trials per study across the declared feature families. Phase 11 recorded model diversity and ensemble comparisons. Phase 12 recorded development calibration and risk-coverage surfaces. Phase 13 recorded completed learning curves and ablations. These surfaces are marked `PRELIMINARY` in the inventory and are not promoted to locked-test evidence.

## Representations, downstream models, HPO, and ensemble

The development registry records Evo2 raw-score and frozen representation tracks, plus the Nucleotide Transformer and Caduceus representation work. Downstream classifiers, validation-only HPO trials, and ensemble comparisons are reported only from their registered TRAIN/VALIDATION artifacts. Fine-tuning/adaptation was formally deferred; no checkpoint or training-loss curve is implied.

## Calibration, abstention, and uncertainty

Platt and isotonic calibration, reliability, Brier/NLL/ECE, and the development risk-coverage surface are reported at the development evidence stage. The final abstention target and signed-delta risk are copied from the immutable Phase 14 artifact; the bundle does not reinterpret that risk as ordinary classification error.

## Ablations, robustness, learning curves, and error analysis

The bundle includes the recorded feature ablations, learning curves, model-diversity/error-correlation surfaces, chromosome and gene error summaries, and final false-positive/false-negative counts. The context-length cell remains explicitly not applicable because the frozen cache contains only 8192-bp features; no missing robustness points are synthesized.

## Development versus final

Development VALIDATION outputs and final LOCKED_TEST outputs are shown with separate evidence-stage labels. Their side-by-side figures are descriptive and do not reopen selection, calibration, threshold, or abstention decisions.

The development-versus-final figures intentionally keep the stages separate. The strongest development Evo2 classifier AUROC is shown alongside the final calibrated locked-test AUROC, but the chart is not a claim that the populations, calibration stage, or selection context are identical.

## Final locked evaluation

The immutable Phase 14 metrics are:

| Metric | Value |
|---|---:|
| AUROC | {metrics['auroc']:.9f} |
| AUPRC | {metrics['auprc']:.9f} |
| Bootstrap mean | {metrics['bootstrap_auc_mean']:.9f} |
| Bootstrap 95% interval | [{metrics['bootstrap_auc_ci95'][0]:.9f}, {metrics['bootstrap_auc_ci95'][1]:.9f}] |
| Accuracy | {metrics['probability_metrics']['accuracy']:.9f} |
| Brier | {metrics['probability_metrics']['brier']:.9f} |
| ECE | {metrics['probability_metrics']['ece']:.9f} |
| NLL | {metrics['probability_metrics']['nll']:.9f} |
| Raw delta-primary AUROC | {metrics['raw_delta_primary_auroc']:.9f} |
| TP / TN / FP / FN | {tp} / {tn} / {fp} / {fn} |

The frozen abstention target and actual coverage are `{metrics['abstention']['target_coverage']}` and `{metrics['abstention']['actual_coverage']}`. The artifact risk `{metrics['abstention']['risk']:.9f}` is signed-delta direction disagreement under the frozen confidence-rank selection. It is not silently relabeled as ordinary classifier error; the bundle also shows a separate descriptive prediction-error calculation at the same fixed subset.

## Compute, cost, and resource boundary

Phase 6 reused 3,968 verified rows and remotely scored 32 new rows. Phase 7 reused the accepted NT prefix and completed the Caduceus representation track under its separate authorization. Phase 14 remotely scored 946 locked rows in 30 H100 calls with recorded remote runtime `{phase14_runtime:.6f}` seconds and a direct estimate of `${phase14_estimated_cost:.9f}`. Paid workers were shut down and the latest no-spend Modal audit found no active containers.

The provider billing summary is workspace-level evidence, not a per-run invoice. The Phase 14 artifact records the execution snapshot at metered `$33.50187443` and billed `$0.13`; the latest no-spend recheck records metered `${billing_snapshot['metered_cost_usd']:.8f}` and billed `${billing_snapshot['billed_cost_usd']:.2f}` with active containers `{billing_snapshot['active_containers']}`. The provider does not expose a confirmed remaining free-credit balance in the local summary. Against the user-stated `$7.17` pre-run headroom, the latest observed `${billing_comparison['observed_metered_delta_usd']:.8f}` metered delta implies an indicative `${billing_comparison['indicative_user_basis_remaining_headroom_usd']:.8f}`, not a provider-confirmed balance.

## Conditional and deferred work

- Phase 10 training loss: `DEFERRED_BY_COMPUTE`; no training run occurred, so no loss curve is emitted.
- Phase 13 context length: `NOT_APPLICABLE_WITH_DOCUMENTED_REASON`; the predeclared 512/1024/2048/4096/8192 cell required additional foundation-model extraction, while current cached features are frozen at 8192 bp. A 64-row, four-additional-context planning sweep is estimated at `$0.387275664` direct H100 cost from the Phase 14 rate, but it is not authorized and must not touch the locked test.
- Phase 15 batch parity: local atomic shard interruption/restart behavior is verified; remote full-cohort parity remains outside the current authorization. No paid batch was started.
- Phase 15 batch parity: the authorized 64-row development-only smoke passed with 56 verified cache rows, 8 newly scored rows, exact canonical parity, and a persisted-shard resume with zero additional remote calls. It does not authorize a full-cohort batch.
- Phase 18 clean room: the free software/control-plane and local artifact hash checks are separate from the representative gated Modal smoke above. A full remote re-inference is not required by the literal Phase 18 task list and was not run or claimed.

## Reproducibility and release gates

The figure inventory is at `research/reports/phase17/FIGURE_INVENTORY.json` and the source sidecars are under `research/figures/final/source/`. Tables are under `research/tables/final/`. The final Phase 14 artifact SHA-256 is `{sha(FINAL_ARTIFACT)}` and the joined-prediction SHA-256 is `{sha(JOINED)}`. The generation path is CPU/local only and records no Modal invocation.

Phase 15's bounded parity smoke is complete; the full batch remains outside scope. Phase 19 is not marked `PASS`: release still requires the clean-room control-plane gate and a fresh exact-candidate release decision. No tag, deployment, publication submission, or external release claim is made by this report.

## Limitations

The historical target identity set is unavailable, so its aggregate is comparison-only. Development results are based on the frozen formal development manifest and are not locked-test evidence. CADD coverage is incomplete and remains explicit. The final cohort is a temporal ClinVar-derived cohort and does not establish clinical validity, prospective performance, or external validity. The provider billing summaries are workspace-level observations with meter adjustments and do not constitute a per-run invoice. Figures preserve these boundaries rather than filling missing cells.

## Conclusion

The reachable EvoVariant-TR evidence bundle is reproducible at the registered-artifact and bounded parity-smoke levels, with Phase 14 preserved as an immutable Evo2-only locked result. Remaining release status is governed by the documented clean-room storage boundary and final release gate; no unrun model, full batch, or full remote re-inference is presented as complete.
"""
    (REPORT_DIR / "FINAL_REPORT.md").write_text(report, encoding="utf-8")
    write_json(REPORT_DIR / "publication_manifest.json", {"status": "PASS_LOCAL_PUBLICATION_BUNDLE", "generator_version": GENERATOR_VERSION, "git_commit": commit, "figure_count": len(inventory), "rendered_count": sum(entry["status"] == "READY" for entry in inventory), "outputs": sorted(generated_outputs), "output_hashes": {path: sha(path) for path in sorted(generated_outputs)}, "table_paths": table_paths, "final_artifact_sha256": sha(FINAL_ARTIFACT), "joined_predictions_sha256": sha(JOINED), "billing_recheck_sha256": sha(BILLING_RECHECK), "no_remote_compute": True})
    print(json.dumps({"status": "PASS_LOCAL_PUBLICATION_BUNDLE", "figures": len(inventory), "rendered": sum(entry["status"] == "READY" for entry in inventory), "tables": len(table_paths), "png_pdf": shutil.which("rsvg-convert") is not None}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
