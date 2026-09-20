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

