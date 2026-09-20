# Project State — EvoVariant-TR ML Extension

## Current state — 2026-09-21

Repository: `https://github.com/UtkarsHMer05/EvoVariant-TR-`

Current phase: `PHASE 19 — Final release gate` (independent local work complete; gated
scientific phases remain blocked)

Phase status: `BLOCKED / PARTIAL` at the final release gate. The repository now has the
schema-validated control plane, fail-closed model registry/adapters, deterministic CPU-only
contracts for later experiment families, a complete evidence-gated research-workbench UI, and
passing local Python/frontend build gates. The fresh clean-room clone now reproduces the default
CPU suite and frontend build after dependency installation. No candidate model has verified
parity/smoke evidence, no paid Modal pilot or model-weight download has run, no scientific result
artifact is registered, and the repository still lacks automated browser E2E coverage and
registry-driven figure output. No model
download, training, HPO, fine-tuning, locked-test evaluation, or clinical classification has been
started.

Last passing source baseline: `1d9cf43` (frontend lint/typecheck/build gate cleanup).
Phase 0 handoff checkpoint: `89e5751`.
Phase 1 implementation commit: `1f777b5`.
Phase 2 implementation commits: `45c2a47`, `3f385fe`.
Phase 3 implementation commit: `f2dcc1f`.
Phase 4 implementation commit: `cc7de42`.
Phase 5 implementation commit: `473d314`.
Later-phase CPU contract/control-surface commit: `7127fc7`.
Research-workbench UI commit: `459ad11`.
Clean-bootstrap dependency commit: `22dac0f`.
Clone-safe clean-room test commit: `e52d7ab`.
Generated-metadata hygiene commit: `421a7ef`.
Final gate documentation commit: `942e042`.
Frontend lint-gate implementation commit: `1d9cf43`.

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
- Historical Phase 0/2/4 checkpoints remain recorded in the phase ledger. The current local gate
  passes secret scan, Ruff, strict mypy over 51 source files, `610 passed, 33 deselected, 1
  warning`, and `95.34%` coverage.
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
- The safe Modal preflight now verifies `modal_installed: true` and
  `modal_authenticated: true` through the project environment's sibling Modal executable and
  `modal app list`. This is only account/CLI evidence: no remote function, image build, model
  load, GPU inference, deployment, or paid-compute operation was invoked because the required
  acknowledgement is absent. The resulting local ledger entry records `PLANNED`, null cost,
  and no approval artifact rather than claiming a pilot.
- Phase 3 recomputed the public archives into a streaming temporal audit and a gene-grouped
  development split. The structural gate is green: 239,992 development records, 191,957
  TRAIN, 48,035 VALIDATION, 946 locked temporal records, zero normalized-ID overlap, zero
  train/validation gene overlap, zero duplicate split IDs, and deterministic rebuild.
- The recomputed temporal cohort is not identical to the handoff QA target: 1,402,895 t0 VUS,
  946 final temporal records (536 B/LB and 410 P/LP), and two t0/t1 gene annotation changes.
  The source archive hashes match the checked-in manifests. The full discrepancy audit is in
  `research/ml_extension/splits/phase3_manifest_summary.json`; model scoring remains blocked
  until it is resolved or explicitly approved through the deviation process.
- Modal identity is now reconciled in the active execution path: app `evovariant-tr`, existing
  volume `hf_cache` mounted at `/root/.cache/huggingface`, H100, the pinned NGC PyTorch image,
  and Evo2 repository revision `4b509ec2a22d6de472659f908bcb0714265ad3a7`. The app fails closed
  when the named volume is absent instead of silently creating an unapproved resource. Stale
  historical configuration remains documented as historical evidence, not as an active target.
- Phase 5 model registry verification passes for seven candidate manifests under
  `research/ml_extension/models/`; the included-model count is intentionally zero. Every
  candidate remains `PLANNED` with `NOT_VERIFIED` or `DEFERRED` provenance, so no candidate can
  silently enter a benchmark. `Evo2Adapter` reports deferred parity when the local package/GPU
  path is absent; other adapters report deferred official-source/smoke evidence.
- Official ClinVar t0/t1 archives are present under the ignored `data/raw/clinvar/` paths and
  match the checked-in manifests. The generated Phase 3 record-level outputs remain ignored;
  the tracked summary preserves the QA-count discrepancy, and the experiment registry still
  has no scientific run records.
- The later-phase CPU-only framework is present in `experiment_control.py`, `benchmark.py`,
  `feature_store.py`, `supervised.py`, `hpo.py`, `ensemble.py`, `analysis_plans.py`,
  `figure_artifacts.py`, and `batch_pipeline.py`. It enforces validation-only selection,
  locked-test guards, content hashes, OOF stacking, frozen config hashes, and refusal to attach
  metrics to non-completed status artifacts.
- The required phase command surface now writes explicit no-result status artifacts for Phases
  6–19 under ignored `research/runs/phase*_status.json`. These artifacts contain blockers and
  no metrics; they do not promote synthetic fixtures to scientific evidence.
- The research workbench at `apps/web/src/app/analysis/page.tsx` exposes all 14 required
  top-level areas. A local production-server browser smoke verified navigation, fail-closed
  single-variant rendering, blocked temporal empty state, and protocol metadata loading. The
  full frontend source tree now passes ESLint with zero errors/warnings, and the canonical
  `make web-check` target runs that lint gate plus TypeScript and the Next production build.
  Automated browser E2E coverage is not yet implemented.

## Experiments and artifacts

Completed experiments: none in the ML extension. Phase 0 ran only free local deterministic,
scientific, and API validation tiers; Phase 3 ran only public-data parsing, cohort auditing,
and split construction; later phases ran only CPU contract tests and status surfaces, not model
inference or outcome optimization.

Pending experiments: all `ZS-*`, `REP-*`, `CLF-*`, `HPO-*`, `FT-*`, `ENS-*`, `CAL-*`, `ABS-*`,
`ABL-*`, `ROB-*`, and `STAT-*` work. Phase 3 data/split artifacts are complete; zero-shot
scoring is held behind the QA discrepancy review, model-inclusion evidence, and real Modal gate.
The status artifacts for Phases 6–15, 17, and 19 are explicit `BLOCKED` records; Phase 16 is
blocked on automated browser E2E and registered outputs; Phase 18 is blocked on browser E2E,
figure, and paid-compute evidence, although the clean-room CPU/build rerun itself now passes.

Last experiment run: none.

Last generated artifacts: ignored record-level Phase 3 outputs under
`data/derived/ml_extension/phase3/`, with the reviewable summary and hashes at
`research/ml_extension/splits/phase3_manifest_summary.json`; schema-validated candidate model
manifests under `research/ml_extension/models/`; and ignored no-result status artifacts under
`research/runs/`. No model result artifact was generated.

Current Modal assets: source scaffolding plus a validated no-spend preflight. The root app and
`modal_config.py` use `evovariant-tr`, H100, `hf_cache`, the pinned image, and the pinned Evo2
source revision. The authenticated CLI listing does not prove that the named app, volume,
image, weights, or inference path exists remotely; those remain unverified until an explicitly
authorized pilot runs.

Monthly budget assumption: approximately `$30/month` included compute as stated by the master
prompt; pricing and credits were not queried in Phase 0. The historical `$500` approval file
is not treated as current ML-extension authorization.

Estimated spend to date: `$0` for local validation and Phase 3 data work.

Measured spend to date: `$0`; no Modal/GPU, model-weight download, or old endpoint call was
made.

## Known blockers and exact next action

Known blockers are the required real Modal pilot (paid-compute acknowledgement and remote
inference evidence), the unresolved discrepancy between the recomputed temporal cohort and the
validation-only QA target, the absence of verified model weights/checkpoints, and the zero-model
inclusion gate. Independent local gates and a fresh clean-room CPU/frontend rerun now pass;
automated browser E2E coverage is absent, registry-driven figure regeneration has no inputs, and
no registered result artifacts exist. A fresh `npm ci` also reports 13 dependency vulnerabilities
(2 low, 2 moderate, 8 high, 1 critical); no automatic audit fix was applied.

Exact next action: preserve this state, then obtain explicit authorization and verified model/
compute evidence before running a tiny Modal pilot. Resolve or formally approve the Phase 3 QA
deviation before scoring; add automated browser E2E and registry-driven figure evidence before
releasing. Do not run model scoring, read locked labels for selection, or start paid Modal work
without the corresponding gate.
