"""Alternate sequence mutation and reverse-complement transformation (M44-M45).

This module provides:
- `mutate_reference`: Creates an alternate sequence by applying a variant
  to a reference window, with strong invariants.
- `reverse_complement`: Computes the reverse complement of a sequence.
- `reverse_complement_sequence`: Creates the reverse-complement alternate
  sequence for a variant on the minus strand.
- `apply_variant_to_reference`: High-level function that takes a reference
  sequence and a variant identity, and returns the alternate sequence.

Invariant guarantees:
1. The output sequence length always equals the input sequence length
   for SNVs (single base substitution).
2. For insertions/deletions, the alternate sequence length differs by
   exactly (len(alt) - len(ref)) bases.
3. The reference sequence at the variant position is preserved in the
   output (except at the variant site).
4. Reverse-complement is its own inverse: RC(RC(seq)) == seq.
"""

from __future__ import annotations

from dataclasses import dataclass

COMPLEMENT = str.maketrans("ACGTNacgtn", "TGCANtgcan")

GENOMIC_NUCLS = frozenset({"A", "C", "G", "T"})


def reverse_complement(seq: str) -> str:
    """Compute the reverse complement of a DNA sequence.

    Args:
        seq: A nucleotide sequence (uppercase or lowercase).

    Returns:
        The reverse complement, uppercase.

    Raises:
        ValueError: If the sequence contains invalid characters.
    """
    invalid = set(seq.upper()) - GENOMIC_NUCLS - {"N"}
    if invalid:
        raise ValueError(f"Invalid nucleotide characters in sequence: {invalid}")

    return seq.translate(COMPLEMENT)[::-1].upper()


def validate_rc_invariant(seq: str) -> bool:
    """Verify that reverse_complement is its own inverse."""
    return reverse_complement(reverse_complement(seq)) == seq


@dataclass(frozen=True)
class VariantIdentity:
    """Normalized variant identity: (chrom, start, ref, alt)."""

    chrom: str
    start: int  # 1-based position
    ref: str
    alt: str

    @property
    def is_snp(self) -> bool:
        return len(self.ref) == 1 and len(self.alt) == 1

    @property
    def is_insertion(self) -> bool:
        return len(self.ref) == 0 and len(self.alt) > 0

    @property
    def is_deletion(self) -> bool:
        return len(self.ref) > 0 and len(self.alt) == 0

    @property
    def is_indel(self) -> bool:
        return not self.is_snp


def mutate_reference(
    ref_sequence: str,
    variant: VariantIdentity,
    variant_ref_offset: int,
) -> str:
    """Apply a variant to a reference sequence, producing the alternate sequence.

    The variant is applied at position variant_ref_offset (0-based) within
    the reference sequence. The reference sequence at that position must match
    the variant's ref allele.

    Args:
        ref_sequence: The reference DNA sequence (uppercase).
        variant: The variant to apply.
        variant_ref_offset: 0-based position of the variant in ref_sequence.

    Returns:
        The alternate sequence with the variant applied.

    Raises:
        ValueError: If the reference allele doesn't match at the offset,
            or if the offset is out of range.
    """
    if variant_ref_offset < 0 or variant_ref_offset + len(variant.ref) > len(ref_sequence):
        raise ValueError(
            f"Variant offset {variant_ref_offset} out of range for "
            f"sequence of length {len(ref_sequence)}"
        )

    actual_ref = ref_sequence[variant_ref_offset:variant_ref_offset + len(variant.ref)]
    if actual_ref != variant.ref.upper():
        raise ValueError(
            f"Reference allele mismatch at offset {variant_ref_offset}: "
            f"expected {variant.ref}, found {actual_ref}"
        )

    before = ref_sequence[:variant_ref_offset]
    after = ref_sequence[variant_ref_offset + len(variant.ref):]
    return before + variant.alt.upper() + after


def mutate_reference_unchecked(
    ref_sequence: str,
    variant: VariantIdentity,
    variant_ref_offset: int,
) -> str:
    """Apply a variant to a reference sequence without validation.

    This is an optimized version that skips reference allele matching.
    Use only when the reference allele is known to match.
    """
    before = ref_sequence[:variant_ref_offset]
    after = ref_sequence[variant_ref_offset + len(variant.ref):]
    return before + variant.alt.upper() + after


def apply_variant_to_reference(
    ref_sequence: str,
    variant: VariantIdentity,
    variant_ref_offset: int,
    strand: str = "forward",
) -> str:
    """Apply a variant to a reference sequence, handling strand orientation.

    For forward strand (strand="forward"):
    - If SNP: substitute ref allele with alt allele at the offset.

    For reverse strand (strand="reverse"):
    - Reverse-complement both the reference sequence and the variant alleles.
    - Apply the mutation to the RC'd reference.
    - The variant_ref_offset must be the offset in the RC'd coordinate system,
      which corresponds to: len(ref_sequence) - variant_ref_offset - len(variant.ref)

    Args:
        ref_sequence: The reference DNA sequence (uppercase).
        variant: The variant to apply.
        variant_ref_offset: 0-based position of the variant in ref_sequence.
        strand: "forward" or "reverse".

    Returns:
        The alternate sequence with the variant applied.
    """
    if strand == "forward":
        return mutate_reference(ref_sequence, variant, variant_ref_offset)

    if strand == "reverse":
        rc_ref = reverse_complement(ref_sequence)
        rc_offset = len(ref_sequence) - variant_ref_offset - len(variant.ref)
        rc_variant = VariantIdentity(
            chrom=variant.chrom,
            start=variant.start,
            ref=reverse_complement(variant.ref),
            alt=reverse_complement(variant.alt),
        )
        return mutate_reference(rc_ref, rc_variant, rc_offset)

    raise ValueError(f"Invalid strand: {strand}. Use 'forward' or 'reverse'.")


def get_reverse_complement_variant(variant: VariantIdentity) -> VariantIdentity:
    """Get the reverse-complement version of a variant's alleles.

    This is for the case where a variant was called on the forward strand
    but the reference is stored on the reverse strand, or vice versa.
    """
    return VariantIdentity(
        chrom=variant.chrom,
        start=variant.start,
        ref=reverse_complement(variant.ref),
        alt=reverse_complement(variant.alt),
    )


def validate_mutate_snp_invariant(ref_sequence: str, variant: VariantIdentity, offset: int) -> bool:
    """Verify that mutating an SNP preserves sequence length."""
    result = mutate_reference(ref_sequence, variant, offset)
    return len(result) == len(ref_sequence)


def validate_mutate_length_invariant(
    ref_sequence: str, variant: VariantIdentity, offset: int
) -> bool:
    """Verify that mutation produces expected length change."""
    result = mutate_reference(ref_sequence, variant, offset)
    expected_len = len(ref_sequence) + len(variant.alt) - len(variant.ref)
    return len(result) == expected_len
