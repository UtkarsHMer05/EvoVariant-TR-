"""Reference-allele validation tests (Milestone 34).

These tests verify that the cohort pipeline correctly validates ClinVar's
reported reference allele against the GRCh38 reference genome. This is a
deterministic check that does not require downloading the full reference —
it uses a small synthetic FASTA + .fai fixture.
"""

from __future__ import annotations

from pathlib import Path

from evovariant_tr.clinvar_parser import VariantSummaryRecord
from evovariant_tr.reference import ReferenceGenome

FASTA_CONTENT = ">chr1\nAAAAAAAAAA\n>chr2\nGGGGGGGGGG\n"
FAI_CONTENT = "chr1\t10\t6\t10\t11\t0\nchr2\t10\t22\t10\t11\t0\n"


def _make_ref(tmp_path: Path) -> ReferenceGenome:
    fasta = tmp_path / "ref.fasta"
    fasta.write_text(FASTA_CONTENT)
    fai = tmp_path / "ref.fasta.fai"
    fai.write_text(FAI_CONTENT)
    return ReferenceGenome(fasta)


def _make_record(chrom: str, start: int, ref: str, alt: str) -> VariantSummaryRecord:
    return VariantSummaryRecord(
        allele_id=1,
        variant_type="SNV",
        clinical_significance="Uncertain_significance",
        review_status="reviewed by expert panel",
        review_stars=3,
        assembly="GRCh38",
        chromosome=chrom,
        start=start,
        stop=start,
        reference_allele=ref,
        alternate_allele=alt,
        variation_id=1,
        rcv_accessions=[],
        origin_simple="germline",
        germline=True,
    )


def test_reference_validates_correct_allele(tmp_path: Path):
    """The reference allele should match the genome."""
    ref = _make_ref(tmp_path)
    assert ref.validate_allele("chr1", 1, "A") is True
    assert ref.validate_allele("chr2", 5, "G") is True


def test_reference_rejects_wrong_allele(tmp_path: Path):
    """A mismatched reference allele should be rejected."""
    ref = _make_ref(tmp_path)
    assert ref.validate_allele("chr1", 1, "T") is False
    assert ref.validate_allele("chr2", 1, "A") is False


def test_reference_get_base_case_insensitive(tmp_path: Path):
    ref = _make_ref(tmp_path)
    assert ref.validate_allele("chr1", 1, "a") is True


def test_reference_unknown_chromosome(tmp_path: Path):
    ref = _make_ref(tmp_path)
    assert ref.get_base("chr3", 1) is None
    assert ref.validate_allele("chr3", 1, "A") is False


def test_reference_out_of_bounds(tmp_path: Path):
    ref = _make_ref(tmp_path)
    assert ref.get_base("chr1", 0) is None
    assert ref.get_base("chr1", 11) is None
    assert ref.get_base("chr1", 1) == "A"


def test_validate_position(tmp_path: Path):
    ref = _make_ref(tmp_path)
    assert ref.validate_position("chr1", 1) is True
    assert ref.validate_position("chr1", 10) is True
    assert ref.validate_position("chr1", 11) is False
    assert ref.validate_position("chr3", 1) is False
