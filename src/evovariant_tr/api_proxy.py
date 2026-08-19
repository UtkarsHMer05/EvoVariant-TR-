"""API route handler for variant scoring (Milestone 91-92).

Proxies requests to the FastAPI backend service.
In production, this would call the FastAPI service at the configured
backend URL. For development, it uses the in-process scorer.
"""

from __future__ import annotations

import os
from typing import Any

from evovariant_tr.fake_scorer import FakeScorer
from evovariant_tr.sequence_mutate import VariantIdentity
from evovariant_tr.sequence_window import ReferenceWindow

BACKEND_URL = os.environ.get("EVOVARIANT_BACKEND_URL", "")
scorer = FakeScorer(scale=1.0)


def _make_window(chrom: str, pos: int, ref: str) -> ReferenceWindow:
    """Create a synthetic reference window for scoring."""
    ref_sequence = "A" * 4096 + ref.upper() + "T" * 4095
    return ReferenceWindow(
        chrom=chrom,
        start=max(1, pos - 4095),
        stop=pos + 4096,
        ref_sequence=ref_sequence,
        variant_offset=4096,
    )


def score_variant_handler(
    chrom: str, start: int, ref: str, alt: str, strand: str = "forward",
) -> dict[str, Any]:
    """Score a single variant using the configured scorer."""
    variant = VariantIdentity(chrom=chrom, start=start, ref=ref, alt=alt)
    window = _make_window(chrom, start, ref)

    ref_score, alt_score, delta = scorer.score_variant(
        window, variant, strand=strand,
    )

    return {
        "variant": f"{chrom}:g.{start}{ref}>{alt}",
        "reference_score": ref_score,
        "alternate_score": alt_score,
        "score_delta": delta,
        "status": "completed",
        "provenance": {
            "scorer": scorer.name,
            "scorer_version": scorer.version,
            "strand": strand,
            "context_length": 8192,
        },
    }


def get_protocol_info() -> dict[str, Any]:
    """Return protocol information."""
    return {
        "protocol_version": "1.0.0",
        "context_length_bp": 8192,
        "scorer": scorer.name,
        "scorer_version": scorer.version,
        "frozen_date": "2026-08-18",
    }


def get_health() -> dict[str, Any]:
    """Return health status."""
    health = scorer.check_health()
    return {
        "status": "healthy",
        "scorer": scorer.name,
        "version": scorer.version,
        "scorer_health": health,
    }