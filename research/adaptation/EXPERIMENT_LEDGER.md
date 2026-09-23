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
| Caduceus HPO | WAITING_FOR_FREE_GPU | Earlier verified checkpoint evidence is in `HPO_RECOVERY_REPORT.md`. Latest default-account poll: snapshot copy integrity `ok`, trial 0 RUNNING / trials 1–3 WAITING, histories 4 / 3, frozen report PASS; expected source shortcut and recovery-copy manifest are absent, so this root is not accepted as a verified resume source. Colab denied T4 due to usage limits. | TRAIN-only, 3-fold gene-grouped CV; selection open; no completed trial | Restore/verify default-account recovery provenance, then reverify checkpoint bindings on an eligible free T4; resume fold 1 completion boundary, then fold 2 epoch 1 |
| Frozen Evo2 anchor audit | EXCLUDED_PENDING_PROVENANCE | Existing 4,000-row output matches development IDs/splits, prediction hash, model revision, and locked exclusion; producer checkout is marked dirty, and the full-run approval referenced in its plan is unavailable | ID/split/hash audit only; score and label values not inspected or used | recover exact producer source and approval provenance, otherwise retain exclusion |
| Final TRAIN refit | BLOCKED | no closed selection lock | none | HPO |
| 801 holdout | CLOSED | evaluator requires selection lock; no output exists | no labels used | final refit |
| NT frozen / PEFT | NOT STARTED | no adaptation result artifacts | none | Caduceus results |
| Calibration / abstention | IMPLEMENTATION IN PROGRESS | TRAIN-OOF calibration and selective-metric helpers under validation | no holdout fit | OOF predictions |
| Seed robustness | IMPLEMENTED_AWAITING_RUNS | Final trainer/evaluator accept only protocol-fixed robustness seeds 1337/2026 with the selection lock; no result files yet | no holdout use | HPO selection and final fit |
| Ensemble / ablations | NOT_STARTED | no adaptation prediction files | none | model outputs |
| Statistics / figures / report | NOT STARTED | no model results to plot | none | predictions |
| Judge notebook | IMPLEMENTED, RESULT CELLS PENDING | 36 ordered sections; canonical code source display | no locked data access | training outputs |
| Notebook recovery | PASS_CONTENT, PREFLIGHT_BLOCKED | Same Colab Drive ID retains 20 cells/10 sections and the raw 78-cell archive. Default-account preflight mounted Drive, then failed closed because the expected source shortcut and recovery-copy manifest are absent. Current diagnostic outputs are saved; no training cell ran. | no holdout or locked-test access | restore/verify authorized Drive provenance and request an eligible free T4 |
| Local validation | PASS | `make validate` on 2026-09-23: 737 passed, 33 deselected, 95.07% core coverage; secret scan, Ruff, and strict mypy passed (67 files) | software-only | continue study |
| Adaptation branch push | PASS | metric/README update `a2f500f` pushed after fixed-seed notebook gate `44ac317`; `main` and baseline tag unchanged | none | continue study |

No holdout or locked-test result is inferred from training progress or the smoke test.
