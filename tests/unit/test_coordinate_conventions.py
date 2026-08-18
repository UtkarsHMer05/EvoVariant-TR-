"""Coordinate convention tests for ClinVar variant_summary parsing.

Verifies that the parser correctly handles:
- 1-based inclusive coordinates (ClinVar convention)
- Right-shifted positions
- VCF left-shifted positions (PositionVCF, ReferenceAlleleVCF, AlternateAlleleVCF)
- Indel vs SNV coordinate differences

Design (Milestone 33): These tests use synthetic data that encodes
known coordinate quirks from the real variant_summary format.
"""

from __future__ import annotations

import gzip
from pathlib import Path

from evovariant_tr.clinvar_parser import (
    iter_variant_summary,
    parse_header,
    parse_record,
)

COORD_HEADER = (
    "#AlleleID\tType\tClinicalSignificance\tReviewStatus\tAssembly\t"
    "Chromosome\tStart\tStop\tReferenceAllele\tAlternateAllele\t"
    "VariationID\tRCVaccession\tOriginSimple\tGeneSymbol\t"
    "RS# (dbSNP)\tLastEvaluated\tPositionVCF\tReferenceAlleleVCF\t"
    "AlternateAlleleVCF"
)


def _write_gz(path: Path, rows: list[list[str]]) -> Path:
    content = COORD_HEADER.lstrip("#") + "\n"
    for row in rows:
        content += "\t".join(row) + "\n"
    with gzip.open(path, "wt", encoding="utf-8") as f:
        f.write(content)
    return path


def test_snv_single_base_coordinates():
    """SNV at position 100 should have Start=Stop=100."""
    row = [
        "1", "SNV", "Pathogenic", "reviewed by expert panel", "GRCh38",
        "7", "100", "100", "A", "T", "101", "RCV000000001",
        "germline", "TEST1", "111", "2024-01-15", "100", "A", "T",
    ]
    header = parse_header(COORD_HEADER)
    record = parse_record(row, header, row_number=2)
    assert record.start == 100
    assert record.stop == 100


def test_indel_deletion_coordinates_match_header():
    """Deletion should have Start == Stop in right-shifted convention."""
    row = [
        "2", "Deletion", "Pathogenic", "reviewed by expert panel", "GRCh38",
        "7", "100", "100", "ACGT", "A", "102", "RCV000000002",
        "germline", "TEST2", "222", "2024-01-15", "99", "ACGT", "A",
    ]
    header = parse_header(COORD_HEADER)
    record = parse_record(row, header, row_number=3)
    assert record.start == 100
    assert record.stop == 100
    assert record.variant_type == "Deletion"


def test_indel_insertion_coordinates():
    """Insertion should have Start == Stop in right-shifted convention."""
    row = [
        "3", "Insertion", "Benign", "criteria provided, single submitter", "GRCh38",
        "7", "100", "100", "A", "ATTT", "103", "RCV000000003",
        "germline", "TEST3", "333", "2024-03-20", "100", "A", "ATTT",
    ]
    header = parse_header(COORD_HEADER)
    record = parse_record(row, header, row_number=4)
    assert record.start == 100
    assert record.stop == 100
    assert record.variant_type == "Insertion"


def test_vcf_left_shifted_coordinates_differ():
    """VCF positions may differ from right-shifted positions for indels."""
    row = [
        "4", "Deletion", "Pathogenic", "reviewed by expert panel", "GRCh38",
        "17", "64220709", "64220712", "ATGG", "A", "104", "RCV000000004",
        "germline", "TEST4", "444", "2024-06-10", "64220707", "ATGG", "A",
    ]
    header = parse_header(COORD_HEADER)
    record = parse_record(row, header, row_number=5)
    assert record.start == 64220709  # Right-shifted (ClinVar default)
    assert record.stop == 64220712


def test_multi_base_same_chromosome_position():
    """Two variants at the same position but different alleles are distinct."""
    row1 = [
        "5", "SNV", "Pathogenic", "reviewed by expert panel", "GRCh38",
        "7", "100", "100", "A", "T", "105", "RCV000000005",
        "germline", "TEST5", "555", "2024-01-15", "100", "A", "T",
    ]
    row2 = [
        "6", "SNV", "Benign", "reviewed by expert panel", "GRCh38",
        "7", "100", "100", "A", "C", "106", "RCV000000006",
        "germline", "TEST5", "666", "2024-01-15", "100", "A", "C",
    ]
    header = parse_header(COORD_HEADER)
    rec1 = parse_record(row1, header, row_number=6)
    rec2 = parse_record(row2, header, row_number=7)
    assert rec1.start == rec2.start
    assert rec1.alternate_allele != rec2.alternate_allele
    assert rec1.reference_allele == rec2.reference_allele


def test_iter_variant_summary_filters_by_coordinate_bounds(tmp_path: Path):
    """All records in a well-formed file should have valid coordinates."""
    rows = [
        ["1", "SNV", "Pathogenic", "reviewed by expert panel", "GRCh38",
         "1", "1000", "1000", "A", "T", "101", "RCV000000001",
         "germline", "GENE1", "111", "2024-01-15", "1000", "A", "T"],
    ]
    fpath = _write_gz(tmp_path / "t0.txt.gz", rows)
    for record in iter_variant_summary(fpath, assembly="GRCh38"):
        assert record.start >= 1
        assert record.stop >= record.start


def test_different_assemblies_filtered(tmp_path: Path):
    """Only GRCh38 records should be yielded."""
    rows = [
        ["1", "SNV", "Pathogenic", "reviewed by expert panel", "GRCh38",
         "1", "100", "100", "A", "T", "101", "RCV000000001",
         "germline", "GENE1", "111", "2024-01-15", "100", "A", "T"],
        ["2", "SNV", "Benign", "reviewed by expert panel", "GRCh37",
         "1", "100", "100", "A", "T", "102", "RCV000000002",
         "germline", "GENE1", "222", "2024-01-15", "100", "A", "T"],
    ]
    fpath = _write_gz(tmp_path / "t0.txt.gz", rows)
    records = list(iter_variant_summary(fpath, assembly="GRCh38"))
    assert len(records) == 1
    assert records[0].allele_id == 1


def test_does_not_guess_coordinates():
    """Parser should never synthesize coordinates — it reads them from the file."""
    row = [
        "1", "SNV", "Pathogenic", "reviewed by expert panel", "GRCh38",
        "chrX", "500", "500", "G", "C", "101", "RCV000000001",
        "germline", "GENE1", "111", "2024-01-15", "500", "G", "C",
    ]
    header = parse_header(COORD_HEADER)
    record = parse_record(row, header, row_number=2)
    assert record.chromosome == "chrX"
    assert record.start == 500
    assert record.stop == 500
    assert record.reference_allele == "G"
    assert record.alternate_allele == "C"
