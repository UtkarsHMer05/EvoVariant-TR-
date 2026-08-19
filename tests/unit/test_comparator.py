"""Tests for comparator.py — Milestone 71."""

from __future__ import annotations

import pytest

from evovariant_tr.comparator import (
    ComparatorAdapter,
    ComparatorResult,
    ComparatorSuite,
)
from evovariant_tr.sequence_mutate import VariantIdentity
from evovariant_tr.sequence_window import ReferenceWindow

TEST_WINDOW = ReferenceWindow(
    chrom="chr1", start=1, stop=8192,
    ref_sequence="A" * 4096 + "CGT" + "T" * 4093,
    variant_offset=4096,
)


class DummyComparator(ComparatorAdapter):
    """A simple comparator for testing."""

    @property
    def name(self) -> str:
        return "dummy"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def is_snp_compatible(self) -> bool:
        return True

    def score(self, ref_window, variant, strand="forward") -> ComparatorResult:
        return ComparatorResult(
            comparator_name="dummy",
            comparator_version="1.0.0",
            variant=(variant.chrom, variant.start, variant.ref, variant.alt),
            reference_score=1.0,
            alternate_score=2.0,
            score_delta=1.0,
        )

    def score_batch(self, variants):
        return [self.score(rw, v, s) for rw, v, s in variants]


def test_comparator_result_creation():
    result = ComparatorResult(
        comparator_name="phyloP",
        comparator_version="2.1",
        variant=("chr1", 100, "A", "T"),
        reference_score=0.5,
        alternate_score=0.7,
        score_delta=0.2,
    )
    assert result.comparator_name == "phyloP"
    assert result.score_delta == 0.2


def test_comparator_adapter_abstract():
    """ComparatorAdapter should be abstract."""
    with pytest.raises(TypeError):
        ComparatorAdapter()


def test_comparator_suite_creation():
    suite = ComparatorSuite()
    assert suite.scorers == []
    assert suite.list_names() == []


def test_comparator_suite_add():
    suite = ComparatorSuite()
    suite.add(DummyComparator())
    assert len(suite.scorers) == 1
    assert "dummy" in suite.list_names()


def test_comparator_suite_score_variant():
    suite = ComparatorSuite()
    suite.add(DummyComparator())
    variant = VariantIdentity("chr1", 50000, "C", "T")
    results = suite.score_variant(TEST_WINDOW, variant)
    assert len(results) == 1
    assert results[0].comparator_name == "dummy"
    assert results[0].score_delta == 1.0


def test_comparator_suite_score_variant_error_handling():
    """Suite should handle comparator errors gracefully."""

    class ErrorComparator(ComparatorAdapter):
        @property
        def name(self) -> str:
            return "error"

        @property
        def version(self) -> str:
            return "1.0"

        @property
        def is_snp_compatible(self) -> bool:
            return True

        def score(self, ref_window, variant, strand="forward"):
            raise RuntimeError("Model load failed")

        def score_batch(self, variants):
            return []

    suite = ComparatorSuite()
    suite.add(DummyComparator())
    suite.add(ErrorComparator())

    variant = VariantIdentity("chr1", 50000, "C", "T")
    results = suite.score_variant(TEST_WINDOW, variant)

    assert len(results) == 2
    assert results[0].comparator_name == "dummy"
    assert results[1].comparator_name == "error"
    assert results[1].metadata.get("skipped") is True
    assert "error" in results[1].metadata


def test_comparator_provenance():
    dummy = DummyComparator()
    prov = dummy.provenance()
    assert prov["comparator_name"] == "dummy"
    assert prov["comparator_version"] == "1.0.0"
    assert prov["is_snp_compatible"] is True