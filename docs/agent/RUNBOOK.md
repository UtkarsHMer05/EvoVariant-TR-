# Runbook

## Session start

1. `git status`
2. `git branch --show-current`
3. read `docs/agent/PROJECT_STATE.md`
4. read latest `docs/agent/DECISIONS.md`
5. check `PHASE_LEDGER.md`
6. inspect uncommitted work
7. do not overwrite user work

## Before paid Modal work

1. verify auth without printing secrets;
2. verify app/environment;
3. inspect current credit/billing if available;
4. estimate job;
5. confirm cost gate;
6. confirm cache miss is real;
7. launch smallest pilot first.

## Before locked-test work

1. protocol finalized;
2. dataset hash frozen;
3. split hash frozen;
4. model config frozen;
5. HPO closed;
6. ensemble config frozen;
7. calibration rule frozen;
8. result directory empty/new immutable run ID.

## After an experiment

1. save config;
2. save environment/model metadata;
3. save raw predictions;
4. save metrics;
5. save timing/cost;
6. validate schema;
7. update registry;
8. generate plots only from artifact;
9. update project state.

## Phase 6/7 approved cohort execution

Use the dedicated runner rather than calling a Modal endpoint ad hoc. Its default invocation is
safe and prints help only:

```bash
make phase-execute
```

For a real run, pass every argument explicitly through `PHASE_EXEC_ARGS`. The approval must be
current, match the current ML-extension protocol hash, and name every requested workload token:

```bash
make phase-execute PHASE_EXEC_ARGS="\
  --phase 6 \
  --family ZS \
  --endpoint-kind score \
  --model-id evo2 \
  --checkpoint evo2_7b \
  --model-revision <pinned-revision> \
  --manifest research/ml_extension/splits/authoritative_cohort_manifest.json \
  --split LOCKED_TEST \
  --split-manifest research/ml_extension/splits/authoritative_split_manifest.json \
  --endpoint https://<approved-score-batch-endpoint> \
  --output-dir research/runs/<immutable-run-id> \
  --approval artifacts/approvals/<current-approval>.json \
  --scope-token \"full Phase 6\" \
  --scope-token Evo2"
```

For Phase 7 use `--endpoint-kind embedding`, add the frozen `--embedding-layer`, and point the
endpoint at the bounded `extract_embeddings_batch` method. `--include-labels` only copies labels
into local output rows after remote execution; it never sends labels across the endpoint
boundary. Do not pass a locked split until the model/configuration is frozen under the protocol.
The runner writes an execution plan, content-hashed shard files, raw JSONL output, and a summary;
inspect and register those artifacts only after their hashes and scientific gates pass.

## Phase 15 local batch planning and recovery

The local batch contract accepts only label-free GRCh38 biallelic SNVs from CSV or VCF/VCF.GZ.
Plan the input before attaching any scorer or requesting remote work:

```bash
make batch-run \
  BATCH_INPUT=examples/batch/variants.csv \
  BATCH_MODEL_REVISION=4b509ec2a22d6de472659f908bcb0714265ad3a7
```

This writes a deterministic `batch_plan.json` and `planning_summary.json` under
`research/runs/phase15_batch_plan/` and reports `PLANNED`; it does not invoke Modal, download a
model, send labels, or create scientific outputs. `src/evovariant_tr/batch_pipeline.py` exposes
the next local boundary through an injected scorer: `execute_batch` writes atomic,
hash-addressed shard envelopes, reuses only exact valid completed shards, persists failure
taxonomy, and retries failed shards only when `retry_failed=True`. `export_batch_results` checks
the plan order, payload hash, exact shard IDs, label-free row shape, and rejects stray or tampered
shards before writing JSONL.

Remote batch parity, kill/restart recovery, full-cohort execution, and any paid compute remain
blocked until a new exact-scope approval and a fresh remote smoke satisfy the master prompt.

## ML-DEV-BUDGETED-001 local design checkpoint

The existing 2,848-row Evo2 prefix is preliminary and must not be promoted to the formal
model-selection study. Before requesting any new compute, run the no-spend audit and subset design:

```bash
make budgeted-study-design
```

The command reconstructs the prefix's ascending `SHA256(normalized_variant_id)` selection,
compares available development metadata against all 239,992 records, and writes the frozen
4,000-record train/validation manifests, QC, hash index, and cost plan under
`research/ml_extension/splits/formal_budgeted_20260921/`. Selection is stratified by the frozen
split and class, uses the recorded amendment seed, preserves gene-disjoint train/validation and
zero locked-test overlap, and never reads model predictions. The same manifests are required for
Evo2, CADD, PhyloP, eligible-only AlphaMissense, NT, and Caduceus tracks.

This is a local planning command only. It does not call Modal, download weights, run scoring,
extract representations, fit classifiers, tune hyperparameters, fine-tune, or evaluate the locked
test. The current rate-based plan is `$7.111681` total (`$6.506744` Evo2, `$0.378539` NT,
`$0.226398` Caduceus), with 3,944 new Evo2 variants after 56 prefix overlaps. The previous
`$5.00` approval is exhausted. The latest explicit user authorization permits an `$8.00` hard cap
and `$7.75` runner safety stop, but the fresh approval artifact must be created from the committed
validated state and pass its exact hash checks before Modal work.

Before remote work, materialize the exact formal comparator evidence and verify the historical
cache reuse artifact:

```bash
make formal-budgeted-approval-verify  # after the fresh approval artifact exists
```

The comparator utility is CPU/network-only and must be run against
`formal_development_manifest.json`, recording CADD v1.7, UCSC phyloP100way hg38, coverage,
missingness, lookup failures, score semantics, source versions, and artifact hashes. The fresh
approval must include the current ML protocol hash, the three formal manifest hashes, the combined
record-set hash, the 56-row cache-reuse verification hash, the current commit, exact model
revisions, H100, the `$8.00` hard cap, `$7.75` safety stop, and all excluded workloads.

The completed comparator qualification for this checkpoint is
`artifacts/phase6a/comparators/phase6a_comparator_qualification_20260921.json`; it records CADD
2,891/4,000 coverage, PhyloP 3,997/4,000 coverage, AlphaMissense zero eligible predictions,
`modal_invoked: false`, and `labels_read_for_scoring: false`. Do not replace its missing values
with zeros or labels.

Run the deterministic 64-row Evo2 preflight first:

```bash
EVOVARIANT_TR_PAID_COMPUTE_ACK=I_ACCEPT_COSTS \
  make formal-budgeted-evo2 FORMAL_LIMIT=64 FORMAL_SUFFIX=sample64
```

Inspect the resulting sample artifact for reference-allele parity, all four orientation views,
finite scores, shard hash/resume behavior, and measured cost. Continue with `FORMAL_SUFFIX=full`
only after the local gate below passes and the measured projection for the new 3,944-variant
workload plus the NT/Caduceus plan remains below `$8.00` and the runner safety stop is not crossed.
The full Evo2 runner reuses only
the 56 independently verified historical rows, sends no labels remotely, and writes atomic
resumable shards.

Materialize and validate the measured projection before the full run:

```bash
make formal-budgeted-preflight-verify
```

This writes `artifacts/phase6/formal_budgeted_preflight_gate_20260921.json`. The full runner
refuses to start unless that artifact is `PASS_FORMAL_PREFLIGHT_WITHIN_BUDGET` and its projected
cumulative additional cost is at or below the `$7.75` safety stop.

After formal Evo2 completes, run:

```bash
EVOVARIANT_TR_PAID_COMPUTE_ACK=I_ACCEPT_COSTS make formal-budgeted-representations
```

This extracts all predeclared NT layers 8/16/24 and Caduceus layers 4/8/16 in one forward pass
per shard, persists reference/alternate/orientation vectors and aggregate delta, absolute,
cosine, distance, and provenance fields, and joins labels locally only. Stop all workers and
refresh billing before beginning the local Phase 6-13 CPU matrix.

## Local downstream training and HPO

Once a verified Phase 7 development feature artifact exists, run CPU-only downstream work with
explicit paths:

```bash
make train FEATURES=research/runs/<features>/features.jsonl \
  TRAIN_OUTPUT=research/runs/<phase8-run>
make hpo FEATURES=research/runs/<features>/features.jsonl \
  HPO_CONFIGS=experiments/configs/<bounded-logistic-search>.json \
  HPO_OUTPUT=research/runs/<phase9-run>
```

The feature loader rejects locked-test rows, duplicate IDs, mixed model/layer artifacts, invalid
content hashes, and train/validation gene overlap. Generated metrics are validation-only and must
be registered as preliminary evidence only after immutable run metadata and output hashes are
checked. If `FEATURES` or `HPO_CONFIGS` is absent, the Make targets write blocked status artifacts
and do not infer a result.

## Ensemble, calibration, and abstention analysis

After a real development prediction artifact exists and member selection is frozen on validation,
run the local analysis with explicit model names:

```bash
make ensemble PREDICTIONS=research/runs/<phase8-run>/development_predictions.jsonl \
  ENSEMBLE_LEFT_MODEL=logistic_regression \
  ENSEMBLE_RIGHT_MODEL=mlp \
  ENSEMBLE_OUTPUT=research/runs/<phase11-run>/ensemble_analysis.json
```

The loader rejects locked-test rows by default and the output path is immutable. The resulting
artifact is preliminary engineering/scientific evidence only until its run metadata, hashes,
selection rule, and registry stage are reviewed. Do not tune weights or abstention thresholds
after reading locked-test metrics.

## Frozen locked evaluation

The Phase 14 evaluator is a one-shot reporting surface. It must receive a real, already-frozen
prediction artifact and configuration; it does not select a model, threshold, ensemble, or
calibration rule. The default command remains blocked and is safe to run:

```bash
make evaluate
```

After the protocol, model, HPO, ensemble, calibration, split, and output directory are frozen and
approved, provide every explicit input:

```bash
make evaluate \
  LOCKED_PREDICTIONS=research/runs/<locked-run>/predictions.jsonl \
  LOCKED_MODEL=<frozen-model-id> \
  LOCKED_CONFIG=research/runs/<locked-run>/frozen_config.json \
  LOCKED_CONFIG_HASH=<sha256-of-frozen-config> \
  LOCKED_OUTPUT=research/runs/<locked-run>/phase14_locked_evaluation.json
```

The evaluator requires only `LOCKED_TEST` rows for the selected model, both classes, a matching
configuration hash, `selection_closed=true`, and a new output path. It writes fixed-threshold
metrics and bootstrap AUROC provenance. Never use locked labels for post-test tuning, and never
reuse or overwrite an existing result artifact.

## Before commit

- tests,
- lint/typecheck,
- secret scan,
- inspect diff,
- no large accidental artifacts,
- docs updated.

## Recovery

If a run fails:
- classify failure,
- preserve logs,
- avoid automatic expensive retries,
- resume idempotently from completed shards.
