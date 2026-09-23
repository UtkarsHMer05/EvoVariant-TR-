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
| Caduceus HPO | WAITING_FOR_FREE_GPU | Histories/checkpoints are consistent at folds 0/1/2 = 4/3/2 epochs; all latest/best checkpoints pass protocol/fold/signature/model-revision/TRAIN-manifest/reference binding. Fold-2 latest SHA `067579471de3b420f0cbf7d0f765ad5a0fadb3bb5f172b6ee1dfae79aa82ad29`; best SHA `27663f7692be220457a44d1bdd62f21f423c4cc359d059d6cb4bec948f8b8e83`. After the worker stopped, a copied SQLite snapshot still passed integrity `ok`; trial 0 remains RUNNING and trials 1–3 WAITING. Parent PID 11483 and child PID 11573 were stopped at 08:05 UTC after the Colab FAQ account-limit rule was checked. | TRAIN-only, 3-fold gene-grouped CV; selection open; holdout closed | Resume trial 0 fold 2 epoch 3 only with provider-compliant free compute |
| Frozen Evo2 anchor audit | EXCLUDED_PENDING_PROVENANCE | Existing 4,000-row output matches development IDs/splits, prediction hash, model revision, and locked exclusion; producer checkout is marked dirty, and the full-run approval referenced in its plan is unavailable | ID/split/hash audit only; score and label values not inspected or used | recover exact producer source and approval provenance, otherwise retain exclusion |
| Final TRAIN refit | BLOCKED | no closed selection lock | none | HPO |
| 801 holdout | CLOSED | evaluator requires selection lock; no output exists | no labels used | final refit |
| NT frozen / PEFT | NOT STARTED | no adaptation result artifacts | none | Caduceus results |
| Calibration / abstention | IMPLEMENTATION IN PROGRESS | TRAIN-OOF calibration and selective-metric helpers under validation | no holdout fit | OOF predictions |
| Seed robustness | IMPLEMENTED_AWAITING_RUNS | Final trainer/evaluator accept only protocol-fixed robustness seeds 1337/2026 with the selection lock; no result files yet | no holdout use | HPO selection and final fit |
| Ensemble / ablations | NOT_STARTED | no adaptation prediction files | none | model outputs |
| Statistics / figures / report | NOT STARTED | no model results to plot | none | predictions |
| Judge notebook | IMPLEMENTED, RESULT CELLS PENDING | 36 ordered sections; canonical code source display | no locked data access | training outputs |
| Notebook recovery | PASS_CONTENT, CHECKPOINTS_VERIFIED, WORKER_STOPPED_BY_POLICY; STATUS_FIX_SYNCED | Colab checkout is synced to `45be47e`; the saved monitor displays the old `SIGTERM: 15` as `EXITED_BY_SIGNAL (legacy status; see runner error)` while preserving the stored record. Final cell explains the trainer call path and current stage; read-only snapshot shows trial 0 `RUNNING`, trials 1–3 `WAITING`, selection open. | no holdout or locked-test access | wait for provider-compliant free GPU access before resume |
| Local validation | PASS | `make validate` on 2026-09-23: 739 passed, 33 deselected, 95.07% core coverage; secret scan, Ruff, and strict mypy passed (67 files). All 21 tests under `tests/adaptation` passed, covering runner signal handling plus data-contract manifests, checkpoint guards, calibration, statistics, and helpers. | software-only; formal data checks read frozen manifest integrity/counts and overlap, with no VALIDATION prediction evaluation or selection | continue study |
| Adaptation branch push | PASS | metric/README update `a2f500f` pushed after fixed-seed notebook gate `44ac317`; `main` and baseline tag unchanged | none | continue study |

No holdout or locked-test result is inferred from training progress or the smoke test.
