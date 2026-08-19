"""Tests for utils.py."""

from __future__ import annotations

from evovariant_tr.utils import (
    deterministic_hash,
    format_variant_identity,
    normalize_gene_symbol,
)


def test_deterministic_hash_deterministic():
    h1 = deterministic_hash("test")
    h2 = deterministic_hash("test")
    assert h1 == h2


def test_deterministic_hash_in_range():
    h = deterministic_hash("test_data")
    assert 0.0 <= h < 1.0


def test_deterministic_hash_different_inputs():
    h1 = deterministic_hash("test1")
    h2 = deterministic_hash("test2")
    assert h1 != h2


def test_normalize_gene_symbol():
    assert normalize_gene_symbol("BRCA1") == "BRCA1"
    assert normalize_gene_symbol("brca1") == "BRCA1"
    assert normalize_gene_symbol(None) == "UNKNOWN"
    assert normalize_gene_symbol("-") == "UNKNOWN"
    assert normalize_gene_symbol("NA") == "UNKNOWN"
    assert normalize_gene_symbol("") == "UNKNOWN"


def test_format_variant_identity():
    result = format_variant_identity("chr1", 100, "A", "T")
    assert result == "chr1:g.100A>T"