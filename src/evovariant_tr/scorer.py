"""Model-agnostic scorer interface for EvoVariant-TR (Milestone 47).

Defines the abstract interface that any sequence-variant scorer must implement.
This allows swapping between Evo 2 (GPU), fake scorers (tests), and
alternative baselines (PhyloP, CADD) without changing the orchestration
code.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from evovariant_tr.cohort_fast import FastVariant
from evovariant_tr.sequence_mutate import VariantIdentity
from evovariant_tr.sequence_window import ReferenceWindow


@dataclass
class ScoredVariant:
    """A variant with its score and metadata."""

    identity: VariantIdentity
    reference_window: ReferenceWindow
    reference_score: float
    alternate_score: float
    score_delta: float
    allele_likelihood: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ScoringResult:
    """Result of scoring a batch of variants."""

    scored: list[ScoredVariant]
    failed: list[tuple[VariantIdentity, str]]
    total: int
    batch_size: int
    timing_ms: float
    scorer_name: str
    scorer_version: str


class Scorer(ABC):
    """Abstract base class for sequence-variant scorers.

    All scorers must:
    1. Be deterministic (same input → same output).
    2. Return reference_score, alternate_score, and score_delta.
    3. Handle strand orientation correctly.
    4. Report provenance metadata.
    """

    name: str = "abstract"
    version: str = "0.0.0"
    context_length_bp: int = 8192

    @abstractmethod
    def score_variant(
        self,
        ref_window: ReferenceWindow,
        variant: VariantIdentity,
        strand: str = "forward",
    ) -> tuple[float, float, float]:
        """Score a single variant.

        Args:
            ref_window: The reference sequence window.
            variant: The variant to score.
            strand: Forward or reverse strand.

        Returns:
            Tuple of (reference_score, alternate_score, score_delta).
            score_delta = alternate_score - reference_score.
            Positive delta = alternate is more likely under the model.
        """

    @abstractmethod
    def score_batch(
        self,
        variants: list[tuple[ReferenceWindow, VariantIdentity, str]],
    ) -> ScoringResult:
        """Score a batch of variants.

        Args:
            variants: List of (ref_window, variant, strand) tuples.

        Returns:
            A ScoringResult with all scored variants.
        """

    @abstractmethod
    def score_cohort(
        self,
        cohort: list[FastVariant],
    ) -> ScoringResult:
        """Score a full cohort of variants.

        Args:
            cohort: List of FastVariant objects from the cohort builder.

        Returns:
            A ScoringResult with all scored variants.
        """

    @abstractmethod
    def check_health(self) -> dict[str, Any]:
        """Check that the scorer is ready and healthy.

        Returns:
            Dict with health check results.
        """

    def provenance(self) -> dict[str, Any]:
        """Return provenance metadata for this scorer."""
        return {
            "scorer_name": self.name,
            "scorer_version": self.version,
            "context_length_bp": self.context_length_bp,
            "deterministic": True,
        }
