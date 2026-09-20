# Product Requirements Document — EvoVariant-TR ML Extension

## Product statement

EvoVariant-TR is a research platform for evaluating genomic foundation-model signals against
the later resolution direction of historically uncertain ClinVar variants, and for studying
whether frozen representations, supervised adaptation, and ensembles improve discrimination
under leakage-controlled temporal evaluation.

## User-visible problem

The legacy visible workflow can appear to be:
variant input → existing model → score → benign/pathogenic-like label.

That presentation hides the actual research depth and makes the system look like a wrapper
around an upstream model.

The upgraded product must visibly demonstrate:
- dataset methodology,
- multi-model benchmarking,
- trainable ML contribution,
- hyperparameter optimization,
- calibration,
- ensemble methodology,
- robustness,
- statistical uncertainty,
- errors/limitations,
- provenance,
- reproducibility.

## Primary users

1. College project-review panel.
2. Student/researcher inspecting genomic foundation-model behavior.
3. Developer reproducing the benchmark.
4. Future contributor extending predictors or analysis.

## Core capabilities

### P0
- canonical variant representation,
- exact sequence generation,
- Evo2 FWD/RC scoring,
- temporal cohort reproducibility,
- leakage-safe splits,
- experiment registry,
- Modal cost control,
- multi-model common interface,
- benchmark metrics,
- downstream ML,
- HPO,
- result provenance.

### P1
- fine-tuning/PEFT feasibility,
- ensembles,
- calibration/abstention,
- robustness and ablations,
- batch VCF/CSV,
- complete research dashboard,
- generated figures/tables.

### P2
- advanced attribution on downstream model,
- optional local mutation scan,
- extra model families,
- richer report exports.

## Explicit non-goals

- Clinical diagnosis.
- Patient-specific treatment recommendations.
- Claiming ClinVar resolution is ground-truth biological causality.
- Guaranteeing fine-tuning improves performance.
- Guaranteeing ensembles improve performance.
- Spending beyond configured compute budget without approval.
- Manually typing benchmark numbers into frontend code.

## Success criteria

Engineering:
- clean install,
- tests pass,
- reproducible commands,
- no secrets,
- reliable Modal pilots,
- resumable batch jobs,
- generated UI from real artifacts.

Scientific:
- split leakage tests pass,
- test set remains locked,
- model identities/checkpoints recorded,
- all metrics are reproducible,
- uncertainty reported,
- negative results preserved,
- no unsupported claim.

Academic-demo:
Reviewer can navigate:
1. temporal cohort,
2. model benchmark,
3. training/HPO,
4. ensemble,
5. calibration,
6. robustness/ablation,
7. errors,
8. batch pipeline,
9. provenance.

