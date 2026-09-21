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

The current registry records Evo2 as the only raw-score `INCLUDED` model.
Nucleotide Transformer and Caduceus are `SUBSET_ONLY`: their official checkpoints
passed real bounded embedding/logit smokes, but neither has the frozen GRCh38
alternate-minus-reference score contract. GPN and CADD are deferred by
compute/assets; PhyloP and AlphaMissense are deferred by compatibility or subset
definition. The full Phase 6 benchmark remains blocked by Phase 3 and the absent
raw-score-compatible multi-model protocol.
