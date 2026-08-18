"""Integration tests: registry + manifest + evidence guards on tiny fixtures.

Everything here runs against temp directories — no network, no GPU, no Modal.
"""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

import pytest

from evovariant_tr.evidence import EvidenceStage
from evovariant_tr.manifest import build_entry, build_manifest, write_manifest
from evovariant_tr.registry import Registry, RunStatus, verify_output_hashes

PROTOCOL_HASH = "78799000023ca157b72836a0ec603abb20c93960b15fba09485bd0dffbbb1525"


def make_git_repo(path: Path) -> Path:
    subprocess.run(["git", "init", "-q", "-b", "main", str(path)], check=True)
    subprocess.run(["git", "-C", str(path), "config", "user.email", "t@e.co"], check=True)
    subprocess.run(["git", "-C", str(path), "config", "user.name", "T"], check=True)
    (path / "seed.txt").write_text("seed\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(path), "add", "."], check=True)
    subprocess.run(["git", "-C", str(path), "commit", "-q", "-m", "seed"], check=True)
    return path


def test_registered_run_with_manifest_and_verified_outputs(tmp_path: Path) -> None:
    repo = make_git_repo(tmp_path / "repo")
    data_dir = repo / "data" / "raw"
    data_dir.mkdir(parents=True)
    asset = data_dir / "tiny_cohort.tsv"
    asset.write_text("id\tgene\n1\tBRCA1\n", encoding="utf-8")

    manifest = build_manifest(
        "tiny_cohort", data_dir, [build_entry("tiny_cohort.tsv", data_dir)]
    )
    manifest_path = write_manifest(manifest, repo / "data" / "manifests" / "tiny.json")
    manifest_hash = hashlib.sha256(manifest_path.read_bytes()).hexdigest()

    registry = Registry(repo / "experiments" / "registry", repo_root=repo)
    record = registry.register(
        title="integration smoke",
        evidence_stage=EvidenceStage.SYNTHETIC_TEST,
        command="pytest tests/integration",
        protocol_hash=PROTOCOL_HASH,
        data_manifests={"tiny_cohort": manifest_hash},
        seed=20260814,
    )

    out_dir = repo / "artifacts" / "synthetic"
    out_dir.mkdir(parents=True)
    output = out_dir / "result.json"
    output.write_text('{"ok": true}\n', encoding="utf-8")
    relative = str(output.relative_to(repo))

    completed = registry.transition(
        record.run_id,
        RunStatus.COMPLETED,
        output_paths=[relative],
        outputs_base_dir=repo,
    )
    verify_output_hashes(completed, repo)
    assert completed.evidence_stage is EvidenceStage.SYNTHETIC_TEST


def test_synthetic_output_blocked_from_final_results_path(tmp_path: Path) -> None:
    from evovariant_tr.evidence import FinalPathWriteError, ResultRecord, write_result_record

    record = ResultRecord(
        metric_name="auroc",
        value=0.5,
        evidence_stage=EvidenceStage.SYNTHETIC_TEST,
    )
    with pytest.raises(FinalPathWriteError):
        write_result_record(record, tmp_path / "artifacts" / "results" / "final" / "x.json")


def test_sharded_parent_child_run_completes(tmp_path: Path) -> None:
    repo = make_git_repo(tmp_path / "repo")
    registry = Registry(repo / "experiments" / "registry", repo_root=repo)
    parent = registry.register(
        title="parent",
        evidence_stage=EvidenceStage.ENGINEERING_PILOT,
        command="cmd",
        protocol_hash=PROTOCOL_HASH,
    )
    child = registry.register(
        title="shard 0",
        evidence_stage=EvidenceStage.ENGINEERING_PILOT,
        command="cmd --shard 0",
        protocol_hash=PROTOCOL_HASH,
        parent_run_id=parent.run_id,
    )
    assert [r.run_id for r in registry.children(parent.run_id)] == [child.run_id]
