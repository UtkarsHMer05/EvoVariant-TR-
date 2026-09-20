"""Tests for protocol-complete content-addressed cache identity."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import evovariant_tr.cache_identity as cache_identity_module
from evovariant_tr.cache_identity import CacheIdentity, ContentAddressedCache


def _identity() -> CacheIdentity:
    return CacheIdentity(
        model_id="evo2",
        checkpoint="evo2_7b",
        model_revision="4b509ec2",
        preprocessing_revision="window-v2",
        assembly="GRCh38",
        context_length_bp=8192,
        orientation="forward",
        layer="raw_score",
        normalized_variant_id="GRCh38:7:100:A>T",
    )


def test_identity_is_deterministic_and_dimension_complete() -> None:
    identity = _identity()
    assert identity.key() == _identity().key()
    changed = CacheIdentity(**{**identity.canonical(), "orientation": "reverse"})
    assert changed.key() != identity.key()


def test_cache_put_get_and_get_or_put(tmp_path: Path) -> None:
    cache = ContentAddressedCache(tmp_path / "cache")
    identity = _identity()
    first, hit = cache.get_or_put(identity, lambda: {"delta": 1.25})
    second, second_hit = cache.get_or_put(
        identity,
        lambda: {"delta": 999},
    )
    assert hit is False
    assert second_hit is True
    assert first.payload == {"delta": 1.25}
    assert second.payload == first.payload
    loaded = cache.get(identity)
    assert loaded is not None
    assert loaded.key == identity.key()
    assert len(list((tmp_path / "cache").rglob("*.json"))) == 1


def test_cache_rejects_tampered_payload_and_identity(tmp_path: Path) -> None:
    cache = ContentAddressedCache(tmp_path / "cache")
    identity = _identity()
    cache.put(identity, {"delta": 1.25})
    path = next((tmp_path / "cache").rglob("*.json"))
    data = json.loads(path.read_text(encoding="utf-8"))
    data["payload"]["delta"] = 9.0
    path.write_text(json.dumps(data), encoding="utf-8")
    assert cache.get(identity) is None

    data = json.loads(path.read_text(encoding="utf-8"))
    data["identity"]["orientation"] = "reverse"
    path.write_text(json.dumps(data), encoding="utf-8")
    assert cache.get(identity) is None


def test_cache_removes_temporary_file_when_replace_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cache = ContentAddressedCache(tmp_path / "cache")

    def fail_replace(_source: str, _target: Path) -> None:
        raise OSError("simulated replace failure")

    monkeypatch.setattr(cache_identity_module.os, "replace", fail_replace)
    with pytest.raises(OSError, match="simulated replace failure"):
        cache.put(_identity(), {"delta": 1.25})
    assert not any(path.is_file() for path in (tmp_path / "cache").rglob("*"))


def test_cache_rejects_non_mapping_factory(tmp_path: Path) -> None:
    cache = ContentAddressedCache(tmp_path / "cache")
    try:
        cache.get_or_put(_identity(), lambda: ["not", "a", "mapping"])
    except TypeError as exc:
        assert "dictionary" in str(exc)
    else:
        raise AssertionError("non-mapping cache payload should fail")
