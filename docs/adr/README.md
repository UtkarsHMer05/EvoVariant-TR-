# Architecture Decision Records — EvoVariant-TR

Index of high-risk design decisions. Each ADR has Context, Decision, Alternatives,
Consequences, and Validation sections. Unknown or not-yet-decidable items are marked
**OPEN** rather than guessed.

| ADR | Title | Status |
|---|---|---|
| [0001](0001-fresh-repository.md) | Fresh-repository isolation | ACCEPTED |
| [0002](0002-temporal-clinvar.md) | Archived ClinVar releases rather than live labels | ACCEPTED |
| [0003](0003-grch38-reference.md) | Exact GRCh38 reference source and checksum | ACCEPTED (source bytes finalized at M31) |
| [0004](0004-zero-shot-policy.md) | Zero-shot model policy | ACCEPTED |
| [0005](0005-exact-8192-windows.md) | Exact 8,192-base sequence windows | ACCEPTED (convention frozen at M41) |
| [0006](0006-forward-rc-retention.md) | Forward and reverse-complement retention | ACCEPTED |
| [0007](0007-disjoint-calibration.md) | Disjoint calibration | ACCEPTED |
| [0008](0008-modal-cost-gates.md) | Modal GPU use and cost gates | ACCEPTED |
| [0009](0009-no-test-label-tuning.md) | No test-label threshold tuning | ACCEPTED |
| [0010](0010-evidence-stage-ui.md) | Evidence-stage UI labels | ACCEPTED |

## OPEN items (explicitly not guessed)

- **Exact GRCh38 FASTA source accession/URL and checksum** — policy fixed (ADR 0003);
  the concrete authoritative source is selected and recorded at Milestone 31 after
  checking approved research artifacts and official sources.
- **Modal app name final confirmation** — `evovariant-tr-v2` proposed (ADR 0008,
  Project Identity); confirmed with the user at Milestone 52 before deployment.
- **Evo 2 checkpoint selection (e.g., 7B vs 7B-base)** — to be justified against the
  official implementation and research question at Milestone 49, before any temporal
  scoring; not decided here.
- **Chromosome-edge window policy choice (exclude vs deterministic shift)** —
  predeclared at Milestone 43 after counting edge-proximal variants; both options
  remain valid until then.

## Amendment procedure

An ADR is amended only via a new dated revision note inside the file (never silent
rewrites). Changes that alter the scientific estimand also require an entry in
`research/protocol/DEVIATION_LOG.md`.
