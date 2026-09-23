# Caduceus HPO recovery, 2026-09-23

## Verified recovery state

- Branch at inspection: `research/posthoc-foundation-adaptation`, HEAD `dc9ee30e5b149832d0adb2f5d64707ec095d713b`.
- The Drive file `hpo/caduceus_hpo.sqlite3` was downloaded read-only as a local copy: 114,688 bytes, SHA-256 `ae22d5c562db0c295cd93d881ca29d1fd77598842f5e706d3f9da460f39ba768`. A local SQLite `PRAGMA integrity_check` returned `ok`. The original Drive file was not edited.
- Optuna study `evovariant_caduceus_train_grouped_cv_v1`: trial 0 `RUNNING`; trials 1, 2, 3 `WAITING`; no completed trial. Study reference hash is `5be01555d98347fdb3714dc84c6f77c9d8bc774adcf32c6f7a8fa06f5baf5e51`.
- Trial 0 parameters: frozen head, learning rate `3e-5`, weight decay `0`, dropout `0.1`, effective batch `16`, epoch cap `4`. Existing trial signature `705d3dee50f29527` matches the Drive checkpoint directory.
- Fold 0 `history.json` has epochs 1–4 (SHA-256 `5aedcbfb4795b534e6f1c4a5986f7b443ce9f01e699331033e4b5d71699c4032`); best observed AUROC was `0.5417921894652882` at epoch 2. Fold 1 has epochs 1–3 (SHA-256 `547e84e6e783e9d08d777ac3412257ad9f8d94c0110e121460d4032678d2f6c4`); best observed AUROC is `0.51218820861678` at epoch 3. Fold 2 has no checkpoint directory.
- On the newly connected free T4, the new account's `EvoVariantTR_original` Drive shortcut resolved to the original folder ID `1RMhA2eEUsvgryqz8YnRryuniroDiTA89`. Its 114,688-byte DB was copied to local disk and passed SQLite integrity again: trial 0 `RUNNING`, trials 1–3 `WAITING`. The new account's separate `EvoVariantTR` folder contains no study DB and is excluded by the clean notebook's path guard.
- All four original HPO checkpoint binaries loaded through PyTorch on the T4. Fold 0 `latest.pt` is 31,078,330 bytes, SHA-256 `935ff06a0cf1788b0ec11b82805fd6202c4329cbf4355232e54f7e9f32937e11`, saved zero-based epoch 3; `best.pt` is 31,077,162 bytes, SHA-256 `490922f1476ff2ed6f2a11fa543350447d9c2fe23604cab0955c9230080a5430`, epoch 1. Fold 1 `latest.pt` is 31,078,330 bytes, SHA-256 `67f32c68d72d44c4819eeeba974fa355b30334a6c8091c9b50908036c0f3dcd0`, epoch 2; `best.pt` is 31,077,162 bytes, SHA-256 `2e65375b10f394be4be32574269a4f3c3afedc0ba1a591b4320977a9d9f68e02`, epoch 0. All four carry protocol `07c93b...a2c2c`, revision `b0477522ac5d044ad03578aa724ec8e4bdbd405b`, TRAIN manifest `32bf517...df044e1`, and verified reference hash `5be01555...f5e51`; fold IDs and trial signature match their paths. Zero-based saved epochs match the histories' 1-based entries.
- The original Optuna database contains intermediate step 1 value `0.5269409039606832`, written during fold 1 before that fold completed. The repaired runner overwrites that step with the completed-fold mean before pruning; this prevents an old partial value from driving a resumed pruning decision.
- No `selection_closed.json`, final refit, or adaptation holdout output was observed. The selection gate remains open.

## Exact next work

1. On an eligible free T4, mount Drive, verify the checkpoint payloads and reference, and restore the study database from a verified Drive snapshot or the intact legacy copy to `/content/evovariant_runtime/hpo/`.
2. Resume **trial 0, fold 1, epoch 4** if the fold-1 `latest.pt` payload confirms epoch 3 and the recorded bindings. Fold 0 requires no new training epoch. If the binary checkpoint disagrees with its history, stop for forensic recovery; do not restart trial 0.
3. Complete fold 2, then the queued trials and predeclared 8 completed TRAIN-only trials. Persist local SQLite via backup API to an atomic Drive `.snapshot` after each epoch, fold, and trial.
4. Keep the 801-row adaptation holdout closed until the selection lock, OOF calibration, and all fixed-seed TRAIN refits are verified. The historical 946-row test remains outside adaptation selection.

The user switched to a second account with an available free T4. No paid compute was selected. The earlier pending CPU-switch approval was not used. The Drive shortcut relies on the original folder's already-existing link access; a named Editor grant to the new account is still subject to a separate action-time confirmation.
