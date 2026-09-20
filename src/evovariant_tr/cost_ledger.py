"""Append-only cost records for local, Modal, and explicitly deferred work."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

Backend = Literal["local", "modal", "unavailable"]
LedgerStatus = Literal["PLANNED", "RUNNING", "COMPLETED", "FAILED", "DEFERRED"]


@dataclass(frozen=True)
class CostLedgerEntry:
    run_id: str
    timestamp: str
    workload: str
    backend: Backend
    gpu_type: str | None
    gpu_count: int
    estimated_seconds: float | None
    measured_seconds: float | None
    estimated_usd: float | None
    measured_usd: float | None
    cache_hit: bool
    approval_artifact: str | None
    status: LedgerStatus
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def new_entry(
    *,
    run_id: str,
    workload: str,
    backend: Backend,
    status: LedgerStatus,
    gpu_type: str | None = None,
    gpu_count: int = 0,
    estimated_seconds: float | None = None,
    measured_seconds: float | None = None,
    estimated_usd: float | None = None,
    measured_usd: float | None = None,
    cache_hit: bool = False,
    approval_artifact: str | None = None,
    notes: str = "",
) -> CostLedgerEntry:
    """Construct a schema-shaped record without inventing unavailable costs."""
    return CostLedgerEntry(
        run_id=run_id,
        timestamp=datetime.now(UTC).isoformat(),
        workload=workload,
        backend=backend,
        gpu_type=gpu_type,
        gpu_count=gpu_count,
        estimated_seconds=estimated_seconds,
        measured_seconds=measured_seconds,
        estimated_usd=estimated_usd,
        measured_usd=measured_usd,
        cache_hit=cache_hit,
        approval_artifact=approval_artifact,
        status=status,
        notes=notes,
    )


def append_entry(path: str | Path, entry: CostLedgerEntry) -> None:
    """Append one JSON record and validate the local scalar constraints."""
    if entry.gpu_count < 0:
        raise ValueError("gpu_count cannot be negative")
    for field_name in (
        "estimated_seconds",
        "measured_seconds",
        "estimated_usd",
        "measured_usd",
    ):
        value = getattr(entry, field_name)
        if value is not None and value < 0:
            raise ValueError(f"{field_name} cannot be negative")
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry.to_dict(), sort_keys=True) + "\n")


def load_entries(path: str | Path) -> list[dict[str, Any]]:
    """Load an append-only JSONL ledger without changing it."""
    target = Path(path)
    if not target.is_file():
        return []
    return [json.loads(line) for line in target.read_text(encoding="utf-8").splitlines()]
