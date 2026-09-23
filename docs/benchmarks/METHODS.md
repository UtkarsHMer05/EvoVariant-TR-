# Methods

The benchmark expansion reuses only registered GRCh38 ClinVar, frozen-model,
representation-cache, comparator, and downstream-prediction artifacts. The
formal development cohort has 4,000 rows and the immutable temporal locked
cohort has 946 rows. Variant IDs are disjoint before analysis.

Evidence quality is grouped by ClinVar review-status stars. Temporal
difficulty uses T0-to-T1 LastEvaluated dates and fixed bins of <=180,
181-365, 366-545, >545, and missing/invalid days. LOCO fits a scaled logistic
classifier on cached Evo2 features with one chromosome held out. Disagreement
uses common validation rows and does not fit on the locked cohort. Case studies
are deterministic selections from the frozen locked artifact.

The external ClinVar manifest is frozen before inference. It excludes formal
and locked IDs and genes. The verified continuation used the local GRCh38
reference FASTA, persisted label-free Evo2 raw scores, and only then joined
labels for evaluation; it did not refit the downstream classifier or
calibrator.
