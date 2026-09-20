"""Synthetic-only tests for the later-phase CPU contracts and gate guards."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from evovariant_tr.analysis_plans import (
    build_ablation_matrix,
    build_learning_curve_sizes,
    build_robustness_matrix,
    freeze_analysis_config,
    require_frozen_config,
)
from evovariant_tr.batch_pipeline import batch_progress, parse_variant_csv
from evovariant_tr.benchmark import (
    benchmark_status,
    build_zero_shot_plan,
    harmonize_score,
    validate_benchmark_rows,
)
from evovariant_tr.ensemble import (
    PredictionRow,
    compare_model_predictions,
    stack_feature_matrix,
    validate_oof_stack,
    weighted_mean,
)
from evovariant_tr.experiment_control import (
    ExecutionStatus,
    deferred_artifact,
    read_artifact,
    write_artifact,
)
from evovariant_tr.feature_store import (
    assemble_feature_matrix,
    make_feature_record,
    validate_feature_split_disjointness,
)
from evovariant_tr.figure_artifacts import (
    build_figure_manifest,
    require_artifact_fields,
)
from evovariant_tr.hpo import run_validation_only_study, write_study
from evovariant_tr.model_registry import RegisteredModel, load_model_registry
from evovariant_tr.supervised import (
    TrainingRow,
    fit_classifier,
    fit_decision_stump,
    fit_logistic_regression,
    fit_mlp,
    validate_training_rows,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MODELS = REPO_ROOT / "research/ml_extension/models"
SCHEMA = REPO_ROOT / "research/schemas/model_manifest.schema.json"


def _rows() -> tuple[list[TrainingRow], list[TrainingRow]]:
    train = [
        TrainingRow("v1", "TRAIN", 0, (0.0, 0.0), "GENE_A"),
        TrainingRow("v2", "TRAIN", 1, (1.0, 1.0), "GENE_B"),
    ]
    validation = [
        TrainingRow("v3", "VALIDATION", 0, (0.1, 0.0), "GENE_C"),
        TrainingRow("v4", "VALIDATION", 1, (0.9, 1.0), "GENE_D"),
    ]
    return train, validation


def test_status_artifact_rejects_metrics_until_completion(tmp_path: Path) -> None:
    artifact = deferred_artifact(
        phase=6,
        family="ZS",
        blockers=["model unavailable"],
        inputs={"split": "frozen"},
    )
    path = write_artifact(tmp_path / "status.json", artifact)
    loaded = read_artifact(path)
    assert loaded.status is ExecutionStatus.BLOCKED
    assert loaded.blockers == ("model unavailable",)
    with pytest.raises(ValueError, match="COMPLETED"):
        deferred_artifact(phase=6, family="ZS", blockers=[], status=ExecutionStatus.COMPLETED)
    with pytest.raises(ValueError, match="metrics"):
        type(artifact)(phase=6, family="ZS", status=ExecutionStatus.BLOCKED, metrics={"auc": 0.5})
    with pytest.raises(ValueError, match="non-empty"):
        type(artifact)(phase=6, family="", status=ExecutionStatus.BLOCKED)
    with pytest.raises(ValueError, match="non-negative"):
        type(artifact)(phase=-1, family="ZS", status=ExecutionStatus.BLOCKED)


def test_benchmark_plan_is_direction_safe_and_blocked_without_models() -> None:
    models = load_model_registry(MODELS, schema_path=SCHEMA)
    plan = build_zero_shot_plan(models, split_manifest_hash="a" * 64)
    assert plan.model_ids == ()
    assert plan.locked_test_allowed is False
    assert benchmark_status(models, split_manifest_hash="a" * 64).status is ExecutionStatus.BLOCKED
    assert harmonize_score(2.0, "higher_is_more_pathogenic") == 2.0
    assert harmonize_score(2.0, "higher_is_more_benign") == -2.0
    with pytest.raises(ValueError, match="declared"):
        harmonize_score(2.0, "unknown")
    with pytest.raises(ValueError, match="locked-test"):
        validate_benchmark_rows(
            [{"normalized_variant_id": "v", "split": "LOCKED_TEST"}],
            purpose="selection",
        )
    validate_benchmark_rows(
        [{"normalized_variant_id": "v", "split": "LOCKED_TEST"}],
        purpose="reporting",
    )


def test_benchmark_plan_handles_included_model_and_authorization() -> None:
    manifest = RegisteredModel(
        Path("fixture.json"),
        {
            "model_id": "fixture",
            "status": "INCLUDED",
            "provenance": {"verification_status": "VERIFIED"},
        },
    )
    unauthorised = build_zero_shot_plan((manifest,), split_manifest_hash="b" * 64)
    assert unauthorised.model_ids == ("fixture",)
    assert unauthorised.locked_test_allowed is False
    authorised = build_zero_shot_plan(
        (manifest,), split_manifest_hash="b" * 64, execution_authorized=True
    )
    assert authorised.locked_test_allowed is True


def test_feature_store_hashes_and_split_guards() -> None:
    train = make_feature_record(
        normalized_variant_id="GRCh38:1:1:A>T",
        model_id="fixture",
        layer="layer_1",
        split="TRAIN",
        values=[1.0, 2.0],
        gene_symbol="GENE_A",
    )
    validation = make_feature_record(
        normalized_variant_id="GRCh38:1:2:A>T",
        model_id="fixture",
        layer="layer_1",
        split="VALIDATION",
        values=[3.0, 4.0],
    )
    locked = make_feature_record(
        normalized_variant_id="GRCh38:1:3:A>T",
        model_id="fixture",
        layer="layer_1",
        split="LOCKED_TEST",
        values=[5.0, 6.0],
    )
    ids, matrix = assemble_feature_matrix([validation, train], split="TRAIN")
    assert ids == [train.normalized_variant_id]
    assert matrix == [[1.0, 2.0]]
    assert validate_feature_split_disjointness([train, validation, locked]) == {
        "normalized_id_overlap": 0
    }
    with pytest.raises(ValueError, match="locked-test"):
        assemble_feature_matrix([locked], split="LOCKED_TEST")
    with pytest.raises(ValueError, match="empty"):
        make_feature_record(
            normalized_variant_id="v",
            model_id="m",
            layer="l",
            split="TRAIN",
            values=[],
        )
    with pytest.raises(ValueError, match="finite"):
        make_feature_record(
            normalized_variant_id="v",
            model_id="m",
            layer="l",
            split="TRAIN",
            values=[float("nan")],
        )
    with pytest.raises(ValueError, match="unknown split"):
        make_feature_record(
            normalized_variant_id="v",
            model_id="m",
            layer="l",
            split="OTHER",
            values=[1.0],
        )
    duplicate = make_feature_record(
        normalized_variant_id=train.normalized_variant_id,
        model_id="fixture",
        layer="layer_1",
        split="TRAIN",
        values=[1.0, 2.0],
    )
    with pytest.raises(ValueError, match="duplicate"):
        assemble_feature_matrix([train, duplicate], split="TRAIN")
    with pytest.raises(ValueError, match="inconsistent"):
        assemble_feature_matrix(
            [
                train,
                make_feature_record(
                    normalized_variant_id="v2",
                    model_id="fixture",
                    layer="l",
                    split="TRAIN",
                    values=[1.0],
                ),
            ],
            split="TRAIN",
        )


def test_supervised_classifiers_and_leakage_guards() -> None:
    train, validation = _rows()
    validate_training_rows(train, validation)
    logistic = fit_logistic_regression(train, steps=10)
    stump = fit_decision_stump(train)
    mlp = fit_mlp(train, hidden_width=2, epochs=3)
    assert 0.0 <= logistic.predict_proba([0.5, 0.5]) <= 1.0
    assert stump.predict_proba([1.0, 1.0]) in {0.0, 1.0}
    assert 0.0 <= mlp.predict_proba([0.5, 0.5]) <= 1.0
    assert fit_classifier("logistic_regression", train, steps=2).weights
    assert fit_classifier("decision_stump", train)
    assert fit_classifier("mlp", train, epochs=1)
    with pytest.raises(ValueError, match="unknown classifier"):
        fit_classifier("svm", train)
    locked = [TrainingRow("v5", "LOCKED_TEST", 1, (1.0, 1.0), "GENE_E")]
    with pytest.raises(ValueError, match="locked-test"):
        validate_training_rows(train, locked)
    with pytest.raises(ValueError, match="overlap"):
        validate_training_rows(train, [TrainingRow("v1", "VALIDATION", 0, (0.0, 0.0), "GENE_C")])
    with pytest.raises(ValueError, match="gene"):
        validate_training_rows(train, [TrainingRow("v5", "VALIDATION", 1, (1.0, 1.0), "GENE_A")])
    with pytest.raises(ValueError, match="both classes"):
        fit_logistic_regression([train[0]])
    with pytest.raises(ValueError, match="dimension"):
        logistic.predict_proba([1.0])
    with pytest.raises(ValueError, match="at least one"):
        fit_decision_stump([])


def test_hpo_is_bounded_and_validation_only(tmp_path: Path) -> None:
    study = run_validation_only_study(
        study_name="fixture",
        configs=[{"x": 1}, {"x": 2}],
        objective=lambda config: float(config["x"]),
    )
    assert study.best_trial.config == {"x": 2}
    path = write_study(tmp_path / "study.json", study)
    assert json.loads(path.read_text())["selection_split"] == "VALIDATION"
    with pytest.raises(ValueError, match="at least one"):
        run_validation_only_study(study_name="empty", configs=[], objective=lambda _: 0.0)
    with pytest.raises(ValueError, match="direction"):
        run_validation_only_study(
            study_name="bad", configs=[{}], objective=lambda _: 0.0, direction="sideways"
        )
    with pytest.raises(ValueError, match="validation-only"):
        run_validation_only_study(
            study_name="bad", configs=[{}], objective=lambda _: 0.0, selection_split="LOCKED_TEST"
        )
    with pytest.raises(ValueError, match="no completed"):
        empty_study = type(study)("empty", "maximize", 1, ())
        _ = empty_study.best_trial


def test_ensemble_oof_and_diversity_guards() -> None:
    rows = [
        PredictionRow("v1", "VALIDATION", "a", -1.0, 0),
        PredictionRow("v1", "VALIDATION", "b", 1.0, 0),
        PredictionRow("v2", "VALIDATION", "a", 1.0, 1),
        PredictionRow("v2", "VALIDATION", "b", 1.0, 1),
    ]
    summary = compare_model_predictions(rows, left_model="a", right_model="b")
    assert summary.n_common == 2
    assert summary.disagreement_rate == 0.5
    assert weighted_mean([1.0, 3.0], [1.0, 3.0]) == 2.5
    with pytest.raises(ValueError, match="same"):
        weighted_mean([1.0], [1.0, 2.0])
    with pytest.raises(ValueError, match="non-negative"):
        weighted_mean([1.0], [-1.0])
    oof = [
        PredictionRow("v1", "TRAIN", "a", -1.0, 0, True),
        PredictionRow("v1", "TRAIN", "b", -0.5, 0, True),
        PredictionRow("v2", "TRAIN", "a", 1.0, 1, True),
        PredictionRow("v2", "TRAIN", "b", 0.5, 1, True),
    ]
    ids, matrix, labels = stack_feature_matrix(oof)
    assert ids == ["v1", "v2"] and matrix == [[-1.0, -0.5], [1.0, 0.5]] and labels == [0, 1]
    with pytest.raises(ValueError, match="out-of-fold"):
        validate_oof_stack([PredictionRow("v", "TRAIN", "a", 0.0, 0, False)])
    with pytest.raises(ValueError, match="locked-test"):
        validate_oof_stack([PredictionRow("v", "LOCKED_TEST", "a", 0.0, 0, True)])
    with pytest.raises(ValueError, match="labels"):
        compare_model_predictions(
            [
                PredictionRow("v", "VALIDATION", "a", 0.0),
                PredictionRow("v", "VALIDATION", "b", 1.0),
            ],
            left_model="a",
            right_model="b",
        )


def test_analysis_plans_figures_and_batch_ingest(tmp_path: Path) -> None:
    frozen = freeze_analysis_config({"model": "fixture", "seed": 42})
    require_frozen_config(frozen, expected_sha256=frozen.sha256)
    with pytest.raises(ValueError, match="hash"):
        require_frozen_config(frozen, expected_sha256="0" * 64)
    assert len(build_ablation_matrix()) == 4
    assert len(build_robustness_matrix()) == 4
    assert build_learning_curve_sizes(10)[-1] == 10
    with pytest.raises(ValueError, match="positive"):
        build_learning_curve_sizes(0)

    specs = build_figure_manifest({"benchmark.json", "calibration.json", "abstention.json"})
    assert {spec["figure_id"] for spec in specs} == {
        "model_auroc",
        "model_auprc",
        "calibration",
        "risk_coverage",
    }
    require_artifact_fields({"model_id": "fixture", "auc_roc": 0.5}, ("model_id", "auc_roc"))
    with pytest.raises(ValueError, match="missing"):
        require_artifact_fields({}, ("auc_roc",))

    csv_path = tmp_path / "variants.csv"
    csv_path.write_text(
        "assembly,chromosome,position_1based,reference,alternate\nGRCh38,chr1,10,A,T\n",
        encoding="utf-8",
    )
    variants = parse_variant_csv(csv_path)
    assert variants[0].normalized_variant_id == "GRCh38:1:10:A>T"
    assert batch_progress(total=10, completed=3, failed=1)["remaining"] == 6
    with pytest.raises(ValueError, match="missing required"):
        bad = tmp_path / "bad.csv"
        bad.write_text("chromosome\n1\n", encoding="utf-8")
        parse_variant_csv(bad)
    with pytest.raises(ValueError, match="duplicate"):
        duplicate = tmp_path / "duplicate.csv"
        duplicate.write_text(
            "assembly,chromosome,position_1based,reference,alternate\n"
            "GRCh38,1,10,A,T\nGRCh38,chr1,10,A,T\n",
            encoding="utf-8",
        )
        parse_variant_csv(duplicate)
    with pytest.raises(ValueError, match="invalid batch progress"):
        batch_progress(total=1, completed=2, failed=0)
