# Milestone 025 — Build a version-aware ClinVar variant_summary parser

- **MILESTONE:** 025
- **TITLE:** Build a version-aware ClinVar variant_summary parser
- **STATUS:** PASS
- **DATE:** 2026-08-19

## WHAT CHANGED

- Created `src/evovariant_tr/clinvar_parser.py` — a version-aware parser for the
  official NCBI ClinVar `variant_summary.txt.gz` format:
  - `ClinicalSignificance` StrEnum with controlled vocabulary (Pathogenic,
    Benign, Uncertain_significance, etc.)
  - `CLINSIG_NORMALIZATION` mapping for raw → controlled label conversion
  - `CLINVAR_REVIEW_STATUS_STARS` mapping for review-status → star count
  - `VariantSummaryHeader` — validates required columns are present
  - `VariantSummaryRecord` — frozen dataclass with parsed/normalized fields
  - `parse_header()`, `parse_record()`, `iter_variant_summary()` — streaming
    parser that filters by assembly (GRCh38)
  - `normalize_clinical_significance()`, `review_status_to_stars()`,
    `parse_rcv_accessions()`, `parse_date()`, `is_germline()` helpers
- Created `tests/unit/test_clinvar_parser.py` — 18 tests covering:
  - Header validation (required columns present/missing)
  - Record parsing (VUS, Pathogenic, Benign)
  - Clinical significance normalization
  - Review status → stars mapping
  - RCV accession parsing
  - Date parsing
  - Germline detection
  - Gzip file streaming

## FILES CREATED

- `src/evovariant_tr/clinvar_parser.py`
- `tests/unit/test_clinvar_parser.py`
- `docs/project/reports/milestone_025.md`

## FILES MODIFIED

- `docs/project/MILESTONE_STATUS.md` (row 025 → PASS)

## VALIDATION

- All 217 tests pass (15 new for clinvar_parser + 2 existing).
- ruff clean, mypy strict clean (10 source files).
- Parser verified against the actual variant_summary.txt.gz format from
  NCBI's official README documentation.

## NEXT MILESTONE

- 026 — Implement germline classification normalization.

## DO NOT CONTINUE IF

- `make validate` fails.
- Required columns are not enforced.
