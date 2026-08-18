# BASELINE SMOKE TEST — Old project, local reproduction only (Milestone 006)

Date: 2026-08-18
Evidence stage: **LEGACY_BASELINE_ONLY**. Nothing here is EvoVariant-TR evidence.
Command log: `artifacts/baseline/command_log.txt`.

Rules honored: no scientific behavior repaired; no paid Modal GPU work; no old
result promoted to research evidence; every pass/failure recorded verbatim and
categorized.

## 1. Results table

| # | Check | Command | Result | Category |
|---|---|---|---|---|
| 1 | Python syntax (backend + evaluation) | `python3 -m compileall evo2-backend evaluation` | **PASS** (exit 0, all files compiled) | — |
| 2 | Backend import deps on system python3 | `python3 -c "import modal"` etc. | **FAIL** — `modal`, `seaborn`, `openpyxl`, `fastapi`, `sklearn` missing; `pandas`, `numpy`, `matplotlib`, `requests`, `pydantic` present | environment |
| 3 | Evaluator CPU deps install in fresh venv | `python3.12 -m venv .venv-baseline && pip install pandas numpy matplotlib seaborn scikit-learn openpyxl requests` | **PASS** — all import | — |
| 4 | Evaluator module import | dynamic import of `evaluation/evaluate_modal_endpoint.py` | **PASS** (after registering module in `sys.modules`; first attempt failed due to a test-harness artifact, not an evaluator bug) | — |
| 5 | Evaluator `compute_metrics` (synthetic 5-row frame) | harness script | **PASS** — accuracy 0.8000, AUROC 1.0000 on synthetic data | — |
| 6 | Evaluator repetition determinism | harness script (two runs) | **PASS** — identical metrics | — |
| 7 | Evaluator failure preservation (`build_diagnostics`) | harness script | **PASS** — failed call retained with status count `{'500': 1}` | — |
| 8 | Evaluator invalid input (empty predictions) | harness script | **PASS** — raises `RuntimeError: No successful calls, cannot compute metrics.` | — |
| 9 | Evaluator invalid input (missing xlsx) | harness script | **PASS** — raises `FileNotFoundError` | — |
| 10 | Frontend dependency install | `npm ci` | **PASS** (reproducible from lockfile) | — |
| 11 | Frontend typecheck | `npm run typecheck` | **PASS** (tsc --noEmit, exit 0) | — |
| 12 | Frontend build, as-is | `npm run build` | **FAIL** — zod env validation: `NEXT_PUBLIC_ANALYZE_SINGLE_VARIANT_BASE_URL` Required | environment |
| 13 | Frontend build, placeholder env | `NEXT_PUBLIC_ANALYZE_SINGLE_VARIANT_BASE_URL=<placeholder> npm run build` | **FAIL** — ESLint: "Failed to compile", 158 error/warning lines (`@typescript-eslint/no-unsafe-*` in `src/utils/genome-api.ts`, `prefer-nullish-coalescing`, 1 `no-unused-vars`) | code |
| 14 | Evaluator live run against deployed endpoint | NOT RUN | **NOT RUN** — would require the old paid Modal deployment; forbidden at this milestone | — |
| 15 | Backend GPU inference | NOT RUN | **NOT RUN** — requires Modal H100; forbidden at this milestone | — |

## 2. Failure categorization

- **Environment-related:**
  - Check 2: system python3 lacks several CPU deps and the GPU/cloud `modal` package.
    Expected on a fresh machine; the old project never shipped a local requirements
    install path separate from the Modal image.
  - Check 12: `next build` requires `NEXT_PUBLIC_ANALYZE_SINGLE_VARIANT_BASE_URL`
    at build time (env.js zod schema). A fresh checkout without `.env.local` cannot
    build. This is an environment/configuration gap, not a code defect per se.
- **Code-related:**
  - Check 13: with env satisfied, the build fails at the ESLint stage due to 150+
    `no-unsafe-*` lint errors concentrated in `genome-api.ts` (parsing of `any`
    values from NCBI/UCSC responses). `tsc --noEmit` passes, so types compile, but
    the project's own lint gate fails. This is a pre-existing baseline failure.
- **Dependency-related:** none beyond the environment items above. `npm ci`
  resolves cleanly from the lockfile; pip CPU deps install cleanly.
- **External-service-related:** none encountered — no external service was called
  except the npm public registry (free package downloads).

## 3. Baseline status summary

The old project's **Python code is syntactically valid** and the evaluator's pure
metric/diagnostic functions work deterministically on synthetic input with explicit
invalid-input handling. The old project's **frontend installs and typechecks**, but
**does not build as-is** (env requirement) and **does not pass its own lint gate**
even with env provided. The old backend cannot be imported locally without the
GPU/cloud stack and was never intended to run outside Modal.

These facts establish the pre-refactor baseline: any future failure in the new
architecture can be compared against this record to distinguish pre-existing
problems from refactor-introduced ones.

## 4. What was explicitly NOT done

- No scientific behavior was repaired (lint errors, env gap, and clinical framing
  left as-is).
- No paid Modal GPU work was run; the old deployed endpoint was not contacted.
- No saved legacy metric was promoted to research evidence. The synthetic metrics in
  §1 (accuracy 0.8, AUROC 1.0) are harness self-checks on fake data, not results.
