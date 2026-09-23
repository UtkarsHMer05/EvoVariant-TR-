# Adaptation State

Study: POSTHOC-FOUNDATION-ADAPTATION-001
Protocol SHA-256: `07c93b4657e84a4ddfbdc2df1af0f467f80959e0534a67840b4bf2b2b04a2c2c`
Evidence stage: `EXECUTION_IN_PROGRESS`
Current persisted stage: `CADUCEUS_HPO_FOLD_PERSISTED` (latest default-account Drive read; recovery provenance is incomplete)

## Completed gates

- Branch hygiene audited; `main` and `evovariant-tr-baseline-v1` unchanged.
- Free-Colab execution approval recorded; paid budget is $0.
- Protocol and manifest identities frozen.
- Environment recorded on Tesla T4: Python 3.11.16, PyTorch 2.2.0+cu121, CUDA 12.1, NumPy 1.26.4, 15,360 MiB device memory.
- TRAIN and VALIDATION manifest checks passed: 3,199 / 801 rows, zero gene and ID overlap, zero overlap with locked IDs.
- UCSC hg38 reference SHA-256 `5be01555d98347fdb3714dc84c6f77c9d8bc774adcf32c6f7a8fa06f5baf5e51`; all 4,000 development REF alleles passed.
- Caduceus smoke passed at 128 bp: finite forward/loss/gradients, optimizer step, checkpoint save/reload compatibility; 10.73 s, 452,699,136 peak bytes.
- Frozen-head TRAIN-only fit completed on the 3,199 TRAIN rows at 8,192 bp, seed 42, 3 epochs (losses `1.1767539545572263`, `1.1581548454985837`, `1.1497443100928366`). Runtime was 1,968.52 s; 7,728,385 total / 3,073 trainable parameters; peak allocation 320,895,488 bytes. The Drive checkpoint SHA-256 is `230fc7bef5c12fcb5f5c5a6b31ff4d79d57c244b8a00d70ac54e60aaf4e02213`; its `run.json` records `PASS`, `TRAIN_ONLY`, and `holdout_evaluated=false`.
- The original account's T4 runtime disconnected and then denied free reconnection. On 2026-09-23 a second account had a connected free T4. Its `EvoVariantTR_original` shortcut resolves to the original Drive folder ID `1RMhA2eEUsvgryqz8YnRryuniroDiTA89`. At the first poll, its separate `EvoVariantTR` folder lacked the study DB; the verified owned recovery copy was subsequently populated there. A fresh local copy of the original HPO SQLite passed `PRAGMA integrity_check`: trial 0 RUNNING, trials 1–3 WAITING. Fold 0 has four history epochs; fold 1 has three. Both folds' latest and best binary checkpoints loaded with matching protocol, revision, manifest, reference hash, signature, and fold. Fold 1's latest checkpoint has `stale_epochs=2`, so its early stopping condition is met; the next trial-0 work is fold-1 final evaluation and fold-2 epoch 1, with no fourth fold-1 training epoch. No trial is complete and selection remains open. See `HPO_RECOVERY_REPORT.md`.
- The second T4 previously verified Python 3.11.16, PyTorch 2.2.0+cu121, CUDA 12.1, pinned Caduceus dependencies, the GRCh38 FASTA hash, and all 4,000 formal REF alleles. The same Colab file ID `15lXyrBjVZw24Mick-cbcPTzA4VD6BY4w` now shows 20 cells / 10 sections, uses the owned `EvoVariantTR` folder for writable state and the original shortcut as a read-only source, and has stale outputs cleared. The UI reported all changes saved. The full notebook has not been executed after this repair.
- A stale launch from the prior live notebook produced HPO child PID 12473 against the shared `EvoVariantTR_original` shortcut; its parent PID 12382 was already a zombie, and the runner log and fold-2 history were absent. The child was stopped with SIGTERM. No new fold checkpoint or completed trial was present at the last verification. The owned recovery copy and shortcut SQLite copies had passed `PRAGMA integrity_check` with trial 0 RUNNING and trials 1–3 WAITING; fold histories remained 4 / 3 / no fold 2, and selection remained open. Training is now `WAITING_FOR_FREE_GPU` under the prompt's default-account rule; no further account rotation or paid compute was used.
- Latest default-account recheck on 2026-09-23: the already-open notebook mounted Drive on a CPU runtime, then cell 3 stopped at its source-path guard. `/content/drive/MyDrive/EvoVariantTR_original` was absent and `state/recovery_copy_manifest.json` was absent from the writable root; `manifests_verified.json` is a dataset summary, not a recovery-copy manifest. Do not treat this Drive root as a verified resume source until its provenance is restored. A read-only copy of its SQLite `.snapshot` passed `PRAGMA integrity_check` (`ok`), with trial 0 `RUNNING` and trials 1–3 `WAITING`; the frozen report was `PASS`, histories were 4 / 3 epochs, and selection remained open. Colab denied the free T4 request due to usage limits. No setup, runner, training, holdout, or locked-test cell ran in this attempt.
- An identity-only audit confirmed the existing Evo2 output covers all 3,199 TRAIN and 801 VALIDATION IDs with no duplicates, split disagreements, or locked-ID overlap; its prediction and development-manifest hashes match the receipt. It remains excluded because the producing checkout is marked dirty and the full-run approval referenced in its execution plan is unavailable. Score and label values were not inspected or used.

## Current repository provenance

- Branch: `research/posthoc-foundation-adaptation`
- HEAD used to start the active Colab training: `34f65a3d8d0125be4cf00b78f19ce115cdc9feae`
- Notebook finalization gate update: `44ac317`; its two executable cells compiled and the live preselection guard blocked without opening VALIDATION. Probability MAE reporting is in `a2f500f`; full `make validate` passed with 736 tests, 33 deselected, and 95.06% core coverage. The HPO worker started from `69ad3e6`; its runner source is unchanged in later revisions. The frozen-head process started at `34f65a3d8d0125be4cf00b78f19ce115cdc9feae`.
- Main: `30b515314d5f8c8be7c83c96b1f576fb7225c869`
- Frozen baseline tag: `1003bc5a20973145e0e096ff7b0f3424045d07e6`
- TRAIN manifest: `32bf517ec8bc401d29f611e83a8c8c81eafc0d1f19886d2650a3bf441df044e1`
- VALIDATION manifest: `b31d884860fcf07b6f7f453c3ef148886913f381965318e9c1da341d1eaf3c8b`
- Locked manifest identity hash: `9f9e052d21f4a6a32f595cb20f48cb81e033c0481942820d04f9b67d410a16cb`
- Drive state: `/content/drive/MyDrive/EvoVariantTR/state/adaptation_state.json`
- Drive smoke checkpoint hash: `da541bb25b2cc556d5089357939c0dd3a1589aa7c604b1242ec6da71604c9042`

## Holdout boundary

```yaml
validation_manifest_identity_checked: true
validation_rows_evaluated: false
validation_labels_used_for_selection: false
locked_946_rows_loaded: false
locked_946_labels_used: false
selection_closed: false
```

## Pending stages

`WAITING_FOR_FREE_GPU` with default-account recovery provenance unresolved → restore or independently verify the expected source shortcut and recovery-copy manifest in the authorized root → reverify checkpoint bindings on an eligible free T4 → resume HPO at the fold-1 completion boundary → 8–12 completed TRAIN-only grouped trials → selection lock → final TRAIN fits → one-shot 801 evaluation → seed/NT tracks as resources allow → analysis/statistics/figures/report → final validation and push.

The full-candidate and NT tracks remain resource-conditional. Missing results are not inferred from the plan.

## Local validation

Latest `make validate` on 2026-09-23: secret scan and Ruff passed; strict mypy passed (67 files); 737 tests passed / 33 deselected; core coverage 95.07%.
