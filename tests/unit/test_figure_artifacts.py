"""Registry-driven figure, table, and export-bundle tests.

Fixture rows are temporary engineering data only. They must never be copied
into the repository's scientific registry or presented as study results.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

import evovariant_tr.figure_artifacts as figure_artifacts
from evovariant_tr.evidence import EvidenceStage
from evovariant_tr.figure_artifacts import (
    REQUIRED_FIGURES,
    REQUIRED_TABLES,
    _load_rows,
    _number,
    _output_path,
    _safe_repo_relative,
    _validate_rows,
    build_registry_figure_manifest,
    render_figure_bundle,
    render_preliminary_figure_bundle,
    write_figure_manifest,
)
from evovariant_tr.registry import Registry, RunStatus

PROTOCOL_HASH = "78799000023ca157b72836a0ec603abb20c93960b15fba09485bd0dffbbb1525"

SOURCE_ROWS: dict[str, list[dict[str, object]]] = {
    "ablation.json": [{"component": "fixture", "metric": 0.5}],
    "abstention.json": [{"coverage": 0.8, "risk": 0.1}],
    "benchmark.json": [
        {
            "model_id": "fixture",
            "auc_roc": 0.5,
            "auc_pr": 0.4,
            "auc_roc_ci_low": 0.4,
            "auc_roc_ci_high": 0.6,
            "auc_pr_ci_low": 0.3,
            "auc_pr_ci_high": 0.5,
        },
        {
            "model_id": "fixture-2",
            "auc_roc": 0.6,
            "auc_pr": 0.5,
            "auc_roc_ci_low": 0.5,
            "auc_roc_ci_high": 0.7,
            "auc_pr_ci_low": 0.4,
            "auc_pr_ci_high": 0.6,
        },
    ],
    "calibration.json": [
        {"confidence": 0.25, "observed_frequency": 0.2},
        {"confidence": 0.75, "observed_frequency": 0.8},
    ],
    "confusion_matrix.json": [{"model_id": "fixture", "tn": 1, "fp": 0, "fn": 0, "tp": 1}],
    "context_length.json": [{"context_length": 8192, "metric": 0.5}],
    "cost_ledger.jsonl": [{"run_id": "fixture", "measured_seconds": 1.0}],
    "dataset_flow.json": [{"stage": "included", "count": 2}],
    "embedding_layer.json": [{"layer": 1, "metric": 0.5}],
    "ensemble.json": [{"model_id": "fixture", "metric": 0.5}],
    "error_correlation.json": [{"model_id": "fixture", "error_correlation": 0.0}],
    "failures.json": [{"component": "fixture", "reason": "engineering fixture"}],
    "finetuning.json": [{"model_id": "fixture", "metric": 0.5}],
    "hpo.json": [{"trial_id": "trial-1", "objective": 0.5}],
    "hpo_importance.json": [{"parameter": "seed", "importance": 0.1}],
    "learning_curve.json": [{"train_size": 2, "metric": 0.5}],
    "loss.json": [{"epoch": 1, "train_loss": 0.5, "validation_loss": 0.6}],
    "model_registry.json": [{"model_id": "fixture", "status": "PLANNED"}],
    "pr.json": [{"model_id": "fixture", "recall": 0.5, "precision": 0.5}],
    "roc.json": [{"model_id": "fixture", "fpr": 0.1, "tpr": 0.5}],
    "split_composition.json": [{"split": "development", "count": 2}],
    "subgroup.json": [{"subgroup": "fixture", "metric": 0.5, "sample_count": 2}],
    "temporal_cohort.json": [{"stage": "included", "count": 2}],
    "trained_models.json": [{"model_id": "fixture", "metric": 0.5}],
}


def _registry(tmp_path: Path) -> Registry:
    return Registry(tmp_path / "experiments" / "registry", repo_root=tmp_path)


def _write_sources(tmp_path: Path, *, invalid_benchmark: bool = False) -> list[str]:
    output_paths: list[str] = []
    for name, rows in sorted(SOURCE_ROWS.items()):
        payload: object = rows
        if invalid_benchmark and name == "benchmark.json":
            payload = [{"model_id": "fixture", "auc_roc": 0.5}]
        path = tmp_path / "runs" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if name.endswith(".jsonl"):
            path.write_text(
                "".join(json.dumps(row, sort_keys=True) + "\n" for row in payload),
                encoding="utf-8",
            )
        else:
            path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
        output_paths.append(path.relative_to(tmp_path).as_posix())
    return output_paths


def _completed_fixture(
    tmp_path: Path,
    *,
    invalid_benchmark: bool = False,
    evidence_stage: EvidenceStage = EvidenceStage.PRELIMINARY,
) -> Registry:
    registry = _registry(tmp_path)
    output_paths = _write_sources(tmp_path, invalid_benchmark=invalid_benchmark)
    record = registry.register(
        title="temporary preliminary figure-input fixture",
        evidence_stage=evidence_stage,
        command="pytest tests/unit/test_figure_artifacts.py",
        protocol_hash=PROTOCOL_HASH,
        experiment_family="TEST_FIXTURE",
        model_name="fixture-only",
        model_source="test fixture",
        license_record={"status": "fixture"},
        gpu="CPU",
        estimated_cost_usd=0.0,
        notes="engineering fixture; not a scientific result",
    )
    registry.transition(
        record.run_id,
        RunStatus.COMPLETED,
        output_paths=output_paths,
        outputs_base_dir=tmp_path,
        runtime_seconds=1.0,
        measured_cost_usd=0.0,
    )
    return registry


def _relabel_fixture_as_final(registry: Registry) -> None:
    """Make a fixture record FINAL without exercising the registry final gate.

    Registry final-gate behavior is covered by registry tests. This helper
    isolates the figure-manifest contract while keeping the temporary fixture
    independent of a clean committed Git repository.
    """
    records = registry.list_runs()
    assert len(records) == 1
    record = records[0].model_copy(update={"evidence_stage": EvidenceStage.FINAL})
    registry._record_path(record.run_id).write_text(  # noqa: SLF001 - test fixture setup
        json.dumps(record.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def test_empty_registry_manifest_and_blocked_bundle_are_stable(tmp_path: Path) -> None:
    registry = _registry(tmp_path)
    first = build_registry_figure_manifest(registry, repo_root=tmp_path)
    second = build_registry_figure_manifest(registry, repo_root=tmp_path)

    assert first == second
    assert first["status"] == "BLOCKED"
    assert first["eligible_completed_run_count"] == 0
    assert first["eligible_final_run_count"] == 0
    assert first["available_figures"] == []
    assert first["available_tables"] == []
    assert not first.get("metrics")

    manifest_path = write_figure_manifest(tmp_path / "figure_manifest.json", first)
    first_hash = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    manifest_path.unlink()
    write_figure_manifest(manifest_path, second)
    assert hashlib.sha256(manifest_path.read_bytes()).hexdigest() == first_hash

    bundle_path = render_figure_bundle(
        first,
        repo_root=tmp_path,
        output_dir=tmp_path / "figures",
    )
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    assert bundle["status"] == "BLOCKED"
    assert bundle["outputs"] == []
    assert bundle["scientific_outputs_included"] is False
    assert "metrics" not in bundle
    bundle_hash = hashlib.sha256(bundle_path.read_bytes()).hexdigest()
    bundle_path.unlink()
    render_figure_bundle(first, repo_root=tmp_path, output_dir=tmp_path / "figures")
    assert hashlib.sha256(bundle_path.read_bytes()).hexdigest() == bundle_hash


def test_manifest_uses_all_hash_verified_eligible_outputs(tmp_path: Path) -> None:
    registry = _completed_fixture(tmp_path)
    manifest = build_registry_figure_manifest(registry, repo_root=tmp_path)

    assert manifest["status"] == "BLOCKED"
    assert manifest["eligible_completed_run_count"] == 1
    assert manifest["eligible_final_run_count"] == 0
    assert any("preliminary sources cannot produce" in blocker for blocker in manifest["blockers"])


def test_manifest_requires_a_completed_final_run_for_promotion(tmp_path: Path) -> None:
    registry = _completed_fixture(tmp_path)
    _relabel_fixture_as_final(registry)
    manifest = build_registry_figure_manifest(registry, repo_root=tmp_path)

    assert manifest["status"] == "READY"
    assert manifest["eligible_completed_run_count"] == 1
    assert manifest["eligible_final_run_count"] == 1
    assert {entry["figure_id"] for entry in manifest["available_figures"]} == {
        spec.figure_id for spec in REQUIRED_FIGURES
    }
    assert {entry["table_id"] for entry in manifest["available_tables"]} == {
        spec.table_id for spec in REQUIRED_TABLES
    }
    assert all(entry["source_records"] for entry in manifest["required_figures"])


def test_invalid_required_fields_block_manifest(tmp_path: Path) -> None:
    registry = _completed_fixture(tmp_path, invalid_benchmark=True)
    manifest = build_registry_figure_manifest(registry, repo_root=tmp_path)

    assert manifest["status"] == "BLOCKED"
    assert any(entry["figure_id"] == "model_auroc" for entry in manifest["available_figures"])
    assert any("invalid registered source artifact" in blocker for blocker in manifest["blockers"])


def test_ready_bundle_regenerates_identically_and_cleans_listed_outputs(tmp_path: Path) -> None:
    registry = _completed_fixture(tmp_path)
    _relabel_fixture_as_final(registry)
    manifest = build_registry_figure_manifest(registry, repo_root=tmp_path)
    output_dir = tmp_path / "figures"
    bundle_path = render_figure_bundle(manifest, repo_root=tmp_path, output_dir=output_dir)
    first = json.loads(bundle_path.read_text(encoding="utf-8"))
    assert first["status"] == "READY"
    assert first["scientific_outputs_included"] is True
    assert len(first["outputs"]) == len(REQUIRED_FIGURES) + len(REQUIRED_TABLES) + 4
    first_hash = hashlib.sha256(bundle_path.read_bytes()).hexdigest()

    for output in first["outputs"]:
        (output_dir / output["path"]).unlink()
    render_figure_bundle(manifest, repo_root=tmp_path, output_dir=output_dir)
    assert hashlib.sha256(bundle_path.read_bytes()).hexdigest() == first_hash
    assert (output_dir / "bundle" / "methods.md").is_file()
    assert (output_dir / "bundle" / "limitations.md").is_file()
    assert "metrics" not in json.loads(
        (output_dir / "bundle" / "model_provenance.json").read_text(encoding="utf-8")
    )


def test_deferred_finetuning_is_not_applicable_with_documented_reason(tmp_path: Path) -> None:
    registry = _completed_fixture(tmp_path)
    _relabel_fixture_as_final(registry)
    decision = tmp_path / "artifacts" / "modal" / "phase10_adaptation_deferral_20260921.json"
    decision.parent.mkdir(parents=True, exist_ok=True)
    decision.write_text(
        json.dumps({"status": "DEFERRED_BY_COMPUTE"}) + "\n",
        encoding="utf-8",
    )

    manifest = build_registry_figure_manifest(registry, repo_root=tmp_path)

    assert manifest["status"] == "READY"
    assert manifest["applicable_required_figure_count"] == len(REQUIRED_FIGURES) - 1
    assert manifest["applicable_required_table_count"] == len(REQUIRED_TABLES) - 1
    assert len(manifest["available_figures"]) == len(REQUIRED_FIGURES) - 1
    assert len(manifest["available_tables"]) == len(REQUIRED_TABLES) - 1
    assert manifest["not_applicable_figure_families"][0]["figure_id"] == "train_validation_loss"
    assert manifest["not_applicable_table_families"][0]["table_id"] == "fine_tuning_summary"
    assert "compute budget deferral" in manifest["not_applicable_table_families"][0]["reason"]

    bundle_path = render_figure_bundle(
        manifest,
        repo_root=tmp_path,
        output_dir=tmp_path / "figures",
    )
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    assert bundle["status"] == "READY"
    assert bundle["required_figure_count"] == len(REQUIRED_FIGURES) - 1
    assert bundle["not_applicable_table_families"][0]["phase"] == "10"


def test_conditional_policy_can_mark_figure_family_not_applicable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    registry = _completed_fixture(tmp_path)
    _relabel_fixture_as_final(registry)
    decision = tmp_path / "artifacts" / "modal" / "conditional-figure.json"
    decision.parent.mkdir(parents=True, exist_ok=True)
    decision.write_text(json.dumps({"status": "DEFERRED_TEST"}) + "\n", encoding="utf-8")
    policy = {
        "phase": "test",
        "status": "DEFERRED_TEST",
        "reason": "The fixture family is conditionally excluded for this contract test.",
        "decision_artifact": "artifacts/modal/conditional-figure.json",
    }
    monkeypatch.setitem(figure_artifacts.CONDITIONAL_SOURCE_POLICIES, "benchmark.json", policy)

    manifest = build_registry_figure_manifest(registry, repo_root=tmp_path)

    assert manifest["status"] == "READY"
    assert manifest["applicable_required_figure_count"] == len(REQUIRED_FIGURES) - 2
    assert manifest["applicable_required_table_count"] == len(REQUIRED_TABLES) - 1
    assert {entry["figure_id"] for entry in manifest["not_applicable_figure_families"]} == {
        "model_auroc",
        "model_auprc",
    }
    assert manifest["not_applicable_table_families"][0]["source_artifact"] == "benchmark.json"


def test_preliminary_bundle_exports_available_sources_without_promotion(tmp_path: Path) -> None:
    registry = _completed_fixture(tmp_path)
    manifest = build_registry_figure_manifest(registry, repo_root=tmp_path)
    partial = dict(manifest)
    partial["available_figures"] = manifest["available_figures"][:1]
    partial["available_tables"] = manifest["available_tables"][:1]
    partial["blockers"] = ["remaining source families are unavailable"]
    output_dir = tmp_path / "preliminary"

    output = render_preliminary_figure_bundle(
        partial,
        repo_root=tmp_path,
        output_dir=output_dir,
    )
    bundle = json.loads(output.read_text(encoding="utf-8"))
    assert bundle["status"] == "PARTIAL"
    assert bundle["evidence_stage"] == "PRELIMINARY"
    assert bundle["promotable"] is False
    assert bundle["scientific_outputs_included"] is True
    assert len(bundle["outputs"]) == 2

    empty = render_preliminary_figure_bundle(
        {"available_figures": [], "available_tables": [], "blockers": ["none"]},
        repo_root=tmp_path,
        output_dir=tmp_path / "empty-preliminary",
    )
    empty_bundle = json.loads(empty.read_text(encoding="utf-8"))
    assert empty_bundle["status"] == "BLOCKED"
    assert empty_bundle["outputs"] == []

    refused = render_preliminary_figure_bundle(
        {"available_figures": [{"figure_id": "unknown"}], "available_tables": []},
        repo_root=tmp_path,
        output_dir=tmp_path / "refused-preliminary",
    )
    refused_bundle = json.loads(refused.read_text(encoding="utf-8"))
    assert refused_bundle["status"] == "BLOCKED"
    assert "refused source manifest" in " ".join(refused_bundle["blockers"])


def test_tampered_registered_output_blocks_manifest(tmp_path: Path) -> None:
    registry = _completed_fixture(tmp_path)
    output = tmp_path / "runs" / "benchmark.json"
    output.write_text("tampered\n", encoding="utf-8")

    manifest = build_registry_figure_manifest(registry, repo_root=tmp_path)
    assert manifest["status"] in {"BLOCKED", "READY"}
    assert manifest["eligible_completed_run_count"] == 0
    assert manifest["eligible_final_run_count"] == 0
    assert any("not reproducible" in blocker for blocker in manifest["blockers"])


def test_ineligible_completed_stage_is_excluded(tmp_path: Path) -> None:
    registry = _completed_fixture(tmp_path)
    record = registry.register(
        title="synthetic figure-input fixture",
        evidence_stage=EvidenceStage.SYNTHETIC_TEST,
        command="pytest tests/unit/test_figure_artifacts.py",
        protocol_hash=PROTOCOL_HASH,
    )
    registry.transition(
        record.run_id,
        RunStatus.COMPLETED,
        output_paths=["runs/benchmark.json"],
        outputs_base_dir=tmp_path,
    )

    manifest = build_registry_figure_manifest(registry, repo_root=tmp_path)
    assert any(entry["run_id"] == record.run_id for entry in manifest["excluded_completed_runs"])


def test_renderer_rejects_source_path_traversal(tmp_path: Path) -> None:
    manifest = {
        "status": "READY",
        "required_figures": [],
        "required_tables": [],
        "available_figures": [
            {
                "figure_id": "model_auroc",
                "source_artifacts": ["benchmark.json"],
                "required_fields": ["model_id", "auc_roc"],
                "source_records": {
                    "benchmark.json": [
                        {"path": "../outside.json", "sha256": "0" * 64, "run_id": "fixture"}
                    ]
                },
            }
        ],
        "available_tables": [],
        "eligible_runs": [],
        "blockers": [],
    }
    output = render_figure_bundle(manifest, repo_root=tmp_path, output_dir=tmp_path / "figures")
    bundle = json.loads(output.read_text(encoding="utf-8"))
    assert bundle["status"] == "BLOCKED"
    assert bundle["outputs"] == []
    assert "renderer refused" in " ".join(bundle["blockers"])


def test_artifact_parser_and_path_guards_fail_closed(tmp_path: Path) -> None:
    jsonl = tmp_path / "rows.jsonl"
    jsonl.write_text('\n{"run_id":"fixture","measured_seconds":1}\n', encoding="utf-8")
    assert _load_rows(jsonl) == [{"run_id": "fixture", "measured_seconds": 1}]

    nested = tmp_path / "nested.json"
    nested.write_text('{"rows":[{"model_id":"fixture","auc_roc":0.5}]}', encoding="utf-8")
    assert _load_rows(nested)[0]["model_id"] == "fixture"

    for index, (content, message) in enumerate(
        (
            ("[]", "no rows"),
            ("[1]", "every artifact row"),
            ("1", "top-level artifact"),
            ("{", "not valid JSON"),
        )
    ):
        invalid = tmp_path / f"invalid-{index}.json"
        invalid.write_text(content, encoding="utf-8")
        try:
            _load_rows(invalid)
        except ValueError as exc:
            assert message in str(exc)
        else:
            raise AssertionError(f"expected parser failure for {content!r}")

    malformed_jsonl = tmp_path / "malformed.jsonl"
    malformed_jsonl.write_text("not-json\n", encoding="utf-8")
    try:
        _load_rows(malformed_jsonl)
    except ValueError as exc:
        assert "line 1" in str(exc)
    else:
        raise AssertionError("expected JSONL parser failure")

    assert _validate_rows([{"model_id": "fixture", "auc_roc": 0.5}], ("model_id", "auc_roc")) == []
    errors = _validate_rows(
        [{"model_id": "", "auc_roc": True}, {"model_id": "fixture", "auc_roc": float("nan")}],
        ("model_id", "auc_roc"),
    )
    assert len(errors) == 3
    for value in (True, float("nan")):
        try:
            _number(value)
        except Exception as exc:  # noqa: BLE001 - guard behavior is the assertion
            assert "finite numeric" in str(exc)
        else:
            raise AssertionError("expected numeric guard failure")
    for recorded in ("/outside.json", "../outside.json"):
        try:
            _safe_repo_relative(tmp_path, recorded)
        except Exception as exc:  # noqa: BLE001 - guard behavior is the assertion
            assert "repository root" in str(exc)
        else:
            raise AssertionError("expected repository path guard failure")
    try:
        _output_path(tmp_path, "../outside.json")
    except Exception as exc:  # noqa: BLE001 - guard behavior is the assertion
        assert "bundle directory" in str(exc)
    else:
        raise AssertionError("expected bundle path guard failure")


def test_legacy_entry_point_cannot_emit_synthetic_curves(tmp_path: Path) -> None:
    from research.scripts.generate_figures import generate_figures

    outputs = generate_figures(tmp_path / "figures")
    assert set(outputs) == {"figure_manifest"}
    assert not (tmp_path / "figures" / "fig3_roc_curve.json").exists()
    manifest = json.loads(
        (tmp_path / "figures" / "figure_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["status"] in {"BLOCKED", "READY"}
    assert not manifest.get("metrics")
