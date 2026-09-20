# Metrics and Statistical Analysis

## Classification metrics

Always compute where defined:
- AUROC
- AUPRC
- MCC
- balanced accuracy
- accuracy
- precision
- recall/sensitivity
- specificity
- F1

## Probabilistic metrics

For calibrated probabilities:
- Brier score
- negative log-likelihood
- ECE
- reliability table/plot

## Selective prediction

- coverage
- retained-set error/risk
- AUROC/AUPRC at prespecified coverage if useful
- risk-coverage curve

## Confidence intervals

Prefer gene-clustered bootstrap for temporal data where gene clustering matters.
Record:
- replicate count,
- seed,
- cluster key,
- percentile/BCa choice if used.

Do not change CI method after seeing which looks better.

## Pairwise comparison

Predictions are paired on the same eligible variants.
Use paired bootstrap/resampling.
If a family of confirmatory comparisons is made, correct multiplicity (e.g. Holm).

## Model selection

Validation only.

Define tie-break order before HPO completion, for example:
1. primary validation metric,
2. calibration or MCC,
3. lower complexity/cost,
4. lower latency.

## Missingness

Every metric declares denominator.
Comparator coverage must be explicit.

## Seeds

Track:
- split seed,
- model initialization seed,
- bootstrap seed,
- HPO sampler seed.

## Plot integrity

Plots must be generated from result files.
Axes must not intentionally exaggerate small differences.
Include n and uncertainty where useful.

