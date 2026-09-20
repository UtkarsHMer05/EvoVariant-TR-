# Experiment Plan — EvoVariant-TR ML Extension

## Experiment naming

Use stable IDs:
- `ZS-*` zero-shot
- `REP-*` representation
- `CLF-*` downstream classifiers
- `HPO-*`
- `FT-*`
- `ENS-*`
- `CAL-*`
- `ABS-*`
- `ABL-*`
- `ROB-*`
- `STAT-*`

## Development ladder

### Level 0 — software correctness
Fake/synthetic fixtures only.

### Level 1 — paid engineering pilot
1–10 real variants.

### Level 2 — development pilot
small multi-gene sample.

### Level 3 — development cohort
train/validation only.

### Level 4 — locked final test
run only after freeze.

## Zero-shot benchmark matrix

For each included predictor record:
- checkpoint,
- context,
- orientation,
- scoring semantics,
- raw score,
- score direction,
- coverage,
- runtime,
- memory,
- cost.

## Representation matrix

For embedding-capable models:
- layer indices chosen by protocol,
- pooling strategies,
- ref embedding,
- alt embedding,
- difference,
- absolute difference,
- cosine/distance,
- raw score appended or not.

## Classifier matrix

At minimum:
- logistic regression,
- tree model,
- MLP.

Compare:
- raw score only,
- embedding difference only,
- embeddings + raw score,
- multi-model features.

## HPO

Pilot search first.
Then bounded full search based on measured trial speed.

Store:
- trial params,
- intermediate metrics,
- pruning status,
- runtime,
- selected reason.

## Fine-tuning

Sequence:
1. tiny smoke,
2. development subset,
3. selected full development,
4. final locked test only after freeze.

Possible outcomes:
PASS_IMPROVED
PASS_NO_IMPROVEMENT
PASS_WORSE
FAILED_TECHNICAL
DEFERRED_BY_COMPUTE

All are valid research outcomes.

## Ensemble experiments

Input candidates selected from validation.

Measure diversity before ensemble.
Then test:
- mean,
- weighted mean,
- majority/soft vote,
- OOF stacking.

## Calibration

Compare:
- uncalibrated,
- Platt,
- isotonic sensitivity.

## Abstention

Choose rule on validation.
Plot:
risk vs coverage and metric vs coverage.

## Ablations

Required:
- FWD only vs RC only vs aggregate,
- context,
- ensemble member removal,
- feature family removal,
- calibration effect.

## Learning curves

Grouped train subsets:
10/20/40/60/80/100% or another protocol-frozen sequence.

## Subgroups

Only report subgroup metrics with n.
Flag small groups and wide uncertainty.
Do not rank genes based on tiny samples.

