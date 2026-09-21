"""Batch job submission and resumption for EvoVariant-TR (Milestone 66-67).

This module implements:
- Shard-based batch submission for efficient GPU utilization
- Deterministic sharding with content-addressed shard IDs
- Idempotent resume and retry semantics
- Explicit failure taxonomy and observability
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from evovariant_tr.cohort_fast import FastVariant


class FailureKind(StrEnum):
    """Taxonomy of failure types for scoring jobs."""

    SEQUENCE_ERROR = "sequence_error"
    MODEL_ERROR = "model_error"
    GPU_ERROR = "gpu_error"
    TIMEOUT = "timeout"
    OUT_OF_MEMORY = "out_of_memory"
    NETWORK_ERROR = "network_error"
    VALIDATION_ERROR = "validation_error"
    UNKNOWN = "unknown"


@dataclass
class ShardSpec:
    """Specification for a scoring shard."""

    shard_id: str
    variant_count: int
    batch_size: int
    expected_duration_seconds: float
    provenance: dict[str, str] = field(default_factory=dict)


@dataclass
class ShardResult:
    """Result of a completed shard."""

    shard_id: str
    status: str
    scored: list[dict[str, Any]] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)
    timing_ms: float = 0.0
    completed_at: str = ""


@dataclass
class BatchJob:
    """A batch scoring job with resume/retry support."""

    job_id: str
    cohort_name: str
    total_variants: int
    shard_size: int
    status: str = "pending"
    created_at: str = field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )
    completed_at: str = ""
    shards: list[ShardResult] = field(default_factory=list)
    failed_shards: list[str] = field(default_factory=list)
    retry_count: int = 0

    def __post_init__(self) -> None:
        if self.total_variants < 0:
            raise ValueError("total_variants cannot be negative")
        if self.shard_size <= 0:
            raise ValueError("shard_size must be positive")

    @property
    def total_shards(self) -> int:
        """Return the deterministic shard count persisted in the manifest."""
        if self.total_variants == 0:
            return 0
        return (self.total_variants + self.shard_size - 1) // self.shard_size

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "cohort_name": self.cohort_name,
            "total_variants": self.total_variants,
            "shard_size": self.shard_size,
            "total_shards": self.total_shards,
            "status": self.status,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "shards_completed": len(self.shards),
            "shards_failed": len(self.failed_shards),
            "retry_count": self.retry_count,
        }


def compute_shard_id(
    variant_identities: list[tuple[str, int, str, str]],
    rank: int,
    total_ranks: int,
) -> str:
    """Compute a deterministic shard ID from variant identities."""
    sorted_ids = sorted(variant_identities)
    raw = json.dumps(sorted_ids, sort_keys=True) + f":{rank}:{total_ranks}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def create_shards(
    variants: list[FastVariant],
    shard_size: int,
    batch_size: int,
    n_ranks: int = 1,
) -> list[ShardSpec]:
    """Split variants into deterministic shards for parallel processing."""
    if shard_size <= 0:
        raise ValueError("shard_size must be positive")
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    if n_ranks <= 0:
        raise ValueError("n_ranks must be positive")
    shards: list[ShardSpec] = []
    identities = [
        (v.chrom, v.start, v.ref, v.alt) for v in variants
    ]

    for i in range(0, len(variants), shard_size):
        end = min(i + shard_size, len(variants))
        shard_variants = variants[i:end]
        shard_ids = identities[i:end]

        rank = (i // shard_size) % n_ranks
        shard_id = compute_shard_id(shard_ids, rank, n_ranks)

        expected_time = len(shard_variants) * 0.001
        shards.append(ShardSpec(
            shard_id=shard_id,
            variant_count=len(shard_variants),
            batch_size=batch_size,
            expected_duration_seconds=expected_time,
            provenance={
                "first_chrom": shard_variants[0].chrom if shard_variants else "",
                "last_chrom": shard_variants[-1].chrom if shard_variants else "",
                "rank": str(rank),
            },
        ))

    return shards


def create_job_id(cohort_name: str, shard_size: int) -> str:
    """Create a deterministic job ID."""
    raw = f"{cohort_name}:{shard_size}:{datetime.now(UTC).strftime('%Y%m%d')}"
    return hashlib.sha256(raw.encode()).hexdigest()[:24]


def save_job_manifest(job: BatchJob, output_path: str | Path) -> None:
    """Save the job manifest to disk for resumability."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(job.to_dict(), indent=2))


def load_job_manifest(path: str | Path) -> dict[str, Any]:
    """Load a job manifest from disk."""
    data: dict[str, Any] = json.loads(Path(path).read_text())
    return data


def check_resume_state(job_dir: str | Path) -> dict[str, Any]:
    """Check the resume state of a job directory."""
    job_dir = Path(job_dir)
    manifest_path = job_dir / "job_manifest.json"
    if not manifest_path.exists():
        return {
            "is_resumable": False,
            "completed_shards": [],
            "failed_shards": [],
            "progress": 0.0,
        }

    manifest = json.loads(manifest_path.read_text())
    results_dir = job_dir / "shards"
    if results_dir.exists():
        completed = []
        failed = []
        for shard_file in results_dir.iterdir():
            data = json.loads(shard_file.read_text())
            if data.get("status") == "completed":
                completed.append(data["shard_id"])
            elif data.get("status") == "failed":
                failed.append(data["shard_id"])
        progress = len(completed) / max(1, manifest.get("total_shards", 1))
        return {
            "is_resumable": True,
            "completed_shards": completed,
            "failed_shards": failed,
            "progress": progress,
        }

    return {
        "is_resumable": True,
        "completed_shards": [],
        "failed_shards": [],
        "progress": 0.0,
    }


def write_shard_result(job_dir: str | Path, result: ShardResult) -> Path:
    """Atomically persist one shard result for idempotent resume."""
    target_dir = Path(job_dir) / "shards"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{result.shard_id}.json"
    payload = {
        "shard_id": result.shard_id,
        "status": result.status,
        "scored": result.scored,
        "errors": result.errors,
        "timing_ms": result.timing_ms,
        "completed_at": result.completed_at or datetime.now(UTC).isoformat(),
    }
    temporary = target.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    temporary.replace(target)
    return target


def load_shard_result(job_dir: str | Path, shard_id: str) -> ShardResult | None:
    """Load a previously persisted shard result, if present."""
    target = Path(job_dir) / "shards" / f"{shard_id}.json"
    if not target.is_file():
        return None
    data = json.loads(target.read_text(encoding="utf-8"))
    return ShardResult(
        shard_id=str(data["shard_id"]),
        status=str(data["status"]),
        scored=list(data.get("scored", [])),
        errors=list(data.get("errors", [])),
        timing_ms=float(data.get("timing_ms", 0.0)),
        completed_at=str(data.get("completed_at", "")),
    )


def retryable_failure(kind: FailureKind) -> bool:
    """Return whether retrying can plausibly change an external failure."""
    return kind in {
        FailureKind.GPU_ERROR,
        FailureKind.NETWORK_ERROR,
        FailureKind.TIMEOUT,
        FailureKind.MODEL_ERROR,
    }


def retry_backoff_seconds(attempt: int, base_seconds: float = 2.0) -> float:
    """Bounded exponential backoff for idempotent transient retries."""
    if attempt < 0:
        raise ValueError("attempt must be non-negative")
    return min(300.0, base_seconds * float(2**attempt))


def classify_error(error_message: str, error_type: str | None = None) -> FailureKind:
    """Classify an error into the failure taxonomy."""
    msg_lower = error_message.lower()

    if "out of memory" in msg_lower or "oom" in msg_lower:
        return FailureKind.OUT_OF_MEMORY
    if "cuda" in msg_lower or "gpu" in msg_lower:
        return FailureKind.GPU_ERROR
    if "timed out" in msg_lower or "timeout" in msg_lower:
        return FailureKind.TIMEOUT
    if "network" in msg_lower or "connection" in msg_lower:
        return FailureKind.NETWORK_ERROR
    if "sequence" in msg_lower and "length" in msg_lower:
        return FailureKind.SEQUENCE_ERROR
    if "validation" in msg_lower:
        return FailureKind.VALIDATION_ERROR
    if "model" in msg_lower and "load" in msg_lower:
        return FailureKind.MODEL_ERROR
    if error_type:
        if "runtime" in error_type.lower():
            return FailureKind.MODEL_ERROR
        if "value" in error_type.lower():
            return FailureKind.VALIDATION_ERROR
        if "index" in error_type.lower() or "key" in error_type.lower():
            return FailureKind.SEQUENCE_ERROR

    return FailureKind.UNKNOWN


@dataclass
class ScoringMetrics:
    """Aggregated metrics from a scoring run."""

    n_scored: int = 0
    n_failed: int = 0
    n_total: int = 0
    mean_score_delta: float = 0.0
    std_score_delta: float = 0.0
    mean_gc_content: float = 0.0
    failures_by_kind: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "n_scored": self.n_scored,
            "n_failed": self.n_failed,
            "n_total": self.n_total,
            "mean_score_delta": self.mean_score_delta,
            "std_score_delta": self.std_score_delta,
            "mean_gc_content": self.mean_gc_content,
            "failures_by_kind": dict(self.failures_by_kind),
        }
