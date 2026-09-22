# Adaptation Decisions

Study: POSTHOC-FOUNDATION-ADAPTATION-001
Protocol: research/adaptation/protocol.yaml
Protocol SHA-256: 07c93b4657e84a4ddfbdc2df1af0f467f80959e0534a67840b4bf2b2b04a2c2c

| ID | Decision | Rationale | Status |
|---|---|---|---|
| D-A001 | Keep adaptation separate from the frozen zero-shot baseline. | Prevents protocol and metric-stage conflation. | FROZEN |
| D-A002 | Use the exact committed 4,000/3,199/801 manifests. | Preserves authorized gene-held-out identities and hashes. | FROZEN |
| D-A003 | Treat the 946 temporal cohort as historical-only and never use it for adaptation selection. | Absolute locked-test rule. | FROZEN |
| D-A004 | Use Caduceus-Ph as primary, NT v2 500M as secondary, and Evo2 7B only as a frozen same-split anchor. | Matches the requested study contract and free-T4 boundary. | FROZEN |
| D-A005 | Select paired representation, orientation, HPO, seeds, epochs, calibration, abstention, and ensemble rules from TRAIN-only evidence. | Prevents holdout leakage. | FROZEN |
| D-A006 | Average forward and reverse-complement logits; do not treat orientations as independent samples. | Preserves strand handling without inflating n. | FROZEN |
| D-A007 | Use free Colab/local resources only; defer rather than fabricate any resource-infeasible result. | Paid compute is prohibited. | FROZEN |
| D-A008 | Evaluate the 801 holdout once per predeclared final system after selection closes. | Preserves the terminal holdout boundary. | FROZEN |
| D-A009 | Use gene-aware paired bootstrap and Holm correction for uncertainty/comparisons. | Accounts for grouped identities and multiple primary comparisons. | FROZEN |
| D-A010 | Keep canonical ML logic in source files and make the Judge notebook render it with inspect.getsource/source inspection. | Makes fine-tuning auditable. | FROZEN |
| D-A011 | Compare uncalibrated, temperature, Platt, and isotonic calibration from TRAIN OOF predictions; derive selective risk at predeclared coverage from confidence alone. | Implements the already-frozen calibration/abstention contract without opening VALIDATION. | FROZEN |

## Open operational items

1. Frozen-head run completed: 3 TRAIN-only epochs; Drive `run.json` records the checkpoint and no holdout evaluation.
2. Continue TRAIN-only grouped HPO from Drive checkpoints/SQLite; never start holdout evaluation before selection closes.
3. Mark Caduceus full fine-tuning and NT workloads with measured feasibility or explicit T4 resource deferral.
4. Generate analysis, figures, report, README updates, and push only from persisted, verified outputs.
