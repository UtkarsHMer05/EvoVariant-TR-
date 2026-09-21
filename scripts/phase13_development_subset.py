#!/usr/bin/env python3
"""Run the feasible, validation-only Phase 13 subset matrix on CPU."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from evovariant_tr.analysis_plans import (
    build_ablation_matrix,
    build_learning_curve_sizes,
    build_robustness_matrix,
)
from evovariant_tr.downstream_pipeline import (
    evaluate_classifier,
    load_training_feature_rows,
)
from evovariant_tr.supervised import TrainingRow, fit_logistic_regression

REPO_ROOT = Path(__file__).resolve().parents[1]
SEED = 42
FEATURE_INDEX = {
    "delta_primary": 0,
    "delta_forward": 1,
    "delta_reverse": 2,
    "orientation_disagreement": 3,
}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _subset(rows: list[TrainingRow], indices: tuple[int, ...]) -> list[TrainingRow]:
    return [
        TrainingRow(
            normalized_variant_id=row.normalized_variant_id,
            split=row.split,
            label=row.label,
            features=tuple(row.features[index] for index in indices),
            gene_symbol=row.gene_symbol,
        )
        for row in rows
    ]


def _fit_and_score(
    train: list[TrainingRow],
    validation: list[TrainingRow],
    indices: tuple[int, ...],
) -> dict[str, Any]:
    train_subset = _subset(train, indices)
    validation_subset = _subset(validation, indices)
    model = fit_logistic_regression(train_subset, seed=SEED)
    return {
        "status": "COMPLETED",
        "feature_names": [name for name, index in FEATURE_INDEX.items() if index in indices],
        "validation_metrics": evaluate_classifier(model, validation_subset),
    }


def _run_orientation_rows(
    train: list[TrainingRow],
    validation: list[TrainingRow],
) -> dict[str, dict[str, Any]]:
    return {
        "aggregate_primary": _fit_and_score(train, validation, (0,)),
        "forward_only": _fit_and_score(train, validation, (1,)),
        "reverse_only": _fit_and_score(train, validation, (2,)),
        "aggregate_with_orientation_auxiliary": _fit_and_score(
            train,
            validation,
            (0, 1, 2, 3),
        ),
    }


def _run_learning_curves(
    train: list[TrainingRow], validation: list[TrainingRow]
) -> list[dict[str, Any]]:
    ordered = sorted(train, key=lambda row: row.normalized_variant_id)
    curves: list[dict[str, Any]] = []
    for size in build_learning_curve_sizes(len(ordered)):
        subset = ordered[:size]
        if {row.label for row in subset} != {0, 1}:
            curves.append({"status": "NOT_RUN_SINGLE_CLASS", "train_count": size})
            continue
        model = fit_logistic_regression(subset, seed=SEED)
        curves.append(
            {
                "status": "COMPLETED",
                "train_count": size,
                "validation_metrics": evaluate_classifier(model, validation),
            }
        )
    return curves


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--features", type=Path, required=True)
    parser.add_argument("--phase8-summary", type=Path, required=True)
    parser.add_argument("--phase11-analysis", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        features_path = args.features.resolve()
        phase8_path = args.phase8_summary.resolve()
        phase11_path = args.phase11_analysis.resolve()
        output_path = args.output.resolve()
        if output_path.exists():
            raise ValueError("Phase 13 output already exists; use a new run directory")
        train, validation, metadata = load_training_feature_rows(features_path)
        phase8 = _read_json(phase8_path)
        phase11 = _read_json(phase11_path)
        if phase8.get("locked_test_evaluated") or phase11.get("locked_test_evaluated"):
            raise ValueError("upstream development artifacts report locked-test evaluation")

        orientation = _run_orientation_rows(train, validation)
        ablation: list[dict[str, Any]] = []
        for plan in build_ablation_matrix():
            component = plan["removed_component"]
            if component == "rc":
                result = orientation["forward_only"]
            elif component == "external_baseline":
                result = {"status": "NOT_APPLICABLE_NO_EXTERNAL_FEATURES"}
            elif component == "embedding_features":
                result = {"status": "NOT_APPLICABLE_NO_EMBEDDING_FEATURES"}
            else:
                result = {"status": "NOT_RUN_NO_CALIBRATOR_FIT"}
            ablation.append({**plan, **result})

        robustness: list[dict[str, Any]] = []
        for plan in build_robustness_matrix():
            if plan["robustness_id"] == "orientation_forward":
                result = orientation["forward_only"]
            elif plan["robustness_id"] == "orientation_reverse":
                result = orientation["reverse_only"]
            else:
                result = {"status": "NOT_RUN_REQUIRES_NEW_MODAL_CONTEXT_SCORES"}
            robustness.append({**plan, **result})

        member_metrics = phase8.get("models", {})
        member_removal = []
        for member in ("logistic_regression", "mlp", "decision_stump"):
            model = member_metrics.get(member)
            if isinstance(model, dict) and isinstance(model.get("validation_metrics"), dict):
                member_removal.append(
                    {
                        "removed_member": member,
                        "status": "COMPLETED_SINGLE_MEMBER_REFERENCE",
                        "validation_metrics": model["validation_metrics"],
                    }
                )
            else:
                member_removal.append(
                    {"removed_member": member, "status": "NOT_AVAILABLE_IN_PHASE8_SUMMARY"}
                )

        output = {
            "status": "PARTIAL_DEVELOPMENT_SUBSET",
            "phase": 13,
            "family": "ABLATION_ROBUSTNESS",
            "selection_split": "VALIDATION",
            "locked_test_evaluated": False,
            "full_development_cohort_complete": False,
            "seed": SEED,
            "inputs": {
                **metadata,
                "feature_artifact_sha256": _sha256_file(features_path),
                "phase8_summary": str(phase8_path.relative_to(REPO_ROOT)),
                "phase8_summary_sha256": _sha256_file(phase8_path),
                "phase11_analysis": str(phase11_path.relative_to(REPO_ROOT)),
                "phase11_analysis_sha256": _sha256_file(phase11_path),
            },
            "orientation_and_feature_variants": orientation,
            "predeclared_ablation_matrix": ablation,
            "predeclared_robustness_matrix": robustness,
            "ensemble_member_removal": member_removal,
            "learning_curves": _run_learning_curves(train, validation),
            "deferred": {
                "context_shift": "requires new paid context-shift sequence scoring",
                "embedding_feature_removal": (
                    "Phase 7 NT/Caduceus feature cache unavailable under current cap"
                ),
                "external_comparator_removal": "development CADD/PhyloP join not materialized",
                "calibration_effect": (
                    "no fitted calibrator; Phase 11/12 reports fixed ensemble "
                    "calibration diagnostics"
                ),
                "locked_test": "excluded by protocol and current approval",
            },
        }
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(output, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"status": output["status"], "output": str(output_path)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
