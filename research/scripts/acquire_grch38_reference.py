#!/usr/bin/env python3
"""Acquire and manifest the frozen GRCh38 GATK reference assets.

The FASTA and .fai are intentionally stored outside Git under ``data/reference``.
This script commits only source metadata and content hashes, and refuses to write a
manifest when either asset is missing or the supplied index is not readable.
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from urllib.request import Request, urlopen

from evovariant_tr.reference import (
    GRCh38_FAI_FILENAME,
    GRCh38_FASTA_FILENAME,
    GRCh38_SOURCE,
    ReferenceGenome,
    sha256_file,
)

FAI_URL = f"{GRCh38_SOURCE.source_url}.fai"
EXPECTED_FASTA_BYTES = 3_249_912_778
EXPECTED_FAI_BYTES = 160_928
EXPECTED_FASTA_SHA256 = "93157a161863464c9435062fd67c173fdaf99cb8b32f1455018361387ffa5564"
EXPECTED_FAI_SHA256 = "edefd93c489dc1baefad312f40388089f8db5cf6dcc3ba0955669ead274e8b6b"


def _download(url: str, destination: Path) -> None:
    """Download one asset atomically, preserving a valid existing asset."""
    if destination.is_file():
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.", suffix=".partial", dir=destination.parent
    )
    os.close(fd)
    temporary = Path(temporary_name)
    try:
        request = Request(url, headers={"User-Agent": "EvoVariant-TR/1.1"})
        with urlopen(request, timeout=120) as response, temporary.open("wb") as output:
            while chunk := response.read(1 << 20):
                output.write(chunk)
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)


def _head(url: str) -> dict[str, str | int | None]:
    request = Request(url, method="HEAD", headers={"User-Agent": "EvoVariant-TR/1.1"})
    with urlopen(request, timeout=30) as response:
        return {
            "status": getattr(response, "status", None),
            "last_modified": response.headers.get("Last-Modified"),
            "content_length": int(response.headers["Content-Length"])
            if response.headers.get("Content-Length")
            else None,
            "etag": response.headers.get("ETag"),
        }


def build_manifest(reference_dir: Path, output: Path, *, download: bool) -> dict[str, object]:
    fasta = reference_dir / GRCh38_FASTA_FILENAME
    fai = reference_dir / GRCh38_FAI_FILENAME
    if download:
        _download(GRCh38_SOURCE.source_url, fasta)
        _download(FAI_URL, fai)
    if not fasta.is_file() or not fai.is_file():
        raise FileNotFoundError(f"both reference assets are required: {fasta} and {fai}")

    fasta_sha256 = sha256_file(fasta)
    fai_sha256 = sha256_file(fai)
    if fasta.stat().st_size != EXPECTED_FASTA_BYTES or fasta_sha256 != EXPECTED_FASTA_SHA256:
        raise ValueError("FASTA does not match the frozen Broad hg38/v0 object metadata")
    if fai.stat().st_size != EXPECTED_FAI_BYTES or fai_sha256 != EXPECTED_FAI_SHA256:
        raise ValueError("FAI does not match the frozen Broad hg38/v0 object metadata")

    genome = ReferenceGenome(fasta)
    contigs = genome.chromosomes
    if not contigs or not all(name.startswith("chr") for name in contigs):
        raise ValueError("reference index does not use the required chr-prefixed naming")

    manifest: dict[str, object] = {
        "manifest_id": "evovariant-tr-grch38-reference-v1",
        "manifest_version": "1",
        "assembly": "GRCh38",
        "assembly_accession_or_build": "GRCh38 / GATK hg38 v0 Homo_sapiens_assembly38",
        "provider": "Broad Institute GATK Resource Bundle",
        "source_url": GRCh38_SOURCE.source_url,
        "fai_source_url": FAI_URL,
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "fasta": {
            "path": "data/reference/Homo_sapiens_assembly38.fasta",
            "filename": GRCh38_FASTA_FILENAME,
            "byte_size": fasta.stat().st_size,
            "sha256": fasta_sha256,
            "http": _head(GRCh38_SOURCE.source_url),
        },
        "fai": {
            "path": "data/reference/Homo_sapiens_assembly38.fasta.fai",
            "filename": GRCh38_FAI_FILENAME,
            "byte_size": fai.stat().st_size,
            "sha256": fai_sha256,
            "http": _head(FAI_URL),
        },
        "contigs": {
            "naming_convention": "chr-prefixed GRCh38 reference contig names",
            "count": len(contigs),
            "first": contigs[:5],
            "last": contigs[-5:],
        },
        "git_policy": "large FASTA and FAI remain outside Git; this manifest is tracked",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference-dir", type=Path, default=Path("data/reference"))
    parser.add_argument("--output", type=Path, default=Path("data/manifests/grch38.json"))
    parser.add_argument("--download", action="store_true")
    args = parser.parse_args()
    manifest = build_manifest(args.reference_dir, args.output, download=args.download)
    print(json.dumps({"status": "PASS", "manifest_id": manifest["manifest_id"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
