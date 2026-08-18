"""Immutable experiment registry for EvoVariant-TR.

Every scientific run must be identifiable and reproducible from metadata alone.
The registry stores one append-only JSON record per run under
``experiments/registry/runs/<run_id>.json`` plus an append-only event log at
``experiments/registry/log.jsonl``.

Guards (Milestone 14):
- a FINAL run is refused when the git tree is dirty unless the caller
  explicitly registers a non-final stage instead;
- output hashes are recomputable from the recorded output paths;
- run records are append-only: existing records are never silently rewritten;
- sharded jobs reference parents, and terminal states are final.
"""

from __future__ import annotations

import hashlib
import json
import re
import secrets
import subprocess
from collections.abc import Sequence
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator

from evovariant_tr.evidence import EvidenceStage

RUN_ID_PATTERN = re.compile(r"^run_[0-9]{8}T[0-9]{6}Z_[0-9a-f]{8}$")
_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")
_MAX_ID_ATTEMPTS = 64


class RegistryError(RuntimeError):
    """Raised for any registry policy violation."""


class RunStatus(StrEnum):
    REGISTERED = "REGISTERED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ABORTED = "ABORTED"


TERMINAL_STATUSES = frozenset(
    {RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.ABORTED}
)


def utc_now_iso(now: datetime | None = None) -> str:
    moment = now or datetime.now(UTC)
    return moment.astimezone(UTC).isoformat()


def generate_run_id(now: datetime | None = None) -> str:
    """Deterministic-prefix run id: ``run_<UTC stamp>_<8 hex chars>``."""
    stamp = (now or datetime.now(UTC)).strftime("%Y%m%dT%H%M%SZ")
    return f"run_{stamp}_{secrets.token_hex(4)}"


def git_state(repo_root: str | Path) -> tuple[str | None, bool]:
    """Return ``(commit_sha_or_None, dirty_flag)`` for a repository.

    A directory without a git repository yields ``(None, False)``; callers that
    need FINAL guarantees must require a real commit sha as well.
    """
    root = Path(repo_root)

    def run_git(*args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            text=True,
            check=False,
        )

    rev = run_git("rev-parse", "HEAD")
    if rev.returncode != 0:
        return None, False
    commit = rev.stdout.strip()
    status = run_git("status", "--porcelain")
    dirty = bool(status.stdout.strip())
    return commit, dirty


def hash_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def compute_output_hashes(paths: Sequence[str | Path], base_dir: str | Path) -> dict[str, str]:
    """Map each path (relative to ``base_dir``) to its SHA-256 hex digest."""
    base = Path(base_dir)
    hashes: dict[str, str] = {}
    for relative in sorted(str(path) for path in paths):
        target = base / relative
        if not target.is_file():
            raise RegistryError(f"output file missing for hashing: {target}")
        hashes[Path(relative).as_posix()] = hash_file(target)
    return hashes


class RunRecord(BaseModel):
    """One immutable, reproducible run record."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    run_id: str
    title: str
    evidence_stage: EvidenceStage
    status: RunStatus
    protocol_hash: str
    git_commit: str | None
    git_dirty: bool
    data_manifests: dict[str, str]
    reference_checksum: str | None
    model_identity: str | None
    scorer_config: dict[str, Any]
    comparator_versions: dict[str, str]
    seed: int | None
    hardware: dict[str, str]
    command: str
    created_at: str
    updated_at: str
    parent_run_id: str | None
    output_paths: tuple[str, ...]
    output_hashes: dict[str, str]

    @field_validator("run_id")
    @classmethod
    def _valid_run_id(cls, value: str) -> str:
        if not RUN_ID_PATTERN.match(value):
            raise ValueError(f"run_id must match {RUN_ID_PATTERN.pattern}, got {value!r}")
        return value

    @field_validator("protocol_hash")
    @classmethod
    def _valid_protocol_hash(cls, value: str) -> str:
        if not _SHA256_HEX.match(value):
            raise ValueError("protocol_hash must be a 64-char lowercase SHA-256 hex string")
        return value

    @field_validator("title", "command")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("field must be non-empty")
        return value


def validate_final_gate(record: RunRecord) -> None:
    """FINAL runs require a real commit and a clean tree.

    The sanctioned escape hatch is explicit: register the run under a non-final
    evidence stage instead. There is no silent override.
    """
    if record.evidence_stage is not EvidenceStage.FINAL:
        return
    if not record.git_commit:
        raise RegistryError(
            f"run {record.run_id}: FINAL evidence stage requires a git commit; "
            f"register under a non-final stage instead if the tree is not ready"
        )
    if record.git_dirty:
        raise RegistryError(
            f"run {record.run_id}: FINAL evidence stage refused because the git "
            f"tree is dirty; commit the tree or register under a non-final stage"
        )


def verify_output_hashes(record: RunRecord, base_dir: str | Path) -> None:
    """Recompute output hashes from recorded paths; raise on any mismatch."""
    if not record.output_paths:
        if record.output_hashes:
            raise RegistryError(
                f"run {record.run_id}: output_hashes recorded without output_paths"
            )
        return
    recomputed = compute_output_hashes(list(record.output_paths), base_dir)
    if recomputed != record.output_hashes:
        raise RegistryError(
            f"run {record.run_id}: output hashes are not reproducible; "
            f"recorded={record.output_hashes} recomputed={recomputed}"
        )


class Registry:
    """Append-only run registry rooted at a directory (e.g. ``experiments/registry``)."""

    def __init__(self, root: str | Path, repo_root: str | Path | None = None) -> None:
        self.root = Path(root)
        self.runs_dir = self.root / "runs"
        self.log_path = self.root / "log.jsonl"
        self.repo_root = Path(repo_root) if repo_root is not None else self.root

    # -- storage -----------------------------------------------------------

    def _record_path(self, run_id: str) -> Path:
        return self.runs_dir / f"{run_id}.json"

    def _append_record(self, record: RunRecord) -> None:
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        target = self._record_path(record.run_id)
        if target.exists():
            raise RegistryError(
                f"run record already exists: {target} (registry is append-only)"
            )
        target.write_text(
            json.dumps(record.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def _replace_record(self, record: RunRecord) -> None:
        """Sanctioned rewrite used only by status transitions."""
        target = self._record_path(record.run_id)
        if not target.exists():
            raise RegistryError(f"cannot transition unknown run {record.run_id}")
        target.write_text(
            json.dumps(record.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def _append_event(self, event: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, sort_keys=True) + "\n")

    # -- operations --------------------------------------------------------

    def register(
        self,
        *,
        title: str,
        evidence_stage: EvidenceStage,
        command: str,
        protocol_hash: str,
        data_manifests: dict[str, str] | None = None,
        reference_checksum: str | None = None,
        model_identity: str | None = None,
        scorer_config: dict[str, Any] | None = None,
        comparator_versions: dict[str, str] | None = None,
        seed: int | None = None,
        hardware: dict[str, str] | None = None,
        parent_run_id: str | None = None,
        now: datetime | None = None,
    ) -> RunRecord:
        if parent_run_id is not None:
            parent = self.load(parent_run_id)
            if parent.status in TERMINAL_STATUSES:
                raise RegistryError(
                    f"parent run {parent_run_id} is terminal "
                    f"({parent.status.value}); cannot attach children"
                )
        commit, dirty = git_state(self.repo_root)
        record = RunRecord(
            run_id=self._allocate_run_id(now),
            title=title,
            evidence_stage=evidence_stage,
            status=RunStatus.REGISTERED,
            protocol_hash=protocol_hash,
            git_commit=commit,
            git_dirty=dirty,
            data_manifests=data_manifests or {},
            reference_checksum=reference_checksum,
            model_identity=model_identity,
            scorer_config=scorer_config or {},
            comparator_versions=comparator_versions or {},
            seed=seed,
            hardware=hardware or {},
            command=command,
            created_at=utc_now_iso(now),
            updated_at=utc_now_iso(now),
            parent_run_id=parent_run_id,
            output_paths=(),
            output_hashes={},
        )
        validate_final_gate(record)
        self._append_record(record)
        self._append_event(
            {"event": "register", "run_id": record.run_id, "at": record.created_at}
        )
        return record

    def transition(
        self,
        run_id: str,
        status: RunStatus,
        *,
        output_paths: Sequence[str] | None = None,
        outputs_base_dir: str | Path | None = None,
        reason: str | None = None,
        now: datetime | None = None,
    ) -> RunRecord:
        current = self.load(run_id)
        if current.status in TERMINAL_STATUSES:
            raise RegistryError(
                f"run {run_id} is terminal ({current.status.value}); "
                f"terminal states are final and cannot transition"
            )
        if status is RunStatus.COMPLETED:
            if not output_paths:
                raise RegistryError(
                    f"run {run_id}: COMPLETED requires output_paths so output "
                    f"hashes are recomputable"
                )
            base = outputs_base_dir if outputs_base_dir is not None else self.root
            hashes = compute_output_hashes(output_paths, base)
            updated_paths: tuple[str, ...] = tuple(
                Path(p).as_posix() for p in sorted(str(p) for p in output_paths)
            )
        else:
            hashes = dict(current.output_hashes)
            updated_paths = current.output_paths
        updated = current.model_copy(
            update={
                "status": status,
                "updated_at": utc_now_iso(now),
                "output_paths": updated_paths,
                "output_hashes": hashes,
            }
        )
        self._replace_record(updated)
        event: dict[str, Any] = {
            "event": "transition",
            "run_id": run_id,
            "from": current.status.value,
            "to": status.value,
            "at": updated.updated_at,
        }
        if reason:
            event["reason"] = reason
        self._append_event(event)
        return updated

    # -- reads -------------------------------------------------------------

    def load(self, run_id: str) -> RunRecord:
        target = self._record_path(run_id)
        if not target.is_file():
            raise RegistryError(f"unknown run_id: {run_id}")
        raw = json.loads(target.read_text(encoding="utf-8"))
        return RunRecord.model_validate(raw)

    def list_runs(self) -> list[RunRecord]:
        if not self.runs_dir.is_dir():
            return []
        return sorted(
            (
                RunRecord.model_validate(json.loads(path.read_text(encoding="utf-8")))
                for path in self.runs_dir.glob("run_*.json")
            ),
            key=lambda record: record.run_id,
        )

    def children(self, run_id: str) -> list[RunRecord]:
        return [r for r in self.list_runs() if r.parent_run_id == run_id]

    def _allocate_run_id(self, now: datetime | None) -> str:
        for _ in range(_MAX_ID_ATTEMPTS):
            candidate = generate_run_id(now)
            if not self._record_path(candidate).exists():
                return candidate
        raise RegistryError("could not allocate a unique run_id")
