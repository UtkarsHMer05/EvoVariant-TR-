# Phase 0 Baseline Audit — EvoVariant-TR ML Extension

Date: 2026-09-21
Phase: `PHASE 0 — Diagnostic snapshot and safety baseline`
Audit status: `PASS` for the diagnostic gate; scientific/code repair is intentionally deferred.

This document records the state observed before any ML-extension implementation. It is the
current baseline for the handoff. Historical milestone reports and saved legacy outputs are
not treated as proof of the current state unless the corresponding command was rerun here.

## 1. Scope and safety boundary

- The repository was inspected before extraction or code edits.
- `EvoVariant_TR_Codex_Handoff.zip` was verified as a valid ZIP with 18 manifest-listed
  project files and no wrapper directory or path collision.
- The archive entries were extracted root-relative. Every manifest entry exists at its intended
  path and matches its manifest byte count and SHA-256.
- The verified ZIP was moved out of the working tree to
  `/private/tmp/EvoVariant_TR_Codex_Handoff.verified.zip` after verification. It was not
  overwritten or deleted irreversibly.
- No source, test, frontend, protocol, or deployment behavior was changed during Phase 0.
  The only repository edits made after extraction are this audit and the required persistent
  state/ledger/decision updates.
- No subagent or new worktree was created for this diagnostic pass. The audit has shared
  contracts and one documentation owner, so it was run sequentially. The pre-existing
  `.kilo/worktrees/mysterious-gilmoreosaurus` detached worktree was observed and left untouched.

## 2. Git and repository baseline

| Item | Observed value |
|---|---|
| Repository root | `/Users/utkarshkhajuria/Desktop/EvoVariant` |
| Remote | `origin` → `https://github.com/UtkarsHMer05/EvoVariant-TR-.git` |
| Active branch | `research/evovariant-tr` |
| Upstream tracking | `origin/research/evovariant-tr` |
| HEAD | `a5604eebec449dc95983f7570c483c443aa15bd8` |
| HEAD subject | `commit` |
| Initial tracked worktree state | clean; only the handoff ZIP was untracked |
| Current tracked diff | none; extracted handoff/control files are untracked additions |

The checkout contains the existing Python package under `src/evovariant_tr`, a Next.js app
under `apps/web`, legacy Modal/backend material under `evo2-backend/`, a newer root Modal
entrypoint, tests in unit/contract/integration/scientific/modal/e2e tiers, frozen protocol and
ADR documentation, manifests, ignored historical result artifacts, and an initially empty
experiment registry. The root also contains ignored runtime/cache material (`.venv`,
`.venv-baseline`, `.next`, Python caches, `.kilo`, and coverage caches).

## 3. Handoff extraction verification

The archive integrity check passed (`unzip -t`). The archive entries matched the keys in
`HANDOFF_MANIFEST.json`, excluding the manifest file itself. All 18 listed files passed exact
byte and SHA-256 verification:

- `CODEX_MASTER_PROMPT.md`
- `README_START_HERE.md`
- 14 files under `docs/agent/`
- `experiments/templates/experiment_config.yaml`
- `research/ml_extension/PROTOCOL.md`

No existing repository file had the same path as an archive entry, so no merge or overwrite
decision was required. The handoff archive did not contain an extra
`EvoVariant_TR_Codex_Handoff/` directory.

## 4. Frozen protocol and existing ADR reconciliation

The original protocol remains unchanged and valid:

- `research/protocol/protocol.yaml` SHA-256:
  `78799000023ca157b72836a0ec603abb20c93960b15fba09485bd0dffbbb1525`
- Protocol version `1.0.0`, frozen 2026-08-18.
- Immutable t0/t1 releases are 2025-01-02 and 2026-08-06, GRCh38, unique normalized
  biallelic A/C/G/T germline SNVs, >=2 review stars, and P/LP versus B/LB later resolution.
- The primary endpoint is AUROC with 2,000 gene-clustered bootstrap replicates and seed
  `20260814`.
- The primary context is exactly 8,192 bases, and the primary score is the retained
  forward/RC aggregate `(delta_fwd + delta_rc) / 2`.
- Test labels are never allowed to fit or select a calibrator, threshold, checkpoint, context,
  comparator, subgroup, score direction, or abstention rule.
- `research/protocol/DEVIATION_LOG.md` still reports no deviations.

The existing ADRs correctly preserve the scientific boundaries, exact-window intent, RC
retention, disjoint calibration, cost gates, and research-only wording. However, historical
ADR/project-identity text still records `evovariant-tr-v2` as the proposed/confirmed Modal
app identity, while current code and cost policy use `evovariant-tr`. This is a real naming
drift, not a protocol change; the canonical ML-extension identity is recorded as D-011 below
and deployment reconciliation is deferred until the appropriate phase.

The pre-existing `docs/project/MILESTONE_STATUS.md` marks milestones 001–100 as PASS. Those
are historical project records, not fresh evidence for this ML-extension handoff. Current
commands below show that the present checkout does not satisfy the new master prompt's
scoring, registry, frontend, or clean-room completion requirements.

## 5. Local validation evidence

The repository's intended Python environment is present but not directly executable in this
checkout: `.venv/bin/python` is a non-executable 10-byte launcher file containing
`python3.12`; the three shell gate scripts are also mode `100644` in `HEAD`. For diagnostic
coverage, the installed `.venv` site-packages were used with the system Python 3.12.8
interpreter at `/Library/Frameworks/Python.framework/Versions/3.12/bin/python3.12`. This
does not change project files.

| Check | Result | Evidence |
|---|---|---|
| `make validate` | FAIL, exit 2 | `./scripts/validate_local.sh: Permission denied` |
| `bash scripts/check_secrets.sh` | PASS | No credential patterns in tracked files |
| Ruff | PASS | `All checks passed!` |
| Strict mypy | PASS | `Success: no issues found in 34 source files` |
| Default pytest | FAIL | 533 passed, 6 failed, 1 skipped, 33 deselected; failures are script executability and `.venv/bin/python`/Make-target assumptions |
| Coverage pytest | FAIL overall, floor reached | Same six test failures; total coverage 95.26%, above the 95% floor |
| Scientific tier (synthetic/local) | PASS with one skip | 7 passed, 1 skipped |
| Python API E2E tier | PASS with one skip | 14 passed, 1 skipped; uses local test clients/fake scoring, not a real Evo2 run |
| Protocol CLI | PASS | `evovariant_tr.cli validate-protocol` accepted protocol 1.0.0 |
| Protocol contract tests | PASS | Frozen hash and schema contract passed |
| Registry verifier | PASS but empty | `experiments/registry` contains no run records |

The six default-test failures are diagnostic evidence of the current checkout/environment;
they were not repaired in Phase 0. No Modal test was enabled and no paid-compute
acknowledgement was set.

## 6. Frontend validation evidence

`apps/web/node_modules` is present. The npm wrapper commands cannot execute because the
installed `.bin/tsc` and `.bin/next` files lack executable permission, so the underlying JS
entrypoints were also run directly.

| Check | Result | Evidence |
|---|---|---|
| `npm run typecheck` | FAIL, exit 126 | `.bin/tsc: Permission denied` |
| Direct TypeScript entrypoint | PASS | `node node_modules/typescript/bin/tsc --noEmit` exit 0 |
| `npm run lint` | FAIL, exit 126 | `.bin/next: Permission denied` |
| Direct Next lint | FAIL, exit 1 | Unsafe `any`, floating promises, nullish/optional-chain, unused-variable, and related lint errors across the app |
| `npm run build` | FAIL, exit 126 | `.bin/next: Permission denied` |
| Direct Next build | FAIL, exit 1 | Compilation succeeds, then `apps/web/src/app/api/batch/[id]/route.ts` has an invalid Next.js 15 GET `params` export type; lint is skipped by the build invocation |

The direct build reports Next.js 15.3.1 from the installed dependency tree. No `npm ci` was
rerun during Phase 0, and no package lock or source file was changed.

## 7. Security, environment, and data boundary

- The tracked-file secret scanner passed.
- `apps/web/.env` and `apps/web/.env.local` are ignored by `apps/web/.gitignore`; values were
  not printed. The current `.env` contains the legacy `variant-analysis-evo2` identity, while
  `.env.local` contains the newer `evovariant-tr` identity. This is local configuration drift
  that must be resolved before a canonical frontend deployment claim.
- No Modal/Hugging Face/compute credential variables were set in the current process
  environment. Only variable names were inspected.
- `data/raw/` is absent in this checkout. The two `research/data_manifests/*.json` files are
  metadata records for large ClinVar archives, not the repository's strict `Manifest` model,
  and the referenced archives were not available for verification.
- Raw data, derived research runs/results, model caches, and frontend/Python caches are
  gitignored according to `.gitignore`. Ignored does not mean present, valid, or reproduced.
- A second ignored detached worktree exists at `.kilo/worktrees/mysterious-gilmoreosaurus`
  at the same HEAD. It was not inspected for project state beyond inventory and was not
  modified.

## 8. Scoring-path audit

### 8.1 Canonical core window code

`src/evovariant_tr/sequence_window.py` implements a separate core convention. For an
interior position, `compute_window_coordinates_with_shift` returns 8,192 inclusive bases;
for a left-edge test it returns positions 1–8,192. The synthetic scientific tests pass these
invariants. `generate_reference_window` does not itself call `validate_sequence_content`, so
the caller/adapter boundary still needs an explicit length/reference/mutation assertion before
real research scoring.

### 8.2 Active root Modal service

`evo2_scorer_app.py:153-155` computes:

```text
start = max(0, position - 1 - half_window)
end   = position - 1 + half_window + 1
```

For an interior position, the resulting half-open interval has length 8,193. At position 1
it has length 4,097, and there is no chromosome-length clamp or hard length assertion. The
service therefore does not satisfy the frozen 8,192 contract. It also scores only forward
orientation, fetches live UCSC sequence per request without an explicit timeout, and returns
no canonical variant ID, sequence hashes, window coordinates, run ID, or failure taxonomy.

### 8.3 Legacy Modal backend

`evo2-backend/main.py` is a legacy monolith. It repeats the same 8,193-base UCSC formula,
uses the old `variant-analysis-evo2` app identity, contains the BRCA1-derived threshold and
confidence constants, has no RC scoring path, and has an unpinned Evo2 git clone/checkpoint
identity. Its outputs and `evaluation/results/final_100` are legacy baseline material only.

### 8.4 Python Evo2 adapter

`src/evovariant_tr/evo2_scorer.py` declares parity requirements but `_compute_log_likelihood`
raises `NotImplementedError`; `score_batch` and `score_cohort` also raise
`NotImplementedError`. The root Modal service bypasses this adapter and calls
`self.model.score_sequences` directly. The adapter and deployed service do not yet implement
one canonical scoring contract.

### 8.5 Fake-versus-real scorer boundary

`src/evovariant_tr/fake_scorer.py` is correctly documented as test-only, and orchestration
accepts an injected scorer. However, `src/evovariant_tr/api.py:35` and
`src/evovariant_tr/api_proxy.py:18` instantiate `FakeScorer(scale=1.0)` as their module-level
service scorer. The Python research API therefore does not use the real Evo2 scorer. The
active Next route proxies directly to the root Modal URL instead of this Python API, so there
are two ununified scoring paths.

### 8.6 Legacy classification behavior

`apps/web/src/app/api/score/variant/route.ts:38-46` still applies the BRCA1-derived
`-0.0009178519` threshold and class-specific standard deviations, then returns
`prediction` and `classification_confidence`. The legacy backend contains the same logic.
The UI renders those fields as “Likely pathogenic”, “Likely benign”, a confidence bar, and
ClinVar agreement. This violates the frozen research-only boundary and must be replaced by
raw/provenance-first output in a later phase; no such change was made here.

### 8.7 API and frontend schema mismatch

- The Python API accepts `{chrom, start, ref, alt, strand}` and constructs a synthetic A/T
  window rather than validating against a GRCh38 reference.
- The root Modal service accepts `{chromosome, variant_position, alternative, genome}` and
  derives the reference base from live UCSC data; it does not accept the declared reference
  allele.
- `/analysis` posts the Python-style `{chrom,start,ref,alt,strand}` body to the Next route,
  which forwards it unchanged to the Modal-style service. The Modal service will not receive
  its required keys.
- The Next route transforms the response using the old classification contract and reads
  `variant_position/reference/alternative` from the request body; the `/analysis` body uses
  `start/ref/alt`, so its transformed metadata is empty/zero even apart from the upstream
  schema failure.
- `/api/protocol` returns only version/date/identity, while `/analysis` expects context and
  scorer fields as well. The root UI uses a separate legacy flow through `genome-api.ts`.

## 9. Modal and deployment audit

| Surface | Observed state |
|---|---|
| Root app entrypoint | `modal.App("evovariant-tr")`, H100 class, `hf_cache` volume |
| `modal_config.py` | app `evovariant-tr`, default GPU A100, `hf_cache` volume |
| `RuntimeConfig` | app `evovariant-tr-v2`, volume `evovariant-tr-model-cache`, H100 |
| Cost policy/approval | app/environment `evovariant-tr`, H100; approval max budget `$500.0` |
| ADR/project identity | historical `evovariant-tr-v2` proposal/confirmation |
| Modal CLI | no executable `modal` command on PATH; `.venv/bin/modal` is non-executable |
| Modal package | importable from the existing `.venv` site-packages |
| Auth/app listing | not verified; `check_modal_environment()` could not spawn `modal` |
| Paid work in this audit | none; measured spend `$0` |

The root Modal image clones the Evo2 repository from an unpinned upstream branch during image
build and does not record a checkpoint revision or model hash. The active `services/modal/`
directory contains only `.gitkeep`; Modal implementation is split between the root entrypoint,
legacy backend, and helper configuration. No machine-readable cost ledger or current account
asset inventory exists in the checkout.

The checked-in approval artifact is historical metadata for `full_primary_evo2_scoring`, uses
the symbolic value `frozen_v1.0.0_2026-08-18` rather than the current protocol SHA-256, and
has a `$500` ceiling. It is not evidence that the current ML extension is approved or that
current Modal pricing/credits were checked. No paid command was launched.

## 10. Registry and saved-artifact audit

- `experiments/registry/` contains only `.gitkeep`; there are no run records or append-only
  log entries. The JSON schema exists at `research/schemas/experiment_run.schema.json` and
  direct empty-registry verification passes.
- `research/ml_extension/PROTOCOL.md` is explicitly DRAFT. The machine-readable ML-extension
  twin, split manifests, model registry, cost ledger, and result registrations do not yet
  exist. These are Phase 1+ deliverables.
- Ignored `research/results/` contains historical JSON snapshots (`cohort_primary`,
  `cohort_calibration`, `disjoint_check`, `qc_report`, and `gene_group_splits`). The saved
  primary snapshot reports 380,776 VUS and t0/t1 dates 2025-01-01/2026-08-01, which do not
  match the frozen protocol's QA target of 1,024 final temporal variants or its 2025-01-02 /
  2026-08-06 release dates. `qc_report.json` references raw files that are absent in the
  current checkout. These files are retained as historical/local artifacts, not promoted as
  current evidence.
- Tracked `evaluation/results/final_100/` contains a 100-row evaluation against the old
  `variant-analysis-evo2` endpoint and a BRCA1 dataset. It is explicitly legacy baseline
  material and cannot support an EvoVariant-TR or ML-extension result claim.
- `artifacts/baseline/command_log.txt` records a 2026-08-18 legacy smoke test; it states no
  GPU work was performed. That historical claim is consistent with this audit's zero spend,
  but it is not a current Modal deployment proof.

## 11. Phase 0 gate and deferred work

The Phase 0 gate passes because the actual current state, protocol hash, repository boundary,
validation evidence, known scientific hazards, deployment identity drift, artifact provenance,
and exact next dependencies are now documented. It does **not** mean the project is ready for
model training, HPO, fine-tuning, locked evaluation, or release.

The following are explicit blockers/deferred items for later phases:

1. Restore executable bits and make the local environment reproducible before using `make`
   as a green gate.
2. Resolve the canonical API/variant schema and eliminate the legacy classification contract.
3. Repair the exact 8,192-base boundary and assert reference/mutation/RC invariants.
4. Implement or replace the Evo2 adapter with a verified official scoring path and pinned
   model/checkpoint provenance.
5. Reconcile Modal app/volume/GPU configuration without reusing legacy deployment assets.
6. Rebuild or verify data/split manifests from the exact frozen archives before any real
   scoring; do not use the stale ignored cohort snapshots as current evidence.
7. Create the ML-extension protocol twin, registry/cost schemas, and locked train/validation/
   test policy before Phase 1 work is considered complete.
8. Keep the locked temporal test untouched; no training, HPO, model downloads, fine-tuning,
   or paid Modal work is authorized by this Phase 0 result.

## 12. Reproducibility command record

The key commands used for this audit were:

```text
git status --short --branch
git branch -vv
git show -s --format=fuller HEAD
git remote -v
unzip -t EvoVariant_TR_Codex_Handoff.zip
manifest path/byte/SHA verification (Python stdlib, read-only)
make validate
bash scripts/check_secrets.sh
python3.12 -m ruff check src tests scripts
python3.12 -m mypy
python3.12 -m pytest
python3.12 -m pytest --cov --cov-report=term -q
python3.12 -m pytest -o addopts='' --run-scientific -q tests/scientific
python3.12 -m pytest -o addopts='' --run-e2e -q tests/e2e
python3.12 -m evovariant_tr.cli validate-protocol --protocol research/protocol/protocol.yaml
python3.12 scripts/verify_registry.py --registry-dir experiments/registry
node node_modules/typescript/bin/tsc --noEmit
node node_modules/next/dist/bin/next lint
node node_modules/next/dist/bin/next build
```

All Python commands above that used the existing installed environment used Python 3.12.8
with `.venv/lib/python3.12/site-packages` on `PYTHONPATH` because the checked-in/working
`.venv/bin/python` launcher is not executable. No command in this audit downloaded a model,
called Modal, called the old endpoint, trained a model, or incurred compute spend.
