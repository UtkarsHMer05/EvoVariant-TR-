# Research Workbench UI Specification

## Navigation

- Overview
- Single Variant
- Temporal VUS Explorer
- Model Benchmark
- Representation Lab
- Training & HPO
- Fine-Tuning
- Ensemble
- Calibration & Abstention
- Robustness & Ablation
- Error Analysis
- Batch Analysis
- Methods & Provenance
- Experiment Registry

## Overview

Show:
- protocol version,
- cohort sizes,
- models registered,
- experiments completed,
- current evidence stage,
- latest final benchmark ID,
- research-only disclaimer.

## Model Benchmark

Table:
model, subset, n, coverage, AUROC, AUPRC, MCC, balanced accuracy, runtime, cost.

Charts:
ROC, PR, metric comparison, latency/cost.

## Training & HPO

Show:
- classifier type,
- feature source,
- layer/context,
- HPO trial history,
- chosen params,
- train/validation curves,
- no test results during selection view unless final freeze completed.

## Ensemble

Show:
- pairwise disagreement/error overlap,
- base-model validation metrics,
- ensemble method,
- weights/meta-model,
- final comparison.

## Calibration

Show:
- raw vs calibrated reliability,
- Brier/NLL/ECE,
- risk coverage,
- abstention thresholds selected on validation.

## Error Analysis

Filters:
- false positive/negative,
- gene,
- variant consequence,
- model disagreement,
- orientation instability,
- review status.

## Provenance

Every result:
- variant ID,
- assembly,
- model checkpoint,
- context,
- orientation,
- run ID,
- git commit,
- protocol hash,
- dataset hash,
- runtime,
- hardware.

## UI correctness

No synthetic/fake result may look like FINAL evidence.
Evidence stage must be visually explicit.

