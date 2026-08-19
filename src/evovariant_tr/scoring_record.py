"""Scoring record and shard format for EvoVariant-TR (Milestone 61).

Defines the on-disk format for scoring records and shards, ensuring
determinism and reproducibility.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class ScoreStatus(StrEnum):
    """Status of a scoring attempt."""

    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ScoringRecord:
    """A single scoring record for one variant.

    This is the atomic unit of scoring output, persisted to disk as JSON.
    Each record is content-addressed by its sha256 hash.
    """

    chrom: str
    start: int
    ref: str
    alt: str
    scorer_name: str
    scorer_version: str
    context_length_bp: int = 8192
    strand: str = "forward"
    window_start: int = 0
    window_stop: int = 0
    variant_offset: int = 0
    reference_score: float = 0.0
    alternate_score: float = 0.0
    score_delta: float = 0.0
    allele_likelihood: float | None = None
    gene_symbol: str | None = None
    t0_clinical_significance: str | None = None
    t0_review_stars: int = 0
    t1_clinical_significance: str | None = None
    t1_review_stars: int | None = None
    outcome: str | None = None
    status: ScoreStatus = ScoreStatus.COMPLETED
    error: str | None = None
    created_at: str = field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )

    @property
    def identity(self) -> tuple[str, int, str, str]:
        return (self.chrom, self.start, self.ref, self.alt)

    @property
    def record_id(self) -> str:
        """Content-addressed ID for this record."""
        s = (
            f"{self.chrom}:{self.start}:{self.ref}:{self.alt}:"
            f"{self.scorer_name}:{self.scorer_version}"
        )
        return hashlib.sha256(s.encode()).hexdigest()[:32]

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "chrom": self.chrom,
            "start": self.start,
            "ref": self.ref,
            "alt": self.alt,
            "scorer_name": self.scorer_name,
            "scorer_version": self.scorer_version,
            "context_length_bp": self.context_length_bp,
            "strand": self.strand,
            "window_start": self.window_start,
            "window_stop": self.window_stop,
            "variant_offset": self.variant_offset,
            "reference_score": self.reference_score,
            "alternate_score": self.alternate_score,
            "score_delta": self.score_delta,
            "allele_likelihood": self.allele_likelihood,
            "gene_symbol": self.gene_symbol,
            "t0_clinical_significance": self.t0_clinical_significance,
            "t0_review_stars": self.t0_review_stars,
            "t1_clinical_significance": self.t1_clinical_significance,
            "t1_review_stars": self.t1_review_stars,
            "outcome": self.outcome,
            "status": self.status.value,
            "error": self.error,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ScoringRecord:
        """Deserialize a ScoringRecord from a dict."""
        status = ScoreStatus(data.get("status", ScoreStatus.COMPLETED))
        return cls(
            chrom=data["chrom"],
            start=data["start"],
            ref=data["ref"],
            alt=data["alt"],
            scorer_name=data["scorer_name"],
            scorer_version=data["scorer_version"],
            context_length_bp=data.get("context_length_bp", 8192),
            strand=data.get("strand", "forward"),
            window_start=data.get("window_start", 0),
            window_stop=data.get("window_stop", 0),
            variant_offset=data.get("variant_offset", 0),
            reference_score=data.get("reference_score", 0.0),
            alternate_score=data.get("alternate_score", 0.0),
            score_delta=data.get("score_delta", 0.0),
            allele_likelihood=data.get("allele_likelihood"),
            gene_symbol=data.get("gene_symbol"),
            t0_clinical_significance=data.get("t0_clinical_significance"),
            t0_review_stars=data.get("t0_review_stars", 0),
            t1_clinical_significance=data.get("t1_clinical_significance"),
            t1_review_stars=data.get("t1_review_stars"),
            outcome=data.get("outcome"),
            status=status,
            error=data.get("error"),
            created_at=data.get("created_at", ""),
        )


@dataclass
class ShardFile:
    """A shard file containing multiple scoring records."""

    shard_id: str
    records: list[ScoringRecord] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def shard_record_id(self) -> str:
        """Content-addressed ID for this shard."""
        record_ids = sorted(r.record_id for r in self.records)
        raw = self.shard_id + ":" + ",".join(record_ids)
        return hashlib.sha256(raw.encode()).hexdigest()[:32]

    def to_dict(self) -> dict[str, Any]:
        return {
            "shard_id": self.shard_id,
            "shard_record_id": self.shard_record_id,
            "record_count": len(self.records),
            "records": [r.to_dict() for r in self.records],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ShardFile:
        return cls(
            shard_id=data["shard_id"],
            records=[ScoringRecord.from_dict(r) for r in data.get("records", [])],
            metadata=data.get("metadata", {}),
        )

    @property
    def completed_count(self) -> int:
        return sum(1 for r in self.records if r.status == ScoreStatus.COMPLETED)

    @property
    def failed_count(self) -> int:
        return sum(1 for r in self.records if r.status == ScoreStatus.FAILED)