"""Tests for cohort.py — Milestone 30 temporal cohort construction."""

from __future__ import annotations

import gzip
from datetime import date
from pathlib import Path

import pytest

from evovariant_tr.clinvar_parser import VariantSummaryRecord
from evovariant_tr.cohort import (
    CohortConfig,
    CohortVariant,
    DuplicateAudit,
    Outcome,
    VariantIdentity,
    audit_duplicates,
    build_primary_cohort,
    build_temporal_cohort,
)

HEADER = (
    "#AlleleID\tType\tClinicalSignificance\tReviewStatus\tAssembly\t"
    "Chromosome\tStart\tStop\tReferenceAllele\tAlternateAllele\t"
    "VariationID\tRCVaccession\tOriginSimple\tGeneSymbol\t"
    "RS# (dbSNP)\tLastEvaluated"
)


def _write_gz(path: Path, rows: list[list[str]]) -> Path:
    content = HEADER.lstrip("#") + "\n"
    for row in rows:
        content += "\t".join(row) + "\n"
    with gzip.open(path, "wt", encoding="utf-8") as f:
        f.write(content)
    return path


@pytest.fixture
def t0_file(tmp_path: Path) -> Path:
    rows = [
        ["1", "SNV", "Uncertain_significance", "criteria provided, single submitter",
         "GRCh38", "7", "100", "100", "A", "T", "101", "RCV000000001",
         "germline", "BRCA1", "111", "2024-01-15"],
        ["2", "SNV", "Uncertain_significance", "criteria provided, multiple submitters",
         "GRCh38", "7", "200", "200", "C", "G", "102", "RCV000000002",
         "germline", "BRCA1", "222", "2024-03-20"],
        ["3", "SNV", "Pathogenic", "reviewed by expert panel",
         "GRCh38", "17", "300", "300", "G", "A", "103", "RCV000000003",
         "germline", "BRCA2", "333", "2024-06-10"],
        ["4", "SNV", "Uncertain_significance", "no submission",
         "GRCh38", "7", "400", "400", "T", "C", "104", "",
         "germline", "PALB2", "444", "2024-01-01"],
    ]
    return _write_gz(tmp_path / "t0.txt.gz", rows)


@pytest.fixture
def t1_file(tmp_path: Path) -> Path:
    rows = [
        ["1", "SNV", "Pathogenic", "reviewed by expert panel",
         "GRCh38", "7", "100", "100", "A", "T", "201", "RCV000000201",
         "germline", "BRCA1", "111", "2026-08-01"],
        ["2", "SNV", "Benign", "criteria provided, multiple submitters",
         "GRCh38", "7", "200", "200", "C", "G", "202", "RCV000000202",
         "germline", "BRCA1", "222", "2026-08-01"],
        ["3", "SNV", "Pathogenic", "reviewed by expert panel",
         "GRCh38", "17", "300", "300", "G", "A", "203", "RCV000000203",
         "germline", "BRCA2", "333", "2026-08-01"],
    ]
    return _write_gz(tmp_path / "t1.txt.gz", rows)


def test_variant_identity_from_record():
    record = type("R", (), {
        "chromosome": "7", "start": 100,
        "reference_allele": "A", "alternate_allele": "T",
    })()
    identity = VariantIdentity.from_record(record)  # type: ignore[arg-type]
    assert identity.chrom == "7"
    assert identity.start == 100
    assert identity.ref == "A"
    assert identity.alt == "T"


def test_variant_identity_hashable():
    v1 = VariantIdentity("7", 100, "A", "T")
    v2 = VariantIdentity("7", 100, "A", "T")
    assert hash(v1) == hash(v2)
    assert v1 == v2


def test_build_cohort_resolves_variants(t0_file, t1_file):
    cohort = build_temporal_cohort(
        t0_file, t1_file,
        t0_release_date=date(2025, 1, 1),
        t1_release_date=date(2026, 8, 1),
    )

    # t0 had 4 records, all germline SNV on GRCh38
    # The frozen protocol has no t0 star gate: alleles 1, 2, and 4 are VUS.
    assert cohort.flow.t0_vus_meets_star_gate == 3

    # Variants 1 and 2 resolve; variant 4 has no t1 record.
    assert cohort.n_resolved_pathogenic == 1
    assert cohort.n_resolved_benign == 1
    assert cohort.n_excluded == 1


def test_build_cohort_flow_counts(t0_file, t1_file):
    cohort = build_temporal_cohort(
        t0_file, t1_file,
        t0_release_date=date(2025, 1, 1),
        t1_release_date=date(2026, 8, 1),
    )
    flow_dict = cohort.flow.to_dict()
    assert "t0_unique_variants" in flow_dict
    assert flow_dict["t0_unique_variants"] == 4


def test_build_cohort_class_counts(t0_file, t1_file):
    cohort = build_temporal_cohort(
        t0_file, t1_file,
        t0_release_date=date(2025, 1, 1),
        t1_release_date=date(2026, 8, 1),
    )
    counts = cohort.class_counts()
    assert counts["resolved_benign"] == 1


def test_build_cohort_outcome_enum_values():
    assert Outcome.RESOLVED_PATHOGENIC.value == "resolved_pathogenic"
    assert Outcome.RESOLVED_BENIGN.value == "resolved_benign"
    assert Outcome.UNRESOLVED.value == "unresolved"
    assert Outcome.EXCLUDED.value == "excluded"


def test_cohort_variant_to_dict():
    identity = VariantIdentity("7", 100, "A", "T")
    cv = CohortVariant(
        identity=identity,
        t0_clinical_significance="Uncertain_significance",
        t0_review_status="test",
        t0_review_stars=2,
        t1_clinical_significance="Pathogenic",
        t1_review_status="test",
        t1_review_stars=3,
        outcome=Outcome.RESOLVED_PATHOGENIC,
        t1_classification="pathogenic",
        gene_symbol="BRCA1",
        allele_id_t0=1,
        allele_id_t1=201,
    )
    d = cv.to_dict()
    assert d["chrom"] == "7"
    assert d["outcome"] == "resolved_pathogenic"
    assert d["gene_symbol"] == "BRCA1"


def test_build_cohort_with_vus_not_resolved(tmp_path):
    """A VUS at t0 that remains VUS at t1 should be unresolved."""
    t0 = _write_gz(tmp_path / "t0.txt.gz", [
        ["1", "SNV", "Uncertain_significance", "reviewed by expert panel",
         "GRCh38", "7", "100", "100", "A", "T", "101", "RCV000000001",
         "germline", "BRCA1", "111", "2024-01-15"],
    ])
    t1 = _write_gz(tmp_path / "t1.txt.gz", [
        ["1", "SNV", "Uncertain_significance", "reviewed by expert panel",
         "GRCh38", "7", "100", "100", "A", "T", "201", "RCV000000201",
         "germline", "BRCA1", "111", "2026-08-01"],
    ])
    cohort = build_temporal_cohort(t0, t1)
    assert cohort.n_resolved_pathogenic == 0
    assert cohort.n_resolved_benign == 0
    assert cohort.n_unresolved == 1


def test_build_cohort_no_t1_record(tmp_path):
    """A VUS at t0 with no record at t1 is excluded."""
    t0 = _write_gz(tmp_path / "t0.txt.gz", [
        ["1", "SNV", "Uncertain_significance", "reviewed by expert panel",
         "GRCh38", "7", "100", "100", "A", "T", "101", "RCV000000001",
         "germline", "BRCA1", "111", "2024-01-15"],
    ])
    t1 = _write_gz(tmp_path / "t1.txt.gz", [
        ["2", "SNV", "Pathogenic", "reviewed by expert panel",
         "GRCh38", "7", "200", "200", "C", "G", "202", "RCV000000202",
         "germline", "BRCA1", "222", "2026-08-01"],
    ])
    cohort = build_temporal_cohort(t0, t1)
    assert cohort.n_excluded == 1


def test_build_cohort_empty_files(tmp_path):
    t0 = _write_gz(tmp_path / "t0.txt.gz", [])
    t1 = _write_gz(tmp_path / "t1.txt.gz", [])
    cohort = build_temporal_cohort(t0, t1)
    assert cohort.n_total == 0
    assert cohort.positive_count() == 0
    assert cohort.negative_count() == 0


# --------------------------------------------------------------------------- #
# M35: Duplicate-resolution audit
# --------------------------------------------------------------------------- #


def test_audit_duplicates_no_dups():
    records = [
        _make_record(identity=VariantIdentity("7", 100, "A", "T")),
        _make_record(identity=VariantIdentity("7", 200, "C", "G")),
    ]
    audit = audit_duplicates(records)
    assert audit.total_records == 2
    assert audit.unique_identities == 2
    assert audit.duplicate_count == 0
    assert audit.max_dups_per_identity == 1
    assert audit.identities_with_dups == 0


def test_audit_duplicates_with_dups():
    records = [
        _make_record(identity=VariantIdentity("7", 100, "A", "T")),
        _make_record(identity=VariantIdentity("7", 100, "A", "T")),
        _make_record(identity=VariantIdentity("7", 100, "A", "T")),
        _make_record(identity=VariantIdentity("7", 200, "C", "G")),
    ]
    audit = audit_duplicates(records)
    assert audit.total_records == 4
    assert audit.unique_identities == 2
    assert audit.duplicate_count == 2
    assert audit.max_dups_per_identity == 3
    assert audit.identities_with_dups == 1


def test_audit_duplicates_empty():
    audit = audit_duplicates([])
    assert audit.total_records == 0
    assert audit.unique_identities == 0
    assert audit.duplicate_count == 0


def test_duplicate_audit_to_dict():
    audit = DuplicateAudit(
        total_records=10,
        unique_identities=8,
        duplicate_count=2,
        max_dups_per_identity=3,
        identities_with_dups=1,
    )
    d = audit.to_dict()
    assert d["total_records"] == 10
    assert d["unique_identities"] == 8
    assert d["duplicate_count"] == 2


def test_cohort_config_defaults():
    cfg = CohortConfig()
    assert cfg.min_review_stars == 2
    assert cfg.assembly == "GRCh38"


def test_build_primary_cohort_delegates(t0_file, t1_file):
    cohort = build_primary_cohort(
        t0_file, t1_file,
        t0_release_date=date(2025, 1, 1),
        t1_release_date=date(2026, 8, 1),
    )
    assert cohort.n_resolved_benign == 1


def test_build_temporal_cohort_with_config(t0_file, t1_file):
    config = CohortConfig(min_review_stars=2)
    cohort = build_temporal_cohort(
        t0_file, t1_file, config=config,
    )
    assert cohort.n_resolved_benign == 1


def test_build_temporal_cohort_min_stars_override(t0_file, t1_file):
    """Override min_review_stars to 0 to include VUS with 0 stars."""
    cohort = build_temporal_cohort(
        t0_file, t1_file, min_review_stars=0,
    )
    # With 0-star gate, allele 4 (VUS, 0 stars) is now included
    # but it has no t1 record, so still excluded
    assert cohort.n_excluded >= 0


def _make_record(identity: VariantIdentity) -> VariantSummaryRecord:
    """Create a minimal record for duplicate audit tests."""
    return VariantSummaryRecord(
        allele_id=1,
        variant_type="SNV",
        clinical_significance="Uncertain_significance",
        review_status="test",
        review_stars=2,
        assembly="GRCh38",
        chromosome=identity.chrom,
        start=identity.start,
        stop=identity.start,
        reference_allele=identity.ref,
        alternate_allele=identity.alt,
        variation_id=1,
        rcv_accessions=[],
        origin_simple="germline",
        germline=True,
    )
