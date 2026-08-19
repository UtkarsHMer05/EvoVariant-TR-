# Milestone 038-050 — Calibration cohort, QC, sequence windows, scorers, orchestration

## Summary

### M38: Disjoint definitive-at-t0 calibration cohort
- Created `src/evovariant_tr/calibration.py` with:
  - `CalibrationCohort`, `CalibrationVariant`, `CalibrationOutcome` dataclasses
  - `build_calibration_cohort()` — builds a control set of definitively classified variants at t0
  - `check_disjoint()` — enforces zero overlap between VUS and definitive cohorts using unified deduplication
- Calibration cohort results from real ClinVar archives:
  - 549,427 definitive variants at t0
  - 508,556 stable (same classification at t1)
  - 40,865 changed classification (7,593 to pathogenic, 19,238 to benign, 14,034 to VUS)

### M39: Zero normalized-ID overlap and gene-group splits
- Updated `check_disjoint()` to use unified deduplication (first pass loads all germline SNVs, dedup by (chrom, start, ref, alt), then splits into VUS vs definitive)
- Results: 0 overlapping identities, cohorts confirmed disjoint
- Added `gene_group_splits()` for gene-grouped analysis
- Results: 9,945 genes with definitive variants, 571,740 total definitive variants

### M40: Freeze cohort outputs and data-only QC package
- Primary cohort output: `research/results/cohort_primary.json` (380,776 VUS)
- Calibration cohort output: `research/results/cohort_calibration.json`
- Disjoint check: `research/results/disjoint_check.json` (0 overlap)
- QC report generator: `research/scripts/generate_qc_report.py`
- All QC checks pass (data integrity, cohort consistency, disjointness)

### M41: Freeze 8,192-base sequence-window convention
- `CONTEXT_LENGTH_BP = 8192` frozen in `src/evovariant_tr/sequence_window.py`
- Window centered on variant with HALF_WINDOW = 4096 bases each side
- Reference: `protocol.yaml` (line 91: `context_length_bp: 8192`)

### M42: Implement exact reference-window generation
- `generate_reference_window()` — produces a `ReferenceWindow` from FASTA + .fai
- Supports samtools faidx and pure-Python fallback
- Tested with mock FASTA fixtures

### M43: Define and test chromosome-edge behavior
- `compute_window_coordinates_with_shift()` handles edge clamping
- When variant is near start: window starts at 1
- When variant is near end: window ends at chrom_len
- `validate_window_coordinates()` checks bounds and consistency

### M44: Alternate-sequence mutation with strong invariants
- Created `src/evovariant_tr/sequence_mutate.py`:
  - `mutate_reference()` — applies SNV/indel to reference sequence
  - Strong invariants: length preserved for SNVs, correct length change for indels
  - Reference allele validation at mutation site
  - Invariant tests: `validate_mutate_snp_invariant()`, `validate_mutate_length_invariant()`

### M45: Reverse-complement variant transformation
- `reverse_complement()` — computes RC of DNA sequence
- `apply_variant_to_reference()` with strand parameter
- `get_reverse_complement_variant()` — RC's variant alleles
- Validated: RC(RC(seq)) == seq

### M46: Deterministic sequence cache
- Created `src/evovariant_tr/sequence_cache.py`:
  - `SequenceCache` — content-addressed cache for reference windows
  - Keys are SHA-256 of (chrom, position, context_length)
  - `CacheEntry` with full provenance metadata
  - `get_or_compute()` pattern for lazy caching

### M47: Model-agnostic scorer interface
- Created `src/evovariant_tr/scorer.py`:
  - Abstract `Scorer` class with `score_variant`, `score_batch`, `score_cohort`, `check_health`, `provenance`
  - `ScoredVariant` and `ScoringResult` data structures
  - Pluggable interface for Evo 2, PhyloP, CADD, etc.

### M48: Deterministic fake scorer
- Created `src/evovariant_tr/fake_scorer.py`:
  - `FakeScorer` implements the `Scorer` interface
  - Hash-based deterministic scoring (SHA-256 of sequence)
  - Scores in range [-10, 10]
  - No external dependencies (GPU, Evo 2, etc.)
  - Used exclusively for testing the orchestration pipeline

### M49: Evo 2 parity requirements
- Documented in `docs/project/reports/milestone_049.md`
- Key requirements: 8,192bp context window, forward+reverse strand scoring,
  deterministic shard format, batched GPU inference

### M50: End-to-end scoring orchestration
- Created `src/evovariant_tr/orchestration.py`:
  - `run_scoring_orchestration()` — full pipeline: cohort → calibration → cache → score
  - `OrchestrationResult` with primary cohort, calibration, disjoint check, scoring
  - Health check integration before scoring

## Tests Added
- `tests/unit/test_sequence_mutate.py` (22 tests)
- `tests/unit/test_sequence_window.py` (32 tests)
- `tests/unit/test_sequence_cache.py` (7 tests)
- `tests/unit/test_scorer.py` (14 tests)
- `tests/unit/test_orchestration.py` (4 tests)

## Validation
- All gates pass: 362 tests, 95.65% coverage, ruff clean, mypy strict clean (21 source files)
