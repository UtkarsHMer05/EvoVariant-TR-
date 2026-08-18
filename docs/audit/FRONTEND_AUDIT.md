# FRONTEND AUDIT — Legacy `evo2-frontend/` (Milestone 005)

Date: 2026-08-18
Companion: `docs/audit/frontend_data_flow.md`. No redesign at this milestone.

## 1. Stack and reproducibility

- Next.js 15.2.3 (App Router), React 19, TypeScript 5.8.2, Tailwind CSS 4,
  shadcn/ui (components.json), zod + @t3-oss/env-nextjs.
- `npm ci` **succeeded** (Validation 1: dependency installation is reproducible).
- `npm run typecheck` (`tsc --noEmit`) **passed** with exit code 0.
- `npm audit` reports **12 vulnerabilities (2 low, 1 moderate, 8 high, 1 critical)**,
  including inherited `sharp`/`libvips` CVEs. These are recorded for the later
  security milestone (M97) and are not fixed here.

## 2. Component trace

| Component | Responsibility |
|---|---|
| `src/app/page.tsx` | entry; `search`/`browse` modes; loads genomes + chromosomes; gene search table; opens GeneViewer; hard-coded "Try BRCA1 example" button (page.tsx:142-145, 270-272) |
| `src/app/layout.tsx` | root layout |
| `src/components/gene-viewer.tsx` | orchestrates gene details, sequence, ClinVar; wires child components |
| `src/components/gene-information.tsx` | gene metadata panel |
| `src/components/gene-sequence.tsx` | sequence window with slider + base coloring; click-to-select nucleotide |
| `src/components/known-variants.tsx` | ClinVar variant table; per-row "Analyze with Evo2"; opens comparison modal |
| `src/components/variant-analysis.tsx` | custom variant entry; POSTs to backend; renders prediction/confidence |
| `src/components/variant-comparison-modal.tsx` | ClinVar vs Evo2 side-by-side; agreement/disagreement framing |
| `src/components/ui/*` | shadcn primitives (button, card, input, select, table, tabs) |
| `src/utils/genome-api.ts` | single API adapter for all external calls |
| `src/utils/coloring-utils.ts` | nucleotide coloring |
| `src/lib/utils.ts` | `cn()` helper |
| `src/env.js` | env schema |

## 3. Data flows

See `frontend_data_flow.md` for the full table. Summary: 6 GET flows to UCSC/NCBI
and 1 POST flow to the Modal endpoint, all client-side, all via `genome-api.ts`.

## 4. Environment variables / secrets

- One client var: `NEXT_PUBLIC_ANALYZE_SINGLE_VARIANT_BASE_URL` (a URL, not a secret).
- No Modal credentials, tokens, or API keys are browser-exposed.
- **Validation 3 PASS:** no secret is exposed through NEXT_PUBLIC variables.

## 5. Clinical-classification assumptions in the UI

The UI treats the model output as a clinical classification:

- `prediction` rendered as "Likely pathogenic"/"Likely benign" with red/green color
  coding (`variant-analysis.tsx:329-347`, `variant-comparison-modal.tsx:153-156`).
- `classification_confidence` rendered as a progress bar
  (`variant-analysis.tsx:339-347`, `variant-comparison-modal.tsx:180-189`).
- Agreement framing: "Evo2 prediction agrees/differs with ClinVar classification"
  (`variant-comparison-modal.tsx:215-216`).

This conflicts with the claim-safety policy and the new evidence-stage model. The
new workbench (Milestone 93) replaces this with research-only, provenance-first
display.

## 6. Accessibility / responsiveness / reproducibility limitations

- **Accessibility:** no evidence of ARIA labels, keyboard-navigation handling, or
  focus management beyond default button behavior; color-only encoding of
  pathogenic/benign (red/green) without text alternatives for color-blind users.
  Must be addressed at M97.
- **Responsiveness:** desktop-oriented layout; no explicit mobile breakpoints
  observed in the traced components. Must be verified at M97.
- **Reproducibility:** `npm ci` + `typecheck` pass; however the app depends on live
  UCSC/NCBI availability and a specific deployed Modal URL, so runtime behavior is
  not reproducible offline.
- **Robustness:** no timeouts, no retries, no AbortSignal, no structured error
  codes; a single typo in an error string ("Faield to search genes", page.tsx:96).
- **Known dependency vulnerabilities:** 12 npm audit findings (see §1).

## 7. What is NOT changed at this milestone

- No component, type, or API adapter is edited.
- The BRCA1 example button, clinical framing, and live-API flows remain as the
  migration baseline. They are replaced/removed in later milestones (M18 move,
  M93 redesign), not now.
