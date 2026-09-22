#!/usr/bin/env python
"""Fit TRAIN-OOF calibration/abstention and gene-aware uncertainty summaries."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path

from evovariant_tr.adaptation.calibration import (
    apply_calibrator,
    fit_calibrators,
    select_abstention_threshold,
    selective_metrics,
)
from evovariant_tr.adaptation.data import (
    EXPECTED_MANIFEST_SHA256,
    load_train_rows,
    verify_formal_data,
)
from evovariant_tr.adaptation.metrics import binary_metrics
from evovariant_tr.adaptation.state import record_stage
from evovariant_tr.adaptation.statistics import (
    gene_bootstrap_metrics,
    holm_adjust,
    paired_gene_bootstrap,
)

PROTOCOL_HASH = "07c93b4657e84a4ddfbdc2df1af0f467f80959e0534a67840b4bf2b2b04a2c2c"


def _read(path: Path) -> tuple[list[str], list[int], list[float], list[str]]:
    identifiers, labels, probabilities, genes = [], [], [], []
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            identifiers.append(row["normalized_variant_id"])
            labels.append(int(row["label"]))
            probability = float(row["probability"])
            if not math.isfinite(probability) or not 0 <= probability <= 1:
                raise ValueError(f"invalid OOF probability for {row['normalized_variant_id']}")
            probabilities.append(probability)
            genes.append(row["gene_symbol"])
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("OOF predictions contain duplicate normalized variant IDs")
    return identifiers, labels, probabilities, genes


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", required=True, help="TRAIN OOF prediction CSV")
    parser.add_argument("--output", required=True)
    parser.add_argument("--root", default=".")
    parser.add_argument("--state")
    args = parser.parse_args()
    identifiers, labels, probabilities, genes = _read(Path(args.predictions))
    rows = load_train_rows(args.root)
    expected = {
        row.normalized_variant_id: (row.label, row.gene_symbol) for row in rows
    }
    observed = dict(zip(identifiers, zip(labels, genes, strict=True), strict=True))
    if observed != expected:
        raise ValueError(
            "OOF predictions do not match exact TRAIN identities, labels, and genes"
        )
    epsilon = 1e-7
    clipped = [min(1 - epsilon, max(epsilon, probability)) for probability in probabilities]
    logits = [math.log(probability / (1 - probability)) for probability in clipped]
    calibrators = fit_calibrators(labels, logits)
    calibrated = apply_calibrator(logits, calibrators)
    threshold = select_abstention_threshold(labels, calibrated)
    abstention = selective_metrics(labels, calibrated)
    before_bootstrap = gene_bootstrap_metrics(labels, probabilities, genes)
    after_bootstrap = gene_bootstrap_metrics(labels, calibrated, genes)
    paired = paired_gene_bootstrap(labels, probabilities, calibrated, genes)
    p_values = [float(paired[name]["two_sided_p"]) for name in paired]
    adjusted = holm_adjust(p_values)
    for name, p_value in zip(paired, adjusted, strict=True):
        paired[name]["holm_adjusted_p"] = p_value
    report = {
        "status": "PASS",
        "study_id": "POSTHOC-FOUNDATION-ADAPTATION-001",
        "fit_scope": "TRAIN_OOF_ONLY",
        "holdout_used_for_fit": False,
        "oof_rows": len(rows),
        "oof_train_manifest_sha256": EXPECTED_MANIFEST_SHA256["formal_train_manifest.json"],
        "oof_predictions_sha256": hashlib.sha256(Path(args.predictions).read_bytes()).hexdigest(),
        "calibrators": calibrators,
        "mcc_threshold_supplementary": threshold,
        "selective_metrics": abstention,
        "metrics_before": binary_metrics(labels, probabilities),
        "metrics_after": binary_metrics(labels, calibrated),
        "gene_bootstrap_before": before_bootstrap,
        "gene_bootstrap_after": after_bootstrap,
        "paired_gene_bootstrap_after_minus_before": paired,
        "protocol_sha256": PROTOCOL_HASH,
        "data": verify_formal_data(args.root),
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + ".tmp")
    temporary.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, output)
    if args.state:
        details = {"fit_scope": "TRAIN_OOF_ONLY", "holdout_used_for_fit": False}
        for stage in ("CALIBRATION_DONE", "ABSTENTION_DONE"):
            record_stage(
                args.state,
                project_root=args.root,
                stage=stage,
                artifacts=(output, Path(args.predictions)),
                details=details,
            )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
