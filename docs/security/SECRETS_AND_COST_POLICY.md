# SECRETS, ENVIRONMENT, AND COST-CONTROL POLICY — EvoVariant-TR (Milestone 019)

Purpose: prevent accidental credential exposure and unapproved GPU spending.

## 1. Secrets are never tracked

- `.env` files are gitignored at both the repo root and `apps/web/`. Only
  `.env.example` templates are committed, and they contain **names only, never
  values**.
- `scripts/check_secrets.sh` scans all tracked files for credential patterns
  (TOKEN/SECRET/PASSWORD/API_KEY assignments, `sk-…`, `ghp_…`, `AKIA…`,
  `xox…-…`, private-key headers). It runs as part of local validation and must
  stay clean.
- If a secret is ever committed: remove it, **rotate it immediately**, and purge
  it from history before any push.

## 2. Modal authentication

- Modal auth is configured with `modal token set` (stored in `~/.modal.toml`),
  **never** in `.env` files or the repository.
- The NEW project uses a fresh Modal environment/app identity
  (`evovariant-tr`), created at Milestone 52. The OLD project's identities
  (`variant-analysis-evo2`, `utkarshmer05--variant-analysis-evo2`) are
  **forbidden** as final infrastructure and are rejected by
  `evovariant_tr.cost_policy`.

## 3. Approved GPU environment

- Approved Modal environment names: `evovariant-tr`.
- Approved GPU type: `H100`.
- Both are enforced by `cost_policy.FullRunApproval`; any other value is
  rejected at validation time.

## 4. Budget approval before full scoring

- Full primary scoring (Milestone 69–70) **refuses to run** without an explicit
  approval artifact at `artifacts/approvals/full_run_approval.json` containing:
  `approved_by`, `approved_at`, `max_budget_usd`, `run_scope`,
  `modal_environment`, `gpu_type`, `protocol_hash`.
- `cost_policy.require_full_run_approval()` raises `CostPolicyError` if the
  artifact is missing or invalid. This gate is enforced again at M69.
- Smaller pilots (M55–68) are bounded by their registered scope and still
  require the paid-compute acknowledgement below.

## 5. Paid-compute acknowledgement

- Anything that spends money requires
  `EVOVARIANT_TR_PAID_COMPUTE_ACK=I_ACCEPT_COSTS` in the environment.
- `cost_policy.assert_paid_compute_allowed()` raises without it.
- The pytest `modal` tier additionally requires this exact value (see
  `tests/conftest.py`), so **paid runs are impossible from ordinary unit tests**
  (Validation 3).

## 6. Log redaction

- `evovariant_tr.redact.redact()` replaces credential-looking substrings
  (key=value secrets, `Bearer` tokens, `sk-…`, `ghp_…`, `AKIA…`, `xox…-…`) with
  `***REDACTED***`.
- `redact.RedactingFilter` can be attached to any logger so tokens never reach
  log files or reports.

## 7. Browser bundle isolation

- The frontend (`apps/web`) uses `@t3-oss/env-nextjs`. Only `NEXT_PUBLIC_*`
  variables may appear in the `client` block; server-only values stay in the
  `server` block and never enter the browser bundle.
- Modal credentials are server-only by construction and have no
  `NEXT_PUBLIC_` form. The frontend `.env.example` lists names only.

## 8. Validation

Run the secret scanner and the full local gate:

```bash
./scripts/check_secrets.sh
./scripts/validate_local.sh
```

Both must pass before any milestone is marked complete.
