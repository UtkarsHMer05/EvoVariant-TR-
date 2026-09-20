"""Registry-driven figure manifest tests.

These tests use only temporary metadata and output files. They must never
promote fixture values into the repository's scientific registry.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from evovariant_tr.evidence import EvidenceStage
from evovariant_tr.figure_artifacts import (
    build_registry_figure_manifest,
    write_figure_manifest,
)
from evovariant_tr.registry import Registry, RunStatus

PROTOCOL_HASH = "78799000023ca157b72836a0ec603abb20c93960b15fba09485bd0dffbbb1525"
SOURCE_NAMES = (
    "benchmark.json",
    "calibration.json",
    "abstention.json",
    "ensemble.json",
    "cost_ledger.jsonl",
)


def _registry(tmp_path: Path) -> Registry:
    return Registry(tmp_path / "experiments" / "registry", repo_root=tmp_path)


def test_empty_registry_manifest_is_blocked_and_stable(tmp_path: Path) -> None:
    registry = _registry(tmp_path)
    first = build_registry_figure_manifest(registry, repo_root=tmp_path)
    second = build_registry_figure_manifest(registry, repo_root=tmp_path)

    assert first == second
    assert first["status"] == "BLOCKED"
    assert first["eligible_completed_run_count"] == 0
    assert first["available_figures"] == []
    assert not first.get("metrics")

    output = write_figure_manifest(tmp_path / "figure_manifest.json", first)
    first_hash = hashlib.sha256(output.read_bytes()).hexdigest()
    output.unlink()
    write_figure_manifest(output, second)
    assert hashlib.sha256(output.read_bytes()).hexdigest() == first_hash


def test_manifest_uses_only_hash_verified_eligible_outputs(tmp_path: Path) -> None:
    registry = _registry(tmp_path)
    output_paths: list[str] = []
    for name in SOURCE_NAMES:
        path = tmp_path / "runs" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}\n", encoding="utf-8")
        output_paths.append(path.relative_to(tmp_path).as_posix())

    record = registry.register(
        title="temporary preliminary figure-input fixture",
        evidence_stage=EvidenceStage.PRELIMINARY,
        command="pytest tests/unit/test_figure_artifacts.py",
        protocol_hash=PROTOCOL_HASH,
    )
    registry.transition(
        record.run_id,
        RunStatus.COMPLETED,
        output_paths=output_paths,
        outputs_base_dir=tmp_path,
    )

    manifest = build_registry_figure_manifest(registry, repo_root=tmp_path)
    assert manifest["status"] == "READY"
    assert manifest["eligible_completed_run_count"] == 1
    assert {entry["figure_id"] for entry in manifest["available_figures"]} == {
        "model_auroc",
        "model_auprc",
        "calibration",
        "risk_coverage",
        "ensemble",
        "cost_latency",
    }
    assert all(entry["source_records"] for entry in manifest["required_figures"])


def test_tampered_registered_output_blocks_manifest(tmp_path: Path) -> None:
    registry = _registry(tmp_path)
    output = tmp_path / "runs" / "benchmark.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"model_id": "fixture"}) + "\n", encoding="utf-8")
    record = registry.register(
        title="tamper fixture",
        evidence_stage=EvidenceStage.PRELIMINARY,
        command="pytest tests/unit/test_figure_artifacts.py",
        protocol_hash=PROTOCOL_HASH,
    )
    relative = output.relative_to(tmp_path).as_posix()
    registry.transition(
        record.run_id,
        RunStatus.COMPLETED,
        output_paths=[relative],
        outputs_base_dir=tmp_path,
    )
    output.write_text("tampered\n", encoding="utf-8")

    manifest = build_registry_figure_manifest(registry, repo_root=tmp_path)
    assert manifest["status"] == "BLOCKED"
    assert manifest["eligible_completed_run_count"] == 0
    assert any("not reproducible" in blocker for blocker in manifest["blockers"])


def test_legacy_entry_point_cannot_emit_synthetic_curves(tmp_path: Path) -> None:
    from research.scripts.generate_figures import generate_figures

    outputs = generate_figures(tmp_path / "figures")
    assert set(outputs) == {"figure_manifest"}
    assert not (tmp_path / "figures" / "fig3_roc_curve.json").exists()
    manifest = json.loads(
        (tmp_path / "figures" / "figure_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["status"] == "BLOCKED"
    assert not manifest.get("metrics")
