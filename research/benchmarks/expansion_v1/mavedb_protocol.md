# MaveDB functional-correlation protocol (B63)

Status at declaration: `PENDING_AUDIT`

This protocol is written before inspecting assay-level correlations. It is an
independent functional-effect analysis and must not be described as a clinical
pathogenicity benchmark.

## Eligibility

An assay is eligible only when an official MaveDB record provides a stable
assay identifier, a declared variant library, an assay-level score and score
direction, and enough metadata to distinguish the assayed reference build and
alleles. The assay must be a variant-level sequence/function measurement rather
than a proxy label copied from ClinVar.

## Mapping and overlap

The mapping must be variant-specific and reproducible from the official assay
record or its linked source data. Accepted mappings are exact GRCh38 SNV
identities or an explicitly documented reference-build conversion with a
one-to-one allele check. A row is not counted from a gene-only or protein-only
match. The predeclared minimum is 20 exact mapped variants per assay and at
least two distinct score values; otherwise the assay is `INSUFFICIENT_SUPPORT`.

## Direction and statistics

Score direction is taken from assay metadata or the linked publication, never
chosen from the observed correlation. Spearman correlation is computed between
the frozen EvoVariant-TR probability/raw score and the assay functional score,
with a deterministic seed-42 bootstrap 95% interval when the mapped set
supports it. No score rescaling is fitted to the external clinical labels.

## Clinical boundary

Functional effect is not equivalent to clinical pathogenicity. MaveDB labels
must never be used to fit the frozen classifier, fit the frozen isotonic
calibrator, choose the 0.50 threshold, or alter the ClinVar external cohort.

If a defensible exact mapping and score-direction record cannot be frozen, B63
remains `DATA_BLOCKED` with the official source, attempted mapping, and failure
reason recorded in `artifacts/benchmarks/mavedb_assay_manifest.json`.
