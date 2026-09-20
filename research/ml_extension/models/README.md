# ML-extension model registry

The JSON files in this directory are candidate manifests, not model results. They
are schema-validated by `make model-registry-verify` and intentionally keep
unverified candidates visible.

`PLANNED` and `DEFERRED` candidates may not be included in a benchmark. An
`INCLUDED` or `AVAILABLE` candidate must have `provenance.verification_status` set
to `VERIFIED`, an official source/checkpoint/revision, a declared input and score
contract, and a recorded tiny parity/smoke result. No manifest causes a model
package or checkpoint to download as a side effect.

The current registry therefore records Evo2 as the required planned candidate and
the other foundation/specialized candidates as feasibility-review candidates.
All scientific model execution remains blocked by the Phase 3 cohort discrepancy
and the Phase 4 paid Modal pilot gate.
