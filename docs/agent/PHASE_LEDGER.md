# Phase Ledger — EvoVariant-TR ML Extension

Status: PENDING | IN_PROGRESS | PASS | BLOCKED | FAILED | DEFERRED

| Phase | Title | Status | Evidence |
|---:|---|---|---|
| 0 | Diagnostic snapshot | PASS | `docs/agent/BASELINE_AUDIT.md` (2026-09-21; no scientific/code repair) |
| 1 | Control plane + ML protocol | PASS | `research/ml_extension/`, control-plane CLI, and contract tests |
| 2 | Canonical scoring repair | BLOCKED | Local repair and validation pass; required real Modal pilot is unavailable because no verified Modal CLI/account authentication or paid-compute acknowledgement is present. See completion record below. |
| 3 | ML dataset + locked splits | PASS | `research/ml_extension/splits/phase3_manifest_summary.json`; generated split manifest SHA-256 `96d3e20e3cd97cb583b6b3d156ecd473c88ab66670704b1facb457351626ef72`, structural leakage/QC invariants pass; QA-count discrepancy is documented and blocks downstream model scoring until reconciled. |
| 4 | Modal compute foundation | BLOCKED | Local foundation and no-spend preflight pass in `cc7de42`; mandatory tiny remote inference, cache-hit evidence, and measured cost record remain unavailable without paid-compute acknowledgement. See completion record below. |
| 5 | Model registry + adapters | BLOCKED | Seven schema-valid candidate manifests and a fail-closed adapter framework pass locally in `473d314`; zero candidates have verified parity plus tiny smoke evidence, so no model is included. See completion record below. |
| 6 | Zero-shot multi-model benchmark | PENDING | |
| 7 | Embedding/representation extraction | PENDING | |
| 8 | Downstream supervised models | PENDING | |
| 9 | Hyperparameter optimization | PENDING | |
| 10 | Fine-tuning / PEFT | PENDING | |
| 11 | Ensemble/meta-classifier | PENDING | |
| 12 | Calibration + abstention | PENDING | |
| 13 | Ablation + robustness | PENDING | |
| 14 | Locked statistical evaluation | PENDING | |
| 15 | Batch research pipeline | PENDING | |
| 16 | Research workbench UI | PENDING | |
| 17 | Figures/tables/report artifacts | PENDING | |
| 18 | Security + clean-room reproducibility | PENDING | |
| 19 | Final release gate | PENDING | |

For each PASS append:
- commit,
- commands,
- tests,
- artifact hashes,
- spend,
- remaining risks.

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
- Blocking evidence: a real Modal pilot is an explicit Phase 2 gate, but this environment has
  no verified Modal CLI/account authentication and no user-provided paid-compute
  acknowledgement. Local/fake tests cannot substitute for that gate.
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
