"""Deterministic file manifest and hashing tests (Milestone 15).

Acceptance validations:
- Validation 1: one-bit corruption fails verification.
- Validation 2: manifest order and serialization are deterministic.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import subprocess
import sys
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from evovariant_tr.manifest import (
    CompressionType,
    Manifest,
    ManifestEntry,
    ManifestError,
    build_entry,
    build_manifest,
    detect_compression,
    load_manifest,
    manifest_to_json,
    sanitize_source_url,
    streaming_sha256,
    streaming_uncompressed_sha256,
    verify_manifest,
    verify_or_raise,
    write_manifest,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
VERIFY_CLI = REPO_ROOT / "scripts" / "verify_manifest.py"
FIXED_TIME = datetime(2026, 8, 18, 12, 0, 0, tzinfo=UTC)


def flip_one_bit(path: Path) -> None:
    data = bytearray(path.read_bytes())
    data[len(data) // 2] ^= 0x01
    path.write_bytes(bytes(data))


@pytest.fixture()
def asset_tree(tmp_path: Path) -> Path:
    base = tmp_path / "data" / "raw"
    base.mkdir(parents=True)
    (base / "clinvar_t0.txt").write_text("variant\tgene\tclass\n1\tBRCA1\tVUS\n", encoding="utf-8")
    (base / "clinvar_t0.txt.gz").write_bytes(
        gzip.compress(b"variant\tgene\tclass\n1\tBRCA1\tVUS\n")
    )
    (base / "notes.md").write_text("# notes\n", encoding="utf-8")
    return base


# ---------------------------------------------------------------------------
# Streaming SHA-256
# ---------------------------------------------------------------------------


def test_streaming_sha256_matches_hashlib(asset_tree: Path) -> None:
    target = asset_tree / "clinvar_t0.txt"
    expected = hashlib.sha256(target.read_bytes()).hexdigest()
    assert streaming_sha256(target) == expected
    # Tiny chunk size exercises the streaming loop.
    assert streaming_sha256(target, chunk_size=3) == expected


def test_streaming_uncompressed_sha256_gzip(asset_tree: Path) -> None:
    plain = (asset_tree / "clinvar_t0.txt").read_bytes()
    expected = hashlib.sha256(plain).hexdigest()
    result = streaming_uncompressed_sha256(asset_tree / "clinvar_t0.txt.gz", CompressionType.GZIP)
    assert result == (expected, len(plain))


def test_streaming_uncompressed_sha256_none_for_zip_and_zstd(asset_tree: Path) -> None:
    target = asset_tree / "clinvar_t0.txt"
    assert streaming_uncompressed_sha256(target, CompressionType.ZIP) is None
    assert streaming_uncompressed_sha256(target, CompressionType.ZSTD) is None


def test_compression_detection() -> None:
    assert detect_compression("x.txt") is CompressionType.NONE
    assert detect_compression("x.txt.gz") is CompressionType.GZIP
    assert detect_compression("x.zip") is CompressionType.ZIP
    assert detect_compression("x.tar.zst") is CompressionType.ZSTD


# ---------------------------------------------------------------------------
# Source URL sanitization: no secrets embedded
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw,expected",
    [
        (
            "https://user:pass@ftp.ncbi.nlm.nih.gov/clinvar/archive/2025/variant_summary.txt.gz",
            "https://ftp.ncbi.nlm.nih.gov/clinvar/archive/2025/variant_summary.txt.gz",
        ),
        (
            "https://example.org/data?token=abc123&release=2025-01",
            "https://example.org/data?release=2025-01",
        ),
        (
            "https://example.org/data?API_KEY=zzz&Signature=sig9&keep=1",
            "https://example.org/data?keep=1",
        ),
        (
            "https://example.org/plain/path",
            "https://example.org/plain/path",
        ),
    ],
)
def test_sanitize_source_url(raw: str, expected: str) -> None:
    assert sanitize_source_url(raw) == expected


def test_sanitize_never_leaks_secret_values() -> None:
    sanitized = sanitize_source_url(
        "https://u:p@example.org/x?token=SUPERSECRET&password=hunter2&ok=1"
    )
    assert "SUPERSECRET" not in sanitized
    assert "hunter2" not in sanitized
    assert "u:p" not in sanitized and ":p@" not in sanitized
    assert "ok=1" in sanitized


# ---------------------------------------------------------------------------
# Entry building: retrieval time separate from release date
# ---------------------------------------------------------------------------


def test_build_entry_records_both_dates_separately(asset_tree: Path) -> None:
    entry = build_entry(
        "clinvar_t0.txt.gz",
        asset_tree,
        source_url="https://ftp.ncbi.nlm.nih.gov/clinvar/archive/2025/variant_summary.txt.gz",
        release_date=date(2025, 1, 2),
        retrieved_at=FIXED_TIME,
        description="ClinVar t0 variant_summary",
    )
    assert entry.release_date == date(2025, 1, 2)
    assert entry.retrieved_at == FIXED_TIME.isoformat()
    assert entry.release_date.isoformat() not in (entry.retrieved_at or "")
    assert entry.compression is CompressionType.GZIP
    assert entry.uncompressed_sha256 is not None
    assert entry.size_bytes == (asset_tree / "clinvar_t0.txt.gz").stat().st_size


def test_build_entry_missing_file_raises(asset_tree: Path) -> None:
    with pytest.raises(ManifestError, match="not found"):
        build_entry("nope.txt", asset_tree)


def test_entry_rejects_bad_hash_and_absolute_path() -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ManifestEntry(
            path="x.txt",
            sha256="XYZ",
            size_bytes=1,
            compression=CompressionType.NONE,
            uncompressed_sha256=None,
            uncompressed_size_bytes=None,
            source_url=None,
            release_date=None,
            retrieved_at=None,
            description=None,
        )
    with pytest.raises(ValidationError):
        ManifestEntry(
            path="/etc/passwd",
            sha256="a" * 64,
            size_bytes=1,
            compression=CompressionType.NONE,
            uncompressed_sha256=None,
            uncompressed_size_bytes=None,
            source_url=None,
            release_date=None,
            retrieved_at=None,
            description=None,
        )


# ---------------------------------------------------------------------------
# Validation 2: deterministic order and serialization
# ---------------------------------------------------------------------------


def test_manifest_order_and_serialization_are_deterministic(asset_tree: Path) -> None:
    entries_a = [
        build_entry("notes.md", asset_tree),
        build_entry("clinvar_t0.txt", asset_tree),
        build_entry("clinvar_t0.txt.gz", asset_tree),
    ]
    entries_b = list(reversed(entries_a))
    manifest_a = build_manifest("test_assets", asset_tree, entries_a, created_at=FIXED_TIME)
    manifest_b = build_manifest("test_assets", asset_tree, entries_b, created_at=FIXED_TIME)
    assert manifest_a == manifest_b
    assert manifest_to_json(manifest_a) == manifest_to_json(manifest_b)
    # Entries are sorted by path regardless of input order.
    assert [entry.path for entry in manifest_a.entries] == sorted(
        entry.path for entry in manifest_a.entries
    )
    # Byte-for-byte stable across repeated serialization.
    assert manifest_to_json(manifest_a) == manifest_to_json(manifest_a)


def test_duplicate_paths_rejected(asset_tree: Path) -> None:
    entry = build_entry("notes.md", asset_tree)
    with pytest.raises(ManifestError, match="duplicate"):
        build_manifest("dup", asset_tree, [entry, entry], created_at=FIXED_TIME)


def test_write_load_round_trip(asset_tree: Path, tmp_path: Path) -> None:
    entries = [build_entry("notes.md", asset_tree), build_entry("clinvar_t0.txt", asset_tree)]
    manifest = build_manifest("round_trip", asset_tree, entries, created_at=FIXED_TIME)
    path = write_manifest(manifest, tmp_path / "manifests" / "round_trip.json")
    assert load_manifest(path) == manifest
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["manifest_version"] == "1.0"


# ---------------------------------------------------------------------------
# Validation 1: one-bit corruption fails verification
# ---------------------------------------------------------------------------


def test_clean_manifest_verifies(asset_tree: Path) -> None:
    entries = [
        build_entry("clinvar_t0.txt", asset_tree),
        build_entry("clinvar_t0.txt.gz", asset_tree),
        build_entry("notes.md", asset_tree),
    ]
    manifest = build_manifest("clean", asset_tree, entries, created_at=FIXED_TIME)
    assert verify_manifest(manifest, asset_tree) == []
    verify_or_raise(manifest, asset_tree)  # must not raise


def test_one_bit_corruption_fails_verification(asset_tree: Path) -> None:
    target = asset_tree / "clinvar_t0.txt"
    manifest = build_manifest(
        "corruptible",
        asset_tree,
        [build_entry("clinvar_t0.txt", asset_tree)],
        created_at=FIXED_TIME,
    )
    flip_one_bit(target)
    failures = verify_manifest(manifest, asset_tree)
    assert len(failures) == 1
    assert failures[0].path == "clinvar_t0.txt"
    assert failures[0].kind in {"HASH_MISMATCH", "SIZE_MISMATCH"}
    with pytest.raises(ManifestError, match="verification failed"):
        verify_or_raise(manifest, asset_tree)


def test_gzip_payload_corruption_detected_via_uncompressed_hash(asset_tree: Path) -> None:
    gz_path = asset_tree / "clinvar_t0.txt.gz"
    entry = build_entry("clinvar_t0.txt.gz", asset_tree)
    # Re-compress different content to the same stored size is unreliable, so
    # corrupt the stored bytes directly: stored hash changes, and if sizes
    # happened to match the uncompressed check would still catch it.
    flip_one_bit(gz_path)
    manifest = Manifest(
        manifest_version="1.0",
        name="gz_corrupt",
        created_at=FIXED_TIME.isoformat(),
        entries=(entry,),
    )
    failures = verify_manifest(manifest, asset_tree)
    assert len(failures) == 1
    assert failures[0].kind in {"HASH_MISMATCH", "SIZE_MISMATCH", "UNCOMPRESSED_MISMATCH"}


def test_missing_file_reported(asset_tree: Path) -> None:
    entry = build_entry("notes.md", asset_tree)
    manifest = Manifest(
        manifest_version="1.0",
        name="missing",
        created_at=FIXED_TIME.isoformat(),
        entries=(entry,),
    )
    (asset_tree / "notes.md").unlink()
    failures = verify_manifest(manifest, asset_tree)
    assert [failure.kind for failure in failures] == ["MISSING"]


def test_wrong_uncompressed_hash_reported(asset_tree: Path) -> None:
    entry = build_entry("clinvar_t0.txt.gz", asset_tree)
    forged = ManifestEntry.model_validate(
        {**entry.model_dump(mode="json"), "uncompressed_sha256": "b" * 64}
    )
    manifest = Manifest(
        manifest_version="1.0",
        name="forged_uncompressed",
        created_at=FIXED_TIME.isoformat(),
        entries=(forged,),
    )
    failures = verify_manifest(manifest, asset_tree)
    assert [failure.kind for failure in failures] == ["UNCOMPRESSED_MISMATCH"]


# ---------------------------------------------------------------------------
# verify-manifest CLI
# ---------------------------------------------------------------------------


def run_cli(manifest: Path, base_dir: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VERIFY_CLI), "--manifest", str(manifest), "--base-dir", str(base_dir)],
        capture_output=True,
        text=True,
        check=False,
    )


def test_cli_exit_codes(asset_tree: Path, tmp_path: Path) -> None:
    manifest_path = write_manifest(
        build_manifest(
            "cli_test",
            asset_tree,
            [build_entry("notes.md", asset_tree)],
            created_at=FIXED_TIME,
        ),
        tmp_path / "manifest.json",
    )
    ok = run_cli(manifest_path, asset_tree)
    assert ok.returncode == 0
    assert "OK" in ok.stdout

    flip_one_bit(asset_tree / "notes.md")
    bad = run_cli(manifest_path, asset_tree)
    assert bad.returncode == 1
    assert "FAIL" in bad.stdout

    missing = run_cli(tmp_path / "nope.json", asset_tree)
    assert missing.returncode == 2
