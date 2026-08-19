"""End-to-end scoring orchestration for EvoVariant-TR (Milestone 50).

This module orchestrates the full pipeline from cohort construction to
scoring, using a deterministic fake scorer for testing. The same interface
can be used with the real Evo 2 scorer (which requires GPU access).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from evovariant_tr.calibration import build_calibration_cohort
from evovariant_tr.cohort_fast import build_cohort_fast
from evovariant_tr.scorer import Scorer, ScoringResult
from evovariant_tr.sequence_cache import SequenceCache
from evovariant_tr.sequence_mutate import VariantIdentity
from evovariant_tr.sequence_window import (
    ReferenceWindow,
    generate_reference_window,
)


@dataclass
class OrchestrationResult:
    """Result of end-to-end scoring orchestration."""

    primary_cohort: dict[str, Any]
    calibration_cohort: dict[str, Any]
    disjoint_check: dict[str, Any]
    scoring: ScoringResult | None
    total_time_seconds: float
    cache_dir: str | None
    errors: list[str] = field(default_factory=list)


def run_scoring_orchestration(
    t0_path: str | Path,
    t1_path: str | Path,
    fasta_path: str | Path,
    fai_path: str | Path,
    scorer: Scorer,
    cache_dir: str | Path | None = None,
    max_variants: int | None = None,
) -> OrchestrationResult:
    """Run the full scoring pipeline from cohort to results.

    Args:
        t0_path: Path to t0 ClinVar variant_summary archive.
        t1_path: Path to t1 ClinVar variant_summary archive.
        fasta_path: Path to reference genome FASTA.
        fai_path: Path to reference genome .fai index.
        scorer: The scorer to use (FakeScorer for tests, Evo2Scorer for production).
        cache_dir: Optional cache directory for reference windows.
        max_variants: Optional limit on number of variants to score.

    Returns:
        An OrchestrationResult with all pipeline outputs.
    """
    start_time = time.time()
    errors: list[str] = []

    health = scorer.check_health()
    if not health.get("healthy", True):
        errors.append(f"Scorer health check failed: {health}")

    primary_cohort = build_cohort_fast(t0_path, t1_path)
    cal_cohort = build_calibration_cohort(t0_path, t1_path)

    from evovariant_tr.calibration import check_disjoint
    disjoint = check_disjoint(t0_path)

    cache: SequenceCache | None = None
    if cache_dir is not None:
        cache = SequenceCache(cache_dir)

    scoring_result: ScoringResult | None = None
    if primary_cohort["n_total"] > 0:
        scored_variants: list[tuple[ReferenceWindow, VariantIdentity, str]] = []

        from evovariant_tr.cohort_fast import _load_t0_vus

        vus_data, _ = _load_t0_vus(t0_path)

        count = 0
        for identity, _record in vus_data.items():
            if max_variants is not None and count >= max_variants:
                break

            chrom, start, ref, alt = identity
            variant = VariantIdentity(
                chrom=chrom, start=start, ref=ref, alt=alt,
            )

            if cache is not None:
                cache_entry = cache.get_or_compute(
                    chrom, start, fasta_path, fai_path,
                )
                window = ReferenceWindow(
                    chrom=cache_entry.chrom,
                    start=cache_entry.window_start,
                    stop=cache_entry.window_stop,
                    ref_sequence=cache_entry.ref_sequence,
                    variant_offset=cache_entry.variant_offset,
                )
            else:
                window = generate_reference_window(
                    fasta_path, fai_path, chrom, start,
                )

            scored_variants.append((window, variant, "forward"))
            count += 1

        scoring_result = scorer.score_batch(scored_variants)

    elapsed = time.time() - start_time

    return OrchestrationResult(
        primary_cohort=primary_cohort,
        calibration_cohort=cal_cohort.to_dict(),
        disjoint_check=disjoint,
        scoring=scoring_result,
        total_time_seconds=elapsed,
        cache_dir=str(cache_dir) if cache_dir else None,
        errors=errors,
    )


def result_to_json(result: OrchestrationResult) -> dict[str, Any]:
    """Convert an OrchestrationResult to a JSON-serializable dict."""
    scoring_data = None
    if result.scoring:
        scoring_data = {
            "total": result.scoring.total,
            "scored": len(result.scoring.scored),
            "failed": len(result.scoring.failed),
            "scorer_name": result.scoring.scorer_name,
            "scorer_version": result.scoring.scorer_version,
            "timing_ms": result.scoring.timing_ms,
        }

    return {
        "primary_cohort": result.primary_cohort,
        "calibration_cohort": result.calibration_cohort,
        "disjoint_check": result.disjoint_check,
        "scoring": scoring_data,
        "total_time_seconds": result.total_time_seconds,
        "cache_dir": result.cache_dir,
        "errors": result.errors,
    }