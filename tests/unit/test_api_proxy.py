"""Tests for explicit-dependency API proxy helpers."""

from __future__ import annotations

import pytest

from evovariant_tr.api_proxy import (
    configure_scorer,
    get_health,
    get_protocol_info,
    score_variant_handler,
)
from evovariant_tr.fake_scorer import FakeScorer


def test_proxy_reports_unconfigured_without_fabricating_health() -> None:
    configure_scorer(None)
    health = get_health()
    assert health["status"] == "unavailable"
    assert health["scorer"] == "unconfigured"
    assert get_protocol_info()["scorer"] == "unconfigured"
    with pytest.raises(RuntimeError, match="no real research scorer"):
        score_variant_handler("chr1", 10, "A", "T")


def test_proxy_uses_explicit_fake_only_when_injected() -> None:
    configure_scorer(FakeScorer(scale=1.0))
    assert get_health()["status"] == "healthy"
    result = score_variant_handler("1", 10, "A", "T")
    assert result["normalized_variant_id"] == "GRCh38:chr1:10:A>T"
    assert result["delta_forward"] is not None
    assert result["delta_reverse"] is not None
    assert result["provenance"]["classification"] == "not_provided"
