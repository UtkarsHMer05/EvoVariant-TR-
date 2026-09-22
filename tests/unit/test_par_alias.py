"""Tests for the narrowly scoped GRCh38 chrY PAR hard-mask alias."""

from __future__ import annotations

from pathlib import Path

import pytest

from evovariant_tr.sequence_window import generate_reference_window_with_par_alias


@pytest.fixture(scope="module")
def par_reference(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Path]:
    """Build a small indexed fixture with masked chrY and usable chrX PAR sequence."""
    directory = tmp_path_factory.mktemp("par-reference")
    length = 2_800_000
    x = bytearray(b"A" * length)
    y = bytearray(b"N" * length)
    x[1_286_043 - 1] = ord("T")
    x[1_309_674 - 1] = ord("G")
    y[45_905 - 1 : 54_096] = b"A" * 8_192
    y[5_000 - 1] = ord("A")
    fasta = directory / "reference.fasta"
    with fasta.open("wb") as handle:
        handle.write(b">chrX\n")
        handle.write(x)
        handle.write(b"\n>chrY\n")
        handle.write(y)
        handle.write(b"\n")
    x_offset = len(b">chrX\n")
    y_offset = x_offset + length + 1 + len(b">chrY\n")
    fai = directory / "reference.fasta.fai"
    fai.write_text(
        f"chrX\t{length}\t{x_offset}\t{length}\t{length + 1}\t0\n"
        f"chrY\t{length}\t{y_offset}\t{length}\t{length + 1}\t0\n",
        encoding="utf-8",
    )
    return fasta, fai


@pytest.mark.parametrize(
    ("position", "expected_ref"),
    [(1_286_043, "T"), (1_309_674, "G")],
)
def test_current_masked_par_variants_alias_to_x(
    par_reference: tuple[Path, Path],
    position: int,
    expected_ref: str,
):
    fasta, fai = par_reference
    window, provenance = generate_reference_window_with_par_alias(
        fasta,
        fai,
        "chrY",
        position,
        expected_ref,
        allow_par_alias=True,
    )
    assert window.chrom == "chrX"
    assert window.ref_sequence[window.variant_offset] == expected_ref
    assert provenance["original_locus"] == {
        "chromosome": "Y",
        "position_1based": position,
    }
    assert provenance["extraction_locus"] == {
        "chromosome": "X",
        "position_1based": position,
    }
    assert provenance["par_alias_applied"] is True
    assert provenance["extracted_ref"] == expected_ref


def test_chr_y_par_with_sequence_uses_canonical_path(par_reference):
    fasta, fai = par_reference
    window, provenance = generate_reference_window_with_par_alias(
        fasta, fai, "chrY", 50_000, "A", allow_par_alias=True,
    )
    assert window.chrom == "chrY"
    assert provenance["par_alias_applied"] is False


def test_chr_y_non_par_variant_does_not_alias(par_reference):
    fasta, fai = par_reference
    window, provenance = generate_reference_window_with_par_alias(
        fasta, fai, "chrY", 5_000, "A", allow_par_alias=True,
    )
    assert window.chrom == "chrY"
    assert provenance["par_alias_applied"] is False


def test_chr_x_variant_does_not_alias(par_reference):
    fasta, fai = par_reference
    window, provenance = generate_reference_window_with_par_alias(
        fasta, fai, "chrX", 50_000, "A", allow_par_alias=True,
    )
    assert window.chrom == "chrX"
    assert provenance["par_alias_applied"] is False


def test_homologous_reference_mismatch_rejects_alias(par_reference):
    fasta, fai = par_reference
    with pytest.raises(ValueError, match="homologous chrX reference mismatch"):
        generate_reference_window_with_par_alias(
            fasta, fai, "chrY", 1_286_043, "G", allow_par_alias=True,
        )


def test_context_crossing_par_boundary_rejects_alias(par_reference):
    fasta, fai = par_reference
    with pytest.raises(ValueError, match="complete unmasked PAR1 window"):
        generate_reference_window_with_par_alias(
            fasta, fai, "chrY", 10_001, "A", allow_par_alias=True,
        )


def test_par_alias_is_deterministic(par_reference):
    fasta, fai = par_reference
    first = generate_reference_window_with_par_alias(
        fasta, fai, "chrY", 1_286_043, "T", allow_par_alias=True,
    )
    second = generate_reference_window_with_par_alias(
        fasta, fai, "chrY", 1_286_043, "T", allow_par_alias=True,
    )
    assert first == second
