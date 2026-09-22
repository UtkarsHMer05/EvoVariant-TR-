# Project State — EvoVariant-TR ML Extension

## Current state — 2026-09-22

### Latest verified checkpoint — Phase 14

Phase 14 is `PASS` for the explicitly authorized Evo2-only locked evaluation subgate. The run
completed exactly `946/946` locked rows under approval
`artifacts/approvals/phase14_locked_evo2_20260922.json`, bound to execution HEAD
`c6c431869724666c84252cbd43979f2c4f38875f` with a `$2.75` hard cap and `$2.50` safety stop.
The final artifact is `artifacts/phase14/phase14_locked_evo2_20260922.json`, SHA-256
`4dd9b9229c47d65491345e87b70a6f6739432c24a7585966f4aea97a9d115499`; approval SHA-256 is
`4b619747a73942e56e15fef4040db1591760ee5a7813fb8f14fcc4740050dae7`.

- Paid inference: 946 newly scored rows, 30 remote H100 shard calls, 1,304.297864 seconds remote
  runtime, direct H100 estimate `$1.431104601`, zero transient retries.
- Finalization: 946 cache-hit rows from 30 verified shards, zero new remote calls, zero
  recomputation.
- Integrity: exact IDs, finite forward/RC/aggregate/calibrated scores, zero duplicates, zero
  unexpected IDs, zero reference mismatches, no labels sent remotely, raw artifact hashed before
  local label join, and every Phase 14 integrity gate `true`.
- Closeout: the immutable Phase 14 artifact records a fresh snapshot at metered `$33.50187443`,
  billed `$0.13`; the later final no-spend recheck at `2026-09-22T11:48:32.102345+00:00` returned
  metered `$33.43187443`, billed `$0.06`, with active containers `[]`. The provider summary does
  not expose a remaining free-credit balance. Against the user-stated `$7.17` pre-run headroom,
  the latest observed `$1.61` metered delta implies only an indicative `$5.56`, not a
  provider-confirmed balance.

The post-publication continuation then completed the bounded Phase15 development-only parity
smoke, connected the 14-area workbench to hash-verified publication inventory metadata, finalized
the conditional Phase17 bundle, and reproduced the free/control-plane clean-room sequence from a
detached checkout. Phase18 is `PASS` for that documented scope, with the Phase15 smoke as the
minimum gated Modal check; full remote re-inference is explicitly not required by the literal
Phase18 task list and is not claimed. Phase19 is `PASS` as an internal gate with
`release_allowed=false`; no tag, deployment, or publication release was requested. NT, Caduceus,
fine-tuning, and any broader paid workload remain outside this checkpoint.

### Latest post-publication continuation — Phase 15–19

- Phase15 approval: `artifacts/approvals/phase15_parity_smoke_20260922.json`, bound to execution
  HEAD `a460ba23626e1c566f56d58cb2f7aa0341f71d7d`, hard cap `$0.25`, safety stop `$0.20`.
- Phase15 validation: `artifacts/phase15/phase15_parity_smoke_validation_20260922.json` is
  `PASS_PHASE15_PARITY_AND_RESUME`. The exact 64-row set contains 56 verified cache rows and 8
  newly scored development rows; canonical raw/delta parity is zero-difference, all integrity
  checks pass, the persisted shard resumes with zero new remote calls, and no labels or locked
  rows crossed the Modal boundary.
- Phase15 compute: one planned remote invocation, 57.525624 seconds remote wall time, rate-based
  estimate `$0.063118`, and post-run active containers `[]`. The immediate post-run snapshot was
  metered `$33.65808745` and billed `$0.12`; the final no-spend recheck is recorded in
  `artifacts/phase19/modal_billing_final_20260922.json` at metered `$31.69808745` and billed
  `$0.00` after provider adjustments. The provider does not expose a confirmed free-credit
  balance. The user's `$7.17` basis minus the Phase15 estimate is an indicative `$7.106882`, not
  provider-confirmed headroom.
- Phase16: `PASS`; `/api/research/workbench` verifies source hashes before exposing per-area
  evidence metadata. `make web-check` and the four committed browser journeys pass.
- Phase17: `PASS_LOCAL_PUBLICATION_BUNDLE`; 41 inventory entries, 39 rendered figure families,
  39 source sidecars, 12 tables, and a report with explicit Motivation, protocol, temporal,
  Evo2, downstream/HPO/ensemble, calibration/uncertainty, robustness/error, limitations, and
  conclusion sections. Current publication manifest SHA-256 is
  `9783ae0a97923110bfe870412cc9245223f8f90c7a94b31455d9da597840d0dc`.
- Phase18: `PASS`; `artifacts/phase18/clean_room_execution_20260922.json` records a clean detached
  checkout at code commit `4681ac1c122bf5bacdf65c5a89c69d9531b672eb` with bootstrap, secret scan,
  Ruff, strict mypy, 714 tests, 95.01% coverage, protocol/model/registry checks, figures, frontend
  install/build, and clean Git status all passing.
- Phase19: `PASS` internal gate; `release_allowed=false` because external release was not requested.

The exact approved formal Evo2 Phase 6 continuation is complete and passed within scope. The
4,000-record formal development cohort is complete: 125 shards, 124 verified stored-shard cache
hits, one new 32-row remote shard, zero pending rows, zero duplicates, zero unexpected IDs, zero
reference mismatches, finite forward/reverse-complement/aggregate scores, no labels sent to Modal,
and zero locked-test rows. This is a bounded Evo2 subtrack result, not a PASS for the broader
multi-model Phase 6 benchmark.

- Final artifact: `artifacts/phase6/phase6_formal_evo2_20260921_full_overnight_20260922.json`,
  SHA-256 `b04940b3b5845fd57144f54a9862da8d9d89fb1b98d9c79fc45364e7a21ef54d`.
- Final predictions: `research/runs/phase6_formal_evo2_20260921_full_overnight_20260922/predictions.jsonl`,
  SHA-256 `088e39fcfa45b2af9cd8f11cbb803213d9030c92036fc9f27f577c3912693751`.
- Fresh approval: `artifacts/approvals/formal_phase6_par_resume_20260922.json`, SHA-256
  `f345f969f996a48ba33db9830d89c718d76fa64d7416e89209da5cef42758ae7`; it is bound to HEAD
  `535d73e56d10ddea5d2ef0098bb7251a57d259d7`, with a `$0.50` hard cap and `$0.40` safety stop.
- Preflight: `artifacts/phase6/formal_phase6_par_resume_preflight_20260922.json`, SHA-256
  `af8e052dde5f163d57951a0bdc7a41cef97da235c204f496597073d652beff17`.
- Reference amendment: `DEV-2026-001`/D-095 and
  `artifacts/reference/par_mask_resolution_20260922.json`, SHA-256
  `2f71248d7a97329db24301a73bdd427a2673af7ebc62a29a2ee4467060815b42`; it authorizes only the
  two verified chrY PAR1 hard-mask aliases and preserves original variant identity.
- Compute closeout: final app-specific observed usage `$0.09374570`; runner wall-rate estimate
  `$0.111328`; workspace billed cost `$0.00`; paid workers shut down and final Modal container
  inventory `[]`. From the exact prior derived free headroom `$5.94229534`, the derived remaining
  headroom is `$5.84854964` (approximately `$5.85`).
- Validation: final no-spend integrity audit PASS; pre-run `make validate` PASS with 715 tests,
  33 deselected, and 95.01% coverage. D-096 accepts the bounded Phase 6 result. The subsequent
  separately authorized Phase 7 and formal CPU continuation are recorded in the dated section
  below; locked-test inference and fine-tuning remained unopened at that earlier checkpoint.

Current control-plane checkpoint: branch `research/evovariant-tr`; the Phase 14 execution
approval was bound to code HEAD `c6c431869724666c84252cbd43979f2c4f38875f`, and no Next/Playwright
process or Modal container is active. Documentation and evidence updates after execution are
descriptive only; they do not widen the completed approval or authorize new paid work.

The current approval audit at implementation/documentation checkpoint
`f82893a29a5209f93f3c37299b99f42cd9228aff` is independently fail-closed:
`validate_overnight_completion_approval.py` rejects the broad overnight artifact because it is
bound to `535d73e56d10ddea5d2ef0098bb7251a57d259d7`, and
`validate_formal_representation_approval.py` rejects the Phase 7 artifact because it is bound to
`408edcc83e4a288cc8afb90a5bb9993af302c3d4`. Documentation-only commits follow that audit; no
paid workload is authorized from either artifact.

The initial Phase 14 request reached the preflight boundary and was correctly stopped before
approval activation; `artifacts/phase14/phase14_preflight_block_20260922.json` preserves that
fail-closed finding. Using development evidence only, the already-selected HPO model was then
materialized and replayed exactly. `artifacts/phase14/phase14_freeze_materialization_20260922.json`
and `research/runs/formal_cpu_20260922/phase13/pre_phase14_materialized_freeze.json` bind the
serialized classifier, TRAIN/VALIDATION hashes, both protocol hashes, Evo2 contract, isotonic
mapping, abstention coverage, and deterministic seeds. This pre-approval history is superseded
by the latest Phase 14 closeout above; no additional approval or paid work is implied here.

## Formal Phase 7 and development CPU continuation — 2026-09-22

The separately authorized Phase 7 continuation is complete and PASS. NT resumed from the
verified 2,432-row cache and scored exactly the remaining 1,568 IDs; Caduceus passed its
label-blind 64-row pilot and then completed all 4,000 formal rows. The final representation
artifact is `artifacts/phase7/formal_budgeted_representation_20260922.json` (SHA-256
`cea3b1c733eb70e58dcbaf49784fe9405e93a65eb0d7101aca464d3368b61783`), bound to approval
`artifacts/approvals/formal_phase7_continuation_20260922.json` (SHA-256
`f21cdc9cacac7407aba1c8117d031ac64b24ee726ccdd35a5b9cb55cef9dfbb3`). NT and Caduceus each
contain 4,000 ordered formal development rows, layers 8/16/24 and 4/8/16 respectively, finite
forward/RC/aggregate features, zero duplicate or unexpected IDs, zero locked overlap, and
`labels_remote_transport=false`. The Caduceus pilot projected `$0.677190`; the combined Phase 7
estimate was `$1.495327` against the `$1.75` hard cap and `$1.50` safety stop. NT runtime was
379.794382 seconds and Caduceus runtime was 646.733672 seconds. Paid workers were shut down;
the final container inventory was empty. The provider billing summary remains workspace-level
evidence rather than a per-run invoice; the recorded representation estimate is `$1.383999`.

The formal local CPU continuation then passed Phases 8, 9, 11, 12, and 13 on the frozen 4,000
row development manifest. Phase 8 evaluated 36 classifier/feature combinations, including Evo2,
NT, Caduceus, CADD, PhyloP, and justified fusion matrices. CADD missingness remains explicit
(2,891/4,000); no value was imputed. The final full-coverage selection is Evo2 combined features
with validation-only HPO logistic regression, not the higher-scoring incomplete comparator fusion.
The high-validation-performance leakage audit PASSed at
`research/runs/formal_cpu_20260922/phase8/leakage_audit.json`; train/validation gene overlap,
locked rows, duplicate IDs, non-finite values, and remote-label transport were all zero/false.

Formal CPU evidence is under `research/runs/formal_cpu_20260922/`: Phase 8 summary SHA-256
`c1f576ec854051e19238438017d28a0c0baf421518eaea9e78b02ff91617ae95`, Phase 9 summary SHA-256
`544016d582d6a37fec9d29a5e17834f99717f0f76e649563cc6b412784e36500`, Phase 11 ensemble SHA-256
`83a35e348d7a6359f3ed9a1d7bf5a5cde44b67d1d76cfd81e19bfa38819a7f1b`, Phase 12 calibration SHA-256
`bf1f9078386f35619d5188eabb07e8345f168cf0717565180cb0bca4c42520a3`, and Phase 13 artifact
SHA-256 `03205bb41bf2db8b814a8f7d312d01190f3f8c3644890e7aa3868e04c61f601f`. The immutable
pre-Phase-14 selection file is `phase13/frozen_config.json`; its content hash is
`3ab606a1e351b536f3c32ce45da956f844904ec704963f88f1cdc256d7d77424` and
`selection_closed=true`. Phase 10 remains `DEFERRED_BY_COMPUTE`. At that development-only
checkpoint Phase 14 had not run; the later locked Evo2 result is recorded in the latest
checkpoint above.

The no-spend figure-source continuation is also recorded. `scripts/register_formal_cpu_figure_sources.py`
materialized 19 hash-registered PRELIMINARY source artifacts from the verified Phase 6–13
development outputs in registry run `run_20260922T083143Z_66e6c1cf` (record SHA-256
`28aab509db409b46967994fe138e00ce7a33f1138ef5c878fcd1e35fc80eb5cc`). The generated figure
manifest now has 15/18 applicable required figure families and 11/11 applicable tables. Phase 9
HPO parameter importance is explicitly `NOT_APPLICABLE_WITH_DOCUMENTED_REASON` under
`artifacts/phase9/hpo_parameter_importance_deferral_20260922.json`; the bounded validation-only
grid has four trials per study and no predeclared importance estimator. The Phase 10 fine-tuning
table is also explicitly not applicable. The preliminary renderer produced 26 explicitly
non-promotable development-stage files. The final figure bundle remains BLOCKED by the three
unavailable mandatory source families (`context_length.json`, `loss.json`, and
`temporal_cohort.json`) and the absence of an eligible completed `FINAL` run; no locked labels or
locked predictions were accessed.

The local Phase 15 batch contract now has an explicit process-interruption regression check:
`tests/unit/test_batch_pipeline.py::test_execute_resumes_after_process_interruption` leaves a
completed shard on simulated worker termination, confirms no temporary file remains, and resumes
the remaining shard without recomputation. The focused batch suite passes 8 tests. This proves
local atomic-shard kill/restart behavior only; remote batch parity, remote smoke, and any
full-cohort batch authorization remain absent.

The Phase 16 workbench now reads `/api/research/status`, which verifies the registered formal CPU
output hashes before exposing development-stage evidence. It reports the completed Phase 8, 9,
11, 12, and 13 gates, 36 classifier combinations, 12 validation-only HPO studies,
`selection_closed=true`, untouched locked-test state, and current 15/18 applicable figure plus
11/11 applicable-table coverage. HPO parameter importance is explicitly not applicable under the
hash-backed Phase 9 decision; the remaining three mandatory source families remain visible as
blockers. The UI remains `PARTIAL`: no `FINAL` run is promoted. `make web-check`, four Playwright
E2E journeys, and the frontend contract tests pass.

## Current state — 2026-09-21

> Historical snapshot retained for provenance; the 2026-09-22 section above is authoritative for
> the current Phase 6–19 state.

Repository: `https://github.com/UtkarsHMer05/EvoVariant-TR-`

Current phase: `PHASE 6/7 FORMAL BUDGETED PRE-COMPUTE GATE / PHASE 15/16/17 LOCAL CONTINUATION`
(Phases 0-5 required gates and the separately approved Phase6A qualification are complete. A
fresh exact-scope `$5.00` development approval was used for a bounded Evo2 TRAIN/VALIDATION
prefix and the dependent CPU-only development stages; their verified PRELIMINARY summaries are
now connected to the experiment registry and read-only workbench. The additive
`ML-DEV-BUDGETED-001` design is frozen locally. The latest user-prioritized checkpoint authorized
up to `$8.00` of additional Modal compute with a `$7.75` runner safety stop; two bounded 64-row
preflight attempts were launched under that authorization, but both failed before any scientific
row completed because the Modal stream terminated during H100 scheduling. No successful new
scoring or representation extraction exists.)

Phase status: `BLOCKED / PARTIAL / FORMAL PRE-COMPUTE FAILED EXTERNALLY` at the final
release gate.
The repository retains the schema-validated control plane, fail-closed model registry/adapters,
deterministic CPU-only contracts for later experiment families, evidence-gated workbench, and
passing local Python/frontend build gates. Nine completed `PRELIMINARY` registry runs now expose
only hash-verified development-subset summaries; no result is promoted to `FINAL`. The local
batch surface now validates label-free CSV/VCF input, persists a hashed immutable plan, supports
injected-scoring shard recovery, and exports only hash-verified plan-order rows; it does not
invoke Modal or create scientific outputs during planning. The final figure renderer still emits
no outputs: nine of nineteen figure families and nine of eleven applicable tables are sourced,
one fine-tuning table is explicitly not applicable because Phase 10 is deferred, nine core source
families remain missing, and no completed `FINAL` run is registered. The separate preliminary
renderer emits 18 explicitly non-promotable development-stage files. The
approved Modal run produced 2,848 verified Evo2 development rows
(2,276 TRAIN, 572 VALIDATION) from the 239,992-row development cohort and stopped at a
`$4.698582` wall-time estimate before the `$5.00` hard cap. The full development cohort,
multi-model benchmark, NT/Caduceus feature extraction, comparator joins, and locked test were
not run. Labels were attached only locally after remote scoring; no labels or locked identifiers
were sent to Modal. The model weights remain cached only in the approved Modal `hf_cache` volume
and no weights are tracked in Git. The Phase 3 audit and independent reference report still
pass after the ML-only deviations; the historical target identity set remains unavailable and
is retained only as validation-only comparison evidence. The authoritative extension cohort is
946 records (536 B/LB, 410 P/LP), with 0 reference mismatches and deterministic regeneration
PASS. Phase 5 has a final separated roster: Evo2 raw score, Nucleotide Transformer/Caduceus
embedding tracks, CADD/PhyloP public CPU comparators, deferred GPN, and subset-only
AlphaMissense. Phase 10 adaptation remains `DEFERRED_BY_COMPUTE`; Phase 14 and all release,
deployment, publication, and clinical-classification surfaces remain excluded or blocked. The
registry/UI connection is `PARTIAL`, and Phase 17 remains blocked until every required source
family is present.

## Current budgeted development checkpoint — 2026-09-21

The latest user-prioritized checkpoint is recorded in
`research/ml_extension/AMENDMENT_ML-DEV-BUDGETED-001.md` and the formal artifacts under
`research/ml_extension/splits/formal_budgeted_20260921/`. The new explicit user authorization is
recorded in the persistent decision log; the exact approval artifact must still be materialized
and validated after the current validated changes are committed. No additional Modal job, model
download, or paid workload has been launched yet.

- The available development population remains 239,992 records: 191,957 TRAIN and 48,035
  VALIDATION; the 946-record temporal cohort remains untouched `LOCKED_TEST`.
- The existing 2,848-record Evo2 prefix is reconstructed exactly as an ascending
  `SHA256(normalized_variant_id)` prefix stopped by a budget reserve. It does not match the frozen
  manifest row prefix, and its representativeness is `NOT_ESTABLISHED`; all derived runs remain
  `PRELIMINARY`.
- The metadata audit covers class, split, gene, chromosome, position, variant type, source
  release, archived t0 review status, and archived t0 `last_evaluated` availability. Submission
  date and consequence type were unavailable in the frozen manifest and archived schema. Gene TVD
  is `0.4251876397`, chromosome TVD `0.03507732795`, class TVD `0.0059606154`, split TVD
  `0.0006901915`, and review-status TVD `0.0040953378`; descriptive similarity does not establish
  representation.
- `ML-DEV-BUDGETED-001` freezes a 4,000-record hash-selected subset: TRAIN 3,199 (2,645
  negative, 554 positive), VALIDATION 801 (581 negative, 220 positive), 3,226 negative and 774
  positive overall, and 1,927 unique genes. The selection is stratified by frozen split and class,
  uses the seed `ML-DEV-BUDGETED-001|2026-09-21|sha256-v1`, preserves zero TRAIN/VALIDATION gene
  overlap and zero locked-test overlap, and overlaps the old prefix in 56 IDs. It reads no model
  predictions and never changes the 239,992-record population.
- Formal manifest hashes are: development
  `f4a9e53bd96c60dd9bd949568adb7a6bece3ff01bd4cceb76f71f1380e16e782`, TRAIN
  `32bf517ec8bc401d29f611e83a8c8c81eafc0d1f19886d2650a3bf441df044e1`, VALIDATION
  `b31d884860fcf07b6f7f453c3ef148886913f381965318e9c1da341d1eaf3c8b`, and the complete
  hash index is in `manifest_hashes.json`.
- The cost plan estimates 3,944 new Evo2 variants at `$6.506744`, NT at `$0.378539`, Caduceus at
  `$0.226398`, and `$7.111681` total using measured Phase6/Phase6A rates. The previous `$5.00`
  approval is exhausted. The latest explicit user authorization permits an `$8.00` hard cap and
  `$7.75` runner safety stop; the fresh approval artifact is still pending the commit gate. The
  read-only workspace billing snapshot captured `$19.27` metered, `$0.00` billed, `$8.78` deployed apps,
  `$7.12` ephemeral apps, `$3.37` volumes, `-$15.90` credits, and `-$3.37` free storage. This
  provider summary is not an invoice or authorization.
- Validation after the amendment passes `make validate` with 703 tests, 33 deselected, strict
  mypy over 57 source files, Ruff, secret scan, and 95.02% coverage. The focused figure suite
  passes 13 tests; `make budgeted-study-design`, `make finetune-smoke`, `make figures`,
  `make registry-verify`, `make ui-check`, `make web-check`, and four local `make web-e2e` tests
  pass. The figure manifest remains truthfully `BLOCKED` with zero final outputs and an explicit
  Phase 10 non-applicable entry.
- Historical cache verification has independently PASSed for exactly 56 scientifically compatible
  Evo2 rows; no other historical prefix row is eligible for implicit reuse. Exact formal CPU
  comparator qualification has now PASSed before GPU work: CADD v1.7 has 2,891/4,000 usable values
  with 1,109 explicit missing rows, PhyloP100way hg38 has 3,997/4,000 usable values with 3 missing
  rows, and AlphaMissense has zero eligible missense rows/predictions in this cohort. Evidence is
  in `artifacts/phase6a/comparators/phase6a_comparator_qualification_20260921.json` and its three
  hash-addressed child artifacts; no labels were read for scoring and Modal was not invoked. Two
  exact-scope 64-row Evo2 preflight attempts then failed before a worker/container produced a
  score: `ap-3nvzpB5VADtBwNaoF5aOmA` and `ap-2yoBkvnIItyhk0pULH36CA` both ended with
  `StreamTerminatedError: Connection lost`. The final sample artifact is
  `artifacts/phase6/phase6_formal_evo2_20260921_sample64.json` with zero completed shards,
  zero remote rows, and unchanged `$19.33` metered / `$0.00` billed workspace billing. The local
  `FAIL_FORMAL_PREFLIGHT` gate therefore blocks the full 4,000-row run and dependent formal
  representations; no further paid retry is authorized without resolving the external Modal
  scheduling/transport failure and obtaining a fresh explicit continuation decision.

The untracked `.agents/` tree is a pre-existing local skills/workspace surface and is preserved;
it is not part of the scientific amendment.

Historical latest source baseline: `36063e8e1b65ddf1653347a5705e89115e52f1d5` (final Phase 3
freeze-summary/control baseline). The latest code-bearing continuation before the current
registry/calibration continuation is `99480fb` (`feat: record bounded development continuation`).
This checkpoint adds the preliminary registry, UI status, and train-only calibration surfaces;
the current `make validate` and control-plane gates pass. The exact current Git HEAD is
intentionally determined from `git rev-parse HEAD` because documentation-only commits update
this file without changing source behavior.
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
The frontend dependency/lint hardening was validated and committed in `739310d`. Continuation
implementation commits are `82ff2d6`, `af97560`, `a3df7ac`, `1423577`, `7fd912f`, `c53dfdb`,
`69a2e4f`, `0f1c5a4`, `c0ad1ad`, and `6196dc5`; continuation documentation/status commits are
`e39d3a3`, `b49b96a`, `e115d23`, `8264c70`, and `9f4a07c`. The current development runner, local
feature/ablation adapters, batch contract, preliminary renderer, and workbench status surface
are covered by the latest validation pass recorded below.

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

## Fresh no-spend gate refresh — 2026-09-21

- `make ml-protocol-verify`, `make schema-verify`, `make model-registry-verify`, and
  `make registry-verify` passed. The model registry reports 7 manifests with 1 included model
  (`evo2`) and the remaining candidates explicitly `SUBSET_ONLY` or `DEFERRED_BY_COMPUTE`.
- `make test-scientific` passed 7 tests with 1 explicit skip, and `make test-e2e` passed 14 tests
  with 1 explicit skip. These are local software/control-plane evidence only; they do not prove
  remote model inference or scientific cohort completion.
- `make web-check` passed ESLint, TypeScript, and the production build. Next.js emitted two
  non-fatal Turbopack warnings that dynamic filesystem access in
  `apps/web/src/app/api/registry/route.ts` broadens tracing; this warning remains recorded rather
  than suppressed.
- `make figures` regenerated an explicit `BLOCKED` manifest with zero available figures because
  no completed PRELIMINARY or FINAL run outputs are registered. Phase 6/7/8/9/11/12/13/14/15/16/
  17/18/19 status commands likewise remained `BLOCKED` with no network or paid compute.
- No scientific status changed: the Phase6A bounded PASS remains the latest authorized remote
  work, the full Phase 6/7 chain still needs a current exact-scope approval, and the downstream
  phases still need real immutable artifacts.

## Current Modal preflight and billing snapshot — 2026-09-21

- `make modal-smoke` verified `modal_installed=true` and `modal_authenticated=true`, then wrote a
  `PLANNED` cost-ledger entry with `gpu_count=0`, null estimated/measured USD, and the explicit
  note `no remote invocation requested`. This is authentication evidence only, not workload
  authorization.
- Read-only `modal billing summary` reported `$13.00` metered cost and `$0.00` billed cost. The
  read-only `modal app list` showed zero tasks for the listed deployed and stopped app entries.
  These are workspace-level observations and not a per-request invoice.
- No remote endpoint was invoked, no model was downloaded, and no new paid workload was started.
  The full Phase 6/7 execution remains blocked pending a current approval matching protocol hash
  `39de386dcf952af0b4d03de770b68ad2c44d49a113510cafab184d6eebc0c6e3` and exact workload scope.

## Current checkout metadata refresh — 2026-09-21

- The authoritative current checkout remains on branch `research/evovariant-tr`. The latest
  code-bearing continuation commit is `1423577`; subsequent commits in this block are
  documentation-only. The only untracked worktree path is the preserved pre-existing `.agents/`
  directory; no project files are unstaged or staged.
- This metadata refresh corrects the stale historical HEAD sentence near the top of this file. It
  does not change scientific phase status: Phase6A remains the latest authorized remote scope and
  full Phase 6/7 plus dependent scientific phases remain blocked pending current approval.
- Evidence: `git status --short --branch`, `git rev-parse HEAD`, and the current successful
  `make validate`/control-plane runs were inspected on 2026-09-21.

## Current bounded development execution — 2026-09-21

- The current exact-scope approval is `artifacts/approvals/phase6_phase7_development_20260921.json`
  (SHA-256 `f903a8ebed963e5c82e5a7578c54fc674685f1b5c1f445b23e38fd4b895fb50a`). It matches
  protocol hash `39de386dcf952af0b4d03de770b68ad2c44d49a113510cafab184d6eebc0c6e3`, development
  manifest hash `96d3e20e3cd97cb583b6b3d156ecd473c88ab66670704b1facb457351626ef72`, exact Evo2
  revision `4b509ec2a22d6de472659f908bcb0714265ad3a7`, H100, 8192-bp forward/RC scoring, and a
  hard `$5.00` cap. The user explicitly raised the cap from `$3.00` to `$5.00`; excluded scope
  remains locked-test labels/metrics, t0 1.4M inference, fine-tuning, Phase 10, Phase 14,
  deployment, release, and publication.
- The final Phase 6 artifact is `artifacts/phase6/phase6_development_evo2_20260921.json` (SHA-256
  `be5edd45942a70f494512c111dd1245f2d721c1a10f909e9de03524f5a22cfe5`) with status
  `PARTIAL_BUDGET_STOP`. It contains 2,848 completed records (2,276 TRAIN, 572 VALIDATION) out
  of 239,992, 237,144 remaining, 89 verified shards, and zero LOCKED_TEST rows. The predictions
  JSONL SHA-256 is `04baecf2d547ffd8ccaafa5eeeb2f11d2cccb46696f7cb9445ab317d133ba16d`.
  The approved manifest prefix, labels, genes, raw scores, forward/RC arithmetic, and every
  shard payload hash were independently rechecked after completion.
- The runner fixes are `69a2e4f` (ClinVar `MT`/`M` to frozen FASTA `chrM` mapping and explicit
  local preparation failure evidence) and `0f1c5a4` (cached source-ID/rate validation and finalizer
  arithmetic). The first two attempts failed closed before accepting an invalid shard; the final
  cache-only resume finalized cleanly. The cost ledger records a `$4.698582` H100 wall-time rate
  estimate, a `$4.75` pre-cap safety stop, and no measured invoice USD. The post-run workspace
  summary was metered `$19.34`, credits `-$15.97`, billed `$0.00`; that is workspace-level only.
- The local four-feature adapter `scripts/phase6_evo2_to_features.py` produced
  `research/runs/phase7_development_subset_20260921/evo2_raw_score_features.jsonl` (SHA-256
  `41bb16f3aa65b589690999449992edf9ec607d1042a99ffb4e20b2091c53dd7f`) and its summary (SHA-256
  `b3082e44292cc29bd12cc27cbe9eb6edb0adf9964be1b94ea823c47becbd6882`). It contains primary,
  forward, reverse, and orientation-disagreement features; labels were attached locally only.
- Real subset-only CPU stages completed from that adapter: Phase 8 summary SHA-256
  `99d1bbd34df34643ffd68eaf8356b6b83763288798efb6b99200da0bd0706c1a`, Phase 9 metadata
  `3d6095554c5744bfe989821f162ab735827d977627436bccf0f376040629393e`, Phase 11/12 analysis
  SHA-256 `6e452d6f9730529e9b3196cd62f2327b5a554976a86e66c023ebdcf07d91e036`, and Phase 13
  matrix SHA-256 `df5d82ffb6878bc5c875a10fabf846c1ad93935ee689766d04d68af24d073c57`. All are
  `locked_test_evaluated=false` and validation-only. The measured subset AUROCs were logistic
  `0.9931128641`, stump `0.9376820388`, MLP `0.9930825243`, HPO best trial `0.9932342233`,
  and fixed 50/50 logistic+MLP `0.9930976942`; they are preliminary subset diagnostics, not
  full-cohort or confirmatory claims.
- Phase 13 completed feasible orientation/feature ablations and CPU learning curves. Center
  shifts, NT/Caduceus embedding removal, external comparator removal, fitted-calibrator effect,
  and all full-cohort robustness cells remain deferred because they require missing features or
  new paid inference. Phase 10 remains `DEFERRED_BY_COMPUTE`; Phase 14 and the locked cohort
  remain untouched; the result registry, figures, release, deployment, and publication remain
  blocked.

## Current preliminary registry and workbench continuation — 2026-09-21

- The local script `scripts/register_development_subset_results.py` now consumes the verified
  Phase 6 artifact and the real local Phase 7/8/9/11/12/13 outputs, refuses any `LOCKED_TEST`
  rows, writes five small tracked development summaries under
  `artifacts/registry/development_subset_20260921/`, and registers seven completed runs at
  evidence stage `PRELIMINARY`. The script is idempotent for its immutable run titles and
  fails closed if a source hash or output path changes.
- Registered run IDs are `run_20260921T134951Z_286931e8` (Phase 6),
  `run_20260921T134951Z_95b4d32a` (Phase 7), `run_20260921T134951Z_c26c0788` (Phase 8),
  `run_20260921T134951Z_4587f802` (Phase 9), `run_20260921T134951Z_4cf11571` (Phases 11/12),
  `run_20260921T134951Z_707e558e` (Phase 13), and
  `run_20260921T134951Z_8b569866` (Phase 17 source bundle). `make registry-verify` passed,
  including recomputation of every recorded output hash.
- The tracked Phase 17 source bundle contains real development-subset ROC/PR curves, confusion
  matrices, reliability bins, risk-coverage points, bounded HPO best-trial data, learning curves,
  fixed ensemble data, feasible ablation cells, dataset/split flow, model-registry data, trained
  baseline summaries, and explicit deferred-cell failures. It intentionally omits unsupported
  benchmark, context-shift, embedding-layer, fine-tuning, subgroup, loss, temporal, cost-invoice,
  and HPO-importance sources.
- `research/runs/phase16_ui_status.json` is `PARTIAL` with seven completed scientific-stage
  registry records. The Next.js registry route and workbench now display the immutable run
  metadata while keeping all metric panels evidence-gated; `make web-check` passed and
  `make web-e2e` passed all four browser journeys.
- `research/runs/phase17_fig_status.json` is `BLOCKED` but no longer empty: 9 of 19 figure
  families and 9 of 12 tables have hash-verified PRELIMINARY source inputs. The renderer correctly
  emits zero scientific outputs until the ten missing source families are supplied, so this is
  not a figure or final-result promotion.
- `make clean-room` remains a blocked status surface because a fresh full scientific Modal
  reproduction was not authorized or run. `make evaluate` remains blocked because no locked
  predictions/configuration exist, and `make release-check` remains blocked because the current
  registry is PRELIMINARY and the full scientific and figure gates are unresolved.

## Current train-only calibration continuation — 2026-09-21

- The local-only calibration extension is `src/evovariant_tr/prediction_calibration.py` with
  `scripts/calibrate_development_predictions.py` and the explicit Make surface
  `make calibration-abstention PREDICTIONS=... CALIBRATION_OUTPUT=...`. It fits Platt and
  isotonic maps on the 2,276 aligned TRAIN rows from the fixed 50/50 logistic+MLP ensemble and
  evaluates them once on the 572 aligned VALIDATION rows. The loader rejects locked-test rows;
  no new remote work was started.
- The ignored full artifact is
  `research/runs/phase12_calibration_development_subset_20260921/calibration_comparison.json`;
  its tracked registry summary is
  `artifacts/registry/development_subset_20260921/phase12_calibration_development_subset_20260921.json`.
  The train-only fit has 2,276 rows, validation evaluation has 572 rows, and
  `locked_test_evaluated=false`. A separate tracked Phase 13 calibration-effect summary records
  the uncalibrated, Platt, and isotonic validation metrics.
- Preliminary validation diagnostics were: uncalibrated ECE `0.0843577465`, Platt ECE
  `0.0727681965`, and isotonic ECE `0.0389348144`; isotonic Brier was `0.0312355584` versus
  uncalibrated `0.2085391341`. These are train-fit/validation-only sensitivity results on the
  processed subset; they do not select a locked-test calibrator, establish clinical validity,
  or support a final claim. The isotonic fit has 311 blocks and the calibration comparison is
  therefore retained as sensitivity evidence rather than a final calibration decision.
- Two additional completed `PRELIMINARY` registry runs now record Phase 12 calibration and the
  Phase 13 calibration-effect summary. `make registry-verify` still passes; the current registry
  count is nine eligible completed preliminary runs. The Phase 17 source bundle remains blocked
  because the missing full-benchmark/context/embedding/fine-tuning/subgroup/loss/temporal/cost
families were not invented.

## Current Phase 15/16/17 local continuation — 2026-09-21

- Implementation commit `6196dc5` (`feat: add local batch and preliminary artifact surfaces`)
  adds a label-free Phase 15 batch contract, a deterministic planning CLI, a tracked three-row
  sample input, a fail-closed preliminary figure renderer, and truthful `PARTIAL` registry/UI
  status when completed runs exist without a `FINAL` run. The pre-existing untracked `.agents/`
  directory remains outside the project change set.
- The Phase 15 planner was verified with
  `make batch-run BATCH_INPUT=examples/batch/variants.csv
  BATCH_MODEL_REVISION=4b509ec2a22d6de472659f908bcb0714265ad3a7`. It produced `PLANNED`, three
  validated variants, one shard, and no scientific output. The input SHA-256 is
  `d0778b9ad572f7aa6d9b48f0d6675b1e8bd29180826ba0834aa64eff799f7378`. The local executor uses
  an injected scorer only, persists atomic content-hashed shard envelopes, reuses exact valid
  completed shards, persists classified failures, and retries failed shards only explicitly.
  Export now rejects corrupt, tampered, duplicate, label-bearing, out-of-order, or unexpected
  shard files. No Modal endpoint, model download, labels, or paid workload was used.
- `make figures` now keeps the final surface fail-closed: `research/figures/bundle_manifest.json`
  remains `BLOCKED` with zero scientific outputs and the same ten missing source families. It
  separately produces `research/figures/preliminary/preliminary_bundle_manifest.json` with
  `status: PARTIAL`, `evidence_stage: PRELIMINARY`, `promotable: false`, 9 figures, 9 tables,
  and 18 existing output files. Its SHA-256 is
  `026a82c02e1151d9bade98744bbd07c11d4c1e2ca7630b4b8ec3fda744cc9d40`.
- The read-only registry API and workbench report `PARTIAL`, with 9 completed scientific-stage
  runs and 0 final runs. `make registry-verify`, `make ui-check`, `make web-check`, and
  `make web-e2e` remain passing; the browser tier is 4 passed tests. The UI exposes metadata only
  and does not promote preliminary metrics to final evidence.
- The latest no-spend Python gate is `make validate`: 700 passed, 33 deselected, strict mypy and
  Ruff/secret checks passed, with 95.01% coverage. The scientific tier remains 7 passed/1
  skipped, and all existing protocol, schema, model-registry, registry, and figure checks remain
  evidence-gated. `git diff --check` passed before the documentation update.
- Phase 15 remains overall `BLOCKED` pending remote batch parity, kill/restart recovery evidence,
  full-cohort authorization, and a new exact-scope approval. Phase 17 remains blocked for final
  export, and Phases 14, 18, and 19 remain blocked by their documented locked-evaluation,
  clean-room, and release dependencies. The exhausted `$5.00` approval is not widened by this
  local continuation.

## Final no-spend gate refresh — 2026-09-21

- The implementation checkpoint is `6196dc5`; the documentation reconciliation checkpoints are
  `6b048af` and `f7dd472`. The branch is `research/evovariant-tr` and remains unpushed; the only
  untracked path is the pre-existing `.agents/` directory. No push was performed.
- `make validate` passed the secret scan, Ruff, strict mypy over 57 source files, 700 default-tier
  tests with 33 deselected, and 95.01% total coverage. `make ml-protocol-verify`,
  `make schema-verify`, `make model-registry-verify` (7 manifests, 1 included), and
  `make registry-verify` passed. The scientific tier passed 7 with 1 skip, and the API/E2E tier
  passed 14 with 1 skip.
- `make ui-check` reports 9 completed scientific-stage runs and `PARTIAL`; `make figures` reports
  final `BLOCKED`/0 outputs plus the preliminary `PARTIAL`/18-output non-promotable bundle;
  `make web-check` passed lint, TypeScript, and production build; and `make web-e2e` passed all 4
  browser journeys. The known non-failing Next/Turbopack filesystem-tracing and package-lock
  warnings remain documented and were not promoted to failures.
- `make evaluate`, `make clean-room`, and `make release-check` each recorded their expected
  `BLOCKED` status. `make phase-execute` printed approval-gated help without a network request.
  `make modal-smoke` reported authenticated Modal, `gpu_count: 0`, `status: PLANNED`, and no
  remote invocation. No new paid work, model download, locked evaluation, deployment, release,
  or publication was performed.

## Modal transport diagnostic continuation — 2026-09-21

- The latest checkpoint is bound to commit `e589efb5443713c864004472b1c3457a437d803a`
  (`docs: record failed formal Modal preflight`). The branch is `research/evovariant-tr`,
  remains unpushed, and the pre-existing `.agents/skills/modal` tree is preserved. The two
  original failed formal app IDs remain preserved: `ap-3nvzpB5VADtBwNaoF5aOmA` and
  `ap-2yoBkvnIItyhk0pULH36CA`.
- Before this checkpoint arrived, a third formal app `ap-TjBjZwIceAIK4Q6U8Y9B4l` had already
  started. It was stopped and retained as an interrupted attempt, not a PASS: its logs show an
  H100/NVIDIA PyTorch container, `evo2_7b.pt` discovery, model initialization, and repeated
  eight-record calls, followed by the deliberate local Ctrl-C and Modal `Runner terminated`.
  It returned no accepted formal result and did not rewrite or promote the failed sample gate.
- The required local pre-commit gate passed after that attempt: `make validate` reported 703
  tests passed, 33 deselected, strict mypy, Ruff, secret scan, and 95.02% coverage; `git diff
  --check` passed. The failed sample and `FAIL_FORMAL_PREFLIGHT` gate were committed separately.
- The diagnostic-only approval is
  `artifacts/approvals/modal_transport_diagnostic_20260921.json`, bound to the execution HEAD
  `e589efb5443713c864004472b1c3457a437d803a`,
  protocol hash `bad95bcf9a4217a2b4029656d327a8f3bdc1b9932a16a5034475a997a22157ec`, study
  `ML-DEV-BUDGETED-001`, Modal workspace/profile `utkarshmer05`, environment `main`, and a
  hard cap of `$0.50` with a `$0.45` safety stop. Formal 64-row retry, full 4,000-row work,
  NT/Caduceus, training, HPO, fine-tuning, locked test, and Phase 14 are excluded.
- Layer isolation passed the CPU transport surface. Four deterministic `cpu_echo` calls for
  values `0, 1, 7, 64` passed through `spawn/get` in
  `ap-23bynwYzoxKGO8TmPHVD9l`; the detached `modal run --detach` check in
  `ap-wsZoBWHGk1jN57Td2HXlIM` also passed, and a later `FunctionCall.from_id(...).get()`
  returned the expected result. Both diagnostic apps were stopped after retrieval.
- The minimal H100 diagnostic app `ap-YYNj6l8iIR9IGJORSrPCrF` did allocate container
  `ta-01M32DEAE8JMWAN7QDNZJHR4MR`, but the probe failed at the diagnostic image dependency
  boundary with `ModuleNotFoundError: No module named 'torch'`. This is a client/container
  diagnostic failure, not evidence that H100 scheduling is unavailable. The probe had no model,
  Hugging Face, or volume access. Per the checkpoint stop rule, the volume read and new Evo2
  load/one-record/eight-record diagnostics were not run.
- The complete evidence is
  `artifacts/modal_diagnostics/formal_preflight_failure_analysis_20260921.json`, with CPU,
  detached, H100, formal app, container/function/call ID, environment, timeout, and billing
  metadata. The single recommendation is `CLIENT_FIX_REQUIRED`: fix and validate the isolated
  H100 diagnostic image before any new H100-layer test, then obtain a fresh explicit continuation.
- Current scientific status remains `PARTIAL / BLOCKED`: the formal 64-row preflight is not a
  PASS, the full formal workload remains refused, no formal rows were accepted, labels were not
  sent remotely, and the locked test, training, HPO, fine-tuning, Phase 14, release, deployment,
  and publication boundaries remain untouched.

## Independent local gate refresh after the Modal diagnostic stop — 2026-09-21

- `make data-qc` completed `PASS` with deterministic regeneration, zero normalized-ID overlap,
  zero TRAIN/VALIDATION gene overlap, zero locked-test overlap, 239,992 development records,
  and split hash `bac30ed0a818258445a7340b1e96fe592902af5d4d7e899fbe227d24af955722`.
- `make phase3-audit` completed `PASS`; every current Phase 3 gate passed, including source
  archive/hash verification, temporal resolution, deterministic regeneration, normalized
  GRCh38 SNV identity, split leakage checks, and the ML-DEV-001 target-identity reconciliation
  boundary. `make phase3-reference-audit` independently checked all 946 authoritative temporal
  records and returned `PASS`. The refreshed tracked artifact is
  `artifacts/reference/grch38_validation_20260921.json`.
- The free validation sweep remains green: protocol verification, ML control-plane verification,
  schema verification, model-registry verification (7 manifests, 1 included), experiment
  registry verification, and the scientific tier (`7 passed, 1 skipped`) all passed. The
  frontend production gate passed and `make web-e2e` passed all 4 browser journeys.
- The H100 diagnostic definition now mirrors the already-qualified formal image by installing
  `torch==2.4.0` from the CUDA 12.4 PyTorch index after adding Python 3.12. Ruff, strict mypy,
  and local compilation pass for this correction. No remote H100 rerun was made; the prior
  `ModuleNotFoundError` evidence remains immutable and the recommendation remains
  `CLIENT_FIX_REQUIRED` until a fresh authorized diagnostic verifies the corrected image.
- Phase 17 remains `BLOCKED` with zero final outputs, Phase 18 remains `BLOCKED` because a full
  clean-room scientific Modal reproduction is unrun, and Phase 19 remains `BLOCKED` because the
  registry is preliminary and full locked/final artifacts do not exist. These are independent
  evidence gaps, not reasons to fabricate PASS results.
- The current no-spend status surface is explicit: Phase 6/7/8/9/11/12/13/14/15 status commands
  return `BLOCKED`, Phase 10 returns `DEFERRED_BY_COMPUTE`, Phase 16 returns `PARTIAL`, and
  Phases 17/18/19 return `BLOCKED`. `make modal-smoke` passes authentication with `gpu_count: 0`,
  `status: PLANNED`, and no remote invocation.

## Corrected H100 diagnostic retry checkpoint — 2026-09-21

- The corrected diagnostic approval is `artifacts/approvals/modal_h100_dependency_retry_20260921.json`,
  bound to execution HEAD `14d8a9812d6bc776a21d3b8e6006cd46d2b89d9e`, the frozen protocol and
  ML-DEV-BUDGETED-001 manifest hashes, Modal workspace/profile `utkarshmer05`, environment
  `main`, and a hard cap of `$0.50` with a `$0.45` safety stop. It does not authorize the formal
  64-row retry.
- The corrected minimal H100 app `ap-ST5uHP1cHmdblqU4CIAncx` allocated container
  `ta-01M32FFXEKXGSTP7SHMPF1KNTR`, function `fu-LUHgmjwLwoAdFTXNMmIEZ1`, and durable call
  `fc-01M32FFX3DC90FWRZ419TX9NJX`. Modal logs show NVIDIA PyTorch 24.07 startup and PyTorch
  `2.4.0a0+3bcc3cd`, so H100 scheduling, container startup, and remote PyTorch import are
  evidenced as PASS.
- The detached client then failed while deserializing the returned value:
  `DeserializationError: Deserialization failed because the 'torch' module is not available in
  the local environment.` The exact layer is local result deserialization after remote H100
  execution, not H100 scheduling. The required CUDA result, GPU name, and compute capability
  were not accepted by the local client.
- The new evidence is `artifacts/modal_diagnostics/h100_dependency_retry_analysis_20260921.json`
  and `artifacts/modal_diagnostics/h100_cuda_probe_20260921.json`. No `hf_cache` read, Evo2 load,
  one-row score, eight-row score, formal 64-row retry, or locked-test access followed the
  failure. The app is stopped and `modal container list` is empty.
- A local follow-up fix now coerces every diagnostic return field to JSON-safe builtins in
  `scripts/modal_h100_diagnostic.py`; it is committed at `e8ae239`. `make validate` passes with
  704 tests, 33 deselected, strict mypy, Ruff, secret scan, and 95.02% coverage. Because the
  existing approval is bound to `14d8a98`, no rerun was made after `e8ae239`; a future H100 retry
  requires a fresh approval bound to the new HEAD.
- Billing snapshots before and after the diagnostic both showed workspace metered cost `19.57`
  and billed cost `$0.00`; this is workspace-level evidence, not a per-run invoice. The single
  continuation state recorded for this stopped ladder is `PYTORCH_IMAGE_FIX_REQUIRED`, with the
  precise remediation being plain-builtins result serialization at the client boundary.
- Phase 6 remains `FAIL_FORMAL_PREFLIGHT`; all dependent scientific/downstream phases retain
  their existing `BLOCKED`, `DEFERRED_BY_COMPUTE`, or `PARTIAL` status. No scientific result or
  formal gate was promoted.

## Independent post-diagnostic gate refresh — 2026-09-21

- The current no-spend checkout remains at HEAD `32359c2` on `research/evovariant-tr`; the only
  untracked project-control inputs are the preserved Modal skill tree and the three approval
  artifacts. No tracked source or scientific artifact is dirty.
- `make web-check` passed frontend lint, TypeScript, and the production build. `make web-e2e`
  passed all four committed Playwright journeys. The existing Next.js tracing and external
  package-lock warnings remain non-failing and were not promoted to errors.
- `make registry-verify` and `make model-registry-verify` passed. The model registry still has
  seven manifests with only Evo2 `INCLUDED`; NT, Caduceus, CADD, PhyloP, and AlphaMissense remain
  `SUBSET_ONLY`, while GPN remains `DEFERRED_BY_COMPUTE`.
- `make ui-check` remains `PARTIAL` with 9 registered/completed preliminary scientific runs,
  zero locked-test evaluation, and a connected registry. `make figures` remains fail-closed:
  final `BLOCKED` with zero outputs and the known missing source families; the separate
  preliminary bundle has 18 non-promotable outputs.
- The refreshed status surfaces remain truthful: Phases 6/7/8/9/11/12/13/14/15/18/19 are
  `BLOCKED`, Phase 10 is `DEFERRED_BY_COMPUTE`, and Phase 16 is `PARTIAL`. `make modal-smoke`
  authenticated successfully with `gpu_count: 0`, `status: PLANNED`, and no remote invocation.
  No phase was promoted from local control-surface evidence.

## Fresh JSON-safe H100 diagnostic ladder — 2026-09-21

- A fresh approval was created at
  `artifacts/approvals/modal_h100_jsonsafe_retry_20260921.json`, bound to HEAD
  `cc035d1d2f49d42c3770fd4e9c9dc94587f5465e`, with a `$0.50` hard cap and `$0.45` safety stop.
  The prior three approval artifacts remain byte-for-byte unchanged. The frozen protocol,
  formal TRAIN/VALIDATION manifests, formal record-set hash, and locked-test manifest were not
  modified. The formal 64-row retry remains explicitly excluded from this approval.
- The corrected JSON-safe H100 probe passed in app `ap-6saybhZYlnXAf2CmB98tXP`, function
  `fu-5lcgqs4HgSSP6xGP1I2rRX`, call `fc-01M32GDY0FPCXSECVK2PJQY5B9`, container
  `ta-01M32GDYA6FBAKDZ2AZ0XGHXNR`. Local `FunctionCall.get()` and independent detached
  `FunctionCall.from_id(...).get()` both returned plain builtins. The probe reported PyTorch
  `2.4.0+cu124`, CUDA `12.4`, `cuda_available: true`, H100 `NVIDIA H100 80GB HBM3`, compute
  capability `[9, 0]`, and tensor result `2.0`. The previous local result-deserialization failure
  did not recur; the exact failure layer is therefore resolved by `e8ae239` for this probe.
- The read-only cache check passed in app `ap-5orUJFT7c3T0Zb6HE1U4gN`, call
  `fc-01M32GMEMTMNFKJ60M6PW1918T`, with a valid mounted `hf_cache`, readable
  `hub/models--arcinstitute--evo2_7b/snapshots/bda0089f92582d5baabf0f22d9fc85f3588f6b58`,
  readable `evo2_7b.pt` (13,766,621,200 bytes), readable `config.json`, and a structurally valid
  cache. No cache write, clear, or redownload was performed.
- Canonical Evo2 load-only passed in app `ap-Th4trAg5I1lyS9edw0SzqG`, function
  `fu-neSkt1w16XgFvZQFEm2y3K`, call `fc-01M32GRHKA7ZASBDXEF9NB7B53`, container
  `ta-01M32GRJ09E2YHWRF2FJ5XMGWR`. `evo2_7b` revision
  `4b509ec2a22d6de472659f908bcb0714265ad3a7` loaded on `cuda:0` with `torch.bfloat16` in
  `29.368544` seconds, with a cache hit and peak allocated/reserved memory of
  `13,669,210,112` / `15,466,496,000` bytes. The independent durable retrieval passed.
- The one-row non-locked development diagnostic passed in app `ap-5pbxOL6rhdzLf87jqec6T4`,
  function `fu-oTEePJyTZ7t6xPK78B0buq`, call `fc-01M32H51FXH9JAPH3HR1G68PB2`, container
  `ta-01M32H51SKQF90YB22H7X4H8KR`. It selected `GRCh38:10:101532297:A>G` from `TRAIN` by
  ascending normalized ID, verified the GRCh38 reference and four 8192-bp orientations, sent no
  label, returned finite forward/RC/aggregate scores, and preserved the exact model revision.
- The eight-row mini-shard passed in app `ap-vQWe7aKZhMWkzrSWKoguGx`, function
  `fu-ZAxNwmp8kElCIkmRhSTfhJ`, call `fc-01M32H843J01JNSS35BF850741`, container
  `ta-01M32H84C5F1D61PR30QD7HR5R`. It processed exactly eight deterministic TRAIN IDs in one
  batch, returned eight finite rows in deterministic order, used the cache, and passed durable
  retrieval. The persisted shard and a separate local resume check passed with zero additional
  remote invocations and no duplicate recomputation.
- The consolidated evidence is
  `artifacts/modal_diagnostics/h100_jsonsafe_retry_20260921.json`; the historical failed probe
  remains unchanged at `h100_cuda_probe_20260921.json`, while the new PASS probe is preserved at
  `h100_cuda_probe_jsonsafe_retry_20260921.json`. Other per-layer artifacts are
  `hf_cache_read_20260921.json`, `evo2_load_20260921.json`,
  `evo2_development_1_20260921.json`, `evo2_development_8_20260921.json`, and the eight-row
  resume artifact. The conservative H100 wall-rate estimate is `$0.208895` additional; the
  workspace meter was `19.61` at the ladder baseline, `19.88` in the final in-ladder artifact,
  and `19.94` at the final read-only inventory check; billed cost remained `$0.00`. Modal
  billing is workspace-level, not a per-run invoice. All diagnostic apps are stopped.
- Diagnostic gates are now `PASS` for JSON-safe H100, `hf_cache`, Evo2 load, one-row scoring,
  and the eight-row shard/resume. This does not promote the formal study: the formal 64-row
  preflight was not started, the locked cohort was not accessed, and downstream Phases 6/7/8/9/
  11/12/13/14/15/18/19 remain `BLOCKED`, Phase 10 remains `DEFERRED_BY_COMPUTE`, and Phase 16
  remains `PARTIAL`. The single next recommendation is `RETRY_FORMAL_64_PREFLIGHT`, but only
  after a separate explicit approval because the current `$0.50` approval excludes it.

## Formal preflight provenance reconciliation — 2026-09-21

- The successful JSON-safe H100/Evo2 diagnostic ladder and its control artifacts were committed
  in `e0e43bf0cbc702db38fbd5a274e574c89e2ad24a`. The tracked worktree is clean; the only
  untracked path is the pre-existing local `.agents/` skills tree.
- The two pinned revisions are intentionally different namespaces and are reconciled. The
  executable source is `https://github.com/ArcInstitute/evo2.git` at
  `4b509ec2a22d6de472659f908bcb0714265ad3a7`; the model repository is
  `https://huggingface.co/arcinstitute/evo2_7b` at snapshot
  `bda0089f92582d5baabf0f22d9fc85f3588f6b58`. The Modal image clones/checks out the former,
  then `Evo2("evo2_7b")` resolves the latter through the mounted Hugging Face cache.
- The cache probe found `evo2_7b.pt` at 13,766,621,200 bytes, with blob identifier
  `c66645929dc1b9c631f5be656da8726f38946315dc9167000a615dd626fcecf4`; the identifier is
  recorded as a cache object identifier, not as an independently recomputed 13.77-GB content
  hash. The cache config is structurally readable and exposes `_name_or_path`, `architecture`,
  and `name` keys.
- The source and model therefore represent the same intended canonical execution contract:
  `evo2_7b`, H100, bfloat16, GRCh38, 8,192 bp, forward plus reverse complement, and
  alternate-minus-reference log likelihood. The cache-hit load and the one/eight-row score
  artifacts independently confirm that contract. Full evidence is in
  `artifacts/modal_diagnostics/evo2_provenance_reconciliation_20260921.json`.
- This reconciliation is `PASS` and does not authorize a full run. A new approval is still
  required for the formal 64-row preflight; the frozen manifests and locked-test boundary remain
  unchanged.

## Formal 64-row preflight checkpoint — 2026-09-21

- The separate approval `artifacts/approvals/formal_64_preflight_20260921.json` was validated
  against execution HEAD `dae42a265f64601af91e209dfcd3c9e5c963ecd2`, with a `$0.75` hard cap and
  `$0.65` safety stop. It authorized only the formal 64-row Evo2 preflight, cache/resume,
  provenance, and cost measurement; the approval was not reused for a full run.
- The formal sample passed at the row level. Exactly 64 records were selected from the frozen
  4,000-row formal development manifest by ascending
  `SHA256(normalized_variant_id|ML-DEV-BUDGETED-001|FORMAL-64-PREFLIGHT|2026-09-21|sha256-v1)`;
  selection was label-blind and did not use CADD, PhyloP, predictions, or locked-test data.
  Descriptive coverage was TRAIN 46, VALIDATION 18, 21 chromosomes represented, and 58 unique
  genes. All 64 rows returned finite canonical forward/reverse scores with zero reference
  mismatches, zero duplicate or unexpected IDs, zero locked rows, and no labels sent to Modal.
- The durable Modal run was app `ap-BJUiZPDuBbdkxaEsbPougn`, function
  `fu-eIxtQurXxHVYM46hfWauMo`, container `ta-01M32K7GE601S233HNHWQQ30DR`, and FunctionCalls
  `fc-01M32K7G6760X0W60KQGVJV94A` and `fc-01M32K9XNR6CT9100REY2KQMCH`. The same plan was
  resumed in app `ap-YTtOeacENcg8Cz5M0jBHys`; two persisted shards were reused and the resume
  invocation made zero remote calls. The detailed log evidence is
  `artifacts/modal_diagnostics/formal_64_preflight_modal_evidence_20260921.json`.
- The measured preflight wall-rate estimate was `$0.135088` for 62 new remote rows, below the
  `$0.65` safety stop. The frozen projection nevertheless scales that measured rate to
  `$8.593340` for the 3,944 new Evo2 rows and `$9.198277` for formal Phase 6/7 including the
  frozen NT/Caduceus estimates. This exceeds both the intended `$7.75` runner stop and `$8.00`
  bounded formal plan.
- The durable gate is
  `artifacts/phase6/formal_budgeted_preflight_gate_20260921_formal64_jsonsafe_retry.json` with
  status `FAIL_FORMAL_PREFLIGHT` and exactly one recommendation:
  `FORMAL_PREFLIGHT_FIX_REQUIRED`. The full 4,000-row run, NT/Caduceus extraction, locked-test
  inference, Phase 14, fine-tuning, deployment, and release were not started. Phase 6 remains
  blocked and no dependent phase is promoted.
- Modal workspace billing observed `$19.96` around the formal run and `$19.98` at the final
  read-only inventory check, with `$0.00` billed; these are workspace-level observations, not a
  per-run invoice. `modal container list --json` is empty. Formal manifests and the locked-test
  cohort remain unchanged.

## Current Phase 7 representation state — 2026-09-22

- Phase 6 formal Evo2 remains complete and immutable. The narrow Phase 7 NT/Caduceus allocation is
  `PARTIAL / ALLOCATION BLOCKED`: 2,432/4,000 NT rows are verified and resumable, while 1,568 NT
  rows and all 4,000 Caduceus rows remain. No Phase 7 PASS is claimed.
- The 504-row small-shard cache and 1,928-row optimized cache are both hash-verified. The union has
  zero duplicates, zero unexpected IDs, zero locked overlap, no remote labels, finite packed layer
  features, and exact local GRCh38/8,192-bp reference construction matches. No paid containers or
  pending calls remain.
- Partial evidence: `artifacts/phase7/formal_budgeted_representation_20260922_partial.json`.
  The cumulative completed client wall-rate estimate is `$0.704889` against the `$1.00` hard cap
  and `$0.85` safety stop. A new explicit allocation and approval are required before resuming.
  Locked-test inference, fine-tuning, Phase 14, deployment, and release remain unopened.

## Clean-room reproducibility correction — 2026-09-22

- The authoritative current implementation HEAD is `27352e52605585e6fd3ec467bdd8afb32396df70`
  on `research/evovariant-tr`. The focused clean-room fixes are `3412071` (declare the existing
  NumPy test dependency), `2f538b7` (track hash-verified registry-referenced CPU outputs and
  align stale fallback assertions), `9662c7d` (make the committed Playwright server command
  self-contained), and `27352e5` (make the blocked research-status API shape-safe and track the
  current Phase 16/17 status manifests).
- A fresh clone from `27352e5` passed `make bootstrap`; `make validate` (`714 passed, 1 skipped,
  33 deselected`, 95.01% coverage); `make registry-verify`; `make frontend-install` (407 packages,
  zero vulnerabilities); `make web-check`; all four `make web-e2e` journeys; `make test-scientific`
  (7 passed, 1 skipped); and `make test-e2e` (14 passed, 1 skipped). The frozen protocol,
  additive ML control plane, JSON schemas, model registry, and `make ui-check` also passed.
- Fresh-clone `make figures` reproduced the expected fail-closed state: 15/18 applicable figure
  families, 11/11 applicable tables, zero final-bundle outputs, and 26 non-promotable preliminary
  outputs. HPO parameter importance is explicitly non-applicable under the hash-backed Phase 9
  decision; missing mandatory sources remain exactly `context_length.json`, `loss.json`, and
  `temporal_cohort.json`, with no eligible completed `FINAL` run. `make clean-room` and
  `make release-check` correctly remain `BLOCKED` because paid scientific reproduction and final
  release evidence are absent.
- The API fallback was independently exercised in the fresh clone with both status manifests
  temporarily absent: `/api/research/status` returned a complete shape with `BLOCKED` status and
  `/analysis` returned HTTP 200. The manifests were restored unchanged. No paid compute, locked
  labels, locked predictions, or Phase 14 work was performed. The pre-existing dirty source,
  test, approval, and `.agents/` paths remain uncommitted and were not staged.
- The no-spend `make modal-smoke` preflight confirmed Modal was installed and authenticated and
  wrote only a `PLANNED` cost-ledger entry with `gpu_count=0`; it made no remote invocation and
  no paid worker was created. The actual gated Modal smoke remains unrun.

## Post-Phase-14 no-spend publication continuation — 2026-09-22

Phase 14 remains immutable `PASS` for the exact Evo2-only locked-evaluation subgate. The
post-Phase-14 continuation completed the reachable no-spend reporting and reproducibility work;
it did not reopen selection, modify any Phase 14 artifact, or start Modal compute.

- The missing temporal source is now materialized and hash-registered in preliminary registry run
  `run_20260922T121044Z_6004c17` at
  `research/runs/formal_cpu_20260922/figure_sources/temporal_cohort.json`. It preserves the
  historical 1,024-row target as comparison-only and the accepted current cohort as 946 rows
  (536 B/LB, 410 P/LP, 367 genes).
- Phase 10 loss is explicitly `DEFERRED_BY_COMPUTE`; Phase 13 context length is explicitly
  `NOT_APPLICABLE_WITH_DOCUMENTED_REASON` under
  `artifacts/phase13/context_length_deferral_20260922.json`. Neither cell has invented points
  or a downstream metric.
- The publication bundle is `PASS_LOCAL_PUBLICATION_BUNDLE`: 39 applicable rendered figure
  families, 39 source sidecars, SVG/PNG/PDF outputs, 12 CSV tables, and a figure inventory/report.
  The inventory is `research/reports/phase17/FIGURE_INVENTORY.json`; the report is
  `research/reports/phase17/FINAL_REPORT.md`; generated figures are under
  `research/figures/final/` and tables under `research/tables/final/`. The final Phase 14 and
  joined-prediction hashes remain
  `4dd9b9229c47d65491345e87b70a6f6739432c24a7585966f4aea97a9d115499` and
  `77cbbb48032ac7852ff09f93ea448d1e98ca21457843c1feda16f31e8dc530e7`.
- Phase 15 is `BLOCKED_NEW_PAID_AUTHORIZATION_REQUIRED`. Local label-free planning and atomic
  shard interruption/restart pass; a minimum future 64-row development-only smoke is estimated
  at `$0.096818916` direct H100 cost, with zero locked rows, but no cap or approval was created.
- Phase 16 remains `PARTIAL`; Phase 17 local publication is complete; Phase 18 is `PARTIAL`
  (local registry/artifact hash reproducibility `PASS`, full remote scientific re-inference not
  run); Phase 19 is `BLOCKED` and release is not allowed. No tag, deployment, publication,
  NT/Caduceus rerun, fine-tuning, or locked-test rerun is authorized here.
- Fresh read-only Modal recheck is recorded at
  `artifacts/phase17/modal_billing_recheck_20260922.json`: metered `$33.59808745`, billed
  `$0.06`, active containers `[]`. Against the user-stated `$7.17` pre-run headroom, the latest
  observed meter delta `$1.77621302` implies an indicative `$5.39378698`; the provider does not
  expose a confirmed remaining free-credit balance.
