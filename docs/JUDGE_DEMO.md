# Judge demo guide

The two notebooks below are CPU/local evidence viewers. They do not launch a GPU worker, open the 801-row holdout, or access the 946-row labels for new selection.

1. Open [EvoVariant_TR_Baseline_Judge_Demo.ipynb](../notebooks/EvoVariant_TR_Baseline_Judge_Demo.ipynb). Run all cells. It reads the frozen Phase 14 receipt, joined predictions, metrics table, figure inventory, and registry/protocol paths.
2. Open [EvoVariant_TR_FineTuning_Attempt_Demo.ipynb](../notebooks/EvoVariant_TR_FineTuning_Attempt_Demo.ipynb). Run all cells. It displays `configure_trainable()`, the actual `backward()` / `optimizer.step()` source path, the HPO queue, the proof record, and the incomplete state.
3. For the complete rendered set, open [final_polish_gallery.html](../artifacts/audits/final_polish_gallery.html) and the existing [figure QA gallery](../artifacts/audits/figure_qa_gallery.html).

The demo notebooks are explanatory evidence surfaces, not a replacement for the persisted JSON/JSONL artifacts. Claims must be read with their evidence stage and cohort boundary.
