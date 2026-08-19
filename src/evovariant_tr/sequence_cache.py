"""Deterministic sequence cache for EvoVariant-TR (Milestone 46).

Provides a content-addressed cache for reference sequence windows and
provenance records. Each cache entry is keyed by a SHA-256 hash of:
- chromosome, position, and context_length_bp

This ensures that the same variant always resolves to the same reference
sequence, regardless of when or where it's fetched.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from evovariant_tr.sequence_window import (
    CONTEXT_LENGTH_BP,
)


def _cache_key(chrom: str, pos: int, context_length: int = CONTEXT_LENGTH_BP) -> str:
    """Generate a deterministic cache key for a variant position."""
    raw = f"{chrom}:{pos}:{context_length}".encode()
    return hashlib.sha256(raw).hexdigest()


@dataclass
class CacheEntry:
    """A single cache entry with provenance."""

    key: str
    chrom: str
    variant_pos: int
    window_start: int
    window_stop: int
    variant_offset: int
    ref_sequence: str
    ref_fasta_path: str
    ref_fasta_sha256: str
    created_at: str
    context_length_bp: int = CONTEXT_LENGTH_BP

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "chrom": self.chrom,
            "variant_pos": self.variant_pos,
            "window_start": self.window_start,
            "window_stop": self.window_stop,
            "variant_offset": self.variant_offset,
            "ref_sequence_sha256": hashlib.sha256(
                self.ref_sequence.encode()
            ).hexdigest(),
            "ref_sequence_length": len(self.ref_sequence),
            "ref_fasta_path": self.ref_fasta_path,
            "ref_fasta_sha256": self.ref_fasta_sha256,
            "created_at": self.created_at,
            "context_length_bp": self.context_length_bp,
        }


class SequenceCache:
    """Content-addressed cache for reference sequence windows.

    Stores reference windows on disk, keyed by (chrom, position, context_len).
    Each entry includes provenance metadata.
    """

    def __init__(self, cache_dir: str | Path) -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._index = self._load_index()

    def _index_path(self) -> Path:
        return self.cache_dir / "cache_index.json"

    def _entry_path(self, key: str) -> Path:
        return self.cache_dir / "entries" / f"{key[:2]}" / f"{key}.json"

    def _load_index(self) -> dict[str, str]:
        """Load the cache index (key -> filepath)."""
        index_path = self._index_path()
        if not index_path.exists():
            return {}
        data = json.loads(index_path.read_text())
        return dict(data)

    def _save_index(self) -> None:
        """Save the cache index."""
        index_path = self._index_path()
        index_path.write_text(json.dumps(self._index, indent=2))

    def get(
        self, chrom: str, pos: int, context_length: int = CONTEXT_LENGTH_BP
    ) -> CacheEntry | None:
        """Look up a cache entry by key."""
        key = _cache_key(chrom, pos, context_length)
        entry_path_str = self._index.get(key)
        if entry_path_str is None:
            return None
        entry_path = Path(entry_path_str)
        if not entry_path.exists():
            return None
        data = json.loads(entry_path.read_text())
        return CacheEntry(
            key=data["key"],
            chrom=data["chrom"],
            variant_pos=data["variant_pos"],
            window_start=data["window_start"],
            window_stop=data["window_stop"],
            variant_offset=data["variant_offset"],
            ref_sequence=data["ref_sequence"],
            ref_fasta_path=data["ref_fasta_path"],
            ref_fasta_sha256=data["ref_fasta_sha256"],
            created_at=data["created_at"],
            context_length_bp=data.get("context_length_bp", CONTEXT_LENGTH_BP),
        )

    def put(self, entry: CacheEntry) -> None:
        """Store a cache entry."""
        # Use the entry's key, but also update the index
        entry_path = self._entry_path(entry.key)
        entry_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "key": entry.key,
            "chrom": entry.chrom,
            "variant_pos": entry.variant_pos,
            "window_start": entry.window_start,
            "window_stop": entry.window_stop,
            "variant_offset": entry.variant_offset,
            "ref_sequence": entry.ref_sequence,
            "ref_fasta_path": entry.ref_fasta_path,
            "ref_fasta_sha256": entry.ref_fasta_sha256,
            "created_at": entry.created_at,
            "context_length_bp": entry.context_length_bp,
        }
        entry_path.write_text(json.dumps(data, indent=2))
        # Update index: map (chrom:pos:context_len) -> key
        computed_key = _cache_key(entry.chrom, entry.variant_pos, entry.context_length_bp)
        self._index[computed_key] = str(entry_path)
        self._save_index()

    def get_or_compute(
        self,
        chrom: str,
        pos: int,
        ref_fasta: str | Path,
        ref_fai: str | Path,
        context_length: int = CONTEXT_LENGTH_BP,
        ref_fasta_sha256: str = "",
    ) -> CacheEntry:
        """Get a cache entry, computing and storing it if not present."""
        existing = self.get(chrom, pos, context_length)
        if existing is not None:
            return existing

        from evovariant_tr.sequence_window import generate_reference_window

        window = generate_reference_window(
            Path(ref_fasta), Path(ref_fai), chrom, pos,
        )

        key = _cache_key(chrom, pos, context_length)
        entry = CacheEntry(
            key=key,
            chrom=chrom,
            variant_pos=pos,
            window_start=window.start,
            window_stop=window.stop,
            variant_offset=window.variant_offset,
            ref_sequence=window.ref_sequence,
            ref_fasta_path=str(ref_fasta),
            ref_fasta_sha256=ref_fasta_sha256,
            created_at=datetime.now(UTC).isoformat(),
            context_length_bp=context_length,
        )
        self.put(entry)
        return entry

    def size(self) -> int:
        """Return the number of entries in the cache."""
        return len(self._index)

    def keys(self) -> list[str]:
        """Return all cache keys."""
        return list(self._index.keys())

    def provenance(self) -> dict[str, Any]:
        """Return provenance metadata for the cache."""
        return {
            "cache_dir": str(self.cache_dir),
            "entry_count": self.size(),
            "index_path": str(self._index_path()),
        }
