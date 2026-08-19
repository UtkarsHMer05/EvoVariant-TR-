"""Tests for model_cache.py — Milestone 54."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from evovariant_tr.model_cache import (
    ModelCacheEntry,
    check_model_exists,
    create_cache_entry,
    get_cached_model_path,
    get_hf_cache_path,
    list_cached_models,
    model_cache_key,
)


def test_model_cache_key_deterministic():
    key1 = model_cache_key("evo2_7b")
    key2 = model_cache_key("evo2_7b")
    assert key1 == key2
    assert len(key1) == 16


def test_model_cache_key_different_revisions():
    key1 = model_cache_key("evo2_7b", "main")
    key2 = model_cache_key("evo2_7b", "v1.0")
    assert key1 != key2


def test_get_hf_cache_path():
    path = get_hf_cache_path()
    assert isinstance(path, str)
    assert "huggingface" in path


def test_check_model_exists_no_cache(tmp_path: Path):
    assert not check_model_exists(tmp_path / "cache", "evo2_7b")


def test_create_and_check_cache_entry(tmp_path: Path):
    cache_dir = tmp_path / "cache"
    model_path = tmp_path / "model.bin"
    model_path.write_text("dummy model data")

    entry = create_cache_entry(cache_dir, "evo2_7b", model_path)

    assert entry.model_name == "evo2_7b"
    assert entry.size_bytes > 0
    assert entry.version == "1.0.0"

    assert check_model_exists(cache_dir, "evo2_7b")
    cached_path = get_cached_model_path(cache_dir, "evo2_7b")
    assert cached_path is not None
    assert "models" in str(cached_path)


def test_get_cached_model_path_not_found(tmp_path: Path):
    assert get_cached_model_path(tmp_path / "cache", "nonexistent_model") is None


def test_list_cached_models_empty(tmp_path: Path):
    assert list_cached_models(tmp_path / "cache") == []


def test_list_cached_models_with_entries(tmp_path: Path):
    cache_dir = tmp_path / "cache"
    model_path = tmp_path / "model.bin"
    model_path.write_text("data")

    create_cache_entry(cache_dir, "evo2_7b", model_path)
    create_cache_entry(cache_dir, "evo2_70m", model_path)

    models = list_cached_models(cache_dir)
    assert len(models) == 2
    names = {m["model_name"] for m in models}
    assert "evo2_7b" in names
    assert "evo2_70m" in names


def test_cache_entry_to_dict():
    entry = ModelCacheEntry(
        model_name="evo2_7b",
        model_path="/models/evo2_7b",
        model_sha256="abc123",
        created_at=datetime.now(UTC).isoformat(),
        size_bytes=1024,
        version="1.0.0",
    )
    d = entry.to_dict()
    assert d["model_name"] == "evo2_7b"
    assert d["size_bytes"] == 1024
    assert d["version"] == "1.0.0"
    assert "model_sha256" in d
    assert "created_at" in d

    json.dumps(d)  # Should be serializable
