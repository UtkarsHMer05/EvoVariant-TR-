"""No-spend tests for the one-shot locked-test evaluation contract."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from evovariant_tr.analysis_plans import freeze_analysis_config
from evovariant_tr.final_evaluation import (
    FinalEvaluationError,
    evaluate_locked_once,
    load_frozen_config,
)


def _locked_predictions(path: Path) -> None:
    rows = [
        {
            "normalized_variant_id": "v1",
            "split": "LOCKED_TEST",
            "model_id": "evo2",
            "score": -1.0,
            "label": 0,
        },
        {
            "normalized_variant_id": "v2",
            "split": "LOCKED_TEST",
            "model_id": "evo2",
            "score": 1.0,
            "label": 1,
        },
        {
            "normalized_variant_id": "v3",
            "split": "LOCKED_TEST",
            "model_id": "evo2",
            "score": -0.5,
            "label": 0,
        },
        {
            "normalized_variant_id": "v4",
            "split": "LOCKED_TEST",
            "model_id": "evo2",
            "score": 0.5,
            "label": 1,
        },
    ]
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def test_locked_evaluation_is_frozen_and_immutable(tmp_path: Path) -> None:
    predictions = tmp_path / "predictions.jsonl"
    _locked_predictions(predictions)
    config = {
        "selection_closed": True,
        "score_direction": "higher_is_more_pathogenic",
        "score_threshold": 0.0,
        "bootstrap_replicates": 20,
    }
    digest = freeze_analysis_config(config).sha256
    artifact = evaluate_locked_once(
        predictions,
        tmp_path / "final.json",
        model_id="evo2",
        frozen_config=config,
        expected_config_sha256=digest,
    )
    assert artifact["locked_test_evaluated"] is True
    assert artifact["metrics"]["auroc"] == 1.0
    assert artifact["metrics"]["bootstrap_replicates"] == 20
    with pytest.raises(FinalEvaluationError, match="already exists"):
        evaluate_locked_once(
            predictions,
            tmp_path / "final.json",
            model_id="evo2",
            frozen_config=config,
            expected_config_sha256=digest,
        )


def test_locked_evaluation_requires_closed_config_and_matching_hash(tmp_path: Path) -> None:
    predictions = tmp_path / "predictions.jsonl"
    _locked_predictions(predictions)
    config = {
        "selection_closed": False,
        "score_direction": "higher_is_more_pathogenic",
        "score_threshold": 0.0,
    }
    with pytest.raises(FinalEvaluationError, match="selection_closed"):
        evaluate_locked_once(
            predictions,
            tmp_path / "not-closed.json",
            model_id="evo2",
            frozen_config=config,
            expected_config_sha256=freeze_analysis_config(config).sha256,
        )
    closed = dict(config, selection_closed=True)
    with pytest.raises(FinalEvaluationError, match="hash"):
        evaluate_locked_once(
            predictions,
            tmp_path / "bad-hash.json",
            model_id="evo2",
            frozen_config=closed,
            expected_config_sha256="0" * 64,
        )


def test_locked_evaluation_rejects_wrong_split_and_bad_config(tmp_path: Path) -> None:
    predictions = tmp_path / "predictions.jsonl"
    predictions.write_text(
        json.dumps(
            {
                "normalized_variant_id": "v1",
                "split": "VALIDATION",
                "model_id": "evo2",
                "score": 0.1,
                "label": 0,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    config = {
        "selection_closed": True,
        "score_direction": "higher_is_more_pathogenic",
        "score_threshold": 0.0,
    }
    with pytest.raises(FinalEvaluationError, match="only LOCKED_TEST"):
        evaluate_locked_once(
            predictions,
            tmp_path / "wrong-split.json",
            model_id="evo2",
            frozen_config=config,
            expected_config_sha256=freeze_analysis_config(config).sha256,
        )
    invalid_config = tmp_path / "invalid-config.json"
    invalid_config.write_text("[]", encoding="utf-8")
    with pytest.raises(FinalEvaluationError, match="JSON object"):
        load_frozen_config(invalid_config)
    with pytest.raises(FinalEvaluationError, match="could not read"):
        load_frozen_config(tmp_path / "missing-config.json")


def test_locked_evaluation_rejects_invalid_config_and_prediction_artifact(
    tmp_path: Path,
) -> None:
    predictions = tmp_path / "predictions.jsonl"
    _locked_predictions(predictions)
    missing_direction = {
        "selection_closed": True,
        "score_threshold": 0.0,
    }
    with pytest.raises(FinalEvaluationError, match="score_direction"):
        evaluate_locked_once(
            predictions,
            tmp_path / "missing-direction.json",
            model_id="evo2",
            frozen_config=missing_direction,
            expected_config_sha256=freeze_analysis_config(missing_direction).sha256,
        )
    invalid_threshold = {
        "selection_closed": True,
        "score_direction": "higher_is_more_pathogenic",
        "score_threshold": "nan",
    }
    with pytest.raises(FinalEvaluationError, match="threshold"):
        evaluate_locked_once(
            predictions,
            tmp_path / "invalid-threshold.json",
            model_id="evo2",
            frozen_config=invalid_threshold,
            expected_config_sha256=freeze_analysis_config(invalid_threshold).sha256,
        )
    malformed = tmp_path / "malformed.jsonl"
    malformed.write_text("{not-json}\n", encoding="utf-8")
    config = {
        "selection_closed": True,
        "score_direction": "higher_is_more_pathogenic",
        "score_threshold": 0.0,
    }
    with pytest.raises(FinalEvaluationError, match="not valid JSON"):
        evaluate_locked_once(
            malformed,
            tmp_path / "malformed-output.json",
            model_id="evo2",
            frozen_config=config,
            expected_config_sha256=freeze_analysis_config(config).sha256,
        )


def test_locked_evaluation_requires_both_classes_and_loads_object_config(
    tmp_path: Path,
) -> None:
    predictions = tmp_path / "one-class.jsonl"
    rows = [
        {
            "normalized_variant_id": "v1",
            "split": "LOCKED_TEST",
            "model_id": "evo2",
            "score": -1.0,
            "label": 0,
        },
        {
            "normalized_variant_id": "v2",
            "split": "LOCKED_TEST",
            "model_id": "evo2",
            "score": -0.5,
            "label": 0,
        },
    ]
    predictions.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    config = {
        "selection_closed": True,
        "score_direction": "higher_is_more_pathogenic",
        "score_threshold": 0.0,
    }
    with pytest.raises(FinalEvaluationError, match="both classes"):
        evaluate_locked_once(
            predictions,
            tmp_path / "one-class-output.json",
            model_id="evo2",
            frozen_config=config,
            expected_config_sha256=freeze_analysis_config(config).sha256,
        )
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    assert load_frozen_config(config_path) == config
