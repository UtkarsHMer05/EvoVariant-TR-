# Recovery audit — 2026-09-23

Status: **RECOVERY PRESERVED; TRAINING WAITING FOR FREE GPU.** The scientific run is incomplete. This update is a recovery-state refresh, not a new full Drive inventory.

- Branch: `research/posthoc-foundation-adaptation`; repository HEAD at refresh: `331e5a35d0fef8a4ed6b714f982c3b57773d4fc1`.
- The file classifications in [RECOVERY_AUDIT.json](RECOVERY_AUDIT.json) remain the earlier inventory from source commit `cfecb11` (121 repository files and 51 Drive files). The full Drive inventory was not repeated in this refresh.
- Original Drive folder ID: `1RMhA2eEUsvgryqz8YnRryuniroDiTA89`. Writable recovery root: `/content/drive/MyDrive/EvoVariantTR`. Read-only source shortcut: `/content/drive/MyDrive/EvoVariantTR_original`.
- The existing Colab file ID `15lXyrBjVZw24Mick-cbcPTzA4VD6BY4w` is saved with 20 cells / 10 sections, corrected roots, and cleared outputs. The notebook was not executed after repair. The remote bytes were not exported, so no post-edit SHA-256 is claimed; the old hash is labeled as pre-repair in the JSON.
- A stale HPO child (PID 12473) writing through the shared shortcut was stopped; its parent PID 12382 was a zombie. At the last verified poll, SQLite integrity was `ok`, trial 0 was `RUNNING`, trials 1–3 were `WAITING`, histories were 4 / 3 / none, and there was no completed trial or selection lock.
- The visible Vivaldi tab was under a non-default Google account. The attached master prompt requires the default account and prohibits switching; training therefore remains `WAITING_FOR_FREE_GPU`. No paid compute or account rotation was used.
- The 801-row adaptation holdout was not accessed; the historical 946-row locked test was not accessed for this work. The selection lock remains open.

## Next gate

On an eligible free T4 under the prompt's default-account rule, verify the owned SQLite snapshot and checkpoint bindings, finalize fold 1 from its best checkpoint, then start fold 2 epoch 1. Continue the predeclared TRAIN-only HPO/refit gates before any one-shot 801-row evaluation. Keep the 946-row test closed to adaptation selection.
