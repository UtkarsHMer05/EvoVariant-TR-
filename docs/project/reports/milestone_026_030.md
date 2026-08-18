# Milestone 026-030 — ClinVar normalization, eligibility filters, and temporal cohort builder

## Summary

This set of milestones implements the core cohort-construction pipeline:

### M26 — Germline classification normalization
- Created `src/evovariant_tr/clinvar_normalize.py`:
  - `normalize_origin_simple()` — normalizes OriginSimple field
  - `is_germline_normalized()` — checks germline origin
  - `classify_variant()` — maps records to "pathogenic"/"benign"/"vus"/"conflicting"/"other"
  - `is_eligible_for_temporal_cohort()` — checks all eligibility criteria
  - `is_vus_at_t0()` — identifies VUS at t0 with star gate
  - `is_definitive_at_t1()` — identifies definitive classifications at t1

### M27 — ClinVar review-status to star normalization
- `CLINVAR_REVIEW_STATUS_STARS` mapping in `clinvar_parser.py` maps all
  ClinVar review-status strings to star counts (0-3).
- Tests verify star counts for all review status levels.

### M28 — Coordinate andallele normalization
- `VariantIdentity` frozen dataclass in `cohort.py` provides normalized
  variant identity: (chrom, start, ref, alt) on GRCh38.
- Validation tests check chromosome, coordinate, allele validity.

### M29 — Deterministic primary eligibility filters
- `is_eligible_for_temporal_cohort()` enforces:
  - Germline origin
  - SNV type
  - GRCh38 assembly
  - Valid chromosome/start/stop
  - Valid reference/alternate alleles (ref != alt)
  - Minimum review stars (default 2)

### M30 — Deterministic t0-to-t1 temporal joining
- Created `src/evovariant_tr/cohort.py`:
  - `build_temporal_cohort()` — loads t0/t1 snapshots, deduplicates, identifies
    VUS at t0, finds t1 resolution, assigns outcomes.
  - `TemporalCohort` — holds variants + flow counts.
  - `CohortFlow` — CONSORT-style flow counts.
  - `CohortVariant` — single variant record with t0/t1 classifications.
  - Deduplication by (chrom, start, ref, alt) identity.
  - Outcome assignment: resolved_pathogenic / resolved_benign / unresolved / excluded.

## Files Created
- `src/evovariant_tr/clinvar_normalize.py`
- `src/evovariant_tr/cohort.py`
- `tests/unit/test_clinvar_normalize.py` (22 tests)
- `tests/unit/test_cohort.py` (10 tests)

## Files Modified
- `src/evovariant_tr/clinvar_parser.py` (added `CLINVAR_REVIEW_STATUS_STARS`)
- `docs/project/MILESTONE_STATUS.md`

## Validation
- 254 tests pass, 96.50% coverage.
- ruff, mypy strict clean.
