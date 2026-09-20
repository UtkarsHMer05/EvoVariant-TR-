# Testing and Validation Plan

## Gate philosophy

Code existence is not completion. Each phase has executable evidence.

## Python quality

- pytest
- coverage consistent with existing repo policy
- ruff
- mypy strict for core modules where configured

## Web quality

- npm clean install
- typecheck
- lint
- production build
- targeted unit/component tests if configured
- E2E critical journeys

## Scientific invariants

Required tests:
- `end-start == context_length`
- sequence length exact
- reference base matches variant
- alt sequence differs at exactly intended locus for SNV
- RC transform is correct
- no train/test normalized-ID overlap
- no validation/test overlap
- no scaler/imputer/calibrator fit on test
- deterministic split rebuild
- model score direction metadata present
- all result rows link to provenance
- frontend does not calculate scientific threshold

## Model adapter tests

For each model:
- import/load,
- tiny input,
- deterministic or tolerance-defined output,
- shape,
- score finite,
- metadata,
- batch equivalence where appropriate,
- error handling.

## Training tests

- tiny dataset overfit test,
- checkpoint save/load,
- seed reproducibility within tolerance,
- early stopping,
- no test access,
- HPO trial persistence.

## Ensemble tests

- OOF generation has no self-training leakage,
- stacker feature matrix correct,
- weights sum/constraints correct if required.

## Calibration tests

- calibrator fit only on allowed split,
- probabilities finite/in range,
- serialization roundtrip.

## Registry tests

- schema validation,
- immutable FINAL records,
- hashes,
- artifact existence.

## Modal tests

Never default.
Must be explicitly paid-compute gated.

## Negative/failure tests

- invalid allele,
- reference mismatch,
- chromosome edge,
- unsupported variant,
- model unavailable,
- OOM classification,
- network/source failure,
- partial batch failure,
- stale cache,
- incompatible checkpoint.

## Clean-room test

From fresh clone:
- install,
- deterministic core test,
- data fixture pipeline,
- web build,
- registry verify,
- figure regeneration,
- optional gated Modal smoke.

