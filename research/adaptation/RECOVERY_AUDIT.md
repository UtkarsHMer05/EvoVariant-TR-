# Recovery audit — 2026-09-23

Status: **RECOVERY PRESERVED; TRAINING WAITING FOR FREE GPU; DEFAULT-ACCOUNT RECOVERY PROVENANCE UNRESOLVED.** The scientific run is incomplete. This update is a recovery-state refresh, not a new full Drive inventory.

- Branch: `research/posthoc-foundation-adaptation`; repository HEAD at refresh: `331e5a35d0fef8a4ed6b714f982c3b57773d4fc1`.
- The file classifications in [RECOVERY_AUDIT.json](RECOVERY_AUDIT.json) remain the earlier inventory from source commit `cfecb11` (121 repository files and 51 Drive files). The full Drive inventory was not repeated in this refresh.
- Previously recorded expected source folder ID: `1RMhA2eEUsvgryqz8YnRryuniroDiTA89`. Writable recovery root: `/content/drive/MyDrive/EvoVariantTR`. Read-only source shortcut: `/content/drive/MyDrive/EvoVariantTR_original`. The latest default-account lookup does not confirm a distinct source folder.
- At the initial audit snapshot, the existing Colab file ID `15lXyrBjVZw24Mick-cbcPTzA4VD6BY4w` was saved with 20 cells / 10 sections, corrected roots, and cleared outputs, and had not been executed after repair. The later partial default-account preflight is recorded below. Remote bytes were not exported, so no post-edit SHA-256 is claimed; the old hash is labeled as pre-repair in the JSON.
- A stale HPO child (PID 12473) writing through the shared shortcut was stopped; its parent PID 12382 was a zombie. At the last verified poll, SQLite integrity was `ok`, trial 0 was `RUNNING`, trials 1–3 were `WAITING`, histories were 4 / 3 / none, and there was no completed trial or selection lock.
- The visible Vivaldi tab was under a non-default Google account. The attached master prompt requires the default account and prohibits switching; training therefore remains `WAITING_FOR_FREE_GPU`. No paid compute or account rotation was used.
- The 801-row adaptation holdout was not accessed; the historical 946-row locked test was not accessed for this work. The selection lock remains open.

## Next gate

Under the prompt's default-account rule, first restore or independently verify the expected source shortcut and recovery-copy manifest in the authorized Drive root. Then, on an eligible free T4, verify the SQLite snapshot and checkpoint bindings, finalize fold 1 from its best checkpoint, and start fold 2 epoch 1. Continue the predeclared TRAIN-only HPO/refit gates before any one-shot 801-row evaluation. Keep the 946-row test closed to adaptation selection.

## Latest default-account execution attempt

The existing Colab tab showed the authorized default account. Its CPU reconnect passed the hardware probe, and Drive mounted after the standard sign-in flow. The first post-mount path guard then failed closed: the expected read-only `EvoVariantTR_original` shortcut was absent, and the writable root lacked `state/recovery_copy_manifest.json`. The present `state/manifests_verified.json` records dataset checks and is not a recovery-copy manifest. Default-account title searches found no exact item-name match for either expected name. Opening the historically recorded folder ID in Drive showed the owned `My Drive/EvoVariantTR` folder, which does not establish a distinct original source; no shortcut was created to avoid pointing read-only input at the writable root. This was a targeted check, not a full Drive inventory; no missing file was recreated and no guard was bypassed.

The notebook's read-only SQLite preflight copied the existing `.snapshot` to local disk and verified integrity `ok`. It reported trial 0 `RUNNING`, trials 1–3 `WAITING`; the status cell showed the frozen report `PASS`, fold history lengths 4 / 3, and selection `OPEN`. No checkpoint payloads were reloaded. Colab rejected the T4 request due to GPU usage limits, and the runtime is now disconnected. No paid compute, account rotation, setup, runner, training, adaptation-holdout, or locked-test cell was used.

The notebook guard remains correct for the evidence available: the default-account root cannot currently prove the expected source and recovery-copy lineage. The UI reports the diagnostic cell outputs saved; remote notebook bytes were not exported, so no current notebook hash is claimed. The next gate is to restore or independently verify those exact artifacts in the authorized root, then recheck checkpoint bindings on an eligible free T4 before resuming. The selection lock remains open.
