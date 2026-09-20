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


@dataclass(frozen=True)
class OrientationScore:
    """Raw score components for one orientation."""

    reference_score: float
    alternate_score: float
    delta: float


@dataclass(frozen=True)
class OrientationScorePair:
    """Forward/RC components and the frozen primary aggregate."""

    forward: OrientationScore | None
    reverse: OrientationScore | None

    @property
    def delta_primary(self) -> float:
        """Return the mean of available orientation deltas."""
        deltas = [
            component.delta
            for component in (self.forward, self.reverse)
            if component is not None
        ]
        if not deltas:
            raise ValueError("at least one orientation score is required")
        return sum(deltas) / len(deltas)

    @property
    def abs_disagreement(self) -> float | None:
        """Return absolute FWD/RC disagreement when both are available."""
        if self.forward is None or self.reverse is None:
            return None
        return abs(self.forward.delta - self.reverse.delta)


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


def score_orientations(
    scorer: Scorer,
    ref_window: ReferenceWindow,
    variant: VariantIdentity,
    *,
    orientations: tuple[str, ...] = ("forward", "reverse"),
) -> OrientationScorePair:
    """Score a validated variant in the requested orientations.

    This helper is the canonical aggregation boundary. It refuses to pass a
    variable-length or reference-mismatched window to a model and retains all
    raw components before calculating the primary orientation mean.
    """
    if len(ref_window.ref_sequence) != scorer.context_length_bp:
        raise ValueError(
            f"reference window length {len(ref_window.ref_sequence)} != "
            f"scorer context {scorer.context_length_bp}"
        )
    if ref_window.stop - ref_window.start + 1 != scorer.context_length_bp:
        raise ValueError("window coordinates do not describe the scorer context length")
    if ref_window.variant_offset < 0 or ref_window.variant_offset >= len(ref_window.ref_sequence):
        raise ValueError("variant offset is outside the reference window")
    actual_ref = ref_window.ref_sequence[ref_window.variant_offset].upper()
    if actual_ref != variant.ref.upper():
        raise ValueError(
            f"reference allele mismatch at offset {ref_window.variant_offset}: "
            f"expected {variant.ref.upper()}, found {actual_ref}"
        )
    if not variant.is_snp:
        raise ValueError("the canonical sequence scoring contract currently accepts SNVs only")
    if variant.ref.upper() == variant.alt.upper():
        raise ValueError("reference and alternate alleles must differ")

    normalized_orientations = tuple(dict.fromkeys(orientations))
    if not normalized_orientations or any(
        orientation not in {"forward", "reverse"} for orientation in normalized_orientations
    ):
        raise ValueError("orientations must contain forward and/or reverse")

    components: dict[str, OrientationScore] = {}
    for orientation in normalized_orientations:
        ref_score, alt_score, delta = scorer.score_variant(
            ref_window, variant, strand=orientation
        )
        if abs(delta - (alt_score - ref_score)) > 1e-9:
            raise ValueError(f"scorer returned inconsistent delta for {orientation}")
        components[orientation] = OrientationScore(
            reference_score=float(ref_score),
            alternate_score=float(alt_score),
            delta=float(delta),
        )

    return OrientationScorePair(
        forward=components.get("forward"),
        reverse=components.get("reverse"),
    )
