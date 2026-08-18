"""Deterministic file manifests and hashing for EvoVariant-TR.

Every external data or result asset is traceable by source, size, retrieval
time, and SHA-256. Manifests are deterministic: entries are sorted by path and
serialized with sorted keys, so two builds over the same tree produce identical
bytes.

Guards (Milestone 15):
- streaming SHA-256 (constant memory for large archives);
- source URLs are sanitized so credentials/tokens are never embedded;
- retrieval time is recorded separately from the data release date;
- compression type and uncompressed checksum are recorded when practical
  (gzip is streamed; zip/zstd record ``None``);
- one-bit corruption fails verification.
"""

from __future__ import annotations

import gzip
import hashlib
import json
from datetime import UTC, date, datetime
from enum import StrEnum
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import BaseModel, ConfigDict, field_validator

MANIFEST_VERSION = "1.0"
_CHUNK_SIZE = 1 << 20

_SECRET_QUERY_KEYS = frozenset(
    {
        "token",
        "access_token",
        "api_key",
        "apikey",
        "key",
        "secret",
        "password",
        "passwd",
        "signature",
        "sig",
        "auth",
        "credential",
        "credentials",
    }
)


class ManifestError(RuntimeError):
    """Raised for manifest policy violations."""


class CompressionType(StrEnum):
    NONE = "none"
    GZIP = "gzip"
    ZIP = "zip"
    ZSTD = "zstd"


_COMPRESSION_BY_SUFFIX = {
    ".gz": CompressionType.GZIP,
    ".gzip": CompressionType.GZIP,
    ".zip": CompressionType.ZIP,
    ".zst": CompressionType.ZSTD,
    ".zstd": CompressionType.ZSTD,
}


def detect_compression(path: str | Path) -> CompressionType:
    return _COMPRESSION_BY_SUFFIX.get(Path(path).suffix.lower(), CompressionType.NONE)


def streaming_sha256(path: str | Path, chunk_size: int = _CHUNK_SIZE) -> str:
    """SHA-256 of the stored (possibly compressed) file bytes, streamed."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def streaming_uncompressed_sha256(
    path: str | Path,
    compression: CompressionType,
    chunk_size: int = _CHUNK_SIZE,
) -> tuple[str, int] | None:
    """SHA-256 and byte count of the *uncompressed* content when practical.

    Gzip is streamed through stdlib. Zip/zstd are not practical here and return
    ``None``. Plain files trivially equal their stored hash.
    """
    if compression is CompressionType.NONE:
        stored = streaming_sha256(path, chunk_size)
        return stored, Path(path).stat().st_size
    if compression is CompressionType.GZIP:
        digest = hashlib.sha256()
        total = 0
        with gzip.open(path, "rb") as handle:
            for chunk in iter(lambda: handle.read(chunk_size), b""):
                digest.update(chunk)
                total += len(chunk)
        return digest.hexdigest(), total
    return None


def sanitize_source_url(url: str) -> str:
    """Strip credentials and secret-like query parameters from a source URL.

    Userinfo (``user:pass@``) is always removed; query parameters whose names
    look like secrets (token, key, signature, ...) are dropped. Everything else
    is preserved so the source remains citable.
    """
    parts = urlsplit(url.strip())
    netloc = parts.hostname or ""
    if parts.port:
        netloc = f"{netloc}:{parts.port}"
    kept_params = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if key.lower() not in _SECRET_QUERY_KEYS
    ]
    return urlunsplit(
        (parts.scheme, netloc, parts.path, urlencode(kept_params), "")
    )


class ManifestEntry(BaseModel):
    """One traceable asset."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    path: str
    sha256: str
    size_bytes: int
    compression: CompressionType
    uncompressed_sha256: str | None
    uncompressed_size_bytes: int | None
    source_url: str | None
    release_date: date | None
    retrieved_at: str | None
    description: str | None

    @field_validator("sha256", "uncompressed_sha256")
    @classmethod
    def _sha256_shape(cls, value: str | None) -> str | None:
        if value is not None:
            valid = len(value) == 64 and all(c in "0123456789abcdef" for c in value)
            if not valid:
                raise ValueError("sha256 must be a 64-char lowercase hex string")
        return value

    @field_validator("path")
    @classmethod
    def _posix_relative(cls, value: str) -> str:
        if not value or value.startswith("/") or value.startswith("\\"):
            raise ValueError("path must be a non-empty relative POSIX path")
        return Path(value).as_posix()


class Manifest(BaseModel):
    """A deterministic, ordered collection of asset entries."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    manifest_version: str
    name: str
    created_at: str
    entries: tuple[ManifestEntry, ...]

    @field_validator("name")
    @classmethod
    def _non_empty_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("manifest name must be non-empty")
        return value


def build_entry(
    path: str | Path,
    base_dir: str | Path,
    *,
    source_url: str | None = None,
    release_date: date | None = None,
    retrieved_at: datetime | None = None,
    compression: CompressionType | None = None,
    description: str | None = None,
) -> ManifestEntry:
    """Hash one file and assemble its manifest entry.

    ``release_date`` describes when the upstream data was released;
    ``retrieved_at`` describes when we fetched it. They are separate fields and
    must never be conflated.
    """
    base = Path(base_dir)
    target = base / path
    if not target.is_file():
        raise ManifestError(f"file not found for manifest entry: {target}")
    relative = Path(path).as_posix()
    kind = compression if compression is not None else detect_compression(target)
    uncompressed = streaming_uncompressed_sha256(target, kind)
    return ManifestEntry(
        path=relative,
        sha256=streaming_sha256(target),
        size_bytes=target.stat().st_size,
        compression=kind,
        uncompressed_sha256=uncompressed[0] if uncompressed else None,
        uncompressed_size_bytes=uncompressed[1] if uncompressed else None,
        source_url=sanitize_source_url(source_url) if source_url else None,
        release_date=release_date,
        retrieved_at=(
            retrieved_at.astimezone(UTC).isoformat() if retrieved_at else None
        ),
        description=description,
    )


def build_manifest(
    name: str,
    base_dir: str | Path,
    entries: list[ManifestEntry],
    *,
    created_at: datetime | None = None,
) -> Manifest:
    """Assemble entries into a manifest with deterministic ordering."""
    ordered = tuple(sorted(entries, key=lambda entry: entry.path))
    paths = [entry.path for entry in ordered]
    if len(set(paths)) != len(paths):
        raise ManifestError("duplicate paths in manifest entries")
    return Manifest(
        manifest_version=MANIFEST_VERSION,
        name=name,
        created_at=(created_at or datetime.now(UTC))
        .astimezone(UTC)
        .isoformat(),
        entries=ordered,
    )


def manifest_to_json(manifest: Manifest) -> str:
    """Deterministic serialization: sorted keys, entries already path-sorted."""
    return json.dumps(manifest.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"


def write_manifest(manifest: Manifest, path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(manifest_to_json(manifest), encoding="utf-8")
    return target


def load_manifest(path: str | Path) -> Manifest:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return Manifest.model_validate(raw)


class VerificationFailure(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    path: str
    kind: str  # MISSING | SIZE_MISMATCH | HASH_MISMATCH | UNCOMPRESSED_MISMATCH
    detail: str


def verify_manifest(
    manifest: Manifest, base_dir: str | Path
) -> list[VerificationFailure]:
    """Re-hash every entry against disk; return all failures (empty = clean)."""
    failures: list[VerificationFailure] = []
    base = Path(base_dir)
    for entry in manifest.entries:
        target = base / entry.path
        if not target.is_file():
            failures.append(
                VerificationFailure(path=entry.path, kind="MISSING", detail=str(target))
            )
            continue
        actual_size = target.stat().st_size
        if actual_size != entry.size_bytes:
            failures.append(
                VerificationFailure(
                    path=entry.path,
                    kind="SIZE_MISMATCH",
                    detail=f"expected {entry.size_bytes} bytes, found {actual_size}",
                )
            )
            continue
        actual_hash = streaming_sha256(target)
        if actual_hash != entry.sha256:
            failures.append(
                VerificationFailure(
                    path=entry.path,
                    kind="HASH_MISMATCH",
                    detail=f"expected {entry.sha256}, found {actual_hash}",
                )
            )
            continue
        if entry.uncompressed_sha256 is not None:
            uncompressed = streaming_uncompressed_sha256(target, entry.compression)
            if uncompressed is None or uncompressed[0] != entry.uncompressed_sha256:
                failures.append(
                    VerificationFailure(
                        path=entry.path,
                        kind="UNCOMPRESSED_MISMATCH",
                        detail=f"expected {entry.uncompressed_sha256}, "
                        f"found {uncompressed[0] if uncompressed else 'unavailable'}",
                    )
                )
    return failures


def verify_or_raise(manifest: Manifest, base_dir: str | Path) -> None:
    failures = verify_manifest(manifest, base_dir)
    if failures:
        report = "; ".join(f"{f.path}: {f.kind} ({f.detail})" for f in failures)
        raise ManifestError(f"manifest verification failed: {report}")
