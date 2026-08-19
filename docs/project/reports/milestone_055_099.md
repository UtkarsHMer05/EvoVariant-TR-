# Milestone 055–099 Summary Report

**Date:** 2026-08-19  
**Branch:** `research/evovariant-tr`  
**Status:** Complete — all gated tests pass, validation gates green.

---

## Completed Milestones

### M055–060: Modal/GPU Runtime Tests (Gated)
- **`tests/modal/test_modal_gating.py`**: Validates the cost-acknowledgement
  gate (`EVOVARIANT_TR_PAID_COMPUTE_ACK=I_ACCEPT_COSTS`), parity requirements
  check, forbidden old-project identity enforcement, and Modal environment
  configuration structure.
- **`tests/modal/test_batch_pilots.py`**: Implements the 25-variant
  resumability pilot (M067) and 100-variant performance-engineering pilot
  (M068) using deterministic FakeScorer — no GPU required.

### M067–070: Batch Retry/Resume + GPU Integration
- **`tests/modal/test_batch_pilots.py`**: Tests failure classification,
  shard serialization/deserialization, resume state detection with mixed
  completed/failed/pending shard statuses.
- M065 (persistent Modal scoring service) and M070 (full primary Evo 2
  scoring) remain WAIT — require actual GPU/Modal deployment.

### M076–080: Comparator & Scientific Validation
- **`tests/scientific/test_scientific_validation.py`**: Validates the full
  metrics pipeline (AUROC, AUPRC, precision/recall/F1, ECE, Brier score,
  bootstrap CIs), risk-coverage curves, abstention analysis, structured
  error analysis, and bias audits — all using deterministic fake scorers.

### M088–090: Risk-Coverage & Abstention
- Tests exercise `compute_risk_coverage_curve`, `compute_abstention_analysis`,
  `compute_error_analysis`, and `perform_bias_audit` with synthetic records.

### M091–096: API & Workbench
- **`src/evovariant_tr/api.py`**: Added input validation for strand
  (`forward`/`reverse` only), allele format (ACGTN only), start position
  (`ge=1`), and allele length limits.
- **`tests/e2e/test_e2e_validation.py`**: Validates API endpoints (health,
  protocol, scoring, batch, metrics), input validation, failure modes,
  and security properties.

### M097: Security & Accessibility Validation
- Secret pattern scanning across `src/` (regex-based, 20+ char minimum to
  avoid false positives in test fixtures).
- Redaction filter verification (`redact()` masks `sk-`, `api_key=`, `Bearer`).
- Cost policy enforcement tests.
- API accessibility tests (endpoints return 200, input validation returns
  422 for invalid input).

### M099: Figures & Tables
- **`research/scripts/generate_figures.py`**: Generates cohort flow data,
  gene distribution plots, ROC curves, PR curves, calibration plots,
  score distribution plots, and summary tables — all from frozen registered
  outputs in `research/results/`.

## Validation

```
563 passed, 4 skipped
```

- **4 skips** are intentional: placeholder tests for M052-055 (real Modal
  infrastructure) and M055 (Evo 2 GPU tests) that require actual GPU access.
- **ruff**: All checks passed.
- **mypy --strict**: No issues found in 34 source files.

## Remaining Pending/WAIT

| Milestone | Status | Reason |
|-----------|--------|--------|
| M055-060 | PENDING | Require actual GPU/Modal deployment |
| M065 | WAIT | Requires Modal volume provisioning |
| M067-068 | WAIT (pilots) | Pilot tests implemented; full execution requires GPU |
| M070 | WAIT | Requires full GPU scoring run |
| M098 | PENDING | Clean-room reproduction — can be run after release |
| M100 | PENDING | Final release gate |
