# Risks and Limitations

Track throughout development.

## Scientific
- ClinVar resolution is not identical to biological truth.
- Temporal test is conditional on eventual reclassification.
- Review-status filtering changes the evaluated population.
- Some comparator scores cover only subsets.
- Gene/subgroup sample sizes can be small.
- HPO can overfit development validation.
- Foundation-model score direction may not map monotonically to clinical interpretation.
- Embeddings can encode dataset artifacts.

## Engineering
- model dependency conflicts,
- GPU memory,
- Modal cost overruns,
- cache corruption/staleness,
- public source schema changes,
- frontend/API schema drift.

## Interpretation
- calibrated study probability is not a patient risk probability.
- a higher AUROC does not imply clinical utility.
- statistical significance does not imply practical significance.
- ensemble opacity must be balanced with explainability.

## Mitigations
- protocol freeze,
- hashes,
- grouped splits,
- locked test,
- independent caches,
- explicit missingness,
- bootstrap uncertainty,
- cost gates,
- clean-room reproduction.

