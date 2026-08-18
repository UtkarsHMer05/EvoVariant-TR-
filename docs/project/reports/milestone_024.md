# Milestone 024 — Download and verify the 6 August 2026 ClinVar archive

- **MILESTONE:** 024
- **TITLE:** Download and verify the 6 August 2026 ClinVar archive
- **STATUS:** PASS
- **DATE:** 2026-08-19

## WHAT CHANGED

- Downloaded `variant_summary_2026-08.txt.gz` from the official NCBI FTP:
  `https://ftp.ncbi.nlm.nih.gov/pub/clinvar/tab_delimited/archive/variant_summary_2026-08.txt.gz`
- File size: 441,792,560 bytes (~442 MB)
- SHA-256: `230ba6d5ac0869bfb46fecb8d19bd8dbfa9a133bfda2e3f8f5b5b662ae7bf500`
- Manifest written to `research/data_manifests/clinvar_t1.json`
- Verified file on disk matches recorded hash

## FILES CREATED

- `data/raw/clinvar/variant_summary_2026-08.txt.gz` (gitignored, not committed)
- `research/data_manifests/clinvar_t1.json`

## VALIDATION

- SHA-256 verified via `compute_sha256()` in the download script.
- File size matches NCBI FTP listing: 441,792,560 bytes.
- Source URL sanitized (no credentials).

## NOTES

- Both t0 (January 2025) and t1 (August 2026) archives are now available locally.
- The file exists in `data/raw/clinvar/` which is gitignored — it will not be committed.
- The manifest JSON is committed as the tracked source of truth for data identity.

## NEXT MILESTONE

- 025 — Build a version-aware ClinVar variant_summary parser.
