# GLOSSARY — EvoVariant-TR canonical terminology (Milestone 007)

Authoritative definitions for the project. Where legacy usage conflicts, this
glossary (and the frozen protocol) wins.

## Scientific terms

- **VUS (variant of uncertain significance)** — a ClinVar aggregate classification of
  "uncertain significance" at a given release. A starting state, not an outcome.
- **t0** — the fixed historical ClinVar archived `variant_summary` release dated
  **2 January 2025**. Defines the baseline VUS cohort.
- **t1** — the later ClinVar archived `variant_summary` release dated
  **6 August 2026**. Defines eventual outcomes.
- **Temporal generalization benchmark** — the study design: score t0-VUS variants
  with a frozen zero-shot model and test whether scores distinguish the direction of
  their later (t1) resolution.
- **P/LP** — pathogenic or likely pathogenic. The positive t1 outcome class.
- **B/LB** — benign or likely benign. The negative t1 outcome class.
- **Review stars** — a 0–4 quality/review-status proxy derived from ClinVar review
  status. A quality gate, not biological certainty. Primary gate: **>= 2 stars**.
- **Canonical variant ID** — `GRCh38:chr:pos:ref:alt` for a unique normalized
  biallelic A/C/G/T germline SNV. The unit of analysis.
- **Allele-likelihood score** — the Evo 2 sequence log-likelihood (or its mean
  reduction) for a given sequence. A raw model quantity.
- **delta_fwd** — `S(x_alt) - S(x_ref)` on the forward strand.
- **delta_rc** — the same delta computed on the reverse-complement representation.
- **delta_primary** — the predeclared orientation-aware score
  `(delta_fwd + delta_rc) / 2`.
- **Orientation disagreement** — `|delta_fwd - delta_rc|`; an observation, not an
  error (unless a parity contract fails).
- **Zero-shot** — the model is used as-is, frozen; no fine-tuning on study labels.
- **Calibration cohort** — variants already definitive (B/LB or P/LP) at t0, used
  only to fit a probability calibrator. Disjoint from the temporal test cohort.
- **Temporal test cohort** — t0-VUS variants with a definitive >=2-star t1 outcome.
  Never used to fit thresholds or calibrators.
- **Study probability** — a calibrated probability that a variant's later resolution
  is P/LB vs B/LB *under this benchmark protocol*. Not an individual clinical risk.
- **Estimand** — the precise quantity estimated: discrimination (AUROC) of frozen
  zero-shot scores for later-resolution direction among eventually-resolved t0 VUS.
- **Coverage** — the fraction of cohort variants for which a predictor yields a
  score. Missingness is a result, not a nuisance.

## Engineering / provenance terms

- **Evidence stage** — one of SYNTHETIC_TEST, LEGACY_BASELINE, ENGINEERING_PILOT,
  PRELIMINARY, FINAL. See `EVIDENCE_STAGES.md`.
- **Run / run_id** — a registered, reproducible execution with full provenance.
- **Manifest** — a JSON record of a data/result asset's source, size, timestamps,
  and SHA-256.
- **Protocol hash** — SHA-256 of the frozen `protocol.yaml`; anchors reproducibility.
- **Parity** — agreement between the project's scoring adapter and the official
  Evo 2 implementation within predeclared tolerance.
- **Shard** — a deterministic partition of the cohort for parallel/resumable scoring.
- **Failure taxonomy** — explicit categories (reference_error, invalid_sequence,
  model_error, oom, timeout, external_service, serialization, unknown) for missing
  scores.

## Deprecated legacy terms (do not use in new outputs)

- "Likely pathogenic" / "Likely benign" as model predictions.
- "classification_confidence".
- "prediction" (as a clinical class). Use "raw score" / "study probability".
