# Adaptation State

Study: POSTHOC-FOUNDATION-ADAPTATION-001
Protocol SHA-256: `07c93b4657e84a4ddfbdc2df1af0f467f80959e0534a67840b4bf2b2b04a2c2c`
Evidence stage: `EXECUTION_IN_PROGRESS`
Current persisted stage: `CADUCEUS_FROZEN_HEAD_ONLY_DONE`

## Completed gates

- Branch hygiene audited; `main` and `evovariant-tr-baseline-v1` unchanged.
- Free-Colab execution approval recorded; paid budget is $0.
- Protocol and manifest identities frozen.
- Environment recorded on Tesla T4: Python 3.11.16, PyTorch 2.2.0+cu121, CUDA 12.1, NumPy 1.26.4, 15,360 MiB device memory.
- TRAIN and VALIDATION manifest checks passed: 3,199 / 801 rows, zero gene and ID overlap, zero overlap with locked IDs.
- UCSC hg38 reference SHA-256 `5be01555d98347fdb3714dc84c6f77c9d8bc774adcf32c6f7a8fa06f5baf5e51`; all 4,000 development REF alleles passed.
- Caduceus smoke passed at 128 bp: finite forward/loss/gradients, optimizer step, checkpoint save/reload compatibility; 10.73 s, 452,699,136 peak bytes.
- Frozen-head TRAIN-only fit completed on the 3,199 TRAIN rows at 8,192 bp, seed 42, 3 epochs (losses `1.1767539545572263`, `1.1581548454985837`, `1.1497443100928366`). Runtime was 1,968.52 s; 7,728,385 total / 3,073 trainable parameters; peak allocation 320,895,488 bytes. The Drive checkpoint SHA-256 is `230fc7bef5c12fcb5f5c5a6b31ff4d79d57c244b8a00d70ac54e60aaf4e02213`; its `run.json` records `PASS`, `TRAIN_ONLY`, and `holdout_evaluated=false`.
- The 8-trial, 3-fold gene-grouped TRAIN-only HPO process is active in the same Vivaldi T4 session. Its SQLite study and logs are on Drive; selection remains open. No validation or locked rows have been loaded. The persisted stage will advance when the first trial finishes.

## Current repository provenance

- Branch: `research/posthoc-foundation-adaptation`
- HEAD used to start the active Colab training: `34f65a3d8d0125be4cf00b78f19ce115cdc9feae`
- Latest implementation/notebook commit: `69ad3e6` (`docs: reconcile adaptation state and push status`). HPO runs from this revision. The frozen-head process started at `34f65a3d8d0125be4cf00b78f19ce115cdc9feae`.
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

8–12 completed TRAIN-only grouped HPO trials → selection lock → final TRAIN fit → one-shot 801 evaluation → seed/NT tracks as resources allow → analysis/statistics/figures/report → final validation and push.

The full-candidate and NT tracks remain resource-conditional. Missing results are not inferred from the plan.

## Local validation

Latest `make validate`: secret scan and Ruff passed; strict mypy passed (67 files); 734 tests passed / 33 deselected; core coverage 95.07%.
