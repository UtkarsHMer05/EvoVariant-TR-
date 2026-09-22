# DEVIATION LOG — EvoVariant-TR research protocol

Any change to an immutable protocol field, or any predeclaration made after seeing
temporal performance, must be recorded here with a date. A protocol change that
changes the estimand is never called a bugfix.

Format for entries:

```text
## DEV-YYYY-NNN — <title>
- Date: YYYY-MM-DD
- Protocol version affected: x.y.z
- What changed:
- Why:
- Impact on estimand:
- Approved by:
```

---

## DEV-2026-001 — Scoped chrY PAR hard-mask sequence-extraction alias
- Date: 2026-09-22
- Protocol version affected: v1.0.0; additive ML-DEV-BUDGETED-001 Phase 6 reference-handling deviation
- What changed: For sequence-model context extraction only, the two verified formal records
  `GRCh38:Y:1286043:T>C` and `GRCh38:Y:1309674:G>T` may use the same-coordinate chrX PAR1
  sequence when the frozen Broad/GATK GRCh38 analysis-set chrY context is hard-masked. The
  original chrY locus, normalized ID, label, split, and all scientific provenance remain
  unchanged. This is not a chromosome remapping or a record-identity change.
- Why: GATK documents that the GRCh38 analysis set hard-masks chrY PARs. Both loci are inside
  official GRCh38 PAR1, both homologous chrX bases match the manifest REF, and both complete
  8,192-bp unmasked hg38 X/Y windows are identical. The frozen chrY windows are all `N`.
- Guard conditions: The alias is valid only for an officially defined PAR locus with a masked
  chrY reference, a matching homologous chrX REF, a complete context inside the homologous PAR,
  and deterministic independent validation. It is not valid for ordinary mismatches or the
  separately audited mitochondrial contexts containing an `N`.
- Impact on estimand: None. Formal identities, normalized IDs, splits, labels, record count,
  locked-test boundary, context length, model, orientation, and score semantics are unchanged;
  only the sequence source used to construct the two model contexts differs.
- Approved by: User-authorized Phase 6 continuation prompt on 2026-09-22; detailed decision
  record D-095; evidence `artifacts/reference/par_mask_resolution_20260922.json`.
