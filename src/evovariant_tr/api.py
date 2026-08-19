"""Research FastAPI service for EvoVariant-TR (Milestone 91-92).

Provides single-variant and batch scoring endpoints with
async batch job submission and result registry.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator

from evovariant_tr.fake_scorer import FakeScorer
from evovariant_tr.metrics import compute_full_metrics
from evovariant_tr.scorer import ScoringResult
from evovariant_tr.scoring_record import ScoringRecord
from evovariant_tr.sequence_mutate import VariantIdentity
from evovariant_tr.sequence_window import (
    CONTEXT_LENGTH_BP,
    ReferenceWindow,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

app = FastAPI(
    title="EvoVariant-TR Research API",
    description="Research API for variant pathogenicity scoring",
    version="0.1.0",
)

scorer = FakeScorer(scale=1.0)
result_registry: dict[str, dict[str, Any]] = {}


class VariantRequest(BaseModel):
    chrom: str = Field(..., description="Chromosome name")
    start: int = Field(..., description="1-based start position", ge=1)
    ref: str = Field(..., description="Reference allele", min_length=1, max_length=32)
    alt: str = Field(..., description="Alternate allele", min_length=1, max_length=32)
    strand: str = Field("forward", description="Strand: forward or reverse")
    model_config = {"json_schema_extra": {
        "examples": [{"chrom": "chr1", "start": 100, "ref": "A", "alt": "T"}]
    }}

    @field_validator("strand")
    @classmethod
    def validate_strand(cls, v: str) -> str:
        if v not in ("forward", "reverse"):
            raise ValueError("strand must be 'forward' or 'reverse'")
        return v

    @field_validator("ref", "alt")
    @classmethod
    def validate_alleles(cls, v: str) -> str:
        import re as _re

        if not _re.match(r"^[ACGTN]+$", v, _re.IGNORECASE):
            raise ValueError("alleles must contain only nucleotide characters ACGTN")
        return v.upper()


class BatchVariantRequest(BaseModel):
    variants: list[VariantRequest]
    description: str = ""


class ScoreResponse(BaseModel):
    variant: str
    reference_score: float
    alternate_score: float
    score_delta: float
    status: str = "completed"
    provenance: dict[str, Any] | None = None


@app.get("/health")
async def health_check() -> dict[str, Any]:
    """Health check endpoint."""
    health = scorer.check_health()
    return {
        "status": "healthy",
        "scorer": scorer.name,
        "version": scorer.version,
        "timestamp": datetime.now(UTC).isoformat(),
        "scorer_health": health,
    }


@app.get("/protocol")
async def get_protocol() -> dict[str, Any]:
    """Return the frozen protocol specification."""
    return {
        "protocol_version": "1.0.0",
        "context_length_bp": CONTEXT_LENGTH_BP,
        "scorer": scorer.name,
        "scorer_version": scorer.version,
        "frozen_date": "2026-08-18",
    }


def _make_synthetic_window(vr: VariantRequest) -> ReferenceWindow:
    """Create a synthetic reference window for scoring."""
    ref_sequence = "A" * 4096 + vr.ref.upper() + "T" * 4095
    return ReferenceWindow(
        chrom=vr.chrom,
        start=max(1, vr.start - 4095),
        stop=vr.start + 4096,
        ref_sequence=ref_sequence,
        variant_offset=4096,
    )


@app.post("/score/variant", response_model=ScoreResponse)
async def score_single_variant(request: VariantRequest) -> ScoreResponse:
    """Score a single variant."""
    variant = VariantIdentity(
        chrom=request.chrom, start=request.start,
        ref=request.ref, alt=request.alt,
    )
    window = _make_synthetic_window(request)

    try:
        ref_score, alt_score, delta = scorer.score_variant(
            window, variant, strand=request.strand,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scoring failed: {e}") from e

    return ScoreResponse(
        variant=f"{request.chrom}:g.{request.start}{request.ref}>{request.alt}",
        reference_score=ref_score,
        alternate_score=alt_score,
        score_delta=delta,
        provenance={
            "scorer": scorer.name,
            "scorer_version": scorer.version,
            "strand": request.strand,
            "context_length": CONTEXT_LENGTH_BP,
        },
    )


@app.post("/score/batch", response_model=dict[str, Any])
async def score_batch_variants(request: BatchVariantRequest) -> dict[str, Any]:
    """Score a batch of variants."""
    windows_and_variants: list[tuple[ReferenceWindow, VariantIdentity, str]] = []
    for vr in request.variants:
        variant = VariantIdentity(
            chrom=vr.chrom, start=vr.start, ref=vr.ref, alt=vr.alt,
        )
        window = _make_synthetic_window(vr)
        windows_and_variants.append((window, variant, vr.strand))

    result: ScoringResult = scorer.score_batch(windows_and_variants)
    return {
        "scored": len(result.scored),
        "failed": len(result.failed),
        "results": [
            {
                "variant": (
                    f"{r.identity.chrom}:g.{r.identity.start}"
                    f"{r.identity.ref}>{r.identity.alt}"
                ),
                "reference_score": r.reference_score,
                "alternate_score": r.alternate_score,
                "score_delta": r.score_delta,
            }
            for r in result.scored
        ],
        "failures": [
            {"variant": str(f[0]), "error": f[1]} for f in result.failed
        ],
        "timing_ms": result.timing_ms,
    }


@app.post("/batch/submit", response_model=dict[str, Any])
async def submit_batch_job(request: BatchVariantRequest) -> dict[str, Any]:
    """Submit an async batch job."""
    job_id = str(uuid.uuid4())
    result_registry[job_id] = {
        "status": "queued",
        "description": request.description,
        "n_variants": len(request.variants),
        "created_at": datetime.now(UTC).isoformat(),
        "scorer": scorer.name,
    }
    return {
        "job_id": job_id,
        "status": "queued",
        "n_variants": len(request.variants),
        "check_url": f"/batch/{job_id}",
    }


@app.get("/batch/{job_id}", response_model=dict[str, Any])
async def get_batch_status(job_id: str) -> dict[str, Any]:
    """Get batch job status."""
    if job_id not in result_registry:
        raise HTTPException(status_code=404, detail="Job not found")
    return result_registry[job_id]


@app.get("/results/{record_id}", response_model=dict[str, Any])
async def get_result(record_id: str) -> dict[str, Any]:
    """Get a result by ID."""
    if record_id not in result_registry:
        raise HTTPException(
            status_code=404,
            detail=f"Result {record_id} not found",
        )
    return result_registry[record_id]


@app.get("/metrics", response_model=dict[str, Any])
async def get_metrics() -> dict[str, Any]:
    """Get aggregated metrics from all scored variants."""
    records: list[ScoringRecord] = []
    for data in result_registry.values():
        if data.get("status") == "completed" and "score_delta" in data:
            records.append(ScoringRecord(
                chrom=data.get("chrom", "chr1"),
                start=data.get("start", 0),
                ref=data.get("ref", "A"),
                alt=data.get("alt", "T"),
                scorer_name=data.get("scorer", "fake"),
                scorer_version="1.0",
                score_delta=data["score_delta"],
                outcome=data.get("outcome"),
            ))

    if len(records) < 2:
        return {"error": "Not enough records for metrics"}

    metrics = compute_full_metrics(
        records, n_bootstrap=min(100, len(records) // 2),
    )
    return metrics.to_dict()