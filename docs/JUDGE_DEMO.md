# EvoVariant-TR Judge Demo

Use the local app and the generated manifest for a 10-15 minute evidence-first walkthrough:

1. Open the normal variant-analysis workflow and confirm the existing form loads.
2. Select Benchmarks in the visible navigation.
3. Start at Overview and scan the contribution registry and B01-B68 status counts.
4. Open Core Baseline for the immutable 946-row result and primary figures.
5. Compare foundation, representation, and classical evidence.
6. Show HPO & Training and explain that downstream HPO is separate from adaptation.
7. Open Calibration & Uncertainty, Evidence Quality, and Temporal Difficulty.
8. Open Generalization for LOCO and seed robustness.
9. Open Model Disagreement for common-row correlations and hard cases.
10. Open External Benchmarks to show the frozen n=200 manifest and explicit compute block.
11. Open Errors & Case Studies for deterministic locked examples.
12. Open Runtime & Cost to show zero new spend and the balance gate.
13. Open Fine-Tuning Attempt if asked; emphasize primary NO, implementation YES,
    feasibility proof YES if the persisted proof verifies, and complete study NO.
14. Use Downloads and Reproducibility to show notebooks, hashes, protocol, and
    the artifact manifest.

Likely questions:

- Is the 946 result fine-tuned? No. The primary result uses frozen foundation
  representations, a downstream classifier, and frozen calibration.
- Why is the external result empty? The candidate manifest is frozen, but the
  safety gate did not expose a verifiable Modal balance; no unsupported scores
  are shown.
- Are review stars biological certainty? No. They are observational evidence-
  quality strata only.
- Can the result be reproduced without paid GPU? The local integrity check,
  generated tables, figures, notebooks, and manifest checks run from persisted
  artifacts; fresh external inference is intentionally blocked.
