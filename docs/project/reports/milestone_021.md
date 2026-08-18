# Milestone 021 — Design the data directory and no-raw-data Git policy

- **MILESTONE:** 021
- **TITLE:** Design the data directory and no-raw-data Git policy
- **STATUS:** PASS
- **DATE:** 2026-08-19

## WHAT EXISTED BEFORE

- No formal data directory policy.
- `data/` directory existed but with no defined structure or .gitignore rules.
- Raw ClinVar archives could be accidentally committed.

## WHAT CHANGED

- Defined the data directory layout:
  `data/raw/`, `data/derived/`, `data/reference/`, `data/model_cache/` — all gitignored.
- Defined the `research/` directory structure:
  `data_manifests/`, `configs/`, `schemas/`, `scripts/`, `runs/`, `results/`, `figures/`, `tables/`.
- Updated root `.gitignore` with explicit rules for all data directories.
- Created `docs/project/data/DATA_POLICY.md` documenting:
  - The no-raw-data Git policy
  - Directory layout
  - Eight explicit rules for data management
  - Verification commands (`make data-verify`)

## FILES CREATED

- `docs/project/data/DATA_POLICY.md`
- `research/runs/.gitkeep`

## FILES MODIFIED

- `.gitignore` (added data directory rules)
- `docs/project/MILESTONE_STATUS.md` (row 021 → PASS)

## VALIDATION

- `make validate` passes (secret scan, ruff, mypy, pytest all green).
- `.gitignore` rules confirmed: `data/raw/` and all data subpaths are ignored.
- No raw data files are currently staged.

## NEXT MILESTONE

- 022 — Implement official ClinVar archive discovery without guessing URLs.

## DO NOT CONTINUE IF

- `.gitignore` does not exclude `data/raw/`.
- Any raw archive is tracked in git.
