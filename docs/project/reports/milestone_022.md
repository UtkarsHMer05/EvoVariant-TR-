# Milestone 022 — Implement official ClinVar archive discovery

- **MILESTONE:** 022
- **TITLE:** Implement official ClinVar archive discovery without guessing URLs
- **STATUS:** PASS
- **DATE:** 2026-08-19

## WHAT EXISTED BEFORE

- No ClinVar data discovery module.
- No programmatic way to find variant_summary archive URLs.

## WHAT CHANGED

- Created `src/evovariant_tr/clinvar.py` with:
  - Constants for official ClinVar FTP paths: `CLINVAR_FTP_ROOT`, `CLINVAR_TAB_DELIMITED_DIR`, `CLINVAR_ARCHIVE_DIR`.
  - `VARIANT_SUMMARY_PATTERN` regex matching the official `variant_summary_YYYY-MM.txt.gz` naming convention.
  - `ArchiveFile` dataclass for parsed FTP listing rows.
  - `ClinVarDataSource` pydantic model for provenance-tracked data sources (URL sanitized, assembly, release_date).
  - `ClinVarArchive` dataclass for discovered archives with `to_manifest_entry()` for manifest integration.
  - `build_archive_url()` — constructs official archive URLs from release dates.
  - `_parse_ftp_listing()` — parses Apache-style HTML directory index from NCBI FTP.
  - `list_variant_summary_archives()` — discovers all variant_summary archives in a directory.
  - `find_archive_for_release()` — finds the specific archive for a given year-month.
  - `discover_temporal_archives()` — discovers t0 and t1 archives from NCBI FTP.
  - `verify_data_source()` — verifies downloaded files against recorded hashes.
- Created `research/scripts/download_clinvar.py` — standalone download script.
- Created `tests/unit/test_clinvar.py` — 15 tests covering parsing, URL building, discovery, sanitisation.

## FILES CREATED

- `src/evovariant_tr/clinvar.py`
- `research/scripts/download_clinvar.py`
- `tests/unit/test_clinvar.py`
- `docs/project/reports/milestone_022.md`

## FILES MODIFIED

- `docs/project/MILESTONE_STATUS.md` (row 022 → PASS)

## VALIDATION

- **Validation 1:** All discovered URLs are constructed from the official NCBI FTP root + archive subdirectory pattern, never guessed. The URL pattern is `https://ftp.ncbi.nlm.nih.gov/pub/clinvar/tab_delimited/archive/<YYYY>/variant_summary_<YYYY-MM>.txt.gz`.
- **Validation 2:** URL sanitisation strips query-parameter secrets (api_key, token, etc.) and userinfo from source URLs.
- **Validation 3:** Tests with mocked HTTP responses (no real network calls) verify correct parsing of the actual NCBI FTP HTML format.
- Full validation gate passes: ruff, mypy strict, 196 tests pass, 96.53% coverage.

## NEXT MILESTONE

- 023 — Download and verify the 2 January 2025 ClinVar archive.

## DO NOT CONTINUE IF

- `make validate` does not pass.
- The URL pattern does not match the official NCBI FTP structure confirmed by manual inspection.
