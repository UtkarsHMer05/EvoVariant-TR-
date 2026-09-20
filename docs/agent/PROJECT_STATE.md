# Project State — EvoVariant-TR ML Extension

## Current state — 2026-09-21

Repository: `https://github.com/UtkarsHMer05/EvoVariant-TR-`

Current phase: `PHASE 3 — ML dataset and locked splits`

Phase status: `PASS` for the structural Phase 3 gate, with the frozen QA-count discrepancy
documented and downstream model scoring explicitly blocked until it is resolved or formally
accepted as a protocol deviation. No model download, training, HPO, fine-tuning, or paid
Modal work has been started.

Last passing source baseline: `a5604eebec449dc95983f7570c483c443aa15bd8`.
Phase 0 handoff checkpoint: `89e5751`.
Phase 1 implementation commit: `1f777b5`.
Phase 2 implementation commits: `45c2a47`, `3f385fe`.
Phase 3 implementation commit: `f2dcc1f`.

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
- Ruff, strict mypy, protocol checks, synthetic scientific tests, API contract tests, and
  synthetic API E2E tests pass through the repaired local environment.
- `make validate` now passes: secret scan, Ruff, strict mypy over 36 source files, default
  pytest (`567 passed, 33 deselected, 1 warning`), and the 95% coverage gate (`95.17%`).
- The canonical scoring contract now enforces exact 8,192-base windows, explicit coordinate
  and allele invariants, forward and reverse-complement raw components, and a consistency
  check for the reported primary delta.
- The Python research API, proxy, and frontend use one canonical GRCh38 variant payload;
  unconfigured services fail closed and no longer default to `FakeScorer`.
- The Evo2 adapter now has a fail-closed dependency boundary plus batch/cohort pathways, but
  actual Evo2 execution remains hardware/package gated.
- The frontend no longer computes or displays BRCA1-derived threshold/confidence clinical
  classification. It displays raw research signal and explicitly labels classification as
  unavailable.
- A real Modal pilot remains unverified: no Modal CLI/account authentication or paid-compute
  acknowledgement is available in this environment, so no deployment or GPU spend was run.
- Phase 3 recomputed the public archives into a streaming temporal audit and a gene-grouped
  development split. The structural gate is green: 239,992 development records, 191,957
  TRAIN, 48,035 VALIDATION, 946 locked temporal records, zero normalized-ID overlap, zero
  train/validation gene overlap, zero duplicate split IDs, and deterministic rebuild.
- The recomputed temporal cohort is not identical to the handoff QA target: 1,402,895 t0 VUS,
  946 final temporal records (536 B/LB and 410 P/LP), and two t0/t1 gene annotation changes.
  The source archive hashes match the checked-in manifests. The full discrepancy audit is in
  `research/ml_extension/splits/phase3_manifest_summary.json`; model scoring remains blocked
  until it is resolved or explicitly approved through the deviation process.
- Modal identities/configuration disagree: canonical current app decision D-011 is
  `evovariant-tr`, while stale `evovariant-tr-v2`, `hf_cache`, A100/H100, and dedicated-volume
  references remain to be reconciled. No current Modal auth/deployment was verified.
- `data/raw/` is absent; ignored historical research results reference unavailable raw files,
  mismatch frozen protocol dates/QA counts, and are not current evidence. The experiment
  registry has no run records.

## Experiments and artifacts

Completed experiments: none in the ML extension. Phase 0 ran only free local deterministic,
scientific, and API validation tiers; Phase 3 ran only public-data parsing, cohort auditing,
and split construction, not model inference or outcome optimization.

Pending experiments: all `ZS-*`, `REP-*`, `CLF-*`, `HPO-*`, `FT-*`, `ENS-*`, `CAL-*`, `ABS-*`,
`ABL-*`, `ROB-*`, and `STAT-*` work. Phase 3 data/split artifacts are complete; zero-shot
scoring is held behind the QA discrepancy review and real Modal gate.

Last experiment run: none.

Last generated artifacts: ignored record-level Phase 3 outputs under
`data/derived/ml_extension/phase3/`, with the reviewable summary and hashes at
`research/ml_extension/splits/phase3_manifest_summary.json`. No model result artifact was
generated.

Current Modal assets: source scaffolding only. The root app names `evovariant-tr` and uses an
H100 class plus a volume named `hf_cache`; `modal_config.py` defaults to A100 and also returns
`hf_cache`; `RuntimeConfig` names `evovariant-tr-v2` and `evovariant-tr-model-cache`. There is
no verified current account asset inventory and no pilot spend.

Monthly budget assumption: approximately `$30/month` included compute as stated by the master
prompt; pricing and credits were not queried in Phase 0. The historical `$500` approval file
is not treated as current ML-extension authorization.

Estimated spend to date: `$0` for local validation and Phase 3 data work.

Measured spend to date: `$0`; no Modal/GPU, model-weight download, or old endpoint call was
made.

## Known blockers and exact next action

Known blockers are the required real Modal pilot (missing verified CLI/auth/paid-compute
acknowledgement), the unresolved discrepancy between the recomputed temporal cohort and the
validation-only QA target, unresolved Modal identity/cache inventory, and the absence of
verified model weights/checkpoints. The frontend still has pre-existing lint and Next 15
dynamic-route build failures outside the scoring contract.

Exact next action: use the Phase 3 audit to reconcile the QA discrepancy without changing
immutable protocol fields, while independently implementing the cost-aware Modal foundation
and evidence-gated model registry. Do not run model scoring, read locked labels for selection,
or start paid Modal work without the corresponding gate.
