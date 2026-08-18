# Milestone 017 — Create the test taxonomy and minimum quality gates

- **MILESTONE:** 017
- **TITLE:** Create the test taxonomy and minimum quality gates
- **STATUS:** PASS
- **DATE:** 2026-08-18

## WHAT EXISTED BEFORE

- Only `tests/unit/` existed (6 test modules, 111 tests). No taxonomy, no gated tiers, no coverage floor, no single validation command.
- `tests/conftest.py` was just a sys.path shim.

## WHAT CHANGED

- Created the taxonomy directories: `tests/{unit,contract,integration,modal,scientific,e2e}`.
- `pyproject.toml` pytest config: default `addopts` deselects `modal`, `scientific`, and `e2e`; markers registered for all gated tiers plus `slow`. Coverage `fail_under = 95` for core deterministic modules.
- `tests/conftest.py` rewritten: registers `--run-modal`, `--run-scientific`, `--run-e2e` flags and hard-blocks gated tests in `pytest_collection_modifyitems` — modal additionally requires `EVOVARIANT_TR_PAID_COMPUTE_ACK=I_ACCEPT_COSTS`. This is a second safeguard on top of the addopts deselect, so even `pytest -m modal` cannot spend money.
- New tests:
  - `tests/contract/test_protocol_contract.py` — frozen protocol hash contract (M11 SHA-256), protocol contract fields, experiment-run JSON schema validity.
  - `tests/integration/test_registry_manifest_integration.py` — registry + manifest + evidence guards end-to-end on tiny temp fixtures (registered run → manifest → completed with verified output hashes; synthetic blocked from final paths; shard parent/child).
  - `tests/modal/test_modal_gating.py`, `tests/scientific/test_scientific_gating.py`, `tests/e2e/test_e2e_gating.py` — marked placeholders proving the gates (real bodies land at M52+/M37+/M97).
  - `tests/unit/test_test_taxonomy.py` — meta-tests for both acceptance validations.
- Created `scripts/validate_local.sh` (executable): ruff → mypy strict → default pytest tiers → coverage floor. Shebang pinned to `/bin/bash` because `/usr/local/bin/bash` on this machine is an x86_64 binary that forces Rosetta and breaks mypy's native extension.
- Created `docs/testing/TEST_TAXONOMY.md` documenting tiers, gates, and the quality floor.

## FILES CREATED

- `tests/contract/test_protocol_contract.py`
- `tests/integration/test_registry_manifest_integration.py`
- `tests/modal/test_modal_gating.py`
- `tests/scientific/test_scientific_gating.py`
- `tests/e2e/test_e2e_gating.py`
- `tests/unit/test_test_taxonomy.py`
- `scripts/validate_local.sh`
- `docs/testing/TEST_TAXONOMY.md`
- `docs/project/reports/milestone_017.md` (this report)

## FILES MODIFIED

- `pyproject.toml` (pytest markers/addopts, coverage floor)
- `tests/conftest.py` (gating logic)
- `docs/project/MILESTONE_STATUS.md` (row 017 → PASS)

## FILES REMOVED / MOVED

- None.

## COMMANDS RUN

- `mkdir -p tests/unit tests/contract tests/integration tests/modal tests/scientific` (+ `tests/e2e`)
- `python -m pytest -q` → **123 passed, 3 deselected in 2.62s**
- `./scripts/validate_local.sh` → ruff clean, mypy strict clean, 123 passed + 3 deselected, coverage **98.49% ≥ 95% floor** → `ALL GATES PASSED`

## TESTS

- 123 default-tier tests pass; 3 gated placeholders deselected.
- Meta-tests prove: default collection of gated dirs yields exit code 5 (nothing runnable); `--run-modal` without the ack still skips with the gate's reason; flag + ack opens the gate (placeholder then skips itself); scientific gate behaves the same; `validate_local.sh` exists and is executable.

## SCIENTIFIC VALIDATION

- The frozen protocol hash is now enforced as a contract test: any drift in `protocol.yaml` fails CI-local validation until a dated deviation is recorded.
- No scientific claims made; this milestone is process infrastructure.

## ENGINEERING VALIDATION

- **Validation 1:** default `python -m pytest` never launches paid compute — gated tiers are deselected by addopts AND hard-skipped by conftest (belt and braces, both proven by meta-tests).
- **Validation 2:** modal tests require the explicit `--run-modal` flag AND the `EVOVARIANT_TR_PAID_COMPUTE_ACK=I_ACCEPT_COSTS` acknowledgement; scientific tests require `--run-scientific`.
- Coverage floor enforced mechanically (`fail_under = 95`); current 98.49%.
- Environment quirk documented and fixed: x86_64 `/usr/local/bin/bash` forced Rosetta in scripts; shebang pinned to native `/bin/bash`.

## COST / EXTERNAL CALLS

- None. Zero external calls, zero GPU, zero spend.

## EVIDENCE GENERATED

- `validate_local.sh` full output (ALL GATES PASSED), coverage table, meta-test results.
- Stage: SYNTHETIC_TEST (process infrastructure only).

## GIT STATUS

- Files listed above; ledger updated. Local commit to follow; no remote configured, no push.

## RISKS / OPEN QUESTIONS

- Gated placeholder tests self-skip once unlocked; they are replaced by real Modal (M52–55), scientific (M37+), and E2E (M97) tests as those milestones land.
- The meta-tests spawn pytest subprocesses (~1s each); acceptable locally, could be marked `slow` if CI time ever matters.

## NEXT MILESTONE

- 018 — Create frontend migration scaffold under apps/web.

## DO NOT CONTINUE IF

- The default pytest command can collect or run any modal/scientific/e2e test.
- `./scripts/validate_local.sh` fails any stage.
- Coverage of core modules drops below 95%.
