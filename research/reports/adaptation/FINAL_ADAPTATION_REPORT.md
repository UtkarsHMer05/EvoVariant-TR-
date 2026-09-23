# Post-Hoc Foundation-Model Adaptation Report

**Study:** `POSTHOC-FOUNDATION-ADAPTATION-001`
**Status:** `IN PROGRESS`
**Protocol SHA-256:** `07c93b4657e84a4ddfbdc2df1af0f467f80959e0534a67840b4bf2b2b04a2c2c`
**Evidence boundary:** adaptation TRAIN/VALIDATION only; the 946-row temporal locked test was not loaded.

## Abstract

The independent adaptation study is underway. Formal TRAIN/VALIDATION identities, GRCh38 REF alleles, the free-T4 environment, and a 128 bp Caduceus forward/backward/checkpoint smoke are verified. The 8,192 bp frozen-encoder/head-training baseline completed on all 3,199 TRAIN rows. Its training loss declined from `1.1767539545572263` to `1.1497443100928366` over three epochs; this is optimization evidence only, not a discrimination metric. The original T4 runtime disconnected during TRAIN-only HPO and denied free reconnection. An earlier free-T4 session verified the original Drive study database and loaded four fold checkpoints with matching metadata, but no training resumed. The later default-account reconnect provided CPU only; its Drive root lacked the expected source shortcut and recovery-copy manifest, and Colab denied another free T4 request due to usage limits. The original notebook was replaced in place with a clean 20-cell version after archiving its exact prior bytes. No completed trial, selected configuration, one-shot holdout result, or model comparison is available yet.

## Research question

Does task-specific adaptation of feasible genomic foundation models improve P/LP-vs-B/LB resolution-direction discrimination relative to frozen representations on the formal gene-held-out 801-row adaptation holdout?

## Relationship to the frozen baseline

The baseline remains the historical temporal study on 946 locked rows (AUROC `0.909225974`), bound to `main` commit `30b515314d5f8c8be7c83c96b1f576fb7225c869` and `evovariant-tr-baseline-v1` tag `1003bc5a20973145e0e096ff7b0f3424045d07e6`. The 801-row adaptation holdout is a separate population and evidence stage; these metrics are not directly interchangeable.

## Dataset

| Split | Rows | Negative | Positive | Status |
|---|---:|---:|---:|---|
| TRAIN | 3,199 | 2,645 | 554 | verified; training only so far |
| VALIDATION | 801 | 581 | 220 | identity verified; no predictions/labels evaluated |
| Development | 4,000 | 3,226 | 774 | manifest identities verified |

TRAIN SHA-256: `32bf517ec8bc401d29f611e83a8c8c81eafc0d1f19886d2650a3bf441df044e1`
VALIDATION SHA-256: `b31d884860fcf07b6f7f453c3ef148886913f381965318e9c1da341d1eaf3c8b`
Development SHA-256: `f4a9e53bd96c60dd9bd949568adb7a6bece3ff01bd4cceb76f71f1380e16e782`

## Leakage controls

The manifests are hash-pinned. TRAIN and VALIDATION have zero normalized-ID and gene overlap. Formal adaptation IDs have zero overlap with the locked manifest. Training and HPO load TRAIN rows only; class weights are fold-local. The evaluation CLI refuses validation without a closed TRAIN-only selection lock and refuses a second output. The one-shot holdout has not been opened.

## Environment and hardware

Observed GPU: Tesla T4, 15,360 MiB device memory (14.56 GiB). Isolated runtime: Python 3.11.16, PyTorch 2.2.0+cu121, CUDA 12.1, NumPy 1.26.4, Transformers 4.38.1, `mamba-ssm` 1.2.0.post1, `causal-conv1d` 1.2.0.post2. No paid compute was used or authorized.

## Sequence construction

The verified UCSC hg38 FASTA decompresses to 3,273,481,150 bytes with SHA-256 `5be01555d98347fdb3714dc84c6f77c9d8bc774adcf32c6f7a8fa06f5baf5e51`. All 4,000 formal development REF alleles match the FASTA. The primary context is 8,192 bp; paired reference and alternate SNV sequences and their reverse complements are constructed through the shared data module.

## Caduceus architecture and smoke

Pinned checkpoint: `kuleshov-group/caduceus-ph_seqlen-131k_d_model-256_n_layer-16`, revision `b0477522ac5d044ad03578aa724ec8e4bdbd405b`. A shared encoder generates masked-mean-pooled reference/alternate embeddings. The head receives `z_ref`, `z_alt`, their signed difference, and its absolute value. Forward and reverse-complement logits are averaged. The 128 bp smoke passed finite forward/loss/gradients, optimizer step, and checkpoint reload prediction compatibility in 10.73 s; peak allocation was 452,699,136 bytes. This smoke is not a training result.

## Frozen Caduceus baseline

`PASS`: frozen encoder, trainable paired head, seed 42, 3 epochs, batch size 1, effective batch 16, AdamW learning rate `2e-5`, weight decay `0.01`, dropout `0.1`, context 8,192 bp. Epoch losses were `1.1767539545572263`, `1.1581548454985837`, and `1.1497443100928366`; runtime was 1,968.52 s (32.81 min). The run used 7,728,385 total parameters / 3,073 trainable parameters; peak allocation was 320,895,488 bytes. The Drive checkpoint `checkpoints/caduceus_frozen_head/latest.pt` has SHA-256 `230fc7bef5c12fcb5f5c5a6b31ff4d79d57c244b8a00d70ac54e60aaf4e02213`. Its run record is `PASS`, `TRAIN_ONLY`, `holdout_evaluated=false`.

## Partial and full fine-tuning

`NOT STARTED`. Any T4 OOM or resource limit will be recorded as `FULL_FINETUNE_RESOURCE_DEFERRED_T4`; no rows will be removed or replaced.

## HPO and seed robustness

`WAITING_FOR_FREE_GPU`. The last verified SQLite snapshots pass integrity; trial 0 is RUNNING and trials 1–3 are WAITING. Fold 0 has four saved epochs, fold 1 has three, and fold 2 has none. A stale worker against the shared Drive shortcut was stopped before it produced a new fold checkpoint or completed trial. The clean notebook now points writes to the owned recovery root, but has not been rerun. The selection lock remains open. Resume only on an eligible free GPU under the prompt's default-account rule, then complete at least 8 trials (maximum 12) with 3-fold gene-grouped CV inside TRAIN. Seeds remain fixed at 42, 1337, and 2026; none may be selected by holdout performance.

## 801-row holdout

`CLOSED`. No evaluation occurs before a hash-bound TRAIN-only selection lock and final TRAIN fit. No holdout metrics are available.

## Nucleotide Transformer v2 500M

Pinned revision: `06615c1660c892fc199840c18123f8385b3542a8`. `NOT STARTED`; begin only after Caduceus results are safely persisted. Frozen and PEFT results will be reported only if actually run within the free-T4 boundary.

## Calibration, abstention, ensemble, robustness, ablations

Calibration and gene-aware selective/statistical helpers are implemented and locally validated; no TRAIN OOF predictions exist yet. No calibrator is fitted, no abstention result is measured, and no ensemble/context/learning-curve/ablation result is available. The frozen protocol requires OOF-only calibrator fitting and a 2,000-replicate gene-aware paired bootstrap with Holm correction.

## Statistics, errors, and figures

No adaptation prediction CSV exists. Therefore no ROC/PR curve, confusion matrix, reliability or risk-coverage curve, subgroup/error analysis, bootstrap result, or adaptation figure has been generated. Missing curves will remain missing rather than interpolated.

## Reproducibility and limitations

The frozen-head process started from HEAD `34f65a3d8d0125be4cf00b78f19ce115cdc9feae`; the HPO worker uses validated pushed revision `69ad3e6`. The baseline checkpoint is bound to the frozen protocol, TRAIN manifest, reference hash, and model revision. The class-stratified development sample does not represent deployment prevalence. This is a research-only discrimination study and does not establish clinical validity, diagnosis, treatment utility, causality, or universal genomic performance.

## Conclusion

The protocol, data gates, short smoke, and full-context frozen-head TRAIN-only fit pass. The repaired notebook is saved and has only had a partial default-account preflight run. That preflight stopped at the missing source shortcut and recovery manifest; Colab also denied the free T4 request. The shared-shortcut worker was stopped before it produced a new checkpoint. Selection remains open. Completion criteria remain unmet until recovery provenance and eligible compute are restored, followed by grouped HPO, selection closure, final fit, one-shot holdout, supported analysis, and remaining figures/reports.

## Latest recovery check, 2026-09-23

The default-account Colab reconnect was CPU-only. Drive mounted, but the notebook correctly stopped at the source guard because the expected `EvoVariantTR_original` shortcut and `state/recovery_copy_manifest.json` were missing. Exact-title searches found neither item; the recorded folder ID opens the owned `My Drive/EvoVariantTR` folder, so a distinct read-only source was not established. A read-only copy of its SQLite snapshot passed integrity (`ok`) and still showed trial 0 `RUNNING`, trials 1–3 `WAITING`; the frozen report was `PASS`, fold histories were 4 / 3 epochs, and selection remained open. Colab denied a free T4 request due to usage limits. No training, adaptation-holdout, or locked-test cell ran. Recovery provenance and eligible free GPU availability are both required before resuming.
