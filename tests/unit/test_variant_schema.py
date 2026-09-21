"""Tests for canonical internal variant validation."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from evovariant_tr.variant_schema import (
    CanonicalVariant,
    VariantPayload,
    normalize_chromosome,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("1", "chr1"), (" chr10 ", "chr10"), ("chr17", "chr17")],
)
def test_normalize_chromosome_matches_ucsc_spelling(raw: str, expected: str) -> None:
    assert normalize_chromosome(raw) == expected


def test_normalize_chromosome_rejects_blank_values() -> None:
    with pytest.raises(ValueError, match="chromosome must be non-empty"):
        normalize_chromosome("  ")


def test_canonical_variant_id_is_stable() -> None:
    variant = CanonicalVariant("GRCh38", "chr1", 42, "a", "t")
    assert variant.normalized_variant_id == "GRCh38:chr1:42:a>t"
    assert variant.is_snv is True


@pytest.mark.parametrize(
    "args",
    [
        ("hg19", "chr1", 1, "A", "T"),
        ("GRCh38", "", 1, "A", "T"),
        ("GRCh38", "chr1", 0, "A", "T"),
        ("GRCh38", "chr1", 1, "", "T"),
        ("GRCh38", "chr1", 1, "N", "T"),
        ("GRCh38", "chr1", 1, "A", "A"),
    ],
)
def test_canonical_variant_rejects_invalid_identity(args: tuple[object, ...]) -> None:
    with pytest.raises(ValueError):
        CanonicalVariant(*args)  # type: ignore[arg-type]


def test_variant_payload_normalizes_chromosome_and_alleles() -> None:
    payload = VariantPayload(
        chromosome="1",
        position_1based=10,
        reference="a",
        alternate="t",
    )
    canonical = payload.canonical()
    assert canonical.chromosome == "chr1"
    assert canonical.reference == "A"
    assert canonical.alternate == "T"


def test_variant_payload_rejects_unknown_assembly_and_fields() -> None:
    with pytest.raises(ValidationError):
        VariantPayload(
            assembly="hg19",
            chromosome="chr1",
            position_1based=10,
            reference="A",
            alternate="T",
        )
    with pytest.raises(ValidationError):
        VariantPayload(
            chromosome="chr1",
            position_1based=10,
            reference="A",
            alternate="T",
            extra="not allowed",
        )
    with pytest.raises(ValidationError):
        VariantPayload(
            chromosome="",
            position_1based=10,
            reference="A",
            alternate="T",
        )
    with pytest.raises(ValidationError):
        VariantPayload(
            chromosome="chr1",
            position_1based=10,
            reference="N",
            alternate="T",
        )
