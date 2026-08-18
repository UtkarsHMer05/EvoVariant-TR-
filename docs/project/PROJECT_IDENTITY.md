# PROJECT IDENTITY — EvoVariant-TR (Milestone 007)

Date: 2026-08-18

## 1. Canonical project title

**EvoVariant-TR** — "Temporal Resolution of Variants of Uncertain Significance with
Frozen Zero-Shot Evo 2 Allele-Likelihood Scoring."

Short form for prose: **EvoVariant-TR**. The suffix "TR" stands for *temporal
resolution* and distinguishes this project from the legacy "EvoVariant"/
"Evo2 Variant Analysis" system.

## 2. Canonical package and module names

| Scope | Name |
|---|---|
| Python package | `evovariant_tr` |
| Python source root | `src/evovariant_tr/` |
| CLI entrypoint | `python -m evovariant_tr.cli` |
| Modal application name | `evovariant-tr-v2` (unique to the NEW project; final name to be confirmed with the user at Milestone 52 before deployment) |
| Modal model-cache volume | `evovariant-tr-model-cache` |
| Frontend app directory | `apps/web` |
| Frontend package name (target) | `evovariant-tr-web` (renamed during the M18 move) |

## 3. Distinctness from the source snapshot

The legacy identities are retired and must not be reused as final infrastructure:

| Legacy identity | Status |
|---|---|
| Project title "Evo2 Variant Analysis" | retired; superseded by EvoVariant-TR |
| Repo/package name `variant-analysis-evo2` | retired |
| Modal app `variant-analysis-evo2` | retired; replaced by `evovariant-tr-v2` |
| Modal volume `hf_cache` | retired; replaced by `evovariant-tr-model-cache` |
| Frontend package `variant-analysis-evo2-frontend` | retired; renamed at M18 |
| Old deployment URL `https://utkarshmer05--variant-analysis-evo2-...modal.run` | retired; never reused |

Verification (Milestone 7): `rg "Evo2 Variant Analysis|variant-analysis-evo2"` now
matches only legacy snapshot files and audit documents that reference them — no new
module, config, or deliverable carries the old names.

## 4. Research-only product wording

EvoVariant-TR is **research software**. Default wording for all UI, API, reports,
and documentation:

- The system produces a **raw sequence score** / **variant-effect score**, not a
  diagnosis.
- Calibrated outputs are a **study probability** under a specific temporal benchmark
  protocol, not a clinical probability for an individual.
- The benchmark measures discrimination of **later resolution direction** among
  historically-VUS variants that were eventually resolved, conditional on eventual
  resolution. It does not estimate whether or when any VUS will be reclassified.
- Every user-facing surface displays the **research-only** boundary and the current
  **evidence stage**.

## 5. Banned default wording

The following are banned from default UI/API output and from claims unless a future
properly designed study supports the exact statement and the user approves it:

- "diagnoses disease", "clinically validated", "predicts patient outcome"
- "medical device"
- "guaranteed pathogenic", "guaranteed benign"
- "clinical confidence"
- "first-ever temporal VUS predictor"
- "Evo 2 is superior"
- The legacy labels "Likely pathogenic" / "Likely benign" as model outputs
- The legacy `classification_confidence` field

## 6. Evidence stages (summary)

Five stages control how any output may be labeled and promoted. Full definitions in
`docs/terminology/EVIDENCE_STAGES.md`:

1. `SYNTHETIC_TEST` — fake/deterministic software-test output. Never research evidence.
2. `LEGACY_BASELINE` — old-project saved outputs. Engineering baseline only.
3. `ENGINEERING_PILOT` — real model runs validating plumbing, not science.
4. `PRELIMINARY` — registered real runs before final freeze/approval.
5. `FINAL` — frozen, approved, fully provenanced primary results.

## 7. Terminology

Canonical definitions of scientific terms live in `docs/terminology/GLOSSARY.md`.
Where the legacy README and the new protocol disagree, the frozen protocol
(`research/protocol/`, Milestone 11) is authoritative; the legacy README is history.
