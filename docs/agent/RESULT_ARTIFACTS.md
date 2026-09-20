# Result Artifact Contract

## Directory example

```text
experiments/runs/<run_id>/
  config.yaml
  manifest.json
  environment.json
  predictions.parquet
  metrics.json
  timing.json
  cost.json
  logs/
  figures/
```

## Predictions

Minimum columns:
- normalized_variant_id
- split
- label if permitted for artifact
- model_name
- raw_score
- probability if calibrated
- prediction if a research threshold is defined
- abstained
- coverage_status
- failure_reason

Model-specific fields live in namespaced columns or sidecars.

## Metrics JSON

Must include denominators and confidence intervals.

## Final immutability

Once a run is marked FINAL:
- do not overwrite;
- generate a new run ID for changes.

