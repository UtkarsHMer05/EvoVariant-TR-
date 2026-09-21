"""No-spend tests for artifact-driven Phase 8/9 CPU execution."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from evovariant_tr.downstream_pipeline import (
    DownstreamPipelineError,
    evaluate_classifier,
    load_hpo_configs,
    load_training_feature_rows,
    run_baseline_training,
    run_logistic_hpo_from_features,
)
from evovariant_tr.feature_store import make_feature_record
from evovariant_tr.supervised import TrainingRow


def _write_features(path: Path, *, include_locked: bool = False) -> None:
    rows: list[dict[str, object]] = []
    values = [
        ("v1", "TRAIN", 0, [0.0, 0.1], "GENE_A"),
        ("v2", "TRAIN", 1, [1.0, 0.9], "GENE_B"),
        ("v3", "TRAIN", 0, [0.1, 0.0], "GENE_C"),
        ("v4", "TRAIN", 1, [0.9, 1.0], "GENE_D"),
        ("v5", "VALIDATION", 0, [0.2, 0.1], "GENE_E"),
        ("v6", "VALIDATION", 1, [0.8, 0.9], "GENE_F"),
        ("v7", "VALIDATION", 0, [0.1, 0.2], "GENE_G"),
        ("v8", "VALIDATION", 1, [0.9, 0.8], "GENE_H"),
    ]
    if include_locked:
        values.append(("v9", "LOCKED_TEST", 1, [1.0, 1.0], "GENE_I"))
    for identity, split, label, vector, gene in values:
        record = make_feature_record(
            normalized_variant_id=identity,
            model_id="evo2",
            layer="blocks.28.mlp.l3:orientation_concat_difference",
            split=split,
            values=vector,
            gene_symbol=gene,
        )
        row = record.to_dict()
        row["label"] = label
        rows.append(row)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def test_baseline_training_writes_validation_only_artifacts(tmp_path: Path) -> None:
    features = tmp_path / "features.jsonl"
    _write_features(features)

    train, validation, metadata = load_training_feature_rows(
        features,
        model_id="evo2",
        layer="blocks.28.mlp.l3:orientation_concat_difference",
    )
    assert len(train) == 4
    assert len(validation) == 4
    assert metadata["locked_test_evaluated"] is False

    summary = run_baseline_training(
        features,
        tmp_path / "training",
        model_id="evo2",
        layer="blocks.28.mlp.l3:orientation_concat_difference",
        mlp_epochs=3,
    )
    assert summary["status"] == "COMPLETED"
    assert summary["selection_split"] == "VALIDATION"
    assert summary["locked_test_evaluated"] is False
    assert set(summary["models"]) == {"decision_stump", "logistic_regression", "mlp"}
    predictions = (tmp_path / "training" / "development_predictions.jsonl").read_text()
    assert "LOCKED_TEST" not in predictions
    assert (tmp_path / "training" / "training_summary.json").is_file()

    with pytest.raises(DownstreamPipelineError, match="already contains"):
        run_baseline_training(features, tmp_path / "training", mlp_epochs=3)
    with pytest.raises(DownstreamPipelineError, match="positive"):
        run_baseline_training(features, tmp_path / "bad", mlp_epochs=0)


def test_validation_only_logistic_hpo_and_config_loader(tmp_path: Path) -> None:
    features = tmp_path / "features.jsonl"
    _write_features(features)
    configs = tmp_path / "configs.json"
    configs.write_text(
        json.dumps(
            [
                {"learning_rate": 0.05, "steps": 10, "l2": 0.0},
                {"learning_rate": 0.1, "steps": 20, "l2": 0.01},
            ]
        ),
        encoding="utf-8",
    )
    loaded = load_hpo_configs(configs)
    assert len(loaded) == 2
    study = run_logistic_hpo_from_features(
        features,
        tmp_path / "hpo",
        loaded,
        model_id="evo2",
        layer="blocks.28.mlp.l3:orientation_concat_difference",
    )
    assert study.best_trial.config in loaded
    hpo_payload = json.loads((tmp_path / "hpo" / "hpo.json").read_text())
    metadata_payload = json.loads((tmp_path / "hpo" / "hpo_metadata.json").read_text())
    assert hpo_payload["selection_split"] == "VALIDATION"
    assert metadata_payload["locked_test_evaluated"] is False
    with pytest.raises(DownstreamPipelineError, match="already exists"):
        run_logistic_hpo_from_features(features, tmp_path / "hpo", loaded)

    bad = tmp_path / "bad-configs.json"
    bad.write_text(json.dumps({"steps": 1}), encoding="utf-8")
    with pytest.raises(DownstreamPipelineError, match="non-empty"):
        load_hpo_configs(bad)
    missing = tmp_path / "missing-configs.json"
    with pytest.raises(DownstreamPipelineError, match="could not read"):
        load_hpo_configs(missing)

    invalid = tmp_path / "invalid-configs.json"
    invalid.write_text(json.dumps([{"unknown": 1}]), encoding="utf-8")
    with pytest.raises(DownstreamPipelineError, match="unsupported"):
        run_logistic_hpo_from_features(
            features,
            tmp_path / "invalid-hpo",
            load_hpo_configs(invalid),
        )


def test_feature_loader_fails_closed_for_integrity_and_split_violations(tmp_path: Path) -> None:
    features = tmp_path / "features.jsonl"
    _write_features(features)
    original = features.read_text()

    tampered = json.loads(original.splitlines()[0])
    tampered["values"][0] = 42.0
    features.write_text(json.dumps(tampered) + "\n", encoding="utf-8")
    with pytest.raises(DownstreamPipelineError, match="hash"):
        load_training_feature_rows(features)
    features.write_text(original, encoding="utf-8")

    locked = tmp_path / "locked.jsonl"
    _write_features(locked, include_locked=True)
    with pytest.raises(DownstreamPipelineError, match="locked-test"):
        load_training_feature_rows(locked)

    def rewrite(rows: list[dict[str, object]], name: str) -> Path:
        target = tmp_path / name
        target.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
        return target

    rows = [json.loads(line) for line in original.splitlines()]
    rows[0]["normalized_variant_id"] = rows[1]["normalized_variant_id"]
    with pytest.raises(DownstreamPipelineError, match="duplicate"):
        load_training_feature_rows(rewrite(rows, "duplicate.jsonl"))

    rows = [json.loads(line) for line in original.splitlines()]
    rows[0]["model_id"] = "other"
    with pytest.raises(DownstreamPipelineError, match="model mismatch"):
        load_training_feature_rows(rewrite(rows, "model-mismatch.jsonl"), model_id="evo2")

    rows = [json.loads(line) for line in original.splitlines()]
    rows[0]["layer"] = "other-layer"
    with pytest.raises(DownstreamPipelineError, match="layer mismatch"):
        load_training_feature_rows(
            rewrite(rows, "layer-mismatch.jsonl"),
            layer="blocks.28.mlp.l3:orientation_concat_difference",
        )

    rows = [json.loads(line) for line in original.splitlines()]
    rows[0]["gene_symbol"] = ""
    with pytest.raises(DownstreamPipelineError, match="empty identity"):
        load_training_feature_rows(rewrite(rows, "empty-gene.jsonl"))

    malformed = tmp_path / "malformed.jsonl"
    malformed.write_text("not-json\n", encoding="utf-8")
    with pytest.raises(DownstreamPipelineError, match="valid JSON"):
        load_training_feature_rows(malformed)
    non_object = tmp_path / "non-object.jsonl"
    non_object.write_text("[]\n", encoding="utf-8")
    with pytest.raises(DownstreamPipelineError, match="not an object"):
        load_training_feature_rows(non_object)
    with pytest.raises(DownstreamPipelineError, match="could not read"):
        load_training_feature_rows(tmp_path / "missing.jsonl")


def test_feature_loader_rejects_missing_rows_and_metric_contracts(tmp_path: Path) -> None:
    features = tmp_path / "features.jsonl"
    _write_features(features)
    rows = [json.loads(line) for line in features.read_text().splitlines()]

    train_only = tmp_path / "train-only.jsonl"
    train_only.write_text(
        "".join(json.dumps(row) + "\n" for row in rows[:4]),
        encoding="utf-8",
    )
    with pytest.raises(DownstreamPipelineError, match="both TRAIN"):
        load_training_feature_rows(train_only)

    unknown_split = dict(rows[0])
    unknown_split["split"] = "OTHER"
    unknown_path = tmp_path / "unknown.jsonl"
    unknown_path.write_text(
        "\n".join([json.dumps(unknown_split), *[json.dumps(row) for row in rows[4:]]]) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(DownstreamPipelineError, match="unsupported"):
        load_training_feature_rows(unknown_path)

    missing_field = dict(rows[0])
    missing_field.pop("label")
    missing_path = tmp_path / "missing-field.jsonl"
    missing_path.write_text(
        "\n".join([json.dumps(missing_field), *[json.dumps(row) for row in rows[1:]]]) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(DownstreamPipelineError, match="missing training metadata"):
        load_training_feature_rows(missing_path)

    mixed = [dict(row) for row in rows]
    mixed[-1]["model_id"] = "other"
    mixed_path = tmp_path / "mixed.jsonl"
    mixed_path.write_text("".join(json.dumps(row) + "\n" for row in mixed), encoding="utf-8")
    with pytest.raises(DownstreamPipelineError, match="mixes"):
        load_training_feature_rows(mixed_path)

    one_class = [dict(row) for row in rows]
    for row in one_class:
        row["label"] = 0
    one_class_path = tmp_path / "one-class.jsonl"
    one_class_path.write_text(
        "".join(json.dumps(row) + "\n" for row in one_class),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="both classes"):
        run_baseline_training(one_class_path, tmp_path / "one-class-output")

    class ConstantModel:
        def predict_proba(self, features: tuple[float, ...] | list[float]) -> float:
            return 2.0

    with pytest.raises(DownstreamPipelineError, match=r"in \[0, 1\]"):
        evaluate_classifier(ConstantModel(), [
            TrainingRow("v1", "VALIDATION", 0, (0.0,), "GENE_A"),
            TrainingRow("v2", "VALIDATION", 1, (1.0,), "GENE_B"),
        ])
