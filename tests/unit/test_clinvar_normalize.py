"""Tests for clinvar_normalize.py — Milestones 26-28."""

from __future__ import annotations

from evovariant_tr.clinvar_normalize import (
    SNV_TYPE,
    classify_variant,
    is_definitive_at_t1,
    is_eligible_for_temporal_cohort,
    is_germline_normalized,
    is_vus_at_t0,
    normalize_origin_simple,
)
from evovariant_tr.clinvar_parser import (
    ClinicalSignificance,
    VariantSummaryRecord,
)


def _make_record(
    clinical_significance: ClinicalSignificance = ClinicalSignificance.UNCERTAIN_SIGNIFICANCE,
    variant_type: str = "SNV",
    assembly: str = "GRCh38",
    chromosome: str = "7",
    start: int = 100,
    stop: int = 100,
    reference_allele: str = "A",
    alternate_allele: str = "T",
    review_stars: int = 2,
    origin_simple: str = "germline",
    **kwargs,
) -> VariantSummaryRecord:
    return VariantSummaryRecord(
        allele_id=kwargs.get("allele_id", 1),
        variant_type=variant_type,
        clinical_significance=clinical_significance,
        review_status=kwargs.get("review_status", "test"),
        review_stars=review_stars,
        assembly=assembly,
        chromosome=chromosome,
        start=start,
        stop=stop,
        reference_allele=reference_allele,
        alternate_allele=alternate_allele,
        variation_id=kwargs.get("variation_id", 1),
        rcv_accessions=kwargs.get("rcv_accessions", []),
        origin_simple=origin_simple,
        germline="germline" in origin_simple.lower(),
        gene_symbol=kwargs.get("gene_symbol"),
        rs_id=kwargs.get("rs_id"),
        last_evaluated=kwargs.get("last_evaluated"),
        name=kwargs.get("name"),
        row_number=kwargs.get("row_number", 0),
        raw_clinical_significance=kwargs.get("raw_clinical_significance", ""),
        raw_review_status=kwargs.get("raw_review_status", ""),
    )


# --------------------------------------------------------------------------- #
# M26: Germline classification normalization
# --------------------------------------------------------------------------- #


def test_normalize_origin_simple():
    assert normalize_origin_simple("germline") == "germline"
    assert normalize_origin_simple("GERMLINE") == "germline"
    assert normalize_origin_simple("germline;unknown") == "germline;unknown"
    assert normalize_origin_simple("-") == ""
    assert normalize_origin_simple("") == ""


def test_is_germline_normalized():
    assert is_germline_normalized("germline") is True
    assert is_germline_normalized("germline;unknown") is True
    assert is_germline_normalized("somatic") is False
    assert is_germline_normalized("") is False


def test_classify_variant_pathogenic():
    record = _make_record(clinical_significance=ClinicalSignificance.PATHOGENIC)
    assert classify_variant(record) == "pathogenic"


def test_classify_variant_likely_pathogenic():
    record = _make_record(
        clinical_significance=ClinicalSignificance.LIKELY_PATHOGENIC
    )
    assert classify_variant(record) == "pathogenic"


def test_classify_variant_benign():
    record = _make_record(
        clinical_significance=ClinicalSignificance.BENIGN
    )
    assert classify_variant(record) == "benign"


def test_classify_variant_vus():
    record = _make_record()
    assert classify_variant(record) == "vus"


def test_classify_variant_somatic_excluded():
    record = _make_record(origin_simple="somatic")
    assert classify_variant(record) is None


def test_classify_variant_non_snv_excluded():
    record = _make_record(variant_type="Indel")
    assert classify_variant(record) is None


def test_classify_variant_conflicting():
    record = _make_record(
        clinical_significance=ClinicalSignificance.CONFLICTING
    )
    assert classify_variant(record) == "conflicting"


# --------------------------------------------------------------------------- #
# M27: Review-status to star normalization (tested via review_status_to_stars)
# --------------------------------------------------------------------------- #


def test_review_stars_via_eligibility():
    record = _make_record(review_stars=1)
    assert is_eligible_for_temporal_cohort(record, min_review_stars=2) is False

    record2 = _make_record(review_stars=2)
    assert is_eligible_for_temporal_cohort(record2, min_review_stars=2) is True

    record3 = _make_record(review_stars=3)
    assert is_eligible_for_temporal_cohort(record3, min_review_stars=2) is True


# --------------------------------------------------------------------------- #
# M28: Coordinate and allele normalization
# --------------------------------------------------------------------------- #


def test_eligible_valid_record():
    record = _make_record()
    assert is_eligible_for_temporal_cohort(record) is True


def test_eligible_excludes_somatic():
    record = _make_record(origin_simple="somatic")
    assert is_eligible_for_temporal_cohort(record) is False


def test_eligible_excludes_non_snv():
    record = _make_record(variant_type="Deletion")
    assert is_eligible_for_temporal_cohort(record) is False


def test_eligible_excludes_grch37():
    record = _make_record(assembly="GRCh37")
    assert is_eligible_for_temporal_cohort(record) is False


def test_eligible_excludes_missing_coordinates():
    record = _make_record(start=0, stop=100)
    assert is_eligible_for_temporal_cohort(record) is False


def test_eligible_excludes_missing_chromosome():
    record = _make_record(chromosome="-")
    assert is_eligible_for_temporal_cohort(record) is False


def test_eligible_excludes_ref_eq_alt():
    record = _make_record(reference_allele="A", alternate_allele="A")
    assert is_eligible_for_temporal_cohort(record) is False


def test_eligible_excludes_missing_alleles():
    record = _make_record(reference_allele="-", alternate_allele="T")
    assert is_eligible_for_temporal_cohort(record) is False


def test_eligible_excludes_low_review_stars():
    record = _make_record(review_stars=0)
    assert is_eligible_for_temporal_cohort(record) is False


# --------------------------------------------------------------------------- #
# M29: Temporal joining helpers
# --------------------------------------------------------------------------- #


def test_is_vus_at_t0():
    record = _make_record(
        clinical_significance=ClinicalSignificance.UNCERTAIN_SIGNIFICANCE,
        review_stars=2,
    )
    assert is_vus_at_t0(record) is True


def test_is_vus_at_t0_excludes_low_stars():
    record = _make_record(
        clinical_significance=ClinicalSignificance.UNCERTAIN_SIGNIFICANCE,
        review_stars=1,
    )
    assert is_vus_at_t0(record, min_review_stars=2) is False


def test_is_vus_at_t0_excludes_pathogenic():
    record = _make_record(
        clinical_significance=ClinicalSignificance.PATHOGENIC,
        review_stars=3,
    )
    assert is_vus_at_t0(record) is False


def test_is_definitive_at_t1_pathogenic():
    record = _make_record(
        clinical_significance=ClinicalSignificance.LIKELY_PATHOGENIC,
    )
    assert is_definitive_at_t1(record) == "pathogenic"


def test_is_definitive_at_t1_benign():
    record = _make_record(
        clinical_significance=ClinicalSignificance.LIKELY_BENIGN,
    )
    assert is_definitive_at_t1(record) == "benign"


def test_is_definitive_at_t1_vus_returns_none():
    record = _make_record()
    assert is_definitive_at_t1(record) is None


def test_is_definitive_at_t1_conflicting_returns_none():
    record = _make_record(
        clinical_significance=ClinicalSignificance.CONFLICTING,
    )
    assert is_definitive_at_t1(record) is None


def test_snv_type_constant():
    assert SNV_TYPE == "single nucleotide variant"
