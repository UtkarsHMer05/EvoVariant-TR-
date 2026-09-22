# Phase Ledger — EvoVariant-TR ML Extension

Status: PENDING | IN_PROGRESS | PASS | PARTIAL | BLOCKED | FAILED | DEFERRED | DEFERRED_BY_COMPUTE | SUBSET_ONLY

| Phase | Title | Status | Evidence |
|---:|---|---|---|
| 0 | Diagnostic snapshot | PASS | `docs/agent/BASELINE_AUDIT.md` (2026-09-21; no scientific/code repair) |
| 1 | Control plane + ML protocol | PASS | `research/ml_extension/`, control-plane CLI, and contract tests |
| 2 | Canonical scoring repair | PASS | Local repair plus real Evo2 7B H100 raw-SNV pilot; corrected `10` to `chr10`, exact 8192-bp context, forward/reverse raw scores, provenance, and HTTP 200 evidence in `artifacts/modal/phase2_phase4_pilot_20260921_success.json`. |
| 3 | ML dataset + locked splits | PASS | `ML-DEV-001`/`ML-DEV-002`, `artifacts/phase3_integrity_audit_20260921.json`, independent `artifacts/reference/grch38_validation_20260921.json`, and authoritative manifests under `research/ml_extension/splits/`; 946 locked records, 536 B/LB, 410 P/LP, reference mismatches 0, deterministic regeneration PASS. |
| 4 | Modal compute foundation | PASS | Real persistent prediction-cache miss/hit, exact numeric equality, 36.2727s versus 0.956s wall time, H100 telemetry, and workspace billing evidence are recorded in the Phase 2/4 pilot artifact and cost ledger. |
| 5 | Model registry + adapters | PASS / ROSTER FINAL | `artifacts/model_audit/phase5_final_roster_20260921.json`; Evo2 is `INCLUDED_RAW_SCORE`, Nucleotide Transformer/Caduceus are separated `INCLUDED_EMBEDDING_TRACK` decisions, CADD/PhyloP are public CPU-comparator contracts, GPN is `DEFERRED`, and AlphaMissense is `SUBSET_ONLY`; no full extraction or benchmark ran. |
| 6 | Zero-shot multi-model benchmark | PARTIAL / FORMAL EVO2 SUBTRACK PASS; MULTI-MODEL TRACK PARTIAL | The bounded formal Evo2 track completed exactly 4,000/4,000 rows under the fresh PAR-resume approval. The final artifact is `artifacts/phase6/phase6_formal_evo2_20260921_full_overnight_20260922.json` (SHA-256 `b04940b3b5845fd57144f54a9862da8d9d89fb1b98d9c79fc45364e7a21ef54d`) with 125 complete shards, 124 reused verified shards, 32 newly scored remote rows, zero pending rows, duplicates, unexpected IDs, reference mismatches, non-finite scores, labels sent to Modal, or locked-test rows. The two chrY PAR hard-mask cases are covered by `DEV-2026-001`/D-095 and `artifacts/reference/par_mask_resolution_20260922.json`; D-096 records acceptance. The broader multi-model Phase 6 benchmark remains partial because its NT/Caduceus representation work is recorded under the separately authorized Phase 7 track; fine-tuning and locked-test work remain outside Phase 6 and were not run. |
| 7 | Embedding/representation extraction | PASS / FORMAL 4,000-ROW MATRIX | `artifacts/phase7/formal_budgeted_representation_20260922.json` (SHA-256 `cea3b1c733eb70e58dcbaf49784fe9405e93a65eb0d7101aca464d3368b61783`); NT resumed 2,432 cached rows and scored only 1,568 new IDs, Caduceus passed the 64-row pilot and completed 4,000 rows, all shard/plan/NPZ integrity checks passed, and no labels or locked rows crossed the remote boundary. |
| 8 | Downstream supervised models | PASS / FORMAL 4,000-ROW DEVELOPMENT STUDY | `research/runs/formal_cpu_20260922/phase8/summary.json` (SHA-256 `c1f576ec854051e19238438017d28a0c0baf421518eaea9e78b02ff91617ae95`); 36 logistic/stump/MLP feature-family combinations were fit on TRAIN and evaluated on VALIDATION, with explicit comparator complete-case coverage. |
| 9 | Hyperparameter optimization | PASS / FORMAL VALIDATION-ONLY | `research/runs/formal_cpu_20260922/phase9/summary.json` (SHA-256 `544016d582d6a37fec9d29a5e17834f99717f0f76e649563cc6b412784e36500`); 12 cached-feature logistic studies preserve every bounded trial and select only from VALIDATION. |
| 10 | Fine-tuning / PEFT | DEFERRED_BY_COMPUTE | `artifacts/modal/phase10_adaptation_deferral_20260921.json`; adaptation is formally `DEFERRED_BY_COMPUTE` with no training run or scientific metrics. |
| 11 | Ensemble/meta-classifier | PASS / FORMAL DEVELOPMENT | `research/runs/formal_cpu_20260922/phase11/ensemble_analysis.json` (SHA-256 `83a35e348d7a6359f3ed9a1d7bf5a5cde44b67d1d76cfd81e19bfa38819a7f1b`); diversity, error overlap, correlation, kappa, mean, weighted, vote, and gene-grouped 5-fold OOF stacking were evaluated without locked labels. |
| 12 | Calibration + abstention | PASS / FORMAL DEVELOPMENT | `research/runs/formal_cpu_20260922/phase12/calibration_abstention.json` (SHA-256 `bf1f9078386f35619d5188eabb07e8345f168cf0717565180cb0bca4c42520a3`); raw, train-fit Platt, isotonic, reliability, Brier/NLL/ECE, risk-coverage, and abstention diagnostics were evaluated on VALIDATION only. |
| 13 | Ablation + robustness | PASS / FORMAL DEVELOPMENT MATRIX | `research/runs/formal_cpu_20260922/phase13/ablations_learning_curves_robustness.json` (SHA-256 `03205bb41bf2db8b814a8f7d312d01190f3f8c3644890e7aa3868e04c61f601f`); 30 ablation cells, exact 10/25/50/75/100% grouped learning curves, seed robustness, subgroups, errors, calibration/abstention effects, and justified no-new-GPU skips are recorded. |
| 14 | Locked statistical evaluation | PASS / FORMAL EVO2 LOCKED SUBGATE | `artifacts/phase14/phase14_locked_evo2_20260922.json` (SHA-256 `4dd9b9229c47d65491345e87b70a6f6739432c24a7585966f4aea97a9d115499`) records exactly 946 completed rows, 30 paid Evo2 H100 shard calls, 1,304.297864 seconds remote runtime, zero retries, zero duplicates/unexpected IDs/reference mismatches, finite scores, no remote labels, and all integrity gates true. Raw predictions SHA-256 `ae288252a3f1bfc8a1754b1626ea6ff91a041df9ff09daf07d1411a242ba2508`; local joined output SHA-256 `77cbbb48032ac7852ff09f93ea448d1e98ca21457843c1feda16f31e8dc530e7`. The exact approval is `artifacts/approvals/phase14_locked_evo2_20260922.json` (SHA-256 `4b619747a73942e56e15fef4040db1591760ee5a7813fb8f14fcc4740050dae7`) bound to execution HEAD `c6c431869724666c84252cbd43979f2c4f38875f`; finalization reused all 30 verified shards locally with zero additional calls. |
| 15 | Batch research pipeline | BLOCKED / LOCAL CONTRACT + KILL/RESTART VERIFIED | `scripts/plan_batch.py`, `src/evovariant_tr/batch_pipeline.py`, and `tests/unit/test_batch_pipeline.py`; label-free CSV/VCF parsing, immutable input/model plan, caller-supplied cost estimate, injected scorer, hash-verified resumable shards, simulated process-interruption recovery, failure taxonomy, and deterministic export are locally covered. Remote batch parity, full-cohort authorization, and remote smoke remain absent. |
| 16 | Research workbench UI | PARTIAL / DEVELOPMENT + FINAL EVIDENCE CONNECTED | `apps/web/src/app/api/research/status/route.ts`, `research/runs/phase16_ui_status.json`; twelve completed registered runs, including the Phase 14 `FINAL` record, now feed the read-only evidence panel showing the completed CPU phase gates, frozen selection state, and figure/table coverage. Final scientific result promotion remains limited by downstream gates. `make web-check`, all four `make web-e2e` journeys, the frontend contract tests, and fresh-clone fallback/API checks PASS at `27352e5`. |
| 17 | Figures/tables/report artifacts | BLOCKED / CONDITIONAL GATE + PARTIAL SOURCES | `research/runs/phase17_fig_status.json` and `research/figures/preliminary/preliminary_bundle_manifest.json`; 15/18 applicable figure families and 11/11 applicable tables have hash-registered sources, and a completed `FINAL` run is now registered. `hpo_importance` is `NOT_APPLICABLE_WITH_DOCUMENTED_REASON` under `artifacts/phase9/hpo_parameter_importance_deferral_20260922.json` because the validation-only HPO evidence has four trials per study and no predeclared importance estimator. The `fine_tuning_summary` table is also not applicable because Phase 10 is `DEFERRED_BY_COMPUTE`. Three mandatory source families (`context_length`, `loss`, `temporal_cohort`) remain missing, so the final bundle produces zero outputs; the separate non-promotable preliminary bundle contains 26 development-stage outputs. |
| 18 | Security + clean-room reproducibility | BLOCKED / CONTROL SURFACE ONLY | Fresh clone from `8025a25` passes bootstrap, secret scan, Ruff, strict mypy, 714-test validation with one skip, and 95.01% coverage; registry verification and the updated fail-closed figure gate also reproduce. Prior frontend build/browser evidence remains verified at `27352e5`. The no-spend Modal preflight is `PLANNED` with zero remote calls. `make clean-room` remains `BLOCKED`: full scientific Modal reproduction and complete mandatory figure-source regeneration are unrun. |
| 19 | Final release gate | BLOCKED | `research/runs/phase19_release_status.json`; the PRELIMINARY registry is connected, but full-cohort science, locked evaluation, complete figures, and final-release evidence remain unresolved. |

Current control-plane checkpoint on `research/evovariant-tr`: Phase 14 is complete for the
explicitly authorized Evo2-only locked subgate, with no paid worker or active container remaining.
The Phase 14 approval was exact-scope and bound to execution HEAD `c6c4318`; NT, Caduceus,
fine-tuning, and release/deployment work were excluded. Phase 15 remains blocked for remote
batch parity, Phase 16 remains partial, and Phases 17–19 remain fail-closed on their documented
missing sources, FINAL registry run, full scientific clean-room reproduction, or release evidence.

## Current formal development design checkpoint — 2026-09-21

- `ML-DEV-BUDGETED-001` is an additive development-study amendment, not a rewrite of the
  frozen 239,992-record population or the existing 2,848-row preliminary history. The 946-record
  temporal cohort remains untouched `LOCKED_TEST`.
- The prefix audit reconstructs the exact old rule as ascending
  `SHA256(normalized_variant_id)` followed by a budget stop. It does not match the frozen manifest
  row prefix, and representativeness is `NOT_ESTABLISHED`. The audit includes class, split, gene,
  chromosome, position, variant type, source release, archived review status, and temporal metadata
  availability. Consequence type and submission date were unavailable in the available schemas.
- The formal subset has 4,000 records: TRAIN 3,199 (2,645 negative, 554 positive), VALIDATION
  801 (581 negative, 220 positive), 3,226 negative and 774 positive overall, and 1,927 unique
  genes. Hash selection is within frozen split/class strata using seed
  `ML-DEV-BUDGETED-001|2026-09-21|sha256-v1`; selection does not read model predictions. TRAIN and
  VALIDATION remain gene-disjoint, the subset has zero locked-test overlap, and 56 IDs overlap the
  preliminary prefix for cache accounting only.
- Formal artifacts are under
  `research/ml_extension/splits/formal_budgeted_20260921/`: train, validation, and combined
  manifests; `prefix_audit.json`; `population_vs_subset_QC.json`; `manifest_hashes.json`;
  `source_metadata_aggregate.json`; and `cost_estimate.json`. The same exact manifests are reserved
  for the predeclared raw-score and representation tracks and the common classifier matrix.
- The local cost plan estimates Evo2 `$6.506744` for 3,944 new variants, NT `$0.378539`, Caduceus
  `$0.226398`, and `$7.111681` total. The previous `$5.00` approval is consumed. The latest
  explicit user authorization permits an `$8.00` hard cap and `$7.75` runner stop; the fresh
  approval artifact, comparator evidence, and 64-row Evo2 preflight remain required before the
  full formal workload. The read-only billing snapshot is provider-workspace evidence only, not an
  invoice or approval.
- The independent cache-reuse verifier PASSed exactly 56 compatible historical Evo2 rows after
  checking model revision, 8,192-bp context, orientation, score semantics, shard payload hashes,
  and aggregate arithmetic. The old prefix remains `PRELIMINARY` and is not treated as a formal
  sample.
- Exact formal comparator qualification completed locally before any GPU request. The aggregate
  artifact is `artifacts/phase6a/comparators/phase6a_comparator_qualification_20260921.json`
  (`PASS_WITH_ALPHA_MISSENSE_DEFERRED`); CADD v1.7 coverage is 2,891/4,000, PhyloP100way hg38
  coverage is 3,997/4,000, and AlphaMissense remains eligible-only with zero predictions. The
  child artifact hashes are recorded in the aggregate; missing comparator values remain missing
  and are never imputed as zeros or labels.
- The approval-gated 64-row Evo2 preflight was attempted twice after read-only Modal checks. Both
  ephemeral apps (`ap-3nvzpB5VADtBwNaoF5aOmA` and `ap-2yoBkvnIItyhk0pULH36CA`) terminated with
  `StreamTerminatedError: Connection lost` after image construction and before a remote worker
  produced output. The final artifact records zero completed shards, zero remote rows, unchanged
  billing (`$19.33` metered and `$0.00` billed), and no active container. The resulting
  `FAIL_FORMAL_PREFLIGHT` gate blocks the full Evo2 and all dependent formal representations.
- Local validation is green: `make validate` reports 703 passed, 33 deselected, strict mypy over
  57 source files, Ruff, secret scan, and 95.02% coverage; the focused figure suite reports 13
  passed. `make budgeted-study-design`, `make finetune-smoke`, `make figures`,
  `make registry-verify`, `make ui-check`, `make web-check`, and four local browser E2E tests pass.
  These are engineering/control-plane gates and do not promote a scientific run.
- Phase 10 remains `DEFERRED_BY_COMPUTE`. The final figure gate now permits an explicit
  `NOT_APPLICABLE_WITH_DOCUMENTED_REASON` conditional family for the fine-tuning summary while
  keeping mandatory core sources and a completed `FINAL` run blocking. The `finetune-smoke`
  command surface now emits the same explicit status.

## Latest recovery, reference, and pre-Phase-6 checkpoint — 2026-09-21

- Phase 3 is now `PASS` for the ML extension only. The exhaustive recovery artifact
  `artifacts/phase3_recovery_search_20260921.json` did not recover the historical normalized-ID
  or source-row manifest, so `ML-DEV-001` freezes the reproducible current cohort without adding
  or filter-tuning records. The original frozen zero-shot protocol remains unchanged.
- The ML-extension reference gap is closed by `ML-DEV-002`: Broad GATK hg38/v0
  `Homo_sapiens_assembly38.fasta`, 3,249,912,778 bytes, SHA-256
  `93157a161863464c9435062fd67c173fdaf99cb8b32f1455018361387ffa5564`, plus the provided FAI,
  160,928 bytes, SHA-256
  `edefd93c489dc1baefad312f40388089f8db5cf6dcc3ba0955669ead274e8b6b`. The large assets remain
  outside Git; source metadata is in `data/manifests/grch38.json`.
- The authoritative locked test has 946 records: 536 B/LB, 410 P/LP, 946 gene labels, and 367
  unique genes. The test manifest SHA-256 is
  `9f9e052d21f4a6a32f595cb20f48cb81e033c0481942820d04f9b67d410a16cb`; the canonical record-set
  SHA-256 is `ae4f6f1c1ad7c8d9ea78a9e5ce0380b1d8862a125592be5474b7826de165a6a0`. The authoritative
  cohort manifest SHA-256 is `0d4386b34196a523ca43b50cc4242d4ecb01df2b40923fc0aa52f15d61c593b1`.
  Independent reference validation checked all 946 records, found zero mismatches and zero missing
  coordinates, and deterministic regeneration passed.
- Phase 5 final roster: Evo2 `INCLUDED_RAW_SCORE`; Nucleotide Transformer and Caduceus
  `INCLUDED_EMBEDDING_TRACK` only; GPN `DEFERRED`; CADD and PhyloP `INCLUDED_RAW_SCORE` as
  separately labeled public CPU-comparator contracts; AlphaMissense `SUBSET_ONLY`.
  Masked-LM logits are not treated as Evo2-style allele likelihoods.
- The required pre-Phase-6 checkpoint is
  `artifacts/phase5_final_checkpoint_20260921.json`. It records model-by-model Phase 6/7 cost
  estimates, source/asset caveats, and the current read-only Modal snapshot of `$12.19` metered
  and `$0.00` billed. No full Phase 6 benchmark, Phase 7 extraction, training, HPO, fine-tuning,
  or locked-test evaluation was launched.

## Phase6A bounded qualification — 2026-09-21

- Implementation commit: `4e072ef` (`feat: complete bounded phase6a qualification`).
- The current user approval is `artifacts/approvals/phase6a_throughput_20260921.json`, tied to
  extension protocol hash `39de386dcf952af0b4d03de770b68ad2c44d49a113510cafab184d6eebc0c6e3`,
  an approximate `$1.50` Modal cap, sample sizes 8/16/32 for Evo2, model batch sizes 1/2/4/8,
  and a post-Evo2 tiny unlabeled NT/Caduceus representation smoke. No older approval was edited.
- The read-only cache preflight found 0 reusable locked-cohort Evo2 cache hits and 946 records
  requiring new inference if a full run is ever separately approved. The unrelated Phase 2/4
  pilot cache and the historical `.kilo` aggregate metrics were not reused. Evidence and hash:
  `artifacts/phase6a/phase6a_cache_preflight_20260921.json` (`eda364b57d5c10021b961e95f60e3d4ffef7caab7143d1311711c668e70c4d5e`).
- CPU comparator qualification completed before GPU work without reading labels for scoring or
  invoking Modal. CADD v1.7 GRCh38 returned usable values for 918/946 records (28 explicit
  requested-ref/alt missing values); UCSC phyloP100way returned 946/946 sitewise values; and
  AlphaMissense had 507 eligible missense rows but 0/507 prediction coverage because no
  prediction asset or transcript-level lookup was used. The aggregate evidence hash is
  `202d683d81c82f5f860228f68ee53af7c7050c763b97d0285a9c9995dfe3bc58`.
- Evo2 `evo2_7b`, revision `4b509ec2a22d6de472659f908bcb0714265ad3a7`, ran on canonical
  GRCh38 8192-bp forward/reverse windows with alternate-minus-reference log likelihood. All
  12 H100 configurations passed with finite outputs; the best warm observation was 0.724826
  variants/s at sample 8 and model sequence batch size 2, with peak GPU allocated/reserved
  `18,075,978,752` / `22,267,559,936` bytes and a measured full-946 rate estimate of `$1.4732`
  and `1,342.653` seconds including one model load. This is a bounded model-only estimate and
  excludes full sequence preparation, network, cache writes, and any full-cohort inference.
  All 12 A100-40GB configurations failed closed at scoring with the checkpoint's
  `Device compute capability 8.9 or higher required for FP8 execution` error; no A100 result is
  treated as throughput. Evidence and hash:
  `artifacts/phase6a/phase6a_evo2_throughput_20260921.json`
  (`6015e40620d4d10adc355f0e8dd8edd9ae8751a3311b769be3f1b706b8251bb8`).
- The post-Evo2 representation smoke used four SHA-256-selected locked-cohort variants, actual
  8192-bp GRCh38 reference/alternate forward and reverse views, mean-token pooling, and no
  feature-cache write. All eight H100 configurations passed: Nucleotide Transformer produced
  finite pooled shapes `[16, 1024]` with best warm throughput 11.7441 variants/s, and Caduceus
  produced finite pooled shapes `[16, 256]` with best warm throughput 19.8545 variants/s. The
  first attempt failed before model load because the worker image omitted the local sequence
  helper; the corrected retry is the only representation result. Evidence and hash:
  `artifacts/phase6a/phase6a_representation_throughput_20260921.json`
  (`48240f71602ae25570ebad2e52d5579a19f2f4bfa848e3f149b6083c71829372`).
- The Phase6A registry reconciliation is in
  `artifacts/phase6a/phase6a_registry_update_20260921.json`. CADD and PhyloP are now qualified
  public CPU comparators with explicit semantics/missingness but remain `SUBSET_ONLY` in the
  model registry so the exact Evo2-only raw benchmark inclusion boundary cannot silently widen;
  AlphaMissense remains `SUBSET_ONLY`; and NT/Caduceus remain `SUBSET_ONLY` embedding tracks.
  `make model-registry-verify` passed with seven manifests and only Evo2 in the benchmark
  inclusion set.
- Modal workspace summaries recorded `$12.34` to `$12.90` metered around Evo2 and `$12.94` to
  `$12.97` around the representation smoke, with `$0.00` billed in both snapshots. The combined
  client wall-rate estimate recorded by the two artifacts is `$0.560167`; this is not a provider
  per-request invoice. The result registry remains empty, and no labels were used for scoring or
  selection.
- Gate decision: Phase6A qualification `PASS` within scope. Stop here. Full Phase 6 zero-shot
  inference, full Phase 7 feature extraction, training, HPO, fine-tuning, locked evaluation,
  and downstream phases remain blocked/not started pending their own gates and authorization.

## Historical priority continuation before recovery — 2026-09-21

- Phase 3 was audited using `make phase3-audit`, including both manifest-verified ClinVar archives,
  all frozen filters, exact normalized IDs, date/review gates, t0/t1 reconciliation, split schema
  and hashes, overlap/leakage invariants, and two fresh deterministic rebuilds. The audit returned
  local PASS for every check and overall `BLOCKED` only for
  `BLOCKED_MISSING_TARGET_ID_SET` and `NOT_RUN` independent FASTA validation.
- The current cohort is recorded without target forcing: train `191,957`, validation `48,035`,
  locked test `946`, development positive `46,429`, development negative `193,563`, train genes
  `9,682`, validation genes `57`, and locked-test classes BLB `536` / PLP `410`. Hashes and exact
  impact deltas are in the two Phase 3 artifacts above.
- Phase 5 used the existing bounded approval and ran two additional official checkpoints on H100.
  Nucleotide Transformer v2 and Caduceus-Ph both returned finite logits and hidden states and
  finite synthetic ref/alt embedding deltas. These are `SUBSET_ONLY` plumbing/representation
  tracks; no score was added to the raw-score benchmark and no cohort model was trained.
- The required pre-large-run checkpoint is `artifacts/phase5_checkpoint_20260921.json`.
  Phase 6, Phase 7 cohort extraction, Phase 10 training, HPO, and locked evaluation remain
  explicitly not launched. The current workspace billing snapshot after the small smokes is
  metered `$12.21122616` and billed `$0.00`; this is workspace-level only.

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

- Fresh no-spend verification passed `make modal-smoke`, the scientific tier (`7 passed, 1
  skipped`), API/E2E (`14 passed, 1 skipped`), and `make web-check`. Figure generation and the
  release surface remain explicitly `BLOCKED` with zero registered scientific outputs; no GPU
  invocation occurred.
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
- The latest validation after the Phase 3 source-archive verification fix passed `make validate`
  with 650 tests, 33 deselected, strict mypy over 51 source files, Ruff, secret scan, and 95.08%
  coverage.
- Phase 5's multi-model inclusion requirement is formally `DEFERRED` after the source-backed
  seven-candidate audit. The deferral preserves the exact exclusion reasons and requires a new
  candidate-specific approval and parity smoke before Phase 6 can be reopened; it does not count
  synthetic comparators as scientific models.
- Commits `696fcd6` and `89563b2` tighten and test the Evo2 adapter readiness boundary: local parity cannot produce
  `READY`; an explicit named remote-smoke evidence checker must pass before an injected scorer
  can execute. This is a fail-closed control fix, not new remote smoke evidence, so Phase 5's
  multi-model deferral and Phase 6 blocker remain unchanged.
- The Phase 3 source-provenance follow-up found no alternate official archive path: both archived
  NCBI URLs return the manifest-matching release sizes, while the corresponding non-archive and
  year-subdirectory fallback URLs return HTTP 404. This strengthens the unresolved target-ID/
  source-provenance blocker; it does not justify replacing the frozen archives or changing filters.
- The t0 filter-sensitivity audit also found no simple reconciliation: broad uncertainty labels
  remain 139 IDs below the target, while relaxing assembly/origin/type filters overshoots. Legacy
  allele fields are unusable (`NA`) and `ClinSigSimple` is numeric only. The audit is preserved in
  `artifacts/phase3_filter_sensitivity_20260921.json`; Phase 3 remains `BLOCKED`.
- Commit `c401140` repairs the generic manifest verification command's compatibility with the
  legacy single-file ClinVar manifests. `make data-verify` now passes for both manifest-verified
  raw archives, while the multi-entry manifest tests remain passing; this is an engineering/data
  integrity gate and does not alter the frozen cohort or resolve the Phase 3 target discrepancy.
- Commit `601e366` makes the Phase 3 builder verify both source archives against their manifests
  before processing. The archive-backed `make data-qc` rerun passed with the existing split-manifest
  hash `96d3e20e3cd97cb583b6b3d156ecd473c88ab66670704b1facb457351626ef72` and split hash
  `bac30ed0a818258445a7340b1e96fe592902af5d4d7e899fbe227d24af955722`; a tampered-source test
  fails closed. This strengthens provenance without changing the frozen cohort definition.

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

## Current full-goal continuation audit — 2026-09-21

- The active task requests continuation beyond the completed Phase6A qualification. This is now
  recorded as the current objective, while the Phase6A approval boundary remains unchanged.
- `artifacts/approvals/full_run_approval.json` is rejected as stale: its 2026-08-19 legacy
  protocol identifier does not match the current ML-extension protocol hash
  `39de386dcf952af0b4d03de770b68ad2c44d49a113510cafab184d6eebc0c6e3`.
- `artifacts/approvals/phase6a_throughput_20260921.json` remains valid only for Phase6A and
  explicitly excludes full Phase 6, t0-pool inference, training, HPO, fine-tuning, and locked
  evaluation. It is not reused for the next phase.
- No paid continuation was launched. Read-only Modal billing reports `$13.00` metered and
  `$0.00` billed; canonical and legacy deployed app entries have zero active tasks.
- Free gates at the current checkout pass: `make validate` (656 passed, 33 deselected, 95.12%
  coverage), ML protocol/schema/model-registry/registry checks, and `make web-check`. `make
  figures` and `make release-check` remain `BLOCKED` with zero registered scientific results.
- Gate decision: Phase6A remains `PASS` within scope; Phase 6 and all dependent phases remain
  `BLOCKED` pending a current exact-scope approval and subsequent scientific artifacts. The next
  action is to obtain that approval, hash-check it, and run the smallest approved Phase 6 parity
  and cohort step.

## Phase 6/7 execution-surface subgate — 2026-09-21

- Engineering outcome: `PASS` for the local control surface only; scientific Phase 6 and Phase 7
  remain `BLOCKED / NOT STARTED`.
- Added `src/evovariant_tr/phase_execution.py`, `scripts/phase_execute.py`, and the
  `make phase-execute` wrapper. The implementation is approval-gated, protocol-hash-checked,
  label-free at transport, explicit about source-vs-`chr` identity, and resumable at the
  content-hashed shard level. Implementation commit: `82ff2d6` (`feat: add gated resumable
  phase execution`).
- Score responses require completed finite raw deltas and exact cohort identity. Embedding
  responses require the frozen layer, validated ref/alt feature hashes, finite vectors, and exact
  cohort identity. The output artifacts retain provenance and do not manufacture metrics.
- Added the source-level Modal `extract_embeddings_batch` endpoint with an eight-variant bound,
  one warm-worker forward path, cache reuse, and explicit partial-failure reporting. No Modal
  deployment or request was performed for this change.
- Evidence: `make validate` passed with 672 tests, 33 deselected, strict mypy, Ruff, secret scan,
  and 95.02% coverage; the targeted Phase 6/7 suite passed 19 tests. No scientific output or
  registry entry was generated, so no phase status was promoted.
- Dependency: a fresh approval must cover the exact cohort/model/endpoint/scope and match the
  current ML protocol hash before `scripts/phase_execute.py` is used for paid work.

## Phase 8/9 downstream CPU subgate — 2026-09-21

- Engineering outcome: `PASS` for the local artifact-driven implementation; scientific Phase 8
  and Phase 9 remain `BLOCKED / NOT STARTED` because no real Phase 7 feature cache exists.
- Added `src/evovariant_tr/downstream_pipeline.py`, `scripts/train_from_features.py`, and
  `scripts/hpo_from_features.py`. `make train` and `make hpo` retain blocked status behavior by
  default and run only when explicit feature/config paths are supplied. Implementation commit:
  `af97560` (`feat: add local downstream training and hpo runners`).
- The loader verifies feature hashes and model/layer identity, requires TRAIN/VALIDATION labels
  and gene metadata, rejects LOCKED_TEST and duplicate IDs, and enforces train/validation
  identity and gene separation before fitting. Baselines fit only on TRAIN; metrics and HPO
  selection read only VALIDATION.
- Synthetic tests pass for baseline outputs, metric validation, tamper/leakage rejection, and
  bounded HPO. No real feature artifact, locked label, scientific registry record, or figure was
  produced. The next dependency is verified Phase 7 development extraction, not additional CPU
  tuning.

## Phase 11/12 ensemble and uncertainty subgate — 2026-09-21

- Engineering outcome: `PASS` for the validation-only analysis surface; scientific Phases 11 and
  12 remain `BLOCKED / NOT STARTED`, and Phase 13 remains blocked on frozen base predictions.
- Added `src/evovariant_tr/analysis_pipeline.py` and `scripts/analyze_ensemble.py`. The path is
  local CPU-only, requires common validation identities, records disagreement/error overlap and
  correlation, and uses fixed weighted aggregation before computing calibration and abstention
  artifacts. Implementation commit: `a3df7ac` (`feat: add validation-only ensemble analysis`).
- Locked-test rows are rejected by default; incomplete/duplicate model coverage and invalid
  scores fail closed. The abstention adapter receives logit-transformed probabilities so its
  zero-centered decision convention is explicit rather than assumed.
- Evidence: `make validate` passed with 679 tests, 33 deselected, strict mypy, Ruff, secret scan,
  and 95.00% coverage. No real predictions or registry outputs were produced; `make ensemble`
  remains blocked unless explicit artifact/model paths are supplied.

## Current status-surface reconciliation — 2026-09-21

- Updated the current Phase 6/7/release status commands and the zero-shot benchmark status
  artifact so their blockers match the accepted Phase3/Phase5/Phase6A state. Historical entries
  retain their original wording; no historical evidence was rewritten.
- Rerun evidence: `make benchmark-zero-shot`, `make extract-features`, and `make release-check`
  all returned truthful `BLOCKED` artifacts with no network or paid compute. `make validate`
  passed with 679 tests, 33 deselected, strict mypy, Ruff, secret scan, and 95.00% coverage.

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

## Phase 14 frozen locked-evaluation subgate — 2026-09-21

- Engineering gate: `PASS`; scientific Phase 14 gate: `BLOCKED / NOT STARTED`.
- The new evaluator in `src/evovariant_tr/final_evaluation.py` and
  `scripts/evaluate_locked.py` is committed as `1423577`. It accepts only one explicitly named
  model, `LOCKED_TEST` rows, both classes, a selection-closed content-hashed configuration, and
  an immutable output path. It computes fixed-threshold metrics and bootstrap AUROC without any
  model/threshold selection from test labels.
- Default control-surface evidence: `make evaluate` wrote
  `research/runs/phase14_stat_status.json` as `BLOCKED`; no real locked evaluation or paid/remote
  work was attempted. The output remains a status artifact, not a scientific result.
- Validation evidence: `make validate` passed with 684 tests, 33 deselected, strict mypy over 56
  source files, Ruff, secret scan, and 95.04% coverage.
- Dependency: a real approved Phase 7/downstream artifact chain and current exact-scope approval
  are required before any locked evaluation can be considered. Phases 15-19 remain blocked.

## Fresh no-spend gate refresh — 2026-09-21

- Local control-plane PASS evidence: ML protocol, schema, model-registry, and experiment-registry
  verification all passed. The registry still contains no scientific result records.
- Software validation evidence: `make test-scientific` passed 7 with 1 skip; `make test-e2e` passed
  14 with 1 skip; and `make web-check` passed ESLint, TypeScript, and the Next production build.
  The frontend build emitted two non-fatal Turbopack dynamic-filesystem tracing warnings for
  `apps/web/src/app/api/registry/route.ts`.
- Figure/status evidence: `make figures` produced zero available figures and `BLOCKED` manifests;
  the Phase 6-19 status surfaces remained blocked for their documented missing dependencies. No
  remote endpoint, model download, training, HPO, locked evaluation, deployment, release, or
  push was performed.
- Gate decision: free local/control-plane refresh `PASS`; scientific completion remains
  `BLOCKED / PARTIAL` pending current exact-scope approval and immutable scientific artifacts.

## Current Modal preflight and billing snapshot — 2026-09-21

- `make modal-smoke` passed the no-spend preflight with installed/authenticated Modal, zero GPU
  count, `PLANNED` status, and no remote invocation. No Phase 6/7 workload was started.
- Fresh read-only workspace evidence: `modal billing summary` reported `$13.00` metered and
  `$0.00` billed; `modal app list` showed zero tasks for the listed app entries. These values are
  workspace observations, not per-request invoice measurements.
- Gate decision: authentication/preflight `PASS`; paid scientific execution remains
  `BLOCKED` until a current exact-scope approval matches the frozen protocol hash and names the
  workload.

## Current checkout metadata refresh — 2026-09-21

- The current validated branch remains `research/evovariant-tr`; the latest code-bearing
  continuation commit is `1423577` and the subsequent changes in this metadata block are
  documentation-only. The worktree has no project-file changes; only the pre-existing untracked
  `.agents/` directory remains and was not modified.
- The stale pre-continuation HEAD reference at the top of `PROJECT_STATE.md` was corrected. This
  is a documentation-integrity update only; Phase6A remains the latest authorized remote work and
  full Phase 6/7 plus dependent scientific phases remain blocked.
- Evidence: current Git status/HEAD inspection and the successful no-spend validation and
  control-plane gates recorded above.

## Current bounded development continuation — 2026-09-21

- A fresh, exact-scope user approval was created at
  `artifacts/approvals/phase6_phase7_development_20260921.json` (SHA-256
  `f903a8ebed963e5c82e5a7578c54fc674685f1b5c1f445b23e38fd4b895fb50a`). It is tied to protocol
  hash `39de386dcf952af0b4d03de770b68ad2c44d49a113510cafab184d6eebc0c6e3`, the development
  manifest SHA-256 `96d3e20e3cd97cb583b6b3d156ecd473c88ab66670704b1facb457351626ef72`, exact Evo2
  revision `4b509ec2a22d6de472659f908bcb0714265ad3a7`, H100, 8192-bp forward/RC scoring, and a
  hard `$5.00` cap. Locked-test labels, t0 1.4M inference, fine-tuning, Phase 10, Phase 14,
  deployment, release, and publication were excluded. The user explicitly increased the cap
  from `$3.00` to `$5.00` for this scope.
- The bounded runner is in `scripts/phase6_development_evo2.py`. Fix commits are `69a2e4f`
  (map ClinVar `MT`/`M` to the frozen FASTA's `chrM` and record local preparation failures) and
  `0f1c5a4` (verify cached source IDs, restore cached rate samples, and fix finalizer completion
  arithmetic). The first attempt failed closed before the next shard because the manifest used
  `MT` while the GATK FASTA uses `chrM`; a second attempt exposed and fixed a local `len(int)`
  finalizer bug. No invalid or partially returned shard was accepted.
- The final Phase 6 artifact is
  `artifacts/phase6/phase6_development_evo2_20260921.json` (SHA-256
  `be5edd45942a70f494512c111dd1245f2d721c1a10f909e9de03524f5a22cfe5`) with status
  `PARTIAL_BUDGET_STOP`. It contains 2,848 completed records (2,276 TRAIN, 572 VALIDATION) out
  of 239,992 development records, 237,144 remaining, 89 verified shards, and no LOCKED_TEST
  rows. The predictions JSONL hash is
  `04baecf2d547ffd8ccaafa5eeeb2f11d2cccb46696f7cb9445ab317d133ba16d`; the processed prefix
  contains both labels and matches the approved manifest exactly. All raw scores are finite,
  forward/RC deltas recompute exactly, and every shard payload hash validates.
- The final cost record is a H100 wall-time rate estimate of `$4.698582`, with a pre-call safety
  stop at `$4.75` and a hard approval cap of `$5.00`. Modal's workspace summary after the run
  reported metered `$19.34`, credits `-$15.97`, and billed `$0.00`; this is workspace-level
  evidence, not a per-request invoice. The append-only ledger records no measured invoice USD.
  No additional GPU work was started after the safety stop.
- A local adapter, `scripts/phase6_evo2_to_features.py`, created the four-feature raw-score
  development artifact `research/runs/phase7_development_subset_20260921/evo2_raw_score_features.jsonl`
  (SHA-256 `41bb16f3aa65b589690999449992edf9ec607d1042a99ffb4e20b2091c53dd7f`) and summary
  (SHA-256 `b3082e44292cc29bd12cc27cbe9eb6edb0adf9964be1b94ea823c47becbd6882`). Features are
  primary delta, forward delta, reverse delta, and absolute orientation disagreement. Labels
  were attached locally after verified raw-score output; none were sent to Modal.
- The real-subset local CPU continuation completed Phase 8 baselines, Phase 9 bounded logistic
  HPO, a fixed 50/50 Phase 11/12 logistic+MLP validation analysis, and the feasible Phase 13
  subset matrix. Evidence hashes are: Phase 8 summary
  `99d1bbd34df34643ffd68eaf8356b6b83763288798efb6b99200da0bd0706c1a`, Phase 9 metadata
  `3d6095554c5744bfe989821f162ab735827d977627436bccf0f376040629393e`, Phase 11/12 analysis
  `6e452d6f9730529e9b3196cd62f2327b5a554976a86e66c023ebdcf07d91e036`, and Phase 13 matrix
  `df5d82ffb6878bc5c875a10fabf846c1ad93935ee689766d04d68af24d073c57`. All are
  `locked_test_evaluated=false` and `selection_split=VALIDATION`.
- The subset-only validation AUROCs were logistic `0.9931128641`, stump `0.9376820388`, MLP
  `0.9930825243`; HPO's best validation-only trial was learning rate `0.05`, `100` steps,
  `l2=0.0`, AUROC `0.9932342233`; and the fixed 50/50 logistic+MLP analysis reported AUROC
  `0.9930976942` and ECE `0.0843577465`. These are preliminary subset diagnostics, not
  confirmatory or full-cohort claims. Phase 13 completed forward/reverse/aggregate feature
  cells and learning curves; center-shift, embedding, comparator, and fitted-calibrator cells
  remain explicitly not run.
- Gate decision: the current exact-scope continuation is `PARTIAL`, not a full Phase 6/7 pass.
  Phase 14 and the locked test remain untouched. The full development cohort, NT/Caduceus
  extraction, comparator joins, fine-tuning, registry promotion, figures, release, deployment,
  and publication remain unresolved and require a new explicit scope/budget if pursued.

## Current preliminary registry and UI reconciliation — 2026-09-21

- `scripts/register_development_subset_results.py` generated five tracked subset summaries and
  fourteen tracked figure-source artifacts, then registered seven completed runs as
  `PRELIMINARY`. `make registry-verify` passed; no `FINAL` record was created and no locked-test
  row was consumed.
- Phase 16 is now `PARTIAL / PRELIMINARY REGISTRY CONNECTED`: the read-only workbench registry
  route sees seven completed scientific-stage records and the UI status artifact reports
  `registry_connected=true`. `make web-check` passed and all four committed Playwright journeys
  passed, including the preliminary-registry journey.
- Phase 17 remains `BLOCKED / PARTIAL SOURCES`: its manifest reports 9/19 available figure
  families and 9/12 available tables, with real subset provenance. The missing source list is
  `benchmark.json`, `context_length.json`, `cost_ledger.jsonl`, `embedding_layer.json`,
  `error_correlation.json`, `finetuning.json`, `hpo_importance.json`, `loss.json`,
  `subgroup.json`, and `temporal_cohort.json`; the bundle output count is zero by design while
  any required source is absent.
- Phases 14, 15, 18, and 19 remain blocked for their independent dependencies. In particular,
  the current `$5.00` approval does not authorize locked evaluation, full scientific clean-room
  reproduction, deployment, release, or publication.

## Current train-only calibration continuation — 2026-09-21

- Phase 12 now has a real preliminary train-only calibration comparison. Platt and isotonic
  maps were fit on TRAIN and evaluated on VALIDATION for the fixed 50/50 logistic+MLP ensemble;
  the locked-test boundary remained false throughout. The tracked summary is
  `artifacts/registry/development_subset_20260921/phase12_calibration_development_subset_20260921.json`.
- Phase 13 now has a separate calibration-effect summary at
  `artifacts/registry/development_subset_20260921/phase13_calibration_effect_20260921.json`.
  It completes the feasible subset calibration-effect cell but does not make the original
  predeclared full matrix complete; context shifts, embeddings, external comparators, and
  full-cohort robustness remain deferred.
- The current registry has nine eligible completed `PRELIMINARY` runs. The figure manifest stays
  `BLOCKED` with 9/19 figures and 9/12 tables available because the missing source families are
genuine unavailable evidence, not values to infer.

## Current local Phase 15/16/17 continuation — 2026-09-21

- Implementation commit `6196dc5` adds the free local Phase 15 boundary. `scripts/plan_batch.py`
  parses the tracked label-free sample `examples/batch/variants.csv`, enforces the GRCh38 SNV
  contract, records input SHA-256 `d0778b9ad572f7aa6d9b48f0d6675b1e8bd29180826ba0834aa64eff799f7378`,
  and writes a deterministic `PLANNED` one-shard plan for the pinned Evo2 revision
  `4b509ec2a22d6de472659f908bcb0714265ad3a7`. No scorer, Modal call, model download, label, or
  scientific result was produced by the planner.
- The injected local executor/exporter is covered by 17 targeted tests. It reuses completed
  shards only after payload-hash, exact ordered-ID, row-shape, and label-free validation;
  persists failure taxonomy; requires explicit retry; and rejects tampered, duplicate,
  out-of-order, malformed, or unexpected shard files. This is an engineering contract, not
  remote batch-parity evidence. Phase 15 remains `BLOCKED` overall until a new exact-scope
  approval authorizes remote parity and kill/restart smoke.
- Phase 16's API/UI now reports `PARTIAL` for 9 completed scientific-stage `PRELIMINARY` runs
  and 0 `FINAL` runs. `make ui-check`, `make web-check`, and `make web-e2e` pass; metadata is
  exposed without promoting preliminary metrics.
- Phase 17's final renderer remains `BLOCKED` with zero final outputs and the ten missing source
  families. The separate preliminary manifest has SHA-256
  `026a82c02e1151d9bade98744bbd07c11d4c1e2ca7630b4b8ec3fda744cc9d40`, `status: PARTIAL`,
  `evidence_stage: PRELIMINARY`, `promotable: false`, 9 figures, 9 tables, and 18 outputs. This
  bundle is useful for engineering review only and cannot satisfy the final Phase 17 gate.
- No paid work was started in this continuation. The existing `$5.00` development approval is
  exhausted at its recorded safety stop and does not authorize full-cohort inference,
  comparators/embeddings, locked evaluation, fine-tuning, remote batch, deployment, release, or
  publication.

## Final no-spend gate refresh — 2026-09-21

- `make validate` passed 700 tests with 33 deselected and 95.01% coverage; strict mypy, Ruff, and
  secret scan passed. ML protocol, schema, model-registry, and experiment-registry verification
  passed. Scientific tests passed 7 with 1 skip, and API/E2E tests passed 14 with 1 skip.
- The frontend gate passed `make web-check`, and `make web-e2e` passed all four browser journeys.
  The registry UI remains `PARTIAL` for nine preliminary runs with no final run. The final Phase
  17 renderer remains `BLOCKED` with zero outputs; the separate preliminary renderer remains
  `PARTIAL` and non-promotable with 18 outputs.
- The safe status surfaces for Phases 14, 18, and 19 each recorded `BLOCKED`. The Phase 6/7
  runner default printed help without a network request. Modal preflight was authenticated but
  recorded `gpu_count: 0`, `status: PLANNED`, and no remote invocation. These are no-spend
  control-plane results and do not change any scientific phase to PASS.

## Modal preflight layer-isolation checkpoint — 2026-09-21

- Evidence commit: `e589efb5443713c864004472b1c3457a437d803a`, with `make validate` PASS
  (703 passed, 33 deselected, strict mypy/Ruff/secret scan, 95.02% coverage) and clean
  `git diff --check` before commit. The failed sample and preflight gate are preserved as
  tracked artifacts; the two prior failed app IDs are not deleted.
- Formal app evidence is intentionally split. `ap-3nvzpB5VADtBwNaoF5aOmA` and
  `ap-2yoBkvnIItyhk0pULH36CA` both recorded client-side `StreamTerminatedError: Connection
  lost` after image construction with zero accepted rows and no server-side worker score log.
  `ap-TjBjZwIceAIK4Q6U8Y9B4l` was already running when the latest checkpoint arrived; it
  reached an H100/NVIDIA PyTorch container and Evo2 initialization, but was deliberately
  interrupted and is not a formal PASS.
- Diagnostic-only approval
  `artifacts/approvals/modal_transport_diagnostic_20260921.json` authorizes at most `$0.50`
  additional Modal compute, with a `$0.45` safety stop, and excludes formal 64-row retry,
  full-cohort work, NT/Caduceus, training, HPO, fine-tuning, locked evaluation, and Phase 14.
- CPU transport isolation PASSed: four deterministic `spawn/get` calls in
  `ap-23bynwYzoxKGO8TmPHVD9l` returned exact doubles, and detached submission/retrieval in
  `ap-wsZoBWHGk1jN57Td2HXlIM` returned the expected value after independent
  `FunctionCall.from_id(...).get()` retrieval. Both apps were stopped and no active container
  remained.
- The minimal H100 layer then allocated `ap-YYNj6l8iIR9IGJORSrPCrF` / container
  `ta-01M32DEAE8JMWAN7QDNZJHR4MR`, but failed before the CUDA probe at
  `ModuleNotFoundError: No module named 'torch'`. This is a diagnostic image/client dependency
  failure; it does not establish H100 unavailability. Per the checkpoint, no `hf_cache` read,
  new Evo2 initialization, one-record check, or eight-record check followed.
- Current Phase 6 gate remains `FAIL_FORMAL_PREFLIGHT`, not PASS. The full formal run and all
  dependent GPU/downstream phases remain blocked. The durable report is
  `artifacts/modal_diagnostics/formal_preflight_failure_analysis_20260921.json`; its sole
  recommendation is `CLIENT_FIX_REQUIRED` before any new H100-layer diagnostic or formal retry.

## Independent local gate refresh after the Modal diagnostic stop — 2026-09-21

- `make data-qc` PASSed with deterministic regeneration, zero normalized-ID overlap, zero
  TRAIN/VALIDATION gene overlap, zero locked-test overlap, 239,992 development rows, and split
  hash `bac30ed0a818258445a7340b1e96fe592902af5d4d7e899fbe227d24af955722`.
- `make phase3-audit` PASSed all current source, temporal, deterministic, schema/hash, SNV,
  and leakage gates. `make phase3-reference-audit` independently PASSed all 946 authoritative
  temporal records against GRCh38; the refreshed evidence is
  `artifacts/reference/grch38_validation_20260921.json`.
- Protocol, ML-control-plane, schema, model-registry, experiment-registry, scientific-test,
  frontend-build, and browser E2E gates pass. The browser tier is 4/4; the scientific tier is
  7 passed with 1 documented skip. Phase 16 remains `PARTIAL` because its nine registered runs
  are preliminary and no final run exists.
- The minimal H100 diagnostic script now installs the same pinned PyTorch version used by the
  qualified formal image. This correction is locally linted/typechecked/compiled only; the
  original remote H100 failure remains the authoritative diagnostic outcome until a fresh
  continuation authorizes verification. Phase 6 remains `FAIL_FORMAL_PREFLIGHT`.
- Phase 17 final figures, Phase 18 clean-room reproduction, and Phase 19 release remain
  `BLOCKED` for their documented missing scientific/final evidence. No status is promoted from
  code presence or preliminary data alone.
- The current no-spend phase-status refresh returns `BLOCKED` for Phases 6/7/8/9/11/12/13/14/15,
  `DEFERRED_BY_COMPUTE` for Phase 10, `PARTIAL` for Phase 16, and `BLOCKED` for Phases 17/18/19.
  `make modal-smoke` authenticates successfully but records `gpu_count: 0`, `PLANNED`, and no
  remote invocation.

## Corrected H100 diagnostic retry checkpoint — 2026-09-21

- The fresh diagnostic approval is bound to execution HEAD `14d8a98`, the frozen protocol and
  ML-DEV-BUDGETED-001 manifest hashes, Modal workspace `utkarshmer05` / environment `main`, and
  a `$0.50` hard cap with a `$0.45` safety stop. The formal 64-row retry remains excluded.
- The corrected H100 diagnostic allocated `ap-ST5uHP1cHmdblqU4CIAncx` / container
  `ta-01M32FFXEKXGSTP7SHMPF1KNTR`; logs show NVIDIA PyTorch 24.07 and PyTorch
  `2.4.0a0+3bcc3cd`. H100 scheduling, startup, and remote PyTorch import therefore PASS.
- The local detached client failed at result deserialization with
  `DeserializationError: Deserialization failed because the 'torch' module is not available in
  the local environment.` The CUDA result was not accepted, so the ladder stopped before
  `hf_cache`, Evo2, one-row, or eight-row diagnostics. Evidence is in
  `artifacts/modal_diagnostics/h100_dependency_retry_analysis_20260921.json`.
- A plain-builtins serialization fix was committed at `e8ae239` and validated by `make validate`
  (`704 passed, 33 deselected`, 95.02% coverage). No rerun followed because the approval remains
  bound to `14d8a98`; a fresh approval is required for any retry. The single continuation state is
  `PYTORCH_IMAGE_FIX_REQUIRED` (the concrete issue is client result serialization, not H100
  scheduling). Phase 6 remains `FAIL_FORMAL_PREFLIGHT` and no downstream status is promoted.

## Independent post-diagnostic gate refresh — 2026-09-21

- `make web-check` passed lint, TypeScript, and production build; `make web-e2e` passed all four
  browser journeys. Known Next tracing and package-lock warnings remain non-failing.
- Registry verification and model-registry verification passed. The registry remains connected
  but preliminary: 9 completed scientific-stage runs, 0 locked-test runs, and 7 model manifests
  with only Evo2 included.
- The final figure manifest remains `BLOCKED` with zero outputs and missing registered source
  families; the separate preliminary bundle remains `PARTIAL`, non-promotable, with 18 outputs.
  Clean-room and release status surfaces remain `BLOCKED`.
- Status-only refreshes preserve `BLOCKED` for Phases 6/7/8/9/11/12/13/14/15/18/19,
  `DEFERRED_BY_COMPUTE` for Phase 10, and `PARTIAL` for Phase 16. `make modal-smoke` passed
  authentication with `gpu_count: 0`, `PLANNED`, and no remote invocation. No scientific phase
  gate was promoted.

## Fresh JSON-safe H100 diagnostic ladder — 2026-09-21

- Fresh approval: `artifacts/approvals/modal_h100_jsonsafe_retry_20260921.json`, bound to
  `cc035d1d2f49d42c3770fd4e9c9dc94587f5465e`, `$0.50` hard cap, `$0.45` safety stop. Formal
  64-row work, full 4,000-row work, NT/Caduceus full extraction, HPO, fine-tuning, locked-test
  access, Phase 14, deployment, and release remain excluded.
- Diagnostic sequence completed without a new failure: JSON-safe H100 `PASS`; read-only
  `hf_cache` `PASS`; canonical Evo2 load `PASS`; one-row non-locked development score `PASS`;
  eight-row non-locked development shard `PASS`; eight-row persistence/resume `PASS`.
- H100 evidence: app `ap-6saybhZYlnXAf2CmB98tXP`, function
  `fu-5lcgqs4HgSSP6xGP1I2rRX`, call `fc-01M32GDY0FPCXSECVK2PJQY5B9`, container
  `ta-01M32GDYA6FBAKDZ2AZ0XGHXNR`; PyTorch `2.4.0+cu124`, CUDA `12.4`, H100, capability
  `[9, 0]`, numeric result `2.0`, local and detached retrieval `PASS`.
- Cache and model evidence: cache app `ap-5orUJFT7c3T0Zb6HE1U4gN`, call
  `fc-01M32GMEMTMNFKJ60M6PW1918T`; load app `ap-Th4trAg5I1lyS9edw0SzqG`, function
  `fu-neSkt1w16XgFvZQFEm2y3K`, call `fc-01M32GRHKA7ZASBDXEF9NB7B53`, container
  `ta-01M32GRJ09E2YHWRF2FJ5XMGWR`. The canonical `evo2_7b` revision loaded with a cache hit;
  no weight download or cache mutation occurred.
- Development evidence: one-row app `ap-5pbxOL6rhdzLf87jqec6T4`, call
  `fc-01M32H51FXH9JAPH3HR1G68PB2`, container `ta-01M32H51SKQF90YB22H7X4H8KR`; eight-row
  app `ap-vQWe7aKZhMWkzrSWKoguGx`, call `fc-01M32H843J01JNSS35BF850741`, container
  `ta-01M32H84C5F1D61PR30QD7HR5R`. Both batches sent no labels, used only TRAIN/VALIDATION,
  used GRCh38/8192-bp forward+reverse-complement inputs, returned finite scores, and matched the
  exact model revision. The eight-row shard resume read the persisted hash and made zero remote
  calls.
- Consolidated evidence: `artifacts/modal_diagnostics/h100_jsonsafe_retry_20260921.json`.
  Estimated additional H100 wall-rate cost is `$0.208895`, below both stops; workspace meter
  was `19.61` at baseline, `19.88` in the ladder artifact, and `19.94` at the final read-only
  inventory check, with `$0.00` billed. This is not a per-run invoice. All apps and containers
  are stopped.
- Phase 6 ledger disposition: `FAIL_FORMAL_PREFLIGHT` remains until a separately approved formal
  64-row preflight actually runs and passes. This diagnostic ladder only resolves the H100/client
  readiness boundary and establishes the single recommendation `RETRY_FORMAL_64_PREFLIGHT`; it
  does not itself promote a formal gate or unblock dependent phases. Phases 7/8/9/11/12/13/14/
  15/18/19 remain `BLOCKED`, Phase 10 remains `DEFERRED_BY_COMPUTE`, and Phase 16 remains
  `PARTIAL`.

## Formal preflight provenance reconciliation — 2026-09-21

- Commit `e0e43bf0cbc702db38fbd5a274e574c89e2ad24a` preserves the successful JSON-safe
  diagnostic ladder and its historical failure artifacts. `make validate` and `git diff --check`
  pass; the only untracked path is the pre-existing `.agents/` tree.
- Provenance is `PASS`: source/code revision `4b509ec2a22d6de472659f908bcb0714265ad3a7` belongs
  to the official Arc Institute Evo2 repository, while model snapshot revision
  `bda0089f92582d5baabf0f22d9fc85f3588f6b58` belongs to the separate Hugging Face
  `arcinstitute/evo2_7b` repository. The differing identifiers are expected because one names
  executable source and the other names model-repository contents.
- The mounted cache contains `evo2_7b.pt` (13,766,621,200 bytes; blob identifier
  `c66645929dc1b9c631f5be656da8726f38946315dc9167000a615dd626fcecf4`) and a readable config.
  The blob identifier is not represented as a recomputed content hash. The cache-hit load and
  successful development score artifacts confirm the same canonical `evo2_7b` / H100 / bfloat16 /
  GRCh38 / 8192-bp / forward+reverse / alternate-minus-reference contract.
- Evidence artifact: `artifacts/modal_diagnostics/evo2_provenance_reconciliation_20260921.json`.
  The formal 64-row preflight has not started and needs its separate `$0.75` / `$0.65` approval.

## Formal 64-row preflight — 2026-09-21

- The exact-scope approval was validated at execution HEAD
  `dae42a265f64601af91e209dfcd3c9e5c963ecd2`, with `$0.75` hard and `$0.65` safety limits.
  Its scope excluded the full 4,000-row run, NT/Caduceus extraction, locked test, Phase 14,
  fine-tuning, context sweeps, deployment, and release.
- Row-level sample gate: `PASS_FORMAL_SAMPLE`. The 64 rows were selected label-blind from the
  frozen formal development manifest using the frozen SHA256 ID-plus-seed ranking. Coverage was
  TRAIN 46, VALIDATION 18, 21 chromosomes, and 58 unique genes. All 64 canonical scores were
  finite and complete; reference mismatches, unexpected IDs, duplicates, locked rows, and remote
  labels were all zero/false.
- Durable execution evidence: app `ap-BJUiZPDuBbdkxaEsbPougn`, function
  `fu-eIxtQurXxHVYM46hfWauMo`, container `ta-01M32K7GE601S233HNHWQQ30DR`, and calls
  `fc-01M32K7G6760X0W60KQGVJV94A` / `fc-01M32K9XNR6CT9100REY2KQMCH`. The resume app
  `ap-YTtOeacENcg8Cz5M0jBHys` reused both shards with zero remote invocations.
- Formal projection gate: `FAIL_FORMAL_PREFLIGHT`. Measured preflight estimate `$0.135088` was
  below the `$0.65` preflight safety stop, but measured-rate scaling projected Evo2 at `$8.593340`
  and formal Phase 6/7 at `$9.198277`, above the intended `$7.75` safety stop and `$8.00` plan.
  Evidence is in `artifacts/phase6/formal_budgeted_preflight_gate_20260921_formal64_jsonsafe_retry.json`
  and `artifacts/modal_diagnostics/formal_64_preflight_modal_evidence_20260921.json`.
- Gate recommendation is exactly `FORMAL_PREFLIGHT_FIX_REQUIRED`. No full formal run or dependent
  GPU phase was launched; Phases 7/8/9/11/12/13/14/15/18/19 remain blocked, Phase 10 remains
  `DEFERRED_BY_COMPUTE`, and Phase 16 remains partial.

## Phase 7 formal NT/Caduceus representation checkpoint — 2026-09-22

- The narrow approval was validated against committed HEAD `71a7c2d16148aecb99037f70439a57243153f6ca`
  with a `$1.00` hard cap, `$0.85` safety stop, and `$3.00` minimum post-run reserve. Scope was
  limited to the exact 4,000-row TRAIN/VALIDATION NT/Caduceus representation matrix; Evo2 reruns,
  locked-test inference, fine-tuning, Phase 14, deployment, and release were excluded.
- The run is `PARTIAL / ALLOCATION BLOCKED`, not PASS. Verified NT coverage is 2,432/4,000:
  504 rows in the original 63-shard cache and 1,928 rows in the 31-shard optimized cache. The
  optimized runner used 64-row shards and 4-row model batches and did not recompute the first 504
  rows. NT remaining is 1,568 rows; Caduceus coverage is 0/4,000.
- The final no-spend audit found zero duplicates, zero unexpected IDs, zero locked overlap, no
  remote labels, finite packed layer features, and exact local reference construction matches for
  all 2,432 persisted rows. There are no pending calls and no active Modal containers.
- The durable partial evidence is
  `artifacts/phase7/formal_budgeted_representation_20260922_partial.json`. The cumulative
  completed client wall-rate estimate is `$0.704889`; the safety gate stopped before the remaining
  workload could be proven within the authorization. A fresh future allocation must reuse both
  caches and bind a new approval to the then-current HEAD.

## Phase 14 locked Evo2 closeout and downstream no-spend continuation — 2026-09-22

- The exact Phase 14 approval was validated against execution HEAD
  `c6c431869724666c84252cbd43979f2c4f38875f`, with a `$2.75` hard cap and `$2.50` safety stop.
  Frozen protocol, manifest, materialized-config, fitted-model, calibration, model-revision,
  and locked-cohort bindings all passed. The approval SHA-256 is
  `4b619747a73942e56e15fef4040db1591760ee5a7813fb8f14fcc4740050dae7`.
- The authorized workload completed exactly `946/946` locked Evo2 rows using 30 shards and 30
  H100 calls. It scored 946 new rows in the paid pass, reused zero rows before that pass, and
  required zero transient retries. The remote runtime was `1,304.297864` seconds and the direct
  H100 runtime estimate at `$3.95/hour` was `$1.431104601`. A later local cache-only resume reused
  all 30 verified shards and made zero additional remote calls.
- The final artifact is
  `artifacts/phase14/phase14_locked_evo2_20260922.json` (SHA-256
  `4dd9b9229c47d65491345e87b70a6f6739432c24a7585966f4aea97a9d115499`). Raw predictions were
  hashed before the local label join: raw SHA-256
  `ae288252a3f1bfc8a1754b1626ea6ff91a041df9ff09daf07d1411a242ba2508`; joined SHA-256
  `77cbbb48032ac7852ff09f93ea448d1e98ca21457843c1feda16f31e8dc530e7`. All positive integrity
  gates passed: exact IDs, finite forward/RC/aggregate/calibrated scores, no labels transported,
  no duplicate IDs, no unexpected IDs, no reference mismatches, no locked labels before raw hash,
  one-shot selection closure, and no post-test tuning.
- The initial paid-run billing snapshot was metered `$31.82187443` and billed `$0.00`; the final
  fresh read-only snapshot at `2026-09-22T11:30:41.805291+00:00` was metered `$33.50187443` and
  billed `$0.13`. Modal's `credits: -30.00000000` is a billing adjustment, not a provider-returned
  free-credit balance. The user-stated pre-run free-compute headroom was `$7.17`; subtracting the
  observed metered delta of `$1.68` gives an indicative `$5.49`, not a provider-confirmed balance.
  The final container inventory was `[]`.
- Phase 15 local batch/kill-restart evidence remains available, but its overall gate is `BLOCKED`
  because remote batch parity and full-cohort batch authorization are absent. Phase 16 is `PARTIAL`
  with 12 connected runs, including the Phase 14 `FINAL` record. The no-spend Phase 17 rerun
  remains `BLOCKED` with 15 available figures and three missing mandatory source families
  (`context_length.json`, `loss.json`, `temporal_cohort.json`). Phase 18 remains `BLOCKED` for full scientific Modal clean-room reproduction;
  Phase 19 remains `BLOCKED` for the unresolved scientific, figure, and release gates.
- No NT, Caduceus, fine-tuning, new HPO, deployment, release, or additional paid work was started
  under this authorization. The initial finalization attempts failed closed on impossible boolean
  gate predicates; the predicates were corrected, and the already-completed raw shards were
  finalized without recomputation.
