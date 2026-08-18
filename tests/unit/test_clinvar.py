"""Tests for clinvar.py — Milestone 22 ClinVar archive discovery."""

from __future__ import annotations

import gzip
from datetime import date
from pathlib import Path
from unittest import mock

import pytest

from evovariant_tr.clinvar import (
    CLINVAR_ARCHIVE_DIR,
    ClinVarArchive,
    ClinVarDataSource,
    _parse_ftp_listing,
    build_archive_url,
    find_archive_for_release,
    list_variant_summary_archives,
    verify_data_source,
)

SAMPLE_FTP_LISTING = (
    """<!DOCTYPE HTML>
<html><head><title>Index</title></head>
<body><h1>Index</h1>
<table><thead><tr><th>Name</th><th>Size</th>"""
    """<th>Released</th><th>Last Modified</th></tr></thead>
<tbody><tr><td><a href="../">Parent</a></td><td>-</td><td>-</td></tr>
<tr><td><a href="variant_summary_2024-01.txt.gz">v_2024-01</a></td>"""
    """<td>223,649,945</td><td>2024-01-04</td><td>2024-01-04 00:05:01</td></tr>
<tr><td><a href="variant_summary_2024-02.txt.gz">v_2024-02</a></td>"""
    """<td>226,024,234</td><td>2024-02-01</td><td>2024-02-01 00:05:01</td></tr>
<tr><td><a href="gene_specific_summary_2024-01.txt.gz">g_2024-01</a></td>"""
    """<td>755,863</td><td>2024-01-02</td><td>2024-01-04</td></tr>
</tbody></table></body></html>"""
)


def test_parse_ftp_listing_filters_to_variant_summary():
    files = _parse_ftp_listing(SAMPLE_FTP_LISTING, "https://example.com/")
    names = [f.filename for f in files]
    assert "variant_summary_2024-01.txt.gz" in names
    assert "variant_summary_2024-02.txt.gz" in names
    assert "gene_specific_summary_2024-01.txt.gz" not in names
    assert len(files) == 2


def test_parse_ftp_listing_extracts_metadata():
    files = _parse_ftp_listing(SAMPLE_FTP_LISTING, "https://example.com/")
    vs1 = [f for f in files if "2024-01" in f.filename][0]
    assert vs1.size_bytes == 223649945
    assert vs1.released == date(2024, 1, 4)
    assert vs1.last_modified == date(2024, 1, 4)


def test_parse_ftp_listing_skips_directories():
    listing = SAMPLE_FTP_LISTING.replace(
        'href="variant_summary_2024-01.txt.gz"',
        'href="variant_summary_2024-01.txt.gz/"',
    )
    files = _parse_ftp_listing(listing, "https://example.com/")
    assert len(files) == 1


def test_parse_ftp_listing_handles_empty():
    assert _parse_ftp_listing("", "https://example.com/") == []


def test_parse_ftp_listing_no_date_falls_back_to_filename():
    listing = (
        '<a href="variant_summary_2024-06.txt.gz">v</a></td>'
        '<td>100</td><td>-</td></tr>'
    )
    files = _parse_ftp_listing(listing, "https://example.com/")
    assert len(files) == 1
    assert files[0].released == date(2024, 6, 1)


def test_clinvar_data_source_sanitizes_url():
    ds = ClinVarDataSource(
        source_url="https://user:token@ftp.ncbi.nlm.nih.gov/pub/clinvar/?api_key=secret123",
        file_name="variant_summary_2025-01.txt.gz",
        release_date=date(2025, 1, 1),
        assembly="GRCh38",
    )
    assert "user:" not in ds.source_url
    assert "api_key" not in ds.source_url
    assert "secret123" not in ds.source_url


def test_clinvar_data_source_freeze():
    ds = ClinVarDataSource(
        source_url="https://example.com/",
        file_name="variant_summary_2025-01.txt.gz",
        release_date=date(2025, 1, 1),
        assembly="GRCh38",
    )
    with pytest.raises((TypeError, ValueError)):
        ds.file_name = "something_else.txt.gz"


def test_build_archive_url():
    url = build_archive_url(date(2025, 1, 1))
    assert url == CLINVAR_ARCHIVE_DIR + "2025/variant_summary_2025-01.txt.gz"


def test_find_archive_returns_none_when_not_found():
    listing = (
        '<a href="variant_summary_2024-01.txt.gz">v_2024-01</a></td>'
        '<td>100</td><td>2024-01-04</td><td>2024-01-04 00:05:01</td>'
    )
    with mock.patch("urllib.request.urlopen") as mock_urlopen:
        mock_response = mock.MagicMock()
        mock_response.read.return_value = listing.encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = find_archive_for_release(date(2024, 6, 1))
        assert result is None


def test_find_archive_finds_match():
    listing = (
        '<a href="variant_summary_2024-01.txt.gz">v_2024-01</a></td>'
        '<td>100</td><td>2024-01-04</td><td>2024-01-04 00:05:01</td>'
    )
    with mock.patch("urllib.request.urlopen") as mock_urlopen:
        mock_response = mock.MagicMock()
        mock_response.read.return_value = listing.encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = find_archive_for_release(date(2024, 1, 1))
        assert result is not None
        assert result.file_name == "variant_summary_2024-01.txt.gz"


def test_list_variant_summary_archives_sorted_desc():
    listing = (
        '<a href="variant_summary_2024-01.txt.gz">v_01</a></td>'
        '<td>100</td><td>2024-01-04</td><td>2024-01-04 00:05:01</td>'
        '<a href="variant_summary_2024-02.txt.gz">v_02</a></td>'
        '<td>200</td><td>2024-02-01</td><td>2024-02-01 00:05:01</td>'
    )
    with mock.patch("urllib.request.urlopen") as mock_urlopen:
        mock_response = mock.MagicMock()
        mock_response.read.return_value = listing.encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        archives = list_variant_summary_archives()
        assert archives[0].release_date == date(2024, 2, 1)
        assert archives[1].release_date == date(2024, 1, 4)


def test_clinvar_archive_to_manifest_entry_missing_file():
    archive = ClinVarArchive(
        release_date=date(2025, 1, 1),
        file_name="variant_summary_2025-01.txt.gz",
        source_url="https://example.com/",
        size_bytes=1000,
    )
    entry = archive.to_manifest_entry(Path("/nonexistent"))
    assert entry is None


def test_clinvar_archive_to_manifest_entry_exists(tmp_path: Path):
    fname = "variant_summary_2025-01.txt.gz"
    fpath = tmp_path / fname
    content = b"test data for manifest"
    fpath.write_bytes(gzip.compress(content))

    archive = ClinVarArchive(
        release_date=date(2025, 1, 1),
        file_name=fname,
        source_url="https://example.com/",
        size_bytes=len(content),
    )
    entry = archive.to_manifest_entry(tmp_path)
    assert entry is not None
    assert entry.path == fname
    assert entry.sha256 is not None
    assert entry.size_bytes == len(gzip.compress(content))


def test_verify_data_source_returns_false_for_missing_hash():
    ds = ClinVarDataSource(
        source_url="https://example.com/",
        file_name="nonexistent.txt.gz",
        release_date=date(2025, 1, 1),
        assembly="GRCh38",
        sha256=None,
    )
    assert verify_data_source(ds) is False


def test_variants_summary_pattern_matches_only_correct_format():
    from evovariant_tr.clinvar import VARIANT_SUMMARY_PATTERN

    assert VARIANT_SUMMARY_PATTERN.search("variant_summary_2025-01.txt.gz")
    assert VARIANT_SUMMARY_PATTERN.search("gene_specific_summary_2025-01.txt.gz") is None
