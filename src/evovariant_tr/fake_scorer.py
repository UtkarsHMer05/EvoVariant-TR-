"""Deterministic fake scorer for software tests (Milestone 48).

This scorer implements the Scorer interface but uses a simple deterministic
hash-based function to generate scores. It is NOT used for actual research
results — only for testing the orchestration pipeline.

The score is based on the GC-content of the variant site and the
length of the alternate allele, producing deterministic but arbitrary
values in the range [-10, 10].
"""

from __future__ import annotations

import hashlib
import time
from typing import Any

from evovariant_tr.cohort_fast import FastVariant
from evovariant_tr.scorer import ScoredVariant, Scorer, ScoringResult
from evovariant_tr.sequence_mutate import VariantIdentity
from evovariant_tr.sequence_window import ReferenceWindow

GENOMIC_NUCLS = frozenset({"A", "C", "G", "T"})


class FakeScorer(Scorer):
    """Deterministic fake scorer for testing.

    Uses a simple hash of the sequence context to produce reproducible
    but arbitrary scores. This allows testing the full orchestration
    pipeline without requiring GPU access or Evo 2 installation.
    """

    name = "fake_scorer"
    version = "0.1.0"
    context_length_bp = 8192

    def __init__(self, scale: float = 10.0) -> None:
        self._scale = scale

    def _hash_score(self, sequence: str) -> float:
        """Generate a deterministic score in [-scale, scale] from a sequence."""
        h = hashlib.sha256(sequence.encode()).hexdigest()
        # Use first 8 hex chars as a deterministic integer
        val = int(h[:8], 16)
        # Map to [-scale, scale]
        normalized = (val / 0xFFFFFFFF) * 2 - 1
        return normalized * self._scale

    def _sequence_gc_content(self, seq: str) -> float:
        """Compute GC content of a sequence."""
        if not seq:
            return 0.0
        gc = sum(1 for c in seq.upper() if c in ("G", "C"))
        return gc / len(seq)

    def score_variant(
        self,
        ref_window: ReferenceWindow,
        variant: VariantIdentity,
        strand: str = "forward",
    ) -> tuple[float, float, float]:
        """Score a variant using deterministic hash-based function.

        Reference score = hash of reference sequence.
        Alternate score = hash of alternate (mutated) sequence.
        """
        ref_seq = ref_window.ref_sequence
        if not ref_seq:
            return 0.0, 0.0, 0.0

        # Compute alternate sequence
        from evovariant_tr.sequence_mutate import apply_variant_to_reference

        try:
            alt_seq = apply_variant_to_reference(
                ref_seq, variant, ref_window.variant_offset, strand=strand,
            )
        except (ValueError, IndexError):
            return 0.0, 0.0, 0.0

        ref_score = self._hash_score(ref_seq)
        alt_score = self._hash_score(alt_seq)
        delta = alt_score - ref_score

        return ref_score, alt_score, delta

    def score_batch(
        self,
        variants: list[tuple[ReferenceWindow, VariantIdentity, str]],
    ) -> ScoringResult:
        """Score a batch of variants deterministically."""
        start_time = time.time()
        scored: list[ScoredVariant] = []
        failed: list[tuple[VariantIdentity, str]] = []

        for ref_window, variant, strand in variants:
            try:
                ref_score, alt_score, delta = self.score_variant(
                    ref_window, variant, strand,
                )
                scored.append(
                    ScoredVariant(
                        identity=variant,
                        reference_window=ref_window,
                        reference_score=ref_score,
                        alternate_score=alt_score,
                        score_delta=delta,
                        allele_likelihood=delta,
                        metadata={
                            "strand": strand,
                            "gc_content": self._sequence_gc_content(
                                ref_window.ref_sequence
                            ),
                        },
                    )
                )
            except Exception as e:
                failed.append((variant, str(e)))

        elapsed_ms = (time.time() - start_time) * 1000

        return ScoringResult(
            scored=scored,
            failed=failed,
            total=len(variants),
            batch_size=len(scored),
            timing_ms=elapsed_ms,
            scorer_name=self.name,
            scorer_version=self.version,
        )

    def score_cohort(self, cohort: list[FastVariant]) -> ScoringResult:
        """Score a full cohort (not implemented for fake scorer - use batch)."""
        raise NotImplementedError(
            "FakeScorer.score_cohort requires reference windows. "
            "Use score_batch with reference windows instead."
        )

    def check_health(self) -> dict[str, Any]:
        """Fake scorer is always healthy."""
        return {
            "healthy": True,
            "scorer": self.name,
            "version": self.version,
            "note": "Fake scorer - no external dependencies.",
        }
