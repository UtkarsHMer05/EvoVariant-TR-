#!/usr/bin/env python3
"""Fit train-only Platt/isotonic maps and evaluate them on VALIDATION."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from evovariant_tr.analysis_pipeline import load_prediction_rows
from evovariant_tr.prediction_calibration import (
    apply_isotonic,
    apply_platt,
    fit_isotonic,
    fit_platt,
    probability_metrics,
)


def _ensemble_rows(rows: list[Any], split: str) -> tuple[list[float], list[int]]:
    selected = [
        row for row in rows if row.split == split and row.model_id in {"logistic_regression", "mlp"}
    ]
    by_id: dict[str, dict[str, Any]] = {}
    for row in selected:
        by_id.setdefault(row.normalized_variant_id, {})[row.model_id] = row
    common = [
        by_id[identity]
        for identity in sorted(by_id)
        if set(by_id[identity]) == {"logistic_regression", "mlp"}
    ]
    if not common:
        raise ValueError(f"no aligned logistic/MLP rows for {split}")
    scores = [(item["logistic_regression"].score + item["mlp"].score) / 2.0 for item in common]
    labels = [item["logistic_regression"].label for item in common]
    return scores, labels


def _write_once(path: Path, payload: dict[str, Any]) -> None:
    if path.exists():
        raise ValueError(f"output already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = load_prediction_rows(args.predictions)
    train_scores, train_labels = _ensemble_rows(rows, "TRAIN")
    validation_scores, validation_labels = _ensemble_rows(rows, "VALIDATION")
    platt = fit_platt(train_scores, train_labels)
    isotonic = fit_isotonic(train_scores, train_labels)
    calibrated = {
        "uncalibrated": probability_metrics(validation_scores, validation_labels),
        "platt": probability_metrics(apply_platt(validation_scores, platt), validation_labels),
        "isotonic": probability_metrics(
            apply_isotonic(validation_scores, isotonic), validation_labels
        ),
    }
    artifact = {
        "phase": 12,
        "family": "CALIBRATION",
        "status": "COMPLETED",
        "selection_split": "TRAIN_CALIBRATION",
        "evaluation_split": "VALIDATION",
        "models": ["logistic_regression", "mlp"],
        "weights": [0.5, 0.5],
        "fit_count": len(train_scores),
        "evaluation_count": len(validation_scores),
        "locked_test_evaluated": False,
        "methods": {
            "platt": platt,
            "isotonic": isotonic,
        },
        "validation_metrics": calibrated,
        "selection_boundary": (
            "calibrators fit on TRAIN rows only; VALIDATION is evaluation-only; "
            "no locked-test rows loaded"
        ),
    }
    _write_once(args.output, artifact)
    print(json.dumps(artifact, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
