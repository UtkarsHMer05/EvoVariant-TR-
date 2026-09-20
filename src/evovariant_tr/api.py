"""Research-only FastAPI service with a single canonical scoring contract.

The production app never constructs :class:`FakeScorer`. Tests inject it through
``create_app(FakeScorer())``. A real deployment must inject an explicitly
constructed model adapter such as ``Evo2Scorer`` after its own readiness gate.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

from evovariant_tr.metrics import compute_full_metrics
from evovariant_tr.scorer import OrientationScorePair, Scorer, score_orientations
from evovariant_tr.scoring_record import ScoringRecord
from evovariant_tr.sequence_mutate import VariantIdentity
from evovariant_tr.sequence_window import CONTEXT_LENGTH_BP, ReferenceWindow
from evovariant_tr.variant_schema import CanonicalVariant


class VariantRequest(BaseModel):
    """Transport request mapped to the canonical internal variant schema."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    assembly: str = "GRCh38"
    chromosome: str = Field(..., validation_alias=AliasChoices("chromosome", "chrom"))
    position_1based: int = Field(
        ..., ge=1, validation_alias=AliasChoices("position_1based", "start")
    )
    reference: str = Field(
        ..., min_length=1, max_length=32, validation_alias=AliasChoices("reference", "ref")
    )
    alternate: str = Field(
        ..., min_length=1, max_length=32,
        validation_alias=AliasChoices("alternate", "alt", "alternative"),
    )
    orientation: Literal["forward", "reverse", "both"] = Field(
        "both", validation_alias=AliasChoices("orientation", "strand")
    )

    @field_validator("assembly")
    @classmethod
    def validate_assembly(cls, value: str) -> str:
        if value != "GRCh38":
            raise ValueError("assembly must be GRCh38")
        return value

    @field_validator("chromosome")
    @classmethod
    def validate_chromosome(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("chromosome must be non-empty")
        return value if value.startswith("chr") else f"chr{value}"

    @field_validator("reference", "alternate")
    @classmethod
    def validate_alleles(cls, value: str) -> str:
        normalized = value.upper()
        if any(base not in "ACGT" for base in normalized):
            raise ValueError("alleles must contain only A/C/G/T")
        return normalized

    def canonical(self) -> CanonicalVariant:
        return CanonicalVariant(
            assembly=self.assembly,
            chromosome=self.chromosome,
            position_1based=self.position_1based,
            reference=self.reference,
            alternate=self.alternate,
        )


class BatchVariantRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    variants: list[VariantRequest]
    description: str = ""


class ScoreResponse(BaseModel):
    """Raw research score components; no clinical classification is returned."""

    model_config = ConfigDict(extra="forbid")

    variant: str
    normalized_variant_id: str
    assembly: str
    chromosome: str
    position_1based: int
    reference: str
    alternate: str
    reference_score: float
    alternate_score: float
    score_delta: float
    delta_forward: float | None
    delta_reverse: float | None
    delta_primary: float
    orientation_disagreement: float | None
    raw_scores: dict[str, dict[str, float]]
    status: str = "completed"
    provenance: dict[str, Any] | None = None


def _make_synthetic_window(variant: CanonicalVariant) -> ReferenceWindow:
    """Create a deterministic 8,192-base test window without genome claims."""
    start = max(1, variant.position_1based - 4095)
    offset = variant.position_1based - start
    if offset >= CONTEXT_LENGTH_BP:
        raise ValueError("synthetic variant position cannot fit in the context window")
    sequence = (
        "A" * offset
        + variant.reference
        + "T" * (CONTEXT_LENGTH_BP - offset - len(variant.reference))
    )
    if len(sequence) != CONTEXT_LENGTH_BP:
        raise ValueError("synthetic window construction produced the wrong length")
    return ReferenceWindow(
        chrom=variant.chromosome,
        start=start,
        stop=start + CONTEXT_LENGTH_BP - 1,
        ref_sequence=sequence,
        variant_offset=offset,
    )


def _variant_identity(variant: CanonicalVariant) -> VariantIdentity:
    return VariantIdentity(
        chrom=variant.chromosome,
        start=variant.position_1based,
        ref=variant.reference,
        alt=variant.alternate,
    )


def _pair_to_payload(
    request: VariantRequest,
    variant: CanonicalVariant,
    pair: OrientationScorePair,
    scorer: Scorer,
) -> dict[str, Any]:
    forward = pair.forward
    reverse = pair.reverse
    selected = forward or reverse
    if selected is None:
        raise ValueError("no orientation was scored")
    raw_scores: dict[str, dict[str, float]] = {}
    if forward is not None:
        raw_scores["forward"] = {
            "reference_score": forward.reference_score,
            "alternate_score": forward.alternate_score,
            "delta": forward.delta,
        }
    if reverse is not None:
        raw_scores["reverse"] = {
            "reference_score": reverse.reference_score,
            "alternate_score": reverse.alternate_score,
            "delta": reverse.delta,
        }
    return {
        "variant": (
            f"{variant.chromosome}:g.{variant.position_1based}"
            f"{variant.reference}>{variant.alternate}"
        ),
        "normalized_variant_id": variant.normalized_variant_id,
        "assembly": variant.assembly,
        "chromosome": variant.chromosome,
        "position_1based": variant.position_1based,
        "reference": variant.reference,
        "alternate": variant.alternate,
        # Compatibility fields remain raw components, never classifications.
        "reference_score": selected.reference_score,
        "alternate_score": selected.alternate_score,
        "score_delta": pair.delta_primary,
        "delta_forward": forward.delta if forward is not None else None,
        "delta_reverse": reverse.delta if reverse is not None else None,
        "delta_primary": pair.delta_primary,
        "orientation_disagreement": pair.abs_disagreement,
        "raw_scores": raw_scores,
        "status": "completed",
        "provenance": {
            "scorer": scorer.name,
            "scorer_version": scorer.version,
            "orientation_requested": request.orientation,
            "context_length_bp": CONTEXT_LENGTH_BP,
            "scoring_semantics": "alternate_minus_reference_log_likelihood",
            "research_only": True,
            "classification": "not_provided",
        },
    }


def create_app(configured_scorer: Scorer | None = None) -> FastAPI:
    """Create an API app with explicit scorer dependency injection.

    ``None`` is the safe production default until a real adapter is configured.
    It never falls back to an arbitrary synthetic scorer.
    """
    app = FastAPI(
        title="EvoVariant-TR Research API",
        description="Research-only raw genomic model scoring; no clinical classification.",
        version="0.2.0",
    )
    result_registry: dict[str, dict[str, Any]] = {}

    def require_scorer() -> Scorer:
        if configured_scorer is None:
            raise HTTPException(
                status_code=503,
                detail="No real research scorer is configured for this service",
            )
        return configured_scorer

    @app.get("/health")
    async def health_check() -> dict[str, Any]:
        if configured_scorer is None:
            return {
                "status": "unavailable",
                "scorer": "unconfigured",
                "timestamp": datetime.now(UTC).isoformat(),
                "scorer_health": {"healthy": False, "reason": "no scorer configured"},
            }
        health = configured_scorer.check_health()
        return {
            "status": "healthy" if health.get("healthy", False) else "degraded",
            "scorer": configured_scorer.name,
            "version": configured_scorer.version,
            "timestamp": datetime.now(UTC).isoformat(),
            "scorer_health": health,
        }

    @app.get("/protocol")
    async def get_protocol() -> dict[str, Any]:
        return {
            "protocol_version": "1.0.0",
            "ml_extension_protocol_version": "1.0.0",
            "context_length_bp": CONTEXT_LENGTH_BP,
            "frozen_date": "2026-08-18",
            "identity": "evovariant-tr",
            "scorer": configured_scorer.name if configured_scorer else "unconfigured",
            "scorer_version": configured_scorer.version if configured_scorer else None,
            "research_only": True,
        }

    @app.post("/score/variant", response_model=ScoreResponse)
    async def score_single_variant(request: VariantRequest) -> ScoreResponse:
        scorer = require_scorer()
        canonical = request.canonical()
        if not canonical.is_snv:
            raise HTTPException(status_code=422, detail="only SNVs are supported by this scorer")
        orientation_tuple = (
            (request.orientation,)
            if request.orientation != "both"
            else ("forward", "reverse")
        )
        try:
            pair = score_orientations(
                scorer,
                _make_synthetic_window(canonical),
                _variant_identity(canonical),
                orientations=orientation_tuple,
            )
            return ScoreResponse.model_validate(
                _pair_to_payload(request, canonical, pair, scorer)
            )
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Scoring failed: {exc}") from exc

    @app.post("/score/batch", response_model=dict[str, Any])
    async def score_batch_variants(request: BatchVariantRequest) -> dict[str, Any]:
        scorer = require_scorer()
        results: list[dict[str, Any]] = []
        failures: list[dict[str, str]] = []
        started = datetime.now(UTC)
        for item in request.variants:
            try:
                canonical = item.canonical()
                if not canonical.is_snv:
                    raise ValueError("only SNVs are supported by this scorer")
                orientation_tuple = (
                    (item.orientation,)
                    if item.orientation != "both"
                    else ("forward", "reverse")
                )
                pair = score_orientations(
                    scorer,
                    _make_synthetic_window(canonical),
                    _variant_identity(canonical),
                    orientations=orientation_tuple,
                )
                results.append(_pair_to_payload(item, canonical, pair, scorer))
            except Exception as exc:
                failures.append({"variant": repr(item.model_dump()), "error": str(exc)})
        elapsed_ms = (datetime.now(UTC) - started).total_seconds() * 1000
        return {
            "scored": len(results),
            "failed": len(failures),
            "results": results,
            "failures": failures,
            "timing_ms": elapsed_ms,
            "provenance": {"research_only": True, "scorer": scorer.name},
        }

    @app.post("/batch/submit", response_model=dict[str, Any])
    async def submit_batch_job(request: BatchVariantRequest) -> dict[str, Any]:
        scorer = require_scorer()
        job_id = str(uuid.uuid4())
        result_registry[job_id] = {
            "status": "queued",
            "description": request.description,
            "n_variants": len(request.variants),
            "created_at": datetime.now(UTC).isoformat(),
            "scorer": scorer.name,
            "research_only": True,
        }
        return {
            "job_id": job_id,
            "status": "queued",
            "n_variants": len(request.variants),
            "check_url": f"/batch/{job_id}",
        }

    @app.get("/batch/{job_id}", response_model=dict[str, Any])
    async def get_batch_status(job_id: str) -> dict[str, Any]:
        if job_id not in result_registry:
            raise HTTPException(status_code=404, detail="Job not found")
        return result_registry[job_id]

    @app.get("/results/{record_id}", response_model=dict[str, Any])
    async def get_result(record_id: str) -> dict[str, Any]:
        if record_id not in result_registry:
            raise HTTPException(status_code=404, detail=f"Result {record_id} not found")
        return result_registry[record_id]

    @app.get("/metrics", response_model=dict[str, Any])
    async def get_metrics() -> dict[str, Any]:
        records: list[ScoringRecord] = []
        for data in result_registry.values():
            if data.get("status") == "completed" and "score_delta" in data:
                records.append(
                    ScoringRecord(
                        chrom=data.get("chromosome", "chr1"),
                        start=data.get("position_1based", 0),
                        ref=data.get("reference", "A"),
                        alt=data.get("alternate", "T"),
                        scorer_name=data.get("scorer", "unconfigured"),
                        scorer_version="research",
                        score_delta=data["score_delta"],
                        outcome=data.get("outcome"),
                    )
                )
        if len(records) < 2:
            return {"error": "Not enough registered labeled records for metrics"}
        metrics = compute_full_metrics(records, n_bootstrap=min(100, len(records) // 2))
        return metrics.to_dict()

    return app


# Safe default for ASGI servers: deployment must inject a real adapter explicitly.
app = create_app()
