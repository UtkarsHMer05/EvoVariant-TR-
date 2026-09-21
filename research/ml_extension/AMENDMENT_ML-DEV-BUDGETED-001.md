# ML-DEV-BUDGETED-001 — Budgeted development-study amendment

Date: 2026-09-21
Status: FROZEN FOR LOCAL DESIGN; NO NEW MODAL COMPUTE AUTHORIZED

This dated amendment is additive to the frozen ML-extension protocol. It does
not rewrite the authoritative development population, the original split
manifest, the 946-record `LOCKED_TEST`, or the previously generated
development-prefix history.

## Scope and reason

- The available development population is exactly 239,992 records from the
  manifest-verified TRAIN/VALIDATION split.
- The existing 2,848-record Evo2 run remains `PRELIMINARY` evidence. It was an
  ascending `SHA256(normalized_variant_id)` prefix stopped by the paid-compute
  reserve. Its metadata audit is descriptive and does not establish
  representativeness.
- Foundation-model scoring and representation extraction will use a new
  deterministic budgeted subset because scoring all 239,992 records is not
  financially justified under the current compute envelope.
- The 946 temporal variants remain the untouched `LOCKED_TEST`. This amendment
  is based on computational budget, not on locked-test performance.

## Frozen formal subset rule

Study identifier: `ML-DEV-BUDGETED-001`
Target size: 4,000 records, never above 5,000 without a new approval.
Sampling seed: `ML-DEV-BUDGETED-001|2026-09-21|sha256-v1`

Within each frozen TRAIN/VALIDATION and label stratum, rank records by:

```text
SHA256(normalized_variant_id + "|" + sampling_seed)
```

Select the deterministic largest-remainder allocation proportional to the
239,992-record population. This preserves the frozen split boundary and the
natural class proportions up to integer allocation. No model predictions are
read during selection. The exact generated manifests, source hash, selected
IDs, allocation, and overlap with the old prefix are recorded under
`research/ml_extension/splits/formal_budgeted_20260921/`.

The subset must retain the following invariants:

- no normalized-ID duplicates;
- zero overlap with `LOCKED_TEST`;
- no TRAIN/VALIDATION gene overlap;
- GRCh38 SNV eligibility and original labels from the frozen development
  manifest;
- the same exact formal manifest across every model track and classifier.

## Formal experiment matrix after a fresh compute approval

Track A zero-shot/raw-score evidence: Evo2, CADD, and PhyloP. AlphaMissense
remains an eligible-subset analysis only. Track B frozen representations:
Evo2 raw-score features, Nucleotide Transformer, and Caduceus. Evo2 embeddings
are optional and require a separately justified incremental estimate.

For NT and Caduceus, the candidate intermediate layers are frozen before any
selection: NT layers `8, 16, 24`; Caduceus layers `4, 8, 16`. An unavailable
layer fails closed and is not replaced after observing locked-test results.
Each model uses the same formal TRAIN/VALIDATION records, labels, and
downstream classifier matrix: logistic regression, a tree/boosting classifier,
and MLP. HPO runs only on cached representations; the foundation models are
not rerun per trial. Ensemble, calibration, abstention, and learning-curve
rules remain validation-only as specified in the parent protocol.

Phase 10 remains `DEFERRED_BY_COMPUTE`. No fine-tuning or PEFT run is
authorized by this amendment; a later feasibility proposal must state model,
method, dataset, GPU, runtime, cost, and expected scientific value first.

## Authorization boundary

This amendment authorizes only local audit, deterministic manifest generation,
QC, protocol/decision documentation, and cost estimation. It authorizes no
Modal invocation, no model download, no training, no HPO, no feature
extraction, no comparator run, and no locked-test access. A fresh exact-scope
compute approval is required after review of `cost_estimate.json`.
