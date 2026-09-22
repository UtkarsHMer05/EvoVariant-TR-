# Adaptation Experiment Ledger

Study: `POSTHOC-FOUNDATION-ADAPTATION-001`
Protocol SHA-256: `07c93b4657e84a4ddfbdc2df1af0f467f80959e0534a67840b4bf2b2b04a2c2c`

| Stage | Status | Evidence | Selection/holdout access | Next dependency |
|---|---|---|---|---|
| Branch hygiene | PASS | `BRANCH_HYGIENE.md`; cleanup commit `dd36ad7`; refs rechecked | none | protocol |
| Protocol freeze | PASS | `PROTOCOL.md`, `protocol.yaml`, SHA-256 above | none | execution |
| Free-Colab contract | PASS | `artifacts/approvals/posthoc_adaptation_free_colab_20260922.json` | none | environment |
| Environment | PASS | Drive `state/environment.json`: T4, Python 3.11.16, Torch 2.2.0+cu121, CUDA 12.1, NumPy 1.26.4 | none | smoke/data |
| Manifest identities | PASS | Drive `state/manifests_verified.json`; pinned hashes and zero gene/ID overlap | identities only; zero locked-ID overlap | reference |
| Reference/REF validation | PASS | Drive `state/data_ready.json`; all 4,000 development REF alleles match GRCh38 | no locked rows loaded | smoke |
| Caduceus smoke | PASS | Drive `runs/caduceus_smoke.json`, checkpoint SHA `da541bb2…04c9042` | no cohort evaluation | frozen head |
| Caduceus frozen head | IN_PROGRESS | Drive `checkpoints/caduceus_frozen_head/latest.pt`, `latest.json`; epoch 0 loss `1.1767539545572263`, 8,192 bp, seed 42 | TRAIN only | finish 3 epochs |
| Caduceus partial fine-tune | NOT STARTED | no artifact | none | frozen baseline |
| Caduceus full fine-tune | NOT STARTED | no artifact | none | feasibility/HPO |
| Caduceus HPO | NOT STARTED | no SQLite/trial summary yet | TRAIN grouped CV only | frozen baseline |
| Final TRAIN refit | BLOCKED | no closed selection lock | none | HPO |
| 801 holdout | CLOSED | evaluator requires selection lock; no output exists | no labels used | final refit |
| NT frozen / PEFT | NOT STARTED | no adaptation result artifacts | none | Caduceus results |
| Calibration / abstention | IMPLEMENTATION IN PROGRESS | TRAIN-OOF calibration and selective-metric helpers under validation | no holdout fit | OOF predictions |
| Ensemble / robustness / ablations | NOT STARTED | no adaptation prediction files | none | model outputs |
| Statistics / figures / report | NOT STARTED | no model results to plot | none | predictions |
| Judge notebook | IMPLEMENTED, RESULT CELLS PENDING | 36 ordered sections; canonical code source display | no locked data access | training outputs |
| Local validation | PASS | `make validate`: 734 passed, 33 deselected, 95.07% core coverage | software-only | commit |
| Adaptation branch push | PENDING | current source/notebook changes are local and uncommitted | none | commit and push |

No holdout or locked-test result is inferred from training progress or the smoke test.
