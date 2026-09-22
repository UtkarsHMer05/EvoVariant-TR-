# Ponytail whole-repository audit — 2026-09-22

Scope: source, scripts, tests, and control-plane files in the current checkout. This is a
read-only over-engineering review; it applies no cleanup.

## Result

No safe deletion or dependency replacement was identified that would preserve the scientific
contracts and reduce complexity without a larger correctness/provenance risk. The apparent
abstractions in the registry, scorer, phase runner, and publication renderer each have multiple
callers or enforce a real evidence boundary. The direct SVG renderer and standard-library audit
scripts are already the minimal dependency-light path for this repository.

The only concrete simplification candidate is the formatting-only final-newline hunk listed in
`PREEXISTING_DIRTY_CORE_DIFF_AUDIT.md`; it is not worth touching during a frozen-result audit.

Skipped: dependency removal, registry/scorer flattening, and renderer consolidation. Add such
changes only in a separate non-scientific refactor with fresh tests and a new reproducibility
manifest.
