# Adaptation Experiment Ledger

Study: POSTHOC-FOUNDATION-ADAPTATION-001
Protocol SHA-256: dce981aaf11425732c5bdc0e081117feb8a9e4e079c28c0529807e5bfe477a7f

| Stage | Status | Evidence | Selection/holdout access | Next dependency |
|---|---|---|---|---|
| Branch hygiene | PASS | BRANCH_HYGIENE.md, cleanup commit dd36ad7 | none | protocol |
| Manifest identity/invariants | PASS | exact hashes and local verification on 2026-09-22 | no locked rows | protocol |
| Protocol freeze | IN_PROGRESS | protocol.yaml | none | protocol hash and approval |
| Free-Colab execution contract | PENDING | artifacts/approvals/posthoc_adaptation_free_colab_20260922.json | none | environment |
| Environment compatibility | PENDING | environment.json | none | Caduceus smoke |
| Caduceus smoke | PENDING | artifacts/adaptation/caduceus_smoke.json | none | data preparation |
| Data preparation | PENDING | Drive/local sequence cache manifests | TRAIN/VALIDATION identities only | Caduceus baseline |
| Caduceus frozen baseline | PENDING | stage artifacts | TRAIN only | partial/full fine-tune |
| Caduceus partial fine-tune | PENDING | stage artifacts | TRAIN/CV only | full/HPO |
| Caduceus full fine-tune | PENDING | stage artifact or FULL_FINETUNE_RESOURCE_DEFERRED_T4 | TRAIN/CV only | HPO |
| Caduceus HPO | PENDING | Drive HPO state | TRAIN grouped CV only | final training |
| Caduceus final training | PENDING | checkpoint and hash | TRAIN only | holdout freeze |
| Caduceus holdout | PENDING | POST-HOC ADAPTATION HOLDOUT artifact | 801 once per final system | NT |
| NT frozen/PEFT | PENDING | stage artifact or RESOURCE_DEFERRED_T4 | TRAIN/CV then 801 once | analysis |
| Calibration | PENDING | TRAIN OOF calibrators | no holdout fit | abstention |
| Abstention | PENDING | OOF thresholds and holdout report | no holdout tuning | ensemble |
| Ensemble | PENDING | OOF fit and holdout report | no holdout fit | robustness |
| Ablations/robustness | PENDING | source artifacts | no 946; no holdout retuning | statistics |
| Statistics | PENDING | machine-readable CIs/comparisons | no selection after report | figures |
| Figures/tables | PENDING | inventory and gallery | none | Judge notebook/report |
| Judge notebook/report/README | PENDING | required deliverables | none | tests |
| Tests | PENDING | adaptation test suite | no locked loading | push |
| Push | PENDING | origin branch ref | none | complete |
