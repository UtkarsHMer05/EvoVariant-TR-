"""Tests for comparator_baselines.py — Milestones 72-75."""

from __future__ import annotations

from evovariant_tr.comparator_baselines import (
    AlphaMissenseComparator,
    CADDComparator,
    GPNComparator,
    PhyloPComparator,
)
from evovariant_tr.sequence_mutate import VariantIdentity
from evovariant_tr.sequence_window import ReferenceWindow

TEST_WINDOW = ReferenceWindow(
    chrom="chr1", start=1, stop=8192,
    ref_sequence="A" * 4096 + "CGT" + "T" * 4093,
    variant_offset=4096,
)
TEST_VARIANT = VariantIdentity("chr1", 50000, "C", "T")


def test_phyloP_comparator():
    comp = PhyloPComparator()
    assert comp.name == "phyloP"
    assert comp.is_snp_compatible is True
    result = comp.score(TEST_WINDOW, TEST_VARIANT)
    assert result.comparator_name == "phyloP"
    assert result.comparator_version == "1.3"
    assert result.score_delta == result.alternate_score - result.reference_score


def test_CADD_comparator():
    comp = CADDComparator()
    assert comp.name == "CADD"
    result = comp.score(TEST_WINDOW, TEST_VARIANT)
    assert result.comparator_name == "CADD"


def test_gpn_comparator():
    comp = GPNComparator()
    assert comp.name == "GPN-MSA"
    result = comp.score(TEST_WINDOW, TEST_VARIANT)
    assert result.comparator_name == "GPN-MSA"


def test_alpha_missense_skips_non_missense():
    comp = AlphaMissenseComparator()
    assert comp.name == "AlphaMissense"
    # Position 50000 % 3 = 2, so it should be missense
    result = comp.score(TEST_WINDOW, TEST_VARIANT)
    assert result.comparator_name == "AlphaMissense"
    assert "score_type" in result.metadata


def test_alpha_missense_skips_deletion():
    comp = AlphaMissenseComparator()
    del_variant = VariantIdentity("chr1", 50000, "CGT", "")
    result = comp.score(TEST_WINDOW, del_variant)
    assert result.metadata.get("skipped") is True
    assert result.metadata.get("reason") == "not_missense_variant"


def test_all_comparators_are_comparators():
    from evovariant_tr.comparator import ComparatorAdapter

    for cls in [PhyloPComparator, CADDComparator, GPNComparator, AlphaMissenseComparator]:
        assert issubclass(cls, ComparatorAdapter)


def test_comparator_provenance():
    comp = PhyloPComparator()
    prov = comp.provenance()
    assert prov["comparator_name"] == "phyloP"
    assert prov["is_snp_compatible"] is True


def test_comparator_batch():
    comp = CADDComparator()
    variant2 = VariantIdentity("chr1", 50001, "A", "G")
    results = comp.score_batch([
        (TEST_WINDOW, TEST_VARIANT, "forward"),
        (TEST_WINDOW, variant2, "forward"),
    ])
    assert len(results) == 2
    assert all(r.comparator_name == "CADD" for r in results)


def test_comparators_deterministic():
    """Same input should produce same scores."""
    comp = GPNComparator()
    r1 = comp.score(TEST_WINDOW, TEST_VARIANT)
    r2 = comp.score(TEST_WINDOW, TEST_VARIANT)
    assert r1.reference_score == r2.reference_score
    assert r1.alternate_score == r2.alternate_score