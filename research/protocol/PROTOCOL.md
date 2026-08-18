# RESEARCH PROTOCOL — EvoVariant-TR (Frozen)

- Protocol version: **1.0.0**
- Frozen date: 2026-08-18 (Milestone 11)
- Machine-readable twin: `research/protocol/protocol.yaml` (SHA-256 recorded in the
  milestone ledger/report; recompute with `shasum -a 256 research/protocol/protocol.yaml`)
- Deviations: only via dated entries in `research/protocol/DEVIATION_LOG.md`.

This protocol controls all downstream work. Where it conflicts with the legacy
README or legacy code behavior, this protocol wins.

## 1. Scientific question (primary)

> Among unique normalized germline GRCh38 SNVs recorded as variants of uncertain
> significance in a fixed historical ClinVar release and later receiving a definitive
> benign/likely-benign or pathogenic/likely-pathogenic classification with the
> prespecified review-status quality gate, how well does a frozen zero-shot Evo 2
> allele-likelihood score distinguish the direction of that later resolution?

This is a **temporal generalization benchmark**, conditional on eventual resolution.

It does **NOT** estimate: whether every VUS will be reclassified; when a VUS will be
reclassified; a patient's diagnosis; treatment; clinical management; or causal
pathogenicity truth. ClinVar is a time-indexed archive of submitter assertions and
aggregated classifications; review stars are a quality/review-status proxy, not
biological certainty.

## 2. Frozen temporal design

| Item | Value | Mutability |
|---|---|---|
| t0 release | ClinVar archived `variant_summary` dated **2025-01-02** | IMMUTABLE (primary) |
| t1 release | ClinVar archived `variant_summary` dated **2026-08-06** | IMMUTABLE (primary) |
| Reference assembly | **GRCh38** | IMMUTABLE (primary) |
| Primary unit | one unique normalized biallelic A/C/G/T germline SNV | IMMUTABLE (primary) |
| t0 state | aggregate **VUS** | IMMUTABLE (primary) |
| t1 positive outcome | **P/LP** (pathogenic / likely pathogenic) | IMMUTABLE (primary) |
| t1 negative outcome | **B/LB** (benign / likely benign) | IMMUTABLE (primary) |
| Primary t1 label-quality gate | **>= 2 review stars** | IMMUTABLE (primary) |

### QA checkpoint (validation target only — never injected, never forced)

Prior research checkpoint numbers: t0 unique VUS 1,403,225; absent at t1 3,615;
not definitive 1,389,535; below two stars 9,051; final temporal n 1,024;
B/LB 614; P/LP 410; gene labels 389; reference mismatch 0 among final candidates.

The new repository MUST recompute the cohort from public source archives. These
numbers are a QA target only. If recomputed values differ, investigate (archive
identity, schema/version, germline field, normalization, review-status mapping,
VCV/RCV/SCV duplication, assembly filtering, coordinate normalization, duplicate
policy, reference, gene annotation) and document the discrepancy **before any model
scoring**. Never change filters merely to force the numbers.

## 3. Primary Evo 2 scoring contract

Let `S(x)` be the frozen, official-implementation-verified Evo 2 sequence score.
For an exact reference context `x_ref` and an otherwise identical context with one
alternate allele `x_alt`:

```text
delta_fwd     = S(x_alt_fwd) - S(x_ref_fwd)
delta_rc      = S(x_alt_rc)  - S(x_ref_rc)
delta_primary = (delta_fwd + delta_rc) / 2     # predeclared orientation-aware score
```

All raw information is retained per variant: reference/alternate scores and delta
for forward and RC; primary mean delta; absolute forward/RC disagreement;
orientation disagreement flag/summary; canonical variant ID; window coordinates;
local mutation index; reference and alternate sequence hashes; model/checkpoint
identity; official package/source revision; runtime; GPU type; software environment;
run ID; failure status.

Do not retain only the mean. Do not convert the raw score directly to a clinical label.

## 4. Exact sequence contract

- Primary context length: exactly **8192 bases**.
- One precise even-window convention (frozen at Milestone 41).
- Code MUST assert: `end - start == 8192`; `len(sequence) == 8192`;
  `sequence[variant_local_index] == declared_reference`;
  `HammingDistance(reference_context, alternate_context) == 1`.
- One-based genomic → zero-based half-open conversion documented and exhaustively
  tested. The legacy calculation is not inherited.

## 5. Calibration contract

- The temporal test cohort is NEVER used to fit a calibrator or threshold.
- Calibration uses variants already definitive at t0.
- Primary method: **Platt / logistic** calibration.
- Folds: **grouped by gene**.
- Unseen-gene analysis: **zero gene overlap**.
- Isotonic: **sensitivity only**, only with adequate n.
- t1 temporal-test outcomes never choose: calibration model, threshold, checkpoint,
  context length, centering, comparator, subgroup, score sign after seeing
  performance, or abstention threshold.

## 6. Primary and secondary statistics

- **Sole primary endpoint: AUROC.**
- Primary uncertainty: **95% gene-clustered bootstrap CI**, **2,000 replicates**,
  **seed 20260814**.
- Secondary: AUPRC; MCC; balanced accuracy; sensitivity; specificity; precision;
  Brier score; negative log-likelihood; ECE with binning sensitivity; reliability
  data/plot; coverage; failure reasons; risk-coverage curves; abstention/selective
  prediction; runtime; peak memory; cold/warm behavior; orientation disagreement;
  context robustness; gene-held-out transport; review-status sensitivity;
  consequence/coding subgroup analyses.
- Confirmatory predictor comparisons use paired gene-clustered resampling with
  multiple-comparison correction (e.g., Holm) per the frozen analysis plan.

## 7. Comparators

- Core feasible: **CADD**, **PhyloP**.
- Conditional preferred: **GPN-Star**. Conditional parity/fallback: **GPN-MSA**.
- Conditional valid subset: **AlphaMissense**. Stretch: **Caduceus**.
- Every comparator records: version, source, license, assembly, allele convention,
  score direction, asset checksum, coverage, missing reason.
- Missing scores stay missing. Never map missing comparator scores to benign.

## 8. Claim-safety and no-fabrication (binding)

- Research-only. Forbidden default claims: diagnoses disease; clinically validated;
  predicts patient outcome; medical device; guaranteed pathogenic/benign; clinical
  confidence; first-ever temporal VUS predictor; "Evo 2 is superior" — unless a
  future properly designed study supports the exact statement and the user approves.
- Never invent model scores, metrics, runtimes, memory, findings, counts, hashes,
  costs, or test output. Unavailable = UNAVAILABLE; not run = NOT RUN. Null and
  negative results are valid.

## 9. Immutable vs exploratory fields

- **Immutable primary fields** (change only via deviation entry): t0/t1 release
  dates; assembly; primary unit; t0 VUS state; P/LP vs B/LB outcome definitions;
  >=2-star primary gate; primary endpoint (AUROC); bootstrap replicates and seed;
  context length 8192; orientation-aware primary score definition; calibration
  disjointness; zero-shot policy.
- **Exploratory/sensitivity fields** (predeclared before inspecting temporal
  performance, labeled sensitivity): >=1-star cohort; expert-panel/practice-guideline
  subsets; context-length and center-shift robustness sets; consequence subgroups;
  isotonic calibration; abstention signals.

## 10. Deviation procedure

Any change to an immutable field, or any predeclaration made after seeing temporal
performance, requires a dated entry in `DEVIATION_LOG.md` stating: what changed,
why, who approved, and the impact on the estimand. A protocol change that changes
the estimand is never called a bugfix.
