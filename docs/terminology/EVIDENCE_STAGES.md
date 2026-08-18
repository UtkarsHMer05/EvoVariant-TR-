# EVIDENCE STAGES — EvoVariant-TR (Milestone 007)

Every run, result, table, figure, and UI metric carries exactly one evidence stage.
The stage controls where an output may be written, how it may be labeled, and
whether it may be cited. Promotion is a deliberate, logged act — never automatic.

## Stage definitions

| Stage | Meaning | May be cited as EvoVariant-TR science? | Typical source |
|---|---|---|---|
| `SYNTHETIC_TEST` | Deterministic fake output used to exercise software (fake scorer, fixtures). Proves plumbing, not science. | No | Unit/integration tests, fake-scorer pipelines |
| `LEGACY_BASELINE` | Saved outputs of the OLD project (e.g. `evaluation/results/final_100`). Engineering baseline only; different estimand, assembly, and threshold. | No | Imported snapshot artifacts |
| `ENGINEERING_PILOT` | Real model runs that validate infrastructure (model load, parity, one-variant, small pilots). Not performance evidence. | No (only as engineering provenance) | Modal smoke/parity/pilot runs |
| `PRELIMINARY` | Registered real runs produced before the final freeze/approval. May be inspected internally but not promoted to final claims. | Only as explicitly-labeled preliminary | Pre-approval scoring/analysis |
| `FINAL` | Frozen, approved, fully-provenanced primary results from the registered full run and frozen analysis plan. | Yes (with stated limitations) | Post-approval primary analysis |

## Rules

1. **Attachment:** every run record and result artifact records its `evidence_stage`.
2. **No silent promotion:** an output's stage can only change via an explicit,
   logged action that records who/what promoted it and why.
3. **Write-path enforcement:** `SYNTHETIC_TEST` and `LEGACY_BASELINE` outputs must
   not be written to final-results directories or aggregate result tables. This is
   enforced in code (Milestone 13) and tested.
4. **No legacy mixing:** legacy BRCA1 metrics must never enter EvoVariant-TR
   aggregate tables or figures.
5. **Serialization survives:** the stage label must survive JSON/CSV/Parquet
   round-trips.
6. **UI display:** user-facing surfaces show the stage of every metric they render.
7. **Dirty-tree guard:** a `FINAL` run requires a clean git tree (or an explicit,
   recorded non-final override) — enforced by the registry (Milestone 14).

## Forbidden promotions (tested at Milestone 13)

- Writing a `SYNTHETIC_TEST` result into a `FINAL` results path.
- Registering a fake-scorer run as `PRELIMINARY` or `FINAL`.
- Merging a `LEGACY_BASELINE` metric into a primary results table.
- Relabeling an `ENGINEERING_PILOT` AUROC as a research finding.
