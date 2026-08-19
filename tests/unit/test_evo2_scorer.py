"""Tests for evo2_scorer.py — Milestone 49."""

from __future__ import annotations

import json

import pytest

from evovariant_tr.evo2_scorer import (
    PARITY_REQUIREMENTS,
    Evo2Scorer,
    Evo2ScorerConfig,
    check_evo2_parity,
)


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
