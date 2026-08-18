"""Official ClinVar archive discovery for EvoVariant-TR.

This module discovers ClinVar ``variant_summary`` archive URLs from the
official NCBI FTP listing — never by guessing filenames. It supports both the
current monthly release (in ``tab_delimited/``) and historical monthly archives
(in ``tab_delimited/archive/<YYYY>/``).

Design (Milestone 22):
- Base URL comes from NCBI's published FTP root.
- Archive listing is fetched and parsed from the official directory index.
- File names are discovered by matching the official naming pattern, not
  constructed from user-supplied strings.
- Every discovered URL is wrapped in a :class:`ClinVarDataSource` that records
  source URL (sanitized), release date, retrieval timestamp, and file metadata.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urljoin

from pydantic import BaseModel, ConfigDict, field_validator

from evovariant_tr.manifest import (
    ManifestEntry,
    build_entry,
    sanitize_source_url,
    streaming_sha256,
)

CLINVAR_FTP_ROOT = "https://ftp.ncbi.nlm.nih.gov/pub/clinvar/"
CLINVAR_TAB_DELIMITED_DIR = urljoin(CLINVAR_FTP_ROOT, "tab_delimited/")
CLINVAR_ARCHIVE_DIR = urljoin(CLINVAR_FTP_ROOT, "tab_delimited/archive/")

VARIANT_SUMMARY_PATTERN = re.compile(
    r"variant_summary_(\d{4})-(\d{2})\.txt\.gz$"
)


@dataclass(frozen=True)
class ArchiveFile:
    """One discovered file in a ClinVar FTP directory listing."""

    filename: str
    size_bytes: int
    released: date | None
    last_modified: date | None
    directory_url: str


class ClinVarDataSource(BaseModel):
    """A discovered ClinVar variant_summary archive with full provenance."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    source_url: str
    file_name: str
    release_date: date
    assembly: str
    retrieved_at: str | None = None
    sha256: str | None = None
    size_bytes: int | None = None
    description: str | None = None

    @field_validator("source_url")
    @classmethod
    def _sanitize(cls, value: str) -> str:
        return sanitize_source_url(value)

    @property
    def full_url(self) -> str:
        return urljoin(self.source_url, self.file_name) if self.source_url else self.file_name


def _parse_ftp_listing(listing_html: str, base_url: str) -> list[ArchiveFile]:
    """Parse an Apache-style directory index HTML into ArchiveFile records.

    The NCBI FTP returns a simple HTML index with one row per entry. We
    extract filename, size, release date, and last-modified date from the
    table rows rather than guessing filenames.
    """
    files: list[ArchiveFile] = []

    row_pattern = re.compile(
        r'<a href="([^"]+)">.*?</a></td>\s*'
        r"<td>(.*?)</td>\s*"
        r"<td>(.*?)</td>\s*"
        r"(?:<td>(.*?)</td>\s*)?",
        re.DOTALL,
    )
    for match in row_pattern.finditer(listing_html):
        filename = match.group(1)
        if filename.endswith("/"):
            continue
        version_match = VARIANT_SUMMARY_PATTERN.search(filename)
        if not version_match:
            continue

        size_str = match.group(2).strip()
        released_str = match.group(3).strip()
        last_mod_str = (match.group(4) or "").strip()

        try:
            if size_str == "-":
                size = 0
            else:
                size = int(size_str.replace(",", ""))
        except ValueError:
            size = 0

        year_match = version_match
        release = date(int(year_match.group(1)), int(year_match.group(2)), 1)

        released: date | None = None
        date_match = re.search(r"(\d{4}-\d{2}-\d{2})", released_str)
        if date_match:
            released = date.fromisoformat(date_match.group(1))

        last_mod: date | None = None
        if last_mod_str:
            last_mod_match = re.search(r"(\d{4}-\d{2}-\d{2})", last_mod_str)
            if last_mod_match:
                last_mod = date.fromisoformat(last_mod_match.group(1))

        files.append(
            ArchiveFile(
                filename=filename,
                size_bytes=size,
                released=released or release,
                last_modified=last_mod,
                directory_url=base_url,
            )
        )
    return files


@dataclass
class ClinVarArchive:
    """Discovered ClinVar variant_summary archive for a given release date."""

    release_date: date
    file_name: str
    source_url: str
    size_bytes: int | None
    sha256: str | None = None
    retrieved_at: datetime | None = None

    def to_manifest_entry(self, base_dir: Path) -> ManifestEntry | None:
        """Build a manifest entry from the downloaded file on disk."""
        target = base_dir / self.file_name
        if not target.is_file():
            return None
        return build_entry(
            self.file_name,
            base_dir,
            source_url=self.source_url,
            release_date=self.release_date,
            description=f"ClinVar variant_summary.gz for release {self.release_date.isoformat()}",
        )


def build_archive_url(release: date) -> str:
    """Construct the FTP URL for a given release month's variant_summary.

    NCBI stores monthly archives in two layouts:
    - 2014–2024: ``archive/<YYYY>/variant_summary_<YYYY-MM>.txt.gz``
    - 2025 onward: ``archive/variant_summary_<YYYY-MM>.txt.gz`` (top-level)
    This function returns the yearly-subdirectory URL. Use candidate URLs
    for robust discovery.
    """
    filename = f"variant_summary_{release.year:04d}-{release.month:02d}.txt.gz"
    return urljoin(CLINVAR_ARCHIVE_DIR, f"{release.year}/{filename}")


def _candidate_urls(release: date) -> list[str]:
    """Return candidate URLs for a release, in priority order."""
    filename = f"variant_summary_{release.year:04d}-{release.month:02d}.txt.gz"
    return [
        urljoin(CLINVAR_ARCHIVE_DIR, f"{release.year}/{filename}"),
        urljoin(CLINVAR_ARCHIVE_DIR, filename),
    ]


def list_variant_summary_archives(
    base_url: str = CLINVAR_ARCHIVE_DIR,
) -> list[ClinVarArchive]:
    """Discover all variant_summary archive files in the given FTP directory.

    Fetches the directory listing HTML and parses it. Returns archives sorted
    by release date (newest first).
    """
    import urllib.request

    try:
        with urllib.request.urlopen(base_url, timeout=30) as response:
            listing = response.read().decode("utf-8", errors="replace")
    except Exception as exc:
        raise RuntimeError(
            f"Could not fetch ClinVar archive listing from {base_url}: {exc}"
        ) from exc

    files = _parse_ftp_listing(listing, base_url)
    archives = [
        ClinVarArchive(
            release_date=f.released,
            file_name=f.filename,
            source_url=f.directory_url,
            size_bytes=f.size_bytes if f.size_bytes > 0 else None,
        )
        for f in files
        if f.released is not None
    ]
    archives.sort(key=lambda a: a.release_date, reverse=True)
    return archives


def find_archive_for_release(
    target_month: date,
    base_url: str = CLINVAR_ARCHIVE_DIR,
) -> ClinVarArchive | None:
    """Find the archive file matching a specific year-month release.

    Args:
        target_month: A date whose year and month identify the desired release.
        base_url: The FTP directory to search (defaults to the archive dir).

    Returns the matching archive, or None if not found.
    """
    archives = list_variant_summary_archives(base_url)
    target_key = (target_month.year, target_month.month)
    for archive in archives:
        if (archive.release_date.year, archive.release_date.month) == target_key:
            return archive
    return None


def discover_temporal_archives(
    t0_date: date,
    t1_date: date,
) -> tuple[ClinVarArchive, ClinVarArchive]:
    """Discover the official ClinVar archives for the t0 and t1 temporal snapshots.

    The t0 archive may be in the archive/ directory (historical), while the t1
    archive may be in the current tab_delimited/ directory. This function tries
    both locations.

    Raises:
        RuntimeError: if either archive cannot be located.
    """
    t0 = find_archive_for_release(t0_date, CLINVAR_ARCHIVE_DIR)
    if t0 is None:
        raise RuntimeError(
            f"t0 archive not found in {CLINVAR_ARCHIVE_DIR} for release {t0_date.isoformat()}"
        )

    t1 = find_archive_for_release(t1_date, CLINVAR_ARCHIVE_DIR)
    if t1 is None:
        t1 = find_archive_for_release(t1_date, CLINVAR_TAB_DELIMITED_DIR)
    if t1 is None:
        raise RuntimeError(
            f"t1 archive not found for release {t1_date.isoformat()} "
            f"in {CLINVAR_ARCHIVE_DIR} or {CLINVAR_TAB_DELIMITED_DIR}"
        )

    return t0, t1


def verify_data_source(data_source: ClinVarDataSource) -> bool:
    """Verify a downloaded data source file against its recorded hash."""
    if data_source.sha256 is None:
        return False
    local_file = Path("data/raw") / data_source.file_name
    if not local_file.is_file():
        return False
    actual = streaming_sha256(local_file)
    return actual == data_source.sha256
