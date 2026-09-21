"""No-spend tests for validation-only ensemble and uncertainty analysis."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from evovariant_tr.analysis_pipeline import (
    AnalysisPipelineError,
    analyze_validation_ensemble,
    load_prediction_rows,
    write_analysis_artifact,
)


def _predictions(path: Path, *, locked: bool = False) -> None:
    rows: list[dict[str, object]] = []
    for identity, label, left, right in (
        ("v1", 0, 0.1, 0.2),
        ("v2", 1, 0.9, 0.8),
        ("v3", 0, 0.2, 0.1),
        ("v4", 1, 0.8, 0.9),
    ):
        for model, score in (("left", left), ("right", right)):
            rows.append(
                {
                    "normalized_variant_id": identity,
                    "split": "VALIDATION",
                    "model_id": model,
                    "score": score,
                    "label": label,
                }
            )
    if locked:
        rows.append(
            {
                "normalized_variant_id": "locked",
                "split": "LOCKED_TEST",
                "model_id": "left",
                "score": 0.5,
                "label": 0,
            }
        )
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def test_validation_ensemble_reports_diversity_calibration_and_abstention(tmp_path: Path) -> None:
    path = tmp_path / "predictions.jsonl"
    _predictions(path)
    rows = load_prediction_rows(path)
    assert len(rows) == 8
    artifact = analyze_validation_ensemble(
        rows,
        left_model="left",
        right_model="right",
        weights=(0.25, 0.75),
    )
    assert artifact["status"] == "COMPLETED"
    assert artifact["locked_test_evaluated"] is False
    assert artifact["diversity"]["n_common"] == 4
    assert artifact["metrics"]["auroc"] == 1.0
    assert len(artifact["calibration"]["risk_coverage"]["points"]) > 0
    output = write_analysis_artifact(tmp_path / "analysis.json", artifact)
    assert output.is_file()
    with pytest.raises(AnalysisPipelineError, match="already exists"):
        write_analysis_artifact(output, artifact)


def test_analysis_loader_and_ensemble_guards(tmp_path: Path) -> None:
    path = tmp_path / "predictions.jsonl"
    _predictions(path, locked=True)
    with pytest.raises(AnalysisPipelineError, match="locked-test"):
        load_prediction_rows(path)

    malformed = tmp_path / "malformed.jsonl"
    malformed.write_text("not-json\n", encoding="utf-8")
    with pytest.raises(AnalysisPipelineError, match="valid JSON"):
        load_prediction_rows(malformed)
    empty = tmp_path / "empty.jsonl"
    empty.write_text("\n", encoding="utf-8")
    with pytest.raises(AnalysisPipelineError, match="empty"):
        load_prediction_rows(empty)

    rows_path = tmp_path / "valid.jsonl"
    _predictions(rows_path)
    rows = load_prediction_rows(rows_path)
    with pytest.raises(AnalysisPipelineError, match="weights"):
        analyze_validation_ensemble(rows, left_model="left", right_model="right", weights=(1.0,))
    with pytest.raises(AnalysisPipelineError, match="no common"):
        analyze_validation_ensemble(rows, left_model="left", right_model="missing")

    duplicate = tmp_path / "duplicate.jsonl"
    duplicate.write_text(
        rows_path.read_text() + rows_path.read_text().splitlines()[0] + "\n",
        encoding="utf-8",
    )
    with pytest.raises(AnalysisPipelineError, match="duplicate"):
        load_prediction_rows(duplicate)


def test_analysis_loader_rejects_bad_rows_and_missing_file(tmp_path: Path) -> None:
    missing = tmp_path / "missing.jsonl"
    with pytest.raises(AnalysisPipelineError, match="could not read"):
        load_prediction_rows(missing)
    cases = [
        {
            "normalized_variant_id": "v",
            "split": "OTHER",
            "model_id": "m",
            "score": 0.1,
            "label": 0,
        },
        {
            "normalized_variant_id": "v",
            "split": "VALIDATION",
            "model_id": "m",
            "score": float("nan"),
            "label": 0,
        },
        {
            "normalized_variant_id": "v",
            "split": "VALIDATION",
            "model_id": "m",
            "score": 0.1,
            "label": 2,
        },
        {"normalized_variant_id": "v", "split": "VALIDATION", "model_id": "m", "score": 0.1},
    ]
    messages = ("unsupported", "invalid identity", "invalid label", "missing required")
    for index, (case, message) in enumerate(zip(cases, messages, strict=True)):
        target = tmp_path / f"bad-{index}.jsonl"
        target.write_text(json.dumps(case) + "\n", encoding="utf-8")
        with pytest.raises(AnalysisPipelineError, match=message):
            load_prediction_rows(target)
