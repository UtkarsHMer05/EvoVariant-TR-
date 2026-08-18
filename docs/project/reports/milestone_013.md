# Milestone 013 — Implement evidence-stage types and claim guards

- **MILESTONE:** 013
- **TITLE:** Implement evidence-stage types and claim guards
- **STATUS:** PASS
- **DATE:** 2026-08-18

## WHAT EXISTED BEFORE

- `docs/terminology/EVIDENCE_STAGES.md` (M7) defined the five stages, rules, and the forbidden-promotion list in prose, with code enforcement explicitly deferred to Milestone 13.
- `src/evovariant_tr/` contained `__init__.py` and `config.py` (M12). No evidence-stage types or guards existed in code.
- `tests/unit/test_config_schema.py` (26 tests) was the only test module.

## WHAT CHANGED

- Implemented `src/evovariant_tr/evidence.py`:
  - `EvidenceStage` enum with exactly `SYNTHETIC_TEST`, `LEGACY_BASELINE`, `ENGINEERING_PILOT`, `PRELIMINARY`, `FINAL`; serialization label is the plain enum value; each stage carries a UI-safe description and a `citable` flag (only FINAL).
  - `ResultRecord` (strict, frozen Pydantic model) attaches `evidence_stage` to every result; `AggregateTable` attaches the guard to aggregate tables.
  - Write-path guard: `check_write_allowed` / `write_result_record` raise `FinalPathWriteError` when any non-FINAL output targets a path containing a `final`/`final_results` segment.
  - Legacy guard: `AggregateTable.add` rejects any record whose source contains legacy markers (`legacy`, `brca1`, `evaluation/results`), so old BRCA1 metrics cannot enter EvoVariant-TR aggregate tables.
  - Scorer-kind guard: `validate_stage_for_scorer` pins fake-scorer outputs to SYNTHETIC_TEST and legacy-scorer outputs to LEGACY_BASELINE.
  - Promotion guard: `promote` returns a new immutable record, grants only `PRELIMINARY -> FINAL`, requires a non-empty reason, and appends a timestamped `PromotionEvent` to a log. Every other transition raises `ForbiddenPromotionError`.
  - Serialization helpers for JSON, CSV, and Parquet (pyarrow) that preserve the stage label through round-trips.
- Installed `pyarrow 25.0.1` into `.venv-baseline` (gitignored) to satisfy the Parquet acceptance validation.

## FILES CREATED

- `src/evovariant_tr/evidence.py`
- `tests/unit/test_evidence_stage.py`
- `docs/project/reports/milestone_013.md` (this report)

## FILES MODIFIED

- `docs/project/MILESTONE_STATUS.md` (row 013 → PASS)

## FILES REMOVED / MOVED

- None.

## COMMANDS RUN

- `python -m pytest tests/unit/test_evidence_stage.py -q` → **35 passed in 3.93s**
- `python -m pytest tests/unit -q` → **61 passed in 0.73s** (no regression in M12 tests)

## TESTS

- `tests/unit/test_evidence_stage.py` — 35 tests covering:
  - exact five-stage enum, UI descriptions, citability;
  - label parsing round-trip and loud rejection of unknown labels;
  - **Validation 1:** synthetic (and every other non-FINAL) result cannot pass the final-result writer; file is never created; FINAL can write and round-trip;
  - fake/legacy scorer stage pinning;
  - aggregate table rejects SYNTHETIC_TEST / LEGACY_BASELINE / ENGINEERING_PILOT stages and legacy BRCA1 sources; accepts clean PRELIMINARY/FINAL;
  - full 5×5 forbidden-promotion matrix (only PRELIMINARY→FINAL grantable, with logged reason and timestamp; original record immutable);
  - **Validation 2:** stage survives JSON, CSV, and Parquet round-trips; serialized label is the plain stage string;
  - record strictness: unknown fields rejected, instances immutable, empty metric names rejected.

## SCIENTIFIC VALIDATION

- Synthetic or engineering outputs are now technically blocked from final-results paths and aggregate tables — claim mislabeling requires defeating a tested guard, not just renaming a file.
- Promotion is a deliberate, logged act (matches EVIDENCE_STAGES.md rule 2); no automatic promotion path exists.
- No scientific numbers were produced or claimed; this milestone is plumbing for claim safety.

## ENGINEERING VALIDATION

- All guards raise typed exceptions with the offending stage and path in the message (actionable failures).
- Cloud-free core preserved: `evidence.py` imports only stdlib + pydantic; pyarrow is imported lazily inside the Parquet helpers.
- Full unit suite green (61 tests).

## COST / EXTERNAL CALLS

- None. Zero external calls, zero GPU, zero spend.

## EVIDENCE GENERATED

- Test run outputs (35 passed; 61 passed).
- Stage: SYNTHETIC_TEST (this milestone tests guard behavior with synthetic records only).

## GIT STATUS

- New files listed above; ledger updated. Local commit to follow; no remote configured, no push.

## RISKS / OPEN QUESTIONS

- `is_final_path` matches path segments named `final`/`final_results`; the canonical results directory layout is fixed at M21 — if it introduces other final-path conventions, extend `FINAL_PATH_SEGMENTS` then.
- The registry (M14) will attach `evidence_stage` to run records and enforce the dirty-tree FINAL guard; `ResultRecord.run_id` is already shaped for that join.

## NEXT MILESTONE

- 014 — Design the immutable experiment registry.

## DO NOT CONTINUE IF

- Any evidence-stage test fails or is skipped.
- A non-FINAL stage can be written to a final-results path.
- Any promotion other than PRELIMINARY→FINAL succeeds, or promotion succeeds without a logged reason.
