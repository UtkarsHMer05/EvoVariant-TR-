"""Tests for scorer.py and fake_scorer.py — Milestones 47-48."""

from __future__ import annotations

import pytest

from evovariant_tr.fake_scorer import FakeScorer
from evovariant_tr.scorer import ScoredVariant, Scorer, ScoringResult
from evovariant_tr.sequence_mutate import VariantIdentity
from evovariant_tr.sequence_window import ReferenceWindow

TEST_SEQ = "A" * 4096 + "CGT" + "T" * 4093
TEST_WINDOW = ReferenceWindow(
    chrom="chr1",
    start=46035,
    stop=54226,
    ref_sequence=TEST_SEQ,
    variant_offset=4096,
)
TEST_VARIANT = VariantIdentity(
    chrom="chr1", start=50000, ref="C", alt="T",
)


# --------------------------------------------------------------------------- #
# M47: Scorer interface
# --------------------------------------------------------------------------- #


def test_scorer_is_abstract():
    """Scorer should be abstract and not directly instantiable."""
    with pytest.raises(TypeError):
        Scorer()


def test_scorer_interface_methods():
    """Scorer subclasses must implement required methods."""
    methods = ["score_variant", "score_batch", "score_cohort", "check_health", "provenance"]
    for method in methods:
        assert hasattr(FakeScorer, method), f"Missing method: {method}"


def test_scored_variant_dataclass():
    v = ScoredVariant(
        identity=TEST_VARIANT,
        reference_window=TEST_WINDOW,
        reference_score=1.0,
        alternate_score=2.0,
        score_delta=1.0,
    )
    assert v.reference_score == 1.0
    assert v.alternate_score == 2.0
    assert v.score_delta == 1.0
    assert v.allele_likelihood is None


def test_scoring_result_dataclass():
    result = ScoringResult(
        scored=[],
        failed=[],
        total=0,
        batch_size=0,
        timing_ms=0.0,
        scorer_name="test",
        scorer_version="1.0",
    )
    assert result.total == 0
    assert result.scorer_name == "test"


def test_scorer_provenance():
    scorer = FakeScorer()
    prov = scorer.provenance()
    assert prov["scorer_name"] == "fake_scorer"
    assert prov["scorer_version"] == "0.1.0"
    assert prov["context_length_bp"] == 8192
    assert prov["deterministic"] is True


# --------------------------------------------------------------------------- #
# M48: Fake scorer
# --------------------------------------------------------------------------- #


def test_fake_scorer_score_variant():
    scorer = FakeScorer()
    ref_score, alt_score, delta = scorer.score_variant(
        TEST_WINDOW, TEST_VARIANT, strand="forward",
    )
    assert isinstance(ref_score, float)
    assert isinstance(alt_score, float)
    assert isinstance(delta, float)
    assert delta == alt_score - ref_score


def test_fake_scorer_deterministic():
    """Same input should always produce the same score."""
    scorer = FakeScorer()
    scores1 = scorer.score_variant(TEST_WINDOW, TEST_VARIANT)
    scores2 = scorer.score_variant(TEST_WINDOW, TEST_VARIANT)
    assert scores1 == scores2


def test_fake_scorer_range():
    """Scores should be in [-10, 10] by default."""
    scorer = FakeScorer(scale=10.0)
    ref_score, alt_score, delta = scorer.score_variant(
        TEST_WINDOW, TEST_VARIANT,
    )
    assert -10.0 <= ref_score <= 10.0
    assert -10.0 <= alt_score <= 10.0
    assert -20.0 <= delta <= 20.0


def test_fake_scorer_score_batch():
    scorer = FakeScorer()
    variants = [
        (TEST_WINDOW, TEST_VARIANT, "forward"),
        (TEST_WINDOW, VariantIdentity("chr1", 50001, "G", "A"), "forward"),
    ]
    result = scorer.score_batch(variants)
    assert result.total == 2
    assert result.batch_size == 2
    assert len(result.scored) == 2
    assert result.scorer_name == "fake_scorer"
    assert result.timing_ms >= 0.0


def test_fake_scorer_batch_deterministic():
    """Batch scoring should be deterministic."""
    scorer = FakeScorer()
    variants = [(TEST_WINDOW, TEST_VARIANT, "forward")]
    result1 = scorer.score_batch(variants)
    result2 = scorer.score_batch(variants)
    assert result1.scored[0].reference_score == result2.scored[0].reference_score
    assert result1.scored[0].alternate_score == result2.scored[0].alternate_score


def test_fake_scorer_check_health():
    scorer = FakeScorer()
    health = scorer.check_health()
    assert health["healthy"] is True
    assert health["scorer"] == "fake_scorer"


def test_fake_scorer_score_cohort_not_implemented():
    """FakeScorer should raise NotImplementedError for score_cohort."""
    scorer = FakeScorer()
    with pytest.raises(NotImplementedError):
        scorer.score_cohort([])


def test_fake_scorer_empty_sequence():
    """Empty reference sequence should return zeros."""
    scorer = FakeScorer()
    empty_window = ReferenceWindow(
        chrom="chr1", start=1, stop=8192,
        ref_sequence="", variant_offset=0,
    )
    ref_score, alt_score, delta = scorer.score_variant(empty_window, TEST_VARIANT)
    assert ref_score == 0.0
    assert alt_score == 0.0
    assert delta == 0.0


def test_fake_scorer_gc_content():
    """GC content metadata should be computed correctly."""
    scorer = FakeScorer()
    result = scorer.score_batch([(TEST_WINDOW, TEST_VARIANT, "forward")])
    gc = result.scored[0].metadata["gc_content"]
    # TEST_SEQ has "CGT" = 2 GC bases out of 8192
    assert gc == pytest.approx(3 / 8192, abs=0.001)
