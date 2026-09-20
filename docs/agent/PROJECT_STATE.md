# Project State — EvoVariant-TR ML Extension

## Current state — 2026-09-21

Repository: `https://github.com/UtkarsHMer05/EvoVariant-TR-`

Current phase: `PHASE 1 — Control plane and ML-extension protocol`

Phase status: `PASS` for the control-plane gate. Phase 2 is next. No model download,
training, HPO, fine-tuning, locked-test evaluation, or paid Modal work has been started.

Last passing source baseline: `a5604eebec449dc95983f7570c483c443aa15bd8`.
Phase 0 handoff checkpoint: `89e5751`.
The Phase 1 implementation commit is recorded in the Phase 1 ledger entry after commit.

Active branch/worktree: `research/evovariant-tr` at
`/Users/utkarshkhajuria/Desktop/EvoVariant`

## Handoff extraction

- All 18 entries in `HANDOFF_MANIFEST.json` were extracted root-relative and verified by exact
  path, byte count, and SHA-256.
- The verified archive is preserved outside the working tree at
  `/private/tmp/EvoVariant_TR_Codex_Handoff.verified.zip`.
- No existing repository file collided with a handoff entry; existing project work was not
  overwritten.

## Existing strong assets confirmed

- Frozen original temporal protocol under `research/protocol/`.
- ADRs for temporal design, zero-shot policy, exact windowing, RC, calibration, Modal cost
  gates, no-test-label tuning, and evidence stages.
- Testable Python scientific modules under `src/evovariant_tr/`.
- Unit/contract/integration/scientific/modal/e2e test taxonomy.
- Existing comparator, calibration, abstention, error-analysis, manifest, registry, and cost
  policy scaffolding.
- Existing Next.js app under `apps/web` and Modal entrypoint scaffolding.

## Phase 0 findings

See `docs/agent/BASELINE_AUDIT.md` for full command output and reconciliation. The key
verified facts are:

- Original protocol YAML hash is intact:
  `78799000023ca157b72836a0ec603abb20c93960b15fba09485bd0dffbbb1525`.
- Phase 1 control plane is present under `research/ml_extension/`, with a machine-readable
  extension protocol, split policy, hash record, and strict JSON Schemas for model, split,
  experiment, and cost records.
- `validate-ml-control-plane` and the new contract tests pass; the original protocol hash
  remains unchanged.
- Ruff, strict mypy, protocol checks, empty-registry verification, synthetic scientific tests,
  and synthetic API E2E tests pass when invoked through available interpreters.
- `make validate` is not green: repository shell scripts are mode `100644`, and the `.venv`
  launcher is not executable. Default pytest has 533 passed, 6 failed, 1 skipped, 33
  deselected; coverage is 95.26% despite those failures.
- Direct frontend TypeScript passes, but direct lint fails and direct Next build fails on an
  invalid dynamic-route `params` type. npm wrapper commands additionally fail with permission
  denied on `.bin` launchers.
- The active route still contains BRCA1-derived threshold/confidence classification behavior.
- The Python research API and proxy default to `FakeScorer`; `Evo2Scorer` compute/batch/cohort
  methods are unimplemented.
- The root Modal UCSC formula returns 8,193 bases for interior positions and 4,097 at the
  left edge for a nominal 8,192 context; it has no hard length assertion.
- Python API, Next `/analysis`, and Modal request/response schemas are incompatible.
- Modal identities/configuration disagree: canonical current app decision D-011 is
  `evovariant-tr`, while stale `evovariant-tr-v2`, `hf_cache`, A100/H100, and dedicated-volume
  references remain to be reconciled. No current Modal auth/deployment was verified.
- `data/raw/` is absent; ignored historical research results reference unavailable raw files,
  mismatch frozen protocol dates/QA counts, and are not current evidence. The experiment
  registry has no run records.

## Experiments and artifacts

Completed experiments: none in the ML extension. Phase 0 ran only free local deterministic,
scientific, and API validation tiers.

Pending experiments: all `ZS-*`, `REP-*`, `CLF-*`, `HPO-*`, `FT-*`, `ENS-*`, `CAL-*`, `ABS-*`,
`ABL-*`, `ROB-*`, and `STAT-*` work. Phase 1 control-plane artifacts are complete.

Last experiment run: none.

Last generated artifact: `docs/agent/BASELINE_AUDIT.md` plus this control-plane update; no
scientific result artifact was generated.

Current Modal assets: source scaffolding only. The root app names `evovariant-tr` and uses an
H100 class plus a volume named `hf_cache`; `modal_config.py` defaults to A100 and also returns
`hf_cache`; `RuntimeConfig` names `evovariant-tr-v2` and `evovariant-tr-model-cache`. There is
no verified current account asset inventory.

Monthly budget assumption: approximately `$30/month` included compute as stated by the master
prompt; pricing and credits were not queried in Phase 0. The historical `$500` approval file
is not treated as current ML-extension authorization.

Estimated spend to date: `$0` for this Phase 0 audit.

Measured spend to date: `$0`; no Modal/GPU or old endpoint call was made.

## Known blockers and exact next action

Known blockers are the findings above, especially the scientific scoring contract, legacy UI
classification, missing raw archives, incomplete registry/control plane, identity drift, and
validation permissions.

Exact next action: begin Phase 2 by repairing the canonical scoring contract. The repair must
preserve the frozen original protocol, enforce exact 8192-base windows, retain forward and RC
raw components, remove production fake-scorer defaults and legacy thresholding, and add contract
tests before any real model or paid compute work.
