# Contribution map

| contribution | implementation/evidence | claim boundary |
|---|---|---|
| temporal benchmark definition | `research/protocol/`, frozen manifests, phase reports | research benchmark; not clinical validation |
| orientation-aware allele scoring | `src/evovariant_tr/`, registered model contracts, Phase 14 receipt | frozen zero-shot Evo2 scoring contract |
| downstream comparison and HPO | `research/runs/formal_cpu_20260922/phase8/`, `phase9/`, final tables | TRAIN/VALIDATION development selection only |
| calibration, uncertainty, and abstention | phase 12–14 receipts and final figure sources | fit before locked evaluation; descriptive benchmark evidence |
| reproducibility and provenance | experiment registry, protocol gates, hash-checked receipts, `make` targets | local/registered artifact reproducibility, not fresh provider rerun |
| Caduceus adaptation implementation | `research/adaptation_attempt/source_snapshot/` | incomplete experimental appendix; no selected adapted model |
| encoder-update feasibility | `research/adaptation_attempt/artifacts/caduceus_partial_small_finetune_smoke.json` | one-step proof only; not completed foundation-model fine-tuning |

The frozen baseline remains the primary contribution. The adaptation work is preserved as a transparent follow-up attempt so future work can resume without confusing feasibility evidence with a scientific result.
