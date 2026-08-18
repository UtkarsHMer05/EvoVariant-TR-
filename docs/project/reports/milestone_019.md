# Milestone 019 — Create secrets, environment, and cost-control policy

- **MILESTONE:** 019
- **TITLE:** Create secrets, environment, and cost-control policy
- **STATUS:** PASS
- **DATE:** 2026-08-19

## WHAT EXISTED BEFORE

- `.gitignore` rules for `.env` (root + `apps/web`), `__pycache__`, `.venv`, `node_modules`, `.next`.
- `tests/conftest.py` with `--run-modal` flag and `EVOVARIANT_TR_PAID_COMPUTE_ACK=I_ACCEPT_COSTS` acknowledgement gating (created at M17).
- No cost-control module, no secret scanner, no names-only env templates, no log redaction.

## WHAT CHANGED

- Added `src/evovariant_tr/cost_policy.py`: paid-compute acknowledgement gate, frozen
  `FullRunApproval` schema (approved Modal env `evovariant-tr`, GPU `H100` only), rejection of
  forbidden old-project deployment identities, and `require_full_run_approval()` hard gate for
  full scoring (re-enforced at M69).
- Added `src/evovariant_tr/redact.py`: `redact()` replaces credential-looking substrings
  (key=value secrets with ≥16-char values, `Bearer` tokens, bare `sk-…`/`ghp_…`/`AKIA…`/
  `xox…-…` shapes) with `***REDACTED***`; `RedactingFilter` attaches to any logger.
- Added `scripts/check_secrets.sh`: scans all git-tracked files (excluding `*.example` and the
  scanner itself) for credential patterns; wired as the first gate in `scripts/validate_local.sh`.
- Added names-only `.env.example` at repo root and `apps/web/.env.example` (public vs
  server-only split documented; Modal credentials have no `NEXT_PUBLIC_` form).
- Added `docs/security/SECRETS_AND_COST_POLICY.md` documenting all eight required actions.
- `cost_policy.load_full_run_approval` now wraps JSON parsing in the same `CostPolicyError`
  path as schema validation, so malformed artifacts fail with an actionable error.

## FILES CREATED

- `src/evovariant_tr/cost_policy.py`
- `src/evovariant_tr/redact.py`
- `scripts/check_secrets.sh`
- `.env.example`
- `docs/security/SECRETS_AND_COST_POLICY.md`
- `tests/unit/test_cost_policy.py`
- `tests/unit/test_redact.py`

## FILES MODIFIED

- `apps/web/.env.example` (documented client/server split and the one client variable)
- `scripts/validate_local.sh` (secret scan added as first gate)
- `docs/project/MILESTONE_STATUS.md` (019 → PASS)

## COMMANDS RUN

- `git status --short`; `git remote -v` (no remotes)
- `./scripts/check_secrets.sh`
- `./scripts/validate_local.sh` (secret scan → ruff → mypy strict → pytest → coverage floor)
- Explicit V2/V3 gate checks via `python -c` (approval artifact refusal; no auto-acknowledgement)

## TESTS AND RESULTS

- `tests/unit/test_cost_policy.py` — 25 tests: all pass.
  - Happy path: acknowledgement on/off, valid approval round-trip, frozen model,
    approved/forbidden identity sets disjoint.
  - Invalid input: negative/zero budget, forbidden env, unapproved env/GPU, empty fields,
    extra fields (Pydantic `ValidationError`).
  - Validation 2: missing artifact, invalid JSON, invalid content, forbidden identity all
    raise `CostPolicyError`; valid artifact loads.
- `tests/unit/test_redact.py` — 16 tests: all pass.
  - Key=value, quoted, Bearer, lowercase keys, multiple secrets, bare token shapes.
  - Short code-like values not redacted (≥16-char rule); clean text unchanged.
  - Determinism; `RedactingFilter` on logger message and on `record.args`.
- Full local suite: **164 passed, 3 gated/deselected**, coverage **98.66%** (floor 95%).
  `cost_policy.py` 100%, `redact.py` 100%.

## SCIENTIFIC VALIDATION

- No scientific logic touched; no protocol change (deviation log unchanged).
- No temporal-test data involved. Evidence-stage language unaffected.

## ENGINEERING VALIDATION

- ruff clean; mypy strict clean (8 source files).
- Secret scan: `OK: no secret patterns found in tracked files.`
- Browser bundle isolation: only `NEXT_PUBLIC_ANALYZE_SINGLE_VARIANT_BASE_URL` is client
  visible (names-only template); Modal credentials server-only by construction.

## EXTERNAL CALLS / GPU / COST

- None. No network calls, no GPU, no paid compute. Scanner is local `git grep` only.

## EVIDENCE GENERATED

- `check_secrets.sh` output: `OK: no secret patterns found in tracked files.` (exit 0)
- V2: `require_full_run_approval('/tmp/nonexistent_approval.json')` →
  `CostPolicyError: full scoring requires an explicit approval artifact …`
- V3: `paid_compute_acknowledged()` → `False` in the ordinary (unacknowledged) environment;
  modal tier additionally hard-blocked in `tests/conftest.py`.
- `validate_local.sh`: `ALL GATES PASSED` (164 tests, 98.66% coverage).

## GIT STATUS

- `git diff --check` clean; only intended M19 files staged.

## RISKS / OPEN QUESTIONS

- `check_secrets.sh` excludes `docs/security/*` from scanning (the policy doc quotes example
  token shapes). The scanner itself is also excluded. Both exclusions are documented in the
  script header and the policy doc.
- Full-run approval artifact format is defined but the approval workflow (who writes it) is a
  human step; automated creation is deliberately not implemented.

## NEXT MILESTONE

- **020 — Create a single project control surface** (Makefile + COMMAND_REFERENCE.md).

## DO NOT CONTINUE IF

- None — gate passed.