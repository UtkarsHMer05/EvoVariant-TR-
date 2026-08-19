"""Persistent model-cache storage on Modal (Milestone 54).

Provides utilities for managing persistent model weights on Modal volumes,
ensuring models are cached across runs for efficiency.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass
class ModelCacheEntry:
    """Metadata for a cached model."""

    model_name: str
    model_path: str
    model_sha256: str
    created_at: str
    size_bytes: int
    version: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_name": self.model_name,
            "model_path": self.model_path,
            "model_sha256": self.model_sha256,
            "created_at": self.created_at,
            "size_bytes": self.size_bytes,
            "version": self.version,
        }


def get_hf_cache_path() -> str:
    """Get the HuggingFace cache path from environment or default."""
    return os.environ.get("HF_CACHE_DIR", "/root/.cache/huggingface")


def model_cache_key(model_name: str, revision: str = "main") -> str:
    """Generate a deterministic cache key for a model."""
    raw = f"{model_name}:{revision}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def check_model_exists(
    cache_dir: str | Path,
    model_name: str,
    revision: str = "main",
) -> bool:
    """Check if a model is already cached."""
    cache_key = model_cache_key(model_name, revision)
    entry_path = Path(cache_dir) / "models" / cache_key / "model_info.json"
    return entry_path.exists()


def get_cached_model_path(
    cache_dir: str | Path,
    model_name: str,
    revision: str = "main",
) -> Path | None:
    """Get the path to a cached model, or None if not cached."""
    if not check_model_exists(cache_dir, model_name, revision):
        return None
    cache_key = model_cache_key(model_name, revision)
    return Path(cache_dir) / "models" / cache_key


def create_cache_entry(
    cache_dir: str | Path,
    model_name: str,
    model_path: Path,
    revision: str = "main",
    version: str = "1.0.0",
) -> ModelCacheEntry:
    """Create a cache entry for a newly downloaded model."""
    cache_key = model_cache_key(model_name, revision)
    cache_entry_dir = Path(cache_dir) / "models" / cache_key
    cache_entry_dir.mkdir(parents=True, exist_ok=True)

    size_bytes = model_path.stat().st_size

    entry = ModelCacheEntry(
        model_name=model_name,
        model_path=str(model_path),
        model_sha256="",
        created_at=datetime.now(UTC).isoformat(),
        size_bytes=size_bytes,
        version=version,
    )

    info_path = cache_entry_dir / "model_info.json"
    info_path.write_text(json.dumps(entry.to_dict(), indent=2))
    return entry


def list_cached_models(cache_dir: str | Path) -> list[dict[str, Any]]:
    """List all cached models."""
    models_dir = Path(cache_dir) / "models"
    if not models_dir.exists():
        return []

    entries = []
    for entry_dir in models_dir.iterdir():
        info_path = entry_dir / "model_info.json"
        if info_path.exists():
            entries.append(json.loads(info_path.read_text()))
    return entries