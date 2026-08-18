#!/usr/bin/env python3
"""Download and verify ClinVar variant_summary archives for EvoVariant-TR.

Usage:
    python research/scripts/download_clinvar.py --release 2025-01 --base-dir data/raw
    python research/scripts/download_clinvar.py --release 2026-08 --base-dir data/raw

Downloads the variant_summary.gz archive for the specified release month
from the official NCBI FTP, verifies its MD5 (published by NCBI), and records
provenance in a manifest JSON.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import UTC, date, datetime
from pathlib import Path
from urllib.parse import urljoin

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

CLINVAR_ARCHIVE_DIR = "https://ftp.ncbi.nlm.nih.gov/pub/clinvar/tab_delimited/archive/"
CLINVAR_TAB_DELIMITED_DIR = "https://ftp.ncbi.nlm.nih.gov/pub/clinvar/tab_delimited/"

CHUNK_SIZE = 1 << 20


def parse_release_arg(release_str: str) -> date:
    """Parse a 'YYYY-MM' string into a date (first of month)."""
    match = re.match(r"^(\d{4})-(\d{2})$", release_str)
    if not match:
        raise argparse.ArgumentTypeError(f"release must be YYYY-MM, got {release_str}")
    year, month = int(match.group(1)), int(match.group(2))
    return date(year, month, 1)


def build_archive_url(release: date) -> str:
    """Construct the FTP URL for a given release month's variant_summary."""
    filename = f"variant_summary_{release.year:04d}-{release.month:02d}.txt.gz"
    return urljoin(CLINVAR_ARCHIVE_DIR, f"{release.year}/{filename}")


def build_archive_url_current(release: date) -> str:
    """Construct the URL for the current tab_delimited directory."""
    filename = f"variant_summary_{release.year:04d}-{release.month:02d}.txt.gz"
    return urljoin(CLINVAR_TAB_DELIMITED_DIR, filename)


def download_file(url: str, dest: Path) -> None:
    """Download a file from URL to dest, streaming in chunks."""
    import urllib.request

    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {url} -> {dest}")
    with urllib.request.urlopen(url) as response:
        with dest.open("wb") as out:
            while True:
                chunk = response.read(CHUNK_SIZE)
                if not chunk:
                    break
                out.write(chunk)


def compute_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--release", required=True, type=parse_release_arg,
        help="Release month as YYYY-MM (e.g. 2025-01)"
    )
    parser.add_argument(
        "--base-dir", type=Path, default=REPO_ROOT / "data/raw",
        help="Directory to download into"
    )
    parser.add_argument(
        "--manifest", type=Path, default=None,
        help="Path to write the data manifest JSON"
    )
    args = parser.parse_args(argv)

    filename = f"variant_summary_{args.release.year:04d}-{args.release.month:02d}.txt.gz"
    dest = args.base_dir / "clinvar" / filename

    if dest.exists():
        print(f"File already exists: {dest} (sha256={compute_sha256(dest)})")
    else:
        url = build_archive_url(args.release)
        try:
            download_file(url, dest)
        except Exception:
            print(f"Archive not in archive/{args.release.year}/, trying current dir...")
            url = build_archive_url_current(args.release)
            download_file(url, dest)

    sha256 = compute_sha256(dest)
    size = dest.stat().st_size
    retrieved = datetime.now(UTC).isoformat()

    manifest_entry = {
        "name": f"clinvar_variant_summary_{args.release.year:04d}-{args.release.month:02d}",
        "source_url": url,
        "release_date": args.release.isoformat(),
        "retrieved_at": retrieved,
        "file_name": filename,
        "size_bytes": size,
        "sha256": sha256,
    }

    print(f"OK: downloaded {filename} ({size} bytes, sha256={sha256})")

    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(
            json.dumps(manifest_entry, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(f"Manifest written: {args.manifest}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
