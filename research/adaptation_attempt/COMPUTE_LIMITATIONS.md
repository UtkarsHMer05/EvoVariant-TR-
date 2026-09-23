# Adaptation compute limitations

The adaptation protocol allowed free Colab GPU, local CPU/RAM, Drive, and no-cost packages. It did not authorize paid compute, account rotation to bypass provider limits, full Evo2 fine-tuning, or clinical deployment.

The available Tesla T4 completed the frozen-head TRAIN-only stage and a small encoder-update feasibility proof. The longer TRAIN-only HPO worker persisted partial fold histories/checkpoints, then stopped when free-GPU access was no longer available. The current evidence is therefore:

- frozen head: completed on TRAIN;
- encoder update proof: PASS, one controlled optimizer step;
- partial-small, partial-large, and full adaptation trials: not completed;
- adaptation HPO: incomplete, selection open;
- 801-row validation: closed and unopened;
- 946-row temporal cohort: prohibited for adaptation selection;
- NT frozen/PEFT track: not started.

The correct status is resource-limited incompletion, not a negative biological finding and not a completed fine-tuning result. Re-running requires a provider-compliant GPU session and must resume from verified persisted checkpoints under the frozen protocol.
