"""Explicit-dependency proxy helpers for research API integrations."""

from __future__ import annotations

from typing import Any

from evovariant_tr.scorer import Scorer, score_orientations
from evovariant_tr.sequence_mutate import VariantIdentity
from evovariant_tr.sequence_window import CONTEXT_LENGTH_BP, ReferenceWindow
from evovariant_tr.variant_schema import CanonicalVariant

_configured_scorer: Scorer | None = None


def configure_scorer(scorer: Scorer | None) -> None:
    """Configure a real scorer explicitly for a process-local proxy."""
    global _configured_scorer
    _configured_scorer = scorer


def _make_window(variant: CanonicalVariant) -> ReferenceWindow:
    start = max(1, variant.position_1based - 4095)
    offset = variant.position_1based - start
    sequence = "A" * offset + variant.reference + "T" * (
        CONTEXT_LENGTH_BP - offset - len(variant.reference)
    )
    return ReferenceWindow(
        chrom=variant.chromosome,
        start=start,
        stop=start + CONTEXT_LENGTH_BP - 1,
        ref_sequence=sequence,
        variant_offset=offset,
    )


def score_variant_handler(
    chrom: str,
    start: int,
    ref: str,
    alt: str,
    strand: str = "both",
    *,
    scorer: Scorer | None = None,
) -> dict[str, Any]:
    """Score one canonical variant through an explicitly supplied adapter."""
    active_scorer = scorer or _configured_scorer
    if active_scorer is None:
        raise RuntimeError("no real research scorer configured for API proxy")
    normalized_chrom = chrom if chrom.startswith("chr") else f"chr{chrom}"
    variant = CanonicalVariant(
        "GRCh38", normalized_chrom, start, ref.upper(), alt.upper()
    )
    identity = VariantIdentity(
        chrom=variant.chromosome,
        start=variant.position_1based,
        ref=variant.reference,
        alt=variant.alternate,
    )
    orientations = ("forward", "reverse") if strand == "both" else (strand,)
    pair = score_orientations(
        active_scorer,
        _make_window(variant),
        identity,
        orientations=orientations,
    )
    return {
        "variant": variant.normalized_variant_id,
        "normalized_variant_id": variant.normalized_variant_id,
        "delta_forward": pair.forward.delta if pair.forward else None,
        "delta_reverse": pair.reverse.delta if pair.reverse else None,
        "delta_primary": pair.delta_primary,
        "orientation_disagreement": pair.abs_disagreement,
        "raw_scores": {
            orientation: {
                "reference_score": component.reference_score,
                "alternate_score": component.alternate_score,
                "delta": component.delta,
            }
            for orientation, component in (("forward", pair.forward), ("reverse", pair.reverse))
            if component is not None
        },
        "status": "completed",
        "provenance": {
            "scorer": active_scorer.name,
            "scorer_version": active_scorer.version,
            "context_length_bp": CONTEXT_LENGTH_BP,
            "research_only": True,
            "classification": "not_provided",
        },
    }


def get_protocol_info() -> dict[str, Any]:
    """Return protocol information without implying a configured scorer."""
    return {
        "protocol_version": "1.0.0",
        "ml_extension_protocol_version": "1.0.0",
        "context_length_bp": CONTEXT_LENGTH_BP,
        "scorer": _configured_scorer.name if _configured_scorer else "unconfigured",
        "scorer_version": _configured_scorer.version if _configured_scorer else None,
        "frozen_date": "2026-08-18",
        "research_only": True,
    }


def get_health() -> dict[str, Any]:
    """Return health status for the explicitly configured adapter."""
    if _configured_scorer is None:
        return {
            "status": "unavailable",
            "scorer": "unconfigured",
            "scorer_health": {"healthy": False, "reason": "no scorer configured"},
        }
    health = _configured_scorer.check_health()
    return {
        "status": "healthy" if health.get("healthy", False) else "degraded",
        "scorer": _configured_scorer.name,
        "version": _configured_scorer.version,
        "scorer_health": health,
    }
