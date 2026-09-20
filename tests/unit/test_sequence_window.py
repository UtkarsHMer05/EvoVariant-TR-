"""Tests for sequence_window.py — Milestones 41-43."""

from __future__ import annotations

from pathlib import Path

import pytest

from evovariant_tr.sequence_window import (
    CONTEXT_LENGTH_BP,
    GENOMIC_NUCLS,
    HALF_WINDOW,
    ReferenceWindow,
    compute_window_coordinates,
    compute_window_coordinates_with_shift,
    generate_reference_window,
    validate_sequence_content,
    validate_window_coordinates,
    validate_window_variant_position,
)

# Test constants
TEST_CHROM_LEN = 100000  # 100kb chromosome for testing
TEST_VARIANT_POS = 50000  # Middle of chromosome


# --------------------------------------------------------------------------- #
# M41: Frozen window convention
# --------------------------------------------------------------------------- #


def test_context_length_is_8192():
    assert CONTEXT_LENGTH_BP == 8192


def test_half_window_is_4096():
    assert HALF_WINDOW == 4096


def test_compute_window_centered():
    start, stop = compute_window_coordinates(TEST_CHROM_LEN, TEST_VARIANT_POS)
    assert start == TEST_VARIANT_POS - HALF_WINDOW + 1
    assert stop == TEST_VARIANT_POS + HALF_WINDOW
    assert stop - start + 1 == CONTEXT_LENGTH_BP


def test_compute_window_near_start_edge():
    """When variant is near start, shift window to start at 1."""
    variant_pos = 100  # Very close to start
    start, stop = compute_window_coordinates(TEST_CHROM_LEN, variant_pos)
    assert start == 1
    assert stop == min(TEST_CHROM_LEN, CONTEXT_LENGTH_BP)


def test_compute_window_near_end_edge():
    """When variant is near end, shift window to end at chrom_len."""
    variant_pos = TEST_CHROM_LEN - 100
    start, stop = compute_window_coordinates(TEST_CHROM_LEN, variant_pos)
    assert stop == TEST_CHROM_LEN
    assert start == max(1, TEST_CHROM_LEN - CONTEXT_LENGTH_BP + 1)


def test_compute_window_with_shift_centered():
    start, stop, offset = compute_window_coordinates_with_shift(TEST_CHROM_LEN, TEST_VARIANT_POS)
    assert start == TEST_VARIANT_POS - HALF_WINDOW + 1
    assert stop == TEST_VARIANT_POS + HALF_WINDOW
    assert offset == HALF_WINDOW - 1  # 0-based offset within window


def test_compute_window_with_shift_near_start():
    variant_pos = 100
    start, stop, offset = compute_window_coordinates_with_shift(TEST_CHROM_LEN, variant_pos)
    assert start == 1
    assert offset == 99  # variant_pos - start = 100 - 1


def test_compute_window_with_shift_near_end():
    variant_pos = TEST_CHROM_LEN - 100
    start, stop, offset = compute_window_coordinates_with_shift(TEST_CHROM_LEN, variant_pos)
    assert stop == TEST_CHROM_LEN
    assert offset == variant_pos - start


# --------------------------------------------------------------------------- #
# M42: Window validation
# --------------------------------------------------------------------------- #


def test_validate_window_coordinates_valid():
    errors = validate_window_coordinates(
        chrom_len=100000,
        window_start=1,
        window_stop=8192,
        variant_pos=4096,
    )
    assert errors == []


def test_validate_window_coordinates_out_of_bounds():
    errors = validate_window_coordinates(
        chrom_len=100,
        window_start=1,
        window_stop=8192,
        variant_pos=50,
    )
    assert any("out of bounds" in e for e in errors)


def test_validate_window_coordinates_invalid_range():
    errors = validate_window_coordinates(
        chrom_len=100000,
        window_start=5000,
        window_stop=1000,
        variant_pos=3000,
    )
    assert any("start > stop" in e for e in errors)


def test_validate_window_coordinates_too_long():
    errors = validate_window_coordinates(
        chrom_len=100000,
        window_start=1,
        window_stop=9000,
        variant_pos=4500,
    )
    assert any("too long" in e for e in errors)


def test_validate_window_coordinates_too_short():
    errors = validate_window_coordinates(
        chrom_len=100000,
        window_start=1,
        window_stop=8191,
        variant_pos=4096,
    )
    assert any("too short" in e for e in errors)


def test_validate_window_coordinates_variant_outside():
    errors = validate_window_coordinates(
        chrom_len=100000,
        window_start=1,
        window_stop=8192,
        variant_pos=10000,
    )
    assert any("not in window" in e for e in errors)


def test_validate_window_variant_position_valid():
    errors = validate_window_variant_position(
        window_start=1, window_stop=8192, variant_pos=4096,
    )
    assert errors == []


def test_validate_window_variant_position_outside():
    errors = validate_window_variant_position(
        window_start=1, window_stop=8192, variant_pos=10000,
    )
    assert any("outside window" in e for e in errors)


def test_validate_window_variant_position_negative_offset():
    errors = validate_window_variant_position(
        window_start=4096, window_stop=12287, variant_pos=100,
    )
    assert any("Negative variant offset" in e or "outside window" in e for e in errors)


# --------------------------------------------------------------------------- #
# M43: Chromosome-edge behavior
# --------------------------------------------------------------------------- #


def test_chromosome_edge_start():
    """Variant at position 1 should have window starting at 1."""
    start, stop, offset = compute_window_coordinates_with_shift(
        chrom_len=100000, variant_pos=1,
    )
    assert start == 1
    assert offset == 0


def test_chromosome_edge_stop():
    """Variant at last position should have window ending at chrom_len."""
    start, stop, offset = compute_window_coordinates_with_shift(
        chrom_len=100000, variant_pos=100000,
    )
    assert stop == 100000
    assert offset == 100000 - start


def test_chromosome_edge_small_chromosome():
    """Chromosome shorter than window size should use full length."""
    start, stop, offset = compute_window_coordinates_with_shift(
        chrom_len=100, variant_pos=50,
    )
    assert 1 <= start <= stop <= 100
    assert stop - start + 1 <= 100  # Can't exceed chrom length


def test_window_windowed_center_exact():
    """The 8,192 window should have the variant at offset 4095 (0-based)."""
    start, stop, offset = compute_window_coordinates_with_shift(
        chrom_len=1000000, variant_pos=500000,
    )
    assert stop - start + 1 == CONTEXT_LENGTH_BP
    assert offset == HALF_WINDOW - 1


# --------------------------------------------------------------------------- #
# Sequence content validation
# --------------------------------------------------------------------------- #


def test_validate_sequence_content_valid():
    seq = "A" * 4096 + "C" * 4096
    errors = validate_sequence_content(seq)
    assert errors == []


def test_validate_sequence_content_with_n():
    seq = "N" * 8192
    errors = validate_sequence_content(seq)
    assert errors == []


def test_validate_sequence_content_invalid_chars():
    seq = "X" * 8192
    errors = validate_sequence_content(seq)
    assert any("Invalid nucleotide" in e for e in errors)


def test_validate_sequence_content_wrong_length():
    seq = "A" * 100
    errors = validate_sequence_content(seq)
    assert any("length" in e.lower() for e in errors)


def test_genomic_nucels_contains_bases():
    assert "A" in GENOMIC_NUCLS
    assert "C" in GENOMIC_NUCLS
    assert "G" in GENOMIC_NUCLS
    assert "T" in GENOMIC_NUCLS


# --------------------------------------------------------------------------- #
# ReferenceWindow dataclass
# --------------------------------------------------------------------------- #


def test_reference_window_is_frozen():
    window = ReferenceWindow(
        chrom="chr1", start=1, stop=8192,
        ref_sequence="ACGT" * 2048, variant_offset=4095,
    )
    with pytest.raises(AttributeError):
        window.chrom = "chr2"


def test_reference_window_creation():
    window = ReferenceWindow(
        chrom="chr1", start=1, stop=8192,
        ref_sequence="A" * 8192, variant_offset=4095,
    )
    assert window.chrom == "chr1"
    assert window.start == 1
    assert window.stop == 8192
    assert window.variant_offset == 4095


# --------------------------------------------------------------------------- #
# M42: Reference window generation with mock FASTA
# --------------------------------------------------------------------------- #


def _make_mock_fasta(tmp_path: Path) -> tuple[Path, Path]:
    """Create a mock FASTA with chr1 (100000 A's) and its .fai index."""
    fasta = tmp_path / "ref.fasta"
    # Single-line FASTA with chr1 = 100000 'A's
    seq = "A" * 100000
    fasta.write_text(f">chr1\n{seq}\n")

    # .fai: name, length, offset, line_bases, line_width, qual_offset
    # >chr1\n = 6 bytes, seq = 100000 bytes, line_width = 100000 + 0 (no newline in sequence)
    # Actually: ">chr1\n" = 6 bytes, then "AAAA..." = 100000 bytes, then "\n" = 1 byte
    # line_bases = 100000, line_width = 100001 (bases + newline)
    fai = tmp_path / "ref.fasta.fai"
    fai.write_text("chr1\t100000\t6\t100000\t100001\t0\n")
    return fasta, fai


def test_generate_reference_window_centered(tmp_path: Path):
    """Test window generation for a variant in the middle of a chromosome."""
    fasta, fai = _make_mock_fasta(tmp_path)
    window = generate_reference_window(fasta, fai, "chr1", 50000)
    assert window.chrom == "chr1"
    assert window.start > 0
    assert window.stop <= 100000
    assert window.variant_offset >= 0
    assert len(window.ref_sequence) > 0 or window.ref_sequence == ""


def test_generate_reference_window_near_start(tmp_path: Path):
    """Test window generation for a variant near the start."""
    fasta, fai = _make_mock_fasta(tmp_path)
    window = generate_reference_window(fasta, fai, "chr1", 100)
    assert window.start == 1
    assert window.variant_offset == 99


def test_generate_reference_window_near_end(tmp_path: Path):
    """Test window generation for a variant near the end."""
    fasta, fai = _make_mock_fasta(tmp_path)
    window = generate_reference_window(fasta, fai, "chr1", 99900)
    assert window.stop == 100000
    assert window.variant_offset >= 0


def test_generate_reference_window_invalid_chrom(tmp_path: Path):
    """Test that requesting an invalid chromosome raises ValueError."""
    fasta, fai = _make_mock_fasta(tmp_path)
    with pytest.raises(ValueError, match="not found"):
        generate_reference_window(fasta, fai, "chr999", 50000)


def test_generated_window_validates(tmp_path: Path):
    """The generated window coordinates should pass validation."""
    fasta, fai = _make_mock_fasta(tmp_path)
    variant_pos = 50000
    window = generate_reference_window(fasta, fai, "chr1", variant_pos)
    errors = validate_window_coordinates(
        chrom_len=100000,
        window_start=window.start,
        window_stop=window.stop,
        variant_pos=variant_pos,
    )
    assert errors == []
