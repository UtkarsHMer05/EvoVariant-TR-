# Milestone 020 — Create a single project control surface

- **MILESTONE:** 020
- **TITLE:** Create a single project control surface
- **STATUS:** PASS
- **DATE:** 2026-08-19

## WHAT EXISTED BEFORE

- `Makefile` existed but had been written as an initial draft; no `COMMAND_REFERENCE.md` existed.
- `scripts/verify_registry.py` and `tests/unit/test_verify_registry_script.py` had failing tests due to a run_id format mismatch: the `RUN_ID_PATTERN` requires 8 hex characters after the timestamp, but test fixtures used 6-digit run IDs.
- No single canonical place documented all commands, test markers, gated tiers, and GPU cost gates.

## WHAT CHANGED

- Created `COMMAND_REFERENCE.md` — the canonical command reference covering:
  - Free-by-default philosophy and opt-in paid-compute model
  - Prerequisites (Python 3.12, frontend npm)
  - Validation gate (`make validate`) and individual gates (`make secrets`, `make lint`, `make typecheck`, `make test`, `make coverage`)
  - Gated-tier markers (`modal`, `scientific`, `e2e`) and their enable flags
  - Protocol and data verification commands
  - Frontend commands
  - GPU/paid-compute targets with explicit acknowledgement requirements
  - Approval-artifact format for `gpu-full`
  - Quick-start for reviewers
- Fixed `tests/unit/test_verify_registry_script.py`: updated all test fixture run_id values from `000001` (6 hex chars) to `00000001` (8 hex chars) to match the `RUN_ID_PATTERN` regex `^run_[0-9]{8}T[0-9]{6}Z_[0-9a-f]{8}$`.
- Fixed `tests/unit/test_makefile.py`: reformatted an over-long line to satisfy ruff E501 (103 > 100).
- `scripts/verify_registry.py` already implemented with correct parent-link validation — tests now pass.

## FILES CREATED

- `COMMAND_REFERENCE.md`
- `docs/project/reports/milestone_020.md` (this report)

## FILES MODIFIED

- `tests/unit/test_verify_registry_script.py` (run_id format fix in 3 fixtures)
- `tests/unit/test_makefile.py` (line-length fix)
- `docs/project/MILESTONE_STATUS.md` (row 020 → PASS)

## COMMANDS RUN

- `./scripts/validate_local.sh` — secret scan, ruff, mypy, pytest, coverage
- `make help` — confirms all targets listed
- `make protocol-verify` — protocol validates OK
- `make registry-verify` — registry verifies OK (empty registry)
- `make gpu-pilot` / `make gpu-full` — refuse correctly without acknowledgement

## TESTS AND RESULTS

- Full suite: **181 passed, 3 deselected** (default tiers)
- Coverage: **98.66%** (floor 95%)
- ruff: All checks passed
- mypy (strict): Success, no issues in 8 source files
- Secret scan: `OK: no secret patterns found in tracked files.`

## ENGINEERING VALIDATION

- **Validation 1:** `make help` lists all required targets including gpu-pilot and gpu-full.
- **Validation 2:** GPU targets are clearly named and never default — `.DEFAULT_GOAL := help`, no non-GPU target depends on a gpu target.
- **Validation 3:** GPU commands refuse without acknowledgement:
  - `make gpu-pilot` → REFUSED without `EVOVARIANT_TR_PAID_COMPUTE_ACK`
  - `make gpu-full` → REFUSED without acknowledgement and approval artifact
- **Validation 4:** `make data-verify` without `MANIFEST=` fails with actionable error.
- **Validation 5:** `make protocol-verify` and `make registry-verify` both pass on the current frozen protocol and empty registry.
- No destructive `clean` target exists in the Makefile.

## COST / EXTERNAL CALLS

- None. All validation is CPU/local/free. No GPU, no Modal, no cloud spend.

## EVIDENCE GENERATED

- `validate_local.sh` output: `ALL GATES PASSED` (181 passed, 98.66% coverage)
- `make help` output: lists all targets
- `make gpu-pilot` / `make gpu-full` refusal messages with cost warnings

## GIT STATUS

- Untracked: `Makefile`, `scripts/verify_registry.py`, `tests/unit/test_makefile.py`, `commands/verify_registry_script.py`, `COMMAND_REFERENCE.md`.
- Modified: `tests/unit/test_verify_registry_script.py`, `tests/unit/test_makefile.py`, `docs/project/MILESTONE_STATUS.md`.
- Local commit to follow on the feature branch.

## RISKS / OPEN QUESTIONS

- The Makefile is a control surface only; actual GPU data-plane implementation lands at M52–M69.
- COMMAND_REFERENCE.md must be kept in sync with Makefile changes; `test_makefile.py` provides meta-tests that help enforce this.

## NEXT MILESTONE

- 021 — Design the data directory and no-raw-data Git policy.

## DO NOT CONTINUE IF

- `make validate` does not pass (all gates must be green).
- GPU targets execute without the cost acknowledgement.
- `COMMAND_REFERENCE.md` diverges from the Makefile targets.
