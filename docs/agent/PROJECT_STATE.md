# Project State — EvoVariant-TR ML Extension

## Current state — 2026-09-21

Repository: `https://github.com/UtkarsHMer05/EvoVariant-TR-`

Current phase: `PHASE 6 CONTINUATION PREPARED / FULL PHASE 6 BLOCKED PENDING CURRENT APPROVAL`
(Phases 0-5 required gates and the separately approved Phase6A cache/comparator/throughput
qualification are complete; no full Phase 6 inference has started.)

Phase status: `BLOCKED / PARTIAL` at the final release gate. The repository retains the
schema-validated control plane, fail-closed model registry/adapters, deterministic CPU-only
contracts for later experiment families, evidence-gated workbench, and passing local Python/
frontend build gates. A real authorized Evo2 7B H100 pilot now passes the Phase 2 raw-score
contract and the Phase 4 persistent cache miss/hit gate; the model weights are cached only in the
approved Modal `hf_cache` volume and no weights are tracked in Git. The Phase 3 audit and
independent reference report now both pass after the ML-only deviations; the historical target
identity set remains unavailable and is retained only as validation-only comparison evidence.
The authoritative extension cohort is 946 records (536 B/LB, 410 P/LP), with 0 reference
mismatches and deterministic regeneration PASS. Phase 5 has a final separated roster: Evo2 raw
score, Nucleotide Transformer/Caduceus embedding tracks, CADD/PhyloP public CPU comparators,
deferred GPN, and subset-only AlphaMissense. Phase6A qualified those CPU comparators, measured
bounded Evo2 H100 throughput, recorded an A100 FP8-compatibility failure, and measured tiny
unlabeled NT/Caduceus embedding throughput. Full Phase 6, full Phase 7 extraction, training,
HPO, fine-tuning, locked-test evaluation, clinical classification, and release remain blocked or
not started. Phase 10 adaptation remains `DEFERRED_BY_COMPUTE` with no training run or scientific
metrics. No full benchmark or feature cache has been created.

Latest validated source baseline: `36063e8e1b65ddf1653347a5705e89115e52f1d5` (final Phase 3
freeze-summary/control baseline; current `make validate` and control-plane gates pass).
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
The frontend dependency/lint hardening was validated and committed in `739310d`; the current
checkout HEAD is `f2a6f53f505d9b4b8466d903404c199a073bfead` before this continuation audit commit.

Active branch/worktree: `research/evovariant-tr` at
`/Users/utkarshkhajuria/Desktop/EvoVariant`

## Authoritative recovery and pre-Phase-6 checkpoint — 2026-09-21

- The complete recovery search is recorded in
  `artifacts/phase3_recovery_search_20260921.json`. It searched the repository's 133 reachable
  commits, 95 reflog entries, 91 reflog commits, 6 refs, deleted paths, unreachable objects,
  fetched remote history, artifacts, generated files, presentations, scripts, logs, local
  worktrees, and supplied attachments. No frozen normalized-ID/source-row manifest for the
  historical target was recovered.
- `ML-DEV-001` formally accepts the current manifest-verified deterministic cohort for the
  ML extension only: 1,402,895 t0 VUS, 946 final temporal records, 536 B/LB, 410 P/LP, and 946
  gene labels. The historical 1,024-record target remains validation-only; the original frozen
  zero-shot protocol was not rewritten.
- `ML-DEV-002` freezes the Broad GATK hg38/v0 reference. The FASTA SHA-256 is
  `93157a161863464c9435062fd67c173fdaf99cb8b32f1455018361387ffa5564`, the FAI SHA-256 is
  `edefd93c489dc1baefad312f40388089f8db5cf6dcc3ba0955669ead274e8b6b`, and the source metadata
  is in `data/manifests/grch38.json`. The large FASTA/FAI remain outside Git.
- Phase 3 is `PASS`: `artifacts/phase3_integrity_audit_20260921.json` and
  `artifacts/reference/grch38_validation_20260921.json` both pass; the independent audit
  checked all 946 authoritative records with zero mismatches and zero missing coordinates. The
  authoritative locked-test manifest SHA-256 is
  `9f9e052d21f4a6a32f595cb20f48cb81e033c0481942820d04f9b67d410a16cb`; its record-set hash is
  `ae4f6f1c1ad7c8d9ea78a9e5ce0380b1d8862a125592be5474b7826de165a6a0`. The authoritative cohort
  manifest SHA-256 is `0d4386b34196a523ca43b50cc4242d4ecb01df2b40923fc0aa52f15d61c593b1`, and the
  restored Phase 3 summary SHA-256 is
  `654c74151302e4ad5d7d9e89403e3dfb4917d19c4c7491e31403230b3888b420`.
- Phase 5 is complete for its final roster only, recorded in
  `artifacts/model_audit/phase5_final_roster_20260921.json`: Evo2 is `INCLUDED_RAW_SCORE`,
  Nucleotide Transformer/Caduceus are `INCLUDED_EMBEDDING_TRACK`, GPN is `DEFERRED`, CADD and
  PhyloP are public CPU-comparator `INCLUDED_RAW_SCORE` tracks, and AlphaMissense is
  `SUBSET_ONLY`. No masked-LM logits were promoted to raw allele scores.
- The final checkpoint is `artifacts/phase5_final_checkpoint_20260921.json`. It records the
  946-record Phase 6 cost scenarios, model-by-model Phase 7 cost status, and the current
  read-only Modal snapshot: `$12.19` metered, `$0.00` billed. No full Phase 6/7 run, training,
  HPO, fine-tuning, or locked-test evaluation was launched.

## Historical priority continuation before recovery — 2026-09-21

- The user-prioritized Phase 3 diagnostic and machine-readable integrity report are
  `artifacts/phase3_integrity_diagnostic_20260921.json` and
  `artifacts/phase3_integrity_audit_20260921.json` (audit SHA-256
  `ffce3a86eed002822d6501a2d0d95ecf59bf73d2a646ae22398c517a772f9fa5`). The exact failing
  gates are `handoff_target_identity_reconciliation = BLOCKED_MISSING_TARGET_ID_SET` and
  `independent_grch38_reference_base = NOT_RUN`; the first is missing target-side identity/source
  evidence and the second is missing `data/reference/Homo_sapiens_assembly38.fasta(.fai)`.
- Current archive-derived accounting is 1,402,895 unique t0 VUS, 946 final temporal records
  (536 BLB, 410 PLP), 3,459 absent at t1, 9,049 definitive outcomes below the two-star gate,
  and 1,389,441 not definitive at t1. The validation-only target differs by -330 t0 IDs and
  -78 final records, all -78 in BLB; PLP matches. The current cohort's internal temporal
  partition sums exactly, so no target count was forced and no synthetic IDs were added.
- The integrity audit found zero duplicate normalized IDs, zero conflicting duplicate IDs, zero
  cross-split normalized-ID overlap, zero train/validation gene overlap, zero locked-test overlap,
  zero future-than-release dates, zero t0/t1 reference/alternate identity mismatches, and PASS
  deterministic regeneration with the locked-ID, split-manifest, and temporal-audit hashes
  reproduced twice. Independent FASTA base validation is explicitly `NOT_RUN`, not inferred from
  these identity checks.
- Full local validation after the Phase 3 audit passed: secret scan, Ruff, strict mypy over 52
  source files, 656 default-tier tests with 33 deselected, and 95.14% total coverage. The new
  `make phase3-audit` command reran both large source archives and two fresh deterministic builds;
  it completed with all local gates PASS and the two external blockers above.
- Phase 5 now has a real smoke artifact at
  `artifacts/model_audit/phase5_real_smokes_20260921.json` and a roster-resolution artifact at
  `artifacts/model_audit/phase5_multi_model_smoke_resolution_20260921.json`. Nucleotide
  Transformer v2 (pinned revision `06615c...`, 498,345,436 parameters) and Caduceus-Ph (pinned
  revision `b047752...`, 7,725,312 parameters) both loaded on H100, produced finite logits and
  hidden states, and produced finite synthetic ref/alt embedding deltas. They are recorded as
  `SUBSET_ONLY`, not raw-score benchmark models, because the smoke input is synthetic and neither
  official checkpoint has the frozen GRCh38 alternate-minus-reference contract.
- GPN remains `DEFERRED_BY_COMPUTE` because its matching 100-way alignment asset is approximately
  42 GB and absent; CADD remains `DEFERRED_BY_COMPUTE` because its GRCh38 annotation bundle is
  approximately 300 GB and license/checksum evidence is incomplete; PhyloP and AlphaMissense
  remain `DEFERRED_BY_COMPATIBILITY` for score/subset reasons. The model manifests and schema now
  preserve these explicit status values; only Evo2 is `INCLUDED` for a raw Phase 6 score.
- The checkpoint summary required before any large benchmark is
  `artifacts/phase5_checkpoint_20260921.json`. It records the current dataset/hashes, model
  roster, estimated Phase 6 cost ($55,835.221 sequential wall-rate or an unmeasured $6,979.403
  perfect-eight-way scenario for one model), and `UNMEASURED` Phase 7/10 estimates. No large
  benchmark, embedding extraction, training, HPO, or locked-test run is authorized.
- The Phase 5 smoke runner's H100 wall-rate estimate was `$0.0152`; the read-only workspace
  billing snapshot after the smoke was metered `$12.21122616`, billed `$0.00`. This is
  workspace-level evidence, not a per-request invoice. The approved `hf_cache` volume contains
  checkpoint caches; no model weights or scientific outputs were written to Git.
- Phase 3 and Phase 5 therefore remain the only active upstream work. Phase 6 and all downstream
  phases must not advance until the external Phase 3 gates are cleared and a compatible raw-score
  comparison protocol is explicitly frozen.

## Current authoritative execution update — 2026-09-21

- The current source baseline `1bf1029` passes `make validate`: secret scan, Ruff, strict mypy
  over 52 source files, 656 default-tier tests with 33 deselected, and a 95.14% coverage floor.
  The current checkout also re-passes `make web-check` and all four `make web-e2e` workbench
  journeys. These are local validation results; they do not create remote scientific outputs.
- Commit `696fcd6` closes a fail-closed readiness defect in `Evo2Adapter`: local package/parity
  checks now remain `DEFERRED` until an explicit named remote-smoke evidence checker passes.
  Missing, malformed, incomplete, or failed remote evidence cannot be promoted to `READY`; this
  strengthens the Phase 5 control plane without claiming another remote execution.
- Current checkout verification at this checkpoint: branch `research/evovariant-tr` is at
  `1bf1029`; the only untracked path is the injected `.agents/` skill bundle, intentionally not
  part of project commits or scientific evidence. Verify the exact HEAD with Git before any phase
  transition.
- The remote pilot was deployed from source HEAD `2f4d117d0d1804bd8479d7da473978d1f796249b`.
  The chromosome-normalization fix, model-manifest updates, pilot artifacts, and the reconciled
  control-file updates are now committed in `f69ee8605e3dcbcf068ffd0f5fed3cef6e3cdcb0`
  (`feat: verify bounded Evo2 pilot and model gates`). The current checkout HEAD and dirty state
  remain authoritative; verify them with Git before any further phase transition.
- The user-authorized pilot approval is
  `artifacts/approvals/phase2_4_pilot_20260921.json` with a `$2.00` bounded pilot-family cap.
  Modal billing is recorded as workspace-level evidence only: metered cost moved from `$11.49`
  before remote requests to `$11.82` after the corrected pilot family, billed cost remained
  `$0.00`, and no exact per-request invoice amount is asserted.
- The latest read-only `modal billing summary` after the pilot reports workspace metered cost
  `$11.99` (`$8.78` deployed apps and `$3.21` volumes) and billed cost `$0.00`. The provider's
  negative credits/free-storage fields are not interpreted as a remaining-credit balance, and
  this snapshot does not establish a per-request measured USD amount.
- Superseded failure evidence is preserved in
  `artifacts/modal/phase2_pilot_20260921_failed_attempts.json`. The first deployment loaded
  `evo2_7b` successfully but failed at UCSC chromosome lookup because raw `10` was passed instead
  of `chr10`; a warm retry reproduced the same failure. The app now centralizes chromosome
  normalization and validates `GRCh38`/`hg38` at the remote boundary, with a local regression test.
- Corrected deployment `evovariant-tr` v3, tag `phase2-pilot-20260921-r1`, passed one real
  cache-miss request and one identical cache-hit request for
  `GRCh38:chr10:100065200:C>T`. The miss returned HTTP 200 in `36.2727` wall seconds with
  `3.914133089` H100 runtime, exact `8192`-bp context, forward/reverse raw scores, and
  `cache_hit: false`. The hit returned HTTP 200 in `0.956` seconds with `cache_hit: true` and
  exact numeric equality. The persistent artifact is recorded in
  `artifacts/modal/phase2_phase4_pilot_20260921_success.json` and the append-only cost ledger.
- Phase 2 gate: `PASS` for the local audit plus real remote raw-score pilot. Phase 4 gate: `PASS`
  for cache identity, persistence, equivalent hit, retry/scaledown configuration, telemetry, and
  available cost evidence. Phase 5 now has two real `SUBSET_ONLY` smoke tracks in addition to
  included Evo2; see `artifacts/model_audit/phase5_multi_model_smoke_resolution_20260921.json`.
- Phase 3 impact decision: `MATERIAL_UNCERTAINTY`; see
  `artifacts/phase3_discrepancy_impact_20260921.json`. Current archive-derived outputs remain
  unchanged apart from the audit-counter semantics correction recorded in
  `artifacts/phase3_partition_audit_20260921.json`: `below_two_stars` now means definitive
  outcomes below the star gate, while `not_definitive_at_t1` includes non-definitive outcomes at
  either star level. The corrected current counts are 9,049 and 1,389,441; no benchmark output
  is authorized until the remaining 330-ID discrepancy is reconciled or a dated protocol
  deviation accepts the changed cohort.
- An independent cross-check through the existing `iter_variant_summary`/`VariantIdentity` path
  yields 1,402,906 unique t0 VUS, only 11 above the ML-extension path and still 319 below the
  handoff target. The official archive directory exposes the same recorded t0 file; no alternate
  target archive or target ID list was found in the repository or supplied handoff attachment.
- A read-only NCBI endpoint check confirms both manifest-verified archive URLs return HTTP 200 with
  the recorded byte lengths and release timestamps, while the corresponding non-archive URLs and
  downloader year-subdirectory fallback URLs return HTTP 404. No alternate official release path
  explains the target discrepancy; the provenance evidence is preserved in
  `artifacts/phase3_source_provenance_check_20260921.json`.
- A read-only t0 filter-sensitivity audit found that exact `Uncertain significance` produces
  1,402,895 unique IDs, all raw labels containing `uncertain` produce 1,403,086, and the target is
  1,403,225. Legacy allele fields are `NA` for these VUS rows, `ClinSigSimple` is numeric `0`/`1`,
  and relaxing assembly/origin/type filters overshoots substantially. No tested field/filter
  combination reproduces the target; evidence is in
  `artifacts/phase3_filter_sensitivity_20260921.json`.
- Commit `c401140` repairs the free `make data-verify` surface without changing the frozen
  protocol or ClinVar source metadata: the verifier now normalizes the repository's legacy
  single-file ClinVar manifests to the generic manifest model. Both manifest-verified raw
  archives pass size/hash verification, and regression coverage preserves the newer multi-entry
  manifest path.
- Commit `601e366` makes `build_phase3_artifacts` verify both raw archives against their manifests
  before reading rows or writing derived artifacts. The archive-backed `make data-qc` rerun passed,
  reproduced the existing split and temporal hashes exactly, and still reports the current cohort
  as 1,402,895 t0 IDs and 946 final records. A tampered-source regression proves the builder fails
  closed before producing Phase 3 outputs.

## Current validation update — 2026-09-21

- A fresh no-spend control-surface rerun passed `make modal-smoke` with Modal installed and
  authenticated, `make test-scientific` (`7 passed, 1 skipped`), `make test-e2e` (`14 passed,
  1 skipped`), and `make web-check`. The web build emitted only the known non-failing dynamic
  registry filesystem and parent-package-lock tracing warnings. `make figures` and
  `make release-check` again returned explicit `BLOCKED` status with zero scientific outputs;
  no GPU invocation or paid work occurred.
- Frontend dependency/lint hardening is committed in `739310d`. The web app now uses Next.js
  `16.3.5`, `eslint-config-next` `16.3.5` with its native flat-config export, direct ESLint
  scripts (the removed Next 16 `next lint` command is no longer used), and PostCSS `8.5.28`.
  The Next 16-generated TypeScript settings are checked in and the explicit Makefile lint step
  remains the build gate.
- The current checkout passes `make web-check` and `make web-e2e`; the latter ran four Playwright
  workbench tests. `npm audit --json` and `npm audit --omit=dev --json` both report zero
  vulnerabilities across the installed dependency graph. Next's build still emits non-failing
  tracing warnings for the intentionally dynamic registry filesystem and the parent-directory
  package-lock discovery; these are recorded warnings, not a scientific or release PASS.
- A fresh clone of `739310d` at `/private/tmp/EvoVariant_cleanroom_latest.thPyN5/repo` passed
  `make bootstrap`, `make frontend-install` (`npm ci`, zero vulnerabilities), `make validate`,
  `make test-scientific`, `make test-e2e`, protocol/control-plane/schema/model-registry/registry
  verification, `make web-check`, and four-test `make web-e2e`. Its `make figures` and
  `make release-check` surfaces correctly remained `BLOCKED` because no eligible scientific
  result artifacts are registered.
- The full-run cost gate now verifies approval freshness against the current frozen ML-extension
  protocol hash. The stale August approval is actively refused with a protocol-hash mismatch;
  the targeted cost-policy suite passes 26 tests, Ruff and strict mypy pass, and no paid command
  was launched. This prevents a structurally valid but scientifically stale approval from
  authorizing future work.
- These results close the frontend security/build/browser gates and the free CPU clean-room
  subgate. They do not change the scientific state: Phase 3's 330-ID discrepancy, Phase 5's
  single included model, absent authorized full-cohort/batch recovery evidence, empty result
  registry, and blocked figure/release gates remain unresolved.
- The current free control-surface rerun passed the explicit scientific tier (`7 passed, 1
  skipped`), API E2E tier (`14 passed, 1 skipped`), ML protocol, JSON Schema, model-registry
  (`7` manifests, `1` included), and result-registry checks. `make modal-smoke` confirmed the
  approved `evovariant-tr` Modal environment and authentication while recording `PLANNED` with
  zero GPU count and no remote invocation. Regenerated Phase 6 and 8–9, 11–19 status surfaces,
  figures, and release checks remain explicitly `BLOCKED` with no metrics or scientific outputs;
  Phase 10 is the separately recorded no-metrics `DEFERRED` status.
- The current frontend rerun also passed `make web-check` (ESLint, TypeScript, and Next production
  build) and `make web-e2e` (4 Playwright journeys). The build emitted only the known non-failing
  dynamic-registry filesystem and parent-package-lock tracing warnings.

## Current engineering follow-up — 2026-09-21

- The local `Evo2Scorer.score_batch` adapter now prepares forward/RC reference and alternate
  sequences for all valid rows and submits them to `Evo2.score_sequences` in configured model-sized
  chunks. A deterministic fake-model regression proves chunking, row-to-score mapping, and raw
  delta arithmetic without importing model weights or spending on Modal.
- `evo2_scorer_app.py` now also contains a bounded source-level `score_batch` endpoint with the
  same canonical raw-score payload, persistent cache identities, input-order preservation, and
  partial-failure reporting. The source helper was checked with a no-spend fake-model smoke; it
  has not been deployed or invoked remotely.
- This is an adapter implementation improvement, not remote batch-parity evidence. The deployed
  canonical Modal app still exposes the verified single-variant endpoint only; the Phase 15 gate
  therefore remains `BLOCKED` until a separately authorized remote batch smoke and recovery test
  are completed after the Phase 3 and model-inclusion gates are resolved.
- The required post-pilot prelaunch estimate is tracked in
  `artifacts/modal/phase6_preflight_cost_estimate_20260921.json`: the observed single-variant
  wall-rate bound is about `$55,835.221` for the current 1,402,895-variant t0 cohort, or about
  `$6,979.403` under an explicitly unmeasured perfect 8x batch-throughput scenario. No Phase 6
  launch is authorized by this estimate.
- The local Phase 15 job manifest now persists its computed `total_shards` denominator and rejects
  non-positive variant/shard/batch/rank sizes before work is queued. This closes a resume-progress
  accounting bug in the free local contract; it does not establish remote batch parity or authorize
  a paid run.
- The explicitly unlocked local recovery simulation
  `EVOVARIANT_TR_PAID_COMPUTE_ACK=I_ACCEPT_COSTS ./.venv/bin/pytest --run-modal -m modal tests/modal -rs`
  passed 9 tests with one documented placeholder skip. It exercises deterministic sharding,
  persisted completed/failed shard state, restart progress, retry classification, and shard-result
  round trips without importing a GPU model or invoking Modal. This strengthens the local recovery
  contract only; the real remote batch kill/restart gate remains blocked.
- `evo2_scorer_app.py` now contains a bounded source-level embedding endpoint using the fixed
  Evo2 `blocks.28.mlp.l3` layer and mean-token pooling for forward and reverse-complement
  reference/alternate sequences. It records vector shapes, dtypes, hashes, provenance, and a
  separate content-addressed feature-cache identity. Commit `2c9b3ca` adds
  `feature_record_from_embedding_payload`, which verifies the completed payload, frozen pooling,
  vector hashes/shapes, finite values, orientation dimensions, and alternate-minus-reference
  arithmetic before creating a compact content-addressed feature record. These are source-level
  and no-spend tests only; no remote embedding smoke or completed feature cache has been
  authorized or run.
- Phase 10 is formally deferred by compute in
  `artifacts/modal/phase10_adaptation_deferral_20260921.json`. The record preserves the measured
  H100 inference envelope, the low-confidence cohort cost preflight, the absence of a checked-in
  official training runner/local CUDA runtime, and the current approval's explicit exclusion of
  training. `make finetune-smoke` now writes a no-metrics `DEFERRED` status artifact; no training
  or PEFT experiment was run.
- The Phase 5 multi-model track is formally deferred in
  `artifacts/model_audit/phase5_multi_model_deferral_20260921.json`: Evo2 passed the real smoke,
  while the six other candidates remain excluded for incompatible score contracts, missing
  assets, applicability, licensing, or unmeasured bounded compute. No deferred model was
  downloaded or promoted as a comparator.
- After the Phase 3 source-archive verification fix, `make validate` passed 650 tests with 33
  deselected, strict mypy over 51 source files, Ruff, secret scan, and 95.08% coverage. The Evo2 readiness
  module reached 100% coverage for its explicit remote-evidence branches; the feature-store
  adapter remains covered by `tests/unit/test_feature_store.py` and the CLI status option by
  `tests/unit/test_cli.py`.

The dated records below are retained as historical evidence. The latest `Current state`,
`Current authoritative execution update`, and follow-up sections at the top of this file override
older wording when a historical entry describes an earlier phase status or pre-pilot state.

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
  946 final temporal records (536 B/LB and 410 P/LP), 3,459 absent records, 9,049 definitive
  below-star records, 1,389,441 non-definitive records, and two t0/t1 gene annotation changes.
  The source archive hashes match the checked-in manifests. The category-semantic correction is
  recorded in `artifacts/phase3_partition_audit_20260921.json`; the full discrepancy audit is in
  `research/ml_extension/splits/phase3_manifest_summary.json`. Model scoring remains blocked
  until the remaining source/ID discrepancy is resolved or explicitly approved through the
  deviation process.
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
scoring is held behind the QA discrepancy review, multi-model inclusion evidence, and the
full-cohort execution gate. The bounded Evo2 pilot is engineering/provenance evidence only and
does not constitute a completed scientific experiment.
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

Current Modal assets: the canonical `evovariant-tr` app is deployed as v3 with tag
`phase2-pilot-20260921-r1`, using H100, `hf_cache`, the pinned NGC image, and Evo2 revision
`4b509ec2a22d6de472659f908bcb0714265ad3a7`. The real pilot loaded `evo2_7b`, verified the
UCSC-backed GRCh38 path, wrote a content-addressed prediction artifact, and returned an exact
equivalent cache hit. The prediction and model-weight caches remain remote in the named volume;
no checkpoint or cache file is tracked in Git.

Monthly budget assumption: approximately `$30/month` included compute as stated by the master
prompt; pricing and credits were not queried in Phase 0. The historical `$500` approval file
is not treated as current ML-extension authorization.

Estimated spend to date: local validation and Phase 3 data work were `$0`; the authorized pilot
family has rate-based wall-time estimates of approximately `$0.084` across the cold failure,
corrected miss, and cache-hit proxy records. This is an estimate, not an invoice.

Measured spend to date: the latest Modal workspace snapshot reports metered cost `$11.99` and
billed cost `$0.00`; the observed corrected pilot-family workspace delta remains approximately
`$0.33` from the pre-remote baseline recorded in the pilot artifact. Per-request measured USD is
unavailable; the failed old `variant-analysis-evo2` app was not called.

## Known blockers and exact next action

Known blockers are the material discrepancy between the recomputed temporal cohort and the
validation-only QA target, the formally deferred multi-model track, the lack of authorized
remote batch/embedding recovery evidence, and the lack of
registered full-cohort scientific outputs. Independent local gates, committed browser E2E, and
a fresh clean-room CPU/frontend rerun now pass. The registry-driven figure manifest and bundle
run with hash and field verification, but report `BLOCKED` because no eligible completed
scientific result artifacts exist; no result artifacts are registered. The earlier 13-
vulnerability report is retained only as historical pre-hardening evidence, not as a current
blocker.

Exact next action: resolve the Phase 3 discrepancy from source-level evidence or obtain a dated
protocol deviation that explicitly accepts the changed cohort and denominators. Only after that
gate and a separately bounded approval may the deferred GPN-Star/second-model path be reopened;
otherwise the multi-model deferral remains the honest terminal outcome for Phase 5. Do not run a
full benchmark, inspect locked labels for selection, train, tune, fine-tune, or generate release
figures from the single pilot record.

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

## Current Phase6A qualification state — 2026-09-21

- Implementation commit: `4e072ef` (`feat: complete bounded phase6a qualification`).
- The current authorized boundary is `artifacts/approvals/phase6a_throughput_20260921.json`:
  Phase6A cache/comparator/throughput qualification only, approximate `$1.50` cap, no full
  946-record Evo2 run, no t0-pool inference, no training/HPO/fine-tuning, and no automatic
  Phase6 continuation. The locked manifest remains 946 records with hashes
  `9f9e052d21f4a6a32f595cb20f48cb81e033c0481942820d04f9b67d410a16cb` and
  `ae4f6f1c1ad7c8d9ea78a9e5ce0380b1d8862a125592be5474b7826de165a6a0`.
- Cache preflight found zero reusable locked-cohort Evo2 predictions and 946 potential new
  records. The unrelated single-variant pilot cache and historical aggregate metrics were
  explicitly rejected. CPU qualification returned CADD usable values for 918/946 with 28
  explicit missing rows, phyloP100way values for 946/946, and AlphaMissense eligibility for
  507/946 with 0/507 prediction coverage. Evidence is in the Phase6A comparator artifacts.
- Canonical Evo2 H100 throughput passed all 12 sample/batch configurations at 8192 bp,
  forward/reverse, alternate-minus-reference scoring. The best warm result was 0.724826
  variants/s; the bounded model-only full-946 estimate was `$1.4732` and 1,342.653 seconds
  including one model load. The A100 comparison failed closed for all 12 configurations because
  this checkpoint requires compute capability 8.9+ for FP8; it is not a throughput result.
- The post-Evo2 real-GRCh38 representation smoke passed all 8 tiny configurations. It used four
  selected variants, four views per variant, mean-token pooling, and no feature-cache write.
  Nucleotide Transformer produced finite `[16, 1024]` pooled outputs and Caduceus finite
  `[16, 256]` outputs. These remain subset-only embedding evidence, not raw scores or a full
  feature extraction.
- The model registry retains only Evo2 in the benchmark inclusion set. CADD/PhyloP are
  qualified public comparator roles but remain `SUBSET_ONLY` to prevent widening the Evo2-only
  raw benchmark; AlphaMissense, NT, and Caduceus are also `SUBSET_ONLY`. The registry update
  artifact is `artifacts/phase6a/phase6a_registry_update_20260921.json`, and the scientific
  result registry is still empty.
- Modal workspace snapshots were `$12.34` to `$12.90` metered around Evo2 and `$12.94` to
  `$12.97` around representations, with `$0.00` billed. The combined client wall-rate estimate
  was `$0.560167`; no per-request invoice amount is claimed. `make validate`, `make
  ml-protocol-verify`, `make schema-verify`, `make model-registry-verify`, and `make
  registry-verify` pass. Full Phase 6 and all downstream phases remain blocked/not started.

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

## Current full-goal continuation audit — 2026-09-21

- The latest task instruction requests continuation beyond the previously completed Phase6A
  boundary. That instruction changes the active work objective, but it does not retroactively
  widen the dated Phase6A approval or make a stale approval artifact valid.
- The only approval that names a full primary run,
  `artifacts/approvals/full_run_approval.json`, is dated 2026-08-19, uses the legacy protocol
  identifier `frozen_v1.0.0_2026-08-18`, and is rejected by the current cost policy because the
  frozen ML-extension protocol hash is
  `39de386dcf952af0b4d03de770b68ad2c44d49a113510cafab184d6eebc0c6e3`.
- The current user approval,
  `artifacts/approvals/phase6a_throughput_20260921.json`, is valid only for Phase6A and explicitly
  excludes the full 946-record Evo2 benchmark, t0-pool inference, training, HPO, fine-tuning, and
  locked-test evaluation. No approval file was edited or widened.
- Current no-spend validation evidence: `make validate` passed with 656 tests, 33 deselected,
  strict mypy over 52 source files, Ruff, secret scan, and 95.12% coverage; ML protocol/schema/
  model-registry/registry verification passed; `make web-check` completed the ESLint, TypeScript,
  and production build gates. `make figures` and `make release-check` truthfully remain
  `BLOCKED` because there are zero registered scientific result records.
- Current read-only Modal evidence: `modal billing summary` reports workspace metered cost
  `$13.00`, billed cost `$0.00`; the canonical `evovariant-tr` and legacy app entries have zero
  active tasks, and no new remote workload was launched in this audit. This is workspace-level
  evidence, not a per-request invoice.
- The tracked project remains scientifically unchanged: the Phase6A result registry is empty,
  the locked cohort remains 946 records with the recorded hashes, and Phases 6-19 remain
  blocked/deferred until a current exact-scope approval and the dependent evidence are available.
- Next action requiring user authority: provide a current approval artifact or explicit budget/scope
  for the full Phase 6 and any subsequent GPU workloads. Once supplied, validate its protocol hash
  and launch only the smallest approved parity/cohort step; do not use the stale August approval.

## Phase 6/7 execution-surface subgate — 2026-09-21

- Local implementation is now present in `src/evovariant_tr/phase_execution.py` and
  `scripts/phase_execute.py`, with a Make control surface at `make phase-execute`. It is committed
  as `82ff2d6` (`feat: add gated resumable phase execution`).
- The runner validates source-manifest IDs and canonical `GRCh38:chr...` transport IDs,
  preserves the manifest file hash, freezes model/checkpoint/revision/protocol/split/shard/layer
  metadata, omits labels from every remote request, validates finite completed score or embedding
  rows, and writes atomic SHA-256-verified resumable shard artifacts plus raw JSONL outputs.
- `evo2_scorer_app.py` now exposes a bounded `extract_embeddings_batch` endpoint alongside the
  existing `score_batch` endpoint. Both report partial failures explicitly; the local runner
  fails closed on any partial, duplicate, unknown, missing, or wrong-layer response.
- No remote endpoint was called in this subgate. No model weights, full-cohort predictions,
  feature cache, scientific metrics, or result-registry record were created. Phase6A remains
  `PASS` only within its dated approval; full Phase 6 and Phase 7 remain `BLOCKED / NOT STARTED`.
- Validation evidence: `make validate` passed with 672 tests, 33 deselected, strict mypy, Ruff,
  secret scan, and 95.02% coverage. The targeted Phase 6/7 contract suite passed 19 tests;
  `make phase-execute` is safe by default because its default arguments print help only.
- The next paid action remains a bounded parity/cohort execution using a fresh approval whose
  protocol hash is `39de386dcf952af0b4d03de770b68ad2c44d49a113510cafab184d6eebc0c6e3`; the
  stale August approval and Phase6A approval must not be widened or reused.

## Phase 8/9 downstream CPU subgate — 2026-09-21

- Implemented `src/evovariant_tr/downstream_pipeline.py` plus
  `scripts/train_from_features.py` and `scripts/hpo_from_features.py`. The existing `make train`
  and `make hpo` targets now execute these local scripts only when explicit feature/config paths
  are provided; with no paths they continue to emit truthful blocked status artifacts. Implementation
  commit: `af97560` (`feat: add local downstream training and hpo runners`).
- The feature loader verifies JSONL content hashes, model/layer identity, binary labels, gene
  metadata, split membership, normalized-ID uniqueness, and train/validation identity and gene
  disjointness. `LOCKED_TEST` rows are rejected rather than filtered.
- Phase 8 baselines are logistic regression, decision stump, and deterministic CPU MLP. They fit
  on TRAIN and produce a validation-only AUROC/AUPRC/MCC-equivalent metric panel including
  accuracy, balanced accuracy, precision, sensitivity, specificity, F1, Brier, NLL, ECE, and
  calibration gap. Phase 9 writes a bounded validation-only logistic study and search space.
- No real feature cache exists, so no Phase 8/9 scientific run was executed, no locked labels
  were read, and no result registry entry or figure input was created. Synthetic fixture tests
  are software evidence only.
- Validation evidence: `make validate` passed with 676 tests, 33 deselected, strict mypy, Ruff,
  secret scan, and 95.01% coverage; `make train` and `make hpo` defaulted to `BLOCKED` status
  artifacts without requiring network or paid compute.

## Phase 11/12 ensemble and uncertainty subgate — 2026-09-21

- Implemented `src/evovariant_tr/analysis_pipeline.py` and `scripts/analyze_ensemble.py`.
  `make ensemble` now runs this local analysis only when explicit prediction/model paths are
  supplied; otherwise it writes the existing blocked status artifact. Implementation commit:
  `a3df7ac` (`feat: add validation-only ensemble analysis`).
- The loader rejects duplicate `(variant, split, model)` rows, malformed/non-finite scores,
  missing labels, and locked-test rows by default. The analysis requires common VALIDATION IDs,
  computes diversity/error overlap/correlation, fixed weighted aggregation, AUROC/AUPRC and
  calibration metrics, plus risk-coverage and abstention curves.
- No real prediction artifact exists, so no ensemble member, calibration method, abstention
  threshold, locked label, registry result, or figure input was selected. Phase 11 and Phase 12
  remain `BLOCKED / NOT STARTED`; Phase 13 remains blocked on the same frozen prediction inputs.
- Validation evidence: `make validate` passed with 679 tests, 33 deselected, strict mypy, Ruff,
  secret scan, and 95.00% coverage. `make ensemble` defaulted to a blocked status artifact with
  no network or paid compute.

## Current status-surface reconciliation — 2026-09-21

- Updated the Phase 6, Phase 7, and Phase 19 Make status surfaces and the zero-shot benchmark
  blocker artifact to match the accepted current state. They no longer report the accepted Phase
  3 discrepancy or the superseded pre-Phase6A model-roster wording as active blockers.
- Current blockers now state the exact missing dependencies: a current approval for the full
  workload, full-cohort batch/endpoint parity, completed Phase 6/7 scientific artifacts, locked
  evaluation, and registry/figure gates.
- `make benchmark-zero-shot`, `make extract-features`, and `make release-check` were rerun and
  each remained `BLOCKED` without network or paid compute. `make validate` passed with 679 tests,
  33 deselected, strict mypy, Ruff, secret scan, and 95.00% coverage.

## Phase 14 frozen locked-evaluation subgate — 2026-09-21

- Engineering outcome: `PASS` for the fail-closed evaluator contract; scientific Phase 14 remains
  `BLOCKED / NOT STARTED` because no real locked prediction artifact or current authorized frozen
  configuration exists.
- Added `src/evovariant_tr/final_evaluation.py` and `scripts/evaluate_locked.py`, and extended
  `make evaluate` to invoke them only when explicit prediction, model, config, config-hash, and
  output inputs are provided. The implementation commit is `1423577` (`feat: add frozen locked
  evaluation guard`).
- The evaluator requires `selection_closed=true`, a matching content hash, finite numeric
  threshold/bootstrap settings, one model's `LOCKED_TEST` rows, both classes, and an immutable
  output path. It reports fixed-threshold metrics and bootstrap AUROC provenance only; it has no
  selection or post-test tuning path.
- `make evaluate` with default variables wrote `research/runs/phase14_stat_status.json` with
  `BLOCKED` status and made no network or paid-compute request. No locked labels were consumed,
  no model/configuration was selected, and no result-registry record was created.
- Validation: `make validate` passed with 684 tests, 33 deselected, strict mypy over 56 source
  files, Ruff, secret scanning, and 95.04% coverage. The remaining Phase 15-19 gates are still
  blocked by absent real Phase 6/7/downstream artifacts, locked results, registry inputs, and
  current exact-scope approval.
