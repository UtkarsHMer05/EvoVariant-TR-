# Milestone 012 — Define protocol and configuration schemas

- **MILESTONE:** 012
- **TITLE:** Define protocol and configuration schemas
- **STATUS:** PASS
- **DATE:** 2026-08-18

## WHAT EXISTED BEFORE

- `research/protocol/protocol.yaml` (frozen in M11, SHA-256 `78799000023ca157b72836a0ec603abb20c93960b15fba09485bd0dffbbb1525`) existed as YAML text with no machine validation.
- `src/evovariant_tr/` contained only a `.gitkeep` placeholder from the M8 directory skeleton.
- No Python package code, no schema layer, no tests directory content.
- `.venv-baseline` (gitignored) already had pytest 9.1.1, pydantic 2.13.4, PyYAML installed (M6/M12 setup).

## WHAT CHANGED

- Created the first real package module: strict Pydantic v2 schemas that validate the frozen protocol YAML.
- Every model inherits `StrictModel` with `ConfigDict(extra="forbid", frozen=True)`, so unknown keys are rejected at every nesting level and validated instances are immutable.
- Immutable primary fields are enforced with exact-value validators: `context_length_bp == 8192`, `min_review_stars == 2`, bootstrap `replicates == 2000`, bootstrap `seed == 20260814`, `delta_primary == "(delta_fwd + delta_rc) / 2"`, `reference_assembly` restricted to `GRCh38`, `primary_endpoint` restricted to `AUROC`, `test_cohort_used_for_fitting` restricted to `"never"`, `legacy_formula_inherited` restricted to `False`.
- Dates (`frozen_date`, t0/t1 `release_date`) are parsed as `datetime.date` by Pydantic, so malformed dates fail loudly.
- Scientific config (`ProtocolConfig`) and deployment config (`RuntimeConfig`) are separate validated objects with disjoint fields; each rejects the other's fields.
- Added `tests/conftest.py` to put `src/` on `sys.path` until the M16 packaging milestone provides a proper install.

## FILES CREATED

- `src/evovariant_tr/__init__.py`
- `src/evovariant_tr/config.py`
- `tests/conftest.py`
- `tests/unit/test_config_schema.py`
- `docs/project/reports/milestone_012.md` (this report)

## FILES MODIFIED

- `docs/project/MILESTONE_STATUS.md` (row 012 → PASS)

## FILES REMOVED / MOVED

- None.

## COMMANDS RUN

- `python -m pytest tests/unit/test_config_schema.py -q` → **26 passed in 0.13s** (in `.venv-baseline`).

## TESTS

- `tests/unit/test_config_schema.py` — 26 tests:
  - real protocol loads with all frozen values intact;
  - QA checkpoint counts match the validation target and the funnel adds up (3,615 + 1,389,535 + 9,051 + 1,024 = 1,403,225; 614 + 410 = 1,024);
  - dict / JSON / YAML round-trips are lossless;
  - unknown keys rejected at top level and in nested blocks (4 parametrized cases);
  - attribute mutation of frozen models raises `ValidationError`;
  - 10 parametrized invalid-value cases fail loudly with actionable messages (8193 bp context, hg19 assembly, 1-star gate, wrong seed/replicates, wrong delta formula, wrong primary endpoint, test-cohort fitting, bad date, legacy formula inherited);
  - missing required block, missing file, and non-mapping YAML all fail;
  - runtime config rejects scientific fields and vice versa.

## SCIENTIFIC VALIDATION

- The frozen protocol now fails loudly on any drift: no scientific knob can be changed without a schema-level error naming the field.
- QA checkpoint values remain validation targets only — they are carried as data in the schema, not used by any filter logic (no filter logic exists yet).
- The 8192-bp contract, 2-star gate, GRCh38 assembly, AUROC endpoint, seed 20260814, and 2000 replicates are all enforced as exact values.

## ENGINEERING VALIDATION

- `extra="forbid"` at every nesting level: frozen config cannot be silently extended.
- `frozen=True` on all models: validated config objects are immutable.
- Scientific/deployment separation proven by negative tests in both directions.
- No network, no Modal, no torch imports in the schema layer (cloud-free core preserved).

## COST / EXTERNAL CALLS

- None. Zero external calls, zero GPU, zero spend.

## EVIDENCE GENERATED

- Test run output: 26 passed (pytest 9.1.1, pydantic 2.13.4).
- Stage: SYNTHETIC_TEST (schema behavior proven against the frozen YAML; no real data or model involved).

## GIT STATUS

- New untracked files listed above; ledger updated. Local commit to follow; no remote configured, no push (correct per policy).

## RISKS / OPEN QUESTIONS

- `tests/conftest.py` sys.path shim is temporary; M16 replaces it with proper packaging (`pyproject.toml` + editable install).
- `.gitkeep` in `src/evovariant_tr/` is now redundant; harmless until M16 reorganizes the package.

## NEXT MILESTONE

- 013 — Implement evidence-stage types and claim guards.

## DO NOT CONTINUE IF

- Any schema test fails or is skipped.
- The protocol YAML hash differs from the M11 frozen hash without a dated `DEVIATION_LOG.md` entry.
- Unknown-key rejection or frozen-instance immutability is weakened.
