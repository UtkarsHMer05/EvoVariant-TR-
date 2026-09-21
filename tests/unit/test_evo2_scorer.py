"""Tests for evo2_scorer.py — Milestone 49."""

from __future__ import annotations

import json

import pytest

from evovariant_tr import evo2_scorer as evo2_scorer_module
from evovariant_tr.evo2_scorer import (
    PARITY_REQUIREMENTS,
    Evo2Scorer,
    Evo2ScorerConfig,
    check_evo2_parity,
)
from evovariant_tr.sequence_mutate import VariantIdentity
from evovariant_tr.sequence_window import ReferenceWindow


def test_parity_requirements():
    assert PARITY_REQUIREMENTS["context_length_bp"] == 8192
    assert PARITY_REQUIREMENTS["assembly"] == "GRCh38"
    assert PARITY_REQUIREMENTS["model"] == "evo2_7b"
    assert PARITY_REQUIREMENTS["precision"] == "bfloat16"
    assert PARITY_REQUIREMENTS["min_vram_gb"] == 24


def test_config_defaults():
    cfg = Evo2ScorerConfig()
    assert cfg.model_name == "evo2_7b"
    assert cfg.context_length_bp == 8192
    assert cfg.precision == "bfloat16"
    assert cfg.batch_size == 128
    assert cfg.device == "cuda"


def test_config_custom():
    cfg = Evo2ScorerConfig(model_name="evo2_70m", batch_size=32)
    assert cfg.model_name == "evo2_70m"
    assert cfg.batch_size == 32


def test_evo2_scorer_raises_without_torch():
    """Evo2Scorer should raise RuntimeError when torch is not available."""
    if __import__("sys").modules.get("torch"):
        pytest.skip("torch is available in this environment")
    with pytest.raises(RuntimeError, match="torch is not available"):
        Evo2Scorer()


def test_evo2_scorer_name_and_version():
    assert Evo2Scorer.name == "evo2_scorer"
    assert Evo2Scorer.version == "1.0.0"
    assert Evo2Scorer.context_length_bp == 8192


def test_check_evo2_parity_without_torch():
    """check_evo2_parity should skip torch checks when torch is unavailable."""
    result = check_evo2_parity()
    assert "all_pass" in result
    assert "checks" in result
    assert "parity_requirements" in result
    assert result["parity_requirements"]["context_length_bp"] == 8192

    # Should have torch_available check
    torch_check = next(c for c in result["checks"] if c["name"] == "torch_available")
    if torch_check["status"] == "SKIP":
        # torch not available, should return early
        assert len(result["checks"]) == 1
        assert result["all_pass"] is True


def test_check_evo2_parity_returns_json():
    result = check_evo2_parity()
    json_str = json.dumps(result)
    assert "context_length_bp" in json_str


def test_evo2_batch_uses_model_batches_and_preserves_row_mapping(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The adapter must submit sequence chunks, not one request per row."""

    class FakeModel:
        def __init__(self) -> None:
            self.calls: list[list[str]] = []

        def score_sequences(self, sequences: list[str]) -> list[float]:
            self.calls.append(list(sequences))
            return [float(sum(ord(base) for base in sequence)) for sequence in sequences]

    sequence = "A" * 4096 + "CGT" + "T" * 4093
    window = ReferenceWindow(
        chrom="chr1",
        start=46035,
        stop=54226,
        ref_sequence=sequence,
        variant_offset=4096,
    )
    window_second = ReferenceWindow(
        chrom="chr1",
        start=46035,
        stop=54226,
        ref_sequence=sequence,
        variant_offset=4097,
    )
    variants = [
        (
            window,
            VariantIdentity("chr1", 50131, "C", "T"),
            "forward",
        ),
        (
            window_second,
            VariantIdentity("chr1", 50132, "G", "A"),
            "reverse",
        ),
    ]
    fake_model = FakeModel()
    scorer = object.__new__(Evo2Scorer)
    scorer._config = Evo2ScorerConfig(batch_size=3)
    scorer._model = fake_model
    monkeypatch.setattr(evo2_scorer_module, "EV2_AVAILABLE", True)

    result = scorer.score_batch(variants)

    assert result.total == 2
    assert result.failed == []
    assert len(result.scored) == 2
    assert [len(call) for call in fake_model.calls] == [3, 1]
    assert result.scored[0].identity.start == 50131
    assert result.scored[1].identity.start == 50132
    assert result.scored[0].metadata["model_batch_size"] == 3
    assert all(
        item.score_delta == item.alternate_score - item.reference_score
        for item in result.scored
    )
