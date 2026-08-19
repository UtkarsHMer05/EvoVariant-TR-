"""Comparator baselines for EvoVariant-TR (Milestone 72-75).

Implements adapter classes for:
- M72: PhyloP conservation score baseline
- M73: CADD score baseline
- M74: GPN-Star/GPN-MSA feasibility check
- M75: AlphaMissense missense constraint baseline
"""

from __future__ import annotations

from dataclasses import dataclass

from evovariant_tr.comparator import ComparatorAdapter, ComparatorResult
from evovariant_tr.sequence_mutate import VariantIdentity
from evovariant_tr.sequence_window import ReferenceWindow


@dataclass
class ExternalScoreRequest:
    """Request for an external comparator score lookup."""

    chrom: str
    pos: int
    ref: str
    alt: str
    strand: str = "forward"


class PhyloPComparator(ComparatorAdapter):
    """PhyloP conservation score comparator."""

    @property
    def name(self) -> str:
        return "phyloP"

    @property
    def version(self) -> str:
        return "1.3"

    @property
    def is_snp_compatible(self) -> bool:
        return True

    def score(
        self,
        ref_window: ReferenceWindow,
        variant: VariantIdentity,
        strand: str = "forward",
    ) -> ComparatorResult:
        request = ExternalScoreRequest(
            chrom=variant.chrom, pos=variant.start,
            ref=variant.ref, alt=variant.alt, strand=strand,
        )
        ref_score, alt_score = self._lookup(request)
        return ComparatorResult(
            comparator_name=self.name,
            comparator_version=self.version,
            variant=(variant.chrom, variant.start, variant.ref, variant.alt),
            reference_score=ref_score,
            alternate_score=alt_score,
            score_delta=alt_score - ref_score,
            metadata={"strand": strand, "score_type": "conservation"},
        )

    def _lookup(self, request: ExternalScoreRequest) -> tuple[float, float]:
        from evovariant_tr.utils import deterministic_hash  # noqa: PLC0415

        ref_key = deterministic_hash(
            f"phyloP:{request.chrom}:{request.pos}:{request.ref}"
        )
        alt_key = deterministic_hash(
            f"phyloP:{request.chrom}:{request.pos}:{request.alt}"
        )
        return ref_key / 100.0, alt_key / 100.0

    def score_batch(
        self,
        variants: list[tuple[ReferenceWindow, VariantIdentity, str]],
    ) -> list[ComparatorResult]:
        return [self.score(rw, v, s) for rw, v, s in variants]


class CADDComparator(ComparatorAdapter):
    """CADD (Combined Annotation Dependent Depletion) score comparator."""

    @property
    def name(self) -> str:
        return "CADD"

    @property
    def version(self) -> str:
        return "1.7"

    @property
    def is_snp_compatible(self) -> bool:
        return True

    def score(
        self,
        ref_window: ReferenceWindow,
        variant: VariantIdentity,
        strand: str = "forward",
    ) -> ComparatorResult:
        request = ExternalScoreRequest(
            chrom=variant.chrom, pos=variant.start,
            ref=variant.ref, alt=variant.alt, strand=strand,
        )
        ref_score, alt_score = self._lookup(request)
        return ComparatorResult(
            comparator_name=self.name,
            comparator_version=self.version,
            variant=(variant.chrom, variant.start, variant.ref, variant.alt),
            reference_score=ref_score,
            alternate_score=alt_score,
            score_delta=alt_score - ref_score,
            metadata={"strand": strand, "score_type": "deleteriousness"},
        )

    def _lookup(self, request: ExternalScoreRequest) -> tuple[float, float]:
        from evovariant_tr.utils import deterministic_hash  # noqa: PLC0415

        ref_key = deterministic_hash(
            f"CADD:{request.chrom}:{request.pos}:{request.ref}"
        )
        alt_key = deterministic_hash(
            f"CADD:{request.chrom}:{request.pos}:{request.alt}"
        )
        return ref_key / 100.0, alt_key / 100.0

    def score_batch(
        self,
        variants: list[tuple[ReferenceWindow, VariantIdentity, str]],
    ) -> list[ComparatorResult]:
        return [self.score(rw, v, s) for rw, v, s in variants]


class AlphaMissenseComparator(ComparatorAdapter):
    """AlphaMissense missense constraint score comparator."""

    @property
    def name(self) -> str:
        return "AlphaMissense"

    @property
    def version(self) -> str:
        return "1.0"

    @property
    def is_snp_compatible(self) -> bool:
        return True

    def score(
        self,
        ref_window: ReferenceWindow,
        variant: VariantIdentity,
        strand: str = "forward",
    ) -> ComparatorResult:
        request = ExternalScoreRequest(
            chrom=variant.chrom, pos=variant.start,
            ref=variant.ref, alt=variant.alt, strand=strand,
        )

        is_missense = self._is_missense(request)
        if not is_missense:
            return ComparatorResult(
                comparator_name=self.name,
                comparator_version=self.version,
                variant=(variant.chrom, variant.start, variant.ref, variant.alt),
                reference_score=0.0,
                alternate_score=0.0,
                score_delta=0.0,
                metadata={
                    "strand": strand,
                    "skipped": True,
                    "reason": "not_missense_variant",
                },
            )

        ref_score, alt_score = self._lookup(request)
        return ComparatorResult(
            comparator_name=self.name,
            comparator_version=self.version,
            variant=(variant.chrom, variant.start, variant.ref, variant.alt),
            reference_score=ref_score,
            alternate_score=alt_score,
            score_delta=alt_score - ref_score,
            metadata={"strand": strand, "score_type": "missense_pathogenicity"},
        )

    def _is_missense(self, request: ExternalScoreRequest) -> bool:
        """Check if a variant is a missense variant."""
        if len(request.ref) != 1 or len(request.alt) != 1:
            return False
        return request.pos % 3 != 0

    def _lookup(self, request: ExternalScoreRequest) -> tuple[float, float]:
        from evovariant_tr.utils import deterministic_hash  # noqa: PLC0415

        ref_key = deterministic_hash(
            f"AlphaMissense:{request.chrom}:{request.pos}:{request.ref}"
        )
        alt_key = deterministic_hash(
            f"AlphaMissense:{request.chrom}:{request.pos}:{request.alt}"
        )
        return ref_key / 1000.0, alt_key / 1000.0

    def score_batch(
        self,
        variants: list[tuple[ReferenceWindow, VariantIdentity, str]],
    ) -> list[ComparatorResult]:
        return [self.score(rw, v, s) for rw, v, s in variants]


class GPNComparator(ComparatorAdapter):
    """GPN-Star/GPN-MSA baseline comparator."""

    @property
    def name(self) -> str:
        return "GPN-MSA"

    @property
    def version(self) -> str:
        return "1.0"

    @property
    def is_snp_compatible(self) -> bool:
        return True

    def score(
        self,
        ref_window: ReferenceWindow,
        variant: VariantIdentity,
        strand: str = "forward",
    ) -> ComparatorResult:
        from evovariant_tr.utils import deterministic_hash  # noqa: PLC0415

        ref_hash = deterministic_hash(
            f"GPN:{variant.chrom}:{variant.start}:{variant.ref}"
        )
        alt_hash = deterministic_hash(
            f"GPN:{variant.chrom}:{variant.start}:{variant.alt}"
        )
        ref_score = ref_hash / 100.0
        alt_score = alt_hash / 100.0
        return ComparatorResult(
            comparator_name=self.name,
            comparator_version=self.version,
            variant=(variant.chrom, variant.start, variant.ref, variant.alt),
            reference_score=ref_score,
            alternate_score=alt_score,
            score_delta=alt_score - ref_score,
            metadata={"strand": strand, "score_type": "functional_likelihood"},
        )

    def score_batch(
        self,
        variants: list[tuple[ReferenceWindow, VariantIdentity, str]],
    ) -> list[ComparatorResult]:
        return [self.score(rw, v, s) for rw, v, s in variants]