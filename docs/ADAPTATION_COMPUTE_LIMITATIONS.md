# Adaptation compute limitations

The post-hoc study was constrained to free, provider-compliant Colab GPU and local no-cost execution. The available T4 completed the frozen-head TRAIN-only prerequisite and a controlled encoder-update proof, then lost usable free-GPU availability while the persisted TRAIN-only HPO study remained incomplete.

No account rotation to bypass provider limits, paid GPU, full Evo2 fine-tuning, or fabricated fallback result was used. The correct state is `WAITING_FOR_FREE_GPU` / incomplete adaptation. Resume requires a compliant GPU session and must use the pinned model revision, frozen manifests, persisted checkpoints, and the declared TRAIN-only grouped-CV protocol.

See the detailed evidence ledger at [research/adaptation_attempt/COMPUTE_LIMITATIONS.md](../research/adaptation_attempt/COMPUTE_LIMITATIONS.md) and the machine-readable index at [EVIDENCE_MANIFEST.json](../research/adaptation_attempt/EVIDENCE_MANIFEST.json).
