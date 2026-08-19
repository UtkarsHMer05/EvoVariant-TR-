"""Tests for sequence_cache.py — Milestone 46."""

from __future__ import annotations

from pathlib import Path

from evovariant_tr.sequence_cache import CacheEntry, SequenceCache


def _make_mock_fasta(tmp_path: Path) -> tuple[Path, Path]:
    """Create a mock FASTA with chr1 (10000 A's with C at pos 5000)."""
    fasta = tmp_path / "ref.fasta"
    seq = list("A" * 10000)
    seq[4999] = "C"
    seq = "".join(seq)

    fasta.write_text(">chr1\n")
    with fasta.open("a") as f:
        for i in range(0, len(seq), 70):
            f.write(seq[i:i + 70] + "\n")

    fai = tmp_path / "ref.fasta.fai"
    fai.write_text("chr1\t10000\t6\t70\t71\t0\n")
    return fasta, fai


def test_cache_entry_creation():
    entry = CacheEntry(
        key="abc123",
        chrom="chr1",
        variant_pos=5000,
        window_start=1,
        window_stop=8192,
        variant_offset=4095,
        ref_sequence="A" * 8192,
        ref_fasta_path="/path/to/ref.fasta",
        ref_fasta_sha256="def456",
        created_at="2026-08-19T00:00:00+00:00",
    )
    assert entry.chrom == "chr1"
    assert entry.variant_pos == 5000
    d = entry.to_dict()
    assert d["key"] == "abc123"
    assert "ref_sequence_sha256" in d
    assert d["ref_sequence_length"] == 8192


def test_sequence_cache_init(tmp_path: Path):
    cache = SequenceCache(tmp_path / "cache")
    assert cache.cache_dir.exists()
    assert cache.size() == 0


def test_sequence_cache_get_or_compute(
    tmp_path: Path,
):
    fasta, fai = _make_mock_fasta(tmp_path)
    cache = SequenceCache(tmp_path / "cache")

    entry = cache.get_or_compute(
        "chr1", 5000, fasta, fai,
    )

    assert entry.chrom == "chr1"
    assert entry.variant_pos == 5000
    assert entry.window_start > 0
    assert entry.window_stop <= 10000
    assert entry.variant_offset >= 0
    assert len(entry.ref_sequence) > 0


def test_sequence_cache_get_existing(tmp_path: Path):
    fasta, fai = _make_mock_fasta(tmp_path)
    cache = SequenceCache(tmp_path / "cache")

    # First call computes and stores
    entry1 = cache.get_or_compute("chr1", 5000, fasta, fai)

    # Second call should return cached entry
    entry2 = cache.get("chr1", 5000)
    assert entry2 is not None
    assert entry2.key == entry1.key
    assert entry2.ref_sequence == entry1.ref_sequence


def test_sequence_cache_put_and_get(tmp_path: Path):
    cache = SequenceCache(tmp_path / "cache")

    entry = CacheEntry(
        key="test_key",
        chrom="chr1",
        variant_pos=100,
        window_start=1,
        window_stop=8192,
        variant_offset=99,
        ref_sequence="A" * 8192,
        ref_fasta_path="/path/to/ref.fasta",
        ref_fasta_sha256="abc",
        created_at="2026-08-19T00:00:00+00:00",
    )
    cache.put(entry)

    # get computes key from (chrom, pos, context_length)
    # entry was created with default context_length_bp = CONTEXT_LENGTH_BP
    retrieved = cache.get("chr1", 100)
    assert retrieved is not None
    assert retrieved.window_start == 1
    assert retrieved.variant_pos == 100


def test_sequence_cache_size(tmp_path: Path):
    cache = SequenceCache(tmp_path / "cache")
    assert cache.size() == 0

    fasta, fai = _make_mock_fasta(tmp_path)
    cache.get_or_compute("chr1", 5000, fasta, fai)
    assert cache.size() >= 1


def test_sequence_cache_provenance(tmp_path: Path):
    cache = SequenceCache(tmp_path / "cache")
    prov = cache.provenance()
    assert "cache_dir" in prov
    assert "entry_count" in prov
    assert prov["entry_count"] == 0