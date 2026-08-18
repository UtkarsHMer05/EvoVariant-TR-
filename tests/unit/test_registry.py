"""Immutable experiment registry tests (Milestone 14).

Acceptance validations:
- Validation 1: registry refuses FINAL when the git tree is dirty unless the
  caller explicitly registers a non-final stage instead.
- Validation 2: output hashes are recomputable.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from pydantic import ValidationError

from evovariant_tr.evidence import EvidenceStage
from evovariant_tr.registry import (
    RUN_ID_PATTERN,
    Registry,
    RegistryError,
    RunRecord,
    RunStatus,
    compute_output_hashes,
    generate_run_id,
    git_state,
    hash_file,
    validate_final_gate,
    verify_output_hashes,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "research" / "schemas" / "experiment_run.schema.json"
PROTOCOL_HASH = "78799000023ca157b72836a0ec603abb20c93960b15fba09485bd0dffbbb1525"


def make_git_repo(path: Path) -> Path:
    subprocess.run(["git", "init", "-q", "-b", "main", str(path)], check=True)
    subprocess.run(["git", "-C", str(path), "config", "user.email", "test@example.com"], check=True)
    subprocess.run(["git", "-C", str(path), "config", "user.name", "Test"], check=True)
    (path / "seed.txt").write_text("seed\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(path), "add", "."], check=True)
    subprocess.run(["git", "-C", str(path), "commit", "-q", "-m", "seed"], check=True)
    return path


@pytest.fixture()
def clean_repo(tmp_path: Path) -> Path:
    return make_git_repo(tmp_path / "repo")


@pytest.fixture()
def dirty_repo(clean_repo: Path) -> Path:
    (clean_repo / "seed.txt").write_text("modified\n", encoding="utf-8")
    return clean_repo


@pytest.fixture()
def registry(clean_repo: Path) -> Registry:
    return Registry(clean_repo / "experiments" / "registry", repo_root=clean_repo)


def register_kwargs(**overrides):
    base = dict(
        title="fake-scorer end-to-end smoke",
        evidence_stage=EvidenceStage.SYNTHETIC_TEST,
        command="python -m evovariant_tr.cli score --scorer fake",
        protocol_hash=PROTOCOL_HASH,
        seed=20260814,
    )
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# run_id generation
# ---------------------------------------------------------------------------


def test_run_id_format_and_uniqueness() -> None:
    ids = {generate_run_id() for _ in range(200)}
    assert len(ids) > 190  # random suffix makes collisions vanishingly rare
    for run_id in ids:
        assert RUN_ID_PATTERN.match(run_id)


def test_run_record_rejects_malformed_run_id() -> None:
    with pytest.raises(ValidationError):
        RunRecord(
            run_id="run_123",
            title="t",
            evidence_stage=EvidenceStage.SYNTHETIC_TEST,
            status=RunStatus.REGISTERED,
            protocol_hash=PROTOCOL_HASH,
            git_commit=None,
            git_dirty=False,
            data_manifests={},
            reference_checksum=None,
            model_identity=None,
            scorer_config={},
            comparator_versions={},
            seed=None,
            hardware={},
            command="cmd",
            created_at="2026-08-18T00:00:00+00:00",
            updated_at="2026-08-18T00:00:00+00:00",
            parent_run_id=None,
            output_paths=(),
            output_hashes={},
        )


# ---------------------------------------------------------------------------
# Registration, storage, JSON schema
# ---------------------------------------------------------------------------


def test_register_writes_record_and_event_log(registry: Registry) -> None:
    record = registry.register(**register_kwargs())
    assert record.status is RunStatus.REGISTERED
    stored = registry.runs_dir / f"{record.run_id}.json"
    assert stored.is_file()
    log_lines = registry.log_path.read_text(encoding="utf-8").strip().splitlines()
    assert json.loads(log_lines[-1])["event"] == "register"


def test_record_round_trips_through_disk(registry: Registry) -> None:
    record = registry.register(**register_kwargs())
    assert registry.load(record.run_id) == record


def test_record_conforms_to_json_schema(registry: Registry) -> None:
    import jsonschema

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    record = registry.register(**register_kwargs())
    jsonschema.validate(record.model_dump(mode="json"), schema)


def test_json_schema_rejects_invalid_stage() -> None:
    import jsonschema

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    bad = {"evidence_stage": "KINDA_FINAL"}
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)


def test_registry_is_append_only(registry: Registry) -> None:
    record = registry.register(**register_kwargs())
    with pytest.raises(RegistryError, match="append-only"):
        registry._append_record(record)


def test_load_unknown_run_raises(registry: Registry) -> None:
    with pytest.raises(RegistryError, match="unknown run_id"):
        registry.load("run_20260818T000000Z_deadbeef")


def test_record_rejects_unknown_fields_and_is_frozen(registry: Registry) -> None:
    record = registry.register(**register_kwargs())
    with pytest.raises(ValidationError):
        RunRecord.model_validate({**record.model_dump(), "surprise": 1})
    with pytest.raises(ValidationError):
        record.status = RunStatus.COMPLETED  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Validation 1: FINAL refused on dirty tree; non-final stage is the escape hatch
# ---------------------------------------------------------------------------


def test_final_refused_when_tree_dirty(dirty_repo: Path) -> None:
    registry = Registry(dirty_repo / "experiments" / "registry", repo_root=dirty_repo)
    commit, dirty = git_state(dirty_repo)
    assert commit is not None and dirty is True
    with pytest.raises(RegistryError, match="dirty"):
        registry.register(
            **register_kwargs(
                evidence_stage=EvidenceStage.FINAL,
                title="primary full run",
            )
        )
    assert registry.list_runs() == []


def test_final_allowed_when_tree_clean(registry: Registry, clean_repo: Path) -> None:
    record = registry.register(
        **register_kwargs(evidence_stage=EvidenceStage.FINAL, title="primary full run")
    )
    assert record.evidence_stage is EvidenceStage.FINAL
    assert record.git_dirty is False
    assert record.git_commit is not None


def test_final_refused_without_git_repository(tmp_path: Path) -> None:
    registry = Registry(tmp_path / "registry", repo_root=tmp_path / "no_git_here")
    with pytest.raises(RegistryError, match="git commit"):
        registry.register(
            **register_kwargs(evidence_stage=EvidenceStage.FINAL, title="primary full run")
        )


def test_dirty_tree_ok_for_non_final_stage(dirty_repo: Path) -> None:
    registry = Registry(dirty_repo / "experiments" / "registry", repo_root=dirty_repo)
    record = registry.register(
        **register_kwargs(evidence_stage=EvidenceStage.ENGINEERING_PILOT)
    )
    assert record.git_dirty is True
    assert record.status is RunStatus.REGISTERED


def test_validate_final_gate_directly() -> None:
    def make(stage: EvidenceStage, commit: str | None, dirty: bool) -> RunRecord:
        return RunRecord(
            run_id="run_20260818T000000Z_deadbeef",
            title="t",
            evidence_stage=stage,
            status=RunStatus.REGISTERED,
            protocol_hash=PROTOCOL_HASH,
            git_commit=commit,
            git_dirty=dirty,
            data_manifests={},
            reference_checksum=None,
            model_identity=None,
            scorer_config={},
            comparator_versions={},
            seed=None,
            hardware={},
            command="cmd",
            created_at="2026-08-18T00:00:00+00:00",
            updated_at="2026-08-18T00:00:00+00:00",
            parent_run_id=None,
            output_paths=(),
            output_hashes={},
        )

    validate_final_gate(make(EvidenceStage.FINAL, "a" * 40, False))  # ok
    validate_final_gate(make(EvidenceStage.PRELIMINARY, None, True))  # non-final: ok
    with pytest.raises(RegistryError):
        validate_final_gate(make(EvidenceStage.FINAL, "a" * 40, True))
    with pytest.raises(RegistryError):
        validate_final_gate(make(EvidenceStage.FINAL, None, False))


# ---------------------------------------------------------------------------
# Status transitions, terminal states, aborted/failed
# ---------------------------------------------------------------------------


def test_lifecycle_to_completed_with_output_hashes(
    registry: Registry, clean_repo: Path
) -> None:
    record = registry.register(**register_kwargs())
    running = registry.transition(record.run_id, RunStatus.RUNNING)
    assert running.status is RunStatus.RUNNING

    out_dir = clean_repo / "artifacts" / "synthetic"
    out_dir.mkdir(parents=True)
    output = out_dir / "metrics.json"
    output.write_text('{"auroc": 0.5}\n', encoding="utf-8")
    relative = output.relative_to(clean_repo)

    completed = registry.transition(
        record.run_id,
        RunStatus.COMPLETED,
        output_paths=[str(relative)],
        outputs_base_dir=clean_repo,
    )
    assert completed.status is RunStatus.COMPLETED
    assert completed.output_hashes == {relative.as_posix(): hash_file(output)}


def test_completed_requires_output_paths(registry: Registry) -> None:
    record = registry.register(**register_kwargs())
    with pytest.raises(RegistryError, match="output_paths"):
        registry.transition(record.run_id, RunStatus.COMPLETED)


def test_failed_and_aborted_are_terminal_with_reason(registry: Registry) -> None:
    first = registry.register(**register_kwargs(title="will fail"))
    failed = registry.transition(first.run_id, RunStatus.FAILED, reason="OOM on GPU node")
    assert failed.status is RunStatus.FAILED
    with pytest.raises(RegistryError, match="terminal"):
        registry.transition(first.run_id, RunStatus.RUNNING)

    second = registry.register(**register_kwargs(title="will abort"))
    aborted = registry.transition(second.run_id, RunStatus.ABORTED, reason="user abort")
    assert aborted.status is RunStatus.ABORTED
    with pytest.raises(RegistryError, match="terminal"):
        registry.transition(second.run_id, RunStatus.COMPLETED, output_paths=["x"])

    events = [
        json.loads(line)
        for line in registry.log_path.read_text(encoding="utf-8").strip().splitlines()
    ]
    reasons = [e.get("reason") for e in events if e.get("event") == "transition"]
    assert "OOM on GPU node" in reasons
    assert "user abort" in reasons


# ---------------------------------------------------------------------------
# Validation 2: output hashes are recomputable
# ---------------------------------------------------------------------------


def test_output_hashes_are_recomputable_and_tamper_evident(
    registry: Registry, clean_repo: Path
) -> None:
    record = registry.register(**register_kwargs())
    out_dir = clean_repo / "artifacts" / "synthetic"
    out_dir.mkdir(parents=True)
    output = out_dir / "scores.parquet.json"
    output.write_text("[]\n", encoding="utf-8")
    relative = str(output.relative_to(clean_repo))

    completed = registry.transition(
        record.run_id,
        RunStatus.COMPLETED,
        output_paths=[relative],
        outputs_base_dir=clean_repo,
    )
    verify_output_hashes(completed, clean_repo)  # recomputes cleanly

    output.write_text("tampered\n", encoding="utf-8")
    with pytest.raises(RegistryError, match="not reproducible"):
        verify_output_hashes(completed, clean_repo)


def test_compute_output_hashes_missing_file_raises(clean_repo: Path) -> None:
    with pytest.raises(RegistryError, match="missing"):
        compute_output_hashes(["does/not/exist.json"], clean_repo)


def test_hashes_without_paths_are_inconsistent() -> None:
    record = RunRecord(
        run_id="run_20260818T000000Z_deadbeef",
        title="t",
        evidence_stage=EvidenceStage.SYNTHETIC_TEST,
        status=RunStatus.COMPLETED,
        protocol_hash=PROTOCOL_HASH,
        git_commit=None,
        git_dirty=False,
        data_manifests={},
        reference_checksum=None,
        model_identity=None,
        scorer_config={},
        comparator_versions={},
        seed=None,
        hardware={},
        command="cmd",
        created_at="2026-08-18T00:00:00+00:00",
        updated_at="2026-08-18T00:00:00+00:00",
        parent_run_id=None,
        output_paths=(),
        output_hashes={"x.json": "a" * 64},
    )
    with pytest.raises(RegistryError, match="without output_paths"):
        verify_output_hashes(record, ".")


# ---------------------------------------------------------------------------
# Parent/child relationships for sharded jobs
# ---------------------------------------------------------------------------


def test_parent_child_relationships(registry: Registry) -> None:
    parent = registry.register(**register_kwargs(title="parent batch"))
    child_a = registry.register(**register_kwargs(title="shard 0", parent_run_id=parent.run_id))
    child_b = registry.register(**register_kwargs(title="shard 1", parent_run_id=parent.run_id))
    assert child_a.parent_run_id == parent.run_id
    children = registry.children(parent.run_id)
    assert {child.run_id for child in children} == {child_a.run_id, child_b.run_id}


def test_cannot_attach_child_to_terminal_parent(registry: Registry) -> None:
    parent = registry.register(**register_kwargs(title="parent batch"))
    registry.transition(parent.run_id, RunStatus.ABORTED, reason="cancel")
    with pytest.raises(RegistryError, match="terminal"):
        registry.register(**register_kwargs(title="late shard", parent_run_id=parent.run_id))


def test_unknown_parent_rejected(registry: Registry) -> None:
    with pytest.raises(RegistryError, match="unknown run_id"):
        registry.register(
            **register_kwargs(parent_run_id="run_20260818T000000Z_deadbeef")
        )


# ---------------------------------------------------------------------------
# Listing
# ---------------------------------------------------------------------------


def test_list_runs_sorted_and_complete(registry: Registry) -> None:
    assert registry.list_runs() == []
    a = registry.register(**register_kwargs(title="a"))
    b = registry.register(**register_kwargs(title="b"))
    listed = registry.list_runs()
    assert [record.run_id for record in listed] == sorted([a.run_id, b.run_id])
