"""Common status/artifact contract for gated ML-extension experiments.

An explicit non-completed artifact is useful evidence: it records why work did
not run without inventing metrics or implying that a dependency passed.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any


class ExecutionStatus(StrEnum):
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"
    DEFERRED = "DEFERRED"
    DEFERRED_BY_COMPUTE = "DEFERRED_BY_COMPUTE"
    NOT_RUN = "NOT_RUN"
    FAILED = "FAILED"


@dataclass(frozen=True)
class ExperimentArtifact:
    """A status record that cannot carry metrics unless execution completed."""

    phase: int
    family: str
    status: ExecutionStatus
    blockers: tuple[str, ...] = ()
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def __post_init__(self) -> None:
        if self.phase < 0:
            raise ValueError("phase must be non-negative")
        if not self.family.strip():
            raise ValueError("family must be non-empty")
        if self.status is not ExecutionStatus.COMPLETED and self.metrics:
            raise ValueError("blocked/deferred artifacts cannot carry scientific metrics")

    def to_dict(self) -> dict[str, Any]:
        return {
            "phase": self.phase,
            "family": self.family,
            "status": self.status.value,
            "blockers": list(self.blockers),
            "inputs": self.inputs,
            "outputs": self.outputs,
            "metrics": self.metrics,
            "created_at": self.created_at,
        }


def deferred_artifact(
    *,
    phase: int,
    family: str,
    blockers: list[str] | tuple[str, ...],
    inputs: dict[str, Any] | None = None,
    status: ExecutionStatus = ExecutionStatus.BLOCKED,
) -> ExperimentArtifact:
    """Build a truthful no-result artifact for a gated experiment."""
    if status is ExecutionStatus.COMPLETED:
        raise ValueError("deferred_artifact cannot have COMPLETED status")
    return ExperimentArtifact(
        phase=phase,
        family=family,
        status=status,
        blockers=tuple(blockers),
        inputs=inputs or {},
    )


def write_artifact(path: str | Path, artifact: ExperimentArtifact) -> Path:
    """Write a status artifact atomically enough for local control files."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(
        json.dumps(artifact.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(target)
    return target


def read_artifact(path: str | Path) -> ExperimentArtifact:
    """Read and reconstruct an experiment status artifact."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return ExperimentArtifact(
        phase=int(data["phase"]),
        family=str(data["family"]),
        status=ExecutionStatus(str(data["status"])),
        blockers=tuple(str(value) for value in data.get("blockers", [])),
        inputs=dict(data.get("inputs", {})),
        outputs=dict(data.get("outputs", {})),
        metrics=dict(data.get("metrics", {})),
        created_at=str(data["created_at"]),
    )
