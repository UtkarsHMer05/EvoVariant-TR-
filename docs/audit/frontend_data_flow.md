# FRONTEND DATA FLOW — Legacy `evo2-frontend/` (Milestone 005)

Date: 2026-08-18
Companion: `docs/audit/FRONTEND_AUDIT.md`. No redesign at this milestone.

## 1. All browser/server data flows

Every external call is centralized in `src/utils/genome-api.ts`. There are **no**
server-side API routes in the Next.js app; all data fetching happens client-side
from the browser.

| # | Trigger (component) | Adapter function | Destination | Method | Purpose |
|---|---|---|---|---|---|
| 1 | HomePage load | `getAvailableGenomes()` | `https://api.genome.ucsc.edu/list/ucscGenomes` | GET | list genome assemblies |
| 2 | Genome selected | `getChromosomes(genomeId)` | `https://api.genome.ucsc.edu/list/chromosomes?genome=<id>` | GET | list chromosomes |
| 3 | Gene search | `searchGenes(terms, genome)` | `https://clinicaltables.nlm.nih.gov/api/ncbi_genes/v3/search` | GET | find genes by symbol/name |
| 4 | Gene selected | `fetchGeneDetails(geneId)` | `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=gene` | GET | gene bounds + summary |
| 5 | GeneViewer load | `fetchGeneSequence(...)` | `https://api.genome.ucsc.edu/getData/sequence?...` | GET | gene sequence window |
| 6 | GeneViewer load | `fetchClinvarVariants(...)` | `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi` then `esummary.fcgi` (`db=clinvar`) | GET | known ClinVar variants |
| 7 | Variant submit / ClinVar row analyze | `analyzeVariantWithAPI(...)` | `env.NEXT_PUBLIC_ANALYZE_SINGLE_VARIANT_BASE_URL` (Modal FastAPI) | POST | Evo2 scoring |

## 2. Environment variables and browser-visible configuration

- Schema: `src/env.js` (zod + @t3-oss/env-nextjs).
- Server vars: `NODE_ENV` only.
- Client vars: **exactly one** — `NEXT_PUBLIC_ANALYZE_SINGLE_VARIANT_BASE_URL`
  (`env.js:19`, consumed at `genome-api.ts:364`).
- This variable is a **URL**, not a credential. It is browser-visible by design
  (the client must know where to POST). It carries **no secret**.
- No Modal token, no API key, no `SERVERVAR` with sensitive value is exposed via
  `NEXT_PUBLIC_`.

**Conclusion (Validation 3):** no secret is exposed through NEXT_PUBLIC variables.

## 3. Direct browser calls to external genomic services

Flows 1–6 above are direct browser → UCSC/NCBI calls. Implications:

- No server-side proxy or caching; every page interaction hits public APIs.
- No API key is used for NCBI eutils (rate-limited to 3 req/s without a key).
- No `AbortSignal`, no timeout, no retry anywhere in `genome-api.ts`
  (verified: `rg "AbortSignal|signal|timeout|retry"` → no matches).
- CORS is satisfied because UCSC/NCBI permit browser access; this is a convenience
  path, distinct from the frozen research data pipeline.

## 4. Variant-analysis request/response contract (legacy)

Request (POST body, `genome-api.ts:371-376`):

```json
{ "variant_position": 43119628, "alternative": "G", "genome": "hg38", "chromosome": "chr17" }
```

Response (parsed into `AnalysisResult`, `genome-api.ts:60-66`):

```json
{ "position": 43119628, "reference": "A", "alternative": "G",
  "delta_score": -0.001234, "prediction": "Likely pathogenic",
  "classification_confidence": 0.73 }
```

The client renders `prediction` and `classification_confidence` directly — the
clinical-framing fields produced by the legacy backend (see BACKEND_AUDIT §6).

## 5. Error / loading states

- `page.tsx`: `isLoading` + `error` string state; disables buttons while loading;
  shows error text. Contains a typo: `"Faield to search genes"` (page.tsx:96).
- `gene-viewer.tsx`: separate loading/error state for gene details, sequence, ClinVar
  (`setClinvarError("Failed to fetch ClinVar variants")`, gene-viewer.tsx:197).
- `variant-analysis.tsx` / `known-variants.tsx`: per-row `isAnalyzing` and
  `evo2Error` fields on ClinVar rows.
- States are present but basic: no retry affordance, no timeout, no structured error
  codes, no distinction between network failure and model failure.

## 6. Assumptions that a model result is a clinical classification

- `variant-analysis.tsx:329-347`: renders `prediction` with color classes
  (pathogenic → red, benign → green) and a `classification_confidence` progress bar.
- `variant-comparison-modal.tsx:131-216`: side-by-side "ClinVar Assessment" vs Evo2
  prediction; states "Evo2 prediction agrees/differs with ClinVar classification".
- `genome-api.ts:44-53,60-66`: `ClinvarVariant.evo2Result` and `AnalysisResult`
  types carry `prediction` + `classification_confidence`.

These present the raw model delta as a clinical classification with confidence —
the framing the new research workbench must remove (Milestone 93).

## 7. Reproducibility

- `package-lock.json` present → `npm ci` is deterministic. Verified: `npm ci`
  succeeded (Milestone 5).
- `packageManager: "npm@10.2.4"` declared in package.json.
- Scripts: `build`, `check` (lint + tsc), `dev`, `typecheck`, `lint`, `format:*`.
