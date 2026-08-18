"""Germline classification normalization for ClinVar variant_summary.

This module provides normalization functions for the ClinVar
variant_summary ClinicalSignificance and Origin fields, implementing the
frozen protocol's inclusion criteria:

- Germline-only variants (OriginSimple contains "germline").
- SNV-only variants (Type == "SNV").
- Valid GRCh38 coordinates with matching reference allele.
"""

from __future__ import annotations

from evovariant_tr.clinvar_parser import (
    ClinicalSignificance,
    VariantSummaryRecord,
)

GERMLINE_ORIGINS = frozenset(
    {
        "germline",
        "germline;unknown",
        "inherited",
        "inherited;unknown",
    }
)

SNV_TYPE = "SNV"


def normalize_origin_simple(raw: str) -> str:
    """Normalize the OriginSimple field.

    ClinVar OriginSimple can be: "germline", "somatic", "inherited",
    "de novo", "unknown", or combinations like "germline;unknown".
    """
    if not raw or raw == "-":
        return ""
    return raw.strip().lower()


def is_germline_normalized(origin_simple: str) -> bool:
    """Check if a normalized OriginSimple indicates germline origin."""
    if not origin_simple:
        return False
    origins = [o.strip() for o in origin_simple.split(";") if o.strip()]
    return any(o in GERMLINE_ORIGINS for o in origins)


def classify_variant(record: VariantSummaryRecord) -> str | None:
    """Classify a variant record into a protocol outcome category.

    Returns:
        "pathogenic" / "benign" / "vus" / "conflicting" / "other" / None (excluded)
    """
    if not record.germline:
        return None
    if record.variant_type != SNV_TYPE:
        return None

    clinsig = record.clinical_significance
    if clinsig in (
        ClinicalSignificance.PATHOGENIC,
        ClinicalSignificance.PATHOGENIC_LIKELY_PATHOGENIC,
        ClinicalSignificance.LIKELY_PATHOGENIC,
    ):
        return "pathogenic"
    if clinsig in (
        ClinicalSignificance.BENIGN,
        ClinicalSignificance.BENIGN_LIKELY_BENIGN,
        ClinicalSignificance.LIKELY_BENIGN,
    ):
        return "benign"
    if clinsig == ClinicalSignificance.UNCERTAIN_SIGNIFICANCE:
        return "vus"
    if clinsig == ClinicalSignificance.CONFLICTING:
        return "conflicting"
    return "other"


def is_eligible_for_temporal_cohort(
    record: VariantSummaryRecord,
    min_review_stars: int = 2,
) -> bool:
    """Check if a record meets basic eligibility for the temporal cohort.

    Eligibility: germline SNV with a valid GRCh38 coordinate, valid alleles,
    and at least the minimum review stars.
    """
    if not record.germline:
        return False
    if record.variant_type != SNV_TYPE:
        return False
    if record.assembly != "GRCh38":
        return False
    if not record.chromosome or record.chromosome == "-":
        return False
    if record.start <= 0 or record.stop <= 0:
        return False
    if not record.reference_allele or record.reference_allele == "-":
        return False
    if not record.alternate_allele or record.alternate_allele == "-":
        return False
    if record.reference_allele == record.alternate_allele:
        return False
    if record.review_stars < min_review_stars:
        return False
    return True


def is_vus_at_t0(record: VariantSummaryRecord, min_review_stars: int = 2) -> bool:
    """Check if a record is VUS at the t0 snapshot."""
    return (
        record.clinical_significance == ClinicalSignificance.UNCERTAIN_SIGNIFICANCE
        and record.review_stars >= min_review_stars
    )


def is_definitive_at_t1(record: VariantSummaryRecord) -> str | None:
    """Check if a record is definitively classified at t1.

    Returns "pathogenic", "benign", or None (not definitive).
    """
    clinsig = record.clinical_significance
    if clinsig in (
        ClinicalSignificance.PATHOGENIC,
        ClinicalSignificance.PATHOGENIC_LIKELY_PATHOGENIC,
        ClinicalSignificance.LIKELY_PATHOGENIC,
    ):
        return "pathogenic"
    if clinsig in (
        ClinicalSignificance.BENIGN,
        ClinicalSignificance.BENIGN_LIKELY_BENIGN,
        ClinicalSignificance.LIKELY_BENIGN,
    ):
        return "benign"
    return None
