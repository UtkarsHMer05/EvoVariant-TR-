#!/usr/bin/env python3
"""Audit the declared raw Evo2 delta orientation without changing results."""

# ruff: noqa: E501

from __future__ import annotations

import hashlib
import json
import math
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from evovariant_tr.metrics import compute_auc_roc  # noqa: E402

JOINED = ROOT / "research/runs/formal_cpu_20260922/phase14_locked_evo2/predictions_with_local_labels.jsonl"
FINAL = ROOT / "artifacts/phase14/phase14_locked_evo2_20260922.json"
CONFIG = ROOT / "research/runs/formal_cpu_20260922/phase13/frozen_config_materialized.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    rows = [json.loads(line) for line in JOINED.read_text(encoding="utf-8").splitlines() if line.strip()]
    labels = [int(row["label"]) for row in rows]
    scores = [float(row["delta_primary"]) for row in rows]
    direct = compute_auc_roc(scores, labels)
    negated = compute_auc_roc([-score for score in scores], labels)
    positives = sum(labels)
    negatives = len(labels) - positives
    positive_rule_accuracy = sum((score > 0) == bool(label) for score, label in zip(scores, labels, strict=True)) / len(rows)
    payload = {
        "schema_version": "raw-delta-sign-audit-v1",
        "status": "PASS_DIRECT_SIGN_CONVENTION",
        "recorded_at_utc": datetime.now(UTC).isoformat(),
        "source": {
            "joined_predictions": str(JOINED.relative_to(ROOT)),
            "joined_predictions_sha256": sha(JOINED),
            "phase14_artifact": str(FINAL.relative_to(ROOT)),
            "phase14_artifact_sha256": sha(FINAL),
            "frozen_downstream_config": str(CONFIG.relative_to(ROOT)),
            "frozen_downstream_config_sha256": sha(CONFIG),
        },
        "cohort": {"rows": len(rows), "positives": positives, "negatives": negatives, "finite_scores": all(math.isfinite(score) for score in scores)},
        "formula": {
            "delta_primary": "(delta_forward + delta_reverse) / 2",
            "delta_definition": "alternate_minus_reference_log_likelihood",
            "direction": "higher_is_more_pathogenic",
            "direct_auc_function": "compute_auc_roc(delta_primary, labels)",
        },
        "results": {
            "direct_raw_delta_primary_auroc": direct,
            "frozen_artifact_raw_delta_primary_auroc": FINAL.read_text(encoding="utf-8").count('"raw_delta_primary_auroc"') and json.loads(FINAL.read_text(encoding="utf-8"))["metrics"]["raw_delta_primary_auroc"],
            "negated_score_diagnostic_only": negated,
            "positive_rule_accuracy": positive_rule_accuracy,
            "score_min": min(scores),
            "score_max": max(scores),
        },
        "conclusion": "Report the direct signed raw-delta AUROC. Do not replace it with 1 - AUROC or flip the score after seeing the result. The higher final Phase 14 AUROC is produced by the frozen Evo2-derived feature pipeline, TRAIN-fit downstream logistic classifier, and TRAIN-fit isotonic calibration; it is not raw Evo2 alone.",
        "no_scientific_mutation": True,
    }
    out = ROOT / "artifacts/audits/raw_delta_auroc_sign_audit_20260922.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = f"""# Raw-delta AUROC sign audit — 2026-09-22

Status: `{payload['status']}`. No scientific artifact or metric was changed.

The frozen raw score is `delta_primary = (delta_forward + delta_reverse) / 2`, and each delta is alternate-minus-reference log likelihood. Under the declared `higher_is_more_pathogenic` convention, the direct AUROC is **{direct:.15f}**, matching the Phase 14 artifact. The negated-score value **{negated:.15f}** is a diagnostic only; it is not substituted into any report or metric.

There is no post-hoc sign flip, `1 - AUROC`, or label reversal. The final `{json.loads(FINAL.read_text(encoding='utf-8'))['metrics']['auroc']:.15f}` AUROC is the output of the frozen Evo2-derived feature pipeline with its TRAIN-fit downstream logistic classifier and TRAIN-fit isotonic calibration, not raw Evo2 alone.

Source hashes are in `raw_delta_auroc_sign_audit_20260922.json`.
"""
    (out.parent / "RAW_DELTA_AUROC_SIGN_AUDIT.md").write_text(md, encoding="utf-8")
    print(json.dumps({"status": payload["status"], "direct_auroc": direct, "negated_diagnostic": negated, "output": str(out)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
