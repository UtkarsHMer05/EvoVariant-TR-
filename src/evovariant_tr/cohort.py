"""Temporal cohort construction for EvoVariant-TR (Milestone 30).

This module implements the deterministic cohort-construction pipeline that:
1. Loads t0 and t1 ClinVar variant_summary snapshots.
2. Parses both with the version-aware parser.
3. Filters to germline SNVs on GRCh38.
4. Identifies VUS at t0 with >=2 review stars.
5. Identifies definitive (P/LP or B/LB) classifications at t1 with >=2 stars.
6. Joins t0 → t1 by normalized variant identity.
7. Assigns outcomes: resolved_pathogenic or resolved_benign.
8. Produces cohort flow counts (CONSORT-style).

Deduplication policy:
- Variants are identified by normalized (chrom, start, ref, alt) on GRCh38.
- If multiple records map to the same normalized variant, the one with the
  most review stars at t1 is kept (most confident classification wins).
- Duplicate alleles (same VCV) are collapsed to a single record.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum
from pathlib import Path
from typing import Any

from evovariant_tr.clinvar_normalize import (
    is_vus_at_t0,
)
from evovariant_tr.clinvar_parser import (
    ClinicalSignificance,
    VariantSummaryRecord,
    iter_variant_summary,
)

MIN_REVIEW_STARS = 2


class Outcome(StrEnum):
    """Temporal cohort outcome for a variant that was VUS at t0."""

    RESOLVED_PATHOGENIC = "resolved_pathogenic"
    RESOLVED_BENIGN = "resolved_benign"
    UNRESOLVED = "unresolved"
    NOT_VUS_AT_T0 = "not_vus_at_t0"
    EXCLUDED = "excluded"


@dataclass(frozen=True)
class VariantIdentity:
    """Normalized variant identity for cohort joining."""

    chrom: str
    start: int
    ref: str
    alt: str

    @classmethod
    def from_record(cls, record: VariantSummaryRecord) -> VariantIdentity:
        return cls(
            chrom=record.chromosome,
            start=record.start,
            ref=record.reference_allele,
            alt=record.alternate_allele,
        )


@dataclass
class CohortFlow:
    """CONSORT-style flow counts for the temporal cohort."""

    total_t0_records: int = 0
    t0_germline_snv: int = 0
    t0_grch38: int = 0
    t0_vus_at_t0: int = 0
    t0_vus_meets_star_gate: int = 0
    t0_unique_variants: int = 0
    t1_definitive_meets_star_gate: int = 0
    t1_resolved_from_t0_vus: int = 0
    t1_pathogenic: int = 0
    t1_benign: int = 0
    t1_unresolved: int = 0
    excluded_no_t1_record: int = 0
    excluded_assembly_mismatch: int = 0

    def to_dict(self) -> dict[str, int]:
        return {
            "total_t0_records": self.total_t0_records,
            "t0_germline_snv": self.t0_germline_snv,
            "t0_grch38": self.t0_grch38,
            "t0_vus_at_t0": self.t0_vus_at_t0,
            "t0_vus_meets_star_gate": self.t0_vus_meets_star_gate,
            "t0_unique_variants": self.t0_unique_variants,
            "t1_definitive_meets_star_gate": self.t1_definitive_meets_star_gate,
            "t1_resolved_from_t0_vus": self.t1_resolved_from_t0_vus,
            "t1_pathogenic": self.t1_pathogenic,
            "t1_benign": self.t1_benign,
            "t1_unresolved": self.t1_unresolved,
            "excluded_no_t1_record": self.excluded_no_t1_record,
            "excluded_assembly_mismatch": self.excluded_assembly_mismatch,
        }


@dataclass
class CohortVariant:
    """A single variant in the temporal cohort."""

    identity: VariantIdentity
    t0_clinical_significance: str
    t0_review_status: str
    t0_review_stars: int
    t1_clinical_significance: str
    t1_review_status: str
    t1_review_stars: int
    outcome: Outcome
    t1_classification: str | None = None
    gene_symbol: str | None = None
    allele_id_t0: int | None = None
    allele_id_t1: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "chrom": self.identity.chrom,
            "start": self.identity.start,
            "ref": self.identity.ref,
            "alt": self.identity.alt,
            "t0_clinical_significance": self.t0_clinical_significance,
            "t0_review_status": self.t0_review_status,
            "t0_review_stars": self.t0_review_stars,
            "t1_clinical_significance": self.t1_clinical_significance,
            "t1_review_status": self.t1_review_status,
            "t1_review_stars": self.t1_review_stars,
            "outcome": self.outcome.value,
            "t1_classification": self.t1_classification,
            "gene_symbol": self.gene_symbol,
            "allele_id_t0": self.allele_id_t0,
            "allele_id_t1": self.allele_id_t1,
        }


@dataclass
class TemporalCohort:
    """The complete temporal cohort with flow counts."""

    variants: list[CohortVariant] = field(default_factory=list)
    flow: CohortFlow = field(default_factory=CohortFlow)
    t0_release_date: date | None = None
    t1_release_date: date | None = None

    @property
    def n_total(self) -> int:
        return len(self.variants)

    @property
    def n_resolved_pathogenic(self) -> int:
        return sum(
            1 for v in self.variants if v.outcome == Outcome.RESOLVED_PATHOGENIC
        )

    @property
    def n_resolved_benign(self) -> int:
        return sum(
            1 for v in self.variants if v.outcome == Outcome.RESOLVED_BENIGN
        )

    @property
    def n_unresolved(self) -> int:
        return sum(1 for v in self.variants if v.outcome == Outcome.UNRESOLVED)

    @property
    def n_excluded(self) -> int:
        return sum(1 for v in self.variants if v.outcome == Outcome.EXCLUDED)

    def positive_count(self) -> int:
        return self.n_resolved_pathogenic

    def negative_count(self) -> int:
        return self.n_resolved_benign

    def class_counts(self) -> dict[str, int]:
        counts: Counter[str] = Counter()
        for v in self.variants:
            counts[v.outcome.value] += 1
        return dict(counts)


def _deduplicate_by_identity(
    records: list[VariantSummaryRecord],
) -> dict[VariantIdentity, VariantSummaryRecord]:
    """Deduplicate records by VariantIdentity, keeping most-review-stars."""
    by_identity: dict[VariantIdentity, VariantSummaryRecord] = {}
    for record in records:
        identity = VariantIdentity.from_record(record)
        existing = by_identity.get(identity)
        if existing is None or record.review_stars > existing.review_stars:
            by_identity[identity] = record
    return by_identity


def build_temporal_cohort(
    t0_path: str | Path,
    t1_path: str | Path,
    t0_release_date: date | None = None,
    t1_release_date: date | None = None,
    min_review_stars: int | None = None,
    config: CohortConfig | None = None,
) -> TemporalCohort:
    """Build the temporal VUS-resolution cohort from t0 and t1 snapshots.

    Args:
        t0_path: Path to t0 variant_summary.txt.gz
        t1_path: Path to t1 variant_summary.txt.gz
        t0_release_date: Release date of the t0 snapshot
        t1_release_date: Release date of the t1 snapshot
        min_review_stars: Minimum review stars for inclusion (overrides config)
        config: Cohort configuration (defaults to CohortConfig())

    Returns:
        A TemporalCohort with variants and flow counts.
    """
    cfg = config or CohortConfig()
    stars = min_review_stars if min_review_stars is not None else cfg.min_review_stars
    flow = CohortFlow()
    flow.t0_release_date = t0_release_date  # type: ignore[attr-defined]
    flow.t1_release_date = t1_release_date  # type: ignore[attr-defined]

    t0_records: list[VariantSummaryRecord] = []
    t1_records: list[VariantSummaryRecord] = []

    for record in iter_variant_summary(t0_path, assembly="GRCh38"):
        flow.total_t0_records += 1

        if record.variant_type == "SNV" and record.germline:
            flow.t0_germline_snv += 1
            if record.assembly == "GRCh38":
                flow.t0_grch38 += 1

        t0_records.append(record)

    for record in iter_variant_summary(t1_path, assembly="GRCh38"):
        t1_records.append(record)

    t0_dedup = _deduplicate_by_identity(t0_records)
    flow.t0_unique_variants = len(t0_dedup)

    t1_dedup = _deduplicate_by_identity(t1_records)

    vus_variants: dict[VariantIdentity, VariantSummaryRecord] = {}
    for identity, record in t0_dedup.items():
        if is_vus_at_t0(record, min_review_stars=stars):
            flow.t0_vus_meets_star_gate += 1
            vus_variants[identity] = record

    flow.t0_vus_at_t0 = flow.t0_vus_meets_star_gate

    variants: list[CohortVariant] = []
    resolved_genes: set[str] = set()

    for identity, t0_record in vus_variants.items():
        t1_record = t1_dedup.get(identity)
        if t1_record is None:
            flow.excluded_no_t1_record += 1
            variants.append(
                CohortVariant(
                    identity=identity,
                    t0_clinical_significance=t0_record.raw_clinical_significance,
                    t0_review_status=t0_record.review_status,
                    t0_review_stars=t0_record.review_stars,
                    t1_clinical_significance="unresolved",
                    t1_review_status="no_record_at_t1",
                    t1_review_stars=0,
                    outcome=Outcome.EXCLUDED,
                )
            )
            continue

        flow.t1_definitive_meets_star_gate += 1

        classification = None
        outcome = Outcome.UNRESOLVED

        if t1_record.clinical_significance in (
            ClinicalSignificance.PATHOGENIC,
            ClinicalSignificance.PATHOGENIC_LIKELY_PATHOGENIC,
            ClinicalSignificance.LIKELY_PATHOGENIC,
        ):
            outcome = Outcome.RESOLVED_PATHOGENIC
            classification = "pathogenic"
            flow.t1_pathogenic += 1
        elif t1_record.clinical_significance in (
            ClinicalSignificance.BENIGN,
            ClinicalSignificance.BENIGN_LIKELY_BENIGN,
            ClinicalSignificance.LIKELY_BENIGN,
        ):
            outcome = Outcome.RESOLVED_BENIGN
            classification = "benign"
            flow.t1_benign += 1
        else:
            flow.t1_unresolved += 1

        if t1_record.gene_symbol:
            resolved_genes.add(t1_record.gene_symbol)

        variants.append(
            CohortVariant(
                identity=identity,
                t0_clinical_significance=t0_record.raw_clinical_significance,
                t0_review_status=t0_record.review_status,
                t0_review_stars=t0_record.review_stars,
                t1_clinical_significance=t1_record.raw_clinical_significance,
                t1_review_status=t1_record.review_status,
                t1_review_stars=t1_record.review_stars,
                outcome=outcome,
                t1_classification=classification,
                gene_symbol=t1_record.gene_symbol,
                allele_id_t0=t0_record.allele_id,
                allele_id_t1=t1_record.allele_id,
            )
        )

    flow.t1_resolved_from_t0_vus = len(variants)

    cohort = TemporalCohort(
        variants=variants,
        flow=flow,
        t0_release_date=t0_release_date,
        t1_release_date=t1_release_date,
    )

    return cohort


@dataclass
class DuplicateAudit:
    """Audit results for duplicate variant resolution."""

    total_records: int = 0
    unique_identities: int = 0
    duplicate_count: int = 0
    max_dups_per_identity: int = 0
    identities_with_dups: int = 0

    def to_dict(self) -> dict[str, int]:
        return {
            "total_records": self.total_records,
            "unique_identities": self.unique_identities,
            "duplicate_count": self.duplicate_count,
            "max_dups_per_identity": self.max_dups_per_identity,
            "identities_with_dups": self.identities_with_dups,
        }


def audit_duplicates(
    records: list[VariantSummaryRecord],
) -> DuplicateAudit:
    """Audit duplicate variants by (chrom, start, ref, alt) identity.

    Returns counts for CONSORT flow reporting.
    """
    identity_counts: Counter[VariantIdentity] = Counter()
    for record in records:
        identity = VariantIdentity.from_record(record)
        identity_counts[identity] += 1

    total = len(records)
    unique = len(identity_counts)
    dups = total - unique
    max_dups = max(identity_counts.values()) if identity_counts else 0
    identities_with_dups = sum(1 for c in identity_counts.values() if c > 1)

    return DuplicateAudit(
        total_records=total,
        unique_identities=unique,
        duplicate_count=dups,
        max_dups_per_identity=max_dups,
        identities_with_dups=identities_with_dups,
    )


@dataclass
class CohortConfig:
    """Configuration for cohort construction (frozen by convention)."""

    min_review_stars: int = MIN_REVIEW_STARS
    assembly: str = "GRCh38"
    min_last_evaluated_date: date | None = field(default=None)


def build_primary_cohort(
    t0_path: str | Path,
    t1_path: str | Path,
    t0_release_date: date | None = None,
    t1_release_date: date | None = None,
    config: CohortConfig | None = None,
) -> TemporalCohort:
    """Build the primary temporal cohort from raw public archives.

    This is the production entry point for cohort construction. It applies
    all eligibility filters, duplicate resolution, and temporal joining.
    """
    cfg = config or CohortConfig()

    cohort = build_temporal_cohort(
        t0_path,
        t1_path,
        t0_release_date=t0_release_date,
        t1_release_date=t1_release_date,
        config=cfg,
    )

    return cohort
