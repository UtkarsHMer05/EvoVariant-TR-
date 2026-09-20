"""Tests for clinvar_parser.py — Milestone 25."""

from __future__ import annotations

import gzip
from datetime import date
from pathlib import Path

import pytest

from evovariant_tr.clinvar_parser import (
    CLINSIG_NORMALIZATION,
    ClinicalSignificance,
    VariantSummaryRecord,
    _parse_int,
    is_germline,
    iter_variant_summary,
    normalize_clinical_significance,
    normalize_review_status,
    parse_date,
    parse_header,
    parse_rcv_accessions,
    parse_record,
    review_status_to_stars,
)

SAMPLE_HEADER = (
    "#AlleleID\tType\tClinicalSignificance\tReviewStatus\tAssembly\t"
    "Chromosome\tStart\tStop\tReferenceAllele\tAlternateAllele\t"
    "VariationID\tRCVaccession\tOriginSimple\tGeneSymbol\t"
    "RS# (dbSNP)\tLastEvaluated"
)

SAMPLE_VUS_ROW = [
    "12345",
    "SNV",
    "Uncertain_significance",
    "criteria provided, single submitter",
    "GRCh38",
    "7",
    "117260530",
    "117260530",
    "A",
    "T",
    "67890",
    "RCV000123456",
    "germline",
    "BRCA1",
    "123456789",
    "2024-01-15",
]

SAMPLE_PATHOGENIC_ROW = [
    "12346",
    "SNV",
    "Pathogenic",
    "reviewed by expert panel",
    "GRCh38",
    "17",
    "7674220",
    "7674220",
    "C",
    "T",
    "67891",
    "RCV000123457|RCV000123458",
    "germline",
    "BRCA2",
    "-",
    "-",
]

SAMPLE_BENIGN_ROW = [
    "12347",
    "SNV",
    "Benign/Likely_benign",
    "criteria provided, multiple submitters",
    "GRCh37",
    "1",
    "1234567",
    "1234567",
    "G",
    "A",
    "67892",
    "",
    "germline",
    "GENE1",
    "987654321",
    "",
]


def test_parse_header_validates_required_columns():
    header = parse_header(SAMPLE_HEADER)
    for col in (
        "AlleleID",
        "Type",
        "ClinicalSignificance",
        "ReviewStatus",
        "Assembly",
        "Chromosome",
        "Start",
        "Stop",
        "ReferenceAllele",
        "AlternateAllele",
        "VariationID",
        "RCVaccession",
        "OriginSimple",
    ):
        assert col in header.columns


def test_parse_header_missing_column_raises():
    bad_header = "#AlleleID\tType\tClinicalSignificance"
    with pytest.raises(ValueError, match="missing required columns"):
        parse_header(bad_header)


def test_parse_record_vus():
    header = parse_header(SAMPLE_HEADER)
    record = parse_record(SAMPLE_VUS_ROW, header, row_number=2)
    assert record.allele_id == 12345
    assert record.variant_type == "SNV"
    assert record.clinical_significance == ClinicalSignificance.UNCERTAIN_SIGNIFICANCE
    assert record.assembly == "GRCh38"
    assert record.chromosome == "7"
    assert record.start == 117260530
    assert record.reference_allele == "A"
    assert record.alternate_allele == "T"
    assert record.germline is True
    assert record.gene_symbol == "BRCA1"
    assert record.rs_id == "123456789"
    assert record.last_evaluated == date(2024, 1, 15)
    assert record.is_vus()
    assert not record.is_pathogenic()
    assert not record.is_benign()


def test_parse_record_pathogenic():
    header = parse_header(SAMPLE_HEADER)
    record = parse_record(SAMPLE_PATHOGENIC_ROW, header, row_number=3)
    assert record.clinical_significance == ClinicalSignificance.PATHOGENIC
    assert record.review_stars == 3
    assert record.is_pathogenic()
    assert len(record.rcv_accessions) == 2
    assert "RCV000123457" in record.rcv_accessions
    assert record.rs_id is None


def test_parse_record_benign():
    header = parse_header(SAMPLE_HEADER)
    record = parse_record(SAMPLE_BENIGN_ROW, header, row_number=4)
    assert record.clinical_significance == ClinicalSignificance.BENIGN_LIKELY_BENIGN
    assert record.review_stars == 2
    assert record.is_benign()
    assert record.last_evaluated is None


def test_parse_record_prefers_vcf_normalized_variant_fields():
    header = parse_header(
        SAMPLE_HEADER + "\tPositionVCF\tReferenceAlleleVCF\tAlternateAlleleVCF"
    )
    fields = SAMPLE_VUS_ROW + ["117260530", "A", "T"]
    fields[7] = "117260531"
    fields[8] = "na"
    fields[9] = "na"
    record = parse_record(fields, header, row_number=2)
    assert record.start == 117260530
    assert record.reference_allele == "A"
    assert record.alternate_allele == "T"


def test_parse_record_invalid_allele_id():
    header = parse_header(SAMPLE_HEADER)
    bad_row = list(SAMPLE_VUS_ROW)
    bad_row[0] = "not_a_number"
    with pytest.raises(ValueError, match="invalid AlleleID"):
        parse_record(bad_row, header, row_number=2)


def test_parse_record_too_few_fields():
    header = parse_header(SAMPLE_HEADER)
    short_row = ["1"]
    with pytest.raises(ValueError, match="expected .* fields"):
        parse_record(short_row, header, row_number=2)


def test_normalize_clinical_significance():
    assert normalize_clinical_significance("Pathogenic") == ClinicalSignificance.PATHOGENIC
    assert normalize_clinical_significance(
        "Uncertain_significance"
    ) == ClinicalSignificance.UNCERTAIN_SIGNIFICANCE
    assert normalize_clinical_significance("") == ClinicalSignificance.NOT_PROVIDED
    assert normalize_clinical_significance("-") == ClinicalSignificance.NOT_PROVIDED
    assert normalize_clinical_significance("weird_value") == ClinicalSignificance.OTHER


def test_normalize_clinical_significance_conflicting():
    assert normalize_clinical_significance(
        "conflicting interpretations"
    ) == ClinicalSignificance.CONFLICTING


def test_normalize_review_status():
    expected = "criteria provided, single submitter"
    assert normalize_review_status(expected) == expected
    assert normalize_review_status("-") == ""
    assert normalize_review_status("") == ""


def test_review_status_to_stars():
    assert review_status_to_stars("criteria provided, single submitter") == 1
    assert review_status_to_stars("reviewed by expert panel") == 3
    assert review_status_to_stars("practice guideline") == 3
    assert review_status_to_stars("no submission") == 0
    assert review_status_to_stars("unknown status") == 0


def test_parse_rcv_accessions():
    assert parse_rcv_accessions("") == []
    assert parse_rcv_accessions("-") == []
    assert parse_rcv_accessions("RCV000000012") == ["RCV000000012"]
    assert parse_rcv_accessions("RCV000000012|RCV000000013") == ["RCV000000012", "RCV000000013"]
    assert parse_rcv_accessions("RCV000000012||RCV000000013") == ["RCV000000012", "RCV000000013"]


def test_parse_date():
    assert parse_date("2024-01-15") == date(2024, 1, 15)
    assert parse_date("-") is None
    assert parse_date("") is None
    assert parse_date("invalid") is None
    assert parse_date("2024-13-45") is None


def test_parse_int():
    assert _parse_int("12345") == 12345
    assert _parse_int("-") is None
    assert _parse_int("") is None
    assert _parse_int("not_a_number") is None


def test_is_germline():
    assert is_germline("germline") is True
    assert is_germline("germline;unknown") is True
    assert is_germline("somatic") is False
    assert is_germline("") is False


def test_clinical_significance_is_pathogenic():
    for sig in (
        ClinicalSignificance.PATHOGENIC,
        ClinicalSignificance.PATHOGENIC_LIKELY_PATHOGENIC,
        ClinicalSignificance.LIKELY_PATHOGENIC,
    ):
        record = VariantSummaryRecord(
            allele_id=1, variant_type="SNV", clinical_significance=sig,
            review_status="test", review_stars=1, assembly="GRCh38",
            chromosome="1", start=100, stop=100, reference_allele="A",
            alternate_allele="T", variation_id=1, rcv_accessions=[],
            origin_simple="germline", germline=True,
        )
        assert record.is_pathogenic()


def test_clinical_significance_is_benign():
    for sig in (
        ClinicalSignificance.BENIGN,
        ClinicalSignificance.BENIGN_LIKELY_BENIGN,
        ClinicalSignificance.LIKELY_BENIGN,
    ):
        record = VariantSummaryRecord(
            allele_id=1, variant_type="SNV", clinical_significance=sig,
            review_status="test", review_stars=1, assembly="GRCh38",
            chromosome="1", start=100, stop=100, reference_allele="A",
            alternate_allele="T", variation_id=1, rcv_accessions=[],
            origin_simple="germline", germline=True,
        )
        assert record.is_benign()


def test_iter_variant_summary_parses_gz(tmp_path: Path):
    """Test streaming parse of a gzipped variant_summary file."""
    content = (
        SAMPLE_HEADER.lstrip("#") + "\n" +
        "\t".join(SAMPLE_VUS_ROW) + "\n" +
        "\t".join(SAMPLE_PATHOGENIC_ROW) + "\n" +
        "\t".join(SAMPLE_BENIGN_ROW) + "\n"
    )
    fpath = tmp_path / "variant_summary.txt.gz"
    with gzip.open(fpath, "wt", encoding="utf-8") as f:
        f.write(content)

    records = list(iter_variant_summary(fpath, assembly="GRCh38"))
    # Only GRCh38 records should pass
    assert len(records) == 2
    assert all(r.assembly == "GRCh38" for r in records)
    assert records[0].allele_id == 12345
    assert records[0].is_vus()
    assert records[1].allele_id == 12346
    assert records[1].is_pathogenic()


def test_clinvar_normalization_keys_present():
    """Verify key normalization mappings exist."""
    assert "Pathogenic" in CLINSIG_NORMALIZATION
    assert "Uncertain_significance" in CLINSIG_NORMALIZATION
    assert "Benign/Likely_benign" in CLINSIG_NORMALIZATION
    assert "Pathogenic/Likely_pathogenic" in CLINSIG_NORMALIZATION


def test_variant_summary_header_idx():
    header = parse_header(SAMPLE_HEADER)
    assert header.idx("AlleleID") == 0
    assert header.idx("VariationID") == 10
    assert header.idx("RCVaccession") == 11
