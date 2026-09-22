# Judge demo guide

**Study:** `POSTHOC-FOUNDATION-ADAPTATION-001`
**Notebook:** [EvoVariant_TR_Adaptation_Judge_Demo.ipynb](../notebooks/EvoVariant_TR_Adaptation_Judge_Demo.ipynb)
**Protocol SHA-256:** `07c93b4657e84a4ddfbdc2df1af0f467f80959e0534a67840b4bf2b2b04a2c2c`

## 5–10 minute walkthrough

1. **Baseline:** section 2 anchors the separate frozen temporal result and commit/tag.
2. **Data split:** sections 4–5 show the exact TRAIN/VALIDATION populations, hashes, gene boundary, and locked-test exclusion.
3. **Sequence and model:** sections 6–8 show real reference-window, mutation, paired-head, and reverse-complement implementation.
4. **Fine-tuning:** sections 9–18 print the source for training, loss, optimizer, forward/backward, clipping, precision, early stopping, and checkpoint/resume.
5. **HPO and results:** sections 19–21 expose the objective and read machine-readable results; absent artifacts are labelled pending.
6. **Post-fit analysis:** sections 22–33 state calibration, abstention, ensemble, robustness, metrics, figures, and error-analysis status without making claims from incomplete runs.
7. **Reproducibility and limits:** sections 34–36 close with contribution boundaries, limitations, and artifact locations.

## Current evidence boundary

This notebook is an inspectable scientific walkthrough, not a claim that every requested stage has completed. The 128 bp smoke passed. The 8,192 bp frozen-head baseline is running in the user’s existing free T4 Colab session; no training result is reported until its checkpoint and `run.json` are persisted. The 946-row locked temporal test is not used for adaptation.
