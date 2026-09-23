# Recovery audit — 2026-09-23

Status: **RECOVERY PRESERVED; HPO PAUSED AFTER PROVIDER-POLICY CHECK; SCIENTIFIC RUN INCOMPLETE.** The latest T4 attempt passed recovery-root and reference checks and persisted fold 2 epoch 2. Its worker was stopped after checking Colab's multiple-account resource-limit rule. This update is not a new full Drive inventory.

- Branch: `research/posthoc-foundation-adaptation`; prior recovery-refresh HEAD: `331e5a35d0fef8a4ed6b714f982c3b57773d4fc1`; latest code HEAD before this documentation update: `664c1cd26b7e7afedb3031e716a326d59ab49480`.
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

The notebook guard remained correct for that default-account attempt. The UI reported its diagnostic outputs saved; remote notebook bytes were not exported, so no notebook hash was claimed for that attempt. The latest user-authorized T4 resume attempt is recorded below.

## Latest authorized T4 resume attempt

The user explicitly authorized the connected Om Srivastava account and other accounts, overriding the attached prompt's default-account-only instruction; no paid compute was selected. The current T4 Drive mount passed the recovery-root, source-folder-ID, recovery-manifest, and study-database guards. A fresh SQLite snapshot copy passed integrity (`ok`) with trial 0 `RUNNING`, trials 1–3 `WAITING`; histories remained 4 / 3, the frozen report was `PASS`, and selection remained open. Reference preparation passed against the pinned GRCh38 SHA-256 and all 4,000 formal REF alleles. Guarded runner PID 11483 is active and has opened the existing Optuna study; exact checkpoint resume and any new epoch are not yet verified. Neither the 801-row adaptation holdout nor the historical 946-row test was accessed.

## Live compute poll, 2026-09-23 07:35–07:37 UTC

A read-only runtime sample showed parent PID 11483 alive and HPO child PID 11573 at 97.5% CPU. The Tesla T4 reported 100% utilization, 847 / 15,360 MiB VRAM, and 77 C. A follow-up notebook refresh still showed trial 0 `RUNNING`, trials 1–3 `WAITING`, fold histories 4 / 3, no fold-2 history, and no new saved epoch or completed trial. The worker was using the GPU, but its exact resumed checkpoint was not yet established. The temporary diagnostic cell was removed; Colab reported the canonical notebook saved at 20 cells / 10 sections. The selection lock remained open; the adaptation holdout and historical test remained closed. Continuation proposed at that time was later stopped after the provider-policy check recorded below.

## Checkpoint-bound continuation, 2026-09-23 07:48–07:50 UTC

The latest run persisted fold 2 epoch 1. Folds 0, 1, and 2 have contiguous history/checkpoint epoch counts 4, 3, and 1. `latest.pt` and `best.pt` for each fold passed exact protocol hash, fold, trial signature, model revision, TRAIN manifest, and reference metadata checks; the latest checkpoint hashes are recorded in `STATE.md`. A copied Drive SQLite snapshot passed integrity (`ok`) with trial 0 `RUNNING`, trials 1–3 `WAITING`. The runner remained active at 07:50 UTC. The persisted stage is `CADUCEUS_HPO_EPOCH_PERSISTED`; selection remains open, and holdout and locked-test gates remain closed.

## Latest checkpoint and policy check, 2026-09-23 08:08 UTC

At the user's request, the notebook ran on the connected Om Srivastava account after the default account's free-GPU limit. Colab's official [FAQ](https://research.google.com/colaboratory/intl/en-GB/faq.html) disallows using multiple accounts to work around access or resource-use restrictions. After checking this rule, HPO child PID 11573 was stopped with SIGTERM at 08:05 UTC; parent PID 11483 exited with a matching `CalledProcessError`. No further account switching or paid compute was used.

After the stop, the Drive SQLite snapshot passed integrity (`ok`); Optuna lists trial 0 `RUNNING` and trials 1–3 `WAITING`, the HPO JSON remains `PENDING`, and the selection lock is absent. Fold histories are contiguous at 4 / 3 / 2. Every latest/best checkpoint passes protocol, fold, signature, model revision, TRAIN manifest, reference, and epoch-history checks. Fold 2 latest (epoch 2) SHA-256 is `067579471de3b420f0cbf7d0f765ad5a0fadb3bb5f172b6ee1dfae79aa82ad29`; best (epoch 1) is `27663f7692be220457a44d1bdd62f21f423c4cc359d059d6cb4bec948f8b8e83`.

The temporary audit cell was removed and the saved notebook is back to 20 cells / 10 sections. Selection remains open; neither the 801-row adaptation holdout nor the historical 946-row test was accessed. Resume only when provider-compliant free compute is available; the next exact item is trial 0 fold 2 epoch 3.
