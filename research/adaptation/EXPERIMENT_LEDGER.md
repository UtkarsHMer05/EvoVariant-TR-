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
| Caduceus frozen head | PASS | Drive `checkpoints/caduceus_frozen_head/run.json`; 3 epochs, losses `1.1767539545572263`, `1.1581548454985837`, `1.1497443100928366`, runtime 1,968.52 s; checkpoint SHA `230fc7be…4e02213`, 7,728,385 total / 3,073 trainable parameters, peak 320,895,488 bytes | TRAIN only; report says holdout not evaluated | partial/full feasibility and HPO |
| Caduceus partial fine-tune | NOT STARTED | no artifact | none | frozen baseline |
| Caduceus full fine-tune | NOT STARTED | no artifact | none | feasibility/HPO |
| Caduceus HPO | IN_PROGRESS | Existing T4 worker PID 58018 at 2:01:25; trial 0 RUNNING, trials 1–3 WAITING; fold 0 four epochs and fold 1 three persisted | TRAIN-only, 3-fold gene-grouped CV; selection open | complete at least 8 trials |
| Frozen Evo2 anchor audit | EXCLUDED_PENDING_PROVENANCE | Existing 4,000-row output matches development IDs/splits, prediction hash, model revision, and locked exclusion; producer checkout is marked dirty, and the full-run approval referenced in its plan is unavailable | ID/split/hash audit only; score and label values not inspected or used | recover exact producer source and approval provenance, otherwise retain exclusion |
| Final TRAIN refit | BLOCKED | no closed selection lock | none | HPO |
| 801 holdout | CLOSED | evaluator requires selection lock; no output exists | no labels used | final refit |
| NT frozen / PEFT | NOT STARTED | no adaptation result artifacts | none | Caduceus results |
| Calibration / abstention | IMPLEMENTATION IN PROGRESS | TRAIN-OOF calibration and selective-metric helpers under validation | no holdout fit | OOF predictions |
| Seed robustness | IMPLEMENTED_AWAITING_RUNS | Final trainer/evaluator accept only protocol-fixed robustness seeds 1337/2026 with the selection lock; no result files yet | no holdout use | HPO selection and final fit |
| Ensemble / ablations | NOT_STARTED | no adaptation prediction files | none | model outputs |
| Statistics / figures / report | NOT STARTED | no model results to plot | none | predictions |
| Judge notebook | IMPLEMENTED, RESULT CELLS PENDING | 36 ordered sections; canonical code source display | no locked data access | training outputs |
| Local validation | PASS | `make validate` at `a2f500f`: 736 passed, 33 deselected, 95.06% core coverage | software-only | continue study |
| Adaptation branch push | PASS | metric/README update `a2f500f` pushed after fixed-seed notebook gate `44ac317`; `main` and baseline tag unchanged | none | continue study |

No holdout or locked-test result is inferred from training progress or the smoke test.
