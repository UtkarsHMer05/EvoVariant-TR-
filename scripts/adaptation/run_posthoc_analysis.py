#!/usr/bin/env python
"""Fit TRAIN-OOF calibration/abstention and gene-aware uncertainty summaries."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from evovariant_tr.adaptation.calibration import (
    apply_temperature,
    fit_temperature,
    select_abstention_threshold,
)
from evovariant_tr.adaptation.data import verify_formal_data
from evovariant_tr.adaptation.metrics import binary_metrics
from evovariant_tr.adaptation.statistics import gene_bootstrap_auc

PROTOCOL_HASH = "07c93b4657e84a4ddfbdc2df1af0f467f80959e0534a67840b4bf2b2b04a2c2c"


def _read(path: Path):
    labels, probabilities, genes = [], [], []
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            labels.append(int(row["label"]))
            probability = float(row["probability"])
            probabilities.append(probability)
            genes.append(row["gene_symbol"])
    return labels, probabilities, genes


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", required=True, help="TRAIN OOF prediction CSV")
    parser.add_argument("--output", required=True)
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    labels, probabilities, genes = _read(Path(args.predictions))
    logits = [
        (0.0 if probability == 0.5 else __import__("math").log(probability / (1 - probability)))
        for probability in probabilities
    ]
    temperature = fit_temperature(labels, logits)
    calibrated = apply_temperature(logits, temperature)
    threshold = select_abstention_threshold(labels, calibrated)
    report = {
        "status": "PASS",
        "fit_scope": "TRAIN_OOF_ONLY",
        "holdout_used_for_fit": False,
        "temperature": temperature,
        "abstention": threshold,
        "metrics_before": binary_metrics(labels, probabilities),
        "metrics_after": binary_metrics(labels, calibrated, threshold=threshold["threshold"]),
        "bootstrap": gene_bootstrap_auc(labels, calibrated, genes),
        "protocol_sha256": PROTOCOL_HASH,
        "data": verify_formal_data(args.root),
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
