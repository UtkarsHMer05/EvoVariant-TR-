"""Common comparator adapter contract for EvoVariant-TR (Milestone 71).

Defines a common interface for integrating multiple baseline scorers
(PhyloP, CADD, AlphaMissense, GPN-MSA) alongside Evo 2.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from evovariant_tr.sequence_mutate import VariantIdentity
from evovariant_tr.sequence_window import ReferenceWindow


@dataclass
class ComparatorResult:
    """Result from a single comparator scoring a variant."""

    comparator_name: str
    comparator_version: str
    variant: tuple[str, int, str, str]
    reference_score: float
    alternate_score: float
    score_delta: float
    metadata: dict[str, Any] = field(default_factory=dict)


class ComparatorAdapter(ABC):
    """Abstract adapter for a baseline comparator scorer."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the comparator (e.g., 'PhyloP', 'CADD')."""

    @property
    @abstractmethod
    def version(self) -> str:
        """Version of the comparator."""

    @property
    @abstractmethod
    def is_snp_compatible(self) -> bool:
        """Whether this comparator works on SNVs."""

    @abstractmethod
    def score(
        self,
        ref_window: ReferenceWindow,
        variant: VariantIdentity,
        strand: str = "forward",
    ) -> ComparatorResult:
        """Score a single variant."""

    @abstractmethod
    def score_batch(
        self,
        variants: list[tuple[ReferenceWindow, VariantIdentity, str]],
    ) -> list[ComparatorResult]:
        """Score a batch of variants."""

    def provenance(self) -> dict[str, Any]:
        return {
            "comparator_name": self.name,
            "comparator_version": self.version,
            "is_snp_compatible": self.is_snp_compatible,
        }


@dataclass
class ComparatorSuite:
    """A suite of comparator adapters for paired analysis."""

    scorers: list[ComparatorAdapter] = field(default_factory=list)

    def add(self, adapter: ComparatorAdapter) -> None:
        """Add a comparator to the suite."""
        self.scorers.append(adapter)

    def score_variant(
        self,
        ref_window: ReferenceWindow,
        variant: VariantIdentity,
        strand: str = "forward",
    ) -> list[ComparatorResult]:
        """Score a variant with all comparators in the suite."""
        results = []
        for scorer in self.scorers:
            try:
                result = scorer.score(ref_window, variant, strand)
                results.append(result)
            except Exception as e:
                results.append(ComparatorResult(
                    comparator_name=scorer.name,
                    comparator_version=scorer.version,
                    variant=(variant.chrom, variant.start, variant.ref, variant.alt),
                    reference_score=0.0,
                    alternate_score=0.0,
                    score_delta=0.0,
                    metadata={"error": str(e), "skipped": True},
                ))
        return results

    def list_names(self) -> list[str]:
        return [s.name for s in self.scorers]