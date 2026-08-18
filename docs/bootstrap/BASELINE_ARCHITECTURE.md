# BASELINE ARCHITECTURE — Source Snapshot Inventory (Milestone 002)

Date: 2026-08-18
Evidence stage of all saved metrics below: **LEGACY_BASELINE_ONLY** (not EvoVariant-TR evidence).

This document inventories the supplied local EvoVariant source snapshot exactly as it
exists at Milestone 2, before any refactor. Companion artifacts:

- `docs/bootstrap/source_snapshot.sha256` — SHA-256 of every tracked/source file
  (excludes `.git/`, `.DS_Store`, `__pycache__/`, `*.pyc`). Verified deterministic:
  two independent generations produced byte-identical manifests.
- `docs/bootstrap/all_files.txt` — sorted file list (66 entries: 62 snapshot files
  + 4 Milestone-1 bootstrap docs).
- `docs/bootstrap/initial_file_inventory.txt` — pre-refactor inventory including
  OS/cache files (66 entries).

## 1. Language / size counts

| Extension | Files | Lines | Notes |
|---|---|---|---|
| `.py` | 15 | 7,605 | backend + evaluation + debug/patch experiments |
| `.ts` | 3 | 418 | frontend utils/lib |
| `.tsx` | 14 | 2,654 | Next.js app + components |
| `.js` | 5 | 110 | config files (next, eslint, postcss, prettier, env) |
| `.json` | 6 | 6,531 | package.json, package-lock.json, tsconfig, components.json, legacy metrics/diagnostics |
| `.md` | 7 | 1,534 | legacy READMEs/PPT + Milestone-1 bootstrap docs |

Total snapshot size ≈ 1.1 MB excluding `.git` (largest files: `package-lock.json`
224 KB; four ~60 KB attention-interface copies; legacy result PNGs 36–48 KB each).

## 2. Component classification

### 2.1 Backend — `evo2-backend/` (production-ish code)

| File | Lines | Role |
|---|---|---|
| `main.py` | 376 | Monolith: Modal image build, dependency install, compatibility monkey patch, model init, live UCSC sequence download, ref/alt construction, Evo 2 scoring, BRCA1 analysis, threshold derivation, confidence heuristic, FastAPI endpoint |
| `requirements.txt` | 8 | Unpinned deps: fastapi[standard], modal, matplotlib, pandas, seaborn, scikit-learn, openpyxl, requests |

Responsibilities combined in `main.py` (all in one file):

1. Modal image creation (`nvidia/cuda:12.4.0-devel-ubuntu22.04`, Python 3.12).
2. Dependency installation (torch 2.4.0 cu124 wheel; **unpinned** `git clone
   --recurse-submodules https://github.com/ArcInstitute/evo2.git`; transformer-engine
   uninstall + `transformer_engine[pytorch]==1.13` reinstall; flash-attn 2.6.3 wheel
   force-reinstall).
3. Compatibility patching: in-image `run_commands` string-replacement monkey patch of
   `vortex/ops/attn_interface.py` (rewrites flash-attn fwd return unpacking and
   disables a `torch.__version__ >= "2.4.0"` branch).
4. Model initialization (`Evo2('evo2_7b')` in `@modal.enter()`; also inside
   `run_brca1_analysis`).
5. Live UCSC sequence download (`get_genome_sequence`, no timeout/retry, no
   provenance).
6. Reference/variant sequence construction (window formula — see §5 defect note).
7. Evo 2 scoring (`score_sequences` ref + alt).
8. BRCA1 analysis (`run_brca1_analysis`: hg19/GRCh37 BRCA1 deep-mutational-scan
   xlsx + GRCh37 chr17 FASTA, first-500-row subset, ROC-Youden threshold derivation).
9. Threshold derivation/use (hard-coded constants in `analyze_variant`).
10. Confidence heuristic (distance-from-threshold divided by class std).
11. HTTP endpoint serving (`@modal.fastapi_endpoint(method="POST")`
    `analyze_single_variant`; Modal app name `variant-analysis-evo2`; volume
    `hf_cache`; `@app.cls(gpu="H100", max_containers=3, retries=2,
    scaledown_window=120)`).

### 2.2 Backend — runtime experiments (NOT production code)

| File | Lines | Role |
|---|---|---|
| `debug_flash_attn.py` | 34 | flash-attn diagnostic |
| `debug_flash_attn2.py` | 40 | flash-attn diagnostic |
| `debug_returns.py` | 38 | return-value diagnostic |
| `download_file.py` | 35 | file download helper |
| `parse.py` | 12 | parsing scratch |
| `local_attn_interface.py` | 1,628 | local copy of vortex attn_interface |
| `patched_attn_interface.py` | 1,630 | patch output v1 |
| `patched_attn_interface2.py` | 1,632 | patch output v2 |
| `patched_attn_interface3.py` | 1,628 | patch output v3 |
| `test_bypass.py` | 4 | patch experiment |
| `test_clone.py` | 16 | clone experiment |
| `test_import.py` | 31 | import experiment |
| `test_patch.py` | 10 | patch experiment |

These document the patch journey for the old CUDA/Torch/FlashAttention stack; they
are migration input for audit only (Milestones 3–4), not code to preserve.

### 2.3 Frontend — `evo2-frontend/` (Next.js app)

Stack: Next.js 15.2.3 (App Router), React 19, TypeScript 5.8.2, Tailwind CSS 4,
shadcn/ui (`components.json`), zod + @t3-oss/env-nextjs env validation.
`package-lock.json` present → `npm ci` reproducibility possible.

| Path | Role |
|---|---|
| `src/app/page.tsx` | entry page; search/browse modes; genome+chromosome loading |
| `src/app/layout.tsx` | root layout |
| `src/components/gene-viewer.tsx` | orchestrates gene details/sequence/ClinVar |
| `src/components/gene-information.tsx` | gene metadata panel |
| `src/components/gene-sequence.tsx` | sequence window w/ slider + base coloring |
| `src/components/known-variants.tsx` | ClinVar variant table + per-row analysis |
| `src/components/variant-analysis.tsx` | custom variant entry → backend call |
| `src/components/variant-comparison-modal.tsx` | ClinVar vs Evo2 side-by-side |
| `src/components/ui/*` | shadcn primitives (button, card, input, select, table, tabs) |
| `src/utils/genome-api.ts` | API adapter: direct browser fetch to UCSC + NCBI + Modal POST |
| `src/utils/coloring-utils.ts` | base coloring |
| `src/lib/utils.ts` | cn() helper |
| `src/env.js` | env schema; client var `NEXT_PUBLIC_ANALYZE_SINGLE_VARIANT_BASE_URL` |
| `src/styles/globals.css` | Tailwind globals |

Config: `package.json`, `tsconfig.json`, `next.config.js`, `eslint.config.js`,
`postcss.config.js`, `prettier.config.js`, `components.json`, `.env.example`,
`.gitignore`, `public/favicon.ico`, `README.md`.

### 2.4 Evaluation — `evaluation/`

| Path | Role |
|---|---|
| `evaluate_modal_endpoint.py` (491 lines) | External HTTP evaluator against the deployed Modal endpoint; BRCA1 hg19 xlsx input; computes accuracy/precision/recall/F1/AUROC-from-delta + latency; writes metrics/plots |
| `README.md` | run instructions (contains a hard-coded absolute venv path under `/Users/utkarshkhajuria/Downloads/variant-analysis-evo2/`) |
| `results/final_100/*` | **Generated results** of one legacy 100-row run: metrics.json, summary.txt, diagnostics.json, predictions.csv, failures.csv, 5 PNG plots |

Legacy saved metrics (LEGACY_BASELINE_ONLY): accuracy 0.90, precision 0.5625,
recall 0.75, F1 0.6429, AUROC-from-delta 0.9309, 100/100 successful calls,
median latency 2.60 s. These describe the OLD endpoint + OLD BRCA1 threshold on a
100-row hg19 BRCA1 subset. They are **not** temporal evidence, **not** GRCh38
evidence, and **not** EvoVariant-TR evidence.

### 2.5 Documentation

| Path | Role |
|---|---|
| `README.md` (687 lines) | Legacy system documentation ("Evo2 Variant Analysis"). Describes the old classification-first design. NOT the EvoVariant-TR scientific specification. |
| `PPT_20_SLIDES_MATERIAL.md` | Legacy presentation material |
| `evaluation/README.md`, `evo2-frontend/README.md` | Component docs |

### 2.6 Configuration / metadata

| Path | Role |
|---|---|
| `.gitignore` | Legacy ignore rules (extended at Milestone 1) |
| `.gitmodules` | Declares submodule `evo2-backend/evo2` → `https://github.com/ArcInstitute/evo2`. **Recorded but NOT initialized**; the submodule directory is absent from the snapshot and will not be initialized under the old design. The new project pins official Evo 2 independently (Milestone 51). |

## 3. External identities present in the snapshot (to be replaced, not reused)

- Modal app name: `variant-analysis-evo2` (main.py:33).
- Modal volume: `hf_cache` (main.py:35).
- Old deployment URL (evaluation default): `https://utkarshmer05--variant-analysis-evo2-evo2model-analyze-si-b52940.modal.run`.
- Frontend package name: `variant-analysis-evo2-frontend`.
- Upstream (allowed third-party source, not the old repo): `https://github.com/ArcInstitute/evo2`.

None of these identities may be silently reused as final EvoVariant-TR
infrastructure (master prompt §0).

## 4. Live network dependencies in legacy code

- Backend inference path: UCSC `getData/sequence` per request (main.py:235).
- Frontend browser: UCSC list/sequence APIs, NCBI clinicaltables gene search,
  NCBI eutils gene/clinvar endpoints, Modal endpoint POST (genome-api.ts).

## 5. Known defect flagged for audit (not fixed at this milestone)

`get_genome_sequence` computes `start = max(0, position-1-4096)` and
`end = position-1+4096+1`, so `end - start == 8193` for ordinary interior
positions — the intended 8,192-base context becomes 8,193 bases. This is exactly
the defect the master prompt §1 warns about and must not be inherited
(Milestones 33/41 define the correct even-window contract).

## 6. What is explicitly NOT classified as new research evidence

- All files under `evaluation/results/` → LEGACY_BASELINE_ONLY.
- The BRCA1 threshold/std constants in `main.py` → legacy design, deprecated.
- The old README's "prediction/confidence" contract → legacy design, deprecated.
