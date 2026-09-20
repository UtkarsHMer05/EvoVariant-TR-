"""Reference sequence window generation for EvoVariant-TR (Milestones 41-42).

Implements the frozen 8,192-base context window convention:
- Window is centered on the variant start position.
- For odd-length windows, the variant is exactly at the center.
- For even-length windows (8,192), the variant is at position 4,095
  (0-based) or 4,096 (1-based from left edge), with 4,096 bases on each
  side.
- Window coordinates are clamped to chromosome bounds.
- Chromosome-edge behavior: if the variant is too close to an edge, the
  window is shifted to extend further on the opposite side, maintaining
  the full window length when possible.

The context_length_bp is frozen at 8,192 (protocol.yaml, Milestone 41).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

CONTEXT_LENGTH_BP = 8192
HALF_WINDOW = CONTEXT_LENGTH_BP // 2  # 4096

GENOMIC_NUCLS = frozenset({"A", "C", "G", "T"})


@dataclass(frozen=True)
class ReferenceWindow:
    """A reference sequence window for a variant.

    Attributes:
        chrom: Chromosome name.
        start: 1-based start position of the window (inclusive).
        stop: 1-based stop position of the window (inclusive).
        ref_sequence: The reference sequence (uppercase).
        variant_offset: 0-based offset within ref_sequence where the variant
            start position falls.
    """

    chrom: str
    start: int
    stop: int
    ref_sequence: str
    variant_offset: int


def compute_window_coordinates(
    chrom_len: int,
    variant_pos: int,
) -> tuple[int, int]:
    """Compute window start/stop for a variant position.

    Uses the frozen convention:
    - Window is 8,192 bases total.
    - Variant is at the center (position 4,096 from either edge).
    - Coordinates are clamped to chromosome bounds [1, chrom_len].

    Args:
        chrom_len: Length of the chromosome.
        variant_pos: 1-based variant start position.

    Returns:
        Tuple of (window_start, window_stop) in 1-based inclusive coordinates.
    """
    half = HALF_WINDOW  # 4096
    desired_start = variant_pos - half + 1
    desired_stop = variant_pos + half

    if desired_start < 1:
        desired_start = 1
        desired_stop = min(chrom_len, CONTEXT_LENGTH_BP)
    elif desired_stop > chrom_len:
        desired_stop = chrom_len
        desired_start = max(1, chrom_len - CONTEXT_LENGTH_BP + 1)

    return desired_start, desired_stop


def compute_window_coordinates_with_shift(
    chrom_len: int,
    variant_pos: int,
) -> tuple[int, int, int]:
    """Compute window coordinates with edge-shift behavior.

    When the variant is near a chromosome edge:
    - If too close to the start (variant_pos < half), shift the window
      to start at position 1 and extend to CONTEXT_LENGTH_BP.
    - If too close to the end, shift the window to end at chrom_len
      and start at chrom_len - CONTEXT_LENGTH_BP + 1.
    - Otherwise, center the window on the variant.

    Returns:
        Tuple of (window_start, window_stop, variant_offset).
        variant_offset is the 0-based offset of the variant within the window.
    """
    half = HALF_WINDOW  # 4096
    desired_start = variant_pos - half + 1
    desired_stop = variant_pos + half

    shift = 0
    if desired_start < 1:
        shift = 1 - desired_start  # How far we need to shift right
        desired_start = 1
        desired_stop = min(chrom_len, desired_stop + shift)
    elif desired_stop > chrom_len:
        shift = chrom_len - desired_stop  # Negative, shift left
        desired_stop = chrom_len
        desired_start = max(1, desired_start + shift)

    # variant_offset: 0-based position of variant_pos within [desired_start, desired_stop]
    variant_offset = variant_pos - desired_start

    return desired_start, desired_stop, variant_offset


def validate_window_coordinates(
    chrom_len: int,
    window_start: int,
    window_stop: int,
    variant_pos: int,
) -> list[str]:
    """Validate window coordinates are within chromosome bounds and correct."""
    errors: list[str] = []
    if window_start < 1 or window_stop > chrom_len:
        errors.append(
            f"Window out of bounds: [{window_start}, {window_stop}] "
            f"not in [1, {chrom_len}]"
        )
    if window_start > window_stop:
        errors.append(f"Invalid window: start > stop ({window_start} > {window_stop})")
    window_len = window_stop - window_start + 1
    if window_len > CONTEXT_LENGTH_BP:
        errors.append(f"Window too long: {window_len} > {CONTEXT_LENGTH_BP}")
    elif window_len < CONTEXT_LENGTH_BP:
        errors.append(f"Window too short: {window_len} < {CONTEXT_LENGTH_BP}")
    if variant_pos < window_start or variant_pos > window_stop:
        errors.append(
            f"Variant position {variant_pos} not in window "
            f"[{window_start}, {window_stop}]"
        )
    return errors


def validate_window_variant_position(
    window_start: int,
    window_stop: int,
    variant_pos: int,
) -> list[str]:
    """Validate that variant_pos is within the window and offset is correct."""
    errors: list[str] = []
    if variant_pos < window_start or variant_pos > window_stop:
        errors.append(
            f"Variant at {variant_pos} is outside window "
            f"[{window_start}, {window_stop}]"
        )
    expected_offset = variant_pos - window_start
    if expected_offset < 0:
        errors.append(f"Negative variant offset: {expected_offset}")
    if expected_offset >= CONTEXT_LENGTH_BP:
        errors.append(f"Variant offset >= context length: {expected_offset}")
    return errors


def generate_reference_window(
    fasta_path: str | Path,
    fai_path: str | Path,
    chrom: str,
    variant_pos: int,
) -> ReferenceWindow:
    """Generate a reference sequence window for a variant.

    Args:
        fasta_path: Path to the indexed reference FASTA.
        fai_path: Path to the .fai index.
        chrom: Chromosome name.
        variant_pos: 1-based variant start position.

    Returns:
        A ReferenceWindow with the sequence and coordinates.
    """
    # Load chromosome length from .fai
    chrom_len: int | None = None
    with Path(fai_path).open("r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("\t")
            if parts[0] == chrom:
                chrom_len = int(parts[1])
                break

    if chrom_len is None:
        raise ValueError(f"Chromosome {chrom} not found in reference index")

    window_start, window_stop, variant_offset = compute_window_coordinates_with_shift(
        chrom_len, variant_pos,
    )

    # Extract sequence using samtools or direct read
    import shutil
    import subprocess

    samtools = shutil.which("samtools")
    if samtools:
        result = subprocess.run(
            [samtools, "faidx", str(fasta_path), f"{chrom}:{window_start}-{window_stop}"],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            seq = "".join(lines[1:]).upper() if len(lines) > 1 else ""
        else:
            fasta_p = Path(fasta_path)
            fai_p = Path(fai_path)
            seq = _read_fasta_region(fasta_p, fai_p, chrom, window_start, window_stop)
    else:
        fasta_p = Path(fasta_path)
        fai_p = Path(fai_path)
        seq = _read_fasta_region(fasta_p, fai_p, chrom, window_start, window_stop)

    sequence_errors = validate_sequence_content(seq)
    if sequence_errors:
        raise ValueError("invalid reference window: " + "; ".join(sequence_errors))

    return ReferenceWindow(
        chrom=chrom,
        start=window_start,
        stop=window_stop,
        ref_sequence=seq,
        variant_offset=variant_offset,
    )


def _read_fasta_region(
    fasta_path: Path,
    fai_path: Path,
    chrom: str,
    start: int,
    stop: int,
) -> str:
    """Read a region from a FASTA file using the .fai index (pure Python).

    This is a fallback that doesn't require samtools.
    """
    # Load index entry for this chrom
    offset = 0
    line_bases = 0
    line_width = 0
    with Path(fai_path).open("r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("\t")
            if parts[0] == chrom:
                offset = int(parts[2])
                line_bases = int(parts[3])
                line_width = int(parts[4])
                break

    seq_chars: list[str] = []
    pos = start
    while pos <= stop:
        line_idx = (pos - 1) // line_bases
        col_in_line = (pos - 1) % line_bases
        byte_pos = offset + line_idx * line_width + col_in_line

        with Path(fasta_path).open("rb") as f:
            f.seek(byte_pos)
            remaining = stop - pos + 1
            available = line_bases - col_in_line
            to_read = min(remaining, available)
            chunk = f.read(to_read)
            seq_chars.append(chunk.decode("ascii").upper())
            pos += to_read

    return "".join(seq_chars)


def validate_sequence_content(seq: str) -> list[str]:
    """Validate that a sequence contains only valid nucleotide characters."""
    errors: list[str] = []
    invalid = set(seq.upper()) - GENOMIC_NUCLS - {"N"}
    if invalid:
        errors.append(f"Invalid nucleotide characters: {invalid}")
    if len(seq) != CONTEXT_LENGTH_BP:
        errors.append(
            f"Sequence length {len(seq)} != expected {CONTEXT_LENGTH_BP}"
        )
    return errors
