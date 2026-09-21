# Phase Ledger — EvoVariant-TR ML Extension

Status: PENDING | IN_PROGRESS | PASS | BLOCKED | FAILED | DEFERRED

| Phase | Title | Status | Evidence |
|---:|---|---|---|
| 0 | Diagnostic snapshot | PASS | `docs/agent/BASELINE_AUDIT.md` (2026-09-21; no scientific/code repair) |
| 1 | Control plane + ML protocol | PASS | `research/ml_extension/`, control-plane CLI, and contract tests |
| 2 | Canonical scoring repair | PASS | Local repair plus real Evo2 7B H100 raw-SNV pilot; corrected `10` to `chr10`, exact 8192-bp context, forward/reverse raw scores, provenance, and HTTP 200 evidence in `artifacts/modal/phase2_phase4_pilot_20260921_success.json`. |
| 3 | ML dataset + locked splits | BLOCKED | Structural current-cohort invariants pass, but the 330-ID / 78-final-record discrepancy is material to denominators and class counts; impact review is reopened in `artifacts/phase3_discrepancy_impact_20260921.json`. |
| 4 | Modal compute foundation | PASS | Real persistent prediction-cache miss/hit, exact numeric equality, 36.2727s versus 0.956s wall time, H100 telemetry, and workspace billing evidence are recorded in the Phase 2/4 pilot artifact and cost ledger. |
| 5 | Model registry + adapters | DEFERRED | `artifacts/model_audit/phase5_multi_model_deferral_20260921.json`; Evo2 passed the real smoke, while six candidates are rigorously deferred/infeasible for contract, asset, license, applicability, or bounded-compute reasons. |
| 6 | Zero-shot multi-model benchmark | BLOCKED | `research/runs/phase6_zs_status.json`; Phase 3 QA discrepancy remains material, the Phase 5 multi-model track is deferred with only Evo2 verified, full-cohort authorization/batch-parity evidence is absent, and prelaunch cost scenarios are recorded in `artifacts/modal/phase6_preflight_cost_estimate_20260921.json`. |
| 7 | Embedding/representation extraction | BLOCKED | `df7a340`, `2c9b3ca`; `research/runs/phase7_rep_status.json`; fixed Evo2 embedding contract and hash-verified feature-store adapter are source-level only, with no remote feature smoke/cache and no Phase 6 benchmark artifact. |
| 8 | Downstream supervised models | BLOCKED | `research/runs/phase8_clf_status.json`; no frozen feature cache or Phase 7 artifact. |
| 9 | Hyperparameter optimization | BLOCKED | `research/runs/phase9_hpo_status.json`; no development feature artifact or Phase 8 model. |
| 10 | Fine-tuning / PEFT | DEFERRED | `artifacts/modal/phase10_adaptation_deferral_20260921.json`; adaptation is formally `DEFERRED_BY_COMPUTE` with no training run or scientific metrics. |
| 11 | Ensemble/meta-classifier | BLOCKED | `research/runs/phase11_ens_status.json`; no registered base predictions or OOF inputs. |
| 12 | Calibration + abstention | BLOCKED | `research/runs/phase12_cal_abs_status.json`; no development predictions and no authorized locked-label selection. |
| 13 | Ablation + robustness | BLOCKED | `research/runs/phase13_abl_rob_status.json`; no frozen base outputs for the predeclared matrix. |
| 14 | Locked statistical evaluation | BLOCKED | `research/runs/phase14_stat_status.json`; no frozen model/config and locked evaluation is not authorized. |
| 15 | Batch research pipeline | BLOCKED | `research/runs/phase15_batch_status.json`; local Evo2 adapter, bounded Modal source endpoint, resumable `total_shards` manifest accounting, and the no-GPU recovery simulation (`9 passed, 1 documented skip`) are regression-checked, but deployment/parity, full-cohort authorization, and remote recovery smoke are absent. |
| 16 | Research workbench UI | BLOCKED | `459ad11`, `1d9cf43`, `7f6c1b1`, `739310d`; Next 16.3.5 dependency/lint migration, `make web-check`, and four-test `make web-e2e` PASS; registered scientific outputs are absent. |
| 17 | Figures/tables/report artifacts | BLOCKED | `14d9593`; all 19 figure families and 12 tables have registry contracts plus deterministic bundle rendering, but `research/runs/phase17_fig_status.json` is `BLOCKED` with zero eligible completed result artifacts and `research/figures/bundle_manifest.json` has zero outputs. |
| 18 | Security + clean-room reproducibility | BLOCKED | Fresh clone of `739310d` + `make bootstrap`, `npm ci` (zero vulnerabilities), `make validate`, `make web-check`, protocol/schema/registry checks, explicit tiers, and four-test `make web-e2e` PASS; gated Modal evidence is absent and the registry figure manifest is blocked on missing scientific outputs. |
| 19 | Final release gate | BLOCKED | `research/runs/phase19_release_status.json`; dependent scientific phases, paid compute, figures, and registered result artifacts remain unresolved. |

For each PASS append:
- commit,
- commands,
- tests,
- artifact hashes,
- spend,
- remaining risks.

The dated records below are historical evidence. The top status table and the newest dated
follow-up sections are authoritative when older entries describe an earlier implementation or
gate state.

## Current validation follow-up — 2026-09-21

- Frontend security/build/browser subgates: PASS in `739310d`. Next.js `16.3.5`, native flat
  ESLint configuration, direct ESLint package scripts, and PostCSS `8.5.28` are installed from
  the checked-in lockfile. Both full and production-only `npm audit` report zero vulnerabilities.
- Paid-execution safety subgate: PASS for stale-approval rejection. `require_full_run_approval()`
  now compares the approval artifact with the frozen hash in
  `research/ml_extension/protocol_hashes.json`; the current stale August artifact is refused,
  and the targeted cost-policy suite passes 26 tests. No paid command was launched.
- Clean-room subgate: PASS from a fresh clone of `739310d`. `make bootstrap`, `make
  frontend-install`, `make validate`, `make test-scientific`, `make test-e2e`, protocol,
  ML-control-plane, schema, model-registry, and registry checks, `make web-check`, and the
  four-test `make web-e2e` run completed successfully. `make figures` and `make release-check`
  remained explicitly `BLOCKED` with zero scientific outputs, as required.
- Overall Phase 18 remains `BLOCKED`, because a clean CPU/frontend reproduction cannot substitute
  for the gated Modal/scientific result reproduction. Phase 19 remains `BLOCKED` for the same
  unresolved scientific, registry, figure, and release dependencies.
- Phase 15's local recovery subgate is also recorded as PASS for the no-GPU simulation:
  `EVOVARIANT_TR_PAID_COMPUTE_ACK=I_ACCEPT_COSTS ./.venv/bin/pytest --run-modal -m modal
  tests/modal -rs` produced 9 passed and one documented placeholder skip. It is not remote
  batch-parity or remote kill/restart evidence, so the overall Phase 15 status remains `BLOCKED`.
- Phase 7 now has a source-level Evo2 feature contract: the fixed
  `blocks.28.mlp.l3` layer is mean-pooled across tokens for forward and reverse-complement
  reference/alternate sequences, with content-addressed feature-cache identity and
  provenance. Commit `2c9b3ca` adds a storage-only adapter that verifies the payload's
  completed status, vector hashes, shapes, finite values, and alternate-minus-reference
  arithmetic before emitting a compact feature record. No remote embedding smoke or
  completed feature cache has been approved or run, so the Phase 7 gate remains `BLOCKED`.
- The current free control-surface rerun passed the scientific/API E2E, ML protocol, schema,
  model-registry, and result-registry checks. The Modal preflight recorded authenticated
  `evovariant-tr` access as `PLANNED` with zero GPU count and no remote invocation. Regenerated
  Phase 6 and 8–9, 11–19 statuses, the Phase 17 figure bundle, and Phase 19 release check remain
  `BLOCKED` with empty metrics/output surfaces; Phase 10 is separately `DEFERRED` with empty
  metrics.
- A fresh read-only Modal billing summary reports workspace metered cost `$11.99` and billed cost
  `$0.00` (`$8.78` deployed apps, `$3.21` volumes). This is workspace-level evidence only; no
  per-request invoice amount or additional GPU invocation is claimed.
- The same current-checkout rerun passed `make web-check` and all 4 `make web-e2e` journeys;
  only the documented non-failing Next tracing warnings were emitted.
- Phase 10's optional adaptation requirement is now formally `DEFERRED` rather than represented
  as an unqualified block: the decision record cites measured H100 inference memory/runtime,
  the low-confidence cohort cost preflight, the absent local/checked-in training path, and the
  current approval's training exclusion. This is not a training or PEFT result.
- The latest post-adapter validation passed `make validate` with 642 tests, 33 deselected, strict
  mypy over 51 source files, Ruff, secret scan, and 95.01% coverage.
- Phase 5's multi-model inclusion requirement is formally `DEFERRED` after the source-backed
  seven-candidate audit. The deferral preserves the exact exclusion reasons and requires a new
  candidate-specific approval and parity smoke before Phase 6 can be reopened; it does not count
  synthetic comparators as scientific models.
- The Phase 3 source-provenance follow-up found no alternate official archive path: both archived
  NCBI URLs return the manifest-matching release sizes, while the corresponding non-archive URLs
  return HTTP 404. This strengthens the unresolved target-ID/source-provenance blocker; it does
  not justify replacing the frozen archives or changing filters.

## Phase 0 completion record — 2026-09-21

- Commit baseline: `a5604eebec449dc95983f7570c483c443aa15bd8`
- Active branch/worktree: `research/evovariant-tr` / `/Users/utkarshkhajuria/Desktop/EvoVariant`
- Commands and results: recorded in `docs/agent/BASELINE_AUDIT.md`; protocol CLI,
  protocol contract, Ruff, mypy, synthetic scientific tests, synthetic API E2E tests, and
  empty-registry verification passed; the repository `make validate` gate and frontend lint/
  build gates remain failed for documented permission/code reasons.
- Frozen protocol SHA-256: `78799000023ca157b72836a0ec603abb20c93960b15fba09485bd0dffbbb1525`
- Handoff manifest: all 18 entries verified by exact path, byte count, and SHA-256 before the
  ZIP was moved to `/private/tmp/EvoVariant_TR_Codex_Handoff.verified.zip`.
- Baseline audit SHA-256: `b5ff51af3eaa840408baf6513715d2cc5abed1bb8587e91d34fe138dfa9634a7`.
- Paid Modal work: not run; estimated and measured Phase 0 spend: `$0`.
- Completed experiments: none; only local deterministic/scientific/API validation tiers ran.
- Remaining risks: active legacy threshold/confidence behavior; fake API scorer; unimplemented
  Evo2 adapter; 8,193-base Modal formula; schema/identity drift; absent raw archives; empty
  registry; and local validation/frontend gate failures. See the audit for exact evidence.
- Gate decision: PASS for diagnostic documentation only. Do not begin model download, training,
  HPO, fine-tuning, locked evaluation, or paid Modal work. Phase 1 remains pending and is not
  started in this turn.

## Phase 1 completion record — 2026-09-21

- Implementation commit: `1f777b5`; no source model or paid compute work was run.
- Control-plane files: `research/ml_extension/protocol.yaml`, `split_policy.yaml`, and
  `protocol_hashes.json`.
- Schemas: `model_manifest.schema.json`, `split_manifest.schema.json`,
  `experiment_config.schema.json`, and `cost_ledger.schema.json`.
- Commands: `python3.12 -m evovariant_tr.cli validate-ml-control-plane --repo-root .` passed;
  targeted contract tests passed (`8 passed` including the frozen protocol contract), Ruff and
  strict mypy passed (`35 source files`).
- Original protocol SHA-256 remained
  `78799000023ca157b72836a0ec603abb20c93960b15fba09485bd0dffbbb1525`.
- Extension protocol SHA-256:
  `374bc2c59941d6001e41c478658ad65fa4e2ae0789829d2625e8801b00ad7c5c`.
- Decisions added: D-012 through D-017 covering separation, schemas, model feasibility,
  cache identity, validation-only selection, adaptation gating, and out-of-fold stacking.
- Spend: `$0`; no model weights, locked labels, or Modal resources used.
- Gate decision: PASS for the control-plane phase. Phase 2 may begin; Phase 3 and later remain
  dependent on repaired scoring and verified data/control artifacts.

## Phase 2 completion record — 2026-09-21

- Implementation commit: `45c2a47` (`feat: repair canonical research scoring contract`).
  Canonical scoring, API/proxy, Modal adapter, and research-workbench UI repairs are included.
- Contract changes: exact 8,192-base windows; coordinate/allele/SNV/orientation invariants;
  forward and reverse-complement raw components; explicit primary-delta and disagreement
  fields; canonical GRCh38 payload aliases; fail-closed unconfigured services; no fake
  production scorer; and no threshold/confidence/clinical classification in the research UI.
- Validation commands and results:
  - `make validate` — PASS: secret scan, Ruff, strict mypy (36 source files), `567 passed,
    33 deselected, 1 warning`, and `95.17%` coverage.
  - `make protocol-verify` — PASS.
  - `make registry-verify` — PASS.
  - `make ml-protocol-verify` — PASS.
  - Scientific tests — `7 passed, 1 skipped`.
  - E2E tests — `14 passed, 1 skipped, 1 warning`.
  - Frontend legacy-classification scan — PASS; no `prediction`, threshold, confidence, or
    pathogenic/benign classification logic remains in `apps/web/src`.
  - `git diff --check` — PASS.
- Frozen original protocol SHA-256 remains
  `78799000023ca157b72836a0ec603abb20c93960b15fba09485bd0dffbbb1525`.
- Spend: `$0`; no model weights, locked labels, Modal deployment, or GPU call was run.
- Blocking evidence: a real Modal pilot is an explicit Phase 2 gate. The no-spend preflight now
  reports authenticated CLI access, but there is no user-provided paid-compute acknowledgement
  and no remote function, image build, model load, or inference evidence. Local/fake tests cannot
  substitute for that gate.
- Gate decision: `BLOCKED` for the complete Phase 2 gate. Phase 3 data/split work may proceed
  independently because it is controlled by the frozen protocol and does not require a paid
  Modal run. Phase 4 compute work remains gated.

## Phase 3 completion record — 2026-09-21

- Implementation commit: `f2dcc1f` (`feat: build reproducible ML extension splits`).
- Source archives were downloaded from official NCBI ClinVar archive URLs and verified against
  the checked-in manifests:
  - t0 `288267418` bytes,
    `931322c5b576e4d46c82b2e275ef0920661ef9c39c1acf62ed48e6756f24d7aa`.
  - t1 `441792560` bytes,
    `230ba6d5ac0869bfb46fecb8d19bd8dbfa9a133bfda2e3f8f5b5b662ae7bf500`.
- The downloader now handles the official 2025+ archive-root layout and accepts exact
  protocol release dates. The parser and fast cohort paths use ClinVar VCF-normalized
  position/reference/alternate fields when present; the archive's legacy allele fields are
  `na` for these SNVs.
- Commands and results:
  - `make data-qc` — PASS; generated the ignored record-level temporal audit, locked-ID file,
    and full split manifest under `data/derived/ml_extension/phase3/`.
  - Generated split manifest validates against `research/schemas/split_manifest.schema.json`.
  - `make ml-protocol-verify` — PASS.
  - `make schema-verify` — PASS.
  - Targeted Phase 3 tests — `66 passed` across parser, cohort, calibration, and split tests.
  - Ruff and strict mypy — PASS (`37 source files`).
- Recomputed cohort: 1,402,895 t0 unique VUS; 3,459 absent at t1; 1,098,941 below the
  two-star outcome gate; 299,549 not definitive; 946 final temporal records (536 B/LB,
  410 P/LP); two gene annotation changes; zero structural reference mismatches.
- Development split: 239,992 records with 191,957 TRAIN and 48,035 VALIDATION; 9,682 and 57
  whole-gene groups respectively; normalized-ID overlap, gene overlap, duplicate IDs, and
  locked-test overlap are all zero.
- Split hash: `bac30ed0a818258445a7340b1e96fe592902af5d4d7e899fbe227d24af955722`.
- QA discrepancy: the validation-only handoff target expected 1,403,225 t0 VUS and 1,024
  final records (614 B/LB, 410 P/LP). The archive hashes match, VCF fields are used, and the
  t0 star-gate interpretation is corrected; the remaining difference is preserved rather than
  tuned away. See the tracked Phase 3 summary for the investigation and limitation.
- Spend: `$0`; local CPU only; no model weights, locked-test tuning, Modal deployment, or GPU
  call was run.
- Gate decision: `PASS` for zero overlap, deterministic rebuild, schema validity, and QC
  invariants. Downstream zero-shot scoring is not authorized by this record until the QA
  discrepancy is resolved or a dated protocol deviation is approved.

## Phase 4 completion record — 2026-09-21

- Implementation commit: `cc7de42` (`feat: add cost-aware Modal execution foundation`).
- Local foundation: canonical Modal app/image/GPU/volume identity, pinned Evo2 repository
  revision, fail-closed named-volume behavior, persistent content-addressed prediction cache,
  atomic cache writes, full cache identity dimensions, shard persistence, bounded retry policy,
  CPU-safe GPU telemetry, and append-only cost ledger.
- Commands and results:
  - `make validate` — PASS: secret scan, Ruff, strict mypy over 40 source files, `591 passed,
    33 deselected, 1 warning`, and `95.21%` coverage.
  - `make ml-protocol-verify` — PASS.
  - `make schema-verify` — PASS.
  - `make protocol-verify` — PASS; frozen original protocol hash remains
    `78799000023ca157b72836a0ec603abb20c93960b15fba09485bd0dffbbb1525`.
  - `make modal-smoke` — PASS as a no-spend preflight only: `modal_installed: true`,
    `modal_authenticated: true`; no remote invocation requested. The generated ledger record
    is `PLANNED` with null estimated/measured USD and no approval artifact.
  - `git diff --check` — PASS before the implementation commit.
- Paid compute and scientific execution: no Modal function, image build, model-weight download,
  model load, GPU inference, or deployment was run. Estimated and measured spend remain `$0`.
- Gate decision: `BLOCKED` for the complete Phase 4 gate. The master prompt requires a tiny
  reproducible remote inference, a verified cache hit, and a cost record. Only the local cache
  contract and no-spend preflight are evidenced here; the remote pilot requires an explicit
  paid-compute acknowledgement and remains deferred.
- Independent work allowed next: Phase 5 registry/adapters and all non-executing provenance,
  feasibility, and contract infrastructure. Scientific scoring remains blocked by both this
  gate and the unresolved Phase 3 QA discrepancy.

## Phase 5 completion record — 2026-09-21

- Implementation commit: `473d314` (`feat: add evidence-gated model registry and adapters`).
- Registry artifacts: seven strict JSON manifests under `research/ml_extension/models/` for
  Evo2, Nucleotide Transformer, Caduceus, GPN, CADD, PhyloP, and the applicable AlphaMissense
  subset. Each manifest records status, source, license state, checkpoint/revision state, input
  and score contract, capabilities, hardware, and provenance verification state.
- Adapter framework: `ModelAdapter`, structured readiness evidence, fail-closed deferred
  adapters, and an Evo2 adapter that can only execute with explicit parity evidence and an
  injected/verified scorer. Importing or building the default adapter map does not download
  packages or checkpoints.
- Commands and results:
  - `make model-registry-verify` — PASS: seven manifests schema-valid; included count `0`.
  - `make schema-verify` — PASS.
  - Targeted registry/adapter/CLI tests — PASS (`14 passed`).
  - Full coverage run — PASS (`601 passed, 33 deselected, 1 warning`, `95.28%` coverage).
  - `git diff --check` — PASS before the implementation commit.
- Gate decision: `BLOCKED`. The phase requires each included model to pass official source,
  license, checkpoint/revision, input/score contract, hardware, and tiny parity/smoke evidence.
  The current local environment has no verified model package/checkpoint path and the project
  has no paid-compute acknowledgement. Planned manifests and deterministic comparator fixtures
  are not benchmark evidence.
- Spend: `$0`; no model weights, remote model execution, or GPU work was run.
- Independent work allowed next: CPU-only contract/framework work for later experiment families;
  no zero-shot benchmark or representation artifact may be promoted until at least the required
  model candidate and the Phase 3/4 gates are resolved.

## Later-phase CPU framework completion record — 2026-09-21

- Implementation commit: `7127fc7` (`feat: add gated ML experiment control surface`).
- Added deterministic, CPU-only contracts for benchmark planning, feature hashing and split
  disjointness, supervised classifiers, validation-only HPO, OOF ensemble stacking, predeclared
  ablation/robustness plans, registry-driven figure manifests, batch CSV validation/progress,
  and immutable experiment status artifacts.
- Every later-phase Make target now has one documented control-surface command. When its
  dependency is not evidenced, the target writes an explicit `BLOCKED` artifact under ignored
  `research/runs/phase*_status.json` with blockers and an empty metrics object. No synthetic
  fixture is promoted as a scientific result.
- `make validate` — PASS: secret scan, Ruff, strict mypy over 51 source files, `610 passed,
  33 deselected, 1 warning`, and `95.34%` coverage.
- `make ml-protocol-verify`, `make schema-verify`, `make protocol-verify`, `make
  model-registry-verify`, and `git diff --check` — PASS at the implementation checkpoint.
- Status surfaces for Phases 6–15, 17, and 19 are `BLOCKED`; Phase 10 is not represented as a
  successful adaptation or as a paid-compute result. Spend remains `$0`.
- Gate decision: independent framework work PASS; scientific execution phases remain BLOCKED by
  model/compute/data evidence and must not be promoted from the status artifacts.

## Phase 16 completion record — 2026-09-21

- Implementation commit: `459ad11` (`feat: expose evidence-gated research workbench`).
- The UI exposes all required areas: Overview; Single Variant Research Analysis; Temporal VUS
  Explorer; Model Benchmark; Representation / Layer Analysis; Training & Hyperparameter
  Experiments; Fine-Tuning Experiments; Ensemble Analysis; Calibration & Abstention; Robustness
  & Ablation; Error Analysis; Batch VCF/CSV; Methods & Provenance; and Experiment Registry.
- Single-variant output renders normalized variant, assembly, context length, raw scorer fields,
  forward/RC details, provenance, and explicit unavailable states for calibration, uncertainty,
  abstention, and comparator evidence. It contains no clinical classification logic or invented
  experiment metrics.
- `make web-check` — PASS: full frontend ESLint (zero errors/warnings), `npx tsc --noEmit`, and
  Next.js 15.3.1 production build. The Next 15 dynamic-route `params` contract was repaired
  for batch and results routes.
- Local production-server browser smoke — PASS: all 14 tabs discoverable; single-variant
  form renders; temporal area shows an intentional blocked state; Methods & Provenance loads
  `/api/protocol`; no hidden manual edits were used. The snapshot is temporary evidence outside
  the repository.
- Committed browser E2E — PASS: `make web-e2e` runs three Playwright tests against a production
  Next server, covering 14-area navigation/blocked state, protocol metadata loading, and
  client-side allele validation without a scorer call.
- `4817ef2` reconciles the generated Phase 16/18/19 status blockers so they no longer report the
  resolved browser gate as missing.
- Gate decision: BLOCKED. The frontend lint/build/browser gates pass, but no registered
  scientific outputs exist to populate result panels; browser coverage does not substitute for
  scientific result evidence.

## Phase 17–19 completion record — 2026-09-21

- Phase 17 figure/table generation has a registry-driven artifact contract and an explicit
  `make figures` status surface. The follow-up manifest is deterministic, checks recorded
  output hashes, excludes non-scientific evidence stages, and correctly records `BLOCKED`
  because no eligible completed result artifact exists to render. The former legacy generator's
  synthetic demo curves were removed; no historical ignored snapshot was promoted. Implementation
  commit: `cb304c9` (`fix: fail closed for registry-driven figures`).
- Phase 18 security/default validation is locally green (`make validate`); the frontend lint,
  typecheck, and build gate is green (`make web-check`). A fresh clone at
  `/private/tmp/EvoVariant_cleanroom_final.CQSZD3` from `613c7a6` ran `make bootstrap`,
  `make frontend-install`, the default suite, scientific tier, E2E/API tier,
  protocol/control-plane/schema/model-registry checks, registry verification, the full frontend
  gate, `make figures`, and `make web-e2e` with three passing browser tests; it remained clean
  after installation. The figure manifest hash was
  `c5169b2c052d129ef0bf9eaab67d13365a4237bcfd28686100f4a1ae970e1805` and its status was
  explicitly `BLOCKED` because no scientific inputs exist; gated Modal smoke remains unrun.
  `npm ci` reports 13 dependency vulnerabilities (2 low, 2 moderate, 8 high, 1 critical), so
  the overall Phase 18 gate is `BLOCKED` despite the clean-room CPU/frontend/browser subgate
  passing.
- Phase 19 `make release-check` records `BLOCKED` because dependent scientific phases, paid
  compute, figure, and registered-result gates remain unresolved. No tag, release, deployment,
  or publication was created. Spend remains `$0`.

## Phase 17 export-bundle follow-up — 2026-09-21

- Implementation commit: `14d9593` (`feat: render registry-driven phase17 bundle`). The renderer
  declares the 19 figure families and 12 tables required by master-prompt Section 14 and Phase
  17, with explicit source artifact names and required fields.
- The figure manifest now checks relative paths, output hashes, JSON/JSONL row structure, required
  fields, finite numeric values, and PRELIMINARY/FINAL evidence eligibility. It records source
  metadata and field errors without copying scientific row values into the gate artifact.
- `make figures` runs manifest generation and `render-figure-bundle`. The current run is
  deterministically `BLOCKED`: manifest SHA-256 is
  `b1a69cc4674b279967984e9e2d5b77addcc9015da8f1bf396d69d3305fb554a8`, the bundle-manifest
  SHA-256 is `a780d87816fa75ed0fe1f4a69d597e5310d5f70eae1946d49e2bd036e8e0c006`, and the bundle
  contains zero outputs because the checked-in result registry is empty. A blocked rerun removes
  only files listed by the previous bundle manifest and does not leave stale scientific figures.
- A future `READY` manifest will produce only source-derived SVG/JSON/report outputs: methods,
  limitations, compute/cost, and model-provenance files are generated from registered metadata;
  no synthetic curve, typed metric, ignored historical snapshot, or unregistered fixture is
  promoted. The standard-library renderer does not add a plotting dependency or invoke paid
  compute.
- Validation: `make validate` passed 625 tests, 33 deselected, one existing warning, and 95.34%
  coverage; `make test-scientific` passed 7 with 1 skip; `make test-e2e` passed 14 with 1 skip;
  `make data-qc`, `make web-check`, `make web-e2e` (4), protocol/control-plane/schema/model-
  registry/registry checks, all Phase 6–19 status surfaces, and `make figures` passed. The
  Phase 3 split hash remains `bac30ed0a818258445a7340b1e96fe592902af5d4d7e899fbe227d24af955722`;
  the QA discrepancy remains documented and downstream scoring is still gated.
- Gate decision: Phase 17 export engineering `PASS`; Phase 17 scientific acceptance remains
  `BLOCKED`, as do Phases 6–16, 18, and 19. Spend remains `$0`.

## Registry and workbench control-plane follow-up — 2026-09-21

- Implementation commit: `800e016` (`feat: expose verified registry metadata surface`).
- The immutable `RunRecord` and `research/schemas/experiment_run.schema.json` now cover the
  master prompt's Section 21 metadata: experiment family, lifecycle timestamps, dataset/split
  hashes, model/checkpoint/source/license fields, preprocessing/feature versions, config,
  seed/hardware/GPU, runtime and cost, metrics, artifact paths, failure reason, and notes.
- Registry transitions revalidate metadata before writing. Non-completed records cannot carry
  scientific metrics; completed records require output paths and hashes; `scripts/verify_registry.py`
  now checks every completed record against an explicit repository root, including tamper
  detection. The checked-in registry remains empty, so this is control-plane evidence only.
- The Next.js `/api/registry` route and Experiment Registry workbench tab now read safe metadata
  from the real registry. With no run records, the route and overview remain `BLOCKED`; no raw
  metrics, file locations, or clinical labels are exposed. Four Playwright tests cover the local
  browser surface, including the empty-registry state.
- Validation: `make validate` — PASS (`619 passed, 33 deselected, 1 warning`, `95.31%`); `make
  web-check` — PASS; `make web-e2e` — PASS (4); `make schema-verify` — PASS; `make
  registry-verify` — PASS; `git diff --check` — PASS before commit.
- Gate decision: this follow-up passes its engineering/control-plane gate but does not change the
  scientific status. Phases 6–19 remain `BLOCKED` pending the Phase 3 QA decision, verified model
  and checkpoint evidence, authorized Modal pilot, registered scientific outputs, and
  registry-driven figure artifacts.

## Phase 3 discrepancy audit and final clean-room validation — 2026-09-21

- `make data-qc` was rerun against the manifest-verified local archives. The recomputed temporal
  audit remains 1,402,895 unique t0 VUS, 3,459 absent at t1, 1,098,941 below the t1 two-star
  gate, 299,549 not definitive, and 946 final records (536 B/LB, 410 P/LP). The generated split
  manifest SHA-256 remains `96d3e20e3cd97cb583b6b3d156ecd473c88ab66670704b1facb457351626ef72`
  and the split hash remains `bac30ed0a818258445a7340b1e96fe592902af5d4d7e899fbe227d24af955722`.
- Direct raw-row accounting finds 1,402,906 exact `Uncertain significance` rows in the filtered
  t0 GRCh38 germline-SNV stream, with 11 rows rejected by the frozen valid single-base rules;
  no duplicate normalized IDs were found. This confirms the current 1,402,895 count and leaves
  the 330-ID difference from the validation-only handoff target unresolved. No protocol field,
  filter, archive, or normalization rule was changed to force agreement.
- A fresh clone at `/private/tmp/EvoVariant_cleanroom_800e016.CxTXjC` from `e798c20` passed
  bootstrap, dependency installation, `make validate` (619 tests, 95.31% coverage), scientific
  and API/E2E tiers, protocol/control-plane/schema/model-registry/registry verification, the
  production frontend build, the four-test Playwright suite, and blocked figure-manifest
  generation. Its tracked status remained clean; `npm ci` reproduced the known 13-vulnerability
  report. The deterministic blocked figure manifest hash was
  `c5169b2c052d129ef0bf9eaab67d13365a4237bcfd28686100f4a1ae970e1805`.
- Gate decision: engineering reproducibility is `PASS`; Phase 3 scientific acceptance remains
  `PASS_WITH_QA_DISCREPANCY_DOCUMENTED`, and Phases 6–19 remain `BLOCKED`. The discrepancy must
  be resolved from source evidence or approved through the dated deviation process before any
  model output or locked-test claim is registered.

## Phase 19 README/status reconciliation — 2026-09-21

- Documentation commit: `0db7e8b` (`docs: align README with current research gates`).
- The repository README was rewritten to match the authoritative control plane. It now describes
  the frozen temporal estimand, the observed Phase 3 counts and unresolved QA discrepancy, the
  empty result registry, the blocked registry-driven figure surface, the no-spend Modal boundary,
  the four-test workbench browser gate, and the exact free/local validation commands.
- Retired BRCA1 threshold/confidence claims, unverified historical Modal endpoint claims, and
  historical milestone PASS statements were removed from the current README. Legacy reports stay
  available under `docs/project/` with an explicit historical boundary.
- Gate decision: documentation reconciliation `PASS`; no scientific status changed. The final
  release gate remains `BLOCKED / PARTIAL` because no verified model, paid/remote inference,
  registered scientific result, or eligible figure input exists.

## Frontend lint and local-gate follow-up — 2026-09-21

- Implementation commit: `1d9cf43` (`fix: clear frontend lint gate`).
- The legacy frontend source tree was audited and repaired without changing the research-only
  evidence boundary. Async event/effect calls now handle rejected promises explicitly, React
  hook dependencies are declared, the forward-ref component has a stable display name, and the
  UCSC/NCBI/ClinVar utility uses explicit response shapes instead of untyped JSON member access.
- Full source lint passes with zero errors and zero warnings. `make web-check` now invokes the
  repository-local ESLint Node entrypoint, TypeScript, and the production Next build; using the
  Node entrypoint avoids a host checkout executable-bit failure from `node_modules/.bin/eslint`.
- The follow-up is engineering-gate evidence only. It creates no model outputs, does not alter
  the frozen protocol, and does not resolve the paid Modal, model-inclusion, Phase 3 QA, browser
  E2E, figure, or result-registry blockers.

## Final Phase 18 clean-room follow-up — 2026-09-21

- Fresh clone: `/private/tmp/EvoVariant_cleanroom_phase17.2YeY5c` at
  `a0ea1caf989c928f10e65d5312fa17fde7c7aed8`. Its tracked status remained clean after setup,
  validation, figure regeneration, frontend build, and browser E2E.
- `make bootstrap`, `make frontend-install`, `make validate` (625 passed, 33 deselected, one
  existing warning, 95.34% coverage), `make test-scientific` (7 passed, 1 skipped), `make
  test-e2e` (14 passed, 1 skipped), protocol/ML-control-plane/schema/model-registry/registry
  verification, `make figures`, `make web-check`, and `make web-e2e` (4 passed) all passed.
- Clean-room `make figures` reproduced the explicit `BLOCKED` empty-registry state with no
  scientific outputs. `npm ci` reproduced 13 vulnerabilities (2 low, 2 moderate, 8 high, 1
  critical); no audit fix was applied. Raw ClinVar archives are ignored and absent in the clone,
  so archive-backed `make data-qc` remains evidence from the main checkout rather than being
  claimed as clean-room evidence.
- Gate decision: free/control-plane clean-room reproducibility `PASS`; full Phase 18 remains
  `BLOCKED / PARTIAL` because the real Modal smoke, verified model artifacts, and registered
  scientific outputs are absent. No release, deployment, publication, or spend was created.

## Phase 2 and Phase 4 authorized Modal pilot — 2026-09-21

- Approval: `artifacts/approvals/phase2_4_pilot_20260921.json`; scope was limited to a tiny
  canonical Evo2 pilot, cache miss/hit validation, and Phase 5 smoke/audit, with a `$2.00` cap.
- Superseded failures are preserved in
  `artifacts/modal/phase2_pilot_20260921_failed_attempts.json`. Deployment v2 loaded the Evo2
  weights but returned HTTP 500 because raw chromosome `10` was passed to UCSC. The fix was to
  centralize `normalize_chromosome`, use `chr10` for UCSC/cache/result identity, validate the
  `GRCh38`/`hg38` boundary, and add regression coverage. `make validate` then passed with 629
  tests, 33 deselected, and 95.35% coverage.
- Corrected deployment: canonical app `evovariant-tr`, v3, tag `phase2-pilot-20260921-r1`,
  H100, NGC PyTorch image, Evo2 revision
  `4b509ec2a22d6de472659f908bcb0714265ad3a7`. The model loaded successfully from the remote
  cache. No weights or prediction files were committed.
- Miss record `phase2-pilot-20260921-modal-miss`: HTTP 200, 36.2727 wall seconds,
  3.914133089 H100 runtime, 18,075,978,752-byte peak GPU memory, `cache_hit=false`, exact
  8192-bp context, forward/reverse raw scores, primary delta `-0.00025135278701782227`, and
  normalized ID `GRCh38:chr10:100065200:C>T`.
- Hit record `phase4-pilot-20260921-modal-hit`: identical request, HTTP 200, 0.956 wall
  seconds, `cache_hit=true`, exact numeric equality with the miss, and no fresh inference
  telemetry. The persistent file was listed at
  `evovariant-tr/predictions/0a/0a5e97eff1df2eab88c4a59a5434b1a5d9b0fa317820d6eaea7bc1d03e7871b3.json`.
- Billing: current H100 rate was `$3.95/hour`; rate-based wall-time estimates are not invoice
  measurements. Modal workspace summary changed from metered `$11.49` before remote requests to
  `$11.82` after the pilot family, with billed cost `$0.00`. The append-only ledger records null
  per-request measured USD and the workspace-level interpretation.
- Gate decisions: Phase 2 `PASS`; Phase 4 `PASS`; no full benchmark, training, HPO, fine-tuning,
  locked-test selection, or clinical classification was run.

## Phase 3 discrepancy impact reopening and Phase 5 candidate audit — 2026-09-21

- `artifacts/phase3_discrepancy_impact_20260921.json` records that the discrepancy is material:
  current valid t0 IDs are 1,402,895 versus the validation-only target 1,403,225, final temporal
  records are 946 versus 1,024, and B/LB is 536 versus 614 while P/LP remains 410. Current-only
  no-overlap, duplicate, reference, and gene-group invariants remain intact, but target-side
  IDs and invariants are unavailable. No filter was changed to force agreement.
- `artifacts/model_audit/phase5_candidate_audit_20260921.json` records official-source checks for
  all seven candidates. `evo2.json` is now `INCLUDED` with `VERIFIED` provenance. Nucleotide
  Transformer and Caduceus are deferred because their documented masked-LM APIs do not supply a
  verified apples-to-apples raw SNV VEP contract. GPN-Star is deferred because the matching
  100-way alignment archive is approximately 42 GB compressed and absent. CADD is deferred
  because the official GRCh38 annotation bundle is approximately 300 GB. PhyloP is a site-wise
  conservation track, not an allele-effect model. AlphaMissense is restricted to precomputed
  missense predictions and does not publish trained weights.
- `make model-registry-verify` passes with seven manifests and one included model. Phase 5
  remains `BLOCKED` for the multi-model gate; no deferred candidate is silently benchmarked.
- Dependency decision: no Phase 6 scoring is authorized until the Phase 3 discrepancy is resolved
  or accepted by a dated deviation and a second candidate either passes its own smoke gate or is
  formally excluded with an approved scope decision.

## Phase 3 partition semantics audit — 2026-09-21

- Implementation: `src/evovariant_tr/splits.py` now records mutually exclusive QA-funnel
  categories. `below_two_stars` counts only definitive t1 outcomes below the primary star gate;
  `not_definitive_at_t1` includes non-definitive outcomes at either star level.
- Validation: `./.venv/bin/pytest -q tests/unit/test_splits.py` passed (7 tests); `make data-qc`
  passed and regenerated the ignored archive-derived outputs. The corrected current partition is
  3,459 absent, 9,049 below-star definitive, 1,389,441 non-definitive, and 946 final, summing to
  1,402,895 t0 VUS.
- Artifact: `artifacts/phase3_partition_audit_20260921.json`; the tracked review summary now
  records the corrected counters. The target arithmetic is consistent with these semantics, but
  the target ID/source set is still unavailable. An independent existing parser path produces
  1,402,906 unique t0 VUS, confirming that the remaining discrepancy is not specific to the new
  streaming implementation. The remaining 330-ID discrepancy and 78-record B/LB difference remain
  material; Phase 3 stays `BLOCKED` and no scoring was started.
