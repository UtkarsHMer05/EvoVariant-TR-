# Architecture — EvoVariant-TR ML Extension

## Layering

### 1. Core scientific layer
Pure/testable Python:
- variant normalization,
- sequence windows,
- mutation,
- reverse complement,
- cohort/splits,
- metrics,
- calibration,
- ensemble math,
- registry schemas,
- feature schemas.

Must be importable without GPU/cloud.

### 2. Model adapters
Each predictor implements a common conceptual interface:
- metadata,
- availability,
- preprocessing,
- score,
- optional embedding extraction,
- optional training capability,
- health check.

Model-specific dependencies stay isolated.

### 3. Feature store
Keyed by immutable provenance:
`model/checkpoint/preprocessing/context/orientation/layer/variant`.

Store:
- scores,
- embeddings,
- feature summaries,
- hashes.

### 4. Training
Reusable pipelines:
- preprocessing fitted on train only,
- model fit,
- validation,
- HPO,
- checkpoint,
- history,
- registry write.

### 5. Evaluation
- metrics,
- bootstrap,
- paired comparisons,
- calibration,
- risk coverage,
- subgroup analysis,
- errors,
- ablations.

### 6. Modal transport
Responsible for:
- GPU container,
- model cache,
- batching,
- feature extraction,
- selected training,
- retries,
- telemetry.

Not responsible for inventing scientific thresholds.

### 7. API
Serves registered research results and submits validated analysis jobs.

### 8. Web
Displays API/registry data.
No scientific computation in React/route handlers beyond presentation-safe transforms.

## Data flow

Variant/data cohort
→ normalization
→ reference validation
→ sequence construction
→ model adapter(s)
→ raw score/embedding cache
→ downstream training/HPO
→ frozen selected model
→ calibration/ensemble
→ evaluation registry
→ figures/API
→ web dashboard.

## Security boundary

Secrets:
- Modal auth local config/secret store,
- never browser/public env,
- never committed.

## Large artifact boundary

Git:
configs/manifests/hashes/summaries.

External/volume:
raw ClinVar, FASTA, checkpoints, embeddings, large prediction tables.

