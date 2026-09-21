# ML-extension model registry

The JSON files in this directory are candidate manifests, not model results. They
are schema-validated by `make model-registry-verify` and intentionally keep
unverified candidates visible.

`SUBSET_ONLY`, `DEFERRED_BY_COMPUTE`, `DEFERRED_BY_COMPATIBILITY`, `PLANNED`, and
`INFEASIBLE` candidates may not be included in the raw-score benchmark. An
`INCLUDED` or `AVAILABLE` candidate must have `provenance.verification_status` set
to `VERIFIED`, an official source/checkpoint/revision, a declared input and score
contract, and a recorded tiny parity/smoke result. No manifest causes a model
package or checkpoint to download as a side effect.

The operational registry records Evo2 as the only raw-score `INCLUDED` model because it
has a verified end-to-end raw-score pilot. The final Phase 5 roster is recorded separately
in `artifacts/model_audit/phase5_final_roster_20260921.json`: Nucleotide Transformer and
Caduceus are promoted to separately labeled `INCLUDED_EMBEDDING_TRACK` decisions for a
future supervised representation phase, while their masked-LM logits remain `SUBSET_ONLY`
for the exact Phase 6 raw-score comparison. CADD and PhyloP have public, CPU-lookup
comparator contracts identified, but their assets, hashes, and cohort missingness must be
manifested before use. GPN remains deferred by its required alignment asset, and AlphaMissense
remains subset-only for applicable missense records. The full Phase 6 benchmark remains
blocked until the Phase 3 gate and a fresh scope-specific approval pass.
