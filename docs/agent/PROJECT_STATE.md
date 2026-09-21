# Project State — EvoVariant-TR ML Extension

## Current state — 2026-09-21

Repository: `https://github.com/UtkarsHMer05/EvoVariant-TR-`

Current phase: `PHASE 19 — Final release gate` (independent local work complete; gated
scientific phases remain blocked)

Phase status: `BLOCKED / PARTIAL` at the final release gate. The repository now has the
schema-validated control plane, fail-closed model registry/adapters, deterministic CPU-only
contracts for later experiment families, a complete evidence-gated research-workbench UI, and
passing local Python/frontend build gates. The Phase 17 export control surface now covers every
required figure/table family and can render only hash-verified registry artifacts; the current
bundle remains explicitly blocked with zero scientific outputs. The fresh clean-room clone now
reproduces the default CPU suite and frontend build after dependency installation. No candidate
model has verified parity/smoke evidence, no paid Modal pilot or model-weight download has run,
no scientific result artifact is registered, and registry-driven figure output has no inputs. The
repository now has committed browser E2E coverage for the no-fabrication workbench journeys. No model
download, training, HPO, fine-tuning, locked-test evaluation, or clinical classification has been
started.

Last passing source baseline: `14d9593` (registry-driven Phase 17 export bundle and enforced coverage floor).
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
Browser workbench E2E commit: `7f6c1b1`.
Browser gate clone-safety fix: `bd7647c`.
Phase-status blocker reconciliation commit: `4817ef2`.
Verified result-registry metadata and UI surface commit: `800e016`.
Current README/status reconciliation commit: `0db7e8b`.
Registry-driven Phase 17 export-bundle commit: `14d9593`.
The final documentation-only follow-ups record the clean-room at `a0ea1ca`; verify the current
checkout HEAD with Git because documentation commits may advance it without changing source code.

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
- A final clean clone at `/private/tmp/EvoVariant_TR_browser_final.bIkxop` from commit `bd7647c`
  passed `make bootstrap`, `make frontend-install`, `make validate`, the full `make web-check`
  (ESLint, TypeScript, and Next production build), `make web-e2e` (three Playwright tests),
  `make test-scientific`, `make test-e2e`, protocol/control-plane/schema/model-registry checks,
  and registry verification. Its final Git status was clean. `npm ci` reproduced the known
  13-vulnerability report; no automatic audit fix was applied.
- The research workbench at `apps/web/src/app/analysis/page.tsx` exposes all 14 required
  top-level areas. A local production-server browser smoke verified navigation, fail-closed
  single-variant rendering, blocked temporal empty state, and protocol metadata loading. The
  full frontend source tree now passes ESLint with zero errors/warnings, and the canonical
  `make web-check` target runs that lint gate plus TypeScript and the Next production build. The
  committed Playwright workbench suite passes through `make web-e2e` with four local browser
  tests covering navigation, blocked empty state, protocol metadata, registry empty state, and
  client validation.
- The result registry now carries the Section 21 metadata surface (`experiment_family`, lifecycle
  timestamps, dataset/split hashes, model/checkpoint/source/license identity, preprocessing and
  feature versions, config, hardware/GPU, runtime/cost, metrics, artifact paths, failure reason,
  and notes). Non-completed records cannot carry scientific metrics, completed artifacts are
  revalidated before persistence, and `scripts/verify_registry.py` checks completed output hashes
  against the explicit repository root. No current registry record was created by this change.
- The `/api/registry` endpoint and Experiment Registry tab expose only safe run metadata and
  artifact counts. The route returns `BLOCKED` for the current empty registry and fails closed on
  malformed metadata; it does not expose raw metrics, source paths, or clinical labels. The
  overview derives its registry status from the endpoint rather than hard-coding a scientific
  result state.

## Experiments and artifacts

Completed experiments: none in the ML extension. Phase 0 ran only free local deterministic,
scientific, and API validation tiers; Phase 3 ran only public-data parsing, cohort auditing,
and split construction; later phases ran only CPU contract tests and status surfaces, not model
inference or outcome optimization.

Pending experiments: all `ZS-*`, `REP-*`, `CLF-*`, `HPO-*`, `FT-*`, `ENS-*`, `CAL-*`, `ABS-*`,
`ABL-*`, `ROB-*`, and `STAT-*` work. Phase 3 data/split artifacts are complete; zero-shot
scoring is held behind the QA discrepancy review, model-inclusion evidence, and real Modal gate.
The status artifacts for Phases 6–15, 17, and 19 are explicit `BLOCKED` records; Phase 16 is
blocked on registered outputs even though its local browser E2E and build gates pass; Phase 18
is blocked on gated Modal smoke and figure evidence, although the clean-room CPU/frontend/browser
rerun at the current committed HEAD now passes.

Last experiment run: none.

Last generated artifacts: ignored record-level Phase 3 outputs under
`data/derived/ml_extension/phase3/`, with the reviewable summary and hashes at
`research/ml_extension/splits/phase3_manifest_summary.json`; schema-validated candidate model
manifests under `research/ml_extension/models/`; and ignored no-result status artifacts under
`research/runs/`. The current ignored Phase 17 bundle manifest is
`research/figures/bundle_manifest.json` with `status: BLOCKED`, 19 required figure families,
12 required tables, and zero outputs. No model result artifact or scientific figure was generated.

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
inclusion gate. Independent local gates, committed browser E2E, and a fresh clean-room
CPU/frontend rerun now pass. The registry-driven figure manifest and bundle now run with hash and
field verification, but report `BLOCKED` because no eligible completed scientific result artifacts
exist; no result artifacts are registered. A fresh `npm ci` also reports 13 dependency vulnerabilities (2 low,
2 moderate, 8 high, 1 critical); no automatic audit fix was applied.

Exact next action: preserve this state, then obtain explicit authorization and verified model/
compute evidence before running a tiny Modal pilot. Resolve or formally approve the Phase 3 QA
deviation before scoring; add registered result artifacts and complete registry-driven figure
rendering before releasing. Do not run model scoring, read locked labels for selection, or start
paid Modal work without the corresponding gate.

## Figure-input integrity follow-up — 2026-09-21

- Implementation commit: `cb304c9` (`fix: fail closed for registry-driven figures`).
- `src/evovariant_tr/figure_artifacts.py` now builds a deterministic Phase 17 manifest from
  hash-verified `COMPLETED` PRELIMINARY/FINAL registry runs only. The manifest contains source
  paths, run identities, hashes, required figure specifications, and blockers, but no metrics.
- `evovariant-tr generate-figure-manifest` and `make figures` write the manifest under the
  ignored `research/runs/` surface and return successfully while exposing `status: BLOCKED` when
  inputs are absent. This preserves an auditable gate artifact without treating a blocked gate as
  a scientific pass.
- The historical `research/scripts/generate_figures.py` compatibility entry point now delegates
  to the current registry manifest. Its prior synthetic 100-record demo curves and reads from
  ignored historical `research/results/` snapshots were removed; those snapshots remain
  historical and unpromoted.
- Tests cover empty-registry determinism, deletion/regeneration hash stability, eligible output
  hash verification, tamper blocking, CLI output, and the legacy entry-point guard. Targeted
  Ruff, strict mypy, unit/integration tests, and `make figures` passed; the Phase 17 scientific
  gate remains BLOCKED because there are no real registered outputs.

## Phase 17 export-bundle follow-up — 2026-09-21

- Implementation commit: `14d9593` (`feat: render registry-driven phase17 bundle`).
- `src/evovariant_tr/figure_artifacts.py` now declares all 19 master-prompt figure families and
  12 required tables. The input manifest validates relative repository paths, recorded SHA-256
  hashes, JSON/JSONL row shape, required fields, finite numeric values, and eligible evidence
  stages before an entry is available to a renderer. The manifest carries provenance and cost
  metadata but never copies scientific row values or metrics into a blocked status artifact.
- `evovariant-tr render-figure-bundle` and `make figures` now provide the Phase 17 export surface.
  A `READY` manifest produces deterministic standard-library SVG figures, source-derived JSON
  tables, `methods.md`, `limitations.md`, `compute_cost.json`, and `model_provenance.json` under
  the ignored bundle directory. A blocked or tampered manifest produces only
  `bundle_manifest.json`; narrow cleanup removes only outputs recorded by the prior bundle
  manifest, so stale generated figures cannot survive a blocked rerun.
- Current repository evidence is intentionally blocked: manifest SHA-256
  `b1a69cc4674b279967984e9e2d5b77addcc9015da8f1bf396d69d3305fb554a8`, bundle manifest SHA-256
  `a780d87816fa75ed0fe1f4a69d597e5310d5f70eae1946d49e2bd036e8e0c006`, zero registered runs,
  zero available figures/tables, and zero bundle outputs. No synthetic fixture is in the project
  registry.
- Validation at this checkpoint: `make validate` passed 625 tests, 33 deselected, one existing
  Starlette deprecation warning, and 95.34% coverage; the coverage floor is now enforced with
  `--cov-fail-under=95`. `make test-scientific` passed 7 with 1 explicit skip; `make test-e2e`
  passed 14 with 1 explicit skip; `make data-qc`, `make web-check`, `make web-e2e` (4 tests),
  protocol, ML-control-plane, schema, model-registry, registry, all Phase 6–19 status surfaces,
  and `make figures` passed. The data-QC split SHA-256 remains
  `96d3e20e3cd97cb583b6b3d156ecd473c88ab66670704b1facb457351626ef72`, with the existing Phase 3
  QA discrepancy preserved.
- Gate decision: the Phase 17 engineering/export control surface passes, but the scientific Phase
  17 gate and dependent release gate remain `BLOCKED` until an authorized model run creates
  complete registered result artifacts. Spend remains `$0`.

## Current clean-room follow-up — 2026-09-21

- Fresh clone: `/private/tmp/EvoVariant_cleanroom_final.CQSZD3`, commit
  `613c7a63e9f7c2aaa5d55c63e2cec250d4007939` (`docs: record figure manifest gate`).
- From that clone, `make bootstrap`, `make frontend-install`, `make validate` (615 tests,
  95.35% coverage), `make web-check`, `make test-scientific` (7 passed, 1 skipped),
  `make test-e2e` (14 passed, 1 skipped), `make web-e2e` (3 passed), protocol/control-plane/
  schema/model-registry/registry checks, and `make figures` all completed successfully.
- The clean clone's tracked Git status remained clean after dependency installation and all
  commands. The deterministic blocked figure manifest hash was
  `c5169b2c052d129ef0bf9eaab67d13365a4237bcfd28686100f4a1ae970e1805`.
- `npm ci` reproduced the known 13-vulnerability report (2 low, 2 moderate, 8 high, 1 critical);
  no automatic audit fix was applied. This clean-room result is engineering evidence only and
  does not create model, benchmark, or paid-compute evidence.

## Current registry/workbench follow-up — 2026-09-21

- Verified implementation commit: `800e016` (`feat: expose verified registry metadata surface`).
- The Section 21 result-registry metadata contract is now represented in the Pydantic model and
  JSON Schema. Completed records are hash-checked by `scripts/verify_registry.py` using an
  explicit repository root, and status transitions revalidate the record before persistence.
- The current checked-in registry has no run records. The new `/api/registry` route therefore
  returns a safe `BLOCKED` summary with zero registered runs, and the Experiment Registry tab
  shows a truthful empty state. No metrics, output paths, or clinical labels are exposed by this
  surface.
- Local validation after the implementation commit: `make validate` passed with 619 tests, 33
  deselected, one existing Starlette deprecation warning, and 95.31% coverage; `make web-check`,
  `make web-e2e` (4 tests), `make schema-verify`, and `make registry-verify` passed. The scoped
  impeccable UI detector returned no findings. These are engineering/control-plane gates only.
- No new model, checkpoint, scientific result, figure, Modal invocation, deployment, release, or
  spend was created. The next authorized scientific action remains explicit compute/model access
  plus resolution or approval of the Phase 3 QA discrepancy; until then Phases 6–19 remain
  blocked.

## Final clean-room follow-up — 2026-09-21

- Fresh clone: `/private/tmp/EvoVariant_cleanroom_800e016.CxTXjC`, commit `e798c20`
  (`docs: record registry control-plane follow-up`). The clone's final tracked Git status was
  clean after `make bootstrap`, `make frontend-install`, all validation commands, figure-manifest
  generation, and browser tests.
- Clean-room evidence: `make validate` passed with 619 tests, 33 deselected, one dependency
  warning, and 95.31% coverage; `make test-scientific` passed 7 with 1 explicit skip; `make
  test-e2e` passed 14 with 1 explicit skip; ML protocol, frozen protocol, schema, model-registry,
  and registry verification passed; `make web-check` passed; and `make web-e2e` passed all 4
  Playwright tests. `npm ci` reproduced 13 vulnerabilities (2 low, 2 moderate, 8 high, 1
  critical); no audit fix was applied.
- Clean-room `make figures` produced the same blocked registry manifest hash
  `c5169b2c052d129ef0bf9eaab67d13365a4237bcfd28686100f4a1ae970e1805`. The clone has no raw
  ClinVar archives, so data-QC remains a local archive-backed check rather than a clean-room
  scientific result.
- A direct streaming audit of the checked-in t0 archive found 1,402,906 exact VUS rows and
  1,402,895 unique valid normalized IDs; 11 rows fail the frozen ACGT/SNV coordinate rules.
  The handoff target is 1,403,225, a 330-ID difference. The archived file hash matches its
  manifest, so no filter was altered to force the target and downstream scoring remains blocked.
- `README.md` was reconciled with the current control plane in `0db7e8b`: it no longer presents
  the retired BRCA1 threshold/confidence classifier, historical legacy milestones, or an old Modal
  endpoint as current scientific evidence. It now directs reviewers to the persistent phase state,
  documents the frozen estimand and current counts, and distinguishes free local validation from
  paid/remote gates.

## Final Phase 18 clean-room follow-up — 2026-09-21

- Fresh clone: `/private/tmp/EvoVariant_cleanroom_phase17.2YeY5c`, final documented commit
  `a0ea1caf989c928f10e65d5312fa17fde7c7aed8` (`docs: record phase17 export gate`). The clone's
  tracked Git status remained clean after all commands and dependency installation.
- Clean-room commands passed: `make bootstrap`, `make frontend-install`, `make validate` (625
  passed, 33 deselected, 1 existing Starlette deprecation warning, 95.34% coverage),
  `make test-scientific` (7 passed, 1 skipped), `make test-e2e` (14 passed, 1 skipped), frozen
  protocol/ML-control-plane/schema/model-registry/registry verification, `make figures`,
  `make web-check`, and `make web-e2e` (4 passed). The regenerated figure manifest and bundle
  remained explicitly `BLOCKED` with zero scientific outputs.
- `npm ci` reproduced 13 dependency vulnerabilities (2 low, 2 moderate, 8 high, 1 critical);
  no automatic audit fix was applied. The clone has no ignored raw ClinVar archives, so `make
  data-qc` was not run there; archive-backed data-QC evidence remains local to the main checkout.
- This clean-room run proves the free/control-plane reproducibility surface only. It does not
  create model weights, scientific results, a registry run, paid Modal inference, or release
  evidence. Phase 18 remains `BLOCKED / PARTIAL` until the gated compute and scientific-result
  inputs exist; spend remains `$0`.
