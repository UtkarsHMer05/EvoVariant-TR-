"""Scientific invariant tests for canonical orientation scoring."""

from __future__ import annotations

import pytest

from evovariant_tr.fake_scorer import FakeScorer
from evovariant_tr.scorer import score_orientations
from evovariant_tr.sequence_mutate import VariantIdentity
from evovariant_tr.sequence_window import ReferenceWindow


def make_window(ref: str = "A") -> ReferenceWindow:
    return ReferenceWindow(
        chrom="chr1",
        start=1,
        stop=8192,
        ref_sequence="C" * 4095 + ref + "G" * 4096,
        variant_offset=4095,
    )


def test_score_orientations_retains_forward_and_reverse_components() -> None:
    scorer = FakeScorer(scale=1.0)
    variant = VariantIdentity("chr1", 4096, "A", "T")
    pair = score_orientations(scorer, make_window(), variant)
    assert pair.forward is not None
    assert pair.reverse is not None
    assert pair.delta_primary == pytest.approx(
        (pair.forward.delta + pair.reverse.delta) / 2
    )
    assert pair.abs_disagreement is not None


def test_score_orientations_rejects_reference_mismatch() -> None:
    scorer = FakeScorer(scale=1.0)
    variant = VariantIdentity("chr1", 4096, "T", "A")
    with pytest.raises(ValueError, match="reference allele mismatch"):
        score_orientations(scorer, make_window(), variant)


def test_score_orientations_rejects_variable_length_window() -> None:
    scorer = FakeScorer(scale=1.0)
    variant = VariantIdentity("chr1", 4096, "A", "T")
    window = ReferenceWindow("chr1", 1, 8191, "A" * 8191, 4095)
    with pytest.raises(ValueError, match="window length"):
        score_orientations(scorer, window, variant)
