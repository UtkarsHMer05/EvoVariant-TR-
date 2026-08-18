# Milestone 023 — Download and verify the 2 January 2025 ClinVar archive

- **MILESTONE:** 023
- **TITLE:** Download and verify the 2 January 2025 ClinVar archive
- **STATUS:** PASS
- **DATE:** 2026-08-19

## WHAT CHANGED

- Downloaded `variant_summary_2025-01.txt.gz` from the official NCBI FTP:
  `https://ftp.ncbi.nlm.nih.gov/pub/clinvar/tab_delimited/archive/variant_summary_2025-01.txt.gz`
- File size: 288,267,418 bytes (~288 MB)
- SHA-256: `931322c5b576e4d46c82b2e275ef0920661ef9c39c1acf62ed48e6756f24d7aa`
- Retrieved: 2026-08-18T23:16:30 UTC
- Manifest written to `research/data_manifests/clinvar_t0.json`
- Verified file on disk matches recorded hash

## FILES CREATED

- `data/raw/clinvar/variant_summary_2025-01.txt.gz` (gitignored, not committed)
- `research/data_manifests/clinvar_t0.json`

## VALIDATION

- SHA-256 verified via `compute_sha256()` in the download script.
- File size matches NCBI FTP listing: 288,267,418 bytes.
- Source URL sanitized (no credentials).

## NOTES

- The 2025 archive file is stored directly in `archive/` (not in a `2025/` subdirectory), unlike 2014-2024 archives which are in `archive/<YYYY>/` subdirectories. The download script handles this via `build_candidate_urls()`.
- NCBI does not provide MD5 checksums in the archive directory; SHA-256 is computed locally and recorded in the manifest.

## NEXT MILESTONE

- 024 — Download and verify the 6 August 2026 ClinVar archive.
