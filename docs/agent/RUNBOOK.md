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
