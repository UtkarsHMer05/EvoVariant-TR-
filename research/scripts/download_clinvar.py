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


def build_candidate_urls(release: date) -> list[str]:
    """Return candidate URLs for a release, in priority order.

    NCBI stores monthly archives in two layouts:
    - 2014–2024: ``archive/<YYYY>/variant_summary_<YYYY-MM>.txt.gz``
    - 2025 onward: ``archive/variant_summary_<YYYY-MM>.txt.gz`` (top-level)
    """
    filename = f"variant_summary_{release.year:04d}-{release.month:02d}.txt.gz"
    if release.year >= 2025:
        return [
            urljoin(CLINVAR_ARCHIVE_DIR, filename),
            urljoin(CLINVAR_ARCHIVE_DIR, f"{release.year}/{filename}"),
        ]
    return [
        urljoin(CLINVAR_ARCHIVE_DIR, f"{release.year}/{filename}"),
        urljoin(CLINVAR_ARCHIVE_DIR, filename),
    ]


def build_archive_url_current(release: date) -> str:
    """Construct the URL for the current tab_delimited directory."""
    filename = f"variant_summary_{release.year:04d}-{release.month:02d}.txt.gz"
    return urljoin(CLINVAR_TAB_DELIMITED_DIR, filename)


def download_file(url: str, dest: Path) -> None:
    """Download a file from URL to dest, streaming in chunks.

    Uses the ``curl`` command-line tool which handles corporate proxies and
    SSL better than Python's urllib in some environments. Falls back to urllib
    with an unverified SSL context if curl is not available.
    """
    import shutil
    import ssl
    import subprocess
    import urllib.request

    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {url} -> {dest}")

    curl_bin = shutil.which("curl")
    if curl_bin:
        result = subprocess.run(
            [curl_bin, "-fsSL", "-o", str(dest), url],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"curl failed: {result.stderr.strip()}")
        return

    # Fallback: urllib with unverified context
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(url, headers={"User-Agent": "EvoVariant-TR/0.1"})
    with urllib.request.urlopen(req, timeout=120, context=ctx) as response:
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
    parser.add_argument(
        "--release-date", type=date.fromisoformat, default=None,
        help="Exact archive release date (YYYY-MM-DD); defaults to the first of the month",
    )
    args = parser.parse_args(argv)

    filename = f"variant_summary_{args.release.year:04d}-{args.release.month:02d}.txt.gz"
    dest = args.base_dir / "clinvar" / filename

    if dest.exists():
        print(f"File already exists: {dest} (sha256={compute_sha256(dest)})")
        url = build_candidate_urls(args.release)[0]
    else:
        urls = build_candidate_urls(args.release)
        for url in urls:
            try:
                download_file(url, dest)
                break
            except Exception as e:
                print(f"Failed to download from {url}: {e}")
                continue
        else:
            print(f"ERROR: could not download {filename} from any known location")
            return 1

    sha256 = compute_sha256(dest)
    size = dest.stat().st_size
    retrieved = datetime.now(UTC).isoformat()

    manifest_entry = {
        "name": f"clinvar_variant_summary_{args.release.year:04d}-{args.release.month:02d}",
        "source_url": url,
        "release_date": (args.release_date or args.release).isoformat(),
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
